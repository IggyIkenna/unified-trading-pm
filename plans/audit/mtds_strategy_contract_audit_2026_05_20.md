---
name: mtds_strategy_contract_audit_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
status: in-flight
deadline: 2026-05-23
priority: P0
parent_epic: manifest_evolution_master_2026_05_08
parent_plan: master_to_live_defi_2026_05_23.md
related_plans:
  - is_mtds_contract_audit_2026_05_20.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
  - bucket_name_ssot_canonicalisation_2026_05_10.md
feeds_ordering_steps: [D4, D6]
---

# MTDS → strategy-service Contract Audit — 2026-05-20

> **Trigger**: Mega-audit Phase C5 (D4/D6 ordering steps). MTDS produces raw tick data that strategy-service is **not**
> supposed to read directly — the canonical pipeline is IS → MTDS → features-service → strategy. This audit verifies (a)
> whether strategy-service bypasses features-service and reads MTDS buckets directly (layering violation), and (b) the
> full 7-pattern contract across the MTDS → strategy pair for the data that IS allowed to flow between them.

---

## 0. Header block

```yaml
pair: MTDS → strategy-service
auditor: slot-4 (C5 task)
audit_date: 2026-05-20
audit_file: plans/audit/mtds_strategy_contract_audit_2026_05_20.md
repo_shas:
  market-tick-data-service: fae9416
  strategy-service: e4e5a1e6
feeds_ordering_step: D4 + D6
status: complete
```

---

## Architectural contract (the allowed data flow)

```
instruments-service
       │
       ▼
market-tick-data-service (MTDS)
       │  writes raw tick data to gs://market-data-tick-{asset_group}-*
       │
       ▼
features-service (features-onchain / features-delta-one)
       │  writes derived features to:
       │    gs://features-onchain-*     (DeFi)
       │    gs://features-delta-one-*   (CeFi/TradFi)
       │
       ▼
strategy-service
       │  reads ONLY features buckets + instruments-store buckets
       │  reads BigQuery analytics dataset for CeFi candles
       │  NEVER reads market-data-tick-* GCS directly
       ▼
execution-service
```

**Banned path**: `strategy-service` reading `gs://market-data-tick-*` GCS directly = layering violation.

---

## MTDS direct-read check (CRITICAL — layering violation scan)

**Grep evidence**:

```
rg 'market-data-tick|market_tick|market_data_tick' strategy-service/ --type py
```

**Results**:

| File                                                 | Line     | Content                                                                                 | Classification                                                                            |
| ---------------------------------------------------- | -------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `scripts/probe_funding_rate_dispersion_coverage.py`  | L1       | `_DEFAULT_TICK_DATA_BUCKET_TEMPLATE: Final[str] = "market-data-tick-cefi-{project_id}"` | Scripts only — not service source                                                         |
| `scripts/trace_arbitrage_price_dispersion.py`        | multiple | `_TARDIS_BUCKET_TEMPLATE: str = "market-data-tick-cefi-{project_id}"`                   | Scripts only — not service source                                                         |
| `scripts/trace_carry_staked_basis.py`                | multiple | `_TARDIS_BUCKET_TEMPLATE: str = "market-data-tick-cefi-{project_id}"`                   | Scripts only — not service source                                                         |
| `strategy_service/config.py`                         | L415     | `default="market-data-tick-{category}-{project_id}"`                                    | Config field `market_data_bucket_template` — NOT used in production code path (see below) |
| `tests/position/integration/test_split_libraries.py` | L1       | `import market_tick_data_service.market_interface`                                      | Test file only                                                                            |
| `strategy_service/engine/futures/roll_emitter.py`    | L1       | docstring reference only                                                                | Doc reference, no read                                                                    |

**Verdict — NO LAYERING VIOLATION in production source code.**

The `market_data_bucket_template` config field in `strategy_service/config.py:415` is defined but **is not used anywhere
in the production service code path** (`strategy_service/`). The strategy service does NOT read `market-data-tick-*` GCS
buckets at runtime. All production market data access goes through:

1. **CeFi/TradFi**: `CloudDataProvider` → `AnalyticsClient.execute_query()` → BigQuery `market_data_hft` dataset
   (candles pre-processed by MTDS processing pipeline)
