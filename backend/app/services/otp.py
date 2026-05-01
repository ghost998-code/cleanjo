from datetime import datetime, timedelta
from random import randint
from typing import Any

from fastapi import HTTPException, status
from redis.asyncio import Redis

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

    def _redis_key(self, phone: str) -> str:
        return f"otp:{phone}"

    def _get_redis(self) -> Redis:
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self) -> None:
        return None

    async def generate(self, phone: str) -> dict[str, str | int | None]:
        now = datetime.utcnow()
        record = await self._get_record(phone)
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
        record = {
            "otp": otp,
            "expires_at": expires_at,
            "resend_at": resend_at,
        }
        await self._store_record(phone, record)

        payload: dict[str, str | int | None] = {
            "message": "OTP sent successfully",
            "expires_in_seconds": settings.OTP_EXPIRE_MINUTES * 60,
            "otp": otp if settings.OTP_DEV_MODE else None,
        }
        return payload

    async def verify(self, phone: str, otp: str) -> None:
        normalized_otp = otp.strip()
        record = await self._get_record(phone)
        now = datetime.utcnow()

        if not record or record["expires_at"] < now:
            await self._delete_record(phone)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP is invalid or expired",
            )

        if record["otp"] != normalized_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP is invalid or expired",
            )

        await self._delete_record(phone)

    async def _get_record(self, phone: str) -> dict[str, datetime | str] | None:
        redis = self._get_redis()
        try:
            try:
                payload = await redis.hgetall(self._redis_key(phone))
                if payload:
                    return self._deserialize_record(payload)
            except Exception:
                pass
        finally:
            await redis.aclose()

        return self._codes.get(phone)

    async def _store_record(self, phone: str, record: dict[str, datetime | str]) -> None:
        redis = self._get_redis()
        try:
            try:
                ttl_seconds = max(int((record["expires_at"] - datetime.utcnow()).total_seconds()), 1)
                await redis.hset(
                    self._redis_key(phone),
                    mapping={
                        "otp": str(record["otp"]),
                        "expires_at": record["expires_at"].isoformat(),
                        "resend_at": record["resend_at"].isoformat(),
                    },
                )
                await redis.expire(self._redis_key(phone), ttl_seconds)
                self._codes.pop(phone, None)
                return
            except Exception:
                pass
        finally:
            await redis.aclose()

        self._codes[phone] = record

    async def _delete_record(self, phone: str) -> None:
        self._codes.pop(phone, None)
        redis = self._get_redis()
        try:
            try:
                await redis.delete(self._redis_key(phone))
            except Exception:
                pass
        finally:
            await redis.aclose()

    def _deserialize_record(self, payload: dict[str, Any]) -> dict[str, datetime | str]:
        return {
            "otp": payload["otp"],
            "expires_at": datetime.fromisoformat(payload["expires_at"]),
            "resend_at": datetime.fromisoformat(payload["resend_at"]),
        }


otp_service = OTPService()
