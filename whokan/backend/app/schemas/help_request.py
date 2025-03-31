from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class HelpRequestBase(BaseModel):
    skill_id: UUID
    description: str


class HelpRequestCreate(HelpRequestBase):
    pass


class HelpRequestUpdate(BaseModel):
    status: str


class HelpRequestInDB(HelpRequestBase):
    id: UUID
    requester_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "open"  # open, assigned, completed


class HelpRequest(HelpRequestInDB):
    pass


class HelpConfirmation(BaseModel):
    request_id: UUID
    helper_id: UUID
    skill_id: UUID
