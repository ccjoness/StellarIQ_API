# StellarIQ Backend API

A comprehensive FastAPI backend for a mobile stock and cryptocurrency tracking application with technical analysis capabilities.

## Features

- **Authentication**: JWT-based user authentication and authorization
- **Stock Data**: Real-time and historical stock data from Alpha Vantage API
- **Cryptocurrency Data**: Real-time crypto exchange rates and historical data
- **Technical Indicators**: RSI, MACD, Bollinger Bands, and Stochastic oscillators
- **Market Analysis**: Automated overbought/oversold analysis with configurable thresholds
- **Favorites Management**: User watchlists for stocks and cryptocurrencies
- **Chart Data**: Formatted data for mobile app charts with technical indicator overlays
- **Caching**: Redis-based caching with 15-minute TTL for optimal performance
- **Rate Limiting**: Built-in rate limiting for Alpha Vantage API calls

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database for user data and favorites
- **Redis**: In-memory caching for API responses
- **SQLAlchemy**: Python SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Alpha Vantage API**: Financial data provider

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (recommended) or pip
- PostgreSQL
- Redis
- Alpha Vantage API key (premium subscription recommended)

### Installation

#### Option 1: Using Poetry (Recommended)

**Quick Setup:**
```bash
git clone <repository-url>
cd StellarIQ_backend

# Linux/macOS
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh

# Windows
scripts\setup-dev.bat
```

**Manual Setup:**

1. Clone the repository:
```bash
git clone <repository-url>
cd StellarIQ_backend
```

2. Install Poetry if you haven't already:
```bash
# Linux/macOS/WSL
curl -sSL https://install.python-poetry.org | python3 -

# Windows PowerShell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

3. Install dependencies:
```bash
poetry install
```

4. Set up pre-commit hooks:
```bash
poetry run pre-commit install
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

6. Start services with Docker Compose:
```bash
make docker-up
# or: docker-compose up -d postgres redis
```

7. Run database migrations:
```bash
make upgrade
# or: poetry run alembic upgrade head
```

8. Start the application:
```bash
make run
# or: poetry run uvicorn main:app --reload
```

#### Option 2: Using pip

1. Clone the repository:
```bash
git clone <repository-url>
cd StellarIQ_backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start services with Docker Compose:
```bash
docker-compose up -d postgres redis
```

6. Run database migrations:
```bash
alembic upgrade head
```

7. Start the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get access token
- `GET /auth/me` - Get current user information
- `GET /auth/verify-token` - Verify token validity

### Stock Data
- `GET /stocks/search` - Search for stock symbols
- `GET /stocks/quote/{symbol}` - Get current stock quote
- `GET /stocks/daily/{symbol}` - Get daily stock data
- `GET /stocks/intraday/{symbol}` - Get intraday stock data

### Cryptocurrency Data
- `GET /crypto/popular` - Get popular cryptocurrency symbols
- `GET /crypto/rate/{from_currency}` - Get crypto exchange rate
- `GET /crypto/daily/{symbol}` - Get daily crypto data
- `GET /crypto/rates/multiple` - Get multiple crypto rates

### Technical Indicators
- `GET /indicators/rsi/{symbol}` - Get RSI indicator
- `GET /indicators/macd/{symbol}` - Get MACD indicator
- `GET /indicators/stoch/{symbol}` - Get Stochastic indicator
- `GET /indicators/bbands/{symbol}` - Get Bollinger Bands
- `GET /indicators/analysis/{symbol}` - Get comprehensive technical analysis

### Favorites Management
- `POST /favorites/` - Add symbol to favorites
- `DELETE /favorites/{symbol}` - Remove symbol from favorites
- `GET /favorites/` - Get user's favorites with quotes
- `GET /favorites/check/{symbol}` - Check if symbol is favorited
- `GET /favorites/stats` - Get favorites statistics

### Chart Data
- `GET /charts/candlestick/{symbol}` - Get candlestick chart data
- `GET /charts/comparison` - Get comparison chart for multiple symbols
- `GET /charts/multi/{symbols}` - Get multi-symbol chart data

### Market Analysis
- `GET /analysis/symbol/{symbol}` - Analyze single symbol
- `POST /analysis/bulk` - Bulk analysis of multiple symbols
- `GET /analysis/watchlist` - Analyze user's watchlist
- `GET /analysis/screener` - Market screener with conditions

## Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://stellariq:password@localhost:5432/stellariq_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=your_api_key_here

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cache
CACHE_TTL_SECONDS=900  # 15 minutes
```

## Technical Analysis

The API provides sophisticated technical analysis with configurable thresholds:

### Supported Indicators
- **RSI (Relative Strength Index)**: Default thresholds 70/30
- **MACD (Moving Average Convergence Divergence)**: Signal line crossovers
- **Stochastic Oscillator**: Default thresholds 80/20
- **Bollinger Bands**: Price position relative to bands

### Market Conditions
- **Overbought**: Multiple indicators suggest selling opportunity
- **Oversold**: Multiple indicators suggest buying opportunity
- **Neutral**: Mixed or inconclusive signals

## Caching Strategy

- All Alpha Vantage API responses are cached for 15 minutes
- Cache keys include all relevant parameters for accurate retrieval
- Automatic cache invalidation and cleanup
- Redis-based for high performance

## Rate Limiting

- Default: 5 requests per minute to Alpha Vantage API
- Configurable rate limiting with automatic queuing
- Request timing optimization for premium API limits

## Error Handling

- Comprehensive error responses with detailed messages
- Graceful degradation when external APIs are unavailable
- Proper HTTP status codes for all scenarios

## Security

- JWT-based authentication with configurable expiration
- Password hashing with bcrypt
- CORS configuration for mobile app integration
- Input validation and sanitization

## Testing

### Using Poetry (Recommended)
```bash
# Run tests
make test
# or: poetry run pytest

# Run tests with coverage
make test-cov
# or: poetry run pytest --cov=app --cov-report=html

# Run linting
make lint
# or: poetry run flake8 app tests && poetry run mypy app

# Format code
make format
# or: poetry run black app tests && poetry run isort app tests

# Run all checks
make check
```

### Using pip
```bash
pytest
```

## Development Commands

With Poetry and the included Makefile, you have access to convenient development commands:

```bash
make help              # Show all available commands
make install-dev       # Install all dependencies including dev tools
make run              # Start development server
make test             # Run tests
make test-cov         # Run tests with coverage
make lint             # Run linting (flake8, mypy)
make format           # Format code (black, isort)
make format-check     # Check code formatting
make migrate msg="description"  # Create new migration
make upgrade          # Apply database migrations
make docker-up        # Start Docker services
make docker-down      # Stop Docker services
make clean            # Clean cache and temp files
```

## Deployment

The application is containerized and ready for deployment:

```bash
docker-compose up --build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.
