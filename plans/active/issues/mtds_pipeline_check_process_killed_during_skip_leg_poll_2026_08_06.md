---
doc_type: issue
title: >-
  pipeline_e2e_check.py's local process is silently killed at a FIXED ~300-330s wall-clock mark — reproducible 3/3
  across two different code paths (force+skip AND live), no traceback despite full stdout+stderr capture
summary: >-
  Reproduced THREE times (2026-08-06, cefi_mtds_smoke_tester's first-ever run, day=2026-08-05), across TWO structurally
  different invocations: Phase 1 (`--legs force,skip`, 2 attempts) and Phase 2 (`--legs live`, 1 attempt). All three
  times, 5 parallel per-asset-group `python3 scripts/pipeline_e2e_check.py` processes were killed with ZERO output (no
  Python traceback, no cleanup log, no report file) at almost exactly the SAME wall-clock offset since process start —
  attempt 1 (force,skip): watchdog observed all 5 dead by its t=330s check. Attempt 2 (force,skip): 4/5 died at real
  elapsed 245-289s (the last log line in every case is `launcher exited 0 ... polling for EXIT_STATUS` for the SKIP leg
  specifically). **Attempt 3 (Phase 2, `--legs live` — a DIFFERENT code path with no force/skip split at all) died at
  the SAME mark**: watchdog t=300s showed 4/5 alive, t=330s showed 0/5 alive — i.e. genuinely killed somewhere in [300s,
  330s) again, this time mid-`live` leg (each process had just launched a `--max-duration-seconds 90` live smoke VM and
  was polling its `EXIT_STATUS`). Because the live leg shares almost no code with the force/skip path (different
  launcher script `launch-mtds-live.sh` vs `launch-mtds-backfill-vm.sh`, different polling call site) and still died at
  the identical ~300-330s wall-clock offset, the death is NOT tied to a specific line/workflow-position in
  `pipeline_e2e_check.py` — it is a FIXED-INTERVAL kill independent of what the process is doing. Ruled out as the
  cause: (a) the script's own `--wall-clock-timeout-sec` SIGALRM backstop (set to 2400s/1200s across the runs, 4-8x
  longer than the observed ~300-330s death — confirmed the only `os._exit()`/`SIGALRM` site in the script); (b) every
  timeout site in the shared `unified_trading_library/pipeline_e2e_check/launcher.py` polling module (raises a catchable
  `subprocess.TimeoutExpired`/returns a `launcher_script_timeout` reason string, not a silent kill — grepped, no
  `os._exit()` there either). DEFI additionally died even earlier in BOTH Phase-1 attempts (before its first VM launch,
  during precheck of its unusually large 2958-candidate MVP set) AND a 3rd narrowly-scoped Phase-1 retry (1 real cell,
  still died before even logging its shard-enumeration line) — but Phase 2's live leg (2958 candidates, same DEFI)
  completed 2 full cells cleanly before the ~330s mark hit, so DEFI's Phase-1-specific pattern looks like a distinct,
  second problem layered on top of the universal ~330s kill, not the same mechanism. Real infra impact was contained
  every time: every VM a since-killed local process had already launched went on to self-terminate cleanly
  (`EXIT_STATUS=0`, `VM_SHUTDOWN_ON_COMPLETION=true` fired, or a live smoke VM's own `--max-duration-seconds 90` bound)
  — confirmed via GCS `vm-logs/<vm>/EXIT_STATUS` reads and `gcloud compute instances list` — so no orphaned/billing-
  leaking VMs resulted, but the LOCAL report was never written any of the 3 times (no `.md`/`.json` in `--report-dir`),
  meaning the checker's whole reason to exist (proving + recording the result) failed silently every run. This pattern,
  if it reproduces host-wide, would explain why no prior run of this smoke-test role (or any full-MVP-matrix
  `pipeline_e2e_check.py` sweep found in `plans/audit/results/`) has a total shard count anywhere close to a real full
  sweep — every historical report found was small-scope (1-20 total shards), consistent with every past attempt also
  dying partway through. A ~300-330s (5-5.5min) fixed kill window is suggestive of a session/sandbox-level background-
  process lifetime cap rather than a `unified-trading-system` codebase bug — see the updated "what I could not confirm"
  section.
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

**Attempt 3** (Phase 2, `--legs live --mvp-only`, 03:53:20 start, `--wall-clock-timeout-sec 1200`): identical shape on a
STRUCTURALLY DIFFERENT code path (no force/skip split — `--mode live` launches one `launch-mtds-live.sh` VM per venue
with `--max-duration-seconds 90`). Watchdog: 5/5 alive through t=270s, 4/5 at t=300s, 0/5 at t=330s — the same [300s,
330s) window as both Phase-1 attempts, this time mid-live-leg `EXIT_STATUS` poll. DEFI notably did NOT die early this
time (unlike both Phase-1 attempts) — it completed 2 full live-leg cells (dex_pool_state, dex_pool_swaps) before the
universal ~330s cutoff hit, suggesting DEFI's Phase-1-specific early-death pattern is a SEPARATE problem from the
universal ~330s kill, not the same root cause.

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

**Revised after attempt 3**: a plain `pkill -f pipeline_e2e_check.py` sweep predicts a kill aligned to WHEN the sweep
fires (e.g. every N minutes of wall-clock), not aligned to WHEN EACH TARGET PROCESS STARTED — yet all 3 attempts died at
almost exactly the same OFFSET FROM THEIR OWN START (~300-330s), across attempts that started at 03:33, 03:42, and 03:53
(i.e. NOT aligned to a shared wall-clock cadence like `:00`/`:05`/`:30`). An age-based reaper (kill any process matching
a pattern once it's been alive >~5min) fits the evidence better than a fixed-schedule sweep, and an age-based policy is
more consistent with a session/sandbox-level background-process lifetime cap than a human/another-agent's cron-style
cleanup. I cannot distinguish "age-based pattern-match reaper elsewhere on the host" from "this Claude Code execution
sandbox's own detached-child-process lifetime limit" without kernel-level access — flagging both as live possibilities
for whoever picks this up with more access than this session has.

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

## Suggested follow-up

- [ ] [INFRA] P1. Diagnose the ~300-330s silent kill of long-lived local `pipeline_e2e_check.py` processes on the shared
      host: reproduce under `strace -f` / `py-spy dump` / `setsid` detached session to capture the actual signal and
      sender (needs VM-level access this sandboxed session lacks) (repos: market-tick-data-service,
      unified-trading-library).
- [ ] [INFRA] P1. Check host-level session/cgroup reaper policies consistent with an age-based kill
      (`systemd user@.service`, `loginctl KillUserProcesses`, idle-session-reaper, or a sandbox detached-child lifetime
      cap) and distinguish from a name/pattern-matched `pkill` sweep (needs root).
- [ ] [INFRA] P2. Install `scripts/dev/install-pkill-guard-shell-env.sh` host-wide (every slot's shell init, not opt-in
      per-session) so the cross-slot pkill guard protects against the failure mode it was built for.
