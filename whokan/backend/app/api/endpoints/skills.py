# app/api/endpoints/skills.py
from typing import Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user
from app.db.session import skills_db, users_db
from app.models.user import User
from app.models.skill import Skill as SkillModel
from app.schemas.skill import Skill, SkillCreate, BulkSkillImport
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.post("", response_model=UserSchema)
def create_skill(
    skill_in: SkillCreate, current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new skill
    """
    # Check if user already has this skill
    for existing_skill in current_user.skills:
        if existing_skill.name.lower() == skill_in.name.lower():
            raise HTTPException(
                status_code=400,
                detail="Skill already exists for this user",
            )
    
    skill_id = uuid4()
    skill = SkillModel(
        id=skill_id,
        name=skill_in.name,
        description=skill_in.description,
    )
    skills_db[str(skill_id)] = skill
    current_user.skills.append(skill)
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


@router.post("/bulk", response_model=UserSchema)
def create_skills_bulk(
    bulk_import: BulkSkillImport, current_user: User = Depends(get_current_user)
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
            
        skill_id = uuid4()
        new_skill = SkillModel(id=skill_id, name=skill_name)
        skills_db[str(skill_id)] = new_skill
        current_user.skills.append(new_skill)
    
    # Save updated user
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


@router.delete("/{skill_id}", response_model=UserSchema)
def delete_skill(
    skill_id: UUID, current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a skill
    """
    current_user.skills = [skill for skill in current_user.skills if skill.id != skill_id]
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