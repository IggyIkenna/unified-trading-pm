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
repos: [deployment-service, market-tick-data-service, agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, quality-gates, host-contention, ci, self-hosted-runner, glue-runner, false-positive, ldr_qg_failure]
related:
  [
    /plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/15-runbooks/devops-ci-walls.md,
    /agents/cicd.md,
    /plans/active/ldr_qg_v2_ci_host_contention_false_wall_2026_08_03_finalize_2026_08_10.md,
  ]
created: "2026-08-03"
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: planning
resolved_by:
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
sequential: true
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

## Todos

- [ ] [INFRA] P2. **Determine whether the CI glue-runner's `quality-gates.sh` invocation shares the `qg-host-governor`
      reservation ledger with interactive agent-orchestrator slots.** Trace whether the glue-runner's QG invocation
      calls `qg_governor_acquire()` (`scripts/quality-gates-base/qg-host-governor.sh`) the same way an interactive slot
      does, or bypasses the ledger entirely — this doc's finding 4 above observed `0s     governor queue-wait` on a CI
      leg despite the host being severely loaded (`uptime` 26-32 on 8 cores), suggesting a bypass. Done-when: a stated
      YES/NO on whether the glue-runner participates in the same reservation ledger, with the code path cited
      (function + file); if NO, file a follow-up todo to wire it in.
- [ ] [INFRA] P2. **Determine whether the shared host running both the interactive agent-orchestrator slot fleet and the
      per-repo GH Actions glue-runner CI is undersized for their combined peak concurrent demand.** Measure physical
      core count + typical interactive-slot heavy-QG-phase concurrency + glue-runner concurrency during a representative
      busy period (`uptime`, `qg-host-governor.sh --status`, `ps aux | grep glue`), and compare against
      `qg_resource_baseline.json`'s assumed baseline. Done-when: a stated verdict (undersized / adequate) with the
      measured numbers cited; if undersized, file a follow-up todo recommending either more headroom or a hard cap on
      concurrent heavy-QG slots while glue-runner CI is active on the same host.
- [ ] [REVIEW] P1. **Confirm whether `quality-gates-v2` is actually enforced as a REQUIRED branch-protection check on
      `deployment-service`'s `ldr_main` promotion path**, given PR#678 merged to `main` with zero successful
      `quality-gates-v2` runs against its head SHA (one timeout-failed, one cancelled) — per CLAUDE.md,
      `quality-gates-v2` is supposed to be a required check on `ldr_main` repos. Check `deployment-service`'s branch
      protection (ruleset + classic settings, `gh api repos/IggyIkenna/deployment-service/branches/main/protection` or
      the ruleset equivalent) for whether `quality-gates-v2` is actually listed as required. Done-when: a stated YES/NO
      on whether branch protection is correctly wired for this repo; if NO, file a follow-up todo to fix it.

— converted 2026-08-06 (/plan-reconcile ao): the 3 "Open questions for whoever picks this up" above were prose-only,
invisible to every todo-counting gate in the corpus (`grep -cE '^- \[ \]'` was 0 across 211 lines). Converted to
canonical `- [ ]` todos per `task_template.md` §3 — prose kept verbatim above, content/investigative scope unchanged,
`assigned_vm: NA` unchanged (still operator/judgment-gated work, not a mechanical fix).

## What I did NOT do

Did not touch any deployment-service code or tests (nothing was wrong with either). Did not force-resolve, did not lower
`MAX_DURATION` or the pytest-timeout, did not disable the resource-drift check. Did not re-trigger the CI workflow given
the host is still visibly oversubscribed right now — a retrigger would very likely fail again for the identical reason
and just burn more contended compute.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries) — codex CI-flow + CI-walls-runbook SSOTs, the
  governor plan this doc found not preventing recurrence, the governor script itself, and the specific failing test
  file.
