"""Search project files for feature evidence."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from spec_check.parser import generate_keywords


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
        keywords = generate_keywords(feature)
        evidence, match_count = _search_for_feature(keywords, project_files, file_contents)

        if match_count >= 2:
            status = "FOUND"
        elif match_count == 1:
            status = "PARTIAL"
        else:
            status = "MISSING"

        results.append(FeatureResult(
            feature=feature,
            status=status,
            evidence=evidence[:3],  # Top 3 evidence items
            match_count=match_count,
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


def _search_for_feature(
    keywords: list[str],
    files: list[Path],
    contents: dict[Path, str],
) -> tuple[list[str], int]:
    """Search for a feature using keywords. Returns (evidence_list, total_match_count)."""
    evidence: list[str] = []
    total_matches = 0

    for filepath in files:
        filename_lower = filepath.name.lower()
        rel_path = str(filepath)

        # Check filename matches
        for kw in keywords:
            if kw.lower() in filename_lower:
                evidence.append(rel_path)
                total_matches += 1
                break

        # Check file content matches
        content = contents.get(filepath, "")
        if content:
            content_lower = content.lower()
            for kw in keywords:
                if kw.lower() in content_lower:
                    total_matches += 1
                    if rel_path not in evidence:
                        evidence.append(rel_path)
                    break

    return evidence, total_matches
