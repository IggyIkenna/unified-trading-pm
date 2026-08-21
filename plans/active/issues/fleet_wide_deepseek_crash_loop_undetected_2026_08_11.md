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
last_updated: 2026-08-19 # was 2026-08-11 -- stale vs the 2026-08-19 na-eligibility-audit + live capacity-check entries; corrected (plan_reconciler ao)
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

- [x] [INVESTIGATE] P1. **Confirm the actual DeepSeek tmux-session-death mechanism.** ✅ **ROOT-CAUSED 2026-08-18** —
      not a DeepSeek mechanism at all: the SAME ambient-default-tmux-socket kill-server vulnerability
      `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` root-caused and fixed (4 layers, landed 2026-08-13,
      zero recurrence confirmed 5 days clean). DeepSeek was purely incidental — 100% of the fleet was forced onto 2
      DeepSeek accounts that exact day (the Anthropic-credit-outage this doc opened with), so every death that day
      necessarily showed a DeepSeek `account_id`. Confirmed via clustering analysis of the raw 08-11
      `tmux_session_lost` timestamps (bucketed into 2s windows): the whole burst resolves into ~30 recurring
      mass-simultaneous-death clusters (3-21+ slots dying together every 5-15min) — the identical shape as the
      confirmed kill-server signature, consistent with Layer 1 isolation not existing yet that day. Slot 15's
      "dies alone" framing was independently falsified — all 12 of its deaths that window had 12-28 other slots
      dying in the same ±3s window. What stays unconfirmed: the specific process/command issuing the kill-server
      calls on 08-11 itself (no forensic trail survives that far back) — the mechanism CLASS is what's now answered.
      Evidence: `unified-trading-pm@3d0f6f9798`, full writeup in Progress Log below. Repo: agent-orchestrator.
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
- **sub-agent investigation 2026-08-18 (continued — live-VM diagnostics, read-only SSM)**: dispatched specifically to
  chase the prior same-day static-analysis pass's own "live-VM evidence that would resolve this next" list (that
  entry's own todo #14:30:28 lives in the sibling `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`, per that
  pass's own cross-reference note — investigated jointly again, same as it did). Findings:
  1. **journalctl retention does not reach back far enough — evidence is gone, not merely unchecked.**
     `journalctl -u orchestrator.service`'s earliest retained line is 2026-08-15 14:26:06Z; `-u
     deepseek-native-proxy`'s earliest is 2026-08-16 07:44:53Z (`journalctl --disk-usage`: 4.0G archived+active;
     `journald.conf` has no explicit `MaxRetentionSec`/`MaxUse` — plain systemd rotation under defaults, not a
     deliberate config). Both the 2026-08-11 05:30-05:43Z burst and the 2026-08-13 14:03-14:35Z window (deaths #1/#2)
     predate that boundary by 3-7 days. Any future incident investigated >~3-5 days after the fact will hit the same
     wall on this VM.
  2. **DeepSeek native-proxy wiring — CONFIRMED for both 08-13 deaths, ruled out for the 08-11 burst.**
     `deepseek-native-proxy.service`'s `ActiveEnterTimestamp` is 2026-08-13 11:43:31Z (continuously active since,
     confirmed via `systemctl show`) — rules the proxy out entirely for 2026-08-11 (service didn't exist yet,
     consistent with its first commit 2026-08-12 14:19+01:00). For the two 08-13 deaths:
     `~/.claude-accounts/deepseek-v4-pro.env` (mtime 2026-08-12 19:44:33Z) and `deepseek-v4-flash.env` (mtime
     2026-08-13 00:29:28Z) both already had `ANTHROPIC_BASE_URL=http://127.0.0.1:8767/accounts/<id>` before either
     death — **both accounts were live-wired through the native proxy at both historical death timestamps**,
     resolving the prior pass's explicit "deploy-time fact, not derivable statically" open question. Could NOT
     confirm/refute whether the proxy itself logged anything at either moment — its journal doesn't retain that far
     back (finding 1); this half stays open.
  3. **Both "Death #1" (14:08:21Z) and "Death #2" (14:30:40Z) are the CONFIRMED kill-server-class mass-death
     signature, not an isolated repeat** — direct `state.db activity_log` evidence (mode=ro), not previously
     surfaced this precisely in either doc. Death #1 killed 6 slots simultaneously (1,7,14,15,18,21), every row
     carrying `tmux_server_alive: false, burst_size: 6`. Death #2 killed 5 slots (1,7,14,18,21), same signature,
     `tmux_server_alive: false, burst_size: 5`, 22min later. Neither is a "dies alone, others survive" pattern —
     both fit the already-root-caused whole-shared-server-death mechanism exactly. Each individual slot's
     `account_snapshot` at death time was clean (`account_status: healthy`, `rate_limited_until`/`overage_status`/
     `auth_failed_at` all null) for the specific deepseek-v4-pro/flash account involved, ruling out "that account was
     rate-limited/quota-exhausted" as the trigger for either burst. The exact trigger for these two specific bursts
     is still not identified (tmpfs-disk-cleanup already ruled out for #2 by the prior live session's own journalctl
     check, before retention rolled it off) — what's newly established is that they're two more instances of the
     SAME mechanism, not a separate unexplained class.

     Widening the query: the identical `tmux_server_alive: false` signature appears **256 times** in `activity_log`
     between 2026-08-12 15:00Z (when the per-death diagnostic capture landed) and 2026-08-13 17:13:32Z — roughly
     every 15-90min throughout that ~26h window, hitting DeepSeek (v4-pro/v4-flash) and multiple Anthropic
     sub-accounts (sub-a-ikenna, sub-b-iggy2london, sub-d/e-odum*default) near-interchangeably within the same
     burst — reconfirms the sibling doc's provider-agnostic finding rather than adding a new one. **Zero
     recurrences since**: the last one is id=484055 at 2026-08-13 17:13:32.157973Z, matching the sibling doc's own
     "last actual occurrence... 17:13:27Z" note from its 2026-08-14 00:12Z entry almost to the second. Extending
     that with fresh evidence — **still zero, ~5 days later** (checked this session, 2026-08-18): 1,363 slot-scope
     `tmux_session_lost` rows since 08-13 17:13:32, every one `tmux_server_alive: true` (ordinary isolated/benign
     losses, not the mass-kill signature). Materially stronger durability signal than either doc had before — the
     layered fix (Layers 1-4, all landed by 2026-08-13 20:20Z) looks like it durably closed the mass-kill-server
     VULNERABILITY CLASS, even though the specific trigger for deaths #1/#2 (which both occurred mid-investigation,
     after the "closing verification" claim and before the final two fixes) stays individually unconfirmed.
  4. **Instrumentation status + a new gap found in it.** `account_snapshot`/`host_snapshot`/`tmux_server_alive`
     (`agent-orchestrator@d825c41`, 2026-08-12 15:27:35+01:00) is live and has captured every death since. But
     `context_used_pct` is captured ONLY on the separate context-saturation-triggered requeue path
     (`pre_reset_context_pct`), never inside the `tmux_session_lost` event itself for a kill-server-class death —
     so the prior pass's "does death correlate with a larger request/context size" hypothesis is genuinely
     untestable with what's captured today; a real instrumentation gap, not just an unresolved question. Separately,
     a bulk query for "deaths with an unhealthy `account_snapshot`" over the same window returned 1,300/1,619 —
     almost certainly inflated by stale carried-forward values (e.g. `sub-a-ikenna`'s snapshot kept showing
     `overage_status: rejected` from a 2026-08-12T13:59:59Z event on deaths hours later) rather than a real
     live-at-death-time correlation; not chased further, but flagging since `agent-orchestrator@3e9a224` (2026-08-18,
     same day, unrelated session — "cross-check pane-text heuristic against real recently-probed usage before
     trusting a block mark") touches an adjacent staleness problem in the same area and may be relevant to whoever
     looks at this next.

  **Net**: still no confirmed trigger for death #1/#2 specifically — no smoking gun for "why these two." What
  changed: the native-proxy wiring question is answered (live + wired at both moments, logs unrecoverable), both
  deaths are now correctly characterized as instances of the already-root-caused mass-kill-server class rather than
  a separate mystery, and "is the fix holding" now has much stronger evidence (5 days clean vs. the prior ~4h).
  `[INVESTIGATE]` checkbox left unflipped — that call is for the lead session after review, per dispatch
  instructions. No code changed; read-only SSM only (`check-ao-backlog-status.sh`/`query-ao-state-db-readonly.sh`
  pattern, `state.db` opened `mode=ro`).
- **sub-agent investigation 2026-08-18 (continued, part 3 — ROOT CAUSE FOUND for the original 08-11 mechanism)**:
  asked to push further. Re-examined the raw 2026-08-11 04:00-06:00Z burst directly — no diagnostic instrumentation
  existed that day, so this uses the raw slot-scope `tmux_session_lost` timestamps themselves, independent of the
  `tmux_server_alive`/`account_snapshot` fields the entries above rely on. Bucketed every death into 2-second
  windows and counted distinct slots dying together. Result: **the entire 2-hour window is made of ~30 recurring
  mass-simultaneous-death clusters**, roughly one every 5-15 minutes (04:09, 04:12-13, 04:18-19, 04:35, 04:43-44,
  04:51, 05:07-08, 05:15, 05:22-24, 05:29, 05:34, 05:39, 05:54, 05:58-59...), each killing 3 to 21+ slots within the
  same 2 seconds — the identical shape as the `tmux_server_alive: false` mass-kill-server signature independently
  confirmed above for 08-13, just far more frequent and larger per-burst here. Fully consistent with the sibling
  doc's own timeline: **Layer 1 (the `TMUX_TMPDIR` isolation that stops any bare process from reaching the fleet's
  shared tmux socket) didn't ship until 2026-08-13** — on 08-11 the fleet was still 100% on the ambient default
  socket, maximally exposed the entire time.

  **This falsifies a claim carried in my own entry above (inherited from the static-analysis pass, itself never
  independently checked against the raw data).** Pulled all 12 of slot 15's deaths in this window and checked, for
  each, how many OTHER slots also died within ±3 seconds: **every single one** had a large simultaneous peer group
  (n=12 to n=28 other slots dying in the same instant) — slot 15 was never dying alone. The "Slot 15's separate
  pattern... NOT simultaneous with other slots... stays genuinely unexplained" framing does not survive an actual
  clustering check — it was an unverified assumption, not a measured fact. Slot 15 wasn't special: it just kept
  getting statistically caught by a fleet-wide event recurring every 5-15 minutes, same as every other slot visible
  in each cluster above.

  **Root cause, confidently, for the ORIGINAL 2026-08-11 crash loop — both the mass burst and slot 15's pattern**:
  the SAME ambient-default-tmux-socket kill-server vulnerability the sibling doc
  (`ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`) root-caused and fixed via its 4-layer fix (all landed
  2026-08-13, zero recurrence confirmed 5 days clean per the entry above). **DeepSeek was never causal** — purely
  incidental: 100% of the fleet was forced onto 2 DeepSeek accounts that exact day (the Anthropic-credit-outage this
  doc opened with), so every death that day necessarily showed a DeepSeek `account_id`, which is why the
  investigation understandably chased a DeepSeek-specific mechanism that was never really there. The flap-detector
  gap (already fixed same-day) independently explains why it went undetected regardless of cause. What remains
  genuinely unconfirmed: the specific process(es) issuing the `kill-server`/`tmux` calls against the ambient socket
  on 08-11 itself — unlike the 08-13 catches, no strace/auditd/journalctl evidence survives from that day to name a
  culprit PID. But the mechanism CLASS this doc's own `[INVESTIGATE]` todo asks to confirm ("the actual DeepSeek
  tmux-session-death mechanism") is now answered: it isn't a DeepSeek mechanism at all.

  Checked one more angle before concluding: `checkout_sha` at each slot-15 death cycles through 3 values
  (`6e3d06c`, `62e9be7`, `a4531e1` — the last being this doc's own `a4531e1293` git-health fix landing
  mid-investigation) with clusters continuing under all three, ruling out "one of that day's own deploys caused it"
  and confirming the mechanism predates, and was unaffected by, this doc's own same-day fixes.

  Not flipping `[INVESTIGATE]` unilaterally — evidence is confident enough to recommend closing it, but leaving that
  call to whoever reviews, per the standing instruction on this doc. No code changed; read-only SSM only, same
  `state.db mode=ro` pattern, this time cross-analyzing raw pre-instrumentation timestamps rather than the
  diagnostic fields captured after 08-12.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:ee781ee3c4c9540d]: KEEP-NA, valid — the original P1 INVESTIGATE todo is already closed (root-caused 2026-08-18, same ambient-tmux-socket kill-server mechanism as the sibling doc, DeepSeek incidental, 5+ days zero recurrence). Sole remaining open item is an explicit [OPERATOR]-tagged tuning-flag revert decision with no decision on record. Converges with the 2026-08-17 na-eligibility-audit verdict (updated for the since-closed investigation item).
