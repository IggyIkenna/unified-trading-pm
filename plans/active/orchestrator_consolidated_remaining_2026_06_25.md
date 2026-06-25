---
title: "Orchestrator / escalation / fleet-ops — consolidated REMAINING work (single SSOT; supersedes 7 prior orchestrator plans + 4 issue docs)"
name: orchestrator_consolidated_remaining_2026_06_25
parent_epic: orchestrator_master
assigned_vm: planning
created: 2026-06-25
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-25
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 11.2 # ×0.8 infra multiplier
supersedes:
  - orchestrator_self_healing_hardening_2026_06_21 (1 open item migrated; done items + decision log preserved in source)
  - orchestrator_agent_type_oversight_coverage_2026_06_17 (1 open item + 2 deferred migrated; done preserved)
  - orchestrator_account_failover_resume_respawn_2026_06_17 (1 open NICE-TO-HAVE migrated; done preserved)
  - orchestrator_human_central_vm_split_2026_06_12 (1 open [OPERATOR] + 1 open [INFRA] DEFERRED migrated; done preserved)
  - agent_orchestrator_dashboard_monitoring_2026_06_19 (5 open [OPERATOR]-gated items migrated; done preserved)
  - fleet_git_health_orchestrator_2026_06_10 (1 open [VERIFY] migrated; done preserved)
  - dispatch_strict_vm_matching_2026_06_24 (all open items migrated; done 0 — plan was all open)
  - issues/agent_orchestrator_alerts_triage_2026_06_20 (1 open item migrated; done preserved; issue fully archived)
  - issues/orchestrator_dirty_state_gate_stomps_live_wip_2026_06_22 (open items migrated as todos; issue archived)
  - issues/orchestrator_spawn_failure_slack_alert_gap_2026_06_25 (all items DONE — pure archive)
  - issues/backfill_vm_silent_worker_stall_watchdog_2026_06_19 (all items DONE — pure archive; parent_epic infrastructure_master not orchestrator_master, but issue referenced orchestrator surface)
source:
  - the 7 plans + 4 issues above (second-level consolidation; first-level 2026-06 fold collapsed many individual plans into themed ones, most now done)
  - parallel rationale-extraction sweep 2026-06-25 (slot-3·laptop) — open items + decision context harvested verbatim from each source
---

# Orchestrator / Escalation / Fleet-Ops — Consolidated Remaining Work

> **Why this plan exists.** Orchestrator work accumulated across 7 active plans + 4 issue docs. Those plans are now
> mostly DONE, leaving a handful of open items scattered across 11 documents. This plan is the **single live SSOT for
> the REMAINING orchestrator work**; the source plans/issues are SUPERSEDED (their done items + full narrative stay
> readable in-source as the historical record). **Nothing below is new scope** — every item is migrated verbatim with
> its priority tag and a one-line provenance ref `(source ▸ tag)`.
>
> **The Decision Log (next section) is the irreplaceable part** — it preserves _why_ each architecture was chosen
> over the alternative, so a future agent picking up an item understands the prior reasoning rather than
> re-litigating it.

---

## Decision Log — preserved rationale (why A over B)

Read the relevant entry **before** touching an item in its workstream. These are the design decisions the source plans
established; they are SSOT here.

### D1 — Human / central VM split (operator 2026-06-12)

The merged "Central API VM == Planning VM" was split. Central VM (`planning` = `i-0c9b283b31d6b5ca7`, m8i.4xlarge,
`api.agent-orchestrator.odum-research.com`) holds the EIP + DNS + hand-wired secrets → it stays the routing hub; the CI
escalation / AutoSpawn / plan-health machinery lives here, with **no human daily work**. Human VM
(`human-planning` = `i-0dd9812a96cdda5dc`, m7i.2xlarge) is Ikenna+Harsh interactive only. **Why:** re-homing the
central role would mean re-pointing the EIP + DNS + re-wiring secrets for zero benefit and real risk — so the human
role is the one that moved to a fresh box. The legacy id `planning` stays on the central VM (runtime
`ORCHESTRATOR_VM_ID=planning` is hand-wired, renaming would orphan live operator sessions).

### D2 — Rotation-not-recovery spawn model (operator 2026-06-25)

