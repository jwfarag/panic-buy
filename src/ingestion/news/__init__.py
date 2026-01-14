# News Ingestion Submodule
# ========================
# Scrapers for news sources.
#
# Supported sources:
# - Yahoo Finance news
# - Google News RSS
# - Seeking Alpha articles
#
# Each scraper implements the base NewsSource interface
# to ensure consistent data format across sources.

from .base import NewsArticle, NewsSource
from .yahoo_news import YahooNewsSource

__all__ = ['NewsArticle', 'NewsSource', 'YahooNewsSource']
