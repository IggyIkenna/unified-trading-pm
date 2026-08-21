---
doc_type: plan
title: Data-status page — honest-coverage fix (shipped) + UX & canonicalisation follow-ups (P1–P8)
summary:
  Eight operator issues on the instruments-service data-status page (deployment-ui + deployment-api), each
  code/live-verified via a multi-agent audit. P1 (Honest Coverage rendering only DeFi) is ROOT-CAUSED and FIXED — the
  daily writer OOM'd on an 8GB VM and wrote a silent partial coverage.json; RAM bump + writer partial-stamping + card
  banner shipped and verified live. P2–P8 are the remaining designs — new-listings/expiries + prediction catalogue
  browser + instrument-type canonicalisation (SPOT_ASSET already exists in UAC) + drilldown de-duplication + catalogue
  explorer + cefi chain-axis drift + sports league-drilldown consistency. Each point carries a self-contained design
  guide; operator decisions are all resolved.
status: complete
nature: process
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [cross-cutting]; title/summary are the
  # deployment-ui + deployment-api data-status PAGE UX itself, not the underlying data pipeline
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
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
    /plans/archive/2026_07/instruments_catalogue_incremental_rollup_2026_06_29.md,
    /plans/archive/2026_07/data_status_page_ux_and_canonicalisation_history_2026_07_24.md,
  ]
created: 2026-07-16
last_updated: "2026-08-06"
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
context_scope:
  [
    /plans/archive/2026_08/instrument_record_schema_completeness_extra_forbid_2026_07_18.md,
    /plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    unified-api-contracts/unified_api_contracts/internal/reference/instrument.py,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
---

# Data-status page — honest-coverage fix + UX & canonicalisation follow-ups

> **Human/LOCAL plan** (`assigned_vm: NA`) — operator-driven, not AO-dispatched. Source: operator review of
> `/service/instruments-service/data-status` on 2026-07-16 + a 16-agent audit (workflow `wf_872e8051-00a`, findings
> cross-checked against live code, the UAC SSOTs, and live GCS reads). **Every point below is self-contained** — read
> the point's `Design guide`, then do its `- [ ]` todos. Line numbers are 2026-07-16 anchors — always grep-confirm the
> symbol before editing (files drift).

## Codex SSOTs (this plan references, does not duplicate)

- `/codex/02-data/honest-coverage-model.md` — Honest Coverage v2 two-layer model (P1, P4).
- `/codex/02-data/availability-manifest-and-data-status.md` + `…/honest-absence-downstream-handling.md` — manifest
  shard-atom identity + no-silent-placeholders (P1, P4, P7, P8).
- `unified-api-contracts/.../registry/data_status_axis_matrix.py` — the shard/display axis SSOT: cefi = `("venue",)`,
  defi adds `chain`; sports = `("data_type","league_id")` (P5, P7, P8).
- `unified-api-contracts/.../_instrument_enums.py` — canonical `InstrumentType` (SPOT_PAIR/PERPETUAL/SPOT_ASSET/…) (P4).
- `unified-api-contracts/.../internal/reference/instrument.py` — `InstrumentRecord` address fields (P4-SPOT_ASSET).
- `instruments-service/docs/PREDICTION_INSTRUMENTS.md` — prediction catalogue + `canonical_question_group` (P3).
- `/codex/06-coding-standards/ui-testing-layers.md` — the `[UI]` + `pw:L2` gate for every deployment-ui tick.

## Root-cause summary (audit findings, all code/live-verified)

| #   | Issue                                       | Verdict                                                      | Where it lives                                                                          |
| --- | ------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| P1  | Honest Coverage card = DeFi only            | **OOM on 8GB VM → silent partial coverage.json** (FIXED)     | `measure_honest_coverage.py` writer; `_live_coverage.py` endpoint; `HonestCoverageCard` |
| P2  | New listings + upcoming expiries            | Feasible read-only from `catalog.parquet`                    | deployment-api `catalogue_lifecycle` (new) + deployment-ui cards                        |
| P3  | Prediction category dropdown                | Canonical grouping already exists                            | `canonical_question_group` + `PredictionMarketCategory` + a new catalogue browser       |
| P4  | Non-canonical instrument types / SPOT_ASSET | Summary shows RAW manifest values; SPOT_ASSET already in UAC | deployment-ui labels + instruments-service catalogue/SPOT_ASSET population              |
| P5  | Hierarchical drilldown redundant            | Redundant for instruments-service only                       | `DataStatusTab.tsx` (gate one drilldown off for IS)                                     |
| P6  | Catalogue explorer                          | Blocks exist but scattered; no MVP filter on lists           | deployment-api `_instruments.py`/`_csv_export.py` + a new catalogue surface             |
| P7  | CeFi chain axis (solana/zksync)             | Axis-matrix drift confirmed                                  | deployment-api/ui chain-derivation gated on `asset_group=='defi'`                       |
| P8  | Sports league-drilldown inconsistency       | Axis-policy + real TEAMS data-correctness drift              | deployment-api `sports_helpers.py` (reclassify TEAMS) + UI affordance                   |

---

## Execution guide (next agent — READ FIRST)

**Repos + how to run quality gates (QG-green tree is the commit contract):**

- Python repos (`deployment-api`, `instruments-service`, `unified-api-contracts`, `deployment-service`): from the repo
  root, `bash scripts/quality-gates.sh` (full) or `bash scripts/quality-gates.sh --no-fix` when committing only your own
  named files. **Never run `pytest` directly.** No `os.getenv()` / `Any` / `# type: ignore` / inline `gs://` / direct
  `google.cloud`/`boto3`; UTC datetimes; UAC types via `unified_api_contracts.{domain}` (no deep paths).
- `deployment-ui` (React/TS, **no Python tooling**): `npx tsc --noEmit`, `npx eslint <files>`, `npx vitest run <spec>`,
  and the **`[UI]` + `pw:L2` gate** — every UI tick needs a cited Playwright/Vitest regression spec
  (`/codex/06-coding-standards/ui-testing-layers.md`). Prettier `.ts/.tsx/.json/.css` before commit.

**Shipping each unit (commit-push-flip in the SAME turn — HARD RULE):**

1. `git status && git diff --cached --stat` (NO path arg) → stage ONLY your files by name (never `git add -A`).
2. Ship code via `bash scripts/quickmerge.sh "<conventional msg>" --agent --files '<paths>'` (lands on
   `live-defi-rollout`, runs the gates). This repo's branch is busy — if quickmerge/commit is blocked by the
   branch-drift hook, `git pull --rebase --autostash origin live-defi-rollout` then retry.
3. In the same turn, flip this plan's checkbox: `- [x] N. ✅ [TAG] … — <repo>@<sha> + Evidence: <test/run>`, and commit
   the plan with the `docs(plans):` prefix. A done claim MUST cite `<repo>@<sha>` + a resolving test/build.

**Recommended order** (points are independent; this front-loads confidence):

1. **Quick wins (no new data, high confidence):** P7 (cefi chain gate) → P5 (drilldown gate) → P4-A (UI label
   normalization). Each is a small, localized change with a pw:L2 spec.
2. **P1 remaining** (deploy the nightly path so the fix is permanent) — small INFRA + a defence-in-depth DATA todo.
3. **P4-B catalogue address columns → SPOT_ASSET** (the enabling projection+regen, then the backfill).
4. **P2** (new-listings/expiries cards) → **P8** (TEAMS reclassify + affordance) → **P3** (prediction browser) → **P6**
   (catalogue explorer).

**Golden rules for this plan specifically:**

- **Shard-atom identity** — never rewrite a manifest grouping/query KEY to make a label prettier (P4). Fix labels at the
  DISPLAY layer, or fix the WRITER + a migration; the query value the UI sends back must stay the raw manifest value.
- **Single-walk discipline** — any NEW whole-corpus GCS walk is review-blocking (P2, P6). Build on
  `read_availability_index` or ONE bounded single-day `_shard_prefix` walk with a `max_results` cap.
- **Honest-absence** — never fabricate a value to fill a gap (P3 titles, P4 CeFi addresses, P8 global entities). A blank
  / slug / explicit "no per-league breakdown" affordance is the honest answer.
- **Trace-first, don't guess** — where a todo says "trace the derivation point" (P7) or "find the predicate" (P5), grep
  then READ the candidate before editing; the audit did not pin every exact line.

---

## Progress Log

> **History extracted 2026-07-24 (two passes).** Pass 1 moved 2 dated Progress Log entries (2026-07-17 P2/P3
> remaining-work session + Playwright re-verification) to
> `/plans/archive/2026_07/data_status_page_ux_and_canonicalisation_history_2026_07_24.md`. Pass 2 (same date, line-cap
> remediation — this plan was 1971L against its enforced 1000L non-umbrella cap) moved the FULL remaining Progress Log +
> the stale "Deferred / remaining work" tracking table + every already-shipped (`- [x]`) checkbox's evidence body across
> P1-P10 to the SAME history file, verbatim. The remaining content was dense active-work narrative, not
> coordinator-shaped, so `umbrella: true` was not the right fix (see `scripts/plan-hygiene/check_line_caps.sh`'s own doc
> comment on that exemption). What stays here: every P-point's Design Guide + Acceptance criteria (still-relevant
> reference for future work on this page), the one genuinely still-OPEN checkbox (P3's `extra='forbid'` todo), and the
> CURRENT-as-of-2026-07-18 "Deferred work after 2026-07-18" table at the end of this file. See the history file for the
> full session-by-session narrative and every shipped item's real-infra evidence (commit SHAs, GCS row counts, rollback
> snapshots, unit-test names).