- **cicd re-dispatch 2026-08-03 (same escalation_id=agt-aa84f7, slot 4)**: the orchestrator re-fired the identical
  escalation (same repo/PR/wall_type/CONTEXT/failing-run-URL as this doc's original filing). Re-verified rather than
  re-investigating from scratch: `gh pr view 678` still shows `state: MERGED`, `mergedAt: 2026-08-03T18:20:44Z`,
  `mergeCommit: c571a5b3` — confirms the original finding (§6, "the specific wall is already moot") still holds; LDR
  HEAD has moved well past that merge (`b64e4a7` at re-check time). The systemic host-contention cause is still ACTIVE:
  `gh run list --workflow quality-gates-v2.yml --branch live-defi-rollout` shows a run `queued` 23m48s plus three more
  recent `cancelled` runs, `uptime` load average 22-28 on 8 physical cores. No code touched (none to touch — PR#678 has
  no outstanding action), no repo-blockers open for deployment-service. The open questions in this doc (governor/CI
  glue-runner integration gap, required-check enforcement on `ldr_main`) remain unanswered and are the actual next step
  for whoever has host-capacity/governor context — this re-dispatch did not have new information to add there.

- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — first marker on this doc;
  `grep -cE '^- \[ \]'` = 0 (this doc carries no real checkbox todos — its "Open questions for whoever picks this up"
  and "What I did NOT do" sections are prose, not `- [ ]` items). Nothing exists here to RECLASSIFY. The 3 open
  questions (does the CI glue-runner participate in the qg-host-governor reservation ledger; is the host undersized for
  interactive-slot + glue-runner concurrent demand; why did #678 merge without a green required `quality-gates-v2` run)
  are all genuinely investigative/judgment calls, not bounded worker-determinable facts — correctly homed NA even if
  converted to checkboxes. Not in `/ag-closeout-audit ao`'s batch6 (no actionable content to extract), consistent with
  this verdict.

- **cicd 2026-08-04 (escalation agt-652032, slot 7, wall_type=main_ci_red)**: SECOND confirmed instance, this time with
  real (not just visibility-gap) impact — `market-tick-data-service` `quality-gates-v2` RED on `main` while
  `live-defi-rollout` is genuinely green. Root-caused as the identical mechanism: `main` had a stale
  `_MTDS_TYPE_IGNORE_BASELINE=658` (the repo-local STEP 5.95 freeze-and-shrink ratchet in
  `market-tick-data-service/scripts/quality-gates.sh`, see the sibling now-archived
  `mtds_type_ignore_ratchet_regression_2026_08_03.md`) while LDR already carries the bump to 659 at
  `market-tick-data-service@840c816d` (verified `git merge-base --is-ancestor 840c816d origin/main` → NO,
  `...origin/live-defi-rollout` → YES). LDR is **973 commits ahead of main** and NOT promoting: the PM fleet workflow
  `ldr-to-main-promote-fleet.yml` (runs every 15 min) logs, every tick,
  `GATE BLOCK market-tick-data-service: ci_status=FAILING (cached='FAILING', live='FAILING') — LDR CI is red; fix before LDR→main`
  — so no new promote PR is even being opened (the last one, #819, merged 2026-08-03T20:19, then its own post-merge
  push-triggered `quality-gates-v2` hit the stale-baseline red before `840c816d` had landed). The `ci_status=FAILING`
  gating this is itself the false-red from this issue's root cause, not a real LDR break: checked the
  currently-`in_progress` LDR `quality-gates-v2` run (30898680083, started 09:58:55) at the job-step level —
  `Run quality gates (leg checks)` step **already completed with `conclusion: success`** at 10:47:33, but the job has
  been wedged on the unrelated `Post Cache uv package cache` housekeeping step for 50+ minutes with no sign of
  progressing (matches this doc's §1 "shutdown signal" / hung-job pattern — a prior sibling run, 30894289340, died with
  `The runner has received a shutdown signal` at 92% through a cache download). Host `uptime` at investigation time:
  load average 20.80/21.41/18.89 on 8 physical cores; `qg-host-governor.sh --status` still reports
  `reserved: 0MB, live reservations: none` — confirms this doc's open question #1 (CI glue-runner not participating in
  the governor ledger) is still unresolved and still the live mechanism keeping the host's real load invisible to the
  reservation system. Both `glue` runners for this repo report `busy:true`. **What I did**: verified the fix is
  genuinely on LDR (no code change needed — mirrors this doc's own precedent of not touching correct code); did NOT
  force-retrigger `quality-gates-v2` given the host is visibly still contended and a retrigger would very likely just
  queue behind/repeat the hang (same reasoning as the original filing's §"What I did NOT do"); did NOT open a
  `repo-blocker` — `GET /api/repo-blockers` returns none open, and this wall does not block `quickmerge` Pass-1/Pass-2
  QG (those run against LDR content, which is fine) — it only stalls the LDR→main promotion cadence, so no worker is
  actively blocked, just main's staleness is growing. Skipped pinging the authoring slot (`AUTHORING_SLOT=ci-reconcile`,
  the literal non-numeric sentinel from `server/ci_reconcile.py`'s self-detected bare-LDR wall — no real originator to
  notify, per `agents/cicd.md`'s skip rule). **New signal for whoever has host-capacity/governor context**: unlike the
  original deployment-service instance (moot by the time it was investigated — the promotion had already gone through
  some other path), this one is NOT self-healing via merge — `market-tick-data-service` has now been stuck un-promotable
  for hours and the gap is only growing, since the fleet gate's `ci_status` pre-check means a red LDR CI reading blocks
  promotion attempts from even being opened, independent of whether any specific promotion PR's checks would pass. If
  the CI-glue-runner/governor integration gap (open question #1) is the root fix, this is now a second data point that
  it is actively costing real promotion cadence, not just visibility.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **fixed 2026-08-06 (/plan-reconcile ao)**: this doc carried zero `- [ ]`/`- [x]` checkboxes across 211 lines despite
  the live "Open questions for whoever picks this up" section (still 3 genuine unresolved questions, reconfirmed by the
  2026-08-04 `cicd` re-dispatch entry above on a second, different repo). Converted the 3 questions into canonical
  `- [ ]` todos under a new `## Todos` heading (per `task_template.md` §3), prose kept verbatim. The 2026-08-04
  na-eligibility-audit entry above correctly recorded `grep -cE '^- \[ \]'` = 0 as of that date — left unedited as an
  accurate point-in-time record; it is now stale (3 open todos exist) as of this fix.

- **2026-08-09T03:20Z (slot-29, infra craft)**: fresh, far more severe corroborating evidence for todo #2 above ("is the
  shared host undersized for combined peak demand") from an unrelated task
  (`cefi_track2_backfill_vm_preempted_no_recovery-99a54eb412aa`, a one-file bash-script fix in deployment-service). 9
  consecutive interactive-slot `quality-gates.sh` runs against a correct, already-verified commit were killed before
  writing a sentinel, over ~90 minutes, while `uptime` climbed 40→69 (4 physical cores) and `ps` showed up to 19
  concurrent `quality-gates.sh` processes host-wide (vs the documented ≤2 rule) with swap usage 14GB+. Root cause for
  most kills: the `qg-host-governor`'s own RAM self-abort watchdog (`_qg_watchdog_pressure_hit`, default abort at <20%
  available) tripping legitimately — confirmed via its `killed.<pid>` marker files. A few earlier kills were even more
  severe: trivial backgrounded `sleep` commands with near-zero footprint were also killed within seconds, suggesting the
  shared `orchestrator.service` systemd cgroup (confirmed via `/proc/self/cgroup` + `memory.max`/`memory.current`,
  ~26GiB cap) may itself have been at/near its ceiling independent of what system-wide `free -h` reported as "available"
  — a plausible answer to this doc's open question about whether the host is undersized for combined interactive-slot +
  CI demand (the interactive-slot side alone, no CI glue-runner involved this time, was enough to saturate it). Did not
  close todo #2 (that needs the glue-runner side traced too, which this incident didn't touch) — leaving it open with
  this as supporting evidence. Eventually shipped via the operator-approved `scripts/**` direct-push carve-out rather
  than continuing to retry QG, per operator ruling that repeated retries under active contention may themselves feed the
  loop (msg 6203, full detail in `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`'s own Progress Log).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3) — RECLASSIFY, `assigned_vm: NA` → `planning`.**
  Fresh re-read of all 3 open todos found the 2026-08-04/06 "genuinely investigative/judgment calls, not bounded
  worker-determinable facts" verdict too broad — each todo actually carries a concrete, deterministic done-when: todo 1
  is a pure code-trace (does the glue-runner's QG invocation call `qg_governor_acquire()`? YES/NO with the code path
  cited); todo 2 is a live measurement + comparison against `qg_resource_baseline.json` (undersized/adequate verdict
  with numbers cited — and this doc's own 2026-08-09 slot-29 entry already supplies strong supporting evidence, so this
  may be mostly synthesis of already-gathered evidence rather than fresh investigation); todo 3 is a single `gh api`
  branch-protection query (YES/NO). None require a design call — each explicitly says "if [gap found], file a follow-up
  todo" rather than asking the worker to design the fix inline, matching the audit-with-a-stated-done-when eligibility
  bar. All 3 are read-only (code grep, `gh api`, `uptime`/`ps aux`/`qg-host-governor.sh --status`) — no CI retrigger, no
  host-state mutation, so the doc's own repeated "did NOT force-retrigger/touch the governor" cautions do not apply to
  this audit work. Conflict-check: grepped every `ao_satellite_ao_dispatch_batch*` (1-16, `status: draft`/`active`) +
  finalizes + `ao_open_issues_consolidated_close_out_2026_07_17.md` for `qg_governor_acquire`/`glue-runner`/
  `ldr_qg_v2_ci_host_contention` — only `ao_satellite_ao_dispatch_batch5_2026_08_03.md` mentions `qg_governor_acquire`,
  for a DIFFERENT source doc (`host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`, already
  archived) — no overlap. `sequential: true` added (all 3 todos record findings into this same doc). Finalize twin:
  `/plans/active/ldr_qg_v2_ci_host_contention_false_wall_2026_08_03_finalize_2026_08_10.md`.
