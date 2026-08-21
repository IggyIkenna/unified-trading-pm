---
doc_type: issue
title: "plan_reconciler findings — ui tranche, 2026-08-18 (dispatch agt-2a424e)"
summary: >-
  Third sharded plan_reconciler run over the `ui` asset_group tranche (23 docs: 11 plans + 12 issues, incl. 3 batch
  docs + 3 finalize docs — batch4/batch4_finalize new since the 2026-08-10 run). Re-checked every item filed by the
  2026-08-10 run (agt-ec1688), fan-out hunters for fresh coverage of what changed since (new batch4, the
  deployment_api_unauthenticated_prod_p0 P0 security doc, the unclassified architecture_v2_drift doc).
status: open
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, ui, 2026-08-18]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md,
    /plans/active/ui_satellite_ao_dispatch_batch4_2026_08_17.md,
    /plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
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
source: "plan_reconciler dispatch agt-2a424e — sharded ui tranche run 2026-08-18"
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/deployment-observability.md,
    /codex/03-deployment/data-status-ui-surface.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md,
  ]
---

# plan_reconciler findings — ui tranche, 2026-08-18

> **Run**: dispatch `agt-2a424e`, sharded to `tranche=ui`. 23 docs in scope (11 plans + 12 issues, incl. 3
> satellite-dispatch batches + 3 finalize docs). This is the THIRD `/plan-reconcile ui` run — the second
> (`agt-ec1688`, 2026-08-10) applied ~20 fixes across 10 files and is linked above.

## Coverage (hunters / batches / docs)

- **Hunters**: 5, all `model=sonnet`, read-only, `SUB_AGENT_MANDATORY_RULES.md` pasted at spawn — data/registry
  cluster (10 docs), observability/admin cluster + 1 unclassified doc (5 docs), AO-dispatch batches + closeout hub (7
  docs), codex-alignment (3 codex SSOTs × 23 docs, targeted grep-then-read), missed-flip + hygiene + prior-findings
  carryover (23 docs, targeted).
- **Docs read in full**: all 23 ui-tranche docs (14 non-grace read directly by a hunter or the orchestrator; 9 grace
  docs read as context only, no edit proposed) + 3 codex SSOTs + the archived `deployment_registry_firestore_p0_unblock_2026_07_14.md`
  (existence + frontmatter-verified) + `deployment-ui/src/components/HonestCoverageCard.tsx` (live source, read by
  the orchestrator during STEP 4 to resolve 2 codex-drift candidates definitively).
- **Candidates surfaced**: ~20 across contradictions, doc-drift, hygiene, codex-drift, and missed-flip. Every
  candidate was independently re-verified by the orchestrator (fresh `grep`/`git log`/live-source reads, not
  hunter-trusted) before any apply — see below.

## Flips verified

