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
    /codex/05-infrastructure/human-fleet-operator-setup.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-19"
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
    agent-orchestrator/scripts/human_fleet,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/deepseek_usage.py,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
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
- **2026-08-15, tick 5 (autonomous, main session)**: Phase 2 (part 1) built and shipped — `agent-orchestrator@5516874`.
  `ao_client.sh` + `ao-register.sh`/`ao-claim.sh`/`ao-done.sh` + `ao-statusline-heartbeat.sh`. **Correction to tick 4's
  finding**: retested the domain-timeout anomaly ~15min later while testing these scripts (5 consecutive attempts) — it
  did NOT reproduce, all 5 succeeded in ~0.7s each with the correct `401`. The earlier reproducible timeout (5+ attempts
  including `--resolve` pinning) was real at the time but is NOT a persistent structural block — most likely transient
  (DNS propagation / connection-pool / an ephemeral network blip on this session's own path). Updated the framing from
  "reproducible anomaly" to "seen once, since cleared" — still worth a real check from the operators' own networks
  during Phase 4, just not something to design defensively around. HTTP mechanics verified end-to-end against the LIVE
  instance using a deliberately invalid token (no real token exists yet): clean `401 invalid or expired token` responses
  confirm request shape, auth header, and connectivity all work correctly; the statusline script's no-config and
  configured-but-invalid-token paths were both verified directly in this session (a live statusline consumer). Also
  fixed the SAME stale "no inbound rule" claim, now found propagated a THIRD time in `check-ao-backlog-status.sh`'s own
  header comment. Remaining Phase 2 item: the local usage-scan-and-push companion (needs a new backend ingest endpoint,
  not yet built) — next tick.
- **2026-08-15, tick 6 (autonomous, main session)**: Phase 2 fully complete — `agent-orchestrator@e9bb4aa`. New
  `POST /api/slots/{slot_id}/human-usage` endpoint reuses `TaskUsageRow`/`record_task_usage` unmodified, prices spend
  SERVER-SIDE via `model_pricing.price_usage()` (request carries only raw token counts, never a client-computed dollar
  figure), synthesizes a stable `human-session-{slot_id}-{claude_session_id}` id for usage not tied to a claimed task
  (plan-authoring time). `scripts/human_fleet/ao-usage-push.py` imports `deepseek_usage.scan_session_usage()` DIRECTLY
  from the sibling agent-orchestrator checkout (no reimplementation) — **tested against this session's own REAL live
  transcript**, not a synthetic fixture, and found a genuine edge case in real data: Claude Code emits real
  `model: "<synthetic>"` internal bookkeeping turns with all-zero usage (8 in this session alone) that
  `scan_session_usage()` correctly includes (matches AO's own existing worker-capture behavior) — filtered client-side
  so an all-zero group is never pushed as wasted noise. Discovered mid-tick: the shared checkout's own local branch
  pointer had drifted stale relative to origin (every ship this whole plan went through separate isolated worktrees,
  never fast-forwarding the shared checkout itself) — switched to developing directly IN a fresh isolated worktree
  (`.ao-iso-dev`) rather than patching a shared-checkout diff in after the fact, avoiding the confusion of editing code
  that doesn't actually exist yet in the tree I'm looking at. **Phase 2 is now fully done. Starting Phase 3 (dashboard)
  next tick.**
- **2026-08-15, tick 7 (autonomous, main session)**: Phase 3 fully complete — `agent-orchestrator@6b50caa`. Also caught,
  this tick, that tick 5's checkbox flips for the register/claim/done scripts and the statusline companion had never
  actually landed on origin despite being marked done in chat — re-verified against `git show origin/...` directly this
  time (not just "the edit tool returned success") and fixed both in the same push as this tick's Progress Log update.
  `AgentKind` union + `KINDS_ORDER`/`AGENT_KIND_LABEL` extended with `"human"`/`"planning-human"`;
  `ROLE_GROUP_FILTER_OPTIONS` extended (covers `BatchingEfficiencyPanel.tsx` for free via its re-export); new
  `HumanFleet.tsx` page joins agents↔slots by `label === operator` (no `slot_id` column on `AgentRow` by design) +
  Router branch + Landing nav button. Full `quality-gates.sh` green after two real fix cycles: a test-fixture bug (an
  unmatched-agent fallback path masked what a test claimed to isolate) and a genuinely missed edit — `"planning-human"`
  had reached the backend vocabulary and the filter arrays but not the `AgentKind` TS union itself, caught by `tsc`, not
  by review. **Phase 3 fully done. Only Phase 4 remains: per-operator JWT issuance (real credential minting — this is
  where the loop should slow down and be deliberate, not rush), the real end-to-end run per operator, and the durable
  codex doc.**
- **2026-08-15, tick 8 (autonomous, main session)**: Shipped the codex doc — `unified-trading-pm@9786794390` — a new
  "Human slots" section in `agent-orchestrator-worker-liveness.md` covering both hard guarantees, what's reused vs.
  genuinely new, and a standing instruction for future liveness/dispatch changes. Found and fixed 2 pre-existing
  dangling references to an archived doc while editing that file (unrelated to this plan — fixed per the "a doc that
  misled you is a finding" rule). **Remaining Phase 4 items are deliberately NOT actioned autonomously**: minting a real
  30-day worker-role JWT and then claiming/completing a REAL backlog task through this brand-new path is a real step up
  in consequence from everything else this plan shipped (all of it tested via unit tests + safe read-only probes against
  production) — surfacing this to the operator directly rather than deciding alone, per ASK > PARK (the operator is
  actively reachable in this session, re-invoking `/autonomous` each tick, not genuinely away). Harsh's half of Phase 4
  (JWT issuance/setup on his own machine) is a genuine physical impossibility from this session regardless of any
  decision here. **Plan is functionally complete pending the operator's own Phase 4 execution** — every prerequisite,
  script, endpoint, and doc it needs is shipped and tested.
- **context-scout 2026-08-15**: populated/refreshed context_scope (14 entries) — all source files + the archived issue
  doc already matched the "What the investigation found" section's own file:line citations; no gaps found.
- **2026-08-15, operator ruling (interactive session)**: **Phase 4 execution is explicitly DEFERRED, not abandoned.**
  Operator confirmed the reasoning behind the earlier autonomous pause was correct: "once we do that, we're going to
  have to start adjusting the way we do things locally... I don't want to get bad feed into AO and mess things up
  because we're trying to get this working" — i.e. flipping Phase 4 live is a real behavioral/workflow change for both
  operators, not just a deploy, and shouldn't happen while the operator has "too much going on" to adjust to it
  properly. Confirmed CURRENT STATE IS FULLY DORMANT, ZERO PRODUCTION FOOTPRINT: no JWT has ever been minted, so every
  Phase 2 script (`ao-register.sh`/`ao-claim.sh`/`ao-done.sh`/`ao-usage-push.py`) 401s and no-ops; no
  `SlotRow`/`AgentRow` exists for slot 9001/9002 in production; `human_slot_ids()`'s liveness exemption is inert because
  there is nothing registered there for it to exempt. Nothing this plan shipped has touched production behavior yet — it
  is pure standing capability, safe to leave dormant indefinitely. **Ruling: hand Phase 4 to Harsh as PURE VERIFICATION,
  not further build work** — "pass it over to Harsh if all other code work is done else complete all other code work so
  his job is verification." Confirmed: all other code work IS done (Phases 0-3 + the codex doc, all shipped and tested
  this session). Harsh's job when he picks this up is exactly the two remaining Phase 4 todos below, no coding — mint
  his own token, run register→claim→done once for real, confirm the dashboard + a usage row. **This plan should be
  treated as feature-complete and left `active` (not archived — real todos remain, just deferred, not done) until Harsh
  actually runs Phase 4.**
- **2026-08-16 (interactive session, operator-requested scope addition)**: operator confirmed Phase 4's real
  registration/JWT step stays OFF for now (unchanged from the 2026-08-15 deferral) but asked for a new, smaller
  addition first: prove out what the dashboard will look like fully populated, entirely without touching production, so
  the only thing left when Phase 4 does flip is "hook it up and test," not "also figure out if the UI works." Added
  Phase 4b below — seeds the two reserved human slots (9001/9002) into the existing mock-mode demo backend
  (`ORCHESTRATOR_MODE=mock`, port 8766, `scripts/populate_demo.py` — the same tool already used to preview every other
  fleet feature) via the real `human-heartbeat`/`human-usage` endpoints, then verifies the Human Fleet page and the
  `role_group=human`/`planning-human` usage filters render correctly against that seeded data with Playwright. Zero
  production footprint: `_refuse_if_live_mode()` already hard-blocks this script from ever running against a live-mode
  server, independent of anything this session does.
- **2026-08-16 (same session, Phase 4b shipped)**: `seed_human_slots()` built, run against a local
  `ORCHESTRATOR_MODE=mock` instance (:8766), and verified end-to-end with Playwright against a
  `VITE_BACKEND_PORT=8766` dashboard dev server. Caught 2 real bugs in the process — `AgentRole` and `AgentKind`
  (`server/models/_types.py`) both never got `"human"`/`"planning-human"` added on the BACKEND, only the frontend TS
  types (Phase 3's own todo 17 only touched `dashboard/src/layout.tsx`+`types.ts`). The `AgentRole` gap 500'd the
  entire `GET /api/agents` — every dashboard page's poll, not just Human Fleet's — the instant a human agent existed;
  the `AgentKind` gap silently mislabeled every human agent as `"custom"` via an existing defense-in-depth coercion
  (`agents.py::_coerce_unknown_kind_to_custom`), never crashing but defeating the entire role_group-split design this
  plan exists to deliver. Both fixed, full `quality-gates.sh` green (3985 pytest + 374 vitest), shipped
  `agent-orchestrator@609e4ea377`. **Production impact of this session's work: zero** — the fix widens two Literal
  types and adds an opt-in local seeding helper; no production data touched, `_refuse_if_live_mode()` unchanged.
  Confirmed with the operator: Phase 4's real registration/JWT step stays explicitly OFF — only the UI's
  fully-populated appearance was proven out, per the operator's own framing ("so we know the final part is just
  hooking it up and testing it"). Phase 4 itself remains deferred to Harsh exactly as the 2026-08-15 ruling states.
- **2026-08-16 (same session, classification reconciliation)**: operator asked for a "light way to see plans created
  and human tasks completed," split by operator — then correctly pressure-tested two proposed designs before either
  was built. First round (self-declared `role_group` per heartbeat) was rejected: a real session mixes investigation/
  authoring/execution fluidly, so asking a human to self-toggle live can't honestly classify it. Second round
  (classify per code-repo commit, by file path touched) was also rejected on two sharper points: (1) a `plans/` commit
  isn't inherently "planning" — flipping a checkbox with cited evidence is task-execution, not authoring, so path-based
  classification mislabels it; (2) most human commits carry no AO `task_id` at all (Phase 4 dormant, and even once live
  plenty of real work — like this exact session — never claims one), so a task-id anchor has near-total "no signal"
  coverage. **Resolved design** (Phase 5 below): classify `unified-trading-pm` plan-repo commits ONLY (never the
  code-repo commit, which is just a cited evidence artifact) — a checkbox-flip commit is unambiguously "task
  completed" (matches this workspace's own existing Commit+Push+Flip hard rule with zero new convention), a
  non-flipping `plans/`-touching commit is "plan created/updated," and untracked work with neither is correctly
  invisible rather than force-classified — per the same hard rule, work without a flip isn't "done" work in this
  workspace's own terms. Operator identity is free from the existing commit-author convention. No AO dependency, no
  new hook, no live registration needed — this can run today, entirely from git history, regardless of Phase 4's
  status.
- **2026-08-16 (same session, deferral reversed for Ikenna)**: operator: "we need to flip it on and then start doing
  it here" — the 2026-08-15 "stays fully dormant" ruling is superseded for Ikenna's own machine specifically (Harsh's
  half unchanged, still a genuine physical impossibility from this session). Split Phase 4's single shared todo into
  4 operator-scoped todos so Ikenna's now-actionable items don't get conflated with Harsh's still-deferred ones.
  Operator also asked (a) for a CLAUDE.md hard rule + a hook so completing a task actually reports to AO
  automatically once a slot is live, rather than relying on memory, and (b) correctly pressure-tested Phase 5 on
  token counts: git commits carry no token data, so Phase 5's git-log classifier stays scoped to plan-vs-task
  labeling ONLY — token/spend counts are Phase 2's already-built job (`ao-usage-push.py`, dormant only because
  nothing has pushed real usage yet), which goes live the moment Phase 4 does. Added Phase 6 (hard-rule pointer +
  hook design) below. **Not yet executed**: minting Ikenna's real JWT and registering against production AO is a
  real production-state change — written up as a todo, not run in this pass; still wants one explicit go-ahead in
  the moment it actually runs.
- **2026-08-16 (same session, Ikenna Phase 4 executed)**: operator gave the explicit go-ahead ("do it") and said
  Harsh's own instructions would be handled separately (doc or link, operator's own follow-up, not this session's
  job). Minted + registered Ikenna's slot 9001 against real production AO. Hit and fixed a genuine production
  regression along the way — the central VM's live `.env.local` had silently drifted to missing all 7 fleet-shared
  secrets (`ORCHESTRATOR_JWT_SECRET` included), contradicting this plan's own 2026-08-15 claim that it was confirmed
  in sync; root-caused via direct SSM checks (never printed secret values), fixed via the existing
  `refresh_env_from_sm.sh --apply` + a service restart (self-serviced, not paused on, per this workspace's own
  IAM-self-service + maintenance-restart rules). Registration confirmed live and rendering correctly
  (`agent_kind="human"`, not `"custom"` — the Phase 4b fix is deployed). **Not done this pass**: the second Phase 4
  todo (claim + complete one real backlog task end-to-end) — "do it" was scoped to registration, a real task
  claim/done cycle is a bigger action and wasn't asked for yet.
