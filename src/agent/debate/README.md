# Stock Debate Agents Module

A LangChain-based module that generates structured debates about whether to buy or avoid a stock after a significant price drop.

## Overview

The debate module creates an entertaining, informative analysis by having two AI participants argue opposing positions:

- **Bull Participant**: Argues why investors should BUY the stock
- **Bear Participant**: Argues why investors should AVOID the stock

The output includes opening statements, rebuttals, and a neutral summary.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DebateOrchestrator                         │
│                                                                 │
│  Input: StockContext                                            │
│    - ticker, company_name                                       │
│    - price_change_pct, volume                                   │
│    - news articles                                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Debate Flow                           │   │
│  │                                                          │   │
│  │  1. OPENING STATEMENTS                                   │   │
│  │     ├── Bull: "Here's why you should buy..."            │   │
│  │     └── Bear: "Here's why you should avoid..."          │   │
│  │                                                          │   │
│  │  2. REBUTTALS                                            │   │
│  │     ├── Bull rebuts Bear's opening                       │   │
│  │     └── Bear rebuts Bull's opening                       │   │
│  │                                                          │   │
│  │  3. SUMMARY                                              │   │
│  │     └── Neutral synthesis of both positions              │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Output: DebateResult                                           │
│    - opening_statements[]                                       │
│    - rebuttals[]                                                │
│    - summary                                                    │
│    - metadata (timing, tokens, config)                          │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### models.py
Core data structures for the module:

| Class | Purpose |
|-------|---------|
| `StockContext` | Input data (ticker, performance, news articles) |
| `ParticipantConfig` | Persona configuration (name, stance, style hints) |
| `DebateStatement` | A single statement from a participant |
| `DebateResult` | Complete debate output with all statements |
| `DebateConfig` | Orchestrator configuration |

### participant.py
The `Participant` class wraps a LangChain chat model with:
- Persona injection via system prompts
- Methods for generating openings and rebuttals
- Token tracking and timing metadata

Default personas are provided but can be swapped via configuration.

### orchestrator.py
The `DebateOrchestrator` coordinates the debate flow:
1. Creates participants from configuration
2. Runs opening statements (parallel-capable)
3. Runs rebuttals (each responds to opponent's opening)
4. Generates neutral summary
5. Assembles final `DebateResult`

All phases are toggleable via `DebateConfig`.

### formatter.py
Output formatting utilities:
- `format_markdown()`: Human-readable debate transcript
- `format_json()`: Machine-parseable output
- `format_short()`: Condensed version for reports

## Usage

```python
from src.agent.debate import DebateOrchestrator, StockContext, DebateConfig

# Create context from your data
context = StockContext(
    ticker="AAPL",
    company_name="Apple Inc.",
    debate_date=date.today(),
    price_change_pct=-0.08,  # -8%
    open_price=185.00,
    close_price=170.20,
    volume=150_000_000,
    volume_vs_average=2.5,
    articles=[
        {"title": "Apple misses Q3 estimates", "summary": "...", "source": "Reuters"}
    ]
)

# Run debate with default settings
orchestrator = DebateOrchestrator()
result = orchestrator.run_debate(context)

# Output
print(result.format_readable())
```

## Configuration

See `config/debate.yaml` for full configuration options:

- Model selection and token limits
- Phase toggles (openings, rebuttals, summary)
- Participant personas and style hints
- Output format preferences

## Integration

The debate module integrates into the main pipeline after ranking:

```
Ranking → Analyst Reports → DEBATE → Daily Report
```

See `src/pipeline/daily_run.py` for integration points.

## Design Principles

1. **Simple**: Each component has a single responsibility
2. **Toggleable**: All phases can be enabled/disabled
3. **Configurable**: Personas and settings live in YAML
4. **Traceable**: Full metadata for debugging and cost tracking
5. **Extensible**: Easy to add new participants or phases
