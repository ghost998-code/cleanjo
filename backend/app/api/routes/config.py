from fastapi import APIRouter

from app.api.schemas.config import MobileConfigResponse
from app.core.config import settings

router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/mobile", response_model=MobileConfigResponse)
async def get_mobile_config():
    return MobileConfigResponse(
        max_report_photos=settings.MAX_REPORT_PHOTOS,
        gps_max_accuracy_meters=settings.GPS_MAX_ACCURACY_METERS,
    )
