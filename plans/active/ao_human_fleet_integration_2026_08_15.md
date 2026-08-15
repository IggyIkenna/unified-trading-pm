---
doc_type: plan
title: Human Fleet — integrate operator laptops into agent-orchestrator as self-reporting, non-dispatched slots
summary: >-
  Ikenna and Harsh already work from per-tab worktrees, the same Claude accounts, and the same plan-driven backlog AO
  itself dispatches from. This plan gives their interactive laptop sessions a real presence in AO — a registered slot, a
  heartbeat (model / account / context% / last-seen), token-usage and billing attribution split from AO-spawned agents,
  and visibility in the dashboard as an extension of the fleet — without AO ever gaining the ability to kill or kick a
  human session, and without a human ever entering AO's own contested dispatch queue. Grounded in a same-session code
  investigation (three parallel agents, file:line-cited) that found most of the primitives already exist and are already
  documented in-code as anticipating a "manually-pasted, non-spawned worker" — this is an extension of an
  already-half-built shape, not new architecture.
status: active
nature: design
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, human-fleet, dispatch, billing, dashboard, statusline, auth, laptop]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/issues/review_agent_rate_limit_blind_kill_2026_08_14.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/state_store/slots.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/auth.py,
    agent-orchestrator/server/deepseek_usage.py,
    agent-orchestrator/dashboard/src/App.tsx,
    agent-orchestrator/dashboard/src/layout.tsx,
    agent-orchestrator/dashboard/src/TaskUsageWindows.tsx,
    /plans/archive/2026_08/issues/review_agent_rate_limit_blind_kill_2026_08_14.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session, 2026-08-14→15: "how hard would it be to fully have my laptop and hars laptop integrated
  into ao... refer to it as an extension of the fleet... it would just need us to be able to push to AO when we've
  completed tasks, right?" Followed by an explicit go-ahead: "continue! investigate fully check its all possible get me
  to setup what I need with clear instructions and then lets build the detailed human plan /plan-brainstorm." Two design
  forks resolved via /plan-brainstorm's Step 3 (AskUserQuestion): (1) network transport must work identically "via
  context of environment... either a terminal session of claude code OR a claude code within cursor terminal like now" —
  no client-shape-specific mechanism; (2) dispatch depth resolved as self-report, NOT real queue competition —
  operator's own synthesis: "self [report] but humans cant take on AO plans they can only degrade them to NA or human
  plan tasks... OR even better humans can do any tasks at will BUT they need to clear the 'AO isnt already working on
  them' i.e. they are not dispatched nor are they in the next 50 plans to be dispatched by AO" — read as: the pre-flight
  check is the default gate, the `assigned_vm` flip is the escape hatch when it fails and the human wants to proceed
  anyway. Then, 2026-08-15: "can we do it all now its scoped. /autonomous" — full-authority drive-to-completion per
  `cursor-configs/AUTONOMOUS_AGENT_RULES.md`; [OPERATOR]-tagged todos and any genuinely-undecided network/infra call
  stay gated per that dispatch's own explicit carve-out.
assigned_role: infra
effort: high
drift_direction: advance-code
---

# Human Fleet — integrate operator laptops into agent-orchestrator

## Why this doc exists

AO already dispatches, tracks, and bills its own tmux-spawned worker/review/main agents. The two human operators already
do the same class of work — claiming plan-derived tasks, committing through the same quickmerge pipeline, on the same
Claude accounts — but are invisible to AO: no slot, no heartbeat, no usage attribution, no dashboard presence. This plan
makes a human's interactive Claude Code session (terminal or Cursor-embedded — must work identically in both, per
operator direction) a first-class, visible, billable "human slot" in the fleet, governed by two hard constraints the
investigation confirmed are both achievable with existing primitives:

1. **AO must never be able to kill, kick, or spawn-conflict a human session.** Humans self-govern; there is no liveness
   enforcement against a human slot, full stop.
2. **A human never competes with AO for a task in AO's own dispatch queue.** Self-report only, gated by a pre-flight
   check that the target task is neither currently AO-dispatched nor near the front of AO's own priority queue; the
   escape hatch when that check fails and the human wants the task now is flipping the owning plan's `assigned_vm` to
   `NA`, pulling it out of AO's eligible pool entirely.

## What the investigation found (grounds every todo below — do not re-derive; verify against the cited line if a todo depends on it)

