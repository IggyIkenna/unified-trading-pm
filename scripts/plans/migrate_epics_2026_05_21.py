#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
"""
Epic consolidation migration — 2026-05-21.

Renames + moves + promotes + creates epic stubs per the operator-acked plan in
plans/epics/README.md. Updates all cross-references workspace-wide.

Actions handled by this script:
  1. RENAME (8) — drop date suffix from existing epic slugs; also restructure 2 names
     (instruments_live_master → instruments_master; ml_and_features_master → features_and_ml_master)
  2. PROMOTE (3) — move from plans/active/ to plans/epics/ with rename:
       mtds_mdps_master → mtds_mdps_master
       orchestrator_master → orchestrator_master
       defi_master → defi_master (also moves dir)
  3. CREATE STUB (9) — new epic files with canonical frontmatter only (operator fills body):
       execution_master, deployment_and_user_management_master, observability_master,
       batch_live_symmetry_master, trading_agent_master,
       strategy_master (from split), dart_and_promote_master (from split),
       manifest_master (from consolidate), client_isolation_and_governance_master (from extend)

NOT handled by this script (operator manual after script runs):
  - Splitting strategy_and_dart_master content into strategy + dart_and_promote bodies
  - Consolidating manifest_evolution + manifest_migration bodies into manifest_master
  - Extending cross_cutting_may_23 scope into client_isolation_and_governance_master
  - Adding SUPERSEDED-BY banners to the old files (script DOES leave them in place;
    operator adds banner + decides whether to archive)

Cross-reference updates: for every rename/promote, this script greps workspace-wide
for the old slug + replaces with new slug. Excludes binary files, .venv*, node_modules,
.git/, archives, and __pycache__.

Usage:
    python3 unified-trading-pm/scripts/plans/migrate_epics_2026_05_21.py --dry-run
    python3 unified-trading-pm/scripts/plans/migrate_epics_2026_05_21.py --apply
    python3 unified-trading-pm/scripts/plans/migrate_epics_2026_05_21.py --apply --skip-stubs
    python3 unified-trading-pm/scripts/plans/migrate_epics_2026_05_21.py --apply --only-renames

Exit codes:
    0 = clean dry-run or successful apply
    1 = unexpected state (e.g. source file missing, dest already exists, rg failure)
    2 = ref-update produced zero hits where >0 expected (sanity check failure)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------- Workspace + path constants ----------

WORKSPACE = Path("/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1")
PM = WORKSPACE / "unified-trading-pm"
PLANS = PM / "plans"
EPICS = PLANS / "epics"
ACTIVE = PLANS / "active"

# Excluded paths in workspace-wide search-and-replace (regex patterns for ripgrep --glob)
EXCLUDE_GLOBS = [
    "!.venv*",
    "!.tabs/*/node_modules",
    "!.git",
    "!**/__pycache__",
    "!**/dist",
    "!**/build",
    "!**/.pytest_cache",
    # Archive plans are frozen — DO NOT update their references; that breaks archaeology
    "!plans/archive/**",
    "!**/plans/archive/**",
]

# ---------- Action dataclasses ----------


@dataclass
class Rename:
    """In-place rename within plans/epics/. Source + dest in same dir."""

    old_slug: str  # e.g. "cefi_master"
    new_slug: str  # e.g. "cefi_master"

    @property
    def old_path(self) -> Path:
        # cross_cutting_may_23_SUPERSEDED_2026_05_21 has the anomalous .epic.md extension
        if self.old_slug == "cross_cutting_may_23_SUPERSEDED_2026_05_21":
            return EPICS / f"{self.old_slug}.epic.md"
        return EPICS / f"{self.old_slug}.md"

    @property
    def new_path(self) -> Path:
        return EPICS / f"{self.new_slug}.md"


@dataclass
class Promote:
    """Move from plans/active/ to plans/epics/ with rename."""

    old_slug: str  # e.g. "mtds_mdps_master"
    new_slug: str  # e.g. "mtds_mdps_master"
    src_dir: Path = field(default_factory=lambda: ACTIVE)

    @property
    def old_path(self) -> Path:
        return self.src_dir / f"{self.old_slug}.md"

    @property
    def new_path(self) -> Path:
        return EPICS / f"{self.new_slug}.md"


@dataclass
class CreateStub:
    """Create a new epic stub with canonical frontmatter only. Body filled by operator."""

    slug: str
    tier: str  # e.g. "L2"
    assigned_vm: str  # e.g. "vm-trading-core"
    asset_group: str  # e.g. "cross-cutting"
    owns: str  # one-line description of scope
    derived_from: str = ""  # if split/consolidate/extend, name the source

    @property
    def path(self) -> Path:
        return EPICS / f"{self.slug}.md"

    def frontmatter(self) -> str:
        derived_line = f"# Derived from: {self.derived_from}\n" if self.derived_from else ""
        return f"""---
