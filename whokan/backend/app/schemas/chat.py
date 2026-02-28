from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List


class ChatMessageResponse(BaseModel):
    id: UUID
    skill_id: UUID
    author_id: UUID
    author_name: str
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    skill_id: UUID
    messages: List[ChatMessageResponse]
