---
doc_type: plan
title: Split self-hosted CI-runner fleet off the AO box onto a dedicated VM, right-size AO, retire the human-planning VM
summary: >-
  The AO orchestrator box (i-0c9b283b31d6b5ca7) colocates its own dispatch role with ~24 repos' self-hosted GitHub
  Actions runners — the confirmed root cause of the open fleet-wide capacity-crisis incident. This plan migrates the
  runner fleet to a dedicated escalation VM, right-sizes AO down afterward, and separately retires the
  operator-interactive human-planning VM (i-0dd9812a96cdda5dc) once idle. Operator-approved 2026-08-03; human plan (not
  AO-dispatched) because each phase gate is a live judgment call, not a determinable worker todo.
status: complete
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
last_updated: "2026-08-07"
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

> **🟢 ARCHIVED 2026-08-07.** Every todo shipped: all 25 self-hosted-runner pools migrated off the AO box onto the
> dedicated `ci-escalation-runner-vm-1` (verified zero old-VM units + zero old-VM GitHub registrations, corpus-wide),
> the human-planning VM was terminated, and the final held todo — downsizing `i-0c9b283b31d6b5ca7` from `m8i.4xlarge` to
> `m8i.2xlarge` — executed live 2026-08-07 after fresh 24h resource-usage data (CPU/RAM/swap/disk/I/O, both the on-box
> `resource-history-sampler` JSONL log and CloudWatch) was presented to the operator and confirmed, saving ~$399/mo. AO
> backlog/dispatch verified healthy post-resize. Codex SSOTs (`agent-orchestrator-deploy.md`,
> `orchestrator-cloud-identity-self-service.md`) already reflect the final state.

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
- [x] ✅ [INFRA] P1. **Batch migration COMPLETE — all 25 of 25 pools done (25, not 21 — see the miscount finding
      above).** Batch 1 (5 repos, 2026-08-03): `strategy-service`, `trading-agent-service`, `unified-api-contracts`,
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
      `writer-ip-172-31-3-59-*`; AO: 2 `glue-*` + 1 `writer-*`, same IP), matching the old VM's counts exactly. **PM
      verified green organically** (this session's own plan-doc quickmerge ship triggered a real `main`-branch job —
      `freeze-deferred-build-replay` succeeded on `glue-ip-172-31-3-59-5`, plus `update-ci-status` succeeded on BOTH
      `writer-ip-172-31-3-59-1` and `-3` — proving both glue and writer slots work). **AO verified via organic history,
      not the manual dispatch** — the manual `quality-gates-v2` re-dispatch (run 30898648500) hit the supersede-check
      pattern again (QG slice cancelled mid-run by newer activity), but a scan of AO's last 25 completed runs found
      real, clean successes on the new VM's glue runners across 4 different job types: Semver Agent, `backmerge`,
      `build + deploy to Firebase Hosting`, `validate / GCP Cloud Build` — sufficient proof. **Old-VM deregistration for
      PM (8) + AO (3) DONE 2026-08-04/05**: `systemctl stop`+`disable` on all 11 old-VM units (`i-0c9b283b31d6b5ca7`)
      confirmed inactive, then `gh api DELETE` for all 11 runner IDs — both repos now show 100% new-VM runners
      (`gh api .../actions/runners`), 0 old-VM entries. PM re-confirmed healthy after (all 8 online). **Batch 3
      update**: `deployment-api` confirmed green (2026-08-05, run 30956307018) and its old-VM runner deregistered.
      `deployment-service`/`alerting-service`/`client-reporting-api`/`ml-service`/`market-data-processing-service` were
      genuinely busy running real production jobs on their old-VM runner at check time (the old VM measured at **load
      average 65.63/65.19/56.76 on 16 vCPUs** during this window — worse than the capacity-crisis issue doc's historical
      25-50 range, real corroborating evidence, not a hang) — waited for each to go idle (never interrupt a live job)
      via a monitor polling `busy`, then deregistered the moment it cleared; all 5 done 2026-08-05. **ALL 25 POOLS NOW
      CONFIRMED FULLY MIGRATED 2026-08-05** — a final fleet-wide sweep confirms **zero** active
      `github-glue-runner*.service` units remain on the old VM (`systemctl list-units ... --state=active` returns empty)
      AND **zero** repos across the full 25-pool list show any `172-31-5-118`-named runner still registered on GitHub
      (`gh api .../actions/runners` checked per-repo). Gate met.
