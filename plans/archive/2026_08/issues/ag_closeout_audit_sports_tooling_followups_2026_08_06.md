---
doc_type: issue
title:
  ag-closeout-audit sports tooling follow-ups (2026-08-06 run) — linkage-gate superseded-status gap + truncated batch9
  Deferred citations
summary: >-
  Two small, clear findings from the 2026-08-06 sports tranche audit (agt-7b0c34): (1) check_ag_closeout_linkage.py
  reports `status: superseded` docs as orphans — the gate has no status exclusion, so a superseded doc reads as an
  unlinked orphan forever (currently the 1 residual sports orphan); (2) several Deferred citations in
  sports_satellite_ao_dispatch_batch9_2026_08_04.md are truncated mid-sentence with a trailing "…", making the 08-04
  conflict-claims not fully recoverable from the record — this run re-verified each affected item live, but the record
  itself should be completed or explicitly retired.
status: resolved
nature: issue
asset_group: [sports, ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, linkage-gate, plan-hygiene, truncated-citation, batch9, tooling]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/archive/2026_08/ag_closeout_audit_sports_tooling_followups_2026_08_06_finalize_2026_08_08.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
depends_on: []
source: >-
  /ag-closeout-audit sports tranche run, 2026-08-06 (agt-7b0c34, slot-13) — the run's two residual tooling observations,
  filed per the pre-compact ritual (findings become - [ ] todos, never prose-only).
resolved_by: "unified-trading-pm@a969d9ba8 (Finding 1), unified-trading-pm@a72c755c3 (Finding 2), live-defi-rollout"
locked_by:
locked_since:
context_scope:
  [
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /plans/active/issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md,
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
  ]
---

> **🟢 ARCHIVED 2026-08-08 — RESOLVED** (status: resolved, 0 open todos, unlocked). Both findings verified live:
> `check_ag_closeout_linkage.py` re-run confirms the previously-flagged superseded doc no longer appears as an orphan
> (`unified-trading-pm@a969d9ba8`); zero `…`-truncated Deferred bullets remain in
> `sports_satellite_ao_dispatch_batch9_2026_08_04.md` (`unified-trading-pm@a72c755c3`). Archived by
> `ag_closeout_audit_sports_tooling_followups_2026_08_06_finalize_2026_08_08.md`'s reconciliation todo.

# ag-closeout-audit sports tooling follow-ups (2026-08-06)

## Finding 1 — linkage gate counts `superseded` docs as orphans

`scripts/plan-hygiene/check_ag_closeout_linkage.py` has no `status` exclusion for orphan candidates (its docstring
excludes only archived docs and multi-asset_group/meta docs). A doc with `status: superseded` is therefore reported as
an unlinked orphan forever. Current instance:
`plans/active/issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` — `status: superseded`, yet
`check_ag_closeout_linkage.py` lists it as a sports orphan (it was the 1 residual sports orphan after the 2026-08-06
run's linkage fixes; the other 2 were genuinely unlinked sports docs fixed by adding them to the consolidated closeout's
`related:` block, `unified-trading-pm@83f122e34`). Superseded docs are already closed — per the skill's Phase 0.3 they
should be excluded from orphan candidacy, same as `resolved`/`archived`.

- [x] ✅ [CI] P3. Add a `status: superseded` exclusion (and audit the other closed statuses the gate may also be
      missing: `resolved`, `complete`/`completed`) to the orphan-candidate filter in
      `scripts/plan-hygiene/check_ag_closeout_linkage.py`, mirroring how
      `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py` already excludes them (`EXCLUDED_STATUS`); then
      re-run the gate and confirm the superseded sports doc drops out. Source: this issue doc. Done when: the gate's
      orphan count excludes superseded-status docs and the previously-flagged superseded doc no longer appears. —
      unified-trading-pm@a969d9ba8 (EXCLUDED_STATUS added; baseline lowered 69→49; superseded doc no longer flagged)

## Finding 2 — batch9 Deferred citations truncated mid-sentence

Several entries in `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s Deferred section end with a trailing "…"
mid-sentence (e.g. the `sports_halftime_odds_sfi_vs_inplay` blank-fixture_id, the
`sports_odds_feature_naming_canonicalization` parity-test, and the CLV-retrain entries), so the 08-04 run's
conflict-claims are not fully recoverable from the record alone. The 2026-08-06 run re-verified each affected item live
(batch10 Progress Log), but the record itself should be completed or explicitly retired so a future audit doesn't have
to re-derive them.

- [x] ✅ [PROCESS] P3. Complete the truncated Deferred citations in
      `plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md` (find every `…`-terminated bullet under the
      `## Deferred` section, finish each citation or replace it with an explicit "claim not recoverable — re-verified in
      batch10" note). Source: this issue doc + the batch10 Progress Log. Done when: zero `…`-truncated Deferred bullets
      remain in batch9, with each either completed or explicitly retired. — unified-trading-pm@a72c755c3

## Progress Log

- **slot-13 (ag_closeout_auditor agt-7b0c34) 2026-08-06**: Filed during the pre-compact ritual at session end, per the
  workspace HARD RULE that findings become `- [ ]` todos. Both findings were surfaced in the batch10 Progress Log as
  prose; this doc makes them tracked work. Neither is blocking: the gate gap affects 1 doc (a superseded issue), and the
  truncated citations were re-verified live this run.
- **context-scout 2026-08-07**: populated/refreshed context_scope (4 entries) -- added
  `generate_ag_closeout_audit_candidates.py`, explicitly named in finding 1's own todo as the reference implementation
  (`EXCLUDED_STATUS`) to mirror.
- **na-eligibility-audit 2026-08-08 (Phase 2/3, sports tranche)**: RECLASSIFY applied — re-verified both open todos
  against the whole-doc bar (finding 1 `[CI] P3` and finding 2 `[PROCESS] P3` are each a checkable fact + a scoped code
  or text change with a stated done-when, no judgment call undecided). Conflict-check (per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) came back CLEAR for both: (a) no
  active `assigned_vm: planning` plan in `parent_epic: sports_master` carries a matching todo —
  `check_ag_closeout_linkage.py` has zero `status`/`EXCLUDED` handling today (independently grepped), and the only prior
  linkage-gate fix (`ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`, already shipped) was the
  AG-coverage bug, not the status-exclusion bug finding 1 describes; (b) no sibling batch/finalize doc drafted this week
  claims either item; (c) `sports_consolidated_closeout_2026_07_19.md` doesn't touch either. Flipped `assigned_vm: NA`
  -> `planning`, `execution_scope: local-only` -> `orchestrator-agent`, `assigned_role: data_engineering` -> `infra`
  (better fit — a plan-hygiene script fix + a doc-citation completion, not data-pipeline work; validated against the
  live `agents/infra.md` registry entry). Companion finalize twin:
  `ag_closeout_audit_sports_tooling_followups_2026_08_06_finalize_2026_08_08.md`.
