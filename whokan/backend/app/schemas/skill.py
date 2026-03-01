from pydantic import BaseModel, Field, validator
from typing import Optional
from uuid import UUID


class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    @validator("name", pre=True)
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


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