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
asset_group: [ao] # retagged 2026-08-02 (/ag-closeout-audit cross-cutting finding 1, corroborated by /na-eligibility-audit cross-cutting) -- was [ci, cross-cutting]; content is 100% agent-orchestrator boot/spawn read-confirmation-gate mechanics, zero cross-cutting/CI vocabulary hits
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, agent-orchestrator, boot-read-confirmation, review-role, docs-drift, live-incident]
related:
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
  - /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md
  - /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md
created: 2026-08-01
author: unknown
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
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md,
    unified-trading-pm/agents/review.md,
    unified-trading-pm/agents/worker.md,
    agent-orchestrator/server/prompts.py,
    agent-orchestrator/server/routes/slots_worker.py,
  ]
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
      `unified-trading-pm/agents/ RULES.md` before any action", no `worker.md` mention. Live hits: slot 7 @
      `2026-08-01T08:11:52Z` and slot 9 @ `2026-08-01T08:49:07Z`, both
      `provided: ["RULES.md", "na_eligibility_auditor.md"]`, `missing: [".../agents/worker.md"]`. -
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

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-02** (tranche `ci`, autonomous): **RECLASSIFY-ELIGIBLE on the merits, but HELD — parked
as `BLOCKED-OPERATOR-DECISION` at the Phase-2 conflict-check. Do NOT flip `assigned_vm` on this verdict alone.** First
audit of this doc (created 2026-08-01, no prior marker). Completeness check: `grep -cE '^- \[ \]'` = 2 = verdicts
reported (the `[OPERATOR] P2` and `[BACKEND] P3` line items above are already `[x]`, not open work).

**Merits** — both open items clear the bounded-outcome bar: the `[DOCS] P1` is a grep-driven multi-file audit-and-patch
against a _named machine oracle_ (`server/prompts.py:expected_read_files`) with an enumerated file set and an explicit
done-when; the `[BACKEND] P2` is a regression test with a clear pass/fail assertion. No undecided design judgment.

**Why held anyway — two independent conflicts, both verified live this run:**

1. **A same-day sibling audit recommends retagging this doc OUT of the `ci` tranche.** The 2026-08-02
   `/ag-closeout-audit cross-cutting` run (dispatch `agt-f23055`, slot 12) classified this doc `exclude_cross_cutting`
   and recorded in `/plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_02.md` that
   `asset_group: [ci, cross-cutting]` is a **double mistag** — content is 100% agent-orchestrator boot/spawn mechanics,
   and the `ci` tag traces only to which NA-tranche audit happened to discover the doc (this doc's own `source:` field
   says so), not to a topical claim. Its recommendation is `[ao]`. `ci` owns this doc today only by the inventory
   script's fallback rule (`parent_epic: infrastructure_master` maps to `infra`, which is not among this doc's own
   tranches, so ownership falls back to `tranches[0]` = `ci`). Flipping `assigned_vm` from a tranche that is about to
   stop owning the doc is precisely the last-writer-wins outcome the primary-owner rule forbids.
2. **An adjacent NA doc claims overlapping ground and could moot part of the `[DOCS] P1` scope.**
   `/plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md`
   (`assigned_vm: NA`, `parent_epic: agent_operating_framework_master` → `ao` tranche) carries an open `[SCRIPT] P2` to
   make `server/prompts.py::_compose()` route lifecycle roles to the slot-less register/poll block, plus a `[SCRIPT] P1`
   extending that guard to one-shot lifecycle/audit roles (`ag_closeout_auditor` and siblings). If that lands, the
   affected roles stop being asked for `worker.md` at all — so patching every role file's STEP-0 to _add_ `worker.md`
   could be partly redundant or actively wrong for exactly the roles this doc cites as live victims
   (`na_eligibility_auditor.md`, `ag_closeout_auditor.md`). Not a verbatim duplicate claim, but a real ordering
   dependency that a worker dispatched off this doc alone would not see.

**Options:** **A [WORKER REC]** — retag `asset_group` → `[ao]` per the sibling run's recommendation, let the `ao`
tranche own the reclassification decision, and sequence it behind (or jointly with) the `boot_composer` composer-guard
fix so the two do not fight over the same role files. **B** — flip `assigned_vm: planning` here now and accept both the
pending retag and the ordering risk against `boot_composer`. **C** — keep NA with no retag and revisit once
`boot_composer`'s composer-guard todos are resolved, at which point the remaining `[DOCS] P1` scope is unambiguous.

## Progress Log

- **2026-08-01 (review agent, slot 1, agt-fed62c)**: Booted clean on the corrected `review.md` (first attempt,
  `[RULES.md, worker.md, review.md]`), confirming the fix works for a fresh session. Closed the `[OPERATOR] P2` todo
  with live evidence (zero slot-1 rejections since the one expected post-fix straggler at 08:23:22Z). Found the same gap
  live in 2 more role files while investigating a separate, unrelated slot-1 tmux-collision incident from the same
  session window (see
  `/plans/archive/issues/persistent_slot_tmux_session_hijacked_by_transient_plan_health_dispatch_2026_08_01.md` — a
  different bug, not a duplicate of this one) — added the 2 todos above and bumped this doc's priority P1→P1 (unchanged
  numeric value, but re-affirmed active given the live multi-file recurrence rather than letting it read as closed).
- **context-scout 2026-08-03**: populated context_scope (6 entries).
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. Both open items already passed a full
  Phase-2 conflict-check (ci tranche, 2026-08-02) that found them bounded-eligible on the merits but explicitly parked
  the flip pending 2 named conflicts. Of those, only the tranche-ownership retag has since resolved (`asset_group` ->
  `ao`, 2026-08-02, confirmed live) — confirming this run is the correct one to hold the decision per that verdict's own
  Option A. The second conflict (sequencing behind
  `boot_composer_misroutes_lifecycle_roles_ into_worker_boot_branch_2026_07_31.md`'s composer-guard fix) remains open —
  verified live: all 3 of that doc's `[SCRIPT]` todos are still unchecked, and it is itself held KEEP-NA on a standing
  corpus ruling that AO/orchestrator dispatch-and-state machinery stays human-reviewed even when a fix looks mechanical.
  No operator has answered this doc's own A/B/C options yet, so the hold continues.

- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 6 entries resolve on disk (codex
  SSOT + the conflicting composer-guard doc + the 2 role-file docs + the 2 backend source files the mechanism section
  cites) — no changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **2026-08-08 (main agt-22de53, relaying a review-craft finding, msg 4310)**: `boot_read_unconfirmed` is recurring live
  for slot 1 (review role) again — review reported ~6 of ~14 `slot_boot` cycles in the 14:30-16:30Z window hit
  `boot_read_unconfirmed` (428, `missing: [".../agents/worker.md"]`) on the first `/boot` attempt, confirming this is
  not fully resolved despite the 2026-08-01 `agents/review.md` STEP-0 text fix. Reporter's own boot prompt this session
  only declared `RULES.md`+`review.md` and had to proactively add `worker.md` — consistent with the still-open
  `[DOCS] P1` todo above (audit every craft-role file) not yet being actioned, or with the auto-composed boot prompt
  (server-side, not the `review.md` doc text) being the actual source for at least some fraction of boots, which would
  point at `boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md`'s composer-guard fix instead.
  Not independently verified against `/api/activity` by main this pass — relaying review's evidence as-is. Re-affirms
  the `[DOCS] P1` and `[BACKEND] P2` todos above are still live, not stale.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