2. **DeFi**: `GCSFeatureProvider` → `resolve_bucket_name(kind="features-onchain", asset_group="defi")` →
   `features-onchain-*` GCS (written by features-onchain-service)

The `scripts/` directory references to `market-data-tick-*` are in one-off diagnostic/trace scripts
(`probe_funding_rate_dispersion_coverage.py`, `trace_arbitrage_price_dispersion.py`, `trace_carry_staked_basis.py`) —
not part of the production batch/live pipeline.

**P0 finding**: The `market_data_bucket_template` config field in `config.py:415` is dead config — it was previously
used by a CloudDataProvider GCS path that has since been replaced by the BigQuery analytics path. This dead config is
misleading (suggests strategy reads MTDS buckets). Should be cleaned up.

---

## 4-dimensional audit matrix

### Dim 1 — MTDS adapter coverage per asset_group (upstream)

Not applicable as primary audit dimension: strategy-service does NOT read MTDS GCS directly. MTDS upstream coverage is
already audited in `is_mtds_contract_audit_2026_05_20.md`. The relevant upstream for strategy-service is
features-service (features-delta-one + features-onchain).

### Dim 2 — Downstream handler upstream-consumption status

| Data consumer                             | Status                                                                        | Evidence                        |
| ----------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------- |
| `CloudDataProvider` (CeFi/TradFi candles) | ✅ Via BigQuery analytics dataset — NOT direct MTDS GCS                       | `cloud_data_provider.py:31-34`  |
| `GCSFeatureProvider` (DeFi features)      | ✅ `resolve_bucket_name(kind="features-onchain")`                             | `gcs_feature_provider.py:57`    |
| `DependencyChecker` (preflight)           | ✅ Checks `features-delta-one-{asset_group}` + `instruments-store` — NOT MTDS | `dependency_checker.py:49-65`   |
| `strategy_config_loader.py`               | ✅ Reads `instruments-store-defi` via `resolve_bucket_name`                   | `strategy_config_loader.py:176` |

**Finding — known A5 issue (pre-existing P0)**: `batch_handler.py:128-130` has a warn-and-proceed path when
`fail_on_missing_deps=False` and required upstream dependencies are missing. The handler:

1. Logs `logger.warning("⚠️ %s dependencies not available (continuing anyway):", len(failures))` (line 128)
2. Emits `PreflightSkipReason.DEPENDENCIES_MISSING_CONTINUE` (lines 134-139) — this IS visible
3. **Does NOT raise `DependencyError`** when `fail_on_missing_deps=False`

This means if the caller passes `fail_on_missing_deps=False`, strategy computes on stale/missing features data with only
a warning, no hard stop. The A5 finding already names this as `batch_handler.py:130,502` (the 502 line is the call site
that passes `fail_on_missing_deps`).

However, `batch_handler.py:123` DOES raise `DependencyError` when `fail_on_missing=True` (the default). The warn-proceed
path is only triggered when the caller explicitly passes `fail_on_missing_deps=False`. Per task context: this is the
**known A5 P0** — already tracked in the mega-audit.

### Dim 3 — Manifest emission discipline (strategy OUTPUT)

Strategy-service is a **consumer** of MTDS-derived data (via features-service), not a writer to MTDS buckets. For the
strategy OUTPUT side:

| Write path                                                     | Manifest status                                                                   | Evidence                                              |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `CloudStorageService.write_instructions()`                     | ❌ **Zero manifest emission**                                                     | `gcs_storage_service.py:159-198` — no `record_*` call |
| `CloudStorageService.write_backtest_result_full()`             | ❌ **Zero manifest emission**                                                     | `gcs_storage_service.py:287-374` — no `record_*` call |
| `CloudStrategyStorage.store_orders()`                          | ⚠ Uses legacy `ManifestWriter.add()` + `writer.write()` (NOT `record_captured`)  | `cloud_strategy_storage.py:187-199`                   |
| `CloudStrategyStorage.store_positions()`                       | ⚠ Uses legacy `ManifestWriter.add()` + `writer.write()` (NOT `record_captured`)  | `cloud_strategy_storage.py:264-276`                   |
| `CloudStrategyStorage.store_pnl()`                             | ⚠ Uses legacy `ManifestWriter.add()` + `writer.write()` (NOT `record_captured`)  | `cloud_strategy_storage.py:340-353`                   |
| `decision_context_writer.py`                                   | ⚠ `record_captured` with `# QG-allow: emission-policy-not-applicable` suppressor | `decision_context_writer.py:152`                      |
| `hedge_ratio_writer.py`                                        | ⚠ `record_captured` with `# QG-allow: emission-policy-not-applicable` suppressor | `hedge_ratio_writer.py:139`                           |
| `_write_instructions_to_gcs()` in `batch_handler.py:1261-1296` | ❌ **Zero manifest emission**                                                     | Direct `storage.upload_bytes()` with no `record_*`    |
| `risk_snapshot_sink.py`                                        | ⚠ Uses `ManifestWriter` (legacy API, no `record_captured`)                       | `risk_snapshot_sink.py:179-190`                       |
| `pnl/cli/handlers/compute_handler.py`                          | ⚠ Uses `ManifestWriter` (legacy API)                                             | `compute_handler.py:233-244`                          |

