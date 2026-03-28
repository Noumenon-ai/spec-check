"""Tests for spec parser."""

from spec_check.parser import generate_keywords, parse_spec


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


def test_generate_keywords_file_variants():
    keywords = generate_keywords("dashboard")
    assert any(kw.endswith(".tsx") for kw in keywords)
