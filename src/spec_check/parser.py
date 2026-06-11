"""Parse spec text into features and build search terms for each feature."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


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


# English filler words that say nothing about WHICH feature this is.
STOPWORDS = {
    "a", "an", "the", "and", "or", "with", "for", "of", "to", "in", "on",
    "by", "via", "from", "as", "at", "is", "are", "be", "it", "its",
    "support", "feature", "features", "functionality", "basic", "simple",
    "full", "new", "add", "create", "build", "make", "implement", "should",
    "must", "can", "will", "have", "has", "using", "use",
}

# Tokens that appear in virtually every codebase. Matching on these is how
# "csv export" used to be reported FOUND in any TypeScript project (every
# module contains the word "export"). Never search for these on their own.
COMMON_CODE_TOKENS = {
    "export", "import", "page", "pages", "form", "forms", "type", "types",
    "class", "classes", "function", "functions", "default", "return",
    "const", "let", "var", "async", "await", "public", "private", "static",
    "void", "string", "number", "bool", "boolean", "true", "false", "null",
    "none", "def", "self", "this", "new", "get", "set", "index", "main",
    "app", "src", "code", "component", "components", "module", "modules",
    "props", "state", "render", "style", "styles", "view", "views",
    "screen", "screens", "section", "button", "buttons", "field", "fields",
    "input", "output", "value", "values", "key", "keys", "name", "names",
    "file", "files", "data", "item", "items", "object", "objects", "user",
    "users", "info", "text", "label", "title", "content", "container",
    "wrapper", "handler", "util", "utils", "helper", "helpers", "manager",
    "service", "base", "common", "core", "system",
}

# Conservative synonym map. Only distinctive alternates: a synonym must be
# specific enough that finding it really is evidence of the feature.
SYNONYMS = {
    "login": ["signin", "sign-in", "sign_in", "auth", "authentication"],
    "signup": ["register", "registration", "sign-up", "sign_up", "create-account"],
    "sign up": ["register", "registration", "signup", "sign-up"],
    "logout": ["signout", "sign-out", "sign_out"],
    "dark mode": ["dark-mode", "darkmode", "dark_mode", "color-scheme", "prefers-color-scheme"],
    "dark theme": ["dark-mode", "darkmode", "dark_mode"],
    "responsive": ["breakpoint", "media-query", "@media"],
    "settings": ["preferences"],
    "profile": ["user-profile", "userprofile"],
    "notification": ["toast", "notify"],
    "database": ["schema", "migration", "postgres", "sqlite", "prisma"],
    "payment": ["stripe", "checkout", "billing"],
    "billing": ["stripe", "checkout", "invoice", "subscription"],
    "email": ["smtp", "mailer", "sendgrid", "nodemailer"],
    "password reset": ["forgot-password", "reset-password", "password-reset"],
    "search": ["typeahead", "autocomplete", "full-text"],
    "upload": ["multipart", "dropzone", "file-picker"],
}


@dataclass
class SearchTerms:
    """Search terms for one feature, split by how strong a signal they are.

    phrase_terms: multi-word phrase variants ("task creation", "taskcreation",
        "task-creation", "task_creation", "TaskCreation", "taskCreation").
        A multi-word feature must match one of these — matching a lone word
        like "task" is not evidence of "task creation form".
    token_terms: a distinctive single token, used only when the feature
        reduces to one distinctive word (e.g. "csv export" -> "csv").
    synonym_terms: distinctive alternates from the synonym map.
    """

    feature: str
    phrase_terms: list[str] = field(default_factory=list)
    token_terms: list[str] = field(default_factory=list)
    synonym_terms: list[str] = field(default_factory=list)

    def all_terms(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for term in self.phrase_terms + self.token_terms + self.synonym_terms:
            low = term.lower()
            if low and low not in seen:
                seen.add(low)
                out.append(term)
        return out


def _distinctive_words(feature_lower: str) -> list[str]:
    words = re.findall(r"[a-z0-9@:]+", feature_lower)
    return [
        w for w in words
        if len(w) >= 3 and w not in STOPWORDS and w not in COMMON_CODE_TOKENS
    ]


def _phrase_variants(words: list[str]) -> list[str]:
    """Compound variants of a word sequence as it would appear in code."""
    variants = [
        " ".join(words),
        "".join(words),
        "-".join(words),
        "_".join(words),
        "".join(w.capitalize() for w in words),                 # PascalCase
        words[0] + "".join(w.capitalize() for w in words[1:]),  # camelCase
    ]
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        if v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
    return out


def generate_search_terms(feature: str) -> SearchTerms:
    """Build weighted search terms for a feature.

    Rules:
    - Stopwords and common programming tokens (export, import, page, form,
      type, class, function, default, ...) are never searched on their own.
    - A feature with 2+ distinctive words requires a multi-word phrase match.
    - A feature with exactly 1 distinctive word searches that token.
    - A feature with 0 distinctive words falls back to its verbatim text.
    """
    feature_lower = feature.lower().strip()
    terms = SearchTerms(feature=feature)
    distinctive = _distinctive_words(feature_lower)

    if len(distinctive) >= 2:
        terms.phrase_terms = _phrase_variants(distinctive)
        if feature_lower not in [t.lower() for t in terms.phrase_terms]:
            terms.phrase_terms.insert(0, feature_lower)
    elif len(distinctive) == 1:
        terms.token_terms = [distinctive[0]]
    else:
        # Nothing distinctive: only the verbatim phrase counts as evidence.
        terms.phrase_terms = [feature_lower]

    # Distinctive synonyms (filtered through the same common-token guard).
    for key, syns in SYNONYMS.items():
        if key in feature_lower:
            for syn in syns:
                if syn not in COMMON_CODE_TOKENS and syn not in STOPWORDS:
                    terms.synonym_terms.append(syn)

    return terms


def generate_keywords(feature: str) -> list[str]:
    """Flat list of search terms for a feature (compatibility wrapper)."""
    return generate_search_terms(feature).all_terms()
