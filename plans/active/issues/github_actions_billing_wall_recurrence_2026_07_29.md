---
doc_type: issue
title: GitHub Actions billing wall recurrence (2026-07-29) — fleet-wide 0-step startup_failure, NOT a code/test defect
summary:
  "Escalated as an ldr_qg_failure wall for deployment-api (escalation agt-913803); reproduction shows this is NOT a
  deployment-api code/test/workflow-content bug. Every sampled repo (8+) shows the identical 0-step `startup_failure`
  (jobs:[]) signature on BOTH push and workflow_dispatch triggers, ongoing live as of 2026-07-29T20:58Z (a fresh
  workflow_dispatch retriggered during this session still failed in 1s). This exactly matches the archived
  github_actions_billing_wall_2026_06_11.md signature (GitHub account-level: recent payment failure / spending limit),
  which recurred again 2026-06-23 and self-recovered both times without any code change. Operator-only fix: check
  github.com/settings/billing. No workflow file, test, or code change can resolve this class."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    agent-orchestrator,
    deployment-service,
    features-service,
    alerting-service,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [ci-cd, github-actions, billing, startup_failure, incident, cross-repo, escalation]
related:
  [
    /plans/archive/issues/github_actions_billing_wall_2026_06_11.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/15-runbooks/devops-ci-walls.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
priority: P0
parent_epic: infrastructure_master
source: "cicd escalation agt-913803 (slot 12), dispatched for deployment-api ldr_qg_failure wall_type"
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# GitHub Actions billing wall recurrence (2026-07-29)

## Why this is a separate doc, not a fold into an existing one

Not the same mechanism as `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` /
`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`: those describe **slow/contended** self-hosted-runner
box symptoms (typecheck timeouts, pytest-xdist worker crashes, 46-78 retry attempts before eventually going green — real
job execution that is merely slow). This incident's signature is **zero job execution** (`jobs: []`, 0-2 second
completion, both `ubuntu-latest`-targeted AND self-hosted-targeted workflows affected identically) — that is the
distinct **account-level billing wall** signature already fully diagnosed and root-caused in the archived
`github_actions_billing_wall_2026_06_11.md` (and its 2026-06-23 recurrence note at the bottom of that doc). This doc is
a fresh dated recurrence record, not a new investigation — the archived doc's diagnosis, evidence method, and
recommended fix all still apply verbatim.

## What triggered this

Dispatched as a `ldr_qg_failure` escalation (`agt-913803`, slot 12) with instructions to reproduce `deployment-api`'s
`quality-gates-v2` failure locally, diagnose code-vs-test, fix the wrong side, ship. Reproduction instead showed the CI
job never executes at all (no code/test to diagnose).

## Evidence (collected 2026-07-29T20:04-20:58Z)

**`gh run view <id> --json jobs` returns `jobs: []`** for every failing run — GitHub rejected the run before
instantiating any job. Runtimes shrink toward zero across repeated attempts (41s → 13s → 2s → 1s → 0s), the same
signature as the archived incident's "0-step kill."

**Fleet-wide, not deployment-api-specific** (sampled 2026-07-29T20:50-20:58Z):

| repo                     | trigger                                         | conclusion            | when (UTC)                           |
| ------------------------ | ----------------------------------------------- | --------------------- | ------------------------------------ |
| deployment-api           | workflow_dispatch (agt-6af63d, slot 5, re-test) | `startup_failure`, 0s | 21:15:53                             |
| deployment-api           | workflow_dispatch (fresh test THIS session)     | `startup_failure`, 1s | 20:58:01                             |
| deployment-api           | workflow_dispatch                               | `startup_failure`, 1s | 19:43:45                             |
| deployment-api           | push                                            | `startup_failure`, 0s | 20:04:19                             |
| unified-api-contracts    | workflow_dispatch                               | `startup_failure`, —  | 20:50:44, 20:49:24                   |
| instruments-service      | workflow_dispatch                               | `startup_failure`, —  | 20:50:57                             |
| deployment-service       | push                                            | `startup_failure`, 0s | 20:45:21                             |
| market-tick-data-service | push                                            | `startup_failure`, 0s | 20:34:35 (and 4 more since 19:12:37) |
| agent-orchestrator       | push                                            | `startup_failure`, 0s | 20:04:33 (and 2 more since 19:25:09) |
| unified-trading-library  | push                                            | `startup_failure`, 0s | 19:34:04                             |
| features-service         | push                                            | `startup_failure`, 0s | 19:23:46                             |

