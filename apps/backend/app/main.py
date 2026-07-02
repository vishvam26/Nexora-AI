import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project configurations
PROJECT_NAME = os.getenv("PROJECT_NAME", "Nexora-AI API")
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(",") if origin.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print(f"Starting up {PROJECT_NAME} in {ENV} mode...")
    yield
    # Shutdown actions
    print(f"Shutting down {PROJECT_NAME}...")

# Initialize FastAPI application
app = FastAPI(
    title=PROJECT_NAME,
    description="The core API service powering the Nexora-AI platform.",
    version="0.1.0",
    debug=DEBUG,
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Input/Output Schemas
class QueryRequest(BaseModel):
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 500

class QueryResponse(BaseModel):
    status: str
    response: str
    model: str

# Endpoints
@app.get("/", tags=["General"])
async def root():
    return {
        "message": f"Welcome to the {PROJECT_NAME}",
        "version": app.version,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "status": "Running"
    }

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "environment": ENV,
        "debug_mode": DEBUG,
        "services": {
            "database": "connected (mocked)",
            "llm_provider": "ready"
        }
    }

@app.post("/api/v1/query", response_model=QueryResponse, tags=["AI Services"])
async def query_model(request: QueryRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Mock AI response logic
    mock_response = f"Received prompt: '{request.prompt}'. This is a mock AI response from the Nexora-AI platform core backend."
    
    return QueryResponse(
        status="success",
        response=mock_response,
        model="gemini-1.5-flash-mock"
    )

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=DEBUG)
