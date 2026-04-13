from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.constants import UserRole
from app.models import User
from app.api.schemas.user import (
    UserResponse,
    AdminPreferences,
    AdminSettingsResponse,
    AdminSettingsUpdate,
)
from app.api.deps import get_current_user, get_admin_user

router = APIRouter(prefix="/users", tags=["Users"])


def _merge_admin_preferences(raw_preferences: Optional[dict]) -> AdminPreferences:
    if not raw_preferences:
        return AdminPreferences()
    return AdminPreferences(**raw_preferences)


@router.get("/me/settings", response_model=AdminSettingsResponse)
async def get_admin_settings(current_user: User = Depends(get_admin_user)):
    return AdminSettingsResponse(
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        preferences=_merge_admin_preferences(current_user.admin_preferences),
    )


@router.patch("/me/settings", response_model=AdminSettingsResponse)
async def update_admin_settings(
    settings_update: AdminSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    if settings_update.full_name is not None:
        current_user.full_name = settings_update.full_name.strip() or current_user.full_name

    if settings_update.preferences is not None:
        current_user.admin_preferences = settings_update.preferences.model_dump()

    await db.commit()
    await db.refresh(current_user)

    return AdminSettingsResponse(
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        preferences=_merge_admin_preferences(current_user.admin_preferences),
    )


@router.get("", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    
    result = await db.execute(query)
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    await db.commit()
    
    return {"message": "Role updated successfully"}
