# Tests for Debate Models
# ========================
# Unit tests for data structures in the debate module.

from datetime import date, datetime, timedelta

import pytest

from src.agent.debate.models import (
    DebateConfig,
    DebatePhase,
    DebateResult,
    DebateStance,
    DebateStatement,
    ParticipantConfig,
    StockContext,
)


# =============================================================================
# StockContext Tests
# =============================================================================


class TestStockContext:
    """Tests for StockContext dataclass."""

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing."""
        return [
            {
                "source": "Reuters",
                "title": "Company reports earnings",
                "summary": "Earnings were below expectations",
                "content": "Full article content here...",
            },
            {
                "source": "Bloomberg",
                "title": "Analyst downgrades stock",
                "summary": "Price target reduced",
            },
            {
                "source": "CNBC",
                "title": "Stock drops sharply",
            },
        ]

    @pytest.fixture
    def stock_context(self, sample_articles):
        """Sample StockContext for testing."""
        return StockContext(
            ticker="AAPL",
            company_name="Apple Inc.",
            debate_date=date(2024, 1, 15),
            price_change_pct=-0.082,
            open_price=185.50,
            close_price=170.30,
            volume=152_000_000,
            volume_vs_average=2.4,
            articles=sample_articles,
        )

    def test_format_for_prompt_default(self, stock_context):
        """Test default formatting includes all expected elements."""
        output = stock_context.format_for_prompt()

        assert "Apple Inc. (AAPL)" in output
        assert "2024-01-15" in output
        assert "-8.20%" in output
        assert "$170.30" in output
        assert "$185.50" in output
        assert "152,000,000" in output
        assert "2.4x average" in output
        assert "Recent News:" in output
        assert "Reuters" in output

    def test_format_for_prompt_max_articles(self, stock_context):
        """Test max_articles parameter limits output."""
        output = stock_context.format_for_prompt(max_articles=1)

        assert "Reuters" in output
        assert "Bloomberg" not in output
        assert "CNBC" not in output

    def test_format_for_prompt_custom_fields(self, stock_context):
        """Test article_fields parameter selects specific fields."""
        output = stock_context.format_for_prompt(article_fields=["source", "title"])

        assert "Reuters | Company reports earnings" in output
        # summary and content should not appear
        assert "Earnings were below expectations" not in output
        assert "Full article content" not in output

    def test_format_for_prompt_missing_fields(self, stock_context):
        """Test graceful handling of missing article fields."""
        # Third article only has source and title
        output = stock_context.format_for_prompt(max_articles=3)

        # Should still include the third article
        assert "CNBC" in output
        assert "Stock drops sharply" in output

    def test_format_for_prompt_empty_articles(self):
        """Test empty articles shows placeholder."""
        context = StockContext(
            ticker="AAPL",
            company_name="Apple Inc.",
            debate_date=date(2024, 1, 15),
            price_change_pct=-0.05,
            open_price=100.0,
            close_price=95.0,
            volume=1_000_000,
            volume_vs_average=1.0,
            articles=[],
        )
        output = context.format_for_prompt()

        assert "No recent news available." in output

    def test_format_for_prompt_articles_with_empty_values(self):
        """Test articles with empty string values are skipped."""
        context = StockContext(
            ticker="TEST",
            company_name="Test Corp",
            debate_date=date(2024, 1, 15),
            price_change_pct=-0.05,
            open_price=100.0,
            close_price=95.0,
            volume=1_000_000,
            volume_vs_average=1.0,
            articles=[{"source": "Reuters", "title": "", "summary": "Has summary"}],
        )
        output = context.format_for_prompt()

        # Empty title should be skipped, but source and summary should appear
        assert "Reuters" in output
        assert "Has summary" in output


# =============================================================================
# ParticipantConfig Tests
# =============================================================================


class TestParticipantConfig:
    """Tests for ParticipantConfig dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = ParticipantConfig(
            id="test_analyst",
            name="Test Analyst",
            stance=DebateStance.BUY,
            persona="You are a test analyst.",
            style_hints=["Be concise", "Use data"],
            temperature=0.8,
        )
        result = config.to_dict()

        assert result["id"] == "test_analyst"
        assert result["name"] == "Test Analyst"
        assert result["stance"] == "buy"
        assert result["persona"] == "You are a test analyst."
        assert result["style_hints"] == ["Be concise", "Use data"]
        assert result["temperature"] == 0.8

    def test_default_values(self):
        """Test default values are applied."""
        config = ParticipantConfig(
            id="test",
            name="Test",
            stance=DebateStance.AVOID,
            persona="Persona",
        )

        assert config.style_hints == []
        assert config.temperature == 0.7


