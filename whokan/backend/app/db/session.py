from typing import Dict, Optional, List
from uuid import uuid4

from app.models.user import User
from app.models.skill import Skill
from app.models.help_request import HelpRequest

# Mock databases
users_db: Dict[str, User] = {}  # Key: email
skills_db: Dict[str, Skill] = {}  # Key: skill_id
help_requests_db: Dict[str, HelpRequest] = {}  # Key: request_id

def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve a user by email
    """
    return users_db.get(email)

def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Retrieve a user by ID
    """
    for user in users_db.values():
        if str(user.id) == user_id:
            return user
    return None

def get_skill_by_id(skill_id: str) -> Optional[Skill]:
    """
    Retrieve a skill by ID
    """
    return skills_db.get(skill_id)

def get_help_request_by_id(request_id: str) -> Optional[HelpRequest]:
    """
    Retrieve a help request by ID
    """
    return help_requests_db.get(request_id)

def get_users_by_skill(skill_term: str) -> List[User]:
    """
    Find users who have skills matching the search term
    """
    found_users = []
    for user in users_db.values():
        for skill in user.skills:
            if skill_term.lower() in skill.name.lower():
                found_users.append(user)
                break
    return found_users

def add_example_data():
    """
    Add example data for testing
    """
    from app.core.security import get_password_hash
    
    # Create users
    users = [
        {
            "email": "jane@example.com",
            "password": "password123",
            "name": "Jane Doe",
            "title": "Product Designer",
            "company": "TechCorp",
        },
        {
            "email": "michael@example.com",
            "password": "password123",
            "name": "Michael Johnson",
            "title": "Software Engineer",
            "company": "TechCorp",
        },
        {
            "email": "sarah@example.com",
            "password": "password123",
            "name": "Sarah Williams",
            "title": "UX Designer",
            "company": "TechCorp",
        },
    ]
    
    for user_data in users:
        if user_data["email"] not in users_db:
            user_id = uuid4()
            hashed_password = get_password_hash(user_data["password"])
            
            user = User(
                id=user_id,
                email=user_data["email"],
                name=user_data["name"],
                title=user_data["title"],
                company=user_data["company"],
                hashed_password=hashed_password,
                skills=[],
                helped_count=0
            )
            users_db[user_data["email"]] = user
    
    # Add skills to users
    skills_data = {
        "jane@example.com": ["UI Design", "User Research", "Prototyping"],
        "michael@example.com": ["JavaScript", "React", "Node.js"],
        "sarah@example.com": ["UI Design", "Figma", "User Research"],
    }
    
    for email, skill_names in skills_data.items():
        user = users_db[email]
        for skill_name in skill_names:
            skill_id = uuid4()
            skill = Skill(id=skill_id, name=skill_name)
            skills_db[str(skill_id)] = skill
            user.skills.append(skill)
    
    # Set help counts
    users_db["michael@example.com"].helped_count = 12
    users_db["sarah@example.com"].helped_count = 8