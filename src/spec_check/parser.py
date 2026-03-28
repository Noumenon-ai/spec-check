"""Parse spec text into a list of features."""

from __future__ import annotations

import re


def parse_spec(text: str) -> list[str]:
    """Parse a spec string into individual feature items.

    Handles:
    - Comma-separated: "login page, signup page, dashboard"
    - Bullet points: "- login page\\n- signup page"
    - Numbered lists: "1. login page\\n2. signup page"
    - Colon-separated headers: "Build a todo app with: login, signup, dashboard"
    """
    # If there's a colon, take everything after the last colon
    if ":" in text:
        parts = text.split(":")
        text = parts[-1].strip()

    features: list[str] = []

    # Check for bullet points or numbered lists
    lines = text.strip().splitlines()
    has_bullets = any(re.match(r"^\s*[-*]\s+", line) for line in lines)
    has_numbers = any(re.match(r"^\s*\d+[.)]\s+", line) for line in lines)

    if has_bullets or has_numbers:
        for line in lines:
            cleaned = re.sub(r"^\s*[-*]\s+", "", line)
            cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned)
            cleaned = cleaned.strip()
            if cleaned:
                features.append(cleaned)
    else:
        # Comma-separated
        for item in re.split(r",\s*", text):
            item = item.strip()
            if item:
                features.append(item)

    return features


def generate_keywords(feature: str) -> list[str]:
    """Generate search keywords for a feature.

    'login page' -> ['login', 'signin', 'sign-in', 'auth', 'Login', 'login.tsx', 'login.jsx', 'login.py']
    """
    keywords = []
    feature_lower = feature.lower().strip()

    # The feature itself and its words
    keywords.append(feature_lower)
    words = feature_lower.split()
    keywords.extend(words)

    # Synonym expansions
    synonyms = {
        "login": ["signin", "sign-in", "sign_in", "auth", "authenticate"],
        "signup": ["register", "sign-up", "sign_up", "registration", "create-account"],
        "sign up": ["register", "signup", "sign-up", "registration"],
        "dashboard": ["dash", "home", "overview", "main"],
        "dark mode": ["dark-mode", "darkmode", "dark_mode", "theme", "color-scheme"],
        "dark theme": ["dark-mode", "darkmode", "dark_mode", "theme"],
        "responsive": ["mobile", "breakpoint", "media-query", "@media", "sm:", "md:", "lg:"],
        "mobile responsive": ["responsive", "mobile", "breakpoint", "@media"],
        "search": ["search", "find", "query", "filter"],
        "settings": ["settings", "preferences", "config", "options"],
        "profile": ["profile", "account", "user-profile"],
        "notification": ["notification", "alert", "toast", "notify"],
        "api": ["api", "endpoint", "route", "handler"],
        "database": ["database", "db", "schema", "model", "migration"],
        "test": ["test", "spec", "__test__", ".test.", ".spec."],
        "payment": ["payment", "stripe", "checkout", "billing", "pay"],
        "email": ["email", "mail", "smtp", "sendgrid", "resend"],
    }

    for key, syns in synonyms.items():
        if key in feature_lower:
            keywords.extend(syns)

    # File name variants
    primary = words[0] if words else feature_lower
    for ext in [".tsx", ".jsx", ".vue", ".svelte", ".py", ".ts", ".js"]:
        keywords.append(primary + ext)

    # PascalCase and camelCase
    if len(words) > 1:
        pascal = "".join(w.capitalize() for w in words)
        camel = words[0] + "".join(w.capitalize() for w in words[1:])
        keywords.extend([pascal, camel])

    return list(set(keywords))
