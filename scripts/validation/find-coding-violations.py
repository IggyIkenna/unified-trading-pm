#!/usr/bin/env python3
"""
Find all coding standards violations across unified-trading repos.

Usage:
    python scripts/find_coding_violations.py                    # Scan all repos
    python scripts/find_coding_violations.py --repo instruments # Scan one repo
    python scripts/find_coding_violations.py --check imports   # One check only
    python scripts/find_coding_violations.py --folder /path    # Custom folder
    python scripts/find_coding_violations.py --report          # Full report (no truncation)
    python scripts/find_coding_violations.py -o report.md      # Write report to file

Checks:
    - print() statements in production code
    - os.getenv() in production code
    - Indented imports (imports inside functions)
    - Naive datetimes (datetime.now() without timezone)
    - Bare except clauses
"""

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any

# Workspace root (parent of unified-trading-codex)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

# Default repos to scan
DEFAULT_REPOS = [
    "instruments-service",
    "market-tick-data-service",
    "unified-trading-deployment-v3",
    "features-calendar-service",
    "features-delta-one-service",
    "features-onchain-service",
    "features-volatility-service",
    "execution-service",
    "ml-inference-service",
    "ml-training-service",
    "strategy-service",
    "unified-trading-services",
]

# Exclusion patterns for all checks (dirs end with /, files use glob)
EXCLUDE_PATTERNS = [
    "tests/",
    "testing/",
    "scripts/",
    "examples/",
    ".venv/",
    "venv/",
    "__pycache__/",
    "site-packages/",
    "node_modules/",
    ".git/",
]
EXCLUDE_FILES = ["pytest_*.py", "conftest.py"]


