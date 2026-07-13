---
doc_type: plan
title: UAC Venue Registry Completion — FX/BITFINEX/BITGET/KRAKEN category-map + leg-eligibility gaps
summary:
  Add FX, BITFINEX, BITGET, KRAKEN to VENUE_CATEGORY_MAP + VENUE_CAPABILITIES; wire archetype-leg eligibility for
  FX/BITFINEX/NASDAQ/NYSE; fix the FX vendor-key mismatch — all confirmed real, precisely-scoped gaps, no further audit
  needed.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [strategy, v2-engine, venue, registry, uac]
related: [v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend-engineer
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

- [ ] [REGISTRY] P0. Add `FX` to `VENUE_CATEGORY_MAP` (value `"tradfi"`) and to `VENUE_CAPABILITIES` (gate the
      composite-venue trade actions it actually supports — check `FXAdapter`'s implemented order types before guessing
      the capability set). File: `unified-api-contracts/unified_api_contracts/registry/venue_constants.py` (category
      dict ~326-368, capabilities dict ~554-590).
- [ ] [REGISTRY] P0. Fix the FX vendor-key bug:
      `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py:121` currently maps
      `"FX": "databento"`, which is wrong — FX never touches Databento, actual data sourcing is Yahoo Finance (hardcoded
      in MTDS `umi_tick_provider.py`, not looked up via this key today). Correct the key to the real vendor (or add a
      dedicated `yahoo_finance` `VENUE_TO_ADAPTER_KEY` entry and point FX at it) — do not propagate the stale
      `databento` tag.
- [ ] [REGISTRY] P0. Add `BITFINEX-SPOT` + `BITFINEX-FUTURES` to `VENUE_CATEGORY_MAP` (`"cefi"`) and
      `VENUE_CAPABILITIES` (`SPOT_TRADE` for `-SPOT`, `PERP_TRADE`+`FUTURES_TRADE` for `-FUTURES`, mirroring the
      existing BINANCE/OKX/BYBIT entries in the same dicts). Same file as above.
- [ ] [REGISTRY] P1. Add `BITGET-SPOT` + `BITGET-FUTURES` to both dicts, same capability pattern as bitfinex.
- [ ] [REGISTRY] P1. Add `KRAKEN-SPOT` + `KRAKEN-FUTURES` to both dicts, same capability pattern as bitfinex.
- [ ] [REGISTRY] P1. Wire archetype-leg eligibility for `FX`, `BITFINEX-SPOT`, `BITFINEX-FUTURES`, `NASDAQ`, `NYSE` into
      `ARCHETYPE_LEG_STRUCTURES`/`eligible_venue_ids`
      (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_leg_spec_seeds.py`) — confirmed 0
      hits for all 5 as of 2026-07-13. `BITGET`/`KRAKEN` do NOT need this (already leg-eligible) — do not touch their
      entries.
- [ ] [REGISTRY] P2. Regenerate + commit `capability-verdict-matrix.json` and confirm: (a) all 6 venues above now
      resolve a non-`(unknown)` category in `openapi/venue-coverage-report.md`, (b) `FX`/`BITFINEX-SPOT`/
      `BITFINEX-FUTURES`/`NASDAQ`/`NYSE` show `leg_eligible=yes`, (c) `split_scope_tokens` does not raise for any of
      these tokens, (d) no existing venue's category/capability entry regressed. Cite the regenerated matrix commit as
      evidence on this todo per the plan's evidence-backed-completion rule.

## Progress Log

(loop handoff lands here)
