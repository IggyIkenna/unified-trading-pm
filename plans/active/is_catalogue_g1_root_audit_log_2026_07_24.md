---
doc_type: plan
title:
  IS catalogue G1-root audit log — G1-ENUM/G1-V8 shape-aware-producer audit trail (extracted from the master
  coordinator)
summary:
  Verbatim IS-catalogue-G1-root audit trail (G1-ENUM shape-aware producer ship, Era-B options/futures-chain
  canonicalisation, the G1-ENUM over-fan false-candidate finding, the G1-V8 v9-migrator "two G1 long poles" analysis)
  extracted from master_data_canonicalisation_migration_catalogue_2026_06_07.md to bring that coordinator back under the
  2000-line umbrella cap.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [coordinator, migration, manifest, data-layer, catalogue, instruments-service, g1, audit-log]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
last_updated: "2026-08-22"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md #16 (bucket-d would-be-(c) split for
    master_data_canonicalisation_migration_catalogue_2026_06_07, operator-approved unlock+fix)",
    "/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md (origin of this content; verbatim
    extraction 2026-07-24)",
  ]
drift_direction: advance-code
context_scope: [/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/02-data/honest-coverage-model.md, instruments-service/scripts/build_instrument_catalogue.py, instruments-service/scripts/enumerate_expected_universe.py, instruments-service/scripts/migrate_instruments_store_v9.py]
---

# IS catalogue G1-root audit log

