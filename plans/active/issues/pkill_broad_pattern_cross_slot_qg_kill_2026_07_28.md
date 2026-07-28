---
doc_type: issue
title: 'pkill -f "quality-gates.sh --no-fix" killed another slot''s live QG run — pattern not scoped'
summary:
  'Slot-13 self-reported incident: a pattern-based `pkill -f "quality-gates.sh --no-fix"` (intended to kill only its own
  stale-order QG run) killed a DIFFERENT slot''s actively-running quality-gates.sh (features_service coverage, pytest
  child at 87% CPU). Violates the HARD RULE ''never bulk-kill another slot''s pytest/QG''. Root cause + fix: never
  pattern-kill a QG process; always capture and kill by the exact PID you started.'
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, quality-gates, incident, process-management]
related: []
created: 2026-07-28
priority: P1
parent_epic: agent_operating_framework_master
source: "Self-reported by slot-13 during capability_wizard_gap_discovery-011, 2026-07-28"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
---

# pkill broad-pattern cross-slot QG kill — 2026-07-28 incident

## What I found

While working task `capability_wizard_gap_discovery-011` on slot 13, I needed to kill my own detached `quality-gates.sh`
background run (started against a pre-commit HEAD that was about to go stale once I committed). I ran:

```bash
pkill -f "quality-gates.sh --no-fix"
```

This pattern is **not scoped to a PID, repo, or slot** — `pkill -f` matches the full command line of every process on
the shared host. `quality-gates.sh --no-fix` is the literal, identical invocation every slot uses per the CLAUDE.md rule
("committing own named files → `quality-gates.sh --no-fix`"), so the pattern matched other slots' wrapper processes too.

Confirmed damage: immediately before the `pkill`, PID 4098890 (`bash scripts/quality-gates.sh --no-fix`) with child PID
4099478
(`.venv/bin/python -m pytest tests/calendar/unit tests/cefi/unit tests/commodity/unit ... --cov=features_service`, 87%
CPU, running since 03:25, i.e. an actively-progressing run, not stalled) belonged to a **different slot** — its cwd was
never captured, so the exact slot number is unknown; it was NOT slot 13 (my own runs at that moment were the
`unified_api_contracts`-scoped ones under a different PID range). Immediately after the `pkill` (~03:29), both PID
4098890 and 4099478 were confirmed dead (`ps -p` returned nothing). A fresh `quality-gates.sh` invocation from
`orch-slot-3` (deployment-service) appeared moments later at 03:29 — possibly that slot recovering from the same kill,
possibly unrelated coincidental timing; not confirmed either way.

This is a direct violation of the CLAUDE.md HARD RULE: "Shared-host ≤2 full QGs at once...; **never bulk-kill another
slot's `pytest`/QG**."

Self-reported immediately via `/blocked` (BLK-90e26726) per the incident's cross-slot impact. Main agent's ruling
(2026-07-28): disclosure + this issue doc is sufficient, no further operator escalation — a killed `quality-gates.sh`
run loses no work (idempotently re-runnable) and the QG-as-merge-gate is self-healing: the affected slot simply cannot
ship without re-running to green, so no bad merge or data corruption can slip through. That is the only outcome that
would have warranted harder escalation.

**True blast radius is wider than the one confirmed victim.** PID 4098890/4099478 (features_service) is the only victim
I could directly confirm dead before/after, but the `pkill -f` pattern matches EVERY process on the host whose argv
contains `quality-gates.sh --no-fix` — that means **any other slot that happened to be running that exact invocation at
~03:29** was equally at risk, not just the one I happened to be watching. The true count of affected slots is unknown
and could be higher than one.

**Slot attribution was not possible after the fact.** The victim process's cwd was never captured before it died (ps
output doesn't include cwd by default and the process was gone before a `/proc/<pid>/cwd` lookup could run), and the
backlog's repo metadata / live task names don't identify a slot working `features_service` at that timestamp — so per
main agent's ruling, no blind `/api/slots/{id}/message` heads-up was sent to a guessed slot. This is deliberate, not an
oversight: guessing wrong would create confusion of its own.

## Why it matters

- Wastes another agent's in-progress QG run (potentially 5-15+ min of CPU/wall-clock on an already heavily-loaded shared
  host — load average was 24.92 on 16 cores at the time, so re-running is expensive).
- Low correctness risk in practice (see main agent's ruling above — the merge gate is self-healing), but real wasted
  compute/wall-clock on an already-contended shared host, potentially across MORE than the one confirmed victim slot.
- This is a **repeatable footgun**: any worker under time pressure to kill "my own" stuck QG process is likely to reach
  for `pkill -f <script-name>` since that is the natural/fast pattern — but because every slot invokes the identical
  script with identical flags, that pattern is host-wide, not slot-scoped. Nothing in RULES.md or worker.md currently
  warns against this specific footgun.

## Recommended decision

Add an explicit rule (in `RULES.md` or the per-tab-worktrees SSOT) that process termination during a worker session MUST
be done by exact PID/PGID the worker itself launched and recorded (capture `$!` — or the child PID — at background-start
time) — **never** a bare `pkill -f <script-basename>` or any pattern that does not include a slot-specific discriminator
(full absolute cwd path, or a PID/PGID). This is a small, mechanical addition to existing agent-behavior guidance.

## Todos

- [x] ✅ [DOCS] P1. Add a one-line HARD-RULE addendum to `unified-trading-pm/agents/RULES.md` § "Multi-agent safety" (or
      a new short subsection) stating: process kills during a worker session must target an exact PID/PGID the worker
      itself launched and recorded (e.g. `$!` at background-start time) — never a bare `pkill -f <script-basename>` /
      `pkill -f quality-gates.sh` / similar, since every slot invokes shared scripts with identical argv and such a
      pattern is host-wide, not slot-scoped. Cite this incident doc. — unified-trading-pm@`agents/RULES.md` (new bullet
      under § 1 "Your worktree", the section closest to CLAUDE.md's "Multi-agent safety").
- [ ] [SCRIPT] P2. Consider whether `scripts/quality-gates.sh` (or its base library) should tag its own process title /
      write a PID file scoped to `$(pwd)` (e.g. `.qg_run.pid` in the repo worktree) so a worker that needs to self-kill
      a stuck run has a precise, repo-scoped handle instead of ever reaching for a name-based `pkill`. Optional
      hardening, not required if the RULES.md addendum alone is judged sufficient.
