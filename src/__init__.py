# Panic Buy Detector
# ==================
# Main source package for the panic buy detection system.
#
# Module overview:
# - ingestion: News and market data fetching
# - entity_resolution: Map news mentions to stock tickers
# - text_processing: Sentiment analysis, topic classification
# - features: Feature engineering for ML models
# - drop_analysis: Detect, filter, and classify price drops
# - models: ML models for panic detection and recovery prediction
# - agent: LLM-based deep analysis
# - mlops: Model versioning, drift detection, rollback
# - reporting: Daily report generation
# - backtest: Historical backtesting framework
# - infrastructure: Local/cloud execution abstraction
# - pipeline: Daily run orchestration
# - execution: (PLACEHOLDER) Broker integration
# - alerts: (PLACEHOLDER) Notification system
