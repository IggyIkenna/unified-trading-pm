---
doc_type: issue
title: execution-service bitfinex_native.py / bitget_native.py are unreachable — no CCXT counterpart to fall back on
summary: >-
  Adjacent finding from the binance/bybit/okx `*_ccxt.py`/`*_native.py` dead-code audit
  (cefi_consolidated_native_ao_extract_2026_07_25.md todo 1): bitfinex_native.py and bitget_native.py share the exact
  same unreachability characteristic as the 3 deleted binance/bybit/okx native adapters (not in any
  CCXT_VENUES/DIRECT_REST_VENUES/TRADFI_VENUES set, not in get_supported_venues(), zero production references — only
  test-referenced) but, unlike binance/bybit/okx, have NO `_ccxt.py` counterpart at all. Deleting them would remove the
  only implementation for those 2 venues entirely, which is a materially different and higher-risk decision than the
  binance/bybit/okx case (where CCXT was already the live, working implementation) — needs its own scoped judgment call,
  not a reflexive deletion under a differently-scoped todo.
status: open
nature: issue
asset_group: [cefi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [dead-code, adapters, cefi, execution]
related:
  [
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md,
  ]
created: 2026-07-28
parent_epic: execution_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
source: >-
  Discovered while auditing the *_ccxt.py/*_native.py parallel-file pattern for BINANCE/BYBIT/OKX
  (cefi_consolidated_native_ao_extract_2026_07_25.md todo 1) — bitfinex/bitget were built in the same batch commit
  (582f1e93d, "Phase 2.B+2.E native REST adapters for Binance/Bybit/OKX/Bitfinex/Bitget") and show the identical
  unreachability signature, but were explicitly out of scope for that todo (BINANCE/BYBIT/OKX only).
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
resolved_by:
---

# execution-service bitfinex_native.py / bitget_native.py unreachable

## What I found

`execution_service/trade_execution/adapters/bitfinex_native.py` (`BitfinexCeFiAdapter`) and `bitget_native.py`
(`BitgetCeFiAdapter`) are not reachable via any production code path:

- Not in `factory.py`'s `CCXT_VENUES`, `DIRECT_REST_VENUES`, or `TRADFI_VENUES` sets.
- Not created by `_create_ccxt_adapter[_extended]`, `_create_direct_rest_adapter`, or `_create_tradfi_adapter`.
- Not in `get_supported_venues()`'s returned list.
- Not exported from `trade_execution/__init__.py`.
- Corpus-wide grep for `BitfinexCeFiAdapter`/`BitgetCeFiAdapter` and `bitfinex_native`/`bitget_native` outside their own
  files finds only test references (`tests/unit/test_native_adapter_contracts.py`,
  `tests/unit/cefi_execution/test_bitfinex_native_adapter.py`, `test_bitget_native_adapter.py`).
- No feature flag or env var gates a future activation.

This is the identical unreachability signature confirmed for `binance_native.py`/`bybit_native.py`/`okx_native.py` in
`cefi_consolidated_native_ao_extract_2026_07_25.md`'s todo 1 (all 5 files shipped in the same commit, `582f1e93d`,
"Phase 2.B+2.E native REST adapters for Binance/Bybit/OKX/Bitfinex/Bitget + token-bucket rate limiter") — but those 3
were deleted because CCXT is the confirmed, live, working implementation for binance/bybit/okx. Bitfinex and bitget have
**no CCXT counterpart** — there is no `bitfinex_ccxt.py`/`bitget_ccxt.py` anywhere in the repo. Per
`issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md` § "Aster", bitfinex/bitget were "built natively
because CCXT support was inadequate for those two at the time" (as of ~2026-05).

## Why it matters

Two different failure modes are plausible and this issue does not adjudicate between them:

1. **Legitimate pre-built scaffold, never wired in** — the native REST work for bitfinex/bitget is real and complete
   (signing, rate limiting, error classification, parse_order_response contract tests), just never connected to
   `factory.py`. If bitfinex/bitget are still wanted as execution venues, wiring these in (adding them to a
   `DIRECT_REST_VENUES`-style set + a `_create_direct_rest_adapter`-style dispatch branch + `get_supported_venues()`) is
   a small, low-risk activation — no new adapter code needed, "just wiring."
2. **Genuinely abandoned** — if bitfinex/bitget are no longer wanted as execution venues (per
   `per_venue_scope_key_provisioning_incomplete_2026_07_23.md`'s own open question: "Whether Upbit/Kraken/Bitfinex/
   Bitget are still wanted as trading venues at all, given zero credentials months after[...]"), these 2 files (plus
   their `_native_base.py` shared helper usage, once confirmed unused by anything else) are dead code per
   `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` and should be deleted the same way
   binance/bybit/okx's were.

Deleting the ONLY implementation for a venue is a categorically bigger decision than deleting a redundant duplicate of a
working implementation (the binance/bybit/okx case) — it forecloses ever trading that venue without rebuilding from
scratch. That's why this was kept out of the binance/bybit/okx todo's scope rather than folded in reflexively.

## Recommended decision

- [ ] [OPERATOR] P3. Decide whether Bitfinex/Bitget are still wanted as execution venues at all (this question is
      already open in `per_venue_scope_key_provisioning_incomplete_2026_07_23.md` — this issue just flags that the
      native-adapter reachability gap is a second, related symptom of the same unresolved question, not a separate
      decision). If YES: file a follow-up todo to wire `bitfinex_native.py`/`bitget_native.py` into `factory.py`
      (mirroring `DIRECT_REST_VENUES`/`_create_direct_rest_adapter`) once credentials exist. If NO (or "not soon"): file
      a follow-up todo to delete both files + their dedicated tests, citing this issue doc + the adapter-dead-code-ban
      SSOT, same pattern as `execution-service@6c9645a5`.
