import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.constants import UserRole
from app.models import User
from app.api.schemas.user import UserCreate, UserResponse, Token, LoginRequest, OTPRequest, OTPResponse, PhoneOTPVerifyRequest
from app.api.deps import get_current_user
from app.services.otp import normalize_phone, otp_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


def build_default_name(phone: str) -> str:
    digits = "".join(char for char in phone if char.isdigit())
    return f"User {digits[-4:] or '0000'}"


def build_phone_email(phone: str) -> str:
    digits = "".join(char for char in phone if char.isdigit())
    return f"user-{digits}@phone.cleanjo.local"


@router.post("/request-registration-otp", response_model=OTPResponse)
async def request_registration_otp(otp_request: OTPRequest, db: AsyncSession = Depends(get_db)):
    normalized_phone = normalize_phone(otp_request.phone)

    result = await db.execute(select(User).where(User.phone == normalized_phone))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    return otp_service.generate(normalized_phone)


@router.post("/request-phone-otp", response_model=OTPResponse)
async def request_phone_otp(otp_request: OTPRequest):
    normalized_phone = normalize_phone(otp_request.phone)
    return otp_service.generate(normalized_phone)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    normalized_phone = normalize_phone(user_data.phone)

    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    result = await db.execute(select(User).where(User.phone == normalized_phone))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    otp_service.verify(normalized_phone, user_data.otp)

    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=normalized_phone,
        role=user_data.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/verify-phone-otp", response_model=Token)
async def verify_phone_otp(phone_data: PhoneOTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    normalized_phone = normalize_phone(phone_data.phone)
    otp_service.verify(normalized_phone, phone_data.otp)

    result = await db.execute(select(User).where(User.phone == normalized_phone))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=build_phone_email(normalized_phone),
            password_hash=get_password_hash(secrets.token_urlsafe(24)),
            full_name=build_default_name(normalized_phone),
            phone=normalized_phone,
            role=UserRole.CITIZEN,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.full_name:
        user.full_name = build_default_name(normalized_phone)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
