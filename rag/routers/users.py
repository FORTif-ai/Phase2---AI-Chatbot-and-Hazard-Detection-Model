"""
User authentication and management endpoints for Fortif.ai Memory Dashboard.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, Patient, UserRole
from database import crud
from auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# === Pydantic Models ===

class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds


class UserCreate(BaseModel):
    """Request model for creating a new user."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="caregiver", pattern="^(caregiver|family|admin)$")


class UserResponse(BaseModel):
    """Response model for user information."""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Request model for updating user information."""
    full_name: Optional[str] = None
    role: Optional[str] = Field(default=None, pattern="^(caregiver|family|admin)$")
    is_active: Optional[bool] = None


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str


class PatientResponse(BaseModel):
    """Response model for patient information."""
    id: int
    patient_id: str
    display_name: str
    can_edit: bool

    class Config:
        from_attributes = True


# === Authentication Endpoints ===

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    - **username**: User email address
    - **password**: User password
    """
    user = crud.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens with user email as subject
    token_data = {"sub": user.email, "role": user.role.value}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    """
    try:
        payload = decode_token(request.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use refresh token."
            )

        email = payload.get("sub")
        user = crud.get_user_by_email(db, email)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new tokens
        token_data = {"sub": user.email, "role": user.role.value}
        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Note: In production, this should be admin-only or require email verification.
    """
    # Check if email already exists
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Map role string to enum
    role_map = {
        "caregiver": UserRole.CAREGIVER,
        "family": UserRole.FAMILY,
        "admin": UserRole.ADMIN
    }

    user = crud.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=role_map.get(user_data.role, UserRole.CAREGIVER)
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at
    )


# === User Profile Endpoints ===

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get the current authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get("/me/patients", response_model=List[PatientResponse])
async def get_my_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all patients assigned to the current user."""
    assignments = current_user.patient_assignments
    return [
        PatientResponse(
            id=a.patient.id,
            patient_id=a.patient.patient_id,
            display_name=a.patient.display_name,
            can_edit=a.can_edit
        )
        for a in assignments
    ]


# === Admin User Management Endpoints ===

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = crud.get_users(db, skip=skip, limit=limit)
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
            is_active=u.is_active,
            created_at=u.created_at
        )
        for u in users
    ]


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)."""
    role_enum = None
    if user_update.role:
        role_map = {
            "caregiver": UserRole.CAREGIVER,
            "family": UserRole.FAMILY,
            "admin": UserRole.ADMIN
        }
        role_enum = role_map.get(user_update.role)

    user = crud.update_user(
        db=db,
        user_id=user_id,
        full_name=user_update.full_name,
        role=role_enum,
        is_active=user_update.is_active
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
