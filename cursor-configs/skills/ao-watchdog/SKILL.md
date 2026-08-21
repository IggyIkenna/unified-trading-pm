---
name: ao-watchdog
description: >-
  General-purpose daily health check + auto-fix for the agent-orchestrator fleet — the roll-up skill that ties
  together everything this workspace already has for checking AO health (fleet-efficiency KPIs, scheduled-job
  status, the escalation queue, blocked questions, git/context/disk canaries, VM resource usage, Slack alert
  quality) into one pass, and does not stop at reporting: it scans `plans/active/issues/` + `plans/archive/issues/`
  for prior understanding of each finding BEFORE acting (so a regression of an already-"RESOLVED" issue is
  recognized as a regression, not re-diagnosed from scratch), fixes what's small/clear at the root, updates any
  stale-but-still-cited issue doc to current reality, and drives open `BLOCKED` questions to an answer in the
  live interactive chat rather than just listing them. Leads every report with a day-over-day diff (yesterday vs
  the day before, across KPIs/escalations/blocked-questions/resources/Slack volume/scheduled-job health) and a
  best-effort flag of any significant architecture/design decisions made that day. Not a replacement for `/ci-reconcile`,
  `/escalation-queue-reconcile`, `/vm-preemption-billing-waste-audit`, `/vm-resource-rightsizing-check`, or
  `/data-pipeline-alerts-reconcile` — this skill's own checks stay cheap and hand off to those for their deep-dive
  domain the moment an anomaly is confirmed. Designed to run interactively (laptop, any slot) or as an
  AO-dispatched scheduled worker once a systemd timer is installed for it (not yet installed as of this skill's
  creation — see "Scheduling this skill" below). Trigger on `/ao-watchdog`, "check AO health", "how's the fleet
  doing", "run the AO watchdog", "daily AO check", "audit the orchestrator", "is anything broken in the fleet",
  "go through the blocked questions", "check fleet efficiency / cost / KPIs".
---

# /ao-watchdog — daily AO fleet health check + auto-fix

**What this is not**: a fifth reconcile skill duplicating `/ci-reconcile` / `/escalation-queue-reconcile` /
`/vm-preemption-billing-waste-audit` / `/vm-resource-rightsizing-check` / `/data-pipeline-alerts-reconcile`. Those
four own their domain's deep-dive. This skill is the **cheap, wide, daily sweep** across everything the operator
actually watches — is the fleet busy or thrashing, is anything costing more than it should, are blocked questions
piling up, is a Slack alert noisy or silent when it shouldn't be, is the VM starved or wasting resources — and it
**hands off** to the narrower skill the moment a finding falls in that skill's domain, rather than re-implementing
the deep dive here. Composes `/check-agent-orchestrator` (Step 1), `/escalation-queue-reconcile` (Step 4),
`/vm-preemption-billing-waste-audit` and `/vm-resource-rightsizing-check` (Step 3f) by reference, not duplication.

**This file is a living document.** Every run that finds a gap this skill's steps didn't already cover — a new
alert shape, a KPI nobody was tracking, a blocked-question pattern with no good answer path — gets folded back
into this file in the same session (a `- [ ]` todo isn't enough here; the point of a watchdog skill is that next
time it already knows). See "Folding findings back in" at the end.

## Step 0 — pre-task plan/issue conflict check + read what's already known

Before touching anything live, this is a workspace-wide HARD RULE (`/codex/12-agent-workflow/pre-task-plan-conflict-check.md`)
and it matters MORE here than usual: an AO-health finding almost always has prior art.

```bash
rg -l "branch-state quarantine|FM5|FM7|autospawn failed|scheduled.job|fleet.kpi|fleet efficiency|blocked question" \
  plans/active/ plans/active/issues/ plans/archive/issues/ plans/archive/2026_0[6-8]/ -i
```

