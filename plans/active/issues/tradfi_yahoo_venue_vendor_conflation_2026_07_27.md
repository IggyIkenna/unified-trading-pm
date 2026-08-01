---
doc_type: issue
title:
  'market-tick-data-service''s YahooFinanceAdapter stamps venue="YAHOO" (a vendor) for every tradfi instrument, not the
  real venue — same conflation class as the just-fixed sports odds_horizon_bucket bug, NOT investigated or fixed here'
summary: >-
  `market_tick_data_service/market_interface/adapters/tradfi/yahoo_finance_adapter.py`'s `write_canonical_shard`
  unconditionally stamps `venue="YAHOO"` on every written row (`row["venue"] = "YAHOO"` + the `write_tradfi_shard(...,
  venue="YAHOO", ...)` call), for ALL three instrument_type classes it serves (CURRENCY/FX pairs, INDEX like `^VIX`, and
  EQUITY plain tickers) — "YAHOO" is the data VENDOR (yfinance/Yahoo Finance), not a real venue/exchange. This is
  structurally the same conflation class just fixed in MDPS's `reprocess_sports_odds.py` (venue=ODDS_API stamped on
  every fine manifest row instead of the real per-row bookmaker, even though the real identity was resolvable) — see
  `plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Phases 0-3 for that precedent's full
  investigation/fix/migration methodology. Filed per that task's explicit instruction to track this as a separate,
  precisely-scoped finding WITHOUT investigating or fixing it in this pass — the consumer-safety analysis (does anything
  filter on venue="YAHOO" specifically, is a real per-instrument venue/exchange even resolvable from Yahoo's API
  responses, what would the correct value be for an FX pair with no single exchange) has NOT been done.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, yahoo, venue, data-correctness, manifest, vendor-conflation]
related:
  [
    /plans/archive/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/venue-availability.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
scope_note: >-
  Filed as a precisely-scoped FINDING, not a fix — out of scope for the task that discovered it
  (mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md Phase 3, explicit operator instruction: "Do NOT fix this in this
  task — just file it as a new, separate, precisely-scoped issue doc... referencing this fix as precedent, so it's
  tracked and not lost, but out of scope to actually fix here").
source: >-
  Found during `mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md`'s Phase 0 investigation of the sports
  odds_horizon_bucket venue=ODDS_API conflation, while confirming that fix's finding wasn't ALSO present elsewhere in
  the codebase. Not independently re-derived here beyond a direct code read of the cited file.
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/venue-availability.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
---

# TradFi YahooFinanceAdapter stamps venue="YAHOO" (vendor) instead of a real per-instrument venue

## What I found (2026-07-27, direct code read only — no live-data/consumer trace performed)

`market_tick_data_service/market_interface/adapters/tradfi/yahoo_finance_adapter.py`:

```python
def write_canonical_shard(self, records, ticker, data_type, day, bucket, instrument_type=None):
    ...
    it = instrument_type or self._classify_yahoo_ticker(ticker)
    rows: list[dict[str, object]] = []
    for rec in records:
        row = dict(rec)
        row["venue"] = "YAHOO"
        row["symbol"] = ticker
        rows.append(row)
    return write_tradfi_shard(
        rows,
        venue="YAHOO",
        instrument_type=it,
        data_type=data_type,
        day=day,
        bucket=bucket,
    )
