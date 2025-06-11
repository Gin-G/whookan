# app/api/endpoints/skills.py
from typing import Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.db.session import get_or_create_skill, add_skill_to_user
from app.db.models import User
from app.db.models import Skill as SkillModel
from app.schemas.skill import Skill, SkillCreate, BulkSkillImport
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.post("", response_model=UserSchema)
def create_skill(
    skill_in: SkillCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new skill
    """
    # Check if user already has this skill
    existing_skill_names = [skill.name.lower() for skill in current_user.skills]
    if skill_in.name.lower() in existing_skill_names:
        raise HTTPException(
            status_code=400,
            detail="Skill already exists for this user",
        )
    
    # Add skill to user (this will create the skill if it doesn't exist)
    add_skill_to_user(db, current_user, skill_in.name)
    
    # Refresh user to get updated skills
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


@router.post("/bulk", response_model=UserSchema)
def create_skills_bulk(
    bulk_import: BulkSkillImport, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Import multiple skills at once
    """
    # Parse the input string based on format
    if bulk_import.format == "csv":
        # Split by comma and trim whitespace
        skill_names = [s.strip() for s in bulk_import.skills.split(",") if s.strip()]
    else:  # newline format
        # Split by newline and trim whitespace
        skill_names = [s.strip() for s in bulk_import.skills.split("\n") if s.strip()]
    
    # Deduplicate skill names (case insensitive)
    unique_skill_names = []
    for skill_name in skill_names:
        if skill_name.lower() not in [s.lower() for s in unique_skill_names]:
            unique_skill_names.append(skill_name)
    
    # Check for skills that user already has
    existing_skill_names = [skill.name.lower() for skill in current_user.skills]
    
    # Add new skills
    for skill_name in unique_skill_names:
        # Skip if user already has this skill
        if skill_name.lower() in existing_skill_names:
            continue
            
        add_skill_to_user(db, current_user, skill_name)
    
    # Refresh user to get updated skills
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


@router.delete("/{skill_id}", response_model=UserSchema)
def delete_skill(
    skill_id: UUID, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a skill from current user
    """
    # Find the skill to remove
    skill_to_remove = None
    for skill in current_user.skills:
        if str(skill.id) == str(skill_id):
            skill_to_remove = skill
            break
    
    if not skill_to_remove:
        raise HTTPException(
            status_code=404,
            detail="Skill not found for this user"
        )
    
    # Remove skill from user
    current_user.skills.remove(skill_to_remove)
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