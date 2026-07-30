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

- [ ] [BACKEND] P2. In `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_mdps.py`, extend
      `mdps_mvp_universe(asset_group)` so its return carries the `data_type` axis alongside the existing `venue` (and,
      if still needed by its current callers, `instrument_type`) — derived from the same canonical config the function
      already reads, so the new axis stays identical to the writer's shard atom (no second, hand-maintained definition).
      Evidence: the new return shape + a passing regression test asserting it against at least one known
      `(venue, data_type)` pair per currently-supported asset_group.
- [ ] [BACKEND] P2. Fix the `ValueError` `mdps_mvp_universe()` raises for `sports`/`prediction`/`models` so the function
      is total over every asset_group value a co-located MDPS+features live VM can run for (the exec-dispatch wiring
      todo calls this at boot with whatever `asset_group` the launcher was given — a partial function there reintroduces
      the same silent-failure class this whole issue chain is about). Evidence: a passing regression test calling
      `mdps_mvp_universe()` for `sports`, `prediction`, and `models` without raising.
- [ ] [BACKEND] P3. Run the post-phase codex audit on any codex doc describing `mdps_mvp_universe()`'s contract/shape
      (grep `codex/` for `mdps_mvp_universe` / `_mvp_scope_mdps`) since its signature changed — update or
      SUPERSEDED-banner anything now stale.

## Progress Log

- **2026-07-30**: Forked out of `mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md` per operator
  ruling on BLK-fd70b57c — that doc's exec-dispatch wiring todo now `depends_on` + `gate_on_depends: true` this doc.
