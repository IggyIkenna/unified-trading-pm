#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Regenerate the domain-grouped active-plan index in plans/active/INDEX.md.

Operator decision 2026-07-27 (`june_2026_vintage_audit_findings_2026_07_27.md` §5#26, resolving
`issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md` Finding 2): KEEP `plans/active/INDEX.md`
but AUTO-GENERATE it, replacing the hand-maintained content that had drifted to 226 stale entries
(dangling links into `archive/`, plans added without an INDEX bump) against the live plan set.

Mirrors `regenerate_active_plan_inventory.py`'s pattern: reads every `plans/active/*.md` plan's own
frontmatter (`asset_group:`, `summary:`, `status:`), groups by asset_group (a plan tagged with
multiple groups appears under each — the point is "findable from any domain section"), and writes a
sorted markdown block between `<!-- AUTO-INDEX-START -->` / `<!-- AUTO-INDEX-END -->` markers.

Usage:
    python3 unified-trading-pm/scripts/plans/regenerate_active_plan_index.py [--commit]

Run from anywhere; resolves paths relative to this script's location.

Idempotent: only rewrites content between the AUTO-INDEX markers. Errors if markers are absent
(operator/agent adds the section + markers once as part of the automation rollout).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
PLANS_DIR = PM_ROOT / "plans" / "active"
INDEX_FILE = PLANS_DIR / "INDEX.md"

SKIP_FILES = {"INDEX.md", "task_template.md", "_agent_pings.md"}
SKIP_PREFIXES = ("work_split_", "continuation_prompts_", "_AUDIT_", "_HANDOFF_", "_SESSION_HANDOFF_")

MARKER_START = "<!-- AUTO-INDEX-START -->"
MARKER_END = "<!-- AUTO-INDEX-END -->"

# plans/PLAN_FORMAT.md's declared asset_group enum, in the display order used below.
KNOWN_ASSET_GROUPS = [
    "cefi",
    "defi",
    "tradfi",
    "sports",
    "prediction",
    "cross-cutting",
    "ao",
    "ci",
    "infrastructure",
    "meta",
]

SUMMARY_MAX_CHARS = 240


def parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal frontmatter parser covering the two shapes plans/PLAN_FORMAT.md actually uses:
    single-line scalars/bracket-lists (`asset_group: [defi]`) and block-scalar or bare-continuation
    multi-line values (`summary: >-` / `summary: |` / bare `summary:` each followed by indented
    continuation lines) - not a general YAML parser, deliberately scoped to this corpus's dialect.
    """
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return {}
    fm: dict[str, str] = {}
    i = 1
    n = len(lines)
    while i < n:
        line = lines[i]
        if line == "---":
            break
        m = re.match(r"^([\w_]+):[ \t]?(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">-", ">", "|", "|-", ""):
            # Block scalar or bare multi-line value: consume indented continuation lines.
            parts: list[str] = []
            j = i + 1
            while j < n and lines[j] != "---" and (lines[j].startswith((" ", "\t")) or lines[j].strip() == ""):
                stripped = lines[j].strip()
                if not stripped or stripped in ("[", "]"):
                    j += 1
                    continue
                # Skip standalone comment lines (e.g. `  # purely a note`).
                if stripped.startswith("#"):
                    j += 1
                    continue
                # Strip trailing `# comment` on value-bearing continuation lines —
                # same treatment as single-line scalars below (line 98).  Without
                # this a line like `[sports] # corrected 2026-07-25 (...), a genuine
                # mistag: ...` gets its comment prose shattered on commas into
                # garbage tokens by parse_asset_groups().
                stripped = re.sub(r"\s+#.*$", "", stripped).strip()
                if stripped:
                    parts.append(stripped)
                j += 1
            fm[key] = " ".join(parts)
            i = j
            continue
        # Strip a trailing `# comment` on single-line scalars (common in this corpus, e.g.
        # `status: active # was: complete ...`) — but only a SPACE-preceded `#`, so bracket
        # lists/URLs containing a literal `#` are untouched.
        fm[key] = re.sub(r"\s+#.*$", "", val).strip()
        i += 1
    return fm


def parse_asset_groups(raw: str) -> list[str]:
    """`[defi, cross-cutting]` / `[]` / `defi` -> ['defi', 'cross-cutting'] / [] / ['defi']."""
    raw = raw.strip()
    if not raw:
        return []
    raw = raw.strip("[]")
    groups = [g.strip() for g in raw.split(",") if g.strip()]
    return groups


def clean_summary(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw).strip()
    if len(text) > SUMMARY_MAX_CHARS:
        text = text[:SUMMARY_MAX_CHARS].rsplit(" ", 1)[0] + "…"
    return text


def _commit_and_push_index() -> None:
    """Self-commit the regenerated INDEX.md so a run never leaves the file dirty/unpushed —
    mirrors regenerate_active_plan_inventory.py's `_commit_and_push_master`. `docs(plans)` is the
    sanctioned direct-push carve-out."""
    rel = str(INDEX_FILE.relative_to(PM_ROOT))

    def _git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(PM_ROOT), *args], capture_output=True, text=True, timeout=120)

    if not _git("status", "--porcelain", rel).stdout.strip():
        print("index: no change to commit")
        return
    _git("pull", "--rebase", "--autostash", "origin", "live-defi-rollout")
    _git("add", rel)
    commit = _git("commit", "-m", "docs(plans): regenerate active-plan domain index")
    if commit.returncode != 0:
        print(f"WARN: index commit failed: {commit.stderr.strip()[:200]}", file=sys.stderr)
        return
    push = _git("push", "origin", "HEAD:live-defi-rollout")
    if push.returncode != 0:
        print(f"WARN: index push failed (will ride next FF-pull): {push.stderr.strip()[:200]}", file=sys.stderr)
    else:
        print("index: committed + pushed to live-defi-rollout")


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the domain-grouped active-plan index.")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Self-commit + push the regenerated INDEX.md (docs(plans) carve-out) so a "
        "scheduled/automated run never leaves it dirty/unpushed. Omit for a dry write-only run.",
    )
    args = parser.parse_args()

    if not INDEX_FILE.exists():
        print(f"ERROR: index file not found at {INDEX_FILE}", file=sys.stderr)
        return 2

    index_text = INDEX_FILE.read_text()
    if MARKER_START not in index_text or MARKER_END not in index_text:
        print(
            f"ERROR: {INDEX_FILE} missing AUTO-INDEX markers. Add this once:\n\n"
            f"{MARKER_START}\n\n"
            f"_(populated by `scripts/plans/regenerate_active_plan_index.py`)_\n\n"
            f"{MARKER_END}\n",
            file=sys.stderr,
        )
        return 2

    grouped: dict[str, list[tuple[str, str, str]]] = {g: [] for g in KNOWN_ASSET_GROUPS}
    uncategorized: list[tuple[str, str, str]] = []
    total = 0

    for plan in sorted(PLANS_DIR.glob("*.md")):
        if plan.name in SKIP_FILES or any(plan.name.startswith(p) for p in SKIP_PREFIXES):
            continue
        text = plan.read_text()
        fm = parse_frontmatter(text)
        if "doc_type" not in fm or fm.get("doc_type") != "plan":
            continue
        total += 1
        summary = clean_summary(fm.get("summary", ""))
        status = fm.get("status", "").strip()
        badge = f" **[{status}]**" if status and status not in ("active",) else ""
        entry = (plan.stem, summary, badge)
        groups = parse_asset_groups(fm.get("asset_group", ""))
        if not groups:
            uncategorized.append(entry)
            continue
        for g in groups:
            grouped.setdefault(g, []).append(entry)

    section_lines: list[str] = []
    for group in KNOWN_ASSET_GROUPS:
        entries = grouped.get(group, [])
        if not entries:
            continue
        section_lines.append(f"### {group} ({len(entries)})\n")
        for name, summary, badge in sorted(entries):
            link = f"[`{name}`](./{name}.md)"
            summary_part = f" — {summary}" if summary else ""
            section_lines.append(f"- {link}{badge}{summary_part}")
        section_lines.append("")

    if uncategorized:
        section_lines.append(f"### uncategorized ({len(uncategorized)}) — missing/empty `asset_group:`\n")
        for name, summary, badge in sorted(uncategorized):
            link = f"[`{name}`](./{name}.md)"
            summary_part = f" — {summary}" if summary else ""
            section_lines.append(f"- {link}{badge}{summary_part}")
        section_lines.append("")

    index_md = (
        f"\n_Auto-generated via `scripts/plans/regenerate_active_plan_index.py`. {total} plans across "
        f"{sum(1 for g in KNOWN_ASSET_GROUPS if grouped.get(g))} domains"
        + (f" + {len(uncategorized)} uncategorized" if uncategorized else "")
        + ". A plan tagged with multiple `asset_group:` values appears under each. Grep this block for a domain "
        "keyword before scanning `plans/active/` by hand._\n\n" + "\n".join(section_lines).rstrip() + "\n"
    )

    new_index = re.sub(
        rf"({re.escape(MARKER_START)}).*?({re.escape(MARKER_END)})",
        lambda m: f"{m.group(1)}{index_md}{m.group(2)}",
        index_text,
        count=1,
        flags=re.DOTALL,
    )

    if new_index == index_text:
        print(f"Index already fresh: {total} plans across {len(KNOWN_ASSET_GROUPS)} known domains.")
        return 0

    INDEX_FILE.write_text(new_index)
    print(f"Regenerated index: {total} plans, {len(uncategorized)} uncategorized.")
    if args.commit:
        _commit_and_push_index()
    return 0


if __name__ == "__main__":
    sys.exit(main())
