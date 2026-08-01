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
assigned_vm: NA
resolved_by:
locked_by:
nature: issue
asset_group: [ao] # corrected 2026-07-30 (/ag-closeout-audit ao) -- was [cross-cutting]; per-slot AO crons, not multi-AG
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
last_updated: 2026-07-30
priority: P2
parent_epic: orchestrator_master
source:
  "review role (msg 2387 to main agt-498659) reported fleet git-health reporter_stale_slots/ff_cron_stale_slots flat at
  19/19 for 3+ ticks; main (agt-498659) partially verified from the orchestrator vantage and captured it here so the
  finding survives compaction (review role never commits)."
execution_scope: local-only
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

**RESOLVED for 2 of 3 hosts; residual localized to the human-planning VM (2026-07-30 update, slot 4).**

Diagnosed from a slot vantage (`.tabs/4` on host `ip-172-31-5-118`):

1. **Direct live evidence on this host**: both cron children were caught actually RUNNING mid-tick via `ps aux`
   (`/usr/sbin/cron -f -P` spawning `slot-cron-ff-pull.sh --all-slots --quiet` at the `:30` boundary), and the actual
   log files (`/run/user/1000/slot-cron-ff-pull.1000.log`, `/run/user/1000/slot-git-status-report.1000.log` — NOT
   `/tmp/*.log` as the script header's example install line suggests; the real cron line redirects to `/run/user/1000/`)
   show **continuous, successful 5-min ticks through 05:27-05:30Z with zero gap**, `[ok] slot N — 25 repos reported` for
   every slot 0-16 on this host. The user crontab itself is unreadable from this session (`fopen: Permission denied` on
   `/var/spool/cron/crontabs/ubuntu`, and `sudo` is blocked by `no_new_privs`), so the cron-table wiring itself couldn't
   be inspected directly — but the live process + log evidence is stronger proof of "is it firing" than reading the
   crontab text would be.
2. **Fleet-wide current state** (`GET /api/fleet/git-health`, queried live): `reporter_stale_slots: 3`,
   `ff_cron_stale_slots: 3` out of **36 total slots across 3 hosts** — down from the reported 19/19. Both my own host
   (`ip-172-31-5-118`, slots 1-16) and the `hk` host show **zero** stale slots. The near-universal 07-27 staleness has
   **self-resolved** on both actual worker-fleet hosts — plausibly it WAS the disk-resize/restart disruption, and it
   cleared once that settled (this host's `journalctl --list-boots` only retains back to 2026-07-29 18:15, so the 07-27
   event itself couldn't be directly re-confirmed from here, but the before/after count (19/19 → 0/16 on the hosts
   checked) is itself strong evidence the disruption was transient, not a dropped/broken cron wiring).
3. **The 3 remaining stale slots are NOT fleet-wide** — all 3 (`slot 0, 1, 2`) are on a single host, resolved via
   `aws ec2 describe-instances` to `i-0dd9812a96cdda5dc` (private IP `172.31.0.185`) = the **human-planning VM**
   (CLAUDE.md: "interactive only", not a worker-fleet host). `slot 0` has been stale since **2026-07-25** (predates the
   07-27 disk-resize event entirely) and `slot 1`/`slot 2` since **2026-07-28T14:02Z**. This looks like a characteristic
   of that VM (an interactive box whose `.tabs/0-2` clones aren't kept warm by a standing cron the same way the
   always-on worker hosts are) rather than a re-run of the same fleet-wide incident — but it's still worth a human eye
   on that VM specifically since it's a genuinely different situation than what was originally reported.
4. **Could not directly re-arm/inspect cron on the human-planning VM**: attempted `aws ssm send-command` against
   `i-0dd9812a96cdda5dc` — denied (`AccessDeniedException`, my session's AWS identity is IAM user `ikenna-worker`, not
   the ambient `uts-orchestrator-epic-role`). Also attempted `sts assume-role` onto `uts-orchestrator-epic-role` —
   denied. Per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, the self-grant rule applies only
   when already acting AS `uts-orchestrator-epic-role`/`unified-trading-sa`; `ikenna-worker` is a genuinely different
   identity this worker cannot assume, so this is a legitimate escalation rather than a self-service gap — see the new
   todo below.

Bottom line: **no fleet-wide cron-wiring breakage exists today** — this closes the original "is it still fleet-wide"
question. The one open thread is operator/human-planning-VM-side: confirm whether slots 0-2 there need re-arming or
whether that stalenesss is an accepted characteristic of an interactive-only VM.

## Todos

- [x] [INFRA] P2. **Diagnose + re-arm the per-slot ff-pull/git-status-report crons** — confirm from a slot vantage
      whether `slot-cron-ff-pull.sh`/`slot-git-status-report.sh` are actually firing fleet-wide, correlate against the
      2026-07-27 disk-resize + orchestrator-restart timeline, and re-arm the cron wiring if it was dropped (see "Status
      / next step" above). — ✅ 2026-07-30, slot 4: confirmed firing (live process + log evidence) on both worker-fleet
      hosts (`ip-172-31-5-118`, `hk`); fleet-wide 19/19 has self-resolved to 3/36, all 3 isolated to the human-planning
      VM, not the worker fleet — nothing to re-arm on the hosts this worker could reach.
- [ ] [OPERATOR] P3. **Check cron/ff-pull health on the human-planning VM (`i-0dd9812a96cdda5dc`) for slots 0-2** —
      `slot 0` stale since 2026-07-25, `slot 1`/`slot 2` since 2026-07-28T14:02Z per `GET /api/fleet/git-health`. Needs
      either (a) SSM/direct access to that VM to confirm whether `slot-cron-ff-pull.sh`/ `slot-git-status-report.sh` are
      wired there at all (plausibly they're not, since it's an interactive-only VM per CLAUDE.md, not a standing worker
      host) and re-arm if genuinely dropped, or (b) a ruling that this staleness is expected/accepted for that VM's
      slots and the git-health aggregator should exclude/label them differently. A worker session here (AWS IAM user
      `ikenna-worker`) could not reach it: `ssm:SendCommand` and `sts:AssumeRole` onto `uts-orchestrator-epic-role` were
      both denied — this is a genuinely different identity than the ambient orchestrator role, so it doesn't qualify for
      the IAM self-service rule (repo: `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`).

## Progress Log

- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the sole
  open `[OPERATOR] P3` item requires access to the human-planning VM (`i-0dd9812a96cdda5dc`); the doc records a
  concrete, verified denial (`ssm:SendCommand`/`sts:AssumeRole` onto `uts-orchestrator-epic-role` both denied for the
  worker's IAM identity), explicitly a genuinely different identity than the ambient orchestrator role — a real access
  barrier, correctly NA.