# =============================================================================
# DebateStatement Tests
# =============================================================================


class TestDebateStatement:
    """Tests for DebateStatement dataclass."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        statement = DebateStatement(
            participant_id="bull_analyst",
            participant_name="Alex Chen",
            stance=DebateStance.BUY,
            phase=DebatePhase.OPENING,
            content="This is a buy opportunity.",
            timestamp=timestamp,
            token_count=150,
            generation_time_ms=1200,
        )
        result = statement.to_dict()

        assert result["participant_id"] == "bull_analyst"
        assert result["participant_name"] == "Alex Chen"
        assert result["stance"] == "buy"
        assert result["phase"] == "opening"
        assert result["content"] == "This is a buy opportunity."
        assert result["timestamp"] == "2024-01-15T10:30:00"
        assert result["token_count"] == 150
        assert result["generation_time_ms"] == 1200

    def test_default_timestamp(self):
        """Test timestamp defaults to now."""
        before = datetime.now()
        statement = DebateStatement(
            participant_id="test",
            participant_name="Test",
            stance=DebateStance.BUY,
            phase=DebatePhase.OPENING,
            content="Test content",
        )
        after = datetime.now()

        assert before <= statement.timestamp <= after


# =============================================================================
# DebateResult Tests
# =============================================================================


class TestDebateResult:
    """Tests for DebateResult dataclass."""

    @pytest.fixture
    def sample_result(self):
        """Sample DebateResult for testing."""
        return DebateResult(
            ticker="AAPL",
            company_name="Apple Inc.",
            debate_date=date(2024, 1, 15),
            opening_statements=[
                DebateStatement(
                    participant_id="bull",
                    participant_name="Bull",
                    stance=DebateStance.BUY,
                    phase=DebatePhase.OPENING,
                    content="Buy now!",
                    token_count=100,
                ),
                DebateStatement(
                    participant_id="bear",
                    participant_name="Bear",
                    stance=DebateStance.AVOID,
                    phase=DebatePhase.OPENING,
                    content="Avoid this!",
                    token_count=100,
                ),
            ],
            rebuttals=[],
            summary="Balanced summary.",
            started_at=datetime(2024, 1, 15, 10, 0, 0),
            completed_at=datetime(2024, 1, 15, 10, 0, 30),
            total_tokens=200,
        )

    def test_duration_seconds(self, sample_result):
        """Test duration calculation."""
        assert sample_result.duration_seconds == 30.0

    def test_duration_seconds_none_when_incomplete(self):
        """Test duration is None when timestamps missing."""
        result = DebateResult(
            ticker="TEST",
            company_name="Test",
            debate_date=date(2024, 1, 15),
            started_at=datetime.now(),
            completed_at=None,
        )
        assert result.duration_seconds is None

    def test_to_dict(self, sample_result):
        """Test serialization to dictionary."""
        result = sample_result.to_dict()

        assert result["ticker"] == "AAPL"
        assert result["company_name"] == "Apple Inc."
        assert result["debate_date"] == "2024-01-15"
        assert len(result["opening_statements"]) == 2
        assert result["summary"] == "Balanced summary."
        assert result["metadata"]["duration_seconds"] == 30.0
        assert result["metadata"]["total_tokens"] == 200


# =============================================================================
# DebateConfig Tests
# =============================================================================


class TestDebateConfig:
    """Tests for DebateConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DebateConfig()

        assert config.model == "claude-sonnet-4-20250514"
        assert config.max_tokens_opening == 500
        assert config.max_tokens_rebuttal == 400
        assert config.max_tokens_summary == 300
        assert config.include_rebuttals is True
        assert config.include_summary is True
        assert config.bull_opens_first is True
        assert config.summary_temperature == 0.5

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = DebateConfig(
            model="claude-3-haiku",
            include_rebuttals=False,
        )
        result = config.to_dict()

        assert result["model"] == "claude-3-haiku"
        assert result["include_rebuttals"] is False
        assert result["include_summary"] is True  # default


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests for enum values."""

    def test_debate_stance_values(self):
        """Test DebateStance enum values."""
        assert DebateStance.BUY.value == "buy"
        assert DebateStance.AVOID.value == "avoid"

    def test_debate_phase_values(self):
        """Test DebatePhase enum values."""
        assert DebatePhase.OPENING.value == "opening"
        assert DebatePhase.REBUTTAL.value == "rebuttal"
        assert DebatePhase.SUMMARY.value == "summary"
