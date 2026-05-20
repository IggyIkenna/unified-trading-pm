---
name: is_mtds_contract_audit_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: refactor
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 5.6
status: in-flight
deadline: 2026-05-23
priority: P0
parent_epic: manifest_evolution_master_2026_05_08
epic_secondary: instruments_live_master_2026_05_08
parent_plan: master_to_live_defi_2026_05_23.md
related_plans:
  - honest_coverage_formula_consolidation_2026_05_19.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
  - expected_unattempted_propagation_chain_2026_05_12.md
  - cross_asset_instruments_service_scope_2026_05_14.md
---

# instruments-service ↔ MTDS Contract Audit + Remediation — 2026-05-20

> **Trigger**: Drift S3 backfill silent-absence finding (2026-05-19) escalated to a workspace
> audit (2026-05-20). The audit found 6+ MTDS handlers hardcode venue URLs/universes despite
> instruments-service already providing the canonical adapter, and NO QG step today enforces
> the no-silent-absence or no-hardcoded-universe rules. Operator framing: "the pattern is
> supposed to be instruments-service holds availability + reference data; if we're resolving
> ids ourselves in MTDS, instruments-service becomes redundant. Solve it properly from the
> root across the chain even if it means backfilling instruments-service again."

## The architectural contract (SSOT)

```
                    ┌────────────────────────────────┐
                    │  instruments-service           │
                    │  ─ enumerates venue universe   │
                    │  ─ writes InstrumentRecord     │
                    │    per (venue, instrument_id,  │
                    │    day) to instruments-store-* │
                    │  ─ owns archive metadata:      │
                    │    url_template, record_type   │
                    │    names, coverage_start/end,  │
                    │    listed_at/delisted_at       │
                    └────────────┬───────────────────┘
                                 │
                                 ▼ read-only catalogue
                    ┌────────────────────────────────┐
                    │  MTDS handler                  │
                    │  ─ calls load_*_metadata_      │
                    │    for_date(...) FIRST         │
                    │  ─ derives URLs from metadata, │
                    │    NEVER hardcodes             │
                    │  ─ emits record_captured /     │
                    │    record_empty(reason=...) /  │
                    │    record_failed per shard     │
                    └────────────────────────────────┘
```

Banned in MTDS handlers:
- Hardcoded venue URLs (`_DRIFT_S3_BASE = "https://..."`)
- Hardcoded universe lists (`SOLANA_LST_TOKENS = [...]`)
- Re-fetching venue API to enumerate markets when IS already wrote them
- Any code path that returns from `handle_date()` without emitting at least one
  `recorder.record_*(...)` for the (data_type, instrument_id, day) shard it visited

## 4-dimensional audit matrix (2026-05-20 snapshot)

### Dim 1 — IS adapter coverage per asset_group

| asset_group | Working adapters | Stubs | MTDS-uses-but-no-IS-call (the violation) |
|---|---|---|---|
| CEFI | Aster, Deribit, Tardis, CCXT, Hyperliquid | none | none |
| DeFi | 54 adapters incl. Drift, Phoenix, Orca, Raydium, Marinade, Jito | none | Drift, Phoenix, Marinade, Jito, native-staking (LSTs) — adapters EXIST in IS; MTDS ignores them |
| TradFi | Databento, Polygon, IBKR Futures, TradFi_Live | none | none |
| Sports | factory + 11 per-source adapters | none | none |
| Prediction | Polymarket, Kalshi | none | none |

### Dim 2 — MTDS handler IS-consumption status

