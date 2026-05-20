---
pair: instruments-service → strategy-service
auditor: ikenna / tab-4
audit_date: 2026-05-20
audit_file: plans/audit/is_strategy_contract_audit_2026_05_20.md
feeds_ordering_step: D1 (IS hardening plan)
status: complete
is_sha: 04e49f7
strategy_service_sha: fcdf3c96
---

# instruments-service → strategy-service Contract Audit — 2026-05-20

> **Trigger**: C-series contract audit ordered by mega-audit 2026-05-20. strategy-service is a
> pure consumer of IS outputs (not a data-capture producer like MTDS). The audit examines whether
> strategy-service correctly reads the IS catalogue to derive its instrument universe, emits
> manifest for its own outputs, handles IS dependency failures correctly, and satisfies the
> 7-pattern architectural contract.

## Architectural contract (SSOT)

```
                    ┌────────────────────────────────┐
                    │  instruments-service           │
                    │  ─ enumerates venue universe   │
                    │  ─ writes InstrumentRecord     │
                    │    per (venue, instrument_id,  │
                    │    day) to instruments-store-* │
                    │  ─ owns archive metadata:      │
                    │    url_template, record_types  │
                    │    coverage_start/end,         │
                    │    listed_at/delisted_at       │
                    └────────────┬───────────────────┘
                                 │
                                 ▼ read-only catalogue
                    ┌────────────────────────────────┐
                    │  strategy-service              │
                    │  ─ calls discover_instruments()│
                    │    → reads instruments-store   │
                    │    instrument_availability/    │
                    │    parquet via resolve_bucket  │
                    │  ─ DependencyChecker declares  │
                    │    IS as required upstream     │
                    │  ─ emits manifest for its own  │
                    │    GCS outputs (strategy-store)│
                    └────────────────────────────────┘
```

**Key distinction from IS→MTDS pair**: strategy-service does NOT run data-capture adapters.
It is a pure consumer that reads IS catalogue to discover its instrument universe and
reads features-service outputs for signals. Pattern 1 (IS consumption) therefore focuses
on the universe-discovery path, not on handler → IS-load chains.

---

## 4-dimensional audit matrix (2026-05-20 snapshot)

### Dim 1 — IS adapter coverage per asset_group (upstream read by strategy-service)

| asset_group | IS adapters available | strategy-service consumption | Violation type |
| ----------- | --------------------- | ----------------------------- | -------------- |
| DeFi        | IS writes instrument_availability per (venue, day) | `discover_instruments()` reads `instruments-store-defi` parquet — **DeFi only** | ⚠ Partial: only AAVEV3/COMPOUNDV3/MORPHO venues supported in `venue_map` |
| CeFi        | IS writes per-venue CeFi catalogues | **NOT READ** — CEFI instruments hardcoded in `cli/resolvers.py` INSTRUMENT_SHORTCUTS | ❌ Hardcoded universe bypasses IS |
| TradFi      | IS writes TradFi catalogues | **NOT READ** — TradFi instruments hardcoded (SPY/ES/NQ etc.) in resolvers + catalog.py | ❌ Hardcoded universe bypasses IS |
| Sports      | IS writes sports adapters | N/A — strategy-service does not trade sports (no sports strategies) | out of scope |
| Prediction  | IS writes prediction adapters | N/A — strategy-service does not trade predictions | out of scope |

**Pre-audit grep evidence:**

```
# Hardcoded CEFI/TradFi instruments in resolvers.py:
INSTRUMENT_SHORTCUTS = {
    "BTC": "BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN",
    "ETH": "BINANCE-FUTURES:PERPETUAL:ETH-USDT@LIN",
    "SOL": "BINANCE-FUTURES:PERPETUAL:SOL-USDT@LIN",
    "SPY": "NASDAQ:EQUITY:SPY",
}
# strategy_service/cli/resolvers.py lines 13-20

# Hardcoded v2 universe in target_universe/catalog.py (no IS read):
for venue in ("binance", "okx", "bybit", "hyperliquid"):
    for asset in ("btc", "eth", "sol"):
        ...  # target_universe/catalog.py lines 62-81

# DeFi: IS-read via discover_instruments():
bucket = resolve_bucket_name(cloud=get_cloud_provider(), kind="instruments-store", asset_group="defi")
path = f"instrument_availability/by_date/day={date_str}/venue={venue}/instruments.parquet"
# strategy_config_loader.py lines 176-178
```

