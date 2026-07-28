---
doc_type: plan
title: DeFi expected_unattempted seeder — design (capability-reconciliation RULED 2026-07-28, AO-dispatchable)
summary: >-
  Design track for the real DeFi expected_unattempted seeder ruled for on BLK-7c950d06 (Option A) — DeFi currently has
  NO expected_unattempted signal at all (MTDS orchestrator excludes every defi venue from the sentinel fan-out;
  DefiManifestRecorder has no record_expected_unattempted method), so a venue with a real UAC capability declaration is
  manifest-indistinguishable from one nobody ever declared. Per BLK-3221d4b3, this plan's first gating step —
  reconciling capability-declared-but-not-actually-collectible venues (the FLUID case) across 3 independently-drifting
  per-handler protocol lists — was an open-ended per-venue judgment call, not a worker-determinable fact. **RULED
  2026-07-28**: wire the existing FLUID-ETHEREUM adapter into the collection loop (disposition (a) — see Background).
  With that reconciliation resolved, the plan is converted to assigned_vm: planning (AO-dispatched) end-to-end.
status: active
nature: design
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, manifest, availability-index, expected-unattempted, honest-coverage, seeder, design]
related:
  [
    defi_manifest_no_expected_unattempted_seeder_2026_07_26,
    defi_satellite_ao_dispatch_batch2_2026_07_26,
    data_completion_defi_2026_07_15,
    mtds_is_full_adapter_smoketest_findings_2026_07_07,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_manifest_no_expected_unattempted_seeder_2026_07_26]
source: [defi_satellite_ao_dispatch_batch2-001 (task C8), BLK-7c950d06, BLK-3221d4b3]
assigned_role: data_engineering
drift_direction: advance-code
---

# DeFi expected_unattempted seeder — design

## Background

`defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s C8 todo ("fill DeFi manifest venue-key under-enumeration") was
dispatched to a worker, who found the premise false — see the full re-diagnosis in
[`defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`](issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md).
DeFi has no `expected_unattempted` seeder at all; the honest-coverage denominator for lst/lending/perp families is
whatever the union of 3 independently hand-maintained `_DEFAULT_PROTOCOLS` lists happens to cover, not derived from or
cross-checked against UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES`/`DEFI_VENUE_PHASE`. Governing SSOT:
`/codex/02-data/honest-absence-downstream-handling.md`.

Two rulings landed 2026-07-26:

- **BLK-7c950d06 → Option A**: build a real seeder mirroring `sentinels.py`'s `record_expected_unattempted`, denominator
  derived from `DEFI_VENUE_DATA_TYPE_CAPABILITIES` + `DEFI_VENUE_PHASE`. The original C8 checkbox CANNOT be completed as
  written and stays unchecked — its disposition is the issue doc's re-diagnosis + this plan.
- **BLK-3221d4b3 → Human plan (assigned_vm: NA), now RESOLVED 2026-07-28**: this plan's own capability-reconciliation
  step was an open-ended per-venue judgment call (not a worker-determinable fact) per the Dispatch-scope-eligibility
  rule (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`), so it had to resolve BEFORE any seeder
  implementation todo became AO-eligible. **Ruling (operator gate-clearance pass, 2026-07-28): disposition (a) — wire
  the existing FLUID-ETHEREUM adapter (`market_interface/adapters/defi/fluid_adapter.py`) into
  `lending_indices_handler.py`'s CLI/manifest-write loop, rather than excluding it from the denominator.** Reasoning:
  the general full-completion mandate for this pass ("all adaptors should be FINISHED with respect to data, unless it is
  literally proven the data cannot be obtained — in which case remove it fully, no half-built adaptors left lying
  around") applies directly here — FLUID-ETHEREUM is NOT a case of unobtainable data: a real, working adapter already
  exists and is already wired into two sibling collectors (risk_params, liquidations); the only gap is that
  lending_indices never got the same wiring. Finishing the wiring (rather than permanently excluding the venue from the
  coverage denominator) is completing an already-established pattern, not new build risk. With this disposition
  resolved, the plan converts to `assigned_vm: planning` and the P0 todo below is DONE.

**Anti-silent-placeholder guardrail (carries through every todo below)**: the seeder must key off ACTUAL collectibility.
No `_DEFAULT_PROTOCOLS` entry (e.g. `fluid`) is ever added without a working collector wired first — doing so would
write a dishonest zero-rows manifest stamp (the exact FLUID failure mode in re-diagnosis finding #5).

## Todos

- [x] ✅ [DATA] P0. **RULED 2026-07-28 (retagged from `[OPERATOR]`) — disposition (a) chosen: wire the existing adapter
      into the manifest-write loop.** Per venue/protocol currently declared in UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
      / `DEFI_VENUE_PHASE` (`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`,
      `defi_venues.py`) but NOT reachable by a working collector today: the FLUID-ETHEREUM case (capability declared,
      real adapter exists at `market_interface/adapters/defi/fluid_adapter.py`, but never wired into
      `lending_indices_handler.py`'s CLI/manifest-write loop — see re-diagnosis finding #5) is resolved as **(a) wire
      the existing adapter into the manifest-write loop** — not (b) exclude-until-collector-exists, since a working
      collector already exists (it's just not wired into this one handler; see Background for full reasoning). Execution
      task: wire `fluid_adapter.py` into `lending_indices_handler.py`'s CLI/manifest-write loop the same way it's
      already wired into the sibling `risk_params`/`liquidations` collectors, verified via a real manifest row for
      FLUID-ETHEREUM lending_indices (not a fabricated placeholder — confirm real fetched data, not a zero-rows stamp).
      If any OTHER venue is found during `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s follow-up audit
      todos with the same capability-declared-but-not-wired pattern, apply the same disposition (a) by default per this
      same ruling — treat (b)/exclude as the fallback ONLY if that venue's data is proven genuinely unobtainable (in
      which case remove the capability declaration + adaptor fully rather than leaving it half-wired). Recorded in this
      plan's Progress Log below.
