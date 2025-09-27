"""Account deletion request model."""

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DeletionStatus(enum.Enum):
    """Account deletion status enumeration."""

    PENDING_EMAIL_CONFIRMATION = "pending_email_confirmation"
    EMAIL_CONFIRMED = "email_confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class AccountDeletionRequest(Base):
    """Account deletion request model."""
    
    __tablename__ = "account_deletion_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable in case user is already deleted
    email = Column(String, nullable=False, index=True)
    status = Column(Enum(DeletionStatus), default=DeletionStatus.PENDING_EMAIL_CONFIRMATION, nullable=False)
    reason = Column(String, nullable=True)
    additional_info = Column(Text, nullable=True)

    # Email confirmation
    confirmation_token = Column(String, unique=True, index=True, nullable=True)
    confirmation_token_expires = Column(DateTime(timezone=True), nullable=True)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    email_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin fields
    processed_by = Column(String, nullable=True)  # Admin who processed the request
    admin_notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="deletion_requests")
    
    def __repr__(self):
        return f"<AccountDeletionRequest(request_id='{self.request_id}', email='{self.email}', status='{self.status.value}')>"
