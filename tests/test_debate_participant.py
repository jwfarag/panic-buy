# Tests for Debate Participant
# =============================
# Unit tests for the Participant class with mocked LLM.

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.agent.debate.models import (
    DebatePhase,
    DebateStance,
    DebateStatement,
    ParticipantConfig,
    StockContext,
)
from src.agent.debate.participant import (
    DEFAULT_BEAR_PERSONA,
    DEFAULT_BULL_PERSONA,
    Participant,
    create_default_participants,
    create_participant_from_config,
)


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
def bull_config():
    """Bull participant configuration."""
    return ParticipantConfig(
        id="test_bull",
        name="Test Bull",
        stance=DebateStance.BUY,
        persona="You are a bullish analyst.",
        style_hints=["Focus on value", "Be optimistic"],
        temperature=0.7,
    )


@pytest.fixture
def bear_config():
    """Bear participant configuration."""
    return ParticipantConfig(
        id="test_bear",
        name="Test Bear",
        stance=DebateStance.AVOID,
        persona="You are a bearish analyst.",
        style_hints=["Focus on risks", "Be cautious"],
        temperature=0.7,
    )


@pytest.fixture
def mock_llm():
    """Mock LangChain ChatAnthropic."""
    with patch("src.agent.debate.participant.ChatAnthropic") as mock_class:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "This is a mock LLM response for testing."
        mock_response.usage_metadata = {"input_tokens": 100, "output_tokens": 50}
        mock_instance.invoke.return_value = mock_response
        mock_class.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Participant Initialization Tests
# =============================================================================


class TestParticipantInit:
    """Tests for Participant initialization."""

    def test_properties(self, bull_config, mock_llm):
        """Test participant properties are accessible."""
        participant = Participant(config=bull_config)

        assert participant.id == "test_bull"
        assert participant.name == "Test Bull"
        assert participant.stance == DebateStance.BUY

    def test_model_initialization(self, bull_config, mock_llm):
        """Test LLM is initialized with correct parameters."""
        with patch("src.agent.debate.participant.ChatAnthropic") as mock_class:
            Participant(
                config=bull_config,
                model="claude-3-haiku",
                max_tokens=300,
            )

            mock_class.assert_called_once_with(
                model="claude-3-haiku",
                max_tokens=300,
                temperature=0.7,
            )


# =============================================================================
# System Prompt Tests
# =============================================================================


class TestSystemPrompt:
    """Tests for system prompt construction."""

    def test_includes_persona(self, bull_config, mock_llm):
        """Test system prompt includes persona."""
        participant = Participant(config=bull_config)
        prompt = participant._build_system_prompt()

        assert "You are a bullish analyst." in prompt

    def test_includes_style_hints(self, bull_config, mock_llm):
        """Test system prompt includes style hints."""
        participant = Participant(config=bull_config)
        prompt = participant._build_system_prompt()

        assert "Focus on value" in prompt
        assert "Be optimistic" in prompt

    def test_includes_guidelines(self, bull_config, mock_llm):
        """Test system prompt includes standard guidelines."""
        participant = Participant(config=bull_config)
        prompt = participant._build_system_prompt()

        assert "concise" in prompt.lower()
        assert "evidence" in prompt.lower()


# =============================================================================
# Opening Prompt Tests
# =============================================================================


class TestOpeningPrompt:
    """Tests for opening statement prompt construction."""

    def test_includes_stock_info(self, bull_config, sample_stock_context, mock_llm):
        """Test opening prompt includes stock context."""
        participant = Participant(config=bull_config)
        prompt = participant._build_opening_prompt(
            sample_stock_context, "Opponent Name"
        )

        assert "AAPL" in prompt
        assert "Apple Inc." in prompt

    def test_includes_opponent_name(self, bull_config, sample_stock_context, mock_llm):
        """Test opening prompt includes opponent name."""
        participant = Participant(config=bull_config)
        prompt = participant._build_opening_prompt(sample_stock_context, "Sarah Bear")

        assert "Sarah Bear" in prompt

    def test_buy_stance_prompt(self, bull_config, sample_stock_context, mock_llm):
        """Test buy stance uses correct action word."""
        participant = Participant(config=bull_config)
        prompt = participant._build_opening_prompt(
            sample_stock_context, "Opponent"
        )

        assert "BUY" in prompt

    def test_avoid_stance_prompt(self, bear_config, sample_stock_context, mock_llm):
        """Test avoid stance uses correct action word."""
        participant = Participant(config=bear_config)
        prompt = participant._build_opening_prompt(
            sample_stock_context, "Opponent"
        )

        assert "AVOID" in prompt


# =============================================================================
# Rebuttal Prompt Tests
# =============================================================================


