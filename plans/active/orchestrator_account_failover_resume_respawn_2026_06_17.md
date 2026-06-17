---
title: "Orchestrator account failover — context-preserving resume-respawn on usage cap"
created: 2026-06-17
status: active
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: local-only
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
source:
  - 2026-06-17 account-pool exhaustion incident (orchestrator_agent_lifecycle_gaps Gap 6) — operator design session
priority: P2
---

# Orchestrator account failover — context-preserving resume-respawn

## Why

The 2026-06-17 incident (`plans/active/issues/orchestrator_agent_lifecycle_gaps_2026_06_16.md` § Gap 6) exposed that
when a spawned `claude` agent (worker or the main orchestrator agent) hits its account's usage cap, it freezes on the
CLI usage-limit modal and the only recovery shipped so far is a **kill + FRESH respawn** — which throws away the agent's
in-flight conversation context. This plan upgrades that to a **context-preserving resume-respawn**: on a genuine cap,
kill the wedged process and respawn it on the next headroom account with `claude --resume <session-id>`, so the agent
continues with its full conversation intact (losing only the single wall-blocked turn).

This is the durable, forward design. The Gap-6 issue doc remains the incident record for the 5 already-shipped fixes
(95% ceilings + env-tunable helpers, honest abandon alert, pool-exhaustion page, re-probe-before-abandon, modal-kill);
this plan supersedes the **kill+fresh-respawn** half of that work with resume.

## Design model (operator-agreed 2026-06-17)

1. **95% ceiling is a SPAWN GATE ONLY.** `pick_headroom_account` (`weekly<95 AND 5h<95`) decides which account a _new_
   agent may start on. It MUST NEVER preempt a running agent.
2. **A running agent consumes its account to 100%.** Killing a working agent at 95% would forfeit the last 5% of every
   account's quota on every cycle — pure waste. Let it run to completion or to the genuine wall.
3. **Failover fires ONLY on an actual usage-cap stuck state** — the CLI usage-limit modal (the existing
   `_RATE_LIMIT_MODAL_RE` / worker `_USAGE_CAP_RE` detection), never on a percentage threshold. At that point the agent
   cannot proceed anyway, so resume-respawn loses nothing but the wall-blocked turn.
4. **No headroom anywhere → WAIT, never force-spawn.** When every account is over its ceiling / rate-limited, the
   correct behaviour is to queue + page (the pool-exhaustion alert) so the operator buys a new account or waits for the
   nearest reset. This already holds (`pick_headroom_account → None` → no spawn) and is not changed here.

## Verified CLI basis (Claude Code v2.1.175 + official docs, read-only verification 2026-06-17)

- **Session-id is assignable at launch.** `claude --session-id <uuid>` sets a specific session id, so we GENERATE a UUID
  at spawn and own it deterministically from t=0 — no filesystem scraping, no race against other slots. (Fallback if
  ever needed: the transcript is `$CLAUDE_CONFIG_DIR/projects/<cwd-with-/-as-->/<session-id>.jsonl`, with `sessionId` in
  the first JSONL line.)
- **`claude --resume <id>` reloads conversation context** when relaunched in the SAME `CLAUDE_CONFIG_DIR` + SAME cwd.
  The transcript is pure conversation history — it carries NO account identity.
- **Resume works across a token change.** Sourcing a different account's `CLAUDE_CODE_OAUTH_TOKEN` and resuming the same
  session authenticates as the new account while replaying the old conversation. Account identity only lives in
  `.credentials.json`, which `CLAUDE_CODE_OAUTH_TOKEN` bypasses entirely — and we don't use it (setup-token env auth).
  Reusing the per-session config dir with a new token is clean; no clearing required.
- **cwd coupling:** `--resume` must run from the original cwd. Our respawn reuses the same slot worktree → satisfied.
- **Gotchas:** permissions don't carry across resume (covered — we run `--dangerously-skip-permissions`); resumed
  context is the _compacted_ history (acceptable). **Kill via the exact `tmux_spawn.kill_session(<name>)`, NEVER
  `pkill -f claude...`** (a wildcard reaps sibling slots sharing the substring).

## Phased execution

### Phase 1 — Deterministic session-id at spawn (foundation)

- [x] ✅ [ORCHESTRATOR] P1. Generate a UUID per spawn and pass `claude --session-id <uuid>` in `tmux_spawn.spawn` /
      `spawn_named` (thread it through `_build_claude_flags` / `_start_session`). Repo: agent-orchestrator
      (`server/tmux_spawn.py`). — agent-orchestrator@380fe6c (`new_session_id()` + `--session-id`/`--resume` in
      `_build_claude_flags`)
