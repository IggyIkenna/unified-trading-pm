---
doc_type: plan
title: Orchestrator e2e control-plane validation + VM-from-scratch hardening
summary: >-
  Agent-orchestrator bootstrap/watchdog/memory-guardrail hardening and VM-from-scratch e2e validation — split out of
  monitoring_control_plane_master_2026_06_10.md as a file-disjoint scope-creep section (agent-orchestrator internals,
  not the CI-dashboard/fleet-git-health mission the parent plan owns).
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: [monitoring, orchestrator, vm-bootstrap, watchdog, e2e, plan-hygiene, plan-split]
related:
  [
    plans/active/monitoring_control_plane_master_2026_06_10.md,
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
depends_on: []
supersedes:
superseded_by:
source: >-
  Split out of monitoring_control_plane_master_2026_06_10.md (§ "Orchestrator e2e control-plane validation + main-agent
  first-responder" + § "VM-from-scratch e2e") per the plan line-cap remediation triage
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row #19; operator-approved unlock+split 2026-07-23).
  This content was a scope-creep section covering agent-orchestrator bootstrap/watchdog/memory-guardrail hardening,
  file-disjoint from the parent's CI-dashboard/fleet-git-health mission — moved verbatim, nothing summarized or dropped.
last_updated: 2026-06-27
context_scope:
  [
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    agent-orchestrator/scripts/bootstrap_vm.sh,
    agent-orchestrator/server/worktree_clean_check/_resolve.py,
    agent-orchestrator/scripts/refresh_env_from_sm.sh,
  ]
---

# Orchestrator e2e control-plane validation + VM-from-scratch hardening

> Split verbatim (2026-07-24) out of `monitoring_control_plane_master_2026_06_10.md` per the plan line-cap remediation
> triage (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`). This doc carries the parent's entire
> "Orchestrator e2e control-plane validation + main-agent first-responder" section (through "VM-from-scratch e2e" and
> its live run) unchanged — no content was rewritten or summarized. See `monitoring_control_plane_master_2026_06_10.md`
> for the CI-dashboard/fleet-git-health mission this scope-creep section was split away from.

### Orchestrator e2e control-plane validation + main-agent first-responder (2026-06-11, Harsh slot-5, local)

Charter line exercised: "Orchestrator side — make the agents **stable** and **picking up** work." Full local e2e run of
the orchestrator control plane from the slot-5 checkout (backend + dashboard on :8765/:5173, sandboxed state in
`.orch-e2e-sandbox/` — fake `ORCHESTRATOR_VM_ID=vm-local-e2e` + `ORCHESTRATOR_PM_REPO_PATH` sandbox PM clone, zero fleet
writes). **VALIDATED live end-to-end**: plan → PlanRegenLoop (assigned_vm-filtered) → backlog → manual spawn → /boot
dispatch → worker executed a real MTDS function-length audit (196 violations / 3,211 functions scanned, report artifact)
→ /done → same-second next-task dispatch → worker /blocked (A/B scoping question) → **main agent auto-answered it in 31
s with plan-grounded reasoning** → worker resumed on the queued answer → applied option B → final /done. Both tasks
`done` in state.db with sentinel SHAs.

- [x] ✅ [CODE] P1. DONE 2026-06-11 — agent-orchestrator@05be1e0 (keeper + lifespan wiring + 7 unit tests; suite 499
      passed) + agent-orchestrator@6b63a77 (main.md boot-template STEP 2.5 blocked-queue sweep: poll
      `/api/state.blocked[]` every tick; answer when plan/SSOT/worker-recommendation suffices via
      `POST /api/blocked/<id>/answer` from_role=main; defer ONLY genuinely operator-level calls — spend, creds,
      destructive, scope — and surface once in chat). **MainAgentKeeper — the main agent (fleet supervisor + /blocked
      FIRST responder per agents/main.md) is now auto-spawned at backend start + kept alive** (singleton tmux
      `orch-agent-main`, 60 s tick, autospawn-shared headroom gate, 5-min cooldown, 3/h flap guard → 1 h backoff,
      `ORCHESTRATOR_MAIN_AGENT_ENABLED` default ON). Previously NOTHING spawned it — the blocked-answer contract
      silently depended on an operator hand-pasting main.md (repro: a worker /blocked sat unanswered on a fresh
      backend). Live-verified: keeper spawn → register → `blocked_answered` (BLK-60790ca7) in 31 s. Repo:
      agent-orchestrator.

Unsolved findings from the run (each repro'd live or read in code; fix not yet shipped):

- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). Route now mirrors PlanRegenLoop env
      resolution (ORCHESTRATOR_VM_ID + REGEN_PRUNE_STALE + REGEN_DB_PATH). Was: **Manual `POST /api/backlog/regen`
      bypasses the `assigned_vm` filter + prune** — `routes/backlog.py:126` calls `regen()` with no args; `regen()`
      defaults `vm_id=None` = ingest-all (its docstring claims an `ORCHESTRATOR_VM_ID` env fallback that is NOT
      implemented — only `PlanRegenLoop.__init__` reads the env). Live repro: manual regen ingested 493 tasks from 53
      fleet plans into a vm-local-e2e backend; the next 120 s loop tick pruned all 491 foreign tasks (self-heal works,
      ≤30 min on fleet), but in that window AutoSpawn can dispatch foreign-VM tasks. Fix: route (or `regen()` itself,
      honouring its docstring) passes `vm_id=ORCHESTRATOR_VM_ID` + `ORCHESTRATOR_REGEN_PRUNE_STALE`. Repo:
      agent-orchestrator (`server/routes/backlog.py` + `server/regen_backlog_from_plan.py`). Found 2026-06-11.
- [x] ✅ [INFRA] P1. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). STEP 5.9 (install_pm_pull.sh → LDR) is now
      the ONLY installer; STEP 7.5c became a loud verifier; duplicate scripts/pm-pull.{service,timer} (origin-main
      pullers) DELETED. Was: **`bootstrap_vm.sh` installs pm-pull TWICE with DIFFERENT branches** — Step 5.9 runs PM's
      `install_pm_pull.sh` (merges `origin/live-defi-rollout`); Step 7.5c installs AO's own `scripts/pm-pull.service`
      (`git pull --ff-only origin main`) under the SAME systemd unit name. Whichever lands first wins (7.5c skips if 5.9
      enabled the timer; if 5.9 WARN-fails — PM clone absent — the main-puller installs into an LDR checkout where
      `--ff-only origin main` near-always fails → **plans silently freeze** with only a journald WARN). Which branch a
      VM's plan source tracks is nondeterministic per bootstrap path. Collapse to ONE installer + ONE branch (LDR per
      the regen/plan-freshness contract). Repo: agent-orchestrator (`scripts/bootstrap_vm.sh` +
      `scripts/pm-pull.service`). Found 2026-06-11.
- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). resolve_dirty_state() wired into the
      autospawn pre-spawn gate (same liveness-gated semantics as the kicker; protected_live_peer/quarantined refuse the
      spawn). Was: **AutoSpawn respawn path skips the FM2/FM3/FM8 dirty-state gate** — `autospawn.py:289-298` runs only
      `check_slot_branch_state` (FM5/FM7); manual `/spawn` (slots_ops.py:204), account rotation (server.py:416), and the
      kicker auto-respawn (worker_liveness.py:929) all call `resolve_dirty_state()`, but the dominant fleet path —
      **watchdog kill → AutoSpawn respawn — boots the new worker into the dead predecessor's dirty tree**, and the \*/5
      FF-cron then `[skip:dirty]`s the slot → stale clone. Also compose: a permanently-dead slot's dispatched task is
      recovered only by same-slot /boot resume (`already_in_progress`); there is no requeue-to-pool on slot death. Wire
      `resolve_dirty_state()` into the autospawn pre-spawn gate. Repo: agent-orchestrator (`server/autospawn.py`).
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). verify_done now sets on_origin (git branch
      -r --contains, local remote-tracking refs — no network); /done emits sha_not_on_origin warning;
      ORCHESTRATOR_DONE_REQUIRE_ORIGIN=true hard-409s (warn-first ratchet). Was: **`/done` verifies the SHA locally only
      — no origin-push guarantee** — `verify.py` runs `git show` in the slot worktree (never `ls-remote`/merge-base vs
      `origin/live-defi-rollout`); sentinel SHAs (`audit-*`, `no-code-change`…) skip verification entirely;
      dirty-tree/plan-flip/scope checks are warnings, not blocks. A worker whose quickmerge silently failed
      (auth/network) still marks the task done with a local-only commit. Add an origin-existence check (warn → block
      ratchet). Repo: agent-orchestrator (`server/verify.py` + `server/routes/slots_worker.py`).
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). tmux_spawn forwards the backend's
      WORKSPACE_ROOT into the spawn shell (exported before the account env file so it stays overridable). Was: **Spawned
      workers get no `WORKSPACE_ROOT`** — boot prompts carry `${WORKSPACE_ROOT}/...` paths but
      `tmux_spawn._start_session` sources only the account env file; the worker's shell expands it EMPTY (live repro:
      worker `cd`'d to a wrong guessed path, self-recovered after 2 probe commands). Export `WORKSPACE_ROOT` (+ any
      boot-prompt-referenced env) in the spawn `bash_cmd`. Repo: agent-orchestrator (`server/tmux_spawn.py`).
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). GET /api/blocked/stats (unanswered + oldest
      age, answered_by split, median/p90 time-to-answer, repeat offenders) + BlockedPanel chip (N/M by main · median
      TTA) computed client-side. Was: **Blocked-queue telemetry missing** — `slot_blocked`/`blocked_answered` land in
      `activity_log` but nothing aggregates: no blocks-per-task counter, no repeated-block alert, no time-to-answer
      metric (now doubly relevant as the MainAgentKeeper SLA measure: main-answered vs operator-answered vs
      unanswered-age). Small rollup endpoint + dashboard chip. Repo: agent-orchestrator.
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). Watchdog Trigger-4: same task >4h + (ctx
      ≥80% OR ≥3 compactions) → context_burn_suspected activity + Slack page, deduped per (slot,task); kill opt-in via
      ORCHESTRATOR_CONTEXT_BURN_KILL (flag-first until fleet mileage). Was: **Execution-vs-context-burn detector
      missing** — nothing correlates time-on-task + context_pct / compactions with pushed output; a worker can heartbeat
      for hours with zero commits and no flag. Rule sketch:
      `dispatched > 4 h AND no done_sha AND (context_pressure high OR compactions climbing) → flag + respawn`. All
      inputs already in state.db (`slots.context_used_pct`, `compactions`, `tasks.dispatched_at`). Repo:
      agent-orchestrator (`server/worker_liveness_watchdog.py` or sibling check).
- [x] ✅ [CODE] P3. DONE 2026-06-12 — agent-orchestrator@c247b6b (one remediation unit: 13 new tests in
      tests/test_e2e_findings_remediation.py; QG green; quickmerge --agent). Dev default flipped to :8765
      (VITE_BACKEND_PORT still overrides). Was: **Orchestrator dashboard dev default still points at retired :8026** —
      `dashboard/src/App.tsx:73` (`devPort ?? "8026"`; backend binds 8765 since the port migration) → fresh local run =
      login "Failed to fetch" until `VITE_BACKEND_PORT=8765`. Flip the default. Repo: agent-orchestrator
      (`dashboard/src/App.tsx`).

- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@1c9b8c1 (4 tests; QG green; quickmerge --agent). **VM-test
      isolation: `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` strict per-VM plan scoping** (operator ask 2026-06-12 — "the test
      VM must not pick up any existing plan by default"). With the flag set, regen ingests ONLY plans whose
      `assigned_vm` EXACTLY matches `ORCHESTRATOR_VM_ID` — the "no assigned_vm ⇒ global, every VM takes it" fallback is
      disabled (a fresh vm-id alone still leaked the global plans, incl. `task_template.md`'s example todos), and with
      no vm_id configured strict mode ingests NOTHING (fail-closed). Env-resolved inside `regen()` so the PlanRegenLoop,
      the manual `POST /api/backlog/regen`, and the CLI all inherit it. The e2e test VM runs
      `ORCHESTRATOR_VM_ID=vm-e2e-test`
  - this flag → guaranteed-empty backlog until a plan explicitly targets it. Repo: agent-orchestrator.

#### VM-from-scratch e2e (operator direction 2026-06-12 — fresh instance, zero pre-allocated resources, fully scripted + reusable)

Current provisioning reality (surveyed 2026-06-12): the 2026-05-22 epic fleet was launched from BARE Ubuntu 24.04 via
EC2 user-data (apt deps → AWS CLI → `GH_PAT` from Secrets Manager → clone agent-orchestrator on LDR →
`bootstrap_vm.sh --role epic` does repos/creds/systemd/health/self-registration end-to-end) — but the user-data
generator was never checked in (recovered from instance `i-003be935f72c13d51`'s userData). IAM
(`uts-orchestrator-epic`), the creds bucket (`s3://uts-orchestrator-creds-427895769566` — accounts.json + setup-token
env files, CredsEnvPoller-synced), Secrets Manager (GH_PAT, ORCHESTRATOR_ENV_LOCAL), and a Packer warm-AMI
(`deployment-service/packer/agent-orchestrator/`) all exist. Worker VMs are LONG-RUNNING instances.

- [x] ✅ [SCRIPT] P1. DONE 2026-06-12 — deployment-service@1b56a37 (QG green; quickmerge --agent).
      `scripts/vm/launch-orchestrator-worker-vm.sh` + `LC_AWS_SHUTDOWN_BEHAVIOR=stop` lib override (long-running workers
      must not terminate-and-wipe on in-VM shutdown). Was: **Reusable worker-VM launcher** —
      `deployment-service/scripts/vm/launch-orchestrator-worker-vm.sh` (script-homes: provision/launch →
      deployment-service; reuses `lib/aws_ec2_launch_lib.sh`): bare Ubuntu 24.04 (SSM-resolved AMI, `AMI_ID` override
      for the Packer warm image) + the PROVEN 2026-05-22 user-data shape, parameterised
      `--name/--vm-id/--role/--slots/--instance-type/--env KEY=VAL...` (env passthrough → the new bootstrap override
      hook below, so isolation vars are live BEFORE the backend starts); reuses `uts-orchestrator-epic` instance
      profile + sg-0080310387e84f613 + subnet-fc09eca6 (all env-overridable); tags Name/vm-id/role/operator/lifecycle;
      prints instance-id + IP + log-tail hint. Repo: deployment-service.
- [x] ✅ [SCRIPT] P1. DONE 2026-06-12 — agent-orchestrator@878274b (QG green; quickmerge --agent). `bootstrap_vm.sh`
      5b-extra: `ORCHESTRATOR_EXTRA_ENV` newline KEY=VAL block upserted into `.env.local` LAST (overrides beat defaults)
      before the service starts. Was: **Bootstrap env-override hook** — `bootstrap_vm.sh` consumes
      `ORCHESTRATOR_EXTRA_ENV` (newline KEY=VAL block, user-data-injectable) into `.env.local` BEFORE the orchestrator
      service starts, so a test VM boots directly with `ORCHESTRATOR_VM_ID=vm-e2e-test` +
      `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true` (+ `ORCHESTRATOR_DONE_REQUIRE_ORIGIN=true` to exercise the new ratchet)
      — no SSH-and-restart step. Repo: agent-orchestrator.
- [x] ✅ [TEST] P1. DONE 2026-06-12 — agent-orchestrator@878274b (QG green; quickmerge --agent).
      `scripts/verify_vm_e2e.sh <instance-id>`: SSM-driven 7-check PASS/FAIL table (running+SSM, bootstrap marker
      ≤15min, :8765 live health, pm-pull.timer, orch-agent-main ≤3min, strict-scoping empty backlog, accounts ≥1);
      bounded waits + explicit verdict on every path. Live-run evidence lands with the launch todo below. Was:
      **Post-launch verification harness** — `agent-orchestrator/scripts/verify_vm_e2e.sh <instance-id|ip>` (laptop-run;
      SSM/ssh): waits ≤10 min for `:8765` health, then asserts with PASS/FAIL table — backend Ready (live mode),
      `pm-pull.timer` enabled + last pull LDR (the STEP 7.5c verifier), MainAgentKeeper spawned `orch-agent-main` (real
      setup-token auth from the creds bucket — NOT the local-credentials hack), backlog EMPTY under strict scoping (the
      isolation proof), AutoSpawn/Watchdog/PlanRegen loops started, self-registration reported. Composes with the
      no-fire-and-forget T+10min rule. Repo: agent-orchestrator.
- [x] ✅ [TEST] P1. DONE 2026-06-12 — PASSED on i-086e8787dddda52d6, full loop in 68 s. Trail (activity stream, UTC):
      08:53:18 regen scanned 31 plans → ingested ONLY the local `assigned_vm: vm-e2e-test` test plan (strict scoping
      held, 1 task); 08:54:49 AutoSpawnLoop spawned slot-1 (`checked=1 spawned=1 skips={}`, account sub-b-iggy2london,
      real setup-token); 08:55:13 worker /boot → task auto-assigned ("tier=1 priority=20"); 08:55:53 /progress; 08:55:57
      /done with correct audit evidence (74 Python files under server/; top-3 by lines incl.
      regen_backlog_from_plan.py@917). Cold-start note: a FRESH VM has zero SlotRows and AutoSpawn only iterates
      existing rows — slot rows were configured once via `upsert_slot` (worktree/branch/operator), the documented
      cold-start step; thereafter the loop is fully autonomous. Bugs found+fixed during the run: `.tabs/` slot clones
      were ROOT-owned (bootstrap user-data runs as root, chowns main checkouts but not .tabs → git "dubious ownership"
      kills every worker write; fixed live + bootstrap now chowns .tabs — agent-orchestrator@27b5212); /done origin-gate
      bypass via non-revision sha — a NON-SENTINEL sha that fails `git show` slid past the DONE_REQUIRE_ORIGIN gate
      (verified=False → on_origin never computed): fixed in the SAME unit @27b5212 (M9b: `sha_unverifiable` warning
      always + 409 under strict env; `read-only*` added to the sentinel prefixes so honest no-commit vocabulary
      short-circuits as applicable=False; +3 tests). @27b5212 deployed + healthy on the test VM. Test plan removed +
      regen-pruned after (backlog back to 0). Was: **Plan-pickup e2e on the VM**. Repo: agent-orchestrator.
- [x] ✅ [TEST] P1. DONE 2026-06-12 — PASSED on i-086e8787dddda52d6. Fired `POST /api/escalate`
      (`wall_type=ldr_qg_failure`, `X-Orchestrator-Secret` auth) exactly as the CI watcher does, with a read-only DRILL
      context. Trail: 08:58:34 `escalation_dispatch_initiated` (wall validated against WALL_TYPES, escalate template
      selected) → free slot 2 picked + headroom account sub-b → 08:58:39 `escalation_dispatched` (orch-slot-2 spawned) →
      08:59:02 worker /progress "Read RULES.md; starting drill" → 08:59:07 reported worktree HEAD 88c53e2 (current LDR
      tip — worktree freshness proven) → 08:59:24 worker pinged the AUTHORING SLOT (slot-5) "DRILL COMPLETE"; watchdog
      reaped the finished session 09:00:19. Semantics note: escalation workers are NOT backlog tasks — /done returns
      task-not-found by design; the completion signal is the authoring-slot ping + escalation activity events. GAP FOUND
      (filed below as P1): the VM's `.env.local` had NO `ORCHESTRATOR_INTERNAL_SECRET` (not in the
      ORCHESTRATOR_ENV_LOCAL SM secret) → auth fell back to an ephemeral generated secret → real CI escalations to a
      bootstrap-launched VM would 401; the drill used a VM-local test secret. Was: **CI-failure → escalation → worker
      assignment e2e** — the operator's target loop, now proven minus the fleet-secret distribution. Repo:
      agent-orchestrator.
- [x] ✅ [INFRA] P2. DONE 2026-06-12 — deployment-service@1b56a37+5655576 (same unit as the launcher): instance carries
      `lifecycle=e2e-test` tag; launcher has `--stop <id>` / `--terminate <id>` teardown helpers;
      `LC_AWS_SHUTDOWN_BEHAVIOR=stop` keeps long-running workers' disks on OS shutdown. Was: **Lifecycle + teardown**.
      Repo: deployment-service.
- [x] ✅ [CREDS] P1. **DONE 2026-06-12** — `ORCHESTRATOR_INTERNAL_SECRET` (vm-0's exact value, sha12-verified identical)
      upserted into the `ORCHESTRATOR_ENV_LOCAL` Secret Manager blob in **GCP (version 2) + AWS (`4c52ae7f`)**;
      bootstrap already writes the blob → `.env.local`, so new VMs now carry it (`/api/escalate` + central→worker proxy
      authenticate fleet-wide). prod vm-0 untouched (read-only via SSM; live auth preserved — SM change only affects
      future bootstraps). Was: **BLOCKED-CREDENTIALS** (CREDENTIAL APPROVAL REQUEST:
      `ikenna_orchestrator/pings/slot_1.md`) — the `ORCHESTRATOR_ENV_LOCAL` Secret Manager value carries only
      JWT_SECRET/USERS_JSON/MODE/TELEGRAM keys (verified 2026-06-12); `auth._load_internal_secret()` then falls back to
      an EPHEMERAL generated secret, so `/api/escalate` + the central→worker proxy 401 every caller on a fresh VM (prod
      vm-0 works only because it is hand-wired). Operator ask: append the fleet
      `ORCHESTRATOR_INTERNAL_SECRET=<value     from prod vm-0's .env.local>` line to the `ORCHESTRATOR_ENV_LOCAL` secret
      in BOTH AWS SM + GCP SM — bootstrap already propagates the whole secret to .env.local, so no code change is needed
      (bootstrap now loud-warns when the key is absent). Found 2026-06-12 escalation e2e. Repo: agent-orchestrator (+
      operator SM update). **CREDENTIAL APPROVAL REQUEST** filed: `ikenna_orchestrator/pings/slot_1.md` (operator:
      append `ORCHESTRATOR_INTERNAL_SECRET` to the `ORCHESTRATOR_ENV_LOCAL` secret in AWS SM + GCP SM).

- [x] ✅ [INFRA] P1. **vm-0 worker-QG memory guardrail** — 2026-06-12 13:43 UTC the central VM (i-0c9b283b31d6b5ca7)
      OOM'd: 16G swap exhausted (156kB free), ≥2 pythons at ~10-11GB total-vm each (pytest/QG class) from
      CIReconcile-dispatched fixer workers grinding billing-wall-doomed LDR QGs (13:33 tick: "2 failing
      (trading-agent-service,e2e-testing) … no capacity" — slots already saturated); kernel killed the ubuntu session
      (systemd/sd-pam UID 1000) + a 4.1GB python; operator rebooted 14:36; MainAgentKeeper re-created orch-agent-main at
      14:36:33 and AutoSpawn respawned slots 1-2 at 14:43 (self-heal verified). Same class as the 2026-05-29
      central-host OOM (the reason bootstrap provisions the 16G swapfile). Guardrails to ship: (a) enforce the
      qg-host-governor token floor (≤2 concurrent full QGs) for ORCHESTRATOR-SPAWNED workers on VMs — it exists for
      laptop slots but VM escalation workers bypass it; (b) systemd `MemoryHigh=`/`MemoryMax=` on the worker scope (or
      per-spawn ulimit) so a runaway QG python is killed before it takes the user session; (c) composes with the
      CIReconcile fleet-red breaker P0 already tracked in `issues/github_actions_billing_wall_2026_06_11.md` (stop
      dispatching doomed QG grinds — removes the load source). Found 2026-06-12 post-incident forensics (journalctl -b
      -1). Repo: agent-orchestrator (+ PM qg-host-governor). — DONE 2026-06-15. **(a)** qg-host-governor floor already
      landed agent-orchestrator@0ef02b3 (`QG_HOST_CONCURRENCY=1` in bootstrap `.env.local` → inherited by the backend
      via systemd `EnvironmentFile` + by spawned workers, since the `Popen` spawn passes no `env=`). **(b)** per-worker
      cgroup cap shipped agent-orchestrator@8e8415e: `tmux_spawn._worker_mem_scope_prefix()` wraps each worker's
      `claude` (+ its QG/pytest children) in a transient `systemd-run --user --scope -p MemoryMax -p MemorySwapMax` —
      the spawn `Popen(start_new_session=True)` detaches workers from `orchestrator.service`'s MemoryMax cgroup, and the
      governor only serialises the heavy TEST phase, NOT the ~5GB UTL import spike that precedes the token acquire (the
      real OOM driver). Opt-in + graceful: no-op unless `ORCHESTRATOR_WORKER_MEMORY_MAX` is set AND a cached
      `systemd-run --user` probe passes (laptop/no-linger hosts fall back to an uncapped spawn + a one-line warn — never
      breaks spawning). bootstrap arms `10G`/`2G` on the dispatch host (`loginctl enable-linger` already runs → the
      `--user` manager exists). Reactive belt **earlyoom** (SIGTERM biggest hog at ≤10% free) already landed
      agent-orchestrator@cd6b4df. **(c)** CIReconcile fleet-red breaker stays tracked in
      `issues/github_actions_billing_wall_2026_06_11.md` (the load SOURCE — separate P0). Verify: AO `quality-gates.sh`
      green (basedpyright 0/0, 603 pass incl. 6 new memory-cap tests) + `bash -n` bootstrap. **Continuous
      verification**: confirm on the next VM bootstrap that the worker pane runs under a `systemd-run --user --scope`
      cgroup (`systemctl --user status` shows the transient scope) and a runaway QG is OOM-killed inside its scope, not
      host-wide (probe-gating makes the code safe regardless).

- [ ] [CREDS] P0. **Finish vm-0 SM wiring: align the blob's stale `ORCHESTRATOR_JWT_SECRET` (SM ← vm-0), operator
      one-liner.** The wiring tooling is DONE — agent-orchestrator@4c558a8 `scripts/refresh_env_from_sm.sh` (UPSERT from
      the `ORCHESTRATOR_ENV_LOCAL` blob for long-lived hosts: SM keys win on drift, the 15+ local-only keys are never
      clobbered, backup-before-write, dry-run default, values never printed; component-verified + deployed to vm-0).
      Live dry-run on vm-0 (2026-06-12 15:1x UTC): 6 keep + **1 REPLACE — the SM blob's `ORCHESTRATOR_JWT_SECRET`
      differs from vm-0's LIVE value** (the blob's copy predates; vm-0's is the one operator logins use, so the fix
      direction is SM ← vm-0, NOT apply-to-host). Agent-side secret writes are permission-blocked by design.

      **STAGED 2026-08-08 (operator ruling, ao round-5 apply session item 22): "Operator will run it - give exact
                      staged commands."** Verified against the live `refresh_env_from_sm.sh` (its own `fetch_blob()`/usage header)
                      before writing this, not guessed. Run entirely on vm-0 (`i-0c9b283b31d6b5ca7`, EIP 13.113.200.22) as one pass:
                      ```bash
                      cd "${WORKSPACE_ROOT}/agent-orchestrator"
                      # 1. Fetch the current SM blob (same two-cloud fallback refresh_env_from_sm.sh itself uses):
                      TMPFILE="$(mktemp)"; chmod 600 "$TMPFILE"
                      trap 'rm -f "$TMPFILE" "${TMPFILE}.new"' EXIT
                      { aws secretsmanager get-secret-value --secret-id ORCHESTRATOR_ENV_LOCAL --query SecretString --output text 2>/dev/null \
                          || gcloud secrets versions access latest --secret=ORCHESTRATOR_ENV_LOCAL --project=central-element-323112; \
                      } > "$TMPFILE"
                      # 2. Replace the blob's ORCHESTRATOR_JWT_SECRET line with vm-0's own LIVE .env.local value (the direction this
                      #    todo requires -- SM catches up to vm-0, not the reverse):
                      LIVE_JWT_LINE="$(grep '^ORCHESTRATOR_JWT_SECRET=' .env.local)"
                      grep -v '^ORCHESTRATOR_JWT_SECRET=' "$TMPFILE" > "${TMPFILE}.new"
                      echo "$LIVE_JWT_LINE" >> "${TMPFILE}.new"
                      mv "${TMPFILE}.new" "$TMPFILE"
                      # 3. Write back to BOTH clouds (both are kept in sync per the blob's own two-cloud design):
                      aws secretsmanager put-secret-value --secret-id ORCHESTRATOR_ENV_LOCAL --secret-string "file://$TMPFILE"
                      gcloud secrets versions add ORCHESTRATOR_ENV_LOCAL --project=central-element-323112 --data-file="$TMPFILE"
                      # 4. Verify (dry-run, no writes) -- expect ALL keys including JWT to report "keep" now that SM matches vm-0:
                      bash scripts/refresh_env_from_sm.sh
                      ```
                      The `trap` removes the temp file on exit regardless of success/failure. Step 4's dry-run output is the
                      done-when check: 7x keep / "in sync", zero REPLACE lines. Repo: agent-orchestrator (+ operator SM write).

**Operator-concerns verification session (2026-06-12 PM, on the live vm-e2e-test):** three concerns checked +
e2e-tested; two new live bugs found + fixed in the process (agent-orchestrator@094f691 + @1a0bea0, both deployed to the
VM).

1. **Task→agent matching (model / effort / thinking) — VERIFIED + e2e-PROVEN.** Chain: plan frontmatter
   `model_tier: sonnet-doable|opus-required` + `thinking_tier: max|high|medium|mechanical` → regen stamps
   model/effort/thinking on the backlog task → AutoSpawn `_top_queued_task_params` picks the top queued task's params →
   claude CLI flags `--model/--effort/--max-thinking-tokens 31999`. Live proof: a `thinking_tier: high` plan produced a
   task with `effort: high, thinking: on` (backlog.yaml) and a FRESH AutoSpawn spawn with
   `--model sonnet --effort high --max-thinking-tokens 31999` (journal 10:57:10). **Policy change shipped @094f691
   (operator 2026-06-12): thinking is the PREFERRED mode** — `high` now maps to thinking ON (was off), the spawn default
   is ON when neither task nor slot opts out, and `thinking_tier: mechanical|off|none` is the explicit opt-out for truly
   mechanical work. Context-burn monitoring is the per-task RUNTIME safety net (watchdog Trigger-4: >4h on one task +
   ctx≥80% or ≥3 compactions → `context_burn_suspected` + Slack; kill opt-in via ORCHESTRATOR_CONTEXT_BURN_KILL) —
   complexity ROUTING stays a plan-authoring concern, monitoring stays runtime; no per-task babysitting needed. Known
   limitation observed live: tier params apply at SPAWN — an already-running parked worker that picks up a task keeps
   its own flags (mixed-tier queue note in `_top_queued_task_params`; its /done honestly reported
   `effort=medium thinking=off` for a high/on task).
2. **Blocked-question → main agent — PROVEN on real infra.** Posted a worker /blocked drill (BLK-bbe34f72, "pip vs uv
   pip install") → the keeper-spawned main agent answered it autonomously in **40.4 s**
   (`/api/blocked/stats: answered_by {"main": 1}`, journal `POST /api/blocked/BLK-bbe34f72/answer 200`). Genuinely-
   operator questions (spend/creds/destructive/scope) stay deferred per agents/main.md STEP 2.5.
3. **tmux session longevity — PROVEN by design + empirically.** `orchestrator.service` has `KillMode=process`
   (root-caused 2026-05-20: only uvicorn dies on restart; tmux + claude sessions survive despite living in the service
   cgroup). Empirical: `orch-agent-main` created 06:48:33 survived FIVE backend restarts today (DR env, port migration,
   @27b5212, @094f691, @1a0bea0 deploys).

Live bugs found during this verification (both fixed):

- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@094f691 (idle-reap guard) + @1a0bea0 (warm-window refinement),
      QG green, deployed. **WorkerLivenessKicker idle respawn/burn loop**: a worker that FINISHED its task parks at the
      claude prompt → pane classifies "frozen" → kicker killed + auto-respawned it into an EMPTY queue → fresh worker
      idles → freezes → respawns… observed live ~19-min cycles on slots 1+2 (each a full claude boot on a real account).
      Fix: `maybe_auto_respawn_stuck_slot` now reaps (kill session, slot→idle, `slot_idle_session_reaped` event) instead
      of respawning when `current_task is None` AND zero queued+undispatched tasks — respawn is for MID-TASK stuck
      workers; AutoSpawnLoop (queue>0-gated) is the only spawn authority for new work. Refinement @1a0bea0: the reap
      respects the 15-min stuck threshold (warm window) — observed live that a parked worker's self-poll heartbeat picks
      up the NEXT task boot-free (`trigger: heartbeat`), so freshly-done sessions are kept warm; only sessions parked
      past the threshold with nothing to do are reaped. 4 unit tests pin reap/warm/in-flight/queued paths.
- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@1a0bea0 (bootstrap upsert). **Every bootstrap VM silently
      became a second CI-responder**: CIReconcileLoop is ON by default in the backend, so within 2 min of the @094f691
      restart the TEST VM autonomously dispatched an `ldr_qg_failure` fixer for market-data-processing-service — a repo
      it has no clone of — duplicating vm-0's CI-responder mandate (per-VM cooldowns don't dedup across the fleet; the 6
      "failing" LDR repos are likely the 2026-06-12 billing wall, unfixable by a worker). Positive side: this proved the
      DETECTION→escalation→spawn loop fires fully autonomously (our earlier drill only proved the POST→spawn half). Fix:
      bootstrap upserts `ORCHESTRATOR_CI_RECONCILE_INTERVAL_SECONDS=0`; the ONE designated responder VM (vm-0)
      re-enables in its .env.local; ORCHESTRATOR_EXTRA_ENV overrides at launch for a deliberate responder. The test VM's
      fixer was killed before it acted; CIReconcile disabled there.
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@3586c89 (QG green; deployed to vm-e2e-test). `_run_one_tick`
      now computes `spawn_budget = _queued_undispatched_count(session)` once per tick and skips further slots with
      `queue_satisfied` once `slots_spawned` reaches it — one queued task warrants one spawn. 2 unit tests pin both
      directions (2 slots/1 task → 1 spawn + queue_satisfied skip; 2 slots/2 tasks → 2 spawns). Live-spawn verification
      DEFERRED-BY-HEADROOM (not a gap in the fix): at test time all 3 accounts were at/over the AutoSpawn ceilings
      (sub-a 95% weekly, sub-b exactly 80% = ceiling, sub-c rate-limited to 19:00) so the loop correctly refused to
      spawn at all — the headroom guard working as designed; the cap rides the identical tick path the morning's live
      spawns used and will be observable on the next real dispatch (`skips={'queue_satisfied': N}` in the tick log).
      BONUS live proof captured during this work: the @1a0bea0 warm-window idle-reap fired ORGANICALLY — journal
      11:13:52 `idle-reap slot 1: session orch-slot-1 reaped; no respawn (empty queue)`, ~15 min after its task
      finished, no respawn after — the burn loop is dead under production conditions. Was: **AutoSpawn over-spawns: N
      idle slots × 1 queued task → N workers** (tick 10:57:10 `checked=2 spawned=2` for one task). Repo:
      agent-orchestrator. Found 2026-06-12 concerns-verification run.
- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@42223e5 (QG green 578 passed; quickmerge --agent from slot-2) +
      LIVE-VERIFIED full lifecycle on vm-e2e-test: dropped an `[OPERATOR]` test todo → regen ingested it as
      `status=blocked, dispatched_to=None` + synthetic `BLK-op-e2e_operator_gate_test-001` (slot 0) in the operator
      queue, ZERO spawn; flipped the checkbox → regen prune GC'd BOTH (tasks=0, blocked entries=0, backlog 0).
      Implementation (option B, operator-chosen): `regen` marks `[OPERATOR]`-tagged todos `operator_gated`;
      `sync_backlog_to_db` inserts blocked (dispatch/autospawn only consider "queued" → structurally unspawnable) +
      files the synthetic blocked-queue entry whose question text forbids main-agent auto-answer; prune GC predicate
      extended queued→{queued,blocked} + deletes slot-0 synthetic entries alongside (real worker questions slot_id>0
      untouched; legacy DBs without blocked_queue tolerated). 3 new tests pin ingest/sync/prune. Was:
      **[OPERATOR]-tagged todos become dispatchable tasks** — vm-planning slot-5 (11:44 UTC) burned a real worker boot
      to ask flip-or-leave. Repo: agent-orchestrator. Found 2026-06-12 Slack-alert triage.
- [ ] [DESIGN] P0. **Dirty-worktree resolution policy (Ikenna, Slack 2026-06-12 — the next-phase "no dirty worktrees"
      flow)**: orchestrator directs a worker on a dirty slot tree to (1) run `quality-gates.sh` — green → quickmerge the
      WIP per the active plans; (2) red but easily fixable → fix, re-QG, quickmerge; (3) not easily fixable → hand to
      the operator as a GENUINELY dirty tree (operator judges useful-or-not); (4) operator says not useful → worker
      hard-resets the slot from remote LDR (operator-sanctioned reset — the only sanctioned discard path). Composes with
      the existing liveness-gated machinery: `resolve_dirty_state` (FM2/FM3/FM8 orphan-WIP inherit) already auto-commits
      DEAD predecessors' WIP; a LIVE operator session's WIP stays protected (FM8) — this policy covers the in-between
      (committed-able but unverified WIP). Needs: worker prompt template + an orchestrator dispatch hook + plan todos
      per repo surface. Repo: agent-orchestrator. Provenance: Ikenna Slack reply on BLK (central-VM migration),
      2026-06-12.

**VM-from-scratch e2e LIVE RUN (2026-06-12, i-086e8787dddda52d6 / agent-orch-vm-e2e-test-20260612, 18.183.31.192, LEFT
RUNNING):** launched from bare Ubuntu via the new launcher; **bootstrap completed in 219 s** (console-verified); all 3
isolation env overrides landed via the EXTRA_ENV hook; pm-pull.timer enabled+active (single-installer model proven on
real systemd); **MainAgentKeeper spawned the main agent 3 s after backend start with the real `sub-a-ikenna`
setup-token** and it polls /api/state every 60 s (STEP 2.5 sweep live); 3 fleet accounts synced from the creds bucket;
strict scoping ingested 0 plan tasks; **backlog 0 after the prune + ghost-fix below**. Launch findings fixed in-flight:
launcher guard fn name (deployment-service@5655576) + the on_regen ghost-backlog fix (agent-orchestrator@7b85fc5,
deployed to the VM + verified). Remaining live-run findings:

- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@7b85fc5 (regression test; QG green; deployed + verified on
      vm-e2e-test). **on_regen refresh skipped prune-only ticks** — `server.py` guard was `new_tasks == 0` so a tick
      that PRUNED (36 stale tasks, yaml+db both 0) never refreshed `_state["backlog"]` → /api/backlog served ghosts
      until the next ADDITIVE tick. Dispatch was safe (db-status filtered) but the display lied. Guard now
      `new_tasks == 0 and pruned_yaml == 0`.
- [x] ✅ [INFRA] P1. DONE 2026-06-12 — agent-orchestrator@f871119 (QG green; quickmerge --agent) + sg swap
      (sgr-0cecb1d4d0536099f adds 8765/172.31.0.0/16; 8026 rule revoked) + deployed/verified on vm-e2e-test (8765
      serving, 8026 dead, main agent respawned). Canonical = 8765 per CLAUDE.md; fixed while ZERO live 8026 workers
      existed (epic fleet stopped) so no migration window. Surfaces: orchestrator.service ExecStart (the template every
      fresh worker inherits — the root cause), orchestrator-demo.service + Dockerfile comments, backends.json
      url/private_url (15 entries). Was: **Worker-VM port is 8026 in REALITY, 8765 in the DOCS** —
      `install-orchestrator-service.sh`'s systemd unit binds uvicorn :8026 on a fresh worker; sg-0080310387e84f613 (22
      public + 8026 in-VPC only) and `backends.json` (:8026 URLs) are consistent with the TEMPLATE, while
      CLAUDE.md/codex say "8026 retired, 8765 canonical" (true only on the planning VM). Decide the canonical worker
      port, then move template + sg + backends.json + docs in ONE change. Repo: agent-orchestrator (+ codex). Found
      2026-06-12 live run.
- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@0780554 (QG green 523 passed; quickmerge --agent). All 3 parts:
      (1) Step 5c fetch loop now `accounts.json` only with a never-re-add comment (`load_backlog()` returns an empty
      `Backlog()` on a missing file — verified — so the seed was always redundant-or-stale); (2) 5b-append upserts
      `ORCHESTRATOR_REGEN_PRUNE_STALE=true` (code now matches the CLAUDE.md fleet-default claim); (3) stale
      `config/backlog.yaml` (40KB, 2026-05-22 — the 36-ghost-task source) DELETED from
      s3://uts-orchestrator-creds-427895769566/config/ (only accounts.json remains). Was: **Bootstrap S3 `backlog.yaml`
      seed contradicts the regen-authoritative model** — Step 5c copies a stale fleet backlog into a fresh VM, bypassing
      regen scoping entirely; AND bootstrap never upserts PRUNE_STALE so the seed persists. Repo: agent-orchestrator.
      Found 2026-06-12 live run (vm-e2e-test booted with 36 foreign tasks).
- [x] ✅ [CODE] P2. DONE 2026-06-12 — agent-orchestrator@0780554 (same unit). SSM probe now captures stderr:
      `AccessDenied`/`UnauthorizedOperation` → SKIP "caller IAM denied — NOT a VM fault" (breaks the 5-min loop
      immediately — the denial is deterministic); genuine not-registered stays FAIL; BOTH paths fall back to SSH
      (`vm_run` transport dispatcher; `ssh_run` pipes commands to `sudo bash -s` so quoting/run-as-root semantics match
      ssm_run; `--ssh-key` flag, default `~/.ssh/agent-orchestrator-key`) and complete all 7 checks instead of exiting
      blind. LIVE-VERIFIED on i-086e8787dddda52d6 from this harsh-worker host (the exact previously-misreported
      scenario): SSM online SKIP (caller IAM denied) → SSH fallback → all remaining checks PASS, VERDICT: PASS, exit 0.
      Was: **verify_vm_e2e.sh: distinguish caller-side IAM denial from agent-not-registered** — the SSM probe swallowed
      `AccessDeniedException` into "agent never registered" (misleading FAIL). Repo: agent-orchestrator. Found
      2026-06-12 live run.
- [x] ✅ [CODE] P1. DONE 2026-06-12 — agent-orchestrator@88c53e2 (QG green; quickmerge --agent) + bucket ops +
      LIVE-VERIFIED round-trip on vm-e2e-test. Discovery correction during impl: the bucket
      `uts-orchestrator-state-427895769566` ALREADY EXISTS and the prod orchestrator VM (vm-0) is actively writing to it
      (state.json every 30 min, sqlite 6h — hand-wired env), so the gap was bootstrap-launched VMs only, exactly as
      filed. Shipped: (1) bootstrap 5b-append upserts `ORCHESTRATOR_S3_BUCKET=uts-orchestrator-state-427895769566` (AWS)
      / `ORCHESTRATOR_GCS_BUCKET=agent-orchestrator-state-prod` (GCP); (2) all 4 writers in `gcs_sync.py` now key by
      `_vm_key_segment()` (`snapshots/<vm_id>/<date>/state_<ts>.json` + `backups/sqlite/<vm_id>/<date>/<mode>_<ts>.db`;
      no vm_id → `unattributed`) + 3 new moto tests pin the layout; (3) `restore_from_gcs.sh` gained S3 transport
      (`--s3-bucket`/$ORCHESTRATOR_S3_BUCKET; transport-agnostic `latest_blob_under`/`fetch_blob`) + `--vm-id` scoping
      (without it a multi-VM flat listing path-sorts by vm name, not recency — now warned); (4) PAB + 30d lifecycle
      applied on snapshots/ + backups/ prefixes; test-VM instance-profile list+put probed OK. Live proof: restarted
      vm-e2e-test backend with the env → `POST /api/snapshot` landed
      `s3://…/snapshots/vm-e2e-test/2026-06-12/state_20260612T084615Z.json`, and
      `restore_from_gcs.sh --json-only     --dry-run` on the VM picked exactly that object via S3 + vm_id scoping. NOTE:
      prod vm-0 still writes flat keys until it picks up @88c53e2 on its normal update cadence (restore script reads
      both layouts; no forced prod restart). Was: **State-DB DR backup is silently OFF on every fleet VM — bootstrap
      never sets the snapshot bucket envs**; the deleted creds-bucket `config/backlog.yaml` seed was NOT part of the DR
      path (backlog resumes via git/PlanRegenLoop, regen-authoritative). Found 2026-06-12 while answering the
      backup-vs-seed design question.
- [x] ✅ [CREDS] P0. **RESOLVED 2026-08-08 (operator ruling, ao round-5 apply session item 23 —
      /plans/active/issues/ao_round5_apply_session_operator_qa_index_2026_08_08.md): "Approve the grant."** Was:
      BLOCKED-CREDENTIALS — `harsh-worker` IAM lacks SSM read/run (`ssm:GetParameters` broke the launcher's Ubuntu-AMI
      resolution — worked around via `AMI_ID=ami-0bf052f8a9dd8bf42`; `ssm:DescribeInstanceInformation`/
      `ssm:SendCommand` broke the verify harness — worked around via SSH). Self-granted live (the `admin_od` AWS
      identity has IAM admin rights, confirmed): inline policy `orchestrator-fleet-ssm-access` attached to
      `harsh-worker` (`AmazonSSMReadOnlyAccess`'s exact permission set replicated inline — direct attach hit the
      10-managed-policy-per-user quota — plus `ssm:SendCommand` scoped to
      `arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7`, the orchestrator VM, the whole "fleet"
      under the current single-VM architecture). Verified live via `aws iam get-user-policy`. CREDENTIAL APPROVAL
      REQUEST closed → `ikenna_orchestrator/pings/slot_5.md`. AMI/SSH workarounds can now be retired from
      `verify_vm_e2e.sh` as a follow-up (not done this session — out of apply-session scope).

Sandbox-only caveat (NOT a fleet bug — do not chase): repeated worker-session deaths during the local run were caused by
sharing the laptop's `~/.claude/.credentials.json` across concurrent claude sessions (refresh-token rotation conflict)
because no setup-token exists on this host — exactly the failure mode CLAUDE.md § "accounts auth via setup-tokens only"
bans. Fleet VMs (setup-token env files) are unaffected.

## Deferred work — migrated to:

- Live-spawn verification (DEFERRED-BY-HEADROOM, line ~337): N/A — no migration. Not a gap in the fix (code + unit tests
  shipped); live observation is expected to surface naturally on the next real dispatch once any account has headroom
  (`skips={'queue_satisfied': N}` in the tick log is the confirming signal).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — all 3 open todos are operator-gated and already ruled so in
  `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred list: two `[CREDS]` secret/IAM
  writes (`ORCHESTRATOR_JWT_SECRET` SM alignment, which the doc itself states is 'permission-blocked by design' for
  agents; and a `harsh-worker` IAM grant with no self-service path) plus one `[DESIGN]` dirty-worktree policy whose step
  4 is an operator-sanctioned hard reset.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid —
  re-verified all 3 remaining open items against live doc text: a permission-blocked-by-design SM secret write, an
  operator-sanctioned dirty-worktree reset policy, and a `BLOCKED-CREDENTIALS`-tagged IAM grant with a filed approval
  request. All three remain genuinely operator-gated, no change since the 2026-07-30 verdict.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- was epic+plan-only; added the 3 real source files
  behind the 3 still-open P0 items (SM secret sync script, dirty-worktree resolver, VM bootstrap script).

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: populated/refreshed context_scope (4 entries) — re-verified all 4 still resolve and
  still map to the 3 open P0 items; unchanged.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — re-verified all 3 open items: 2 remain
  genuinely credential-blocked (`ORCHESTRATOR_JWT_SECRET` SM alignment is permission-blocked by design for agents;
  `harsh-worker`'s SSM IAM grant already has a filed CREDENTIAL APPROVAL REQUEST). **Lower-confidence flag, not
  reclassifying**: the `[DESIGN] P0` dirty-worktree resolution item (line ~364) cites an already-operator-directed
  4-step policy (Ikenna, Slack 2026-06-12) — the DESIGN itself reads as decided, with only "worker prompt template +
  dispatch hook + plan todos per repo surface" left to build; worth a second look on a future pass to confirm whether
  this is still a genuine open design call or has become bounded implementation work. Left untouched this pass — 3 prior
  audits (07-30, 08-01, 08-06) all classified it the same way and I have no new evidence to override that.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **2**, matching. The `[CREDS] P0` SM-secret-write item is fully staged with exact operator-run commands (2026-08-08
  ruling: "Operator will run it") — an agent-side secret write, permission-blocked by design. Took a fresh second look
  at the `[DESIGN] P0` dirty-worktree-resolution item per the 2026-08-07 marker's own flagged uncertainty: grepped codex
  for whether the 4-step policy (QG→quickmerge / fix→re-QG / escalate / operator-sanctioned hard-reset) has since been
  built elsewhere — found only the adjacent-but-distinct fresh-spawn dirty-state resolution (`resolve_dirty_state`,
  FM2/FM3/FM8, already covered/cited in this same doc) and no implementation of the "committed- able but unverified WIP"
  chain this item specifically describes. Still genuinely open, unbuilt design work — 4th consecutive audit pass
  reaching the same conclusion, now with an actual second look performed, not just deferred.
