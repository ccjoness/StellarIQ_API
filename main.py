from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from app.routers import auth, stocks, crypto, indicators, favorites, charts, analysis
import uvicorn
import logging

logger = logging.getLogger(__name__)
# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for StellarIQ mobile app - Stock and Cryptocurrency data with technical analysis",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(crypto.router)
app.include_router(indicators.router)
app.include_router(favorites.router)
app.include_router(charts.router)
app.include_router(analysis.router)

@app.get("/")
async def root():
    return {
        "message": "StellarIQ Backend API",
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
