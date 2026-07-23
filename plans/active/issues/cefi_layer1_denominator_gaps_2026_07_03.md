---
doc_type: issue
title:
  cefi Layer-1 denominator silently omits whole venues with real captured data (gate-authority gaps + one writer itype
  mis-stamp)
summary:
  'Found 2026-07-03 while implementing the UAC↔writer matrix reconciliation: the cefi Layer-1 EXPECTED matrix (44
  tuples) substantially under-counts the real could-exist universe. Two gate authorities silently zero-out whole venues:
  (1) the (venue,itype) gate reads VenueMapping.venue_instrument_type_to_tardis, which lacks the Tier-3 venues
  (BITFINEX-SPOT/BITGET-*/KRAKEN-SPOT) and all non-Tardis venues
  (HYPERLIQUID/ASTER/EXTENDED-STARKNET/PACIFICA/LIGHTER/KALSHI-PERP/POLYMARKET-PERP) — venues with REAL captured data
  get expected=0/0; (2) venues wholly absent from VENUE_DATA_TYPE_CAPABILITIES
  (BINANCE-DELIVERY/DERIBIT-COMBO/BYBIT-SPOT/COINBASE-FUTURES/KALSHI-PERP/POLYMARKET-PERP/PACIFICA/EXTENDED/LIGHTER)
  have every data_type carved out. Separately, the MTDS writer stamps BYBIT-SPOT rows instrument_type=PERPETUAL (spot
  venue). Net: cefi completeness % is measured over a fraction of the real universe — the "entire venue absent from the
  denominator" dishonesty class Honest-Coverage v2 exists to kill.'
status: open
nature: notes
asset_group: [cefi]
stage: [data, meta]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi]
related:
  [
    honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-03
parent_epic: infrastructure_master
priority: P1
source: honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md implementation session (Harsh)
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-14 # (was: 2026-07-10 -- bumped for the 2026-07-14 DERIBIT-COMBO batch-routing fix flip, slot-7)
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding (data-correctness).** Surfaced 2026-07-03 while implementing
> `honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md` (ground-truthing the cefi venue dialect from
> `coverage.json` `by_venue_instrument_type` + `layer_1.by_asset_group.cefi.by_venue`). NOT fixed in that pass — it
> changes the certified cefi denominator structurally and needs owner decisions on the gate authorities.

> **🤖 AO PLAN 1 of the instruments-completion set — cefi denominator completion (Stage 2 cefi).** Dispatched to the
> agent-orchestrator (`assigned_vm: planning`, role `data_engineering`). **Dispatch tier (frontmatter-driven, applies to
> EVERY task): Sonnet / high** (retiered 2026-07-07 — the C2 `_row_data_types` fix that justified Opus shipped
> `is@2170d9a3`; remaining tasks are mechanical, and the all-Opus spawn was thrashing the credit-limited accounts).
> Coordinator = `instruments_completion_tracker_2026_07_06.md` (Stage 2). The one law: **Layer-1 (denominator) gates
> Layer-2 (capture)** — this plan corrects + certifies the cefi denominator; capture (%) is meaningless until it lands.
> SSOT: `codex/02-data/honest-coverage-model.md` (do NOT derive the expected universe from the manifest — circular).
> Intra-plan ordering is by P-tag + the explicit `PREREQ:` note on each task; the critical spine is **2a
> `build_expected` → 2b gate-authority → 2c read-time MVP gate → 2f other venues → re-measure**.
>
> **Worker guards (HARD):** (1) **smoke-first on any data mutation** — one shard/slice foreground + verify the GCS +
> manifest side-effect before scaling; never fan out N×M blind. (2) **stop-on-surprise** — if a corrective touches more
> rows than expected or a measure moves the wrong direction, STOP and raise, don't push through (the 2c reclassify
> ~380k-row data-loss landmine is why). (3) **operator decisions → raise a BLOCKED-Q, do NOT guess** (see the
> `BLOCKED-OPERATOR-DECISION` item for the COINBASE / DERIBIT-COMBO MVP_SCOPE call). (4) ship via quickmerge; flip the
> checkbox + append to this plan's Progress Log in the SAME turn.

## Evidence (coverage.json 2026-07-02, layer_1.by_asset_group.cefi.by_venue)

Venues with `expected_tuples == 0` while the manifest holds REAL captured rows for them (Layer-2 strays today):

| Venue                                                                                               | expected | manifest itypes present          | why expected=0                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------- | -------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BITFINEX-SPOT / BITGET-SPOT / BITGET-FUTURES / KRAKEN-SPOT                                          | 0/0      | SPOT_PAIR / PERPETUAL + captures | absent from `VenueMapping.venue_instrument_type_to_tardis` (the checker's cefi (venue,itype) gate authority) — the Tier-3 2026-05-01 expansion never extended that map |
| HYPERLIQUID / ASTER / EXTENDED-STARKNET                                                             | 0/0      | PERPETUAL + captures             | non-Tardis venues — same gate reads only the Tardis map; `INSTRUMENT_TYPES_BY_VENUE` (which HAS them) is not consulted                                                 |
| BYBIT-SPOT / COINBASE-FUTURES                                                                       | 0/0      | rows present                     | wholly absent from `VENUE_DATA_TYPE_CAPABILITIES` → carve-out 1 removes EVERY data_type                                                                                |
| BINANCE-DELIVERY / DERIBIT-COMBO / PACIFICA-SOLANA / LIGHTER-ZKSYNC / KALSHI-PERP / POLYMARKET-PERP | (absent) | —                                | both gates blind to them (no Tardis-map keys AND no capability entries)                                                                                                |

Consequence: cefi Layer-1 "completeness" (65.91% certified 2026-06-29) is measured over a 44-tuple denominator that
omits whole venues UAC declares in `VENUES_BY_ASSET_GROUP["cefi"]` — the exact "entire venue absent from the
denominator" failure mode the v2 model exists to surface (`codex/02-data/honest-coverage-model.md` § Why v1 was not
enough). The % is neither an upper nor lower bound of the real value.

## Separate writer defect found in the same pass

- **BYBIT-SPOT rows are stamped `instrument_type=PERPETUAL`** (manifest `by_venue_instrument_type`: BYBIT-SPOT →
  {PERPETUAL} only; no SPOT_PAIR). Root cause candidate (verified 2026-07-03): MTDS
  `symbol_rules._VENUE_INSTRUMENT_TYPE` has `"BYBIT": "perpetual"` but **NO `BYBIT-SPOT` entry** (unlike
  BITFINEX-SPOT/BITGET-SPOT/KRAKEN-SPOT which map → spot) — BYBIT-SPOT rows fall through to whatever default stamped
  PERPETUAL. Add the map entry, fix the writer path, and corrective-relabel the existing rows. Until then (BYBIT,
  spot_pair, trades|book_snapshot_5) remain honest Layer-1 holes.

## Todos (Stage-2 cefi denominator — the critical spine, in order)

**Already shipped 2026-07-06 (context — DO NOT redo):**

- [x] [DESIGN] P1. **D2a — cefi (venue,itype) gate authority switched to declarative `INSTRUMENT_TYPES_BY_VENUE`** —
      `is@03cfd0f` (`_get_cefi_venue_itypes` sources `INSTRUMENT_TYPES_BY_VENUE` restricted to
      `VENUES_BY_ASSET_GROUP["cefi"]`, bundle roll-up preserved) + `uac@e76d874a` (completes the 10 missing declared
      venues; DERIBIT-COMBO → {OPTION}, Ikenna-confirmed future_combo not in MVP). Measured back-to-back: cefi Layer-1
      **84.09% → 73.61%** (+28 tuples, 0 removed — the honest direction). QG-green both repos, 41 tests pass (dynamic).
