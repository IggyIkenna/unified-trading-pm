---
doc_type: plan
title:
  UI satellite docs — AO dispatch batch 1 (3 conflict-cleared todos extracted from 2 of 12 orphaned ui-tranche docs; the
  ui tranche's FIRST batch)
summary: >-
  First-ever `/ag-closeout-audit ui` run (2026-08-06, Autonomous/AO-dispatched, dispatch agt-8d6508). Phase 0 found the
  ui tranche's covering set is `ui_consolidated_closeout_2026_07_30.md` alone — a digest with zero AO-dispatchable todos
  of its own (its 5 Todos are explicitly self-declared "Verification-only... not itself AO-eligible") and no
  `ui_*_satellite_ao_dispatch_batch*`/`_finalize` pair has ever existed. Phase 1 (12-agent Workflow) read all 12
  tranche-primary candidate docs end-to-end and classified 9 as orphaned (`orphaned_never_touched`), 2 as
  `archivable_after_planned_work` (already claimed by named active sibling plans), and 1 as fully done but stuck at a
  stale `status: open` (not this plan's concern — see Findings). Phase 3 applied the dispatch-scope eligibility test +
  the mandatory conflict check across all 9 orphaned docs: the large majority of their remaining work is genuinely
  operator-gated (explicit `[HUMAN]` tags, unmade design decisions, KEEP-NA-confirmed items), time-gated (a live-fleet
  convergence measurement, a sequential-phase dependency), or too-large/risky for a first-pass batch todo (one 953-line
  live multi-phase doc this SAME concern was independently raised about by `infra_satellite_ao_dispatch_batch1`'s own
  Deferred section on 2026-07-26, back when this doc was still infra-tagged). Only 3 todos, from 2 source docs, cleared
  every gate — this is a deliberately small first batch, not an exhaustive one; see `## Deferred` for the other 9
  orphaned items and why each is held back.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags: [ui, ao-dispatch, satellite-docs, batch-1, plan-hygiene, close-out]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-07"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.1
estimate_calibrated_ai_days: 0.9
assigned_role: ui_developer
effort: max
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ui` run 2026-08-06 (Autonomous/AO-dispatched mode, dispatch agt-8d6508, tranche-sharded per the
  ag_closeout_auditor role). Phase 0 found the ui covering set is a single non-dispatching digest with no batch plan
  (this tranche's own first-ever run); Phase 1 read all 12 tranche-primary docs end-to-end via a 12-agent Workflow and
  classified 9 as orphaned; Phase 3 applied the dispatch-scope eligibility test + the HARD conflict check before
  drafting anything here.
---

# UI satellite docs — AO dispatch batch 1

> **`status: active` — operator-approved 2026-08-08, ingested/dispatched.** Drafted autonomously 2026-08-06 by the
> scheduled `ag_closeout_auditor` role; a fresh conflict-check re-verified the original Phase 3 clearance still held
> before dispatch — see `## Operator approval gate` at the bottom for what approving this batch meant, and the Progress
> Log for the re-check.

## Why this plan exists (the coverage gap, measured)

`ui_consolidated_closeout_2026_07_30.md` § "Todos" carries 5 items, but its own header states they are
"Verification-only — measures whether the tranche is actually done, not new work to dispatch (`assigned_vm: NA`, not
itself AO-eligible)" — a digest, not dispatch, the same structural gap every `/ag-closeout-audit` tranche starts from.
No `ui_*_satellite_ao_dispatch_batch*` or matching `_finalize` plan has ever existed
(`ls plans/active/ | grep -E 'ui.*(satellite|ao_dispatch|batch)'` → nothing; `plans/archive/*/` has no archived ui batch
either — this tranche is only 8 days old, launched 2026-07-30). So the audit question "if the closeout plan's own todos
and every active batch ran to completion, what is left orphaned?" resolves to "everything not self-dispatched," because
nothing in the covering set does anything. This plan starts the drain.

**Measured 2026-08-06**: of 12 tranche-primary candidate docs, 9 are orphaned (`orphaned_never_touched`), 2 are
`archivable_after_planned_work` (their remaining work is already named and claimed by sibling active plans —
`deployment_registry_firestore_migration_2026_07_14.md` cites its own P3/P5 phase docs;
`deployment_api_sigabrt_crash_loop_2026_07_24.md` is itself `assigned_vm: planning` + `status: open`, i.e.
self-dispatched), and 1 is fully done but stuck at a stale `status: open` (see `## Findings`, not a batch concern). This
plan extracts the 3 items that are both genuinely AO-eligible (bounded, worker-determinable, no undecided judgment call)
AND conflict-clear today.

## Rules this plan follows

- Every todo ends with `Source: \`<doc>.md\`` naming the satellite doc it was extracted from, plus a **Done when**
  clause.
- Same-priority todos dispatch CONCURRENTLY by default, so zero same-file collisions was a hard requirement — verified
  pairwise across all 3 todos (they touch 3 disjoint targets: a deployment-api instrumentation path, a brand-new issue
  doc, and an existing codex doc) and against the corpus (checked each target for an existing claimer — see
  `## Deferred` item under RESOLVED BY LOGIC for the one near-miss found).
- `sequential:` deliberately UNSET — this is not a dependency chain.
- Anything gated on an unmade operator/design decision, on elapsed real time, or on a doc too large/fast-moving to
  safely extract from is in `## Deferred` with the reason — not dispatched speculatively.

## Todos

- [x] ✅ [BACKEND] P1. **Measure + profile the cell-grid build's memory footprint.** Instrument `deployment-api`'s
      cell-grid endpoint/build path to confirm, with real numbers, the per-service memory growth pattern this source
      doc's OOM root-cause claim describes (repeated deployment-api OOMs reading the whole manifest for full-history
      date-range windows — re-confirmed live-code-accurate as of a 2026-07-22 trace in the source doc). This is the
      source doc's OWN todo 1, independent of its still-undecided todo 2 (the bound/stream/precompute design-gate,
      correctly held NA/operator-gated — see `## Deferred`) — a plain measurement, not a design choice. **Do NOT**
      attempt the design-gate decision or any implementation from todos 3+ in the source doc; those remain correctly
      un-dispatched pending the design call this todo's own output should inform. **Done when**: a measured
      memory-footprint number/curve (e.g. peak RSS vs date-range-width, or manifest bytes read vs range) is recorded in
      the source doc's own Progress Log, and its own todo 1 checkbox is flipped citing this evidence. Repo:
      deployment-api. Source: `data_status_cell_grid_rearchitecture_2026_07_18.md`. — deployment-api@8a36931

