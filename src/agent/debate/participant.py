# Debate Participant
# ==================
# LangChain-based participant for stock debates.

import logging
import time
from pathlib import Path
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from .models import (
    DebatePhase,
    DebateStance,
    DebateStatement,
    ParticipantConfig,
    StockContext,
)

logger = logging.getLogger(__name__)

# Path to prompt templates
PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "debate"


# =============================================================================
# Default Personas
# =============================================================================

DEFAULT_BULL_PERSONA = ParticipantConfig(
    id="bull_analyst",
    name="Alex Chen",
    stance=DebateStance.BUY,
    persona="""You are Alex Chen, a seasoned value investor with 15 years of experience
finding opportunities in market overreactions. You believe markets often panic over
short-term news, creating buying opportunities in quality companies. You look for
strong fundamentals, competitive moats, and management track records.""",
    style_hints=[
        "Focus on long-term value",
        "Cite historical precedents of recoveries",
        "Acknowledge risks but emphasize opportunity",
        "Use specific data points to support arguments",
    ],
    temperature=0.7,
)

DEFAULT_BEAR_PERSONA = ParticipantConfig(
    id="bear_analyst",
    name="Sarah Martinez",
    stance=DebateStance.AVOID,
    persona="""You are Sarah Martinez, a risk-focused analyst known for protecting
clients from value traps. You've seen too many investors catch falling knives by
ignoring warning signs. You prioritize capital preservation and believe in waiting
for clear evidence of stabilization before buying.""",
    style_hints=[
        "Focus on risk factors and what could go wrong",
        "Question assumptions about recovery",
        "Cite examples of stocks that didn't recover",
        "Emphasize uncertainty and unknowns",
    ],
    temperature=0.7,
)


# =============================================================================
# Participant Class
# =============================================================================


