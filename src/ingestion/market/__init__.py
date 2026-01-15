# Market Data Ingestion Submodule
# ===============================
# Fetchers for market price and volume data.
#
# Currently supported:
# - Yahoo Finance (via yfinance library)
#
# Data types fetched:
# - OHLCV (Open, High, Low, Close, Volume)
# - Historical data for backtesting
# - Real-time(ish) data for daily runs

from .base import OHLCV, TickerData, MarketDataSource
from .yahoo_market import YahooMarketData

__all__ = ['OHLCV', 'TickerData', 'MarketDataSource', 'YahooMarketData']
