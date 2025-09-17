import pytest

from app.utils.data_parser import DataParser


def test_parse_stock_quote():
    """Test parsing stock quote data."""
    sample_data = {
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
            "10. change percent": "0.99%",
        }
    }

    quote = DataParser.parse_stock_quote(sample_data)

    assert quote.symbol == "AAPL"
    assert quote.open == 150.00
    assert quote.high == 155.00
    assert quote.low == 149.00
    assert quote.price == 152.50
    assert quote.volume == 1000000
    assert quote.latest_trading_day == "2023-12-01"
    assert quote.previous_close == 151.00
    assert quote.change == 1.50
    assert quote.change_percent == "0.99%"


def test_parse_search_results():
    """Test parsing search results."""
    sample_data = {
        "bestMatches": [
            {
                "1. symbol": "AAPL",
                "2. name": "Apple Inc.",
                "3. type": "Equity",
                "4. region": "United States",
                "5. marketOpen": "09:30",
                "6. marketClose": "16:00",
                "7. timezone": "UTC-04",
                "8. currency": "USD",
                "9. matchScore": "1.0000",
            },
            {
                "1. symbol": "AAPLW",
                "2. name": "Apple Inc. Warrant",
                "3. type": "Warrant",
                "4. region": "United States",
                "5. marketOpen": "09:30",
                "6. marketClose": "16:00",
                "7. timezone": "UTC-04",
                "8. currency": "USD",
                "9. matchScore": "0.8000",
            },
        ]
    }

    results = DataParser.parse_search_results(sample_data)

    assert len(results) == 2
    assert results[0].symbol == "AAPL"
    assert results[0].name == "Apple Inc."
    assert results[0].type == "Equity"
    assert results[0].match_score == 1.0
    assert results[1].symbol == "AAPLW"
    assert results[1].match_score == 0.8


def test_parse_time_series():
    """Test parsing time series data."""
    sample_data = {
        "Time Series (Daily)": {
            "2023-12-01": {
                "1. open": "150.00",
                "2. high": "155.00",
                "3. low": "149.00",
                "4. close": "152.50",
                "5. volume": "1000000",
            },
            "2023-11-30": {
                "1. open": "148.00",
                "2. high": "151.00",
                "3. low": "147.00",
                "4. close": "150.00",
                "5. volume": "900000",
            },
        }
    }

    results = DataParser.parse_time_series(sample_data, "Time Series (Daily)")

    assert len(results) == 2
    # Should be sorted by timestamp (most recent first)
    assert results[0].timestamp == "2023-12-01"
    assert results[0].open == 150.00
    assert results[0].close == 152.50
    assert results[1].timestamp == "2023-11-30"


def test_parse_crypto_exchange_rate():
    """Test parsing crypto exchange rate."""
    sample_data = {
        "Realtime Currency Exchange Rate": {
            "1. From_Currency Code": "BTC",
            "2. From_Currency Name": "Bitcoin",
            "3. To_Currency Code": "USD",
            "4. To_Currency Name": "United States Dollar",
            "5. Exchange Rate": "45000.00",
            "6. Last Refreshed": "2023-12-01 10:00:00",
            "7. Time Zone": "UTC",
            "8. Bid Price": "44950.00",
            "9. Ask Price": "45050.00",
        }
    }

    rate = DataParser.parse_crypto_exchange_rate(sample_data)

    assert rate.from_currency_code == "BTC"
    assert rate.from_currency_name == "Bitcoin"
    assert rate.to_currency_code == "USD"
    assert rate.exchange_rate == 45000.00
    assert rate.bid_price == 44950.00
    assert rate.ask_price == 45050.00


def test_get_metadata():
    """Test extracting metadata."""
    sample_data = {
        "Meta Data": {
            "1. Information": "Daily Prices",
            "2. Symbol": "AAPL",
            "3. Last Refreshed": "2023-12-01",
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern",
        }
    }

    metadata = DataParser.get_metadata(sample_data)

    assert metadata["symbol"] == "AAPL"
    assert metadata["last_refreshed"] == "2023-12-01"
    assert metadata["time_zone"] == "US/Eastern"


def test_parse_invalid_data():
    """Test parsing invalid data raises appropriate errors."""
    with pytest.raises(ValueError):
        DataParser.parse_stock_quote({})

    with pytest.raises(ValueError):
        DataParser.parse_search_results({})

    with pytest.raises(ValueError):
        DataParser.parse_time_series({}, "Invalid Key")
