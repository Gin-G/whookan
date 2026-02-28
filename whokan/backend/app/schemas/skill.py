from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(SkillBase):
    pass


class SkillInDB(SkillBase):
    id: UUID

    class Config:
        orm_mode = True


class Skill(SkillInDB):
    pass


class BulkSkillImport(BaseModel):
    skills: str  # Raw string containing skills (CSV or newline-separated)
    format: str = "newline"  # "newline" or "csv"