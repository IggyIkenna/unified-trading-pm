---
doc_type: plan
title: UAC Venue Registry Completion — FX/BITFINEX/BITGET/KRAKEN category-map + leg-eligibility gaps
summary:
  Add FX, BITFINEX, BITGET, KRAKEN to VENUE_CATEGORY_MAP + VENUE_CAPABILITIES; wire archetype-leg eligibility for
  FX/BITFINEX/NASDAQ/NYSE; fix the FX vendor-key mismatch — all confirmed real, precisely-scoped gaps, no further audit
  needed.
status: complete # (was: active) 2026-07-15 plan-reconcile: all todos [x], evidence spot-checked, no open prose work
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [strategy, v2-engine, venue, registry, uac]
related: [/plans/active/v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up, naming-mismatch verification wf_6df96698-5dc 2026-07-13]
sequential: true
---

# UAC Venue Registry Completion

> **Split out 2026-07-13** from [`v2_engine_venue_buildout_2026_06_15.md`](v2_engine_venue_buildout_2026_06_15.md)
> (Follow-ups section) — this chunk is fully unblocked and precisely scoped (verified against live code, not grep-0),
> unlike the rest of that plan which is mostly `BLOCKED-CREDENTIALS`/`BLOCKED-model-variant`. Do not duplicate work
> already tracked there.

## Ground truth (2026-07-13 verification, `wf_6df96698-5dc` — do not re-derive, just act)

All venue tokens below are the EXACT canonical registry-key forms already in use throughout
`unified-api-contracts/unified_api_contracts/registry/venue_constants.py` — uppercase `VENUE` or `VENUE-KIND`, no
lowercase/alnum-stripped variants for these dict keys (that convention is for `KNOWN_VENUE_TOKENS` slot-labels only,
which are already wired for all of these):

- `FX` — bare, single composite TradFi venue (not multi-chain). Execution: `FXAdapter` (IBKR IDEALPRO) already routed.
  Data: Yahoo Finance daily bars (`yfinance`), confirmed live — no intraday feed exists, this is an accepted ceiling,
  not a gap to fix here.
- `BITFINEX-SPOT`, `BITFINEX-FUTURES` — both fully wired everywhere EXCEPT `VENUE_CATEGORY_MAP`/`VENUE_CAPABILITIES` AND
  `ARCHETYPE_LEG_STRUCTURES` (0 rows in `capability-verdict-matrix.json` vs. 44 each for siblings).
- `BITGET-SPOT`, `BITGET-FUTURES` — fully wired including leg-eligibility; missing ONLY
  `VENUE_CATEGORY_MAP`/`VENUE_CAPABILITIES`.
- `KRAKEN-SPOT`, `KRAKEN-FUTURES` — same as BITGET: missing ONLY `VENUE_CATEGORY_MAP`/`VENUE_CAPABILITIES`.
- `NASDAQ`, `NYSE` — `VENUE_CATEGORY_MAP` entries ALREADY EXIST (`venue_constants.py:341,342,350`) — the old F43 finding
  was a false positive there. Their real gap is leg-eligibility ONLY.

**HARD RULE — canonical form, no ad-hoc casing**: every new dict key MUST match the exact uppercase `VENUE` /
`VENUE-KIND` form listed above (these are the same strings already used as `VENUE_TO_ADAPTER_KEY` keys, collateral keys,
and `data_type_capability.py` `venue=` values — do not invent a lowercase or differently-punctuated variant). Do not
touch `KNOWN_VENUE_TOKENS` (already correct) or any GCS path/bucket logic — this plan is registry-dict-only, no storage
code.

## Todos

- [x] ✅ [REGISTRY] P0. Add `FX` to `VENUE_CATEGORY_MAP` (value `"tradfi"`) and to `VENUE_CAPABILITIES` (gate the
      composite-venue trade actions it actually supports — check `FXAdapter`'s implemented order types before guessing
      the capability set). File: `unified-api-contracts/unified_api_contracts/registry/venue_constants.py` (category
      dict ~326-368, capabilities dict ~554-590). — SHIPPED `unified-api-contracts@0bd81fc2`. Category `"tradfi"`;
      capability `{SPOT_TRADE}` only — confirmed via `execution-service`'s `FXAdapter(IbkrTradFiAdapter)`: routes
      through IDEALPRO using `secType="CASH"` contracts exclusively (no `FUT`/`OPT`), matching NASDAQ/NYSE's spot-only
      pattern. Found + fixed a 3rd registry in the same commit: `VENUE_ORDER_CAPABILITIES` also requires an entry for
      every `VENUE_CAPABILITIES` key (enforced by
      `tests/unit/test_venue_order_capabilities.py`/`tests/integration/test_instruction_venue_integration.py`, which
      failed until `"FX": _TRADFI_EXCHANGE` was added, same set NASDAQ/NYSE use). 1072 relevant tests + full
      `quality-gates.sh` green, sentinel verified.