### Dim 2 — Downstream handler IS-consumption status

| Component | Status | Citation |
| --------- | ------ | -------- |
| `strategy_config_loader.discover_instruments()` | ✅ Reads IS via `resolve_bucket_name(..., kind="instruments-store", asset_group="defi")` then parquet read | `strategy_config_loader.py:176-178` |
| `engine/core/dependency_checker.py` | ✅ Declares IS as required upstream dep via `UPSTREAM_DEPS["instruments-service"]` with bucket template check | `dependency_checker.py:60-64` |
| `cli/resolvers.py resolve_instruments()` | ❌ Hardcodes CeFi + TradFi instrument lists; IS never consulted for CEFI/TRADFI defaults | `resolvers.py:13-20, 48-56` |
| `engine/strategies/v2/target_universe/catalog.py` | ❌ Hardcodes full v2 instance universe (CeFi venues/instruments); no IS read | `catalog.py:57-81+` |
| `engine/core/market_hours_utils.py` | ⚠ IS metadata cache used when provided by caller; fallback to hardcoded UTC hours when unavailable | `market_hours_utils.py:15-19, 71-80` |
| `adapters/fill_subscriber.py` | ⚠ `DEFI_FILL_VENUES` hardcodes DeFi PubSub subscription targets; IS not consulted for venue list | `fill_subscriber.py:25` |

**Violation severity assessment**:
- `cli/resolvers.py` ❌ — CEFI/TradFi defaults bypass IS entirely. When strategy runs with `--category CEFI` and no explicit instruments, it uses the hardcoded shorthand list instead of checking IS for active instruments on that date.
- `target_universe/catalog.py` ❌ — The v2 target universe catalog is a static compiled list; instrument changes in IS (listings/delistings) do not propagate to strategy dispatching.
- `fill_subscriber.py` ⚠ — DeFi venue subscription list is hardcoded; adding a new DeFi execution venue requires a code change rather than flowing from IS.

### Dim 3 — Manifest emission discipline

strategy-service is a **signal producer**, not a data-capture pipeline (like MTDS). It writes
to `strategy-store-*` buckets, not manifest-indexed data buckets. The manifest emission
discipline applies to its OWN output data_types.

| Writer component | Status | Evidence |
| ---------------- | ------ | -------- |
| `cloud_strategy_storage.py` (orders/positions/pnl) | ⚠ Uses legacy `ManifestWriter.add() + .write()` API with inline `f"strategy-store-{cfg.project_id}"` bucket string; does NOT use `record_captured/record_empty/record_failed` 4-state API | `cloud_strategy_storage.py:187-199, 264-276` |
| `engine/strategies/v2/carry_and_yield/hedge_ratio_writer.py` | ⚠ Uses `record_captured` (QG-allow exemption); manifest writer is best-effort (exception swallowed); inline `f"strategy-store-{cfg.project_id}"` catalogue_bucket construction bypasses `resolve_bucket_name` | `hedge_ratio_writer.py:132-153` |
| `engine/strategies/v2/carry_and_yield/decision_context_writer.py` | ⚠ Same as hedge_ratio_writer — best-effort `record_captured`, exception swallowed, inline bucket f-string | `decision_context_writer.py:145-166` |
| `risk/core/risk_snapshot_sink.py` | ⚠ Uses legacy `ManifestWriter.add()/.write()` with inline bucket | `risk_snapshot_sink.py` |
| `pnl/cli/handlers/compute_handler.py` | ⚠ Uses legacy `ManifestWriter.add()/.write()` with inline bucket | `compute_handler.py` |
| `engine/core/gcs_storage_service.py` (primary output: strategy_instructions) | ❌ **NO manifest emission** — writes strategy_instructions parquet via DataSink but does NOT call any `record_*` or `ManifestWriter` | `gcs_storage_service.py` — zero manifest hits |

