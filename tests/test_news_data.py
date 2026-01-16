# Tests for News Data Module
# ==========================

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ingestion.news.base import NewsArticle, NewsSource
from src.ingestion.news.massive_source import MassiveNewsSource
from src.ingestion.news.newsapi_source import NewsAPISource


class TestNewsArticle:
    """Tests for NewsArticle dataclass."""

    def test_news_article_creation(self):
        """Test creating a NewsArticle."""
        article = NewsArticle(
            id="abc123",
            source="reuters",
            title="Apple Announces New Product",
            url="https://example.com/article",
            published_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            summary="Apple unveiled a new product today.",
            content="Full article content here...",
            tickers=["AAPL"],
        )

        assert article.id == "abc123"
        assert article.source == "reuters"
        assert article.title == "Apple Announces New Product"
        assert article.url == "https://example.com/article"
        assert article.published_at.year == 2024
        assert "AAPL" in article.tickers
        assert article.content == "Full article content here..."

    def test_news_article_to_dict(self):
        """Test converting NewsArticle to dict."""
        article = NewsArticle(
            id="abc123",
            source="bloomberg",
            title="Test Article",
            url="https://example.com",
            published_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            tickers=["AAPL", "MSFT"],
        )

        result = article.to_dict()

        assert result["id"] == "abc123"
        assert result["source"] == "bloomberg"
        assert result["title"] == "Test Article"
        assert result["tickers"] == ["AAPL", "MSFT"]
        assert "2024-01-15" in result["published_at"]

    def test_news_article_defaults(self):
        """Test NewsArticle with default values."""
        article = NewsArticle(
            id="test",
            source="newsapi",
            title="Test",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
        )

        assert article.content is None
        assert article.summary is None
        assert article.tickers == []
        assert article.raw_data == {}


class TestNewsAPISource:
    """Tests for NewsAPISource class."""

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_source_name(self, mock_er):
        """Test source name property."""
        source = NewsAPISource()
        assert source.source_name == "newsapi"

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_initialization_defaults(self, mock_er):
        """Test default initialization."""
        source = NewsAPISource()
        assert source._rate_limit_delay == 0.5
        assert source._max_items == 100

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_initialization_custom_config(self, mock_er):
        """Test initialization with custom config."""
        config = {"rate_limit_delay": 2.0, "max_items": 50}
        source = NewsAPISource(config)
        assert source._rate_limit_delay == 2.0
        assert source._max_items == 50

    def test_initialization_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove NEWSAPI_AI_KEY if it exists
            os.environ.pop('NEWSAPI_AI_KEY', None)
            with pytest.raises(ValueError, match="API key required"):
                NewsAPISource()

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_initialization_with_config_api_key(self, mock_er):
        """Test initialization with API key in config."""
        # Clear env var
        with patch.dict(os.environ, {}, clear=True):
            config = {"api_key": "config_key"}
            source = NewsAPISource(config)
            mock_er.assert_called_once_with(apiKey="config_key")

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_parse_article(self, mock_er):
        """Test parsing an article from NewsAPI.ai response."""
        source = NewsAPISource()

        mock_item = {
            "uri": "article-123",
            "title": "Test Article Title",
            "url": "https://example.com/article",
            "date": "2024-01-15",
            "time": "10:30:00",
            "body": "This is the full article content. It contains detailed information.",
            "source": {"title": "Reuters"},
        }

        article = source._parse_article(mock_item, "AAPL")

        assert article is not None
        assert article.id == "article-123"
        assert article.title == "Test Article Title"
        assert article.url == "https://example.com/article"
        assert article.content == "This is the full article content. It contains detailed information."
        assert article.source == "Reuters"
        assert "AAPL" in article.tickers
        assert article.published_at is not None
        assert article.published_at.year == 2024

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_parse_article_missing_fields(self, mock_er):
        """Test parsing article with missing fields."""
        source = NewsAPISource()

        mock_item = {
            "title": "Minimal Article",
            "url": "https://example.com",
        }

        article = source._parse_article(mock_item, "AAPL")

        assert article is not None
        assert article.title == "Minimal Article"
        assert "AAPL" in article.tickers
        assert article.content is None

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_parse_article_generates_id_from_url(self, mock_er):
        """Test that article ID is generated from URL if uri missing."""
        source = NewsAPISource()

        mock_item = {
            "title": "Test Article",
            "url": "https://example.com/unique-article",
        }

        article = source._parse_article(mock_item, "AAPL")

        assert article is not None
        assert article.id  # Should have generated an ID
        assert len(article.id) > 0

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    @patch('src.ingestion.news.newsapi_source.QueryArticlesIter')
    def test_fetch_for_ticker(self, mock_query, mock_er):
        """Test fetching articles for a ticker."""
        source = NewsAPISource()

        # Mock the query execution
        mock_query_instance = MagicMock()
        mock_query.return_value = mock_query_instance
        mock_query_instance.execQuery.return_value = iter([
            {
                "uri": "article-1",
                "title": "Apple News",
                "url": "https://example.com/1",
                "date": "2024-01-15",
                "time": "10:00:00",
                "body": "Article about Apple.",
                "source": {"title": "Reuters"},
            }
        ])

        articles = source.fetch_for_ticker("AAPL", lookback_hours=24)

        assert isinstance(articles, list)
        assert len(articles) == 1
        assert articles[0].title == "Apple News"
        assert "AAPL" in articles[0].tickers

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    @patch('src.ingestion.news.newsapi_source.QueryArticlesIter')
    def test_fetch_for_tickers(self, mock_query, mock_er):
        """Test fetching articles for multiple tickers."""
        source = NewsAPISource()

        # Mock returns empty for simplicity
        mock_query_instance = MagicMock()
        mock_query.return_value = mock_query_instance
        mock_query_instance.execQuery.return_value = iter([])

        results = source.fetch_for_tickers(["AAPL", "MSFT"], lookback_hours=24)

        assert "AAPL" in results
        assert "MSFT" in results
        assert isinstance(results["AAPL"], list)
        assert isinstance(results["MSFT"], list)

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    @patch('src.ingestion.news.newsapi_source.QueryArticlesIter')
    def test_fetch_for_company(self, mock_query, mock_er):
        """Test fetching articles by company name."""
        source = NewsAPISource()

        mock_query_instance = MagicMock()
        mock_query.return_value = mock_query_instance
        mock_query_instance.execQuery.return_value = iter([
            {
                "uri": "article-1",
                "title": "Apple Inc Earnings",
                "url": "https://example.com/1",
                "date": "2024-01-15",
                "time": "10:00:00",
                "body": "Apple Inc reported earnings.",
                "source": {"title": "Bloomberg"},
            }
        ])

        articles = source.fetch_for_company("Apple Inc.", "AAPL", lookback_hours=24)

        assert isinstance(articles, list)
        assert len(articles) == 1
        assert "AAPL" in articles[0].tickers

    @pytest.mark.integration
    def test_fetch_for_ticker_real(self):
        """Integration test: fetch real news for a ticker."""
        api_key = os.environ.get("NEWSAPI_AI_KEY")
        if not api_key:
            pytest.skip("NEWSAPI_AI_KEY not set")

        source = NewsAPISource()
        articles = source.fetch_for_ticker("AAPL", lookback_hours=168)  # 1 week

        assert isinstance(articles, list)

        if articles:
            article = articles[0]
            assert isinstance(article, NewsArticle)
            assert article.title
            assert article.url
            assert "AAPL" in article.tickers


