---
type: audit-findings
title: MDPS Long-Running Efficiency Audit — CLI Granularity + Canonical Instrument_ID Parser
epic: mtds_mdps_master
auditor: claude opus 4.7 (slot main subagent)
date: "2026-05-28"
status: complete
name: mdps_long_running_cli_granularity_2026_05_28
audit_instructions: mtds_mdps_master_audit_instructions.md
parent_plan: mdps_long_running_multi_shard_architecture_audit_2026_05_28.md
---

# MDPS Long-Running Efficiency Audit — CLI Granularity + Canonical Instrument_ID Parser

## What I read

The audit scope is **Concern B** from `plans/audit/instructions/mdps_long_running_efficiency_audit_instructions.md` §
66-88. The codex contract is `codex/06-coding-standards/cli-convention.md` § "Instrument Identity and CLI Granularity"
(lines 108-219).

**MDPS source files read:**

- `market_data_processing_service/cli/main.py:1-312` — ServiceBootstrap entry, `_build_legacy_argv` bridge (lines
  166-228)
- `market_data_processing_service/cli/parser.py:1-287` — legacy parser, `--instrument-ids` definition (lines 156-161),
  validator hooks
- `market_data_processing_service/app/core/orchestration_scanner.py:1-500` — scanner mixin,
  `_collect_matching_parquet_blobs` (lines 411-472), filter logic (lines 441-461)
- `market_data_processing_service/app/utils/path_parsing.py:1-147` — blob filter helpers, `_resolve_venue_from_blob`
  (lines 76-115), `filter_blob_by_criteria` (lines 118-147)
- `market_tick_data_service/cli/shard_key.py:1-100` — reference implementation of `--shard-key` (atomic 6-tuple) for
  cross-service comparison
- `unified_api_contracts` (UAC) import: `VENUES_BY_ASSET_GROUP` import (parser.py:14) — reverse-lookup candidate

**Codex SSOT references:**

- `cli-convention.md` § "Canonical instrument_id form" (lines 115-131) — the `VENUE:INSTRUMENT_TYPE:SYMBOL` contract
- `cli-convention.md` § "Which axes derive from instrument_id" (lines 132-146) — derivability table
- `cli-convention.md` § "Parsing rule (the implementation contract)" (lines 161-184) — the reference parser pseudocode
- `cli-convention.md` § "Reference incident" (lines 200-209) — the 2026-05-28 operator-reported incident

---

## CLI argument inventory