- [x] ✅ [REVIEW] P2. **CORRECTED 2026-08-07 (was: "file a new artifact-pipeline metadata-gaps issue doc" — stale, would
      have created a duplicate; see below) — reconcile the source doc's stale Phase-5 issue-filing checkbox + fix the
      one genuinely-still-wrong item in the doc it should have pointed at.** The source doc's own line 652 checkbox
      ("File `plans/active/issues/artifact_pipeline_metadata_gaps_<date>.md` with the 6 pipeline bugs above... Verify
      bug #2 first") is stale: its own "Pipeline bugs found" section (a few lines above) and its "Deferred work after
      2026-07-23" table both already state this filing was done 2026-07-21, under a DIFFERENT name —
      `plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` — and bug #2 (the one
      the stale checkbox says to "verify first") was itself already resolved as **NOT A BUG** in that same section
      ("never reproduced... dropped"), not something left to verify. Filing a second doc now would duplicate existing,
      already-mostly-resolved tracking. Correct actions instead: (1) flip the source doc's line 652 checkbox `[x]`,
      citing `build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` as where the filing already
      happened; (2) that issue doc's own #1 item still frames the `version`-tag question as open/unconfirmed, but the
      source doc's Progress Log (2026-07-24) already root-caused it — "the semver-agent that would compute + send
      `version` is dead, deliberately... SHA-only tagging is the expected, intentional consequence, not a defect" — the
      source doc itself flags this exact correction as an owed follow-up ("out of this plan's direct scope; flagging
      here so it isn't lost"); apply it to that issue doc's #1 with the same evidence. **Done when**: the source doc's
      line-652 checkbox is flipped citing the existing issue doc, and that issue doc's #1 item reflects the
      confirmed-dead-semver-agent finding. Repo: unified-trading-pm. Source:
      `artifact_pipeline_observability_2026_07_17.md` (line 652), cross-referencing
      `build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`. — unified-trading-pm@d2094b791

- [x] ✅ [REVIEW] P2. **Fix the 5 named `dual-cloud-image-builds.md` codex drifts.** Correct
      `/codex/05-infrastructure/dual-cloud-image-builds.md` per the source doc's own "Phase 5" description: registry
      name, tag convention, trigger/project naming, the canonical-trigger claim, and empty-manifest provenance — then
      run the standard post-phase codex audit for this doc (check the rest of that codex file against current behavior
      while touching it, not just the 5 named lines). A narrowly-scoped doc-correction action, not implementation work.
      **DONE 2026-08-08**: all 5 named drifts corrected with fresh 2026-08-08 evidence (live `gcloud artifacts`,
      `gcloud builds triggers`, and `workspace-manifest.json` re-verification — not just re-citing the 2026-07-17
      finding); AWS-side sub-claims retained unverified-this-pass due to an identity/permission gap (tracked as a
      follow-up, not silently assumed). Post-phase audit additionally found + fixed 2 more stale sections
      (live-defi-rollout trigger claim now stale-in-the-other-direction; reusable validate workflow moved repos
      2026-08-06). 5 smaller code/infra findings surfaced during verification filed as follow-up todos rather than fixed
      inline (out of this narrowly-scoped doc task):
      `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md`. Source doc's own Phase 5 checkbox flipped
      too. Repo: unified-trading-pm. Source: `artifact_pipeline_observability_2026_07_17.md`. —
      unified-trading-pm@dab5f0273

## Deferred — real remaining work held back, with the reason (per the non-batchable taxonomy)

**OPERATOR-GATED** (an undecided design/judgment call or an explicit `[HUMAN]` tag — no amount of re-triage resolves
these; they need a ruling, then they become normal batch candidates):

1. **`data_status_catalogue_true_source_phase2_2026_07_24.md`'s sole open todo** (P3, true-catalogue/expected-universe
   source) is explicitly self-described as "architecturally open-ended" with a stated prerequisite — the prediction
   `/catalogue` 79-row `_dedupe_latest` collapse must be decided first. Two independent `na-eligibility-audit` passes
   (2026-07-30, 2026-08-06) both confirmed KEEP-NA valid on exactly this basis.
