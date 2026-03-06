#!/usr/bin/env python3
"""
R&D Tax Credit Export Script

Queries GitHub issues and git commits to generate a CSV export for R&D tax credit claims.
Calculates actual hours worked based on commit timestamps and extracts time/cost estimates
from issue bodies.

Usage:
    python export-script.py --start-date 2024-01-01 --end-date 2024-12-31 --output exports/rd-claim-2024.csv
    python export-script.py --start-date 2024-01-01 --end-date 2024-12-31 \
        --output exports/rd-claim-2024.csv --repo unified-trading-deployment-v3
    python export-script.py --start-date 2024-01-01 --end-date 2024-12-31 --output exports/rd-claim-2024.csv --all-repos

Requirements:
    - gh CLI installed and authenticated
    - git repositories cloned locally
    - Python 3.8+
"""

import argparse
from pathlib import Path

from export_helpers import (
    DEFAULT_REPOS,
    export_to_csv,
    print_export_summary,
    process_repos_for_export,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export GitHub issues and commits for R&D tax credit claims")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--repo", help="Single repository to scan")
    parser.add_argument("--all-repos", action="store_true", help="Scan all repos in the workspace")
    parser.add_argument("--workspace-root", default=".", help="Path to workspace root")
    parser.add_argument("--github-org", default="IggyIkenna", help="GitHub organization/user")

    args = parser.parse_args()

    if args.all_repos:
        repos = DEFAULT_REPOS
    elif args.repo:
        repos = [args.repo]
    else:
        print("Error: Must specify either --repo or --all-repos")
        return 1

    workspace_root = Path(args.workspace_root).resolve()
    all_data = process_repos_for_export(repos, workspace_root, args.github_org, args.start_date, args.end_date)
    output_path = Path(args.output)
    export_to_csv(all_data, output_path)
    print_export_summary(all_data, output_path)
    return 0


if __name__ == "__main__":
    exit(main())
