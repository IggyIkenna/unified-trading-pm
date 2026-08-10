---
doc_type: issue
title:
  market-tick-data-service's Kalshi/Polymarket prediction adapters carry a whole dead "live REST-polling" interface —
  tested but never reached by any production code path
summary: >-
  Both `KalshiAdapter` and `PolymarketAdapter` in market-tick-data-service's `market_interface/adapters/prediction/`
  package define a `get_markets`/`get_prices`/`normalize_market`/`normalize_odds`/`parse_market`/`parse_token`/
  `parse_order_book`/`parse_trade`/`_convert_gamma_market`/`_build_order_book_record` method family that is exercised
  ONLY by unit/integration tests — zero production call sites anywhere in the repo. The actual live/batch pipeline is
  exclusively `download_batch()` -> `get_trades_batch()`/`get_books_batch()` -> the `_fetch_*_for_date` family. Two
  additional helper methods (`KalshiAdapter._load_tickers_from_gcs`, `PolymarketAdapter._load_condition_ids_from_gcs`)
  are explicitly self-labeled "Legacy wrapper" and have ZERO callers anywhere, not even in tests. `vulture` (corpus-wide
  dead-code detection) does not catch any of this because every symbol IS referenced — just only from test code — which
  is exactly the blind spot `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` was written to close.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [dead-code, adapters, prediction, kalshi, polymarket, adapter-dead-code-and-fallback-ban]
related:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/archive/2026_07/prediction_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: 2026-07-31
author: unknown
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-31 (slot-12, backend_engineer) while executing
    prediction_consolidated_native_ao_extract_2026_07_25.md todo 1's adapter dead-code/fallback audit, per
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md.",
  ]
resolved_by:
locked_by:
locked_since:
archive_exempt: true
supersedes:
superseded_by:
context_scope:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py,
  ]
---

# MTDS prediction adapters: dead live-REST-polling interface

## What I found

The production data path for both prediction adapters is exclusively the batch-download family:

```
download_batch() -> {get_trades_batch, get_books_batch} -> {_fetch_trades_for_date, _fetch_books_for_date}
                  -> {_annotate_cid_dataframe / _annotate_kalshi_ticker, _apply_lifecycle_gate / _collect_kalshi_frames}
```

Confirmed via repo-wide grep (excluding `tests/`) — every one of the following methods has ZERO non-test call sites:

**`market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py`** (`KalshiAdapter`):

- `parse_market()`, `parse_trade()`, `parse_order_book()` (lines 129-139)
- `normalize_market()` (141-172), `normalize_odds()` (174-190)
- `_load_tickers_from_gcs()` (476-484) — its own docstring says "Legacy convenience wrapper... Retained for callers that
  only need the ticker list" but grep confirms there are no such callers anywhere, including tests.

**`market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py`** (`PolymarketAdapter`):

- `get_markets()` (146-192), `get_prices()` (194-229), `_convert_gamma_market()` (110-144), `_build_order_book_record()`
  (231-250)
- `parse_market()`, `parse_token()`, `parse_order_book()` (252-262)
- `normalize_market()` (264-297), `normalize_odds()` (299-321)
- `_load_condition_ids_from_gcs()` (816-819) — self-labeled "Legacy wrapper — use `_load_instruments_from_gcs` for shard
  info", zero callers anywhere.

`normalize_market`/`parse_market`/`parse_order_book`/etc. ARE covered by
`tests/market_interface/unit/ test_prediction_adapters.py` and friends, and `PolymarketAdapter.get_markets`/`get_prices`
are covered by `tests/integration/test_polymarket_integration.py` — so this is real, deliberately-tested code, not a
stub. It reads like the remnant of an earlier live-REST-polling design (`get_markets`/`get_prices` naming and the
Gamma-API-only `ENDPOINT_STATUS = "IMPLEMENTED"` marker in polymarket_adapter.py both suggest a pre-`download_batch()`
architecture) that the batch/lifecycle-gated pipeline superseded without deleting the superseded interface.

This is exactly the class of gap `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` names explicitly: "a
module/class/function that is defined and registered somewhere... but never actually reached by any live code path is
dead code, even though `vulture` won't flag it (it IS referenced)" — referenced here by tests, not by any caller that a
production run would ever exercise.

## Why it matters