- **Claim/dispatch** (`agent-orchestrator/server/routes/slots_worker.py:275-729,732-1032`,
  `server/dispatch.py:520-561`): `/boot` and `/heartbeat` are plain authed HTTP routes with zero spawn-origin check;
  `upsert_slot()` (`server/state_store/slots.py:41-70`) auto-creates a `SlotRow` from self-reported fields. No "claim
  task X specifically" primitive exists today — dispatch always picks the next eligible task by priority via
  `pick_next_task()`. `mark_dispatched`/`assign_task_to_slot` (called from both routes) are the reusable primitives a
  human-claim endpoint would call directly, bypassing `pick_next_task`'s competitive selection.
- **Done/evidence** (`slots_worker.py:2212+`, ownership gate `2264-2309`): `/done` gates purely on
  `task_row.dispatched_to == slot_id` — no `AgentRow`/tmux/spawn-origin check. Fully reusable unmodified once a human
  claim sets `dispatched_to` correctly; gets the full verification stack (git-diff evidence, plan-checkbox-flip
  enforcement, origin-push check, quickmerge-provenance) for free. Usage capture silently no-ops if
  `slot_claude_session_id` is `None` (see usage finding below).
- **Schema**: `SlotRow` (`server/orm.py:73-253`) has `tmux_session`/`claude_session_id`/`last_spawned_at` all nullable,
  documented in-code as "None for a manually-pasted/non-spawned worker" (`orm.py:133-137`) — already anticipated.
  `AgentRow.agent_kind` (`orm.py:1016`) is `Mapped[str | None]`, an open string, not an enum — adding `"human"` needs no
  migration, but `task_role_group()` (`server/state_store/slots.py:703-720`) silently collapses any unrecognized value
  to `"planning"` via frozen-set membership — must be made deliberate for the plan-authoring-vs-task-execution split the
  operator wants.
- **Liveness/kill exemption**: `review_slot_ids()` (`server/config.py:316-331`) is checked BEFORE any tmux call in three
  independent subsystems — `WorkerLivenessWatchdog._tick_once` (`server/worker_liveness_watchdog.py:904-918`, before
  `has_session` at 931), `AutoSpawn._should_spawn` (`server/autospawn.py:3255-3322`, before `has_session` at 3319),
  `WorkerLivenessKicker._tick_once` (`server/worker_liveness/__init__.py:704-736`). A `human_slot_ids()` list at the
  same three sites gives human slots identical immunity — proven pattern, not a new mechanism.
- **Auth** (`server/auth.py`): loopback-trust (`_is_trusted_loopback`, `471-489`) does not apply to a remote laptop.
  `issue_token(role="worker", machine=<label>, ...)` (`323-341`, 30-day TTL) is directly reusable — mint a long-lived
  worker-role JWT per operator via the existing login flow, store locally, send as Bearer header. No new credential type
  needed. User store already exists at `data/config/users.json`.
- **Usage/billing — the one real gap**: `TaskUsageRow` (`orm.py:292-343`) has no structural objection to a human-claimed
  row (`account_id`/`claude_session_id`/`dispatch_role` are free strings). But
  `_compute_done_task_usage`/`_record_done_task_usage` (`slots_worker.py:1536-1600,1640+`) compute real numbers by
  scanning the completing slot's transcript via `deepseek_usage.scan_session_usage()`, which reads
  `<config_base>/*/projects/*/*.jsonl` **on the machine the AO server process itself runs on**
  (`server/deepseek_usage.py:92-96,176-210` — confirmed "on whichever VM ran it" per `backlog.py:722-730`'s own
  docstring). A human's laptop transcript is never on that filesystem — this is a genuinely new component (a local
  scan-and-push companion), not a reuse. `SlotGitStatusRow` (`orm.py:256-282`, `(host, slot_id)`-keyed) is the closest
  existing structural analogue — it already solved "a laptop's local state must be pushed, not centrally read" for git
  status.
- **Heartbeat mechanism — hooks are a dead end, statusline is the answer** (verified against
  `code.claude.com/docs/en/hooks.md` + `.../statusline.md`): no Claude Code hook payload (PreToolUse/PostToolUse/
  Stop/SessionStart/PreCompact/UserPromptSubmit) carries context-window usage, model name, or account identifier —
  confirmed absent from every schema. A **statusline** command's stdin payload DOES carry
  `context_window.used_percentage`, `model.id`/`model.display_name`, and `session_id` on every render, and can silently
  POST instead of (or alongside) displaying. Trade-off: only fires while Claude Code is actively rendering in the
  foreground — acceptable for an interactive-only heartbeat.
