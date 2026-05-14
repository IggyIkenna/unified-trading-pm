---
title: ICE US Softs (CT/CC/KC/SB/OJ/DX) dataset disambiguation — IFUS.IMPACT canonical
created: 2026-05-14
author: harsh-slot-7
source:
  - plans/active/cross_asset_group_catalogue_audit_2026_05_10.md Phase 5B (TRADFI_ROOTS deferred note)
  - unified_api_contracts/registry/tradfi_symbology.py:103-115
  - unified_api_contracts/registry/tradfi_instrument_universe.py:110
  - unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py
locked_by: live-defi-rollout
locked_since: 2026-05-14
severity: P2
suggested_owner: ikenna (UAC write authority for cross-cutting refactor)
---

# ICE US Softs (CT/CC/KC/SB/OJ/DX) — dataset disambiguation

## What I found

Phase 5B (TRADFI_ROOTS) was shipped at UAC@`24dd517` with ICE US softs deferred:
> "ICE US softs (CT/CC/KC/SB/OJ/DX/T) deferred — dataset ambiguity between 2 source files (Phase 6)"

Disambiguation analysis (2026-05-14 slot 7 Day-3):

### Source file 1 — `tradfi_symbology.py:103-115` (CORRECT)

```python
# ICE Futures US (IFUS.IMPACT)
"CT": ("CT.FUT", "IFUS.IMPACT"),  # Cotton No. 2
"COTTON": ("CT.FUT", "IFUS.IMPACT"),
"CC": ("CC.FUT", "IFUS.IMPACT"),  # Cocoa
"COCOA": ("CC.FUT", "IFUS.IMPACT"),
"KC": ("KC.FUT", "IFUS.IMPACT"),  # Coffee
"COFFEE": ("KC.FUT", "IFUS.IMPACT"),
"SB": ("SB.FUT", "IFUS.IMPACT"),  # Sugar No. 11
"SUGAR": ("SB.FUT", "IFUS.IMPACT"),
"OJ": ("OJ.FUT", "IFUS.IMPACT"),  # OJ Frozen Concentrate
"ORANGEJUICE": ("OJ.FUT", "IFUS.IMPACT"),
"DX": ("DX.FUT", "IFUS.IMPACT"),  # US Dollar Index
"DOLLARINDEX": ("DX.FUT", "IFUS.IMPACT"),
```

Also in `TRADFI_DATA_BINDINGS` (lines 408-413):
```python
"CT.FUT": [_db("IFUS.IMPACT", "parent", "CT")],
"CC.FUT": [_db("IFUS.IMPACT", "parent", "CC")],
"KC.FUT": [_db("IFUS.IMPACT", "parent", "KC")],
"SB.FUT": [_db("IFUS.IMPACT", "parent", "SB")],
"OJ.FUT": [_db("IFUS.IMPACT", "parent", "OJ")],
"DX.FUT": [_db("IFUS.IMPACT", "parent", "DX")],
```

### Source file 2 — `tradfi_instrument_universe.py:110` (WRONG)

```python
DatabentoInstrumentDef("CT.FUT", "CME", "FUTURE", "GLBX.MDP3", "parent", "COTTON", "commodity", "CT"),
```

This is **incorrect**: CT (Cotton No. 2 Futures) is an ICE Futures US product, not a CME product. CME
Group's GLBX.MDP3 dataset covers CBOT/CME/NYMEX/COMEX — none of which list cotton futures. Cotton No. 2
has traded exclusively on ICE Futures US since ICE acquired NYBOT in 2007.

Additionally: CC (Cocoa), KC (Coffee), SB (Sugar No. 11), OJ (Orange Juice), DX (Dollar Index) are
**entirely missing** from `tradfi_instrument_universe.py`. They are ICE Futures US products and should
appear with IFUS.IMPACT.

### Source file 3 — `tradfi_roots.py` (SSOT — missing entries)

`DATASET_ICE_US = "IFUS.IMPACT"` is defined at line 75. ICE Europe entries (BRN/G/T) follow the pattern
`RootMetadata(..., "ICE", DATASET_ICE_EUROPE, ...)`. ICE US softs entries are absent (deferred from
Phase 5B).

## Why it matters

The ambiguity blocks:
1. **TRADFI_ROOTS completion** — Phase 5B explicitly deferred CT/CC/KC/SB/OJ/DX pending disambiguation.
   Until these are added to TRADFI_ROOTS, `get_canonical_inventory("tradfi")` under-reports the TradFi
   instrument universe.
2. **`tradfi_instrument_universe.py` bug** — CT.FUT entry points to CME/GLBX.MDP3. Any consumer that
   reads this file for data source routing will request CT data from the wrong Databento dataset.
3. **Missing CC/KC/SB/OJ/DX** in `tradfi_instrument_universe.py` — these 5 ICE US softs are silently
   absent from the instrument universe used for data pipeline scheduling.

## Disambiguation conclusion

**IFUS.IMPACT is the canonical dataset for all 6 ICE US softs.** No ambiguity remains.

Evidence:
- `tradfi_symbology.py` explicitly labels them "ICE Futures US (IFUS.IMPACT)" — the most specific
  labeling in the codebase.
