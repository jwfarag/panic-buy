# Market Filter
# =============
# Filter out drops that are correlated with market/sector moves.
#
# Key insight: We want IDIOSYNCRATIC drops (stock-specific),
# not drops caused by market-wide or sector-wide movements.
#
# Method:
# Idiosyncratic Return = Actual Return - (Beta × Market Return)
#
# If idiosyncratic return is small, the drop is market-driven.
# If idiosyncratic return is large, the drop is stock-specific.
#
# TODO: Implement the following:
#
# @dataclass
# class FilteredDrop:
#     """A drop event with market correlation info."""
#     # Fields:
#     # - drop: DropEvent - Original drop event
#     # - market_return: float - Market (SPY) return same period
#     # - sector_return: float - Sector ETF return same period
#     # - beta_market: float - Stock's beta to market
#     # - beta_sector: float - Stock's beta to sector
#     # - idiosyncratic_return_market: float - After market adjustment
#     # - idiosyncratic_return_sector: float - After sector adjustment
#     # - is_idiosyncratic: bool - Passed filter
#
# class MarketFilter:
#     """Filter market-correlated drops."""
#
#     def __init__(self, config: dict):
#         """
#         Initialize market filter.
#
#         Args:
#             config: Configuration from drop_thresholds.yaml
#                 - min_idiosyncratic_drop: Minimum to keep
#                 - high_market_volatility_threshold: Extra caution level
#                 - beta_lookback_days: For beta calculation
#         """
#         pass
#
#     def filter(
#         self,
#         drops: List[DropEvent],
#         market_data: Dict[str, "TickerData"],
#         ticker_sector_map: Dict[str, str]
#     ) -> List[FilteredDrop]:
#         """
#         Filter drops to keep only idiosyncratic ones.
#
#         Args:
#             drops: List of detected drops
#             market_data: Market data including SPY, sector ETFs
#             ticker_sector_map: Map of ticker -> sector ETF
#
#         Returns:
#             List of FilteredDrop with only idiosyncratic drops
#         """
#         pass
#
#     def calculate_idiosyncratic_return(
#         self,
#         stock_return: float,
#         market_return: float,
#         beta: float
#     ) -> float:
#         """
#         Calculate idiosyncratic (unexplained) return.
#
#         Formula:
#         Idiosyncratic = Actual - Expected
#         Expected = Beta × Market Return
#
#         Example:
#         Stock dropped 5%, Market dropped 4%, Beta = 1.2
#         Expected drop = 4% × 1.2 = 4.8%
#         Idiosyncratic = -5% - (-4.8%) = -0.2%
#         -> This is NOT a stock-specific drop
#         """
#         pass
#
#     def calculate_beta(
#         self,
#         stock_data: "pd.DataFrame",
#         benchmark_data: "pd.DataFrame",
#         lookback_days: int = 252
#     ) -> float:
#         """
#         Calculate beta of stock vs benchmark.
#
#         Beta = Cov(stock, benchmark) / Var(benchmark)
#         """
#         pass
#
#     def is_high_market_volatility(
#         self,
#         market_data: "TickerData",
#         date: date
#     ) -> bool:
#         """
#         Check if market is unusually volatile.
#
#         If market moved more than threshold, be extra
#         cautious about flagging individual stocks.
#         """
#         pass
#
#     def get_sector_etf(self, ticker: str) -> str:
#         """Get the sector ETF for a ticker."""
#         pass
