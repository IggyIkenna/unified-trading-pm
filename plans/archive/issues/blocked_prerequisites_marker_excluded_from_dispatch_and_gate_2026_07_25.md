---
doc_type: issue
title: BLOCKED-PREREQUISITES todos are permanently excluded from dispatch AND silently defeat gate_on_depends
summary: >-
  `_NON_DISPATCHABLE_RE` in agent-orchestrator/server/regen_backlog_from_plan.py matches the broad pattern
  `BLOCKED-[A-Z]`, which — beyond the documented closed set (CREDENTIALS/OPERATOR-DECISION/BILLING/UPSTREAM-OUTAGE/
  PLAYWRIGHT/JURISDICTION, all genuinely human/external-only blocks) — also permanently excludes `BLOCKED-PREREQUISITES`
  todos from ever becoming a backlog task, even after the prerequisites they name have since landed. Because the same
  `_parse_open_todos` helper backs both the ADD pass and the `gate_on_depends` upstream "has_open" disambiguation, a
  plan whose only remaining item is a `BLOCKED-PREREQUISITES` todo reads as having ZERO open todos — so any downstream
  `gate_on_depends: true` plan gated on it dispatches prematurely, believing the upstream is fully clear. Confirmed live
  on `infra_capture_and_devops_leftovers_2026_07_06.md` / `infra_capture_and_devops_leftovers_finalize_2026_07_25.md`:
  dispatched to slot 2 (2026-07-25T04:52Z) and again to slot 3 same day, both times finding the gate not actually met.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [dispatcher, gate_on_depends, backlog-regen, blocked-marker, regression]
related:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-07-25
assigned_vm: planning
parent_epic: agent_operating_framework_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
source: >-
  Discovered while working infra_capture_and_devops_leftovers_finalize-001 (slot 3, data_engineering) — the finalize
  todo's own progress-log note (from an earlier slot-2 dispatch, 2026-07-25T04:52Z) already flagged the gate as not
  genuinely met; this doc traces the mechanism so it stops recurring.
resolved_by: >-
  agent-orchestrator@a6c87d7 (regex fix + regression tests, plan-flip 0098ea9cc). Second todo closed as superseded — the
  actual ASTER connector launch is tracked under `infra_capture_and_devops_leftovers-001` (parent plan's own todo, now
  correctly re-ingested), not this doc.
locked_by:
drift_direction: advance-code
depends_on: []
---

# BLOCKED-PREREQUISITES excluded from dispatch AND defeats gate_on_depends

> **🟢 ARCHIVED 2026-07-25** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule (terminal_status_archival_backlog_sweep_2026_07_25.md).

## What I found

`agent-orchestrator/server/regen_backlog_from_plan.py:957` defines:

```python
_NON_DISPATCHABLE_RE = re.compile(
    r"BLOCKED-[A-Z]"  # status tokens are always UPPERCASE-hyphenated (taxonomy)
    r"|_\(\s*[Ss]tretch"
    r"|\b[Ss]tretch,\s*optional\b"
    r"|\*\*[Ss]tretch\*\*"
)
```

The docstring above it (lines 948-956) documents the INTENDED closed set as todos that "can NEVER be auto-worked by a
spawned worker — it waits on a human/operator/external event":
`BLOCKED-CREDENTIALS / -OPERATOR(-DECISION) / -BILLING / -UPSTREAM-OUTAGE / -PLAYWRIGHT / -JURISDICTION`. But the actual
regex `BLOCKED-[A-Z]` is a catch-all — it also matches `BLOCKED-PREREQUISITES`, which is semantically different: it
waits on OTHER AGENT-COMPLETABLE work (another backlog task / a code merge), not a human/external event. Nothing in the
taxonomy comment lists `PREREQUISITES` as intentionally included.

