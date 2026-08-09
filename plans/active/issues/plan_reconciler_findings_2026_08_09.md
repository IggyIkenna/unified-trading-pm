---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — ui tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-0c9e3f (slot 8, 2026-08-09), TRANCHE=ui — the first-ever
  `/plan-reconcile ui` pass (per `ui_consolidated_closeout_2026_07_30.md`'s own Todo 6, unchecked across 4 prior
  `/ag-closeout-audit ui` runs). Corpus: 20 asset_group:[ui] docs (~569KB) — 8 in the 12h grace window (the 5-doc
  covering set + 2 actively-dispatched AO docs + today's own ag_closeout_audit_ui_parked doc), 12 non-grace and
  actionable. Builds directly on the same-day 2026-08-09 `ag_closeout_auditor` run's fresh 14-doc verdict tally.
status: open
nature: issue
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, ui]
related:
  [/plans/active/ui_consolidated_closeout_2026_07_30.md, /plans/active/issues/ag_closeout_audit_ui_parked_2026_08_09.md]
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 8, plan_reconciler agt-0c9e3f, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-0c9e3f, tranche=ui)

## Scope + method

- `TRANCHE=ui` supplied → topic-scoped shard per `cursor-configs/skills/plan-reconcile/SKILL.md` § "Topic-scoped
  (sharded) runs". Population = every doc with `asset_group: [ui]` (2-line YAML-list frontmatter form, `asset_group:`
  then `  [ui]` on the next line — confirmed via a block-aware scan, not a single-line grep) in `plans/active/*.md` +
  `plans/active/issues/*.md`. **20 docs, ~569KB, 6256 lines.** No `plans/epics/*.md` doc is ui-tagged; no doc's
  `parent_epic:` points at the closeout (the tag is the sole signal, as the hub doc itself documents).
- This is the **first-ever `/plan-reconcile ui` run** — `ui_consolidated_closeout_2026_07_30.md` Todo 6 has read "not
  yet run" across 4 consecutive `/ag-closeout-audit ui` passes (2026-08-06/07/08/09).
- Grace set (newest commit <12h old at run start, 2026-08-09T03:07Z): **8 of 20** — the entire 5-doc covering set
  (`ui_consolidated_closeout`, `ui_satellite_ao_dispatch_batch{1,2}[_finalize]`) plus 2 actively-dispatched
  `assigned_vm: planning` docs (`deployment_api_sigabrt_crash_loop_2026_07_24.md`,
  `deployment_registry_firestore_p3_cutover_2026_07_14.md`) plus today's own
  `issues/ag_closeout_audit_ui_parked_2026_08_09.md`. Read-only context this run.
- Non-grace actionable set: **12 docs** (the ag-closeout-audit "candidate" population minus the 2 grace-protected AO
  docs, plus the 2 older `ag_closeout_audit_ui_parked_2026_08_0{7,8}.md`).
- Corpus-wide normative refs (`PLAN_FORMAT.md`, `task_template.md`, `INDEX.md`, `ACTIVE_INDEX.md`) + codex stay in scope
  per the sharding contract.
- Leaned heavily on the same-day `ag_closeout_auditor` run (`agt-db95b9`,
  `issues/ag_closeout_audit_ui_parked_2026_08_09.md`) as a verified-fresh input rather than re-deriving the whole
  orphan/coverage picture from scratch — that run's own remit (completeness-projection) is disjoint from this one's
  (contradiction + false-unchecked + hygiene), but its Phase-1 per-doc reads are recent, corroborated evidence this run
  can build on.

## Flips verified

(populated as verified)

## Archived (verified-done, unlocked, non-grace)

(populated as verified)

## Contradictions

1. **[FIXED] `deployment_registry_firestore_migration_2026_07_14.md` — frontmatter/body self-contradiction on dispatch
   state (P0).** Frontmatter `assigned_vm: planning`/`execution_scope: orchestrator-agent` directly contradicted the
   body's own opening banner ("This is the non-dispatched design/index doc", `assigned_vm: NA`,
   `execution_scope: local-only`). Verified: the doc's own 2026-07-30 na-eligibility-audit Progress Log entry documents
   the flip ("RECLASSIFY... flipped `assigned_vm: NA -> planning`") for a real AO todo the doc briefly carried (now
   `[x]`) — frontmatter is the current/correct value, body banner was never updated since 2026-07-14. Fixed the banner
   to state the doc's dispatch state is live-tracked, not fixed NA. Evidence: hunter-B1 finding F0, independently
   re-verified by reading the full doc myself. unified-trading-pm (this branch, pending final push sha).
