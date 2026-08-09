---
doc_type: issue
title:
  TradFi "MVP-of-the-MVP" instrument scope ruling — narrowed immediate backfill target, rest gated until November 2026
summary: >-
  Operator ruling 2026-08-09: rather than complete all 6 tradfi MVP cells to 100% right now, immediate backfill work is
  narrowed to exactly the instruments needed for the equities-vs-perps basis strategy (Binance-listed equity perps
  launched 2026). Completing the REST of the tradfi MVP universe (full-history equities beyond 2026, daily Treasuries,
  VIX futures, CBOE yield index, FX KRW) to 100% is explicitly GATED until November 2026 — no plan/todo should drive
  that broader work before then. This doc is the SSOT other tradfi plans point to; it supersedes the "MVP universe"
  framing in `tradfi_consolidated_closeout_2026_07_18.md` for near-term dispatch purposes only (that doc's full 6-cell
  definition stays valid as the eventual November target, it is not rewritten).
status: open
nature: process
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, mvp-scope, instrument-scope, operator-decision, backfill, november-gate]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
  ]
created: 2026-08-09
author: claude-code (interactive session, operator-directed 2026-08-09)
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source:
  [
    "Operator chat instruction, 2026-08-09: narrowed scope to (1) MVP equities OHLCV_1m, year 2026 only — Binance listed
    equity perps this year, that is the main strategy being tested (equities-vs-perps basis); (2) Korean stocks —
    OHLCV_24h from Yahoo Finance as a proxy only, no intraday; (3) S&P 500 — the full 6.5-year OHLCV_1m for both futures
    (ES) AND options (ES options); (4) BTC futures, ETH futures (CME), and BTC/ETH spot ETFs (equities). Completing the
    rest of the tradfi MVP universe to 100% is gated until November. Operator: 'to start with, really as a starting
    point we just need the year 2026 ... for korean stocks we just need ohlcv 24h from yahoo finance as a proxy ... for
    s&p 500 year we want the 6.5 year ohlcv_1m futures and options ... we also need btc futures eth futures and btc and
    eth etfs.'",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [/plans/active/tradfi_consolidated_closeout_2026_07_18.md, /codex/02-data/tradfi-databento-sourcing-ssot.md]
drift_direction: advance-code
depends_on: []
---

# TradFi "MVP-of-the-MVP" instrument scope ruling

## In scope — proceed now

| Cell                                     | Scope                                                | Data type   | Source                   |
| ---------------------------------------- | ---------------------------------------------------- | ----------- | ------------------------ |
| Delta-one single-stock equities          | **Year 2026 only** (not the full multi-year history) | `ohlcv_1m`  | Databento (`DBEQ.BASIC`) |
| Korean stocks (KRX)                      | Daily proxy only, no intraday                        | `ohlcv_24h` | Yahoo Finance            |
| S&P 500 futures (ES)                     | Full 6.5-year history (2020-01-01 → now)             | `ohlcv_1m`  | Databento (`GLBX.MDP3`)  |
| S&P 500 options (ES options)             | Full 6.5-year history (2020-01-01 → now)             | `ohlcv_1m`  | Databento (`GLBX.MDP3`)  |
| CME BTC/ETH futures (BTC, ETH, MBT, MET) | Full history                                         | `ohlcv_1m`  | Databento (`GLBX.MDP3`)  |
| BTC/ETH spot ETFs (e.g. IBIT, ETHA)      | Full history                                         | `ohlcv_1m`  | Databento (`DBEQ.BASIC`) |

**Rationale**: Binance listed single-stock equity perps in 2026 — the equities-vs-perps basis strategy this is meant to
feed only needs 2026-forward equities data to test against. S&P futures+options get the full window because the
strategy's price-arb/ML backtest (`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`) explicitly runs a
2020-2026 train/test split. BTC/ETH futures+ETFs are the crypto-adjacent legs of the same basis family.

## Out of scope — gated until November 2026

Everything else in the 6-cell tradfi MVP universe (`tradfi_consolidated_closeout_2026_07_18.md` § "MVP universe"):

- Delta-one single-stock equities for years **other than 2026** (i.e. completing the full historical equities corpus to
  100%).
- Daily Treasuries (`ohlcv_24h`, FRED).
- VIX FUTURE (CBOE) + CBOE yield INDEX.
- FX KRW spot pair, beyond whatever the KRX-daily proxy already covers.
- Any FX/commodity futures backfill not named above (the currently-running `tradfi-bf-cme-ohlcv-1m-g0{1,2,3}-*` fleet —
  6A/6B/6C/6E/6J/6L currency futures, 6M/CL/CT/HG commodities — is **entirely out of this scope** and is being killed,
  not relaunched, per this ruling).

**No plan/todo should dispatch backfill work for the out-of-scope list before November 2026.** If a worker or an
autonomous session (e.g. `wave_launcher.py`'s gap-driven dispatch) would otherwise pick up one of these cells, treat it
as `BLOCKED-OPERATOR-DECISION` citing this doc, not as ready work.

## Relationship to the Databento billing-suspension issue

`/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` gated several of these same todos
(ES_OPT launch, MVP backfill readiness gate) on 2026-08-09 pending confirmation the vendor account wasn't suspended.
That was independently live-verified the same day — direct calls to Databento's `metadata.list_datasets` and a live
`ES.FUT ohlcv-1m` pull both succeeded — so the billing gate is lifted specifically for the in-scope items above (this
doc's scope list). The billing issue doc itself stays open as a standing awareness record; it no longer blocks the
in-scope relaunch this doc authorizes.

## Known relaunch gotchas (carry forward, don't re-discover)

- `wave_launcher.py`'s dedup check (`running_cell_keys`) parses live VM names for a `root` group label and never matches
  the per-single-root dispatch candidate keys it computes internally for CME — this is why the FX/commodity fleet
  duplicated 3-13x per shard. Any relaunch of the in-scope CME cells (ES, BTC/ETH futures) must not reuse
  `wave_launcher.py` blind — either fix the key mismatch first, or launch directly via
  `launch-tradfi-bf-cme-ohlcv-1m.sh` / `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` per-shard with a manual "is a VM already
  running for this shard" check.
- ES ohlcv_1m capture has a real, confirmed (not vendor-side) gap May-December every year 2020-2026 — live-verified
  against Databento directly. Relaunching ES needs `--force`/`VM_FORCE=true` semantics that don't just skip on a false
  "already captured" read for those months, since the manifest's own `NO_INPUT_AVAILABLE` classification there is wrong.

## Disposition of currently-running infra (2026-08-09)

167 `tradfi-bf-cme-ohlcv-1m-g0{1,2,3}-*` VMs were running at the time of this ruling, 100% out of the scope above
(FX/commodity futures) and massively duplicated (up to 13 concurrent VMs per shard, see above). Disposition: killed, not
resumed. See Progress Log below for the kill + scoped-relaunch record.

## Todos

- [ ] [SCRIPT] P2. Fix `wave_launcher.py`'s `running_cell_keys` dedup check so it matches the per-single-root CME
      dispatch candidate keys it computes internally, instead of only matching a VM-name-parsed "root group" label —
      currently causes CME launches to duplicate 3-13x per shard (measured: 167 stray VMs from one erroneous wave, per
      "Disposition of currently-running infra" above). Any relaunch of the in-scope CME cells (ES, BTC/ETH futures)
      needs this fixed first, or must bypass `wave_launcher.py` per the manual-check workaround already noted in "Known
      relaunch gotchas" above. **(na-eligibility-audit 2026-08-09, tradfi tranche, dispatch agt-3df41f: converted from
      prose-only "Known relaunch gotchas" text to a tracked checkbox — same finding, not new scope.)**

## Progress Log

- 2026-08-09: doc created, scope ruling recorded. Sweep of tradfi plans/issues for regression risk against this scope in
  progress — see this doc's `related` list and the per-doc scope notes added to each.
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:6648d0c11c478b7d]: **KEEP-NA,
  valid -- first audit, functioning correctly as an SSOT ruling doc.** A dedicated sub-agent hunter read this doc
  end-to-end plus cross-referenced its live consumers (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` -- both confirmed already citing this ruling correctly, same day).
  Converted the "Known relaunch gotchas" wave_launcher.py dedup-bug prose into a tracked `- [ ]` checkbox above (same
  finding, not new scope) -- kept KEEP-NA rather than RECLASSIFY despite it reading as a bounded code fix, because it
  touches live-dispatch-critical-path machinery (`wave_launcher.py`'s VM-launch dedup) that this pass did not itself
  directly read the code for; flagging as a RECLASSIFY candidate for a follow-up pass that reads `wave_launcher.py`
  directly rather than promoting on secondhand evidence alone. Separately noted (not this doc's to verdict):
  `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` reports a live, unresolved possible
  violation of this doc's "year 2026 only" scope contending for the same account-wide Databento lock as the authorized
  ES_OPT launch -- worth a prompt look by whoever owns tradfi triage today.
