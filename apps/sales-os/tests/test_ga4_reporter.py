"""Unit tests for GA4 Reporter."""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest

ENGINE = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from ga4_reporter import (
    DEFAULT_PROPERTY_ID,
    fetch_overview,
    fetch_top_events,
    fetch_top_pages,
    format_markdown,
    generate_report,
    resolve_credentials_path,
)


def test_resolve_credentials_path():
    with patch("os.path.exists", return_value=True):
        path = resolve_credentials_path("/custom/path.json")
        assert path == "/custom/path.json"


def test_fetch_overview_parsing():
    mock_client = MagicMock()
    mock_client.properties().runReport().execute.return_value = {
        "metricHeaders": [{"name": "activeUsers"}, {"name": "screenPageViews"}],
        "rows": [{"metricValues": [{"value": "42"}, {"value": "100"}]}],
    }

    result = fetch_overview(mock_client, "123456", days=30)
    assert result == {"activeUsers": "42", "screenPageViews": "100"}


def test_fetch_top_pages_parsing():
    mock_client = MagicMock()
    mock_client.properties().runReport().execute.return_value = {
        "rows": [
            {
                "dimensionValues": [{"value": "/reparatur/"}],
                "metricValues": [{"value": "50"}, {"value": "20"}],
            }
        ]
    }

    pages = fetch_top_pages(mock_client, "123456", days=30)
    assert len(pages) == 1
    assert pages[0]["pagePath"] == "/reparatur/"
    assert pages[0]["screenPageViews"] == 50
    assert pages[0]["activeUsers"] == 20


def test_fetch_top_events_parsing():
    mock_client = MagicMock()
    mock_client.properties().runReport().execute.return_value = {
        "rows": [
            {
                "dimensionValues": [{"value": "page_view"}],
                "metricValues": [{"value": "120"}],
            }
        ]
    }

    events = fetch_top_events(mock_client, "123456", days=30)
    assert len(events) == 1
    assert events[0]["eventName"] == "page_view"
    assert events[0]["eventCount"] == 120


def test_format_markdown():
    data = {
        "property_id": "543244027",
        "days": 30,
        "overview": {
            "activeUsers": "45",
            "screenPageViews": "212",
            "sessions": "75",
            "eventCount": "803",
        },
        "top_pages": [
            {"pagePath": "/", "screenPageViews": 65, "activeUsers": 33}
        ],
        "top_events": [
            {"eventName": "page_view", "eventCount": 212}
        ],
    }
    md = format_markdown(data)
    assert "GA4 Analytics Report (Property: 543244027 | Last 30 Days)" in md
    assert "**Active Users:** 45" in md
    assert "| `/` | 65 | 33 |" in md
    assert "| `page_view` | 212 |" in md
