#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Data availability validation checker.

Reads workspace-manifest.json for all repos with service_declaration.capabilities_needed
containing "data_source". For each such repo, checks:
1. Whether VCR cassettes or test fixtures exist in the repo's tests/ directory.
2. Whether the repo has mock data providers or fixture files.
3. Which venues are referenced in the repo's source code.

Reports: repo, cassette_status, fixture_status, venue_count.

Exit codes:
  0 -- all checks pass (or --warning-only)
  1 -- at least one data-source repo has zero cassettes and zero fixtures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PM_ROOT = WORKSPACE_ROOT / "unified-trading-pm"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

# Known VCR cassette file extensions
_CASSETTE_EXTENSIONS = frozenset({".yaml", ".yml", ".json"})
_CASSETTE_DIR_NAMES = frozenset({"cassettes", "vcr_cassettes", "recordings", "fixtures"})
_FIXTURE_DIR_NAMES = frozenset({"fixtures", "test_data", "mock_data", "sample_data"})

# Directories to skip when scanning
_SKIP_DIRS = frozenset(
    {
        ".venv",
        ".venv-workspace",
        "node_modules",
        "__pycache__",
        ".git",
        "build",
        "dist",
        ".egg-info",
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
    }
)


def _should_skip(path: Path) -> bool:
    """Return True if path is inside a skip directory."""
    return any(part in _SKIP_DIRS or part.endswith(".egg-info") for part in path.parts)


def _count_cassettes(repo_path: Path) -> int:
    """Count VCR cassette files in the repo's test directories."""
    count = 0
    tests_dir = repo_path / "tests"
    if not tests_dir.exists():
        return 0

    for cassette_dir_name in _CASSETTE_DIR_NAMES:
        for match in tests_dir.rglob(cassette_dir_name):
            if not match.is_dir() or _should_skip(match):
                continue
            for f in match.iterdir():
                if f.is_file() and f.suffix in _CASSETTE_EXTENSIONS:
                    count += 1
    return count


def _count_fixtures(repo_path: Path) -> int:
    """Count fixture/mock data files in the repo's test directories."""
    count = 0
    tests_dir = repo_path / "tests"
    if not tests_dir.exists():
        return 0

    for fixture_dir_name in _FIXTURE_DIR_NAMES:
        for match in tests_dir.rglob(fixture_dir_name):
            if not match.is_dir() or _should_skip(match):
                continue
            for f in match.iterdir():
                if f.is_file() and not f.name.startswith("."):
                    count += 1
    return count


def _find_venues(repo_path: Path) -> list[str]:
    """Scan Python source files for venue references.

    Looks for common venue identifiers in the source (not tests).
    """
    known_venues = [
        "binance",
        "bybit",
        "okx",
        "deribit",
        "coinbase",
        "aave",
        "hyperliquid",
        "polymarket",
        "kalshi",
        "betfair",
        "bet365",
        "pinnacle",
        "smarkets",
        "matchbook",
        "ibkr",
        "bloomberg",
        "refinitiv",
    ]

    found: set[str] = set()

    # Scan Python source files only (not tests, not venvs)
    for py_file in repo_path.rglob("*.py"):
        if _should_skip(py_file):
            continue
        # Skip test files
        if "tests" in py_file.parts or "test_" in py_file.name:
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace").lower()
            for venue in known_venues:
                if venue in content:
                    found.add(venue)
        except OSError:
            continue

    return sorted(found)


def _get_data_source_repos(manifest: dict[str, object]) -> list[str]:
    """Extract repo names that have data_source in capabilities_needed."""
    repos: list[str] = []
    repositories = manifest.get("repositories", {})  # noqa: qg-empty-fallback
    if not isinstance(repositories, dict):
        return repos

    for repo_name, repo_cfg in repositories.items():
        if not isinstance(repo_cfg, dict):
            continue
        service_decl = repo_cfg.get("service_declaration", {})  # noqa: qg-empty-fallback
        if not isinstance(service_decl, dict):
            continue
        capabilities = service_decl.get("capabilities_needed", [])  # noqa: qg-empty-fallback
        if not isinstance(capabilities, list):
            continue
        if "data_source" in capabilities:
            repos.append(repo_name)

    return sorted(repos)


def main(argv: list[str] | None = None) -> int:
    """Run the data availability checker."""
    parser = argparse.ArgumentParser(
        description="Validate data availability (cassettes, fixtures, venues) for data-source repos.",
    )
    parser.add_argument(
        "--warning-only",
        action="store_true",
        default=False,
        help="Always exit 0, even if repos lack cassettes/fixtures",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Override workspace root directory",
    )
    args = parser.parse_args(argv)

    ws_root = Path(args.workspace_root).resolve() if args.workspace_root else WORKSPACE_ROOT
    manifest_path = ws_root / "unified-trading-pm" / "workspace-manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: workspace-manifest.json not found at {manifest_path}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_source_repos = _get_data_source_repos(manifest)

    if not data_source_repos:
        print("WARNING: No repos with data_source capability found in manifest")
        return 0

    results: list[dict[str, object]] = []
    repos_without_data: list[str] = []

    for repo_name in data_source_repos:
        repo_path = ws_root / repo_name
        repo_exists = repo_path.is_dir()

        cassette_count = _count_cassettes(repo_path) if repo_exists else 0
        fixture_count = _count_fixtures(repo_path) if repo_exists else 0
        venues = _find_venues(repo_path) if repo_exists else []

        has_data = cassette_count > 0 or fixture_count > 0
        if not has_data and repo_exists:
            repos_without_data.append(repo_name)

        results.append(
            {
                "repo": repo_name,
                "repo_exists": repo_exists,
                "cassette_count": cassette_count,
                "fixture_count": fixture_count,
                "venue_count": len(venues),
                "venues": venues,
                "cassette_status": "OK" if cassette_count > 0 else "MISSING",
                "fixture_status": "OK" if fixture_count > 0 else "MISSING",
            }
        )

    # Output
    if args.format == "json":
        output: dict[str, object] = {
            "total_repos": len(results),
            "repos_without_data": repos_without_data,
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 80)
        print(f"Data Availability Report — {len(results)} data-source repos")
        print("=" * 80)
        print(f"  {'Repo':<45s} {'Cassettes':>9s} {'Fixtures':>9s} {'Venues':>7s}  Status")
        print("-" * 80)
        for r in results:
            repo = str(r["repo"])
            cassettes = int(r.get("cassette_count", 0))
            fixtures = int(r.get("fixture_count", 0))
            venue_count = int(r.get("venue_count", 0))
            exists = bool(r.get("repo_exists", False))

            if not exists:
                status = "NOT_FOUND"
            elif cassettes > 0 or fixtures > 0:
                status = "OK"
            else:
                status = "NO_DATA"

            print(f"  {repo:<45s} {cassettes:>9d} {fixtures:>9d} {venue_count:>7d}  {status}")

            venues_list = r.get("venues", [])  # noqa: qg-empty-fallback
            if isinstance(venues_list, list) and venues_list:
                print(f"    venues: {', '.join(str(v) for v in venues_list)}")

        print("=" * 80)

        if repos_without_data:
            print(f"\nWARNING: {len(repos_without_data)} repos have no cassettes or fixtures:")
            for repo_name in repos_without_data:
                print(f"  - {repo_name}")

        total_ok = sum(1 for r in results if r.get("cassette_count", 0) or r.get("fixture_count", 0))
        print(f"\nSummary: {total_ok}/{len(results)} repos have test data")

    if args.warning_only:
        return 0

    return 1 if repos_without_data else 0


if __name__ == "__main__":
    sys.exit(main())