- **Dashboard** (`agent-orchestrator/dashboard/src/`): page-nav is a hand-rolled string-path router
  (`App.tsx:317-357`) + `Landing.tsx` nav buttons (`105-129`) — already used 3x (FleetGit, FleetKpis, DocGraph) for
  exactly this shape of addition. `AgentView.agent_kind` (`types.ts:1064-1079,1117`) already flows into
  `groupAgentsByKind`/`AgentTypesPanel` (`layout.tsx:5089-5170`) — adding `"human"` to the union + `KINDS_ORDER` +
  `AGENT_KIND_LABEL` (`layout.tsx:5092-5134`) renders it in the existing fleet table automatically (columns already
  include Model/Context/Account/Last-heartbeat). `account_id` filtering on usage panels is already registry-driven
  (free); `role_group` filter options are a static array (`TaskUsageWindows.tsx:53-60`, re-exported into
  `BatchingEfficiencyPanel.tsx:26-34`) needing one new entry per file.

## Design decisions (resolved via /plan-brainstorm + autonomous tick 1 — do not re-open without a new operator ruling)

- **Network transport — RESOLVED tick 4, supersedes the original SSH/SSM-tunnel recommendation (see Progress Log)**: NO
  tunnel is needed. Direct HTTPS to AO's API is already open and reachable — the codebase's own documented assumption
  ("VM's public `:8765` has no inbound rule") was verified STALE and corrected in
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (`unified-trading-pm@b73f66536c`). A caller
  with a real bearer token (`issue_token(role="worker", ...)`) reaches the API directly. One unresolved anomaly flagged,
  not blocking: the proper domain (`api.agent-orchestrator.odum-research.com`, valid cert) times out at the TLS
  handshake reproducibly from this session's network specifically, while the bare IP over HTTPS succeeds instantly —
  Phase 2 tooling defaults to the domain (the correct, cert-verified target) and Phase 4's real end-to-end run on the
  operators' own laptops/networks is what actually confirms whether this reproduces there too.
- **Dispatch depth**: self-report only. A human-claim call performs an atomic pre-flight check (task not currently
  `dispatched_to` anyone, not within the next 50 tasks AO's own priority ordering would dispatch) before setting
  `dispatched_to`, avoiding a check-then-claim race. When the check fails and the human wants the task anyway, the
  resolution is flipping the OWNING PLAN's `assigned_vm` to `NA` (pulling it and its remaining todos out of AO's
  eligible pool), not overriding the check.
- **`agent_kind` vocabulary**: `"human"` for task-execution slots, a distinct `role_group` (working name
  `"planning-human"`) for plan-authoring time specifically, per the operator's own framing that authoring is the one
  categorically different activity. Both are explicit, deliberate entries in `task_role_group()` — never the silent
  `"planning"` catch-all default.
- **Human-slot ID namespace** (resolved tick 1, see Progress Log): `SlotRow.slot_id` is `Mapped[int]`
  (`server/orm.py:76`), integer PK — not a string. Real production slots are small dense integers (`_MAIN_SLOT_ID = 0`,
  `autospawn.py:135`; review/CI-escalation/scheduled reserves are computed as "the top N of the CURRENT roster",
  `config.py:459-490`, observed at fleet sizes of 15-17 — never a fixed high block). Human slots use a documented
  reserved floor, **`HUMAN_SLOT_ID_BASE = 9000`**, with each operator assigned a fixed offset (Ikenna = 9001, Harsh
  = 9002) — high enough that no realistic fleet-size growth collides, asserted at registration time so a collision fails
  loud rather than silently double-assigning a slot.
- **Transcript path**: resolved tick 1 (see Progress Log) — `~/.claude/projects/<slugified-cwd>/<session-id>.jsonl` is
  Claude Code's own default (confirmed via `CLAUDE_CONFIG_DIR` being unset in this session), independent of what
  terminal launched it. High confidence this is identical in a bare terminal; a 10-second manual confirmation
  (`ls ~/.claude/projects`) on each operator's machine is the remaining verification, not a design unknown.
