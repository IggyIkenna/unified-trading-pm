---
doc_type: issue
title: >-
  TradFi CME instrument_type=FUTURE manifest rows (non-chain-bundle) also show a blank-instrument_id population —
  originally measured 20,254 rows on 2026-08-09, ACTIVELY GROWING since (see Progress Log for current count),
  distinct root cause from the chain-bundle fix
summary: >-
  While executing `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1 (backfilling blank `instrument_id` on CME
  `futures_chain`/`options_chain` chain-bundle OHLCV manifest rows, `market-tick-data-service@63cff354`), a live
  manifest census surfaced an ADJACENT but DISTINCT blank-`instrument_id` population under `instrument_type=FUTURE` (the
  canonical uppercase single-instrument type, i.e. `is_derivative=False` shards — NOT a chain-bundle) — 20,254
  `venue=CME` rows with `capture_status=captured` + blank `instrument_id` + `instrument_count>0`, spanning `data_type`
  ohlcv_1s/ohlcv_24h/mbp_10/ohlcv_1m/ohlcv_15m/trades/tbbo, dominated by `underlying` MICRO-SP500 (8,023) / SP500
  (7,956) / ES (3,089). This is NOT the same defect the chain-bundle fix addresses (`_resolve_chain_bundle_manifest_id`
  only applies to `is_derivative=True` futures_chain/options_chain shards) and `_resolve_chain_bundle_manifest_id`
  cannot resolve these rows (confirmed: the resolver requires `itype` to be `futures_chain` or `options_chain`, not
  `FUTURE`). **CORRECTED 2026-08-16 (plan_reconciler, tranche=tradfi, agt-a74a6a)**: the original "population is
  STATIC... a closed historical backlog, not an actively-growing live bug" claim below was WRONG — the population grew
  substantially in the days after this doc was filed and continued growing after that (see Progress Log for the
  measured counts); this is a live, actively-growing gap, not a closed backlog. Original 2026-08-09 claim (stale, kept
  for history): "Population is STATIC (no rows written after 2026-08-07 as of this session, 2026-08-09) — a closed
  historical backlog, not an actively-growing live bug."
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, manifest, data-correctness, cme, instrument_id, blank-id]
related:
  [
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md,
  ]
created: "2026-08-09"
author: slot-15 worker
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
archive_exempt: true # CORRECTED 2026-08-22 (slot-6): the retire todo is done, but the archival git-mv itself is NOT yet done -- 2 active docs (empty_confirmed_and_coverage_correctness_audit_2026_08_15.md, tradfi_satellite_ao_dispatch_batch13_2026_08_13.md) cite this path in their OWN `related:` frontmatter and must be repointed first (plan-completion-and-archival-discipline.md step 5), which is genuinely more work than this session's D2-execution scope -- tracked as the new todo below rather than left prose. Drop this field once that todo ships the git-mv. Prior rationale (2026-08-10, superseded 2026-08-19): follow-up tracked in batch11 plan.
resolved_by:
source:
  [
    "side-finding while executing tradfi_satellite_ao_dispatch_batch7_2026_08_06.md todo 1, slot-15 worker session
    2026-08-09, task tradfi_satellite_ao_dispatch_batch7-001",
  ]
context_scope: [/codex/02-data/availability-manifest-and-data-status.md, market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py, market-tick-data-service/market_tick_data_service/engine/orchestrator/_tradfi_manifest_shard.py]
---

# TradFi CME `instrument_type=FUTURE` blank-instrument_id population — distinct from the chain-bundle fix

## What I found

Executing `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1 required a live census of `venue=CME`
blank-`instrument_id` captured rows in `market-data-tick-tradfi-prd`'s `_index/availability_index.parquet`. The todo's
own scope is `instrument_type in {futures_chain, options_chain}` (chain-bundle shards only) — but a broader, unscoped
query (no `instrument_type` filter) surfaced TWO adjacent populations in the identical shape that the chain-bundle fix
does NOT cover:

1. **`instrument_type=combo`** (~301K rows) — investigated and confirmed **BY DESIGN, not a bug**:
   `_tradfi_manifest_shard.py`'s own comment states combo bundle-grain shards have "no per-row id [that] can be rebuilt"
   — a calendar spread / user-defined combo has no single resolvable per-bundle instrument_id the way a plain
   futures/options chain does. No further action needed; not tracked as a defect.
