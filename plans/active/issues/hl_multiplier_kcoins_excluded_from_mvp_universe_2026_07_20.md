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
- ⬜ **STEP 3 — rebuild the IS catalogue so the stored `mvp` column flips True for the 6 k-coins.** REQUIRED because
  `CeFiCatalogReader._row_in_mvp_capture_universe` PREFERS the catalogue's pre-computed `mvp` column over the live
  `is_in_mvp_capture_universe` gate — so `list_instruments` keeps excluding the k-coins until a rebuild recomputes `mvp`
  from the new UAC. Depends on UAC@7eb1cecb being deployed to the IS build service (CI/CD: LDR→main promote → IS Cloud
  Run redeploy). Then trigger the cefi catalogue regen (Cloud Scheduler, region asia-northeast1:
  `uts-prod-instruments-cefi-t1-schedule` @06:00Z daily, or `lifecycle-catalogue-full-cefi-weekly` Sat @03:00Z, or
  un-pause + run `instrument-catalogue-regen-nightly`). VERIFY: raw `prod/catalog.parquet` shows `mvp=True` for
  `HYPERLIQUID:PERPETUAL:KPEPE-USD@LIN` (+ the other 5).
- ⬜ **STEP 4 — rebuild + upload the UAC code tarball.** `git archive` UAC@7eb1cecb →
  `unified-api-contracts-code.tar.gz` → `gs://deployment-scripts-central-element-323112/code/` (same pattern as the MTDS
  tarball rebuild this session). VMs install UAC from THIS tarball at boot (NOT from LDR), so a freshly-launched
  backfill VM must have the new universe or its manifest expected-universe will mis-classify the k-coin cells.
- ⬜ **STEP 5 — supplementary k-coin backfill.**
  `bash deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` with
  `VENUES=HYPERLIQUID DATA_TYPES=trades FORCE=true SHARD_DAYS=21 OVERRIDE_START_DATE=2025-05-25` and either
  `SYMBOLS="KPEPE;KBONK;KSHIB;KFLOKI;KLUNC;KNEIRO"` (surgical) or `SYMBOLS=ALL` (now that they're mvp=True). The shipped
  k-prefix fetch fix (mtds@50b6406e) + parse-once (mtds@a6e974b6) capture them.
- ⬜ **STEP 6 — verify + close.** Confirm fresh `HYPERLIQUID:PERPETUAL:KPEPE-USD@LIN.parquet` (+ other 5) land with real
  rows + today's `time_created`, and the manifest marks the k-coin cells captured/expected. Then flip this issue
  `status: resolved` + `resolved_by:`.

Sequencing note: STEP 5 needs BOTH STEP 3 (catalogue mvp=True → universe path + downstream features/strategy see the
coins) AND STEP 4 (new UAC on the VM → correct manifest expected-universe). Explicit `SYMBOLS=` bypasses the catalogue
universe gate, so if STEP 3 lags, an explicit-symbols run with the STEP-4 tarball still lands the DATA + correct
manifest coverage; downstream wiring then follows on the STEP-3 catalogue rebuild.

Live state (2026-07-20): STEP 1 done (UAC@7eb1cecb). The finer-sharded 172-universe HL trades backfill
(deployment-service@00886fe) is running/finishing over 2025-05-25→2026-07-20 and does NOT include the k-coins — they
land in the STEP 5 supplementary pass.
