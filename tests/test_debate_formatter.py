# Tests for Debate Formatter
# ===========================
# Unit tests for output formatting utilities.

import json
from datetime import date, datetime

import pytest

from src.agent.debate.formatter import (
    format_for_report,
    format_json,
    format_markdown,
    format_short,
)
from src.agent.debate.models import (
    DebatePhase,
    DebateResult,
    DebateStance,
    DebateStatement,
    ParticipantConfig,
)


@pytest.fixture
def sample_participants():
    """Sample participant configs."""
    return [
        ParticipantConfig(
            id="bull_analyst",
            name="Alex Chen",
            stance=DebateStance.BUY,
            persona="Bull persona",
        ),
        ParticipantConfig(
            id="bear_analyst",
            name="Sarah Martinez",
            stance=DebateStance.AVOID,
            persona="Bear persona",
        ),
    ]


@pytest.fixture
def sample_debate_result(sample_participants):
    """Sample DebateResult for testing formatters."""
    return DebateResult(
        ticker="AAPL",
        company_name="Apple Inc.",
        debate_date=date(2024, 1, 15),
        opening_statements=[
            DebateStatement(
                participant_id="bull_analyst",
                participant_name="Alex Chen",
                stance=DebateStance.BUY,
                phase=DebatePhase.OPENING,
                content="This is a great buying opportunity. The fundamentals are strong.",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                token_count=100,
                generation_time_ms=1500,
            ),
            DebateStatement(
                participant_id="bear_analyst",
                participant_name="Sarah Martinez",
                stance=DebateStance.AVOID,
                phase=DebatePhase.OPENING,
                content="Investors should avoid this stock. Too many risks ahead.",
                timestamp=datetime(2024, 1, 15, 10, 0, 30),
                token_count=100,
                generation_time_ms=1400,
            ),
        ],
        rebuttals=[
            DebateStatement(
                participant_id="bull_analyst",
                participant_name="Alex Chen",
                stance=DebateStance.BUY,
                phase=DebatePhase.REBUTTAL,
                content="The risks Sarah mentions are overblown.",
                timestamp=datetime(2024, 1, 15, 10, 1, 0),
                token_count=80,
                generation_time_ms=1200,
            ),
            DebateStatement(
                participant_id="bear_analyst",
                participant_name="Sarah Martinez",
                stance=DebateStance.AVOID,
                phase=DebatePhase.REBUTTAL,
                content="Alex is ignoring the China exposure.",
                timestamp=datetime(2024, 1, 15, 10, 1, 30),
                token_count=80,
                generation_time_ms=1100,
            ),
        ],
        summary="Both sides make valid points. The key question is China exposure.",
        participants=sample_participants,
        started_at=datetime(2024, 1, 15, 10, 0, 0),
        completed_at=datetime(2024, 1, 15, 10, 2, 0),
        total_tokens=360,
        config_snapshot={"model": "claude-sonnet-4-20250514"},
    )


# =============================================================================
# format_markdown Tests
# =============================================================================


class TestFormatMarkdown:
    """Tests for format_markdown function."""

    def test_includes_header(self, sample_debate_result):
        """Test output includes title and date."""
        output = format_markdown(sample_debate_result)

        assert "# Stock Debate: Apple Inc. (AAPL)" in output
        assert "**Date:** 2024-01-15" in output

    def test_includes_debaters(self, sample_debate_result):
        """Test output includes debater names."""
        output = format_markdown(sample_debate_result)

        assert "Alex Chen (Bull)" in output
        assert "Sarah Martinez (Bear)" in output

    def test_includes_opening_statements(self, sample_debate_result):
        """Test output includes opening statements section."""
        output = format_markdown(sample_debate_result)

        assert "## Opening Statements" in output
        assert "### Alex Chen [BUY]" in output
        assert "### Sarah Martinez [AVOID]" in output
        assert "great buying opportunity" in output
        assert "Investors should avoid" in output

    def test_includes_rebuttals(self, sample_debate_result):
        """Test output includes rebuttals section."""
        output = format_markdown(sample_debate_result)

        assert "## Rebuttals" in output
        assert "risks Sarah mentions" in output
        assert "China exposure" in output

    def test_includes_summary(self, sample_debate_result):
        """Test output includes summary section."""
        output = format_markdown(sample_debate_result)

        assert "## Summary" in output
        assert "Both sides make valid points" in output

    def test_metadata_excluded_by_default(self, sample_debate_result):
        """Test metadata is excluded by default."""
        output = format_markdown(sample_debate_result)

        assert "## Metadata" not in output
        assert "Duration:" not in output

    def test_metadata_included_when_requested(self, sample_debate_result):
        """Test metadata is included when requested."""
        output = format_markdown(sample_debate_result, include_metadata=True)

        assert "## Metadata" in output
        assert "**Duration:** 120.0s" in output
        assert "**Total tokens:** 360" in output
        assert "**Model:** claude-sonnet-4-20250514" in output

    def test_no_rebuttals_section_when_empty(self, sample_participants):
        """Test rebuttals section is skipped when empty."""
        result = DebateResult(
            ticker="TEST",
            company_name="Test Corp",
            debate_date=date(2024, 1, 15),
            opening_statements=[
                DebateStatement(
                    participant_id="bull",
                    participant_name="Bull",
                    stance=DebateStance.BUY,
                    phase=DebatePhase.OPENING,
                    content="Buy it.",
                ),
            ],
            rebuttals=[],
            participants=sample_participants,
        )
        output = format_markdown(result)

        assert "## Opening Statements" in output
        assert "## Rebuttals" not in output


