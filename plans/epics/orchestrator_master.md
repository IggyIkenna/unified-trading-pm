---
name: orchestrator_master
title: "Orchestrator Master (L5)"
type: epic
tier: L5
status: active
priority: P0
assigned_vm: vm-orchestrator
parent: master_to_live_defi_2026_05_23
co_operators: [harsh]
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - ../archive/2026_05/agent_orchestrator_dual_deployment_2026_05_19.md
  - ../archive/2026_05/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md
  - ../archive/agent_orchestrator_slack_notifications_2026_05_19.md
  - ../active/agent_orchestrator_workers_on_vms_2026_05_19.md
  - ../archive/2026_05/agent_reliability_mitigations_2026_05_20.md
  - ../archive/2026_05/d0_orchestrator_migration_2026_05_20.md
  - ../active/issues/human_led_audit_pool_2026_05_21.md
codex_ssots:
  - codex/11-project-management/epic-execution-with-sub-agents.md # pointer to plans/epics/README.md (epic-flow SSOT)
  - codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md # operator-shared 2026-05-21: long-lived setup-token pattern
external_references:
  - "Operator-shared 2026-05-21: Claude CLI Multi-Account Headless Authentication Guide (long-lived setup-token via
    CLAUDE_CODE_OAUTH_TOKEN env var, ~1y validity, multi-machine reuse, ANTHROPIC_API_KEY-precedence gotcha) — drives
    the r3 Auth & accounts revision and Phase 4 r3 rewrite"
---

# Orchestrator Master (L5)

**Owns**: agent-orchestrator multi-VM stack (planning-vm + 9 epic VMs); dashboard aggregation; auth failover (long-lived
setup-token pattern); per-spawn account isolation; cross-VM observability; Telegram alert framework; safety mechanisms
(stuck-agent respawn, auth failover without respawn, fresh-spawn dirty-commit, git staleness alerts).

**Assigned VM**: `vm-orchestrator` (self-managing — the agent-orchestrator stack runs the agent-orchestrator stack).

## Scope inherited from `orchestrator_v07_multi_vm_topology_2026_05_21` (promoted 2026-05-21)

This epic was promoted from the active plan `orchestrator_v07_multi_vm_topology_2026_05_21.md` per the epic
consolidation. Detailed design moved to codex SSOTs; implementation phases continue as the assigned active plans listed
below.

## Why this epic exists

Today's orchestrator runs ONE VM, ONE main agent, ONE backlog. It scaled to ~11 slots but hits recurring failure modes:
auth token expiry cascade (2026-05-21 incident), agent staleness without recovery, cross-plan blast radius, no cross-VM
observability, operator cognitive load. The v0.7 fix splits into **per-epic VM fleets** (each isolated, full agent
topology + own backend) + **one planning VM** for human work + a **dashboard landing page** that aggregates.

## Operator vision (verbatim 2026-05-21)

> "Topology should be as follows: ikenna and harsh pick master plans which agent groups tackle over their time with 1
> VM. We should be able to change these plans without restarting the VM. Each VM and epic/master plan has 1 slot main
> orchestrator agent, 1 slot review agent, x worker agents max within rate limits + CPU bound. In the dashboard we want
> a landing page overview of all the master plans/epics that each VM owns, and then when we click through we see the
> same view we already have. Separately we want a planning VM where ikenna and harsh can see each others chats.
> Auto-refresh works on each VM after one-time /login. 4 accounts per VM, primary round-robin across VMs so 8 VMs each 2
> share an account. Things should be backed up to GCS/S3 such that on VM restarts we get the info we need."

## Design SSOTs (codex)

Three codex docs hold the detailed design. The epic body is the planning orchestrator; the active plans drive the
implementation; the codex SSOTs are the architectural truth.

| Codex SSOT                                                                                                                                     | Owns                                                                                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`codex/12-agent-workflow/orchestrator-multi-vm-topology.md`](../../codex/12-agent-workflow/orchestrator-multi-vm-topology.md)                 | VM shapes (epic VM + planning VM) + Plan→VM assignment + Registry + Per-VM backend + Backlog auto-gen + Dashboard aggregation + Persistence + VM provisioning |
| [`codex/12-agent-workflow/orchestrator-safety-mechanisms.md`](../../codex/12-agent-workflow/orchestrator-safety-mechanisms.md)                 | Stuck-agent detection + auto-respawn + Auth failover (non-blocking) + Telegram alerts framework + Git staleness ping + Fresh-spawn dirty-commit               |
| [`codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`](../../codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md) | r3 auth architecture (long-lived `setup-token` via `CLAUDE_CODE_OAUTH_TOKEN`); supersedes the `.credentials.json` swap that caused the 2026-05-21 cascade     |

