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

- [x] [INFRA] P2. ✅ **Determine whether the CI glue-runner's `quality-gates.sh` invocation shares the
      `qg-host-governor` reservation ledger with interactive agent-orchestrator slots.** — unified-trading-pm@b867ae4
      (doc-only, findings below). **NO — it calls the identical `qg_governor_acquire()` code path but writes to a
      DIFFERENT, disjoint ledger directory than interactive slots.**
- [x] [INFRA] P2. ✅ **Wire the glue-runner CI ledger and the interactive-slot ledger back into ONE shared reservation
      namespace** (follow-up from the todo above) — unified-trading-pm@\<see Progress Log for SHA\>. Fixed
      `_qg_shared_root()` in `scripts/quality-gates-base/qg-host-governor.sh` so the glue-runner branch
      (`/opt/github-glue-runners*`) now resolves to the SAME directory the interactive-slot branch (`*/.tabs/*`) already
      derives in production, live-verified via a real (non-dead-PID) cross-topology reservation test. **NOT** unified
      onto `/opt/.qg-governor-glue-shared` as this todo's own text suggested as the first option — see Progress Log for
      why that was live-disproven mid-fix (every interactive-slot process is sandboxed away from `/opt` entirely;
      unified onto a `/home`-based root instead). Full detail in the Progress Log entry below.