| Handler | Status | Citation |
|---|---|---|
| `dex_pools_handler.py` | ✅ Reads IS via `load_pool_metadata_for_date()` | lines 90-120 |
| `dex_swaps_handler.py` | ✅ Reads IS | lines 75-95 |
| `lending_indices_handler.py` | ✅ Reads IS via `load_lending_metadata_for_date()` | lines 210-240 |
| `evm_defi_handler.py` | ✅ Reads IS via `load_instrument_catalog()` | lines 95-115 |
| `liquidations_handler.py` | ✅ Reads IS | lines 80-105 |
| `oracle_prices_handler.py` | ✅ Reads IS via `load_price_feed_metadata()` | lines 120-140 |
| `gas_fee_handler.py` | ✅ Validates against IS networks | lines 95-110 |
| `governance_*_handler.py` | ✅ Reads IS venue metadata | lines 60-100 |
| `liquidation_events_handler.py` | ✅ Reads IS | lines 110-130 |
| `mev_events_handler.py` | ✅ Reads IS | lines 95-115 |
| `eigenlayer_rewards_handler.py` | ✅ Reads IS | lines 75-95 |
| `bridge_events_handler.py` | ✅ Reads IS | lines 80-100 |
| `flash_loan_events_handler.py` | ✅ Reads IS | lines 65-80 |
| `token_transfers_handler.py` | ✅ Reads IS | lines 100-125 |
| `vault_share_price_handler.py` | ✅ Reads IS | lines 80-105 |
| **`solana_defi_handler.py`** | **❌ Hardcodes Drift S3 + Phoenix + Solana protocol URLs** | **lines 164-203, 1101-1199** |
| **`perp_funding_handler.py`** | **⚠ Hardcodes Drift market list** | **line 145** |
| **`lst_rates_handler.py`** | **⚠ Hardcodes Solana LST URLs** | **lines 135-160** |
| **`native_staking_handler.py`** | **⚠ Hardcodes Solana staking endpoint** | **line 85** |
| **`staking_yields_handler.py`** | **⚠ Hardcodes Lido/Marinade URLs** | **lines 110-135** |
| **`solana_lst_archival.py`** | **⚠ Hardcodes Marinade/Jito endpoints** | **lines 75-95** |
| `position_data_handler.py` | ⚠ Partial — fallback hardcodes some exchanges | lines 200-215 |
| `tick_data_handler.py` | ⚠ Partial — fallback hardcodes exchange list | line 200 |
| `websocket_streaming_handler.py` | ⚠ Partial — hardcodes Solana RPC | line 220 |
| `data_manifest_handler.py` | (legacy generator, separate scope) | — |
| `replay_handler.py` | (legacy replay, separate scope) | — |

### Dim 3 — Manifest emission discipline

| Handler | Status | Evidence |
|---|---|---|
| 22 of 26 handlers | ✅ Emit `record_captured` + `record_empty` + `record_failed` per shard | dex_pools 399-415 is the canonical pattern |
| **`solana_defi_handler.py`** Drift backfill | **❌ Silent absence** | lines 1101-1199: zero `record_*` calls |
| `data_manifest_handler.py` | ❌ Legacy generator (intent unclear) | needs audit |
| `replay_handler.py` | ❌ Legacy replay | needs audit |
| `tick_data_handler.py` | ❌ Raw tick passthrough | needs audit |

### Dim 4 — Manifest schema version per bucket

| Bucket | Schema version | Action |
|---|---|---|
| `gs://market-data-tick-{cefi,defi,tradfi,sports,prediction}-…` | v8 | OK |
| `gs://lending-indices-…` | v8 | OK |
| `gs://instruments-store-…` | v8 | OK (per sports manifest probe) |
| **`gs://solana-defi-central-element-323112/`** | **v4 (hardcoded in `data_manifest_handler.py:242`)** | **MIGRATE to v8** |

## Pre-Audit Before Execution (Citadel-Grade)

Workspace-wide consumers/symbols this plan touches:

```bash
# Adapter-archive-metadata users:
rg -l "_DRIFT_S3_BASE|_PHOENIX_QUOTE_ROUTE|SOLANA_LST_TOKENS|MARINADE_API_URL" \
   --type py --glob '!.venv*' --glob '!tests'

# Handlers without record_* calls:
for h in market-tick-data-service/.../cli/handlers/*.py; do
  if ! grep -q 'record_captured\|record_empty\|record_failed' "$h"; then
    echo "SILENT-ABSENCE CANDIDATE: $h"
  fi
done

# load_*_metadata_for_date callers (the ✅ pattern):
rg 'load_.*_metadata_for_date' --type py
```

