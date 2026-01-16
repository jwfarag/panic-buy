#!/usr/bin/env python3
"""
Test NewsAPI Direct
===================
Tests the newsapi.org API directly using the newsapi-python package.

This is separate from NewsAPI.ai (Event Registry) - they are different services!

Usage:
    python scripts/test_newsapi_direct.py

Requires:
    pip install newsapi-python
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


def test_newsapi_org():
    """Test newsapi.org (newsapi-python package)."""
    from newsapi import NewsApiClient

    print("=== Testing newsapi.org ===")
    print("(This is DIFFERENT from NewsAPI.ai/Event Registry)\n")

    # Try both possible env var names
    api_key = os.environ.get("NEWSAPI_KEY") or os.environ.get("NEWSAPI_AI_KEY")

    if not api_key:
        print("ERROR: No API key found.")
        print("Set NEWSAPI_KEY or NEWSAPI_AI_KEY in .env or environment.")
        return False

    api_key = api_key.strip()
    print(f"Using API key: {api_key[:4]}... (length: {len(api_key)})")

    # Check key format hints
    if len(api_key) == 32:
        print("Key length 32 suggests newsapi.org format")
    elif len(api_key) > 32:
        print("Key length > 32 suggests NewsAPI.ai (Event Registry) format")
        print("You may be using the wrong key for this service!")

    print("\nInitializing NewsApiClient...")
    client = NewsApiClient(api_key=api_key)

    print("Fetching top headlines for 'technology'...")
    try:
        response = client.get_top_headlines(
            category='technology',
            language='en',
            country='us',
            page_size=3
        )

        if response.get('status') == 'ok':
            articles = response.get('articles', [])
            print(f"SUCCESS! Found {len(articles)} articles\n")

            for i, article in enumerate(articles, 1):
                print(f"{i}. {article.get('title', 'No title')}")
                print(f"   Source: {article.get('source', {}).get('name', 'Unknown')}")
                print(f"   URL: {article.get('url', 'N/A')}\n")

            return True
        else:
            print(f"ERROR: API returned status '{response.get('status')}'")
            print(f"Message: {response.get('message', 'No message')}")
            return False

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False


def test_everything_search():
    """Test the /everything endpoint."""
    from newsapi import NewsApiClient

    print("\n=== Testing /everything endpoint ===\n")

    api_key = (os.environ.get("NEWSAPI_KEY") or os.environ.get("NEWSAPI_AI_KEY") or "").strip()
    if not api_key:
        print("Skipping - no API key")
        return False

    client = NewsApiClient(api_key=api_key)

    print("Searching for 'Apple stock'...")
    try:
        response = client.get_everything(
            q='Apple stock',
            language='en',
            sort_by='publishedAt',
            page_size=3
        )

        if response.get('status') == 'ok':
            total = response.get('totalResults', 0)
            articles = response.get('articles', [])
            print(f"SUCCESS! Found {total} total results, showing {len(articles)}\n")

            for i, article in enumerate(articles, 1):
                print(f"{i}. {article.get('title', 'No title')}")
                print(f"   Published: {article.get('publishedAt', 'Unknown')}\n")

            return True
        else:
            print(f"ERROR: {response.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False


def main():
    print("NewsAPI.org Direct Test")
    print("=" * 40)
    print()
    print("NOTE: newsapi.org and NewsAPI.ai are DIFFERENT services!")
    print("- newsapi.org: Uses 'newsapi-python' package, 32-char API keys")
    print("- NewsAPI.ai:  Uses 'eventregistry' package, longer API keys")
    print()

    success = test_newsapi_org()

    if success:
        test_everything_search()

    print("=" * 40)
    if success:
        print("Tests passed! Your key works with newsapi.org")
    else:
        print("Tests failed. Check your API key and service.")


if __name__ == "__main__":
    main()
