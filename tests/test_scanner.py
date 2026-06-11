"""Tests for the project scanner."""

from pathlib import Path

from spec_check.scanner import scan_project

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT = FIXTURES / "sample_project"


def test_scan_finds_existing_features():
    features = ["login page", "signup page", "dashboard", "task list", "task creation form"]
    result = scan_project(str(SAMPLE_PROJECT), features)
    assert result.total_features == 5
    assert result.found_count >= 3  # login, signup, dashboard should be found
    assert result.missing_count >= 1  # task creation form should be missing


def test_scan_reports_completeness():
    features = ["login page", "signup page", "dashboard", "task list", "task creation form"]
    result = scan_project(str(SAMPLE_PROJECT), features)
    assert 40 <= result.completeness <= 100  # At least 3/5 found = 60%


def test_scan_empty_directory(tmp_path):
    features = ["login", "signup"]
    result = scan_project(str(tmp_path), features)
    assert result.missing_count == 2
    assert result.completeness == 0.0


def test_scan_nonexistent_directory():
    result = scan_project("/nonexistent/path", ["feature1"])
    assert result.missing_count == 1


def test_no_false_positives_on_absent_features():
    # None of these exist in the fixture project. The old substring
    # matcher reported 40% of them FOUND (e.g. "csv export" matched the
    # word "export" in every .tsx file). All five must be MISSING.
    features = [
        "user profile page",
        "admin panel",
        "password reset",
        "csv export",
        "stripe billing",
    ]
    result = scan_project(str(SAMPLE_PROJECT), features)
    assert result.missing_count == 5
    assert result.found_count == 0
    assert result.partial_count == 0
    assert result.completeness == 0.0


def test_task_creation_form_not_matched_by_lone_task_word():
    # "task" appears in TaskList.tsx and dashboard.tsx, but that is not
    # evidence of a task creation form.
    result = scan_project(str(SAMPLE_PROJECT), ["task creation form"])
    assert result.features[0].status == "MISSING"


def test_existing_features_still_found_with_evidence():
    result = scan_project(str(SAMPLE_PROJECT), ["login page", "task list"])
    by_feature = {f.feature: f for f in result.features}
    assert by_feature["login page"].status == "FOUND"
    assert any("login" in e.lower() for e in by_feature["login page"].evidence)
    assert by_feature["task list"].status == "FOUND"
    assert any("tasklist" in e.lower() for e in by_feature["task list"].evidence)
