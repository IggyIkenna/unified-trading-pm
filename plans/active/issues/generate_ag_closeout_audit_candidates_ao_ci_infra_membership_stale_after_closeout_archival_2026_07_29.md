---
doc_type: issue
title:
  generate_ag_closeout_audit_candidates.py's ao/ci/infra membership branch silently returns ZERO candidates once the
  tranche's own consolidated-closeout doc is archived — stale relative to the skill's 2026-07-27 asset_group schema
  migration
summary: >-
  Discovered running `/ag-closeout-audit ci` (autonomous, 2026-07-29, scheduled `ag_closeout_auditor` worker, slot 7).
  `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche ci --json` returned `total_members: 0` /
  `never_cited_count: 0` / `cited_somewhere_count: 0` even though 29 live docs currently carry `asset_group: [ci]`. Root
  cause: for the `ao`/`ci`/`infra` tranches, `main()`'s membership test is `member = basename in
  non_ag_member_sets.get(t, set())`, and `non_ag_member_sets` is built via `_cited_basenames(_closeout_paths(nt))` —
  i.e. it scans the tranche's OWN `<tranche>_consolidated_closeout_*.md` for basename-shaped citations.
  `_closeout_paths()` globs `plans/active/{prefix}_consolidated_closeout_*.md`. `ci_consolidated_closeout_2026_07_25.md`
  was archived to `plans/archive/2026_07/` on 2026-07-28 (its own single todo done — it was a pure reachability digest).
  Once archived, the glob returns an empty list, `_cited_basenames([])` returns an empty set, and EVERY candidate fails
  `basename in non_ag_member_sets.get(t, set())` — silently zero, not an error. This is exactly the retired
  2026-07-25→27 "citation-in-closeout-doc" workaround the skill's own SKILL.md now documents as superseded: as of
  2026-07-27 (`unified-trading-pm@a97bc7bed`), `ao`/`ci`/`infrastructure` are real dedicated `asset_group` enum values
  and membership should be tested directly (`t in asset_group`, same as the 5 real AGs) — this script's `else` branch
  was never updated to match, and the 2026-07-28 closeout archival additionally broke even the OLD fallback mechanism it
  still implements, compounding into total silent failure rather than a partial staleness.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, plan-hygiene, script-bug, asset-group, tranche-membership, silent-failure]
related:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/asset_group_ao_ci_infra_schema_expansion_2026_07_27.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-29"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: none
assigned_role: cicd
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
locked_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit ci` run 2026-07-29 (ag_closeout_auditor scheduled worker, slot 7) — Phase 0.3 discovery step.
---

# `generate_ag_closeout_audit_candidates.py`'s ao/ci/infra branch is silently blind once the closeout doc archives

## What was found

Running the Phase-0 pre-filter for the `ci` tranche audit:

```
.venv/bin/python scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche ci --json
```

returned:

```json
{
  "tranche": "ci",
  "covering_paths": [
    "plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md",
    "plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md"
  ],
  "total_members": 0,
  "never_cited_count": 0,
  "never_cited": [],
  "cited_somewhere_count": 0
}
```

`total_members: 0` is wrong — a direct frontmatter sweep the same session found **31 live docs** with `asset_group`
containing `ci` (29 after excluding the two covering docs themselves).

## Root cause

`generate_ag_closeout_audit_candidates.py` (lines 158-166):

```python
if t in AGS:
    member = t in asset_group
elif t == "cross-cutting":
    member = "cross-cutting" in asset_group and (parent_epic in DATA_EPICS or basename in cited)
else:  # ao/ci/infra
    member = basename in non_ag_member_sets.get(t, set())
```

`non_ag_member_sets` (lines 119-121):

```python
non_ag_member_sets = (
    {nt: _cited_basenames(_closeout_paths(nt)) for nt in NON_AG_TRANCHES} if t in NON_AG_TRANCHES else {}
)
```