### 2026-07-27 (slot-8, review) — tradfi native-extract todo 6: canonical ids + venue-lookup gap re-verify

Re-verified per `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md` todo 6 (catalogue Surface A
migration landed live 2026-07-25, `instruments-service@52d8b3ef`, un-blocking this check — the parent closeout's digest
table saying "NOT yet executed" is stale).

**Upcoming Expiries widget — canonical ids confirmed live, not stale.** Called
`deployment_api.services.catalogue_lifecycle.list_upcoming_expiries_page` (the exact function the widget/catalogue view
uses) scoped to `asset_group="tradfi"`, `within_days=365`: 149,957 matching rows. Every sampled `instrument_id` (25 rows
across two windows) is fully canonical, e.g. `CME:OPTION:SP500-USD@LIN-20260717-100-P`,
`CME:OPTION:BTC-USD@LIN-20260723-560-C` — the raw wire symbol (e.g. `E4AN6 C10100`) only appears in the separate
`raw_symbol` field, never surfaced as the id. No `E3AN6     C7960`-style raw output found in the sample.

**Venue-lookup gap fix
(`plans/archive/issues/deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md`) — confirmed still
holds for tradfi.** Live-called `DataQueryService()._venue_to_category()` for CME/NYSE/NASDAQ/CBOE/ICE: all 5 resolve to
`TRADFI` via the canonical UAC `VENUE_TO_ASSET_GROUP` registry lookup, matching `VENUE_TO_ASSET_GROUP.get(venue)`
directly (not a reverted hardcoded allowlist). Confirmed genuinely registry-backed — not coincidentally still working
off the old hardcode — by also querying two venues NEVER in the old hardcoded 5-venue tradfi allowlist (`XCBF`, `BATS`,
both correctly resolve `None` — not yet UAC-registered venues) and one cefi venue (`ASTER` → correctly resolves `CEFI`),
proving the lookup is generic/registry-driven across asset groups. Fix holds.

Verified against `deployment-api@c19edcc` (fresh-pulled to `origin/live-defi-rollout` before checking); read-only
verification, no code changed. Source: `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`
todo 6.

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries) -- this doc's every P-section
  now reads shipped except P3's dedup pointer, so swapped the stale downloads-remediation ancestor +
  PREDICTION_INSTRUMENTS.md for `instrument_record_schema_completeness_extra_forbid_2026_07_18.md`, the plan that
  actually now owns the doc's one live remaining item (`InstrumentRecord extra='forbid'`) and was missing from the prior
  list entirely.

## P1 — Honest Coverage: remaining hardening

**Design guide.** The user-facing bug is already fixed and verified (Progress Log). What remains: (a) make the fix
_permanent for the nightly cron_, and (b) defence-in-depth so a future OOM can't recur.

- _Nightly path:_ today's fix was a manual VM run on the new `e2-highmem-4` launcher, but the **scheduled** cron
  (`honest-coverage-daily`, 00:30 UTC → `launch-honest-coverage-vm.sh` → a code tarball in
  `gs://deployment-scripts-central-element-323112/`) uses whatever tarball is published. The RAM bump + the writer
  partial-stamping only reach the nightly run once the tarballs are republished.
- _Memory driver:_ `measure_honest_coverage._read_parquet_safe`
  (`instruments-service/scripts/measure_honest_coverage.py` ~226) reads `_READ_COLUMNS` = all 6 incl. `instrument_id`
  (the high-cardinality column). Dropping `instrument_id` where the coverage math doesn't need it removes the OOM cliff
  entirely.