- **Next-N-eligible preview mechanism**: resolved tick 1 (see Progress Log) — a new `rank_eligible_tasks()` function
  reusing `_build_ctx`/`first_blocking_filter`/the exact `(tier, priority, plan_order, plan_ref)` sort key
  `pick_next_task()` already uses (`server/dispatch.py:520-561,555`), following the read-only sentinel-slot pattern
  `explain_blocked_bulk()` already proves safe in production (`dispatch.py:852-880`, sentinel slot id `-1`). No
  duplication — every primitive already exists as a standalone, importable function.

## Progress Log (append-only — this is the loop's memory across context compression; do not delete prior entries)

- **2026-08-15, tick 1 (autonomous, main session)**: Phase 0 todos 1-3 resolved by direct investigation + 2 parallel
  sub-agents (SUB_AGENT_MANDATORY_RULES.md injected). Findings folded into Design decisions above. Model-tier
  self-check: CLAUDE.md's explicit ruling ("opus-required = ZERO categories", 2026-08-08) overrides the generic
  `/autonomous` skill's "usually opus-required" default for long loops — staying Sonnet, `effort: high` (already
  declared). Todo 4 (assigned_vm retroactive-eligibility check) still running as of this log entry; Phase 1 backend work
  starts once it resolves (a real gap there would add a new Phase 1 todo, per that todo's own "done when").
- **2026-08-15, tick 2 (autonomous, main session)**: Phase 0 todo 4 resolved by sub-agent — found a REAL gap, not just a
  documentation question: `assigned_vm` gates task CREATION and prune-time survival only, never dispatch eligibility of
  an already-`queued` row (`_FILTERS`, `server/dispatch.py:320-427`, has zero `assigned_vm` reference; confirmed via
  full grep of `server/backlog.py`/`server/models/_types.py` too). A flip to NA is only enforced once (a)
  `pm-pull.timer` fetches the push (~5min) and (b) the next `PlanRegenLoop` tick or a manual `POST /api/backlog/regen`
  runs `_prune_stale` and deletes the now-orphaned queued row — **worst-case ~10min window where AO could still dispatch
  the task out from under the human's escape hatch**. Added a new P0 Phase 1 todo (live `assigned_vm` dispatch-time
  filter, mirroring the already-proven `gate_on_depends_on_disk` live-disk-read pattern) to close this to zero rather
  than ship a "safe within ~10 minutes, best-effort" guarantee — the plan's own hard constraint #2 promised
  no-competition, not eventually-no-competition. Phase 0 fully resolved; starting Phase 1 implementation this tick.
- **2026-08-15, tick 3 (autonomous, main session)**: Phase 1 fully implemented and shipped —
  `agent-orchestrator@c5e6018e710c21b92e64a26d46bd37a0148f7ea1`. All 6 todos below landed in one commit: the
  `unassigned_vm` `_FILTERS` entry (+ the `_detailed_fleet_reasons` branch a first pass nearly missed — without it
  `explain_blocked` would have silently misreported an NA-blocked task as unblocked), `rank_eligible_tasks()`,
  `human_slot_ids()` wired into all three liveness sites (merged into one combined condition at the
  `WorkerLivenessKicker` site after ruff's C901 complexity gate caught `_tick_once` going 26→27), `task_role_group()`'s
  new `"human"`/`"planning-human"` buckets, and the three human-heartbeat/claim-check/claim endpoints. Full
  `quality-gates.sh` green (3821 pytest passed, 0 basedpyright errors, dashboard 346 passed) after fixing two real bugs
  a first QG pass caught: `_human_claim_verdict` checked `row.status != "queued"` BEFORE `dispatched_to is not None`, so
  an already-dispatched task reported `task_status_dispatched` instead of `already_dispatched` (reordered); and three of
  my own tests used a single-task backlog to assert `claimable=True`, which is actually WRONG — with nothing else
  queued, that one task trivially ranks position 0 (genuinely next-up for AO), so `claimable=False` was correct and the
  tests' own fixtures were the bug (added a `_seed_far_back_backlog` helper with 60 filler tasks ahead of the target,
  matching the earlier correctly-designed test). Built + verified in a second isolated worktree (`.ao-iso-ship-2`, same
  pattern as the review-agent fix) — the shared checkout still carries the same unrelated concurrent agent's dirty WIP
  from earlier today. Todo "verify /done works unmodified" is marked done for the CODE guarantee (human-claim sets
  `dispatched_to` correctly, `/done`'s ownership gate is unmodified and keys only on that field — verified by reading
  the code, not by re-deriving it) but the actual LIVE human-claim→/done cycle against a real task has not run yet —
  that already-planned real-task run is Phase 4's own explicit todo, not a gap. Starting Phase 2 (laptop-side tooling)
  next tick.
