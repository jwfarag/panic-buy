# Market Data Source Base Class
# =============================
# Abstract interface for market data providers.
#
# TODO: Implement the following:
#
# @dataclass
# class OHLCV:
#     """Single OHLCV bar."""
#     # Fields:
#     # - timestamp: datetime
#     # - open: float
#     # - high: float
#     # - low: float
#     # - close: float
#     # - volume: int
#     # - adjusted_close: float (optional, for splits/dividends)
#
# @dataclass
# class TickerData:
#     """Market data for a single ticker."""
#     # Fields:
#     # - ticker: str
#     # - bars: List[OHLCV]
#     # - metadata: dict (company name, sector, etc.)
#
# class MarketDataSource(ABC):
#     """Abstract base class for market data providers."""
#
#     @abstractmethod
#     def fetch_ohlcv(
#         self,
#         ticker: str,
#         start_date: date,
#         end_date: date,
#         interval: str = "1d"
#     ) -> TickerData:
#         """
#         Fetch OHLCV data for a ticker.
#
#         Args:
#             ticker: Stock symbol
#             start_date: Start of date range
#             end_date: End of date range
#             interval: Bar interval (1d, 1h, etc.)
#
#         Returns:
#             TickerData with OHLCV bars
#         """
#         pass
#
#     @abstractmethod
#     def fetch_batch(
#         self,
#         tickers: List[str],
#         start_date: date,
#         end_date: date,
#         interval: str = "1d"
#     ) -> Dict[str, TickerData]:
#         """Fetch OHLCV data for multiple tickers."""
#         pass
#
#     @abstractmethod
#     def get_latest_price(self, ticker: str) -> float:
#         """Get most recent price for a ticker."""
#         pass
#
#     @property
#     @abstractmethod
#     def source_name(self) -> str:
#         """Return the name of this data source."""
#         pass
