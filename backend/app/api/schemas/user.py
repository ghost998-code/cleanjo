from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.core.constants import UserRole


class UserBase(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


class RegisterRequest(UserBase):
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    otp: Optional[str] = Field(None, min_length=6, max_length=6)
    role: UserRole = UserRole.CITIZEN

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.email and not self.phone:
            raise ValueError("Email or phone is required")
        return self


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AdminPreferences(BaseModel):
    notify_on_critical: bool = True
    compact_report_cards: bool = False
    auto_refresh_map: bool = True


class AdminSettingsResponse(BaseModel):
    full_name: Optional[str] = None
    email: str
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
    last_login: Optional[datetime] = None

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
    identifier: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str

    @model_validator(mode="after")
    def validate_identifier(self):
        if not any([self.identifier, self.email, self.phone]):
            raise ValueError("identifier, email, or phone is required")
        return self


class OTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)


class OTPResponse(BaseModel):
    message: str
    expires_in_seconds: int
    otp: Optional[str] = None


class PhoneOTPVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserRoleUpdate(BaseModel):
    role: UserRole