A dead account / auth-failed token drops OUT of rotation (`mark_account_auth_failed` → `account_is_usable=False` →
`_pick_headroom_account` skips it → auto-re-probe after backoff). The orchestrator keeps spawning on the healthy pool —
it does NOT block the queue retrying a dead slot. Account-bad is a **poller verdict only** (a startup-EXIT spawn
failure with an auth-shaped pane-tail — `/login`/`Invalid API key`/`setup-token`/`unauthorized` — now also feeds
`mark_account_auth_failed`; a generic non-auth tmux throw does NOT drop the account). **Why over recovery:** a
recovery path ("re-auth then retry the same slot") blocks the queue and starves dispatch; rotation keeps velocity on
the healthy pool and lets the operator re-auth at their own pace. The 95% usage ceiling is a SPAWN GATE ONLY (never
preempts running agents); failover fires only on actual stuck-modal state.

### D3 — Context-preserving failover via `--session-id` + `--resume` (2026-06-17)

Each spawn receives a deterministic `--session-id <uuid>` (stored in `AgentRow`). On failover (`SUB_HEADROOM` stuck
state), the worker is killed ONLY if there is headroom on another account, then resumed with
`claude --resume <session-id>` on the headroom account. Empirically proven: different account's
`CLAUDE_CODE_OAUTH_TOKEN` + same `--resume` session-id restores context. Frozen slots (no headroom) are left intact.
`rotate_all_slots_off_account` uses `pick_headroom_account` (95% gated), NOT `pick_next_account` (weaker gate).
**Kill path:** ONLY via `tmux_spawn.kill_session(<name>)`, never `pkill -f claude…`.

### D4 — Watchdog daily-kill cap raised 20→50; LoopSupervisor revives daemon threads (2026-06-21)

The per-VM WorkerLivenessWatchdog daily cap was raised 20→50 (the original limit triggered on heavy churn days and
starved dispatch). `LoopSupervisor` revives dead daemon threads every 120 s so a one-off thread crash doesn't
permanently disable the watchdog/autospawn. Escalation worker must return repos to `live-defi-rollout` before EXIT
so the slot is clean for the next spawn.

### D5 — All live agent types register `AgentRow` (unified oversight model, 2026-06-17)

Escalate / conflict-resolver / plan-health / plan-reconciler / monitor agents all register an `AgentRow`
(`agent_kind` + `lifecycle`) alongside the pre-existing main/review. `AgentKind` two-axis:
`kind` (main/worker/review/escalate/conflict_resolver/plan_health/plan_reconciler/monitor) + `lifecycle`
(one_shot/scheduled/persistent). `AgentKeeper` ensures mandatory {main, review} on every VM;
`AutoSpawn._ensure_review_agents` extracted into keeper. Fleet-worker cap: 10 default, 6 on planning VM.
`backup` DEPRECATED (keeper supersedes). `usage_reporter` DELETED. Reviewed-ledger is advisory
(sha→verdict persisted, NOT a gate). **Why unified:** a single `AgentRow` per live entity gives the dashboard a
complete picture of all automation; the previous model only tracked main/review/worker.

### D6 — Dashboard messaging stays poll-based; wake-on-message nudge via tmux send-keys (2026-06-19)

Operator decision 2026-06-19: **NO messaging-layer rewrite** — no adaptive-cadence / long-poll / SSE. The poll model
stays. The visibility gap (pending → delivered) is covered by a per-agent `count_pending_to_agent`/`pending_count`
chip. **Wake-on-message:** `POST /api/agents/{id}/nudge` → tmux send-keys (the loops are now long: review 15 min,
main up to 60 min; the nudge makes a long idle loop responsive to a UI message). **Why:** a full messaging rewrite
would touch auth + backend + dashboard without materially improving the operator workflow.

### D7 — Agent-type messaging: per-agent `target_agent_id` alongside `target_role` ([OPERATOR]-gated, 2026-06-19)

The current `AgentMessageRow.target_role` model collapses all task-agents into one `custom` chat tab. The operator
confirmed the per-agent + Fleet/tab-surface model as the right design, but marked it **IMPLEMENT LATER** (5 todos
remain `[OPERATOR]`-gated, never auto-dispatched). **Model:** per-agent `target_agent_id` (nullable, alongside
`target_role`); per-kind `surface: fleet|tab` attribute (not lifecycle-derived); Fleet swarm list for
escalate/conflict-resolver/recovery-audit; main-tab chats for singleton kinds (plan-reconciler/plan-health/monitor).

### D8 — Strict fail-closed dispatch: `assigned_vm == backend_id`, no epic-delegation (2026-06-24)

