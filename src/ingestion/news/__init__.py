# News Ingestion Submodule
# ========================
# Fetches news articles from multiple sources.
#
# Available sources:
#   - MassiveNewsSource: Uses Polygon API for metadata + Trafilatura for content
#   - NewsAPISource: Uses NewsAPI.ai (Event Registry) for full articles
#
# Environment variables:
#   - POLYGON_API_KEY: Required for MassiveNewsSource
#   - NEWSAPI_AI_KEY: Required for NewsAPISource

from .base import NewsArticle, NewsSource
from .massive_source import MassiveNewsSource
from .newsapi_source import NewsAPISource

__all__ = ['NewsArticle', 'NewsSource', 'MassiveNewsSource', 'NewsAPISource']