> **Extracted verbatim 2026-07-24** from `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s
> `## G1 expanded — IS catalogue is the ROOT of all missing-data understanding (operator 2026-06-07)` section, as part
> of the line-cap remediation split (`/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` #16). Lossless
> relocation — no content rewritten or summarized. See `master_data_canonicalisation_migration_catalogue_2026_06_07.md`
> for the live gate-board + dependency DAG this content feeds into (this doc is a historical/audit record, not itself
> gating anything).

## G1 expanded — IS catalogue is the ROOT of all missing-data understanding (operator 2026-06-07)

> **IS (instruments-service) + UAC together define the could-exist universe — every downstream honest denominator,
> preflight (⑥/⑦), and `expected_unattempted` seed reads it. If IS or UAC is wrong, EVERY AG's coverage % is wrong.** So
> G1 is gated, and its catalogue has a full code → dry-run → real-run → schedule lifecycle, tracked per-AG.

> **🟢 G1-ENUM — CODE SHIPPED 2026-06-07 (vm-cross-cutting / slot-7)**: the shape-aware producer is live — UAC validity
> matrix `uac@97c26dbe` (`valid_data_types_for_instrument_type` + `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`, defi
> lazily derived from `PROTOCOL_CAPABILITIES`, uncertain rows flagged for AG owners) + instruments-service enumerator
> `is@6ea46565` (`_row_data_types` filters every `_enumerate_v2_*` to valid pairs + preserves prediction grain-binding;
> cefi OPTION/COMBO leaves → zero per-leaf rows; impossible combos excluded; +12 IS / +32 UAC tests, both repos QG
> green). **Unblocks slots 2-6 G1.run** (each AG owner still verifies its matrix slice + re-runs its dry-run against the
> shape-aware producer before `--apply-write`). Original finding ↓ retained for context.
>
> **✅ ERA-B SHIPPED 2026-06-07 (vm-cross-cutting / slot-7) — `options_chain`/`futures_chain` are now canonical
> INSTRUMENT_TYPES (data_type=trades) in the contracts + producer.** `options_chain`/`futures_chain` are
> INSTRUMENT_TYPES (per-underlying chain bundles) with `data_type=trades`, bundled per-underlying — matching the live
> writer (`tardis_shared.py` Phase 1.6) + the on-disk object paths + the `CEFI_OPTIONS_CHAIN_TRADES` schema
> (symbol=underlying). The earlier rollup (item 1(b) below, `uac@cb3a846b`/`is@687d1443`) was **Era-A-shaped** (emitted
> `data_type=options_chain`); this reconciles it UP to Era-B. **Shipped (each a QG-`--no-fix`-green commit on
> `tab/ikennaigboaka/7`, prek-green, tab ⊇ LDR):**
>
> - **`uac@ae70338d`** — (1) validity matrix: `(cefi/tradfi, options_chain/futures_chain)` → `frozenset({"trades"})`
>   (was `{options_chain}`/`{futures_chain}`); `(tradfi, option/combo)` → `frozenset()` (was UNMAPPED → None fallback →
>   the ~563K false candidates); (2) renamed `bundle_data_type_for_instrument_type` → `bundle_instrument_type_for_leaf`
>   (returns the bundle INSTRUMENT_TYPE; the data_type resolves to `trades` via the matrix); (3) `SOURCE_PRIORITY` +
>   `capability_declarations/_cefi.py`+`_tradfi.py`: Era-B docs (the bundle resolves source via `(ag, "trades")`; the
>   legacy data_type-keyed `options_chain`/`futures_chain` entries are RETAINED for pre-migration legacy rows + the
>   bidirectional `SOURCE_PRIORITY ↔ AVAILABILITY_AT_SEMANTICS` closed-set round-trip — the per-AG v9 migrators own
>   their removal, see follow-up todo); (4) flipped the Era-A matrix/schema tests to Era-B; `CEFI_OPTIONS_CHAIN_TRADES`
>   schema unchanged.
> - **`is@74df991d`** — `enumerate_expected_universe._rollup_bundle_grain`: the synthetic bundle entry now carries
>   `instrument_type=options_chain`/`futures_chain` + `data_type=None` → the enumerator resolves its data_type from the
>   validity matrix → emits ONE candidate per underlying with **`data_type=trades`** (NOT `data_type=options_chain`).
>   Tests flipped to assert `(underlying, options_chain, trades)`.
>
> Regression verified by the QG suite (both repos `quality-gates.sh --no-fix` exit 0; UAC 3264 + IS 3267 tests green):
> OPTION/COMBO leaf → **0** per-contract candidates; underlying → **exactly one** `options_chain`/`futures_chain`
> candidate with `data_type=trades`; PERPETUAL/SPOT unchanged; **no `data_type=options_chain` emitted**; tradfi
> option/combo no longer fall through to the all-data_types fallback. **🔔 NOTIFY slots 3 (cefi) + 6 (tradfi): the Era-B
> shape-aware producer is GREEN — re-run your `enumerate` dry-runs to confirm the prod numbers (tradfi ~588K →
> plausible, ~563K false GONE; cefi DERIBIT no longer dominant) before `--apply-write`; flip each AG's matrix slice
> verify row.** **BLOCKED-PROMOTION**: the LDR→`staging` promotion is gated on the workspace **staging lock** (breaking
> MINOR bump cascade, `instruments-service=0.2.0`, locked since 2026-06-07T16:59Z) — both commits are QG-green on the
> tab branch (→ LDR via the tab-mirror); the staging→main promotion flows via the automation once the cascade
> converges + unlocks. **OUT OF SCOPE (per-AG migrators own)**: the v8→v9 manifest relabel of legacy
> `data_type=options_chain` rows.

> **🔴 G1-ENUM (P0, CROSS-AG, surfaced by slot-3 cefi dry-run 2026-06-07) — the v2 enumerator over-fans → false
> `expected_unattempted` pollution.** `_enumerate_v2_*` (`enumerate_expected_universe.py`) fans ALL `data_types` over
> EVERY instrument with **no `(instrument_type × data_type)` validity filter and no bundle-grain handling**. cefi
> ground-truth: options/futures are captured as per-underlying `options_chain`/`futures_chain` BUNDLES (~0 per-OPTION /
> per-COMBO rows), yet the catalog has 72,156 OPTION + 17,472 COMBO → `OPTION/COMBO × 7 data_types` never match the
> present-set + impossible combos (`PERPETUAL × options_chain`). An `--apply-write` now would seed **millions of false
> `expected_unattempted` rows → distort the exact denominator G1 exists to make honest.** The dry-run caught it
> pre-write. **This is the SAME root as slot-4's sports finding** (generic producer is fixture-grain, sports atom is
> league-grain; prediction already solved it with a per-cqg granularity-aware producer). **Cross-AG**: the
> `for dt in data_types` no-filter pattern is in EVERY `_enumerate_v2_*`. **FIX (owner: slot-7 G1-foundation in
> instruments-service)**: the generic producer becomes instrument-shape-aware — `(instrument_type × data_type)` validity
> filter + bundle-grain (mirror the prediction per-cqg producer); **each AG owner (slots 2-6) verifies their slice**
> before any G1.run apply-write. **Gates every AG's `--apply-write` seed** (a G1 prerequisite). Tracked: P0 in cefi
> plan + must land in `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (central fix) + a verify-slice todo in
> each AG plan. **Re-scopes WAVE-1 slot-7**: the "generic foundation" must be AG-shape-aware, NOT one-size fan-out.
>
> **✅ G1-V8 (P0, cross-AG, the SECOND G1 long pole): the instruments-store v9 MIGRATOR IS BUILT 2026-06-07
> (`is@febb899e`) + dry-run-green for all 5 AGs — see "Two G1 long poles" item 2 below. The `--apply` RUN stays G4-gated
> per-AG. Historical context (now RESOLVED):** Confirmed v8 across **cefi (100% v8), sports (v8), tradfi (0.8% v9 /
> 20,218 rows v8)** — and slot-6 found the fix is "a gated G4-class single-walk `--apply` with **no migrator built yet**
> (instruments_manifest **E2**, vm-cross-cutting)". So gate-c (v9 `_index`) is UNMET for every AG **because the tool to
> fix it hasn't been written**. This gates EVERY AG's G1.run apply-write alongside G1-ENUM. **Owner: vm-cross-cutting
> must BUILD the `instruments_manifest` E2 v9 single-walk migrator**
> (asset_group=/pipeline_mode=batch\*<source>/source/transport/ available_at/typed data_type) for the instruments-store
> buckets — the analogue of the per-AG MTDS migrators, which don't exist for the IS reference surface. Until it lands,
> no AG's instruments-store goes v9 → no honest G1 seed. Tracked: `instruments_manifest_canonicalisation_2026_06_01`
> (must spawn the E2 migrator) + each AG plan's §H.

**Two G1 long poles gate every AG's `--apply-write` seed (both cross-cutting, both must land first):**

1. ✅ **G1-ENUM — CODE DONE 2026-06-07** — in TWO parts (the WAVE-1 claim "validity filter + bundle-grain" was
   inaccurate: `is@6ea46565` shipped ONLY the `(instrument_type × data_type)` VALIDITY FILTER + sports league-grain
   (`is@99a5fbf5`); the OPTIONS/COMBO BUNDLE-GRAIN ROLLUP did NOT ship — slot-6 re-ran tradfi on `6ea46565` and got only
   −808, ~563K false per-contract candidates remained):
   - **(a) validity filter** — `uac@97c26dbe` matrix + `is@6ea46565` producer (impossible
     `(instrument_type × data_type)` pairs filtered; per-leaf OPTION/COMBO zeroed via `frozenset()` — but that
     UNDER-seeds bundles to zero).
   - **(b) bundle-grain ROLLUP (the real fix) — SHIPPED 2026-06-07 (slot-7); ERA-A-shaped, reconciled to ERA-B by
     `uac@ae70338d`/`is@74df991d` — see the "✅ ERA-B SHIPPED" block above**: `uac@dd7fa100` (GRAIN axis SSOT
     `grain_for_instrument_type`) + `uac@cb3a846b` (`bundle_data_type_for_instrument_type` + tradfi grain) +
     `is@687d1443` (`enumerate_expected_universe._rollup_bundle_grain` — read-side pre-pass in `enumerate_v2` collapses
     every option/combo LEAF of a `(venue, chain, underlying)` into ONE synthetic per-underlying `options_chain`
     candidate; generalises slot-4's league-grain rollup, NO per-AG special-casing; `underlying` carried on the
     catalogue +`InstrumentCatalogEntry`, derived from instrument\*id as fallback) + `is@df15dba2` (contract tests).
     Net: OPTION/COMBO leaf → ZERO per-contract candidates; underlying → exactly ONE chain candidate. **(b) originally
     emitted `data_type=options_chain` (Era-A); the Era-B reconciliation (`uac@ae70338d`/`is@74df991d`) flips that to
     `data_type=trades` — the chain name is the instrument_type, the market data_type is trades.** (kills the ~563K
     tradfi over-fan + cefi DERIBIT dominance). **🔔 slots 3 (cefi) + 6 (tradfi): re-run `enumerate` dry-runs on the
     Era-B rollup producer to confirm (tradfi ~588K → plausible; cefi DERIBIT no longer dominant) — you were gated on
     this.** ✅ **F2 residual — RESOLVED (uac@e3dcd868 + instruments-service enumerate threading, slot-7 2026-06-08)**:
     the DERIBIT/OKX FUTURE-leaf per-contract over-fan is fixed by the **sound venue registry** `FUTURE_BUNDLE_VENUES`
     (`registry/market_data_categories.py`) — `grain_for_instrument_type` / `bundle_instrument_type_for_leaf` now take
     an optional `venue`: a bare FUTURE leaf bundles to a per-underlying `futures_chain` ONLY at DERIBIT/OKX, and stays
     per-contract at BYBIT (the unsound `VENUE_DATA_TYPE_CAPABILITIES` discriminator is NOT used). `enumerate_v2`'s
     `_rollup_bundle_grain` threads `instr.venue`; +8 UAC tests + 3 enumerate tests (DERIBIT/OKX bundle, BYBIT leaf).
     Kills the ~700 false DERIBIT/OKX per-contract FUTURE candidates while keeping BYBIT honest. **🔔 NOTIFY slots 3
     (cefi) + 6 (tradfi): re-run your `enumerate` dry-runs on the venue-aware producer — the DERIBIT/OKX FUTURE over-fan
     is gone (cefi 880→~180 per-underlying).** Per-AG slice verification + dry-run re-run still owed by each AG owner
     before `--apply-write`.
2. ✅ **G1-V8 — MIGRATOR BUILT + DRY-RUN GREEN (all 5 AGs) 2026-06-07** (`is@febb899e`,
   `instruments-service/scripts/migrate_instruments_store_v9.py`). AG-parametric single-walk that rewrites BOTH the
   instruments-store `_index` rows AND object paths to canonical v9 (CF-1 v9 · CF-2 `asset_group=` · CF-3
   `pipeline_mode=batch_instruments_service` · CF-4 `source=instruments_service` · CF-TRANSPORT `transport=rest` · CF-5
   typed reasons · CF-7 `data_type` · CF-8 `available_at` · CF-9 `resolve_bucket_name` · CF-10 honest `capture_status`
   from `instrument_count`). DRY-RUN validated on all 5 real prod `_index` files (cefi/defi/tradfi/sports/prediction →
   100% v9 projection). 14 credential-free unit tests; QG `--no-fix` exit 0. The `--apply` RUN stays G4-gated
   (coordinator G0 + Phase-0 writer-code + pre-migration drain; each AG owner runs its bucket's `--apply`). Sports is
   structural-only (its `capture_status`/reasons are enumerator-authoritative → sports plan owns the relabel). So gate-c
   (v9 `_index`) is now **TOOL-READY** for every AG; what remains is each AG's gated `--apply` run.

**Per-AG G1 status (WAVE-1 dry-runs):**

- **cefi (slot-3)**: ✅ **APPLY-READY (2026-06-08)** — Era-B + bundle-grain rollup LANDED (`uac@ae70338d`
  options_chain/futures_chain → `{trades}` + `is@74df991d`/`687d1443` read-side `_rollup_bundle_grain`; **F1 Era-B
  recommendation adopted**). **Enumerate RE-RUN GREEN** = **3,454 candidates**: 0 per-leaf OPTION/COMBO; **8
  `options_chain` candidates, ONE per underlying (DERIBIT BTC/ETH option+combo), all `data_type=trades`** (no
  `data_type=options_chain`); 0 impossible pairs; **DERIBIT 11.5%** (no longer dominates). Migrators + instruments-store
  v9 (30,803→100% v9) re-confirmed GREEN; 7+2 audit green (CF-1…13 ✓; CF-14 options-bundle ✓). **UAC slice verified
  correct — no change.** 🟡 **ONE residual = F2 (slot-7-owned, NOT a G4 blocker)**: `FUTURE` not rolled up (slot-7
  DELIBERATELY omits `future→futures_chain`, venue-specific: DERIBIT/OKX bundle vs BYBIT per-contract) → 880
  per-contract FUTURE candidates (700 DERIBIT/OKX = false over-seed) — over-seeds only the **G1.run futures seed**, fix
  = slot-7 venue-aware `build_instrument_catalogue` rollup. **Remaining gates are OPERATIONAL only**: instruments-store
  v9 walk RUN · IS backfill · Era-B legacy relabel (rides G4, operator `slot-7 edca81b57`) · pre-migration drain · F2
  (slot-7). Full verdict in (archived) `plans/archive/2026_07/cefi_manifest_canonicalisation_2026_06_01.md` § "cefi
  APPLY-READY" (folded→M-1, archived 2026-07-13, finding 197). 🟢 G3 ✓ · G0 ✓. **🔁 12-POINT PRE-APPLY RE-VERIFICATION
  (slot-3, 2026-06-08, real-prod data-state):** ①–⑫ re-run on real GCS (migrate/ rebuild/enumerate dry-runs + `_index`
  byte-probes; MTDS cefi `_index`=2.64M rows 100% v8 pre-migration confirmed). **G4 data/manifest migration =
  APPLY-READY, REGRESSION RISK NONE** (⑪ batch=live byte-identical; ②/① no double-count/no loss — copy-not-move safe via
  rebuild dedup + migrate-before-rebuild; ⑤/⑨/⑩/⑫ 🟢). **TWO honest-coverage gates surfaced (NOT G4 blockers): ⑧ 🟡 IS
  cefi reference universe lists only 12 venues — KRAKEN-SPOT/FUTURES (107K captured rows, on-disk-real) +
  BITFINEX-SPOT + PACIFICA + LIGHTER absent ⇒ catalogue ⊉ present-set ⇒ falsely-high coverage. **ROOT CAUSE = IS Tardis
  adapter `_DEFAULT_EXCHANGES` stale 8-id subset drifted below SSOT `VenueMapping.all_tardis_exchanges`; 🟢 CODE FIX
  SHIPPED `is@a6bc4d48` (derives from SSOT + regression tests).** Remaining = operational IS reference backfill re-run +
  CLOB venues (PACIFICA/LIGHTER) — owner `instruments_backfill_phase3`; **⑦(a) 🟡 deployment-api cefi coverage
  denominator re-derives genesis/launch instead of READING `expected_unattempted`\*\* (correct pre-seed; switch post
  enumerate `--apply-write` — owner: deployment-api/downstream). Both tracked as todos in the cefi plan § "PRE-APPLY
  12-POINT AUDIT VERDICT".
- **sports (slot-4)**: **WAVE-2 dry-runs GREEN (2026-06-07)** — G1-ENUM league-grain producer DONE (is@99a5fbf5) +
  AG-specific producer present; **fixed a real G1-ENUM bug: the UAC `("sports","league")` validity slice silently
  dropped `ODDS` → now derived from `SPORTS_DATA_TYPE_TO_SOURCE` (uac@aff80339/PR#95)**. G1-V8 instruments-store v9
  dry-run GREEN (2.68M → 100% v9, `asset_group`/`source`/`transport`/`available_at` all stamped,
  `pipeline_mode=batch_<source>`). MTDS migrator object-path dry-run GREEN (source-aware `batch_odds_api`,
  `category`→`asset_group`). `--apply` gated (G0 + IS v9 walk + IS backfill + 2 data-state findings: 6,869 blank
  `capture_status` + mdps consolidated-index-reads-0). Full verdict: `sports_manifest_canonicalisation_2026_06_01.md` §
  "G2 WAVE-2 readiness verdict".
- **tradfi (slot-6)**: catalogue + enumerate dry-run mechanism GREEN (588,798 candidates) — BUT this ran on the OLD
  over-fanning producer (predates G1-ENUM) → **re-validate the candidate set against slot-7's shape-aware producer**
  (tradfi is per-contract so less bundle-affected than cefi, but impossible-combo filtering still applies). gate-b
  (capture FROZEN — catalogue marks ~651K delisted) **remediated**: slot-6 shipped the **Massive IS reference adapter**
  (uac@12974b11/#91 + is@6ea46565/#407, auto-merging to staging) so tradfi reference data is no longer frozen. gate-c
  (v9) still blocked on G1-V8.
- **defi (slot-2)**, **prediction (slot-5)**: prediction's per-cqg producer is the G1-ENUM reference; both still owe
  their v9 walk (G1-V8) + dry-run.

**The could-exist universe = (IS instrument lifecycle catalogue) × (UAC availability rules).** The two halves:

- **IS half — the lifecycle catalogue** (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04`):
  `build_instrument_catalogue.py` rolls up the maintained per-date
  `instrument_availability/by_date/day=…/venue=…/ instruments.parquet` defns into the cumulative
  `available_from`/`available_to` lifecycle catalogue, which `enumerate_expected_universe.py` (v2) cross-joins × dates ×
  data_types − existing manifest rows → seeds `record_expected_unattempted` for IS-listed-but-not-yet-backfilled cells.
