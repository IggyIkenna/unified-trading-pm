---
doc_type: plan
title: Data-status tab + instruments download remediation (deployment-api / deployment-ui / CeFi universe)
summary:
  Fix data-status tab UI bugs and instruments CSV download regressions in deployment-api/deployment-ui, gated on v9
  manifest migration completion.
status: active
nature: process
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [cross-cutting]; title/summary are deployment-api/
  # deployment-ui data-status tab UI bugs, the new ui tranche's exact scope
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, instruments-service, market-tick-data-service, ml-service]
scope: [engineer, admin]
tags: [data-status, downloads, remediation, deployment-ui, deployment-api, instruments, csv, manifest-v9]
related: []
created: 2026-06-16
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-27
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    "plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md (root-caused findings A–H,
    file:line)",
    operator 2026-06-16 (data-status tab walkthrough; "blockers to mtds migration and downloads"; smoke-test downloads
    across all asset_groups + fix globally),
  ]
assigned_role: backend_engineer
drift_direction: advance-code
context_scope:
  [
    /plans/archive/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md,
    /plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md,
    deployment-ui/src/components/DataStatusTab.tsx,
    deployment-api/deployment_api/services/data_status/reference_scope.py,
  ]
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

> **🔴 APPLY GATE (operator 2026-06-17) — DRY-RUN EVERYTHING VIA MANIFEST-BETA BEFORE ANY `--apply`.** No v9 `--apply`
> (path migration / object movement / `reconcile_phantom_manifest_rows_all.py --apply`) for ANY `asset_group` OR service
> may run until the v9 **dry-run projected index has been built for EVERY service × asset_group** —
> **instruments-service AND market-tick-data-service** (defi/cefi/tradfi/sports/prediction) AND the downstream services
> — and each has been **eyeballed in the data-status tab under Manifest-beta mode** (the "m variable":
> `DATA_STATUS_BETA_MANIFEST_BLOB=\_index/audit/projected_index*{asset_group}.parquet`, Mode = Manifest). The dry-run is
> non-destructive (`--projection requires --dry-run`): it routes every `add`/`record_empty`/`record_failed`into a
> projected v9`\_index`parquet we read back, so we verify the movements make sense BEFORE committing them. **This gate
> precedes TIER 2** — TIER 2's per-AG`--apply` is the LAST step, only after every projection is reviewed + signed off.
>
> **MTDS gap to close first**: `BETA_ELIGIBLE_SERVICES` in `deployment-api/deployment_api/services/manifest_source.py`
> is currently `{instruments-service}` ONLY — so the beta data-status read cannot preview MTDS even though the MTDS
> projection writers already exist (`market-tick-data-service/scripts/rebuild_{defi,cefi,tradfi,prediction}_manifest.py`
>
> - `rebuild_sports_manifest_v9.py`, all routing through `_rebuild_projection.write_projection`). Add MTDS (+ downstream
>   services) to `BETA_ELIGIBLE_SERVICES` once their projections are generated, so the all-AG beta view covers them.
>   This is why the operator's MTDS data-status currently shows the LIVE pre-migration index (DeFi ~36%), while
>   instruments-service (the one beta-eligible service) shows its projected/canonical numbers (DeFi ~93%).
>
> **What the projection LOCATES (it does not FETCH — corrects the "migration won't lift numbers" framing)**: the rebuild
> **walks GCS** (`rebuild_defi_manifest.py:494` `_day_prefixes` probes BOTH `category=`/`asset_group=` hive vocabularies
> AND bare + `pipeline_mode=` path shapes) and emits one manifest row per discovered parquet, re-canonicalising
> **orphaned** objects the current live `_index` never indexed (the "100% phantom rate" orphan class). So a projected
> captured% ABOVE the live `_index` captured% is legitimate **orphan recovery** — locating data that already exists in
> non-canonical places, NOT adding data. The residual gap after discovery still splits into honest `empty_confirmed`
> (e.g. Sports 71% empty = no-fixture days), `attempted_failed` (real fetch failures to backfill), and
> `expected_unattempted` (never tried) — only the first is benign. The dry-run preview is exactly how we tell these
> apart per service×AG before any movement.

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

