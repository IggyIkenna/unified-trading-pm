#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Count genuinely operator/credential-blocked todos across plans/active — a live snapshot,
not a one-off. The operator re-runs this periodically to track "how many things still need me"
as the fleet resolves items; the number changes daily, so this is a real tool, not throwaway.

Mirrors the ACTUAL dispatch-eligibility logic in
`agent-orchestrator/server/regen_backlog_from_plan.py` (`_is_non_dispatchable` /
`_has_live_blocked_token` / `_OPERATOR_TAG_PREFIX_RE`), not a simplified approximation — built
2026-07-29 while investigating `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`
(a real bug where a todo's OWN resolution note restating an old BLOCKED-* marker in past tense
was incorrectly re-gating it). If that parser changes, re-sync this file's regex constants —
they are intentionally copy-pasted, not imported, since this script has no dependency on the
agent-orchestrator repo being checked out alongside this one.

Classifies every open (`- [ ]`) todo in `plans/active/*.md` + `plans/active/issues/*.md` into:
  - operator_tag: leading `[OPERATOR]` tag — a live judgment call needing the operator's decision.
  - blocked_marker: a genuine BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch-optional marker, with no
    resolution language (was/no longer/retagged from/previously) immediately before it — an
    external credential/outage/permanent-deprioritization block, not a decision.
  - (everything else): dispatchable, not counted here.

Usage:
    python3 scripts/plan-hygiene/count_operator_blocking_todos.py [--json] [--by-tier]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PM_DIR = Path(__file__).resolve().parents[2]
PLANS_DIR = PM_DIR / "plans" / "active"
ISSUES_DIR = PLANS_DIR / "issues"

_UNCHECKED_RE = re.compile(r"^\s*-\s+\[ \]\s+(.+)$")
_FENCE_RE = re.compile(r"^\s*```")
_STRIKETHROUGH_RE = re.compile(r"^\s*~~.*~~\s*$")
_TODO_BLOCK_BOUNDARY_RE = re.compile(r"^\s*-\s+\[|^\s*#")

# Re-synced 2026-08-16 with agent-orchestrator/server/regen_backlog_from_plan.py: added
# the missing UPSTREAM-DESIGN alternative and an optional `:<doc-slug>` citation suffix
# (e.g. `BLOCKED-UPSTREAM-DESIGN:<slug>`) so a worker can name the specific blocking doc.
# Deliberately NOT a new `ON` alternative — `BLOCKED-ON:<ref>` is a SEPARATE, established
# marker family in agent-orchestrator/server/verify.py whose todos are deliberately
# dispatchable; see that file's `_ADDED_BLOCKED_LINE_RE` / `_BLOCKED_LINE_RE`.
_BLOCKED_TOKEN_RE = re.compile(
    r"BLOCKED-(CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-(OUTAGE|DESIGN)|PLAYWRIGHT|JURISDICTION)"
    r"(?::[\w-]+)?\b"
)
_STALE_MARKER_PREFIX_RE = re.compile(
    r"(?:\bwas\b|\bno longer\b|\bretagged\s+(?:from|away\s+from)\b|\bpreviously\b)"
    r"(?:\s*[`\[]{1,2}[\w\s\-]{0,24}[`\]]{1,2})?"
    r"\s*[:`\[]?\s*$",
    re.IGNORECASE,
)
_PERMANENT_NON_DISPATCHABLE_RE = re.compile(
    r"DEFERRED-BY-DESIGN\b|_\(\s*[Ss]tretch|\b[Ss]tretch,\s*optional\b|\*\*[Ss]tretch\*\*"
)
_OPERATOR_TAG_PREFIX_RE = re.compile(r"^\s*(?:\d+[a-z]?\.\s+)?(?:(?:\[[A-Z][A-Z_-]*\]|P[0-3]\.)\s*)+")
_PRIORITY_RE = re.compile(r"\bP([0-3])\b")


