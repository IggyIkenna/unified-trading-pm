---
doc_type: plan
title: Sports satellite AO batch 16 — na-eligibility-audit residual extraction (2026-08-17)
summary: >-
  Sixteenth AO-dispatch batch for sports, drafted by the daily /na-eligibility-audit sports run (dispatch agt-1c51ee,
  slot 29). Extracts 2 conflict-clear bounded items from sports_consolidated_closeout_2026_07_19.md's Track S
  (standing 2026-07-23 operator ruling against a direct assigned_vm flip on that doc — per-item extraction is its
  established cadence, same pattern batches 5/9/10/12/14/15 already used). Both items conflict-checked against every
  other active sports satellite batch (5/9/10/12/14/15) and sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md
  before inclusion — none overlap. Source doc's own checkboxes are NOT flipped by this run (its line count, 1007L,
  sits over the 1000L hard cap and does not fit any SCOPED-mode line-cap exception for a multi-item citation edit) —
  reconciliation is deferred to this batch's own gated finalize plan, the same deferral pattern
  sports_satellite_ao_dispatch_batch15_2026_08_17_finalize.md already uses for its own source-doc reconciliation.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-16, satellite-docs, na-eligibility-audit]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit sports (2026-08-17, dispatch agt-1c51ee, slot 29) Phase 3, per
  /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §3's shared conflict-check protocol and
  task_template.md's dispatch-scope eligibility test.
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Sports satellite AO batch 16 — na-eligibility-audit residual extraction (2026-08-17)

## Conflict-check findings

Both candidates were read directly in `sports_consolidated_closeout_2026_07_19.md` Track S (lines 580, 582) and
checked against every other active sports satellite batch (5, 9, 10, 12, 14, 15) and
`sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md` — no overlap found for either item. Neither item
carries an `[OPERATOR]` tag or a design/judgment call; both are bounded, worker-determinable outcomes per
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Todos

- [ ] [CODE] P2. **Eliminate (or document) the legacy bare `entity=fixtures/` (no `pipeline_mode=`) write path** still
      active today alongside the canonical split writer (5-league subset). Source:
      `sports_consolidated_closeout_2026_07_19.md` Track S. Repo: instruments-service. Done when: either the legacy
      write path is removed (with a confirming grep/test that nothing still calls it), or a documented reason is
      recorded for why it must stay, and the source doc's checkbox is flipped (via this batch's finalize plan).
- [x] ~~[DATA] P2. Snapshot-then-cull the 16 remaining post-floor day dirs (2024-12-24..2026-04-20) in
      `sports_reference_v2/by_date/`~~ — **DUPLICATE, already done — struck 2026-08-19 (plan_reconciler, agt-07473e).**
      This exact population shipped 2026-08-04 (slot-12): `deployment-service@1b63863`,
      `wipe_sports_reference_v2_post_floor_2026_08_04.py --apply`, 64/64 objects deleted, 0 error, post-delete 0
      objects under prefix — reconciled into `sports_consolidated_closeout_2026_07_19.md`'s own Track S checkbox in
      the same pass this todo was struck. Drafted 2026-08-17, 13 days after the work shipped, without checking
      `sports_consolidated_native_ao_extract_2026_07_25.md`'s already-DONE todo for the same population. No worker
      should pick this up.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the shared conflict-check
  protocol applied to both items above
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — reversibility-verified delete carve-out

## Progress Log

- **2026-08-17 (na-eligibility-audit sports, dispatch agt-1c51ee, slot 29)**: authored from
  `sports_consolidated_closeout_2026_07_19.md` Track S during the sports-tranche `/na-eligibility-audit` run's Phase 3
  (RECLASSIFY per-todo split path — the source doc's own ⛔ 2026-07-23 banner forbids a direct `assigned_vm` flip,
  per-item extraction is its established pattern). Source doc's own checkboxes NOT flipped this run — the source doc
  is 1007L, over its 1000L hard cap, and a multi-item citation edit does not fit any SCOPED-mode line-cap exception
  (see `check_line_caps.sh`'s documented exceptions); a small Progress Log marker was added there instead noting this
  extraction, and full reconciliation is deferred to this batch's own gated finalize plan (mirroring
  `sports_satellite_ao_dispatch_batch15_2026_08_17_finalize.md`'s identical deferral for its own 11 items). **Status
  set `active`** (not `draft`) per the 2026-07-30 no-double-gate ruling this skill's own verdict already constitutes
  the operator decision to apply.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries) -- re-verified all 3 entries still
  resolve on disk; no change.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
