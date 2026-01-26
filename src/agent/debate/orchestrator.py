# Debate Orchestrator
# ===================
# Coordinates the debate flow between participants.

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from .models import (
    DebateConfig,
    DebatePhase,
    DebateResult,
    DebateStance,
    DebateStatement,
    ParticipantConfig,
    StockContext,
)
from .participant import Participant, create_default_participants

logger = logging.getLogger(__name__)

# Path to prompt templates
PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "debate"


class DebateOrchestrator:
    """
    Orchestrates a structured debate between two participants.

    Flow:
    1. Opening statements (both sides)
    2. Rebuttals (both sides respond to opponent's opening)
    3. Summary (neutral synthesis)

    All phases are toggleable via DebateConfig.
    """

    def __init__(
        self,
        config: Optional[DebateConfig] = None,
        participants: Optional[Tuple[Participant, Participant]] = None,
    ):
        """
        Initialize the debate orchestrator.

        Args:
            config: Debate configuration (uses defaults if None)
            participants: Tuple of (bull, bear) Participant objects.
                         If None, creates default participants.
        """
        self.config = config or DebateConfig()

        if participants:
            self.bull, self.bear = participants
        else:
            self.bull, self.bear = create_default_participants(
                model=self.config.model,
                max_tokens=self.config.max_tokens_opening,
            )

        # LLM for summary generation (separate from participants)
        self._summary_llm = ChatAnthropic(
            model=self.config.model,
            max_tokens=self.config.max_tokens_summary,
            temperature=self.config.summary_temperature,
        )

    def run_debate(self, context: StockContext) -> DebateResult:
        """
        Execute a full debate on the given stock.

        Args:
            context: Stock information and news for the debate

        Returns:
            DebateResult with all statements and summary
        """
        logger.info(f"Starting debate for {context.ticker}")
        started_at = datetime.now()

        result = DebateResult(
            ticker=context.ticker,
            company_name=context.company_name,
            debate_date=context.debate_date,
            participants=[self.bull.config, self.bear.config],
            started_at=started_at,
            config_snapshot=self.config.to_dict(),
        )

        # Phase 1: Opening statements
        logger.info("Phase 1: Opening statements")
        openings = self._run_openings(context)
        result.opening_statements = openings

        # Phase 2: Rebuttals (optional)
        if self.config.include_rebuttals:
            logger.info("Phase 2: Rebuttals")
            rebuttals = self._run_rebuttals(context, openings)
            result.rebuttals = rebuttals

        # Phase 3: Summary (optional)
        if self.config.include_summary:
            logger.info("Phase 3: Summary")
            result.summary = self._generate_summary(context, result)

        result.completed_at = datetime.now()
        result.total_tokens = self._calculate_total_tokens(result)

        logger.info(
            f"Debate completed for {context.ticker} "
            f"in {result.duration_seconds:.1f}s, "
            f"{result.total_tokens} tokens"
        )

        return result

    def _run_openings(self, context: StockContext) -> List[DebateStatement]:
        """Generate opening statements from both participants."""
        openings = []

        # Determine order
        if self.config.bull_opens_first:
            first, second = self.bull, self.bear
        else:
            first, second = self.bear, self.bull

        # Update token limits
        first.max_tokens = self.config.max_tokens_opening
        second.max_tokens = self.config.max_tokens_opening

        # First participant opens
        logger.debug(f"Generating opening from {first.name}")
        opening_1 = first.generate_opening(context, second.name)
        openings.append(opening_1)
        logger.debug(f"Opening from {first.name}: {len(opening_1.content)} chars")

        # Second participant opens
        logger.debug(f"Generating opening from {second.name}")
        opening_2 = second.generate_opening(context, first.name)
        openings.append(opening_2)
        logger.debug(f"Opening from {second.name}: {len(opening_2.content)} chars")

        return openings

    def _run_rebuttals(
        self,
        context: StockContext,
        openings: List[DebateStatement],
    ) -> List[DebateStatement]:
        """Generate rebuttals responding to opponent's opening."""
        rebuttals = []

        # Find opening statements by stance
        bull_opening = next(s for s in openings if s.stance == DebateStance.BUY)
        bear_opening = next(s for s in openings if s.stance == DebateStance.AVOID)

        # Update token limits for rebuttals
        self.bull.max_tokens = self.config.max_tokens_rebuttal
        self.bear.max_tokens = self.config.max_tokens_rebuttal

        # Bull rebuts bear's opening
        logger.debug(f"Generating rebuttal from {self.bull.name}")
        bull_rebuttal = self.bull.generate_rebuttal(context, bear_opening)
        rebuttals.append(bull_rebuttal)

        # Bear rebuts bull's opening
        logger.debug(f"Generating rebuttal from {self.bear.name}")
        bear_rebuttal = self.bear.generate_rebuttal(context, bull_opening)
        rebuttals.append(bear_rebuttal)

        return rebuttals

    def _generate_summary(
        self,
        context: StockContext,
        result: DebateResult,
    ) -> str:
        """Generate a neutral summary synthesizing both perspectives."""
        # Build debate transcript
        transcript = self._format_transcript_for_summary(result)

        # Load summary template
        template = self._load_summary_template()

        system_prompt = """You are a neutral financial analyst summarizing a debate.
Your job is to provide a balanced, concise summary that:
1. Captures the strongest points from both sides
2. Identifies the crux of the disagreement
3. Helps the reader make an informed decision
4. Remains neutral - do NOT pick a winner or make a recommendation

Keep the summary punchy and engaging while being substantive."""

        user_prompt = template.format(
            ticker=context.ticker,
            company_name=context.company_name,
            context=context.format_for_prompt(),
            debate_transcript=transcript,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self._summary_llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "[Summary generation failed]"

    def _format_transcript_for_summary(self, result: DebateResult) -> str:
        """Format debate statements into a transcript for the summary prompt."""
        lines = []

        # Opening statements
        for stmt in result.opening_statements:
            stance_label = "BUY" if stmt.stance == DebateStance.BUY else "AVOID"
            lines.append(f"**{stmt.participant_name} ({stance_label}) - Opening:**")
            lines.append(stmt.content)
            lines.append("")

        # Rebuttals
        for stmt in result.rebuttals:
            stance_label = "BUY" if stmt.stance == DebateStance.BUY else "AVOID"
            lines.append(f"**{stmt.participant_name} ({stance_label}) - Rebuttal:**")
            lines.append(stmt.content)
            lines.append("")

        return "\n".join(lines)

    def _load_summary_template(self) -> str:
        """Load the summary prompt template."""
        template_path = PROMPTS_DIR / "summary.txt"

        if template_path.exists():
            return template_path.read_text()

        # Fallback template
        return """Summarize this debate about {company_name} ({ticker}).

## Stock Context
{context}

## The Debate
{debate_transcript}

Provide a balanced summary covering both perspectives."""

    def _calculate_total_tokens(self, result: DebateResult) -> int:
        """Calculate total tokens used in the debate."""
        total = 0
        for stmt in result.opening_statements + result.rebuttals:
            if stmt.token_count:
                total += stmt.token_count
        return total


# =============================================================================
# Factory Functions
# =============================================================================


def create_orchestrator_from_config(config_dict: Dict[str, Any]) -> DebateOrchestrator:
    """
    Create an orchestrator from a configuration dictionary (e.g., from YAML).

    Args:
        config_dict: Configuration dictionary with model, structure, participants

    Returns:
        Configured DebateOrchestrator instance
    """
    from .participant import create_participant_from_config

    # Build DebateConfig
    model_config = config_dict.get("model", {})
    structure_config = config_dict.get("structure", {})
    phases = structure_config.get("phases", {})

    debate_config = DebateConfig(
        model=model_config.get("name", "claude-sonnet-4-20250514"),
        max_tokens_opening=model_config.get("max_tokens", {}).get("opening", 500),
        max_tokens_rebuttal=model_config.get("max_tokens", {}).get("rebuttal", 400),
        max_tokens_summary=model_config.get("max_tokens", {}).get("summary", 300),
        include_rebuttals=phases.get("rebuttals", True),
        include_summary=phases.get("summary", True),
        bull_opens_first=structure_config.get("bull_opens_first", True),
    )

    # Build participants if provided
    participants_config = config_dict.get("participants", {})
    participants = None

    if participants_config:
        bull_config = participants_config.get("bull", {})
        bear_config = participants_config.get("bear", {})

        if bull_config and bear_config:
            bull_config["stance"] = "buy"
            bear_config["stance"] = "avoid"

            bull = create_participant_from_config(
                bull_config,
                model=debate_config.model,
                max_tokens=debate_config.max_tokens_opening,
            )
            bear = create_participant_from_config(
                bear_config,
                model=debate_config.model,
                max_tokens=debate_config.max_tokens_opening,
            )
            participants = (bull, bear)

    return DebateOrchestrator(config=debate_config, participants=participants)