**Critical gap**: `gcs_storage_service.py` writes the primary output (`strategy_instructions` parquet
shards — the signal that execution-service reads) without any manifest emission. Downstream
preflight gates cannot verify "did strategy run for date=X, strategy_id=Y?" against a manifest.
The `manifest_allocation_guard.py` reads IS manifest (for upstream availability check) but
strategy-service does not write its own manifest for execution-service to read.

### Dim 4 — Manifest schema version per bucket

strategy-service writes to `strategy-store-{project_id}`, not to the IS/MTDS manifest buckets.
Its ManifestWriter calls target the `strategy-store-*` catalogue bucket.

| Bucket | Schema version | Action |
| ------ | -------------- | ------ |
| `gs://strategy-store-{project_id}/` | Undetermined — uses legacy `ManifestWriter.add()/.write()` API in most writers; schema version not audited directly | AUDIT NEEDED |
| `gs://instruments-store-defi-{project_id}/` | v8 (per C1 audit) | OK — read-only by strategy-service |

**Key finding**: `hedge_ratio_writer.py` and `decision_context_writer.py` use `record_captured()` which is the v8 API. `cloud_strategy_storage.py` uses the older `ManifestWriter.add()/.write()` API — unclear whether this writes v8 rows.

---

## Pattern 1 — SSOT-owned reference flowing down

### Findings

**P0 Finding**: `discover_instruments()` in `strategy_config_loader.py` reads IS catalogue via
`instruments-store-defi` parquet — **but only for DeFi strategies with a GCS config**. The
code path is gated by `if is_defi` (line 635) and `if _gcs_config` (line 651). For CeFi/TradFi,
IS is never consulted for universe.

**P0 Finding**: `venue_map` in `discover_instruments()` only covers three DeFi lending protocols:
```python
venue_map = {
    "AAVE_V3": f"AAVEV3-{chain}",
    "COMPOUND_V3": f"COMPOUNDV3-{chain}",
    "MORPHO": f"MORPHO-{chain}",
}
```
Other DeFi venues (Uniswap, Curve, Drift, etc.) are not in this map — `discover_instruments()`
returns `[]` for them (line 165-167 warn + return).

**P0 Finding**: `discover_instruments()` silently returns `[]` on GCS read failure (line 215-221
`except Exception`), rather than raising `DependencyError`. This means IS unavailability during
discovery is invisible to the caller.

**P1 Finding**: `cli/resolvers.py:INSTRUMENT_SHORTCUTS` provides hardcoded CeFi/TradFi CLI
defaults. These are documented as "CLI shortcuts" but effectively define the production universe
when no explicit instruments are passed via `--instruments`.

**P1 Finding**: `target_universe/catalog.py` builds the entire v2 strategy dispatch table from
hardcoded (venue, instrument, timeframe) tuples without any IS read. IS listings/delistings
cannot influence this catalog without a code change.

---

## Pattern 2 — Manifest emission discipline

### Findings

**P0 Finding**: The primary output writer (`gcs_storage_service.py`) writes `strategy_instructions`
parquet to GCS with zero manifest emission. No `record_captured`, no `record_empty`, no
`record_failed`. Execution-service cannot run a data-driven preflight gate against strategy
output coverage.

**P1 Finding**: `cloud_strategy_storage.py` uses the legacy `ManifestWriter.add()/.write()` 2-call
API rather than the v8 `record_captured(data_type=..., row_key=..., ...)` single-call API. The
`catalogue_bucket` is constructed inline: `f"strategy-store-{cfg.project_id}"` instead of
`resolve_bucket_name(...)`.

**P1 Finding**: `hedge_ratio_writer._record_manifest()` and `decision_context_writer._record_manifest()`
swallow manifest-write exceptions (`except Exception: logger.debug(...)`). Manifest failures are
invisible in production logs (DEBUG level).

**P2 Finding**: None of the manifest writers in strategy-service emit `record_empty()` or
`record_failed()` calls. The 4-state `capture_status` discipline is not implemented for
strategy-service outputs.

---

## Pattern 3 — Schema-version compliance

Not directly applicable to IS→strategy reads (strategy-service reads IS-written parquet, not
manifest index rows). The relevant schema concern is for strategy-service's own manifest writes:

