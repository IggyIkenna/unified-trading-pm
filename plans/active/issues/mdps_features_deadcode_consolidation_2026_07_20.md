---
doc_type: issue
title:
  MDPS + features dead-code / orphan-launcher consolidation — broken/registered-but-unrunnable launchers, a monitoring
  blind spot, and stale post-consolidation config (surfaced building /data-pipeline-check-mdps + -features)
summary: >-
  Grep-then-read-verified dead-code + orphaned-launcher findings in deployment-service / features-service /
  market-data-processing-service, surfaced by the pass-2 audit while building the two data-pipeline-check skills. THREE
  are big findings needing an operator keep/delete decision because of self-heal / registered-live-launcher blast
  radius: (S1-a) launch-prediction-features-vm.sh is BROKEN — it packages the removed features-cross-instrument-service
  repo and its import-verify ModuleNotFounds under set -e, yet launcher_registry.py binds the prediction-features-
  relaunch to it, so an OOM/preempted prediction-features VM self-heals via a launcher that cannot succeed (also: no
  SPOT, 50GB disk that escapes the disk QG, no live-collision guard); (S1-b) launch-mdps-features-live.sh is registered
  production-ready in vm_prefix_registry.py (5 rows) but has no dispatcher branch and emits
  VM_SERVICE=market_data_processing_service+features_service (a + in a module name) → ModuleNotFoundError; its enabling
  plan is archived; (S1-c) launch-mdps-sharded-backfill.sh emits mdps-sports-<year>-<ts> VM names that are registered in
  NEITHER vm_prefix_registry.py NOR launcher_registry.py, so a preempted sports MDPS shard is invisible to the zombie
  watchdog and has no relaunch binding — and the parity test misses it because both registries agree with each other.
  Plus lower-severity dead code (S2/S3) that is safe to trim.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [deployment-service, features-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dead-code, orphan, vm-launcher, registry, self-heal, monitoring, consolidation, mdps, features]
related: [../data_pipeline_check_mdps_features_2026_07_20.md, /codex/05-infrastructure/vm-launcher-runbook.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  pass-2 audit (6 sub-agents, 2026-07-20) while building /data-pipeline-check-mdps + /data-pipeline-check-features; all
  findings verified by direct Read at the cited file:line, no conclusion rests on a grep-0.
---

# MDPS + features dead-code / orphan-launcher consolidation

> Filed autonomously 2026-07-20 while the operator is away. The three S1 findings are BIG (blast radius on a shared
> fleet the operator returns to: self-heal rebinding, deleting a registered live-pipeline launcher, registry parity) —
> per findings-triage they are documented here + surfaced in the final report, NOT auto-deleted. S2/S3 are safe trims.

## Big findings — operator keep/delete decision (options)

**Recommended (A):** delete the two orphan launchers (S1-a, S1-b) + their registry rows, and close the `mdps-sports-`
registry gap (S1-c) by registering it. **(B):** finish `launch-mdps-features-live.sh`'s dispatcher branch and keep it;
repoint S1-a's self-heal to `launch-features-vm.sh`. **(C):** do only the `mdps-sports-` registry gap now, defer the
launcher deletions. Other: operator free-text.

## Todos

- [ ] 1. [SCRIPT] P2. S1-a — `launch-prediction-features-vm.sh` BROKEN (packages removed
      `features-cross-instrument-service`, import-verify ModuleNotFounds under `set -e`; no SPOT; 50GB disk escaping the
      disk QG; no live-collision guard; `launcher_registry.py:154` binds `prediction-features-` self-heal to it).
      Superseded by `launch-features-vm.sh --feature-family cross_instrument --asset-group PREDICTION`. DELETE + repoint
      registry (pending operator A/B/C).
- [ ] 2. [SCRIPT] P2. S1-b — `launch-mdps-features-live.sh` non-runnable (no dispatcher branch;
      `VM_SERVICE=market_data_processing_service+features_service` → ModuleNotFoundError; plan archived) but registered
      in `vm_prefix_registry.py:841-851` (5 rows). DELETE launcher + 5 rows OR finish the dispatcher branch (pending
      operator).
- [ ] 3. [SCRIPT] P1. S1-c — `mdps-sports-<year>-<ts>` emitted by `launch-mdps-sharded-backfill.sh:206` but registered
      in NEITHER `vm_prefix_registry.py` NOR `launcher_registry.py` → sports MDPS shard invisible to zombie watchdog +
      no relaunch binding; parity test misses it (both registries agree). Add `mdps-sports-` (bucket `_TICK_SPORTS`,
      EPHEMERAL_BATCH) to both, OR drop `sports` from the sharded launcher default set. Add a launcher→emitted-name
      test.
- [ ] 4. [SCRIPT] P3. S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (lines 170-309 unreachable dead
      body; duplicate `lc_verify_tarball_freshness` 274-278/280-284; pre-consolidation module names in
      `_python_module_for`).
- [ ] 5. [SCRIPT] P3. S2-b — delete the 8 stale `features_*_service` keys in `setup-data-pipeline-vm.sh`
      SERVICE_TARBALLS (post-2026-05-08 consolidation; only `features_service` is built). Adjacently fix the stale
      `ml_*_service` keys.
- [ ] 6. [SCRIPT] P3. S3-a — delete MDPS one-offs past `Delete-when` after verifying each condition:
      `reconcile_mdps_available_at_2026_05_13.py`, `reconcile_mdps_available_at_off_by_one_2026_05_10_2026_05_11.py`,
      `reconcile_1440_nan_placeholders.py`. KEEP `benchmark_fullmonth_binance.py` (reused for the MDPS steady-state
      benchmark in the parent plan; its `Delete-when` plan is archived but the tool is in active use).
- [ ] 7. [SCRIPT] P3. S3-c — repoint `features-service/scripts/sports/smoke_matrix.py` SSOT citations (archived plan +
      dead `launch-features-backfill-vm.sh` header) to `launch-features-vm.sh` + the codex smoke-matrix doc.
- [ ] 8. [SCRIPT] P3. S3-b — sports dual entrypoint (`python -m features_service.sports` with `--tables`/sfi-progressive
      vs `--feature-family sports`) — operator/design adjudication (fold submodule behind the family flag OR bless the
      submodule). Do NOT silently delete (breaks live sports backfills). Also the misleading "DEPRECATION NOTE" on the
      live `launch-features-sports-*` launchers.

## Data-orphan findings (from the same audit — tracked in the parent plan, not here)

Feature families `performance_features` + `strategy_pnl_archetype` = honest-by-design orphans (unwired
StrategyPnlStreamEvent → always `empty_confirmed(EXPECTED_NO_PNL_STREAM)`; consumers NO-OP/post-cutover). Candle cells
produced-but-unconsumed to VERIFY: TRADFI `ohlcv_1s`, DEFI `book_snapshot_5/market_state/liquidity/fx_rates`, SPORTS
`arbitrage_opportunity`; upstream trap TRADFI `mbp_10` (`needs_candle_processing` defaults True, no adapter, not
captured → should be pinned False). These are handled by the `/data-pipeline-check-mdps` + `-features` skills' canonical

- orphan checks (parent plan `data_pipeline_check_mdps_features_2026_07_20.md` todos 11/13).