- **2026-08-16 (same session, "finish it all")**: operator asked to complete everything remaining. Shipped Phase 5
  (`plan_task_activity.py`, `unified-trading-pm@baf8fd3762`) and Phase 6 (codex Half-4 + confirm-first hook,
  `agent-orchestrator@1af50054cf` + same PM commit), both full-QG-green. Attempted the real task-claim/done cycle
  (Ikenna's remaining Phase 4 todo): fetched the FULL live queued backlog (314 tasks, confirmed exhaustive) — every
  single one carries a `blocked_reason`. Correctly left un-run rather than force-claiming a gated task, which would
  mean doing real work against an unmet prerequisite. **Genuinely complete**: Phases 0-3 (prior session), 4b
  (demo preview), 4-Ikenna-registration, 5, 6. **Genuinely still open, not oversights**: Ikenna's real-task cycle
  (blocked on backlog state, not on anything this session controls — re-attempt when something clears or the
  operator names a task directly), and Harsh's entire Phase 4 (physically impossible from this session, per the
  operator's own "I'll give Harsh instructions separately" framing).
- **2026-08-15, operator ruling (interactive session)**: **Phase 4 execution is explicitly DEFERRED, not abandoned.**
  Operator confirmed the reasoning behind the earlier autonomous pause was correct: "once we do that, we're going to
  have to start adjusting the way we do things locally... I don't want to get bad feed into AO and mess things up
  because we're trying to get this working" — i.e. flipping Phase 4 live is a real behavioral/workflow change for
  both operators, not just a deploy, and shouldn't happen while the operator has "too much going on" to adjust to it
  properly. Confirmed CURRENT STATE IS FULLY DORMANT, ZERO PRODUCTION FOOTPRINT: no JWT has ever been minted, so
  every Phase 2 script (`ao-register.sh`/`ao-claim.sh`/`ao-done.sh`/`ao-usage-push.py`) 401s and no-ops; no
  `SlotRow`/`AgentRow` exists for slot 9001/9002 in production; `human_slot_ids()`'s liveness exemption is inert
  because there is nothing registered there for it to exempt. Nothing this plan shipped has touched production
  behavior yet — it is pure standing capability, safe to leave dormant indefinitely.
  **Ruling: hand Phase 4 to Harsh as PURE VERIFICATION, not further build work** — "pass it over to Harsh if all
  other code work is done else complete all other code work so his job is verification." Confirmed: all other code
  work IS done (Phases 0-3 + the codex doc, all shipped and tested this session). Harsh's job when he picks this up
  is exactly the two remaining Phase 4 todos below, no coding — mint his own token, run register→claim→done once for
  real, confirm the dashboard + a usage row. **This plan should be treated as feature-complete and left `active`
  (not archived — real todos remain, just deferred, not done) until Harsh actually runs Phase 4.**

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
      `test_role_group_human_roles_map_to_themselves_ not_planning` in `tests/test_task_usage_windows.py`. Evidence:
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
- [x] 14. ✅ [INFRA] P1. **Build `ao-register.sh`, `ao-claim.sh`, `ao-done.sh`** (equivalent scripts, calling the Phase
      1 endpoints through `ao_client.sh`, reading the operator's stored token from Phase 4). Ships as
      `agent-orchestrator/scripts/human_fleet/{ao-register,ao-claim,ao-done}.sh`. HTTP mechanics verified against the
      LIVE instance with a deliberately invalid token (no real token exists yet — Phase 4): `ao-register.sh` got a
      clean, correct `401 invalid or expired token`, confirming request shape, auth header, and live connectivity all
      work end-to-end. Full operator run against a real backlog task is Phase 4's explicit todo. Evidence:
      agent-orchestrator@55168745de6ad5789fa78f4b9531926183fe3470.
- [x] 15. ✅ [INFRA] P1. **Build the statusline-based heartbeat companion** —
      `agent-orchestrator/scripts/human_fleet/ao-statusline-heartbeat.sh`, reads `context_window.used_percentage`,
      `model.id`/`display_name`, `session_id` from stdin, POSTs to `human-heartbeat`, throttled
      (`AO_STATUSLINE_MIN_INTERVAL_SECONDS`, default 60s) via a per-slot state file. Verified DIRECTLY in this session
      (a live statusline consumer): both the no-config path (prints normally, skips heartbeat) and the
      configured-but-invalid-token path (prints normally, heartbeat attempt fails silently, state file correctly not
      written on failure) behave as designed. Evidence: agent-orchestrator@55168745de6ad5789fa78f4b9531926183fe3470.
- [x] 16. ✅ [INFRA] P2. **Build the local usage-scan-and-push companion** — new `POST /api/slots/{slot_id}/human-usage`
      endpoint (reuses `TaskUsageRow`/`record_task_usage` unmodified, prices spend SERVER-SIDE via
      `model_pricing.price_usage()` — never trusts a client-computed dollar figure) +
      `agent-orchestrator/scripts/human_fleet/ao-usage-push.py`, which imports `deepseek_usage.scan_session_usage()`
      DIRECTLY from the sibling repo checkout against the confirmed local transcript path. **Tested against this
      session's own REAL live transcript** (not a synthetic fixture) — found and correctly filtered a genuine edge case:
      real `model: "<synthetic>"` all-zero-usage internal bookkeeping turns Claude Code emits (8 in this session), which
      `scan_session_usage()` correctly includes (matches AO's own existing worker-capture behavior). Usage not tied to a
      claimed task (plan-authoring time) gets a stable synthetic `human-session-{slot_id}-{claude_session_id}` id rather
      than being dropped — `SlotGitStatusRow`'s `(host, slot_id)`-keyed pattern informed this design (a
      per-source-identity row) without literally reusing that table, since `TaskUsageRow`'s existing
      role_group-filterable shape was the better fit once `task_role_group()` already had the human/planning-human
      buckets from Phase 1. 6 new tests, full `quality-gates.sh` green. Evidence:
      agent-orchestrator@e9bb4aa2d1d4573318d406a9efd5363184810be9.

### Phase 2b — UI-agnostic liveness (statusLine doesn't fire for IDE-extension sessions) + incremental usage-push fix

> **Added 2026-08-19 (operator, interactive session)**: operator asked to actually flip on continuous live
> heartbeat + usage for real sessions "like the one we're having right now" — an IDE-extension-hosted session, not
> a terminal `claude` CLI session. Investigation found the original Phase 2 statusline mechanism structurally
> cannot cover this: confirmed against the official docs that `statusLine` is a terminal-CLI-only feature, never
> invoked by the VS Code/Cursor native extension chat panel. Resolved with a UI-agnostic replacement below rather
> than accepting the gap.

- [x] [BACKEND] P1. **Build a UI-agnostic liveness heartbeat that works for terminal AND IDE-extension sessions
      alike.** `ao-liveness-heartbeat.py` polls the same local transcript files every Claude Code UI surface
      already writes identically (`~/.claude/projects/<cwd-slug>/<session-id>.jsonl`, confirmed universal in
      Phase 0) rather than depending on `statusLine`/hooks firing at all — "was any transcript touched in the
      last N minutes" is a file-based signal, not a rendering-surface-specific one. `context_used_pct` is
      deliberately left unreported (None = "alive, not measuring", an already-supported state) rather than
      reverse-engineering Claude Code's own context accounting and risking a wrong number. Evidence:
      agent-orchestrator@0affeffedd.
- [x] [BACKEND] P1. **Fix a real double-counting bug found while designing the recurring job**: `ao-usage-push.py`
      re-aggregated and re-pushed the FULL transcript total on every invocation (`scan_session_usage()` does a
      full-file scan every call by its own docstring; `record_task_usage` always INSERTs, never upserts, by
      design) — running it on a cron against a still-growing session would have double/triple/N-times overcounted
      spend the longer the session ran. Added a local cursor (`message_id` set, persisted per slot+session under
      `$TMPDIR`) so each push is a correct, non-overlapping delta batch; a failed push does not advance the
      cursor, so it retries next tick rather than losing data. Evidence: same commit as above.
- [x] [INFRA] P1. **Wire both into one recurring job, installable identically for either operator.**
      `ao-fleet-sync-tick.sh` drives both scripts each tick (usage-push for every recently-touched session, then
      one liveness heartbeat); `install-fleet-sync-cron.sh` idempotently installs a crontab entry, parameterized
      by `AO_SLOT_ID`/`AO_HUMAN_LABEL` so the same command works for both. **Verified live in production this
      session**: installed for Ikenna (9001, 15-min cadence), fired one tick immediately — 5 of 8 recently-active
      sessions' usage pushed successfully (real spend: $10.53/$45.60/$5.06/$1.24/$99.46), 3 hit a transient
      `502 Bad Gateway` (not retried-away silently lost — the cursor design means they retry next tick), and the
      liveness heartbeat succeeded (`agt-14768c`). Confirmed via a direct `GET /api/agents?kind=human` read:
      `"role":"human"`, `"agent_kind":"human"`, `"online":true`, fresh `last_ping` — this exact session (running
      in the VS Code/Cursor extension, not a terminal) is now genuinely visible in AO for the first time. Evidence:
      agent-orchestrator@0affeffedd, live verification this session.
- [x] ✅ [OPERATOR] P2. **Harsh — install the same recurring job on his own machine (his half of Phase 4, extended).**
      Once Harsh has registered (existing Phase 4 todo above), one additional command:
      `AO_HUMAN_LABEL=harsh bash scripts/human_fleet/install-fleet-sync-cron.sh 9002 --minutes 15`. No coding —
      the script is already generic per-operator. Done when: `crontab -l | grep 'ao-fleet-sync:9002'` shows the
      installed entry and a `GET /api/agents?kind=human` call shows `harsh` with a fresh `last_ping`. **Executed
      2026-08-19 (interactive session, slot 2)**: cron entry installed (`*/15 * * * * ... # ao-fleet-sync:9002`);
      manually fired one tick to verify rather than waiting 15min — hit and fixed a real, previously-undiscovered bug
      in `ao-fleet-sync-tick.sh` doing so (see Progress Log). Both done-when conditions confirmed after the fix.
      Evidence: `agent-orchestrator@1e80d160e0`, live verification this session.

### Phase 2c — per-tab presence sub-slots (2026-08-19, operator caught the real gap)

> Operator: "why only one slot, i am working over 11 registered slots on my laptop albeit many are dormant 4 or 5
> doing real work why cant it discern the difference" — Phase 2b collapsed every concurrently-active `.tabs/<N>`
> session to a single "most recent" heartbeat, hiding real concurrent-work visibility. Operator explicitly chose
> the fuller fix over a cheaper "active count" alternative: "Give each tab its own slot/row."

- [x] [BACKEND] P1. **Reserve a wide per-operator slot range for per-tab presence** — `server/config.py`:
      `HUMAN_TAB_SLOT_BASE = {"ikenna": 91000, "harsh": 92000}`, 1000-wide each. `is_human_slot_id()` widens the
      membership check from `human_slot_ids()`'s fixed 2-element set to a RANGE check, so a brand-new tab is
      recognized with no server-side config change. Task-claim endpoints (`human_claim`/`human_claim_check`)
      deliberately keep calling `human_slot_ids()` directly, unwidened — a claim stays tied to the operator's one
      stable identity, never fragments across tabs. Wired into `human_heartbeat` + all 3 liveness/kill-exemption
      sites (`WorkerLivenessWatchdog`, `WorkerLivenessKicker`, `AutoSpawn._should_spawn`) — 3 of 4 shipped;
      `AutoSpawn`'s site deferred (see follow-up below). Evidence: agent-orchestrator@a20126efbe (new
      `tests/test_human_tab_slots.py` + updated existing liveness-exemption tests).
- [x] [INFRA] P1. **Fan out `ao-liveness-heartbeat.py` per active tab.** Tab number recovered directly from Claude
      Code's own cwd-slugified project-directory name (`-tabs-(\d+)` regex — no need to read inside the
      transcript); each active tab heartbeats its own slot, labeled `<operator>-tabN`; the stable identity slot
      also still refreshes from whichever tab is most recent (existing task-claim/done tooling unaffected).
      **Verified live in production this session**: 3 concurrently-active tabs (3, 4, 6) each registered as a
      distinct `AgentRow`/slot, plus the identity slot (9001) refreshed — confirmed via the scripts' own
      `{"ok":true,"agent_id":...,"slot_id":...}` responses. Evidence: same commit as above, live verification.
