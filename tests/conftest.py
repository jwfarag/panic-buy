# Test Configuration
# ==================
# Shared fixtures and setup for pytest.

import sys
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require API keys)"
    )

# Mock eventregistry before any imports (it has build issues in some environments)
mock_eventregistry = MagicMock()
sys.modules['eventregistry'] = mock_eventregistry

# Provide the classes that newsapi_source.py imports
mock_eventregistry.EventRegistry = MagicMock
mock_eventregistry.QueryArticlesIter = MagicMock
mock_eventregistry.QueryItems = MagicMock
mock_eventregistry.ReturnInfo = MagicMock
mock_eventregistry.ArticleInfoFlags = MagicMock
