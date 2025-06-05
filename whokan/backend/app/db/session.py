from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.database import SessionLocal
from app.db.models import User, Skill, HelpRequest
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by email
    """
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """
    Retrieve a user by ID
    """
    return db.query(User).filter(User.id == user_id).first()

def get_skill_by_id(db: Session, skill_id: str) -> Optional[Skill]:
    """
    Retrieve a skill by ID
    """
    return db.query(Skill).filter(Skill.id == skill_id).first()

def get_skill_by_name(db: Session, skill_name: str) -> Optional[Skill]:
    """
    Retrieve a skill by name
    """
    return db.query(Skill).filter(Skill.name == skill_name).first()

def get_or_create_skill(db: Session, skill_name: str) -> Skill:
    """
    Get existing skill or create new one
    """
    skill = get_skill_by_name(db, skill_name)
    if not skill:
        skill = Skill(name=skill_name)
        db.add(skill)
        db.commit()
        db.refresh(skill)
    return skill

def get_help_request_by_id(db: Session, request_id: str) -> Optional[HelpRequest]:
    """
    Retrieve a help request by ID
    """
    return db.query(HelpRequest).filter(HelpRequest.id == request_id).first()

def get_users_by_skill(db: Session, skill_term: str) -> List[User]:
    """
    Find users who have skills matching the search term
    """
    return db.query(User).join(User.skills).filter(
        Skill.name.ilike(f"%{skill_term}%")
    ).distinct().all()

def create_user(db: Session, email: str, name: str, password: str, title: str = None, company: str = None) -> User:
    """
    Create a new user
    """
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        name=name,
        title=title,
        company=company,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def add_skill_to_user(db: Session, user: User, skill_name: str):
    """
    Add a skill to a user
    """
    skill = get_or_create_skill(db, skill_name)
    if skill not in user.skills:
        user.skills.append(skill)
        db.commit()

def add_example_data():
    """
    Add example data for testing
    """
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).first():
            print("Example data already exists, skipping...")
            return
            
        # Create users
        users_data = [
            {
                "email": "jane@example.com",
                "password": "password123",
                "name": "Jane Doe",
                "title": "Product Designer",
                "company": "TechCorp",
                "skills": ["UI Design", "User Research", "Prototyping"]
            },
            {
                "email": "michael@example.com",
                "password": "password123",
                "name": "Michael Johnson",
                "title": "Software Engineer", 
                "company": "TechCorp",
                "skills": ["JavaScript", "React", "Node.js"],
                "helped_count": 12
            },
            {
                "email": "sarah@example.com",
                "password": "password123",
                "name": "Sarah Williams",
                "title": "UX Designer",
                "company": "TechCorp",
                "skills": ["UI Design", "Figma", "User Research"],
                "helped_count": 8
            },
        ]
        
        for user_data in users_data:
            # Create user
            user = create_user(
                db=db,
                email=user_data["email"],
                name=user_data["name"],
                password=user_data["password"],
                title=user_data["title"],
                company=user_data["company"]
            )
            
            # Add skills
            for skill_name in user_data["skills"]:
                add_skill_to_user(db, user, skill_name)
            
            # Set helped count if provided
            if "helped_count" in user_data:
                user.helped_count = user_data["helped_count"]
                db.commit()
        
        print("Example data added successfully!")
        
    except Exception as e:
        print(f"Error adding example data: {e}")
        db.rollback()
    finally:
        db.close()