A backend ingests a plan **iff** `plan.assigned_vm == backend_id`. Unset or `NA` → **nobody**. `parent_epic` stays
for orphan-check + priority rollup ONLY (epic→VM delegation DROPPED for matching). **Why:** the `plans/epics/`
snapshot omission bug made delegation resolve every plan as "global" → every backend ingested everyone's plans;
fail-closed on `assigned_vm` makes the match deterministic from the plan alone, independent of the epic snapshot.
`NA` is a valid value meaning "intentionally unassigned / future plan → not dispatched." Claim-marker-on-task-START
was REJECTED (cost: doubles commit volume fleet-wide for a dedup benefit only in the rare mid-flight reassignment
case; operator-awareness covers it at zero cost).

### D9 — Liveness discriminator for dirty-WIP must gate BOTH commit-and-push AND stash paths (2026-06-22)

The orchestrator orphan gate (`server/worktree_clean_check/_orphan.py`) has two resolution paths —
`COMMIT_AND_PUSH` and `git stash` — and NEITHER currently enforces the liveness check. Both can stomp a live
session's uncommitted WIP (two incidents: slot-2 2026-06-22, main clone 2026-06-23). **Required fix:** check
fresh `.agent-claim`/heartbeat OR any tracked file with mtime < 120 s BEFORE either resolution path; if liveness
confirmed → PROTECT (never commit or stash). **Additionally:** if COMMIT_AND_PUSH's push is rejected (slot behind),
the recovery must `pull --rebase --autostash` (not `reset --hard`) so the just-made commit stays reachable; slot-removal
hygiene must scope to the removed slot's OWN clone only.

### D10 — Fleet git-health: per-uid lock files + EUID guard prevent the root-cron contention class (2026-06-22)

The `slot-cron-ff-pull.sh` root-cron bug (two incidents: human-planning VM 2026-06-16, e2e-test VM) is durably
fixed by two layers: (1) `install-slot-cron-ff-pull.sh` now refuses EUID==0 (PM@d512e82e6), so the root crontab
entry can never be created again; (2) lock + state files are now per-uid (`${XDG_RUNTIME_DIR:-/tmp}/<name>.$(id -u).lock`,
PM@4a2f88b9e) so a manual root run never blocks the ubuntu cron. `accounts.json` in agent-orchestrator is gitignored +
`git rm --cached`ed (perpetual-dirty source, kept on disk via creds-bucket SSOT, PM@6385056+@78ca79c).

---

## WS-A — Orchestrator self-healing (source ▸ self_healing)

- [ ] [ORCHESTRATOR] P1. **Account self-recovery reprobe:** two bugs: (1) route gap —
      `/api/accounts/{id}/refresh-usage` never called `clear_account_auth_failed`; (2) latency — `UsagePoller`
      re-probes every 30 min. Fix: (a) route calls `clear_account_auth_failed` on a valid probe; (b) new
      `UsagePoller._reprobe_unhealthy_once` every 120 s, re-probing only `auth_failed`/`rate_limited` accounts.
      3 regression tests. Repo: agent-orchestrator.
      (source ▸ orchestrator_self_healing_hardening_2026_06_21)

---

## WS-B — Agent-type oversight (source ▸ agent_type_oversight)

- [ ] [ORCHESTRATOR] P2. **Phase 5 live smoke** on the central VM: trigger an escalation + the plan-reconciler,
      confirm both appear as agents in the dashboard while working and are reaped when their session dies.
      Repo: agent-orchestrator.
      (source ▸ orchestrator_agent_type_oversight_coverage_2026_06_17)

> **DEFERRED-ASPIRATIONAL (not actionable yet):** `recovery-audit` plan-reconciler finalization — never-launch
> guard shipped (`NEVER_LAUNCH` frozenset + RuntimeError in agent-orchestrator); Ikenna must define DR Layer-1
> design before wiring/deleting. "Do NOT wire or delete it." Filed as a sub-todo below when that design is ready.

> **DEFERRED:** plan-reconciler systemd timer installer (`scripts/install-plan-reconciler-timer.sh`) exists but was
> NOT run on the central VM. Run after Phase 5 smoke passes.

---

## WS-C — Account failover / respawn (source ▸ account_failover)

- [ ] [ORCHESTRATOR] P3. **NICE-TO-HAVE** Dispatch-boundary headroom gate: the `_pick_next_account` callers in
      `server/routes/slots_worker.py` (~lines 125/305/787 — `_pick_next_account` at the worker-done boundary) use the
      weaker "not-429" gate. A worker finishing a task could be re-spawned onto a 99%-usage account. Lower severity
      (between tasks; backstopped by Phase-3 watchdog `_handle_usage_cap`). Make those callers ceiling-gated too,
      or add `require_headroom=True` option to `pick_next_account`. Repo: agent-orchestrator.
      (source ▸ orchestrator_account_failover_resume_respawn_2026_06_17)

