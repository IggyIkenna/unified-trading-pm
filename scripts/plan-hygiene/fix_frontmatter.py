#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""
Fix plan frontmatter for unified-trading-pm.

Changes made (frontmatter block only — body is NEVER touched):
  - Unjam frontmatter: ---key: val → ---\nkey: val on first line
  - Remove deprecated fields (and their multiline continuations)
  - Add missing: title (from first # heading), status, locked_by, locked_since
  - Add missing parent_epic (from slug-prefix mapping)
  - Add missing priority (from context or default P2)

Usage:
  python3 scripts/plan-hygiene/fix_frontmatter.py [--dry-run]
"""

import pathlib
import re
import sys

DRY_RUN = "--dry-run" in sys.argv

PM_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
ACTIVE_DIR = PM_DIR / "plans" / "active"
EPICS_DIR = PM_DIR / "plans" / "epics"

DEPRECATED_PLAN_FIELDS = {
    "slug",
    "deadline",
    "owner",
    "horizon",
    "operator",
    "companion_to",
    "companion_plans",
    "spawned_from",
    "parent_plan",
    "related_codex",
    "overview",
    "date",
    "type",
    "author",
    "plan_type",
}

DEPRECATED_EPIC_FIELDS = {"owner"}

SKIP_ACTIVE = {"INDEX.md", "task_template.md"}

# Map filename prefix → parent_epic slug
EPIC_MAPPING = {
    "alerting": "observability_master",
    "api_keys_wallets": "defi_master",
    "available_at": "manifest_master",
    "aws_migration": "infrastructure_master",
    "batch_live_symmetry": "batch_live_symmetry_master",
    "bucket_name_ssot": "infrastructure_master",
    "canary_coverage": "observability_master",
    "code_freeze_migrate": "infrastructure_master",
    "codex_vs_citadel": "orchestrator_master",
    "compute_optimization": "infrastructure_master",
    "config_grid_archetype": "strategy_master",
    "cross_cutting_may_23": "orchestrator_master",
    "d1_is_hardening": "instruments_master",
    "d2_uac_continuity": "manifest_master",
    "d3_manifest_v8": "manifest_master",
    "d4_mtds_adapters": "mtds_mdps_master",
    "d5_features_missing": "features_and_ml_master",
    "d8_perf_upgrade": "features_and_ml_master",
    "data_pipeline_master": "manifest_master",
    "defi_archetypes": "defi_master",
    "defi_catalogue": "defi_master",
    "defi_protocol_outage": "defi_master",
    "defi_recursive_borrow": "defi_master",
    "deployment_ui_lifecycle": "deployment_and_user_management_master",
    "dex_perp": "defi_master",
    "expected_unattempted": "manifest_master",
    "expected_universe": "manifest_master",
    "features_repo_consolidation": "features_and_ml_master",
    "features_service_qg": "features_and_ml_master",
    "features_tick_observation": "features_and_ml_master",
    "gate_3_phantom": "manifest_master",
    "gcs_migration_bundle": "infrastructure_master",
    "global_ledger_pnl": "global_ledger_pnl_attribution_master",
    "hard_schema": "manifest_master",
    "hedge_ratio": "defi_master",
    "honest_coverage": "manifest_master",
    "human_work_backlog": "orchestrator_master",
    "live_pipeline_mtds_mdps": "mtds_mdps_master",
    "manifest_cross_asset": "manifest_master",
    "manifest_schema": "manifest_master",
    "master_to_live_defi": "orchestrator_master",
    "mdps_streaming": "mtds_mdps_master",
    "missing_question_docs": "orchestrator_master",
    "ml_repo_consolidation": "features_and_ml_master",
    "mtds_databento": "mtds_mdps_master",
    "mtds_per_instrument": "mtds_mdps_master",
    "orchestrator": "orchestrator_master",
    "per_agent_worktrees": "infrastructure_master",
    "phase5_features": "features_and_ml_master",
    "plan_hygiene": "plan_hygiene_master",
    "post_freeze_roadmap": "orchestrator_master",
    "promote_workflow": "dart_and_promote_master",
    "ruff_workspace": "infrastructure_master",
    "scratch_codefreeze": "infrastructure_master",
    "simulation_scenarios": "strategy_master",
    "strategy_archetype": "strategy_master",
    "strategy_execution_contract": "execution_master",
    "strategy_repo_consolidation": "strategy_master",
    "tradfi": "tradfi_master",
    "trigger_based_reference": "instruments_master",
    "uac_source_capability": "manifest_master",
    "venue_heartbeat": "cefi_master",
    "wave3x": "manifest_master",
    "work_split": "orchestrator_master",
    "writegate": "mtds_mdps_master",
}

# Plans with known priority (for files missing priority field entirely)
KNOWN_PRIORITY = {
    "master_to_live_defi_2026_05_23.md": "P0",
    "writegate_honest_coverage_endtoend_2026_05_06.md": "P0",
    "alerting_service_live_rules_2026_05_07.md": "P0",
    "defi_catalogue_chain_primitives_2026_05_10.md": "P0",
    "live_pipeline_mtds_mdps_features_2026_05_08.md": "P1",
    "batch_live_symmetry_2026_05_10.md": "P0",
    "api_keys_wallets_accounts_readiness_2026_05_10.md": "P0",
    "code_freeze_migrate_backfill_sequencing_2026_05_10.md": "P0",
    "promote_workflow_may23_cli_path_2026_05_10.md": "P1",
    "promote_workflow_post_cutover_ui_pipeline_2026_05_10.md": "P2",
    "features_repo_consolidation_2026_05_08.md": "P1",
    "strategy_repo_consolidation_2026_05_19.md": "P1",
    "ml_repo_consolidation_2026_05_19.md": "P1",
    "human_work_backlog_2026_05_20.md": "P1",
    "work_split_2026_05_19_harsh.md": "P1",
    "work_split_2026_05_20_ikenna.md": "P1",
    "plan_hygiene_sweep_kickoff_2026_05_21.md": "P1",
    "simulation_scenarios_topology_price_shocks_2026_05_09.md": "P2",
    "simulation_scenarios_post_cutover_2026_06_01.md": "P2",
    "defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md": "P1",
    "defi_recursive_borrow_archetypes_2026_05_10.md": "P1",
    "defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md": "P2",
    "bucket_name_ssot_canonicalisation_2026_05_10.md": "P0",
}

# Estimate defaults for plans genuinely missing them
KNOWN_ESTIMATES = {
    "human_work_backlog_2026_05_20.md": ("infra", 0.5, 0.4),
    "live_pipeline_mtds_mdps_features_2026_05_08.md": ("infra", 12.0, 9.6),
    "work_split_2026_05_20_ikenna.md": ("infra", 0.5, 0.4),
}


def get_h1_title(body_lines):
    """Extract title from first # heading in body."""
    for line in body_lines:
        m = re.match(r"^# (.+)", line.rstrip())
        if m:
            title = m.group(1).strip().strip("\"'")
            return title
    return None


def get_epic_for_file(filename):
    """Map filename to parent_epic slug using prefix matching."""
    stem = filename.replace(".md", "")
    for prefix, epic in EPIC_MAPPING.items():
        if stem.startswith(prefix):
            return epic
    return None


def is_continuation_line(line):
    """A line is a continuation of a multiline value if it starts with whitespace."""
    return line and (line[0] in (" ", "\t"))


def parse_frontmatter_blocks(text, filepath):
    """
    Returns (is_jammed, opening_extra, fm_lines, body_text) or None.
    - is_jammed: True if line 1 was ---key: val
    - opening_extra: the "key: val" part stripped from the jammed opening (or "")
    - fm_lines: lines between the two --- delimiters
    - body_text: everything after the closing ---\n
    """
    lines = text.splitlines(keepends=True)
    if not lines:
        return None

    first = lines[0].rstrip("\n").rstrip("\r")

    is_jammed = False
    opening_extra = ""

    if first == "---":
        start_idx = 1
    elif first.startswith("---"):
        is_jammed = True
        opening_extra = first[3:]  # e.g. "title: foo" or "type: plan"
        start_idx = 1
    else:
        return None

    # Find closing ---
    fm_end_idx = None
    for i in range(start_idx, len(lines)):
        stripped = lines[i].rstrip("\n").rstrip("\r")
        if stripped == "---":
            fm_end_idx = i
            break

    if fm_end_idx is None:
        return None

    fm_lines = lines[start_idx:fm_end_idx]
    body_text = "".join(lines[fm_end_idx + 1 :])

    return is_jammed, opening_extra, fm_lines, body_text


def has_field(fm_lines, field):
    return any(re.match(rf"^{re.escape(field)}:", ln) for ln in fm_lines)


def remove_deprecated_fields(fm_lines, deprecated_set):
    """Remove deprecated fields and their multiline continuations."""
    result = []
    skip_continuations = False

    for line in fm_lines:
        stripped = line.rstrip("\n").rstrip("\r")

        if is_continuation_line(stripped) and skip_continuations:
            continue

        m = re.match(r"^([\w][\w-]*):", line)
        if m:
            field = m.group(1)
            if field in deprecated_set:
                skip_continuations = True
                continue
            else:
                skip_continuations = False

        result.append(line)

    return result


def fix_active_plan(fp):
    text = fp.read_text()
    result = parse_frontmatter_blocks(text, fp)
    if result is None:
        print(f"  SKIP {fp.name}: no frontmatter block detected")
        return False

    is_jammed, opening_extra, fm_lines, body_text = result
    changes = []

    # Build initial fm_lines: prepend the jammed opening field if present
    new_fm = list(fm_lines)
    if is_jammed and opening_extra.strip():
        field_line = opening_extra.strip()
        if not field_line.endswith("\n"):
            field_line += "\n"
        new_fm.insert(0, field_line)
        changes.append("unjammed")

    # Remove deprecated fields
    before = list(new_fm)
    new_fm = remove_deprecated_fields(new_fm, DEPRECATED_PLAN_FIELDS)
    if new_fm != before:
        changes.append("removed deprecated")

    # Add title from H1 heading if missing
    if not has_field(new_fm, "title"):
        body_lines = body_text.splitlines(keepends=True)
        title = get_h1_title(body_lines)
        if title:
            new_fm.insert(0, f'title: "{title}"\n')
            changes.append("added title")

    # Add parent_epic if missing
    if not has_field(new_fm, "parent_epic"):
        epic = get_epic_for_file(fp.name)
        if epic:
            new_fm.append(f"parent_epic: {epic}\n")
            changes.append(f"added parent_epic={epic}")

    # Add priority if missing
    if not has_field(new_fm, "priority"):
        priority = KNOWN_PRIORITY.get(fp.name, "P2")
        new_fm.append(f"priority: {priority}\n")
        changes.append(f"added priority={priority}")

    # Add status if missing
    if not has_field(new_fm, "status"):
        new_fm.append("status: active\n")
        changes.append("added status")

    # Add locked_by + locked_since if missing
    if not has_field(new_fm, "locked_by"):
        new_fm.append("locked_by: live-defi-rollout\n")
        new_fm.append("locked_since: 2026-05-21\n")
        changes.append("added locked_by")

    # Add estimate fields if in known list
    if fp.name in KNOWN_ESTIMATES and not has_field(new_fm, "estimate_class"):
        cls, baseline, calibrated = KNOWN_ESTIMATES[fp.name]
        new_fm.append(f"estimate_class: {cls}\n")
        new_fm.append(f"estimate_baseline_ai_days: {baseline}\n")
        new_fm.append(f"estimate_calibrated_ai_days: {calibrated}\n")
        changes.append("added estimates")

    if not changes:
        return False

    new_text = "---\n" + "".join(new_fm) + "---\n" + body_text
    if new_text == text:
        return False

    if DRY_RUN:
        print(f"  DRY-RUN {fp.name}: {', '.join(changes)}")
        return True

    fp.write_text(new_text)
    print(f"  FIXED {fp.name}: {', '.join(changes)}")
    return True


def fix_epic(fp):
    text = fp.read_text()
    result = parse_frontmatter_blocks(text, fp)
    if result is None:
        print(f"  SKIP {fp.name}: no frontmatter block detected")
        return False

    is_jammed, opening_extra, fm_lines, body_text = result
    changes = []

    new_fm = list(fm_lines)
    if is_jammed and opening_extra.strip():
        new_fm.insert(0, opening_extra.strip() + "\n")
        changes.append("unjammed")

    before = list(new_fm)
    new_fm = remove_deprecated_fields(new_fm, DEPRECATED_EPIC_FIELDS)
    if new_fm != before:
        changes.append("removed deprecated")

    # Add title from H1 heading if missing
    if not has_field(new_fm, "title"):
        body_lines = body_text.splitlines(keepends=True)
        title = get_h1_title(body_lines)
        if title:
            # Insert after name: if present
            insert_idx = 1
            for i, line in enumerate(new_fm):
                if re.match(r"^name:", line):
                    insert_idx = i + 1
                    break
            new_fm.insert(insert_idx, f'title: "{title}"\n')
            changes.append("added title")

    if not changes:
        return False

    new_text = "---\n" + "".join(new_fm) + "---\n" + body_text
    if new_text == text:
        return False

    if DRY_RUN:
        print(f"  DRY-RUN epic {fp.name}: {', '.join(changes)}")
        return True

    fp.write_text(new_text)
    print(f"  FIXED epic {fp.name}: {', '.join(changes)}")
    return True


def main():
    print("=== fix_frontmatter.py ===")
    if DRY_RUN:
        print("  (dry-run mode — no files written)")

    plan_fixed = 0
    print("\n--- Active plans ---")
    for fp in sorted(ACTIVE_DIR.glob("*.md")):
        name = fp.name
        if name in SKIP_ACTIVE:
            continue
        if name.startswith("_"):
            continue
        if name.endswith(".HANDOVER.md"):
            continue
        if fix_active_plan(fp):
            plan_fixed += 1

    # Also fix plans in issues/ subdir
    issues_dir = ACTIVE_DIR / "issues"
    if issues_dir.exists():
        for fp in sorted(issues_dir.glob("*.md")):
            if fix_active_plan(fp):
                plan_fixed += 1

    epic_fixed = 0
    print("\n--- Epics ---")
    for fp in sorted(EPICS_DIR.glob("*.md")):
        name = fp.name
        if "SUPERSEDED" in name:
            continue
        if name == "README.md":
            continue
        if fix_epic(fp):
            epic_fixed += 1

    print(f"\nDone: {plan_fixed} plans fixed, {epic_fixed} epics fixed")


if __name__ == "__main__":
    main()
