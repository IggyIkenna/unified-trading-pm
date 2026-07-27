---
doc_type: issue
title:
  Fleet git-health reports near-universal per-slot reporter/ff_cron staleness (reporter_stale_slots and
  ff_cron_stale_slots flat at 19/19 for 3+ consecutive 15-min ticks, up from a ~3 baseline) — the per-slot
  slot-cron-ff-pull.sh + slot-git-status-report.sh crons appear to have stopped firing broadly, plausibly disrupted by
  today's disk resize (290G→484G) and the 2 orchestrator server restarts, leaving a growing staleness/drift-detection
  blind spot even though no visible harm has landed yet.
summary: >-
  On 2026-07-27 the review role observed the fleet git-health aggregator reporting reporter_stale_slots and
  ff_cron_stale_slots both flat at 19/19 across 3 consecutive ticks (~45 min), up from an earlier ~3 baseline. The
  aggregator itself is healthy (generated_at current; fleet-git-health-guard.sh cron running every 15 min per /var/log),
  and slots 0-5 + 21-30 were all individually flagged true on BOTH per-slot signals — i.e. the staleness is
  near-universal, not a few stragglers. That pattern points at the PER-SLOT crons
  (unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh + slot-git-status-report.sh, per CLAUDE.md "Multi-agent safety")
  having stopped firing fleet-wide, rather than genuine per-slot drift. Plausible trigger: today's disk resize
  (290G→484G) plus the 2 orchestrator server self-heal restarts observed the same day. No visible harm yet — drift/dirty
  counts stay low and real work keeps landing on LDR — but those crons are precisely how slots stay current with LDR AND
  how staleness itself is detected, so if they are genuinely down fleet-wide this is a growing blind spot (staleness
  would keep accreting undetected), not a cosmetic metric. Main (agt-498659) partially verified from the orchestrator
  vantage: both scripts exist; the readable crontabs (ubuntu/root) show no invocation (no-access, INCONCLUSIVE —
  per-slot clones may carry their own crontab); and the github-glue-slot-refresh.timer that IS firing is unrelated (it
  refreshes the GitHub-glue runner's clone to main, not worker-slot LDR ff-pull). P2.
status: open
assigned_vm:
resolved_by:
locked_by:
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    per-slot-worktrees,
    ff-pull,
    slot-git-status-report,
    fleet-git-health,
    cron,
    observability,
    staleness-detection,
    blind-spot,
  ]
related: [/codex/05-infrastructure/per-tab-worktrees.md]
created: 2026-07-27
last_updated: 2026-07-27
priority: P2
parent_epic: orchestrator_master
source:
  "review role (msg 2387 to main agt-498659) reported fleet git-health reporter_stale_slots/ff_cron_stale_slots flat at
  19/19 for 3+ ticks; main (agt-498659) partially verified from the orchestrator vantage and captured it here so the
  finding survives compaction (review role never commits)."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## Observation

The review-role agent reported (2026-07-27) that the fleet git-health aggregator shows **reporter_stale_slots** and
**ff_cron_stale_slots** both flat at **19/19 for 3 consecutive 15-min ticks (~45 min)**, up from an earlier baseline of
~3. Spot-checked slots 0-5 and 21-30 were all flagged `true` on BOTH signals — the staleness is near-universal, not a
few stragglers.

The aggregator itself is healthy: `generated_at` is current and `fleet-git-health-guard.sh` runs every 15 min per
`/var/log`. So the flat 19/19 is a real signal about the per-slot layer, not an aggregator artifact.

## Likely cause

The per-slot crons `unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh` and `slot-git-status-report.sh` (CLAUDE.md
"Multi-agent safety": the 5-min ff-pull + git-status-report loop that keeps each slot current with LDR and emits its
freshness heartbeat) appear to have stopped firing fleet-wide. Plausible trigger: today's disk resize (290G→484G) plus
the 2 orchestrator server self-heal restarts observed the same day — either of which could have disrupted the per-slot
cron/timer wiring.

## Partial verification from the orchestrator vantage (main agt-498659)

- Both scripts exist at `unified-trading-pm/scripts/dev/`.
- Readable user crontabs (`ubuntu`, `root`) show no invocation of them — but this is **no-access / INCONCLUSIVE**: the
  per-slot clones may carry their own crontab that the orchestrator vantage can't read.
- `github-glue-slot-refresh.timer` IS firing (~1/min, last run current) but is **unrelated** — it refreshes the
  GitHub-glue runner's clone to `main`, not the worker slots' LDR ff-pull.

## Why it matters

Those crons are how slots (a) stay current with `live-defi-rollout` and (b) surface their own staleness. If they are
genuinely down fleet-wide, staleness/drift would keep accreting **undetected** — the 19/19 is both the symptom and the
loss of the detector. No visible harm has landed yet (drift/dirty counts stay low, work keeps landing), so this is not
urgent, but it is a real observability/robustness blind spot rather than a cosmetic metric.

## Status / next step

Captured only; **not yet diagnosed on the slot side.** Needs an owner on the agent-orchestrator / infra side to (1)
confirm from a slot vantage (readable per-slot crontab / systemd timer) whether the two crons are actually firing, (2)
correlate against the disk-resize + orchestrator-restart timeline, and (3) re-arm the cron wiring if it was dropped.
Low-risk today, but re-check the 19/19 trend — if it keeps climbing or drift/dirty counts start rising, escalate.
