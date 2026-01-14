# Tests for News Data Module
# ==========================

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from src.ingestion.news.base import NewsArticle, NewsSource
from src.ingestion.news.yahoo_news import YahooNewsSource


class TestNewsArticle:
    """Tests for NewsArticle dataclass."""

    def test_news_article_creation(self):
        """Test creating a NewsArticle."""
        article = NewsArticle(
            id="abc123",
            source="yahoo",
            title="Apple Announces New Product",
            url="https://example.com/article",
            published_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            summary="Apple unveiled a new product today.",
            content="Full article content here...",
            tickers=["AAPL"],
        )

        assert article.id == "abc123"
        assert article.source == "yahoo"
        assert article.title == "Apple Announces New Product"
        assert article.url == "https://example.com/article"
        assert article.published_at.year == 2024
        assert "AAPL" in article.tickers

    def test_news_article_to_dict(self):
        """Test converting NewsArticle to dict."""
        article = NewsArticle(
            id="abc123",
            source="yahoo",
            title="Test Article",
            url="https://example.com",
            published_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            tickers=["AAPL", "MSFT"],
        )

        result = article.to_dict()

        assert result["id"] == "abc123"
        assert result["source"] == "yahoo"
        assert result["title"] == "Test Article"
        assert result["tickers"] == ["AAPL", "MSFT"]
        assert "2024-01-15" in result["published_at"]

    def test_news_article_defaults(self):
        """Test NewsArticle with default values."""
        article = NewsArticle(
            id="test",
            source="yahoo",
            title="Test",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
        )

        assert article.content is None
        assert article.summary is None
        assert article.tickers == []
        assert article.raw_data == {}


class TestYahooNewsSource:
    """Tests for YahooNewsSource class."""

    def test_source_name(self):
        """Test source name property."""
        source = YahooNewsSource()
        assert source.source_name == "yahoo"

    def test_initialization_defaults(self):
        """Test default initialization."""
        source = YahooNewsSource()
        assert source._rate_limit_delay == 1.0
        assert source._max_retries == 3

    def test_initialization_custom_config(self):
        """Test initialization with custom config."""
        config = {"rate_limit_delay": 2.0, "max_retries": 5}
        source = YahooNewsSource(config)
        assert source._rate_limit_delay == 2.0
        assert source._max_retries == 5

    @pytest.mark.integration
    def test_fetch_for_ticker_real(self):
        """Integration test: fetch real news for a ticker."""
        source = YahooNewsSource()
        articles = source.fetch_for_ticker("AAPL", lookback_hours=168)  # 1 week

        # yfinance usually returns some news for major tickers
        assert isinstance(articles, list)
        # Don't assert non-empty as news availability varies

        if articles:
            article = articles[0]
            assert isinstance(article, NewsArticle)
            assert article.source == "yahoo"
            assert article.title  # Should have a title
            assert article.url  # Should have a URL
            assert "AAPL" in article.tickers

    @pytest.mark.integration
    def test_fetch_for_multiple_tickers_real(self):
        """Integration test: fetch news for multiple tickers."""
        source = YahooNewsSource()
        tickers = ["AAPL", "MSFT"]
        results = source.fetch_for_tickers(tickers, lookback_hours=168)

        assert "AAPL" in results
        assert "MSFT" in results
        assert isinstance(results["AAPL"], list)
        assert isinstance(results["MSFT"], list)

    def test_parse_yf_news_item(self):
        """Test parsing a yfinance news item."""
        source = YahooNewsSource()

        mock_item = {
            "title": "Test Article Title",
            "link": "https://example.com/article",
            "providerPublishTime": 1705320600,  # 2024-01-15 10:30:00 UTC
            "summary": "This is a summary",
            "relatedTickers": ["MSFT", "GOOGL"],
        }

        article = source._parse_yf_news_item(mock_item, "AAPL")

        assert article is not None
        assert article.title == "Test Article Title"
        assert article.url == "https://example.com/article"
        assert article.summary == "This is a summary"
        assert "AAPL" in article.tickers
        assert "MSFT" in article.tickers
        assert article.published_at is not None

    def test_parse_yf_news_item_missing_fields(self):
        """Test parsing news item with missing fields."""
        source = YahooNewsSource()

        mock_item = {
            "title": "Minimal Article",
            "link": "https://example.com",
        }

        article = source._parse_yf_news_item(mock_item, "AAPL")

        assert article is not None
        assert article.title == "Minimal Article"
        assert "AAPL" in article.tickers

    def test_parse_yf_news_item_empty(self):
        """Test parsing empty/invalid news item."""
        source = YahooNewsSource()

        # Should handle gracefully
        article = source._parse_yf_news_item({}, "AAPL")
        # May return an article with empty title or None depending on implementation


class TestNewsSourceInterface:
    """Test that YahooNewsSource properly implements the interface."""

    def test_implements_interface(self):
        """Verify YahooNewsSource implements NewsSource."""
        source = YahooNewsSource()

        assert hasattr(source, 'fetch')
        assert hasattr(source, 'fetch_for_ticker')
        assert hasattr(source, 'source_name')
        assert callable(source.fetch)
        assert callable(source.fetch_for_ticker)


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_delay(self):
        """Test that rate limiting waits appropriately."""
        import time

        config = {"rate_limit_delay": 0.1}  # 100ms
        source = YahooNewsSource(config)

        start = time.time()
        source._rate_limit()
        elapsed = time.time() - start

        assert elapsed >= 0.1

    def test_retry_with_backoff_success(self):
        """Test retry succeeds on first attempt."""
        source = YahooNewsSource({"rate_limit_delay": 0.01})

        call_count = 0

        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = source._retry_with_backoff(success_func)

        assert result == "success"
        assert call_count == 1

    def test_retry_with_backoff_eventual_success(self):
        """Test retry succeeds after failures."""
        source = YahooNewsSource({"rate_limit_delay": 0.01, "max_retries": 3})

        call_count = 0

        def eventual_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = source._retry_with_backoff(eventual_success)

        assert result == "success"
        assert call_count == 3

    def test_retry_with_backoff_all_failures(self):
        """Test retry raises after all attempts fail."""
        source = YahooNewsSource({"rate_limit_delay": 0.01, "max_retries": 2})

        def always_fail():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            source._retry_with_backoff(always_fail)


# Run integration tests only when explicitly requested
# pytest -m integration tests/test_news_data.py
