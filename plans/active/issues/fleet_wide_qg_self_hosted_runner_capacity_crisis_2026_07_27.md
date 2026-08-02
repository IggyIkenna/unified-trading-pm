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
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [cross-cutting]; content is a self-hosted
  # GitHub Actions runner-capacity incident, squarely ci-tranche (CI/CD pipeline mechanics), not generic cross-AG content.
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

- [x] ✅ **DECIDED 2026-07-28 (operator, live, mid-session).** Initial autonomous pass took path (a) (blanket revert +
      trim the allowlist to the 2 verified pools). **Operator corrected this live**: capacity had freed up materially
      since the incident (EBS IOPS/throughput bump from the earlier VM I/O-contention fix, plus most of the fleet
      already off self-hosted by then) — do not blanket-strip the fleet. Revised posture: put back self-hosted for every
      repo THIS session had personally taken off (6 repos: features-service, fund-administration-service,
      greeks-service, ibkr-gateway-infra, instruments-service, market-tick-data-service), leave the ~10 repos other
      agents genuinely reverted overnight for a real observed hang alone (settled, evidence-based work, not re-litigated
      here), and leave the 2 repos whose revert never shipped (strategy-service, system-integration-tests — blocked
      mid-session by an unrelated stale sibling-clone issue in a non-`.tabs/1` checkout, never actually left
      self-hosted) alone too. This is now genuinely path (b) for a 12-repo subset, on the operator's live authority, not
      a capacity-planning exercise this session did — it is NOT the "provision real per-repo pools" version of (b); just
      "leave the box as loaded as it currently tolerates."
- [x] ✅ **DONE 2026-07-28.** `scripts/workflow-templates/self-hosted-qg-repos.txt` restored to match reality: the 2
      original verified pools (agent-orchestrator, unified-trading-pm) + the 5 repos nobody touched overnight
      (strategy-service, system-integration-tests, trading-agent-service, unified-api-contracts, unified-trading-api) +
      the 6 restored above = 13 entries. The ~10 repos other agents settled on `ubuntu-latest` stay OFF the list.
      Shipped `unified-trading-pm@<see quickmerge output, "restore self-hosted-qg-repos.txt...">`.
- [x] ✅ **DONE 2026-07-28 (superseded by the live operator correction above).** Ran the live-runner-count audit
      (`gh api .../actions/runners`) across the 11 still-self-hosted-at-the-time repos before reverting them — every one
      showed exactly 1 lone runner (`total=1 online=1`), confirming the pattern held for the ones not yet individually
      corroborated. 6 were reverted-then-restored per the operator's live call (see above); the other 5
      (strategy-service, system-integration-tests, trading-agent-service, unified-api-contracts, unified-trading-api)
      were never actually reverted (2 blocked, 3 never dispatched before the correction landed) — all 5 stay on the
      allowlist per the operator's decision, unaudited beyond the 1-runner headcount above.