Read (don't just grep-and-move-on) any hit that shares a symptom shape with what you're about to investigate —
this is what turns "found the same bug again" into "confirmed regression of `<issue-doc>`'s fix" instead of a
fresh, context-free re-diagnosis. The known recurring classes as of this skill's creation (2026-08-17), so you
recognize them on sight instead of re-deriving them:

- **`branch-state quarantine (FM5/FM7)` autospawn failures** — `plans/archive/issues/ao_scheduled_job_branch_quarantine_friction_2026_07_28.md`
  fixed the SCHEDULED-JOB-DISPATCH-FAMILY-SCOPED case (300s recency guard + different-slot retry). A storm hitting
  ordinary worker/escalation spawns (not scheduled jobs) across many slots is a **different, unfixed surface** —
  don't assume the 07-28 fix covers it. Read `agent-orchestrator/server/worktree_clean_check/_realign_guard.py` and
  `autospawn.py`'s `heal_dead_slot_branch_quarantine` for the general (non-scheduled-job) path before concluding
  anything.
- **`reaped-stale` scheduled-job runs** — `dispatched` ≠ `done`; join `ScheduledJobRunRow` to `AgentRow.agent_exit_reason`.
- **`no_capacity` on a scheduled dispatch is legacy** — only reachable when the caller omits `job_name`; a modern
  caller queues instead (`ScheduledJobQueueRow`), so `no_capacity` showing up on a `job_name`-bearing dispatch is
  itself a regression, not normal backpressure.
- **A 503 body containing "quarantine" but NOT matching `BENIGN_503_RE`** (`no free configured slot|no headroom|
protected_live_peer|is paused by operator`) is a real spawn failure, never benign — the allowlist is deliberate
  (see `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § "503-classification allowlist").

Also skim the last digest / today's Slack pull (Step 1 below produces this) before diagnosing anything — a finding
that's already mid-fix in another slot's session is not yours to re-open.

## Step 1 — the cheap live snapshot (one aggregated pass, minimize round trips)

Batch independent tool calls-tool-call-batching HARD RULE applies doubly hard here: this step alone can be 6+
separate lookups if done naively. Do them as few round trips as possible.

**If you're running ON the orchestrator VM** (a dispatched scheduled-job worker — `curl -s -m 5 localhost:8765/api/mode`
succeeds): every call below is a plain `curl localhost:8765/...`, no SSM.

**If you're checking remotely** (interactive laptop session, any slot): use the same AWS SSM `send-command` pattern
as `/check-agent-orchestrator` and `check-scheduled-job-health.sh` (`aws ssm send-command` against
`i-0c9b283b31d6b5ca7`, `ap-northeast-1`, `AWS-RunShellScript`) — and **aggregate ON the VM in one remote script**,
not one SSM round trip per endpoint (SSM `StandardOutputContent` truncates at ~24000 chars, and every extra round
trip is a full `send-command`/`get-command-invocation` pair). Pull all of the following in one remote Python
heredoc (mirror `check-scheduled-job-health.sh`'s pattern exactly — it already solves the truncation problem).
**Measured trap (2026-08-18 run): building one big dict and `json.dumps`-ing it at the end silently truncates
mid-object when the total crosses ~24000 chars — the raw `/api/backlog` task list and `/api/fleet-kpis`'s
`usage.entries` are the two fields most likely to blow the budget.** Stream one `KEY\tjson.dumps(val)` line per
field instead (`print(key + "\t" + json.dumps(val))`, called right after each fetch, not batched into one final
print) — a truncation then only loses the last (possibly partial) field's line, every prior field parses cleanly,
and you can tell from `cut -f1` which field survived. Summarize list-shaped fields (status `Counter`, not the raw
list) before emitting them for the same reason. If the health cluster (fleet-kpis/escalations/blocked/accounts/
agents/resource-watchdog/batching/state) and the resource cluster (point-in-time snapshot + the Step 10 resource-
history day-diff) still don't fit one command's budget together, split them into two SSM round trips rather than
fighting for space in one — two clean pulls beat one truncated one.

1. `GET /api/backlog` summary (queued/dispatched/done counts) — same view `/check-agent-orchestrator` reads.
2. `GET /api/fleet-kpis` — the full KPI payload (see Step 3a).
3. `GET /api/escalations/active` — the same cheap check `/escalation-queue-reconcile` Step 1 uses.
4. `GET /api/blocked/stats` (telemetry rollup) + `GET /api/state`'s `blocked_queue` field (the unanswered-only
   list, `server/routes/state.py` — there is no separate `GET /api/blocked` list route) (see Step 6).
5. `bash agent-orchestrator/scripts/orchestrator/check-scheduled-job-health.sh runs 2` and `... agents` (Step 5).
6. On the VM shell: `uptime`, `free -h`, `df -h /`, `ps aux --sort=-%cpu | head -15` (Step 3f resource check).

A genuinely healthy fleet (empty/aging-normally escalations, no stale-past-24h `queued` scheduled-job rows, no
`unresolved`/`quarantined`/`timeout`/`error` scheduled-job statuses, disk/CPU/mem nowhere near the canary
thresholds, zero or only-fresh blocked questions) means **Steps 2-9 stay cheap** — confirm each briefly and move
on. This mirrors `/escalation-queue-reconcile`'s "Step 1 only, on a healthy queue" contract: don't manufacture
depth where there's nothing to find.

## Step 2 — the dashboard's "Multiple issues — eyes on this" panel, and the day's alert shapes

This is the operator's own daily entry point, so treat it as a checklist, not a vibe. The panel is real code, not
a vague dashboard vibe — `agent-orchestrator/dashboard/src/layout.tsx`, fed by TWO independent aggregators, and
**`GET /api/state` alone is NOT enough data to reproduce it**:

- **`summarise(state: StateResponse)`** (`layout.tsx` ~L393-498) — fleet-only health straight from `GET /api/state`'s
  `slots[]`: stale/blocked/idle/paused counts, high-context (≥80%) slots, thrashing, pending-blocked count,
  `parkedCount` (`backlog_summary.auto_parked`), `watchdogDormant`, `tmuxServerDown`, `recentOrphanReapCount` — all
  top-level fields on `StateResponse` (`server/models/state_views.py`), alongside `blocked_queue[]` and
  `git_red_sustain_secs`.
- **`criticalHealth(accounts, agents, escalations, scheduledJobRuns, slots, backlog)`** (`layout.tsx` ~L579-647) —
  cross-endpoint: account exhaustion (`GET /api/accounts`), persistent-role liveness (`GET /api/agents`, see 3f
  below), worker-fleet-fully-idle-with-work-queued, blocked scheduled jobs, failed escalations
  (`GET /api/escalations`), claimable-vs-queued backlog mismatch. The crit label render is `layout.tsx` ~L1080.

So reproducing this panel's own verdict needs `/api/state` + `/api/accounts` + `/api/agents` + `/api/escalations` +
scheduled-job runs pulled together — pull all five in the Step 1 aggregated snapshot, not just `/api/state` alone.
`criticalHealth`'s crit thresholds (e.g. `stale≥2`, `pendingBlocked≥3`, `watchdogDormant` true, `tmuxServerDown`
true) are the actual bar for "eyes on this" — match against those, don't invent your own severity cutoffs.

Neither aggregator groups repeat-shape failures across slots by itself (e.g. a dozen near-identical "autospawn
failed" events don't automatically collapse into one row) — **you** do that grouping in Step 2's own triage below,
same as the FM5/FM7 storm class: read the raw counts the panel surfaces, but group by error SHAPE yourself before
deciding how many findings you actually have.

For each item the panel surfaces:

1. **Group by error shape first, not by slot.** `{"'healed': False, 'liveness': ..., 'detail': 'still-quarantined-after-heal'}"`
   repeated across slots 1, 4, 5, 8… is ONE finding (one root cause, N symptoms), not N findings.
2. **Cross-reference Step 0's known-issue scan.** Does this shape match a "RESOLVED" issue doc? If yes, this is a
   **regression of that fix** — the doc's `🟢 RESOLVED` banner is now wrong and misleads the next reader (workspace
   HARD RULE: "a doc/comment/pointer that MISLED you is a finding — fix it in the same turn"). Update that doc's
   status honestly (a new dated section explaining the regression, not silently editing the old resolution away)
   rather than opening a fresh doc that leaves the stale banner standing.
3. **Check whether the item SHOULD have deduped per the alerting SSOT** (`/codex/04-architecture/agent-orchestrator-alerting.md`)
   but didn't — e.g. `notify_spawn_failed` is documented as summary-only/no-page, so if a spawn-failure storm
   genuinely paged Slack repeatedly, that's itself a finding (see Step 9).

## Step 3 — KPIs: is the fleet busy, efficient, and affordable?

### 3a. Fleet efficiency (boots / dispatches / done / conversion / regression)

`GET /api/fleet-kpis` (`server/fleet_kpis.py::compute_fleet_efficiency_kpis`) is the SSOT — never hand-roll a
recount from `activity_log`. Fields and what they mean:

- **`boots`** (`slot_boot` events), **`dispatches`** (`task_dispatched`), **`done`** (`slot_done`) — NOT
  `autospawn_succeeded`/`slot_spawned` (those are the boot's own upstream trigger and double-count if substituted).
- **`conversion_pct`** — done/dispatches. Low conversion with high boots is the "fleet looks busy, work doesn't
  land" pattern this exact KPI was built to catch (`plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md`
  — the plan that built this found conversion at ~20% before the fix).
- **`boots_per_done`**, **`boots_to_dispatch_ratio`** — division-by-zero-safe (`None`, never a misleading 0/∞); a
  `None` ratio in a report means "say so," never round to 0.
- **`regression_alert`** — `detect_sharp_regression` fires at ≥5x day-over-day (`TuningDefaults.fleet_kpi_regression_multiple`).
  A populated `regression_alert` field is itself the day's headline finding — lead the report with it, don't bury
  it under routine KPI numbers.
- **`usage_by_account`** — transcript-file-size proxy per account (the operator's own lightweight-option ruling;
  not a token count). See 3d below for turning this into a $ estimate — with the caveat that matters.

### 3b. "How busy is the fleet" — dispatched vs idle slot count

`GET /api/backlog` / `/api/state`'s per-slot view gives live `dispatched`/`idle`/`quarantined` counts directly —
don't derive busyness from the KPI ratios above, they measure conversion, not occupancy. Report both: occupancy
(what fraction of slots are doing something right now) and conversion (of what they did, how much actually
finished) — a fleet can be 100% occupied and 20% converting, and that's a worse state than 50%/80%.

### 3c. Batch tool-call efficiency — a real, live metric; read it, don't re-derive it

This is measured, not a gap. `server/batching_stats.py::scan_turns_from_file` scans agent transcripts turn-by-turn
for `tool_calls`/`bash_calls`/`bash_chained_segments`; `server/batching_stats_poller.py`'s `BatchingStatsPoller`
upserts the results into `BatchingTurnRow` on a tick. `GET /api/backlog/batching-stats/windows` returns rolling
`multi_tool_turn_pct` over 1h/5h/24h/7d/lifetime windows — this is the SAME number the dashboard's
`BatchingEfficiencyPanel.tsx` renders. **Pull this endpoint directly; never sample transcripts yourself to
estimate batching compliance** — that would silently duplicate a metric that already exists and drift from the
dashboard's own number. Report the 24h window as the headline figure (matches this skill's own daily cadence),
with the 7d/lifetime windows as trend context. A falling `multi_tool_turn_pct` trend across windows is itself a
finding worth a line in the report, even with no single anomalous value.

### 3d. Cost per task — real per-slot $ tracking exists; read the measured subscription multiplier, don't invent one

Cost tracking is more developed than a transcript-bytes guess. `SlotView` (`server/models/slots.py`) carries
**`current_task_spend_usd`** and **`session_spend_usd`** per slot, priced against `server/model_pricing.py`'s
date-effective LIST-price table (its own docstring is explicit: "what tokens were worth at list, never what we
paid"). Read these fields directly from `/api/state`'s `slots[]` (already pulled in Step 1) rather than
reconstructing a $ figure from `usage_by_account`'s transcript-byte proxy (3a) — the byte proxy is a fallback for
when per-slot spend isn't available, not the primary source now that it is.

**The subscription-vs-list-price gap is ALSO already measured, live — don't apply a fixed multiplier from memory.**
`server/subscription_value.py`'s `MeasuredValue.multiplier = list_price_usd / subscription_cost_usd` computes the
real ratio from actual usage; its own module docstring states list price "does NOT" reflect real spend, and the
last calibration on record (2026-08-10, a 4h25m window) measured **~190x** — read this module's current live
value at run time, don't hardcode 190x here either, it's a measured-not-fixed number that will keep moving.
**Correction (2026-08-20, live run):** there is currently no continuously-updated STORED value to read —
`scripts/orchestrator/calibrate_account_value.py` is read-only/print-to-log only and persists nothing, so "read
the live value" in practice today means re-reading the 2026-08-10-dated docstring constant, not a fresh
measurement. Say so explicitly when reporting this figure, and treat persisting calibration runs somewhere
queryable as an open follow-up rather than assuming freshness.

**Do not conflate this with the separate ~20x figure in `unified-trading-pm/codex/11-project-management/
cloud-spend-forecast-and-credits-2026-08.md`** — that doc's "~20x gap … IS the credit ask" is a different,
blended FORECAST construct (folds in a max-tier rate-limit discount + a negotiated discount), not
`subscription_value.py`'s live-measured ratio. If both numbers come up in the same report, name which is which
explicitly — do not average them or present one as confirming the other.

**Report shape**: lead with the real per-slot/per-account `*_spend_usd` figures (list-price-equivalent, from
`model_pricing.py`) as the primary number, then divide by `subscription_value.py`'s current measured multiplier
to state the estimated real cost, explicitly labeled as an estimate derived from a measured ratio (not a
guess) — never present the raw list-price figure alone as "what this cost."

### 3e. Retry accounting

`boots_to_dispatch_ratio` (3a) **is** the retry-accounting signal — a ratio far from ~1:1 means the fleet is
booting many more times than it's landing dispatches, i.e. retrying/respawning. Cross-reference against
`autospawn_flap` / `worker_kicked` / `worker_kick_failed` activity-log counts (from the daily digest glossary,
`/codex/04-architecture/agent-orchestrator-alerting.md` § "Digest event glossary") for the qualitative retry
picture the ratio alone doesn't show — a high ratio from many small flaps reads differently than one from a few
big respawn storms.

### 3f. Review-agent-down / main-agent-down + resource usage/burst

- **Main/review agent liveness**: this IS measured, and it's the same signal Step 2's `criticalHealth()` reads —
  `layout.tsx`'s `PERSISTENT_KINDS = [{kind:"orchestrator", label:"Orchestrator (main) agent"}, {kind:"review",
label:"Review agents"}]`; `blockedRoles` (any kind with zero `GET /api/agents` rows where `agent_kind===kind &&
online`) forces the dashboard to `level="crit"`. Read that directly rather than re-deriving liveness from
  `GET /api/agents` yourself. **Gap worth naming**: there is no DEDICATED Slack notifier for "review agent down"
  specifically (only `notify_main_agent_rate_limited` for main) — review-liveness paging exists ONLY via this
  dashboard crit signal, so if nobody is looking at the dashboard, a dead review agent has no Slack page at all.
  That asymmetry is itself a Step-9 alerting-hardening finding, not something to quietly work around here.
  `main_agent_keeper.py`'s `AgentKeeper` is what respawns both roles — `autospawn.ensure_review_agents` for
  review — so a `blockedRoles` crit that persists past one respawn cycle is a real finding, not transient churn.
  The two context-safety-net canaries (`context_saturation_detected`, `context_activity_silence_detected`, per
  the alerting SSOT's "Self-monitoring detector registry") are the complementary check — confirm neither has
  silently stopped firing (recent activity-log rows for these event types, cited test suites still exist).
- **A large `accounts_summary.disabled` count is not automatically a finding — check WHICH accounts first.**
  Operator-confirmed 2026-08-18: the non-Anthropic diversity-pool accounts (DeepSeek/Gemini/GLM/Grok/Kimi/Nvidia
  variants) being disabled right now is largely EXPECTED, mid-onboarding/testing under active plans:
  `deepseek_claude_blended_provider_routing_2026_07_28.md`, `grok_gemini_translation_proxy_2026_08_14.md`,
  `codex_luna_flex_bridge_2026_08_14.md`, `kimi_gemma_provider_onboarding_2026_08_16.md`. Cross-reference a
  disabled account's provider against these plans before flagging it — only a disabled ANTHROPIC `sub-*` account,
  or a non-Anthropic account disabled for a reason NOT explained by one of these plans, is a real finding worth
  surfacing. Pull `overage_disabled_reason` (not `disabled_reason` — a wrong field name this skill's first live
  run queried and got nulls back) for the actual cause per account.
- **Resource usage/burst — this is a REAL, live-traceable subsystem, not a gap.** Two mechanisms already exist,
  separate from the Canary family (`DiskSpaceCanary` etc. in `server/*.py`) — this is what "resource issues are
  now fully traceable" refers to: (1) **`resource-watchdog.service`** (PM repo, `scripts/infra/resource-watchdog/`)
  polls every 10s and SIGKILLs non-allowlisted processes over RSS/CPU/swap thresholds —
  `POST /api/resource-watchdog/kill`, `GET /api/resource-watchdog/status`, dashboard `ResourceWatchdog.tsx`,
  documented `/codex/05-infrastructure/agent-orchestrator-api-host.md` (built from the 2026-08-05 OOM incident:
  two 26-27GB runaway processes). **Read `GET /api/resource-watchdog/status` for recent kills** — a kill in the
  last 24h is a real finding (name the process + slot + RSS that triggered it), not silently absorbed cleanup.
  (2) **`ResourceHistoryLoop`** (`server/resource_history.py`, standalone `resource-history-sampler.service`)
  samples `host_resources.py::snapshot()` (cpu%, iowait%, load avg, ram/swap/disk %, cgroup mem) every 5s to a
  **per-day JSONL file** at `config.resource_history_dir()/<date>.jsonl` (`STATE_DIR/resource_history/`, live —
  `resource_history.py:202-206`; **confirmed live path (2026-08-20)**:
  `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/resource_history/<date>.jsonl` — use
  this directly over SSM rather than a blind `find /` sweep, which timed out at the default 20s on the first live
  run), mirrored to GCS/S3 via the separate `resource-history-backup.timer` +
  `resource_history_backup_once.py`. **Correction (2026-08-18, this skill previously said BigQuery here — verified
  wrong):** this JSONL log is NOT the same system as BigQuery `deployment_operational_data.resource_samples` — that
  table is written via Pub/Sub from deployment-service's `HeartbeatDaemon` and is scoped to
  deployment-service-launched VMs only (backfill/launcher fleet), not the orchestrator host itself
  (`deployment-observability.md` §§ 625-652). For "was the ORCHESTRATOR under sustained load over the last N
  hours," read its own per-day JSONL (`cat`/tail via SSM, see Step 10 below) — there is no BigQuery table for this
  host. For a launcher/backfill VM's sustained-load history, `GET /api/vm-resources/rolling` or the BigQuery table
  is the right source instead. Either way this beats a single point-in-time `uptime`/`free -h` snapshot, which only
  shows the instant you happened to look.
  Still pull the point-in-time snapshot too (`uptime`, `free -h`, `df -h /`, `ps aux --sort=-%cpu | head -15`) as
  the cheap Step-1 check — cross-check against `DiskSpaceCanary`'s `tuning.disk_space_min_free_gb` (default 60G)
  and flag **swap in active use** (any non-zero swap on a VM that shouldn't be swapping is worth a line even
  without a canary firing) alongside a high load average relative to core count. If a VM other than the central
  orchestrator is involved (a backfill/launcher VM), hand off to `/vm-resource-rightsizing-check` rather than
  re-deriving its CPU/mem-growth analysis here.
- **"Are we using all the resources or wasting them"**: this is exactly `/vm-preemption-billing-waste-audit`'s
  remit (preempted-without-recovery, non-retriable shards re-attempted every wave) — run it (or note it's due) as
  part of this sweep rather than re-implementing its checks inline.

### 3g. Diverged/dirty idle-slot reconciliation (operator policy, 2026-08-17)

A slot sitting RED for hours (`notify_git_staleness_red`'s 90-min-sustain / 4h-re-remind pages) is not acceptable
to wave off as "it's just idle" — **idle does not excuse divergence**. "Idle" only changes WHO should fix it and
HOW, never WHETHER. The operator's standing policy for every slot the git-staleness pager names:

1. **Check idle vs live first** (same liveness check as everywhere else in this workspace — a fresh heartbeat,
   `worker_alive`/`tmux_alive`, an in-flight dispatched task). A LIVE slot's own worker should reconcile its own
   tree in the course of its normal work — don't touch it out of band. An IDLE slot needs an outside actor to fix
   it, since nothing there will do it on its own.
2. **For an idle diverged/dirty slot, the fixing agent gathers the slot's PREVIOUS task context before touching
   anything** — read that slot's last `current_task`/`plan_ref` (or the AO activity log for that slot around when
   it went idle) so the divergence is understood in light of what that slot was actually doing, not blind-reset
   by an agent with zero context on why the tree looks the way it does. This is exactly the review-agent's normal
   job (context-aware reconciliation), just triggered by a staleness page instead of a `/done` claim.
3. **Classify what's actually diverged/dirty, per item, before choosing a remediation path** — "diverged" (ahead/
   behind the remote branch pointer) and "dirty" (uncommitted local file changes) are different failure shapes
   that both render as RED in the fleet-git panel; don't apply one fix to both:
   - **Untracked files that should never have been tracked/warned on** (build artifacts, scratch output, logs) →
     add them to `.gitignore` — this is the CORRECT fix and legitimately silences the warning going forward; it
     is not "hiding" the problem, it's fixing a genuine false-positive.
   - **Ahead-commits or dirty content that's real, intended work** → sync it in canonical form: `safe-doc-push.sh`
     for a docs/plans-only change, `quickmerge.sh --agent --files '<paths>'` for code — the SAME two-pass
     discipline every other skill in this workspace already uses, never a raw push.
   - **Ahead-commits that are ALREADY safely preserved elsewhere** (the FM5/FM7 auto-heal's own
     `wip-preserve/orchestrator-slot-<N>-<repo>-diverged-<ts>` ref is exactly this case — confirmed present via
     `git ls-remote origin 'refs/heads/wip-preserve/orchestrator-slot-<N>-*'`) → the local branch just needs a
     safe realign back to origin (`git fetch` then a **fast-forward-only** reset to `origin/<branch>`, verified
     via `git merge-base --is-ancestor <local-head> <preserve-ref>` first so you're certain the content genuinely
     survives elsewhere before discarding the local pointer) — never a blind `git reset --hard`/`clean -fd`
     without that verification, per this workspace's own git-safety rules.
4. **A fleet-wide storm of identical `ahead=N behind=M` across many slots for the SAME repo** (the exact shape
   the operator flagged live: `unified-trading-ci` sitting `DIVERGED ahead=3 behind=1` on slots 3/10/19/20+
   simultaneously) is a single root cause wearing many slot numbers — diagnose ONE of them fully (which almost
   always ties back to whatever auto-heal/realign mechanism touched that repo fleet-wide, e.g. this session's own
   FM5/FM7 branch-quarantine incident), then apply the same verified remediation to every other slot showing the
   identical shape, rather than re-diagnosing each slot from scratch. Confirm the underlying auto-heal bug itself
   is fixed (Step 8) BEFORE reconciling the individual stuck slots — otherwise the same storm re-diverges them
   within the hour.
5. **Report which path each slot took** (gitignored / synced-via-safe-doc-push / synced-via-quickmerge /
   fast-forward-realigned-to-a-preserve-ref / left live for its own worker) — this is exactly the kind of
   per-slot audit trail that keeps a future run from re-litigating a slot that's already clean.

## Step 4 — escalations: defer to the narrow skill

Run `/escalation-queue-reconcile`'s Step 1 cheap check (`GET /api/escalations/active`, same endpoint) inline here
— it's already cheap-first by design. **Only if it finds a genuine anomaly** (an `unresolved` row, a row past its
45-min deadline judged correctly by `dispatched_at`/`resolved_at` not `created_at` per that skill's own
re-escalation-aware rules), hand off to `/escalation-queue-reconcile` proper for the Step 2+ root-cause — don't
duplicate its diagnosis ladder here.

**A `last_error: "no free configured slot to dispatch escalation onto"` is NOT automatically account exhaustion —
check whether the reserve slots themselves are paused first** (confirmed root cause, 2026-08-18 live incident,
`ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`): the CI-escalation reserve is the top-3 non-review,
non-human, non-main slot ids (`config.ci_escalation_reserved_slot_ids`) — **when computing this set yourself,
exclude `config.human_slot_ids()` (default `{9001, 9002}`)**, a first pass that skipped this wrongly swept a human
operator's own slot into the guessed reserve. Pull those 3 slots' live `status`/`worker_alive`/`account_id`
directly (`GET /api/state`) before assuming account exhaustion — a `paused` reserve slot produces the identical
error message with zero account involvement. Also check whether all 3 are bound to the SAME account (a real,
separate finding even once unpaused — a single-account reserve is a single point of failure the moment that one
account is paused/rate-limited).

## Step 5 — scheduled-job efficiency + backlog

`bash agent-orchestrator/scripts/orchestrator/check-scheduled-job-health.sh runs 2` and `... agents` (already
pulled in Step 1). Read the output against the status model
(`/codex/04-architecture/agent-orchestrator-scheduled-jobs.md`):

- **`quarantined`/`timeout`/`error`** are the three statuses that page — any of these present is a Step-8 finding.
- **`dispatched` is a spawn receipt, not completion** — cross-check `agent_exit_reason == "lifecycle-complete"` via
  the `agents` mode of the health-check script; a `dispatched` row whose agent went `reaped-stale` is silent data
  loss on that day's audit, even though nothing paged.
- **A sharded job (plan-reconciler / ag-closeout-auditor / na-eligibility-auditor) missing a tranche** for the day
  is a finding even if every individual dispatch shows `dispatched` — the `runs` mode's "tranches DISPATCHED per
  day" section is the check, not the raw status counts.
- **A paused scheduled-dispatch mode** (`POST /api/scheduled-dispatch/{mode}/pause` — see
  `agent-orchestrator/server/scheduled_dispatch_pause.py`) is a **deliberate, self-resolving non-failure**, not an
  error — but a mode that's been paused for a long time with no operator note explaining why is worth surfacing:
  check `GET /api/scheduled-dispatch` (or the equivalent list endpoint) for currently-paused modes and report them
  by name + how long paused, so a forgotten pause from an unrelated investigation doesn't silently starve a job
  for weeks (this exact class of bug — 6 modes left paused from an unrelated 2026-08-11 investigation, misread as
  "error" on every retry for days — is documented in
  `agent-orchestrator/scripts/install-escalation-queue-reconciler-timer.sh`'s own header comment).
  **Currently-known paused modes (as of 2026-08-18, operator-confirmed intentional — check
  `plans/active/issues/ao_scheduled_dispatch_pause_reasons_2026_08_18.md` for the full reasons before
  re-flagging these as a mystery):** `cefi_mtds_smoke` (cost/orphan-resource risk, pending deployment-service
  registration of its spawned resources), `ag_closeout` (heavy concurrent manual AG-closeout reconciliation in
  flight), `ci_reconcile` (deliberately run manually as a daily task until escalation-routing confidence is
  higher). If `GET /api/scheduled-dispatch/status` still shows exactly these three paused, treat it as expected
  and move on; if the SET has changed (a new mode paused, or one of these three unexpectedly resumed), that's a
  real finding — check the issue doc's "Unblocks when" for each before assuming anything.
- **Capacity-queue depth** (`ScheduledJobQueueRow`) — a persistently non-empty queue across multiple ticks means
  the fleet's scheduled-job reserve (`scheduled_task_slot_reserve()`, default 4) is undersized relative to actual
  contention; this is a capacity-sizing finding, not a per-job bug.

## Step 6 — blocked questions: VERIFY VALIDITY FIRST, then bring the operator only what's still real

Blocked questions piling up unanswered is explicitly one of the things this skill exists to fix, not just report —
but **do not hand the operator a raw dump of every open question and make them adjudicate each one.** Operator
correction (2026-08-17), verbatim: "most of these questions aren't valid — why don't you just go through all of
them yourself, check if they're actually valid versus the current state of affairs, and just come back with the
ones that are actually valid... what's the point when a lot of them you end up just going and finding out that
they're invalid?" A live measured session this same day found roughly a **third of a 51-question backlog had
already self-resolved** (a promotion deadlock that cleared on its own, a ratchet baseline back at zero, a VM
already killed, a manifest "shrink" that was a bucket-mixup already retracted, a relaunch already covered by an
established auto-approved pattern) — every one of those would have wasted the operator's attention if asked
directly instead of checked first.

**0. Verify BEFORE presenting — this is the default, not an opt-in.** For every open blocked question, before it
ever reaches the operator: re-check its claim against CURRENT live state (not the question's own age-old snapshot).
Concretely, per question: is the thing it's asking about still true right now (a stuck process, a paused
scheduler, a pending VM, a contested doc claim)? Has it already been fixed by another session, self-healed, or
been superseded by later work on the same doc? A question is **stale/invalid** when re-checking shows the
underlying condition no longer holds — close it out directly (`disposition: final`, citing the fresh evidence that
made it moot), never hand it to the operator to notice that for you. A question is **still genuinely valid** only
when the live re-check confirms the condition holds AND it needs a real judgment call the worker/AO couldn't make
alone (a cost/scope tradeoff, an ambiguous fork with no clear right answer, a live credential/production action
that's genuinely operator-territory). **Only THAT subset goes to the operator**, and even then with your own
verified recommendation attached, not a bare question. Dispatch this verification in parallel across as many
sub-agents as the backlog's domain spread reasonably supports (don't serialize 40+ individual live-state checks
one at a time) — but batch related items from the same doc/domain into one agent rather than one agent per
question, or the verification pass itself becomes the thing burning excessive tool calls.

**Two failure modes measured live (2026-08-18 run), fold into how you read this step's results:**

- **A verification subagent's own hand-back can get flagged for exceeding its authority** — e.g. recommending the
  parent kill+relaunch a live VM it didn't create, or read credential-sensitive files (wallet/KMS config) via a
  path that bypasses the intended access pattern, or self-mark an `[OPERATOR]`-tagged todo done without actual
  operator sign-off. When a subagent's result carries a security-policy flag like this, treat its factual findings
  as informative but do NOT execute its recommended action — surface it to the operator via `AskUserQuestion` same
  as any other still-valid finding, and only act once they've actually said yes. This isn't a subagent bug to
  suppress; it's the harness correctly catching a subagent overstepping an `[OPERATOR]` gate that exists for a
  reason.
- **A verification (or any) subagent can itself fail with a session/rate-limit error** (`"You've hit your session
limit"`) when the account pool backing this interactive session — not just AO's fleet — is broadly exhausted.
  This is a REAL signal, not noise: if it fires, cross-check it against Step 3f's account-status pull (a subagent
  failing this way while several named accounts show `rate_limited` is corroborating evidence for that finding,
  not a separate problem). Don't retry-loop against it — note the check as incomplete/deferred (answer the
  corresponding blocked question with `disposition: partial` if one exists), state the reset time if given, and
  let the next run or a later retry pick it back up once capacity returns.

1. **Pull every open question.** `GET /api/blocked/stats` for the count/age distribution; the full list (grep
   `server/routes/backlog.py` / `state.py` for the exact list route if `/stats` alone doesn't carry full text —
   `group_similar_blocked`/`_blocked_to_view` in `routes/state.py` are the rendering helpers the dashboard itself
   uses, so whatever route feeds those is the right one). For each: `blocked_id`, originating slot/task, the
   question text, the options offered, age.
2. **Draft a recommendation for every question before presenting any of them** — same "always present options,
   never open-ended, mark your recommendation" convention every other worker in this workspace already follows
   (`SUB_AGENT_MANDATORY_RULES.md` § "When escalating a question to the operator"). A question with only one
   real answer isn't a question — say so and answer it yourself if it's a slam-dunk case (see step 4 below); don't
   manufacture a choice.
3. **Present the batch via `AskUserQuestion`** (this session's own interactive-chat tool) rather than just listing
   them in prose — the goal is answers landing in AO, not a summary the operator has to re-transcribe by hand.
   Group similar/duplicate questions (the dashboard's own `group_similar_blocked` already does this by normalized
   question text — reuse that grouping, don't re-cluster by eye) so the operator answers each distinct question
   once, not once per slot that asked it.
4. **Route by who's answering, per the operator's own instruction**: if the person in this interactive chat is
   Harsh, they answer what they can and this skill immediately updates AO (`POST /api/blocked/{blocked_id}/answer`)
   for each answered one so it disappears from the open-questions list, and leaves the rest genuinely open for
   Ikenna — do not guess an answer on Harsh's behalf for a question they didn't address. If the person is Ikenna,
   they can answer all of them (nothing is deferred past this session). **If the chat participant's identity
   isn't already established in this session, ask once** rather than guessing — a wrong guess here means an
   answer gets attributed to the wrong operator or a question gets silently left for someone who wasn't actually
   present. Don't ask on every run once identity is already known from context.
5. **Apply every answer immediately as it's given** — `POST /api/blocked/{blocked_id}/answer` per answered
   question, in the same turn as the answer, not batched to the end. A `partial` answer keeps the row open and
   re-paging per the alerting SSOT's own bookend rule (`notify_slot_blocked_answered` only fires on a FINAL
   answer) — make sure whichever answer you submit is actually final if that's the operator's intent, or say
   explicitly that it's partial and will re-page.
6. **Report what's left.** Anything genuinely deferred (waiting on Ikenna, or waiting on external info) stays
   listed with its recommendation intact for next time — don't lose the drafted recommendation between runs.

## Step 7 — known-issue regression scan (before filing anything new)

Already primed by Step 0 and applied per-finding in Step 2, but restate as its own gate before Step 8: **for every
finding this run produces, has this exact shape been seen and "resolved" before?** If yes, this is a regression —
correct the existing doc (new dated section, corrected banner, root-cause note on why the earlier fix didn't
hold) rather than opening a duplicate. If the earlier fix's scope was narrower than today's incident (the FM5/FM7
example: fixed for scheduled-job dispatch, not for general spawns), say so explicitly — don't claim the old fix
"didn't work," when it may simply have never covered this surface.

## Step 8 — fix or file (standard findings-triage HARD RULE, no exception here)

Same ladder as every other skill in this family (`/escalation-queue-reconcile` Step 4, `/ci-reconcile`, the
workspace-wide rule): a small, clear, obviously-correct fix (a stale dedup constant, a missing log line, an
alerting-classification gap) → fix directly, `quality-gates.sh --no-fix` → `quickmerge.sh --agent --files '<paths>'`.
Ambiguous, cross-repo, or a genuine judgment call → the ask-main-first-bounded-wait pattern
(`POST /api/slots/$SLOT_ID/blocked`, 2-minute cap) before falling back to
`plans/active/issues/<slug>_<date>.md` — cite whatever Step 0/7 prior art you found. A **big finding**
(data-correctness, cross-repo, SSOT contradiction, or anything the workspace's big-finding rule already names) →
notify the operator directly in chat AND file the issue doc, same as everywhere else. "Pre-existing" is never a
reason to skip triage.

## Step 9 — Slack/GH alert-quality pass: would this have paged correctly?

For every genuine finding from Steps 2-8, check it against the alerting SSOT's pager-audit table
(`/codex/04-architecture/agent-orchestrator-alerting.md` § "Complete pager audit") — **before** filing an
alerting-hardening finding, confirm you're reading the CURRENT table, not a stale memory of it (this doc gets
amended often; re-read it fresh this run).

- **Should have paged, and did** — fine, no finding.
- **Should have paged, and didn't** (or paged too quietly / too late) — a real gap, file it.
- **Paged, but shouldn't have per the actionable-only contract** (routine lifecycle churn reaching the channel) —
  also a real gap; noisy alerting erodes trust in the channel just as much as silent gaps do.
- **Paged correctly but with no dedup**, producing N near-identical pages for one root cause (the FM5/FM7 storm's
  own suspected shape — confirm live whether `notify_spawn_failed`'s documented "summary-only, no page" status
  actually held, or whether these alerts DID page repeatedly, which would itself be a doc-vs-reality drift finding
  distinct from the underlying quarantine bug) — file as a dedup-hardening gap, citing the specific notifier and
  how many near-duplicate pages fired in the observed window.
- **Read today's/this-week's actual channel history** via `python3 unified-trading-pm/scripts/dev/slack-read-channel.py
agent-orchestrator-alerts <hours>` (also check `ci-failures` if the run's findings touch CI) before asserting
  anything about what "actually paged" — don't infer it from the code alone; the doc and the live channel can
  drift apart, and that drift is itself the kind of finding this step exists to catch. **Gap confirmed live
  (2026-08-20)**: this script can fail in a fresh interactive/laptop session with
  `gcloud failed to resolve SLACK_ALERTS_READER_BOT_TOKEN` when the pinned service account isn't activated
  locally — try `gcloud auth activate-service-account` for the SA named in
  `/codex/05-infrastructure/agent-slack-read-access.md` first; if that's not available in-session, fall back to
  reading the VM's `data/state/*.dedup.json` files (which alert conditions fired + when, from dedup-state
  timestamps) as a partial substitute rather than skipping the alert-quality pass entirely, and say explicitly
  that the check is partial/degraded in the report.

## Step 10 — day-over-day diff: yesterday vs the day before

The operator's standing ask (2026-08-18): every run should read as "what changed since yesterday, compared to the
day before" — not just a snapshot. Each metric family below has a DIFFERENT real mechanism (there is no one
generic "give me day N" API across this fleet) — use the one that actually exists, don't invent a param:

1. **Fleet KPIs — already built, just read both halves.** `GET /api/fleet-kpis?window_hours=24`
   (`server/routes/state.py:340-379`) returns `current` (last 24h from now) AND `baseline` (the 24h before that) in
   ONE response, plus the derived `regression_alert`. This is now-anchored, not UTC-midnight-anchored, but it
   already IS "since yesterday vs the day before" for practical purposes — Step 3a's gap so far has been reading
   only `regression_alert` and discarding `baseline`. Report `current` vs `baseline` side by side for every field
   (boots, dispatches, done, conversion_pct, boots_per_done), not just the alert boolean.
2. **Scheduled-job health — already buckets by calendar day.** `check-scheduled-job-health.sh runs 2` (Step 5)
   sweeps `within_hours` in 24h increments and prints one row per calendar day already — read yesterday's row and
   the day-before's row and diff status counts + tranche coverage directly; no second call needed.
3. **Escalations & blocked questions — no day-scoped route exists** (verified 2026-08-18: `/api/blocked/stats` and
   `/api/escalations/active` are both current-snapshot-only, zero date params). Until a real route exists, derive
   counts from `activity_log` event types `escalation_dispatched`/`escalation_resolved`/`slot_blocked`
   (`/codex/04-architecture/agent-orchestrator-alerting.md` digest glossary), grouped by day, as one more query in
   the same aggregated remote script Step 1 already runs — don't add a separate round trip. File a follow-up plan
   todo for a real `by_day` route mirroring `compute_dispatch_efficiency_by_day` (`fleet_kpis.py:363-385`) rather
   than re-deriving this ad hoc every run. **Gap confirmed live (2026-08-20)**: a direct
   `GET /api/activity?types=escalation_dispatched,escalation_resolved,slot_blocked&since=...` attempt **500'd** on
   the live server — don't treat this as a permanently-missing route without re-checking; file/confirm a follow-up
   to root-cause the 500 (param combination vs a genuine route bug) rather than assuming it's simply absent. **Gap confirmed live (2026-08-20)**: a direct
   `GET /api/activity?types=escalation_dispatched,escalation_resolved,slot_blocked&since=...` attempt **500'd** on
   the live server — don't treat this as a permanently-missing route without re-checking; file/confirm a follow-up
   to root-cause the 500 (param combination vs a genuine route bug) rather than assuming it's simply absent.
4. **Slack alert volume — no offset param; split it yourself.** `slack-read-channel.py <channel> 48 --json-only`
   (there is no "hours N-to-M ago" flag) pulls a 48h window to one JSON file; bucket its messages by `ts` at the
   24h boundary to get yesterday's count vs the day-before's.
5. **Resource usage — two different mechanisms for two different hosts, don't conflate them** (see the Step 3f
   correction above for why):
   - **The orchestrator VM itself**: per-day JSONL at `config.resource_history_dir()/<date>.jsonl` — `cat`/aggregate
     yesterday's and the day-before's files (avg/max cpu/iowait/load/ram/swap/disk) via the same SSM shell Step 1
     already opens.
   - **Backfill/launcher VMs**: `GET /api/vm-resources/rolling` gives rolling-window avg/min/max/p95 (1h/4h/24h/1wk,
     now-anchored) — for a strict calendar-day diff instead, use the documented `bq extract` → DuckDB pattern
     (`deployment-observability.md` § resource_samples) grouping by `DATE(ts)`, not a from-scratch query.

Report every diff as a table (metric | yesterday | day-before | delta), and lead with anything that moved
meaningfully — two columns of numbers with no callout defeats the point of a diff report.

## Step 11 — flag significant design changes

Confirmed gap (2026-08-18 research): no existing activity_log event type, dashboard field, or worker-reporting
mechanism captures "a worker made a significant architecture/design decision today" — checked against the full
digest event glossary (`/codex/04-architecture/agent-orchestrator-alerting.md` § "Digest event glossary") and
found nothing. This step is a best-effort heuristic sweep until a real signal exists, not a complete detector —
say so in the report rather than implying full coverage:

1. **New/changed codex SSOT docs** in the last 24h (`git log --since=<yesterday-midnight> --name-only -- 'codex/**'`
   across the fleet) — a new or materially-edited SSOT is close to the definition of "a design decision got made."
2. **New epics/plans** under `plans/epics/`, or `plans/active/` docs with major architectural framing — a new epic
   is a scope-of-work decision worth a one-line flag even when expected.
3. **`feat!:`/`BREAKING`-tagged commits** across the fleet in the window (the same AST-based breaking-change
   detector `scripts/cicd/detect_breaking_change.py` already classifies these) — a genuine breaking-change commit
   is definitionally a design decision, not routine.
4. **Resolved `[OPERATOR]`-tagged design/architecture questions** from Step 6's blocked-questions pass — if any of
   today's answered questions were framed as an architecture/design tradeoff (not a routine unblock), pull them
   into this section too rather than letting them disappear into a bare "questions answered" count.
5. **Big-finding notifications** (the workspace's own data-correctness/cross-repo/SSOT-contradiction triage class)
   that fired today — these already page the operator per the workspace HARD RULE, but restate them here so the
   daily report is a complete "here's what needed your judgment today" digest, not just a duplicate of the pager.

Report each hit with repo + file/PR + a one-line description of the decision — never a bare commit count. If
nothing matches, say so explicitly ("no design-shaped changes detected today") rather than omitting the section —
a heuristic sweep finding nothing is a real, if weaker, signal, not the same as not having looked.

## Step 12 — report

Lead with anything from `regression_alert` (3a), Step 10's biggest day-over-day mover, a Step 11 design-change
flag, or a genuine Step 2-9 finding — never bury a real problem under a wall of healthy-KPI numbers. Then, in
order: the Step 10 day-over-day diff table (this is the headline shape the operator asks for, not an afterthought),
occupancy + conversion (3a/3b), cost caveat-labeled estimate (3d), scheduled-job health (Step 5), blocked-questions
outcome (how many answered now vs left open and for whom, Step 6), escalation-queue verdict (Step 4, one line if
healthy), resource usage (3f + Step 10's VM diff), Step 11's design-change flags, and the Step 9 alert-quality
verdict. Every $ figure carries its "API-list-price-equivalent, not actual spend" label inline, not as a
disclaimer at the bottom where it'll get dropped in a copy-paste.

## Composability — what this skill does NOT do

Does not root-cause an individual CI wall (`/ci-reconcile`'s job). Does not deep-diagnose the escalation-queue
mechanism (`/escalation-queue-reconcile`'s job, only invoked here past its own Step 1). Does not audit VM
preemption/billing-waste in depth or CPU/mem rightsizing (`/vm-preemption-billing-waste-audit` /
`/vm-resource-rightsizing-check`'s job). Does not reconcile the `data-pipeline-alerts` channel
(`/data-pipeline-alerts-reconcile`'s job). Does not itself install or modify a scheduled-job timer, change
`escalation.py`/`fleet_kpis.py` tuning constants without evidenced drift, or force anything through the blocked-
questions queue without a real answer from the operator present.

## Scheduling this skill

**Repo-side wiring is done, but the live systemd timer is NOT yet installed on the VM** (corrected 2026-08-19 by a
live `/ao-watchdog` run — the previous text here claiming "are all live" was stale/wrong, confirmed via
`systemctl status ao-watchdog.timer` on the orchestrator VM returning "Unit ao-watchdog.timer could not be found").
What IS live: `mode="ao_watchdog"` in `agent-orchestrator/server/plan_health.py`'s dispatch handler (the
`_MODE_PROMPT_TEMPLATE`/`_MODE_AGENT_KIND` dicts, mirroring `escalation_reconcile`'s wiring), the thin wrapper role
file `unified-trading-pm/agents/ao_watchdog.md`, and the installer script itself
`agent-orchestrator/scripts/install-ao-watchdog-timer.sh` (targeting daily 00:47 UTC — midnight-adjacent per the
operator's 2026-08-18 cadence decision, staggered against `ci_reconciler`/`plan_reconciler`) — but that script has
never actually been RUN on the central orchestrator VM, so no `ao-watchdog.timer`/`.service` unit exists there yet.
This is tracked as the sole remaining open todo in `ao_watchdog_scheduled_timer_wiring_2026_08_17.md`
(`[OPERATOR] P2. Re-run install-ao-watchdog-timer.sh on the central orchestrator VM`) — it needs either operator
action or an explicitly-authorized AO-dispatched-worker/SSM run (the script itself needs no `sudo` per the
2026-08-08 hard rule, so technically runnable via the same read-only-adjacent SSM `RunShellScript` path this skill
already uses for its own live checks — but installing a unit is a real mutating change, not read-only, so get
explicit go-ahead before running it). Until that lands, this skill runs manually / via `/autonomous` only — there
is no additive timer path yet.

## Under `/autonomous` / one-shot dispatch contract

One-shot per invocation, matching the shape every other scheduled AO worker uses — Step 6's `AskUserQuestion`
interactive path only applies when actually running interactively; a dispatched worker with no chat present skips
Step 6's live-answer flow and instead leaves every open question with its drafted recommendation intact in the
report (never fabricate an answer on the operator's behalf). Step 6's 2-minute bounded-wait pattern (Step 8, when
used) is the one exception to "never pause," same as `/escalation-queue-reconcile`.

## Folding findings back in (read this before finishing every run)

This skill is explicitly meant to get smarter every time it runs — the operator's own instruction. Before ending
any run: did this pass discover an alert shape, KPI gap, blocked-question pattern, or dashboard section not
already named above? **Add it to this file in the same session**, in the right numbered step (or a new one) —
not as a separate note, not deferred to "next time." A watchdog skill that doesn't update itself from what it just
found is not actually watching.
