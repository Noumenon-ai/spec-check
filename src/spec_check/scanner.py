"""Search project files for feature evidence.

Matching model (heuristic, not semantic):
- Each feature gets search terms from parser.generate_search_terms().
  Multi-word features must match a compound phrase variant; common
  programming tokens (export, import, page, form, ...) are never searched.
- Matches are weighted: a hit in a filename or inside an identifier
  (LoginPage, task_list, TaskList) scores 2; a plain word in text scores 1.
- Feature score = sum of per-file scores. >=3 FOUND, 1-2 PARTIAL, 0 MISSING.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from spec_check.parser import SearchTerms, generate_search_terms


@dataclass
class FeatureResult:
    feature: str
    status: str  # FOUND, PARTIAL, MISSING
    evidence: list[str]
    match_count: int


@dataclass
class ScanResult:
    features: list[FeatureResult]
    total_features: int
    files_scanned: int
    directory: str

    @property
    def found_count(self) -> int:
        return sum(1 for f in self.features if f.status == "FOUND")

    @property
    def partial_count(self) -> int:
        return sum(1 for f in self.features if f.status == "PARTIAL")

    @property
    def missing_count(self) -> int:
        return sum(1 for f in self.features if f.status == "MISSING")

    @property
    def completeness(self) -> float:
        if not self.total_features:
            return 0.0
        score = self.found_count + (self.partial_count * 0.5)
        return round((score / self.total_features) * 100, 1)


SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".cache",
}

SCAN_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".vue", ".svelte",
    ".html", ".css", ".scss", ".json", ".yaml", ".yml",
    ".md", ".toml", ".cfg", ".rb", ".go", ".rs",
}

# Feature score thresholds.
FOUND_THRESHOLD = 3
PARTIAL_THRESHOLD = 1


def scan_project(directory: str, features: list[str]) -> ScanResult:
    """Scan a project directory for feature evidence."""
    dir_path = Path(directory).resolve()
    if not dir_path.is_dir():
        return ScanResult(
            features=[FeatureResult(f, "MISSING", [], 0) for f in features],
            total_features=len(features),
            files_scanned=0,
            directory=str(dir_path),
        )

    # Collect all project files
    project_files = _collect_files(dir_path)
    file_contents = _read_files(project_files)

    # Check each feature
    results = []
    for feature in features:
        terms = generate_search_terms(feature)
        evidence, score = _search_for_feature(terms, project_files, file_contents, dir_path)

        if score >= FOUND_THRESHOLD:
            status = "FOUND"
        elif score >= PARTIAL_THRESHOLD:
            status = "PARTIAL"
        else:
            status = "MISSING"

        results.append(FeatureResult(
            feature=feature,
            status=status,
            evidence=evidence[:3],  # Top 3 evidence items
            match_count=score,
        ))

    return ScanResult(
        features=results,
        total_features=len(features),
        files_scanned=len(project_files),
        directory=str(dir_path),
    )


def _collect_files(directory: Path) -> list[Path]:
    """Collect all scannable files in a directory."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in filenames:
            filepath = Path(root) / name
            if filepath.suffix.lower() in SCAN_EXTENSIONS:
                files.append(filepath)
    return files


def _read_files(files: list[Path]) -> dict[Path, str]:
    """Read file contents, skipping binary/large files."""
    contents = {}
    for f in files:
        try:
            if f.stat().st_size > 500_000:  # Skip files > 500KB
                continue
            contents[f] = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    return contents


def _term_weight_in_content(term: str, content: str) -> int:
    """Best match weight for a term in file content: 0, 1, or 2.

    A match must sit on a word boundary (camelCase boundaries count), so
    'auth' does not match 'author'. Matches embedded in identifiers
    (LoginPage, task_list) or written in identifier case (TaskList)
    weigh 2; plain words in prose or strings weigh 1.
    """
    best = 0
    try:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
    except re.error:
        return 0

    for m in pattern.finditer(content):
        start, end = m.start(), m.end()
        prev = content[start - 1] if start > 0 else ""
        nxt = content[end] if end < len(content) else ""
        actual = m.group(0)

        left_ok = (not prev.isalnum()) or (prev.islower() and actual[:1].isupper())
        right_ok = (not nxt.isalnum()) or nxt.isupper()
        if not (left_ok and right_ok):
            continue  # substring of an unrelated word

        inside_identifier = prev.isalnum() or prev == "_" or nxt.isalnum() or nxt == "_"
        identifier_case = actual not in (actual.lower(), actual.capitalize(), actual.upper())
        weight = 2 if (inside_identifier or identifier_case) else 1
        if weight > best:
            best = weight
        if best == 2:
            break

    return best


def _search_for_feature(
    terms: SearchTerms,
    files: list[Path],
    contents: dict[Path, str],
    base_dir: Path,
) -> tuple[list[str], int]:
    """Search for a feature. Returns (evidence_list, total_score)."""
    search_terms = terms.all_terms()
    scored_evidence: list[tuple[int, str]] = []
    total_score = 0

    for filepath in files:
        filename_lower = filepath.name.lower()
        file_score = 0

        # Filename match (strong signal): compound terms only, no spaces.
        for term in search_terms:
            tl = term.lower()
            if " " not in tl and tl in filename_lower:
                file_score += 2
                break

        # Content match: best single weight across terms (no stacking).
        content = contents.get(filepath, "")
        if content:
            content_best = 0
            for term in search_terms:
                w = _term_weight_in_content(term, content)
                if w > content_best:
                    content_best = w
                if content_best == 2:
                    break
            file_score += content_best

        if file_score > 0:
            try:
                rel = str(filepath.relative_to(base_dir))
            except ValueError:
                rel = str(filepath)
            scored_evidence.append((file_score, rel))
            total_score += file_score

    scored_evidence.sort(key=lambda pair: -pair[0])
    return [path for _, path in scored_evidence], total_score
