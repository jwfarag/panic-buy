# Stock Debate Agents Module
# ==========================
# LangChain-based debate system for stock analysis.
#
# This module creates structured debates between AI participants
# arguing opposing positions (buy vs. avoid) on stocks that have
# experienced significant price drops.
#
# Usage:
#     from src.agent.debate import DebateOrchestrator, StockContext
#
#     context = StockContext(
#         ticker="AAPL",
#         company_name="Apple Inc.",
#         debate_date=date.today(),
#         price_change_pct=-0.08,
#         open_price=185.00,
#         close_price=170.20,
#         volume=150_000_000,
#         volume_vs_average=2.5,
#         articles=[{"title": "...", "summary": "...", "source": "..."}]
#     )
#
#     orchestrator = DebateOrchestrator()
#     result = orchestrator.run_debate(context)
#     print(result.format_readable())

from .models import (
    DebateConfig,
    DebatePhase,
    DebateResult,
    DebateStance,
    DebateStatement,
    ParticipantConfig,
    StockContext,
)
from .orchestrator import DebateOrchestrator, create_orchestrator_from_config
from .participant import (
    Participant,
    create_default_participants,
    create_participant_from_config,
)
from .formatter import (
    format_for_report,
    format_json,
    format_markdown,
    format_short,
)

__all__ = [
    # Models
    "StockContext",
    "ParticipantConfig",
    "DebateStatement",
    "DebateResult",
    "DebateConfig",
    "DebateStance",
    "DebatePhase",
    # Participant
    "Participant",
    "create_default_participants",
    "create_participant_from_config",
    # Orchestrator
    "DebateOrchestrator",
    "create_orchestrator_from_config",
    # Formatter
    "format_markdown",
    "format_json",
    "format_short",
    "format_for_report",
]