# =============================================================================
# format_json Tests
# =============================================================================


class TestFormatJson:
    """Tests for format_json function."""

    def test_valid_json(self, sample_debate_result):
        """Test output is valid JSON."""
        output = format_json(sample_debate_result)
        parsed = json.loads(output)

        assert parsed["ticker"] == "AAPL"
        assert parsed["company_name"] == "Apple Inc."

    def test_includes_all_fields(self, sample_debate_result):
        """Test JSON includes all expected fields."""
        output = format_json(sample_debate_result)
        parsed = json.loads(output)

        assert "ticker" in parsed
        assert "company_name" in parsed
        assert "debate_date" in parsed
        assert "opening_statements" in parsed
        assert "rebuttals" in parsed
        assert "summary" in parsed
        assert "participants" in parsed
        assert "metadata" in parsed

    def test_indent_parameter(self, sample_debate_result):
        """Test indent parameter affects formatting."""
        output_2 = format_json(sample_debate_result, indent=2)
        output_4 = format_json(sample_debate_result, indent=4)

        # More indent = longer output
        assert len(output_4) > len(output_2)

    def test_statements_serialized(self, sample_debate_result):
        """Test statements are properly serialized."""
        output = format_json(sample_debate_result)
        parsed = json.loads(output)

        opening = parsed["opening_statements"][0]
        assert opening["participant_name"] == "Alex Chen"
        assert opening["stance"] == "buy"
        assert opening["phase"] == "opening"


# =============================================================================
# format_short Tests
# =============================================================================


class TestFormatShort:
    """Tests for format_short function."""

    def test_includes_header(self, sample_debate_result):
        """Test short format includes header."""
        output = format_short(sample_debate_result)

        assert "Apple Inc. (AAPL)" in output

    def test_includes_first_sentences(self, sample_debate_result):
        """Test short format includes first sentence of each opening."""
        output = format_short(sample_debate_result)

        # First sentence of bull's opening
        assert "great buying opportunity" in output
        # First sentence of bear's opening
        assert "should avoid this stock" in output

    def test_truncates_summary(self, sample_participants):
        """Test long summary is truncated."""
        long_summary = "A" * 500
        result = DebateResult(
            ticker="TEST",
            company_name="Test",
            debate_date=date(2024, 1, 15),
            opening_statements=[
                DebateStatement(
                    participant_id="bull",
                    participant_name="Bull",
                    stance=DebateStance.BUY,
                    phase=DebatePhase.OPENING,
                    content="Test opening.",
                ),
            ],
            summary=long_summary,
            participants=sample_participants,
        )
        output = format_short(result)

        assert "..." in output
        assert len(output) < len(long_summary) + 200


# =============================================================================
# format_for_report Tests
# =============================================================================


class TestFormatForReport:
    """Tests for format_for_report function."""

    def test_default_no_truncation(self, sample_debate_result):
        """Test no truncation by default."""
        output = format_for_report(sample_debate_result)

        # Should be full markdown without metadata
        assert "## Opening Statements" in output
        assert "## Rebuttals" in output
        assert "## Summary" in output

    def test_respects_max_length(self, sample_debate_result):
        """Test max_length parameter truncates output."""
        output = format_for_report(sample_debate_result, max_length=200)

        assert len(output) <= 200
        assert "[Truncated...]" in output

    def test_excludes_metadata(self, sample_debate_result):
        """Test metadata is excluded from report format."""
        output = format_for_report(sample_debate_result)

        assert "## Metadata" not in output
        assert "Duration:" not in output