2. **`data_status_cell_grid_rearchitecture_2026_07_18.md`'s own todo 2** (design-gate: bound vs stream vs precompute)
   and everything downstream of it (todos 3-7) — a genuine three-way architecture choice this batch's todo 1
   (measurement) is meant to inform, not preempt.
3. **`deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md`'s sole open todo** is itself `[HUMAN]`-tagged in
   the source doc (an architecture trade-off: reuse the existing 45s-TTL inventory endpoint vs. build a narrower
   alert-check-only path). KEEP-NA-confirmed twice (2026-07-30, 2026-08-06).
4. **`consolidator_throughput_backlog_monitor_2026_07_09.md`'s two `[REVIEW]` deploy-gate closers** (QG+verify+deploy
   for WS-1 and WS-3) are explicitly operator-deferred (2026-07-10) to "end-of-cockpit-plans" — a stated milestone,
   local-dev-only until then. Not neglected; deliberately paused.
5. **`cost_observability_deferred_followups_2026_07_10.md`'s 2 explicitly-gated items**: business-context enrichment
   (asset_group/archetype spend view) awaiting the operator's own By-label evaluation; AWS CUR historical backfill
   awaiting Ikenna's decision (Athena only holds July-2026, a real data-availability constraint on the decision too).

**TIME-GATED** (depends on elapsed real time or a sequential-phase dependency — re-triage will keep finding the same
"not yet" until the clock/phase actually passes):

