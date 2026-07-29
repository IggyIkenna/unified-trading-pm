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
status: open
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
resolved_by:
---

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

- [x] ✅ [DECISION] P2. **Operator-ruled 2026-07-29 (interactive decision session): wire `mvp_mode` to a real caller —
      do NOT delete it. The caller is an opt-in flag on the existing recurring forward-poll launcher
      (`launch-tradfi-forward-poll.sh`), not a brand-new dedicated launcher, and it must stay a manually-invoked
      non-default flag — never silently default-on, per the existing 2026-06-22 "download everything, no client-side
      filters" ruling on the CME backfill launcher. See the new [CODE] P1 todo below for the concrete implementation
      plan.** Decide whether `mvp_mode` should ever be wired live — either (a) find/create a real caller that needs the
      narrower MVP-only fetch (e.g. a cost-optimization backfill mode) and wire `mvp_mode=True` through from a CLI flag
      or config, or (b) if the full-universe-unfiltered fetch is actually the intended production behavior and the
      MVP-scoped fetch path was speculative/never-needed, delete `mvp_mode`, `_resolve_by_dataset`'s dead branch, and
      `get_mvp_databento_symbols_for_venue` (checking its unit test first) rather than keep unreachable code around.
      Operator call — not prescribed here.
- [x] ✅ [SCRIPT] P2. **Operator-ruled 2026-07-29: superseded by the concrete [CODE] P1 todo below** (wire via an opt-in
      `--mvp-mode` flag on `launch-tradfi-forward-poll.sh` — see the (i)-(iv) plan). Implement the chosen direction —
      either wire a real caller + add a regression test proving `mvp_mode=True` actually narrows the fetched instrument
      set for a real venue (e.g. CME), or remove the dead path cleanly (no shims, delete the now-unused registry
      function + its dedicated test file/class).
- [x] ✅ [SCRIPT] P2. **Operator-ruled 2026-07-29: superseded — folded into the new [CODE] P1 todo's own "done when"
      below** (ship via quickmerge once that todo lands, per the standard commit-push-flip discipline). Ship via
      quickmerge, quality-gates green in both `market-tick-data-service` and `unified-api-contracts` if the removal path
      is chosen.
- [ ] [CODE] P1. **Wire `mvp_mode` via an opt-in flag on the existing forward-poll launcher — operator-ruled 2026-07-29
      concrete implementation plan.** (i) Add `VM_MVP_MODE` metadata plumbing to
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`'s `mtds-backfill` branch, mirroring the existing
      `VM_FORCE`/`VM_FORCE_WINDOW` metadata pattern already in that same file (`_meta VM_FORCE` → `--force` on the
      generated CLI). (ii) Add an opt-in `--mvp-mode` CLI flag + `VM_MVP_MODE=true` metadata line to
      `deployment-service/scripts/vm/launch-tradfi-forward-poll.sh` specifically, mirroring that launcher's existing
      `--force` flag parsing (`--force) FORCE=true; shift ;;`) — explicitly NOT changing that launcher's default
      behavior (no flag = today's unfiltered full-universe fetch, unchanged). (iii) Extend the existing regression tests
      (`market-tick-data-service/tests/market_interface/unit/test_databento_adapter_logic.py`,
      `market-tick-data-service/tests/unit/test_handler.py` if this repo is checked out alongside) with a `--dry-run`
      assertion that `VM_MVP_MODE=true` produces `--mvp-mode` in the generated CLI. (iv) Explicitly note
      `launch-tradfi-bf-cme-ohlcv-1m.sh` and `launch-tradfi-backfill-vm.sh` are NOT touched by this ruling — the first
      has its own no-client-side-filters ruling, the second already has its own separate `--instrument-ids` narrowing
      mechanism; both coexist unchanged, `mvp_mode` does not replace either. Repos: deployment-service,
      market-tick-data-service. Done when: (i)-(iii) land QG-green in the affected repo(s), the dry-run regression test
      in (iii) passes, and the change ships via quickmerge (quality-gates green in both `market-tick-data-service` and
      `unified-api-contracts` if that registry function's callsite needs touching).

## Progress Log

- **2026-07-08** — Filed from the operator-requested MVP-catalogue-code audit. Root cause re-verified directly before
  filing: `rg -rn "mvp_mode=True|mvp_mode = True"` across the whole workspace (all repos) returns zero matches;
  `get_mvp_databento_symbols_for_venue`'s only callers are its own unit test and the dead branch. No fix applied yet —
  operator decision needed on direction (a) vs (b) above.
- **2026-07-29 — RULED (interactive decision session).** Operator ruled TWO things: (1) wire `mvp_mode` to a real caller
  — do not delete it; (2) the specific caller is an opt-in flag on the existing recurring forward-poll launcher
  (`launch-tradfi-forward-poll.sh`), NOT a brand-new dedicated launcher, and it must stay a manually-invoked non-default
  flag (never silently default-on, consistent with the 2026-06-22 "download everything, no client-side filters" ruling
  on the CME backfill launcher). All 3 original todos flipped to record this ruling; a new concrete [CODE] P1 todo added
  with the (i)-(iv) implementation plan (VM_MVP_MODE metadata plumbing in `setup-data-pipeline-vm.sh`, opt-in
  `--mvp-mode` flag in `launch-tradfi-forward-poll.sh` only, dry-run regression test, explicit non-touch note for
  `launch-tradfi-bf-cme-ohlcv-1m.sh`/`launch-tradfi-backfill-vm.sh`). Doc stays `status: open` pending that
  implementation todo. Every corpus doc citing this issue as "genuinely operator-gated"/"0 AO-eligible"/"DECISION still
  open" is being retagged in the same pass to point at this ruling.