---

## WS-D — Human / central VM split (source ▸ human_central_split)

- [ ] [OPERATOR] P1. **Migrate interactive work to human-planning VM at your pace** (no forced session loss —
      provisioning did NOT touch the central VM): on the central VM, commit/push WIP in any open Claude Code tabs,
      then close them; `ssh human-planning-vm` and resume interactive work there
      (`setup-tab-worktrees.sh` already ran for slots 1-2). The central VM keeps serving throughout.
      (source ▸ orchestrator_human_central_vm_split_2026_06_12)

- [ ] [INFRA] P2. **DEFERRED** — pin down what spawned the 37 GB python OOM (2026-06-12 central VM wedge;
      pre-reboot journal gone, needs catching live via earlyoom log). Consider a per-slot cgroup `MemoryMax` so a
      runaway is cgroup-OOM'd (kills just that slot). Repo: agent-orchestrator.
      (source ▸ orchestrator_human_central_vm_split_2026_06_12)

---

## WS-E — Dashboard: per-agent messaging (source ▸ dashboard_monitoring; [OPERATOR]-gated)

> All items in this workstream are `[OPERATOR]`-gated — **never auto-dispatched**. They implement the per-agent chat
> + Fleet swarm surface design (D7). Prerequisites: operator greenlight → ship in order (P2-foundation first).

- [ ] [OPERATOR] P2. **Per-agent messaging FOUNDATION** — add `target_agent_id` (nullable) to `AgentMessageRow`
      (+ `bootstrap.py` ALTER migration) alongside `target_role`; `/api/agents/{id}/poll` drains
      `target_agent_id == id` OR (`target_agent_id IS NULL` AND `target_role == role`); per-agent
      `/api/agents/{id}/history` + `/api/agents/{id}/message` + `count_pending_to_agent`. Prereq for the 4 items
      below. Repo: agent-orchestrator (`server/orm.py`, `bootstrap.py`, `state_store/agents.py`,
      `routes/agents.py`).
      (source ▸ agent_orchestrator_dashboard_monitoring_2026_06_19)

- [ ] [OPERATOR] P2. **Per-kind `surface: fleet|tab` attribute** — config per `AgentKind` (NOT lifecycle-derived:
      escalate + recovery_audit are both one_shot but route differently). Fleet = {escalate, conflict_resolver,
      recovery_audit}; tab = {plan_reconciler, plan_health, monitor}; main/review implicitly tab. Repo:
      agent-orchestrator (`server/` + dashboard `types.ts`).
      (source ▸ agent_orchestrator_dashboard_monitoring_2026_06_19)

- [ ] [OPERATOR] P2. **[UI] Main-tab chats for singleton kinds** — each `surface=tab` kind with a live agent gets
      its OWN agent-keyed chat tab beside main/review (no longer collapsed into `custom`), with per-agent live dot
      (cadence-aware `online` already shipped). pw/vitest gate (PLAN_FORMAT §9). Repo: agent-orchestrator (dashboard
      `App.tsx` tab bar + `RoleChat` → agent-keyed).
      (source ▸ agent_orchestrator_dashboard_monitoring_2026_06_19)

- [ ] [OPERATOR] P2. **[UI] Fleet swarm list** — render live swarm-kind agents (escalate/conflict-resolver/
      recovery-audit) as rows in the EXISTING Fleet view: one row per agent (kind · task/PR · account · live dot ·
      `tmux attach -t …`), click → that agent's per-agent chat drawer. pw/vitest gate. Repo: agent-orchestrator
      (dashboard Fleet view + per-agent chat component).
      (source ▸ agent_orchestrator_dashboard_monitoring_2026_06_19)

- [ ] [OPERATOR] P3. **[UI] Retire the collapsed `custom` role-chat tab** once per-agent chats + Fleet land (it is
      currently the only home for all task-agents; superseded by the per-kind surfaces). Repo: agent-orchestrator.
      (source ▸ agent_orchestrator_dashboard_monitoring_2026_06_19)

---

## WS-F — Fleet git-health (source ▸ fleet_git_health)

