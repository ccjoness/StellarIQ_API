from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Refresh token fields
    refresh_token = Column(Text, nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Password reset fields
    password_reset_token = Column(Text, nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    favorites = relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan"
    )
