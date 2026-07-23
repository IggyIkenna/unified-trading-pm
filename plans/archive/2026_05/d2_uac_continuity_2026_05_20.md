---
doc_type: plan
title: D2 — UAC continuity + known-gap calendars + expected_coverage integration
summary:
status: complete
nature: record
asset_group: [sports]
stage: [meta]
repos: [execution-service, features-service, instruments-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/honest_coverage_formula_consolidation_2026_05_19.md,
    /plans/archive/2026_05/d3_manifest_v8_finish_2026_05_20.md,
    /plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md,
  ]
created: 2026-05-20
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
source_audits:
  [plans/audit/results/expected_coverage_dump_2026_05_20.parquet, plans/audit/uac_consumer_contract_audit_2026_05_20.md]
parent_epic: sports_master
---

# D2 — UAC continuity + known-gap calendars + expected_coverage integration

> **Ordering step 2** in the Phase-E execution chain. Can run in parallel with D1.
>
> A2 audit (2026-05-20) built `expected_coverage()` function in UAC (`registry/expected_coverage.py`) and produced a
> 429,088-row dump (`expected_coverage_dump_2026_05_20.parquet`). This plan wires that function into the runtime
> pipeline: pre-flight gates check it before each shard, and post-hoc divergence-detector uses it to flag
> DIVERGENT_EMPTY cells.

## What this covers

1. **UAC deep-import violations**: C9 found 49 prod files using `canonical.*` deep paths (not root facade)
2. **UAC_CANONICAL_EXEMPT bypass**: execution-service + IS-service bypass UAC import surface via exempt flag
3. **expected_coverage() runtime integration**: wire preflight + post-hoc into each service's batch handler
4. **Known-gap calendar decisions**: 5 open decisions from A2 sidecar (sports off-seasons, DeFi protocol pauses, etc.)

## P0 findings from audits

### From C9 (All → UAC)

| Finding                                                                                                           | Severity | Description                                                        |
| ----------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------ |
| execution-service + IS-service set `UAC_CANONICAL_EXEMPT=true` in QG — bypasses import surface check              | P0-C9-1  | QG bypass enables undetected deep imports                          |
| 49 prod files across workspace with `from unified_api_contracts.canonical.*` deep imports                         | P0-C9-2  | A1 CSV confirms `uac_import_surface` = 995 violations              |
| features-service: `from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason` | P0-C9-3  | Should be `from unified_api_contracts import EmptyConfirmedReason` |

### From A2 (expected_coverage function + dump)

| Finding                                                                                | Severity | Description                                                                                                                          |
| -------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 5 known-gap calendar decisions left open in sidecar doc                                | P1       | sports off-seasons, DeFi protocol pauses, per-symbol axis, `SourceCapability.coverage_start` integration, pre-Tardis-archive windows |
| expected_coverage() not yet wired into any service's batch handler preflight           | P0       | Function built; not yet consumed                                                                                                     |
| DIVERGENT_EMPTY post-hoc check requires QG integration test harness (deferred from D3) | P1       | runtime-only; see D3 for tooling                                                                                                     |

## Remediation backlog (ordered)

### Phase 1 — UAC import surface compliance

- [x] [AGENT] P0. Remove `UAC_CANONICAL_EXEMPT=true` from execution-service `quality-gates.sh`: ✅ —
      execution-service@a848ef61 (12 deep imports fixed across engine/defi/sports adapters; QG STEP 5.23 clean)
- [x] [AGENT] P0. Remove `UAC_CANONICAL_EXEMPT=true` from IS-service `quality-gates.sh`: ✅ —
      instruments-service@b476663 + UAC@ceeaddd (5 IS files fixed; POLYMARKET_MARKET_TO_CANONICAL +
      slugify_canonical_name added to sports facade; QG STEP 5.23 clean)
- [x] [AGENT] P1. Sweep top 49 deep-import violations: ✅ — prod source across all repos = 0 violations
      (execution-service 12 files + IS 5 files fixed in P0; features-service/strategy-service/MTDS prod source was
      already 0). Residual violations in test/scripts are not in scope for QG STEP 5.23 $SOURCE_DIR scan.

### Phase 2 — Known-gap calendar decisions (A2 sidecar)

- [x] [OPERATOR/AGENT] P1. Resolve 5 open calendar decisions from `expected_coverage_calendar_decisions_2026_05_20.md`:
      ✅ — UAC@8565c87
  1. Sports off-seasons: ✅ Documented in KNOWN_COVERAGE_GAPS comment — per-league seasonal gaps handled by
     `get_league_fixture_calendar()` + `SEASON_BY_COUNTRY` (fixture-calendar level); KNOWN_COVERAGE_GAPS reserved for
     source-level provider outages; oracle per-league integration deferred to Decision 3.
  2. DeFi protocol pauses: ✅ `protocol_pause_windows.py` architecture complete (detector-derived from on-chain
     governance events per operator directive 2026-05-20 round 4); oracle gate wired; registry populates from daily
     detector run.
  3. Per-symbol axis: ✅ DEFERRED — per temporary states: oracle stays per-(asset_group, venue, data_type); per-symbol
     requires IS catalogue integration (named successor: integrate per-symbol axis after IS hardening ships).
  4. `SourceCapability.coverage_start` integration: ✅ Already wired in oracle via `is_before_source_coverage_start()`.
     Tardis dates now populated in capability declarations for all 8 in-scope CeFi venues.
  5. Pre-Tardis-archive windows: ✅ coverage_start added to \_cefi.py for BINANCE (2019-01-01), BYBIT (2019-01-01), OKX
     (2020-01-01), COINBASE (2019-01-01), DERIBIT (2019-01-01), UPBIT (2019-06-01), HYPERLIQUID (2023-06-14), ASTER
     (2024-09-25); all Tardis data types (trades, book_snapshot_5, derivative_ticker, liquidations, options_chain,
     futures_chain) where applicable.
