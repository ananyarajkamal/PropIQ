"""System Health and Operational Status Route Handler."""

from fastapi import APIRouter
from app.config import Config
from app.models import HealthResponseModel

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponseModel,
    summary="System health check endpoint",
)
async def get_health_status() -> HealthResponseModel:
    """Return backend service operational health status."""
    return HealthResponseModel(
        status="ok",
        service=Config.APP_NAME,
        phase="phase7",
        groq_configured=Config.is_groq_configured(),
    )