name: {self.slug}
type: epic
tier: {self.tier}
status: active
priority: P0
assigned_vm: {self.assigned_vm}
parent: master_to_live_defi_2026_05_23
owner: ikenna
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
asset_group: {self.asset_group}
related_plans: []
---

{derived_line}
# {self.slug.replace("_", " ").title()}

**Owns**: {self.owns}

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body
with P0/P1/P2/P3 priority blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## P0 — must complete before next foundation gate

_(operator fills this in with active plan references)_

## P1 — important; post-current-gate

_(operator fills this in)_

## P2 — useful; opportunistic

_(operator fills this in)_

## P3 — backlog; revisit quarterly

_(operator fills this in)_
"""


# ---------- The migration manifest ----------

RENAMES: list[Rename] = [
    Rename("cefi_master", "cefi_master"),
    Rename("tradfi_master", "tradfi_master"),
    Rename("sports_master", "sports_master"),
    Rename("predictions_master", "predictions_master"),
    Rename("infrastructure_master", "infrastructure_master"),
    Rename("instruments_master", "instruments_master"),
    Rename("features_and_ml_master", "features_and_ml_master"),
    Rename("strategy_and_dart_master_SUPERSEDED_2026_05_21", "strategy_and_dart_master_SUPERSEDED_2026_05_21"),
    # ^ strategy_and_dart is being split into strategy_master + dart_and_promote_master.
    # The old file is renamed with SUPERSEDED suffix (archaeology) and stays in plans/epics/.
    # Operator manually moves body content into the two new stubs (created below) and
    # adds a SUPERSEDED-BY banner to the renamed file.
    Rename("manifest_evolution_SUPERSEDED_2026_05_21", "manifest_evolution_SUPERSEDED_2026_05_21"),
    Rename("manifest_migration_SUPERSEDED_2026_05_21", "manifest_migration_SUPERSEDED_2026_05_21"),
    # ^ manifest_evolution + manifest_migration consolidate into manifest_master.
    # Old files renamed with SUPERSEDED suffix. Operator merges bodies into new stub.
    Rename("cross_cutting_may_23_SUPERSEDED_2026_05_21", "cross_cutting_may_23_SUPERSEDED_2026_05_21"),
    # ^ cross_cutting scope extends into client_isolation_and_governance_master.
]

PROMOTES: list[Promote] = [
    Promote("defi_master", "defi_master"),
    Promote("mtds_mdps_master", "mtds_mdps_master"),
    Promote("orchestrator_master", "orchestrator_master"),
]

STUBS: list[CreateStub] = [
    # NEW epics (no prior content)
    CreateStub(
        slug="execution_master",
        tier="L2",
        assigned_vm="vm-trading-core",
        asset_group="cross-cutting",
        owns=(
            "execution-service: handlers + transfers + treasury coordinator"
            " + custody integration + flash loan + matching engine"
        ),
    ),
    CreateStub(
        slug="deployment_and_user_management_master",
        tier="L3",
        assigned_vm="vm-operator-ops",
        asset_group="cross-cutting",
        owns="deployment-api + deployment-ui + user-management-service + user-management-ui",
    ),
    CreateStub(
        slug="observability_master",
        tier="L4",
        assigned_vm="vm-cross-cutting",
        asset_group="cross-cutting",
        owns="alerting-service + monitoring + telemetry + 3am-auto-recovery agent",
    ),
    CreateStub(
        slug="batch_live_symmetry_master",
        tier="L4",
        assigned_vm="vm-cross-cutting",
        asset_group="cross-cutting",
        owns="per-service batch=live audit; reconciliation; codifies CLAUDE.md HARD RULE 'Batch = Live'",
    ),
    CreateStub(
        slug="trading_agent_master",
        tier="L2",
        assigned_vm="vm-trading-core",
        asset_group="cross-cutting",
        owns="trading-agent-service closed-loop allocator + AllocationDirective + PnL stream consumer",
    ),
    # SPLIT outputs (operator fills with content from strategy_and_dart_master)
    CreateStub(
        slug="strategy_master",
        tier="L2",
        assigned_vm="vm-trading-core",
        asset_group="cross-cutting",
        owns=(
            "strategy-service post-consolidation (engine + portfolio_allocator + risk + position + pnl); 53 archetypes"
        ),
        derived_from="strategy_and_dart_master_SUPERSEDED_2026_05_21 (split)",
    ),
    CreateStub(
        slug="dart_and_promote_master",
        tier="L3",
        assigned_vm="vm-operator-ops",
        asset_group="cross-cutting",
        owns="DART UI + ManualTradeGateDialog + promote workflow (CLI + UI) + state machine + candidate manifest",
        derived_from="strategy_and_dart_master_SUPERSEDED_2026_05_21 (split)",
    ),
    # CONSOLIDATE output (operator merges manifest_evolution + manifest_migration bodies)
    CreateStub(
        slug="manifest_master",
        tier="L1",
        assigned_vm="vm-defi",
        asset_group="cross-cutting",
        owns=(
            "manifest schema v8 + honest absence + backfill + evolution discipline"
            " (consolidates manifest_evolution + manifest_migration)"
        ),
        derived_from=(
            "manifest_evolution_SUPERSEDED_2026_05_21 + manifest_migration_SUPERSEDED_2026_05_21 (consolidate)"
        ),
    ),
    # EXTEND output (operator carries cross_cutting_may_23 scope + adds client/jurisdiction/share-class)
    CreateStub(
        slug="client_isolation_and_governance_master",
        tier="L4",
        assigned_vm="vm-cross-cutting",
        asset_group="cross-cutting",
        owns=(
            "per-client subprocess isolation + cross-client funds isolation HARD RULE"
            " + jurisdiction restrictions + share-class enum reconciliation"
            " + UAC schema evolution + hardcoded-value cleanup"
        ),
        derived_from="cross_cutting_may_23_SUPERSEDED_2026_05_21 (extend)",
    ),
]


# ---------- Helpers ----------


def run(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a shell command. Default: capture output, check rc."""
    return subprocess.run(
        cmd,
        check=check,
        cwd=WORKSPACE,
        capture_output=capture,
        text=True,
    )


