# News Source Base Class
# ======================
# Abstract interface for news source scrapers.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Data class representing a single news article."""
    id: str
    source: str
    title: str
    url: str
    published_at: datetime
    content: Optional[str] = None
    summary: Optional[str] = None
    tickers: List[str] = field(default_factory=list)
    raw_data: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'source': self.source,
            'title': self.title,
            'url': self.url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'content': self.content,
            'summary': self.summary,
            'tickers': self.tickers,
        }


class NewsSource(ABC):
    """Abstract base class for news sources."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize news source.

        Args:
            config: Configuration dict with rate limits, proxy settings, etc.
        """
        self.config = config or {}
        self._rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        self._max_retries = self.config.get('max_retries', 3)

    @abstractmethod
    def fetch(self, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch news articles from the last N hours.

        Args:
            lookback_hours: How many hours back to look

        Returns:
            List of NewsArticle objects
        """
        pass

    @abstractmethod
    def fetch_for_ticker(self, ticker: str, lookback_hours: int = 24) -> List[NewsArticle]:
        """
        Fetch news articles related to a specific ticker.

        Args:
            ticker: Stock symbol
            lookback_hours: How many hours back to look

        Returns:
            List of NewsArticle objects
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this news source."""
        pass

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        time.sleep(self._rate_limit_delay)

    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to func

        Returns:
            Result of func

        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        for attempt in range(self._max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                wait_time = (2 ** attempt) * self._rate_limit_delay
                logger.warning(
                    f"Attempt {attempt + 1}/{self._max_retries} failed: {e}. "
                    f"Waiting {wait_time}s before retry."
                )
                time.sleep(wait_time)

        raise last_exception