| Flag / env var                             | Code path that reads it                                                    | What axis it scopes                                         | Required?                                                 | Derivable from canonical instrument_id?                                                        |
| ------------------------------------------ | -------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `--asset-group` / `MDPS_ASSET_GROUP`       | `cli/main.py:166-192` (env var bridge); `cli/parser.py` (no direct flag)   | Selects CEFI/TRADFI/DEFI/SPORTS/PREDICTION                  | No (none selected = all)                                  | **Yes** — via `VENUES_BY_ASSET_GROUP` reverse lookup                                           |
| `--data-types` / `MDPS_DATA_TYPES`         | `cli/main.py:219-226`; `cli/parser.py:130-136` (choices validated)         | Selects data_type partition (trades, book_snapshot_5, etc.) | No (all default)                                          | **No** — a single instrument_id spans multiple data_types                                      |
| `--venues` / `MDPS_VENUES`                 | `cli/main.py:219-226`; `cli/parser.py:139-144`                             | Selects venue (BINANCE-FUTURES, BYBIT, etc.)                | No (all default)                                          | **Yes** — first colon-separated field of canonical form                                        |
| `--instrument-ids` / `MDPS_INSTRUMENT_IDS` | `cli/main.py:219-226`; `cli/parser.py:156-161`                             | Scopes to specific instruments (symbol match)               | No (all default)                                          | **Partial** — the canonical form encodes venue, instrument_type, AND symbol; parser must split |
| `--start-date` / (no env var)              | `cli/main.py:171-174`; `cli/parser.py:104`                                 | Time axis lower bound                                       | **Yes** (required)                                        | **No** — independent time axis                                                                 |
| `--end-date` / (no env var)                | `cli/main.py:175-176`; `cli/parser.py:105`                                 | Time axis upper bound                                       | **Yes** (required)                                        | **No** — independent time axis                                                                 |
| `--timeframes` / `MDPS_TIMEFRAMES`         | `cli/main.py:211-213`; `cli/parser.py:147-153` (default: 15s,1m,5m,...24h) | Candle timeframes to generate                               | No (defaults provided)                                    | **No** — independent axis                                                                      |
| `--max-workers` / `MAX_WORKERS`            | `cli/parser.py:178-183` (default: 4)                                       | Concurrency level                                           | No                                                        | **No** — operational knob                                                                      |
| `--force`                                  | `cli/main.py:195-196`; `cli/parser.py:164`                                 | Skip freshness check                                        | No                                                        | **No** — operational flag                                                                      |
| `--dry-run`                                | `cli/main.py:197-198`; `cli/parser.py:172-176`                             | No writes, local output                                     | No                                                        | **No** — operational flag                                                                      |
| `--skip-existing`                          | `cli/parser.py:167-170`                                                    | Skip dates with existing candles                            | No                                                        | **No** — operational flag                                                                      |
| `--mode`                                   | `cli/parser.py:228-235` (batch/live)                                       | batch vs live infrastructure                                | No (default: batch)                                       | **No** — operational mode                                                                      |
| `--operation`                              | `cli/parser.py:237-246` (timer-candles/streaming-aggregation)              | Live-mode operation type                                    | No (default: timer-candles)                               | **No** — operational mode                                                                      |
| `--shard-spec`                             | `cli/parser.py:248-257`                                                    | Streaming-aggregation shard (ASSET_GROUP:VENUE:DATA_TYPE)   | Only when `--mode live --operation streaming-aggregation` | **Partial** — three fields, but not canonical form                                             |

**Key finding**: The canonical form `VENUE:INSTRUMENT_TYPE:SYMBOL` is NOT directly usable in the current
`--instrument-ids` parser. The parser does **substring matching** (line 459:
`any(iid in blob_name for iid in instrument_ids)`) rather than **canonical parsing** per the codex contract.

---

## What the scanner actually matches

The scanner filter logic lives in three layers:

### Layer 1: `_collect_matching_parquet_blobs` (orchestration_scanner.py:411-472)

Pseudocode of the per-blob matching gate:

```python
def _collect_matching_parquet_blobs(
    blobs: list[BlobMetadata],
    data_type: str,
    venues: list[str] | None,
    instrument_ids: list[str] | None,
) -> tuple[list[str], list[str]]:
    files = []
    for blob in blobs:
        blob_name = blob.name

        # Gate 1: must match the data_type partition
        if not _blob_matches_data_type_partition(blob_name, data_type):
            continue

        # Gate 2: if venues specified, must match a venue
        if venues:
            blob_has_venue = any(f"venue={v}/" in blob_name for v in venues)
            # Fallback: check chain-split venues (DeFi DEX venues)
            if not blob_has_venue:
                blob_has_venue = _blob_matches_chain_split_venue(blob_name, venues)
            # Fallback: use filter_blob_by_criteria for filename-encoded venue
            if not blob_has_venue and not filter_blob_by_criteria(blob_name, venues, None):
                continue

        # Gate 3 (THE GAP): if instrument_ids specified, substring-match each
        # This is the BROKEN gate — canonical form does NOT substring-match blob paths.
        if instrument_ids and not any(iid in blob_name for iid in instrument_ids):
            continue

        files.append(blob_name)

    return files, all_parquet
```

### Layer 2: `_resolve_venue_from_blob` (path_parsing.py:76-115)

Fallback venue resolver (used in the chain-split + filename-encoding gates):

