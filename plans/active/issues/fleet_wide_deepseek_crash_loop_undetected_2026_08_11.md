---
doc_type: issue
title: "Fleet-wide DeepSeek spawn crash loop went undetected — root mechanism still unconfirmed"
summary:
  "All 6 Anthropic accounts were simultaneously out of credit (operator-confirmed 2026-08-11: expected, not a bug),
  forcing the entire ~33-slot fleet onto 2 DeepSeek accounts. tmux_session_lost fired for nearly every slot in a
  13-minute window (~55 spawn attempts fleet-wide); slot 15 alone died 7 times in an hour, each time after making real
  logged progress, with the tmux pane vanishing with NO captured exit signal (not OOM — 21Gi free, no kernel kill
  lines). Zero flap alerts fired anywhere in the fleet because the per-slot flap detector (DEFAULT_FLAP_THRESHOLD=3
  successes in DEFAULT_FLAP_WINDOW_SECONDS=600) is tuned for one slot failing fast — it never trips when churn is spread
  thin across many slots at a moderate ~7-15min per-slot cadence. DeepSeek's own documented concurrency ceiling (500
  concurrent connections on v4-pro, 2500 on v4-flash per api-docs.deepseek.com) is nowhere near being hit by 33 workers,
  so account-level rate-limiting is ruled out as the cause — the actual crash mechanism remains unconfirmed. A
  fleet-wide flap detector (pages + activity-logs) was shipped same-day to close the zero-alert visibility gap; a
  git-health monotonic-guard bug was also found and fixed during triage but confirmed NOT to be the cause of this
  specific loop (the resume/requeue decision path reads live git status, not the cached column that bug affected)."
status: open
nature: notes
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, deepseek, crash-loop, flap-detection, incident]
related:
  [
    /codex/15-runbooks/safe-service-restart-procedures.md,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /plans/active/ao_satellite_ao_dispatch_batch19_2026_08_10.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
  ]
created: 2026-08-11
last_updated: 2026-08-11
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/resume_lifecycle.py,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
  ]
source: operator-reported respawn-without-finishing pattern on slot 15, investigated + partially remediated 2026-08-11
archive_exempt:
---

# Fleet-wide DeepSeek spawn crash loop — root mechanism still unconfirmed

## What I found

Operator reported agents "keep respawning without finishing their tasks and burning through credits." Investigation
(read-only, via AWS SSM against the orchestrator VM, `i-0c9b283b31d6b5ca7` / `ap-northeast-1`) found:

- **Cause of the DeepSeek fallback**: all 6 Anthropic accounts were simultaneously `rate_limited`/`disabled`,
  `overage_status: rejected` — **operator-confirmed 2026-08-11: this was expected, ran out of credit, not a bug or
  surprise.** No further investigation needed on this half.
- **The actual crash loop**: with every slot forced onto the 2 DeepSeek accounts, `tmux_session_lost` fired for nearly
  every slot ID (1-33) in a single 13-minute window (05:30:51–05:43:38), several twice — `autospawn_succeeded` ×61 and
  `slot_boot` ×56 in that same window (the fleet spawning ~4-5x/minute). Slot 15 specifically died 7 times between 04:35
  and 05:34 across 4 different tasks, each death preceded by real logged progress (`slot_progress`, real token spend) —
  not an idle/no-op loop, genuine work getting interrupted mid-task.
- **Not memory pressure**: `free -h` showed 21Gi available at the time; no OOM/kill lines in `journalctl -k` for the
  window.
