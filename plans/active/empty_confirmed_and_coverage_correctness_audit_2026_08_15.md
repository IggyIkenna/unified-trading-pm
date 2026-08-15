---
doc_type: plan
title: Empty-confirmed correctness audit — cefi/defi/tradfi/prediction (Phase 0, audit-only)
summary: >-
  Pre-investigation phase before any manifest mutation, backfill, or purge: for each asset_group's large empty_confirmed
  population, determine root cause (genuinely out-of-scope → prune, mislabeled → re-backfill, or tagging-quality bug →
  fix the tagger) with real evidence, not guesses. Covers cefi PERPETUAL/SPOT_PAIR scope + error_reason breakdown,
  defi's un-investigated 78.7M empty_confirmed, a cross-AG SOURCE_RETURNED_ZERO tagging-quality audit,
  weekend/holiday-gap handling, defi's EXPECTED_INSTRUMENT_NOT_LISTED semantics, and prediction's catalogue-driven
  expected-window feasibility + category-dimension design. Zero mutations in this phase — findings feed Phase-N
  execution plans (per-AG or per-fix-type) gated via depends_on.
status: active
nature: design
asset_group: [meta]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, deployment-api, deployment-ui]
scope: [engineer]
tags: [honest-coverage, empty-confirmed, data-correctness, cefi, defi, tradfi, prediction, audit]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md,
    /plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 7.2
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    instruments-service/scripts/measure_honest_coverage.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md,
  ]
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
effort: high
drift_direction: advance-code
---

# Empty-confirmed correctness audit — cefi/defi/tradfi/prediction (Phase 0, audit-only)

> **Phase 0 of 2 — audit only, ZERO manifest/GCS mutations in this plan.** Operator ruling 2026-08-15: human plan (not
> AO-dispatched — most of this is genuine judgment calls), audit-first structure. Findings here feed per-AG/per-fix-type
> Phase-N execution plans, each gated on this plan via `depends_on` + `gate_on_depends: true`. Any todo below that would
> mutate manifest rows or GCS objects is out of scope for THIS doc — cite
> `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` in whichever Phase-N plan actually performs it.

## Why

Session-long investigation (2026-08-15) into the Honest Coverage rollup's `empty_confirmed` volumes surfaced real
concern: for several asset_groups, `empty_confirmed` is comparable to or larger than `captured` (defi 78.7M vs 32.5M;
prediction 2.27M vs 452K). The operator's framing: for each large population, is it (a) a known-out-of-scope population
that should never have been marked `empty_confirmed` at all — clear/purge it, or (b) a genuinely mislabeled population
that needs re-backfill + recategorization? Guessing either way risks either leaving real data gaps invisible, or purging
data that's actually needed. This plan gets the evidence first.

## Todos (LOCAL — investigation only, no mutations)

- [ ] [DATA] P1. **cefi PERPETUAL/SPOT_PAIR scope determination.** These two instrument_types are 62.9%/20.15% of cefi's
      6.4M empty_confirmed (session-2026-08-15 finding). For each dominant (venue, instrument_type) combination,
      determine: is there a known venue-capability rule (`VENUE_DATA_TYPE_CAPABILITIES`, `VENUES_BY_ASSET_GROUP`) saying
      this combo should never exist (e.g. a venue that doesn't actually list perpetuals for that data_type) — in which
      case it's a Layer-1/enumerator bug generating a phantom expected row that should never have been enumerated — or
      is capture genuinely expected but failing/never-attempted? Done-when: a table of the top 15 (venue,
      instrument_type, data_type) combos from the session's cross-tab, each classified OUT-OF-SCOPE (cite the capability
      rule) or GENUINE-GAP (cite what's missing), with counts.
- [ ] [DATA] P1. **cefi error_reason breakdown.** The 2026-08-15 cefi investigation covered venue/date/data_type/
      instrument_type but never pulled the `error_reason` column (tradfi's and prediction's investigations did, and it
      was the single most explanatory axis for both). Query `empty_confirmed` rows for `asset_group=cefi` grouped by
      `error_reason`, same method as the tradfi/prediction sibling queries (`read_availability_index`,
      column-projected + filtered, never a bare full-table read). Done-when: a full reason-code breakdown table,
      cross-tabbed against the PERPETUAL/SPOT_PAIR finding above if it clarifies scope.
- [ ] [DATA] P1. **FUTURE→futures_chain bundling migration scope** (cefi AND tradfi — the tradfi side is ALREADY a
      tracked open issue, `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`, read it in full first, don't
      re-derive). Operator ruling: futures should always bundle into the `futures_chain` instrument_type (shared
      expiry + day; other dims identical) — a bare `FUTURE` itype is legacy/pre-rollup, not a distinct target state. For
      cefi: quantify the current `FUTURE`-itype population (rows, venues, empty_confirmed share) the same way the tradfi
      issue already did, and determine whether cefi's `_rollup_bundle_grain` (G1-ENUM, cited in the Honest Coverage
      codex doc) already covers cefi the way it covers tradfi, or needs the same fix. Done-when: a written migration
      scope (which rows migrate, which get purged as duplicates-of-bundle, estimated row count, whether existing
      captured `FUTURE` data needs re-stamping to `futures_chain` vs is genuinely redundant) — this feeds a Phase-N
      execution plan, does not execute here.