None with STEP-4 HARD evidence this run. The 2 candidates Hunter 5 surfaced (`ui_consolidated_closeout` P2 todo re:
re-running `/ag-closeout-audit ui`; `architecture_v2_drift`'s `[ENGINEER] P1` todo) were both already self-negated by
the hunter's own read — see Refuted.

## Contradictions

1. **[FIXED]** `plans/active/deployment_registry_firestore_migration_2026_07_14.md` — the phase-index table's **P0**
   row read `**active** — reallocated back to AO 2026-07-24 ... success criteria ... not yet fully verified` with a
   dangling link (`deployment_registry_firestore_p0_unblock_2026_07_14.md`, missing the `../archive/2026_07/` prefix
   every sibling P1/P2/P4 row already carries). Verified: the archived doc's own frontmatter reads `status: complete`.
   The 2026-07-21 "REFRESHED" banner fixed P1/P2/P4's rows but predated P0's 2026-07-29 archival, so P0's cell was
   never revisited — 3+ weeks stale. Corrected the link + status to `**complete (archived)**`, matching the sibling
   rows' style. Commit: this session.
2. **[CLARIFIED, not force-resolved]** `plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md` —
   its gate sentence ("Do not start until all 5 of its todos are `[x]`") is now ambiguous: the referenced P0 doc has
   grown a second `## Follow-ups (post-flip durable close-out)` section (5 open items) since 2026-08-10, and the
   finalize doc itself has sat with **zero dispatch activity for 8+ days** despite its original 5-todo gate having
   been satisfied since 2026-08-10/11. Did NOT decide whether the Follow-ups should also gate this finalize (a real
   scope judgment call, not mine to make) — instead added a factual note clarifying the P0 doc's current 2-section
   shape and flagging the ambiguity for whoever picks up todo 3 (archive the source issue doc). The 8-day dispatch
   inactivity itself is noted in Filed below as worth an AO-backlog-status check, not something this run can fix via
   doc edit. Commit: this session.

## Doc-drift

Confirmed by hunters + independently re-verified by the orchestrator, but **routed, not fixed** — every item below
lives on a currently GRACE-PROTECTED doc (newest commit <12h old at run start), so the safe resolution is already
known but cannot be applied until the grace window clears (next run):

1. `plans/active/ui_consolidated_closeout_2026_07_30.md` Track 3 Sources (line ~122) still frames the `/artifacts`
   page as "mock-first done, real API+UI wiring **in progress**" — the source plan's own banner
   (`artifact_pipeline_observability_2026_07_17.md:396`) shows all 5 vertical slices landed `deployment-ui@3210bb5`
   (2026-07-23), before the hub doc even existed (2026-07-30). Stale since authoring, uncorrected 19+ days.
2. Same hub doc, Track 3's close-out criterion ("the alerts N+1 read pattern fixed at the root, not just the two
   stopgaps") contradicts its own Sources paragraph 7 lines above, which documents the root fix as deliberately
   WONT-DO'd 2026-08-01. **Already flagged in this doc's own Progress Log 2026-08-06** (`ag_closeout_auditor`) and
   still unfixed 12 days later — a second confirmation this needs the actual edit, not another flag.
3. `plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` is a genuine, correctly
   `[ui]`-tagged live orphan (1 open `[ENGINEER] P1` todo, UI-repo-only per its own 2026-08-16 retag note — see
   Hygiene fix below) but is cited by **zero** Track 1-4 Sources lists in the closeout hub and is absent from the
   2026-08-10 predecessor findings doc. Needs adding to the hub's Track 3 or a new line once the hub is writable.
4. `plans/active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md` todo 4's premise (draft a migration-batch
   plan for `data_status_tab_and_downloads_remediation_2026_06_16.md`'s cleared items) is now stale — all 6 named
   items are already shipped `[x]` directly in the source doc (dated 2026-08-14 through 08-16, via pw:L2 + a
   `/plan-reconcile` pass), not via a new satellite-batch extraction as the todo anticipates. Needs annotation or a
   scope-narrowing edit once writable.

## Hygiene fixes

1. **[FIXED, 3 of 4 docs]** Context-scout script bug — the 2026-08-17-dated Progress Log entry in at least 4 docs
   was appended without its leading `- ` bullet marker (`"**context-scout 2026-08-17**: ..."` instead of
   `"- **context-scout 2026-08-17**: ..."`), a pattern consistent across independent files on the same date
   (strongly suggests a script-level append bug, not manual typos). Fixed the 3 non-grace instances:
   `data_status_catalogue_true_source_phase2_2026_07_24.md`, `data_status_tab_and_downloads_remediation_2026_06_16.md`,
   `deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md`. The 4th instance
   (`deployment_api_unauthenticated_prod_p0_2026_08_10.md:686`) is GRACE-PROTECTED — deferred to next run. Root cause
   (likely the context-scout skill/script itself) is outside `plans/**` — filed below, not chased this run.
2. **[FIXED, 7 docs]** Stale `last_updated` frontmatter — bumped to 2026-08-18 with a `# (was: ...)` provenance
   comment (matching the established 2026-08-15 precedent) on 7 docs where `git log` showed real content activity
   after the stamped date: `deployment_registry_firestore_migration_2026_07_14.md` (stale 32 days),
   `deployment_registry_firestore_p3_cutover_2026_07_14.md` (34 days), `deployment_registry_firestore_p5_verify_2026_07_14.md`
   (27 days), `consolidator_throughput_backlog_monitor_2026_07_09.md` (10 days — also fixed a confused
   self-referential comment that claimed a 2026-08-15 bump which the stored value didn't reflect),
   `data_status_cell_grid_rearchitecture_2026_07_18.md` (9 days), `data_status_catalogue_true_source_phase2_2026_07_24.md`
   (2 days), `plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md` (7 days).
3. **[FIXED]** `plans/active/ui_satellite_ao_dispatch_batch4_finalize_2026_08_17.md` lacked a same-file
   dispatch-collision note for `data_status_tab_and_downloads_remediation_2026_06_16.md`, unlike its sibling
   `batch3_finalize` which carries an explicit one for the same class of risk. Added, noting the risk is currently
   moot (see Doc-drift item 4 above — `batch1_finalize` todo 4's target items already shipped independently) but
   should still be flagged for future concurrent dispatch.
4. **[FIXED]** `plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` frontmatter —
   `repos: [unified-api-contracts, unified-trading-system-ui, strategy-service]` → `[unified-trading-system-ui]` and
   `parent_epic: defi_master` → `deployment_and_user_management_master`. The doc's own 2026-08-16 retag Progress Log
   entry already states in prose that the UAC-source portion is fully resolved and the sole remaining todo is
   "exclusively the UI-side resync ... all `unified-trading-system-ui` content, not defi-domain" — this just aligns
   the frontmatter (which drives dispatch routing) with what the doc's own body already documents, matching the
   convention every other ui-tranche doc uses for `parent_epic`.

## Codex corrections applied (mechanical, evidence-cited)

Narrow carve-out (plan_reconciler STEP 5.f2): HARD evidence (live grep-then-READ of running code), single
unambiguous substitution, no HARD-STOP governance area, no new measurement run.

1. `/codex/03-deployment/data-status-ui-surface.md` — the "Styling conventions" table (4 rows, `bg-yellow-400`/
   `bg-gray-300`) was stale against the shipped `SEGMENT_COLORS` fix
   (`data_status_tab_and_downloads_remediation_2026_06_16.md:225-227`, `deployment-ui@7007529`) — codex's own
   `last_reviewed: 2026-08-12` postdates that fix, so it was never reconciled. Read
   `deployment-ui/src/components/HonestCoverageCard.tsx` directly (live source, not hunter-trusted): current
   `SEGMENT_COLORS` const has 6 bg-only entries (`captured`/`empty_confirmed`/`known_empty`/`attempted_failed`/
   `pending_fetch`/`out_of_window`), no paired `text-*` class per segment (the `text-*` colors elsewhere in that
   component style an unrelated numeric-threshold indicator). Replaced the stale 4-row bg+text table with the
   verified-current 6-row bg-only table, and fixed the same stale color list repeated in the "UI component" section's
   quick-mention 19 lines above it.
2. Same doc, "Operational notes" — `"Card silently hides itself when the API returns 404"` directly contradicted the
   SAME doc's own "UI component" section 25 lines above (`"renders a muted 'not yet measured' note"`) — an
   intra-codex self-contradiction, likely a partial edit that updated one section without the other. Live-verified
   which side is correct: `HonestCoverageCard.tsx:217` (`notYetComputed = !loading && data === null && error ===
   null`) and `:257` (`"Coverage data not yet computed for {date}."`) confirm the muted-note behavior; there is no
   early-return/hide path. Corrected the wrong side to match the right side + live code.

## Filed

1. Context-scout script's missing-bullet-marker bug (Hygiene fix 1) — root cause is the context-scout skill/script
   itself, outside `plans/**`, not fixable by this role. Worth a dedicated look next time someone touches that
   script; the 4-doc same-date pattern is fairly strong evidence.
2. `deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md` has sat with zero dispatch activity for 8+ days
   despite `depends_on`+`gate_on_depends: true` on a plan whose original 5-todo gate has been `[x]` since
   2026-08-10/11 (Contradiction 2 above). Worth an AO-backlog-status check (`/check-agent-orchestrator`) to confirm
   whether this is a genuine dispatch gap or correctly still-blocked on the newer Follow-ups section — not resolved
   here, this run only clarified the doc text.
3. The 4 grace-protected Doc-drift items above — already diagnosed with a known-correct resolution, just needs the
   grace window (12h from each doc's own last touch) to clear before the next `/plan-reconcile ui` run can apply
   them directly from this findings doc.
4. `plans/active/issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` — confirmed still accurate
   (Hunter 1 Q3), not superseded. Worth noting for future readers: the new `deployment-api-verify-auth-contract`
   Cloud Scheduler job added by the P0 security doc is a DIFFERENT mechanism (auth-contract 401/200 polling) from
   what this issue is about (health-transition alerting having no dedicated schedule) — don't mistake one for
   resolving the other. Not edited into the doc this run (would need a fresh Read first; deferred as low-priority).

## Archive candidates (operator review)

None this run — no fully-done + unlocked ui-tranche doc surfaced by any hunter.

## Refuted (dropped by verify)

1. Hunter 5's candidate A1 (`ui_consolidated_closeout_2026_07_30.md` P2 todo re: re-running `/ag-closeout-audit ui`,
   citing `unified-trading-pm@b2e3e5f8fe`) — self-negated on read: the cited sha proves a *prerequisite tooling fix*
   shipped, not that the todo (re-running the audit) itself is done; the same doc block says so explicitly. Also
   GRACE-PROTECTED regardless.
2. Hunter 5's candidate A2 (`architecture_v2_drift`'s `[ENGINEER] P1` todo, citing commits `80bb6a9c`/`88422902`) —
   self-negated: those commits close only 1 of the todo's 2 still-open sub-parts (already struck same-day per the
   todo's own text); the todo correctly stays open for the remaining scope.
3. Predecessor's (2026-08-10) "4 missed-flip candidates, still locked" characterization of
   `data_status_tab_and_downloads_remediation_2026_06_16.md` — now stale-as-history, not a live contradiction: the
   doc is unlocked today (`locked_by`/`locked_since` both blank), and only 2 genuinely-gated open todos remain
   (neither a missed-flip — both correctly cite an unmet precondition, not completion evidence). At least 3 items
   were flipped with hard evidence by the 2026-08-15 `/plan-reconcile` pass in the interim.
4. `consolidator_throughput_backlog_monitor_2026_07_09.md`'s WS-3 seam-endpoint hedge — reconfirmed already
   resolved (checkbox `[x]` with a `STALE — already done piecemeal, closing 2026-08-07` annotation), matching the
   2026-08-10 predecessor's own Refuted item 4. 3 other hedge-phrase hits in this doc are all inside dated,
   historical Progress Log entries correctly superseded by later same-day entries — no live mismatch.
5. Non-canonical todo-format hit from the corpus-wide hygiene sweep (`check_todo_format`) — confirmed OUTSIDE the ui
   tranche (`plans/active/issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md:158`, a prediction/ML doc).
   Scoped re-run of `check_todo_format.sh` against exactly the 23 ui-tranche docs returns 0 hits.
6. Delete/VM-launch todo-tagging soft warning — 0 hits among the 9 `assigned_vm: planning` ui-tranche docs (verified
   via `check_delete_vm_launch_gating.sh` + a manual cross-check of the script's own RISK_PAT terms — the 3 raw
   pattern hits found are all non-actionable prose, none inside an open-todo instruction).
7. `plan_reconciler_findings_ui_2026_08_10.md`'s 2 open `## Todos` (scope 3 orphaned Firestore-migration successors;
   define the undefined "agreed window" soak duration) — both re-confirmed still accurately open, zero drift: no new
   plan covers any of the 3 successor items (targeted corpus grep, false positives excluded), and the soak duration
   is still undefined with the phase still HALTED on its unrelated GO/NO-GO precondition. This findings doc's
   carryover claims are current as of 2026-08-18.

## Plans not reached

None — all 23 tranche docs were read (by a hunter, the orchestrator, or both), 14 non-grace in full with edits
where warranted, 9 grace-protected as context only.

## Progress Log

- **2026-08-18** — plan_reconciler dispatch `agt-2a424e` started. Repos synced (all clean except pre-existing
  `unified-trading-ci` AHEAD=3, out of scope — not a ui-tranche repo). Confirmed 23-doc `ui` tranche membership via
  `generate_tranche_doc_inventory.py` (never a same-line grep, per this skill's own confirmed-miss precedent). Grace
  set: 9 docs (`artifact_pipeline_observability_2026_07_17.md` 10h, `cost_observability_deferred_followups_2026_07_10.md`
  11h, `deployment_api_unauthenticated_prod_p0_2026_08_10.md` 8h, `ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`
  11h, `ui_consolidated_closeout_2026_07_30.md` 10h, `ui_satellite_ao_dispatch_batch1_2026_08_06.md` 10h,
  `ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md` 10h, `ui_satellite_ao_dispatch_batch3_2026_08_09.md` 10h,
  `ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md` 10h) — read-only this run. Read the 2026-08-10 predecessor
  findings doc + the `ui_consolidated_closeout` hub in full before dispatching hunters. Hygiene sweep (corpus-wide):
  1 pre-existing hard failure (`assigned_vm:NA` corpus-size ratchet — `/na-eligibility-audit`'s remit, not ui-specific,
  not touched here), 1 soft warning (delete/VM-launch tagging, no ui-tranche hits). `build_health_digest.sh` produced
  no output file despite exit 0 — noted as a minor tooling gap, not chased (outside `plans/**` write-scope; skeleton +
  full hygiene-sweep text were sufficient inputs). Fan-out hunters dispatched next.
- **na-eligibility-audit 2026-08-18 (ui tranche, dispatch agt-a78a10)** [body-hash:a40baea9962dda25]: KEEP-NA, valid —
  this doc is itself the live in-progress findings report for the sibling `/plan-reconcile ui` dispatch `agt-2a424e`
  above (same day, still mid-run per its own Progress Log: hunters dispatched, no Coverage/Flips/Contradictions/etc.
  populated yet). 0 open checkboxes to classify — a process/tracking artifact, correctly `assigned_vm: NA` /
  `execution_scope: local-only`, not AO-dispatchable content. Confirmed via `git fetch` immediately before this edit
  that no further plan_reconciler commits had landed on this file (last commit `f3689fe1` at 02:39 UTC, 17+ min prior)
  — appended only, nothing existing touched.
- **2026-08-18 (STEP 3-5, same session)**: 5 hunters returned (~3.5-11 min each, ~172-264k tokens each). Consolidated
  ~20 candidates, dropped 2 self-negated + several already-clean per hunter's own investigation, independently
  re-verified the rest (fresh `grep`/`git log`/live-source reads — including reading
  `deployment-ui/src/components/HonestCoverageCard.tsx` directly to definitively resolve 2 codex-drift candidates
  that needed live source, not just PM-corpus content). Applied 19 edits across 12 files: 1 confirmed contradiction
  fixed (Firestore P0 phase-table row — dangling link + stale status, verified against the archived doc's own
  frontmatter), 1 gate-ambiguity clarified without deciding new scope, 7 stale `last_updated` frontmatter bumps, a
  4-doc context-scout bullet-marker bug fixed in the 3 non-grace instances, a missing same-file collision note added,
  a frontmatter retag-cleanup on `architecture_v2_drift`, and 2 mechanical codex corrections (color-palette table +
  an intra-doc 404-behavior self-contradiction) under the STEP 5.f2 carve-out. 4 confirmed doc-drift items routed
  (all on grace-protected docs — resolution already known, deferred to next run). Ran
  `check_frontmatter_yaml.py`/`check_frontmatter_schema.py`/`check_reference_paths.py`/`fix_todo_format.sh --check`
  against every touched file before committing: all clean, 0 new violations, reference-path dangling-ref baseline
  unchanged at 34 (my new archive-path link resolves correctly, not counted). No genuinely-undecidable judgment call
  surfaced this run — nothing routed via `/blocked`, so STEP 8 has zero open questions. (Merge note: this entry and
  the na-eligibility-audit entry above landed as a genuine same-file concurrent-edit collision during push —
  git's autostash-reapply raised a textual conflict since both are independent Progress Log appends anchored at the
  same point; resolved by keeping both, na-eligibility-audit's first since it read the doc before this entry existed.)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21 (ui tranche)**: KEEP-NA, valid — reconfirmed. This is a completed
  plan_reconciler run report (dispatch `agt-2a424e`, 19 edits applied), not a checkbox-tracked work doc — 0 open
  `- [ ] [TAG] P<n>.` items, only "Filed" prose notes for follow-up. Per the successor doc's own Phase -1
  reconciliation (`plan_reconciler_findings_ui_2026_08_19.md`, same day+1), this doc is explicitly "not archivable
  this run" — 2 of its 4 Filed items are still genuinely open (the context-scout bullet-marker bug, outside
  `plans/**`; the AO-backlog-status check for the P0 finalize doc's dispatch inactivity, inconclusive so far) and 2
  more remain routed/low-priority. Deferring to that more recent, dedicated assessment rather than re-litigating
  archival here. No reclassification.
