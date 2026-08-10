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
    /plans/active/issues/plan_reconciler_findings_2026_08_07.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /plans/active/ui_satellite_ao_dispatch_batch3_2026_08_09.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
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
3. **[ROUTED — see Filed]** `deployment_registry_firestore_migration_2026_07_14.md` ("Fully autonomous — no operator
   gates" for the P3 GCS delete) vs. `deployment_registry_firestore_p3_cutover_2026_07_14.md` ("🔴 BLOCKED... GCS DELETE
   HELD UNTIL OPERATOR CONFIRMS", "operator-supervised"). Authority question on an irreversible delete — evidence cannot
   settle which framing governs. Asked via `/blocked`.
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

1. **[ROUTED]** `plans/epics/deployment_and_user_management_master.md` — 2 stale UI-Verification-Contract table rows:
   (a) `tests/playbooks/auth_flow.spec.ts` for the user-management-ui surface that was dropped 2026-07-12 per this SAME
   doc's own "Owns" section (live-verified: file doesn't exist); (b) `tests/widgets/deployment-lifecycle.test.tsx` — no
   `tests/widgets/` directory exists in deployment-ui at all, and the codex SSOT (`ui-testing-layers.md`) itself
   documents deployment-ui as not having an L1.5 widget-harness layer — ambiguous whether this row should be deleted
   (never-applicable) or tracked as a real gap. **Not fixed**: this epic carries `locked_by: live-defi-rollout` (the
   same placeholder pattern filed corpus-wide below) — stayed consistent with my own not-yet-ruled treatment of that
   value and left the doc untouched.
2. **[ROUTED]** `/codex/03-deployment/data-status-ui-surface.md` — behavioral drift beyond the mechanical path fix
   applied below: (a) the 404-on-missing-date contract doesn't mention the 14-day fallback-lookback behavior shipped
   2026-07-15; (b) the "Top-level keys" table omits 2 additive response fields shipped 2026-07-17
   (`requested_date`/`resolved_date`). Both need newly-composed documentation prose, not a pure substitution — outside
   the mechanical codex-staleness carve-out (STEP 5.f2 requires a single unambiguous substitution, no invented content).
   Asked via `/blocked`.
3. **[ROUTED]** `/codex/06-coding-standards/ui-testing-layers.md` + 2 sibling codex docs
   (`/codex/14-customer-journeys/testing/README.md`, `test-matrix.md`) — corpus-wide stale UI test-path convention:
   `tests/playbooks/**` should be `tests/e2e/playbooks/**` (per hunter's git-log check, this was wrong from inception,
   not a later drift); `lib/registry/route-manifest.ts` doesn't exist in `unified-trading-system-ui`;
   `tests/smoke/routes.spec.ts` naming doesn't match that repo's real `*.smoke.spec.ts` convention (it DOES exist
   correctly in deployment-ui — the drift is specific to the doc's Next.js worked example). Load-bearing: this is the
   literal source of the `regression: tests/playbooks/...` evidence-tag convention `plans/PLAN_FORMAT.md` § 9 requires
   on every UI plan tick. Big blast radius (3 codex docs, none fully read by me this run) — did not attempt a multi-doc
   surgical fix without independent verification of each. Asked via `/blocked`.
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
5. **[FIXED]** `plans/active/issues/plan_reconciler_findings_2026_08_07.md` — converted a 2×-flagged, never-tracked
   prose-only finding (missing `ACTIVE_INDEX.md` normative ref) into a real `[DOC] P3` todo per the "every follow-up is
   a todo, never prose" rule. Commit `69a5ac46e2`.

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
   (small enough to resolve inline once ruled — will apply directly to both docs on answer).
3. Doc-drift #2 above (data-status-ui-surface.md behavioral drift, needs new prose) — asked via `/blocked`.
4. Doc-drift #3 above (ui-testing-layers.md corpus-wide stale test-path convention) — asked via `/blocked`.
5. Doc-drift #1 above (epic's 2 stale verification-contract rows, entangled with the locked_by lock) — folded into the
   locked_by question's context, not a separate ask (resolves once that lock question is ruled).
6. `plans/active/ui_consolidated_closeout_2026_07_30.md` Todo 6 ("First `/ag-closeout-audit ui` + `/plan-reconcile ui`
   runs...") — will flip at STEP 7 flush citing this run's own dispatch (both skills have now run on this tranche at
   least once; `/ag-closeout-audit ui` ×4, `/plan-reconcile ui` ×2 counting 2026-08-07).
7. `plans/active/deployment_registry_firestore_migration_2026_07_14_finalize_2026_07_30.md`'s Out-of-scope successors (3
   real follow-up items in `deployment_registry_firestore_migration_2026_07_14.md`, prose-only, no tracking doc cited:
   real-time UI listeners, lifecycle-events archival, run.log overwrite efficiency) — NOT converted to todos here
   (explicitly "out of scope" for that plan, and inventing new tracked plans for genuinely new future work is bigger
   than this run's reconciliation mandate). Noted for a human session to decide where these belong.
8. `deployment_registry_firestore_p3_cutover_2026_07_14.md` todo "the agreed window" (soak duration) — no duration
   stated anywhere in the doc; missing definition-of-done, needs domain knowledge this run doesn't have. Noted, not
   resolved.
9. `ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md` todo 1's conflict-check — named only the 2 batch plans, not
   `batch1_finalize`'s own still-open todo 4, which touches the same file
   (`artifact_pipeline_observability_2026_07_17.md`'s checkboxes). Potential future same-file dispatch collision if both
   ever run concurrently. Noted for whoever dispatches either.
10. `plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` archive candidate — all 3
    todos independently re-verified done (2 hunters cross-checked via the deployment-ui git history this run, confirming
    no regression through later renames). Blocked solely by the `locked_by` bug (item 1 above). Will archive immediately
    once that's ruled.

## Archive candidates (operator review)

1. `plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` — 3/3 todos HARD-verified
   done, `locked: true` (`live-defi-rollout`, almost certainly the corpus-wide placeholder bug, not filed above).
   `archived: false` — blocked pending the locked_by ruling.

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
