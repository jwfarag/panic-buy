# Drop Detector
# =============
# Scan universe of stocks for price drops.
#
# TODO: Implement the following:
#
# @dataclass
# class DropEvent:
#     """A detected price drop event."""
#     # Fields:
#     # - ticker: str
#     # - drop_date: date
#     # - drop_pct: float - Percentage drop (negative)
#     # - open_price: float
#     # - close_price: float
#     # - high_price: float
#     # - low_price: float
#     # - volume: int
#     # - volume_ratio: float - vs average volume
#     # - days_of_drop: int - How many days the drop spans
#
# class DropDetector:
#     """Detect price drops in stock universe."""
#
#     def __init__(self, config: dict):
#         """
#         Initialize drop detector.
#
#         Args:
#             config: Configuration with:
#                 - min_drop_pct: Minimum drop to flag (e.g., 0.01 = 1%)
#                 - lookback_days: How far back to check
#                 - volume_spike_threshold: Min volume ratio to consider
#         """
#         pass
#
#     def scan(
#         self,
#         market_data: Dict[str, "TickerData"],
#         as_of_date: date = None
#     ) -> List[DropEvent]:
#         """
#         Scan all tickers for recent drops.
#
#         Args:
#             market_data: Dict of ticker -> OHLCV data
#             as_of_date: Date to check (default: today)
#
#         Returns:
#             List of detected drop events
#         """
#         pass
#
#     def detect_single(
#         self,
#         ticker: str,
#         ohlcv: "TickerData",
#         as_of_date: date = None
#     ) -> Optional[DropEvent]:
#         """
#         Check a single ticker for drops.
#
#         Drop detection logic:
#         1. Calculate return over lookback period
#         2. If return < -min_drop_pct, create DropEvent
#         3. Calculate supporting metrics (volume, etc.)
#         """
#         pass
#
#     def _calculate_drop(
#         self,
#         df: "pd.DataFrame",
#         end_date: date,
#         lookback_days: int
#     ) -> float:
#         """
#         Calculate drop percentage over lookback period.
#
#         Uses close-to-close return.
#         """
#         pass
#
#     def _calculate_volume_ratio(
#         self,
#         df: "pd.DataFrame",
#         date: date,
#         avg_period: int = 20
#     ) -> float:
#         """Calculate volume on drop date vs average."""
#         pass
#
#     def _is_multi_day_drop(
#         self,
#         df: "pd.DataFrame",
#         end_date: date
#     ) -> tuple:
#         """
#         Check if drop spans multiple days.
#
#         Returns:
#             (is_multi_day: bool, num_days: int)
#         """
#         pass