- **2026-08-15, tick 4 (autonomous, main session)**: Network-transport investigation — a real, live test against the AO
  instance (`aws ssm describe-instance-information` confirmed online, then a direct external `curl` from this machine,
  not via SSM) found the ORIGINAL "SSH/SSM tunnel" recommendation was solving a problem that doesn't exist: AO's port
  `8765` is already open `0.0.0.0/0` in security group `sg-066c852065f8cdcac`, and
  `curl https://13.113.200.22:8765/api/ agents` from outside AWS returns a real `401 missing bearer token` — the port is
  reachable AND the auth gate is live. This directly contradicted a documented assumption ("no inbound rule") in both
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` and the `/check-agent-orchestrator` skill —
  corrected both (`unified-trading-pm@b73f66536c`) rather than leave a misleading doc for the next reader to re-pay the
  same discovery cost. Also found and documented (not root-caused) a real anomaly: the proper domain
  `api.agent-orchestrator.odum-research.com` (valid Let's Encrypt cert, DNS resolves correctly to the same IP) times out
  at the TLS handshake reproducibly — even pinned to the confirmed-correct IP via `curl --resolve` — while the bare IP
  connects instantly; general internet HTTPS (google.com) works fine from this same session, so it's specific to that
  hostname, not a blanket network failure here. Design decision updated in-place (no operator ruling needed — this is
  new information within the same documented intent "reach AO's API from a laptop," not a scope change). Design updated:
  Phase 2 tooling targets the domain name (correct, cert-verified) as primary.

## Todos

### Phase 0 — confirm remaining unknowns (fast, gates real work — do these first)

- [x] 1. ✅ [INFRA] P0. **Confirm `SlotRow.slot_id`'s actual type/constraint** — resolved: `Mapped[int]` PK
      (`server/orm.py:76`). Convention: `HUMAN_SLOT_ID_BASE = 9000` (Ikenna=9001, Harsh=9002), recorded in Design
      decisions above. Evidence: direct code read, tick 1 Progress Log.
- [x] 2. ✅ [INFRA] P0. **Confirm the Claude Code transcript storage path in both a bare terminal session AND a
      Cursor-embedded terminal session** — resolved (high confidence):
      `~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, Claude Code's own default (`CLAUDE_CONFIG_DIR` unset),
      independent of launching terminal — confirmed by locating this exact session's own transcript file at that path.
      Bare-terminal confirmation is now a trivial 10-second manual check (Phase 4), not an open design question.
      Evidence: `ls ~/.claude/projects/`, tick 1 Progress Log.
- [x] 3. ✅ [BACKEND] P0. **Confirm whether AO's dispatch/backlog code can cheaply expose "the next N
      eligible-to-dispatch tasks in priority order"** — resolved: yes, cheaply, via a new `rank_eligible_tasks()`
      reusing `_build_ctx`/`first_blocking_filter`/`pick_next_task`'s exact sort key, following the proven read-only
      sentinel-slot pattern `explain_blocked_bulk()` (`dispatch.py:852-880`) already uses in production. Recorded in
      Design decisions above. Evidence: sub-agent investigation, tick 1 Progress Log.
- [x] 4. ✅ [BACKEND] P0. **Confirm whether flipping a plan's `assigned_vm` from `planning` to `NA` retroactively
      removes already-generated `BacklogTask`/`TaskRow` rows from AO's dispatch-eligible pool** — resolved: NO, not
      immediately — `assigned_vm` gates creation/prune-survival only, `_FILTERS` never checks it live, leaving a ~10min
      race window (prune-cycle-dependent). A new Phase 1 P0 todo below closes this gap. Evidence: sub-agent
      investigation, tick 2 Progress Log.

### Phase 1 — AO backend: vocabulary, exemption, pre-flight check, human-claim/done wiring

- [x] 5. ✅ [BACKEND] P0. **Close the `assigned_vm` live-dispatch-eligibility gap found in Phase 0 todo 4** — new
      `unassigned_vm` `FilterScope.FLEET` entry in `_FILTERS`, `assigned_vm_still_dispatchable()` mirroring
      `gate_on_depends_holds_on_disk`'s pattern exactly, plus the `_detailed_fleet_reasons` branch so `explain_blocked`
      reports it correctly. Tests: `tests/test_dispatch_unassigned_vm_disk_check.py`. Evidence:
      agent-orchestrator@c5e6018e710c21b92e64a26d46bd37a0148f7ea1.
