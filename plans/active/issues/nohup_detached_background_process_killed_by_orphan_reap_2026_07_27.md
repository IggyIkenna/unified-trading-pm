---
doc_type: issue
title:
  "`nohup <cmd> & echo PID` inside a Bash-tool `run_in_background` call gets the real work killed by orphan_reap
  ~300-355s later — fleet-wide recurring pattern, not a one-off"
summary: >-
  Backgrounding a long-running script with `nohup <cmd> & echo "PID:$!"` (so the wrapping Bash-tool call returns
  immediately) detaches the real process from the tracked session tree. The server's `orphan_reap` sweep
  (`agent-orchestrator/server/orphan_reap.py`) then classifies it as an orphan and SIGKILLs it ~300-355s later —
  observed on slot 8 (this session, killed a real VM-launch-and-poll script mid-run) and independently on slots 7, 9,
  10, 15 in the same hour via `journalctl | grep orphan_reap`, so this is a recurring fleet-wide trap, not an isolated
  mistake. The correct pattern is to pass the actual long-running command directly to the Bash tool with
  `run_in_background: true` (no `nohup`/`&` wrapper) — the harness's own backgrounding keeps the process properly
  parented and tracked, and the harness notifies on real completion.
status: open
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, orphan-reap, background-task, worker-liveness, recurring-bug, lesson]
related:
  [
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-27"
author: unknown
source: "found while verifying instrument_availability_hive_canonicalisation-001 on real infra, slot-8, 2026-07-27"
parent_epic: agent_operating_framework_master
priority: P2
estimate_class: research
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    agent-orchestrator/server/orphan_reap.py,
    agents/worker.md,
    /plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md,
  ]
depends_on: []
---

# `nohup & echo PID` gets killed by orphan_reap ~300-355s later

## What I found

While proving the `instrument_availability_hive_canonicalisation-001` writer fix green on real infra (real VM launch +
poll via `instruments-service/scripts/pipeline_e2e_check.py`), I backgrounded the checker with:

```bash
nohup .venv/bin/python scripts/pipeline_e2e_check.py ... > check.log 2>&1 &
echo "PID:$!"
```

wrapped inside a Bash-tool call with `run_in_background: true`. The wrapping Bash-tool call returned almost instantly
(just the `echo`), which I initially mistook for a real "background task started" signal. The actual
`pipeline_e2e_check.py` process (PID 700349) kept running detached — and was killed ~323s later:

```
$ journalctl --since "10 min ago" | grep 700349
Jul 27 08:58:29 ... orphan_reap sweep: slot 8 pid 700349 age=323s KILLED
```

This silently discarded a real, in-flight VM-launch-and-poll operation (the force-leg VM had already written real data
by the time it was killed — I recovered by reading the per-VM manifest shard directly rather than trusting the dead
checker's own report, but a less careful session would have seen "process vanished, no report" and either wrongly
concluded failure or silently re-launched a duplicate VM).

**This is not an isolated slot-8 mistake.** A broader `journalctl | grep orphan_reap` sweep over the same session window
shows the identical `age=3XXs KILLED` pattern hitting slots 7, 9, 10 (multiple times), and 15 — all within about 25
minutes of each other. The consistent ~300-355s age band matches a single orphan-reap timeout constant, and the volume
across distinct slots strongly suggests many agents independently reach for the same `nohup & echo PID` idiom when they
want a Bash-tool call to "return immediately so I can keep working," not realizing the harness's own
`run_in_background: true` parameter already does exactly that — correctly, without detaching the process from the
tracked session tree that `orphan_reap` uses to decide what's alive.

## Why it matters

- **Silent work loss**: a killed VM-launch-and-poll script can leave a real GCP VM running with no local observer, or
  worse, get "cleanly" retried by a subsequent call that duplicates in-flight work (double VM launches, double spend, or
  a race on the same GCS shard).
- **Misleading failure signal**: the process just vanishes — no traceback, no exit code in the log, nothing to
  distinguish "the script crashed" from "the orchestrator killed it." A worker following the async-wait-discipline HARD
  RULE ("never report a backgrounded task done before its real exit") can be fooled into thinking a real crash occurred
  and file a wrong root-cause finding.
- **Recurring, not rare**: 5+ distinct slots hit this in roughly the same hour — this is a fleet-wide idiom trap, not a
  one-off typo.

## Recommended decision