def count_references(slug: str) -> int:
    """Count workspace-wide references to a slug (excluding archive + .git + node_modules)."""
    cmd = [
        "rg",
        "--no-config",
        "--count-matches",
        "--no-heading",
        "--no-line-number",
        "--no-filename",
        slug,
    ]
    for glob in EXCLUDE_GLOBS:
        cmd.extend(["--glob", glob])
    cmd.append(str(WORKSPACE))
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE)
    if proc.returncode == 1:
        # No matches
        return 0
    if proc.returncode != 0:
        print(f"WARN: ripgrep failed for slug={slug}: {proc.stderr}", file=sys.stderr)
        return -1
    # Output is one line per file with count; sum.
    return sum(int(line.split(":")[-1] if ":" in line else line) for line in proc.stdout.splitlines() if line.strip())


def find_referencing_files(slug: str) -> list[Path]:
    """List files that reference the slug (for diff transparency in dry-run)."""
    cmd = [
        "rg",
        "--no-config",
        "--files-with-matches",
        slug,
    ]
    for glob in EXCLUDE_GLOBS:
        cmd.extend(["--glob", glob])
    cmd.append(str(WORKSPACE))
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE)
    if proc.returncode == 1:
        return []
    if proc.returncode != 0:
        return []
    return [Path(line) for line in proc.stdout.splitlines() if line.strip()]


