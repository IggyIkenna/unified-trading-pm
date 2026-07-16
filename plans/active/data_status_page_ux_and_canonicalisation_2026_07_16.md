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
- [x] **DECIDED (operator 2026-07-16): slug for v1 + document the follow-up.** Ship v1 labels from the `raw_symbol` slug
      (e.g. `bitcoin-up-or-down-june-24-2026`) / `base_asset` (= first 50 chars of the raw `question` text for OTHER) /
      Polymarket `event_title`; derive the CATEGORY from `canonical_question_group` (the canonical thematic label —
      already a stored column + a `prediction_canonical_question_group` cluster data_type). Confirmed: the
      human-readable form is parseable from what already exists (`PREDICTION_INSTRUMENTS.md:217,230,247-266` — "all
      fields come from the real InstrumentRecord, never a title field"). Never fabricate a title.
- [ ] [DATA] P3. _(follow-up)_ Add a real `question`/`title` column to the polymarket/kalshi adapters +
      `CATALOG_COLUMNS` + a catalogue regen so the label is the true question text rather than the slug (upstream title
      exists at adapter parse time — `event_title` 100% hit for Polymarket sports — and is dropped before roll-up).

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
- [x] **DECIDED (operator 2026-07-16): POPULATE SPOT_ASSET for every distinct token leg.** Scope: one SPOT_ASSET record
      per unique (chain, token → `contract_address`) across the DeFi + spot-CeFi universe, so **every base AND quote leg
      of a `SPOT_PAIR`/`POOL` (and LST/A_TOKEN/DEBT_TOKEN underlyings) resolves to a SPOT_ASSET with a contract
      address** — the wallet/chain position-monitoring identity. Decomposed into the todos below.
- [ ] [DATA] P1. **Add address columns to the instrument catalogue (enabling step — cheap projection + regen, operator
      2026-07-16).** The addresses ALREADY exist in the per-date instruments-store parquet schema
      (`instrument.py:205-206` — `pool_address`, `pool_fee_tier`, `base_asset_contract_address`,
      `quote_asset_contract_address`, + `atoken_address`/`debt_token_address`), and the catalogue builder ALREADY
      consumes `pool_address` (DeFi POOL `instrument_id == pool_address.lower()`, `_pool_address_of`) — they are simply
      not PROJECTED into the output. Add `pool_address` (for POOLs) + `base_asset_contract_address` +
      `quote_asset_contract_address` (+ `atoken_address`/ `debt_token_address` where present) to `CATALOG_COLUMNS`
      (`build_instrument_catalogue.py:264-303`), project them from the source rows, and **regen the catalogue**. This is
      a projection change, NOT a re-fetch. Then pools resolve to their `pool_address` and spot legs to their token
      `contract_address` from a single catalogue read.
- [ ] [DATA] P1. **SPOT_ASSET backfill/migration** — with the address columns in place, derive the unique token set
      (base + quote legs of every `SPOT_PAIR`/`POOL`, + LST/A_TOKEN/DEBT_TOKEN underlyings) and emit one SPOT_ASSET
      record per unique (chain, token → `base_asset_contract_address`). Reuse the LST/A_TOKEN/DEBT_TOKEN addresses
      (confirmed fetched by the DeFi adapters — `renzo.py`/`etherfi.py`/`solend.py` set the LST token address;
      `curve.py`/ `uniswap_v2/v3.py` set base/quote). Idempotent; runs on real infra (manifest-verified rows).
- [ ] [DATA] P1. **CeFi-spot leg mapping** — a spot-CeFi asset (e.g. ETH on Binance) has no venue contract address; map
      each CeFi spot leg's symbol → native-chain canonical `contract_address` (e.g. ETH → WETH/native on ethereum) via a
      symbol→chain→address registry so CeFi SPOT_PAIR legs also resolve to a SPOT_ASSET. Flag any symbol with no
      canonical on-chain address (honest-absence — don't invent one).
- [ ] [BACKEND] P1. **Make SPOT_ASSET emission normal at discovery time** — during token-pair discovery (future
      backfills + live), also emit the per-leg SPOT_ASSET records so the dump is continuous, not a one-off migration.
- [ ] [UI] P2. Surface `base_asset_contract_address` (+ chain) in `ShardDetailModal` / the instrument drilldown for
      SPOT_ASSET rows so an operator can copy the contract address.
- [x] **DECIDED (default, operator did not override): summary shows the CANONICAL label with the raw value on hover** —
      canonical labels for readability, raw kept visible (tooltip) so manifest drift stays diagnosable. Covered by the
      P4 UI label-fix + alias-map todos above.

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
- [x] **DECIDED (operator 2026-07-16): BOTH, phased.** Phase 1 = availability-derived (the two backend/UI todos above),
      labelled "captured instruments (availability-derived)". Phase 2 (below) = the true-catalogue projection.
- [ ] [BACKEND] P3. _(phase 2)_ True-catalogue source — add a deployment-api→instruments-service read path OR a
      manifest-backed catalogue projection so the explorer can list instruments that EXIST in the catalogue (not just
      captured). Respect the T4 tier rule (integrate by contract/projection, not a direct service→service import).

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

- [x] **DECIDED (operator 2026-07-16): direction A — reclassify TEAMS → per-league.** Read-side change; matches the IS
      writer + UAC shard-atom SSOT.
- [ ] [BACKEND] P1. `sports_helpers.py` TEAMS axis `global_trigger_date` → `per_league_trigger_date` (mirrors
      PLAYER_VALUES); update codex `sports-data-source-coverage-matrix.md:106` to per-league; add a unit test asserting
      the TEAMS response carries `leagues`.
- [ ] [BACKEND] P1. **Seasonal TEAMS is accounted for by the DATE axis** (operator question 2026-07-16): the writer keys
      TEAMS as `row_key={date, data_type:TEAMS, league_id}` (`sports_reference_core.py:335`) captured on trigger dates
      (season-start + transfer windows). So each season's roster is a distinct snapshot under the same `league_id`, and
      the drilldown becomes `data_type=TEAMS → league_id → date` — per-season change surfaces as the date axis, no extra
      dimension needed. Verify the `per_league_trigger_date` branch surfaces sensible trigger dates per league in the UI
      date drilldown (e.g. one TEAMS snapshot per season boundary), and that off-season dates read as legitimately empty
      (honest-absence), not gaps.
- [ ] [UI] P1. Honest-absence affordance — for genuinely-global data_types (LEAGUES, VENUES) render an explicit "global
      reference entity — no per-league breakdown (axis: {axis})" row instead of silently omitting the Leagues section
      (the response already carries `axis`). `[UI]` + pw:L2.
- [ ] [UI] P2. Deep-drill parity — the per-fixture breakdown + downloads are hardcoded to `name === "FIXTURES"`; either
      generalize `build_fixture_breakdown` to all `per_league_per_fixture_date` sources (non-trivial — it reads
      api-football fixture entities) behind a backend `supports_fixture_breakdown` capability flag, OR add a one-line UI
      note that per-fixture drill/download is FIXTURES-only.

---

## Operator decisions — RESOLVED (2026-07-16)

1. **P8 — TEAMS axis**: ✅ direction A (reclassify per-league). Seasonal change is captured by the trigger-date axis
   under each league (verify todo added).
2. **P4 — SPOT_ASSET**: ✅ populate for every base+quote token leg across DeFi + spot-CeFi (backfill/migration + live
   discovery-time emission + CeFi symbol→chain→address mapping + verify LST/A_TOKEN/DEBT_TOKEN addresses). Summary
   labels = canonical with raw on hover.
3. **P3 — prediction label**: ✅ slug for v1 (category from `canonical_question_group`), real title column as a
   follow-up.
4. **P6 — catalogue explorer**: ✅ both, phased (availability-derived now, true-catalogue projection follow-up).

## Full audit artefacts

Findings digest + per-agent verdicts: workflow `wf_872e8051-00a` (findings all `CONFIRMED-WITH-CORRECTIONS`; P7 agent
failed the structured-output cap but the SSOT + venue-name evidence is captured above). This plan is the durable
worklist; the transcript is ephemeral.
