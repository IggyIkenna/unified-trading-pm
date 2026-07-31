---
doc_type: issue
title: Extend UAC mdps_mvp_universe() with a data_type axis + total-over-asset_group handling
summary: >-
  Prerequisite for mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md's exec-dispatch wiring todo,
  which needs a boot-time shard-discovery enumerator returning WHICH (venue, data_type) shards are live for a given
  asset_group. The nearest existing UAC primitive, unified_api_contracts.canonical.crosscutting._mvp_scope_mdps
  .mdps_mvp_universe(asset_group), returns {(venue, instrument_type)} — missing the data_type axis — and raises
  ValueError for sports/prediction/models, so it is not total over every asset_group a co-located MDPS+features live VM
  can run. Operator-ruled 2026-07-30 (BLK-fd70b57c): extend this ONE UAC function rather than add a sibling enumerator
  (keeps a single universe definition per the shard-atom-identity + SSOT-in-UAC hard rules) or hand-list a bash array
  (rejected — the exact drift surface those rules exist to prevent) or repurpose the live-VM staleness watcher (wrong
  tool + boot-time ordering hazard).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [uac, mdps, features-service, mvp-scope, shard-discovery, ssot, live-launch]
related:
  [
    /plans/active/issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Operator ruling 2026-07-30 on BLK-fd70b57c (slot-6 blocked question), answering
  mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md's 2026-07-30 investigation note on the
  never-decided shard-discovery mechanism.
resolved_by:
---

# Extend UAC `mdps_mvp_universe()` with a `data_type` axis

## Why this exists

`mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`'s exec-dispatch wiring todo cannot ship code
without a way for the co-located MDPS+features live VM to learn, at boot, WHICH `(venue, data_type)` shards are live for
its `asset_group` — no `discover_live_shards`/`get_mvp_shards`-style function exists anywhere in the workspace today
(confirmed via a fresh Explore-agent sweep across deployment-service, deployment-api, instruments-service, MTDS, MDPS,
features-service, and UAC, 2026-07-30).

The nearest primitive, `unified_api_contracts.canonical.crosscutting._mvp_scope_mdps.mdps_mvp_universe(asset_group)`,
already returns a UAC-derived `frozenset[tuple[venue, instrument_type]]` — one axis short of what the launcher needs
(`data_type`, not `instrument_type`) — and raises `ValueError` for `sports`/`prediction`/`models`, so it is not total
over every asset_group a co-located MDPS+features live VM might run for.

The operator ruled (2026-07-30, BLK-fd70b57c) that extending this ONE function is the correct SSOT-preserving path — not
a hand-maintained bash array (the exact "shard atom identical across writer/manifest/status/gate/UI" drift surface the
DATA hard rule forbids) and not repurposing `live_stream_watcher.build_prediction_live_shards()` (a post-hoc "what IS
live" staleness-alerting primitive, wrong contract for a pre-launch "what SHOULD be live" decision, and a boot-time
ordering hazard).

## Todos

- [x] ✅ [BACKEND] P2. In `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_mdps.py`,
      extend `mdps_mvp_universe(asset_group)` so its return carries the `data_type` axis alongside the existing `venue`
      (and, if still needed by its current callers, `instrument_type`) — derived from the same canonical config the
      function already reads, so the new axis stays identical to the writer's shard atom (no second, hand-maintained
      definition). Evidence: `unified-api-contracts@724b6633` — `mdps_mvp_universe` now returns
      `frozenset[tuple[venue, instrument_type, data_type]]`, derived via `get_mvp_data_types_for_cefi_venue_itype` for
      cefi and the flat `data_types` product for defi/tradfi (same canonical config as before, no second definition).
      `TestMdpsMvpUniverse` in `tests/unit/test_mvp_scope.py` asserts exact-set identity against `MVP_SCOPE` for
      cefi/defi/tradfi (implies every individual `(venue, data_type)` pair) plus explicit known-pair spot-checks
      (`DERIBIT/OPTION/options_chain`, `BINANCE-FUTURES/PERPETUAL/trades`, `CME/FUTURE/ohlcv_1m`,
      `NASDAQ/EQUITY/ohlcv_1m`). The 3 existing 2-tuple callers (`liquid_representative.py` x2, `execution_fidelity.py`)
      were updated to project down to `(venue, instrument_type)` in the same commit.
- [x] ✅ [BACKEND] P2. Fix the `ValueError` `mdps_mvp_universe()` raises for `sports`/`prediction`/`models` so the
      function is total over every asset_group value a co-located MDPS+features live VM can run for (the exec-dispatch
      wiring todo calls this at boot with whatever `asset_group` the launcher was given — a partial function there
      reintroduces the same silent-failure class this whole issue chain is about). Evidence:
      `unified-api-contracts@724b6633` (same commit as above — the two todos shipped together) —
      `test_sports_is_total_returns_empty`, `test_prediction_is_total_returns_empty`,
      `test_models_is_total_returns_empty` all assert `mdps_mvp_universe(...) == frozenset()` with no raise;
      `test_unknown_asset_group_raises` confirms a genuinely undeclared asset_group still raises, so the two cases stay
      distinguishable.