- [ ] [DATA] P1. **defi empty_confirmed breakdown** (78.7M rows, larger than captured 32.5M — never investigated this
      session, sibling to the cefi/tradfi/prediction breakdowns already done). Same method: grain confirmation,
      date/venue/data_type/instrument_type/error_reason distribution, cross-tab for a dominant combination. Done-when:
      same shape of report as the cefi/tradfi/prediction sibling findings.
- [ ] [DATA] P1. **defi `EXPECTED_INSTRUMENT_NOT_LISTED` semantics.** Operator question: does this reason mean the
      instrument is genuinely not listed on-chain/on the venue, or does it reflect instruments-service's own catalogue
      being incomplete (i.e. the row exists on-chain but IS never enumerated it)? Trace
      `EXPECTED_INSTRUMENT_NOT_LISTED`'s write call sites for defi specifically and determine which. Separately confirm:
      are `EXPECTED_PRE_SOURCE_COVERAGE_START` rows already tagged as out-of-scope/excluded from the "real gap" surface,
      or do they currently read as ordinary `empty_confirmed` indistinguishable from a real gap? Done-when: a clear
      statement of what each reason actually proves, with file:line evidence.
- [ ] [DATA] P1. **Cross-AG `SOURCE_RETURNED_ZERO` tagging-quality audit.** Operator concern: is this reason only
      stamped when the source explicitly confirms zero rows (a genuine successful-request-empty-response), or does it
      also catch bidding/API/network/transient failures that got miscategorized as "confirmed empty"? For EACH
      asset_group (cefi, defi, tradfi, sports, prediction), find every
      `record_empty(...,     reason=SOURCE_RETURNED_ZERO)` (or equivalent) call site and read the surrounding
      error-handling: does it sit behind a genuine "got a 2xx / explicit empty-response" branch, or could a caught
      exception (timeout, 429, 5xx, auth failure) fall through into the same reason code? Done-when: a per-AG verdict
      (CLEAN / MISCATEGORIZING, with file:line evidence for each) — this is a correctness-critical finding, not a style
      nitpick, since a miscategorized failure silently masquerades as honest absence.
