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
status: resolved
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
  "agent-orchestrator@5353b6b (cefi one-shot-role fix + regression test), unified-trading-pm@6f7ed49c2 (review.md fix +
  checkbox flips)"
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

> **🟢 ARCHIVED 2026-08-10 — RESOLVED** (status: resolved, 0 open todos, unlocked). Both remaining checkboxes
> (`[DOCS] P1` cross-role-file audit, `[BACKEND] P2` regression test) independently re-verified and flipped by
> `ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md` todo 3 (2026-08-09) — `agent-orchestrator@5353b6b` +
> `unified-trading-pm@6f7ed49c2`. Archived by that same finalize plan's todo 4.

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
- [x] ✅ [DOCS] P1. **Audit complete 2026-08-09 (slot 30, backend_engineer/infra crafts, batch9 todo) — flip reconciled
      2026-08-09 (slot 24, review craft, batch9-finalize todo 3): `agent-orchestrator@5353b6b` (cefi one-shot-role fix +
      regression test) and `unified-trading-pm@6f7ed49c2` (review.md stale-gate-claim fix) both independently
      re-verified via `git show --stat` against their claimed content before this flip — see below.** First re-confirmed
      live which roles the composer-guard fix now routes to the slot-less register/poll or one-shot branches
      (`server/prompts.py::_REGISTER_POLL_ROLES = {review, main, monitor}`,
      `_ONE_SHOT_ESCALATION_ROLES = {cicd, conflict_resolver, data_pipeline_failure, plan_health, plan_reconciler,     docs_reconciler, ag_closeout_auditor, na_eligibility_auditor, context_scout_auditor,     escalation_queue_reconciler}`
      as of `agent-orchestrator@6166269`/`@41da3e578`, both 2026-08-08). **Both `ag_closeout_auditor` AND
      `na_eligibility_auditor` are now covered** (this doc's own uncertainty — "ag_closeout_auditor may now be covered
      while na_eligibility_auditor may not be" — resolved: both are, and neither file's current STEP-0 claims
      `worker.md`, so no patch was needed for either). Full per-file audit table (role → dispatch shape → worker.md
      required? → file declares it?):

      | role | shape | needs worker.md | file declares it |
                                  |---|---|---|---|
                                  | backend_engineer, infra, quant_dev, ui_developer, data_engineering | craft worker | yes | yes (all 5, already correct) |
                                  | review, main, monitor | register/poll | no | review.md corrected this pass (was stale-claiming it, see below); main/monitor never claimed it |
                                  | cicd, conflict_resolver, data_pipeline_failure, plan_health, plan_reconciler, docs_reconciler, ag_closeout_auditor, na_eligibility_auditor, context_scout_auditor, escalation_queue_reconciler | one-shot | no | none claim it (already correct) |
                                  | cefi_reconciliation_auditor, cefi_mtds_smoke_tester | one-shot (but see finding below) | no | neither claims it (already correct) |

                                  **New finding, fixed same pass (was NOT anticipated by this doc):** `cefi_reconciliation_auditor` and
                                  `cefi_mtds_smoke_tester` (added to `plan_health.py`'s `_MODE_PROMPT_TEMPLATE`/`_MODE_AGENT_KIND` 2026-08-05,
                                  `agent-orchestrator@83314de2`) were never mirrored into `_ONE_SHOT_ESCALATION_ROLES` — a live gap in the exact
                                  mechanism this todo audits, so fixed in the same commit rather than filed as a separate issue (findings-triage:
                                  "in your file → fix in same commit"). Both roles' own files already correctly document the one-shot contract
                                  (`lifecycle: scheduled`, `one_shot_complete: true`); only the composer-side mirror was missing, meaning a real
                                  spawn would have been told to `POST /boot` for a task-fetch that doesn't exist for them.

                                  **Second finding, fixed same pass:** `review.md`'s STEP-0 still claimed "the live read-confirmation gate enforces
                                  `worker.md` for this role's boot path" — true historically (2026-07-27→2026-08-08, the 225+-rejection incident
                                  this doc opened with) but stale post-`6166269`: `review` no longer calls `/api/slots/<N>/boot` at all (its
                                  composed stub routes to the register/poll shape), so the gate described can't fire for it anymore. Corrected to a
                                  historical note; kept the recommendation to read `worker.md` (still useful for review's actual job — auditing
                                  workers against the contract worker.md documents — just not because a gate demands it).

                                  **14:30-16:30Z 2026-08-08 recurrence timing, answered:** PREDATES the fix, not a regression of it —
                                  `agent-orchestrator@6166269` landed 2026-08-08T19:35:33Z, ~3-5h after the reported window; the earlier
                                  `@41da3e578` (one-shot-family extension) landed 08:29:53Z the same day, also before the window. No P0 issue
                                  needed. Evidence: `unified-trading-pm@6f7ed49c2` (review.md fix), `agent-orchestrator@5353b6b` (cefi fix +
                                  regression test).

