"""Account deletion service."""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.account_deletion import AccountDeletionRequest, DeletionStatus
from app.models.user import User
from app.schemas.account_deletion import (
    AccountDeletionRequest as AccountDeletionRequestSchema,
    AccountDeletionResponse,
    AccountDeletionStatus,
)
from app.services.email import email_service

logger = logging.getLogger(__name__)


class AccountDeletionService:
    """Service for handling account deletion requests."""

    @staticmethod
    def create_deletion_request(
        db: Session, request_data: AccountDeletionRequestSchema, base_url: str = "https://stellariq.app"
    ) -> AccountDeletionResponse:
        """Create a new account deletion request and send confirmation email."""

        # Check if user exists
        user = db.query(User).filter(User.email == request_data.email).first()
        if not user:
            raise ValueError("No account found with this email address")

        # Check if there's already a pending request
        existing_request = (
            db.query(AccountDeletionRequest)
            .filter(
                AccountDeletionRequest.email == request_data.email,
                AccountDeletionRequest.status.in_([
                    DeletionStatus.PENDING_EMAIL_CONFIRMATION,
                    DeletionStatus.EMAIL_CONFIRMED
                ])
            )
            .first()
        )

        if existing_request:
            raise ValueError("A deletion request is already pending for this account")

        # Generate secure confirmation token
        confirmation_token = secrets.token_urlsafe(32)
        request_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        estimated_completion = now + timedelta(days=30)
        token_expires = now + timedelta(hours=24)  # 24 hour expiry

        # Create new deletion request
        deletion_request = AccountDeletionRequest(
            request_id=request_id,
            user_id=user.id,
            email=request_data.email,
            reason=request_data.reason,
            additional_info=request_data.additional_info,
            estimated_completion=estimated_completion,
            confirmation_token=confirmation_token,
            confirmation_token_expires=token_expires,
            status=DeletionStatus.PENDING_EMAIL_CONFIRMATION,
        )

        db.add(deletion_request)
        db.commit()
        db.refresh(deletion_request)

        # Send confirmation email
        confirmation_url = f"{base_url}/account-deletion/confirm?token={confirmation_token}"
        email_sent = email_service.send_account_deletion_confirmation(
            request_data.email, confirmation_url, request_id
        )

        if email_sent:
            deletion_request.email_sent_at = now
            db.commit()
            logger.info(f"Account deletion confirmation email sent to {user.email}")
        else:
            logger.error(f"Failed to send confirmation email to {user.email}")
            # Don't fail the request, user can try again

        logger.info(f"Account deletion request created: {request_id} for user {user.email}")

        return AccountDeletionResponse(
            message="Account deletion request submitted. Please check your email to confirm.",
            request_id=request_id,
            email=request_data.email,
            estimated_completion=estimated_completion.strftime("%Y-%m-%d"),
        )

    @staticmethod
    def get_deletion_status(db: Session, request_id: str) -> Optional[AccountDeletionStatus]:
        """Get the status of a deletion request."""
        
        deletion_request = (
            db.query(AccountDeletionRequest)
            .filter(AccountDeletionRequest.request_id == request_id)
            .first()
        )
        
        if not deletion_request:
            return None
        
        return AccountDeletionStatus.from_orm(deletion_request)

    @staticmethod
    def confirm_deletion_request(db: Session, confirmation_token: str) -> bool:
        """Confirm account deletion request via email token and delete the account."""

        # Find the deletion request by token
        deletion_request = (
            db.query(AccountDeletionRequest)
            .filter(
                AccountDeletionRequest.confirmation_token == confirmation_token,
                AccountDeletionRequest.status == DeletionStatus.PENDING_EMAIL_CONFIRMATION
            )
            .first()
        )

        if not deletion_request:
            logger.warning(f"Invalid or already used confirmation token: {confirmation_token}")
            return False

        # Check if token has expired
        now = datetime.now(timezone.utc)
        if deletion_request.confirmation_token_expires < now:
            deletion_request.status = DeletionStatus.EXPIRED
            db.commit()
            logger.warning(f"Expired confirmation token: {confirmation_token}")
            return False

        # Mark as confirmed
        deletion_request.status = DeletionStatus.EMAIL_CONFIRMED
        deletion_request.email_confirmed_at = now
        db.commit()

        # Immediately delete the account
        try:
            user = db.query(User).filter(User.id == deletion_request.user_id).first()
            if user:
                user_email = user.email

                # Delete user and all associated data (cascade relationships handle this)
                db.delete(user)
                db.commit()

                # Mark deletion as completed
                deletion_request.status = DeletionStatus.COMPLETED
                deletion_request.completed_at = now
                db.commit()

                # Send completion email
                email_service.send_account_deletion_completed(user_email)

                logger.info(f"Account deletion completed for token: {confirmation_token}")
                return True
            else:
                logger.error(f"User not found for deletion request: {deletion_request.request_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete account for token {confirmation_token}: {e}")
            # Revert status back to confirmed
            deletion_request.status = DeletionStatus.EMAIL_CONFIRMED
            deletion_request.completed_at = None
            db.commit()
            return False

    @staticmethod
    def cancel_deletion_request(db: Session, request_id: str, user_email: str) -> bool:
        """Cancel a pending deletion request."""

        deletion_request = (
            db.query(AccountDeletionRequest)
            .filter(
                AccountDeletionRequest.request_id == request_id,
                AccountDeletionRequest.email == user_email,
                AccountDeletionRequest.status.in_([
                    DeletionStatus.PENDING_EMAIL_CONFIRMATION,
                    DeletionStatus.EMAIL_CONFIRMED
                ])
            )
            .first()
        )

        if not deletion_request:
            return False

        deletion_request.status = DeletionStatus.CANCELLED
        db.commit()

        logger.info(f"Account deletion request cancelled: {request_id}")
        return True

    @staticmethod
    def process_deletion_request(db: Session, request_id: str, admin_user: str) -> bool:
        """Process a deletion request (admin function - for confirmed requests only)."""

        deletion_request = (
            db.query(AccountDeletionRequest)
            .filter(
                AccountDeletionRequest.request_id == request_id,
                AccountDeletionRequest.status == DeletionStatus.EMAIL_CONFIRMED
            )
            .first()
        )

        if not deletion_request:
            return False

        # Update status to processing
        now = datetime.now(timezone.utc)
        deletion_request.status = DeletionStatus.PROCESSING
        deletion_request.processing_started_at = now
        deletion_request.processed_by = admin_user
        db.commit()

        try:
            # Delete user and all associated data
            user = db.query(User).filter(User.id == deletion_request.user_id).first()
            if user:
                user_email = user.email

                # The cascade relationships will handle deletion of:
                # - favorites
                # - device_tokens
                # - notifications
                # - deletion_requests
                db.delete(user)
                db.commit()

                # Send completion email
                email_service.send_account_deletion_completed(user_email)

            # Mark deletion as completed
            deletion_request.status = DeletionStatus.COMPLETED
            deletion_request.completed_at = now
            db.commit()

            logger.info(f"Account deletion completed: {request_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to process deletion request {request_id}: {e}")
            # Revert status back to confirmed
            deletion_request.status = DeletionStatus.EMAIL_CONFIRMED
            deletion_request.processing_started_at = None
            deletion_request.processed_by = None
            db.commit()
            return False

    @staticmethod
    def get_pending_requests(db: Session, limit: int = 50) -> list[AccountDeletionRequest]:
        """Get all pending deletion requests (admin function)."""

        return (
            db.query(AccountDeletionRequest)
            .filter(AccountDeletionRequest.status.in_([
                DeletionStatus.PENDING_EMAIL_CONFIRMATION,
                DeletionStatus.EMAIL_CONFIRMED
            ]))
            .order_by(AccountDeletionRequest.requested_at)
            .limit(limit)
            .all()
        )

    @staticmethod
    def cleanup_expired_requests(db: Session) -> int:
        """Clean up expired deletion requests (admin function)."""

        now = datetime.now(timezone.utc)
        expired_requests = (
            db.query(AccountDeletionRequest)
            .filter(
                AccountDeletionRequest.status == DeletionStatus.PENDING_EMAIL_CONFIRMATION,
                AccountDeletionRequest.confirmation_token_expires < now
            )
            .all()
        )

        count = 0
        for request in expired_requests:
            request.status = DeletionStatus.EXPIRED
            count += 1

        db.commit()
        logger.info(f"Marked {count} deletion requests as expired")
        return count
