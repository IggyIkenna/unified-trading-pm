---
doc_type: issue
title: >-
  Fleet dispatch:done gap is driven by unplanned tmux session loss mid-task, not watchdog kills — root cause not yet
  found
summary: >-
  Follow-up from shipping the Fleet Efficiency KPIs `dispatches/done` tile + a slot/role/day breakdown
  (agent-orchestrator@016abaff2f, @8a7a8c0fe0, @<pending>): operator asked why redispatch (retry) is so common and
  whether it's fixable, since "tasks done per spend" would improve a lot if it were. Live read-only query (SSM,
  `state.db` mode=ro) against the last 24h's `task_dispatched`/`slot_done` activity_log rows found: 157 of 541 distinct
  dispatched tasks (29%) got redispatched at least once; of those, `tmux_session_lost` appears in the gap for 148/157
  (94%) vs. an explicit watchdog kill in only 11/157 (7%) and `stale_dispatch_reclaimed` in just 1/157 — the fleet's own
  watchdog is NOT the dominant cause of retries, an unexplained tmux session death is. Widening to all
  `tmux_session_lost` events in 24h (1203 total, most self-heal via resume and never need a full task requeue): 971/1203
  (81%) have NO planned-teardown or already-in-progress-resume precursor in the preceding 60s (i.e., genuinely abrupt),
  and 508/1203 (42%) fire while the slot is holding an undone dispatched task — directly explaining a meaningful share
  of the retry/redispatch volume. Correlated against the orchestrator's own `resource_history` samples (24h,
  `data/state/resource_history/*.jsonl`): CPU%, load_avg_1m, and swap% at the moment of loss were NOT elevated vs. the
  24h baseline (if anything, median CPU at loss-time was LOWER than the 24h median) — a working hypothesis that acute
  host resource contention (the host runs ~15-20 concurrent `claude` worker processes plus other repos' heavy pytest/QG
  runs on one 16-vCPU/30GB box, with the box observed steadily swapping, 5%->21.6% swap-used over 24h with 0 OOM-kills
  logged) triggers the losses was NOT supported by this pass — swap is climbing gradually but RAM usage stays low
  (~27%), consistent with normal idle-page reclaim rather than genuine memory pressure. Root cause of the abrupt tmux
  session death itself (network/SSH layer? tmux server bug? underlying Claude CLI crash? per-account rate-limit
  teardown?) is UNRESOLVED — this doc exists to hand that off as tracked, evidence-backed next steps rather than losing
  the investigation to chat history.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, fleet-efficiency, tmux, root-cause, dispatch-retry, kpi]
related:
  - /codex/04-architecture/agent-orchestrator-scheduled-jobs.md
  - /codex/15-runbooks/safe-service-restart-procedures.md
  - /codex/05-infrastructure/deployment-observability.md
  - /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md
created: "2026-08-10"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by:
locked_by:
locked_since:
source: >-
  Operator chat instruction, 2026-08-10, after being shown the redispatch/retry breakdown: "yeah but why are they
  crashing/timing out/getting killed mid-task this is what we need to improve as our tasks done per spend will imprve
  alot in that case so add to your todos and investigate."
assigned_vm: NA
execution_scope: local-only
priority: P2
drift_direction: advance-code
depends_on: []
---

# Fleet dispatch:done gap root cause — unplanned tmux session loss, not watchdog kills

## What was measured (live, read-only, via SSM against `state.db` on the orchestrator VM)

**Redispatch precursor (157 redispatched tasks, last 24h)** — filtered to events scoped to the exact `task_id` (or
slot-level events with `task_id IS NULL`) between a task's first and second `task_dispatched`, NOT all activity on a
busy slot (an earlier, less careful pass conflated the two and produced a misleading picture):