class Participant:
    """
    A debate participant powered by LangChain.

    Encapsulates persona, stance, and LLM interactions for generating
    debate statements. Designed for basic prompting (no tools).
    """

    def __init__(
        self,
        config: ParticipantConfig,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 500,
    ):
        """
        Initialize a debate participant.

        Args:
            config: Participant configuration with persona details
            model: Model name for LangChain
            max_tokens: Maximum tokens per response
        """
        self.config = config
        self.model_name = model
        self.max_tokens = max_tokens

        # Initialize LangChain chat model
        self._llm = ChatAnthropic(
            model=model,
            max_tokens=max_tokens,
            temperature=config.temperature,
        )

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def stance(self) -> DebateStance:
        return self.config.stance

    def generate_opening(
        self,
        context: StockContext,
        opponent_name: str,
    ) -> DebateStatement:
        """
        Generate opening statement for the debate.

        Args:
            context: Stock information and news
            opponent_name: Name of the opposing participant

        Returns:
            DebateStatement with the opening argument
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_opening_prompt(context, opponent_name)

        return self._generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            phase=DebatePhase.OPENING,
        )

    def generate_rebuttal(
        self,
        context: StockContext,
        opponent_statement: DebateStatement,
    ) -> DebateStatement:
        """
        Generate rebuttal to opponent's opening statement.

        Args:
            context: Stock information and news
            opponent_statement: The opponent's opening statement to rebut

        Returns:
            DebateStatement with the rebuttal
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_rebuttal_prompt(context, opponent_statement)

        return self._generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            phase=DebatePhase.REBUTTAL,
        )

    def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        phase: DebatePhase,
    ) -> DebateStatement:
        """Execute LLM call and return structured statement."""
        start_time = time.time()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self._llm.invoke(messages)
            content = response.content

            # Extract token usage if available
            token_count = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                token_count = (
                    response.usage_metadata.get("input_tokens", 0)
                    + response.usage_metadata.get("output_tokens", 0)
                )

        except Exception as e:
            logger.error(f"LLM generation failed for {self.name}: {e}")
            raise

        elapsed_ms = int((time.time() - start_time) * 1000)

        return DebateStatement(
            participant_id=self.id,
            participant_name=self.name,
            stance=self.stance,
            phase=phase,
            content=content.strip(),
            token_count=token_count,
            generation_time_ms=elapsed_ms,
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt with persona."""
        style_hints = "\n".join([f"- {hint}" for hint in self.config.style_hints])

        return f"""{self.config.persona}

Your argument style:
{style_hints}

Guidelines:
- Keep responses concise and punchy (follow the word limits in the prompt)
- Be entertaining but substantive
- Support claims with specific evidence from the provided context
- Stay in character throughout
- You may concede genuinely strong points, but explain why they don't change your conclusion"""

    def _build_opening_prompt(self, context: StockContext, opponent_name: str) -> str:
        """Build prompt for opening statement."""
        template = self._load_prompt_template("opening")
        price_change = f"{context.price_change_pct:+.1%}"

        return template.format(
            ticker=context.ticker,
            company_name=context.company_name,
            price_change=price_change,
            context=context.format_for_prompt(),
            opponent_name=opponent_name,
        )

    def _build_rebuttal_prompt(
        self,
        context: StockContext,
        opponent_statement: DebateStatement,
    ) -> str:
        """Build prompt for rebuttal."""
        template = self._load_prompt_template("rebuttal")
        stance_action = "BUY" if self.stance == DebateStance.BUY else "AVOID"

        return template.format(
            ticker=context.ticker,
            company_name=context.company_name,
            stance=stance_action,
            context=context.format_for_prompt(),
            opponent_name=opponent_statement.participant_name,
            opponent_argument=opponent_statement.content,
        )

    def _load_prompt_template(self, template_type: str) -> str:
        """Load a prompt template from file."""
        if template_type == "opening":
            filename = f"opening_{self.stance.value}.txt"
        else:
            filename = f"{template_type}.txt"

        template_path = PROMPTS_DIR / filename

        if template_path.exists():
            return template_path.read_text()

        # Fallback to inline templates if file not found
        logger.warning(f"Template not found: {template_path}, using fallback")
        return self._get_fallback_template(template_type)

    def _get_fallback_template(self, template_type: str) -> str:
        """Fallback templates if files are missing."""
        if template_type == "opening":
            stance = "BUY" if self.stance == DebateStance.BUY else "AVOID"
            return f"""You are debating whether to {stance} {{company_name}} ({{ticker}}).

Your opponent is {{opponent_name}}.

## Context
{{context}}

Make your opening statement arguing why investors should {stance} this stock.
Keep it to 2-3 paragraphs."""

        return """You are responding to your opponent's argument.

## Context
{context}

## Opponent's Argument ({opponent_name})
{opponent_argument}

Deliver a sharp rebuttal. 2 paragraphs max."""


# =============================================================================
# Factory Functions
# =============================================================================


def create_default_participants(
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 500,
) -> tuple:
    """
    Factory function to create default bull/bear participants.

    Args:
        model: LangChain model name
        max_tokens: Max tokens per response

    Returns:
        Tuple of (bull_participant, bear_participant)
    """
    bull = Participant(
        config=DEFAULT_BULL_PERSONA,
        model=model,
        max_tokens=max_tokens,
    )
    bear = Participant(
        config=DEFAULT_BEAR_PERSONA,
        model=model,
        max_tokens=max_tokens,
    )
    return bull, bear


def create_participant_from_config(
    config_dict: dict,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 500,
) -> Participant:
    """
    Create a participant from a configuration dictionary.

    Args:
        config_dict: Dictionary with participant config (from YAML)
        model: LangChain model name
        max_tokens: Max tokens per response

    Returns:
        Configured Participant instance
    """
    stance = DebateStance(config_dict.get("stance", "buy"))

    config = ParticipantConfig(
        id=config_dict.get("id", f"{stance.value}_analyst"),
        name=config_dict.get("name", "Analyst"),
        stance=stance,
        persona=config_dict.get("persona", "You are a financial analyst."),
        style_hints=config_dict.get("style", []),
        temperature=config_dict.get("temperature", 0.7),
    )

    return Participant(config=config, model=model, max_tokens=max_tokens)
