from pydantic import BaseSettings
from typing import Optional, Dict, Any, List
import secrets


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


settings = Settings()