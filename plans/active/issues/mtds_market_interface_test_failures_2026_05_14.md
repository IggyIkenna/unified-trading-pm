---
title: MTDS 53 market_interface unit test failures — mixed API drift + mock issues
created: 2026-05-14
author: slot-3 (harsh)
source:
  - market-tick-data-service/tests/market_interface/unit/
severity: P1
suggested_owner: operator triage
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## What I found

Running `pytest tests/market_interface/unit/` in `.tabs/3/market-tick-data-service` produces 53 failures across 5 test modules:

1. **`test_defi_handlers.py`** (≥2 failures) — `assert result["total_rows"] == 1` but got 2.
   - Likely cause: handler now counts rows for 2 venues (AAVEV3 + MORPHO) but test fixture expects 1.
   - Log output: `"liquidation_events for 2024-01-15: 2 rows total"` — handler produces 2, test expects 1.
   - Root cause: implementation changed to handle multiple venues; test expectation not updated.

2. **`test_defi_adapters_boost_2.py`** — `TestAlchemyBaseClient::test_get_rpc_url_unsupported_chain` failure.
   - Likely API shape drift in `AlchemyBaseClient`.

3. **`test_g9_regression_canonicalisation.py`** — `TestUnparseableDatabentoSymbolEventRegressionG9::test_classifier_failure_emits_event`.
   - Likely: classifier event shape or logging changed.

4. **`test_prediction_market_venue_wiring.py`** — `TestPredictionMarketVenueRegistry::test_remaining_planned_venues`.
   - Likely: venue registry membership drift; test expects specific set of planned venues.

5. **`test_tardis_stream_client.py`** (3 failures) — `TardisHTTPError: Tardis HTTP 404`.
   - Tests hit live network (`--block-network` not active or `@pytest.mark.allow_network` missing).
   - Tests should mock at the aiohttp session level per workspace testing standards.

All failures are pre-existing (present before my slot-3 Phase 0 Reserve work began). The unit tests at `tests/unit/` all pass (1062 passed after `9f5a4e3` Cluster D upstream fix landed).

## Why it matters

MTDS `bash scripts/quality-gates.sh` includes both `tests/unit/` and `tests/market_interface/`. With 53 failures in market_interface, QG cannot go green, blocking Phase 0 QG clean-start goal.

The `tests/unit/` suite is now clean. The market_interface suite needs targeted fixes per the 5 clusters above.

## Recommended decision

Assign to MTDS owner for next cycle. Cluster by root cause:

- **A** (defi_handlers row-count): Update test expectations to match new multi-venue handler (AAVEV3 + MORPHO dual-venue path). Clear diagnosis — test drifted from implementation.
- **B** (defi_adapters_boost_2, g9_regression): Read both sides of contract; likely test expectation drift from recent API shape change.
- **C** (prediction_market_venue_wiring): Sync venue registry membership expectations with current canonical venue list.
- **D** (tardis_stream_client): Wire `respx` / `aiohttp` mock at session level per testing standards; eliminate live network calls.

Not recommended: patching tests to pass without understanding the invariant (especially defi_handlers row-count and venue registry membership — those are data-correctness assertions).