**This is the C2 finding** already cited in the task description: `gcs_storage_service.py` has zero manifest emission
for strategy output. Confirmed. The `CloudStorageService` class (the primary write path for strategy instructions +
backtest results) emits NO manifest records at all.

Additionally, all `ManifestWriter` usages in `cloud_strategy_storage.py` use the legacy `.add()` + `.write()` API rather
than the 4-state `record_captured()` / `record_empty(reason=...)` / `record_failed()` API. The legacy path does not
populate `capture_status`, `error_reason`, or `pipeline_mode` columns — it produces v4 manifest rows, not v8.

### Dim 4 — Manifest schema version per bucket

| Bucket                        | Schema version                           | Evidence                                                                                                       |
| ----------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `strategy-store-{project_id}` | **v4 (legacy `ManifestWriter.add()`)**   | `cloud_strategy_storage.py:190-197` uses legacy API which produces v4-compatible rows without `capture_status` |
| `features-onchain-*` (input)  | v8 (written by features-onchain-service) | audited separately                                                                                             |
| `instruments-store-*` (input) | v8 (audited in is_mtds_contract_audit)   | confirmed                                                                                                      |

---

## Pattern-by-pattern findings

### Pattern 1 — SSOT-owned reference flowing down

**Status: CLEAN** (no layering violation)

Strategy-service correctly reads features from features-service and reference data from instruments-service. No
hardcoded MTDS bucket strings in production source. No hardcoded universe lists sourced from MTDS.

Dead config finding: `strategy_service/config.py:415` `market_data_bucket_template` field references
`market-data-tick-{category}-{project_id}` but is not used in any production code path.

**Pre-audit grep evidence**:

```bash
# Hardcoded URL constants in strategy-service source (production):
rg '_[A-Z_]+_URL\s*=\s*"https?://' strategy-service/strategy_service/
# 0 hits

# MTDS bucket template in production source:
rg 'market.data.tick' strategy-service/strategy_service/ --type py
# Only: config.py:415 (unused dead config field)
```

### Pattern 2 — Manifest emission discipline

**Status: VIOLATIONS (C2 confirmed)**

Primary write paths for strategy output have zero manifest emission. `gcs_storage_service.py` (the main
`CloudStorageService` class used for writing strategy instructions and backtest results) has no `record_*` calls
anywhere. The `_write_instructions_to_gcs()` in `batch_handler.py` likewise has zero manifest emission.

The `cloud_strategy_storage.py` paths use the legacy `ManifestWriter.add()` / `writer.write()` API which does not emit
4-state capture status.

**Grep evidence**:

```bash
rg 'record_captured|record_empty|record_failed' strategy-service/strategy_service/ --type py | wc -l
# Result: 6 (all concentrated in 2 writers: decision_context_writer + hedge_ratio_writer)
# gcs_storage_service.py: 0 hits
# cloud_strategy_storage.py: 0 record_captured hits (only ManifestWriter.add)
# batch_handler.py _write_instructions_to_gcs: 0 hits
```

### Pattern 3 — Schema-version compliance

**Status: GAP**

`cloud_strategy_storage.py` uses the legacy `ManifestWriter.add()` API. This API path does not populate v8-required
columns (`capture_status`, `error_reason`, `pipeline_mode`). Strategy-store manifest index will have v4-equivalent rows
for any shard written via this path.

