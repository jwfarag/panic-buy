# Massive (Polygon) News Source
# ==============================
# Uses Polygon.io API for article metadata and Trafilatura for content extraction.

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import trafilatura
from polygon import RESTClient

from .base import NewsArticle, NewsSource

logger = logging.getLogger(__name__)

# =============================================================================
# FUTURE IMPROVEMENTS (TODO)
# =============================================================================
# 1. Rate limiting: Trafilatura fetches are slower than API-only calls.
#    Consider adding configurable delays between requests.
#
# 2. Caching: Cache extracted text to avoid re-fetching the same URLs.
#    Could use a simple dict cache or something like diskcache.
#
# 3. Parallel extraction: Use asyncio or concurrent.futures for faster
#    extraction when fetching multiple articles.
#
# 4. Fallback: Keep NewsAPISource as fallback if Massive doesn't have
#    coverage for certain tickers or time ranges.
# =============================================================================


class MassiveNewsSource(NewsSource):
    """
    News source using Massive (Polygon) for article metadata
    and Trafilatura for content extraction.

    Polygon provides: id, title, url, published_at, tickers, publisher
    Trafilatura provides: full article text content
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[dict] = None):
        """
        Initialize the Massive news source.

        Args:
            api_key: Polygon API key. Falls back to POLYGON_API_KEY env var.
            config: Optional configuration dict.
        """
        super().__init__(config)
        self._api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Polygon API key required. Set POLYGON_API_KEY env var or pass api_key."
            )
        self._client = RESTClient(self._api_key)

    @property
    def source_name(self) -> str:
        return "massive"

    def fetch(self, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch general news articles (not ticker-specific).

        Note: Polygon's API is primarily ticker-based, so this returns
        an empty list. Use fetch_for_ticker() or fetch_for_tickers() instead.
        """
        logger.warning(
            "MassiveNewsSource.fetch() called without ticker. "
            "Use fetch_for_ticker() for best results."
        )
        return []

    def fetch_for_ticker(self, ticker: str, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch news articles for a specific ticker.

        Args:
            ticker: Stock symbol (e.g., "AAPL")
            lookback_hours: How many hours back to search

        Returns:
            List of NewsArticle objects with extracted content
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        logger.info(f"Fetching news for {ticker} from last {lookback_hours} hours")

        articles = []
        try:
            # Query Polygon for ticker news
            news_items = self._client.list_ticker_news(
                ticker=ticker,
                published_utc_gte=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                limit=100,
            )

            for item in news_items:
                article = self._process_news_item(item, default_ticker=ticker)
                if article:
                    articles.append(article)
                    self._rate_limit()

        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            raise

        logger.info(f"Fetched {len(articles)} articles for {ticker}")
        return articles

    def fetch_for_tickers(self, tickers: List[str], lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch news for multiple tickers.

        Args:
            tickers: List of stock symbols
            lookback_hours: How many hours back to search

        Returns:
            List of NewsArticle objects (may contain duplicates if article
            mentions multiple tickers)
        """
        all_articles = []
        seen_urls = set()

        for ticker in tickers:
            articles = self.fetch_for_ticker(ticker, lookback_hours)
            for article in articles:
                # Deduplicate by URL
                if article.url not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(article.url)

        return all_articles

    def _process_news_item(self, item, default_ticker: str) -> Optional[NewsArticle]:
        """
        Process a single news item from Polygon API.

        Args:
            item: News item from Polygon API
            default_ticker: Ticker to use if none provided in item

        Returns:
            NewsArticle with extracted content, or None if extraction fails
        """
        try:
            # Extract content using trafilatura
            content = self._extract_content(item.article_url)

            # Parse published timestamp
            published_at = self._parse_timestamp(item.published_utc)

            # Get tickers from item or use default
            tickers = list(item.tickers) if item.tickers else [default_ticker]

            # Get publisher name
            publisher_name = "unknown"
            if hasattr(item, "publisher") and item.publisher:
                publisher_name = getattr(item.publisher, "name", "unknown")

            return NewsArticle(
                id=item.id,
                source=publisher_name,
                title=item.title,
                url=item.article_url,
                published_at=published_at,
                content=content,
                summary=content[:500] if content else None,
                tickers=tickers,
                raw_data={
                    "polygon_id": item.id,
                    "amp_url": getattr(item, "amp_url", None),
                    "image_url": getattr(item, "image_url", None),
                },
            )
        except Exception as e:
            logger.warning(f"Failed to process news item: {e}")
            return None

    def _extract_content(self, url: str) -> Optional[str]:
        """
        Extract article text content using Trafilatura.

        Args:
            url: Article URL to fetch and extract

        Returns:
            Extracted text content, or None if extraction fails
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded)
                return content
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
        return None

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse Polygon timestamp string to datetime."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str

        # Polygon uses ISO format: "2024-01-15T10:30:00Z"
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return datetime.now(timezone.utc)
