---
doc_type: issue
title:
  quality-gates-v2 on the self-hosted "glue" runner fleet false-failed a promotion PR + has cancelled every hourly
  live-defi-rollout re-check for 8+ hours — shared-host resource contention, not a code/test defect
summary: >-
  Escalation agt-aa84f7 (wall_type=ldr_qg_failure) dispatched me to fix a RED quality-gates-v2 on deployment-service#678
  (LDR → main promotion PR). Root-caused: NOT a code or test defect — both failing legs (`checks`: overall run 345s >
  the 300s MAX_DURATION budget; `tests`: 2 subprocess-heavy tests exceeded the 300s pytest-timeout) are
  wall-clock/timing failures on a host that was — and still is at filing time — severely oversubscribed (load average
  26-32 on 8 physical cores). The two "failing" tests reproduce cleanly and quickly in isolation (6/6 passed in 66s even
  under the SAME host's load 32). By the time I investigated, PR#678 had ALREADY merged (`mergedAt` == the exact instant
  the failing quality-gates-v2 run was even created) and main/LDR both already carry the commit — so the specific wall
  is moot, no code fix needed, nothing to ship. Filing this because the underlying cause is systemic and still active:
  EVERY `quality-gates-v2` `workflow_dispatch` run against LDR since ~2026-08-03T12:31 has completed `cancelled` (not
  success, not failure) rather than a clean run, with one currently stuck `queued` 16+ min. This masks whether LDR is
  actually green and burns CI compute repeatedly.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service, agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, quality-gates, host-contention, ci, self-hosted-runner, glue-runner, false-positive, ldr_qg_failure]
related:
  [
    /plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/15-runbooks/devops-ci-walls.md,
    /agents/cicd.md,
  ]
created: "2026-08-03"
parent_epic: agent_operating_framework_master
assigned_vm: NA
resolved_by:
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
source: [agt-aa84f7]
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/15-runbooks/devops-ci-walls.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    scripts/quality-gates-base/qg-host-governor.sh,
    deployment-service/tests/unit/test_vm_launcher_scripts.py,
  ]
---

# quality-gates-v2 false-red on a contended self-hosted runner host (LDR + promotion PR)

## What I was dispatched to do

`escalation_id=agt-aa84f7`, `wall_type=ldr_qg_failure`, `repo=deployment-service`, `pr_number=678`. CONTEXT: "
quality-gates-v2 FAILED on promotion PR deployment-service#678 (LDR -> main). The promote gate is red + the PR is
blocked. Fix the gate failure ON live-defi-rollout ..., then the promotion re-gates green." Failing run:
https://github.com/IggyIkenna/deployment-service/actions/runs/30840847394.

## What I found

**1. The failing run's two red legs are timing failures, not logic failures.**

- `QG slice (checks)`, job 91777297709: every substantive check passed (basedpyright, codex-compliance ratchet,
  actionlint, the ~100 STEP 5.x architectural gates) — the run just took 345s wall against `qg_resource_baseline.json`'s
  106s baseline (own log line: `⚠️ Resource drift: wall 345s > 2× baseline 106.0s ... investigate before merge`), then
  hard-failed the separate `MAX_DURATION=300` gate:
  `❌ Quality gates must complete in <300s (took 345s work + 0s governor queue-wait = 345s wall)`.
- `QG slice (tests)`, job 91777297719: `2 failed, 2887 passed, 17 skipped ... in 2522.41s (42min)`. Both failures are
  `Failed: Timeout (>300.0s) from pytest-timeout` in
  `tests/unit/test_vm_launcher_scripts.py::TestApiFootballLauncherHardenedPreemptionSignal`
  (` test_launcher_writes_launch_params_with_replayable_scope`,
  `test_shutdown_script_bakes_in_vm_name_and_project_no_metadata_lookup`) — subprocess-spawning tests (real `bash` +
  `python3` cold-starts under a fully-mocked `gcloud`) that are inherently ~10s each even loaded, so 300s is only
  exceeded under severe contention.

**2. Reproduced clean.**
`.venv/bin/python -m pytest tests/unit/test_vm_launcher_scripts.py::TestApiFootballLauncherHardenedPreemptionSignal -v --timeout=90`
→ **6/6 passed in 66.29s**, run on the SAME shared host, at the SAME time, under an even higher observed load
(`load average: 32.01, 32.83, 30.21`) than the CI run likely saw. No code or test change reproduces or explains the
failure — the tests and the code under test are correct.

