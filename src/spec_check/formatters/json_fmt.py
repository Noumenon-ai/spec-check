"""JSON output formatter for CI/CD pipelines."""

import json
from datetime import datetime, timezone

from spec_check.scorer import summarize
from spec_check.scanner import ScanResult


def format_json(result: ScanResult) -> str:
    """Format scan result as JSON string."""
    data = summarize(result)
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(data, indent=2)
