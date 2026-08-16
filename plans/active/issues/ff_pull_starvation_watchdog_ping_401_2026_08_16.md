---
doc_type: issue
title: "FF-pull starvation watchdog detects correctly but its operator-ping delivery has been HTTP 401 fleet-wide since at least 19:28Z"
summary: >-
  `slot-git-status-report.sh`'s FF-pull starvation watchdog (`check_starvation_for_slot`,
  `ff-starvation-detect.sh`) is correctly detecting real starvation episodes (a dirty local edit colliding with
  incoming origin content, blocking `slot-cron-ff-pull.sh`'s auto-heal) — confirmed live for `.tabs/5/unified-
  trading-pm` (starved 20:13:27Z-21:10:21Z, 42 commits behind, well past both the 25-commit and 3-tick paging
  thresholds). But every ping attempt to `${ORCH_URL}/api/slots/<N>/message` returns HTTP 401 and is logged as
  `[starve-ping-fail]` — the operator never actually gets notified. Same 401 hitting slots 3, 4, and 5 in
  `/tmp/slot-git-status-report.501.log`, starting at least 19:28Z (slot 3/4) and 20:13Z (slot 5), continuing every
  ~5 min with zero successful pings in the observed window. The DETECTION half of the system is healthy; the
  DELIVERY half is fleet-wide broken. Root cause not yet diagnosed — likely an expired/misconfigured bearer token
  the watchdog uses to authenticate against the orchestrator's slot-message API, not investigated further this
  session (don't guess-fix a credential without understanding its provisioning/rotation path).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ff-pull, starvation, watchdog, alerting, auth, 401, cron, per-tab-worktrees]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
author: claude-code (interactive session, slot-5)
priority: P1
parent_epic: infrastructure_master
source: >-
  Operator asked "isnt here a rule or cron for this... thought we fixed this" after I manually `git pull --ff-only`ed
  a starved PM repo. Investigation of /tmp/slot-cron-ff-pull.result.json (repo_dirty_ticks: 6 for this slot's PM
  clone) and /tmp/slot-git-status-report.501.log found the watchdog fired repeatedly and failed to deliver every time.
assigned_vm: planning
execution_scope: orchestrator-agent
effort: max
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: backend_engineer
drift_direction: none
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    scripts/dev/slot-git-status-report.sh,
    scripts/dev/ff-starvation-detect.sh,
    scripts/dev/slot-cron-ff-pull.sh,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /tmp/slot-git-status-report.501.log,
  ]
---

# FF-pull starvation watchdog detects correctly but ping delivery is 401 fleet-wide

## What I found

- `slot-cron-ff-pull.sh` (cron, every 5 min) reported `.tabs/5/unified-trading-pm` as `repo_dirty_ticks: 6` in
  `/tmp/slot-cron-ff-pull.result.json` — 6 consecutive ticks unable to fast-forward, despite the repo being only
  42 commits behind origin (confirmed via `git rev-list --count HEAD..origin/live-defi-rollout`), and despite the
  working-tree content of the dirty files being byte-identical to origin (confirmed via `git diff origin/...`).
- The starvation detector (`ff-starvation-detect.sh`, invoked by `slot-git-status-report.sh`'s
  `check_starvation_for_slot`) correctly identified this as a paging-worthy episode: 42 ≥ `FF_STARVE_COMMIT_THRESHOLD`
  (25, default) and 6 ticks ≥ `FF_DIRTY_STREAK_THRESHOLD` (3, `slot-cron-ff-pull.sh`).
- Every ping attempt (`post_starve_ping` → `POST ${ORCH_URL}/api/slots/${slot_id}/message`, bearer-token
  authenticated) returned HTTP 401, logged as `[starve-ping-fail] slot 5/unified-trading-pm — HTTP 401` — first
  observed 20:13:27Z, repeating every ~5 min through at least 21:10:21Z with zero successful `[starve-ping]`
  (200) entries anywhere in the visible log window.
- **Not isolated to this slot**: the same log shows `[starve-ping-fail] slot 3/unified-trading-pm — HTTP 401` and
  `[starve-ping-fail] slot 4/unified-trading-pm — HTTP 401` starting at least 19:28Z, and slot 3 also logged one
  `HTTP 502` (21:09:40Z) — consistent with a shared credential/endpoint problem, not a per-slot config issue.
- I manually resolved MY slot's starvation with `git pull --ff-only origin live-defi-rollout` (succeeded cleanly,
  `Applied autostash`, `ahead=0`/`behind=0` after) — this is a workaround for one instance, not a fix for the
  delivery pipeline.

## Why it matters

The whole point of the starvation watchdog (per `per-tab-worktrees.md`'s documented design) is that a stuck slot
self-reports instead of silently drifting hundreds of commits behind until someone notices by accident (the
exact `2026-06-10`/`2026-07-14` incidents that motivated building this). Right now the DETECTION half works but
the DELIVERY half is silently swallowing every alert — functionally equivalent to having no watchdog at all,
except it looks like one exists (misleading). This is exactly the kind of gap that lets a slot drift for hours
before an operator notices, same failure class as the incidents the mechanism was built to prevent.

## What I did NOT do

- Did not touch the ping/auth code — the token's provisioning/rotation mechanism isn't something to guess-fix
  from the client side without understanding how it's meant to be issued/refreshed.
- Did not attempt to diagnose the orchestrator-side `/api/slots/<N>/message` endpoint or check whether a JWT
  secret rotated recently — out of scope for a client-log-driven investigation.

## Todos

- [ ] [OPERATOR] P1. Diagnose the 401: check whether the bearer token `slot-git-status-report.sh` uses to POST to
      `${ORCH_URL}/api/slots/<N>/message` has expired, was rotated, or the endpoint itself changed its auth
      contract — cross-check against however AO's other internal-proxy ES256/JWT auth is provisioned (per
      CLAUDE.md: "internal proxy ES256 / accounts via GSM"). Confirm which of the fleet's slots are affected
      (at minimum 3, 4, 5 confirmed here) — likely all of them if it's a shared credential.
- [ ] [BACKEND] P2. Once root-caused, fix the credential/endpoint mismatch and verify with a live starvation
      episode (or a forced test) that `[starve-ping]` (200) actually appears in the log — the fix isn't done
      until a real successful delivery is observed, not just "the code looks right."
- [ ] [BACKEND] P3. Consider whether the watchdog itself should escalate differently (e.g. fall back to a Slack
      webhook, or write a local marker file an operator/agent can grep) when the orchestrator ping fails
      repeatedly, so a broken delivery path doesn't silently degrade to zero visibility again.

## Progress Log

- **2026-08-16 (interactive session, slot-5)**: filed after the operator asked why a starved PM repo wasn't
  auto-healed given the documented cron/watchdog — traced to detection working correctly but delivery 401'ing
  fleet-wide. Not root-caused further this session.
