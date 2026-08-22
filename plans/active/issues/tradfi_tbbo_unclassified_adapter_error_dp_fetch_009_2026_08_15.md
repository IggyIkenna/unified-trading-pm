---
doc_type: issue
title: TradFi tbbo/NYSE+NASDAQ — 1584 fresh attempted_failed(UNCLASSIFIED_ADAPTER_ERROR) rows, DP-FETCH-009 page, capability-gate bypass suspected
summary: >-
  DP-FETCH-009 escalation agt-9b0feb paged on asset_group=tradfi data_type=tbbo (1584 of 15249 attempted, 10.4%,
  "Fresh"). Live read of the tradfi `_index/availability_index.parquet` confirms this is NOT the already-registered
  billing-gated-by-design pattern (`known_dead_cells_registry.py` covers tradfi/mbp_10 and tradfi/ohlcv_15m only): all
  1584 rows carry `error_reason=UNCLASSIFIED_ADAPTER_ERROR` (a value the codebase itself documents as "any
  record_failed callsite producing this reason in production is a bug in the calling adapter" —
  `unified_api_contracts/canonical/crosscutting/honest_coverage.py`), venues NYSE (1164) + NASDAQ (420), all
  `attempted_at` between 2026-08-15T13:12Z and 14:29Z (today, ~77-minute window — a single fresh run, not a static
  backlog), shard dates 2024-07-01/07-02, `source=databento`, `pipeline_mode=batch_databento`, `instrument_id` shape
  `NASDAQ:EQUITY:ABNB-USD` etc.

  Critically, `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`'s
  `VENUE_DATA_TYPE_CAPABILITIES["NYSE"]` / `["NASDAQ"]` do NOT declare `tbbo` at all (only `ohlcv_1m`/`ohlcv_1s`/
  `ohlcv_1h`) — the same structural gate the sibling issue doc
  `tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md` describes for CME (`get_expected_data_types_for_venue`
  intersects every fetch request against this list; `venue_fetch.py` never lets an undeclared data_type reach the
  Databento fetch call). If that gate is honored, tbbo for NYSE/NASDAQ should be UNREACHABLE by the normal orchestrator
  path — yet 1584 real fetch attempts happened today. This strongly suggests a bypass path (a manual/scratch
  script or a non-standard entrypoint) drove this backfill outside `venue_fetch.py`'s capability gate AND outside
  `sentinels.py`'s `classify_venue_error()` pipeline (which is why the error_reason is the generic
  UNCLASSIFIED_ADAPTER_ERROR fallback rather than a classified Databento code).

  Also matches the pre-existing operator ruling in `tradfi_massive_dual_source_2026_05_28.md` (archived): "Equity/ETF
  tick-level trades+tbbo — OPERATOR DECISION RESOLVED: NOT needed for TradFi MVP (connector must still implement)" —
  so this backfill activity is likely out-of-scope work regardless of the classification bug.

  A genuinely separate, smaller bug was also found and left unfixed here pending confirmation it's worth a scoped
  patch: `unified_api_contracts/canonical/crosscutting/errors/tradfi.py`'s `VENUE_ERRORS_TRADFI["databento"]` entries
  (DATABENTO_SUBSCRIPTION_GUARD / DATABENTO_LOOKBACK_EXCEEDED / etc.) are keyed by the PROVIDER string `"databento"`,
  but `engine/orchestrator/sentinels.py`'s Tier-2/Tier-3 emitters call `classify_venue_error(venue, code_token)` with
  the MARKET venue (`"NYSE"`, `"CME"`, etc.) as the first arg, not `"databento"` — so for ANY tradfi Databento venue,
  a genuine DATABENTO_* code always misses `VENUE_ERROR_MAP[venue.lower()]` and the venue-agnostic `internal` fallback
  bucket (which also has no DATABENTO_* entries), producing `classify_venue_error()->None` and a degraded
  `f"UNCLASSIFIED:{code_token}"` string (per `sentinels.py:672` Tier-3) rather than the intended classified code. This
  does NOT by itself explain the literal `UNCLASSIFIED_ADAPTER_ERROR` string in the alert (that string never appears
  live in `market-tick-data-service`'s `engine/orchestrator/`, `market_interface/adapters/tradfi/`, or
  `unified-trading-library`'s `manifest_writer/*` per an exhaustive grep + a dedicated Explore-agent trace — it only
  appears in two cefi-scoped one-off migration scripts, `_rebuild_cefi_cf11.py` and `canonicalize_mtds_index.py`,
  neither of which should ever touch the tradfi bucket), but it is a real, confirmed, separate classification-quality
  gap worth closing.
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [tradfi, tbbo, dp-fetch-009, unclassified-adapter-error, capability-gate, classify-venue-error, databento, honest-absence]
related:
  [
    /plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-08-15
author: agt-9b0feb (data_pipeline_failure escalation worker, slot-33)
source: ["DP-FETCH-009 escalation agt-9b0feb, asset_group=tradfi data_type=tbbo, 1584/15249 attempted_failed (10.4%)"]
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
context_scope:
  [
    /plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    market-data-processing-service/market_data_processing_service/app/adapters/base_adapter.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/tradfi.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
last_updated: 2026-08-15
parent_epic: tradfi_master
priority: P1
---

# TradFi tbbo/NYSE+NASDAQ — fresh UNCLASSIFIED_ADAPTER_ERROR batch, DP-FETCH-009

> **CORRECTED 2026-08-19 (plan_reconciler, epic-scoped tradfi_master pass)**: the frontmatter `title:`/`summary:`
> above still lead with the original "capability-gate bypass suspected" hypothesis. That hypothesis is SUPERSEDED
> — this doc's own `## UPDATE 2026-08-15` section below says plainly "this is NOT a capability-gate bypass driving
> fresh Databento fetches"; the real, confirmed root cause is an MDPS `_get_local_timestamp_column` presence-only
> bug, fixed and shipped (`market-data-processing-service@c5e0d68bcf`, verified ancestor of
> `origin/live-defi-rollout` this pass). A reader who stops at the title/summary gets a materially wrong picture.
> Not rewriting the frontmatter `title:`/`summary:` in place (several corpus referrers cite this doc by its exact
> title text) — flagging here instead, at the point a reader actually lands.

## What I found

Live-verified via `deployment_service.data_pipeline_monitors.meta_targets.market_data_bucket("tradfi")`'s
`_index/availability_index.parquet` (GCS-streamed, column-projected, bounded via
`run-bounded-analysis.sh` — no ad-hoc full-corpus load):

- 1584 rows: `data_type=tbbo`, `capture_status=attempted_failed`, `error_reason=UNCLASSIFIED_ADAPTER_ERROR` (100% —
  zero other error_reason values in this set).
- `venue`: NYSE=1164, NASDAQ=420.
- `attempted_at`: min `2026-08-15T13:12:26.667735+00:00`, max `2026-08-15T14:29:16.804203+00:00` — a single ~77-minute
  run TODAY, not an aged static backlog (rules out the "just re-page the same old 14d-window backlog" pattern the
  cefi `(cefi, book_snapshot_5)` DP-FETCH-009 history in `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
  repeatedly hit).
- `date` (shard date, i.e. what day's tick data was requested): 2024-07-01 / 2024-07-02 only — a narrow 2-day window
  backfill, not a broad multi-year sweep.
- `source=databento`, `pipeline_mode=batch_databento`.
- `instrument_id` sample: `NASDAQ:EQUITY:ABNB-USD`, `NASDAQ:EQUITY:CME-USD`, `NASDAQ:EQUITY:QQQ-USD`,
  `NASDAQ:EQUITY:SPY-USD`, `NASDAQ:EQUITY:COIN-USD`, etc. — real, plausible equity tickers, not garbage/test data.

## Why this is NOT the known billing-gated-by-design pattern

`deployment-service/deployment_service/data_pipeline_monitors/known_dead_cells_registry.py`'s `KNOWN_DEAD_CELLS`
already suppresses `("tradfi", "mbp_10")` (CME, 2026-07-15 operator decision) and `("tradfi", "ohlcv_15m")` — both
because their `attempted_failed` population is a frozen, non-growing historical residue with a documented root cause.
This tbbo batch is the OPPOSITE shape: 100% fresh (all rows within one run today), and the error_reason
(`UNCLASSIFIED_ADAPTER_ERROR`) is not one of the expected billing-guard codes
(`DATABENTO_SUBSCRIPTION_GUARD`/`DATABENTO_LOOKBACK_EXCEEDED`/`DATABENTO_PAYMENT_REQUIRED`) that
`market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py::_classify_databento_exception`
would produce for an entitlement rejection. Registering `("tradfi", "tbbo")` in `KNOWN_DEAD_CELLS` to silence the page
would be masking a genuinely fresh, unclassified failure — explicitly banned
(`unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` "never write an empty/placeholder... never mask a
real failure"). I did not do this.

## The capability-gate contradiction (the strongest lead)

`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`:

```python
"NASDAQ": {
    "ohlcv_1m": "2023-04-15",
    "ohlcv_1s": "2023-04-15",
    "ohlcv_1h": "2026-01-01",
},
"NYSE": {
    "ohlcv_1m": "2023-04-15",
    "ohlcv_1s": "2023-04-15",
    "ohlcv_1h": "2026-01-01",
},
```

`tbbo` is absent from both. Per the sibling issue doc
`tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md`'s verified finding for CME,
`get_expected_data_types_for_venue(venue)` reads `VENUE_DATA_TYPE_CAPABILITIES.get(venue).data_types` directly, and
`venue_fetch.py`'s per-shard dispatch intersects every fetch request against that list — so tbbo for NYSE/NASDAQ
should be structurally unreachable through the normal orchestrator dispatch path, exactly like CME's
trades/tbbo/mbp_10. This matches the archived operator ruling in `tradfi_massive_dual_source_2026_05_28.md`:
"Equity/ETF tick-level `trades`+`tbbo` — OPERATOR DECISION RESOLVED: NOT needed for TradFi MVP (connector must still
implement)".

Yet 1584 real Databento fetch attempts for exactly this (asset_group, data_type, venue) combination happened today.
**I was not able to identify, within this one-shot escalation's budget, which code path issued these fetches** — I
grepped + dispatched a dedicated Explore agent across `market_tick_data_service/engine/orchestrator/` (including both
`sentinels.py` Tier-2 AND Tier-3 emitters), `market_interface/adapters/tradfi/databento_*.py`,
`engine/orchestrator/known_dead_shard_gate.py`, and `unified-trading-library`'s `manifest_writer/*` +
`legacy_reason_classifier.py`, and could not find a live call site that both (a) writes the literal string
`UNCLASSIFIED_ADAPTER_ERROR` and (b) would fire for a per-instrument NYSE/NASDAQ tbbo shard. The literal string exists
in this codebase ONLY inside two `Lifecycle: oneoff` cefi-scoped migration scripts
(`market_tick_data_service/scripts/_rebuild_cefi_cf11.py`, `market_tick_data_service/scripts/canonicalize_mtds_index.py`)
— neither should ever run against the tradfi bucket, and their transform preserves `attempted_at` (so if either had
run against tradfi it should NOT produce today's fresh timestamps unless the underlying rows were also fresh today
from a genuinely separate write, which loops back to the same open question).

**Leading hypothesis**: a manual/scratch script or a non-standard entrypoint (not `venue_fetch.py`'s normal gated
dispatch, not `sentinels.py`'s Tier-2/3 `classify_venue_error()` pipeline) directly drove a Databento tbbo backfill
for these two venues today, with its own naive `except Exception: record_failed(error="UNCLASSIFIED_ADAPTER_ERROR")`
(or equivalent) — consistent with both the capability-gate bypass AND the non-classified error string. This is
plausible manual "let's see if equity tbbo actually works now" exploration ahead of formally re-scoping the MVP.

## A separate, confirmed, smaller bug (found along the way, NOT the direct cause of this alert)

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/tradfi.py`'s `VENUE_ERRORS_TRADFI` dict
keys its Databento-specific classifications (`DATABENTO_SUBSCRIPTION_GUARD`, `DATABENTO_LOOKBACK_EXCEEDED`,
`DATABENTO_PAYMENT_REQUIRED`, `DATABENTO_ENTITLEMENT`, plus generic `RATE_LIMIT`/`AUTH_FAILURE`/`SERVER_ERROR`/etc.)
under the literal provider key `"databento"` — matching the convention `databento_symbology.py:120` uses
(`classify_venue_error("databento", "TimeoutError")`). But `market_tick_data_service/engine/orchestrator/sentinels.py`
Tier-2 (`~line 604`) and Tier-3 (`~line 638`) both call `classify_venue_error(venue, code_token)` with the MARKET
venue (`"NYSE"`/`"CME"`/etc.), not `"databento"`. Since `classify_venue_error()`
(`unified_api_contracts/canonical/crosscutting/errors/__init__.py:51`) only checks `VENUE_ERROR_MAP[venue.lower()]`
then the venue-agnostic `internal` bucket, and NEITHER has NYSE/NASDAQ/CME-keyed entries for the Databento codes, any
genuinely-classified Databento failure reaching this path for a tradfi venue silently degrades to
`f"UNCLASSIFIED:{code_token}"` (Tier-3) or the raw `code_token` (Tier-2) instead of the intended classified reason.
This is real and worth fixing but is NOT itself sufficient to produce the exact literal `UNCLASSIFIED_ADAPTER_ERROR`
observed in the alert (it would produce `UNCLASSIFIED:DATABENTO_SUBSCRIPTION_GUARD` etc., a different string) — so I
left it unfixed here pending the root-cause trace below, to avoid shipping a change I can't tie to the actual symptom.

## Why it matters

- **Billing/API-call waste**: 1584 real Databento API calls for structurally out-of-scope (not-yet-MVP) equity tbbo
  data, if the capability gate really is being bypassed.
- **Alert noise**: DP-FETCH-009 will keep re-paging (30-min re-nag cooldown) until this cell either goes quiet or gets
  a deliberate disposition — and it must NOT be silenced via `KNOWN_DEAD_CELLS` without first confirming it's
  genuinely the by-design billing-gated pattern (it currently is not).
- **A capability-gate bypass, if confirmed, is a data-pipeline-correctness HARD RULE concern** (CLAUDE.md "Data
  pipeline correctness is the heartbeat") — any code path that can write `attempted_failed` rows for a data_type the
  registry says is out of scope, without going through the same `classify_venue_error()` contract every other adapter
  path uses, is a latent honest-absence/classification-integrity gap that could recur for other venues/data_types.

## UPDATE 2026-08-15 (agt-bb295c, data_pipeline_failure escalation, slot-14) — root cause found, one bug fixed + shipped, one genuine scope decision remains

**This escalation re-fired on the SAME 1584-row population agt-9b0feb diagnosed** (identical counts: 1584/15249,
10.4%, NYSE=1164/NASDAQ=420, attempted_at 2026-08-15T13:12-14:29Z) — agt-9b0feb was a one-shot worker that
investigated but did not fix, so the still-`attempted_failed` cells re-triggered DP-FETCH-009 on the next scan.

**Correction to the leading hypothesis above: this is NOT a capability-gate bypass driving fresh Databento fetches.**
Direct GCS verification (`unified_trading_library.cloud_interface.get_storage_client().list_blobs(...)`, live prod
bucket `market-data-tick-tradfi-prd-central-element-323112`) found **134 real, pre-existing raw tbbo parquet files**
for NYSE+NASDAQ on 2024-07-01 alone (e.g.
`raw_tick_data/by_date/day=2024-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NASDAQ/instrument_type=equity/data_type=tbbo/NASDAQ:EQUITY:ABNB-USD.parquet`,
2099 real quote rows, `source=databento`) — a genuine historical capture, not a live bypass fetch (agt-9b0feb's own
manual GCS probe that found "no files" used the wrong casing, `instrument_type=EQUITY` vs the real lowercase
`instrument_type=equity` — a false negative, not evidence of absence). The manifest's own `service_name` column
(never checked by agt-9b0feb — a cheap, decisive check) confirms the actual writer:
**100% of the 1584 rows have `service_name=market-data-processing-service`** — this is MDPS's own downstream candle-
DERIVATION layer (reading MTDS's already-captured raw ticks), not a fetch-side bypass of `venue_fetch.py` at all.

**Root cause #1 (FOUND + FIXED + SHIPPED, `market-data-processing-service@c5e0d68bcf`):** MDPS's shared
`BaseCandleAdapter._get_local_timestamp_column()` (`app/adapters/base_adapter.py`) picks the local-timestamp column by
**presence alone** (`ts_init` → `local_timestamp` → `ts_event` → `timestamp`, first COLUMN THAT EXISTS wins). This
real tbbo capture has `ts_init` and `ts_event` present as columns but **100% null** — Databento's TBBO record type
for these equities apparently never populated them at write time — while `timestamp` (priority 4, "last resort")
carries valid, correctly-scaled microsecond-epoch data for every row. The old code always picked the unusable
`ts_init`, producing an all-NaT `processing_dt` in `_convert_to_processing_dt` — no warning fires because the
"dropped_out_of_bounds" counter only counts values that were newly invalidated by conversion, not inputs that were
already null. `TradfiTbboAdapter.process_to_candles`'s `tick_data["processing_dt"].dt.date.value_counts().idxmax()`
then crashes with a generic `ValueError: attempt to get argmax of an empty sequence` on an empty (all-NaN-excluded)
Series. This is a plain `ValueError` (not a typed `UpstreamTimestampBiasError`/`MalformedTickFieldError`), so
`_process_instrument_file`'s outer broad except in `live_workers.py` — which has no typed-error tier, unlike the
sibling per-timeframe loop in `live_workers_chain.py` — routes it to the generic
`_record_unclassified_failed_for_all_timeframes` → `error_reason=UNCLASSIFIED_ADAPTER_ERROR`. **Reproduced live**
against the real GCS object both before (crash) and after (succeeds, returns a real `CandleOutput`) the fix. The fix
is a minimal validity check (`col in df.columns and df[col].notna().any()`) — strictly additive, cannot regress any
caller whose priority-1 column already has data (only changes behavior for the previously-always-broken
present-but-null case), and is used by ~10 other adapters (trades, book_snapshot, liquidations, options_chain,
futures_chain, derivative, etc.) so it also closes this exact failure mode for any of them that hits the same shape.
`quality-gates.sh` green; shipped via quickmerge, `git merge-base --is-ancestor` verified on
`origin/live-defi-rollout`.

**Root cause #2 (FOUND, NOT FIXED — genuine operator-gated scope decision, do not guess):** fixing #1 let processing
reach the WRITE step, which immediately hit a second, distinct, pre-existing gap: `No SchemaContract registered for
asset_group='tradfi' instrument_type='EQUITY' data_type='tbbo_1m' venue='NASDAQ'. Add a contract to
unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY...` — reproduced on every one of the 134 real
files when I re-ran the exact narrow scope (`MDPS_DATA_TYPES=tbbo MDPS_VENUES='NYSE NASDAQ' ... --operation process
--mode batch --start-date 2024-07-01 --end-date 2024-07-02 --force`) to try to flip the cells to `captured`. A grep
of `unified_api_contracts/internal/schemas/contracts.py`'s `CONTRACT_REGISTRY` + `VENUE_CONTRACT_OVERRIDES` finds
**zero** `tbbo`-prefixed entries for ANY venue or instrument_type — tbbo candle-derivation output was never
schema-registered anywhere, not just for equities. Combined with the archived operator ruling already cited above
("Equity/ETF tick-level trades+tbbo — NOT needed for TradFi MVP"), this reads as an incomplete/never-finished MDPS
capability, not a regression — `TradfiTbboAdapter` exists and (after fix #1) runs correctly, but its output was never
wired to a write-time contract. **This is a genuine design/scope decision, not a mechanical bug** — I have NOT
invented a schema (that requires deciding the actual column set/dtypes for a tbbo-derived candle, real design
review, and cross-repo coordination with `unified-api-contracts`), and have NOT registered `("tradfi","tbbo")` in
`KNOWN_DEAD_CELLS` (deployment-service) either, because `is_known_dead()`'s own safety contract only suppresses
while `attempted_failed` activity stays at-or-before `narrowed_at` — registering it WITHOUT an accompanying capability
change would just be a hollow band-aid that re-breaks on the next narrow-scope backfill (exactly what happened here:
agt-9b0feb's session already saw this population once, uncorrected, and it re-paged).

**Recommended decision (posted to `/blocked` for the main agent / operator; recorded here regardless of a live
answer):**
- **Option A (recommended)** — gate MDPS's `data_type` scan against the SAME `VENUE_DATA_TYPE_CAPABILITIES` registry
  `venue_fetch.py` already uses on the fetch side, so MDPS naturally skips (`expected_unattempted`) a data_type the
  registry says is out of scope for a venue, instead of attempting real historical data with no output contract.
  Matches the ALREADY-DECIDED operator MVP-scope ruling with no new scope expansion; smaller, safer, single-repo
  change. Needs a real review of where to hook it in `orchestration_service.py`'s scan path without adding a new
  failure mode for OTHER data_types.
- **Option B** — design + register the missing `tbbo_1m`/etc. `SchemaContract` (any timeframe MDPS derives) for
  `instrument_type=EQUITY`, completing equity tbbo candle-derivation end-to-end. Only appropriate if the operator
  affirmatively wants this now, reversing the archived MVP-scope ruling — a real feature-completion decision, not a
  hot-fix.
- Until one ships, `("tradfi","tbbo")` will keep re-paging DP-FETCH-009 roughly every 30 min (the event's registered
  re-nag cooldown) whenever the detector re-scans — this is a KNOWN, EXPLAINED residual (not a silent gap), tracked
  here.

## Open work (tracked todos)

- [x] [SCRIPT] P1. Identify the exact code path (script/CLI/handler) that issued the 1584 tbbo/NYSE+NASDAQ Databento
      fetch attempts on 2026-08-15 13:12-14:29 UTC for shard dates 2024-07-01/07-02 — check GCP Cloud Run/VM launch
      history + any interactive/manual invocation in that window, and grep `market-tick-data-service` +
      `deployment-service` for any tbbo/equity backfill entrypoint that does NOT route through
      `venue_fetch.py`'s `get_expected_data_types_for_venue` capability gate. (repos: market-tick-data-service,
      deployment-service) — ✅ CORRECTED (agt-bb295c, 2026-08-15): not a fetch-side bypass at all. The 134+ real raw
      tbbo files are a pre-existing historical capture; the 1584 manifest rows are written by MDPS's own downstream
      candle-derivation (`service_name=market-data-processing-service`, confirmed via direct manifest read), which
      does not consult `venue_fetch.py`'s gate because it never fetches — it only reads MTDS's already-written
      parquet. See UPDATE above.
- [x] [SCRIPT] P1. Once the call site is found, route it through `classify_venue_error()` per the standard
      `record_failed` contract instead of a generic except-Exception fallback, and confirm it either honors
      `VENUE_DATA_TYPE_CAPABILITIES` (blocking tbbo for NYSE/NASDAQ, matching current MVP scope) or — if the operator
      has decided equity tbbo IS now in scope — file the corresponding registry + capability update as its own
      tracked change (not silently expanded via a bypass path). (repos: market-tick-data-service, unified-api-contracts)
      — ✅ SUPERSEDED (agt-bb295c, 2026-08-15): `classify_venue_error()` is fetch-side and not on this code path at
      all (see correction above). The REAL cause was a plain adapter bug (`_get_local_timestamp_column` presence-only
      selection) — fixed + shipped `market-data-processing-service@c5e0d68bcf`. The capability-honoring half of this
      todo is now Option A in the UPDATE's recommended decision, still open pending operator input.
- [ ] [SCRIPT] P2. Fix the `classify_venue_error(venue, code)` provider-vs-market-venue key mismatch for TradFi
      Databento venues: either alias `VENUE_ERRORS_TRADFI["databento"]`'s DATABENTO_* + generic HTTP-code entries
      under every Databento-backed tradfi market venue key, or change `sentinels.py`'s Tier-2/Tier-3 call sites to
      pass the actual data-provider key (`"databento"`) when the failure originated from a Databento adapter (needs a
      provider tag threaded through `failed_shards`/`failed_per_dt_by_venue`, since sentinels.py doesn't currently
      know which provider handled a given failed shard). (repos: unified-api-contracts, market-tick-data-service) —
      still valid/open, unrelated to the MDPS finding above; not attempted by agt-bb295c (out of this escalation's
      root cause).
- [ ] [BACKEND] P2. Per D133 ruling (2026-08-22): Option A chosen — gate out. Gate MDPS's tbbo data_type scan against
      `VENUE_DATA_TYPE_CAPABILITIES` (the same registry `venue_fetch.py` already uses on the fetch side) so MDPS
      naturally skips (`expected_unattempted`) tbbo for NYSE/NASDAQ instead of attempting real historical data with no
      output contract — matches the decided MVP scope with the smaller single-repo change; Option B (registering the
      missing `tbbo_1m` SchemaContract) would require affirmatively reversing that ruling. Once shipped, register
      `("tradfi","tbbo")` in `KNOWN_DEAD_CELLS` (mirrors `("tradfi","mbp_10")`) — registering it without the capability
      change first would be a hollow band-aid per `is_known_dead()`'s own re-arm-on-new-activity safety contract.
      (repos: deployment-service, market-data-processing-service, unified-api-contracts)

## Progress Log

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** Todo 4 is explicitly
  `[OPERATOR]`-tagged; doc's own text states plainly this is "a genuine design/scope decision, not a mechanical bug."
  Genuinely operator-gated. `assigned_vm` unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **KEEP-NA, valid — independent review
  declines to promote the `classify_venue_error()` todo (line 292) despite a Phase-1 hunter flagging it
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE.** The todo offers two structurally different fixes with no prescribed choice
  between them — (a) alias `VENUE_ERRORS_TRADFI["databento"]`'s entries under every Databento-backed tradfi venue
  key (a scoped registry edit), or (b) thread a provider tag through `sentinels.py`'s shared
  `failed_shards`/`failed_per_dt_by_venue` Tier-2/Tier-3 call sites (a cross-cutting change to shared
  shard-level-failure-isolation machinery, `/codex/04-architecture/shard-level-failure-isolation.md`) — picking
  between them is a design call, not pure execution, and per the "never re-litigate" clause's own caution about
  self-framed-bounded todos on live-dispatch-critical-path machinery (cf. the BLK-29884333 precedent,
  `regen_positional_task_ids_not_content_stable_2026_07_17.md`), a classifier's `ao_eligible: true` flag is a
  strong signal, not a final ruling. Todo (line 300, [OPERATOR] disposition decision) stays genuinely operator-gated,
  matching the 08-16 marker. Flagging line 292 MISCLASSIFIED_LIKELY_AO_ELIGIBLE for a future pass — worth resolving
  which of the two fix paths is intended (a scoped design note pinning one approach would likely clear it) rather
  than re-flagging indefinitely. `assigned_vm` unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Todo (`classify_venue_error()` provider-vs-market-venue
  key mismatch) stays flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE but not promoted — the two candidate fixes are a real
  design choice (scoped registry alias vs. a cross-cutting provider-tag threading change to shared shard-level-failure
  machinery), not pure execution. The `[OPERATOR]` disposition-decision todo stays genuinely gated. `assigned_vm`
  unchanged.
- **2026-08-22 — ruling D133 (Equity tbbo scope)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Gate out — matches the decided scope with the smaller single-repo change; the
  alternative requires affirmatively reversing a ruling. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
