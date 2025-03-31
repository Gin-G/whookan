from fastapi import APIRouter

from app.api.endpoints import auth, users, skills, help_requests

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(skills.router, prefix="/users/me/skills", tags=["skills"])
api_router.include_router(help_requests.router, prefix="/help-requests", tags=["help-requests"])