**Finding**: Strategy-service uses a mix of `ManifestWriter.add()/.write()` (legacy) and
`record_captured()` (v8). No code in strategy-service hardcodes `schema_version < 8`. The
legacy `.add()/.write()` API schema version is UTL-internal — no violation at code level.

---

## Pattern 4 — Honest-absence reason taxonomy

Not applicable: strategy-service does not call `record_empty()` anywhere. This is a gap
(see Pattern 2 findings) but not a "wrong reason" violation.

---

## Pattern 5 — `expected_coverage()` preflight + `DIVERGENT_EMPTY` post-hoc check

**Finding**: strategy-service is a consumer of upstream manifests (via `manifest_allocation_guard.py`
which reads IS availability index). It does not run `expected_coverage()` for its own outputs.
No post-hoc divergence scanner exists for `strategy-store-*` outputs.

---

## Pattern 6 — Error classification at the boundary

### Findings

**P0 Finding** (confirmed from A5 phase): `batch_handler.py:127-140` — when `fail_on_missing_deps=False`
and IS/features-service are unavailable, the handler calls `logger.warning()` and `emit_preflight_skip()`
but does NOT raise `DependencyError`. The code continues running strategy on degraded inputs. The
condition is `elif failures: logger.warning("⚠️ %s dependencies not available (continuing anyway)")`.

**P0 Finding** (confirmed from A5 phase): `batch_handler.py:494-508` — `validate_batch_completeness()`
returns `(is_complete, missing)` but on `not is_complete` the handler only calls `logger.warning()`;
it does NOT raise `DependencyError` and does NOT emit `record_failed`. Silent degraded runs proceed.

**P1 Finding**: `discover_instruments()` in `strategy_config_loader.py:215-221` swallows all
exceptions from the GCS read and returns `[]`. This is effectively a "warn-but-proceed" on IS
unavailability — the IS dependency check passes (bucket exists) but the actual catalogue read
can fail silently.

**P1 Finding**: `classify_and_emit_error()` is used in `strategy_config_loader.py` (lines 45-50,
74-78, 216-220) — **this is the UTL wrapper, not `classify_venue_error()` from UAC**. The UTL
wrapper classifies generically; it does not follow the FAIL/RETRY/SKIP prefix taxonomy from
`unified_api_contracts.canonical.crosscutting.errors.classify_venue_error`. For strategy-service
as a consumer (not an adapter), this is a P2 concern rather than P0.

**Positive**: `dependency_checker.py` correctly raises `DependencyError` in the `fail_on_missing_deps=True`
path (line 123), gated by `emit_preflight_skip()` before the raise.

---

## Pattern 7 — Bucket-SSOT

### Findings

**P1 Finding**: `hedge_ratio_writer.py:136` and `decision_context_writer.py:149`:
```python
catalogue_bucket = f"strategy-store-{cfg.project_id}"
```
These are inline f-string bucket constructions bypassing `resolve_bucket_name()`. QG STEP 5.69
should catch these; they are inside `_record_manifest()` exception handlers so they may be
exempt from QG scan.

**P1 Finding**: `cloud_strategy_storage.py:189, 266, 344` — same pattern:
```python
bucket = f"strategy-store-{cfg.project_id}"
```
Three occurrences in the manifest-writer exception blocks.

**Clean**: Primary bucket resolution throughout strategy-service uses `resolve_bucket_name(...)`:
- `strategy_config_loader.py:36, 62, 176` — `resolve_bucket_name(cloud=get_cloud_provider(), kind=..., asset_group=...)`
- `pnl/adapters/domain_adapter.py` — `resolve_bucket_name(...)`
- `gcs_storage_service.py` — uses `config.get_output_bucket()` which is a template format, not `resolve_bucket_name`

**P2 Finding**: `gcs_storage_service.py` uses `config.get_output_bucket()` (returns `output_bucket_template.format(project_id=...)`) rather than `resolve_bucket_name()`. This is a bypass of the canonical SSOT. The template `"strategy-store-{project_id}"` is hardcoded in `config.py:407-408` not derived from `deployment-service/configs/cloud-providers.yaml`.

