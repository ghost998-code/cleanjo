from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def log_audit(
    db: AsyncSession,
    *,
    action: str,
    user_id: Any = None,
    report_id: Any = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            user_id=user_id,
            report_id=report_id,
            details=details or {},
        )
    )