- **Not git-dirty state** (the operator's working hypothesis going in): `classify_dead_worker()`
  (`server/resume_lifecycle.py`) does a LIVE `git status --porcelain` via `check_slot_clean()` — it never reads the
  cached `SlotGitStatusRow` column. Confirmed empirically: slot 15's `resume_decision` alternated `resume`
  (dirty)/`requeue` (clean) across its 7 deaths, ruling out dirty-state as the common factor. (A real, unrelated bug WAS
  found and fixed in that cached column's write path — see "Already fixed" below — but it only feeds the dashboard's
  git-health display, a separate consumer from this respawn path.)
- **Not a DeepSeek rate/concurrency limit**: DeepSeek's documented policy (api-docs.deepseek.com) is concurrency-gated,
  not RPM/TPM — 500 concurrent connections on `deepseek-v4-pro`, 2,500 on `deepseek-v4-flash`. 33 workers sharing 2
  accounts is nowhere near either ceiling, so the "too many workers on too few accounts hit a rate limit" framing (my
  own early hypothesis) does not hold up.
- **The actual death signature is unexplained**: the tmux pane just disappears — `pane_dead_status`/`signal`/`time` are
  all empty in what's captured, tmux itself has no crash diagnostic for this case. Most consistent with DeepSeek-side
  instability or a client-side issue under this account's concurrency, but NOT provable from activity-feed data alone —
  flagged as the leading hypothesis, not a confirmed cause.
- **Flap-detector gap, confirmed empirically**: slot 15's spawn/resume timestamps never landed 3-deep inside any single
  10-minute window (per-slot cadence ~7-15min, just under the trip threshold), and a search of the last 400 fleet-wide
  activity rows for any flap-related event returned zero hits — the per-slot detector is real but was structurally blind
  to a fleet-wide, moderate-per-slot-cadence pattern.

## Already fixed (2026-08-11, same day)

- `agent-orchestrator@a4531e1293` — monotonic guard on `set_slot_git_status()`: the lock-less
  `slot-git-status-report.sh` reporter cron has no cross-process lock and a full sweep (7-10min) exceeds its own 5-min
  cadence, so overlapping invocations could let a slow/stale POST overwrite a fresher clean snapshot with a stale dirty
  one — this was the cause of the SEPARATE "killed slots stuck showing `git: N warn` for hours" dashboard symptom,
  confirmed NOT the cause of this respawn loop (see above).
- `agent-orchestrator@c13f213d02` — new fleet-wide aggregate flap detector in `AutoSpawnLoop._record_attempt`
  (`DEFAULT_FLEET_FLAP_THRESHOLD = 15` attempts fleet-wide within the existing 10-min window) — pages Slack
  (`notify_fleet_autospawn_flap`, a genuine page, unlike the per-slot detector which only logs) and writes an
  `autospawn_fleet_flap_detected` activity-feed row (closing the dashboard-visibility gap the per-slot detector never
  had either). Has its own 1h cooldown so a sustained incident pages once, not on every attempt. This does NOT fix the
  crash-loop's root cause — it makes a recurrence immediately visible instead of silent.
- AO server restarted (operator-authorized 2026-08-11, `sudo systemctl restart orchestrator` via SSM) to deploy the
  above + clear the stuck-session backlog. Confirmed healthy post-restart (`/api/healthz` → `{"status":"ok",...}`). Per
  the operator's own explicit call: this trades "~25 in-flight sessions interrupted immediately" for "clean slate + the
  new detector live" — accepted knowing it likely does not stop a fresh recurrence if the underlying DeepSeek-side cause
  is still present.

## What's still open

- [ ] [INVESTIGATE] P1. **Confirm the actual DeepSeek tmux-session-death mechanism.** Not OOM, not a documented DeepSeek
      rate/concurrency limit (500-2500 concurrent, 33 workers nowhere close). Leading hypothesis: DeepSeek-side
      instability or a client/transport issue specific to this account pair under concurrent load — unproven. Needs
      either DeepSeek-side support engagement (their account dashboard/status page, or a support ticket citing account
      IDs + timestamps) or a client-side repro with verbose transport logging enabled on a deliberately-isolated single
      slot to capture what actually happens at the moment a pane dies (current activity- feed data has no exit signal at
      all). Repo: agent-orchestrator.
- [ ] [OPERATOR] P2. **Decide whether `tuning.deepseek_opus_emergency_fallback` should be turned back off** once
      Anthropic capacity is reliably restored. This flag (turned on 2026-08-05 for a prior Claude-credit-outage posture)
      currently routes opus-tier work to DeepSeek too, not just sonnet-tier — it was not touched by this investigation
      and its current live value was not checked. `select_account_for_spawn` already self-corrects the sonnet-tier
      DeepSeek fraction automatically as Anthropic headroom returns (`_quota_adaptive_fraction` shades the routed
      fraction down as headroom rises, no manual action needed there) — this flag is the one knob that does NOT
      auto-revert and needs an explicit operator call. Repo: agent-orchestrator,
      `server/config.py`/`server/autospawn.py`.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (4 entries).
