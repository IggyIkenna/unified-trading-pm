---
doc_type: issue
title: Kick-escalation force-killed 7 slots on one out-of-credits account — watchdog had no rate-limit awareness
summary: >-
  Operator noticed an unexplained overnight kill wave (00:30-05:30 UTC, 2026-08-14): 7 `slot_wedged_killed_for_resume`
  events clustered in a 90s window (02:13:58-02:15:15), plus elevated
  `orphan_process_reaped`/`orphaned_sibling_dirty_repo_detected` noise across the whole window. Live read-only
  investigation (SSM against `state.db`) found the root cause: account `sub-a-ikenna` ran out of usage credits
  (`overage_status: rejected`, `overage_disabled_reason: out_of_credits`) shortly before 02:09 UTC. Every slot pinned to
  that account showed Claude Code's own blocking menu ("❯ 1. Stop and wait for limit to reset"), which `classify_pane`
  reads as an ordinary "frozen"/"idle" buffered-prompt state — indistinguishable from a genuine wedge to
  `WorkerLivenessKicker`. The kick loop's escalation counter (`_consecutive_kick_failures` →
  `kick_escalation_threshold`) has zero rate-limit awareness (confirmed via grep — no `rate_limit` reference anywhere in
  `worker_liveness/__init__.py`), so it force-killed all 6-7 affected slots within ~90s, requeuing most of their
  in-flight tasks — which then landed right back on the same still-exhausted account and repeated through the night
  (confirmed recurring kills at 02:33 and 03:05 on the same account, `rate_limited_until` stamped `2026-08-14T06:40:00`,
  still in effect as of the 05:47 UTC live check that also found the fleet at 0 live tmux worker sessions with 716 tasks
  dispatched/queued). The fleet's OWN periodic rate-limit scanner (`TmuxPruner.scan_rate_limits_once`, `_RATE_LIMIT_RE`
  in `tmux_pruner.py`) exists for exactly this class of problem but only matched the original "You've hit your Sonnet
  limit" banner, not the persistent follow-up menu that stays on screen after that banner scrolls/redraws away — so it
  never caught this account either.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, watchdog, rate-limit, kick-escalation, force-kill, root-cause]
related:
  - /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md
  - /codex/04-architecture/agent-orchestrator-worker-liveness.md
  - /codex/15-runbooks/tmux-death-diagnostics.md
created: "2026-08-14"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by: agent-orchestrator@b8d62f8dd7
locked_by:
locked_since:
source: >-
  Operator chat instruction, 2026-08-14: "in AO getting alot of kills i can't explain 00:30 to 05:30, lets dig into what
  was the issue and how we could have preevnted it needing to sotp" — followed by "yes please and then fix and ship"
  once root cause was found.
assigned_vm: NA
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: []
---

# Kick-escalation force-killed 7 slots on one out-of-credits account

## What was measured (live, read-only, via SSM against `state.db`)

Full event-count breakdown for the reported 00:30-05:30 UTC window, queried directly off `activity_log`:

| event_type                             | count | window                        |
| -------------------------------------- | ----- | ----------------------------- |
| `orphan_ref_verified`                  | 652   | continuous, 00:30:53-05:20:16 |
| `orphan_ref_self_closed`               | 631   | continuous, 00:30:53-05:20:16 |
| `orphaned_sibling_dirty_repo_detected` | 25    | spread, 00:30:08-04:47:35     |
| `orphan_process_reaped`                | 9     | 01:29:18-03:32:27             |
| `slot_wedged_killed_for_resume`        | 7     | **02:13:58-02:15:15 (90s)**   |
| `watchdog_heartbeat_resumed`           | 2     | 01:42:08, 03:07:13            |
| `slot_resume_respawned`                | 1     | 02:19:11                      |

The last four (`orphan_ref_*`, `orphan_process_reaped`, `orphaned_sibling_dirty_repo_detected`) are downstream cleanup
consequences of the kill cluster, not independent causes — more force-kills produce more orphaned processes and dirty
worktrees to reap. `watchdog_heartbeat_resumed` is a different, gentler recovery path (unrelated slots 12/2), not part
of this cluster.

**All 7 `slot_wedged_killed_for_resume` rows share the identical `reason`**:
`"kick failed, pane='idle', K consecutive kick failures (forced)"`. Tracing the preceding `worker_kick_failed` rows
(02:09:14-02:10:30) for the same 6 slots (5, 6, 11, 14, 21, 26 — slot 18 joined via a differently-classified pane) shows
identical `input_snippet`: `"1. Stop and wait for limit to reset"` — Claude Code's own usage-limit / out-of-credits
blocking menu. The `tmux_session_lost` records for the kills all carry the same `account_snapshot`:
`account_id: "sub-a-ikenna"`, `overage_status: "rejected"`, `overage_disabled_reason: "out_of_credits"`.

