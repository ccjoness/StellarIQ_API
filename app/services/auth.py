"""Business logic service for auth operations."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    get_password_hash,
    get_password_reset_expire_time,
    get_refresh_token_expire_time,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.email import email_service

logger = logging.getLogger(__name__)


class AuthService:

    """AuthService class."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        if self.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        # Validate disclaimer agreement
        if not user_data.agreed_to_disclaimer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must agree to educational disclaimer to create account",
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        current_time = datetime.now(timezone.utc)

        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            agreed_to_disclaimer=user_data.agreed_to_disclaimer,
            disclaimer_agreed_at=current_time
            if user_data.agreed_to_disclaimer
            else None,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def login_user(self, email: str, password: str) -> dict:
        """Login user and return access and refresh tokens."""
        user = self.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # Create tokens
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
        refresh_token = create_refresh_token()

        # Store refresh token in database
        user.refresh_token = refresh_token
        user.refresh_token_expires_at = get_refresh_token_expire_time()
        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,  # 30 minutes in seconds
            "user": user,
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        logger.debug(f"Attempting to refresh token: {refresh_token}")

        # Find user by refresh token
        user = self.db.query(User).filter(User.refresh_token == refresh_token).first()
        logger.debug(f"Found user: {user.id if user else 'None'}")

        if not user:
            logger.error("No user found with this refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Check if refresh token is expired
        if (
            user.refresh_token_expires_at is None
            or user.refresh_token_expires_at < datetime.now(timezone.utc)
        ):
            # Clear expired refresh token
            user.refresh_token = None
            user.refresh_token_expires_at = None
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # Create new access token
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

        # Optionally rotate refresh token (recommended for security)
        new_refresh_token = create_refresh_token()
        user.refresh_token = new_refresh_token
        user.refresh_token_expires_at = get_refresh_token_expire_time()
        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,  # 30 minutes in seconds
        }

    def revoke_refresh_token(self, user_id: int) -> bool:
        """Revoke user's refresh token (logout)."""
        user = self.get_user_by_id(user_id)
        if user:
            user.refresh_token = None
            user.refresh_token_expires_at = None
            self.db.commit()
            return True
        return False

    def request_password_reset(self, email: str) -> bool:
        """Request password reset for user."""
        logger.debug(f"Password reset requested for email: {email}")

        user = self.get_user_by_email(email)
        if not user:
            # For security, don't reveal if email exists or not
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True  # Return True to not reveal if email exists

        if not user.is_active:
            logger.warning(f"Password reset requested for inactive user: {email}")
            return True  # Return True to not reveal user status

        # Generate password reset token
        reset_token = create_password_reset_token()
        user.password_reset_token = reset_token
        user.password_reset_expires_at = get_password_reset_expire_time()

        try:
            self.db.commit()

            # Send password reset email
            email_sent = email_service.send_password_reset_email(
                user.email, reset_token
            )
            if not email_sent:
                logger.error(f"Failed to send password reset email to {user.email}")
                # Don't fail the request if email fails, user can try again

            logger.info(f"Password reset token generated for user {user.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save password reset token for {email}: {e}")
            self.db.rollback()
            return False

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        logger.debug(f"Password reset attempted with token: {token}")

        # Find user by reset token
        user = self.db.query(User).filter(User.password_reset_token == token).first()

        if not user:
            logger.warning("Invalid password reset token used")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Check if token is expired
        if (
            user.password_reset_expires_at is None
            or user.password_reset_expires_at < datetime.now(timezone.utc)
        ):
            # Clear expired token
            user.password_reset_token = None
            user.password_reset_expires_at = None
            self.db.commit()

            logger.warning(f"Expired password reset token used for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        if not user.is_active:
            logger.warning(f"Password reset attempted for inactive user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not active"
            )

        try:
            # Update password and clear reset token
            user.hashed_password = get_password_hash(new_password)
            user.password_reset_token = None
            user.password_reset_expires_at = None

            # Also revoke all refresh tokens for security
            user.refresh_token = None
            user.refresh_token_expires_at = None

            self.db.commit()

            logger.info(f"Password successfully reset for user {user.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset password for user {user.id}: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password",
            )

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """Change user password after verifying current password."""
        logger.debug(f"Password change requested for user {user_id}")

        user = self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Password change attempted for non-existent user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_active:
            logger.warning(f"Password change attempted for inactive user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is not active",
            )

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            logger.warning(f"Invalid current password provided for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Check if new password is different from current
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        try:
            # Update password
            user.hashed_password = get_password_hash(new_password)

            # Revoke all refresh tokens for security (force re-login on other devices)
            user.refresh_token = None
            user.refresh_token_expires_at = None

            self.db.commit()

            logger.info(f"Password successfully changed for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password",
            )

    def update_user_profile(self, user_id: int, profile_data: dict) -> User:
        """Update user profile information."""
        logger.debug(f"Profile update requested for user {user_id}")

        user = self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Profile update attempted for non-existent user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_active:
            logger.warning(f"Profile update attempted for inactive user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is not active",
            )

        try:
            # Update profile fields if provided
            if profile_data.get("full_name") is not None:
                user.full_name = profile_data["full_name"].strip() if profile_data["full_name"] else None

            if profile_data.get("timezone") is not None:
                user.timezone = profile_data["timezone"]

            if profile_data.get("preferred_currency") is not None:
                user.preferred_currency = profile_data["preferred_currency"]

            if profile_data.get("email_notifications") is not None:
                user.email_notifications = profile_data["email_notifications"]

            if profile_data.get("push_notifications") is not None:
                user.push_notifications = profile_data["push_notifications"]

            # Update the updated_at timestamp
            user.updated_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Profile successfully updated for user {user_id}")
            return user

        except Exception as e:
            logger.error(f"Failed to update profile for user {user_id}: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile",
            )
