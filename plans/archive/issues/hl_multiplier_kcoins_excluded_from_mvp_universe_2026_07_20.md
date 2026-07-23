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
status: resolved
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [mvp-universe, hyperliquid, catalogue, capture-universe, data-completeness, operator-decision, cefi-onchain-perp]
related:
  [
    /plans/active/issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
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
resolved_by: >-
  uac@7eb1cecb (universe add) + IS catalogue rebuild (lifecycle-catalogue-full-cefi-fmnt4, 2026-07-20T19:57:38Z) + mtds
  backfill RUN_TS 20260720-205915 (21 VMs). All 6 k-coins verified captured with real canonical-cased data across
  2025-05-25→2026-07-20.
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

## Decision (made 2026-07-20): ADD the 6 k-coins to capture

Operator approved adding all 6 (kPEPE/kBONK/kSHIB/kFLOKI/kLUNC/kNEIRO). This is now an execution checklist, not an open
question — resume from the first unchecked step below.

## Resolution plan + live state — RESUME HERE if context is lost (update boxes as steps land)

- ✅ **STEP 1 — UAC universe (the SSOT gate).** Added the 6 canonical bases (KPEPE/KBONK/KSHIB/KFLOKI/KLUNC/KNEIRO) to
  `CEFI_BASE_ASSET_UNIVERSE` (`unified_api_contracts/registry/cefi_instrument_universe.py`) →
  `is_in_mvp_capture_universe(HYPERLIQUID, KPEPE)=True` (was False). SHIPPED **UAC@7eb1cecb** (2026-07-20), universe
  540→546, full gate green.
- ✅ **STEP 2 — 172-universe backfill finished** (2026-07-20 ~10:03Z). All 21 finer shards (deployment-service@00886fe,
  RUN_TS 20260720-094957) over 2025-05-25→2026-07-20 self-shut-down. VERIFIED: sampled days across the whole range hold
  ~143-169 per-instrument trades parquets, essentially all `time_created` today (FORCE rewrite), count rising over time
  as HL listed more perps (≤172 mvp=True). k-coins NOT included (expected — they land in STEP 5). Safe to proceed to
  STEP 3.
- ✅ **STEP 3 — IS catalogue rebuilt, `mvp` flipped True.** Correction to the original plan: the mvp column is computed
  from whatever UAC the `lifecycle-catalogue-full-cefi` Cloud Run JOB's deployed image has baked in at build time
  (`uv.sources` local-path dependency), not a separately-deployed "IS build service" — and that image
  (`instruments-service:latest`) was independently verified (via `docker run --entrypoint python`) to ALREADY carry
  UAC@7eb1cecb + UAC@34580d92 (universe size 556, `KPEPE`/`1000PEPE` both present) before any rebuild was needed.
  Triggered `gcloud run jobs execute lifecycle-catalogue-full-cefi` (execution `lifecycle-catalogue-full-cefi-fmnt4`,
  rolled up 53,188 by_date parquets). VERIFIED: `prod/catalog.parquet` refreshed 2026-07-20T19:57:38Z, all 16
  k-coins/1000-coins (6 HL + 10 ASTER) confirmed `mvp=True`.
- ✅ **STEP 4 — N/A, no separate UAC tarball needed.** The catalogue's STORED `mvp` column (not a live UAC call on the
  backfill VM) is what `CeFiCatalogReader._row_in_mvp_capture_universe` consults — confirmed by reading the actual code
  path, not assumed. So a fresh catalogue alone unblocks STEP 5 regardless of which UAC tarball a VM installs.
- ✅ **STEP 5 — supplementary k-coin backfill SHIPPED + VERIFIED.** Ran
  `VENUES=HYPERLIQUID DATA_TYPES=trades FORCE=true SYMBOLS="KPEPE;KBONK;KSHIB;KFLOKI;KLUNC;KNEIRO" YEARS="2025 2026" SHARD_DAYS=21 OVERRIDE_START_DATE=2025-05-25`
  (RUN_TS 20260720-205915, 21 VMs, all self-shut-down clean).
- ✅ **STEP 6 — verified + closed.** All 6 k-coins confirmed present across the FULL date range (spot-checked 2025-05-25
  / 08-01 / 11-01, 2026-02-01 / 05-01 / 07-19 — 6/6 every day). Sampled `KPEPE-USD@LIN.parquet` (day=2026-05-01): 18,970
  real rows, canonical `coin=KPEPE` (uppercase, proving the k-prefix `.upper()` fix from mtds@50b6406e works
  end-to-end), real prices. `status: resolved` below.

Live state (2026-07-20): ALL 6 STEPS COMPLETE. HL k-coins are captured, canonical, and verified with real data across
the full 2025-05-25→2026-07-20 range.
