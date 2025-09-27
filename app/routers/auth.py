"""API router for auth endpoints."""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.account_deletion import (
    AccountDeletionRequest as AccountDeletionRequestSchema,
    AccountDeletionResponse,
)
from app.schemas.user import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResponse,
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserProfileResponse,
    UserProfileUpdate,
    UserResponse,
)
from app.services.account_deletion import AccountDeletionService
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    auth_service = AuthService(db)
    user = auth_service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access and refresh tokens."""
    auth_service = AuthService(db)
    result = auth_service.login_user(user_data.email, user_data.password)
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"],
    }


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information with full profile."""
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    logger.debug(f"Refresh endpoint called with token: {token_data.refresh_token}")
    try:
        auth_service = AuthService(db)
        result = auth_service.refresh_access_token(token_data.refresh_token)
        logger.debug("Refresh successful")
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
        }
    except Exception as e:
        logger.error(f"Refresh failed with error: {e}")
        raise


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Logout user and revoke refresh token."""
    auth_service = AuthService(db)
    auth_service.revoke_refresh_token(current_user.id)
    return {"message": "Successfully logged out"}


@router.post("/password-reset-request", response_model=PasswordResetResponse)
async def request_password_reset(
    request_data: PasswordResetRequest, db: Session = Depends(get_db)
):
    """Request password reset email."""
    logger.debug(f"Password reset requested for email: {request_data.email}")

    auth_service = AuthService(db)
    success = auth_service.request_password_reset(request_data.email)

    if success:
        return PasswordResetResponse(
            message="If the email exists in our system, you will receive password reset instructions."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request",
        )


@router.post("/password-reset-confirm", response_model=PasswordResetResponse)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """Confirm password reset with token."""
    logger.debug(f"Password reset confirmation with token: {reset_data.token}")

    auth_service = AuthService(db)
    success = auth_service.reset_password(reset_data.token, reset_data.new_password)

    if success:
        return PasswordResetResponse(
            message="Password has been successfully reset. Please log in with your new password."
        )


@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """Verify if token is valid."""
    return {"valid": True, "user_id": current_user.id}


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change user password."""
    logger.debug(f"Password change requested for user {current_user.id}")

    auth_service = AuthService(db)
    success = auth_service.change_password(
        current_user.id, password_data.current_password, password_data.new_password
    )

    if success:
        return ChangePasswordResponse(
            message="Password changed successfully. Please log in again."
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user profile information."""
    logger.debug(f"Profile update requested for user {current_user.id}")

    auth_service = AuthService(db)
    updated_user = auth_service.update_user_profile(
        current_user.id, profile_data.model_dump(exclude_unset=True)
    )

    return updated_user


@router.get("/account-deletion", response_class=HTMLResponse)
async def account_deletion_form(request: Request, email: str = None):
    """Display account deletion request form."""
    return templates.TemplateResponse(
        "account-deletion.html",
        {
            "request": request,
            "email": email,
            "success": False,
            "error": None,
        }
    )


@router.post("/account-deletion", response_class=HTMLResponse)
async def submit_account_deletion(
    request: Request,
    email: str = Form(...),
    reason: str = Form(None),
    additional_info: str = Form(None),
    confirm_deletion: bool = Form(...),
    db: Session = Depends(get_db),
):
    """Submit account deletion request."""
    try:
        # Validate the confirmation checkbox
        if not confirm_deletion:
            raise ValueError("You must confirm that you want to delete your account")

        # Create the deletion request
        request_data = AccountDeletionRequestSchema(
            email=email,
            reason=reason if reason else None,
            additional_info=additional_info if additional_info else None,
            confirm_deletion=confirm_deletion,
        )

        deletion_service = AccountDeletionService()
        response = deletion_service.create_deletion_request(db, request_data)

        return templates.TemplateResponse(
            "account-deletion.html",
            {
                "request": request,
                "email": email,
                "success": True,
                "error": None,
            }
        )

    except ValueError as e:
        logger.warning(f"Account deletion request failed: {e}")
        return templates.TemplateResponse(
            "account-deletion.html",
            {
                "request": request,
                "email": email,
                "success": False,
                "error": str(e),
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in account deletion: {e}")
        return templates.TemplateResponse(
            "account-deletion.html",
            {
                "request": request,
                "email": email,
                "success": False,
                "error": "An unexpected error occurred. Please try again later.",
            }
        )