6. **`deployment_registry_firestore_p3_cutover_2026_07_14.md`'s 4 remaining todos** (drop GCS-write, soak-verify,
   snapshot+delete GCS blobs, ship) are held by a dated 2026-07-14 operator HALT on a 4-item GO/NO-GO checklist.
   Re-measured 3 times already (2026-07-14, 2026-07-30 ×2) — 3 of 4 criteria fully pass with fresh live evidence; only
   criterion 1 (Firestore doc-count ≈ live-VM-count) has not converged (4 of ~19 running VMs represented at last
   measurement, rest awaiting a boot-cycle). This is a passive fleet-convergence wait, not a code defect — and several
   of the remaining steps are irreversible GCS-blob deletes needing their own `[OPERATOR]` + delete-safety citation once
   ready, not a bare AO todo. Re-check at finalize time (see the paired finalize plan).
7. **`deployment_registry_firestore_p5_verify_2026_07_14.md`'s 3 remaining todos** (codex SSOT update, CLAUDE.md
   one-liner, archival ritual for the whole 6-phase chain) are explicitly sequenced behind item 6 above landing in prod
   — writing "the registry IS Firestore" before the cutover completes would be false, per the doc's own 2026-07-14
   Progress Log.

**TOO-LARGE-OR-RISKY-FOR-A-BATCH-TODO** (needs its own dedicated look, not a first-pass batch slot):

8. **`artifact_pipeline_observability_2026_07_17.md`'s remaining 10 open items** beyond the 2 extracted above: Phase 1
   snapshot worker (net-new component, not started); Phase 3d tarball-lane display fix (itself blocked pending a net-new
   VM-launch deploy provider); Phase 4 absorb/retire `CloudBuildsTab` (×2, real UI deletion + route retirement in a live
   multi-phase build); Phase 6 stretch items (3 of 4 still open, explicitly optional/lower-priority); Phase 7
   `[REVIEW] P0` "STILL OPEN — prod is silent even with all three fixes live," an active investigation explicitly
   operator-paused since 2026-07-24 pending an untested CPU-throttling hypothesis. **Precedent**:
   `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own Deferred section independently flagged this SAME doc (then
   still infra-tagged, 23 open items at the time) as too-large-or-risky, stating "folding even its cleanest candidate
   risks colliding with its own in-flight state." This batch judged the 2 items it DID extract (both `[REVIEW]`-tagged
   meta/doc actions — filing an issue doc, correcting a codex doc — neither touching the pipeline's actual running code)
   as a narrower, lower-risk exception to that general caution; everything implementation-shaped or touching the live
   build stays deferred, consistent with the prior audit's judgment. A future batch (or a dedicated standalone plan, per
   the prior audit's own recommendation) should pick this doc up once Phase 7's investigation resolves and the doc's
   churn rate settles.
9. **`data_status_tab_and_downloads_remediation_2026_06_16.md`'s 8 remaining items** — a large (455-line), multi-phase,
   `locked_by: live-defi-rollout` doc spanning UI polish (gated on a fresh pw:L2 full-suite re-run), a DATA scope
   investigation (Yahoo/Kalshi out-of-scope check), an explicitly-still-owned deferred phantom-row audit gated on this
   same doc's own APPLY GATE + TIER-2 v9 migration, a per-service `BucketNamingError` bug list, and a P0 operator
   sign-off gate. Deferred whole rather than cherry-picked this run given the mixed gating (some items ARE plausibly
   bounded — the Yahoo/Kalshi scope-check and the `BucketNamingError` fixes look like reasonable batch2 candidates — but
   the doc needs a dedicated closer read than this first pass gave it, and the `locked_by` field's real semantics are
   unclear, see `## Findings`).

**NEEDS VERIFICATION** (possibly already covered or needs closer scoping before it's safely batchable — not the same as
a cross-plan conflict, but not yet a clean batch candidate either):

