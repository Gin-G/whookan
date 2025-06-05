# app/api/endpoints/users.py
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.deps import get_current_user, get_db
from app.db.session import create_user, get_users_by_skill, get_user_by_email
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
        "skills": [skill.name for skill in current_user.skills] if current_user.skills else [],
        "helped_count": current_user.helped_count
    }


@router.put("/me", response_model=User)
def update_user_me(
    user_update: UserUpdate, 
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
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

    db.commit()
    db.refresh(current_user)
    
    # Convert model to dict to match Pydantic schema
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "title": current_user.title,
        "company": current_user.company,
        "skills": [skill.name for skill in current_user.skills] if current_user.skills else [],
        "helped_count": current_user.helped_count
    }


@router.post("/", response_model=User)
def create_user_endpoint(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Create new user
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    # Create the user using the CRUD function
    user = create_user(
        db=db,
        email=user_in.email,
        name=user_in.name,
        password=user_in.password,
        title=user_in.title,
        company=user_in.company
    )
    
    # Convert model to dict to match Pydantic schema
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "title": user.title,
        "company": user.company,
        "skills": [skill.name for skill in user.skills] if user.skills else [],
        "helped_count": user.helped_count
    }


@router.get("/", response_model=List[User])
def read_users(
    skill: Optional[str] = None, 
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve users. If skill is provided, filter users by skill.
    """
    if skill:
        users = get_users_by_skill(db, skill)
    else:
        users = db.query(UserModel).all()
    
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
            "skills": [skill.name for skill in user.skills] if user.skills else [],
            "helped_count": user.helped_count
        }
        for user in filtered_users
    ]