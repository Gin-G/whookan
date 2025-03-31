from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime


class HelpRequest:
    def __init__(
        self,
        requester_id: UUID,
        skill_id: UUID,
        description: str,
        status: str = "open",
        created_at: Optional[datetime] = None,
        id: Optional[UUID] = None,
    ):
        self.id = id or uuid4()
        self.requester_id = requester_id
        self.skill_id = skill_id
        self.description = description
        self.status = status  # open, assigned, completed
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        return f"HelpRequest(id={self.id}, requester_id={self.requester_id}, skill_id={self.skill_id})"