- `TRADFI_DATA_BINDINGS` in `tradfi_symbology.py` maps all 6 to IFUS.IMPACT parent symbology.
- Databento's published dataset coverage confirms: IFUS.IMPACT = ICE Futures US; GLBX.MDP3 = CME Group.
- `tradfi_instrument_universe.py:110` CT entry with CME/GLBX.MDP3 is a data-entry error.

## Recommended decision

No design call needed — fix is mechanical. Suggested owner: ikenna (UAC write authority).

**Fix 1 — Add CT/CC/KC/SB/OJ/DX to `tradfi_roots.py` TRADFI_ROOTS dict** (after the ICE Europe section):

```python
# ── ICE Futures US (Softs) ─────────────────────────────────────────────────
"CT": RootMetadata("CT", CATEGORY_COMMODITY_FUTURES, "COTTON", "ICE", DATASET_ICE_US, "commodity"),
"CC": RootMetadata("CC", CATEGORY_COMMODITY_FUTURES, "COCOA", "ICE", DATASET_ICE_US, "commodity"),
"KC": RootMetadata("KC", CATEGORY_COMMODITY_FUTURES, "COFFEE", "ICE", DATASET_ICE_US, "commodity"),
"SB": RootMetadata("SB", CATEGORY_COMMODITY_FUTURES, "SUGAR", "ICE", DATASET_ICE_US, "commodity"),
"OJ": RootMetadata("OJ", CATEGORY_COMMODITY_FUTURES, "OJ", "ICE", DATASET_ICE_US, "commodity"),
"DX": RootMetadata("DX", CATEGORY_COMMODITY_FUTURES, "DOLLARINDEX", "ICE", DATASET_ICE_US, "commodity"),
```

Note: `CATEGORY_COMMODITY_FUTURES` may need to be added (check if that constant exists in tradfi_roots.py;
if not, use the closest existing category or add `CATEGORY_SOFTS_FUTURES = "softs_futures"`).

**Fix 2 — Correct CT entry + add missing CC/KC/SB/OJ/DX in `tradfi_instrument_universe.py`**:

```python
# Replace line 110:
# DatabentoInstrumentDef("CT.FUT", "CME", "FUTURE", "GLBX.MDP3", "parent", "COTTON", "commodity", "CT"),
# With:
DatabentoInstrumentDef("CT.FUT", "ICE", "FUTURE", "IFUS.IMPACT", "parent", "COTTON", "commodity", "CT"),
# And add:
DatabentoInstrumentDef("CC.FUT", "ICE", "FUTURE", "IFUS.IMPACT", "parent", "COCOA", "commodity", "CC"),
DatabentoInstrumentDef("KC.FUT", "ICE", "FUTURE", "IFUS.IMPACT", "parent", "COFFEE", "commodity", "KC"),
DatabentoInstrumentDef("SB.FUT", "ICE", "FUTURE", "IFUS.IMPACT", "parent", "SUGAR", "commodity", "SB"),
DatabentoInstrumentDef("OJ.FUT", "ICE", "FUTURE", "IFUS.IMPACT", "parent", "OJ", "commodity", "OJ"),
DatabentoInstrumentDef("DX.FUT", "ICE", "FUTURE", "IFUS.IMPACT", "parent", "DOLLARINDEX", "fx", "DX"),
```

Note: DX (Dollar Index) is classified as "fx" not "commodity" since it's a currency futures contract.
After the fix, `ROOT_SYMBOL_MAP` additions are also needed: "CC" → "COCOA", "KC" → "COFFEE", "SB" →
"SUGAR", "OJ" → "OJ", "DX" → "DOLLARINDEX".

**Fix 3 — Run UAC QG after both fixes** to confirm no ruff/basedpyright violations introduced.

## Cross-plan pointers

- Owner plan: `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 5B (TRADFI_ROOTS deferred note)
- Also: `tradfi_master_2026_05_07.md` (ICE coverage dict gaps: TF-3 `ICE` missing from TRADFI_TICKER_COVERAGE_START)
- UAC file: `unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py`
- UAC file: `unified_api_contracts/registry/tradfi_instrument_universe.py:110`

## Resolution

✅ **RESOLVED** (2026-05-14 — shipped by harsh-main during OOM recovery):

- `unified-api-contracts@2fb27f8` (feat(tradfi): add ICE US softs (CT/CC/KC/SB/OJ/DX) to TRADFI_ROOTS + fix CT dataset routing):
  - Fix 1 — `tradfi_roots.py`: added CT / CC / KC / SB / OJ / DX under ICE Futures US (IFUS.IMPACT)
    after the ICE Europe entries; DX classified as `fx` (currency basket).
  - Fix 2 — `tradfi_instrument_universe.py`: removed CT.FUT from `_CME_COMMODITY_FUTURES` (was
    incorrectly mapped to CME/GLBX.MDP3; CT trades on ICE Futures US only). Added `_ICE_US_FUTURES`
    list (CT / CC / KC / SB / OJ / DX, IFUS.IMPACT) wired into `TRADFI_DATABENTO_INSTRUMENTS`. Added
    CC / KC / SB / OJ / DX to `EXCHANGE_CODE_TO_NAME`.
  - Fix 3 — UAC QG green.
