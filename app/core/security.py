import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token() -> str:
    """Create a secure refresh token."""
    return secrets.token_urlsafe(32)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        # Check if token type matches
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def get_refresh_token_expire_time() -> datetime:
    """Get refresh token expiration time (7 days from now)."""
    return datetime.now(timezone.utc) + timedelta(days=7)


def create_password_reset_token() -> str:
    """Create a secure password reset token."""
    return secrets.token_urlsafe(32)


def get_password_reset_expire_time() -> datetime:
    """Get password reset token expiration time (1 hour from now)."""
    return datetime.now(timezone.utc) + timedelta(hours=1)
