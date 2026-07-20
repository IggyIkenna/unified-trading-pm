---
doc_type: issue
title: >-
  HL multiplier k-coins (kPEPE/kBONK/kSHIB/kFLOKI/kLUNC/kNEIRO) are in the catalogue but tagged mvp=False → excluded
  from the MTDS capture universe → never backfilled; the k-prefix fetch fix (mtds@50b6406e) is inert for them
summary: >-
  Hyperliquid lists 232 perps including 7 lowercase-k multiplier coins (kPEPE=1000·PEPE, kBONK, kSHIB, kFLOKI, kLUNC,
  kNEIRO, kDOGS). The IS cefi catalogue DOES carry the 6 active ones as canonical uppercase (KPEPE-USD@LIN …,
  available_from 2023), but all 6 are tagged mvp=False / force_include=False, and UAC
  is_in_mvp_capture_universe(HYPERLIQUID, KPEPE)=False. MTDS's catalogue-driven backfill resolves its universe via
  CeFiCatalogReader.list_instruments(include_non_mvp=False), which gates on mvp — so the 172 mvp=True HL perps are
  captured and the 10 mvp=False rows (incl. the 6 k-coins) are skipped BY DESIGN. Net effect: the 2026-07-20 HL trades
  full-universe backfill captures 172 instruments, NOT the k-coins. This means the earlier k-prefix fetch fix
  (mtds@50b6406e, lowercase-k fill-coin .upper() normalization + a regression test) is CORRECT code but INERT for the
  backfill — those coins are never in the requested universe, so the normalization never fires end-to-end. kPEPE is one
  of HL's highest-volume perps and the ONLY PEPE exposure on HL (no plain PEPE perp exists), so this is a real
  data-completeness gap, not a niche edge case — but expanding the MVP universe has broad downstream blast radius
  (capture → features → strategy), so it is an OPERATOR SCOPE DECISION.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [mvp-universe, hyperliquid, catalogue, capture-universe, data-completeness, operator-decision, cefi-onchain-perp]
related: [cefi_backfill_per_day_catalogue_reload_2026_07_20.md, cefi_hl_aster_batch_data_gaps_2026_06_22.md]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: data-pipeline
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source:
  ["discovered 2026-07-20 verifying the HL trades full-universe backfill actually captures the k-prefix instruments"]
---

# HL multiplier k-coins excluded from the MVP capture universe

## Evidence (raw prod/catalog.parquet, built 2026-07-20T01:02Z — fresh)

- 182 HL rows total: **172 `mvp=True`**, **10 `mvp=False`**.
- The 6 active multiplier k-coins are all `mvp=False`, `force_include=False`, `available_to=None` (active):
  `KBONK / KFLOKI / KLUNC / KNEIRO / KPEPE / KSHIB -USD@LIN` (available_from 2023). (kDOGS is `isDelisted=True` in HL
  `/info` meta, correctly dropped.)
- `is_in_mvp_capture_universe("HYPERLIQUID", "KPEPE", PERPETUAL, has_perp_for_base=True)` = **False** (`BTC` = True).
- HL public `/info` meta: 232 perps, k-coins present + active.
- `CeFiCatalogReader.list_instruments(..., include_non_mvp=False)` (the default the MTDS backfill uses via
  `catalogue_symbols_for_venue`) gates on `mvp` → returns 172 HL symbols, excluding the k-coins. Confirmed on GCS: the
  2026-07-20 backfill wrote 143 instrument parquets for day=2025-05-29, none of them a k-coin.

## Why it matters

kPEPE is the SOLE PEPE-family exposure on Hyperliquid (HL lists no plain `PEPE` perp) and one of its highest-volume
perps; likewise kBONK/kSHIB/kFLOKI/kNEIRO/kLUNC are the only representation of those assets on HL. Excluding them from
capture means no market data for a chunk of HL's most-liquid meme book. The k-prefix fetch fix (mtds@50b6406e) was
shipped to recover them but is inert while they stay non-MVP.

## Decision needed (operator)

Are the HL multiplier k-coins in scope for capture?

- **If YES** (recommended given "all instruments" intent): add them to the MVP capture universe. Fix path:
  1. UAC `is_in_mvp_capture_universe` — include the HL k-coin bases (or drop the rule that excludes them). This is the
     authoritative gate.
  2. IS catalogue rollup — tag these rows `mvp=True` (or set `force_include=True`), so `list_instruments` surfaces them.
  3. Re-run the HL trades backfill (the shipped k-prefix fix + parse-once perf then capture them correctly; verify a
     fresh `KPEPE-USD@LIN.parquet` lands with real rows).
- **If NO**: the current 172-instrument backfill is complete + correct; close the k-prefix fetch work as inert-by-scope
  and record that HL k-coins are deliberately out of the capture universe.

Interim state (2026-07-20): the finer-sharded HL trades backfill (21 VMs, deployment-service@00886fe) is capturing the
full **172 mvp=True** HL universe over 2025-05-25→2026-07-20. It does NOT include the k-coins pending this decision.
