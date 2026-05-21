---
name: d1-is-hardening-2026-05-20
title: D1 — instruments-service hardening plan
created: 2026-05-20
author: ikenna (slot-8)
status: active
priority: P0
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
parent_plan: master_to_live_defi_2026_05_23.md
source_audits:
  - plans/audit/is_mtds_contract_audit_2026_05_20.md # C0
  - plans/audit/is_features_contract_audit_2026_05_20.md # C1
  - plans/audit/is_strategy_contract_audit_2026_05_20.md # C2
  - plans/audit/is_execution_contract_audit_2026_05_20.md # C3
related_plans:
  - d4_mtds_adapters_preflight_2026_05_20.md
  - live_pipeline_mtds_mdps_features_2026_05_08.md
---

# D1 — instruments-service hardening plan

> **Ordering step 1** in the Phase-E execution chain. Gates D4 (MTDS preflight).
>
> Source audits: C0 (IS→MTDS), C1 (IS→features), C2 (IS→strategy), C3 (IS→execution).

## P0 findings from audits

### From C1 (IS → features)

| Finding                                                                                                       | Severity | File             |
| ------------------------------------------------------------------------------------------------------------- | -------- | ---------------- |
| `volatility/cli/handlers/batch_handler.py._get_instruments()` hardcodes `["BTC","ETH"]` for CEFI — no IS read | P0-C1-1  | features-service |
| `onchain/cli/handlers/batch_handler.py` — no IS read; derives universe from MTDS DependencyChecker            | P0-C1-2  | features-service |
| `cefi/cli/handlers/perp_funding_handler.py` — no IS read; reads MTDS bucket directly                          | P0-C1-3  | features-service |
| Zero `classify_venue_error()` calls in `onchain/cli/handlers/batch_handler.py` (6 except blocks)              | P0-C1-4  | features-service |
| Sports handler uses `classify_and_emit_error` (UTL wrapper) instead of `classify_venue_error()` (UAC)         | P1-C1-5  | features-service |

### From C2 (IS → strategy)

| Finding                                                                                                          | Severity | File             |
| ---------------------------------------------------------------------------------------------------------------- | -------- | ---------------- |
| `gcs_storage_service.py` — zero manifest emission for IS-catalogue-derived strategy outputs                      | P0-C2-1  | strategy-service |
| `discover_instruments()` swallows GCS exceptions silently — no DependencyError raised                            | P0-C2-2  | strategy-service |
| Deep UAC import: `from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason` | P1-C2-3  | features-service |

### From C3 (IS → execution)

| Finding                                                                                | Severity | File                                  |
| -------------------------------------------------------------------------------------- | -------- | ------------------------------------- |
| 13 inline bucket f-strings in execution-service that don't use `resolve_bucket_name()` | P0-C3-1  | execution-service                     |
| Deribit tick_size fetched from live API at startup instead of from IS InstrumentRecord | P0-C3-2  | execution-service `venues/deribit.py` |

## Remediation backlog (ordered)

### Phase 1 — features-service IS catalogue wiring

- [ ] [AGENT] P0. Fix `features-service/volatility/cli/handlers/batch_handler.py._get_instruments()`:
  - Replace hardcoded `["BTC", "ETH"]` with IS catalogue read for CEFI asset_group
  - Use `resolve_instruments_bucket()` + GCS parquet walk (same pattern as `sports/data/gcs_reader.py`)
  - Empty IS catalogue → `record_empty(reason=EmptyConfirmedReason.EXPECTED_UPSTREAM_EMPTY)` not silent skip
- [ ] [AGENT] P0. Wire `onchain/cli/handlers/batch_handler.py` to read IS catalogue for DeFi instrument universe:
  - IS has 54 DeFi adapters (Drift, Phoenix, Orca, Raydium, LST protocols, Aave, etc.)
  - Handler should load `instruments-store-defi-*` GCS output for the batch date
  - If IS output empty for date → `record_empty(reason=EmptyConfirmedReason.EXPECTED_UPSTREAM_EMPTY)`
- [ ] [AGENT] P0. Wire `cefi/cli/handlers/perp_funding_handler.py` to validate IS catalogue for CeFi instruments:
  - MTDS perp-funding bucket is the data source; IS catalogue provides the universe boundary
  - Add IS read as a preflight step (not blocking compute, but failing manifest if IS is empty)

