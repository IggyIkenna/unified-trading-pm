---
doc_type: plan
title: Split self-hosted CI-runner fleet off the AO box onto a dedicated VM, right-size AO, retire the human-planning VM
summary: >-
  The AO orchestrator box (i-0c9b283b31d6b5ca7) colocates its own dispatch role with ~24 repos' self-hosted GitHub
  Actions runners — the confirmed root cause of the open fleet-wide capacity-crisis incident. This plan migrates the
  runner fleet to a dedicated escalation VM, right-sizes AO down afterward, and separately retires the
  operator-interactive human-planning VM (i-0dd9812a96cdda5dc) once idle. Operator-approved 2026-08-03; human plan (not
  AO-dispatched) because each phase gate is a live judgment call, not a determinable worker todo.
status: active
nature: process
asset_group: [ci, infrastructure]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity, vm-migration, cost, infra, ec2]
related:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md,
    scripts/self-hosted-runners/ssm-run.sh,
    scripts/self-hosted-runners/hosted-baseline.sh,
    scripts/self-hosted-runners/setup-glue-runners.sh,
  ]
source: ["operator request, interactive session, 2026-08-03 — infra cost comparison + capacity-crisis follow-through"]
locked_by:
locked_since:
---

# Split self-hosted CI-runner fleet off the AO box, right-size AO, retire human-planning VM

## Why (evidence, gathered live this session — not estimates)

- **`i-0c9b283b31d6b5ca7`** (`agent-orchestrator-vm-1`, EIP `13.113.200.22`, ap-northeast-1) is currently
  **`m8i.4xlarge`** (16 vCPU / 64GB) — resized up from its original `m8i.2xlarge` (8 vCPU/32GB, per the 2026-07-15
  migration doc) at some point after the runner rollout, presumably to absorb contention. It still isn't enough: the
  [capacity-crisis issue](/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md) has ~15
  dated corroborations through 2026-08-02 of load average 25-50 on 16 vCPUs, RAM-pressure SIGTERMs, and multi-hour
  promotion-gate stalls, all traced to the colocated self-hosted-runner pools (`glue`/`glue-writer`) for ~24 repos
  sharing this one box with AO's own dispatch role.
- **`i-0dd9812a96cdda5dc`** (`agent-orch-human-planning-vm`) is a SEPARATE box — `m7i.xlarge` (4 vCPU/16GB, 150GB gp3),
  interactive-only for Ikenna + Harsh, no runners, no orchestrator role. Live AWS pricing (`aws pricing get-products`,
  ap-northeast-1): $0.2604/hr.