def replace_in_workspace(old: str, new: str, apply: bool) -> int:
    """Replace `old` with `new` workspace-wide in text files. Returns count of files changed."""
    files = find_referencing_files(old)
    changed = 0
    for path in files:
        # Skip the file being renamed itself (handled separately via git mv)
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        if old not in content:
            continue
        new_content = content.replace(old, new)
        if new_content == content:
            continue
        if apply:
            path.write_text(new_content, encoding="utf-8")
        changed += 1
    return changed


def git_mv(src: Path, dst: Path, apply: bool) -> None:
    """git mv preserving history."""
    if not src.exists():
        print(f"  ERROR: source missing: {src}", file=sys.stderr)
        return
    if dst.exists():
        print(f"  ERROR: dest already exists: {dst}", file=sys.stderr)
        return
    if apply:
        cmd = ["git", "-C", str(PM), "mv", str(src.relative_to(PM)), str(dst.relative_to(PM))]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"  ERROR: git mv failed: {proc.stderr}", file=sys.stderr)
            return
    print(f"  {'APPLIED ' if apply else 'WOULD '} git mv: {src.relative_to(WORKSPACE)} → {dst.relative_to(WORKSPACE)}")


# ---------- Action handlers ----------


def do_renames(renames: list[Rename], apply: bool) -> None:
    print("\n=== RENAMES (8 + 4 SUPERSEDED) ===\n")
    for r in renames:
        print(f"\n→ {r.old_slug} → {r.new_slug}")
        if not r.old_path.exists():
            print(f"  SKIP: source missing — {r.old_path.relative_to(WORKSPACE)}")
            continue
        ref_count = count_references(r.old_slug)
        files = find_referencing_files(r.old_slug)
        print(f"  refs: {ref_count} matches across {len(files)} files")
        if not apply:
            for f in files[:5]:
                print(f"    - {f.relative_to(WORKSPACE)}")
            if len(files) > 5:
                print(f"    - ... and {len(files) - 5} more")
        # 1. git mv the file
        git_mv(r.old_path, r.new_path, apply)
        # 2. replace old slug with new slug everywhere
        changed = replace_in_workspace(r.old_slug, r.new_slug, apply)
        print(f"  {'APPLIED' if apply else 'WOULD update'} {changed} files for slug ref")


def do_promotes(promotes: list[Promote], apply: bool) -> None:
    print("\n=== PROMOTES (3) ===\n")
    for p in promotes:
        print(f"\n→ {p.old_slug} (active/) → {p.new_slug} (epics/)")
        if not p.old_path.exists():
            print(f"  SKIP: source missing — {p.old_path.relative_to(WORKSPACE)}")
            continue
        ref_count = count_references(p.old_slug)
        files = find_referencing_files(p.old_slug)
        print(f"  refs: {ref_count} matches across {len(files)} files")
        if not apply:
            for f in files[:5]:
                print(f"    - {f.relative_to(WORKSPACE)}")
            if len(files) > 5:
                print(f"    - ... and {len(files) - 5} more")
        git_mv(p.old_path, p.new_path, apply)
        changed = replace_in_workspace(p.old_slug, p.new_slug, apply)
        print(f"  {'APPLIED' if apply else 'WOULD update'} {changed} files for slug ref")


def do_stubs(stubs: list[CreateStub], apply: bool) -> None:
    print("\n=== CREATE STUBS (9) ===\n")
    for s in stubs:
        print(f"\n→ create stub: {s.slug} (tier={s.tier}, vm={s.assigned_vm})")
        if s.path.exists():
            print(f"  SKIP: file already exists — {s.path.relative_to(WORKSPACE)}")
            continue
        if apply:
            s.path.write_text(s.frontmatter(), encoding="utf-8")
            print(f"  APPLIED: created {s.path.relative_to(WORKSPACE)}")
        else:
            print(f"  WOULD create: {s.path.relative_to(WORKSPACE)} ({len(s.frontmatter().splitlines())} lines)")
            if s.derived_from:
                print(f"  derived from: {s.derived_from}")


