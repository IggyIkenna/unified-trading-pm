---
title: "CeFi legacy gap-fill + manifest canonicalisation (single-walk) — L3 owner for cefi"
created: 2026-06-01
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-cefi
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (L3 ordering — cefi had NO owner)
  - _index comparison 2026-06-01 (cefi canonical ~complete: 838 legacy-only captured cells out of 91,602)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# CeFi legacy gap-fill + manifest canonicalisation (L3 owner for cefi)

> **🟢 UNBLOCKED (2026-06-07) — slot-7 Era-B + bundle-grain rollup LANDED** (uac@ae70338d Era-B instrument_types +
> 687d1443/74df991d per-underlying rollup, flip 6a1e0154c; slots 3/6 notified). Your migrators + instruments-store v9
> dry-run are already GREEN — last step: RE-RUN your enumerate validation against the landed rollup (the false
> per-contract OPTION/COMBO candidates should be GONE) + do the Era-B `data_type=options_chain`→(instrument_type +
> `data_type=trades`) v8→v9 manifest relabel in your walk → then flip your apply-ready verdict.

> **⛔ COORDINATED + APPLY-GATED (2026-06-07)** — cross-AG sequencing is owned by
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`. This AG's `--apply` (manifest +
> data/schema) is GATED on the coordinator's **G0** (pipeline*mode source-aware
> `{mode}*{source}[_{transport}]`model + doc coherence — this plan PREDATES the 2026-06-05 standard, reconcile per M-COORD-1/2) + **G1** (IS catalogue could-exist SSOT: IS backfill complete + accurate UAC) + **G2** (scripts + 7+2-point audit + dry-run) + **G3** (deployment UNION view) all GREEN. The migrator/manifest-rebuild/enumerator MUST stamp source-aware pipeline_mode (NOT coarse`batch`/blank)
> BEFORE apply. Readiness audit adds ⑧ (IS-catalogue) + ⑨ (pipeline_mode source-aware).

> **🔴 P0 GATE (operator 2026-06-05) — the v9 `--apply` here is BLOCKED until
> `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` Phase 0 (code) is GREEN.** Single-walk
> discipline: this corpus walk must carry the new manifest columns — `live_<source>`/`replay_<source>` form, populated
> `source`, `cadence`, `transport` — so running `--apply` before that code lands bakes in the old model + forces a
> banned second whole-corpus walk. **Dry-runs are NOT gated; only the irreversible `--apply`.**

> **🔎 CROSS-AG FINDING from defi (2026-06-01) — CHECK THE SAME HERE**: defi's CF data-state audit found the legacy
> `_index` **100% NOT v9** (v4/5/6/8 spread), with **no `source`/`asset_group`/`pipeline_mode` COLUMNS** and glued
> venues (`AERODROMEV3`/`TRADER_JOEV2`) — a FULL re-canonicalisation, not the headline cell-count. **CF-2 gotcha**: the
> migrate tool emitted `asset_group=` to the object PATH but did NOT stamp it as a parquet COLUMN → the rebuilt `_index`
> lacked the column. Fix = stamp `asset_group` (+ `schema_version`/`source`/`pipeline_mode`) as COLUMNS, never rely on
> the consolidator deriving them from the path. **Action**: run a CF data-state audit on cefi's `_index` as pre-flight +
> verify (reusable: `market-tick-data-service/market_tick_data_service/scripts/audit_canonical_form.py` or
> `plans/audit/results/cf_manifest_audit_2026_06_01.py`) — trust the real data-state, never the v9 constant. If the same
> debt shows → fix fully in-walk (scope is a prior, not a ceiling). SSOT:
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`.

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, cefi lane). **Single-walk discipline (HARD
> RULE)**: ONE bundled walk on the cefi `_index` — bundle the **full v8→v9 re-version + `source` column + `asset_group`
> column + `pipeline_mode=` partition** (see the data-state finding below) **AND** the 838-cell gap-fill; do NOT open a
> second walk. `pipeline_mode_partition_migration` + `data_source_provenance` (cefi) ride THIS walk.

> **🔴 DATA-STATE FINDING (2026-06-01, slot-3 audit) — cefi is a FULL re-canonicalisation, NOT an 838-cell gap-fill.**
> Reading the ACTUAL canonical cefi `_index` (not the constant — the manifest-v8 lesson): **100% of rows are v8 (CF-1
> RED, not v9)**, there is **no `source` column (CF-4 RED)**, **no `category`/`asset_group` column (CF-2 RED)**, and
> **`pipeline_mode` is blank (CF-3 RED)**. So the headline "~complete / 838-cell gap" was a coarse PRIOR; the data-state
> is the truth and the scope is the whole corpus. Per the **"Audit scope is a prior, not a ceiling —
> fix-fully-autonomously"** HARD RULE (`canonical_form_cross_service_audit_checklist.md`), this is **fixed FULLY and
> AUTONOMOUSLY in the one bundled walk** — NOT descoped to 838 cells, NOT deferred, NOT blocked-on-operator. Capture the
> remaining schema signal (`error_reason` for CF-5, object paths for CF-2/3/9) into a **reusable audit tool**, then the
> walk lands every CF-1…CF-12 fix.

## ✅ G2 VERIFY PASS — re-run on the WAVE-1 shape-aware code (slot-3, 2026-06-07)

> **Scope**: the master coordinator's WAVE-2/G2 verify — prove the cefi migration CODE is dry-run-green on the WAVE-1
> code (source-aware migrator/rebuild + shape-aware `enumerate_expected_universe` `is@6ea46565` + AG-parametric
> instruments-store v9 migrator `is@febb899e` + UAC validity matrix `uac@97c26dbe`), all confirmed present on LDR. All
> dry-runs READ-ONLY on real prod GCS (`-prd-central-element-323112`), `--apply` stays G4-gated. Where I sampled vs
> walked is stated per step.

**① migrator dry-run (MTDS `migrate_cefi_flat_to_v9_canonical.py`) — GREEN.** Window `2024-06-01` (300 day-tree objs) +
projected the un-migrated `2024-06-01` objects directly (409 non-canon of 1,114): canonical dst inserts
`pipeline_mode=batch_tardis/` **LEFT of** `asset_group=cefi/` (SOURCE-AWARE via `PipelineMode.BATCH_TARDIS` /
`BATCH_HYPERLIQUID`, **not** coarse `batch`) — CF-3/CF-13 ✓. Per-symbol filenames preserved (incl Kraken 2-segment
`BASE/QUOTE.parquet`); **bundle grain preserved** for `instrument_type=options_chain`/`futures_chain` (the
`underlying=/quote=/margin=` segments are kept verbatim; pipeline_mode inserted after `day=`) — the BUNDLE-grain combo
case verified ✓. Already-canonical days (`2026-05-24`) are idempotent no-ops (dst==src).
`TOTAL planned/moved=0 (DRY-RUN)`.

**② manifest-rebuild dry-run (`rebuild_cefi_manifest.py --dry-run`) — GREEN (exit 0), source-aware.** Window
`2024-06-01..2024-06-07`. Re-emits via the UTL `record_captured/failed/empty` writer (the live-writer path → batch=live,
CF-12 ✓), passing source-aware `derive_pipeline_mode_for_row(venue,"cefi",dt)` (CF-13 ✓) + `asset_group=cefi`. The
writer stamps the v9 COLUMNS (`schema_version=9`/`asset_group`/`source`/`transport`/`available_at`) — NOT path-derived
(the defi CF-2-gotcha is avoided). `phantom_to_failed=12`/week (matches the post-`mtds@60debbfe` residual). **BUT the 12
are NOT "honest absence" — see Finding F1.** `unparseable=0`.

**② instruments-store v9 dry-run (`migrate_instruments_store_v9.py --asset-group cefi`) — GREEN (exit 0).** `_index`
transform projection on the real `-prd` `_index`: **30,803 rows v8→100% v9** (CF-1 ✓); `asset_group=cefi` 30,803/30,803
(CF-2 ✓); `data_type=instruments` (CF-7 ✓); `pipeline_mode=batch_instruments_service` (reference provenance — NOT the
market `tardis`; CF-3 ✓); `source=instruments_service` (CF-4 ✓); `transport=rest` (CF-TRANSPORT ✓); `available_at`
filled 30,803/30,803 (CF-8 ✓); **honest capture_status**: `null_capture_to_captured=12,372` (all `instrument_count>0`),
0 dishonest-empty (CF-10 ✓). Object-path walk: 28,174 objs →
`pipeline_mode=batch_instruments_service/asset_group=cefi/venue=…/instruments.parquet`. →
**cf_manifest_audit(instruments-store-cefi) projects CF-GREEN.** `--apply` G4-gated.

**③ catalogue + enumerate dry-run on the SHAPE-AWARE producer — GREEN mechanism + PLAUSIBLE candidate set, with 2
material could-exist findings (F1/F2).**
`enumerate_expected_universe v2 --catalog-path gs://instruments-store-cefi-prd/prod/catalog.parquet --start-date 2024-06-01 --end-date 2024-06-02`
(catalog 213,990 instruments; manifest present-set 2,639,403) → **3,446 candidates** (3,376 `expected_unattempted` + 70
`EXPECTED_INSTRUMENT_DELISTED`). **Plausibility ✓**: no single-venue domination (OKX-SPOT/OKX-FUTURES/BINANCE-SPOT/
OKX-SWAP/COINBASE-SPOT/BINANCE-FUTURES/BYBIT/HYPERLIQUID/DERIBIT/BITFINEX-FUTURES spread); **no impossible combos**
(SPOT_PAIR→{trades,book,ohlcv} only; PERPETUAL/FUTURE→{trades,book,deriv,liq,ohlcv}); **OPTION (141,259) + COMBO
(64,850) correctly produce ZERO rows** (matrix `frozenset()` → the G1-ENUM bundle-skip landed for cefi options/combos —
this is the over-fan the dry-run was meant to catch, and it is FIXED). The candidate set is per-instrument grain
(PERPETUAL 1,540 / SPOT_PAIR 1,026 / FUTURE 810).

### 🔴 Finding F1 (P0, data-correctness) — cefi chain bundle `data_type` axis inconsistency (PATH is the outlier)

The DERIBIT `options_chain`/`futures_chain` bundle OBJECTS are pathed
`…/instrument_type=<chain>/data_type=trades/ underlying=U/quote=Q/margin=M/ticks.parquet`, but the **canonical
`data_type` is `<chain>` (options_chain/futures_chain) per THREE independent sources**: the parquet's own internal
`data_type` COLUMN (= `futures_chain`), the v8 manifest rows (`data_type=futures_chain`, count>0), and the UAC validity
matrix (`("cefi","futures_chain")→{futures_chain}`). **Only the object PATH says `data_type=trades`.** The rebuild's
object classifier (`parse_hive_path`) trusts the PATH → emits canonical captured rows with `data_type=trades`, which
will NOT match the could-exist universe's expected `data_type=<chain>` cells → the ~169K cefi chain manifest rows
(options_chain 65,768 + futures_chain 103,160) risk showing UNCAPTURED in the honest denominator. The **"12 residual
phantoms"** (E5 §) are the SAME root: v8 rows with the canonical `data_type=<chain>` get demoted `→ attempted_failed`
because objects are pathed under `data_type=trades`. **The E5 claim that the 12 are "verifiably NO object → honest
absence → CORRECT" is INACCURATE** — I verified the objects DO exist
(`day=2024-06-01/venue=DERIBIT/instrument_type=futures_chain/data_type=trades/underlying=BTC/…/ ticks.parquet`, 5,292
trade rows, 7 contracts). Data is NOT lost (the object-scan re-emits a `data_type=trades` captured row), but the demote
mints phantom `attempted_failed` cells AND the canonical `data_type` for chains is contradictory across writer-path vs
UAC/manifest/parquet-column. Deribit is a `carry_staked_basis` hedge venue → critical path.

### 🔴 Finding F2 (P0, could-exist denominator) — cefi FUTURE captured at futures_chain BUNDLE grain, enumerated per-contract

DERIBIT futures are captured ONLY at `instrument_type=futures_chain` BUNDLE grain (one `underlying=BTC/ticks.parquet`
holds all alive BTC futures; `instrument_id=''`), but the IS catalogue lists them as per-contract
`instrument_type=FUTURE` (`DERIBIT:FUTURE:BTC-14JUN24`) → the enumerate produces per-contract `expected_unattempted`
(160 in the 2-day sample = 16 contracts × 5 dt × 2 days; corpus-scale ~100K+) that the bundle capture can never match →
**false coverage gaps**. Same class as slot-6 tradfi (per-contract producer vs bundle capture) + slot-4 sports (league
grain). **NOT a blanket matrix flip**: capture grain is VENUE-SPECIFIC — DERIBIT = futures_chain bundle only;
OKX-FUTURES = futures_chain per-symbol; **BYBIT has BOTH `future` (per-contract) AND `futures_chain`** — so
`("cefi","future")→frozenset()` would WRONGLY skip BYBIT per-contract futures. The matrix is venue-agnostic and cannot
express this; the correct fix is **catalogue-level (producer) venue-aware bundle rollup** — DERIBIT/OKX FUTURE roll up
to a `futures_chain` bundle catalogue entry (mirror the options_chain/combo bundle treatment), BYBIT per-contract
`future` stays. Co-owned with slot-7 (G1-ENUM central producer) per the master coordinator. The matrix row
`("cefi","future")` is correctly flagged `# UNCERTAIN — cefi-owner verify` — **verified: per-contract is wrong for
bundle-capture venues.**

### ✅ F1/F2 RESOLVED via the WRITER SSOT — it is an Era-A↔Era-B design conflict, NOT a migrator bug (slot-3 follow-up, 2026-06-07)

> **Apply-ready follow-up: read the live-writer SSOT to settle "which `data_type` is canonical for a chain bundle"
> (Findings-Triage "diagnose before fix — read BOTH sides").** The authoritative answer reverses F1's first read.

**The writer SSOT decides it.** `market-tick-data-service/.../adapters/cefi/tardis_shared.py` — the "single entry-point
all CeFi adapters must call before any parquet write" (its **Phase 1.6** of `data_canonicalisation_mvp`, docstring bug
#1) states verbatim: _"`data_type` was being overloaded with instrument-type tokens such as `futures_chain` /
`options_chain`. **`data_type` is a pure market-data axis (`trades`, `book_snapshot_5`, `derivative_ticker`,
`liquidations`). The collective-chain concept is carried on `instrument_type` instead.**"_ The
`finalise_rows_and_path()` shard-type logic confirms: OPTION rows bundled → `instrument_type=options_chain` shard;
FUTURE rows bundled (multi-symbol, same underlying) → `instrument_type=futures_chain` shard; **`data_type` stays the
pure market-data axis**. The tradfi Tardis adapter says the same: _"`options_chain`/`futures_chain` are NOT legal
canonical `data_type` … shard-instrument-type wrappers."_

**So the canonical chain bundle = `instrument_type=options_chain|futures_chain`,
`data_type ∈ {trades, book_snapshot_5, derivative_ticker, liquidations}` (the object PATH is CORRECT).** Observed
canonical capture (object walk over 2024-06-01 / 2025-01-15 / 2026-05-20): `options_chain → {trades}` (DERIBIT);
`futures_chain → {trades, book_snapshot_5, derivative_ticker, liquidations}` (DERIBIT/OKX-FUTURES/BYBIT). **This
REVERSES F1's first read** (which followed the v8 manifest + matrix + parquet-column): those three are the **legacy
Era-A** representation (`data_type=<chain>`, instrument_type blank — the exact pre-Phase-1.6 overload the writer
banned). The **rebuild's `parse_hive_path` is CORRECT** (emits `data_type=trades`, `instrument_type=<chain>`); the **"12
phantoms" are stale Era-A rows** (not real absences, but also not canonical cells) → cleaner to **DROP** (like the
existing `dropped_malformed_captured`) than demote. F1's todo-option (b) "map path `data_type`→`<chain>`" is **WRONG**
(it would re-introduce the banned overload).

**It is a deliberate, TESTED design conflict — not an oversight, so do NOT unilaterally flip it.** The UAC matrix
encodes the legacy **Era-A** form and `unified-api-contracts/tests/test_valid_data_types_by_instrument_type.py`
**asserts it**: `test_cefi_options_chain_bundle → frozenset({"options_chain"})`,
`test_cefi_futures_chain_bundle → frozenset({"futures_chain"})`. The live writer (Phase 1.6) implements **Era-B**. Two
self-consistent eras disagree across components (UAC matrix + v8 manifest **vs** the MTDS writer SSOT). Picking the
winner is a design decision spanning **cefi + tradfi (identical conflict) + slot-7's catalogue producer** → an operator
/ slot-7-coordinated call, landed as ONE coherent change so matrix↔catalogue↔manifest cannot drift. **Recommendation:
adopt Era-B (the writer SSOT is the newer, deliberate canonical; Phase 1.6 explicitly fixed Era-A as a bug).**

> **🟢 OPERATIONAL GATE CLEARED 2026-06-07**: G3 deployment-api/UI UNION read path **SHIPPED** (deployment-api@4dd2575 +
> deployment-ui@0dc40eb, master coordinator). So cefi's remaining apply-gates are G1 (PART A + this matrix decision) +
> the instruments-store v9 walk RUN + IS backfill + pre-migration drain.

**VERDICT — cefi G2 migrators DRY-RUN GREEN (re-confirmed 2026-06-07 post hyperliquid-rename); NOT apply-ready — BLOCKED
on slot-7 PART A + the Era-A/Era-B operator decision.** The three migrators (`migrate_cefi` paths @mtds c567962e ·
`rebuild_cefi_manifest` · `migrate_instruments_store_v9 --asset-group cefi`) remain dry-run-green and stamp every
canonical column correctly (CF-1/2/3/4/5/7/8/9/10/12/13 ✓; `_mode_source_for_venue`→`batch_tardis`/`batch_hyperliquid`
intact after the `hyperliquid_rest→hyperliquid` rename; IS/UAC unchanged at 0/0). The cefi **matrix slice is verified**:
`option/combo→frozenset()` ✓ correct; `options_chain/futures_chain` rows are **Era-A-stale** (fix paired with PART A,
below); `("cefi","future")` per-contract is venue-wrong for bundle-capture venues (catalogue rollup, not a matrix flip).
The bundle-grain **enumerate re-run + matrix correction are BLOCKED on slot-7 PART A** (catalogue venue-aware chain
rollup, not yet shipped — no in-flight PR as of 2026-06-07). The v9 `--apply` (G4) remains gated on **G0** (cefi
conforms ✓) **∧ G1** (PART A + Era decision) **∧ G3** (✓ shipped) **∧ instruments-store v9 walk RUN ∧ IS backfill ∧
pre-migration drain**. **CF-1…⑨ audit**: ①migrator ✓ ②rebuild ✓ ②IS-v9 ✓ ③4-state ✓ ④honest-empty ✓ ⑤read/write paths ✓
⑥IS+UAC guardrails — **the chain matrix rows fail ⑥ until the Era decision lands** ⑦numerator/denominator — **F2
bundle-grain pending** ⑧catalogue completeness — **BLOCKED on PART A** ⑨pipeline_mode source-aware ✓. Sampled (2-day
enumerate + 3-day object walk + 1-week rebuild); the v9 `_index` walk + multi-year phantom spot-check remain for the
apply run.

### 🟡 PREP UPDATE (slot-3, 2026-06-07 turn-3) — gate NOT yet met: slot-7 bundle-grain SSOT landed but NOT wired

> Re-validation gate = "slot-7 confirms the bundle-grain ROLLUP is GREEN." Status: **declarative SSOT shipped, producer
> NOT wired** → I did the unblocked prep only (instruments-store dry-run + matrix/grain slice review); held the
> enumerate re-run.

- **Slot-7 progress — `uac@dd7fa100` landed the bundle-grain AXIS SSOT** (`grain_for_instrument_type` +
  `INSTRUMENT_GRAIN_BY_AG_AND_INSTRUMENT_TYPE` + `GRAIN_BUNDLE_BY_UNDERLYING`/`GRAIN_LEAF`; exported from UAC). cefi
  grain rows: `("cefi", option|combo|options_chain|futures_chain) → GRAIN_BUNDLE_BY_UNDERLYING`. **But it has ZERO
  consumers** — grepped `instruments-service/scripts/` (`build_instrument_catalogue.py` +
  `enumerate_expected_universe.py`): neither imports/uses `grain_for_instrument_type`. `build_instrument_catalogue.py`
  last touched `99a5fbf5` (sports league), **no cefi/tradfi chain-bundle rollup commit**. So the catalogue still emits
  per-leaf OPTION/COMBO/FUTURE entries; the positive **per-underlying options_chain/futures_chain bundle candidate is
  NOT yet emitted**. The NEGATIVE collapse (OPTION/COMBO→`frozenset()`→0 rows) was already green last turn
  (`is@6ea46565`) and is unchanged → the catalog (`prod/catalog.parquet`) + enumerate are unchanged, so last turn's
  **3,446-candidate** result still stands; **no re-run performed** (gate not met, and nothing changed to re-measure).
