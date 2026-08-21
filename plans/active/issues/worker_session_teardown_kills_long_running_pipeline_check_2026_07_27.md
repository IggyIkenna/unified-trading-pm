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
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-library, market-data-processing-service, agent-orchestrator]
scope: [engineer, admin]
created: 2026-07-27
author: unknown
assigned_vm: NA
parent_epic: security_and_cross_cutting_master
resolved_by:
locked_by:
source: [data_pipeline_check_mdps_features_2026_07_20.md todo 8]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
tags: [infra, worker-lifecycle, data-pipeline-check, flakiness]
priority: P1
execution_scope:
  local-only # corrected 2026-08-02 (operator ruling on
  # plan_reconcile_parked_operator_decisions_2026_08_02.md na-eligibility-audit item 20, option A): was
  # orchestrator-agent, contradicting assigned_vm: NA. Stays NA until the shared-host RAM exhaustion mechanism
  # (condition mdps-e2e-shared-host-teardown-fixed) is also closed, not just the partial root-cause on todo 1.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/,
  ]
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
AT THAT MOMENT — but the operator independently identified the likely actual cause the same day:
`issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` documents fleet-wide shared-host RAM contention
silently killing background processes anywhere from 32s to 520s in (NOT tied to elapsed time — matching this session's
~18s kill far better than a fixed-threshold theory would), with no visible exit code/stderr/dmesg entry either,
correlated with 5-8 concurrent `quality-gates.sh`/VM-launch processes fleet-wide at kill time (this session's own
`free -h` snapshot — taken only once, not sampled repeatedly across the run like that doc's — is consistent with but
does not itself prove this, since RAM pressure can spike and recede within seconds). **This is now the 5th independent
reproduction, across 2 different sessions and both an ad-hoc interactive worker AND an AO-managed persistent slot
worker** — ruling out "just that one session was unusual" as an explanation, and now tracked jointly under condition
`mdps-e2e-shared-host-teardown-fixed` (gates `data_pipeline_check_mdps_features_2026_07_20.md`'s new post-split
follow-up todo) alongside slot-7's identical hit. **Two distinct, both-real mechanisms are now implicated**: (1) the
`WorkerLivenessWatchdog` heartbeat-silent kill (900s, confirmed root cause of the original ~19-minute reproduction — see
todo 1 below) and (2) shared-host RAM exhaustion (a much better fit for the fast, sub-minute kills including this
session's ~18s one). Do not assume either alone is the WHOLE story — a from-scratch fix attempt should account for both.

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

**2026-07-27 (slot-3) — the heartbeat-cadence mitigation WORKS, confirmed on a real run.** Running todo 9
(`/data-pipeline-check-features`, CEFI:delta_one, day auto-resolved to 2026-07-19..2026-07-20), the driver was
backgrounded via `run_in_background` and a companion `Monitor` loop sent an `/api/slots/<N>/progress` heartbeat every
240s (well under the 900s watchdog threshold) while tailing the log. The driver ran ~9 minutes end-to-end (2 VM
launch+poll cycles) and completed naturally, writing a real report — **zero session-teardown kills**, the first clean
automated round-trip since this issue was opened. Confirms the procedural fix in the first todo below actually closes
the gap for a run in this duration range; the still-open `--resume`/checkpoint todo remains the harder fix for
multi-hour full-matrix runs.

Given this session could not reliably keep the driver alive long enough to produce a genuine automated skip-proof
verdict, the honest disposition for `data_pipeline_check_mdps_features_2026_07_20.md` todo 8 is: **force-leg mechanism
independently proven correct on real infra (4x)**; the skill's own automated round-trip + the other AGs remain undone,
tracked here rather than silently claimed complete.

## Todos

- [x] ✅ [INFRA] P1. **ANSWERED 2026-07-27 (slot-9), partial.** Root-caused the ~19-minute reproduction (attempt 1) via
      direct code read of `agent-orchestrator`: `WorkerLivenessWatchdog` (`server/worker_liveness_watchdog.py`) kills a
      slot's ENTIRE tmux session after `watchdog_heartbeat_timeout` (default 900s/15min, config.py:354) of no
      `/progress`/`/done` — and `kill_session` (`server/tmux_spawn.py:_reap_pane_tree`, lines 245-293) ALSO reaps the
      pane's whole descendant process tree (SIGTERM then SIGKILL) BEFORE the tmux kill, specifically so a
      `nohup`/`disown`/`setsid`-detached background job (or the harness's own `run_in_background` Bash) doesn't survive
      as an orphan. This exactly matches attempt 1: a long, synchronous, single blocking Bash call with no intervening
      `/progress` for ~19 minutes would cross the 900s heartbeat-silent threshold, and the resulting kill reaps the
      backgrounded driver too — even though it was correctly progressing and would have re-invoked on its own
      completion. **This was a genuine STALE-codex gap**:
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md`'s "Kill execution" section documented
      `kill_session` calling only `tmux kill-session`, with no mention of the pane-tree reap added 2026-07-10 —
      corrected in the same commit as this todo. **Actionable fix (procedural, no code change needed)**: a worker
      driving a `/data-pipeline-check-*` skill (or any multi-minute wait) MUST keep sending explicit `/progress`
      heartbeats at the existing ~10min HARD RULE cadence EVEN WHILE "just waiting" on a `run_in_background` task or a
      `ScheduleWakeup` — `ScheduleWakeup` has NO server-side heartbeat effect (confirmed: no implementation in
      agent-orchestrator, client-side `/loop` concept only per
      `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`'s existing "Wake sources" section), so relying on it
      alone during a long wait silently lets the AO-side heartbeat clock run out. **NOT fully explained**: this
      session's OWN 5th reproduction (see "What I found" above) was killed after only ~18s — far too fast for the 900s
      heartbeat-silent path, and this session HAD sent an HTTP ping (a rejected `/done` call) shortly before. That
      faster kill remains genuinely unexplained (no OS-level log access from this session to confirm/rule out an
      OOM-kill or a different, undiscovered reaper) — flagged as residual, not swept under this answered todo.
- [ ] [SCRIPT] P2. Add a `--resume`/checkpoint capability to `unified_trading_library.pipeline_e2e_check`'s
      `run_pipeline_check` so a killed driver process can resume from the next not-yet-attempted shard cell instead of
      restarting the whole `--legs` matrix from scratch (repo: unified-trading-library).
- [x] ✅ [SCRIPT] P2. **SHIPPED 2026-07-27 (slot-9)**: `unified-trading-library@7aad5833` (repointed 2026-08-06 —
      original sha orphaned by the 2026-08-05 history rewrite; content verified identical). Loosened the launcher-script
      VM-creation wait in `launch_vm_and_wait`/`_run_launcher_script` (`pipeline_e2e_check/launcher.py`): a
      `subprocess.TimeoutExpired` on the launcher subprocess is now caught in `_run_launcher_script_once` and converted
      to a synthetic nonzero-exit `CompletedProcess` (sentinel `_LAUNCHER_TIMEOUT_RC = -1000`), so it flows through the
      SAME `_vm_is_present`-gated retry path a real nonzero launcher exit already used — matching this exact incident's
      own root cause (attempt 3: launcher timed out client-side waiting to confirm VM creation while
      `gcloud compute instances create` had already succeeded server-side a few minutes later). Previously the timeout
      propagated straight out of `_run_launcher_script` to `launch_vm_and_wait`'s outer
      `except subprocess.TimeoutExpired`, which returned `reason="launcher_script_timeout"` immediately with ZERO
      retry/presence-check, even though the identical retry machinery already existed one level down for ordinary
      nonzero exits. 3 new regression tests (`tests/unit/test_pipeline_e2e_check_launcher_timeout.py`) cover: (1)
      timeout + VM confirmed present → treated as launched, no further retry; (2) timeout + VM genuinely absent →
      retries and succeeds on the next attempt; (3) end-to-end `launch_vm_and_wait` no longer returns
      `launcher_script_timeout` for a timeout the retry path recovers from. QG green (226s, full run). This does NOT
      itself complete todo 8 of the parent plan (the full all-AG matrix + skip-proof still needs a from-scratch run
      under the now-fixed retry path — likely still blocked by the separate P1 session-teardown investigation above),
      but removes one of the two concretely-identified blockers.
- [x] ✅ [SCRIPT] P1. **NEW 2026-07-27 (slot-10)**: each session-teardown kill (this issue's whole premise) makes the
      NEXT session re-launch the same cell from scratch rather than resuming — and with no in-flight check first, this
      produces genuine concurrent-duplicate VM billing waste, observed live:
      `gcloud compute instances list --filter="name~'features-e2e-cefi'"` (2026-07-27 11:15 UTC) showed **5
      simultaneously-RUNNING** delta_one:CEFI VMs from repeated prior-session relaunches — two exact-duplicate pairs
      computing the IDENTICAL shard (`features-e2e-cefi-20260727-063401` + `-083854`, both `--force` on window
      2026-07-19..2026-07-20; `-101851` + `-102228`, both `--force` on window 2026-06-28..2026-06-29), all still
      mid-flight ~1-4.7h after launch (confirmed via `run.log` tails showing live, advancing timestamps — not
      stuck/zombie, genuinely still computing, so NONE were killed per the VM-delete guardrail). Separately, this
      session nearly added a **6th** duplicate: launched `--family volatility --asset-group CEFI` before checking for an
      in-flight LOCAL process, and only a `ps aux` immediately after the launch caught that slot-3 was already running
      the identical `--family volatility` (all-AG, includes CEFI) driver since 10:44 UTC — killed the 5-second-old
      duplicate before it reached VM-launch, zero cost, but the near-miss shows the gap is real and easy to hit even
      when actively watching for it. **Recommended fix** (repo: unified-trading-library, `pipeline_e2e_check` driver
      entry point): before launching any cell, check BOTH (a)
      `gcloud compute instances list --filter="name~'features-e2e-<ag>'"` for an existing VM whose
      `VM_FEATURE_FAMILY`/`VM_ASSET_GROUP`/date-range metadata matches the cell about to be launched, and (b) a local
      `ps aux | grep pipeline_e2e_check` for an already-running driver targeting the same `(family, asset_group)` —
      skip/attach rather than relaunch on either hit. This is a distinct, cheaper fix from the `--resume`/checkpoint
      todo above (that one resumes a KILLED run's remaining cells; this one prevents re-launching a cell that's already
      alive and progressing, killed or not).

      **SHIPPED 2026-07-27 (slot-6)**: `features-service@6981b2b8`. Re-checked live fleet state on pickup of todo 9b —
          the waste had gotten WORSE since this todo was filed: **7** simultaneously-RUNNING `features-e2e-cefi-*` VMs (up
          from 5) + 2 `features-e2e-tradfi-*` VMs, confirmed via fresh `run.log` tails all live-advancing (none
          stalled/zombie). Root-caused one of the two NEW VMs launched after the 11:15 UTC check
          (`features-e2e-cefi-20260727-112159-025349`, window 2026-06-28..2026-06-29): it is slot-7's OWN legitimate
          full-matrix driver (`pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day`, no
          `--family`/`--asset-group` restriction, enumerating all 16 shards for todo 9b) — its `run.log` shows it launched
          that exact VM at 11:21:59 UTC for shard 1/16 (`CEFI:delta_one`), auto-day-resolved to the SAME window
          2026-06-28..2026-06-29 that `-101851`/`-102228` were ALREADY running. **This is live proof of the bug**: even a
          legitimate, freshly-dispatched full-matrix run has no in-flight check and silently launched a 3rd duplicate for a
          window two other VMs were already computing. Implemented the recommended metadata-based check in
          `features-service/scripts/pipeline_e2e_check.py` (`_find_inflight_duplicate_vm`): before either the force or skip
          leg launches a VM, query `aggregated_list_instances` (via UTL's `get_compute_engine_client`, no raw
          `gcloud`/subprocess) with `filter_str='status = "RUNNING" AND labels.purpose = "features-backfill" AND
          labels.family = "<dashed>" AND labels.category = "<ag-lower>"'` — every launch already stamps these labels
          (`launch-features-vm.sh`), so this needed no launcher changes. A hit returns `status="skipped"` with reason
          `duplicate_in_flight: <vm> ...` and launches nothing; a transport error fails OPEN (returns `None`, launch
          proceeds) so a Compute API blip can never block a real run. Deliberately coarser than day-window (family+AG
          only) — the observed waste was always same-cell/different-window duplication, and a same-cell VM already running
          will itself produce this cell's result, so the coarser check never loses coverage. QG green (`features-service`),
          shipped via quickmerge. **NOT done**: the identical launcher-side gap exists in
          market-data-processing-service's own `pipeline_e2e_check.py` driver (same launch pattern, not yet checked for
          this guard) — follow-up todo below. Did NOT touch slot-7's already-running VMs (all genuinely progressing per
          the VM-delete guardrail) and launched zero new VMs this session.

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-27 (slot-2)** — `market-data-processing-service@063cea2` +
      `deployment-service@c8ee47e`. Confirmed vulnerable: `pipeline_e2e_check.py`'s force/skip legs had no
      duplicate-in-flight guard at all. Also confirmed the launcher's labels were INSUFFICIENT for a features-style
      guard — `launch-mdps-backfill-vm.sh` stamped only `labels.category`, but MDPS's shard granularity is finer (one VM
      per `(asset_group, venue, data_type)`, not per `(family, asset_group)`), so a category-only match would wrongly
      treat two different concurrent shards under the same asset_group as duplicates. Shipped both halves: (1) ported
      `_find_inflight_duplicate_vm(project_id, shard)` keyed on `(asset_group, venue, data_type)` into both
      `_run_force_leg`/`_run_skip_leg`, 6 new regression tests, QG green (118s); (2) extended the launcher's `--labels=`
      to also stamp `venue=`/`data_type=` when the caller passes a single (non-multi-value) value — the driver's actual
      per-shard call pattern — 5 new regression tests extract + evaluate the real snippet in isolation (no `gcloud` call
      ever invoked). Full detail: `plans/active/data_pipeline_check_mdps_features_2026_07_20.md` todo 9b's 2026-07-27
      (slot-2) Progress Log entry.

