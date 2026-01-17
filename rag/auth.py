"""
Authentication utilities for Fortif.ai RAG API.
Implements API key-based authentication and JWT for dashboard users.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import settings
from database.connection import get_db
from database.models import User


# API Key header configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# OAuth2 configuration for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# JWT Configuration (from settings)
JWT_SECRET_KEY = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    This dependency can be used to protect endpoints:
        @app.post("/api/query", dependencies=[Depends(verify_api_key)])

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key string

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If no API key is configured in settings, allow all requests (dev mode)
    if not settings.api_key:
        return "dev-mode-no-auth"

    # Check if API key was provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header in request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key using constant-time comparison (prevents timing attacks)
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key.

    Utility function for administrators to generate new API keys.

    Args:
        length: Length of the API key (default 32 characters)

    Returns:
        Secure random API key string

    Example:
        >>> key = generate_api_key()
        >>> print(f"Your new API key: {key}")
    """
    return secrets.token_urlsafe(length)


# Optional: Role-based access control (future enhancement)
class APIKeyPermissions:
    """Define permission levels for different API keys."""

    READ_ONLY = "read"  # Can query, cannot ingest
    WRITE = "write"  # Can ingest data
    ADMIN = "admin"  # Full access

    @staticmethod
    def check_permission(api_key: str, required_permission: str) -> bool:
        """
        Check if API key has required permission level.

        Args:
            api_key: Validated API key
            required_permission: Required permission level

        Returns:
            True if permission granted

        Note:
            Current implementation grants all permissions.
            Extend this for production with key-to-permission mapping.
        """
        # TODO: Implement key-to-permission mapping
        # For now, all valid keys have all permissions
        return True


# === JWT Authentication Functions ===

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims (e.g., {"sub": user_email})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Dictionary containing claims (e.g., {"sub": user_email})

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT.

    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None:
            raise credentials_exception

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional version of get_current_user that returns None instead of raising.
    Useful for endpoints that work with or without authentication.
    """
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


def require_role(allowed_roles: list):
    """
    Dependency factory to check user role.

    Usage:
        @app.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
        async def admin_only():
            return {"message": "Admin access granted"}

    Args:
        allowed_roles: List of allowed role values (e.g., ["admin", "caregiver"])

    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker


# Convenience role dependencies
require_admin = require_role(["admin"])
require_caregiver = require_role(["admin", "caregiver"])
require_any_user = require_role(["admin", "caregiver", "family"])