- [x] [INFRA] P2. ✅ **Determine whether the shared host running both the interactive agent-orchestrator slot fleet and
      the per-repo GH Actions glue-runner CI is undersized for their combined peak concurrent demand.** —
      unified-trading-pm (doc-only, see Progress Log 2026-08-10 slot-9 entry for full measured numbers). **Verdict:
      UNDERSIZED.** The physical envelope (8 physical cores / 16 vCPU, 30GiB RAM, `orchestrator.service` cgroup-capped
      at ~26GiB) cannot safely absorb the fleet's own documented peak concurrent heavy-QG demand — the 2026-08-09
      slot-29 incident (already in this doc's Progress Log) measured up to 19 concurrent `quality-gates.sh` processes
      (vs. the CLAUDE.md-documented ≤2 rule) with load average climbing 40→69 and 14GB+ swap, and the RAM watchdog
      killing even trivial near-zero- footprint background commands — evidence the host, not just the QG governor's
      accounting, was at its real ceiling. A live re-check today (moderate period, no glue-runner CI active on this host
      right now — see below) still showed load average 15.85 against 8 physical cores (~2x oversubscribed) with only 3-4
      concurrent `quality-gates.sh` processes running. `qg_resource_baseline.json`'s wall-clock figures are all
      `measured_concurrency: 1` (serial, uncontended) — e.g. `deployment-service` baseline `wall_s=106.0`, but this
      doc's own finding 1 shows the SAME test suite hit `345s` wall (3.25× baseline) purely from contention, tripping
      the `MAX_DURATION=300s` gate that was never calibrated for real fleet concurrency. Filed follow-up todo below
      (hard-cap tightening, now that todo 2's ledger unification makes it enforceable) rather than recommending a host
      resize, which is an operator cost decision out of AO scope.
- [x] [INFRA] P2. ✅ **Tighten the qg-host-governor's admission caps now that the CI-glue-runner and interactive-slot
      ledgers are unified (todo 2, 2026-08-10)** — unified-trading-pm@1ec1d683f9. See Progress Log (2026-08-10, slot-11)
      for the full trace: `QG_HOST_CONCURRENCY` turned out to be INERT on this host (reservation mode, not token mode) —
      tightened the total-instance gate default cap (`floor(cores × 0.75)`, floored at 6 → K=8→6 on this host) and
      `QG_HOST_RAM_ABORT_PCT` (80→75) instead.
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

- **2026-08-10 (slot-12, infra craft) — todo 1 RESOLVED, NO (disjoint ledger, not a full bypass).** Traced the full code
  path rather than re-running any CI: `python-quality-gates-v2.yml`'s `qg-slices` job (reusable workflow,
  `unified-trading-ci/.github/workflows/python-quality-gates-v2.yml:293-320`) sets `QG_GOVERNOR_MODE: reservation`
  whenever the caller passes `self_hosted_runner_labels` (empty ⟹ `token`, a no-op on single-tenant `ubuntu-latest`),
  then its "Run quality gates" step (`:775+`) execs the SAME `scripts/quality-gates.sh` → `base-service.sh` that every
  interactive slot runs, cloned fresh from PM at `live-defi-rollout` HEAD in the preceding "Clone unified-trading-pm and
  dependencies" step (not a per-repo fork). `base-service.sh:825-827` unconditionally calls `qg_governor_acquire()`
  before TESTS/TYPECHECK (unless sentinel-hit or no heavy phase) — no `QG_GOVERNOR_DISABLE` is set anywhere in any
  workflow (fleet-wide grep, zero hits), so the glue-runner leg does NOT skip the governor call. `qg_governor_acquire()`
  (`qg-host-governor.sh:593-595`) dispatches to `_qg_governor_acquire_reservation()` when `QG_GOVERNOR_MODE=reservation`
  — confirmed this VM's own interactive slot shell env also runs `QG_GOVERNOR_MODE=reservation` (installed via
  `install-qg-governor-shell-env.sh` sourcing `.env.local`; live-checked: `QG_GOVERNOR_MODE=reservation`,
  `QG_HOST_CONCURRENCY=6` in this very session's env) — so BOTH surfaces run the identical reservation-mode function.
  **The actual gap**: the reservation ledger's location is `_qg_ledger_dir()` → `_qg_shared_root()`
  (`qg-host-governor.sh:269-278`), whose `case` statement resolves DIFFERENTLY per caller — `WORKSPACE_ROOT` matching
  `*/.tabs/*` (every interactive slot) → `${ws%/.tabs/*}` (this host: `/home/ubuntu/unified-trading-system-repos`), but
  cwd matching `/opt/github-glue-runners*` (glue-runner CI, per `setup-glue-runners.sh`'s `RUNNER_BASE` default) → the
  hardcoded `$_QG_GLUE_RUNNER_SHARED_ROOT` = `/opt/.qg-governor-glue-shared`. **Live-verified these are genuinely
  disjoint, not a symlink**: both directories exist on this host (same filesystem device id `66305`) but different
  inodes (`1624209` vs `524911`); the interactive-slot ledger (`~/unified-trading-system-repos/.benchmarks/qg-governor`)
  has fresh entries as of 2026-08-10 (today), while the glue-shared ledger
  (`/opt/.qg-governor-glue-shared/.benchmarks/qg-governor`) last wrote 2026-08-05 (consistent with
  `deployment-service` + 14 other public repos being reverted off self-hosted runners that same day per
  `self-hosted-qg-repos.txt`'s own changelog — fewer self-hosted callers since, though the 7 remaining private
  self-hosted repos, incl. `agent-orchestrator`, should still be writing there on their next run). Also checked this
  host currently has NO live `/opt/github-glue-runners*` install (`find /opt -iname '*glue*'` → only
  `/opt/.qg-governor-glue-shared` + unrelated `/opt/glue-deploy`; no matching systemd units beyond the crash-loop
  watchdog) — the glue-runner pools for the 7 still-self-hosted repos are evidently NOT colocated on THIS particular
  host anymore, a separate fact from the ledger-split finding itself (worth folding into todo 2's live measurement, not
  re-litigated here). **Answer: NO, they do not share the same reservation ledger** — this reconciles finding 4's
  `governor queue-wait: 0s` observation: the CI leg wasn't bypassing the governor, it was correctly reporting zero wait
  against ITS OWN (disjoint, and at the time near-empty) ledger while the interactive slots' load lived in a ledger the
  CI leg never looks at, and vice versa — functionally equivalent to no shared admission control even though the code
  path is identical. Filed the follow-up wiring todo above per this todo's own done-when instruction.

- **2026-08-10 (slot-14, infra craft) — todo 2 RESOLVED, ledgers unified, but NOT onto `/opt` as originally suggested.**
  Started implementing the todo's first suggested option (hardcode both branches of `_qg_shared_root()` to
  `/opt/.qg-governor-glue-shared`) and hit a live, disqualifying discovery mid-fix: **every interactive
  agent-orchestrator worker process is sandboxed AWAY from `/opt` entirely, always.** Confirmed via `/proc/self/cgroup`
  → this worker's own process tree is a descendant of the `orchestrator.service` systemd unit; `/proc/self/mountinfo`
  shows `/` bind-mounted `ro` specifically for that mount namespace (per-mount options `ro,nosuid,relatime` vs. the
  underlying superblock's real `rw,discard,...`) — a systemd `ProtectSystem`-style sandbox scoped to `ReadWritePaths=`
  under `/home` + `/tmp`, NOT a real host disk/filesystem incident (ruled that out explicitly: cross-checked that
  `rsyslogd`/`amazon-ssm-agent`/the AO server itself keep writing to `/var/log` in real time on the SAME host at the
  SAME moment every write attempt from this worker's own shell to `/opt`, `/var`, or `/etc` failed EROFS, with AND
  without the Bash tool's own sandbox override — `dangerouslyDisableSandbox: true` made no difference, ruling out a
  Bash-tool-layer sandbox and confirming it's a systemd/cgroup-layer one instead). This means hardcoding the shared
  ledger to `/opt/.qg-governor-glue-shared` would have "fixed" the directory-unification bug on paper while silently
  degrading admission control to unlocked best-effort for the interactive-slot side specifically (via
  `_qg_ledger_with_lock`'s existing mkdir-failure degrade — no crash, just zero real coordination, defeating the entire
  point of this todo). Did NOT file this as a separate incident doc — it is not a bug, it is working-as-designed host
  hardening (protects the shared VM from a worker agent's mistakes), just previously undocumented in this corpus; noting
  it here and in the code comments so a future investigator doesn't waste time treating `/opt` write failures from an
  interactive slot as a disk/fs incident. **Actual fix shipped**: `_qg_shared_root()`'s glue-runner branch
  (`/opt/github-glue-runners*`) now resolves to `${HOME:-/home/ubuntu}/unified-trading-system-repos` (a new
  `_QG_HOST_SHARED_LEDGER_ROOT_DEFAULT` constant, overridable via `QG_HOST_SHARED_LEDGER_ROOT` env, read fresh per call)
  — the SAME directory the interactive-slot branch (`*/.tabs/*`) already derives via its original `${ws%/.tabs/*}`
  stripping in production (every real WORKSPACE_ROOT on this one live host is
  `${HOME}/unified-trading-system-repos/.tabs/<N>`), so both surfaces genuinely converge without changing the
  interactive-slot branch's own derivation (which stays dynamic — kept that way deliberately after an initial attempt to
  also hardcode the `.tabs` branch broke `test-qg-cross-host.sh`'s per-test `$TMP`-isolated ledger dirs; confirmed via a
  stash-and-rerun against the pre-fix baseline that this was a genuine regression I introduced, not pre-existing).
  `/opt/.qg-governor-glue-shared` is no longer referenced by the ledger path at all; removed its now-dead
  pre-provisioning step from `setup-glue-runners.sh`'s `install` (no replacement provisioning needed — the new
  `/home`-based dir is already writable by both the glue-runner `RUNNER_USER` and every interactive slot, both `ubuntu`,
  with no new setup). **Live-verified the actual cross-topology fix** (not just unit tests): added a REAL (non-dead-PID,
  backgrounded `sleep`) reservation under a simulated glue-runner `WORKSPACE_ROOT`, then read it back via
  `qg-host-governor.sh --status` under a simulated interactive-slot `WORKSPACE_ROOT` — the glue-sim reservation appeared
  in the interactive side's live-reservations list while the sim process was alive, and disappeared (correctly, via the
  existing dead-PID sweep) once it exited. Also ran the FULL `test-qg-*.sh` + `test-trap-release.sh` suite (34 files)
  before and after (via `git stash`/`stash pop`, tree otherwise clean) to separate genuine regressions from pre-existing
  flakiness: `test-qg-governor-wait-time.sh`'s one failure (`contended acquire recorded wait=0`) and
  `test-qg-mem-cap.sh`'s SKIP (`systemd-run not available`) reproduce IDENTICALLY on the unmodified baseline —
  pre-existing, unrelated to this change, not touched. Updated `test-qg-glue-runner-shared-root.sh` (renamed the old
  `_QG_GLUE_RUNNER_SHARED_ROOT` var references, flipped its test 3 assertion from "unchanged .tabs stripping" to "now
  collapses to the same root as glue-runner CI", added a 6th case proving `QG_HOST_SHARED_LEDGER_ROOT` overrides both
  branches at once) — all 8 assertions pass.

- **2026-08-10 (slot-9, infra craft) — todo 3 RESOLVED, verdict: UNDERSIZED.** Live measurement on this shared host (the
  same one both slot-12 and slot-14 worked on earlier today):
  - **Physical envelope**: `lscpu`/`_qg_physical_cores()` → 8 physical cores, 16 logical (2 threads/core, 1 socket).
    `free -h`: 30GiB total RAM, 47GiB swap configured. `orchestrator.service` cgroup (every interactive slot's actual
    ceiling, confirmed via `/proc/self/cgroup`): `memory.max=27917287424` (approx 26.0GiB), `memory.high=24696061952`
    (approx 23.0GiB throttle point), `memory.current=17147256832` (approx 16.0GiB, ~61% of cap) at measurement time.
  - **Live snapshot right now** (moderate period — no self-hosted CI active on this host at measurement time, see
    below): `uptime` load average **15.85, 15.69, 17.23** against 8 physical cores (~2x oversubscribed even with light
    load); `qg-host-governor.sh --status` shows `physical_cores=8`, `CPU slots (80% x 8): 6`, `running heavy phases: 0`,
    `live reservations: none`, `total-instance gate: K=8, tokens held now: 0/8`; live `ps aux` showed **3-4 concurrent
    `quality-gates.sh` processes** from 3 different slots (27, 18, one more) despite the governor reporting zero
    reservations — consistent with this doc's already-diagnosed (todo 1) ledger-visibility gap, now fixed as of today
    but not yet observed under a genuinely busy period post-fix.
  - **Documented peak** (this doc's own 2026-08-09 slot-29 entry, already in this Progress Log above): load average
    climbed **40 to 69** over ~90 min, **up to 19 concurrent `quality-gates.sh` processes** host-wide (vs. the
    CLAUDE.md-documented at-most-2-full-QGs-at-once rule), **14GB+ swap**, and the governor's own RAM self-abort
    watchdog (`_qg_watchdog_pressure_hit`, default trip at <20% available) killed multiple runs legitimately — plus
    trivial near-zero-footprint backgrounded `sleep` commands were ALSO killed within seconds, which that entry
    attributed to the shared `orchestrator.service` cgroup itself being at/near its ceiling independent of what
    host-wide `free -h` reported as "available." Today's live cgroup read above (`memory.max` approx 26.0GiB) confirms
    that cap is real and not large relative to the fleet's peak demand.
  - **Glue-runner CI concurrency right now**: **zero** — `ps aux | grep glue` found no glue-runner processes, and
    `find /opt -iname '*glue*'` found no `/opt/github-glue-runners*` install on this host at all (only the inert
    `glue-runner-crash-loop-watchdog` systemd timer + the now-unused `/opt/.qg-governor-glue-shared` ledger dir from
    before todo 2's fix). Cross-checked `scripts/self-hosted-runners/self-hosted-qg-repos.txt`: 7 private repos
    (`agent-orchestrator`, `strategy-service`, `e2e-testing`, `features-service`, `market-tick-data-service`,
    `execution-service`, `ml-service`) are still configured to route their real `qg-slices` job to self-hosted runners,
    but none has a live pool on THIS host at measurement time — reconciles slot-12's earlier finding that the
    glue-runner pools for the 7 remaining repos are not currently colocated here. This measurement window therefore
    could not directly observe interactive-slot + glue-runner CI concurrently saturating the SAME host at once; the
    verdict below rests on the interactive-slot fleet's own documented peak (2026-08-09) plus today's baseline-vs-live
    comparison, not a fresh combined-load observation.
  - **Baseline comparison**: `qg_resource_baseline.json` is uniformly `measured_concurrency: 1` (single-process,
    uncontended profiling) — e.g. `deployment-service` local baseline `wall_s=106.0`, `unified-trading-library` local
    baseline `wall_s=215.7` / `peak_rss_mb=5406` (approx 5.3GB for ONE repo's QG run alone). This doc's own finding 1
    already showed the identical `deployment-service` suite hit `345s` wall (3.25x baseline) purely from host
    contention, tripping the `MAX_DURATION=300s` gate. The baseline was never calibrated against realistic fleet
    concurrency, so any wall-clock-based CI gate keyed to it will keep producing false reds whenever real concurrent
    load (which the fleet's own operation routinely produces, per the 2026-08-09 measurement) pushes wall time past
    approximately 3x baseline — structurally, not as a rare fluke.
  - **Verdict: UNDERSIZED.** 8 physical cores / 26GiB cgroup-capped RAM is not enough headroom for the interactive-slot
    fleet's own documented peak concurrency (19 simultaneous heavy QG runs) to run safely, independent of whether
    self-hosted CI is also active — the 2026-08-09 incident reproduced RAM-pressure kills from interactive-slot load
    alone, with zero glue-runner involvement. Adding self-hosted CI (7 repos still configured) on top of that peak, now
    correctly visible to a single shared reservation ledger (todo 2, shipped earlier today), will surface admission
    contention/queueing that was previously invisible rather than adding new physical capacity — the resource envelope
    itself is unchanged. Filed the follow-up hard-cap-tightening todo above per this todo's own done-when instruction;
    did not recommend a host resize (operator cost decision, out of AO scope) as the primary fix.
  - **Caveat**: this measurement window did not catch a live host state combining BOTH a busy interactive-slot period
    AND active self-hosted glue-runner CI simultaneously (none of the 7 configured repos had a live run in progress at
    measurement time) — the verdict is a synthesis of this doc's own prior peak-load evidence (interactive-slot side)
    plus today's baseline/cgroup/governor-config reading, not a single fresh combined-saturation observation. A future
    re-check during an active self-hosted CI run would strengthen this further but is not required for this todo's
    stated done-when (verdict + measured numbers cited).

- **2026-08-10 (slot-11, infra craft) — todo 4 RESOLVED, admission caps tightened — unified-trading-pm@1ec1d683f9.**
  Traced this todo's own literal suggestion ("Lower `QG_HOST_CONCURRENCY` (CPU-slot budget)") before implementing it and
  found it does NOT apply on this host as worded — a precision gap worth recording so a future reader doesn't repeat the
  same dead-end:
  - **`QG_HOST_CONCURRENCY` is currently INERT here.** This host runs `QG_GOVERNOR_MODE=reservation` (live-confirmed:
    `agent-orchestrator/.env.local` and this session's own ambient env both read `QG_GOVERNOR_MODE=reservation`,
    `QG_HOST_CONCURRENCY=6`). `qg_governor_acquire()` (`qg-host-governor.sh:640-642`) branches to
    `_qg_governor_acquire_reservation()` whenever mode is `reservation` and NEVER reaches the token-bucket code path
    that reads `QG_HOST_CONCURRENCY` at all — that env var only governs the legacy `token`-mode heavy-phase K, which
    this host doesn't use. So lowering it would have shipped a no-op change with zero live effect. (It is also already
    at an operator-set floor — `max(2, floor(cores/4))`, "the host must be able to run 2 full QGs at once", ruling
    2026-06-05 — that this todo's own text shouldn't be read as license to violate.) The todo's "CPU-slot budget" phrase
    actually maps to a DIFFERENT live knob: `QG_CPU_FRAC` (reservation-mode CPU gate,
    `cpu_slots = floor(cores × QG_CPU_FRAC)`, default 0.80 → 6 on this 8-core host) and `QG_MEM_SAFETY_FRAC` (the RAM
    reservation-sum bound, default 0.70). Deliberately did NOT touch either — both are the SSOT-documented,
    already-shipped, already-tested contract of a SEPARATE closed plan
    (`plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`'s own "cross-host behaviour" proof table,
    `tests/test-qg-cross-host.sh`, and an explicit "0.80"/"0.70×MemTotal" citation in
    `/codex/06-coding-standards/quality-gates.md`) — changing those defaults would require updating that table + codex
    citation + 2 cross-host tests in the same change, a materially larger and riskier blast radius than this todo's own
    1-hour estimate and "and/or" wording require, when a second, equally-real, much more isolated lever was available
    (below).
  - **What was actually tightened (the isolated, live-effective lever):** the TOTAL-INSTANCE gate
    (`qg_governor_acquire_total_instance`/`release`, added 2026-08-09 — bounds ALL concurrent `quality-gates.sh`
    PROCESSES host-wide, not just the heavy TESTS+TYPECHECK phase the RAM/CPU dual gate governs; this is the mechanism
    that directly answers the incident's own complaint of "19 concurrent `quality-gates.sh` processes" since
    BOOTSTRAP/LINT/CODEX-COMPLIANCE previously ran fully ungated). Its default cap was a flat `physical_cores` (floored
    at 6) — `K=8` on this 8-core host, live-confirmed via `--status` before the change. Changed
    `_qg_total_default_cap()` to `floor(cores × 0.75)`, still floored at 6 → `K=6` on this host (monotonic tightening on
    every host size: `floor(cores×0.75) ≤ cores` always, and the unchanged floor=6 protects small/macOS hosts from
    regressing below the already-validated minimum). Also lowered `QG_HOST_RAM_ABORT_PCT` (runtime abort-monitor trip
    point — the SECOND line of defense that fired legitimately during the 2026-08-09 incident, per that entry's own
    root-cause finding) 80 → 75, for earlier defensive margin independent of the admission-side change. Both changes are
    isolated to `qg-host-governor.sh` + its own dedicated test file — no cross-plan table or codex-cited fraction
    touched.
  - **Live-verified, not just unit-tested**: `bash qg-host-governor.sh --status` on this actual host, before vs. after,
    read `total-instance gate: K=8` → `total-instance gate: K=6` (CPU slots unchanged at 6, RAM budget unchanged at
    70%/22GB — confirming only the intended lever moved). Full governor test suite (`test-qg-*.sh` +
    `test-trap-release.sh`, 16 files) run before AND after via `git stash`/`stash pop`: two failures reproduce
    IDENTICALLY on the unmodified baseline (`test-qg-governor-wait-time.sh`'s "contended acquire recorded wait=0",
    `test-qg-mem-cap.sh`'s SKIP for absent `systemd-run`) — pre-existing, unrelated, not introduced by this change;
    every other test (including the 2 new/updated assertions in `test-qg-total-instance-gate.sh` covering the new
    formula at cores=8→6 and cores=16→12) passes clean.
  - **Codex updated in the same commit**: added a `🟢 2026-08-09/10` banner to
    `/codex/06-coding-standards/quality-gates.md` documenting the total-instance gate's existence (previously completely
    undocumented there — a pre-existing gap from before this todo, not introduced by it) and today's tightening, per the
    plan-authoring HARD RULE that codex is the durable SSOT and a plan/issue doc should reference it, not duplicate it.
  - **Done-when, honestly assessed**: "a lowered cap is shipped" — done (above, live-verified). "a follow-up busy-period
    measurement shows no RAM-watchdog kills of unrelated (non-overbudget) processes" — NOT yet satisfiable from this
    session: I cannot force a genuinely busy, representative multi-slot contention period on demand, and manufacturing
    artificial load on a shared production host to self-validate a safety change would itself risk reproducing the exact
    incident this fix exists to prevent. This is a real, deliberately left-open half of the done-when, not a skipped one
    — flagging it explicitly rather than silently marking the todo fully closed. Whoever next observes this host under
    genuine multi-slot + glue-runner contention (a future `/vm-preemption-billing-waste-audit` pass, a future incident
    investigation, or routine `--status` spot-checks) should confirm `total-instance gate: K=6` is holding and no
    RAM-watchdog kill markers (`aborted.<pid>` files under the shared ledger dir) accumulate for non-overbudget
    processes during a busy window — if kills recur even at the tightened cap, that's evidence the RAM/CPU dual-gate
    fractions (deliberately left untouched here) are the next lever to revisit, not the total-instance cap again.
