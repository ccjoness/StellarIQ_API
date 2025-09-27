"""FastAPI application for StellarIQ backend."""

import logging
import os

import uvicorn
from fastapi import Depends, FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.routers import (
    analysis,
    auth,
    charts,
    crypto,
    favorites,
    indicators,
    notifications,
    stocks,
    )
from app.services.scheduler import scheduler
from app.core.database import get_db
from app.schemas.account_deletion import AccountDeletionRequest as AccountDeletionRequestSchema
from app.services.account_deletion import AccountDeletionService
from config import settings
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)
# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for StellarIQ mobile app - "
        "Stock and Cryptocurrency data with technical analysis"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

# Template directory
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(crypto.router)
app.include_router(indicators.router)
app.include_router(favorites.router)
app.include_router(charts.router)
app.include_router(analysis.router)
app.include_router(notifications.router)


@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    try:
        scheduler.start()
    except Exception as e:
        print(f"Failed to start scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on application shutdown."""
    try:
        scheduler.stop()
    except Exception as e:
        print(f"Failed to stop scheduler: {e}")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning API information."""
    return {
        "message": "StellarIQ Backend API",
        "version": settings.app_version,
        "status": "running",
        }


@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """Render the privacy policy page."""
    policy_effective_date = "2025-09-26"
    return templates.TemplateResponse("privacy-policy.html", {"request": request, "policy_effective_date": policy_effective_date})


@app.get("/account-deletion", response_class=HTMLResponse)
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


@app.post("/account-deletion", response_class=HTMLResponse)
async def submit_account_deletion(
        request: Request,
        email: EmailStr = Form(...),
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

        # Create the deletion request with proper email validation
        logger.info(f"Account deletion requested for email: {email}")
        request_data = AccountDeletionRequestSchema(
            email=email,
            reason=reason if reason else None,
            additional_info=additional_info if additional_info else None,
            confirm_deletion=confirm_deletion,
            )

        deletion_service = AccountDeletionService()
        # Get the base URL from the request
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        response = deletion_service.create_deletion_request(db, request_data, base_url)

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
        # Log the actual error for debugging
        logger.error(f"Account deletion error: {e}", exc_info=True)

        return templates.TemplateResponse(
            "account-deletion.html",
            {
                "request": request,
                "email": email,
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}",
                }
            )


@app.get("/account-deletion/confirm", response_class=HTMLResponse)
async def confirm_account_deletion(request: Request, token: str, db: Session = Depends(get_db)):
    """Confirm account deletion via email token."""
    try:
        deletion_service = AccountDeletionService()
        success = deletion_service.confirm_deletion_request(db, token)

        if success:
            return templates.TemplateResponse(
                "account-deletion-confirmed.html",
                {
                    "request": request,
                    "success": True,
                    "message": "Your account has been successfully deleted.",
                    }
                )
        else:
            return templates.TemplateResponse(
                "account-deletion-confirmed.html",
                {
                    "request": request,
                    "success": False,
                    "message": "Invalid or expired confirmation link. Please try submitting a new deletion request.",
                    }
                )

    except Exception as e:
        logger.error(f"Error confirming account deletion: {e}")
        return templates.TemplateResponse(
            "account-deletion-confirmed.html",
            {
                "request": request,
                "success": False,
                "message": "An error occurred while processing your request. Please contact support.",
                }
            )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        )
