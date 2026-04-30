from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
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
    ReportDetailResponse,
    ReportListResponse,
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
from app.models import Feedback, Report, StatusHistory, User
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


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
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
    video: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_latitude = latitude if latitude is not None else lat
    normalized_longitude = longitude if longitude is not None else lng
    normalized_accuracy = gps_accuracy if gps_accuracy is not None else accuracy
    normalized_reported_at = reported_at or timestamp or datetime.utcnow()

    if normalized_latitude is None or normalized_longitude is None:
        raise HTTPException(status_code=400, detail="Latitude and longitude are required")
    if description and len(description) > settings.MAX_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="Description is too long")
    if normalized_accuracy is not None:
        if normalized_accuracy > settings.GPS_MAX_ACCURACY_METERS and not accuracy_override:
            raise HTTPException(status_code=400, detail="GPS accuracy is too low for submission")
        if normalized_accuracy <= 0:
            raise HTTPException(status_code=400, detail="GPS accuracy must be positive")

    image_file = photo or image
    image_url = None
    if image_file:
        contents = await read_upload(image_file, settings.MAX_IMAGE_UPLOAD_BYTES, "image/")
        image_url = await upload_image(contents)

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
        status=ReportStatus.SUBMITTED,
    )
    db.add(report)
    await db.flush()
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

    try:
        await kafka_service.send_message("report.created", {
            "report_id": str(report.id),
            "user_id": str(current_user.id),
            "latitude": normalized_latitude,
            "longitude": normalized_longitude,
            "timestamp": datetime.utcnow().isoformat(),
        })
    except Exception:
        pass

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
        .options(selectinload(Report.status_history), selectinload(Report.feedback_entries))
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