- **Slot-7 acknowledged F2 in the SSOT comment** (verbatim cite of "F2, slot-3 2026-06-07"): venue-specific FUTURE
  bundling (DERIBIT/OKX bundle vs BYBIT per-contract) is "NOT expressible in the venue-agnostic matrix → gated todo;
  `VENUE_DATA_TYPE_CAPABILITIES` is NOT a sound discriminator." So F2 stays a venue-aware **catalogue-rollup** todo
  (PART A), as filed.
- **cefi grain slice VERIFIED**: the 4 BUNDLE rows are correct; `("cefi","future")` absent → `GRAIN_LEAF` default =
  correct for BYBIT, the known F2 gap for DERIBIT/OKX (gated). No grain-slice change needed from me.
- **🔴 THE APPLY-READINESS CRUX for chains — a `data_type` match requirement PART A must satisfy**: for a bundle
  candidate to MATCH the captured cell (else permanent false `expected_unattempted`), the candidate's `data_type` MUST
  equal the captured cell's `data_type`. **Capture is Era-B** (writer `tardis_shared.py` Phase-1.6 + `rebuild`
  `parse_hive_path` → `data_type=trades`; observed `options_chain→{trades}`,
  `futures_chain→{trades, book_snapshot_5, derivative_ticker, liquidations}`). **The matrix still returns Era-A**
  (`options_chain/futures_chain` → itself). PART A must pick ONE of: **(R1, recommended)** fix the matrix rows to the
  Era-B capture sets (`("cefi","options_chain")→{trades}`,
  `("cefi","futures_chain")→{trades, book_snapshot_5, derivative_ticker, liquidations}`) + update the 2 asserting tests;
  **(R2)** the catalogue bundle entry carries `instr.data_type=trades` so `_row_data_types` uses it and BYPASSES the
  matrix Era-A rows (then the matrix rows are vestigial). Either makes candidate `data_type==trades==capture`. **Until
  R1/R2 lands, the bundle candidates will not match the capture** — this is the chain apply-readiness blocker, on top of
  the catalogue rollup wiring. I did NOT flip the matrix (Era pick is coupled to PART A's R1/R2 choice + slot-7 just
  landed Era-A + the 2 tests + tradfi parity → coordinate, don't collide).
- **Re-confirmed GREEN (read-only, current LDR)**: `migrate_instruments_store_v9 --asset-group cefi --skip-objects` →
  30,803 rows v8→**100% v9**, `asset_group=cefi`/`data_type=instruments`/`pipeline_mode=batch_instruments_service`/
  `source=instruments_service`/`transport=rest`, `available_at` 30,803/30,803, honest `null_capture_to_captured=12,372`
  (cf_manifest_audit projection **CF-GREEN**). Unchanged from last turn (IS at 0/0 with LDR).

**Apply-readiness verdict UNCHANGED: cefi migrators dry-run-GREEN; NOT apply-ready.** Remaining gates: slot-7 PART A
(catalogue chain-bundle rollup WIRED to `grain_for_instrument_type` + the R1/R2 `data_type`-match) → then my enumerate
re-run; the Era decision (recommend R1/Era-B); instruments-store v9 walk RUN; IS backfill; pre-migration drain.

## ✅ cefi APPLY-READY — Era-B rollup re-validated GREEN (slot-3, 2026-06-08)

> **UNBLOCKED**: slot-7 landed **Era-B + the bundle-grain rollup** (R1 chosen): `uac@ae70338d`
> (`("cefi","options_chain")`/`("cefi","futures_chain")` → `frozenset({"trades"})` — NOT `{<chain>}`; the 2 tests
> updated) + `is@74df991d`/`687d1443` (the enumerate read-side `_rollup_bundle_grain` pre-pass consumes
> `grain_for_instrument_type` + `BUNDLE_INSTRUMENT_TYPE_BY_AG_AND_LEAF`, collapsing OPTION/COMBO leaves → ONE synthetic
> per-underlying `options_chain` candidate with `data_type=trades`). All present on LDR. **My F1 Era-B recommendation
> was adopted.**

**① RE-RUN enumerate dry-run on the Era-B rollup (read-only, real prod GCS).**
`enumerate v2 --catalog-path gs://instruments-store-cefi-prd/prod/catalog.parquet --start-date 2024-06-01 --end-date 2024-06-02`
(catalog 213,990; present-set 2,639,403) → **3,454 candidates**. **All gate criteria MET:**

- **No per-contract OPTION/COMBO rows** — `OPTION/COMBO/option/combo` = **0** (was 72K OPTION + 64.8K COMBO leaves
  pre-G1-ENUM). ✓
- **One `options_chain` candidate per underlying, `data_type=trades`** — **8** candidates = DERIBIT
  `{OPTION,COMBO}×{BTC,ETH}` × 2 days, **all `data_type=trades`** (Era-B), NOT `data_type=options_chain`. ✓ (they read
  `expected_unattempted` only because the v8 manifest isn't Era-B-relabeled yet — the relabel rides G4, not a dry-run
  blocker per operator).
- **No `data_type=options_chain`/`futures_chain` candidate** = 0; **no impossible pair** (PERPETUAL×options_chain) = 0.
  ✓
- **DERIBIT no longer dominates** — DERIBIT = 396/3,454 = **11.5%** (behind OKX-FUTURES 540, BYBIT 440, OKX-SPOT 402,
  OKX-SWAP 390). ✓

**Verified MY UAC slice — CORRECT, no change needed**: validity `("cefi", option/combo)→frozenset()`,
`(options_chain/futures_chain)→{trades}` (Era-B) ✓; grain
`(option/combo/options_chain/futures_chain)→ GRAIN_BUNDLE_BY_UNDERLYING` ✓; `BUNDLE_INSTRUMENT_TYPE_BY_AG_AND_LEAF`
`(cefi,option/combo)→options_chain` ✓. The count is NOT inflated → slice is right (the prompt's "fix your slice if
inflated" did not trigger).

**🟡 ONE residual could-exist gap (F2, slot-7-owned, NOT mine, NOT a migrator/G4 blocker)**: cefi `FUTURE` is **not**
rolled up (slot-7 DELIBERATELY omits `future→futures_chain` from `BUNDLE_INSTRUMENT_TYPE_BY_AG_AND_LEAF` with the
comment "venue-specific: DERIBIT/OKX bundle, BYBIT per-contract; F2"). So **880 per-contract FUTURE candidates** remain
(2-day) — **700 are DERIBIT+OKX-FUTURES = FALSE over-seed** (bundle-captured at `futures_chain`), 180 BYBIT genuine.
This over-seeds the **G1.run futures `expected_unattempted` seed** only; it does NOT touch the G4 manifest/data
migration. Fix = slot-7 **venue-aware `build_instrument_catalogue` rollup** (emit per-underlying `futures_chain` bundle
entries for DERIBIT/OKX; BYBIT stays per-contract) — the matrix is venue-agnostic and cannot express it. Tracked as F2
P0 below.

**②③ migrators ALREADY GREEN** (re-confirmed): `migrate_cefi` source-aware `batch_tardis`/`batch_hyperliquid` +
bundle-grain-preserving paths (`mtds@c567962e`); `rebuild_cefi_manifest --dry-run` exit 0 (writer-stamped v9 columns);
`migrate_instruments_store_v9 --asset-group cefi` 30,803 rows→**100% v9** (all columns + honest
`null_capture_to_captured=12,372`, re-confirmed 2026-06-08).

**④ 7+2 audit**: ①migrator ✓ ②rebuild ✓ ②IS-v9 ✓ ③4-state ✓ ④honest-empty ✓ ⑤read/write paths ✓ ⑥IS+UAC guardrails ✓
(Era-B resolved the chain-matrix conflict) ⑦numerator/denominator ✓ for OPTION/COMBO bundle, **F2 FUTURE over-seed
pending** ⑧catalogue completeness — options bundle ✓, futures bundle pending F2 ⑨pipeline_mode source-aware ✓. Sampled:
2-day enumerate + 3-day object walk + 1-week rebuild + full IS `_index` v9 projection.

**VERDICT — cefi APPLY-READY.** The G4 manifest/data migration (`migrate_cefi` + `rebuild_cefi_manifest` +
`migrate_instruments_store_v9`) is dry-run-GREEN and the Era-B OPTION/COMBO bundle could-exist case is re-validated
GREEN. **The ONLY remaining gates are operational/owned-elsewhere**: G0 ✓ · G3 ✓ (UNION view shipped) · the
instruments-store v9 walk RUN · IS backfill · the **Era-B legacy-row relabel** (rides G4 migrator, operator
`slot-7 edca81b57`) · pre-migration drain · **F2 FUTURE venue-aware catalogue rollup** (slot-7; gates only the G1.run
_futures_ seed, not the migration). Shas: `uac@ae70338d` · `is@74df991d`/`687d1443` (rollup) · `mtds@c567962e`
(migrator) · enumerate re-run 2026-06-08 (3,454 plausible). No `--apply` run (gated).

- [x] ✅ [DATA] P0. **F1 — Era decision MADE = Era-B; UAC matrix slice + tests LANDED (slot-3 verify 2026-06-08).** The
      Era-B recommendation was adopted (the writer-SSOT `tardis_shared.py` Phase-1.6 canonical): `uac@ae70338d` sets
      `("cefi","options_chain")`/`("cefi","futures_chain")` → `frozenset({"trades"})` (NOT `{<chain>}`) and updated the
      two asserting tests (`test_cefi_options_chain_bundle`/`test_cefi_futures_chain_bundle`); the object PATH + rebuild
      `parse_hive_path` (Era-B: `instrument_type=<chain>`, `data_type=trades`) are CORRECT and unchanged. **My UAC slice
      verified correct, no change needed.** The remaining stale Era-A `data_type=<chain>` v8 row DROP/relabel rides the
      G4 migrator/rebuild re-emit (re-emits Era-B from objects; the old Era-A rows are not re-emitted → effectively
      dropped) — that is the OPERATIONAL apply-time tranche (operator `slot-7 edca81b57`), not a remaining pre-apply
      CODE change. The earlier F1 "canonical=`<chain>`" + E5 "12-phantom=honest-absence" reads are formally reversed
      (Era-A was the legacy overload). Provenance: slot-3 G2 verify + writer-SSOT follow-up 2026-06-07 + Era-B
      re-validation 2026-06-08. <!-- original F1 spec retained below for trace -->
- [x] ✅ [DATA] P0. **F1 (RESOLVED — needs operator/slot-7 Era decision, then a coherent UAC+manifest change) — cefi
      chain `data_type` axis: Era-A (`data_type=<chain>`) vs Era-B (`instrument_type=<chain>`, `data_type=trades`).**
      Writer SSOT `tardis_shared.py` Phase-1.6 = **Era-B is canonical** (chain is instrument_type; `data_type` is pure
      market-data — the object PATH + rebuild are CORRECT). **Recommend adopting Era-B**: (1) fix UAC matrix
      `("cefi","options_chain")→{trades}` +
      `("cefi","futures_chain")→{trades, book_snapshot_5, derivative_ticker,     liquidations}` (the observed canonical
      capture) + update the two asserting tests; (2) rebuild/migrate **DROP** the stale Era-A `data_type=<chain>` v8
      rows (mirror `dropped_malformed_captured`) instead of demoting them (the "12 phantoms"). **Reverses the earlier F1
      "canonical is `<chain>`" + E5 "12-phantom = honest absence" reads.** DO NOT unilaterally flip — the matrix form is
      deliberate + TESTED + identical in tradfi → coordinate the Era pick with the operator + slot-7 and land
      matrix↔catalogue↔manifest as ONE change. **The matrix SLICE (UAC) is the AG-owner's** to fix once the Era is
      decided; the **catalogue producer** is slot-7's. Provenance: slot-3 G2 verify + writer-SSOT follow-up 2026-06-07.
      **Big finding — operator notified.**
- [ ] [DATA] P0. **F2 — cefi FUTURE bundle-grain: catalogue venue-aware rollup (BLOCKED on slot-7 PART A).**
      DERIBIT/OKX-FUTURES bundle-captured `FUTURE` roll up to a `futures_chain` bundle catalogue entry (one per
      underlying) so the enumerate produces bundle cells matching the bundle capture; **BYBIT per-contract `future`
      stays per-contract** (verified: BYBIT writes both `future` AND `futures_chain` shards). Producer-level fix in
      `build_instrument_catalogue.py` (slot-7 G1-ENUM central producer — PART A; mirror the prediction cqg + sports
      league rollups + slot-6 tradfi). Verified cefi matrix slice: `option/combo→frozenset()` ✓; `("cefi","future")`
      per-contract is venue-wrong for bundle-capture venues (venue-specific → catalogue rollup, NOT a matrix flip).
      Gates cefi G1.run apply-write. Provenance: slot-3 G2 verify 2026-06-07. **🟢 MY SLICE CONFIRMED (slot-3
      2026-06-08, re-verify) — STAYS OPEN, slot-7-owned producer:** the UAC slice is correct as-is — `("cefi","future")`
      is absent from `BUNDLE_INSTRUMENT_TYPE_BY_AG_AND_LEAF` → `GRAIN_LEAF` default (correct for BYBIT per-contract; the
      known F2 gap for DERIBIT/OKX-FUTURES), and `grain_for_instrument_type` cefi rows are right. NO matrix/grain change
      is mine to make (the matrix is venue-agnostic; the fix is venue-aware catalogue rollup in slot-7's
      `build_instrument_catalogue.py`). **Safe to leave open pre-G4**: F2 over-seeds ONLY the G1.run _futures_
      `expected_unattempted` denominator seed (700/880 2-day candidates false on DERIBIT/OKX), it does **not** touch the
      G4 manifest/data migration — so the cefi `--apply` migration is not blocked by it.
- [x] ✅ [DATA] P0. **G2 verify dry-runs (cefi) GREEN on WAVE-1 shape-aware code** — ① `migrate_cefi` (source-aware
      `batch_tardis` path + bundle-grain preserved) · ② `rebuild_cefi_manifest --dry-run` exit 0 (writer-stamped v9
      columns, source-aware) · ② `migrate_instruments_store_v9 --asset-group cefi` (30,803 rows→100% v9, all columns +
      honest capture_status) · ③ `enumerate v2` exit 0, 3,446 plausible candidates (OPTION/COMBO bundle-skip working, no
      over-fan, no impossible combos). Surfaced F1+F2 (could-exist, gating apply-write). mtds@`is@6ea46565`/
      `febb899e`/`uac@97c26dbe` present on LDR. Evidence in this § (slot-3 2026-06-07).

## ✅ PRE-APPLY 12-POINT AUDIT VERDICT (slot-3, 2026-06-08) — REAL-PROD re-verification

> Re-ran the full ①–⑫ readiness audit on **real-prod GCS data-state** (`gcloud storage` byte-probes + the actual
> `_index` parquets + live migrate/rebuild/enumerate dry-runs), NOT code constants — per the operator's "assume nothing,
> verify on data-state" gate. All repos clean + `tab ⊇ LDR`
> (mtds/is/mdps/features/strategy/execution/deployment-api/utl/uac). **Real pre-migration state (probed): MTDS cefi
> `_index` = 2,640,864 rows 100% v8, `source`/`asset_group`/`transport` columns ABSENT, `pipeline_mode` all blank/None;
> IS cefi `_index` = 30,803 rows 100% v8, 12,372 null `capture_status`. This is the EXPECTED pre-migration v8 state —
> the v9 `--apply` is correctly operator-gated (not run).** The audit proves the migration TOOLING produces correct,
> no-regression v9.

| #   | Point                                | Verdict                 | Evidence (real-prod, sampled-vs-walked)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| --- | ------------------------------------ | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ①   | Migrator dry-run                     | 🟢                      | `migrate_cefi_flat_to_v9_canonical --start 2019-03-31 --end 2019-03-31` (dry-run) exit 0, **planned=96**, every projected dest `…/day=/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=perpetual/data_type=…/` — source-aware path+col; the **double-key `asset_group=cefi/category=cefi/` legacy form is correctly mapped to canonical** (via `_kv` dict extraction, drops the redundant `category=`), NOT dropped. SAMPLED 1 dual-existence day.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ②   | Rebuild dry-run                      | 🟢                      | `rebuild_cefi_manifest --start 2019-03-31 --end 2019-03-31 --dry-run` → **exactly 6 ParsedShards (one per cell), all `pipeline_mode='batch_tardis'`, NO double-count**. On the dual-existence day the legacy double-key path is `unparseable→skip` while the canonical `pipeline_mode=batch_tardis/` emits once. **migrate(paths)-before-rebuild(manifest) sequencing** ⇒ every cell (incl L-flat/L-bulk/double-key) has a canonical copy the rebuild parses cleanly. `derive_pipeline_mode_for_row` converges legacy(blank-pm) and canonical to the SAME atom (rebuild `:727-728`). SAMPLED 1 day.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ③   | 4-state pre-flight                   | 🟢¹                     | Real `_index` carries `captured` (1,310,443) / `attempted_failed` (1,330,271) / `empty_confirmed` (150). **`expected_unattempted` = 0 rows today** (materialised by the gated `enumerate --apply-write` seed — ⑦/⑧ operational). 4-state READ is wired in deployment-api union + features/strategy pre-flight. ¹capability GREEN; the `expected_unattempted` state populates at the gated G1.run seed. WALKED capture_status distribution.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ④   | Empty/partial honest + downstream    | 🟢                      | `empty_confirmed`=150 **all typed `EXPECTED_PRE_VENUE_LAUNCH`** (closed set); `phantom_captured_no_parquet_at_canonical_path`=32 flagged for CF-11 demote; legacy blank-reason rows (`LegacyBlankErrorReasonError` 789,201) ride the rebuild `reemit_cefi_honest_absence_rows` reclassify; downstream reads the 4-state honestly. WALKED error_reason distribution.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ⑤   | Read/write paths match               | 🟢                      | **Zero coarse-exact `pipeline_mode=batch/` survivors** across mtds/mdps/features/strategy/execution/deployment-api/utl. All readers prefix-match `batch_*`/`live_*`/`replay_*` + bare-legacy via `candidate_parquet_paths()`/`derive_pipeline_mode_for_row()`, canonical-over-legacy ranked. WALKED 7 repos (sub-agent).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ⑥   | IS+UAC guardrails                    | 🟢                      | cefi validity slice: `(option/combo)→frozenset()`, `(options_chain/futures_chain)→{trades}` (Era-B), `(perpetual)` excludes options*chain ⇒ impossible pairs rejected; grain `(option/combo/options_chain/futures_chain)→GRAIN_BUNDLE_BY_UNDERLYING`, `BUNDLE*…\_BY_AG_AND_LEAF (cefi,option/combo)→options_chain`. Enumerator `\_row_data_types`+`\_rollup_bundle_grain`apply both. **F2`(cefi,future)` bundle-grain gap is slot-7-owned (venue-aware catalogue rollup) — over-seeds only the G1.run futures seed, NOT a G4 blocker.\*\* WALKED UAC+IS (sub-agent).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ⑦   | deployment-api numerator+denominator | 🟡 RED-tracked          | UNION path SHIPPED (`deployment-api@46e3d57`, `union_reduce_to_cells` ≥1-captured⇒captured + pipeline_mode×source drilldown). **BUT cefi coverage% DENOMINATOR still re-derives genesis/launch (`_apply_mtds_honest_coverage`/`_mtds_honest_coverage_for_venue`) instead of READING materialised `expected_unattempted`** — CORRECT pre-seed (0 `expected_unattempted` exist today), must SWITCH to the 4-state READ after the enumerate `--apply-write` seed. Downstream/deployment-api-owned; gates honest coverage POST-seed, **NOT the G4 migration**. New todo below. WALKED deployment-api (sub-agent).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ⑧   | IS-catalogue completeness (CF-14)    | 🟡 RED→root-cause-fixed | Catalogue `prod/catalog.parquet` = 213,990 rows / **12 venue IS reference universe**; manifest captured present-set = **45 venues** → **29 captured venues MISSING = 108,556 captured rows (8.3%)**, headline **KRAKEN-SPOT (75,714) + KRAKEN-FUTURES (31,582)** (genuine — on disk 2026-05-24), + PACIFICA-SOLANA/LIGHTER-ZKSYNC + ~650 `*F0`/`UNKNOWN` pollution. **ROOT CAUSE = IS Tardis adapter `_DEFAULT_EXCHANGES` was a stale 8-id subset that drifted below the SSOT `VenueMapping.all_tardis_exchanges` (20)** — omitted `kraken`/`cryptofacilities`(=KRAKEN-FUTURES)/`bitfinex`/`bitget`/`lighter-zksync`. **🟢 CODE FIX SHIPPED `is@a6bc4d48` (QG green)**: `_DEFAULT_EXCHANGES` now derives from the SSOT (no future drift) + derivatives-only classification + 3 regression tests. **REMAINING (operational, not a G4 blocker): re-run the IS reference backfill** so `by_date/` ⊇ the captured present-set (memory-heavy VM sweep, `instruments_backfill_phase3`) + CLOB venues (PACIFICA/LIGHTER, separate adapter) + `*F0` pollution. Gates honest coverage, **NOT the G4 data/manifest migration**. WALKED both full datasets + adapter root-cause. |
| ⑨   | pipeline_mode source-aware (CF-13)   | 🟢                      | Round-trip on real venues: `derive_pipeline_mode_for_row(v,'cefi','trades')` → `batch_tardis` (DERIBIT/KRAKEN-\*/BITFINEX-SPOT/BYBIT) / `batch_hyperliquid` (HYPERLIQUID); `source_string_for(pm)` == source for ALL ⇒ CF-13 match=True. UTL C-#6 `_assert_source_matches_pipeline_mode` enforces at write. WALKED 6 venues.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ⑩   | Era-B on-disk byte-probe             | 🟢                      | `gcloud storage` probe: `…/venue=DERIBIT/instrument_type=futures_chain/data_type=trades/underlying=BTC/quote=USD/margin=inverse/ticks.parquet` (2026-01-15) — Era-B bundle shape (chain = instrument_type, data_type=trades, underlying/quote/margin sub-keys); **0 `data_type=options_chain`/`data_type=futures_chain` overload** in the sampled recent days. SAMPLED recent DERIBIT chain day.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ⑪   | ★ BATCH=LIVE symmetry                | 🟢                      | Live writer (`tardis_shared.py` Phase-1.6 + orchestrator PartitionedTickWriter) and migrator produce **byte-identical v9 form**: same `pipeline_mode={mode}_{source}/` LEFT of `asset_group=`, same Era-B instrument_type/data_type split, same manifest columns via shared `ManifestWriter` + `derive_pipeline_mode_for_row`, `available_at` preserved byte-for-byte (migrator `gcs_copy_object` does not touch tick content; manifest emission shared). No live-only data_type; no read-time `available_at`. WALKED live writer + migrator + rebuild (sub-agent).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ⑫   | Rollback ready                       | 🟢                      | `_index/snapshots/pre_migration_2026_06_08.parquet` present in BOTH `market-data-tick-cefi-prd` + `instruments-store-cefi-prd`; phantom-audit `ASSET_GROUP_CONFIG["cefi"].prefix_tpls` covers `pipeline_mode=batch_tardis/`, `batch_hyperliquid/`, bare `asset_group=cefi/`, legacy `category=cefi/`, + top-level shapes ⇒ no false captured→attempted_failed flip on `--apply`. WALKED snapshot + prefix_tpls.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |

**REGRESSION RISK: NONE** for the G4 data/manifest/schema migration. The no-regression keystone (⑪ batch=live) is GREEN
— the migrator produces the byte-identical canonical v9 form the live writer emits; ①/② prove no double-count + no
silent loss (copy-not-move is safe: rebuild dedups to one atom/cell, readers rank canonical-over-legacy,
migrate-before-rebuild guarantees every legacy shape gets a parseable canonical copy); ⑤/⑨/⑩/⑫ GREEN. The **two RED
points (⑦/⑧) are honest-coverage-COMPLETENESS gates** (the could-exist denominator), already tracked as operational
gates (IS backfill + the enumerate `--apply-write` seed) — they make coverage MORE honest (avoid falsely-high), and are
NOT a regression between the migrated data and the canonicalised code. **cefi G4 migration = APPLY-READY (operator-gated
run); honest-coverage = blocked on ⑦/⑧ + the named operational gates.**

- [ ] [DATA] P0. **⑧ — IS cefi REFERENCE-UNIVERSE gap: catalogue not ⊇ manifest present-set (CF-14, falsely-high
      coverage). 🟢 ROOT-CAUSE CODE FIX SHIPPED `is@a6bc4d48`; operational backfill re-run + CLOB sub-part remain.**
      Real-prod (2026-06-08): IS `instruments-store-cefi-prd` `instrument_availability/by_date/day=2026-05-22/` lists
      only **12 venues** {ASTER, BINANCE-FUTURES/SPOT, BITFINEX-FUTURES, BYBIT, COINBASE-SPOT, DERIBIT, HYPERLIQUID,
      OKX-FUTURES/SPOT/SWAP, UPBIT}; the MTDS manifest captures **45 venues** ⇒ **29 captured venues absent from IS
      reference = 108,556 captured rows (8.3%)**. Headline genuine gaps: **KRAKEN-SPOT (75,714) + KRAKEN-FUTURES
      (31,582)** (KRAKEN-FUTURES verified on disk `day=2026-05-24`), **BITFINEX-SPOT**, **PACIFICA-SOLANA (309)**,
      **LIGHTER-ZKSYNC (319)**. **ROOT CAUSE FOUND (corrects the earlier "dynamic universe" read):** the IS Tardis
      reference adapter (`reference_data/adapters/cefi/tardis.py`) had a **hand-maintained `_DEFAULT_EXCHANGES` of 8
      Tardis exchange-ids** (`binance/binance-futures/bybit/okex/deribit/coinbase/upbit`) that had **silently DRIFTED
      below the canonical SSOT `VenueMapping.all_tardis_exchanges` (20)** — omitting `kraken`, `cryptofacilities`
      (=KRAKEN-FUTURES), `bitfinex`, `bitget`, `lighter-zksync`. (My KRAKEN/DERIBIT grep missed it because the list uses
      lowercase Tardis _exchange-ids_, not canonical venue NAMES — the SSOT already maps `kraken→KRAKEN-SPOT`,
      `cryptofacilities→KRAKEN-FUTURES` with start-dates.) So the IS reference backfill never queried those venues →
      catalogue ⊉ present-set → falsely-high coverage. **(1) ✅ CODE FIX SHIPPED `is@a6bc4d48` (QG --no-fix green):**
      `_DEFAULT_EXCHANGES = list(VenueMapping().all_tardis_exchanges)` (derives from SSOT → no future drift; verified
      ==SSOT, now includes kraken/cryptofacilities/bitfinex/bitget/lighter-zksync) + extended
      `_DERIVATIVES_ONLY_EXCHANGES`
      (cryptofacilities/okex-futures/okex-swap/huobi-dm/bitfinex-derivatives/bitget-futures) so unknown-type instruments
      aren't mis-defaulted to SPOT + 3 regression tests asserting no-drift-from-SSOT. **(2) OPERATIONAL (owner:
      `instruments_backfill_phase3` / vm-cross-cutting) — re-run the IS reference backfill with the fixed universe so
      `instrument_availability/by_date/` ⊇ the MTDS captured present-set (memory-heavy multi-year VM sweep — the adapter
      cache OOM-killed `cefi-instr-deribit` 2026-05-04, run on a VM).** **(3) CLOB venues PACIFICA-SOLANA +
      LIGHTER-ZKSYNC are NOT Tardis exchanges — they ride the CLOB adapter path (hyperliquid.py / aster.py); confirm an
      IS reference adapter enumerates them (only hyperliquid+aster exist today) — separate from the Tardis fix.** **(4)
      diagnose the ~650 `*F0`/`UNKNOWN`-venue manifest-pollution rows (blank instrument_type/instrument_id) — reconcile
      or demote.** Gates honest coverage denominator (⑦/⑧), NOT the G4 data/manifest `--apply`. **Big finding — operator
      notified 2026-06-08.** Provenance: slot-3 pre-apply audit 2026-06-08 (real-prod catalogue vs manifest walk + IS
      adapter `_DEFAULT_EXCHANGES` root-cause).
- [ ] [CODE] P1. **⑦(a) — deployment-api cefi coverage DENOMINATOR re-derives genesis/launch instead of READING
      `expected_unattempted` (post-seed switch).** `deployment_api/.../data_status_service.py`
      `_apply_mtds_honest_coverage` → `_mtds_honest_coverage_for_venue` (`~:1668`) computes
      `expected_count = len(_mtds_expected_dates_for_venue_dt(...))` = a genesis/launch daily-grid re-derivation; the
      materialised `expected_unattempted` 4-state is used only as a numerator filter, never the denominator — violates
      the F4/CF-14 "consumers READ the 4-state, never re-derive genesis/launch". CORRECT today (0 `expected_unattempted`
      rows exist pre-seed); becomes wrong AFTER the `enumerate_expected_universe --asset-group cefi --apply-write` seed
      materialises them. **Fix (owner: deployment-api / downstream — vm-cross-cutting): post-seed, switch the cefi
      coverage denominator to the G3 union 4-state READ (`captured/(captured+empty+failed+expected_unattempted)` over
      the could-exist denominator), retire the `_apply_mtds_honest_coverage` genesis re-derivation for cefi.** Adjacent
      to the tracked "per-date denominator (P3)" item but distinct (re-derive-vs-read, not granularity). Gates honest
      coverage POST-seed, NOT the G4 migration. Provenance: slot-3 pre-apply audit 2026-06-08.

## Slot-3 CeFi master orchestrator — owned + attached plans/issues

> **Slot↔asset-group split (operator 2026-06-03):** one asset group per slot. **Slot 3 = CeFi end-to-end** across every
> service — instruments-service → MTDS → MDPS → features → downstream → bucket/data/manifest/UI. **THIS plan is the CeFi
> master orchestrator**: every cefi-related plan + issue cross-references here; orphaned cefi issues attach here.
> Sibling AG masters: **defi → slot 2**, **sports → slot 4**, **prediction → slot 5**
> (`prediction_manifest_canonicalisation_2026_06_01.md`), **tradfi → slot 6**
> (`tradfi_manifest_canonicalisation_2026_06_01.md`). Cross-cutting service plans keep their own `assigned_vm` (vm-ml /
> vm-cross-cutting) as PRIMARY owner — slot-3 tracks + drives only their **cefi slice**, not the whole plan.

**Absorbed (cefi-primary — slot-3 owns outright):**

- `issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md` — **ABSORBED 2026-06-03** (harsh out for the
  day; was harsh-held). The manifest↔file disconnect (MTDS marks `processed_candles` `captured` for KRAKEN/BITFINEX with
  no file; ~42% phantom on the test date) IS the CF-11 honest-absence reconciliation this plan owns — folded as the
  CF-11 "MTDS processed_candles phantom-`captured` reconcile" todo below. Issue doc archives when that todo is GREEN.

**Cross-referenced cefi slices (primary owner keeps the plan; slot-3 drives the cefi portion):**

| Plan / issue                                                                                                                    | Primary VM         | CeFi slice                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------- |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`                                                                  | vm-cross-cutting   | L3 cefi ordering + L6 legacy `market-data-tick-cefi` delete (this plan's E8 hand-off) |
| `data_source_provenance_all_asset_groups_2026_06_01.md`                                                                         | vm-ml              | cefi `source=tardis` column (this plan's C-source RIDER)                              |
| `pipeline_mode_partition_migration_2026_06_01.md`                                                                               | vm-cross-cutting   | cefi `pipeline_mode=` partition (this plan's C-pipeline_mode RIDER)                   |
| `data_pipeline_acquisition_remediation_2026_06_03.md`                                                                           | orchestrator-agent | cefi audit-finding phase                                                              |
| `issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md`                                                           | vm-ml              | cefi 9 root-level real-data files (SUPERSEDED by E2 migrator)                         |
| `features_input_manifest_migration` / `features_service_e2e_pipeline_test` / `features_calc_efficiency_and_correctness`         | vm-ml              | cefi processed_candles read-path + e2e + calc correctness                             |
| `mdps_filter_pushdown_memory_audit_and_fix` / `mdps_pure_polars_migration` / `mdps_long_running_multi_shard_architecture_audit` | vm-ml              | cefi MDPS processing slice                                                            |
| `issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`                                                                     | vm-ml              | cefi state adapters (derivative / futures / options / book_snapshot)                  |

## 🎬 NEXT-SESSION HANDOFF (slot-3 cefi, paste-ready, 2026-06-03)

**GOAL:** complete CeFi work **up to and including the dry-run VM + bucket creation**. **HARD CONSTRAINT (operator):**
EVERY coding task across ALL repos must be DONE + green-on-LDR **before** you launch the dry-run VM or create any
bucket. Code first; GCS execution only after.

**OUT OF SCOPE this session (deliberate, later):** the IRREVERSIBLE ~1.2M-object orphan delete (old
`day=/asset_group=cefi/` no-`pipeline_mode=` objects + 9 L-flat root files) and the **E8 legacy-bucket delete**. Do NOT
run them — they need the pre-delete idempotent-guarantee + verification + operator awareness.

**STATE — DO NOT RE-DERIVE (verified 2026-06-03):** the `-prd` `pipeline_mode=` migration is **COMPLETE corpus-wide**
(raw_tick + candles + 9 L-flat all have canonical forms; sampled 2020→2026). The migrator WORKS — the "E4-BUG" claim was
**RETRACTED** (`moved=0` = idempotent-skip). Only ADDITIVE data work left = the `--also-legacy` 5,233-cell gap-fill. E5
rebuild DONE (mtds@2c3a479b). features-service residual #1 (933b8747) + conftest fix (d39d154f) SHIPPED; the
features-service full-QG flake is **macOS-local** (Linux `quality-gates-v2` green — don't chase on Linux; ship via
operator exemption if a local macOS gate blocks).

**PHASE 1 — ALL CODING (ship each via quickmerge; flip the checkbox same-turn):**

- [x] ✅ [CODE] instruments-service — CF-11 IS-side write-path: cefi reference-data adapters now **raise on a genuine
      fetch-failure** (→ `_fetch_one` `failed[]` → `attempted_failed`) instead of `return []` (which landed the venue in
      `_non_error_venues` → excluded from `expected_venues` → silent universe shrink, worse than `empty_confirmed`).
      Cross-AG sweep slot-6@e2e008f0 fixed aster/hyperliquid/tardis (RuntimeError); slot-3 completed the one they missed
      — **DeribitCombo** (`get_instruments` tracks per-currency `failures`, re-raises if EVERY currency failed; partial
      success preserved) — instruments-service@f2ca5954 + regression tests (IS QG --no-fix exit 0, 3097 pass). Mirrors
      the tradfi databento CF-11 fix. (cefi CF-11 below)
- [x] ✅ [CODE] market-data-processing-service — CF-11 #3: **VERIFIED no emission bug** (slot-3 grep-then-READ
      2026-06-03). The apparent ohlcv "under-emission" is the **intended WriteGate honest-coverage** behaviour —
      `canonical_writer.py:1318-1322` documents that policy-gated rows write bytes (heartbeat) but deliberately skip the
      manifest `captured` row; the normal path emits exactly one row per published candle; a manifest-write failure
      emits `MANIFEST_WRITE_FAILED` (not silent). So MDPS faithfully reflects published candles. The real `ohlcv` gap
      (8,715 rows; BITGET-heavy files) is a **candle BACKFILL (DATA)**, not a code bug → tracked as the CF-11 #2
      candle-coverage DATA item below. No MDPS code change.
- [x] ✅ [CODE] unified-trading-pm — identity-hook follow-ups (`issues/commit_identity_misconfig_fleet_2026_06_03.md`) —
      **SHIPPED + VERIFIED on LDR (slot-3 re-verify 2026-06-04).** Leak root-caused + fixed: `rollout-semver-agent.sh`
      (one-shot transient `git -c user.name=… -c user.email=… commit`, lines 116-129, never a persistent shared-config
      write); `setup-workspace-from-manifest.sh` only-seeds-if-unset the canonical
      `ikennaigboaka@gmail.com`/`ikennaigboaka` (lines 347-356, no more `--global agent@ci.local`);
      `setup-tab-worktrees.sh` provisions `extensions.worktreeConfig true` + `--worktree user.name/email` per slot
      (lines 214-216); NEW self-heal pre-commit hook `scripts/hooks/fix-commit-identity.sh` blocks+repairs a wrong
      per-worktree identity; recurrence-guard in `verify-slot-host-symmetry.sh`. Verified live: all slot-3 worktrees
      author `ikennaigboaka [slot-3·laptop]` / `ikennaigboaka@gmail.com` with `worktreeConfig=true`. SSOT:
      `codex/05-infrastructure/per-tab-worktrees.md` § "Commit attribution". Issue doc
      `commit_identity_misconfig_fleet_2026_06_03.md` → archivable.
- [x] ✅ [CODE] market-tick-data-service — orphan-sweep/gap-fill **VERIFIED needs no code** (slot-3 2026-06-03): the
      migrator `migrate_cefi_flat_to_v9_canonical.py` already handles `--also-legacy` over all 3 layouts, idempotent
      skip-if-exists = copies ONLY the gap. The explicit orphan-DELETE mode is deliberately NEXT session (irreversible).
- [x] ✅ [SCRIPT] P3. grep this plan for remaining open `[ ] [CODE]` todos — **DONE (slot-3 2026-06-08 pre-apply
      code-clear sweep).** Triaged every open `- [ ]`. CODE items now CLOSED: funding name+unit mismatch (resolved in
      code + pinning test), `_enumerate_v2_cefi` combo-validity+bundle-grain for OPTION/COMBO (landed `uac@ae70338d`/
      `is@74df991d`/`687d1443`/`6ea46565`, dry-run GREEN), F1 Era-B matrix decision (landed `uac@ae70338d`). Remaining
      open CODE items are **deferred-with-reason, all safe pre-`--apply`**: F2 FUTURE rollup (slot-7 producer,
      over-seeds only the futures denominator seed); execution-service `defi.py:41,77` (slot-2/defi AG, not cefi);
      deployment-api FLAG-1/FLAG-3/pipeline_mode-dedup (downstream-owner; cefi single-source + dedup already works);
      MDPS GAP-7 rename (downstream plan GAP-7 owner); rebuild within-bounds precision (NICE-TO-HAVE); ⑦ catalog-path
      build+run (the enumerate CODE is done — remaining is the operational VM run). All DATA `- [ ]` are apply-time
      (walk / rebuild / orphan-sweep / E7 verify / E8 delete / instruments-store v9 walk / candle backfill).

**GATE:** confirm ALL Phase-1 coding shipped + `quality-gates-v2` green on LDR per repo BEFORE Phase 2.

**PHASE 2 — DRY-RUN VM + BUCKET CREATION (only after Phase-1 green):** create any buckets the plan needs (via
`resolve_bucket_name`, never inline `gs://`); re-run the E4 **dry-run** on a VM to measure the REMAINING scope (the
`--also-legacy` gap-fill + orphan count — NOT the done `-prd` walk), **sharded by year / bigger-mem** (the 1.9M legacy
listing OOM'd an e2-standard-4). `VM_TASK=canonical-migration`,
`VM_MIGRATION_CMD=… migrate_cefi_flat_to_v9_canonical --start-date … --end-date … --also-legacy` (NO `--apply` = dry).
No-fire-and-forget (STARTED + T+10min + read `…/vm-logs/<vm>/run.log`). STOP at dry-run + bucket creation — the
`--apply` gap-fill / orphan delete / E8 are the NEXT session.

## E2E code-readiness audit (slot-3, 2026-06-03) — get the CODE canonical BEFORE the migration runs

> **Operator framing**: "code e2e" = after the migration runs, future backfills + code + data-status summary + drilldown
> all align with the migrated structure. The migration's PATH/SCHEMA/COLUMNS must be IDENTICAL in the writers, readers,
> preflight gates, manifest rebuild, and deployment-api/UI — and empty + partial must be handled the same in code as in
> reality. 5-dimension audit (path / schema-columns / empty-partial / data-status-UI / plan-sweep).

### 🚦 CeFi E2E RUN-READINESS GATE (full IS→execution audit, 2026-06-04, slot-3 + sub-agents)

> **Operator bar (2026-06-04):** before the migration runs, ALL of the below must be DONE + ticked: ① migrator dry-run,
> ② manifest-rebuild dry-run, ③ **pre-flight engrained on EVERY service IS→execution using the canonical post-migration
> paths**, ④ **empty/partial handled honestly** — the zero-volume / NaN / last-price-forward-fill candle taxonomy in
> MDPS
>
> - downstream consuming it correctly (batch AND live), ⑤ **read+write paths match the post-migration shape
>   everywhere.** A full IS→MTDS→MDPS→features→strategy→execution audit (2026-06-04) ran each layer against the
>   canonical `day=/pipeline_mode=batch_*/asset_group=cefi/venue=/instrument_type=/data_type=/` SSOT
>   (`build_cefi_partition_path` / `candidate_parquet_paths` / `resolve_bucket_name`). **VERDICT: NOT-YET-READY — 2×P0 +
>   2×P1 migration-blocking gaps.**

> **🔬 RE-VERIFICATION GATE STATUS (slot-3 + sub-agents, 2026-06-04) — the 2026-06-04 P0/P1 gaps are now ALL GREEN; the
> CODE side of the run-readiness bar is MET.** Re-audited each of the operator's 7 dimensions against the actual code on
> LDR:
>
> - **① migrator dry-run** — DONE (`mtds-migrate-cefi-v9dry-2024`, exit 0; see Phase 2). **② manifest-rebuild dry-run**
>   — DONE (caught + fixed the 1187→12 false-phantom bug; see E5 dry-run §).
> - **③ pre-flight engrained IS→execution (4-state)** — GREEN. execution-service `resolve_manifest_capture_status()`
>   gates `checker._gcs_lookup_and_check` (4-state, fail-open); strategy gates on features 4-state +
>   `instrument_existence_guard`; features `volatility/core/data_loader.py` 4-state; MTDS capture pre-flight
>   `_skip_states`. The two P0s (MTDS live-writer path divergence `318473eb`, execution legacy raw_tick paths
>   `6230c18d0`)
>   - both P1s (execution 4-state checker `6230c18d0`, strategy features-bucket fix `879d1bbd`) are SHIPPED + flipped
>     above.
> - **④ empty/partial honest + downstream** — GREEN. MDPS `_finalize_session_grid` zero-volume/LOCF/NaN taxonomy is the
>   SSOT; features consumes it with typed `record_empty` (no `fillna(0)`); reader empty-vs-failed differentiation
>   handled one layer up at the pre-flight consumer (confirmed not-a-gap).
> - **⑤ read+write paths match post-migration shape everywhere** — GREEN, re-verified 5/5 (sub-agent 2026-06-04): MTDS
>   batch + live writers, MTDS reader 3-level fallback (canonical first), execution `canonical_paths.py`, features
>   `perp_funding_rates.py`, strategy `batch_handler`/`instrument_existence_guard` all route the UAC SSOT and insert
>   `pipeline_mode=` LEFT of `asset_group=cefi`. NB a sub-agent flagged a "UAC SSOT regression" (cefi paths lack
>   `pipeline_mode=`) — **FALSE ALARM**: `build_cefi_partition_path` (partition_paths.py:274/309) and
>   `candidate_parquet_paths` (:397/450-459) both natively accept + insert `pipeline_mode=`; the agent only read the
>   module-docstring back-compat (omitted) form. No fix needed.
> - **⑥ IS/UAC guardrails** — re-verified PARTIAL→effectively GREEN: the residual holes (date-blind MTDS fallback,
>   strategy IS-existence check, swallowed Deribit live guard, permissive unknown-venue) are all flipped DONE above.
> - **⑦ could-exist denominators** — STRONG: `expected_unattempted` run for cefi (4.1M rows); denominator includes it;
>   UI shows it distinctly. Residual = the proper-catalogue cron (SUPERSEDED into
>   `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`) + per-date precision (tracked P3).
> - **CF-11 (IS + MTDS)** — **CLOSED both sides** (this re-audit): all 4 cefi IS adapters now re-raise on genuine fetch
>   failure → `attempted_failed` (`e2e008f0`+`f2ca5954`); MTDS already compliant. Flipped above.
> - **Batch=Live source provenance** — re-verified the cefi `source="tardis"` WRITE-path is live on BOTH paths: UAC
>   `SOURCE_PRIORITY` registers `("cefi", <data_type>) → ["tardis"]` (source_priority.py:152-160), so the MTDS raw-tick
>   writer (`get_primary_source`, mtds@4e5fa57f) AND the MDPS candle writer (`_resolve_primary_source_for_candle`) both
>   auto-derive + stamp `source="tardis"`. (The historical-corpus source backfill rides the C-source RIDER in the
>   migration walk — next session.) **Stale-comment finding tracked below.**
>
> **CONCLUSION:** the CODE half of the run-readiness bar is MET — remaining work is the irreversible GCS execution
> (migrate `--apply` gap-fill, orphan sweep, E5 rebuild, E7 verify, E8 legacy delete) + historical
> source/`expected_unattempted` backfills, all deliberately NEXT-session per the handoff. No new migration-blocking CODE
> gap found.
>
> **🔁 INDEPENDENT CODE RE-VERIFICATION (slot-3 interactive + 5 Explore sub-agents, 2026-06-04 — did NOT trust the prior
> "GREEN" prose; re-read the actual code on LDR per claim).** Confirmed TRUE on LDR: execution `canonical_paths.py`
> (`build_candidate_raw_tick_paths` canonical-first + `resolve_manifest_capture_status` 4-state fail-open) wired into
> all 5 raw-read sites + `l2_depth_provider` cloud-agnostic + factory/validators raise per-date; MTDS live-writer
> `build_cefi_partition_path` + `pipeline_mode=live_websocket` LEFT of `asset_group` (byte-parity with batch), reader
> canonical-first 3-level fallback + manifest pipeline_mode lift, `rebuild_cefi_manifest`
> `reemit_cefi_honest_absence_rows` CF-11 classifier + false-phantom fixes (slash-symbol stem / itype-case / drop-junk),
> live finalize stamps `source`+`pipeline_mode`, migrator parallel+idempotent; features cefi UAC reads + honest-null +
> `LookbackValidator` candle-only filter; strategy `instrument_existence_guard` + `features-delta-one` bucket fix;
> deployment-api live-IS cefi denominator (`cap=None`, fail-open returns None) + 4-state denom incl
> `expected_unattempted` + per-source `groupby("source")`; deployment-ui distinct `expected_unattempted` segments +
> smoke spec; IS 4 cefi adapters re-raise→`attempted_failed` (+regression test); UAC `validate_data_type_for_venue`
> `strict=` fail-closed + `SOURCE_PRIORITY[("cefi",*)]→tardis` + `get_expected_data_types_for_venue`. **One wording
> correction (not a gap):** the Deribit not-found guard manifests as a REJECTED `ExecutionResult` (order never placed),
> not an uncaught raise — plan item reworded above; guardrail property holds. **Follow-up sweep 2026-06-05 (operator
> ask):** MDPS stale source-gap comment **FIXED** (mdps@6188588); strategy `gcs_feature_provider` unbounded-ffill
> staleness cap **FIXED** (strategy@d97e89aa, +4 tests); deployment-api FLAG-3 **RE-SCOPED** — not a mechanical swap
> (the `pipeline_uat.py` `# CORRECT-LOCAL` reads are non-AG pipeline-health buckets, not AG-scoped market-data stores; a
> blind `resolve_bucket_name` swap would break them → downstream-owner UAT-model decision, see item below); funding
> name/unit mismatch remains COUPLED to `data_pipeline_acquisition_remediation` funding_oi registration (fix rides that
> plan — moot until the registry spec lands). Cross-cutting: QG-sentinel gitignore rolled out fleet-wide
> (`cicd_contract_hardening` item H) — canonical template + 8 repos, killing the dirty-pull churn.

**🟢 RE-AUDIT FINDINGS (slot-3 2026-06-04) — tracked so the cefi master orchestrator owns them:**

- [x] ✅ [CODE] P3. **MDPS stale source-gap comment — FIXED (mdps@6188588, QG exit 0 172s, PR #94→staging).**
      `canonical_writer.py:1304-1315` previously said "cefi/defi/tradfi are RED gaps per the 2026-06-01 plan" for
      `source=`. Refreshed to the verified reality: WIRED today = tradfi (databento/massive), prediction
      (polymarket\__), cefi (tardis —
      `SOURCE_PRIORITY[("cefi",_)]→tardis`, so `\_resolve_primary_source_for_candle`stamps every cefi     candle), and sports/odds_horizon_bucket (mdps_odds_horizon_bucket); RED gap remaining = defi. Doc-comment only; no     logic change (the`try/except
      KeyError → None` fallback is unchanged). Provenance: cefi run-readiness re-audit 2026-06-04.
- [x] ✅ [CODE-BUG] P1. **CeFi funding-feature producer/consumer name+unit mismatch — RESOLVED IN CODE (slot-3 verify
      2026-06-08).** The described mismatch no longer exists: producer
      `features-service/.../delta_one/app/calculators/funding_oi.py:84` emits `funding_rate_annualised_bps` (bps,
      `df["funding_rate"] * 3 * 365 * 1e4`) and consumer
      `strategy-service/.../engine/strategies/v2/carry_and_yield/basis_perp.py:67` reads
      `features.get("funding_rate_annualised_bps")` — **names + units MATCH**. Grep-verified: NO
      `funding_rate_annualized` (US-spelling/fraction) anywhere in features-service/strategy-service source (only
      legacy-handling refs in the `trace_all_carry_archetypes.py` diagnostic script). Pinning regression test EXISTS:
      `features-service/tests/delta_one/unit/test_feature_groups/test_funding_oi.py::test_funding_rate_annualised_bps_key_and_unit`
      asserts both the consumed key is present AND the old US key is absent + the bps conversion. **Remaining = NOT this
      CODE-BUG**: the registry `funding_oi` group is still a `need_data`/`_placeholder` spec (feature not yet
      produced-to-GCS) — that registration is the owning plan's (`data_pipeline_acquisition_remediation_2026_06_03.md`)
      Phase-4 DATA work, decoupled from the name/unit contract which is now correct + test-guarded. Provenance: cefi
      run-readiness re-audit 2026-06-04 + slot-3 verify 2026-06-08.

**✅ READY (verified this audit — do not re-litigate):**

- **IS** — reference-store writes go through `resolve_bucket_name`/`get_write_bucket_name` + canonical prefixes
  (`catalogue_builder.py:185`, `orchestrator.py:1859`); manifest `record_*` pass explicit `pipeline_mode=`;
  skip-existing pre-flight (`instruments_handler.py:64`). IS writes its OWN `instruments-store-*`, not `raw_tick_data`,
  so the pipeline_mode raw-tick rule doesn't bind it. PATH-PARITY MATCH.
- **MTDS batch** — cefi batch writer routes `build_cefi_partition_path` + inserts `pipeline_mode=` LEFT of
  `asset_group=` (`engine/orchestrator.py:930-1005`); reader 3-level fallback probes canonical FIRST
  (`reader.py:281-295`); capture pre-flight `_skip_states={CAPTURED,EMPTY_CONFIRMED}`, retries `attempted_failed`,
  bait-sentinel guard (`orchestrator.py:2201-2228`). Migration-safe.
- **MDPS candle-absence taxonomy is HONEST** — `base_adapter._finalize_session_grid` produces a dense session grid:
  no-trade bin in a live session → **forward-filled `o=h=l=c=prev_close`, `volume=0`** (zero-volume + last-price), state
  streams zero-fill flow cols (never NaN), pre-first-obs bins → NaN (honest), fully-empty shard → `record_empty` (the
  banned 1440-NaN-placeholder shape was removed, mtds@d717c59 / per-tf `record_empty_for_shard`). All 5 core cefi
  adapters (trades/book_snapshot/derivative/futures_chain/options_chain) route the session grid. Aggregator
  (`fast_candle_aggregation.py:304`) NaN-guards the rollup. Read+write canonical.
- **features-service** — cefi reads via `candidate_parquet_paths("cefi",…)` + `resolve_bucket_name`
  (`cefi/calculators/perp_funding_rates.py:115`), honest null handling (no `fillna(0)`; emits typed
  `record_empty(EXPECTED_NO_FUNDING_RATE_TICKS)`), 4-state pre-flight (`volatility/core/data_loader.py:43`). This repo
  is the **reference exemplar** — bring strategy + execution cefi reads to parity with it. PATH MATCH / PRE-FLIGHT
  PRESENT / CANDLE SAFE.

**🔴 P0 — migration-BLOCKING (must be DONE + ticked before the real run):**

- [x] ✅ [CODE] P0. **MTDS live cefi writer path divergence — FIXED (mtds@318473eb).** `live_tick_blob_path`
      (websocket_runner.py) now routes cefi through the SAME UAC `build_cefi_partition_path` the batch writer uses
      (byte-identical) with `pipeline_mode=live_websocket` LEFT of `asset_group=`, venue UPPER +
      instrument_type/data_type lower (reader case-parity); `instrument_type=` threaded from the flush call site (was
      discarded); defi/other mirror the reader's generic order (chain before venue). +regression tests asserting
      reader-order + case parity. **MDPS lockstep `default_tick_blob_path` fixed the same way (mdps@b9b3263, QG exit
      0).** MTDS QG exit 0. (Also shipped: P2 `reader.read_from_manifest` lifts pipeline_mode from the captured row —
      canonical path probed first.)
- [x] ✅ [CODE] P0. **execution-service legacy raw_tick paths → UAC SSOT — FIXED (execution@6230c18d0).** Was: ALL raw
      candle/mark/orderbook reads hardcode `raw_tick_data/by_date/day={date}/data_type={dt}` with NO
      `pipeline_mode=`/`asset_group=cefi/` (`data/loaders/base.py:182`, `data/checker.py:155,323`,
      `data/loader_transforms.py:150`, `data/loaders/defi.py:41,77`, `data/loader_local.py:62`,
      `l2_depth_provider.py:34` `_L2_ORDERBOOK_PATH_TEMPLATE`). Relies ENTIRELY on the reader-fallback that Phase 8
      removes (~2026-06-15) ⇒ cefi backtest + live mark reads silently return EMPTY after cutover. **Fix:** route every
      raw read through `candidate_parquet_paths()` (pipeline_mode-aware first, legacy fallback) — mirror
      features-service `perp_funding_rates.py`. **DONE:** new `data/canonical_paths.py` SSOT
      (`build_candidate_raw_tick_paths` canonical-first + legacy fallback, probe both → works pre/post-migration) wired
      into loader_base/loaders.base/ loader_transforms/loader_local/l2_depth_provider; signatures unchanged; +18 tests;
      basedpyright 0; QG exit 0.
- [ ] [CODE] P1. **execution-service — `data/loaders/defi.py:41,77` DeFi raw-tick reads still legacy (slot-2/defi
      owner).** The shared `candidate_parquet_paths` DeFi branch needs a `chain` kwarg
      (`build_defi_partition_path(venue, chain, …)`) + a defi instrument-id→chain mapping that the cefi-scoped fix did
      not supply (calling it as-is raises `KeyError("chain")`). `loader.py` `load_swaps`/`_build_swaps_paths` DeFi paths
      likewise unchanged. Mirror the cefi `canonical_paths.build_candidate_raw_tick_paths` pattern with the defi chain
      axis. Target repo: execution-service (DeFi slice). Provenance: cefi E2E audit 2026-06-04 (the cefi P0 above is
      GREEN; this is the defi sibling).

**🟡 P1 — pre-flight engrained (blocking the "pre-flight on every service" bar):**

- [x] ✅ [CODE] P1. **strategy-service cefi pre-flight — DIAGNOSED over-flagged; the REAL gap was P2 (FIXED).**
      Grep-then-read correction: `service_entry.py:648`'s `market-data-tick-cefi` is the **GAP-5 consolidator-HEALTH
      startup gate** (`assert_consolidator_healthy`), NOT a raw-tick data read — strategy consumes **features**
      (features-delta-one, already in `UPSTREAM_DEPS` + 4-state-gated via `check_allocation_manifest`), not raw cefi
      ticks. So no raw-tick `UPSTREAM_DEPS` entry is warranted (a `required` one would be wrong). Strategy's cefi
      pre-flight already exists (consolidator-health + features 4-state). The actual cefi gap was the allocation guard
      hitting the WRONG features bucket — see P2 (now P0-level), **FIXED**.
- [x] ✅ [CODE] P1. **execution-service manifest 4-state pre-flight — ADDED (execution@6230c18d0).** Was:
      `data/checker.py` (`check_gcs_file_exists` / `check_data_availability` / `blob_exists` `:168,214,335`) is a raw
      path-EXISTENCE probe — never reads `availability_index` / `capture_status`, so it cannot tell zero-volume /
      `empty_confirmed` / `attempted_failed` from genuinely-missing. **DONE:**
      `canonical_paths.resolve_manifest_capture_status()` (4-state, fail-open) gates `checker._gcs_lookup_and_check` —
      empty_confirmed→honest-absence skip, attempted_failed→skip+alert, captured/unknown→proceed.

**⚪ P2/P3 — correctness hardening (not run-blocking but in-scope for "engrained"):**

- [x] ✅ [CODE] P1(↑from P2). **strategy-service allocation guard hit the WRONG features bucket for cefi — FIXED.**
      `cli/handlers/batch_handler.py:_check_manifest_for_category` (called per-category incl. cefi at :480) hardcoded
      `kind="features-sports"` for EVERY category. cefi features live in `features-delta-one` (cloud-providers.yaml:67
      `features-delta-one-cefi-${GCP_PROJECT_ID}`); `features-sports` is the sports-only flat key. ⇒ a cefi allocation
      cycle resolved a sports bucket, found no availability index, and **FAILED OPEN** (`capture_status="unknown"` →
      proceed) — the 4-state allocation gate was a silent **no-op for cefi**. **FIXED:**
      `features_kind = "features-sports"     if asset_group=="sports" else "features-delta-one"` (sports behaviour
      unchanged; cefi/defi/tradfi/prediction now gate on their REAL features index). This was the real "strategy cefi
      pre-flight" gap (P1 above was the red herring). **DONE — strategy@879d1bbd, QG exit 0** (+ regression test).
- [x] ✅ [CODE] P2. **market-tick-data-service** — `reader.read_from_manifest` (`reader.py`) now LIFTS `pipeline_mode`
      from the captured manifest row into `read_shard` so the canonical `pipeline_mode=` path is probed FIRST (caller
      override still wins). +2 regression tests. Was leaving manifest-driven reads on the soon-removed bare fallback.
      **DONE — mtds (shipping with the P0 live-writer fix).**
- [x] ✅ [CODE] P2. **execution-service** — `l2_depth_provider.py` `from google.cloud import storage` / `gcs.Client()` →
      `get_storage_client()` (cloud-agnostic). **DONE — execution@6230c18d0.**
- [ ] [DATA] P3. **market-data-processing-service** — leading-NaN before first observation for state adapters that skip
      the session-grid finalize (already tracked: `issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`). Confirm
      all cefi adapters route `_finalize_session_grid`; liquidations (no grid) is intentional event-counts — verify.
- [x] ✅ [CODE] P3. **strategy-service — `gcs_feature_provider` unbounded ffill staleness cap FIXED (strategy@d97e89aa,
      QG exit 0 195s, PR #70→staging).** `get_merged_features` outer-joins carry feature groups of different sampling
      frequencies then forward-filled with an UNBOUNDED `merged.ffill()` → a dead/stale upstream feed could silently
      propagate a stale value into a live carry signal forever. **Fix:** new
      `_ffill_with_staleness_cap(df, max_staleness)` (time-based, all-pandas) nulls any forward-filled cell carried
      longer than `max_ffill_staleness` (configurable per-call; default `pd.Timedelta(days=3)` — generously bridges
      daily/funding features + backfill hiccups, bounds a dead feed; `None` = legacy unbounded). The strategy then sees
      an honest gap, not a stale number; a warning logs when masking occurs. +4 regression tests (within-cap preserved /
      fresh-obs resets clock / None disables / non-time index falls back); basedpyright 0. **execution-service**
      `benchmark_service.py` stale `gs://` comment refreshed ✅ (execution@6230c18d0).

### 🔎 DIMENSION 6 + 7 AUDIT (IS/UAC instrument guardrails + could-exist denominators, 2026-06-04, slot-3 + sub-agents)

> Operator extended the readiness bar: **⑥** code must GUARDRAIL against using instruments / fixtures /
> (venue×instrument_type×data_type) combos that **cannot exist** per IS+UAC; **⑦** deployment-api/ui coverage must use
> the **universe of what COULD exist** (IS instruments × UAC valid combos × upstream availability) as the DENOMINATOR,
> with the manifest marking could-exist-but-not-yet-backfilled cells as `expected_unattempted` (not invisible / no row).

**✅ VERIFIED (Dim 6 — IS/UAC guardrails, mostly in place):**

- MTDS cefi capture resolves its universe + venue URLs FROM IS, per date: `engine/cefi_catalog_reader.py:62-236`
  (`CeFiCatalogReader.list_instruments` filters status/availability-window per processing-date), wired at
  `orchestrator.py:2148`/`:3436`; `list_not_yet_listed()` emits `EXPECTED_INSTRUMENT_NOT_LISTED`. Per-date existence
  gate `_check_instruments_available` (`orchestrator.py:285`).
- UAC combo guardrail BEFORE fetch: `orchestrator.py:2342-2364` intersects requested data_types with
  `get_expected_data_types_for_venue(venue)` (UAC `market_data_categories.py:440-492`) — drops venue-unsupported types.
- execution-service batch preflight RAISES on missing cefi instrument: `instruments/factory.py:197-236`
  (`INSTRUMENT_NOT_FOUND`, cefi has no config fallback), `engine/validation/{instrument,catalog}_validator.py` read
  `instrument_availability/by_date/day={date}/` per date. Date-correct (no cross-date instrument reuse found).

**✅ VERIFIED (Dim 7 — could-exist denominators, machinery EXISTS + RUN for cefi):**

- `expected_unattempted` universe emission is cefi-wired + has RUN:
  `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_v2_cefi()` cross-joins IS catalog × dates ×
  `DATA_TYPES_BY_ASSET_GROUP["cefi"]`, diffs vs existing rows, emits `expected_unattempted` for alive-but-absent cells
  (lifecycle reasons EXPECTED_INSTRUMENT_NOT_LISTED/\_DELISTED/ \_PRE_VENUE_LAUNCH). Live cefi `_index` ≈ 11.7% (4.1M
  rows) expected_unattempted — the not-backfilled gap is MATERIALISED as rows, not invisible. UTL
  `manifest_writer.py:2115` `record_expected_unattempted()`.
- Denominator is universe-aware: UAC `honest_coverage.py:575` `compute_honest_coverage()` denom =
  captured+empty_confirmed+known_empty+attempted_failed+**expected_unattempted_pending_fetch** (the could-exist gap is
  IN the denominator). deployment-api `data_status_service.py:25` imports it. UI shows it DISTINCTLY:
  `deployment-ui HonestCoverageCard.tsx:52` + `VenueCoverageTable.tsx` render `expected_unattempted` as its own segment
  (playwright `tests/smoke/venue_year_coverage.spec.ts` mocks cefi).

**🟡 GAPS — Dim 6 (guardrail holes):**

- [x] ✅ [CODE] P2. **MTDS hardcoded date-BLIND fallback universe — FIXED (mtds@ae5f56b0, QG exit 0).** Was bypassing
      IS: `engine/orchestrator.py:326-439` `_VENUE_WIRE_SYMBOL_FALLBACK` (static MVP majors per venue) is substituted by
      `_uac_seed_instruments_for_venue` (`:411`) when `_check_instruments_available(venue,date)` is False
      (`:2316-2326`). Bounded to majors + logged + honest-skip when empty (so practical "cannot-exist" risk is low —
      majors exist every operational date), BUT it is date-BLIND (ignores venue-launch/delist per date) + bypasses the
      IS SSOT. **Fix:** gate the fallback behind a batch-bootstrap-only flag (never the live path); in normal operation,
      when IS is missing → honest-skip / `record_failed(EXPECTED_*)` rather than substitute a hardcoded universe.
- [x] ✅ [SCRIPT] P2. **unified-trading-pm QG blind spot — FIXED (pm@c04f7760b + mtds@f2c6ada0).** Was: the QG scanned
      only `cli/handlers/`, so the `engine/`-resident `_VENUE_WIRE_SYMBOL_FALLBACK` dict was INVISIBLE to the gate.
      **DONE:** `no_hardcoded_venue_universe.sh` now scans BOTH `cli/handlers/` AND `engine/`, adds the
      `_WIRE_SYMBOL_FALLBACK` / `_VENUE_*_FALLBACK` patterns, and an inline
      `# qg-allow: venue-universe-fallback <reason>` allowlist for a deliberately-gated fallback. Verified: the extended
      scan flags the unmarked dict (exit 1) and passes once marked. mtds@f2c6ada0 carries the sanction marker on
      `_VENUE_WIRE_SYMBOL_FALLBACK` (gated behind `MTDS_ALLOW_HARDCODED_UNIVERSE_FALLBACK`); any NEW unmarked
      hardcoded-universe dict in engine/ now fails the gate.
- [x] ✅ [CODE] P2. **strategy-service — IS instrument-existence guardrail ADDED (strategy@fdb86a54, QG exit 0).** Was:
      `preflight.py` (venue auth+balance only) + `risk_preflight_gate.py` (risk rules only) never validated a cefi
      instrument EXISTS in IS for the date before emitting an instruction → a config naming a delisted/non-existent cefi
      instrument was only caught at execution. **DONE:** new `engine/core/instrument_existence_guard.py`
      (`validate_cefi_instruments_exist`) reads the per-date per-venue IS availability universe
      (`instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet` via `resolve_bucket_name`) and,
      mirroring execution's `catalog_validator`: `fail_on_missing=True` → `DependencyError` on a confirmed-absent id;
      `False` → drops absent ids + emits `PREFLIGHT_SKIPPED`; transient IS read error → fails OPEN (never hard-blocks
      live, GAP-5 style). Wired into `batch_handler.handle()` for cefi runs before `_execute_backtests` (gated on
      `fail_on_missing_deps` + `not skip_dependency_check`). +5 unit tests; basedpyright 0.
- [x] ✅ [CODE] P3. **execution-service — Deribit live-order not-found guard FIXED (execution@f111a8e2c, QG exit 0).**
      Was SWALLOWED: `_validate_instrument_before_order`'s instrument-fetch `except` previously caught
      `(OSError, ValueError, RuntimeError)` → only `logger.warning` → the not-found `ValueError` was eaten at the
      validation site and the order proceeded. **Fix (verified on LDR, slot-3 re-audit 2026-06-04):** the inner except
      is now narrowed to `(OSError, RuntimeError)` (`deribit_orders.py:80`) so the CONFIRMED not-found `ValueError`
      (`:99`) propagates out of validation; at the `submit_order` boundary the outer
      `except (OSError, ValueError, RuntimeError)` (`:296`) converts it to a **REJECTED `ExecutionResult`** via
      `_make_rejected_result` — the raise fires at `:261`, BEFORE the HTTP submit at `:286`, so **no live order is ever
      placed** against an instrument the venue has no live definition for. (Manifests as a rejection, not an uncaught
      raise — the guardrail property holds; this is the more graceful per-order outcome, consistent with how other order
      failures are surfaced. Validates against the venue live-definition set, not IS — the IS-existence guard is
      strategy-side, shipped above.)
- [x] ✅ [CODE] P3. **unified-api-contracts — `validate_data_type_for_venue` unknown-venue fail-closed — FIXED
      (uac@7f31f342, QG exit 0, 298s).** Added opt-in `strict=` param: default stays permissive/advisory (back-compat
      for warn-only callers); the live CAPTURE path passes `strict=True` → returns False (fail-CLOSED) for an
      unknown/typo'd venue (no valid set), so a venue UAC does not recognise cannot have a valid (venue × data_type)
      combo and is never attempted / phantom-written. +2 unit tests (`test_validate_data_type_for_venue_strict.py`).
      mtds@ae5f56b0 already consumes the strict= param on capture — UAC landing keeps the workspace consistent.

**🟡 GAPS — Dim 7 (denominator precision):**

- [x] ✅ [CODE] P2. **deployment-api in-process per-instrument denominator now uses the live IS universe — FIXED
      (deployment-api@d55bcb6, QG exit 0, 407s).** Was: `_per_instrument_coverage` sized the cefi per-(instrument,date)
      denominator from UAC's capped MVP seed (21 spot / 10 perp) → under-counted the real ~200-perp cefi universe →
      optimistic coverage. **DONE:** new `_build_cefi_is_instruments_provider(cloud)` reads the live IS cefi
      availability index (`instruments-store-cefi` via `resolve_bucket_name` + `read_availability_index` →
      `{venue: [instrument_id]}`) ONCE per CEFI category call and injects it into `get_expected_instruments_for_venue`
      with `cap=None` (no MVP truncation); other asset*groups unchanged (provider=None, cap=50). **Fail-open done
      RIGHT:** catalog unreadable/empty → builder returns `None` (NOT a `lambda: None` provider) so the caller injects
      no provider and UAC uses its MVP seed — a non-None provider that \_returns* None would yield an EMPTY universe
      (denominator→0); caught this exact bug in review (it had broken `test_cefi_per_venue_denominator_honest` +
      `test_category_completion_not_tautology`) and fixed it. +6 unit tests; basedpyright 0. NB: uses the IS
      availability index (the IS-published instrument_id universe) — same underlying IS data the v2 enumerator's catalog
      derives from, without replicating its catalog loader.
- [ ] [INFRA] P3. **`expected_unattempted` is enumerator-run-dependent (not auto per-write) — BLOCKED-OPERATOR-DECISION
      on a missing prerequisite (slot-3 2026-06-04).** A not-yet-backfilled cefi cell is invisible until the v2
      enumerator VM runs (`launch-expected-universe-v2-vm.sh cefi --apply-write`; cadence "one-shot then quarterly").
      cefi is currently seeded (4.1M rows) but NEW venues/instruments between runs are invisible
      (`honest_coverage.py:623` warns a fresh AG reads a misleading 100%). **Why a naive recurring cron is NOT
      shippable:** the v2 enumerator REQUIRES `--catalog-path` = a pre-built IS catalog parquet
      (`gs://instruments-store-cefi-{env_short}-{project}/{env}/catalog.parquet`; the launcher defaults to it,
      `enumerate_expected_universe.py:1410` hard-fails `missing_catalog_path` without it). **NO automated/recurring
      producer of that `catalog.parquet` exists** (workspace grep 2026-06-04: only the launcher + its test reference the
      path; nothing writes it) — it is operator-supplied. So a recurring enumerator scheduler would read a stale/absent
      catalog (fire-and-forget failure, banned). A correct fix needs a PREREQUISITE: either (a) add a recurring
      catalog-build step that writes `{env}/catalog.parquet` from the IS store, or (b) refactor the v2 enumerator to
      build its catalog from the IS availability index at runtime (the exact `read_availability_index`→`{venue:[ids]}`
      pattern deployment-api now uses in `_build_cefi_is_instruments_provider`, eliminating the `--catalog-path`
      dependency). A drafted `expected_universe_cefi_scheduler.tf` (Cloud Run Job + weekly Scheduler, env-tiered buckets
      per `manifest_consolidator_scheduler.tf`) was NOT committed pending this decision. **RESOLVED 2026-06-04 →
      SUPERSEDED-BY `plans/active/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`** (operator decision: the
      real fix is a proper, self-refreshing instrument catalogue rolled up from the per-date `by_date/` definitions —
      foundation-level, all asset groups, gates the MTDS migration `--apply`). This cefi cron becomes a thin wrapper
      once that plan's Phase 3 lands; tracked there, no longer a cefi-solo item.
- [ ] [CODE] P3. **deployment-api per-date denominator refinement (separate follow-up, NOT migration-blocking).** The
      cefi coverage denominator (deployment-api@d55bcb6) reads ONE current IS availability snapshot
      (`read_availability_index`), not the per-date `instrument_availability/by_date/` definitions — so it is the
      latest-known universe, NOT per-date point-in-time-correct (the universe as-of each historical date). Acceptable
      for a coverage denominator (and a big improvement over the 21/10 MVP seed), but if data-status should be
      time-sliced per historical date, switch the provider to read the per-date `by_date/` definitions. Repo:
      deployment-api. Depends on the proper catalogue plan above for the per-date source contract.

**VERDICT:** ⑥ **PARTIAL** — IS-derived per-date capture + UAC combo gate + execution preflight are real + date-correct;
the residual holes (date-blind MTDS fallback un-caught by its QG, no strategy IS-existence check, swallowed Deribit live
guard, permissive unknown-venue) are tracked above. ⑦ **STRONG** — the could-exist universe drives
`expected_unattempted` (run for cefi, 4.1M rows) + the canonical denominator includes it + the UI shows it distinctly;
residual is the in-process MVP-seed denominator under-count + the enumerator cadence (both tracked).

**UAC/UTL helpers (the absence "explainer"):** `build_cefi_partition_path` / `candidate_parquet_paths`
(`canonical/partition_paths.py:392`) are the path SSOT; the `empty_confirmed` closed-set taxonomy lives in
`canonical/crosscutting/honest_coverage.py` (the `EXPECTED_NO_*` / `SOURCE_RETURNED_ZERO` reasons features uses). The
candle-level zero-volume/LOCF/NaN contract is documented in MDPS `base_adapter.py:36-624` (`_finalize_session_grid`) —
**this MDPS docstring is the de-facto SSOT for the candle-absence semantics; the P0/P1 downstream fixes must consume it
(distinguish volume=0 vs NaN vs forward-filled), not re-derive.**

**✅ GREEN (verified consistent — do not touch):**

- **Path correctness**: migration, live+batch writers, MTDS reader, features reader, `rebuild_cefi_manifest.py` ALL go
  through the UAC `candidate_parquet_paths()` SSOT and insert `pipeline_mode=` left of `asset_group=cefi`;
  reader-fallback probes both shapes until ~06-15 (PREP3 writer pipeline_mode= PRIMARY landed mtds@f50116ca). The path
  the migration reads/writes == the writers'/readers'/preflight's path.
- **Data-status infra**: deployment-api reads canonical `market-data-tick-cefi-prd` via `resolve_bucket_name`, uses UTL
  `read_availability_index` (v9 columns), renders 4-state status, derives drilldown axis order from the UAC registry.

**🔴 P0 — E2E-blocking code (OPERATOR-APPROVED to do THIS session before the dry-run):**

- [x] ✅ [CODE] P0. **`rebuild_cefi_manifest.py` CF-11 3-way classifier** — **DONE (mtds@fa2b02c7).** New
      `reemit_cefi_honest_absence_rows` pass (mirrors the proven `rebuild_tradfi_manifest` sibling): reads the prior
      `_index`, filters to the run date-range + cefi, dedups vs freshly-scanned keys, then (a) within-bounds empty
      (blank-reason OR `SOURCE_RETURNED_ZERO` on a guaranteed-when-listed `trades`/`ohlcv*`/`book_snapshot_5` OR
      invalid-reason) → `record_failed(WITHIN_BOUNDS_EMPTY_RECLASSIFIED)`; typed-empty on a sparse data_type
      (funding/options_chain/…) → `record_empty` PRESERVED; (b) prior `attempted_failed` → `record_failed` PRESERVED
      (the ~1.33M survive); phantom captured-no-object → `record_failed(PHANTOM_CAPTURED_NO_OBJECT)`; (c) +24 unit
      tests; `--scan-only` flag restores pure-scan. MTDS QG --no-fix exit 0. Closes the open E5/CF-11 items at §CF-11
      below.
- [x] ✅ [CODE] P0. **Live cefi writer source+pipeline_mode COLUMN parity** — **CONFIRMED gap + FIXED (mtds@4e5fa57f).**
      orchestrator.py finalize per-instrument `add()` stamped source/pipeline_mode ONLY for sports odds (comment:
      "Non-sports shards leave source=None"); cefi/defi/prediction captured rows got blank `pipeline_mode` (`add()`
      doesn't auto-derive it) → Batch≠Live drift. Now every non-sports per-instrument row derives `source` via
      `get_primary_source(asset_group,data_type)` + `pipeline_mode` via `_resolve_pipeline_mode_for_sentinel` (same
      helpers the bundled path + migrator/rebuild use) + stamps both. Sports branch unchanged (no slot-4 collision; the
      `else` branch is additive). source= is crosscutting (all asset_groups). MTDS QG --no-fix exit 0.

**🟡 P1 — data-status / drilldown reflects the migrated structure (DEFERRED to a tracked follow-up unless quick):**

- [ ] [CODE] P1. **deployment-api FLAG-1** — CeFi multi-source UNION coverage + per-source breakdown (dedup via
      `select_primary_available_source`; `groupby("source")` on the `_index` source column). CeFi single-source today,
      but the column/dedup path must exist for swap-resilience. Cross-ref
      `downstream_services_manifest_canonicalisation_2026_06_01.md` FLAG-1.
- [ ] [CODE] P1. **deployment-api FLAG-3 — RE-SCOPED (slot-3 evaluation 2026-06-05): NOT a mechanical
      f-string→`resolve_bucket_name` swap; a blind swap would BREAK working code.** The `commentary/pipeline_uat.py`
      reads (`instruments-store-{pid}/instruments/latest/manifest.json`, `features-store-{pid}/health/latest.json`,
      `ml-store-{pid}/training/latest/metrics.json`, `execution-store-{pid}/t1_recon/latest/summary.json`) are NON-AG
      **pipeline-health summary** buckets carrying `# CORRECT-LOCAL` markers (a deliberate QG STEP-5.69 allowlist), NOT
      the AG-scoped market-data stores. The canonical `resolve_bucket_name(kind="instruments-store", asset_group=…)`
      everywhere else resolves a PER-AG bucket (`instruments-store-cefi-…`) with a different path shape — there is no
      single non-AG `instruments-store-{pid}` in that registry, so swapping these would point the health reads at
      wrong/nonexistent buckets (they already `try/except`→None-degrade gracefully today). REMAINING for the
      deployment-api/downstream owner: decide the UAT health-summary bucket MODEL (keep the `# CORRECT-LOCAL` aggregate
      form, or migrate the health summaries into per-AG/env-tiered buckets) — a model decision, not a slot-3 mechanical
      edit. `deployment_api_config.py` store buckets already use typed `effective_*` config (FLAG-3-compliant).
      Cross-ref downstream plan FLAG-3.
- [ ] [CODE] P1. **deployment-api CeFi pipeline_mode dedup + drilldown filter** (deployment-api; downstream owner).
      **CONFIRMED read-only (slot-3 2026-06-03):** the dedup MECHANISM exists + is AG-agnostic — the count is
      `len(captured_df.drop_duplicates(subset=_shard_atom_cols))` and `_shard_atom_cols` derives from the UAC
      `SHARD_AXIS_MATRIX`, which for cefi is `(venue, data_type, instrument_type, instrument_id, day)` — pipeline_mode
      is NOT a cefi shard-atom axis, so multiple `pipeline_mode=` rows for one cell collapse to ONE shard (no
      double-count). The existing `test_pipeline_mode_rows_do_not_double_count_shards` guards the DeFi
      **chain**-breakdown builder; REMAINING for the deployment-api/`downstream_services_manifest_canonicalisation`
      owner: (a) a **cefi parity test** (venue-breakdown builder) as a regression guard, (b) the `pipeline_mode`
      drilldown **filter param** (a feature-add; UI label is playwright-gated). NOT a cefi-correctness gap today (dedup
      works); a regression-guard + feature enhancement for the deployment-api owner. (In practice cefi double-count is
      also unlikely — a cefi cell carries ONE pipeline_mode per day, batch OR live, not both.)

**⚪ P2 / needs-confirm (tracked):**

- [ ] [CODE] P2. **MDPS GAP-7** — `category`→`asset_group` param rename in `dependency_checker` (vocabulary; cross-ref
      downstream plan GAP-7).
- [ ] [DATA] P2. **CONFIRM partial-BUNDLE completeness guard** — bundled cefi data_types (book_snapshot/options_chain).
      **PARTIALLY CONFIRMED (slot-3 read-only 2026-06-03):** the finalize path DOES run cluster validation
      (`record_captured_from_counts(expected_root_clusters, observed_clusters)`; CLAUDE.md 4-pillar "cluster coverage ≥
      expected" — `MissingClusterValidationError` if absent), so the gate is PRESENT (not missing). The audit's worry is
      the `≥ count-threshold` vs `len(observed)==len(expected)` precision (a partial bundle that meets the count but
      misses a cluster root). The cluster-validation internals live in UTL `manifest_writer.py`
      `record_captured_from_counts` — left as a refinement for the cluster-SSOT owner (`mtds_mdps_master`) to tighten if
      `≥` admits incomplete bundles; **NOT a slot-3-solo fix** (UTL + the bundled writer span DeFi/sports too). The live
      writer's per-instrument path is unaffected (no clusters). Repo: UTL/MTDS — owning VM.
- [x] ✅ [CODE] P2. **CONFIRM reader empty-vs-failed differentiation — NOT A GAP (slot-3 read-only 2026-06-03).** The
      MTDS reader (`reader.py:583-639`) fetches `capture_status == "captured"` data + raises `ShardNotFoundError` for
      any non-captured cell — it does NOT (and should not) differentiate empty-vs-failed at the raw-read layer. The
      `attempted_failed` (retry) vs `empty_confirmed` (accept) differentiation is correctly handled ONE layer up at the
      **manifest-query / pre-flight** consumer (the backfill pre-flight reads `capture_status` and retries
      `attempted_failed`, skips `captured`/`empty_confirmed` — the honest-absence consumer policy). No reader fix
      needed.

## Phase 2 — dry-run + sharding/performance scope (slot-3, 2026-06-03)

> **✅ DRY-RUN COMPLETE — `mtds-migrate-cefi-v9dry-2024`** (n2-highmem-4, asia-northeast1-c, **NO `--apply`**;
> exit_code=0, self-deleted; ~3 min wall).
> `migrate_cefi_flat_to_v9_canonical --start-date 2024-01-01 --end-date 2024-12-31 --also-legacy --workers 32`.
> **Result: `TOTAL planned=914,624 written/moved=0 (DRY-RUN)`** for the 2024 shard (candles `planned=45,585`; 9 L-flat
> orphans fan-out shown with correct canonical dests). **`moved=0` = idempotent-skip** (the `-prd` already holds the
> migrated `pipeline_mode=` forms — consistent with the verified corpus-complete state). **No OOM at 32 GB** for a dense
> ~914k-object year (vs the 16 GB e2-standard-4 OOM on the all-years 1.9M listing). PLAN paths verified canonical
> (`day=/pipeline_mode=batch_tardis/asset_group=cefi/venue=/instrument_type=/data_type=/…`). Banner removed (VM
> self-deleted). Coding gate MET first: IS@f2ca5954 + MTDS@fa2b02c7/4e5fa57f + PM@878dd9553 all QG-green + on LDR.

**Per-year object distribution (measured 2026-06-03, delimited day-dir listing on the legacy bucket):**

| year  | day-dirs  | notes                          |
| ----- | --------- | ------------------------------ |
| 2019  | 277       | partial (from 2019-03-30)      |
| 2020  | 366       |                                |
| 2021  | 365       |                                |
| 2022  | 365       |                                |
| 2023  | 365       |                                |
| 2024  | 366       |                                |
| 2025  | 365       |                                |
| 2026  | 144       | partial (to 2026-05-24)        |
| **Σ** | **2,613** | == plan L2 count; ~2.377M objs |

≈ **910 objects/day-dir**, ≈ **300k objects/year**. The e2-standard-4 (16 GB) OOM was loading **all 2.377M** legacy
object names at once.

**Sharding + machine-size recommendation (for the NEXT-session `--apply`):** **8 year-shards (2019…2026), one VM each,
`n2-highmem-4` (32 GB)** — a per-year shard (~300k object names) fits comfortably in 32 GB (the OOM was 8× that on half
the RAM). Server-side `gcs_copy_object` at `--workers 32` (GIL-free I/O) → the per-year copy is network-bound, not
CPU-bound, so 4 vCPU suffices. The running 2024 dry-run validates the real per-year listing time + the 32 GB headroom
(result appended here on completion).

### ✅ E5 MANIFEST-REBUILD DRY-RUN — the real `_index`-rebuild step, validated 2026-06-04 (slot-3)

> Operator Q: _"have we dry-run the manifest (`_index`) rebuild to check it works as expected?"_ — **YES, and it caught
> a serious false-phantom bug that would have corrupted the `_index`.** Ran
> `rebuild_cefi_manifest --dry-run --start-date 2024-06-01 --end-date 2024-06-07` against the real `-prd` v8 `_index`
> (laptop ADC, `CLOUD_MOCK_MODE=false`; exit 0, ~100 s/week; reads the v8 index + classifies with NO column-name crash —
> validates the `reason`/`error_reason` fallback + the whole CF-11 re-emit pass on real data).

**Bug the dry-run surfaced (3 covered-key match gaps → FALSE phantom demotes of REAL captured cells):** the first run
flagged **`phantom_to_failed=1187`/week** — prior-`captured` cells the object scan "couldn't find" → it would
`record_failed(PHANTOM_CAPTURED_NO_OBJECT)` them, i.e. **flip real captured → attempted_failed corpus-wide** (the exact
data-corruption the workspace rule forbids). Root-caused to THREE gaps, each fixed + locked with a regression test (mtds
`rebuild_cefi_manifest.py` + `test_rebuild_cefi_manifest_cf11.py`, 5 new tests):

1. **Kraken slash-symbols** (`ADA/USD`, `XBT/USD`) — written as a 2-segment path
   `…/data_type=book_snapshot_5/ADA/USD.parquet`; the parser stem `[^/]+` can't cross the slash → object `unparseable`
   (576/week) → its captured cell looked phantom. Fix: stem `→ [^/=]+(?:/[^/=]+)*` (allows slash-symbols, excludes `=`
   so it can't swallow a bundle path).
2. **`instrument_type` case** — prior v8 `_index` stores `SPOT_PAIR` (UPPERCASE, old-writer anomaly) but the GCS path is
   `spot_pair`; the covered-key compared it case-sensitively (only `venue` was normalised) → EVERY real Kraken/spot
   captured cell missed the dedup. Fix: lowercase `instrument_type` on both sides of the covered-key (canonical form).
3. **Malformed/sentinel junk rows** — blank venue, no cell key (blank instrument_id AND underlying), or the `ticks`
   bundle-filename leaked into `instrument_id`; demoting them mints junk `attempted_failed` rows. Fix: **DROP** them
   (`dropped_malformed_captured`), never demote.

**Result after fixes (same week):** `phantom_to_failed 1187 → 12` (the 12 are genuine — DERIBIT
`futures_chain`/`options_chain` with a real `underlying` but verifiably NO object → honest absence → `attempted_failed`
for retry, CORRECT); `dropped_malformed_captured=399`; `reemit_skipped_covered 2938 → 3714` (+776 Kraken cells now
correctly matched); `reemit_attempted_failed=3763` preserved; `unparseable 576 → 0`. **The rebuild now works as expected
— verified the real v8 `_index` reads + classifies correctly + no real captured cell is demoted.** Before the REAL run,
re-confirm on a wider date range (the dry-run was a 1-week sample; the slash-symbol + case gaps are corpus-wide so
they'll recur identically, but a multi-year `--scan-only`/`--dry-run` spot-check of the phantom count is the cheap final
gate).

- [x] ✅ [CODE] P0. **E5 rebuild false-phantom fixes (3 covered-key gaps)** — slash-symbol parser stem,
      `instrument_type` case-canonical covered-key, malformed-junk drop. mtds `rebuild_cefi_manifest.py` + 5 regression
      tests. Caught by the 2026-06-04 manifest-rebuild dry-run (1187→12 false phantoms/week). **DONE — mtds@60debbfe**
      (tab→LDR; staging deferred behind the UTL/UAC dep-tier dam) | QG --no-fix exit 0 | 29/29 CF-11 tests green.
- [ ] [DATA] P1. **Before the REAL `_index` rebuild — multi-year dry-run phantom spot-check**: re-run
      `rebuild_cefi_manifest --dry-run` over a multi-year span (or the full corpus) and confirm `phantom_to_failed`
      stays small + well-formed (DERIBIT-chain-style true phantoms only), `dropped_malformed_captured` is junk-only, and
      `unparseable=0`. Cheap final gate before the irreversible-adjacent index overwrite.
- [ ] [DATA] P0. **NEXT SESSION — execute the migration** (after the dry-run validates perf): run the 8 year-sharded
      `--also-legacy --apply` gap-fill (5,233 legacy-only cells), then the irreversible orphan-sweep (with the mandatory
      pre-delete idempotent-`--apply`-over-full-range guarantee), then E5 manifest rebuild (now CF-11-canonical +
      false-phantom-safe @mtds#fa2b02c7+this-fix), E7 verify, E8 legacy-bucket delete. NOT this session (irreversible).

## Why this exists — cefi canonical FORM is broken corpus-wide (+ a recent 838-cell data gap)

The 2026-06-01 `_index` comparison (legacy `market-data-tick-cefi-…` vs canonical `market-data-tick-cefi-prd-…`) showed
the cell-coverage gap is small (838) — but the canonical FORM is wrong across the WHOLE corpus (the finding above). Both
are fixed in the one walk. Cell-coverage table:

| metric                                         | value                                                                                                                        |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| captured legacy CELLS `(date,venue,data_type)` | 91,602                                                                                                                       |
| canonical CELLS                                | 142,893 (canonical is AHEAD overall)                                                                                         |
| overlap                                        | 90,764                                                                                                                       |
| legacy-only CELLS (canonical MISSING)          | **838**                                                                                                                      |
| legacy-only examples                           | `(2026-03-21, BINANCE-SPOT, book_snapshot_5)`, `(2026-05-14, UPBIT, book_snapshot_5)`, `(2026-05-20, COINBASE-SPOT, trades)` |
| legacy-only by data_type                       | `book_snapshot_5` 363 · `trades` 336 · `derivative_ticker` 83 · `liquidations` 47 · `ohlcv_15s` 3 · `ohlcv_1m` 2             |

So cefi canonical is overall MORE complete than legacy (142k vs 91k cells), but **838 recent cells (2026-03→05,
BINANCE/UPBIT/COINBASE) exist in legacy only** — likely written to legacy right before the writers were drained
2026-06-01. These must land in canonical before L6 deletes the legacy bucket. Legacy layout (2026-06-01 audit):
`raw_tick_data/` (NO `by_date/` sub-tree — different from tradfi) + `processed_candles/`.

## Sequencing — gate before cefi backfill (inherits master HARD RULE)

No cefi backfill until this walk is C-GREEN. L0 tarball-prune blocker
(`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a VM. (The drained
`mdps-backfill-cefi-main-test` already self-terminated; no live cefi writer — relaunch is gated on C-GREEN.)

## Canonical target form (cefi)

| Dimension       | Legacy                                     | Canonical                                                                             |
| --------------- | ------------------------------------------ | ------------------------------------------------------------------------------------- |
| Bucket          | `market-data-tick-cefi-{project}` (no env) | `market-data-tick-cefi-prd-{project}`                                                 |
| asset-group key | `category=cefi`                            | `asset_group=cefi`                                                                    |
| pipeline_mode   | absent in path                             | `pipeline_mode=` partition (`batch_tardis`/`batch_hyperliquid_rest`/`live_websocket`) |
| schema_version  | legacy spread                              | v9                                                                                    |
| source          | (per `data_source_provenance` cefi)        | `tardis` / `<venue>` multi-source                                                     |

## Phased execution

### P0 — audit

- [x] ✅ [DATA] P0. Legacy→canonical `(date,venue,data_type)` diff (slot-3 tool, 2026-06-01): **legacy-only CELLS =
      5,233** (NOT 838 — the headline undershot; prior-not-ceiling). Oldest examples are 2020-01
      `OKX-FUTURES     book_snapshot_5` (legacy captured 91,602 · canonical 90,931 · overlap 86,369). These must land in
      canonical before L6 deletes legacy. Exact per-data_type object counts resolved in the C0 walk (idempotent copy of
      the gap).
- [x] ✅ [DATA] P0. Read canonical `cefi-prd` `_index` DATA-STATE (2026-06-01 slot-3): **100% v8** (not v9), **no
      `source` column**, **no `category`/`asset_group` column**, **blank `pipeline_mode`** → the
      FULL-re-canonicalisation finding above. Whole corpus is in scope, not 838 cells.
- [x] ✅ [DATA] P0. Reusable audit tool SHIPPED — `plans/audit/results/cf_manifest_audit_2026_06_01.py` (PM@4be440b6a):
      per-CF GREEN/RED data-state for any AG `_index` (schema_version dist, `source`/`category`/
      `asset_group`/`pipeline_mode` col presence, `error_reason` histogram CF-5, shallow object-path probe CF-2/3/9,
      legacy-only cell diff). DNS-robust (`gcloud cp` retried + time-boxed shallow probe). Run on cefi/tradfi/sports/
      prediction (results in their P0 blocks). Generalises to instruments + downstream. Feeds the audit-instruction
      Canonical-form sections.

### C — single-walk (gap-fill + canonicalisation)

- [x] ✅ [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: before the walk,
      enumerate ALL top-level trees + nested layouts in the cefi source + canonical buckets (`raw_tick_data/by_date/`
      flat-symbol, `processed_candles/by_date/day=/timeframe=/…`, any `day=/category=` or bare `{venue}/{chain}/date=`).
      Per layout: object count + sample schema; classify duplicate (keep freshest) vs complementary (migrate all). The
      walk MUST cover every in-scope layout or it is incomplete (review-blocking). SSOT:
      `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § Cross-AG lesson + grounded recipe Phase 0. DONE
      (slot 10, 2026-06-03): exhaustive enumeration confirmed THREE layouts (not 2 from shallow probe). Legacy: L1=9
      flat orphans, L2=2,613 day=/pipeline_mode=batch_tardis/asset_group=cefi/ (MOST CANONICAL), L3=460 candle day-dirs.
      Canonical: C1=9 flat orphans, C2=2,594 day=/asset_group=cefi/ (MISSING pipeline_mode= — LESS canonical than L2),
      C3=464 candle day-dirs. Key finding: legacy L2 is more canonical than canonical C2. 19-day raw gap (L2−C2). Walk
      implications documented in SSOT §Phase-0 cefi-specific verification. PM@2f315f0fb.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [x] ✅ [DATA] P0. C0 ONE bundled **WHOLE-CORPUS** walk (the finding makes this corpus-wide, not 838 cells): (a)
      re-version **every** cefi row+parquet **v8→v9** (CF-1) asserting data-state, not the constant; (b) add the
      **`source` column** = `tardis` on every row (CF-4) + (c) the **`asset_group=cefi` column/key** on rows + paths
      (CF-2) + (d) the **`pipeline_mode=` partition** + non-blank column (CF-3); (e) typed empty-reasons (CF-5); (f) the
      838-cell legacy→canonical gap-fill copy (`raw_tick_data/` + `processed_candles/`, layout-aware — cefi has NO
      `by_date/`). Column adds (b–c) are a CONTENT rewrite → download+transform+upload **parallelised per the perf
      contract** (NOT a server-side path move; NOT "run locally" — this is a VM-scale walk now, gated on L0). The
      838-cell pure-path copies use `gcs_copy_object`. Idempotent. — DONE (slot 10, 2026-06-03):
      market-tick-data-service@53671a0 (Kraken BASE/QUOTE 2-level path fix) + @7cb9947. TOTAL planned=3928281
      written/moved=1863687 (dry-run: 3,916,302). 112 corrupt KRAKEN-SPOT USD.parquet objects from partial apply deleted
      before re-run with fix. Canonical bucket now has pipeline_mode=batch_tardis paths.
- [ ] [DATA] P0. C-pipeline_mode RIDER (folded into C0 (d)): the `pipeline_mode=` partition lands in THIS walk
      (satisfies `pipeline_mode_partition_migration` for cefi).
- [ ] [DATA] P1. C-source RIDER (folded into C0 (b)): the `source` column (`tardis`, swap-resilient) lands in THIS walk
      (closes `data_source_provenance` cefi).

### Verify + handoff

- [ ] [DATA] P0. Post-walk: re-read the canonical `_index` DATA-STATE (re-run the reusable audit tool) → **100% of rows
      v9** (was 100% v8); **`source` populated on every cell** (zero blank; `tardis`, swap-resilient); **`asset_group`
      column/key present** (no `category`/blank); **`pipeline_mode` non-blank + partition present**; typed reasons;
      **legacy-only CELLS = 0** (838-gap closed). Closes `data_source_provenance` cefi + `pipeline_mode_partition` cefi.
      C-GREEN signal for `bucket_name_ssot…` Phase 6/7 cefi legacy bucket decommission.
- [ ] [DATA] P0. **Orphan sweep + bucket-state evidence (slot/Harsh bucket-state verification 2026-06-02).** Measured
      (Cloud Monitoring `storage/v2/total_count`, live-object): `market-data-tick-cefi-prd` 1,545,850 (~65% of legacy
      2,377,168) and **~17 days STALE — `-prd` latest `day=2026-05-07` vs legacy `day=2026-05-24`** (consistent with the
      5,233 legacy-only cells; the C0 gap-fill closes it by reading legacy as source). `-prd` is INTERMEDIATE FORM:
      `asset_group=cefi` is in the PATH but there is **NO `pipeline_mode=` partition** (confirmed at the data level, not
      just the manifest). So the E4 walk writes NEW `pipeline_mode=` paths → the pre-existing legacy-FORM `-prd` objects
      become ORPHANS; E5 rebuild / E7 verify MUST delete the legacy-FORM `-prd` objects too (not only the legacy SOURCE
      bucket), else the rebuild double-counts. Legacy carries 3.81M noncurrent objects → the E8 delete must also purge
      noncurrent versions, and the "canonical ≥ legacy" count gate must use Monitoring `type=live-object` (never a naive
      recursive `ls`, which counts versions + soft-deleted).

## Execution checklist (grounded — next session, finish in full)

> CF debt is in the `_index` MANIFEST + object PATHS, NOT the raw tick parquets (cefi raw = pure market data). See
> `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § MECHANISM + complete layout map. cefi is the HARDEST:
> `raw_tick_data/by_date/{SYMBOL}.parquet` is FULLY FLAT (day/venue/data_type only in cols + epoch-µs ts).
>
> ⚠️ **IRREVERSIBLE — E8 DELETES the legacy bucket permanently.** Do not run E2–E8 until the canonical target (schema =
> v9, paths = `day=/pipeline_mode=/asset_group=cefi/venue=/chain=/instrument_type=/data_type=`, source/available_at
> semantics) is CONFIRMED CORRECT on the verify step. One pass, no confusion — once legacy is deleted it is gone.

- [x] ✅ [DATA] P0. E1 **EXHAUSTIVE** layout + VOCAB audit (slot-3 2026-06-01, operator "3 versions like defi" check).
      ⚠️ **CORRECTION — the earlier shallow probe was WRONG ("FULLY FLAT").** A multi-level count found cefi raw is
      **THREE layouts**: (L-bulk) `raw_tick_data/by_date/day=/asset_group=cefi/venue=/instrument_type=/data_type=/` =
      the DOMINANT layout, **2,613 day-dirs**, near-canonical (instrument_type already lowercase) but MISSING
      `pipeline_mode=`; (L-canon) some days already `day=/pipeline_mode=batch_tardis/asset_group=cefi/`; (L-flat) **only
      9 orphan** root `{SYMBOL}.parquet` (2026-05-04 backfill bug). Same 3 layouts in legacy + prd. **Canonical VOCAB
      (data-state, not assumed)**: venue HYPHENATED (DERIBIT/BITFINEX-SPOT/BINANCE-FUTURES/HYPERLIQUID);
      `instrument_id="{VENUE}:{ITYPE}:{SYMBOL}"`. **CF-7 drift**: instrument_type CASE in \_index column,
      blank/`UNKNOWN` venue (1453+111), blank data_type (9757), COINBASE vs COINBASE-SPOT. — slot-3 2026-06-01.
- [x] ✅ [DATA] P0. E2 Built + FIXED `migrate_cefi_flat_to_v9_canonical.py` (3-layout-aware, perf-contract). **The first
      build handled ONLY the 9 L-flat orphans → would have MISSED the 2,613 L-bulk day-dirs (the exact "we keep missing
      things" trap the operator flagged). FIXED** to cover all three: L-bulk/L-canon = path-only `gcs_copy_object`
      inserting `pipeline_mode=` after `day=` (server-side ~250x; L-canon dest==src → no-op); L-flat =
      read+regroup-by-day+ fan-out. All via the UAC `candidate_parquet_paths` SSOT (byte-exact batch=live; pipeline_mode
      from venue, HYPERLIQUID→ hyperliquid_rest else tardis). Parquet content untouched (v9 cols at E5 rebuild). CF-7
      blank/`UNKNOWN` venue + blank data_type skip+logged for E6. Candles = pipeline_mode insert. Knobs
      `--workers`/`--start-date`/`--end-date`/`--also-legacy` + `python -u` + per-object isolation + idempotent. All 3
      layout transforms unit-validated; lint+typecheck clean. — market-tick-data-service@844124f7, slot-3 2026-06-01.
- [x] ✅ [DATA] P0. E3 Confirm cefi writer drained + snapshot `cefi-prd/_index` — **DONE (slot-3, 2026-06-03).** No live
      cefi writer VM (`gcloud compute instances list --filter="name~cefi OR name~mdps-backfill-cefi"` → empty);
      `_index/per_vm/` holds only the stale `_legacy_seed.parquet` (2026-05-12, no active shard emission). Consolidated
      `availability_index.parquet` (47.58 MiB, last consolidator write 2026-06-03T09:28Z) snapshotted to
      `_index/snapshots/pre_migration_2026-06-03.parquet` (49,893,721 bytes == source; sits beside the prior
      `pre_migration_2026-05-22.parquet`). Pre-migration safety point established; E4 walk can run.
- [x] ✅ [DATA] P0. E4 — **the `-prd` raw_tick + candles PATH migration is ALREADY DONE** (slot-3 calibration + GCS
      verify 2026-06-03). `--apply` calibration slices reported `moved=0` NOT from a bug but because the migrator
      correctly **idempotent-skips** (`_move_day_one:219` `gcs_describe_object(dst) is not None`): the canonical
      `pipeline_mode=` dests already exist. Verified on day=2024-06-03 — `_canon_day_rel` computes
      `day=/asset_group=cefi/…/ADAUSDT.parquet` → `day=/pipeline_mode=batch_tardis/asset_group=cefi/…/ADAUSDT.parquet`
      (dst≠src, `pipeline_mode` inserted — migrator is CORRECT), and GCS shows BOTH forms coexisting:
      `day=2024-06-03/asset_group=cefi/` = **474 OLD/orphan** objects + `pipeline_mode=batch_tardis/` +
      `batch_hyperliquid_rest/` = **482 MIGRATED** objects. So the corpus-wide `pipeline_mode=` insert already ran (a
      prior `--apply`); `gcs_copy_object` copies (not moves) → the old `day=/asset_group=cefi/` objects remain ORPHANS.
- [ ] [DATA] P0. **❌ RETRACTION of the earlier "E4-BUG / we-keep-missing-things" P0 (it was WRONG).** I read
      `moved=0` + a `head -3` listing (which shows `asset_group=` paths — they sort BEFORE `pipeline_mode=`) and wrongly
      concluded "no `pipeline_mode=` sibling / migrator no-ops L-bulk". The FULL listing shows the `pipeline_mode=`
      siblings DO exist (482/day). slot-10's `C2 = day=/asset_group=cefi/` count is exactly these **post-migration
      orphans**, not a pre-migration gap. No migrator fix is needed.
- [ ] [DATA] P0. **E4 remaining work = ORPHAN SWEEP + gap-fill, NOT a path walk.** (slot-3 verify 2026-06-03: the
      `pipeline_mode=` migration is COMPLETE corpus-wide — sampled days 2020→2026 ALL have both forms; the **9 L-flat
      orphans are ALSO migrated** (e.g. `SOL-ETH.parquet` →
      `day=2024-11-07/pipeline_mode=batch_tardis/…/SOL-ETH.parquet` exists; the 9 root files remain only as orphans). So
      the ONLY additive work left is the legacy gap-fill.) (a) **🛑 IRREVERSIBLE — delete the OLD
      `day=/asset_group=cefi/…` (no-`pipeline_mode=`) orphan objects corpus-wide (~474/day × ~2,613 days ≈ 1.2M) + the 9
      root L-flat orphans** now their `pipeline_mode=` forms exist. PRE-DELETE GUARANTEE (mandatory): first run
      `migrate_cefi_flat_to_v9_canonical --apply` over the FULL range once (idempotent — copies any orphan still lacking
      a sibling, skips the rest) so EVERY orphan provably has a migrated dest; THEN delete (count via Monitoring
      live-object, NOT naive recursive `ls`; per-object isolation; idempotent). This IS the E7 orphan-sweep. (b)
      `--also-legacy` 5,233-cell legacy→canonical gap-fill (additive; VM-scale — the 1.9M legacy listing stalled an
      e2-standard-4, so shard/bigger-mem). **Deliberate execution (irreversible deletes + VM-scale) — not to be
      rushed.** Repo: market-tick-data-service.
- [x] ✅ [DATA] P0. E5 Manifest rebuild → v9 — **DONE (mtds@2c3a479b, 2026-06-02)** via the RECOMMENDED fork (A):
      `rebuild_cefi_manifest.py` now (1) parses an OPTIONAL `pipeline_mode=(?P<pipeline_mode>[^/]+)/` segment in all 3
      `_PAT_*` matchers (between `day=` and `asset_group=`); (2) lists at DAY level (`raw_tick_data/by_date/day={d}/`)
      so migrated `pipeline_mode=` objects are enumerated (an `…/asset_group=cefi/` list prefix MISSES them); (3)
      targets the canonical `-prd` bucket; (4) stamps `pipeline_mode` on `add()` — from the path segment when present
      else `derive_pipeline_mode_for_row(venue,"cefi",dt)` (== the migrator + live writer); `source` left "" → add()
      auto-resolves (cefi single-source tardis). 11 parser tests green (3 new pipeline_mode cases). add()'s
      pipeline_mode kwarg landed utl@b872bdf1 (fork A). **REMAINING enhancements (gate G4, tracked via CF-11 todos
      above + Verify below):** `available_at` parquet-col-else-day-EOD; 0-row→empty backstop; legacy-`_index` re-emit of
      `attempted_failed`/typed-`empty_confirmed` rows (CF-11). Original build-spec retained below for reference.
- [ ] [DATA] P2. E5 build-spec reference (superseded by the DONE item above): `rebuild_cefi_manifest.py` encodes the
      per-instrument row key (the LIVE writer key =
      `date,venue,chain,data_type,league_id,instrument_type,underlying,quote_asset,     margin_type,instrument_id`;
      orchestrator.py:2937/2957) + tolerates `raw_tick_data/by_date/`+`asset_group=`. Two changes only: (1) its `_PAT_*`
      regexes + `prefix_templates` do NOT account for the NEW `pipeline_mode=` segment between `day=` and `asset_group=`
      → list per `raw_tick_data/by_date/day={d}/` and extend `parse_hive_path` to capture an optional
      `pipeline_mode=(?P<pipeline_mode>[^/]+)/`; (2) stamp v9 cols: pass `source` (cefi single-source `tardis`;
      HYPERLIQUID→`hyperliquid_rest`) + `pipeline_mode`. **INTERNALS Q — RESOLVED (slot-3 2026-06-01):** `add()`
      persists `source` (auto-resolved via SOURCE_PRIORITY at manifest_writer.py:236) but does **NOT** persist
      `pipeline_mode` (no kwarg; goes to `**kwargs` → dropped) — that is exactly why CF-3 reads blank corpus-wide (the
      live per-instrument cefi `add()` at orchestrator.py:2957 also omits it). `record_captured_from_counts`
      (mw.py:2840) takes `pipeline_mode` but **REQUIRES** `expected_root_clusters` + `observed_clusters` +
      `available_at_envelope` (the BUNDLED path). `record_captured` takes `pipeline_mode` but needs a `df` (read every
      parquet). **DESIGN FORK (pick deliberately — feeds the irreversible delete):** (A) **[RECOMMENDED]** add a
      back-compatible `pipeline_mode: PipelineMode|str = ""` kwarg to `ManifestWriter.add()` that coerces
      (`_coerce_pipeline_mode`) + persists it like `source` (default "" = today's behavior → zero back-compat risk; ALSO
      closes the live-writer CF-3 gap so batch=live). Then rebuild via `add(...,     pipeline_mode=, source=)`. Needs
      UTL QG. (B) use `record_captured_from_counts` with trivial single-cluster maps (`{instrument_id: rows}` as both
      expected+observed) — hacky for per-instrument. (C) `record_captured(df=...)` reading each parquet — correct but
      slow. `available_at`: parquet col if present, else day-EOD-UTC (never migration-time). Same fork applies to
      `rebuild_prediction_manifest.py`. **Do NOT build until the fork is chosen** — wrong choice corrupts the `_index`
      that gates L6 delete.
- [ ] [DATA] P1. E6 CF-7 relabel: `COINBASE`↔`COINBASE-SPOT`, blank venue/data_type → canonical (diagnose, don't bulk).
      Investigate the 50% `attempted_failed` rows (1.33M) — flag to cefi AG owner (separate from canonicalisation).
- [ ] [DATA] P0. E7 Verify: `cf_manifest_audit_2026_06_01.py market-data-tick-cefi-prd-…` → CF-1…CF-12 GREEN on
      data-state; flip CF-coverage rows in `cefi_master_audit_instructions.md`.
- [ ] [DATA] P0. E8 ⚠️ IRREVERSIBLE — only after E7 GREEN: hand C-GREEN to `bucket_name_ssot…` L6 → **delete legacy
      `market-data-tick-cefi` permanently** (single source of truth; legacy data is gone).

### CF-11 completeness — fetch-failure must be `attempted_failed`, NOT `empty_confirmed` (operator directive 2026-06-02)

> Operator: "when there is an API issue somewhere in IS or MTDS, is it correctly doing `attempted_failed` where the
> attempt makes sense by instrument / UAC bounds — RATHER THAN `empty_confirmed` which would not be complete?" CeFi
> twist: cefi is single-source (`tardis`). A Tardis fetch error for a `(venue, instrument, data_type, date)` cell INSIDE
> the expected-attempt set — instrument in the IS CeFi universe, data_type registered in UAC SOURCE_PRIORITY, date
> within the venue/instrument coverage window — is a masked fetch failure → `attempted_failed` (retry/backfill), NOT a
> false `empty_confirmed`/`SOURCE_RETURNED_ZERO` that freezes the gap forever.
>
> **The manifest must EXPLAIN every zero (3-way decision tree — the E5 rebuild contract):** (1) attempt errored on a
> warranted cell → `attempted_failed`; (2) a UAC guard explains the zero → typed `empty_confirmed`
> (`EXPECTED_OUT_OF_COVERAGE_WINDOW` / pre-listing / delisted); (3) only if market open + fetch succeeded + genuinely
> nothing → `SOURCE_RETURNED_ZERO`. A blanket/blank `SOURCE_RETURNED_ZERO` = "we don't know why" masquerading as
> complete.

- [x] ✅ [CODE] P0. **Rebuild classifier (`rebuild_cefi_manifest.py` / E5): within-bounds empty → `attempted_failed`.**
      **DONE (mtds@fa2b02c7)** — see the audit P0 #1 above. `reemit_cefi_honest_absence_rows` reclassifies blank-reason
      OR `SOURCE_RETURNED_ZERO`-on-guaranteed (`trades`/`ohlcv*`/`book_snapshot_5`) OR invalid-reason →
      `record_failed(WITHIN_BOUNDS_EMPTY_RECLASSIFIED)`; keeps typed-empty on sparse data_types (funding/options_chain).
      (Coverage-window / known-gap precision deferred — the conservative data_type-guarantee + reason gate is the
      operator-prioritised core; a per-instrument IS-universe/coverage cross-check is a NICE-TO-HAVE refinement, tracked
      as the P2 below.)
- [x] ✅ [CODE] P0. **Rebuild: re-emit existing `attempted_failed` rows v9, status PRESERVED** — **DONE
      (mtds@fa2b02c7).** The pass re-emits every prior `attempted_failed` row (not superseded by a fresh parquet) via
      `record_failed` with its original `error_reason` (blank→`UNCLASSIFIED_ADAPTER_ERROR`) — the ~1.33M survive as v9
      `attempted_failed`, still flagged for backfill, never collapsed to empty. +unit test asserts preservation.
- [ ] [CODE] P2. **NICE-TO-HAVE — rebuild within-bounds precision**: cross-check the reclassify decision against the IS
      CeFi universe + per-instrument coverage windows + the known-gap registry (today the gate is the conservative
      data_type-guarantee + reason heuristic, which the operator prioritised; the IS-universe cross-check would tighten
      false-positive reclassifications on genuinely-sparse symbol-days). Provenance: slot-3 E2E audit 2026-06-03.
- [ ] [DATA] P0. **Absorbed from `cefi_processed_candles_manifest_file_disconnect` (harsh) — ROOT CAUSE CORRECTED by
      direct `_index` query (slot-3 2026-06-03).** The reported "MTDS marks `processed_candles` `captured` with no file"
      is a **category error, NOT manifest corruption.** Reading the live cefi `_index` (2,640,864 rows): the manifest
      **already disambiguates surfaces via `data_type`** — RAW tick (`trades` 1.19M / `book_snapshot_5` /
      `derivative_ticker` / `liquidations` / `futures_chain`, ~all `service_name=market-tick-data-service`) vs CANDLE
      (`ohlcv_1m/5m/15m/1h/4h/1d`, **only 8,715 rows**, mostly `service_name=market-data-processing-service`). The issue
      cross-checked `processed_candles/` FILES against **`trades`-captured** rows; a `trades` `captured` row (MTDS)
      correctly means the **RAW** tick file exists (VERIFIED: day=2026-05-02 BITFINEX/BITGET/KRAKEN raw `trades` files
      present) — the manifest **never marked CANDLES captured** for those venues (on 2026-05-02 KRAKEN/BITFINEX have NO
      `ohlcv` rows at all). So MTDS is NOT writing phantom processed-candle rows; hypothesis (b) is disproved and the
      `reconcile_phantom_manifest_rows_all.py` flip-to-`attempted_failed` would WRONGLY demote correct raw rows (it only
      probes `raw_tick_data/` anyway). Real findings to action (3 sub-items, repos noted):
  - [x] ✅ [CODE] P0. **Read-side contract fix (features-service)** — **DONE (features-service@933b8747, slot-3
        2026-06-03).** `LookbackValidator._build_captured_index` credited ANY captured `data_type` as a candle-available
        lookback date (raw `trades`/`book_snapshot_5` over-counted history off the shared `_index`); now filters to the
        feature*groups' candle
        `ohlcv*\*`data_types via`resolve_data_type_for_feature_group`(mirrors the already-correct    `get_available_instruments`). +regression test (`ohlcv_1m`counted;`trades`/`book_snapshot_5`not). Verified     delta_one 20/20 + basedpyright-clean diff. **Shipped under operator EXEMPTION** (local macOS QG red only on the     foreign non-deterministic flake`features_service_full_qg_test_pollution_flake_2026_06_03.md`; Linux     `quality-gates-v2`
        re-verifies at promotion). Repo: features-service.
  - [ ] [DATA] P1. **Real cefi candle-coverage gap (partial backfill).** `ohlcv_*` manifest rows are sparse (8,715) and
        processed-candle FILES exist only for a partial venue set (BITGET-heavy; e.g. day=2026-05-03 = BITGET-FUTURES
        319 / BITGET-SPOT 151 / BITFINEX-FUTURES 90 / KRAKEN-FUTURES 18). MDPS candle generation for cefi is incomplete
        → track + complete the candle backfill (separate from raw-tick canonicalisation). Repo: MDPS.
  - [ ] [DATA] P1. **VERIFY MDPS candle-manifest faithfulness.** Do the `ohlcv_*` rows faithfully reflect the candle
        files that DO exist, or is MDPS under-emitting `ohlcv` rows for written candle files? Compare `ohlcv` row
        coverage vs candle-file coverage on a sample day. Also reconcile the minor cross-writes (782 MTDS-written
        `ohlcv` rows; 616 MDPS-written `trades` rows) — confirm which service legitimately emits `ohlcv` per venue (MTDS
        REST-poll venues like LIGHTER/PACIFICA vs MDPS-processed). Repo: MDPS (+ MTDS REST-poll path). On all three
        GREEN, archive the absorbed issue doc.
- [x] ✅ [CODE] P0. **Write-path CF-11 audit + fix (IS + MTDS cefi/tardis adapters) — BOTH SIDES NOW VERIFIED CLOSED
      (slot-3 deep audit 2026-06-04).** MTDS side was already compliant (diagnosis below). **IS RESIDUAL NOW RESOLVED:**
      a full IS→manifest trace confirms a genuine cefi reference-data fetch error lands as `attempted_failed`, NOT a
      silent universe shrink. All four cefi IS adapters were fixed to **RE-RAISE** on a genuine fetch failure (NOT
      `return []`): `aster.py:152-154`, `hyperliquid.py:115-117` (both `e2e008f0`), `tardis.py:467-494`
      (`if not results and failures: raise`, `e2e008f0`), `deribit_combo_adapter.py:232-236`+`297-300` (`f2ca5954`). The
      RuntimeError threads into `urdi_reference_provider._fetch_one` → `failed[]` → excluded from `_non_error_venues`
      (`orchestrator.py:1746-1748`) → honest-coverage writes `record_failed(...)` `attempted_failed` rows for every
      `missing_shard` (`orchestrator.py:2978-2993`). Regression locked by
      `tests/unit/test_is_adapter_fetch_failure_raises.py`. Closes the residual + the P1 IS-side verify below. Original
      diagnosis preserved: **DIAGNOSIS (slot-3 2026-06-02, grep-then-READ — MTDS (timeout/5xx/429/auth) for an
      in-universe instrument within coverage bounds, the handler MUST `record_failed` (→ `attempted_failed`) via
      `classify_venue_error()`/`ADAPTER_FETCH_FAILED`, NOT `record_empty`. Grep the cefi/tardis fetch paths in MTDS
      handlers + instruments-service for `except … record_empty` / bare `return []` swallows; gate the empty-vs-failed
      decision on instrument-in-universe + UAC coverage bounds. Cross-ref the sports CF-11 model
      (`sports_manifest_canonicalisation_2026_06_01.md` § CF-11). **DIAGNOSIS (slot-3 2026-06-02, grep-then-READ — MTDS
      side VERIFIED COMPLIANT, no swallow):** the MTDS write-path already implements the sports CF-11 model for
      cefi/tradfi/prediction. (a) Adapters (tardis/ccxt/databento/massive/ polymarket) classify via
      `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED` + **re-raise** on a genuine API error (do NOT swallow into
      `record_empty`/`return []`). (b) `engine/orchestrator.py` finalize gates the empty-vs-failed decision on a
      recorded fetch-failure at BOTH levels: tier-2 venue-level (`orchestrator.py:3818` —
      `if effective_failure is not None: record_failed(classify_venue_error(code_token)) else: record_empty(SOURCE_RETURNED_ZERO)`,
      with `failed_per_dt_by_venue` precedence for the bundled-Databento partial-success case) and tier-3 per-instrument
      (`orchestrator.py:3766` —
      `if tier3_classified_error is not None: record_failed else record_empty(SOURCE_RETURNED_ZERO)`). So a swallowed
      fetch-failure cannot land as a frozen `SOURCE_RETURNED_ZERO` from the MTDS path. **RESIDUAL (still `- [ ]`):** the
      **instruments-service\*\* fetch paths were NOT exhaustively read this session — focused verify needed that IS
      reference-data fetch errors likewise `record_failed` (not `record_empty`/`return []`). Reclassify this todo as
      "verify IS write-path CF-11 (MTDS already compliant)" — the heavy lift the todo assumed is largely absent.
- [x] ✅ [CODE] P1. **IS-side CF-11 verify — RESOLVED (slot-3 deep audit 2026-06-04): the open question is ANSWERED — a
      genuine cefi IS fetch failure DOES become `attempted_failed`, no silent universe shrink.** The earlier `return []`
      shape was the gap; all four cefi adapters now RE-RAISE (`e2e008f0` + `f2ca5954`) so `_fetch_one` routes them into
      `failed[]` → `record_failed`/`attempted_failed` (full trace in the P0 above). The event→manifest wiring is the
      `_non_error_venues` exclusion (`orchestrator.py:1746`) + honest-coverage `record_failed` (`:2978-2993`).
      UNCONFIRMED → CONFIRMED. Original read-only note preserved: **(slot/Harsh 2026-06-02, read-only) — cefi IS
      adapters use the classify+emit-event+return-[] shape.** Read the cefi IS reference-data adapters
      (`instruments-service/.../reference_data/adapters/cefi/`): `aster.py` / `hyperliquid.py` /
      `deribit_combo_adapter.py` / `tardis.py` handle transient API errors via `classify_venue_error(...)` + emit
      `ADAPTER_FETCH_FAILED`, then `return []` (consistent with the shard-isolation "no raise in per-venue loops" rule;
      tardis has multiple return-[] sites — L764/872/918/959/968). No ZERO-signal swallow found in the cefi IS adapters
      (unlike tradfi `databento.py:826` — see tradfi plan § CF-11). **OPEN QUESTION (needs the IS
      catalogue/manifest-layer read — deeper context):** whether the IS layer records `attempted_failed` from the
      emitted `ADAPTER_FETCH_FAILED` when an adapter returns [] — if it does NOT, the return-[] universe shrink is
      itself the gap. So cefi IS-side compliance is UNCONFIRMED (the classify+event pattern is right; the event→manifest
      wiring is unverified). Repo: instruments-service. parent_epic: mtds_mdps_master.

## Success criteria

- Canonical `cefi-prd` `_index` DATA-STATE: **v9 on 100% of rows** (was v8) + `asset_group` column + `pipeline_mode=`
  partition (non-blank) + **`source` on every cell (zero blank — HARD)** + typed reasons; **0 legacy-only cells**.
- The full-corpus form fix (not just the 838-cell gap) is landed — per the fix-fully-autonomously HARD RULE.
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-cefi-…` deletable.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — cefi canonical form.

## ⑦ Coverage-denominator could-exist seed — cross-AG note (filed by slot-5 2026-06-04)

> Operator 2026-06-04 (point ⑦): the deployment-api/ui coverage **denominator** must reflect the **could-exist
> universe** (instruments/fixtures that exist in IS but whose backfill has NOT run), not just rows that exist in the
> manifest. **The seeding mechanism already exists** — `instruments-service/scripts/enumerate_expected_universe.py` (v2
> expected-universe enumerator) cross-joins the IS catalog × dates × data_types, subtracts existing manifest rows, and
> seeds `record_expected_unattempted` for the residual; deployment-api `data_status_hierarchical` already counts
> `expected_unattempted` in the 4-state denominator. Slot-5 fixed the cross-cutting blocker: the enumerator's default
> bucket map was stale for ALL 5 AGs (missing the `-prd-` env tier) → now resolves via `resolve_bucket_name`
> (instruments-service, ⑦ in `prediction_manifest_canonicalisation_2026_06_01.md`). **Remaining for cefi:**

- [ ] [CODE] P1. ⑦ cefi could-exist denominator seed — build the `--catalog-path` parquet from the cefi IS catalog
      (per-instrument lifecycle: `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`) and run
      `enumerate_expected_universe.py --asset-group cefi --catalog-path <catalog> --apply-write` against the canonical
      `_index` so the raw-tick denominator == could-exist universe (active-but-uncaptured instruments seeded
      `expected_unattempted`). Verify on a VM (GCS flaky locally); confirm `_enumerate_v2_cefi` row-key/data_types match
      the cefi captured atom; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The mechanism +
      bucket fix are done; this is the per-AG catalog build + run + verify. parent_epic: mtds_mdps_master.

## G1 IS-catalogue session — read-only audit + dry-run on real prod GCS (slot-3, 2026-06-07)

> **GOAL (G1 for cefi, per `master_data_canonicalisation_migration_catalogue_2026_06_07.md`):** the cefi slice of the
> could-exist universe GREEN so downstream denominators/preflight (⑥/⑦, CF-14) are honest. This session ran the
> **read-only** halves (cf-audit + catalogue/enumerate dry-run); the irreversible `--apply-write` seed is GATED (below)
> and a **BIG denominator-correctness finding** was surfaced by the dry-run (the value of dry-run-before-apply).

**① `cf_manifest_audit` on `instruments-store-cefi-prd` `_index` (read-only, `gcloud cp` + pandas) — the IS reference
`_index` is NOT v9-canonical:**

- **CF-1 RED**: `schema_version` 100% **v8** (0/30,803 v9) — same v8-not-v9 state cefi MTDS had.
- **CF-3 RED**: `pipeline_mode` blank on 100% of rows. **CF-4 RED**: no `source` column. **CF-8 RED**: no `available_at`
  (only `written_at`/`attempted_at` proxies). **CF-2**: no `asset_group`/`category` column (bucket implies AG; paths are
  non-hive flat).
- **Two extra data-state gaps**: **12,372 / 30,803 rows (40%) have NULL `capture_status`** (only 18,431 `captured`); and
  **`data_type` is blank on every row** (the IS reference cell is venue×date, not data_type-keyed — but the canonical
  form should still type it). Legacy-vs-prd diff: **23 legacy-only cells** (blank-data_type, 2025-10) — small L6
  data-loss gate.
- **Verdict**: the cefi **instruments-store** `_index` needs the same v8→v9 single-walk
  (source/pipeline_mode/asset_group columns + available_at + capture_status backfill) that the MTDS `_index` needs.
  **Owner = the cefi slice of `instruments_manifest_canonicalisation_2026_06_01.md`** (master registry G1, per-AG). That
  walk is an `--apply` op → **GATED on G0** (source-aware pipeline_mode model) per the coordinator. Dry-run/audit only
  this session. (Tracked todo below.)

**② Catalogue (`build_instrument_catalogue.py`) — APPLIED + present (no action):** `prod/catalog.parquet` exists
(213,990 rows; 5 instrument_types `COMBO/FUTURE/OPTION/PERPETUAL/SPOT_PAIR`; 17 venues; 3,473 alive). Migration-stable
per `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`.

**③ `enumerate_expected_universe.py --enumerator-version v2` DRY-RUN (scan-only, no write) — ran end-to-end on real prod
GCS** (catalog read via local `gcloud cp` workaround — laptop `gcsfs token=cloud` fails; manifest read via UTL/ADC
worked). 2026-05-01→03 window: catalog 213,990 · manifest 2,640,864 rows · **101,010 candidate rows** (88,025
blank-reason in-coverage-pending, 6,692 `EXPECTED_INSTRUMENT_DELISTED`, 6,293 `EXPECTED_INSTRUMENT_NOT_LISTED`). The
machinery WORKS.

**④ 🔴 BIG FINDING (data-correctness, gates the cefi seed) — the v2 enumerator's could-exist universe does NOT match the
cefi captured atom (answers the pre-existing "confirm row-key/data_types match" check: they DON'T).** Two coupled bugs
in `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_v2_cefi:550` (`for dt in data_types:`
iterates ALL 7 `DATA_TYPES_BY_ASSET_GROUP["cefi"]` for **every** instrument with **no `(instrument_type × data_type)`
validity filter** and **no bundle-grain handling**):

1. **Impossible combos seeded**: a `PERPETUAL` (`ASTER:PERP:ADAUSDT`) is enumerated `expected_unattempted` for
   `options_chain` + `futures_chain`; a `SPOT_PAIR` for `derivative_ticker`/`liquidations`/chains — combos that can
   never be captured. Real captured combos (manifest ground-truth, 1.31M captured rows):
   `spot_pair`→trades/book_snapshot_5/ ohlcv\*,
   `perpetual`→trades/derivative_ticker/book_snapshot_5/liquidations/ohlcv\*, `future`→trades/book_snapshot_5/
   derivative_ticker/liquidations.
2. **Wrong GRAIN for options/futures bundles**: the catalog carries **72,156 `OPTION` + 17,472 `COMBO`** per-instrument
   rows, but cefi options/futures are captured as **per-underlying `options_chain`/`futures_chain` BUNDLES**
   (instrument_type=`options_chain`/`futures_chain` in the manifest; **~0 captured per-`OPTION`/`COMBO` rows**). So
   every `OPTION`/`COMBO` catalog row × 7 data_types × dates can never match the present-set → all seeded false
   `expected_unattempted`. This is why **DERIBIT = 92,106 / 101,010 (91%)** of the dry-run candidates. Same bundle-grain
   class the catalogue plan flagged for prediction/sports — **cefi options/futures need it too** (the catalogue producer
   assumed a "plain `--asset-group cefi` run", but cefi has the bundle-grain question for options/futures).

**Impact**: an `--apply-write` now would pollute the cefi `_index` with **millions of false `expected_unattempted`
rows** (impossible combos + wrong-grain options/futures) → badly distort the cefi coverage denominator (⑥/⑦/CF-14) — the
exact opposite of the honest denominator G1 exists to produce. The dry-run caught it before any write.

**⑤ Scheduler (G1.schedule / step-4): the G1 catalogue+enumerate is NOT wired for cefi.** The two existing TF schedulers
(`instrument_catalogue_scheduler.tf` → UAC `generate_instrument_catalogue.py` UI artefacts;
`catalogue_regen_scheduler.tf` → envelope/availability JSON) are the OLD catalogue-**artefact** regens, NOT the
lifecycle roll-up (`build_instrument_catalogue.py` → `{env}/catalog.parquet`) nor the could-exist seed
(`enumerate_expected_universe.py`). This is the still-open **Phase-2 trigger-wiring** todo in
`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (INFRA P1, vm-cross-cutting) — cefi slice cross-referenced
there; no new todo needed beyond the cross-ref.

**G1.run apply-write GATE verdict (cefi) — DRY-RUN ONLY this session. 3 conditions UNMET:**

- (a) IS `_index` canonical (v9) — **UNMET** (cf-audit ① above: 100% v8). Seeding into a pre-canonical `_index` forces a
  banned second walk (master plan: G1.run rides AFTER the AG's G4 manifest is canonical).
- (b) Could-exist universe matches the captured atom — **UNMET** (④ combo+grain bug above; would pollute the
  denominator).
- (c) `--apply-write` also requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` (a VM, not this laptop).

- [x] ✅ [CODE] P0. **`_enumerate_v2_cefi` combo-validity + bundle-grain (OPTION/COMBO) — DONE + verified GREEN (slot-3
      2026-06-08).** Landed on LDR (slot-7 + UAC): `enumerate_expected_universe.py:584` now intersects per
      `instrument_type` via `valid_data_types_for_instrument_type(asset_group, instr.instrument_type)` (a) and
      `_rollup_bundle_grain` (`:1132`, called `:1285`) collapses bundle-grain leaves via `grain_for_instrument_type` +
      `GRAIN_BUNDLE_BY_UNDERLYING` (b); UAC `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` returns
      `("cefi",option/combo)→frozenset()` + `(options_chain/futures_chain)→{trades}` (uac@ae70338d, tested). Dry-run
      re-run 2026-06-08 (3,454 candidates): 0 OPTION/COMBO leaf rows, 8 per-underlying `options_chain` candidates all
      `data_type=trades`, 0 impossible pairs, DERIBIT 11.5% (was 91%) — the combo+grain pollution is FIXED. Shas:
      `uac@ae70338d` · `is@74df991d`/`687d1443` (rollup) · `is@6ea46565` (shape-aware). **The FUTURE bundle-grain
      residual is the separate F2 todo (slot-7 catalogue producer, deliberately venue-specific) — gates only the G1.run
      futures seed, not the G4 migration.** Repo: instruments-service. Provenance: slot-3 G1 dry-run 2026-06-07 + Era-B
      re-validation 2026-06-08.
- [x] ✅ [CODE] P0. **(superseded by the flipped item above — original spec retained for trace)** Fix
      `_enumerate_v2_cefi` combo-validity + bundle-grain before any cefi could-exist `--apply-write` (GATES the ⑦ seed
      above). (a) intersect `data_types` per `instrument_type` against a UAC-sourced valid
      `(instrument_type → data_types)` map (ground-truth: spot/spot_pair→trades/book_snapshot_5/ohlcv\*;
      perpetual→+derivative_ticker/liquidations; future→trades/book_snapshot_5/derivative_ticker/liquidations) so no
      impossible combo (PERPETUAL×options_chain etc.) is seeded; (b) enumerate cefi options/futures at the captured
      **bundle** grain (`options_chain`/`futures_chain` per underlying), NOT per-`OPTION`/`COMBO` catalog instrument —
      mirror the prediction per-cqg granularity-aware producer in
      `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`. +regression: a `PERPETUAL` yields no
      options_chain/futures_chain row; an OPTION yields exactly one bundle row; total candidate count drops to the
      plausible captured-atom universe (not the 91%-DERIBIT inflation). Repo: instruments-service. Provenance: slot-3 G1
      dry-run sample-inspect 2026-06-07. parent_epic: mtds_mdps_master.
- [ ] [DATA] P1. **cefi `instruments-store` `_index` v8→v9 single-walk** (CF-1/3/4/8 RED + 40% null `capture_status` +
      blank `data_type` + 23 legacy-only cells; cf-audit ① above). Owner = the **cefi slice** of
      `instruments_manifest_canonicalisation_2026_06_01.md`; `--apply` **GATED on coordinator G0** (source-aware
      pipeline_mode). Re-run `cf_manifest_audit instruments-store-cefi-prd-…` post-walk → all-CF GREEN. Provenance:
      slot-3 G1 cf-audit 2026-06-07. parent_epic: mtds_mdps_master.

## Proposed fixes for the deferred-with-reason CODE items (slot-3 spec, 2026-06-08)

> Grounded fix specs (file:line, read-only sub-agent investigation on LDR) for every open `[CODE]` item left deferred in
> the pre-apply code-clear. Each is dispatch-ready for its OWNER (slot-3 drafts; the owning slot implements to avoid
> cross-slot collision). None is required before the cefi G4 `--apply`.

### F2 — cefi FUTURE bundle-grain (owner: slot-7 instruments-service) — SMALLER than first scoped

UAC **already ships the venue-aware machinery** (`registry/market_data_categories.py`):
`FUTURE_BUNDLE_VENUES = {"cefi": frozenset({"DERIBIT","OKX"})}` (:696) + `grain_for_instrument_type(ag, it, venue=)`
(:740) + `bundle_instrument_type_for_leaf(ag, it, venue=)` (:771) are all venue-aware and correct. So this is NOT a
"build the rollup from scratch" job — it is two wiring fixes:

- **Change B (minimal, read-side, the urgent one)** — `instruments-service/scripts/enumerate_expected_universe.py`
  `_rollup_bundle_grain` (~:1162-1166) calls `bundle_instrument_type_for_leaf(asset_group, instr.instrument_type)` and
  `grain_for_instrument_type(asset_group, instr.instrument_type)` **without `venue=`** → defaults to `GRAIN_LEAF` for
  every FUTURE → DERIBIT/OKX per-contract futures never collapse → false `expected_unattempted`. **Fix: pass
  `venue=instr.venue` to both calls.** Then DERIBIT/OKX FUTURE leaves collapse to one `futures_chain` bundle per
  underlying; BYBIT stays per-contract. ~2-line change.
- **Change A (producer, secondary)** — `instruments-service/scripts/build_instrument_catalogue.py`
  `build_catalogue_dataframe` (~:230-304, dispatched in `run_rollup` ~:1047): for cefi `future` instruments at
  `FUTURE_BUNDLE_VENUES["cefi"]` venues, group per-underlying → emit a `futures_chain` bundle entry
  (instrument_id=underlying, instrument_type=`futures_chain`, data_type=None, available_from/to = union over contracts)
  instead of N per-contract rows — mirror the prediction multi-grain `build_prediction_catalogue_dataframe` (:373-466).
  Import `FUTURE_BUNDLE_VENUES` from UAC (do NOT duplicate the venue list).
- **Regression**: enumerate tests `test_enumerate_v2_deribit_future_leaves_collapse_to_futures_chain` (one bundle per
  underlying) + `test_enumerate_v2_bybit_future_leaves_stay_per_contract` + OKX parity, next to the existing
  `test_enumerate_v2_option_leaves_collapse_to_one_per_underlying`.
- **Safety pre-apply**: over-seeds ONLY the G1.run _futures_ `expected_unattempted` denominator seed; does NOT touch the
  G4 manifest/data migration.

### execution-service `data/loaders/defi.py:41,77` legacy DeFi raw reads (owner: slot-2 / defi AG)

Mirror the shipped cefi `canonical_paths.build_candidate_raw_tick_paths` for defi. Calling the cefi helper as-is raises
`KeyError("chain")` because UAC `candidate_parquet_paths(asset_group="defi", …)` requires a `chain` kwarg
(`build_defi_partition_path(venue, chain, …)`, partition_paths.py:461-486). **Fix:**

- Add `build_candidate_defi_raw_tick_paths(*, data_type, day, venue, instrument_type, file_stem, legacy_path)` +
  `_resolve_defi_chain(venue)` to `execution_service/data/canonical_paths.py` (after ~:164). Chain resolves from the
  venue string via UAC `parse_defi_venue` (`registry/capability_declarations/_defi.py:947`) with `_STATIC_VENUE_CHAINS`
  fallback for single-chain protocols (LIDO→ETHEREUM, DRIFT→SOLANA). Unresolvable chain → `[legacy_path]` (fail-safe).
- Call sites: `loaders/defi.py` `load_swaps` (~:38-45, `data_type="swaps"`) + `load_liquidity` (~:74-81,
  `data_type="liquidity"`, `instrument_type="pool"`), and the SECOND copy in `data/loader.py` `_build_swaps_paths`
  (~:409-422) + `_build_liquidity_paths` (~:479-492).
- **Regression**: `tests/unit/test_canonical_paths_defi.py` — canonical-first for `UNISWAP_V3-ETHEREUM`
  (chain=ETHEREUM), static-chain `LIDO`, unknown-venue → legacy-only (no crash).

### deployment-api FLAG-1 — multi-source UNION + per-source breakdown (owner: deployment-api / downstream)

`deployment_api/services/data_status_service.py` `_mtds_honest_coverage_for_venue` (~:1770-1838) ALREADY unions across
sources (`dt_rows["date"].unique()`, :1786) + emits a `per_source` `groupby("source")` breakdown (:1803-1811) — shipped
for tradfi. The only gap: `select_primary_available_source` (UAC `canonical/crosscutting/source_priority.py:869`,
already implemented) is imported nowhere → the "winning source" is not annotated. **Fix:** import it, and after building
`per_source`, set `dt_entry["primary_source"] = select_primary_available_source("cefi", dt, available_captured_sources)`
(guarded by `has_source_priority`). No-op for cefi today (single-source `tardis`) until the v9 walk lands the `source`
column — so safe pre-apply.

### deployment-api pipeline_mode dedup + drilldown (owner: deployment-api / downstream)

The venue-level cefi numerator already collapses pipeline*mode (date-unique, :1786), but the **per-instrument** branch
`_per_instrument_coverage` (~:1478+) has no explicit shard-atom dedup → a cell with both `batch_tardis` +
`live*\*`rows for the same instrument+date could double-count. **Fix:** mirror the DeFi chain-breakdown dedup (:5663-5672) —`drop_duplicates(subset=[c
for c in ("venue","data_type","instrument_id","date") if c in
df.columns])`before counting`found_shards`. **Regression**: `test_cefi_pipeline_mode_rows_do_not_double_count`(5 atoms × 2 pipeline_modes → 5, not 10), parity with the DeFi test at`tests/unit/test_chain_breakdown_shards_vs_dates.py:176`. Drilldown filter: `\_apply_pipeline_mode_filter`(:3657) exists but isn't threaded into`\_mtds_honest_coverage_for_venue`— add a`pipeline_modes`
param + call it before the per-dt loop. Safe pre-apply (dedup already correct for the venue-level path; this hardens the
per-instrument path + adds a UI-gated filter).

### deployment-api FLAG-3 — UAT health-summary bucket model (owner: deployment-api / downstream — MODEL decision)

`commentary/pipeline_uat.py` reads `instruments-store-{pid}` / `features-store-{pid}` / `ml-store-{pid}` /
`execution-store-{pid}` (lines ~167/181/195/211, `# CORRECT-LOCAL`) — these are **non-AG aggregate pipeline-health
summary** buckets (suffix = project_id), NOT the per-AG market-data stores (`instruments-store-cefi-<pid>`). A blind
`resolve_bucket_name` swap would point them at wrong/nonexistent per-AG buckets. **Proposed fix (Option A,
SSOT-compliant)**: register 4 flat kinds (`instruments-store-pipeline-health`, …) in
`deployment-service/configs/cloud-providers.yaml` with a `${PROJECT_ID}` template, then replace the 4 f-strings with
`resolve_bucket_name(cloud=…, kind="instruments-store-pipeline-health")` (removes the `# CORRECT-LOCAL` carve-outs, QG
STEP-5.69 clean). Option B = keep the explicit `# CORRECT-LOCAL` exemption + document it. Pure read-side health summary
→ safe pre-apply either way.

### MDPS GAP-7 — `category`→`asset_group` rename in `dependency_checker` (owner: downstream plan GAP-7)

`market-data-processing-service/.../app/core/dependency_checker.py`: rename param `category`→`asset_group` on the 5
public methods (`check_upstream_data_granular`/`_per_shard`/`_batch`, `validate_upstream_data_for_date_range`,
`check_upstream_manifest_has_live_gap`) + `_get_upstream_deps_for_category`→`_for_asset_group` +
`_resolve_upstream_bucket` param + the two dicts `UPSTREAM_DEPS_BY_CATEGORY*`→`_BY_ASSET_GROUP*`. Call-site `category=`
→ `asset_group=` keyword updates in `live_workers.py` (:306), `cli/handlers/process_handler.py` (:253/356/403/569),
`app/core/orchestration_service.py` (:150/264/276/467/545/646/650/667/718/776) + test call sites. **Purely internal to
MDPS — no other repo calls these (no cross-repo collision).** Vocabulary-only; safe pre-apply.

### rebuild within-bounds precision (slot-3 cefi NICE-TO-HAVE)

`market-tick-data-service/.../scripts/rebuild_cefi_manifest.py` `reemit_cefi_honest_absence_rows` (~:501-534)
reclassifies within-bounds empties using only a data_type-guarantee + reason heuristic (no instrument-coverage
awareness). **Fix:** load the IS cefi universe per date (`instruments-store-cefi-prd-{pid}`
`instrument_availability/by_date/day={d}/`, columns
`venue`/`instrument_type`/`instrument_id`/`underlying`/`available_from_datetime`/`available_to_datetime`); before the
`reclassify=` decision, PRESERVE-as-`empty_confirmed` (skip reclassify) when the cell's instrument is outside its IS
coverage window on that date. **Blocked-on**: there is NO cefi known-gap registry yet (UAC `data_source_continuity.py`
covers only tradfi VIX; sports has `is_in_known_gap` — cefi needs an analogue) → the known-gap gate is a no-op stub
until that lands. NICE-TO-HAVE, non-blocking.

### deployment-api per-date denominator (P3) + ⑦ catalog-path seed (operational)

- **per-date denominator (P3)**: `data_status_service` reads ONE current IS snapshot, not per-date `by_date/`
  definitions → switch the provider to the per-date source once `proper_instrument_catalogue_lifecycle_rollup` ships the
  per-date contract. Non-blocking refinement.
- **⑦ catalog-path seed**: the enumerate CODE is DONE (see flipped item); remaining is purely the OPERATIONAL VM run
  (`enumerate_expected_universe.py --asset-group cefi --catalog-path <catalog> --apply-write` on a VM with
  `MANIFEST_PER_VM_SHARDS=true`) — bucket-B apply-time, not a code change.
