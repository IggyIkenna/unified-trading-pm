---
doc_type: issue
title: AAVE-PLASMA flipped to phase=live in UAC without an IS instrument-discovery producer — fleet-wide QG red
summary: >-
  unified-api-contracts flipped AAVE-PLASMA's DEFI_VENUE_PHASE from "pipeline" to "live" (2026-08-01,
  defi_plasma_chain_onboarding_gap_2026_07_26.md P3) based on MTDS's lending_indices RPC capture verifying 18 real rows
  — but that capture path is separate from instruments-service's reference-data/instrument-discovery layer.
  instruments-service's _build_defi_venues() has no producer for AAVE-PLASMA (its aave_v3 IS adapter is subgraph-only
  via factory.py's ADAPTER_DATA_SOURCE mapping ("aave_v3": "thegraph"), and Plasma has no subgraph — RPC-only fallback
  per the same doc's P2 scoping). This breaks the denominator drift-guard invariant fleet-wide in instruments-service's
  quality-gates.sh, blocking every unrelated commit from shipping via quickmerge --agent.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [honest-coverage, denominator-drift, defi, plasma, aave, qg-red, instruments-service]
related:
  [
    /plans/archive/issues/defi_plasma_chain_onboarding_gap_2026_07_26.md,
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-01
last_updated: 2026-08-01
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
assigned_role: data_engineering
drift_direction: advance-code
resolved_by: instruments-service@a340e34c
locked_by:
source: >-
  Discovered 2026-08-01 (slot-10, data_engineering craft) while shipping an unrelated instruments-service change (real
  column-prune streaming refactor of measure_honest_coverage.py, defi_consolidated_native_ao_extract-002) —
  quality-gates.sh's full run failed on 2 tests wholly outside that change's scope. Investigated to confirm pre-existing
  + find root cause rather than blindly filing a repo-blocker.
depends_on: []
---

# AAVE-PLASMA denominator drift — IS has no instrument-discovery producer

## What I found

`unified-api-contracts` flipped `AAVE-PLASMA`'s `DEFI_VENUE_PHASE` `"pipeline"` → `"live"` today
(`unified-api-contracts@06c54fee`, per `defi_plasma_chain_onboarding_gap_2026_07_26.md`'s now-archived P3 todo) and
registered `VENUE_TO_ADAPTER_KEY["AAVE-PLASMA"] = "aave_v3"` (`@18ed167f`). The justification cited was MTDS-side:
`market-tick-data-service`'s `lending_indices_handler.py`/`lending_indices_rpc.py` RPC path captured 18 real
`venue=AAVE_V3, chain=PLASMA` rows into the manifest, `capture_status=captured`, `date=2026-07-30`.

That capture path is **NOT** the same subsystem as `instruments-service`'s reference-data / instrument-universe
discovery layer (per this workspace's `instruments-service owns reference data; MTDS is market-data only` split).
`instruments-service/instruments_service/engine/orchestrator/defi.py::_build_defi_venues()` has no producer for
`AAVE-PLASMA` at all — it's neither in `_SUBGRAPH_PROTOCOL_TO_VENUE_PREFIX`'s auto-gen loop (no `subgraph_id` exists for
Plasma — confirmed RPC-only fallback, same class of gap as `RADIANT-BSC`'s explicit `venue_adapter_keys.py` comment
already documents) nor in `_STATIC_DEFI_VENUES`.

**I verified — did not guess — that a naive one-line add to `_STATIC_DEFI_VENUES` would be WRONG**:
`instruments_service/reference_data/factory.py` line 235 maps `"aave_v3": "thegraph"` — the IS `aave_v3` reference-data
adapter (`adapters/defi/aave_v3.py`, `AaveV3ReferenceDataAdapter`) is subgraph-only. Plasma has no subgraph_id
(confirmed in `defi_plasma_chain_onboarding_gap_2026_07_26.md`'s own P2 scoping — RPC-only). Requesting `AAVE-PLASMA`
through the normal orchestrator/factory path would either raise or return 0 instruments, exactly the
"expected-but-always-empty pollutes honest-coverage" anti-pattern this same file's own comments warn against for
METEORA-SOLANA/LIFINITY-SOLANA/PHOENIX-SOLANA (dead-upstream case) and the Phase-4 BEEFY/YEARN chain exclusions
(empty-registry case).

**Fleet-wide impact, confirmed on a clean tree**: `instruments-service`'s `quality-gates.sh` currently fails 2 tests for
every commit on `live-defi-rollout`, regardless of what the commit touches:

- `tests/unit/test_orchestrator_helpers.py::TestVenueProducerUACInvariant::test_defi_set_equals_uac_denominator_drift_guard`
  — `UAC-only (denominator re-widened): {'AAVE-PLASMA'}`.
- `tests/unit/test_pipeline_e2e_prediction.py::test_rule11_per_ag_dedup_target_counts_byte_unchanged` —
  `DEFI dedup'd target count drifted: 101 != 100` (same root cause: UAC's defi denominator now enumerates one more venue
  than IS's `_build_defi_venues()` produces).

Both failures trace to the SAME single root cause (verified via `git show HEAD~1:<path>` byte-identical on both test
files — confirmed pre-existing, not introduced by my own commit `ee12b692`). Not filing this against
`defi_venue_pipeline_to_live_ao_build_2026_07_30.md` — that plan is fully checked off and scoped to the 6 OTHER venues
(ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER); AAVE-PLASMA is a fresh, separate occurrence of the same drift class,
introduced by a same-day phase flip that landed without the IS-side producer work.

## Why it matters

**Fleet-wide QG red**: every instruments-service commit — unrelated to DeFi venues entirely — is currently blocked from
shipping via `quickmerge --agent` (the sentinel requires a fully-green `quality-gates.sh` run). Filed repo-blocker
`RB-151dfbac` (slot-10) as the passive wait mechanism; this issue doc is the actionable fix Trigger the
`RepoHealthWatcher`'s green signal depends on.

**Data-correctness angle**: even if IS's `_build_defi_venues()` stays silent on `AAVE-PLASMA` (a legitimate outcome —
not every UAC-live venue needs IS instrument discovery if MTDS's RPC capture is a standalone data source), the
denominator drift-guard test's CURRENT design assumes `IS producer set == UAC live-venue set` unconditionally. If
`AAVE-PLASMA`'s honest answer is "MTDS captures it via RPC without an IS reference-data producer," the test itself needs
an explicit documented exemption (mirroring the existing `test_sports_exempt_is_disjoint_from_uac_sports` Decision-C
precedent) — not a silent skip.

## Recommended decision

Two possible resolutions — needs a real investigation/judgment call, not a blind guess:

1. **Build a genuine RPC-based IS instrument-discovery adapter path for `aave_v3`+Plasma** (mirroring MTDS's own
   `lending_indices_rpc.py` RPC pattern, adapted for IS's reference-data-adapter interface), then add `AAVE-PLASMA` to
   `_STATIC_DEFI_VENUES` once that producer genuinely returns ≥1 real instrument (same bar every other
   `_STATIC_DEFI_VENUES` entry's comment cites).
2. **OR** determine AAVE-PLASMA is legitimately IS-non-producible (MTDS-only data source, no IS reference-data
   instrument-discovery concept applies to it) and add a scoped, documented exemption to
   `test_defi_set_equals_uac_denominator_drift_guard` (same class as the sports exemption) plus a matching fix to
   `test_rule11_per_ag_dedup_target_counts_byte_unchanged`'s hardcoded count.

- [x] ✅ [DATA] P1. Investigate which of the two resolutions above is correct for AAVE-PLASMA (read
      `adapters/defi/aave_v3.py` + `lending_indices_rpc.py` closely; consult the Aave Plasma market's actual on-chain
      shape — is there a per-market instrument concept distinct from the lending-rate time series MTDS already
      captures?), then implement it: either the genuine RPC producer (option 1) or the documented test exemption (option
      2). Repo: instruments-service (+ unified-api-contracts if option 1 needs a `venue_adapter_keys.py` correction).
      **Done when**: `quality-gates.sh` green in instruments-service with both
      `test_defi_set_equals_uac_denominator_drift_guard` and `test_rule11_per_ag_dedup_target_counts_byte_unchanged`
      passing (fixed forward, not skipped), and `RB-151dfbac` resolves. — **instruments-service@a340e34c**: resolved
      **Option 1** (genuine RPC producer) — read `aave_v3.py`'s existing OPTIMISM static-fallback +
      `lending_indices_rpc.py` closely and confirmed AAVE-PLASMA DOES have a real per-market instrument concept
      (aToken/debtToken per reserve, same as every other AAVE_V3-* venue) discoverable via the SAME
      `AaveProtocolDataProvider.getAllReservesTokens()` RPC call MTDS already uses against this exact contract (proven
      working, 18 rows captured); Option 2's exemption premise ("no IS instrument-discovery concept applies") was
      verified FALSE, so building the exemption would have been dishonest. Added
      `AaveV3ReferenceDataAdapter._get_plasma_reserves_via_rpc()` (routes `chain=="PLASMA"` before the subgraph path) +
      a new `aave_v3_plasma_rpc.py` module (web3.py Contract walk against `getAllReservesTokens` +
      `getReserveTokensAddresses` + `getReserveConfigurationData`, isolated into its own file so its inherently dynamic
      typing doesn't loosen the rest of `aave_v3.py`'s basedpyright baseline — same split MTDS itself used). Total-fetch
      failure raises (honest `attempted_failed`, not `empty_confirmed`); a single reserve's detail-call failure is
      shard-isolated (log + skip). 9 new unit tests (mocked `web3.Web3`, no live network) all green. Full
      `quality-gates.sh`: PASSED (155s) — both cited tests pass; `RB-151dfbac` should already read resolved via
      slot-11's earlier fix (2de31f0d) which is what actually turned the fleet-wide QG green.

## Progress Log

- 2026-08-01 (slot-10, data_engineering craft): Filed while blocked shipping an unrelated change
  (`defi_consolidated_native_ao_extract_2026_07_25.md`'s DATA P2 honest-coverage streaming refactor,
  `instruments-service@ee12b692`, committed locally, not yet pushed). Investigated root cause instead of blindly
  waiting; confirmed a naive `_STATIC_DEFI_VENUES` one-liner would be WRONG (subgraph-only adapter, Plasma has no
  subgraph) so did not attempt the fix myself — out of craft/task scope, genuine judgment call. Repo-blocker
  `RB-151dfbac` stays open as the passive wait mechanism.
- 2026-08-01 (slot-14, data_engineering craft): Dispatched the P1 todo above. Found slot-11 had already landed
  `instruments-service@2de31f0d` in the interim (fleet-wide QG-red fix: added `AAVE-PLASMA` to `_STATIC_DEFI_VENUES`
  - bumped the DEFI dedup count 100→101 — this is what actually resolved `RB-151dfbac`'s fleet-blocking urgency). That
    fix satisfied the denominator-SET equality test but left the deeper gap this issue's own "Why it matters" section
    called out: `aave_v3.py`'s `get_instruments()` has no chain routing for `PLASMA` (only `OPTIMISM`), so it fell
    through to the subgraph path, which returns `[]` for Plasma (no subgraph_id) — a genuine expected-but-always-empty
    producer, silently returning 0 instruments forever. Investigated + resolved per the todo above (Option 1, genuine
    RPC producer) — see the todo's own resolution note for the full technical detail. Shipped
    `instruments-service@a340e34c` (verified on origin), full `quality-gates.sh` green. Status → resolved.