1. **Immediate (no code change needed)** — add a one-line callout to `unified-trading-pm/agents/RULES.md` § 2 (the ship
   loop) or `worker.md`'s async-wait section: _"Never `nohup <cmd> & echo $!` inside a `run_in_background: true` Bash
   call — pass the long-running command directly with `run_in_background: true` and no `&`/`nohup` wrapper; the
   harness's own backgrounding is what keeps the process correctly parented against `orphan_reap`."_ This is the
   cheapest fix and would have prevented all 5+ observed occurrences today.
2. **Investigate (optional, `agent-orchestrator`)**: `orphan_reap.py`'s liveness check currently can't distinguish "a
   worker's own intentionally-detached background job" from "a genuinely orphaned/leaked process" — if there's a
   legitimate use case for a worker wanting a script to outlive a single tool call (there might not be; the harness's
   native `run_in_background` already covers the common case), consider whether the reap sweep should special-case
   processes whose parent is a tracked worker shell rather than reaping by age alone. Lower priority than (1) since the
   RULES.md fix addresses the actual root cause (agents shouldn't be using `nohup` here at all).

## Evidence

```
$ journalctl --since "1 hour ago" | grep orphan_reap
Jul 27 08:31:39 ... orphan_reap sweep: slot 10 pid 12510 age=354s KILLED
Jul 27 08:33:44 ... orphan_reap sweep: slot 7 pid 88689 age=323s KILLED
Jul 27 08:37:51 ... orphan_reap sweep: slot 10 pid 210847 age=310s KILLED
Jul 27 08:37:52 ... orphan_reap sweep: slot 10 pid 211516 age=306s KILLED
Jul 27 08:37:53 ... orphan_reap sweep: slot 10 pid 211517 age=305s KILLED
Jul 27 08:38:55 ... orphan_reap sweep: slot 15 pid 220651 age=314s KILLED
Jul 27 08:44:03 ... orphan_reap sweep: slot 9 pid 330750 age=324s KILLED
Jul 27 08:45:04 ... orphan_reap sweep: slot 10 pid 355910 age=331s KILLED
Jul 27 08:55:23 ... orphan_reap sweep: slot 10 pid 636064 age=355s KILLED
Jul 27 08:58:29 ... orphan_reap sweep: slot 8 pid 700349 age=323s KILLED   <- this session
```

Recovery in this session: verified the force-leg's real GCS write + manifest row directly (per-VM shard
`_index/per_vm/instr-backfill-cefi-pchk-0727085259-f-hyperliquid.parquet`) rather than trusting the killed process's own
(never-written) report, then re-ran the skip leg using the correct pattern (no `nohup`) and it completed normally.