- [x] [AGENT] P1. Implement decisions 1, 2, 4, 5 as UAC constant updates in
      `registry/capability_declarations/_cefi.py` + `canonical/domain/sports/league_data.py`: ✅ — UAC@8565c87 (8 CeFi
      venue coverage_start + sports design decision comment; QG 2850 passed clean)

### Phase 3 — expected_coverage() preflight wiring

- [x] [AGENT] P0. Wire `expected_coverage()` preflight into each service's batch handler: ✅ — MTDS@2b63dc6
  - Pattern: before writing a shard, call `expected_coverage(asset_group, venue, data_type, date)` → check result
  - If `EXPECTED_EMPTY:<reason>` → call `record_empty(reason=<typed_reason>)` immediately; skip compute
  - If `NOT_YET_LIVE` → call `record_empty(reason=<oracle_reason>)` immediately; skip
  - If `SHOULD_HAVE_DATA` → proceed with compute; any failure → `record_failed` not silent skip
  - MTDS `lending_indices_handler.py`: replaces `get_protocol_launch_date()` with oracle; 4 oracle-mock unit tests added
    (TestOraclePreflight); 22 tests pass; QG green.
  - IS, features-service, strategy-service: **DEFERRED** pending D2 Phase 3 P1 (DIVERGENT_EMPTY detector) and IS
    hardening (D1). Named successor: wire oracle into IS batch handlers after D1 IS catalogue lands.
- [x] ✅ [AGENT] P1. Wire DIVERGENT_EMPTY post-hoc check into divergence-detector script
      (`detect_manifest_divergence.py` from D3 Phase 4):
  - Use `expected_coverage()` as the oracle (not static CSV)
  - Emit `DIVERGENT_EMPTY` event when manifest shows 0 rows but `expected_coverage()` returns `SHOULD_HAVE_DATA` — DONE
    2026-05-21: UTL@0d1e489f. `_build_oracle_expected()` calls `expected_coverage()` per (venue, data_type, date); date
    range derived from manifest min/max or explicit `--start-date`/`--end-date`. Legacy `--expected-coverage` parquet
    mode retained for backward compat. 17 unit tests: classify logic, oracle builder, DIVERGENT_EMPTY integration. Ruff
    clean; QG tests PASSED (pre-existing prod-readiness soft-fail unchanged).

## Success criteria

- [x] Phase 1: `UAC_CANONICAL_EXEMPT` removed from both QG files; `rg 'UAC_CANONICAL_EXEMPT' --type sh` returns 0 hits;
      QG passes clean ✅
- [x] Phase 2: 5 calendar decisions documented + implemented in UAC constants; `expected_coverage()` 14 unit tests still
      pass post-update ✅ — UAC@8565c87 (QG 2850 passed; 2 new Binance coverage_start tests added)
- [x] Phase 3 (MTDS): `rg 'expected_coverage' market-tick-data-service/ --type py` returns hits in
      `lending_indices_handler.py`; MTDS QG green; 22 tests pass ✅ — MTDS@2b63dc6
  - IS, features-service, strategy-service: deferred to named successor (IS hardening D1 prerequisite)
- [x] Phase 3 (divergence-detector oracle): `detect_manifest_divergence.py` calls `expected_coverage()` directly; oracle
      generates per-cell expected state (not static CSV); 17 unit tests including DIVERGENT_EMPTY integration ✅ —
      UTL@0d1e489f

## Full-execution criterion

> MTDS batch handler for one DeFi shard calls `expected_coverage()` in preflight: date before
> `SourceCapability.coverage_start` returns `NOT_YET_LIVE` → `record_empty(EXPECTED_NOT_YET_LIVE)`; date within range
> returns `SHOULD_HAVE_DATA` → compute proceeds. Verified via unit test with mocked oracle. UAC QG exempt flags removed;
> no `canonical.*` deep imports in execution-service or IS-service.

## Temporary states + their canonical follow-up plans

- Per-symbol axis decision deferred pending operator input (decision 3 from A2 sidecar): expected_coverage() is
  initially per-(asset_group, venue, data_type) not per-symbol. Per-symbol would require IS instrument catalogue
  integration. Named successor: integrate per-symbol axis after IS hardening (D1) ships IS catalogue reads to downstream
  services.
- DIVERGENT_EMPTY QG integration test harness: deferred to D3 Phase 4 tooling — runtime-only detection not yet wired to
  QG STEP. Acceptable for May-23; post-cutover QG step added.
