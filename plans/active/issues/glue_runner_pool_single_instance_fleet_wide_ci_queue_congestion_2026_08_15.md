---
doc_type: issue
title:
  The fleet's entire quality-gates-v2 self-hosted-runner pool is ONE instance — multiple repos' CI queued/stuck 20-30+
  minutes simultaneously during a 2026-08-15 /ci-reconcile sweep
summary: >-
  Found live during a 2026-08-15 /ci-reconcile sweep while verifying a fix (unified-api-contracts@a4ba9c6f05,
  pacifica_solana containment gap) had actually resolved e2e-testing's red quality-gates-v2. Every quality-gates-v2.yml
  QG-slice job fleet-wide runs on `runs-on: [self-hosted, glue]` (confirmed via
  e2e-testing/.github/workflows/quality-gates-v2.yml lines 104/159/189, and this is the shared template so it applies
  fleet-wide). `gh api repos/IggyIkenna/e2e-testing/actions/runners` shows exactly ONE registered runner
  (`glue-ip-172-31-3-59-1`, status=online, busy=true) — `total_count: 1`. During this sweep's ~30-minute observation
  window, a manually re-triggered e2e-testing run (31857318274) sat with its "QG slice (tests)" job in `queued` the
  entire time and "QG slice (checks)" in `in_progress` without completing; simultaneously, market-tick-data-service was
  `queued` (since 01:45Z), and features-service's run had been `in_progress` since 01:31Z (30+ min, well past the ~3-4
  min duration a full QG run normally takes per this same sweep's earlier observations). A single self-hosted runner
  serving quality-gates-v2 for the ENTIRE ~25-repo fleet is either (a) a severe under-provisioning relative to the
  fleet's actual concurrent CI volume, or (b) evidence that the runner pool is SUPPOSED to have more instances and most
  of them are down/deregistered (a scaling-group or autoscaler failure). Neither could be distinguished from this
  session — diagnosing further needs the host-level view (`systemctl status` glue-runner services, autoscaling-group
  desired vs. actual instance count, `glue-runner-health-monitor` / `glue-pool-starvation-monitor` workflow's own recent
  verdicts) which requires AWS SSM access this session's identity (`ikenna-worker` IAM user) does not have —
  `ssm:SendCommand` returned `AccessDeniedException`, and the user is not authorized to `sts:AssumeRole` into the
  self-service-blessed `uts-orchestrator-epic-role` either (confirmed live, both calls attempted and denied). This is
  the SAME coverage gap as this sweep's §0c host-dispatched-watchdog sweep (also blocked by the identical IAM gap) — see
  this doc's "What's NOT confirmed" section.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-reconcile, glue-runner, self-hosted-runners, capacity, fleet-wide, coverage-gap]
related: []
created: 2026-08-15
source: ci_reconcile-sweep-2026-08-15
author: ci_reconciler
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    .github/workflows/glue-runner-health-monitor.yml,
    e2e-testing/.github/workflows/quality-gates-v2.yml,
  ]
drift_direction: advance-code
depends_on: []
---

# Glue-runner pool is a single instance — fleet-wide CI queue congestion observed live

## What's confirmed

- `runs-on: [self-hosted, glue]` on every quality-gates-v2 QG-slice job (e2e-testing's copy checked; this is a
  template-derived workflow, so the same `runs-on` almost certainly applies fleet-wide — not independently confirmed on
  every repo this session).
- `gh api repos/IggyIkenna/e2e-testing/actions/runners` → `total_count: 1`, the single runner `glue-ip-172-31-3-59-1`
  shows `status: online, busy: true`.
- Live congestion observed over a ~30-minute window (2026-08-15, ~01:31Z-02:04Z):
  - e2e-testing run `31857318274`: "QG slice (tests)" stuck `queued` for the entire window; "QG slice (checks)"
    `in_progress` without completing.
  - `market-tick-data-service`: `queued` since 01:45Z.
  - `features-service`: `in_progress` since 01:31Z (30+ min — a normal full QG run completes in ~3-4 min per this same
    sweep's earlier direct observation of e2e-testing's own failed run, `31856314351`, which ran start-to-finish in
    under 4 minutes).