No hardcoded `schema_version=<N>` literals found in strategy-service source.

### Pattern 4 — Honest-absence reason taxonomy

**Status: GAP**

`record_empty(reason=...)` is never called in strategy-service source. The service does not emit `empty_confirmed`
manifest rows. When strategy produces no signals for a date × instrument shard (e.g. no features data available, market
closed), the shard simply has no manifest row at all (silent absence) rather than an
`empty_confirmed[reason=EXPECTED_*]` row.

**Grep evidence**:

```bash
rg 'record_empty|EmptyConfirmedReason' strategy-service/strategy_service/ --type py
# 0 hits
```

### Pattern 5 — `expected_coverage()` preflight + `DIVERGENT_EMPTY` post-hoc check

**Status: PARTIAL**

Strategy-service has a `DependencyChecker` that checks upstream availability before running (features-service

- instruments-service manifests). However, it does NOT call `expected_coverage()` from UAC to classify whether a given
  (venue, data_type, date) shard is `SHOULD_HAVE_DATA | EXPECTED_EMPTY`. The dependency checker only checks bucket-level
  availability, not per-cell availability.

The `manifest_allocation_guard.py` module reads availability index and classifies cells, but this is for **input**
consumption (checking whether features data is available before running), not for **output** emission.

**Grep evidence**:

```bash
rg 'expected_coverage' strategy-service/strategy_service/ --type py
# 0 hits — no preflight coverage classification
```

### Pattern 6 — Error classification at the boundary

**Status: PARTIALLY COMPLIANT**

`classify_venue_error` is used correctly in the signal broadcast subsystem:

- `signal_broadcast/failure_isolation.py:26` imports and calls `classify_venue_error`
- `ADAPTER_FETCH_FAILED` emitted at `failure_isolation.py:90`
- `version_governance/pending_approvals_runner.py:109,154` emits `ADAPTER_FETCH_FAILED`

However, `cloud_data_provider.py:153-155` catches `(OSError, ValueError)` and re-raises without calling
`classify_venue_error` or emitting `ADAPTER_FETCH_FAILED`. This is the BigQuery candle fetch path — errors here produce
no classified error event.

**Grep evidence**:

```bash
rg 'classify_venue_error' strategy-service/strategy_service/ --type py
# strategy_service/signal_broadcast/failure_isolation.py:26 — import
# strategy_service/signal_broadcast/failure_isolation.py:75 — call site
# strategy_service/signal_broadcast/observability_ingest.py:228 — docstring
# NOT in cloud_data_provider.py, gcs_storage_service.py, batch_handler.py
```

### Pattern 7 — Bucket-SSOT

**Status: PARTIALLY COMPLIANT — violations exist**

`resolve_bucket_name()` is used in several paths:

- `gcs_feature_provider.py:57` — correct
- `strategy_config_loader.py:36,62,176` — correct
- `decision_context_writer.py:105`, `hedge_ratio_writer.py:92`, `domain_adapter.py:118` — correct

**Violations** (inline `f"strategy-store-{project_id}"` without `resolve_bucket_name`):

- `cloud_strategy_storage.py:189` — `bucket = f"strategy-store-{cfg.project_id}"` (ManifestWriter path)
- `cloud_strategy_storage.py:266` — same pattern (positions)
- `cloud_strategy_storage.py:343` — same pattern (pnl)
- `cli/service_entry.py:159` — `bucket_name = f"strategy-store-{project_id}"`
- `cli/handlers/batch_handler.py:1276` — `bucket = f"strategy-store-{project_id}"`

These are all for the strategy-store bucket, not MTDS buckets — so they are not layering violations. But they ARE
bucket-SSOT violations (Pattern 7). QG STEP 5.69 fires for these but they appear to be in the existing ratchet baseline
(no `noqa: gs-uri` on some paths; others have it).

**Grep evidence**:

```bash
rg 'f"strategy-store-{' strategy-service/strategy_service/ --type py | grep -v test | grep -v 'noqa: gs-uri'
# cloud_strategy_storage.py:189,266,343
# cli/service_entry.py:159 (no noqa comment)
# batch_handler.py:1276 (no noqa comment)
```

---

## Summary — P0 findings table