- [ ] [DATA] P1. **Unblocked 2026-07-28 — P0's disposition is now RULED, so this is an ordinary determinable design
      task, no further human judgment required.** Design the seeder itself: a `record_expected_unattempted`-equivalent
      method on `DefiManifestRecorder`
      (`market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py`), fired from a new DeFi
      enumeration pass mirroring `market_tick_data_service/engine/orchestrator/sentinels.py`'s existing
      `record_expected_unattempted` pattern, with denominator = UAC `DEFI_VENUE_DATA_TYPE_CAPABILITIES` +
      `DEFI_VENUE_PHASE` filtered per the P0 reconciliation's dispositions (a FLUID-ETHEREUM lending_indices venue-key
      counts as attempted once its wiring lands, never a venue disposed "exclude until collector exists"). Write the
      design as a doc section here (schema of the new manifest rows, where the enumeration pass hooks into the DeFi
      `collect-*` CLI flow, how it avoids double-counting rows a handler already wrote). Done when: the design section
      is written + reviewed, with no open question about how a disposed-exclude venue is prevented from getting a
      stamped row.
- [ ] [DATA] P2. **Sequentially gated on the P1 design todo above** (an ordinary implementation task once the design
      lands, no further human judgment needed). Implement the seeder per the design, unit-tested, wired into the DeFi
      manifest-write path. Done when: `quality-gates.sh` is green on `market-tick-data-service` and a manifest census
      (deployment-api `_axis_census.py` or equivalent) shows every UAC-declared, non-excluded venue-key carrying at
      least one manifest row (captured or honest `expected_unattempted`) for its declared instrument_type family.
- [ ] [DATA] P3. **Reclassified 2026-07-27 — sequentially gated on the P2 implementation todo above, NOT itself a fresh
      operator-decision** (a bookkeeping checkbox-flip once the seeder is live, no human judgment needed). Once the
      seeder is live, re-open `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s C8 checkbox and flip it referencing
      this plan + the census evidence (dropping the unsatisfiable DRIFT-SOLANA criterion permanently, per the 2026-07-16
      operator ruling that removed DRIFT-SOLANA from every UAC registry).

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` — governing rule for this whole plan (a genuine absence and an
  unattempted state must never collapse into one signal).
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest/`capture_status` contract the new seeder must
  conform to.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § Dispatch-scope eligibility — why the P0 todo
  was human-only before the 2026-07-28 ruling resolved its disposition.

## Progress Log

- 2026-07-26 (slot 2): Plan created per BLK-3221d4b3's ruling (human plan, `assigned_vm: NA`). No design work started —
  next action is the operator resolving the P0 reconciliation todo.
- 2026-07-28 (operator gate-clearance pass): P0 resolved — **disposition (a)** for FLUID-ETHEREUM lending_indices: wire
  the existing `fluid_adapter.py` into `lending_indices_handler.py`'s manifest-write loop (not
  exclude-from-denominator). Reasoning: the adapter already exists and is already wired into the sibling
  `risk_params`/`liquidations` collectors — this is completing an established pattern, not new build risk, and the
  general full-completion mandate for this pass says finish adaptors rather than leave them half-wired unless the
  underlying data is proven unobtainable (it isn't here). Plan converted `assigned_vm: NA → planning`; P1/P2/P3 are now
  sequentially AO-dispatchable against this disposition.
