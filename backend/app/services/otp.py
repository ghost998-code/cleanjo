from datetime import datetime, timedelta
from random import randint

from fastapi import HTTPException, status

from app.core.config import settings


def normalize_phone(phone: str) -> str:
    normalized = "".join(char for char in phone if char.isdigit() or char == "+")
    if normalized.count("+") > 1 or ("+" in normalized and not normalized.startswith("+")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format",
        )

    digits = normalized[1:] if normalized.startswith("+") else normalized
    if not digits.isdigit() or len(digits) < 10 or len(digits) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must contain 10 to 15 digits",
        )

    return normalized if normalized.startswith("+") else f"+{digits}"


class OTPService:
    def __init__(self) -> None:
        self._codes: dict[str, dict[str, datetime | str]] = {}

    def generate(self, phone: str) -> dict[str, str | int | None]:
        now = datetime.utcnow()
        record = self._codes.get(phone)
        if record:
            resend_after = int((record["resend_at"] - now).total_seconds())
            if resend_after > 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {resend_after} seconds before requesting another OTP",
                )

        otp = f"{randint(0, 999999):06d}"
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        resend_at = now + timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
        self._codes[phone] = {
            "otp": otp,
            "expires_at": expires_at,
            "resend_at": resend_at,
        }

        payload: dict[str, str | int | None] = {
            "message": "OTP sent successfully",
            "expires_in_seconds": settings.OTP_EXPIRE_MINUTES * 60,
            "otp": otp if settings.OTP_DEV_MODE else None,
        }
        return payload

    def verify(self, phone: str, otp: str) -> None:
        record = self._codes.get(phone)
        now = datetime.utcnow()

        if not record or record["expires_at"] < now:
            self._codes.pop(phone, None)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP is invalid or expired",
            )

        if record["otp"] != otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP is invalid or expired",
            )

        self._codes.pop(phone, None)


otp_service = OTPService()
