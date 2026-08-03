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
    scripts/self-hosted-runners/setup-glue-runners.sh,
    scripts/self-hosted-runners/classify-glue-workflows.sh,
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
- [ ] [INFRA] P0. Launch the escalation VM — `c8i.4xlarge` (16 vCPU/32GB), ap-northeast-1, sized/secured to match the
      current AO box's access model (SSM-only, no inbound SSH unless explicitly decided otherwise), gp3 storage sized
      per the enumerated runner count from the prior todo (not a blind 600GB guess). Gate: `aws ec2 describe-instances`
      shows `running`, verified reachable via SSM.
- [ ] [INFRA] P0. Deploy the runner toolchain to the new VM via a **dedicated fresh git clone** (mirroring
      `/opt/glue-deploy/unified-trading-pm`, never copying the old box's files), run `preflight` in the runner's real
      environment, confirm exit 0. Gate: `preflight` green via `systemd-run --uid=ubuntu`, not a login shell.
- [ ] [INFRA] P0. Migrate ONE canary repo's runner registration to the new VM (pick the smallest/lowest-risk repo from
      the enumeration), verify its next CI run claims the new VM's runner and goes green, THEN deregister that repo's
      old runner on `i-0c9b283b31d6b5ca7`. Gate: a real CI run on the canary repo shows `success`, claimed by the new
      VM's runner name.
- [ ] [INFRA] P1. Migrate the remaining enumerated repos in verified batches (mirror the original migration's
      canary→10→remaining phasing) — each batch: register on new VM, verify green, THEN deregister the old runner for
      those repos. Do not batch-migrate without verifying the prior batch first. Gate: per-batch, a passing CI run per
      migrated repo cited by run URL.
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
