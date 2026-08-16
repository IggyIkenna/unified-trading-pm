---
doc_type: issue
title: prediction_satellite_ao_dispatch_batch4 — archival prerequisite (migrate Deferred sections, then archive)
summary: >-
  `/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` reached zero open top-level todos 2026-08-14
  (4b-iii — shape #4 merge+delete — was the last one, verified complete: VM
  `canonical-migration-prediction-shape4-merge-20260812-221112` EXIT_STATUS=0, 799,510 objects, 737,828 deleted, 61,682
  correctly kept as honest non-canonical). Per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` §
  1, the plan is now archival-eligible but its several "Deferred" sections carry substantive content that must not
  "evaporate with the archived plan" — this is a judgment-call audit (which items are already tracked elsewhere vs.
  genuinely need a new batch5 dispatch plan), out of scope for the single mechanical worker who flipped the last
  checkbox.
status: resolved
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, archival, plan-hygiene, ao-dispatch, batch4, batch5]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-14"
author: slot-18 (data_engineering)
assigned_vm: NA
execution_scope: local-only
priority: P2
parent_epic: predictions_master
resolved_by: cicd escalation agent (slot 3, agt-8b735e), unified-trading-pm, 2026-08-16
locked_by:
source: [prediction_satellite_ao_dispatch_batch4_2026_07_26.md todo 4b-iii, this session's completion]
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# prediction_satellite_ao_dispatch_batch4 — archival prerequisite

> **ARCHIVED**: resolved by unified-trading-pm (cicd escalation agent, slot 3, agt-8b735e, 2026-08-16) — Deferred
> sections audited + migrated to `/plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md`;
> `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` archived to `plans/archive/2026_08/`. Successor:
> `prediction_batch4_deferred_residuals_2026_08_16.md` (the 2 migrated residual todos).

## What I found

`prediction_satellite_ao_dispatch_batch4_2026_07_26.md` now has every top-level `- [ ]` checked (4a/4b-i/4b-ii/4b-iii/4c
all COMPLETE as of 2026-08-14) and no `locked_by` — mechanically archival-eligible. But it carries four "Deferred"
sections with real, un-migrated content:

- "Deferred — gated on a sibling todo landing" (2 items, both already gate-cleared/promoted-to-ready per the doc's own
  text — likely just need a home in a new batch5 doc, not fresh triage).
- "RULED 2026-07-28 — arb-pairing wiring + politics/geo canonicalization" (2 rulings, one partially shipped already per
  batch6 — check whether the residual is already tracked in a live doc before assuming it needs migration).
- "Deferred — cross-cutting" (1 item — routes to the infra/ci tranche closeout, not prediction; may already be tracked
  there, needs a grep-and-confirm, not necessarily a new todo).
- "Deferred — time-gated / too-large / upstream-blocked (non-batchable)" (a few items — some reference other still-live
  docs like `prediction_cross_venue_arb_and_coverage_2026_07_24.md`, which may already carry the tracked todo).

The "Deferred — already triaged + deferred by batch3" section needs **no action** — it explicitly documents that its
items are already tracked in `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md`; do not
re-derive.

## Why it matters

Archiving the plan without first confirming each Deferred item's disposition would let real intent silently evaporate —
exactly the failure mode `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 1 exists to close. This
is also a `run_hygiene_sweep.sh` / `regenerate_active_plan_inventory.py` finding waiting to happen (a
stale-active-but-fully-checked plan) if left alone.

## Recommended decision

Run `/ag-closeout-audit prediction` (or an equivalent manual pass) scoped to this one plan's Deferred sections:

1. For each Deferred bullet, determine: already a real `- [ ]` todo in a live doc (cite it, no action needed) vs.
   genuinely orphaned (needs a new `- [ ]` todo).
2. Draft any genuinely-orphaned items into `prediction_satellite_ao_dispatch_batch5_<date>.md` (`status: draft`,
   mirroring how `/ag-closeout-audit prediction` produced batch4 from batch3's gaps — never auto-shipped; operator flips
   to `active` per CLAUDE.md "Plan destination — ASK BEFORE CREATING").
3. Once every Deferred bullet has a disposition, archive `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` to
   `plans/archive/2026_08/` via the 6-step ritual (incl. the corpus-wide referrer-path fixup —
   `grep -rl "prediction_satellite_ao_dispatch_batch4_2026_07_26" --include='*.md' .` found ~30 hits, mostly
   already-archived historical docs; prioritize fixing references in `plans/active/**` and `codex/**`, which affect live
   navigation, over rewriting frozen archive history).

## Todos

- [x] ✅ [SCRIPT] P2. **DONE 2026-08-16 (cicd escalation agent, slot 3).** Audited all 4 Deferred sections against the
      live corpus: 5 of 7 items already had a tracked home elsewhere (fixture-pairing residual + politics/geo
      canonicalization both complete in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`; the tarball race +
      historical Kalshi enumeration both still live open items in `prediction_cross_venue_arb_and_coverage_2026_07_24.md`;
      the `book_snapshot_5` row-proof complete in `prediction_live_clob_depth_capture_2026_07_24.md`;
      `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` is itself `status: complete`). The 2 genuinely-orphaned
      items (the `_index` manifest out-of-lifecycle reclassification + the 49-day metadata-gap investigation) migrated
      into a real tracked issue doc rather than a full batch5-style AO plan (both are single bounded items, not a
      dispatch-batch's worth of AO-eligible work):
      `/plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md`. Full per-bullet disposition table in
      that doc. Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-16 (cicd escalation agent, slot 3).** Archived
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` to `plans/archive/2026_08/` via the 6-step ritual —
      archive banner added, referrer-path fixup applied to the 4 live `plans/active/**` referrers carrying a
      leading-slash `/plans/active/...` reference (`autonomous_session_operator_decisions_2026_07_25.md`,
      `prediction_live_clob_depth_capture_2026_07_24.md` ×3, `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`
      ×3, `prediction_cross_venue_arb_and_coverage_2026_07_24.md`) repointed to the new archive path; the 2
      `codex/02-data/*.md` mentions (`canonical-cutover-register.md`, `non-canonical-path-inventory.md`) use bare
      (non-leading-slash) filename citations, out of `check_reference_paths.py`'s existence-check scope, left as
      historical citations. No codex contract change from this plan's completion (its content was operational
      migration work, not a new architectural pattern). Repo: unified-trading-pm.

## Progress Log

- 2026-08-14 (slot 18, data_engineering): filed after verifying + closing batch4's last open todo (4b-iii). See that
  plan's own Progress Log for the 4b-iii completion evidence.
- **context-scout 2026-08-15**: populated context_scope (3 entries).
- 2026-08-16 (cicd escalation agent, slot 3, agt-8b735e, dispatched on `ldr_qg_failure` for
  `check_archive_candidates`'s ratchet blocking `live-defi-rollout`): completed both todos above — audited +
  migrated the Deferred residuals, then archived batch4. This doc itself now has 0 open todos and no lock; archiving
  it in the same commit per the single-repo same-commit flip+archival sanctioned pattern
  (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).
