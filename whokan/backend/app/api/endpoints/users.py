# app/api/endpoints/users.py
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.core.security import get_password_hash
from app.deps import get_current_user
from app.db.session import users_db, get_users_by_skill
from app.schemas.user import User, UserCreate, UserUpdate
from app.models.user import User as UserModel

router = APIRouter()


@router.get("/me", response_model=User)
def read_user_me(current_user: UserModel = Depends(get_current_user)) -> Any:
    """
    Get current user
    """
    # Convert model to dict to match Pydantic schema
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "title": current_user.title,
        "company": current_user.company,
        "skills": current_user.skills,
        "helped_count": current_user.helped_count
    }


@router.put("/me", response_model=User)
def update_user_me(
    user_update: UserUpdate, current_user: UserModel = Depends(get_current_user)
) -> Any:
    """
    Update current user
    """
    if user_update.name:
        current_user.name = user_update.name
    if user_update.title:
        current_user.title = user_update.title
    if user_update.company:
        current_user.company = user_update.company

    users_db[current_user.email] = current_user
    
    # Convert model to dict to match Pydantic schema
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "title": current_user.title,
        "company": current_user.company,
        "skills": current_user.skills,
        "helped_count": current_user.helped_count
    }


@router.post("/", response_model=User)
def create_user(user_in: UserCreate) -> Any:
    """
    Create new user
    """
    if user_in.email in users_db:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    hashed_password = get_password_hash(user_in.password)
    user = UserModel(
        email=user_in.email,
        hashed_password=hashed_password,
        name=user_in.name,
        title=user_in.title,
        company=user_in.company,
    )
    users_db[user.email] = user
    
    # Convert model to dict to match Pydantic schema
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "title": user.title,
        "company": user.company,
        "skills": user.skills,
        "helped_count": user.helped_count
    }


@router.get("/", response_model=List[User])
def read_users(
    skill: Optional[str] = None, current_user: UserModel = Depends(get_current_user)
) -> Any:
    """
    Retrieve users. If skill is provided, filter users by skill.
    """
    if skill:
        users = get_users_by_skill(skill)
    else:
        users = list(users_db.values())
    
    # Filter out current user
    filtered_users = [user for user in users if user.id != current_user.id]
    
    # Convert model list to dict list to match Pydantic schema
    return [
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "title": user.title,
            "company": user.company,
            "skills": user.skills,
            "helped_count": user.helped_count
        }
        for user in filtered_users
    ]