**3. Host state at filing time confirms severe, ongoing oversubscription.** `uptime`: load average 26-32 on
`physical_cores=8` (per `qg-host-governor.sh --status`) — 3-4x oversubscribed. `ps aux` showed 15+ concurrent
`quality-gates.sh` processes from other agent-orchestrator slots at once. The GH Actions self-hosted "glue" runners
(`/opt/github-glue-runners-<repo>/glue-N/`) run ON THIS SAME shared VM as the interactive agent slots — confirmed via
`ps aux | grep glue` showing `github-glue-runners-ao`, `-deployment-service`, etc. listener processes alongside slot
work. So CI job wall-clock and interactive-slot QG wall-clock compete for the identical CPU/RAM pool.

**4. The `qg-host-governor` reservation system (shipped `qg_host_adaptive_resource_governor_2026_07_14.md`, closing
`plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md`) is NOT preventing this recurrence.**
`bash scripts/quality-gates-base/qg-host-governor.sh --status` at filing time:
`running heavy phases: 0, live reservations: none` — i.e. the governor believes the host is idle — while `uptime` shows
load 26-32. Either (a) the CI glue-runner's own `quality-gates.sh` invocation doesn't participate in the same governor
token/ledger as interactive slots (plausible — the governor's `MAX_DURATION` exclusion for `QG_GOVERNOR_WAIT_SECONDS`
assumes the caller went through `qg_governor_acquire()`; the failing run's own log shows `0s governor queue-wait`,
consistent with the CI leg never registering a reservation at all), or (b) the load is coming from processes the "heavy
phase" reservation was never scoped to gate (light QG slices, non-QG agent work, etc.). Not root-caused further — this
needs someone with host-capacity + governor-integration context, same class of judgment call the 2026-07-13 issue
explicitly said not to self-adjust blind.

**5. Systemic, not a one-off**: every `quality-gates-v2` `workflow_dispatch` run against `live-defi-rollout` for the
last 8+ hours (`gh run list --repo IggyIkenna/deployment-service --workflow quality-gates-v2.yml`) completed `cancelled`
— never a clean success or failure — with the most recent stuck `queued` 16+ min at filing time. This is consistent with
the workflow's `concurrency: cancel-in-progress` group killing each hourly re-check before it can finish under the
current contention, which means **LDR's actual green/red state for deployment-service has been unverified by CI for
hours** — a silent visibility gap, not just wasted compute.

**6. The specific wall is already moot.** `gh pr view 678` → `state: MERGED`, `mergedAt: 2026-08-03T18:20:44Z` (the same
instant run 30840847394 was even created) → `mergeCommit c571a5b3`. Verified `c571a5b3` is on `origin/main`
(`compare/main...c571a5b3` → `behind: 0`) and already back-merged into `live-defi-rollout` (visible in
`git log origin/live-defi-rollout` as `3b186a1 chore(promote): LDR → main (Option-B direct)`, with several commits
landed on top since). **No PR-#678-specific action remains** — I did not push any code change (none was needed; the
failure was not reproducible and the promotion already succeeded through whatever path actually gated it, which appears
to have run alongside — not blocked by — the failing/cancelled quality-gates-v2 checks; worth a separate look at whether
the `ldr_main` required-check set is actually enforcing `quality-gates-v2` as documented, since this PR merged without a
green one).

## Open questions for whoever picks this up

1. Does the CI glue-runner's `quality-gates.sh` invocation participate in the same `qg-host-governor` reservation ledger
   as interactive agent-orchestrator slots? If not, that's the concrete integration gap.
2. Is the current host (RAM/core count) simply undersized for (interactive slot fleet) + (per-repo glue runner CI)
   concurrent demand, and does that call for either more headroom or a hard cap on how many slots can run heavy QG
   phases while glue-runner CI is active on the same box?
3. Why did deployment-service#678 merge to `main` without ANY successful `quality-gates-v2` run against its head SHA
   (both attempts: one failed on timeout, one cancelled)? If `quality-gates-v2` is a genuinely REQUIRED check on
   `ldr_main` repos per CLAUDE.md, this merge should not have been possible — worth confirming branch-protection is
   actually wired the way the SSOT describes for this repo.

## What I did NOT do

Did not touch any deployment-service code or tests (nothing was wrong with either). Did not force-resolve, did not lower
`MAX_DURATION` or the pytest-timeout, did not disable the resource-drift check. Did not re-trigger the CI workflow given
the host is still visibly oversubscribed right now — a retrigger would very likely fail again for the identical reason
and just burn more contended compute.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries) — codex CI-flow + CI-walls-runbook SSOTs, the
  governor plan this doc found not preventing recurrence, the governor script itself, and the specific failing test
  file.