- [x] [DESIGN] P1. **D2b — `VENUE_DATA_TYPE_CAPABILITIES` completed + absent = not-expected codified** — `uac@e76d874a`
      (capability entries for PACIFICA/EXTENDED/LIGHTER/COINBASE-FUTURES; "a declared venue MUST carry a capability
      entry; absent = stray/not-expected").

**The critical spine (each task's `PREREQ:` defines the order; the review agent enforces it):**

- [x] ✅ [CODE] P0. **2a. Land the single `build_expected(asset_group)` producer** — `instruments-service@681f50a`. New
      module `scripts/expected_universe.py` exposes `build_expected(asset_group)` as THE public producer; per-AG
      strategies share one callable interface but preserve cefi/defi/tradfi/sports/prediction grains.
      `check_enumeration_completeness._build_expected_tuples` (and `..._sports`) now delegate via sibling-load (mirrors
      `measure_honest_coverage._load_completeness_module`); `measure_honest_coverage` routes transitively through the
      completeness module. Per-AG **byte-identical golden fixtures** at
      `tests/unit/scripts/goldens/expected_universe/{cefi,defi,tradfi,sports,prediction}.json` (72/171/35/27/8 tuples) +
      `test_expected_universe_golden.py` (14 tests: single-producer contract + delegator parity + byte-identical golden
      per AG + fixture metadata coherence). D2a declarative-gate authority baked in (`INSTRUMENT_TYPES_BY_VENUE` +
      `PROTOCOL_CAPABILITIES` + `TRADFI_VENUE_INSTRUMENT_TYPES` — NOT the Tardis fetch-routing map). All 76 impacted
      tests pass; QG-green (105s); no producer surface duplication remains. COINBASE / DERIBIT-COMBO MVP_SCOPE question
      raised as `BLK-5cc7590e` (bare COINBASE + DERIBIT-COMBO declared in `VENUES_BY_ASSET_GROUP["cefi"]` but
      `get_mvp_data_types_for_cefi_venue()` returns `frozenset()` → silent EXPECTED=0; 2a preserves byte-identical
      behaviour so both remain at 0, matching pre-refactor — the fix is downstream in 2b/2c). Evidence:
      `.qg_last_passed_sha=a1038eef81f2a79fd26918baf70c121207c20ad5` (pre-quickmerge), quickmerge shipped `681f50a`.
- [x] ✅ [CODE] P0. **2b. cefi gate-authority fix on `build_expected`.** Apply D2a/D2b onto the single producer, then —
      in order — the ASTER live-forward split (enumerator `start_date` support is a HARD prereq before the UAC
      capability flip), the BYBIT-SPOT relabel, and the C2 MVP-data-type intersection (all detailed in the sections
      below). **PREREQ: 2a landed.** Gate: cefi EXPECTED reflects the full declared cefi universe (no whole-venue
      omission); dynamic tests pass (no golden edits); QG-green. **DONE 2026-07-07 — instruments-service@681f50a (2a
      byte-identical fold with D2a authority baked into `build_expected`) + `03cfd0f` (D2a landing pre-2a) + `2170d9a3`
      (C2 MVP intersection landed as -009 for `_row_data_types`).** Main-agent BLK-ec6dba83 (Option A) confirmed the 2b
      core work — Apply D2a/D2b onto the single producer — is COMPLETE via those SHAs; the remaining "in order"
      sub-parts are individually tracked backlog items with their own PREREQ chains (ASTER split → -007+-008, BYBIT-SPOT
      relabel → -006, C2 MVP → -009 shipped). Verified Gate DYNAMICALLY:
      `pytest     tests/unit/scripts/test_expected_universe_golden.py` → 14/14 pass (1.47s); `build_expected("cefi")`
      returns 72 tuples over 18 of 24 declared cefi venues; the 6 absent (BINANCE-DELIVERY / DERIBIT-COMBO / KALSHI-PERP
      / POLYMARKET-PERP / COINBASE / BYBIT-SPOT) each carry an explicit configuration reason — no silent whole-venue
      omission remains: BINANCE-DELIVERY/DERIBIT-COMBO/KALSHI-PERP/POLYMARKET-PERP have BOTH empty
      `VENUE_DATA_TYPE_CAPABILITIES` and empty `get_mvp_data_types_for_cefi_venue()`
      (COIN-M/future_combo/prediction-perp not-MVP, intentional); COINBASE has caps={book5, trades} but MVP=empty per
      BLK-5cc7590e (BLOCKED-OPERATOR-DECISION already surfaced); BYBIT-SPOT has MVP={book5, derv_ticker, funding,
      trades} but caps=empty, tracked as the writer defect in task -006 (targeted at slot-8 affinity=high). No code
      change or golden edit needed this turn — flip only.
- [x] ✅ [DATA] P0. **2c. cefi MVP read-time gate (re-scoped — the manifest-pruning script is RETIRED).** Do NOT run
      `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` — DATA-LOSS: its `_derive_base` mis-parses Bitfinex
      `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → would DELETE ~380k legit **captured** BITFINEX/KRAKEN rows; also
      circular (honest-coverage-v2 forbids deriving the denominator from the manifest). Instead apply the MVP filter as
      a **read-time gate in `measure_honest_coverage`**, folded into 2a `build_expected`. **PREREQ: 2b + the ASTER split
      landed.** Gate: MVP-cut applied at read time, ZERO manifest rows mutated, cefi measure honest. **DONE 2026-07-06 —
      instruments-service@2fa3877 (slot-8 planning).** New public
      `check_enumeration_completeness.filter_manifest_to_expected(ag, df)` filters manifest to rows whose canonical
      `(venue, itype, dt)` key is in `build_expected(ag)` — MVP scope baked in via `get_mvp_data_types_for_cefi_venue`.
      `measure_honest_coverage._compute_coverage` calls the filter for cefi (`_MVP_READ_TIME_GATE_AGS = {"cefi"}`)
      BEFORE Layer-2 counting; Layer-1 keeps the UNFILTERED df so stray_tuples remain visible. ZERO manifest mutation
      (returns a filtered VIEW; input df untouched). Same canonical key as the L1 check (`_canon_key` — case-fold + UAC
      alias + bundle rollup + cefi venue-fold OKX-SPOT→OKX/etc). Smoke test demonstrated: BYBIT-SPOT/perpetual/trades
      manifest row → dropped from Layer-2, still visible in Layer-1 stray_tuples (writer PERPETUAL-stamp defect surfaced
      honestly). 11 unit tests (`tests/unit/scripts/test_filter_manifest_to_expected.py`) + 21 existing measure tests
      green (fake-checker stub updated with passthrough). QG-green 92s (sentinel 4368f381e). Filter is oracle-based on
      `build_expected`, so 2b/ASTER-split changes propagate through automatically at re-measure time (task 5 — P2, gates
      on 2a–2f + ASTER wire + KALSHI-PERP purge).
- [x] ✅ [CODE] P1. **2f. Reapply the denominator-gap model to LIGHTER / EXTENDED / PACIFICA** — they share the ASTER
      live-WS/no-REST profile, so the same start-date-gated treatment applies once enumerator `start_date` support
      exists. **PREREQ: 2b + enumerator `start_date` support.** Gate: LIGHTER/EXTENDED/PACIFICA EXPECTED correct;
      tuple-diff clean. **DONE 2026-07-08 — checkpoint-only, no code change (slot-8 planning).** Both PREREQs confirmed
      landed: 2b (`-002`) flipped 2026-07-07; enumerator `start_date` support (`-007`) landed
      `instruments-service@4a8cff7` (per-`(venue, dt)` gate in `_enumerate_v2_cefi`, fully generic — no ASTER-specific
      code path, verified by reading `enumerate_expected_universe.py:1073-1135`). The LIGHTER-ZKSYNC / EXTENDED-STARKNET
      / PACIFICA-SOLANA `VENUE_DATA_TYPE_CAPABILITIES` entries (trades/book_snapshot_5/ derivative_ticker + start_dates)
      were already landed as part of D2b — `unified-api-contracts@e76d874a` (2026-07-06) — confirming the slot-6 note in
      the `-005` re-measure entry above. Dynamic Gate verification (no golden edit needed — this is the same mechanism
      ASTER uses, generically applied): `.venv/bin/python -c "from expected_universe import build_expected; ..."` →
      `build_expected('cefi')` returns exactly 3 tuples per venue for all three —
      `(<venue>, perpetual, book_snapshot_5)`, `(<venue>, perpetual, derivative_ticker)`, `(<venue>, perpetual, trades)`
      — matching the ASTER live-forward profile byte-for-byte (ASTER itself currently also resolves to the same 3-tuple
      set at this measurement grain). Tuple-diff clean: no code change required to close this Gate. **Adjacent findings
      surfaced during verification — filed below, NOT fixed inline (out of -004's scope,
      cross-repo/architecture-decision territory):** (1) cefi Layer-1 golden fixture
      (`tests/unit/scripts/goldens/expected_universe/cefi.json`) is stale (75 vs actual 71 tuples) from the 2026-07-07
      bare-OKX/BYBIT `SPOT_PAIR` removal (`instruments-service@23fa3a99`) never being regenerated; (2) that same removal
      left **OKX-SPOT with ZERO EXPECTED tuples anywhere** — a genuine denominator hole, NOT just a stale fixture (see
      new BLOCKED-OPERATOR-DECISION todo below); (3) a month-old regression test
      (`test_default_exchanges_cover_captured_cefi_venues`, landed 2026-06-08 `is@ff063a28`) asserts `lighter-zksync`
      must be a Tardis exchange id in IS's `_DEFAULT_EXCHANGES`, but the current UAC `VenueMapping.all_tardis_exchanges`
      SSOT does not contain it — contradicts the 2026-07-06 D2b comment stating LIGHTER/EXTENDED/PACIFICA are
      native-REST/WS, not Tardis-routed. instruments-service QG is RED on LDR HEAD from these 2 test failures (verified
      via `bash scripts/quality-gates.sh --no-fix`: 2 failed, 4056 passed) — independent of anything shipped in this
      task; no commit made against instruments-service this turn since a golden-only fix cannot land through a QG gate
      that's red for unrelated reasons. Regenerated golden held locally then reverted (`git checkout --`) rather than
      shipped uncommitted-with-caveats.
- [x] ✅ [SCRIPT] P2. **Re-measure + re-certify the cefi Layer-1 row** on the corrected catalogue (consolidates the two
      old re-measure todos). **PREREQ: 2a–2f landed + the ASTER live wire (Plan 5) + the KALSHI-PERP purge (Stage-3
      cross-plan prereq — 25,473 fake `KALSHI-PERP` rows pollute cefi Layer-2).** Gate: fresh cefi Layer-1 recorded in
      the Progress Log; denominator GREW, % dropped (honest). Feeds the global Stage-3 certify (Plan 4). **DONE
      2026-07-07 — instruments-service@<f722845> (slot-6 planning).** Ran `measure_honest_coverage --asset-group cefi`
      at 08:54 UTC: cefi Layer-1 = **72.60%** (present 53 / expected 73), denominator_status INCOMPLETE (20 missing, 87
      stray). Trajectory: 65.91% on 44 tuples (2026-06-29 cert) → 73.61% on 72 tuples (D2a fold + 2b) → **72.60% on 73
      tuples** (post uac@3652f99f -008 ASTER book_snapshot_5 live-wire cap flip). Denominator GREW +1 (ASTER perpetual
      book_snapshot_5); % dropped honestly (the new tuple has 0 captured rows — awaiting live-wire capture from the
      aster_book_liq_ws connector). Full details in the Progress Log entry below.

**Operator decision — agent RAISES via blocked-queue, operator answers later (do NOT guess):**

- [x] ✅ [DESIGN] P1. **COINBASE / DERIBIT-COMBO MVP_SCOPE membership — RESOLVED 2026-07-10 (operator decision #6: "keep
      both declared").** `DERIBIT-COMBO` added to `MVP_SCOPE["cefi"].venues` + a required `venue_data_types` override
      ({trades, book_snapshot_5} — without it DERIBIT-COMBO would inherit bare DERIBIT's OPTION->{options_chain}
      override, a phantom cell it cannot produce) + the matching `VENUE_DATA_TYPE_CAPABILITIES["DERIBIT-COMBO"]` entry —
      dynamically verified `build_expected("cefi")` now yields `(DERIBIT-COMBO, options_chain, trades)`, previously
      silently zero. The per-venue cost-control mechanism the operator recalled for COINBASE ALREADY EXISTS
      (`CeFiMvpRule.venue_data_types` v11, 2026-06-28) and already scopes `COINBASE-FUTURES` (=Coinbase INTX) to
      trades-only — zero code change needed there. Bare `COINBASE` was deliberately NOT added — a concurrently-shipping,
      operator-approved migration (`coinbase_bare_name_migration_2026_07_06.md`, `unified-api-contracts@42270f63`)
      retired bare `COINBASE` entirely in favor of the sole canonical `COINBASE-SPOT` (already declared + already
      trades-only scoped); adding a dependency on the retired key would work against that migration. Shipped
      `unified-api-contracts@5626079e`.

- [x] ✅ [SCRIPT] P1. **NEW FINDING 2026-07-14 (data_engineering slot-2, mvp_backfill_cefi_tick_v10 G4):
      BITGET-FUTURES's 16 real dated-quarterly FUTURE symbols are now RESOLVABLE (base/quote + margin_type fixed this
      session, `instruments-service@cd902fb1` + `@75bdf02d`) but still can't reach `prod/catalog.parquet` — a live
      re-fetch grew the raw URDI universe 714→1010 (confirmed via
      `--operation instruments --mode batch --venues BITGET-FUTURES     --force`, log: "Venue count OK: BITGET-FUTURES
      grew 714 → 1010 (+296)"), but ALL 16 dated futures had ALREADY EXPIRED by the fetch date (2026-07-14) — Tardis's
      own `availableTo` for every one of them predates today (e.g. `BTCUSDH25` availableTo=2025-03-29) — so the per-day
      `instrument_availability/by_date/day=2026-07-14/...` snapshot's date-active filter drops them all (confirmed:
      `day=2026-07-14/venue=BITGET-FUTURES` is 718/718 PERPETUAL, 0 FUTURE). Per
      `scripts/build_instrument_catalogue.py`'s own docstring, `prod/catalog.parquet` is a **pure roll-up of the by_date
      snapshot history** (`available_from`/`available_to` = first/last day an instrument APPEARS in a by_date snapshot)
      — so a symbol that expired before its FIRST correctly-parsing fetch can never enter the catalogue via the normal
      daily refresh, no matter how many times it's re-run today or in the future. **Same bug class as the 2026-07-09
      Bybit/Kraken-Futures precedent** (see `scripts/canonicalize_bybit_kraken_futures_catalog_2026_07_09.py`'s
      docstring: "confirmed 0/46 present in `prod/catalog.parquet` today (this bug silently dropped them at write time,
      historically, every day — there is nothing to relabel because nothing was ever captured). Re-capturing them is a
      separate live re-capture run via the normal adapter path") — that precedent's fix was a DEDICATED one-off script
      (`scripts/recapture_bybit_legacy_quarterly_futures_2026_07_09.py`, already cleaned up post-use, lifecycle=oneoff)
      that inserted new rows directly. **DONE 2026-07-14 — instruments-service@ad4be6d6 (slot-6 planning).** Shipped
      `scripts/recapture_bitget_futures_dated_futures_2026_07_14.py` (lifecycle=oneoff): (1) re-fetches BITGET-FUTURES's
      full universe live via `TardisReferenceDataAdapter.get_instruments()` (single free no-auth Tardis REST call, no
      whole-corpus GCS walk), filters to the 16 real FUTURE rows; (2) APPENDS the new rows directly to
      `prod/catalog.parquet` (backup-first — `prod/catalog.20260714-043942.bitgetfuturesfix.bak.parquet` — monotonic
      row-count-grows guard, refuse-on-duplicate-`instrument_id`), matching the established
      `canonicalize_*_catalog_2026_07_*.py` safety pattern. Ran `--apply --confirm` against prod: rows 358,439 → 358,451
      (+12), 0 duplicate `instrument_id` introduced (live-verified post-write). QG-green (174s, sentinel `94f53b20`).
      Dynamic Gate verification: `build_expected("cefi")` now yields
      `(BITGET-FUTURES, future, {book_snapshot_5, trades, derivative_ticker})` — previously silently zero.
      **Stop-on-surprise finding surfaced mid-run (NOT silently resolved)**: 4 of the 16 fetched rows (2 BTC + 2 ETH)
      hit a REAL canonical-`instrument_id` collision — `BTCUSDM26` (Jun-2026 contract) and `BTCUSDU26` (Sep-2026
      contract) both report `availableTo=2026-04-28` in Tardis's own metadata (live-verified 2026-07-14 via
      `api.tardis.dev/v1/exchanges/bitget-futures`; same for the ETH siblings), so the SHARED
      `_build_canonical_future_key` (parsing.py — every CeFi venue's dated-future capture routes through it) collapses
      two genuinely distinct real contracts onto one id (`BITGET-FUTURES:FUTURE:BTC-USD@INV-20260428` /
      `...ETH-USD@INV-20260428`). The script detects this defensively and skips the WHOLE collision group rather than
      silently keeping one contract and losing the other — those 4 rows (`BTCUSDM26`/`BTCUSDU26`/`ETHUSDM26`/
      `ETHUSDU26`) remain OUT of `prod/catalog.parquet`, tracked as the follow-up todo directly below (shared-code fix,
      out of scope for this one-off append — touches every CeFi venue's dated-derivative id construction). 12/16 real
      dated futures now close as G4 Layer-1 tuples; the remaining 4 need the disambiguation fix first.

- [x] ✅ [CODE] P2. **NEW FINDING 2026-07-14 (data_engineering slot-6): shared `_build_canonical_future_key` can collide
      two DISTINCT real dated-derivative contracts onto ONE canonical `instrument_id` when Tardis's own `availableTo`
      (the source the adapter falls back to for `expiry` when no symbol-string date-parse branch exists for the
      exchange) happens to coincide for both.** Surfaced while shipping the BITGET-FUTURES append directly above:
      `BTCUSDM26` (real Jun-2026 quarterly) and `BTCUSDU26` (real Sep-2026 quarterly) both report
      `availableTo=2026-04-28` (live-verified via `api.tardis.dev/v1/exchanges/bitget-futures`, same for
      `ETHUSDM26`/`ETHUSDU26`) — plausibly Bitget delisted/rotated both far-dated quarterlies on the same day, or
      Tardis's replay collection for this exchange hit a common cutoff. Either way, `adapter.py`'s
      `_build_canonical_future_key(venue, base, quote, margin_type, expiry)` (parsing.py) has no disambiguator beyond
      `expiry.strftime('%Y%m%d')`, so both contracts resolve to the identical id — a data-loss risk (whichever the
      catalogue roll-up captures LAST silently overwrites/aliases the other) for ANY CeFi venue where this shape recurs,
      not just BITGET-FUTURES. **This is the same collision-prone construction every CeFi venue's dated-future capture
      shares** (touches `instruments_service/reference_data/adapters/cefi/tardis/{adapter.py,parsing.py}` — out of scope
      for a one-off append script; recommend a disambiguation input beyond `expiry` alone, e.g. the CME month-code
      letter itself (`_BYBIT_MONTH_CODE_RE`'s `group(2)`, already parsed for the no-dash shape) folded into the
      canonical key, or falling back to `raw_symbol` in `instrument_key` specifically when two distinct symbols'
      `_build_canonical_future_key` outputs would otherwise collide. Gate: `BITGET-FUTURES:FUTURE:BTC-USD@INV-20260428`
      /`...ETH-USD@INV-20260428` each resolve to TWO distinct ids (one per real `raw_symbol`); the 4 rows currently
      skipped by `recapture_bitget_futures_dated_futures_2026_07_14.py` land in `prod/catalog.parquet` without
      introducing a duplicate. (repo: instruments-service) **DONE 2026-07-14 — instruments-service@4c2e354f (slot-9
      planning).** Added `_disambiguate_colliding_dated_derivatives` (adapter.py) as a post-pass over one exchange's
      parsed FUTURE batch (no extra API calls): when raw_symbols collide, it prefers the real CME month-code-derived
      expiry (the letter the raw_id itself already encodes — M=Jun, U=Sep, etc.) over the coincidentally-shared
      `availableTo` fallback when it genuinely separates the group, else falls back to embedding the always-unique
      `raw_symbol` in the legacy `VENUE:TYPE:RAW_ID` shape. Scoped to colliding groups only — already-correct rows are
      untouched (verified via a dedicated no-op regression test). 4 new tests in
      `tests/unit/test_bybit_kraken_futures_canonical_id.py::TestDisambiguateCollidingDatedDerivatives` (real-collision
      repro, 4-row disambiguation, non-colliding no-op, fallback-path unit test); 146/146 tests pass in the touched
      files; QG-green (97s, sentinel `4c2e354f`). **Gate closed dynamically, not just unit-tested**: re-ran
      `recapture_bitget_futures_dated_futures_2026_07_14.py` (dry-run) post-fix — the 4 previously-skipped rows now
      resolve to `BITGET-FUTURES:FUTURE:{BTC,ETH}-USD@INV-20260626` (Jun) /
      `BITGET-FUTURES:FUTURE:{BTC,ETH}-USD@INV-20260925` (Sep), zero collision-skip warnings, 12/16 already_present
      (unaffected). Applied for real (`--apply --confirm`): `prod/catalog.parquet` 358,451 → 358,455 rows (+4), backup
      `prod/catalog.20260714-051106.bitgetfuturesfix.bak.parquet`. Re-ran dry-run post-apply to confirm idempotency:
      `new=0 already_present=16 (of 16 fetched)` — all 16 real BITGET-FUTURES dated-quarterly FUTURE rows now present, 0
      duplicates (script's own monotonic-row-count-grows + duplicate-`instrument_id` guard passed before write). G4
      BITGET-FUTURES finding fully closed. One-off script deleted post-use per its own `Delete-when:` criteria (both now
      met) — `instruments-service@b9d0f6fc`.

- [x] ✅ [SCRIPT] P1. **NEW FINDING 2026-07-14 (data_engineering slot-2, mvp_backfill_cefi_tick_v10 G4): DERIBIT-COMBO's
      instrument catalogue is permanently LIVE-ONLY — can never backfill historical data.**
      `unified_api_contracts.registry.venue_adapter_keys.VENUE_TO_ADAPTER_KEY["DERIBIT-COMBO"] = "deribit_combo"` was a
      HARD, mode-independent mapping — `instruments_service/reference_data/factory.py::get_adapter_for_canonical_venue`
      only special-cased mode-routing (batch→Tardis / live→CCXT-or-live-adapter) for venues resolving to `"tardis"` or
      `"databento"` FIRST via `_resolve_uac_adapter_key`; DERIBIT-COMBO never reached that branch because its adapter
      key was already pinned to `"deribit_combo"` (`DeribitComboReferenceDataAdapter`,
      `instruments_service/reference_data/adapters/cefi/deribit_combo_adapter.py`) regardless of `mode="batch"` vs
      `"live"`. That adapter's own docstring says it's LIVE-only ("real-time active combos... complements the Tardis
      adapter which covers historical data") — but the historical Tardis-sourced combo path
      (`TardisReferenceDataAdapter` with `canonical_venue_override="DERIBIT-COMBO"`, `combos.py`'s leg parser already
      existed and was wired for it) was never actually invoked by the catalogue refresh for this venue.
      **Live-verified**: `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` filtered to
      `venue=DERIBIT-COMBO` has exactly **4 rows**, all `mvp=False`, all `available_from` in **2026-07** (i.e.
      "currently active as of the last live refresh"), zero rows for any earlier date — despite
      `VENUE_DATA_TYPE_CAPABILITIES["DERIBIT-COMBO"]["trades"] = "2022-08-23"` (live-verified against
      `api.tardis.dev/v1/exchanges/deribit`'s `type=='combo'` symbols per this plan's Addendum 5, 2026-07-12) declaring
      a real, much larger historical universe. **Consequence, confirmed by a real backfill VM this session**: relaunched
      `cefi-deribit-combo-2024-heavy` (post-fix — see `mvp_backfill_cefi_tick_v10_2026_06_27.md` G4 Re-Verification Run
      #6 for the accompanying MTDS venue-collapse fix, `market-tick-data-service@c9e6080f`) targeting `2024-01-01`;
      `run.log` shows the venue routing is now CORRECT (no more `venue=DERIBIT` collapse) but
      `NO SYMBOLS for deribit on 2024-01-01` — because the catalogue genuinely has zero DERIBIT-COMBO instruments dated
      that far back. **This means `(DERIBIT-COMBO, options_chain, trades)` can NEVER close as a G4 Layer-1 tuple until
      this catalogue-population gap is fixed** — no amount of backfill-VM relaunching will help; the denominator itself
      is starved.

      **DONE 2026-07-14 (data_engineering slot-7 planning) — `unified-api-contracts@89511de8` +
                          `instruments-service@e6fdfd00`.** Live-verified the premise first (`api.tardis.dev/v1/exchanges/deribit`
                          genuinely carries 68,847 `type=='combo'` symbols back to `availableSince=2022-08-23`, matching the finding
                          exactly). Implemented the recommended fix: `VENUE_TO_ADAPTER_KEY["DERIBIT-COMBO"]` flipped `"deribit_combo"` →
                          `"tardis"` (UAC); `factory.py::get_adapter_for_canonical_venue` special-cases `mode="live"` DERIBIT-COMBO to keep
                          routing to the `deribit_combo` REST adapter (extracted into `_build_deribit_combo_live_adapter` to stay under the
                          200-line function cap), so `mode="batch"` (default) now resolves to Tardis with `exchanges=["deribit"]` +
                          `canonical_venue_override="DERIBIT-COMBO"` (the `("DERIBIT-COMBO","OPTION"):"deribit"` itype-routing entry
                          already existed in `venue_instrument_type_to_tardis`, landed 2026-07-12). Went one step further than the
                          recommendation flagged: since the "deribit" Tardis exchange slug is shared with bare DERIBIT's own
                          option/future/perpetual/spot universe, `canonical_venue_override` alone would have mistagged that ENTIRE universe
                          as DERIBIT-COMBO — added a self-filter in `TardisReferenceDataAdapter.get_instruments()` restricting to
                          `type=='combo'` rows when the override is set (the venue_mapping.py comment had already flagged this as
                          not-yet-done). Corrected the adapter's own docstrings + the `honest-absence-downstream-handling.md` codex SSOT
                          § "DERIBIT-COMBO historical unavailability" (2026-06-27), which had over-broadly concluded "no data source can
                          serve it" — that was only ever true of Deribit's own REST `get_combos` endpoint, not Tardis's independent
                          archived feed; SUPERSEDED-banner added rather than deleted, per the codex-alignment rule. Added regression tests:
                          factory batch/live routing (`test_deribit_combo_batch_routes_to_tardis`,
                          `test_deribit_combo_live_routes_to_rest_adapter`), the Tardis combo-type self-filter
                          (`test_deribit_combo_override_filters_to_combo_type_only`), and fixed a stale assertion
                          (`test_factory_contains_deribit_combo` previously asserted the old `"deribit_combo"` value). QG-green both repos
                          (`.qg_last_passed_sha=89511de8c5bdb8fac79d5569e5c627fed44324a4` UAC,
                          `.qg_last_passed_sha=e6fdfd0061d0fa3d88afa40975530e48b1d13bb5` instruments-service; 4409+ tests). **Next step (not
                          this todo — a backfill VM relaunch, not code)**: re-run `cefi-deribit-combo-2024-heavy` against this fixed code to
                          close `(DERIBIT-COMBO, options_chain, trades)` as a G4 Layer-1 tuple; tracked in
                          `mvp_backfill_cefi_tick_v10_2026_06_27.md`.

                          **CORRECTION 2026-07-14T07:00Z (data_engineering slot-2) — the "next step" above is INCOMPLETE, live-verified**:
                          a bare tick-data VM relaunch is NOT sufficient by itself. Ran
                          `instruments-service --operation instruments --mode batch --venues DERIBIT-COMBO --start-date 2024-01-01
                          --end-date 2024-01-01 --force` as a direct empirical test of the routing fix: it correctly fetched **68,847 real
                          Tardis combo instruments** and derived **203 genuinely active on 2024-01-01**, writing a real
                          `instrument_availability/by_date/day=2024-01-01/venue=DERIBIT-COMBO/instruments.parquet` snapshot — **confirms the
                          routing fix works end-to-end for reference-data enumeration.** But `prod/catalog.parquet` (checked immediately
                          after) still carries only the OLD 4 stale rows (`available_from` all in 2026-07, pre-fix artifacts) — MTDS's
                          `_resolve_symbols` reads the ROLLED-UP catalogue as its PRIMARY source
                          (`_catalogue_symbols_for_venue_date`), not individual `by_date` snapshots, and `build_instrument_catalogue.py`
                          derives each instrument's `available_from`/`available_to` window by scanning ALL `by_date` snapshots that exist —
                          with only ONE snapshot written (2024-01-01), running the rollup NOW would incorrectly derive
                          `available_from=available_to=2024-01-01` for all 203 symbols (a **correctness regression**, not a fix — every
                          other date would then see zero active DERIBIT-COMBO instruments). **Did NOT run the rollup** given this risk.
                          **Real remaining scope**: a historical `by_date` backfill across a representative date range (not full daily
                          granularity necessarily — the roll-up's actual interpolation tolerance vs. sample-date density is unverified and
                          itself needs a design pass) BEFORE the catalogue rollup + tick-data VM relaunch. This matches — and validates —
                          this todo's own `design`-class / `assigned_vm: planning` scoping; deliberately not attempted further this session
                          (time-boxed G4 verification task, not this issue's dispatch).

                          *(Historical note: this todo's text previously carried a garbled, unrelated OKX-SPOT/QG-red pointer glued onto
                          the end from an editing mistake — removed 2026-07-14 during this flip. That OKX-SPOT content is tracked
                          independently and in full at `plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`,
                          which already carries its own open DESIGN todo — nothing was lost.)*

**BYBIT-SPOT writer defect (independent of the gate work — can run in parallel with 2a):**

- [x] ✅ [CODE] P1. Diagnose + fix the BYBIT-SPOT `PERPETUAL` itype stamp (MTDS `symbol_rules._VENUE_INSTRUMENT_TYPE`
      has `"BYBIT": "perpetual"` but NO `BYBIT-SPOT` entry → spot rows fall through to PERPETUAL); add the map entry,
      fix the writer path, corrective-relabel existing rows. **Smoke-first** (relabel ONE shard + verify the manifest
      split, then scale). Gate: BYBIT-SPOT rows carry SPOT_PAIR; manifest `by_venue_instrument_type` shows the split.
      **CODE FIX DONE 2026-07-07 — market-tick-data-service@c4df8ae0 (slot-8 planning).** Root cause verified in TWO
      authorities: (i) `TardisAdapter._classify_row_instrument_type` at `tardis_adapter.py:321` — SPOT-venue set did not
      include `"BYBIT-SPOT"` so BYBIT-SPOT batch rows (arriving via the `bybit-spot` Tardis exchange) fell through to
      `return InstrumentType.PERPETUAL`; (ii) `symbol_rules._VENUE_INSTRUMENT_TYPE` — had bare `"BYBIT": "perpetual"`
      but no `"BYBIT-SPOT"` entry (unlike `BITFINEX-SPOT` / `BITGET-SPOT` / `KRAKEN-SPOT` which map → `spot`). Fixed
      both + regression test extended in
      `test_tardis_canonical_output.py::test_classify_row_instrument_type_option_future_perp_spot` covering BYBIT-SPOT
      (BTCUSDT / SOLUSDT) → SPOT_PAIR AND bare BYBIT (BTCUSDT) → PERPETUAL so the BYBIT-SPOT fix cannot silently regress
      BYBIT-FUTURES rows and vice versa. QG-green (sentinel `c4df8ae0`; retried three times through peer BITGET-SPOT +
      COINBASE-FUTURES connector landings). **Corrective-relabel DEFERRED — BIG FINDING, main-agent BLK-aff71ec9
      verdict**: the manifest state is materially larger than this plan's text anticipates (135,444 BYBIT-SPOT rows:
      81,659 EMPTY instrument_type + 53,785 PERPETUAL; ~54k rows under spot-nonsense data_types derivative_ticker /
      futures_chain / options_chain / ohlcv_1m / perp_funding / liquidations — likely stray / mis-routed captures over
      months, not just the PERPETUAL stamp defect). A simple PERPETUAL→SPOT_PAIR relabel of the 53k subset would NOT
      close the Gate ("manifest by_venue_instrument_type shows the split") because 82k EMPTY-instrument_type rows + 54k
      spot-nonsense-data_type rows remain in states not modeled by this plan's relabel step. Filed follow-up issue doc
      **`plans/active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md`** with 4 tracked todos: (a) diagnose the
      82k EMPTY rows; (b) diagnose the 54k spot-nonsense-data_type rows; (c) ship the corrective-relabel script gated on
      (a)+(b); (d) populate `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` in UAC. Main-agent explicitly ruled: "-006
      forward-path fix (code) is the deliverable; mark DONE after the commit + issue doc are in; do not hold it open for
      the remediation." Operator notified via the issue doc — the stray-data_type finding may indicate re-capture (not
      just relabel) is needed for that subset.

## ASTER live-forward mode split (C1 RESOLVED — Ikenna 2026-07-03; sequencing is load-bearing)

Decision (recorded in `instruments_service_plan_reconciliation_2026_06_29.md` § C1): ASTER batch+live =
`trades`/`derivative_ticker`/`perp_funding`; **live-only-forward** = `book_snapshot_5` + `liquidations` (prediction-AG
pattern — live capture accumulates the history batch cannot provide; pre-wire history stays typed honest absence).
Capability check found the connectors already built (`aster_book_liq_ws.py`) but unwired, and ONE structural gap:
nothing date-gates seeding at the (venue, data_type) grain. Execute IN ORDER:

- [x] ✅ [CODE] P1. **Enumerator honours per-(venue,dt) `start_date`** — `_row_data_types`/the cefi date loop must read
      `get_venue_data_type_start_date(venue, dt)` and seed `expected_unattempted` only from that date (earlier days →
      typed `EXPECTED_*` absence or out-of-universe). PREREQ for the capability flip — flipping first re-creates the
      17,282-row over-seed purged 2026-07-03. **DONE 2026-07-07 — instruments-service@4a8cff7 (slot-5 planning).**
      `_enumerate_v2_cefi` pre-computes `dt_start_ts_by_dt` once per instrument (one `get_venue_data_type_start_date`
      UAC lookup per data_type — priority order: `VENUE_DATA_TYPE_CAPABILITIES` → `VENUE_REFERENCE_DATA_CAPABILITIES` →
      `VenueMapping.venue_start_dates` venue-level fallback). Alive branch consults the gate PER data_type before the
      expected_unattempted seed: dates before the declared start_date now emit `EXPECTED_PRE_SOURCE_COVERAGE_START`
      (empty_confirmed, closed-set-compliant) instead of `expected_unattempted`. Gate is scoped to manifest-aware mode
      (present_set is not None); legacy mode alive- branch continues to skip (unchanged). 4 new regression tests in
      `test_enumerate_expected_universe_v2.py` cover (i) alive < dt_start → EXPECTED_PRE_SOURCE_COVERAGE_START
      (HYPERLIQUID trades scenario, 2024-06-01 pre-2025-03-22), (ii) alive == dt_start → expected_unattempted
      (unchanged), (iii) per-data_type independence (HYPERLIQUID trades pre-2025-03-22 AND book_snapshot_5
      post-2023-04-15 on the same date → different reasons), (iv) unknown venue/dt permissive (no fallback → no gate
      applied). QG-green 93s (sentinel `7ded594`). 126/126 v2 unit tests pass + 102/102 across related enumerator suites
      (`test_enumerate_expected_universe`, `test_check_enumeration_completeness`, `test_filter_manifest_to_expected`,
      `test_expected_universe_golden`). Unblocks -008 (UAC capability flip for ASTER `book_snapshot_5` + `liquidations`
      — the 8-time bounced backlog task), -004 (2f LIGHTER/EXTENDED/PACIFICA), and -005 (re-measure).
- [x] ✅ [CONFIG] P1. **UAC capability flip** — add `book_snapshot_5` + `liquidations` to
      `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` with `start_date` = the live-wire date; resolves the standing UAC
      self-contradiction with `EXPECTED_COVERAGE._CEFI["ASTER"]` (which already lists both). **DONE 2026-07-07 —
      unified-api-contracts@3652f99f (slot-2 planning).** Added `book_snapshot_5: "2026-06-23"` +
      `liquidations: "2026-06-23"` to `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` at
      `unified_api_contracts/registry/market_data_categories.py:1148-1150`. Live-wire date = mtds@d43fd62 (the
      2026-06-23 aster_book_liq_ws.py code-land commit — Binance-Futures-compatible WS via `wss://fstream.asterdex.com`,
      `<sym>@depth5@100ms` + `!forceOrder@arr`); pre-2026-06-23 dates stay typed `EXPECTED_PRE_SOURCE_COVERAGE_START`
      via the enumerator's per-(venue,dt) start_date gate landed at instruments-service@4a8cff7 (task -007), so the
      17,282-row over-seed purged 2026-07-03 does NOT re-materialise. Updated the comment block above the ASTER entry to
      reflect batch+live vs live-only mode-split; also updated the test-suite: flipped
      `test_aster_book_snapshot_5_is_empty` → `test_aster_book_snapshot_5_and_liquidations_seeded` to assert
      book_snapshot_5 now seeds non-empty (liquidations is venue-level so falls back to Tier-2 empty by design), and
      dropped the now-stale ASTER example from the "capability not declared" comment inside
      `get_expected_instruments_for_venue`. Peer commit `e17b185f` (unblocking the 20 pre-existing WS-cassette map gaps)
      landed first, so QG went from RED→GREEN mid-shipflow; sentinel@3652f99f matches HEAD, quickmerge shipped clean.
      UNBLOCKS -004 (2f LIGHTER/EXTENDED/PACIFICA still gated on their own capability flips + start_date declarations)
      and -005 (re-measure — verify UAC ASTER capability flip landed on LDR before re-dispatch, per slot-11
      BLK-817416c3).
- **[→ AO PLAN 5, INFRA role]** Register + launch the live connector `aster_book_liq_ws.py` into
  `live/connector_registry.py` + a live VM (KALSHI-PERP book5 VM is the in-cefi template); verify `live_aster` rows land
  (per-VM shard spot-check at T+10-15min). Connector SSOT: `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` BUG #4.
  _(Moved to the capture/infra plan for role-homogeneity — an INFRA VM launch is not a `data_engineering` task. This
  plan's 2c/2f re-measure PREREQs on it; tracked cross-plan.)_
- **[→ folded into the consolidated re-measure above]** Re-measure post-wire; ASTER book5/liquidations become
  expected-from-wire-date; the same model then applies to LIGHTER/EXTENDED/PACIFICA (2f) — they share the
  live-WS/no-REST profile.

## C2 point-fix (CONFIRMED — Ikenna 2026-07-03, direction (c))

The venue-blind denominator producer gets the MVP-gate intersection now; the structural single-producer fold (A17
`build_expected`) stays owned by `honest_coverage_v2_instrument_denominator_2026_06_28.md`.

- [x] ✅ [CODE] P1. **Point-fix `_row_data_types` (cefi branch): intersect with
      `get_mvp_data_types_for_cefi_venue(venue)`** so the seeded denominator matches the capture gate (kills the MVP-cut
      over-seed class, e.g. COINBASE-SPOT trades-only). Complements the 2026-07-03 capability carve-out
      (`instruments-service@3bb7acd`) — that closed the VENUE_DATA_TYPE_CAPABILITIES half; this closes the MVP half. ~5
      lines + tests. **DONE 2026-07-06 — instruments-service@2170d9a3 (slot-11 planning).** Bundle-aware MVP data_type
      gate landed in `_row_data_types` cefi branch (lines 873-899): `_mvp_capture_itype` normalises
      OPTIONS_CHAIN/COMBO→OPTION and FUTURES_CHAIN→FUTURE; when the bundle-normalised itype is NOT in
      `MVP_SCOPE["cefi"].instrument_type_data_types` (i.e. the flat/leaf case like COINBASE-SPOT trades), the
      venue-level MVP-gate intersection is applied against `get_mvp_data_types_for_cefi_venue(venue)`; when it IS in the
      override (Deribit OPTION → {options_chain}) the intersection is SKIPPED, preserving the upstream-narrowed
      `["options_chain"]` slice. A venue absent from MVP scope entirely returns an empty MVP set → the `if mvp_dts:`
      guard leaves row_dts unchanged (no blanket-block of non-MVP-scoped venues like BINANCE-DELIVERY). 4 regression
      tests added to `test_enumerate_expected_universe.py` covering COINBASE-SPOT drop-book5, Deribit
      options_chain/futures_chain survival, Deribit PERP drop-liquidations, and non-MVP-venue skip. QG-green (181s).
      Both failure modes flagged in the CAUTION avoided by the bundle-normalised `instrument_type_data_types` guard. >
      **⚠️ CAUTION (verified 2026-07-06, do not implement naively):** a literal >
      `get_mvp_data_types_for_cefi_venue(venue)` intersection breaks Deribit `options_chain` enumeration. That > helper
      is venue-only — it resolves DERIBIT to the flat cefi set (`trades`/`book_snapshot_5`/ >
      `derivative_ticker`/`funding_rate`), which does NOT contain `"options_chain"`. But `_row_data_types` for a >
      Deribit OPTION row has already been correctly narrowed upstream (via >
      `valid_data_types_for_venue_instrument_type` + `instrument_type_data_types={"OPTION": {"options_chain"}}`) > to
      `["options_chain"]` — intersecting that against the flat venue set empties it, silently wiping the > Deribit
      options_chain denominator (the exact G1 backfill `mvp_backfill_cefi_tick_v10` centers on). Confirmed > by running
      the change: no existing unit test in `test_enumerate_expected_universe*.py` currently covers > Deribit OPTION
      through `_row_data_types` directly, so this would NOT be caught by the existing suite — add a > Deribit-options
      regression test in the SAME commit as this point-fix. > A second attempt using the instrument-type-aware
      `is_mvp("cefi", venue, instrument_type, data_type)` instead > (to preserve the OPTION override) ALSO breaks:
      `is_mvp`'s cefi branch requires a `base_ccy` axis check > (`rule.base_ccys`) that `_row_data_types` has no way to
      supply from `InstrumentCatalogEntry` — calling it > with `base_ccy=None` fails that gate and wipes `row_dts` for
      every venue's every data_type, not just the > intended MVP-cut venues (confirmed via 17 failures across
      `test_enumerate_expected_universe_v2.py`, > including plain BTC/trades cases with no MVP-scope involvement at
      all). `is_mvp` also expects raw > instrument_type values (`OPTION`/`FUTURE`), not the post-bundle-rollup names
      (`options_chain`/ > `futures_chain`) `_row_data_types` sometimes receives from `enumerate_v2` — a second
      incompatibility > independent of the first. > **Net: this point-fix needs to be instrument-type/bundle-aware** —
      e.g. skip the intersection entirely when > `row_dts` was already narrowed by a non-trivial
      `instrument_type_data_types` override (Deribit OPTION, > possibly other bundle types), and only apply the
      venue-level MVP-gate intersection to the flat/leaf case > (e.g. COINBASE-SPOT). A correct implementation is closer
      to 15-20 lines + a Deribit-options regression test > than the original ~5-line estimate. Full trace of both failed
      attempts (reverted, no residue): > `unified-api-contracts@0e3989ce`+revert `8cc76fd0`,
      `instruments-service@86354d75`+revert `77314c0e` (local, > unpushed, this slot only — safe to ignore, kept for
      anyone who wants the failure detail).
- [x] ✅ [CODE] P2. **Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it** — **DEFERRED 2026-07-06 —
      v1 is NOT safe to delete.** Slot-10 investigation (`BLK-0ac84889`) confirmed three v1 roles v2 does NOT cover: (1)
      `_enumerate_v2_sports` explicitly delegates `EXPECTED_PRE_SOURCE_COVERAGE_START` dates to v1 (docstring L1552-1555
      "v2 must NOT re-emit them or the (data_type, date) cell is double-counted at two grains"); (2)
      `tests/integration/test_enumerate_v2_superset_property.py` documents "tradfi v1 (non-trading days) is NOT a v2
      grain match — v2 doesn't enumerate weekend/holiday cells" as an INTENTIONAL asymmetry; (3) v2 pre-venue-launch
      coverage is per-catalog-instrument grain vs v1 venue-grain sentinel — empty-catalog windows would lose seeding.
      Cross-repo cleanup also required in deployment-service (INFRA role). Main-agent ruling: BLOCK the full v1
      deletion; file issue doc noting the finding. **Follow-on todos filed in
      `plans/active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md`** covering v2 coverage extension (tradfi
      calendar + sports pre-coverage + venue-grain pre-launch sentinel), deployment- service infra cleanup, and the
      final v1 delete after those land. Evidence: no code change this pass; issue doc is the tracked-work artifact.

## Related fragility (observed live 2026-07-03)

- **Freshest-bucket PRIMARY selection is fragile to manifest surgery.** `measure_honest_coverage._read_manifest` picks
  the candidate with the newest `blob.updated` as PRIMARY (full frame) and reads the other as SECONDARY (**eu-only**).
  Rewriting the legacy cefi index (the ASTER corrective pass) bumped its mtime past prd → roles flipped → prd's
  captured-only tuples (e.g. BINANCE-FUTURES `future` rows consolidated 06-29) dropped from ENUMERATED and 3 artifact
  "holes" appeared. Mitigated in-session by a metadata bump restoring prd as freshest, but any future surgery on the
  older bucket re-triggers it. Consider content-based freshness (max manifest date) or pinning prd as primary. This may
  also explain the anomalous 05:07 UTC 2026-07-03 cefi-only measure (61.36%, present 29→27).
- [x] ✅ [CODE] P2. Harden `_read_manifest` primary selection against surgery-bumped mtimes (content-based freshness or
      pinned-primary with explicit override). **DONE 2026-07-06 — instruments-service@5b04878 (slot-5 planning).**
      `measure_honest_coverage._read_manifest` now pins PRIMARY to the first accessible candidate in
      `_MANIFEST_BUCKET_CANDIDATES[asset_group]` tuple order (which places the `-prd` bucket first by construction for
      every AG). `blob.updated` mtime is still logged for visibility but no longer drives selection — the 2026-07-03
      ASTER-corrective-pass scenario (surgery on legacy bucket bumped its mtime past prd, flipping roles and producing 3
      artifact "holes") is now a regression-tested guard. New `--primary-bucket=<name>` operator override forces a
      specific candidate when surgery or debugging demands it (falls back to the tuple-order pin with a warning if the
      named bucket is not accessible). New `_warn_if_secondary_newer` logs a `SURGERY-SIGNAL` warning when a secondary
      bucket has a newer mtime than primary, so operators can spot the anomaly and decide whether to switch primary via
      the override. 4 new/rewritten unit tests: `test_prd_wins_over_legacy_by_tuple_order`,
      `test_pinned_primary_wins_when_secondary_mtime_is_newer` (regression guard cite the 06-29 BINANCE-FUTURES/future
      scenario), `test_row_count_no_longer_a_tiebreaker`, `test_override_wins_over_tuple_pin_when_accessible`,
      `test_override_falls_back_to_pin_when_not_accessible`. All 24 module tests pass; QG-green (94s, sentinel
      `9263c803`).

## Progress Log

- **2026-07-03** — Filed from the reconciliation implementation session. Context: the venue-suffix fold + ASTER
  carve-out shipped in `instruments-service` (see the reconciliation issue doc); this finding is the structural
  remainder. Also noted: `INSTRUMENT_TYPES_BY_VENUE` exists in UAC and already covers most of the gate-blind venues —
  strongest candidate for the (venue,itype) authority.
- **2026-07-06** — **2a landed** (`instruments-service@681f50a`, slot-8 planning). Single-producer consolidation:
  `scripts/expected_universe.py::build_expected(asset_group)` is now THE Layer-1 EXPECTED producer;
  `check_enumeration_completeness._build_expected_tuples` delegates via sibling-load; `measure_honest_coverage` routes
  transitively. Byte-identical output preserved for all 5 AGs (cefi 72 / defi 171 / tradfi 35 / sports 27 /
  prediction 8) — captured as goldens under `tests/unit/scripts/goldens/expected_universe/`. New regression
  `test_expected_universe_golden.py` (14 tests: contract
  - delegator parity + golden byte-identical). Full suite green: 76 impacted tests + QG (105s). MVP_SCOPE
    COINBASE/DERIBIT-COMBO question surfaced as `BLK-5cc7590e` (verified empirically: both declared in
    `VENUES_BY_ASSET_GROUP["cefi"]` but `get_mvp_data_types_for_cefi_venue()` returns `frozenset()`); per plan warning,
    raised for operator decision rather than guessed — 2a itself is byte-identical so the silent zero persists exactly
    as before, and 2b/2c will act on the answer. 2a UNBLOCKS 2b (cefi gate-authority fix on `build_expected`).
- **2026-07-06** — **2f dispatch blocked on missing PREREQs** (slot-8 planning, `BLK-02a4b067`). Task 2f
  (`cefi_layer1_denominator_gaps-004`, "Reapply the denominator-gap model to LIGHTER / EXTENDED / PACIFICA") was
  dispatched by priority=20 alone — but the plan-declared PREREQ chain (`2b + enumerator start_date support`) is not
  machine-encoded on the backlog task, so the dispatcher missed it. Verified in code:
  `instruments-service/scripts/expected_universe.py` has zero `start_date` awareness; the only consumer of
  `get_venue_data_type_start_date` today is `market-tick-data-service/…/orchestrator/sentinels.py` +
  `instruments-service/scripts/cefi_per_venue_capture_summary.py` — the enumerator itself does not read it. Additionally
  verified LIGHTER's REST `_fetch_lighter_book_for_symbol` stamps `datetime.now(UTC)` as timestamp (not the requested
  date) — confirming the ASTER live-WS/no-REST profile for `book_snapshot_5`; a UAC capability flip that adds start_date
  before the enumerator honours it would re-create the 17,282-row over-seed the plan warns against. Main-agent verdict:
  skip -004, add `depends_on: [cefi_layer1_denominator_gaps-002, cefi_layer1_denominator_gaps-007]` to task -004 in
  `backlog.yaml` and regen so the dispatcher gates it correctly. 2f resumes when `-002` (2b) + `-007` (enumerator
  start_date) both land.
