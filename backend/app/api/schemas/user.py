from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.core.constants import UserRole, ReportStatus, Severity


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    phone: str = Field(..., min_length=10, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6)
    role: UserRole = UserRole.CITIZEN


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AdminPreferences(BaseModel):
    notify_on_critical: bool = True
    compact_report_cards: bool = False
    auto_refresh_map: bool = True


class AdminSettingsResponse(BaseModel):
    full_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    preferences: AdminPreferences


class AdminSettingsUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    preferences: Optional[AdminPreferences] = None


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)


class OTPResponse(BaseModel):
    message: str
    expires_in_seconds: int
    otp: Optional[str] = None


class PhoneOTPVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6)
