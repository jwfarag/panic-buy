# Agent Module

This module contains the AI-powered analysis layer for the panic-buy pipeline.
It currently implements a structured debate system (`debate/`) and stubs for a
deeper analyst agent (`analyst.py`, `tools.py`).

## Current Architecture

At present, agents operate on a static `StockContext` object assembled upstream
in the pipeline before any agent is invoked. The participants in a debate receive
a pre-packaged snapshot—price data, volume metrics, and a fixed set of ingested
news articles—and generate arguments solely from that context.

```
Pipeline ingestion
  → drop detection
  → ranking
  → StockContext (static snapshot)
       └── DebateOrchestrator
               ├── Participant (Bull): prompt → LLM → response
               ├── Participant (Bear): prompt → LLM → response
               └── Summary LLM: prompt → response
```

This works, but it limits the quality of agent reasoning. Participants can only
reason about what was collected upstream. They can't follow up on something
interesting they notice, verify a claim, or pull context that wasn't in the
original news window.

---

## Future Vision: Agentic Tooling with MCP

The goal is to evolve from a *pre-fetch everything* model to a *fetch on demand*
model, where agents actively direct their own research using tools, and a
higher-level orchestrator coordinates the flow.

The Model Context Protocol (MCP) is the natural interface layer here. MCP lets
us define discrete, reusable tool servers that any agent in the system can call.
Rather than baking data fetching into the pipeline and hoping the right data
lands in the context window, agents ask for exactly what they need when they need
it.

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT ORCHESTRATOR                          │
│                                                                     │
│  Input: drop candidate (ticker, drop%, date)                        │
│  Output: AnalystReport + DebateResult + ResearchPackage             │
│                                                                     │
│  Coordinates the research phase and debate phase in sequence.       │
│  Manages tool budgets, caching, and error recovery.                 │
└────────────────────────┬────────────────────────────────────────────┘
                         │
          ┌──────────────┴───────────────┐
          ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────────────────┐
│   RESEARCH AGENT     │      │         DEBATE ORCHESTRATOR          │
│                      │      │                                      │
│  Runs before debate. │      │  Receives enriched ResearchPackage.  │
│  Goal: build a rich  │─────▶│                                      │
│  context package by  │      │  ┌────────────────────────────────┐  │
│  directing its own   │      │  │ Bull Participant                │  │
│  tool calls.         │      │  │ - Has tool access for targeted  │  │
│                      │      │  │   follow-up fetches             │  │
│  Tools used:         │      │  │ - Agent loop: reason → tool     │  │
│  - financials        │      │  │   call → reason → respond       │  │
│  - news search       │      │  └────────────────────────────────┘  │
│  - analyst ratings   │      │  ┌────────────────────────────────┐  │
│  - insider activity  │      │  │ Bear Participant                │  │
│  - comparable events │      │  │ - Same tool access as Bull      │  │
│  - macro context     │      │  │ - Independent research means    │  │
│                      │      │  │   legitimately different        │  │
│  Returns:            │      │  │   evidence bases are possible   │  │
│  ResearchPackage     │      │  └────────────────────────────────┘  │
└──────────────────────┘      │  ┌────────────────────────────────┐  │
                              │  │ Summary Agent                  │  │
                              │  │ - Reads full debate transcript  │  │
                              │  │ - May fetch additional context  │  │
                              │  │   to resolve factual disputes   │  │
                              │  └────────────────────────────────┘  │
                              └──────────────────────────────────────┘