- **UAC half — the availability rules**: chain genesis dates, `DEFI_VENUE_LAUNCH_DATES` / per-AG venue launch, listing/
  delist windows, `SOURCE_PRIORITY`, `expected_coverage()` scope — these tell the enumerator WHEN a listed instrument is
  genuinely expected to have data (post-genesis, post-launch, in-coverage). UAC accuracy is a HARD G1 input.

**G1 catalogue lifecycle (tracked stages — each per-AG, on a VM where it touches prod GCS):**

- [ ] [CODE] P0. **G1.code — catalogue producer + enumerator GREEN** (`build_instrument_catalogue.py` +
      `enumerate_expected_universe.py` v2, defi/cefi/tradfi/sports/prediction-capable; `resolve_bucket_name` env-tier
      fix). Owner: `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (vm-cross-cutting) + per-AG slices of
      `instruments_manifest_canonicalisation_2026_06_01`. **DeFi (slot-2): code-ready + denominator regression shipped
      is@bb8fb203** (⑦-defi). cefi dry-run proven 2026-06-05.
- [ ] [DATA] P0. **G1.dry-run — per-AG catalogue + enumerate dry-run** (read-only; **cefi RE-RUN on shape-aware producer
      DONE slot-3 2026-06-07** — enumerate v2 exit 0, 3,446 plausible candidates, OPTION/COMBO bundle-skip working;
      residual F1 chain-`data_type`-axis + F2 FUTURE bundle-grain gate apply-write, see cefi plan § "G2 VERIFY PASS";
      defi pending — each AG slot runs its own). **sports DRY-RUN DONE (slot-4, 2026-06-07): generic
      `build_instrument_catalogue --asset-group sports` → 0-row catalogue (raw entity cols lack
      `instrument_key`/`instrument_id`; no `sports` branch in `run_rollup`) AND captured atom is per-LEAGUE not
      per-fixture → needs a league-grain `build_sports_catalogue_dataframe` producer before enumerate v2 can run. Full
      finding + spec + gate flags in `sports_manifest_canonicalisation_2026_06_01.md` § ⑦.** **prediction DRY-RUN DONE
      (slot-5, 2026-06-07): found+fixed a crash — `build_instrument_catalogue` resolved the prediction instruments-store
      via the per-AG dict (no PREDICTION entry → `BucketNamingError`) so the cqg roll-up never ran; fix=flat-kind helper
      `is@a7fa55a8` (+regression test). With that, `--asset-group prediction --dry-run` runs exit 0 → 0 cqg rows, GATED
      on the IS prediction backfill (`market_lifecycle/by_canonical_group/`=0 objects;
      `instrument_availability/by_date/` is `market=`-grain, no `canonical_question_group=`). enumerate rides the
      catalogue (same gate). cf_manifest_audit(instruments-store-pred): 493 rows 100% v8, CF-1/3/4/8 RED (§H v9 walk
      gated). G1.schedule WIRED (prediction in both catalogue schedulers). Full finding in
      `plans/archive/2026_07/prediction_manifest_canonicalisation_2026_06_01.md` § ⑦ G1-2026-06-07 (folded→M-1, archived
      2026-07-13, finding 197).** **tradfi DRY-RUN DONE (slot-6, 2026-06-07):
      `build_instrument_catalogue --asset-group tradfi` rolls up 11,579 `by_date` parquets (full local run = VM job,
      timed out ~10min; producer already proven — slot-7 applied `prod/catalog.parquet` = 684,372 instruments, 95%
      delisted = capture-freeze signature). `enumerate_expected_universe v2 --catalog-path <prod/catalog.parquet>`
      scan-only (2026-06-04..05) exit 0 → **588,798 candidate `expected_unattempted`** (= 32,711 alive × 9 data_types ×
      2 days; present-set 73,352/144,062), sample-inspected (e.g. `CBOE:INDEX:VIX × {trades,ohlcv_1m,…}`). **RE-RAN on
      the G1-ENUM shape-aware producer (@6ea46565) 2026-06-07 → 587,990 (barely dropped, −808). 🔴 gate-(a) RED —
      ROOT-CAUSE: tradfi options/combos are captured at BUNDLE grain (manifest: 0 per-contract OPTION rows;
      options_chain 3,262 + combo 58,292 + futures_chain 15,600) but the catalogue + enumerate are PER-CONTRACT (622K
      OPTION) → ~563K false candidates (grain mismatch). Needs G1-ENUM BUNDLE-GRAIN rollup for tradfi (catalogue emits
      options_chain/futures_chain bundles + matrix `option/combo→frozenset()`, mirror cefi) — co-owned slot-6+slot-7;
      validity matrix alone insufficient.** cf_manifest_audit(instruments-store-tradfi-prd): 20,388 rows 0.8% v9,
      CF-1/3/4/8 RED + 60 legacy-only (§ Step-1 v9 walk **BLOCKED on the G1-V8 instruments_manifest E2 migrator
      BUILD** + G0). **G1.run apply-write GATED** (a RED bundle-grain; b: capture freeze; c: v9 indices/migrator-build)
      → dry-run only; gate-b remediation Massive IS adapter SHIPPED + **STAGING-GREEN** (UAC@12974b11 PR#91 MERGED +
      IS@c0f2f39c PR#407 MERGED, both quality-gates-v2 PASS). **G1.schedule: tradfi MISSING from both catalogue
      schedulers' instruments-store `for_each` → gated todo filed.** Full finding in
      `plans/archive/2026_07/tradfi_manifest_canonicalisation_2026_06_01.md` § G1 (folded→M-1, archived 2026-07-13,
      finding 197).**
- [ ] [DATA] P0. **G1.run — per-AG `--apply-write` of the could-exist seed against the AG's canonical `_index`** (VM;
      `MANIFEST_PER_VM_SHARDS=true`). **GATED on**: (a) **IS instrument BACKFILL complete** for that AG
      (`instruments_backfill_phase3_2026_05_22` — the catalogue can only roll up instruments IS actually fetched); (b)
      **accurate UAC** (launch/genesis/coverage rules for that AG verified — else the seeded expected set is wrong); (c)
      **`instruments_manifest_canonicalisation` v9** for the AG's instruments-store `_index`. NOTE: G1.run seeds the
      manifest **could-exist** rows but the canonical `_index` itself comes from the AG's G2 walk — so G1.run for
      raw-tick denominators rides AFTER that AG's G4 manifest is canonical (the catalogue-of-record vs the seed are
      sequenced in the per-AG plan; do not double-walk).
- [x] ✅ [INFRA] P0. **G1.enumerator-cron — the v2 `--apply-write` SECOND HOP is now cron-wired** (the missing half of
      G1). AUDIT 2026-06-19: `expected_unattempted` was **0 rows in EVERY IS+MTDS `_index` fleet-wide** — the catalogue
      regen was cron-wired (`lifecycle_catalogue_scheduler.tf`) but NOTHING consumed it with `--apply-write` (the v2 VM
      launcher was one-shot, `last_executed: NEVER`). Closed:
      `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf` — per-AG Cloud Run Job + Scheduler @01:30 UTC
      (after 01:00 catalogue regen), bounded recent window (`EXPECTED_UNIVERSE_START_DATE`, ~120d), per-VM shard
      `_index/per_vm/enum-universe-v2-<ag>.parquet` (consolidator-merge-safe). — deployment-service@`c90ea48` |
      **`tofu apply` PENDING-OPERATOR** (TF authored + validated against the proven `lifecycle_catalogue_scheduler.tf`
      shape; apply rides the next prod tofu run like the G1.enumerator-cron sibling above). ⚠️ idle-AG consolidator trap
      noted in the TF + issue `consolidator_idle_bucket_incremental_trap_2026_06_19.md` (needs companion
      force-consolidate / consolidator fix).
- [x] ✅ [DATA] P0. **G1.run-bounded — v2 `--apply-write` materialised the LIVE-window could-exist seed for 4 AGs**
      (manual run 2026-06-19, window 2026-02-20→today, per-VM shard → consolidator-merged, eu = `expected_unattempted`
      4th-state rows): **defi eu 2,307,358** · **cefi eu 482,114** · **tradfi eu 818,311** · **sports eu 1,027,396**
      (was 0 fleet-wide). Captured PRESERVED post-merge (defi 367,567 / cefi 1,311,984 / tradfi 102,936 / sports
      659,693). cefi/tradfi needed a manual `consolidate(force=True)` (idle-bucket trap). Ran existing
      `enumerate_expected_universe.py` v2 — no code change. Concurrent-safe with the live tradfi instruments-backfill
      VMs (different per-VM shards). **Correctness caveat (added 2026-07-14, verify-rerun-2 finding 153)**: this same
      run is the seed the still-open "G1-ENUM present-set asymmetry" coordination todo below (found 2026-06-08, tradfi
      pre-apply audit) flags as carrying PHANTOM `(options_chain|futures_chain, trades)` `expected_unattempted` cells
      for cefi + tradfi specifically — so the cefi/tradfi `eu` counts above are known-inflated until that todo ships a
      fix; DONE means "seed materialised", not "seed correctness verified" for those 2 of the 4 AGs.
- [ ] [DATA] P1. **G1.run-prediction — grain.** The prediction catalogue is per-conditionId (870,987 markets) but the
      MTDS manifest is ~19,639 rows at the cqg/market grain → a per-conditionId v2 seed emits >50M rows that NEVER match
      the present-set (every cell a false `expected_unattempted`). Prediction `expected_unattempted` must seed at the
      **cqg-bundle grain** (`prediction_canonical_question_group`). **No longer `BLOCKED-OPERATOR-DECISION` (retagged
      2026-07-28, investigated per `autonomous_session_operator_decisions_2026_07_25.md`)**: the operator-decision fork
      this todo cited — "decision 338" — is the classifier registry-EXTENSION ruling (extend `canonical_question_group`
      coverage vs. leave unmatched markets unclassified), NOT a separate ruling on seeder grain; it was ratified +
      implemented 2026-06-16. **SHA CORRECTED 2026-08-19** (`/plan-reconcile manifest_master`): the previously-cited
      `unified-api-contracts@d4523602` is WRONG — verified via `git log -1 d4523602` it is dated 2026-07-16 (a month
      later) and is an unrelated logging-level perf fix, not a decision-338 commit. The real decision-338 sequence,
      all dated 2026-06-16 and all tagged `(decision 338)` in their own commit messages (cross-confirmed against
      `infra_ops_residual_migration_verification_2026_07_24.md`'s independent citation of the same 3 SHAs), is
      `unified-api-contracts@d52217f`+`e0035fd`+`8e3108d` — see that doc for the per-commit breakdown; not
      independently re-verified here whether these 3 specifically cover the "OTHER-catch-all" sub-change this
      sentence originally attributed to the wrong SHA. and independently
      re-confirmed 2026-07-26/27 (`autonomous_session_operator_decisions_2026_07_25.md` entry #14;
      `/plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md` todo 1;
      `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch5_2026_07_26.md` "Why this batch exists") —
      `ClassifierConfidenceLow` measured 0.0000% for BOTH venues, so there is no remaining open operator fork on cqg
      coverage. **Confirmed via the SAME resolution already applied to the identical registry-copy of this todo** in
      `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` § "Deferred work — migrated to:"
      item 1 (retagged there 2026-07-28 — this file's own copy was simply never updated to match). **Still genuinely NOT
      dispatchable as an `--apply-write` today, but for an ENGINEERING reason, not an operator one**: the IS
      catalogue-rollup loader still yields `cqg_str=""` (confirmed 2026-07-27, `prediction_cqg_residual_2026_07_24.md`
      todo 2 / `prediction_satellite_ao_dispatch_batch5_2026_07_26.md` todo 2, both still open as of this edit) — until
      that loader wiring lands, a cqg-bundle-grain seed would still emit against an empty grain. **Do NOT
      `--apply-write` prediction v2 at conditionId grain** (unchanged). Named successor for the loader-wiring
      prerequisite: `prediction_cqg_residual_2026_07_24.md` todo 2 (repos: instruments-service, unified-api-contracts);
      once that lands, this todo's cqg-bundle-grain seed run is normal AO-dispatchable engineering work
      (`enumerate_expected_universe.py` at cqg-bundle grain), no further operator input needed. **na-eligibility-audit
      2026-08-03**: the loader-wiring prerequisite has now landed — `prediction_cqg_residual_2026_07_24.md` is archived
      `status: complete` ("todo 2 (249-b, cqg grain) shipped and flipped", 2026-07-29,
      `unified-api-contracts@283d7449` + `instruments-service@38e393de`, `quality-gates.sh` green both repos). That same
      doc explicitly notes "Prod `catalog.parquet` promotion explicitly NOT run... carried by
      `prediction_phase_ab_residuals_2026_07_24.md`'s gated regen" — so the actual cqg-bundle-grain seed run this
      checkbox asks for is still not executed; not flipping here, the AO-dispatchable seed-run work now lives (or should
      be tracked) in `prediction_phase_ab_residuals_2026_07_24.md` (active).
- [x] ✅ [DATA] P2. **DONE 2026-08-11/16 (batch2 reconciliation)** — G1.run-full-history: extended the bounded-window
  `expected_unattempted` seed to the full 2018→today universe, via VM `--apply-write` (no single commit — VM-launched
  batch seeding per `launch-expected-universe-v2-historical-backfill-vm.sh`). All 5 AGs fully seeded + post-run
  verified: cefi 11,516,896 eu (captured 5,627,008 preserved); tradfi 450,743 eu (captured 4,676,872); prediction 5,475
  eu (cqg-bundle-grain, captured 428,289); sports 2,510,499 eu (captured 2,260,520); defi 38,894,569 eu total
  2018-2026 (VMs `expected-universe-v2-defi-20260810-212538` [2025: 17,578,560 rows] +
  `expected-universe-v2-defi-20260810-225807` [2026H1: 2,358,166 rows]). Final verify 2026-08-11: 0 pending shards,
  consolidator `streak=0`. Was: EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`
  (archived).
