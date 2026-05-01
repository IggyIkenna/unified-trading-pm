---
title: Instruments — COMBO `legs` field serialized as JSON string instead of list
status: open
severity: low
created: 2026-05-01
last_updated: 2026-05-01
owners:
  - instruments-service / URDI Tardis adapter (root cause)
  - unified-trading-api (read-side mitigation if needed)
related:
  - URDI adapter (Tardis): .extra/unified-reference-data-interface/unified_reference_data_interface/adapters/tardis.py
  - Backend reader: unified-trading-api/unified_trading_api/services/instruments_reader.py
  - UAC schema: unified-api-contracts/unified_api_contracts/internal/reference/instrument.py
  - Drift detector: unified-trading-api/scripts/check_live_universe_schema.py
---

# Instruments — COMBO `legs` field serialized as JSON string instead of list

## TL;DR

For DERIBIT COMBO instruments, the `legs` column in the live-universe response comes back as a **JSON string** rather
than a parsed list of objects. UAC `InstrumentRecord.legs: list[InstrumentLeg] | None` validation fails with:

```
list_type: Input should be a valid list
input: '[{"instrument_key": "DERIBIT:FUTURE:BTC-26JUN26", "side": "BUY", ...}]'  ← still a string
```

Discovered 2026-05-01 by `scripts/check_live_universe_schema.py`. ~451 rows in CEFI affected (Deribit COMBO instruments
— futures/perp pair spreads and similar multi-leg structures).

## Concrete reproduction

```bash
# 1. Run a tier-1-real backend
bash scripts/dev-tiers.sh --tier 1 --real

# 2. Run the drift detector
cd unified-trading-api
.venv/bin/python scripts/check_live_universe_schema.py --asset-groups cefi
# → reports "451/3690 rows failed UAC validation"

# 3. Inspect a single COMBO row
.venv/bin/python -c "
import json, urllib.request
resp = json.loads(urllib.request.urlopen('http://localhost:8030/instruments/live-universe?asset_group=cefi').read())
combo = next(r for r in resp['data'] if r['instrument_type'] == 'COMBO')
print('legs type:', type(combo['legs']).__name__)
print('legs value (first 80 chars):', repr(combo['legs'])[:80])
"
# → legs type: str
# → legs value: '[{"instrument_key": "DERIBIT:FUTURE:BTC-26JUN26", "side": "BUY", ...'
```

## Where it goes wrong

`unified-trading-api/unified_trading_api/services/instruments_reader.py:_normalise_row` converts every pandas cell to a
JSON-serialisable scalar. The general `pd.Series.apply` walks each value:

- `Decimal` → `float` ✓
- `pd.Timestamp` → ISO string ✓
- numpy scalars → `.item()` ✓
- Lists / dicts / nested objects → returned as-is

But the **parquet column itself** stores `legs` as a string when written upstream — meaning the cell is already a string
by the time it reaches the API. The bug isn't in `_normalise_row`; it's in the writer (URDI Tardis adapter or the
`InstrumentRecord` parquet serialization step).

UAC's `InstrumentRecord` says:

```python
legs: list[InstrumentLeg] | None = Field(default=None, ...)
```

But the doc comment on `InstrumentRecord` mentions:

> Type flattening on write: Decimal → str, enum → str, datetime → datetime64[ns]

Lists/objects aren't covered. The current writer probably JSON-encodes the list to fit it into a string parquet column —
which works for storage but breaks when consumers expect a list back.

## Mitigations available

### Option A (read-side, this repo) — JSON-decode in `_normalise_row`

In `instruments_reader._normalise_row`, detect `legs`-shaped string values and `json.loads` them. ~5 lines, no upstream
coordination needed.

```python
# In _normalise_row, after the existing scalar conversions:
if key_str == "legs" and isinstance(value, str):
    try:
        result[key_str] = json.loads(value)
    except json.JSONDecodeError:
        result[key_str] = None
```

Same shape applies to any other "object packed as JSON string" columns that surface later. We don't have any others
today.

### Option B (write-side, upstream) — Use parquet struct type

Have instruments-service write `legs` as a parquet struct/list column rather than a string. Cross-repo change, ripples
through readers.

### Option C — Just accept it as a string in UAC

Change `InstrumentRecord.legs` type to `str | list[InstrumentLeg] | None` with a validator that decodes strings on read.
Loses some type safety.

## Recommendation

**Option A** for the immediate fix — scoped to this repo, ~5 lines, fixes the validation drift on the next pytest run.
Keep this finding open until the upstream writer is fixed (Option B), at which point Option A becomes unnecessary.

## Why this is low severity

- The watchlist UI doesn't render COMBO instruments today (system lists don't include them, and the picker modal works
  fine — it just shows the raw symbol).
- No current consumer reads `legs` and acts on it.
- The drift detector is the only thing that fires on this — well-isolated.

Filed to keep us honest: **the schema-parity test is supposed to catch exactly this class of bug**, and it did. The fact
that we shipped to production with this latent makes the test work valuable retroactively.

## Why this is NOT being fixed in this commit

Out of scope for the watchlist plan. The plan's Unit B/C/D/E/F are about **adding test coverage** to catch drift. This
finding is the first thing the new tests caught. Fixing the underlying drift is a separate ticket that needs a
writer-side decision (Option A vs B vs C above).

The drift is also already isolated by Option A's ability to land defensively. No production user is impacted today.
