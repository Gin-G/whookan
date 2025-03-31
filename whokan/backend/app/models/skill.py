from uuid import UUID, uuid4
from typing import Optional


class Skill:
    def __init__(self, name: str, description: Optional[str] = None, id: Optional[UUID] = None):
        self.id = id or uuid4()
        self.name = name
        self.description = description

    def __repr__(self):
        return f"Skill(id={self.id}, name={self.name})"