`_parse_open_todos()` (line 964) applies this same regex in BOTH the ADD pass (no backlog task is ever created for a
`BLOCKED-PREREQUISITES` todo) AND the prune pass — so once a worker parks a todo with this marker (as slot-9 did on
`infra_capture_and_devops_leftovers_2026_07_06.md`'s ASTER connector todo, 2026-07-07), it can **never** re-enter the
dispatch pool automatically, even after the prerequisites it names have since landed. Confirmed live right now:

```
$ curl -s localhost:8765/api/backlog | jq '.[] | select(.plan_ref | test("infra_capture_and_devops_leftovers"))'
infra_capture_and_devops_leftovers_finalize-001  dispatched  ...
```

Only the FINALIZE plan's todo appears — the parent's ASTER connector todo
(`- [ ] 🚧 BLOCKED-PREREQUISITES [DATA] P1. Register + launch the ASTER live connector`) has never been a backlog row,
despite living under a section explicitly titled `## Capture wiring (dispatchable)` and despite its own in-body note
confirming both named prereqs (cefi-007, UAC `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]`) landed on LDR back on 2026-07-07.

Second-order effect: `_wire_gate_on_depends_prereqs()` (line 1637) computes upstream "open" state via the SAME
`_parse_open_todos()`. With the ASTER todo excluded, the parent plan reads as having zero open todos → the derived
`gate-upstream-open:infra_capture_and_devops_leftovers_2026_07_06` condition is set `True` (cleared) →
`infra_capture_and_devops_leftovers_finalize_2026_07_25.md`'s own gated todo dispatches — even though the parent's real
remaining work (launch + verify `live_aster` row-landing) is nowhere near done. This has now dispatched the SAME
premature finalize task to two different slots on the same day (slot 2 @ 2026-07-25T04:52Z, slot 3 later same day), each
independently re-discovering the gate isn't met and releasing the task without progress.

## Why it matters

- Wastes a worker turn every time the finalize task gets re-dispatched (it will keep happening — nothing about the
  underlying state changes on retry).
- Worse than wasted turns: a LESS careful future worker could take the finalize task's `gate cleared` signal at face
  value and run the standard 6-step archival ritual on the parent plan while its actual remaining work (the ASTER
  connector launch) is silently lost — the todo text says "Once the ASTER live connector todo is `[x]`" but nothing
  forces a worker to re-verify that by hand; the dispatcher itself already vouches (incorrectly) that the gate cleared.
- The underlying ASTER connector todo is itself orphaned: it is real, currently-actionable `[DATA]` work (prerequisites
  confirmed landed 2026-07-07) that will never be picked up by any worker because it is permanently excluded from
  ingestion by this same regex — someone has to notice it by manually reading the parent plan.

## Recommended decision

Narrow `_NON_DISPATCHABLE_RE` to the documented closed set instead of the open-ended `BLOCKED-[A-Z]` catch-all — e.g.
`BLOCKED-(CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-OUTAGE|PLAYWRIGHT|JURISDICTION)` — so
`BLOCKED-PREREQUISITES` (and any other non-taxonomy `BLOCKED-*` token) is NOT excluded and participates normally in both
the ADD pass and `gate_on_depends` open-todo detection. A `BLOCKED-PREREQUISITES` todo that genuinely isn't ready will
simply get picked up, re-checked, and re-parked by a worker (as already happened once, cheaply) rather than silently
vanishing from the pipeline forever. This is a scoped regex change + a regression test asserting a
`BLOCKED-PREREQUISITES` todo (a) IS ingested as a backlog task and (b) DOES count as "open" for `gate_on_depends`
upstream detection, plus a control case that `BLOCKED-CREDENTIALS` etc. remain excluded.

## Todos

- [x] ✅ [BACKEND] P1. Narrow `_NON_DISPATCHABLE_RE` in `agent-orchestrator/server/regen_backlog_from_plan.py` (line
      ~957) to the documented closed set of truly-external-only tokens (CREDENTIALS / OPERATOR(-DECISION) / BILLING /
      UPSTREAM-OUTAGE / PLAYWRIGHT / JURISDICTION), excluding `PREREQUISITES` (and any other non-taxonomy token) so
      those todos are ingested normally and correctly participate in `gate_on_depends` open-todo detection. Add a
      regression test in the regen test suite covering both the ADD-pass and `_wire_gate_on_depends_prereqs` paths.
      (repo: agent-orchestrator) — agent-orchestrator@a6c87d7. Regex now anchors on the exact closed set
      (`CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-OUTAGE|PLAYWRIGHT|JURISDICTION`); added
      `test_parse_ingests_blocked_prerequisites_but_excludes_taxonomy_tokens` (ADD-pass) and
      `test_regen_gate_on_depends_holds_when_upstream_only_open_todo_is_blocked_prerequisites`
      (`_wire_gate_on_depends_prereqs` path) to `tests/test_regen_backlog_from_plan.py`. QG green (1694 passed).
- [x] ✅ [DATA] P1. Once the regex fix lands and the ASTER connector todo in
      `infra_capture_and_devops_leftovers_2026_07_06.md` re-enters the backlog, pick it up: register
      `aster_book_liq_ws.py` into `live/connector_registry.py`, launch the live VM (KALSHI-PERP book5 VM is the in-cefi
      template), and verify `live_aster` book5/liquidations rows land (per-VM shard spot-check at T+10-15min) before
      flipping the checkbox. This is the actual gate that `infra_capture_and_devops_leftovers_finalize_2026_07_25.md` is
      waiting on. (repo: market-tick-data-service, deployment-service) — **RESOLVED AS SUPERSEDED (slot 3, checked
      2026-07-25)**: this todo was a spun-out pointer written before the regex fix landed, to make sure the ASTER work
      wouldn't be forgotten. The fix worked exactly as intended — `GET /api/backlog` now shows the parent plan's OWN
      todo re-ingested as `infra_capture_and_devops_leftovers-001` (`collision_group: script:aster_book_liq_ws.py`,
      `status: dispatched`, `dispatched_to: 4`). That is now the single canonical task for the actual launch+verify
      work; this todo duplicating it (with no `collision_group` of its own, since it lives in a different plan file)
      would risk a double-launch of a live connector. Closing here without touching the VM/connector — the real work is
      tracked and in progress under `infra_capture_and_devops_leftovers-001`, not this doc. Authoring note for next
      time: a same-file todo with a genuine "once X lands, do Y" dependency should have set `sequential: true` on this
      plan (or used `depends_on`/`gate_on_depends`) instead of relying on prose ordering — that's the same class of gap
      this issue doc itself is about.
