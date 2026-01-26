#!/usr/bin/env python3
"""
Run a stock debate with sample data.

Usage:
    python scripts/run_debate.py
    python scripts/run_debate.py --ticker AAPL --company "Apple Inc."
    python scripts/run_debate.py --no-rebuttals --no-summary
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.debate import (
    DebateConfig,
    DebateOrchestrator,
    StockContext,
    format_markdown,
)


def create_sample_context(
    ticker: str = "AAPL",
    company_name: str = "Apple Inc.",
) -> StockContext:
    """Create a sample StockContext with dummy data."""
    return StockContext(
        ticker=ticker,
        company_name=company_name,
        debate_date=date.today(),
        price_change_pct=-0.082,  # -8.2%
        open_price=185.50,
        close_price=170.30,
        volume=152_000_000,
        volume_vs_average=2.4,
        articles=[
            {
                "source": "Reuters",
                "title": "Apple misses Q3 revenue estimates amid China slowdown",
                "summary": "Apple reported quarterly revenue of $81.8B, below analyst expectations of $84.5B, citing weaker iPhone sales in Greater China.",
                "content": "Apple Inc reported fiscal third-quarter revenue that missed Wall Street estimates...",
            },
            {
                "source": "Bloomberg",
                "title": "Morgan Stanley downgrades Apple to Equal Weight",
                "summary": "Analyst Erik Woodring cut the rating citing near-term headwinds in services growth and iPhone replacement cycles.",
            },
            {
                "source": "CNBC",
                "title": "Apple stock drops 8% in heaviest trading day of 2024",
                "summary": "Shares fell sharply as investors reassessed growth prospects following disappointing guidance for the holiday quarter.",
            },
            {
                "source": "WSJ",
                "title": "Apple's China problem deepens as Huawei gains ground",
                "summary": "Market share data shows Apple losing ground to domestic competitors in its second-largest market.",
            },
        ],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run a stock debate with sample or custom data"
    )
    parser.add_argument(
        "--ticker",
        default="AAPL",
        help="Stock ticker symbol (default: AAPL)",
    )
    parser.add_argument(
        "--company",
        default="Apple Inc.",
        help="Company name (default: Apple Inc.)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--no-rebuttals",
        action="store_true",
        help="Skip the rebuttal phase",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip the summary phase",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of markdown",
    )

    args = parser.parse_args()

    # Create sample context
    print(f"Creating debate for {args.company} ({args.ticker})...")
    context = create_sample_context(
        ticker=args.ticker,
        company_name=args.company,
    )

    # Configure the debate
    config = DebateConfig(
        model=args.model,
        include_rebuttals=not args.no_rebuttals,
        include_summary=not args.no_summary,
    )

    # Run the debate
    print(f"Running debate (rebuttals: {config.include_rebuttals}, summary: {config.include_summary})...")
    print("-" * 60)

    orchestrator = DebateOrchestrator(config=config)
    result = orchestrator.run_debate(context)

    # Output
    if args.json:
        from src.agent.debate import format_json
        print(format_json(result))
    else:
        print(format_markdown(result, include_metadata=True))

    # Summary stats
    print("-" * 60)
    print(f"Completed in {result.duration_seconds:.1f}s")
    print(f"Total tokens: {result.total_tokens}")


if __name__ == "__main__":
    main()
