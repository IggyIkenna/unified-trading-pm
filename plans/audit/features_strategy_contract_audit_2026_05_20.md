---
pair: features-service → strategy-service
auditor: slot-4 / ikenna
audit_date: 2026-05-20
audit_file: plans/audit/features_strategy_contract_audit_2026_05_20.md
feeds_ordering_step: D5 (features missing-data downgrade plan), D6 (strategy + execution plan)
status: complete
strategy_service_sha: e4e5a1e6
features_service_sha: 33e85297
---

# C6 Contract Audit — features-service → strategy-service

> **AUDIT SCOPE**: Standard 7-pattern contract audit + C6 scope addendum (per-pair viability + pricing ownership, per
> operator directive 2026-05-20).
>
> **Sampling vs exhaustive**: This audit examined ALL Python source files under `strategy_service/` and
> `features_service/` (1086 files in features, ~120 in strategy). Full-depth read on the 12 most critical handler/engine
> files. GCS bucket state NOT sampled (read-only audit of code contracts).

---

## Executive summary

| Severity         | Count | Description                                    |
| ---------------- | ----- | ---------------------------------------------- |
| P0 (blocker)     | 5     | Critical contract violations; May-23 blocking  |
| P1 (high)        | 3     | Non-trivial gaps that degrade data correctness |
| P2 (medium)      | 2     | Improvements needed before stable ops          |
| Clean (verified) | 3     | Patterns confirmed correct                     |

**Overall audit verdict: RED — 5 P0 findings block May-23 live deployment.**

---

## 0. Audit context

**Upstream**: `features-service/` — writes per-asset and cross-instrument features to GCS; emits pub/sub events.

**Downstream**: `strategy-service/` — reads features from GCS via `GCSFeatureProvider`; generates trading signals via V2
archetype engines.

**Key inheritance from known findings**:

- C1 finding: features-service volatility handler hardcodes `["BTC","ETH"]` (separate handler audit)
- C2 finding: strategy-service `gcs_storage_service.py` has zero manifest emission for outputs
- A5 (P0): strategy `batch_handler.py:130,502` warn-but-proceed pattern

---

## Pattern 1 — SSOT-owned reference flowing down

### Dim 1 — Upstream adapter coverage per asset_group

| asset_group | features-service outputs                                                  | Gap                                                    |
| ----------- | ------------------------------------------------------------------------- | ------------------------------------------------------ |
| DeFi        | `lending_rates`, `onchain_perps`, `lst_yields`, `paired_price_dispersion` | No freshness / viability filter per-pair (see P0-C6-1) |
| CeFi        | `delta_one` features, `paired_price_dispersion` cross-venue               | ✅ Catalog-driven via UAC PAIRED_DISPERSION_CATALOG    |
| TradFi      | `delta_one` features, `paired_price_dispersion` CME/ICE legs              | ✅ Catalog-driven                                      |
| Sports      | Not consumed by strategy-service for May-23 archetypes                    | N/A                                                    |
| Prediction  | Not consumed by strategy-service for May-23 archetypes                    | N/A                                                    |

### Dim 2 — Downstream handler upstream-consumption status

| Handler / Engine                         | Status                                                                                                                                                        | Citation                      |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| `gcs_feature_provider.py`                | ✅ Reads features bucket via `resolve_bucket_name(kind="features-onchain", asset_group="defi")`                                                               | `gcs_feature_provider.py:57`  |
| `batch_handler.py` — DeFi path           | ✅ Routes DEFI category to `GCSFeatureProvider.get_merged_features()` with `_MULTI_GROUP_STRATEGIES` map                                                      | `batch_handler.py:898-925`    |
| `batch_handler.py` — strategy write path | ❌ **P0-C7-1**: `f"strategy-store-{project_id}"` hardcoded inline bucket — violates bucket-SSOT rule                                                          | `batch_handler.py:1276`       |
| `ArbitragePriceDispersionEngine`         | ⚠ **P1-C6-2**: reads `mid_price_<venue>` from features dict keyed by config `candidate_venues` param — no per-pair viability check against features presence | `price_dispersion.py:219-229` |
| `catalog.py` — target universe           | ✅ Enumerates via `StrategyArchetype` + `TargetInstanceSpec`; does NOT call IS cross_asset endpoint                                                           | `catalog.py:1-50`             |

