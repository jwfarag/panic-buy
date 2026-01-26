# Debate Formatter
# ================
# Output formatting utilities for debate results.

import json
from typing import Optional

from .models import DebateResult, DebateStance


def format_markdown(result: DebateResult, include_metadata: bool = False) -> str:
    """
    Format debate result as human-readable markdown.

    Args:
        result: The debate result to format
        include_metadata: Whether to include timing/token metadata

    Returns:
        Formatted markdown string
    """
    lines = [
        f"# Stock Debate: {result.company_name} ({result.ticker})",
        f"**Date:** {result.debate_date}",
        "",
    ]

    # Participants
    if result.participants:
        bull = next((p for p in result.participants if p.stance == DebateStance.BUY), None)
        bear = next((p for p in result.participants if p.stance == DebateStance.AVOID), None)
        if bull and bear:
            lines.append(f"**Debaters:** {bull.name} (Bull) vs {bear.name} (Bear)")
            lines.append("")

    # Opening statements
    lines.append("---")
    lines.append("## Opening Statements")
    lines.append("")

    for stmt in result.opening_statements:
        stance_tag = "[BUY]" if stmt.stance == DebateStance.BUY else "[AVOID]"
        lines.append(f"### {stmt.participant_name} {stance_tag}")
        lines.append("")
        lines.append(stmt.content)
        lines.append("")

    # Rebuttals
    if result.rebuttals:
        lines.append("---")
        lines.append("## Rebuttals")
        lines.append("")

        for stmt in result.rebuttals:
            stance_tag = "[BUY]" if stmt.stance == DebateStance.BUY else "[AVOID]"
            lines.append(f"### {stmt.participant_name} {stance_tag}")
            lines.append("")
            lines.append(stmt.content)
            lines.append("")

    # Summary
    if result.summary:
        lines.append("---")
        lines.append("## Summary")
        lines.append("")
        lines.append(result.summary)
        lines.append("")

    # Metadata
    if include_metadata:
        lines.append("---")
        lines.append("## Metadata")
        lines.append("")
        if result.duration_seconds:
            lines.append(f"- **Duration:** {result.duration_seconds:.1f}s")
        lines.append(f"- **Total tokens:** {result.total_tokens}")
        lines.append(f"- **Model:** {result.config_snapshot.get('model', 'unknown')}")
        lines.append("")

    return "\n".join(lines)


def format_json(result: DebateResult, indent: int = 2) -> str:
    """
    Format debate result as JSON string.

    Args:
        result: The debate result to format
        indent: JSON indentation level

    Returns:
        JSON string
    """
    return json.dumps(result.to_dict(), indent=indent, default=str)


def format_short(result: DebateResult) -> str:
    """
    Format debate result as a condensed summary for reports.

    Args:
        result: The debate result to format

    Returns:
        Short formatted string (suitable for inclusion in larger reports)
    """
    lines = [
        f"### {result.company_name} ({result.ticker}) Debate",
        "",
    ]

    # Get participant names
    bull_name = "Bull"
    bear_name = "Bear"
    for p in result.participants:
        if p.stance == DebateStance.BUY:
            bull_name = p.name
        else:
            bear_name = p.name

    # Opening summaries (first sentence of each)
    for stmt in result.opening_statements:
        first_sentence = stmt.content.split(".")[0] + "."
        if stmt.stance == DebateStance.BUY:
            lines.append(f"**{bull_name} (Buy):** {first_sentence}")
        else:
            lines.append(f"**{bear_name} (Avoid):** {first_sentence}")

    lines.append("")

    # Summary if available
    if result.summary:
        lines.append(f"**Summary:** {result.summary[:300]}...")

    return "\n".join(lines)


def format_for_report(
    result: DebateResult,
    max_length: Optional[int] = None,
) -> str:
    """
    Format debate result for inclusion in a daily report.

    Args:
        result: The debate result to format
        max_length: Optional maximum length (truncates if exceeded)

    Returns:
        Formatted string suitable for report inclusion
    """
    output = format_markdown(result, include_metadata=False)

    if max_length and len(output) > max_length:
        # Truncate and add indicator
        output = output[: max_length - 20] + "\n\n[Truncated...]"

    return output
