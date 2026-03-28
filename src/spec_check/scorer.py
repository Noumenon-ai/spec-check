"""Score features as FOUND, PARTIAL, or MISSING."""

from spec_check.scanner import ScanResult


def summarize(result: ScanResult) -> dict:
    """Generate a summary dict of the scan result."""
    return {
        "directory": result.directory,
        "files_scanned": result.files_scanned,
        "total_features": result.total_features,
        "found": result.found_count,
        "partial": result.partial_count,
        "missing": result.missing_count,
        "completeness": result.completeness,
        "features": [
            {
                "feature": f.feature,
                "status": f.status,
                "evidence": f.evidence,
                "matches": f.match_count,
            }
            for f in result.features
        ],
    }
