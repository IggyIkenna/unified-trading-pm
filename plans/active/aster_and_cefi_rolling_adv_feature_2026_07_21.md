---
doc_type: plan
title: Rolling ADV (average daily volume) feature for CeFi instruments — strategy-side volume caps
summary: >-
  Strategy code needs a rolling-N-day average-daily-volume (ADV) signal per CeFi instrument, both to cap position size
  as a % of ADV and to gate an instrument as "not yet tradeable" until it has a minimum history of real volume. Surfaced
  during the ASTER 1000-multiplier-coin data-completeness work — some instruments show flat/degenerate funding rates and
  near-zero live 24h volume (e.g. 1000SATS at $6.04/24h, 1 trade), which is genuine illiquidity, not a pipeline defect,
  and needs a determinable downstream signal rather than manual eyeballing. MDPS's `processed_candles` already has the
  right schema (`volume`/`quote_volume` at `timeframe=24h`) for this, canonically keyed per instrument, but currently
  has zero coverage for the on-chain-perp CeFi venues (ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/ EXTENDED-STARKNET) — only
  legacy tardis-sourced CeFi venues have candles today. Decision — scaffold the ADV CONSUMER now against MDPS's existing
  canonical path/schema (so it activates automatically once candle coverage is extended to these venues, a separate
  deferred task), rather than building a parallel volume-computation pipeline.
status: active
nature: design
asset_group: [cefi]
stage: [data]
repos: [features-service, market-data-processing-service, market-tick-data-service]
scope: [engineer]
tags:
  [
    adv,
    average-daily-volume,
    volume-cap,
    liquidity,
    cross-instrument,
    mdps,
    processed-candles,
    funding-rate,
    illiquidity,
  ]
related:
  [
    /plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md,
    /codex/02-data/data-lineage-MTDS-features-ml.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    "operator ask 2026-07-21: strategy-side volume caps as % of ADV, min-7-day-history-to-trade gate, discovered while
    diagnosing ASTER funding-rate realism for the 1000-multiplier coins (1000SHIB/1000SATS showing flat funding +
    near-zero live volume)",
  ]
context_scope:
  [
    /codex/02-data/data-lineage-MTDS-features-ml.md,
    features-service/features_service/cross_instrument/app/calculators/adv.py,
    features-service/features_service/cross_instrument/app/calculators/book_depth.py,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md,
  ]
---

# Rolling ADV feature for CeFi instruments

## Why (evidence)

Diagnosing whether ASTER funding-rate data is realistic (operator question, 2026-07-21) surfaced that funding-rate
variance correlates with liquidity but isn't a clean function of it alone (a live-API cross-check showed one coin,
1000WOJAK, with genuinely high funding variance at only modest volume). The determinable, no-extra-fetch signal that
DOES work is a rolling distinct-value count on `funding_rate` itself — but the operator separately asked for the more
general, standard tool: a real ADV feature, so strategy code can (a) cap position size at some % of ADV and (b) refuse
to trade an instrument until it has amassed a minimum trailing history of real volume (proposed: 7 days).

Live-API spot-check (2026-07-21) of the 10 ASTER 1000-multiplier coins found volume spanning
**$6.04/24h (1000SATS, 1
trade)** to **$536,278/24h (1000PEPE, 824 trades)** — a >80,000x range within a single MVP-gated
instrument set. This is exactly the kind of dispersion an ADV-based cap/gate is meant to catch, and it isn't
ASTER-specific — every CeFi venue has a long illiquid tail.

## Design decision (2026-07-21)

**MDPS's `processed_candles` is the right source** — `venue={V}/{instrument_id}.parquet` keyed, `timeframe=24h` candles
carry `quote_volume` directly (see `/codex/02-data/data-lineage-MTDS-features-ml.md` § Layer 2, corrected 2026-07-21
with the real verified path). It is NOT currently populated for the 4 on-chain-perp CeFi venues
(ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET) — confirmed via a direct GCS listing on a recent day, zero
`pipeline_mode=batch_aster`/`batch_hyperliquid`/etc. objects under `processed_candles/`, even for HYPERLIQUID which has
2+ years of raw trade history.

**Decision: do NOT extend MDPS's candle-building scope right now** (separate, deferred future task — Phase 2 below).
Instead, scaffold the ADV **consumer** against MDPS's existing canonical path/schema, so it activates the moment that
gap closes, with zero additional wiring. This plan tracks Phase 1 (the consumer) as done/in-review; Phase 2 (extending
MDPS candle coverage to the 4 venues) is explicitly NOT started.

## Codex SSOTs