- ~200 lines of adapter surface area (two files) that nobody maintaining the live pipeline needs to reason about, but
  that every future adapter change/audit has to read past to find the actually-live code.
- Test coverage on dead code inflates the coverage numbers for files that need review attention on the parts that matter
  (the lifecycle-gating / CF-11 failure-signalling logic actually in the request path).
- If Kalshi/Polymarket ever DOES need a live-polling path again (vs. batch), reviving THIS code without re-verifying it
  against the current lifecycle-gating contract (`compute_lifecycle_window_ts`, CF-11 `attempted_failed` signalling)
  would silently reintroduce the exact classes of bug (silent-empty, no lifecycle gate) the rest of these two files were
  hardened against.

## Recommended decision

Not adjudicated here (genuine judgment call on scope, not auto-resolved):

- **(A) Delete** the dead methods + the two explicitly-legacy wrapper functions, and delete/trim the tests that only
  exist to cover them — cleanest, matches "Delete deprecated code (no shims)" (CLAUDE.md Governance rule).
- **(B) Keep, but document why** — if there's a near-term plan to revive a live-polling ingestion path (as opposed to
  batch-only), add a one-line note at each method (or a module docstring) stating that activation path explicitly, per
  the codex doc's "or document why it's intentionally kept (e.g. behind a feature flag with a stated activation path)"
  escape hatch. A vague "might be useful later" comment does not satisfy that bar.

## Todos

- [x] ✅ [BACKEND] P2. **RULED 2026-08-07 (operator) — DELETE (option A).** — market-tick-data-service@a0b4957e
      instruments-service finding (`is_polymarket_dead_fixture_cross_reference_2026_07_31.md`): prediction markets
      should get fixture/market availability from the canonical manifest/GCS-objects batch path, not a live-polling REST
      interface. Delete
      `KalshiAdapter.{parse_market,parse_trade,parse_order_book,normalize_market,normalize_odds,_load_tickers_from_gcs}` +
      `PolymarketAdapter.{get_markets,get_prices,_convert_gamma_market,_build_order_book_record,parse_market,parse_token,parse_order_book,normalize_market,normalize_odds,_load_condition_ids_from_gcs}`
      and their dedicated tests. (repo: market-tick-data-service)

## Progress Log

- **na-eligibility-audit 2026-07-31 (prediction tranche)**: KEEP-NA, valid — 1 open. Same shape as the sibling
  Polymarket dead-fixture finding filed the same day: the doc's own "Recommended decision" section explicitly frames (A)
  delete vs (B) keep-and-document as a genuine judgment call, not auto-resolved. Doc stays NA.
- **context-scout 2026-08-03**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-04 (prediction tranche)**: KEEP-NA, valid — 1 open, unchanged since the 2026-07-31
  marker (only intervening commit is the 2026-08-03 context-scout refresh; live-verified the dead REST-polling methods
  are still present unchanged in both adapters). Same shape as the sibling Polymarket dead-fixture finding: the doc's
  own "Recommended decision" section frames (A) delete vs (B) keep-and-document as a genuine judgment call, not
  auto-resolved. Doc stays NA.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA, valid — re-verified, 1 open, unchanged
  since the 2026-08-04 marker. The doc's own "Recommended decision" section still frames (A) delete vs (B)
  keep-and-document as a genuine judgment call, not auto-resolved; live-verified `KalshiAdapter._load_tickers_from_gcs`
  (kalshi_adapter.py) and `PolymarketAdapter._load_condition_ids_from_gcs` (polymarket_adapter.py) are both still
  present unchanged. Doc stays NA.
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: RULED — delete (option
  A). See Todos section above for the full ruling + rationale.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-09 (prediction tranche)**: KEEP-NA — re-verified, 1 open. Same shape as the sibling
  `is_polymarket_dead_fixture_cross_reference_2026_07_31.md`: the 2026-08-07 operator ruling (DELETE, option A) makes
  this bounded in isolation, but today's sibling `/ag-closeout-audit prediction` run already extracted this exact
  deletion into `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4 (`status: draft`, verbatim source
  citation), gated for reconciliation via `batch10_finalize`. Not independently reclassified — would create a duplicate
  AO-dispatch surface. Doc stays NA pending batch10's operator-approved dispatch + execution.
