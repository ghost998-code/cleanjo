from pydantic import BaseModel, Field


class MobileConfigResponse(BaseModel):
    max_report_photos: int = Field(..., ge=1)
    gps_max_accuracy_meters: float = Field(..., gt=0)
