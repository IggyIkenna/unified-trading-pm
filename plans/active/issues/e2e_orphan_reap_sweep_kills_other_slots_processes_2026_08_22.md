---
doc_type: issue
title: Running the agent-orchestrator dashboard's Playwright e2e suite appears to trigger a host-wide orphan_reap sweep that kills OTHER slots' real processes
summary: >-
  While shipping a UI todo (ao_review_slot_hard_rule_and_diagnostics_2026_08_17's Agents-panel reserved-role badge),
  running `npx playwright test tests/e2e/agents-reserved-role-badge.spec.ts` against the dashboard's isolated e2e
  backend (`run-e2e-backend.sh`, its own port/DB/fixture per repo convention) produced webServer log lines naming
  `orphan_reap sweep: slot <N> pid <P> age=<S>s KILLED` for slot ids (1, 2, 4, 8, 19, 23 on one run; slot 24 on a
  second run) that are NOT part of this e2e suite's own fixture roster (which only ever seeds slots 0/1/2/5/9001) —
  strongly suggesting `server/orphan_reap.py`'s sweep scans real, host-wide OS processes/tmux sessions (shared across
  every `.tabs/<N>/` slot on this VM), not something scoped to the isolated e2e backend's own SQLite DB. If real, this
  means ANY agent running this repo's e2e Playwright suite on a shared multi-slot host risks killing a SIBLING slot's
  genuinely-live, in-progress work (a background QG run, an in-flight quickmerge, etc.) — the exact class of harm
  CLAUDE.md's "Never bulk-kill a peer's pytest/QG" hard rule exists to prevent, just triggered indirectly via a test
  harness rather than a direct pkill. NOT independently confirmed as actual harm (the reported PIDs were already gone
  by the time I checked `ps -p <pids>`, and the codex's own `orphan_reap.py::sweep_orphan_processes` history shows it
  already has some liveness/CPU-progress sparing logic — 2026-08-08 fix for a similar false-positive class — so this
  may be intentional, safe cleanup of genuinely-dead orphans rather than a sibling-work kill). Filing because the
  ambiguity itself is worth a real look: either confirm this is safe-by-design (and document that clearly, since
  nothing today tells a worker running e2e tests to expect this), or it is a genuine cross-slot hazard that needs a
  scope fix (e.g. gate the sweep to only PIDs/sessions the e2e backend's own isolated DB actually knows about).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, orphan-reap, e2e-testing, shared-host-safety, worker-liveness]
related:
  [
    /plans/active/issues/ao_review_slot_hard_rule_and_diagnostics_2026_08_17.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-22"
author: worker slot 26 (backend/ui craft, agent-orchestrator dashboard task)
parent_epic: orchestrator_master
resolved_by:
locked_by:
source: >-
  Observed as a side effect while running this repo's own e2e Playwright suite from a shared-host slot worktree
  (.tabs/26), unrelated to the actual UI task being shipped.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/orphan_reap.py,
    agent-orchestrator/dashboard/tests/e2e/run-e2e-backend.sh,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
---

# e2e Playwright suite's orphan_reap sweep appears host-wide, not e2e-scoped

## What I found

Two independent `npx playwright test tests/e2e/agents-reserved-role-badge.spec.ts --project=chromium` runs from
`.tabs/26/agent-orchestrator/dashboard` (a fresh `.venv` + `npm install`, otherwise stock `run-e2e-backend.sh`) each
printed a `[WebServer]` log line of the shape `orphan_reap sweep: slot <N> pid <P> age=<S>s KILLED`:

- Run 1: slots 1, 2, 4, 8, 19, 23 (PIDs 2168051 / 2168846 / 2168861 / 2170459 / 2190378 / 2650908, ages 588–1225s).
- Run 2 (after a fixture fix, same command): slot 24 (PID 3023812, age 390s).

The e2e backend's own isolated SQLite DB (seeded fresh every run by `seed_e2e_state.py`) only ever creates `SlotRow`s
for slot_id 0, 1, 2, 5, and 9001 — slots 4, 8, 19, 23, 24 are NOT part of this fixture at all. That rules out "the
sweep is reaping its own fixture rows" as the explanation; the sweep must be discovering these PIDs some other way
(most likely scanning real host state — `/proc`, `ps`, or live tmux sessions — independent of which SQLite DB the
triggering backend process happens to be pointed at).

## Why it matters

If `sweep_orphan_processes` (or whatever component logged this) genuinely operates on host-wide process/tmux state,
then spinning up the e2e backend (which shares the same `server/` codebase as the real production orchestrator,
just on an isolated port+DB) inherits that component's ambient host-wide sweep behavior too — meaning it could kill a
SIBLING slot's real, live work purely as a side effect of running this repo's own test suite. That is a direct
instance of the failure class CLAUDE.md's "Never bulk-kill a peer's `pytest`/QG" rule and the per-tab-worktrees SSOT's
"don't touch dirty files/processes in another agent's tree" rule both exist to prevent — just reached via `npx
playwright test` rather than a manual `pkill`.

## What I did NOT confirm

- I did not confirm actual harm: by the time I checked (`ps -p <pids>`), all reported PIDs were already gone, and I
  have no way from this session alone to tell whether they were genuinely-dead orphans (correct cleanup) or
  live sibling work (a real kill). This is exactly the ambiguity that needs an "audit-scope" look, not a small
  same-file fix.
- I did not read `server/orphan_reap.py::sweep_orphan_processes`'s actual scanning logic end-to-end to confirm the
  host-wide-scan hypothesis — this issue is filed at the "found a signal worth investigating" stage, not a root-caused
  fix.

## Recommended decision

A `backend_engineer` (or `infra`) pass should: (1) read `sweep_orphan_processes` to confirm/refute the host-wide-scan
hypothesis, (2) if confirmed, decide whether the e2e backend should suppress this specific sweep entirely (it already
suppresses/fakes several liveness mechanisms per `run-e2e-backend.sh`'s existing comments — this may just need to join
that list), and (3) if it's actually safe-by-design (e.g. the sweep only ever touches genuinely-dead, no-owner
processes regardless of which backend triggered it), document that explicitly in `run-e2e-backend.sh`'s header comment
so the next worker running this suite on a shared host isn't left guessing the way this session was.

## Todos

- [ ] [BACKEND] P2. Read `server/orphan_reap.py::sweep_orphan_processes` (and whatever calls it from the FastAPI app's
      startup/background-task wiring) to confirm whether its process/session scan is genuinely host-wide (scans real
      `/proc`/`ps`/tmux state) or scoped to the triggering backend's own DB-known slots. Report back in this doc.
- [ ] [BACKEND] P2. If host-wide: either scope the sweep so a test/e2e-mode backend instance never scans/kills
      processes it doesn't own (e.g. gate on `ORCHESTRATOR_MODE=mock` or a dedicated test-mode flag, mirroring how
      `run-e2e-backend.sh` already fakes/suppresses other liveness mechanisms for its fixture agents), or clearly
      document in `run-e2e-backend.sh`'s header why it's safe as-is (e.g. it provably only reaps processes with no
      live parent/owner, host-wide is intentional and correct).

## Progress Log

- 2026-08-22: Filed by worker slot 26 as a side observation while shipping an unrelated UI todo
  (`ao_review_slot_hard_rule_and_diagnostics_2026_08_17`'s Agents-panel reserved-role badge). Not investigated further
  in that session — out of ui_developer craft scope (backend orphan-reap internals) and tangential to the assigned
  task; handed off here for a backend/infra pass.