```

---

## MCP Server Design

Each MCP server wraps a data source or capability and exposes it as a set of
typed tools. Agents connect to these servers through the MCP protocol. Because
MCP is standardized, the same server can serve the research agent, both debate
participants, and the analyst agent without duplication.

### `market-data` MCP

Wraps market data sources (yfinance, Polygon).

| Tool | Returns |
|------|---------|
| `get_ohlcv(ticker, period, interval)` | Price/volume history |
| `get_fundamentals(ticker)` | P/E, EV/EBITDA, margins, debt/equity, cash |
| `get_volume_profile(ticker, days)` | Volume distribution vs. historical average |
| `get_short_interest(ticker)` | Short interest %, days to cover |
| `get_options_flow(ticker, days)` | Put/call ratio, unusual options activity |

### `news-search` MCP

Wraps news APIs for targeted, query-directed retrieval beyond the pre-ingested
batch.

| Tool | Returns |
|------|---------|
| `search_news(query, days, limit)` | Articles matching a specific query |
| `get_company_news(ticker, days)` | All recent news for a ticker |
| `get_sector_news(sector, days)` | Sector-wide context |
| `get_regulatory_news(ticker, days)` | Regulatory/legal filings and coverage |

### `analyst-intelligence` MCP

Wraps sell-side research data.

| Tool | Returns |
|------|---------|
| `get_analyst_ratings(ticker)` | Consensus rating, price target (mean/hi/lo) |
| `get_rating_changes(ticker, days)` | Recent upgrades/downgrades |
| `get_earnings_estimates(ticker)` | EPS/revenue estimates and revision trends |
| `get_estimate_surprises(ticker, quarters)` | Historical beat/miss history |

### `sec-filings` MCP

Wraps SEC EDGAR for primary source data.

| Tool | Returns |
|------|---------|
| `get_insider_transactions(ticker, days)` | Form 4 filings, insider buys/sells |
| `get_recent_8k(ticker)` | Recent material event disclosures |
| `get_filing_summary(ticker, form_type)` | Summarized 10-Q/10-K content |
| `search_filings(query, ticker)` | Keyword search within filings |

### `comparable-events` MCP

Wraps internal historical data for precedent lookup.

| Tool | Returns |
|------|---------|
| `find_analogous_drops(sector, magnitude, cause_type)` | Similar historical drops with outcomes |
| `get_recovery_stats(conditions)` | Base rate: % recovered, median time, distribution |
| `get_company_drop_history(ticker, years)` | This company's own historical drops |

### `macro-context` MCP

Wraps macro indicators relevant to interpreting a single-stock move.

| Tool | Returns |
|------|---------|
| `get_market_conditions()` | VIX level, SPY trend, market breadth |
| `get_sector_performance(sector, days)` | Is the whole sector down? |
| `get_fed_calendar(days_ahead)` | Upcoming FOMC events, rate expectations |
| `get_credit_spreads()` | HY/IG spreads as systemic risk proxy |

---

## How Participants Become Agentic

Today, `Participant._generate()` is a single-shot LLM call: build a prompt,
call the model, return the response. In an agentic model, this becomes a loop.

### Current (static)

```python
def _generate(self, system_prompt, user_prompt, phase):
    messages = [SystemMessage(system_prompt), HumanMessage(user_prompt)]
    response = self._llm.invoke(messages)
    return DebateStatement(content=response.content)
```

### Future (agentic tool loop)

```python
async def _generate_agentic(self, system_prompt, user_prompt, phase):
    messages = [SystemMessage(system_prompt), HumanMessage(user_prompt)]
    tool_calls_remaining = self.tool_budget  # e.g., 5 calls max

    while tool_calls_remaining > 0:
        response = await self._llm.invoke_with_tools(
            messages, tools=self._get_available_tools()
        )

        if response.stop_reason == "end_turn":
            # Agent decided it has enough to respond
            return DebateStatement(content=response.content)

        # Process tool calls and feed results back
        for tool_call in response.tool_calls:
            result = await self._mcp_client.execute(tool_call)
            messages.append(AssistantMessage(response))
            messages.append(ToolResultMessage(tool_call.id, result))
            tool_calls_remaining -= 1

    # Force a final response if budget is exhausted
    return await self._force_response(messages, phase)
```

The key behavioral change: the agent itself decides what it needs to argue well,
rather than receiving a pre-assembled context window and making do.

---

## The Research Agent

Before the debate starts, a dedicated research agent runs a directed investigation
of the candidate stock. This serves two purposes:

1. **Ensures baseline coverage** — fundamentals, news, ratings, insider activity
   are always checked, even if participants don't independently fetch them.
2. **Reduces redundant tool calls** — results are cached and shared; participants
   don't re-fetch the same data.

The research agent is itself an agent loop. It receives a minimal trigger
(ticker, drop magnitude, date) and decides, step by step, what to look up. Its
reasoning might look like:

> "The drop is 12% on high volume. Let me check the news first to understand
> the trigger. It's an earnings miss. Let me pull the earnings estimates and the
> actual numbers. The miss is on margins. Let me check if margins have been
> trending down. Let me also check if any insiders sold before the drop. Let me
> find comparable earnings-driven drops in the sector."

The output is a `ResearchPackage` — a structured document that the debate
participants receive as their starting context, while still retaining the ability
to do targeted follow-ups.

```python
@dataclass
class ResearchPackage:
    ticker: str
    research_date: date

    # Structured findings
    price_action: dict            # OHLCV, volume vs. avg, context window
    fundamentals: dict            # Key financial ratios and trends
    news_summary: str             # Research agent's synthesis of news
    news_articles: List[dict]     # Raw articles for participant reference
    analyst_view: dict            # Consensus rating, price targets, changes
    insider_activity: List[dict]  # Recent Form 4 filings
    comparable_events: List[dict] # Historical precedents with outcomes
    macro_context: dict           # Market/sector conditions

    # Research metadata
    tool_calls_made: List[dict]   # Audit trail
    research_duration_seconds: float
    total_tokens_used: int

    def format_for_participant(self) -> str:
        """Formats the package as a rich prompt context block."""
        ...