- No existing `plans/active/issues/*glue*capacity*` or similarly-named doc found before filing this one.

## What's NOT confirmed (the actual root cause)

- Whether 1 runner is the INTENDED pool size (in which case this is a genuine under-provisioning finding — the fleet
  clearly generates more concurrent QG demand than 1 runner can serve) or whether more runners are SUPPOSED to be
  registered and have crashed/deregistered/failed to scale up (in which case this is an outage, not a capacity-planning
  gap).
- The glue-runner host's own live state (`systemctl status glue-runner*.timer/.service`, `journalctl`) — blocked by the
  AWS IAM gap below.
- Whether `glue-runner-health-monitor` / `glue-pool-starvation-monitor` (both catalog-listed as `manual`-trigger-only,
  not `schedule`-triggered per this sweep's §0b catalog check, dispatched instead via `ci-health.yml`'s
  `dispatch:glue-runner-health` — a host-triggered `repository_dispatch`, part of §0c's population) already caught and
  is actively working this, or has posted anything about it — this sweep's §0c host-dispatched-watchdog check could not
  run (same IAM gap).

## Why this couldn't be root-caused further this session

AWS identity active this session: `arn:aws:iam::427895769566:user/ikenna-worker`. Both self-service paths failed live:

```
$ aws ssm send-command --instance-ids i-042a6332509482556 ...
AccessDeniedException: User: .../ikenna-worker is not authorized to perform: ssm:SendCommand

$ aws sts assume-role --role-arn arn:aws:iam::427895769566:role/uts-orchestrator-epic-role ...
AccessDenied: User: .../ikenna-worker is not authorized to perform: sts:AssumeRole
```

Per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, the self-manage-own-policies grant is scoped
ONLY to `uts-orchestrator-epic-role` itself (assumed via EC2 instance profile, not by an arbitrary IAM user assuming
it), so `ikenna-worker` cannot self-grant its way into this — per the RULES.md §5 exception, a permission gap on a
genuinely different, non-self-service identity is a real access gap, not something to route around.

## Suggested next step (for whoever picks this up)

1. From a session that has SSM access to `i-042a6332509482556` (or whichever host actually runs the glue-runner service
   — confirm this is the right host, this doc reuses the address named in the ci-reconcile skill's §0c for a DIFFERENT
   watchdog and has not independently verified it hosts `glue-ip-172-31-3-59-1` specifically): `systemctl status` the
   glue-runner service/timer, check for a crash loop, and check the intended autoscaling-group desired-capacity if one
   exists.
2. If 1 instance is confirmed as the intentional design: this is a capacity-planning finding — either accept the latency
   (queue depth during peak fleet CI activity) or provision more runner capacity.
3. If more runners are supposed to exist: root-cause why they're not registered/online (crash loop, IAM/registration
   token expiry, image/AMI issue) and restore them.
4. Re-run this sweep's e2e-testing verification run (`31857318274`, or a fresh trigger) once the pool is healthy, and
   confirm the pacifica_solana containment fix (unified-api-contracts@a4ba9c6f05) actually goes green end-to-end — the
   fix itself is already verified correct via a full local `quality-gates.sh` run on unified-api-contracts (13198
   passed, 0 failed, 672 skipped, 5 xfailed), so a subsequent e2e-testing green is expected, not a further diagnosis.

## Progress Log