- [x] ✅ [INFRA] P1. (**APPLIED 2026-06-11, autonomous run** — `tofu apply` vs `terraform/state/prod`: **16 added / 0
      changed / 0 destroyed**; all 5 `lifecycle-catalogue-regen-<ag>` Cloud Run jobs + 5 ENABLED 01:00-UTC schedulers
      verified via `gcloud run jobs list`/`scheduler jobs list`; cefi smoke execution triggered + watched. THREE
      pre-existing tf bugs fixed to get there: (1) bucket literals were LEGACY/nonexistent → canonical env-short
      `-prd-`/`pred` (deployment-service@9e2904a); (2) main.tf had 7 MERGE-DOUBLED `instruments_*` bucket resources —
      the whole prod config was UN-PARSEABLE for everyone (second set proven strict-subset, deleted); (3)
      `cf_manifest_audit` alert policy used `labels` (not in schema) → `user_labels` — both
      @deployment-service@04e3d20.) **G1.schedule — daily catalogue-aggregation scheduler live per-AG** keyed to the IS
      update cadence. **TF AUTHORED deployment@98bee4b** —
      `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf` (NEW): per-AG `for_each`
      (cefi/defi/tradfi/sports/prediction) Cloud Run Job + Scheduler running `build_instrument_catalogue.py` (sports
      carries `--by-date-prefix`), 01:00 UTC, terraform-fmt clean. **Finding (vm-cross-cutting 2026-06-07)**: the two
      PRE-EXISTING schedulers (`catalogue_regen_scheduler.tf` + `instrument_catalogue_scheduler.tf`) run DIFFERENT
      scripts (UAC envelope/availability + `generate_instrument_catalogue.py`) — NEITHER ran the
      `build_instrument_catalogue.py` lifecycle roll-up, so this is a NEW scheduler, not a per-AG extension of cefi.
      **REMAINING (apply-gated)**: `terraform apply` + T+10min per-AG `gcloud run jobs executions` verify (infra apply
      pipeline) → then GREEN. Bucket-name `pred`-vs-`prediction` discrepancy flagged in the .tf header. **VERIFIED on
      LDR 2026-06-07 (slot-7)**: `lifecycle_catalogue_scheduler.tf` carries all 5 AGs
      (cefi/defi/tradfi/sports/prediction) — the G1 daily catalogue scheduler is AG-complete; `terraform apply` is the
      only remaining (gated) step.