- [ ] [VERIFY] P2. **Full two-host fleet verification** — laptop single-slot smoke was done 2026-06-10 (result
      write + reporter read round-trip verified). Remaining: one full `*/5` cron cycle on the laptop + one AWS VM
      with the orchestrator live — fleet page shows both hosts, states match `git status` ground truth on 3
      spot-checked repos, killing the reporter cron flips `reporter_stale` within 15 min, killing the FF-pull cron
      flips `ff_cron_stale`. (Needs the orchestrator running + a second host; do on the live orchestrator VM.)
      (source ▸ fleet_git_health_orchestrator_2026_06_10)

---

## WS-G — Strict VM dispatch matcher (source ▸ dispatch_strict_vm_matching)

- [x] ✅ [SCRIPT] P0. **Phase 0 pre-audit:** enumerate every `plans/active/*.md` — current `assigned_vm` coverage vs
      the registry-valid VM ids (`orchestrator_vm_registry.yaml` — 13 ids incl. `harsh_pc`); list the ~20 active
      plans lacking own `assigned_vm` and the value each _should_ get (its epic's VM, or `NA` if future). Output a
      table into this plan's Progress Log. **Gate**: table present + delegating-plan list confirmed against registry.
      (source ▸ dispatch_strict_vm_matching_2026_06_24)

- [ ] [CODE] P0. **Phase 1 strict matcher** — in `server/regen_backlog_from_plan.py`:
      `_resolve_plan_vms` returns the plan's OWN `assigned_vm` only (drop the `parent_epic` resolution branch —
      D8); matcher fail-closed on unset/`NA`; make strict the **only** mode (retire the non-strict default of
      `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` in `config.py:538`). Verify `_prune_stale` still shares the gate so
      reassigned-away plans' queued tasks GC. **Gate**: unit tests — match / mismatch / `NA` / unset all
      fail-closed; reassignment prunes queued + leaves dispatched/done; `quality-gates.sh` green.
      Repo: agent-orchestrator.
      (source ▸ dispatch_strict_vm_matching_2026_06_24)

- [ ] [INFRA] P0. **Immediate relief for the running `harsh_pc` box**: set strict mode + restart so the 33
      mis-ingested tasks drop on the next regen (operator-applied on their host; queued-only prune, no data loss).
      **Gate**: `harsh_pc` backlog == only `harsh_pc`-assigned plan tasks.
      (source ▸ dispatch_strict_vm_matching_2026_06_24)

- [ ] [DOCS] P0. **Phase 2 supersede-audit** — audit `orchestrator_v07_multi_vm_topology_2026_05_21.md` +
      `agent_orchestrator_backlog_state_alignment_2026_05_29.md` for tasks overlapping this scope
      (VM-assignment / strict matching / regen-prune); migrate each to this epic OR confirm done / not required.
      Add partial-supersede banners pointing here for the VM-assignment + matching scope. **NOT a wholesale
      supersede.** (source ▸ dispatch_strict_vm_matching_2026_06_24)

- [ ] [DOCS] P1. **Phase 3 docs** — update CLAUDE.md: strict-matching rule (`assigned_vm == backend` iff;
      unset/`NA` → nobody) + `assigned_vm` domain = registry ∪ `NA` + the reassignment/prune model. Update
      `codex/12-agent-workflow/` (regen strict-matching + reassignment/prune; fix the stale "epic-delegation is the
      fix" docstring). (source ▸ dispatch_strict_vm_matching_2026_06_24)

---

## WS-H — Orchestrator dirty-WIP gate (source ▸ dirty_state_gate)

- [ ] [CODE] P1. **Liveness guard on COMMIT_AND_PUSH path** — `commit_and_push_dirty_repos`
      (`server/worktree_clean_check/_orphan.py`) currently has NO mtime / `.agent-claim` / heartbeat liveness
      check. Enforce the documented discriminator BEFORE committing: a slot with a provably-live session (fresh
      `.agent-claim`/heartbeat OR any tracked file with mtime < 120 s) must be PROTECTED. Also: if
      COMMIT_AND_PUSH's push is rejected (slot behind), the recovery must `pull --rebase --autostash` (not
      `reset --hard`) so the just-made orphan-wip commit stays reachable (not dangling). Repo: agent-orchestrator.
      (source ▸ issues/orchestrator_dirty_state_gate_stomps_live_wip_2026_06_22)