10. **`consolidator_throughput_backlog_monitor_2026_07_09.md`'s WS-3 "per-run output-production verdict endpoint"** todo
    — the Phase-1 audit found much of its originally-scoped intent was later delivered under separately-shipped
    `fired_but_empty`/stale-output/verdict-badge todos, but no Progress Log entry explicitly closes or supersedes THIS
    specific checkbox. Recommend a `/plan-reconcile ui` pass check whether it's already effectively done before drafting
    a fresh implementation todo for it in batch2.
11. **`cost_observability_deferred_followups_2026_07_10.md`'s 4 unscheduled P3 items** (month-aware AWS cutoff,
    credits/discounts view, usage-quantity unit economics, "Other resources" leaf table) are real, bounded,
    AO-eligible-looking feature work — but all 4 plausibly touch the SAME two files (`deployment-api`'s costs route +
    `deployment-ui`'s `CostObservability.tsx`), which would collide if dispatched as 4 separate concurrent todos per
    CLAUDE.md's same-file concurrency rule. Needs a closer read to properly scope (combine into 1-2 sequential todos, or
    confirm genuine independence) before a future batch, rather than guessing the split here.

## Findings surfaced during extraction that are NOT todos here

- **`issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` is fully done but not archived.** All 3
  todos are `[x]` with fresh re-verification evidence through the 2026-08-06 context-scout entry (no reopening).
  Frontmatter still reads `status: open` with `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` — a lock
  timestamp that PREDATES the doc's own `created: 2026-07-21` by two months, which is impossible for a genuine exclusive
  claim and strongly suggests a stale/placeholder value rather than a live lock. Out of this skill's scope to fix
  (archival needs `[unlock-plan]`, never autonomous) — flagging for `/plan-reconcile ui` or `/archive-candidates-audit`.
- **`locked_by: live-defi-rollout` appears on 62 active docs corpus-wide**
  (`grep -rl '^locked_by: live-defi-rollout' plans/active/*.md plans/active/issues/*.md | wc -l` → 62). Whether this is
  a genuine per-doc exclusive-claim mechanism or a stale authoring-template default that's silently affecting archival
  eligibility workspace-wide is unclear from this ui-scoped run alone — worth a dedicated corpus-wide check, not fixed
  here.
- **`ui_consolidated_closeout_2026_07_30.md`'s own Track 3 and Track 4 close-out-criterion prose is stale.** Track 3
  still reads "alerts N+1 read pattern fixed at root, not just the two stopgaps" and Track 4 still reads "mock/live
  contract parity restored on all 12 drifted endpoints" as if open — both are already fully resolved and archived
  (`issues/alerts_endpoint_per_object_gcs_read_performance_2026_07_23.md`,
  `issues/deployment_api_live_mock_parity_2026_07_17.md`, both confirmed archived+resolved this run). A future touch of
  the tracker should trim these criteria to what's actually still open.
- **The tracker's own P2 todo #5 ("corpus-wide ui retag audit still owed") remains genuinely unresolved.** Not
  re-attempted here (separate, already-tracked scope, deliberately deferred by the tracker's own 2026-07-30 session).
  The 2 named candidates (`monitoring_control_plane_master_2026_06_10.md`, `ui_build_warm_cache_2026_06_17.md`, both
  currently tagged `ci`) are still un-triaged as of this run.
- **No Orthogonality HARD CHECK violations found** — all 12 candidate docs' `asset_group` arrays are cleanly
  single-tagged `[ui]` with a dated correction comment; no dual-tag mistags.

## Operator approval gate

Approving this plan means: flip `status: draft` → `active` here (the finalize plan ships `active` from the start — see
`task_template.md` §4's no-double-gate rule). Until then nothing here is ingested or dispatched (`plans/PLAN_FORMAT.md`
— `status: draft` is not ingested). Before flipping, note:

1. **This is batch 1 of an expected several** — the ui tranche is 8 days old and this is its first audit; the large
   operator-gated/time-gated population in `## Deferred` is expected for a brand-new tranche, not a sign this batch is
   incomplete. Items 6-7 (Firestore) and 10-11 (verification-needed) are the most likely to convert quickly once
   re-checked.
2. **Todo 2's "notify Ikenna" clause** is a findings-triage notification (cross-repo, touches Ikenna's CI area), not a
   destructive or irreversible action — no `[OPERATOR]` tag needed, but flagging it here for visibility since it's a
   human-facing action.