Registry SSOT: [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml) — 10 VMs × 19 epics × 4
accounts.

## Operator decisions captured

- **Backend topology**: per-VM backend, dashboard aggregates (each VM independently resilient).
- **VM count**: 1 planning VM + 9 epic VMs as default; flexible per epic count over time; current topology in
  `orchestrator_vm_registry.yaml`.
- **Plan → VM assignment**: frontmatter on plan is source of truth + registry regen script.
- **Failover order**: lowest-weekly-pct-first across the 3 non-primary accounts.
- **Planning VM**: cloud-hosted (NOT operator's mac); SSH from VSCode like every other VM.
- **VM naming**: descriptive ids (`vm-defi`, `vm-cefi`, ...). Dashboard `label:` field is the human-readable dropdown
  name. `ssh_host:` matches `~/.ssh/config`.
- **DNS**: single UI URL `agent-orchestrator.odum-research.com`. API endpoints under
  `*.agent-orchestrator.odum-research.com` (wildcard A record acceptable).
- **KMS**: same key per VM (one shared `agent-orchestrator-state-encrypt` key in GCP, one in AWS).
- **Cold-start**: <5 min target.
- **Per-VM RBAC**: out of scope; revisit if external collaborators get dashboard access.

## Implementation roadmap (Phase status + active plan ownership)

Detailed Phase 0-12 design lives in
[`codex/12-agent-workflow/orchestrator-multi-vm-topology.md`](../../codex/12-agent-workflow/orchestrator-multi-vm-topology.md).
Implementation work is owned by the assigned active plans below. Status as of 2026-05-21:

| Phase      | Scope                                                                                                                                                                                                                                                                                                                                                                                                                            | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Owned by active plan                                                                             |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 0          | Prerequisites (OAuth auto-refresh + per-account creds swap + Telegram alert framework)                                                                                                                                                                                                                                                                                                                                           | ✅ DONE (agent-orch@4eabf5c + @2de9410); one operator action remaining                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | `d0_orchestrator_migration_2026_05_20`                                                           |
| 1          | Registry yaml + `assigned_vm:` frontmatter + regen script + CLAUDE.md update                                                                                                                                                                                                                                                                                                                                                     | ✅ DONE (PM@e3f11893; updated to v2 2026-05-21)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `d0_orchestrator_migration_2026_05_20`                                                           |
| 2          | Multi-VM dashboard (SPA `/` landing + `/api/vm/summary` endpoint + cross-VM cards + Firebase deploy)                                                                                                                                                                                                                                                                                                                             | ✅ DONE 2026-05-21 (agent-orch@c274059 + @f357132)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `agent_orchestrator_cloud_run_deployment_2026_05_19`                                             |
| 3          | Safety mechanisms (stuck-detection + auto-respawn + dirty-commit + git-staleness alert)                                                                                                                                                                                                                                                                                                                                          | ✅ DONE 2026-05-21 (agent-orch@72b4b0a)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `agent_reliability_mitigations_2026_05_20` + `agent_orchestrator_slack_notifications_2026_05_19` |
| 4a         | Spawn path → env-var auth (r3) (`oauth_token_env_file` + `tmux_spawn.py` refactor)                                                                                                                                                                                                                                                                                                                                               | ✅ DONE 2026-05-21 (agent-orch@d7b6ad6)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b         | r3 env-file routing: roster on SSOT slugs (`sub-a-ikenna`/`sub-b-iggy2london`) + `AccountDef.operator`; spawn + `/usage` probe + `oauth_refresh` all bypass the legacy swap/refresh for any account with `oauth_token_env_file`. Legacy `.credentials.json` path retained for `harsh-primary` until its setup-token lands. Also fixed a silent poller `resets_at`-kwarg `TypeError` that was blocking per-account usage updates. | ✅ DONE 2026-05-21 (agent-orch@5d78133; deployed + env-file `/usage` probe verified: sub-a 8%/4%, sub-b 1%/8%)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b-cleanup | Remove legacy code once `harsh-primary` migrates to a setup-token: delete `_swap_credentials_for`/`_restore_credentials`, disable `oauth_refresh.refresh()` auto-call, remove `.credentials.<id>.json` files + the `swap_claude_account.sh` reference. CLAUDE.md HARD RULE (no `.credentials.json` copy between machines).                                                                                                       | ✅ DONE 2026-05-28 (agent-orch@d883e41→@8c52691: dropped swap helpers + oauth_refresh + gcs_creds_poller modules + refresh-oauth/sync-from-gcs endpoints + OAuthBadge UI; tightened tmux_spawn/usage_tracker/spawn callers to require env_file; CLAUDE.md HARD RULE landed in PM)                                                                                                                                                                                                                                                                                                                                                                              | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4c         | Dashboard repurpose (`SetupTokenBadge` shows 1-year expiry warn/crit/expired levels; `notify_setup_token_expiring` fires at ≤30d + ≤7d; `setup_token_expires_at` in accounts.json; all 3 r3 accounts seeded to 2027-05-21)                                                                                                                                                                                                       | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 5          | Account roster expansion (operator runs `setup-token` per distinct subscription; verify-distinct-subscription test; GCS distribution)                                                                                                                                                                                                                                                                                            | ✅ DONE 2026-05-28 — All 4 accounts (3 Ikenna + 1 Harsh) have setup-tokens minted + env files distributed to both GCS (`central-element-323112-orchestrator-creds/accounts/`) and S3 (`uts-orchestrator-creds-427895769566/accounts/`), 206 bytes each, verified                                                                                                                                                                                                                                                                                                                                                                                               | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 6          | Backlog auto-gen from plans (`regen_backlog_from_plan.py` + plan-reload poll + CLAUDE.md hard rule)                                                                                                                                                                                                                                                                                                                              | ✅ DONE 2026-05-28 — `regen_backlog_from_plan.py` + `PlanRegenLoop` (6h cadence, fires within 60s of boot, env-tunable, `POST /api/backlog/regen` for manual) + 29-test suite (agent-orch@2a24c46); content-based dedup fixed an idempotency bug surfaced by the new tests; CLAUDE.md HARD RULE added                                                                                                                                                                                                                                                                                                                                                          | (formerly `agent_orchestrator_workers_on_vms_2026_05_19`, archived)                              |
| 7          | Planning VM provisioning (cloud-hosted; slot 1+2 only; registry symlink; landing-page wired)                                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-28 — Central API EC2 VM (`13.113.200.22`, AWS ap-northeast-1) serves as the planning VM (ikenna-vm role=planning in `backends.json`); cross-VM `/api/fleet/summary` fan-out + `Landing.tsx` cards live in dashboard (verified: HTTPS /health 200 + 12 backends registered); planning VM bootstrap items shipped under archived `epic_vm_fleet_commissioning_2026_05_21`                                                                                                                                                                                                                                                                        | (formerly `agent_orchestrator_workers_on_vms_2026_05_19`, archived)                              |
| 8          | Persistence (SQLite hot-backup → GCS every 6h via `SnapshotLoop`; restore script `scripts/restore_from_gcs.sh`)                                                                                                                                                                                                                                                                                                                  | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1; KMS-encrypted creds pending)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | `agent_orchestrator_dual_deployment_2026_05_19`                                                  |
| 9          | VM provisioning (packer/docker pipeline; immutable image; `bootstrap_vm.sh`; <5min cold-start)                                                                                                                                                                                                                                                                                                                                   | ✅ DONE 2026-05-28 — Packer HCL2 template + provisioner scripts (`deployment-service/packer/agent-orchestrator/`); `bootstrap_vm.sh` detects `/etc/orchestrator-ami-version` marker + rsyncs warm repos + venv from `/opt/orchestrator-warm/` (Steps 1+2+4.5 skipped on prebaked path); `launch-epic-vm-aws.sh` accepts `AMI_ID` env-var override; README + codex DNS-cutover SSOT shipped. Operator runs `packer build` to bake, then `AMI_ID=… launch-epic-vm-aws.sh` to use                                                                                                                                                                                 | (formerly `agent_orchestrator_dual_deployment_2026_05_19`, archived)                             |
| 10         | Review agent role (`agents/review.md` boot prompt; commit-poll logic; auto-merge happy-path)                                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-21 (`agents/review.md` shipped; agent-orch@tab/ikennaigboaka/1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `agent_orchestrator_workers_on_vms_2026_05_19`                                                   |
| 11         | Rollout to 9 epic VMs (provision via Phase 9 pipeline; DNS A records; cut over current single-VM to vm-defi)                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-28 — Fleet of 10 epic VMs already running (commissioned 2026-05-22→23 via `aws_epic_vm_fleet_2026_05_22`); cut over from single-VM model superseded by central-API-VM-plus-fleet topology (current `backends.json` shows 12 backends, all live); EIP allocation script shipped (`deployment-service/scripts/aws/allocate-orchestrator-eips.sh`) + DNS cutover recipe codified ([agent-orchestrator-dns-cutover.md](../../codex/05-infrastructure/agent-orchestrator-dns-cutover.md)). Operator runs EIP script + adds A records to complete cutover when convenient (not blocking; current ops work fine on dynamic IPs via central API proxy) | (formerly `agent_orchestrator_cloud_run_deployment_2026_05_19`, archived)                        |
| 12         | Cleanup + docs (archive superseded plans; codex SSOTs landed; CLAUDE.md System-First Architecture pointer)                                                                                                                                                                                                                                                                                                                       | ✅ DONE 2026-05-21 — codex SSOTs landed, plans archived (hygiene sweep), CLAUDE.md System-First Architecture pointer already accurate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `d0_orchestrator_migration_2026_05_20`                                                           |

## Composition with other epics

- **Orchestrates all 18 other epics**: every epic VM in the registry hosts an instance of the agent-orchestrator stack
  this epic owns. Topology changes (new VM, account roster expansion, planning VM moves) ripple to every other epic.
- **Audit-pool flow**: every audit row in `plans/active/issues/human_led_audit_pool_*.md` flows through the planning VM
  (defined here) → wrapper plans → target epic VM dispatch. See
  [`../../plans/epics/README.md`](../../plans/epics/README.md) for the audit→plan→epic flow.
- **Cross-cutting partnerships**: `infrastructure_master` (VM tarballs + provisioning + cloud bootstrap underpins this
  epic's VM lifecycle); `observability_master` (alerting-service + Telegram alerts + monitoring composes with § C
  Telegram alerts framework); `client_isolation_and_governance_master` (per-spawn account isolation per
  `agent_orchestrator_per_spawn_account_isolation_2026_05_20` enforces governance at the spawn boundary).

## Out of scope (post-v0.7)

- Multi-region VMs (today: all asia-northeast1)
- Per-VM separate Telegram channels (today: single shared chat)
- Cross-VM dependency graph (e.g. vm-ml waits on vm-features); today operators coordinate via epic prereqs
- Auto-scaling worker count based on backlog depth (today: fixed at 8-16 per VM)
- Cloud Run / serverless orchestrator backend (today: VM-bound systemd); defer until VM ops become painful
- Per-VM RBAC

## Assigned active plans

_All originally-assigned sub-plans are now archived (last-touched 2026-05-22 via supersession). Remaining non-archived
orchestrator work lives in the Phase 6/9/11 rows of the table above + the audit-pool issue doc linked under
[Composition with other epics](#composition-with-other-epics). Auto-populated by
`scripts/plans/populate_epic_bodies_2026_05_21.py` (next regeneration will surface zero active plans here)._

## P0 — must complete before next foundation gate

### `auth_failed` was a one-way ratchet → rotation pool collapsed to one account (discovery + fix 2026-06-07)

**status**: 🟢 CODE FIXED (agent-orchestrator, `tab/ikennaigboaka/1` → LDR) — one operator action remaining on the live
VM. · **provenance**: slot-1 main during account-99%/PM#164-escalation triage, 2026-06-07.

**What I found**: The orchestrator IS designed to auto-rotate across all 4 accounts (cross-operator shared pool;
`_pick_headroom_account` / `pick_next_account` pick any usable account with headroom). But `auth_failed` was a **one-way
latch**: the spawn-heartbeat watchdog (`worker_liveness.py:_check_spawn_heartbeat_timeouts`) marks an account
`auth_failed` on ANY spawn that doesn't `/heartbeat` within ~180 s (cold-start slowness, a custom prompt that skips the
lifecycle, a transient), `account_is_usable` then excludes it from rotation, and the ONLY clear path (`server.py:~829`)
was a `/heartbeat` from a worker spawned **on that account** — which can never happen while it's excluded. So every
transient spawn failure permanently sidelined a healthy account. Over time the usable pool eroded to just
`sub-a-ikenna`; when it hit 99% weekly, `pick_next_account` returned `None` → the PM#164 escalation reported "no
headroom account / no escalation_id" even though `sub-b-iggy2london` + `sub-c-ikenna-odum` had valid tokens (good
to 2027) and full headroom.

