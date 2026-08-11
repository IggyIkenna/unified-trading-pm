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
                     marker at or after the doc's last-touched date (MAX of frontmatter
                     `last_updated`, when present, and the file's real git last-commit date --
                     never `last_updated` alone, which nothing auto-bumps on edit and so silently
                     goes stale; see `_last_touched`'s docstring)
  - COUNT_MISMATCH — has `context_scope` and a date-fresh marker (marker date >= last-touched),
                     but the marker's parenthetical count claim (e.g. "(4 entries)") disagrees
                     with the actual length of the live frontmatter list. Triggers a re-scout
                     pass so the list is restored to agreement. Root cause: a subsequent
                     context-scout batch edits the frontmatter list without updating the prior
                     marker's claimed count -- confirmed systemic (4 instances in one 13-doc
                     sample, 2026-08-06; see
                     plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md).
  - UP_TO_DATE     — marker date >= last-touched date AND claimed count matches actual (or the
                     marker carries no parenthetical count claim); skip (incremental mode)

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

# COUNT_MISMATCH detection: parenthetical count claim in a context-scout Progress Log bullet.
# Matches "(1 entry)" and "(4 entries)" plus a comma/prose-extended claim like
# "(4 entries, written and counted with extra care ...)" -- a `\b` after "entr(y|ies)" instead of
# requiring the closing paren immediately: the closing-paren-required form let a non-conforming
# real claim (comma-extended) fall through to a LATER, strict-form match elsewhere in the same
# window (e.g. a quoted excerpt of a different doc's marker), producing a false COUNT_MISMATCH --
# confirmed corpus false positive on
# plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md, see
# plans/active/issues/context_scope_count_mismatch_regex_false_positive_comma_extended_claim_2026_08_08.md.
# Verified against the live corpus (2026-08-11): this widening only ever RESOLVES a previously
# `None` claim to the doc's actual live count (4 docs affected, all now correct) -- no doc's
# extracted count flips to a different, wrong value.
COUNT_RE = re.compile(r"\((\d+)\s+entr(?:y|ies)\b")
# Marker bullet window: bounds how far to scan before/after the marker text.
_WINDOW_END_PATTERNS = ("\n- ", "\n## ", "\n```", "\n---", "\n> ")
_MAX_MARKER_WINDOW_CHARS = 2000
_BULLET_LOOKBACK = 300


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
# real per-commit cost (each commit needs its own parent's file content fetched AND its own file
# content fetched -- see _commit_touches_only_ref_fields's docstring). Never returns a date OLDER
# than the truth, only
# ever fails to look far enough back on a doc with an unusually long run of pure-reference commits
# -- a safe direction to fail in (worst case: a few docs stay STALE that a deeper walk would have
# cleared, never the reverse).
_MAX_HISTORY_WALK = 5