- **Cost comparison** (on-demand, live AWS Pricing API, not estimates): today's 2-box total ≈
  $1,051/mo (compute +
  storage, 24/7). The chosen split — new `c8i.4xlarge` (16 vCPU/32GB, $0.9438/hr) escalation VM +
  AO down to `m8i.2xlarge` (8 vCPU/32GB, $0.5468/hr) + human-planning terminated — comes to ≈ $1,203/mo, **~15% MORE**
  than today on raw list price (mainly because storage also grows, 500+150GB → 600+600GB). The justification is NOT
  lower AWS spend (today's box is credit-covered per `agent-orchestrator-deploy.md`) — it's resolving the open P0
  contention incident and getting real per-box blockage visibility. Re-confirm the credit-coverage assumption still
  holds before treating cost as a non-issue (§ Todo below).
- **No 12-vCPU size exists** for `m8i`/`c8i` (confirmed via `aws pricing get-products` — zero matches for
  `m8i.3xlarge`/`c8i.3xlarge`). AO's real choice is 8 vCPU (`m8i.2xlarge`) or stay at 16; 8 is chosen here as the
  operator's decision, understanding it's the "safe margin" choice, not the cheaper-than-today one (4 vCPU, i.e.
  `m8i.xlarge`, would be cheaper than today but is unmeasured — AO's actual post-split CPU need has never been isolated
  from the runner load it's been carrying).

## Hard sequencing rule — do not violate

**Runners migrate off `i-0c9b283b31d6b5ca7` BEFORE it is downsized.** Downsizing AO first (16→8 vCPU) while it still
carries the full ~24-repo runner load would make the documented contention WORSE, not better. The order is: (1) stand up
the new escalation VM with runners registered and verified per-repo, (2) decommission the old runners once every repo's
new pool is confirmed green, (3) only then resize AO down.

## Mechanics carried over from the original migration (read before touching either VM)

- No inbound SSH to `i-0c9b283b31d6b5ca7` — **AWS SSM only** (`scripts/self-hosted-runners/ssm-run.sh`). Same will apply
  to the new escalation VM once launched (match its security-group/access model to the existing AO box, not open SSH,
  unless the operator wants interactive access to it too).
- Runner registration token = GCP Secret Manager `GH_PAT` (`GH_TOKEN_SECRET=GH_PAT`) — never a raw PAT on disk. Deploy
  clone is a DEDICATED git clone (`/opt/glue-deploy/unified-trading-pm`), never scp/heredoc'd files — both hard lessons
  from the original migration (`/plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md`
  §"DEPLOY RULE" and §"HOW TO TOUCH THE BOX AT ALL").
- Verify in the runner's REAL environment (`systemd-run --uid=ubuntu`, scrubbed `env -i`), not a login shell — the
  single costliest lesson from the original deploy (preflight that passes in the wrong shell reports a false green).
- The live allowlist of which repos actually have runners today, and their current per-repo registration state
  (`gh api repos/IggyIkenna/<repo>/actions/runners`), must be re-enumerated at execution time — the fleet has grown
  significantly past the original 8-runner/2-pool baseline (the capacity-crisis doc's 2026-08-02 entry counts "129 live
  github-glue-runners processes across 25 colocated pools"), so do not trust either doc's original runner count.
- Revert path exists if a migrated repo's runner breaks its CI:
  `scripts/self-hosted-runners/hosted-baseline.sh restore <wf>|--all` puts a workflow back on GitHub-hosted runners.

## Todos

- [x] ✅ [INFRA] P0. **Re-confirm AWS-credit coverage — DOES NOT HOLD, materially different from the plan's premise.**
      `aws ce get-cost-and-usage` (2026-08-03, live query): June 2026 total UnblendedCost ≈ $0 net (~$3,434 gross fully
      offset by ~$3,434 credit — fully covered). **July 2026: total (post-credit) cost = $1,020.06**, despite
      $1,846.49
      of credit still being applied that month — i.e. July already had ~$1,020 of REAL out-of-pocket
      spend. **August 2026 (Aug 1-4, 3 days in): total cost $268.46, credit applied only -$0.01** — essentially ALL of
      August's spend so far is genuine, uncredited money, at a ~$89/day run-rate (whole-account, not just this VM).
      Credits have clearly wound down/expired between June and August. This directly invalidates the plan's "today's box
      is credit-covered... this is all list-price math, not real spend" framing — the ~15% cost delta from adding the
      escalation VM is now REAL money, not moot. **PAUSED HERE per the operator's own instruction** (surface anything
      materially different from the plan's assumptions before todo 3's VM launch) — see Progress Log.
- [x] ✅ [INFRA] P0. **Enumerate the CURRENT full runner fleet** — live `gh api repos/IggyIkenna/<repo>/actions/runners`
      query, 2026-08-03, across all 21 repos in `scripts/workflow-templates/self-hosted-qg-repos.txt`: **30 total
      runners** — `agent-orchestrator`=3, `unified-trading-pm`=8, all other 19 repos=1 each (19). Supersedes both prior
      docs' stale/approximate counts (the capacity-crisis doc's "129 live processes" figure counted OS processes
      including JIT churn, not registered runners — the real registered-runner count is 30, smaller and more precise).
- [x] ✅ [INFRA] P0. **Launch the escalation VM — DONE.** `i-042a6332509482556` (`ci-escalation-runner-vm-1`),
      `c8i.4xlarge`, ap-northeast-1, subnet `subnet-fc09eca6` — same AMI (`ami-0bf052f8a9dd8bf42`) and IAM instance
      profile (`uts-orchestrator-epic`) as the AO box for toolchain/permission parity (SSM Session Manager + AWS access
      all confirmed working via the shared profile's `uts-orchestrator-epic-policy`). Security: a NEW, tighter group
      `sg-0984fc3eedabc5a84` with **zero inbound rules** (SSM-only) — the live AO box's actual SG
      (`sg-066c852065f8cdcac`) was found to have drifted from its own documentation (port 22 + 8765 open to 0.0.0.0/0,
      contradicting "no inbound SSH" in the archived migration doc) — deliberately did NOT replicate that drift onto the
      new box. 300GB gp3 (vs AO's 500GB) — sized for a pure runner host with no AO slot worktrees. Gate met:
      `aws ec2 describe-instances` shows `running`; `aws ssm describe-instance-information` shows `PingStatus=Online`
      (registered within the same SSM call window as launch — AMI ships the agent pre-baked).
- [x] ✅ [INFRA] P0. **Deploy the runner toolchain — DONE, preflight green.** Discovered live: the AMI is a bare-OS
      snapshot with NO CLI toolchain baked in (contradicting the assumption that "same AMI as AO" means same software) —
      `aws`/`gcloud`/`gh`/`uv`/etc. were all absent on first boot. Ran
      `scripts/self-hosted-runners/bootstrap-ci-host.sh` (the sanctioned failsafe for exactly this — its own header
      literally says "provisions from scratch," and its own STATUS notes this was never before proven on a real bare VM,
      only a container) — hit and fixed one real bug along the way: an earlier credential-bootstrap step's `mkdir -p`
      had left `/home/ubuntu/.config` root-owned, which broke the `uv` installer's `~/.config/fish` write (permission
      denied) — fixed by chowning it back to ubuntu, then the bootstrap completed clean
      (git/jq/python3/gh/gcloud/aws/curl/node/npm/uv/Python 3.13.14/claude-code all verified present and working for the
      `ubuntu` user in a real login shell). **GCP credential bootstrap** (the codex doc's documented
      `unified-trading-sa` mechanism didn't match the LIVE AO box's actual identity, `github-actions-deploy` — codex
      drift, not touched here): minted a fresh `unified-trading-sa` service-account key via the IAM REST API (`gcloud`
      CLI itself needed an interactive reauth this session couldn't do; the Python `google.auth` ADC session already
      active could call the REST API directly), staged it through an encrypted SSM Parameter Store SecureString (never
      printed, never left in SSM command-text logs), placed at `/home/ubuntu/.config/gcp/unified-trading-sa-key.json`
      (0600, ubuntu-owned) on the new VM, activated via `gcloud auth activate-service-account`, and verified — **in a
      scrubbed `env -i` non-login shell, matching exactly how the real runner wrapper invokes it** — that
      `gcloud secrets versions access latest --secret=GH_PAT` succeeds. Granted `uts-orchestrator-epic-role` (shared by
      both VMs) a narrow `ssm:GetParameter`/`DeleteParameter` scoped to `/ci-escalation-runner/*` for this; parameter +
      local scratch key deleted after use. **Clone**: `/opt/glue-deploy/unified-trading-pm` on `live-defi-rollout`,
      cloned fresh as `ubuntu` via `gh` (needed `gh auth login --with-token` first — the repo is private, plain HTTPS
      clone has no credential). **Gate met**: `setup-glue-runners.sh preflight` → `preflight OK` exit 0, resolved via
      the runner's REAL PATH (`/opt/github-glue-runners/venv/bin:/home/ubuntu/.local/bin:...`), not a login shell.
      **Caveat found along the way (self-correcting, not left broken)**: `scripts/self-hosted-runners/ssm-run.sh`
      silently ignores any positional argument — it always targets `SSM_INSTANCE` (default: the OLD AO box) — a command
      intended for the new VM ran on the old box instead; caught it (via the error message's own instance ID), cleaned
      up the harmless empty artifact it left there, and used `SSM_INSTANCE=<id>` explicitly from then on. Consider
      fixing the script to accept `$1` for real, so this can't bite the next person.
- [x] ✅ [INFRA] P0. **Canary migration (`system-integration-tests`) — DONE, verified green on the new runner, AND a
      real self-caused incident found + fixed along the way.** Chose it: has `workflow_dispatch`, not one of the
      operator's 6 explicitly-protected repos, test-only (not execution-critical). - `setup-glue-runners.sh install`
      with `POOL_TAG=system-integration-tests` (own isolated slot/env-file/systemd units, disjoint from every other
      pool) → runner `glue-ip-172-31-3-59-1` registered online alongside the old box's `glue-ip-172-31-5-118-1` (both
      online, same labels — GitHub splits jobs non-deterministically between them until the old one is removed). - First
      real `workflow_dispatch` run: `checks` slice landed on the NEW runner and FAILED — root cause
      `❌ ripgrep       required` (base-service.sh's own `[0/6] ENVIRONMENT` hard-check; `bootstrap-ci-host.sh` never
      installed it — a genuine gap, not contention/flakiness). Fixed: `apt-get install ripgrep` on the live VM, AND
      folded back into `bootstrap-ci-host.sh install_base()` + `verify()`'s tool list (its own documented discipline:
      "fold every discovery back in immediately"). Re-dispatched: **all green**, `tests` slice claimed by the new runner
      (`glue-ip-172-31-3-59-1`), full run `success`. - **Real incident, self-caused and self-fixed**: deregistering the
      OLD box's runner via `setup-glue-runners.sh teardown` with
      `POOL_TAG=system-integration-tests OWNER=IggyIkenna       REPO=system-integration-tests` silently operated on
      **PM's own default (no-POOL_TAG) pool instead** — removed PM's `github-glue-runner@.service` template unit, slice,
      and slot-refresh timer files, taking **all 8 of PM's own runners offline** (confirmed via a live GitHub API check,
      caught within minutes via a routine post-teardown verification, not by a wider alert). **Root cause traced but not
      fully resolved**: a `bash -x` trace of the SAME invocation pattern against the (non-destructive) `status`
      subcommand showed `OWNER`/`REPO` correctly picked up my CLI-supplied values but `POOL_TAG` silently resolved empty
      — `sudoers` has no active `env_keep`/`env_check` entries that would explain a selective drop, and a separate
      dry-run (`sudo POOL_TAG=... bash -c 'echo $POOL_TAG'`) showed the var DOES propagate through `sudo` correctly in
      isolation — so something specific to `setup-glue-runners.sh`'s own execution silently drops `POOL_TAG`
      specifically, not `sudo` in general. **Not chased further given the live-incident context** (deprioritized safe
      restoration over root-causing precisely) — flagged as a real, reproducible bug needing investigation before anyone
      reuses `teardown`/`install` with `POOL_TAG` via this exact CLI-env-var invocation pattern. - **Fix + safe path
      taken instead**: re-ran `setup-glue-runners.sh install` for PM's own default pool (no POOL_TAG) — idempotently
      regenerated the missing unit/slice/timer files — confirmed via live API all 8 PM runners back `online`. For the
      canary's actual old-runner teardown, used a NAME-EXACT, non-script path instead (avoids the same bug entirely):
      `systemctl stop/disable` the exact confirmed unit name
      (`github-glue-runner-system-integration-tests@glue-1.service`) + `gh api -X DELETE` the specific runner ID — both
      zero ambiguity, no environment-variable resolution involved. Verified: canary repo now shows exactly ONE runner
      (the new VM's, online); a fleet-wide sweep across all 21 allowlisted repos confirmed zero collateral damage beyond
      the PM incident (which was fully restored). - **Gate met**: real CI run `success`, claimed by the new VM's runner
      (`glue-ip-172-31-3-59-1`); old runner cleanly deregistered; PM's pool restored + verified; fleet-wide sweep clean.
- [x] ✅ [INFRA] P1. **Side-finding, fixed: the original 21-repo fleet count (todo 2) was undercounted — 25 repos,
      not 21.** While auditing the old VM's live systemd units (`systemctl list-units 'github-glue-runner*'`) before
      migrating PM's/AO's pools, found 4 running, GitHub-registered, online pools never accounted for anywhere in the
      batch plan: `deployment-ui`, `e2e-testing`, `unified-trading-library`, `unified-trading-system-ui` — confirmed
      real via `gh api repos/IggyIkenna/<repo>/actions/runners` (all `status=online`) before touching anything. Folded
      in as **Batch 4** and migrated the same way (register on new VM, `WRITER_COUNT=0` to match the old VM's glue-only
      config for these 4 — the first attempt (`deployment-ui`) defaulted to 3 unwanted writer runners when
      `WRITER_COUNT` was left unset, caught via a registration-count diff against the old VM and fixed by stopping +
      `gh api DELETE`-ing the 3 extras before repeating the remaining 3 installs with `WRITER_COUNT=0` explicit). **Root
      cause of the miscount not investigated** — todo 2's original enumeration method should be revisited so this
      doesn't recur; not done here (out of scope for a migration task). Batch 4 installed + `quality-gates-v2`
      dispatched on all 4 2026-08-04; verification pending.
- [ ] [INFRA] P1. **Batch migration IN PROGRESS — 13 of 25 pools done (25, not 21 — see the miscount finding above).**
      Batch 1 (5 repos, 2026-08-03): `strategy-service`, `trading-agent-service`, `unified-api-contracts`,
      `unified-trading-api`, `execution-service`. Batch 2 (7 repos, 2026-08-04): `features-service`,
      `fund-administration-service`, `greeks-service`, `ibkr-gateway-infra`, `instruments-service`,
      `market-tick-data-service`, `batch-live-reconciliation-service` — 4 verified via a clean manual `quality-gates-v2`
      dispatch, 3 (`features-service`, `instruments-service`, `market-tick-data-service`) hit the same "supersede check"
      cancellation pattern as batch 1 on re-dispatch too, so verified instead via REAL organic production traffic
      already on the new runner (a Semver Agent run + an `update-dep` job, both `success`) — a stronger signal than a
      manual dispatch anyway. Every batch: register on the new VM (`POOL_TAG=<repo>`), verify green (manual dispatch OR
      real organic traffic), THEN deregister the old runner via the safe exact-unit-name + `gh api DELETE` method (never
      `teardown` — see the canary todo's incident note). PM's pool re-checked healthy after each batch (0 offline, both
      times). Batch 3 (6 repos: `alerting-service`, `client-reporting-api`, `ml-service`, `deployment-api`,
      `market-data-processing-service`, `deployment-service`) installed + dispatched, **stuck `queued` on real fleet
      contention for several minutes at check time** — direct evidence of the exact problem this split exists to fix;
      waiting on completion, not re-dispatching into the same backlog. Remaining after batch 3: PM's 8-runner pool +
      AO's 3-runner pool — the two highest-stakes pools, done last and carefully given the batch-1 incident. **Operator
      explicit hold (2026-08-04): do PM + AO pool migration, then STOP before the actual AO box downsize (todo below)
      and wait for explicit confirmation — accepting the temporary extra spend of running both boxes at current size
      meanwhile.** Mirror the original migration's canary→10→remaining phasing — each batch: register on new VM, verify
      green, THEN deregister the old runner for those repos. Do not batch-migrate without verifying the prior batch
      first. Gate: per-batch, a passing CI run per migrated repo cited by run URL. **Batch 4** (the 4 miscounted repos
      above) installed + `quality-gates-v2` dispatched 2026-08-04; verification pending. **PM's 8-runner pool (5 glue +
      3 writer) and AO's 3-runner pool (2 glue + 1 writer) both installed on the new VM 2026-08-04** — every slot
      confirmed online at the correct count via `gh api .../actions/runners` (PM: 5 `glue-ip-172-31-3-59-*` + 3
      `writer-ip-172-31-3-59-*`; AO: 2 `glue-*` + 1 `writer-*`, same IP), matching the old VM's counts exactly. AO's
      `quality-gates-v2` dispatched (run 30897598568, queued). PM's workflow has no `workflow_dispatch` trigger (422 on
      manual dispatch attempt) — verification will come from this session's own next quickmerge ship to
      `unified-trading-pm` (organic push-triggered CI), not a manual dispatch. **Old-VM deregistration for PM/AO NOT YET
      DONE** — waiting on the above verification first, given the batch-1 incident precedent (never partially deregister
      a multi-runner pool).
