---
title: "2-yr config-grid backtest VM launcher authoring + Item #4 bounce-sweep scope decision (operator triage)"
created: 2026-05-10
author: agent-task-2026-05-10-vm-launches
status: resolved-pending-completion
source:
  - audit_2026_05_08_substantial_unfixed_items.md Item #2 (RESOLVED-PENDING-OPERATOR-RUN) + Item #4 (recommended deferral)
  - master_to_live_defi_2026_05_23.md Group F Item 18 (already flipped [x])
  - strategy-service@3dea3c7 — run_2yr_config_grid_backtest.py shipped
  - deployment-service@06f0a54 — launcher + setup-vm routing branch + watchdog dict prefix shipped 2026-05-10
  - deployment-service@5914c83 — script-path invocation fix shipped 2026-05-10
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner: agent-task-2026-05-10-vm-launches (option α executed)
  cadence: one-shot (script execution); review at next daily-split sweep
  verifier: per-archetype `gs://strategy-store-{pid}/backtests/config_grid_2yr/<archetype>/<run_id>/{per_config,summary}.parquet` exists with non-empty rows + sample row inspection passes
  last_executed: "2026-05-10 (launched; running)"
---

## RESOLUTION 2026-05-10 — option (α) executed

Both items shipped per the chain below. The 2 backtest VMs are RUNNING in `asia-northeast1-c`:

- `strategy-backtest-grid-carry-staked-basis-20260510-195855` — STATUS=RUNNING.
- `strategy-backtest-grid-arbitrage-price-dispersi-20260510-195914` — STATUS=RUNNING.

Run logs at `gs://deployment-scripts-central-element-323112/vm-logs/{vm-name}/run.log` show both runners
past the V2 instance registration phase (slot subscription per archetype). Heartbeat blobs present at
`gs://deployment-scripts-central-element-323112/vm-heartbeat/{vm-name}.txt`. Auto-shutdown configured.

ETA for completion: ~8-12h per archetype (medium grid, 2-yr replay window).

Final exit-criteria closure (writing per-config / summary.parquet to
`gs://strategy-store-central-element-323112/backtests/config_grid_2yr/{archetype}/{run_id}/`) lands when the
runners finish. Operator should reverify event-stream emission + parquet row inspection at that point and
then close this issue + flip master Group F Item 18 evidence cite to reference the actual run_id.

### Code shipped this session

- **deployment-service@`06f0a54`** — `launch-strategy-backtest-grid-vm.sh` (new, 232 LOC) +
  `setup-data-pipeline-vm.sh` `strategy-backtest-grid` VM_TASK branch + `vm_zombie_watchdog.py`
  `strategy-backtest-grid-` prefix registration (heartbeat-only).
- **deployment-service@`5914c83`** — fix: invoke as `python scripts/run_2yr_config_grid_backtest.py` (script
  path) not `python -m strategy_service.scripts.run_...` (module path). The repo's `scripts/` directory is
  not part of the `strategy_service` package (no `__init__.py`); first launch attempt failed with
  ModuleNotFoundError, fixed in second launch.

### Item #4 — formally deferred per audit doc recommendation

No work this session. Tracking remains at
`mtds_databento_path_streaming_2026_05_07.md` Phase 4 per audit recommendation (b).

# 2-yr config-grid backtest operational completion + Item #4 bounce-sweep deferral

> **Severity**: P0 — Item #2 master Group F Item 18 closure pending operational run. **Blast radius**:
> strategy-service / deployment-service / unified-trading-pm. **Suggested owner**: next strategy/deployment-service
> tab pairing.

## Background — what's already shipped vs operationally pending

Per `audit_2026_05_08_substantial_unfixed_items.md` Item #2 status update 2026-05-09:

- ✅ Script shipped: `strategy-service/scripts/run_2yr_config_grid_backtest.py` (893 lines, strategy-service@`3dea3c7`)
- ✅ 22 unit tests + smoke verified on both archetypes (`carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION`)
- ✅ basedpyright + ruff clean
- ✅ Master Group F Item 18 line item flipped to `[x]` with same evidence
- ❌ **Full 2-yr grid run NEVER EXECUTED on real infra** — purely operational completion remaining

Per "Plans Run To Actual Completion" HARD RULE (codified 2026-05-08): code-shipped is not the same as operationally-
shipped. The `[x]` flip on master Item 18 is currently leaning on smoke-verified code, NOT a captured grid result.

## What needs to happen — full operational chain

The 2-yr grid run for both archetypes needs to land on real GCE VMs in `asia-northeast1-c`:

### Required artefacts

