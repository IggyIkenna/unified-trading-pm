#!/usr/bin/env python3
"""Generate the current `context_scope` maintenance inventory across plan/issue docs.

Why this exists: `/context-scout` needs to know, on every run, which docs already carry an
up-to-date `context_scope:` reading-list and which don't — without re-reading the whole ~500-doc
corpus every day. Parses frontmatter properly via scripts/docs/docspec.py (PyYAML), the same
pattern generate_na_doc_tranche_inventory.py and generate_ag_closeout_audit_candidates.py already
use, instead of re-deriving YAML/line-grep parsing (that class of bug — a multi-line frontmatter
value or a star-bullet checkbox missed by a naive regex — has recurred twice already in this repo).

Verdict per in-scope doc (status active/open/blocked/paused only — a draft/complete/superseded/
cancelled/resolved/false-positive doc is dead weight, never scouted):
  - NEVER_SCOUTED  — no `context_scope` field, or present but empty
  - STALE          — has `context_scope`, but no dated `context-scout YYYY-MM-DD` Progress Log
                     marker at or after the doc's last-touched date (frontmatter `last_updated`,
                     falling back to the file's git last-commit date when absent)
  - UP_TO_DATE     — marker date >= last-touched date; skip (incremental mode)

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never (standing Phase-0 tool for the daily /context-scout sweep)
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]

DOC_TREES = ["plans/active/*.md", "plans/active/issues/*.md"]
IN_SCOPE_STATUS = {
    "plan": {"active", "blocked", "paused"},
    "issue": {"open", "blocked"},
}
MARKER_RE = re.compile(r"context-scout\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


def _load_docspec():
    spec = importlib.util.spec_from_file_location("docspec", PM / "scripts" / "docs" / "docspec.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load_docspec()


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pat in DOC_TREES:
        for p in PM.glob(pat):
            if p.is_file() and p not in seen:
                seen.add(p)
                out.append(p)
    return sorted(out)


def _git_last_commit_date(path: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=PM,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    date = out.stdout.strip()
    return date or None


def _last_touched(fm: dict, path: Path) -> str | None:
    last_updated = fm.get("last_updated")
    if isinstance(last_updated, (dt.date, dt.datetime)):
        return last_updated.isoformat()[:10]
    if isinstance(last_updated, str) and last_updated.strip():
        return last_updated.strip()[:10]
    return _git_last_commit_date(path)


def _latest_marker(body: str) -> str | None:
    dates = MARKER_RE.findall(body)
    return max(dates) if dates else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a summary table")
    args = parser.parse_args(argv)

    records = []
    for path in _iter_docs():
        rel = path.relative_to(PM).as_posix()
        try:
            fm, body = ds.parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError:
            continue
        if fm is None:
            continue
        doc_type = fm.get("doc_type")
        if doc_type not in IN_SCOPE_STATUS:
            continue
        status = fm.get("status")
        if status not in IN_SCOPE_STATUS[doc_type]:
            continue

        context_scope = fm.get("context_scope") or []
        if isinstance(context_scope, str):
            context_scope = [context_scope]

        if not context_scope:
            verdict = "NEVER_SCOUTED"
        else:
            last_touched = _last_touched(fm, path)
            marker = _latest_marker(body)
            if marker is not None and last_touched is not None and marker >= last_touched:
                verdict = "UP_TO_DATE"
            else:
                verdict = "STALE"

        records.append(
            {
                "path": rel,
                "doc_type": doc_type,
                "status": status,
                "parent_epic": fm.get("parent_epic"),
                "context_scope_count": len(context_scope),
                "verdict": verdict,
            }
        )

    if args.json:
        print(json.dumps(records, indent=1))
        return 0

    by_verdict: dict[str, int] = {}
    for r in records:
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1
    print(f"Total in-scope plan/issue docs: {len(records)}")
    for verdict in ("NEVER_SCOUTED", "STALE", "UP_TO_DATE"):
        print(f"  {verdict:14s} {by_verdict.get(verdict, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
