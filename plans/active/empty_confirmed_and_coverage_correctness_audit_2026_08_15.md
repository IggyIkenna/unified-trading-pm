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

- [x] 1. ✅ [DATA] P1. **cefi PERPETUAL/SPOT_PAIR scope determination — RESOLVED, no purge needed.** None of the top-15
      dominant combos are phantom/enumerator bugs — every venue genuinely supports the flagged instrument_type/data_type
      combination (verified against UAC's `DATA_TYPE_CAPABILITY_REGISTRY`/`INSTRUMENT_TYPES_BY_VENUE`). Full
      error_reason breakdown (folds in todo 2 below) shows **81.15% of cefi's 6.99M empty_confirmed already carries a
      reason in `OUT_OF_COVERAGE_WINDOW_REASONS`** (`EXPECTED_INSTRUMENT_NOT_LISTED` 57.17% +
      `EXPECTED_INSTRUMENT_DELISTED` 11.53% + `EXPECTED_PRE_VENUE_LAUNCH` 8.07% + `EXPECTED_PRE_SOURCE_COVERAGE_START`
      4.38%) — already excluded from the coverage-% denominator by existing honest-coverage v2 logic, genuinely correct
      absence signaling, nothing to prune or backfill. The remaining 18.72% is `SOURCE_RETURNED_ZERO` (1.31M rows) — the
      only population that could be a real gap or miscategorized failure, folded into todo 6's tagging-quality audit
      below. One minor find: 5,567 rows (0.08%) carry a legacy `EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400` reason no longer
      in the current `EmptyConfirmedReason` enum — too small to chase, noted for whoever next touches that taxonomy.
- [x] 2. ✅ [DATA] P1. **cefi error_reason breakdown — DONE, folded into todo 1 above** (same investigation, same
      evidence). Full table: `EXPECTED_INSTRUMENT_NOT_LISTED` 3,998,955 (57.17%) · `SOURCE_RETURNED_ZERO` 1,309,725
      (18.72%) · `EXPECTED_INSTRUMENT_DELISTED` 806,823 (11.53%) · `EXPECTED_PRE_VENUE_LAUNCH` 564,587 (8.07%) ·
      `EXPECTED_PRE_SOURCE_COVERAGE_START` 306,641 (4.38%) · `EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400` 5,567 (0.08%,
      legacy/unmapped) · `EXPECTED_SOURCE_DELIVERY_LAG` 3,072 (0.04%).
- [x] 3. ✅ [DATA] P1. **FUTURE→futures_chain bundling migration scope — DONE, found a LIVE ongoing bug, not just
      backlog.** CeFi FUTURE-itype: 1,596,176 rows (empty_confirmed 65.5%, matches the 16.24%-of-6.4M finding). Venue
      split: KRAKEN-FUTURES 46.6% · BYBIT 25.6% · OKX-FUTURES 11.9% · DERIBIT 7.8%. The enumerator/denominator side is
      already correctly wired for DERIBIT/OKX (`FUTURE_BUNDLE_VENUES={"cefi":{"DERIBIT","OKX"}}`,
      `market_data_categories.py:1712`). **The writer side is NOT** — OKX-FUTURES is still actively writing 159,732
      bare-`FUTURE` rows with real per-contract IDs, writes continuing through 2026-08-10/11 (4 days before this audit —
      a live ingestion defect, not closed backlog). Duplication check on the 182,584 captured FUTURE rows: the ~3,299
      legacy blank-ID rows (BYBIT/DERIBIT) are genuinely unique (zero matching `futures_chain` rows exist for either
      venue) — **needs re-stamping, not purging**. TradFi's side is already fixed at the code level
      (`unified-trading-library@74fe04fd98`, `instruments-service@de6c820956`) — only needs a
      `rebuild_tradfi_manifest.py` re-run, no new code. CeFi needs THREE separate fixes: (a) canonicalizer fix +
      re-stamp for the legacy blank-ID bucket (mirror the tradfi fix — add `"future"` to `_BUNDLE_GRAIN_EXCLUDED` or
      route it to `futures_chain` at `rebuild_cefi_manifest.py:454`), (b) an actual ingestion-code change for
      OKX-FUTURES' live per-contract writing (re-stamping alone would mislabel real per-contract files — the writer
      itself needs to fetch bundle-grain), (c) an `[OPERATOR]` decision on KRAKEN-FUTURES (743,935 rows, not even in
      `FUTURE_BUNDLE_VENUES` today). **Policy conflict flagged for Phase-N, needs operator ruling** (source: this doc's
      own Progress Log, 2026-08-15 session entry —
      `/plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`): the operator's 2026-08-15 "always
      bundle" ruling is broader than the existing F2 rule, which deliberately leaves BYBIT (409,343 rows) as
      per-contract — does BYBIT come into scope too, or stay an intentional exception?
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
- [x] 6. ✅ [DATA] P1. **Cross-AG `SOURCE_RETURNED_ZERO` tagging-quality audit — DONE, confirms operator's concern was
      correct.** Per-AG verdict: **cefi MISCATEGORIZING** (Deribit DVOL: sustained HTTP 429 has no backoff/failure flag,
      `deribit_volatility_index_handler.py:119-152`; Hyperliquid perp funding: per-coin failures swallowed via
      `return_exceptions=True`, `_perp_funding_hyperliquid.py:253-262` — if every coin fails, returns 0 without raising,
      fabricates a 200-OK evidence object). **defi MISCATEGORIZING** (5 on-chain oracle collectors — Aave/Compound/
      Fluid/Radiant/Spark — nested per-reserve/per-market `except Exception` swallows without setting an error flag; if
      every call in the loop fails, `clean_fetch_evidence()` synthesizes a fabricated 200-OK/0-rows evidence never
      reflecting real state; `dex_swaps`/`evm_defi`/`lending` call sites are clean by contrast). **sports CLEAN** (both
      call sites correctly gate on genuine confirmed-2xx-empty, any real failure re-raises to `attempted_failed`).
      **tradfi mostly CLEAN with one live structural landmine**: `_route_databento` (`umi_tick_provider.py:513-518`)
      pre-filters requested data_types against a supported-list BEFORE contacting Databento — unsupported types silently
      return an empty DataFrame with no failure signal, fabricating evidence for a request that never reached the
      source; not misfiring today (all configured tradfi dts are supported) but the code's own comment confirms this
      exact pattern caused a real incident once (mbp_10, fixed 2026-07-15) — a future dt addition without updating the
      supported-list reproduces it. **prediction PARTIAL**: per-market historical backfill is clean (real per-ticker
      evidence); the daily venue-grain catalog stamp (`process_completeness.py:205-259`) fabricates evidence the same
      way — and may already be connected to the already-filed Polymarket catalog-writer gap (zero blobs since
      2026-08-05): if `get_instruments_cached()` returns `[]` without raising when that gap fires, it lands in
      `empty_ok_venues` and stamps honest `SOURCE_RETURNED_ZERO` daily, masking a real production outage. **NOT verified
      against live manifest rows in this pass — see new todo below.**
