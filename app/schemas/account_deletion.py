"""Pydantic schemas for account deletion requests."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class AccountDeletionRequest(BaseModel):
    """Schema for account deletion request."""
    
    email: EmailStr
    reason: Optional[str] = None
    additional_info: Optional[str] = None
    confirm_deletion: bool


class AccountDeletionResponse(BaseModel):
    """Schema for account deletion response."""
    
    message: str
    request_id: str
    email: EmailStr
    estimated_completion: str


class AccountDeletionStatus(BaseModel):
    """Schema for account deletion status."""
    
    request_id: str
    email: EmailStr
    status: str  # pending, processing, completed, cancelled
    requested_at: datetime
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reason: Optional[str] = None
    additional_info: Optional[str] = None
    
    class Config:
        """Config class."""
        from_attributes = True
