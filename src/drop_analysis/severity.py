# Severity Bucketing
# ==================
# Categorize drops by severity/magnitude.
#
# Buckets are:
# - MINOR: 1-2% (monitor only)
# - MODERATE: 2-5% (analyze if stable)
# - MAJOR: 5-10% (priority analysis)
# - SEVERE: 10%+ (immediate deep dive)
#
# Thresholds are:
# - Configurable via YAML
# - Sector-specific (tech vs utilities)
# - Learnable based on historical recovery rates
#
# TODO: Implement the following:
#
# class SeverityBucket(Enum):
#     """Severity levels for price drops."""
#     MINOR = "minor"
#     MODERATE = "moderate"
#     MAJOR = "major"
#     SEVERE = "severe"
#
# @dataclass
# class SeverityConfig:
#     """Configuration for a severity bucket."""
#     # Fields:
#     # - min_drop: float
#     # - max_drop: float
#     # - action: str
#     # - description: str
#
# class SeverityClassifier:
#     """Classify drops by severity."""
#
#     def __init__(self, config_path: str):
#         """
#         Initialize severity classifier.
#
#         Args:
#             config_path: Path to drop_thresholds.yaml
#         """
#         # TODO: Load thresholds from config
#         # TODO: Load sector overrides
#         pass
#
#     def classify(
#         self,
#         drop_pct: float,
#         sector: str = None
#     ) -> SeverityBucket:
#         """
#         Classify a drop into a severity bucket.
#
#         Args:
#             drop_pct: Drop percentage (negative, e.g., -0.05 for 5%)
#             sector: Optional sector for sector-specific thresholds
#
#         Returns:
#             SeverityBucket
#         """
#         pass
#
#     def get_thresholds(self, sector: str = None) -> Dict[SeverityBucket, SeverityConfig]:
#         """
#         Get thresholds for a sector (or default).
#
#         Returns sector-specific thresholds if available,
#         otherwise returns default thresholds.
#         """
#         pass
#
#     def update_thresholds(
#         self,
#         new_thresholds: Dict[SeverityBucket, SeverityConfig],
#         sector: str = None
#     ) -> None:
#         """
#         Update thresholds (from learning or manual adjustment).
#
#         Args:
#             new_thresholds: New threshold configuration
#             sector: Optional sector to update (None = default)
#         """
#         pass
#
#     def suggest_threshold_adjustment(
#         self,
#         historical_recoveries: "pd.DataFrame"
#     ) -> Dict[SeverityBucket, SeverityConfig]:
#         """
#         Suggest threshold adjustments based on historical data.
#
#         Analysis:
#         - For each bucket, calculate recovery rate
#         - If MODERATE has higher recovery than MAJOR,
#           thresholds may need adjustment
#         - Suggest new boundaries that maximize signal quality
#
#         This is used by the threshold_learner in mlops.
#         """
#         pass
#
#     def get_action(self, bucket: SeverityBucket) -> str:
#         """Get recommended action for a severity bucket."""
#         pass