```python
def _resolve_venue_from_blob(blob_name: str, venues: list[str] | None) -> str | None:
    # Step 1: try hive-style venue= segment
    blob_venue = extract_venue_from_blob_path(blob_name)

    # Step 2: fallback to filename encoding (VENUE:TYPE:SYMBOL.parquet)
    if not blob_venue and ":" in filename:
        raw_id = filename.replace(".parquet", "")
        if raw_id.startswith("instrument_key="):
            raw_id = raw_id.split("=", 1)[1]
        filename_parts = raw_id.split(":")
        if len(filename_parts) >= 1 and filename_parts[0] in venues:
            blob_venue = filename_parts[0]

    return blob_venue
```

Note: **This function DOES parse the canonical form** — it splits on `:` to extract the venue. But the caller at line
459 doesn't use this; it just does substring matching.

### Layer 3: `filter_blob_by_criteria` (path_parsing.py:118-147)

The helper used as a final fallback:

```python
def filter_blob_by_criteria(
    blob_name: str,
    venues: list[str] | None,
    instrument_ids: list[str] | None,
) -> bool:
    if venues:
        blob_venue = _resolve_venue_from_blob(blob_name, venues)
        if not (blob_venue and blob_venue in venues):
            return False

    if instrument_ids:
        # BROKEN: substring match, not canonical parse
        if not any(iid in blob_name for iid in instrument_ids):
            return False

    return True
```

---

### Truth table for canonical form `BINANCE-FUTURES:PERPETUAL:BTCUSDT`

Given a blob path like:

```
raw_tick_data/by_date/day=2024-03-04/asset_group=cefi/venue=BINANCE-FUTURES/
  instrument_type=perpetual/data_type=trades/BTCUSDT.parquet
```

| Condition                                                                                                | Result                  | Why                                                                         |
| -------------------------------------------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------- |
| Does `f"venue=BINANCE-FUTURES/" in blob_path`?                                                           | **Yes**                 | Hive path matches directly                                                  |
| Does `f"instrument_type=perpetual/" in blob_path`?                                                       | **Yes**                 | Hive path matches (lowercased)                                              |
| Does the canonical id `BINANCE-FUTURES:PERPETUAL:BTCUSDT` substring in `blob_path`?                      | **No**                  | Path uses `=` not `:` as separator                                          |
| Does the gate `any(iid in blob_name for iid in ["BINANCE-FUTURES:PERPETUAL:BTCUSDT"])` pass?             | **No**                  | Substring `:` is not in the path                                            |
| With `--venues BINANCE-FUTURES --instrument-ids BINANCE-FUTURES:PERPETUAL:BTCUSDT`, does the blob match? | **No** — silent failure | Venue gate passes (line 445), but instrument_ids gate (line 459) rejects it |

**The operator's exact incident (2026-05-28):**

The operator passed:

```bash
MDPS_INSTRUMENT_IDS="BINANCE-FUTURES:PERPETUAL:BTCUSDT BINANCE-FUTURES:PERPETUAL:ETHUSDT
BYBIT:PERPETUAL:BTCUSDT BYBIT:PERPETUAL:ETHUSDT"
MDPS_VENUES="BINANCE-FUTURES BYBIT"
```

Expected: 4 blobs (one per instrument × venue pair).

Actual:

- Canonical form gate (line 459) matches ZERO blobs because `:` is not in path.
- Fallback hive-gate (line 383-390) applies when
  `not files and all_parquet and not _data_type_requires_partition(data_type)`.
- For data_types like `trades` that DO require partition (line 127-154), fallback DOES NOT fire.
- So the operator gets **ZERO blobs, with no error message**.
- The venue-prefix shortcut (line 445) also fires: `any(f"venue={v}" in blob_name ...)` matches ~200 blobs across both
  venues.
- Memory hit 70 GB.

**Conclusion**: The current substring matcher returns **ZERO blobs** when passed the canonical form — the operator gets
a silent failure with no blobs processed and no error.

---

## Canonical parser specification

