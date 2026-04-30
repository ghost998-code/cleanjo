from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.core.constants import (
    AmountEstimate,
    DensityType,
    ReachabilityType,
    ReportCategory,
    ReportStatus,
    Severity,
    TerrainType,
)


class ReportBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    locality: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    gps_accuracy: Optional[float] = Field(None, ge=0)
    reported_at: Optional[datetime] = None
    category: ReportCategory
    severity: Severity
    terrain: TerrainType
    reachability: ReachabilityType
    density: DensityType
    amount_estimate: AmountEstimate


class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    severity: Optional[Severity] = None
    category: Optional[ReportCategory] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = Field(None, max_length=500)


class ReportResponse(ReportBase):
    id: UUID
    user_id: UUID
    garbage_type: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    status: ReportStatus
    assigned_to: Optional[UUID] = None
    admin_notes: Optional[str] = None
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


class FeedbackCreate(BaseModel):
    is_helpful: bool
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    id: UUID
    report_id: UUID
    user_id: UUID
    is_helpful: bool
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportDetailResponse(ReportResponse):
    status_history: List[StatusHistoryResponse] = Field(default_factory=list)
    feedback_entries: List[FeedbackResponse] = Field(default_factory=list)


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
    comment: Optional[str] = Field(None, max_length=500)
