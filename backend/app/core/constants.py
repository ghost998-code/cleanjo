from enum import Enum


class UserRole(str, Enum):
    CITIZEN = "citizen"
    INSPECTOR = "inspector"
    ADMIN = "admin"


class ReportStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


GARBAGE_TYPES = [
    "plastic",
    "paper",
    "glass",
    "metal",
    "organic",
    "electronic",
    "hazardous",
    "construction",
    "mixed",
    "other",
]