> **🟡 pw:L2 RE-RUN (2026-07-28) — the prediction_v9_breakdown blocker is now independently FIXED; a NEW, unrelated
> blocker replaced it, so the 3 UI items below stay unticked.** Fresh full run
> (`npx playwright test --project=chromium tests/smoke/`, deployment-ui HEAD `dfa5d0e`, slot `.tabs/4`): **410/423
> passed.** `prediction_v9_breakdown.spec.ts` has **0** failures (root-caused + fixed same-day 2026-06-16 by
> deployment-ui@`687d4ce`, confirmed still fixed). Every data-status-focused spec passes, incl. the vitest regression
> (`tests/unit/components/DataStatusTab.refetch_dedupe_pagination.test.tsx`) all 3 items below cite. **But 13 NEW,
> unrelated failures** now keep the full-suite exit non-zero: `cockpit.spec.ts` / `fleet-git-tab.spec.ts` /
> `nav-menu-dedup.spec.ts` / `repos-tab.spec.ts`, all clustering on a standalone "Fleet Git-Health" nav entry that
> appears to have been dropped from `NAV_ITEMS_CANONICAL` during 2026-07-27 Cockpit/observability nav work (unrelated to
> this plan). None reference `DataStatusTab.tsx`, venue-filter, de-dupe-panel, or pagination code. Filed as its own
> issue rather than fixed inline (ambiguous fold-vs-regression call + risk of colliding with whoever is actively in that
> nav territory — task_template.md finding S, don't guess a scope-unclear fix):
> `plans/archive/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md`. Per this doc's own established
> precedent (the 2026-06-16 banner above) and the `pw:L2` SSOT definition
> (`codex/06-coding-standards/ ui-testing-layers.md`: full `tests/smoke/` exits 0), the 3 UI items below stay formally
> unticked pending that separate doc's resolution — this is evidence-backed "genuinely still blocked," not a stale
> unrun-check.

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
      DERIBIT) stay "" by design (documented in code) → unlocks per-instrument_type scope + per-type UI drilldown + §J
      Deribit-options signal once the gated v9 apply runs. Guards: `test_orchestrator_helpers.py` (3 writer tests) +
      `test_migrate_instruments_store_v9.py` (backfill + existing-value-preserved). — instruments-service.
- [x] ✅ [CODE] P1. **Venue filter — backend** — DONE deployment-api@3d9a0e032: added repeatable `venue: list[str]` to
      the `/manifest` route + `get_manifest_status` (threaded through
      `_get_manifest_status_sync`/`_dispatch_category_builds`/ `_build_manifest_category`), engaged it in the
      `any_row_filter` gate, added `_apply_venue_filter` (case-insensitive OR) before the venue breakdown, and gated the
      process-pool path off (it doesn't thread filters); +3 tests; QG green. — deployment-api
- [ ] [UI] P1. **Venue filter — frontend** — CODE-SHIPPED deployment-ui@`80c547d` (re-fetch `useEffect` on
      `selectedVenues`/folders/data-types change, post-first-load guarded; regression:
      `tests/unit/components/DataStatusTab.refetch_dedupe_pagination.test.tsx`; vitest+tsc+build green under Node 22).
      **NOT ticked ✅ — `pw:L2` RAN 2026-07-28 (410/423, 0 failures touching this item) but the full suite doesn't exit
      0** (13 unrelated failures, see the 🟡 2026-07-28 banner above +
      `deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md`). Genuinely still blocked on that separate doc, not
      an unrun check. — deployment-ui `[UI]`. **na-eligibility-audit 2026-08-03**: the cited blocker doc is now
      `status: resolved`/ARCHIVED (2026-07-29, `deployment-ui@067f7cd`, "89/89 Playwright smoke tests pass", no compat
      redirect needed per operator direction) — the specific 13-failure Fleet-Git nav regression that was the sole
      reason this wasn't ticked is fixed. Not flipping here myself (no fresh `pw:L2` re-run performed this pass, and the
      runtime-verification rule requires an actual green run, not a doc-only inference) — the next touch should re-run
      `pw:L2` full suite and tick on a confirmed exit 0.

