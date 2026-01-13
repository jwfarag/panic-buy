# News Source Base Class
# ======================
# Abstract interface for news source scrapers.
#
# All news sources must implement this interface to ensure
# consistent behavior and data format across sources.
#
# TODO: Implement the following:
#
# class NewsArticle:
#     """Data class representing a single news article."""
#     # Fields:
#     # - id: str - Unique identifier
#     # - source: str - Source name (yahoo, google, seeking_alpha)
#     # - title: str - Article headline
#     # - content: str - Full article text (if available)
#     # - summary: str - Article summary/snippet
#     # - url: str - Link to original article
#     # - published_at: datetime - Publication timestamp
#     # - tickers: List[str] - Mentioned tickers (if tagged by source)
#     # - raw_data: dict - Original response data for debugging
#
# class NewsSource(ABC):
#     """Abstract base class for news sources."""
#
#     @abstractmethod
#     def fetch(self, lookback_hours: int) -> List[NewsArticle]:
#         """Fetch news articles from the last N hours."""
#         pass
#
#     @abstractmethod
#     def fetch_for_ticker(self, ticker: str, lookback_hours: int) -> List[NewsArticle]:
#         """Fetch news articles related to a specific ticker."""
#         pass
#
#     @property
#     @abstractmethod
#     def source_name(self) -> str:
#         """Return the name of this news source."""
#         pass
#
#     def _rate_limit(self) -> None:
#         """Apply rate limiting between requests."""
#         # TODO: Implement configurable rate limiting
#         pass
#
#     def _retry_with_backoff(self, func, max_retries: int = 3):
#         """Retry a function with exponential backoff."""
#         # TODO: Implement retry logic
#         pass
