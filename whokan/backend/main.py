from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import os
import traceback
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.database import engine

# Import api_router last, after database setup
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__, "trace": traceback.format_exc()}
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

    # Import models here to ensure they're loaded
    from app.db.models import Base

    if os.environ.get("ENVIRONMENT") == "test":
        # Fast path for tests: create tables directly
        Base.metadata.create_all(bind=engine)
        print("Database tables created (test mode)!")
    else:
        # Production: run alembic migrations
        from sqlalchemy import inspect as sa_inspect
        from alembic import command
        from alembic.config import Config as AlembicConfig

        inspector = sa_inspect(engine)
        existing_tables = inspector.get_table_names()

        cfg = AlembicConfig("alembic.ini")
        if existing_tables:
            # DB already has tables from a previous create_all — stamp as current
            # so alembic knows the schema is up to date without re-running migration 0001.
            try:
                command.stamp(cfg, "head")
                print("Alembic stamped existing schema as head.")
            except Exception as e:
                print(f"Alembic stamp warning (non-fatal): {e}")
        command.upgrade(cfg, "head")
        print("Alembic migrations applied!")

    # Add example data
    from app.db.session import add_example_data
    add_example_data()

# Import and include router after startup event is defined
from app.api.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    try:
        # Try to connect to database
        connection = engine.connect()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}