**Why it matters**: single-point-of-failure on one account; defeats the entire multi-account failover design; blocks
escalations + autospawn fleet-wide when the primary rate-limits. Contradicts the epic's "4 accounts, round-robin" SSOT.

**Fix shipped** (agent-orchestrator): added cooldown-based auto-recovery — `AccountUsageRow.auth_failed_at` +
`auth_failed_retries` columns (ORM + `bootstrap.py` ALTER-TABLE migration); `mark_account_auth_failed` stamps the time +
increments retries; new `account_in_auth_failed_cooldown()` (exponential backoff `600s·2^(retries-1)`, cap 6 h) gates
`account_is_usable` so a sidelined account **re-enters the pool for a re-probe** after the window — a successful
heartbeat fully clears it (`clear_account_auth_failed` resets timestamp+retries), a repeat failure re-marks with a
longer window. Legacy rows with NULL `auth_failed_at` are treated as cooldown-elapsed → auto-heal the already-latched
accounts on first deploy. `account_is_auth_failed` kept as the raw-status check for the heartbeat healing path. Tests:
`tests/test_auth_failed_rotation.py` `TestAuthFailedCooldownAutoRecovery` (+ 78 related rotation/escalation tests
green).

- [x] ✅ [AGENT] P0. Cooldown auto-recovery for `auth_failed` — code shipped (agent-orchestrator, QG-green).
- [ ] [OPERATOR] P0. On the LIVE orchestrator (`i-0c9b283b31d6b5ca7`, not SSM-reachable): **(a)** redeploy
      agent-orchestrator so the new code + migration take effect; the NULL-timestamp auto-heal then un-latches
      `sub-b-iggy2london` / `sub-c-ikenna-odum` on the next rotation tick. **(b)** Immediate unblock before redeploy:
      from the dashboard force a spawn with `account_id=sub-b-iggy2london` (explicit `/api/slots/{N}/spawn` bypasses the
      usable gate) → on heartbeat `server.py` auto-clears its `auth_failed`. Repeat for `sub-c-ikenna-odum`. Confirm
      `~/.claude-accounts/sub-b-iggy2london.env` is present on the live VM (re-sync from the creds bucket if not).