| Precursor in the gap                                                                  | Count | % of 157                                                      |
| ------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------- |
| `tmux_session_lost` present                                                           | 148   | 94%                                                           |
| An explicit `watchdog_*kill*` event                                                   | 11    | 7%                                                            |
| `stale_dispatch_reclaimed` (the last-resort reconciler in `server/stale_dispatch.py`) | 1     | 0.6%                                                          |
| Context saturation/compact event present                                              | 68    | 43%                                                           |
| A `slot_done`/`slot_done_verified` tagged to THIS exact task_id in the gap            | 3     | 2% (rules out "double-counted as both done and redispatched") |

Gap duration (dispatch #1 -> dispatch #2): median 1428s (~24min), min 127s, max 65009s (~18h) — wide spread, not one
single mechanism.

**All `tmux_session_lost` events, last 24h (1203 total — most self-heal via resume and never reach a full redispatch)**,
classified by what preceded each on the same slot in the prior 60s:

| Classification                                                                                  | Count   | %       |
| ----------------------------------------------------------------------------------------------- | ------- | ------- |
| Preceded by a planned session end (`worker_one_task_per_session_reset` or `slot_done_verified`) | 142     | 12%     |
| Preceded by an already-in-flight resume attempt (`slot_resume_pending`)                         | 90      | 7%      |
| **Unexplained — no planned/in-progress-resume precursor**                                       | **971** | **81%** |
| Slot was holding an undone `task_dispatched` (mid-task) at the moment of loss                   | 508     | 42%     |

**Resource correlation (24h `resource_history` samples, `cpu_percent`/`load_avg_1m`/`swap_percent`/`iowait_percent`)** —
at the exact moment of a `tmux_session_lost` event vs. the 24h baseline:

| Metric      | At tmux_session_lost (median) | 24h baseline (median) | At tmux_session_lost (p90) | 24h baseline (p90) |
| ----------- | ----------------------------- | --------------------- | -------------------------- | ------------------ |
| CPU%        | 43.8                          | 63.2                  | 64.9                       | 97.8               |
| load_avg_1m | 11.6                          | 16.9                  | 20.2                       | 43.4               |
| swap%       | 14.7                          | 13.6                  | 15.1                       | 25.3               |
| iowait%     | 9.5                           | 9.0                   | 40.7                       | 24.3               |

Loss moments are NOT elevated vs. baseline on CPU/load/swap — if anything lower. iowait p90 is somewhat higher at loss
moments (40.7 vs 24.3 baseline) — the one metric worth a closer look, but the median is unremarkable, so this reads as
noisy/inconclusive rather than a confirmed signal.

Separately: `free -h` on the VM showed swap climbing from 5.2% (2026-08-09 00:00) to 21.7% (2026-08-10 17:47) over 24h
with RAM usage steady at ~27% and **zero OOM-kills** in that window (`journalctl -k` grep, though the check needs `sudo`
and partially failed — see follow-up todo). Rising swap with low RAM usage and no OOM-kills reads as normal idle-page
reclaim under Linux's default swappiness, not acute memory pressure — this does not support "the host briefly ran out of
memory and that's what kills sessions" as-is.

## What this rules out

- **NOT the fleet's own watchdog** (`server/worker_liveness_watchdog.py`) killing workers it judges stuck — only 7% of
  redispatch gaps show an explicit kill event.
- **NOT the stale-dispatch last-resort reclaimer** (`server/stale_dispatch.py`) — that's a backstop for a slot stuck
  `dispatched` with a dead `tmux_session` for a long time; it fired in only 1/157 cases here, meaning most of these
  never even reach that backstop's multi-minute-to-hours threshold before the tmux loss is independently observed.
- **NOT (as measured) acute host CPU/load/swap spikes** — the correlation pass found no elevation at loss moments.
  Caveat: this used the periodic `resource_history` sampler's nearest sample (up to 120s away), which could miss a
  genuinely brief (sub-sample-interval) spike — not a fully conclusive ruling-out.

## What's confirmed but not yet root-caused

- The proximate event immediately preceding almost every redispatch is `tmux_session_lost` (94%), and the large majority
  of ALL `tmux_session_lost` events (81%) have no planned-teardown explanation in the preceding minute — these are
  genuinely abrupt.
- 42% of all tmux losses hit a slot mid-task (not idle) — directly interrupting live work, which is exactly the
  mechanism inflating `dispatches` without a matching `done` (the `dispatches/done` and per-role/slot/day breakdown
  shipped this session: `agent-orchestrator@016abaff2f`, `@8a7a8c0fe0`).
- Context saturation (compact/force-compact events) co-occurs with 43% of redispatch gaps, including one directly
  self-descriptive event name, `context_saturated_session_lost_task_requeued` — this is the strongest concrete lead for
  a SUBSET of cases (hitting the context ceiling appears to itself precipitate a session loss in some fraction of runs),
  but doesn't explain the other ~57%.

## Todo

- [ ] [INFRA] P2. **Get real tmux/system-level evidence for an unplanned loss**, not just orchestrator-side activity_log
      inference. On the orchestrator VM (`i-0c9b283b31d6b5ca7`, read-only SSM only — see
      `scripts/orchestrator/check-ao-backlog-status.sh` for the access pattern): (a) fix the `journalctl -k` OOM check
      that partially failed this session (needed `sudo`, command errored before finishing — rerun cleanly and confirm 0
      OOM-kills over a longer window, not just 24h); (b) check `journalctl --user` or the tmux server's own log (if any)
      for the PIDs/session names tied to a sample of `tmux_session_lost` events with NO planned precursor; (c) check
      whether the underlying `claude` CLI process for a lost session is still alive (zombie/defunct) or fully gone at
      the moment of loss — distinguishes "tmux itself died" from "the CLI process crashed and took the pane with it."
      **Done when**: at least one genuinely unplanned loss has a confirmed process-level cause (CLI crash, tmux server
      issue, OOM-kill, SIGKILL from elsewhere, or ruled out entirely with real evidence). Repo: agent-orchestrator.
- [ ] [INFRA] P2. **Check for a per-account correlation** — do losses cluster on specific `account_id`s (e.g. one
      DeepSeek/Anthropic account rotating or rate-limiting more aggressively, which could force a session teardown
      independent of host load)? Join the 1203 `tmux_session_lost` events' `slot_id` against `SlotRow.account_id` at
      that time and look for a skew. **Done when**: either a specific account/provider is shown to explain a
      disproportionate share, or the loss rate is confirmed roughly uniform across accounts. Repo: agent-orchestrator.
- [ ] [INFRA] P3. **Narrow the context-saturation lead**: of the 43% of redispatch gaps that show a
      compact/force-compact event, how many specifically show `context_saturated_session_lost_task_requeued` (the
      self-descriptive one) vs. an unrelated compact that happened to also be in the window? If the former is common,
      the actual fix may be in the context-saturation/force-compact path itself (does forcing a compact near the context
      ceiling sometimes crash the session instead of shrinking it?). Repo: agent-orchestrator.
- [ ] [INFRA] P3. **Re-run the resource-history correlation with tighter sampling** if the sampler's interval allows —
      the current pass could miss a spike shorter than the sample gap. Check `resource_history.SAMPLE_INTERVAL_SECONDS`
      and, if it's coarse (e.g. 60s+), consider whether a sub-interval spike is plausible given `iowait_percent`'s
      elevated p90 (40.7 vs 24.3 baseline) at loss moments — the one metric in this pass that wasn't clearly
      unremarkable. Repo: agent-orchestrator.

## Progress Log

- 2026-08-10: doc created same session as the Fleet Efficiency KPIs `dispatches/done` tile +
  slot/role/day/retry-accounting breakdown shipped to `agent-orchestrator` (commits `016abaff2f`, `8a7a8c0fe0`, and a
  pending `TaskUsageRow.dispatch_role` fallback fix for the role breakdown). Investigation run entirely read-only via
  SSM against the live `state.db` + `resource_history` JSONL — no code changed as part of this doc. All four follow-ups
  above are diagnostic reads, not fixes — a real fix can't be scoped until one of them lands on an actual cause.