## Phase B (TIER 1 cleanup) — UI clarity (duplicate panels, pagination)

- [ ] [UI] P2. **Collapse duplicate "available" vs "available dates"** — CODE-SHIPPED deployment-ui@`80c547d` (legacy
      "Data Types" block gated so it no longer double-renders beside the honest panel; same regression spec; green under
      Node 22). **`pw:L2` RAN 2026-07-28 (410/423, 0 failures touching this item) but the full suite doesn't exit 0**
      (same unrelated 13-failure Fleet-Git nav regression, see the 🟡 2026-07-28 banner above +
      `deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md`). Genuinely still blocked, not an unrun check. —
      deployment-ui `[UI]`. **na-eligibility-audit 2026-08-03**: same resolved-blocker citation as the venue-filter item
      above (`deployment-ui@067f7cd`, 2026-07-29, 89/89 pass) — not flipping without a fresh `pw:L2` re-run.
- [ ] [UI] P2. **Pagination visible-count selector** — CODE-SHIPPED deployment-ui@`80c547d` (`DateList` size selector
      50/100/200/1000/2000/All; same regression spec; green under Node 22). Static server-truncation `+{N} more` labels
      (`:3891,3911,5386`, `VenuePillList :230`) still need a backend `limit` bump to be client-pageable — follow-on if
      wanted. **`pw:L2` RAN 2026-07-28 (410/423, 0 failures touching this item) but the full suite doesn't exit 0**
      (same unrelated 13-failure Fleet-Git nav regression, see the 🟡 2026-07-28 banner above +
      `deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md`). Genuinely still blocked, not an unrun check. —
      deployment-ui `[UI]`. **na-eligibility-audit 2026-08-03**: same resolved-blocker citation as the venue-filter item
      above (`deployment-ui@067f7cd`, 2026-07-29, 89/89 pass) — not flipping without a fresh `pw:L2` re-run.
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
      three near-indistinguishable greens (emerald-500 / teal-400 / sky-300) + two low-contrast greys. New
      `SEGMENT_COLORS` palette walks distinct hues (emerald → cyan → blue → amber → red → slate, all 500-stop, no
      <40%-opacity fills); legend swatches kept in lockstep + enlarged (w-2.5) with higher-contrast text. — repo
      deployment-ui@`7007529` | pw:L2 ✓ (215/215 smoke) | regression: tests/smoke/data_status_coverage_labels.spec.ts —
      deployment-ui `[UI]`
- [x] ✅ [CODE] P1. **CeFi venues "out of scope" on the `/service/instruments-service/` board — REAL root cause was a
      reference-catalogue venue-token vocabulary mismatch (the prior "STALE DEPLOY" verdict was WRONG; corrected
      2026-06-17 after the operator confirmed it persisted post-redeploy + hard-refresh).** The IS view is a
      `REFERENCE_BUNDLE_SERVICE`, so `breakdowns_core._classify_data_type_for_venue` scopes each venue via
      `reference_scope.is_reference_venue_day_in_scope` against the **instruments-service catalogue**
      (`data-catalogue.instruments-service.yaml`), NOT the market-data `is_expected` registry (which the prior
      reproduction tested — wrong path). `reference_genesis` did an EXACT uppercased lookup, but the catalogue lists
      **base exchanges** (`COINBASE`, `OKX`, `DERIBIT`) while the instruments-store manifest qualifies them by role
      (`COINBASE-SPOT`, `OKX-FUTURES/SPOT/SWAP`, `DERIBIT-COMBO`) → those resolved to `None` = out*of_scope. Two further
      cefi venues (`BITFINEX-*`, `BITGET-_`) were real instruments-store venues simply absent from the catalogue.
      **FIX** (deployment-api `reference_scope.py`): `reference_genesis` now falls back to the base token after
      stripping a market-role suffix (`-SPOT/-FUTURES/-SWAP/-PERP/-PERPETUAL/-COMBO`) →
      COINBASE-SPOT/OKX-_/DERIBIT-COMBO resolve; **+** PM `configs/data-catalogue.instruments-service.yaml` adds
      `BITFINEX-SPOT/FUTURES` (2020-01-01) + `BITGET-SPOT/FUTURES` (2024-11-08), genesis transcribed from
      `VenueMapping`/the live instruments-store manifest. VERIFIED: all **18** `instruments-store-cefi` venues now
      resolve in-scope; `tradfi`/`prediction` IS instruments- stores already held only catalogued venues (no IS-view
      out-of-scope there). +1 regression test (`test_reference_genesis_tolerates_market_role_suffix`). NOTE:
      `KRAKEN-_`(cefi) /`YAHOO_FINANCE`(tradfi) / `KALSHI`(prediction) are NOT in any instruments-store → they never
      appear on the IS view; any out-of-scope the operator sees for them is the **market-tick**`is_expected`path at the
      data_type grain (e.g. raw`ohlcv_1m` from Yahoo/Kalshi), which is informative-by-design, not the IS-view bug —
      tracked separately below.

