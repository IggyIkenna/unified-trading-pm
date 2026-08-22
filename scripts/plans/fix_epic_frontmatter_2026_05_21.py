#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""
Epic frontmatter conformity fix — 2026-05-21.

Rewrites every active epic's frontmatter to the canonical epic schema (per plans/epics/README.md):
  REQUIRED: name, type=epic, tier, status, priority, assigned_vm, parent, owner, created, last_updated,
            locked_by, locked_since, asset_group, related_plans
  FORBIDDEN (stripped): deadline, estimate_class, estimate_baseline_ai_days, estimate_calibrated_ai_days,
            slug, date, phase, domain, folds_in, completion_gates, repo_gates, owner_repos, references,
            companion_to, related, todos, isProject, co_operators, codex_ssots, external_references, operator

Preserves: the `related_plans:` list (populator's work) + the entire body. Maps old fields → canonical
(slug→name, date→created, type=umbrella/plan/mixed→epic). Tier + assigned_vm + asset_group come from the
canonical registry below. SUPERSEDED archaeology files are skipped (kept as-is).

Usage:
    python3 scripts/plans/fix_epic_frontmatter_2026_05_21.py --dry-run
    python3 scripts/plans/fix_epic_frontmatter_2026_05_21.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EPICS = Path("/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm/plans/epics")

# Canonical registry: slug → (tier, assigned_vm, asset_group, default_priority)
REGISTRY = {
    "defi_master": ("L0", "vm-defi", "defi", "P0"),
    "cefi_master": ("L0", "vm-cefi", "cefi", "P0"),
    "tradfi_master": ("L0", "vm-tradfi", "tradfi", "P1"),
    "sports_master": ("L0", "vm-sports", "sports", "P1"),
    "predictions_master": ("L0", "vm-prediction", "prediction", "P1"),
    "instruments_master": ("L1", "vm-cefi", "cross-cutting", "P0"),
    "mtds_mdps_master": ("L1", "vm-ml", "cross-cutting", "P0"),
    "features_and_ml_master": ("L1", "vm-ml", "cross-cutting", "P1"),
    "manifest_master": ("L1", "vm-defi", "cross-cutting", "P0"),
    "strategy_master": ("L2", "vm-trading-core", "cross-cutting", "P0"),
    "execution_master": ("L2", "vm-trading-core", "cross-cutting", "P0"),
    "trading_agent_master": ("L2", "vm-trading-core", "cross-cutting", "P0"),
    "global_ledger_pnl_attribution_master": ("L2", "vm-trading-core", "cross-cutting", "P0"),
    "dart_and_promote_master": ("L3", "vm-operator-ops", "cross-cutting", "P0"),
    "deployment_and_user_management_master": ("L3", "vm-operator-ops", "cross-cutting", "P1"),
    "infrastructure_master": ("L4", "vm-cross-cutting", "infrastructure", "P0"),
    "observability_master": ("L4", "vm-cross-cutting", "cross-cutting", "P1"),
    "batch_live_symmetry_master": ("L4", "vm-cross-cutting", "cross-cutting", "P1"),
    "client_isolation_and_governance_master": ("L4", "vm-cross-cutting", "cross-cutting", "P0"),
    "orchestrator_master": ("L5", "vm-orchestrator", "meta", "P0"),
}


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_text, body_text). Robust to glued '---name:' opener."""
    # Normalise: ensure opener has newline. Find the closing --- on its own line.
    if not text.startswith("---"):
        return "", text
    # Find end delimiter: a line that is exactly '---'
    # Search after the first 3 chars.
    rest = text[3:]
    m = re.search(r"\n---\s*\n", rest)
    if not m:
        # try '---' at end
        m = re.search(r"\n---\s*$", rest)
    if not m:
        return "", text
    fm = rest[: m.start()]
    body = rest[m.end() :]
    return fm, body


def parse_fm(fm: str) -> dict[str, str]:
    out = {}
    for line in fm.split("\n"):
        mm = re.match(r"^([a-z_][a-z0-9_]*)\s*:\s*(.*)$", line, re.I)
        if mm and mm.group(2).strip():
            out[mm.group(1)] = mm.group(2).strip().strip("\"'")
    return out


def extract_related_plans(fm: str) -> list[str]:
    """Extract related_plans list items (lines like '  - ../active/x.md')."""
    out = []
    in_block = False
    for line in fm.split("\n"):
        if re.match(r"^related_plans\s*:", line):
            in_block = True
            continue
        if in_block:
            m = re.match(r"^\s+-\s+(.+?)\s*$", line)
            if m:
                out.append(m.group(1).strip())
            elif re.match(r"^[a-z_]", line, re.I):
                break  # next key
    return out


def build_canonical(slug: str, old: dict, related: list[str]) -> str:
    tier, vm, ag, default_pri = REGISTRY[slug]
    priority = old.get("priority", default_pri)
    if priority not in {"P0", "P1", "P2", "P3"}:
        priority = default_pri
    status = old.get("status", "active")
    if status not in {"active", "paused", "cancelled"}:
        status = "active"
    owner = old.get("owner", "ikenna")
    if owner == "claude-code":
        owner = "claude-code"
    created = old.get("created") or old.get("date") or "2026-05-07"
    # normalise created to YYYY-MM-DD if it has trailing text
    cm = re.match(r"(\d{4}-\d{2}-\d{2})", created)
    created = cm.group(1) if cm else "2026-05-07"
    locked_since = old.get("locked_since", "2026-05-07")
    lsm = re.match(r"(\d{4}-\d{2}-\d{2})", locked_since)
    locked_since = lsm.group(1) if lsm else "2026-05-07"

    lines = ["---"]
    lines.append(f"name: {slug}")
    lines.append("type: epic")
    lines.append(f"tier: {tier}")
    lines.append(f"status: {status}")
    lines.append(f"priority: {priority}")
    lines.append(f"assigned_vm: {vm}")
    lines.append("parent: master_to_live_defi_2026_05_23")
    lines.append(f"owner: {owner}")
    lines.append(f"created: {created}")
    lines.append("last_updated: 2026-05-21")
    lines.append("locked_by: live-defi-rollout")
    lines.append(f"locked_since: {locked_since}")
    lines.append(f"asset_group: {ag}")
    if related:
        lines.append("related_plans:")
        for r in related:
            lines.append(f"  - {r}")
    else:
        lines.append("related_plans: []")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run ^ args.apply):
        print("ERROR: pass exactly one of --dry-run / --apply", file=sys.stderr)
        return 1
    apply = args.apply

    fixed = 0
    for f in sorted(EPICS.glob("*.md")):
        if f.name == "README.md" or "SUPERSEDED" in f.name or f.stem == "orchestrator_master":
            continue
        slug = f.stem
        if slug not in REGISTRY:
            print(f"  WARN: {f.name} not in REGISTRY — skipping (add to REGISTRY if it's a real epic)")
            continue
        text = f.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        if not fm:
            print(f"  WARN: {f.name} no frontmatter found — skipping")
            continue
        old = parse_fm(fm)
        related = extract_related_plans(fm)
        new_fm = build_canonical(slug, old, related)
        new_text = new_fm + body.lstrip("\n").join("") if False else new_fm + "\n" + body.lstrip("\n")
        # Avoid leading blank explosion: ensure exactly one blank line between --- and body
        new_text = new_fm + "\n" + body.lstrip("\n")
        if new_text == text:
            print(f"  {f.name:<48} already canonical")
            continue
        if apply:
            f.write_text(new_text, encoding="utf-8")
        fixed += 1
        print(
            f"  {'FIXED' if apply else 'WOULD fix'} {f.name:<48}"
            f" tier={REGISTRY[slug][0]} vm={REGISTRY[slug][1]} ag={REGISTRY[slug][2]} related={len(related)}"
        )
    print(f"\n{'Fixed' if apply else 'Would fix'}: {fixed} epics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
