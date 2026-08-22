#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Fix plan frontmatter for unified-trading-pm.

Changes made (frontmatter block only — body is NEVER touched):
  - Unjam frontmatter: ---key: val → ---\nkey: val on first line
  - Remove deprecated fields (and their multiline continuations)
  - Add/fix: doc_type, title, summary, status, nature, asset_group, stage, repos,
    scope, tags, related, created, parent_epic, assigned_vm (validate only),
    execution_scope, priority, estimate_class, estimate_baseline_ai_days,
    estimate_calibrated_ai_days, assigned_role, drift_direction, depends_on, last_updated

Usage:
  python3 scripts/plan-hygiene/fix_frontmatter.py [--dry-run] [--dir <dir>] [file ...]

  # Process all *.md files in a directory:
  python3 scripts/plan-hygiene/fix_frontmatter.py --dir plans/active/

  # Process specific files:
  python3 scripts/plan-hygiene/fix_frontmatter.py plans/active/my_plan_2026_06_27.md
"""

import importlib.util
import pathlib
import re
import sys
from typing import cast

import yaml

DRY_RUN = "--dry-run" in sys.argv

PM_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
ACTIVE_DIR = PM_DIR / "plans" / "active"
EPICS_DIR = PM_DIR / "plans" / "epics"

TODAY = "2026-06-27"

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

# Fields worker.md § 4.5 "FINDINGS CLOSURE" (HARD RULE 2026-06-10) requires on every doc_type: issue doc. `author` is a
# legitimate DEPRECATED_PLAN_FIELDS entry for doc_type: plan (PLAN_FORMAT.md's schema has no
# `author` field), but the same name collides with a hard-required issue-doc field — confirmed live
# regression, fix_frontmatter_strips_required_author_field_from_issue_docs_2026_08_04.md. Subtracted
# from the deprecated set for issue docs (see fix_active_plan()) so this collision class can't recur
# for any other field either.
ISSUE_REQUIRED_FIELDS = {"title", "created", "author", "source", "assigned_vm"}

SKIP_ACTIVE = {"INDEX.md", "task_template.md"}

# Valid assigned_vm values per PLAN_FORMAT.md
VALID_ASSIGNED_VM = {"planning", "NA"}


def _load_enum_sets() -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    """Load the nature/stage/scope enum vocabularies from docspec (the schema SSOT).

    Sourced live rather than hardcoded so this fixer can never drift from the checker that gates
    the corpus (``check_frontmatter_schema.py`` loads the same docspec). Degrades to empty sets if
    docspec cannot be imported — enum-normalisation then no-ops, never crashes the fixer.
    """
    try:
        spec = importlib.util.spec_from_file_location("docspec", PM_DIR / "scripts" / "docs" / "docspec.py")
        if spec is None or spec.loader is None:
            return frozenset(), frozenset(), frozenset()
        mod = importlib.util.module_from_spec(spec)
        sys.modules["docspec"] = mod  # docspec self-references; must be registered before exec
        spec.loader.exec_module(mod)
        # cast (not type:ignore): a dynamically-loaded module's attrs are Unknown to the type checker.
        return (
            cast("frozenset[str]", mod.NATURE),
            cast("frozenset[str]", mod.STAGE),
            cast("frozenset[str]", mod.SCOPE),
        )
    except Exception as exc:  # noqa: broad-except — any import failure must degrade to a no-op, never crash the fixer
        print(
            f"  WARN fix_frontmatter: could not load docspec enums ({exc}); skipping enum-normalisation",
            file=sys.stderr,
        )
        return frozenset(), frozenset(), frozenset()


_NATURE, _STAGE, _SCOPE = _load_enum_sets()

# Present-but-INVALID enum remapping (2026-07-21). Historically the fixer only ADDED missing fields;
# a field present with a value outside its docspec enum (an issue doc with nature: test-harness-gap,
# or stage: foundation) still red-lined the corpus gate for the WHOLE FLEET. Such values are
# PARSEABLE (valid YAML, wrong vocabulary), so the refuse-on-unparseable contract does not apply and
# they are safe to normalise. Conservative by design: nature is doc_type-derived (high confidence);
# stage/scope keep any already-valid elements, apply a small explicit alias, else fall back to a
# NEUTRAL catch-all — never a specific guess. Every remap is logged so it shows in the diff.
_DOC_TYPE_NATURE = {"issue": "issue", "plan": "process", "audit-result": "record", "runbook": "process"}
_STAGE_ALIAS = {"foundation": "data"}  # operator ruling 2026-07-20: foundation work == data layer here
_STAGE_DEFAULT = "meta"  # neutral "cross-cutting/unclassified", not a guess at a specific stage
_SCOPE_DEFAULT = ["engineer", "admin"]  # same safe default the missing-field path uses

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

# Keywords to derive asset_group from parent_epic. Values MUST be members of docspec.ASSET_GROUP
# (there is no "crypto" or "cross-asset" value in that enum — a prior version of this table used
# both and would seed a HARD-violating value on every doc that fell through to it).
ASSET_GROUP_KEYWORDS = {
    "defi": "defi",
    "cefi": "cefi",
    "tradfi": "tradfi",
    "equity": "tradfi",
    "sports": "sports",
    "prediction": "prediction",
    "cross_asset": "cross-cutting",
    "cross-asset": "cross-cutting",
    "all": "cross-cutting",
}


def get_h1_title(body_lines: list[str]) -> str | None:
    """Extract title from first # heading in body."""
    for line in body_lines:
        m = re.match(r"^# (.+)", line.rstrip())
        if m:
            title = m.group(1).strip().strip("\"'")
            return title
    return None


