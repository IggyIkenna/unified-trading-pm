---
doc_type: issue
title:
  "glue-runner-health-monitor.yml 403'd on EVERY run (100%, not intermittent) because GET
  /repos/{owner}/{repo}/actions/runners requires the `administration` scope, which does not exist as a grantable
  GITHUB_TOKEN permission — masked as 'intermittent' by set +e (job conclusion always success) + notify-slack's 60-min
  dedup cooldown"
summary: >-
  The dead-man-switch `glue-runner-health-monitor` paged twice today (~09:53, ~12:48 operator-observed) with "could not
  query the runner API ... HTTP 403". An earlier same-session pass saw 8 consecutive GREEN run conclusions and wrongly
  concluded the 403 was transient/self-resolved — a repeat of the exact "pre-existing/transient" triage anti-pattern
  this workspace bans (SUB_AGENT_MANDATORY_RULES.md "Findings triage"). Root-caused instead: pulled every run's actual
  JOB LOG (not just its conclusion) for the 13 runs spanning 2026-08-07T05:20Z-11:47Z and found **13/13 hit the exact
  same 403** — the failure is not intermittent at all, it is constant. Two things independently masked that from a
  conclusion-level read: (1) the workflow step runs `python3 ... || true`-equivalent (`set +e`; RC captured but the
  step/job itself never fails), so `gh run list --json conclusion` reports `success` on every run regardless of whether
  the script's own exit code was 0 or 1 — conclusion is not a valid proxy for "the query succeeded"; (2) the downstream
  `notify-slack.yml` reusable workflow dedups `dedup_key: glue-runner-pool-low` with `cooldown_min: 60` — a STANDING
  (never-clearing) failure condition only re-pages on the hour, which reads exactly like "it recurred" rather than "it
  never stopped." Mechanism: `GET /repos/{owner}/{repo}/actions/runners` requires the `administration` repository
  permission (fine-grained PAT: `Administration:read`; classic PAT: `repo` scope) — confirmed against GitHub's
  workflow-syntax docs that `administration` is **not** one of the ~16 keys grantable to the automatic `GITHUB_TOKEN` in
  a workflow's `permissions:` block at all (only actions/attestations/checks/contents/deployments/discussions/
  id-token/issues/packages/pages/pull-requests/security-events/statuses/artifact-metadata/code-quality/
  vulnerability-alerts). So `actions: read` was never insufficient by a small margin — no `permissions:` block could
  ever have satisfied this endpoint; the workflow needed a different CREDENTIAL, not a different scope declaration.
  Fixed by switching the step's `GH_TOKEN` from `secrets.GITHUB_TOKEN` to `secrets.GH_PAT` — the same fine-grained PAT
  this repo already uses for exactly this class of gap (`ci-status-update.yml`, `escalate-to-orchestrator.yml`), and the
  SAME PAT `setup-glue-runners.sh`/`refresh-gh-token.sh` already require to carry `Administration:write` (a strict
  superset of the `Administration:read` this call needs) in order to mint runner-registration tokens in the first place.
  Live-verified via a fresh `workflow_dispatch` run (`31177324373`, ref `live-defi-rollout`): the "Count online glue
  runners" step log no longer contains the 403 — it now returns a real payload. **That real payload is itself a second,
  genuine finding**: `GET /repos/IggyIkenna/unified-trading-pm/actions/runners` returns `{"total_count":0,
  "runners":[]}` — this repo's OWN `glue`/`glue-writer` pools currently have ZERO registered runners (by contrast,
  `agent-orchestrator`'s pool shows 3/3 online) — so the monitor now correctly reports "pool depleted: 0/0 online" the
  same fail-closed way it used to report "blind"; the Slack post for that specific run was itself deduped (same
  `glue-runner-pool-low` key, still inside the 60-min window from the last blind-page), which is correct dedup behavior,
  not a bug. This depletion is left OPEN below — diagnosing/fixing it needs host access to the planning VM's systemd
  units, which this session did not have.
status: open
nature: issue
asset_group: [cross-cutting, ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    glue-runner,
    self-hosted-runner,
    github-token-permissions,
    dead-man-switch,
    monitoring-gap,
    false-transient-triage,
  ]