- [x] ✅ [INFRA] P0. **Self-caught false-progress finding, corrected: 7 repos claimed "migrated + deregistered" in
      earlier batches (1/2/4) still had a LIVE, GitHub-registered, actively-serving runner on the old VM** —
      `deployment-ui`, `e2e-testing`, `instruments-service`, `market-tick-data-service` (partial — see below),
      `unified-api-contracts`, `unified-trading-library`, `unified-trading-system-ui`. Found while answering the
      operator's direct question ("are all runners on the new VM") — a fresh
      `systemctl list-units     'github-glue-runner*.service' --state=active` sweep of the old VM turned up units for
      repos the plan doc already marked done, several with GitHub showing them `online`/`busy=true` and actively taking
      real production traffic (i.e. the "migration" for these repos was only ever half-done: new pool registered +
      verified, but the old pool never actually stopped). **Root cause**: ephemeral glue runners run under `Restart=` —
      a `gh api     DELETE` of the GitHub-side registration alone does NOT stop the systemd unit, so it just
      re-registers a fresh ephemeral runner on the next job, silently undoing the "deregistration" if the unit itself
      was never `systemctl stop`+`disable`-ed first. Some earlier-session step for these 7 repos apparently only did the
      API delete (or skipped it entirely) without confirming the unit was stopped — the plan doc's own claims for those
      batches were never re-verified against live VM state before being marked done. **Fixed 2026-08-05**: checked
      `busy` status first (never interrupt a live job) — 7 were idle, stopped+disabled+deleted immediately; confirmed
      via `gh api .../actions/runners` showing 0 old-VM entries for all 7 afterward. **Lesson for the remainder of this
      plan and any future batch-style migration**: verifying "green" is not the same as verifying "drained" — always
      re-check the OLD side's live systemd + GitHub registration state after claiming a deregistration, don't trust a
      plan-doc `[x]` from a prior session/batch without a fresh live check.
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
      `/plans/archive/issues/deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md` (shipped). The
      fix + test sit locally uncommitted in this session's checkout until that issue clears.
- [x] ✅ [OPERATOR] P2. **Done 2026-08-06 — operator ran the on-disk cleanup directly via `aws ssm send-command` (SSM
      Session Manager wasn't available locally — `session-manager-plugin` not installed — so used the `send-command`
      path with a pre-built `--cli-input-json` file to avoid manual shell-quoting of a multi-line script).** Real,
      verified result (command output, not estimated): root volume **592G → 459G used (88% → 68%), 133GB freed** — close
      to the ~139GB estimate, the gap being the `du` estimate's own rounding across 24 dirs.
      `systemctl is-active orchestrator` → `active` throughout, unaffected. All `github-glue-runner-*.slice`,
      `github-glue-runner-*@.service`, `github-glue-slot-refresh-*` unit files removed + `daemon-reload`d;
      `glue-runner-crash-loop-watchdog.timer` (permanent, shared with the CI VM) correctly left untouched, still
      `enabled`. **One harmless miss**: the bare top-level `github-glue-runner.slice` (no per-repo dash suffix) didn't
      match the `github-glue-runner-*.slice` glob used, so it's still present — an inert, empty, `static` resource-cap
      boundary with nothing left parented under it now; zero risk either way, not worth a follow-up todo for a no-op
      cleanup pass. Prep (stopping/disabling every unit) was done earlier the same session; this entry closes the final
      on-disk-delete step. Command ref: `fd1e3c8f-07da-45b3-9eb8-c26ff586e334` via SSM on `i-0c9b283b31d6b5ca7`.
