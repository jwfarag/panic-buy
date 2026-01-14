# Yahoo Finance News Scraper
# ==========================
# Fetches news from Yahoo Finance using yfinance library and web scraping.

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import yfinance as yf

from .base import NewsSource, NewsArticle

logger = logging.getLogger(__name__)


class YahooNewsSource(NewsSource):
    """Yahoo Finance news scraper."""

    BASE_URL = "https://finance.yahoo.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize Yahoo news scraper.

        Args:
            config: Configuration dict with rate limits, proxy settings, etc.
        """
        super().__init__(config)
        self._session = requests.Session()
        self._session.headers.update(self.HEADERS)

    def fetch(self, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch recent market news from Yahoo Finance main page.

        Args:
            lookback_hours: How many hours back to look

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching general Yahoo Finance news (lookback={lookback_hours}h)")
        articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        try:
            # Fetch main news page
            url = f"{self.BASE_URL}/news/"
            response = self._retry_with_backoff(
                self._session.get, url, timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')
            articles = self._parse_news_page(soup, cutoff_time)

            logger.info(f"Found {len(articles)} articles from Yahoo Finance news")
            return articles

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance news: {e}")
            return []

    def fetch_for_ticker(self, ticker: str, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch news for a specific ticker from Yahoo Finance.

        Uses yfinance's built-in news feature for reliability.

        Args:
            ticker: Stock symbol
            lookback_hours: How many hours back to look

        Returns:
            List of NewsArticle objects
        """
        logger.info(f"Fetching news for {ticker} (lookback={lookback_hours}h)")
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        articles = []

        try:
            # Use yfinance's news feature
            yf_ticker = yf.Ticker(ticker)
            news_data = yf_ticker.news

            if not news_data:
                logger.warning(f"No news found for {ticker}")
                return []

            for item in news_data:
                article = self._parse_yf_news_item(item, ticker)
                if article:
                    # Filter by time if we have a valid timestamp
                    if article.published_at:
                        pub_time = article.published_at
                        if pub_time.tzinfo is None:
                            pub_time = pub_time.replace(tzinfo=timezone.utc)
                        if pub_time >= cutoff_time:
                            articles.append(article)
                    else:
                        # Include if we can't determine time
                        articles.append(article)

            logger.info(f"Found {len(articles)} articles for {ticker}")
            return articles

        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []

        finally:
            self._rate_limit()

    def fetch_for_tickers(self, tickers: List[str], lookback_hours: int = 24) -> dict:
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

    @property
    def source_name(self) -> str:
        return "yahoo"

    def _parse_yf_news_item(self, item: dict, ticker: str) -> Optional[NewsArticle]:
        """Parse a single news item from yfinance."""
        try:
            # Handle both old and new yfinance API structures
            # New structure has data nested under 'content' key
            content = item.get('content', item)

            # Get URL from various possible locations
            url = ''
            if 'canonicalUrl' in content and content['canonicalUrl']:
                url = content['canonicalUrl'].get('url', '')
            elif 'clickThroughUrl' in content and content['clickThroughUrl']:
                url = content['clickThroughUrl'].get('url', '')
            elif 'link' in item:
                url = item.get('link', '')

            # Generate unique ID
            article_id = item.get('id') or content.get('id') or hashlib.md5(url.encode()).hexdigest()[:16]

            # Parse timestamp - try multiple fields
            published_at = None
            pub_date_str = content.get('pubDate')
            if pub_date_str:
                try:
                    published_at = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass

            if not published_at:
                pub_timestamp = item.get('providerPublishTime')
                if pub_timestamp:
                    published_at = datetime.fromtimestamp(pub_timestamp, tz=timezone.utc)

            if not published_at:
                published_at = datetime.now(timezone.utc)

            # Get title and summary
            title = content.get('title', '') or item.get('title', '')
            summary = content.get('summary', '') or content.get('description', '') or item.get('summary', '')

            # Get related tickers
            related_tickers = item.get('relatedTickers', [])
            if ticker not in related_tickers:
                related_tickers = [ticker] + related_tickers

            return NewsArticle(
                id=article_id,
                source=self.source_name,
                title=title,
                url=url,
                published_at=published_at,
                summary=summary,
                tickers=related_tickers,
                raw_data=item,
            )

        except Exception as e:
            logger.warning(f"Error parsing news item: {e}")
            return None

    def _parse_news_page(self, soup: BeautifulSoup, cutoff_time: datetime) -> List[NewsArticle]:
        """Parse news articles from a Yahoo Finance news page."""
        articles = []

        # Find news article containers
        # Note: Yahoo Finance page structure may change; this is a best-effort implementation
        news_items = soup.find_all('li', class_='js-stream-content')

        for item in news_items:
            try:
                # Find article link
                link_tag = item.find('a', href=True)
                if not link_tag:
                    continue

                url = link_tag.get('href', '')
                if not url.startswith('http'):
                    url = urljoin(self.BASE_URL, url)

                # Find title
                title_tag = item.find('h3') or item.find('h2')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)

                if not title:
                    continue

                # Generate ID from URL
                article_id = hashlib.md5(url.encode()).hexdigest()[:16]

                # Find summary if available
                summary_tag = item.find('p')
                summary = summary_tag.get_text(strip=True) if summary_tag else None

                article = NewsArticle(
                    id=article_id,
                    source=self.source_name,
                    title=title,
                    url=url,
                    published_at=datetime.now(timezone.utc),  # Approximate
                    summary=summary,
                    tickers=[],  # Would need entity resolution to determine
                )
                articles.append(article)

            except Exception as e:
                logger.warning(f"Error parsing news item: {e}")
                continue

        return articles
