---
doc_type: issue
title: "plan_reconciler findings — ui tranche, 2026-08-10 (dispatch agt-ec1688)"
summary: >-
  Second sharded plan_reconciler run over the `ui` asset_group tranche (23 docs: 11 plans + 12 issues, incl. 3 batch
  docs + 3 finalize docs). Re-checked every item filed by the 2026-08-07 run (agt-a40e5f), 5-hunter fan-out for fresh
  coverage, ~20 fixes applied across 10 files, 4 items routed to the operator via /blocked (locked_by placeholder
  ruling, GCS-delete autonomy contradiction, 2 codex-drift items needing new prose/cross-doc scope).
status: open
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, ui, 2026-08-10]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/archive/2026_08/issues/plan_reconciler_findings_2026_08_07.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /plans/active/ui_satellite_ao_dispatch_batch3_2026_08_09.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-21"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: ui_developer
drift_direction: none
locked_by:
locked_since:
resolved_by:
source: "plan_reconciler dispatch agt-ec1688 — sharded ui tranche run 2026-08-10"
depends_on: []
context_scope:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/03-deployment/data-status-ui-surface.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# plan_reconciler findings — ui tranche, 2026-08-10

> **Run**: dispatch `agt-ec1688`, sharded to `tranche=ui`. 23 docs in scope (11 plans + 12 issues, incl. 3
> satellite-dispatch batches + 3 finalize docs). This is the SECOND `/plan-reconcile ui` run — the first (`agt-a40e5f`,
> 2026-08-07) applied zero fixes (grace/lock blocked everything) and is linked above.

## Coverage (hunters / batches / docs)

- **Hunters**: 5 (Track1+2 content, Track3+4 content, AO-dispatch batches + parked audits, codex-alignment + epics,
  hedge/zero-checkbox/referrer sweep), all `model=sonnet`, read-only, `SUB_AGENT_MANDATORY_RULES.md` pasted at spawn.
- **Docs read in full**: all 23 ui-tranche docs (21 non-grace + 2 grace-protected read as context) + 2 related epics
  (`deployment_and_user_management_master.md`, `observability_master.md`) + 3 codex SSOTs
  (`deployment-observability.md`, `data-status-ui-surface.md`, `ui-testing-layers.md`) + the normative refs.
- **Candidates surfaced**: ~30 across contradictions, missed-flips, hygiene/formatting, AO-dispatch-readiness, and codex
  drift. Self-verified (independent re-derivation, not hunter-trust) before any apply — see below.

## Flips verified

1. `plans/active/artifact_pipeline_observability_2026_07_17.md` — "File the deployment-bucket-resolution issue doc"
   `[REVIEW] P3` todo. HARD evidence: `plans/active/issues/deployment_bucket_resolution_gaps_2026_08_09.md` confirmed on
   disk (`ls`), sourced explicitly from this exact todo per `ui_satellite_ao_dispatch_batch3_2026_08_09.md`'s own
   todo 1. Flipped `[ ]`→`[x]`. Commit `69a5ac46e2`.
2. `plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` — the stdout/stderr-blackout `[BACKEND] P1`
   "DEFERRED-BY-DESIGN" todo. HARD evidence: its own done-when ("stdout resuming") is satisfied per the doc's own
   2026-08-08 (slot 12, review) Progress Log entry confirming `deployment-api@785405d`'s pid-role logging appeared live.
   Flipped `[ ]`→`[x]`. Companion `[REVIEW] P1` todo NOT flipped (its 2nd clause — "read the next SIGABRT's dump" — is
   genuinely still open, no SIGABRT has recurred since 2026-08-04; annotated with the partial-resolution instead,
   cross-referencing the still-open `[BACKEND] P3` follow-up). Commit `2e85d2348a`.

## Contradictions

1. **[FIXED]** `deployment_registry_firestore_migration_2026_07_14.md` — frontmatter (`assigned_vm: planning`,
   reclassified 2026-07-30 na-eligibility-audit) contradicted by its own summary + body blockquote (both still said
   "non-dispatched design/index doc", written 2026-07-14, never updated). Verified reality: frontmatter is current (0
   open todos right now, but the field itself is correct per a deliberate, evidenced ruling) — aligned the stale prose
   to match. Commit `2e85d2348a`.