- [ ] [DATA] P2. **Verify the market-tick-view (`is_expected`) out-of-scope for YAHOO_FINANCE / KALSHI is
      correct-by-design vs a registry gap** (deployment-api `breakdowns_core` market-data path; UAC
      `registry/expected_coverage.py`). On the `market-tick-data-service` view (NOT the IS view),
      `YAHOO_FINANCE ohlcv_1m` + `KALSHI ohlcv_1m` resolve `out_of_scope=True` because `is_expected(...)==False` for
      those RAW fine-grained data_types AND `is_processed_data_type==False`. For Yahoo (daily/coarse provider, no
      historical 1m) + Kalshi this is almost certainly **correct/informative** (the source genuinely doesn't supply that
      granularity). Confirm per-venue which raw data_types each source ACTUALLY provides; if a data_type that IS
      provided is wrongly out-of-scope, add it to `EXPECTED_COVERAGE_BY_ASSET_GROUP[ag][venue]`; otherwise leave
      out-of-scope (it correctly signals "this source doesn't provide this data_type"). Provenance: operator "I still
      see out of scope … prediction and tradfi" 2026-06-17; the IS-view cefi out-of-scope is the separate ✅ item above.

- [x] ✅ [CODE] P1. **DeFi venue breakdown duplicates bare PROTOCOL alongside PROTOCOL-CHAIN** — FIXED
      deployment-api@`67972d8`. Root cause: `_filter_to_canonical_defi_venues` used
      `empty_axis = (venues == "") | (chains == "")` as its pass-through guard. Rows with a real DeFi protocol venue
      (e.g. `TRADER_JOE_V2`) but blank chain were NOT in the canonical `(venue, chain)` whitelist yet passed through via
      `chains == ""`. They then reached `_canonicalise_defi_venue_column` where `normalize_defi_venue(v, None)` emits
      the bare `TRADER_JOE_V2` string, producing a duplicate entry alongside the canonical `TRADER_JOE_V2-AVALANCHE`
      row. The same pattern affected `AAVE_V3`, `BALANCER`, `CURVE`, `SUSHISWAP_V3` (all with `–AVALANCHE` siblings).
      Fix: tighten `empty_axis` to `empty_venue = venues == ""` only — rows with a blank chain but a non-empty venue are
      dropped (they are sub-bucket phantom rows, NOT in the whitelist, and produce no canonical display label).
      Regression test added:
      `TestDefiLegacyVenueFilter::test_blank_chain_protocol_row_does_not_produce_bare_protocol_duplicate`.

