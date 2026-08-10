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
archive_exempt: true
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
author: unknown
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
context_scope:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md,
    /codex/08-workflows/ci-cd-flow.md,
    scripts/workflow-templates/self-hosted-qg-repos.txt,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
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

> **2026-08-03 line-cap remediation**: every 2026-07-29 → 2026-08-01 corroboration entry extracted verbatim to
> `/plans/archive/2026_08/fleet_wide_qg_self_hosted_runner_capacity_crisis_progress_log_history_2026_08_03.md` (doc was
> at 995/1000 lines). New entries append below this note going forward (2026-08-02 entries onward were already below the
> extraction point and are unaffected).

- **2026-08-05 — post-runner-split partial re-verification**: all 25 self-hosted runner pools (fleet-wide, per
  `/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`) fully migrated off the old shared VM
  (`i-0c9b283b31d6b5ca7`) onto a dedicated escalation VM (`i-042a6332509482556`) as of today. Live `uptime` readings
  (both real, dated): old VM peaked at **65.63/65.19/56.76** load average on 16 vCPUs during the migration's final hour
  (worse than this issue's historical 25-50 range); new dedicated VM measured at **29.25/29.36/30.65** shortly after the
  split completed. **Verdict: real improvement (~roughly halved peak load), NOT fully resolved** — a same-window
  spot-check dispatch of 3 fresh `quality-gates-v2` runs saw 2 of 3 sit `queued` for the full ~2min check. This is a
  single spot-check, not a sustained-trend measurement — re-check after the fleet has run a full day on the new VM (and
  again once AO's box is downsized, `ci_runner_fleet_split...` todo 8, still on operator hold) before deciding whether
  to close or keep open with a lower baseline.

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

**2026-08-02 ~18:32 UTC corroboration (ml-service, escalation agt-d4bfa9, cicd agent slot-3, `wall_type=main_ci_red`)**
— first `main_ci_red`-wall_type entry in this doc (prior entries are `ldr_qg_failure`), extending its scope. Dispatched
on `main`'s `quality-gates-v2` FAILING (push-triggered run
[30748528741](https://github.com/IggyIkenna/ml-service/actions/runs/30748528741), promotion of PR #328 head
`1c9570818a69`) — the same underlying defect as this doc's own 2026-08-02 ~18:04 UTC ml-service "counter-example" entry
above (`test_distribute_training_without_global_features` real-subprocess timeout), already fixed on LDR
(`ml-service@e5acff48`, "fix(tests): mock subprocess.Popen..."), but that fix landed at `16:27:16Z` — **after** the
`12:46Z` promotion had already pushed the pre-fix commit to `main`. New finding beyond the 18:04 entry: read the fleet
promote-cron's own log (`ldr-to-main-promote-fleet.yml` run `30760695553`, `unified-trading-pm`, `18:15Z`) to see
exactly why the fix hasn't reached `main` yet:
`GATE BLOCK ml-service: ci_status=FAILING (cached='MAIN_GREEN', live='FAILING') — LDR CI is red; fix before LDR→main` —
LDR's OWN `quality-gates-v2` is currently red (run `30756959449`, `16:35Z`, an unrelated flaky pytest-timeout on
`test_shap_explainer.py`), which blocks the cron from promoting the already-fixed LDR HEAD to `main`. Watched a fresh
LDR retry already in flight (not started by me), run `30760924114` (`18:21Z`) — its `checks` job failed AGAIN at the
identical `Type check FAILED/timeout (exit=124)` signature this doc already tracks (6m3s, basedpyright hit the 120s
`PYRIGHT_TIMEOUT`). Live host corroboration at diagnosis time: `uptime` load average 49.21/46.23/43.46 (16 vCPU box),
17Gi/47Gi swap in use, `/proc/pressure/io` `some avg10=66.15 full avg10=36.96`, 35 `Runner.Listener` + 153 `glue`
processes — matches this doc's established severe-contention signature, consistent with today's simultaneous
strategy-service/market-tick-data-service corroborations above. No code/test/workflow change made or needed: the actual
defect is already fixed on LDR; `main` receives it automatically once (a) LDR's own `quality-gates-v2` goes green on a
future retry and (b) the next promote-cron tick (~15 min cadence) picks it up — no manual push to `main` performed or
warranted (HARD RULE), and did not retrigger a 3rd time per this doc's established "a duplicate dispatch to an
already-contended pool doesn't help" guidance. No open repo-blockers for `ml-service` (`GET /api/repo-blockers` →
`{"open": []}`). Pinged authoring slot with this outcome; slot left clean on `live-defi-rollout`.

