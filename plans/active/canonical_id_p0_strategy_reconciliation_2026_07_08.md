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
status: active
nature: notes
asset_group: [cefi]
stage: [meta]
repos: [strategy-service, deployment-api, unified-api-contracts]
scope: [engineer]
tags: [instrument-id, reconciliation, pnl, bug-fix, p0, live-vs-batch]
related:
  [
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md,
    issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    ../../codex/09-strategy/operational/paper-batch-live-reconciliation.md,
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

- [ ] [BACKEND] P0. **Fix `_find_exchange_qty`'s comparison** — once
      `canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md` lands, confirm the comparison now succeeds for real
      positions; add an explicit mismatch-vs-zero distinction so a genuine "no position" and a "match failed" case are
      never conflated again (fail loud on a match failure, don't silently default to zero).
- [ ] [BACKEND] P0. **Fix the AAVE PnL symbol-parser disagreement** — make `pnl/engine/orchestrator.py`'s
      `_extract_asset_symbol` and `engine/core/settlement_service.py`'s parser agree (one canonical strip-prefix
      function, not two independently-written ones), then confirm `projected_rates.get(symbol)` actually hits for a real
      AAVE position.
- [ ] [BACKEND] P1. **Fix `risk_monitor.py`/`exit_playbook_executor.py`'s colon-count assumption** for DEX
      instrument_ids — don't silently return `"UNKNOWN"`, either handle the real bare-address shape correctly or fail
      loud so the gap is visible instead of silent.
- [ ] [BACKEND] P1. **Fix deployment-api's Tier-3 cross-service exact-match** — either canonicalize both sides before
      comparing, or key the join on something more stable than the raw string (needs design thought — flagged, not
      prescribed here).
- [ ] [BACKEND] P1. **Fix `derive_underlying_from_instrument_id`'s bare-BASE-QUOTE assumption** in deployment-api to
      handle the real venue-prefixed shape.
- [ ] [DATA] P1. **Fix strategy-service's own DERIBIT mock/test data** (`scripts/seed_mock_data.py:60`,
      `engine/mock_data_provider.py`) to match what execution-service's real DERIBIT adapter actually produces
      (`DERIBIT:PERPETUAL:BTC-USD@INV`, not the current mock's `DERIBIT:PERPETUAL:BTC-PERPETUAL`) — this test-data gap
      is why CI could plausibly stay green while bug #1 above went undetected.
- [ ] [VERIFY] P0. **End-to-end reconciliation test against a real (paper/testnet) CCXT position** — confirm the fixed
      chain (CCXT adapter produces canonical id → reconciliation engine matches it → real quantity compared, not a
      silent zero) actually works, not just that the code compiles.
- [ ] [SCRIPT] P1. **Ship via quickmerge**, quality-gates green, in dependency order (CCXT-canonicalization plan first,
      then this plan).

## Progress Log

- **2026-07-08** — Filed from the canonical instrument-id audit's P0 findings #2 and #5, plus the strategy-service
  follow-up agent's detailed trace of the reconciliation break to a concrete broken consumer chain. No fix applied yet —
  operator explicitly wants direction confirmed before touching reconciliation logic given the safety stakes; this plan
  exists to hold that scope, not to claim it's already fixed.