class ViolationChecker:
    """Base class for violation checkers."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.repo_name = repo_path.name

    def get_exclude_globs(self) -> list[str]:
        """Return glob patterns for ripgrep --glob (exclude dirs and test files)."""
        # Directories: !**/name/**
        dirs = [f"!**/{p.rstrip('/')}/**" for p in EXCLUDE_PATTERNS if p.endswith("/")]
        # Files: !**/pattern
        files = [f"!**/{f}" for f in EXCLUDE_FILES]
        return dirs + files

    def should_exclude_line(self, content: str) -> bool:
        """Return True if this line should be excluded (false positive)."""
        return False

    def run_ripgrep(self, pattern: str, additional_args: list[str] = None) -> list[tuple[str, int, str]]:
        """Run ripgrep and return (filepath, line_num, content) tuples."""
        cmd = ["rg", pattern, "--type", "py", "-n"]

        # Add exclude globs
        for glob in self.get_exclude_globs():
            cmd.extend(["--glob", glob])

        # Add additional args
        if additional_args:
            cmd.extend(additional_args)

        cmd.append(str(self.repo_path))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return []
        except FileNotFoundError:
            print("⚠️  ripgrep (rg) not found. Install: brew install ripgrep")
            return []

        hits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            # rg output: path:line_num:content
            parts = line.split(":", 2)
            if len(parts) >= 3:
                filepath, ln, content = parts[0], int(parts[1]), parts[2]
                if not self.should_exclude_line(content):
                    hits.append((filepath, ln, content.strip()))

        return hits

    def check(self) -> dict[str, Any]:
        """Run check and return results."""
        raise NotImplementedError


class PrintChecker(ViolationChecker):
    """Find print() statements in production code."""

    def should_exclude_line(self, content: str) -> bool:
        """Exclude console.print, doctest, string literals."""
        stripped = content.strip()
        if "console.print(" in stripped or ".print(" in stripped:
            return True
        if stripped.startswith(">>>") or ">>> print(" in stripped:
            return True
        if stripped.startswith('"') or stripped.startswith("'"):
            return True
        if "python3 -c" in stripped or "python -c" in stripped:
            return True
        return False

    def check(self) -> dict[str, Any]:
        hits = self.run_ripgrep(r"print\(")
        return {
            "name": "print() statements",
            "count": len(hits),
            "hits": hits,
        }


class OsGetenvChecker(ViolationChecker):
    """Find os.getenv() in production code."""

    def check(self) -> dict[str, Any]:
        hits = self.run_ripgrep(r"os\.getenv")
        return {
            "name": "os.getenv() usage",
            "count": len(hits),
            "hits": hits,
        }


class IndentedImportChecker(ViolationChecker):
    """Find imports inside functions/classes."""

    def should_exclude_line(self, content: str) -> bool:
        """Exclude TYPE_CHECKING blocks, comments, docstring examples, optional deps."""
        stripped = content.strip()
        # Exclude imports in TYPE_CHECKING blocks (these are correct)
        if "TYPE_CHECKING" in content:
            return True
        # Exclude commented imports
        if stripped.startswith("#"):
            return True
        # Exclude doctest / docstring examples (>>> or ...)
        if stripped.startswith(">>>") or stripped.startswith("..."):
            return True
        # Exclude docstring usage examples (e.g. "    from X import Y" in Usage: block)
        if "get_schema_for_output_type" in stripped and "from " in stripped:
            return True
        # Exclude optional/conditional deps (try/except, lazy loading)
        optional_patterns = (
            "from dotenv import",
            "from rich.",
            "from scipy ",
            "import uvloop",
            "import gcsfs",
            "from web3 import",
            "from binance.",
            "from playwright",
            "from optuna",
            "import optuna",
            "from quantstats",
            "import quantstats",
            "from matplotlib",
            "import matplotlib",
            "from seaborn",
            "import seaborn",
            "import playwright",
            "from strategy_roe_analysis import",
            "import databento",
            "from databento",
            "import boto3",
            "from botocore.",
            "import polars",
            "import watchtower",
            "from execution_service.",
            "from market_data_tick_handler.",
            "from instruments_service.",
            "from features_calendar_service.",
            "import importlib",
            "import importlib.",
            "from nautilus_trader.",
            "from unified_trading_services.observability",
            "import unified_trading_services.core",
            "from unified_trading_services import clients",
            "from unified_trading_services.core.config import",
            "from unified_trading_services.core.gcsfuse_helper import",
            "from unified_trading_services.core.signal_handler import",
            "from unified_trading_services import get_storage_client",
            "from unified_trading_services import setup_cloud_logging",
            "from unified_trading_services.core.performance_monitor import",
            "from unified_trading_services.core.provider import",
            "from my_service.",
            # deployment-v3: route-specific imports for API isolation
            "from api.",
            "from deployment.",
            "from deployment import",
            "from backends.",
            "from backends import",
            "from unified_trading_deployment.",
            "from google.cloud",
            "from google.auth",
            "from github import",
            "import redis",
            # deployment-v3: stdlib and relative imports in route handlers
            "from .",
            "import time",
            "import json",
            "import re",
            "import os",
            "import yaml",
            "import secrets",
            "import subprocess",
            "import traceback",
            "import fnmatch",
            "import copy",
            "import logging",
            "import requests",
            "import tomllib",
            "import urllib",
            "import concurrent.futures",
            "import shlex",
            "from datetime import",
            "from concurrent.futures import",
            "from collections import",
            "from pathlib import Path",
            "from itertools import",
            "from unified_trading_services import",
            "from google.oauth2 import",
            "from src.cloud_client import",
            "import pyarrow",
        )
        # Exclude try-block imports (4 spaces) for optional unified_trading_services
        if content.startswith("    from unified_trading_services") or content.startswith(
            "    from unified_trading_services."
        ):
            return True
        for pat in optional_patterns:
            if pat in stripped:
                return True
        return False

    def check(self) -> dict[str, Any]:
        # Match indented import or from...import (excludes module-level)
        hits = self.run_ripgrep(r"^[[:space:]]+import |^[[:space:]]+from .* import")
        return {
            "name": "Indented imports",
            "count": len(hits),
            "hits": hits,
        }


class NaiveDatetimeChecker(ViolationChecker):
    """Find naive datetime usage."""

    def should_exclude_line(self, content: str) -> bool:
        """Exclude comments explaining the issue."""
        stripped = content.strip()
        if stripped.startswith("#"):
            return True
        # Exclude if it's in a comment about NOT using datetime.now()
        if "NOT datetime.now()" in content:
            return True
        return False

    def check(self) -> dict[str, Any]:
        patterns = [
            (r"datetime\.now\(\)", "datetime.now()"),
            (r"datetime\.utcnow\(\)", "datetime.utcnow()"),
        ]

        all_hits = []
        for pattern, label in patterns:
            hits = self.run_ripgrep(pattern)
            all_hits.extend(hits)

        return {
            "name": "Naive datetime usage",
            "count": len(all_hits),
            "hits": all_hits,
        }


class BareExceptChecker(ViolationChecker):
    """Find bare except: clauses."""

    def should_exclude_line(self, content: str) -> bool:
        """Exclude except: that's in comments or has a type."""
        stripped = content.strip()
        if stripped.startswith("#"):
            return True
        # Has exception type (except (ConnectionError, TimeoutError, OSError, ValueError):, except ValueError:)
        if re.match(r"except\s+\w+", stripped):
            return True
        return False

    def check(self) -> dict[str, Any]:
        hits = self.run_ripgrep(r"except:")
        return {
            "name": "Bare except clauses",
            "count": len(hits),
            "hits": hits,
        }