- [x] ✅ [REGISTRY] P0. Fix the FX vendor-key bug:
      `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:121` currently maps
      `"FX": "databento"`, which is wrong — FX never touches Databento, actual data sourcing is Yahoo Finance (hardcoded
      in MTDS `umi_tick_provider.py`, not looked up via this key today). Correct the key to the real vendor (or add a
      dedicated `yahoo_finance` `VENUE_TO_ADAPTER_KEY` entry and point FX at it) — do not propagate the stale
      `databento` tag. — SHIPPED `unified-api-contracts@bd7117ba`. Verified no `yahoo_finance` URDI reference-data
      adapter class exists in instruments-service's `_ADAPTERS`, and confirmed `umi_tick_provider.py` fetches FX market
      data via a hardcoded `venue_upper == "FX"` branch that bypasses `VENUE_TO_ADAPTER_KEY`/URDI entirely — FX
      genuinely has no URDI adapter. Changed `"FX": "databento"` → `"FX": NO_ADAPTER_YET` (the documented sentinel for
      exactly this case) rather than inventing a phantom `yahoo_finance` adapter key with no backing class. Added `FX`
      to `test_venue_adapter_keys.py`'s `EXPECTED_SENTINEL_VENUES` deliberate-decision gate with the same reasoning. 836
      relevant tests + full `quality-gates.sh` green, sentinel verified.
- [x] ✅ [REGISTRY] P0. Add `BITFINEX-SPOT` + `BITFINEX-FUTURES` to `VENUE_CATEGORY_MAP` (`"cefi"`) and
      `VENUE_CAPABILITIES` (`SPOT_TRADE` for `-SPOT`, `PERP_TRADE`+`FUTURES_TRADE` for `-FUTURES`, mirroring the
      existing BINANCE/OKX/BYBIT entries in the same dicts). Same file as above. — SHIPPED
      `unified-api-contracts@85b4ea01`. Also added the required `VENUE_ORDER_CAPABILITIES` entries (empty frozenset, not
      `_CEFI_FULL`) — `test_all_venues_with_capabilities_have_order_capabilities` requires every `VENUE_CAPABILITIES`
      key to appear there too (same discovery class as the FX todo above), and `BitfinexCeFiAdapter` (execution-service)
      is `BLOCKED-CREDENTIALS` with every trading method raising `NotImplementedError`, so an empty set is the honest
      capability, not an assumed `_CEFI_FULL`. Full `quality-gates.sh` green (274s once the shared host-QG-governor
      token was acquired; an earlier attempt hit the token after a 796s queue wait and tripped the `<720s` MAX_DURATION
      gate purely from queue-time being counted as work time — see
      `plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md`), sentinel verified at
      `85b4ea015c65f56d0777d6a8a2b65117e848ce6f`.
- [x] ✅ [REGISTRY] P1. Add `BITGET-SPOT` + `BITGET-FUTURES` to both dicts, same capability pattern as bitfinex. —
      SHIPPED `unified-api-contracts@21dde0f8`. Category `"cefi"`; capabilities `{SPOT_TRADE}` /
      `{PERP_TRADE,     FUTURES_TRADE}`. Same `VENUE_ORDER_CAPABILITIES` discovery as BITFINEX applied —
      `BitgetCeFiAdapter` (execution-service) is also `BLOCKED-CREDENTIALS` with every trading method raising
      `NotImplementedError`, so empty frozenset entries were added there too. Full `quality-gates.sh` green (297s),
      sentinel verified at `21dde0f8ce9e860e4115cb30845a5eb35e9b6938`.
