from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from datetime import datetime


class PostCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class PostCommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    author_id: UUID
    author_name: str
    body: str
    created_at: datetime


class ForumPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=10000)


class ForumPostSummary(BaseModel):
    id: UUID
    skill_id: UUID
    author_id: UUID
    author_name: str
    title: str
    body: str
    vote_count: int
    comment_count: int
    created_at: datetime


class ForumPostDetail(ForumPostSummary):
    user_voted: bool
    comments: List[PostCommentResponse]