class HardcodedPathChecker(ViolationChecker):
    """Find hardcoded path literals."""

    def should_exclude_line(self, content: str) -> bool:
        """Exclude common false positives."""
        stripped = content.strip()
        # Exclude comments
        if stripped.startswith("#"):
            return True
        # Exclude imports (from x.y.z import)
        if "import" in stripped and ("from " in stripped or stripped.startswith("import")):
            return True
        # Exclude URLs (http://, https://)
        if "http://" in stripped or "https://" in stripped:
            return True
        # Exclude API endpoint paths (/v1/, /v2/, /api/, dict values like "key": "/path")
        if '"/v' in stripped or '"/api' in stripped or "'/v" in stripped or "'/api" in stripped:
            return True
        if '": "/' in stripped or "': '/" in stripped:  # API path in dict
            return True
        if "{" in stripped and '"/' in stripped:  # Path with param e.g. "/path/{id}"
            return True
        return False

    def check(self) -> dict[str, Any]:
        # Find absolute paths like "/path/to/file"
        hits = self.run_ripgrep(r'"/[^"]+/[^"]+"')
        return {
            "name": "Hardcoded paths",
            "count": len(hits),
            "hits": hits[:50],  # Limit to first 50 (can be many)
        }


# Registry of all checkers
ALL_CHECKERS = {
    "print": PrintChecker,
    "getenv": OsGetenvChecker,
    "imports": IndentedImportChecker,
    "datetime": NaiveDatetimeChecker,
    "except": BareExceptChecker,
    "paths": HardcodedPathChecker,
}


def scan_single_repo(repo_path: Path, check_names: list[str] = None) -> dict[str, Any]:
    """Scan a single repo for violations."""
    if check_names is None:
        check_names = list(ALL_CHECKERS.keys())

    results = {}
    for check_name in check_names:
        if check_name not in ALL_CHECKERS:
            print(f"⚠️  Unknown check: {check_name}")
            continue

        checker_cls = ALL_CHECKERS[check_name]
        checker = checker_cls(repo_path)
        results[check_name] = checker.check()

    return results


def print_results(
    repo_name: str,
    repo_path: Path,
    results: dict[str, Any],
    verbose: bool = False,
    full_report: bool = False,
):
    """Print scan results for a repo."""
    total_violations = sum(r["count"] for r in results.values())

    if total_violations == 0:
        print(f"✅ {repo_name}: CLEAN")
        return

    print(f"\n{'=' * 70}")
    print(f"📁 {repo_name}: {total_violations} violations")
    print(f"{'=' * 70}")

    for check_name, result in results.items():
        count = result["count"]
        if count == 0:
            print(f"  ✅ {result['name']}: CLEAN")
            continue

        print(f"  ❌ {result['name']}: {count} found")

        if (verbose or full_report) and result["hits"]:
            # Group by file (relative to repo root)
            by_file: dict[str, list[tuple[int, str]]] = {}
            for filepath, ln, content in result["hits"]:
                try:
                    rel = Path(filepath).relative_to(repo_path)
                except ValueError:
                    rel = Path(filepath)
                rel_str = str(rel)
                if rel_str not in by_file:
                    by_file[rel_str] = []
                by_file[rel_str].append((ln, content))

            max_files = None if full_report else 5
            max_entries = None if full_report else 3
            files_shown = sorted(by_file.keys())[:max_files] if max_files else sorted(by_file.keys())

            for filepath in files_shown:
                entries = by_file[filepath]
                print(f"      {filepath}")
                entries_shown = entries[:max_entries] if max_entries else entries
                for ln, content in entries_shown:
                    preview = content[:80] + "..." if len(content) > 80 else content
                    print(f"        L{ln}: {preview}")
                if max_entries and len(entries) > max_entries:
                    print(f"        ... and {len(entries) - max_entries} more")

            if max_files and len(by_file) > max_files:
                print(f"      ... and {len(by_file) - max_files} more files")
        print()