- 2026-08-15 (ci_reconciler, slot 21): Filed after observing 30+ minutes of fleet-wide CI queue congestion behind a
  single busy self-hosted glue runner while verifying an unrelated fix's downstream CI. Root cause not reachable this
  session (AWS IAM gap, confirmed live, matches the sweep's §0c host-dispatched-watchdog coverage gap). No code changed.
- **context-scout 2026-08-15**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:c92f713e54e5825d]: KEEP-NA, valid — genuinely open live-infra investigation blocked by a real IAM gap (ssm:SendCommand/sts:AssumeRole denied for ikenna-worker, confirmed live). No tracked checkboxes exist yet (prose-only follow-on steps) — a separate hygiene gap outside this audit's scope.
- **cicd escalation agt-3378e5 2026-08-17 ~13:53Z (slot 8)**: NEW manifestation of this same single-runner capacity gap
  — `codeload.github.com` 429 (Too Many Requests) downloading `actions/checkout@v4` on `glue-ip-172-31-3-59-1`, not a
  queue/disk/cache-hang symptom. deployment-service promote PR #1036 (LDR→main, head 782975f4, wall agt-3378e5)
  quality-gates-v2 failed 3x in a row (run 32034350306, attempts 1-3, ~13:18Z/13:46Z/13:51Z), every attempt dying at
  the SAME "Set up job" step of the "QG slice (tests)" job with `Failed to download archive
  '.../actions/checkout/tar.gz/11d5960a...'` after 3 backoff retries (~22s/~13-29s). Confirmed NOT a code break: full
  local `bash scripts/quality-gates.sh` on the exact PR head sha (782975f4) passed clean (`✅ ALL QUALITY GATES PASSED
  (261s)`, only pre-existing warn-tolerance ratchet warnings). Confirmed fleet-wide correlation: execution-service,
  features-service, instruments-service, and strategy-service all also failed quality-gates-v2 in the same ~13:18-13:31Z
  window (`gh run list --workflow quality-gates-v2.yml`), while other repos (alerting-service, unified-trading-library)
  succeeded either side of that window — consistent with a burst of concurrently-dispatched promote-PR CI runs (likely
  the `ldr-to-main-promote-fleet.yml` `*/30` tick) all landing on the SAME single glue runner and its action-download
  cache not persisting the `actions/checkout` tarball between jobs, so every job re-downloads it fresh and the
  cumulative per-IP request volume trips GitHub's codeload rate limit. Re-confirmed the IAM gap this doc already
  names is unchanged: `aws sts get-caller-identity` = `arn:aws:iam::427895769566:user/ikenna-worker` (same identity as
  the 2026-08-15 finding); `aws ssm describe-instance-information` still `AccessDeniedException`. No code fix exists
  or is needed on `deployment-service` — this wall will clear once the runner's action-download congestion drains (or
  the runner gets a persistent `_work/_actions` cache so it stops re-fetching `actions/checkout` every job). Provenance:
  cicd escalation agt-3378e5, deployment-service#1036.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries), unchanged.

- **cicd escalation agt-8c192b 2026-08-17 ~14:07Z (slot 4)**: THIRD manifestation of the same single-glue-runner
  congestion — instruments-service `live-defi-rollout` quality-gates-v2 red at commit `a1754003466946c0e5b7b71ad4a5b58`
  (run 32034365453, wall_type=ldr_qg_failure, `#0` no PR). Root cause identical to agt-3378e5 above: job logs (fetched
  via the `/actions/runs/{id}/logs` zip endpoint — the per-job `/jobs` and `/check-runs` endpoints both 403 for this
  session's GH_PAT, "Resource not accessible by personal access token", an Actions-permission gap on the PAT distinct
  from its already-granted Workflows:read/write scope) show "QG slice (tests)" dying in "Set up job" downloading
  `actions/checkout@v4` from `codeload.github.com` → 429 after 3 backoff retries. Confirmed NOT a code break: full local
  `bash scripts/quality-gates.sh` on the exact HEAD sha (a1754003) passed clean (`✅ ALL QUALITY GATES PASSED (118s)`,
  sentinel written for that exact sha). Re-triggered the workflow live (`gh workflow run quality-gates-v2.yml --ref
  live-defi-rollout`, run 32038587130) to double-check — it ALSO failed, same signature (`codeload.github.com` 429 on
  `actions/checkout`/`actions/setup-python` during "Set up job"), confirming the congestion is still ongoing ~1h after
  agt-3378e5's finding, not a one-off blip that already cleared. No code fix exists or is needed on instruments-service.
  This escalation will retry-poll for a clean quality-gates-v2 run and close once the runner congestion drains — it
  does not duplicate the [OPERATOR] follow-up already tracked below. Provenance: cicd escalation agt-8c192b,
  instruments-service (no PR).