- [ ] [CODE] P1. **Liveness guard on git-stash path** — the same liveness check must gate the `git stash`
      resolution path in orphan/clean-check hygiene (Incident 2: stash fired on a live interactive session's main
      clone when phantom slots were killed). Also: slot-removal hygiene must scope to the removed slot's OWN
      clone only — killing `orch-slot-N` must never touch a different clone's working tree. If the gate does stash,
      log the stash ref + name loudly + ideally re-apply on the next tick once it confirms liveness.
      Repo: agent-orchestrator.
      (source ▸ issues/orchestrator_dirty_state_gate_stomps_live_wip_2026_06_22)

- [ ] [CODE] P2. **Interactive-session liveness:** confirm that an interactive Claude Code session on a slot
      registers the same `.agent-claim`/heartbeat the gate keys off (the symmetric-worker model says an interactive
      session IS slot N). If it doesn't, the gate will keep treating live operator WIP as dead-predecessor leftovers.
      Repo: agent-orchestrator.
      (source ▸ issues/orchestrator_dirty_state_gate_stomps_live_wip_2026_06_22)

---

## WS-I — Alert routing (source ▸ alerts_triage)

- [ ] [INFRA] P3. **cloud-build-router prod-deploy readiness for service repos** — decide
      (deploy-readiness, pre-cutover): do core service repos (strategy-service, instruments-service, …) get a
      prod-deploy trigger + auto-deploy on main now, or stay build-only until live cutover? If yes, fix the router's
      trigger-detection / add the prod-deploy triggers + fix the stale
      `create-cloud-build-feature-triggers.sh` remediation pointer. **NOT triggering prod deploys of trading
      services autonomously** (consequential; operator-decision required). Repo: deployment-service.
      (source ▸ issues/agent_orchestrator_alerts_triage_2026_06_20)

---

## Recently verified DONE (harvested from source plans — do not re-do)

**orchestrator_self_healing_hardening_2026_06_21 (all other items):**

- `heal_dead_slot_branch_quarantine` wired into `_do_spawn` — preserves WIP to `wip-preserve/` ref, then
  `checkout -B` to origin/base, ONLY for provably-dead slot; verified live 2026-06-21.
- `_reclaim_leftover_merged_branch`: throwaway `_tmp-*` / `_backmerge` branches auto-reclaimed if clean + ancestor.
- LoopSupervisor revives dead daemon threads every 120 s.
- Escalate worker returns repos to `live-defi-rollout` before EXIT.
- Fleet-resilience: `regen_backlog_from_plan` reads PM LDR (not main) to avoid PM red gate starving dispatch.
- UTC outage recovery: flap-guard + poller clears `_flap_backoff_until` fleet-wide on recovery.
- Watchdog daily cap raised 20→50.
- S3 state-snapshot region bug FIXED (UTL provider-aware `get_region()`).

**orchestrator_agent_type_oversight_coverage_2026_06_17 (all other items):**

- `AgentKind` + `lifecycle` on all 8 agent types; `AgentKeeper` for mandatory {main, review}.
- `backup` DEPRECATED; `usage_reporter` DELETED.
- `NEVER_LAUNCH` frozenset guard on `recovery-audit` (never auto-wired).
- Phase 7: `_do_spawn` reordered — `resolve_dirty_state` BEFORE `check_slot_branch_state`.
- Escalation slot starvation fix: `_recently_quarantined` 10-min TTL skip in `_pick_free_slot`.

**orchestrator_account_failover_resume_respawn_2026_06_17 (all other items):**

- 95% ceiling spawn gate; `rotate_all_slots_off_account` uses `pick_headroom_account`.
- `claude --session-id <uuid>` at spawn + `--resume <id>` on failover; resume across token change proven.
- Kill ONLY via `tmux_spawn.kill_session`, never `pkill -f claude...`.

**orchestrator_human_central_vm_split_2026_06_12 (all other items):**

- Central + human-planning VMs provisioned + verified (`verify_vm_e2e.sh` PASS 8/8).
- Registry split `planning`→`central` + `human-planning` added; codex/CLAUDE.md topology docs updated.
- earlyoom installed on BOTH VMs (bootstrap.py); central VM OOM-wedge recovered via EC2 reboot.
- Per-uid lock files + EUID guard shipped (PM@4a2f88b9e + PM@d512e82e6).
- `accounts.json` gitignored + `git rm --cached` (agent-orchestrator@6385056+@78ca79c).

**agent_orchestrator_dashboard_monitoring_2026_06_19 (all Phase A–C items):**

