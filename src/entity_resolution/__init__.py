# Entity Resolution Module
# ========================
# Maps company mentions in news to stock tickers.
#
# Pipeline:
# 1. NER: Extract organization entities from text
# 2. Ticker Matching: Fuzzy match entities to ticker database
# 3. Disambiguation: Use OpenFIGI or other sources to resolve ambiguity
#
# Challenges:
# - Company name variations (Apple vs Apple Inc. vs AAPL)
# - Subsidiaries vs parent companies
# - Name collisions (e.g., "Amazon" could be company or region)
# - Abbreviations and acronyms
