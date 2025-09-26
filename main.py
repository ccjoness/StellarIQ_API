"""FastAPI application for StellarIQ backend."""

import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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
from config import settings
from fastapi.staticfiles import StaticFiles
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