1. **`deployment-service/scripts/vm/launch-strategy-backtest-grid-vm.sh`** — does not yet exist; must be authored.
   - Mirror `launch-mtds-*-backfill-vm.sh` shape (singleton-locked optional given short prefix collision surface).
   - Args: `--archetype <CARRY_STAKED_BASIS|ARBITRAGE_PRICE_DISPERSION>` `--start YYYY-MM-DD` `--end YYYY-MM-DD`
     `--grid-density coarse|medium|fine` `--vm-name <prefix-ts>` `--zone asia-northeast1-c`.
   - Boots via `gs://deployment-scripts-${PID}/vm/setup-data-pipeline-vm.sh`.
   - Sets metadata `VM_TASK=strategy-grid-backtest` + `VM_BACKFILL_CMD="$VENV/bin/python -m strategy_service.scripts.run_2yr_config_grid_backtest --archetype $VM_STRATEGY_ARCHETYPE --start $VM_START_DATE --end $VM_END_DATE --grid-density $VM_GRID_DENSITY"` (or equivalent — see #2 below).
   - Self-deletes on completion via shutdown-script hook (mirror `launch-strategy-test-vm.sh` lines 153-170).
   - Emits ServiceBootstrap STARTED/STOPPED events to
     `gs://central-element-323112-events/events/strategy-service/<today>/<vm-name>/`.

2. **`deployment-service/scripts/vm/setup-data-pipeline-vm.sh` routing branch** — currently has explicit branches for
   `canonical-migration` / `sports-manifest-rescan` / `sports-gap-fill` / `mdps-sports-bucket` / `sports-scheduler-poll`
   / `manifest-consolidator-poll` / the generic `mdps-backfill / features-backfill / phantom-recon / expected-universe-enum` pool (line 643), and a fallthrough at line 659 that builds `--operation/--mode/--asset-group` CLI args. The
   strategy-grid-backtest does NOT match the fallthrough pattern (script is a standalone runner, not a service CLI
   subcommand). Two options:
   - **(a)** Extend the line-643 branch to accept `strategy-grid-backtest` and run via the existing `VM_BACKFILL_CMD`
     pass-through (~5-line change — consistent with existing pattern).
   - **(b)** Author a fresh `elif [[ "$VM_TASK" == "strategy-grid-backtest" ]]` block that hard-codes the python
     invocation against `VM_STRATEGY_ARCHETYPE` / `VM_START_DATE` / `VM_END_DATE` / `VM_GRID_DENSITY` metadata. Cleaner
     boundary at the cost of one more branch.

   Recommend (a): re-uses the established `VM_BACKFILL_CMD` channel; less workspace-routing-surface drift.

3. **`deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` registration** — add
   `"strategy-backtest-grid-": f"strategy-store-{PROJECT_ID}",` (or `None` if the script doesn't use ManifestWriter —
   verify via grep on `run_2yr_config_grid_backtest.py`; spot check shows it writes parquet directly via
   `google.cloud.storage`, NO `record_captured`, so heartbeat-only is correct → use `None`). Per CLAUDE.md "VM Naming
   Convention" — relaunch the watchdog VM after the dict edit (`gcloud compute instances delete vm-zombie-watchdog-*
   --zone=asia-northeast1-c --quiet` then `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`).

4. **Tarball refresh** — `bash deployment-service/scripts/vm/create-code-tarballs.sh --include strategy-service
   --include deployment-service` (or `--all` if any other repo touched). The launcher uses tarball-based deploy
   (production path) not tarball-from-local. Per CLAUDE.md "VM tarball deployment" — bare `create-code-tarballs.sh`
   only re-tars CORE; the strategy-service tarball MUST be explicitly included.

5. **Launch + verify** (per CLAUDE.md "No fire-and-forget VM launches"):
   ```bash
   RUN_TS="$(date +%Y%m%d-%H%M%S)"

   bash deployment-service/scripts/vm/launch-strategy-backtest-grid-vm.sh \
     --archetype CARRY_STAKED_BASIS \
     --start 2024-01-01 --end 2026-05-01 \
     --grid-density medium \
     --vm-name strategy-backtest-grid-carry-staked-basis-${RUN_TS}

   bash deployment-service/scripts/vm/launch-strategy-backtest-grid-vm.sh \
     --archetype ARBITRAGE_PRICE_DISPERSION \
     --start 2024-01-01 --end 2026-05-01 \
     --grid-density medium \
     --vm-name strategy-backtest-grid-arb-price-dispersion-${RUN_TS}

   sleep 90

   gcloud storage ls gs://central-element-323112-events/events/strategy-service/$(date +%Y-%m-%d)/strategy-backtest-grid-carry-staked-basis-${RUN_TS}/
   gcloud storage ls gs://central-element-323112-events/events/strategy-service/$(date +%Y-%m-%d)/strategy-backtest-grid-arb-price-dispersion-${RUN_TS}/
   ```
   Expected: `hour=*` partition with JSONL containing `event=="STARTED"`. ETA: 8-12h per archetype = ~24h
   wall-clock for both, plus ~15min recheck cadence per CLAUDE.md.

### Estimated scope

- Launcher authoring + setup-script branch + watchdog dict + tarball refresh + smoke-launch + 24h monitoring window =
  ~2-4 hours of focused agent time. Multi-repo commits across strategy-service / deployment-service / unified-trading-pm.

### Why this session deferred the authoring

This agent's session-prompt called for both Task A (2yr backtest) + Task B (18 MTDS bounce-sweep). On reading
[`audit_2026_05_08_substantial_unfixed_items.md`](audit_2026_05_08_substantial_unfixed_items.md):

- **Item #2** (Task A): Status RESOLVED-PENDING-OPERATOR-RUN; the launcher script is genuinely missing. Authoring the
  launcher + setup-script branch + watchdog dict + tarball refresh combined exceeds the 1-hour authoring window the
  prompt declared as defer-threshold. PM repo is also in a heavy multi-agent dirty state (10+ codex doc edits queued
  per `git status`), so a setup-data-pipeline-vm.sh edit risks foot-gun #2 (foreign-WIP clobbering) on the shared
  deployment-service tree. Right action per "Findings Triage Discipline" case-3 (outside this agent's clear context,
  fits another active plan) — file this issue doc + hand back.

- **Item #4** (Task B): Audit doc explicitly recommends **(b) defer-post-cutover**, not (a) launch the bounce-sweep:
  > "Recommended: (b) for this cycle (focus on May-23); track as P1 in `mtds_databento_path_streaming_2026_05_07.md`
  > Phase 4 (real-VM validation gap is already noted there)."

  Per CLAUDE.md "Clear context = implement, don't ask" — the audit doc names the canonical answer. Launching 18 VMs
  this session would directly contradict the audit's own recommendation + risk Tardis rate-limit collision with the
  existing 9 cefi heavy-backfill VMs that are running fine. The singleton-lock pattern in
  `launch-cefi-sharded-backfill.sh` (lines 85-100) would refuse the launch.

## Recommended decision

**Item #2 next steps** — pick one:
- **(α)** Spawn a focused next-session agent (Tab 2 strategy-service + deployment-service paired) with explicit scope
  to author the launcher + setup-script branch + watchdog dict + tarball refresh + grid run launches per the chain
  above. Expected ETA: 1 day to ship + monitor.
- **(β)** Operator runs the script locally via `python -m strategy_service.scripts.run_2yr_config_grid_backtest
  --archetype CARRY_STAKED_BASIS --start 2024-01-01 --end 2026-05-01 --grid-density medium` from the workstation
  (the script writes to `gs://strategy-store-{pid}/...` directly via ADC; no VM needed). 8-12h local run; faster than
  authoring the launcher + monitoring 2 VMs. Drawback: ties up operator workstation.
- **(γ)** Drop `--grid-density medium` (3,125 configs) → `coarse` (243 configs); local run shrinks to ~30-60min.
  Coverage is thinner but unblocks the operational evidence the master plan flip is leaning on.

Recommend (α) given May-23 deadline pressure + the work needs to be re-runnable as live config evolves.

**Item #4** — formally adopt audit recommendation (b): defer post-May-23 cutover. Track as P1 in
`mtds_databento_path_streaming_2026_05_07.md` Phase 4. No new work this cycle.

## Exit criteria

For Item #2 closure (when option α executes):
- ✅ `launch-strategy-backtest-grid-vm.sh` shipped to `deployment-service/scripts/vm/`.
- ✅ `setup-data-pipeline-vm.sh` routes `VM_TASK=strategy-grid-backtest` to the strategy-service runner.
- ✅ `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` registers `strategy-backtest-grid-` prefix.
- ✅ Tarball refreshed via `create-code-tarballs.sh --include strategy-service --include deployment-service`.
- ✅ Watchdog VM relaunched.
- ✅ 2 backtest VMs launched + verified emitting STARTED in <90s.
- ✅ Both VMs auto-shut + STOPPED event captured + `summary.parquet` exists at expected GCS path with non-empty rows.
- ✅ Master Group F Item 18 evidence cite updated to reference the actual run_id + grid output URI (currently leans on
  the smoke-only `[x]` flip).

## Cross-references

- `audit_2026_05_08_substantial_unfixed_items.md` Item #2 + Item #4
- `master_to_live_defi_2026_05_23.md` Group F Item 18
- `strategy-service@3dea3c7` — `run_2yr_config_grid_backtest.py`
- `deployment-service/scripts/vm/launch-strategy-test-vm.sh` — closest existing template (pipeline-based, not script-runner-based; pattern to mirror for shutdown-script hook + metadata shape)
- `deployment-service/scripts/vm/setup-data-pipeline-vm.sh:643-686` — VM_TASK routing branches
- `deployment-service/scripts/vm/vm_zombie_watchdog.py:113-200` — `VM_PREFIX_TO_BUCKET` registry
