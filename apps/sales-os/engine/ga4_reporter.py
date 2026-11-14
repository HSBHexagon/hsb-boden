"""GA4 Reporter for HSB Sales OS & Website Analytics.

Authenticates via Service Account (sa-agy-remote-mcp@hsb-boden.iam.gserviceaccount.com)
and queries the production GA4 Property (543244027).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_PROPERTY_ID = "543244027"
DEFAULT_KEY_PATH = r"C:\Users\Joel\AppData\Roaming\gcloud\hsb_sa_agy_remote_mcp.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def resolve_credentials_path(custom_path: Optional[str] = None) -> Optional[str]:
    """Resolve credentials JSON path (preferring dedicated HSB service account)."""
    if custom_path and os.path.exists(custom_path):
        return custom_path
    if os.path.exists(DEFAULT_KEY_PATH):
        return DEFAULT_KEY_PATH
    env_sa = os.getenv("HSB_GA4_KEY_PATH")
    if env_sa and os.path.exists(env_sa):
        return env_sa
    env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.exists(env_path):
        return env_path
    return None


def get_ga4_client(key_path: Optional[str] = None) -> Any:
    """Build and return an authorized Google Analytics Data API client."""
    import google.auth
    from googleapiclient.discovery import build

    resolved_key = resolve_credentials_path(key_path)
    if not resolved_key:
        raise FileNotFoundError(
            "Service account credentials not found. Provide --key or set GOOGLE_APPLICATION_CREDENTIALS."
        )

    creds, _ = google.auth.load_credentials_from_file(resolved_key, scopes=SCOPES)
    return build("analyticsdata", "v1beta", credentials=creds)


def fetch_overview(client: Any, property_id: str, days: int = 30) -> Dict[str, Any]:
    """Fetch high-level overview metrics."""
    res = client.properties().runReport(
        property=f"properties/{property_id}",
        body={
            "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
            "metrics": [
                {"name": "activeUsers"},
                {"name": "screenPageViews"},
                {"name": "sessions"},
                {"name": "eventCount"},
            ],
        },
    ).execute()

    headers = [h["name"] for h in res.get("metricHeaders", [])]
    values = res.get("rows", [{}])[0].get("metricValues", []) if res.get("rows") else []
    return {h: v.get("value", "0") for h, v in zip(headers, values)}


def fetch_top_pages(client: Any, property_id: str, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch top pages by screen views."""
    res = client.properties().runReport(
        property=f"properties/{property_id}",
        body={
            "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [
                {"name": "screenPageViews"},
                {"name": "activeUsers"},
            ],
            "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
            "limit": limit,
        },
    ).execute()

    results = []
    for row in res.get("rows", []):
        results.append({
            "pagePath": row["dimensionValues"][0]["value"],
            "screenPageViews": int(row["metricValues"][0]["value"]),
            "activeUsers": int(row["metricValues"][1]["value"]),
        })
    return results


def fetch_top_events(client: Any, property_id: str, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch top event counts."""
    res = client.properties().runReport(
        property=f"properties/{property_id}",
        body={
            "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
            "dimensions": [{"name": "eventName"}],
            "metrics": [{"name": "eventCount"}],
            "orderBys": [{"metric": {"metricName": "eventCount"}, "desc": True}],
            "limit": limit,
        },
    ).execute()

    results = []
    for row in res.get("rows", []):
        results.append({
            "eventName": row["dimensionValues"][0]["value"],
            "eventCount": int(row["metricValues"][0]["value"]),
        })
    return results


def generate_report(property_id: str, key_path: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """Compile full analytics report."""
    client = get_ga4_client(key_path)
    return {
        "property_id": property_id,
        "days": days,
        "overview": fetch_overview(client, property_id, days),
        "top_pages": fetch_top_pages(client, property_id, days),
        "top_events": fetch_top_events(client, property_id, days),
    }


def format_markdown(data: Dict[str, Any]) -> str:
    """Format report dict as a markdown table."""
    ov = data["overview"]
    lines = [
        f"# GA4 Analytics Report (Property: {data['property_id']} | Last {data['days']} Days)",
        "",
        "### Key Metrics",
        f"- **Active Users:** {ov.get('activeUsers', '0')}",
        f"- **Sessions:** {ov.get('sessions', '0')}",
        f"- **Pageviews:** {ov.get('screenPageViews', '0')}",
        f"- **Event Count:** {ov.get('eventCount', '0')}",
        "",
        "### Top Pages",
        "| Page Path | Pageviews | Active Users |",
        "| :--- | :--- | :--- |",
    ]
    for p in data["top_pages"]:
        lines.append(f"| `{p['pagePath']}` | {p['screenPageViews']} | {p['activeUsers']} |")

    lines.extend([
        "",
        "### Top Events",
        "| Event Name | Count |",
        "| :--- | :--- |",
    ])
    for e in data["top_events"]:
        lines.append(f"| `{e['eventName']}` | {e['eventCount']} |")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query GA4 Production Data for HSB Boden")
    parser.add_argument("--property-id", default=os.getenv("HSB_GA4_PROPERTY_ID", DEFAULT_PROPERTY_ID))
    parser.add_argument("--key", default=None)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--json", action="store_true", help="Output JSON instead of Markdown")

    args = parser.parse_args()
    report = generate_report(args.property_id, args.key, args.days)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_markdown(report))


if __name__ == "__main__":
    main()
