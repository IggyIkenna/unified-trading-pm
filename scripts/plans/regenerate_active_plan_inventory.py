#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Regenerate the auto-tracked active plan inventory in master_to_live_defi_2026_05_23.md.

Reads every `plans/active/*.md` plan with `estimate_class` frontmatter, computes per-plan
done/todo checkbox count + cal_remaining (calibrated x todo/total), finds which epic master
(if any) references the plan, and writes a sorted markdown table between the AUTO-INVENTORY
markers in the master plan.

Solves two coupled problems:
- "What's done vs left?" — aggregate row + per-plan progress at a glance.
- "Which plans aren't wrapped by master/epics?" — orphan column visible inline.

Usage:
    python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py

Run from anywhere; resolves paths relative to this script's location.

Idempotent: only rewrites content between `<!-- AUTO-INVENTORY-START -->` and
`<!-- AUTO-INVENTORY-END -->` markers. Errors if markers absent (operator must add the
section + markers manually once).
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
EPICS_DIR = PM_ROOT / "plans" / "epics"
# MASTER_FILE itself was archived 2026-07-28 (plan-hygiene sweep: verified auto-regenerated
# inventory table, no Todos section, no unfinished work of its own) -- it keeps being
# auto-regenerated in place at its new archived path so this twice-daily Cloud-Scheduler job
# doesn't break; the script only ever rewrites content between the AUTO-INVENTORY markers, so
# the doc's own frontmatter/ARCHIVED-banner/Deferred-work section (all outside those markers)
# are untouched by this script.
MASTER_FILE = PM_ROOT / "plans" / "archive" / "2026_07" / "active_plan_inventory_dashboard_2026_07_24.md"
# The inventory TABLE lives in MASTER_FILE (above), but the ~175-sub-plan cross-reference
# corpus that "master"-attribution substring-matches against stayed behind in the archived
# cutover doc when the table was extracted out 2026-07-24 (plan_line_cap_remediation_2026_07_23.md
# op #2) -- read-only reference, included in the "master" attribution search but never written to.
MASTER_HISTORICAL_ARCHIVE = PM_ROOT / "plans" / "archive" / "2026_07" / "master_to_live_defi_2026_05_23.md"

SKIP_FILES = {"INDEX.md", "task_template.md", "_agent_pings.md"}
SKIP_PREFIXES = ("work_split_", "continuation_prompts_", "_AUDIT_", "_HANDOFF_", "_SESSION_HANDOFF_")