- [x] ✅ [INFRA] P1. **Side-finding, fixed: PM's/AO's pool installs on the new VM stalled ~9 minutes on a real per-pool
      memory-cap throttle, not a code bug.** `scripts/self-hosted-runners/github-glue-runner.slice` caps EVERY pool
      independently at `MemoryMax=8G`/`MemoryHigh=6G` (each `POOL_TAG` renders its own separately-named slice — this is
      a per-pool fence, not a single fleet-wide 8G ceiling as the unit file's own comment implies). The old VM's
      identical PM slice sits at the same ~6G `MemoryHigh` line in steady state too (confirmed via a live check:
      `MemoryCurrent=6.44G` there) — so 8G/6G was ALREADY tight, just not stall-inducing under the old VM's warmed-up,
      staggered-restart operating pattern. On the new VM, all 8 PM processes (+3 AO) cold-started simultaneously, pushed
      the slice's cgroup into sustained `MemoryHigh` throttling (confirmed via `memory.pressure`: `some avg10=100.00`,
      `full avg10=98.44` on the parent `github-glue.slice`) — every memory-allocating syscall in the pool got delayed,
      producing 9+ minutes with literally zero script-level log output past the systemd `Started` line (confirmed via
      `journalctl`) despite the HOST having 22GB+ genuinely free (`free -h`: 30Gi total, only ~8.3Gi used). **Fix**:
      raised `MemoryMax`/`MemoryHigh` to `20G`/`18G` for `github-glue-runner.slice` (PM) and
      `github-glue-runner-ao.slice` (AO) — via `systemctl set-property` (live, immediate) plus a persistent
      `*.slice.d/override-dedicated-vm.conf` drop-in (survives future reinstalls/reboots without editing the shared
      template) — **on the new VM only**. The old VM's copy and the repo's canonical `.slice` template are UNTOUCHED:
      the rationale in that file ("a CI burst must never starve the agent-orchestrator sharing this VM") is specific to
      the shared old-VM topology and genuinely doesn't apply on the new, CI-dedicated escalation VM. Registration
      completed within ~90s of the cap raise (confirmed: `MemoryCurrent` climbed past the old 8G ceiling to 8.15G then
      13.3G, both `.runner` markers appeared). **Not done**: the OTHER 23 pools on the new VM (single glue-only, no
      writers) never showed this symptom and were left on the stock 8G/6G template — only PM's and AO's wide
      (multi-process) pools needed the override. **Follow-up not filed as a todo** (low priority, informational): the
      unit file's own comment ("resource cap for the WHOLE glue-runner fleet... guarantees the orchestrator always
      keeps >= 4 of the 8 vCPUs") is misleading given the actual per-pool-not-fleet-wide behavior confirmed here — worth
      a comment fix next time that file is touched, not urgent enough for its own todo.