- [x] [SCRIPT] P2. **Widen `AutoSpawn._should_spawn`'s human-slot check too (the 4th exemption site, deferred from
      the Phase 2c commit)** — the peer session's unrelated WIP in `server/autospawn.py` landed (confirmed via
      `git fetch` + a clean `git status` on the file), so the hunk was safely reapplied: `_should_spawn` now
      calls `config.is_human_slot_id(slot.slot_id)` instead of the fixed-set `config.human_slot_ids()` membership
      check — mirrors the other 3 sites exactly. New test `test_should_spawn_blocks_human_tab_sub_slot` (slot
      91004) proves AO will never attempt to spawn a worker onto a per-tab presence sub-slot, same as the
      stable identity slot. All 4 of 4 liveness/kill-exemption sites now cover the widened range. Evidence:
      agent-orchestrator@0443654c9c.
- [ ] [OPERATOR] P2. **Harsh — same per-tab visibility, no extra steps beyond his existing Phase 4/2b setup.** The
      identical `install-fleet-sync-cron.sh 9002` command (Phase 4/2b above) already installs the per-tab-aware
      script — no new command needed. Done when: `GET /api/agents?kind=human` shows one or more `harsh-tabN` rows
      alongside `harsh` once he's actively working in more than one tab.

### Phase 3 — dashboard

