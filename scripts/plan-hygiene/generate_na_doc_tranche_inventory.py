#!/usr/bin/env python3
"""Generate the current assigned_vm:NA + status:{active,open} doc inventory, split by the 9
/ag-closeout-audit tranches (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra).

Why this exists: a single-line `grep -lE '^assigned_vm:\\s*$'`-style sweep misses multi-line YAML
values (key on its own line, value on an indented continuation) and any value expressed via YAML
flow/quoting — confirmed live on sports_consolidated_closeout_2026_07_19.md
(na_docs_validity_and_ao_eligibility_audit_2026_07_26.md Phase 0). This script parses frontmatter
properly via scripts/docs/docspec.py (PyYAML) instead of line-grepping, for this and every future
sweep.

ao/ci/infrastructure are real dedicated asset_group enum values (2026-07-27 schema expansion,
unified-trading-pm@a97bc7bed) -- membership for those 3 tranches (plus the 5 real AGs) is tested
directly against `asset_group`, exactly like the 5 real AGs (`infra`'s enum VALUE is
`infrastructure`, not `infra` -- see TRANCHE_ASSET_GROUP_VALUE). This replaces a retired
2026-07-25->27 workaround (ground-truthing membership by citation-grepping each tranche's own
<tranche>_consolidated_closeout_2026_07_25.md body) that silently zeroed out a tranche's whole
membership the moment its closeout doc archived -- a normal, expected lifecycle event -- and
separately cross-contaminated tranches via ordinary `related:`/footnote citations; see
na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md for the
incident this fixed (same root-cause family as
generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md,
the sibling script's identical bug, already fixed there).

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never (this class of bug -- grep-based frontmatter/membership sweeps -- has recurred
# twice already; keep the proper-parse version around as the standing tool)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]

# Matches the dated na-eligibility-audit verdict marker and an optional [body-hash:…] tag
# written alongside it.  Handles all known marker variants:
#   **na-eligibility-audit 2026-07-30**: ...
#   **na-eligibility-audit 2026-07-30** [body-hash:abc123]: ...
#   **na-eligibility-audit 2026-08-06 (infra tranche)**: ...
#   **na-eligibility-audit 2026-08-03** (infra tranche, dispatch …): **KEEP-NA…
_VERDICT_MARKER_RE = re.compile(
    r"\*\*na-eligibility-audit (\d{4}-\d{2}-\d{2})"  # group 1: date
    r"[^\n\[]*"  # anything on the same line before '[' or newline
    r"(?:\[body-hash:([a-f0-9]{8,64})\])?"  # group 2: optional stored body hash
)

# Sibling-marker family: automated skills that write a purely boilerplate dated
# bookkeeping line into a doc's body (no doc-specific verdict/analysis payload) each
# time they touch it -- a touch-only visit from one of these must not flip
# body_content_hash, or every future run forces a needless full re-classification
# (na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md: 44%
# false-positive rate from context-scout's line alone, one tranche, one run).
#
# Confirmed by grepping plans/active/ for every `**<name> YYYY-MM-DD**` convention in
# informal use and sampling each candidate's actual line text before adding it here:
#   - na-eligibility-audit: this skill's own verdict marker (also parsed by
#     _VERDICT_MARKER_RE below) -- boilerplate template, verdict text is standardized.
#   - context-scout: "**context-scout YYYY-MM-DD**: populated/refreshed context_scope
#     (N entries)." -- always boilerplate, never doc-specific content.
# Investigated and DELIBERATELY EXCLUDED: docs-reconcile / plan-reconcile /
# ag-closeout-audit / ag_closeout_auditor all write doc-specific substantive analysis
# in the same marker line (e.g. "linkage fix -- added...", "operator confirmed...",
# "first-ever `/ag-closeout-audit ui` run -- the..."). Stripping those would hide a
# genuine content change from the hash and cause a false SKIP -- worse than the
# false-positive this family fixes. Add a name here only after confirming (by
# sampling real lines, same as above) that the skill's marker is boilerplate-only.
_BOOKKEEPING_MARKER_SKILL_NAMES = (
    "na-eligibility-audit",
    "context-scout",
)

# Strips entire lines that contain a bookkeeping marker so body_content_hash is
# stable w.r.t. marker addition/update (the marker itself lives in the body, so
# without this the hash would change every time one is written or updated).
_BOOKKEEPING_MARKER_ALTERNATION = "|".join(re.escape(n) for n in _BOOKKEEPING_MARKER_SKILL_NAMES)
_VERDICT_MARKER_LINE_RE = re.compile(
    r"^[^\n]*\*\*(?:" + _BOOKKEEPING_MARKER_ALTERNATION + r") \d{4}-\d{2}-\d{2}[^\n]*\n?",
    re.MULTILINE,
)


def strip_frontmatter(text: str) -> str:
    """Return the doc body with the leading YAML frontmatter block removed."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return "".join(lines[i + 1 :])
    return text  # no closing ---, treat as bodyless frontmatter


