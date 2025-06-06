import os
from typing import List
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "WhoKan")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security - These should come from external secrets
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "11520"))  # 8 days
    
    # Database - Full URL from external secrets or individual components
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Fallback individual DB components if DATABASE_URL not provided
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app_db")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []
    
    # Environment-specific defaults
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string from env var
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY must be set")
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set CORS origins based on environment if not explicitly set
        if not self.BACKEND_CORS_ORIGINS:
            if self.ENVIRONMENT == "development":
                self.BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]
            elif self.ENVIRONMENT == "production":
                cors_origins = os.getenv("BACKEND_CORS_ORIGINS", "")
                if cors_origins:
                    self.BACKEND_CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]
                else:
                    # Fallback - should be set via env var in production
                    self.BACKEND_CORS_ORIGINS = ["https://your-domain.com"]
        
        # Build DATABASE_URL if not provided directly
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        case_sensitive = True

settings = Settings()