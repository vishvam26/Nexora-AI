print(">>> MAIN.PY LOADED <<<")
import logging
# Configure physical file logging to capture all backend warnings, errors, and exceptions outside watched folder
import os
log_path = "backend.log"
if os.name == "nt":
    local_path = "C:/Users/vishv/.gemini/antigravity-ide/brain/ba311efa-90f6-4f38-a17e-4d8a2be32c35/backend.log"
    # Ensure directory exists before using it
    if os.path.exists(os.path.dirname(local_path)):
        log_path = local_path

file_handler = logging.FileHandler(log_path, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

root_logger = logging.getLogger()
if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import settings


from app.db.database import Base, engine

# IMPORTANT - Register all models
import app.db.base

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="The core API service powering the Nexora AI platform.",
)

# Configure CORS Middleware to allow cross-origin requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


print("====================================")
print(Base.metadata.tables)
print("====================================")

Base.metadata.create_all(bind=engine)


app.include_router(api_router)


@app.on_event("startup")
def startup_event():
    if settings.AI_PROVIDER.lower().strip() == "nexora":
        print(">>> NEXORA AI PROVIDER IS ACTIVE (Lazy preloading enabled) <<<")
        # Preloading is disabled on startup to prevent RAM exhaustion crashes and allow instant server start.
        # The model will load lazily on the first chat request.
        pass


@app.get("/", tags=["General"])
def root():
    return {"message": f"Welcome to {settings.APP_NAME} 🚀"}