2. **[FIXED] Same doc — "fully autonomous, no human in the loop" contradicted its own demonstrated human-escalation path
   (P1).** Banner + "Migration invariants" section both asserted zero-human-in-the-loop, but the doc's own Todo text and
   2026-07-30 Progress Log show this was already exercised for real: GO/NO-GO criterion 1 FAILed and the response was to
   file a tracked human follow-up (`deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md`),
   not auto-remediate. Fixed both locations to state "autonomous on the happy path; a GO/NO-GO failure routes to a human
   follow-up." Evidence: hunter-B1 finding F5, re-verified directly.
3. **[FIXED] Same doc — Phase-index table's P3 halt-reason stale ("measured EMPTY 2026-07-17") vs the doc's own later
   measurements (P2).** The table cell still framed the ongoing halt as "registry is empty," but the SAME doc's
   2026-07-30 Progress Log entries show 192-193 Firestore docs exist (just 0% overlap with live GCE VMs) — same halt
   verdict, materially different current reason. Fixed the cell to state both the historical trigger and the current
   (evolving) GO/NO-GO-criterion-1 reason without hardcoding a re-stale-prone count (points to P3's own doc for the
   current number instead, per CLAUDE.md "prefer deleting a derivable restated fact"). Evidence: hunter-B1 finding
   F-empty.
4. **[FIXED, cosmetic] Same doc — dangling sentence fragment (P3).** "...GCS-write-drop/delete step. stays `draft`
   behind it." was missing its subject; from context (P5's own status elsewhere in the doc) the intended subject is
   "P5." Evidence: hunter-B1 finding F-frag.

## Doc-drift

1. **[FIXED, plan-side] `data_status_cell_grid_rearchitecture_2026_07_18.md` — "Design directions" + todos 2/4 treated
   Precompute (and Bound, for one endpoint) as an undecided 3-way choice; both already shipped.** Codex-alignment hunter
   found `/codex/05-infrastructure/deployment-observability.md` already documents a live precompute rollup worker;
   independently verified myself (not just trusting the hunter) by reading
   `deployment_api/scripts/data_status_rollup_worker.py` directly, confirming
   `deployment-service/terraform/gcp/data_status_rollup_scheduler.tf` exists live, and finding the rollup's own
   pre-existing plan `plans/ai/data_status_offline_rollup_2026_05_06.plan.md`. The plan was the stale side, not codex —
   corrected in place (no todo flipped; the real remaining gap — filtered requests bypass both shipped fast paths — is
   still genuine open work, now correctly scoped instead of re-litigating a settled choice). Side-finding, NOT fixed
   (outside PM-doc-only scope): the worker's own docstring claims "every 5 min" but the live terraform schedule is
   `*/20 * * * *` — a minor code-comment/config drift in `deployment-api`, flagged here for a future code-touching
   session, not actionable by this skill.
2. **[ROUTED — see Filed] `/codex/05-infrastructure/deployment-observability.md` — "defaults to Firestore on GCP" (P0)
   reads as settled/operative with zero caveat that the cutover is under an active, still-unlifted 2026-07-14 operator
   HALT** (dual-write never ran on the live fleet; GCS remains operationally authoritative; latest remeasurement only
   27% Firestore↔fleet overlap). Codex is the stale/premature side — the plan-sanctioned path to fix this exact section
   (`deployment_registry_firestore_p5_verify_2026_07_14.md` todo 3) is itself still blocked on P3. Codex edits are NEVER
   autonomous in this skill — filed + alerted per STEP 6, not applied.
3. **[ROUTED — see Filed] `/codex/03-deployment/data-status-ui-surface.md` — stale re: `HonestCoverageCard` behavior
   (P1).** Describes the card rendering raw `coverage_pct` verbatim; a `deriveCoverage()` recompute fix shipped
   `deployment-ui@7007529` (2026-06-17, over a month ago) that codex never absorbed (`last_reviewed:` blank since
   creation). Filed + alerted, not applied.