## Phased execution DAG

```
Phase 1 (UAC schema)
   │
   ├── Phase 2 (IS adapter writes new fields) ──┐
   │                                            │
   ├── Phase 3 (MTDS handlers consume IS) ──────┼──> Phase 5 (re-backfill) ──> Phase 6 (verify)
   │                                            │
   ├── Phase 4 (solana-defi v4→v8 migration) ──┘
   │
   └── Phase 7 (QG enforcement — new ratchet steps)

Phase 8 — codex docs follows everything
```

### Phase 1 — UAC schema extension

- [ ] **P0. Extend `InstrumentRecord`** in `unified-api-contracts/unified_api_contracts/internal/reference/instrument.py`
      with new optional fields:
      - `source_archive_url_template: str | None` (e.g. `"https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/{program_id}/market/{market}/{record_type}/{year}/{day}"`)
      - `source_record_types: dict[str, str] | None` (data_type → archive record-type name, e.g. `{"trades": "tradeRecords", "funding_rate": "fundingRateRecords"}`)
      - `source_coverage_start: dict[str, date] | None` (per data_type)
      - `source_coverage_end: dict[str, date] | None` (per data_type — the EXPECTED_PAST_SOURCE_COVERAGE_END trigger)
      - `listed_at: date | None`, `delisted_at: date | None` (some IS adapters already populate)
- [ ] **P0. Add `EXPECTED_PAST_SOURCE_COVERAGE_END`** to `EmptyConfirmedReason` in `unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py`.
      Sister of `EXPECTED_PRE_SOURCE_COVERAGE_START` (already exists). Reason: archive stopped writing on a known date (e.g. Drift tradeRecords ended 2025-01-08).
- [ ] **P0. Test**: roundtrip Pydantic write + read of `InstrumentRecord` with new optional fields.

### Phase 2 — IS adapter migration (writes new fields)

Each existing IS adapter must populate the new archive-metadata fields. Priority order = audit Dim 1 violations:

- [ ] **P0. Drift** (`instruments-service/instruments_service/reference_data/adapters/defi/drift.py`):
      Set `source_archive_url_template` + `source_record_types={"trades": "tradeRecords", "funding_rate": "fundingRateRecords", ...}` + `source_coverage_end={"trades": date(2025, 1, 8), ...}` (per direct S3 probe 2026-05-20).
- [ ] **P0. Phoenix** (`adapters/defi/phoenix.py`): same shape, populate Jupiter quote-route metadata.
- [ ] **P0. Marinade** (`adapters/defi/marinade.py`): API URL template + coverage windows.
- [ ] **P0. Jito** (`adapters/defi/jito.py`): same.
- [ ] **P1. Orca / Raydium / others**: populate template fields opportunistically.

### Phase 3 — MTDS handler migration (consume IS, emit manifest)

Each ❌/⚠ handler from Dim 2 + Dim 3 must:
- Call `load_<domain>_metadata_for_date()` FIRST (dex_pools pattern)
- Derive URLs from `record.source_archive_url_template` + `record.source_record_types` — NEVER hardcode
- Wrap every (date × instrument) iteration with `record_captured` / `record_empty(reason=...)` / `record_failed(...)`

- [ ] **P0. `solana_defi_handler.py`**: full rewrite of Drift S3 backfill path (lines 1101-1199).
      Remove `_DRIFT_S3_BASE` (line 165), remove `_collect_drift` hardcoded URL re-fetch (line 419),
      remove hardcoded Phoenix routes (lines 180-203). Call IS DriftReferenceDataAdapter.
- [ ] **P0. `perp_funding_handler.py`**: remove Drift market hardcode at line 145; call IS.
- [ ] **P0. `lst_rates_handler.py`**: remove Solana LST hardcoded URLs (lines 135-160).
- [ ] **P0. `native_staking_handler.py`**: remove hardcoded endpoint at line 85.
- [ ] **P0. `staking_yields_handler.py`**: remove Lido/Marinade hardcodes (lines 110-135).
- [ ] **P0. `solana_lst_archival.py`**: remove Marinade/Jito hardcodes (lines 75-95).
- [ ] **P1. `position_data_handler.py` + `tick_data_handler.py` + `websocket_streaming_handler.py`**:
      remove partial fallback hardcodes.
