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
status: draft
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
last_updated: 2026-07-08
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

> **Status: `draft`** — not ingested/dispatched. Flip to `active` when an operator or agent picks this up. Everything
> here is scoped, evidence-backed design work from the 2026-07-08 investigation session; nothing here has been
> implemented yet.

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

- [ ] [DATA] P1. **Populate `InstrumentRecord.underlying` at adapter-construction time** — in both
      `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/parsing.py::_parse_market()`
      and `.../prediction/kalshi.py::_parse_market()`, call `classify_polymarket_to_canonical_group()` /
      `classify_kalshi_to_canonical_group()` (already called for `MarketLifecycle.canonical_group` in the same method —
      reuse the result, don't reclassify) → `underlying_for_group()`
      (`unified_api_contracts.canonical.domain.predictions.two_axis`), and pass
      `underlying=None if <sports bet_type> else underlying_value.value` to the `InstrumentRecord(...)` constructor —
      mirroring the exact convention `cross_venue_mapping.py::_build_mapping()` already uses for its own output schema.
      Add unit coverage asserting a real BTC/CPI/politics/sports example each get the right `underlying`/`None`.
- [ ] [DATA] P1. **Regenerate/backfill `prod/catalog.parquet` for Prediction** after the `raw_symbol`/`base_asset`
      rollup fix (already shipped) AND the `underlying` adapter change above ship together — a full
      `build_instrument_catalogue.py --asset-group prediction` run against real GCS data, manifest-verified row counts
      (per the workspace's "plans run to actual completion on real infra" rule — no smoke-test-only claim).
- [ ] [DATA] P2. **Wire `cross_venue_mapping.build_cross_venue_mapping()` into a real, scheduled step** that runs over
      the full Kalshi + Polymarket universes (today it's a pure function with no caller in the write/rollup path) and
      persists `PredictionMarketCrossVenueMapping.canonical_event_id` onto the matched side's
      `InstrumentRecord.canonical_instrument_id` (an already-existing, currently Prediction-unused field) — either at
      adapter-write time (requires cross-adapter coordination, since each adapter only sees its own venue) or as a
      post-processing step inside `build_instrument_catalogue.py` (which already reads both venues' snapshots together
      in `build_prediction_catalogue_dataframe()` — likely the lower-friction integration point). Unmatched instruments
      keep `canonical_instrument_id=None` (honest absence, never a false pair — matches the matcher's existing design).
- [ ] [DATA] P2. **Decide + document the `titles` map source for sports fixture matching** — `cross_venue_mapping.py`'s
      sports branch needs an `instrument_key -> title` map the canonical `InstrumentRecord` doesn't carry (the `symbol`
      field was dropped from the schema); today only a caller-supplied map enables sports pairing. Identify the real
      source for this — the per-day parquet's raw title-bearing fields, or a re-derivation — before wiring todo 3 for
      the sports branch specifically.
- [ ] [DATA] P2. **Align Prediction's sports fixture key with the Sports asset group's `build_fixture_id()`** —
      `SportsFixtureKey.pairing_key()` (`unified_api_contracts/canonical/domain/predictions/fixture_parsing.py`) and
      `build_fixture_id()` (`unified_api_contracts/canonical/domain/sports/canonical_ids.py`,
      `{LEAGUE}:{HOME}_v_{AWAY}:{YYYYMMDD}`) carry the same information (league + two teams + date) via two independent
      implementations today — not guaranteed to normalize team names identically. Either (a) make `fixture_parsing.py`
      call `build_fixture_id()`'s own team-normalization registry, or (b) wire up the already- written-but-unused
      `_cross_reference_fixture()` method in `polymarket/parsing.py` (resolves a real API-Football `fixture_id`) and
      surface that resolved id on `canonical_instrument_id` for Prediction sports rows specifically — giving a
      Prediction sports market's identity byte-parity with the Sports asset group's fixture_id for the SAME real event,
      not just conceptual similarity. Concrete test: one real EPL fixture that exists in both the Sports asset group's
      fixture registry and a live Polymarket/Kalshi sports market, asserting the two resolve to the same id.
- [ ] [VERIFY] P2. **Check whether any real downstream consumer treats Prediction `instrument_id` as globally unique
      without also keying on `venue`** (carried over from the original finding-8 open question — never actually
      checked). If one exists, the `canonical_instrument_id` population in todo 3 needs to preserve per-venue uniqueness
      at the raw `instrument_id` level regardless of what `canonical_instrument_id` adds.
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
