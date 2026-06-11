"""Tests for spec parser."""

from spec_check.parser import generate_keywords, generate_search_terms, parse_spec


def test_parse_comma_separated():
    features = parse_spec("login page, signup page, dashboard")
    assert len(features) == 3
    assert "login page" in features


def test_parse_bullet_list():
    text = "- login page\n- signup page\n- dashboard"
    features = parse_spec(text)
    assert len(features) == 3


def test_parse_numbered_list():
    text = "1. login page\n2. signup page\n3. dashboard"
    features = parse_spec(text)
    assert len(features) == 3


def test_parse_with_colon_prefix():
    text = "Build a todo app with: login, signup, dashboard, tasks, settings"
    features = parse_spec(text)
    assert len(features) == 5


def test_parse_empty():
    features = parse_spec("")
    assert len(features) == 0


def test_generate_keywords():
    keywords = generate_keywords("login page")
    assert "login" in keywords
    assert "signin" in keywords or "auth" in keywords


def test_common_code_tokens_never_searched_alone():
    # "csv export" must not search for "export" — it appears in every
    # JS/TS module and produced false FOUND results.
    keywords = [k.lower() for k in generate_keywords("csv export")]
    assert "export" not in keywords
    assert "csv" in keywords

    keywords = [k.lower() for k in generate_keywords("user profile page")]
    assert "page" not in keywords
    assert "user" not in keywords
    assert "profile" in keywords


def test_multiword_features_require_phrase_match():
    terms = generate_search_terms("task creation form")
    # Lone words like "task" must not be searchable terms for a
    # multi-word feature.
    lowered = [t.lower() for t in terms.all_terms()]
    assert "task" not in lowered
    assert "creation" not in lowered
    assert "taskcreation" in lowered
    assert "task-creation" in lowered


def test_single_distinctive_token_features():
    terms = generate_search_terms("dashboard")
    assert terms.token_terms == ["dashboard"]
    assert terms.phrase_terms == []


def test_phrase_variants_include_identifier_cases():
    terms = generate_search_terms("task list")
    lowered = [t.lower() for t in terms.all_terms()]
    assert "tasklist" in lowered
    assert "task_list" in lowered
    assert "task-list" in lowered