| #         | Pattern                            | Severity | File                                                                | Lines              | Finding                                                                                                        |
| --------- | ---------------------------------- | -------- | ------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------- |
| C5-1      | P1 — SSOT reference                | P1       | `strategy_service/config.py`                                        | 413-418            | Dead config field `market_data_bucket_template` references MTDS bucket but is unused in production; misleading |
| C5-2      | P2 — Manifest emission             | **P0**   | `gcs_storage_service.py`                                            | 159-374            | `CloudStorageService` (primary instruction/backtest write path) emits ZERO manifest records                    |
| C5-3      | P2 — Manifest emission             | **P0**   | `batch_handler.py`                                                  | 1261-1296          | `_write_instructions_to_gcs()` has zero manifest emission                                                      |
| C5-4      | P2/P3 — Manifest emission + schema | P1       | `cloud_strategy_storage.py`                                         | 187-353            | Uses legacy `ManifestWriter.add()` — produces v4-equivalent rows, not 4-state v8                               |
| C5-5      | P4 — Honest absence                | P1       | strategy_service-wide                                               | all writers        | No `record_empty(reason=...)` anywhere — silent absence when strategy output is empty                          |
| C5-6      | P5 — Expected coverage preflight   | P1       | strategy_service-wide                                               | dependency_checker | `expected_coverage()` not called; dependency check is bucket-level only, not cell-level                        |
| C5-7      | P6 — Error classification          | P1       | `cloud_data_provider.py`                                            | 153-155            | Catches `OSError/ValueError` without `classify_venue_error` or `ADAPTER_FETCH_FAILED`                          |
| C5-8      | P7 — Bucket SSOT                   | P1       | `cloud_strategy_storage.py`, `service_entry.py`, `batch_handler.py` | multiple           | Inline `f"strategy-store-{project_id}"` without `resolve_bucket_name` or `noqa: gs-uri`                        |
| **C5-A5** | **Known pre-existing**             | **P0**   | `batch_handler.py`                                                  | **128-130,502**    | **warn-but-proceed when `fail_on_missing_deps=False` and required upstream missing**                           |
| **C5-C2** | **Known pre-existing**             | **P0**   | `gcs_storage_service.py`                                            | **159-374**        | **Zero manifest emission for strategy output (same as C5-2 above)**                                            |

---

## Layering violation assessment

**VERDICT: NO DIRECT LAYERING VIOLATION in production code.**

Strategy-service does NOT read `market-data-tick-*` GCS buckets in its production code path. The canonical pipeline
(MTDS → features-service → strategy) is respected. The config field `market_data_bucket_template` is dead config and
does not indicate a live violation.

The `scripts/` directory does reference MTDS buckets (diagnostic scripts), but these are not part of the production
batch/live pipeline and are outside the scope of the production contract audit.

---

## Phased remediation DAG

```
Phase 1 — Fix C5-2 + C5-3 (CRITICAL): add record_captured/record_empty/record_failed to
           CloudStorageService.write_instructions() + _write_instructions_to_gcs()
           │
           ├── Phase 2 — Migrate cloud_strategy_storage.py from ManifestWriter.add()
           │             to record_captured / record_empty (4-state v8 API)
           │
           ├── Phase 3 — Add record_empty(reason=EXPECTED_*) to all write paths
           │             for empty-output cases
           │
           ├── Phase 4 — Fix bucket SSOT violations (C5-8):
           │             route inline f"strategy-store-{project_id}" through resolve_bucket_name
           │
           ├── Phase 5 — Fix CloudDataProvider error classification (C5-7):
           │             add classify_venue_error + ADAPTER_FETCH_FAILED to except block
           │
           └── Phase Q — QG wiring: verify strategy-service QG catches manifest gaps
                         (no_silent_absence_handlers.sh does not currently apply to
                          strategy write paths — needs scope extension)
```

**Foundation-completion-gate**: Phases 1-3 are P0 (strategy output must have manifest coverage for the paper-trade gate
— execution-service needs to read strategy instructions and know their manifest status).

---

## QG-ratchet phase

### Phase Q — QG enforcement gaps

