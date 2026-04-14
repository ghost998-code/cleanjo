import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Enum,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import UserRole, ReportStatus, Severity


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(
        Enum(
            UserRole,
            name="userrole",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=UserRole.CITIZEN,
    )
    phone = Column(String(20), unique=True, index=True)
    admin_preferences = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship(
        "Report", back_populates="user", foreign_keys="Report.user_id"
    )
    assigned_reports = relationship(
        "Report", back_populates="assignee", foreign_keys="Report.assigned_to"
    )
    status_changes = relationship("StatusHistory", back_populates="changed_by_user")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    address = Column(String(500))
    garbage_type = Column(String(100))
    severity = Column(Enum(Severity), default=Severity.MEDIUM)
    image_url = Column(String(500))
    description = Column(Text)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reports", foreign_keys=[user_id])
    assignee = relationship(
        "User", back_populates="assigned_reports", foreign_keys=[assigned_to]
    )
    status_history = relationship(
        "StatusHistory", back_populates="report", order_by="StatusHistory.created_at"
    )

    __table_args__ = (
        Index("idx_reports_status", "status"),
        Index("idx_reports_created", "created_at"),
    )


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    old_status = Column(Enum(ReportStatus))
    new_status = Column(Enum(ReportStatus), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="status_history")
    changed_by_user = relationship("User", back_populates="status_changes")
