"""Optional LLM-enhanced feature matching."""

from __future__ import annotations

import os

from rich.console import Console

console = Console()


def is_available() -> bool:
    """Check if an LLM API key is configured."""
    return bool(os.environ.get("OPENAI_API_KEY"))


def match_features_with_llm(
    spec: str,
    file_list: list[str],
    file_contents: dict[str, str] | None = None,
) -> dict[str, dict] | None:
    """Use an LLM to intelligently match spec features to project files.

    Returns None if LLM is not available. Otherwise returns a dict of
    {feature: {status, evidence, confidence}}.
    """
    if not is_available():
        return None

    try:
        from openai import OpenAI
    except ImportError:
        console.print("  [dim]openai not installed. pip install spec-check[llm][/]")
        return None

    try:
        client = OpenAI()
        prompt = f"""Analyze this spec and project file list. For each feature in the spec,
determine if it's FOUND, PARTIAL, or MISSING in the project.

SPEC:
{spec}

PROJECT FILES:
{chr(10).join(file_list[:100])}

Respond as JSON: {{"features": [{{"feature": "...", "status": "FOUND|PARTIAL|MISSING", "evidence": "filename", "confidence": 0.0-1.0}}]}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        import json
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        console.print(f"  [dim]LLM matching failed: {e}[/]")
        return None
