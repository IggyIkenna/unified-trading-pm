---
doc_type: issue
title:
  launch-mdps-features-live.sh's compound VM_SERVICE has no exec-dispatch branch in setup-data-pipeline-vm.sh — falls
  through to a literal `python -m market_data_processing_service+features_service`, and even a correct per-service
  branch can't invoke either service today because neither's CLI supports the launcher's premise
summary: >-
  With the dependency-install bug
  (/plans/archive/issues/mdps_features_live_launcher_shared_venv_dependency_conflict_2026_07_26.md) fixed, a live-VM
  verification (`mdps-features-live-cefi-20260727-004133`) got past `uv pip install` cleanly for the first time,
  exposing the NEXT bug in the same launcher: `setup-data-pipeline-vm.sh` has no exec-dispatch branch for
  `VM_TASK=mdps-features-live` (or any compound "+"-joined `VM_SERVICE` at run time — only the tarball-resolution
  section was fixed to split on "+"), so it falls through to the generic default `python -m $VM_SERVICE $CLI_ARGS`,
  literally invoking `python -m market_data_processing_service+features_service` — not a valid Python module path.
  Worse: even a correctly-split two-process branch cannot work today without further design, because **neither service's
  actual CLI supports what the launcher's design assumes**: MDPS's live path (`process --mode live --operation
  streaming-aggregation`) requires an explicit single `--shard-spec ASSET_GROUP:VENUE:DATA_TYPE`, not a
  whole-asset-group run, and features-service's top-level CLI dispatches to exactly ONE of 9 `--feature-family`
  sub-packages per invocation — there is no "run all live for this asset_group" mode for either service. The launcher's
  own docstring already flags this as unfinished ("operational launch awaits Harsh slot 5 per-service consumer wiring +
  Phase 12 reconciliation gate green"; archived `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 15 =
  "DEFERRED-POST-CUTOVER... successor plan"), so this is a confirmed, evidenced instance of a known-and-labeled gap, not
  a regression — but it means "get genuine live-VM confirmation" cannot be fully satisfied for this launcher until real
  design work on shard/family iteration lands.
status: open
nature: issue
asset_group: [cefi, cross-cutting]
stage: [meta]
repos: [deployment-service, market-data-processing-service, features-service]
scope: [engineer, admin]
tags:
  [mdps, features-service, vm-launcher, exec-dispatch, live-launch, cli-contract-mismatch, design-gap, silent-failure]