- **2026-08-19 (interactive session, live check via SSM against `i-0c9b283b31d6b5ca7`)**: pulled `GET /api/accounts`
  filtered to every `sub-*`/`provider:anthropic` account (8 total). **Capacity has NOT recovered** —
  `sub-a-ikenna`/`sub-c..f-*` all `rate_limited` with `rate_limited_until` spanning 2026-08-19T13:59Z through
  2026-08-21T18:59Z; `sub-b-iggy2london`/`sub-g-alpavolt` `high_usage`; every one of the 8 carries
  `overage_status: "rejected"`. **Decision (trust-mode, operator's "apply your recommendation" ruling): keep
  `tuning.deepseek_opus_emergency_fallback` ON — do not revert.** Reverting now would route opus-tier work back onto
  accounts that are still rejected/rate-limited fleet-wide, recreating the exact starvation this flag exists to
  avoid. Re-check trigger (unchanged from the todo's own framing): once every `sub-*` account shows
  `overage_status` other than `rejected` for a sustained period, this is safe to revert — not yet met. Todo stays
  open (this is a status check-in against a still-unmet condition, not a final answer).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries), unchanged.
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — sole remaining item is an explicit [OPERATOR]-tagged tuning-flag revert decision; per the 2026-08-19 live check, Anthropic capacity had still not recovered (every `sub-*` account still `overage_status: rejected`), so the revert condition remains unmet. Converges with the 2026-08-19 verdict.
