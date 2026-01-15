# Ingestion Module
# ================
# Responsible for fetching news and market data from external sources.
#
# Submodules:
# - news/: News source scrapers (Yahoo, Google, Seeking Alpha)
# - market/: Market data fetchers (Yahoo Finance)
#
# Key responsibilities:
# - Fetch news articles within configured lookback window
# - Fetch OHLCV data for universe of tickers
# - Handle rate limiting and retries
# - Cache data appropriately
# - Normalize data formats across sources