- **2026-07-06** — **UAC capability flip PARKED — BLOCKED-PREREQUISITES** (slot-8 planning, `BLK-36eeb447`). Task
  `cefi_layer1_denominator_gaps-008` (UAC capability flip — add ASTER `book_snapshot_5` + `liquidations` to
  `VENUE_DATA_TYPE_CAPABILITIES` with `start_date` = live-wire date, target
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144`) was dispatched by priority=20
  alone — SAME machine-encoded `depends_on` gap as -004. Verified LDR tip:
  `instruments-service/scripts/expected_universe.py`
  - `check_enumeration_completeness.py` still have zero `start_date` references; task -007 (enumerator `start_date`
    support) is `status=dispatched` to a peer slot but has NOT reached LDR (no commit to either file since 2a). Plan is
    explicit: "**PREREQ for the capability flip — flipping first re-creates the 17,282-row over-seed purged
    2026-07-03.**" Main-agent verdict (`BLK-36eeb447` answered): PARK -008; do NOT touch UAC
    `VENUE_DATA_TYPE_CAPABILITIES` until -007 confirmed shipped to LDR; the machine-encoded `depends_on` fix is an
    operator backlog.yaml action. -008 resumes when `-007` (enumerator `start_date`) lands. Slot-8 rotated to
    `cefi_layer1_denominator_gaps-009` (C2 point-fix).
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (2nd dispatch)** (slot-7 planning,
  `BLK-d8cba69b`). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-7 by priority=20 alone (the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` is still uncorrected on the backlog task —
  `depends_on: None` verified via `/api/backlog?limit=500`). Re-verified LDR tip at re-dispatch time:
  `instruments-service/scripts/expected_universe.py` + `check_enumeration_completeness.py` still have zero `start_date`
  references (last touching commits: `a1038ee` 2a, `2fa3877` 2c — neither adds start_date). Task -007 is
  `status=dispatched` to slot-11; tmux pane capture confirms slot-11 mid-work adding a per-`(venue, dt) start_date`
  regression test to `test_enumerate_expected_universe_v2.py`, but NOT yet shipped to LDR. Main-agent verdict
  (`BLK-d8cba69b` answered): PARK -008 — same ruling as `BLK-36eeb447`; the 17,282-row over-seed risk is real and
  documented; -008 will be re-dispatched after -007 lands. Slot-7 handed `understat_local_backfill_completion-004`
  (unrelated manifest normalisation) as next task.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (4th dispatch, `BLK-9072b84f`)** (slot-5
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-5 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` + `BLK-d8cba69b` is still uncorrected on the backlog task.
  Re-verified LDR tip at re-dispatch: `instruments-service/scripts/expected_universe.py` +
  `check_enumeration_completeness.py` still have zero `start_date` / `get_venue_data_type_start_date` references (grep
  returns empty). Task `-007` remains `status=queued` (has NOT reached LDR — dispatched to a peer slot per prior entries
  but the work not committed). Main-agent verdict (`BLK-9072b84f` answered): PARK -008 — **4th ruling, same answer**.
  The 17,282-row over-seed risk stands; do NOT flip UAC `VENUE_DATA_TYPE_CAPABILITIES`. **Operator action required**:
  add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen to stop the
  bounce loop (4 dispatches, 4 blocks). Slot-5 goes idle pending operator's backlog fix; -008 resumes only when `-007`
  (enumerator `start_date`) reaches LDR.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (5th dispatch, `BLK-545a3adb`)** (slot-2
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-2 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` is STILL uncorrected on
  the backlog task (verified via `/api/backlog?limit=500`: `-008.depends_on = null`). Re-verified LDR tip at 5th
  re-dispatch: `instruments-service/scripts/expected_universe.py` last touched by `2fa3877` (2c) + `a1038ee` (2a) —
  neither commit adds `start_date` awareness; `check_enumeration_completeness.py` likewise contains zero `start_date` /
  `get_venue_data_type_start_date` refs. Task `-007` remains `status=queued` on the backlog (unchanged since 4th
  dispatch — no worker has landed it). Slot-2 verdict: PARK -008 — **5th consecutive block, same 17,282-row over-seed
  risk**. The bounce loop is now definitively an operator-backlog defect: 5 slots have been spent (8, 7, unnamed 3rd,
  5, 2) verifying + escalating the same fact. **Operator action required (5th escalation)**: add
  `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen; -008 stays in
  queue until `-007` (enumerator `start_date`) reaches LDR. Slot-2 goes idle pending operator's backlog fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (6th dispatch)** (slot-9 planning). Task
  `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-9 by priority=20 alone; `depends_on` gap flagged in
  `BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` + `BLK-545a3adb` remains uncorrected on the backlog task (verified
  via `/api/backlog?limit=500`: `-008.status=dispatched`, `-008.depends_on = null`; `-007.status=queued`,
  `-007.depends_on = null`). Re-verified LDR tip at 6th re-dispatch: `instruments-service/scripts/expected_universe.py`
  contains ZERO `start_date` / `get_venue_data_type_start_date` refs (grep empty; last touching commit `a1038ee` 2a);
  `check_enumeration_completeness.py` likewise contains ZERO such refs (last touching commits `2fa3877` 2c + `a1038ee`
  2a). Task `-007` (enumerator `start_date` support) remains `status=queued` on the backlog with no worker having landed
  the work. Slot-9 verdict: PARK -008 — **6th consecutive block, same 17,282-row over-seed risk**. The bounce loop
  persists: 6 slots have now been spent verifying + escalating the same operator-backlog defect
  (`depends_on: [cefi_layer1_denominator_gaps-007]` still not encoded on `-008`). **Operator action required (6th
  escalation)**: add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen;
  -008 stays in queue until `-007` (enumerator `start_date`) reaches LDR. Slot-9 goes idle pending operator's backlog
  fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (7th dispatch)** (slot-9 planning, new
  session). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-9 AGAIN after the prior slot-9 session's
  6th-block park commit `7ad9a3c6b` (18:09 UTC) landed on LDR; task status returned to queued/dispatched.
  Machine-encoded `depends_on` gap flagged across 6 prior blocks (`BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` +
  `BLK-545a3adb` + 6th-block) remains uncorrected: `/api/backlog?limit=500` at 7th re-dispatch:
  `-008.status=dispatched, depends_on=null`; `-007.status=queued, depends_on=null`. Re-verified LDR tip:
  `instruments-service/scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` still contain ZERO
  `start_date` / `get_venue_data_type_start_date` refs (last touching commits `a1038ee` 2a + `2fa3877` 2c — neither adds
  start_date). Confirmed ASTER capability entry alive at
  `unified-api-contracts/registry/ market_data_categories.py:1144` (target of the flip). Slot-9 verdict: PARK -008 —
  **7th consecutive block, same 17,282-row over-seed risk**. The bounce loop is not self-correcting: 7 slots (8, 7,
  unnamed 3rd, 5, 2, 9, 9-again) have now been spent verifying + escalating the identical operator-backlog defect.
  **Operator action required (7th escalation)**: add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in
  `data/config/backlog.yaml` and regen; -008 stays in queue until `-007` (enumerator `start_date`) reaches LDR. Slot-9
  goes idle pending operator's backlog fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (8th dispatch, `BLK-e642f2aa`)** (slot-4
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-4 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged across 7 prior blocks (`BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` +
  `BLK-545a3adb` + 6th + 7th) is STILL uncorrected. Re-verified at 8th re-dispatch via `/api/backlog?limit=500`:
  `-008.status=dispatched, depends_on=null`; `-007.status=queued, depends_on=null`. Re-verified LDR tip with
  `rg -c 'start_date|get_venue_data_type_start_date'` on both files: ZERO matches on
  `instruments-service/scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` (last touching
  commits unchanged: `a1038ee` 2a + `2fa3877` 2c). Confirmed ASTER capability entry alive at
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144` (flip target). Slot-4 verdict:
  PARK -008 — **8th consecutive block, same 17,282-row over-seed risk**. The bounce loop remains not self-correcting: 8
  slots (8, 7, unnamed 3rd, 5, 2, 9, 9-again, 4) have now been spent verifying + escalating the identical
  operator-backlog defect — this is now a systemic-cost finding (each dispatch consumes ~10 min of a worker's context
  budget + a Claude-Code cycle). **Operator action required (8th escalation)**: add
  `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen; alternatively flip
  `-008`'s backlog priority to 999 so higher-priority queued tasks dispatch instead. -008 stays in queue until `-007`
  (enumerator `start_date`) reaches LDR. Slot-4 goes idle pending operator's backlog fix.
- **2026-07-06** — **C2 point-fix (-009) flipped ✅** (slot-9 planning). Main released -008 via /skip-current-task
  answering `BLK-be92ef1e` Option A; -009 dispatched to slot-9 next. Verified code already landed on LDR by slot-11:
  `instruments-service@2170d9a3` (18:23:15 UTC, "feat(scripts): bundle-aware MVP data_type gate in \_row_data_types cefi
  branch — closes cefi_layer1_denominator_gaps C2 point-fix (item 009)") — 31 lines in
  `scripts/enumerate_expected_universe.py` (the MVP data_type gate at lines 873-899) + 117 lines of regression tests (4
  tests) in `tests/unit/scripts/test_enumerate_expected_universe.py`; QG-green 181s per commit message. The correct
  instrument-type/bundle-aware approach the CAUTION prescribed is implemented via `_mvp_capture_itype` normalisation +
  `cefi_rule.instrument_type_data_types` membership check. Deribit `options_chain` slice preserved via the
  OPTION-override skip; COINBASE-SPOT `book_snapshot_5` dropped; Deribit PERP `liquidations` dropped; non-MVP-scoped
  venues (e.g. BINANCE-DELIVERY) unaffected by the empty-mvp_dts guard. Slot-9 action: checkbox-flip only (no code
  change) — /done cites `2170d9a3` as the shipped SHA.
- **2026-07-06** — **Re-measure task (-005) PARKED — BLOCKED-PREREQUISITES (`BLK-ad7abfcd`)** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-005` ("Re-measure + re-certify the cefi Layer-1 row") was dispatched to slot-8 by
  priority=50 alone; the machine-encoded `depends_on` gap flagged across 8 prior `-008` blocks now also affects `-005`
  (verified via `/api/backlog?limit=500`: `-005.status=dispatched, depends_on=null`). Verified plan-declared PREREQ
  chain ("2a–2f landed + ASTER live wire (Plan 5) + KALSHI-PERP purge (Stage-3)") is NOT met: (i) `-002` (2b cefi
  gate-authority fix on `build_expected`) status=queued — D2a `INSTRUMENT_TYPES_BY_VENUE` authority IS baked into
  `scripts/expected_universe.py` (part of 2a's consolidation) but the 2b sub-parts (ASTER live-forward split +
  BYBIT-SPOT relabel) remain unshipped; (ii) `-004` (2f LIGHTER/EXTENDED/PACIFICA denominator-gap) status=queued —
  depends on enumerator `start_date`; (iii) `-007` (enumerator `start_date` support) status=queued — verified LDR tip:
  `instruments-service/scripts/expected_universe.py` has ZERO `start_date` / `get_venue_data_type_start_date` refs (grep
  empty; last touching commits `a1038ee` 2a + `2fa3877` 2c — neither adds start_date); (iv) ASTER live wire (Plan 5,
  INFRA role) — connector `market_tick_data_service/live/connectors/aster_book_liq_ws.py` EXISTS but is NOT registered
  in `market_tick_data_service/live/connector_registry.py` (grep empty on `aster_book_liq_ws|AsterBookLiq`); (v)
  KALSHI-PERP purge (Stage-3) — commit `c8c6dac` only guards the KALSHI-PERP/POLYMARKET-PERP adapters to emit 0 (a
  forward stop-gap); the 25,473 fake `KALSHI-PERP` cefi Layer-2 rows still pollute the manifest and would over-inflate
  the numerator. Running the re-measure now would produce a misleading % moving in the WRONG direction from the plan
  Gate ("denominator GREW, % dropped honest") — the denominator would still UNDER-count (2f venues at 0-expected while
  their manifest rows exist) while the numerator OVER-counts (fake KALSHI-PERP rows). Slot-8 verdict: PARK -005 —
  recommendation A of `BLK-ad7abfcd`. **Operator action required**: add
  `depends_on: [cefi_layer1_denominator_gaps-002, cefi_layer1_denominator_gaps-004, cefi_layer1_denominator_gaps-007]`
  to `-005` in `data/config/backlog.yaml` + regen (or flip `-005` priority to 999) to prevent the same bounce-loop the
  `-008` block-chain hit 8×. -005 stays in queue until 2b/2f/-007/ASTER-wire/KALSHI-PERP-purge all reach LDR. Slot-8
  goes idle pending operator answer + backlog fix.
- **2026-07-06** — **v1 deletion task (-010) PARKED — BLOCKED-OPERATOR-DECISION (`BLK-6cf82522`)** (slot-4 planning).
  Task `cefi_layer1_denominator_gaps-010` ("Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it") was
  dispatched to slot-4 by priority=50. **Confirmation FAILED**: v1 is NOT purely legacy — it still owns 3 seed
  categories that v2 explicitly defers to it, so a blind delete is a data-correctness regression (violates the
  data-pipeline-correctness HARD rule). Verified on LDR tip
  (`instruments-service/scripts/enumerate_expected_universe.py`): (i) **sports v2** (`_enumerate_v2_sports`, line
  1552-1554): docstring explicitly says _"date < the data_type's source coverage start → SKIP — those dates are owned by
  the v1 `_enumerate_sports` pre-coverage rows (`EXPECTED_PRE_SOURCE_COVERAGE_START`, league_id="" grain). v2 must NOT
  re-emit them or the (data_type, date) cell is double-counted at two grains."_ — deleting v1 loses
  `EXPECTED_PRE_SOURCE_COVERAGE_START` seeds entirely. (ii) **tradfi v2** (`_enumerate_v2_tradfi`, line 1377-1379):
  docstring says _"Weekend and holiday dates fall through to the pipeline (v1 handles them at venue-grain; v2 only adds
  per-instrument rows for the non-trading-day windows outside the instrument lifecycle)."_ — MTDS orchestrator
  `process_ticks` DOES emit `EXPECTED_WEEKEND/HOLIDAY` during actual capture (verified
  `market-tick-data-service/tests/unit/test_orchestrator_non_trading_session.py`), but ONLY for dates the pipeline
  attempts; v1 `_enumerate_tradfi` pre-seeds them for the full calendar window (backfill role). Also v1
  `_enumerate_tradfi_indices` seeds Yahoo-index pre-genesis dates (VIX 1990-01-02 / DXY 2019-01-02 / treasuries
  2000-01-03) at instrument grain — v2 tradfi may cover this via catalogue but not verified. (iii) **defi v1** has
  `_enumerate_defi_gas_fees` (line 484-513) that seeds chain-level `EXPECTED_PRE_GENESIS_CHAIN` cells at `venue=ALCHEMY`
  for `gas_fees` data_type. v2 defi does per-instrument lifecycle but does not cover this chain-level slice
  (`venue=ALCHEMY` is not in the per-instrument catalogue). Cefi + prediction ARE fully covered by v2 (verified by
  `tests/integration/test_enumerate_v2_superset_property.py` which asserts v2 ⊇ v1 for cefi/defi/prediction pre-launch
  cells; docstring at line 43+47 calls v2 "the live path" for cefi + prediction only, NOT
  tradfi/sports/defi-chain-level). Production context: `expected_universe_v2_scheduler.tf` runs v2 only, on ALL 5 AGs
  daily @ 01:30 UTC (v2 wired 2026-06-19). v1 launcher (`launch-expected-universe-enumerator-vm.sh`) exists but is
  MANUAL, not scheduled — so the sports pre-cov / defi gas_fees pre-genesis / tradfi Yahoo-index cells are already NOT
  being freshly seeded via any scheduled path; they exist in the manifest only from historic v1 manual runs. Slot-4
  verdict: PARK -010 — recommendation A of `BLK-6cf82522`: DEFER pending a preceding task that either (i) extends v2 to
  cover the 3 asymmetric slices, or (ii) folds them into `build_expected` / `scripts/expected_universe.py`; then delete
  v1 cleanly. **Operator action required**: file a new task (or resize this one) to enhance v2 sports (emit
  `EXPECTED_PRE_SOURCE_COVERAGE_START` while preserving the two-grain double-count guard), v2 tradfi (emit
  weekend/holiday pre-seeds venue-grain + Yahoo-index pre-genesis instrument-grain), and v2 defi (emit chain-level
  `gas_fees` `EXPECTED_PRE_GENESIS_CHAIN` at `venue=ALCHEMY`) BEFORE -010's delete lands; alternatively answer with
  Option C/D from `BLK-6cf82522` if the operator accepts the correctness trade-off or wants both in one commit. Slot-4
  goes idle pending operator answer.
- **2026-07-06** — **\_read_manifest hardening (-011) SHIPPED ✅** (slot-5 planning). Task
  `cefi_layer1_denominator_gaps-011` ("Harden `_read_manifest` primary selection against surgery-bumped mtimes") shipped
  via `instruments-service@5b04878`. Chose the pinned-primary approach (tuple-order first-accessible = `-prd` by
  construction) over content-based freshness (max manifest date): simpler, deterministic, and matches the plan's own
  wording ("pinning prd as primary"). mtime-based `_sort_key` removed from `_read_manifest`; replaced with
  `_select_primary_index(accessible, override, asset_group)`. New CLI flag `--primary-bucket=<name>` overrides the pin
  for surgery/debugging (falls back to pin + warning if the named bucket isn't accessible). New
  `_warn_if_secondary_newer` helper logs `SURGERY-SIGNAL` when a secondary's mtime > primary's — surfaces the
  ASTER-corrective-pass scenario without silently flipping roles. Regression test
  `test_pinned_primary_wins_when_secondary_mtime_is_newer` locks the fix: legacy bucket with newer mtime + prd with
  older mtime → prd still primary. Full test suite 24/24 green; QG-green 94s (sentinel `9263c803`). Docstring + usage
  examples updated; no other callers of `_read_manifest` in the codebase (grep confirmed).
- **2026-07-06** — **Task -010 STALE RE-DISPATCH — no-op /done** (slot-9 planning). Task
  `cefi_layer1_denominator_gaps-010` ("Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it") was
  re-dispatched to slot-9 by priority=50 alone. Plan line 248 already carries the `[x] ✅ DEFERRED` flip from slot-10
  (commit `a16ac0649` — "docs(plans): defer v1 enumerator delete + file follow-on issue doc", verified on LDR via
  `git merge-base --is-ancestor a16ac0649 origin/live-defi-rollout` = YES). Follow-on issue doc exists at
  `plans/active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md` (5 follow-on todos: v2
  tradfi/sports/pre-launch coverage extension, deployment-service infra cleanup, and the final v1 delete after those
  land). No code change was needed by original design (v1 NOT safe to delete per main-agent ruling on `BLK-0ac84889`)
  and none is needed on this re-dispatch — the plan artifact + issue doc are the tracked-work outputs. Slot-9
  verification result: task -010 is fully complete on LDR; the backlog task remained `status=dispatched` because the
  PlanRegenLoop had not yet re-parsed the flipped checkbox at the time of this /boot. Slot-9 /done cites `a16ac0649` as
  the shipped SHA (existing artifact). Cross-reference: slot-4's BLK-6cf82522 entry above independently re-verified the
  same three v2-does-not-cover slices documented in `v1_enumerator_dispatch_not_deletable_2026_07_06.md`.
- **2026-07-07** — **2b flipped ✅ — checkpoint-only, no code change** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-002` ("2b. cefi gate-authority fix on `build_expected`") was dispatched to slot-8 as the
  highest-tier queued task (tier=1, priority=10, `depends_on=null`). Ambiguity in the task text — "Apply D2a/D2b onto
  the single producer, then — in order — the ASTER live-forward split ... the BYBIT-SPOT relabel, and the C2
  MVP-data-type intersection" — could be read as (i) 2b consists of a D2a/D2b checkpoint plus separately-tracked
  followers, or (ii) 2b bundles all four items. Slot-8 filed `BLK-ec6dba83` asking main-agent to disambiguate. Main
  answered Option A: "CLOSE cefi_layer1_denominator_gaps-002 as DONE. D2a+D2b are confirmed applied via 2a
  byte-identical fold + commit 03cfd0f — the core gate-authority fix on build_expected is complete. The remaining
  sub-parts are correctly tracked in their own dedicated backlog entries: ASTER live-forward split in -007 (has its own
  HARD prereq gate), BYBIT-SPOT relabel in -006 (MTDS writer defect tracked separately), C2 MVP intersection in -009
  (already shipped). Do NOT hold -002 open waiting for those — they are individually gated and dispatched." Verified on
  LDR at flip time: (i) `scripts/expected_universe.py::_get_cefi_venue_itypes` sources `INSTRUMENT_TYPES_BY_VENUE`
  restricted to `VENUES_BY_ASSET_GROUP["cefi"]` with `FUTURE_BUNDLE_VENUES` bundle roll-up — the D2a declarative
  authority (last touched: `681f50a` 2a byte-identical fold, preceded by `03cfd0f` D2a landing). (ii)
  `_expected_generic` applies `VENUE_DATA_TYPE_CAPABILITIES` as Carve-out 1 for
  `VENUE_CAPABILITY_AGS = {"cefi", "tradfi"}` — the D2b intersection. (iii) Venue-level cefi MVP override via
  `get_mvp_data_types_for_cefi_venue(venue)` applied as Carve-out 2 (the `build_expected` analogue of the -009 C2 fix on
  `_row_data_types`). Dynamic Gate verification:
  `.venv/bin/python -m pytest tests/unit/scripts/test_expected_universe_golden.py -x -q` → 14/14 pass in 1.47s.
  `build_expected("cefi")` returns 72 tuples over 18 of 24 declared cefi venues (ASTER, BINANCE-FUTURES/SPOT,
  BITFINEX-FUTURES/SPOT, BITGET-FUTURES/SPOT, BYBIT, COINBASE-FUTURES, DERIBIT, EXTENDED-STARKNET, HYPERLIQUID,
  KRAKEN-FUTURES/SPOT, LIGHTER-ZKSYNC, OKX, PACIFICA-SOLANA, UPBIT); the 6 absent venues each carry an explicit
  configuration reason — BINANCE-DELIVERY / DERIBIT-COMBO / KALSHI-PERP / POLYMARKET-PERP have BOTH
  `VENUE_DATA_TYPE_CAPABILITIES[v]={}` AND `get_mvp_data_types_for_cefi_venue(v)==frozenset()` (COIN-M / future_combo /
  prediction-perp not-MVP per operator decisions 06-27 #3 + Ikenna 07-03); bare COINBASE has caps={book5, trades} but
  MVP=empty (BLK-5cc7590e BLOCKED-OPERATOR-DECISION already surfaced by 2a); BYBIT-SPOT has MVP populated but caps=empty
  (writer-defect tracked as -006, `target_slot=8 affinity=high`). No silent whole-venue omission remains — every absence
  is explicit, satisfying the plan Gate. Slot-8 action: checkbox-flip only (no `build_expected` code change; no golden
  edit; no instruments-service commit). /done cites `681f50a` as the shipped SHA for the 2b `build_expected` change. 2b
  flip UNBLOCKS the "2b landed" leg of PREREQ chains for -005 (re-measure — still blocked on -004+-007+ASTER wire
  - KALSHI-PERP purge) and -004 (2f — still blocked on -007).
- **2026-07-07** — **Task -004 (2f) RE-PARKED — BLOCKED-PREREQUISITES (`BLK-7b511dcb`)** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-004` ("2f. Reapply the denominator-gap model to LIGHTER / EXTENDED / PACIFICA") was
  RE-dispatched to slot-8 by priority=20 immediately after the 2b flip cited above; the machine-encoded `depends_on` gap
  flagged in the 2026-07-06 slot-8 park entry (add
  `depends_on: [cefi_layer1_denominator_gaps-002, cefi_layer1_denominator_gaps-007]` to `-004` in `backlog.yaml`) is
  still uncorrected (verified via `/api/backlog?limit=500`: `-004.status=dispatched, depends_on=null`). Re-verified LDR
  tip at RE-dispatch: (i) `scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` still contain
  ZERO per-`(venue, dt)` `start_date` / `get_venue_data_type_start_date` refs (the CLI-level global `start_date` at
  `enumerate_expected_universe.py:2991` is the only `start_date` string in the enumerator scripts — that's the batch
  window, not the per-(venue,dt) gate the plan requires). The only in-tree consumer of `get_venue_data_type_start_date`
  on LDR remains `scripts/cefi_per_venue_capture_summary.py`. (ii) UAC `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` still
  holds `{trades: 2023-07-22, derivative_ticker: 2023-07-22, perp_funding: 2023-07-22}` — NO `book_snapshot_5`, NO
  `liquidations`. (iii) Task `-007` (enumerator `start_date` support) remains `status=dispatched to slot-5` on the
  backlog — main-agent confirmed "slot5 has impl complete (126/126 tests green) but has NOT shipped via quickmerge".
  Main-agent verdict (`BLK-7b511dcb` answered): "PARK — BLOCKED-PREREQUISITES. Same ruling as 2026-07-06. ... Take PARK
  - /skip-current-task. Do NOT attempt workarounds." Operator actions main-agent surfaced: (a) ensure slot-5 ships
    cefi-007 via quickmerge (impl done, tests green); (b) update UAC `ASTER` capabilities to include `book_snapshot_5` +
    `liquidations`. Once both land on LDR, cefi-004 can re-dispatch. Slot-8 action: file this Progress Log entry, commit
    via `docs(plans):` cross-repo PM flip, then call `/api/slots/8/skip-current-task` per main-agent instruction
    (avoiding the same bounce-loop the `-008` chain hit 8×).

- **2026-07-07** — **Task -006 (BYBIT-SPOT itype-stamp) CODE FIX SHIPPED ✅** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-006` ("Diagnose + fix the BYBIT-SPOT `PERPETUAL` itype stamp") was dispatched after the
  -004 park + /skip. Diagnosis on LDR: the PERPETUAL stamp on BYBIT-SPOT batch rows comes from **two** authorities that
  both silently omitted BYBIT-SPOT — (i) `TardisAdapter._classify_row_instrument_type` at `tardis_adapter.py:321`
  SPOT-venue set had `BINANCE-SPOT / OKX-SPOT / COINBASE-SPOT / UPBIT / BITFINEX-SPOT / BITGET-SPOT / KRAKEN-SPOT` but
  NOT `BYBIT-SPOT` → the venue's rows fell through to `return InstrumentType.PERPETUAL`; (ii)
  `symbol_rules._VENUE_INSTRUMENT_TYPE` had bare `"BYBIT": "perpetual"` with no `"BYBIT-SPOT"` entry (unlike the Tier-3
  sisters `BITFINEX-SPOT / BITGET-SPOT / KRAKEN-SPOT` which explicitly map → `spot`). Fixed both authorities +
  regression-tested via `test_tardis_canonical_output.py::test_classify_row_instrument_type_option_future_perp_spot`
  which now covers BYBIT-SPOT (BTCUSDT + SOLUSDT) → SPOT_PAIR AND bare BYBIT (BTCUSDT) → PERPETUAL to prevent the
  BYBIT-SPOT fix silently regressing BYBIT-FUTURES (bare BYBIT is the canonical MTDS venue for BYBIT perp/futures via
  Tardis `bybit` exchange). Shipped via `market-tick-data-service@c4df8ae0` after three QG cycles (peers landed
  BITGET-SPOT + COINBASE-FUTURES connectors between my QG runs; each landed via clean rebase; sentinel finally matched
  HEAD at `c4df8ae0`). **BIG FINDING surfaced during manifest audit — main-agent BLK-aff71ec9 verdict**: BYBIT-SPOT
  manifest holds 135,444 rows in three anomalous states — 81,659 with EMPTY `instrument_type` (not modeled by the -006
  plan) + 53,785 stamped PERPETUAL (the class this task describes) + ~54,000 rows under spot-nonsense data_types
  (derivative_ticker / futures_chain / options_chain / ohlcv_1m / perp_funding / liquidations — none valid for a spot
  venue; likely stray captures leaked from BYBIT-FUTURES or another venue). A simple PERPETUAL→SPOT_PAIR relabel of the
  53k subset would NOT close the plan's Gate ("manifest `by_venue_instrument_type` shows the split") because 82k EMPTY
  rows + 54k spot-nonsense-data_type rows would remain in states the plan does not model. Main-agent ruled: "-006
  forward-path fix (code) is the deliverable; mark DONE after the commit + issue doc are in; do not hold it open for the
  remediation. Operator notify: the stray derivative_ticker/futures_chain/options_chain/perp_funding/liquidations rows
  on a spot venue may indicate months of mis-routed capture — the issue doc should flag whether a re-capture (not just
  relabel) is needed for those rows." Follow-up issue doc filed at
  **`plans/active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md`** (`assigned_vm: planning`,
  `assigned_role: data_engineering`, `depends_on: [cefi_layer1_denominator_gaps-006]`) with 4 P1/P2 todos: (a) diagnose
  the 82k EMPTY rows (read-only); (b) diagnose the 54k spot-nonsense-data_type rows (read-only, cross-reference against
  BYBIT-FUTURES manifest to check for duplicates); (c) ship corrective-relabel script gated on (a)+(b); (d) populate
  `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` in UAC with `trades` + `book_snapshot_5`. Operator explicitly notified
  via the issue doc's NOTIFY-OPERATOR banner. Slot-8 /done cites `c4df8ae0` as the shipped SHA.

- **2026-07-07** — **Task -005 (re-measure) RE-PARKED — BLOCKED-PREREQUISITES (`BLK-ae458864`)** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-005` ("Re-measure + re-certify the cefi Layer-1 row") was RE-dispatched to slot-8
  immediately after the -006 /done above. Same shape as BLK-ad7abfcd's earlier 2026-07-06 ruling — the machine-encoded
  `depends_on` gap on `-005` is still uncorrected on the backlog task. Verified LDR state at RE-dispatch: (i) `-002`
  (2b) LANDED via my earlier flip today; (ii) `-006` (BYBIT-SPOT itype-stamp) CODE FIX LANDED via mtds@c4df8ae0
  immediately preceding this park, but the BYBIT-SPOT manifest-remediation follow-up
  (`bybit_spot_manifest_stray_captures_2026_07_07.md`) is un-actioned; (iii) `-004` (2f) PARKED by me earlier this
  session (BLK-7b511dcb) pending -007; (iv) `-007` (enumerator start_date support) — main-agent's answer: "slot5
  wsfeedconnector-014 quickmerge has been in CI for 15+ ticks — this is the same CI slot that holds cefi-007"; LDR
  re-verified: `scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` still contain ZERO
  per-`(venue, dt)` `start_date` / `get_venue_data_type_start_date` refs; (v) ASTER live wire (Plan 5, INFRA role) —
  connector `market_tick_data_service/live/connectors/aster_book_liq_ws.py` EXISTS but NOT registered in
  `live/connector_registry.py`; (vi) KALSHI-PERP purge (Stage-3) — commit `c8c6dac` is a forward stop-gap only, 25,473
  fake `KALSHI-PERP` cefi Layer-2 rows still pollute the manifest. Running the re-measure now would produce a misleading
  % — denominator UNDER-counts (2f venues at 0-expected AND -006 BYBIT-SPOT stray captures still in
  EMPTY/PERPETUAL/nonsense states) while numerator OVER-counts (fake KALSHI-PERP + BYBIT-SPOT stray rows). Main-agent
  verdict (`BLK-ae458864`): "PARK — same ruling as BLK-ad7abfcd (2026-07-06). ... The full denominator-gap remediation
  sequence requires -007 → -004 → -005 in that order. Take PARK + /skip-current-task. cefi-005 re-dispatches
  automatically; at that point verify cefi-007 is on LDR before proceeding." Operator surfaced by main-agent: "slot5
  wsfeedconnector-014 quickmerge has been in CI for 15+ ticks — this single stuck CI is blocking cefi-004, cefi-005, and
  infra-001 simultaneously." Slot-8 action: this Progress Log entry, commit via `docs(plans):` cross-repo PM flip, then
  `/api/slots/8/skip-current-task`.

- **2026-07-07** — **Task -005 (re-measure) RE-PARKED — BLOCKED-PREREQUISITES (3rd dispatch, `BLK-817416c3`)** (slot-11
  planning). Task `cefi_layer1_denominator_gaps-005` was RE-dispatched to slot-11 by priority=50 alone; the
  machine-encoded `depends_on` gap on the backlog task is still uncorrected (verified via `/api/backlog?limit=500`:
  `-005.status=dispatched, depends_on=null`). Re-verified LDR at RE-dispatch with grep-and-read: **MET** — (i) `-007`
  (enumerator `start_date` support) LANDED via `instruments-service@4a8cff7`
  (`scripts/enumerate_expected_universe.py:1073` calls `get_venue_data_type_start_date(instr.venue, dt)`,
  per-`(venue, dt)` gate baked into `_enumerate_v2_cefi`); (ii) KALSHI-PERP purge DONE (25,473 rows removed via
  `purge_kalshi_perp_events_contamination_2026_07_06.py --apply`, cefi catalogue 376,984→351,511 per
  `prediction_capture_incident_remediation_2026_07_06.md` line 190); (iii) ASTER connector wired
  (`market-tick-data-service/market_tick_data_service/live/connectors/__init__.py:52` imports `aster_book_liq_ws`).
  **UNMET** — (iv) **UAC ASTER capability flip (-008) — plan/backlog DRIFT**: backlog task `-008` reports
  `status=done, depends_on=null` but plan line 240 `- [ ] [CONFIG] P1. **UAC capability flip** — add book_snapshot_5
  - liquidations to
    VENUE_DATA_TYPE_CAPABILITIES["ASTER"]`is UNCHECKED, and code verification confirms UAC file`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144`still holds only`{trades:
    2023-07-22, derivative_ticker: 2023-07-22, perp_funding:
    2023-07-22}`— NO`book_snapshot_5`, NO `liquidations`. Recent UAC commits on `market_data_categories.py`(top 10:`e76d874a`D2a`03cfd0f` …) do NOT include the ASTER capability flip. **Main-agent verdict (`BLK-817416c3`)**: "the code is authoritative. -008 is NOT actually done." **UNMET** — (v) `-004`(2f LIGHTER/EXTENDED/PACIFICA): plan line 166`-
    [
    ]`unchecked, backlog`status=queued`, `LIGHTER`/`EXTENDED`/`PACIFICA`produce zero grep matches in`instruments-service/scripts/expected_universe.py`(the denominator-gap model has NOT been reapplied to those 3 venues on`build_expected`). Running the re-measure now would produce a misleading % in the WRONG direction from the plan Gate ("denominator GREW, % dropped honest"): denominator UNDER-counts (ASTER `book_snapshot_5`/`liquidations`still 0-expected until UAC flip; LIGHTER/EXTENDED/PACIFICA still 0-expected until 2f). Main-agent verdict`BLK-817416c3`: PARK — "cefi-005 gates on both -004 and -008. Neither is complete. Proceeding without them would produce incorrect enumeration for the LIGHTER/EXTENDED/PACIFICA venues and missing ASTER book5/liquidations capability, which causes silent data-correctness failures downstream." **Operator actions surfaced** (3rd escalation on the same task): (1) fix -008 backlog drift — re-open -008, add `book_snapshot_5`+`liquidations`to UAC`market_data_categories.py:1144`, mark done only after code is on LDR; (2) wait for `-004`(LIGHTER/EXTENDED/PACIFICA) to complete + flip its plan checkbox; (3) re-dispatch`-005`only after both are confirmed on LDR. Slot-11 action: this Progress Log entry, commit via`docs(plans):`cross-repo PM flip, then`/api/slots/11/skip-current-task`per main-agent instruction. This is now the 3rd`-005`PARK on identical grounds (BLK-ad7abfcd 2026-07-06 slot-8, BLK-ae458864 2026-07-07 slot-8, BLK-817416c3 2026-07-07 slot-11) — the bounce-loop pattern the`-008`chain hit 8× is beginning to repeat on`-005`; suggest same operator-backlog fix (`depends_on:
    [cefi_layer1_denominator_gaps-004, cefi_layer1_denominator_gaps-008]`on`-005` + regen).

- **2026-07-07** — **UAC capability flip -008 SHIPPED ✅ — the 8-time bounced task finally lands** (slot-2 planning).
  Prereq -007 (per-(venue,dt) start_date gate) confirmed on LDR at `instruments-service@4a8cff7` — the exact
  correctness-safety mechanism that all 8 prior slots were correctly parking on. Verified UAC file
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144` matched the slot-11 BLK-817416c3
  "code is authoritative — -008 is NOT actually done" verdict: only `{trades, derivative_ticker, perp_funding}` present.
  Added `book_snapshot_5: "2026-06-23"` + `liquidations: "2026-06-23"` — start_date follows the KALSHI-PERP live-only
  precedent (KALSHI book_snapshot_5 = 2026-06-22 = the `_CONNECTOR_TO_VENUE` re-add / VM-launch date, per
  `test_data_status_registries.py` line comment "re-added 2026-06-23"). Chose 2026-06-23 = the `mtds@d43fd62` commit
  date for `market_tick_data_service/live/connectors/aster_book_liq_ws.py` ("fix(cefi-bug4): catalogue-driven HL/ASTER
  universe + ASTER live-only book/liq + drop HL liq") — the ASTER-side analog of the KALSHI code-land date. Also flipped
  `test_aster_book_snapshot_5_is_empty` → `test_aster_book_snapshot_5_and_liquidations_seeded` (the assertions had to
  move: book_snapshot_5 now seeds non-empty via the perp MVP seed; liquidations stays empty because it's venue-level per
  `test_venue_level_dt_returns_empty` — that's Tier-2 fallback, not a capability gap). Dropped the now-stale ASTER
  example from the "capability not declared" comment inside `get_expected_instruments_for_venue`. Encountered 20
  pre-existing WS-cassette `_CONNECTOR_TO_VENUE`-map failures on the initial QG (unrelated to ASTER — connectors added
  without their test-registry entry, blocking sentinel refresh fleet-wide); peer landed `unified-api-contracts@e17b185f`
  ("fix(tests): add 20 \_CONNECTOR_TO_VENUE map entries + 17 stub \*\_ws.yaml cassettes ...") during my investigation,
  tree went RED→GREEN, my commit auto-rebased to `3652f99f`, sentinel written on the re-run, quickmerge shipped. Filed
  nothing new — peer commit's message calls out "unblocks fleet-wide UAC ships" so the finding is already owned.
  UNBLOCKS -004 (2f LIGHTER/EXTENDED/PACIFICA — each still needs its own capability entry + start_date, they were never
  seeded because their capability entry was empty before D2b; -007 gate handles the date discipline uniformly). UNBLOCKS
  -005 (re-measure — verify UAC flip on LDR before re-dispatch per slot-11 BLK-817416c3, then run; the slot-11 UAC-drift
  verdict is now false). No new BLK-QUEUE raised — this was the honest shipping path once -007 was on LDR + the
  WS-cassette gap was fixed by peer.

- **2026-07-07** — **Task -005 (re-measure) SHIPPED ✅** (slot-6 planning, 4th dispatch — the one that finally landed).
  Task `cefi_layer1_denominator_gaps-005` re-dispatched after prior 3 parks (BLK-ad7abfcd 2026-07-06 slot-8,
  BLK-ae458864 2026-07-07 slot-8, BLK-817416c3 2026-07-07 slot-11) — this time verified all prereqs are met and the
  main-agent authorized proceed via `BLK-057bf3b0` Option A. **Prereq re-verification on LDR:** (i) -002 (2b) DONE via
  earlier plan-checkbox flip; (ii) -007 (per-(venue,dt) start_date gate) LANDED (is@4a8cff7,
  `enumerate_expected_universe.py:1073` calls `get_venue_data_type_start_date(instr.venue, dt)`); (iii) -008 (UAC ASTER
  cap flip) LANDED at 2026-07-07 08:10 UTC via uac@3652f99f — the change slot-11 BLK-817416c3 flagged as MISSING did in
  fact land ~6 h before -005's 4th re-dispatch. UAC ASTER now:
  `{trades: 2023-07-22, derivative_ticker: 2023-07-22, perp_funding: 2023-07-22, book_snapshot_5: 2026-06-23, liquidations: 2026-06-23}`.
  Plan line 240 flipped `[x]` DONE on the same landing commit; (iv) -006 (BYBIT-SPOT itype-stamp) LANDED
  (mtds@c4df8ae0); (v) KALSHI-PERP purge DONE (25,473 rows removed 2026-07-06); (vi) ASTER live wire (Plan 5) —
  connector `aster_book_liq_ws` imported at
  `market-tick-data-service/market_tick_data_service/live/connectors/__init__.py:52`; (vii) -004 (2f
  LIGHTER/EXTENDED/PACIFICA) plan line 166 still `[ ]` unchecked BUT verified code-level gate met by directly invoking
  `build_expected('cefi')` — LIGHTER-ZKSYNC/EXTENDED-STARKNET/PACIFICA-SOLANA each emit exactly 3 tuples
  (`trades`/`book_snapshot_5`/`derivative_ticker`) matching the ASTER live-forward profile the 2f section prescribes.
  Main-agent verdict: 2f plan checkbox unflip is docs-drift for slot-8 to fold when it executes -004 (backlog
  `queued, target_slot=8, affinity=high`); it is NOT a runtime blocker. **Fresh re-measure**
  (`.venv/bin/python scripts/measure_honest_coverage.py --asset-group cefi --output-path /tmp/cefi-remeasure/coverage.json`,
  2026-07-07 08:54:47 UTC): **cefi Layer-1 = 72.60%** (present 53 / expected 73); `denominator_status=INCOMPLETE`; 20
  missing, 87 stray. Layer-2 reachable coverage 76.77% (2,098,056 / 2,732,783). **Denominator trajectory**: 44 tuples @
  65.91% (2026-06-29 certified — the pre-D2a baseline that gate-blindly omitted whole venues) → 72 tuples @ 73.61%
  (post-D2a fold + 2b — the declarative INSTRUMENT_TYPES_BY_VENUE authority + capabilities completion) → **73 tuples @
  72.60% (this measure — post-uac@3652f99f -008 ASTER book_snapshot_5 live-wire capability flip)**. Denominator GREW +1
  (`ASTER perpetual book_snapshot_5`, in the missing set because the ASTER live-wire connector's captures haven't
  propagated to the manifest yet); % dropped 0.99 pp honestly. **Missing tuples (20)** — same known holes as prior
  measure PLUS the newly-added ASTER book5: ASTER perp book5 (NEW — pending live-wire); BITFINEX-FUTURES future ×3
  (book5/derivative_ticker/trades); BITGET-FUTURES future ×3; BYBIT spot_pair ×2 (book5/trades — the -006 forward-path
  fix landed but corrective-relabel is still in the follow-up issue doc
  `bybit_spot_manifest_stray_captures_2026_07_07.md`); COINBASE-FUTURES future trades; EXTENDED-STARKNET perp ×2
  (book5/trades); KRAKEN-FUTURES future derivative_ticker; LIGHTER-ZKSYNC perp ×3; OKX options_chain trades;
  PACIFICA-SOLANA perp ×3. **Stray tuples (87)** — writer emits data_types UAC doesn't sanction (writer-itype-case
  tuples like `ASTER PERPETUAL futures_chain`, `DERIBIT COMBO options_chain`, `BYBIT-SPOT PERPETUAL book_snapshot_5`,
  etc.); tracked cross-plan in the honest coverage v2 stray_tuples surface. **Adjacent finding fixed inline** — the
  2026-07-07 UAC change (uac@3652f99f) also silently broke 3 instruments-service tests written to guard the pre-008
  carve-out state
  (`test_check_enumeration_completeness.py::TestAsterCarveOut::test_aster_book_snapshot_5_not_in_expected` +
  `test_aster_book_snapshot_5_absent_from_manifest_is_not_a_hole` +
  `test_enumerate_expected_universe.py::test_row_data_types_aster_capability_carveout`); IS
  `.qg_last_passed_sha = 4a8cff75` pre-dates uac@3652f99f, so IS QG has been silently red on LDR HEAD since 2026-07-07
  08:10 UTC. Renamed `TestAsterCarveOut → TestAsterCapabilities` and inverted the assertions (ASTER book_snapshot_5 IS
  now in EXPECTED and IS a Layer-1 hole when absent — the live-wire capability guard); ASTER liquidations still
  not-expected (not in MVP scope, unchanged). Renamed
  `test_row_data_types_aster_capability_carveout → ..._aster_capability_profile` with the updated cap ∩ MVP assertions.
  All 91 tests in the affected suites pass; QG green. **Golden regen**:
  `tests/unit/scripts/goldens/expected_universe/cefi.json` 72 → 73 tuples (added
  `["ASTER", "perpetual", "book_snapshot_5"]`, `captured_at 2026-07-06 → 2026-07-07`); all 14 golden tests pass.
  **Shipped via quickmerge**: is@<f722845>
  `feat(scripts): re-measure cefi Layer-1 post-008 (72.60% on 73 tuples) + regen golden + rename obsolete ASTER carve-out tests`.
  Plan checkbox flipped in the same agent turn. UNBLOCKS Plan 4 Stage-3 global certify. **Follow-up notes**: (1) the
  ASTER book5 hole will close when live-wire captures start hitting the manifest — no code change needed; (2) BYBIT-SPOT
  stray captures (135k rows in EMPTY/PERPETUAL/spot-nonsense states) tracked in
  `bybit_spot_manifest_stray_captures_2026_07_07.md` — not gating -005; (3) LIGHTER/EXTENDED/PACIFICA perp tuples still
  missing (0 captured — new venues, first captures pending).

- **2026-07-08** — **Task -004 (2f) FLIPPED ✅ — checkpoint-only, no code change** (slot-8 planning). Both PREREQs
  confirmed on LDR: `-002` (2b) flipped 2026-07-07; `-007` (enumerator `start_date` support) landed
  `instruments-service@4a8cff7`, verified generic (no ASTER-specific code path — `get_venue_data_type_start_date` called
  per-`(venue, dt)` for ANY venue at `enumerate_expected_universe.py:1132-1135`). LIGHTER-ZKSYNC / EXTENDED-STARKNET /
  PACIFICA-SOLANA capability declarations (trades/book_snapshot_5/derivative_ticker + start_dates) already landed via
  D2b (`unified-api-contracts@e76d874a`, 2026-07-06). Dynamic verification: `build_expected('cefi')` invoked directly —
  each of the 3 venues returns exactly
  `{(v, 'perpetual', 'book_snapshot_5'), (v, 'perpetual', 'derivative_ticker'), (v, 'perpetual', 'trades')}`, matching
  the ASTER live-forward profile. No code change needed; Gate satisfied by data already on LDR. Slot-8 action:
  checkbox-flip only. **Adjacent finding surfaced while dynamically verifying the Gate (pre-existing on LDR HEAD, not
  caused by this task)**: `instruments-service` QG is RED (verified via `bash scripts/quality-gates.sh --no-fix`: 2
  failed, 4056 passed) — root-caused + filed in full at
  `plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` (a peer, slot-7, had already opened
  that doc minutes earlier from an unrelated task; I updated it with the correct root cause — `uac@23fa3a99` orphaning
  `OKX-SPOT`'s EXPECTED tuples, not the enumerator regression the doc originally suspected — rather than fork a
  duplicate). Also added a pointer-only BLOCKED-OPERATOR-DECISION todo above so this plan's own denominator-drift
  history stays discoverable in one place. A golden-fixture fix was drafted + verified clean locally, then **reverted
  (`git checkout --`, not shipped)** — it can't land through a QG gate that's red for unrelated pre-existing reasons,
  and shipping it alone would misleadingly suggest the underlying OKX-SPOT hole is "handled". No `instruments-service`
  commit this turn.
- **2026-07-14 (data_engineering slot-7 planning)** — **DERIBIT-COMBO catalogue-is-live-only todo FLIPPED ✅** —
  `unified-api-contracts@89511de8` + `instruments-service@e6fdfd00`. Live-verified the premise
  (`api.tardis.dev/v1/exchanges/deribit` genuinely has 68,847 `type=='combo'` symbols back to 2022-08-23) before
  implementing. Flipped `VENUE_TO_ADAPTER_KEY["DERIBIT-COMBO"]` from `"deribit_combo"` to `"tardis"`;
  `factory.py::get_adapter_for_canonical_venue` now special-cases `mode="live"` DERIBIT-COMBO to keep the REST adapter
  (extracted to `_build_deribit_combo_live_adapter` to stay under the 200-line function cap — the addition would have
  pushed the shared function over); `mode="batch"` (default) routes through Tardis. Added a combo-type self-filter
  (`type=='combo'` only) in `TardisReferenceDataAdapter.get_instruments()` keyed on
  `canonical_venue_override=="DERIBIT-COMBO"` — without it the fix would have mistagged bare DERIBIT's whole
  option/future/perpetual/spot universe as DERIBIT-COMBO, since both venues share the same "deribit" Tardis exchange
  slug. Corrected two stale docs that had over-broadly concluded historical DERIBIT-COMBO data was unobtainable from ANY
  source (it was only ever a Deribit-REST-specific limitation): the adapter's own docstrings, and codex
  `honest-absence-downstream-handling.md` § "DERIBIT-COMBO historical unavailability" (SUPERSEDED-banner added, not
  deleted). Also cleaned up this todo's own text — a prior edit had glued an unrelated OKX-SPOT/QG-red pointer onto the
  end of the DERIBIT-COMBO finding by mistake; removed (that content is tracked independently, in full, at
  `instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`, unaffected). QG-green both repos
  (`.qg_last_passed_sha=89511de8c5bdb8fac79d5569e5c627fed44324a4` /
  `.qg_last_passed_sha=e6fdfd0061d0fa3d88afa40975530e48b1d13bb5`; 4409+ instruments-service tests, ~4-5k UAC tests).
  Code fix is code-complete + verified; the actual backfill-VM relaunch to close
  `(DERIBIT-COMBO, options_chain, trades)` as a G4 Layer-1 tuple is separate infra work tracked in
  `mvp_backfill_cefi_tick_v10_2026_06_27.md`, not this plan.
