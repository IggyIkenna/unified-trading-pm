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
status: open
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
resolved_by:
locked_by:
source: [prediction_satellite_ao_dispatch_batch4_2026_07_26.md todo 4b-iii, this session's completion]
drift_direction: advance-code
depends_on: []
---

# prediction_satellite_ao_dispatch_batch4 — archival prerequisite

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

- [ ] [SCRIPT] P2. Audit `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s four Deferred sections per the
      Recommended decision above; draft `prediction_satellite_ao_dispatch_batch5_<date>.md` for any genuinely-orphaned
      item. Repo: unified-trading-pm. Done when: every Deferred bullet has a recorded disposition in this issue doc's
      Progress Log.
- [ ] [SCRIPT] P2. Archive `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` to `plans/archive/2026_08/` via the
      6-step ritual (banner, codex-alignment re-check, referrer-path fixup scoped to `plans/active/**` + `codex/**`,
      confirm the move). Gated on the todo above. Repo: unified-trading-pm.

## Progress Log

- 2026-08-14 (slot 18, data_engineering): filed after verifying + closing batch4's last open todo (4b-iii). See that
  plan's own Progress Log for the 4b-iii completion evidence.
