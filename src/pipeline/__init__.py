# Pipeline Module
# ===============
# Orchestration for the daily batch pipeline.
#
# Components:
# - Daily Run: Main pipeline orchestration
# - Scheduler: Cron-style run scheduling
#
# The pipeline coordinates all other modules to:
# 1. Ingest data
# 2. Detect and filter drops
# 3. Compute features
# 4. Run predictions
# 5. Analyze top candidates
# 6. Generate reports