- [ ] [DATA] P2. **DEFERRED — Audit sub-bucket shards (oracle-prices / perp-funding / lst-rates) for blank-chain
      manifest rows that produce phantom entries in the consolidated DeFi index.** The
      `_filter_to_canonical_defi_venues` fix (item above) drops them from the display, but the underlying blank-chain
      rows still exist in the MTDS manifest. These rows likely originate from older sub-bucket shards (oracle-prices /
      perp-funding / lst-rates) that pre-date the chain split. A proper cleanup would: (1) run
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run` to confirm
      scope; (2) verify whether these rows correspond to real GCS data or are genuine phantoms; (3) if phantom, apply
      `--apply` after the TIER-2 v9 migration is complete (gated on the same APPLY-GATE above). Do NOT address before
      the v9 migration lands — path shapes change. **MIGRATED FROM:** deployment-api@`67972d8` investigation
      (2026-06-22). — deployment-api + instruments-service (Phase C / TIER 2 scope).

## Phase C (TIER 1 cleanup) — CeFi universe extension (instruments completeness + EigenLayer dust)

- [x] ✅ [CONFIG] P1. **Extend `CEFI_BASE_ASSET_UNIVERSE`** (audit §G) — DONE unified-api-contracts@f4f7f8e (operator
      2026-06-16 "add the rest"): added `EIGEN` (EigenLayer rewards dust) +
      `AAVE, ALGO, AXS, CHZ, COMP, DASH, ENJ, EOS,     FIL, GALA, ICP, MANA, SAND, THETA, XLM, ZEC` to the frozenset
      (~28→~45); regression test `tests/test_cefi_universe_coverage.py`; QG green. All three adapters
      (tardis/hyperliquid/aster) import it. — unified-api-contracts
- [x] [DATA] P1. ✅ **DONE — EIGEN + added bases already re-captured (verified 2026-07-18).** Read the live cefi
      `prod/catalog.parquet` on real infra: **`base_asset=EIGEN` = 25 rows across 8 venues** (ASTER, BINANCE-FUTURES,
      BINANCE-SPOT, BITFINEX-SPOT, BITGET-FUTURES, BITGET-SPOT, BYBIT, BYBIT-SPOT). So the re-capture happened (the
      capture-freeze un-froze + the active cefi enumeration ran) — the added bases are in the universe + downloadable
      catalogue. No further VM re-capture needed. — instruments-service
- [x] [TEST] P2. ✅ **DONE — already covered by `unified-api-contracts/tests/test_cefi_universe_coverage.py`.**
      `test_eigen_usdt_and_usdc_pairs_would_be_accepted()` (line 230) asserts EIGEN/USDT (binance-spot) + EIGEN/USDC
      (hyperliquid settle) are accepted (base ∈ CEFI_BASE_ASSET_UNIVERSE ∧ quote ∈ accepted quotes);
      `test_restaking_extras_present()` asserts KING/EIGEN/ETHFI present + `test_universe_size_band()` guards accidental
      shrink. — unified-api-contracts

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

### APPLY-GATE todos (the dry-run-everything gate above — these BLOCK every TIER 2 `--apply`)

- [x] ✅ [INFRA] P0. **Build the v9 dry-run projected index for market-tick-data-service, per asset_group** — ALREADY
      DONE: verified all 5 MTDS projections exist in the prd buckets' `_index/audit/`
      (`projected_index_{defi,cefi,tradfi,sports,prediction}.parquet`; defi + prediction re-run 2026-06-17). DeFi
      projection diffed vs live: 100% v9, recovers +92k captured shards (orphan_sweep = 315,711 rows) and surfaces 15×
      more `attempted_failed` than the stale v8 live index. Non-destructive (`--projection requires --dry-run`). —
      market-tick-data-service
- [x] ✅ [CODE] P0. **Add `market-tick-data-service` to `BETA_ELIGIBLE_SERVICES`** — DONE deployment-api@`a5b678e`:
      `manifest_source.BETA_ELIGIBLE_SERVICES = {instruments-service, market-tick-data-service}` (premise satisfied —
      all 5 MTDS AGs now projected). Reworked 5 test sites to use a still-non-projected service (features-delta-one) as
      the non-eligible exemplar; the two-phase rollup worker writes MTDS's `.beta` rollup in phase 2 so the beta read
      finds its blob (no 503). QG green (87s); landed on LDR (Tier-C drain → staging ≤30 min). Inert in prod (beta is
      env-gated on `DATA_STATUS_BETA_MANIFEST_BLOB`). Downstream services (features/strategy) stay non-eligible until
      their projections land. — deployment-api
- [x] ✅ [INFRA] P0. **FIXED the rollup-svc phase-2 (BETA) 500 — root-caused + shipped + prod-verified green**
      (deployment-api@`b014ae9`, build `eea66498`). ROOT CAUSE (not memory/deadline): the coverage build for the SHARED
      pseudo-key (`features-calendar` / `ml-service`) called `resolve_bucket_name(asset_group='shared')` →
      `BucketNamingError`, which subclasses bare `Exception` and so ESCAPED `run_rollup`'s narrow
      `except (RuntimeError, ValueError, OSError)` → crashed the ENTIRE phase-1 sweep → phase-2 (BETA) never ran →
      instruments `.beta` froze since 2026-06-16 + MTDS `.beta` never written. Reproduced faithfully via the exact
      two-phase route path locally (events initialised). FIX (2 parts): (1) `defi.py::_read_defi_merged_index` returns
      empty for the `'shared'` pseudo-key instead of raising; (2) `data_status_rollup_worker.run_rollup` broadened both
      per-service catches to `except Exception` (shard-level failure isolation — one bad service must never abort the
      sweep; also contains the separate per-service coverage errors tracked in the P2 follow-up below). VERIFIED in
      prod: rollup-run flipped 500→**200** (335s), and the **prod cron auto-refreshed BOTH** beta blobs (instruments +
      MTDS) at 16:13 with zero manual intervention — self-healing every `*/10`. — deployment-api
- [x] ✅ [CODE] P2. **`features-cross-instrument` per-AG/prediction-kind bug FIXED + prod-verified** —
      deployment-api@`c1aab6e` (build `61eb6e93`): the `ag=="prediction"` branch resolved kind-only
      (`pred_kind if pred_kind else kind`), which for a per-AG kind with no `PREDICTION_KIND_MAP` entry raised
      "asset_group= is required" → fixed in BOTH `defi.py` + `manifest.py` to resolve WITH `asset_group` when no
      prediction-special kind. Verified in prod: cron rollup-run 200 (16:20/16:40), features-cross-instrument coverage
      refreshes, ZERO `SERVICE_FAILED` for it in 40m. The SHARED services (features-calendar/ml-service) remain
      honest-empty BY DESIGN (routing them through the DeFi reader = garbage; real cross-asset coverage = a dedicated
      SHARED path, tracked in `instruments_mtds_subset_consistency_remediation_2026_06_17.md`). — deployment-api
- [ ] [CODE] P3. **Per-service coverage `BucketNamingError`s surfaced by the rollup isolation fix (follow-up)** — after
      the isolation fix (deployment-api@b014ae9) the rollup sweep no longer crashes, but it now logs `SERVICE_FAILED`
      for cross-asset/edge services whose coverage build mis-resolves a bucket: (1) `features-calendar-service` /
      `ml-service` (SHARED pseudo-key → now honest-skipped to empty by the defi.py guard — they show no coverage until a
      `(service,'shared')` override or kind-only resolve is added); (2) `features-cross-instrument-service` →
      `resolve_bucket_name` called with `asset_group=None` for a per-AG kind ("asset_group= is required"). These are
      PRE-EXISTING (were masked because the sweep crashed on `'shared'` first) and are now CONTAINED (rollup stays
      green, beta blobs write) — but those services' coverage is degraded. Root-fix each service's coverage bucket
      resolution (override / kind-only / correct cat enumeration) so their data-status panels are accurate. —
      deployment-api
- [x] ✅ [DATA] P0. **APPLY GATE sign-off — cefi, tradfi, prediction: DONE, eyeballed by Ikenna (operator ruling
      2026-08-07, recorded here in `data_status_tab_and_downloads_remediation_2026_06_16.md`; corroborated in
      `/plans/active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md`).** Projected captured/attempted/empty/
      failed split confirmed sane (orphan recovery looks right, no phantom over-count) for these 3 AGs under
      Manifest-beta mode. **TIER 2 `--apply` is UNBLOCKED for cefi, tradfi, prediction** — proceed per the APPLY GATE
      banner above (per-AG, not a whole-doc gate).
- [ ] [DATA] P0. **APPLY GATE sign-off — defi, sports: HOLD (operator ruling 2026-08-07).** NOT yet eyeballed — Ikenna
      is still wrestling with agents on manifest canonicalisation for these 2 AGs (see their own outstanding
      canonicalisation todos elsewhere in the corpus); the projected index isn't stable enough to sign off yet. **TIER 2
      `--apply` STAYS GATED for defi and sports** until this is re-run and confirmed clean after canonicalisation lands.
      Re-check status before assuming this has cleared — do not infer from the cefi/tradfi/ prediction sign-off above. —
      deployment-api / market-tick-data-service / instruments-service

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
- [x] [DATA] P2. ✅ **VERIFIED 2026-07-18 — Deribit BTC/ETH options present in the live cefi catalogue.** Read
      `prod/catalog.parquet` (cefi, 425,573 rows) on real infra: **264,122 DERIBIT OPTION rows — BTC 129,777 + ETH
      134,345** (instrument_types on DERIBIT = COMBO/FUTURE/OPTION/PERPETUAL/SPOT_PAIR; option metadata intact). Per
      operator 2026-06-16, kept BTC/ETH underlyings only (did NOT widen `CEFI_OPTIONS_UNDERLYINGS`). —
      instruments-service

## Phase E (TIER 4 — LAST, 🔴 GATED on the v9 `--apply` migration) — Download path-drift + all-asset-group smoke test

> **Do NOT start until TIER 2 (the per-AG v9 `--apply` migration) has landed** — the path-fix must target the FINAL
> canonical `pipeline_mode={mode}_{source}/…/venue=…` shape, not the current v8 shape (operator 2026-06-16: downloads
> last). The smoke-test (first item) MAY run earlier to record the before-state, but the path-template fix lands against
> the migrated shape.

- [x] [DATA] P1. ✅ **SMOKE DONE 2026-07-18** (prod `uts-shared-deployment-api-cldtjniqvq-an.a.run.app`,
      `/api/data-status/download-catalogue-csv?service=…&asset_group=…`, unauth reads work). Results — **HTTP code +
      bytes**: `IS/defi → 200 text/csv (941,845 b)` ✅ · `IS/cefi → 200 text/csv (32,879,539 b)` ✅ ·
      `IS/prediction → 200 text/csv` ✅ · **`MTDS/defi → 200 text/csv`** ✅ (the specifically 502-prone chain/protocol
      path WORKS — no path-drift 502) · **`IS/sports → 500`** ⚠️ · **`IS/tradfi → 500`** ⚠️ (both generic "Internal
      server error, check server logs", req_id bee0103f… — the large-catalogue CSV build errors; NEW finding, needs a
      Cloud Run server-log triage — likely a build OOM/timeout or a sports/tradfi-specific CSV-shape bug). Net: the DeFi
      502 the §A fix targeted does NOT reproduce (DeFi + MTDS-DeFi both 200 real CSV); the break is now sports+tradfi. —
      deployment-api. **RESOLVED 2026-07-20** — filed + fully root-caused + fixed same window, archived:
      `plans/archive/issues/data_status_catalogue_csv_download_500_sports_tradfi_2026_07_18.md`
      (deployment-api@`65f5593`). **tradfi** was a real bug (67.41 MiB CSV built as one buffered `Response`, exceeding
      Cloud Run's ~32 MiB buffered cap — the platform rejected it, no Python traceback; fixed by streaming via
      `_iter_catalogue_csv_chunks` + `StreamingResponse`; cefi was 0.7 MiB from the same cliff and is now covered too).
      **sports** was NOT a code bug — a transient manifest-consolidator staleness (honest-absence 500 by design,
      re-measure succeeds). Regression:
      `deployment-api/tests/unit/test_route_data_status_catalogue.py::TestDownloadCatalogueCsvPerAssetGroupSmoke` +
      `TestDownloadCatalogueCsvStreamingBoundaries`. (Verified re-checking 2026-07-28: no newer successor doc was needed
      — this one already closes the loop; a fresh live re-probe against prod during this session returned 200 for sports
      on the first attempt, consistent with the documented "transient, not a bug" finding.)
- [x] ✅ [CODE] P1. **Fix DeFi download path-drift against the FINAL v9 shape** (audit §A): thread `chain` from
      `download_shard_csv` (`_downloads.py:407`) into `build_instruments_shard_csv_export` and reconstruct the
      **combined** DeFi venue token for the `venue=` GCS segment (`f"{venue}-{chain}"`, matching
      `canonicalize_defi_venue_combined`) in `services/data_status_drilldown/_csv_export.py:307-339`; mirror in the
      drilldown reader `_instruments.py:62-70`. Verify against the **post-migration** writer truth + the new
      `pipeline_mode=…` prefix. — deployment-api@610a412
- [x] [CODE] P1. ✅ **NOT NEEDED (verified 2026-07-18).** The smoke above shows `MTDS/defi → 200 text/csv` — the MTDS
      DeFi download path does NOT 502, so there is no path-drift to mirror. The §A DeFi fix (`@610a412`) already covers
      the reproducing case. (The remaining break is sports+tradfi 500, an unrelated large-catalogue-build error — new
      finding, not a chain/protocol path-drift.) — deployment-api
- [x] ✅ [TEST] P1. Regression: a download-path unit test that builds the GCS object path for a DeFi shard and asserts
      it matches the (migrated) writer's combined-venue/chain shape (guards the split-venue drift from recurring). —
      deployment-api@610a412 (tests/unit/data_status/test_defi_shard_download_path.py)

## Success criteria

- All-asset-group download smoke test green (200 + non-empty CSV) for DeFi/CeFi/TradFi/Sports/Prediction.
- instruments-service drilldown rows no longer all "out of scope"; venue filter narrows results (UI + API).
- No duplicate available/available-dates panels; pagination selector works; QG green per repo; UI todos carry
  `pw:L2 ✓` + regression spec.
- EIGEN + requested bases present in a downloaded binance-spot/hyperliquid instruments CSV (after re-capture).
- TradFi instruments carry a human-canonical base/root + instrument-id (not raw `ESM0`); Deribit BTC/ETH options present
  in the catalogue (or operator-confirmed scope).

## Deferred work — migrated to:

**Not yet identified** — the inline `[DATA] P2` item "Audit sub-bucket shards (oracle-prices / perp-funding / lst-rates)
for blank-chain manifest rows that produce phantom entries" is explicitly gated on this SAME plan's own
`APPLY GATE (operator 2026-06-17)` section (dry-run-everything-before-`--apply`) and the TIER-2 v9 migration, both still
tracked within this document (see the `### APPLY-GATE todos` section). Searched `plans/active/` + `plans/epics/` for a
plan that has since taken ownership of this specific sub-bucket phantom-row audit — none found. This plan remains the
owner; the item stays blocked until this plan's own APPLY-GATE + TIER-2 v9 migration land.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — `locked_by: live-defi-rollout`; carries an explicit APPLY GATE
  requiring operator eyeball of every service × asset_group projected index before any TIER-2 `--apply`, and 3 UI todos
  blocked on a separate playwright-suite regression doc.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: APPLY GATE sign-off
  split per-AG — cefi/tradfi/prediction eyeballed by Ikenna, DONE, TIER 2 `--apply` unblocked for those 3. defi/sports
  HOLD — Ikenna still wrestling with agents on manifest canonicalisation for those two, sign-off not attempted yet. The
  DeFi sub-bucket phantom-row audit todo (§ "Deferred work") stays blocked accordingly — it's gated on defi's own
  sign-off, which is explicitly still HOLD, not on the doc-wide gate as a whole.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- added the DataStatusTab.tsx + reference_scope.py
  source targets the remaining open UI/backend todos actually touch.
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, valid — `locked_by: live-defi-rollout`; the 3 UI todos stay
  correctly blocked pending a fresh `pw:L2` full-suite green (the cited nav-regression blocker doc is resolved but no
  re-run has happened since); the DeFi sub-bucket phantom-row audit + the defi/sports APPLY-GATE sign-off stay correctly
  HOLD per today's own operator ruling above (Ikenna's canonicalisation work not yet landed).