2. **[FIXED]** Same doc's phase-index table, P3 status cell — claimed "prod Firestore `deployments` measured EMPTY
   2026-07-17" as the current blocker; `deployment_registry_firestore_p3_cutover_2026_07_14.md`'s own 2026-08-08
   remeasurement (2,351 docs, 557 stale `running`, reaper gap — NOT empty) supersedes it. Updated the cell to cite
   current numbers. Commit `2e85d2348a`.
3. **[x] [FIXED 2026-08-15]** `deployment_registry_firestore_migration_2026_07_14.md` ("Fully autonomous — no operator
   gates" for the P3 GCS delete) vs. `deployment_registry_firestore_p3_cutover_2026_07_14.md` ("🔴 BLOCKED... GCS DELETE
   HELD UNTIL OPERATOR CONFIRMS", "operator-supervised"). **Operator ruling: fully autonomous is correct** — the
   `..._p3_cutover_2026_07_14.md` banner was the stale side (it already contradicted its own dispatch-note above it,
   "Fully autonomous — NO operator gates"). Replaced the banner with a corrected framing that keeps the real, still-
   unmet 4-item GO/NO-GO data-precondition checklist in force (technical HALT unchanged) while removing the "operator
   confirms" authority framing. Documentation-only — no GCS object touched, no delete triggered. Commit: pending (this
   reconciliation session).