- _Endpoint:_ `get_honest_coverage` (`deployment-api/deployment_api/routes/data_status/_live_coverage.py:598-683`) walks
  back up to 14 days and returns the file verbatim; the card infers staleness from the payload `date`.
- **Acceptance:** tomorrow's 00:30 UTC file has `asset_groups_measured` = all 5 AND `partial: false`
  (`gcloud storage cat gs://central-element-323112-honest-coverage/<YYYY-MM-DD>/coverage.json`).

**Status: ✅ all 4 checkboxes above shipped** — full evidence (commit SHAs, real-infra verification, rollback snapshots)
moved verbatim to `/plans/archive/2026_07/data_status_page_ux_and_canonicalisation_history_2026_07_24.md` § "P1 — Honest
Coverage: remaining hardening — completed checkbox evidence".

## P2 — New Listings + Upcoming Expiries (catalogue-derived, user thresholds)

**Design guide.** Today the IS data-status page has exactly one forward-looking panel, **"Upcoming fixtures"**, which is
the exact pattern to clone (it already has a threshold input).

- _Existing pattern (mirror this end-to-end):_ route `deployment-api/deployment_api/routes/fixtures.py:15-24`
  (`GET /fixtures/upcoming?days=<1..31>&league_id=` — `days` is already a `Query(7, ge=1, le=31)`); service
  `deployment-api/deployment_api/services/upcoming_fixtures.py` (per-day window read, 5-min TTL cache, shard-isolated,
  TypedDict return); UI `deployment-ui/src/components/UpcomingFixtures.tsx:74-152` (Card + clamped numeric input +
  refetch-on-change); client `deployment-ui/src/api/client.ts:944-959`; mount point `DataStatusTab.tsx:1741` under the
  `serviceName === "instruments-service"` guard.
- _Data source:_ per-AG lifecycle catalogue `gs://instruments-store-{ag}-{env}-{pid}/{env}/catalog.parquet`
  (`instruments-service/scripts/build_instrument_catalogue.py`). Columns: `available_from` = listing date
  (MIN(first-observed, venue-declared)); `available_to` = a **4-way** value (delisted_at / expiry / None-if-active /
  last-observed — `build_instrument_catalogue.py:1034-1041`). Read the parquet DIRECTLY (deployment-api cannot call
  `list_instruments()` — no reader registered, T4). Bucket resolve via
  `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group=ag)` (prediction:
  `kind="instruments-store-prediction"`).
- _The load-bearing rule:_ **Upcoming Expiries MUST filter `instrument_type ∈ {FUTURE, OPTION, COMBO}` AND
  `available_to ∈ [today, today+within_days]`.** Because delistings + last-observed values are always ≤ today, the
  forward window admits only genuine future expiries — the type filter + forward window together make it correct even
  though `available_to` is overloaded.
- **Acceptance:** two endpoints honour mock mode; two cards with numeric threshold inputs render next to Upcoming
  fixtures; a pw:L2 spec drives a threshold change and asserts the list refetches.

**Status: ✅ all 5 checkboxes above shipped** — full evidence moved verbatim to the history file § "P2 — New Listings +
Upcoming Expiries — completed checkbox evidence".

## P3 — Prediction markets: category dropdown → human-readable catalogue browser

**Design guide.** Prediction is fully onboarded (venues `POLYMARKET`+`KALSHI`, `InstrumentType.PREDICTION_MARKET`); the
canonical grouping already exists. Build a browse-the-live-catalogue surface, decided to ship on the slug for v1.

- _Grouping (already canonical, already stored):_ `canonical_question_group` (cqg) is a manifest column + the prediction
  shard axis (`deployment-api/deployment_api/services/data_status_hierarchical.py:16,367-401`; projected in
  `manifest_source.py:84,92`). The coarse category = `PredictionMarketCategory`
  (`unified-api-contracts/.../canonical/domain/prediction/prediction_mapping.py:23`, values crypto/politics/sports/…) —
  **NOT facade-exported today.** `underlying_for_group(cqg)` + `_category_for_underlying(...)` already exist
  (`.../predictions/cross_venue_mapping.py:279-328`), so `category_for_group(cqg)` is a 2-line composition.
- _Live source:_ `prod/catalog.parquet` in `instruments-store-pred-{env}-{pid}` (deployment-api already reads it for the
  unique-count at `manifest_source.py:216-222`, projecting only `instrument_id` — just widen the `columns=`).
- _Label (v1, honest fallback):_ `raw_symbol` slug (e.g. `bitcoin-up-or-down-june-24-2026`) → `base_asset` (first 50
  chars of the raw question for OTHER) → Polymarket `event_title` → `instrument_id`. **Never fabricate a title.** Data
  caveat: `prod/catalog.parquet` may hold NaN `raw_symbol`/`base_asset` until a regen
  (`PREDICTION_INSTRUMENTS.md:324-326`) — the fallback chain handles it.
- **Acceptance:** category `<select>` → cqg sub-filter → a paginated, searchable table of human-readable markets with
  venue chip + resolution/close date; pw:L2 asserts category change narrows the list.

**Status: ✅ 5 of 6 checkboxes shipped** — full evidence moved verbatim to the history file § "P3 — Prediction markets
catalogue browser — completed checkbox evidence". The still-open todo (the `InstrumentRecord extra='forbid'`
side-discovery) stays below, unmoved.

- [x] ✅ [DATA] P3. **DEDUPED 2026-08-02 — resolved-by-reference, not by completion.** This finding already has its own
      proper home: `/plans/archive/2026_08/instrument_record_schema_completeness_extra_forbid_2026_07_18.md` (filed the same day,
      same operator ruling) tracks the actual `extra='forbid'` + workspace-grep + prediction-title remediation work end
      to end (currently 4 open todos there). Closing the duplicate pointer here to stop double-bookkeeping the same
      finding in two docs — see that plan for live status, not this one. DECIDED (operator 2026-07-18: extra='forbid' +
      workspace-grep callers + fix the discarded prediction title). _(NEW — side-discovery 2026-07-17, adversarial
      review of the `question`/`title` todo)_ **`InstrumentRecord` silently swallows unknown kwargs — real data has been
      discarded on every prediction capture with zero signal.** Both prediction adapters pass a `symbol=` kwarg that
      `InstrumentRecord` does not declare; pydantic `extra='ignore'` drops it silently. Kalshi's value is
      `str(title)[:100]` — **the human-readable title the `question`/`title` todo above wants has been arriving and
      being thrown away on every capture**, for an unknown duration, with no warning, no log, no test failure. Two
      actions: (1) decide whether `InstrumentRecord` should use `extra='forbid'` (a silent-drop of a field a caller
      believed it was persisting is the same honest-absence violation class as a fabricated value — it makes the record
      lie by omission); (2) **workspace-wide grep for other `InstrumentRecord(...)` callers passing undeclared kwargs**
      — if prediction has been doing this unnoticed, other asset groups plausibly are too, and the blast radius is
      "fields we think we capture but don't".