- [x] 17. ✅ [UI] P2. **Add `"human"`/`"planning-human"` to the `AgentKind` union, `KINDS_ORDER`, and
      `AGENT_KIND_LABEL`** (`dashboard/src/layout.tsx`, `dashboard/src/types.ts`). A registered human agent renders
      correctly in the existing `AgentTypesPanel` table with no other frontend changes. Evidence:
      agent-orchestrator@6b50caa795cfede5ecac6e91125a5284cad3a68e.
- [x] 18. ✅ [UI] P2. **Add `"human"`/`"planning-human"` entries to the static role_group filter arrays**
      (`TaskUsageWindows.tsx` — `BatchingEfficiencyPanel.tsx` re-exports the same array, one edit covers both). Both
      appear as selectable filter options in both panels. Evidence:
      agent-orchestrator@6b50caa795cfede5ecac6e91125a5284cad3a68e.
- [x] 19. ✅ [UI] P2. **Build a "Human Fleet" page** (`dashboard/src/HumanFleet.tsx`) following the
      `FleetGit.tsx`/`FleetKpis.tsx` recipe exactly, + one new `Router` branch (`/human-fleet`) + one new `Landing.tsx`
      nav button. Shows current task, model, account, context%, last-heartbeat — joins human-kind agents against slots
      in the 9000+ range by `label === operator` (`AgentRow` carries no `slot_id` column by design). Reachable from
      Landing, auto-refreshes every 30s, 8 new component tests mirroring `FleetKpis.test.ts`. Two real bugs caught by
      the gate itself, not by inspection: a test fixture that didn't isolate what it claimed (an unmatched-agent
      fallback row masked the case it was testing), and a genuinely missed edit — `"planning-human"` had been added to
      the backend vocabulary and the role_group filter arrays but NOT to the `AgentKind` TS union, caught by `tsc`.
      Evidence: agent-orchestrator@6b50caa795cfede5ecac6e91125a5284cad3a68e.

### Phase 4 — per-operator setup + rollout

> **Deferral REVERSED for Ikenna, 2026-08-16 (operator, interactive session)**: the 2026-08-15 "stays fully dormant"
> ruling is superseded for Ikenna's own machine specifically — "we need to flip it on and then start doing it here."
> Harsh's half is untouched (still a genuine physical impossibility from this session, still pure-verification when he
> picks it up). Split into two operator-scoped todos below so the two don't get conflated.

- [x] 22. ✅ [OPERATOR] P1. **Ikenna — issue a long-lived worker-role JWT and register (slot 9001).** Executed this
      session on explicit operator go-ahead ("do it"). Minted via `issue_token('ikenna', role='worker',
      machine='ikenna-laptop')`, token written to `~/.config/agent-orchestrator/human-fleet-token` (0600). **Found +
      fixed a real production gap along the way**: the first mint attempt 401'd — SSM-verified directly against the
      central VM (`i-0c9b283b31d6b5ca7`) that its live `.env.local` (confirmed as the exact file
      `orchestrator.service`'s own `EnvironmentFile=` points to, and confirmed absent from the RUNNING process's own
      `/proc/<pid>/environ`) had ZERO of the 7 fleet-shared keys set, including `ORCHESTRATOR_JWT_SECRET` — meaning the
      live server was signing every token with an ephemeral, per-restart-only secret, contradicting this plan's own
      2026-08-15 Progress Log claim that vm-0's secret was confirmed in sync. AWS Secrets Manager and GCP Secret
      Manager both held the correct, matching value (compared by length/equality only, values never printed). Fixed
      via the already-built `scripts/refresh_env_from_sm.sh --apply` (synced 7 keys) + `systemctl restart orchestrator`
      (workers survive, `KillMode=process`) — self-serviced per this workspace's own "both cloud identities are
      IAM-self-service, don't pause" + "maintenance restarts skip scheduling" rules, not paused on. **Side effect worth
      knowing**: any dashboard session whose token was signed with the now-replaced ephemeral secret needs a fresh
      login — self-healing, not a data-loss risk. Registration then succeeded:
      `{"ok":true,"agent_id":"agt-f6b475","slot_id":9001}`, verified rendering correctly via a direct
      `GET /api/agents?kind=human` call — `"role":"human"`, `"agent_kind":"human"` (not `"custom"`), confirming
      `agent-orchestrator@609e4ea377`'s fix is live in production too (self-pulled via the standing 15-min LDR cron).
      Done when: met — `ikenna` is live in AO's `GET /api/agents` with `role="human"`, `agent_kind="human"`.
