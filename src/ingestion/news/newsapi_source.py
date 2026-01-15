# NewsAPI.ai News Source
# ======================
# Fetches news articles using the NewsAPI.ai (Event Registry) API.
# Provides full article text, unlike scrapers that only get summaries.

import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from eventregistry import (
    EventRegistry,
    QueryArticlesIter,
    QueryItems,
    ReturnInfo,
    ArticleInfoFlags,
)

from .base import NewsSource, NewsArticle

logger = logging.getLogger(__name__)


class NewsAPISource(NewsSource):
    """NewsAPI.ai (Event Registry) news source.

    Provides access to full article text from thousands of news sources
    including Reuters, Bloomberg, WSJ, and more.

    Requires NEWSAPI_AI_KEY environment variable to be set.
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize NewsAPI.ai source.

        Args:
            config: Configuration dict. Supported keys:
                - api_key: NewsAPI.ai API key (or use NEWSAPI_AI_KEY env var)
                - max_items: Max articles per query (default: 100)
                - rate_limit_delay: Delay between requests (default: 0.5)
        """
        super().__init__(config)

        api_key = (config or {}).get('api_key') or os.environ.get('NEWSAPI_AI_KEY')
        if not api_key:
            raise ValueError(
                "NewsAPI.ai API key required. Set NEWSAPI_AI_KEY environment "
                "variable or pass api_key in config."
            )

        # Debug: log key info to help diagnose authentication issues
        key_source = "config" if (config or {}).get('api_key') else "NEWSAPI_AI_KEY env var"
        original_len = len(api_key)
        api_key = api_key.strip()  # Remove any leading/trailing whitespace
        stripped_len = len(api_key)

        logger.info(f"NewsAPI.ai key loaded from: {key_source}")
        logger.info(f"Key prefix: {api_key[:4]}... (length: {stripped_len})")
        if original_len != stripped_len:
            logger.warning(f"Key had whitespace stripped ({original_len} -> {stripped_len} chars)")

        self._er = EventRegistry(apiKey=api_key)
        self._max_items = (config or {}).get('max_items', 100)
        self._rate_limit_delay = (config or {}).get('rate_limit_delay', 0.5)

    @property
    def source_name(self) -> str:
        return "newsapi"

    def fetch(self, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch recent financial/market news.

        Args:
            lookback_hours: How many hours back to look

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching general market news (lookback={lookback_hours}h)")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=lookback_hours)

        try:
            query = QueryArticlesIter(
                keywords=QueryItems.OR(["stock market", "financial markets", "wall street"]),
                dateStart=start_date.strftime("%Y-%m-%d"),
                dateEnd=end_date.strftime("%Y-%m-%d"),
                lang="eng",
            )

            articles = self._execute_query(query)
            logger.info(f"Found {len(articles)} general market articles")
            return articles

        except Exception as e:
            logger.error(f"Error fetching general news: {e}")
            return []

    def fetch_for_ticker(self, ticker: str, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch news for a specific ticker/company.

        Args:
            ticker: Stock symbol (e.g., "AAPL")
            lookback_hours: How many hours back to look

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching news for {ticker} (lookback={lookback_hours}h)")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=lookback_hours)

        try:
            # Search by ticker symbol and common variations
            query = QueryArticlesIter(
                keywords=ticker,
                dateStart=start_date.strftime("%Y-%m-%d"),
                dateEnd=end_date.strftime("%Y-%m-%d"),
                lang="eng",
            )

            articles = self._execute_query(query, default_ticker=ticker)
            logger.info(f"Found {len(articles)} articles for {ticker}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []

        finally:
            self._rate_limit()

    def fetch_for_company(
        self,
        company_name: str,
        ticker: str,
        lookback_hours: int = 24
    ) -> List[NewsArticle]:
        """
        Fetch news using company name (often yields better results than ticker).

        Args:
            company_name: Full company name (e.g., "Apple Inc.")
            ticker: Stock symbol to tag results with
            lookback_hours: How many hours back to look

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching news for {company_name} ({ticker}) (lookback={lookback_hours}h)")

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=lookback_hours)

        try:
            # Search by company name for better coverage
            query = QueryArticlesIter(
                keywords=company_name,
                dateStart=start_date.strftime("%Y-%m-%d"),
                dateEnd=end_date.strftime("%Y-%m-%d"),
                lang="eng",
            )

            articles = self._execute_query(query, default_ticker=ticker)
            logger.info(f"Found {len(articles)} articles for {company_name}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching news for {company_name}: {e}")
            return []

        finally:
            self._rate_limit()

    def fetch_for_tickers(
        self,
        tickers: List[str],
        lookback_hours: int = 24
    ) -> Dict[str, List[NewsArticle]]:
        """
        Fetch news for multiple tickers.

        Args:
            tickers: List of stock symbols
            lookback_hours: How many hours back to look

        Returns:
            Dict mapping ticker to list of NewsArticle objects
        """
        results = {}
        for ticker in tickers:
            results[ticker] = self.fetch_for_ticker(ticker, lookback_hours)
        return results

    def _execute_query(
        self,
        query: QueryArticlesIter,
        default_ticker: Optional[str] = None
    ) -> List[NewsArticle]:
        """
        Execute a query and convert results to NewsArticle objects.

        Args:
            query: QueryArticlesIter instance
            default_ticker: Ticker to assign if none extracted

        Returns:
            List of NewsArticle objects
        """
        articles = []

        # Configure what info to return
        return_info = ReturnInfo(
            articleInfo=ArticleInfoFlags(
                body=True,
                title=True,
                date=True,
                time=True,
                url=True,
                source=True,
            )
        )

        count = 0
        for item in query.execQuery(self._er, returnInfo=return_info):
            if count >= self._max_items:
                break

            article = self._parse_article(item, default_ticker)
            if article:
                articles.append(article)
                count += 1

        return articles

    def _parse_article(
        self,
        item: dict,
        default_ticker: Optional[str] = None
    ) -> Optional[NewsArticle]:
        """
        Parse a single article from NewsAPI.ai response.

        Args:
            item: Raw article dict from API
            default_ticker: Ticker to assign if none extracted

        Returns:
            NewsArticle object or None if parsing fails
        """
        try:
            # Extract article ID
            article_id = item.get('uri') or hashlib.md5(
                item.get('url', '').encode()
            ).hexdigest()[:16]

            # Parse publication datetime
            published_at = None
            date_str = item.get('date')
            time_str = item.get('time', '00:00:00')
            if date_str:
                try:
                    dt_str = f"{date_str}T{time_str}"
                    published_at = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)

            # Extract source name
            source_info = item.get('source', {})
            source_name = source_info.get('title', 'unknown') if isinstance(source_info, dict) else 'unknown'

            # Build tickers list
            tickers = []
            if default_ticker:
                tickers.append(default_ticker)

            return NewsArticle(
                id=article_id,
                source=source_name,
                title=item.get('title', ''),
                url=item.get('url', ''),
                published_at=published_at,
                content=item.get('body'),  # Full article text!
                summary=item.get('body', '')[:500] if item.get('body') else None,
                tickers=tickers,
                raw_data=item,
            )

        except Exception as e:
            logger.warning(f"Error parsing article: {e}")
            return None
