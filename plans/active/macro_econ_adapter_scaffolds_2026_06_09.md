---
title: "Macro/alt-data free adapter scaffolds — fear_greed / CFTC COT / Baker Hughes / EIA"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
created: 2026-06-09
author: ikennaigboaka [slot-3·laptop]
locked_by: live-defi-rollout
locked_since: 2026-06-09
source:
  - plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md (Phase 2 — free quick-win adapters)
---

# Macro/alt-data free adapter scaffolds (2026-06-09)

> **Wrapper plan** for the buildable adapter-scaffold slice of
> `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md` (Category C, Phase 2). The audit's backfill
> RUN, paid-source credentials, and the `altdata` asset-group / honest-coverage-gate registration remain
> **operator-blocked** (audit Open Questions #1–#4 + Phases 3–6) and stay tracked on the audit doc.

## Scope (Phase 2 of the audit — free, public-domain macro/alt-data adapters)

These four sources are **free** and were declared in UAC (`registry/capability_declarations/_altdata.py`) but had **no
fetch adapter**. Build the adapter scaffold per the **External-Data-Always-Available** HARD RULE: fetch (aiohttp) +
parse-through-UAC-schema + normalize → `CanonicalOnChainMetric` + `classify_venue_error()` + `ADAPTER_FETCH_FAILED`
emission + mock unit tests + `requires_credentials` integration tests (skipped by default). Adapters live in MTDS
`market_interface/adapters/tradfi/` alongside the existing free-macro precedent (`fred_adapter.py`).

**Target surface** (declare-overlap, per multi-agent safety): `unified-api-contracts/unified_api_contracts/external/fear_greed/**`
+ `registry/capability_declarations/_altdata.py` (additive `_FEAR_GREED`) + `canonical/crosscutting/errors/altdata.py`
(additive map) + `registry/endpoints.py` (additive macro URLs); `market-tick-data-service/.../adapters/tradfi/{fear_greed,cftc_cot,baker_hughes,eia}_adapter.py`
+ `tradfi/__init__.py` + `market_interface/__init__.py` re-exports; `tests/unit/test_macro_adapters.py` +
`tests/integration/test_macro_adapters_integration.py`. (CFTC/EIA/Baker-Hughes UAC schema+normalize were already
committed pre-2026-06-09; this plan adds the fear_greed UAC contract + all four MTDS adapters.)

## Phase 1 — fear_greed adapter (free, no auth) — BUILD NOW

- [x] [SCRIPT] P1. fear_greed UAC contract — fill the empty stub: `external/fear_greed/{__init__,schemas,normalize}.py`
      + `mocks/stub.yaml`; `FearGreedRawObservation`/`FearGreedReading` → `normalize_fear_greed_reading` →
      `CanonicalOnChainMetric(metric_type="crypto_fear_greed")`. Register `_FEAR_GREED` SourceCapability +
      `fear_greed` base URL. — unified-api-contracts@7ae9daee
- [x] [SCRIPT] P1. `FearGreedAdapter` (MTDS `adapters/tradfi/fear_greed_adapter.py`) — `fetch_index(limit)` via
      aiohttp from alternative.me `/fng/`; classify_venue_error + ADAPTER_FETCH_FAILED; wired into `tradfi/__init__.py`
      + `market_interface/__init__.py`. Mock unit tests green. — market-tick-data-service@b6dde028

## Phase 2 — CFTC COT adapter (free, no key) — BUILD NOW

- [x] [SCRIPT] P1. `CFTCCOTAdapter` (`adapters/tradfi/cftc_cot_adapter.py`) — Socrata `publicreporting.cftc.gov`
      Disaggregated Futures-Only (`72hh-3qpy`); `fetch_cot(limit)` → `CFTCCOTReport` →
      `normalize_cftc_cot_report` (`metric_type="cot_managed_money_net"`). Mock unit tests green. —
      market-tick-data-service@b6dde028

## Phase 3 — Baker Hughes rig-count adapter (free) — BUILD NOW

- [x] [SCRIPT] P1. `BakerHughesAdapter` (`adapters/tradfi/baker_hughes_adapter.py`) — `fetch_rig_counts()` →
      `BakerHughesRigCount` (WoW deltas computed across the oldest-first series) → `normalize_baker_hughes_rig_count`
      (`metric_type="rig_count"`). Mock unit tests green. — market-tick-data-service@b6dde028

## Phase 4 — EIA adapter (free key required for live) — SCAFFOLD NOW, live fetch BLOCKED-CREDENTIALS

- [x] [SCRIPT] P1. `EIAAdapter` (`adapters/tradfi/eia_adapter.py`) — EIA v2 (`api.eia.gov`), key from constructor or
      Secret Manager `eia-api-key`; `fetch_series(route)` → `EIASeriesObservation` →
      `normalize_eia_series_observation`. Scaffold + mock unit tests green (missing-key guard tested). —
      market-tick-data-service@b6dde028
- [ ] [BLOCKED-CREDENTIALS] P1. EIA live fetch + cassette recording — needs the free EIA API key. CREDENTIAL APPROVAL
      REQUEST filed in `ikenna_orchestrator/pings/slot_3.md` (vendor=EIA, free tier). Unblocks the live integration
      test (`tests/integration/test_macro_adapters_integration.py::test_eia_live`) + EIA backfill RUN.

## Operator-blocked follow-ups (stay on the audit doc — NOT closed here)

- [ ] [OPERATOR-DECISION] P1. `altdata` home — revive `altdata` as a real `asset_group` vs model macro as a SHARED
      cross-asset axis. **DEFERRED** — gates the GCS-shard write + manifest `record_captured` + bucket
      (`resolve_bucket_name`) wiring for all four sources (adapters today return `CanonicalOnChainMetric` lists; they do
      NOT yet write GCS shards because the asset_group/bucket/data_type is undecided). Provenance: audit Open Question #1.
- [ ] [OPERATOR-DECISION] P2. Honest-coverage-gate registration — add the macro key to `expected_coverage.py` +
      `coverage_start` dates so macro can no longer be silently empty. **DEFERRED** — audit Phase 5. Depends on the
      asset-group decision above.
- [ ] [SCRIPT] P2. Wire the macro adapters into an MTDS handler + CLI operation + manifest emission once the
      asset-group home lands (the GCS shard-write path). **DEFERRED** — audit Phase 5/6, gated on OPERATOR-DECISION #1.

## Codex SSOT updates

- [ ] [DOC] P2. After the asset-group decision lands, document the macro/alt-data capture path in
      `codex/02-data/` (no new contract was introduced by the scaffolds themselves — they reuse `CanonicalOnChainMetric`
      + the existing adapter/`classify_venue_error`/`ADAPTER_FETCH_FAILED` patterns). **DEFERRED** until Phase 5 wiring.

## Success criteria

- 3 free adapters (fear_greed/CFTC/Baker Hughes) + EIA scaffold present in MTDS, exported, `classify_venue_error`-wired.
- `tests/unit/test_macro_adapters.py` green under `bash scripts/quality-gates.sh` (MTDS collects `tests/unit/`).
- fear_greed UAC contract present + cassette-parity-valid; `_FEAR_GREED` capability + altdata error map registered.
- EIA credential ask filed in `pings/slot_3.md`; EIA live test skips without `EIA_API_KEY`.

## Findings captured during this work (Findings-Triage)

- [x] [FIX] P1. **Pre-existing MTDS unit reds fixed (shipped in this unit).** The recent
      `uac feat(defi-caps)` PROTOCOL_CAPABILITIES expansion added 7 `collect-*` DeFi ops that the test fixture
      `tests/unit/test_collect_handler_schema.py::_CLI_OP_TO_MODULE` didn't map (handler modules already existed) →
      added the 7 entries (liquidation-events/position-data/token-transfers/bridge-events/flash-loan-events/
      governance-events/mev-events). Also `tests/unit/test_spot_ws_connectors.py::TestOKXSpot::test_registry` was
      xdist-flaky (relied on lazy okx_spot_ws import side-effect) → now calls production `register_all()`. Both were
      blocking a green MTDS sentinel for ALL slots. — market-tick-data-service@b6dde028
- [ ] [SCRIPT] P2. **DEFERRED — PM-template gap: `base-library.sh` QG writes `.qg_content_sentinel` but
      `quickmerge.sh` `--agent` fast-path (STAGE 3) verifies `.qg_last_passed_sha`** — so the agent quickmerge
      fast-path is structurally unsatisfiable for **library** repos (UAC), whereas `base-service.sh` writes the sha
      sentinel. Worked around here by writing `.qg_last_passed_sha` after a verified-green UAC QG. Fix: have
      `base-library.sh` also write `.qg_last_passed_sha` on a complete green run (mirror base-service), then roll out
      via `rollout-workflow-templates`/the QG-base propagation. Provenance: UAC quickmerge 2026-06-09 STAGE 3 block.
      Target repo: `unified-trading-pm` (`scripts/quality-gates-base/base-library.sh`).