def get_first_paragraph_after_heading(body_text: str) -> str | None:
    """Extract first non-empty paragraph from body (after optional H1 heading)."""
    lines = body_text.splitlines()
    in_heading = True
    paragraph_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip H1 heading
        if in_heading and stripped.startswith("# "):
            in_heading = False
            continue
        in_heading = False

        if not stripped:
            if paragraph_lines:
                break
            continue

        # Skip headings beyond H1
        if stripped.startswith("#"):
            if paragraph_lines:
                break
            continue

        # Skip blockquotes, lists, code blocks as first paragraph
        if stripped.startswith(">") or stripped.startswith("-") or stripped.startswith("```"):
            if paragraph_lines:
                break
            continue

        paragraph_lines.append(stripped)

    if paragraph_lines:
        result = " ".join(paragraph_lines)
        # Truncate to reasonable length, respecting word/sentence/clause boundaries.
        if len(result) > 200:
            truncated = result[:197]
            # A boundary only counts as "good" if it uses at least half the budget —
            # otherwise the FIRST sentence-ending punctuation in a long paragraph (e.g.
            # at char 20) would win via rfind() finding no later match, discarding most
            # of the 197-char budget and producing a needlessly short, dangling summary.
            min_boundary_pos = len(truncated) // 2

            def _last_boundary(puncts: tuple[str, ...]) -> int:
                pos = -1
                for punct in puncts:
                    found = truncated.rfind(punct)
                    if found > pos:
                        pos = found
                return pos

            last_sentence = _last_boundary((". ", "! ", "? "))
            if last_sentence >= min_boundary_pos:
                result = truncated[: last_sentence + 1] + " ..."
            else:
                # No sentence boundary uses enough of the budget — try a clause
                # boundary (comma/semicolon/dash) before falling back further.
                last_clause = _last_boundary((", ", "; ", " - ", " — "))
                if last_clause >= min_boundary_pos:
                    result = truncated[:last_clause] + " ..."
                else:
                    # Last resort: cut at the last whole-word boundary — never mid-word
                    # unless the paragraph has no word boundary at all (one giant token).
                    last_space = truncated.rfind(" ")
                    result = truncated[:last_space] + " ..." if last_space > 0 else truncated + "..."
        return result
    return None


def derive_asset_group_from_epic(parent_epic: str) -> str:
    """Derive asset_group from parent_epic value."""
    epic_lower = parent_epic.lower()
    for keyword, group in ASSET_GROUP_KEYWORDS.items():
        if keyword in epic_lower:
            return group
    return "cross-cutting"


def _is_issue_path(fp: pathlib.Path) -> bool:
    """Path-derived doc_type check, mirroring docspec.doc_type_for_path's issue rule
    (2026-07-06 HARD rule: doc_type is path-derived and a contradicting declared value fails
    the schema gate) — a doc under plans/active/issues/ IS an issue, never a plan."""
    return "/plans/active/issues/" in str(fp.resolve()).replace("\\", "/")


def _is_audit_result_path(fp: pathlib.Path) -> bool:
    """Path-derived doc_type check — a doc under plans/audit/results/ or plans/audit/instructions/
    IS an audit-result/audit-instruction doc, never plan-shaped. This fixer has no audit-aware
    branch: `fix_active_plan()` unconditionally hints `doc_type_hint="plan"` for anything outside
    `_is_issue_path`, which strips `date` (DEPRECATED_PLAN_FIELDS, but `Req.R` on audit-result per
    docspec.py's FIELD_SPECS) and injects plan-only fields (execution_scope/priority/
    drift_direction/depends_on/locked_by — none of which exist in the audit-result/audit-instruction
    schema) — confirmed live corrupting `plans/audit/results/*.md` docs that quality-gates.sh's
    changeset-scoped fixer call picks up (`_fm_doc_trees` includes `plans/audit/results/*.md`)."""
    p = str(fp.resolve()).replace("\\", "/")
    return "/plans/audit/results/" in p or "/plans/audit/instructions/" in p


