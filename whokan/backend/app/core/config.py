from pydantic import BaseSettings
from typing import Optional, Dict, Any, List
import secrets
import os

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    PROJECT_NAME: str = "WhoKan"

    class Config:
        env_file = ".env"
        case_sensitive = True
    
    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "postgres"  # This will be the service name in docker-compose
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "app_db"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Environment
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()