4. **[ROUTED — see Filed] `/codex/11-project-management/issue-doc-lifecycle.md` vs recurring
   `ag_closeout_audit_ui_parked_*.md` docs (P1/P2, ambiguous).** Both `_2026_08_07.md` and `_2026_08_08.md` self-declare
   fully-actioned/0-open-todos yet sit `status: open` in `plans/active/issues/` rather than archiving per the codex's
   "archive immediately once acked" rule — but this may be a legitimate doc-class exception (a recurring dated
   audit-trail record functioning more like a decision log) rather than a genuine gap; the codex-alignment hunter
   explicitly declined to assert either reading. Also confirmed cross-tranche (a sibling
   `ag_closeout_audit_defi_parked_2026_08_07.md` shows the same pattern) — wider than this shard can resolve. Filed +
   alerted for an operator/skill-maintainer ruling.

## Hygiene fixes

1. **`deployment_registry_firestore_migration_2026_07_14.md`** — added explicit `effort: max` (was silently relying on
   the todo-count-derived default despite `assigned_vm: planning`; caught by the pre-commit
   `check_effort_signal_ratchet` hard gate when staging this doc's other fixes, and independently already flagged by
   this run's own STEP-1 corpus-wide hygiene sweep as 1 of ~9 ui-tranche docs in the silently-flagged set). Matches the
   convention of every sibling `ui_satellite_ao_dispatch_batch*` doc in this tranche (`effort: max`).
2. **`data_status_cell_grid_rearchitecture_2026_07_18.md`, `data_status_catalogue_true_source_phase2_2026_07_24.md`** —
   same silent-default-effort gap (`assigned_role` set, no `effort:`/`thinking_tier:`); added `thinking_tier: medium` to
   both (human/`assigned_vm: NA` design docs, not AO-dispatched, so `effort: max` isn't the applicable convention —
   matched the one sibling ui doc that already had this field set correctly,
   `cost_observability_deferred_followups_2026_07_10.md`).
3. **`data_status_catalogue_true_source_phase2_2026_07_24.md` — severe leading-whitespace formatting defect (~278
   spaces/line across lines 90-136).** Under CommonMark, content indented 4+ columns past its list-item baseline renders
   as an inert code block — this span (a load-bearing design-rationale writeup: why an identity-catalogue shortcut was
   prototyped and reverted, plus a markdown comparison table) was at serious risk of rendering as unreadable
   preformatted text everywhere the doc is displayed. Content was byte-for-byte preserved; re-indented to the todo's own
   6-space continuation baseline (prettier settled nested paragraphs at 10 for its bold-emphasis continuation
   convention). Verified via `git diff` that only whitespace changed, no wording. Evidence: hunter-B2 finding
   (data_status_catalogue_true_source_phase2:90-137), independently re-measured myself (`awk`-counted 278 leading
   spaces) before fixing.
4. **Both docs above** — bumped `last_updated` to match each doc's own most recent Progress Log entry (2026-08-08 /
   2026-08-07 respectively; both were stale at their `created:` date).
5. **`deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md`** — `parent_epic: infrastructure_master` →
   `deployment_and_user_management_master` (stale post-retag: `asset_group` was corrected `infrastructure`→`ui`
   2026-07-30 but `parent_epic` was missed; hub doc's own Track 2 already treats this doc as
   `deployment_and_user_management_master`-scoped). Also added missing `last_updated` (doc had none; self-flagged as a
   known gap in its own 2026-08-06 Progress Log entry). Evidence: hunter-B2 finding.
6. **`consolidator_throughput_backlog_monitor_2026_07_09.md`** — fixed 4 bare (non-`/`-prefixed) references to
   `issues/phantom_audit_estate_coverage_gap_2026_07_10.md` → `/plans/active/issues/...` (confirmed target resolves at
   that path before fixing); bumped stale `last_updated` (2026-07-10 → 2026-08-07, its own most recent Progress Log
   entry); added `thinking_tier: medium` (same silent-default-effort gap).
