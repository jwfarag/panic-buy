# Panic Buy Detector

A system for detecting reactionary, panic-driven price drops in stable stocks and identifying potential buying opportunities.

## Overview

This system monitors stable companies for sudden price drops caused by isolated news events (not market-wide corrections), classifies whether the drop is likely panic/overreaction vs. fundamental deterioration, and generates daily reports ranking the best opportunities.

## Key Capabilities

- **News Ingestion**: Scrapes Yahoo Finance, Google News, and Seeking Alpha for relevant news
- **Market Data**: Historical and daily OHLCV data from Yahoo Finance
- **Entity Resolution**: Maps company mentions in news to stock tickers
- **Text Processing**: Sentiment analysis, topic classification, severity scoring
- **Drop Analysis**: Detects drops, filters out market-correlated moves, classifies drop types
- **Panic Detection**: ML model to distinguish panic selling from fundamental issues
- **AI Agent**: LLM-powered deep analysis of top candidates
- **MLOps**: Model versioning, drift detection, threshold learning, rollback capability
- **Reporting**: Daily HTML/PDF reports with ranked opportunities

## Design Philosophy

### Isolated Event Detection (Not Crisis Detection)

This system focuses on **isolated, company-specific events** that cause temporary price drops in otherwise stable companies. It explicitly filters out:

- Market-wide corrections (COVID crash, 2008, etc.)
- Sector rotations
- Macro-driven moves

The goal is to find overreactions to news that doesn't fundamentally change the company's value.

### Batch Processing Model

The system runs **1-2 times daily** (configurable), not in real-time. This design choice:

- Reduces infrastructure complexity
- Allows for more thorough analysis
- Fits the investment thesis (buying panic dips, not day trading)

### Configurable & Learnable Thresholds

Drop severity buckets are:
- Configurable via YAML
- Learnable based on historical recovery rates
- Sector-specific (tech vs utilities have different volatility norms)

---

## Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BATCH INGESTION (1-2x daily)                     │
│       ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│       │  Yahoo   │      │  Google  │      │ Seeking  │              │
│       │  News    │      │  News    │      │  Alpha   │              │
│       └────┬─────┘      └────┬─────┘      └────┬─────┘              │
│            └─────────────────┼─────────────────┘                    │
│                              ▼                                      │
│                     ┌──────────────┐                                │
│                     │Yahoo Finance │                                │
│                     │ Market Data  │                                │
│                     └──────────────┘                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DROP ANALYSIS MODULE                          │
│                                                                     │
│  1. DROP DETECTOR                                                   │
│     • Scan universe for price drops in last 24-48h                  │
│     • Flag stocks with significant negative moves                   │
│                                                                     │
│  2. MARKET FILTER                                                   │
│     • Calculate beta-adjusted return                                │
│     • Compare to SPY/QQQ movement                                   │
│     • Compare to sector ETF movement                                │
│     • Filter out: drops correlated with market/sector               │
│     • Keep: idiosyncratic drops (stock-specific)                    │
│                                                                     │
│  3. DROP CLASSIFIER                                                 │
│     • EARNINGS_MISS - Post-earnings drop                            │
│     • NEWS_REACTION - Isolated news event                           │
│     • ANALYST_DOWNGRADE - Rating change                             │
│     • SECTOR_ROTATION - Capital flow shift                          │
│     • UNKNOWN - Needs investigation                                 │
│                                                                     │
│  4. SEVERITY BUCKETING (Configurable + Learnable)                   │
│     • MINOR: 1-2% drop                                              │
│     • MODERATE: 2-5% drop                                           │
│     • MAJOR: 5-10% drop                                             │
│     • SEVERE: 10%+ drop                                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROCESSING & FEATURES                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │Entity Resol. │  │  Sentiment   │  │  Technical   │               │
│  │   (NER)      │──▶│  Analysis    │──▶│  Features    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 PREDICTION LAYER (Batch Mode)                       │
│                                                                     │
│  PANIC VS FUNDAMENTAL CLASSIFIER                                    │
│  • Input: Filtered idiosyncratic drops + features                   │
│  • Output: Probability this is panic/overreaction                   │
│  • Key signals: sentiment-magnitude mismatch, volume patterns       │
│                                                                     │
│  RECOVERY PREDICTOR                                                 │
│  • Expected recovery % (30-day horizon)                             │
│  • Confidence interval                                              │
│  • Estimated time to recovery                                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                                  │
│                                                                     │
│  LLM ANALYST (Top N candidates)                                     │
│  1. Summarize triggering event                                      │
│  2. Assess: Overreaction or legitimate concern?                     │
│  3. Company strength analysis (moat, balance sheet)                 │
│  4. Historical analogues (similar past events)                      │
│  5. Risk factors and counter-arguments                              │
│  6. Confidence-weighted recommendation                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      REPORTING MODULE                               │
│                                                                     │
│  DAILY REPORT                                                       │
│  1. Executive Summary (# drops, # filtered, # opportunities)        │
│  2. Top Opportunities (ranked by panic_prob * expected_recovery)    │
│  3. Watchlist (lower confidence candidates)                         │
│  4. Model Performance (accuracy, threshold performance)             │
│                                                                     │
│  Output: HTML, PDF, JSON                                            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MLOPS LAYER                                  │
│                                                                     │
│  • Model Registry (MLflow)                                          │
│  • Drift Detection (Evidently)                                      │
│  • Threshold Learning (auto-adjust severity buckets)                │
│  • Rollback Manager (revert to previous models if drift detected)   │
└─────────────────────────────────────────────────────────────────────┘
```

### Market Filter Logic

The key insight is separating stock-specific drops from market-driven moves:

```
Idiosyncratic Return = Actual Return - (Beta × Market Return)

Example:
- Stock dropped 5%
- Market (SPY) dropped 4%
- Stock beta = 1.2
- Expected drop = 4% × 1.2 = 4.8%
- Idiosyncratic = -5% - (-4.8%) = -0.2%
- Result: NOT a stock-specific issue, filter out
```

### Daily Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                 DAILY RUN (configurable)                │
├─────────────────────────────────────────────────────────┤
│  1. INGEST     - Pull news and market data              │
│  2. DETECT     - Find drops, filter market correlation  │
│  3. CLASSIFY   - Categorize drop type and severity      │
│  4. PROCESS    - NER, sentiment, features               │
│  5. PREDICT    - Score panic probability, recovery      │
│  6. RANK       - Sort by opportunity score              │
│  7. ANALYZE    - LLM deep-dive on top candidates        │
│  8. REPORT     - Generate daily report                  │
│  9. MLOPS      - Log predictions, check drift           │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
panic-buy/
├── config/
│   ├── settings.yaml           # Main configuration (API keys, schedule, etc.)
│   ├── tickers.yaml            # Universe of stable companies to monitor
│   └── drop_thresholds.yaml    # Configurable severity buckets
├── src/
│   ├── ingestion/
│   │   ├── news/               # News source scrapers
│   │   │   ├── base.py         # Abstract news source interface
│   │   │   ├── yahoo_news.py
│   │   │   ├── google_news.py
│   │   │   └── seeking_alpha.py
│   │   └── market/
│   │       ├── base.py         # Abstract market data interface
│   │       └── yahoo_market.py
│   ├── entity_resolution/
│   │   ├── ner.py              # Named entity recognition
│   │   ├── ticker_matcher.py   # Fuzzy match to ticker database
│   │   └── openfigi.py         # FIGI lookup for disambiguation
│   ├── text_processing/
│   │   ├── preprocessor.py     # Text cleaning and normalization
│   │   ├── sentiment.py        # Sentiment analysis (FinBERT)
│   │   ├── topic_classifier.py # News topic categorization
│   │   └── severity_scorer.py  # News severity assessment
│   ├── features/
│   │   ├── technical.py        # Price/volume features
│   │   ├── fundamental.py      # Company stability metrics
│   │   ├── sentiment_agg.py    # Aggregated sentiment signals
│   │   └── store.py            # Feature store interface
│   ├── drop_analysis/
│   │   ├── detector.py         # Detect price drops
│   │   ├── market_filter.py    # Filter market-correlated drops
│   │   ├── classifier.py       # Classify drop type
│   │   └── severity.py         # Severity bucketing with learning
│   ├── models/
│   │   ├── panic_detector.py   # Panic vs fundamental classifier
│   │   ├── recovery_predictor.py
│   │   └── ensemble.py         # Model combination
│   ├── agent/
│   │   ├── analyst.py          # LLM-based analysis
│   │   ├── prompts/            # Prompt templates
│   │   │   ├── news_assessment.txt
│   │   │   ├── company_analysis.txt
│   │   │   └── recommendation.txt
│   │   └── tools.py            # Agent tool definitions
│   ├── mlops/
│   │   ├── registry.py         # Model versioning
│   │   ├── drift_detector.py   # Performance monitoring
│   │   ├── retrainer.py        # Scheduled retraining
│   │   ├── rollback.py         # Version rollback logic
│   │   └── threshold_learner.py
│   ├── reporting/
│   │   ├── generator.py        # Report generation
│   │   ├── templates/          # Report templates
│   │   │   └── daily_report.html
│   │   ├── ranker.py           # Opportunity ranking
│   │   └── exporter.py         # PDF/HTML/JSON export
│   ├── backtest/
│   │   ├── engine.py           # Backtesting framework
│   │   ├── metrics.py          # Performance metrics
│   │   └── scenarios.py        # Historical scenarios
│   ├── infrastructure/
│   │   ├── executor.py         # Local/cloud task routing
│   │   ├── storage.py          # Storage abstraction
│   │   └── compute.py          # Compute abstraction
│   ├── pipeline/
│   │   ├── daily_run.py        # Main batch orchestration
│   │   └── scheduler.py        # Cron-style scheduling
│   ├── execution/              # PLACEHOLDER for broker integration
│   │   └── __init__.py
│   └── alerts/                 # PLACEHOLDER for notifications
│       └── __init__.py
├── data/
│   ├── raw/                    # Raw ingested data
│   ├── processed/              # Cleaned/transformed data
│   ├── features/               # Computed features
│   ├── labels/                 # Labeled historical events
│   └── reports/                # Generated reports
├── models/                     # Serialized model artifacts
├── notebooks/
│   ├── eda.ipynb
│   ├── labeling.ipynb
│   ├── threshold_analysis.ipynb
│   └── model_experiments.ipynb
├── docs/
│   └── TODO.md                 # Infrastructure TODOs
├── tests/
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

---

## Configuration

### Run Schedule (config/settings.yaml)

```yaml
schedule:
  runs:
    - name: morning_run
      time: "06:00"
      timezone: "America/New_York"
      enabled: true
    - name: evening_run
      time: "18:00"
      timezone: "America/New_York"
      enabled: true
  market_hours_only: true
  holiday_calendar: "NYSE"
```

### Drop Thresholds (config/drop_thresholds.yaml)

```yaml
severity_buckets:
  MINOR:    { min_drop: 0.01, max_drop: 0.02 }
  MODERATE: { min_drop: 0.02, max_drop: 0.05 }
  MAJOR:    { min_drop: 0.05, max_drop: 0.10 }
  SEVERE:   { min_drop: 0.10, max_drop: 1.00 }

sector_overrides:
  XLK:  # Tech - more volatile
    MODERATE: { min_drop: 0.03, max_drop: 0.07 }
  XLU:  # Utilities - less volatile
    MODERATE: { min_drop: 0.015, max_drop: 0.03 }

threshold_learning:
  enabled: true
  lookback_days: 180
  target_metric: recovery_rate_30d
```

### Environment (config/settings.yaml)

```yaml
environment:
  mode: "local"  # "local", "cloud", or "hybrid"
  local:
    data_dir: "./data"
    models_dir: "./models"
    max_workers: 4
  cloud:
    provider: "aws"
    data_bucket: "panic-buy-data"
    models_bucket: "panic-buy-models"
```

---

## Tech Stack

| Layer           | Technology                |
|-----------------|---------------------------|
| Orchestration   | Prefect or Airflow        |
| Market DB       | TimescaleDB or SQLite     |
| Document Store  | Elasticsearch or SQLite   |
| ML Framework    | PyTorch + HuggingFace     |
| Model Registry  | MLflow                    |
| Drift Detection | Evidently AI              |
| Agent Framework | Claude API or LangChain   |
| API             | FastAPI                   |
| Monitoring      | Prometheus + Grafana      |

---

## Critical Success Factors

1. **Labeled training data** - Curated dataset of historical panic events with outcomes
2. **False positive management** - Precision matters more than recall (buying real declines is costly)
3. **Universe filtering** - Define "stable" companies rigorously (market cap, beta, earnings consistency)
4. **Market filtering accuracy** - Must reliably separate stock-specific from market-wide moves

---

## Future Work

See [docs/TODO.md](docs/TODO.md) for infrastructure TODOs including:

- Hybrid local/cloud execution
- Storage abstraction layer
- Training offload to cloud
- Cost controls for cloud usage

---

## License

TBD
