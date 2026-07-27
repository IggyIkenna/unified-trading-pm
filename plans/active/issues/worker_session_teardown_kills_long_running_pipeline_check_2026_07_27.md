---
doc_type: issue
title: Worker interactive-session teardown repeatedly kills long-running data-pipeline-check-* driver processes
summary: >-
  Running `/data-pipeline-check-mdps` for a single scoped shard cell, the driver process was killed mid-run four
  separate times across different backgrounding strategies (run_in_background, nohup&disown, foreground, setsid) before
  completing one full automated force+skip round-trip — despite the underlying MDPS mechanism itself being independently
  proven correct (4x) via direct GCS state checks. Blocks any long-poll data-pipeline-check-* skill from completing its
  own multi-cell matrix from an interactive session.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, market-data-processing-service, agent-orchestrator]
scope: [engineer, admin]
created: 2026-07-27
assigned_vm: NA
parent_epic: infrastructure_master
resolved_by:
locked_by:
source: [data_pipeline_check_mdps_features_2026_07_20.md todo 8]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
tags: [infra, worker-lifecycle, data-pipeline-check, flakiness]
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Worker interactive-session teardown repeatedly kills long-running data-pipeline-check-* driver processes

## What I found

Executing `/data-pipeline-check-mdps` (todo 8 of `data_pipeline_check_mdps_features_2026_07_20.md`) for a single scoped
shard cell (CEFI:BINANCE-FUTURES:trades, day=2026-07-05), the `pipeline_e2e_check.py --legs force,skip` driver process
was killed mid-run **four separate times** before completing one full automated force+skip round-trip:

1. Backgrounded via the harness's `run_in_background` — process vanished (no `ps` entry, no traceback, log file
   empty/truncated) after ~19 minutes, mid-way through the skip leg's VM poll. Harness reported `status: "stopped"` /
   "No completion record was found ... may have been stopped ... or running when the previous Claude Code process
   exited."
2. Retried as a plain `nohup ... &; disown` background job — same outcome: process disappeared silently after the force
   leg succeeded (VM `EXIT_STATUS=0`, confirmed independently via `gcloud storage cat`) but before the skip leg's VM
   reached a terminal state.
3. Retried as a **foreground** (non-backgrounded) Bash call with a 590s timeout — the harness auto-backgrounded it
   anyway; it was later reported "completed (exit code 0)" but the report it wrote showed the **force leg itself**
   marked `failed: vm_not_success:launcher_script_timeout`, even though the force VM's own `run.log` independently
   confirms `exit_code=0` and 7,615 candles derived. The local driver's own launcher-script wait evidently timed out
   waiting to confirm VM creation (a ~120s gap between "launching argv=..." and the next log line, vs. ~20s in
   successful attempts) — plausibly `gcloud` API contention from the many other concurrently-running fleet VMs
   (`cefi-aster-*`, `cefi-hyperliquid-*`, `canonical-migration-*`, `datapoint-validation-*`, `af-backfill`,
   `footystats-fwd`, ... — a dozen+ VMs were running project-wide at the time).
