# News Ingestion Submodule
# ========================
# Fetches news articles using NewsAPI.ai (Event Registry).
#
# Provides full article text from thousands of sources including
# Reuters, Bloomberg, WSJ, and more.
#
# Requires NEWSAPI_AI_KEY environment variable.

from .base import NewsArticle, NewsSource
from .newsapi_source import NewsAPISource

__all__ = ['NewsArticle', 'NewsSource', 'NewsAPISource']
