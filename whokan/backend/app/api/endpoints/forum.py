"""Forum endpoints — one forum per skill, Reddit-style posts + comments + upvotes."""
from typing import Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.db.models import Skill, ForumPost, PostComment, PostVote
from app.db.models import User as UserModel
from app.schemas.forum import (
    ForumPostCreate, ForumPostSummary, ForumPostDetail,
    PostCommentCreate, PostCommentResponse,
)

router = APIRouter()


def _serialize_post(post: ForumPost, current_user_id: UUID, detail: bool = False) -> dict:
    voted = any(str(v.user_id) == str(current_user_id) for v in post.votes)
    base = {
        "id": post.id,
        "skill_id": post.skill_id,
        "author_id": post.author_id,
        "author_name": post.author.name,
        "title": post.title,
        "body": post.body,
        "vote_count": len(post.votes),
        "comment_count": len(post.comments),
        "created_at": post.created_at,
    }
    if detail:
        base["user_voted"] = voted
        base["comments"] = [
            {
                "id": c.id,
                "post_id": c.post_id,
                "author_id": c.author_id,
                "author_name": c.author.name,
                "body": c.body,
                "created_at": c.created_at,
            }
            for c in sorted(post.comments, key=lambda c: c.created_at)
        ]
    return base


def _get_skill_or_404(skill_id: UUID, db: Session) -> Skill:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


# ---------------------------------------------------------------------------
# GET /api/v1/skills/{skill_id}/forum/info  – skill metadata for the forum page
# ---------------------------------------------------------------------------

@router.get("/info")
def get_skill_info(
    skill_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    skill = _get_skill_or_404(skill_id, db)
    return {"id": str(skill.id), "name": skill.name}


# ---------------------------------------------------------------------------
# GET  /api/v1/skills/{skill_id}/forum   – list posts (newest first)
# POST /api/v1/skills/{skill_id}/forum   – create a post
# ---------------------------------------------------------------------------

@router.get("", response_model=List[ForumPostSummary])
def list_posts(
    skill_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    _get_skill_or_404(skill_id, db)
    posts = (
        db.query(ForumPost)
        .filter(ForumPost.skill_id == skill_id)
        .order_by(ForumPost.created_at.desc())
        .all()
    )
    return [_serialize_post(p, current_user.id) for p in posts]


@router.post("", response_model=ForumPostSummary)
def create_post(
    skill_id: UUID,
    post_in: ForumPostCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    _get_skill_or_404(skill_id, db)
    post = ForumPost(
        id=uuid4(),
        skill_id=skill_id,
        author_id=current_user.id,
        title=post_in.title,
        body=post_in.body,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _serialize_post(post, current_user.id)


# ---------------------------------------------------------------------------
# GET  /api/v1/skills/{skill_id}/forum/{post_id}  – post detail + comments
# ---------------------------------------------------------------------------

@router.get("/{post_id}", response_model=ForumPostDetail)
def get_post(
    skill_id: UUID,
    post_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    post = db.query(ForumPost).filter(
        ForumPost.id == post_id, ForumPost.skill_id == skill_id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _serialize_post(post, current_user.id, detail=True)


# ---------------------------------------------------------------------------
# POST /api/v1/skills/{skill_id}/forum/{post_id}/comments  – add comment
# ---------------------------------------------------------------------------

@router.post("/{post_id}/comments", response_model=PostCommentResponse)
def add_comment(
    skill_id: UUID,
    post_id: UUID,
    comment_in: PostCommentCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    post = db.query(ForumPost).filter(
        ForumPost.id == post_id, ForumPost.skill_id == skill_id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = PostComment(
        id=uuid4(),
        post_id=post_id,
        author_id=current_user.id,
        body=comment_in.body,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "author_id": comment.author_id,
        "author_name": current_user.name,
        "body": comment.body,
        "created_at": comment.created_at,
    }


# ---------------------------------------------------------------------------
# POST /api/v1/skills/{skill_id}/forum/{post_id}/vote  – toggle upvote
# ---------------------------------------------------------------------------

@router.post("/{post_id}/vote")
def toggle_vote(
    skill_id: UUID,
    post_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    post = db.query(ForumPost).filter(
        ForumPost.id == post_id, ForumPost.skill_id == skill_id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(PostVote).filter(
        PostVote.user_id == current_user.id,
        PostVote.post_id == post_id,
    ).first()

    if existing:
        db.delete(existing)
        voted = False
    else:
        db.add(PostVote(user_id=current_user.id, post_id=post_id))
        voted = True

    db.commit()
    db.refresh(post)
    return {"voted": voted, "vote_count": len(post.votes)}