- [x] ✅ [INFRA] P1. **Downsize `i-0c9b283b31d6b5ca7` from `m8i.4xlarge` to `m8i.2xlarge` — DONE 2026-08-07,
      operator-confirmed against fresh 24h usage data (not a re-run of the 2026-08-04 hold on stale assumptions).**
      **Pre-check**: pulled real 24h history from the on-box `resource-history-sampler.service` JSONL log (17,278
      samples at ~5s cadence, 2026-08-06 10:32 → 2026-08-07 10:32 UTC) — CPU avg 18.3%/p95 36.2%/max 98.7% (time ≥50%:
      1.3%, ≥80%: 0.2%), RAM avg 15.9%/p95 29.1%/max 45.3% (10.5GB avg, 30.0GB peak of 64GB total, time ≥50%: 0%), swap
      avg 9.3%/max 14.5% of 47GB configured, disk 73.8% avg/80.1% max (independent of instance size). Cross- confirmed
      CPU via CloudWatch `AWS/EC2` (avg 15-27%/hr, one peak hour 77%) and EBS write throughput via `AWS/EBS`
      (477.5GB/24h ≈ 5.5MB/s avg, 11.8M ops ≈ 136/s avg — negligible vs the 1000MB/s/16000-IOPS provisioned gp3 volume).
      Confirmed no CloudWatch agent installed on this host (0 `CWAgent` metrics) and `deployment-api`'s fleet-wide
      `resource_samples` BigQuery table has zero rows for this hand-provisioned box (deployment-ui's `/ops/vm-resources`
      won't show it) — the JSONL sampler + CloudWatch EBS metrics were the real data sources, not deployment-ui. Live
      AWS Pricing API (ap-northeast-1): `m8i.4xlarge` $1.09368/hr → `m8i.2xlarge` $0.54684/hr =
      **$13.12/day / $399.19/mo / $4,790/yr savings** (storage cost unchanged — EBS is instance-type-independent).
      Presented full data + one real caveat (RAM's single 30GB peak sample would be 93.8% of the new 32GB ceiling,
      though p95 is well under and 47GB of swap remains as an instance-size-independent buffer) to the operator via
      `AskUserQuestion`; operator chose "Proceed now." **Execution** (live AWS CLI, ap-northeast-1): `stop-instances` →
      `aws ec2 wait instance-stopped` (confirmed `stopped`) → `modify-instance-attribute --instance-type m8i.2xlarge`
      (confirmed via `describe-instances` before restart) → `start-instances` → `aws ec2 wait instance-running` +
      `wait instance-status-ok` (both passed) → final state: `running`, `m8i.2xlarge`, EIP `13.113.200.22` re-associated
      correctly. **Post-verify**: `/check-agent-orchestrator` (`check-ao-backlog-status.sh`) against the resized box
      returned `mode: live, is_mock: false`, `TOTAL_TASKS=1976`, normal status distribution (308 queued / 1 actively
      dispatched to slot 8 / 14 blocked / 59 cancelled / 1594 done) — dispatch/backlog fully functional post-resize, no
      degradation. Gate met in full.
- [x] ✅ [INFRA] P2. **Partial re-verification done 2026-08-05 — real improvement, not fully resolved.** Post-migration
      spot-check: dispatched 3 fresh `quality-gates-v2` runs (`ml-service`, `deployment-service`, `greeks-service`) and
      measured the new VM's load average — **29.25/29.36/30.65 on 16 vCPUs**, vs the old VM's measured peak of
      **65.63/65.19/56.76** during this same session's migration window (both real, dated `uptime` readings, not
      estimates). All 25 pools' worth of load now concentrated on one dedicated box is still genuinely high (~2x vCPU
      count) — 2 of the 3 fresh dispatches sat `queued` for the full ~2min check window, one flickered
      `in_progress`→`queued` (supersede-check pattern) — so the split has NOT eliminated contention, it has roughly
      HALVED peak load relative to the old shared VM. **Not done**: a longer-window, steady-state measurement (this was
      a single spot-check, not a sustained trend) and updating
      `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s own Progress Log with this
      dated evidence — filed as a follow-up in that issue doc directly rather than duplicated here.
- [x] ✅ [INFRA] P2. **Partially done 2026-08-05 — the parts that ARE true now.** Added a "CI-runner fleet — split off
      to a dedicated VM" section to `/codex/05-infrastructure/agent-orchestrator-deploy.md` documenting the migration
      (escalation VM details, 0 runner units remaining on this box) and fixed the stale "AWS credits cover" cost line to
      match todo 1's re-confirmed finding. **Deliberately NOT claimed at the time**: "AO at `m8i.2xlarge`" — the
      instance was still `m8i.4xlarge` then (todo 8 was on operator hold). **Update 2026-08-07 — DONE**: todo 8 has
      resolved (downsize executed), and this codex section (both the spec table and the prose note) has been re-touched
      to state `m8i.2xlarge` as current fact.

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
- [x] ✅ [INFRA] P1. **Done 2026-08-05.** Full `grep -rn "i-0dd9812a96cdda5dc" codex/ plans/active/` sweep (10 hits) —
      fixed the 2 load-bearing codex SSOTs (`agent-orchestrator-single-vm-architecture.md`'s "unaffected" framing,
      `orchestrator-cloud-identity-self-service.md`'s per-VM ADC note, both now state the termination as fact); the rest
      were historical/dated records, left as-is except one genuine, more serious finding surfaced along the way (see the
      human-planning-VM-retirement section below): the VM's termination went ahead WITHOUT cross-checking an
      already-filed P1 WIP-preservation warning for that exact host, and the flagged uncommitted work in 5 repos is now
      very likely permanently lost (no snapshot/volume survives). Resolved + escalated in
      `/plans/archive/issues/per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md` and
      `/plans/archive/issues/fleet_git_health_ip_185_known_human_planning_vm_2026_08_03.md` (both now
      `status:     resolved`), plus the duplicate now-moot allowlist todo in
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md`.

