---
doc_type: issue
title:
  GET /api/backlog 500'd fleet-wide because gate_on_depends_unmet_upstreams_on_disk() has no defensive
  handling for a malformed depends_on dep_stem — root cause was one plan's inline YAML comment, but the
  parser crashing instead of skipping is the real gap
summary: >-
  Reported by a review-role agent (agt-11d1df, slot 2, 2026-08-19 ~01:49Z) — GET /api/backlog was returning
  500 Internal Server Error fleet-wide (confirmed both unfiltered and filtered by ?id=), breaking the
  review-agent done-rejected-family cross-check that worker.md/RULES.md rely on to distinguish parked-vs-stuck
  slots. Main verified independently via curl + `journalctl -u orchestrator.service`. Root cause: a `depends_on:`
  line in `plans/active/prediction_satellite_ao_dispatch_batch11_2026_08_13.md` (line 40) had an inline `#`
  comment appended on the SAME line as the machine-parsed `depends_on: [prediction_phase_ab_residuals_2026_07_24]`
  value — the comment text itself contained a `/` (from "(/plan-reconcile predictions_master)"), and whatever
  extracts the dep_stem in `agent-orchestrator/server/dispatch.py::_detailed_fleet_reasons()` /
  `regen_backlog_from_plan.py::gate_on_depends_unmet_upstreams_on_disk()` grabbed everything after the LAST "/"
  in the raw line as the dependency stem, producing a ~500-char garbage stem. That stem then hit
  `regen_backlog_from_plan.py::_resolve_plan_file()`'s `candidate.is_file()` call, which raised
  `OSError: [Errno 36] File name too long` — uncaught, 500ing the whole route for every caller, not just the
  one task whose depends_on happened to be malformed.

  IMMEDIATE FIX ALREADY APPLIED (main, same session, 2026-08-19 ~01:50Z): moved the inline comment off the
  `depends_on:` line in the offending plan onto its own `#`-prefixed lines below `gate_on_depends: true`.
  Verified `GET /api/backlog` returns 200 again post-fix (server reads plan files live from disk, no restart
  needed). This doc tracks two follow-ups NOT done by that immediate fix: (1) commit/ship the doc edit through
  the sanctioned pipeline (main does not ship code/docs itself), (2) the actual code-hardening gap — the backend
  should never let one malformed plan frontmatter field crash a shared, fleet-wide-consumed route; this is a
  correctness/CI HARD RULE candidate (`/api/backlog` is depended on by every review-role agent's parked-vs-stuck
  triage) — a single bad doc should degrade gracefully (skip that task's gate-explanation, log a warning) not
  502-equivalent everyone.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, backlog-route, depends-on, plan-format, review-role, big-finding, production-bug]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch11_2026_08_13.md,
    /plans/epics/predictions_master.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: NA
priority: P1
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
source: >-
  Review-role agent (agt-11d1df, slot 2) message to main (agt-a03340), 2026-08-19 ~01:49Z, corroborated
  independently by main via curl + journalctl.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/routes/backlog.py,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
---

# GET /api/backlog 500 — malformed depends_on comment crashed a shared route

## Timeline

- ~01:49Z: review-role agent (slot 2) messages main reporting `GET /api/backlog` 500ing fleet-wide (confirmed
  3x: unfiltered + filtered by two different `?id=` values). Correctly worked around it via `/api/state` for
  that tick's done-rejected-family check and flagged the route itself as the actionable item.
- ~01:49-01:50Z: main independently reproduces via `curl -o /tmp/backlog_check.json -w "HTTP_STATUS:%{http_code}"
  http://localhost:8765/api/backlog` → 500, then pulls the traceback via
  `journalctl -u orchestrator.service --no-pager -n 200`.
