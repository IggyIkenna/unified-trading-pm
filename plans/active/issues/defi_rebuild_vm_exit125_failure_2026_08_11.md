---
doc_type: issue
title: >-
  `canonical-migration-defi-rebuild-20260810-113426` failed with exit_code=125 — new failure mode, not OOM; RB-INFRA-RELAUNCH bound reached
summary: >-
  The on-demand rebuild VM (`-113426`, launched after two SPOT-preemption attempts on `-093118`/`-101545`) reached
  terminal `status=failed, exit_code=125` with `reap_reason=vm_not_running`. The OOM fix
  (`market-tick-data-service@483eb895581cc645cf884ba780c871b65060202d`) worked — `mem_pct` peaked at 55.4% vs 94% on the
  prior OOM'd run — but the VM died anyway ~2h53m after start with a different failure signature: run.log stops abruptly
  at `13:16:05Z` with no crash traceback, no signal handler output, no `DEPLOYMENT_FAILED` line. The reaper caught it
  ~14 min later (`13:30:11Z`). This is the 2nd terminal non-completion for the `defi-rebuild` prefix (the SPOT-
  preempted `-093118`/`-101545` pair don't count — zero logs written), reaching RB-INFRA-RELAUNCH's ≤2/(prefix,day)
  bound. A 3rd/4th relaunch requires new root-cause diagnosis.
status: open
nature: issue
asset_group: [defi, infrastructure]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi-rebuild, exit-code-125, vm-failure, rb-infra-relaunch, stop-clause]
related:
  [
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
  ]
created: "2026-08-11"
author: slot-19
last_updated: "2026-08-11"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source: >-
  Slot 19 worker verifying the rebuild VM for
  `/plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 1 — found the VM failed.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
---

# `-113426` failed with exit_code=125 — new failure mode, RB-INFRA-RELAUNCH bound reached

## What the plan's todo 1 asked

`/plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` todo 1: verify the rebuild VM reached
terminal SUCCESS. Its stop clause: "If the VM instead failed again, STOP — do not proceed to todo 2; file a fresh
issue doc citing this plan and the failure evidence, do not blind-retry a 3rd/4th time without new root-cause
information (RB-INFRA-RELAUNCH's stop clause)."

## VM lineage (all `canonical-migration-defi-rebuild-*`)

| VM name | Launched | Status | Exit code | Notes |
|---|---|---|---|---|
| `-20260809-163511` | 2026-08-09T15:43Z | FAILED | 137 (SIGKILL/OOM) | Root cause: unbounded `covered_keys` accumulation. Fix shipped `mtds@483eb89` |
| `-20260810-093118` | 2026-08-10T08:31Z | SPOT-preempted ×2 | N/A | Zero `run.log` written |
| `-20260810-101545` | 2026-08-10T~10:15Z | SPOT-preempted ×2 | N/A | Zero `run.log` written |
| `-20260810-113426` | 2026-08-10T10:37Z | **FAILED** | **125** | ON_DEMAND, run.log stops abruptly at 13:16:05Z |

## What we found on `-113426`

**Deployment record** (`gs://deployment-scripts-central-element-323112/deployments/archive/2026-08-10/9227149b-1762-4227-9e07-fb9c4ca1c24d.json`):
- `status: failed`, `exit_code: 125`
- `reap_reason: vm_not_running` — the reaper found the VM not running at `13:30:11Z`
- Started `10:37:11Z`, completed (reaped) `13:30:11Z` — ~2h53m runtime
- `git_commit: 483eb895581cc645cf884ba780c871b65060202d` (the OOM fix)

