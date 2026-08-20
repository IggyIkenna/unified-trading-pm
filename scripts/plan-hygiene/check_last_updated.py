#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never
"""Check and synchronise plan frontmatter ``last_updated`` dates.

``last_updated`` is a maintenance signal, but it is not automatically updated by
git when a plan body changes.  That made the field stale across the live plans
corpus and forced repeated manual date bumps during reconciliation.  Git's latest
commit date is the mechanical source of truth used here.

The default mode is read-only and exits non-zero when a live document's date is
older than its latest commit.  ``--apply`` updates only the field value, retaining
its quoting and any trailing provenance comment.  Archives are intentionally out
of scope: they are closed records.

Usage:
    python3 scripts/plan-hygiene/check_last_updated.py [--quiet]
    python3 scripts/plan-hygiene/check_last_updated.py --apply
    python3 scripts/plan-hygiene/check_last_updated.py --only <path> [<path> ...]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs"))
import docspec

PM_DIR = Path(__file__).resolve().parents[2]
DOC_GLOBS = ("plans/active/*.md", "plans/active/issues/*.md", "plans/epics/*.md")
LIVE_STATUSES = frozenset({"active", "blocked", "paused", "open"})
LAST_UPDATED_RE = re.compile(
    r"^(last_updated:\s*)(?P<quote>[\"']?)(?P<value>\d{4}-\d{2}-\d{2})(?P=quote)(?P<tail>.*)$",
    re.MULTILINE,
)


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    docs: list[Path] = []
    for pattern in DOC_GLOBS:
        for path in PM_DIR.glob(pattern):
            if path.is_file() and path not in seen:
                seen.add(path)
                docs.append(path)
    return sorted(docs)


def _git_dates(paths: list[Path]) -> dict[str, date]:
    """Return each path newest commit date with one bounded git invocation."""
    relative_paths = [path.relative_to(PM_DIR).as_posix() for path in paths]
    pathspecs = ("plans/active", "plans/epics") if len(paths) > 100 else tuple(relative_paths)
    result = subprocess.run(
        ["git", "log", "--format=COMMIT %cs", "--name-only", "--max-count=10000", "--", *pathspecs],
        cwd=PM_DIR,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        return {}
    dates: dict[str, date] = {}
    commit_date: date | None = None
    wanted = set(relative_paths)
    for line in result.stdout.splitlines():
        if line.startswith("COMMIT "):
            try:
                commit_date = date.fromisoformat(line.removeprefix("COMMIT ").strip())
            except ValueError:
                commit_date = None
        elif commit_date is not None and line in wanted and line not in dates:
            dates[line] = commit_date
    return dates


def _frontmatter(path: Path) -> tuple[dict[str, object], str] | None:
    try:
        parsed, body = docspec.parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    if parsed is None:
        return None
    return parsed, body


def _stale_date(path: Path, committed: date | None) -> tuple[date, date] | None:
    parsed = _frontmatter(path)
    if parsed is None:
        return None
    frontmatter, _body = parsed
    if frontmatter.get("status") not in LIVE_STATUSES:
        return None
    raw = frontmatter.get("last_updated")
    if isinstance(raw, date):
        recorded = raw
    elif isinstance(raw, str):
        try:
            recorded = date.fromisoformat(raw.strip()[:10])
        except ValueError:
            return None
    else:
        return None
    if committed is None or committed <= recorded:
        return None
    return recorded, committed


def _apply_date(path: Path, committed: date) -> bool:
    text = path.read_text(encoding="utf-8")
    match = LAST_UPDATED_RE.search(text)
    if match is None:
        print(f"skip: {path.relative_to(PM_DIR)} has a non-canonical multiline last_updated", file=sys.stderr)
        return False
    replacement = (
        f"{match.group(1)}{match.group('quote')}{committed.isoformat()}"
        f"{match.group('quote')}{match.group('tail')}"
    )
    path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="update stale fields to their git commit date")
    parser.add_argument("--quiet", action="store_true", help="suppress the success summary")
    parser.add_argument("--only", nargs="+", type=Path, help="check only these PM-relative paths")
    args = parser.parse_args(argv)

    paths = args.only or _iter_docs()
    valid_paths: list[Path] = []
    for raw_path in paths:
        path = raw_path if raw_path.is_absolute() else PM_DIR / raw_path
        path = path.resolve()
        if path.is_file() and PM_DIR in path.parents:
            valid_paths.append(path)
    git_dates = _git_dates(valid_paths)
    stale: list[tuple[Path, date, date]] = []
    skipped = 0
    for raw_path in paths:
        path = raw_path if raw_path.is_absolute() else PM_DIR / raw_path
        path = path.resolve()
        if not path.is_file() or PM_DIR not in path.parents:
            skipped += 1
            continue
        result = _stale_date(path, git_dates.get(path.relative_to(PM_DIR).as_posix()))
        if result is None:
            continue
        recorded, committed = result
        stale.append((path, recorded, committed))
        if args.apply:
            _apply_date(path, committed)

    action = "updated" if args.apply else "stale"
    for path, recorded, committed in stale:
        print(f"{action}: {path.relative_to(PM_DIR)} {recorded.isoformat()} -> {committed.isoformat()}")
    if stale:
        if args.apply:
            print(f"✅ check_last_updated: updated {len(stale)} live doc(s)")
            return 0
        print(f"❌ check_last_updated: {len(stale)} live doc(s) have stale last_updated", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"✅ check_last_updated: no stale live dates ({skipped} path(s) skipped)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
