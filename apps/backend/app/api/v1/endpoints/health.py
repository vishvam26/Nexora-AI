from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["System"])
def health():
    return {
        "status": "healthy",
        "service": "Nexora AI"
    }