### LDR integration has no hard regression-gate (discovery 2026-06-01, fleet code-freeze)

**status**: 🔴 OPEN — surfaced during the 2026-06-01 fleet code-freeze (operator-called to stop agents undoing
data-migration + quality-gate work). Root-cause item for the orchestrator/QG hardening pass. · **provenance**:
operator + slot-1 main, 2026-06-01.

**What I found**: Worker tab-branch commits reach `live-defi-rollout` (LDR) only via the worker's own
`Commit + Push + Flip` step (`git push origin HEAD:live-defi-rollout`). There is **no hard gate** preventing an
autonomous worker (running `--dangerously-skip-permissions`) from resolving a rebase/merge conflict by reverting another
agent's committed work — just to land a clean merge or a green QG — which **silently regresses plan intent**. The
existing machinery _parks, reports, and (after 15 min) pages + nudges_ — but it does **not block**:
`slot-cron-ff-pull.sh` is fast-forward-only and skips ahead/diverged worktrees (`[skip:diverged] … need manual rebase`);
`slot-git-status-report.sh` POSTs ahead/behind drift to `/api/slots/<N>/git-status`; and `worker_liveness.py` (line
~343) already flags `ahead>0 || diverged` for >15 min (`any_red_15m`), fires `notify_git_staleness_red`, and nudges the
worker to commit. So detection + alert + nudge EXIST. What does NOT exist is a hard gate: nothing stops an autonomous
worker from force-resolving a conflict (alert ≠ prevention), and the server has no tab→LDR auto-integration. Concrete
instance at freeze: `vm-cefi:.tabs/2/market-tick-data-service` = **6 ahead / 34 behind** LDR, un-integrated.