- Retain finished agents (soft-delete `finished` + prune last N/kind/7d).
- Filterable `GET /api/agents` (status/kind/lifecycle/include_finished/limit).
- `AgentTypesPanel` — per-kind online count + show-finished toggle; desktop + mobile.
- Activity feed backend — SQL filters + cursor pagination + denoise rollup; frontend — Load older / server-side
  filter tabs / xN collapse.
- Failure-reason render inline (expandable) on failure-class activity rows + escalations view.
- Conditions collapsible (COLLAPSED_COUNT=5, blocking-gates-first sort, Show N more).
- Message-delivery chip (`count_pending_to_agent` → queued N / delivered).
- Live-validation bugs fixed: main-agent `agent_kind=orchestrator`, reaper reconciles active+stale.
- Review heartbeat mislabel fixed (cadence-aware silence thresholds, live-session dedup).

**fleet_git_health_orchestrator_2026_06_10 (all other items):**

- `GET /api/fleet/git-health` — per-host×slot×repo aggregation with `reporter_stale`/`ff_cron_stale`/`drift_violation`.
- Fleet Git dashboard page (`/fleet-git`) with 30s poll, summary chips, red badges.
- cron-liveness ingestion in `GitStatusPostRequest`; vitest harness added (17 specs).
- Phase 3.5 root-cause fix: EUID guard + per-uid lock files; human-planning VM remediated; reporter token provisioned.

**issues/orchestrator_spawn_failure_slack_alert_gap_2026_06_25 — ALL DONE:**

- Auth-shaped spawn failure → `mark_account_auth_failed` (rotation drop); `remain-on-exit` + pane-tail capture.
- Alerting reframed: WARNING=drop-from-rotation, CRITICAL=rotation-exhausted; deduped per-slot `notify_spawn_failed`.
- Transient spawn race hardened: `_SPAWN_TRANSIENT_MAX_RETRIES=2` + `_is_transient_spawn_failure()` (agent-orchestrator@6e6638a).
- Codex updated: `agent-orchestrator-overview.md` §Auto-spawn.

**issues/backfill_vm_silent_worker_stall_watchdog_2026_06_19 — ALL DONE:**

- Progress-marker mode (`STALL_PROGRESS_REGEX`) added to `vm-exec-with-gcs-tee.sh`.
- Gas-fees `--chunks N` chunk-parallelism; `STALL_PROGRESS_REGEX` wired for gas-fees + SFI + sports-MDPS.
- aiohttp `ClientTimeout` bounded on 37 sites (mtds) + all adapter base classes (instruments-service).

**issues/agent_orchestrator_alerts_triage_2026_06_20 (all other items):**

- WorkerLivenessWatchdog bogus idle-minute bug fixed (session_created_at anchor).
- Quarantined-slot auto-recovery (`heal_dead_slot_branch_quarantine`) — live-verified 2026-06-21.
- Paper-trading "trades to do now" split to `#paper-trading-alerts` — wired + verified end-to-end.
- Build Smoke workflow fixed (PROJECT_ID / GAR auth + scoped to wheel-build / Dockerfile-lint).

---

## Success criteria

- A backend ingests ONLY plans whose `assigned_vm` equals its id; `NA`/unset → nobody (proven by unit test). **WS-G**
- The 33 mis-ingested tasks drop from `harsh_pc` backlog on next regen after strict mode. **WS-G INFRA P0**
- Account self-recovery (`_reprobe_unhealthy_once` + route fix) ships + passes 3 regression tests. **WS-A**
- Phase 5 live smoke: escalation + plan-reconciler visible in dashboard as `AgentRow` while running. **WS-B**
- Dirty-WIP gate enforces liveness before COMMIT_AND_PUSH and stash; push-rejected commits preserved via rebase. **WS-H**
- Operator migrated to human-planning VM; central VM is headroom-only for AutoSpawn workers. **WS-D**
- `quality-gates.sh` green on all touched repos; `regen_vm_registry.py --check` exits 0.

---

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — dispatch strict-matcher + human/central VM split (already
  updated 2026-06-12); WS-A reprobe + WS-H liveness guard after those ship.
- `codex/12-agent-workflow/` — regen strict-matching + reassignment/prune model (WS-G DOCS P1); fix stale
  "epic-delegation is the fix" docstring.
- `codex/05-infrastructure/agent-orchestrator-worker-topology.md` — WS-D once operator migrates.

---

## Progress Log

