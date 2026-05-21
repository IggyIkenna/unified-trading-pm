---
name: d2-uac-continuity-2026-05-20
title: D2 — UAC continuity + known-gap calendars + expected_coverage integration
created: 2026-05-20
author: ikenna (slot-8)
status: active
priority: P0
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
parent_plan: master_to_live_defi_2026_05_23.md
source_audits:
  - plans/audit/results/expected_coverage_dump_2026_05_20.parquet # A2
  - plans/audit/uac_consumer_contract_audit_2026_05_20.md # C9
related_plans:
  - honest_coverage_formula_consolidation_2026_05_19.md
  - d3_manifest_v8_finish_2026_05_20.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
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

- [x] [AGENT] P0. Remove `UAC_CANONICAL_EXEMPT=true` from execution-service `quality-gates.sh`: ✅ — execution-service@a848ef61 (12 deep imports fixed across engine/defi/sports adapters; QG STEP 5.23 clean)
- [x] [AGENT] P0. Remove `UAC_CANONICAL_EXEMPT=true` from IS-service `quality-gates.sh`: ✅ — instruments-service@b476663 + UAC@ceeaddd (5 IS files fixed; POLYMARKET_MARKET_TO_CANONICAL + slugify_canonical_name added to sports facade; QG STEP 5.23 clean)
- [ ] [AGENT] P1. Sweep top 49 deep-import violations (A1 CSV:
      `plans/audit/results/codified_shape_compliance_2026_05_20.csv`):
  - Focus: files in execution-service, IS-service, features-service (highest violation count repos)
  - Fix: `from unified_api_contracts import X` for every `canonical.*` deep path

### Phase 2 — Known-gap calendar decisions (A2 sidecar)

- [ ] [OPERATOR/AGENT] P1. Resolve 5 open calendar decisions from `expected_coverage_calendar_decisions_2026_05_20.md`:
  1. Sports off-seasons: codify per-league off-season date ranges as `EXPECTED_EMPTY` in UAC calendar
  2. DeFi protocol pauses: codify known Aave v2/v3 pause events as `EXPECTED_EMPTY`
  3. Per-symbol axis: decide whether `expected_coverage()` is per-asset_group or per-(asset_group, symbol)
  4. `SourceCapability.coverage_start` integration: wire each adapter's `coverage_start` date into the oracle (so dates
     before `coverage_start` are `NOT_YET_LIVE` not `MISSING_EXPECTED`)
  5. Pre-Tardis-archive windows: codify Tardis historical coverage start date per venue
- [ ] [AGENT] P1. Implement decisions 1, 2, 4, 5 as UAC constant updates in `registry/data_source_continuity.py` +
      `registry/expected_coverage.py`

### Phase 3 — expected_coverage() preflight wiring

- [ ] [AGENT] P0. Wire `expected_coverage()` preflight into each service's batch handler:
  - Pattern: before writing a shard, call `expected_coverage(asset_group, venue, data_type, date)` → check result
  - If `EXPECTED_EMPTY:<reason>` → call `record_empty(reason=<typed_reason>)` immediately; skip compute
  - If `NOT_YET_LIVE` → call `record_empty(reason=EmptyConfirmedReason.EXPECTED_NOT_YET_LIVE)` immediately; skip
  - If `SHOULD_HAVE_DATA` → proceed with compute; any failure → `record_failed` not silent skip
  - Services to wire: MTDS (highest priority), IS, features-service, strategy-service
- [ ] [AGENT] P1. Wire DIVERGENT_EMPTY post-hoc check into divergence-detector script (`detect_manifest_divergence.py`
      from D3 Phase 4):
  - Use `expected_coverage()` as the oracle (not static CSV)
  - Emit `DIVERGENT_EMPTY` event when manifest shows 0 rows but `expected_coverage()` returns `SHOULD_HAVE_DATA`

## Success criteria

- [ ] Phase 1: `UAC_CANONICAL_EXEMPT` removed from both QG files; `rg 'UAC_CANONICAL_EXEMPT' --type sh` returns 0 hits;
      QG passes clean
- [ ] Phase 2: 5 calendar decisions documented + implemented in UAC constants; `expected_coverage()` 14 unit tests still
      pass post-update
- [ ] Phase 3: `rg 'expected_coverage' market-tick-data-service/ --type py` returns hits in batch handlers; preflight
      wired for at least MTDS + IS

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
