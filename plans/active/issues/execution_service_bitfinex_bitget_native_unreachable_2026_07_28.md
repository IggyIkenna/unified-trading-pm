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
assigned_vm: planning
assigned_role: backend_engineer
execution_scope: orchestrator-agent
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
context_scope:
  [
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md,
    execution-service/execution_service/trade_execution/factory.py,
    execution-service/execution_service/trade_execution/adapters/bitfinex_native.py,
  ]
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

> **RULED 2026-07-28** (operator general theme applied — no venue-specific answer was given, this decision falls under
> the standing design-choice theme: "opt for full completions, no shortcuts... no half-built, half-referenced adaptors
> left lying around either way" + "all adaptors should be FINISHED unless it is literally proven the data/access cannot
> be obtained, in which case FULLY REMOVE"). **Ruling: KEEP Bitfinex/Bitget as execution venues — wire the existing
> native adapters back in.** Reasoning: nothing here proves credentials are literally unobtainable (only that they
> haven't been requested yet, months after the adapters were built) — deleting complete, tested, working adapter code
> because it hasn't been connected yet is exactly the "cheap"/shortcut path the theme rejects; the adapters are already
> a FULL implementation (signing, rate limiting, error classification, `parse_order_response` contract tests — see "What
> I found" above), not a half-built scaffold, so completing the wiring (not deleting the work) is the
> full-completion-mandate answer. This also resolves the identical open sub-question in
> `per_venue_scope_key_provisioning_incomplete_2026_07_23.md`'s "Aster" section for these 2 venues — same ruling applies
> there.

- [x] ✅ [SCRIPT] P3. **Wire `bitfinex_native.py`/`bitget_native.py` into `factory.py`** — add BITFINEX/BITGET to a
      `DIRECT_REST_VENUES`-style set, a `_create_direct_rest_adapter`-style dispatch branch routing to
      `BitfinexCeFiAdapter`/`BitgetCeFiAdapter`, and both venues into `get_supported_venues()`'s returned list,
      mirroring the existing `DIRECT_REST_VENUES` pattern exactly — full wiring for BOTH venues in the same change, no
      partial (wire-one-skip-the-other) landing. **Do not gate this code change on credentials existing** — the adapter
      code already compiles and is unit-tested; wiring it is independent of whether live keys exist yet (the existing
      `_load_secret`-style credential path 404s safe-closed exactly like every other unprovisioned venue until keys
      land, same shape as Kalshi's pre-fix state in `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`).
      **Remaining concrete step this ruling does NOT cover**: acquiring real Bitfinex/Bitget API credentials (account
      creation + key generation on each exchange) is a real-world vendor-account action for the operator (or AO's own
      ambient identity, if a self-service path exists for these two vendors — unconfirmed) to complete before live
      trading can actually use these venues; it does not block landing this wiring todo.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). the keep-vs-delete judgment was RULED 2026-07-28; the residue is a fully-specified factory.py wiring
  change; conflict-check clear (the parent `cefi_consolidated_native_ao_extract` explicitly scoped bitfinex/bitget OUT).
  Shared conflict-check protocol: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 -
  CLEARED.
- **2026-08-03** (slot-8, backend_engineer): Todo shipped. `execution-service@0f37ec8a` wires BITFINEX/BITGET into
  `factory.py` — added to `DIRECT_REST_VENUES`, `_create_direct_rest_adapter` dispatch branch routing to
  `BitfinexCeFiAdapter`/`BitgetCeFiAdapter` (bitget mirrors kraken's spot/futures split via its `futures` flag; bitfinex
  is spot-only per the adapter's own `__init__`, no futures variant wired), both venues added to
  `get_supported_venues()`. **Companion cross-repo change discovered mid-task and required**: factory.py's import-time
  `_unregistered_venues` consistency check requires every `DIRECT_REST_VENUES` entry to resolve against UAC's
  `CLOB_VENUES | DEX_VENUES` (lowercase-base-split match) — BITFINEX/BITGET were NOT in UAC's `CLOB_VENUES` (despite
  already being registered elsewhere in UAC: `VENUE_CATEGORY_MAP`, `INSTRUMENT_TYPES_BY_VENUE`, `VENUE_CAPABILITIES`,
  `venue_collateral.py`, `venue_launch_dates.py` all already carry `BITFINEX-SPOT`/
  `BITFINEX-FUTURES`/`BITGET-SPOT`/`BITGET-FUTURES`), so wiring bitfinex/bitget into `DIRECT_REST_VENUES` without a UAC
  change would have raised `ValueError` at module import time. Fixed via `unified-api-contracts@1ee4dbd5`: added
  `BITFINEX_SPOT`/`BITGET_SPOT`/`BITGET_FUTURES` constants and registered them in `CLOB_VENUES` (mirroring the existing
  `KRAKEN_SPOT`/`KRAKEN_FUTURES` pattern) — a genuine registry gap-fill, not scope creep, confirmed via
  `tests/integration/test_registry_consumer_contracts.py::test_all_clob_venues_in_instrument_types` already having
  `INSTRUMENT_TYPES_BY_VENUE` entries for all three, so no downstream contract broke. Both repos' full
  `quality-gates.sh` passed (execution-service: 7811 passed/21 skipped/1 pre-existing xpass, unrelated to this change)
  and both SHAs verified as ancestors of `origin/live-defi-rollout`. Not archiving this doc despite the only todo now
  being done — it carries `locked_by: live-defi-rollout` and unlock/archival per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` requires an explicit `[unlock-plan]` ask, not
  autonomous action.
