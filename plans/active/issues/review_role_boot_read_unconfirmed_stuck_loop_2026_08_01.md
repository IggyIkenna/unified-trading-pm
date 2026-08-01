---
doc_type: issue
title:
  Review-role boot stuck in a 225+-rejection `boot_read_unconfirmed` loop since 2026-07-27 — docs fixed, live slot needs
  attention
summary: >-
  `agents/review.md`'s own "Boot — read the canonical files first" section named only `RULES.md` as the required
  pre-poll read — it never listed `worker.md`. But the live `/api/slots/<N>/boot` read-confirmation gate
  (`server/routes/slots_worker.py`) DOES require `worker.md` for a review-role boot in the common case (a craft-scoped
  worker path where `spawn_base_role` stays `"worker"`, which resolves `expected_read_files("worker", "review")` =
  `[RULES.md, worker.md, review.md]`). The docs/code mismatch meant a fresh review session that followed `review.md`'s
  own instructions literally (RULES.md + review.md only) got rejected 428 on every single `/boot` call. Confirmed live
  via `GET /api/activity?slot=1`: **225 `boot_read_unconfirmed` events for slot 1 between 2026-07-27T03:06:16Z and
  2026-08-01T01:23:12Z** (still recurring as of this doc's creation), every single one citing `missing:
  [".../agents/worker.md"]`, `provided: ["RULES.md", "review.md"]` — i.e. slot 1 has been retrying a review boot roughly
  every 5-15 minutes for close to 5 days without ever successfully clearing this specific gate on that declared-files
  basis (interspersed activity shows the slot DOES do other work in between, e.g.
  `agentkeeper_review_succeeded`/`escalation_dispatched` events — so this is a recurring re-trigger, not a single wedged
  tmux session, but the sheer repetition count means real wasted cycles every occurrence).
status: open
nature: issue
asset_group: [ci, cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, agent-orchestrator, boot-read-confirmation, review-role, docs-drift, live-incident]
related:
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
  - /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md
created: 2026-08-01
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
locked_by:
resolved_by:
depends_on: []
gate_on_depends: false
supersedes:
superseded_by:
source: >-
  Discovered during `/na-eligibility-audit ci` (2026-08-01) while classifying
  `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`'s own `[DOCS] P3` todo (opened
  2026-07-31, citing this exact `boot_read_unconfirmed` rejection as its trigger). Independently re-verified via a live
  `GET /api/activity?slot=1` query (not just the source doc's self-report) before acting.
---

# Review-role boot stuck in a 225+-rejection `boot_read_unconfirmed` loop since 2026-07-27

## What's confirmed

- `server/routes/slots_worker.py`'s read-confirmation gate: for a non-typed (craft-scoped) worker boot,
  `expected = prompts.expected_read_files("worker", req.slot_role)`, which (`server/prompts.py:111-124`) resolves to
  `[RULES.md, worker.md, <craft file>]` when `assigned_role != "worker"` and the craft file exists — for
  `slot_role="review"`, that craft file is `review.md`, so the full expected set is `[RULES.md, worker.md, review.md]`.
- `agents/review.md`'s own "Boot — read the canonical files first" section (pre-fix) named only `RULES.md` as the
  literal required pre-poll read — a session following that instruction verbatim declares `[RULES.md, review.md]` and is
  missing `worker.md` every time.
- Live evidence: 225 `boot_read_unconfirmed` activity events for `slot_id=1` between 2026-07-27T03:06:16Z and
  2026-08-01T01:23:12Z (this doc's creation time), each with `details.missing` naming `.../agents/worker.md` and
  `details.provided` = `["RULES.md", "review.md"]` verbatim, every time.

## Fixed this pass

- `agents/review.md`'s STEP 0 now explicitly instructs reading `RULES.md` **and** `worker.md` (in order) before polling,
  and calls out the live-enforced `read_files` requirement explicitly so a fresh review boot declares the correct set on
  its first `/boot` call. Landed same commit as this issue doc.

## Not fixed / needs attention (NOT resolved by the docs fix alone)

- [ ] [OPERATOR] P2. **Confirm whether slot 1's current occupant is still hitting this rejection after the docs fix, or
      whether it self-recovered.** A doc fix only helps a FRESH review boot that reads the corrected file; if slot 1's
      current tmux session is running from an already-loaded system prompt / already-declared `read_files` list that
      predates this fix, it will keep failing until that session is respawned. Check `GET /api/activity?slot=1` for any
      `boot_read_unconfirmed` event with a timestamp AFTER this doc's `created` date — if one exists, the session needs
      an operator-directed respawn/kill+restart (per CLAUDE.md's "never manually kill tmux" absent a confirmed
      dead/stuck claim — this is exactly that judgment call, not a mechanical worker-alone fix).
- [ ] [BACKEND] P3. Consider whether `server/prompts.py:expected_read_files`'s dependency on `spawn_base_role` (rather
      than always deriving straight from `slot_role`) is the right long-term contract for a persistent, non-typed role
      like `review` — this incident is a symptom of the docs (hand-maintained) and the code (`expected_read_files`)
      being two independent sources of truth for the same required-reads set, with no automated check that they agree. A
      regression test asserting `agents/review.md`'s own declared STEP-0 read list is a superset of
      `expected_read_files("worker", "review")`'s basenames would catch a future re-drift mechanically instead of via a
      live 225-event incident.
