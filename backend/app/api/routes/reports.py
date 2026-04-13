from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
import math

from app.core.database import get_db
from app.core.constants import UserRole, ReportStatus, Severity, GARBAGE_TYPES
from app.models import User, Report, StatusHistory
from app.api.schemas.report import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportListResponse,
    GeoJSONResponse,
    GeoJSONFeature,
    StatusHistoryResponse,
)
from app.api.deps import get_current_user, require_role, get_admin_user, get_inspector_or_admin
from app.services.kafka import kafka_service
from app.services.image import upload_image

router = APIRouter(prefix="/reports", tags=["Reports"])


def paginate(query, page: int, page_size: int):
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: Optional[str] = Form(None),
    garbage_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    severity: Optional[Severity] = Form(Severity.MEDIUM),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_url = None
    if image:
        contents = await image.read()
        image_url = await upload_image(contents)
    
    report = Report(
        user_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        address=address,
        garbage_type=garbage_type,
        description=description,
        severity=severity,
        image_url=image_url,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    try:
        await kafka_service.send_message("report.created", {
            "report_id": str(report.id),
            "user_id": str(current_user.id),
            "latitude": latitude,
            "longitude": longitude,
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
    garbage_type: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
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
    if garbage_type:
        query = query.where(Report.garbage_type == garbage_type)
    if assigned_to:
        query = query.where(Report.assigned_to == assigned_to)
    
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
                "garbage_type": r.garbage_type,
                "created_at": r.created_at.isoformat(),
            },
        )
        for r in reports
    ]
    
    return GeoJSONResponse(type="FeatureCollection", features=features)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user.role == UserRole.CITIZEN and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return report


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
