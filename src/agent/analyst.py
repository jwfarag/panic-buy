# LLM Analyst Agent
# =================
# Deep analysis of top drop candidates using LLM.
#
# The analyst reviews each candidate and provides:
# 1. Event summary
# 2. Overreaction assessment
# 3. Company strength analysis
# 4. Historical precedents
# 5. Risk factors
# 6. Final recommendation
#
# TODO: Implement the following:
#
# @dataclass
# class AnalystReport:
#     """LLM analyst report for a drop candidate."""
#     # Fields:
#     # - ticker: str
#     # - drop_date: date
#     # - event_summary: str
#     # - overreaction_assessment: str
#     # - company_analysis: str
#     # - historical_analogues: List[str]
#     # - risk_factors: List[str]
#     # - recommendation: str - "BUY", "WATCH", "AVOID"
#     # - confidence: str - "HIGH", "MEDIUM", "LOW"
#     # - reasoning: str
#     # - raw_response: str - Full LLM response
#
# class AnalystAgent:
#     """LLM-powered analyst for deep drop analysis."""
#
#     def __init__(self, config: dict):
#         """
#         Initialize analyst agent.
#
#         Args:
#             config: Configuration with:
#                 - provider: "anthropic" or "openai"
#                 - model: Model name (e.g., "claude-sonnet-4-20250514")
#                 - max_candidates: Max candidates to analyze per run
#         """
#         # TODO: Initialize LLM client
#         # TODO: Load prompt templates
#         pass
#
#     def analyze(
#         self,
#         candidate: "EnsemblePrediction",
#         news_articles: List["NewsArticle"],
#         company_info: dict,
#         market_context: dict
#     ) -> AnalystReport:
#         """
#         Perform deep analysis on a single candidate.
#
#         Args:
#             candidate: Model predictions for this drop
#             news_articles: Related news articles
#             company_info: Fundamental data about company
#             market_context: Current market conditions
#
#         Returns:
#             AnalystReport with detailed analysis
#         """
#         pass
#
#     def analyze_batch(
#         self,
#         candidates: List["EnsemblePrediction"],
#         news_data: Dict[str, List["NewsArticle"]],
#         company_data: Dict[str, dict]
#     ) -> List[AnalystReport]:
#         """
#         Analyze multiple candidates.
#
#         Runs in sequence (LLM calls are expensive).
#         Only analyzes top N candidates.
#         """
#         pass
#
#     def _build_prompt(
#         self,
#         candidate: "EnsemblePrediction",
#         news_articles: List["NewsArticle"],
#         company_info: dict
#     ) -> str:
#         """
#         Build analysis prompt from templates.
#
#         Combines:
#         - News assessment prompt
#         - Company analysis prompt
#         - Recommendation prompt
#         """
#         pass
#
#     def _parse_response(self, response: str) -> AnalystReport:
#         """Parse LLM response into structured report."""
#         pass
#
#     def _load_prompt_template(self, template_name: str) -> str:
#         """Load a prompt template from file."""
#         pass
#
#     def find_historical_analogues(
#         self,
#         ticker: str,
#         drop_type: str,
#         drop_magnitude: float
#     ) -> List[str]:
#         """
#         Find similar historical events for this company or peers.
#
#         Helps agent assess likely outcome based on precedent.
#         """
#         pass
