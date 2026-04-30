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
    Float,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import (
    AmountEstimate,
    DensityType,
    ReachabilityType,
    ReportCategory,
    ReportStatus,
    Severity,
    TerrainType,
    UserRole,
)


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


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
            values_callable=enum_values,
        ),
        default=UserRole.CITIZEN,
    )
    phone = Column(String(20), unique=True, index=True)
    admin_preferences = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    reports = relationship(
        "Report", back_populates="user", foreign_keys="Report.user_id"
    )
    assigned_reports = relationship(
        "Report", back_populates="assignee", foreign_keys="Report.assigned_to"
    )
    status_changes = relationship("StatusHistory", back_populates="changed_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    feedback_entries = relationship("Feedback", back_populates="user")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    address = Column(String(500))
    locality = Column(String(255))
    category = Column(Enum(ReportCategory, values_callable=enum_values), default=ReportCategory.OTHER, nullable=False)
    severity = Column(Enum(Severity, values_callable=enum_values), default=Severity.MEDIUM)
    image_url = Column(String(500))
    video_url = Column(String(500))
    description = Column(Text)
    gps_accuracy = Column(Float)
    reported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    terrain = Column(Enum(TerrainType, values_callable=enum_values), default=TerrainType.OTHER, nullable=False)
    reachability = Column(Enum(ReachabilityType, values_callable=enum_values), default=ReachabilityType.MODERATE, nullable=False)
    density = Column(Enum(DensityType, values_callable=enum_values), default=DensityType.MODERATE, nullable=False)
    amount_estimate = Column(Enum(AmountEstimate, values_callable=enum_values), default=AmountEstimate.BAG_1, nullable=False)
    admin_notes = Column(Text)
    status = Column(Enum(ReportStatus, values_callable=enum_values), default=ReportStatus.SUBMITTED)
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
    feedback_entries = relationship("Feedback", back_populates="report")
    audit_logs = relationship("AuditLog", back_populates="report")

    __table_args__ = (
        Index("idx_reports_status", "status"),
        Index("idx_reports_created", "created_at"),
    )

    @property
    def garbage_type(self) -> str:
        return self.category.value


class StatusHistory(Base):
    __tablename__ = "report_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    old_status = Column(Enum(ReportStatus, values_callable=enum_values))
    new_status = Column(Enum(ReportStatus, values_callable=enum_values), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="status_history")
    changed_by_user = relationship("User", back_populates="status_changes")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_helpful = Column(Boolean, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="feedback_entries")
    user = relationship("User", back_populates="feedback_entries")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"))
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")
    report = relationship("Report", back_populates="audit_logs")
