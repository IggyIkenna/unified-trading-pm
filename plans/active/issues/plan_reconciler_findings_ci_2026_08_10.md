---
doc_type: issue
title: plan_reconciler findings — ci tranche — 2026-08-10
summary: >-
  Daily deep plan-reconciliation run-findings doc for the ci topic tranche, dispatch agt-fb0ce4 (slot 2). Records
  hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and coverage
  for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, ci, sharded-run]
related:
  [
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_09.md,
    /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
  ]
created: "2026-08-10"
author: plan_reconciler
source: agt-fb0ce4
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-fb0ce4) since 2026-08-10T05:19:46Z
depends_on: []
---

# plan_reconciler findings — ci tranche — 2026-08-10

Dispatch `agt-fb0ce4`, slot 2, tranche `ci`. PM head at run start: `7930a990ec`.

## Scope

**57 docs carry `asset_group: ci`** in `plans/active/` (incl. `issues/`) — computed via a YAML-safe frontmatter parse
(`yaml.safe_load`, same method `docspec.py::parse_frontmatter` uses — comment-safe, avoids the over-match artifact
yesterday's run found in a naive grep). **25 of 57 are inside the 12-hour grace window** (heavy concurrent fleet
activity on this tranche continues — batch12/batch12_finalize pairs, today's `ag_closeout_audit_ci_parked_2026_08_10`,
several same-day issue docs) and are READ-ONLY context this run. **32 are writable** (outside grace) — see Coverage for
the full list.

The `ci` tranche's former epic hub `ci_consolidated_closeout_2026_07_25.md` is already archived
(`plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md`); no active doc carries
`parent_epic: ci_consolidated_closeout` outside the `asset_group: ci` set already captured above.

**Predecessor-run continuity**: `plan_reconciler_findings_ci_2026_08_09.md` (dispatch `agt-04cb0e`, slot 29) is still
`locked_by: plan_reconciler (agt-04cb0e) since 2026-08-09T16:22:00Z` with only 2 commits ever landed against it (start +
one checkpoint) and several sections left `(pending)` — it appears to have died mid-flight before reaching STEP 7 (the
"7 of 8 daily attempts reaped-stale" failure mode the sharded-dispatch design itself cites). Per this skill's own HARD
LIMIT, a `locked_by:` doc is never auto-unlocked by a later run — noted as a routed hygiene finding (see Routed/Filed)
rather than edited directly. `plan_reconciler_ci_late_findings_2026_08_06.md` is fully resolved except 2
deliberately-left-open P3 cosmetic items (archived-doc typo; editorial-judgment title rewrite) — both already correctly
classified as not worth extracting, re-confirmed, not re-litigated this run.

## Flips verified

1. **`archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md` todo 2** — hunter batch 6, HARD
   evidence: already shipped via a different, independently-filed duplicate issue
   (`/plans/archive/2026_08/issues/check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md`,
   `unified-trading-pm@a231c2a80`). Independently re-verified live before flipping: the codex section, the
   `check_archive_candidates.sh` skip logic (4 call sites), and the bats regression test all confirmed present on disk.
   **FIXED**.

No other flip candidates — hunter batches 1-6 collectively checked every open `- [ ]` across the 32-doc writable set;
where evidence existed the checkbox was already flipped, and the remainder are genuinely still open (several
independently re-confirmed AO-eligibility findings, see AO-dispatch-readiness below).

## Contradictions