## Progress Log

- **2026-08-07**: Operator asked whether the held AO downsize (todo 8, 2026-08-04 hold) should proceed, and whether we
  have monitoring for VM resource usage. Found real historical monitoring already exists on this host
  (`resource-history-sampler.service`, 5s-cadence CPU/RAM/swap/disk/iowait JSONL since 2026-07-31 — NOT surfaced in
  deployment-ui, which only covers deployment-service-launched VMs) — pulled a genuine 24h window (17,278 samples) plus
  CloudWatch `AWS/EC2`+`AWS/EBS` cross-checks, confirmed the box is now lightly loaded (CPU p95 36%, RAM p95 29% of
  64GB, negligible EBS I/O relative to provisioned capacity) with one real but non-blocking caveat (RAM's single 24h
  peak sample at 93.8% of the new 32GB ceiling). Live AWS Pricing API: downsize saves $399.19/mo ($4,790/yr). Presented
  full findings to the operator; operator confirmed "Proceed now." **Executed live**: stop → verified `stopped` →
  `modify-instance-attribute --instance-type m8i.2xlarge` → start → verified `running` + `instance-status-ok` + EIP
  `13.113.200.22` intact. **Post-verify**: `/check-agent-orchestrator` confirmed normal backlog/dispatch behavior
  post-resize (1976 tasks, live dispatch to slot 8, no degradation). Todo 8 flipped done. Also fixed
  `agent-orchestrator-deploy.md`'s stale `m8i.4xlarge` references (table + prose) to `m8i.2xlarge` in the same pass
  (todo 7's entry updated to match) — every open item in this plan is now closed.

- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — operator-approved human plan with explicit dated
  hold (Progress Log 2026-08-04: "STOP before the actual AO box downsize and wait for explicit confirmation"); remaining
  items = AO downsize under hold + 24h-soak-gated on-disk cleanup where this plan already recorded a teardown incident.

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
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