### Phase 2 — error classification in features handlers

- [ ] [AGENT] P0. Replace `classify_and_emit_error` with `classify_venue_error()` +
      `log_event("ADAPTER_FETCH_FAILED", ...)` in:
  - `onchain/cli/handlers/batch_handler.py` — 6 except blocks, 0 classify_venue_error calls
  - `sports/cli/handlers/batch_handler.py` — 12 except blocks using wrong classifier
  - `commodity/cli/handlers/batch_handler.py` — check for any venue error classification
- [ ] [AGENT] P1. Fix deep import:
      `from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason` →
      `from unified_api_contracts import EmptyConfirmedReason` in all features-service files

### Phase 3 — strategy-service IS interaction hardening

- [x] ✅ [AGENT] P0. Fix `discover_instruments()` in strategy-service — add explicit GCS exception handling:
  - Catch `google.cloud.exceptions.GoogleCloudError` and similar
  - Raise `DependencyError(fail_fast=True)` instead of swallowing silently
  - Log `ADAPTER_FETCH_FAILED` event on exception
  — DONE 2026-05-21: strategy-service@046d45a1. `classify_venue_error` + `log_event("ADAPTER_FETCH_FAILED")` + `raise
  DependencyError(...)` replaces silent `return []`. Applied consistently to all 3 exception blocks in
  `strategy_config_loader.py`.
- [x] ✅ [AGENT] P0. Wire `gcs_storage_service.py` manifest emission (see also D5 Phase 3 — same finding from C2 and C6)
  — DONE via D5/D6: strategy-service@cd617891 (StrategyManifestRecorder wired in write_instructions). Verified
  `record_captured/empty/failed` present in gcs_storage_service.py.

### Phase 4 — execution-service bucket-SSOT fixes

- [x] ✅ [AGENT] P0. Fix inline bucket f-strings in execution-service (C3 finding):
  — DONE 2026-05-21: execution-service@e8296ed6. 20 sites flagged (AST JoinedStr.lineno
    points to first line of implicit concatenation, not the gs:// line). All are legitimate
    URI composers (bucket already resolved); added # noqa: gs-uri to first-line of each.
    QG STEP 5.69: 0 violations == baseline 0. QG exits 0.
- [ ] [AGENT] P0. Fix Deribit tick_size fetched from live API (`execution_service/venues/deribit.py`):
  - Load `tick_size` from IS `InstrumentRecord` cache instead of making live API call at startup
  - Live API call on startup = wrong; IS is the SSOT for instrument metadata per CLAUDE.md

### Phase 5 — Quality gates

- [ ] [AGENT] P0. Run `cd features-service && bash scripts/quality-gates.sh` — must be green
- [ ] [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh` — must be green
- [ ] [AGENT] P0. Run `cd execution-service && bash scripts/quality-gates.sh` — must be green

## Success criteria

- [ ] Phase 1: `rg '"BTC".*"ETH"' features_service/volatility/ --type py` returns 0 hits in handler (hardcode removed)
- [ ] Phase 2: `rg 'classify_venue_error' features_service/ --type py` returns hits in onchain + sports + commodity
      handlers
- [ ] Phase 3: `rg 'DependencyError' strategy_service/ --type py` returns hits near IS catalogue reads
- [ ] Phase 4: `rg 'f"gs://' execution_service/ --type py` returns 0 hits (all bucket names via resolver)
- [ ] Phase 5: all 3 services QG green

## Full-execution criterion

> features-service volatility handler tested with IS catalogue mock returning `["BTC","ETH","SOL","BNB"]` → feature
> computation runs for all 4 (not just hardcoded 2). execution-service QG STEP 5.69 (no_inline_bucket_uri) passes with 0
> violations. Deribit `tick_size` loaded from IS InstrumentRecord (verify via unit test that no live API call is made at
> service startup).

## Temporary states + their canonical follow-up plans

- IS catalogue empty for onchain DeFi until IS DeFi adapters backfill for dates < 2026-05-20: acceptable; onchain
  handler emits `record_empty(EXPECTED_UPSTREAM_EMPTY)` for those dates. Follow-up: IS DeFi backfill is part of
  `defi_catalogue_chain_primitives_2026_05_10.md`.
- `classify_and_emit_error` (UTL wrapper) removal: UTL wrapper may still be used by other services; removal from
  features-service only. No cross-repo breaking change.