**Clean**: No inline `gs://` f-strings with hardcoded bucket names. All `f"gs://..."` constructions in `gcs_storage_service.py` use `self.bucket_name` variable (resolved via `_get_shared_bucket()`) — not raw bucket strings. All have `# noqa: gs-uri` comments indicating intentional use of resolved bucket variable.

---

## P-numbered findings summary

| ID | Severity | Pattern | Finding | File:Lines |
| -- | -------- | ------- | ------- | ---------- |
| F1 | P0 | P6 | `fail_on_missing_deps=False` path warns but does NOT raise `DependencyError` on IS absence — strategy runs on degraded inputs silently | `batch_handler.py:127-140` |
| F2 | P0 | P6 | `validate_batch_completeness()` fail path uses `logger.warning()` only — no `DependencyError`, no `record_failed` | `batch_handler.py:501-508` |
| F3 | P0 | P2 | `gcs_storage_service.py` writes primary `strategy_instructions` output with zero manifest emission (`record_captured/empty/failed`) | `gcs_storage_service.py` — no ManifestWriter calls |
| F4 | P0 | P1 | `discover_instruments()` returns `[]` silently on GCS exception — IS unavailability during universe discovery is invisible; no `DependencyError` raised | `strategy_config_loader.py:215-221` |
| F5 | P1 | P1 | `cli/resolvers.py` hardcodes CEFI/TradFi default instrument universes (BTC/ETH/SOL/SPY); IS not consulted for these categories | `resolvers.py:13-20, 48-56` |
| F6 | P1 | P1 | `target_universe/catalog.py` v2 instance universe is a static compiled list; IS listings/delistings do not propagate | `catalog.py:57+` |
| F7 | P1 | P1 | `venue_map` in `discover_instruments()` covers only 3 DeFi protocols; other DeFi venues return `[]` silently | `strategy_config_loader.py:160-167` |
| F8 | P1 | P2 | All 5 legacy ManifestWriter call sites use `ManifestWriter.add()/.write()` (not v8 `record_captured`) and inline `f"strategy-store-{cfg.project_id}"` bucket | `cloud_strategy_storage.py:189,266,344` + `risk_snapshot_sink.py` + `compute_handler.py` |
| F9 | P1 | P2 | `hedge_ratio_writer` + `decision_context_writer` swallow manifest failures at DEBUG level — best-effort only | `hedge_ratio_writer.py:148-153`, `decision_context_writer.py:161-166` |
| F10 | P1 | P7 | 5 inline `f"strategy-store-{cfg.project_id}"` catalogue_bucket constructions bypass `resolve_bucket_name()` | `cloud_strategy_storage.py:189,266,344`, `hedge_ratio_writer.py:136`, `decision_context_writer.py:149` |
| F11 | P2 | P7 | `gcs_storage_service.py` uses `config.get_output_bucket()` (template format) not `resolve_bucket_name()` — SSOT bypass | `gcs_storage_service.py:58-65` |
| F12 | P2 | P1 | `fill_subscriber.py:DEFI_FILL_VENUES` hardcodes DeFi PubSub venue subscription list; IS not consulted | `fill_subscriber.py:25` |
| F13 | P2 | P5 | No `record_empty()` or `record_failed()` emitted by strategy-service for any output; 4-state manifest discipline absent | workspace-wide |

---

## Pre-audit evidence: grep outputs