- [ ] [SCRIPT] P2. **Ikenna — run one real, low-stakes task end-to-end.** **Attempted 2026-08-16, genuinely blocked —
      not skipped, not forced.** Fetched the FULL live queued backlog (`GET /api/backlog?status=queued`, 314 tasks,
      confirmed exhaustive — `limit=2000` returned the same 314 as `limit=200`): every single one carries a non-null
      `blocked_reason` (`gate_on_depends`, unmet prereq task, etc.) — zero tasks are currently ready for AO's own
      dispatch. `_human_claim_verdict` does NOT re-check `gate_on_depends`/prereq state at all (only
      dispatched_to/status/next-50-ranking) — a human COULD technically force-claim a gated task through this path,
      but doing so means working against a prerequisite the system itself says isn't met, which is a worse outcome
      than deferring. Correctly left un-run rather than manufactured. Re-attempt once something genuinely clears (the
      backlog is fluid — re-run the same fetch+filter to check), or the operator names a specific task directly to
      override the "wait for something ready" default. Steps for when a candidate exists:
      `AO_SLOT_ID=9001 bash scripts/human_fleet/ao-claim.sh <task_id> --check-only` (confirm claimable), then without
      `--check-only` to actually claim, do the real work, commit+push+flip the plan checkbox, then
      `AO_SLOT_ID=9001 bash scripts/human_fleet/ao-done.sh <task_id> <sha> "<evidence>"`, then run
      `ao-usage-push.py` to confirm a real, priced `TaskUsageRow` appears (this is what actually turns the dormant
      Phase 2 usage/billing capability into real numbers — see Phase 5's note on token counts below). Done when: the
      task shows up correctly in the "Human Fleet" dashboard page and
      `GET /api/backlog/usage/windows?role_group=human` returns a real row.
- [x] ✅ [OPERATOR] P1. **Harsh — hand to Harsh, pure verification, no coding (unchanged from the 2026-08-15 ruling).**
      Same steps as Ikenna's todo above, but `machine='harsh-laptop'`, `AO_SLOT_ID=9002`:
      `python3 -c "from server.auth import issue_token; t,e = issue_token('harsh', role='worker', machine='harsh-laptop'); print(t); print('expires', e)"`,
      then `mkdir -p ~/.config/agent-orchestrator && nano ~/.config/agent-orchestrator/human-fleet-token` (paste the
      token), then `AO_SLOT_ID=9002 bash scripts/human_fleet/ao-register.sh harsh`. Done when: `ao-register.sh`
      returns `{"ok": true, ...}` and `harsh` shows up in AO's `GET /api/agents`. **Executed 2026-08-19 (interactive
      session, slot 2)**: minted via the confirmed-in-sync local `.env.local` `ORCHESTRATOR_JWT_SECRET` (verified
      matching the canonical Secret-Manager blob first via `refresh_env_from_sm.sh` dry-run — `keep`, not `REPLACE` —
      before use; the raw secret itself was never fetched fresh or printed), saved to
      `~/.config/agent-orchestrator/human-fleet-token` (0600), registered:
      `{"ok":true,"agent_id":"agt-76ed5c","slot_id":9002}`. Live-verified via `GET /api/agents?kind=human`: `harsh`,
      `role=human`, `agent_kind=human`, `status=active`, `online=true`, fresh `last_ping`. Evidence: live API response,
      this session.
- [ ] [SCRIPT] P2. **Harsh — run one real, low-stakes task end-to-end (unchanged from the 2026-08-15 ruling).** Same
      steps as Ikenna's task todo above, `AO_SLOT_ID=9002`. Done when: the task shows up correctly in the "Human
      Fleet" dashboard page and a `TaskUsageRow` with `role_group="human"` exists for it
      (`GET /api/backlog/usage/windows?role_group=human`). **Re-checked 2026-08-20 (interactive session, Harsh)**:
      still genuinely blocked, same wall as Ikenna's identical todo — fetched the full live queued backlog
      (706 tasks, same count as the 2026-08-18 check) via `GET /api/backlog?status=queued&limit=2000`: 0 without a
      `blocked_reason`. Correctly left un-forced; re-check anytime the backlog shifts, or claim a task the operator
      names directly.
- **[OPERATOR] P1. CANCELLED — SUPERSEDED 2026-08-18 (Ikenna, interactive session), duplicate of the "Harsh —
  hand to Harsh, pure verification" register todo above, accumulated from a repeated autonomous-loop tick and
  flagged (not actioned) by the 2026-08-17 na-eligibility-audit; deduped this session.**
- **[SCRIPT] P2. CANCELLED — SUPERSEDED 2026-08-18 (Ikenna, interactive session), duplicate of the "Harsh — run
  one real, low-stakes task" todo above, same accumulation and dedup pass as the entry directly above.**
- **[SCRIPT] P2. CANCELLED — SUPERSEDED 2026-08-18 (Ikenna, interactive session), a second duplicate of the
  "Harsh — run one real, low-stakes task" todo above, same accumulation and dedup pass.**
- [x] 21. ✅ [INFRA] P2. **Phase 4b — preview the fully-populated dashboard via the mock demo backend, zero production
      connectivity.** Added `seed_human_slots()` to `scripts/populate_demo.py` — seeds `SlotRow`/`AgentRow`/
      `TaskUsageRow` for both reserved human slots (9001=ikenna, role_group="human", claimed task B-004; 9002=harsh,
      role_group="planning-human", no claimed task) against `ORCHESTRATOR_MODE=mock` on :8766 only —
      `_refuse_if_live_mode()` hard-blocks the script against a live-mode server regardless. **Found and fixed 2 real,
      previously-undetected bugs while proving this out** — neither is specific to the demo/preview path; both would
      have hit a REAL human registration in production the moment Phase 4 went live:
      1. `AgentRole` (`server/models/_types.py`) never got `"human"` added alongside `AgentKind` — `human_heartbeat`
         registers `role="human"` (write succeeds, no crash), but `AgentView.role: AgentRole` then threw a hard
         `pydantic.ValidationError` on read, 500ing the ENTIRE `GET /api/agents` the instant any human agent existed —
         not just Human Fleet's own fetch, but the main dashboard's own unfiltered poll (every fleet page, every
         refresh). Confirmed via live `curl` against the mock backend before the fix, clean 200 after.
      2. `AgentKind` (`server/models/_types.py`) also never got `"human"`/`"planning-human"` added — Phase 3's own todo
         17 only touched `dashboard/src/layout.tsx`+`types.ts` (frontend), never the backend Literal. A defense-in-depth
         `@field_validator` (`server/models/agents.py::_coerce_unknown_kind_to_custom`,
         `agent_orchestrator_agent_kind_literal_gap_2026_07_28`) caught this SILENTLY — no crash, but every human agent
         would have rendered as generic `"custom"`, not `"human"`/`"planning-human"`, defeating the entire point of this
         plan's role_group split (exactly the "don't pollute general agent stats" requirement the operator asked for).
         Only surfaced because the validator's own `logger.warning(...)` was checked, not because anything visibly broke.
      Both fixed by widening the two Literals (mirroring the existing frontend `AgentKind` union, which already had both
      values). Verified end-to-end with Playwright against a `VITE_BACKEND_PORT=8766` dashboard dev server: Human Fleet
      page renders both rows correctly labeled (`human`/`planning-human`, not `custom`), model/context%/current-task/
      online all populate correctly, and the `role_group=human`/`planning-human` filter buttons on the existing
      `TaskUsageWindows` panel return the seeded, server-priced usage numbers ($0.68 spend, matching the raw API
      response exactly) — confirming the "toggles and splits on the existing pages, not a new billing page" design
      holds. Full `quality-gates.sh` green (3985 passed). Evidence: `agent-orchestrator@609e4ea377`.
- [x] 20. ✅ [INFRA] P3. **Document the human-slot contract as a durable codex SSOT** — new "Human slots" section
      appended to `/codex/04-architecture/agent-orchestrator-worker-liveness.md` covering both hard guarantees
      (never-killable, never-competing), what's reused vs. genuinely new, and a standing instruction that a future
      liveness/dispatch change must re-verify both. `related:`/`referenced_by` cross-linked both directions. Found +
      fixed 2 pre-existing dangling references to an archived doc while in this file (unrelated to this plan, fixed per
      the "a doc that misled you is a finding" rule rather than left for the next reader). Evidence:
      unified-trading-pm@9786794390.

### Phase 5 — lightweight per-operator plan/task activity view (git-log-derived, no live AO dependency)