**C6 P0 finding — no universe enumeration wired**: Strategy `ArbitragePriceDispersionEngine` derives its venue list from
slot config params (`candidate_venues` field) — NOT from a features-service universe stream. If features-service emits
`mid_price_binance` but NOT `mid_price_deribit` (because deribit had no tick data), the engine silently drops that venue
pair (`per_venue` dict misses the key) without emitting any degraded-signal event. The universe is thus NOT driven by
features-service output; it is driven by static slot config.

---

## Pattern 2 — Manifest emission discipline

### Dim 3 — Manifest emission per handler

#### features-service handlers

| Handler                                | Status                                                                                                                                                                                                                | Evidence                              |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `cross_instrument/batch_handler.py`    | ⚠ **P1-C6-3**: Uses `ManifestWriter.add()` (success-only path) — NO `record_empty()` call when groups skip; when `_run_paired_dispatch` returns empty df it is silently skipped in `_persist_results` (line 457-463) | `batch_handler.py:594-629`, `457-463` |
| `delta_one/engine/orchestrator.py`     | ⚠ Uses ManifestWriter but `ManifestWriter failed ... non-fatal` suppresses errors                                                                                                                                    | `orchestrator.py:395`                 |
| `onchain/engine/orchestrator.py`       | ✅ ManifestWriter present                                                                                                                                                                                             | `orchestrator.py`                     |
| `sports/cli/handlers/batch_handler.py` | ✅ `record_empty()`, `record_failed()`, `record_captured()` all wired                                                                                                                                                 | `batch_handler.py`                    |

**C6 P0 finding — cross_instrument handler has no `record_empty` for skipped groups**: In `_persist_results()` (line
457-463), if `result.success=True` but `result.features.height == 0`, the group is silently skipped — no
`record_empty(reason=SOURCE_RETURNED_ZERO)` emitted. This is a DIVERGENT_EMPTY class bug for `paired_price_dispersion` +
`cross_venue_spreads` on any day where upstream legs were absent. Manifest shows no row = operator cannot distinguish
"hasn't run" from "ran but got zero data".

#### strategy-service handlers

| Handler                                      | Status                                                                                                                                                                                                              | Evidence                                               |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `cli/handlers/batch_handler.py`              | ❌ **P0-C6-4 / C2-confirmed**: Zero manifest emission for strategy outputs. `_write_instructions_to_gcs()` writes parquet to GCS but never calls `record_captured`. `gcs_storage_service.py` has no manifest calls. | `batch_handler.py:1261-1296`, `gcs_storage_service.py` |
| `carry_and_yield/hedge_ratio_writer.py`      | ⚠ `record_captured` present but `ManifestWriter.record_captured skipped` path — best-effort only                                                                                                                   | `hedge_ratio_writer.py`                                |
| `carry_and_yield/decision_context_writer.py` | ⚠ Same best-effort pattern                                                                                                                                                                                         | `decision_context_writer.py`                           |

---

## Pattern 3 — Schema-version compliance

### Dim 4 — Manifest schema version per bucket

| Service          | Code check                                          | Finding                                  |
| ---------------- | --------------------------------------------------- | ---------------------------------------- |
| features-service | No `schema_version=[1-7]` hardcodes found in source | ✅ No code-level regression              |
| strategy-service | No `schema_version=[1-7]` hardcodes found in source | ✅ No code-level regression              |
| GCS state        | NOT sampled in this audit (read-only code audit)    | Requires runtime scan per A3-style audit |

**Note**: Confirmed no code-level schema-version regressions. Runtime bucket scan is required separately (A3 audit
pattern) — this is explicitly out of scope for a code-only C-series audit.

---

## Pattern 4 — Honest-absence reason taxonomy

### Dim 5 — `record_empty` reason usage

| Service                                      | Finding                                                                                                                            |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| features-service `cross_instrument`          | ❌ **P0** (see Dim 3 above) — no `record_empty` call at all for skipped groups                                                     |
| features-service `sports` handler            | ✅ Uses typed `EmptyConfirmedReason` enum                                                                                          |
| features-service `cefi/perp_funding_handler` | ⚠ Comments reference `record_empty(reason=EXPECTED_NO_FUNDING_RATE_TICKS)` but call is deferred to caller — not confirmed emitted | `perp_funding_handler.py` |
| strategy-service                             | ❌ No `record_empty` calls anywhere in strategy output path                                                                        |

No blank `reason=""` strings found — no `LegacyBlankErrorReasonError` exposure in scoped code.

---