- [x] ✅ [INFRA] P2. **catalogue_regen_scheduler.tf MISSING tradfi — DONE (deployment-service@a27b05a, slot-7
      2026-06-08)**: added `instruments-store-tradfi-central-element-323112` to the `catalogue_regen_instruments_reader`
      `for_each` IAM grant (+ the doc comment) so the regen job's `strategy_instruments` join can read the tradfi
      instruments-store parquet (the sibling `lifecycle_catalogue_scheduler.tf` + `instrument_catalogue_scheduler.tf`
      already had it). `terraform fmt -check` clean. The `terraform apply` is the gated infra step (out of scope here).
      Repo: deployment-service `terraform/gcp/catalogue_regen_scheduler.tf`.

**Cross-AG IS references (each AG owns its instruments-store reference surface — sliced, not duplicated):** defi §H
`instruments-store-defi` walk · sports `instruments-store-sports` (2.68M rows + the 316-cell legacy→prd data-loss-gated
migration) · cefi/tradfi/prediction reference surfaces — all sub-items of
`instruments_manifest_canonicalisation_2026_06_01` (the per-service all-AG plan) + each AG's
`*_manifest_canonicalisation` §H slice. **G2 (an AG's MTDS/data walk) must NOT be trusted as denominator-complete until
that AG's G1 (IS catalogue + UAC) is GREEN** — the audit's ⑧ enforces this.

## Deferred work — migrated to:

- G1.run-prediction (per-conditionId grain): **no longer migrated/BLOCKED-OPERATOR-DECISION as of 2026-07-28** — see the
  todo's own updated text above. The operator-decision fork (decision 338) is ratified; the remaining gate is the IS
  catalogue-rollup loader wiring (`prediction_cqg_residual_2026_07_24.md` todo 2), tracked there, not a
  `predictions_master` Phase 3 operator decision.
- G1.run-full-history (extend bounded-window seed to full 2018→today): **STALE, corrected by plan_reconciler
  2026-08-10** — this line said "still owned + open in this plan" but the item's own entry above (in the todos list)
  shows it was EXTRACTED 2026-08-09 to `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`. Live-verified: that
  doc's line 502 carries the item, open, citing this doc by name as its source. Migrated to:
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.

## Progress Log

- **2026-07-28 (gate-cleanup pass)**: retagged the `G1.run-prediction` todo — its cited "decision 338 /
  `predictions_master` Phase 3" operator-decision fork is ratified (2026-06-16, re-confirmed 2026-07-26/27; see the
  todo's own updated text + `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` § "Deferred
  work — migrated to:" item 1, which already carried the identical retag). Investigated via
  `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md` — decision 338 is NOT numbered as an item in
  that file (its own numbering runs 1-38); its content is documented instead at entry #14 (the `OTHER` vs
  `attempted_failed` ratification) plus `prediction_satellite_ao_dispatch_batch5_2026_07_26.md`'s detailed
  reconstruction of what "decision 338" actually ruled (classifier registry EXTENSION, not seeder grain). No `--apply`
  run; the todo remains genuinely un-dispatchable for an engineering (not operator) reason — the IS catalogue-rollup
  loader wiring (`prediction_cqg_residual_2026_07_24.md` todo 2) is still open.