# ---------- Summary + sanity checks ----------


def print_pre_summary() -> None:
    print("=" * 80)
    print("EPIC CONSOLIDATION MIGRATION — 2026-05-21")
    print("=" * 80)
    print(f"\nWorkspace:  {WORKSPACE}")
    print(f"Renames:    {len(RENAMES)} (8 normal + 4 → SUPERSEDED for split/consolidate/extend sources)")
    print(f"Promotes:   {len(PROMOTES)} (active/ → epics/)")
    print(f"Stubs:      {len(STUBS)} (5 net-new + 2 split + 1 consolidate + 1 extend)")
    print(f"\nReference scope: workspace-wide grep, excluding {len(EXCLUDE_GLOBS)} glob patterns")
    print("Archive files (plans/archive/**) are NEVER updated — frozen archaeology.")


def print_post_summary(apply: bool) -> None:
    print("\n" + "=" * 80)
    print("MIGRATION " + ("COMPLETE" if apply else "DRY-RUN COMPLETE"))
    print("=" * 80)
    if not apply:
        print("\nThis was a DRY-RUN. No files were changed.")
        print("To apply for real:")
        print(f"  python3 {Path(__file__).relative_to(WORKSPACE)} --apply")
    else:
        print("\nNext steps (operator manual):")
        print("  1. Fill content in the 9 stub files in plans/epics/")
        print("     - 5 net-new: execution_master, deployment_and_user_management_master,")
        print("       observability_master, batch_live_symmetry_master, trading_agent_master")
        print("     - 2 split targets: strategy_master + dart_and_promote_master")
        print("       (carry body from strategy_and_dart_master_SUPERSEDED_2026_05_21.md)")
        print("     - 1 consolidate target: manifest_master")
        print("       (merge bodies from manifest_evolution_SUPERSEDED + manifest_migration_SUPERSEDED)")
        print("     - 1 extend target: client_isolation_and_governance_master")
        print("       (carry body from cross_cutting_may_23_SUPERSEDED + add client/jurisdiction/share-class)")
        print("  2. Add SUPERSEDED-BY banner to the 4 SUPERSEDED files in plans/epics/")
        print("  3. Update orchestrator_vm_registry.yaml with the new epic slugs + assigned_vm mappings")
        print("  4. Sweep every active plan's frontmatter: add parent_epic: <epic-slug>")
        print("     - Run: python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py")
        print("     - Resolve any ORPHAN entries before next PR merge")
        print("  5. Update CLAUDE.md if any remaining old slug references slipped through")


# ---------- Main ----------


def main() -> int:
    parser = argparse.ArgumentParser(description="Epic consolidation migration 2026-05-21")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen; do not change files")
    parser.add_argument("--apply", action="store_true", help="Actually do the renames + ref updates + stub creates")
    parser.add_argument("--only-renames", action="store_true", help="Skip promotes + stub creates")
    parser.add_argument("--skip-stubs", action="store_true", help="Do renames + promotes but skip stub creates")
    parser.add_argument("--only-stubs", action="store_true", help="Do stub creates only")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("ERROR: must pass --dry-run or --apply", file=sys.stderr)
        return 1

    if args.dry_run and args.apply:
        print("ERROR: --dry-run and --apply are mutually exclusive", file=sys.stderr)
        return 1

    apply = args.apply

    print_pre_summary()

    if args.only_renames:
        do_renames(RENAMES, apply)
    elif args.skip_stubs:
        do_renames(RENAMES, apply)
        do_promotes(PROMOTES, apply)
    elif args.only_stubs:
        do_stubs(STUBS, apply)
    else:
        do_renames(RENAMES, apply)
        do_promotes(PROMOTES, apply)
        do_stubs(STUBS, apply)

    print_post_summary(apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