**Onset window**: last confirmed real success across the fleet was ~16:31Z (unified-trading-library,
unified-api-contracts via workflow_dispatch). First real (non-startup) failure: deployment-api 18:22:13 (13s, genuine
early exit). Mass `startup_failure` onset: ~19:12-19:44Z. **Still active** — re-confirmed 21:15:53Z (a fresh
`workflow_dispatch` for deployment-api, escalation `agt-6af63d`/slot 5, identical `startup_failure`, 0s, `jobs: []`
signature) — an ongoing window of at least ~3-5h so far, no self-recovery yet.

**Ruled out** (each independently checked this session):

- Workflow YAML content: `deployment-api/.github/workflows/quality-gates-v2.yml` + the reusable
  `unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout` it calls — both parse cleanly,
  both unchanged across the entire failure window (last touch 09:00Z / 05:10Z respectively, well before onset).
- The coincident fleet-wide `main-backmerge-to-ldr.yml` template rollout (21/22 repos synced 15:49-20:07Z, same commit
  message per repo): timing correlation is coincidental, not causal — `unified-api-contracts` received its sync at
  15:52Z and then ran a clean **success** at 16:31Z, 40 minutes later, on the already-synced tree. A content-caused
  break would not produce a later clean success on the same (already-updated) content.
- Repo Actions permissions (`enabled: true, allowed_actions: all`), API rate limit (4732/5000 remaining), GitHub public
  status page (only an unrelated Copilot-model-provider incident, started 20:07Z, separate component) — all clean.
- Self-hosted runner contention: `deployment-api`'s caller passes `self_hosted_runner_labels: ""` (targets
  `ubuntu-latest`, GitHub-hosted) — box contention on the workspace's own self-hosted fleet cannot explain a
  GitHub-hosted-runner job failing to even schedule.
- My own token cannot read GH Actions billing (`GET users/IggyIkenna/settings/billing/actions` → 403 "Resource not
  accessible by personal access token") — **exact match** to the archived doc's finding that this class of check needs
  the account owner's own credentials; no worker-held token can confirm or clear this state.

## Why it matters

Every `quality-gates-v2`-gated promotion PR fleet-wide is blocked (LDR→staging, LDR→main, any PR-triggered gate) for as
long as the wall holds — this is a full fleet CI outage, not a single-repo issue. Per the archived doc's history, this
class has recurred at least 3 times before (2026-06-11, continuing 2026-06-12, recurring 2026-06-23) and both prior
recurrences self-recovered without any code change once the account-side condition cleared.

## Recommended decision

**Operator-only** (payment/account action, same as the archived precedent): check `github.com/settings/billing` → fix
the failed payment method or raise the Actions spending limit. No code change exists to apply from a repo-scoped worker.
Re-test after: `gh workflow run quality-gates-v2.yml --repo IggyIkenna/deployment-api --ref live-defi-rollout` should
return to a normal (non-zero-job) run.

## Todos

- [ ] [OPERATOR] P0. Check `github.com/settings/billing` (payment method / Actions spending limit) and clear the block.
      Re-test via `gh workflow run quality-gates-v2.yml --repo IggyIkenna/deployment-api --ref live-defi-rollout` after.
- [ ] [BACKEND] P2. This is the 3rd+ recurrence of this exact class (2026-06-11, 2026-06-23, 2026-07-29) — the archived
      doc's own P3 remediation item (spend telemetry / 50-80-95% budget alert, `BLOCKED-ON-DECISION` pending an
      operator-minted `Plan: read` billing-scoped token) was never unblocked. Worth revisiting now that it has recurred
      a third time: either mint that token so the workspace can self-detect this before it walls CI, or accept recurring
      manual operator intervention as the standing posture.