- Traceback (abbreviated, full route: `server/routes/backlog.py:184` →
  `server/dispatch.py::explain_blocked_bulk` (line 973) → `_explain_blocked_with_ctx` (line 911) →
  `_detailed_fleet_reasons` (line 864) → `regen_backlog_from_plan.py::gate_on_depends_unmet_upstreams_on_disk`
  (line 2698) → `_resolve_plan_file` (line 2647) → `candidate.is_file()` →
  `OSError: [Errno 36] File name too long`):

  ```
  OSError: [Errno 36] File name too long: "/home/.../unified-trading-pm/plans/active/plan-reconcile
  predictions_master) -- both todos below were only ever prose-gated on this doc's open-todo count reaching 0
  (see each todo's own text), never machine-enforced; 2 separate dispatched workers (slot-29, slot-12, both
  2026-08-14) had to independently self-skip after wasted round-trips discovering the gate live. Encodes the
  already-stated intent as a real dispatch gate, does not change it..md"
  ```

- Located the source: `plans/active/prediction_satellite_ao_dispatch_batch11_2026_08_13.md:40` (a
  `/plan-reconcile predictions_master` run on 2026-08-19 had added `depends_on: [...]` with a long explanatory
  `#` comment appended on the same line — the comment text contains a literal `/` in `(/plan-reconcile
  predictions_master)`, which is almost certainly why the dep_stem extraction grabbed everything after the last
  `/` in the raw line rather than just the intended slug).
- Main applied the immediate doc fix (moved the comment off the `depends_on:` line, verified `depends_on:
  [prediction_phase_ab_residuals_2026_07_24]` now parses as a clean bare slug per the workspace's own
  `depends_on stays a bare slug` convention) and confirmed `GET /api/backlog` returns 200 again — no server
  restart was needed since plan files are read live from disk at request time.

## Follow-up