3. **Item 6 in Deferred (Firestore P3 cutover) contains irreversible GCS-blob deletes once its GO/NO-GO clears** — a
   future batch drafting those specific steps will need `[OPERATOR]` + a delete-safety citation per CLAUDE.md, not a
   bare todo. Flagging now so it isn't missed later.

## Codex SSOTs (read before touching a todo)

`/codex/05-infrastructure/deployment-observability.md` · `/codex/03-deployment/data-status-ui-surface.md` ·
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` ·
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`

## Progress Log

- **2026-08-06** — Drafted by `ag_closeout_auditor` (dispatch agt-8d6508, `/ag-closeout-audit ui`, Autonomous mode,
  operator away). Left `status: draft` — flips to `active` only on explicit operator approval.
- **2026-08-07 (ag_closeout_auditor, dispatch agt-eb521b, slot 9)** — Second `/ag-closeout-audit ui` run (still
  `status: draft`, still pending operator approval — no dispatch has happened yet). Fresh Phase 1 (12-agent Workflow)
  re-classified all 12 tranche-primary docs against this batch's now-existing coverage:
  `data_status_cell_grid_rearchitecture_2026_07_18.md` and `artifact_pipeline_observability_2026_07_17.md` moved from
  `orphaned_never_touched` (2026-08-06 baseline, before this batch existed) to `orphaned_partial_coverage` (this batch's
  Todos 1/2/3 now cite them) — expected drift, not a new problem; the other 7 orphaned docs + 3 non-orphaned docs are
  unchanged. New orphan baseline: 9 of 12 (was 9 of 12 — same count, composition shifted as described). **Corrected Todo
  2** (was: file a new `artifact_pipeline_metadata_gaps_<date>.md` issue doc) — a fresh per-doc read found the source
  doc's own "Pipeline bugs found" section + "Deferred work" table already state this filing was done 2026-07-21 under a
  different name (`issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`), and that the "verify
  bug #2 first" instruction refers to a bug already resolved as NOT-A-BUG in that same section — executing the original
  Todo 2 as written would have created a duplicate doc. Redirected it to the actual remaining work: flip the source
  doc's stale line-652 checkbox citing the existing issue doc, and correct that issue doc's own stale #1 item (the
  source doc itself already flags this exact correction as an owed follow-up). No conflict-gated items cleared from
  `## Deferred` (re-checked all 11 via git log + fresh per-doc reads; zero material changes since 2026-08-06 on any of
  them — see `issues/ag_closeout_audit_ui_parked_2026_08_07.md` for the full Phase 0/1 findings write-up, including 2
  plausible `ui`-mistag candidates found this run, not retagged pending the tranche's own corpus-wide retag pass). Per
  the skill's iterative-drain guidance, did NOT draft a batch2: nothing conflict-clear has newly emerged, this batch
  itself is still unapproved/undispatched, and batch2-candidate discovery is explicitly this batch's own finalize plan's
  job (todo 2) once triggered. Recommendation carried to `/done` evidence: approve + dispatch this batch; batch2
  candidates will surface naturally once the finalize plan's re-check runs.
- **2026-08-08 (operator approval)**: flipped `status: draft` → `active` after a fresh conflict-check: (a) no
  `deployment_and_user_management_master` sibling batch drafted after this one besides batch2
  (`ui_satellite_ao_dispatch_batch2_2026_08_08.md`, also flipped active today in the same session) — the two batches'
  todos touch disjoint target files (this batch: deployment-api cell-grid endpoint, a stale-checkbox reconciliation, and
  a codex doc; batch2: `deployment-api/routes/costs.py` + `deployment-ui/CostObservability.tsx`), no collision; (b) no
  new active `parent_epic: deployment_and_user_management_master` claim found on any of the 3 todos' targets; (c)
  `ui_consolidated_closeout_2026_07_30.md` unchanged since this batch's 2026-08-07 re-verification. `locked_by` unset.
  Dispatching.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