- [x] 7. ✅ [DATA] P2. **Weekend/holiday gap handling — RESOLVED, deliberate documented design, not a bug.** Tradfi
      weekend/holidays ARE enumerated into `expected` (`enumerate_expected_universe.py:1918-1958`), but as a calendar
      pre-skip (no real fetch attempted, dedicated `EXPECTED_WEEKEND`/`EXPECTED_HOLIDAY` reasons). Keeping them IN the
      coverage-% denominator is an explicit, documented decision (`_honest_coverage_empty_reasons.py:660-664`: "a
      covered venue's weekend gap is part of the coverable universe") — not something to prune.
      `is_non_trading_day`/`non_trading_day_reason` is only called from the tradfi enumerator path —
      cefi/defi/sports/prediction are structurally unaffected (24/7 or non-calendar-gated markets), matching the
      operator's own hunch. No fix needed.
- [x] 8. ✅ [DATA] P2. **Prediction: instrument-catalogue-gated expected-window feasibility — RESOLVED, already built
      and already wired in, contrary to the plan's premise.** instruments-service already maintains a per-market
      catalogue (`build_prediction_catalogue_dataframe`, `build_instrument_catalogue.py:2127-2439`) with real
      `market_created_at`/`settlement_time` per (venue, conditionId), rolled up to (venue, canonical_question_group).
      `enumerate_expected_universe.py::_enumerate_v2_prediction` (lines 2964-3111) already gates on it: before listing →
      `EXPECTED_INSTRUMENT_NOT_LISTED`, after expiry → `EXPECTED_INSTRUMENT_DELISTED`, only inside the live window →
      `expected_unattempted`. One real nuance, not a bug: gating is at cqg-bundle grain (not literal per-market) per
      "decision 338" (2026-06-19), deliberately, to avoid a >50M-row blowup — same grain the manifest itself uses
      everywhere else for prediction. **No enumerator change needed** — the operator's original ask is already
      satisfied.
- [x] 9. ✅ [DATA] P1. **Prediction: June-2026 expected-universe growth spike — root cause found, already fixed,
      separate from the live-capture issue.** NOT connected to the already-filed live-capture doc (that's dated
      ~08-03/08-05, seven weeks after this spike began). Real cause: `build_instrument_catalogue.py`'s prediction
      catalogue parser required a `canonical_question_group=` path segment the writer never emits — so the prediction
      catalogue was **permanently 0 rows from the start of history** until commit `aab02153` (2026-06-16 19:11 UTC)
      fixed the path-parsing bug, jumping 0 → 668,384 rows in one commit (exact match to the "~668K markets" finding).
      Before that fix, `_enumerate_v2_prediction`'s `for instr in catalog:` loop (line 3018) never ran for ANY
      historical date — only the venue-grain pre-launch pass existed. Once fixed, the enumerator began correctly
      reaching real, previously-unenumerated markets and confirming them empty (99.8% `SOURCE_RETURNED_ZERO` in the
      surge = genuine data, not a tagging bug). **Already shipped — nothing to execute, just recorded here for the
      record.**
- [x] 10. ✅ [DATA] P2. **Prediction: category dimension feasibility — RESOLVED, cheaper than the VM-join framing
      suggested.** (1) Confirmed structurally, not just observationally:
      `write_guard.py::validate_prediction_instrument_type` (lines 35-45) raises `ValueError` unless
      `instrument_type == PREDICTION_MARKET` — it is the ONLY value possible, enforced at write time. (2) No
      existing-column proxy — `venue + instrument_type` collapses to just `venue` (2 values) since instrument_type is
      invariant. (3)/(4) A classifier already computes `(category, underlying,     resolution_period)` internally
      (`classifiers.py`) but never persists it; `CanonicalQuestionGroup` is a small, closed, static 89-member enum, not
      a live-cardinality problem — **recommendation: build an ~89-row static `cqg → category` lookup table** (a UAC
      registry addition, NOT a manifest schema change, near-zero cost), covering the cqg-bundle grain used everywhere in
      the rollup today. A finer per-conditionId join is possible later against the already-built catalogue snapshot if
      wanted, but isn't required to satisfy the original ask.

### New execution-scoped todos (surfaced by the above audit findings, not in original scope)

- [ ] [DATA] P0. **Fix cefi's 2 SOURCE_RETURNED_ZERO miscategorization bugs**: Deribit DVOL sustained-429 (no backoff/
      no failure flag, `deribit_volatility_index_handler.py:119-152`) and Hyperliquid per-coin swallowing
      (`_perp_funding_hyperliquid.py:253-262`, `return_exceptions=True` with no per-coin failure propagation).
      Done-when: both paths correctly route a total-failure case to `attempted_failed`/`record_failed`, not a fabricated
      `SOURCE_RETURNED_ZERO`, with a regression test forcing all-calls-fail and asserting the correct reason.
