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
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch19_2026_08_10.md,
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
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:9534953f4daf58bc]: KEEP-NA, valid — 2 open items are an unresolved investigation into the actual DeepSeek-side crash mechanism (possibly needing vendor engagement) and an explicit operator decision on reverting a tuning flag; neither bounded/deterministic.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries), unchanged.
- **sub-agent investigation 2026-08-18 (INVESTIGATE P1 — confirm the DeepSeek tmux-session-death mechanism)**:
  static-analysis-only pass over `server/worker_liveness_watchdog.py`, `server/tmux_spawn.py`, `server/tmux_pruner.py`,
  `server/tmux_session_loss_rate_canary.py` + their tests, per dispatch instructions to not ship code without a
  confirmed cause. **Doc cross-reference correction first**: the dispatch brief quoted this doc's open todo as
  `[INVESTIGATE] P1. Root-cause death #2 (14:30:28) — NOT explained by tmpfs-disk-cleanup...` — that exact todo and
  timestamp actually live in the sibling `/plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
  (its own todo list), not in this doc, whose own open INVESTIGATE item carries no timestamp. Flagging so a future
  reader searching THIS doc for "14:30:28" doesn't come up empty — investigated both together since they're clearly
  related (this doc is even cited in that one's own evidence for "account_snapshot" instrumentation).

  **Ruled out, with reasoning (not readback)**:
  - The DeepSeek 1M-context-window fix (`agent-orchestrator@ac9ba18`, 2026-08-10,
    `server/tmux_spawn.py::_DEEPSEEK_CONTEXT_WINDOW_EXPORT` + `server/model_tier.py::_CONTEXT_WINDOW_DEEPSEEK`) as a
    NEW crash-inducing regression. Its 1,048,565-token ceiling was measured directly against the raw DeepSeek API
    (laddered oversized POSTs, not inferred from CLI transcripts — archived
    `ao_deepseek_context_window_unknown_and_self_repoisoning_2026_08_10.md`), AO's export (1,000,000) stays 4.5% under
    it, and I found no path in `_start_session`'s spawn-command construction where a session's real request size could
    silently exceed `CLAUDE_CODE_MAX_CONTEXT_TOKENS` before the CLI's own auto-compact fires. (One adjacent,
    NOT-ruled-out consequence below.)
  - The DeepSeek native-usage-capture proxy (`server/deepseek_native_proxy_server.py`, outside this task's file
    cluster but directly relevant — a standalone process DeepSeek `claude` CLI workers can be routed through via
    `ANTHROPIC_BASE_URL`). Its own docstring documents a dev-time bug where an earlier revision buffered a whole
    stream before responding (pane-silent long enough to trip the spawn-heartbeat watchdog into a mid-turn respawn) —
    but that bug was caught and fixed BEFORE the proxy's first commit (`8523248`, 2026-08-12 14:19:01+01:00), which
    postdates the 2026-08-11 05:30-05:43 crash-loop burst by over a day. Cannot explain that incident. Could have been
    live by death #2 (2026-08-13 14:30:28) — see open questions below.
  - tmpfs-disk-cleanup and the confirmed kill-server/ambient-socket mechanism as death #2's cause — both already
    ruled out in the sibling doc with direct evidence (zero `tmpfs-disk-cleanup` runs 14:25-14:35Z; Layers 1+2 were
    live + every session force-recycled onto them by ~13:10Z, over an hour before 14:30:28). Re-verified the sibling
    doc's own timeline is internally consistent rather than re-deriving it.

  **Remains plausible, unconfirmed**:
  - The 2026-08-11 burst conflates two DISTINCT signatures: (a) the ~13-min, ~55-attempt, nearly-every-slot mass burst
    matches the confirmed kill-server signature exactly (one shared-tmux-SERVER death takes every pane on the socket
    with it), and that vulnerability was live + unfixed at the time — plausibly explains the bulk of it with DeepSeek
    incidental (100% of the fleet just happened to be on 2 DeepSeek accounts when it fired), not causal. (b) Slot 15's
    separate pattern — 7 deaths in one hour, ~7-15min apart, NOT simultaneous with other slots — does not fit that
    signature (kill-server takes the whole shared socket at once; it would not selectively re-kill one slot 7x while
    32 others survive). This half stays genuinely unexplained by anything either doc has confirmed.
  - Whether the DeepSeek native proxy was actually WIRED UP (an account's env file pointed `ANTHROPIC_BASE_URL` at it,
    not just present in the codebase) by 2026-08-13 14:30:28 is a deploy-time fact, not derivable from a static read —
    the proxy's own docstring is explicit that shipping the code and flipping the wire-up are separate steps.
  - Unverified consequence of the 08-10 context-window fix: it changed DeepSeek's runtime PROFILE, not just its
    compaction threshold — sessions that used to compact at ~200K now legitimately run toward the real ~1M ceiling
    first, so each request DeepSeek's provider serves keeps growing far larger than before (DeepSeek's own usage shape
    is ~99.4% cache-read tokens per the archived doc's measurement). Neither investigation has checked whether death
    likelihood correlates with request/context size specifically for DeepSeek — worth testing since it's a genuine
    behavior change landing one day before the crash loop first appeared.

  **Live-VM evidence that would resolve this next** (none derivable statically):
  1. Slot 15's repeat pattern: pull `context_used_pct`/`account_snapshot` (now captured on every `tmux_session_lost`
     via `server/tmux_pruner.py`'s death snapshot, landed after 2026-08-11 so not retroactively available for that
     incident but live going forward) for the next DeepSeek-account death and check whether it died at a large
     context size — a real correlation would support the "bigger requests since 08-10" hypothesis.
  2. Any future unexplained DeepSeek death: `journalctl -u deepseek-native-proxy` (unit:
     `scripts/deepseek-native-proxy.service`) for the exact window — a crash/restart/mid-stream-failure log line there
     would directly implicate the proxy; silence would rule it out.
  3. Confirm via the live account env files (`~/.claude-accounts/<deepseek-account-id>.env`, `ANTHROPIC_BASE_URL`)
     whether DeepSeek accounts were actually routed through the native proxy at each historical death timestamp of
     interest — a deploy fact the code alone can't prove.
  4. A deliberate isolated-sandbox repro (the sibling doc's own pattern,
     `/codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md`) driving one DeepSeek session's context up near
     the ~1M ceiling under concurrent load on a shared 2-account pool, watching for the death signature — the most
     direct test of the "large-request stress" hypothesis without waiting for a live recurrence.

  No code changed this pass — could not confidently root-cause death #2 or slot 15's repeat pattern from static
  analysis alone; not guessing-and-shipping. `[INVESTIGATE]` checkbox left unflipped per dispatch instructions.