**Recurrence confirmed**: slot 1 killed again on the same account at 02:33, slot 10 killed again (SIGKILL) at 03:05 —
`rate_limited_until` for `sub-a-ikenna` moved from a stale `2026-08-13T15:29:59` to a fresh `2026-08-14T06:40:00`
between 02:15 and 02:33, meaning the account was STILL exhausted through the rest of the night. A live fleet check at
05:47 UTC found 0 live tmux worker sessions with 716 tasks dispatched/queued — consistent with continued churn on this
and other accounts (see "Other confirmed contributors" below).

## Root cause

1. `WorkerLivenessKicker._tick_once` (`server/worker_liveness/__init__.py`) classifies a pane via `classify_pane()`,
   which reads any non-empty buffered `❯`-line as "frozen" — including Claude Code's usage-limit menu
   (`❯ 1. Stop and wait for limit to reset`), which is structurally indistinguishable from genuine unsubmitted input.
2. The kick loop has **zero rate-limit awareness** — confirmed via
   `grep -n "rate_limit" server/worker_liveness/__init__.py` returning nothing prior to this fix. A kick sent into this
   menu is a guaranteed no-op (there is nothing useful to submit), so `_consecutive_kick_failures` climbs on every tick
   until `kick_escalation_threshold`, then `_maybe_auto_respawn_stuck_slot` force-kills via `_kill_wedged_for_resume`
   (`server/worker_liveness/_respawn.py`).
3. Every slot sharing the same exhausted account shows the identical menu at the same time (a quota exhaustion blocks
   the WHOLE account, not one session), so all of them cross the threshold together — explaining the tight 90s cluster.
4. `TmuxPruner.scan_rate_limits_once()` (`server/tmux_pruner.py`) already exists specifically to catch an account
   hitting its limit mid-session and mark it via `mark_account_rate_limited` (which fans out a fleet-wide rotation off
   that account) — but its `_RATE_LIMIT_RE` only matched the ORIGINAL "You've hit your Sonnet limit" banner line, not
   the persistent follow-up menu that remains on screen after that banner scrolls/redraws out of the periodic scan's
   60-line capture window. It never caught this account, so nothing steered new dispatch away from it, and requeued
   tasks kept landing back on the same wall.

## Other confirmed contributors (pre-existing, unrelated to tonight's trigger)

- `sub-g-alpavolt` (slots 27/31): `spawn_retry_cap_reached` with `session_alive: false`, `elapsed_s: ~185,000` (~51h) —
  a chronic dead spawn-retry loop, not new tonight. Worth its own follow-up but out of scope here.
- `sub-f-odum2default` (slot 1, 01:15): hit a `deepseek-pro` "model not found / no access" error — a config issue,
  unrelated to rate limits.

## Fix shipped

Two-layer, same-day:

1. **`server/tmux_pruner.py`** — widened `_RATE_LIMIT_RE` to also match `"Stop and wait for limit to reset"`, so the
   periodic scanner catches the persistent menu even when the original banner has already scrolled away.
2. **`server/worker_liveness/__init__.py`** — added `_ACCOUNT_BLOCKED_RE` and a guard at the top of the per-slot kick
   loop (right after `classify_pane`): if the captured pane matches the blocking-menu pattern, the slot is never kicked,
   never counted toward `kick_escalation_threshold`, and its `_consecutive_kick_failures` streak is cleared. The account
   is marked rate-limited (idempotent, same call the periodic scanner makes) so the fleet-wide rotation fires
   immediately rather than waiting for the next scan tick.

Tests added: `tests/test_worker_liveness.py` (two new cases —skip-and-mark, and don't-re-mark-if-already-marked) and
`tests/test_tmux_pruner_rate_limit_scan.py` (new file — menu-only pane now marks the account; regression guard that the
original banner phrasing still matches).

## Todo

1. ✅ [SCRIPT] P1. Widen `tmux_pruner.py`'s `_RATE_LIMIT_RE` to catch the persistent usage-limit menu —
   agent-orchestrator@b8d62f8dd7.
2. ✅ [SCRIPT] P1. Add the account-blocked guard to `WorkerLivenessKicker._tick_once` before any kick/escalation branch,
   with account-marking + failure-streak reset — agent-orchestrator@b8d62f8dd7 (extracted as
   `_handle_account_blocked_pane` to stay under the `_tick_once` complexity cap).
3. ✅ [SCRIPT] P1. Add regression tests for both layers — agent-orchestrator@b8d62f8dd7 (`tests/test_worker_liveness.py`
   2 new cases, `tests/test_tmux_pruner_rate_limit_scan.py` new file, 2 cases).
4. ✅ [SCRIPT] P1. Run `quality-gates.sh` green and ship via `quickmerge.sh` — agent-orchestrator@b8d62f8dd7, landed on
   `live-defi-rollout`, post-push ancestry verified.

## Progress Log

- **2026-08-14** — Investigated live via SSM (`check-ao-recent-deaths.sh` + direct `activity_log` queries), found root
  cause (account exhaustion blind spot in kick-escalation), implemented both fix layers + tests (`quality-gates.sh`
  green: 3668 passed, 6 skipped, 0 ruff/basedpyright issues), shipped via `quickmerge.sh --agent` as
  agent-orchestrator@b8d62f8dd7 (landed `live-defi-rollout`, Tier-C drain promotes to staging within ~15min). Issue
  resolved.
