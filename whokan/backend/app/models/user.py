from uuid import UUID, uuid4
from typing import List, Optional
from app.models.skill import Skill


class User:
    def __init__(
        self,
        email: str,
        hashed_password: str,
        name: str,
        title: Optional[str] = None,
        company: Optional[str] = None,
        skills: Optional[List[Skill]] = None,
        helped_count: int = 0,
        id: Optional[UUID] = None,
    ):
        self.id = id or uuid4()
        self.email = email
        self.hashed_password = hashed_password
        self.name = name
        self.title = title
        self.company = company
        self.skills = skills or []
        self.helped_count = helped_count

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, name={self.name})"