**Independent re-occurrence (2026-07-28, slot 7):** hit the identical pattern fresh, mid-backfill on
`prediction_satellite_ao_dispatch_batch4-010` (resuming
`market-tick-data-service/scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply` across 348 dates).
Backgrounded with `nohup .venv/bin/python ... > run.log 2>&1 &` in a plain (non-`run_in_background`) Bash call; the
process (PID 4006112) ran healthily for 23+ dates then vanished with no traceback, no exit code, no TOTALS line —
confirmed via `journalctl -k --since "2026-07-28 12:10:00"`: `orphan_reap sweep: slot 7 pid 4006112 age=346s KILLED`.
This is very likely the SAME root cause previously mis-attributed to "shared-host RAM exhaustion" in
`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` and in this exact task's own prior session (slot-16's
earlier 55/348-date run, which the plan doc's Progress Log describes as "WORKER SESSION DIED mid-run (background process
reaped, exit 144/SIGTERM — not a script bug)" — that framing was right that it wasn't a script bug, but the actual
mechanism is `orphan_reap`, not RAM pressure; worth a cross-check against
`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`'s own evidence for whether some or all of ITS occurrences
are actually this same bug misdiagnosed). Recovery: relaunched via the correct pattern (the long-running command passed
directly to the Bash tool's `run_in_background: true`, no `nohup`/`&` wrapper) — the script's own idempotency check made
this a zero-cost resume (no data lost, only compute time). Confirms the recommended-decision-1 fix (below) directly,
independently, a day later — implementing it now rather than leaving it open a third time.

**A DIFFERENT, second kill hit the same task 25 min after the `run_in_background` fix landed (2026-07-28, slot 7):**
after switching to the correct pattern (long-running command passed directly to `run_in_background: true`, no `nohup`),
the resumed backfill ran cleanly for ~25 minutes of local-only bash progress-checking with **no `/progress` heartbeat**
sent in that window — the worker.md Heartbeat HARD RULE's ≤10-min cadence was violated. `WorkerLivenessWatchdog` read
the slot as stale and triggered `kill_session(orch-slot-7)`, which SIGTERMs the pane's whole descendant tree BEFORE
`tmux kill-session` (by design, `_reap_pane_tree` in `tmux_spawn.py`) — killing the properly-parented backfill as
collateral, confirmed via `journalctl | grep 'kill_session(orch-slot-7)'` at the death timestamp, a DIFFERENT log
signature from `orphan_reap sweep: ... KILLED`. **This means `run_in_background` fixes the orphan-reap failure mode but
does NOT exempt a worker from the heartbeat rule while monitoring a long job** — heartbeat cadence is the binding
constraint, independent of how well-parented the background process is. Documented as its own numbered item (5) in
`/codex/12-agent-workflow/async-wait-and-poll-discipline.md` § "Watcher coverage" (the durable SSOT for this class of
lesson) rather than folded into this doc's own `nohup`-specific open work, since it is a genuinely separate mechanism.
Recovery: resumed again (idempotent via `--report`) + immediately began sending `/progress` every ≤8 min.

## Open work

- [x] ✅ [DOC] P2. Add the one-line `nohup`-avoidance callout to `unified-trading-pm/agents/RULES.md` § 2 or
      `worker.md`'s async-wait section (recommended decision 1 above). — unified-trading-pm (worker.md, added right
      after the Heartbeat section's PROGRESS guidance, 2026-07-28).
- [ ] [SCRIPT] P3. Optional — investigate whether `agent-orchestrator/server/orphan_reap.py` should special-case a
      worker-shell-parented background process (recommended decision 2 above). Lower priority; the RULES.md/worker.md
      fix is the primary mitigation and now shipped; this remains open only as a defense-in-depth nice-to-have.
- [ ] [SCRIPT] P3. Cross-check `plans/active/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`'s own
      evidence (its logged death timestamps) against `journalctl | grep -E 'orphan_reap sweep|kill_session'` for the
      same windows — some or all of its "RAM exhaustion" occurrences may actually be this doc's `nohup`/`orphan_reap`
      bug (or the sibling `kill_session` heartbeat-staleness collateral-kill, see this doc's 2026-07-28 addendum above)
      misdiagnosed, not genuine memory pressure. If confirmed, correct that doc's root-cause framing rather than leaving
      two docs describing the same incidents under different causes. Repo: unified-trading-pm (investigation + doc
      correction only, no code).

      **na-eligibility-audit 2026-08-03**: the referenced doc is now archived/resolved
                                                                                                              (`plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`, 2026-07-28) but via a
                                                                                                              DIFFERENT fix mechanism (a qg-governor runtime abort-monitor watchdog + SIGTERM/SIGINT/SIGHUP signal traps) — its
                                                                                                              own extensive multi-session Progress Log never performs the specific `orphan_reap`/`kill_session`-journalctl
                                                                                                              cross-check this todo asks for; every one of its own recorded incidents cites `free -h` swings, load-average
                                                                                                              spikes, OOM-killer signatures, or TYPE-CHECK/pytest timeouts, never an `orphan_reap sweep ... KILLED` log line.
                                                                                                              This cross-check remains genuinely un-done, not closing here.

## Progress Log

- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — first marker on this doc. Covered by
  the 2026-07-31 operator directive `unified-trading-pm@14478ca26` (`planning` → `NA` + local-only). The primary
  mitigation already shipped (the `nohup`-avoidance callout in `worker.md`); both remaining `[SCRIPT] P3` items are
  explicitly optional/defense-in-depth — todo 2 is framed "consider whether `orphan_reap.py` should special-case a
  worker-shell-parented process (there might not be a legitimate use case)", and todo 3 is a cross-doc root-cause
  RE-ATTRIBUTION judgment (deciding whether `shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`'s occurrences
  are actually this bug misdiagnosed). Neither has a worker-determinable done-state.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — re-read end-to-end; both remaining `[SCRIPT] P3` items
  are explicitly optional/defense-in-depth per the doc's own primary-mitigation-already-shipped framing (one is a
  "consider whether there's even a legitimate use case" question, the other a cross-doc root-cause re-attribution
  judgment). Checked against the round7-10 precedent set — none apply. Corroborated same-day: `/ag-closeout-audit ao`
  batch12 independently lists this doc under genuinely-human-only (4), "(optional leg only)."

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of both open
  items. Item 1 (orphan_reap special-casing investigation) is explicitly open-ended ('there might not be a legitimate
  use case'). Item 2 (cross-check the archived RAM-exhaustion doc's incidents against orphan_reap journalctl signatures)
  is a real but low-materiality (P3) root-cause re-attribution judgment call; 3 prior audits (08-02, 08-06,
  round11-08-09) kept this NA consistently. No new facts found this pass.