- [ ] [DATA] P0. **Fix defi's 5 oracle-collector SOURCE_RETURNED_ZERO miscategorization bugs**: Aave/Compound/Fluid/
      Radiant/Spark all have nested per-reserve/per-market `except Exception` that swallows without setting an error
      flag (`_aave_oracle_collection.py:78-79`, `_compound_oracle_collection.py:151-152,169-170,261-262`, and the
      identically-structured Fluid/Radiant/Spark equivalents). Done-when: each collector correctly distinguishes
      "genuinely queried, got nothing" from "every RPC call in the loop errored," with a regression test forcing
      total-failure and asserting `record_failed` not `record_empty`.
- [ ] [DATA] P1. **Close tradfi's `_route_databento` unsupported-dt landmine** (`umi_tick_provider.py:513-518`) before
      it reproduces the mbp_10 incident (fixed 2026-07-15) — add a real failure signal when a requested data_type isn't
      in `_DATABENTO_SUPPORTED_DATA_TYPES` instead of silently returning an empty DataFrame with no failure flag. Not
      urgent (nothing currently misfires — all configured tradfi dts are supported today) but should land before any new
      tradfi data_type is added to the expected-universe.
- [ ] [DATA] P0. **Verify whether prediction's Polymarket catalog-writer gap (zero blobs since 2026-08-05) is being
      silently absorbed as honest `SOURCE_RETURNED_ZERO`** via `process_completeness.py:205-259`'s daily venue-grain
      stamp — check live manifest rows for POLYMARKET `empty_confirmed`/`SOURCE_RETURNED_ZERO` counts since 2026-08-05
      specifically (not yet done, flagged but out of scope in the tagging-quality pass). If confirmed, this is masking a
      real production outage as clean data — treat as P0 alongside the already-filed catalog-gap issue.
- [ ] [OPERATOR] P1. **Rule on BYBIT's scope in the FUTURE→futures_chain "always bundle" policy** — 409,343 rows,
      currently an intentional per-contract exception under the existing F2 rule; the 2026-08-15 "always bundle" ruling
      is broader than F2 and doesn't explicitly resolve whether BYBIT is now in scope too.