1. **`quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`** — self-contradiction (P3, one doc): the
   `## Suggested next steps` numbered list (items 2 and 4) still read as "not yet fixed"/"not done this session", but
   the `## Todos` section below it was already corrected 2026-08-07 (na-eligibility-audit) to state both steps shipped
   (`unified-trading-library@dc1dc7df`; fleet grep "none found"). Independently re-verified: Todos section is
   authoritative (carries the sha + dated correction marker). **FIXED**: annotated items 2+4 in the numbered list as
   done, citing the Todos section — `unified-trading-pm` (this run's commit).
2. **`ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`** — self-contradiction (P1, one doc), hunter
   batch 1: the `## Deferred work after 2026-08-06` table (2 rows) was never resynced after later checkboxes flipped —
   "Fix the 6 plan-hygiene ratchets" shows `[x] DONE — closed 2026-08-07` at line 594 but the table still said "Not
   done" (+ a "Recommended NEXT item" pointer telling a reader to redo already-finished work); "Downsize CI VM /
   planning VM" shows both `[x] DONE` at lines 638/687 but the table still said "Operator-owned... pending".
   Independently re-verified both underlying `[x]` claims (read the cited commit messages + evidence inline) before
   fixing. **FIXED**: corrected both table rows + the "Recommended NEXT item" pointer (now points at the one row that is
   genuinely still not-done: re-baseline `qg_resource_baseline.json`).
3. **`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`** — stale "protected repos" list (P1, hunter batch
   1): "6 explicitly-protected repos" (incl. `greeks-service`, `ibkr-gateway-infra`, `instruments-service`,
   `fund-administration-service`) is superseded — 4 of those 6 were public repos REMOVED from self-hosted entirely on
   2026-08-05. Independently re-verified against the live `scripts/workflow-templates/self-hosted-qg-repos.txt` (current
   7-repo list: `agent-orchestrator`, `strategy-service`, `e2e-testing`, `features-service`, `market-tick-data-service`,
   `execution-service`, `ml-service` — none of the 4 removed repos present). **NOT FIXED**: the doc is at 998/1000 lines
   (2 lines of headroom); even the smallest clarifying banner I drafted tipped it to 1001-1003L, breaching the hard cap.
   Reverted my edit cleanly (0 diff) rather than trade one hygiene violation for another. Routed to the operator (see
   Filed) — needs a split/extraction pass before this or the doc's own already-flagged "one entry from breaching a 3rd
   time" risk can be safely addressed.
4. **K=cores/4 physical-vs-logical-core disagreement** (P2, hunter batch 1, cross-doc): `ci_vm_io_starvation_audit...`
   (2026-08-06) claimed the governor code uses physical cores (`floor(8/4)=2`); `qg_host_adaptive_resource_governor...`
   (2026-08-09, "NEW FINDING") claimed it actually uses `lscpu -p=core` logical-CPU counting with no HT dedup, so K
   could be up to 2x too permissive. **RESOLVED — empirically re-verified live on this exact host**:
   `lscpu -p=core | grep -vc '^#'` = 16 (logical), unique core ids = 8 (physical), `nproc` = 16 — confirms the governor
   doc's claim (code counts logical, K is currently 4 not 2) and refutes the audit doc's (physical-core assumption). The
   underlying CODE bug is already correctly tracked as an open todo in `qg_host_adaptive_resource_governor...` (line
   ~420, NEW FINDING 2026-08-09, names the existing `_qg_physical_cores()` fix) — nothing further needed there.
   **FIXED**: corrected the stale claim (2 locations) in
   `ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`.

## Doc-drift

- **`self_hosted_runner_public_repo_revert_2026_08_05.md:related`** didn't list
  `github_actions_operator_gated_followups_2026_07_17.md` even though named directly in that doc's own "Why this plan
  exists" prose (batch 4, P3, mechanical — note: my own first pass mis-attributed this finding to the WRONG file,
  `fleet_workflow_template_dedup...`; caught on self-review before applying). **FIXED**: added the cross-reference.
- **`shared_ci_workflow_repo_extraction_2026_08_06.md` todo 3's premise was false** (batch 4, P3): its cited
  "UNCONFIRMED" propagation-mechanism gap was already resolved the PREVIOUS DAY in
  `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 1 (DONE 2026-08-05) — `rollout-workflow-templates.sh`
  byte-copies via a directory glob (independently re-verified at line 410), no per-file registration needed; the file
  has existed at that path since `168aa509e5` (2026-06-27). **FIXED**: closed todo 3 as moot.
- **`github_actions_operator_gated_followups_2026_07_17.md`'s Phase-7 "fully shipped" checkbox lacks a forward-pointer**
  (batch 4, P3) to the later, much larger `self_hosted_runner_public_repo_revert_2026_08_05.md` (17-18 of the same
  fanned-out repos reverted back to `ubuntu-latest` for public-repo billing/visibility reasons). Not currently
  misleading in a P0/P1 sense (both docs are individually accurate for their own dates). **NOT FIXED**: doc is at
  exactly 1000L (the hard cap, zero headroom) — any net-positive-line addition breaches it. Did fix one unrelated
  corrupted-whitespace artifact in the same doc (net 0 lines). Routed to the operator (see Filed) alongside the other 2
  line-cap-blocked docs.
- **`monitoring_control_plane_master_2026_06_10.md` `parent_epic: observability_master`** — a corpus-wide keyword
  heuristic flagged a mismatch (top match `infrastructure_master`) at run start. Batch 5 independently re-verified: the
  doc's own body (lines 71-74) records an explicit, dated, first-party operator decision ("Parenting — SPLIT: CI
  dashboard + this master under `observability_master`; fleet git-health under `orchestrator_master`") that directly
  outranks the heuristic — matches the prior 2026-08-06 reconciliation run's conclusion. **CONFIRMED CORRECT, no fix
  needed.**
- **`ci_pipeline_speed_and_cost_redesign_2026_08_05.md`** claimed (as a `[x]`-closed P1 todo) a fix
  (`self_hosted_runner_labels` added to PM's own `quality-gates-v2.yml`) that was directly reverted 2 days later by an
  unrelated change (PM went public, free `ubuntu-latest` became available). Independently re-verified live:
  `.github/workflows/quality-gates-v2.yml:58` currently reads `self_hosted_runner_labels: ""`; the reverting commit is
  `unified-trading-pm@c8cd56251e` (2026-08-07). **FIXED**: annotated the claim as superseded, corrected the doc's own
  "Expected impact" misattribution.
- **`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`'s 2026-08-09 na-eligibility-audit entry** cited
  a stale rationale ("still parked as Deferred E8, unruled") — E8 was actually ruled the DAY BEFORE (2026-08-08, todo 5,
  `[x]` DONE). Independently re-verified: todo 6 (`[SCRIPT] P2`, NEW 2026-08-08, implement the ruling) is the doc's
  genuinely-still-open item and gives the same KEEP-NA verdict a valid basis. **FIXED**: corrected the cited rationale
  without disputing the verdict itself (outside this skill's remit — verdict correctness is `/na-eligibility-audit`'s
  call).
- **`post_cutover_silent_assumption_sweep_2026_07_23.md`'s `## Docs (P2)` section** described
  `/codex/08-workflows/ci-cd-flow.md`'s branch-model narrative as still stale — but the SAME doc's own
  resolution-checklist item (`[DOC] P2`, DONE 2026-07-26, `unified-trading-pm@97970974e`) says it was already fixed.
  Independently re-verified live: the codex doc's branch-model section now correctly describes the LDR→main model and
  carries a "Staging re-entry procedure" section. **FIXED**: struck the stale section, pointed to the resolution item.

