from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class HelpRequestBase(BaseModel):
    skill_id: UUID
    description: str = Field(..., min_length=1, max_length=2000)


class HelpRequestCreate(HelpRequestBase):
    pass


class HelpRequestUpdate(BaseModel):
    status: str


class HelpRequestInDB(HelpRequestBase):
    id: UUID
    requester_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "open"  # open, in_progress, completed, cancelled
    requester_name: str = ""
    skill_name: str = ""

    class Config:
        orm_mode = True


class HelpRequest(HelpRequestInDB):
    pass


class HelpConfirmation(BaseModel):
    request_id: UUID
    helper_id: UUID
    skill_id: UUID
