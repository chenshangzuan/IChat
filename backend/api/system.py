from fastapi import APIRouter

from common.config import config

router = APIRouter(tags=["系统"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
    }