## Codex corrections applied (mechanical, evidence-cited)

- **`/codex/03-observability/monitoring-control-plane.md`** described deployment-ui's `/fleet` "Fleet Git landing tab"
  as the live single-pane surface — that tab is DELETED (2026-07-27,
  `/plans/archive/issues/deployment_ui_fleet_tab_removal_2026_07_27.md`), per a `🟡 PARTIALLY SUPERSEDED` banner in the
  citing plan's own body (`monitoring_control_plane_master_2026_06_10.md`) plus its Progress Log naming the
  correctly-updated sibling codex doc (`deployment-observability.md`) — this doc was simply missed at the time.
  **FIXED**: corrected the paragraph, stamped `last_reviewed: 2026-08-10` (was empty).
- **`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`** documented 2 of the corpus's 3 shipped
  line-cap carve-outs (RULED 2026-07-30, RULED 2026-08-02) but not the 3rd (RULED 2026-08-09, bounded same-line
  link-repoint on an over-cap doc) — independently re-verified the shipped fix (`unified-trading-pm@d765b4cfb1`,
  `check_line_caps.sh`) and its citing issue doc
  (`plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`) before writing. **FIXED**: added the 3rd
  carve-out section, matching the existing 2 in style and evidence density.
- **`/codex/08-workflows/ci-cd-flow.md:1258-1262`** — same stale `staging-lock-check.yml` claim I found independently
  (batch 4): "still full content — deliberately NOT yet converted" vs. todo 11 (`[x]` DONE 2026-08-08, all 24 repos
  converted). **SUPERSEDED, not applied by me**: a concurrent infra-tranche plan_reconciler run (`agt-716973`, slot-6)
  independently found and fixed the identical staleness first (`unified-trading-pm@16c5f227d3`, landed while I was
  mid-verification). My redundant edit produced a `git stash pop` conflict (2 files, `ci-cd-flow.md` +
  `shared_ci_workflow_repo_extraction_2026_08_06.md`) when reconciling against their concurrent push — resolved by
  discarding my version of this one correction (theirs is equivalent and already live) and re-applying my other,
  non-overlapping edits cleanly on top of their content. No content lost; verified 0 conflict markers / clean diff
  before the final commit.

## Hygiene fixes

**Applied (hunter batch 3, independently re-verified before fixing):**

1. `quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` `related:` entry pointed to
   `plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`, which no longer exists
   there — confirmed via `ls` (target absent at that path, present at
   `plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`, `status: resolved`).
   Repointed to the leading-slash archive path.
2. `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md` had 2 of 3 `related:` entries missing the
   leading-slash repo-root-relative convention — confirmed both targets exist at their stated paths (not dangling, pure
   format). Added leading slashes to both.
3. `monitoring_control_plane_master_2026_06_10.md` (batch 5) had 3 corrupted/missing-slash path references: a `related:`
   entry and a body-prose citation both missing the leading slash on
   `/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md`; a body citation with embedded mid-filename whitespace
   corruption pointing at `consolidator_throughput_backlog_monitor_2026_07_09.md` — target verified to exist at the
   clean path. All 3 fixed.