**2026-08-02 ~18:35 UTC corroboration (deployment-api, escalation agt-dc6a1b, cicd agent slot-7,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #476 (head `4c4b007fd15d`, run
[30754057988](https://github.com/IggyIkenna/deployment-api/actions/runs/30754057988)) — `QG slice (checks)` failed on
`Type check FAILED/timeout (exit=124)`, basedpyright ran to the full 600s `PYRIGHT_TIMEOUT` this repo already carries
(bumped from 120s during its own 2026-07-28 recurrence, `deployment-api@8561af10` — see Follow-up below) before being
SIGKILLed. Initially misread this as organic codebase growth outstripping the existing budget and drafted a
PYRIGHT_TIMEOUT 600->1200s / MAX_DURATION 700->1400s bump plus a `qg_resource_baseline.json` reprofile — but the
reprofile itself undercut that theory (peak_rss 1483MB, stable/lower than the stale 1768MB entry, not evidence of
growth), and cross-checking this doc's own established signature before shipping caught the actual cause: this is the
SAME fleet-wide host contention every other entry here documents, not organic growth. Confirmed via the sanctioned
distinction in `/codex/06-coding-standards/quality-gates.md` ("PYRIGHT_TIMEOUT remains sanctioned for TRANSIENT
contention escapes... NOT the fix for a suite that has permanently grown") — reverted both drafted changes
(`git reset HEAD~1` + `git checkout --` on the unpushed local commit; the PM baseline edit was never committed) before
either reached origin. Reproduced locally at the identical PR head to rule out a code regression regardless:
`QG_SLICE=typecheck bash scripts/quality-gates.sh --no-fix` → `✅ QG_SLICE=typecheck PASSED` (303 pre-existing
basedpyright errors, no `BASEDPYRIGHT_MAX_ERRORS` ceiling configured, non-blocking; completed in 29-160s depending on
warm/cold cache, nowhere near 600s). Live host corroboration at diagnosis time: `uptime` load average 43.01/43.03/42.66
(16 vCPU box), swap 19Gi/47Gi in use, 156 `Runner.Listener`/glue processes live, dozens of concurrent `quality-gates.sh`
invocations observed fleet-wide across other slots at the same moment — matches this doc's established severe-contention
signature exactly. PR #476 had **already merged** (`mergedAt=2026-08-02T15:18:43Z`, merge commit `969bce02`, ~35 min
before the failing run's own investigation, well within the "required-check-satisfied- independent-of-this-run" pattern
every prior `#904`/`#912`/`#918`/`#623`/`#823`/`#482`/`#815`/`#328` entry above documents) and is on `main`. LDR's own
direct `quality-gates-v2` health is currently mixed (2 cancelled runs, 1 stuck `queued` 2h15m+ as of this write-up, run
`30756441204`) — left un-retriggered per this doc's established "a duplicate dispatch to an already-saturated
single-runner pool doesn't help" guidance; it will resolve once host contention clears or a newer LDR push supersedes
the ref. No open repo-blockers for `deployment-api` (`GET /api/repo-blockers` → `{"open": []}`). No code/test/workflow
change made or needed; slot left clean on `live-defi-rollout` (repo tree verified unmodified before/after — both drafted
commits were reverted). `deployment-api` runs exactly 1 lone `glue` runner (`glue-ip-172-31-5-118-1`, `busy=true` at
check time) — did not touch `self_hosted_runner_labels` (an out-of-scope fleet-capacity allowlist decision per the
2026-07-28 operator ruling above, same as every non-protected-repo corroboration in this doc). Second
`deployment-api`-specific Progress Log corroboration in this doc's timeline (the first is the archived 2026-07-29
recurrence cited in Follow-up below) — worth noting for whoever actions the open `[REVIEW] P2` allowlist-cleanup todo,
since this is now this repo's 3rd confirmed occurrence of the same signature.

**2026-08-02 ~19:30 UTC (deployment-api, escalation `agt-dc6a1b`, cicd agent slot-9) — DUPLICATE dispatch of the
already-resolved entry immediately above.** Same `escalation_id` (`agt-dc6a1b`), same `REPO`/`PR_NUMBER`
(deployment-api#476, run `30754057988`) as the ~18:35 UTC slot-7 entry above — the identical wall re-dispatched to a
second `cicd` worker, same dispatch-dedup gap as the 2026-08-01 ~03:10 UTC `client-reporting-api` duplicate entry.
Independently re-verified rather than trusting the prior entry blind: PR #476 still `merged=True`
(`merged_at=2026-08-02T15:18:43Z`), no open PRs on `deployment-api` (`gh pr list --state open` → `[]`), no open
repo-blockers (`GET /api/repo-blockers` → `{"open": []}`). Started an independent local
`bash scripts/quality-gates.sh --no-fix` reproduction (backgrounded) purely for a second data point; killed it partway
through `[4/6] TYPE CHECK` once this doc's already-exhaustive same-run corroboration (slot-7, ~18:35 UTC) surfaced —
redundant given the prior entry already reproduced `QG_SLICE=typecheck` clean at this exact PR head, and continuing
would only add another concurrent `quality-gates.sh` invocation to the same contended host this doc's root cause already
documents. No code/test/workflow change made or needed; slot never touched the `deployment-api` repo tree beyond the
killed reproduction process (no commits, no branch changes). Attempted to ping `AUTHORING_SLOT=ci` per the standard
completion step — expected the same 422 (`slot_id` must be an integer; `ci` denotes "CI-authored commit, no human worker
slot") as the precedented `client-reporting-api` duplicate entry.

**2026-08-02 ~21:30 UTC corroboration (alerting-service, escalation `agt-ab4093`, cicd agent slot-5,
wall_type=ldr_qg_failure)**: dispatched on a direct-LDR `ldr_qg_failure` (`PR_NUMBER=0`, no PR) at commit `356cec1`
(HEAD, up to date with origin — no incoming commits). Found the failing run (`30760911251`, `workflow_dispatch`, started
18:20:58Z): `QG slice (checks)` failed with `Type check FAILED/timeout (exit=124)` — basedpyright ran unwrapped
(systemd-run unavailable, `QG_MEM_CAP` warning present) and hit the full 120s `PYRIGHT_TIMEOUT`, same signature as the
`#912`/`#918` entries above; `QG slice (tests)` sat `in_progress` for **2h16m1s** before GitHub Actions itself canceled
it (`##[error]The operation was canceled.`) — no pytest-timeout thread-dump this time, the job never even reached a
verdict. That job's own cache-restore step also logged repeated `/usr/bin/tar: ... Cannot open: File exists` errors
across multiple unrelated `uv` cache archive members (google, nodejs_wheel, bandit, opentelemetry, fontTools, oauthlib
packages) — consistent with a second concurrent process on the same runner racing the same on-disk cache path, a
contention symptom this doc hadn't previously captured in this specific form. Reproduced LOCALLY at the identical commit
to rule out a code regression: fresh `live-defi-rollout` HEAD `356cec1` — ran `bash scripts/quality-gates.sh` twice,
once with the existing green content-sentinel (fast path, 36s, all gates including STEP-checks green) and once with
`.qg_content_sentinel`/`.qg_last_passed_sha` deleted to force a full cold run (82s, **910 passed, 8 warnings**,
basedpyright completed in seconds, `✅ ALL QUALITY GATES PASSED`) — both runs clean, confirming neither the typecheck
nor the test suite has a real regression. Live host state at diagnosis time matched this doc's established signature:
`uptime` load average 32.51/35.11/34.42 (16 vCPU box), 26/47GB swap in use, `/proc/pressure/io`
`some avg10=75.61 full avg10=53.86`, 149 live `github-glue-runners` processes.
`gh api repos/IggyIkenna/alerting-service/actions/runners` confirms the same lone-runner pattern
(`glue-ip-172-31-5-118-1`, `total=1`, `online`, `busy`) every prior corroboration in this doc has found. A fresh
`quality-gates-v2` run (`30767022900`, `workflow_dispatch`, not triggered by me) was already `queued`/`in_progress` 25+
minutes at check time on the same saturated single-runner pool — left running, not intervened on, per this doc's
established pattern (canceling a queued run on an already-saturated pool doesn't help and risks adding load). No
code/test change made or needed; no repo push required. No open repo-blockers for `alerting-service`
(`GET /api/repo-blockers` → `{"open": []}`). `alerting-service` is not one of the operator's 6
explicitly-restored/protected repos nor one of the 5 never-touched repos (2026-07-28 ruling above); its
`self_hosted_runner_labels` were left as-is (a fleet-capacity allowlist decision, out of scope for a single wall).
Pinged `AUTHORING_SLOT=planning` with the outcome.

**2026-08-02 ~21:35 UTC (alerting-service, escalation `agt-1b1528`, cicd agent slot-13, wall_type=ldr_qg_failure) —
DUPLICATE dispatch of the entry immediately above.** Same repo, same `PR_NUMBER=0` (direct-LDR wall, no PR), same
`AUTHORING_SLOT=planning`, dispatched within minutes of `agt-ab4093` (slot-5) at the same commit `356cec1`
(`live-defi-rollout` HEAD, still up to date — no incoming commits) — the same dispatch-dedup gap this doc already
documents for `deployment-api`/`client-reporting-api`. Independently reproduced rather than trusting the prior entry
blind: `bash scripts/quality-gates.sh` (backgrounded per the mandatory heartbeat pattern) on fresh `356cec1` →
`✅ ALL QUALITY GATES PASSED (67s)`, 910 tests passed, type check clean — no regression, matching the immediately-prior
entry's own two local reproductions. Checked the actual failing run (`30760911251`) independently: `QG slice (checks)`
failed on `Type check FAILED/timeout (exit=124)` (basedpyright hit the 120s `PYRIGHT_TIMEOUT` unwrapped — `QG_MEM_CAP`
set but `systemd-run` unavailable), `QG slice (tests)` sat `in_progress` 2h16m1s before GitHub Actions force-canceled it
— identical signature already fully diagnosed in the `agt-ab4093` entry above. The follow-on `quality-gates-v2` run
(`30767022900`) was still `queued` at check time, now 1h36m+ — left un-retriggered, same established reasoning (a
duplicate dispatch to an already-saturated single-runner pool doesn't help). No open repo-blockers
(`GET /api/repo-blockers` → `{"open": []}`). No code/test/workflow change made or needed; slot never diverged from
`live-defi-rollout` (no commits, no branch changes) other than this doc-only corroboration append. Pinged
`AUTHORING_SLOT=planning` with the outcome.

**2026-08-03 ~10:53 UTC corroboration + automation-gap finding (instruments-service, slot-11, data_engineering craft,
via `instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md` todo 12)**: same
signature, `quality-gates-v2` run `30800087100` (`workflow_dispatch`, started 09:07:46Z) — `content sentinel` completed
09:12:01Z but both QG-slice jobs (`tests`, `checks`) sat `queued` since 09:12:02Z, confirmed unchanged across 4
consecutive checks (todos 9-12 of that plan, spanning ~1h45m) against the repo's one registered `glue` runner
(`glue-ip-172-31-5-118-1`, reporting `online, busy` throughout). This blocks `instruments-service@ba87cc32` (a sports
writer fix) from reaching `main` (still 767 commits behind `live-defi-rollout` at check time). **New finding beyond
prior corroborations in this doc**: confirmed via direct code read (not assumption) that NEITHER existing automation
covers this specific queued-behind-busy-runner class. `ci_failure_watcher.py`'s `auto_recover_stuck_prs()`
(`scripts/repo-management/ci_failure_watcher.py:1642-1799`) only fires for a `BLOCKED`-state promotion PR matching one
of three signatures — `v2_present==False` (never fired at all), v2 concluded `action_required`, or a stale failed-check
— none of which describes this run (v2 DID fire; the stall is GitHub's own job scheduler leaving 2 jobs `queued` against
a runner that reports itself alive/busy, not a PR-merge-state condition at all). `glue-pool-starvation-monitor`
(`scripts/cicd/glue_pool_starvation_monitor.py`) is scoped `--repo IggyIkenna/unified-trading-pm` by default
(`find_starved_glue_jobs()`, its own docstring) and never queries `instruments-service`; even in-scope, its own
starvation rule (lines 111-127) treats "queued behind a busy runner" as normal backlog, not starvation, so it would not
fire on this pattern regardless of repo. No runbook covers "restart a live/busy single self-hosted runner to unstick a
GitHub-side queued job" (`central-vm-relaunch-glue-runner-reinstall.md` only covers post-VM-relaunch reinstall). Added a
Follow-up todo below for this gap rather than filing a duplicate P1 doc (same root incident/repo/runner this doc already
tracks at P0). No code/workflow change made; slot did not intervene on the stuck jobs (cancelling a runner-claimed job
to force a retry doesn't help a saturated single-runner pool, same established reasoning above).

**2026-08-03 ~20:24 UTC corroboration (market-data-processing-service, escalation agt-39c3cb, cicd agent slot-4,
wall_type=ldr_qg_failure)**: dispatched on `quality-gates-v2` FAILURE on promotion PR #572 (head `8ce3378e2a1d`, run
[30842791604](https://github.com/IggyIkenna/market-data-processing-service/actions/runs/30842791604)) —
`QG slice (tests)` failed during `uv sync --frozen` before any test ran:
`Failed to install: fastapi-0.140.7-py3-none-any.whl — Caused by: failed to open file .../.cache/uv/archive-v0/1JAeNkDjDkEUoCsNM4SjH/fastapi-0.140.7.dist-info/METADATA: No such file or directory (os error 2)`
— the identical shared-cache-race signature as this doc's `pytz`/`vcrpy`/`botocore` entries. By dispatch time PR #572
had **already merged** (`mergedAt=2026-08-03T18:46:42Z`, 1s after this failing run's own `createdAt`) via the fleet's
required-check-path-independent-of-this-run mechanism, same pattern as prior entries. Independently reproduced at the
exact merged LDR HEAD (`28ffed1`) anyway: `bash scripts/quality-gates.sh` (backgrounded) →
`✅ ALL QUALITY GATES PASSED (54s)`, confirming the code is genuinely green and the failure was host-side. No open PRs,
no open repo-blockers (`GET /api/repo-blockers` → `[]`). No code/test/workflow change made or needed.
`AUTHORING_SLOT=ci` is not a real numbered slot (per this role's own skip rule) — not pinged; the dispatch-time Slack
alert already covered the FYI. Slot never diverged from `live-defi-rollout`.

**2026-08-04 ~10:20 UTC corroboration + stale-repo-blocker fix (market-tick-data-service, escalation agt-bb7054, cicd
agent slot-3, wall_type=ldr_qg_failure)**: dispatched on `quality-gates-v2` FAILURE on promotion PR #819 (head
`06cd3ca5`, run [30849674872](https://github.com/IggyIkenna/market-tick-data-service/actions/runs/30849674872)) —
`QG slice (checks)` failed during `uv sync` before any check ran:
`Failed to install: botocore-1.41.5-py3-none-any.whl — Caused by: failed to hardlink file from .../.venv/.../botocore/data/bcm-data-exports/... to /home/ubuntu/.cache/uv/archive-v0/.../botocore/... No such file or directory (os error 2)`
— the identical shared-cache-race signature as this doc's `pytz`/`vcrpy`/`fastapi`/`botocore` entries. PR #819 had
**already merged** (`mergedAt=2026-08-03T20:19:13Z`, same second as the failing run's own `createdAt`) via the fleet's
required-check-path-independent-of-this-run mechanism, same pattern as every prior entry above. **New finding beyond a
pure corroboration**: `GET /api/repo-blockers` showed a genuinely open, STALE blocker for this repo — `RB-e7d79260`
(kind `qg_red`, condition `repo-market-tick-data-service-qg-green`, opened 2026-08-03 22:59:04 by a prior slot-3 session
for the pip-audit `cryptography` CVE-2026-69247 finding, 4 slots registered as waiters). The underlying fix
(`market-tick-data-service@f4c16feb`, "bump cryptography 49.0.0 -> 50.0.0", committed 23:49:06 — AFTER the blocker
opened) had already landed but the blocker was never auto-cleared by the RepoHealthWatcher. Verified the fix is
genuinely live rather than trusting the git log alone: confirmed `pyproject.toml`'s pin now reads
`cryptography>=50.0.0,<51.0.0`, then ran `.venv/bin/python -m pip_audit -l` directly (fast, targeted — ~90s vs a full
suite run) → **"No known vulnerabilities found"**. Also started a full local `bash scripts/quality-gates.sh --no-fix`
reproduction (backgrounded); it reached 6800+/9988 tests (68%) with zero failures (only expected skips/xfails) before
the backgrounded process was killed with no exit trace — live host state at the time showed a dozen+ _other_ slots'
concurrent `quality-gates.sh`/pytest invocations, consistent with this doc's established severe-contention signature,
not a code-side kill. Did not retry the full run (would only add another concurrent invocation to the same contended
host per this doc's own established guidance) — the targeted `pip_audit -l` result plus the partial zero-failure test
run plus the confirmed dependency-pin change were treated as sufficient evidence per this doc's evidentiary bar.
Resolved the stale blocker: `POST /api/repo-blockers/RB-e7d79260/resolve {"source": "reporter"}` →
`{"ok": true, "waiters_notified": 4}` — freed slots 3/8/5/11 (each got an immediate orchestrator nudge to resume their
tradfi/vault tasks on this repo). `AUTHORING_SLOT=ci` is not a real numbered slot (per this role's own skip rule) — not
pinged. Slot never diverged from `live-defi-rollout` (only this doc touched). First entry in this doc combining the
established stale-CI-signal corroboration pattern with an actual stuck-automation fix (a stale repo-blocker, not just a
noisy CI run) — worth noting for whoever eventually actions the P1 automation-gap todo below, since this is a second
class of automation gap (blocker-resolution lag) distinct from the queued-behind-busy-runner gap already tracked there.

**2026-08-04 ~11:35-13:35 UTC (deployment-api, escalation `agt-85e0c1`, cicd agent slot-2, wall_type=ldr_qg_failure)**:
dispatched on `quality-gates-v2` FAILURE on `live-defi-rollout` (commit `6650577e`, run
[30846199952](https://github.com/IggyIkenna/deployment-api/actions/runs/30846199952)). By dispatch time LDR had moved 2
commits ahead to `d06e5f7` (a dep-only `chore(deps)` digest-pin bump); the latest actual failing run at that tip was
[30903062326](https://github.com/IggyIkenna/deployment-api/actions/runs/30903062326), `QG slice (tests)` FAILED on 2
tests: `test_route_venue_year_coverage.py::test_total_and_remaining_computed` (`Failed: Timeout (>150.0s)`) and
`test_route_deployments_inventory.py::test_inventory_route_live_path_mocks_registry_and_cloud_run`
(`AssertionError: assert '...' in set()`). Both tests fully mock their external dependencies (registry/Cloud Run/GCE),
so ruled out a genuine logic regression before touching code: `uv sync` + `uv run pytest tests/` locally (full suite,
matching the `PYTEST_WORKERS=4`/`--timeout=150` invocation) → **5289 passed, 17 skipped, 0 failed in 28.67s** — both
"failing" tests pass cleanly, including in isolation. The decisive signal: CI's own log shows `QG slice (tests)` took
**2827.79s (47m07s)** wall-clock for the identical test set that ran in 28.67s locally — a ~100x slowdown, not a
code-side symptom. This matches this doc's established severe-contention signature exactly (deployment-api's 3rd-4th
confirmed occurrence — see the 2026-08-02 ~18:35/19:30 UTC entries above), and the timeout

- empty-set-assertion pairing is consistent with a real (mocked-path) socket call getting blocked/slow under host
  contention and an upstream broad exception handler degrading to an honest-empty result rather than propagating — same
  root cause, not two separate bugs. Re-triggered once (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`,
  run [30907879446](https://github.com/IggyIkenna/deployment-api/actions/runs/30907879446)) per this doc's evidentiary
  bar (a single confirmation dispatch, not a retry loop) to rule out a stuck/queued run rather than genuine contention —
  it started immediately (not queued) and `QG slice (checks)` went green, but `QG slice (tests)` was still `in_progress`
  past 13:35 UTC (85+ min, exceeding even the 47min baseline), consistent with this doc's "1-2.5+ hour" precedent under
  sustained load. Did not retrigger a 3rd time or attempt to fix `deployment_api` code/tests per this doc's established
  "a duplicate dispatch to an already-saturated single-runner pool doesn't help" guidance — left the confirmation run
  30907879446 running unattended; it (or a future LDR push) will resolve the `ci_status` once host contention clears. No
  open repo-blockers for `deployment-api` (`GET /api/repo-blockers` → `{"open": []}`). No open PRs on `deployment-api`.
  No code/test/workflow change made or needed; slot tree verified clean + unmodified on `live-defi-rollout` throughout.
  `AUTHORING_SLOT=ldr-ci-monitor` is not a real numbered slot (per this role's own skip rule) — not pinged. **Outcome
  confirmed**: run 30907879446's `QG slice (tests)` finally completed at 13:44:04 UTC — `started_at=12:10:10Z` to
  `completed_at=13:44:04Z` = **1h33m54s** wall-clock (vs 28.67s locally) — and the whole `quality-gates-v2` run went
  **green**, on the exact same unmodified tree, closing this wall. This is the strongest evidence yet in this doc that
  the failure mode is pure host contention with no code component: identical code, identical tests, red under load /
  green once the runner got a turn. LDR `ci_status` for `deployment-api` should now read `FEATURE_GREEN` (no manual push
  needed — the workflow's own `ci-status-update` step records it).

## Follow-up

Migrated 2026-07-29 from `/plans/archive/issues/deployment_api_self_hosted_runner_capacity_recurrence_2026_07_29.md`
(2nd recurrence on deployment-api, fixed via `deployment-api@8561af10`) at archival time per the archival ritual's
"migrate any DEFERRED item into a real tracked todo" step — these 2 items were still open there despite that doc's own
`status: resolved`.

- [x] ✅ [REVIEW] P2. When the `[SCRIPT] P0 allowlist-cleanup todo` above (the `market-data-processing-service`
      progress-log entry) is eventually actioned, cross-check whether `deployment-api` should be REMOVED from
      `scripts/workflow-templates/self-hosted-qg-repos.txt` entirely (not just hand-reverted in its own copy) so a
      future template rollout doesn't silently re-flip it a 3rd time the same way `a63f255` did — the per-repo hand-edit
      fixes the symptom but the shared allowlist is still the source-of-truth a rollout would read from. **RECONCILED
      2026-08-09 (ci_satellite_ao_dispatch_batch6_finalize todo 1) — already done, stale checkbox.** Decided +
      implemented via `ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s own `[REVIEW] P2` todo: **DECISION: YES,
      remove** — `unified-trading-pm@917fc626a` (verified ancestor of `origin/live-defi-rollout`). `deployment-api`
      confirmed NOT in the active `self-hosted-qg-repos.txt` allowlist (already removed 2026-08-05 as part of the
      15-public-repos cleanup); this doc's own checkbox was simply never flipped.
- [x] ✅ [SCRIPT] P1. Automation gap (found 2026-08-03 via `instruments-service` run `30800087100`, see Progress Log
      entry above): a `quality-gates-v2` run whose QG-slice jobs sit `queued` for hours behind a live/busy single
      self-hosted runner is caught by NEITHER `ci_failure_watcher.py`'s `auto_recover_stuck_prs()`
      (PR-`BLOCKED`-state-scoped, three signatures, none of which is "jobs queued behind a busy runner") NOR
      `glue_pool_starvation_monitor.py` (hardcoded to `--repo unified-trading-pm` only, and its own rule treats
      queued-behind-busy as normal backlog, not starvation, even in-scope). Either (a) generalize
      `glue_pool_starvation_monitor.py` to sweep every self-hosted-runner-flipped repo (not just PM) and add a
      queued-job-age threshold that pages/escalates regardless of reported runner busy-state, or (b) extend
      `auto_recover_stuck_prs()`'s signature set to also detect a `workflow_dispatch`/promotion run whose downstream
      jobs have been `queued` past a threshold with the upstream job already `success` (repo: unified-trading-pm —
      `scripts/cicd/glue_pool_starvation_monitor.py`, `scripts/repo-management/ci_failure_watcher.py`). **DONE
      2026-08-08 (`ci_satellite_ao_dispatch_batch6` todo 3) — unified-trading-pm@b073c47f9** (verified ancestor of
      `origin/live-defi-rollout`). (a) `find_stalled_glue_jobs()` + `--busy-queued-min 120` + `--repos-file` fleet sweep
      added to `glue_pool_starvation_monitor.py` (option (a) taken); 5 new regression tests; workflow timeout 5→10m. (b)
      Separately confirmed `glue-runner-crash-loop-watchdog.sh` did NOT page for the 2026-08-05 89-restart
      `agent-orchestrator` crash-loop (bug in watchdog comment lines 309-321, fixed same session).
- [x] [REVIEW] P3. **✅ DONE 2026-07-29.** Split done — `## Progress Log` history hoisted to
      `/plans/archive/2026_07/fleet_wide_qg_self_hosted_runner_capacity_crisis_progress_log_history_2026_07_29.md` (768
      lines extracted, doc went from 1015L to 250L).

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the allowlist posture is set by a live operator correction
  (2026-07-28, 'do not blanket-strip the fleet'); the single residual is a conditional cross-check gated on another todo
  being actioned first.

- **na-eligibility-audit 2026-07-31**: **CONFIRMS the verdict above, unchanged** — doubly so now. The residual
  `[REVIEW] P2` item is (a) still gated on the allowlist-cleanup todo, un-actioned, AND (b) independently
  already-extracted verbatim into the sibling `/ag-closeout-audit ci` skill's same-day draft
  `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (its own `[REVIEW] P2` item, citing this doc's
  `## Follow-up` as Source). Either reason alone would keep this NA; both together make it unambiguous. 3 commits since
  the prior marker (2026-07-30→07-31) are all pure Progress Log corroboration appends for `features-service`
  host-contention — no code/checkbox change, reinforcing the standing operator ruling, not undermining it.

- **na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA-STALE (already-duplicated), confirmed a third
  time. Verified `ci_satellite_ao_dispatch_batch4_2026_07_31.md` is still `status: draft` (not yet ingested) — its
  extraction of this item is real but not yet an ACTIVE duplicate per the strict rubric bar; reason (a) alone (still
  gated on the un-actioned allowlist-cleanup todo) independently keeps this doc NA regardless. No checkbox change needed
  this pass.

**2026-08-03 ~11:03 UTC corroboration (market-data-processing-service, escalation `agt-7784b3`, cicd agent slot-6,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #569 (head
`23aad425a8689d4b11f7088c98cc857237289937`, run
[30790876831](https://github.com/IggyIkenna/market-data-processing-service/actions/runs/30790876831)) — both
`QG slice (tests)` and `QG slice (checks)` red. The `tests` leg's own log shows the real pytest suite genuinely
completed (two `PluggyTeardownRaisedWarning`/`OSError: cannot send (already closed?)` xdist-worker-teardown messages at
08:26:36-08:26:40Z, no test-failure output anywhere in the log — no `short test summary`, no `FAILED`/`AssertionError`
line), then **41 minutes of complete silence** before `##[error]QG selector 'tests' FAILED (leg=tests, exit=1)` at
09:07:56Z — the same "silent multi-minute gap with no diagnostic output, real work already finished" signature this
doc's other entries document (client-reporting-api/unified-api-contracts bare-`Killed`, deployment-api/alerting-service/
strategy-service basedpyright-timeout-124, market-tick-data-service/ml-service same). Considered and ruled out this
commit's own newly-added QG step (`scripts/quality-gates.sh` section `[7.1] TEST-IMPACT SELECTOR — SHADOW MODE`, landed
same-commit `1c8588c7`, `test_impact_selector.py`/`import_graph_walker.py` — a same-day trial from
`test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`): it has no `run_timeout` wrapper (unlike the sibling
6.Y/5.X sections) so a hang there was a live suspect, but (a) it's fail-open by construction (`|| :` on its one python
invocation, cannot itself produce `_qg_rc=1` for the `tests` selector), (b) this repo is small (251 tracked `.py` files,
properly `.venv`-excluded) so `build_import_edges` has no plausible multi-minute cost, and (c) the local reproduction
below hit this exact section and it resolved sub-second
(`RUN_FULL_SUITE=true reason="no HEAD~1 diff available or no .py files changed"` — HEAD~1 only touched
`quality-gates.sh` itself, no `.py` diff to classify). Reproduced LOCALLY end-to-end at the identical LDR HEAD
(`1c8588c7`, `origin/live-defi-rollout` — matches, not stale): `bash scripts/quality-gates.sh --no-fix` (backgrounded
per the mandatory heartbeat pattern) → **`✅ ALL QUALITY GATES PASSED (86s)`**, real pytest execution confirmed (not a
stale-sentinel skip — full `[3/6] TESTS` output present, **2332 passed, 2 skipped, 43 warnings in 28.33s**),
typecheck/codex-compliance/production-readiness sections all green, the new `[7.1]` shadow section logged and exited
clean — no code/test regression anywhere. By the time this was reached, PR #569 had **already merged**
(`mergedAt=2026-08-03T06:38:48Z`, merge commit visible via `gh pr view`, `~1s` after the failing run's own
`createdAt=06:38:47Z`) via the same "required-check-satisfied-independent-of-this-run" path as every prior
`#904`/`#912`/`#918`/`#623`/`#823`/`#482`/`#815`/`#328`/`#476` entry above — `main` already has it, no open PRs
(`gh pr list --state open` → `[]`), no open repo-blockers (`GET /api/repo-blockers` → `{"open": []}`). Live host state
at diagnosis time matched (and exceeded) this doc's established signature: `uptime` load average 41.30/32.01/29.66 (16
vCPU box, worse than most prior entries), swap 19Gi/47Gi in use, `/proc/pressure/io`
`some avg10=65.68 full avg10=37.04`, 149 live glue/`Runner.Listener` processes; separately confirmed the currently
in-progress direct-LDR `quality-gates-v2` dispatch (`30792603292`, started 07:09:31Z) has been running **3h51m+** at
check time (documented-normal duration is 8-15 min) and a `main`-push run (`30790880111`) has sat `queued` **4h22m+** —
both left un-retriggered/un-canceled per this doc's established "a duplicate dispatch to an already-saturated
single-runner pool doesn't help" guidance. `gh api .../actions/runners` confirms the same lone-runner pattern
(`glue-ip-172-31-5-118-1`, `total=1`, `online`, `busy=true`) every prior corroboration in this doc has found. No
code/test/workflow change made or needed; did not touch `self_hosted_runner_labels` or the allowlist
(`market-data-processing-service` is not one of the operator's 6 explicitly-protected repos nor the 5 never-touched
repos — a generic non-protected entry, out of scope for a single wall regardless). Slot left clean on
`live-defi-rollout` (only this doc touched: no commits, no branch changes to the service repo). Pinged
`AUTHORING_SLOT=ci` with this outcome (expected the same `slot_id must be an integer` 422 the `client-reporting-api`/
`deployment-api` duplicate entries above already document for the literal `ci` authoring-slot value — a CI-authored
commit, not a numeric worker slot). First `market-data-processing-service`-specific corroboration in this doc.

**2026-08-03 ~11:55 UTC second corroboration (market-data-processing-service, escalation `agt-1f1e67`, cicd agent
slot-8, `wall_type=main_ci_red`, `pr_number=0`)**: dispatched on the `main`-push `quality-gates-v2` run
([30790880111](https://github.com/IggyIkenna/market-data-processing-service/actions/runs/30790880111), the same
merge-of-#569 commit `54b596e6` the entry immediately above already diagnosed) framed as "MAIN CI RED" rather than
`ldr_qg_failure` — classified per the escalation's own (A)/(B) framing before concluding neither applies cleanly: (A)
promotion-stuck does NOT apply (`gh pr list --state open --base main` → `[]`, PR #569 already merged
`mergedAt=06:38:48Z`); (B) stale-workflow-on-main does NOT apply either (the workflow definition is fine, the required
check DID report — it genuinely ran and failed). The actual condition is the same fleet-wide single-runner capacity
crisis this doc already tracks, just surfaced via the `main`-push check specifically. Independently re-verified rather
than trusting the prior entry: `git fetch` + `rev-parse` confirmed `live-defi-rollout` HEAD is unchanged since the prior
entry (`1c8588c78605f1370e5b751bb2aa2457c5e757e1`, one commit ahead of what merged into `main`, that one extra commit
being the fail-open `[7.1]` test-impact-selector shadow-mode trial — non-regressing by construction), then ran a fresh
independent local `bash scripts/quality-gates.sh --no-fix` (backgrounded, heartbeated) at that same HEAD:
**`✅ ALL QUALITY GATES PASSED (108s)`, 2332 passed, 2 skipped, 43 warnings** — confirms, a second time, zero code/test
regression. `gh api .../actions/runners` still shows the identical lone runner (`glue-ip-172-31-5-118-1`, `online`,
`busy=true`); `GET /api/repo-blockers` → `{"open": []}`. **New concrete downstream-impact confirmation (not previously
spelled out this explicitly in this doc)**: checked the fleet promote workflow's own most recent tick
(`ldr-to-main-promote-fleet` run `30810912821`, `unified-trading-pm`, 11:47:20Z) — its log shows
`GATE BLOCK market-data-processing-service: ci_status=FAILING (cached='FAILING', live='FAILING') — LDR CI is red; fix before LDR→main`
AND `⚠️ BLOCKED (dep not on main yet): system-integration-tests → dep market-data-processing-service is FAILING`, i.e.
this repo's stuck `ci_status` is actively holding back BOTH its own next promotion cycle AND
`system-integration-tests`'s dep-ordered promotion — this is the live mechanics behind why "self-clears" here isn't
purely cosmetic; it resolves the moment ANY subsequent run for this repo goes green (the currently in-flight direct-LDR
dispatch `30809754899`, started 11:29:42Z, still `queued`/`in_progress` on `QG slice (tests)` at check time, is that
candidate — left un-retriggered/un-canceled, same established "don't add to an already-saturated single-runner queue"
reasoning as every entry above). No code/test/workflow change made; slot touched only this doc, left clean on
`live-defi-rollout` in the service repo (`git status --short` empty post-run). `AUTHORING_SLOT=planning` is not a
numeric slot id, so the completion ping to `/api/slots/<n>/message` was skipped per `cicd.md`'s own carve-out (no real
numbered originator to notify — the dispatch-time Slack alert already covered the FYI).

**2026-08-03 ~12:40 UTC corroboration (execution-service, escalation `agt-bd0d27`, cicd agent slot-14,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #538 (head `9ad9265fe170`, run
[30790876666](https://github.com/IggyIkenna/execution-service/actions/runs/30790876666)) — part of the SAME synchronized
promotion wave the market-data-processing-service#569 entry above already documents: both runs' `createdAt` is
`2026-08-03T06:38:47-48Z`, one second apart. `QG slice (checks)` failed at the dependency-install step, before any test
ran: `uv sync --frozen` errored
`Failed to install: vcrpy-8.2.1-py3-none-any.whl (vcrpy==8.2.1) — Caused by: failed to read directory /home/ubuntu/.cache/uv/archive-v0/IrEVifhONTNQem83y0Dbe: No such file or directory (os error 2)`
— the identical missing-shared-uv-cache-entry signature as the 2026-08-01 `client-reporting-api` pytz entry above (a
concurrent glue-runner process racing/evicting the same cache path mid-read); `QG slice (tests)` was `cancelled` as a
side effect of the `checks` leg's fail-fast roll-up, not an independent failure. Confirmed the specific cache directory
now EXISTS and is populated (checked directly on this shared host, which colocates `execution-service`'s own `glue`
runner alongside 24 other repos') — consistent with a transient race, not permanent corruption. Ruled out a
code/dependency regression: `git log -S"vcrpy" -- uv.lock` shows no recent lockfile touch; reproduced the FULL suite
locally at the exact HEAD (`b68bc236`, `origin/live-defi-rollout` — not stale): `bash scripts/quality-gates.sh`
(backgrounded per the mandatory heartbeat pattern) → **`✅ ALL QUALITY GATES PASSED (165s)`, 7811 passed, 21 skipped, 1
xpassed, 0 failed**, typecheck/codex-compliance/production-readiness sections all green. PR #538 had **already merged**
(`mergedAt=2026-08-03T06:38:49Z`, merge commit `9ad9265f`, ~2s after the failing run's own start) via the same
"required-check-satisfied-independent-of-this-run" path as every prior corroboration above; no open PRs
(`gh pr list --state open` → `[]`), no open repo-blockers (`GET /api/repo-blockers` → `{"open": []}`) — nothing is
currently blocked. Live host state at diagnosis time matched (and exceeded) this doc's established signature: `uptime`
load average 23.12/23.43/24.16 (16 vCPU box), 17Gi/47Gi swap in use, `/proc/pressure/io`
`some avg10=65.52 full avg10=50.14`, 139 live `github-glue-runners` processes, 35 `Runner.Listener` processes.
Post-merge `main`-push `quality-gates-v2` (`30790881175`) is still red with the same signature; a direct-LDR
`workflow_dispatch` (`30805151319`) has sat `queued` 2h20m+ and a `main`-push `workflow_dispatch` (`30812209370`) 33m+
at check time — both left un-retriggered/un-canceled per this doc's established "a duplicate dispatch to an
already-saturated single-runner pool doesn't help" guidance; resolves once host contention clears or a newer LDR push
supersedes the ref. `execution-service` currently carries `self_hosted_runner_labels: '["self-hosted","glue"]'`
(re-flipped back to self-hosted at some point after this doc's own originating 2026-07-27 incident reverted it to
`ubuntu-latest`) — not one of the operator's 6 explicitly-protected repos nor the 5 never-touched repos, so per every
non-protected-repo precedent above, did **not** touch `self_hosted_runner_labels` or the allowlist (a fleet-capacity
decision out of scope for a single wall). No code/test/workflow change made or needed; slot left clean on
`live-defi-rollout` (repo tree verified unmodified: `git status --short` empty, HEAD still `b68bc236` =
`origin/live-defi-rollout`). `AUTHORING_SLOT=ci` is not a numeric slot id, so the completion ping to
`/api/slots/<n>/message` was skipped per `cicd.md`'s own carve-out (no real numbered originator to notify — the
dispatch-time Slack alert already covered the FYI). First `execution-service`-specific Progress Log corroboration in
this doc since the original 2026-07-27 incident.

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): KEEP-NA, valid/mixed — re-read end-to-end.
Both open items live in `## Follow-up` (everything in `## Recommended fix path` is already `[x]`). (1) Whether to remove
`deployment-api` from `scripts/workflow-templates/self-hosted-qg-repos.txt` — three PRIOR audit passes (2026-07-30/31,
2026-08-01) all landed KEEP-NA; re-verified live that `deployment-api` is still present in the actual allowlist file,
and that `ci_satellite_ao_dispatch_batch4_2026_07_31.md` (status: draft) already carries a verbatim-scoped version of
this exact item (line 188, citing this doc by name) — respecting that existing extraction vehicle rather than opening a
competing one. (2) Brand-new item (added today, ~10:53 UTC) presenting two unresolved alternative implementation
approaches without picking one — a design choice, not a bounded task. No RECLASSIFY, no ARCHIVE.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged — verified all still resolve and remain
  the right minimal reading list for this doc's ongoing corroboration pattern).

**2026-08-03 ~17:40 UTC corroboration (features-service, escalation agt-0a8231, cicd agent slot-3,
wall_type=ldr_qg_failure)**: dispatched on `ldr_qg_failure` for commit `abff85a3` (run `30818407385`, `#0` no PR,
resolved 13:32-14:28Z) — `QG slice (tests)` failed on a pytest-timeout thread-dump stuck inside
`test_feature_groups/test_momentum.py::test_volume_momentum_columns_present` (`_add_lagged_features` → `pd.concat` →
pandas' `_instancecheck`, no user loop/I-O on the stack), and `QG slice (checks)` separately failed with
`Type check FAILED/timeout (exit=124)` after `basedpyright` sat on `[4/6] TYPE CHECK` for ~5 min — the identical
dual-slice-timeout signature as the 2026-07-30/07-31 `features-service` entries above. Ruled out a code/test regression:
no commits touched `calculators/base.py` or `momentum.py` since 2026-07-31 (`git log --since=2026-07-31` on both paths →
empty); reproduced the specific failing test in isolation (`2.73s`, PASSED) and the full
`tests/delta_one/unit/test_feature_groups/` directory (309 tests, `27.17s`, all PASSED) at the exact escalated HEAD.
Root cause confirmed as the same shared-host capacity crisis this doc tracks:
`gh api repos/IggyIkenna/features-service/actions/runners` caught the repo's sole `glue-1` runner `status=offline` at
first check (systemd `github-glue-runner-features-service@glue-1.service` restart counter at 314-315, consistent with
this doc's documented ephemeral-per-job cycling, not a crash-loop); live host state at diagnosis: `uptime` load average
30.92/30.46/27.33 (16 vCPU box), 14Gi/47Gi swap in use, `/proc/pressure/io` `some avg10=49.40 full avg10=27.05`, 141
`github-glue-runners`-tree processes / 33 `Runner.Listener` processes — same whole-host-thrashing signature as every
prior entry. An hourly `workflow_dispatch` re-run (`30837377996`) was already `queued`/running against current HEAD at
check time (not triggered by me) — per this doc's established guidance, did not add a duplicate dispatch to the
already-saturated single-runner pool; left it running rather than blocking on completion. No code/test/workflow change
made or needed; `features-service` stays on the operator's protected-repo set so `self_hosted_runner_labels` was not
touched. No open repo-blockers for `features-service` at check time (`GET /api/repo-blockers` → `{"open": []}`). Slot
left clean: `git status --short` empty in the `features-service` worktree, HEAD unchanged at `origin/live-defi-rollout`.
`AUTHORING_SLOT=ldr-ci-monitor` is not a numeric slot id, so the completion ping to `/api/slots/<n>/message` was skipped
per `cicd.md`'s carve-out. Fourth `features-service`-specific corroboration of this exact signature (2026-07-29 is
fleet-wide/MTDS, 2026-07-30, 2026-07-31 ×2, this one) — the pattern remains firmly established for this repo.

**2026-08-03 ~17:40 UTC corroboration (unified-api-contracts, escalation `agt-499d33`, cicd agent slot-7,
wall_type=main_ci_red — first entry for this new escalation type)**: dispatched on a red `main`-branch
`quality-gates-v2` with `live-defi-rollout` reported green. Promotion PR #834 (`Promoted-From-LDR: 079d48ff46b2`) had
**already merged** (`mergedAt=2026-08-03T11:48:17Z`) — the post-merge `main`-push `quality-gates-v2` run
([30810979867](https://github.com/IggyIkenna/unified-api-contracts/actions/runs/30810979867)) failed 4h11m25s later:
`QG slice (tests)` —
`FAILED tests/internal/unit/test_sports_prediction_contracts.py:: test_prediction_market_trades_validates_sample_dataframe - Failed: Timeout (>150.0s) from pytest-timeout`
alongside **12265 passed, 739 skipped, 5 xfailed** in the same run — the failing test itself is a trivial single-row
`pd.DataFrame`/`validate_dataframe` assertion with no I/O or loop, i.e. no plausible 150s+ genuine runtime; matches this
doc's established host-contention-timeout signature, not a code regression. A prior manual `workflow_dispatch` retrigger
on `main` ([30830936327](https://github.com/IggyIkenna/unified-api-contracts/actions/runs/30830936327), 16:10:23Z)
failed with the **identical single-test signature** 1h11m31s later. `gh api .../actions/runners` at diagnosis time
showed both registered runners (`glue-ip-172-31-3-59-1`, `glue-ip-172-31-5-118-1`) `online`/`busy:true`.
`unified-api-contracts` is one of the 5 repos this doc's 2026-07-28 operator ruling explicitly left
untouched/self-hosted (never reverted) — consistent with every non-protected-repo precedent above, did **not** touch
`self_hosted_runner_labels` or the allowlist. No open repo-blockers (`GET /api/repo-blockers` → `{"open": []}`). Since
`main` had no other dispatch already queued/in-flight (unlike the "don't duplicate a saturated queue" cases above), this
new `wall_type` genuinely needed _some_ re-fire to have any chance of flipping `main`'s `ci_status` back green (a merged
promotion PR alone does not re-run the check) — re-triggered once more
([30837867269](https://github.com/IggyIkenna/unified-api-contracts/actions/runs/30837867269), in flight at report time),
left running per this doc's "resolves once host contention clears" pattern rather than blocking the one-shot session on
a run that has historically taken hours. No code/test/workflow change made or needed. Slot's `unified-api-contracts`
tree left clean and untouched on `live-defi-rollout` (never checked out this fix in the slot — diagnosis was read-only
via `gh`). `AUTHORING_SLOT=ci-reconcile` is not a numeric slot id, so the completion ping was skipped per `cicd.md`'s
own carve-out (no real numbered originator — `server/ci_reconcile.py`'s self-detected bare wall). First
`main_ci_red`-wall-type corroboration in this doc.

**2026-08-03 ~18:25 UTC corroboration (greeks-service, escalation `agt-62c091`, cicd agent slot-3,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #402 (head
`020ac0ad864bb4f7a4b7c9dc61050459f7c011a9`, run
[30837609087](https://github.com/IggyIkenna/greeks-service/actions/runs/30837609087)) — `QG slice (tests)` failed at the
dependency-install step, before any test ran: `uv sync --frozen` errored
`Failed to install: botocore-1.43.14-py3-none-any.whl (botocore==1.43.14) — Caused by: failed to hardlink file from .../.venv/lib/python3.13/site-packages/botocore/data/sso/2019-06-10/endpoint-rule-set-1.json.gz to /home/ubuntu/.cache/uv/archive-v0/.../botocore/data/sso/2019-06-10/endpoint-rule-set-1.json.gz: No such file or directory (os error 2)`
— the identical missing-shared-uv-cache-entry signature as the 2026-08-01 `client-reporting-api` pytz entry and the
2026-08-03 `execution-service` vcrpy entry above (a concurrent glue-runner process racing/evicting the same cache path
mid-write). Ruled out a code/dependency regression: `git log -S"botocore" -- uv.lock` shows the last touch to `botocore`
predates this incident by the repo's original skeleton commit (months old); the LDR HEAD's own most recent commit
(`020ac0a`, "chore(deps): re-pin unified-trading-library to 0.72.0") is an unrelated major-floor re-pin, not a
`botocore`/AWS-SDK change; `live-defi-rollout`'s own recent `quality-gates-v2` history is unbroken green (5 consecutive
successful runs, most recent 27s content-sentinel hit at 03:05 UTC same day, well before this failure). Reproduced the
FULL suite locally at the exact HEAD (`2e7e783a292e21c88e01e35e9f0f52c64ce83108`, `origin/live-defi-rollout` — not
stale): `bash scripts/quality-gates.sh --no-fix` (backgrounded per the mandatory heartbeat pattern) →
**`✅ ALL QUALITY GATES PASSED (121s)`, 179 passed + 6 passed (2 warnings)**, dependency install (incl. `botocore`)
succeeded cleanly outside CI, typecheck/codex-compliance/production-readiness sections all green — no code/test
regression anywhere. By the time this was diagnosed, PR #402 had **already merged** (`merged=true`,
`merged_at=2026-08-03T17:37:40Z`, ~1s _before_ the failing run's own `createdAt=17:37:41Z`) via the same
"required-check-satisfied-independent-of-this-run" path as every prior `#904`/`#912`/`#918`/`#623`/`#823`/`#482`/`#815`/
`#328`/`#476`/`#569`/`#538`/`#834` entry above — `main` already has it (confirmed `main-backmerge-to-ldr` and
`Semver Agent` both green on the merge push); no open PRs (`gh api .../pulls/402` → `state=closed`), no open
repo-blockers for `greeks-service` (`GET /api/repo-blockers` → `{"open": []}` filtered). Live host state at diagnosis
time matched this doc's established signature: `uptime` load average 44.11/35.97/31.55 → 41.08/39.76/33.91 (16 vCPU
box), `/proc/pressure/io` `some avg10=58.11 full avg10=28.23`, 159 live `github-glue-runners` processes. No
code/test/workflow change made or needed. `greeks-service` is one of the operator's 6 explicitly-protected repos
(2026-07-28 ruling above — features-service, fund-administration-service, greeks-service, ibkr-gateway-infra,
instruments-service, market-tick-data-service), so `self_hosted_runner_labels` was left untouched, consistent with every
protected-repo precedent above. Slot left clean: `git status --short --branch` shows `live-defi-rollout` tracking
`origin/live-defi-rollout` with zero diff in the `greeks-service` worktree (repo untouched, no checkout/branch change).
`AUTHORING_SLOT=ci` is not a numeric slot id, so the completion ping to `/api/slots/<n>/message` was skipped per
`cicd.md`'s own carve-out (no real numbered originator to notify — the dispatch-time Slack alert already covered the
FYI). First `greeks-service`-specific Progress Log corroboration in this doc (the repo was already listed in the
`repos:` frontmatter and the 2026-07-28 "6 restored repos" list, but had no dedicated corroboration entry until now).

**2026-08-03 ~21:47 UTC corroboration (deployment-api, escalation `agt-c7f2be`, cicd agent slot-8,
wall_type=ldr_qg_failure)**: dispatched on a `quality-gates-v2` FAILURE on promotion PR #478 (head `e922a72b8716`, run
[30842805784](https://github.com/IggyIkenna/deployment-api/actions/runs/30842805784)) — `QG slice (tests)` failed at the
`uv sync` dependency-install step, before any test ran:
`error: Failed to install: multidict-6.7.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (multidict==6.7.1) — Caused by: failed to read directory /home/ubuntu/.cache/uv/archive-v0/23WH4PLRVu_nU6W-sI14T: No such file or directory (os error 2)`
— the identical shared-`uv`-cache-race signature this doc already tracks (a concurrent colocated `glue` job
pruning/rewriting the same cache dir mid-install), not a code or lockfile change. By the time I reached this escalation,
PR #478 had **already merged** (merge commit `94b9411`, `mergedAt=2026-08-03T18:46:51Z`) — the `main-backmerge-to-ldr`
and `Semver Agent` checks on the merge push both show `success`, and my own `live-defi-rollout` worktree already carries
the backmerge (`git log` shows `94b9411 chore(promote): LDR → main` +
`6650577 Merge remote-tracking branch 'origin/main' into _backmerge` at HEAD, tree clean). No open PRs
(`gh pr list --state open` → `[]`) and no open repo-blockers for `deployment-api` (`GET /api/repo-blockers` → filtered
empty) — same "required-check-satisfied-independent-of-this-run" self-heal path as every prior entry above. Live host
state at diagnosis time matched this doc's established signature: `uptime` load average 24.29/23.27/25.07 (16 vCPU box),
`/proc/pressure/io` `some avg10=64.25 full avg10=48.57`, `/proc/pressure/memory` `some avg10=18.47`. No code/test/
workflow change made or needed. A separate `push`-triggered `quality-gates-v2` run on `main` (`30842810802`) was still
`queued` 3h+ at check time — left alone (post-merge, non-blocking, same "stuck job on an already-saturated pool" pattern
as prior entries; a duplicate dispatch would only add load). `AUTHORING_SLOT=ci` is not a numeric slot id, so the
completion ping was skipped per `cicd.md`'s own carve-out. Slot left clean: `deployment-api` worktree untouched,
`live-defi-rollout` tracking `origin/live-defi-rollout` with zero diff. Second `deployment-api`-specific corroboration
of this exact signature in this doc (see 2026-08-02 ~18:35 UTC entry above).

**2026-08-04 ~09:53 UTC corroboration (alerting-service, interactive session) — DEVIATION FROM PATTERN: cancelled rather
than left alone, because the hang was blocking the shared runner itself, not just its own PR.** Investigating a
fleet-wide deploy stall (unrelated tradfi manifest-fix work needed `unified-api-contracts@0.91.0`, git-tagged but never
reaching the package registry — `publish-package` queued 2+ hours on `main`), found the single `glue-ip-172-31-3-59-1`
self-hosted runner `busy=true` with `quality-gates-v2` run
[30886137054](https://github.com/IggyIkenna/alerting-service/actions/runs/30886137054) stuck on its `QG slice (checks)`
job's **`Post Cache uv package cache` step** — `in_progress` since `2026-08-04T09:05:03Z`, 48+ minutes on a step that
normally completes in seconds (this doc's prior entries diagnose slow/failed _main_ steps under contention; a post-step
cache-save hanging this long is a different, more severe failure mode — the runner process itself, not just the job,
looks wedged). Unlike every prior entry above (confirm self-heal already happened, leave alone), this run was the ONLY
thing occupying the fleet's one shared runner, so nothing else — including the `publish-package` run this session
actually needed — could even start. Ran `gh run cancel 30886137054`; status transitioned `in_progress` → `queued` (GH's
cancel-in-flight state) within seconds, confirming the runner was still responsive to signals (not fully hung at the OS
level, just stuck in this one step). Not verified further this session (queue-drain confirmation) — context-constrained
handoff, see Deferred table.

**2026-08-05 ~10:00-10:40 UTC — post-migration evidence on `ci-escalation-runner-vm-1` (i-042a6332509482556): bottleneck
is DISK THROUGHPUT, not CPU/IOPS — plus a genuine, now-fixed crash-loop bug.** Fills the
`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` todo's own stated gap ("not done: a longer-window
measurement... filed as a follow-up in this issue doc directly"). Investigating why a manually-dispatched
`Deploy Dashboard` run for `agent-orchestrator` sat queued 45+ min, found:

- **`iostat -x` on the box's `nvme0n1` (gp3, 300GB, baseline 3000 IOPS / 125 MB/s throughput — no provisioned extra):
  `rkB/s` ≈126,192 KB/s (≈126 MB/s) — AT the 125 MB/s baseline throughput ceiling, `%util` 89.5%, `aqu-sz` (avg I/O
  queue depth) 101.35, `r_await` 46.77ms (high for gp3/NVMe).** `vmstat` confirms: `wa` (iowait) 70%, `b`
  (uninterruptible-sleep/blocked procs) 124-180 at a time. `ps aux` found **52 processes system-wide in `D` state** at
  once (blocked on I/O, not runnable) — this is the actual mechanism behind the previously-reported high load averages
  (the earlier "load average 310" reports in this doc were never disambiguated CPU-bound vs I/O-bound; this measurement
  shows it is predominantly I/O-bound). Raw IOPS (~2169 total r/s+w/s) was well under the 3000 IOPS cap — **the binding
  constraint is the 125 MB/s throughput baseline, not IOPS or the 16 vCPUs.**
- Confirms and quantifies the rightsizing plan's own finding ("halved peak load, contention NOT eliminated") — the box
  has real, mostly-idle CPU headroom most of the time (per-process CPU% mostly 0.4-0.9% across the ~52 concurrent runner
  processes sampled), so **more vCPUs / a bigger instance would not directly fix this** — the fix is either (a)
  provision higher gp3 throughput (cheap, no-downtime AWS change, up to 1000 MB/s on the same volume), or (b) reduce
  concurrent disk-heavy job count, since throughput is shared across whatever's running at once regardless of vCPU
  count. Total registered runner units on this box right now: **34** (PM=8 [5 glue + 3 writer], agent-orchestrator=3 [2
  glue + 1 writer], 23 other repos=1 each) — PM and AO are the only repos with >1 glue slot; the other 23 are already at
  the minimum (1 each).
- **Separately, found and fixed a genuine bug** (not the throughput issue, a distinct root cause for agent-orchestrator
  specifically being stuck): `github-glue-runner-ao@glue-1.service` was crash-looping (89 consecutive restarts) on
  `status=4/NOPERMISSION` — misleading label; the actual cause was `scripts/self-hosted-runners/glue-runner-run.sh`'s
  stale-registration cleanup: `curl -fsS -X DELETE ... || true` silently swallowed a transient `422` on the delete call,
  so the stale registration was never actually removed, and the immediately-following `generate-jitconfig` call then
  failed `409 "already exists"` on every single restart, forever — a crash loop with zero diagnostic trail (the response
  body was never captured/logged). Reproduced the exact same DELETE call manually outside the tight restart loop with
  the same token — it succeeded immediately (`HTTP 204`), consistent with a transient failure under host I/O pressure
  rather than a real permission/state problem. **Fixed**: the delete now retries 3x with backoff and logs the actual
  HTTP status + body on every failed attempt (`unified-trading-pm@a4eb9a288`,
  `scripts/self-hosted-runners/glue-runner-run.sh`). The manual delete unblocked agent-orchestrator's glue-1/glue-2
  immediately; the code fix prevents recurrence for any repo hitting the same race, but has NOT yet been re-deployed to
  the live VM copy at `/opt/github-glue-runners-ao/glue-runner-run.sh` (a static `install`-copied file, not git-tracked
  live — requires re-running `setup-glue-runners.sh` or a direct file push; not done this session).
- **Not done / follow-up**: (1) redeploy the fixed wrapper script to the live VM; (2) operator decision on
  throughput-provisioning vs. concurrency-reduction (or both) — reducing PM's 5 glue slots and/or AO's 2 is the most
  direct concurrency lever, but touches fleet-wide CI capacity and needs explicit sign-off before executing; (3) check
  whether `glue-runner-crash-loop-watchdog.sh` (RESTART_THRESHOLD=5 by default) actually paged for the 89-restart
  agent-orchestrator crash-loop — if it didn't, that watchdog itself has a gap worth a separate look.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — actively-evolving P0 incident, operator ruling on allowlist
posture

**na-eligibility-audit 2026-08-07** (tranche `ci`): KEEP-NA, valid — confirms the established verdict. Both residual
`- [ ]` items remain open: the `[REVIEW] P2` allowlist cross-check is still gated on its own prerequisite todo being
actioned first (`DEPENDENCY_BLOCKED`); the `[SCRIPT] P1` automation-gap item (generalize
`glue_pool_starvation_monitor.py` or extend `auto_recover_stuck_prs()`) reads as individually bounded/deterministic in
isolation — flagging for a possible future RECLASSIFY look — but this is still an actively-evolving P0 incident doc with
a live operator-set allowlist posture, not defaulted-to-NA-and-never-assessed; not reclassifying here.

**2026-08-08 — [SCRIPT] P1 implementation (ci_satellite_ao_dispatch_batch6-002)**

Sub-item (b) ANSWERED — did `glue-runner-crash-loop-watchdog.sh` page for the 89-restart agent-orchestrator crash-loop?

**Answer: NO — the watchdog did NOT page.** Evidence is the watchdog script's own comment at lines 309–321 of
`scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh` (fixed `unified-trading-pm@<sha>` below): a bare
`systemctl list-units --type=service --all` without a pattern argument does not reliably enumerate JIT-ephemeral
`glue-N` template instances that have cycled out of systemd's in-memory unit cache between jobs — it returned only 1
line (the watchdog's own service unit) even with ~68 real glue-runner units genuinely present. The empty `alerted-units`
state file (no entries ever written) corroborates this: the watchdog ran through the entire 89-restart episode without
once detecting a unit over the `RESTART_THRESHOLD=5` default. Fix (passing an explicit `github-glue-runner-*` pattern to
`systemctl`) was also applied 2026-08-05. No separate follow-up needed for the watchdog — the fix shipped that same day.

Sub-item (a) SHIPPED — glue starvation detection generalised (mode 2 added):

Implementation choice: extend `glue_pool_starvation_monitor.py` rather than `auto_recover_stuck_prs()`. Rationale:
`auto_recover_stuck_prs()` is PR-state-scoped and only fires for `BLOCKED`-state PRs with specific signatures; the stall
occurs on direct-LDR dispatch runs too (not just PRs), so the starvation monitor is the correct conceptual home. The fix
adds `find_stalled_glue_jobs()` (mode 2: pool oversubscribed) alongside the existing `find_starved_glue_jobs()` (mode 1:
pool dead):

- **Mode 2** fires when an `in_progress` workflow run has `glue`-labelled jobs still individually `queued` past
  `--busy-queued-min` (default 120m). The 120m threshold is 3× the usual QG runtime and deliberately higher than mode
  1's 20m — short queuing behind a live runner is normal.
- `--repos-file scripts/workflow-templates/self-hosted-qg-repos.txt` sweeps the full fleet so a stall in any service
  repo pages even if PM itself is fine.
- Workflow updated: `timeout-minutes: 5→10`, `--repos-file` and `--busy-queued-min` wired in.
- 5 new regression tests added: stalled-case fires, healthy-fresh-case silent, no-queued-glue silent, bad-ts skipped,
  multi-job-one-run fires both.
- `build_report()` now produces distinct STARVED vs STALLED sections; healthy message names both thresholds so silence
  is falsifiable. **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — checked both residual
  open items against today's 9 operator-Q&A precedents; none apply. The `[REVIEW] P2` allowlist cross-check stays
  KEEP-NA-STALE (already-duplicated) — still gated on its own prerequisite todo being actioned first AND independently
  tracked in `ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s own `[REVIEW] P2` item. The `[SCRIPT] P1` automation-gap
  item flagged 2026-08-07 as a possible RECLASSIFY candidate was in fact already shipped via
  `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 3 (`unified-trading-pm@b073c47f9`) — its write-up already lives
  in this doc's own 2026-08-08 Progress Log entry; the checkbox itself should be flipped `[x]` by whoever next lands a
  commit here (stale-checkbox correction, not a fresh dispatch). No `assigned_vm` change; this remains an
  actively-evolving P0 incident doc with a live operator-set allowlist posture.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.

- **2026-08-09 (`ci_satellite_ao_dispatch_batch6_finalize` todo 1, slot 31)**: flipped the doc's 2 remaining `- [ ]`
  checkboxes (both confirmed already-done, stale — see D6-8-equivalent reasoning above), bringing the checkbox count to
  0 open. **Set `archive_exempt: true` rather than archiving or marking `status: resolved`**: this is a genuine
  false-zero — real open work survives in PROSE form, not checkboxes: the `## Follow-up` "Not done / follow-up" list
  item (1) "redeploy the fixed wrapper script to the live VM" is still not done, and item (2) "operator decision on
  throughput-provisioning vs. concurrency-reduction" is still operator-gated open (matches batch6's own D6-4 Deferred
  entry, unresolved as of this pass). `check_archive_candidates` only counts `- [ ]`/`- [x]` checkboxes, so it cannot
  see this — `archive_exempt: true` documents the reason rather than letting the mechanical gate force a premature
  archive/resolve.
- **na-eligibility-audit 2026-08-09**: KEEP-NA, valid — deferred to `ci_satellite_ao_dispatch_batch6_finalize` todo 1's
  fuller same-day resolution above (line-cap headroom exhausted, no new marker this pass).