def main():
    parser = argparse.ArgumentParser(description="Find coding standards violations across repos")
    parser.add_argument(
        "--repo",
        help="Scan specific repo only (e.g., instruments-service)",
        default=None,
    )
    parser.add_argument(
        "--folder",
        help="Scan custom folder instead of default repos",
        default=None,
    )
    parser.add_argument(
        "--check",
        help="Run specific check only (print, getenv, imports, datetime, except, paths)",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Show detailed violations with file paths and line numbers",
        action="store_true",
    )
    parser.add_argument(
        "--report",
        help="Full report: show ALL violations (no truncation)",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write full report to file (implies --report)",
        metavar="FILE",
        default=None,
    )

    args = parser.parse_args()

    # Determine repos to scan
    repos_to_scan = []

    if args.folder:
        # Custom folder
        folder_path = Path(args.folder).resolve()
        if not folder_path.exists():
            print(f"❌ Folder not found: {args.folder}")
            return 1
        repos_to_scan = [(folder_path.name, folder_path)]

    elif args.repo:
        # Single repo
        repo_path = WORKSPACE_ROOT / args.repo
        if not repo_path.exists():
            print(f"❌ Repo not found: {args.repo}")
            print(f"   Looking in: {repo_path}")
            return 1
        repos_to_scan = [(args.repo, repo_path)]

    else:
        # All default repos
        for repo in DEFAULT_REPOS:
            repo_path = WORKSPACE_ROOT / repo
            if repo_path.exists():
                repos_to_scan.append((repo, repo_path))

    # Determine checks to run
    check_names = [args.check] if args.check else list(ALL_CHECKERS.keys())

    # Header
    print("=" * 70)
    print("CODING STANDARDS VIOLATION SCANNER")
    print("=" * 70)
    print(f"Scanning: {len(repos_to_scan)} repos")
    print(f"Checks: {', '.join(check_names)}")
    print(f"Excludes: {', '.join(EXCLUDE_PATTERNS)}")
    print("=" * 70)

    full_report = args.report or bool(args.output)

    # Scan all repos
    all_results = {}
    for repo_name, repo_path in repos_to_scan:
        results = scan_single_repo(repo_path, check_names)
        all_results[repo_name] = results
        print_results(
            repo_name,
            repo_path,
            results,
            verbose=args.verbose,
            full_report=full_report,
        )

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY BY CHECK")
    print("=" * 70)

    summary_by_check = {}
    for repo_name, results in all_results.items():
        for check_name, result in results.items():
            if check_name not in summary_by_check:
                summary_by_check[check_name] = {"total": 0, "repos": []}
            count = result["count"]
            summary_by_check[check_name]["total"] += count
            if count > 0:
                summary_by_check[check_name]["repos"].append(f"{repo_name} ({count})")

    for check_name in check_names:
        if check_name not in summary_by_check:
            continue
        data = summary_by_check[check_name]
        check_label = ALL_CHECKERS[check_name](Path(".")).check()["name"]

        if data["total"] == 0:
            print(f"✅ {check_label}: CLEAN across all repos")
        else:
            print(f"❌ {check_label}: {data['total']} violations across {len(data['repos'])} repos")
            for repo_info in data["repos"][:10]:  # First 10 repos
                print(f"   - {repo_info}")
            if len(data["repos"]) > 10:
                print(f"   ... and {len(data['repos']) - 10} more repos")

    print("=" * 70)

    # Write to file if requested
    if args.output:
        with open(args.output, "w") as f:
            f.write("# Coding Standards Violations Report\n\n")
            f.write("Generated by find_coding_violations.py\n")
            f.write(f"Repos scanned: {len(repos_to_scan)}\n")
            f.write(f"Checks: {', '.join(check_names)}\n\n")
            for repo_name, repo_path in repos_to_scan:
                results = all_results.get(repo_name, {})
                total = sum(r["count"] for r in results.values())
                f.write(f"\n## {repo_name} ({total} violations)\n\n")
                for check_name, result in results.items():
                    if result["count"] == 0:
                        continue
                    f.write(f"### {result['name']} ({result['count']})\n\n")
                    by_file = {}
                    for filepath, ln, content in result["hits"]:
                        try:
                            rel = str(Path(filepath).relative_to(repo_path))
                        except ValueError:
                            rel = filepath
                        if rel not in by_file:
                            by_file[rel] = []
                        by_file[rel].append((ln, content))
                    for fp in sorted(by_file.keys()):
                        f.write(f"- **{fp}**\n")
                        for ln, content in by_file[fp]:
                            f.write(f"  - L{ln}: {content[:100]}\n")
                    f.write("\n")
        print(f"\n📄 Full report written to: {args.output}")

    return 0


if __name__ == "__main__":
    exit(main())