- [x] ✅ [INFRA] P2. **Side-finding, fixed: the new VM was invisible in `deployment-ui`'s `/deployments` + `/cockpit` —
      not a dashboard limitation, a real registration gap.** Operator asked whether the new VM shows up anywhere for
      load/dispatch/log visibility; the AO dashboard genuinely never tracks arbitrary EC2 instances (only its own
      in-process worker slots — confirmed via code read, no fix possible there), but `deployment-api`'s AWS EC2 census
      (`deployment-service/backends/aws_census.py::list_ec2_census`) DOES discover every running instance
      unconditionally — the gap was downstream: `_ec2_item()` silently DROPS any instance whose `Name` tag matches no
      registered prefix (`deployment_api/routes/deployments_inventory/__init__.py::_VM_PREFIX_REGISTRY`), unlike the GCP
      path which degrades to a visible `NONE`-umbrella row instead of hiding it (a real, confirmed asymmetry between the
      two cloud paths — not fixed here, out of scope). Fixed by registering `"ci-escalation-runner"` →
      `LifecycleClass.LONG_LIVED_LIVE` (same class as `agent-orchestrator`/`planning`) + adding it to
      `_CONTROL_PLANE_PREFIXES`, with a new passing test
      (`test_build_aws_inventory_classifies_ci_escalation_runner_as_live`) proving the instance is no longer silently
      skipped. **Blocked from shipping**: quickmerge's re-gate hit 2 PRE-EXISTING, unrelated `deployment-api` test
      failures (confirmed via `git stash` — fail identically on the clean tree), which block ANY commit to
      `deployment-api` right now — filed as
      `/plans/active/issues/deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md` (shipped). The
      fix + test sit locally uncommitted in this session's checkout until that issue clears.