- [ ] [DATA] P2. **Weekend/holiday gap handling.** Operator wants confirmation: are non-trading days (weekends, exchange
      holidays) currently enumerated into `expected` at all (and thus counted as `empty_confirmed` once
      confirmed-absent), or already excluded from the expected universe entirely (never attempted, never counted)? If
      the former, scope what it would take to exclude them at enumeration time instead (never generate the expected row)
      — done-when: current behavior confirmed with evidence, and if it needs fixing, a scoped description of the
      enumerator change (which AGs affected, roughly how many rows this would prune from `expected`/`empty_confirmed`
      going forward — this does NOT retroactively purge existing manifest rows, that's a Phase-N execution decision).
- [ ] [DATA] P2. **Prediction: instrument-catalogue-gated expected-window feasibility.** Operator's core ask: prediction
      markets are transient (listed → active → delisted/expired), so `empty_confirmed` should only ever be stamped for
      days the market was actually live — not before listing, not after delisting/expiry — the same pattern DeFi/TradFi
      already use via their instrument catalogues. Investigate: (1) does instruments-service already maintain a
      prediction catalogue with listing/expiry dates per market (Kalshi has explicit expiry; Polymarket resolution
      dates) that COULD gate the expected-window the way `PREDICTION_VENUE_LAUNCH_DATES` gates the venue-level
      pre-launch floor? (2) if yes, why isn't the Layer-2 enumerator already using it per-market instead of
      blanket-generating an expected row for every day regardless of listing state? (3) if a catalogue exists but is
      incomplete/stale, is that consistent with the June-2026 expected-universe growth spike (see next todo)? Done-when:
      a definitive yes/no on catalogue existence + completeness, with file:line evidence, and if yes, a scoped
      description of the enumerator change needed (feeds Phase-N).
- [ ] [DATA] P1. **Prediction: June-2026 expected-universe growth spike (100-200x) — root cause.** Session finding: the
      per-market sentinel fan-out grew from ~trickle to ~668K distinct markets touched starting almost exactly 2026-06.
      Operator hypothesis to check: was the catalogue rebuilt/widened around then (i.e. earlier dates were captured too
      narrowly — only a subset of markets grabbed historically — and June-2026 is when a wider catalogue first got wired
      in), or is the growth itself genuine (the actual number of live markets on Polymarket/Kalshi grew that much)?
      Cross-reference against the ALREADY-FILED
      `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` (read in full first) —
      that doc's root cause (B), Polymarket's catalog writer stopping after 2026-08-05, and (A), the live cache never
      refreshing, are LIVE-capture-side bugs; determine whether either is mechanistically connected to the
      BATCH-backfill expected-universe growth, or whether this is a genuinely separate root cause requiring its own
      investigation (e.g. `enumerate_expected_universe.py`'s prediction path being re-run/re-triggered around June 2026,
      or a UAC venue-capability/registry change landing then). Done-when: either a definitive connection to the
      already-filed issue (cite it, no new doc needed) or a clear statement that it's separate with the actual root
      cause named.
- [ ] [DATA] P2. **Prediction: category dimension feasibility (no manifest schema change).** Operator wants
      category-like groupings (Kalshi's 6 categories: Crypto/Economics/Financials/Commodities/Sports/Politics;
      Polymarket's tag-based equivalent) visible in the drilldown UI, but does NOT want to change the manifest schema
      right now. Investigate: (1) what are ALL of prediction's actual `instrument_type` values in the manifest today
      (session finding only confirmed `PREDICTION_MARKET` — confirm if that's genuinely the only one, or if there's more
      granularity already there that could double as a category proxy)? (2) could `venue` + `instrument_type` combined,
      or some other EXISTING manifest column, serve as a category proxy without a schema change? (3) if no existing
      column can serve, what's the actual cost of joining `instrument_id` back to the catalogue snapshot to derive
      category — the operator noted "you could do this with a VM" for the expensive join; scope roughly how expensive
      (row count, join cardinality) and whether a VM-based one-time join + cached category-lookup table (NOT a manifest
      schema change, a separate lookup artifact) is a viable middle ground. Done-when: a recommendation
      (existing-column-viable / needs-a-cached-lookup-table / needs-a-schema-change-after-all) with the reasoning,
      feeding a Phase-N design decision — do not build anything here.

## Progress Log

- **2026-08-15 (interactive session, slot 3)**: Filed following operator's session-long investigation into
  cefi/defi/tradfi/prediction empty_confirmed volumes and several structural questions (FUTURE→futures_chain, prediction
  catalogue-gating, category dimension, SOURCE_RETURNED_ZERO tagging quality). Operator ruled: human plan (not AO),
  audit-first structure with per-AG/per-fix-type execution plans to follow, gated on this doc's findings.
  Cross-referenced and linked (not duplicated) two already-open relevant docs:
  `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` (FUTURE-vs-bundle-grain, tradfi side already tracked) and
  `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` (live-capture-side
  prediction bugs, possibly connected to the batch-backfill growth-spike question).