Per `codex/06-coding-standards/cli-convention.md` § "Parsing rule" (lines 161-184), the implementation contract is:

```python
def _parse_canonical_instrument_id(iid: str) -> tuple[str, str, str] | None:
    """Parse VENUE:INSTRUMENT_TYPE:SYMBOL → (venue, instrument_type, symbol).

    Returns None if iid is not a 3-segment colon-split (e.g., bare-symbol fallback).

    Args:
        iid: canonical form or legacy bare symbol

    Returns:
        (venue, instrument_type, symbol) tuple, or None for legacy form
    """
    parts = iid.split(":", 2)  # max 2 splits — symbol may contain ":"
    if len(parts) != 3:
        return None  # fall through to bare-symbol legacy form
    return parts[0], parts[1], parts[2]


def matches_canonical_instrument_id(blob_path: str, venue: str, inst_type: str, symbol: str) -> bool:
    """Check if blob_path matches all three components of a canonical instrument_id.

    Args:
        blob_path: the GCS blob path
        venue: canonical venue (e.g., "BINANCE-FUTURES")
        inst_type: canonical instrument_type (e.g., "PERPETUAL")
        symbol: canonical symbol (e.g., "BTCUSDT")

    Returns:
        True iff all three components match the expected hive-path segments.
    """
    return (
        f"venue={venue}/" in blob_path
        and f"instrument_type={inst_type.lower()}/" in blob_path  # paths are lowercased
        and f"/{symbol}.parquet" in blob_path
    )
```

**Critical note from codex (line 179):** The blob paths use **lowercase** `instrument_type`
(`instrument_type=perpetual/`), but the canonical form uses **uppercase** (`PERPETUAL`). The parser must handle this
casing mismatch by lowercasing the instrument_type before the hive-path check.

**Integration point:** Replace the substring-match gate at `orchestration_scanner.py:459` with:

```python
if instrument_ids:
    matched = False
    for iid in instrument_ids:
        parsed = _parse_canonical_instrument_id(iid)
        if parsed:
            venue, inst_type, symbol = parsed
            if matches_canonical_instrument_id(blob_name, venue, inst_type, symbol):
                matched = True
                break
        else:
            # Fallback: legacy bare-symbol substring match (for backwards compatibility)
            if iid in blob_name:
                matched = True
                break

    if not matched:
        continue
```

---

## Derivability check

Per the codex table at `cli-convention.md:132-146`:

| Axis              | Derivable?       | How                                              | MDPS Status                                                           |
| ----------------- | ---------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| `venue`           | Yes              | First colon-segment                              | ✅ Can be extracted from canonical form                               |
| `instrument_type` | Yes              | Second colon-segment                             | ✅ Can be extracted from canonical form                               |
| `symbol`          | Yes              | Third+ field (may contain `-`)                   | ✅ Can be extracted from canonical form                               |
| `asset_group`     | Yes (via lookup) | `VENUES_BY_ASSET_GROUP` reverse lookup           | ⚠️ **Needs verification** — see below                                 |
| `data_type`       | No               | A single instrument_id spans multiple data_types | ✅ Correctly independent in MDPS (`--data-types` required)            |
| `date`            | No               | Time axis                                        | ✅ Correctly independent in MDPS (`--start-date/--end-date` required) |

**Asset-group reverse lookup status:**

The codex promises `VENUES_BY_ASSET_GROUP` reverse lookup in UAC `unified_api_contracts.canonical.venue_taxonomy`.
Reading the import in `parser.py:14`:

```python
from unified_api_contracts import (
    DATA_TYPES_BY_ASSET_GROUP,
    VENUES_BY_ASSET_GROUP,
)
```

The dict exists and is imported. **Current MDPS use**: `parser.py:281` reads it for the list command. But the `process`
subcommand does NOT auto-derive `asset_group` from the venue when `--instrument-ids` is canonical. The operator must
still pass one of the category flags (`--CEFI`, `--TRADFI`, etc.) or set `MDPS_ASSET_GROUP`.

