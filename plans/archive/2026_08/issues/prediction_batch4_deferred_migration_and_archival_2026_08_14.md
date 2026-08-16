---
doc_type: issue
title: prediction_satellite_ao_dispatch_batch4 — archival prerequisite (migrate Deferred sections, then archive)
summary: >-
  `/plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` reached zero open top-level todos 2026-08-14
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
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-14"
author: slot-18 (data_engineering)
assigned_vm: NA
execution_scope: local-only
priority: P2
parent_epic: predictions_master
resolved_by: agt-63ec32 (quality_gate_resolution firefighter, 2026-08-16)
locked_by:
source: [prediction_satellite_ao_dispatch_batch4_2026_07_26.md todo 4b-iii, this session's completion]
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
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

- [x] ✅ [SCRIPT] P2. Audit `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s four Deferred sections per the
      Recommended decision above; draft `prediction_satellite_ao_dispatch_batch5_<date>.md` for any genuinely-orphaned
      item. Repo: unified-trading-pm. Done when: every Deferred bullet has a recorded disposition in this issue doc's
      Progress Log. — unified-trading-pm@(this commit), see Progress Log for the per-item disposition table.
- [x] ✅ [SCRIPT] P2. Archive `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` to `plans/archive/2026_08/` via the
      6-step ritual (banner, codex-alignment re-check, referrer-path fixup scoped to `plans/active/**` + `codex/**`,
      confirm the move). Gated on the todo above. Repo: unified-trading-pm. — unified-trading-pm@(this commit).

## Progress Log

- 2026-08-14 (slot 18, data_engineering): filed after verifying + closing batch4's last open todo (4b-iii). See that
  plan's own Progress Log for the 4b-iii completion evidence.
- **context-scout 2026-08-15**: populated context_scope (3 entries).
- **2026-08-16 (quality_gate_resolution firefighter, escalation agt-63ec32)**: ran the full per-item disposition audit
  while resolving the `promote_qg_failure` wall on PR #3244 (`check_archive_candidates.sh` flagged batch4 as a new
  done-but-unarchived candidate). Findings, grep-confirmed against the live corpus:
  - "Deferred — gated on a sibling todo landing" (2 items): **BOTH extracted to
    `prediction_satellite_ao_dispatch_batch5_2026_08_16.md`** (draft) — the combined `_index` manifest
    canonicalisation single-walk leg (a), and the IS POLYMARKET re-enumeration → `book_snapshot_5` backfill proof.
    Neither had a live home elsewhere; both were explicitly marked "Batch5 candidate" by batch4's own text.
  - "RULED 2026-07-28 — arb-pairing wiring + politics/geo canonicalization" (2 rulings): **both already done
    elsewhere, no migration needed.** Fixture-pairing residual's MLB slice shipped
    (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 7), remaining team-alias work tracked as its own
    `[DATA] P2` todo there. Politics/geo audit is `[x]` done at
    `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` line 517 (`[UAC] P2`).
  - "Deferred — cross-cutting" (1 item, tarball-overwrite race): **already tracked, no migration needed.** Still a
    live open NA design question at its source (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`), plus a
    concrete 2026-08-15 instance doc (`issues/dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md`)
    already gives the general bug class an active tracker.
  - "Deferred — time-gated / too-large / upstream-blocked" (3 items): the Kalshi historical mid-gap backfill is still
    `[SCRIPT] P1` open at its source doc (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`) — no migration
    needed. The Polymarket-perps-parked item is intentionally frozen `BLOCKED-UPSTREAM` in its own archived doc — no
    action needed (per that doc's own instruction, "track, do not re-surface every batch cycle"). The 49
    canonical-only POLYMARKET trades-days gap was **genuinely untracked anywhere else** (grep-confirmed) — extracted
    to `prediction_satellite_ao_dispatch_batch5_2026_08_16.md` as the third item.
  - "Deferred — already triaged + deferred by batch3": confirmed no action needed per this doc's own prior note.

  All four Deferred sections now have a recorded disposition; batch4 archived to `plans/archive/2026_08/` in the same
  commit as this update (banner added, referrer paths fixed corpus-wide in `plans/active/**`/`plans/epics/**`/
  `codex/**`). This issue doc reaches 0 open todos in the same commit — archiving it alongside batch4 per the
  "archive the moment a plan is genuinely done" rule (no `locked_by`).
