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

- 2026-07-28 (cicd agent, slot-2, escalation `agt-b195a8`, `ldr_qg_failure` on `alerting-service`, no PR): **3rd
  corroboration + per-repo fix**, same pattern. This repo is one of the two named directly in
  `/plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`'s live diagnosis ("long-running
  pytest processes for `alerting-service` and `fund-administration-service` (~2h wall-clock)"). Failing run
  `30306788671` (at `d6dfb30f`, the repo's own Phase-7 rollout commit) ran **2h44m27s** before failing —
  `QG slice (tests)` sat on step "Run quality gates (leg tests)" for 64+ min with no completion recorded, consistent
  with the job being killed mid-hang rather than failing on its merits. A same-config auto-retry (`30310510143`) then
  queued/ran for **2h22m47s** and actually went GREEN (self-recovered once shared-VM iowait eased from the documented
  66-93% peak down to ~24% by the time I checked — confirmed live on `i-172-31-5-118` itself: `uptime`/`top` showed load
  avg ~21, iowait 24.3%, plus the actual `alerting-service` `quality-gates.sh` PID visible mid-run in the process
  table). Since the wall had already self-resolved by the time I started, I canceled the redundant still-queued 3rd
  retry (`30317509169`) to free the sole shared runner, then applied the same precedented fix regardless (the underlying
  capacity issue is still open per this doc's own P2/VERIFY findings, so leaving the flip in place would just hang the
  next commit): reverted `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via the same hand-edit pattern +
  `quickmerge --agent` — `alerting-service@0fc5cab` (local `quality-gates.sh` passed in 57s). Verified live: triggered a
  fresh run (`30318470827`) post-fix, confirmed via `gh api .../jobs/<id>` it ran on `labels: ["ubuntu-latest"]` (not
  self-hosted), and it completed **green in 2m33s total** (`QG slice (tests)` 1m40s) — back to normal, no contention.
  Did not touch the shared allowlist file, any other repo, or the VM — same scope boundary as the prior two fixes. No
  open repo-blockers existed for this repo at the time.

- 2026-07-28 (cicd agent, slot-3, escalation `agt-5b9083`, `ldr_qg_failure` on `client-reporting-api`, no PR): **4th
  corroboration + per-repo fix**, same pattern, detected by `ldr-ci-monitor` at commit `ab32fba4` (the repo's own "Phase
  7 + quality-gates-v2 self-host rollout for client-reporting-api" commit). Failing run `30306795757` ran **2h54m8s**:
  `QG slice (checks)`'s "Run quality gates (leg checks)" step sat `in_progress` from 22:33:34 to 23:29:06 (55m32s)
  before being marked `cancelled` — not a genuine assertion failure. Two further `workflow_dispatch` retries had already
  auto-queued behind it on the sole shared runner before I picked up the escalation: `30310512581` (its
  `QG slice (tests)` alone took 25m3s; `checks` was still `in_progress` when I checked) and `30317512237` (still
  `pending`, never got a runner). Confirmed NOT a code regression: a clean local `quality-gates.sh` run at HEAD
  (`0881465`) passed in 69s. Canceled both stuck/queued retries to free the sole runner, then applied the same
  precedented fix: reverted `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via the same hand-edit pattern +
  `quickmerge --agent` — `client-reporting-api@4a4ba6e`. Verified live: triggered a fresh run (`30319083342`) post-fix,
  confirmed via `gh api .../jobs` both `QG slice (checks)` and `QG slice (tests)` ran on `labels: ["ubuntu-latest"]`
  (not self-hosted), and it completed **green in ~2m total** (`checks` 1m40s, `tests` 1m56s) — back to normal, no
  contention. Did not touch the shared allowlist file, any other repo, or the VM — same scope boundary as the prior
  three fixes. No open repo-blockers existed for this repo at the time.

- 2026-07-28 (cicd agent, slot-8, escalation `agt-71f135`, `ldr_qg_failure` on `e2e-testing`, no PR): **5th
  corroboration + per-repo fix**, same pattern, detected by `ldr-ci-monitor` at commit `12846a43` (the repo's own "Phase
  7 + quality-gates-v2 self-host rollout for e2e-testing" commit). The escalating run `30306809955` failed on the
  classic signature (`git status` subprocess `TimeoutExpired` (40s) mid-build of the `unified-api-contracts` editable
  dep). A later retry (`30314443597`, after the reusable workflow's independent
  `SETUPTOOLS_SCM_SUBPROCESS_TIMEOUT`/`VCS_VERSIONING_SUBPROCESS_TIMEOUT=180` mitigation had already landed) got past
  the timeout but still queued **712s** on `[qg-governor] all 4 tokens busy` before failing on an unrelated genuine STEP
  5.105 GCS-CLI-baseline break that a separate commit (`420e834`) fixed independently — confirms the runner-capacity
  symptom and a real code issue can coexist in the same window without one masking the other. This repo's own runner
  pool showed only 1 registered runner (`glue-ip-172-31-5-118-1`), and a subsequent `workflow_dispatch` run
  (`30317519815`) sat `pending` 16+min with zero jobs materialized while that sole runner was busy elsewhere — canceled
  to free it. Applied the same precedented fix: reverted `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via
  the same hand-edit pattern + `quickmerge --agent` — `e2e-testing@a881a43`. (Mid-fix, this worker's own session was
  reaped by the WorkerLivenessWatchdog for going heartbeat-silent >15min while babysitting the quickmerge subprocess via
  repeated `ScheduleWakeup` calls instead of the AO `/api/slots/N/progress` endpoint — worth flagging as a recurring
  trap for any one-shot agent backgrounding a long-running shell command: `ScheduleWakeup` paces the _skill loop_, it
  does not itself satisfy the liveness watchdog. The backend's dead-session recovery correctly preserved the
  committed-but-unpushed fix on `origin/wip-preserve/orchestrator-slot-8-5e97b9e` rather than losing it; recovered by
  cherry-picking the real fix commit — skipping an unrelated auto-committed cache-artifact commit stacked on top — back
  onto a fresh `live-defi-rollout` and re-shipping with a self-heartbeating wrapper script.) Verified live: triggered a
  fresh run (`30326015026`) post-fix, confirmed via `gh api .../jobs` every job ran on `labels: ["ubuntu-latest"]` (not
  self-hosted), and it completed **green in ~3m02s** (`checks` 1m54s, `tests` 2m24s) — back to normal, no contention;
  GH's own "QG Recovered" Slack step fired automatically. Did not touch the shared allowlist file, any other repo, or
  the VM — same scope boundary as the prior four fixes. No open repo-blockers existed for this repo at the time.

- 2026-07-28 (cicd agent, slot-2, escalation `agt-f11cae`, `ldr_qg_failure` on `unified-trading-library`, originally
  filed against promotion PR #674): **6th corroboration + per-repo fix**, same pattern. This repo's own Phase-7 rollout
  commit `5f48d47f` ("feat(ci): Phase 7 + quality-gates-v2 self-host rollout for unified-trading-library") landed in the
  same ~21:40-21:55 UTC 2026-07-27 window as the other 18. PR #674 (pinned to `5f48d47f`) failed `QG slice (tests)` with
  3 genuine `pytest-timeout` failures on otherwise-fast tests
  (`test_utc_aligned_scheduler.py::test_first_callback_fires_at_aligned_boundary_plus_grace` >60s,
  `test_streaming_writer.py::TestDynamicFlush::test_flush_triggered_by_memory_pressure` >60s,
  `synthetic/test_synthetic_harness.py::test_harness_auto_resolves_params_from_specs` >300s; 6801 passed, 3 failed) —
  consistent with CPU contention rather than a code regression. #674 was auto-superseded by #675 (pinned to a later LDR
  commit `080a84a0`, an unrelated consolidator fix already landed) before I could act on it; #675's own `pull_request`
  quality-gates-v2 run (`30318034158`) hit the identical `QG slice (tests)` timeout failure at the SAME LDR head,
  confirming the flakiness was runner-capacity, not the intervening commit. Runner check
  (`gh api repos/IggyIkenna/unified-trading-library/actions/runners`) showed exactly 1 registered runner
  (`glue-ip-172-31-5-118-1`), same shared-VM signature as the other 5. Applied the same precedented fix: reverted
  `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via the same hand-edit pattern + `quickmerge --agent` —
  `unified-trading-library@7677ff71`. Verified live: triggered a fresh run (`30326782451`) post-fix; both
  `QG slice (tests)` and `QG slice (checks)` completed green, aggregate `quality-gates-v2` succeeded in ~6m38s total —
  back to normal, no contention. Did not touch the shared allowlist file, any other repo, or the VM — same scope
  boundary as the prior five fixes. No open repo-blockers existed for this repo at the time (`GET /api/repo-blockers` →
  `{"open":[]}`).