- 2026-06-25 (slot-3·laptop): All 7 source plans + 4 issues fully read. Open items extracted verbatim with
  provenance. Decision Log D1–D10 authored from source decisions. Workstreams WS-A through WS-I created.
  "Recently verified DONE" section populated from source plan done-items. This plan authored.

- 2026-06-25 (slot-3·laptop) WS-G Phase 0 pre-audit complete. 111 active plans scanned against 13 valid VM
  ids + `NA`. **86 OK / 24 missing / 1 invalid.** Table of plans needing `assigned_vm`:

  | # | Plan file | Current `assigned_vm` | Parent epic | Suggested `assigned_vm` |
  |---|-----------|----------------------|-------------|------------------------|
  | 1 | `INDEX.md` | (unset) | (none) | `NA` (meta file) |
  | 2 | `_agent_pings.md` | (unset) | (none) | `NA` (meta file) |
  | 3 | `cefi_deribit_binance_futures_bundle_verification_2026_06_20.md` | (unset) | `cefi_master` | `vm-cefi` |
  | 4 | `cefi_ml_directional_continuous_live_2026_06_20.md` | (unset) | `cefi_master` | `vm-cefi` |
  | 5 | `colocated_feature_pipeline_in_memory_handoff_2026_06_21.md` | (unset) | `features_and_ml_master` | `vm-ml` |
  | 6 | `data_pipeline_acquisition_remediation_2026_06_03.md` | (unset) | `mtds_mdps_master` | `vm-ml` |
  | 7 | `defi_governance_params_refresh_2026_06_20.md` | (unset) | `defi_master` | `vm-defi` |
  | 8 | `defi_mtds_subgraph_and_adapter_fixes_2026_06_20.md` | (unset) | `defi_master` | `vm-defi` |
  | 9 | `defi_onchain_derivable_values_and_date_drift_2026_06_20.md` | (unset) | `defi_master` | `vm-defi` |
  | 10 | `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` | (unset) | `defi_master` | `vm-defi` |
  | 11 | `global_ledger_pnl_attribution_migration_2026_06_01.md` | `vm-execution` **[INVALID]** | `global_ledger_pnl_attribution_master` | `vm-trading-core` |
  | 12 | `harsh_day_master_2026_06_02.md` | (unset) | `plan_hygiene_master` | `planning` |
  | 13 | `mdps_adapter_protocol_pandas_to_polars_2026_06_21.md` | (unset) | `mtds_mdps_master` | `vm-ml` |
  | 14 | `orchestrator_consolidated_remaining_2026_06_25.md` | (unset) | `orchestrator_master` | `planning` |
  | 15 | `predictions_lookahead_and_reader_migration_2026_06_20.md` | (unset) | `predictions_master` | `vm-prediction` |
  | 16 | `predictions_ml_walk_forward_and_arb_2026_06_20.md` | (unset) | `predictions_master` | `vm-prediction` |
  | 17 | `predictions_other_bucket_and_ui_drilldown_2026_06_20.md` | (unset) | `predictions_master` | `vm-prediction` |
  | 18 | `sports_features_readiness_for_predictions_2026_06_20.md` | (unset) | `sports_master` | `vm-sports` |
  | 19 | `sports_fixtures_schema_split_completion_2026_06_20.md` | (unset) | `sports_master` | `vm-sports` |
  | 20 | `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` | (unset) | `sports_master` | `vm-sports` |
  | 21 | `sports_phantom_recon_and_coverage_windows_2026_06_20.md` | (unset) | `sports_master` | `vm-sports` |
  | 22 | `task_template.md` | (unset) | (none) | `NA` (meta file) |
  | 23 | `tradfi_cme_event_contract_backfill_2026_06_20.md` | (unset) | `tradfi_master` | `vm-tradfi` |
  | 24 | `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` | (unset) | `tradfi_master` | `vm-tradfi` |
  | 25 | `work_split_2026_05_22_ikenna.md` | (unset) | `orchestrator_master` | `vm-orchestrator` |

  **Notes:** Row 11 (`global_ledger_pnl_attribution_migration`) has invalid value `vm-execution` (retired VM id;
  epic `global_ledger_pnl_attribution_master` → `vm-trading-core`). Rows 1/2/22 are meta files (not real plans).
  Row 14 (`orchestrator_consolidated_remaining_2026_06_25.md` = this plan) likely already has `assigned_vm: planning`
  in frontmatter but was detected as missing due to a script read-limit edge case; frontmatter is correct.
  Gate: **TABLE PRESENT ✅ | registry-confirmed ✅** — all 25 rows checked against registry.
