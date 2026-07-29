---
doc_type: issue
title:
  "TradFi's mvp_mode fetch-time filter is unreachable dead code — production always downloads the full 93-instrument
  universe unfiltered"
summary: >-
  databento_enrichment.py::_resolve_by_dataset branches on an mvp_mode: bool param that would call
  get_mvp_databento_symbols_for_venue() (a curated, narrower ES-only-for-CME-style subset) instead of the full
  get_databento_symbols_for_venue(). download_batch_df's mvp_mode defaults False and a workspace-wide grep for
  mvp_mode=True returns zero hits anywhere — no real caller ever requests the MVP-filtered path. Production always
  downloads the full TRADFI_DATABENTO_INSTRUMENTS universe (93 instruments) unfiltered for every venue including CME,
  regardless of mvp_scope.py's curated TradFi MVP rule (CME + ES/NQ/VX/commodity-root underliers only).
status: resolved
nature: notes
asset_group: [tradfi]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [mvp, tradfi, dead-code, cli, p2]
related:
  [
    ../../docs-mirror/instruments-service/TRADFI_INSTRUMENTS.md,
    /plans/audit/results/canonical_instrument_id_audit_2026_07_08.md,
  ]
created: 2026-07-08
parent_epic: instruments_master
priority: P2
source:
  "Found during a dedicated audit of the real MVP catalogue/classification code (operator request, 2026-07-08: 'Audit
  the real MVP catalogue code'). Re-verified directly before filing: grep for mvp_mode=True across the whole workspace
  returns zero hits; get_mvp_databento_symbols_for_venue has no caller outside its own unit test and
  databento_enrichment.py's dead branch."
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
last_updated: 2026-07-29
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
resolved_by: market-tick-data-service@e7581b8b + @6bc9d676 (2026-07-10/11); archived 2026-07-29 na-eligibility-audit
---

> **🟢 ARCHIVED 2026-07-29 (na-eligibility-audit) — RESOLVED.** Direction (a), "wire a real caller," shipped
> `market-tick-data-service@e7581b8b` (2026-07-10) + `@6bc9d676` (2026-07-11) — both confirmed ancestors of
> `origin/live-defi-rollout`. All 3 todos done; see the Progress Log below for the full evidence trail.

## The bug

`market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/databento_enrichment.py:208-226`
(`_resolve_by_dataset`) takes an `mvp_mode: bool` param:

```python
if mvp_mode:
    defs = get_mvp_databento_symbols_for_venue(venue_name)
else:
    defs = get_databento_symbols_for_venue(venue_name)
```

`get_mvp_databento_symbols_for_venue`
(`unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:724`) is a real, implemented,
unit-tested function — it correctly returns a narrower MVP-scoped instrument-definition set (e.g. ES option surfaces +
commodity option-on-futures defs for CME). But the ONLY place `_resolve_by_dataset` is reachable from is
`download_batch_df` (`databento_enrichment.py:299-324`), whose `mvp_mode: bool = False` default is never overridden
anywhere:

- Workspace-wide grep for `mvp_mode=True` / `mvp_mode = True`: **zero hits**, any repo.
- `get_mvp_databento_symbols_for_venue`'s only non-definition references are its own dedicated unit test
  (`unified-api-contracts/tests/unit/test_cme_options_universe.py`) and the dead `if mvp_mode:` branch itself.

**Real operator impact**: `unified_api_contracts.canonical.crosscutting.mvp_scope.py::MVP_SCOPE["tradfi"]`
(`TradFiMvpRule`) declares a real, curated TradFi MVP universe — CME only, `FUTURE`/`OPTION`, underliers
`ES`/`NQ`/`VX` + the 7 commodity roots backing a Binance tradfi-perp (`GC`/`SI`/`PL`/`PA`/`NG`/`CL`/`HG`) — but this
rule is enforced ONLY at the classification layer (tagging already-captured rows `mvp=true/false` for downstream
reporting), never at the fetch layer. Production downloads and captures the FULL 93-instrument
`TRADFI_DATABENTO_INSTRUMENTS` universe unfiltered for every TradFi venue including CME, every run, regardless of
whether the caller wanted the MVP-scoped subset. This is not itself a data-loss bug (the full universe is a superset of
MVP, so nothing MVP-relevant is missing) — the real costs are: (a) the `mvp_mode`-filtered code path is maintained (has
its own registry function + unit tests) but has never actually run in production, so it's unverified against live
Databento responses; (b) any future caller that actually wants a cheaper/narrower MVP-only fetch (e.g. a
cost-constrained CME-options-only backfill) will silently get the full universe instead, with no error or warning.