def derive_created_from_filename(filename: str) -> str | None:
    """Extract date from filename pattern *_YYYY_MM_DD.md."""
    stem = filename.replace(".md", "")
    # Match the last date-like suffix: _YYYY_MM_DD
    m = re.search(r"_(\d{4})_(\d{2})_(\d{2})$", stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def get_epic_for_file(filename: str) -> str | None:
    """Map filename to parent_epic slug using prefix matching."""
    stem = filename.replace(".md", "")
    for prefix, epic in EPIC_MAPPING.items():
        if stem.startswith(prefix):
            return epic
    return None


def is_continuation_line(line: str) -> bool:
    """A line is a continuation of a multiline value if it starts with whitespace."""
    return bool(line and (line[0] in (" ", "\t")))


def _clear_field_continuations(fm_lines: list[str], field: str) -> list[str]:
    """Drop ACCIDENTAL multiline-folded continuation lines attached to `field`'s own line.

    `last_updated`/`execution_scope` are meant to be single-line plain scalars, but YAML's
    plain-scalar folding silently absorbs any following indented lines into the SAME value —
    so a one-off stray manual edit (or an earlier bug) can leave dangling garbage attached
    that a plain emptiness check on the field's own line never detects once that line itself
    holds a real value. Left unstripped, each fixer run only ever patches the field's own
    line and never removes the stale continuation, so repeated runs accumulate a runaway
    string rather than converging (confirmed via live repro on
    plans/active/defi_consolidated_closeout_2026_07_18.md — a multi-date runaway value with
    embedded changelog prose folded into `last_updated:`; see
    plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md).
    Call this unconditionally (not just when the field looks empty) so a field whose own
    line already holds a real value still gets its stale continuation cleaned.

    Distinguishes that accidental-fold garbage from two DELIBERATE patterns:

    1. A quoted multiline scalar (e.g. `last_updated:\n  '2026-07-10 (was: 2026-06-27 -- ...)'`, a
       real annotation pattern already in this corpus —
       plans/active/issues/defi_code_codex_drift_2026_05_27.md,
       plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md): if the
       FIRST continuation line (after stripping leading whitespace) opens with a quote character,
       it's an intentional quoted scalar — leave it untouched.
    2. A real single-line value immediately followed by a `#`-prefixed explanatory comment, itself
       possibly wrapped across further indented comment-only lines (e.g.
       `execution_scope:\n  local-only # corrected 2026-08-02 (operator ruling on\n  # ...): was
       orchestrator-agent, contradicting assigned_vm: NA. Stays NA until ...`,
       plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md):
       if the FIRST continuation line has real (non-comment) content before an unquoted `#`, it's a
       value + trailing comment — leave the whole block untouched rather than deleting the value.
    """
    result: list[str] = []
    i = 0
    n = len(fm_lines)
    while i < n:
        ln = fm_lines[i]
        if re.match(rf"^{re.escape(field)}:", ln):
            result.append(ln)
            i += 1
            keep_continuation = False
            if i < n and is_continuation_line(fm_lines[i]):
                first_stripped = fm_lines[i].strip()
                if first_stripped[:1] in ("'", '"'):
                    keep_continuation = True
                elif "#" in first_stripped and not first_stripped.startswith("#"):
                    value_part = first_stripped.split("#", 1)[0].strip()
                    keep_continuation = bool(value_part)
            if keep_continuation:
                while i < n and is_continuation_line(fm_lines[i]):
                    result.append(fm_lines[i])
                    i += 1
            else:
                while i < n and is_continuation_line(fm_lines[i]):
                    i += 1
            continue
        result.append(ln)
        i += 1
    return result


def frontmatter_yaml_error(text: str) -> str | None:
    """Return a one-line YAML error if this doc's frontmatter does NOT parse, else None.

    Why this exists (2026-07-20): every parser in THIS file is line-based —
    ``parse_frontmatter_blocks`` just locates the ``---`` delimiters and treats the span
    between them as opaque lines. It therefore happily APPENDS fields to a doc whose YAML is
    already broken, which is actively harmful in two ways:

      1. The auto-fixer commits a change to a file that is still invalid, so the commit diff
         makes it look like the FIXER authored the breakage. (Measured: `44e1fb449` added three
         valid lines to `defi_available_at_clobbered_by_wallclock_2026_07_20.md`, whose
         `summary:` was ALREADY an unquoted multi-line plain scalar containing a colon-space —
         broken by the authoring commit `273f5a9d5`, not by the bot. A reader of the diff
         reasonably but WRONGLY blames the bot.)
      2. It MASKS the breakage. Appending the missing required fields makes a presence-only
         check pass while the YAML still does not parse — so the doc looks healthier while the
         real fault (a syntax error) survives and keeps failing the corpus-wide gate, blocking
         every slot's quality-gates run on the shared branch.

    A doc whose frontmatter cannot be parsed needs a HUMAN to fix the syntax; it must not be
    mechanically edited. Fail loudly, change nothing.
    """
    blocks = parse_frontmatter_blocks(text)
    if blocks is None:
        return None  # no frontmatter block at all — existing SKIP path already reports this
    _is_jammed, opening_extra, fm_lines, _body = blocks
    raw = ("".join(fm_lines)) if not opening_extra.strip() else (opening_extra + "\n" + "".join(fm_lines))
    try:
        yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return " ".join(str(exc).split())[:200]
    return None


# Docs this run REFUSED to touch because their frontmatter does not parse. Reported at exit and
# turned into a non-zero exit code, so an automated caller (plan-health-agent.yml runs
# `fix_frontmatter.py || true`) cannot silently commit a corpus that still contains a broken doc.
_REFUSED: list[tuple[pathlib.Path, str]] = []


def _record_refusal(fp: pathlib.Path, err: str) -> None:
    _REFUSED.append((fp, err))
    print(f"  REFUSE {fp.name}: frontmatter is not valid YAML — {err}", file=sys.stderr)
    print("         NOT modified. A human must fix the syntax; auto-appending fields to a", file=sys.stderr)
    print("         broken doc masks the error and misattributes it to this fixer.", file=sys.stderr)


def _assert_output_parses(fp: pathlib.Path, new_text: str) -> None:
    """Round-trip guard: whatever this fixer WRITES must itself parse as YAML.

    Validating the input is not enough — the fixer edits frontmatter line-by-line, so a bug in
    field insertion could emit invalid YAML from a valid input. This makes that failure mode
    impossible to commit: it raises before the write lands, and main() turns it into exit 2.
    """
    err = frontmatter_yaml_error(new_text)
    if err is not None:
        raise ValueError(
            f"auto-fix would have written INVALID YAML frontmatter to {fp.name} ({err}). "
            "Refusing to write. This is a bug in fix_frontmatter.py — the input parsed but the "
            "output did not."
        )


def parse_frontmatter_blocks(
    text: str,
) -> tuple[bool, str, list[str], str] | None:
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


def has_field(fm_lines: list[str], field: str) -> bool:
    return any(re.match(rf"^{re.escape(field)}:", ln) for ln in fm_lines)


def get_field_value(fm_lines: list[str], field: str) -> str | None:
    """Get the value of a field from frontmatter lines (first line only, not multiline)."""
    for ln in fm_lines:
        m = re.match(rf"^{re.escape(field)}:\s*(.*)", ln)
        if m:
            return m.group(1).strip()
    return None


def _enum_list_tokens(raw: str) -> list[str]:
    """Extract candidate tokens from a frontmatter value that may be ``[a, b]``, a bare scalar,
    or free text. Free text (no brackets) collapses to a single token that will match no enum —
    the desired behaviour (free-text scope has no recoverable member, so it falls to the default)."""
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [t.strip().strip("'\"") for t in raw[1:-1].split(",") if t.strip()]
    return [raw.strip("'\"")] if raw else []


def _replace_field_line(fm_lines: list[str], field: str, new_value: str) -> bool:
    for i, ln in enumerate(fm_lines):
        if re.match(rf"^{re.escape(field)}:", ln):
            fm_lines[i] = f"{field}: {new_value}\n"
            return True
    return False


def normalize_invalid_enums(new_fm: list[str], changes: list[str]) -> None:
    """Remap PRESENT-but-invalid nature/stage/scope values to valid docspec vocabulary (in-place).

    Valid values are never touched. See the _DOC_TYPE_NATURE / _STAGE_ALIAS constants for the
    (deliberately conservative) mapping policy.
    """
    if not (_NATURE and _STAGE and _SCOPE):  # docspec unavailable → no-op
        return

    # nature (single enum) — doc_type-derived, high confidence; unknown doc_type → leave for a human.
    nature = get_field_value(new_fm, "nature")
    if nature is not None and nature not in _NATURE:
        mapped = _DOC_TYPE_NATURE.get(get_field_value(new_fm, "doc_type") or "")
        if mapped and _replace_field_line(new_fm, "nature", mapped):
            changes.append(f"remapped invalid nature={nature!r} → {mapped}")

    # stage (enum_list) — keep valid elements; alias known-wrong tokens; else neutral default.
    stage_raw = get_field_value(new_fm, "stage")
    if stage_raw is not None:
        toks = _enum_list_tokens(stage_raw)
        valid = [t for t in toks if t in _STAGE]
        if not valid or len(valid) != len(toks):
            if not valid:
                valid = [_STAGE_ALIAS[t] for t in toks if t in _STAGE_ALIAS] or [_STAGE_DEFAULT]
            new_val = "[" + ", ".join(dict.fromkeys(valid)) + "]"
            if new_val != stage_raw and _replace_field_line(new_fm, "stage", new_val):
                changes.append(f"remapped invalid stage={stage_raw!r} → {new_val}")

    # scope (enum_list) — keep valid elements; free-text/invalid → neutral default.
    scope_raw = get_field_value(new_fm, "scope")
    if scope_raw is not None:
        toks = _enum_list_tokens(scope_raw)
        valid = [t for t in toks if t in _SCOPE]
        if not valid or len(valid) != len(toks):
            new_val = "[" + ", ".join(dict.fromkeys(valid or _SCOPE_DEFAULT)) + "]"
            if new_val != scope_raw and _replace_field_line(new_fm, "scope", new_val):
                changes.append(f"remapped invalid scope={scope_raw!r} → {new_val}")


def remove_deprecated_fields(fm_lines: list[str], deprecated_set: set[str]) -> list[str]:
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


def is_field_empty(fm_lines: list[str], field: str) -> bool:
    """Check if a field exists but has an empty or blank value (not a meaningful value).

    A field whose own line is bare (`field:` with nothing after the colon) is NOT
    automatically empty — its value may live on a preserved continuation line instead
    (a quoted multiline scalar, or a value+trailing-`#`-comment block that
    `_clear_field_continuations()` already decided to keep). Callers run this AFTER
    `_clear_field_continuations()`, so by construction any continuation line still present
    survived that guard and carries a deliberate value — treating the field as "empty" here
    would overwrite the bare own-line with a default while leaving the real value dangling
    underneath as orphaned YAML-fold garbage on the very next parse (the exact runaway-string
    bug class `_clear_field_continuations()` exists to prevent), silently re-corrupting a
    just-repaired field on this same fixer run.
    """
    for i, ln in enumerate(fm_lines):
        m = re.match(rf"^{re.escape(field)}:\s*(.*)", ln)
        if m:
            val = m.group(1).strip()
            if val:
                return False
            next_ln = fm_lines[i + 1] if i + 1 < len(fm_lines) else ""
            return not is_continuation_line(next_ln)
    return False


def _apply_field_defaults(  # noqa: C901
    new_fm: list[str],
    body_text: str,
    filename: str,
    changes: list[str],
    doc_type_hint: str = "plan",
) -> None:
    """Populate missing/empty plan frontmatter fields with safe defaults (in-place).

    `doc_type_hint` is the PATH-derived doc_type (see `_is_issue_path`) — used only when the
    `doc_type` field itself is absent, so a doc under plans/active/issues/ seeds `doc_type: issue`
    (+ the issue-shaped status/nature default below) instead of unconditionally `plan`, which
    previously produced a doc_type declared-vs-path contradiction that the schema gate hard-fails
    on (fix_frontmatter_issue_doc_seeded_as_plan_2026_08_19).
    """
    # 1. doc_type
    if not has_field(new_fm, "doc_type"):
        new_fm.insert(0, f"doc_type: {doc_type_hint}\n")
        changes.append(f"added doc_type={doc_type_hint}")

    # 2. title (from H1 heading)
    if not has_field(new_fm, "title"):
        body_lines = body_text.splitlines(keepends=True)
        title = get_h1_title(body_lines)
        if title:
            insert_idx = 0
            for i, line in enumerate(new_fm):
                if re.match(r"^doc_type:", line):
                    insert_idx = i + 1
                    break
            new_fm.insert(insert_idx, f'title: "{title}"\n')
            changes.append("added title")

    # 3. summary (derive from first body paragraph if field is absent)
    if not has_field(new_fm, "summary"):
        summary = get_first_paragraph_after_heading(body_text)
        if not summary:
            raw = get_field_value(new_fm, "title") or ""
            summary = raw.strip("\"'") if raw else ""
        if summary:
            # Must be quoted — extracted text can contain YAML-special chars (* : | etc.)
            quoted = summary.replace("\\", "\\\\").replace('"', '\\"')
            new_fm.append(f'summary: "{quoted}"\n')
            changes.append("added summary")
    # If field exists but empty, leave it — intentional gap

    # 4. status — issue docs use `open`, never `active` (operator 2026-06-24; STATUS_BY_TYPE has no
    # "active" member for doc_type: issue at all).
    if not has_field(new_fm, "status"):
        default_status = "open" if doc_type_hint == "issue" else "active"
        new_fm.append(f"status: {default_status}\n")
        changes.append(f"added status={default_status}")

    # 5. nature — issue docs default to the `issue` nature value, not `process`.
    if not has_field(new_fm, "nature"):
        default_nature = "issue" if doc_type_hint == "issue" else "process"
        new_fm.append(f"nature: {default_nature}\n")
        changes.append(f"added nature={default_nature}")

    # 6. asset_group (derive from parent_epic keywords; always a bracketed enum_list, never a bare
    # scalar — asset_group's FieldSpec kind is enum_list)
    if not has_field(new_fm, "asset_group"):
        parent_epic = get_field_value(new_fm, "parent_epic") or ""
        asset_group = derive_asset_group_from_epic(parent_epic) if parent_epic else "cross-cutting"
        new_fm.append(f"asset_group: [{asset_group}]\n")
        changes.append(f"added asset_group=[{asset_group}]")

    # 7. stage
    if not has_field(new_fm, "stage"):
        new_fm.append("stage: [meta]\n")
        changes.append("added stage=[meta]")

    # 8. repos
    if not has_field(new_fm, "repos"):
        new_fm.append("repos: []\n")
        changes.append("added repos=[]")

    # 9. scope
    if not has_field(new_fm, "scope"):
        new_fm.append("scope: [engineer, admin]\n")
        changes.append("added scope=[engineer, admin]")

    # 10. tags
    if not has_field(new_fm, "tags"):
        new_fm.append("tags: []\n")
        changes.append("added tags=[]")

    # 11. related
    if not has_field(new_fm, "related"):
        new_fm.append("related: []\n")
        changes.append("added related=[]")

    # 12. created (derive from filename date suffix if field is absent)
    if not has_field(new_fm, "created"):
        created_date = derive_created_from_filename(filename)
        if created_date:
            new_fm.append(f"created: {created_date}\n")
            changes.append(f"added created={created_date}")

    # 13. parent_epic (prefix mapping; preserve if present)
    if not has_field(new_fm, "parent_epic"):
        epic = get_epic_for_file(filename)
        if epic:
            new_fm.append(f"parent_epic: {epic}\n")
            changes.append(f"added parent_epic={epic}")

    # 14. assigned_vm (validate only; don't fabricate)
    if has_field(new_fm, "assigned_vm"):
        val = get_field_value(new_fm, "assigned_vm") or ""
        if val and val not in VALID_ASSIGNED_VM:
            print(f"  WARN {filename}: assigned_vm={val!r} is not in {VALID_ASSIGNED_VM} - leaving as-is")

    # 15. execution_scope — derive the default FROM assigned_vm (assigned_vm: NA means "not
    # dispatched", so its default must be local-only, never orchestrator-agent; blindly
    # defaulting to orchestrator-agent regardless of assigned_vm previously produced the exact
    # NA + orchestrator-agent contradiction manually corrected once already, see
    # plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md
    # referenced in _clear_field_continuations's docstring above).
    assigned_vm_val = get_field_value(new_fm, "assigned_vm") or ""
    default_execution_scope = "local-only" if assigned_vm_val == "NA" else "orchestrator-agent"
    cleaned = _clear_field_continuations(new_fm, "execution_scope")
    if cleaned != new_fm:
        new_fm[:] = cleaned
        changes.append("stripped stray execution_scope continuation lines")
    if not has_field(new_fm, "execution_scope"):
        new_fm.append(f"execution_scope: {default_execution_scope}\n")
        changes.append(f"added execution_scope={default_execution_scope}")
    elif is_field_empty(new_fm, "execution_scope"):
        new_fm[:] = [
            re.sub(r"^execution_scope:\s*$", f"execution_scope: {default_execution_scope}\n", ln)
            if re.match(r"^execution_scope:\s*$", ln)
            else ln
            for ln in new_fm
        ]
        changes.append(f"set execution_scope={default_execution_scope}")

    # 16. priority
    if not has_field(new_fm, "priority"):
        priority = KNOWN_PRIORITY.get(filename, "P2")
        new_fm.append(f"priority: {priority}\n")
        changes.append(f"added priority={priority}")

    # 17-21. estimate fields (only for known plans)
    if filename in KNOWN_ESTIMATES and not has_field(new_fm, "estimate_class"):
        cls, baseline, calibrated = KNOWN_ESTIMATES[filename]
        new_fm.append(f"estimate_class: {cls}\n")
        new_fm.append(f"estimate_baseline_ai_days: {baseline}\n")
        new_fm.append(f"estimate_calibrated_ai_days: {calibrated}\n")
        changes.append("added estimates")

    # 22. assigned_role: preserve existing (no safe default)

    # 23. drift_direction
    if not has_field(new_fm, "drift_direction"):
        new_fm.append("drift_direction: advance-code\n")
        changes.append("added drift_direction=advance-code")

    # Optional: depends_on
    if not has_field(new_fm, "depends_on"):
        new_fm.append("depends_on: []\n")
        changes.append("added depends_on=[]")

    # Optional: last_updated (only for active plans)
    status_val = get_field_value(new_fm, "status") or ""
    if status_val == "active":
        cleaned = _clear_field_continuations(new_fm, "last_updated")
        if cleaned != new_fm:
            new_fm[:] = cleaned
            changes.append("stripped stray last_updated continuation lines")
        if not has_field(new_fm, "last_updated"):
            new_fm.append(f"last_updated: {TODAY}\n")
            changes.append(f"added last_updated={TODAY}")
        elif is_field_empty(new_fm, "last_updated"):
            new_fm[:] = [
                re.sub(r"^last_updated:\s*$", f"last_updated: {TODAY}\n", ln)
                if re.match(r"^last_updated:\s*$", ln)
                else ln
                for ln in new_fm
            ]
            changes.append(f"set last_updated={TODAY}")

    # locked_by + locked_since: present-but-empty placeholders, matching every other optional
    # key in this function (supersedes/superseded_by, etc.) — a doc with no genuine lock claim
    # must not get one fabricated. The prior hardcoded "live-defi-rollout" / "2026-05-21" values
    # were bogus on any doc they touched (a branch name is not a lock-holder identity, and the
    # date predates most docs entirely) — real bug, not a stand-in worth preserving. Found live
    # 2026-08-03 stamping garbage onto a freshly-authored plan.
    if not has_field(new_fm, "locked_by"):
        new_fm.append("locked_by:\n")
        new_fm.append("locked_since:\n")
        changes.append("added empty locked_by/locked_since")

    # Present-but-invalid enum remapping (runs last, over the fully-populated frontmatter).
    normalize_invalid_enums(new_fm, changes)


def fix_active_plan(fp: pathlib.Path) -> bool:
    text = fp.read_text()
    result = parse_frontmatter_blocks(text)
    if result is None:
        print(f"  SKIP {fp.name}: no frontmatter block detected")
        return False

    if _is_audit_result_path(fp):
        print(f"  SKIP {fp.name}: audit-result doc — no audit-aware defaults; fix by hand per docspec.py")
        return False

    # REFUSE-ON-UNPARSEABLE (2026-07-20): never mechanically edit a doc whose YAML is already
    # broken — appending fields to it masks the real syntax error and misattributes it to the
    # fixer. See frontmatter_yaml_error() for the measured case.
    yaml_err = frontmatter_yaml_error(text)
    if yaml_err is not None:
        _record_refusal(fp, yaml_err)
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

    # Remove deprecated fields — never strip a field THIS doc's own doc_type requires (e.g.
    # `author` is deprecated for doc_type: plan but REQUIRED on doc_type: issue).
    # Falls back to the PATH-derived doc_type when the field itself is absent (the common case for
    # a freshly-auto-filed issue doc) — a doc under plans/active/issues/ IS an issue regardless of
    # whether it declares the field yet.
    path_doc_type = "issue" if _is_issue_path(fp) else "plan"
    doc_type_val = get_field_value(new_fm, "doc_type") or path_doc_type
    deprecated_set = DEPRECATED_PLAN_FIELDS
    if doc_type_val == "issue":
        deprecated_set = DEPRECATED_PLAN_FIELDS - ISSUE_REQUIRED_FIELDS
    before = list(new_fm)
    new_fm = remove_deprecated_fields(new_fm, deprecated_set)
    if new_fm != before:
        changes.append("removed deprecated")

    # Apply all field defaults (extracted to keep fix_active_plan under complexity limit)
    _apply_field_defaults(new_fm, body_text, fp.name, changes, doc_type_hint=path_doc_type)

    if not changes:
        return False

    new_text = "---\n" + "".join(new_fm) + "---\n" + body_text
    if new_text == text:
        return False

    _assert_output_parses(fp, new_text)

    if DRY_RUN:
        print(f"  DRY-RUN {fp.name}: {', '.join(changes)}")
        return True

    fp.write_text(new_text)
    print(f"  FIXED {fp.name}: {', '.join(changes)}")
    return True


def fix_epic(fp: pathlib.Path) -> bool:
    text = fp.read_text()
    result = parse_frontmatter_blocks(text)
    if result is None:
        print(f"  SKIP {fp.name}: no frontmatter block detected")
        return False

    # REFUSE-ON-UNPARSEABLE — same contract as fix_active_plan().
    yaml_err = frontmatter_yaml_error(text)
    if yaml_err is not None:
        _record_refusal(fp, yaml_err)
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

    _assert_output_parses(fp, new_text)

    if DRY_RUN:
        print(f"  DRY-RUN epic {fp.name}: {', '.join(changes)}")
        return True

    fp.write_text(new_text)
    print(f"  FIXED epic {fp.name}: {', '.join(changes)}")
    return True


def collect_target_files(args: list[str]) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    """
    Parse CLI args to determine which files to process.
    Returns (plan_files, epic_files).
    When --dir is given, process all *.md in that dir.
    When positional args are given, process those files only.
    When neither is given, fall back to default (active + epics).
    """
    plan_files: list[pathlib.Path] = []
    epic_files: list[pathlib.Path] = []

    # Strip known flags
    filtered = [a for a in args if a not in ("--dry-run",)]

    dir_idx = None
    for i, a in enumerate(filtered):
        if a == "--dir":
            dir_idx = i
            break

    if dir_idx is not None:
        if dir_idx + 1 >= len(filtered):
            print("ERROR: --dir requires a directory argument", file=sys.stderr)
            sys.exit(1)
        target_dir = pathlib.Path(filtered[dir_idx + 1]).resolve()
        if not target_dir.is_dir():
            print(f"ERROR: --dir path is not a directory: {target_dir}", file=sys.stderr)
            sys.exit(1)
        for fp in sorted(target_dir.glob("*.md")):
            name = fp.name
            if name in SKIP_ACTIVE or name.startswith("_") or name.endswith(".HANDOVER.md"):
                continue
            plan_files.append(fp)
        return plan_files, epic_files

    # Positional file arguments (excluding flags and --dir value)
    positional = []
    skip_next = False
    for a in filtered:
        if skip_next:
            skip_next = False
            continue
        if a == "--dir":
            skip_next = True
            continue
        if not a.startswith("-"):
            positional.append(a)

    if positional:
        for path_str in positional:
            fp = pathlib.Path(path_str).resolve()
            if not fp.exists():
                print(f"ERROR: file not found: {fp}", file=sys.stderr)
                sys.exit(1)
            plan_files.append(fp)
        return plan_files, epic_files

    # Default: process all active plans + epics
    for fp in sorted(ACTIVE_DIR.glob("*.md")):
        name = fp.name
        if name in SKIP_ACTIVE or name.startswith("_") or name.endswith(".HANDOVER.md"):
            continue
        plan_files.append(fp)

    issues_dir = ACTIVE_DIR / "issues"
    if issues_dir.exists():
        for fp in sorted(issues_dir.glob("*.md")):
            plan_files.append(fp)

    for fp in sorted(EPICS_DIR.glob("*.md")):
        name = fp.name
        if "SUPERSEDED" in name or name == "README.md":
            continue
        epic_files.append(fp)

    return plan_files, epic_files


def main() -> None:
    print("=== fix_frontmatter.py ===")
    if DRY_RUN:
        print("  (dry-run mode — no files written)")

    args = sys.argv[1:]
    plan_files, epic_files = collect_target_files(args)

    plan_fixed = 0
    if plan_files:
        print("\n--- Plans ---")
        for fp in plan_files:
            try:
                if fix_active_plan(fp):
                    plan_fixed += 1
            except Exception as e:  # noqa: broad-except — top-level per-file CLI guard: any failure
                # aborts with a clear message rather than a raw traceback
                print(f"  ERROR {fp.name}: {e}", file=sys.stderr)
                sys.exit(2)

    epic_fixed = 0
    if epic_files:
        print("\n--- Epics ---")
        for fp in epic_files:
            try:
                if fix_epic(fp):
                    epic_fixed += 1
            except Exception as e:  # noqa: broad-except — top-level per-file CLI guard: any failure
                # aborts with a clear message rather than a raw traceback
                print(f"  ERROR {fp.name}: {e}", file=sys.stderr)
                sys.exit(2)

    print(f"\nDone: {plan_fixed} plans fixed, {epic_fixed} epics fixed")

    if _REFUSED:
        print(
            f"\n❌ {len(_REFUSED)} doc(s) REFUSED — frontmatter is not valid YAML, so they were NOT modified:",
            file=sys.stderr,
        )
        for fp, err in _REFUSED:
            try:
                shown = fp.relative_to(PM_DIR)
            except ValueError:
                shown = fp
            print(f"  - {shown}\n      {err}", file=sys.stderr)
        print(
            "\n  These need a HUMAN to fix the YAML syntax. Auto-appending fields to a doc whose\n"
            "  frontmatter does not parse masks the real error and makes the fixer's commit look\n"
            "  like the cause. A single such doc fails the corpus-wide frontmatter gate, which\n"
            "  blocks quality-gates.sh — and therefore every slot's ship — on the shared branch.\n"
            "  Common cause: an unquoted multi-line `summary:`/`title:` containing a colon-space\n"
            "  (`...backfill: the shipped...`), which YAML reads as a nested mapping key. Fix by\n"
            "  making it a folded block scalar: `summary: >-`.",
            file=sys.stderr,
        )
        # Non-zero so an automated caller cannot silently proceed. plan-health-agent.yml runs this
        # as `fix_frontmatter.py || true`; the exit code is belt-and-braces, the stderr block above
        # is what a human actually reads in the run log.
        sys.exit(3)


if __name__ == "__main__":
    main()
