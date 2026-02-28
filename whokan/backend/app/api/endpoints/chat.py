"""Chat endpoints — one real-time chat room per skill, Discord-style."""
from typing import Any, List
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.database import SessionLocal
from app.db.models import ChatMessage, Skill
from app.db.models import User as UserModel
from app.db.session import get_user_by_email
from app.deps import get_current_user, get_db
from app.schemas.chat import ChatHistoryResponse, ChatMessageResponse

router = APIRouter()

HISTORY_LIMIT = 50


# ---------------------------------------------------------------------------
# In-process connection manager (works for single-replica deployment)
# ---------------------------------------------------------------------------

class _ConnectionManager:
    def __init__(self):
        # skill_id (str) → list[WebSocket]
        self._rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, skill_id: str) -> None:
        await ws.accept()
        self._rooms.setdefault(skill_id, []).append(ws)

    def disconnect(self, ws: WebSocket, skill_id: str) -> None:
        room = self._rooms.get(skill_id, [])
        if ws in room:
            room.remove(ws)

    async def broadcast(self, payload: dict, skill_id: str) -> None:
        for ws in list(self._rooms.get(skill_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                pass


manager = _ConnectionManager()


def _serialize_message(msg: ChatMessage) -> dict:
    return {
        "id": str(msg.id),
        "skill_id": str(msg.skill_id),
        "author_id": str(msg.author_id),
        "author_name": msg.author.name,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /api/v1/skills/{skill_id}/chat/history
# ---------------------------------------------------------------------------

@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(
    skill_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Skill not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.skill_id == skill_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    return {
        "skill_id": skill_id,
        "messages": [_serialize_message(m) for m in messages],
    }


# ---------------------------------------------------------------------------
# WS /api/v1/skills/{skill_id}/chat/ws?token=<jwt>
# ---------------------------------------------------------------------------

@router.websocket("/ws")
async def websocket_chat(
    skill_id: UUID,
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    # Validate token and resolve user before accepting the connection
    db = SessionLocal()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user = get_user_by_email(db, payload.get("sub", ""))
    except Exception:
        await websocket.close(code=1008)
        db.close()
        return

    if not user:
        await websocket.close(code=1008)
        db.close()
        return

    skill_id_str = str(skill_id)
    await manager.connect(websocket, skill_id_str)

    # Send recent history to the newly connected client
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.skill_id == skill_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    for msg in messages:
        await websocket.send_json({"type": "history", **_serialize_message(msg)})

    try:
        while True:
            content = await websocket.receive_text()
            content = content.strip()
            if not content:
                continue

            msg = ChatMessage(
                id=uuid4(),
                skill_id=skill_id,
                author_id=user.id,
                content=content,
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            payload_out = {"type": "message", **_serialize_message(msg)}
            await manager.broadcast(payload_out, skill_id_str)

    except WebSocketDisconnect:
        manager.disconnect(websocket, skill_id_str)
    finally:
        db.close()
