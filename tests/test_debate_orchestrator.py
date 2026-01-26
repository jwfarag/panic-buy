# Tests for Debate Orchestrator
# ==============================
# Integration tests for debate flow coordination.

from datetime import date
from unittest.mock import MagicMock, patch

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
from src.agent.debate.orchestrator import (
    DebateOrchestrator,
    create_orchestrator_from_config,
)
from src.agent.debate.participant import Participant


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_stock_context():
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
        articles=[
            {
                "source": "Reuters",
                "title": "Apple misses earnings",
                "summary": "Revenue below expectations",
            }
        ],
    )


@pytest.fixture
def mock_participant():
    """Create a mock participant that returns predictable statements."""

    def create_mock(stance: DebateStance, name: str):
        mock = MagicMock(spec=Participant)
        mock.config = ParticipantConfig(
            id=f"{stance.value}_analyst",
            name=name,
            stance=stance,
            persona="Test persona",
        )
        mock.id = f"{stance.value}_analyst"
        mock.name = name
        mock.stance = stance
        mock.max_tokens = 500

        # Mock opening generation
        def mock_opening(context, opponent_name):
            return DebateStatement(
                participant_id=mock.id,
                participant_name=mock.name,
                stance=stance,
                phase=DebatePhase.OPENING,
                content=f"Opening statement from {name}.",
                token_count=100,
            )

        mock.generate_opening.side_effect = mock_opening

        # Mock rebuttal generation
        def mock_rebuttal(context, opponent_statement):
            return DebateStatement(
                participant_id=mock.id,
                participant_name=mock.name,
                stance=stance,
                phase=DebatePhase.REBUTTAL,
                content=f"Rebuttal from {name}.",
                token_count=80,
            )

        mock.generate_rebuttal.side_effect = mock_rebuttal

        return mock

    return create_mock


@pytest.fixture
def mock_orchestrator(mock_participant):
    """Create an orchestrator with mocked participants and LLM."""
    bull = mock_participant(DebateStance.BUY, "Test Bull")
    bear = mock_participant(DebateStance.AVOID, "Test Bear")

    with patch("src.agent.debate.orchestrator.ChatAnthropic") as mock_llm_class:
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is a balanced summary of the debate."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm

        orchestrator = DebateOrchestrator(
            config=DebateConfig(),
            participants=(bull, bear),
        )
        yield orchestrator


# =============================================================================
# Initialization Tests
# =============================================================================


class TestOrchestratorInit:
    """Tests for DebateOrchestrator initialization."""

    def test_default_config(self, mock_participant):
        """Test default configuration is used when none provided."""
        bull = mock_participant(DebateStance.BUY, "Bull")
        bear = mock_participant(DebateStance.AVOID, "Bear")

        with patch("src.agent.debate.orchestrator.ChatAnthropic"):
            orchestrator = DebateOrchestrator(participants=(bull, bear))

            assert orchestrator.config.model == "claude-sonnet-4-20250514"
            assert orchestrator.config.include_rebuttals is True
            assert orchestrator.config.include_summary is True

    def test_custom_config(self, mock_participant):
        """Test custom configuration is applied."""
        bull = mock_participant(DebateStance.BUY, "Bull")
        bear = mock_participant(DebateStance.AVOID, "Bear")

        config = DebateConfig(
            model="claude-3-haiku",
            include_rebuttals=False,
            include_summary=False,
        )

        with patch("src.agent.debate.orchestrator.ChatAnthropic"):
            orchestrator = DebateOrchestrator(
                config=config,
                participants=(bull, bear),
            )

            assert orchestrator.config.model == "claude-3-haiku"
            assert orchestrator.config.include_rebuttals is False

    def test_creates_default_participants_when_none_provided(self):
        """Test default participants are created when not provided."""
        with patch("src.agent.debate.orchestrator.ChatAnthropic"):
            with patch(
                "src.agent.debate.orchestrator.create_default_participants"
            ) as mock_create:
                mock_bull = MagicMock()
                mock_bear = MagicMock()
                mock_create.return_value = (mock_bull, mock_bear)

                orchestrator = DebateOrchestrator()

                mock_create.assert_called_once()
                assert orchestrator.bull == mock_bull
                assert orchestrator.bear == mock_bear


