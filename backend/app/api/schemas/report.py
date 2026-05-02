from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
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


class ReportPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    report_id: UUID
    image_url: str
    source_type: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    gps_accuracy: float = Field(..., ge=0)
    captured_at: datetime
    exif_latitude: Optional[float] = Field(None, ge=-90, le=90)
    exif_longitude: Optional[float] = Field(None, ge=-180, le=180)
    exif_accuracy: Optional[float] = Field(None, ge=0)
    exif_captured_at: Optional[datetime] = None
    predicted_category: ReportCategory
    prediction_confidence: float = Field(..., ge=0, le=1)
    predicted_severity: Optional[Severity] = None
    severity_confidence: Optional[float] = Field(None, ge=0, le=1)
    model_name: str
    model_version: str
    inference_ran_at: datetime
    inference_source: Literal["mobile"]
    top_predictions: Optional[List["InferencePrediction"]] = None
    created_at: datetime

class InferencePrediction(BaseModel):
    label: ReportCategory
    confidence: float = Field(..., ge=0, le=1)


class ReportInferenceSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    summary_category: ReportCategory
    summary_confidence: float = Field(..., ge=0, le=1)
    summary_strategy: str = Field(..., min_length=1, max_length=100)
    derived_from_photo_count: int = Field(..., ge=1)
    model_version: str = Field(..., min_length=1, max_length=100)


class ReportPhotoCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    source_type: Literal["camera", "gallery"]
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    gps_accuracy: float = Field(..., gt=0)
    captured_at: datetime
    exif_latitude: Optional[float] = Field(None, ge=-90, le=90)
    exif_longitude: Optional[float] = Field(None, ge=-180, le=180)
    exif_accuracy: Optional[float] = Field(None, gt=0)
    exif_captured_at: Optional[datetime] = None
    predicted_category: ReportCategory
    prediction_confidence: float = Field(..., ge=0, le=1)
    predicted_severity: Optional[Severity] = None
    severity_confidence: Optional[float] = Field(None, ge=0, le=1)
    model_name: str = Field(..., min_length=1, max_length=100)
    model_version: str = Field(..., min_length=1, max_length=100)
    inference_ran_at: datetime
    inference_source: Literal["mobile"] = "mobile"
    top_predictions: Optional[List[InferencePrediction]] = None


class ReportUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ReportResponse(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user: Optional[ReportUser] = None
    garbage_type: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    status: ReportStatus
    assigned_to: Optional[UUID] = None
    admin_notes: Optional[str] = None
    inference_summary_category: Optional[ReportCategory] = None
    inference_summary_confidence: Optional[float] = Field(None, ge=0, le=1)
    inference_summary_strategy: Optional[str] = None
    inference_model_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime

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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    old_status: Optional[ReportStatus]
    new_status: ReportStatus
    notes: Optional[str]
    changed_by: Optional[UUID]
    created_at: datetime

class FeedbackCreate(BaseModel):
    is_helpful: bool
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_id: UUID
    user_id: UUID
    is_helpful: bool
    comment: Optional[str]
    created_at: datetime

class ReportDetailResponse(ReportResponse):
    photos: List[ReportPhotoResponse] = Field(default_factory=list)
    status_history: List[StatusHistoryResponse] = Field(default_factory=list)
    feedback_entries: List[FeedbackResponse] = Field(default_factory=list)


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
    comment: Optional[str] = Field(None, max_length=500)
