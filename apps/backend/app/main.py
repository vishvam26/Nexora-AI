from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import settings
from app.db.database import Base, engine

# Register models
import app.db.base

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="The core API service powering the Nexora AI platform.",
)

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(api_router)


@app.get("/", tags=["General"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} 🚀"
    }