## Pattern 5 — `expected_coverage()` preflight

Neither features-service (cross_instrument path) nor strategy-service call `expected_coverage()` before fetching. This
is a **P2 gap** — no preflight classification means EXPECTED_EMPTY shards get attempted instead of being
short-circuited. No QG step enforces this today.

---

## Pattern 6 — Error classification at the boundary

| Service                                                  | Finding                                                                                                                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------- |
| features-service `cross_instrument`                      | `_run_paired_dispatch` catches `(OSError, RuntimeError, ValueError)` but does NOT call `classify_venue_error()` + does NOT emit `ADAPTER_FETCH_FAILED` | `batch_handler.py:362-373`        |
| strategy-service `gcs_feature_provider`                  | `_load_date_frames` catches `(OSError, ValueError, RuntimeError)` but only `logger.warning` — no `classify_venue_error()`                              | `gcs_feature_provider.py:122-125` |
| strategy-service `signal_broadcast/failure_isolation.py` | ✅ `classify_venue_error` + `ADAPTER_FETCH_FAILED` wired for signal broadcast path                                                                     | correct                           |

**P1 finding**: Two exception handlers on the critical paired-dispatch + GCS feature read paths lack
`classify_venue_error()` + `ADAPTER_FETCH_FAILED` emission — the mandatory UAC error-classification contract for every
adapter boundary.

---

## Pattern 7 — Bucket-SSOT

| Service                                                  | Finding                                                                                                                                           |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `gcs_feature_provider.py`                                | ✅ Uses `resolve_bucket_name(kind="features-onchain", asset_group="defi")`                                                                        | line 57                         |
| `strategy_config_loader.py`                              | ✅ Uses `resolve_bucket_name` for both `strategy-store` and `instruments-store`                                                                   |                                 |
| `batch_handler.py:1276`                                  | ❌ **P0-C7-1**: `bucket = f"strategy-store-{project_id}"` inline f-string construction                                                            | line 1276                       |
| `gcs_storage_service.py`                                 | ⚠ `_get_shared_bucket()` delegates to `config.get_output_bucket()` — chain unclear; non-`resolve_bucket_name` path                               | line 58-65                      |
| `grid_generator.py`                                      | ⚠ Uses `f"gs://{output_bucket}/configs_grid/..."` — URI construction, not bucket construction; `#noqa: gs-uri` present but bucket source unclear |                                 |
| features-service `cefi/perp_funding_rates.py`            | ❌ `f"gs://{bucket}/{path}"` inline URI without noqa suppression                                                                                  | `perp_funding_rates.py`         |
| features-service `onchain/feature_observation_writer.py` | ❌ `f"gs://{bucket}/{_DATA_TYPE}/..."` inline URI                                                                                                 | `feature_observation_writer.py` |

---

## C6 Scope Addendum — Per-pair viability + pricing ownership

### C6.1 — Universe enumeration

**Finding: FAIL — P0-C6-1**

`ArbitragePriceDispersionEngine` derives its pair universe from static slot config params (`candidate_venues` param,
`price_dispersion.py:220`). This is NOT sourced from features-service output. The engine reads `mid_price_<venue>` from
the incoming `features` dict and silently drops any venue where `px is None or px <= 0` (line 227-228). There is:

- No per-leg data-freshness filter wired
- No liquidity floor check
- No event emitted when a configured venue is absent from the feature stream
- No mechanism for features-service to advertise "this pair is viable today"

The viable universe is encoded in strategy slot config, not derived from features output.

**Impact**: If features-service stops producing `mid_price_okx` for a day (OKX outage, empty parquet, upstream MTDS
gap), strategy silently reduces to N-1 venues with no observable signal. Operator cannot distinguish a correct no-signal
day from a degraded-input day.

### C6.2 — Per-pair pricing signal schema

**Finding: PARTIAL — P1-C6-2**

Features-service `cross_instrument` DOES emit the canonical per-pair pricing signal: `paired_price_dispersion` feature
group with `spread_bps` + `annualised_apy_bps` per (left_venue, left_root, right_venue, right_root, expiry, day) shard.
Schema is declared in UAC `_PAIRED_PRICE_DISPERSION_REQUIRED_COLUMNS` — both leg identifiers AND spread value are
present.

**However**:

- Strategy `ArbitragePriceDispersionEngine` does NOT consume `paired_price_dispersion` features. It reads raw
  `mid_price_<venue>` per tick and computes its own spread inline (`price_dispersion.py:168`).