- [ ] [BACKEND] P3. `python-quality-gates-v2.yml`'s "Record CI status" step (`if: always()`) still dispatches a normal
      FAILING status on a 0-step billing-kill, per the archived doc's still-open P1 "outage-aware v2 status dispatch"
      remediation item — confirm whether that item shipped since 2026-06-11; if not, this wall is currently also
      generating `ldr_qg_failure` escalation spam (like this one) fleet-wide for every affected repo, which is wasted
      escalation-worker dispatch on a wall no worker can fix. Not actioned in this session (out of scope for a
      single-repo one-shot escalation worker) — flagging for the next fleet-wide CI hygiene pass.

## Evidence log

- `gh run view <id> --json jobs,conclusion,status` on deployment-api runs 30485690624 / 30490502075: `jobs: []`,
  `conclusion: startup_failure`.
- `python -m server.ci_status deployment-api` (agent-orchestrator venv):
  `{"blocked": true, "conclusion": "startup_failure", "qg_v2_state": "startup_failure", ...}`, reconfirmed live 20:58Z
  after a fresh dispatch.
- Cross-repo sample via `gh run list --repo IggyIkenna/<repo> --limit 3-15` across 8 repos (table above).
- `gh api users/IggyIkenna/settings/billing/actions` → 403 (token cannot read billing, matching archived precedent).
- `curl https://www.githubstatus.com/api/v2/incidents/unresolved.json` → only an unrelated Copilot-model-provider
  incident (20:07Z onset, different component) — no GitHub Actions-component incident posted.
- **2026-07-29T21:08Z (cicd escalation `agt-49fba5`, slot 4)**: corroborating data point, still active ~30-45min after
  this doc's last sample. Dispatched for `alerting-service` `ldr_qg_failure` (no PR, `#0`). Local
  `bash scripts/quality-gates.sh` on the exact escalation-cited HEAD (`86ca026`) passed clean (47s, all gates green,
  sentinel written) — no code/test defect exists to fix. The CI run at that same SHA (`30479581235`, workflow_dispatch,
  18:22Z) showed the earlier _partial_ signature (content-gate + both real QG slices — tests, checks — succeeded; only
  the lightweight `quality-gates-v2` aggregator job failed in 11s with logs since expired, `BlobNotFound`). Re-running
  it (`gh run rerun --failed`) now returns full-run `startup_failure` with zero jobs; a brand-new `workflow_dispatch`
  (`30491173482`) also `startup_failure` in ~1s, `gh api .../timing` → `{"billable":{},"run_duration_ms":1000}` — the
  same 0-billable-ms / `jobs:[]` signature as every other repo in the table above. Confirms the fleet-wide wall has
  escalated from partial (aggregator-only) to full startup_failure on `alerting-service` too, and that it was already
  mid-escalation (partial form) as early as 18:22Z — earlier than this doc's ~19:12-19:44Z mass-onset estimate for the
  repos it sampled. No code changed; `alerting-service` left clean on `live-defi-rollout`. Not re-filing a fresh
  `/blocked` — the standing `[OPERATOR] P0` todo above already covers this decision and multiple duplicate
  `alerting-service` `ldr_qg_failure` escalations are already queued/dispatched (`agt-9132b2`, `agt-d970e3`,
  `agt-2450f6` at query time) against the same unfixable wall.