```

The module docstring confirms this is unconditional across every instrument_type this adapter serves: _"venue (`YAHOO`),
instrument_type (`CURRENCY` for FX pairs, `INDEX` for `^VIX`, `EQUITY` for plain tickers)"_ — i.e. every row written
through this adapter, regardless of whether it's an FX pair, a volatility index, or a plain equity ticker, gets
`venue="YAHOO"`. "YAHOO" is the data VENDOR (the yfinance library / Yahoo Finance's aggregation service), not a
venue/exchange in the sense the rest of the tradfi manifest uses the column (per
`/codex/02-data/tradfi-databento-sourcing-ssot.md`, real tradfi venues are exchanges like CME/ICE/NASDAQ/NYSE).

## Why this looks like the same conflation class as the sports fix (structural similarity, not a proven identical bug)

The sports `odds_horizon_bucket` bug (see the related issue doc) had the same shape: a vendor identifier (`ODDS_API`)
was stamped as `venue` when a real, more specific identity was available. The Yahoo case is structurally similar
(`YAHOO` the vendor stamped as `venue`) but is **NOT confirmed to be the same bug** — unlike the sports case, where the
real bookmaker was ALREADY present as a column in the underlying data (making the vendor-as-venue stamp a clear,
provable defect), it has NOT been checked here whether:

1. Yahoo's API responses even carry a resolvable "real exchange" per row for FX pairs (an FX cross like EUR/USD has no
   single exchange — this may be a case where "YAHOO" or some other vendor-level identity is the ONLY defensible value,
   unlike sports bookmakers which are always real, distinct, resolvable entities).
2. Any consumer (features-service, ml-service, manifest coverage/enumeration) filters on `venue="YAHOO"` explicitly in a
   way that a fix could break (the sports fix's single biggest regression risk, per that task's Phase 0).
3. What the "correct" venue value would even be for each of the three instrument_type classes (EQUITY tickers DO trade
   on a real, resolvable exchange like NASDAQ/NYSE; INDEX/CURRENCY may not).

## Not performed here (deliberately, per scope)

- No trace of `write_tradfi_shard`'s manifest-write path or the resulting `_index/availability_index.parquet` rows.
- No check of whether `/codex/02-data/tradfi-databento-sourcing-ssot.md` or any other codex doc already documents this
  as intentional (a quick related-doc read did not surface one, but this was not an exhaustive search).
- No consumer trace (features-service / ml-service / manifest enumeration) for a `venue="YAHOO"` dependency.
- No row-count/blast-radius measurement against the live manifest.

## Recommended next step

Treat as a genuine candidate for the SAME investigation methodology the sports fix used (Phase 0: reconcile real
counts + trace consumers for a venue="YAHOO" dependency; Phase 1: fix the writer if genuinely wrong, preserving any
consumer-relied-upon "give me all Yahoo data" query path; Phase 2: migrate existing rows if scale requires it) — but
only once resolvable per-instrument venue identities are confirmed to exist and be worth the migration cost for FX/INDEX
classes (EQUITY looks like the clearest win, since a real exchange is normally resolvable per ticker).

## Todos

> **NOTE (na-eligibility-audit 2026-07-30, tradfi tranche) — KEEP-NA-STALE, do NOT reclassify.** This doc's sole todo is
> already claimed VERBATIM by `/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md` ("Run the Phase-0
> YAHOO_FINANCE venue-vendor-conflation investigation methodology already defined in the doc", whose `Source:` cites
> this doc by name, and which explicitly sequences it FIRST among its three entangled Yahoo/venue todos). That batch doc
> is `assigned_vm: planning` but **`status: draft`** — NOT ingested, NOT dispatched today. Flipping this doc's
> `assigned_vm` would dispatch a duplicate AND break batch5's deliberate run-once-cite-thrice sequencing across the
> three Yahoo-axis docs, so the shared conflict-check
> (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) verdict is CONFLICT → citation fix
> only. Live blocker = batch5's draft status (operator item 5 in
> `/plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md`).

- [ ] [DATA] P2. **Run the Phase-0 investigation methodology** (reconcile real counts + trace consumers for a
      `venue="YAHOO"` dependency) before deciding whether/how to fix the vendor-as-venue stamp — per "Recommended next
      step," this has NOT been done yet.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA-STALE — citation fixed, `assigned_vm` deliberately
  unchanged.** The sole todo is a bounded, precedented investigate-only task (the sports `venue=ODDS_API` Phase-0
  methodology, named entry point `yahoo_finance_adapter.py::write_canonical_shard`) and would otherwise be a clean
  RECLASSIFY. Conflict-check returned CONFLICT: `/plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`
  already extracts it verbatim citing this doc as its `Source:`, and explicitly sequences it FIRST among three entangled
  Yahoo/venue todos so the investigation runs once and is cited by the other two.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-01** (tradfi tranche): **KEEP-NA-STALE, re-verified — citation still accurate.** Sole
  open todo re-read; count matches tranche-inventory tool (1). No content change since the 2026-07-30 verdict — only a
  context-scout `context_scope` backfill touched the file since. Conflict-check basis unchanged: batch5 still extracts
  this todo verbatim and still sequences it first among the three entangled Yahoo/venue todos.