- [ ] [INFRA] P1. Once every repo's runner is confirmed migrated and no runner-claimed job has landed on
      `i-0c9b283b31d6b5ca7` for a full day, tear down the old runner pool there (`setup-glue-runners.sh teardown` or
      equivalent). Gate: `gh api .../actions/runners` shows zero runners registered against the old VM fleet-wide.
- [ ] [INFRA] P1. **Downsize `i-0c9b283b31d6b5ca7` from `m8i.4xlarge` to `m8i.2xlarge`** (stop →
      modify-instance-attribute --instance-type → start). Per CLAUDE.md's maintenance-window rule, brief orchestrator
      downtime during this is pre-authorized (pre-live-trading) — do now, no separate scheduling needed. Verify AO's own
      dispatch/backlog functionality afterward (`/check-agent-orchestrator` or equivalent). Gate: instance shows
      `m8i.2xlarge` `running`, AO backlog responds normally post-restart.
- [ ] [INFRA] P2. Re-run the fleet-wide contention check the capacity-crisis issue doc uses (glue-pool-starvation
      monitor / spot-check a few repos' recent `quality-gates-v2` queue times) to confirm the split actually resolved
      the contention, and update `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`
      with the outcome (close or re-open with new evidence). Gate: a dated Progress Log entry in that issue doc citing
      post-split queue-time measurements.
- [ ] [INFRA] P2. Update `/codex/05-infrastructure/agent-orchestrator-deploy.md` to reflect the new topology (AO at
      `m8i.2xlarge`, escalation VM details, no more colocated runners) — codex must not describe a topology that no
      longer exists. Gate: doc diff shipped, `unified-trading-pm@<sha>`.

### Human-planning VM retirement (separate box, tracked here since bundled by the operator)

- [x] ✅ [INFRA] P0. **Deferred idle-check + terminate armed** — session cron `67ed27cd` scheduled for 2026-08-03 19:37
      BST (4h after operator approval): re-checks `who`/`w`/`tmux`/load on `human-planning-vm` and terminates
      `i-0dd9812a96cdda5dc` only if genuinely idle; reports back either way. At the initial 15:35 BST check, load was
      idle-quiet (0.81/0.89/0.61) but 2 SSH entries with identical idle times looked like possibly-stale utmp rather
      than confirmed-idle, which is why the deferred re-check (not an immediate terminate) was used. **Caveat**: this
      timer is session-bound (Claude Code session-only cron, not written to disk) — if the session ends before 19:37
      BST, re-arm it or terminate manually:
      `aws ec2 terminate-instances --region ap-northeast-1 --instance-ids     i-0dd9812a96cdda5dc` after confirming idle
      via `ssh human-planning-vm "who; w; tmux ls; uptime"`.
- [ ] [INFRA] P1. Once terminated, confirm no dangling reference to `i-0dd9812a96cdda5dc` remains load-bearing in codex
      (`grep -rn "i-0dd9812a96cdda5dc" codex/ plans/active/` — update any doc that assumes it's live, e.g.
      `agent-orchestrator-single-vm-architecture.md`'s "unaffected — it never executes backlog tasks" framing, and
      `orchestrator-cloud-identity-self-service.md`'s per-VM ADC setup note). Gate: grep shows only historical/archived
      references, no active-doc assumes the VM still exists.

## Progress Log

- **2026-08-03 (autonomous execution start)**: Operator said "let's do the plan in full" — began execution per
  `/autonomous`, in file order, per this plan's own Hard Sequencing Rule. Todos 1-2 (both read-only, no infra touched)
  completed with a materially significant finding: **AWS credits do NOT reliably cover current spend.** Live
  `aws ce get-cost-and-usage` query: June net cost ≈$0 (fully credited), July net cost = **$1,020.06** (real,
  out-of-pocket, despite $1,846 credit still applied that month), August (3 days in) = **$268.46 real cost, only
  $0.01 credited** — i.e. essentially 100% of August's spend so far is genuine money, ~$89/day whole-account run-rate.
  This directly contradicts the plan's own "today's box is credit-covered, this is all list-price math" framing (§ Why,
  bullet 3) — the ~15% cost delta from adding the escalation VM is REAL spend now, not moot. Runner-fleet enumeration
  (todo 2) came back smaller/more precise than either prior doc's estimate: 30 real registered runners across 21 repos
  (not "129 processes across 25 pools" — that figure counted OS processes/JIT churn, not registrations). **Paused here,
  before todo 3 (VM launch — real billing begins), per the operator's own explicit instruction to surface anything
  materially different from the plan's assumptions at exactly this checkpoint.** Not proceeding to provisioning until
  the operator confirms whether to continue given credits are exhausted.

## Full-execution criterion (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE)

- Every runner-migration todo above is real-infra (VM provisioning, live GitHub Actions runner re-registration across
  ~24 repos) — no todo here is done on a smoke-test/local basis. Each batch's "Gate:" is a live CI run URL + status, not
  a local dry-run.
- **Handoff exception**: none anticipated — this plan is scoped to be executed start-to-finish across one or more
  interactive sessions by the operator + this agent, given the live-judgment-call nature of each phase gate (per the
  operator's own choice of "human plan" over AO-dispatch).

## Progress Log

**2026-08-03 ~15:3X BST** — Plan authored following an interactive cost-comparison discussion (live AWS Pricing API +
`describe-instances` queries, not estimates) that surfaced the runner-migration scope was much larger than a simple
launch+resize. Operator approved: terminate human-planning VM (deferred idle-check, 4h timer), draft this as a human
plan (not AO-dispatched) before executing the AO/escalation-VM split. Human-planning termination timer armed (session
cron `67ed27cd`, fires 19:37 BST). No other todos started yet — next action is the fleet enumeration todo (P0) before
any VM is launched.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped `classify-glue-workflows.sh` (never
  mentioned in this doc's own body) for `ssm-run.sh` and `hosted-baseline.sh`, which the doc's own "Mechanics carried
  over" section explicitly flags as "read before touching either VM."