class TestMassiveNewsSource:
    """Tests for MassiveNewsSource class."""

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_source_name(self, mock_client):
        """Test source name property."""
        source = MassiveNewsSource()
        assert source.source_name == "massive"

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_initialization_with_env_var(self, mock_client):
        """Test initialization with API key from environment."""
        source = MassiveNewsSource()
        mock_client.assert_called_once_with("test_key")

    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_initialization_with_explicit_key(self, mock_client):
        """Test initialization with explicit API key."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('POLYGON_API_KEY', None)
            source = MassiveNewsSource(api_key="explicit_key")
            mock_client.assert_called_once_with("explicit_key")

    def test_initialization_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('POLYGON_API_KEY', None)
            with pytest.raises(ValueError, match="Polygon API key required"):
                MassiveNewsSource()

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_fetch_returns_empty_list(self, mock_client):
        """Test that fetch() without ticker returns empty list."""
        source = MassiveNewsSource()
        articles = source.fetch(lookback_hours=24)
        assert articles == []

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    @patch('src.ingestion.news.massive_source.trafilatura')
    def test_fetch_for_ticker(self, mock_trafilatura, mock_client_class):
        """Test fetching articles for a ticker."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create mock news item
        mock_item = MagicMock()
        mock_item.id = "article-123"
        mock_item.title = "Apple News Article"
        mock_item.article_url = "https://example.com/article"
        mock_item.published_utc = "2024-01-15T10:30:00Z"
        mock_item.tickers = ["AAPL"]
        mock_item.publisher = MagicMock()
        mock_item.publisher.name = "Reuters"

        mock_client.list_ticker_news.return_value = [mock_item]

        # Setup trafilatura mock
        mock_trafilatura.fetch_url.return_value = "<html>content</html>"
        mock_trafilatura.extract.return_value = "Extracted article content."

        source = MassiveNewsSource()
        articles = source.fetch_for_ticker("AAPL", lookback_hours=24)

        assert len(articles) == 1
        assert articles[0].id == "article-123"
        assert articles[0].title == "Apple News Article"
        assert articles[0].content == "Extracted article content."
        assert articles[0].source == "Reuters"
        assert "AAPL" in articles[0].tickers

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    @patch('src.ingestion.news.massive_source.trafilatura')
    def test_fetch_for_tickers_deduplicates(self, mock_trafilatura, mock_client_class):
        """Test that fetch_for_tickers deduplicates by URL."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Same article appears for both tickers
        mock_item = MagicMock()
        mock_item.id = "shared-article"
        mock_item.title = "Tech News"
        mock_item.article_url = "https://example.com/shared"
        mock_item.published_utc = "2024-01-15T10:30:00Z"
        mock_item.tickers = ["AAPL", "GOOGL"]
        mock_item.publisher = MagicMock()
        mock_item.publisher.name = "Bloomberg"

        mock_client.list_ticker_news.return_value = [mock_item]
        mock_trafilatura.fetch_url.return_value = "<html>content</html>"
        mock_trafilatura.extract.return_value = "Article content."

        source = MassiveNewsSource()
        articles = source.fetch_for_tickers(["AAPL", "GOOGL"], lookback_hours=24)

        # Should only have 1 article despite being returned for both tickers
        assert len(articles) == 1
        assert articles[0].url == "https://example.com/shared"

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    @patch('src.ingestion.news.massive_source.trafilatura')
    def test_extract_content_failure_returns_none(self, mock_trafilatura, mock_client_class):
        """Test that content extraction failure returns article with None content."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_item = MagicMock()
        mock_item.id = "article-456"
        mock_item.title = "Article Title"
        mock_item.article_url = "https://example.com/paywalled"
        mock_item.published_utc = "2024-01-15T10:30:00Z"
        mock_item.tickers = ["AAPL"]
        mock_item.publisher = MagicMock()
        mock_item.publisher.name = "WSJ"

        mock_client.list_ticker_news.return_value = [mock_item]

        # Trafilatura fails to extract
        mock_trafilatura.fetch_url.return_value = None

        source = MassiveNewsSource()
        articles = source.fetch_for_ticker("AAPL", lookback_hours=24)

        assert len(articles) == 1
        assert articles[0].content is None
        assert articles[0].summary is None

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_parse_timestamp_iso_format(self, mock_client):
        """Test parsing ISO timestamp strings."""
        source = MassiveNewsSource()

        result = source._parse_timestamp("2024-01-15T10:30:00Z")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_parse_timestamp_datetime_passthrough(self, mock_client):
        """Test that datetime objects pass through unchanged."""
        source = MassiveNewsSource()

        dt = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        result = source._parse_timestamp(dt)
        assert result == dt

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_parse_timestamp_invalid_returns_now(self, mock_client):
        """Test that invalid timestamp returns current time."""
        source = MassiveNewsSource()

        result = source._parse_timestamp("invalid-timestamp")
        # Should return a datetime close to now
        assert isinstance(result, datetime)
        assert (datetime.now(timezone.utc) - result).total_seconds() < 5

    @patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"})
    @patch('src.ingestion.news.massive_source.RESTClient')
    def test_implements_interface(self, mock_client):
        """Verify MassiveNewsSource implements NewsSource interface."""
        source = MassiveNewsSource()

        assert hasattr(source, 'fetch')
        assert hasattr(source, 'fetch_for_ticker')
        assert hasattr(source, 'source_name')
        assert callable(source.fetch)
        assert callable(source.fetch_for_ticker)

    @pytest.mark.integration
    def test_fetch_for_ticker_real(self):
        """Integration test: fetch real news for a ticker."""
        api_key = os.environ.get("POLYGON_API_KEY")
        if not api_key:
            pytest.skip("POLYGON_API_KEY not set")

        source = MassiveNewsSource()
        articles = source.fetch_for_ticker("AAPL", lookback_hours=72)

        assert isinstance(articles, list)

        if articles:
            article = articles[0]
            assert isinstance(article, NewsArticle)
            assert article.title
            assert article.url
            assert "AAPL" in article.tickers


class TestNewsSourceInterface:
    """Test that NewsAPISource properly implements the interface."""

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_implements_interface(self, mock_er):
        """Verify NewsAPISource implements NewsSource."""
        source = NewsAPISource()

        assert hasattr(source, 'fetch')
        assert hasattr(source, 'fetch_for_ticker')
        assert hasattr(source, 'source_name')
        assert callable(source.fetch)
        assert callable(source.fetch_for_ticker)


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @patch.dict(os.environ, {"NEWSAPI_AI_KEY": "test_key"})
    @patch('src.ingestion.news.newsapi_source.EventRegistry')
    def test_rate_limit_delay(self, mock_er):
        """Test that rate limiting waits appropriately."""
        import time

        config = {"rate_limit_delay": 0.1}  # 100ms
        source = NewsAPISource(config)

        start = time.time()
        source._rate_limit()
        elapsed = time.time() - start

        assert elapsed >= 0.1


# Run integration tests only when explicitly requested
# pytest -m integration tests/test_news_data.py
