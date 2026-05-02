from datetime import datetime, timezone
import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import math

from app.api.deps import get_admin_user, get_current_user, get_inspector_or_admin
from app.api.schemas.report import (
    FeedbackCreate,
    FeedbackResponse,
    GeoJSONFeature,
    GeoJSONResponse,
    ReportInferenceSummary,
    ReportDetailResponse,
    ReportListResponse,
    ReportPhotoCreate,
    ReportResponse,
    ReportStatusUpdate,
    ReportUpdate,
    StatusHistoryResponse,
)
from app.core.config import settings
from app.core.constants import (
    AmountEstimate,
    DensityType,
    ReachabilityType,
    ReportCategory,
    ReportStatus,
    STATUS_TRANSITIONS,
    Severity,
    TerrainType,
    UserRole,
)
from app.core.database import get_db
from app.models import Feedback, Report, ReportPhoto, StatusHistory, User
from app.services.audit import log_audit
from app.services.kafka import kafka_service
from app.services.image import upload_image, upload_video

router = APIRouter(prefix="/reports", tags=["Reports"])


def paginate(query, page: int, page_size: int):
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def validate_upload(file: UploadFile, allowed_prefix: str) -> None:
    if not file.content_type or not file.content_type.startswith(allowed_prefix):
        raise HTTPException(status_code=400, detail=f"Invalid {allowed_prefix} upload")


async def read_upload(file: UploadFile, max_size: int, allowed_prefix: str) -> bytes:
    validate_upload(file, allowed_prefix)
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail=f"Uploaded file exceeds {max_size} bytes")
    return contents


def ensure_status_transition(current_status: ReportStatus, new_status: ReportStatus):
    if new_status == current_status:
        return
    allowed = STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {current_status.value} to {new_status.value}",
        )


photo_metadata_adapter = TypeAdapter(List[ReportPhotoCreate])
report_inference_summary_adapter = TypeAdapter(ReportInferenceSummary)