- [x] ✅ [SCRIPT] P1. **Commit/ship the doc fix** already applied to
      `plans/active/prediction_satellite_ao_dispatch_batch11_2026_08_13.md` (moved the inline comment off the
      `depends_on:` line) through the sanctioned doc-ship path (`scripts/dev/safe-doc-push.sh` per this
      workspace's "pure doc/plan-flip" convention) — main applied the on-disk edit directly during this
      incident to unblock the live 500 immediately, but did not commit/push it (main's role does not ship
      code/docs). Verify the fix is still in place before shipping (nothing else should have touched this file
      in the interim). Shipped 2026-08-20 via safe-doc-push. (repo: unified-trading-pm)
- [x] ✅ [BACKEND] P1. **Harden `gate_on_depends_unmet_upstreams_on_disk()` / `_resolve_plan_file()`** (both in
      `agent-orchestrator/server/regen_backlog_from_plan.py`) against a malformed `dep_stem` — at minimum,
      catch `OSError`/`FileNotFoundError`-family exceptions from `candidate.is_file()` and treat that dependency
      as "cannot resolve, log a warning, do not crash the caller." A single plan's malformed `depends_on` value
      should never be able to 500 a fleet-wide-consumed route like `/api/backlog` for every task, not just the
      one with the bad dependency. Consider also validating `depends_on` entries look like bare slugs (no
      whitespace, no `/`, no `#`) at `regen_backlog_from_plan.py` regen time and refusing/warning on ingest,
      rather than only failing downstream at explain-time. (repo: agent-orchestrator@b56b3488 + 86ad0df8; Evidence: `quality-gates.sh` — 5,239 passed, 4 skipped, coverage 86.1556%; dashboard 468 passed)
- [x] ✅ [BACKEND] P2. **Audit other `depends_on:`/`parent_epic:`/`supersedes:`/`superseded_by:` lines across
      active plans for the same inline-comment-on-machine-parsed-line pattern** — this specific incident was
      caused by a `/plan-reconcile` run appending an explanatory comment directly onto a machine-parsed
      frontmatter field; the same authoring mistake could exist elsewhere and would silently degrade (or crash)
      the same code paths. A simple `grep -n 'depends_on:.*#' plans/**/*.md` (and the same for the other
      bare-slug fields) would surface any other instances. (repo: unified-trading-pm) — unified-trading-pm@ca6160aa10; Evidence: rg sweep of `plans/active/**/*.md` for inline ` # ` on the 5 machine-parsed bare-slug fields (+`assigned_vm`, same-class) found 41 active docs — 34× on the 5 fields (predominantly `parent_epic: <slug> # was: <old-epic> -- <explanation>` appended by the 2026-08-19 epic-assignment audit, the exact incident authoring mistake at scale; `depends_on`/`superseded_by` also hit) + 8× `assigned_vm: planning # reclassified NA -> planning ...` (parser does not strip comments → garbage VM id → doc drops out of the ingestible set). All 41 fixed (each inline comment moved to its own `#` line above the field); post-fix grep = 0 hits; frontmatter yaml-parse clean across all 41.
- [ ] [BACKEND] P3. **Harden `_parse_frontmatter_assigned_vm`** (`agent-orchestrator/server/regen_backlog_from_plan.py`) to strip inline `# ...` comments (align with `status`/`execution_scope`/`sequential`/`effort`, which all `.split("#")[0]`) — the todo-3 sweep found 8 live issue docs carrying `assigned_vm: planning # reclassified NA -> planning ...` (2026-08-19 na-eligibility-audit), which makes `_resolve_plan_vms()` return a garbage VM id and drops the doc out of the ingestible set (silent starvation of NEW todos; same bug class as this issue's depends_on 500, worse because silent). Docs fixed in todo-3; the parser must not rely on authors never doing it again. (repo: agent-orchestrator)
      **➡️ EXTRACTED 2026-08-21 (ag-closeout-audit, ao tranche Phase 3) → `plans/active/ao_satellite_ao_dispatch_batch4_2026_08_21.md` todo 1.**
- [ ] [BACKEND] P3. **Add a plan-hygiene ratchet check** rejecting inline ` # ` comments on machine-parsed frontmatter field lines (`depends_on`/`parent_epic`/`supersedes`/`superseded_by`/`entry_point_for`/`assigned_vm`/`status`/`execution_scope`/`sequential`/`model_tier`/`effort`/`assigned_role`/`gate_on_depends`) in `unified-trading-pm/scripts/plan-hygiene/` — shrinking-ratchet baseline (mirroring `reference_paths_baseline.yaml`) tolerating the ~30 currently-harmless `status`/`execution_scope`/`sequential`/`effort` instances whose parsers strip comments, so this bug class can never re-land undetected. (repo: unified-trading-pm)
      **➡️ EXTRACTED 2026-08-21 (ag-closeout-audit, ao tranche Phase 3) → `plans/active/ao_satellite_ao_dispatch_batch4_2026_08_21.md` todo 2.**

## Why this is P1, not P0

Does not block trading/critical-path execution — it degrades a review-role diagnostic tool (parked-vs-stuck
triage), and the review agent already had a working fallback via `/api/state`. But it is genuinely cross-cutting
(every review-role agent depends on this route) and was live-broken for at least the ~13 minutes between the
`/plan-reconcile` commit landing and this fix (2026-08-19 ~01:37Z commit per `git log`, discovered ~01:49Z, fixed
~01:50Z) — worth the P1 given the blast radius and because the underlying code-hardening gap (follow-up #2) means
this exact failure mode can recur from any future doc-authoring mistake of the same shape.

## Codex SSOTs

- `/codex/11-project-management/cross-reference-path-convention.md` — the `depends_on stays a bare slug` rule this
  incident violated.
- `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` / worker.md / RULES.md — the review-role
  done-rejected-family cross-check that this route outage broke.

## Progress Log

- **context-scout 2026-08-20**: populated context_scope (4 entries).
- **backend_engineer (slot-5) 2026-08-20**: executed todo 3 — audited every `plans/active/**/*.md` for inline ` # ` on the 5 machine-parsed bare-slug fields (+`assigned_vm`, discovered same-class). Found 41 docs: 34× the 5-field pattern (predominantly `parent_epic: <slug> # was: <old-epic> -- <explanation>` appended by the 2026-08-19 epic-assignment audit — the exact incident authoring mistake at scale) + 8× `assigned_vm: planning # reclassified NA -> planning ...` (`_parse_frontmatter_assigned_vm` does not strip comments → garbage VM id → doc drops out of the ingestible set). Fixed all 41 by moving each inline comment to its own `#` line above the field; verified post-fix grep = 0 hits + frontmatter yaml-parse clean on all 41. Noted ~30 cosmetic `status`/`execution_scope`/`sequential`/`effort` inline comments whose parsers DO strip comments (non-blocking; covered by the new hygiene-check todo). Shipped via safe-doc-push @ca6160aa10.
