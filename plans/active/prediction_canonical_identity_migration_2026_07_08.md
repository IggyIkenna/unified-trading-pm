---
doc_type: plan
title:
  Prediction canonical identity migration — underlying population + cross-venue canonical_instrument_id + sports
  fixture_id alignment
summary:
  "Follow-up migration from the 2026-07-08 finding-8 resolution (see instrument_id_format_canonicalization_2026_07_08.md
  + instruments-service/docs/PREDICTION_INSTRUMENTS.md § Canonical identity model). The null-fields catalogue-rollup bug
  (base_asset/raw_symbol) is already fixed. What's left is real adapter-level + cross-venue work: populate
  InstrumentRecord.underlying from the existing classify_*_to_canonical_group SSOT, materialise canonical_instrument_id
  from the existing cross_venue_mapping.build_cross_venue_mapping() output, and align Prediction's sports fixture key
  with the Sports asset group's own build_fixture_id() scheme."
status: active
nature: design
asset_group: [prediction]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags:
  [
    prediction,
    canonicalization,
    instrument-identity,
    cross-venue-arbitrage,
    underlying,
    canonical_instrument_id,
    sports-fixture-id,
  ]
related:
  [
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    audit/results/canonical_instrument_id_audit_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-18
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "Operator, 2026-07-08: 'Are you sure these are even sensible things to have for prediction? ... We need to pick one,
  document it, and migrate and update the code if needed.' Filed by the same session that diagnosed + fixed the
  base_asset/raw_symbol catalogue-rollup NULL bug and documented the canonical scheme decision in
  instruments-service/docs/PREDICTION_INSTRUMENTS.md."
assigned_role: data_engineering
drift_direction: advance-code
---

> **Status: `active`** — picked up 2026-07-09. Todos 1, 3, 4, 5 implemented and verified against real prod GCS data (see
> Progress Log); todo 6 VERIFIED SAFE / closed 2026-07-18 (no code change — raw prediction `instrument_id` embeds venue
> by construction; all real consumers respect venue). Remaining open: todo 2 (full catalogue regen/backfill, real-scoped
> and smoke-tested, the FULL unsupervised run intentionally NOT executed — staged-rollout, and must wait for the shared
> canonical-identity migration to settle), todo 7 (shared UAC `gcs_paths.py` MARKET_DATA bucket — gated on MTDS
> migration confirmation), todo 8 (MDPS stale test assertions — different repo, gated on its UAC pin bump). See the
> 2026-07-18 Progress Log entry for the DEFERRED reasons.

## Codex SSOTs

- `instruments-service/docs/PREDICTION_INSTRUMENTS.md` § "Canonical identity model" — the decision this plan executes.
  Read in full before touching any todo below.
- `unified-trading-pm/plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md` finding 8 — the parent
  finding, now resolved-with-a-migration-scoped.
- `codex/02-data/availability-manifest-and-data-status.md`, `codex/06-coding-standards/` — standard data-pipeline +
  coding-standards rules apply (honest absence, no fabricated values, UAC SSOT types).

## Background (do not re-derive — read the doc)

The 2026-07-08 investigation traced `base_asset`/`underlying`/`raw_symbol` NULLs in `prod/catalog.parquet` end-to-end.
`base_asset`/`raw_symbol` were a **catalogue-rollup bug** (already fixed:
`instruments-service/scripts/build_instrument_catalogue.py::build_prediction_catalogue_dataframe()` now threads them
through). `underlying` is a **different, non-bug case** — no adapter has ever called `InstrumentRecord(underlying=...)`.
The operator's real question — do these fields make conceptual sense for Prediction, and what's the real canonical
scheme — is answered in the doc above: `underlying` is sensible for the crypto/macro/commodity subset (comprehensive
`PredictionUnderlying` axis already exists, `unified_api_contracts/canonical/domain/predictions/two_axis.py`) and
correctly `None`/`OTHER` for politics/sports; the per-instance cross-venue identity mechanism already exists
(`cross_venue_mapping.py::build_cross_venue_mapping()`) but runs on-demand over two full venue universes rather than
being wired into the write path or persisted on the catalog. This plan is the migration that closes those two gaps.

## Todos

- [x] [DATA] P1. ✅ **Populate `InstrumentRecord.underlying` at adapter-construction time** —
      `instruments-service@0d0c3742`. Both
      `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/parsing.py::_parse_market()`
      and `.../prediction/kalshi.py::_parse_market()` call `classify_polymarket_to_canonical_group()` /
      `classify_kalshi_to_canonical_group()` (already called for `MarketLifecycle.canonical_group` in the same method —
      reused via a new `classify_lifecycle(market, group=...)` param, not reclassified) → `underlying_for_group()`, and
      pass `underlying=None if is_sports else underlying_value.value` to the `InstrumentRecord(...)` constructor —
      mirroring the exact convention `cross_venue_mapping.py::_build_mapping()` already uses for its own output schema.
      Unit coverage: `tests/unit/test_prediction_underlying.py` (new, 11 tests) — real BTC/CPI/politics/sports examples
      per adapter. Evidence: Progress Log.
- [ ] [DATA] P1. **Regenerate/backfill `prod/catalog.parquet` for Prediction** after the `raw_symbol`/`base_asset`
      rollup fix (already shipped) AND the `underlying` adapter change above ship together — a full
      `build_instrument_catalogue.py --asset-group prediction` run against real GCS data, manifest-verified row counts
      (per the workspace's "plans run to actual completion on real infra" rule — no smoke-test-only claim). Real
      scoping/smoke-test/ETA done 2026-07-09 (see Progress Log) — the full run itself is NOT executed yet (staged
      rollout).
- [x] [DATA] P2. ✅ **Wire `cross_venue_mapping.build_cross_venue_mapping()` into a real, scheduled step** —
      `instruments-service@0d0c3742`. Wired into `build_instrument_catalogue.py::build_prediction_catalogue_dataframe()`
      as a post-processing step (runs every catalogue regen) that persists
      `PredictionMarketCrossVenueMapping.canonical_event_id` onto the matched side's new `canonical_instrument_id`
      catalogue column. Unmatched instruments keep `canonical_instrument_id=""` (honest absence, never a false pair —
      matches the matcher's existing design; verified by a dedicated unit test). Real evidence against prod GCS: 250 /
      1264 matched pairs on 200-/2000-blob samples — see Progress Log.
- [x] [DATA] P2. ✅ **Decide + document the `titles` map source for sports fixture matching** —
      `instruments-service@0d0c3742` (`docs/PREDICTION_INSTRUMENTS.md` §3 item 4). DECIDED: no per-instrument title
      survives anywhere the offline roll-up can reach (`InstrumentRecord` dropped the `symbol` field) — shipped with no
      `titles=` kwarg (the matcher's own honest-absence default). A persisted title side-table (mirroring
      `clob_token_ids`) is documented as the real, buildable follow-up, NOT built this migration.
- [x] [DATA] P2. ✅ **Align Prediction's sports fixture key with the Sports asset group's `build_fixture_id()`** —
      `instruments-service@0d0c3742`, **Polymarket only** (Kalshi explicitly deferred — no team-name-to-canonical
      registry exists for Kalshi's city-level sports titles, left undone rather than guessed).
      `polymarket/parsing.py::_build_sports_id()` now calls `parse_polymarket_sports_fixture()` +
      `build_fixture_id(league, build_team_id(home), build_team_id(away), date)` — the exact call shape
      `build_sports_fixture_team_player_catalogue()` uses for the Sports asset group's own fixture rows (verified by
      reading that function; no network call, unlike the unused `_cross_reference_fixture()`). Real example: EPL Arsenal
      vs. Chelsea, 2026-03-22 → `canonical_instrument_id="EPL:CHELSEA_v_ARSENAL:20260322"`. Concrete byte-parity test in
      `tests/unit/test_polymarket_boost.py::TestBuildSportsId::test_valid_league_returns_tuple`.
- [x] [VERIFY] P2. ✅ **Check whether any real downstream consumer treats Prediction `instrument_id` as globally unique
      without also keying on `venue`** — VERIFIED SAFE, no code change needed (2026-07-18 read-only cross-repo sweep;
      see Progress Log). The raw prediction `instrument_id` embeds venue **by construction** (`PREDICTION:{VENUE}:…`,
      `FOOTBALL:{VENUE}:…`, `{VENUE}:PREDICTION_MARKET:…` — PREDICTION routes through UAC `build_instrument_id`), so it
      is already globally unique on its own; every real consumer respects venue: UTL
      `instruments_catalog_reader.get_availability_bounds()` keys on the `(asset_group, venue, instrument_id)` triple,
      MTDS `live/_is_universe.py::collect_keys_from_is_blobs()` takes `venue` as a param AND prepends it to every
      deduped id, and the features cross-venue arb calculators use a purpose-built venue-less `xv_instrument_id` match
      key **while retaining separate `kalshi_market_ticker` / `polymarket_condition_id` columns** (intentional
      cross-venue matching, not a collision). No collision-risky consumer exists → todo 3's remediation clause is moot;
      and `canonical_instrument_id` is a SEPARATE catalogue column that never mutates the raw `instrument_id`, so
      per-venue uniqueness is preserved unconditionally. (Side-note, out of this plan's prediction-file scope:
      execution-service `validation/instrument_format.py::get_venue_from_instrument_id()` returns `split(":")[0]`, which
      is the TYPE/SPORT prefix — not the venue — for prediction/sports ids; a latent venue-derivation mismatch,
      unrelated to this uniqueness question, flagged for the execution-service owner.)
- [ ] [DECISION] P3. **Re-evaluate `gcs_paths.py`'s `(PREDICTION, MARKET_DATA)` bucket template** once
      `market-tick-data-service/scripts/migrate_prediction_to_pred_prd_v9.py`'s Progress Log confirms
      `market-data-tick-pred-prd-{pid}` is the sole, complete SSOT (deliberately left as the long-form
      `market-data-tick-prediction-{env}-{project_id}` in this session's fix — see `gcs_paths.py`'s own comment). Flip
      to the abbreviated form only after that confirmation, not before.
- [ ] [VERIFY] P3. **Update `market-data-processing-service`'s stale test assertions** —
      `tests/unit/test_dependency_checker_sports_prediction.py` (lines ~149, ~155) assert the OLD unabbreviated
      `instruments-store-prediction-` value for `BucketKind.INSTRUMENTS`, which this session's `gcs_paths.py` fix
      changed to the abbreviated `instruments-store-pred-`. Outside this session's edit scope (MDPS not touched this
      round) — file/update once MDPS bumps its `unified-api-contracts` pin past this fix; until then its own CI will
      catch the drift on that bump.

## Progress Log

- **2026-07-08** — Filed as the tracked follow-up from the finding-8 investigation (null-fields diagnosis +
  catalogue-rollup fix + canonical scheme decision, done same session — see
  `instrument_id_format_canonicalization_2026_07_08.md` and `instruments-service/docs/PREDICTION_INSTRUMENTS.md`). No
  implementation here yet; `status: draft` until an operator/agent picks it up.
- **2026-07-09** — Todos 1, 3, 4, 5 implemented in `instruments-service` (adapters + `build_instrument_catalogue.py`)
  and verified end-to-end against real prod GCS data. Real evidence:
  - **Todo 1 (`underlying`)**: `_parse_market()` in both adapters now calls `underlying_for_group()` on the SAME
    `classify_*_to_canonical_group()` result already computed for `MarketLifecycle.canonical_group` (new optional
    `group=` param on `classify_lifecycle()` so the caller's classification is reused, not redone). Verified with real
    market shapes (direct `_parse_market()` calls, both adapters): Polymarket BTC daily → `underlying="BTC"`; CPI macro
    → `"CPI"`; Trump approval → `"TRUMP"`; unclassifiable → `"OTHER"`; EPL sports → `None`. Kalshi `KXBTCD-*` → `"BTC"`;
    `KXCPIYOY-*` → `"CPI"`; `KXFEDDECISION-*` → `"FED"`; `KXMLBGAME-*` sports → `None`; unclassifiable → `"OTHER"`.
    Correction to this plan's own todo 1 wording: `OTHER` is NOT a blanket politics/sports bucket — most classified
    politics/geo/culture markets get their OWN named underlying (`TRUMP`, `GEO_ISRAEL_IRAN`, `OSCARS`, …); `OTHER` is
    reserved for genuinely-unclassified markets. Unit tests:
    `instruments-service/tests/unit/test_prediction_underlying.py` (new file, 11 tests).
  - **Todo 3 (cross-venue `canonical_instrument_id`)**: wired `build_cross_venue_mapping()` into
    `build_instrument_catalogue.py::build_prediction_catalogue_dataframe()` as a real step that runs on every catalogue
    regen — builds minimal per-conditionId `InstrumentRecord` views split by venue, runs the matcher, and persists
    `canonical_event_id` onto the new `CATALOG_COLUMNS` field `canonical_instrument_id` for matched conditionIds (`""`
    honest absence for unmatched, verified). **Real evidence against prod GCS**
    (`instruments-store-pred-prd-central-element-323112`, `--max-blobs` smoke tests, `--dry-run` forced — see todo 2
    evidence below for the full run log): a 200-blob sample (935 Kalshi + 3024 Polymarket instruments) found **250 real
    matched pairs**; a 2000-blob sample (3834 Kalshi + 31118 Polymarket) found **1264 real matched pairs**, e.g. Kalshi
    `KXBTCD-26JUN24-T95000` ↔ a same-day Polymarket BTC UP_DOWN market both resolving to
    `canonical_instrument_id="PRICE::BTC::UP_DOWN::2026-06-24::DIR"` (unit-test-reproduced in
    `tests/unit/scripts/test_build_instrument_catalogue.py`). Unmatched-stays-blank verified by a dedicated unit test.
  - **Todo 4 (titles map decision)**: DECIDED not to build a titles map this migration — no per-instrument human title
    survives anywhere the offline catalogue roll-up can reach (`InstrumentRecord` dropped the `symbol` field per
    `cross_venue_mapping.py`'s own docstring). Shipped with no `titles=` kwarg, which is the matcher's own documented
    honest-absence default (sports cross-venue pairing stays honestly absent in the catalogue). A persisted title
    side-table (mirroring the existing `clob_token_ids` side-table pattern) is the real, buildable follow-up — NOT done
    this session, left as a documented option in `instruments-service/docs/PREDICTION_INSTRUMENTS.md` §3 item 4.
  - **Todo 5 (sports fixture_id alignment)**: SHIPPED for Polymarket only (not Kalshi — see below). `_build_sports_id()`
    now calls `parse_polymarket_sports_fixture()` (same "Away vs Home" title parser `cross_venue_mapping.py` uses) then
    `build_fixture_id(league, build_team_id(home), build_team_id(away), date)` — the EXACT call shape
    `build_sports_fixture_team_player_catalogue()` uses for the Sports asset group's own fixture rows (verified by
    reading that function; no crosswalk, no network call — the unused `_cross_reference_fixture()` was deliberately NOT
    wired, since a per-market API-Football call is unsuitable for the hot adapter-parsing loop over a 1M+-market
    universe). Confirmed Prediction's league short-code space (`POLYMARKET_PREDICTION_LEAGUES`, e.g. `"EPL"`) IS the
    Sports asset group's own `LEAGUE_REGISTRY` canonical `league_id` space (`league_data_prediction.py`), not a separate
    namespace. Real example: EPL Arsenal vs. Chelsea, 2026-03-22 →
    `canonical_instrument_id="EPL:CHELSEA_v_ARSENAL:20260322"`. Kalshi sports alignment is a real, tracked gap (no
    Kalshi-specific team-name-to-canonical registry exists to safely bridge city-level names like "Seattle" — left
    undone rather than guessed).
  - **Todo 2 (full catalogue regen) — real scoping/smoke-test/ETA, per the staged-rollout rule (full run NOT
    executed)**: real corpus size measured via `gcloud storage ls` on the by_date prefix: **20,909**
    `instruments.parquet` blobs under
    `gs://instruments-store-pred-prd-central-element-323112/instrument_availability/by_date/` (current
    `prod/catalog.parquet` = 2,486,092 rows). Two real, bounded `--max-blobs` dry-run smoke tests against this bucket
    (`--mode full`, ADC admin, ran to completion, correctly `CATALOGUE_SHRINK_BLOCKED`-rejected the write since a
    truncated sample is always smaller than the full catalogue — the monotonic guard worked exactly as designed):
    - 200 blobs: listing ~42s, download+rollup+cross-venue-match ~11s, guard-check ~13s → 7,923 rows, 250 matched pairs.
    - 2000 blobs: listing ~40s, download+rollup+cross-venue-match ~118s, guard-check ~12s → 69,929 rows, 1,264 matched
      pairs. Listing time is roughly FLAT between the two samples (~40-42s — dominated by GCS prefix-walk overhead, not
      blob count in this range); download+rollup+match scales close to linearly with blob count (~59ms/blob).
      Extrapolating the linear phase to the full 20,909 blobs: ~20-25 minutes for download+rollup+match, plus ~1 min
      listing and ~1-2 min guard+promote-write (writing the larger final parquet) → **ETA ~25-40 minutes for a complete
      `--mode full` non-dry-run regen**. Honest caveat: row-DENSITY per blob in the small early-path-sorted samples
      (200/2000-blob: ~35-40 rows/blob average) is lower than the full corpus's real average (2,486,092/20,909 ≈ 119
      rows/blob) — the path-sorted walk likely front-loads chronologically-earlier, thinner-universe dates, so the
      row-count extrapolation is NOT reliable (the wall-clock-time extrapolation above, based on directly-measured
      per-blob processing cost, is the trustworthy number). **This plan's execution_scope is `local-only` — the full
      regen is a real, schedulable follow-up run, intentionally not executed unsupervised this session.**
  - Ship: `instruments-service` (adapters, `build_instrument_catalogue.py`, tests) — `unified-api-contracts` needed NO
    changes (all consumed via existing public `unified_api_contracts.predictions` / `unified_api_contracts.sports`
    facade exports).
  - Deferred (todos 6-8): not started this session — carried forward as-is.
- **2026-07-14** — Investigated a "0.1% canonical_instrument_id population anomaly" flagged from earlier session
  tracking (framed as "smoke-test writes rejected by a shrink guard"). **Finding: not a bug, and not caused by the
  shrink guard.** Live measurement against prod
  (`gs://instruments-store-pred-prd-central-element-323112/prod/catalog.parquet`, 2,530,212 rows as of today — up from
  the 07-08 snapshot's 2,486,092/20,909 blobs to 21,116 blobs, confirming the pipeline has kept running):
  `canonical_instrument_id` populated (non-blank) on 2,570 rows = **0.10157%** (KALSHI 2,270/58,383 = 3.89%; POLYMARKET
  300/2,471,829 = 0.0121%). This is the correct, expected arithmetic consequence of todo 3's own documented scope —
  `canonical_instrument_id` only fires for (a) matched Kalshi↔Polymarket same-market pairs and (b) Polymarket sports
  fixtures — combined with Polymarket outnumbering Kalshi ~42:1 in row count. The overwhelming majority of Polymarket
  rows are single-venue markets with no Kalshi counterpart, so they correctly get no id (honest absence, not a
  dropped/rejected write). The actual `CATALOGUE_SHRINK_BLOCKED` events on record (200-blob/2000-blob smoke-test
  samples, todo 2 evidence above) are a SEPARATE, unrelated, expected event (a truncated sample is always smaller than
  the full catalogue — "the monotonic guard worked exactly as designed"), not a rejection of canonical_instrument_id
  writes specifically. No fix needed here; closing this as investigated/resolved. Also noted in passing: the
  `canonical_instrument_id_audit_2026_07_08.md` doc's reference to an `instruments-store-prediction` bucket (as a live
  naming-split partner) is now stale — that bucket 404s; only `instruments-store-pred-prd-*` exists.
- **2026-07-18** — Prediction-specific open-item sweep (scope-restricted session: prediction files only; shared UAC
  canonical infra was mid-migration by other slots and must not be touched). Reconfirmed todos 1/3/4/5 remain shipped +
  intact — `instruments-service@0d0c3742` is an ancestor of HEAD, tree clean (adapters + `build_instrument_catalogue.py`
  - tests all present). Actioned the remaining opens:
  * **Todo 6 (downstream `instrument_id` uniqueness) — VERIFIED SAFE, closed.** Read-only cross-repo sweep (IS/UTL/MTDS/
    features/execution/strategy/MDPS). The raw prediction `instrument_id` embeds venue by construction (PREDICTION
    routes through UAC `build_instrument_id` → `PREDICTION:{VENUE}:…` / `FOOTBALL:{VENUE}:…` /
    `{VENUE}:PREDICTION_MARKET:…`), so it is globally unique on its own. Real consumers verified venue-respecting: UTL
    `instruments_catalog_reader.get_availability_bounds()` keys on the `(asset_group, venue, instrument_id)` triple
    (exact canonical-id match first, venue+raw_symbol / venue+base_asset fallbacks); MTDS `live/_is_universe.py`
    `collect_keys_from_is_blobs()` takes `venue` as a param and prepends it to every deduped id (venue-scoped `set`);
    features cross-venue arb (`prediction_cross_venue_dispersion.py` et al.) uses a deliberate venue-less
    `xv_instrument_id = "XV:{underlying}:{bet_type}:{settlement}"` match key while carrying separate
    `kalshi_market_ticker` / `polymarket_condition_id` columns (intentional cross-venue matching, not a collision). No
    collision-risky consumer exists → the todo-3 remediation clause is moot; and `canonical_instrument_id` is a SEPARATE
    catalogue column that never mutates raw `instrument_id`, so per-venue uniqueness is preserved unconditionally. Side
    finding (out of this plan's prediction-file scope): execution-service `validation/instrument_format.py`
    `get_venue_from_instrument_id()` returns `split(":")[0]` — the TYPE/SPORT prefix, not the venue, for
    prediction/sports ids (latent venue-derivation mismatch, unrelated to this uniqueness question; flagged for the
    execution-service owner, not fixed here as it is outside the prediction-adapter/UAC-predictions scope this session
    was restricted to).
  * **Todo 2 (full `prod/catalog.parquet` regen) — still open, DEFERRED.** This is an operational full-corpus prod-GCS
    run (~21k blobs → ~2.5M-row catalogue, ~25-40 min), `execution_scope: local-only` + staged-rollout, not a
    prediction-file change. Deliberately NOT fired this session: other slots were actively migrating the shared
    canonical identity infra (`canonical_id_builder`, tradfi/cefi canonicalizers) that `build_instrument_catalogue.py`
    imports — running a full regen mid-migration would bake transitional/half-migrated canonical ids into the persisted
    catalogue. Schedule after the canonical-identity migration settles.
  * **Todo 7 (`gcs_paths.py` MARKET_DATA bucket template) — still open, DEFERRED.** `gcs_paths.py` is a shared UAC file
    (not prediction-specific) and the flip is explicitly gated on the MTDS `migrate_prediction_to_pred_prd_v9.py`
    Progress Log confirming `market-data-tick-pred-prd-{pid}` is the sole complete SSOT. Shared file + external gate →
    operator/owner decision, out of this session's scope.
  * **Todo 8 (MDPS stale test assertions) — still open, DEFERRED.** Lives in `market-data-processing-service` (not
    instruments-service / UAC-predictions), gated on MDPS bumping its `unified-api-contracts` pin past the
    `gcs_paths.py` abbreviation; its own CI catches the drift on that bump. Out of the prediction-file scope this
    session was restricted to.