```bash
# Hardcoded URL constants in strategy-service handlers:
strategy_service/position/position_interface/adapters/betfair.py: _JSONRPC_URL = "https://..."
strategy_service/position/position_interface/adapters/binance.py: _MAINNET_BASE + _TESTNET_BASE
strategy_service/position/position_interface/adapters/bybit.py:   _MAINNET_BASE + _TESTNET_BASE
strategy_service/position/position_interface/adapters/upbit.py:   _BASE_URL
strategy_service/position/position_interface/adapters/polymarket.py: _GAMMA_BASE
# NOTE: these are live execution adapters (position-interface), NOT IS-derived data URLs.
# They represent REST API endpoints for order submission, not reference data URLs.
# These are P7-pattern clean under the position-interface URL scope (live trading adapter).

# IS catalogue read calls:
strategy_config_loader.py:176: resolve_bucket_name(..., kind="instruments-store", asset_group="defi")
strategy_config_loader.py:177: path = f"instrument_availability/by_date/day={date_str}/venue={venue}/instruments.parquet"

# Manifest emission per file:
hedge_ratio_writer.py: record_captured (QG-allow; best-effort)
decision_context_writer.py: record_captured (QG-allow; best-effort)
cloud_strategy_storage.py: ManifestWriter.add()/.write() (legacy API x3)
gcs_storage_service.py: 0 manifest calls

# Bucket-SSOT resolve_bucket_name usage:
strategy_config_loader.py:36,62,176 — ✅ resolve_bucket_name
pnl/adapters/domain_adapter.py     — ✅ resolve_bucket_name
hedge_ratio_writer.py:92           — ✅ resolve_bucket_name (data write bucket)
hedge_ratio_writer.py:136          — ❌ f"strategy-store-{cfg.project_id}" (manifest bucket)
decision_context_writer.py:105     — ✅ resolve_bucket_name (data write bucket)
decision_context_writer.py:149     — ❌ f"strategy-store-{cfg.project_id}" (manifest bucket)
cloud_strategy_storage.py:189,266,344 — ❌ f"strategy-store-{cfg.project_id}" (manifest bucket x3)
```

---

## QG status: gaps in current quality-gates.sh (strategy-service)

| Pattern | QG step | Status in strategy-service QG |
| ------- | -------- | ------------------------------ |
| P1 — SSOT-owned reference | `no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` | **NOT WIRED** — `scripts/quality-gates.sh` has no call to these scripts |
| P2 — Manifest emission | `no_silent_absence_handlers.sh` | **NOT WIRED** — but note: strategy-service is a consumer, not a capture pipeline; handler definition of "silent absence" needs per-service adaptation |
| P3 — Schema-version | Inline `rg 'schema_version\s*=\s*[1-7]'` | N/A — no schema_version constants in strategy-service code |
| P4 — Honest-absence reasons | Inline `rg 'record_empty.*reason\s*=\s*""'` | N/A — no `record_empty()` calls |
| P6 — Error classification | `no_adapter_contract_regression.sh` (STEP 5.83) | Status unknown — `quality-gates.sh` does not show this wired explicitly |
| P7 — Bucket SSOT | `check_inline_bucket_uri.py` (STEP 5.69) | Ratchet exclusion exists: `HARDCODED_PROJECT_EXCLUDE_GLOBS=("!**/engine/core/strategy_config_loader.py")` but catalogue_bucket f-strings in writers are NOT excluded |

---

## Phased remediation DAG

```
Phase 1 — Fix F1/F2: DependencyError discipline in batch_handler
   │  batch_handler.py warn-but-proceed paths → raise DependencyError(fail_fast=True)
   │  validate_batch_completeness fail → emit record_failed + raise
   │
   ├── Phase 2 — Fix F3: Add manifest emission to gcs_storage_service.py
   │   strategy_instructions write → record_captured(data_type="strategy_instructions",
   │   row_key={date, strategy_id}, ...)
   │   (PARALLEL with Phase 1)
   │
   ├── Phase 3 — Fix F4/F7: discover_instruments() hardening
   │   → raise DependencyError on GCS read failure
   │   → expand venue_map to cover DeFi execution venues
   │   (PARALLEL with Phase 2)
   │
   ├── Phase 4 — Fix F8/F10: ManifestWriter migration
   │   cloud_strategy_storage.py: legacy .add()/.write() → record_captured() + resolve_bucket_name
   │   risk_snapshot_sink.py + compute_handler.py: same migration
   │   hedge_ratio_writer + decision_context_writer: inline bucket → resolve_bucket_name
   │   (PARALLEL with Phase 3)
   │
   ├── Phase 5 — Fix F5/F6: IS-driven universe for CeFi/TradFi (operator decision required)
   │   resolvers.py: CEFI/TRADFI defaults → IS-read via discover_instruments() equivalent
   │   catalog.py: IS-derived at build time or runtime refresh
   │   NOTE: this requires IS to have per-date CeFi/TradFi listings — confirm IS coverage first
   │   BLOCKED-OPERATOR-DECISION: scope of IS-driven CeFi universe (vs static shortcuts)
   │
   └── Phase Q — QG enforcement (wire scripts into quality-gates.sh)
       Wire no_hardcoded_venue_urls.sh + no_hardcoded_venue_universe.sh
       Add record_captured check for gcs_storage_service.py output writers
       Wire check_inline_bucket_uri.py to flag catalogue_bucket f-strings

Phase D — Codex update follows Phase Q
```