**Host metrics** — the OOM fix worked:
- `mem_pct` ranged 34%–55.4% across all 10 samples (vs 61%–94% on the OOM'd run)
- Last sample (`13:16:19Z`): `mem_pct=55.4`, `cpu_pct=18.7`, `io_write=90.5 KB/s`
- No memory climb pattern — `mem_slope` stayed flat-to-moderate

**Run.log** (920 lines, ends at `13:16:05Z`):
- Last log line: `INFO ManifestWriter: per-VM shard updated (2898844 total entries, 5000 new, process_final=False)`
- Last progress marker: `date=2025-09-01: 28961 shards scanned` (at `13:14:52Z`)
- Resumed from `2025-06-02` — made ~3 months of progress covering June–Aug 2025
- **No terminal markers at all** — no `Rebuild complete:`, no `command exited rc=`, no `DEPLOYMENT_FAILED`, no
  `received signal`, no Python traceback
- The log simply **stops** mid-progress

**Heartbeat** (`vm-heartbeat/canonical-migration-defi-rebuild-20260810-113426.txt`):
- Stale: `1786367724` (a boot-time timestamp), status `starting`, last modified `13:15:26Z`
- Heartbeat sidecar was already dead ~15 min before the reaper declared failure

## Analysis

Exit code 125 is NOT 137 (OOM). Common causes of exit 125:
- Docker: `docker run` failed (image pull failure, invalid command)
- `timeout`: command timed out (but no `timeout` wrapper is visible in the run.log command line)
- Shell: `command not found` or similar exec failure

The abrupt log cutoff with no Python traceback/ signal handler output suggests the Python process was killed at the
OS level (not from within Python). The VM itself was ON_DEMAND (not SPOT), so preemption is ruled out. The host
metrics show healthy CPU/memory/IO right up to the last sample. The heartbeat sidecar dying ~15 min before the
reaper noticed the VM was gone is consistent with the entire VM going down hard.

**RB-INFRA-RELAUNCH bound**: the `-113426` failure is the 2nd terminal non-completion for this prefix (the two
SPOT-preempted launches don't count — they had zero logs and were immediate platform rejections, not code failures).
The bound of ≤2/(prefix,day) is reached. A 3rd/4th relaunch requires root-cause diagnosis of THIS failure mode,
not just the prior OOM.

## Impact on downstream work

`/plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` is blocked — its todo 1 stop clause
triggers. The manifest was partially rebuilt (made it to ~2025-09-01 of a 2026-12-31 target, ~2.9M entries written)
but the rebuild did NOT complete, so the manifest is in an intermediate state. The downstream retirement steps
(todos 2–4: retiring POOL/rate_indices/dex_pool_fees legacy rows, triggering honest-coverage rollup) are UNSAFE
against a partially-rebuilt manifest.

## Recommended next steps

- [ ] [INFRA] P1. Root-cause the exit-code-125 failure — check GCE serial console logs for the VM
  (`gcloud compute instances get-serial-port-output canonical-migration-defi-rebuild-20260810-113426 --zone=asia-northeast1-c`),
  check if the VM hit a GCE host error / live migration, and determine whether this is a platform issue or a code bug
  (repo: deployment-service)
- [ ] [DATA] P1. Assess whether the partially-rebuilt manifest (~2.9M entries through 2025-09-01) is safe to use
  for the retirement steps, or whether the rebuild must complete first — check if the consolidator has since merged
  the per-VM shard into the main index (repo: market-tick-data-service)
- [ ] [INFRA] P2. If root cause is platform-level (not code): relaunch with explicit `--end-date 2026-12-31`
  resuming from `last_completed_date=2025-09-01` (the confirmed checkpoint from this run's log) — this would be the
  1st relaunch under a NEW root-cause diagnosis, resetting RB-INFRA-RELAUNCH's counter (repo: deployment-service)
- [ ] [INFRA] P2. If root cause is a code bug: fix, ship, THEN relaunch per the RB-INFRA-RELAUNCH carve-out
  (repo: market-tick-data-service)

## Pointers

- Failed deployment record: `gs://deployment-scripts-central-element-323112/deployments/archive/2026-08-10/9227149b-1762-4227-9e07-fb9c4ca1c24d.json`
- Failed run.log: `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-rebuild-20260810-113426/run.log` (920 lines, ends abruptly)
- Prior OOM issue doc: `/plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md`
- Blocked plan: `/plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md`
- RB-INFRA-RELAUNCH runbook: `/codex/15-runbooks/incidents/rb_infra_relaunch.md`