def parse_photo_metadata(photo_metadata: Optional[str]) -> List[ReportPhotoCreate]:
    if not photo_metadata:
        return []

    try:
        payload = json.loads(photo_metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="photo_metadata must be valid JSON") from exc

    try:
        return photo_metadata_adapter.validate_python(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def parse_report_inference_summary(report_inference_summary: Optional[str]) -> Optional[ReportInferenceSummary]:
    if not report_inference_summary:
        return None

    try:
        payload = json.loads(report_inference_summary)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="report_inference_summary must be valid JSON") from exc

    try:
        return report_inference_summary_adapter.validate_python(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def validate_photo_metadata_entries(photo_entries: List[ReportPhotoCreate]) -> None:
    for entry in photo_entries:
        if entry.gps_accuracy <= 0:
            raise HTTPException(status_code=400, detail="GPS accuracy must be positive")

        if entry.source_type == "gallery":
            if entry.exif_latitude is None or entry.exif_longitude is None:
                raise HTTPException(status_code=400, detail="Gallery photos must include EXIF GPS coordinates")
            if entry.exif_accuracy is not None and entry.exif_accuracy <= 0:
                raise HTTPException(status_code=400, detail="Gallery photo EXIF accuracy must be positive")


def validate_report_inference_summary(
    report_inference_summary: Optional[ReportInferenceSummary],
    photo_entries: List[ReportPhotoCreate],
) -> None:
    if report_inference_summary is None:
        return

    if report_inference_summary.derived_from_photo_count != len(photo_entries):
        raise HTTPException(status_code=400, detail="Summary photo count must match uploaded photo count")


def to_utc_naive(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: Request,
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    locality: Optional[str] = Form(None),
    garbage_type: Optional[str] = Form(None),
    category: Optional[ReportCategory] = Form(None),
    description: Optional[str] = Form(None),
    severity: Optional[Severity] = Form(Severity.MEDIUM),
    terrain: TerrainType = Form(TerrainType.OTHER),
    reachability: ReachabilityType = Form(ReachabilityType.MODERATE),
    density: DensityType = Form(DensityType.MODERATE),
    amount_estimate: Optional[AmountEstimate] = Form(None),
    amount: Optional[AmountEstimate] = Form(None),
    gps_accuracy: Optional[float] = Form(None),
    accuracy: Optional[float] = Form(None),
    reported_at: Optional[datetime] = Form(None),
    timestamp: Optional[datetime] = Form(None),
    accuracy_override: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    photo: Optional[UploadFile] = File(None),
    photo_metadata: Optional[str] = Form(None),
    report_inference_summary: Optional[str] = Form(None),
    video: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form = await request.form()
    uploaded_photos = [
        uploaded_photo
        for uploaded_photo in form.getlist("photos")
        if getattr(uploaded_photo, "filename", None)
    ]

    if uploaded_photos and (image or photo):
        raise HTTPException(status_code=400, detail="Use either photos or image/photo fields, not both")

    image_file = photo or image
    if image_file:
        uploaded_photos.append(image_file)

    if not uploaded_photos:
        raise HTTPException(status_code=400, detail="At least one photo is required")
    if len(uploaded_photos) > settings.MAX_REPORT_PHOTOS:
        raise HTTPException(status_code=400, detail="Photo count exceeds maximum allowed")

    metadata_entries = parse_photo_metadata(photo_metadata)
    if not metadata_entries:
        raise HTTPException(status_code=400, detail="photo_metadata is required for all photo uploads")
    if metadata_entries and len(metadata_entries) != len(uploaded_photos):
        raise HTTPException(status_code=400, detail="Photo metadata count must match uploaded photo count")
    report_summary = parse_report_inference_summary(report_inference_summary)

    validate_photo_metadata_entries(metadata_entries)
    validate_report_inference_summary(report_summary, metadata_entries)

    first_photo_metadata = metadata_entries[0] if metadata_entries else None

    normalized_latitude = latitude if latitude is not None else lat
    if normalized_latitude is None and first_photo_metadata is not None:
        normalized_latitude = first_photo_metadata.latitude

    normalized_longitude = longitude if longitude is not None else lng
    if normalized_longitude is None and first_photo_metadata is not None:
        normalized_longitude = first_photo_metadata.longitude

    normalized_accuracy = gps_accuracy if gps_accuracy is not None else accuracy
    if normalized_accuracy is None and first_photo_metadata is not None:
        normalized_accuracy = first_photo_metadata.gps_accuracy

    normalized_reported_at = reported_at or timestamp
    if normalized_reported_at is None and first_photo_metadata is not None:
        normalized_reported_at = first_photo_metadata.captured_at
    normalized_reported_at = normalized_reported_at or datetime.utcnow()
    normalized_reported_at = to_utc_naive(normalized_reported_at)

    if normalized_latitude is None or normalized_longitude is None:
        raise HTTPException(status_code=400, detail="Latitude and longitude are required")
    if description and len(description) > settings.MAX_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="Description is too long")
    if normalized_accuracy is not None:
        if normalized_accuracy <= 0:
            raise HTTPException(status_code=400, detail="GPS accuracy must be positive")

    photo_urls: List[str] = []
    for uploaded_photo in uploaded_photos:
        contents = await read_upload(uploaded_photo, settings.MAX_IMAGE_UPLOAD_BYTES, "image/")
        photo_urls.append(await upload_image(contents))

    # Keep the legacy cover image populated while older consumers transition to report_photos.
    image_url = photo_urls[0]

    video_url = None
    if video:
        contents = await read_upload(video, settings.MAX_VIDEO_UPLOAD_BYTES, "video/")
        video_url = await upload_video(contents)

    report_category = category
    if report_category is None:
        report_category = ReportCategory(garbage_type) if garbage_type in {item.value for item in ReportCategory} else ReportCategory.OTHER

    report = Report(
        user_id=current_user.id,
        latitude=normalized_latitude,
        longitude=normalized_longitude,
        address=address,
        locality=locality,
        category=report_category,
        description=description,
        severity=severity,
        gps_accuracy=normalized_accuracy,
        reported_at=normalized_reported_at,
        terrain=terrain,
        reachability=reachability,
        density=density,
        amount_estimate=amount_estimate or amount or AmountEstimate.BAG_1,
        image_url=image_url,
        video_url=video_url,
        inference_summary_category=report_summary.summary_category if report_summary else None,
        inference_summary_confidence=report_summary.summary_confidence if report_summary else None,
        inference_summary_strategy=report_summary.summary_strategy if report_summary else None,
        inference_model_version=report_summary.model_version if report_summary else None,
        status=ReportStatus.SUBMITTED,
    )
    db.add(report)
    await db.flush()

    if metadata_entries:
        for photo_url, metadata_entry in zip(photo_urls, metadata_entries):
            db.add(
                ReportPhoto(
                    report_id=report.id,
                    image_url=photo_url,
                    source_type=metadata_entry.source_type,
                    latitude=metadata_entry.latitude,
                    longitude=metadata_entry.longitude,
                    gps_accuracy=metadata_entry.gps_accuracy,
                    captured_at=to_utc_naive(metadata_entry.captured_at),
                    exif_latitude=metadata_entry.exif_latitude,
                    exif_longitude=metadata_entry.exif_longitude,
                    exif_accuracy=metadata_entry.exif_accuracy,
                    exif_captured_at=to_utc_naive(metadata_entry.exif_captured_at),
                    predicted_category=metadata_entry.predicted_category.value,
                    prediction_confidence=metadata_entry.prediction_confidence,
                    predicted_severity=metadata_entry.predicted_severity.value if metadata_entry.predicted_severity else None,
                    severity_confidence=metadata_entry.severity_confidence,
                    model_name=metadata_entry.model_name,
                    model_version=metadata_entry.model_version,
                    inference_ran_at=to_utc_naive(metadata_entry.inference_ran_at),
                    inference_source=metadata_entry.inference_source,
                    top_predictions=[prediction.model_dump(mode="json") for prediction in metadata_entry.top_predictions] if metadata_entry.top_predictions else None,
                )
            )

    db.add(
        StatusHistory(
            report=report,
            changed_by=current_user.id,
            old_status=None,
            new_status=ReportStatus.SUBMITTED,
            notes="Report submitted",
        )
    )
    await log_audit(
        db,
        action="report.created",
        user_id=current_user.id,
        report_id=report.id,
        details={"severity": severity.value, "category": report_category.value},
    )
    await db.commit()
    await db.refresh(report)

    return report


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ReportStatus] = Query(None, alias="status"),
    severity: Optional[Severity] = None,
    category: Optional[ReportCategory] = None,
    assigned_to: Optional[UUID] = None,
    terrain: Optional[TerrainType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Report).order_by(Report.created_at.desc())
    
    if current_user.role == UserRole.CITIZEN:
        query = query.where(Report.user_id == current_user.id)
    elif current_user.role == UserRole.INSPECTOR:
        query = query.where(
            (Report.assigned_to == current_user.id) | (Report.assigned_to.is_(None))
        )

    if status_filter:
        query = query.where(Report.status == status_filter)
    if severity:
        query = query.where(Report.severity == severity)
    if category:
        query = query.where(Report.category == category)
    if assigned_to:
        query = query.where(Report.assigned_to == assigned_to)
    if terrain:
        query = query.where(Report.terrain == terrain)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = paginate(query, page, page_size)
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return ReportListResponse(
        items=reports,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/me", response_model=ReportListResponse)
async def list_my_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ReportStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Report).where(Report.user_id == current_user.id).order_by(Report.created_at.desc())
    if status_filter:
        query = query.where(Report.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(paginate(query, page, page_size))
    reports = result.scalars().all()

    return ReportListResponse(
        items=reports,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/map", response_model=GeoJSONResponse)
async def get_reports_map(
    ne_lat: Optional[float] = Query(None, ge=-90, le=90),
    ne_lng: Optional[float] = Query(None, ge=-180, le=180),
    sw_lat: Optional[float] = Query(None, ge=-90, le=90),
    sw_lng: Optional[float] = Query(None, ge=-180, le=180),
    status_filter: Optional[ReportStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Report)
    
    if status_filter:
        query = query.where(Report.status == status_filter)
    
    if all([ne_lat, ne_lng, sw_lat, sw_lng]):
        query = query.where(
            Report.latitude <= ne_lat,
            Report.latitude >= sw_lat,
            Report.longitude <= ne_lng,
            Report.longitude >= sw_lng,
        )
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    features = [
        GeoJSONFeature(
            type="Feature",
            geometry={
                "type": "Point",
                "coordinates": [float(r.longitude), float(r.latitude)],
            },
            properties={
                "id": str(r.id),
                "status": r.status.value,
                "severity": r.severity.value,
                "garbage_type": r.category.value,
                "category": r.category.value,
                "created_at": r.created_at.isoformat(),
            },
        )
        for r in reports
    ]
    
    return GeoJSONResponse(type="FeatureCollection", features=features)


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.photos),
            selectinload(Report.status_history),
            selectinload(Report.feedback_entries),
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user.role == UserRole.CITIZEN and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ReportDetailResponse.model_validate(report)


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: UUID,
    update_data: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_inspector_or_admin),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    old_status = report.status
    
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"notes"})

    for key, value in update_dict.items():
        if key == "status" and value is not None:
            ensure_status_transition(report.status, value)
        setattr(report, key, value)

    if update_data.notes:
        history = StatusHistory(
            report_id=report.id,
            changed_by=current_user.id,
            old_status=old_status,
            new_status=update_data.status or old_status,
            notes=update_data.notes,
        )
        db.add(history)

    await log_audit(
        db,
        action="report.updated",
        user_id=current_user.id,
        report_id=report.id,
        details={"fields": list(update_dict.keys())},
    )
    await db.commit()
    await db.refresh(report)

    try:
        await kafka_service.send_message("report.status.changed", {
            "report_id": str(report.id),
            "old_status": old_status.value if old_status else None,
            "new_status": report.status.value,
            "changed_by": str(current_user.id),
            "timestamp": datetime.utcnow().isoformat(),
        })
    except Exception:
        pass

    return report