4. Retried via `setsid nohup ... &; disown -a` (own session, immune to the parent shell's process group) — process still
   disappeared without a trace (0-byte log file) after ~lengthy resolve/consolidation I/O, before reaching the VM-launch
   stage.

Independently, direct `gcloud storage cat .../run.log` + `gcloud storage objects describe` checks on the GCS state
(decoupled from the local driver process) confirmed the underlying MDPS mechanism itself is sound: **4 independent
real-VM force-leg runs** for the same shard cell all completed with `exit_code=0` and derived the identical 7,615
candles (`1440×1m, 288×5m, 96×15m, 24×1h, 6×4h, 1×24h`).

**5th reproduction, 2026-07-27 (slot-9), AO-managed persistent worker session (not an ad-hoc interactive session):**
after fixing the launcher-timeout retry bug (todo 3 below) + a corrupted local pyarrow venv + a missing `GCP_PROJECT_ID`
env var — none of which explain this — a 3rd relaunch of the same scoped CEFI:BINANCE-FUTURES:trades check via the
harness's `run_in_background` was reported **`status: "killed"` / "was stopped"** after only **~18 seconds** of real
work (Phase-0 manifest consolidation had already logged one completed shard-consolidation line), well before reaching
the VM-launch stage. Two immediately-prior attempts in the SAME session (using the same `run_in_background` mechanism)
instead ran to natural completion in under a minute each, failing with clean, real, unrelated Python tracebacks (the
pyarrow `ImportError`, then the `GCP_PROJECT_ID` `ValueError`) — i.e. the harness's background-task mechanism CAN and
did keep those alive long enough to surface a real error, so this is not a blanket "backgrounding never survives more
than N seconds" pattern; something specifically ended the 3rd, longer-lived attempt mid-flight. No `dmesg`/`journalctl`
access from this session (permission denied) and `free -h` showed no memory pressure (22Gi available, no swap thrashing)
at kill time, so an OOM-kill was not confirmed — but also not ruled out definitively; a kernel-level or
orchestrator-level killer this session cannot see remains the leading hypothesis. **This is now the 5th independent
reproduction, across 2 different sessions and both an ad-hoc interactive worker AND an AO-managed persistent slot
worker** — ruling out "just that one session was unusual" as an explanation.

## Why it matters

The `/data-pipeline-check-mdps` (and by the same shared-engine construction, `-mtds`/`-is`/`-features`) skills are
designed as **long-running, multi-VM-launch, multi-minute** processes (Phase-0 manifest consolidation alone measured
7s–150s depending on fleet contention; each VM launch+poll is 20s–5min). If the interactive worker session/container is
torn down on some cadence shorter than that (observed: session death within single-digit minutes to ~20 minutes across 4
attempts, no consistent pattern pointing at CPU/memory), _*no data-pipeline-check-* skill can ever complete its own
multi-cell matrix from an interactive session_* — only the isolated single-VM launcher scripts (which
complete/self-report within a couple of minutes) survive reliably. This directly blocks todo 8/9 of this plan (and any
future re-run of the other three check skills) from ever reaching a clean automated `report written` verdict for
anything beyond a trivially fast single cell.

This is a different failure class from the already-tracked async-wait / poll-discipline rules (which govern _watching_ a
task, not _whether the harness itself keeps the watched process alive_).

## Recommended decision

Two independent things worth operator attention:

1. **Root-cause the session/container teardown cadence.** Is this a deliberate per-session wall-clock or resource cap on
   interactive worker slots? If so, `data-pipeline-check-*` (and any other long-poll skill) needs either (a) a
   documented "run this on the human-planning VM / via a detached systemd-style unit, never interactively" caveat, or
   (b) a resumable/checkpointed driver (write progress to a local state file; `--resume` picks up the next
   not-yet-attempted shard rather than restarting the whole `--legs` matrix).
2. **`gcloud` VM-creation contention under fleet load** (attempt 3's `launcher_script_timeout`) is a separate,
   probably-pre-existing finding: the launcher's own wait-for-instance-confirmation timeout may need loosening, or
   VM-creation calls could benefit from the same kind of concurrency-aware backoff the Tardis-cap guard already uses for
   downloads.

Given this session could not reliably keep the driver alive long enough to produce a genuine automated skip-proof
verdict, the honest disposition for `data_pipeline_check_mdps_features_2026_07_20.md` todo 8 is: **force-leg mechanism
independently proven correct on real infra (4x)**; the skill's own automated round-trip + the other AGs remain undone,
tracked here rather than silently claimed complete.

## Todos

- [ ] [INFRA] P1. Investigate whether interactive worker sessions have a wall-clock/resource teardown cadence that is
      shorter than a realistic `/data-pipeline-check-*` full run, and document the finding (or fix the cadence) in
      `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` or a new dedicated codex doc.
- [ ] [SCRIPT] P2. Add a `--resume`/checkpoint capability to `unified_trading_library.pipeline_e2e_check`'s
      `run_pipeline_check` so a killed driver process can resume from the next not-yet-attempted shard cell instead of
      restarting the whole `--legs` matrix from scratch (repo: unified-trading-library).
- [x] ✅ [SCRIPT] P2. **SHIPPED 2026-07-27 (slot-9)**: `unified-trading-library@137e219c`. Loosened the launcher-script
      VM-creation wait in `launch_vm_and_wait`/`_run_launcher_script` (`pipeline_e2e_check/launcher.py`): a
      `subprocess.TimeoutExpired` on the launcher subprocess is now caught in `_run_launcher_script_once` and converted
      to a synthetic nonzero-exit `CompletedProcess` (sentinel `_LAUNCHER_TIMEOUT_RC = -1000`), so it flows through the
      SAME `_vm_is_present`-gated retry path a real nonzero launcher exit already used — matching this exact incident's
      own root cause (attempt 3: launcher timed out client-side waiting to confirm VM creation while
      `gcloud compute     instances create` had already succeeded server-side a few minutes later). Previously the
      timeout propagated straight out of `_run_launcher_script` to `launch_vm_and_wait`'s outer
      `except subprocess.TimeoutExpired`, which returned `reason="launcher_script_timeout"` immediately with ZERO
      retry/presence-check, even though the identical retry machinery already existed one level down for ordinary
      nonzero exits. 3 new regression tests (`tests/unit/test_pipeline_e2e_check_launcher_timeout.py`) cover: (1)
      timeout + VM confirmed present → treated as launched, no further retry; (2) timeout + VM genuinely absent →
      retries and succeeds on the next attempt; (3) end-to-end `launch_vm_and_wait` no longer returns
      `launcher_script_timeout` for a timeout the retry path recovers from. QG green (226s, full run). This does NOT
      itself complete todo 8 of the parent plan (the full all-AG matrix + skip-proof still needs a from-scratch run
      under the now-fixed retry path — likely still blocked by the separate P1 session-teardown investigation above),
      but removes one of the two concretely-identified blockers.
