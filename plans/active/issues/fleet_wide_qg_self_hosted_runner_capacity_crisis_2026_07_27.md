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