- [ ] [BACKEND] P3. Run the post-phase codex audit on any codex doc describing `mdps_mvp_universe()`'s contract/shape
      (grep `codex/` for `mdps_mvp_universe` / `_mvp_scope_mdps`) since its signature changed — update or
      SUPERSEDED-banner anything now stale.
- [x] ✅ [BACKEND] P2. **NEW 2026-07-31 (slot-8, discovered via `market-data-processing-service`'s `quality-gates.sh` §
      "PIPELINE-E2E-CHECK DRIVER SMOKE" step — non-blocking on QG's own exit code, but a real enumeration break).**
      `market-data-processing-service/scripts/pipeline_e2e_check.py::_candle_data_types_for_market_ag` (line ~436) was
      missed by todo 1's caller-update sweep (that sweep covered only `unified-api-contracts`-internal callers —
      `liquid_representative.py` x2 + `execution_fidelity.py` — not this cross-repo consumer) — it still does
      `for venue, instrument_type in mdps_mvp_universe(ag_lower):`, a 2-tuple unpack against the now-3-tuple
      `(venue, instrument_type, data_type)` return, raising `ValueError: too many values to unpack (expected 2)` on
      every call. Confirmed pre-existing (present at `market-data-processing-service` HEAD before slot-8's unrelated
      `content_check` commit touched this file) — repro:
      `python scripts/pipeline_e2e_check.py --dry-enumerate --asset-group cefi` (or run `bash scripts/quality-gates.sh`,
      § "PIPELINE-E2E-CHECK DRIVER SMOKE"). Fix: update the unpack to the 3-tuple shape and re-derive
      `_candle_data_types_for_market_ag`'s per-venue data_type set directly from the enumerated `data_type` axis (the
      function's whole purpose is producing `(venue, data_type)` pairs — the now-redundant separate
      `_mvp_data_types_for_cell`/`get_mvp_data_types_for_cefi_venue_itype` derivation downstream may be collapsible into
      this one read, but verify against the real UAC universe before removing it). Repo:
      `market-data-processing-service`. Evidence: `market-data-processing-service@4a5985b` —
      `_candle_data_types_for_market_ag` now unpacks the 3-tuple directly
      (`for venue, _instrument_type, dt in     mdps_mvp_universe(ag_lower)`) and `_mvp_data_types_for_cell` was removed
      (verified collapsible: cefi's data_type axis in `mdps_mvp_universe` IS `get_mvp_data_types_for_cefi_venue_itype`,
      defi's IS the flat `DATA_TYPES_BY_ASSET_GROUP["defi"]` set per `_mvp_scope_rules.py`'s `_mvp_defi_data_types()`
      docstring, and tradfi's flat `{ohlcv_1m, ohlcv_1s}` set is the correct MVP scope — narrower than but a
      superset-consistent replacement for the old base_ccy-ungated is_mvp-probe fallback). Now-unused
      `get_mvp_data_types_for_cefi_venue_itype` / `is_mvp` imports dropped. Repro re-run clean post-fix:
      `--dry-enumerate` produces 819/91/1974 shard-cells for cefi/tradfi/defi respectively with no unpack error;
      `bash scripts/quality-gates.sh` PIPELINE-E2E-CHECK DRIVER SMOKE step passes.

## Progress Log

- **2026-07-30**: Forked out of `mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md` per operator
  ruling on BLK-fd70b57c — that doc's exec-dispatch wiring todo now `depends_on` + `gate_on_depends: true` this doc.
- **2026-07-31 (slot-9)**: Todos 1+2 were already shipped together in `unified-api-contracts@724b6633`
  (`feat(mvp-scope): extend mdps_mvp_universe with a data_type axis`) — landed on `live-defi-rollout` and already
  promoted through to `main`, commit status `success` (`sit-gate/fleet-green` green), but the checkbox flip was never
  done (a Commit+Push+Flip gap on whoever shipped it). Verified via source read + the `TestMdpsMvpUniverse` regression
  suite + the GitHub commit-status API, then flipped both checkboxes here to match shipped reality. Todo 3 (codex audit)
  is untouched — genuinely not yet done, left for its own dispatch (`uac_mdps_mvp_universe_data_type_axis-003`).
- **2026-07-31 (slot-6)**: Fixed todo 4's `market-data-processing-service` cross-repo consumer break —
  `pipeline_e2e_check.py@4a5985b`. Confirmed via source read that `mdps_mvp_universe`'s data_type axis is already the
  SSOT resolution the old `_mvp_data_types_for_cell` helper duplicated (cefi: same
  `get_mvp_data_types_for_cefi_venue_itype` call; defi: same flat `DATA_TYPES_BY_ASSET_GROUP["defi"]` set; tradfi: the
  precise `{ohlcv_1m, ohlcv_1s}` MVP set, replacing a base_ccy-ungated `is_mvp` probe that used to fall back to the full
  candidate set), so collapsed the redundant derivation per the todo's suggestion instead of just widening the unpack.
  quality-gates.sh green + PIPELINE-E2E-CHECK DRIVER SMOKE passing is the regression proof (no unit test previously
  covered this enumeration path).