## P4 — Instrument Coverage Summary: canonical labels (A) + SPOT_ASSET population (B)

**Design guide.** Two INDEPENDENT workstreams. (A) is a small display fix; (B) is a data/backfill effort. Do (A) as a
quick win; (B) after the catalogue-address enabler.

**(A) Canonical labels.** The "Instrument Coverage Summary" is manifest-derived and shows RAW string values with no UAC
normalization: `coverage.py:_build_breakdowns` / `_build_latest_day_breakdown` group
`index[axis].fillna("").astype(str)` (~223-293), a blank → the `"__legacy__"` sentinel (`coverage.py:227,240`), and
`BreakdownsAccordion.tsx:84` `formatValueLabel` renders `__legacy__` → "(legacy — pre-job_id)" for EVERY axis (wrong on
instrument_type/data_type; it only means pre-job_id on the `job_id` axis). The canonical enum is
`_instrument_enums.py:17-82` (UPPERCASE SPOT_PAIR/PERPETUAL/… with a legacy→canonical map in the docstring lines 24-27).
**DO NOT rewrite the manifest grouping key** — `DataStatusTab.tsx:1863-1870` sends `{axis,value}` back verbatim as a
secondary-axis manifest query (shard-atom identity). Fix at the DISPLAY layer, raw value kept on hover. NOTE: the DeFi
type mix (LENDING vs A_TOKEN/DEBT_TOKEN, STAKING/YIELD_BEARING/LST) is CANONICAL-but-mid-migration — do not "fix" it;
only drain residual LENDING.

**(B) SPOT_ASSET population** (operator-approved). `SPOT_ASSET` is ALREADY a canonical type (`_instrument_enums.py:59`),
mapped to `LedgerAssetClass.SPOT_TOKEN`, with a `spot_assets` data-type family, and `InstrumentRecord` already carries
the address fields (`instrument.py`: `pool_address:213`, `base_asset_contract_address:221`,
`quote_asset_contract_address:225`, `atoken_address:235`, `debt_token_address:239`; validator 325-390 requires
`pool_address` OR `base_asset_contract_address` for on-chain types) — but **no live adapter emits SPOT_ASSET yet**. The
addresses already exist in the per-date parquet schema (`instrument.py:205-206`) and the catalogue builder already reads
`pool_address` (`build_instrument_catalogue.py` `_pool_address_of`; DeFi POOL `instrument_id == pool_address.lower()`);
they're just not projected into `CATALOG_COLUMNS` (`build_instrument_catalogue.py:264-303`). So the enabler is a
**projection + regen, not a re-fetch**. Goal: one SPOT_ASSET per unique (chain, token → contract_address) so every base
AND quote leg of a SPOT_PAIR/POOL (and LST/A_TOKEN/DEBT_TOKEN underlyings) resolves to a copy-pastable contract address.

- **Acceptance (A):** the summary shows canonical UPPERCASE labels / "(unlabeled)" for blank type/data_type; "(legacy —
  pre-job_id)" appears ONLY on the job_id axis; raw value visible on hover; the manifest query still works (key
  unchanged); pw:L2 spec on `BreakdownsAccordion`.
- **Acceptance (B):** `catalog.parquet` carries `pool_address` + `base_asset_contract_address` +
  `quote_asset_contract_address`; SPOT_ASSET records exist for every distinct DeFi + spot-CeFi token leg with an address
  (verified row counts on real infra); UI can show + copy the contract address; discovery-time emission keeps it
  current.

**Status: ✅ all 15 checkboxes above (A + B) shipped** — full evidence moved verbatim to the history file § "P4 —
Instrument Coverage Summary: canonical labels (A) + SPOT_ASSET population (B) — completed checkbox evidence".

## P5 — Remove the redundant hierarchical-drilldown button (instruments-service only)

**Design guide.** `DataStatusTab.tsx:1884` renders `LazyDrilldownDetails` → `HierarchicalShardDrilldown` inside each
asset-group box of the Instrument Coverage Summary, for every service. For **instruments-service** the axes collapse to
`venue → [chain] → date` (`data_status_axis_matrix.py:63-70`) — a strict, shallower SUBSET of the TURBO "Data Coverage"
grid right below it (`DataStatusTab.tsx:3383+`, which drills the same axes and opens a richer 4-tab `ShardDetailModal`).
The two features that would make the tree non-redundant (per-instrument_id load-more; per-leaf pipeline_mode/source
provenance) don't fire for IS (single-source venue-level reference data). **Keep the component** — it's the primary
drilldown for prediction (`DataStatusTab.tsx:4111`) + MTDS/features/sports.