**Why it matters**: This is the structural path by which "stupid agents undo good work on data migration and quality
gates" — the exact failure the 2026-06-01 freeze was called to stop. The protection today is soft governance (CLAUDE.md
conditional-push + `rebase --abort` rules + agent judgment), not enforcement.

- [x] ✅ [SCRIPT] P0. **OWNED BY QUICKMERGE (operator decision 2026-06-01).** The pre-LDR-push gate lives in
      `quickmerge`'s conditional-push / SHA-sentinel path (QG must have passed on the exact SHA, else blocked) — NOT a
      separate orchestrator hook. A fleet-wide git `pre-push` hook was evaluated + rejected: it requires
      `core.hooksPath` (collides with prek's pre-commit hooks), only adds "block non-FF" (which GitHub already rejects
      server-side), and carries fleet-wide blast radius for ~zero marginal value. Any hardening of the
      force-resolved-integration guard is tracked against quickmerge (PM), not here. Originally: add a pre-LDR-push gate
      that BLOCKS any non-fast-forward push to `HEAD:live-defi-rollout` unless (a) the rebase replayed with ZERO
      conflicts, or (b) explicit plan-ref + ack. Composes with the `Commit + Push + Flip` HARD RULE.
- [x] ✅ [SCRIPT] P1. ✅ DONE 2026-06-01 (live). `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` now SET fleet-wide: enabled on both
      running orchestrator VMs (`agent-orchestrator-vm-1` i-0c9b283b31d6b5ca7 + `agent-orch-vm-orchestrator-20260522`
      i-007e8d99d12831578) via systemd drop-in `slack-alerts.conf` (webhook fetched from GCP SM
      `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` — the AWS instance role is denied SM read, GCP gcloud auth is the working
      path), orchestrator restarted, `slack_env_set=1` + test message delivered (`webhook_post=ok`) on both. The
      clean-but-diverged page is already wired (`worker_liveness` L355 fires on `ahead>0||diverged` independent of dirty
      — verified). Tooling for new/re-bootstrapped VMs: `bootstrap_vm.sh` 5.5b-quater
      (agent-orchestrator@a07a8bb/@34333b0) + drop-in `scripts/orchestrator/enable_slack_alerts.sh`
      (PM@424b8db98/@a0fe469d6). (Live fleet is 2 VMs, not 11 — consolidated.)
