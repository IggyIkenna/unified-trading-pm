#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""
Epic body populator — 2026-05-21.

Scans every active plan in plans/active/*.md for `parent_epic:` frontmatter, groups by epic, and:

  1. Updates each epic's `related_plans:` frontmatter list with the full set of plans pointing at it.
  2. For each epic, replaces the "## Assigned active plans" section in the body with a freshly-generated
     priority-block grouping (P0/P1/P2/P3) listing every assigned plan with its title, status, and estimate.

If the epic doesn't have an existing "## Assigned active plans" section, the script appends one. For the 9 NEW stub
epics (which only have placeholder `_(operator fills this in)_` markers in their P0/P1/P2/P3 sections), this populator
replaces the placeholder with the real plan list.

The populator does NOT touch any other body content — existing epic narrative (rationale / scope / open questions /
codex SSOT pointers) is preserved as-is.

For each assigned plan in the priority block, the populator emits:

  ### [plan-slug](../active/plan-slug_YYYY_MM_DD.md)
  **status**: active | blocked | paused | complete
  **estimate**: <N> cal AI-days (class: refactor|design|infra|brand-new|research)
  **title**: <human-readable title>

  <empty line>

So the epic body becomes a manifest of all assigned active plans. Workers reading the epic see:
  - which plans they own (in priority order)
  - which are blocked
  - estimate to size effort

Usage:
    python3 unified-trading-pm/scripts/plans/populate_epic_bodies_2026_05_21.py --dry-run
    python3 unified-trading-pm/scripts/plans/populate_epic_bodies_2026_05_21.py --apply

Exit codes:
    0 = clean run (orphan count printed; per-epic counts printed)
    1 = unexpected (file unreadable, frontmatter malformed)
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

WORKSPACE = Path("/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1")
PM = WORKSPACE / "unified-trading-pm"
ACTIVE = PM / "plans" / "active"
EPICS = PM / "plans" / "epics"

# The 19 active epics (lowercase slugs, matching filenames in plans/epics/<slug>.md)
ACTIVE_EPICS = [
    # L0
    "defi_master",
    "cefi_master",
    "tradfi_master",
    "sports_master",
    "predictions_master",
    # L1
    "instruments_master",
    "mtds_mdps_master",
    "features_and_ml_master",
    "manifest_master",
    # L2
    "strategy_master",
    "execution_master",
    "trading_agent_master",
    # L3
    "dart_and_promote_master",
    "deployment_and_user_management_master",
    # L4
    "infrastructure_master",
    "observability_master",
    "batch_live_symmetry_master",
    "client_isolation_and_governance_master",
    # L5
    "orchestrator_master",
]


@dataclass
class PlanRef:
    """A reference to one active plan that points at an epic."""

    path: Path
    slug: str  # filename without .md
    title: str = ""
    priority: str = "P2"  # default if no priority found
    status: str = "active"
    estimate_class: str = ""
    estimate_calibrated_ai_days: str = ""

    @property
    def relative_path(self) -> str:
        return f"../active/{self.slug}.md"


def parse_frontmatter(path: Path) -> dict[str, str]:
    """Extract frontmatter key→value as raw strings (no YAML parser dep)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("---", 4)
    if end == -1:
        return {}
    frontmatter = text[4:end]
    out: dict[str, str] = {}
    current_key = None
    for line in frontmatter.split("\n"):
        m = re.match(r"^([a-z_][a-z0-9_]*)\s*:\s*(.*)$", line, re.IGNORECASE)
        if m:
            current_key = m.group(1)
            value = m.group(2).strip()
            if value:
                out[current_key] = value.strip("\"'")
        # Multi-line values (e.g. status: |) — only handle single-line for our needs
    return out


def normalise_epic(parent_epic: str) -> str:
    """Strip .md + path prefix + quotes; lowercase to match ACTIVE_EPICS."""
    val = parent_epic.strip().strip("\"'")
    val = val.split("/")[-1]
    if val.endswith(".md"):
        val = val[:-3]
    return val


def load_plan_refs() -> dict[str, list[PlanRef]]:
    """Scan active plans + group by parent_epic."""
    by_epic: dict[str, list[PlanRef]] = defaultdict(list)
    for path in sorted(ACTIVE.glob("*.md")):
        fm = parse_frontmatter(path)
        parent = fm.get("parent_epic", "")
        if not parent:
            continue
        epic = normalise_epic(parent)
        if epic not in ACTIVE_EPICS:
            # Could be SUPERSEDED slug or invalid — skip but warn
            print(f"  WARN: {path.name} has parent_epic={epic!r} (not in 19-epic registry; skipping)", file=sys.stderr)
            continue
        slug = path.stem
        title = fm.get("title", slug.replace("_", " ").replace("-", " ").title())
        # Priority may be in `priority:` field OR derived from `## Pn` headings in body — use frontmatter
        priority = fm.get("priority", "P2").upper().strip()
        if priority not in {"P0", "P1", "P2", "P3"}:
            priority = "P2"
        status = fm.get("status", "active").lower()
        # status can be multi-line (e.g. status: |\n  ACKED — ...) — handle that
        if "\n" in status or len(status) > 40:
            status = "active"
        estimate_class = fm.get("estimate_class", "")
        estimate_days = fm.get("estimate_calibrated_ai_days", "") or fm.get("estimate_baseline_ai_days", "")
        by_epic[epic].append(
            PlanRef(
                path=path,
                slug=slug,
                title=title,
                priority=priority,
                status=status,
                estimate_class=estimate_class,
                estimate_calibrated_ai_days=estimate_days,
            )
        )
    return by_epic


def render_priority_block(priority: str, plans: list[PlanRef]) -> str:
    """Render a P0/P1/P2/P3 section listing all plans at that priority."""
    titles = {
        "P0": "P0 — must complete before next foundation gate",
        "P1": "P1 — important; post-current-gate",
        "P2": "P2 — useful; opportunistic",
        "P3": "P3 — backlog; revisit quarterly",
    }
    if not plans:
        return f"## {titles[priority]}\n\n_(no plans currently assigned at this priority)_\n"
    lines = [f"## {titles[priority]}", ""]
    for p in sorted(plans, key=lambda x: x.slug):
        lines.append(f"### [`{p.slug}`]({p.relative_path})")
        meta_parts = [f"**status**: {p.status}"]
        if p.estimate_calibrated_ai_days:
            est_class = f" (class: {p.estimate_class})" if p.estimate_class else ""
            meta_parts.append(f"**estimate**: {p.estimate_calibrated_ai_days} cal AI-days{est_class}")
        lines.append(" · ".join(meta_parts))
        if p.title and p.title.lower() != p.slug.replace("_", " ").lower():
            lines.append(f"**title**: {p.title}")
        lines.append("")
    return "\n".join(lines)


def render_assigned_section(epic_slug: str, plans: list[PlanRef]) -> str:
    """Build the full '## Assigned active plans' section with P0/P1/P2/P3 sub-blocks."""
    if not plans:
        return (
            "## Assigned active plans\n\n"
            f"_(no active plans currently declare `parent_epic: {epic_slug}`."
            " Audit-pool wrapper plans for this epic land here as they are dispatched."
            " See [README.md](README.md) for the audit→plan→epic flow.)_\n"
        )
    # Group by priority
    by_priority: dict[str, list[PlanRef]] = defaultdict(list)
    for p in plans:
        by_priority[p.priority].append(p)
    # Render
    parts = [
        "## Assigned active plans",
        "",
        (
            f"_{len(plans)} active plans declare `parent_epic: {epic_slug}` in their frontmatter."
            " Workers pick up in priority order (P0 first)."
            " Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._"
        ),
        "",
    ]
    for priority in ["P0", "P1", "P2", "P3"]:
        parts.append(render_priority_block(priority, by_priority.get(priority, [])))
    return "\n".join(parts)


def update_related_plans_frontmatter(epic_path: Path, plans: list[PlanRef], apply: bool) -> int:
    """Update the related_plans: list in the epic's frontmatter."""
    if not epic_path.exists():
        return 0
    text = epic_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return 0
    end = text.find("---", 4)
    if end == -1:
        return 0
    frontmatter = text[4:end]
    body = text[end:]

    new_related = "\n".join(f"  - {p.relative_path}" for p in sorted(plans, key=lambda x: x.slug))
    if not new_related:
        new_related = "  []"
        new_value = "[]"
    else:
        new_value = "\n" + new_related

    # Find existing related_plans: block and replace
    pattern = re.compile(r"^related_plans\s*:\s*(\[\s*\]|\n(?:  - .+\n)*)", re.MULTILINE)
    if pattern.search(frontmatter):
        new_fm = pattern.sub(f"related_plans:{new_value}\n", frontmatter, count=1)
    else:
        # Append before closing ---
        new_fm = frontmatter.rstrip() + f"\nrelated_plans:{new_value}\n"

    if new_fm == frontmatter:
        return 0

    # Ensure frontmatter starts with newline so we don't join "---" + "name:" on same line
    if not new_fm.startswith("\n"):
        new_fm = "\n" + new_fm
    new_text = "---" + new_fm + body
    if apply:
        epic_path.write_text(new_text, encoding="utf-8")
    return 1


def replace_or_append_assigned_section(epic_path: Path, new_section: str, apply: bool) -> str:
    """Replace existing '## Assigned active plans' section, or append it before closing tags."""
    if not epic_path.exists():
        return "MISSING"
    text = epic_path.read_text(encoding="utf-8")

    # STEP 1: If this is a stub file with placeholder P0/P1/P2/P3 sections, strip the placeholder
    # block FIRST so we don't end up with duplicates after insert/append.
    placeholder_pattern = re.compile(
        r"## P0 — must complete before next foundation gate.*?(?=^## (?!P[0-3])|^# (?!#)|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    had_placeholder = "_(operator fills this in)_" in text and placeholder_pattern.search(text)
    if had_placeholder:
        text = placeholder_pattern.sub("", text)

    # STEP 2: If file already has a "## Assigned active plans" section (from a prior populator run
    # or hand-authored), replace it. The section extends until the next non-P0/P1/P2/P3 heading.
    assigned_pattern = re.compile(
        r"^## Assigned active plans.*?(?=^## (?!P[0-3])|^# (?!#)|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if assigned_pattern.search(text):
        # Replace ALL occurrences (in case of prior duplication bug)
        new_text = assigned_pattern.sub(new_section + "\n", text)
        # Collapse multiple consecutive replacements into one
        new_text = re.sub(r"(## Assigned active plans.*?\n)\1", r"\1", new_text, flags=re.DOTALL)
        action = "replaced"
    else:
        # No existing section — insert before trailing heading OR append
        trail_pattern = re.compile(
            r"^(## (?:Cross-references|Composition with workspace rules|Migration discipline|Lifecycle))",
            re.MULTILINE,
        )
        if trail_pattern.search(text):
            new_text = trail_pattern.sub(new_section + "\n\n\\1", text, count=1)
            action = "inserted"
        else:
            new_text = text.rstrip() + "\n\n" + new_section + "\n"
            action = "appended"

    if had_placeholder:
        action = "stub-replaced"

    if apply:
        epic_path.write_text(new_text, encoding="utf-8")
    return action


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate epic bodies from active plan parent_epic frontmatter")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("ERROR: must pass --dry-run or --apply", file=sys.stderr)
        return 1
    if args.dry_run and args.apply:
        print("ERROR: --dry-run and --apply are mutually exclusive", file=sys.stderr)
        return 1
    apply = args.apply

    print("=" * 80)
    print("EPIC BODY POPULATOR — 2026-05-21")
    print("=" * 80)
    print(f"\nWorkspace: {WORKSPACE}")
    print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
    print()

    by_epic = load_plan_refs()

    total_plans = sum(len(plans) for plans in by_epic.values())
    print("=== Active plans scanned, grouped by parent_epic ===\n")
    print(f"Total plans with parent_epic: {total_plans}\n")

    for epic_slug in ACTIVE_EPICS:
        plans = by_epic.get(epic_slug, [])
        by_p = defaultdict(int)
        for p in plans:
            by_p[p.priority] += 1
        p_summary = ", ".join(f"{p}={by_p[p]}" for p in ["P0", "P1", "P2", "P3"] if by_p[p] > 0) or "(empty)"
        print(f"  {epic_slug:50s} {len(plans):3d} plans  {p_summary}")
    print()

    print("=== Updating epic frontmatter (related_plans) + body (## Assigned active plans section) ===\n")
    for epic_slug in ACTIVE_EPICS:
        epic_path = EPICS / f"{epic_slug}.md"
        if not epic_path.exists():
            print(f"  SKIP: {epic_slug} — epic file missing at {epic_path.relative_to(WORKSPACE)}")
            continue
        plans = by_epic.get(epic_slug, [])
        new_section = render_assigned_section(epic_slug, plans)

        fm_changed = update_related_plans_frontmatter(epic_path, plans, apply)
        body_action = replace_or_append_assigned_section(epic_path, new_section, apply)

        action_label = "APPLIED" if apply else "WOULD"
        print(f"  {action_label} {epic_slug:50s} {len(plans):3d} plans  | frontmatter:{fm_changed} body:{body_action}")

    print("\n" + "=" * 80)
    print(f"POPULATION {'COMPLETE' if apply else 'DRY-RUN COMPLETE'}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
