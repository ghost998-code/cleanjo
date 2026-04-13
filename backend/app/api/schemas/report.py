from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.core.constants import ReportStatus, Severity


class ReportBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    garbage_type: Optional[str] = None
    description: Optional[str] = None


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    severity: Optional[Severity] = None
    garbage_type: Optional[str] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None


class ReportResponse(ReportBase):
    id: UUID
    user_id: UUID
    severity: Severity
    image_url: Optional[str] = None
    status: ReportStatus
    assigned_to: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict


class GeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


class StatusHistoryResponse(BaseModel):
    id: UUID
    old_status: Optional[ReportStatus]
    new_status: ReportStatus
    notes: Optional[str]
    changed_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True