- [x] ✅ [SCRIPT] P2. **NEW 2026-07-27 (slot-6)**: port the identical `_find_inflight_duplicate_vm` duplicate-in-flight
      guard (labels.purpose/family/category filter via `aggregated_list_instances`) into
      `market-data-processing-service/scripts/pipeline_e2e_check.py`'s force/skip leg VM launch — its
      `launch-mdps-vm.sh`-equivalent launcher likely stamps analogous labels already (verify), and the driver has the
      same unchecked-relaunch shape that caused this whole finding for features. Not yet checked/confirmed vulnerable,
      just not yet protected either — do the same live-fleet check first before assuming it needs the fix.
      **STALE-CLOSED 2026-07-30 (na-eligibility-audit, infra tranche, dispatch agt-30721a)** — already shipped by the
      sibling `[x] DONE 2026-07-27 (slot-2)` checkbox immediately above in this same doc:
      `market-data-processing-service@063cea2` + `deployment-service@c8ee47e` ported `_find_inflight_duplicate_vm(...)`
      keyed on `(asset_group, venue, data_type)` into both `_run_force_leg`/`_run_skip_leg` — this todo's own ask was
      completed by that commit before this checkbox was ever closed.
- [x] [REVIEW] P1. **DONE-VIA-SUCCESSOR 2026-07-28** — this todo's own ask (run `/vm-preemption-billing-waste-audit`
      against the fleet and get a stop-vs-let-run decision) was carried out by the very next `[OPERATOR]` P0 todo below
      (the audit ran 2026-07-27 ~17:03 UTC). See that todo for the applied 2026-07-28 ruling. Closing this one rather
      than duplicating the decision here — original body retained below for the historical record.

      **NEW 2026-07-27 (slot-3)**: the `_find_inflight_duplicate_vm` fix (`features-service@6981b2b8`) is
          confirmed WORKING on new launches — my own todo-9b day=2026-07-19 run shows it firing twice live
          (`TRADFI:cross_instrument skip` and `TRADFI:multi_timeframe skip`, both `duplicate_in_flight: <vm> ...` skips,
          zero new VMs launched for those cells). But the fix only stops NEW duplicates — it does nothing for the PRE-FIX
          fleet already running. Fresh `gcloud compute instances list --filter="name~'features-e2e'"` at todo-9b handoff
          time (2026-07-27, ~13:00 UTC) shows **9 VMs still simultaneously RUNNING**, spanning slot-3/6/7/10's overlapping
          sessions: 8 `features-e2e-cefi-*` (creation timestamps 2026-07-26T23:34 PDT through 2026-07-27T05:02 PDT — the
          oldest is **~9 hours old**) + 1 `features-e2e-tradfi-*` (05:49 PDT). At least 3 of these are confirmed exact-
          duplicate pairs/triples on the SAME shard+window from this issue's own earlier findings above
          (`-063401`/`-083854`; `-101851`/`-102228`; `-112159`). None have been stopped — per the VM-delete guardrail (only
          kill a VM confirmed genuinely dead, never one still progressing) none of the sessions that found them chose to
          delete them, so they have been silently accumulating real `e2-standard-8` on-demand spend (**--day.268/hr each**
          per the `/data-pipeline-check-features` skill's own cost table) for hours, un-actioned, because no session's scope
          included "go clean up the fleet." **Recommended**: run `/vm-preemption-billing-waste-audit` (already a standing
          codex HARD RULE — "every agent watching VMs should use it, not just when an incident is already suspected")
          against this exact VM set to (a) confirm which are genuinely still progressing vs. silently stalled (this session
          independently confirmed the original `-101851` VM went from healthy-progressing to byte-identical-stalled at ~2.5h
          runtime — see the parent plan's Progress Log), and (b) get an operator decision on stopping the
          confirmed-redundant/stalled ones rather than leaving a 9-VM, multi-hour fleet running unobserved. Not actioned in
          this session — flagging for the next session/operator rather than unilaterally deleting VMs outside this task's
          scope.

          **CORRECTION 2026-07-27 (slot-3, later same session)**: the `-101851` "byte-identical-stalled at ~2.5h" claim
          above was WRONG — a stale-read artifact, not a real stall. Continued monitoring after this entry was written
          showed the SAME VM's `run.log` line count climbing steadily and repeatedly (159,987 → 356,664 → ... → 480,409+
          across dozens of properly-spaced checks spanning several more hours, still RUNNING and still advancing as of
          this correction), with no further flat reads. It never stopped computing; the earlier single flat-then-stalled
          read was misdiagnosed as a genuine stall instead of a transient upload-cadence gap. Root cause of why it runs
          this slowly (not why it "stalled" — it didn't) is separately, correctly diagnosed by another slot:
          `issues/features_delta_one_sequential_per_day_gcs_scan_2026_07_27.md` (a sequential per-instrument-day GCS
          existence-probe loop). **Lesson**: a single flat line-count read is not enough to call a stall on a VM this
          size — the ~2.5h read that looked stalled needed a longer confirming re-check before being written up as fact,
          not just the one comparison point available at the time.

- [x] [INFRA] P0. **`/vm-preemption-billing-waste-audit` RUN 2026-07-27 (slot-3), ~17:03 UTC — 8 confirmed-duplicate
      CEFI:delta_one VMs, ALL still genuinely alive, now 18+ hours old, still unaddressed.** Executing the P1 todo's own
      recommendation above. Findings: - **Step 1 (preemption scan)**: no match — these 8 VM names never appear in
      `compute.instances.preempted` (2 OLDER, differently-named VMs did preempt the prior night and were auto-relaunched
      per the working PROGRESS-checkpoint contract; that mechanism is fine and not this finding's subject). - **Step 2
      equivalent (duplicate-launch billing waste, this shard's actual failure mode)**: re-verified via
      `gcloud compute instances describe --format="value(labels)"` on all 8 — every single one carries
      `category=cefi;family=delta-one;purpose=features-backfill`. Re-checked all 8 `run.log` line counts + last-line
      timestamps just now: **ALL EIGHT are genuinely alive and actively advancing** (line counts 215,948–748,818; every
      last-line timestamp within the same ~17:02-17:03 UTC minute as the check) — none stalled, none safe to reap under
      the VM-delete guardrail. Oldest (`-063401`) was created 2026-07-26T23:34 PDT — **~18 hours ago**. This is the SAME
      duplicate set this issue doc already named (`-063401`/`-083854`; `-101851`/`-102228`; `-112159`) plus 2 more
      (`-114259`, `-120200`) that joined since — still running, still un-actioned, ~9 hours after the P1 todo above
      first flagged it and explicitly recommended this exact audit. - **Step 3 (alerting check)**: no
      `attempted_failed`/preemption signal would have caught this — a healthy, successfully-progressing,
      merely-REDUNDANT VM produces no error signal at all. This class of waste is invisible to every existing alert;
      only a manual fleet-label sweep (as done here) surfaces it. Filing that gap is this todo's own scope, not a
      separate finding. - **Cost, conservative estimate**: 8 × `e2-standard-8` (**--day.268/hr on-demand** per the
      skill's own cost table; provisioning model not re-verified this pass) × ~13h average age ≈
      **~$28 burned so far, growing at
        ~$2.14/hr while all 8 remain up** — genuinely small in absolute terms, but
      100% attributable to unresolved duplication, not real backfill progress the fleet needed. - **Why [OPERATOR] not
      [SCRIPT]**: per the VM-delete guardrail, a worker cannot decide alone whether to stop a genuinely-healthy,
      genuinely-progressing VM just because a sibling VM is doing overlapping work — that judgment call (accept the
      redundant spend vs. stop N-1 of the 8 and keep only the furthest-along) belongs to the operator, not to whichever
      session next reads this doc. **Recommended options**: (a) let all 8 run to their own natural completion (small,
      bounded, self-terminating spend, no further action needed), or (b) stop the 7 LEAST-progressed VMs now (keep only
      `-063401`, the furthest along at 748,818 lines) to cut ongoing spend by ~7/8 — a human call, not an automated one.

      **RULED 2026-07-28 — Option (a): let all remaining VMs run to natural completion, no kill action.** No specific
          operator answer was given; applying the standing workspace theme instead: total exposure is ~$28 spent +
          ~$2/hr while the remainder run, far under the pre-approved $100-is-not-a-blocker threshold, so cost alone does not
          justify intervening; and killing a still-progressing VM to save that small amount would destroy real, non-resumable
          partial progress on that shard's backfill — exactly the kind of partial-completion the theme rules against. The
          passive check-ins below (same session, after this todo was written) already show this playing out organically:
          2 of the original set (`-063401`, `-083854`) self-completed and self-deleted with zero operator/worker action,
          supporting option (a) as the actual outcome, not just the theoretical ruling. Retag `[SCRIPT]`/`[INFRA]` monitoring
          only (no kill): whichever session next touches this doc should confirm the remaining VMs (`-101851`/`-102228`/
          `-112159`/`-114259`/`-120200` as of the last check-in) have since self-completed, and close this todo once none
          remain — do not proactively stop any of them.

- 2026-07-27 (slot-3, later same-session passive check-in): **`-063401` (the furthest-along VM, 748,818 lines at last
  check) is now COMPLETELY GONE from the project** —
  `gcloud compute instances describe features-e2e-cefi-20260727-063401-025349 --zone=asia-northeast1-c` returns
  "resource ... was not found", and a broader `name~'063401'` filter across the whole project returns zero matches.
  Consistent with a successful self-delete on completion (`VM_SHUTDOWN_ON_COMPLETION=true`), not independently confirmed
  via its run.log (already deleted) — no crash/error signal seen, and option (a) from the recommendation above ("let all
  8 run to natural completion") appears to be happening organically without operator action. **Duplicate set is down to
  6** (`-083854`/`-101851`/`-102228`/`-112159`/`-114259`/`-120200`, all confirmed RUNNING via
  `gcloud compute instances list --filter="name~'features-e2e-cefi-2026072'"`). Still no operator response on
  `resolved_by:` — leaving this open, just recording the organic progress rather than treating it as resolved.

- 2026-07-27 (slot-3, further passive check-in): **`-083854` is now ALSO completely gone**
  (`gcloud compute instances describe ... --zone=asia-northeast1-c` → resource not found). Same pattern as `-063401` —
  consistent with organic completion, not independently confirmed via run.log (already deleted). **Duplicate set now
  down to 5**: `-101851`/`-102228`/`-112159`/`-114259`/`-120200`, all still confirmed RUNNING. 2 of the original 8 have
  now self-resolved without any operator action, supporting option (a) ("let all 8 run to natural completion") as the
  path actually playing out. Still no `resolved_by:` — leaving open.

## Progress Log

- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`, no operator present): **RECLASSIFY candidate — PARKED,
  `BLOCKED-OPERATOR-DECISION`.** This is the one doc in the whole `ao` tranche whose remaining work passes the
  bounded/deterministic-outcome bar on its own text, so it was taken through the full Phase-2 conflict-check rather than
  kept NA by default. What the check found:
  - **Conflict surfaces are CLEAR.** The sole open todo (`[SCRIPT] P2`, add `--resume`/checkpoint to
    `unified_trading_library.pipeline_e2e_check.run_pipeline_check`) is named in
    `/plans/active/data_pipeline_check_mdps_features_2026_07_20.md` (`status: active`, `assigned_vm: planning`, same
    `parent_epic: infrastructure_master`) — but only as row 2 of its `## Deferred work after 2026-07-27` table, whose
    "Where tracked" column points back here ("same issue doc"). That is a digest pointer, not a dispatch claim, and that
    plan carries **no open checkbox** claiming the resume work. Zero/milestone-only overlap → clear.
  - **But the same table's Gating column says `depends on #1's root cause`, and #1 is only PARTIALLY answered.** Todo 1
    here is `- [x]` but self-labels "**ANSWERED 2026-07-27 (slot-9), partial**", and this doc's own 5th-reproduction
    note names **two** distinct live mechanisms (`WorkerLivenessWatchdog` heartbeat-silent kill AND shared-host RAM
    exhaustion) with an explicit warning: "Do not assume either alone is the WHOLE story."
  - **Why that blocks an autonomous flip.** There is no per-todo prereq syntax in this corpus (prereqs come only from
    plan-level `sequential` / `depends_on`+`gate_on_depends`), so flipping `assigned_vm` here would let backlog-regen
    derive this todo directly with **nothing holding the declared prerequisite** — the exact mis-dispatch shape
    `/plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` documents 13+ times, and the
    shape `/cursor-configs/skills/na-eligibility-audit/SKILL.md` Phase 1 warns about after the
    `regen_positional_task_ids_not_content_stable_2026_07_17.md` revert.
  - Noted alongside: this doc's frontmatter is internally inconsistent — `assigned_vm: NA` with
    `execution_scope: orchestrator-agent` — and it carries no `assigned_role`/`estimate_class`. Whichever option below
    is chosen should settle that too.

  **Operator decision needed:**

  ```
  Does the PARTIAL root-cause answer on todo 1 satisfy the "depends on #1's root cause" gate that
  data_pipeline_check_mdps_features_2026_07_20.md declares over the --resume/checkpoint todo?

  A: NO — keep assigned_vm: NA until the second mechanism (shared-host RAM exhaustion, condition
     `mdps-e2e-shared-host-teardown-fixed`) is also closed; fix execution_scope to local-only so the
     frontmatter stops contradicting itself. [WORKER REC — the prerequisite is declared in the corpus and
     is demonstrably not met; no machine gate would hold it if flipped]
  B: YES — the resume/checkpoint work is independently useful regardless of which mechanism kills the
     driver; flip assigned_vm: NA -> planning now, add assigned_role, and let it dispatch.
  C: SPLIT — move the --resume todo into data_pipeline_check_mdps_features_2026_07_20.md as a real gated
     todo (so plan-level sequencing actually holds it), and archive this doc's dispatch role.
  Other: operator can type a custom answer
  ```

  **RULED 2026-08-02 (option A)**: `assigned_vm` stays `NA`; `execution_scope` corrected to `local-only` above.

- **na-eligibility-audit 2026-07-30** (infra tranche, dispatch agt-30721a): KEEP-NA-STALE — closed the 1 stale checkbox
  already shipped by a sibling DONE entry in this same doc (see the checkbox's own STALE-CLOSED note above,
  `market-data-processing-service@063cea2` + `deployment-service@c8ee47e`). Doc stays NA overall — the remaining open
  item (`--resume`/checkpoint capability for `pipeline_e2e_check`) is genuinely still open and unshipped (confirmed via
  `data_pipeline_check_mdps_features_2026_07_20.md:638`, which cites this doc rather than duplicating the work).
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **2026-08-01 (slot-3, data_engineering, 6th reproduction — new candidate mechanism, ruling out the 900s-silence theory
  for this instance)**: running `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s prediction manifest
  `rebuild_prediction_manifest.py --chunk-days 60` apply as a `run_in_background` Bash call (not a
  `/data-pipeline-check-*` skill, but the identical shape: a single long-running, multi-hour, chunked driver process).
  Sent `/api/slots/3/progress` heartbeats to the AO server roughly every ~60-90s throughout via a separate watchdog loop
  — well inside the 900s `WorkerLivenessWatchdog` heartbeat-silent threshold this issue's first todo root-caused, so
  that mechanism does not explain this kill. Both the apply job's `run_in_background` Bash call AND its own
  heartbeat-watchdog `run_in_background` Bash call were reported `status: "killed"`/"was stopped" **simultaneously**, on
  the SAME turn that a previously-issued `ScheduleWakeup` fired and re-invoked this session. 18 of the job's planned
  chunks had already completed cleanly (no crash, no traceback, no OOM signal — `free -h` at the time showed 35GB+
  available, `dmesg`/`uptime` showed no recent reboot) before the kill; recovery (resuming the remaining date range)
  succeeded cleanly using the `Monitor` tool instead of `ScheduleWakeup` for all subsequent waits, with zero further
  kills for the rest of a multi-hour run. **New candidate mechanism worth root-causing**: does a
  `ScheduleWakeup`-triggered re-invocation tear down the prior turn's `run_in_background`-tracked child processes as
  part of resuming a fresh turn context, independent of the heartbeat-silence watchdog? This session did not have
  harness-internals access to confirm the mechanism directly — flagging the correlation (2 independent
  `run_in_background` processes, both killed on the exact turn a `ScheduleWakeup` fired, both otherwise healthy) as a
  lead for whoever root-causes the residual "not fully explained" gap this issue's first todo already flagged. Full
  narrative: `/plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s 2026-08-01 (`#8`) Progress
  Log entry.
- **2026-08-02 (slot 11, backend_engineer) — 7th+ reproduction, a NEW correlated observation: extreme host load +
  orphaned zombie QG processes from other dead sessions.** While running `bash scripts/quality-gates.sh` (a
  `run_in_background` Bash call, not `/data-pipeline-check-*`) for `agent-orchestrator` on
  `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`'s general-fix todo, the session died mid-run 6
  separate times across ~70 minutes, each time losing the in-flight `quality-gates.sh`/`pytest` process (confirmed via
  `ps aux` — the specific PID was gone post-resume, not merely orphaned). `uptime` at each resume showed climbing load
  averages: 30.83 → 32.43 → 39.64 → 40.59/44.27 → 42.86 → 54.77/62.23 (16-core box), swap actively in use. **New data
  point**: `ps aux` at one resume showed 14+ OTHER slots' `bash scripts/quality-gates.sh`/`python -m pytest` processes
  still running from timestamps spanning `12:06`–`13:26` that same session (i.e., already 20-100+ min old at observation
  time) — plausibly orphaned survivors of OTHER slots' own session deaths, compounding the load spike this doc's
  mechanism keeps hitting. Did not kill any of them (not this slot's PIDs, no name-based pattern per RULES.md §1, and no
  certainty they're dead-not-just-slow given the "D" uninterruptible-sleep state several showed). Each individual
  `quality-gates.sh` run's own diagnostic output (ruff/basedpyright/pytest dot-progress) never once showed an actual
  TEST failure across all 6 attempts — only ever an external kill, consistent with prior entries' "otherwise healthy,
  externally terminated" pattern. Flagging the fleet-wide zombie-QG-process angle as a possible contributing (or at
  least corroborating-symptom) mechanism alongside the `ScheduleWakeup`-teardown lead above — a host running many dead
  sessions' orphaned heavy processes would independently explain both the climbing load AND a higher day-over-day rate
  of fresh session deaths, without needing a single root cause. Recovery: `git status` confirmed the local uncommitted
  code diff survived every session death untouched (no orphan-wip auto-commit fired this time, unlike two earlier fires
  this same session on an unrelated task — see `unified_trading_system_ui_smoke_suite_workers_unpinned_2026_08_01.md`'s
  archived Progress Log for that recovery), so no data was lost — just repeated wall-clock cost re-attempting the gate.
- **2026-08-02 (slot 14, data_engineering) — 9th+ reproduction, TWO independent kills in one session, new disambiguating
  data point against the `ScheduleWakeup`-specific hypothesis.** Running the same
  `mtds_available_at_cross_asset_backfill_2026_07_13.md` prediction-manifest `rebuild_prediction_manifest.py` apply
  (same shape as entry #6 above) as a `run_in_background` Bash call, killed TWICE across one long session: (1)
  mid-chunk-18 of the original full-range launch, right around a `/pre-compact` + manual `/compact` cycle — confirmed
  via `ps -p <pid>` empty, last log line seconds before the process vanished, no traceback/OOM signal; 17 of 18 planned
  chunks had already completed cleanly. Documented + corrected a stale "still running independently" claim in the plan
  doc's own handoff note as a direct consequence (`unified-trading-pm@7616e6592`). (2) After resuming from that
  checkpoint, killed a SECOND time mid-chunk-4 of the relaunch, at a plain session-continuation boundary (the harness's
  own re-invocation after a context reset) — **critically, with NO `ScheduleWakeup` pending or recently-fired at the
  time of this second kill** (monitoring had switched to manual turn-by-turn checks with no queued wakeup at that exact
  moment). This is new evidence against entry #6's "does a `ScheduleWakeup`-triggered re-invocation specifically tear
  down the prior turn's `run_in_background` children" hypothesis being the WHOLE mechanism — a plain
  session/context-boundary re-invocation with no `ScheduleWakeup` involved reproduced the identical symptom (healthy
  process, 0 errors, vanishes exactly at the turn boundary). Broadens the suspected trigger from "`ScheduleWakeup`
  firing" to "any session-lifecycle/ context-boundary re-invocation the harness performs, `ScheduleWakeup`-triggered or
  not." Both kills recovered cleanly (relaunch scoped to the last confirmed-durable checkpoint, per this doc's own
  established recovery pattern) — no data lost, just wall-clock cost re-scanning a small already-clean range each time.
  Full narrative: `/plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s Progress Log (search
  "confirmed killed" and "session-end handoff... CORRECTED").

- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. Sole open item is directly covered by
  an explicit, dated 2026-08-02 operator RULING (option A) in this doc's own Progress Log, which keeps `assigned_vm: NA`
  pending closure of the shared-host-RAM-exhaustion mechanism (condition `mdps-e2e-shared-host-teardown-fixed`). That
  prerequisite remains unmet post-ruling — 2 further independent reproductions of the underlying session-teardown kill
  are logged in this doc's Progress Log after the ruling (2026-08-02 host-load/zombie-QG finding; 2026-08-02
  two-kills-one-session finding disambiguating against `ScheduleWakeup`).
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole open item (`--resume`/checkpoint capability) remains directly covered by the explicit, dated
  2026-08-02 operator ruling (option A) keeping `assigned_vm: NA` until the shared-host-RAM-exhaustion mechanism
  (condition `mdps-e2e-shared-host-teardown-fixed`) also closes — that prerequisite remains unmet (no closure entry
  found in this doc's Progress Log since the ruling). Not re-litigated.

- **2026-08-15 (slot-2, data_engineering) — 10th+ reproduction, `quality-gates.sh` (not a `/data-pipeline-check-*`
  skill, same shape as the 2026-08-02 entries).** A `market-tick-data-service` QG rerun (`--no-fix`, logging to
  `/tmp/mtds_qg_kamino_final3.log`) was launched as a backgrounded Bash call to verify a `KAMINO-SOLANA` oracle_prices
  wiring fix (`uac_data_type_validity_combinator_fragmentation_2026_07_07.md` todo). It was confirmed alive and
  correctly queued behind the host-wide qg-governor (cap 6) across several checks in the prior session segment. After a
  `/compact` + session-continuation boundary, the tracked PID no longer appeared in `ps aux` anywhere on the host, and
  the log was frozen mid-queue ("queued 330s", no further lines) with **no `EXIT_CODE=` line ever written** — i.e. it
  never even reached the point of starting real work, unlike most prior entries here (which died mid-execution). Same
  otherwise-healthy, zero-error-signal, killed-at-a-session-boundary signature as every entry above. Recovery:
  relaunched the QG run explicitly via `nohup bash -c '...' & disown` (rather than relying on the Bash tool's own
  `run_in_background`) plus a tracked `run_in_background` watchdog loop polling for `EXIT_CODE=`/liveness every 30s —
  not yet confirmed whether the explicit `disown` avoids the same kill (still monitoring as of this entry). No data lost
  (the underlying code diff was never touched by the dead process, confirmed via `git diff --stat` unchanged pre/post).
  Adds a queued-not-yet-executing case to this doc's existing evidence that the kill mechanism operates independent of
  the watched process's execution phase.

- **2026-08-15 (slot-2, data_engineering) — 11th reproduction, same task, AND a working mitigation found.** The
  `nohup ... & disown`-relaunched QG run from the entry above (PID 3960636, logging to `/tmp/mtds_qg_kamino_final4.log`)
  died the same way — confirmed independently via direct `ps -p 3960636` (no output) and log inspection (frozen at
  "queued 300s", no `EXIT_CODE=` line) — i.e. explicit `disown` did NOT survive the boundary either, same as the doc's
  existing evidence that even `setsid`-class detachment failed against the `WorkerLivenessWatchdog` pane-tree reap.
  **New signal**: this death lines up tightly with a `/compact` command the operator issued in the same turn the
  watchdog reported the failure — the closest yet to isolating the trigger as the session/turn-boundary re-invocation
  itself, not elapsed time (this run died _earlier_, at 300s vs the previous run's 330s). **Mitigation that worked**:
  instead of relaunching backgrounded again, ran the QG check as a plain **foreground/blocking** Bash call
  (`bash scripts/quality-gates.sh --no-fix > log 2>&1; echo EXIT_CODE=$? >> log`, no `&`, no `run_in_background`) — it
  ran to completion inside one tool call/turn (governor queue + full gate suite) and returned `EXIT_CODE=0` cleanly, no
  loss. This is consistent with the hypothesis that the kill fires between-turns (at session/context-boundary
  re-invocation), not mid-tool-call — a call that blocks synchronously inside a single turn never crosses that boundary
  and so never gets torn down. **Not a general fix**: only viable when the expected runtime fits inside one turn's tool
  timeout (~10 min here); still doesn't help longer-running backgrounded work, which remains exposed pending the
  `mdps-e2e-shared-host-teardown-fixed` closure condition. Worth surfacing to whoever roots-causes this: prefer
  foreground execution over backgrounding for any check expected to finish within the timeout budget, until the
  underlying watchdog/RAM-exhaustion mechanism is fixed.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:34a75202ca1bc9fd]: KEEP-NA, valid — sole open item (--resume/checkpoint capability) is directly gated by an explicit dated 2026-08-02 operator ruling until a named prerequisite condition closes; that condition remains unmet as of the doc's most recent 2026-08-15 reproduction entries.
- **context-scout 2026-08-17**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — sole open item (`--resume`/checkpoint
  capability for `pipeline_e2e_check`) is directly gated by the explicit dated 2026-08-02 operator ruling (option A)
  until the shared-host-RAM-exhaustion mechanism (`mdps-e2e-shared-host-teardown-fixed`) also closes; that
  prerequisite remains unmet as of the doc's most recent 2026-08-15 reproduction entries.