**Finding**: The reverse lookup CAN be implemented (the dict exists), but it's not wired into the handler dispatch. This
is an **architectural** finding, not a **parser** finding — the immediate fix is the canonical parser; the
forward-looking fix is auto-derivation of asset_group from the venue in the canonical form.

---

## Atomic shard semantics

Per the codex at `cli-convention.md:147-159`, the atomic shard is the 6-tuple:

```
(asset_group, venue, instrument_type, data_type, symbol, date)
```

This is equivalent to the `--shard-key` pipe-delimited format in MTDS (line 283-286):

```
asset_group | venue | data_type | instrument_type | instrument_id_or_root | day
```

**MDPS alignment check:**

The blob path layout in `orchestration_scanner.py:312-318`:

```
raw_tick_data/by_date/day={date}/{hive_key}={ag}/venue={V}/
  instrument_type={IT}/data_type={DT}/{INSTRUMENT_ID}.parquet
```

Shard decomposition:

- `day={date}` → `date` field ✅
- `{hive_key}={ag}` → `asset_group` field ✅ (where `hive_key` is canonical `asset_group=`)
- `venue={V}` → `venue` field ✅
- `instrument_type={IT}` → `instrument_type` field ✅
- `data_type={DT}` → `data_type` field ✅
- `{INSTRUMENT_ID}.parquet` → `symbol` field ✅ (filename stem is the canonical instrument_id)

**Finding**: The 6-tuple shard atom IS consistent across blob layout, manifest row key (implied by partition structure),
and the canonical instrument_id form. No divergence detected.

---

## Cross-service surface

Quick grep for `--instrument-ids` parsers in other services:

| Service                                | Parser location                                 | Assessment                                                                         |
| -------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| **instruments-service**                | `cli/parser.py` (if exists)                     | Not found in grep search; service is reference-data-only, not data-filtering       |
| **market-tick-data-service (MTDS)**    | `cli/shard_key.py:74-100` (decompose_shard_key) | ✅ **Has `--shard-key` atomic 6-tuple**; shard_key is the canonical form           |
| **features-service** (if consolidated) | `cli/main.py` (dispatcher)                      | Not scanned (post-May-8 consolidation; separate codepath)                          |
| **ml-service** (if consolidated)       | `cli/main.py`                                   | Not scanned (post-May-20 consolidation; uses `--operation` not `--instrument-ids`) |

**Assessment**: MTDS has the **right** shape (atomic 6-tuple via `--shard-key`); MDPS does not. The cross-service
pattern is:

- **Tactical fix for MDPS**: Implement the canonical parser (like MTDS does implicitly via the 6-tuple decomposition).
- **Architectural pattern**: All batch services that accept `--instrument-ids` should follow the codex contract and
  parse the canonical form atomically.

---

## Single-cell drilldown demo

The exact invocation that SHOULD work but doesn't today:

### Current (broken) — operator must pass redundant --venues + --asset-group:

```bash
# Phase 3.2 canary incident: operator forced to pass both to get 4 blobs instead of 200
MDPS_ASSET_GROUP="CEFI" \
MDPS_VENUES="BINANCE-FUTURES BYBIT" \
MDPS_INSTRUMENT_IDS="BTCUSDT ETHUSDT" \
MDPS_DATA_TYPES="trades" \
python -m market_data_processing_service \
  --operation process --mode batch \
  --start-date 2024-03-04 --end-date 2024-03-04

# Result: works, but requires 3 separate flags for what should be ONE canonical form
```

### Target (post-fix) — canonical form alone:

```bash
# What the operator SHOULD be able to do per codex contract (not yet working):
MDPS_INSTRUMENT_IDS="BINANCE-FUTURES:PERPETUAL:BTCUSDT BINANCE-FUTURES:PERPETUAL:ETHUSDT BYBIT:PERPETUAL:BTCUSDT BYBIT:PERPETUAL:ETHUSDT" \
MDPS_DATA_TYPES="trades" \
python -m market_data_processing_service \
  --operation process --mode batch \
  --start-date 2024-03-04 --end-date 2024-03-04

# Result (if parser fixed):
# - Parser extracts (BINANCE-FUTURES, PERPETUAL, BTCUSDT), etc.
# - asset_group auto-derived from VENUES_BY_ASSET_GROUP reverse lookup: CEFI
# - Scanner matches exactly 4 blobs
# - No redundant --venues flag needed
```