```

---

## Key Design Decisions

### 1. Research-First vs. Fully Dynamic

**Research-first** (recommended for v1): A research agent builds a
`ResearchPackage` before the debate. Participants receive rich context and can
do targeted follow-ups but start from a shared foundation.

**Fully dynamic**: Each participant fetches independently with no pre-research.
More autonomous and potentially surfaces divergent evidence, but doubles tool
costs and makes the debate harder to audit.

**Recommendation**: Start with research-first. The research agent enforces
coverage of baseline signals (financials, insider activity, ratings) that
participants might skip in favor of confirming their stance. Evolve to allow
fuller participant autonomy once tooling is stable.

### 2. Shared vs. Private Research

Should both debate participants see the same `ResearchPackage`?

- **Shared** (simpler): Both start from the same facts; disagreement emerges
  from interpretation. Matches the debate format intent.
- **Private** (more realistic): Each participant can do independent research,
  potentially uncovering different evidence. More realistic to how human analysts
  work; a bull might find an insider-buy signal the bear didn't emphasize.

**Recommendation**: Shared package from the research agent, with each participant
free to use their tool budget for targeted follow-up. This gives a consistent
baseline while allowing divergence.

### 3. Tool Call Budgets

Unconstrained tool calling creates unpredictable latency and cost. Each agent
role should have an explicit budget:

| Agent | Suggested Budget | Rationale |
|-------|-----------------|-----------|
| Research agent | 10-15 calls | Broad coverage needed |
| Bull participant | 3-5 calls | Targeted follow-ups only |
| Bear participant | 3-5 calls | Targeted follow-ups only |
| Summary agent | 0-2 calls | Fact-checking disputed claims |

Budgets should be configurable in `debate.yaml`.

### 4. Caching MCP Results

The same underlying data (e.g., fundamentals for AAPL) should not be fetched
multiple times within a single pipeline run. A simple in-memory cache keyed by
`(tool_name, ticker, date)` is sufficient. This matters most when the research
agent and both participants might independently call `get_fundamentals`.

### 5. Evidence Grounding vs. Hallucination Risk

The current prompt README notes that v1 uses strict grounding (provided data
only). With agentic tooling, this constraint relaxes naturally: agents ground
their claims in tool call results. However, this introduces new risks:

- Agents may misinterpret tool outputs
- Tool outputs may themselves be inaccurate (API errors, stale data)
- Agents may selectively cite data that confirms their stance

Mitigations:
- Include raw tool outputs in the `ResearchPackage` for auditability
- Summary agent can call tools to verify disputed factual claims
- Log all tool calls and results for post-run review

### 6. Orchestrator Responsibility

The top-level `AgentOrchestrator` (to be implemented) should own:
- Starting and stopping the MCP server connections
- Running the research agent and collecting the `ResearchPackage`
- Passing the package to the `DebateOrchestrator`
- Enforcing total tool call budgets across all agents
- Handling failures (tool unavailable, MCP server down) gracefully
- Logging a full execution trace for auditability

---

## Phased Implementation Path

### Phase 1 — Tool Definitions (Current state)
`tools.py` defines the tool signatures. No execution. Agents still use static
context.

### Phase 2 — MCP Server Stubs
Implement lightweight MCP servers for each data category above. Wrap existing
data source clients (yfinance, news APIs) already in `src/ingestion/`. Verify
tool call / response format works end-to-end with the Claude API.

### Phase 3 — Research Agent
Implement `ResearchAgent` as an agentic loop that uses the MCP servers to build
a `ResearchPackage`. Run it before the debate. Replace `StockContext` as the
primary context object passed to participants.

### Phase 4 — Agentic Participants
Upgrade `Participant._generate()` to an async tool-use loop. Start with a small
budget (3 calls). Evaluate whether argument quality improves relative to cost.

### Phase 5 — Analyst Agent
Implement `analyst.py` as a fully agentic single-agent loop. The analyst
receives the `ResearchPackage` and `DebateResult` and produces an `AnalystReport`
with a `BUY / WATCH / AVOID` recommendation, using tool calls to fill gaps in its
reasoning.

---

## File Map

```
src/agent/
├── README.md                  ← This file
├── analyst.py                 ← (stub) Deep single-agent analyst
├── tools.py                   ← (stub) Tool definitions for agent use
│
├── debate/
│   ├── __init__.py
│   ├── orchestrator.py        ← Debate flow coordination
│   ├── participant.py         ← Bull/Bear LangChain participants
│   ├── models.py              ← StockContext, DebateResult, etc.
│   └── formatter.py           ← Markdown/JSON output formatting
│
└── prompts/
    ├── debate/
    │   ├── README.md          ← Prompting guide
    │   ├── opening_buy.txt
    │   ├── opening_avoid.txt
    │   ├── rebuttal.txt
    │   └── summary.txt
    ├── news_assessment.txt
    ├── company_analysis.txt
    └── recommendation.txt
```

Future additions:
```
src/agent/
├── orchestrator.py            ← Top-level AgentOrchestrator
├── research/
│   ├── agent.py               ← ResearchAgent loop
│   └── models.py              ← ResearchPackage dataclass
└── mcp/
    ├── market_data.py         ← MCP server: price/fundamentals
    ├── news_search.py         ← MCP server: targeted news queries
    ├── analyst_intel.py       ← MCP server: ratings/estimates
    ├── sec_filings.py         ← MCP server: EDGAR/Form4
    ├── comparable_events.py   ← MCP server: historical precedents
    └── macro_context.py       ← MCP server: VIX/sector/macro
```
