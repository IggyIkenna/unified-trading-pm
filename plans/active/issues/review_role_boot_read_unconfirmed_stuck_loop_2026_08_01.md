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

- [x] ✅ [OPERATOR] P2. **Confirmed clean for slot 1 — reviewed by slot-1's own review-agent session (agt-fed62c),
      2026-08-01 ~13:10.** `GET /api/activity?type=boot_read_unconfirmed` shows exactly ONE more slot-1 rejection after
      this doc's fix commit (`unified-trading-pm@bd604958`, landed 2026-08-01T08:20:43Z): a single straggler at
      `2026-08-01T08:23:22Z`, 3 minutes after the fix — consistent with a session that had already loaded its system
      prompt/`read_files` declaration before the fix landed (exactly the self-resolving case this todo anticipated, not
      a fix failure). Zero slot-1 `boot_read_unconfirmed` events since 08:23:22Z through current time (~5h clean); my
      own fresh `/boot` at 12:56:13Z declared `[RULES.md, worker.md, review.md]` per the corrected STEP 0 and cleared on
      the first attempt. No operator action needed for slot 1 specifically — see the new todo below for a broader,
      NOT-yet-fixed recurrence of the same bug class in other role files.
- [x] ✅ [BACKEND] P3→**upgraded to P1, see new todo below** — the speculative "future re-drift" this todo worried about
      is not hypothetical: it is LIVE, in at least 2 other role files, as of this same review pass.
- [ ] [DOCS] P1. **The docs fix only patched `agents/review.md` — the identical STEP-0 gap (missing `worker.md` in the
      role file's own declared pre-boot reads) independently reproduces in at least 2 other craft-role files, with LIVE
      `boot_read_unconfirmed` events, one as recent as 90 minutes before this update:** -
      `agents/na_eligibility_auditor.md` — STEP 0 (around line 104) says only "read
      `unified-trading-pm/agents/       RULES.md` before any action", no `worker.md` mention. Live hits: slot 7 @
      `2026-08-01T08:11:52Z` and slot 9 @ `2026-08-01T08:49:07Z`, both
      `provided: ["RULES.md", "na_eligibility_auditor.md"]`, `missing:       [".../agents/worker.md"]`. -
      `agents/ag_closeout_auditor.md` — STEP 0 (around line 96) has the identical gap. Live hit: slot 12 @
      `2026-08-01T11:35:12Z`, `provided: ["RULES.md", "ag_closeout_auditor.md"]`, same `missing`. Fix: audit EVERY file
      in `unified-trading-pm/agents/*.md` whose `slot_role` is not literally `"worker"` (i.e. every craft/audit role:
      `backend_engineer`, `quant_dev`, `ui_developer`, `infra`, `data_engineering`, `cicd`, `conflict_resolver`,
      `context_scout_auditor`, `data_pipeline_failure`, `docs_reconciler`, `plan_health`, `plan_reconciler`, `monitor`,
      plus the two named above) against `server/prompts.py:expected_read_files` — for each whose expected set includes
      `worker.md`, confirm the file's own STEP-0/boot section explicitly instructs reading it (mirroring `review.md`'s
      current corrected wording), not just `RULES.md`. Patch every file missing it in one pass so this doesn't surface a
      third time per-file. (repo: unified-trading-pm)
- [ ] [BACKEND] P2. Build the regression test the original P3 todo proposed — assert, for every role file, that its own
      declared STEP-0 read list (basenames) is a superset of `expected_read_files("worker", <that role's slot_role>)`'s
      basenames — now with concrete proof (3 live incidents across 3 different role files in one week) that hand-sync
      alone does not hold. (repo: agent-orchestrator)

## Progress Log

- **2026-08-01 (review agent, slot 1, agt-fed62c)**: Booted clean on the corrected `review.md` (first attempt,
  `[RULES.md, worker.md, review.md]`), confirming the fix works for a fresh session. Closed the `[OPERATOR] P2` todo
  with live evidence (zero slot-1 rejections since the one expected post-fix straggler at 08:23:22Z). Found the same gap
  live in 2 more role files while investigating a separate, unrelated slot-1 tmux-collision incident from the same
  session window (see
  `/plans/active/issues/persistent_slot_tmux_session_hijacked_by_transient_plan_health_dispatch_2026_08_01.md` — a
  different bug, not a duplicate of this one) — added the 2 todos above and bumped this doc's priority P1→P1 (unchanged
  numeric value, but re-affirmed active given the live multi-file recurrence rather than letting it read as closed).
