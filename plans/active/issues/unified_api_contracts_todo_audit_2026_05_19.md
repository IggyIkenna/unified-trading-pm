---
title: unified-api-contracts TODO audit — 2 real issues requiring scope
created: 2026-05-19
author: slot-1
source:
  - unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:247
  - unified-api-contracts/unified_api_contracts/canonical/coverage_starts.py:57,78,79,94,95
locked_by: live-defi-rollout
---

## What I found

Ran TODO/FIXME/XXX/HACK sweep in unified-api-contracts Python source.

**False positives (5)** — not actionable:
- `external/api_football/team_mappings.py:739,2011` — "HACKEN"/"BK Hacken" are soccer team name string literals
- `external/binance/ws_schemas.py:47` — "autoclose-XXX" is Binance protocol notation in a field description comment
- `external/odds_api/team_names.py:637` — "BK Hacken" team name string literal
- `registry/capability_declarations/_defi_chain_data.py:681` — "So1anaXXXXXXXXXX" is a placeholder program ID

**Real issues (2)**:

### Issue 1 — VX front-month symbols not generated dynamically (`tradfi_instrument_universe.py:247`)

```python
# CBOE VX futures: XCBF.PITCH only supports stype_in=raw_symbol with explicit
# contract codes (e.g. "VXH6" for March 2026). Parent/continuous symbology not
# supported.  TODO: generate front-month VX symbols dynamically from target date.
_CBOE_INSTRUMENTS: list[DatabentoInstrumentDef] = []
```

`_CBOE_INSTRUMENTS` is an empty list. VX futures are not currently included in the TradFi instrument universe. Front-month symbols must be generated using contract-month codes (e.g. "VXH6" = March 2026, "VXJ6" = April 2026). Requires: month-code table, front-month date calculation logic, and integration with Databento symbology.

### Issue 2 — 5 coverage start dates marked `# TODO verify`  (`coverage_starts.py`)

```python
"TARDIS":      date(2017, 6, 1),  # TODO verify  (CEFI + TRADFI)
"ETHERFI":     date(2023, 11, 1),  # TODO verify
"UNISWAP_V4":  date(2025, 1, 31),  # TODO verify
"CME":         date(2010, 1, 1),   # TODO verify
```

These are best-effort seed values per the module docstring. Inaccurate coverage starts → false `missing` or false `present` manifest rows. Verification path: `read_availability_index({bucket}).date.min()` on prod manifest.

## Why it matters

Issue 1: VX futures are in the TradFi backfill target but the instrument list is empty — no symbols → no data fetch → silent gap.

Issue 2: Incorrect coverage starts cause honest-coverage false positives/negatives. `TARDIS` appears in both CEFI and TRADFI dicts with the same unverified date. `CME` date(2010,1,1) is a round-number placeholder.

## Recommended decision

- **Issue 1**: Assign to TradFi epic slot — implement VX front-month symbol generator in `_CBOE_INSTRUMENTS`. Requires ~0.5 AI-day. SSOT: `epics/tradfi_master_2026_05_07.md`.
- **Issue 2**: Assign to data-quality slot — probe prod manifest for each unverified venue, replace placeholder dates with confirmed values. ~0.3 AI-day. Can be done in a single PR.
