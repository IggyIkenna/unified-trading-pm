---
title:
  "orchestrator_autonomy_audit_remediation residual open findings — F1 (running VM behind LDR HEAD), F2 (vm-ml
  stopped/SSM-degraded), FM3 (foreign-repo playwright-report not gitignored) — surfaced when the parent plan was
  archived 2026-06-01 with these still open"
created: 2026-06-02
author: ikenna (slot-1)
source:
  - plans/archive/2026_06/orchestrator_autonomy_audit_remediation_2026_06_01.md (archived with Findings F1/F2 open + FM3
    deferred to "those repos' owners" with NO named successor plan — violates the archival deferred-work HARD RULE)
  - bash scripts/orchestrator/verify_fleet_autonomy_health.sh @ 2026-06-02T05:19Z (vm-orchestrator behind=3 flags=4/4
    ver=0.6.0; api-host behind=0; 9 epic VMs ssm-send-command-failed)
  - aws ec2 describe-instances 2026-06-02T05:20Z (2 RUNNING:
      vm-orchestrator i-007e8d99d12831578 + agent-orchestrator-vm-1
    i-0c9b283b31d6b5ca7; 9 STOPPED: cefi/defi/ml/operator-ops/prediction/sports/tradfi/trading-core/cross-cutting)
  - deployment-ui/.gitignore (no playwright-report line) + git ls-files (1 tracked playwright-report artifact) @
    2026-06-02
parent_epic: plans/epics/orchestrator_master.md
locked_by: orchestrator_autonomy_residual_findings_2026_06_02
---

## What I found

The `orchestrator_autonomy_audit_remediation_2026_06_01` plan was archived 2026-06-01 stating "all phases complete." All
four phases of **code** did ship + QG-green + deploy. But three items in the plan's own Findings / deferred-work banner
were **not actually closed**, and the archive carried them silently (the FM3 deferral names no successor plan, which is
the archival deferred-work HARD RULE):

### F1 — running VM behind LDR HEAD; FF-cron not keeping it current

2026-06-01 run found 3 VMs behind LDR HEAD (vm-orchestrator −6, vm-operator-ops −5, vm-prediction −6). As of
2026-06-02T05:19Z the fleet has consolidated to **2 running VMs**, and the picture is:

- **vm-orchestrator** (i-007e8d99d12831578, RUNNING) — `behind=3` vs `origin/live-defi-rollout`, flags=4/4, ver=0.6.0.
  The FF-pull cron is supposed to keep its agent-orchestrator worktree current and is not (3 commits stale: `478b3ff`
  slack-auth-alert, `11c2212` docs, `1fe3386` api-host swap-headroom). Root cause to confirm: dirty/diverged worktree
  blocking FF, or wedged `slot-cron-ff-pull.sh`, or the agent-orchestrator base-branch resolution.
- **api-host / agent-orchestrator-vm-1** (i-0c9b283b31d6b5ca7, RUNNING) — `behind=0`, flags=4/4, `/health` ver=NA
  (central health on :8765 not :8026 — known, not an outage).

### F2 — vm-ml SSM-degraded → now STOPPED

2026-06-01 finding: vm-ml SSM execution returned Status=Failed for every command (suspected disk-full from the
historical 142k-line backlog bloat or a wedged SSM agent), so its autonomy flags + currency were unverified. As of
2026-06-02 **vm-ml (i-02294132088f23e50) is STOPPED** along with the other 8 epic VMs — the fleet was intentionally
consolidated to 2. The SSM-broken state is therefore latent, not live; but it MUST be cleared (disk + SSM agent)
**before vm-ml is next started**, or the same wedge recurs on boot.

### FM3 — foreign-repo playwright-report still tracked + not gitignored, no successor plan

The archived plan deferred the belt-and-suspenders (`git rm --cached` + `.gitignore playwright-report/` in
**deployment-ui** + **user-management-ui**) to "those repos' owners" with **no named successor plan** — a deferred-work
HARD RULE gap. Confirmed still open 2026-06-02: `deployment-ui/.gitignore` has no `playwright-report` line and
`git ls-files` still shows 1 tracked `playwright-report` artifact. (The agent-orchestrator-side FM3,
`restore_generated_artifacts`, did ship @1f9af64 — only the foreign-repo half is open.)

## Why it matters

- **F1**: a running orchestrator VM silently 3 commits behind LDR is the exact "stale server code" state the worktree
  model + FF-cron exist to prevent. If the FF cron is wedged it will keep drifting; this is also the canonical signal
  the deploy-currency gate watches.
- **F2**: a stopped VM that wedged SSM on its last run will wedge again on next boot — and SSM-broken means it can't be
  remediated remotely (SSM itself can't execute). Needs disk-clear + SSM-agent restart on/just-after boot.
- **FM3**: a tracked regenerated artifact is precisely what triggers FM3 working-tree pathologies (orphan-wip commits of
  build output) on those UI repos' slots. Leaving it tracked + un-gitignored re-arms the failure on every respawn.

## Recommended decision

1. **F1** — SSM into vm-orchestrator, inspect the agent-orchestrator worktree, FF (or force-reset to
   `origin/live-defi-rollout` if dirty/diverged — operator-authorized 2026-06-02), restart orchestrator, confirm
   `slot-cron-ff-pull.sh` is installed + last-run <10min. Re-run `verify_fleet_autonomy_health.sh` to confirm behind=0.
2. **F2** — gate vm-ml's next start on a disk-headroom + SSM-agent-health check; document the
   clear-disk-then-restart-SSM recipe in the start path. Until vm-ml is needed, leave stopped (no live risk).
3. **FM3** — file/hand to the deployment-ui + user-management-ui owners: `git rm --cached` the tracked playwright-report
   artifact + add `playwright-report/` to each repo's `.gitignore`. Out of agent-orchestrator scope but now NAMED here
   so it is no longer a silent deferral.

This issue doc archives once all three are resolved (per issue-doc-lifecycle: surfaces UNACKED work; closes when acked
into shipped code / owning repo).
