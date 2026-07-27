---
doc_type: issue
title:
  "git-health reporter goes silent host-wide when ~/.orch_token expires: slot-git-status-report.sh POSTs to the PUBLIC
  ORCH_URL with a Bearer token, so a rotated/expired token silences the whole host's git-health view while FF-pull stays
  healthy (it never pushes)"
summary:
  The per-slot git-health reporter (unified-trading-pm/scripts/dev/slot-git-status-report.sh) POSTs each slot's
  git-status snapshot to /api/slots/{slot_id}/git-status using the default public ORCH_URL
  (https://api.agent-orchestrator.odum-research.com) with an `Authorization` Bearer header read from ~/.orch_token. When
  that token expires/rotates, every push 401s and the reporter goes SILENT for the entire host — the dashboard
  git-health view for all of that host's slots freezes at the last successful report and the server's staleness watchdog
  then fires `git_staleness_alert_sent` (message "git reporter cron silent for Nm") for every slot on a loop. Critically
  the FF-pull cron (slot-cron-ff-pull.sh) is UNAFFECTED because it never pushes to the server — so ff-pull keeps working
  while the dashboard shows the host as stale, which can mask a real dirty/behind worktree or raise false ff_cron_stale
  alarms fleet-wide. Confirmed live 2026-07-24 on host ip-172-31-5-118 (17 slots) — reporter froze at
  2026-07-24T15:47:03Z, and `git_staleness_alert_sent` was still firing for slots 0-16 at 20:02Z (~255m silent);
  ~/.orch_token mtime was 2026-06-24, consistent with an expired/stale bearer token. Non-blocking, no-page
  (observability-integrity, not operational) — but it recurs on every token rotation and spams the activity feed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [git-health, monitoring, reporter, token-expiry, loopback, false-positive, per-tab-worktrees, agent-orchestrator]
related:
  [
    /plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
priority: P2
parent_epic: infrastructure_master
source:
  "review(agt-af7186) msgs 1862/1867 + review(agt-d76e80) to main orchestrator, 2026-07-24; main root-cause on-host"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# git-health reporter goes silent host-wide on ~/.orch_token expiry

## What happens

`slot-git-status-report.sh` (cron, ~5-min cadence, per host) walks `.tabs/<N>/<repo>/`, builds a git-status snapshot,
and POSTs it to `/api/slots/<N>/git-status`. Defaults (script header):

- `ORCH_URL` = `https://api.agent-orchestrator.odum-research.com` (PUBLIC — token-required)
- Auth = `Authorization: Bearer <cat ORCH_TOKEN_FILE>`, `ORCH_TOKEN_FILE` default `$HOME/.orch_token`

When `~/.orch_token` expires/rotates, every POST 401s, the reporter stops updating server state for that host, and the
server's staleness watchdog emits `git_staleness_alert_sent` ("git reporter cron: silent for Nm") for each slot on the
host, every tick. FF-pull (`slot-cron-ff-pull.sh`) is unaffected — it fast-forwards local clones and never talks to the
server — so the host keeps pulling cleanly while its dashboard git-health rows freeze. Net harm: the dashboard
git-health view for the whole host is stale/misleading (can mask a genuinely dirty/behind worktree, or drive false
`ff_cron_stale`/`reporter_stale` alarms) and the activity feed fills with per-slot staleness alerts.

## Evidence (2026-07-24, host ip-172-31-5-118, 17 slots)

- `/api/fleet/git-health`: `reporter_stale=true` + `ff_cron_stale=true` for all 17 slots; cached `reported_at` frozen at
  `2026-07-24T15:47:03Z`.
- `/api/activity` at ~20:02Z: `git_staleness_alert_sent` for slot_id 0-16,
  `red_repos: ["git reporter cron: silent for 255m"]`.
- `slot-cron-ff-pull.sh` live + healthy: `/tmp/slot-cron-ff-pull.result.json` `ff_pull_last_run` ~2 min old (per review
  agt-af7186).
- `~/.orch_token` mtime `2026-06-24` — stale bearer token, consistent with the 15:47Z silence onset.

## Fix (agreed direction: loopback trusted-local, no token)

The reporter runs ON the orchestrator host, where `http://localhost:8765` is trusted-local and needs no bearer token —
so the durable fix is to make on-VM reporting use loopback rather than the public URL + a rotating token (re-minting the
token just resets the same treadmill). Design constraint: operator laptops run this script OFF-VM and MUST keep using
the public URL + token, so the fix must be conditional, not a blanket default flip.

## Todos

- [x] ✅ **DONE 2026-07-26 (slot-11, `infra`) — `unified-trading-pm@421262a`.** Make `slot-git-status-report.sh` prefer
      `http://localhost:8765` (trusted-local, no token) when the loopback backend is reachable, falling back to the
      public `ORCH_URL` + `ORCH_TOKEN_FILE` when it is not (off-VM operator laptops). Do NOT unconditionally flip the
      default `ORCH_URL` — that would break off-VM reporters. **Done-when:** on host ip-172-31-5-118, after the next
      reporter tick `/api/fleet/git-health` shows `reporter_stale=false` for the host's slots and
      `git_staleness_alert_sent` stops firing; off-VM path still uses public URL + token (verified by reading the
      branch, not just on-VM behaviour). Wire into the primary consumer's `quality-gates.sh` if the script isn't already
      covered. Implementation: a top-level probe (skipped entirely when `--orch-url`/`ORCH_URL` is explicit) hits
      `LOOPBACK_ORCH_URL` (default `http://localhost:8765`) `/api/healthz` with a 1s connect-timeout; on 200 it sets
      `ORCH_URL`+`IS_LOOPBACK=1` for the whole run. `resolve_token_for_slot` now succeeds with an EMPTY token in
      loopback mode when no token file exists (instead of skip-with-no-POST); `post_snapshot`/`post_starve_ping` omit
      the `Authorization` header entirely when the token is empty (not `Bearer ` with nothing after) so the request
      qualifies for the server's `_is_trusted_loopback` anonymous fallback. Live-verified against the real orchestrator
      (not just unit tests): ran the reporter with `ORCH_TOKEN_FILE` pointed at a deliberately garbage token, restricted
      to slot 11 — `[loopback] http://localhost:8765 reachable...` fired, POST succeeded
      (`[ok] slot 11 — 25 repos reported`), and `/api/fleet/git-health` confirmed `reporter_stale=false` for slot 11
      immediately after. 7 new hermetic bats tests in `tests/test_slot_git_status_loopback_preference.bats` (explicit
      URL/env override still wins; loopback-reachable vs unreachable; `resolve_token_for_slot` loopback-tolerant vs
      off-VM-strict; `post_snapshot` sends no Authorization header on an empty token) — all pass, plus the 7
      pre-existing `test_slot_git_status_dirty_count.bats` tests unaffected. `quality-gates.sh` green (sentinel matches
      HEAD). **"Wire into quality-gates.sh"**: NOT done — discovered `bats tests/` is not actually invoked anywhere in
      this repo's QG pipeline (bats-core is installed by CI tooling but never run), a pre-existing gap spanning every
      `.bats` file and the shared `base-service.sh` framework, out of scope for this one-script fix. Filed as
      `/plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`.
- [ ] [INFRA] P3. Immediate unblock (independent of the code fix): refresh `~/.orch_token` on ip-172-31-5-118 so the
      reporter resumes now, and confirm `reporter_stale` clears within one tick. (Stopgap only — the loopback fix above
      is what stops the recurrence on the next rotation.)

## Notes

- Non-blocking / no-page disposition confirmed with review (agt-af7186, msg 1867) and main on 2026-07-24.
- Sibling reporter issue (different failure mode — mid-FF-pull dirty flicker):
  /plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md.