def _commit_touches_only_ref_fields(sha: str, path: Path) -> bool:
    """True if `sha`'s change to `path` leaves the body and every non-ref frontmatter field
    byte-identical to the parent commit -- i.e. only the _REF_ONLY_FIELDS values differ.

    Parses both the parent's and this commit's file content via the same PyYAML-backed
    docspec parser the rest of the corpus tooling uses, then diffs the STRUCTURED frontmatter
    dict + body string -- rather than hand-scanning the diff's hunk line ranges against a
    string-matched bracket span. That line-range heuristic (kept in git history if needed)
    mis-measured a single-line field's span: `depends_on: []` closes its bracket inline, so
    the scan for "the next bare ']' line" kept hunting PAST it looking for a closing bracket
    that was never there for depends_on -- and instead landed on an unrelated LATER field's
    closing bracket (e.g. context_scope's, several fields down), silently absorbing every
    field in between into depends_on's "block". Confirmed on a real corpus commit
    (17b53df1e3 against ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md):
    a genuinely new field, `archive_exempt: true`, landed between `resolved_by:`/`locked_by:`
    inside that erroneous span and was misclassified as ref-only-confined -- a false
    UP_TO_DATE risk, since walking back past a commit that actually changed real frontmatter
    content means `_last_touched` can return an earlier date than the truth. A structured
    old-vs-new comparison has no line-position component to get wrong. Still 2 subprocess
    calls per commit walked (parent content + this commit's content), same cost as before.
    """
    parent = subprocess.run(
        ["git", "show", f"{sha}^:{path.relative_to(PM).as_posix()}"],
        cwd=PM,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if parent.returncode != 0:
        return False  # no parent (doc created in this commit) -- always real content

    new_text = subprocess.run(
        ["git", "show", f"{sha}:{path.relative_to(PM).as_posix()}"],
        cwd=PM,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    ).stdout

    try:
        fm_old, body_old = ds.parse_frontmatter(parent.stdout)
        fm_new, body_new = ds.parse_frontmatter(new_text)
    except yaml.YAMLError:
        return False
    if fm_old is None or fm_new is None:
        return False
    if body_old != body_new:
        return False

    ref_keys = {f.rstrip(":") for f in _REF_ONLY_FIELDS}
    for key in set(fm_old) | set(fm_new):
        if key in ref_keys:
            continue
        if fm_old.get(key) != fm_new.get(key):
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
    """Real edit signal is git's commit date; `last_updated` is a manually-maintained frontmatter
    field nothing in this workspace auto-bumps on edit, so it silently goes stale (measured
    2026-08-03: 390/435 corpus docs carrying it were behind their real last commit; for 200 of
    those, trusting the stale value outright flipped the doc's verdict to a false UP_TO_DATE,
    hiding real post-scout edits from the incremental sweep -- e.g.
    `vol_dvol_backtestable_engines_2026_07_13.md` got genuine todo-flip commits after its scout
    marker, but its unbumped `last_updated` still read UP_TO_DATE). Take the MAX of `last_updated`
    and the best available git signal instead of trusting `last_updated` outright: a
    legitimately-set `last_updated` (e.g. an edit not yet committed) still counts, but it can never
    mask a later git-tracked edit the field was never updated to reflect."""
    candidates: list[str] = []
    last_updated = fm.get("last_updated")
    if isinstance(last_updated, (dt.date, dt.datetime)):
        candidates.append(last_updated.isoformat()[:10])
    elif isinstance(last_updated, str) and last_updated.strip():
        candidates.append(last_updated.strip()[:10])

    # Git signal: cheap single-commit date first; only pay for the multi-commit walk-back past
    # reference-only-confined commits (_git_last_commit_date_accurate) when the cheap date doesn't
    # already satisfy UP_TO_DATE against the marker -- walking back can only push the date EARLIER
    # or leave it unchanged, never later, so if the cheap date already clears the bar the accurate
    # date can only agree too.
    cheap_date = _git_last_commit_date_cheap(path)
    if marker is not None and cheap_date is not None and marker >= cheap_date:
        git_date = cheap_date
    else:
        git_date = _git_last_commit_date_accurate(path)
    if git_date:
        candidates.append(git_date)

    return max(candidates) if candidates else None


def _latest_marker_info(body: str) -> tuple[str, int] | None:
    """Return (date, position) of the latest context-scout marker in `body`, or None."""
    matches = list(MARKER_RE.finditer(body))
    if not matches:
        return None
    latest_date = max(m.group(1) for m in matches)
    latest_pos = max(m.start() for m in matches if m.group(1) == latest_date)
    return latest_date, latest_pos


def _latest_marker(body: str) -> str | None:
    info = _latest_marker_info(body)
    return info[0] if info is not None else None


def _marker_claimed_count(body: str, marker_pos: int) -> int | None:
    """Return the `(N entries)` count claimed in the Progress Log bullet containing
    `marker_pos`, or None if the bullet carries no parenthetical count claim."""
    start = body.rfind("\n- ", max(0, marker_pos - _BULLET_LOOKBACK), marker_pos)
    if start == -1:
        start = body.rfind("\n-", max(0, marker_pos - _BULLET_LOOKBACK), marker_pos)
    if start == -1:
        start = max(0, body.rfind("\n", 0, marker_pos))
    end = len(body)
    for pat in _WINDOW_END_PATTERNS:
        idx = body.find(pat, marker_pos, min(len(body), marker_pos + _MAX_MARKER_WINDOW_CHARS))
        if idx != -1 and idx < end:
            end = idx
    m = COUNT_RE.search(body[start:end])
    return int(m.group(1)) if m else None


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
            marker_info = _latest_marker_info(body)
            marker = marker_info[0] if marker_info is not None else None
            last_touched = _last_touched(fm, path, marker)
            if marker is not None and last_touched is not None and marker >= last_touched:
                # Date-fresh: also verify the marker's claimed count matches the actual list.
                if marker_info is not None:
                    claimed = _marker_claimed_count(body, marker_info[1])
                    if claimed is not None and claimed != len(context_scope):
                        verdict = "COUNT_MISMATCH"
                    else:
                        verdict = "UP_TO_DATE"
                else:
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
    for verdict in ("NEVER_SCOUTED", "STALE", "COUNT_MISMATCH", "UP_TO_DATE"):
        print(f"  {verdict:14s} {by_verdict.get(verdict, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
