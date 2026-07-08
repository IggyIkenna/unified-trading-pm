---
doc_type: plan
title: Fix CCXT live-mode instrument_id divergence — 13 major CeFi venues get a structurally different id live vs batch
summary: >-
  instruments-service's CCXTReferenceDataAdapter stores instrument_key as the bare, unmodified ccxt-native market symbol
  (e.g. "BTC/USDT", "BTC/USDT:USDT") with zero canonicalization — this is the live-mode route for 13 canonical venues
  (BINANCE-SPOT/-FUTURES, BYBIT(+SPOT/FUTURES), OKX(+SPOT/SWAP/FUTURES), DERIBIT, COINBASE-SPOT, UPBIT,
  KRAKEN-SPOT/-FUTURES). Batch mode (Tardis) produces a differently-shaped canonical id for the same real instrument. A
  direct live=batch determinism violation on this workspace's most heavily-traded CeFi venues.
status: active
nature: notes
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [instrument-id, live-vs-batch, determinism, bug-fix, p0, ccxt]
related:
  [
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    ../../codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Canonical instrument-id audit, 2026-07-08 (canonical_instrument_id_audit_2026_07_08.md, finding #4), cross-referenced
  under batch_live_symmetry_master per operator decision (2026-07-08) to track under existing epics rather than a new
  one, since this is precisely that epics scope: per-service batch=live audit + reconciliation."
---

> **Direct violation of a core workspace invariant** — paper(W) must equal batch-rerun(W) trade-for-trade. If the same
> real instrument has two different ids depending on capture mode, nothing downstream can reconcile live vs batch data
> for it without a lossy manual join.

## Root cause

`instruments_service/reference_data/adapters/cefi/ccxt_adapter.py:156-157` (`_parse_ccxt_market`) builds
`InstrumentRecord(instrument_key=symbol, ...)` where `symbol` is the raw ccxt unified market symbol verbatim
(`"BTC/USDT"` spot, `"BTC/USDT:USDT"` perp, `"BTC/USDT:USDT-250328"` future) — never passed through
`canonical_id_builder.build_instrument_id()` or given any `VENUE:TYPE:` structure. This adapter is the live-mode route
for 13 canonical venues per `factory.py`'s `_CANONICAL_VENUE_TO_CCXT_EXCHANGE` (routed from `factory.py:95-114,383-398`
and `router.py:193-197,290-307`): `BINANCE-SPOT`, `BINANCE-FUTURES`, `BYBIT`/`-SPOT`/`-FUTURES`, `OKX`/`-SPOT`/`-SWAP`/
`-FUTURES`, `DERIBIT`, `COINBASE-SPOT`, `UPBIT`, `KRAKEN-SPOT`, `KRAKEN-FUTURES`. Batch mode for the same venues goes
through Tardis, which (per this session's earlier real-catalog reads) produces properly dash-cleaned canonical ids for
most of these (e.g. `BYBIT:PERPETUAL:BTC-USDT`).

## Todos

- [ ] [DATA] P0. **Route `CCXTReferenceDataAdapter`'s instrument_key construction through the same canonicalization path
      batch mode uses** — the target isn't necessarily `canonical_id_builder.py` itself (per the audit, that module is
      barely used in practice) but whatever real logic produces the correct batch-mode ids for these same 13 venues, so
      live and batch converge on an identical id for the identical instrument.
- [ ] [VERIFY] P0. **Confirm convergence for all 13 venues** — for at least one real instrument per venue, confirm the
      live-mode CCXT-derived id now matches the real batch-mode (Tardis) id exactly.
- [ ] [VERIFY] P1. **Check every real consumer of CCXT-adapter instrument_ids** (strategy-service's reconciliation
      engine, per `canonical_id_p0_strategy_reconciliation_2026_07_08.md`, is one confirmed consumer) — changing this id
      shape is a breaking change for anything that persisted or compared against the OLD raw ccxt-symbol shape.
- [ ] [SCRIPT] P1. **Ship via quickmerge**, quality-gates green. Coordinate with
      `canonical_id_p0_strategy_reconciliation_2026_07_08.md` since fixing this is a prerequisite for that plan's
      reconciliation-engine fix to actually work end-to-end.

## Progress Log

- **2026-07-08** — Filed from the canonical instrument-id audit's P0 finding #4. Root cause + affected venue list
  confirmed via direct code reads. No fix applied yet.
