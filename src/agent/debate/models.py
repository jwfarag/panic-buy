# Debate Models
# =============
# Data structures for the stock debate agents module.

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DebateStance(Enum):
    """Position a participant takes in the debate."""

    BUY = "buy"
    AVOID = "avoid"


class DebatePhase(Enum):
    """Phases of the debate."""

    OPENING = "opening"
    REBUTTAL = "rebuttal"
    SUMMARY = "summary"


# =============================================================================
# Input Models
# =============================================================================


@dataclass
class StockContext:
    """
    Input context for a debate about a stock.

    Aggregates all information participants need to form arguments.
    """

    ticker: str
    company_name: str
    debate_date: date

    # Day's performance
    price_change_pct: float  # e.g., -0.08 for -8%
    open_price: float
    close_price: float
    volume: int
    volume_vs_average: float  # e.g., 2.5 for 250% of average

    # Related news articles
    # Each article: {"title": str, "summary": str, "source": str, "published_at": str}
    articles: List[Dict[str, Any]] = field(default_factory=list)

    # Optional enrichment (for future versions)
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    beta: Optional[float] = None

    # Default fields to extract from article dicts
    DEFAULT_ARTICLE_FIELDS = ["source", "title", "summary", "content"]

    def format_for_prompt(
        self,
        max_articles: int = 5,
        article_fields: Optional[List[str]] = None,
    ) -> str:
        """
        Format context for injection into prompts.

        Args:
            max_articles: Maximum number of articles to include (default: 5)
            article_fields: List of field names to extract from each article dict.
                           Fields are joined with " | ". Missing fields are skipped.
                           Default: ["source", "title", "summary", "content"]

        Returns:
            Formatted string suitable for prompt injection
        """
        fields = article_fields or self.DEFAULT_ARTICLE_FIELDS
        news_lines = []

        for article in self.articles[:max_articles]:
            parts = [str(article.get(f)) for f in fields if article.get(f)]
            if parts:
                news_lines.append(f"- {' | '.join(parts)}")

        news_text = "\n".join(news_lines) or "No recent news available."

        return f"""Stock: {self.company_name} ({self.ticker})
Date: {self.debate_date}
Price Change: {self.price_change_pct:+.2%}
Close: ${self.close_price:.2f} (Open: ${self.open_price:.2f})
Volume: {self.volume:,} ({self.volume_vs_average:.1f}x average)

Recent News:
{news_text}"""


# =============================================================================
# Participant Configuration
# =============================================================================


@dataclass
class ParticipantConfig:
    """
    Configuration for a debate participant.

    Placeholder personas can be swapped by changing these fields.
    """

    id: str  # Unique identifier
    name: str  # Display name
    stance: DebateStance  # BUY or AVOID
    persona: str  # Injected into system prompt
    style_hints: List[str] = field(default_factory=list)
    temperature: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "stance": self.stance.value,
            "persona": self.persona,
            "style_hints": self.style_hints,
            "temperature": self.temperature,
        }


# =============================================================================
# Output Models
# =============================================================================


@dataclass
class DebateStatement:
    """A single statement made during the debate."""

    participant_id: str
    participant_name: str
    stance: DebateStance
    phase: DebatePhase
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Metadata for analysis
    token_count: Optional[int] = None
    generation_time_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "participant_name": self.participant_name,
            "stance": self.stance.value,
            "phase": self.phase.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
            "generation_time_ms": self.generation_time_ms,
        }


@dataclass
class DebateResult:
    """
    Complete output of a stock debate.

    Contains all statements plus formatted final output.
    """

    ticker: str
    company_name: str
    debate_date: date

    # The debate itself
    opening_statements: List[DebateStatement] = field(default_factory=list)
    rebuttals: List[DebateStatement] = field(default_factory=list)
    summary: Optional[str] = None

    # Metadata
    participants: List[ParticipantConfig] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tokens: int = 0

    # Configuration used (for reproducibility)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON export."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "debate_date": self.debate_date.isoformat(),
            "opening_statements": [s.to_dict() for s in self.opening_statements],
            "rebuttals": [s.to_dict() for s in self.rebuttals],
            "summary": self.summary,
            "participants": [p.to_dict() for p in self.participants],
            "metadata": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_seconds": self.duration_seconds,
                "total_tokens": self.total_tokens,
            },
            "config_snapshot": self.config_snapshot,
        }


# =============================================================================
# Orchestrator Configuration
# =============================================================================


@dataclass
class DebateConfig:
    """Configuration for debate orchestration."""

    # Model settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens_opening: int = 500
    max_tokens_rebuttal: int = 400
    max_tokens_summary: int = 300

    # Phase toggles
    include_rebuttals: bool = True
    include_summary: bool = True

    # Debate order
    bull_opens_first: bool = True

    # Summary settings
    summary_temperature: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "max_tokens_opening": self.max_tokens_opening,
            "max_tokens_rebuttal": self.max_tokens_rebuttal,
            "max_tokens_summary": self.max_tokens_summary,
            "include_rebuttals": self.include_rebuttals,
            "include_summary": self.include_summary,
            "bull_opens_first": self.bull_opens_first,
            "summary_temperature": self.summary_temperature,
        }