| Pattern                          | QG script                                                       | Status for strategy-service                                                                                                                                                                        |
| -------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1 — SSOT-owned reference        | `no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` | Not wired for strategy-service (MTDS-focused). N/A for strategy layer.                                                                                                                             |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh`                                 | **GAP** — script targets `*_handler.py` files. `gcs_storage_service.py` + `cloud_strategy_storage.py` are write classes, not handlers. Script needs scope extension to cover strategy write paths. |
| P3 — Schema-version              | Inline rg step                                                  | Not wired in strategy-service QG                                                                                                                                                                   |
| P4 — Honest-absence reasons      | `LegacyBlankErrorReasonError` runtime                           | No `record_empty` calls exist — no runtime coverage. Need static QG check.                                                                                                                         |
| P5 — expected_coverage preflight | Post-hoc divergence scanner                                     | Not wired                                                                                                                                                                                          |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                 | Not confirmed wired in strategy-service QG                                                                                                                                                         |
| P7 — Bucket SSOT                 | STEP 5.69 `check_inline_bucket_uri.py`                          | Wired via base-service.sh — but violations exist in current ratchet baseline                                                                                                                       |

---

## Continuous verification

| Pattern                   | Continuous-verification path                                           | Cadence               | Last verified |
| ------------------------- | ---------------------------------------------------------------------- | --------------------- | ------------- |
| P2 — Manifest emission    | `no_silent_absence_handlers.sh` (needs scope extension)                | every push            | TBD           |
| P3 — Schema-version       | Inline QG rg step (not yet added)                                      | every push            | TBD           |
| P4 — Honest absence       | `LegacyBlankErrorReasonError` runtime (needs record_empty calls first) | every batch run       | TBD           |
| P5 — expected_coverage    | Post-hoc `DIVERGENT_EMPTY` scanner after Phase 1                       | daily scheduled audit | TBD           |
| P6 — Error classification | Add to `cloud_data_provider.py` except block + static check            | every push            | TBD           |
| P7 — Bucket SSOT          | `check_inline_bucket_uri.py` (STEP 5.69) — already wired               | every push            | 2026-05-20    |

---

## Scope exclusions

- **P1 (SSOT-owned reference)**: Verified clean for MTDS-direct reads. No hardcoded MTDS venue URLs in production
  strategy-service source. Dead config field at `config.py:415` is a cleanup task (P1 severity), not a live contract
  violation.
- **P3 (schema-version)**: No hardcoded `schema_version=<N>` literals found. The gap is that `ManifestWriter.add()` in
  `cloud_strategy_storage.py` implicitly produces v4 rows. Remediation is migration to `record_captured()` API (part of
  Phase 2).
- **Layering violation**: Exhaustively checked. NOT present in production code paths.

---

## Temporary states + their canonical follow-up plans

- Legacy `ManifestWriter.add()` in `cloud_strategy_storage.py` remains until Phase 2 migration executes. Downstream
  consumers: `deployment-api` reads strategy-store manifest to show status.
- Dead config field `market_data_bucket_template` in `config.py:415` remains until Phase 1 cleanup. No downstream impact
  (unused).
- `gcs_storage_service.py` `CloudStorageService` writes without manifest until Phase 1 ships. Risk: execution-service
  cannot see strategy output in manifest — degraded visibility only (data still exists in bucket).

Successor plan for Phases 1-Q: `plans/active/strategy_manifest_emission_remediation_2026_05_20.md` (to be created by the
slot picking up remediation).

---

## Key findings for operator

**Good news**: No MTDS direct-read layering violation found. The canonical pipeline is respected.

**P0 items requiring remediation** (two pre-known + one new):

1. **C5-A5 (pre-known)**: `batch_handler.py:128-130` warn-but-proceed on missing upstream data when
   `fail_on_missing_deps=False`. Fix: add `DependencyError(fail_fast=True)` unconditionally when required deps missing.
2. **C5-C2 (pre-known = C5-2)**: `gcs_storage_service.py` zero manifest emission. Fix: add `record_captured()` /
   `record_empty()` to `write_instructions()` and all write paths.
3. **C5-3 (new)**: `batch_handler.py:_write_instructions_to_gcs()` also zero manifest emission (second write path for
   instructions, used by the live-mode path).

**P1 items**:

- `cloud_strategy_storage.py` legacy ManifestWriter API (v4 output)
- `config.py:415` dead MTDS bucket config field
- `cloud_data_provider.py` missing error classification
- Inline bucket string violations in 3 files