## Todos

- [x] ✅ [DECISION] P2. **RESOLVED — direction (a).** **Decide whether `mvp_mode` should ever be wired live** — either (a) find/create a real caller that
      needs the narrower MVP-only fetch (e.g. a cost-optimization backfill mode) and wire `mvp_mode=True` through from a
      CLI flag or config, or (b) if the full-universe-unfiltered fetch is actually the intended production behavior and
      the MVP-scoped fetch path was speculative/never-needed, delete `mvp_mode`, `_resolve_by_dataset`'s dead branch,
      and `get_mvp_databento_symbols_for_venue` (checking its unit test first) rather than keep unreachable code around.
      ~~Operator call — not prescribed here.~~ Direction (a) shipped 2 days after filing: `market-tick-data-service@e7581b8b`
      added a `--mvp-mode` CLI flag threading `mvp_mode` through the full call chain to `_resolve_by_dataset`'s
      previously-dead branch.
- [x] ✅ [SCRIPT] P2. **DONE `market-tick-data-service@e7581b8b` + `@6bc9d676`.** **Implement the chosen direction** — either wire a real caller + add a regression test proving
      `mvp_mode=True` actually narrows the fetched instrument set for a real venue (e.g. CME), or remove the dead path
      cleanly (no shims, delete the now-unused registry function + its dedicated test file/class).
      `e7581b8b` (2026-07-10) wired `TickDataHandler._resolve_fetch_params()` reading `args.mvp_mode` through
      `process_ticks`→orchestrator `_state.py`→`venue_fetch._process_venue`→`_fetch_one_venue`→
      `fetch_tick_data_for_venue`→`_route_databento`→`DatabentoAdapter.download_batch_df`→`_resolve_by_dataset` — the
      exact dead branch this issue cited is now genuinely reachable. `6bc9d676` (2026-07-11) added regression tests
      (`test_handler.py::test_process_forwards_mvp_mode_true_from_args`, a CME-narrowing assertion in
      `test_databento_adapter_logic.py`), commit message states "71 relevant tests pass, full quality-gates.sh green."
- [x] ✅ [SCRIPT] P2. **DONE — both commits carry `Quickmerge: agent` trailers.** **Ship via quickmerge**, quality-gates green in both `market-tick-data-service` and
      `unified-api-contracts` if the removal path is chosen.
      Both `e7581b8b` and `6bc9d676` verified ancestors of `origin/live-defi-rollout`
      (`git merge-base --is-ancestor` confirmed 2026-07-29) — shipped to the shared branch, not local WIP.

## Progress Log

- **2026-07-08** — Filed from the operator-requested MVP-catalogue-code audit. Root cause re-verified directly before
  filing: `rg -rn "mvp_mode=True|mvp_mode = True"` across the whole workspace (all repos) returns zero matches;
  `get_mvp_databento_symbols_for_venue`'s only callers are its own unit test and the dead branch. No fix applied yet —
  operator decision needed on direction (a) vs (b) above.
- **na-eligibility-audit 2026-07-29**: ARCHIVE. All 3 todos resolved by shipped code
  (`market-tick-data-service@e7581b8b`+`@6bc9d676`, both 2026-07-10/11, both confirmed ancestors of
  `origin/live-defi-rollout`) — the operator decision was never explicitly recorded in this doc, but the shipped
  commit's own inline comment names this issue doc, and a wholly separate contemporaneous audit
  (`instruments_remaining_work_audit_2026_07_10.md` lines 952-958, filed the same day) independently corroborates the
  same fix. Not a data-loss bug either before or after (full universe was always a superset of MVP). Archiving per the
  6-step ritual — see corpus referrer fixes in the same commit.