- [x] ✅ **DONE 2026-07-28.** Re-checked fleet health post-fix: `glue-pool-starvation-monitor` reported "glue pool
      healthy: no `glue`-labelled job queued > 20m while idle" (run 30340860563, 08:04 UTC); spot-checked
      `quality-gates-v2` runs across the 6 restored repos post-restore — none stuck `queued`/`in_progress` past normal
      duration. Did not re-verify `i-0c9b283b31d6b5ca7`'s raw process count directly (no SSH access from this session);
      the glue-pool monitor's own queue-depth signal is used as the proxy instead, per the "use existing observability"
      guidance elsewhere in this workspace. If the operator's "capacity freed up" read changes, re-open this VERIFY.

      **Re-open trigger fired, 2026-07-28 ~15:28 UTC** (found incidentally while verifying deploy-currency for
                                                                                                                                                                                                                                  `agent_orchestrator_mobile_and_worker_tmux_chat_2026_07_28.md` Track 4 — not a re-audit of this issue, just a
                                                                                                                                                                                                                                  fresh data point landing in scope): agent-orchestrator's own promote PR
                                                                                                                                                                                                                                  (https://github.com/IggyIkenna/agent-orchestrator/pull/691, head `promote/agent-orchestrator/3e83ba8aecc2`) has
                                                                                                                                                                                                                                  its `quality-gates-v2` run (`30368810017`) stuck `in_progress` on `QG slice (tests)`/`QG slice (checks)` for
                                                                                                                                                                                                                                  **56+ minutes** (started 14:31:47Z) as of this observation. `gh api .../actions/runners` confirms both of
                                                                                                                                                                                                                                  agent-orchestrator's own runners (`glue-ip-172-31-5-118-1`, `glue-ip-172-31-5-118-2`) show `online`/`busy` — same
                                                                                                                                                                                                                                  runner name (`glue-ip-172-31-5-118-1`) implicated in the SEPARATE `deployment-service` incident write-up
                                                                                                                                                                                                                                  (`ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md`) the same day. **Not
                                                                                                                                                                                                                                  escalating or intervening**: agent-orchestrator is one of the 2 deliberately-kept-self-hosted verified pools per
                                                                                                                                                                                                                                  this doc's own operator ruling above, so reverting its runner labels would be the WRONG fix and isn't what's
                                                                                                                                                                                                                                  happening here — this looks like the underlying shared-host contention resurfacing on an otherwise-correctly-
                                                                                                                                                                                                                                  configured repo's pool, not a misconfigured allowlist entry. Left the stuck run alone (canceling/retriggering a
                                                                                                                                                                                                                                  job two BUSY runners already claimed didn't look likely to help and risked adding load); it will resolve on its
                                                                                                                                                                                                                                  own once host contention clears or the `ldr-to-main-promote-fleet.yml` cron supersedes the PR to a newer LDR ref.
                                                                                                                                                                                                                                  Net effect on the citing plan: its dashboard-only commit (`agent-orchestrator@f120922`) is genuinely blocked from
                                                                                                                                                                                                                                  reaching `main`/Firebase Hosting by THIS pre-existing infra condition, not by anything in that plan's own code —
                                                                                                                                                                                                                                  documented there, not duplicated here beyond this evidence note.

## Evidence

- `execution-service` failing run: https://github.com/IggyIkenna/execution-service/actions/runs/30306813710
- `execution-service` hung promotion-PR run (canceled): `30309965212` (PR #501)
- `deployment-api` stuck queue: run `30306799237`, queued 2h28m+ at time of writing
- Allowlist: `scripts/workflow-templates/self-hosted-qg-repos.txt` (24 entries)
- `agent-orchestrator` PR #691 (`quality-gates-v2` run `30368810017`) stuck `in_progress` 56+min as of 2026-07-28 ~15:28
  UTC, both repo runners `online`/`busy` — see re-open-trigger note above (added while working an unrelated plan, not a
  full re-audit of this issue).
- Template wiring: `scripts/workflow-templates/rollout-workflow-templates.sh` `get_qg_runner_labels()` (line ~207-214),
  `scripts/workflow-templates/quality-gates-v2.yml.tmpl` line 67
- Fix shipped: `execution-service@<see quickmerge output>` (revert of `self_hosted_runner_labels` only)

## Progress Log

> **2026-07-29 line-cap remediation**: every 2026-07-28 corroboration/fix entry extracted verbatim to
> `/plans/archive/2026_07/fleet_wide_qg_self_hosted_runner_capacity_crisis_progress_log_history_2026_07_29.md` (doc was
> at 1015/1000 lines). New entries append below this note going forward.

**2026-07-29 ~15:51 UTC corroboration (market-tick-data-service, escalation agt-7a5abf, cicd agent slot-16,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #779 (head `5bf8a3c7`) —
`QG slice (tests)` failed on `test_tardis_free_only_gate.py::test_free_only_allows_recent_rolling_window`
(`Timeout (>60.0s)` from pytest-timeout), with two sibling tests in the same fully-mocked async test file at
394.52s/29.33s and several unrelated files in the same run also at anomalous 12-34s — the multi-file spread matches this
doc's existing signature (host contention, not a per-test bug); traced every line these tests execute and found no real
I/O, sleep, or retry loop that could explain minutes of wall-clock on fully-mocked code. PR lineage: #779 → closed
(superseded), #780 (`a6e0a788`) → closed (superseded), #781 (`dc82b08d`, current LDR HEAD) is live and its
`quality-gates-v2` already shows `success` with NO code change involved (auto-regenerated by
`ldr-to-main-promote-fleet.yml` against a newer ref); LDR-direct `quality-gates-v2` dispatches show the same flip-flop
(fail 01:35/03:03/04:30/06:56 UTC, pass 05:02/08:59/09:59 UTC) across commits that never touch the failing test.
Confirmed live contention on this orchestrator host at diagnosis time: `/proc/pressure/io` `some avg10=7.59`, 10Gi swap
in use of 47Gi, load 5.8-6.5 on 16 cores, a colocated `github-glue-runners/writer-2` process plus a concurrent
`instruments-service` QG pytest run and 7 other agent sessions. No code/test change made or needed — same "resolves once
host contention clears or the promote-cron supersedes to a newer ref" pattern as the 2026-07-28 agent-orchestrator PR
#691 entry above. No open repo-blockers for `market-tick-data-service` at check time.

**2026-07-30 ~15:14 UTC corroboration (features-service, escalation agt-7bcf55, cicd agent slot-2,
wall_type=ldr_qg_failure)**: dispatched on `ldr_qg_failure` for commit `6d4a9374` (run `30547641524`, `#0` no PR) —
`QG slice (checks)` failed with `Type check FAILED/timeout (exit=124)` (basedpyright ran unwrapped — systemd-run
unavailable on this host — past the 120s `PYRIGHT_TIMEOUT`), and `QG slice (tests)` failed on a pytest-timeout
thread-dump mid `test_feature_groups/test_momentum.py::test_adx_columns_present`, stuck inside a plain `pd.Series.std()`
call in `_check_constant_columns` (no I/O, no loop that could hang — a stack trace, not an infinite loop). Confirmed no
code/test delta in the hot path (`calculators/base.py`, `test_momentum.py`) between the failing commit and current LDR
HEAD (`f0fc6f2e`), and the two immediately-surrounding LDR runs (10:44, 12:35 UTC) were green against the same code.
`journalctl -u github-glue-runner-features-service@glue-1` shows the identical checks/tests timeout signature repeating
on two more independent runs (14:16-14:28 and 14:29-14:40 UTC — main-branch push + promote/features-service/b7e221d3 PR
triggers), ruling out a one-off flake tied to the escalated commit specifically. Live host state at diagnosis time:
`uptime` load average 27.0/29.5/25.5 (16 vCPU box), 12/47GB swap in use, `/proc/pressure/io` `some avg10=40.67`,
`/proc/pressure/cpu` `some avg10=17.86`, 47 glue-runner worker processes live — same whole-host-thrashing signature as
every other corroboration in this doc. `features-service` is one of the operator's 6 explicitly-restored/protected repos
(2026-07-28 ruling above), so per that ruling did **not** touch `self_hosted_runner_labels`. No code/test change made or
needed. A fresh `quality-gates-v2` re-run at current HEAD (`f0fc6f2e`, run `30553419354`, `workflow_dispatch`) was
already queued by an earlier retry (not by me) and had sat `queued` 27+ minutes with the sole `glue-1` runner reporting
`busy` — did not trigger a duplicate run against the same saturated single-runner pool. No open repo-blockers for
`features-service` at check time. Resolves once host contention clears or a newer LDR push supersedes this ref (same
pattern as the entries above).

**2026-07-31 ~01:35 UTC corroboration (features-service, escalation agt-33c1c1, cicd agent slot-10,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #904 (head `3bce3997`, run
`30593753225`) — `QG slice (tests)` failed on a pytest-timeout thread-dump: the MainThread stuck >60s inside
`_pytest/capture.py` `readouterr()` → `tmpfile.read()` during `pytest_runtest_setup`'s capture-snap for the item after
`tests/delta_one/unit/test_registry_invariants.py` (no user code on the stack — the hang is in pytest's own
global-capture FD read, the signature of a starved/stalled runner process, not a test-code defect). Struck by a
stronger-than-usual corroborating data point this time: the exact same commit (`3bce3997`) was ALSO run via
`workflow_dispatch` on `live-defi-rollout` (run `30593853513`, started 2 min after the PR run) and **passed clean in
58m57s** — same code, same SHA, one host-contended run failed and one succeeded, which rules out a code/test regression
definitively (not just "no diff found," an actual same-commit pass/fail split). By the time I reached this escalation,
PR #904 had **already merged** (`92c15600`, merged 00:30:52Z by `IggyIkenna` — 3s after the failing run even started,
evidently via a required-check path independent of this specific tests-slice run) and is on `main`; LDR has since
advanced to `c46509be` with its own green `quality-gates-v2` history. No code/test change made or needed. No open
repo-blockers for `features-service` at check time (`GET /api/repo-blockers` — empty for this repo). `features-service`
stays on the operator's 6 explicitly-restored/protected repos (2026-07-28 ruling above); did not touch
`self_hosted_runner_labels`. Third `features-service` corroboration of this exact signature in 3 days (2026-07-29,
2026-07-30, this one) — the pattern is firmly established for this repo specifically, not just fleet-wide.

**2026-07-31 ~05:45 UTC corroboration (features-service, escalation agt-97a0b4, cicd agent slot-14,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #912 (head `ce369620`, run
`30606331366`) — `QG slice (checks)` failed on `Type check FAILED/timeout (exit=143)`: the `[4/6] TYPE CHECK` section
header printed and the failure fired **under 0.2s later** (05:22:10.8066 → 05:22:10.9825), with 0 errors/0 warnings
extracted from `basedpyright`'s output — too fast to be the documented 120s `PYRIGHT_TIMEOUT` genuinely elapsing;
consistent instead with an external SIGTERM to the whole job's process group from host-level contention on the shared
`glue` runner (same signature class as this doc's other entries, just caught earlier in its lifecycle: signal delivered
at process start rather than after a multi-minute hang). Reproduced LOCALLY to rule out a code regression: fresh-pulled
`live-defi-rollout` (HEAD `ce369620`, matches the PR head exactly — not stale), ran
`QG_SLICE=typecheck bash scripts/quality-gates.sh` backgrounded — completed cleanly, `basedpyright` ran to completion
and reported `✅ QG_SLICE=typecheck PASSED` (964 pre-existing errors, all under the warn-only path since no
`BASEDPYRIGHT_MAX_ERRORS` ceiling is configured — non-blocking, unrelated to this failure). By the time I reached this
escalation, PR #912 had **already merged** (`5e974169`, merged `2026-07-31T05:16:06Z` — **3 seconds** after the failing
run even started at `05:16:03Z`, the same "merged via an already-satisfied required-check path independent of this
specific run" pattern as the #904 entry above — LDR's own `quality-gates-v2` at the identical SHA `ce369620` had already
gone green 14 minutes earlier at `05:01:42Z`) and is on `main`. No code/test change made or needed; no repo push
required. No open repo-blockers for `features-service` at check time (`GET /api/repo-blockers` → `{"open": []}`).
`features-service` stays on the operator's 6 explicitly-restored/protected repos (2026-07-28 ruling above); did not
touch `self_hosted_runner_labels`. Fourth `features-service` corroboration of this exact signature in 3 days
(2026-07-29, 2026-07-30, 2026-07-31 ×2) — reinforces this is a firmly-established repo-specific pattern, not a one-off.
Separately observed (out of this escalation's scope, not touched): `main-backmerge-to-ldr` failed twice on
`features-service` around this same window (runs `30605455733`, `30606335871`, step "Back-merge main into LDR
(merge-only; conflict → visible PR; never force)") — flagging for whichever worker next touches `features-service` CI
health, not diagnosed here.

**2026-07-31 ~13:40 UTC corroboration (features-service, escalation agt-63ed22, cicd agent slot-4,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #918 (head `f57d11ae`, run
`30632803681`) — BOTH matrix legs red: `QG slice (checks)` failed on `Type check FAILED/timeout (exit=124)`
(basedpyright ran to the full documented 120s `PYRIGHT_TIMEOUT` this time, unlike the #912 entry's sub-second SIGTERM
signature — same underlying cause, different point in the timeout window); `QG slice (tests)` failed on a pytest-timeout
thread-dump mid `tests/delta_one/unit/test_cross_timeframe_sanity.py::test_output_index_matches_input`, stuck inside a
plain `pandas.core.frame.select_dtypes` → `_config.using_copy_on_write` call chain (no I/O, no loop — ordinary pandas
internals, not a hang-prone code path). Reproduced LOCALLY end-to-end to rule out a code regression: fresh-pulled
`live-defi-rollout` (HEAD `f108477a`, contains PR head `f57d11ae` as an ancestor — not stale), ran the full
`bash scripts/quality-gates.sh` — **18055 passed, 209 skipped, 0 failed in 254.86s** (test file in question passed
clean, nowhere near any timeout threshold), confirming the tests leg is sound; separately ran
`QG_SLICE=typecheck bash scripts/quality-gates.sh --no-fix` in the foreground — completed in <90s and reported
`✅ QG_SLICE=typecheck PASSED` (964 pre-existing basedpyright errors, same figure as the #912 entry, all under the
warn-only path since no `BASEDPYRIGHT_MAX_ERRORS` ceiling is configured — non-blocking), confirming the checks leg is
sound too. Live host state at diagnosis time matched every prior corroboration's signature: `uptime` load average
26.81/33.36/33.41 (16 vCPU box), 16/47GB swap in use, `/proc/pressure/io` `some avg10=53.83` `full avg10=38.65`, 130
live `github-glue-runners` processes. By the time I reached this escalation, PR #918 had **already merged** (`eac5b902`,
`mergedAt=2026-07-31T13:01:17Z` — the same "merged via an already-satisfied required-check path independent of this
specific run" pattern as the #904/#912 entries above) and is on `main`; a fresh post-merge `main` push run
(`30634789136`) was sitting `queued` 19+ minutes at check time — same single-runner-saturation symptom as the #912
entry's 27-minute queue, not intervened on (canceling one queued run on an already-saturated single-runner pool wouldn't
help and risks adding load). No code/test change made or needed; no repo push required. No open repo-blockers for
`features-service` at check time (`GET /api/repo-blockers` → `{"open":[]}`). `features-service` stays on the operator's
6 explicitly-restored/protected repos (2026-07-28 ruling above); did not touch `self_hosted_runner_labels`. Fifth
`features-service` corroboration of this exact signature in 3 days (2026-07-29, 2026-07-30, 2026-07-31 ×3) — this is the
first of the five where BOTH legs failed on the SAME run rather than just one, consistent with worsening (not improving)
host contention on this shared box; flagging for whoever next reviews the fleet-wide capacity remediation timeline.

**2026-07-31 ~20:40 UTC corroboration (features-service, escalation agt-8ac0d7, cicd agent slot-6,
wall_type=ldr_qg_failure)**: dispatched on a direct-LDR `ldr_qg_failure` (`PR_NUMBER=0`, no PR). Checked the 3 most
recent `quality-gates-v2` runs on `live-defi-rollout`, all red: run `30640289115` (14:50:10Z) — `QG slice (tests)`
pytest-timeout thread-dump mid `test_cross_timeframe_sanity.py::test_output_index_matches_input`, stuck in
`_check_extreme_outliers` → `pandas.core.frame.select_dtypes`, the identical signature as the #918 entry above; run
`30655029889` (18:24:31Z) — `QG slice (checks)` `qg_red_reason=basedpyright` (a `Type check FAILED/timeout` variant);
run `30659440157` (19:31:53Z) — BOTH legs red again, and this run's `tests`-slice log contains a NEW, more direct piece
of evidence than any prior entry in this doc: the QG script's own governor fired explicitly —
`[qg-governor-watchdog] features-service pid=895711: host RAM pressure >= 80% for 2 consecutive checks — sending SIGTERM to its process tree`
— a first-party admission of host RAM exhaustion, not an inferred signature from load-average/swap/`/proc/pressure`
side-evidence the way every prior entry in this doc had to reconstruct it. Reproduced LOCALLY to rule out a code
regression: fresh-pulled `live-defi-rollout` (HEAD `97351fef`), ran
`tests/delta_one/unit/test_cross_timeframe_sanity.py -v --timeout=60` in isolation — **102 passed, 17 skipped in
8.14s**, the specific parametrization that hung in CI (`test_output_index_matches_input`) included and passing clean, no
margin concerns. Did not also re-run the full suite locally (redundant given the isolated-file result plus this doc's
already-exhaustive precedent — killed a duplicate full-suite background run started before finding this doc, to avoid
adding load to an already-contended shared host). No code/test change made or needed. A fresh `quality-gates-v2` run
(`30663077898`, `workflow_dispatch`) was already in flight at investigation time (auto-retriggered, not by me) — left
running, not intervened on. No open repo-blockers for `features-service` (`GET /api/repo-blockers` → `{"open":[]}`).
`features-service` stays on the operator's 6 explicitly-restored/protected repos (2026-07-28 ruling above); did not
touch `self_hosted_runner_labels`. Sixth `features-service` corroboration of this exact signature in 3 days (2026-07-29,
2026-07-30, 2026-07-31 ×4) — the explicit governor-watchdog RAM-pressure message is the strongest direct evidence yet
for this doc's standing root cause and may be worth citing if/when the fleet-wide capacity remediation is actually
scoped (todo list above, still open).

**2026-07-31 ~21:06 UTC corroboration (client-reporting-api, escalation agt-6d4271, cicd agent slot-3,
wall_type=ldr_qg_failure)**: dispatched on a direct-LDR `ldr_qg_failure` (`PR_NUMBER=0`, no PR) at commit `9ecb4a46`,
run `30655522780`. `QG slice (checks)` passed (7m33s); `QG slice (tests)` failed, but the pytest run itself completed
**665 passed, 4 skipped, 0 failed**, coverage 71.63% (≥70% required) — i.e. the suite was fully green. 4m42s of total
silence followed (no output at all), then `bash: ... line 23: 507490 Killed  bash scripts/quality-gates.sh --no-fix`
(exit 137) — a bare kernel SIGKILL (not the catchable-SIGTERM governor watchdog, which would have logged a
`[qg-governor-watchdog]` line first; none appears anywhere in the log), with the same
`⚠️ QG_MEM_CAP=2048M set but systemd-run unavailable on this host` gap this doc's root cause already tracks. Ruled out a
code cause directly: `9ecb4a46` is a 1-line `Dockerfile` `ARG BASE_IMAGE_DIGEST` bump (an automated dependency-pin
refresh unrelated to the venv-based test execution path) — and the identical commit-message pattern had passed clean
twice earlier the same day (`b3cc470`@07:00 UTC, `22dac144`@12:40 UTC). Live host state at diagnosis time (this
orchestrator host, which colocates `client-reporting-api`'s own `glue-1` runner alongside 24 other repos' pools):
`/proc/pressure/io` `some avg10=63.03 full avg10=52.03`, `/proc/pressure/memory` `some avg10=7.61 full avg10=6.67`, 129
live `github-glue-runners` processes across 25 colocated pools on 16 vCPUs — same whole-host-thrashing signature as
every other corroboration in this doc. Did not run a local full-suite reproduction: the failing run's own log already
shows a complete, clean, 100%-passing pytest execution (stronger evidence than a fresh local run), and this host itself
was already running 8 concurrent `quality-gates.sh --no-fix` processes at check time (over the `≤2 full QGs at once`
cap) — adding a 9th would only worsen the exact condition being diagnosed. A fresh `quality-gates-v2` run
(`30659427138`, `workflow_dispatch`, targeting current LDR HEAD `d2a2e01`) was already in flight at investigation time
(auto-retriggered, not by me); its `checks` slice passed and `tests` slice was still running past its own 40+ minute
mark — left running, not intervened on, per this doc's established "resolves once host contention clears or a newer LDR
push supersedes this ref" pattern. No code/test change made or needed. No open repo-blockers for `client-reporting-api`
at check time (`GET /api/repo-blockers` → `{"open": []}`). `client-reporting-api` is not one of the operator's 6
explicitly-restored/protected repos (2026-07-28 ruling above) and was not individually touched by this escalation — its
`self_hosted_runner_labels` were left as-is (a fleet-capacity allowlist decision, out of scope for a single wall). First
`client-reporting-api`-specific corroboration in this doc (the repo was already listed in this doc's own `repos:`
frontmatter from the original 2026-07-27 incident, but had no dedicated Progress Log entry until now).

**2026-08-01 ~01:31 UTC corroboration (client-reporting-api, escalation agt-922ac7, cicd agent slot-4,
wall_type=ldr_qg_failure)**: dispatched on `quality-gates-v2` FAILURE on promotion PR #623 (head `619367e64a06`, run
[30672419096](https://github.com/IggyIkenna/client-reporting-api/actions/runs/30672419096)). `QG slice (checks)` passed
(10m25s); `QG slice (tests)` failed at the dependency-install step, before any test ran: `uv sync --frozen` errored
`Failed to install: pytz-2025.2-py2.py3-none-any.whl ... Caused by: failed to hardlink file from .../.venv/lib/python3.13/site-packages/pytz/zoneinfo/America/Dominica to /home/ubuntu/.cache/uv/archive-v0/.../pytz/zoneinfo/America/Dominica: No such file or directory (os error 2)`
— a missing hardlink source in the shared `uv` cache. The same job's earlier `actions/cache@v4` restore step logged two
`tar: ... Cannot open: File exists` conflicts on unrelated `ccxt` cache entries, indicating a concurrent process was
writing the same shared cache directory at restore time — the mechanism, not just the symptom, matches this doc's root
cause exactly (colocated `glue` runner processes racing a shared host-level cache). Ruled out a code/dependency cause on
multiple independent axes: (1) `git log -S"pytz" -- uv.lock` shows the last touch to `pytz` in the lockfile predates
this incident by months (an unrelated old `feat` commit) — no recent lockfile change; (2) every LDR commit in the
failure window (`9ecb4a46`→`d2a2e01`→`e02d2f5`→`619367e`) is a trivial automated
`chore(deps): refresh base-image digest pin` / backmerge / promote commit, none touching `pyproject.toml`/`uv.lock`/test
code; (3) reproduced `uv sync --frozen` locally at the identical HEAD — `Audited 217 packages in 276ms`, zero errors;
(4) direct same-SHA split: LDR commit `d2a2e01` FAILED `quality-gates-v2` at 19:31:41Z (run `30659427138`, already
corroborated above by agt-6d4271) and PASSED at 21:24:37Z (run `30666455970`) with **zero code change between the two
runs**. By the time this was diagnosed the PR had already self-healed with no code change: PR #623
`mergedAt=2026-07-31T23:16:20Z` (merge commit `e3616d7c`, `Promoted-From-LDR: 619367e64a06`) — merged via the fleet's
own required-check path independent of this specific tests-slice run, same "required-check path independent of this
specific run" mechanism as the 2026-07-31 agent-orchestrator PR #691 and 2026-07-30 `client-reporting-api` PR #609
entries above. No open PRs on `client-reporting-api` at check time (`gh pr list --state open` → `[]`) and no open
repo-blockers (`GET /api/repo-blockers` → `{"open": []}`) — nothing is currently blocked. The direct-LDR
`workflow_dispatch` health check (`30672687292`, targeting a later LDR ref `12702a20`) was still `queued`/`in_progress`
2h+ after dispatch at check time — left alone, not retriggered (a stuck job on an already-saturated runner pool is not
helped by adding a duplicate dispatch, per this doc's established guidance). No code/test/workflow change made or
needed. `client-reporting-api`'s `self_hosted_runner_labels` left as-is (fleet-capacity allowlist decision, out of scope
for a single wall). Pinged the authoring slot (`ci`) with this outcome; slot left clean on `live-defi-rollout`, no repo
branch touched. Fourth `client-reporting-api`-specific corroboration of this exact signature in the last ~40h
(2026-07-29 ~21:00Z `agt-dfdd5b`, 2026-07-30 ~08:44Z `agt-08a769`#609, 2026-07-31 ~21:06 UTC `agt-6d4271`, this one) —
the recurrence rate for this repo specifically is now high enough that it reads as a standing property of its runner
pool, not an occasional flake; no action taken beyond corroborating, since the fleet-capacity remediation itself is
already tracked in this doc's own Todos/Follow-up (out of scope for a single-wall dispatch).

**2026-08-01 ~02:33 UTC corroboration (unified-api-contracts, escalation agt-bae355, cicd agent slot-2,
wall_type=ldr_qg_failure)** — first `unified-api-contracts`-specific entry in THIS doc (a prior corroboration for this
repo, PR #796, is logged in the day-2 continuation doc, `agt-0cd704` 2026-07-29 ~20:56Z). Dispatched on a
`quality-gates-v2` FAILURE on promotion PR #823 (head `18ed167f`, run
[30679154169](https://github.com/IggyIkenna/unified-api-contracts/actions/runs/30679154169)) — `QG slice (tests)` went
completely silent for ~90s after the `[3/6] TESTS` header printed (02:11:56→02:13:26) then a bare kernel `Killed` (exit
137), zero test output/traceback — the identical signature as the `client-reporting-api` `9ecb4a46` entry above
(2026-07-31 ~21:06 UTC), just with a shorter silent window. By the time I reached this escalation, PR #823 had **already
merged** (`mergedAt=2026-08-01T02:01:25Z`, merge commit `5fbef978`, `Promoted-From-LDR: 18ed167f`) — 3s after this run's
own `created_at` (02:01:22Z) and ~12 min before the tests-leg kill even happened — the same "merged via an
already-satisfied required-check path independent of this specific run" pattern as the #904/#912/ #918/#623 entries
above. No open PRs (`gh pr list --state open` → `[]`), no open repo-blockers (`GET /api/repo-blockers` → `[]`) — nothing
is currently blocked. Reproduced locally anyway for independent confirmation
(`QG_SLICE=tests bash scripts/quality-gates.sh --no-fix`, backgrounded, at the identical HEAD `18ed167f`): hit the SAME
root-cause class but caught by a more diagnostic mechanism than CI's bare kill — this repo's own `qg-governor-watchdog`
fired a genuine `SIGTERM` citing host RAM pressure and wrote a kill marker (`.benchmarks/qg-governor/killed.276516`:
`killed_by_signal=TERM, pid=276516, repo=unified-api-contracts`) rather than the run completing or a raw `SIGKILL`. This
is first-party, not-inferred confirmation that the root cause is live on THIS shared host right now, not reconstructed
from side-evidence: at diagnosis time `uptime` load average 24.85/25.64/24.22 (16 vCPUs), `/proc/pressure/io`
`some avg10=45.14 full avg10=34.20`, 19Gi/47Gi swap in use, 35 live `Runner.Listener` processes — matches this doc's
established contended-host signature. Did not retry a second full local pass — per the `client-reporting-api` entry's
same "adding a 9th would only worsen the exact condition being diagnosed" reasoning, and this session's own repro had
just demonstrated the host would kill it again. No code/test change made or needed. `unified-api-contracts` is not one
of the operator's 6 explicitly-protected repos, so no `self_hosted_runner_labels` decision applied here either way —
left untouched. Slot left clean on `live-defi-rollout`, no branch changes.

**2026-08-01 ~03:10 UTC (client-reporting-api, escalation agt-922ac7, cicd agent slot-5) — DUPLICATE dispatch of an
already-resolved escalation.** Same `escalation_id` (`agt-922ac7`) as the corroboration immediately above this one
(slot-4, ~01:31 UTC) — the identical wall re-dispatched to a second cicd worker rather than a fresh one, an orchestrator
dispatch-dedup gap distinct from the boot-misroute bug tracked in
`boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` (that one is a one-shot-role→worker-boot
misroute; this is a same-escalation-id redispatch to the same role). Independently re-verified rather than trusting the
prior entry blind: PR #623 still `MERGED` (`mergedAt=2026-07-31T23:16:20Z`, merge commit `e3616d7c`), current
`live-defi-rollout` HEAD `b6347c9` `quality-gates-v2` `success` (run `30681241055`, 2026-08-01T03:03:56Z), no open
repo-blockers (`GET /api/repo-blockers` → `{"open": []}`). Attempted to ping `AUTHORING_SLOT=ci` per the standard
completion step — `POST /api/slots/ci/message` 422s (`slot_id` must be an integer; `ci` denotes "CI-authored commit, no
human worker slot", not a numeric slot id — the endpoint cannot target it). No code/test change made or needed; slot
never touched the `client-reporting-api` repo tree (verified clean on `live-defi-rollout` before and after). Fifth
`client-reporting-api`-specific corroboration of this signature in this doc.

**2026-08-02 ~15:40 UTC corroboration (strategy-service, escalation agt-6f553d, cicd agent slot-13,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #482 (head `d4efea96722a`, run
[30748527240](https://github.com/IggyIkenna/strategy-service/actions/runs/30748527240)) — BOTH matrix legs red:
`QG slice (checks)` failed with `Type check FAILED/timeout (exit=124)` (basedpyright ran the full documented 120s
`PYRIGHT_TIMEOUT`); `QG slice (tests)` sat completely silent after `Coverage floor` printed, then hit its own job-level
`timeout-minutes: 135` and was force-canceled by GitHub (`##[error]The operation was canceled.`) with orphan
`bash`/`tee`/`python` processes still alive at cleanup — 2h13m of zero pytest output, not a per-test hang. Ruled out a
code/test regression on two independent axes: (1) zero `strategy_service` source changed since the last verified-green
promote (`074c8bc0`) — only a CI-workflow concurrency tweak (`d4efea96`, itself already proven fine on
unified-trading-library/unified-api-contracts the same day) and a Dockerfile digest-pin bump; (2) reproduced BOTH legs
locally at the identical LDR HEAD, backgrounded: `QG_SLICE=tests` → **5660 passed, 248 skipped, 22 xfailed, 0 failed in
62.93s**; `QG_SLICE=typecheck` → `✅ QG_SLICE=typecheck PASSED` (7 pre-existing non-blocking basedpyright warnings).
Confirmed live fleet-wide contention at diagnosis time, not just this repo: `uptime` load average 48.05/45.06/44.53 (16
vCPU box), 18/47Gi swap in use — matches this doc's established whole-host-thrashing signature — and cross-checked 3
other repos' live run queues, all showing the same multi-hour stall pattern simultaneously (market-tick-data-service:
promote-PR `quality-gates-v2` `in_progress` 2h38m+, `main`-push run queued 2h39m+; instruments-service: `main`-push run
queued 2h54m+; unified-api-contracts: `main`-push run failed after 1h37m, a `workflow_dispatch` on `main` queued 1h30m+)
— this is the fleet-wide condition this doc already tracks, not a new signature. Confirmed via
`setup-glue-runners.sh status` (run locally on this same orchestrator host, IP `172.31.5.118`, matching the implicated
`glue-ip-172-31-5-118-*` runner name in every prior entry) that the PM's own 8-runner pool (`glue-1..5`, `writer-1..3`)
is healthy/idle — the contention is on the _service repos'_ separate lone-runner registrations sharing this same
physical host's CPU/RAM, not a crashed PM pool. By the time I reached this escalation, PR #482 had **already merged**
(`mergedAt=2026-08-02T12:46:26Z`, merge commit `89082c00`, ~2s after the failing run's own `created_at`) — the same
"merged via an already-satisfied required-check path independent of this specific run" pattern as every prior
`#904`/`#912`/`#918`/`#623`/`#823` entry above. No open PRs on `strategy-service` (`gh pr list --state open` → `[]`), no
open repo-blockers (`GET /api/repo-blockers` → `{"open": []}`) — nothing is currently blocked. No code/test/workflow
change made or needed. `strategy-service` is one of the 5 repos this doc's own 2026-07-28 operator ruling explicitly
says to leave alone on the self-hosted allowlist ("the 2 repos whose revert never shipped (strategy-service,
system-integration-tests ...) alone too") — did **not** touch `self_hosted_runner_labels` or
`scripts/workflow-templates/self-hosted-qg-repos.txt`, consistent with every non-protected-repo corroboration in this
doc. Slot left clean on `live-defi-rollout` (only this doc touched); repo-blocker fast-path skipped (none open for
`strategy-service`). First `strategy-service`-specific Progress Log corroboration in this doc (the repo was already
listed in the original 2026-07-27 `repos:` frontmatter and named in the 2026-07-28 operator ruling, but had no dedicated
entry until now).

**2026-08-02 ~18:04 UTC — ml-service, escalation agt-6bc7d4, cicd agent slot-3, wall_type=ldr_qg_failure —
COUNTER-EXAMPLE, not a pure host-contention corroboration.** Dispatched on the same `quality-gates-v2` FAILURE on
promotion PR #328 (head `1c9570818a69`, run
[30748526106](https://github.com/IggyIkenna/ml-service/actions/runs/30748526106)) already investigated by slot-5 — a
duplicate dispatch of an already-resolved escalation, same pattern as the 2026-08-01 ~03:10 UTC `client-reporting-api`
entry above (`AUTHORING_SLOT=ci` also 422s on `/api/slots/ci/message` here, for the same reason: `ci` denotes a
CI-authored change, not a numeric slot). On arrival, found `live-defi-rollout` HEAD already at
`e5acff4836b1ada65e502f3a204efa93dc69576b` ("fix(tests): mock subprocess.Popen in distribute_training tests to stop real
training runs", author slot-5, `Quickmerge: agent`, committed 16:27:16Z — before this dispatch). **Unlike every prior
entry in this doc, this failure's genuine root cause was NOT whole-host contention starving an otherwise-innocent job —
it was a real code/test bug that then MANIFESTED via this doc's host-contention signature**:
`test_distribute_training_with_global_feature_selection_error` and `test_distribute_training_without_global_features`
never mocked `subprocess.Popen`/`_create_training_script`, so `distribute_training`'s process-launch path spawned REAL
python training subprocesses; the polling loop's `time.sleep(10)` then blocked ~82 minutes waiting on real training,
blowing the 150s pytest-timeout on those two tests directly AND starving the concurrent basedpyright typecheck leg (120s
hard cap) on the SAME shared self-hosted runner into its own timeout — a single runaway subprocess explains both the
`tests`-leg failures (matching this doc's signature) and the `checks`-leg `Type check FAILED/timeout (exit=124)` (also
matching this doc's signature) in one shot, with a 3rd tests-leg casualty
(`test_cascade_publisher.py::test_publish_returns_true_on_success`, 1213.77s vs its own 150s bound) most plausibly
collateral CPU/RAM starvation from the same rogue subprocess rather than an independent defect. Verified the fix is
correctly scoped (mirrors the already-correct mocking pattern in the sibling
`test_distribute_training_process_completion` in the same file) and complete (both named tests patched, no other
subprocess-spawning test paths found in the same module). PR #328 had **already merged**
(`mergedAt=2026-08-02T12:46:24Z`, merge commit `8e2d4feb`) via the same "required-check-satisfied-independent-of-this-
run" path as every prior corroboration — `main` now carries the pre-fix test code (the fix landed on LDR ~3.7h after the
promotion merged; it will ride the next LDR→main promotion, tests-only so no runtime/prod impact meanwhile). No open PRs
(`gh pr list --state open` → `[]`), no open repo-blockers (`GET /api/repo-blockers` → `{"open": []}`) — nothing is
currently blocked. Did not re-touch the fix or `self_hosted_runner_labels`; ml-service is one of the 10 RAM-aware-
governor-restored repos (2026-07-28 ruling above), not one of the 6 explicitly-protected repos, but no allowlist action
was warranted here regardless since the actual defect was in test code, not infra. **Flagging for whoever next reviews
this doc's aggregate pattern**: this doc's running signature list (pytest-timeout thread-dumps stuck in pure-stdlib/
pandas/pytest-internals calls with no user code on the stack) is a reasonably strong "no real root cause" tell, but a
timeout stuck inside actual application code that spawns subprocesses/threads (as here) deserves the same "trace every
line it executes" scrutiny this doc's own entries already apply before defaulting to the host-contention verdict — this
is the first entry in the doc where that scrutiny found a real bug instead of confirming there wasn't one.

**2026-08-02 ~18:20 UTC corroboration (market-tick-data-service, escalation agt-c9d4f8, cicd agent slot-6,
wall_type=ldr_qg_failure)** — dispatched on the same `quality-gates-v2` FAILURE already cross-checked in passing by the
~15:40 UTC `strategy-service` entry above ("market-tick-data-service: promote-PR `quality-gates-v2` `in_progress`
2h38m+, `main`-push run queued 2h39m+"); this is that repo's own dedicated entry. Failing run on promotion PR #815 (head
`bd991bc0`, run [30748529212](https://github.com/IggyIkenna/market-tick-data-service/actions/runs/30748529212)):
`QG slice (checks)` → `Type check FAILED/timeout (exit=124)`, basedpyright hit the full documented 120s
`PYRIGHT_TIMEOUT` with 0 errors/0 warnings captured (killed mid-analysis, not a real finding). Reproduced
`QG_SLICE=typecheck` locally at the identical `live-defi-rollout` HEAD (`3c51b3d0`), backgrounded:
`✅ QG_SLICE=typecheck PASSED` (933 pre-existing basedpyright warnings, no `BASEDPYRIGHT_MAX_ERRORS` ceiling set for
this repo, well under 120s) — no code regression. PR #815 had **already merged** (`mergedAt=2026-08-02T12:46:31Z`, ~3s
after the failing run's own start) via the same "required-check-satisfied-independent-of-this-run" path as every prior
`#904`/`#912`/`#918`/`#623`/`#823`/`#482` entry above. The identical `Type check FAILED/timeout (exit=124)` signature
then recurred a second time on this same repo's `main`-branch push-triggered `quality-gates-v2` run
([30748532256](https://github.com/IggyIkenna/market-tick-data-service/actions/runs/30748532256), job
`QG slice (checks)`, 17:42:42→17:44:43) — that run's own queueing gap is itself evidence of the fleet condition: its
`content sentinel` job finished at 12:46:47Z but `QG slice (checks)` didn't even START until 17:34:40Z, a ~4h48m wait
for a runner slot on this repo's single `glue-ip-172-31-5-118-1` registration (`gh api .../actions/runners` → 1 runner,
`busy=true`), followed by a separate `live-defi-rollout` `workflow_dispatch` re-run
([30758739206](https://github.com/IggyIkenna/market-tick-data-service/actions/runs/30758739206), same HEAD `3c51b3d0`)
sitting `queued` behind it for 45+ min with no progress at check time. Host-level corroboration at diagnosis time:
`uptime` load average 48.51/42.54/41.91 (16 vCPU box), swap 22Gi/47Gi in use — matches this doc's established
whole-host-thrashing signature exactly. No open PRs (`gh pr list --state open` → `[]`), no open repo-blockers
(`GET /api/repo-blockers` → `{"open": []}`) — nothing is currently blocked; the still-queued `workflow_dispatch` run
will pick up once a runner slot frees, no manual re-trigger needed. No code/test/workflow change made or needed on
`market-tick-data-service`; did not touch `self_hosted_runner_labels` or the allowlist. Bounded a background poll of the
queued re-run (~1 min, well short of the doc's established multi-hour clearance window) rather than holding the slot —
consistent with this doc's own guidance that further individual waits don't change the outcome, only fleet-capacity
remediation does. Slot left clean on `live-defi-rollout` (only this doc touched). Sixth repo-specific corroboration of
the `Type check FAILED/timeout (exit=124)` signature class in this doc.

## Follow-up

Migrated 2026-07-29 from `/plans/archive/issues/deployment_api_self_hosted_runner_capacity_recurrence_2026_07_29.md`
(2nd recurrence on deployment-api, fixed via `deployment-api@8561af10`) at archival time per the archival ritual's
"migrate any DEFERRED item into a real tracked todo" step — these 2 items were still open there despite that doc's own
`status: resolved`.

- [ ] [REVIEW] P2. When the `[SCRIPT] P0 allowlist-cleanup todo` above (the `market-data-processing-service`
      progress-log entry) is eventually actioned, cross-check whether `deployment-api` should be REMOVED from
      `scripts/workflow-templates/self-hosted-qg-repos.txt` entirely (not just hand-reverted in its own copy) so a
      future template rollout doesn't silently re-flip it a 3rd time the same way `a63f255` did — the per-repo hand-edit
      fixes the symptom but the shared allowlist is still the source-of-truth a rollout would read from.
- [x] [REVIEW] P3. **✅ DONE 2026-07-29.** Split done — `## Progress Log` history hoisted to
      `/plans/archive/2026_07/fleet_wide_qg_self_hosted_runner_capacity_crisis_progress_log_history_2026_07_29.md` (768
      lines extracted, doc went from 1015L to 250L).

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the allowlist posture is set by a live operator correction
  (2026-07-28, 'do not blanket-strip the fleet'); the single residual is a conditional cross-check gated on another todo
  being actioned first.

- **na-eligibility-audit 2026-07-31**: **CONFIRMS the verdict above, unchanged** — doubly so now. The residual
  `[REVIEW] P2` item is (a) still gated on the allowlist-cleanup todo, un-actioned, AND (b) independently
  already-extracted verbatim into the sibling `/ag-closeout-audit ci` skill's same-day draft
  `/plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (its own `[REVIEW] P2` item, citing this doc's
  `## Follow-up` as Source). Either reason alone would keep this NA; both together make it unambiguous. 3 commits since
  the prior marker (2026-07-30→07-31) are all pure Progress Log corroboration appends for `features-service`
  host-contention — no code/checkbox change, reinforcing the standing operator ruling, not undermining it.

- **na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA-STALE (already-duplicated), confirmed a third
  time. Verified `ci_satellite_ao_dispatch_batch4_2026_07_31.md` is still `status: draft` (not yet ingested) — its
  extraction of this item is real but not yet an ACTIVE duplicate per the strict rubric bar; reason (a) alone (still
  gated on the un-actioned allowlist-cleanup todo) independently keeps this doc NA regardless. No checkbox change needed
  this pass.
