from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID

from app.schemas.skill import Skill


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)


class UserInDBBase(UserBase):
    id: UUID
    skills: List[Skill] = []
    helped_count: int = 0


class UserInDB(UserInDBBase):
    hashed_password: str


class User(UserInDBBase):
    pass
