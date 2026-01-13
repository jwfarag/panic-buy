# Severity Scorer
# ===============
# Assess how "bad" or impactful news is likely to be.
#
# This goes beyond sentiment - negative sentiment about a minor
# issue is different from negative sentiment about an existential threat.
#
# Factors:
# - Magnitude of issue (material vs immaterial)
# - Duration of impact (one-time vs ongoing)
# - Controllability (internal vs external factor)
# - Precedent (has company recovered from similar before?)
#
# TODO: Implement the following:
#
# class SeverityLevel(Enum):
#     """Levels of news severity."""
#     LOW = "low"           # Minor issues, likely noise
#     MEDIUM = "medium"     # Notable but recoverable
#     HIGH = "high"         # Significant, needs analysis
#     CRITICAL = "critical" # Potentially existential
#
# @dataclass
# class SeverityResult:
#     """Result of severity scoring."""
#     # Fields:
#     # - level: SeverityLevel
#     # - score: float (0-1)
#     # - factors: List[str] - Contributing factors
#     # - reasoning: str - Explanation
#
# class SeverityScorer:
#     """Score the severity/impact of news."""
#
#     def __init__(self):
#         """Initialize severity scorer."""
#         # TODO: Load severity indicators
#         pass
#
#     def score(self, text: str, topic: str = None) -> SeverityResult:
#         """
#         Score severity of news text.
#
#         Combines multiple signals:
#         1. Keyword severity (lawsuit > criticism)
#         2. Magnitude indicators ($1B loss > $1M loss)
#         3. Temporal indicators (ongoing > one-time)
#         4. Source credibility
#         5. Topic-specific rules
#         """
#         pass
#
#     def _extract_magnitude_indicators(self, text: str) -> dict:
#         """
#         Extract magnitude-related information.
#
#         Look for:
#         - Dollar amounts
#         - Percentages
#         - Numbers of affected customers/products
#         - Geographic scope
#         """
#         pass
#
#     def _assess_duration(self, text: str) -> str:
#         """
#         Assess whether impact is one-time or ongoing.
#
#         Indicators:
#         - "one-time charge" -> one-time
#         - "ongoing investigation" -> ongoing
#         - "quarterly impact" -> temporary
#         - "structural change" -> permanent
#         """
#         pass
#
#     def _keyword_severity(self, text: str) -> float:
#         """
#         Score based on presence of severity keywords.
#
#         High severity: "fraud", "criminal", "bankruptcy", "death"
#         Medium severity: "lawsuit", "investigation", "recall"
#         Low severity: "disappointing", "missed expectations"
#         """
#         pass
#
#     def compare_to_fundamentals(
#         self,
#         severity: SeverityResult,
#         price_drop: float
#     ) -> float:
#         """
#         Compare news severity to price drop magnitude.
#
#         Returns mismatch score:
#         - High positive: Drop seems overdone relative to news
#         - Near zero: Drop proportional to news
#         - High negative: Drop seems mild relative to news
#
#         This is a key signal for panic detection.
#         """
#         pass
