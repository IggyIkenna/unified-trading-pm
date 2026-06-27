---
doc_type: plan
title: "MTDS LDR fleet-red — cefi MVP-gate tests + thegraph 9-key shard tests fail on current live-defi-rollout"
created: 2026-06-23
source:
  - "market-tick-data-service@fbf3db8 (feat(cefi): gate MTDS capture on MVP capture universe)"
  - "market-tick-data-service@5830cc8 (thegraph key count 20→9)"
locked_by: live-defi-rollout
priority: P2
status: active
summary: While shipping the DeFi per-pool writer fix (`defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md`), the MTDS `quality-gates.sh --no-fix` over the **whole tree** surfaced **~54 pre-existin...
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

## What I found

While shipping the DeFi per-pool writer fix (`defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md`), the MTDS
`quality-gates.sh --no-fix` over the **whole tree** surfaced **~54 pre-existing test failures on current
`live-defi-rollout`** (proven pre-existing: they fail with ALL my changes stashed on a freshly-pulled clean LDR tree).
They split into two classes:

1. **thegraph 9-key shard tests (DeFi-domain — I FIXED these in my ship unit):**
   `tests/market_interface/unit/test_thegraph_client_logic.py::TestGetKeyNumberForShard::*` asserted the OLD 20-key
   wrap (`shard_9→10`, `shard_20→1`) but the code was correctly changed to a **9-key round-robin**
   (`(shard % 9) + 1`) at mtds@5830cc8 (codex defi-canonical DURABLE gotcha #5 — the 9-key TheGraph pool). Stale-test
   drift. **Fixed in the defi writer ship** (tests updated to 9-key: `shard_9→1`, `shard_19→2`, `shard_20→3`, range 1–9).

2. **cefi MVP-capture-gate tests (FOREIGN — not fixed here, filed for the cefi/mvp owner):**
   `tests/unit/engine/test_cefi_catalog_reader_mvp_gate.py::{test_reader_yields_only_mvp_universe,test_row_in_mvp_capture_universe_perp_gate}`
   + `tests/unit/scripts/test_reclassify_cefi_manifest_mvp_universe.py::{test_out_of_mvp_rows_removed,test_legit_and_captured_and_failed_preserved}`
   + several integration tests (kalshi/polymarket/tardis/databento/extended-starknet/vcr) all trace to mtds@fbf3db8
   (`feat(cefi): gate MTDS capture + reclassify on the MVP capture universe (perp-gated SSOT)`). The cefi reader yields
   `UPBIT` (non-MVP venue) when the test expects only the perp-gated MVP universe → `is_in_mvp_capture_universe` (UAC
   SSOT) is not gating as the MTDS code at fbf3db8 expects. Likely a **cross-repo UAC↔MTDS version-skew** (a UAC
   `_backmerge` 6d215c1b landed after fbf3db8) OR the fbf3db8 commit shipped with red tests.

## Why it matters

These reds are on the integration branch (LDR), so any MTDS `quality-gates.sh` whole-tree run is red → blocks the
quickmerge sentinel for EVERY MTDS shipper until reconciled. It is NOT caused by the DeFi per-pool writer change
(stash-baseline proven). The cefi MVP-gate is also the denominator gate for cefi honest-coverage — if it mis-gates
UPBIT in, the cefi coverage % is wrong.

## UPDATE 2026-06-23 (autonomous session — partial reconcile)

Triaged the full 38-failure set. Categorized + actioned:
- **28 `test_vcr_ac_schema_validation.py` — FIXED (this session, mtds).** Root cause: a **hardcoded macOS absolute
  `CASSETTE_DIR = Path("/Users/ikennaigboaka/Code/.../unified_api_contracts/external")`** at line 23 → on any non-macOS
  clone (Linux VM/CI) VCR can't find the cassette → tries to record → `CannotOverwriteExistingCassetteException` in
  `record_mode="none"`. THIS is the recurring "38 pre-existing failures" (mtds@a156caf). Fixed: resolve the UAC
  `external/` dir portably via `importlib.util.find_spec("unified_api_contracts")` (the installed editable dep, present
  in every clone) + a sibling-repo fallback. 30 passed / 5 skipped after the fix.
- **3 `test_databento_adapter_logic.py` — FOREIGN (tradfi/databento UAC allowlist skew).** Tests trip
  `DatabentoSchemaNotAllowedError`/`DatabentoBatchApiBannedError` from the UAC `databento_subscription_allowlist` —
  a UAC↔MTDS expectation skew, NOT a DeFi concern. Owner: tradfi/databento.
- **1 `test_tardis_options_adapter.py::test_tardis_options_real_fetch` — FOREIGN + INTENTIONAL.**
  `NotImplementedError: scaffold ... after operator ACKs the Tardis credential request` — a `BLOCKED-CREDENTIALS`
  scaffold test, expected-red until creds. Owner: cefi/tardis.
- **4 cefi MVP-gate (`test_cefi_catalog_reader_mvp_gate.py` ×2 + `test_reclassify_cefi_manifest_mvp_universe.py` ×2) —
  FOREIGN (cefi MVP perp-gate UAC skew, mtds@fbf3db8).** Owner: cefi/mvp-universe.

Net: 28 fixed here; **10 residual foreign reds** (databento 3 + tardis 1 + cefi-mvp 4 + 2 reclassify) belong to the
tradfi/cefi owners — they block the MTDS whole-tree local QG sentinel until those owners reconcile their UAC skews. The
DeFi per-pool writer ship is verified green against the genuine suite (7521 passed with only these 10 foreign files
excluded) and ships with the cassette-path fix.

## UPDATE 2026-06-23 (correction — the GATED scope is `tests/unit/`, RUN_INTEGRATION=false)

The MTDS `scripts/quality-gates.sh` gates ONLY `tests/unit/` with `RUN_INTEGRATION=false` (verified). So the VCR /
databento-write / polymarket / extended-starknet / tardis failures (under `tests/integration/` + `tests/market_interface/`)
are OUTSIDE the gate (they're the SIT/live layer, credential/network-dependent — correctly not gated locally). The VCR
cassette-path fix (this session) is still a good fleet hygiene fix and shipped, but those files weren't gating.

**The actual GATED (`tests/unit/`) foreign reds = 5, all cefi (none DeFi, none mine):**
- `tests/unit/engine/test_cefi_catalog_reader_mvp_gate.py` ×2
- `tests/unit/scripts/test_reclassify_cefi_manifest_mvp_universe.py` ×2
- `tests/unit/test_perp_funding_normalization.py::test_hyperliquid_and_aster_positive_rates_same_sign` ×1

All trace to the cefi MVP-perp-gate UAC skew (mtds@fbf3db8) — a cefi-track / UAC-version reconcile, NOT DeFi. The DeFi
per-pool writer ship is verified green on `tests/unit/` with ONLY these 5 foreign cefi files deselected (5,333 passed),
so it ships with the 5 documented-foreign reds deselected from the sentinel run. Owner: cefi/mvp-universe track.

## UPDATE 2026-06-23 (peer resolved most cefi reds mid-session)

A peer landed `mtds@d2052c7 test(cefi): update MVP gate tests for UAC v8 UPBIT perp-gate-exempt` during this session —
which RESOLVED 4 of the 5 gated cefi reds (`test_cefi_catalog_reader_mvp_gate` ×2 + `test_reclassify_cefi_manifest_mvp_universe`
×2 now PASS). The cefi MVP-gate UAC↔MTDS skew is therefore reconciled upstream. **1 residual gated foreign red:**
`tests/unit/test_perp_funding_normalization.py::TestAsterFundingNormalization::test_funding_rate_column_present_and_decimal`
(aster perp-funding column normalization — foreign cefi/perp, pre-existing on LDR, not DeFi). The DeFi per-pool writer
ship deselects only this 1 remaining foreign red for its sentinel run. Owner: cefi/perp-funding track. The foreign
`tardis_symbol_resolution.py` WIP that was dirty in the shared clone is stashed (`foreign-tardis-wip-2-defi-session`).

## Recommended decision

- thegraph shard tests: RESOLVED in the defi writer ship (mtds, this session).
- cefi MVP-gate + integration reds: the cefi/mvp-universe owner reconciles the UAC↔MTDS skew (confirm the installed UAC
  `is_in_mvp_capture_universe` gates non-MVP venues like UPBIT; re-pin/re-lock if a backmerge regressed it; or fix the
  fbf3db8 test fixtures if the gate intentionally changed). Until then the MTDS whole-tree gate stays red on these
  foreign tests — a DeFi-only shipper must scope-verify its own touched tests + ship via `quickmerge --files`.