4. **[REFUTED — stale citation, no action]** Line-683 `artifact_pipeline_observability_2026_07_17.md` prose-open-item
   claim (from a 2026-08-08 `ag_closeout_auditor` finding cited in this doc's own history) — already fixed the SAME day
   by na-eligibility-audit (split into a real checkbox, now at line ~694-699), before this run started. The citing
   finding is itself now stale; no live defect.
5. **[REFUTED — non-contradiction, resolved]** "No batch 3 was drafted" (`ui_consolidated_closeout_2026_07_30.md`
   2026-08-09 Progress Log, `ag_closeout_auditor agt-db95b9`) vs. `ui_satellite_ao_dispatch_batch3_2026_08_09.md`
   existing. Resolved: different mechanism (a manual "round11" cross-tranche sweep, not that day's
   `/ag-closeout-audit ui` dispatch), ~7h43m later same day, different `parent_epic`. Both docs independently accurate
   as written. Forward-looking gap noted (batch1_finalize todo 4 predates batch3, doesn't know about its extraction) —
   folded into the Filed section below rather than re-litigated here.

## Doc-drift

1. **[x] [FIXED 2026-08-15]** `plans/epics/deployment_and_user_management_master.md` — 2 stale UI-Verification-Contract
   table rows: (a) `tests/playbooks/auth_flow.spec.ts` for the user-management-ui surface that was dropped 2026-07-12
   per this SAME doc's own "Owns" section (live-verified: file doesn't exist); (b)
   `tests/widgets/deployment-lifecycle.test.tsx` — no `tests/widgets/` directory exists in deployment-ui at all, and the
   codex SSOT (`ui-testing-layers.md`) itself documents deployment-ui as not having an L1.5 widget-harness layer.
   **Operator ruling (2026-08-15): `locked_by: live-defi-rollout` on this epic is the corpus-wide placeholder-lock bug
   (root-caused in `issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`), not a real lock — safe
   to edit despite the field being set.** Removed both stale rows, added a footnote explaining why (surface dropped / no
   L1.5 widget-harness layer for deployment-ui, per verified `ls` + the codex SSOT's own ownership table). Commit:
   pending (this reconciliation session).
2. **[ROUTED]** `/codex/03-deployment/data-status-ui-surface.md` — behavioral drift beyond the mechanical path fix
   applied below: (a) the 404-on-missing-date contract doesn't mention the 14-day fallback-lookback behavior shipped
   2026-07-15; (b) the "Top-level keys" table omits 2 additive response fields shipped 2026-07-17
   (`requested_date`/`resolved_date`). Both need newly-composed documentation prose, not a pure substitution — outside
   the mechanical codex-staleness carve-out (STEP 5.f2 requires a single unambiguous substitution, no invented content).
   Asked via `/blocked`. **[x] [RESOLVED — fixed by `unified-trading-pm@bfd94b8d0c`, 2026-08-12]**: that commit ("fix 5
   doc_drift findings from blocked-question triage (batch 1/3)") added the 14-day
   `_HONEST_COVERAGE_FALLBACK_LOOKBACK_DAYS` fallback-lookback prose and the `requested_date`/`resolved_date`
   additive-provenance-fields prose to this doc's API-endpoint section — both confirmed present on a fresh read of the
   live doc during this 2026-08-15 reconciliation session.
3. **[x] [FIXED 2026-08-15]** `/codex/06-coding-standards/ui-testing-layers.md` + 2 sibling codex docs
   (`/codex/14-customer-journeys/testing/README.md`, `test-matrix.md`) — corpus-wide stale UI test-path convention:
   `tests/playbooks/**` should be `tests/e2e/playbooks/**` (per hunter's git-log check, this was wrong from inception,
   not a later drift); `lib/registry/route-manifest.ts` doesn't exist in `unified-trading-system-ui`;
   `tests/smoke/routes.spec.ts` naming doesn't match that repo's real `*.smoke.spec.ts` convention (it DOES exist
   correctly in deployment-ui — the drift is specific to the doc's Next.js worked example). Load-bearing: this is the
   literal source of the `regression: tests/playbooks/...` evidence-tag convention `plans/PLAN_FORMAT.md` § 9 requires
   on every UI plan tick. **Operator ruling (2026-08-15): approved, correct to verified-current paths.** Re-verified
   every claim independently via `ls`/`find` in `unified-trading-system-ui` (not hunter-trusted) before applying:
   confirmed `tests/e2e/playbooks/` is real and `tests/playbooks/` doesn't exist; confirmed `lib/registry/` has no
   `route-manifest.ts`; confirmed `tests/smoke/` uses the `*.smoke.spec.ts` naming convention with no `routes.spec.ts`
   file. Applied the `tests/playbooks/**` → `tests/e2e/playbooks/**` path fix corpus-wide across all 3 docs (5 sites in
   `ui-testing-layers.md`: Layer 3a "Where it lives", Playwright Projects table, Plan-Level Enforcement table ×2, plus
   the README.md tree/comments/prose and test-matrix.md's staging-future path). For the route-manifest.ts /
   routes.spec.ts absence in `unified-trading-system-ui` specifically, added verified-current annotations marking those
   sections as the aspirational/illustrative Next.js pattern (real and live only in `deployment-ui`) rather than
   inventing a substitute file path. Also flagged (not fixed — out of this pass's verified scope) that
   `testing/README.md`'s finer scaffolding structure (per-playbook filenames, `helpers/` subdirectory) doesn't fully
   match the live `tests/e2e/playbooks/` directory listing — needs its own closer-read pass. Commit: pending (this
   reconciliation session).
4. **[FLAG ONLY, cannot fix]** `cursor-configs/skills/plan-reconcile/SKILL.md:559` + `agents/plan_reconciler.md:297`
   both still describe opus as this skill's own automatic dispatch default ("spawns the worker (opus / effort max /
   thinking on)"; "you are opus/max") — contradicts CLAUDE.md's 2026-08-07/08-08 ruling (opus-required = ZERO
   categories, manual-only) AND `plan_reconciler.md`'s own frontmatter (`model: sonnet`) AND my own boot session
   (`MODEL=claude-sonnet-5`). Both files are outside `plans/**` — no plan_reconciler dispatch can fix them. Filed below
   for a human/operator session.

## Hygiene fixes

1. **[FIXED]** `plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md` — 42 lines carrying 278-280 leading
   spaces (the known corpus-wide prettier proseWrap continuation-padding idempotency bug — tracked in
   `issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md`, a DIFFERENT sibling plan_reconciler run is actively
   working that issue's own todo today in the cross-cutting tranche). This padding was hiding an important "read this
   before starting" design-rationale note behind what renders as a giant blank code block. Collapsed to the
   structurally-correct 6-space indent; verified content-only via `git diff -w` (empty diff) before committing. Commit
   `69a5ac46e2`.
2. **[FIXED]** `plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md` — `model_tier: opus-required`
   (stale since 2026-07-14 creation) corrected to `sonnet` per CLAUDE.md's current ruling; field isn't part of the
   enforced `docspec.py` schema (legacy vestige), single unambiguous substitution. Commit `2e85d2348a`.
3. **[FIXED]** `plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md` +
   `plans/active/deployment_registry_firestore_p5_verify_2026_07_14.md` — added `sequential: true` where a hunter found
   a real internal todo-ordering dependency with no machine gate (design-gate-before-implementation; ship
   -after-doc-updates). Both currently `assigned_vm: NA` (zero live dispatch risk today) — fixed preemptively before
   either is ever reclassified to `planning`. Restricts scheduling only, no content/meaning change. Commit `cb78f3deec`.
4. **[FIXED]** `plans/active/ui_satellite_ao_dispatch_batch2_finalize_2026_08_08.md` — 2 occurrences of "batch-3
   candidate" reworded to "future-satellite-batch candidate" (name now taken by an unrelated doc,
   `ui_satellite_ao_dispatch_batch3_2026_08_09.md`, drafted after this text was written). Commit `6232701a11`.
5. **[FIXED]** `plans/archive/2026_08/issues/plan_reconciler_findings_2026_08_07.md` — converted a 2×-flagged,
   never-tracked prose-only finding (missing `ACTIVE_INDEX.md` normative ref) into a real `[DOC] P3` todo per the "every
   follow-up is a todo, never prose" rule. Commit `69a5ac46e2`.

## Codex corrections applied (mechanical, evidence-cited)

Narrow carve-out (STEP 5.f2): HARD evidence, single unambiguous substitution, no HARD-STOP governance area touched, no
new measurement run — self-verified every path with `ls`/`grep` before applying, not hunter-trusted.

1. `/codex/05-infrastructure/deployment-observability.md` — 5 dangling `plans/active/...` refs repointed to their
   confirmed `plans/archive/...` locations (lines citing `deployment_ui_cost_per_day_accuracy_2026_07_20.md` ×2,
   `terminated_vm_disk_orphan_no_reaper_2026_06_30.md`,
   `deployment_observability_parity_live_batch_paper_2026_06_22.md`, `deployment_ui_vm_log_viewer_2026_07_20.md`) + 4
   missing-leading-slash cosmetic fixes on frontmatter array entries (repo-root-relative convention). Commit
   `6232701a11`.
2. `/codex/03-deployment/data-status-ui-surface.md` — dangling plan ref
   (`cross_asset_group_catalogue_audit_2026_05_10.md` → its archived path) + stale source-file path for
   `get_honest_coverage()` (the flat `data_status.py` module was split into a package 2026-06-10, further 2026-07-31 —
   function name unchanged, fixed in BOTH places it appeared in this doc: the "API endpoint" section AND the
   "Cross-references" list at the bottom, the second one missed by the hunter that surfaced this). Commit `6232701a11`.

## Filed

1. `plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` — NEW issue doc. Root-caused
   `locked_by: live-defi-rollout` (96 docs corpus-wide, plus at least 1 epic) to a hardcoded placeholder in
   `scripts/plans/fix_epic_frontmatter_2026_05_21.py:133`, not any real actor claim. Directly blocks the
   `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` archive candidate (5 consecutive audit passes
   flagged, zero resolution). 3 options proposed (A: treat the literal value as equivalent to unlocked; B: one-time
   corpus sweep clearing the bad value; C: manual per-doc). Asked via `/blocked`. Commit `50f079ecfe`.
2. Contradiction #3 above (GCS-delete autonomy vs. operator-gate framing) — asked via `/blocked`, no separate issue doc
   (small enough to resolve inline once ruled — will apply directly to both docs on answer). **RESOLVED 2026-08-15** —
   see Contradiction #3 above.
3. Doc-drift #2 above (data-status-ui-surface.md behavioral drift, needs new prose) — asked via `/blocked`. **RESOLVED
   2026-08-15** — see Doc-drift #2 above (self-resolved by an unrelated commit before the ruling was needed).
4. Doc-drift #3 above (ui-testing-layers.md corpus-wide stale test-path convention) — asked via `/blocked`. **RESOLVED
   2026-08-15** — see Doc-drift #3 above.
5. Doc-drift #1 above (epic's 2 stale verification-contract rows, entangled with the locked_by lock) — folded into the
   locked_by question's context, not a separate ask (resolves once that lock question is ruled). **RESOLVED 2026-08-15**
   — see Doc-drift #1 above (operator confirmed the `locked_by` value is the corpus-wide placeholder bug, safe to edit;
   the corpus-wide `locked_by` question itself, tracked as items 1-2 in
   `issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`). **Status update (plan_reconciler
   agt-8fc5a6, 2026-08-16, read that doc fresh)**: item 1 (the ruling — may a confirmed-dead worker's lock ever
   auto-clear) is now RESOLVED — operator ruled Option A 2026-08-15. Item 2 (the actual one-off script clearing the
   placeholder value corpus-wide) remains open — a `[BACKEND] P1` implementation todo, not yet run. That doc is
   `asset_group: [ao]`, outside this ui-tranche doc's write-scope — not edited directly, only this cross-reference
   corrected.
6. `plans/active/ui_consolidated_closeout_2026_07_30.md` Todo 6 ("First `/ag-closeout-audit ui` + `/plan-reconcile ui`
   runs...") — will flip at STEP 7 flush citing this run's own dispatch (both skills have now run on this tranche at
   least once; `/ag-closeout-audit ui` ×4, `/plan-reconcile ui` ×2 counting 2026-08-07). **RESOLVED (2026-08-10,
   prose-findings formalization sweep): confirmed done.** `plans/active/ui_consolidated_closeout_2026_07_30.md:194` is
   `[x]` — this run's own STEP 7 flush did flip it as promised (see that doc's own Progress Log, "Flipped Todo 6
   above"). No further action.
7. `plans/active/deployment_registry_firestore_migration_2026_07_14_finalize_2026_07_30.md`'s Out-of-scope successors (3
   real follow-up items in `deployment_registry_firestore_migration_2026_07_14.md`, prose-only, no tracking doc cited:
   real-time UI listeners, lifecycle-events archival, run.log overwrite efficiency) — NOT converted to todos here
   (explicitly "out of scope" for that plan, and inventing new tracked plans for genuinely new future work is bigger
   than this run's reconciliation mandate). Noted for a human session to decide where these belong. **Formalized
   2026-08-10 — see `## Todos` below (todo 1); the finalize doc is archived
   (`plans/archive/2026_07/deployment_registry_firestore_migration_2026_07_14_finalize_2026_07_30.md`), the 3 items
   actually live in the still-active parent's own "Out of scope (named successors)" section
   (`plans/active/deployment_registry_firestore_migration_2026_07_14.md:187-190`).**
8. `deployment_registry_firestore_p3_cutover_2026_07_14.md` todo "the agreed window" (soak duration) — no duration
   stated anywhere in the doc; missing definition-of-done, needs domain knowledge this run doesn't have. Noted, not
   resolved. **Formalized 2026-08-10 — see `## Todos` below (todo 2); re-confirmed still undefined (grepped the doc
   fresh, no duration anywhere), and the phase is currently HALTED on an earlier precondition regardless (see that doc's
   own Progress Log).**
9. `ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md` todo 1's conflict-check — named only the 2 batch plans, not
   `batch1_finalize`'s own still-open todo 4, which touches the same file
   (`artifact_pipeline_observability_2026_07_17.md`'s checkboxes). Potential future same-file dispatch collision if both
   ever run concurrently. Noted for whoever dispatches either. **Formalized 2026-08-10 — see `## Todos` below (todo 3);
   re-confirmed both todos (`batch1_finalize` todo 4 at line 280, `batch3_finalize` todo 1 at line 56) are still open
   and the collision risk is unchanged.**
10. `plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` archive candidate —
    all 3 todos independently re-verified done (2 hunters cross-checked via the deployment-ui git history this run,
    confirming no regression through later renames). Was blocked solely by the `locked_by` bug (item 1 above);
    **RESOLVED 2026-08-10 via a targeted operator-approved `[unlock-plan]` for this one doc** (did not wait on item 1's
    corpus-wide ruling) — unlocked + archived to the path above.

## Todos

> Added 2026-08-10 (prose-findings formalization sweep) — formalizing 3 genuinely-still-open Filed items (7, 8, 9 above)
> that were left as narrative flags rather than tracked checkboxes, per the workspace's "every follow-up is a `- [ ]`
> todo, never prose" hard rule. `assigned_vm`/`status` on this doc left untouched.

- [ ] [DOC] P3. **D114 ruling applied (2026-08-21, issues_corpus_completion_dispatch_2026_08_21.md ledger): author 3
      separate plan docs for the orphaned "Out of scope (named successors)" items in
      `plans/active/deployment_registry_firestore_migration_2026_07_14.md`** — (1) real-time UI listeners /
      push-instead-of-poll, (2) archiving emitted `lifecycle-events`/resource samples to a durable event log, (3)
      `run.log` whole-file-overwrite efficiency via GCS compose/rotation. Each becomes its own
      `plans/active/<slug>_2026_08_22.md` doc (default `assigned_vm: NA` per the standard ask-before-creating rule
      unless the operator says otherwise), citing
      `plans/active/deployment_registry_firestore_migration_2026_07_14.md:187-190` as source. From Filed item 7.
      Done-when: 3 new plan docs exist, each cross-linked from the parent doc's "Out of scope" section.
- [ ] [DATA] P2. **D114 ruling applied (2026-08-21, issues_corpus_completion_dispatch_2026_08_21.md ledger): check the
      GO/NO-GO precondition, set the duration if near, else it can wait.** Re-check
      `plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md`'s 4-item GO/NO-GO data-precondition
      checklist's current status; if it is now met or genuinely near, set "the agreed window" soak duration explicitly
      in that doc's `[REVIEW] P1` "Soak" todo (line ~111) with a stated rationale (e.g. a specific 24h/48h/72h value);
      if it remains far from met, leave the duration unset and note the re-check trigger/date instead. From Filed item
      8. Done-when: either a concrete duration is written into that doc, or a dated note explains why it's still
      premature and names what would need to change.
- [x] [DOC] P3. **DONE 2026-08-16 (plan_reconciler Phase -1).** `cursor-configs/skills/plan-reconcile/SKILL.md:648`
      described this skill's dispatch default as "the worker (opus / effort max / thinking on)" — contradicted
      CLAUDE.md's 2026-08-07/08-08 ruling (opus-required = ZERO categories, manual-only) and
      `agents/plan_reconciler.md`'s own current frontmatter/prose (sonnet-5). This todo was ADDED 2026-08-16
      (plan_reconciler agt-8fc5a6, zero-checkbox conversion of this doc's own Doc-drift #4 finding) with a note that
      it was "outside `plans/**`, not this skill's write-scope" — re-assessed this run: `cursor-configs/skills/` is
      regular PM-repo content, not `codex/**`/`CLAUDE.md` (the only gated paths per Trust Mode's one carve-out), so a
      general reconciliation session CAN and should fix it directly rather than waiting on a dedicated human/operator
      session. Corrected to "sonnet-5, effort max, extended thinking" — `unified-trading-pm` (this session).
- [x] [DOC] P3. **DONE 2026-08-15 (plan_reconciler reconciliation session).** Add the missing cross-file conflict-check
      to `plans/active/ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md` todo 1 — it reconciles
      `artifact_pipeline_observability_2026_07_17.md`'s checkboxes against batch 3's work but its conflict-check didn't
      name `plans/active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md` todo 4 (line ~280, still open), which
      touches the SAME source doc's checkboxes for batch 1's work. Both finalize plans are `status: active` and
      `assigned_vm: planning` today — a real same-file dispatch collision risk if both are ever worked concurrently.
      Added a "Same-file dispatch-collision note" to batch3_finalize's todo 1, explicitly naming `batch1_finalize`
      todo 4. From Filed item 9.

## Archive candidates (operator review)

1. `plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` — 3/3 todos
   HARD-verified done, was `locked: true` (`live-defi-rollout`, almost certainly the corpus-wide placeholder bug, filed
   above). **RESOLVED 2026-08-10**: `archived: true` — operator asked directly, approved a targeted `[unlock-plan]` for
   this doc (ahead of the corpus-wide placeholder ruling), unlocked + archived via the 6-step ritual.

## Refuted (dropped by verify)

1. Line-683 `artifact_pipeline_observability` prose-open-item — already fixed same-day before this run (see
   Contradictions #4).
2. "No batch 3 drafted" vs. batch3 existing — non-contradictory, different mechanisms same day (see Contradictions #5).
3. `data_status_tab_and_downloads_remediation_2026_06_16.md`'s "Not yet identified" deferred-work hedge — corroborated
   as a genuine, self-consistent absence (corpus-grepped, no owner found); doc is grace-protected regardless.
4. `consolidator_throughput_backlog_monitor` WS-3 seam-endpoint hedge (referenced from
   `ui_satellite_ao_dispatch_batch1_2026_08_06.md`) — already resolved elsewhere (checkbox flipped 2026-08-07,
   na-eligibility-audit), hedge is stale prose only, no live defect.
5. `deployment_api_sigabrt_crash_loop_2026_07_24.md:372` "NOT YET IDENTIFIED" hedge — self-resolved within the same doc
   (the very next todo is the confirmed-done follow-up).
6. Doc6 (`issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md`) `[HUMAN]` tag non-standard vs.
   task_template.md's `[TAG]` vocabulary — `assigned_vm: NA`, not AO-ingested regardless; not worth an edit.
7. Progress-Log chronological-order defects (2 docs) — cosmetic (P2-P3), reordering existing dated entries carries more
   risk (could read as altering someone's record) than the defect's severity warrants; left as-is.
8. `deployment_registry_firestore_migration_2026_07_14.md` Model/effort column citing historical "Opus" for
   already-archived P1/P2 phases — accurate historical record of what actually ran, not a stale current-policy claim;
   not touched.

## Plans not reached

None — all 23 tranche docs were read (21 in full by a hunter or myself, 2 grace-protected read as context only).

## Exit hygiene-gate status

Re-ran `run_hygiene_sweep.sh --ci` after all fixes landed: **1 hard failure** (`assigned_vm:NA corpus size (ratchet)` —
51 new NA-population docs / 115 new open todos vs. `origin/main`), **1 soft warning** (delete/VM-launch tagging,
pre-existing candidate signal, no ui-tranche hits). The NA-corpus ratchet was **already red at this run's own STEP 1
baseline** (46/112, before any edit) — confirmed pre-existing, not a regression introduced here, and its shrink is
`/na-eligibility-audit`'s standing job, not this skill's (SKILL.md's own precedent from the 2026-08-07 run treats this
exact class of corpus-wide ratchet failure the same way). Honest accounting: this run's own 2 new NA docs (this findings
doc + the locked_by issue doc, both correctly `assigned_vm: NA` — a coordination record and an operator-decision-gated
issue, neither AO-dispatchable work) are a small part of the +5-doc growth since STEP 1; the remainder is concurrent
corpus activity from other sessions on the shared branch (confirmed: a sibling plan_reconciler dispatch `agt-33a6ec` was
actively working the cross-cutting tranche during this run, per its own Progress Log entry found in
`issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md`). proseWrap-padding and reference-path-convention — both
hard-red at STEP 1 — are GREEN now (my fixes + the sibling cross-cutting run's own fixes both landed against the same
shared ratchet). Every doc this run touched is individually `run_hygiene_sweep.sh`-clean (verified via `--only` on each
staged batch before commit).

## Progress Log

- **2026-08-10 (operator-approved archival)**: the `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`
  archive candidate (item 10 in Filed, item 1 in Archive candidates) was unlocked + archived — operator asked directly
  and approved a targeted `[unlock-plan]` for this one doc, ahead of the corpus-wide `locked_by` placeholder ruling in
  `locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` (todos 1-2 there remain open for the other 95
  docs). Doc now lives at
  `/plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`.
- **2026-08-10 (prose-findings formalization sweep)**: converted 3 prose findings into 3 formal todos (1 already
  resolved, cited inline — Filed item 6, `ui_consolidated_closeout` Todo 6 confirmed `[x]`); Filed items 7-9 (orphaned
  Firestore-migration successor scoping, undefined soak-window duration, batch1/batch3-finalize same-file conflict-check
  gap) formalized into `## Todos` above with fresh re-verification of each.
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up)**: KEEP-NA, valid — 2 of the 3 open todos are explicitly
  `[OPERATOR]`-tagged genuine human judgment/definition calls, not worker-determinable: todo 1 needs a human decision on
  whether/when each of 3 named orphaned successor items becomes its own plan; todo 2 needs a human to supply a
  soak-window duration nowhere stated in the source doc (and that doc's own phase is separately HALTED on an earlier
  precondition regardless). Todo 3 (the batch1/batch3-finalize same-file conflict-check note) is individually small and
  plausibly bounded, but the whole-doc RECLASSIFY bar requires every open todo to clear, and todos 1-2 do not.
- **2026-08-10** — plan_reconciler dispatch `agt-ec1688` started. Confirmed 23-doc `ui` tranche membership via
  multi-line-aware frontmatter scan (the plain single-line grep undercounts — `asset_group:` often wraps its `[ui]`
  value to the next line). Grace set: 2 docs (`data_status_tab_and_downloads_remediation_2026_06_16.md`, 5h;
  `ui_satellite_ao_dispatch_batch3_2026_08_09.md`, 6h) — read-only this run. Re-verified all 6 items filed by the
  2026-08-07 run: (1) the 4 missed-flip candidates in `data_status_tab_and_downloads_remediation` remain open AND still
  locked AND now additionally grace-protected — cannot act; (2) the
  `deployment_ui_smoke_failures_daily_costs_nav_mobile` archive candidate remains locked
  (`locked_by: live-defi-rollout`, `locked_since: 2026-05-21`, still predates its own `created: 2026-07-21`) — now 5
  consecutive audit passes (2026-08-06/07/08/09 + this one) with zero resolution; (3)
  `deployment_registry_firestore_p5_verify` stale-draft gate unchanged, still behind P3 cutover; (4) the
  `ui_consolidated_closeout` Track 3/4 stale prose remains correctly tracked (not re-filed) — `batch1_finalize` todo 4
  (archival) is "now dispatchable" per its own Progress Log but has not yet run; (5) `plans/active/ACTIVE_INDEX.md`
  confirmed still nonexistent — it is a stale reference inside `plan-reconcile/SKILL.md` / `agents/plan_reconciler.md`
  themselves (both outside `plans/**`, out of my write-scope — flagged, not fixed); (6) hygiene sweep hard-failure set
  has CHANGED since 2026-08-07 (was: reference-path/AG-closeout-linkage/terminal-status-archived/archive-candidates;
  now: proseWrap/reference-path/NA-corpus-size) — corpus-wide, not ui-specific, no action here. **New finding this
  run**: `locked_by: live-defi-rollout` is traced to a hardcoded placeholder in
  `scripts/plans/fix_epic_frontmatter_2026_05_21.py:133` (`lines.append("locked_by: live-defi-rollout")`) — not a real
  actor/agent/operator identity (no one is named after the branch). Corpus-wide grep: 96 docs in `plans/active`+`issues`
  alone carry this exact value, versus legitimate agent locks which carry a real dispatch id + timestamp (e.g.
  `plan_reconciler (agt-xxxxxx) since <ts>`). The `deployment_ui_smoke_failures` doc's `locked_since: 2026-05-21`
  matches this script's own date exactly. Filed as a dedicated cross-cutting issue (see Filed section) since fixing it
  corpus-wide is out of this ui-scoped run's mandate, but it directly blocks a ui-tranche archival decision. Fan-out
  hunters dispatched next for fresh contradiction/hygiene/AO-readiness/ codex-alignment coverage.
- **context-scout 2026-08-14**: populated context_scope (5 entries).
- **2026-08-15 (operator-ruling application session)**: applied 2 operator rulings received on this doc's routed
  questions, plus the resolved doc-drift item and the auto-fixable cross-reference todo. **Contradiction #3**
  (GCS-delete autonomy): operator ruled fully-autonomous is correct; replaced `..._p3_cutover_2026_07_14.md`'s "OPERATOR
  CONFIRMS" banner with a corrected framing (data-precondition HALT preserved unchanged, only the authority framing
  fixed) — documentation-only, no GCS object touched. **Doc-drift #1** (epic stale table rows): operator confirmed the
  epic's `locked_by: live-defi-rollout` is the corpus-wide placeholder bug, not a real lock, safe to edit; removed both
  stale rows with an explanatory footnote. **Doc-drift #3** (ui-testing-layers.md + 2 siblings): operator approved
  correcting to verified-current paths; re-verified every claim independently via `ls`/`find` before applying (did not
  trust the findings doc's claims blindly) — `tests/playbooks/**` → `tests/e2e/playbooks/**` corpus-wide (5 sites across
  the 3 docs), `lib/registry/route-manifest.ts`/`tests/smoke/routes.spec.ts` absence in `unified-trading-system-ui`
  annotated as aspirational/illustrative rather than invented-path-substituted. **Doc-drift #2**
  (data-status-ui-surface.md behavioral drift): confirmed already fixed by `unified-trading-pm@bfd94b8d0c` (2026-08-12)
  — 14-day fallback-lookback
  - `requested_date`/`resolved_date` prose both present on a fresh read; flipped to resolved. **Todos item 3**
    (batch1/batch3-finalize same-file collision note): added the cross-reference note to batch3_finalize todo 1; flipped
    done. **Todos items 1-2** (orphaned successors scoping / soak-window duration): left open per the operator's
    minor-items ruling — annotated item 1 with a "NEEDS SCOPING" flag (no plan drafted, out of this session's mandate)
    and item 2 with a fresh re-confirmation that it's still moot (Phase 3's GO/NO-GO checklist still unmet). No git
    add/commit/push performed by this session — edits only, per this session's own instructions (someone else commits
    centrally afterward).

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-17 (ui tranche)** [body-hash:1babc61ff534fae3]: KEEP-NA, valid — both remaining open
  items are `[OPERATOR]`-tagged genuine human calls (scoping 3 orphaned successor items; defining an undefined
  soak-duration value), neither worker-determinable. Consistent with this doc's own 2026-08-10 self-audit note.

- **2026-08-21 — ruling D114 (Firestore-migration successors)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Author the 3 plans (bounded, prevents drift); set the duration if the GO/NO-GO
  precondition is near, else it can wait. Applied by retagging both open todos above from `[OPERATOR]`-gated to plain
  dispatchable todos (author 3 successor plan docs; check-then-set the soak duration). Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