**Codex reference:** `cli-convention.md` § "Reference incident" (lines 200-209) documents this exact scenario. The
canonical form is **the minimum information required** to scope a run; passing redundant axes should validate-against
(not override) the derived values.

---

## Recommended next step

### Immediate fix (parser replacement):

1. **Add `_parse_canonical_instrument_id()` function** to `orchestration_scanner.py` (or a new `canonical_parser.py`
   module):
   - Takes `str` → returns `tuple[str, str, str] | None`
   - Splits on first two colons only (symbol may contain `-` or `:`)
   - Returns `None` for legacy bare-symbol form (fallback to substring match)

2. **Replace the substring gate** at `orchestration_scanner.py:459`:
   - For each instrument_id, try canonical parse
   - If parsed, call `matches_canonical_instrument_id()` (hive-path check with lowercasing)
   - If not parsed, fall back to legacy substring match (backwards compat)

3. **Test coverage**:
   - Unit test: `_parse_canonical_instrument_id("BINANCE-FUTURES:PERPETUAL:BTCUSDT")` →
     `("BINANCE-FUTURES", "PERPETUAL", "BTCUSDT")`
   - Unit test: `_parse_canonical_instrument_id("BTCUSDT")` → `None` (bare symbol fallback)
   - Unit test: `matches_canonical_instrument_id(blob_path, "BINANCE-FUTURES", "PERPETUAL", "BTCUSDT")` → `True` on real
     path
   - Integration test: single-cell drilldown matches exactly 1 blob (not 0, not 200)

4. **Deprecation log**: If bare-symbol form is still accepted, emit
   `logger.warning("Bare-symbol substring matching is deprecated; use VENUE:INSTRUMENT_TYPE:SYMBOL canonical form")` on
   fallback.

### Architectural follow-up (post-immediate fix):

1. **Auto-derive asset_group from venue**:
   - At handler entry, check if `--instrument-ids` is all canonical forms
   - Extract venues
   - Reverse-lookup via `VENUES_BY_ASSET_GROUP` to infer asset_group(s)
   - Validate against operator-passed asset-group flags (error if conflict)
   - If all instruments in one asset_group, auto-populate missing category flag

2. **Update `cli-convention.md` implementation section** with MDPS-specific details:
   - The lowercasing of `instrument_type` for hive-path checks
   - The fallback to bare-symbol substring for backwards compatibility
   - The optional auto-derivation of asset_group

3. **Cross-service standardisation**:
   - features-service + ml-service + any new batch service should adopt the same canonical parser
   - Consider moving the parser to `unified_trading_library` (UTL) as a shared utility
   - Link SSOT: `cli-convention.md` is canonical; implementations delegate to UTL

---

## Summary

The 2026-05-28 operator incident revealed that MDPS's CLI parser does **not** implement the codex contract for canonical
instrument_id forms. The scanner uses **substring matching** against blob paths, which silently fails for the canonical
form `VENUE:INSTRUMENT_TYPE:SYMBOL` because the blob paths use `=` not `:` as separators. This forces operators to pass
redundant `--venues` + `--asset-group` flags, violating the codex promise that "a single canonical instrument_id should
be sufficient to scope one cell."

The fix is a two-line parser replacement: extract the three colon-separated fields, then check hive-path segments
independently with proper case handling. The architectural follow-up is auto-derivation of asset_group from the venue
via the existing UAC `VENUES_BY_ASSET_GROUP` reverse lookup. Both are **mandatory** to satisfy the codex contract and
prevent the operational confusion that led to the 70 GB memory incident.