MARKER_START = "<!-- AUTO-INVENTORY-START -->"
MARKER_END = "<!-- AUTO-INVENTORY-END -->"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter_dict, body). Handles standard --- ... --- YAML."""
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return {}, text
    fm: dict[str, str] = {}
    end_idx = -1
    for i, line in enumerate(lines[1:], start=1):
        if line == "---":
            end_idx = i
            break
        m = re.match(r"^([\w_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    body = "\n".join(lines[end_idx + 1 :]) if end_idx > 0 else text
    return fm, body


def count_checkboxes(body: str) -> tuple[int, int]:
    done = len(re.findall(r"^[ \t]*-\s+\[x\]", body, re.MULTILINE | re.IGNORECASE))
    todo = len(re.findall(r"^[ \t]*-\s+\[\s\]", body, re.MULTILINE))
    return done, todo


def parse_cal(value: str) -> float | None:
    if not value or value.strip().upper() == "TBD":
        return None
    try:
        return float(value.split()[0].rstrip(","))
    except (ValueError, IndexError):
        return None


def find_owner(plan_stem: str, ref_corpus: dict[str, str], master_keys: set[str]) -> str:
    """Return 'master' / '<epic-name>' / 'orphan' based on first reference found."""
    for ref_name in sorted(ref_corpus.keys()):
        if plan_stem in ref_corpus[ref_name]:
            if ref_name in master_keys:
                return "master"
            return ref_name.replace(".epic.md", "").replace(".md", "")
    return "**orphan**"


def _commit_and_push_master() -> None:
    """Self-commit the regenerated master-plan inventory so a run never leaves the
    file dirty/unpushed (the "Slot N has unpushed plan(s)" fleet-git alert, 2026-06-21).

    docs(plans) is the sanctioned direct-push carve-out, so a regenerate-then-commit is
    safe. Best-effort: rebase onto LDR first (multi-agent), commit only when actually
    dirty, push; a push reject is logged, not raised (the next FF-pull/quickmerge carries
    it). SSOT: orchestrator_self_healing_hardening_2026_06_21 (2:37 inventory churn).
    """
    rel = str(MASTER_FILE.relative_to(PM_ROOT))

    def _git(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(PM_ROOT), *args], capture_output=True, text=True, check=check, timeout=120
        )

    if not _git("status", "--porcelain", rel).stdout.strip():
        print("inventory: no change to commit")
        return
    _git("pull", "--rebase", "--autostash", "origin", "live-defi-rollout")
    _git("add", rel)
    commit = _git("commit", "-m", "docs(plans): regenerate active-plan inventory dashboard")
    if commit.returncode != 0:
        print(f"WARN: inventory commit failed: {commit.stderr.strip()[:200]}", file=sys.stderr)
        return
    push = _git("push", "origin", "HEAD:live-defi-rollout")
    if push.returncode != 0:
        print(f"WARN: inventory push failed (will ride next FF-pull): {push.stderr.strip()[:200]}", file=sys.stderr)
    else:
        print("inventory: committed + pushed to live-defi-rollout")


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the active-plan inventory dashboard in the master plan.")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Self-commit + push the regenerated master plan (docs(plans) carve-out) so a "
        "scheduled/automated run never leaves it dirty/unpushed. Omit for a dry write-only run.",
    )
    args = parser.parse_args()

    if not MASTER_FILE.exists():
        print(f"ERROR: master plan not found at {MASTER_FILE}", file=sys.stderr)
        return 2

    master_text = MASTER_FILE.read_text()
    if MARKER_START not in master_text or MARKER_END not in master_text:
        print(
            f"ERROR: master plan missing AUTO-INVENTORY markers. Add this once:\n\n"
            f"## Active plan inventory + Done-vs-Left dashboard (auto-tracked)\n\n"
            f"{MARKER_START}\n\n"
            f"_(populated by `scripts/plans/regenerate_active_plan_inventory.py`)_\n\n"
            f"{MARKER_END}\n",
            file=sys.stderr,
        )
        return 2

    ref_corpus = {MASTER_FILE.name: master_text}
    master_keys = {MASTER_FILE.name}
    if MASTER_HISTORICAL_ARCHIVE.exists():
        archive_key = f"{MASTER_HISTORICAL_ARCHIVE.name} (archived)"
        ref_corpus[archive_key] = MASTER_HISTORICAL_ARCHIVE.read_text()
        master_keys.add(archive_key)
    for epic in sorted(EPICS_DIR.glob("*.md")):
        ref_corpus[epic.name] = epic.read_text()

    rows: list[dict] = []
    for plan in sorted(PLANS_DIR.glob("*.md")):
        if plan.name in SKIP_FILES or any(plan.name.startswith(p) for p in SKIP_PREFIXES):
            continue
        text = plan.read_text()
        fm, body = parse_frontmatter(text)
        if "estimate_class" not in fm:
            continue
        done, todo = count_checkboxes(body)
        total = done + todo
        pct = (done / total * 100) if total > 0 else 0.0
        cal_cal = parse_cal(fm.get("estimate_calibrated_ai_days", ""))
        cal_left = (cal_cal * todo / total) if (cal_cal is not None and total > 0) else cal_cal
        owner = find_owner(plan.stem, ref_corpus, master_keys)
        rows.append(
            {
                "name": plan.stem,
                "class": fm.get("estimate_class", "?"),
                "cal_cal": cal_cal,
                "done": done,
                "todo": todo,
                "pct": pct,
                "cal_left": cal_left,
                "owner": owner,
                "deadline": fm.get("deadline", "—").strip()[:40] or "—",
            }
        )

    rows.sort(key=lambda r: -(r["cal_left"] if r["cal_left"] is not None else -1))

    lines = [
        "| Plan | Owner | Class | Checkboxes | % done | Cal left | Deadline |",
        "|---|---|---|---|---|---|---|",
    ]
    total_cal = 0.0
    total_done_cal = 0.0
    total_left_cal = 0.0
    tbd_count = 0
    orphan_count = 0
    for r in rows:
        if r["owner"] == "**orphan**":
            orphan_count += 1
        if r["cal_cal"] is None:
            tbd_count += 1
            cal_left_str = "TBD"
        else:
            total_cal += r["cal_cal"]
            total_done_cal += r["cal_cal"] * (r["pct"] / 100)
            total_left_cal += r["cal_left"] or 0
            cal_left_str = f"{r['cal_left']:.1f}" if r["cal_left"] is not None else "0"
        cb = f"{r['done']}/{r['done'] + r['todo']}" if (r["done"] + r["todo"]) > 0 else "—"
        pct_str = f"{r['pct']:.0f}%" if (r["done"] + r["todo"]) > 0 else "—"
        link = f"[`{r['name']}`](./{r['name']}.md)"
        lines.append(f"| {link} | {r['owner']} | {r['class']} | {cb} | {pct_str} | {cal_left_str} | {r['deadline']} |")

    agg_pct = (total_done_cal / total_cal * 100) if total_cal > 0 else 0
    lines.append(
        f"| **TOTAL** ({len(rows)} plans) | {orphan_count} orphans, {tbd_count} TBD | — | — | "
        f"**{agg_pct:.0f}% done** | **{total_left_cal:.0f}** | — |"
    )

    inventory_md = (
        "\n_Auto-generated via `scripts/plans/regenerate_active_plan_inventory.py`. "
        "Sorted by `cal_left` desc. TBD = baseline not yet filled by owner agent. "
        "Orphan = plan not referenced by master or any epic — should be folded into the appropriate epic._\n\n"
        + "\n".join(lines)
        + "\n"
    )

    new_master = re.sub(
        rf"({re.escape(MARKER_START)}).*?({re.escape(MARKER_END)})",
        lambda m: f"{m.group(1)}{inventory_md}{m.group(2)}",
        master_text,
        count=1,
        flags=re.DOTALL,
    )

    if new_master == master_text:
        # Markers are present (checked above) and the regenerated table is byte-identical:
        # a no-op refresh, not a failure. Hook callers (prek pre-commit / post-merge) hit
        # this on every run where no plan state changed — must exit 0.
        print(
            f"Inventory already fresh: {len(rows)} plans, {orphan_count} orphans, {tbd_count} TBD, "
            f"{agg_pct:.0f}% done overall, {total_left_cal:.0f} cal AI-days left."
        )
        return 0

    MASTER_FILE.write_text(new_master)
    print(
        f"Regenerated inventory: {len(rows)} plans, {orphan_count} orphans, {tbd_count} TBD, "
        f"{agg_pct:.0f}% done overall, {total_left_cal:.0f} cal AI-days left."
    )
    if args.commit:
        _commit_and_push_master()
    return 0


if __name__ == "__main__":
    sys.exit(main())