- [x] ✅ [ORCHESTRATOR] P1. Persist the session uuid on the owning row at spawn time — `SlotRow` for workers,
      `AgentRow`/the main-agent record for the main agent (new column, e.g. `claude_session_id`). Set it in
      `autospawn._do_spawn` and `main_agent_keeper._spawn`. Repo: agent-orchestrator (`server/orm.py`, `autospawn.py`,
      `main_agent_keeper.py`). — agent-orchestrator@380fe6c (`claude_session_id` on both rows + `bootstrap.py`
      ALTER-TABLE migration + `register_agent(claude_session_id=…)`; `_do_spawn` mints+sets, `_run_one_tick` persists)
- [ ] [ORCHESTRATOR] P2. Verify `--session-id` is accepted alongside `--dangerously-skip-permissions` on a fresh session
      in the live CLI version (smoke one spawn on the VM, confirm the transcript filename == our uuid). Repo:
      agent-orchestrator (verification). **AWAITING CENTRAL VM** — needs a real `claude` spawn on the central VM
      (`planning`/`i-0c9b283b31d6b5ca7`); not reproducible from a laptop slot.

### Phase 2 — Resume-aware respawn variant

- [x] ✅ [ORCHESTRATOR] P1. Add a resume path to the spawn machinery: when given a `resume_session_id`, launch
      `claude --resume <id> --dangerously-skip-permissions …` and **skip the boot-prompt paste** (the agent already has
      its context); send a `continue` nudge instead. Same session NAME + same `CLAUDE_CONFIG_DIR` + same cwd as the
      killed session. Repo: agent-orchestrator (`server/tmux_spawn.py`). — agent-orchestrator@380fe6c (`spawn` /
      `spawn_named` `resume_session_id` + `resume_nudge`: skip `_paste_prompt`, `send_command(nudge)`)
- [x] ✅ [ORCHESTRATOR] P1. Source the NEW account's env file (new `CLAUDE_CODE_OAUTH_TOKEN`) on the resume respawn so
      the continued agent authenticates as the headroom account. Repo: agent-orchestrator (`server/tmux_spawn.py` /
      `autospawn`). — agent-orchestrator@380fe6c (callers pass the headroom account's `env_file`; `_start_session`
      sources it before `exec claude`)

### Phase 3 — Wire cap-detection → resume-respawn (HEADROOM-GATED, decision B)

> **No-headroom-at-cap = decision B (operator 2026-06-17):** the kill + resume-respawn fires ONLY when a headroom
> account is available to move to. If the agent is capped AND no account has headroom, **leave it frozen on the modal
> (do NOT kill)** — it sits inactive, harmless, and the pool-exhaustion page already nags the operator to add an account
> / wait for a reset. This needs zero extra machinery and de-risks the rollout (prove `--resume` end-to-end before
> killing into a state we can't immediately resume). **Decision A (kill immediately on cap, resume later from the
> on-disk transcript when an account frees) is the NAMED SUCCESSOR** — adopt once `--resume` is proven end-to-end (see §
> Temporary states).

- [x] ✅ [ORCHESTRATOR] P1. Main agent: in `main_agent_keeper._handle_rate_limit_modal`, on modal-detect FIRST pick a
      headroom account; **if one exists** → kill + resume-respawn with the stored `claude_session_id` on that account;
      **if none** → do NOT kill (leave it frozen), keep the deduped page firing, re-check next tick. (Supersedes the
      shipped unconditional kill+fresh-respawn.) Repo: agent-orchestrator (`server/main_agent_keeper.py`). —
      agent-orchestrator@380fe6c (returns `resumed`/`killed_fresh`/`frozen_no_headroom`; failover cooldown vs lingering
      modal)
- [x] ✅ [ORCHESTRATOR] P1. Workers: in `WorkerLivenessWatchdog`, when a worker pane matches the hard cap (NOT a
      recoverable transient), pick a headroom account FIRST; **if one exists** → kill + respawn that slot with
      `--resume <stored id>` on it (not a fresh boot); **if none** → leave the worker frozen (do not kill), rely on the
      pool-exhaustion page. Reuse Phase-2 machinery. Repo: agent-orchestrator (`server/worker_liveness_watchdog.py`). —
      agent-orchestrator@380fe6c (Trigger 1.4 `_handle_usage_cap`: resume / fresh-respawn-if-no-sid / frozen)