- [ ] **P1. Legacy intent audit** for `data_manifest_handler.py` / `replay_handler.py`:
      either wire manifest emission OR document why exempt with `# legacy: no manifest emission, see <plan>` comment.

### Phase 4 — solana-defi bucket v4 → v8 migration

- [ ] **P0. Patch `data_manifest_handler.py:242`** — hardcoded `schema_version=4` becomes `schema_version=8`.
- [ ] **P0. Migration script** `instruments-service/scripts/migrate_solana_defi_v4_to_v8.py`:
      walk `gs://solana-defi-central-element-323112/_index/availability_index.parquet`,
      add v8 columns (`capture_status`, `error_reason`, …), backfill `capture_status='captured'` for
      existing rows (best-guess since v4 lacks the distinction — note assumption in plan).
- [ ] **P0. Snapshot v4 manifest** to `_index/snapshots/pre_v8_migration_2026_05_20.parquet` before mutation.

### Phase 5 — Re-backfill where the audit found data corruption

- [ ] **P0. Drift S3 backfill rerun** (after Phase 3 ships): 2020-01-01 → 2025-01-08 (the actual
      coverage window — anything after `EXPECTED_PAST_SOURCE_COVERAGE_END=2025-01-08` is
      auto-recorded as `empty_confirmed`).
- [ ] **P0. Backfill instruments-service** for Solana DeFi venues (Drift, Phoenix, Marinade, Jito,
      Orca, Raydium) so the new archive-metadata fields are populated in the catalogue.
      Operator-acknowledged in this turn's directive ("even if it means backfilling instruments-service again").
- [ ] **P1. Re-backfill other MTDS asset-groups for affected (handler, data_type) pairs** identified
      in Phase 3 after their migrations ship.

### Phase 6 — Real-fleet verification

- [ ] **P0. Re-pull every (asset_group, data_type) cell's `CaptureStatusCounts`** post-Phase 5
      (cross-references honest_coverage Phase 8). Cells reporting 100% with zero
      `expected_unattempted_pending_fetch` ARE NOW MEANINGFUL — denominator includes the Tier-3
      sentinels populated by the IS catalogue.

### Phase 7 — QG enforcement (the gates that should have caught this)

- [ ] **P0. `qg/no_silent_absence_handlers.sh`** in `unified-trading-pm/scripts/qg/`:
      grep every `*_handler.py` in MTDS + instruments-service. For each, find every function whose
      name matches `handle_*|collect_*|backfill_*|_fetch_*` and assert it contains
      a call to one of `record_captured|record_empty|record_failed|record_expected_unattempted`.
      Exempt list (docstring required): `data_manifest_handler.py`, `replay_handler.py`,
      `tick_data_handler.py` until their Phase 3 audit completes.
- [ ] **P0. `qg/no_hardcoded_venue_urls.sh`**: blocklist patterns like
      `_DRIFT_S3_BASE`, `_PHOENIX_QUOTE_ROUTE`, `https://.*\.s3\.` literals in MTDS handlers.
      Handlers MUST source URLs from IS-loaded `InstrumentRecord.source_archive_url_template`.
- [ ] **P0. `qg/no_hardcoded_venue_universe.sh`**: blocklist patterns like
      `SOLANA_LST_TOKENS = [...]`, `DRIFT_MARKETS = [...]`. Universe MUST come from
      `load_*_metadata_for_date()`.
- [ ] **P0. Wire all three** into per-service `quality-gates.sh` (instruments-service + MTDS).
      Pre-existing handlers failing the check produce REVIEW-BLOCKING warnings at PR time.
- [ ] **P1. Cross-link** with `honest_coverage_formula_consolidation_2026_05_19.md` Phase 6
      (the "no inline coverage formula" linter). All three QG steps live in the same script
      bundle.

### Phase 8 — Codex SSOT updates