- [x] ✅ [BACKEND] P2. **Regression test shipped 2026-08-09 — flip reconciled 2026-08-09 (slot 24, review craft,
      batch9-finalize todo 3): re-ran `tests/test_role_file_worker_md_read_sync.py` fresh at
      `agent-orchestrator@5353b6b` — 38/38 passed.** — `agent-orchestrator/tests/test_role_file_worker_md_read_sync.py`:
      asserts, for every craft role file, its own declared STEP-0 read list (basenames) is a superset of
      `expected_read_files("worker", <role>)`'s basenames; and, for every register-poll/one-shot role, that it
      structurally never requires `worker.md` AND its composed stub never references `/boot` — the inverse-drift
      direction found live in `review.md` this same pass. Also includes a live drift-detector
      (`test_hardcoded_inventory_matches_loaded_roles`) so a future new role file that isn't classified into either
      group fails loudly instead of silently going unchecked. `agent-orchestrator@5353b6b`, full `quality-gates.sh`
      green (3059 tests + 262 dashboard tests). (repo: agent-orchestrator)

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

- **2026-08-09 (slot 30, backend_engineer/infra crafts, `ao_satellite_ao_dispatch_batch9_2026_08_08.md` todo 1)**:
  executed both remaining todos — see the evidence appended inline on each above (checkboxes deliberately left unflipped
  per batch9's own "Rules for every worker on this plan"; the paired finalize plan
  `ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md` reconciles the flip back into this doc). Summary: full
  per-file audit found ZERO gaps in the originally-anticipated direction (all 5 craft roles + `ag_closeout_auditor` +
  `na_eligibility_auditor` already correctly documented) but 2 UNANTICIPATED gaps — (1) `cefi_reconciliation_auditor`/
  `cefi_mtds_smoke_tester` missing from `_ONE_SHOT_ESCALATION_ROLES` since their 2026-08-05 addition to `plan_health.py`
  (`agent-orchestrator@83314de2`), fixed in the same commit as this audit; (2) `review.md`'s STEP-0 still carrying a
  now-stale claim that the live /boot gate enforces `worker.md` for it, corrected to a historical note now that `review`
  never calls `/boot` post-`6166269`. Also answered the 2026-08-08 14:30-16:30Z recurrence timing question: it PREDATES
  `6166269` (landed 19:35Z that day), not a regression of it — no P0 needed. Regression test shipped:
  `agent-orchestrator/tests/test_role_file_worker_md_read_sync.py` (`agent-orchestrator@5353b6b`, full
  `quality-gates.sh` green). `unified-trading-pm@6f7ed49c2` carries the `review.md` fix + this Progress Log entry.
- **2026-08-09 (slot 24, review craft, `ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md` todo 3)**: reconciled
  the verified evidence back into this doc's own checkboxes — flipped `[DOCS] P1` and `[BACKEND] P2` to `[x]`.
  Independently re-verified both cited commits before flipping (not just re-reading the prior session's self-report):
  `git show --stat agent-orchestrator@5353b6b` confirmed it touches `server/prompts.py` +
  `tests/test_role_file_worker_md_read_sync.py` + the 2 cefi fixture files exactly as claimed;
  `git show --stat unified-trading-pm@6f7ed49c2` confirmed it touches `agents/review.md` + this doc + the batch9 plan,
  matching the claimed scope; re-ran `tests/test_role_file_worker_md_read_sync.py` fresh — 38/38 passed. No
  discrepancies found. Both items in this doc are now closed; no other open items remain. Set `archive_exempt: true` on
  this flip-only commit per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "sanctioned bridge"
  ruling (2026-08-09) — this doc's own last todo is its own archival trigger, so a flip-only commit would otherwise trip
  `check_archive_candidates.sh --only`'s immediate-archival demand while combining the flip with the `git mv` in one
  commit is separately banned. The field is dropped in the immediately-following archival commit (batch9-finalize todo
  4).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: MOOT, superseded before this marker landed — both
  checkboxes were flipped `[x]` by `ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md` todo 3 (see the entry
  directly above, same day this audit ran) via a real independent re-verification, not a bare pointer.
  `grep -cE '^[[:space:]]*[-*] \[ \]'` = **0** as of this read. This doc is pending archival via that same finalize
  plan's todo 4 — not archived here (outside this sweep's scope), just noting real remaining work is genuinely zero.
