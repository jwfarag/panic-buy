# Tests for Market Data Module
# ============================

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
import pandas as pd

from src.ingestion.market.base import OHLCV, TickerData, MarketDataSource
from src.ingestion.market.yahoo_market import YahooMarketData


class TestOHLCV:
    """Tests for OHLCV dataclass."""

    def test_ohlcv_creation(self):
        """Test creating an OHLCV bar."""
        bar = OHLCV(
            timestamp=datetime(2024, 1, 15, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000,
            adjusted_close=103.0
        )
        assert bar.open == 100.0
        assert bar.high == 105.0
        assert bar.low == 99.0
        assert bar.close == 103.0
        assert bar.volume == 1000000
        assert bar.adjusted_close == 103.0

    def test_ohlcv_daily_return(self):
        """Test daily return calculation."""
        bar = OHLCV(
            timestamp=datetime(2024, 1, 15),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000
        )
        assert bar.daily_return == pytest.approx(0.02, rel=1e-6)

    def test_ohlcv_daily_return_zero_open(self):
        """Test daily return with zero open price."""
        bar = OHLCV(
            timestamp=datetime(2024, 1, 15),
            open=0.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000
        )
        assert bar.daily_return is None


class TestTickerData:
    """Tests for TickerData dataclass."""

    def test_ticker_data_creation(self):
        """Test creating TickerData."""
        bars = [
            OHLCV(datetime(2024, 1, 15), 100.0, 105.0, 99.0, 103.0, 1000000),
            OHLCV(datetime(2024, 1, 16), 103.0, 107.0, 102.0, 106.0, 1200000),
        ]
        data = TickerData(ticker="AAPL", bars=bars, metadata={"sector": "Technology"})

        assert data.ticker == "AAPL"
        assert len(data.bars) == 2
        assert data.metadata["sector"] == "Technology"

    def test_ticker_data_latest_bar(self):
        """Test getting latest bar."""
        bars = [
            OHLCV(datetime(2024, 1, 15), 100.0, 105.0, 99.0, 103.0, 1000000),
            OHLCV(datetime(2024, 1, 16), 103.0, 107.0, 102.0, 106.0, 1200000),
        ]
        data = TickerData(ticker="AAPL", bars=bars)

        assert data.latest_bar.close == 106.0
        assert data.latest_close == 106.0

    def test_ticker_data_empty_bars(self):
        """Test empty bars handling."""
        data = TickerData(ticker="AAPL", bars=[])

        assert data.latest_bar is None
        assert data.latest_close is None

    def test_ticker_data_to_dataframe(self):
        """Test converting to DataFrame."""
        bars = [
            OHLCV(datetime(2024, 1, 15), 100.0, 105.0, 99.0, 103.0, 1000000, 103.0),
            OHLCV(datetime(2024, 1, 16), 103.0, 107.0, 102.0, 106.0, 1200000, 106.0),
        ]
        data = TickerData(ticker="AAPL", bars=bars)
        df = data.to_dataframe()

        assert len(df) == 2
        assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume', 'adjusted_close']
        assert df['close'].iloc[0] == 103.0
        assert df['close'].iloc[1] == 106.0


class TestYahooMarketData:
    """Tests for YahooMarketData class."""

    def test_source_name(self):
        """Test source name property."""
        provider = YahooMarketData()
        assert provider.source_name == "yahoo"

    @pytest.mark.integration
    def test_fetch_ohlcv_real(self):
        """Integration test: fetch real data from Yahoo Finance."""
        provider = YahooMarketData()
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        data = provider.fetch_ohlcv("AAPL", start_date, end_date)

        assert data.ticker == "AAPL"
        assert len(data.bars) > 0
        # Verify bar structure
        bar = data.bars[0]
        assert bar.open > 0
        assert bar.high >= bar.low
        assert bar.close > 0
        assert bar.volume >= 0

    @pytest.mark.integration
    def test_fetch_batch_real(self):
        """Integration test: fetch multiple tickers."""
        provider = YahooMarketData()
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        tickers = ["AAPL", "MSFT"]
        results = provider.fetch_batch(tickers, start_date, end_date)

        assert "AAPL" in results
        assert "MSFT" in results
        assert len(results["AAPL"].bars) > 0
        assert len(results["MSFT"].bars) > 0

    @pytest.mark.integration
    def test_get_latest_price_real(self):
        """Integration test: get latest price."""
        provider = YahooMarketData()
        price = provider.get_latest_price("AAPL")

        assert price > 0
        assert price < 10000  # Sanity check

    @pytest.mark.integration
    def test_get_ticker_info_real(self):
        """Integration test: get ticker info."""
        provider = YahooMarketData()
        info = provider.get_ticker_info("AAPL")

        assert "sector" in info
        assert "market_cap" in info
        assert info["sector"] == "Technology"

    def test_dataframe_to_bars(self):
        """Test DataFrame to bars conversion."""
        provider = YahooMarketData()

        # Create test DataFrame in yfinance format
        df = pd.DataFrame({
            'Open': [100.0, 103.0],
            'High': [105.0, 107.0],
            'Low': [99.0, 102.0],
            'Close': [103.0, 106.0],
            'Volume': [1000000, 1200000],
            'Adj Close': [103.0, 106.0]
        }, index=pd.to_datetime(['2024-01-15', '2024-01-16']))

        bars = provider._dataframe_to_bars(df)

        assert len(bars) == 2
        assert bars[0].open == 100.0
        assert bars[0].close == 103.0
        assert bars[1].close == 106.0


class TestMarketDataSourceInterface:
    """Test that YahooMarketData properly implements the interface."""

    def test_implements_interface(self):
        """Verify YahooMarketData implements MarketDataSource."""
        provider = YahooMarketData()

        assert hasattr(provider, 'fetch_ohlcv')
        assert hasattr(provider, 'fetch_batch')
        assert hasattr(provider, 'get_latest_price')
        assert hasattr(provider, 'source_name')
        assert callable(provider.fetch_ohlcv)
        assert callable(provider.fetch_batch)
        assert callable(provider.get_latest_price)


# Run integration tests only when explicitly requested
# pytest -m integration tests/test_market_data.py