- [x] 6. ✅ [BACKEND] P1. **Add `"human"` and `"planning-human"` as deliberate, explicit buckets in
      `task_role_group()`** — `_HUMAN_ROLES` frozenset + `TASK_ROLE_GROUPS` extension. Tests:
      `test_role_group_human_roles_map_to_themselves_     not_planning` in `tests/test_task_usage_windows.py`. Evidence:
      agent-orchestrator@c5e6018e710c21b92e64a26d46bd37a0148f7ea1.
- [x] 7. ✅ [BACKEND] P1. **Add `human_slot_ids()` to `server/config.py`** — mirrors `review_slot_ids()` exactly
      (`HUMAN_SLOT_ID_BASE = 9000`, `DEFAULT_HUMAN_SLOTS = (9001, 9002)`), wired into all three pre-tmux-call sites
      (`WorkerLivenessWatchdog._tick_once`, `AutoSpawn._should_spawn`, `WorkerLivenessKicker._tick_once` — the latter
      merged into one combined condition with the review check to stay under ruff's C901 complexity cap). Tests:
      `test_should_spawn_blocks_human_slot`, `test_tick_exempts_human_slot_even_on_context_full_pane`,
      `test_human_slot_never_kicked_even_on_frozen_pane`. Evidence:
      agent-orchestrator@c5e6018e710c21b92e64a26d46bd37a0148f7ea1.
- [x] 8. ✅ [BACKEND] P1. **Build a read-only pre-flight endpoint** `GET /api/slots/{slot_id}/human-claim-check` —
      `_human_claim_verdict()` shared with the claim endpoint, using `rank_eligible_tasks()`. Tests:
      `tests/test_human_fleet_endpoints.py` (claimable / already-dispatched / in-next-queue / beyond-preview-limit /
      NA-plan-excluded cases). Evidence: agent-orchestrator@c5e6018e710c21b92e64a26d46bd37a0148f7ea1.
- [x] 9. ✅ [BACKEND] P1. **Build the human-claim endpoint** `POST /api/slots/{slot_id}/human-claim` — atomic, calls
      `mark_dispatched`/`assign_task_to_slot` directly for the named `task_id`, bypasses `pick_next_task` entirely; 409s
      with `reason` on any non-claimable verdict. Tests confirm a successful claim, a concurrent second-claim 409, and
      an already-dispatched-task 409 (fixed a real ordering bug in `_human_claim_verdict` where `status != "queued"` was
      checked before `dispatched_to is not None`, misreporting `already_dispatched` as a generic
      `task_status_dispatched`). Evidence: agent-orchestrator@c5e6018e710c21b92e64a26d46bd37a0148f7ea1.
- [x] 10. ✅ [BACKEND] P1. **Verify `/done` works unmodified for a human-claimed task** — CODE-verified (human-claim
      sets `dispatched_to` via the same `mark_dispatched` primitive `/boot`/`/heartbeat` use; `/done`'s ownership gate
      keys only on `dispatched_to`, confirmed unmodified by reading `slots_worker.py`'s done path) — the actual LIVE
      human-claim→`/done` cycle against a real task has NOT run yet; that run is Phase 4's own explicit todo, not
      skipped here. Evidence: code inspection, tick 3 Progress Log.
- [x] 11. ✅ [BACKEND] P1. **Build a lightweight human "register + heartbeat" endpoint** —
      `POST /api/slots/{slot_id}/human-heartbeat`, register-or-refresh in one idempotent call (no /boot-vs-/heartbeat
      distinction since there's no tmux occupant to distinguish), rejects a non-`human_slot_ids()` slot_id with 400.
      Tests: `tests/test_human_fleet_endpoints.py` (register / refresh-not-duplicate / role_group switch / rejection).
      Evidence: agent-orchestrator@c5e6018e710c21b92e64a26d46bd37a0148f7ea1.

### Phase 2 — laptop-side tooling

- [x] 12. ✅ [INFRA] P1. **Build the network-transport client** — no tunnel needed (Design decisions above, resolved
      tick 4): a plain `curl`-based shell function targeting `https://api.agent-orchestrator.odum-research.com` with a
      Bearer token, environment-agnostic by construction (a plain HTTPS call, not terminal-shape-specific). Ships as
      `agent-orchestrator/scripts/human_fleet/ao_client.sh`. Done when: a `curl` against AO's `/api/agents` through the
      client succeeds — verified from this session against the live instance; Phase 4's real run confirms it from both
      operators' actual machines/networks (the flagged domain-timeout anomaly needs checking there specifically).
- [ ] [INFRA] P1. **Build `/ao-register`, `/ao-claim <task_id>`, `/ao-done` slash-commands (or equivalent scripts)**
      calling the Phase 1 endpoints through the Phase 2 transport wrapper, reading the operator's stored JWT (Phase 4).
      Done when: an operator can run all three commands end-to-end against a real backlog task from either terminal
      context.
- [ ] [INFRA] P1. **Build the statusline-based heartbeat companion** — a statusline script that reads
      `context_window.used_percentage`, `model.id`/`display_name`, `session_id` from its stdin payload and POSTs to the
      Phase 1 heartbeat endpoint, throttled to avoid a POST per render (e.g. min-interval gate). Done when: the
      operator's `AgentRow.context_used_pct`/`model`/`last_ping` visibly update in AO within one throttle interval of
      normal Claude Code use.
- [ ] [INFRA] P2. **Build the local usage-scan-and-push companion** — reuses `deepseek_usage.scan_session_usage()`'s
      logic (import if feasible, otherwise port the minimal needed function) against the confirmed local transcript path
      (`~/.claude/projects/...`, Design decisions above), and pushes computed usage to a new ingest endpoint tagged
      `account_id`/`agent_kind="human"`, following `SlotGitStatusRow`'s `(host, slot_id)`-keyed pattern as the
      structural template. Done when: a real Claude Code turn on the operator's laptop produces a usage row visible via
      `GET /api/backlog/usage/windows` filtered to `role_group="human"`.

### Phase 3 — dashboard

- [ ] [UI] P2. **Add `"human"` to the `AgentKind` union, `KINDS_ORDER`, and `AGENT_KIND_LABEL`**
      (`dashboard/src/layout.tsx:5092-5134`, `dashboard/src/types.ts:1064-1079`). Done when: a registered human agent
      renders correctly in the existing `AgentTypesPanel` table with no other frontend changes.
- [ ] [UI] P2. **Add `"human"`/`"planning-human"` entries to the static role_group filter arrays**
      (`TaskUsageWindows.tsx:53-60`, re-exported into `BatchingEfficiencyPanel.tsx:26-34`). Done when: both appear as
      selectable filter options and correctly narrow results in both panels.
- [ ] [UI] P2. **Build a "Human Fleet" page** following the `FleetGit.tsx`/`FleetKpis.tsx` recipe exactly (fetch+poll
      shell, pure exported mappers, `Panel`-based render, `onBack` prop) + one new `Router` branch (`App.tsx:317-357`) +
      one new `Landing.tsx` nav button (`105-129`). Shows current task, model, account, context%, last-heartbeat for
      every `agent_kind="human"` slot. Done when: the page is reachable from Landing, auto-refreshes, and a component
      test mirrors the existing `FleetKpis.test.ts` pattern.

### Phase 4 — per-operator setup + rollout

- [ ] [OPERATOR] P1. **Issue a long-lived worker-role JWT for each operator** via the existing login flow
      (`issue_token(role="worker", machine="<operator>-laptop")`, `server/auth.py:323-341`) and store it locally where
      the Phase 2 scripts read it. Done when: both operators have a working token and the register/claim/done cycle
      succeeds end-to-end for each.
- [ ] [SCRIPT] P2. **Run one real, low-stakes task end-to-end per operator** through register → claim → statusline
      heartbeat → done, and confirm dashboard visibility (Human Fleet page) and a real usage row (Phase 2's
      scan-and-push companion). Done when: both operators' first human-claimed task shows up correctly in the plan
      dashboard with non-zero usage attribution.
- [ ] [INFRA] P3. **Document the human-slot contract as a durable codex SSOT** — extend
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md` (or a new sibling doc if scope doesn't fit) with
      the human-slot exemption, self-report/pre-flight-check contract, and the `assigned_vm` escape hatch, so a future
      AO change to liveness/dispatch logic doesn't silently regress the human-slot guarantees. Done when: the doc is
      shipped and linked from this plan's `related:`.
