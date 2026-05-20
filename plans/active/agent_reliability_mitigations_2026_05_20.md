---
title: Agent reliability mitigations — close the multi-agent loop gaps (2026-05-20)
type: implementation-plan
status: active
created: 2026-05-20
deadline: 2026-05-22
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
companion_to: codex/05-infrastructure/per-tab-worktrees.md
---

# Agent reliability mitigations — close the multi-agent loop gaps

> **Provenance**: surfaced during 2026-05-20 agent-orchestrator-on-AWS post-cutover review (operator session with
> ikenna-main slot-1). After the EC2 VM stood up + 12 slot worktrees were ready to spawn, operator asked four sharp
> questions about reliability that exposed real gaps in the multi-agent loop. This plan closes them.

## Context

The agent-orchestrator now runs on a dedicated EC2 VM with 12 slot worktrees ready to receive agents. Before spawning
agents at scale, four reliability gaps must be closed — left unaddressed, the system silently loses work or
mis-attributes ownership during context-reset / tmux-death / mirror-conflict events.

| Gap                                                                   | What breaks today                                                           | Likelihood                                         |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------- |
| 1. Tab→LDR mirror failure → no notification                           | Agent pushes, GHA `[mirror:skip]`-logs silently, work orphaned on tab       | Whenever two tabs touch overlapping files          |
| 2. Slot spawns into a dirty worktree                                  | New agent inherits another agent's WIP, conflates ownership                 | Whenever tmux dies / context-resets mid-edit       |
| 3. New agent can't distinguish own predecessor's WIP from foreign WIP | Per CLAUDE.md the rule "untracked = foreign" is wrong on context-reset      | Whenever an agent's context window resets mid-task |
| 4. Slot lacks "in-flight files" record                                | After a heartbeat gap, no way to recover what the last agent was working on | Whenever a slot dies without `done`                |

## Phased execution

### Phase 1 — Mirror-failure → orchestrator alert (highest leverage, smallest blast)

**Target repos**: every repo with `tab-mirror-to-ldr.yml` (workspace-wide), `agent-orchestrator` (backend),
`unified-trading-pm/scripts/workflow-templates/` (SSOT for the workflow).

**Mechanics**:

1. New backend endpoint `POST /api/mirror-events` (no auth — webhook): accepts `{repo, branch, sha, decision, reason}`.
   Persists to a new `mirror_events` table + sets `slot.mirror_blocked_at = now()` when decision != "ff" / "noop".
2. `tab-mirror-to-ldr.yml` adds final step that POSTs the result via `curl` to
   `https://api.agent-orchestrator.odum-research.com/api/mirror-events` — fire-and-forget, exits 0 either way.
3. Dashboard reads `mirror_blocked_at` per slot; shows red banner: "LDR mirror blocked on `<repo>@<sha>` — tab is
   `<reason>` to LDR. Rebase + retry." Operator can mark resolved.
4. Slack hook (slot 11 plan) gets first non-test customer.

**Rollout**: SSOT edit in PM repo + run `rollout-workflow-templates.sh --template tab-mirror-to-ldr.yml` to fan-out to
every consumer repo. Backend ships independently; workflows can call the endpoint before the backend is deployed
(endpoint returns 503; workflow tolerates).

### Phase 2 — Pre-spawn dirty-state gate

**Target**: `agent-orchestrator/server/server.py` `spawn_slot()` handler + a new helper module.

**Mechanics**:

1. New helper `worktree_clean_check.py::check_all_worktrees(slot_id) -> dict[str, DirtyReport]` runs
   `git status --porcelain` in each of the 27 repos under `.tabs/<slot_id>/`. Returns map repo → DirtyReport
   (`unstaged`, `staged`, `untracked` lists).
2. `spawn_slot()` calls this before launching tmux. If any dirty: refuse spawn with HTTP 409 + body listing dirty files
   per repo + a list of three resolution options the operator must pick from:
   - `stash-and-continue` — `git stash push -m "auto-stashed-pre-spawn-{ts}-{slot_id}"`, then spawn
   - `commit-and-continue` — `git commit -am "auto-commit-pre-spawn-{ts}-{slot_id}"` + push, then spawn
   - `reset` — `git reset --hard origin/{branch}`, then spawn (DESTRUCTIVE — extra confirm)
3. New `SpawnRequest.dirty_state_resolution: Literal["refuse", "stash", "commit", "reset"] = "refuse"` field. `refuse`
   (default) returns 409. Others execute the chosen path then proceed.
4. Dashboard wraps this: spawn click → if 409 → modal showing per-repo dirty list + 3 buttons → user picks → resend with
   `dirty_state_resolution=...`.

