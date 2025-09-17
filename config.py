from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://stellariq:password@localhost:5432/stellariq_db")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Alpha Vantage API
    alpha_vantage_api_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    alpha_vantage_rate_limit_per_minute: int = int(os.getenv("ALPHA_VANTAGE_RATE_LIMIT_PER_MINUTE", "5"))
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-here-change-this-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Application
    app_name: str = os.getenv("APP_NAME", "StellarIQ Backend")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = True #bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Cache
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "900"))  # 15 minutes
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields

settings = Settings()
