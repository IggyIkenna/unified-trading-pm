---
doc_type: issue
title:
  Fleet-wide quality-gates-v2 self-hosted-runner flip already landed on 19/24 repos today, ahead of the documented
  operator-paced capacity plan — multiple repos' promotion gates hung for 1-2.5+ hours on a severely oversubscribed
  shared 16-vCPU VM
summary: >-
  Responding to an `ldr_qg_failure` escalation for execution-service (commit 535ab998, a docs-only commit — ruling out a
  code regression), root-caused the actual failure to a `subprocess.TimeoutExpired` (git status timed out after 40s)
  inside hatch-vcs version resolution while building the `unified-api-contracts` editable dependency, during the
  `qg-slices (checks)` job on the repo's newly-self-hosted `quality-gates-v2` runner. Investigating further surfaced a
  much larger problem: `github_actions_operator_gated_followups_2026_07_17.md`'s own P1 INFRA todo says the fanout of
  the self-hosted-runner flip from the verified agent-orchestrator canary to the other 23 repos is "NOT started ...
  deliberately paused ... for an operator scope/pacing decision" — but a live grep of `scripts/workflow-templates/
  self-hosted-qg-repos.txt` (the allowlist `rollout-workflow-templates.sh`'s `get_qg_runner_labels()` reads to decide
  whether a repo's `quality-gates-v2.yml` gets `self_hosted_runner_labels` rendered in) already lists ALL 24 repos, and
  19 of them already have the flip LIVE in their actual per-repo `quality-gates-v2.yml` (confirmed via direct file grep
  across every slot-16 sibling clone). Each of ~9 sampled repos shows exactly 1 runner actually registered (`gh api
  repos/IggyIkenna/<repo>/actions/runners`) — not the "2-runner pool" some rollout commit messages claimed — and ALL of
  them are colocated on the SAME shared `i-0c9b283b31d6b5ca7` 16-vCPU/64GB EC2 instance that also hosts
  agent-orchestrator's 3-runner canary pool and PM's original 8-runner pool. Two repos checked directly
  (execution-service, deployment-api) both had a `quality-gates-v2` run stuck `queued`/`in_progress` for 1.5-2.5+ hours
  — consistent with severe CPU/disk contention across ~20+ colocated self-hosted-runner processes fighting over 16
  vCPUs, not isolated flakes. The allowlist file's OWN header comment states the HARD RULE this violates: "a repo goes
  on this list ONLY after its own self-hosted runner pool is registered + verified healthy ... Adding a repo here before
  its pool exists hangs that repo's promotion gate forever."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    execution-service,
    deployment-api,
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-service,
    e2e-testing,
    features-service,
    fund-administration-service,
    greeks-service,
    ibkr-gateway-infra,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    strategy-service,
    system-integration-tests,
    trading-agent-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity, phase-7, workflow-templates, incident, cross-repo]
related:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-27
priority: P0
parent_epic: infrastructure_master
source: "cicd agent, slot-16, escalation agt-2cbf1d (execution-service ldr_qg_failure), 2026-07-27"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# Fleet-wide quality-gates-v2 self-hosted-runner capacity crisis (2026-07-27)

## What I found

**Trigger**: dispatched as a one-shot `cicd` worker (escalation `agt-2cbf1d`) to fix an `ldr_qg_failure` wall on
`execution-service` at commit `535ab998bbe7fea38e7d261b1e47f90a59d810a9`. That commit is **docs-only** (a Phase-3 S5.11
redirect/slim of markdown docs, zero code changed) — ruling out a code regression as the cause.

**Immediate root cause (execution-service, run `30306813710`)**: the `QG slice (checks)` job failed with:

```
subprocess.TimeoutExpired: Command ['git', '--git-dir', '.../unified-api-contracts/.git', 'status', '--porcelain',
'--untracked-files=no'] timed out after 40 seconds
TypeError: TimeoutExpired.__init__() missing 1 required positional argument: 'timeout'
```

(the second error is hatchling's own error-wrapping bug masking the real cause — `raise type(e)(message) from None` on a
`TimeoutExpired` whose constructor needs more than a message). The real problem: a plain `git status` on a
shallow-cloned sibling dependency took **over 40 seconds** — consistent with severe CPU/disk contention on the runner,
not a code or dependency-version issue.

**Why**: `execution-service`'s `quality-gates-v2.yml` was flipped to
`self_hosted_runner_labels: '["self-hosted","glue"]'` today via commit `4cd5b5c08c7c` ("Phase 7 + quality-gates-v2
self-host rollout for execution-service"), routing its CPU-heavy `qg-slices` job onto a self-hosted runner pool.

**Escalating the investigation — this is NOT execution-service-specific**:

1. `plans/active/github_actions_operator_gated_followups_2026_07_17.md`'s own P1 INFRA todo (still unchecked as of this
   write-up) says: _"Fan out Phase 7 + the quality-gates-v2 self-host flip from the now-fully-verified
   agent-orchestrator canary to the remaining 23 repos ... NOT started — this is a much larger-aggregate-risk action ...
   and was deliberately paused here for an operator scope/pacing decision."_
2. But `scripts/workflow-templates/self-hosted-qg-repos.txt` (the live allowlist `rollout-workflow-templates.sh`'s
   `get_qg_runner_labels()` reads when rendering `quality-gates-v2.yml.tmpl`) already lists **all 24 repos** in the
   fleet.
3. Direct grep of every slot-16 sibling repo clone's actual `.github/workflows/quality-gates-v2.yml` shows **19 of 24
   already have `self_hosted_runner_labels` live** (only `deployment-ui` and `unified-trading-system-ui` don't yet — the
   JS/UI repos, likely a different template path). All 19 landed via near-identical
   `feat(ci): Phase 7 + quality-gates-v2 self-host rollout for <repo>` commits within roughly the same ~21:40-21:55 UTC
   window today (2026-07-27) — e.g. `execution-service@4cd5b5c0` (21:53), `deployment-api@c19edcc2` (21:46).
4. Runner registration reality check (`gh api repos/IggyIkenna/<repo>/actions/runners`) on 9 sampled repos
   (execution-service, deployment-api, alerting-service, instruments-service, ml-service, unified-api-contracts,
   market-tick-data-service, unified-trading-library, agent-orchestrator): **every one shows exactly 1 runner** except
   agent-orchestrator's verified 3 (2 glue + 1 writer). Several rollout commit messages claim "this repo's own 2-runner
   pool ... was verified online before this rollout" — only 1 is online now. All of these runners
   (`glue-ip-172-31-5-118-1[-N]`) are registered on the **same physical EC2 instance** `i-0c9b283b31d6b5ca7` (resized to
   `m8i.4xlarge`, 16 vCPU / 64GB, per the same plan doc), which ALSO hosts PM's original 8-runner pool. That's ~20+
   separate self-hosted-runner processes competing for 16 vCPUs.
5. Live symptom confirmed on 2 repos directly: `execution-service` run `30310511700` sat `queued` for **1h34m**;
   `deployment-api` run `30306799237` sat `queued` for **2h28m**. A separate `execution-service` promotion-PR run
   (`30309965212`, PR #501) had its `checks` job stuck `in_progress` for **>90 minutes** (historical successful
   duration: 4-32 min) before I canceled it to free the sole runner and unblock the retry queue.

**The allowlist file's own header comment states the exact failure mode this violates**:

> HARD RULE: a repo goes on this list ONLY after its own self-hosted runner pool is registered + verified healthy ...
> Adding a repo here before its pool exists hangs that repo's promotion gate forever.

19 repos are on the list without a remotely adequate pool. This is not a future risk — it is an **active, ongoing
incident** causing hours-long promotion-gate stalls fleet-wide, discovered only because one repo's wall happened to
escalate to a `cicd` worker.

## What I fixed (within my scoped escalation only)

- Canceled the hung `execution-service` run `30309965212` to free the sole shared runner for my repo's retry queue.
- Reverted **only** `execution-service`'s `self_hosted_runner_labels` line back to empty (→ `ubuntu-latest` default) via
  a hand-edit + `quickmerge --agent` (this specific field is a documented per-repo override, not part of the
  templated-identical content — precedented by the agent-orchestrator canary's own "hand-set, TEMPORARY" pattern in the
  followups plan). Left the same commit's thin push/repository_dispatch glue-workflow flips (`main-backmerge-to-ldr`
  etc.) in place — those are low-CPU and match Phase 7's own stated safe scope.
- Did **not** touch any of the other 18 already-flipped repos, the shared allowlist file, or the VM itself — that is a
  cross-repo capacity-planning decision outside a single `ldr_qg_failure` escalation's scope, and multiple other
  slots/agents may be actively working in this space (see the related workflow-template-drift issue below).

## Why it matters

- **Every one of the 19 already-flipped repos' promotion gates (`quality-gates-v2`, a REQUIRED check) is at risk of
  multi-hour stalls right now**, not just execution-service — this blocks LDR→main promotion fleet-wide, not just one
  repo's unrelated work.
- The allowlist populating ahead of the paced-fanout decision, combined with the workflow-template `.tmpl` mechanism
  already being wired to consume it (`get_qg_runner_labels()` → `{{QG_RUNNER_LABELS}}` in `quality-gates-v2.yml.tmpl`),
  means **any future routine `rollout-workflow-templates.sh` run touching this template for ANY of the remaining
  un-flipped repos would silently arm the same landmine for them too**, with no additional authorization step in the
  way.
- Related but distinct from `workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md` (multiple slots
  racing on the SAME workflow files, filed ~19:29-20:09 UTC) — that issue is about **coordination churn** during the
  agent-orchestrator canary. This issue is about **capacity**: the fanout itself already happened despite being marked
  "not started," and the shared VM cannot serve this many repos' CI load concurrently.

## Recommended fix path

- [ ] [OPERATOR] P0. Decide fleet posture right now: (a) revert the flip fleet-wide back to `ubuntu-latest` for every
      repo that doesn't have a verified, adequately-sized, DEDICATED runner pool (safest, matches the paused-plan's own
      intent), or (b) approve keeping some subset self-hosted but immediately capacity-plan + provision real
      per-repo/per-pool runner counts against the 16 vCPU ceiling (the followups plan itself says "23× that is NOT a
      straight multiply, size down for low-traffic repos" — that sizing was never done before the flip landed).
- [ ] [SCRIPT] P0. Whichever way (a)/(b) goes, remove the un-provisioned repos from
      `scripts/workflow-templates/self-hosted-qg-repos.txt` immediately so the file's own HARD RULE is actually true
      again, and so no future template rollout can silently re-arm this for a repo without a real pool.
- [ ] [DATA] P1. Audit every repo currently in the allowlist for its actual live runner count
      (`gh api repos/IggyIkenna/<repo>/actions/runners`) vs. what its own rollout commit message claimed, and check each
      repo's `quality-gates-v2` run history for multi-hour stalls
      (`gh run list --branch live-defi-rollout     --repo IggyIkenna/<repo>` — anything `queued`/`in_progress` well past
      its own historical run duration is a live symptom). Fix (revert to ubuntu-latest) each affected repo the same way
      I did for execution-service, or route through whichever fleet-wide mechanism the operator picks above.
- [ ] [VERIFY] P1. Once resolved, re-check `i-0c9b283b31d6b5ca7`'s actual runner-process count matches an intentional,
      capacity-planned total (not ~20+ processes on 16 vCPUs), and confirm no repo's `quality-gates-v2` sits
      `queued`/`in_progress` past its own historical p95 duration.

## Evidence

- `execution-service` failing run: https://github.com/IggyIkenna/execution-service/actions/runs/30306813710
- `execution-service` hung promotion-PR run (canceled): `30309965212` (PR #501)
- `deployment-api` stuck queue: run `30306799237`, queued 2h28m+ at time of writing
- Allowlist: `scripts/workflow-templates/self-hosted-qg-repos.txt` (24 entries)
- Template wiring: `scripts/workflow-templates/rollout-workflow-templates.sh` `get_qg_runner_labels()` (line ~207-214),
  `scripts/workflow-templates/quality-gates-v2.yml.tmpl` line 67
- Fix shipped: `execution-service@<see quickmerge output>` (revert of `self_hosted_runner_labels` only)

## Progress Log

- 2026-07-28 (cicd agent, slot-4, escalation `agt-70dbed`, `ldr_qg_failure` on `batch-live-reconciliation-service`#255
  LDR→main promotion PR): **2nd corroboration + per-repo fix**, same pattern as execution-service. Failing run
  `30305786014` ran **51m18s** (vs normal 8-15min): `QG slice (checks)` typecheck hit a hard `timeout` (exit=124) after
  being admitted, then `lint-codex` got `Terminated`; `QG slice (tests)` queued behind `[qg-governor] all 4 tokens busy`
  for 6+ minutes and never started before also being `Terminated`. Confirmed NOT a code regression: a clean local
  `quality-gates.sh` run at the same HEAD (`806fba72`) passed in 58s. This repo's flip landed via `1c2b5ba` ("Phase 7 +
  quality-gates-v2 self-host rollout for batch-live-reconciliation-service"), same ~21:40-21:55 UTC 2026-07-27 window as
  the other 18. Applied the same fix as execution-service: reverted `self_hosted_runner_labels` to empty (→
  `ubuntu-latest`) via hand-edit (documented per-repo override field, not templated-identical content) +
  `quickmerge --agent` — `batch-live-reconciliation-service@2f591901160e2edbadf250f11a2256c25f2540c7`. Did not touch the
  shared allowlist file, any other repo, or the VM — same scope boundary as the execution-service fix. This repo is also
  independently named in `/plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`'s P2 todo
  (its SIT `cross-repo-invariants` dispatch blew a 90s poll budget same window) — one shared root cause (oversubscribed
  `i-0c9b283b31d6b5ca7`) manifesting across multiple symptoms for this repo.
