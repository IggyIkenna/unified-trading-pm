#!/usr/bin/env python3
"""
Find tracked files that match .gitignore in each workspace repo and remove them from the index.
Run from workspace root: python3 unified-trading-pm/scripts/untrack-ignored-files.py
Use --dry-run to only report, no git rm.
"""

import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent


def get_repos():
    repos = []
    for d in WORKSPACE_ROOT.iterdir():
        if d.is_dir() and (d / ".git").exists():
            name = d.name
            if name.startswith(".") or name in (".venv-workspace", ".mypy_cache"):
                continue
            repos.append(d)
    return sorted(repos, key=lambda x: x.name)


def run(cmd: list[str], cwd: Path, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
    )


def tracked_ignored_files(repo: Path) -> list[str]:
    """Return list of tracked file paths that are ignored by .gitignore."""
    # -i = ignored, -c = cached (in index); --exclude-standard = use standard excludes
    r = run(["git", "ls-files", "-i", "-c", "--exclude-standard"], cwd=repo)
    if r.returncode != 0:
        return []
    return [p.strip() for p in r.stdout.splitlines() if p.strip()]


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    repos = get_repos()
    total_removed = 0
    for repo in repos:
        name = repo.name
        ignored = tracked_ignored_files(repo)
        if not ignored:
            continue
        if dry_run:
            print(f"{name}/: would untrack {len(ignored)} file(s)")
            for p in ignored:
                print(f"  {p}")
            total_removed += len(ignored)
            continue
        for path in ignored:
            r = run(["git", "rm", "--cached", "--", path], cwd=repo)
            if r.returncode == 0:
                print(f"{name}/: untracked {path}")
                total_removed += 1
            else:
                print(f"{name}/: failed to untrack {path}: {r.stderr or r.stdout}", file=sys.stderr)
    if total_removed:
        print(f"Total: {'would untrack' if dry_run else 'untracked'} {total_removed} file(s).")
    else:
        print("No tracked files matched .gitignore in any repo.")


if __name__ == "__main__":
    main()
