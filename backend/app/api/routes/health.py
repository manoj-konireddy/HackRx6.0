"""Health check endpoints."""

from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system information."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": {
            "debug": settings.debug,
            "log_level": settings.log_level
        },
        "features": {
            "document_processing": True,
            "vector_search": True,
            "llm_integration": True,
            "supported_domains": ["insurance", "legal", "hr", "compliance", "general"]
        }
    }