Corpus-wide `run_hygiene_sweep.sh --ci` hard failures at run start (3): `prettier proseWrap continuation-padding`
(ratchet), `Reference path convention` (ratchet), `assigned_vm:NA corpus size` (ratchet). Per 2026-08-09's precedent,
checked whether any land in-tranche before actioning — **none do** (corpus-wide ratchets with standing owners, not
ci-tranche findings): re-ran `check_reference_paths.py` directly (no `--quiet`) mid-run — both its format (62
violations, baseline 81) and existence (61 dangling, baseline 86) sub-checks currently PASS their ratchets (the `--ci`
sweep's FAIL at run-start was a transient snapshot on this high-churn shared branch, not a stable state — see Progress
Log), and zero of the 123 itemized violations touch any `asset_group: ci` doc as either violator or target.
`assigned_vm:NA corpus size` is a pure corpus-wide count ratchet with no per-tranche attribution and an explicitly
disjoint owner (`/na-eligibility-audit` — this skill does not adjudicate NA-classification correctness, per its own
scope note). No ci-tranche hygiene action needed from the Phase-0 corpus-wide checks.

## Filed

Routed to the operator via `POST /api/slots/2/blocked` (`blocked_id: BLK-6b80187a`, batched Q1-Q4 + 1 FYI note per
SUB_AGENT_MANDATORY_RULES escalation format, options + `[WORKER REC]` marked). Every item below is durably tracked here
too, per Phase-5.9(a)'s routed==parked reconciliation. **9 items filed** (8 sent in the blocked-question call + 1
discovered afterward, item 9 below — the blocked-question mechanism itself, so not something that could have been
included in its own call):

- [ ] [DOC] P1. **`pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` is 1004L, OVER the 1000L hard
      cap** (confirmed via `check_line_caps.sh` directly — the periodic sweep misses this doc because it globs
      `plans/active/*.md` but not `plans/active/issues/*.md`, per hunter batch 2). Needs a split (`continued4`) or an
      explicit ruling that the sweep gap is acceptable. Part of blocked-question Q1.