- **2026-07-29T21:15Z (cicd escalation `agt-0518b0`, slot 12)**: corroborating data point for `client-reporting-api`
  `ldr_qg_failure` (`#0`, no PR). Local `bash scripts/quality-gates.sh` at HEAD `ed6586b8` run twice independently (once
  bare, once with explicit `$?` capture) — both clean, `exit=0`, 665 passed/4 skipped/71.56% coverage,
  `ALL QUALITY GATES PASSED`. The CI run that fired this escalation (`30479590370`, 18:22:09Z) shows the same _partial_
  signature already on record above: `content-gate` + both `qg-slices` (`checks`, `tests`) `success`, only the
  `quality-gates-v2` aggregator job failing in 12s with 0 recorded steps and an expired log blob. Re-dispatched fresh at
  21:15:33Z (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`) → still `startup_failure`, 0 jobs — the
  wall has not self-cleared, extending the confirmed-active window past every prior sample in this doc. Widened
  independently to `market-tick-data-service` and `deployment-service`: same signature across multiple recent commits
  each (not re-tabulated here — same conclusion as the table above). Note for corpus hygiene: a same-repo prior
  diagnosis (`agt-dfdd5b`, slot 5, ~21:00Z) exists but was logged into the sibling
  `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`'s Progress Log instead of here — its content (0-job
  `startup_failure`, billing-wall signature) matches this doc's mechanism, not that doc's self-hosted-contention
  mechanism, so a future reconciliation pass should probably relocate it; not doing that migration myself (out of scope
  for a one-shot escalation worker, and `check_line_caps.sh` / cross-doc migrations warrant their own pass). Not filing
  a fresh `/blocked` (same standing `BLK-21d55fb1` condition; avoiding the escalation-spam pattern the P3 todo above
  already flags). Pinged the authoring slot with the outcome. No code or workflow change made or needed; slot left clean
  on `live-defi-rollout`.

- **2026-07-29T21:23Z (cicd escalation `agt-d970e3`, slot 4)**: this session's own dispatch — `alerting-service`
  `ldr_qg_failure` (`#0`, no PR). Confirms the `agt-49fba5` entry above (same repo, same slot number, earlier session):
  local `bash scripts/quality-gates.sh` at HEAD `86ca026` passed clean via content-sentinel hit (14s,
  `ALL QUALITY GATES PASSED`) — no code/test defect to diagnose. Re-dispatched fresh (`workflow_dispatch` on
  `live-defi-rollout`, `30492162920`, 21:23:13Z) → still `startup_failure`, 0 jobs, 1s — wall has not self-cleared, now
  confirmed active ~3h+ past this doc's original onset estimate. Also independently reproduced fleet-wide via
  `gh run list` across `market-tick-data-service`, `instruments-service`, `unified-api-contracts` (all `startup_failure`
  at 21:10-21:17Z) — same signature, not repo-specific. Ran `actionlint` v1.7.12 against both the caller
  (`alerting-service/.github/ workflows/quality-gates-v2.yml`) and the reusable
  (`unified-trading-pm/.github/workflows/python-quality-gates-v2.yml`) — both clean (the only finding, "glue" runner
  label unknown, is expected/false-positive for an unregistered custom self-hosted label, not a real defect) — rules out
  a workflow-content regression as an independent check beyond the YAML-parse check already on record above. Not
  re-filing `/blocked` (same standing `BLK` condition, already covered by the `[OPERATOR] P0` todo). Pinged the
  authoring slot with the outcome. No code or workflow change made or needed; `alerting-service` left clean on
  `live-defi-rollout`.

- **2026-07-29T22:02Z (cicd escalation `agt-69e9e4`, slot 14)**: corroborating data point for
  `unified-trading-system-ui` `ldr_qg_failure` (`#0`, no PR). Fresh slot clone had no `node_modules` (first
  `bash scripts/quality-gates.sh` failed at `[0/6] ENVIRONMENT`/`[1/6] TYPE CHECK` with `tsc: not found` — an
  environment-setup artifact, not the reported CI defect); `pnpm install --frozen-lockfile` (21.4s) resolved it. With
  deps installed, local `bash scripts/quality-gates.sh` at HEAD `baf995ff` passed clean (186s, 286 tests passed,
  coverage 50.93% ≥ 40%, build passed, sentinel `.qg_last_passed_sha=baf995fff61000513c8910d68ed5cf6c0b623027` written
  matching HEAD) — no code/test defect exists to fix. `gh run view` on the escalation-triggering run (`30492984669`,
  workflow_dispatch, 21:35:57Z) and a fresh re-dispatch (`30494688036`, workflow_dispatch, 22:02:59Z, failed in 15s)
  both show the identical annotation: `"The job was not started because your account is locked due to a billing issue."`
  — exact match to this doc's signature, still active ~40min past the last sample above. Added
  `unified-trading-system-ui` to this doc's `repos:` frontmatter (newly-confirmed affected repo, not in the original
  sampled table). Not filing a fresh `/blocked` (same standing `[OPERATOR] P0` todo already covers this decision;
  avoiding the escalation-spam pattern the P3 todo above flags). Pinged the authoring slot with the outcome. No code or
  workflow change made or needed; `unified-trading-system-ui` left clean on `live-defi-rollout`.