related:
  [
    /plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md,
    /plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: devops
drift_direction: advance-code
depends_on: []
resolved_by: "unified-trading-pm@f05e93d10a (live-defi-rollout)"
locked_by:
locked_since:
source: "operator-flagged recurring page 2026-08-07 (~09:53, ~12:48), main session /autonomous-adjacent investigation"
context_scope:
  [
    scripts/cicd/glue_runner_health_monitor.py,
    .github/workflows/glue-runner-health-monitor.yml,
    scripts/self-hosted-runners/README.md,
    scripts/self-hosted-runners/setup-glue-runners.sh,
  ]
---

# glue-runner-health-monitor 403: constant, not intermittent — GITHUB_TOKEN structurally cannot list self-hosted runners

## Fix applied (RESOLVED)

`.github/workflows/glue-runner-health-monitor.yml`, `check` job, `Count online glue runners` step: `GH_TOKEN` changed
from `${{ secrets.GITHUB_TOKEN }}` to `${{ secrets.GH_PAT }}`. Shipped `unified-trading-pm@f05e93d10a` on
`live-defi-rollout` via `quickmerge.sh --agent`.

**Live verification** (not just "the code looks right"): triggered
`gh workflow run glue-runner-health-monitor.yml --ref live-defi-rollout` → run `31177324373`. Job log for "Count online
glue runners":

```
:rotating_light: *glue runner pool depleted* — only 0/0 `glue` runner(s) online (need ≥ 3):
  • no registered `glue` runner is offline — the pool itself may have shrunk.
```

No 403, no "could not query the runner API" — the query itself now succeeds. (The 0/0 reading is the second finding
below, not a re-occurrence of the auth bug.)

## Still open

- [ ] [DEVOPS] P1. `unified-trading-pm`'s own self-hosted runner pool (`glue` + `glue-writer` labels) currently shows
      `total_count: 0` via `GET /repos/IggyIkenna/unified-trading-pm/actions/runners` — every registered runner is gone,
      not just offline (compare `agent-orchestrator`'s pool: 3/3 `online`). This is distinct from the 17-public-repo
      deregistration in `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` (PM is private and
      was explicitly NOT in scope of that revert) and distinct from the 2-stopped-units incident in
      `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` (that was `unified-api-contracts`/`instruments-service`
      units, not PM's own). Needs someone with host access to the planning VM to run
      `scripts/self-hosted-runners/setup-glue-runners.sh status` (or
      `sudo systemctl status     'github-glue-runner-unified-trading-pm@*'`) and re-register/restart whatever's down —
      this session had no VM access to diagnose further. Until fixed, every PM workflow still declaring
      `runs-on: [self-hosted, glue]` (the README says ~37 "MOVE" workflows) has no runner to claim it.
- [ ] [DEVOPS] P3. `.github/workflows/ci-status-update.yml` lines 45-47 and 265-267 carry a stale comment ("Goes to the
      LONG-LIVED glue-writer pool, NOT the JIT glue pool") directly above `runs-on: ubuntu-latest` — the workflow was
      apparently already reverted to GitHub-hosted at some point but the comment wasn't updated to match. Low-priority
      doc-drift (confirmed NOT causing the queued jobs observed during this investigation — those cleared normally), but
      worth a one-line comment fix next time that file is touched.

## Progress Log

- **2026-08-07 ~12:00-12:15 UTC**: root-caused via full job-log pull across 13 runs (100% 403 rate, not intermittent);
  confirmed `administration` is not a valid `GITHUB_TOKEN` `permissions:` key against GitHub's workflow-syntax docs;
  confirmed `GH_PAT` (this repo's existing runner-admin PAT, already required to carry `Administration:write` per
  `setup-glue-runners.sh`'s own registration-token probe) is the correct, already-precedented fix; shipped `f05e93d10a`;
  live-verified via triggered run `31177324373` — 403 gone, real `0/0 online` reading returned; opened the
  pool-depletion finding above as follow-up (out of this session's tool reach — no VM access).