- [ ] [DOC] P1. **`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` is 998L**, 2 lines of headroom,
      already breached its cap twice before (per its own Progress Log) — blocks even a small stale-content correction
      (the "6 protected repos" fix above, see Contradictions #3) from landing safely. Needs a split/extraction pass.
      Part of blocked-question Q1.
- [ ] [DOC] P1. **`github_actions_operator_gated_followups_2026_07_17.md` is exactly 1000L**, zero headroom — blocks the
      forward-pointer fix above (see Doc-drift) from landing safely. Needs a split/extraction pass. Part of
      blocked-question Q1.
- [ ] [DOC] P2. **`credential_ask_orphan_checker_ping_format_stale_2026_07_27.md` is `assigned_vm: planning` but its
      sole open todo fails the dispatch-scope-eligibility bounded-outcome test** (it's an open design/naming decision —
      "consider whether an IAM-permission gap should get a distinct marker" — not a worker-checkable fact; hunter batch
      2). Needs the design question resolved (then rewrite the todo) or reclassification to `assigned_vm: NA`.
      Blocked-question Q2.
- [ ] [DOC] P2. **`ci_pipeline_speed_and_cost_redesign_2026_08_05.md`'s "5→3 glue" sizing rationale may be moot** now
      that PM carries zero self-hosted load (the fix it was sized against was reverted, see Doc-drift) — hunter batch 5
      flagged this as needing arithmetic across 2 docs, not independently re-verified this run. Blocked- question Q3.
- [ ] [DOC] P3. **AWS Cost Explorer $ quantification item (`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`)
      has been "extraction-ready" since 2026-08-01 (9 days), promised for batch-7, never landed through batch-12**
      (hunter batch 1, fresh-grepped every batch7-12/finalize doc, 0 matches). Needs extraction into the next ci-tranche
      AO-dispatch batch. Blocked-question Q4.
- [ ] [DOC] P3. **`plan_reconciler_findings_ci_2026_08_09.md` (yesterday's predecessor run) is still
      `locked_by: plan_reconciler (agt-04cb0e) since 2026-08-09T16:22:00Z`** — only 2 commits ever landed, several
      sections left `(pending)`, consistent with the "reaped-stale mid-flight" failure mode. A dead session's lock,
      never auto-unlocked per HARD LIMITS. FYI note in blocked-question (not a ruling — the answer is unambiguous, just
      gated on unlock authority).
- [ ] [DOC] P3. **`pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`'s sole open todo has a definition-of-done
      gap** (hunter batch 6): "run clean across a full fleet PR cycle" doesn't say whether the doc's own recorded 49
      pre-existing bats failures are in-scope, or define a threshold for "a full fleet PR cycle." Needs scoping before
      AO dispatch proceeds cleanly. Not separately escalated via blocked-question (lower stakes, bundled here for the
      record per Phase-5.9(b) — every skip/defer gets enumerated, not just a bare count).
- [ ] [INFRA] P2. **Blocked-question answer retrieval may have a real gap.** A harness-level notification stated the
      operator had answered `BLK-6b80187a`, but the two documented retrieval channels
      (`GET /api/slots/$SLOT_ID/messages`; the `messages` array on a `/progress` POST response) both returned empty
      across 6 attempts spanning ~20 min, and 4 guessed alternate endpoint shapes (`/api/blocked/<id>`,
      `/api/blocked-questions/<id>`, `/api/slots/2/blocked-questions`, `/api/slots/2/status`, with and without
      `X-Orchestrator-Secret`) all 404'd. Two explanations, not distinguished this run: (a) a genuine answer-delivery
      gap in the blocked-question mechanism (worth checking whether OTHER plan_reconciler/na-
      eligibility-audit/ag-closeout-audit runs' blocked-questions have silently never received their answers either —
      same failure shape as the escalation-queue's own past `verify_dispatched_escalations` gap, different subsystem),
      or (b) this specific notification fired without a real backing answer (a harness artifact). Worth an operator-side
      check of the dashboard's actual delivery path for `BLK-6b80187a` specifically, and — if genuinely broken — a wider
      audit of whether other slots' blocked-questions are in the same silently-unretrievable state.

## Deferred work after 2026-08-10

| Item                                                         | State              | Blocked on                                                       |
| ------------------------------------------------------------ | ------------------ | ---------------------------------------------------------------- |
| `pytest_timeout_60s_flaky_under_contention_continued2` split | **Operator-owned** | split/extraction decision (line-cap at 1004L, over hard cap)     |
| `fleet_wide_qg_self_hosted_runner_capacity_crisis` split     | **Operator-owned** | split/extraction decision (998L, 2 lines of headroom)            |
| `github_actions_operator_gated_followups` split              | **Operator-owned** | split/extraction decision (exactly 1000L, zero headroom)         |
| `credential_ask_orphan_checker` AO-scope fix                 | **Operator-owned** | a design/naming decision only a human can make                   |
| `ci_pipeline_speed_and_cost_redesign` "5→3 glue" re-check    | **Not done**       | real work — arithmetic re-verification across 2 docs, nobody yet |
| AWS Cost Explorer extraction into next ci batch              | **Not done**       | real work — needs a batch-authoring pass, 9 days overdue         |
| Unlock `plan_reconciler_findings_ci_2026_08_09.md`           | **Operator-owned** | unlock authority (dead-session lock, HARD-STOP per rules)        |
| `pm_bats_tests` definition-of-done scoping                   | **Not done**       | real work — small scoping decision, nobody yet                   |
| Blocked-question retrieval gap investigation                 | **Operator-owned** | needs dashboard-side visibility this worker doesn't have         |

**Recommended NEXT item**: the 3 line-cap-blocked splits (rows 1-3) are the highest-leverage — each unblocks an
already-drafted, already-verified correction that's just sitting blocked on doc size, and
`fleet_wide_qg_self_hosted_runner_capacity_crisis` is one Progress Log entry from breaching its hard cap a 3rd time
regardless of whether this specific correction ever lands. Everything else is lower urgency (no live incident, no
fleet-wide impact).

## Archive candidates (operator review)

- **`ui_build_warm_cache_2026_06_17.md`** — flagged by today's `ag_closeout_audit_ci_parked_2026_08_10.md` as now
  zero-open-work, archival blocked only by `locked_by: live-defi-rollout`. Independently re-verified: 0 open / 4 done
  checkboxes (`grep -cE '^[[:space:]]*[-*] \[ \]'` / `\[x\]`), `status: complete`, `locked_since:` blank. **This is the
  same `locked_by: live-defi-rollout` placeholder-lock defect** a sibling ui-tranche run root-caused and filed today as
  `/plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` (P1, `[OPERATOR]`, pending an
  A/B/C ruling — NOT a genuine lock, traced to `scripts/plans/fix_epic_frontmatter_2026_05_21.py:133`). Not re-filed as
  a duplicate; this doc is 2 more corroborating hits for that ticket, not a new finding. Also found in-tranche with the
  identical signature (`locked_since: 2026-05-21`, predating the doc's own later `created:` date — the same "impossible
  claim" tell): `plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` and
  `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (both `status: open`, not
  independently re-checked for done-ness since the lock is the blocking question either way). Left that corpus-wide doc
  itself untouched — it's <12h old (created today by the ui-tranche run), inside this run's own grace window, and not
  mine to edit; the corroboration lives here with a cross-reference instead, for a future `all` pass (or the operator
  ruling once it lands) to consolidate. **Parked, not archived** — per HARD LIMITS, `locked_by:` is never auto-unlocked
  regardless of how confident the evidence.

## Refuted (dropped by verify)

- **`plan_reconciler_ci_late_findings_2026_08_06.md`'s 2 remaining open todos** (batch1 D1 "todo 2"→"todo 1" typo on an
  archived doc; the mtds monkeypatch-leak title/summary editorial rewrite) — re-read in full this run (not delegated to
  a hunter, already fully read directly): both were re-confirmed as recently as the 2026-08-09 round-9 sweep as
  correctly-left-open (cosmetic-on-an-archived-doc not worth a dedicated pass; genuine editorial-characterization
  judgment call, not a deterministic grep-and-fix). No new evidence this run changes either determination — not
  re-extracted, not re-litigated, candidate dropped.
- **`plan_reconciler_findings_ci_2026_08_09.md`** — 0 open / 0 done checkboxes (pure narrative run-journal, not a
  todo-tracked doc) — not a done-but-unchecked candidate by construction. Its `locked_by:` staleness is tracked
  separately (see Filed).

## Coverage (hunters / batches / docs)

Writable set (32 docs, outside 12h grace):

- plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md
- plans/active/ci_vm_exposure_remediation_2026_08_06.md
- plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md
- plans/active/github_actions_operator_gated_followups_2026_07_17.md
- plans/active/issues/archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md
- plans/active/issues/aws_codebuild_terraform_import_pending_2026_07_22.md
- plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md
- plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md
- plans/active/issues/credential_ask_orphan_checker_ping_format_stale_2026_07_27.md
- plans/active/issues/deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md
- plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md
- plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md
- plans/active/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md
- plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md
- plans/active/issues/operator_ruling_record_gcloud_wif_poisoning_2026_08_08.md
- plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md
- plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md
- plans/active/issues/plan_reconciler_findings_ci_2026_08_09.md
- plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md
- plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md
- plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md
- plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md
- plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md
- plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md
- plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md
- plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md
- plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md
- plans/active/monitoring_control_plane_master_2026_06_10.md
- plans/active/qg_host_adaptive_resource_governor_2026_07_14.md
- plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md
- plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md
- plans/active/ui_build_warm_cache_2026_06_17.md

**6 parallel read-only hunter sub-agents** (sonnet, `SUB_AGENT_MANDATORY_RULES.md` pasted in full at each spawn),
covering all 30 of the 32 writable docs not already fully read directly by me
(`plan_reconciler_findings_ci_2026_08_09.md`

- `plan_reconciler_ci_late_findings_2026_08_06.md` — my own predecessor-continuity docs, see Scope):

1. QG capacity/VM contention cluster (5 docs) — 4 contradiction candidates, 1 hedge-pointer (9-days-overdue extraction),
   1 mechanical (998L near-cap)
2. pytest-timeout flaky-under-contention series (4 docs) — 0 contradictions, 1 line-cap HARD violation (1004L), 1
   AO-dispatch-readiness failure (task briefing itself was wrong about which doc was AO-dispatched — hunter
   self-corrected and checked the right one)
3. quickmerge/mtds-deployment-env-race cluster (5 docs) — 1 self-contradiction, 2 mechanical ref-path issues, 1
   locked-placeholder corroboration; verified 3 commit shas
4. self-hosted-runner/workflow-template/gh-actions infra (5 docs) — 2 contradiction candidates, 1 real codex-drift
   (staging-lock-check.yml), 1 mechanical cross-ref gap; spot-checked a sibling codex doc unprompted, found it clean
5. monitoring/pipeline-redesign/breaking-change/codebuild (4 docs) — 3 contradiction candidates (1 confirmed P1 fix, 1
   needs further arithmetic, 1 resolved as parent_epic-correct), 1 real codex-drift, 3 mechanical ref-path issues; ran
   the AO-dispatch-readiness check on both docs that needed it
6. misc small ci-tranche docs (7 docs) — 1 flip candidate (HARD evidence), 1 contradiction (duplicate-of-archived), 2
   codex-alignment findings (1 real gap, 1 stale-prose), 1 AO-dispatch-readiness gap, content-sanity-checked
   `ui_build_warm_cache` per my own pre-verified claim

**~1.29M hunter tokens, 144 tool calls, ~44 min total wall-clock** (parallel; slowest batch 6 at ~9min). Every candidate
independently re-verified by me before any apply (live file reads, `git log`, an empirical on-host `lscpu` measurement,
filesystem existence checks) — none taken on a hunter's word alone.

## Plans not reached

None — all 32 writable docs were covered (30 via the 6 hunter batches, 2 read directly by me). The 25 grace-window docs
were read only as cross-reference context where a writable doc cited them, per the grace-window contract (never
written).

## Lessons (this run)

- **A corpus-wide hygiene-sweep FAIL can be a transient snapshot, not a stable verdict, on this high-churn shared
  branch.** `run_hygiene_sweep.sh --ci` showed 3 hard failures at run start; re-running the specific check
  (`check_reference_paths.py`) minutes later showed 2 of the 3 passing. Always re-verify a Phase-0 flag's current state
  before treating it as still-live, especially anything corpus-wide rather than doc-specific.
- **`lscpu -p=core | grep -vc '^#'` counts LOGICAL cpus, not physical** — it emits one row per hyperthread sibling with
  no dedup, which looks like it should return physical-core count but doesn't. This bit the original
  `ci_vm_io_starvation_audit...` doc's author (2026-08-06) and my own hunter batch 1 both assumed physical-core
  semantics until an empirical on-host check (`lscpu -p=core` raw output, unique-vs-total row count) settled it. Worth
  remembering for any future host-sizing claim citing this exact command.
- **Self-correction, not a hunter's**: my own first-pass logging mis-attributed the "missing `related:` cross-ref"
  finding to `fleet_workflow_template_dedup...` when the hunter had actually named
  `self_hosted_runner_public_repo_revert_2026_08_05.md`. Caught by re-reading the hunter's raw text before applying, not
  by trusting my own paraphrase in the findings doc. General lesson: when applying a hunter's finding, re-check its
  literal file citation against the source text, not a summary written a few messages earlier.
- **A blind pull→add→commit retry loop is unsafe under this level of branch churn.** Chaining
  `git pull --rebase --autostash && git add $FILES && git commit` inside a tight bash loop, without checking for
  conflict-marker syntax between steps, let one `git stash pop` merge-conflict land literal git conflict-marker text
  (angle-bracket/equals-sign runs) into 2 staged files — caught only because the pre-commit hook's conflict-marker check
  fired, not by the loop itself. The safer pattern used afterward: pull once, explicitly grep for that syntax, only then
  add+commit — one cycle at a time, not a blind N-iteration loop. (Self-referential note: writing this lesson down the
  first time literally tripped the same conflict-marker check on THIS doc — the checker matches the raw character
  sequence anywhere in a staged file, including inside a backtick-quoted description of it, so describe the syntax in
  prose rather than spelling it out literally.)
- **Cross-tranche same-finding collisions are a real, expected occurrence on this fleet, not a bug.** A concurrent
  infra-tranche `plan_reconciler` run independently found and fixed the identical `ci-cd-flow.md` staleness I had (same
  corpus-wide codex doc, read by every tranche that touches CI/CD). Resolution: when a stash-pop conflict shows the
  other side's fix is equivalent and already live, take theirs and drop your redundant edit rather than trying to merge
  two versions of the same correction.
- **The documented blocked-question answer-retrieval channels did not surface an answer this run** despite a
  harness-level notification claiming one existed — see Filed item 9. Noting this here too since it's the kind of thing
  that's easy to explain away as "must have been checking wrong" in the moment, and worth taking at face value as a
  possible real gap instead.

## Progress Log

- **2026-08-10 05:19 UTC** — Run started. FF'd PM + all 25 sibling repo clones (all clean, no reconciliation needed —
  earlier slot-boot heartbeat nudges about dirty repos were stale/already-resolved by the time of first check).
  `run_hygiene_sweep.sh --ci` completed (exit 1: 3 corpus-wide hard failures, none yet confirmed in-tranche).
  `build_health_digest.sh`/`extract_plan_skeleton.sh` kicked off in background — host is heavily contended (multiple
  sibling slots running concurrent hygiene sweeps at the same time, matching yesterday's run's observation). Computed
  ci-tranche population via YAML-safe frontmatter parse: 57 docs, 25 grace / 32 writable.
- **2026-08-10 ~05:35 UTC** — Dispatched 6 parallel hunter batches over the 30-doc writable set (2 docs already read
  directly). Investigated the `locked_by: live-defi-rollout` anomaly independently while waiting — found a sibling
  ui-tranche run had already root-caused it as a corpus-wide placeholder-lock data bug the same day; corroborated with 3
  ci-tranche instances rather than re-filing a duplicate.
- **2026-08-10 ~05:45-06:15 UTC** — All 6 hunter batches returned. Verified + applied the mechanical/HARD-evidence
  findings inline as each batch landed (pipelined, not batched-at-the-end): 1 checkbox flip, 4 self-contradictions
  fixed, 2 codex corrections applied, 5 mechanical ref-path/format fixes, 1 physical-vs-logical-core disagreement
  settled via a live empirical `lscpu` measurement on this exact host.
- **2026-08-10 ~06:16 UTC** — Hit a genuine cross-tranche collision: a concurrent infra-tranche plan_reconciler run
  (`agt-716973`) independently fixed the identical `staging-lock-check.yml` codex staleness I'd found, landing first. My
  `git pull --rebase --autostash` produced real conflict markers (not a clean auto-merge) across 2 files when
  reconciling. Resolved conservatively: discarded my redundant `ci-cd-flow.md` edit (theirs is equivalent, already live,
  verified), reconstructed `shared_ci_workflow_repo_extraction_2026_08_06.md` from clean origin + reapplied my own
  non-overlapping edits, re-verified 0 conflict markers / clean line-caps / clean ref-paths on all 12 files before the
  final commit. No content lost on either side.
- **2026-08-10 ~06:25 UTC** — Committed + pushed the 12-file reconciliation batch (`unified-trading-pm@f1d2dd3e51`),
  synced 0-ahead. Filed the 8 genuinely operator-gated findings (3 line-cap-blocked docs, 1 AO-dispatch-scope violation,
  1 needs-more-arithmetic contradiction, 1 overdue extraction, 1 stale dead-session lock, 1 definition-of-done gap) as a
  batched blocked-question (`BLK-6b80187a`, Q1-Q4 + FYI, options + `[WORKER REC]` marked) — `can_continue: true`.
  Routed==parked reconciled at 8==8 (Phase-5.9(a)).
- **2026-08-10 ~06:35 UTC** — STEP 7: `POST /api/plan-health/result` sent (15 confirmed / 2 refuted, coverage 6 hunters
  / 6 batches / 32 docs, `commit_sha: 2ed4199b00`). STEP 8: a harness notification indicated the operator had answered
  `BLK-6b80187a`, but 6 polling attempts across ~15 min via both documented channels (`GET /api/slots/2/messages`, the
  `/progress` response's own `messages` array) plus several undocumented endpoint-shape guesses (`/api/blocked/<id>`,
  `/api/blocked-questions/<id>`, `/api/slots/2/status`, with and without `X-Orchestrator-Secret`) all returned
  empty/404. Not treating the notification as unfounded — the answer may simply not be retrievable through this worker's
  available HTTP surface. Every one of the 8 filed items is independently durable (this doc's Filed section + the
  standing `BLK-6b80187a` record in the dashboard) regardless. Armed a bounded (480s) background poll of
  `GET /api/slots/2/messages` rather than busy-waiting, and continued other STEP-6/7-adjacent work while it ran.
- **2026-08-10 ~06:50 UTC** — `/pre-compact` invoked mid-wait (background poll `bjg620o2c` still running, not yet
  resolved). Ran the full pre-compact ritual: confirmed `ahead=0`/`behind=0` before starting, found one legitimate
  uncommitted addition (the STEP 7/8 Progress Log entry above — the exact kind of loss this ritual exists to catch),
  swept the scratchpad (12 files, all cheap-to-regenerate tranche-population/hygiene-sweep artifacts, none referenced by
  anything committed, none secret-shaped — deliberately not promoted, see verdict), added the
  `## Deferred work after 2026-08-10` table and `## Lessons` section this ritual requires, and filed 1 new item (9)
  discovered only during this audit — the blocked-question retrieval gap itself. Committing this checkpoint now; STEP 8
  (apply-answer-then-`/done`) resumes once the background poll resolves (answer found, or its 480s bound expires) — not
  resolved as of this checkpoint, so `/done` has NOT been called yet.
- **2026-08-10 ~07:02 UTC** — Background poll `bjg620o2c` completed: `loop_exit=124` (timeout — the 480s bound expired
  with `GET /api/slots/2/messages` still returning `{"messages":[]}"` throughout). Ran one final direct re-check of both
  documented channels post-timeout: `/api/slots/2/messages` still empty, `/api/slots/2/blocked` returns
  `405 Method Not Allowed` (not a data channel). Treating this as confirmed-unresolved rather than retrying further —
  the async-wait-and-poll-discipline HARD RULE calls for a bounded watchdog, not indefinite polling, and it already ran
  to its bound. Not escalating further this run: item 9 above already captures the gap as a durably filed, routed
  finding; `can_continue: true` was set at blocked-question submission time (SUB_AGENT_MANDATORY_RULES ASK-never-BLOCK),
  so the sweep's completion was never contingent on this answer arriving. Proceeding to close the one-shot lifecycle.