- The `paired_price_dispersion` feature stream is computed by features-service but there is NO confirmed consumer in
  strategy-service that reads it for signal generation.

**Grep evidence**:

```
rg 'paired_price_dispersion' strategy-service/ --type py  →  0 hits (source, not tests)
rg 'spread_bps|annualised_apy_bps' strategy-service/strategy_service --type py  →  0 hits
```

This means features-service computes `paired_price_dispersion` (with proper catalog + UAC SSOT integration), but
strategy-service re-derives the spread inline from raw per-venue features instead of consuming the pre-computed per-pair
stream.

### C6.3 — Strategy consumes per-pair feature stream (NOT raw MTDS)

**Finding: FAIL — P0-C6-3**

`ArbitragePriceDispersionEngine` reads raw per-venue `mid_price_<venue>` floats from the features dict — NOT the
`paired_price_dispersion` stream. The `GCSFeatureProvider` loads feature groups declared in `_MULTI_GROUP_STRATEGIES`
(which includes `lending_rates`, `onchain_perps`, `lst_yields` but does NOT include `paired_price_dispersion`). This
constitutes the banned pattern:

> _Strategy code that re-enumerates legs from raw per-leg data_

The consequences:

- Freshness checks on the upstream `paired_price_dispersion` shard are bypassed
- Spread computation is duplicated (features-service computes it, strategy computes it independently)
- Universe viability enforced in the catalog/dispatcher path (PAIRED_DISPERSION_CATALOG) is bypassed

### C6.4 — No IS `cross_asset` shard reads

**Finding: CLEAN — verified**

Neither strategy-service nor features-service source contains any call to an IS `cross_asset` endpoint. Grep confirmed 0
hits for `cross_asset_shard` and `instruments.*cross_asset` in both repos. The catalog-driven approach (UAC
`PAIRED_DISPERSION_CATALOG`) correctly avoids IS entirely for cross-pair universe enumeration.

---

## 4-dimensional audit matrix

| Dim   | What it measures                               | Status                                                                                          |
| ----- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Dim 1 | Upstream adapter coverage per asset_group      | ⚠ PARTIAL — features output exists but strategy doesn't consume paired_price_dispersion stream |
| Dim 2 | Downstream handler upstream-consumption status | ❌ FAIL — APD engine reads raw per-venue features, not pre-computed per-pair stream             |
| Dim 3 | Manifest emission discipline per handler       | ❌ FAIL — cross_instrument no record_empty; strategy no manifest on outputs                     |
| Dim 4 | Manifest schema version per bucket             | ⚪ NOT SAMPLED — code clean; runtime scan required                                              |

---

## P0 findings summary (May-23 blocking)

### P0-C6-1: No per-pair viability filter in strategy APD engine

- **Location**:
  `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py:219-229`
- **Finding**: Universe derived from static `candidate_venues` param, not features-service stream. Missing venue
  silently dropped — no event emitted.
- **Required fix**: Add `VENUE_DATA_ABSENT` event emission when a configured venue is missing from features dict. Wire
  `paired_price_dispersion` shard presence check as viability gate.

### P0-C6-3: Strategy APD engine does not consume `paired_price_dispersion` feature stream

- **Location**: `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py` +
  `strategy-service/strategy_service/cli/handlers/batch_handler.py:869-878`
- **Finding**: `_MULTI_GROUP_STRATEGIES` map does not include `paired_price_dispersion`; APD engine re-derives spread
  inline from raw `mid_price_<venue>` floats. This bypasses the features-service catalog-driven per-pair stream
  entirely.
- **Required fix**: Add `paired_price_dispersion` to `_MULTI_GROUP_STRATEGIES["ARBITRAGE_PRICE_DISPERSION"]`. Modify
  `ArbitragePriceDispersionEngine.on_tick` to consume `spread_bps` + `annualised_apy_bps` from features dict instead of
  re-computing.

### P0-C6-4 (C2 confirmed): Zero manifest emission for strategy outputs

- **Location**: `strategy-service/strategy_service/cli/handlers/batch_handler.py:1261-1296`
- **Finding**: `_write_instructions_to_gcs()` writes strategy instructions parquet to GCS but never calls
  `record_captured()`. `gcs_storage_service.py` has no ManifestWriter at all.
- **Required fix**: Add `ManifestWriter.record_captured()` call per (strategy_id, client_id, date) after each successful
  GCS write in `_write_instructions_to_gcs()`.