- **cicd escalation agt-723f23 2026-08-17 ~14:31Z (slot 3)**: FOURTH manifestation of the same single-glue-runner
  congestion — features-service `live-defi-rollout` quality-gates-v2 red at commit `6392c07ceb43a2bc7e3f8956d5bc080524ed2a78`
  (original wall run 32034350333, wall_type=ldr_qg_failure, `#0` no PR; a subsequent ldr-ci-monitor re-check run
  32038016611 at 14:08:59Z also failed). Confirmed NOT a code break: full local `bash scripts/quality-gates.sh` on the
  current live-defi-rollout HEAD (20d71ed0, one commit past the escalating commit) passed clean (exit 0, verified via
  the process's own `$?` — the captured log merely stopped mid-stream after STEP 5.104 with no failure banner, an
  unflushed-buffer artifact of the backgrounding wrapper, not a real crash). The failing commit itself only bumped the
  Dockerfile's pinned `BASE_IMAGE_DIGEST` (both old and new digests verified resolvable in Artifact Registry via
  `gcloud artifacts docker images describe`); a full read of the reusable `python-quality-gates-v2.yml` confirms this
  digest/Dockerfile is not referenced anywhere in the CI gate, ruling out any causal link. Re-triggered live
  (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`, run 32039215897) to get a clean signal against
  current HEAD — it ALSO failed. Job logs (fetched via the `/actions/runs/{id}/logs` zip endpoint, same as agt-8c192b —
  the per-job `/jobs` and `/check-runs` endpoints both still 403 for this session's GH_PAT) show the identical
  signature: "QG slice (tests)" Set up job dying on `actions/checkout@v4` download — `codeload.github.com` 429 (Too
  Many Requests), then a 502, then a third 429, hard-failing after 3 backoff attempts (14:31:04Z-14:32:30Z). Confirms
  the congestion is STILL ongoing ~40min after agt-8c192b's finding — 4 distinct repos hit within ~1.5h
  (deployment-service, instruments-service, features-service, plus the original 2026-08-15 e2e-testing/
  market-tick-data-service queueing). No code fix exists or is needed on features-service; not retrying further from
  this session (each retry adds another `actions/checkout` download to the same congested IP, working against the
  fix rather than toward it) — leaving this for the existing `[OPERATOR]` follow-up below and the next external
  ldr-ci-monitor check. Also confirmed (informational, not actioned): this session's AWS identity (`ikenna-worker`)
  hit the same `ssm:SendCommand AccessDeniedException` on `i-042a6332509482556` attempting to inspect the runner's
  local diagnostic logs; did not attempt an `sts:AssumeRole` self-grant given this doc's existing finding that this
  identity is not the self-service-blessed one. Given the escalating recurrence rate (4 confirmations in ~1.5h vs. the
  original single 2026-08-15 observation), this may now warrant re-weighing P1 vs. a harder operator page — left as an
  observation for whoever next reviews this doc, not unilaterally re-prioritized here. Provenance: cicd escalation
  agt-723f23, features-service (no PR).

- **slot-3 2026-08-17 ~17:40Z (interactive session)**: picked up the `[OPERATOR]` follow-up below — this session's AWS
  identity (`arn:aws:iam::427895769566:user/admin_od`) DOES have working `ssm:SendCommand`/`ssm:DescribeInstanceInformation`
  access to the glue-runner host (unlike `ikenna-worker`, blocked in every prior attempt) — confirmed `i-042a6332509482556`
  (region `ap-northeast-1`, matches `172.31.3.59` = `glue-ip-172-31-3-59-1` exactly, resolving this doc's own
  unconfirmed-host-identity caveat). **Root cause now confirmed at the host level** (`scripts/self-hosted-runners/ssm-run.sh`):
  this is NOT "one runner for the whole fleet" — there are ~25 separate `github-glue-runner-<repo>@glue-1.service` systemd
  units (one dedicated runner per repo, e.g. `github-glue-runner-deployment-service@glue-1.service`), all running as
  processes on this SAME single EC2 host, sharing one egress IP. Each is a **JIT/ephemeral runner by explicit design**
  (unit-file comment: "Never give up restarting (the glue-* pool exits after every single job by design)"; run.sh:
  "glue-*: one job per process, restart to re-register"). Confirmed directly: `deployment-service`'s glue-1
  `_work/_actions` cache directory **does not exist** — every single job re-downloads `actions/checkout@v4` (and every
  other action) fresh from `codeload.github.com`, for every one of the ~25 per-repo runners, all from the same host IP.
  When enough repos' quality-gates-v2 fire in the same window (the `*/30` `ldr-to-main-promote-fleet.yml` tick, or
  several repos' hourly `workflow_dispatch` re-checks landing close together — exactly the pattern the 2026-08-17
  escalations agt-3378e5/agt-8c192b/agt-723f23 above independently observed), the AGGREGATE per-IP codeload request rate
  trips GitHub's 429. This is standard, documented GitHub Actions behavior for `--ephemeral`/JIT-registered runners (the
  working directory is torn down between jobs by design, for job-to-job isolation) — not a misconfiguration bug, a real
  architecture tradeoff. The infra ALREADY has a proven alternative pattern in the same unit-template family: the
  `writer-N` runners (e.g. `github-glue-runner-ao@writer-1.service`) are "long-lived, restart only on crash" — NOT
  ephemeral — so their `_work/_actions` would naturally persist across jobs. **Did not implement a fix this session**:
  switching the QG-slice runners from ephemeral to long-lived is a genuine fleet-wide CI-security-posture decision (job
  isolation guarantee vs. this congestion), not a narrow bug fix — flagged for operator decision rather than unilaterally
  changed on a host that also runs the agent-orchestrator (`github-glue-runner.slice` comment: "protects the
  agent-orchestrator"). Verified the congestion is BURSTY/self-clearing, not a sustained outage: `gh api
  repos/IggyIkenna/deployment-service/actions/runners` showed `busy:false` at check time (no backlog), and a single
  fresh `quality-gates-v2` dispatch against current LDR head was attempted to confirm — see Follow-ups for the outcome
  once observed. Also confirms disk is NOT the constraint (290G root, 107G avail, 64% used).

## Follow-ups (tracked work, not prose)

- [ ] [OPERATOR] P1. From a session/identity WITH `ssm:SendCommand`/`ssm:DescribeInstanceInformation` on the
      glue-runner host (or console access), check whether the self-hosted runner's `_work/_actions` action-download
      cache is being wiped between jobs (ephemeral/containerized runner re-provisioned per job would explain why
      EVERY quality-gates-v2 job re-downloads `actions/checkout@v4` fresh, not just the first job after a cold boot).
      If confirmed, either (a) make the actions cache persistent across jobs on this runner, or (b) provision
      additional runner capacity so a single IP isn't accumulating enough codeload requests/hour to trip GitHub's
      rate limit. This is the SAME capacity gap as this doc's original P1 finding, now with a second concrete
      symptom (codeload 429 on `actions/checkout`, 2026-08-17) in addition to the original queue-depth/duration
      symptom (2026-08-15).
