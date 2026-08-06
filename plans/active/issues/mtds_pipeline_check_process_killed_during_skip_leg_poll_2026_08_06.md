---
doc_type: issue
title: >-
  pipeline_e2e_check.py's local process is silently killed ~3.5-5.5min in — reproducible 2/2, during the skip-leg
  EXIT_STATUS poll, no traceback despite full stdout+stderr capture
summary: >-
  Reproduced twice (2026-08-06, cefi_mtds_smoke_tester's first-ever run, day=2026-08-05): 5 parallel `python3
  scripts/pipeline_e2e_check.py --asset-group <AG> --legs force,skip --mvp-only --require-captured --auto-day
  --wall-clock-timeout-sec 2400` invocations (CEFI/TRADFI/SPORTS/PREDICTION) each got through a real force-leg VM
  launch+poll+verify, launched the skip-leg VM, logged `launcher exited 0 ... polling for EXIT_STATUS`, then the LOCAL
  python process vanished with ZERO further output (no Python traceback, no cleanup log, no report write) — both times
  ~3.5-4.3 minutes into that specific poll (real elapsed since process start: attempt 1 ~330s watchdog-observed window;
  attempt 2 the same shape, per-process ~245-289s). DEFI (2958 MVP candidates vs. 225/5/110/4 for the others) died even
  earlier BOTH times — right after Phase-0 manifest consolidation, before its first VM launch — a distinct failure
  point, possibly related to its far larger candidate-precheck volume. Ruled out as the cause: (a) the script's own
  `--wall-clock-timeout-sec` SIGALRM backstop (set to 2400s = 40min, ~8-13x longer than the observed death); (b) every
  other `os._exit()`/timeout site in `pipeline_e2e_check.py` and the shared
  `unified_trading_library/pipeline_e2e_check/launcher.py` polling module (grepped both files — the launcher's own
  timeouts raise a catchable `subprocess.TimeoutExpired`/return a `launcher_script_timeout` reason, not a silent kill).
  Real infra impact was contained both times: every VM the dying local process had already launched went on to
  self-terminate cleanly (`EXIT_STATUS=0`, `VM_SHUTDOWN_ON_COMPLETION=true` fired) — confirmed via GCS
  `vm-logs/<vm>/EXIT_STATUS` reads and `gcloud compute instances list` showing zero leftover instances after each
  attempt — so no orphaned/billing-leaking VMs resulted, but the LOCAL report was never written either time (no
  `.md`/`.json` in `--report-dir`), meaning the checker's whole reason to exist (proving + recording the result) failed
  silently. This pattern, if it reproduces host-wide, would explain why no prior run of this smoke-test role (or any
  full-MVP-matrix `pipeline_e2e_check.py` sweep found in `plans/audit/results/`) has a total shard count anywhere close
  to a real full sweep — every historical report found was small-scope (1-20 total shards), consistent with every past
  attempt also dying partway through.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [meta]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [infra, process-killed, reproducible, pipeline-e2e-check, smoke-test, shared-host, silent-failure, observability-gap]
related:
  [
    plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
created: 2026-08-06
author: cefi_mtds_smoke_tester (agt-e76dc5, slot 6)
last_updated: 2026-08-06
source: cefi_mtds_smoke_tester
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data-pipeline
drift_direction: worsening-slowly
resolved_by:
locked_by:
depends_on: []
---

# pipeline_e2e_check.py's local process is silently killed mid-run — reproducible 2/2

## What I found

Dispatched as the first-ever run of `cefi_mtds_smoke_tester` (day=2026-08-05), Phase 1 (force+skip matrix). Launched 5
parallel per-asset-group invocations of `market-tick-data-service/scripts/pipeline_e2e_check.py`, each via `nohup ... &`
(attempt 2 also `disown`ed), stdout+stderr both redirected to a log file, `--wall-clock-timeout-sec 2400`. A
`run_in_background` watchdog polled all 5 PIDs' liveness + log-byte-growth every 30s.

**Attempt 1** (03:33:34 start): all 5 processes alive and logging normally through t=270s; by the watchdog's t=330s
check all 5 had exited. Real per-process death times (from last log timestamp): cefi 03:37:52, defi 03:38:15 (died right
after launching its first force-leg VM — later than attempt 2's defi, see below), tradfi 03:37:42, sports 03:38:26,
prediction 03:37:45 — i.e. roughly 03:37:34-03:38:26 UTC, a ~52s spread across the 5.

**Attempt 2** (03:42:54 start, after fixing an unrelated missing-`--project` issue from a since-discarded attempt 0):
same shape. cefi/tradfi/sports/prediction all got through a full force-leg (launch, poll, `EXIT_STATUS`-verify) and
launched their skip-leg VM; the LAST log line in all 4 is `launcher exited 0 for vm=... — polling for EXIT_STATUS` for
the SKIP leg specifically — then silence. Real death timestamps: cefi 03:47:12 (started 03:42:54, +258s), tradfi
03:46:59 (+245s), sports 03:47:43 (+289s), prediction 03:47:00 (+246s). defi died far earlier both times — attempt 2:
03:43:05 (+11s), right after "Phase-0 consolidation" logged, before even its first sampled-instrument lookup.

```
# last 2 lines of cefi's attempt-2 log, verbatim — this is the ENTIRE tail, nothing follows:
2026-08-06 03:46:54,553 INFO launch_vm_and_wait: launching argv=... --vm-name mtds-backfill-cefi-pipelinecheck-20260806-034654-dcc37f ... (skip leg, no --force)
2026-08-06 03:47:12,509 INFO launch_vm_and_wait: launcher exited 0 for vm=mtds-backfill-cefi-pipelinecheck-20260806-034654-dcc37f (vm_confirmed_present=True) — polling for EXIT_STATUS
<process gone — no more log lines, no traceback, `kill -0 <pid>` fails, run.log stops growing>
```

Confirmed via `kill -0 <pid>` (fails, process genuinely gone, not just quiet) and log-file byte-count (stops growing at
the exact same point). `ps -p <pid>` after the fact returns nothing.

## What I ruled out

- **Not the script's own `--wall-clock-timeout-sec` SIGALRM backstop.** Set explicitly to 2400s (40 min); every death
  happened at 245-330s (4-5.5 min), 8-13x sooner. `_setup_wall_clock_timeout`/`_wall_clock_timeout_handler`
  (`pipeline_e2e_check.py` ~line 2897) is the ONLY `os._exit()`/`SIGALRM` site in the script — grepped exhaustively.
- **Not a timeout inside the shared VM-polling library.** `unified_trading_library/pipeline_e2e_check/launcher.py` (the
  module `launch_vm_and_wait` lives in) has its own `_LAUNCHER_SCRIPT_TIMEOUT_SEC`-based timeouts, but they raise
  `subprocess.TimeoutExpired` / return a `launcher_script_timeout`/`timeout_no_exit_status` REASON STRING — a normal,
  catchable Python control-flow path that would either log a result or (if genuinely unhandled) print a traceback to the
  redirected stderr. No `os._exit()` or raw `signal` usage anywhere in that file.
- **Not an orphaned-VM cost problem.** Every VM launched by a since-killed local process went on to self-terminate
  cleanly on its own (`EXIT_STATUS=0` + `VM_SHUTDOWN_ON_COMPLETION=true` fired, confirmed via
  `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm>/EXIT_STATUS` for all 8 VMs launched across
  both attempts, and `gcloud compute instances list` showing zero leftover instances after each attempt settled).

## What I could NOT confirm (no root/kernel access in this sandboxed session)

`sudo dmesg`/`sudo journalctl -k` both refused (`"no new privileges" flag is set`) — I cannot directly confirm an
OOM-kill or an external `SIGKILL` sender. Circumstantially consistent with an external kill rather than a hang:
`free -h` immediately after showed 17Gi free / 53Gi available (not memory-starved AT THAT MOMENT, though a transient
spike earlier can't be ruled out), and the shared host's own `pkill`/`pgrep` cross-slot-kill guard
(`scripts/dev/install-pkill-guard-shell-env.sh`, documented in `agents/RULES.md` §1 as protection against a recurring
incident class: a broad `pkill -f <script-basename>` on this multi-slot shared host killing a DIFFERENT slot's live
process) was **not installed** in my session's shell (`type pkill` resolved to the raw `/usr/bin/pkill`, not a guard
function) — meaning if the guard also isn't active in whichever session issued a broad kill, my legitimately-running
`pipeline_e2e_check.py` processes (a shared script basename every slot would invoke identically) would be exactly the
kind of victim that incident class describes. This is a plausible, NOT a confirmed, explanation — flagging the
possibility rather than asserting it.

## Why this matters

`/data-pipeline-check-mtds` (and by extension every scheduled role that depends on it, currently just
`cefi_mtds_smoke_tester`, but the pattern is generic to any long-lived local Python process on this shared host) cannot
currently complete a real force+skip proof for more than ~1 cell per asset_group before dying — and the death is SILENT
(no exception, no report write, no error surfaced to whatever's watching) unless something is specifically polling the
process's liveness the way this run's watchdog did. A cron-fired, unattended run of this same command (exactly what
`install-cefi-mtds-smoke-timer.sh` sets up to fire every 2h) would look like it simply never completed — no report file,
no error in the systemd journal beyond a generic non-zero/timeout exit — with no obvious signal pointing at "something
killed the process at ~4-5min," which is a genuinely hard failure mode to diagnose from the outside. It also explains a
fact I found separately: every historical `data_pipeline_e2e_check_mtds_*.md` report in `plans/audit/results/` covers a
small, narrowly-scoped shard count (1-20) — consistent with this same silent-death pattern having capped every past
attempt too, not just mine.

## Workaround used this run

Retried Phase 1 (2 full attempts, all 5 asset-groups); accepted the 1-2 real cells/group both attempts DID complete as
this run's honest, evidence-backed scope rather than retrying indefinitely; extracted verdicts directly from the real
GCS VM logs (`vm-logs/<vm>/run.log`, `EXIT_STATUS`) for cells whose local orchestrator died before writing a report,
rather than re-launching (and re-spending) the same VMs a third time. For DEFI specifically (0/2 cells completed at full
2958-candidate scope, dying during precheck both times before any VM launch) — re-ran narrowly scoped to one concrete,
protocol-appropriate cell (`--venue UNISWAP_V2-ETHEREUM --data-types dex_pool_swaps`) to at least get one real DEFI cell
proven this run.

## Suggested follow-up (not attempted this run — needs VM-level access this sandboxed session doesn't have)

- Reproduce with `strace -f`/`py-spy dump` attached to the process, or run under `setsid` in a fully detached session
  (rules out a controlling-terminal/session-group signal propagation) to capture the actual signal number instead of
  inferring "silent death = SIGKILL-shaped."
- Check whether this host has a systemd `user@.service`/`loginctl` `KillUserProcesses`/idle-session-reaper policy that
  might tear down a user's whole cgroup slice after some minutes of... (needs root — I don't have it here). the calling
  shell/session going quiet, independent of nohup/disown (both only protect against SIGHUP, not a cgroup-wide signal
  sweep) — this session's own background watchdog (a plain `while` loop) survived the same window unaffected, which
  argues against a whole-session teardown and toward a NAME/PATTERN-targeted kill instead, but is not conclusive.
- If a cross-slot `pkill` is confirmed as the mechanism: get `install-pkill-guard-shell-env.sh` running host-wide (every
  slot's shell init, not opt-in per-session) so the guard actually protects against the failure mode it was built for.
