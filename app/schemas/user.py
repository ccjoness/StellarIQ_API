"""Pydantic schemas for user data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):

    """UserBase class."""

    email: EmailStr
    username: str


class UserCreate(UserBase):

    """UserCreate class."""

    password: str


class UserLogin(BaseModel):

    """UserLogin class."""

    email: EmailStr
    password: str


class UserResponse(UserBase):

    """UserResponse class."""

    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        """Config class."""

        from_attributes = True


class UserUpdate(BaseModel):

    """UserUpdate class."""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class Token(BaseModel):

    """Token class."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenRefresh(BaseModel):

    """TokenRefresh class."""

    refresh_token: str


class TokenData(BaseModel):

    """TokenData class."""

    email: Optional[str] = None


class PasswordResetRequest(BaseModel):

    """PasswordResetRequest class."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):

    """PasswordResetConfirm class."""

    token: str
    new_password: str


class PasswordResetResponse(BaseModel):

    """PasswordResetResponse class."""

    message: str
