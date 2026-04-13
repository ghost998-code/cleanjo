from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.database import get_db
from app.core.constants import UserRole, ReportStatus
from app.models import User, Report, StatusHistory
from app.api.deps import get_current_user, get_admin_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    total_reports = await db.execute(
        select(func.count(Report.id)).where(Report.created_at >= start_date)
    )
    total = total_reports.scalar() or 0
    
    status_counts = {}
    for status in ReportStatus:
        count = await db.execute(
            select(func.count(Report.id)).where(
                Report.status == status,
                Report.created_at >= start_date,
            )
        )
        status_counts[status.value] = count.scalar() or 0
    
    by_severity = await db.execute(
        select(Report.severity, func.count(Report.id))
        .where(Report.created_at >= start_date)
        .group_by(Report.severity)
    )
    severity_counts = {s.value: c for s, c in by_severity.all()}
    
    reports_by_day = await db.execute(
        select(
            func.date_trunc("day", Report.created_at).label("day"),
            func.count(Report.id),
        )
        .where(Report.created_at >= start_date)
        .group_by("day")
        .order_by("day")
    )
    daily_counts = [{"date": str(d), "count": c} for d, c in reports_by_day.all()]
    
    return {
        "period_days": days,
        "total_reports": total,
        "by_status": status_counts,
        "by_severity": severity_counts,
        "daily_trend": daily_counts,
    }


@router.get("/heatmap")
async def get_heatmap_data(
    status_filter: Optional[ReportStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    query = select(Report.latitude, Report.longitude, Report.severity)
    
    if status_filter:
        query = query.where(Report.status == status_filter)
    
    result = await db.execute(query)
    reports = result.all()
    
    grid_size = 0.01
    heatmap = defaultdict(int)
    
    for lat, lng, severity in reports:
        lat_key = round(float(lat) / grid_size) * grid_size
        lng_key = round(float(lng) / grid_size) * grid_size
        key = (lat_key, lng_key)
        
        weight = {"low": 1, "medium": 2, "high": 3, "critical": 5}.get(severity.value, 1)
        heatmap[key] += weight
    
    return {
        "points": [
            {"lat": lat, "lng": lng, "weight": weight}
            for (lat, lng), weight in heatmap.items()
        ]
    }