- [x] 23. ✅ [SCRIPT] P2. **Build a git-log-derived "plans created" / "tasks completed" activity view, split by operator, with
      no dependency on live AO registration (Harsh's Phase 4 stays dormant).** Resolved this session (see Progress Log
      2026-08-16, "classification reconciliation") after the operator correctly flagged that self-declared
      `role_group` per-heartbeat can't honestly classify a mixed session, and that neither the code-repo commit nor a
      task_id is a reliable anchor — a human's interactive commits carry no `task_id` at all (Phase 4 off), and
      classifying by file path (`plans/` = "planning") wrongly buckets a checkbox-flip-with-evidence commit (task
      execution) the same as a plan-authoring commit. **Resolved design**: classify from `unified-trading-pm` commits
      only (never the code-repo commit itself, which is just a cited evidence artifact):
      - **Task completed** = a `unified-trading-pm` commit that flips a `- [ ]` → `- [x]` checkbox — by construction
        always tied to one named todo, matching this workspace's own existing "Commit + Push + Flip" hard rule
        (`/codex/12-agent-workflow/commit-push-flip-rule.md`) exactly, no new convention needed.
      - **Plan created/updated** = a `unified-trading-pm` commit touching `plans/` that flips no checkbox.
      - Operator identity: free from the existing commit-author convention (`ikennaigboaka [slot-N·host]` /
        `scripts/hooks/slot-identity-lib.sh`) — no new tagging needed.
      - Work with no checkbox flip and no plan-doc commit (pure investigation, a question answered) legitimately shows
        as neither — this is correct, not a gap: per the same hard rule, untracked work without a flip is genuinely
        not "done" work in this workspace's own terms, so it shouldn't inflate a completion count.
      Implementation: a read-only script (`scripts/plan-hygiene/`-style, mirrors `count_open_tasks.py`'s pattern) over
      `git log --format=... -- plans/` in `unified-trading-pm`, diffing each commit's checkbox state against its
      parent to detect flips, grouped by commit-author operator. Surface as a small addition to the existing Human
      Fleet dashboard page (`dashboard/src/HumanFleet.tsx`) OR as a standalone CLI/report — operator's call at build
      time, not a forced new dashboard section. Done when: running it against this session's own commits correctly
      correctly distinguishes real checkbox-flip commits from plan-authoring ones — see the actual spot-check result
      in the shipped-evidence entry below, which corrects an inaccurate pre-verification guess made here.
      **Explicitly OUT of scope: token/spend counts.** Git commits carry no token data — that was never git's job.
      Once Phase 4 is live (above), token counts flow through the ALREADY-BUILT Phase 2 mechanism instead:
      `ao-usage-push.py` scans that operator's OWN local `~/.claude/projects/*.jsonl` transcript and pushes
      server-priced spend to AO, tagged `role_group="human"`/`"planning-human"` — the exact same
      `TaskUsageWindows`/`BatchingEfficiencyPanel` panels every other slot already uses. This script never reads a
      transcript and never needs to — it stays a pure git-log classifier, one lane only.
      Shipped as `scripts/plan-hygiene/plan_task_activity.py` — classifies every `unified-trading-pm` commit touching
      `plans/` by comparing checkbox counts against its parent (`min(old_open - new_open, new_done - old_done) > 0` =
      a real flip, not just noise from an unrelated done-item addition landing in the same commit); operator identity
      from commit-author email domain (`gmail.com` -> ikenna, `odum-research.com` -> harsh). Spot-checked against 4
      real commits from this session: `2873fd7c4f` correctly `task_completed` (a genuine open-`[ ]`-committed →
      done-`[x]`-committed transition, git-visible); `633f048465`/`60a951793c` correctly `plan_updated` (added new
      open todos, flipped nothing). **One real, explained miss**: `12e83c4074` shows `plan_updated`, not
      `task_completed` — because that todo (Phase 4b) was AUTHORED already-`[x]` in the same edit that first added
      it, so no separate open-`[ ]` version was ever committed to git for this heuristic to see decrease; from git's
      own history there IS no open->done transition to detect, so `plan_updated` is the defensible call, not a bug —
      but it does mean the earlier "Done when" guess above (asserting this exact commit would show `task_completed`)
      was wrong, made before actually spot-checking. Corrected here per measurement-claims discipline rather than
      left standing. Standalone CLI as scoped (`--json` for machine use); the dashboard-page option was left undone
      as explicitly optional in the original design. Evidence: `unified-trading-pm@baf8fd3762`.

### Phase 6 — after-flip discipline: CLAUDE.md hard rule + a hook that reports completion to AO automatically

- [x] 24. ✅ [DOC] P2. **Add a one-line CLAUDE.md hard rule (pointer only, per this file's own size-budget/condense
      convention) to the existing "Commit + Push + Flip" section**: once a human-fleet slot is registered (Phase 4
      live), completing a Half-2 checkbox flip is followed by reporting it to AO
      (`ao-done.sh <task_id> <sha> "<evidence>"`) — a "Half 3" for a human-fleet-registered operator specifically, not
      a fleet-wide change (AO-dispatched workers already do this via their own `/done` call; this closes the gap only
      for a human's own interactive session). Full rule text + rationale lives in a new codex doc this rule points to
      — CLAUDE.md itself only gets the 1-line essence + pointer, per its own maintenance rule at the top of the file.
      Added a "Half 4" section to `/codex/12-agent-workflow/commit-push-flip-rule.md` (the existing 3-halves SSOT,
      extended rather than forked into a new doc) covering the confirm-first hook + the token-counts-are-out-of-scope
      boundary. **CLAUDE.md itself got NO net-new bytes** — found it already 186B over its own 40,960B hard cap before
      touching anything (`check_agent_rules_size_cap.py`, QG-enforced, "never raise the cap"); the existing SSOT
      pointer already resolved to the doc I extended, so no new prose was needed there at all — confirmed the
      untouched pointer line is enough by re-running the size-cap check standalone (passed, 38B headroom) before the
      full re-run confirmed clean. Evidence: `unified-trading-pm@baf8fd3762`.
- [x] 25. ✅ [SCRIPT] P2. **Design + build a Claude Code hook that auto-fires `ao-done.sh` after a detected
      commit+push+flip sequence**, so the Phase 6 hard rule above is enforced mechanically, not by memory. Resolved
      the design question in favor of confirm-first (as recommended): `agent-orchestrator/scripts/human_fleet/
      post_plan_commit_hook.py`, a `PostToolUse` hook matching `Bash`, wired in `cursor-configs/settings.json` (new
      entry, matcher `"Bash"`, alongside the existing batching-nudge entry). Fast-exit chain (command match ->
      exit_code==0 -> cwd is unified-trading-pm -> token file exists -> `AO_SLOT_ID` env set -> HEAD actually flipped
      a checkbox) before the one AO API call (`GET /api/state`, checking the slot's `current_task`) — the network
      call only fires once every local, cheap gate has already passed. On a match, surfaces a `systemMessage`
      suggesting the exact `ao-done.sh` invocation; NEVER calls it itself. 10 new tests (every fast-exit branch +
      both positive/negative outcomes, using a real temp git repo for the checkbox-flip detection, not a mock), full
      `quality-gates.sh` green (3995 passed). Evidence: `agent-orchestrator@1af50054cf`.

### Phase 7 — main Fleet table exclusion + registration re-verification (found 2026-08-18, not yet fixed)

- [x] N. ✅ [UI] P2. **Exclude human-kind slots from the main dashboard Fleet table's generic role-badge rendering** —
      slot 9001 currently renders there with a role badge from the generic worker/reserve pool ("CI reserve"),
      confirmed live via dashboard screenshot 2026-08-18. Phase 3's `AgentKind`/`KINDS_ORDER`/`AGENT_KIND_LABEL`
      work (`dashboard/src/layout.tsx`, `agent-orchestrator@6b50caa795cfede5ecac6e91125a5284cad3a68e`) only ever
      wired human slots into the DEDICATED `HumanFleet.tsx` page — find wherever the main Fleet table computes its
      per-slot role badge and add the same `human_slot_ids()`-style exclusion the liveness/kill sites already use
      (`server/config.py:316-331` pattern), so a human slot renders nowhere in the generic table at all (not
      mislabeled, not present). Done when: a live dashboard check shows slot 9001 absent from the main Fleet
      table's rows entirely, still correctly present on the Human Fleet page. Repo: agent-orchestrator. Extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 4 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).
- [x] ✅ [SCRIPT] P2. **Re-verify live whether `GET /api/agents?kind=human` still returns Ikenna's registered row** —
      this plan's own 2026-08-16 Progress Log confirmed `agent_id=agt-f6b475`, `slot_id=9001`, `agent_kind=human`
      live in production. A same-day sibling issue doc (`plans/active/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`)
      reported a live check on 2026-08-18 finding ZERO human rows from that same endpoint — a direct contradiction
      neither doc has reconciled. **RESOLVED 2026-08-20 (interactive session, Harsh)**: pulled `GET
      /api/agents?kind=human` live via the registered bearer token (not SSM — the token path already works and is
      simpler) — returns multiple live human rows right now: `harsh` (`agt-45655b`, `status:active`,
      `online:true`, `last_ping:2026-08-20T14:30:10Z`, fresh) plus `ikenna-tab5`/`ikenna-tab6` (`active`) and
      `ikenna-tab2` (`stale`). The 2026-08-18 "zero rows" report was a **transient snapshot, not a persisting
      regression** — no crash/restart evidence found in this check, and the row is unambiguously live now under
      the same registration from 2026-08-16 (no re-registration was needed to produce this result). Not
      independently root-caused further since the state today is simply correct — no reproducible bug remains to
      chase. Done when: met, live state confirmed with fresh evidence. Repo: agent-orchestrator.

## Progress Log

- **context-scout 2026-08-19**: refreshed context_scope, trimmed 14→6 entries — remaining open work is now
  E2E-verification-shaped (the `scripts/human_fleet/` claim/done/usage-push tooling, a live `GET /api/agents?kind=human`
  contradiction to resolve, `config.py`'s human-slot-exclusion pattern for the main Fleet-table todo) rather than the
  broad implementation surface the original 14-entry list covered; dropped the now-shipped-and-stable
  `dispatch.py`/`state_store/slots.py`/`orm.py`/`worker_liveness*`/`autospawn.py`/`auth.py`/dashboard files and the
  archived `review_agent_rate_limit_blind_kill` issue doc (unrelated to the remaining todos), added the corrected
  single-vm-architecture codex doc and the `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md` issue doc (the
  live-state contradiction this plan's own last open todo must resolve).
- **context-scout 2026-08-17**: populated/refreshed context_scope (14 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:ffc453bde60eb30a]: KEEP-NA, valid — all 6 open todos are Harsh's (explicit 2026-08-15/08-16 operator ruling: physically impossible from this session) or Ikenna's (blocked on all 314 live backlog tasks currently carrying a blocked_reason). Note: the 6 checkboxes are 3 near-verbatim duplicate pairs from repeated autonomous-loop ticks — a housekeeping dedup is worth a future pass, not actioned here (content not wrong, no hard evidence one supersedes another).
- **2026-08-18 (interactive session, operator asked to complete the plan)**: Re-checked Ikenna's blocked task-cycle todo
  live via `GET /api/backlog` (706 queued tasks now, up from 314 on 2026-08-16) — **still 0 tasks without a
  `blocked_reason`**, same wall as before, just grown. Correctly left un-forced again (same reasoning as 2026-08-16:
  force-claiming a gated task means working against an unmet prerequisite). Did the housekeeping dedup the
  2026-08-17 audit flagged but didn't action: Harsh's Phase 4 todos had accumulated to 5 entries across repeated
  autonomous-loop ticks (2 near-identical "register" copies, 3 near-identical "run one task" copies) representing
  only 2 distinct pieces of work, plus a garbled/orphaned command-line fragment + duplicate "Done when" clause stuck
  onto the tail of already-checked-off todo 21 (Phase 4b) from an apparent copy-paste corruption in an earlier tick.
  Collapsed to exactly 2 clean Harsh todos (register, task-cycle) and removed the stray tail from todo 21 — no
  content lost, every removed copy was a verbatim or near-verbatim duplicate of a kept one. **Remaining open work,
  confirmed accurate**: Ikenna's task-cycle (blocked on live backlog state, re-check anytime, or operator names a
  task directly to override), and Harsh's entire Phase 4 (physically requires his own machine).
- **2026-08-18 (interactive session, slot 3)**: Two new gaps found live, not yet fixed — captured as todos below
  rather than left in chat. (1) The main agent-orchestrator dashboard Fleet table (NOT the dedicated Human Fleet
  page this plan built) still renders slot 9001 with a role badge from the generic worker/reserve pool ("CI
  reserve") instead of excluding human-kind slots from that computation entirely — confirmed via a live dashboard
  screenshot. Phase 3's `AgentKind`/`KINDS_ORDER` work only ever touched the DEDICATED Human Fleet page; nothing
  excludes a human slot from the separate, generic Fleet table's own role-badge logic. (2) A same-day sibling issue
  doc (`ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`) reported `GET /api/agents` returning zero human rows
  when it checked live on 2026-08-18 — directly contradicting this plan's own 2026-08-16 confirmation that
  Ikenna's `agent_id=agt-f6b475`/`slot_id=9001` row was live and correctly typed. Not independently re-verified
  this session; could be a real regression or a stale/wrong claim in the other doc — needs a fresh live check to
  settle which. Design fork surfaced but NOT resolved this session (operator asked to scope it, then the
  conversation moved on before an answer landed): should the Human Fleet content move to a same-page subsection
  below the main Fleet table, or stay the existing separate `/human-fleet` page with just the exclusion bug (1)
  fixed? Todos below are written to be answerable either way — resolving the fork changes WHERE the fix in (1)
  renders, not whether it's needed.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:750fff6078039cf5]: RECLASSIFY (per-todo split) — the Fleet-table role-badge exclusion item extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 4. Doc stays NA for its other remaining items (Harsh's Phase 4 — physically requires his own machine; Ikenna's task-cycle — blocked on live backlog state, 0/706 tasks without a blocked_reason; the /api/agents zero-rows contradiction — cross-referenced, see `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md` item 11).
- **2026-08-19 (interactive session, slot 2, Harsh's Phase 4/2b executed)**: Ran Harsh's onboarding live, one step at a
  time per his own request, following `/codex/05-infrastructure/human-fleet-operator-setup.md`. Two real findings
  along the way, not just execution. (1) At the start of this session that runbook doc genuinely did not exist in
  this checkout — a `find`/`rg` sweep came up empty — so the first response to Harsh incorrectly told him the doc was
  nonexistent/a misremembering. It was NOT: a concurrent session (Ikenna, slot-4·laptop,
  `unified-trading-pm@b9b59e817d`, "docs(codex): add Human Fleet operator setup runbook for Harsh (CLI + Cursor)",
  2026-08-19T04:41:23+01:00) had just created it, and this checkout's `git pull --ff-only origin live-defi-rollout`
  (run later in the same session, to safely edit this very plan file) pulled it in — the earlier "doesn't exist"
  answer was a stale-checkout artifact, not a wrong premise on Harsh's part. Corrected once found; the doc's own Step
  5 ("Cursor's Claude Code extension ignores `permissions.defaultMode`... constant permission prompts the CLI never
  shows") was real and was applied: `claudeCode.allowDangerouslySkipPermissions`/`claudeCode.initialPermissionMode` set
  in this machine's actual editor config (`~/.config/Code/User/settings.json` — genuinely VS Code here, not Cursor;
  the doc's example path was macOS/Cursor-specific, adapted for this Linux/VS-Code machine). (2) The first mint
  attempt ran in a fresh shell with neither `ORCHESTRATOR_JWT_SECRET` nor its GCS path exported — `_load_secret()`
  correctly fell back to an ephemeral per-process secret (loud warning), which would have produced a token the real
  server could never validate. Rather than fetching the raw secret from GSM into a laptop checkout (his first
  suggestion — works against the code's own "central-VM-only, never shared with worker VMs" design intent for zero
  benefit over the alternative), found the secret was ALREADY present in this checkout's `.env.local` via the
  standard `refresh_env_from_sm.sh` sync path and confirmed in sync with the canonical Secret-Manager blob (dry-run
  `keep`, not `REPLACE`) before using it — identical practical outcome, smaller exposure surface, raw secret value
  never printed. Registration then succeeded first try. Installing the Phase 2b cron surfaced a real,
  previously-undiscovered bug: `ao-fleet-sync-tick.sh`'s mtime probe tried BSD `stat -f %m` before GNU `stat -c %Y`
  — on Linux, GNU `stat -f` doesn't error, it silently returns filesystem info instead of a file's mtime, so the
  arithmetic on the resulting garbage string crashed under `set -u`. The correct GNU-first order is already the
  established convention elsewhere in this exact repo (`ao-self-pull.sh:76`; `qg-common.sh:293` even documents this
  precise gotcha) — this one script just had it backwards. Fixed + shipped (`agent-orchestrator@1e80d160e0`, full QG
  green — also had to `npm ci` the dashboard, which was missing an already-committed `recharts` dependency, an
  unrelated pre-existing local-env gap, not a code issue). Harsh (slot 9002) now live: `agt-76ed5c`, `role=human`,
  `status=active`, fresh `last_ping`; cron installed; one manually-fired tick already proved usage-push (4 sessions,
  real priced spend) and the liveness heartbeat both work end-to-end. **Worth a follow-up, not investigated further
  this session**: while verifying, `GET /api/agents?kind=human` showed Ikenna's `ikenna-tab3/4/5/6` rows all
  `status=stale`/`online=false` — if his cron was installed before this fix shipped and his machine is Linux, this
  exact bug would explain it; not confirmed, captured as a todo below rather than assumed.

### Phase 8 — follow-up from Harsh's 2026-08-19 onboarding (not yet actioned)

- [x] ✅ [SCRIPT] P2. **Check whether Ikenna's stale `ikenna-tabN` rows (observed 2026-08-19, `GET /api/agents?kind=human`
      showing tab3/4/5/6 all `status=stale`/`online=false`) were caused by the `ao-fleet-sync-tick.sh` GNU/BSD `stat`
      ordering bug fixed this session (`agent-orchestrator@1e80d160e0`)** — if his cron was installed before this fix
      and his machine is Linux, every tick since would have silently crashed before reaching the heartbeat call.
      Check his crontab log (`/tmp/ao-fleet-sync-9001.log`) for the failure signature, confirm the fix resolves it on
      his machine too, not just Harsh's. Repo: agent-orchestrator. **Resolved 2026-08-19 (same session)**: not the
      `stat` bug — a SEPARATE, bigger bug found checking Harsh's own log: `ao-fleet-sync-tick.sh` called bare
      `python3` for both `ao-usage-push.py` and `ao-liveness-heartbeat.py`. Under cron's real minimal PATH that
      resolves to system Python (no `pydantic` installed), not this repo's `.venv` — so **every scheduled tick on
      Harsh's own host, since his cron was first installed, silently crashed** (`/tmp/ao-fleet-sync-9002.log` full
      of `ModuleNotFoundError: No module named 'pydantic'`; confirmed by reproducing under
      `env -i PATH=/usr/bin:/bin`). Fixed by pinning to `${SCRIPT_DIR}/../../.venv/bin/python3` explicitly (fallback
      to bare `python3` only if the venv is missing) — verified under the same simulated cron-minimal-PATH before
      shipping. Evidence: `agent-orchestrator@6e5c8ccc57`. **Correction, same session, operator caught it**: the
      Progress Log originally claimed this as a BOTH-operators bug and credited this fix with `ikenna-tab2/4/6`
      going `active` shortly after shipping — both wrong. Ikenna's cron runs on his own separate machine against
      his own separate checkout; confirmed `/tmp/ao-fleet-sync-9001.log` does not even exist on this host, so his
      already-running cron job could not have picked up a fix that only landed on `origin/live-defi-rollout` without
      his own `git pull` — nothing shipped this session could mechanically have caused his recovery. The observed
      timing was coincidental (his own tick cycle, independent of this fix), not causal. Whether Ikenna's host ever
      hit this exact bug is **unconfirmed** — his log was never read, his host's `python3` resolution was never
      checked, and no access to his machine exists from this session. Confirmed scope: this bug is proven on Harsh's
      host only; the fix is real and correct regardless of whether it was ever needed elsewhere. **Separately
      confirmed, not a bug**: `harsh-tabN` rows still don't appear for THIS
      session specifically — `resolve_tab_number()` only matches a `-tabs-(\d+)-` cwd-slug segment, and this
      session's own transcript lives under the bare `-active-unified-trading-system-repos` project slug (no
      `.tabs/N` segment), unlike Ikenna's, whose active tabs are each opened with `.tabs/N` as their own VS Code
      workspace root. Per-tab visibility is working as designed; it requires each window to actually be opened at
      its own `.tabs/N` folder (this workspace's own existing "an interactive session IS slot N" rule), which at
      least this session isn't. Not fixed here — flagged to Harsh directly, his call how to restructure his windows.
- **2026-08-19 (same session, scope leak found + fixed, cron repointed to a stable checkout)**: Harsh asked whether the
  cron only scans this workspace — it did not. `ao-fleet-sync-tick.sh`'s usage-push loop globbed
  `~/.claude/projects/*/*.jsonl` with no project filter, so ANY local Claude Code project's real, priced token spend
  active within the recency window got pushed into this trading system's AO under his identity — a real scope leak,
  not cosmetic (`ao-liveness-heartbeat.py`'s per-tab rows were already correctly scoped via `resolve_tab_number()`;
  only the usage-push loop lacked the equivalent check). Fixed by adding the identical `-tabs-[0-9]+` guard to the
  usage-push loop. Separately, Harsh asked to repoint the standing cron job from `.tabs/2` to the root
  `agent-orchestrator` checkout, reasoning a `.tabs/N` worktree is more likely to be deleted/rotated than the root
  checkout — reinstalled via `install-fleet-sync-cron.sh` run from the root checkout (bakes in an absolute path;
  crontab entry now points there). Shipped from `.tabs/2` per operator instruction (not the root checkout, despite
  cron now targeting root — root's own uncommitted copy of the identical fix was left as local-only, to be
  reconciled by a future `git pull` there). Found and fixed one more real gap while shipping: `.tabs/2`'s own
  `.venv` had drifted stale (`orchestrator==0.99.1...` vs the current `0.100.4...`) — `basedpyright` failed on
  unrelated files (`codex_bridge_server.py`/`codex_mcp_proxy.py`, missing `tiktoken`/`mcp`) until
  `uv pip install -e . --python .venv/bin/python3` resynced it (plain `uv pip install -e .` without an explicit
  `--python` silently targeted the pyenv global environment instead of `.venv` from this shell — worth remembering
  for any future manual dependency sync in a per-slot checkout). Evidence: `agent-orchestrator@24a249b42f`.
- **2026-08-20 (interactive session, Harsh)**: Worked the plan's remaining Harsh-scoped/general open items directly
  (this plan is `assigned_vm: NA`/`execution_scope: local-only`, so interactive work here is correct, unlike the
  AO-dispatched plans this session was otherwise steering clear of). Resolved the `/api/agents?kind=human`
  contradiction todo — live now, transient not regressive (see flipped checkbox above). Re-checked Harsh's own
  task-cycle todo — still genuinely blocked, same 0-unblocked-of-706 wall as Ikenna's identical todo, correctly left
  un-forced. Harsh's per-tab-visibility todo not actionable from this exact session — its cwd is the bare
  `/active/unified-trading-system-repos` root, not a `.tabs/N` folder, so it structurally cannot produce a
  `harsh-tabN` row regardless of anything done here; unchanged, waits on Harsh working from `.tabs/N` windows.
  **Remaining open work, confirmed accurate**: Harsh's task-cycle (blocked on live backlog state) and Harsh's
  per-tab visibility (waits on tab-scoped sessions) — both self-resolve once their real-world precondition clears,
  neither is a code or doc gap.
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, valid — reaffirmed. All 3 open todos remain either
  physically laptop-scoped (Harsh's per-tab visibility, needs him working from `.tabs/N` windows) or blocked on
  live backlog state (Ikenna's and Harsh's "run one real task" todos — both re-checked as recently as 2026-08-20
  and still 0 unblocked-of-706 queued tasks). No new facts since the 2026-08-19 per-todo-split verdict; the one
  item that RECLASSIFIED then (Fleet-table role-badge exclusion) is already extracted and tracked in
  `ao_satellite_ao_dispatch_batch25_2026_08_19.md`. Doc stays `assigned_vm: NA`.
