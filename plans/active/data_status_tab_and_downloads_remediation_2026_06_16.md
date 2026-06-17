---
title: Data-status tab + instruments download remediation (deployment-api / deployment-ui / CeFi universe)
created: 2026-06-16
parent_epic: deployment_and_user_management_master
assigned_vm: vm-operator-ops
status: active
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-06-16
source:
  - plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md (root-caused findings A–H,
    file:line)
  - operator 2026-06-16 (data-status tab walkthrough; "blockers to mtds migration and downloads"; smoke-test downloads
    across all asset_groups + fix globally)
---

# Data-status tab + instruments download remediation

> Findings of record + every `file:line`:
> `plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md`. **Operator-flagged blockers**: (1)
> instruments CSV **downloads** (Phase E — LAST, gated on the migration), (2) instruments/MTDS **migration-to-100%**
> (owned by `instruments_manifest_canonicalisation_2026_06_01.md` — see § Cross-plan blockers, do NOT re-implement
> here). Backend = deployment-api (Python QG); frontend = deployment-ui (tsc/ESLint/Vitest/Playwright — `[UI]` +
> `pw:L2 ✓` + regression spec required before ticking). Each worker reads `SUB_AGENT_MANDATORY_RULES.md` cold-start.

> **🔴 EXECUTION SEQUENCING (operator 2026-06-16) — downloads LAST, after the v9 manifest migration.** This plan sits in
> the migration chain's **TIER 4**. Hard order: **TIER 0** pipeline_mode Phase-0 code foundation
> (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` — M1 full enum / M3 / M4 resolver /
> manifest-stamp fixes #1·#2·#3 / **GATE 0**) → **TIER 1** cleanup+correctness (catalogue lifecycle, provenance,
> honest-absence, instruments G1 universe/scope, TradFi naming, Deribit-spot — most can land now, independent of the
> migration) → **TIER 2** the real v9 `--apply` migrations per asset_group (gated on GATE 0) → **TIER 3** orphan-safety
> verification → **TIER 4 (this plan's DOWNLOAD work) LAST.** The **download path-drift fix (Phase D below) MUST target
> the FINAL canonical `pipeline_mode=…/venue=…` shape** — fixing it against the current v8 shape is wasted rework once
> the migration changes the path. The UI/scope/universe/naming items here are TIER-1 cleanup and may proceed
> independently; only the download path-fix is gated on the migration landing. Full landscape map:
> `plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md` § Sequencing.

> **🟢 UI test-env CORRECTION (2026-06-16) — it was NOT broken; a host Node-version mismatch.** My earlier "fleet-wide
> breakage" call was WRONG: deployment-ui's vitest suite is GREEN in CI (`quality-gates-v2` success, Node 22). The local
> `ERR_REQUIRE_ESM` was this host on **Node 20.18** — jsdom@29's ESM deps need **Node ≥22**. **FIXED**: pinned
> `.nvmrc`/`engines` Node>=22 + shipped the UI fixes under Node 22 (deployment-ui@`80c547d`; PREDICTION de-dupe
> exemption follow-up `f4adfd3f2`). **`pw:L2` RAN under Node 22: 211/213 smoke pass** — all data-status specs green, the
> venue/de-dupe/pagination changes verified. The remaining **2 failures are PRE-EXISTING in
> `prediction_v9_breakdown.spec.ts`** (confirmed identical on the pre-de-dupe baseline — NOT caused by this work; a
> separate prediction-smoke bug). They keep the full-suite exit non-zero, so the UI items below stay formally unticked
> until that spec is fixed. Enforcement: the shared UI gate (`base-ui.sh`) + `verify-slot-host-symmetry.sh` now require
> Node ≥22. Issue (RESOLVED): `deployment_ui_test_env_esm_breakage_2026_06_16.md`.

## Phase A (TIER 1 cleanup) — Scope + venue-filter correctness

- [x] ✅ [CODE] P1. **instruments-service "out of scope" — PROPER fix** — DONE deployment-api@`8710152`: new
      `services/data_status/reference_scope.py` reads the bundled `data-catalogue.instruments-service.yaml` genesis
      (`shard_status[ag][venue].start_date`) via `get_config_dir()`; `breakdowns_core._classify_data_type_for_venue`
      branches `_PER_VENUE_DAY_BUNDLE_SERVICES` onto it → in-scope ⟺ configured IS venue for the AG AND day ≥ genesis
      (covered-but-missing stays actionable; unlisted/pre-genesis → out_of_scope). NOT the all-in-scope hack. +4 tests;
      QG green. Grain = venue/day. **Nuance:** the catalogue carries only CEFI/TRADFI/DEFI genesis — SPORTS/PREDICTION
      IS venues read out_of_scope until added to `data-catalogue.instruments-service.yaml` (follow-on). — deployment-api
- [x] ✅ [CONFIG] P1. **SPORTS/PREDICTION genesis follow-on (the Nuance above) — DONE** — unified-trading-pm@`7752e58`
      added `shard_status.SPORTS` (9 venue keys: the dominant `""` blank-venue current-writer shape @2015-01-01 + legacy
      provider tokens API_FOOTBALL/API_FOOTBALL_FIXTURES/FOOTYSTATS/ODDS_API/MDPS_ODDS_HORIZON_BUCKET/OPEN_METEO/
      SOCCER_FOOTBALL_INFO/TRANSFERMARKT) + `shard_status.PREDICTION.POLYMARKET`@2025-03-14 to
      `configs/data-catalogue.instruments-service.yaml`. Venue keys + genesis transcribed from the ACTUAL
      `instruments-store-{sports,pred}` `_index/availability_index.parquet` (service_name=instruments-service rows,
      uppercased venue) — NOT guessed: the live writer stamps `venue=""` for sports (provider → data_type per
      `writers.py:115`), `venue=POLYMARKET` for prediction. The deployment-service + deployment-api copies are SYMLINKS
      to this one PM file (no separate quickmerge needed). Verified
      `reference_genesis(sports,"")`/`(prediction,     "POLYMARKET")` + every real venue now resolve non-None /
      `is_reference_venue_day_in_scope == True` (negative control stays out_of_scope). PM PR #382 (v2-gated auto-merge).
      No `kalshi` IS rows live yet → KALSHI added when it lands.
- [x] ✅ [DESIGN] P1. **instruments-service manifest carries `instrument_type` (per-type counts)** (audit §K) —
      **instruments-service@b475ae8** (CODE; the destructive `--apply` rides the gated IS v9 walk, not run standalone).
      Single-walk discipline RESPECTED: rode the EXISTING `scripts/migrate_instruments_store_v9.py` (added
      `instrument_type` to `_V9_TEXT_COLUMNS` + backfill from the venue suffix `-SPOT`→spot / `-FUTURES`→perpetual,
      mirroring UTL's recorded-column inference) — NO new whole-corpus walk. Going forward
      `writers.py::_derive_instrument_type` stamps the REAL single instrument_type per venue×date shard (blank when
      mixed/absent — never fabricated; the manifest row is venue-grain). Venues without a derivable suffix (e.g.
      DERIBIT) stay "" by design (documented in code) → unlocks per-instrument_type scope + per-type UI drilldown +
      §J Deribit-options signal once the gated v9 apply runs. Guards: `test_orchestrator_helpers.py` (3 writer tests) +
      `test_migrate_instruments_store_v9.py` (backfill + existing-value-preserved). — instruments-service.
- [x] ✅ [CODE] P1. **Venue filter — backend** — DONE deployment-api@3d9a0e032: added repeatable `venue: list[str]` to
      the `/manifest` route + `get_manifest_status` (threaded through
      `_get_manifest_status_sync`/`_dispatch_category_builds`/ `_build_manifest_category`), engaged it in the
      `any_row_filter` gate, added `_apply_venue_filter` (case-insensitive OR) before the venue breakdown, and gated the
      process-pool path off (it doesn't thread filters); +3 tests; QG green. — deployment-api
- [ ] [UI] P1. **Venue filter — frontend** — CODE-SHIPPED deployment-ui@`80c547d` (re-fetch `useEffect` on
      `selectedVenues`/folders/data-types change, post-first-load guarded; regression:
      `tests/unit/components/DataStatusTab.refetch_dedupe_pagination.test.tsx`; vitest+tsc+build green under Node 22).
      **NOT ticked ✅ — `pw:L2` smoke pending a browser-capable slot** (playwright HARD RULE). — deployment-ui `[UI]`

## Phase B (TIER 1 cleanup) — UI clarity (duplicate panels, pagination)

- [ ] [UI] P2. **Collapse duplicate "available" vs "available dates"** — CODE-SHIPPED deployment-ui@`80c547d` (legacy
      "Data Types" block gated so it no longer double-renders beside the honest panel; same regression spec; green under
      Node 22). **`pw:L2` pending** a browser-capable slot. — deployment-ui `[UI]`
- [ ] [UI] P2. **Pagination visible-count selector** — CODE-SHIPPED deployment-ui@`80c547d` (`DateList` size selector
      50/100/200/1000/2000/All; same regression spec; green under Node 22). Static server-truncation `+{N} more` labels
      (`:3891,3911,5386`, `VenuePillList :230`) still need a backend `limit` bump to be client-pageable — follow-on if
      wanted. **`pw:L2` pending.** — deployment-ui `[UI]`
- [ ] [UI] P3. **Rollup-difference clarity** (audit §F, by-design): optional small UI note/tooltip explaining IS is a
      per-venue/day reference bundle (no data_type axis) vs MTDS's 5-axis market-data shards — so the structurally
      different drilldown reads as intentional, not broken. — deployment-ui

## Phase F (TIER 1 cleanup) — Operator live-board data-status display bugs (2026-06-17)

> Operator 2026-06-17: three data-status display bugs on the live board. Diagnosed against the ACTUAL code + the live
> deployment-api (`:8004`) response. Scope = deployment-api + deployment-ui ONLY.

- [x] ✅ [UI] P1. **"Honest Coverage" vs "Data Coverage" headline % disagree wildly (CeFi 11.7% vs 98.5%)** — FIXED
      deployment-ui@`7007529`. **Root cause:** `/api/data-status/honest-coverage` returns a GCS `coverage.json` emitted
      VERBATIM by the instruments-service cron `measure_honest_coverage.py`, whose `coverage_pct` is **captured-only** —
      `captured / (captured + attempted_failed + expected_unattempted)` (EXCLUDES `empty_confirmed` from the numerator).
      For CeFi the 29.7M legitimately-empty cells dominate (no liquidations/book-snapshot that minute) → `coverage_pct`
      collapses to **11.68%** while TURBO "Data Coverage" shows ~98.5% (`attempt_coverage_pct`, where empty_confirmed
      counts as covered). The cron also does NOT emit `completion_pct_shards_weighted` / the split known/pending fields
      the card expected, so the card fell back to the mislabeled `coverage_pct` as the bold headline. **Fix
      (`HonestCoverageCard.tsx` + `client.ts`):** `deriveCoverage()` recomputes the headline = manifest-capture ratio
      (of attempted) = `(captured+empty+known_empty)/(that+attempted_failed)` from the raw counts the cron reliably
      emits — the SAME metric the "Data Coverage" widget shows, so the two headlines agree; secondary = captured-only
      ratio; the collapsed `expected_unattempted` is handled. The cron formula itself (instruments-service, migration
      agents) is left untouched. Regression: `tests/smoke/data_status_coverage_labels.spec.ts` (real cron payload shape;
      asserts headline ≠ 11.7%) + `HonestCoverageCard.test.tsx`. — repo deployment-ui@`7007529` | pw:L2 ✓ (215/215
      smoke) | regression: tests/smoke/data_status_coverage_labels.spec.ts — deployment-ui `[UI]`
- [x] ✅ [UI] P1. **Bar colours unreadable in HonestCoverageCard** — FIXED deployment-ui@`7007529`. The 6 segments used
      three near-indistinguishable greens (emerald-500 / teal-400 / sky-300) + two low-contrast greys. New `SEGMENT_COLORS`
      palette walks distinct hues (emerald → cyan → blue → amber → red → slate, all 500-stop, no <40%-opacity fills);
      legend swatches kept in lockstep + enlarged (w-2.5) with higher-contrast text. — repo deployment-ui@`7007529` |
      pw:L2 ✓ (215/215 smoke) | regression: tests/smoke/data_status_coverage_labels.spec.ts — deployment-ui `[UI]`
- [x] ✅ [DATA] P1. **Every CEFI venue read "out of scope" on the live board — STALE DEPLOY, not a code/data bug
      (RE-DIAGNOSED 2026-06-17 against the REAL prod manifest; the sub-agent's "token-mismatch → migration agents"
      verdict is REFUTED).** The earlier sub-agent could not reproduce (its local `:8004` had an empty CeFi manifest) so
      it speculated a token mismatch. Reproduced properly against
      `gs://market-data-tick-cefi-prd-…/_index/availability_index.parquet`: **every CeFi venue's tokens MATCH the scope
      and resolve in-scope.** For ALL 15 venues (ASTER/BINANCE-FUTURES/BINANCE-SPOT/BITFINEX-*/BITGET-*/BYBIT/
      COINBASE-SPOT/DERIBIT/HYPERLIQUID/OKX-*/UPBIT), `is_expected("cefi", venue, "trades")==True` and
      `is_expected(..., "book_snapshot_5")==True`; the `ohlcv_*` types are caught by `is_processed_data_type(...)==True`
      → `out_of_scope = not scope_in and not dt_is_processed == False`. So **NO CeFi venue resolves out_of_scope with the
      current code** (each has ≥1 in-scope data_type, so the UI's `every(dt.out_of_scope)` is never all-true). Therefore
      the screenshot showing all-out-of-scope was a **stale/cached render** (pre-`8710152` deploy or a cached SPA/API
      response). FIX = redeploy (the niE fix `8710152` is correct + on LDR; rebuilt + redeployed 2026-06-17, build
      `6655127f`) + a hard browser refresh — **no code or data change required**. Verified: the classifier is correct;
      this was a deploy/cache artifact. (Note: `derivative_ticker`/`futures_chain` on a few SPOT venues are
      legitimately out-of-scope at the data_type grain, but never make the VENUE out-of-scope since `trades` is in
      scope.)

## Phase C (TIER 1 cleanup) — CeFi universe extension (instruments completeness + EigenLayer dust)

- [x] ✅ [CONFIG] P1. **Extend `CEFI_BASE_ASSET_UNIVERSE`** (audit §G) — DONE unified-api-contracts@f4f7f8e (operator
      2026-06-16 "add the rest"): added `EIGEN` (EigenLayer rewards dust) +
      `AAVE, ALGO, AXS, CHZ, COMP, DASH, ENJ, EOS,     FIL, GALA, ICP, MANA, SAND, THETA, XLM, ZEC` to the frozenset
      (~28→~45); regression test `tests/test_cefi_universe_coverage.py`; QG green. All three adapters
      (tardis/hyperliquid/aster) import it. — unified-api-contracts
- [ ] [DATA] P1. **Re-enumerate + re-capture** the IS catalogue for the added bases so they appear in the universe +
      downloadable CSV (re-run the IS CLI per affected venue/date; the universe edit alone doesn't backfill past days).
      Cross-links the capture-freeze item below. — instruments-service
- [ ] [TEST] P2. UAC unit test asserting EIGEN + the added bases pass `_passes_asset_filter` for binance-spot (USDT) and
      hyperliquid; guards accidental universe shrink. — unified-api-contracts / instruments-service

## Cross-plan blockers — instruments/MTDS migration to 100% (do NOT re-implement here)

These are **operator-flagged blockers to MTDS migration**, owned by existing plans — a finding callout is being added to
the canon plan; track there, not as duplicate todos:

- v9 `--apply` is 🔴 GATED on `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` Phase-0; then E3–E6
  (drain/run/manifest-rebuild/verify) in `instruments_manifest_canonicalisation_2026_06_01.md:189-194`.
- ~40% cefi `_index` null-`capture_status`-with-count>0 rows + phantoms → honest relabel via the v9 walk (CF-10) +
  `reconcile_phantom_manifest_rows_all.py` (reconcile, recovers most of the missing %).
- Real capture-freeze ~2026-05-21 fleet-wide (defi 05-07; tradfi degraded 16K→2/day then stopped 05-22 — anomalous,
  needs root-cause) → un-freeze IS daily capture + backfill via the IS CLI
  (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md:194-212,418`).

## Phase D (TIER 1 cleanup) — TradFi canonical naming + Deribit spot fix (instruments-service / UAC)

- [x] ✅ [DESIGN] P1. **TradFi human-canonical naming — NO Databento dependency** — DONE instruments-service@`2caa3128`
      (operator 2026-06-16): adapter `_parse_row_to_record` now resolves the product root from `raw_symbol` via the
      static UAC exchange-code registry (`EXCHANGE_CODE_TO_NAME` ∪ `DatabentoInstrumentDef.exchange_code→base_asset`,
      `symbology._resolve_product_root`; NO Databento call), populating `product_root` (`ES`→`SP500`) +
      `canonical_instrument_id` (`{venue}:{type}:{root}:{YYYY-MM}[:{strike}{C|P}]`) incl. spaced options
      (`E5AH0 C2510`); `raw_symbol` KEPT as the raw exchange code. +tests. QG green. — instruments-service
- [x] ✅ [SCHEMA] P1. **Add canonical instrument-id + base/root fields to `InstrumentRecord`** — DONE
      unified-api-contracts@`50a93175`: optional additive `canonical_instrument_id` + `product_root` on
      `InstrumentRecord` + 1:1 into `INSTRUMENTS_PARQUET_SCHEMA` (nullable; NOT in the CeFi-only `model_validator`).
      Non-breaking (added-optional-field) — does NOT touch v9 `schema_version`; old parquets read null. +tests. QG
      green. — unified-api-contracts
- [x] ✅ [CODE] P1. **Fix Deribit spot being dropped** — DONE instruments-service@be4c7930a: removed `deribit` from
      `_DERIVATIVES_ONLY_EXCHANGES` (the set's only consumers are the two spot-drop guards in
      `_parse_tardis_instrument`; surgical), updated the stale "deribit has no spot" comments, added
      `test_deribit_spot_not_dropped` (BTC_USDC spot enumerates as SPOT_PAIR; BTC-PERPETUAL still PERPETUAL), and
      corrected 2 pre-existing tests that asserted the bug; QG green (88.53% cov). Deribit spot now enumerates + passes
      `CEFI_BASE_ASSET_UNIVERSE` like any venue. **Run-verify that real Deribit spot appears in a re-captured day**
      (data-ops, rides the IS re-capture). — instruments-service
- [ ] [DATA] P2. **Verify Deribit BTC/ETH options present** (audit §J): run-verify a representative day has BTC/ETH
      options in the batch catalogue (Tardis DERIBIT path; check the endpoint tier didn't drop option metadata).
      **Operator 2026-06-16: BTC/ETH underlyings are FINE for now** — do NOT widen `CEFI_OPTIONS_UNDERLYINGS` or wire
      the dedicated `DERIBIT-OPTIONS` adapter. — instruments-service

## Phase E (TIER 4 — LAST, 🔴 GATED on the v9 `--apply` migration) — Download path-drift + all-asset-group smoke test

> **Do NOT start until TIER 2 (the per-AG v9 `--apply` migration) has landed** — the path-fix must target the FINAL
> canonical `pipeline_mode={mode}_{source}/…/venue=…` shape, not the current v8 shape (operator 2026-06-16: downloads
> last). The smoke-test (first item) MAY run earlier to record the before-state, but the path-template fix lands against
> the migrated shape.

- [ ] [DATA] P1. **Smoke-test instrument/shard CSV download for a representative AVAILABLE shard per asset_group**
      against prod (`https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app`, `DISABLE_AUTH=true`): DeFi (aave_v3 + a
      Solana protocol, with chain), CeFi (binance-futures), TradFi, Sports (with league_id), Prediction. Record HTTP
      code + whether bytes returned. Establishes the before-state + which axes break. — deployment-api
- [ ] [CODE] P1. **Fix DeFi download path-drift against the FINAL v9 shape** (audit §A): thread `chain` from
      `download_shard_csv` (`_downloads.py:407`) into `build_instruments_shard_csv_export` and reconstruct the
      **combined** DeFi venue token for the `venue=` GCS segment (`f"{venue}-{chain}"`, matching
      `canonicalize_defi_venue_combined`) in `services/data_status_drilldown/_csv_export.py:307-339`; mirror in the
      drilldown reader `_instruments.py:62-70`. Verify against the **post-migration** writer truth + the new
      `pipeline_mode=…` prefix. — deployment-api
- [ ] [CODE] P1. **Apply the same fix to any MTDS chain/protocol-partitioned download path** if the smoke test shows
      MTDS DeFi shards 502 the same way (operator: "fix them globally so for MTDS too"). — deployment-api
- [ ] [TEST] P1. Regression: a download-path unit test that builds the GCS object path for a DeFi shard and asserts it
      matches the (migrated) writer's combined-venue/chain shape (guards the split-venue drift from recurring). —
      deployment-api

## Success criteria

- All-asset-group download smoke test green (200 + non-empty CSV) for DeFi/CeFi/TradFi/Sports/Prediction.
- instruments-service drilldown rows no longer all "out of scope"; venue filter narrows results (UI + API).
- No duplicate available/available-dates panels; pagination selector works; QG green per repo; UI todos carry
  `pw:L2 ✓` + regression spec.
- EIGEN + requested bases present in a downloaded binance-spot/hyperliquid instruments CSV (after re-capture).
- TradFi instruments carry a human-canonical base/root + instrument-id (not raw `ESM0`); Deribit BTC/ETH options present
  in the catalogue (or operator-confirmed scope).