7. **`data_status_tab_and_downloads_remediation_2026_06_16.md` (locked — see note below)** — fixed 1 bare reference to
   the archived `data_status_catalogue_csv_download_500_sports_tradfi_2026_07_18.md` issue doc (confirmed it resolves
   under `/plans/archive/issues/`); fixed `assigned_vm: NA` + `execution_scope: orchestrator-agent` mismatch →
   `local-only` (every sibling ui doc pairs `NA` with `local-only`; `orchestrator-agent` normally correlates with
   `assigned_vm: planning` — pre-2026-06-27 schema drift never migrated, per hunter-B2); bumped stale `last_updated`
   (2026-06-27 → 2026-08-07); added `thinking_tier: medium`; also added a missing traceable-source citation
   (`unified-trading-pm@f9672e180` + self-pointer) to a pre-existing `[x]` todo's "operator ruling 2026-08-07" claim —
   caught by the pre-commit `check_plan_operator_ruling_evidence` hard gate when staging this doc's other fixes
   (pre-existing gap, unrelated to my edits, but this doc was staged so the whole-file scan surfaced it; fixed in the
   same commit per the findings-triage rule rather than leaving the checkpoint blocked).
   - **Note on the lock**: this doc carries `locked_by: live-defi-rollout`/`locked_since: 2026-06-16` (same day as
     `created`). Independently investigated (hunter-B2 + my own read of the doc's na-eligibility-audit lineage, 3
     passes): this is a confirmed-intentional **APPLY GATE** (blocks a class of destructive v9 `--apply` migrations
     until every projected index is operator-eyeballed) — NOT a stale/general "don't touch this doc" claim, and the doc
     has been routinely edited by many agents (na-eligibility-audit ×3, context-scout ×4, worker sessions) while under
     this same lock. The 3 hygiene fixes above are unrelated to the APPLY GATE axis (metadata + a dead-link fix, not a
     `--apply` migration action), so proceeded without an unlock ask — narrower in scope than the archival HARD LIMIT
     (`locked_by:` blocks ARCHIVAL without `[unlock-plan]`; this run did not archive this doc).
