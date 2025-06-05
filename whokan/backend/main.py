# main.py (in backend directory)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import asyncio
from sqlalchemy.exc import OperationalError

from api.api import api_router
from core.config import settings
from db.session import add_example_data
from db.database import engine
from db.models import Base

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

async def wait_for_db():
    """Wait for database to be ready"""
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Try to connect to database
            connection = engine.connect()
            connection.close()
            print("Database connection successful!")
            return True
        except OperationalError:
            retry_count += 1
            print(f"Database not ready, retrying... ({retry_count}/{max_retries})")
            await asyncio.sleep(2)
    
    raise Exception("Could not connect to database after maximum retries")

@app.on_event("startup")
async def startup_event():
    # Wait for database to be ready
    await wait_for_db()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")
    
    # Add example data
    add_example_data()

@app.get("/health")
async def health_check():
    try:
        # Try to connect to database
        connection = engine.connect()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}