- **2026-07-25**: `execution_scope` corrected `orchestrator-agent` → `local-only` to match `assigned_vm: NA`
  (`task_template.md`'s two valid paired tracks: LOCAL = NA+local-only, AO-DISPATCHED = planning+orchestrator-agent).
  Functionally inert either way — `assigned_vm: NA` alone already yields an empty owning-VM set in `_resolve_plan_vms`
  (`agent-orchestrator/server/regen_backlog_from_plan.py`), so this plan was never ingested — corrected for internal
  consistency. The same mismatch recurs on 4 sibling 2026-07-24 fork plans (`infra_ops_residual_migration_verification`,
  `sports_prelaunch_cf5_verify_residual`, `prediction_cqg_residual`, `defi_venue_lst_rates_residual`), fixed in the same
  pass. Also repaired a frontmatter YAML defect from the original 2026-07-25 fix attempt: the correction had been
  written as a trailing multi-line comment directly under `execution_scope:` rather than replacing the value inline,
  which this corpus's frontmatter parser folded into the scalar itself
  (`execution_scope: 'orchestrator-agent local-only'`, an invalid enum value) — found via the corpus-wide
  `check_frontmatter_schema.py` full sweep, confirmed via direct `docspec.parse_frontmatter()` inspection before fixing
  (grep/`git show` alone showed the file as clean, since they don't fold multi-line YAML scalars the way the parser
  does).

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — self-described historical/audit record; every open todo is gated
  (G1.run on the IS backfill + UAC accuracy + v9; G1.run-prediction on another plan's loader wiring; G1.run-full-history
  explicitly DEFERRED pending operator review of a 190M index blow-up).
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- dropped the sibling defi audit-log link, added
  the 3 real source-code targets this log's shipped commits actually touch (catalogue builder, enumerator, v9 migrator).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- self-described historical/audit
  record; every open todo is gated (G1.run on the IS backfill + UAC accuracy + v9; G1.run-prediction on another plan's
  loader wiring; G1.run-full-history explicitly deferred pending the operator's already-approved-but-not-yet-executed
  dedicated VM-launch pass) -- consistent with 2026-08-02/08-06 verdicts.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:30ae01e1b38c4987]: KEEP-NA, valid -- Self-described historical/audit-log record ('this doc is a historical/audit record, not itself gating anything'). All 4 open items are cross-AG rollup/gate trackers, not standalone work: G1.code and G1.dry-run track per-AG owner plans' own completion status; G1.run is explicitly gated on (a) IS backfill completion, (b) UAC accuracy, (c) v9 canonicalisation per AG; G1.run-prediction is explicitly redirected — the doc's own Progress Log states the AO-dispatchable seed-run work 'now lives (or should be tracked) in prediction_phase_ab_residuals_2026_07_24.md (active)', a textbook redirect-to-a-different-doc citation. Two prior na-eligibility-audit passes (2026-08-02, 08-08) confirmed KEEP-NA with matching reasoning.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — Self-described historical/audit-log record ('this doc is a historical/audit record, not itself gating anything'). All 4 open todos are cross-AG rollup/gate trackers, not standalone work: G1.code and G1.dry-run track.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche): KEEP-NA, valid — reaffirms the chain of 4 prior audit passes (2026-08-02/08/17/19), unchanged: self-described historical/audit-log record ('not itself gating anything'); all 4 open todos are cross-AG rollup/gate trackers, not standalone work — G1.code/G1.dry-run track per-AG owner plans' own completion status, G1.run is explicitly gated on IS-backfill+UAC-accuracy+v9-canonicalisation per AG, G1.run-prediction is explicitly redirected to `prediction_phase_ab_residuals_2026_07_24.md`.
- **2026-08-22**: corrected `repos:` frontmatter from a copy-paste leftover of the 2026-07-24 extraction split
  (`[agent-orchestrator, batch-live-reconciliation-service, deployment-api, deployment-service, deployment-ui,
  e2e-testing]` — none of which this doc's content touches) to `[instruments-service, unified-api-contracts]`,
  matching the doc's actual content (`build_instrument_catalogue.py`, `enumerate_expected_universe.py`,
  `migrate_instruments_store_v9.py`, the UAC validity matrix). Source: `cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md`
  item, itself sourced from `plan_reconciler_findings_cross_cutting_2026_08_18.md` "Plans not reached" item 4.
