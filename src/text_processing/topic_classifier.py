# Topic Classifier
# ================
# Categorize news articles by topic/type.
#
# Categories help determine the nature of the drop:
# - Earnings-related news
# - Legal/regulatory news
# - Product/service news
# - Executive changes
# - Analyst opinions
# - General market news
#
# TODO: Implement the following:
#
# class NewsCategory(Enum):
#     """Categories of financial news."""
#     EARNINGS = "earnings"              # Earnings reports, guidance
#     LEGAL = "legal"                    # Lawsuits, SEC, investigations
#     PRODUCT = "product"                # Product launches, recalls, issues
#     EXECUTIVE = "executive"            # CEO/CFO changes, departures
#     ANALYST = "analyst"                # Upgrades, downgrades, price targets
#     MA = "m&a"                         # Mergers, acquisitions, divestitures
#     REGULATORY = "regulatory"          # FDA, FTC, regulatory actions
#     MACRO = "macro"                    # Interest rates, economic data
#     COMPETITOR = "competitor"          # Competitor news affecting company
#     OTHER = "other"
#
# @dataclass
# class TopicResult:
#     """Result of topic classification."""
#     # Fields:
#     # - category: NewsCategory
#     # - confidence: float
#     # - all_scores: Dict[NewsCategory, float]
#
# class TopicClassifier:
#     """Classify news articles by topic."""
#
#     def __init__(self, model_path: Optional[str] = None):
#         """
#         Initialize topic classifier.
#
#         Args:
#             model_path: Path to trained classifier, or None for rule-based
#
#         Options:
#         1. Rule-based (keyword matching) - simple, no training needed
#         2. Fine-tuned classifier - better accuracy, needs training data
#         3. Zero-shot classification - flexible, uses LLM
#         """
#         pass
#
#     def classify(self, text: str, title: str = None) -> TopicResult:
#         """
#         Classify a news article.
#
#         Title is optional but helps (often more indicative).
#         """
#         pass
#
#     def classify_rule_based(self, text: str) -> TopicResult:
#         """
#         Simple keyword-based classification.
#
#         Keywords per category:
#         - EARNINGS: "earnings", "EPS", "revenue", "guidance", "quarter"
#         - LEGAL: "lawsuit", "sued", "SEC", "investigation", "settlement"
#         - PRODUCT: "product", "launch", "recall", "defect", "FDA approval"
#         - EXECUTIVE: "CEO", "CFO", "appointed", "resigned", "departure"
#         - ANALYST: "upgrade", "downgrade", "price target", "rating"
#         - etc.
#         """
#         pass
#
#     def classify_zero_shot(self, text: str) -> TopicResult:
#         """
#         Use zero-shot classification with a language model.
#
#         More flexible but slower.
#         Uses: facebook/bart-large-mnli or similar
#         """
#         pass