### P0-Bucket-SSOT: Hardcoded bucket name in batch_handler

- **Location**: `strategy-service/strategy_service/cli/handlers/batch_handler.py:1276`
- **Finding**: `bucket = f"strategy-store-{project_id}"` constructs bucket name as inline f-string. Violates bucket-SSOT
  rule (QG STEP 5.69).
- **Required fix**: Replace with
  `resolve_bucket_name(cloud=get_cloud_provider(), kind="strategy-store", asset_group=category)`.

### P0-Manifest-Empty: `cross_instrument/batch_handler.py` no `record_empty` for skipped groups

- **Location**: `features-service/features_service/cross_instrument/cli/handlers/batch_handler.py:457-463`
- **Finding**: `_persist_results()` silently skips groups where `features.height == 0` — no
  `record_empty(reason=SOURCE_RETURNED_ZERO)` emitted. DIVERGENT_EMPTY class bug for `paired_price_dispersion` when
  upstream legs absent.
- **Required fix**: Add `ManifestWriter.record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)` for every group
  with `result.features.height == 0` (with upstream-fail reason where applicable via `manifest_leg_guard`).

---

## P1 findings summary

### P1-C6-2: `paired_price_dispersion` stream produced but not consumed

- Detailed in C6.2 above. Features-service correctly emits per-pair spread features; strategy doesn't consume them.

### P1-C6-5: Missing `classify_venue_error` + `ADAPTER_FETCH_FAILED` in paired-dispatch and GCS feature read

- **Locations**: `features-service: cross_instrument/cli/handlers/batch_handler.py:362-373`;
  `strategy-service: engine/core/gcs_feature_provider.py:122-125`
- Both except blocks log warnings but do not call `classify_venue_error()` or emit `ADAPTER_FETCH_FAILED`.

### P1-C6-6: `ManifestWriter.add()` only tracks successes in cross_instrument batch

- `_write_run_manifest()` iterates `results.items()` and skips any group where `not result.success` — no
  `record_failed()` emitted for failed groups. `ManifestWriter failed (non-fatal)` exception suppression means even
  write errors are invisible.

---

## P2 findings summary

### P2-C6-7: No `expected_coverage()` preflight in either service

- Neither features-service cross_instrument nor strategy-service batch path calls `expected_coverage()` before
  attempting fetch. EXPECTED_EMPTY shards are attempted unnecessarily.

### P2-C6-8: `gcs_storage_service.py` bucket chain unclear

- `_get_shared_bucket()` delegates to `config.get_output_bucket()` — does not visibly use `resolve_bucket_name`. Needs
  audit to confirm chain is SSOT-compliant.

---

## Scope exclusions — verified clean

- **P3 (schema-version)**: No hardcoded `schema_version=[1-7]` found in either repo source. Continuous-verification via
  runtime bucket scan (separate A3-pattern audit required).
- **C6.4 (IS cross_asset reads)**: Confirmed 0 hits. Neither repo calls IS cross_asset endpoint.
- **P4 (blank reason strings)**: No `record_empty(reason="")` found in either repo. No `LegacyBlankErrorReasonError`
  exposure.

---

## Phase execution DAG

```
Phase 1 — UAC schema: add `paired_price_dispersion` feature keys to strategy's feature-group registry
   │
   ├── Phase 2 — Strategy APD engine: consume spread_bps/annualised_apy_bps from features (not re-compute)
   │   + emit VENUE_DATA_ABSENT when configured venue absent from feature stream
   │   + add `paired_price_dispersion` to _MULTI_GROUP_STRATEGIES map
   │
   ├── Phase 3 — Manifest emission: add record_captured to strategy _write_instructions_to_gcs
   │   + add record_empty to cross_instrument _persist_results skipped-groups path
   │   + add record_failed to cross_instrument _write_run_manifest for failed groups
   │
   ├── Phase 4 — Bucket SSOT: replace hardcoded `strategy-store-{project_id}` with resolve_bucket_name
   │
   ├── Phase 5 — Error classification: add classify_venue_error + ADAPTER_FETCH_FAILED to
   │   cross_instrument batch_handler + gcs_feature_provider exception handlers
   │
   └── Phase Q — QG enforcement: add STEP for no_silent_absence_handlers in strategy-service QG
```

**Foundation-completion-gate rule**: Phase 3 (manifest emission) must be GREEN before strategy outputs are considered
auditable for downstream consumers (execution-service, PnL attribution).