# =============================================================================
# Debate Flow Tests
# =============================================================================


class TestDebateFlow:
    """Tests for the debate execution flow."""

    def test_run_debate_returns_result(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test run_debate returns a DebateResult."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        assert isinstance(result, DebateResult)
        assert result.ticker == "AAPL"
        assert result.company_name == "Apple Inc."

    def test_run_debate_generates_openings(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test both participants generate opening statements."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        assert len(result.opening_statements) == 2

        stances = [s.stance for s in result.opening_statements]
        assert DebateStance.BUY in stances
        assert DebateStance.AVOID in stances

    def test_run_debate_generates_rebuttals(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test both participants generate rebuttals."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        assert len(result.rebuttals) == 2

        phases = [s.phase for s in result.rebuttals]
        assert all(p == DebatePhase.REBUTTAL for p in phases)

    def test_run_debate_generates_summary(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test summary is generated."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        assert result.summary is not None
        assert "balanced summary" in result.summary

    def test_run_debate_tracks_timing(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test timing metadata is captured."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.started_at

    def test_run_debate_calculates_tokens(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test token count is accumulated."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        # 2 openings * 100 + 2 rebuttals * 80 = 360
        assert result.total_tokens == 360

    def test_run_debate_captures_config(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test configuration snapshot is captured."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        assert result.config_snapshot is not None
        assert "model" in result.config_snapshot


# =============================================================================
# Phase Toggle Tests
# =============================================================================


class TestPhaseToggles:
    """Tests for phase enable/disable functionality."""

    def test_skip_rebuttals(self, mock_participant, sample_stock_context):
        """Test rebuttals are skipped when disabled."""
        bull = mock_participant(DebateStance.BUY, "Bull")
        bear = mock_participant(DebateStance.AVOID, "Bear")

        config = DebateConfig(include_rebuttals=False)

        with patch("src.agent.debate.orchestrator.ChatAnthropic") as mock_llm:
            mock_llm.return_value.invoke.return_value.content = "Summary"

            orchestrator = DebateOrchestrator(
                config=config,
                participants=(bull, bear),
            )
            result = orchestrator.run_debate(sample_stock_context)

            assert len(result.rebuttals) == 0
            bull.generate_rebuttal.assert_not_called()
            bear.generate_rebuttal.assert_not_called()

    def test_skip_summary(self, mock_participant, sample_stock_context):
        """Test summary is skipped when disabled."""
        bull = mock_participant(DebateStance.BUY, "Bull")
        bear = mock_participant(DebateStance.AVOID, "Bear")

        config = DebateConfig(include_summary=False)

        with patch("src.agent.debate.orchestrator.ChatAnthropic") as mock_llm:
            orchestrator = DebateOrchestrator(
                config=config,
                participants=(bull, bear),
            )
            result = orchestrator.run_debate(sample_stock_context)

            assert result.summary is None
            mock_llm.return_value.invoke.assert_not_called()

    def test_openings_only(self, mock_participant, sample_stock_context):
        """Test debate with only opening statements."""
        bull = mock_participant(DebateStance.BUY, "Bull")
        bear = mock_participant(DebateStance.AVOID, "Bear")

        config = DebateConfig(include_rebuttals=False, include_summary=False)

        with patch("src.agent.debate.orchestrator.ChatAnthropic"):
            orchestrator = DebateOrchestrator(
                config=config,
                participants=(bull, bear),
            )
            result = orchestrator.run_debate(sample_stock_context)

            assert len(result.opening_statements) == 2
            assert len(result.rebuttals) == 0
            assert result.summary is None


# =============================================================================
# Order Tests
# =============================================================================


class TestDebateOrder:
    """Tests for debate participant ordering."""

    def test_bull_opens_first_by_default(
        self, mock_participant, sample_stock_context
    ):
        """Test bull participant opens first by default."""
        bull = mock_participant(DebateStance.BUY, "Bull")
        bear = mock_participant(DebateStance.AVOID, "Bear")

        with patch("src.agent.debate.orchestrator.ChatAnthropic") as mock_llm:
            mock_llm.return_value.invoke.return_value.content = "Summary"

            orchestrator = DebateOrchestrator(participants=(bull, bear))
            result = orchestrator.run_debate(sample_stock_context)

            # First opening should be from bull
            assert result.opening_statements[0].stance == DebateStance.BUY

    def test_bear_opens_first_when_configured(
        self, mock_participant, sample_stock_context
    ):
        """Test bear participant can open first."""
        bull = mock_participant(DebateStance.BUY, "Bull")
        bear = mock_participant(DebateStance.AVOID, "Bear")

        config = DebateConfig(bull_opens_first=False)

        with patch("src.agent.debate.orchestrator.ChatAnthropic") as mock_llm:
            mock_llm.return_value.invoke.return_value.content = "Summary"

            orchestrator = DebateOrchestrator(
                config=config,
                participants=(bull, bear),
            )
            result = orchestrator.run_debate(sample_stock_context)

            # First opening should be from bear
            assert result.opening_statements[0].stance == DebateStance.AVOID


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestOrchestratorFactory:
    """Tests for create_orchestrator_from_config."""

    def test_creates_from_config_dict(self):
        """Test orchestrator creation from config dictionary."""
        config_dict = {
            "model": {"name": "claude-3-haiku"},
            "structure": {
                "phases": {"rebuttals": False, "summary": True},
                "bull_opens_first": False,
            },
        }

        with patch("src.agent.debate.orchestrator.ChatAnthropic"):
            with patch(
                "src.agent.debate.orchestrator.create_default_participants"
            ) as mock_create:
                mock_create.return_value = (MagicMock(), MagicMock())

                orchestrator = create_orchestrator_from_config(config_dict)

                assert orchestrator.config.model == "claude-3-haiku"
                assert orchestrator.config.include_rebuttals is False
                assert orchestrator.config.include_summary is True
                assert orchestrator.config.bull_opens_first is False

    def test_creates_custom_participants_from_config(self):
        """Test custom participants are created from config."""
        config_dict = {
            "model": {"name": "claude-sonnet-4-20250514"},
            "participants": {
                "bull": {
                    "id": "custom_bull",
                    "name": "Custom Bull",
                    "persona": "A custom bull persona",
                    "style": ["Be aggressive"],
                },
                "bear": {
                    "id": "custom_bear",
                    "name": "Custom Bear",
                    "persona": "A custom bear persona",
                    "style": ["Be cautious"],
                },
            },
        }

        with patch("src.agent.debate.orchestrator.ChatAnthropic"):
            orchestrator = create_orchestrator_from_config(config_dict)

            assert orchestrator.bull.name == "Custom Bull"
            assert orchestrator.bear.name == "Custom Bear"


# =============================================================================
# Transcript Formatting Tests
# =============================================================================


class TestTranscriptFormatting:
    """Tests for debate transcript formatting."""

    def test_format_transcript_for_summary(
        self, mock_orchestrator, sample_stock_context
    ):
        """Test transcript is properly formatted for summary prompt."""
        result = mock_orchestrator.run_debate(sample_stock_context)

        # The transcript should have been passed to the summary LLM
        transcript = mock_orchestrator._format_transcript_for_summary(result)

        assert "Test Bull (BUY)" in transcript
        assert "Test Bear (AVOID)" in transcript
        assert "Opening" in transcript
        assert "Rebuttal" in transcript
