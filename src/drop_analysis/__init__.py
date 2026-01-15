# Drop Analysis Module
# ====================
# Core module for detecting, filtering, and classifying price drops.
#
# Pipeline:
# 1. Detector: Scan universe for price drops
# 2. Market Filter: Remove market-correlated drops
# 3. Classifier: Categorize drop type (earnings, news, etc.)
# 4. Severity: Bucket drops by magnitude
#
# This is the key module that separates panic-driven drops
# from fundamental-driven drops.