### Phase 3 — Per-agent `.agent-claim` ownership tag

**Target**: `agent-orchestrator/server/tmux_spawn.py` (boot path), `agents/<role>.md` templates (boot prompt), and a new
`worktree_claim.py` helper.

**Mechanics**:

1. On `spawn_slot`, before pasting the boot prompt, write `.tabs/<N>/.agent-claim` JSON:
   ```json
   {
     "agent_id": "<slot>-<role>-<spawn-ts>",
     "slot_id": <N>,
     "role": "worker",
     "model": "sonnet",
     "tmux_session": "orch-slot-<N>",
     "spawned_at": "<iso>",
     "operator": "ikenna",
     "expires_at": "<spawned_at + 24h>"
   }
   ```
   `.gitignore` for `.agent-claim` so it never gets committed.
2. Append to every boot prompt: "On any unfamiliar dirty file, read `.tabs/<N>/.agent-claim` first. If `agent_id`
   matches yours: that's your predecessor (context reset). Treat the file as your own WIP, finish the work, then
   `git commit + push`. If `agent_id` doesn't match or claim is stale (>24h): treat as foreign, stash by name, do not
   edit."
3. Heartbeat updates `expires_at = now() + 1h` so a still-live slot never looks stale.
4. New endpoint `GET /api/slots/<N>/claim` returns the current claim for operator visibility.

### Phase 4 — Per-slot heartbeat `in_flight_files`

**Target**: `agent-orchestrator/server/models.py` (HeartbeatRequest schema), `state_store.py` (slot row),
`agents/<role>.md` (heartbeat protocol).

**Mechanics**:

1. Extend `HeartbeatRequest` with `in_flight_files: list[InFlightFile]` where
   `InFlightFile = {repo: str, path: str, last_touched: iso8601, intent: "edit" | "review" | "test"}`.
2. Slot row stores latest `in_flight_files` (overwrite each heartbeat). Backend exposes
   `GET /api/slots/<N>/in-flight-files`.
3. Boot prompt addendum: "Before each Edit/Write, POST a heartbeat to `/api/slots/<N>/heartbeat` including the file
   you're about to touch in `in_flight_files`. After commit, the file drops off the list on the next heartbeat."
4. On boot, new agent fetches its predecessor's `in_flight_files` (preserved on slot row even past tmux death) and uses
   it as the recovery hint (composes with Phase 3 claim file).
5. Stale check: heartbeat older than 15 min → backend marks slot `stale`; dashboard shows.

## Phase ordering rationale

Phases stack:

- Phase 1 fixes the OUTBOUND blind spot (work pushed but didn't land on LDR)
- Phase 2 fixes the INBOUND blind spot (worktree dirty before spawn)
- Phase 3 + 4 compose: claim file is the agent's own identity assertion; in-flight files are the orchestrator's
  state-truth. Phase 3 alone handles context-reset within a slot; Phase 4 alone handles slot-death between agents;
  together they handle every combination.

Phase 1 + 2 are quick wins (~30 min each). Phase 3 + 4 are design-heavier (~45-60 min each) but worth it before running
many slots in parallel.

## Success criteria

- Phase 1: pushing a tab branch that conflicts with LDR triggers a Slack ping AND a red banner on the dashboard within
  60s. Verified by intentionally pushing a divergent tab branch.
- Phase 2: attempting to spawn a slot with a dirty worktree returns 409 with a complete dirty-files manifest. Operator
  can resolve via stash/commit/reset and re-spawn succeeds.
- Phase 3: killing a tmux session mid-edit, then re-spawning into the same slot, the new agent recognizes the
  predecessor's WIP via `.agent-claim` and finishes the work without re-doing it.
- Phase 4: backend `/api/slots/<N>/in-flight-files` returns the most-recent file list per slot, persists past tmux death
  until a new agent boots and overwrites.

## Codex SSOT updates

After phases land, update:

- `codex/05-infrastructure/per-tab-worktrees.md` — § "Mirror-failure handling", § "Pre-spawn gate", § "Agent ownership
  claims", § "Heartbeat in-flight files"
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — add the agent-claim reading protocol
- `unified-trading-pm/CLAUDE.md` — replace the "Untracked = foreign" rule with the claim-file-aware version

## Out of scope

- Two-side ping resolution / cross-side conflict mediation (already handled by `_agent_pings.md`)
- Slot reassignment workflow (existing `/api/slots/<N>/reassign` endpoint covers this)
- GHA self-hosted-runner migration (parallel concern, separate plan)