- [x] ✅ [ORCHESTRATOR] P2. A frozen-but-no-headroom agent must NOT read as healthy: the keeper/watchdog still DETECTS
      the cap each tick (so it acts the moment a headroom account appears) and the agent shows as capped/blocked in the
      UI, not "working". Repo: agent-orchestrator. — agent-orchestrator@380fe6c (cap trigger runs before stuck/silent
      every tick so it's never reaped; `slot.last_msg` capped marker; keeper returns `rate_limited`, not `alive`)

## Temporary states + their canonical follow-up

- **Decision B (headroom-gated kill+resume; leave frozen when no headroom)** is the INITIAL behavior. **Canonical
  successor = Decision A** (kill immediately on cap + resume later from the on-disk transcript when an account frees) —
  adopted within THIS plan once `--resume` is proven end-to-end on the live VM (Phase 4 smoke green). Until then B
  holds.

### Phase 4 — Tests + deploy

- [x] ✅ [ORCHESTRATOR] P1. Unit tests: deterministic `--session-id` flag emitted + persisted at spawn; resume respawn
      builds `--resume <id>` + skips boot-paste + sources new token; main-agent + worker cap → resume (not fresh);
      no-headroom-at-cap → no fresh spawn. Repo: agent-orchestrator (`tests/`). — agent-orchestrator@380fe6c
      (`tests/test_account_failover_resume.py` + updated `test_main_agent_keeper.py` /
      `test_worker_liveness_watchdog.py`; QG green: 682 passed, 0 type errors)
- [ ] [ORCHESTRATOR] P1. Live smoke on the central VM: drive a session to the usage modal (or simulate), confirm it
      respawns on a fresh account AND the resumed pane shows prior context (not a blank boot). Repo: agent-orchestrator.
      **AWAITING CENTRAL VM** — needs a live capped session on the central VM; can't be driven from a laptop slot.
- [ ] [ORCHESTRATOR] P2. Deploy: `git pull --ff-only` + `systemctl restart orchestrator.service`; verify the keeper +
      watchdog log the resume path. Repo: agent-orchestrator (central VM). **AWAITING CENTRAL VM** — the bootstrap
      ALTER-TABLE migration auto-applies on backend start; deploy = pull LDR + restart the service on
      `i-0c9b283b31d6b5ca7`.

## Success criteria

- A worker or the main agent that hits its account's usage cap is **continued on a fresh headroom account with its
  conversation context intact** — verified by the resumed pane showing prior turns, not a fresh boot.
- No running agent is ever preempted below the genuine cap (95% never triggers a kill).
- Session-ids are deterministic (assigned at spawn), persisted, and used for resume — no transcript scraping.
- When no account has headroom, the system waits + pages; it never fresh-spawns into a capped pool.
- Kills are exact (`tmux_spawn.kill_session`), never `pkill -f`.

## Risks / open items

- `--session-id` acceptance with `--dangerously-skip-permissions` on a brand-new session is verified by docs but
  smoke-confirmed in Phase 1 P2 before building on it.
- Compacted-history-on-resume means a very long capped session resumes slightly lighter than its peak context —
  acceptable; flag if a worker ever resumes mid-task with lost critical state.
- Main agent is mostly stateless ticks (fresh respawn is cheap there); the resume win is largest for workers mid-task —
  but apply uniformly for consistency.

## Codex SSOT updates

- ✅ `codex/04-architecture/agent-orchestrator-overview.md` § Worker liveness watchdog — added "Trigger 1.4 — usage-cap
  account failover (resume-respawn)" documenting cap → resume on fresh headroom account, 95%-is-spawn-gate-only,
  wait-don't-force-spawn when capped, deterministic session-id + persistence, main-agent parity, cooldown + no-daily-cap
  for the resume path.
- ✅ `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` § "Context-preserving resume across a token
  change" — added the verified resume-across-token-change facts (session-id at launch, `--resume` reloads context in the
  same config-dir + cwd, token-change clean under setup-token auth, gotchas).

## Progress Log

- **2026-06-17 (slot-5, laptop)** — Phases 1–4 (code + tests) shipped: agent-orchestrator@380fe6c on `live-defi-rollout`
  (`feat(orchestrator): context-preserving account-failover resume-respawn on usage cap`). Deterministic
  `claude --session-id` at every spawn, persisted on `SlotRow`/`AgentRow.claude_session_id`; `--resume` path in
  `spawn`/`spawn_named` (skip boot-paste + `continue` nudge + source new account env); headroom-gated resume wired into
  `main_agent_keeper._handle_rate_limit_modal` (decision B) and the worker watchdog Trigger 1.4 (`_handle_usage_cap`).
  Local QG green (682 passed, 0 type errors, ruff clean, dashboard tsc+vitest green). Codex SSOTs updated. **Remaining =
  live central-VM steps only** (Phase 1 P2 `--session-id` CLI smoke; Phase 4 P1 live cap→resume smoke; Phase 4 P2
  deploy + `systemctl restart orchestrator.service`) — not reproducible from a laptop slot; the bootstrap ALTER-TABLE
  migration auto-applies on backend start.

## Cross-links

- Incident record + the 5 shipped Gap-6 fixes (95% ceilings, honest abandon alert, pool page, re-probe, modal-kill):
  `plans/active/issues/orchestrator_agent_lifecycle_gaps_2026_06_16.md` § Gap 6. The kill+fresh-respawn there is
  UPGRADED to resume here.
- Escalation-drain residual (slot-1 FM5 quarantine + `_pick_free_slot` quarantine-skip + retry-loop no-HOL-block) stays
  in that issue doc — a separate slot/worktree-health problem, not account failover.