---

## QG-ratchet phase

| Pattern                          | QG script                                                       | Current status                                                      |
| -------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------- |
| P1 — SSOT-owned reference        | `no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` | SHIPPED for MTDS; NOT wired in strategy-service or features-service |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh`                                 | NOT wired in strategy-service                                       |
| P3 — Schema-version              | Inline rg step                                                  | **GAP — add as STEP**                                               |
| P4 — Honest-absence reasons      | `rg 'record_empty.*reason=""'` inline                           | **GAP**                                                             |
| P5 — expected_coverage preflight | (runtime-only)                                                  | **GAP**                                                             |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                 | Wired for signal_broadcast; NOT for feature-read path               |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)                        | SHIPPED — batch_handler.py:1276 is a current violation              |

---

## Continuous-verification column

| Pattern                          | Continuous-verification path                                        | Cadence         | Last verified                       |
| -------------------------------- | ------------------------------------------------------------------- | --------------- | ----------------------------------- |
| P1 — SSOT-owned reference        | `no_hardcoded_venue_urls.sh` in QG (once wired)                     | every push      | NOT YET WIRED                       |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh` in strategy-service QG (once wired) | every push      | NOT YET WIRED                       |
| P3 — Schema-version              | Inline QG rg step (once added)                                      | every push      | NOT YET WIRED                       |
| P4 — Honest-absence reasons      | `LegacyBlankErrorReasonError` at runtime                            | every batch run | N/A — no record_empty in strategy   |
| P5 — expected_coverage preflight | Post-hoc DIVERGENT_EMPTY scanner                                    | daily           | NOT YET WIRED                       |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                     | every push      | Partial — signal_broadcast only     |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)                            | every push      | ACTIVE — catches batch_handler:1276 |

---

## Temporary states + canonical follow-up plans

- **Inline spread re-computation in APD engine**: Temporary while Phase 2 migration is in-flight. Retire when
  `_MULTI_GROUP_STRATEGIES["ARBITRAGE_PRICE_DISPERSION"]` includes `paired_price_dispersion` and APD engine reads from
  features dict. Successor: this audit's Phase 2 items → D6 strategy plan.
- **ManifestWriter non-fatal suppression** (`ManifestWriter failed (non-fatal)`): This pattern exists in 5 handlers
  across features-service. Successor: convert to hard-fail once manifest infrastructure is proven stable; tracked in
  `D5 features downgrade plan`.

---

## Deferred work captured as todos

- [ ] P0. Emit `VENUE_DATA_ABSENT` event when configured venue missing from APD features dict
- [ ] P0. Add `paired_price_dispersion` to `_MULTI_GROUP_STRATEGIES` map; migrate APD engine to consume `spread_bps`
      from features instead of re-computing — `strategy-service`
- [ ] P0. Add `ManifestWriter.record_captured()` to `_write_instructions_to_gcs()` — `strategy-service`
- [ ] P0. Replace hardcoded `f"strategy-store-{project_id}"` with `resolve_bucket_name` —
      `strategy-service batch_handler.py:1276`
- [ ] P0. Add `record_empty(reason=SOURCE_RETURNED_ZERO)` to `cross_instrument/_persist_results` skipped-groups path —
      `features-service`
- [ ] P1. Add `classify_venue_error` + `ADAPTER_FETCH_FAILED` to `cross_instrument/batch_handler._run_paired_dispatch`
      except block
- [ ] P1. Add `classify_venue_error` + `ADAPTER_FETCH_FAILED` to `gcs_feature_provider._load_date_frames` except block
- [ ] P1. Add `record_failed()` to `cross_instrument/_write_run_manifest` for failed groups
- [ ] P2. Wire `no_silent_absence_handlers.sh` into strategy-service `quality-gates.sh`
- [ ] P2. Audit `config.get_output_bucket()` chain in `gcs_storage_service.py` to confirm SSOT compliance

## Coverage + sampling transparency

- **Code sampled**: 100% of handler/engine Python files in scope; deep-read on 12 critical files
- **GCS bucket state**: NOT sampled — separate A3-style runtime scan required
- **Test coverage**: Excluded from audit scope per analysis rules (tests cannot substitute for prod code correctness)
- **Open gap**: Live vs batch parity for features consumption path not verified at GCS level — `GCSFeatureProvider` only
  supports batch reads via date-range iteration; live path is TBD