- [ ] **P0. New** `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` —
      codifies the contract diagram at top of this plan.
- [ ] **P0. Update** `codex/02-data/availability-manifest-and-data-status.md` § "Reason taxonomy"
      to include `EXPECTED_PAST_SOURCE_COVERAGE_END`.
- [ ] **P0. SUPERSEDED banner** on `cross_asset_instruments_service_scope_2026_05_14.md`'s
      "BLOCKED-OPERATOR-DECISION" if Phase 1-3 of this plan resolve it.
- [ ] **P0. CLAUDE.md update** to mention the QG steps in `### Service architecture`.

## Continuous verification

| Item | Cutover criterion | Continuous verification | Last verified |
|---|---|---|---|
| InstrumentRecord schema | Pydantic roundtrip test passes | `pytest tests/.../test_instrument_record_archive_metadata.py` | TBD |
| No-silent-absence | All MTDS handlers emit ≥1 record_* per shard | QG STEP `no_silent_absence_handlers.sh` | TBD |
| No-hardcoded-URLs | grep returns 0 hits | QG STEP `no_hardcoded_venue_urls.sh` | TBD |
| Drift coverage | Manifest shows captured (2020→2025-01-08) + empty_confirmed (2025-01-09→today, reason=EXPECTED_PAST_SOURCE_COVERAGE_END) | Sample query post-Phase-5 backfill | TBD |
| solana-defi schema v8 | `schema_version` column = 8 in manifest | `gsutil cp ... + pandas check` | TBD |

## Temporary states + their canonical follow-up plans

- Drift handler continues running silently (no manifest emission) until Phase 3 ships.
  Mitigation: deleted the running Drift VM at 2026-05-19. New Drift VMs SHALL NOT launch
  until Phase 3 ships.
- solana-defi bucket on v4 until Phase 4. Downstream consumers reading from this bucket
  should be aware (none currently — bucket is write-mostly).

## Scope: all phases pre-May-23 (operator directive 2026-05-20)

All 8 phases are P0 pre-cutover. ~5.6 calibrated AI-days into a 3-day window (today 2026-05-20 → 2026-05-23)
requires fan-out across slots. Parallelizable subdivisions:

- **Phase 1 (UAC schema)** — single slot, ~0.5 day. Blocks everything else, ship first.
- **Phase 2 (IS adapters)** — fan out per venue (Drift / Phoenix / Marinade / Jito / Orca / Raydium), one slot
  per venue, in parallel. ~0.5 day each, can run concurrently with Phase 3.
- **Phase 3 (MTDS handlers)** — fan out per handler. 6 ❌/⚠ handlers + 3 legacy handlers. ~0.4 day each,
  parallel. The Drift handler is critical-path P0; others P0 (no P1 anymore).
- **Phase 4 (solana-defi v4→v8 migration)** — single slot, ~0.5 day. Gated on Phase 2 (Drift adapter writes new
  fields) before migration so v8 rows carry archive metadata.
- **Phase 5 (re-backfill)** — fan out per venue. Bounded by Drift S3 coverage end + IS-bucket fresh write.
  ~1 day total wall-clock (VMs run in parallel).
- **Phase 6 (real-fleet verification)** — single slot, ~0.3 day, AFTER Phase 5.
- **Phase 7 (QG enforcement)** — single slot, ~0.5 day. Can ship in parallel with Phases 2/3 — it gates
  FUTURE merges, doesn't block current phases.
- **Phase 8 (codex docs)** — single slot, ~0.3 day. Last phase.

Critical path (sequential): Phase 1 → (Phase 2/3 in parallel) → Phase 4 → Phase 5 → Phase 6 → Phase 8.
Phase 7 runs orthogonally.

3-day wall-clock fit if 4+ slots run in parallel through Phases 2/3/5.

## Cross-asset note (preserved)

| Item | Status | Successor |
|---|---|---|
| Cross-asset instruments-service extension | BLOCKED-OPERATOR-DECISION (pre-existing) | `cross_asset_instruments_service_scope_2026_05_14.md` |