@router.put("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: UUID,
    status_update: ReportStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_inspector_or_admin),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    ensure_status_transition(report.status, status_update.status)
    old_status = report.status
    report.status = status_update.status

    db.add(
        StatusHistory(
            report_id=report.id,
            changed_by=current_user.id,
            old_status=old_status,
            new_status=status_update.status,
            notes=status_update.comment,
        )
    )
    await log_audit(
        db,
        action="report.status_changed",
        user_id=current_user.id,
        report_id=report.id,
        details={"from": old_status.value, "to": status_update.status.value},
    )
    await db.commit()
    await db.refresh(report)
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    await db.delete(report)
    await db.commit()


@router.get("/{report_id}/history", response_model=List[StatusHistoryResponse])
async def get_report_history(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(StatusHistory)
        .where(StatusHistory.report_id == report_id)
        .order_by(StatusHistory.created_at.desc())
    )
    history = result.scalars().all()
    return history


@router.post("/{report_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_report_feedback(
    report_id: UUID,
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if current_user.role == UserRole.CITIZEN and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    entry = Feedback(
        report_id=report.id,
        user_id=current_user.id,
        is_helpful=feedback.is_helpful,
        comment=feedback.comment,
    )
    db.add(entry)
    await log_audit(
        db,
        action="report.feedback_created",
        user_id=current_user.id,
        report_id=report.id,
        details={"is_helpful": feedback.is_helpful},
    )
    await db.commit()
    await db.refresh(entry)
    return entry