- [ ] [OPERATOR] P2. **Rule on KRAKEN-FUTURES's scope** (743,935 FUTURE-itype rows) — not in `FUTURE_BUNDLE_VENUES` at
      all today; needs an explicit decision before any bundling migration touches it.
- [ ] [DATA] P2. Re-run `rebuild_tradfi_manifest.py` to apply the already-shipped FUTURE-canonicalization fix
      (`unified-trading-library@74fe04fd98`, `instruments-service@de6c820956`) — no code change needed, purely
      operational.
- [ ] [DATA] P2. Fix cefi's legacy blank-instrument-id FUTURE bucket (~3,299 captured rows, BYBIT/DERIBIT) — add
      `"future"` to `_BUNDLE_GRAIN_EXCLUDED` or route it to `futures_chain` at `rebuild_cefi_manifest.py:454` (mirrors
      the tradfi fix), then re-stamp the confirmed-unique existing rows (NOT duplicates — verified this session).
- [ ] [DATA] P1. Fix OKX-FUTURES' live per-contract writing bug (159,732 rows and growing daily as of 2026-08-15) —
      needs an actual ingestion-code change (bulk bundle-grain fetch replacing per-contract fetch), not a manifest-only
      re-stamp; re-stamping alone would mislabel real per-contract files as bundle-grain.
- [ ] [DATA] P2. Add the ~89-row static `cqg → category` lookup table to UAC (per todo 10's recommendation) and wire it
      into the deployment-api/ui drilldown once built.
- [ ] [DATA] P0. **defi empty_confirmed breakdown + `EXPECTED_INSTRUMENT_NOT_LISTED` semantics — still open, agent was
      running at session checkpoint time (2026-08-15), not yet reported.** Pick up where the dispatched investigation
      left off — same method as the cefi/tradfi/prediction sibling breakdowns (grain, date/venue/data_type/
      instrument_type/error_reason distribution via `read_availability_index`, column-projected + filtered; large
      manifest, ~159M total rows, scope queries carefully). This is the single biggest unresolved empty_confirmed
      population (78.7M, larger than captured 32.5M) and the highest-priority remaining audit gap.

## Progress Log

- **2026-08-15 (interactive session, slot 3)**: Filed following operator's session-long investigation into
  cefi/defi/tradfi/prediction empty_confirmed volumes and several structural questions (FUTURE→futures_chain, prediction
  catalogue-gating, category dimension, SOURCE_RETURNED_ZERO tagging quality). Operator ruled: human plan (not AO),
  audit-first structure with per-AG/per-fix-type execution plans to follow, gated on this doc's findings.
  Cross-referenced and linked (not duplicated) two already-open relevant docs:
  `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` (FUTURE-vs-bundle-grain, tradfi side already tracked) and
  `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` (live-capture-side
  prediction bugs, possibly connected to the batch-backfill growth-spike question).
- **2026-08-15 (same session, ~2h later, /pre-compact checkpoint)**: 8 of 9 original audit todos completed via 5
  parallel investigation agents (one of them recursively spawned its own 5 sub-agents for the per-AG
  SOURCE_RETURNED_ZERO tagging pass). Only the defi breakdown remained in-flight at checkpoint time — see the new
  execution-scoped todos above, which convert every finding into tracked follow-up work rather than leaving it as
  chat-only prose (workspace hard rule). Headline results: cefi's PERPETUAL/SPOT_PAIR dominance turned out to be benign
  (81% already correctly out-of-coverage-window); the SOURCE_RETURNED_ZERO tagging-quality concern was CONFIRMED correct
  — real miscategorization bugs found in cefi (2 sites) and defi (5 oracle collectors), plus a live structural landmine
  in tradfi; the FUTURE→futures_chain migration found a LIVE ongoing bug (OKX-FUTURES still writing bare-FUTURE rows
  daily as of 2026-08-10/11), not just historical backlog; and two of prediction's three open questions turned out to
  already be solved (catalogue-gated expected-windows already exist and are already wired in; the June-2026 growth spike
  has an exact, already-shipped root-cause commit) — only the category-dimension question needed a genuine new
  recommendation. Also caught and fixed a real correctness issue while shipping the UAC prediction-registry fix: a
  2026-07-07 decision had deliberately deleted this exact registry row, and both that decision AND this session's fix
  are correct simultaneously — they're about two different consumers (Layer-2 backfill vs Layer-1 audit) that the
  2026-07-07 decision didn't distinguish. Documented the reconciliation in both the test and the registry comment so a
  future reader doesn't repeat the same "looks inert, safe to delete" mistake.