- [x] ✅ [REGISTRY] P1. Add `KRAKEN-SPOT` + `KRAKEN-FUTURES` to both dicts, same capability pattern as bitfinex. —
      SHIPPED `unified-api-contracts@7c9c1a0a`. Category `"cefi"`; capabilities `{SPOT_TRADE}` /
      `{PERP_TRADE,     FUTURES_TRADE}`. `VENUE_ORDER_CAPABILITIES` deliberately did NOT copy the Bitfinex/Bitget
      empty-set pattern: `KrakenCeFiAdapter` (execution-service `kraken_rest_adapter.py`) is a REAL implementation —
      `place_order` genuinely POSTs to Kraken's `AddOrder` endpoint (not a `NotImplementedError` stub) — supporting
      MARKET/LIMIT/STOP*LIMIT/STOP_LOSS/TAKE_PROFIT via its outbound order-type mapping, with no post-only/ reduce-only
      oflags and no batch or cancel-replace endpoint wired. Added a custom `frozenset({STOP_LIMIT})` entry (not empty,
      not any `\_CEFI*\*`tier — those all require`POST_ONLY`, which isn't implemented). Full `quality-gates.sh`green
      (748s, run with`IGNORE_TIMEOUT=true`— the documented override in`base-service.sh`/`base-library.sh`for exactly
      this queue-contention wall-clock false-fail, see
      `plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md`— after two prior attempts tripped the
      `<720s`gate by 11-18s purely from governor queue-wait), sentinel verified at
      `7c9c1a0a9c8c009f3e5ad3fcc9e2318ce0da54a3`.
- [x] ✅ [REGISTRY] P1. Wire archetype-leg eligibility for `FX`, `BITFINEX-SPOT`, `BITFINEX-FUTURES`, `NASDAQ`, `NYSE`
      into `ARCHETYPE_LEG_STRUCTURES`/`eligible_venue_ids`
      (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_leg_spec_seeds.py`) — confirmed 0
      hits for all 5 as of 2026-07-13. `BITGET`/`KRAKEN` do NOT need this (already leg-eligible) — do not touch their
      entries. — SHIPPED `unified-api-contracts@61ba5239`. Per-site additions, each citing a real engine adapter or
      codex archetype-doc example instance (the module's own "NEVER invented" sourcing rule): `bitfinex` (SPOT-only,
      `bitfinex_native.py:167` has no futures adapter) → `CARRY_BASIS_PERP` spot leg, `CARRY_BASIS_DATED`(+INV) spot
      leg; `nasdaq`/`nyse` → `CARRY_BASIS_DATED`(+INV), `STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`; `fx` +
      `nasdaq`/`nyse` → `ML_DIRECTIONAL_CONTINUOUS` + `RULES_DIRECTIONAL_CONTINUOUS` (via a new
      `continuous_tradfi_venues` tuple, NOT mutating the shared `continuous_venues` — that tuple also feeds
      `TSMOM_BTC_CTA`, whose own codex doc states "BTC-only CeFi archetype by design"); `fx`/`nasdaq` (not `nyse`) →
      `EVENT_DRIVEN`. **Deliberately NOT wired** (would be inventing a leg per the module's sourcing rule, not a gap
      left for later): `bitfinex` on `CARRY_BASIS_PERP`'s perp leg, `CARRY_FUNDING_DISPERSION`, the shared
      `_CEFI_CLOB_VENUES` tuple, and `ARBITRAGE_PRICE_DISPERSION` (no `BITFINEX-FUTURES` adapter exists to back a perp
      claim); `nyse` on `EVENT_DRIVEN` (no NYSE-ticker example found in either codex doc, only AAPL/MSFT/NVDA on
      NASDAQ). Full `quality-gates.sh` green (285s, `IGNORE_TIMEOUT=true`; also survived one host root-disk-full
      transient mid-commit — self-recovered per `plans/active/issues/host_root_disk_full_transient_2026_07_13.md` — and
      one quickmerge sentinel-invalidating rebase from a concurrent unrelated sports-venue commit), sentinel verified at
      `61ba523906afc462943b24db83d40bf16ff90695`.
- [x] ✅ [REGISTRY] P2. Regenerate + commit `capability-verdict-matrix.json` and confirm: (a) all 6 venues above now
      resolve a non-`(unknown)` category in `openapi/venue-coverage-report.md`, (b) `FX`/`BITFINEX-SPOT`/
      `BITFINEX-FUTURES`/`NASDAQ`/`NYSE` show `leg_eligible=yes`, (c) `split_scope_tokens` does not raise for any of
      these tokens, (d) no existing venue's category/capability entry regressed. Cite the regenerated matrix commit as
      evidence on this todo per the plan's evidence-backed-completion rule. — SHIPPED `unified-api-contracts@c138145b`.
      Ran both regenerators (`unified-trading-pm/scripts/openapi/     generate_capability_verdict_matrix.py` +
      `audit_venue_coverage.py`) against the 6 already-shipped fixes above. **(a)/(b) confirmed by direct grep of the
      regenerated `venue-coverage-report.md`**: `BITFINEX-FUTURES`/
      `BITFINEX-SPOT`/`BITGET-FUTURES`/`BITGET-SPOT`/`KRAKEN-FUTURES`/`KRAKEN-SPOT` all `category=cefi`, `FX`/`NASDAQ`/
      `NYSE` all `category=tradfi`, all 9 show `leg_eligible=yes`. **(c) found a genuine gap while verifying, not
      assumed**: `split_scope_tokens(("fx",))` RAISED — `"fx"` was missing from `KNOWN_VENUE_TOKENS` (`_TRADFI_TOKENS`
      in `venue_tokens.py`), contradicting this plan's own ground-truth claim that it was "already wired." The other 8
      tokens (bitfinex/bitget/kraken/nasdaq/nyse, bare lowercase, no hyphens) were genuinely fine. Fixed as a minimal
      necessary companion (added `"fx"` to `_TRADFI_TOKENS`, matching the other IBKR-routed entries) since criterion (c)
      is this exact todo's job to ensure — a pure frozenset addition, provably non-regressive
      (`is_venue_token`/`split_scope_tokens` can only succeed in MORE cases afterward, never fewer). Re-ran both
      regenerators after the fix; all 9 tokens confirmed no-raise. **(d) verified by diffing category-line-by-line**
      against the pre-regen committed report: every category flip is either one of this plan's 6 already-shipped fixes
      (unknown→known, expected) or an unrelated concurrent registry change from another slot (e.g. Barchart retirement,
      POLYMARKET-PERP/KALSHI-PERP additions) — zero known→unknown flips, zero regressions attributable to this change.
      Full `quality-gates.sh` green (237s), sentinel verified at `c138145b9dc5f2f0c598671ddcff1c1136c75fd7`. **All 7
      todos in this plan are now complete.**

## Progress Log

(loop handoff lands here)
