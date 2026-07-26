---
doc_type: plan
title: DeFi expected_unattempted seeder — design (human-driven, capability-reconciliation gated)
summary: >-
  Human/operator-driven design track for the real DeFi expected_unattempted seeder ruled for on BLK-7c950d06 (Option A)
  — DeFi currently has NO expected_unattempted signal at all (MTDS orchestrator excludes every defi venue from the
  sentinel fan-out; DefiManifestRecorder has no record_expected_unattempted method), so a venue with a real UAC
  capability declaration is manifest-indistinguishable from one nobody ever declared. Per BLK-3221d4b3, this plan stays
  assigned_vm: NA (human plan) because its first gating step — reconciling capability-declared-but-not-actually-
  collectible venues (the FLUID case) across 3 independently-drifting per-handler protocol lists — is an open-ended
  per-venue judgment call, not a worker-determinable fact. Once that reconciliation is operator-resolved, the
  implementation todos below may be converted to assigned_vm: planning (AO-dispatched) against its outcome.
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
assigned_vm: NA
execution_scope: local-only
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
- **BLK-3221d4b3 → Human plan (assigned_vm: NA)**: this plan's own capability-reconciliation step is an open-ended
  per-venue judgment call (not a worker-determinable fact) per the Dispatch-scope-eligibility rule
  (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`), so it must resolve BEFORE any seeder
  implementation todo becomes AO-eligible.

**Anti-silent-placeholder guardrail (carries through every todo below)**: the seeder must key off ACTUAL collectibility.
No `_DEFAULT_PROTOCOLS` entry (e.g. `fluid`) is ever added without a working collector wired first — doing so would
write a dishonest zero-rows manifest stamp (the exact FLUID failure mode in re-diagnosis finding #5).

## Todos

- [ ] [OPERATOR] P0. Resolve, per venue/protocol currently declared in UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES` /
      `DEFI_VENUE_PHASE` (`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`,
      `defi_venues.py`) but NOT reachable by a working collector today (the FLUID-ETHEREUM case: capability declared,
      real adapter exists at `market_interface/adapters/defi/fluid_adapter.py`, but never wired into
      `lending_indices_handler.py`'s CLI/manifest-write loop — see re-diagnosis finding #5), one of: (a) wire the
      existing adapter into the manifest-write loop, (b) exclude the venue from the seeder's denominator until a
      collector exists, or (c) some other disposition. This is the judgment call gating every todo below — it is a human
      decision because "capability declared" and "actually collectible" are two different registries today with no
      automatic reconciliation, and picking a wrong disposition either fabricates a manifest row for never-attempted
      data or perpetually hides a real gap. Done when: a disposition is recorded per currently-known-mismatched venue
      (FLUID confirmed, any others found during `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s follow-up
      audit todos) in this plan's Progress Log, with `market-tick-data-service` + `unified-api-contracts` file/symbol
      pointers for the chosen disposition.
- [ ] [DATA] P1. BLOCKED-OPERATOR-DECISION (gated on the P0 todo above) — design the seeder itself: a
      `record_expected_unattempted`-equivalent method on `DefiManifestRecorder`
      (`market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py`), fired from a new DeFi
      enumeration pass mirroring `market_tick_data_service/engine/orchestrator/sentinels.py`'s existing
      `record_expected_unattempted` pattern, with denominator = UAC `DEFI_VENUE_DATA_TYPE_CAPABILITIES` +
      `DEFI_VENUE_PHASE` filtered per the P0 reconciliation's dispositions (never a venue disposed "exclude until
      collector exists"). Write the design as a doc section here (schema of the new manifest rows, where the enumeration
      pass hooks into the DeFi `collect-*` CLI flow, how it avoids double-counting rows a handler already wrote). Done
      when: the design section is written + reviewed, with no open question about how a disposed-exclude venue is
      prevented from getting a stamped row.
- [ ] [DATA] P2. BLOCKED-OPERATOR-DECISION (gated on the P1 design todo above) — implement the seeder per the design,
      unit-tested, wired into the DeFi manifest-write path. Done when: `quality-gates.sh` is green on
      `market-tick-data-service` and a manifest census (deployment-api `_axis_census.py` or equivalent) shows every
      UAC-declared, non-excluded venue-key carrying at least one manifest row (captured or honest
      `expected_unattempted`) for its declared instrument_type family.
- [ ] [DATA] P3. BLOCKED-OPERATOR-DECISION (gated on the P2 implementation todo above) — once the seeder is live,
      re-open `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s C8 checkbox and flip it referencing this plan + the
      census evidence (dropping the unsatisfiable DRIFT-SOLANA criterion permanently, per the 2026-07-16 operator ruling
      that removed DRIFT-SOLANA from every UAC registry).

## Codex SSOTs

- `/codex/02-data/honest-absence-downstream-handling.md` — governing rule for this whole plan (a genuine absence and an
  unattempted state must never collapse into one signal).
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest/`capture_status` contract the new seeder must
  conform to.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § Dispatch-scope eligibility — why the P0 todo
  is human-only.

## Progress Log

- 2026-07-26 (slot 2): Plan created per BLK-3221d4b3's ruling (human plan, `assigned_vm: NA`). No design work started —
  next action is the operator resolving the P0 reconciliation todo.
