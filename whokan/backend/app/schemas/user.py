from pydantic import BaseModel, EmailStr
from typing import List, Optional
from uuid import UUID

from app.schemas.skill import Skill


class UserBase(BaseModel):
    email: EmailStr
    name: str
    title: Optional[str] = None
    company: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None


class UserInDBBase(UserBase):
    id: UUID
    skills: List[Skill] = []
    helped_count: int = 0


class UserInDB(UserInDBBase):
    hashed_password: str


class User(UserInDBBase):
    pass