- [x] ✅ [DOC] P1. ✅ DONE 2026-06-01 — agent-orchestrator@f31f8ff (worker.md fresh-pull 1b:
      tab-branch-vs-integration-branch topology + "park-and-preserve, never force-resolve" contract + per-repo base) +
      PM@74a557f1f (codex `per-tab-worktrees.md` "Pre-spawn branch-state + liveness-gated dirty resolution" section). A
      worker can no longer infer "pushed to my tab branch" == "integrated to LDR".

### VM `.git` file-ownership rot (root-owned objects) — fleet-wide (discovery 2026-06-01)

**status**: ✅ RESOLVED 2026-06-01 — durable fix shipped: `fleet-git-health-guard.sh` (chown + fsck + alert) on a 30-min
root cron on both live VMs (auto-heals root-owned objects + detects corruption). Root-cause investigation confirmed the
tarball excludes `.git` and no standing root op creates them (all git runs as ubuntu). On install the guard caught +
healed real object corruption on vm-2 (`unified-trading-api` + `instruments-service`). Earlier MITIGATED note
(fleet-wide chown, 121–133 → 0) stands; the guard makes it self-healing. · **provenance**: slot-1 main during
code-freeze cleanup + the 2026-06-01 agent-orchestrator campaign.

**What I found**: Every orchestrator VM had ~121–133 root-owned files under `~/unified-trading-system-repos/**/.git/`
(objects). `bootstrap_vm.sh` chowns after its initial clones (lines 291/316), so provisioning is NOT the origin — a
LATER root-run operation created them (most likely the VM code-tarball redeploy extracting as root, or a `sudo git`/cron
on the box). Symptoms already observed: `error: task 'gc' failed`, `failed to run reflog`, and
`cannot lock ref … Permission denied` on fetch. On **vm-ml** this tipped into real corruption — a fetch interrupted by
the permission error left a missing parent object (`83fac638`), breaking history walks across all 7 pm worktrees (the
bogus "2858 ahead" reading). Healed via ownership fix + `git fetch --refetch`; 3 uncommitted base edits preserved on
`chore/ml-base-wip-2026-06-01`. No existing plan/issue tracked VM `.git` ownership (closest are Claude/API-auth plans —
different scope).

**Why it matters**: latent fleet-wide git breakage — silent fetch/gc/ref-lock failures degrade the FF-pull + LDR
integration machinery and can corrupt object stores (as on ml). Directly undermines the "clean start" + data-pipeline
correctness the freeze protects.

- [x] ✅ [INFRA] P0. ✅ INVESTIGATED + durable fix shipped 2026-06-01. **The tarball is NOT the origin** —
      `create-code-tarballs.sh` line 212 `--exclude='.git'`, so the redeploy/extract path carries no `.git` objects.
      Audited the live fleet (both VMs via SSM): orchestrator.service runs as `User=ubuntu`; both git crons
      (slot-cron-ff-pull, slot-git-status-report) run as ubuntu; `pm-pull.service` runs as `User=root` BUT wraps every
      git call in `sudo -u ubuntu git` (verified); `bootstrap_vm.sh` chowns after its clones. **No standing root
      operation creates root-owned `.git`** — the original 121–133 root-owned objects were episodic (ad-hoc root git ops
      / early pre-chown bootstrap / now-retired VMs). Durable fix = the fleet git-health guard on a timer (INFRA P1
      below), now deployed. Residual hardening if ever needed: ensure ad-hoc root SSM ops that touch repos `chown` after
      (the guard auto-heals regardless).