related:
  [
    /plans/archive/issues/mdps_features_live_launcher_shared_venv_dependency_conflict_2026_07_26.md,
    /plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.36
assigned_role: infra_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: interactive session, live-VM verification of the sibling dependency-conflict fix, 2026-07-27
resolved_by:
---

# launch-mdps-features-live.sh exec-dispatch was never actually wired up

## Evidence

Launched `mdps-features-live-cefi-20260727-004133` to verify the dependency-install fix in
`/plans/archive/issues/mdps_features_live_launcher_shared_venv_dependency_conflict_2026_07_26.md`. Bootstrap now
succeeds cleanly (no more `position-balance-monitor-service` unsatisfiable conflict — that fix is confirmed correct).
`run.log` then showed:

```
[vm-exec] starting: bash -c ( ... ) & ...; /home/ikennaigboaka/venv/bin/python -m market_data_processing_service+features_service --operation live_aggregate_and_compute --mode live --asset-group CEFI
/home/ikennaigboaka/venv/bin/python: No module named market_data_processing_service+features_service
[vm-exec] command exited rc=1
```

VM deleted after confirming the failure (no reason to keep an e2-standard-8 billing on a known-broken exec path).

## Root cause — two independent gaps, not one

**Gap 1 — no exec-dispatch branch for this VM_TASK/compound VM_SERVICE.** `setup-data-pipeline-vm.sh`'s tarball
resolution section (fixed 2026-07-26) splits `VM_SERVICE` on "+" to resolve the right tarballs, but the RUN-command
construction later in the same script has no equivalent branch — `VM_TASK=mdps-features-live` matches none of the
existing special cases (`strategy-paper`/`synthetic-benchmark`/etc.), so it falls through to the generic default (~line
2042): `_launch_with_tee "$VENV/bin/python -m $VM_SERVICE $CLI_ARGS" ...` — passing the raw, unsplit
`"market_data_processing_service+features_service"` straight to `python -m`, which is never a valid module path for any
compound value.

**Gap 2 — even a correctly-split two-process branch can't work without further design**, because the launcher's premise
(one co-located live consumer per (MDPS, features-service) pair, scoped to a whole `asset_group`) doesn't match either
service's actual CLI surface as it exists today:

- MDPS's live path is `process --mode live --operation streaming-aggregation --shard-spec ASSET_GROUP:VENUE:DATA_TYPE`
  (`market-data-processing-service/market_data_processing_service/cli/parser.py` lines ~276-322) — `--shard-spec` is
  required and scopes to exactly ONE venue+data_type, not a whole asset_group. `VM_OPERATION=live_aggregate_and_compute`
  (set by the launcher) also doesn't match any of MDPS's actual `--operation` choices
  (`timer-candles`/`streaming-aggregation`/`build-continuous`) — the intended value is almost certainly
  `streaming-aggregation`, but the launcher was never updated to pass it, or `--shard-spec`, at all.
- features-service's top-level CLI (`features-service/features_service/cli/main.py`) dispatches to exactly ONE of 9
  `--feature-family` sub-packages per invocation (calendar/commodity/cross_instrument/delta_one/multi_timeframe/
  onchain/performance_features/sports/volatility) — there is no "run every applicable family live for this asset_group"
  mode. Which families apply to a given `asset_group` (e.g. does `cefi` need all 9, or a subset?) is a real
  product/domain decision, not something inferable from the code alone.

## Why this wasn't caught earlier

This is a **known, already-labeled gap**, not a silent regression: `launch-mdps-features-live.sh`'s own docstring says
"ships code-ready as part of Phase 13; operational launch awaits Harsh slot 5 per-service consumer wiring + Phase 12
reconciliation gate green" — and the archived plan that shipped it
(`plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md`, `status: complete`) explicitly deferred Phase
15 ("Workspace-wide QG sweep + 7-day live smoke... **DEFERRED-POST-CUTOVER**... Phase 15 → successor plan"). The
launcher was shipped "code-ready" against a design that assumed a monolithic per-asset-group live consumer; neither
MDPS's nor features-service's CLI ever grew that shape, and because Gap 1 (the dependency-conflict bug this session's
sibling issue fixed) made every prior launch attempt die at `uv pip install` — long before reaching the `python -m` line
— Gap 2 was structurally unreachable and unobserved until today's fix let a VM get far enough to hit it.

## Why this is NOT a same-session mechanical fix

Per workspace planning discipline, a todo is only mechanically dispatchable when its outcome is determinable by the
worker alone. "Which feature families run live for which asset_group, and does MDPS's live streaming-aggregation model
even support a whole-asset-group co-located consumer or does it need N per-shard sibling processes" is a real
design/product decision, not a lookup — inventing an answer under this issue risks a plausible-looking but wrong fix
(e.g. silently guessing "all 9 families, one asset_group-wide `--shard-spec` per venue actually present" without knowing
whether that matches the intended architecture or the co-location assumption behind "MDPS→features handoff stays
in-process / sub-ms" still holds once features-service is genuinely family-sharded).

## Todos

- [ ] [OPERATOR] P2. Decide the intended exec-dispatch shape for `VM_TASK=mdps-features-live`: (a) does MDPS run one
      process per live shard (`ASSET_GROUP:VENUE:DATA_TYPE`) discovered from the instruments universe, with
      features-service running once per applicable `--feature-family` subscribing to the same asset_group's
      `candle_computed` stream — or (b) some other shape entirely? Needs sign-off before a worker can wire the actual
      branch. Reference: Phase 15 successor plan (`live_pipeline_mtds_mdps_features_2026_05_08.md`, if a successor plan
      exists — none found under `plans/active/` as of this issue's filing; may need to be created).
- [ ] [SCRIPT] P2. Once the shape is decided: add a `VM_TASK == "mdps-features-live"` (or generic "+"-split) branch to
      `setup-data-pipeline-vm.sh`'s exec-dispatch section (mirrors the existing tarball-resolution split + the
      multi-worker sharding pattern at ~line 2031 for backgrounding N python processes under one `_launch_with_tee`
      wrapper) that invokes MDPS and features-service with the CLI flags their actual parsers require, per the decided
      shape.
- [ ] [SCRIPT] P3. Also fix `launch-mdps-features-live.sh`'s `VM_OPERATION=live_aggregate_and_compute` metadata value —
      it doesn't match any of MDPS's real `--operation` choices (`timer-candles`/`streaming-aggregation`/
      `build-continuous`); once the dispatch branch is designed, set the metadata this launcher passes to match whatever
      the branch actually consumes.
- [ ] [SCRIPT] P3. Related, smaller gap noticed in passing: `vm-exec-with-gcs-tee.sh`'s post-launch task-failure path (a
      wrapped command exiting non-zero AFTER bootstrap succeeded, as happened here —
      `[vm-exec] command exited     rc=1`) does not appear to self-delete or otherwise loudly signal on a
      `VM_SHUTDOWN_ON_COMPLETION=false` live launcher, mirroring (but distinct from) the bootstrap-phase gap fixed in
      `/plans/archive/issues/mdps_features_live_launcher_shared_venv_dependency_conflict_2026_07_26.md` Update 4 — not
      investigated further here since it's a different code path (the tee wrapper, not `_self_delete_on_setup_failure`);
      worth auditing once Gap 1/2 above are resolved and a real live launch exists to observe its failure-signaling
      behavior against.