def _has_live_blocked_token(todo_block: str) -> bool:
    for match in _BLOCKED_TOKEN_RE.finditer(todo_block):
        prefix = todo_block[max(0, match.start() - 60) : match.start()]
        if not _STALE_MARKER_PREFIX_RE.search(prefix):
            return True
    return False


def _parse_frontmatter(text: str) -> dict[str, str]:
    fm: dict[str, str] = {}
    in_fm = False
    for i, line in enumerate(text.splitlines()):
        if line.strip() == "---":
            if not in_fm and i == 0:
                in_fm = True
                continue
            if in_fm:
                break
        if in_fm:
            m = re.match(r'^(\w[\w_-]*):\s*"?(.+?)"?\s*$', line)
            if m:
                fm[m.group(1)] = m.group(2)
    return fm


def _parse_file(plan_path: Path) -> list[dict]:
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    results: list[dict] = []
    in_fm = fm_opened = in_code = False
    idx = line_num = 0
    total = len(lines)
    while idx < total:
        raw = lines[idx]
        line_num += 1
        idx += 1
        line = raw.rstrip()
        if line_num == 1 and line.strip() == "---":
            in_fm = fm_opened = True
            continue
        if in_fm:
            if line.strip() == "---" and fm_opened:
                in_fm = False
            continue
        if _FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        if _STRIKETHROUGH_RE.match(line):
            continue
        m = _UNCHECKED_RE.match(line)
        if not m:
            continue
        description = m.group(1).strip()
        if not description:
            continue
        cont: list[str] = []
        peek = idx
        while peek < total and not _TODO_BLOCK_BOUNDARY_RE.match(lines[peek]):
            cont.append(lines[peek])
            peek += 1
        todo_block = "\n".join([description, *cont])
        non_dispatchable = bool(_PERMANENT_NON_DISPATCHABLE_RE.search(todo_block)) or _has_live_blocked_token(
            todo_block
        )
        tag_prefix = _OPERATOR_TAG_PREFIX_RE.match(description)
        operator_gated = bool(tag_prefix) and "[OPERATOR]" in tag_prefix.group(0)
        p_match = _PRIORITY_RE.search(description)
        p_tag = int(p_match.group(1)) if p_match else None
        if operator_gated or (non_dispatchable and not operator_gated):
            kind = "operator_tag" if operator_gated else "blocked_marker"
            results.append({"line": line_num, "kind": kind, "priority": p_tag, "desc": description[:180]})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="emit full row-level JSON instead of a summary")
    parser.add_argument("--by-tier", action="store_true", help="also print a per-asset_group breakdown")
    args = parser.parse_args(argv)

    if not PLANS_DIR.is_dir():
        print(f"ERROR: plans/active not found at {PLANS_DIR}", file=sys.stderr)
        return 2

    docs = sorted(PLANS_DIR.glob("*.md"))
    if ISSUES_DIR.is_dir():
        docs += sorted(ISSUES_DIR.glob("*.md"))

    rows: list[dict] = []
    for doc in docs:
        fm = _parse_frontmatter(doc.read_text(encoding="utf-8", errors="replace"))
        ag_raw = fm.get("asset_group", "?").strip("[]")
        groups = tuple(sorted(g.strip().strip("'\"") for g in ag_raw.split(",") if g.strip())) or ("?",)
        for r in _parse_file(doc):
            rows.append({"file": doc.name, "tier": ",".join(groups), **r})

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    by_kind = Counter(r["kind"] for r in rows)
    print(f"Total genuinely operator/credential-blocked todos: {len(rows)}")
    print(f"Distinct files: {len({r['file'] for r in rows})}")
    print(f"  operator_tag (direct decisions needed): {by_kind.get('operator_tag', 0)}")
    print(f"  blocked_marker (credential/external, not decisions): {by_kind.get('blocked_marker', 0)}")

    if args.by_tier:
        print("\nBy asset_group:")
        tier_counts = Counter(r["tier"] for r in rows)
        for tier, count in tier_counts.most_common():
            print(f"  {count:4d}  {tier}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