- [x] ✅ [INFRA] P1. ✅ DONE 2026-06-01 — `agent-orchestrator/scripts/fleet-git-health-guard.sh` (@c5d7cc7: chown -R to
      slot user + `git fsck --connectivity-only` per repo + orchestrator-inbox Slack alert) DEPLOYED + installed as a
      30-min root cron on both live VMs. **Caught + healed real corruption on its first run:** vm-2 had broken/missing
      git objects in `unified-trading-api` + `instruments-service` (the same rot class as the vm-ml incident) — healed
      via `git fetch --refetch` → both `fsck OK`. Composes with the `worker_liveness.py` git-staleness alert. NB
      follow-up: the guard's Slack alert needs the webhook in the cron env (currently logs to
      `/var/log/fleet-git-health-guard.log`; the chown+fsck heal works regardless) — see Findings.
- [x] ✅ [SCRIPT] P2. ✅ DONE 2026-06-01 — agent-orchestrator@589b711. `fleet-git-health-guard.sh` gained
      `_resolve_webhook()`: when `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is unset (the root-cron case) it self-fetches from
      Secret Manager (gcloud as the slot user → AGENT_ORCHESTRATOR_SLACK_WEBHOOK /
      alerting-uts-live-alerts-slack-webhook; AWS SM fallback). Verified live on both VMs from the root path:
      `webhook self-resolve len=81 OK`. So corruption like the vm-2 find now PAGES, not just logs.
- [x] ✅ [INFRA] P1. ✅ DONE 2026-06-01 — agent-orchestrator@589b711. `scripts/ao-self-pull.sh` FF-pulls the
      orchestrator's actual `WorkingDirectory` checkout from origin/live-defi-rollout (git as slot user, ff-only, never
      forces) and restarts orchestrator on HEAD change; installed as a 15-min root cron on both live VMs (verified
      `ao-self-pull cron installed=1`, AO HEAD=589b711 on both). Closes the deploy-currency gap (vm-2 had been 14 behind
      running stale server code). NB: a `verify_fleet_autonomy_health.sh` gate citing the AO main-checkout behind-count
      is a nice incremental add (the existing script already reports per-VM behind-count vs LDR HEAD).

## P1 — important; post-current-gate

### [`d0_orchestrator_migration_2026_05_20`](../archive/2026_05/d0_orchestrator_migration_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-21 — Port 8026 aligned, CORS confirmed, LEDGER.md deprecated, CLAUDE.md prod URL added.
All phases done.

## P2 — useful; opportunistic

- [ ] [INFRA] P1. **F7 — slot-4 WIP recovery on vm-0** [BLOCKED-INFRA: live-host WIP judgment] (**MIGRATED FROM:**
      `orchestrator_fleet_worker_spawn_enablement_2026_06_02.md`, archived 2026-06-07). `origin/tab/vm-0/4` does not
      exist for `unified-api-contracts` (slot-4 worktree on `fix/tradfi-exchange-mappings-minimal`) +
      `unified-trading-pm` (on `fix/pm-ci-self-clone`) — the slot branch was never created / was replaced by these
      feature branches holding unmerged WIP. Fix (on the live vm-0 via SSM): inspect each WIP (merged? abandonable?) →
      merge or set aside → create `tab/vm-0/4` from LDR + recreate the 2 worktrees. Slot-4 stays quarantined by design
      (1 of 10) until then. NOT blind-switchable — needs per-branch WIP judgment, hence operator/live-host-gated.

**status**: ✅ ARCHIVED 2026-05-21 — Phases 0-4+6 done. Firebase first-deploy + Phase 5 prod cutover DEFERRED-HUMAN-GATE
(gated on workers-on-vms D3). · **estimate**: 4.8 cal AI-days (class: infra)

### [`agent_orchestrator_dual_deployment_2026_05_19`](../archive/2026_05/agent_orchestrator_dual_deployment_2026_05_19.md)

**status**: ✅ ARCHIVED 2026-05-21 — Design locked. D11/D5/D18/D19/D4 done. D14 DEFERRED-POST-CUTOVER (ships with
workers-on-vms). · **estimate**: 0.6 cal AI-days (class: design)

### [`agent_orchestrator_per_spawn_account_isolation_2026_05_20`](../archive/2026_05/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-21 — SUPERSEDED by oauth token env-var approach (`CLAUDE_CODE_OAUTH_TOKEN`); Phase
4b-cleanup landed 2026-05-28 (legacy `.credentials.json` swap path + `oauth_refresh` + `gcs_creds_poller` modules
removed).

### [`agent_orchestrator_slack_notifications_2026_05_19`](../archive/agent_orchestrator_slack_notifications_2026_05_19.md)

**status**: ✅ archived 2026-05-21 · **estimate**: 2.0 cal AI-days (class: infra) · all 4 phases shipped

### [`agent_orchestrator_workers_on_vms_2026_05_19`](../archive/agent_orchestrator_workers_on_vms_2026_05_19.plan.md)

**status**: ✅ ARCHIVED 2026-05-22 — SUPERSEDED by `epic_vm_fleet_commissioning_2026_05_21` (10-VM fleet replaced the
asymmetric Ikenna+Harsh topology). · **estimate**: 6.4 cal AI-days (class: infra)

### [`agent_reliability_mitigations_2026_05_20`](../archive/2026_05/agent_reliability_mitigations_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-4 done (mirror-events, dirty-state gate, claim tag, in-flight files).
Phase 5 gitignore-on-demand DEFERRED-POST-CUTOVER. · **estimate**: 1.2 cal AI-days (class: infra)

### [`aws_epic_vm_fleet_2026_05_22`](../archive/2026_05/aws_epic_vm_fleet_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — AWS EC2 fleet commissioned (10 VMs); CLOUD_PROVIDER=aws default flipped; GCP path
retained. All phases done. · **estimate**: 1.2 cal AI-days (class: infra)

**Deferred (MIGRATED FROM archived plan)** — post-cutover P3:

- DNS: point `api-<vm>.agent-orchestrator.odum-research.com` to AWS EIPs or ALB
- EIP allocation: stable EIPs for DNS (currently dynamic IPs); update `backends.json` once allocated
- AWS Secrets Manager rotation: automate quarterly rotation via Lambda
- Cost monitoring: weekly `aws ce get-cost-and-usage` report for orchestrator fleet

### [`orchestrator_headless_agent_auth_2026_05_22`](../archive/2026_05/orchestrator_headless_agent_auth_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Headless token-auth shipped for workers + main/review/backup agents; 10-VM fleet
deployed to main@1a98cca; usage scraping re-engineered for Claude 2.1.145. · **estimate**: original scope (infra)

**Deferred (MIGRATED FROM archived plan)** — P3 backlog:

- RC-capable agents: `.credentials.json` capture/sync pipeline + per-account CLAUDE_CONFIG_DIR wiring; unblocks
  `claude.ai/code` Remote Control URL for live session drop-in. Separate build-out from setup-token flow; both auth
  types coexist via separate CLAUDE_CONFIG_DIRs.

### [`multi_backend_fleet_connectivity_2026_05_22`](../archive/2026_05/multi_backend_fleet_connectivity_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-6 done: centralized API router with private-VPC proxying; single-token
auth (HS256); per-VM interactive proxy; self-registration + staleness; codex updated. · **estimate**: 2.8 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — P3 backlog:

- **GCS JWT secret read** + **`reload_secret()` poller**: grant `storage.objectViewer` on
  `central-element-323112-orchestrator-creds` to central VM's ADC, or provision a VM SA. Two items ship together.
  BLOCKED-OPERATOR (needs project-owner action).
- **RS256/ES256 asymmetric auth**: fleet-wide auth migration; seam already in Phase 4. Successor:
  `orchestrator_asymmetric_auth_<date>` plan when operator gives go-ahead.

## P3 — backlog; revisit quarterly

- [x] ✅ [SCRIPT] P3. **NICE-TO-HAVE** ✅ DONE 2026-06-01 — `scripts/orchestrator/probe_plan_regen_pipeline.sh`: POSTs
      `/api/backlog/regen` (loopback, tries :8765 central then :8026) and asserts `ok==true` AND `scanned_plans>0`
      (scanned>0 proves PM-pull delivered current plans AND regen walked them). Exit 0/1 for cron alerting; intended as
      a daily cron (`0 6 * * *`). Live-verified on vm-1: `{"ok":true,"scanned_plans":44,"total_tasks":211}` — pipeline
      alive. **MIGRATED FROM:** `e2e_test_plan_regen_pipeline_2026_05_29.md` (one-shot test verified the pipeline
      2026-05-30 but left no continuous guard). NB: the daily cron entry itself is not yet installed on the VMs (script
      shipped + verified; scheduling is a one-line crontab add per VM).