def body_content_hash(text: str) -> str:
    """SHA-256 of the verdict-relevant body, truncated to 16 hex chars.

    Stable w.r.t.:
    - frontmatter-only changes (e.g. context_scope: backfills) — frontmatter is stripped.
    - verdict marker additions/updates — marker lines are excluded so writing or updating
      a [body-hash:…] tag does not change the hash that was stored at verdict time.

    Two docs that differ only in frontmatter or verdict markers produce the same hash,
    while any real body-content change (new todo, status update, body text edit) produces
    a different hash.
    """
    body = strip_frontmatter(text)
    body = _VERDICT_MARKER_LINE_RE.sub("", body)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def _latest_verdict_marker(text: str) -> tuple[str, str | None] | None:
    """Parse the most recent na-eligibility-audit verdict marker from a doc.

    Returns (date, stored_hash) where stored_hash is None for pre-hash-extension
    markers (written before [body-hash:…] was added to the marker format).
    Returns None when the doc has no verdict marker at all.
    """
    best: tuple[str, str | None] | None = None
    for m in _VERDICT_MARKER_RE.finditer(text):
        date = m.group(1)
        stored = m.group(2)  # None when no [body-hash:…] tag
        if best is None or date > best[0]:
            best = (date, stored)
    return best


def _git_body_hash_at_date(pm: Path, rel_path: str, marker_date: str) -> str | None:
    """Return body_content_hash of rel_path at the latest git commit on or before marker_date.

    Fallback for markers written before the [body-hash:…] extension.  Returns None
    when git is unavailable, the path has no history, or the call times out.
    """
    try:
        log = subprocess.run(
            ["git", "log", "--format=%H", f"--until={marker_date}T23:59:59", "--", rel_path],
            cwd=pm,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if log.returncode != 0 or not log.stdout.strip():
            return None
        sha = log.stdout.splitlines()[0].strip()
        show = subprocess.run(
            ["git", "show", f"{sha}:{rel_path}"],
            cwd=pm,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if show.returncode != 0:
            return None
        return body_content_hash(show.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _load_docspec():
    spec = importlib.util.spec_from_file_location("docspec", PM / "scripts" / "docs" / "docspec.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load_docspec()

AGS = ["cefi", "defi", "tradfi", "prediction", "sports"]
NON_AG_TRANCHES = ["ao", "ci", "infra", "ui"]
ALL_TRANCHES = [*AGS, "cross-cutting", *NON_AG_TRANCHES]

# infra's TRANCHE name (CLI --tranche, closeout-doc prefix) does not match its actual `asset_group`
# enum VALUE, which is `infrastructure` (plans/PLAN_FORMAT.md's ASSET_GROUP enum has no "infra"
# member) -- ao/ci/ui have no such mismatch (their enum values equal their tranche names).
TRANCHE_ASSET_GROUP_VALUE = {"infra": "infrastructure"}

# One owning tranche per multi-tranche doc, ruled 2026-07-30
# (sharded_per_tranche_audit_stash_race_and_multitranche_marker_gap_2026_07_30.md, option A): derived
# from `parent_epic` -- single-valued, maps 1:1 onto a real plans/epics/{parent_epic}.md -- rather than
# the first `asset_group` list entry (codex/11-project-management/ao-dispatch-batch-naming-and-conflict-
# check.md SS 2 "Grouping"). Built by reading every plans/epics/*.md's own dominant scope (most non-AG
# epics self-tag `asset_group: [cross-cutting]` or `[meta]`, too coarse to derive a single tranche from
# directly -- see that same codex SS 2 -- so this table encodes the ag-closeout-audit SKILL.md
# classification-mechanism section's documented epic groupings instead of re-deriving them per run).
EPIC_TO_TRANCHE = {
    # 5 real AGs -- each has one dedicated master epic.
    "cefi_master": "cefi",
    "defi_master": "defi",
    "tradfi_master": "tradfi",
    "predictions_master": "prediction",
    "sports_master": "sports",
    # ao -- agent-orchestrator dispatch/worker-lifecycle.
    "orchestrator_master": "ao",
    "agent_operating_framework_master": "ao",
    # infra -- generic repo/dependency/terraform/org hygiene + plan-corpus hygiene tooling. CI-specific
    # docs already self-tag `asset_group: ci` directly (2026-07-27 schema expansion), so this epic-level
    # fallback rarely needs to arbitrate the ci/infra split within infrastructure_master's own content.
    "infrastructure_master": "infra",
    "plan_hygiene_master": "infra",
    # ui -- deploy/launch consoles, data-status UI, cost/VM/alerts observability (tranche added 2026-07-30).
    "deployment_and_user_management_master": "ui",
    "observability_master": "ui",
    # Every other epic is a genuinely cross-AG / platform-wide coordinator -- cross-cutting is the
    # correct single owner (includes DATA_EPICS' non-infra members plus the rest, and the SUPERSEDED
    # coordinators for defensiveness even though no live doc should still carry them as parent_epic).
    "batch_live_symmetry_master": "cross-cutting",
    "client_isolation_and_governance_master": "cross-cutting",
    "dart_and_promote_master": "cross-cutting",
    "escalation_and_disaster_recovery_master": "cross-cutting",
    "execution_master": "cross-cutting",
    "features_and_ml_master": "cross-cutting",
    "global_ledger_pnl_attribution_master": "cross-cutting",
    "instruments_master": "cross-cutting",
    "manifest_master": "cross-cutting",
    "mtds_mdps_master": "cross-cutting",
    "strategy_master": "cross-cutting",
    "trading_agent_master": "cross-cutting",
    "cross_cutting_may_23_SUPERSEDED_2026_05_21": "cross-cutting",
    "manifest_evolution_SUPERSEDED_2026_05_21": "cross-cutting",
    "manifest_migration_SUPERSEDED_2026_05_21": "cross-cutting",
    "strategy_and_dart_master_SUPERSEDED_2026_05_21": "cross-cutting",
}


def owning_tranche(parent_epic: str, tranches: list[str]) -> str:
    """The ONE tranche that writes this doc's incremental-skip verdict marker (every other tranche a
    multi-tranche doc belongs to still classifies + reports it, but never writes to it -- see this
    script's module docstring precedent + the primary-owner rule in na-eligibility-audit/SKILL.md).
    Falls back to the first classified tranche when `parent_epic` is unmapped/blank or its mapped
    tranche isn't one of the doc's own classified tranches -- ownership is never assigned to a tranche
    the doc isn't otherwise a real member of."""
    mapped = EPIC_TO_TRANCHE.get(parent_epic)
    if mapped and mapped in tranches:
        return mapped
    return tranches[0]


DOC_TREES = ["plans/active/*.md", "plans/active/issues/*.md"]

DATA_EPICS = {
    "infrastructure_master",
    "instruments_master",
    "mtds_mdps_master",
    "manifest_master",
    "features_and_ml_master",
}

# [-*] bullet, standard case. A star-bullet variant is confirmed live
# (defi_expected_unattempted_backlog_1m_2026_07_03.md -- exactly the "non-canonical checkbox format
# the regex missed" failure class this script exists to avoid).
CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[ \]", re.MULTILINE)


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pat in DOC_TREES:
        for p in PM.glob(pat):
            rel = p.relative_to(PM).as_posix()
            if p.is_file() and p not in seen and not rel.startswith(".claude/"):
                seen.add(p)
                out.append(p)
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tranche", choices=[*ALL_TRANCHES, "all"], default="all")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a summary table")
    parser.add_argument(
        "--owned-only",
        action="store_true",
        help="filter to docs this --tranche OWNS (writes the verdict marker for) -- requires --tranche != all",
    )
    args = parser.parse_args(argv)
    if args.owned_only and args.tranche == "all":
        parser.error("--owned-only requires --tranche to name a specific tranche, not 'all'")

    records = []
    for path in _iter_docs():
        rel = path.relative_to(PM).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            fm, _ = ds.parse_frontmatter(text)
        except yaml.YAMLError:
            continue
        if fm is None:
            continue
        assigned_vm = fm.get("assigned_vm")
        status = fm.get("status")
        if not (isinstance(assigned_vm, str) and assigned_vm.strip().upper() == "NA"):
            continue
        if status not in ("active", "open"):
            continue

        asset_group = fm.get("asset_group") or []
        if isinstance(asset_group, str):
            asset_group = [asset_group]
        parent_epic = fm.get("parent_epic") or ""
        basename = path.name

        open_todos = len(CHECKBOX_RE.findall(text))

        # Content-hash (frontmatter-blind) incremental-skip logic.  A doc is skippable when its
        # body content has not changed since its last na-eligibility-audit verdict marker —
        # regardless of intervening frontmatter-only commits (e.g. context_scope: backfills).
        current_hash = body_content_hash(text)
        marker = _latest_verdict_marker(text)
        verdict_date: str | None = None
        incremental_skip = False
        if marker is not None:
            verdict_date, stored_hash = marker
            if stored_hash is not None:
                # Primary path: hash stored in marker — exact comparison, no git needed.
                incremental_skip = stored_hash == current_hash
            else:
                # Fallback for pre-hash-extension markers: retrieve body at marker commit via git
                # and compare.  Returns None if git is unavailable or the path has no history.
                hist_hash = _git_body_hash_at_date(PM, rel, verdict_date)
                incremental_skip = hist_hash is not None and hist_hash == current_hash

        tranches: list[str] = []
        for ag in AGS:
            if ag in asset_group:
                tranches.append(ag)
        for t in NON_AG_TRANCHES:
            # ao/ci/infra are real dedicated asset_group enum values (2026-07-27 schema expansion);
            # ui joined them 2026-07-30 -- all tested identically to the 5 real AGs, not via the
            # retired closeout-citation proxy (see
            # na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md).
            if TRANCHE_ASSET_GROUP_VALUE.get(t, t) in asset_group:
                tranches.append(t)
        if "meta" in asset_group and not tranches:
            tranches.append("infra")  # default fold per ag_closeout_audit_scope_widening_triage precedent
        if "cross-cutting" in asset_group and (parent_epic in DATA_EPICS or not tranches):
            tranches.append("cross-cutting")

        # Fixed 2026-08-02 (operator ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md
        # na-eligibility-audit item 15, option C): a doc whose `asset_group` resolves to NOTHING more
        # specific than the generic "infra" bucket (either directly via `asset_group: [infrastructure]`, or
        # via the "meta" default-fold above) previously stayed invisible to its actual `parent_epic`-mapped
        # tranche (e.g. `ao`) forever -- the asset_group-derived `tranches` list is the ONLY input
        # `_iter_docs`'s caller uses to decide which tranche's `--tranche <x>` run even sees this doc, so a
        # mistagged doc was structurally invisible to the one tranche that could correctly retag it: every
        # future `ao` run never saw it, every future `infra` run saw it but wasn't the domain owner and (per
        # the primary-owner rule) couldn't write a cross-tranche retag either -- a genuine deadlock,
        # confirmed on 4 live docs 2026-08-02. Fix: ONLY when "infra" ended up as the SOLE candidate (never
        # when a doc already has a real, specific tranche -- own AG, `ao`/`ci`/`ui`, or `cross-cutting`, all
        # of which must win exactly as before), ALSO add the parent_epic-mapped tranche if it differs. This
        # only ever ADDS a second candidate to the single-generic-bucket case; every other classification
        # path above is completely unchanged.
        if tranches == ["infra"]:
            epic_tranche = EPIC_TO_TRANCHE.get(parent_epic)
            if epic_tranche and epic_tranche in ALL_TRANCHES and epic_tranche != "infra":
                tranches.append(epic_tranche)

        doc_tranches = tranches or ["UNCLASSIFIED"]
        records.append(
            {
                "path": rel,
                "basename": basename,
                "doc_type": fm.get("doc_type"),
                "asset_group": asset_group,
                "parent_epic": parent_epic,
                "open_todos": open_todos,
                "tranches": doc_tranches,
                "owning_tranche": owning_tranche(parent_epic, doc_tranches),
                # Incremental-diff fields (Phase 0 of /na-eligibility-audit).
                # body_content_hash: SHA-256 of frontmatter-stripped body (first 16 hex chars).
                #   Skills write this into the verdict marker as [body-hash:…] so future runs
                #   can skip without a git call when only frontmatter changed.
                # incremental_skip: True when the body hasn't changed since the last verdict.
                #   A doc with incremental_skip=True needs no Phase-1 re-read.
                "body_content_hash": current_hash,
                "verdict_marker_date": verdict_date,
                "incremental_skip": incremental_skip,
            }
        )

    if args.tranche != "all":
        records = [r for r in records if args.tranche in r["tranches"]]
    if args.owned_only:
        records = [r for r in records if r["owning_tranche"] == args.tranche]

    if args.json:
        print(json.dumps(records, indent=1))
        return 0

    tranches_with_unclassified = [*ALL_TRANCHES, "UNCLASSIFIED"]
    by_tranche: dict[str, list[dict]] = {t: [] for t in tranches_with_unclassified}
    owned_by_tranche: dict[str, list[dict]] = {t: [] for t in tranches_with_unclassified}
    for r in records:
        for t in r["tranches"]:
            by_tranche.setdefault(t, []).append(r)
        owned_by_tranche.setdefault(r["owning_tranche"], []).append(r)

    total_docs = len(records)
    total_zero = sum(1 for r in records if r["open_todos"] == 0)
    print(f"Total NA+active/open docs: {total_docs}  (zero-open-todo: {total_zero})")
    for t in tranches_with_unclassified:
        docs = by_tranche.get(t, [])
        zero = sum(1 for r in docs if r["open_todos"] == 0)
        owned = len(owned_by_tranche.get(t, []))
        print(f"  {t:14s} {len(docs):4d} docs  ({zero} zero-open-todo)  [{owned} owned]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