class TestRebuttalPrompt:
    """Tests for rebuttal prompt construction."""

    def test_includes_opponent_argument(
        self, bull_config, sample_stock_context, mock_llm
    ):
        """Test rebuttal prompt includes opponent's statement."""
        participant = Participant(config=bull_config)
        opponent_statement = DebateStatement(
            participant_id="bear",
            participant_name="Bear Analyst",
            stance=DebateStance.AVOID,
            phase=DebatePhase.OPENING,
            content="This stock is too risky to buy right now.",
        )
        prompt = participant._build_rebuttal_prompt(
            sample_stock_context, opponent_statement
        )

        assert "too risky to buy" in prompt
        assert "Bear Analyst" in prompt

    def test_includes_stock_context(self, bull_config, sample_stock_context, mock_llm):
        """Test rebuttal prompt includes stock context."""
        participant = Participant(config=bull_config)
        opponent_statement = DebateStatement(
            participant_id="bear",
            participant_name="Bear",
            stance=DebateStance.AVOID,
            phase=DebatePhase.OPENING,
            content="Avoid it.",
        )
        prompt = participant._build_rebuttal_prompt(
            sample_stock_context, opponent_statement
        )

        assert "AAPL" in prompt


# =============================================================================
# Generation Tests
# =============================================================================


class TestGeneration:
    """Tests for LLM generation."""

    def test_generate_opening_returns_statement(
        self, bull_config, sample_stock_context, mock_llm
    ):
        """Test generate_opening returns a DebateStatement."""
        participant = Participant(config=bull_config)
        result = participant.generate_opening(sample_stock_context, "Opponent")

        assert isinstance(result, DebateStatement)
        assert result.participant_id == "test_bull"
        assert result.participant_name == "Test Bull"
        assert result.stance == DebateStance.BUY
        assert result.phase == DebatePhase.OPENING
        assert result.content == "This is a mock LLM response for testing."

    def test_generate_opening_tracks_tokens(
        self, bull_config, sample_stock_context, mock_llm
    ):
        """Test token count is captured."""
        participant = Participant(config=bull_config)
        result = participant.generate_opening(sample_stock_context, "Opponent")

        assert result.token_count == 150  # 100 input + 50 output

    def test_generate_opening_tracks_time(
        self, bull_config, sample_stock_context, mock_llm
    ):
        """Test generation time is captured."""
        participant = Participant(config=bull_config)
        result = participant.generate_opening(sample_stock_context, "Opponent")

        assert result.generation_time_ms is not None
        assert result.generation_time_ms >= 0

    def test_generate_rebuttal_returns_statement(
        self, bull_config, sample_stock_context, mock_llm
    ):
        """Test generate_rebuttal returns a DebateStatement."""
        participant = Participant(config=bull_config)
        opponent_statement = DebateStatement(
            participant_id="bear",
            participant_name="Bear",
            stance=DebateStance.AVOID,
            phase=DebatePhase.OPENING,
            content="Avoid it.",
        )
        result = participant.generate_rebuttal(sample_stock_context, opponent_statement)

        assert isinstance(result, DebateStatement)
        assert result.phase == DebatePhase.REBUTTAL


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_default_participants(self, mock_llm):
        """Test default participants are created correctly."""
        bull, bear = create_default_participants()

        assert bull.stance == DebateStance.BUY
        assert bear.stance == DebateStance.AVOID
        assert bull.name == "Alex Chen"
        assert bear.name == "Sarah Martinez"

    def test_create_default_participants_custom_model(self, mock_llm):
        """Test custom model is passed through."""
        with patch("src.agent.debate.participant.ChatAnthropic") as mock_class:
            create_default_participants(model="claude-3-haiku", max_tokens=300)

            # Called twice (once for bull, once for bear)
            assert mock_class.call_count == 2
            # Check first call
            call_args = mock_class.call_args_list[0]
            assert call_args.kwargs["model"] == "claude-3-haiku"
            assert call_args.kwargs["max_tokens"] == 300

    def test_create_participant_from_config(self, mock_llm):
        """Test participant creation from config dict."""
        config_dict = {
            "id": "custom_bull",
            "name": "Custom Bull",
            "stance": "buy",
            "persona": "You are a custom analyst.",
            "style": ["Be bold", "Use numbers"],
            "temperature": 0.9,
        }
        participant = create_participant_from_config(config_dict)

        assert participant.id == "custom_bull"
        assert participant.name == "Custom Bull"
        assert participant.stance == DebateStance.BUY
        assert participant.config.temperature == 0.9

    def test_create_participant_from_config_defaults(self, mock_llm):
        """Test config dict with minimal values uses defaults."""
        config_dict = {
            "stance": "avoid",
        }
        participant = create_participant_from_config(config_dict)

        assert participant.stance == DebateStance.AVOID
        assert participant.name == "Analyst"  # default


# =============================================================================
# Default Persona Tests
# =============================================================================


class TestDefaultPersonas:
    """Tests for default persona configurations."""

    def test_default_bull_persona_exists(self):
        """Test default bull persona is defined."""
        assert DEFAULT_BULL_PERSONA is not None
        assert DEFAULT_BULL_PERSONA.stance == DebateStance.BUY
        assert DEFAULT_BULL_PERSONA.name == "Alex Chen"
        assert len(DEFAULT_BULL_PERSONA.style_hints) > 0

    def test_default_bear_persona_exists(self):
        """Test default bear persona is defined."""
        assert DEFAULT_BEAR_PERSONA is not None
        assert DEFAULT_BEAR_PERSONA.stance == DebateStance.AVOID
        assert DEFAULT_BEAR_PERSONA.name == "Sarah Martinez"
        assert len(DEFAULT_BEAR_PERSONA.style_hints) > 0