8. **`deployment_registry_firestore_p5_verify_2026_07_14.md`** — reflowed a malformed heartbeat-cadence cost table
   (pipe/row syntax scattered mid-paragraph across ~10 hard-wrapped lines instead of one row each — confirmed via raw
   inspection, matched hunter-B1 finding F2 exactly); content preserved verbatim (cross-checked the $13/day-at-5,000-VMs
   figure against the sibling migration doc's independent citation of the same number). Bumped stale `last_updated`
   (2026-07-14 → 2026-08-08) + added `thinking_tier: medium` (same silent-default-effort gap, pre-emptive — this
   `status: draft` doc hadn't been flagged yet but matches the pattern).
9. **`cost_observability_deferred_followups_2026_07_10.md`** — bumped stale `last_updated` (2026-07-10 → 2026-08-08, its
   own most recent Progress Log entry — a 29-day gap, the largest in the tranche).

## Zero-checkbox sweep (this skill's standing responsibility, per SKILL.md § "4. ZERO-CHECKBOX docs")

3 hits in the `ui` tranche's 20-doc population: `issues/ag_closeout_audit_ui_parked_2026_08_0{7,8,9}.md` — all read in
full, all genuinely prose-only-by-design audit-record docs (0 fabricated real work found; converting to `- [ ]` todos
would misrepresent an audit RESULT as open engineering work). Recorded in the standing corpus-wide register
`/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md` § "Measurement 2026-08-09 — /plan-reconcile ui"
(this register is this skill's own maintained artifact, not one of the 20 ui-tranche docs — updated per its documented
"standing owner" convention). 0 converted, 0 archived (see Doc-drift item 4 / Filed item 4 for the separate, still-open
archival-POLICY question this same 3-doc family raises).

## Filed

Every genuinely-undecidable item below was BOTH alerted (`POST /blocked`, fires a dashboard escalation) AND filed here
durably, per STEP 6's two-channel routing rule. `routed_to_operator` = 4, `parked_in_issue_doc` (this section) = 4 —
balanced (Phase 5.9(a) ledger check).

1. **`BLK-63280f61`** — 2 codex SSOT staleness fixes need operator approval before applying (codex edits are never
   autonomous): `/codex/05-infrastructure/deployment-observability.md` P0 ("defaults to Firestore on GCP" with no HALT
   caveat) + `/codex/03-deployment/data-status-ui-surface.md` P1 (stale `HonestCoverageCard` description). See
   `## Doc-drift` items 2-3 for full evidence. Recommended: A (apply both as proposed).
2. **`BLK-160d8cee`** — `plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` is fully
   done (3/3 todos `[x]`, hard evidence) but stuck behind `status: open` + an impossible `locked_since` (predates its
   own `created` by ~2 months) — 4th consecutive flag across audit runs with zero action. Asked for `[unlock-plan]`
   authorization to fix metadata + run the 6-step archival ritual. Recommended: A (unlock, I'll archive it this pass).
3. **`BLK-97110aee`** — possible DeFi Phase-E gate-sequencing contradiction in
   `data_status_tab_and_downloads_remediation_2026_06_16.md` (a shipped path-fix pre-dating its own stated TIER-2 gate
   clearing by ~3 weeks) — a data-pipeline-correctness question outside ui-shard domain expertise to resolve solo;
   plausible innocent explanation exists (writer-cutover vs. backfill-apply) but not my call. Recommended: C (route to
   the defi tranche's own reconciliation).
4. **Codex `/codex/11-project-management/issue-doc-lifecycle.md` vs recurring `ag_closeout_audit_*_parked_*.md` docs —
   NOT sent as a live blocked-question** (genuinely ambiguous whether this is even a gap — see `## Doc-drift` item 4 —
   and confirmed cross-tranche, wider than one shard's dispatch can resolve or usefully force a same-day ruling on).
   Filed here for a future `all`-scope `/plan-reconcile` run or a skill-maintainer pass to pick up: either codex needs
   an explicit "recurring dated audit-trail record" exception, or these docs (2 in the ui tranche: `_2026_08_07.md`,
   `_2026_08_08.md`; confirmed ≥1 sibling in `defi`) are a genuine, silently-accumulating archival-discipline gap.

## Archive candidates (operator review)

(populated as verified)

## Refuted (dropped by verify)

(populated as verified)

## Investigated, genuinely still open (recorded so a future session doesn't re-derive this)

Hunter-MissedFlip checked all 36 open todos across the 11 non-locked writable docs against live repo state (git log +
code reads, not just doc prose). 34 are confirmed genuinely open with no shipping evidence — not worth re-listing
individually (they match each doc's own self-assessment). 2 are **partial-ship** — real code exists but doesn't fully
satisfy the todo's own stated ask, so neither was flipped nor is either purely "not started":

- **`issues/cost_observability_deferred_followups_2026_07_10.md` — "Credits/discounts as a first-class view"**: a
  `GrossCredit` component is shipped (`deployment-ui/src/pages/CostObservability.tsx` ~lines 427-463, wired into the KPI
  band + breakdown table) implementing "gross → credits → net." But the todo also explicitly asks for a computed
  "effective discount rate" (%) — not found anywhere near this code. Half the ask shipped.
- **Same doc — "Usage quantity + unit → unit economics"**: `cost_per_gb` + a storage/operations/egress cost-component
  split + raw `vcpu` tracking are shipped
  (`deployment-api/deployment_api/services/cost_observability/{models,resource_rows,queries}.py`). But no `$/vCPU-hour`
  derived metric exists — only a raw vcpu count field — which the todo also explicitly asks for. Half the ask shipped.

Neither should be flipped on this evidence; the genuinely-still-open remainder in each is real, matching the doc's own
current framing. Recorded here as a documented starting point (exact file:line + what's missing) so a future session
implementing these doesn't have to re-derive what's already there.

## Coverage (hunters / batches / docs)

(populated at STEP 7)

## Plans not reached

(populated if applicable — none yet; this run is still in progress, see § "In-flight verification" below)

## Grace-protected findings (deferred to a future `/plan-reconcile ui` run — HARD LIMIT, not this run's to fix)

The 8 grace-window docs (Scope+method above) were read for cross-check context per the skill's rules, and that read
surfaced genuine candidate findings this run could NOT act on (newest commit <12h old at run start). Recording them here
so they aren't silently lost — the next `ui`-tranche run should re-verify each is still current (grace status will have
cleared) before acting:

1. **`issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` todos at "DEFERRED-BY-DESIGN" and `[REVIEW]` (2 items)** —
   both cite blockers (the `e8ce86a` stdout-fix rollout, a cold-start issue) that LATER entries in the same doc suggest
   have since cleared (a "GATE MET" note; "silent since 2026-08-04"), but neither todo was revisited/flipped against
   that newer evidence. Candidate missed-flip, needs fresh verification (was grace at read time, 6h old).
2. **`deployment_registry_firestore_p3_cutover_2026_07_14.md`** — `last_updated: "2026-07-14"` stale vs. Progress Log
   entries through 2026-08-09 (today); also a na-eligibility-audit Progress-Log-shaped entry appears misplaced under a
   "## Codex SSOTs" heading. Both mechanical, low-risk fixes once grace clears (was 0h old at read time).
3. **`ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md` line ~82** — a formatting glitch (irregular multi-space
   gaps mid-sentence, reads like copy-paste corruption, not markdown-breaking). Cosmetic, low priority.
4. **`issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` lines ~748-750/905-907** — cites a companion doc
   (`/plans/archive/2026_07/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`) as
   `"(status: open)"` / `"the live tracker"` while the path is under `/plans/archive/` — worth a quick existence+status
   re-check (mechanical) once the source doc is out of grace.
5. **`issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` lines ~455-456** — flags an untracked concurrent
   investigation (`iam-fix-verify`/`iam-fix-retest` revision tags) with 0 matching plan/issue doc found via a scoped
   grep. Speculative/unconfirmed — only worth a fresh issue doc if corroborated independently by a future run, not
   actioned on this single mention.

Not carried forward (self-resolving, no action ever needed): a stale "4 of ~19" Firestore figure in
`ui_satellite_ao_dispatch_batch1_2026_08_06.md`'s Deferred item 6, and a "9-of-13" vs "8-of-14" orphan-count baseline
drift between `ui_satellite_ao_dispatch_batch2_2026_08_08.md` and its finalize sibling — both batch docs already cite
fresher numbers elsewhere in the same covering-set, so no future action is needed on either.

## In-flight verification (checkpoint note — this run is NOT finished as of this commit)

**Session context checkpoint 2026-08-09 ~04:03 UTC**: this run has 7 commits pushed to `plan_reconciler/agt-0c9e3f` so
far (all contradiction/doc-drift/hygiene fixes + STEP 6 routing complete) and 1 background verification still IN FLIGHT:

- **What**: `npx playwright test --project=chromium tests/smoke/` (full suite, 450 tests) running in `deployment-ui`,
  launched ~2026-08-09T03:52Z, to gate the 3 missed-flip candidates in
  `data_status_tab_and_downloads_remediation_2026_06_16.md` lines ~166-195 (venue-filter frontend, duplicate
  available-dates panel collapse, pagination visible-count selector) — all 3 are independently confirmed code-shipped
  (`deployment-ui@80c547d`) with their sole cited blocker confirmed already resolved (`deployment-ui@067f7cd`,
  2026-07-29); the doc's own 2026-08-07 na-eligibility-audit note says the only remaining gate is "a fresh `pw:L2`
  full-suite green" — this run is that fresh re-verification.
- **Where**: log at this session's scratchpad (`playwright_smoke_run.log`, NOT durable — regenerable by re-running the
  command above; do not treat its absence in a future session as a problem, just re-run it).
- **Resumption instructions for whoever picks this up next** (a fresh session, or me after a context compact):
  1. Check if the process is still running (`ps aux | grep playwright` in `deployment-ui`, or just re-run the command
     fresh — it's idempotent and takes ~35-40 min for the full suite at `workers: 1`).
  2. If it already finished: check the exit code. Clean `exit 0` → flip all 3 todos in
     `data_status_tab_and_downloads_remediation_2026_06_16.md` (lines ~166-195) citing `deployment-ui@80c547d` +
     `deployment-ui@067f7cd` + this fresh full-suite pass as evidence (per `## Contradictions`/`## Flips verified`
     format), commit `docs(plans): flip 3 data-status UI todos — pw:L2 fresh full-suite green [agt-0c9e3f]`, push, and
     append to `## Flips verified` above.
  3. If it failed: do NOT flip — read which spec(s) failed, determine if it's a NEW regression (file it) or an unrelated
     pre-existing flake (note it, still don't flip without a clean run).
  4. Either way, this doc's own `## Coverage`/`## Plans not reached` sections and STEP 7 (final flush + PR) are still
     owed after this resolves — this run is not done at this checkpoint, just durably saved.
- **Why this doesn't block anything else**: this is the ONLY item this run was still waiting on; everything else (all
  fixes, all 3 blocked-questions, the zero-checkbox sweep) is already committed + pushed.
  `git rev-list --count origin/plan_reconciler/agt-0c9e3f..HEAD` = 0 as of this checkpoint.