`_closeout_paths()` (lines 75-77) globs `plans/active/{prefix}_consolidated_closeout_*.md`. This is the RETIRED
2026-07-25→27 workaround SKILL.md itself documents: "ao, ci, and infra are now real dedicated asset_group enum values
(added 2026-07-27) ... The 2026-07-25→27 workaround this section used to describe (no dedicated value, ground-truth only
via each tranche's Sources list) is RETIRED ... asset_group containing ao/ci/infrastructure is now the PRIMARY
membership signal for these 3 tranches — use it exactly like the 5 real AGs." This script's `else` branch was never
updated to match — it still implements the retired mechanism.

Independently, `ci_consolidated_closeout_2026_07_25.md` was archived to `plans/archive/2026_07/` on 2026-07-28 (its own
single `- [ ]` todo, "verify the reachability digest is accurate," was done — a legitimate archival per the 6-step
ritual). Because `_closeout_paths()` globs `plans/active/` only, the archival made `_closeout_paths("ci")` return an
EMPTY list, `_cited_basenames([])` return an empty set, and every `basename in non_ag_member_sets.get("ci", set())` test
fail — **not a partial staleness, total silent zero-candidate failure**, with no error, warning, or non-zero exit code.
The same code path (same `NON_AG_TRANCHES` list, same `else` branch) applies identically to `ao` and `infra` — both of
those tranches' own consolidated-closeout docs are still `status: active` in `plans/active/` as of this writing, so they
are not currently affected, but either archiving in the future (a legitimate, expected event per the digest/dispatch
split architecture — see `ci_consolidated_closeout_2026_07_25.md`'s own archival banner) would silently reproduce this
exact failure for that tranche too.

## Impact

A worker or scheduled `/ag-closeout-audit` run using this script's Phase-0 pre-filter for `ci` (or, in the future,
`ao`/`infra` once their closeout docs archive) gets a false "zero candidates, nothing to audit" signal instead of an
error — the kind of silent-false-pass this workspace's data-pipeline-correctness and honest-absence rules exist to
prevent in the data domain, showing up here in plan-hygiene tooling instead. This session worked around it via a direct
frontmatter sweep (`asset_group` containing `ci`, matching the AG-style test) rather than trusting the script's output,
so no audit gap resulted this run — but an agent that trusts the tool's `total_members: 0` at face value without
independently verifying would silently skip auditing an entire live 29-doc tranche.

## Fix direction (not implemented — read-only audit worker, out of dispatch scope)

Update the `else` branch (ao/ci/infra) to match the `if t in AGS` branch: `member = t in asset_group`, dropping the
`non_ag_member_sets` / `_closeout_paths()`-based citation mechanism entirely for these 3 tranches (it is provably
retired per SKILL.md and now also provably broken on archival). This also simplifies `main()` — the `non_ag_member_sets`
computation and the whole `_closeout_paths(nt)` call for `NON_AG_TRANCHES` becomes dead code once removed. Should
preserve the script's `never_cited`/`cited_somewhere` split (still useful — same meaning as for the 5 AGs) using the
SAME `covering_paths`-based `_cited_basenames()` computation already used for the AGs, just with the corrected
membership test feeding it.

## Todos

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 — unified-trading-pm@e88c41727.** `ao`/`ci`/`infra` membership branch now tests
      `t in asset_group` directly, matching the 5 real AGs — `non_ag_member_sets`/`_closeout_paths(nt)`-based citation
      mechanism removed entirely. **Done-when confirmed live**: `--tranche ci --json` now returns `total_members: 30`
      (current live count, was 0); `--tranche ao` returns 39; `--tranche infra` returns 42 (was 0 — see the second bug
      below). Adjacent bug found + fixed in the SAME change: the `infra` tranche name does not match its own
      `asset_group` enum VALUE (`infrastructure`, per `plans/PLAN_FORMAT.md`'s `ASSET_GROUP` enum — there is no `infra`
      member) — a naive `t in asset_group` for `t="infra"` would have silently reproduced the exact zero-candidates
      failure this doc reports, just via a different root cause; added
      `TRANCHE_ASSET_GROUP_VALUE = {"infra":     "infrastructure"}` mapping to close it.
- [x] ✅ [TEST] P2. **DONE 2026-07-30 — unified-trading-pm@e88c41727**,
      `tests/unit/test_generate_ag_closeout_audit_candidates.py` (5 cases):
      `test_non_ag_tranche_membership_survives_closeout_archival` (parametrized ci/ao/infra) builds a synthetic corpus,
      confirms `total_members >= 1` with the closeout doc present, then deletes it and re-confirms `total_members` is
      UNCHANGED — the exact regression this doc reports, now guarded. Plus
      `test_infra_tranche_asset_group_value_is_infrastructure_not_infra` (the adjacent bug) and
      `test_ag_tranche_membership_unaffected_by_the_fix` (regression guard on the untouched 5-real-AG branch). All 5
      pass.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the 2026-07-27 schema-migration section this script is stale
  against
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the archival ritual that legitimately
  triggered this
