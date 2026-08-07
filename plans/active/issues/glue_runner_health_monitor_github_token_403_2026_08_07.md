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
  not a bug. **Follow-up correction (see "Still open")**: a fresh, non-comment-only grep confirmed zero live PM
  workflows currently target `[self-hosted, glue]`, so the empty pool has no current consumer — a sibling session
  shipped `95cce3aa46` disabling this monitor's schedule (kept `workflow_dispatch`), which is the right outcome on
  balance, modulo one provenance nuance recorded below.
status: resolved
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

- [x] [DEVOPS] P1. **CORRECTED, not a live blocker — verified after this doc's first version overclaimed it.**
      `unified-trading-pm`'s own runner pool shows `total_count: 0` (confirmed), but a follow-up check — grepping every
      `.github/workflows/*.yml`'s **live, non-comment** `runs-on:` line, not a substring match that also catches
      historical comments — found **zero** PM workflows currently declare `[self-hosted, glue]` at all (the one hit,
      `ldr-docs-gate.yml`, only mentions `glue` in a comment describing a PAST fix; its live directive is
      `runs-on: ubuntu-latest`, and its recent `queued`/`failure` runs are a genuine content-gate failure — "Corpus
      frontmatter check" — unrelated to runners). So the empty pool currently has nothing depending on it. A sibling
      session (`slot-2·laptop`, same investigation thread) independently reached the same practical conclusion and
      shipped `unified-trading-pm@95cce3aa46` disabling this monitor's `schedule:` trigger (kept `workflow_dispatch` for
      manual checks) — **that fix is correct on the outcome**, though its commit message's cited provenance
      ("permanently deregistered fleet-wide" per `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 21) does NOT
      actually cover PM — that todo explicitly confirms PM's 8-unit pool was left ACTIVE/online at the time, and a later
      plan (`ci_pipeline_speed_and_cost_redesign_2026_08_05.md`) deliberately sized it to 3 (not 0). So PM's pool going
      to 0 was never a single fleet-wide decision — every individual PM workflow that used to target it was migrated to
      `ubuntu-latest` independently over time (see the `ci-status-update.yml` drift below), leaving the pool orphaned
      rather than formally retired. Net effect is the same either way (0 online, 0 consumers, safe to leave the schedule
      off) — flagging the provenance mismatch only so a future reader doesn't cite todo 21 for a claim it doesn't
      support, and doesn't assume PM's actual glue-writer/glue systemd units were ever explicitly decommissioned (nobody
      has confirmed that on the VM — they may still exist crashed/stopped rather than deregistered; harmless either way
      while 0 workflows target them, but worth closing out for real next time anyone has VM access, rather than leaving
      stopped units lying around).
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
  pool-depletion finding as a P1 follow-up (initial version of this doc).
- **2026-08-07 ~12:15-12:30 UTC**: caught my own overclaim before shipping it as final — the initial P1 follow-up said
  "every PM workflow still declaring `runs-on: [self-hosted, glue]` has no runner to claim it," sourced from a grep that
  matched a comment line (`ldr-docs-gate.yml`'s changelog note), not a live directive. Re-ran the grep comment-filtered
  across every workflow: zero live hits. Corrected the P1 item in place rather than leaving the wrong claim standing,
  per the same findings-triage discipline this doc's summary is about not violating. Also found (independently, same
  investigation thread) that a sibling session shipped `95cce3aa46` disabling this monitor's schedule for the same
  reason, and reconciled its commit-message provenance (cites todo 21 of
  `self_hosted_runner_public_repo_revert_2026_08_05.md`, which does not actually cover PM) without re-litigating its
  correct practical outcome.
