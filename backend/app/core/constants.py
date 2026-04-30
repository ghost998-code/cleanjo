from enum import Enum


class UserRole(str, Enum):
    CITIZEN = "citizen"
    INSPECTOR = "inspector"
    ADMIN = "admin"


class ReportStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    SCHEDULED = "scheduled"
    CLEANED = "cleaned"
    REJECTED = "rejected"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportCategory(str, Enum):
    HOUSEHOLD = "household"
    CONSTRUCTION = "construction"
    GREEN = "green"
    HAZARDOUS = "hazardous"
    ELECTRONIC = "electronic"
    BULKY = "bulky"
    MIXED = "mixed"
    OTHER = "other"


class TerrainType(str, Enum):
    STREET = "street"
    SIDEWALK = "sidewalk"
    OPEN_LOT = "open_lot"
    WATERWAY = "waterway"
    RESIDENTIAL = "residential"
    INDUSTRIAL = "industrial"
    OTHER = "other"


class ReachabilityType(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    REQUIRES_SPECIAL_EQUIPMENT = "requires_special_equipment"


class DensityType(str, Enum):
    SPARSE = "sparse"
    MODERATE = "moderate"
    DENSE = "dense"
    ILLEGAL_DUMP = "illegal_dump"


class AmountEstimate(str, Enum):
    BAG_1 = "1_bag"
    BAGS_2_5 = "2_5_bags"
    BAGS_6_15 = "6_15_bags"
    TRUCKLOAD = "truckload"


LEGACY_STATUS_MAPPING = {
    "pending": ReportStatus.SUBMITTED,
    "in_progress": ReportStatus.UNDER_REVIEW,
    "resolved": ReportStatus.CLEANED,
    "rejected": ReportStatus.REJECTED,
}

STATUS_TRANSITIONS = {
    ReportStatus.SUBMITTED: {ReportStatus.UNDER_REVIEW, ReportStatus.REJECTED},
    ReportStatus.UNDER_REVIEW: {ReportStatus.SCHEDULED, ReportStatus.CLEANED, ReportStatus.REJECTED},
    ReportStatus.SCHEDULED: {ReportStatus.CLEANED, ReportStatus.REJECTED},
    ReportStatus.CLEANED: set(),
    ReportStatus.REJECTED: set(),
}
