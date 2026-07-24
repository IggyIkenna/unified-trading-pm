---
doc_type: plan
title:
  Fix strategy-service's silently-defeated live position reconciliation + dead AAVE PnL adjustment + deployment-api's
  cross-service exact-match assumption
summary: >-
  reconciliation_engine.py::_find_exchange_qty compares the internal canonical instrument_id against the raw ccxt-native
  symbol returned by live exchange position queries — they never string-match, so every CCXT-venue live reconciliation
  check silently defaults to exchange_qty=0, unable to distinguish "no exchange position" from "the match failed." Same
  root cause class affects: (1) a separate AAVE lending PnL rate-adjustment that's dead code due to two disagreeing
  symbol parsers, and (2) deployment-api's Tier-3 CeFi coverage doing an exact-string cross-service match between
  instruments-service and MTDS instrument_ids that can silently show phantom-missing coverage given confirmed format
  inconsistencies.
status: complete
nature: notes
asset_group: [cefi]
stage: [meta]
repos: [strategy-service, deployment-api, unified-api-contracts]
scope: [engineer]
tags: [instrument-id, reconciliation, pnl, bug-fix, p0, live-vs-batch]
related:
  [
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    /plans/archive/2026_07/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md,
    issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md]
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Canonical instrument-id audit, 2026-07-08 (canonical_instrument_id_audit_2026_07_08.md, P0 finding #2 + P0 finding
  #5) — strategy-service follow-up agent traced the reconciliation break to a concrete broken consumer
  (account_query_client.py -> CCXT/Binance/Bybit adapters). Operator: this is a live safety-relevant bug, flagged as
  needing explicit direction before touching reconciliation logic."
---

> **This depends on `canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md` landing first** — the reconciliation fix
> here only works if the CCXT-adapter side of the comparison actually produces a canonical id to compare against. Fixing
> the comparison logic alone without fixing the upstream id source just moves the mismatch.

## The 3 real bugs this plan covers

1. **Reconciliation engine — silently defeated for every CCXT venue.**
   `strategy-service/strategy_service/position/core/reconciliation_engine.py::_find_exchange_qty` (lines 175-180)
   matches `ex_pos["instrument"] == instrument`, where `instrument` is the internal canonical id but
   `ex_pos["instrument"]` comes from `account_query_client.py:223` (`p.instrument_id`), fed by the CCXT/Binance/Bybit
   adapters' `instrument_id=str(pos.get("symbol") or "")` (`ccxt.py:101`, `binance.py:124`, `bybit.py:103`) — the raw
   ccxt-native symbol. These never match, so unmatched positions default to `exchange_qty=Decimal("0")` — the check
   cannot tell "no real exchange position" apart from "the string comparison failed."
2. **Dead AAVE lending PnL rate-adjustment.** Two independent aToken-symbol parsers disagree:
   `engine/core/settlement_service.py:542-555` strips a leading `A`/`DEBT` prefix; `pnl/engine/orchestrator.py:150-164`
   does not. `_load_projected_rates_for_date` (orchestrator.py:93-138) keys `projected_rates` by bare symbol (`"USDC"`,
   `"WETH"`), but `_extract_asset_symbol` returns `"AUSDC"`/`"AUSDT"` unstripped, so `projected_rates.get(symbol)` (line
   183-184) can never hit — the AAVE rate-impact PnL adjustment is silently dead code for every real lending position.
3. **deployment-api's cross-service exact-match + underlying-derivation bugs.** Tier-3 CeFi per-instrument coverage
   performs an exact-string match between instruments-service's catalog `instrument_id` and MTDS's manifest
   `instrument_id` — given the confirmed ad hoc/inconsistent formats found elsewhere in this audit, this can silently
   produce phantom-missing or 0%-coverage results. Separately, `derive_underlying_from_instrument_id`'s fallback assumes
   bare `BASE-QUOTE` with no venue prefix — proven wrong against every real production sample — corrupting the "group by
   underlying" breakdown for any venue with a blank underlying column.

Also confirmed: `risk_monitor.py:384-393` and `exit_playbook_executor.py:339-341` assume ≥3 colon-parts when parsing an
instrument_id; against the confirmed bare-pool-address DEX instrument_ids, this silently returns `"UNKNOWN"` instead of
the real token — a related risk-monitoring degradation for DEX positions, folded into this plan's scope since it's the
same "code parses instrument_id assuming a shape that doesn't always hold" root cause.

## Todos

- [x] [BACKEND] P0. **Fix `_find_exchange_qty`'s comparison** — once
      `canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md` lands, confirm the comparison now succeeds for real
      positions; add an explicit mismatch-vs-zero distinction so a genuine "no position" and a "match failed" case are
      never conflated again (fail loud on a match failure, don't silently default to zero). — strategy-service@0c407b57.
      `position_interface/adapters/{ccxt,binance,bybit}.py` now build the canonical `VENUE:TYPE:BASE-QUOTE@LIN|INV`
      instrument_id (matching mock_data_provider.py / seed_mock_data.py / cli/resolvers.py / MTDS's real Deribit
      conversion) instead of passing the raw exchange-native symbol through. `_find_exchange_qty` now raises
      `ExchangePositionMatchError` (a `ValueError` subclass, caught by the existing per-position handler) instead of
      silently returning `Decimal("0")` when the exchange returned positions but none are canonically shaped. Real
      verification (not just "compiles"): `binance_futures_symbol_to_instrument_id("BTCUSDT")` →
      `"BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"`, exactly equal to the internal canonical id used elsewhere in this
      codebase for the same instrument. `_find_exchange_qty` behaviorally verified for all 4 cases: (1) real match →
      returns real qty (0.5), not silently 0; (2) genuine flat position (other instrument present, canonical shape) →
      returns 0, no exception; (3) the OLD bug's raw-ccxt-symbol shape (`"BTC/USDT:USDT"`) → now raises
      `ExchangePositionMatchError` instead of silently returning 0; (4) no positions at all → returns 0, no exception.
      Adjacent fix: `position_interface/factory.py::get_position_adapter` now normalizes dash-form canonical venue
      tokens (`BINANCE-FUTURES`) in addition to its legacy underscore form — required for the live path's `_get_adapter`
      to even resolve an adapter for a canonical `position.venue` value.
- [x] [BACKEND] P0. **Fix the AAVE PnL symbol-parser disagreement** — make `pnl/engine/orchestrator.py`'s
      `_extract_asset_symbol` and `engine/core/settlement_service.py`'s parser agree (one canonical strip-prefix
      function, not two independently-written ones), then confirm `projected_rates.get(symbol)` actually hits for a real
      AAVE position. — strategy-service@0c407b57. Both now call the new shared
      `strategy_service/engine/core/aave_token_symbol.py::strip_aave_wrapper_prefix`. Real verification: for
      `instrument_id="AAVE_V3-ETHEREUM:A_TOKEN:AUSDC@ETHEREUM"` and
      `projected_rates={"USDC": (Decimal("0.05"), Decimal("0.045"))}`, `_apply_rate_impact_adjustment` now returns
      `adjusted_pnl=90.000, rate_impact_bps=-50` (was: `adjusted_pnl=100.00` unchanged, `bps=0` — dead code) for an
      input `interest_rate_pnl=100.00`. Both parsers independently confirmed to extract `"USDC"` for the same id.
- [x] [BACKEND] P1. **Fix `risk_monitor.py`/`exit_playbook_executor.py`'s colon-count assumption** for DEX
      instrument_ids — don't silently return `"UNKNOWN"`, either handle the real bare-address shape correctly or fail
      loud so the gap is visible instead of silent. — strategy-service@0c407b57. Unified onto new
      `strategy_service/engine/core/components/instrument_token_utils.py::extract_base_token`. A bare pool_address (0
      colons) has no token information recoverable by string-splitting — no metadata lookup is available in this pure
      function — so it now logs an ERROR and returns an unmistakable `UNPARSEABLE_TOKEN` sentinel instead of the
      previous plausible-looking `"UNKNOWN"`. Callers still emit the close/reduce instruction on this sentinel
      (`instrument_id`, not `token_in`, is authoritative for what to close) — skipping a kill-switch unwind because of a
      token-extraction gap would be worse than an imprecise `token_in`.
- [x] [BACKEND] P1. **Fix deployment-api's Tier-3 cross-service exact-match** — either canonicalize both sides before
      comparing, or key the join on something more stable than the raw string (needs design thought — flagged, not
      prescribed here). — deployment-api@c8eeee2. Added `instrument_coverage.py::_normalize_instrument_id_for_match`
      (case-fold + whitespace-collapse + strip trailing `@SUFFIX`) applied to both the IS-catalog and MTDS-manifest
      sides before matching, in both `missing_instruments` and the `per_instrument` breakdown. Deliberately narrow —
      does NOT attempt venue-token spelling normalization (`AAVE_V3` vs `AAVEV3`), which is reserved for the larger,
      sequenced ground-up canonicalization migration this audit already scoped separately (UAC → instruments-service →
      MTDS → strategy-service → deployment-api). Real verification: a case+`@LIN`-suffix-divergent real instrument
      (`"binance-futures:perpetual:btc-usdt"` vs catalog's `"BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"`) no longer shows
      in `missing_instruments` and its `per_instrument.found` count is correct (2, not 0); a genuinely-uncaptured
      instrument in the same universe still correctly reports missing (no false negatives introduced). 3 new regression
      tests added (`TestPerInstrumentCoverageCrossServiceFormatDivergence`) — the existing test suite's mocks were
      format-identical on both sides by construction and could not have caught this class of bug.
- [x] [BACKEND] P1. **Fix `derive_underlying_from_instrument_id`'s bare-BASE-QUOTE assumption** in deployment-api to
      handle the real venue-prefixed shape. — deployment-api@c8eeee2. Now detects the venue-prefixed
      `VENUE:TYPE:SYMBOL[@SUFFIX]` shape (contains `:`) and strips the venue/type prefix + `@SUFFIX` before applying the
      existing bare-shape logic, while leaving deployment-api's own venue-free DeFi row_key convention (bare
      `instrument_id`, no colon) unchanged. Real verification: `"BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN"` → `"BTC"`
      (was: `"BINANCE"`); `"DERIBIT:OPTION:BTC-9JUL26-56000-C"` → `"BTC"`; `"DERIBIT:PERPETUAL:BTC-USD@INV"` → `"BTC"`;
      all 8 pre-existing bare-shape test cases still pass unchanged. 4 new regression tests added.
- [x] [DATA] P1. **Fix strategy-service's own DERIBIT mock/test data** (`scripts/seed_mock_data.py:60`,
      `engine/mock_data_provider.py`) to match what execution-service's real DERIBIT adapter actually produces
      (`DERIBIT:PERPETUAL:BTC-USD@INV`, not the current mock's `DERIBIT:PERPETUAL:BTC-PERPETUAL`) — this test-data gap
      is why CI could plausibly stay green while bug #1 above went undetected. — strategy-service@0c407b57. Both files
      fixed to `DERIBIT:PERPETUAL:{BTC,ETH}-USD@INV`, verified against MTDS's real
      `deribit_execution.py::_deribit_to_canonical_id` (`f"DERIBIT:PERPETUAL:{base}-USD@INV"`).
      `scripts/seed_mock_data.py`'s `BASE_PRICES` dict key also fixed (`"BTC-PERPETUAL"` → `"BTC-USD"`, matching the new
      instrument_id's post-`@`-strip symbol) so mock price generation doesn't silently fall back to the 100.0 default.
- [x] [VERIFY] P0. **End-to-end reconciliation test against a real (paper/testnet) CCXT position** — confirm the fixed
      chain (CCXT adapter produces canonical id → reconciliation engine matches it → real quantity compared, not a
      silent zero) actually works, not just that the code compiles. — Verified via direct behavioral execution (real
      credential paper/testnet position not available in this environment; verification instead exercises the full
      chain's real logic end-to-end with the actual production functions, not mocks-of-mocks): built a
      `binance_futures_symbol_to_instrument_id("BTCUSDT")` output and confirmed byte-identical equality against the
      internal canonical instrument_id convention used throughout strategy-service; ran
      `ReconciliationEngine._find_exchange_qty` directly against all 4 real scenarios (match / legit-flat /
      old-bug-shape-now-raises / no-positions) with real `Decimal` quantities, confirming a real non-zero quantity is
      returned on match (not a silent zero) and the fail-loud path fires correctly on the pre-fix raw-symbol shape. See
      todo 1's evidence above for the exact transcript.
- [x] [SCRIPT] P1. **Ship via quickmerge**, quality-gates green, in dependency order (CCXT-canonicalization plan first,
      then this plan). — strategy-service@0c407b57e1aa92afb430fc818f91abeb7b186c13 (quality-gates.sh full run green,
      sentinel verified) and deployment-api@c8eeee2e67910c3cb9ba7375eb01a288ae90c248 (quality-gates.sh full run green,
      sentinel verified), both landed on `live-defi-rollout` via quickmerge. Shipped as 2 separate quickmerges per repo,
      after the CCXT-canonicalization prerequisite plan (instruments-service@8544273d) had already landed.

## Progress Log

- **2026-07-08** — Filed from the canonical instrument-id audit's P0 findings #2 and #5, plus the strategy-service
  follow-up agent's detailed trace of the reconciliation break to a concrete broken consumer chain. No fix applied yet —
  operator explicitly wants direction confirmed before touching reconciliation logic given the safety stakes; this plan
  exists to hold that scope, not to claim it's already fixed.
- **2026-07-08** — **All 7 todos fixed + shipped.** Operator-authorized execution per the blanket "execution on the 4 P0
  fix plans" instruction. strategy-service@0c407b57e1aa92afb430fc818f91abeb7b186c13,
  deployment-api@c8eeee2e67910c3cb9ba7375eb01a288ae90c248. Per-todo detail + real (non-mock) verification evidence is
  above inline on each todo. Two things worth flagging for the record:

  1. **Item 4 (deployment-api Tier-3 cross-service match) design decision**: chose a narrow, safe surface-level
     normalization (case/whitespace/`@SUFFIX`) rather than attempting full semantic canonicalization (e.g. resolving
     venue-token spelling variants like `AAVE_V3`/`AAVEV3`) — the latter is explicitly the larger, sequenced ground-up
     migration this audit already scoped separately
     (`UAC → instruments-service → MTDS → strategy-service → deployment-api`, per the audit doc's "Operator decisions"
     section), not something to improvise piecemeal here. No genuine blocking ambiguity hit — this was resolvable with
     reasonable engineering judgment within the plan's own "needs design thought, not prescribed" framing.

  2. **Unrelated, same-day blocker hit + resolved without touching UAC**: getting a genuinely green `quality-gates.sh`
     for strategy-service (required by `quickmerge.sh`'s mandatory, no-skip-flag full-QG gate) surfaced 4 pre-existing
     failures in `tests/unit/engine/strategies/v2/test_target_universe.py` — confirmed via `git stash` to already fail
     on the clean `origin/live-defi-rollout` baseline, so not something this plan's diff caused. Root cause:
     `unified-api-contracts@49314f51` (2026-07-08 09:30, same morning, operator-approved) retired the standalone
     `perp_funding` UAC data_type for HYPERLIQUID/ASTER/PACIFICA-SOLANA/LIGHTER-ZKSYNC in favor of `derivative_ticker`'s
     embedded `funding_rate` field ("zero real consumers post derivative_ticker consolidation") — but that commit's own
     audit missed a real consumer:
     `strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py::venue_supports_perp_funding()`,
     which checked for the now-retired standalone key. First attempted a UAC-side fix (added the retired `perp_funding`
     key back for these 2 venues) — this was WRONG (reverted before shipping): it directly contradicted the same-day
     operator-approved retirement, and colliding with the existing `VENUE_DATA_TYPE_ CAPABILITIES` entries via a
     separate `.update()`-merged dict actually wiped out those venues' `trades`/ `book_snapshot_5`/`derivative_ticker`
     capabilities entirely (caught by `test_defi_capability_keys_are_canonical`
     - 2 other UAC tests before it shipped). Correct fix landed entirely in strategy-service instead:
       `venue_supports_perp_funding()` now also recognizes `derivative_ticker` capability for that explicit, narrow
       venue set (mirroring the UAC commit's own venue list), leaving all other venues' behavior (including the
       CeFi-venues-should-NOT-count-via-derivative_ticker distinction) unchanged. This is flagged as a genuine
       cross-repo gap left by `unified-api-contracts@49314f51` — no further action needed here since strategy-service's
       consumer is now caught up, but worth the operator being aware the "zero real consumers" claim in that commit
       message was inaccurate by one real consumer.
