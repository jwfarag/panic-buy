# Market Data Source Base Class
# =============================
# Abstract interface for market data providers.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional


@dataclass
class OHLCV:
    """Single OHLCV bar."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None

    @property
    def daily_return(self) -> Optional[float]:
        """Calculate daily return based on open and close."""
        if self.open and self.open != 0:
            return (self.close - self.open) / self.open
        return None


@dataclass
class TickerData:
    """Market data for a single ticker."""
    ticker: str
    bars: List[OHLCV]
    metadata: Dict = field(default_factory=dict)

    @property
    def latest_bar(self) -> Optional[OHLCV]:
        """Get the most recent bar."""
        return self.bars[-1] if self.bars else None

    @property
    def latest_close(self) -> Optional[float]:
        """Get the most recent close price."""
        return self.bars[-1].close if self.bars else None

    def to_dataframe(self):
        """Convert to pandas DataFrame."""
        import pandas as pd

        if not self.bars:
            return pd.DataFrame()

        data = {
            'timestamp': [b.timestamp for b in self.bars],
            'open': [b.open for b in self.bars],
            'high': [b.high for b in self.bars],
            'low': [b.low for b in self.bars],
            'close': [b.close for b in self.bars],
            'volume': [b.volume for b in self.bars],
            'adjusted_close': [b.adjusted_close for b in self.bars],
        }
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df


class MarketDataSource(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def fetch_ohlcv(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> TickerData:
        """
        Fetch OHLCV data for a ticker.

        Args:
            ticker: Stock symbol
            start_date: Start of date range
            end_date: End of date range
            interval: Bar interval (1d, 1h, etc.)

        Returns:
            TickerData with OHLCV bars
        """
        pass

    @abstractmethod
    def fetch_batch(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> Dict[str, TickerData]:
        """Fetch OHLCV data for multiple tickers."""
        pass

    @abstractmethod
    def get_latest_price(self, ticker: str) -> float:
        """Get most recent price for a ticker."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this data source."""
        pass
