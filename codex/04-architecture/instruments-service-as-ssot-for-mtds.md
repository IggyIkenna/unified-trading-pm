# instruments-service as SSOT for MTDS — Architecture Contract

> **Codified**: 2026-05-20 (is_mtds_contract_audit_2026_05_20 Phase 8)
> **SSOT plan**: `plans/active/is_mtds_contract_audit_2026_05_20.md`

## The contract

instruments-service is the **single source of truth** for all venue reference data consumed by MTDS handlers.
MTDS handlers MUST NOT hardcode venue URLs, universe lists, or coverage windows — they derive these at
runtime from the instruments-service catalogue.

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
                    │    listed_at/delisted_at        │
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

## What instruments-service owns (in InstrumentRecord)

| Field | Type | Role |
|---|---|---|
| `source_archive_url_template` | `str \| None` | Parameterised S3/HTTP archive URL — `{market}`, `{record_type}`, `{year}`, `{day}` substitution slots |
| `source_record_types` | `dict[str, str] \| None` | Logical → archive record-type name mapping (e.g. `{"trades": "tradeRecords"}`) |
| `source_coverage_start` | `dict[str, date] \| None` | Per data_type first date with records |
| `source_coverage_end` | `dict[str, date] \| None` | Per data_type last date with records (drives `EXPECTED_PAST_SOURCE_COVERAGE_END`) |

## Banned patterns in MTDS handlers

```python
# ❌ BANNED — hardcoded URL constant
_DRIFT_S3_BASE = "https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/..."

# ❌ BANNED — hardcoded universe list
SOLANA_LST_TOKENS = {"jitoSOL": {...}, "mSOL": {...}, ...}
_DRIFT_MARKETS = ["SOL-PERP", "BTC-PERP", ...]
_PHOENIX_PAIRS = ["SOL/USDC", ...]

# ✅ CORRECT — derive from IS catalogue at call time
instruments = await load_solana_defi_metadata_for_date(session, date)
for inst in instruments:
    url = inst.source_archive_url_template.format(market=inst.raw_symbol, ...)
```

## Manifest emission requirement (one of these per shard)

Every `handle_*`, `collect_*`, `backfill_*`, `_fetch_*` function MUST emit exactly one manifest call:

| Outcome | Call |
|---|---|
| Data fetched successfully | `recorder.record_captured(...)` |
| Expected empty (e.g. past archive end) | `recorder.record_empty(reason="EXPECTED_PAST_SOURCE_COVERAGE_END")` |
| Fetch failed with error | `recorder.record_failed(error=exc, ...)` |
| Upstream IS catalogue says empty | `recorder.record_expected_unattempted(reason=...)` |

Silent returns (no manifest call) are banned. QG STEP `no_silent_absence_handlers.sh` enforces.

## QG enforcement (STEP 5.70)

Three scripts under `unified-trading-pm/scripts/qg/` run in both instruments-service and MTDS quality gates:

| Script | What it blocks |
|---|---|
| `no_silent_absence_handlers.sh` | handlers that return without any manifest emission |
| `no_hardcoded_venue_urls.sh` | `_*_S3_BASE\s*=`, `"https://.*\.s3\.` literals, hardcoded API host strings |
| `no_hardcoded_venue_universe.sh` | `SOLANA_LST_TOKENS\s*=`, `_DRIFT_MARKETS\s*=`, `_PHOENIX_PAIRS\s*=`, `_LST_TOKENS\s*=`, `_MARKET_LIST\s*=`, `_UNIVERSE\s*=` |

## Coverage-end honest-absence pattern

When `source_coverage_end[data_type]` is set on an `InstrumentRecord`, MTDS handlers must check the target date:

```python
if target_date > inst.source_coverage_end.get("trades", date.max):
    recorder.record_empty(
        venue=inst.venue,
        chain=inst.chain,
        data_type="perp_funding",
        reason="EXPECTED_PAST_SOURCE_COVERAGE_END",
        pipeline_mode=PipelineMode.BATCH_ONCHAIN_RPC,
    )
    return 0
```

This drives `empty_confirmed` rows in the manifest (not `attempted_failed`), signalling to downstream consumers that the
absence is by-design, not a fetch error. See `honest-absence-downstream-handling.md` § "Reason taxonomy" for the full
`EXPECTED_PAST_SOURCE_COVERAGE_END` entry.

## Solana DeFi reference implementation

- **instruments-service adapter**: `instruments_service/reference_data/adapters/defi/drift.py`
  — populates `source_archive_url_template`, `source_record_types`, `source_coverage_start/end`
- **MTDS handler**: `market_tick_data_service/cli/handlers/solana_defi_handler.py`
  — `_backfill_drift_s3_date()` derives S3 URL from IS catalogue, checks `_DRIFT_S3_ARCHIVE_END`

## Related docs

- `codex/02-data/honest-absence-downstream-handling.md` § "Reason taxonomy" — full `error_reason` matrix including `EXPECTED_PAST_SOURCE_COVERAGE_END`
- `codex/02-data/availability-manifest-and-data-status.md` — manifest schema + `capture_status` state machine
- `plans/active/is_mtds_contract_audit_2026_05_20.md` — Phase 1-8 remediation plan
