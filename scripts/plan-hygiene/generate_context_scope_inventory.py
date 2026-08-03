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


# Pure-reference frontmatter fields: their only job is citing another doc's path. When a cited
# doc moves/archives, check_reference_paths.py's own repoint tooling mechanically rewrites these
# fields on every citing doc -- that keeps the citation alive but is not a content change, and
# should not make the citing doc look newly STALE. Measured 2026-08-03: of 169 docs relying on
# this git-fallback (no `last_updated:` field), 103 (61%) had ONLY this class of commit as their
# single most recent touch -- i.e. ~34% of the corpus-wide STALE count was this false-positive
# class before this walk-back fix, not genuine content drift.
_REF_ONLY_FIELDS = ("context_scope:", "related:", "supersedes:", "superseded_by:", "depends_on:")
# Bounded walk-back depth. Deliberately small: measured 2026-08-03, 61% of docs on this fallback
# path resolve on the FIRST historical commit checked; a deep cap buys little extra accuracy for a
# real per-commit cost (each commit needs its OWN diff + its OWN full-file fetch -- see why in
# _commit_touches_only_ref_fields's docstring). Never returns a date OLDER than the truth, only
# ever fails to look far enough back on a doc with an unusually long run of pure-reference commits
# -- a safe direction to fail in (worst case: a few docs stay STALE that a deeper walk would have
# cleared, never the reverse).
_MAX_HISTORY_WALK = 5


def _commit_touches_only_ref_fields(sha: str, path: Path) -> bool:
    """True if `sha`'s diff to `path` is confined to the flow-list bodies of _REF_ONLY_FIELDS.

    Needs the file's content AT THIS COMMIT (not the current HEAD content) to locate those
    fields' line ranges -- an earlier version reused the current file's line positions as an
    approximation and it was wrong in practice (frontmatter shifts between commits, e.g. a field
    added/removed upstream of context_scope moves everything below it), producing a WORSE STALE
    count than not fixing this at all. Correctness over speed: this is 2 subprocess calls per
    commit walked, bounded by _MAX_HISTORY_WALK.
    """
    diff = subprocess.run(
        ["git", "show", sha, "--unified=0", "--", str(path)],
        cwd=PM,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    ).stdout
    hunk_headers = re.findall(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.MULTILINE)
    if not hunk_headers:
        return False

    full_new = subprocess.run(
        ["git", "show", f"{sha}:{path.relative_to(PM).as_posix()}"],
        cwd=PM,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    ).stdout.splitlines()

    blocks: list[tuple[int, int]] = []
    for idx, line in enumerate(full_new):
        stripped = line.strip()
        if any(stripped.startswith(f) for f in _REF_ONLY_FIELDS):
            start = idx + 1
            end = start
            for j in range(idx + 1, min(idx + 60, len(full_new))):
                if full_new[j].strip() in ("]", "],"):
                    end = j + 1
                    break
            blocks.append((start, end))
    if not blocks:
        return False

    def in_any_block(line_no: int) -> bool:
        return any(s <= line_no <= e for s, e in blocks)

    for new_start_s, new_count_s in hunk_headers:
        new_start = int(new_start_s)
        new_count = int(new_count_s) if new_count_s else 1
        for offset in range(max(new_count, 1)):
            if not in_any_block(new_start + offset):
                return False
    return True


def _git_last_commit_date_cheap(path: Path) -> str | None:
    """Date of the single most recent commit touching `path` -- one `git log` call, no diff
    inspection. This is what the whole corpus needs on every run, so it stays cheap."""
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


def _git_last_commit_date_accurate(path: Path) -> str | None:
    """Date of the most recent commit that changed `path` in a way that isn't confined to a
    pure-reference frontmatter field (see `_REF_ONLY_FIELDS`) -- a mechanical repoint of one of
    those fields (because a cited doc archived/moved) doesn't mean the doc's OWN content changed.
    Walks bounded history (_MAX_HISTORY_WALK commits) and falls back to the single newest commit
    if every commit checked is reference-only-confined (or on any parse/subprocess failure). Only
    called once the cheap single-commit date has already been tried and found wanting -- see
    `_last_touched`'s short-circuit -- since this needs 2 subprocess calls per commit walked.
    """
    try:
        out = subprocess.run(
            ["git", "log", f"-{_MAX_HISTORY_WALK}", "--format=%H %cs", "--", str(path)],
            cwd=PM,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [line for line in out.stdout.splitlines() if line.strip()]
    if not lines:
        return None

    newest_date = lines[0].split(" ", 1)[1]
    for line in lines:
        sha, date = line.split(" ", 1)
        try:
            if not _commit_touches_only_ref_fields(sha, path):
                return date
        except (OSError, subprocess.SubprocessError, ValueError):
            return newest_date
    return newest_date


def _last_touched(fm: dict, path: Path, marker: str | None) -> str | None:
    last_updated = fm.get("last_updated")
    if isinstance(last_updated, (dt.date, dt.datetime)):
        return last_updated.isoformat()[:10]
    if isinstance(last_updated, str) and last_updated.strip():
        return last_updated.strip()[:10]

    # No explicit last_updated -- fall back to git history. Walking back past reference-only
    # commits (_git_last_commit_date_accurate) can only push this date EARLIER or leave it
    # unchanged relative to the cheap single-commit date, never later -- so if the cheap date
    # already satisfies UP_TO_DATE against the marker, the accurate date can only agree too.
    # Skip the expensive walk entirely in that case -- it only needs to run for docs the cheap
    # check would flag STALE, which is a minority of the corpus.
    cheap_date = _git_last_commit_date_cheap(path)
    if marker is not None and cheap_date is not None and marker >= cheap_date:
        return cheap_date
    return _git_last_commit_date_accurate(path)


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
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            fm, body = ds.parse_frontmatter(text)
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
            marker = _latest_marker(body)
            last_touched = _last_touched(fm, path, marker)
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