- _Gotcha:_ do NOT gate on a blanket `serviceName !== "instruments-service"` — the `:1884` drilldown also renders for
  IS-sports and IS-prediction, whose axes the grid does NOT cover. Use an **axis-comparison predicate** (compare the
  pair's hierarchical axes vs what the grid already expands) so only IS cefi/tradfi/defi are suppressed.
- **Acceptance:** on the IS page the Data Coverage grid renders but the redundant Instrument-Coverage-Summary drilldown
  button is gone for cefi/tradfi/defi; prediction (`:4111`) + sports drilldowns intact; other services unchanged. pw:L2.

- [x] [UI] P1. ✅ Gated the `:1884` `LazyDrilldownDetails` behind the axis-comparison predicate
      `isHierarchicalDrilldownRedundant(service, assetGroup, shardAxisMatrix)` — suppresses the drilldown ONLY for
      instruments-service asset groups whose shard axes ⊆ `{venue, chain}` (cefi/tradfi/defi); IS sports (`league_id`) +
      prediction (`canonical_question_group`) + every other service keep it. Predicate is a pure helper in
      `data-status-helpers.ts` (testable in isolation; `HierarchicalShardDrilldown.tsx` + `LazyDrilldownDetails`
      untouched). — deployment-ui@953fa81 + Evidence: `data-status-helpers.test.ts` 5 specs green
      (cefi/tradfi/defi→true, sports/prediction/MTDS→false, case-insensitive, fail-open) + full UI QG green
      (tsc/eslint/vitest 87/build). `[UI]` + pw:L2 (Vitest regression spec). _(Minor file-scope note: the pure predicate
      lives in `data-status-helpers.ts` rather than inline in `DataStatusTab.tsx` — the plan's "DataStatusTab.tsx only"
      note was to keep `HierarchicalShardDrilldown`/`LazyDrilldownDetails` untouched, which holds; a pure exported
      helper is far more testable.)_

## P6 — Instrument catalogue explorer (per-AG list, CSV, search, MVP filter)

**Design guide.** The building blocks exist but don't compose, and the MVP filter is only on the coverage grid.

- _What exists:_ per-AG drill `GET /data-status/drilldown/{service}/{ag}` (`_deploy_turbo.py:59`); instrument LIST only
  at the deepest leaf (`list_instruments_for_shard`, `_instruments.py:357` — single day + full tuple); CSV at leaf
  (`build_csv_export`, `_csv_export.py:133`) + per-venue bundle (`_csv_export.py:345`); leaf search
  (`_apply_search_and_pagination`, `_instruments.py:272`, caps `DEFAULT=50/MAX=500/SEARCH=100` at `:243-247`); cross-AG
  search `GET /data-status/instruments/search` (`data_query_service.py:283`). `get_instruments_list`
  (`data_query_service.py:192`) is effectively stale (its `{venue}/{folder}/` prefix mismatches the live
  `instrument_availability/by_date/day=/venue=/` layout — `_instruments.py:64-86`).
- _MVP:_ `is_mvp(asset_group, venue, instrument_type, data_type, *, base_asset, league_id, market_group, source)`
  (`_mvp_scope_predicate.py:229`) + `filter_to_mvp` (`_coverage_scope.py:72-114`) power the grid's `scope=mvp` toggle
  ONLY (`VenueCoverageTable.tsx`, default 'mvp'); the LIST + CSV paths never call it.
- _Decision:_ BOTH, phased. Phase 1 = availability-derived; Phase 2 = a true-catalogue projection.
- _Gotchas:_ **single-walk discipline** — build the new `/catalogue` on `read_availability_index` or ONE bounded
  single-day `_shard_prefix` walk (`_collect_parquet_files`, `max_results` cap); NO whole-corpus walk. **Label it
  "captured instruments (availability-derived)", NOT "the catalogue"** — deployment-api cannot reach the IS
  `InstrumentCatalogReader` SSOT (T4).
- **Acceptance:** an MVP-only toggle + per-row is_mvp badge on the instrument list; "Download CSV" == the on-screen
  filtered (search+mvp) view; a per-AG explorer lists instruments with id-substring search + MVP filter + CSV. pw:L2.

**Status: ✅ all 4 phase-1 checkboxes above shipped** — full evidence moved verbatim to the history file § "P6 —
Instrument catalogue explorer — completed checkbox evidence (phase 1)".

> **Phase-2 open todo moved to a child plan (2026-07-24, plan line-cap remediation).** The still-open P3 phase-2
> true-catalogue-source todo — including the full prototyped-and-deliberately-reverted design investigation (the
> identity-catalogue shortcut, the "not the true catalogue" realisation, the T4-safe published-projection direction, the
> prediction `_dedupe_latest` prerequisite, and the perf constraint) — was forked out **verbatim** into
> `/plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md`. See that child plan for the full open-todo
> text and current status; the shipped Phase-1 history above (design guide, what exists, the MVP predicate, the phase-1
> commits) is the durable record and stays here.

## P7 — Data Coverage breakdown: CeFi chain-axis drift + "instruments breakdown" button

**Design guide.** Confirmed against the SSOT: the shard/display axis for cefi is `("venue",)` and only defi adds `chain`
(`data_status_axis_matrix.py:67-69`). But the cefi CLOB-perp venues `PACIFICA-SOLANA` and `LIGHTER-ZKSYNC`
(`unified-api-contracts/.../registry/venue_constants.py:445-447`) use the DeFi-style `{PROTOCOL}-{CHAIN}` naming, so a
chain-deriving parser (splitting the venue name on `-`) manufactures `SOLANA`/`ZKSYNC` chains in the cefi breakdown.
Those venues are already unique by name — cefi must not be chain-keyed; only multi-chain DeFi protocols (Aave deployed
across chains) need the chain axis.

- _TRACE-FIRST (not pinned by the audit):_ grep the TURBO grid renderer + breakdown builder for where a `chain` is
  derived from the venue string (likely a `split("-")` / `rsplit`), then gate that derivation on `asset_group == 'defi'`
  so cefi renders venue-only. Confirm the fix in both the backend breakdown and the UI grid.
- _"instruments breakdown" button:_ this overlaps the P5 redundancy — resolve it with the same decision (remove/merge)
  so its meaning is unambiguous.
- **Acceptance:** the CeFi breakdown shows venues only (no `solana`/`zksync` chain sub-rows); DeFi still shows chains;
  shard-level CSV (`download-shard-csv`) present + consistent across AGs; the "instruments breakdown" button is
  removed/merged. pw:L2.

**Status: ✅ all 3 checkboxes above shipped** — full evidence moved verbatim to the history file § "P7 — Data Coverage
breakdown: CeFi chain-axis drift — completed checkbox evidence".

## P8 — Sports league-drilldown consistency + TEAMS data-correctness

**Design guide.** Drillability is set per `data_type` by the `axis` in `SPORTS_DATA_TYPE_META`
(`deployment-api/deployment_api/services/data_status/sports_helpers.py:77-219`): `per_league` → the response carries a
`leagues` map → the UI's `hasLeagues` gate (`DataStatusTab.tsx:4288,5279`) renders a league drilldown; `global` →
`per_league: None` → no league section at all. So some sources drill by league and some don't. Separately, the deeper
per-fixture drill + downloads are hardcoded to `name === "FIXTURES"`
(`DataStatusTab.tsx:5285,5385,5393,5433,5440,5462`).

- _TEAMS data-correctness drift (decided → direction A):_ TEAMS is classed `global_trigger_date` in
  `sports_helpers.py:139` + codex, but the IS writer emits **per-league** TEAMS rows (`sports_reference_core.py:293,335`
  — `row_key={date, data_type:'TEAMS', league_id}`) AND both the UAC `SHARD_AXIS_MATRIX`
  (`data_status_axis_matrix.py:70`) and `gcs_paths.py:127` classify TEAMS per-league — a 4-way drift. Fix: flip the
  TEAMS axis to `per_league_trigger_date` (the branch at `sports_helpers.py:582-625` already works for PLAYER_VALUES,
  which shares TEAMS' trigger-date cadence), a read-side change that RESTORES shard-atom identity.
- _Seasonal TEAMS is handled by the DATE axis:_ TEAMS is captured on trigger dates (season-start + transfer windows)
  keyed by `(date, league_id)`, so each season's roster is a distinct snapshot under the same league — the drilldown
  `TEAMS → league_id → date` surfaces per-season change as the date axis; no extra dimension.
- **Acceptance:** TEAMS is league-drillable and consistent with STANDINGS; genuinely-global data_types (LEAGUES, VENUES)
  show an explicit "global reference entity" affordance instead of a silent gap; off-season dates read as legitimately
  empty. Unit test asserts the TEAMS response carries `leagues`. pw:L2 for the UI affordance.

**Status: ✅ all 5 checkboxes above shipped** — full evidence moved verbatim to the history file § "P8 — Sports
league-drilldown consistency + TEAMS data-correctness — completed checkbox evidence".

---

## P9 — Operator review round 2 (2026-07-16 pm) — data-status deep-dive + reconciliation

> Operator re-reviewed the live (prod-deployed, PRE the P1–P8 fixes) data-status page. Findings validated against REAL
> GCS via a local full-stack run (deployment-api on real GCS + deployment-ui + Playwright). Each tagged
> **fixed-not-shipped** (fixed in LDR, awaiting promote/deploy), **fixed-now** (shipped this round), or **not-fixed**
> (new finding → todo below).

**Reconciliation — instrument_type + data_type per AG (REAL data, coverage-summary breakdowns):**

| AG         | instrument_type (unique-id counts)                                                                                                       | data_type                                                             | Verdict                                                                                                                                                                             |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI       | SPOT_PAIR, PERPETUAL, COMBO, FUTURE, OPTION (canonical) **+ `perpetual` 1.15M, `spot` 502k (LEGACY dupes)** + `__legacy__` 4.85M (blank) | `instruments` (+ `__legacy__` 284)                                    | P4-A canonicalises the DISPLAY (fixed-not-shipped); DATA dupes need the migration (P4 DATA P2).                                                                                     |
| TRADFI     | (pre-fix) `__legacy__` 46.5M (blank — 98% of rows!) + OPTION/COMBO/SPOT_PAIR/EQUITY/FUTURE/ETF/INDEX                                     | `instruments`                                                         | **✅ fixed 2026-07-16**: instruments-service@66258618 — writer was already fixed pre-mission; migration backfilled the 15,017 blank manifest rows (0 `captured` rows remain blank). |
| DEFI       | POOL, LENDING, STAKING, YIELD_BEARING, A_TOKEN, DEBT_TOKEN, PERPETUAL, SPOT_PAIR, LST (canonical) + `__legacy__` 3.85M                   | **TWO: `instrument-catalog` 8.45M + `instruments` 3.03M**             | **not-fixed**: two data_types — root-cause (a `backfill_defi_catalog_data_type_2026_06_21` migration left churn).                                                                   |
| SPORTS     | (source axis) — see below                                                                                                                | —                                                                     | **not-fixed**: invalid `source` values.                                                                                                                                             |
| PREDICTION | PREDICTION_MARKET                                                                                                                        | `prediction_canonical_question_group` + `prediction_market_lifecycle` | Two prediction GRAINS (cqg bundle + per-market lifecycle) — likely legit; confirm.                                                                                                  |

**Status: ✅ all 8 checkboxes (Q1-Q4) above shipped** — full evidence moved verbatim to the history file § "P9 —
Operator review round 2 — Q1-Q4 completed checkbox evidence".

### P9 — cross-agent verification (2026-07-16 pm, other agents' P3/P6 work)

P3 (prediction browser: deployment-api@9238983 + deployment-ui@3bdb4e4 + uac@72fd959) and P6 phase-1 (catalogue
explorer: deployment-api@abcce0b + @1e3c7b4) are **committed, on LDR, CI-green (`quality-gates-v2` success), plan todos
flipped with evidence, and code is real** (not stubs) — the shipping process was followed correctly. TWO gaps found on a
local real-GCS run (worth confirming — same "CI-green-with-mocks but slow/empty on real data" class as the Q1 symbol
search):

**Status: ✅ all 5 checkboxes above shipped** — full evidence moved verbatim to the history file § "P9 — cross-agent
verification (2026-07-16 pm, other agents' P3/P6 work) — completed checkbox evidence".

---

## P10 — Sports fixtures browser: filter by date / league / team (operator round 3, 2026-07-17)

> Operator: _"for catalogue sports should have all the fixtures broken down by searching by date, league and/or team for
> filtering"_. The P9 fixtures browser shipped league→day grouping with a `league_id` filter over a **today-relative**
> window only — so team search did not exist and no historical date was addressable (`days_back` caps at 60).

**Status: ✅ both checkboxes above shipped** — full evidence moved verbatim to the history file § "P10 — Sports fixtures
browser: filter by date / league / team — completed checkbox evidence".

> **Scope note (SUPERSEDED 2026-07-17 by P10-B below — kept for provenance):** the day-walk reader bounded "all the
> fixtures" to a ≤120-day window. Operator asked whether a single rolled-up fixtures parquet existed (like the
> instruments catalogue); it does, and P10-B replaces the day-walk with it.

### P10-B — single-file fixtures source + full-history catalogue (operator round-3 cont., 2026-07-17)

> Operator: _"is there a single fixtures parquet like we have the instruments catalogue which rollups daily so we can
> pull from a single file rather than aggregating across day files?"_ → **Yes**:
> `instruments-store-sports-prd/prod/catalog.parquet` (~440KB, ONE GET) already carried a fixture-grain row per fixture,
> keyed by date + league + teams. It lacked only kickoff/status. Operator chose: **extend the builder** (option C) over
> a hybrid or a lossy switch. Then: _"make it full"_ + _"lets get to 134k in the catalogue or whatever it should be and
> then fetch all the round"_.

**Corrections the operator forced (both mine, both wrong before they pushed):**

1. I claimed the single file was "all the fixtures". It was **~13 months**. Operator: _"only 17k fixtures since 2020 are
   you sure about that"_ — correct. 17,064 = **exactly ONE season** across 89 leagues, because the FTP roll-up windowed
   to `SPORTS_FTP_WINDOW_DAYS=400`. Raw is complete **2019→2026** (verified every year on real GCS). The capture was
   never missing fixtures — per-league counts are exact (EPL=380, LA_LIGA=380, SERIE_A=380, BUNDESLIGA=308≈306,
   ENG_CHAMPIONSHIP=558≈552). Their 500k estimate assumed 380/league; real median is **149** (many of the 89 are
   cups/knockouts), so the true 8-season target is **~136k**.
2. I triaged `round` as a cosmetic blank. Operator: _"what is round is that used to separate relegation games etc"_ —
   correct, and it reframed the whole thing: `round` is the SOLE input to `classify_competition_phase` ("critical for ML
   training data filtering"), so this is an **ML data-correctness bug**, not a display nit. → own issue doc.

**Status: ✅ all 3 checkboxes above shipped** — full evidence moved verbatim to the history file § "P10-B — single-file
fixtures source + full-history catalogue — completed checkbox evidence".

> **Remaining P10-B todos moved to a child plan (2026-07-24, plan line-cap remediation).** The 3 still-open P10-B todos
> — switch `fixtures_browser.py` to the single-file catalogue source, relabel the UI span-cap warning once that lands,
> and decide the regen-freshness caveat — were forked out **verbatim** into
> `/plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md`. See that child plan for the full
> open-todo text and current status; the shipped P10-B history above (the operator dialogue, the two corrections, the
> full 105,509-fixture rollup evidence) is the durable record and stays here.

> **`round` → its own issue doc** (ML data-correctness, not this plan's UI scope):
> `plans/active/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md` — operator approved a
> **full round fill**. `_flatten_fixture` defaults `round` to `""` (CanonicalFixture has no such field), so
> `competition_phase`=UNKNOWN and `is_promotion_relegation`=**False** (a WRONG value, not an honest null) on ~16.5k
> fixtures / ~136k after the rollup. It is a **regression**: 545/17,064 rows DO carry real values ('Round of 16',
> 'Quarter-finals', 'Final'), ALL within 2025-12-01..30. Recovery is **not** per-fixture — the adapter fetches bulk per
> (league, season) with no `date=` and keeps the raw carrying `league.round` → **~600-700 calls for 2019→2026**, not
> 17k. Backfill rewrites 8 years of day-parquets (**the copy ML reads**) → dry-run + snapshot + row-count verify first.

> **Process finding raised this session** →
> `plans/active/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md`: `git pull --rebase --autostash`
> restores FOREIGN dirty files into the **index**, so a by-name `git add` still commits another agent's WIP. Measured:
> `unified-trading-pm@1a59516af` intended 1 file, shipped 3 (swept another agent's in-progress plan edits + an
> uncommitted issue doc). No data lost; not reverted (a revert would delete their only copy). Affects every agent in a
> shared checkout.

---

## Operator decisions — RESOLVED (2026-07-16)

1. **P8 — TEAMS axis**: ✅ direction A (reclassify per-league). Seasonal change is the trigger-date axis under each
   league.
2. **P4 — SPOT_ASSET**: ✅ populate for every base+quote token leg across DeFi + spot-CeFi (catalogue address columns →
   backfill → live discovery-time emission → CeFi symbol→chain→address mapping). Summary labels = canonical with raw on
   hover.
3. **P3 — prediction label**: ✅ slug for v1 (category from `canonical_question_group`), real title column as a
   follow-up.
4. **P6 — catalogue explorer**: ✅ both, phased (availability-derived now, true-catalogue projection follow-up).

### P9 round-2 decisions (operator 2026-07-16 pm)

5. **DeFi data_type**: ✅ `instruments` is canonical → migrate `instrument-catalog` → `instruments`.
6. **CeFi instrument_type**: ✅ migrate the non-canonical lowercase `perpetual`→`PERPETUAL`, `spot`→`SPOT_PAIR`.
7. **TradFi instrument_type**: ✅ migrate/stamp the 46.5M blank (`__legacy__`) rows to their canonical InstrumentType.
8. **Prediction data_types**: ✅ KEEP both grains (`prediction_canonical_question_group` +
   `prediction_market_lifecycle`) — no change.
9. **Sports invalid sources**: ✅ root-cause WHY `mdps_odds_horizon_bucket` + `instruments_service` appear as IS sports
   `source` values (operator: "is it a sign of deeper issues?") BEFORE any correction — diagnose the cross-service
   leakage path first, then fix at the writer/consolidator.

> **Migration HARD RULES (all three data migrations 5–7):** `instrument_type` + `data_type` are SHARD axes for
> MTDS/MDPS/features (NOT for instruments-service, where they are DISPLAY axes) — a naive IS-only rewrite of these
> values breaks cross-service shard-atom identity. Each migration must: (a) fix the WRITER first so new rows are
> canonical; (b) an IDEMPOTENT one-off migration script (pattern: `instruments-service/scripts/canonicalize_*_2026_*.py`
>
> - `backfill_defi_catalog_data_type_2026_06_21.py`) run on REAL infra with manifest-verified row counts; (c) preserve /
>   co-migrate shard-atom identity across MTDS/MDPS/features (confirm those services' shards for the same instruments,
>   or coordinate); (d) regen the affected catalogue + availability index. Run behind a pre-migration drain if any live
>   writer touches the same index. These are heavy real-infra ops — a fresh-context agent owns them (handoff prompt in
>   the operator's hands).

## Full audit artefacts

Findings digest + per-agent verdicts: workflow `wf_872e8051-00a` (findings all `CONFIRMED-WITH-CORRECTIONS`; P7 agent
failed the structured-output cap, so P7's exact chain-derivation line is TRACE-FIRST above). This plan is the durable
worklist; the transcript is ephemeral.

## Deferred work after 2026-07-18 (autonomous session — data-status audit remaining-items sweep)

Autonomous session drove every OPERATOR-DECISION-blocked item from the data-status audit to a ruling, then executed all
safely-completable work. Terminal state:

**✅ Completed + shipped this session**

| Item                                | Outcome                                                                                                                                                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| IS dead `/api/data-status` endpoint | DELETED `instruments-service@650dd4b7` (verified no caller — the data-pipeline-check skills + all workspace callers)                                                                                                                             |
| 847 phantom `captured` rows         | RESOLVED — `reconcile_phantom_manifest_rows_all.py --dry-run` on real infra shows cefi COINBASE/OKX=0 + defi CURVE/LIDO=0 phantoms (drained by the active cefi/defi consolidation since the finding)                                             |
| Deribit BTC/ETH options             | VERIFIED present — 264,122 DERIBIT OPTION rows (BTC 129,777 + ETH 134,345) in the live cefi catalogue                                                                                                                                            |
| Sports `odds` fork ruling           | Plan `sports_odds_exchange_fixed_fork_2026_07_18.md` (operator: FORK, venue→class by mechanism + edge confirms)                                                                                                                                  |
| DeFi POOL-id chain-uniqueness       | Superseded by the canonical `defi_consolidated_closeout_2026_07_18.md` (dual-key: canonical_instrument_id carries chain)                                                                                                                         |
| Cell-grid re-architecture           | Plan `data_status_cell_grid_rearchitecture_2026_07_18.md` (operator: SCHEDULE)                                                                                                                                                                   |
| InstrumentRecord silent-drop        | Prediction title already fixed (A4 `question=`); `extra='forbid'` hardening → plan `instrument_record_schema_completeness_extra_forbid_2026_07_18.md` (operator: schema-completeness, code-usage+business-reason+not-already-exists disposition) |
| non-Tardis DEX-perp MVP             | Ruled keep MVP + BLOCKED-CREDENTIALS scaffold; recorded in `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`                                                                                                                        |

**⏳ Remaining — bounded by real-world constraints (NOT decisions; do NOT bulldoze unattended)**

| Item                                                                                           | Why it's not closeable in a short unattended window                                                                                                                                                                                                                          |
| ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| non-Tardis confirmed bugs (LIGHTER override, EXTENDED book_snapshot date, HYPERLIQUID phantom) | Subtle venue-semantics fixes the code itself flags for careful design — LIGHTER "needs date-aware fix, not rename"; EXTENDED book endpoint is current-only so a target-date stamp would FABRICATE a timestamp (data-correctness violation). Tracked as careful-design todos. |
| cache_oom 24h soak                                                                             | Partial signal GREEN (0 OOM in 24h at rev 00205 16Gi/4CPU); full 24h-continuous memory-p99/warm-p95 soak is wall-clock-bound.                                                                                                                                                |
| Downloads CeFi re-capture (EIGEN + added bases)                                                | VM-scale IS CLI backfill (per venue/date) — a "no fire-and-forget" prod-write op that needs an attended VM launch.                                                                                                                                                           |
| Downloads CSV-download smoke + path-fix                                                        | Gated on the TIER-2 v9 `--apply` migration (the downloads plan's own sequencing gate).                                                                                                                                                                                       |
| Sports fork / cell-grid / InstrumentRecord / DeFi POOL-id                                      | Now tracked human/canonical plans — multi-step efforts for their own focused execution.                                                                                                                                                                                      |

## Todos (follow-up)

- [x] [DOC] P3. ✅ **DONE — all 4 confirmed already tracked + resolved in their owning docs; nothing missing, no new
      issue doc needed.** The 2 grep candidates named in this todo (`artifact_pipeline_observability_2026_07_17.md`,
      `cost_observability_deferred_followups_2026_07_10.md`) do NOT own any of the 4 items (checked both in full — zero
      relevant hits: no `cache_oom`/`soak`/`EIGEN`/`csv` content tied to these rows). The real owning docs, found by
      targeted grep + full read: - **non-Tardis confirmed venue bugs** (LIGHTER override, EXTENDED book_snapshot date,
      HYPERLIQUID phantom) — owned by `plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`
      (the 3rd grep candidate). All three are tracked `- [x]` FIX todos and are now DONE: LIGHTER `_VENUE_OVERRIDES`
      core-fixed `unified-trading-library@d59f14db` + re-verified 2026-07-30; EXTENDED `book_snapshot_5` date bug fixed
      `market-tick-data-service@55dac12a` (honest-absence skip, no fabricated timestamp) + re-verified 2026-07-30;
      HYPERLIQUID phantom rows un-flipped via `reconcile_phantom_manifest_rows_all.py --unphantom-only` (2026-07-19,
      1,277 rows healed). Two narrower follow-on todos remain genuinely open in that same doc (HYPERLIQUID k-prefix
      case-sensitivity P3, RULE 11 cefi-CEX relax P3) — both real, already `- [ ]` tracked there, not orphaned. -
      **cache_oom 24h soak** — owned by the archived
      `plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md` (18/18 todos done). The soak
      todo is `- [x]` CLOSED per operator 2026-07-18 ruling ("no 24h wait needed") on the strength of the partial GREEN
      signal (0 OOM in 24h at rev 00205, 16Gi/4CPU, stable across ~7 revisions) — not an open gap. - **Downloads CeFi
      re-capture** (EIGEN + added bases) — owned by
      `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`, `- [x]` DONE (verified 2026-07-18: 25
      EIGEN rows across 8 venues in the live cefi catalogue). - **Downloads CSV-download smoke + path-fix** — same doc,
      `- [x]` DONE: smoke ran 2026-07-18 (DeFi/CeFi/ prediction/MTDS-DeFi all 200; sports/tradfi 500 found),
      root-caused + fixed same window (`deployment-api@65f5593`, streamed CSV build for the >32 MiB Cloud Run
      buffered-response cap), archived at
      `plans/archive/issues/data_status_catalogue_csv_download_500_sports_tradfi_2026_07_18.md`. Net: this plan's "⏳
      Remaining" table (above) is stale prose as of this check — all 4 rows are actually resolved, just tracked in other
      docs rather than restated here. No new issue doc filed; nothing was orphaned.

- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-2cd17a)**: KEEP-NA, valid — 0 open todos of its own (all
  P1-P10 shipped or forked to owning child plans, per this doc's own 2026-08-02 Todos entry). NOT archived here: its
  ARCHIVE-vs-`archive_exempt` disposition is the explicit open todo 3 of
  `/plans/archive/issues/archive_candidates_content_verification_backlog_2026_08_06.md` (already
  `assigned_vm: planning`, operator-ruled 2026-08-06 to run only via that plan's own AO workers, not an
  interactive/one-shot session) — deferring to that plan rather than racing it.
- **archive_candidates_content_verification 2026-08-06 (slot 9, review)**: Archived per the standard 6-step ritual. All
  3/3 checkboxes were already done — every P1-P10 point shipped or deduped to other plans. `status: active → complete`,
  `last_updated: 2026-08-06`, all 16 corpus referrers (2 skills, 1 epic, 10 active plans, 3 issue docs) repointed to
  archive path.

> **ARCHIVED 2026-08-06** — human/local plan for the data-status page honest-coverage fix + UX & canonicalisation
> follow-ups. All P1-P10 work shipped (full evidence in
> `/plans/archive/2026_07/data_status_page_ux_and_canonicalisation_history_2026_07_24.md`). The one remaining finding
> (`InstrumentRecord extra='forbid'`) is deduped to `instrument_record_schema_completeness_extra_forbid_2026_07_18.md`.
> superseded_by: N/A (self-contained, all work complete).