- `/codex/02-data/data-lineage-MTDS-features-ml.md` § Layer 2 — MDPS canonical path (corrected 2026-07-21) + the
  on-chain-perp coverage gap note.
- `plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md` — the ASTER data-completeness work
  this originated from, including the funding-rate realism finding.

## Progress Log

- 2026-07-21 — Plan created (human/local track, per operator's explicit answer to the plan-destination question).
  Dispatched the Phase-1 scaffold to a sub-agent in parallel with unrelated ASTER manifest remediation work. Codex
  updated (data-lineage doc's MDPS path correction + coverage-gap note; manifest-consolidator-ssot.md's CAS-marker
  gotcha, a related-but-separate finding from the same session).
- 2026-07-21 (later) — Resumed after context compaction; the dispatched sub-agent (`a52c04d559875393f`) was no longer
  tracked (task registry had no record of it — likely lost across the compaction boundary) and had never shipped.
  `adv.py` + `test_adv.py` were still present on disk, untracked. Reviewed the module directly: reads
  `resolve_bucket(kind="market-data", asset_group=...)` + `derive_pipeline_mode_for_row(venue, asset_group, data_type)`
  (the same SSOT resolver `perp_funding_rates` uses — no hardcoded per-venue if/elif), probes the
  `pipeline_mode=`-partitioned path before a bare fallback (mirrors `DataLoader._resolve_blob_paths`), and returns a
  three-state `AdvStatus` (`OK` / `INSUFFICIENT_HISTORY` / `NO_DATA`) via a frozen `RollingAdvResult` dataclass with an
  `is_tradeable` property. First `quality-gates.sh --no-fix` run: 17,776 tests passed (19 new, `test_adv.py`) but ONE
  real gate failure — `RollingAdvReader.compute_rolling_adv()` at 80 lines, over the workspace's 50-line method-size
  cap. Refactored twice: round 1 split the day-loop into `_collect_observed_quote_volumes` and the reduction into
  `_build_result` (80L → but `_build_result` itself landed at 55L, still over); round 2 collapsed the duplicate
  `RollingAdvResult(...)` construction and extracted `_status_for_observed_days` + `_log_rolling_adv_outcome` as
  module-level helpers, bringing every method under the cap. Re-ran QG twice more to converge; final run:
  `✅ ALL QUALITY GATES PASSED (244s)`, 17,776 tests still green, zero violations. Ship was blocked twice by other
  slots' live path-dependency WIP (`unified-trading-library`, then `unified-api-contracts`) — confirmed via mtime
  liveness each time (both <30s old, repeatedly), left untouched, waited for each to clear. **Shipped:
  `features-service@8608ea5d`** ("feat(cross_instrument): rolling ADV consumer over MDPS processed_candles"),
  `git rev-list --count origin/live-defi-rollout..HEAD` = 0. Same dirty-dep churn also delayed the independent GAP-4
  genesis-clip fix (see the ASTER issue doc) across execution-service/unified-trading-pm/market-tick-data-service,
  worked on in parallel while waiting.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - Phase 2 is an explicit operator
  "consumer-first, producer later" deferral and Phase 3 needs a design conversation on cap placement and the % ceiling.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added `book_depth.py` as a second source path (the
  Phase-3 stretch item's named target), since Phase 1's `adv.py` is now shipped and the remaining work is Phase 3
  (strategy-side wiring) + the book_depth stretch item.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — re-confirms the 2026-07-30 verdict
  (content unchanged besides context-scout refreshes). Phase 1 fully shipped (features-service@8608ea5d); Phase 3's
  strategy-side ADV consumption needs a design conversation on cap placement/% ceiling (doc's own text: "needs a design
  conversation"), and the book_depth.py item is an explicit out-of-scope stretch.
- **na-corpus-digest-closeout 2026-08-08**: operator ruled interactively on Phase 3's open design question: cap applies
  at order-sizing time, ceiling 10% of ADV. Filed the concrete `[BACKEND]` implementation todo (scope: clamp
  `PerClientSignal.allocation_amount_usd` in `AllocationSizer.size_signal()` to `0.10 * adv_usd`, fail-closed when
  `AdvStatus` isn't `OK`). Implementation still depends on Phase 2 candle coverage landing for the relevant venues
  (largely done per Phase 2's own log; residual manifest-emission gap tracked in the separate
  `mdps_cefi_candle_manifest_never_emitted_2026_07_26` issue). `assigned_vm` stays `NA` — flipping to `planning` needs a
  gated finalize companion plan (`task_template.md` §4, plan-hygiene-enforced) which is out of scope for a single-item
  ruling application; a future scoping pass can flip it together with authoring that companion.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — Phases 1-2 shipped; Phase 3 backend
  already extracted 2026-08-09 to cefi_satellite_ao_dispatch_batch12_2026_08_09.md todo 2. Sole remaining open item is
  an explicit judgment-call stretch item (book_depth.py).
- **cefi_satellite_ao_dispatch_batch12_2026_08_09_finalize.md todo 1, 2026-08-09** (review): Phase 3's citation-pointer
  line replaced with the verified shipping commit, `strategy-service@73aa792f` (confirmed reachable on
  `origin/live-defi-rollout` before citing). **Remaining open in this doc: 1** — the Phase-3 `[DATA] P3` stretch item
  (`book_depth.py` → Phase-1 utility wiring), an explicit judgment call, out of scope for this reconciliation pass.

## Phase 1 — ADV consumer (scaffold against MDPS's existing schema)

- [x] [DATA] P1. Implement a reusable rolling-window ADV reader — **features-service@8608ea5d**. Module:
      `features-service/features_service/cross_instrument/app/calculators/adv.py`, class `RollingAdvReader` with
      `compute_rolling_adv(venue, instrument_id, asset_group, as_of_date, window_days=7, *, data_type="derivative_ticker")`
      (module-level `compute_rolling_adv()` / `compute_rolling_adv_7d()` convenience wrappers). Reads MDPS
      `timeframe=24h` candles per `(venue, instrument_id, asset_group)` across the trailing window, averaging
      `quote_volume` over the OBSERVED days only (never diluted by `window_days` — see module docstring). Bucket via
      `features_service.common.resolve_bucket(kind="market-data", asset_group=...)`; `pipeline_mode` via the SSOT
      resolver `derive_pipeline_mode_for_row(venue, asset_group, data_type)` (no hardcoded per-venue if/elif), probing
      the `pipeline_mode=`-partitioned path before a bare fallback. The originally-dispatched sub-agent
      (`a52c04d559875393f`) had built the file but was no longer tracked after a context-compaction boundary and never
      shipped; picked up directly, fixed a 50-line method-size-gate violation (`compute_rolling_adv` was 80L; split into
      `_collect_observed_quote_volumes` + `_build_result`, then further extracted module-level
      `_status_for_observed_days` / `_log_rolling_adv_outcome` to clear `_build_result`'s own 55L overage), reran QG to
      convergence, shipped.
- [x] [DATA] P1. Distinguish three result states — `AdvStatus` (`OK` / `INSUFFICIENT_HISTORY` / `NO_DATA`) StrEnum +
      frozen `RollingAdvResult` dataclass with `days_observed`, `adv_usd: float | None`, and an `is_tradeable` property
      (`status is AdvStatus.OK`). A missing candle file (`blob_exists` False on both candidate paths, or a
      download/parse exception routed through `classify_and_emit_error`) is counted as an unobserved day, never an error
      — verified this is the actual behavior for ASTER/HYPERLIQUID/LIGHTER/EXTENDED today (zero MDPS candle coverage,
      `NO_DATA` on every call). Shipped in the same commit, **features-service@8608ea5d**.
- [x] [DATA] P1. Unit tests — `tests/cross_instrument/unit/test_adv.py`, 19 tests: full window (all days observed),
      exact-mean value correctness, partial window (`INSUFFICIENT_HISTORY`, averaged over observed days only), zero
      candles (`NO_DATA`, `download_bytes` never called), `blob_exists` guard, `pipeline_mode`-partitioned path probed
      before the bare fallback, null/missing `quote_volume` not counted, download-exception classified + day skipped,
      `window_days<=0` raises `ValueError`, module-level wrapper behavior, `is_tradeable` across all three states.
      Storage client mocked the same way `test_book_depth.py`/`test_raw_data_loader.py` do (`MagicMock` substituted for
      `RollingAdvReader._storage_client`). All 19 passing as part of the shipped commit's 17,776-test green run.
- [x] [REVIEW] P1. Confirmed the shipped module against this plan + the data-lineage codex doc — this checklist item's
      values above ARE the real shipped path/signature/resolution-approach (no placeholder text). Codex doc
      (`/codex/02-data/data-lineage-MTDS-features-ml.md`) cross-referenced with the actual module path in the same
      commit as this plan update.

## Phase 2 — extend MDPS candle coverage to on-chain-perp CeFi venues (DONE for the core ask 2026-07-26, 2 residuals filed separately)

- [x] ✅ **DONE 2026-07-26 (cefi_satellite_ao_dispatch_batch1_2026_07_25.md todo -001).** No MDPS code change was needed
      — `pipeline_mode=batch_aster`/`batch_hyperliquid`/`batch_lighter_api`/`batch_extended` were already
      generic-resolved (venue list is UAC-owned, timeframe list is one flat default, `resolve_pipeline_mode_from_source`
      is closed-set generic). Real backfill launched + verified live: HYPERLIQUID `trades` candles for 2026-07-19
      (BTC+ETH) confirmed with real non-zero `volume` (BTC 24h: `volume=28140.06`). ASTER excluded pending its own
      manifest-registration gap, since RESOLVED — re-scoped + backfill launched
      (`/plans/archive/issues/aster_raw_capture_manifest_registration_gap_2026_07_26.md`). Repo:
      market-data-processing-service (no diff needed — infra/VM execution only).
- [x] ✅ **DONE (substantially) 2026-07-26 — full-range VM in progress, not yet 100%.** Backfill VM
      `mdps-backfill-cefi-20260726-165959` (`trades`, 2024-01-01→2026-07-25,
      HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET) launched and confirmed healthy/advancing per
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s Progress Log; a recent-window verification VM independently
      confirmed real candle output for a recent day. Manifest-verified full-range completion is blocked on the separate
      universal MDPS candle-manifest-emission bug
      (`/plans/archive/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`) — the live write path cannot
      register these rows in the manifest today for ANY venue, so full-range coverage confirmation must go through that
      issue's own `rebuild_manifest_from_canonical_paths` reconciliation once fixed, not the live write path. ASTER
      stays excluded per the item above.

## Phase 3 — wire ADV into strategy-side volume caps (RULED 2026-08-08 — implementation not yet started)

- [x] ✅ [DESIGN] P2. Design + implement the strategy-side consumption of the ADV signal: position-size cap as a % of
      ADV, and the min-7-day-history-to-trade gate the operator asked for. **RULED (operator, 2026-08-08)**: cap applies
      **at order-sizing time**, ceiling **10% of ADV** — filed as `[BACKEND]` below.
- [x] ✅ [BACKEND] P2. Implement the 10%-of-ADV position-size cap at order-sizing time in
      `AllocationSizer.size_signal()`, per the 2026-08-08 ruling above. **DONE
      (cefi_satellite_ao_dispatch_batch12_2026_08_09.md todo 2, 2026-08-09)** — `strategy-service@73aa792f`: clamps
      `PerClientSignal.allocation_amount_usd` to `min(computed_size, 0.10 * adv_usd)` via a new T4-local
      `strategy_service/engine/core/rolling_adv_reader.py` (mirrors features-service's verified-correct `adv.py` logic
      locally, since T4 services have no service-to-service import path per
      `/codex/04-architecture/tier-and-import-architecture.md`), fail-closed on `INSUFFICIENT_HISTORY`/`NO_DATA`.
      Covered by 8 new/updated unit tests, `quality-gates.sh` green (sentinel-verified).
- [ ] [DATA] P3. _(stretch, optional)_ Consider whether `book_depth.py`'s currently-unfilled `adv_30d_usd` input should
      be wired to call the SAME Phase-1 utility with `window_days=30`, now that a real producer exists — out of scope
      for this plan, a candidate follow-up once Phase 1 ships.

## Deferred work after 2026-07-21

| Item                                     | Status      | Why deferred                                                  |
| ---------------------------------------- | ----------- | ------------------------------------------------------------- |
| Phase 2 (MDPS candle coverage extension) | Not started | Operator explicit decision — consumer-first, producer later   |
| Phase 3 (strategy-side wiring)           | Not started | RULED 2026-08-08 (order-sizing time, 10% ADV) — build pending |
| `book_depth.py` → Phase-1 utility wiring | Not started | Stretch, only after Phase 1 ships and proves out              |

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid overall — the Phase-3 `[BACKEND] P2`
  implementation todo is now bounded/deterministic per today's 2026-08-08 ruling (clamp `AllocationSizer.size_signal()`
  to `0.10 * adv_usd`, fail-closed on non-`OK` `AdvStatus`), but the sibling `[DATA] P3` `book_depth.py` stretch item
  ("consider whether... should be wired") is a genuine open judgment call, not yet decided either way. Per the HARD RULE
  (`assigned_vm` flips WHOLE-DOC only, every remaining open item must be worker-determinable), the doc cannot flip while
  that stretch item stays open. Cross-checked against `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` (today's
  independent full-corpus audit), which reached the same verdict via its own "Deferred — human-only" list.
  **Recommendation for the next `/ag-closeout-audit` cefi batch (batch11)**: extract the Phase-3 backend todo alone into
  a satellite AO-dispatch item (leaving this source doc's stretch item open/NA) — not executed in this pass, since
  satellite-batch authoring is that skill's own numbered sequence, not this sweep's mechanism.