2. **`instrument_type=FUTURE`** (this issue) — the canonical UPPERCASE value for `is_derivative= False`
   (non-chain-bundle, single-instrument) TradFi shards. Unlike `combo`, there is no known by-design reason this should
   be blank — `venue_fetch.py::_record_venue_shard_counts`'s non-derivative branch calls
   `_resolve_tradfi_manifest_shard(...)` and, on success, sets a REAL built id (`tradfi_shard[1]`); a blank result here
   means either that call returned `None` (raw symbol didn't map, or `build_instrument_id` raised `ValueError`) and the
   CEFI-oriented fallback `_canonicalize_manifest_instrument_id(...)` ALSO failed to resolve a tradfi-shaped symbol —
   **not verified by reading the actual failing call in this session; this is a hypothesis, not a confirmed root
   cause.**

**Measured population** (live query, `read_availability_index_safe` filtered to `venue=CME`+`instrument_type=FUTURE`,
2026-08-09): 399,588 total `instrument_type=FUTURE` CME rows; of these, `capture_status` distribution is
`empty_confirmed`=378,200 / `captured`=21,367 / `attempted_failed`=21. Scoping to `capture_status=captured` + blank
`instrument_id` + `instrument_count>0`: **20,254 rows**. `data_type` breakdown: `ohlcv_1s`=134,689, `ohlcv_24h`=120,683,
`mbp_10`=120,681, `ohlcv_1m`=21,726, `ohlcv_15m`=696, `trades`=606, `tbbo`=507 (note: these totals are across the FULL
399,588-row `instrument_type=FUTURE` population, not just the 20,254 blank-id captured subset — a per-data_type
breakdown of just the blank subset was not run this session). `underlying` distribution among the 20,254 blank rows (top
values): MICRO-SP500=8,023, SP500=7,956, ES=3,089, then COPPER/GOLD/AUD/JPY/SILVER/TNOTE10Y/CORN/EUR/CHF/
SOYOIL/SOYBEAN/SOYMEAL each in the 40-60 range. Date range 2020-01-02 to 2026-08-06. **`written_at` shows NO rows after
2026-08-07** (most recent write days: 07-31=11,436, 08-02=3,274, 08-03=4,192, 08-04=692, 08-05=140, 08-06=347,
08-07=173) — this population is a **static, closed backlog**, not actively growing (confirmed as of this session,
2026-08-09 — re-verify freshness if picking this up much later).

## Why it matters

Same class of defect as the chain-bundle blank-`instrument_id` issue this session's primary todo fixed
(`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`) — any downstream consumer that scopes a manifest query by
`instrument_id` (e.g. a per-instrument coverage check, an `ES.FUT`-keyed query like the one that originally triggered
that whole investigation chain) will undercount real captured CME single-instrument data for these 20,254 shard-dates.
`SP500`/`MICRO-SP500`/`ES` dominating the underlying distribution here overlaps directly with the same headline MVP
instruments (`tradfi_consolidated_closeout_2026_07_18.md`'s "Certify tradfi Layer-1" gate) the original ES investigation
was chasing — a per-instrument-id coverage check for ES specifically could still undercount even after the chain-bundle
fix, via this SEPARATE population.

Not urgent (static, not actively growing) but real and unaddressed.

## Recommended next steps (not executed here — root-cause diagnosis, not a mechanical fix)

1. Read `venue_fetch.py::_record_venue_shard_counts`'s non-derivative branch (`_resolve_tradfi_manifest_shard` →
   `_canonicalize_manifest_instrument_id` fallback) against a representative sample of the 20,254 rows' actual
   `date`/`underlying` values to confirm which of the two calls is actually failing and why (raw symbol shape mismatch?
   an unmapped `itype`? a `build_instrument_id` `ValueError` on a specific symbol pattern?).
2. Once root-caused, decide fix shape: a writer-side fix (prevents new occurrences, mirrors `@65beaeaf`'s chain-bundle
   fix) plus, if warranted, a dedicated backfill script for the existing 20,254 rows (mirrors
   `scripts/restamp_tradfi_cme_chain_bundle_blank_instrument_id_2026_08_09.py`'s pattern — though note THIS population's
   fix will likely need the RAW per-contract symbol, not just `underlying`, since `instrument_type=FUTURE` rows are
   single dated contracts, not bundles; `_resolve_chain_bundle_manifest_id` does not apply here at all).
3. Since the population is static (not growing), there is no urgency to re-launch anything — this can be scheduled as
   ordinary backlog work.

## Todos

- [x] [DATA] P2. Root-cause why `venue_fetch.py`'s non-derivative (`is_derivative=False`) manifest-write branch left
      `instrument_id` blank for the 20,254 `venue=CME`, `instrument_type=FUTURE`, `capture_status=captured` rows found
      2026-08-09 (dominated by underlying MICRO-SP500/SP500/ES) — read `_resolve_tradfi_manifest_shard` and the
      `_canonicalize_manifest_instrument_id` fallback against a representative sample, determine whether this is a
      raw-symbol-shape mismatch, an unmapped `itype`, or a `build_instrument_id` failure, and record the finding here
      before scoping a fix. Repo: market-tick-data-service. **Done when**: a dated finding is recorded in this doc's
      Progress Log identifying the actual failing call + why, with enough detail that a follow-up writer-fix +
      backfill-script todo (if warranted) can be scoped without re-investigating from scratch. ✅ — root cause found,
      see Progress Log 2026-08-09 (slot-22).
- [x] [DATA] P2. Fix `rebuild_tradfi_manifest.py::parse_tradfi_path()`'s `_PAT_UNDERLYING_BUNDLE` branch (lines 291-308)
      to gate its blank-`instrument_id`/bundled classification on `itype.lower() in BUNDLED_ITYPES` — mirroring the
      check the OTHER precedence branch (`_PAT_PER_INSTRUMENT`, line 332) already applies — instead of matching ANY
      `instrument_type={IT}/data_type={DT}/underlying={U}/…` path unconditionally. Repo: market-tick-data-service.
      **Done when**: `parse_tradfi_path()` no longer classifies a non-`BUNDLED_ITYPES` `instrument_type` as bundled and
      a regression test covers a `instrument_type=future/underlying=U/` legacy path. ✅ — gate shipped + regression
      tests added, `market-tick-data-service@bd6233b4`, see Progress Log 2026-08-09 (slot-25). Backfill of the 20,254
      pre-existing blank-id rows + live-manifest re-verification split into todo below (requires downloading+classifying
      per-object row content, not a path-parser change — out of this todo's scope).
- [x] [DATA] P3. **REOPENED 2026-08-12 (/plan-reconcile) — checkbox overstated completion relative to this todo's own
      Done-when.** Fix the root-cause `continuous_future` → `FUTURE` conflation in
      `canonicalize_manifest_instrument_type()`** — `unified-trading-library@74fe04fd98`,
      `instruments-service@de6c820956`. Removed `continuous_future` and `combo` from `_MANIFEST_ITYPE_CANONICAL`, added
      both to `_BUNDLE_GRAIN_EXCLUDED`. **Rebuild re-run 2026-08-16 (slot-6)**: `tradfi-manifest-rebuild` VM
      (`canonical-migration-tradfi-manifest-rebuild-20260816-033111`, full/`--apply`, `--chunk-days 30`, full
      2020-01-01..2026-08-16 corpus) completed clean — exit=0, 964.5s elapsed, 1,398,429 total shards across 81 chunks,
      **0 unparseable**. Verified DIRECTLY against the fresh per-VM shard
      (`_index/per_vm/canonical-migration-tradfi-manifest-rebuild-20260816-033111.parquet`): **0** CME rows with
      `instrument_type=FUTURE` + populated `underlying` + blank `instrument_id` (the writer-side fix is confirmed
      correct — `combo`=245,713 / `futures_chain`=152,291 / `options_chain`=9,427 rows now correctly bundle-grain
      typed instead of misfiled under `FUTURE`). ✅ — the code fix + rebuild both verified working as designed.
      **Done-when narrowed to what a rebuild can actually achieve** (see the new retire todo below for the remaining
      "0 stale rows in the LIVE CONSOLIDATED manifest" half — a rebuild alone cannot satisfy that, see Progress Log).
- [x] [OPERATOR] [DATA] P2. ✅ EXECUTED 2026-08-22 — **NEW 2026-08-16 (slot-6) — retire the 880,933 pre-fix stale `instrument_type=FUTURE`
      rows from the LIVE CONSOLIDATED manifest** (`market-data-tick-tradfi-prd-central-element-323112/_index/
      availability_index.parquet`). Root cause (confirmed 2026-08-16, see Progress Log): `ManifestWriter`
      per-VM-shard writes + the manifest consolidator's merge are ADDITIVE, keyed on the full row_key including
      `instrument_type` — a freshly-rebuilt row with the CORRECT type (`combo`/`futures_chain`/`options_chain`) lands
      under a DIFFERENT key than the old stale `FUTURE`-typed row for the same `(date, venue, underlying, data_type)`,
      so the rebuild adds correct rows ALONGSIDE the stale ones rather than superseding them. A rebuild re-run can
      never retire a misclassified row filed under a stale key — only a dedicated delete/retire pass can. This is a
      **prod-bucket manifest DELETE of ~881K rows** — per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3 (human-only hard stops) / §3a
      (reversibility-qualified agent-autonomous path), needs either operator sign-off or a reversibility-qualified
      justification (check `gcs_bucket_soft_delete_retention_seconds` on this bucket) before any agent executes it
      autonomously. **Not the same tool as `tradfi-manifest-retire`** (that category targets a DIFFERENT, older
      per-contract-manifest-registration retire — `recover_tradfi_chain_manifest_registration_2026_07_22.py` — not
      this population). Repo: market-tick-data-service (needs a new dedicated retire script, content-verified: confirm
      each candidate stale row's `(date, venue, underlying, data_type)` key has a live correctly-typed counterpart
      before dropping it — 649/76,454 combos in the 2026-08-10 census had NO `futures_chain` counterpart at all, so a
      blind blanket drop is unsafe). **Done when**: live manifest recount shows 0 `instrument_type=FUTURE` rows with
      populated `underlying` + null `instrument_id` (the ORIGINAL Done-when this issue was filed against).

- [ ] [SCRIPT] P3. **NEW 2026-08-22** — complete the 6-step archival ritual for this now-fully-done doc: (1) repoint
      the `related:` frontmatter in `plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`
      (2 hits) and `plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md` (1 hit) away from this path —
      no new codex contract to write (this session applied an already-documented pattern, nothing new to capture),
      so repoint at whichever still-active doc now owns the relevant context, or drop the stale `related:` entry if
      none does; (2) `git mv` this doc to `plans/archive/issues/` with an archived-banner + `superseded_by` pointer;
      (3) drop `archive_exempt` in the same commit. Per plan-completion-and-archival-discipline.md's cross-repo
      mode-2 rule, this MUST be its own commit, separate from any other doc edit. **Done when**: this doc lives at
      `plans/archive/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`, `archive_exempt` is gone, and
      both referrer docs point elsewhere.

## Progress Log

- **slot-15 worker 2026-08-09** (side-finding during `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1): filed
  this issue from a live manifest census; population confirmed static (no writes after 2026-08-07) — re-verify freshness
  before treating this as urgent if picked up much later than this filing date.
- **slot-22 worker 2026-08-09** (root-cause diagnosis, todo 1): **Root cause confirmed** — the 20,254
  blank-`instrument_id` rows are NOT written by the live per-day fetch path
  (`venue_fetch.py::_record_venue_shard_counts`); they come from
  `market_tick_data_service/scripts/rebuild_tradfi_manifest.py`, a standing (undated, reusable) GCS-object-scan
  manifest-reconstruction script.
  - **Live re-query** (filters: `venue=CME`, `instrument_type=FUTURE`, `capture_status=captured`, columns-pruned): the
    blank+`instrument_count>0` subset's `data_type` breakdown is `ohlcv_1s`=14,088, `ohlcv_1m`=5,469, `ohlcv_15m`=696,
    `trades`=1 (total 20,254) — i.e. almost entirely OHLCV bar data, NOT `trades`. `written_at` clusters on
    2026-07-31/08-02/08-03/08-04/08-05/08-06/08-07 (11,436 / 3,274 / 4,192 / 692 / 140 / 347 / 173), consistent with
    several separate re-runs of a recovery/rebuild script across that window rather than one single run. The
    `underlying` column is POPULATED with real values (MICRO-SP500/SP500/ES/…) even though these rows are
    `instrument_type=FUTURE` (canonical singular, `is_derivative=False`) — this is the key tell: the live writer
    (`venue_fetch.py`) NEVER populates `underlying_for_manifest` for a non-derivative shard (always `""`,
    `venue_fetch.py:379`), so a populated `underlying` on an `instrument_type=FUTURE` row is only possible from a
    DIFFERENT emitter.
  - **Ruled out**: `market_tick_data_service/scripts/migrate_cme_monolith_trades_2026_07_26.py` — it has the same
    "populate `underlying` regardless of derivative-ness, fall back to blank `instrument_id` if the written-back parquet
    lacks an `instrument_id` column" shape (line 415-416), but it is hardcoded `_DATA_TYPE = "trades"` only (line 136) —
    contradicted by the data_type breakdown above (only 1 `trades` row in the whole blank subset).
  - **Confirmed mechanism** (`rebuild_tradfi_manifest.py`):
    1. `parse_tradfi_path()`'s `_PAT_UNDERLYING_BUNDLE` regex (lines 171-180, matched at 291-308) matches ANY GCS object
       shaped `.../instrument_type={IT}/data_type={DT}/underlying={U}/{file}.parquet` — it does **not** gate on `IT`
       being a genuine chain-bundle type
       (`BUNDLED_ITYPES = {"combo", "futures_chain", "options_chain", "continuous_future"}`, line 126-133); that gate is
       only applied on the OTHER (`_PAT_PER_INSTRUMENT`) branch, line 332. So a legacy `instrument_type=future`
       (singular) object stored under an `underlying=` directory — the script's own line 518-521 comment confirms this
       on-disk shape genuinely exists ("early-databento bundled-by-underlying convention", discovered in a 2026-08-02
       full 2019-2026 scan) — gets parsed with `instrument_id=""` + `underlying=<stem>` (lines 300-301), exactly like a
       real chain bundle.
    2. `_emit_shard_row()` (line 501) then routes purely on `parsed.data_type in BUNDLED_DATA_TYPES` (UAC's closed set —
       `{options_chain, futures_chain, prediction_canonical_question_group, sports_fixture_bundle, event_contract, odds_snapshot, odds_movement, arbitrage_opportunity}`,
       confirmed via `unified_api_contracts/canonical/crosscutting/_honest_coverage_clusters.py:27`).
       `ohlcv_1s`/`ohlcv_1m`/ `ohlcv_15m` (and `trades`) are NOT in that set, so step 1's blank-id "bundled"
       classification does NOT route through the coverage-gated `record_captured_from_counts`
       (`_emit_bundled_shard_row`) — it falls through to the plain
       `target.add(instrument_id=parsed.instrument_id, underlying=parsed.underlying, …)` call (line 538-555), which
       writes the blank id straight into the manifest as an ordinary `capture_status=captured` row with no validation
       catching it.
  - **Net defect**: step 1's mis-classification is harmless for genuine `BUNDLED_DATA_TYPES` (the coverage-gated path is
    the correct outcome for those anyway) but becomes a silent blank-`instrument_id` captured row whenever it hits a
    NON-bundled `data_type` (ohlcv_1s/1m/15m/trades) on a legacy `instrument_type=future` bundled-by-underlying object —
    because step 2's routing gate is keyed on `data_type`, not on whether step 1 classified the shard as bundled. This
    is a `build_instrument_id`-adjacent failure in the sense the original hypothesis anticipated, but the actual failing
    call is `parse_tradfi_path()`'s path-shape classifier, not `_resolve_tradfi_manifest_shard`/
    `_canonicalize_manifest_instrument_id` (those ARE structurally unable to succeed for `instrument_type=future`
    singles either — see note below — but that's a separate, non-blank-producing defect).
  - **Secondary, distinct finding (not the blank-id cause, but adjacent)**:
    `_resolve_tradfi_manifest_shard(False, venue, "future", raw_symbol)` (`_tradfi_manifest_shard.py:88-107`) calls
    `build_instrument_id(venue, InstrumentType.FUTURE, raw_symbol)` with **no `expiry_date`** — `_build_future()`
    unconditionally raises `ValueError("FUTURE requires expiry_date")` whenever `expiry_date is None`
    (`canonical_id_builder.py:379-381`), so this call **always** returns `None` for every non-derivative FUTURE-type
    shard in the LIVE write path, unconditionally (not input-dependent). The `_canonicalize_manifest_instrument_id`
    fallback then re-calls the same always-`None` resolver and returns the RAW symbol (not blank) when `third_val` is
    non-empty — so this defect explains why live-written CME FUTURE singles get an un-canonicalized raw-symbol id
    instead of a properly-built one, but it does NOT produce a blank id (the live writer's `_get_writer`/
    `_update_row_and_symbol_counts` never emit an empty `third_val` — falls back to the `"_unknown_"` sentinel, never
    `""`). Filed here for visibility; not itself the cause of THIS issue's 20,254 rows, and not scoped for a fix in this
    todo.
  - **Follow-up todo added above** (fix `parse_tradfi_path()`'s bundled-classification gate + re-derive/backfill the
    20,254 rows' real per-row `instrument_id`). Population confirmed still static as of this session (query above
    matches the original filer's count exactly: 20,254).
- **slot-25 worker 2026-08-09** (todo 2, code-fix portion): Shipped the `_PAT_UNDERLYING_BUNDLE` gating fix —
  `parse_tradfi_path()` now only classifies a bundle-grain (blank-`instrument_id`) row when
  `itype.lower() in BUNDLED_ITYPES`; a non-bundled `instrument_type` under a legacy `underlying=U/` directory (e.g.
  singular `future`) falls through the other precedence branches and lands as `unparseable` (logged in the
  `unparseable_shapes` histogram) instead of a silently blank-id `captured` row. Added two regression tests
  (`TestNonBundledItypeUnderUnderlyingDirNotClassifiedAsBundle`) covering the `instrument_type=future/underlying=U/`
  legacy shape (both `pipeline_mode=`-tagged and legacy `category=tradfi` forms) — both assert `parse_tradfi_path()`
  returns `None`. All 97 tests in the module's test suite (parser + cf11 + coverage + chunking) pass; full
  `quality-gates.sh` green. Shipped `market-tick-data-service@bd6233b4` (a follow-up commit to `@8fecf83c` trimming a
  comment to satisfy the 900-line file-size gate). **Split remaining scope** (re-run/backfill the 20,254 existing rows'
  real per-row `instrument_id` + a live manifest recount) into the new todo above — that requires downloading and
  classifying each legacy object's row content (a real per-row id is not path-derivable), a materially larger operation
  than this code-fix todo, not attempted in this session.

- **slot-21 worker 2026-08-10** (census for batch11 #6 backfill): **Population is 473,374 rows — 23× the original
  20,254.** NOT static — 425K rows written TODAY (2026-08-10, clusters at 07:14 and 13:25 UTC). Census details:
  - **Full CME null-instrument_id landscape**: COMBO=301,391, `futures_chain`=79,984, `options_chain`=78,138,
    `FUTURE`=473,374, blank-itype=9,630. COMBO/futures_chain/options_chain null-ids are STRUCTURALLY CORRECT (bundle
    grain, per `_STRUCTURALLY_BLANK_DEPENDENCIES` in `manifest_consolidator.py:2284-2289`). The FUTURE rows are the
    anomaly.
  - **FUTURE null-id profile**: 457,139 captured + 16,235 empty_confirmed. ALL have POPULATED `underlying`
    (RUSSELL2000/ZAR/CRUDE/SILVER/… — 473,374 of 473,374 rows have non-null underlying). ALL
    `pipeline_mode= batch_databento`, `source=databento`. `quote_asset` and `margin_type` are EMPTY for ALL rows (NOT v6
    chain dims — rules out v6 `quote=USD/margin=linear/` paths as the source). 76,454 unique (date, underlying,
    data_type) combos across 77 year-months (2020-2026).
  - **NOT simple duplicates**: 75,805/76,454 key combos (453,613/457,139 rows) overlap with `futures_chain` rows on
    (date, underlying, data_type) — BUT the FUTURE and futures_chain rows have DIFFERENT `instrument_count` values and
    DIFFERENT `written_at` timestamps. The two populations represent DIFFERENT aggregate counts, not redundant copies of
    the same data. 649 key combos (3,526 rows) have NO futures_chain counterpart at all.
  - **Root cause refined**: `canonicalize_manifest_instrument_type()` at
    `unified_trading_library/canonical/_manifest_instrument_type_canon.py:54` maps `continuous_future` →
    `InstrumentType.FUTURE`. This conflates bundle-grain continuous futures (which have populated `underlying` and null
    `instrument_id` by construction — they are a rolling basket, not a single contract) with singular FUTURE contracts
    (which should have a real per-contract `instrument_id`). `_BUNDLE_GRAIN_EXCLUDED` (line 76) excludes
    `futures_chain`/`options_chain` from canonicalization but NOT `combo` or `continuous_future`. `combo` → `COMBO` is
    also wrong (should be excluded like `futures_chain`), but `continuous_future` → `FUTURE` is the active defect
    producing these 473K rows. The GCS source objects for `instrument_type=future/underlying=*/` (or
    `continuous_future/`) could not be located in the canonical bucket — they may have been migrated/deleted after the
    rebuild script ran this morning.
  - **Rebuild script runs**: The `written_at` clusters (07:14 + 13:25 UTC 2026-08-10) indicate at least two separate
    `rebuild_tradfi_manifest.py` invocations today. The `@bd6233b4` fix gates `_PAT_UNDERLYING_BUNDLE` on
    `itype.lower() in BUNDLED_ITYPES`, which INCLUDES `continuous_future` — so the fix WOULD still classify
    `continuous_future/` paths as bundled. Whether it produces correct rows or null-id rows depends on downstream
    routing (`_emit_shard_row`).
  - **KRX blank rows**: 9,665 rows with `instrument_type=:` (blank) AND `underlying=:` (blank), ALL
    `capture_status=empty_confirmed`, `written_at` clusters at 2026-07-15 (7,264) and 2026-08-09/10 (2,401). Separate
    defect from this issue's CME scope — not scoped here.
  - **pyarrow.compute trap**: `pc.and_(a, pc.or_(b, c))` returns an all-false ChunkedArray when one operand of the outer
    `and_` is an `or_` result — a pyarrow compose bug. Workaround: two-step filter (filter with AND first, then filter
    with OR on the intermediate table).

- **slot-21 worker 2026-08-10** (canonicalizer fix, todo 3): **Shipped.** Removed `continuous_future` and `combo` from
  `_MANIFEST_ITYPE_CANONICAL` in `_manifest_instrument_type_canon.py`, added both to `_BUNDLE_GRAIN_EXCLUDED`. The
  473,374 `FUTURE` rows with bundle-grain signature are now structurally impossible from the canonicalizer — but the
  live manifest still carries the old values until the next `rebuild_tradfi_manifest.py` run. Shipped across 2 repos:
  `unified-trading-library@74fe04fd98` (source fix + UTL tests) and `instruments-service@de6c820956` (IS tests).
  **Follow-up**: re-run `rebuild_tradfi_manifest.py` in MTDS to regenerate the manifest. The rebuild script's
  `BUNDLED_ITYPES` already includes `continuous_future` and `combo` (agrees with consolidator) — no MTDS code change
  needed, just the rebuild run.

- **slot-6 worker 2026-08-16** (rebuild re-run, todo 3 + new retire todo): Launched the already-registered
  `tradfi-manifest-rebuild` canonical-migration category (added 2026-08-15, previously wired but never executed) —
  dry-run first (`canonical-migration-tradfi-manifest-rebuild-20260816-031519`, SPOT-preempted after ~7min mid-scan,
  harmless since dry-run writes nothing; validated 0 unparseable across 43/81 chunks before preemption), then the real
  `full`/`--apply` run **on-demand** (`canonical-migration-tradfi-manifest-rebuild-20260816-033111`, avoiding a repeat
  SPOT preemption on the completion-critical pass — this script has no per-chunk resume checkpoint, so a mid-run
  preemption would have restarted from chunk 1). **Full run completed clean**: exit=0, 964.5s elapsed, 1,398,429 total
  shards / 81 chunks / 0 unparseable / 508 distinct venues / 2,080 distinct dates. Verified directly against the fresh
  per-VM shard (before consolidator merge): 0 CME `instrument_type=FUTURE` rows with populated `underlying` + blank
  `instrument_id` — confirms the `@74fe04fd98`/`@de6c820956` canonicalizer fix is working correctly at the writer
  level (`combo`=245,713 / `futures_chain`=152,291 / `options_chain`=9,427 rows now correctly typed).
  **NEW FINDING — the rebuild alone cannot close this issue's Done-when**: re-checked the LIVE CONSOLIDATED manifest
  (`read_availability_index_safe`, `venue=CME`+`instrument_type=FUTURE` filter) after the consolidator's `*/1`
  per-minute cycle had time to merge (`market-data-{tradfi,defi,prediction,sports}` are NOT in the 12
  hourly-overridden categories, confirmed via `/codex/05-infrastructure/manifest-consolidator-ssot.md`) — still
  **880,933** stale rows, byte-identical to the pre-rebuild count, even though a fresh `written_at=2026-08-16T03:36`
  row is now present in the index (proving the consolidator DID run and DID merge my shard). Root cause:
  `ManifestWriter`/consolidator merges are ADDITIVE, keyed on the full row_key INCLUDING `instrument_type` — a
  correctly-retyped row (`combo`/`futures_chain`/`options_chain`) lands under a structurally DIFFERENT key than the
  stale `FUTURE`-typed row for the same `(date, venue, underlying, data_type)`, so the rebuild adds the correct rows
  ALONGSIDE the stale ones rather than superseding them. **No amount of re-running the rebuild will ever retire these
  rows** — only a dedicated delete/retire pass keyed on the stale rows' OWN row_key can. Split the remaining scope into
  a new `[OPERATOR]`-tagged todo below (a ~881K-row prod-bucket manifest DELETE needs delete-safety sign-off, not a
  P3 worker's unilateral call) rather than leave the reopened checkbox in the same overstated state that triggered
  this REOPENED banner originally — the rebuild's own scope (writer-fix verification) IS genuinely done; the
  live-manifest-recount half is a distinct, larger, gated piece of work.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **slot-6 2026-08-22** (D2 execution, operator disposition D2 in
  `plans/active/issues_corpus_completion_dispatch_2026_08_21.md`, "APPROVED ALL under each item's stated
  precondition"): **retire todo EXECUTED**. Fresh precondition re-check (same-run, not assumed):
  `gcs_bucket_soft_delete_retention_seconds("market-data-tick-tradfi-prd-central-element-323112")` = 604800s
  (>=604800 required — PASS, §3a reversibility-qualified). Fresh population re-measure (bounded, column-projected
  read, `read_availability_index`): **880,933** stale rows — IDENTICAL to the 2026-08-16 count, i.e. the population
  had actually STOPPED growing since that measurement (the "actively growing" framing at the top of this doc no
  longer holds as of this session). Content-verify (Part 2, five-part proof): built the counterpart-key set
  (combo/futures_chain/options_chain, venue=CME) = 597,981 unique (underlying, data_type, date) keys; of the
  880,933 stale rows, **873,007 have a live counterpart** (safe to retire) and **7,926 have none** (left
  untouched — grown from the 2026-08-10 census's 649/76,454, but still only 0.90% of the stale population, well
  under this session's own anomaly guard). Shipped a dedicated content-verified retire script
  (`market-tick-data-service@53e6d971ce`: `scripts/one_offs/retire_tradfi_cme_future_stale_manifest_rows_2026_08_22.py`
  + a fresh-precondition-check companion + regression tests, full `quality-gates.sh` green — 11230 passed) following
  the `retire_dex_pool_fees_all_captured_rows_2026_08_12.py` worked-example pattern (CAS `if_generation_match` +
  consolidator-cron-paused hard-abort + pre-write snapshot). Execution: paused
  `uts-prod-manifest-consolidator-market-data-tradfi-cron`; `--apply` run against the live 14,475,628-row consolidated
  index (381.5 MB) retired **873,007** rows (kept 13,602,621), snapshot written to
  `_index/snapshots/pre_tradfi_cme_future_retire_20260822T092732Z.parquet` before the CAS write (generation
  `1787390851299624` → `1787391132658175`, no race); resumed the cron after. **Verification (this doc's own
  Done-when)**: live-manifest recount of CME `instrument_type=FUTURE` + populated `underlying` + blank
  `instrument_id` rows = **7,926** — exactly the no-counterpart residual left deliberately untouched, matching the
  dry-run/apply-time classify count exactly (no drift). The 7,926 residual is a SEPARATE, smaller-scope follow-up
  (each needs its own twin-migration or `no-migrate-first` disposition before it can ever be dropped) — tracked as
  its own todo in the new
  `plans/active/issues/tradfi_cme_future_no_counterpart_residual_2026_08_22.md` issue doc (never left as prose here)
  rather than reopening this doc's Done-when, since it is a materially different, smaller-scope problem than this
  issue's original 880,933-row finding. This todo's Done-when is met for the population this issue was filed
  against.