**Foundation-completion-gate rule**: Phase 1 (DependencyError discipline) and Phase 2
(strategy_instructions manifest emission) must be GREEN before execution-service can
run IS-sourced preflight against strategy output coverage.

---

## Continuous verification

| Pattern | Continuous-verification path | Cadence | Last verified |
| ------- | ----------------------------- | ------- | ------------- |
| P1 — IS consumption | `no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` (once wired to QG) | every push | NOT YET WIRED |
| P2 — Manifest emission | `record_captured` check on gcs_storage_service.py (once added to QG) | every push | NOT YET WIRED |
| P3 — Schema-version | N/A — no hardcoded schema_version < 8 in code | — | clean |
| P4 — Honest-absence | `LegacyBlankErrorReasonError` at runtime (N/A — no record_empty calls) | — | N/A |
| P5 — expected_coverage | Post-hoc DIVERGENT_EMPTY scanner for strategy-store (not yet built) | daily | NOT YET BUILT |
| P6 — Error classification | Manual audit; no_adapter_contract_regression.sh (once wired) | every push | NOT YET WIRED |
| P7 — Bucket SSOT | `check_inline_bucket_uri.py` STEP 5.69 (catalogue_bucket f-strings not excluded) | every push | PARTIAL |

---

## Scope exclusions

**P3 (schema-version)**: No `schema_version` constants exist in strategy-service code. Verified clean
at commit `fcdf3c96`. ManifestWriter API version is UTL-internal; no code-level violation.

**P4 (honest-absence reasons)**: No `record_empty()` calls exist in strategy-service. The absence
of `record_empty()` is itself a P2/P3 finding (see F13), but there are no *incorrect reason string*
violations.

**Position-interface adapter URLs**: `binance.py`, `bybit.py`, `betfair.py`, `upbit.py`, `polymarket.py`
all have hardcoded live-trading API URLs. These are **execution adapter endpoints** (order submission),
not IS-derived reference data URLs. They are out-of-scope for this audit's P1 pattern — the
anti-pattern targets data archive/universe URLs, not live trading REST endpoints. These are
documented at their declaration sites and are architecturally correct per the IS→MTDS contract
SSOT distinction (IS owns archive metadata; execution adapters own their API endpoints).

---

## Temporary states + their canonical follow-up plans

- **F5/F6 (CeFi/TradFi IS-driven universe)**: BLOCKED-OPERATOR-DECISION. Static shortcuts
  are intentional for May-23 go-live (speed). Successor: `plans/active/is_strategy_universe_ceti_tradfi_2026_05_20.md`
  (to be created when operator decides scope). Per CLAUDE.md rule: deferred only with named
  successor.
- **Legacy ManifestWriter.add()/.write()**: transitional until Phase 4 migration. retire when
  cloud_strategy_storage.py migrates to `record_captured()` API.
- **catalogue_bucket f-strings**: transitional until Phase 4 adds `resolve_bucket_name()` to
  the manifest-writer helper paths.

---

## Known A-phase findings disposition

| Finding | Status | Evidence |
| ------- | ------ | -------- |
| A5: `batch_handler.py:130` warn-but-proceed | **CONFIRMED P0** — `elif failures: logger.warning("continuing anyway")` at line 128-130 | F1 above |
| A5: `batch_handler.py:502` warn-but-proceed | **CONFIRMED P0** — `validate_batch_completeness` fail at lines 501-508 uses warning only | F2 above |
| A4: 0% v8 manifest — legacy-fallback readers | **NOT CONFIRMED** — no schema_version < 8 constants; no legacy v4/v5 readers in strategy-service | P3 scope exclusion above |
| A6: strategy-service IS reads | **CONFIRMED PARTIAL** — DeFi IS reads exist via `discover_instruments()`; CeFi/TradFi bypass IS entirely | F4/F5/F7 above |
