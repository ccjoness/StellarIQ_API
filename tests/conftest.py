import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from main import app

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client() -> Generator:
    """Create a test client."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client."""
    # Register a test user
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    
    # Login to get token
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Add authorization header to client
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    return client

# Sample data for testing
@pytest.fixture
def sample_stock_quote():
    """Sample stock quote data."""
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "02. open": "150.00",
            "03. high": "155.00",
            "04. low": "149.00",
            "05. price": "152.50",
            "06. volume": "1000000",
            "07. latest trading day": "2023-12-01",
            "08. previous close": "151.00",
            "09. change": "1.50",
            "10. change percent": "0.99%"
        }
    }

@pytest.fixture
def sample_time_series():
    """Sample time series data."""
    return {
        "Meta Data": {
            "1. Information": "Daily Prices",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": "2023-12-01",
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": {
            "2023-12-01": {
                "1. open": "150.00",
                "2. high": "155.00",
                "3. low": "149.00",
                "4. close": "152.50",
                "5. volume": "1000000"
            },
            "2023-11-30": {
                "1. open": "148.00",
                "2. high": "151.00",
                "3. low": "147.00",
                "4. close": "150.00",
                "5. volume": "900000"
            }
        }
    }

@pytest.fixture
def sample_rsi_data():
    """Sample RSI indicator data."""
    return {
        "Meta Data": {
            "1: Symbol": "AAPL",
            "2: Indicator": "Relative Strength Index (RSI)",
            "3: Last Refreshed": "2023-12-01",
            "4: Interval": "daily",
            "5: Time Period": 14,
            "6: Series Type": "close",
            "7: Time Zone": "US/Eastern"
        },
        "Technical Analysis: RSI": {
            "2023-12-01": {
                "RSI": "65.5000"
            },
            "2023-11-30": {
                "RSI": "62.3000"
            }
        }
    }
