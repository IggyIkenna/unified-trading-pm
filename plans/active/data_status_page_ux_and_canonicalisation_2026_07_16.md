---
doc_type: plan
title: Data-status page — honest-coverage fix (shipped) + UX & canonicalisation follow-ups (P1–P8)
summary:
  Eight operator issues on the instruments-service data-status page (deployment-ui + deployment-api), each
  code/live-verified via a multi-agent audit. P1 (Honest Coverage rendering only DeFi) is ROOT-CAUSED and FIXED — the
  daily writer OOM'd on an 8GB VM and wrote a silent partial coverage.json; RAM bump + writer partial-stamping + card
  banner shipped and verified live. P2–P8 are the remaining designs — new-listings/expiries + prediction catalogue
  browser + instrument-type canonicalisation (SPOT_ASSET already exists in UAC) + drilldown de-duplication + catalogue
  explorer + cefi chain-axis drift + sports league-drilldown consistency. Operator-decisions flagged inline.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, instruments-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-status,
    honest-coverage,
    deployment-ui,
    deployment-api,
    instruments,
    canonicalisation,
    prediction,
    sports,
    catalogue,
    ux,
  ]
related:
  [
    data_status_tab_and_downloads_remediation_2026_06_16.md,
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
    instruments_catalogue_incremental_rollup_2026_06_29.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 5.4
assigned_role: ui_developer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: operator request 2026-07-16 (data-status page review) + multi-agent audit workflow wf_872e8051-00a
---

# Data-status page — honest-coverage fix + UX & canonicalisation follow-ups

> **Human/LOCAL plan** (`assigned_vm: NA`) — operator-driven, not AO-dispatched. Source: operator review of
> `/service/instruments-service/data-status` on 2026-07-16 + a 16-agent audit (workflow `wf_872e8051-00a`, findings
> digest cross-checked against live code, the UAC SSOTs, and live GCS reads).

## Codex SSOTs (this plan references, does not duplicate)

- `codex/02-data/honest-coverage-model.md` — Honest Coverage v2 two-layer model (P1, P4).
- `codex/02-data/availability-manifest-and-data-status.md` + `…/honest-absence-downstream-handling.md` — manifest
  shard-atom identity + no-silent-placeholders (P1, P4, P7, P8).
- `unified-api-contracts/.../registry/data_status_axis_matrix.py` — the shard/display axis SSOT: cefi = `("venue",)`,
  defi adds `chain`; sports = `("data_type","league_id")` (P7, P8).
- `unified-api-contracts/.../_instrument_enums.py` — canonical `InstrumentType` (SPOT_PAIR/PERPETUAL/SPOT_ASSET/…) (P4).
- `instruments-service/docs/PREDICTION_INSTRUMENTS.md` — prediction catalogue + `canonical_question_group` (P3).
- `codex/06-coding-standards/ui-testing-layers.md` — the `[UI]` + `pw:L2` gate for every deployment-ui tick.

## Root-cause summary (audit findings, all code/live-verified)

| #   | Issue                                       | Verdict                                                      | Evidence anchor                                                                                                             |
| --- | ------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| P1  | Honest Coverage card = DeFi only            | **OOM on 8GB VM → silent partial coverage.json** (FIXED)     | `measure_honest_coverage._read_parquet_safe` swallows OOM; live coverage.json `asset_groups_measured` swung defi-only↔all-5 |
| P2  | New listings + upcoming expiries            | Feasible read-only from `catalog.parquet`                    | `available_from` (listing), `available_to` (expiry folded in)                                                               |
| P3  | Prediction category dropdown                | Canonical grouping already exists                            | `canonical_question_group` (stored) + `PredictionMarketCategory` (derived)                                                  |
| P4  | Non-canonical instrument types / SPOT_ASSET | Summary shows RAW manifest values; SPOT_ASSET already in UAC | `_instrument_enums.py:59`; `coverage.py` groups raw `index[axis]`                                                           |
| P5  | Hierarchical drilldown redundant            | Redundant for instruments-service only                       | `DataStatusTab.tsx:1884` vs TURBO grid `:3383+`                                                                             |
| P6  | Catalogue explorer                          | Blocks exist but scattered; no MVP filter on lists           | `_instruments.py`, `_csv_export.py`, `_mvp_scope_predicate.py`                                                              |
| P7  | CeFi chain axis (solana/zksync)             | Axis-matrix drift confirmed                                  | `data_status_axis_matrix.py` cefi=`(venue,)`; `PACIFICA-SOLANA`/`LIGHTER-ZKSYNC` `{proto}-{chain}` names                    |
| P8  | Sports league-drilldown inconsistency       | Axis-policy + real TEAMS data-correctness drift              | `SPORTS_DATA_TYPE_META`; TEAMS classed global vs per-league SSOT                                                            |

---

## Progress Log

### 2026-07-16 — P1 Honest Coverage FIXED (immediate + durable), verified live

- **Root cause (live-verified):** the Honest Coverage card is a verbatim mirror of
  `gs://central-element-323112-honest-coverage/{date}/coverage.json` (endpoint `get_honest_coverage` returns the bytes
  unchanged). The daily writer ran on an **8 GB `e2-standard-2`**; `measure_honest_coverage._read_parquet_safe` loads
  each asset-group's full availability-index parquet into pandas and **swallows exceptions → returns None**, so a
  MemoryError on the growing cefi/tradfi/sports parquets silently skips that AG. `main()` then wrote
  `asset_groups_measured = only-the-AGs-that-fit` with no error. Live proof: `asset_groups_measured` swung
  `['cefi','defi','tradfi','sports','prediction']` (07-09/07-11) → `['cefi']` (07-13) → `['defi']` (07-15/07-16).
- **Immediate fix (verified):** launched `honest-coverage-20260716-073157` on `e2-highmem-4` (32 GB) → today's
  `coverage.json` regenerated (`generated_at 2026-07-16T06:39:00Z`) with **all 5 asset groups**. VM auto-shut-down.
- Shipped:
  - `- [x]` **[INFRA] P0. ✅ Right-size the scheduled honest-coverage VM e2-standard-2 → e2-highmem-4 (32 GB)** —
    `deployment-service@9d97eb2` + Evidence: VM `honest-coverage-20260716-073157` re-measured all 5 AGs (`coverage.json`
    `asset_groups_measured=['cefi','defi','tradfi','sports','prediction']`, `generated_at 2026-07-16T06:39:00Z`).
  - `- [x]` **[DATA] P0. ✅ Writer stamps `partial`/`asset_groups_failed`/`asset_groups_requested` + logs ERROR on a
    partial run** (honest-absence — never serve a partial as complete) — `instruments-service@a29e483`.
  - `- [x]` **[UI] P0. ✅ Honest Coverage card renders an amber "coverage incomplete" banner (lists failed groups) and a
    stale banner + tinted date when the 14-day fallback serves an older file** — `deployment-ui@8ef7a95` + Evidence:
    `HonestCoverageCard.test.tsx` 8 specs green (tsc/eslint clean).

---

## P1 — Honest Coverage: remaining hardening

- [ ] [INFRA] P1. Republish the code tarballs
      (`deployment-service/scripts/vm/lib/create-code-tarballs.sh --include instruments-service deployment-service`) so
      the **nightly** cron VM runs the new writer (partial-stamping) AND launches `e2-highmem-4`; then verify tomorrow's
      00:30 UTC run writes a full 5-AG file with `partial: false`. (Today's manual run used the pre-fix tarball, so
      `partial` is absent on the 2026-07-16 file — expected.)
- [ ] [DATA] P2. Column-prune the writer read — `_read_parquet_safe` pulls all 6 columns incl. `instrument_id` (the
      memory driver). Drop `instrument_id` where the coverage compute doesn't need it (or stream row-groups via pyarrow)
      so the read stops scaling toward OOM regardless of VM RAM. Verify the `by_venue_instrument_type*` breakdowns still
      populate. _(Defence-in-depth beyond the RAM bump.)_
- [ ] [BACKEND] P3. _(stretch, optional)_ Endpoint staleness signal — `get_honest_coverage` could add
      `resolved_date`/`requested_date` so the card distinguishes "today's file" from a 14-day-fallback precisely rather
      than inferring from the payload `date`. Low priority — the card already derives staleness from `date`.

## P2 — New Listings + Upcoming Expiries (catalogue-derived, user thresholds)

- [ ] [BACKEND] P1. deployment-api service `catalogue_lifecycle.py` (mirror `upcoming_fixtures.py`) reading per-AG
      `catalog.parquet` — `list_new_listings(max_age_days, asset_group?, venue?)`
      (`available_from >= today - max_age_days`) and `list_upcoming_expiries(within_days, …)`
      (`instrument_type ∈ {FUTURE,OPTION,COMBO}` AND `available_to ∈ [today, today+within_days]`). Read-only, 5-min TTL,
      shard-isolated. Read the parquet directly (deployment-api cannot reach `list_instruments()` — no reader
      registered, T4).
- [ ] [BACKEND] P1. Routes `GET /instruments/new-listings` + `GET /instruments/upcoming-expiries` (mirror
      `routes/fixtures.py`, honour mock mode).
- [ ] [UI] P1. Two sibling cards next to `UpcomingFixtures` in `DataStatusTab.tsx` (IS-only guard) with numeric
      threshold inputs ("new if listed within N days", "expiring within M days"); mirror the fixtures card. `[UI]` +
      pw:L2 regression spec.
- [ ] [DATA] P2. _(clean long-term)_ Add a distinct `expiry` column to `CATALOG_COLUMNS` in
      `build_instrument_catalogue.py` (today expiry is folded into the 4-way `available_to`); needed to honour
      shard-atom identity and to disambiguate expiry vs delisting vs last-observed. Then a catalogue regen.
- [ ] [BACKEND] P2. New-listings false-positive guard — for legacy rows `available_from == pipeline-first-seen` (not a
      real listing date); quantify + either show provenance or exclude `available_from == pipeline-start` rows.

## P3 — Prediction markets: category dropdown → human-readable catalogue browser

- [ ] [BACKEND] P1. `read_prediction_catalogue(category?, canonical_question_group?, venue?, search?, limit, offset)`
      widening the existing `manifest_source.py` `prod/catalog.parquet` read to project
      cqg/underlying/raw_symbol/timing; return facet counts per category + per cqg.
- [ ] [BACKEND] P1. UAC facade — export `PredictionMarketCategory` + add `category_for_group(cqg)` (trivial composition
      of existing `underlying_for_group` + `_category_for_underlying`) to `unified_api_contracts.predictions` (no
      deep-path import). Route `GET /data-status/prediction-catalogue`.
- [ ] [UI] P1. Prediction "Catalogue" surface — category `<select>` (crypto/politics/sports/… with MVP badge) → cqg
      sub-filter → paginated searchable human-readable table (label = `raw_symbol` slug fallback, venue chip, resolution
      date). `[UI]` + pw:L2.
- [ ] [OPERATOR] P2. BLOCKED-OPERATOR-DECISION — human-readable label: ship v1 on the Polymarket `raw_symbol` slug, OR
      first add a `question`/`title` column to the polymarket/kalshi adapters + `CATALOG_COLUMNS` + regen (multi-hour)
      so the label is the real question text. **Recommend: slug for v1, title column as a follow-up.** Never fabricate a
      title.

## P4 — Instrument Coverage Summary: canonical labels + SPOT_ASSET

- [ ] [UI] P1. Axis-aware label fix — `BreakdownsAccordion.formatValueLabel` currently renders the `__legacy__` sentinel
      as "(legacy — pre-job_id)" for EVERY axis; make it "(legacy — pre-job_id)" only for the `job_id` axis and
      "(unlabeled)" for instrument_type/data_type. `[UI]` + pw:L2.
- [ ] [UI] P1. Display-only canonical alias map in `data-status-helpers.ts` (spot→SPOT_PAIR, perp/perpetual→PERPETUAL,
      futures→FUTURE, lending_market→LENDING, …, from the `_instrument_enums.py` docstring) applied AFTER grouping so
      the summary shows canonical labels while the query key stays raw (shard-atom identity — do NOT rewrite the
      grouping key).
- [ ] [DATA] P2. Root-cause the legacy values — grep the instruments-service catalogue/manifest writer for where
      `instrument_type` is stamped; ensure new rows emit `InstrumentType.value` (uppercase). Author a one-off legacy-row
      canonicalization migration (pattern: `scripts/canonicalize_*_2026_*.py`) for residual lowercase rows. NOTE:
      `instrument_type` is a SHARD axis for MTDS/MDPS/features — a value migration must preserve shard-atom identity
      across those services, not just IS.
- [ ] [DATA] P2. Drain residual `LENDING` — finish the A_TOKEN/DEBT_TOKEN split for MORPHO/FLUID/AAVE_PLASMA (the
      LENDING vs A_TOKEN/DEBT_TOKEN mix is canonical-but-mid-migration, not drift).
- [ ] [OPERATOR] P2. BLOCKED-OPERATOR-DECISION — SPOT_ASSET is **already** a canonical `InstrumentType`
      (`_instrument_enums.py:59`), keyed by `base_asset_contract_address` (an InstrumentRecord attribute), mapped to
      `LedgerAssetClass.SPOT_TOKEN`, with a `spot_assets` data-type family — but **no live adapter emits it**. Decision:
      which chains/tokens should emit SPOT_ASSET records (raw fungible on-chain asset → contract address for
      wallet/chain position monitoring), and is populating it in scope now? If yes → scope an instruments-service
      adapter task + surface `base_asset_contract_address` in `ShardDetailModal`.
- [ ] [OPERATOR] P3. BLOCKED-OPERATOR-DECISION — should the summary show canonical labels only, or raw value + a
      canonical badge so manifest drift stays visible for remediation?

## P5 — Remove the redundant hierarchical-drilldown button (instruments-service only)

- [ ] [UI] P1. Gate off the `LazyDrilldownDetails` at `DataStatusTab.tsx:1884` for instruments-service cefi/tradfi/defi
      (the venue→[chain]→date tree is a shallower subset of the TURBO Data Coverage grid below, which drills the same
      axes + a richer 4-tab `ShardDetailModal`). Use an **axis-comparison predicate**, NOT a blanket `serviceName` check
      — IS-sports and IS-prediction axes differ from the grid and must be kept. Keep `HierarchicalShardDrilldown`
      (load-bearing for prediction `:4111` + MTDS/features/sports). `[UI]` + pw:L2 asserting the grid renders but the
      redundant button is gone.

## P6 — Instrument catalogue explorer (per-AG list, CSV, search, MVP filter)

- [ ] [BACKEND] P1. Extend the leaf drilldown — add `mvp_only` + a per-row `is_mvp` tag to `list_instruments_for_shard`
      (call UAC `is_mvp(...)` mirroring `filter_to_mvp` semantics, reading
      `base_asset`/`league_id`/`market_group`/`source`), and add `search` + `mvp_only` to `build_csv_export` so
      "Download CSV" == the on-screen filtered view.
- [ ] [BACKEND] P2. New aggregated `GET /data-status/catalogue` (+ `.csv` twin) parameterised by pinned axes + search +
      mvp_only → de-duped instrument list with `is_mvp` + `capture_status`. Build on `read_availability_index` or ONE
      bounded single-day `_shard_prefix` walk — **do NOT introduce a new whole-corpus GCS walk** (single-walk
      discipline; review- blocking). Label the surface "captured instruments (availability-derived)", NOT "the
      catalogue" (deployment-api cannot reach the instruments-service catalogue SSOT — T4).
- [ ] [UI] P2. `InstrumentsModalStandard` — add an "MVP only" toggle (mirror `VenueCoverageTable` pills) + MVP badge per
      row + thread `mvp_only`/`search` into the CSV URL. New "Catalogue Explorer" panel driven by
      `/data-status/catalogue`. `[UI]` + pw:L2.
- [ ] [OPERATOR] P3. BLOCKED-OPERATOR-DECISION — "catalogue" vs "availability": do you want instruments that EXIST in
      the instruments-service catalogue (needs a new deployment-api→IS read path or a manifest-backed projection) or
      instruments CAPTURED on a day (availability parquets, what every current surface reads)?

## P7 — Data Coverage breakdown: CSV, "instruments breakdown" button, CeFi chain-axis drift

- [ ] [BACKEND] P1. **CeFi chain-axis drift** — the axis SSOT sets cefi = `("venue",)`, only defi adds `chain`, but the
      cefi CLOB-perp venues `PACIFICA-SOLANA` / `LIGHTER-ZKSYNC` (`{protocol}-{chain}` names) make a chain-parser derive
      `SOLANA`/`ZKSYNC` chains in the cefi breakdown. Fix: stop deriving/displaying a chain axis for cefi venues (their
      venue name is already unique); keep chain only for multi-chain DeFi protocols (Aave). Trace the exact derivation
      point (TURBO grid renderer / breakdown builder) and gate it on `asset_group == 'defi'`.
- [ ] [UI] P2. "instruments breakdown" button — confirm it is the same overlap surfaced in P5; remove or merge per the
      P5 decision so the button's meaning is unambiguous. Ensure shard-level CSV (`download-shard-csv`) is present +
      consistent across asset groups at the shard leaf.

## P8 — Sports league-drilldown consistency + TEAMS data-correctness

- [ ] [OPERATOR] P0. BLOCKED-OPERATOR-DECISION (data-correctness) — TEAMS is classed `global_trigger_date` in
      deployment-api `SPORTS_DATA_TYPE_META` + codex, but the IS writer emits **per-league** TEAMS rows AND both the UAC
      `SHARD_AXIS_MATRIX` and `gcs_paths` classify TEAMS **per-league** (a 4-way drift). The UAC shard-atom SSOT
      mandates **direction A: reclassify TEAMS → per-league** in deployment-api (read-side only, restores shard-atom
      identity). Confirm direction A vs "writer stops emitting league_id" (a much larger, SSOT-contradicting change).
- [ ] [BACKEND] P1. (on direction A) `sports_helpers.py` TEAMS axis `global_trigger_date` → `per_league_trigger_date`
      (mirrors PLAYER_VALUES); update codex `sports-data-source-coverage-matrix.md:106` to per-league; add a unit test
      asserting the TEAMS response carries `leagues`.
- [ ] [UI] P1. Honest-absence affordance — for genuinely-global data_types (LEAGUES, VENUES) render an explicit "global
      reference entity — no per-league breakdown (axis: {axis})" row instead of silently omitting the Leagues section
      (the response already carries `axis`). `[UI]` + pw:L2.
- [ ] [UI] P2. Deep-drill parity — the per-fixture breakdown + downloads are hardcoded to `name === "FIXTURES"`; either
      generalize `build_fixture_breakdown` to all `per_league_per_fixture_date` sources (non-trivial — it reads
      api-football fixture entities) behind a backend `supports_fixture_breakdown` capability flag, OR add a one-line UI
      note that per-fixture drill/download is FIXTURES-only.

---

## Operator decisions outstanding (blocking the tagged todos above)

1. **P8 / P0 — TEAMS axis direction** (data-correctness): confirm direction A (reclassify per-league). Code evidence
   points decisively at A.
2. **P4 — SPOT_ASSET adoption**: populate now (which chains/tokens emit it) or defer? And: canonical-labels-only vs
   raw+badge in the summary.
3. **P3 — prediction label**: slug for v1 (recommended) vs real question-title column first.
4. **P6 — catalogue vs availability**: which data source for the explorer.

## Full audit artefacts

Findings digest + per-agent verdicts: workflow `wf_872e8051-00a` (findings all `CONFIRMED-WITH-CORRECTIONS`; P7 agent
failed the structured-output cap but the SSOT + venue-name evidence is captured above). This plan is the durable
worklist; the transcript is ephemeral.
