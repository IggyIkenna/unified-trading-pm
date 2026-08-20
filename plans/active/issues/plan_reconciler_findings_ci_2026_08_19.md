---
doc_type: issue
title: plan_reconciler findings — ci tranche — 2026-08-19
summary: >-
  Daily deep plan-reconciliation run-findings doc for the ci topic tranche, dispatch agt-f212cb (slot 1). Records
  Phase -1 predecessor-doc reconciliation (2 fully-resolved findings docs archived), hunter-detected candidates,
  adversarial-verification outcomes, applied fixes, routed operator questions, and coverage for this run. Also the
  progress journal for the run itself.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, ci, sharded-run]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/plan_reconciler_findings_ci_2026_08_16.md,
    /plans/archive/issues/plan_reconciler_findings_ci_2026_08_10.md,
  ]
created: "2026-08-19"
author: plan_reconciler
source: agt-f212cb
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.3
calibrated_ai_days: 0.3
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: "plan_reconciler (agt-f212cb) since 2026-08-19T18:19:00Z"
locked_since: "2026-08-19T18:19:00Z"
depends_on: []
context_scope:
  [
    /plans/archive/issues/plan_reconciler_findings_ci_2026_08_16.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# plan_reconciler findings — ci tranche — 2026-08-19

Dispatch `agt-f212cb`, slot 1, tranche `ci`. PM head at run start: `4865661cd2` (before FF).

## Scope

**56 docs carry `asset_group: ci`** in `plans/active/` (incl. `issues/`), computed via
`generate_tranche_doc_inventory.py --tranche ci` (never a same-line grep, per SKILL.md), taken AFTER Phase -1's
archival of 2 predecessor findings docs (which were part of the tranche themselves). **18 of 56 are inside the
12-hour grace window** (a notably hot corpus this run — includes 2 docs this run's own Phase -1 edits just touched:
`ag_closeout_audit_ci_parked_2026_08_16.md`, `ci_tranche_zero_checkbox_archive_sweep_2026_08_18.md`). **38 are
writable.** Of those, **7 were already directly investigated with HARD evidence during this run's own Phase -1 pass**
(see below) — folded into this doc's coverage rather than re-dispatched to a hunter. **31 dispatched to 6 parallel
hunter batches.**

## Phase -1 — predecessor findings-doc reconciliation

Full detail in the commits themselves (`unified-trading-pm@b30280613a`). Summary: both
`plan_reconciler_findings_ci_2026_08_10.md` and `plan_reconciler_findings_ci_2026_08_16.md` had every leftover item
reach a terminal state on fresh re-check (the shared blocker — a blocked-question answer-retrieval gap — resolved via
`agent-orchestrator@4a0753791a`, independently verified reachable on `origin/live-defi-rollout`). Both archived
(`git mv` to `plans/archive/issues/`), 2 structured referrers repointed
(`ag_closeout_audit_ci_parked_2026_08_16.md`, `ci_tranche_zero_checkbox_archive_sweep_2026_08_18.md`).

## Docs already covered by Phase -1 investigation (not re-dispatched to a hunter)

Directly read + checkbox-verified (`grep -cE` against live content) during Phase -1's investigation of the
`ci_tranche_zero_checkbox_archive_sweep_2026_08_18.md` plan's own todos and the grace-window doc:

1. `qg_host_adaptive_resource_governor_2026_07_14.md` — read in full to line 549/930 this run. Its "ledger
   unification" open todo (2026-08-03-dated) independently re-verified as genuinely-scoped, self-disambiguated from
   an already-shipped sibling fix — NOT stale/contradictory (the predecessor 2026-08-16 doc's claim to the contrary
   could not be reproduced). No action needed.
2. `qg_sentinel_environment_blind_2026_07_23.md` — 0 open / 5 done, confirmed fresh. Tracked as an open todo in
   `ci_tranche_zero_checkbox_archive_sweep_2026_08_18.md` (AO-dispatched, `assigned_role: review`) — correctly
   pending its own dispatch, not a gap.
3. `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` — 0 open / 31 done, confirmed fresh. Same
   archive-sweep-plan tracking as above.
4. `sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` — 1 open / 6 done — **no longer** a
   zero-checkbox candidate; a genuine new P3 todo (`ldr_to_main_fleet_promote.sh:638`'s `gh api` call) appeared since
   2026-08-16. Correctly active with real open work — no action needed.
5. `deployment_service_basedpyright_ratchet_exceeded_sports_trigger_2026_08_08.md` — 0 open / 1 done, confirmed
   fresh. Same archive-sweep-plan tracking.
6. `codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md` — 0 open / 6 done,
   confirmed fresh. Same archive-sweep-plan tracking (this is the plan's own NEXT undispatched todo, item 2).
7. `ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md` — 0 open / 2 done, confirmed fresh. Same
   archive-sweep-plan tracking.

None of these 7 need a fresh hunter read this run — all independently re-verified with direct tool-call evidence
during Phase -1, not carried forward from a prior run's claim.

## Hunter dispatch (Phase 1 / STEP 3)

**6 parallel read-only hunter batches dispatched** (sonnet, `SUB_AGENT_MANDATORY_RULES.md` pasted in full at each
spawn) over the 31 docs not already covered by Phase -1:

- Batch A — QG/host-contention cluster (5 docs) — **RETURNED**
- Batch B — pytest-timeout flaky series (5 docs)
- Batch C — quickmerge/glue-runner/CI infra cluster (6 docs)
- Batch D — ldr-to-main/promote + unified-api-contracts cluster (6 docs)
- Batch E — misc cluster 1 (5 docs)
- Batch F — misc cluster 2 (4 docs)

### Batch A candidate ledger (pre-verification)

**C1 — Doc self-contradiction + codex corroboration (P1, borders P0 — opposing directives on a security posture).**
`ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md:534` — open `[OPERATOR] P0` todo: "RULED
2026-08-06, option (a)... Keep `unified-trading-pm` public and self-hosted; close the fork-PR code-execution hole
instead of moving CI or making the repo private" (re-affirmed "STILL the current exposure" at L557, dated
2026-08-08) — contradicted by the SAME doc's own L610-620 + Deferred table L702: "Complete the public-repo
migration — DONE 2026-08-07... PM's 8 self-hosted runners... fully deregistered" — and by
`/codex/07-security/self-hosted-runner-security-posture.md:80-89`: "the `unified-trading-pm` exposure is RESOLVED
(2026-08-07)... Standing invariant going forward: never register a self-hosted runner pool on a public repo." The
open todo prescribes the OPPOSITE remediation path (harden fork-PR-approval, keep self-hosted) from what the doc's
own later content + codex show was actually adopted (full revert to `ubuntu-latest`). Not a missed-flip (the todo
as literally written was never executed — a different, superseding fix shipped instead) — needs STEP 4 verify then
resolution (likely: close/annotate L534 as superseded-by-the-actual-remediation, not flip to `[x]`).

**Missed flips**: none found (checked all 12 open todos across the 5 docs for hidden-completion evidence).

**Archive candidates**: none new — `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` has 0 open
checkboxes but is correctly `archive_exempt: true` (set 2026-08-09, real prose-only open work) — verified-clean,
not a finding.

**H1 — Systemic truncated na-eligibility-audit entries (P2).** 4 of 5 docs have a `na-eligibility-audit 2026-08-18
(ci tranche)` Progress Log entry cut off mid-sentence at EOF: `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md:626`,
`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md:826`,
`ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md:880`,
`deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md:213`. Identical truncation shape
across 4 independently-authored docs suggests a systemic bug (likely a length cap) in the 2026-08-18 na-eligibility-
audit ci-tranche run's own append path, not 4 coincidental typos — the stated verdict lands before each cutoff, so
no routing decision was lost. `deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md` has NO
2026-08-18 entry at all (possible coverage gap in that run, or correctly out of scope — undeterminable from this
doc alone). Cannot safely reconstruct the cut-off text (would be fabrication) — route only, do not attempt a fix.

**H2 — Stale/missing `last_updated` frontmatter, 5 of 5 docs (P3, mechanically fixable).**
`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (2026-08-03, 15d stale),
`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (field absent),
`ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` (field absent),
`deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md` (2026-08-03, 15d stale),
`deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md` (2026-08-06, 11d stale) — all should
bump to match each doc's own actual last Progress Log entry date.

### Batch D candidate ledger (ldr-to-main/promote + unified-api-contracts cluster) — pre-verification

**F1 — Missed flip (P2), HARD evidence.** `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md:276-279`'s
sole remaining blocking todo ("start/hold a genuinely clean 60-consecutive-minute window... before declaring this
incident `resolved`") was independently confirmed satisfied 5 days before this audit —
`ci_satellite_ao_dispatch_batch13_2026_08_13.md:143-166`: "✅ CONFIRMED CLEAN 2026-08-14... the 60-min clean-window
bar is met — exceeded ~168x over" — but that same entry explicitly deferred reconciling the source doc's checkbox
to `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`, and a grep of that finalize doc for the topic returns
zero hits — the deferral was never honored.

**F2 — Contradiction (P2).** `github_actions_operator_gated_followups_2026_07_17.md:266`'s operator table asserts
"MTDS promote PR #601 blocked on QG failure... Real, current" — contradicted by live `market-tick-data-service` git
log showing 5 successful `chore(promote): LDR → main` merges dated TODAY (2026-08-19: `27b1cc20`, `85b4b63d`,
`77319e07`, `c0bd7382`, `cada444d`, tags through `v0.144.20`), plus an earlier successful promote-merge already
recorded 2026-08-07 in the sibling doc. Caveat from the hunter: PR #601's literal open/closed state by number was
not independently verified — only the headline "blocked" claim, which the live promote history contradicts.

**F3 — Truncation instances (P2) — ADD TO EXISTING FILED DOC, do not re-file.** A dedicated issue doc
`plans/active/issues/na_eligibility_audit_marker_text_silently_truncated_2026_08_19.md` was filed TODAY (before this
run) already tracking this exact truncation-bug pattern (2 instances, explicitly notes "this run did not do a
corpus-wide sweep"). Batch D found 2 MORE instances: `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md:343`,
`silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md:235`.

**F4 — Stale `last_updated`, 2 docs (P3).** `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md:44`
(2026-08-07, 11d stale), `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md:30` (2026-07-17, never
once bumped across ~9 dated passes).

**F5 — Cross-tranche stuck item (P3, informational only — not ci-tranche's to fix).**
`github_actions_operator_gated_followups_2026_07_17.md:410-420`'s slot-concurrency revisit-date is 17 days overdue;
the doc's own na-eligibility-audit passes explicitly decline it as "cross-tranche (ao, not ci)" — structurally
nothing in the normal ci-tranche cadence will ever revisit it. Worth an `ao`-tranche pickup, not actionable here.

**Missed flips (other)**: none beyond F1. **Contradictions (other)**: none beyond F2. **Codex-alignment /
archive-candidates**: none — checked `ci-cd-flow.md`, `ci-alerting.md`, `self-hosted-runner-security-posture.md`
against this batch's claims, no drift either direction; no doc in this batch is a zero-checkbox candidate. Docs
`promote_pr_non_supersession_after_greeks_service_fix_2026_08_18.md`,
`unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md`, and its `_finalize` pair
are CLEAN — no findings (finalize-plan coverage explicitly verified as complete, no gap).

### Batch B candidate ledger (pytest-timeout flaky series) — pre-verification

**Finding A — Codex-alignment drift (P2), codex is stale/incomplete.**
`/codex/06-coding-standards/quality-gates.md`'s "Sanctioned timeout overrides" section documents only
`IGNORE_TIMEOUT`/`PYRIGHT_TIMEOUT` — zero hits for `PYTEST_TIMEOUT` (measured: `grep -c`), despite this entire
~2,900-line 5-doc incident chain living on `PYTEST_TIMEOUT_SECONDS`/`PYTEST_TIMEOUT`/`PYTEST_TIMEOUT_RETRIES`
(confirmed live in `base-library.sh`/`base-service.sh`, used across 7+ repos). This is an ADDITION of missing
content, not a single-fact substitution — does not cleanly qualify for the narrow mechanical-codex-staleness
auto-apply carve-out (STEP 5.f2 requires no invented content); routing rather than auto-fixing.

**Finding C — Truncation instances (P1, systemic) — ADD TO EXISTING FILED DOC.** 2 more confirmed instances (1 new,
1 re-confirmed) beyond the already-filed `na_eligibility_audit_marker_text_silently_truncated_2026_08_19.md`:
`pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md:149` (new, literal EOF),
`pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md:565` (re-confirmed, doc grew, now literal EOF).
Also re-confirmed still-present: `..._continued_2026_08_02.md:985` (mid-word truncation, NOT at EOF — a later entry
was appended after it, meaning the bug can leave a truncated entry stranded mid-document, not just at file end).
Strong pattern: every truncation instance across Batches A/B/D is a `na-eligibility-audit 2026-08-18 (ci tranche)`
entry, always on an `assigned_vm: NA` doc — worth naming this correlation explicitly when updating the filed issue.

**Finding D — Stale `last_updated`, 4 of 5 docs (P3).** All 4 dated pytest-timeout docs stale by 2-14 days (3 of
them "corrected" once already by plan_reconciler 2026-08-16 and already drifted stale again); doc5 has no
`last_updated` field at all.

**Finding E — Missing cross-links (P3).** Doc1's `related:`/`context_scope` lists none of its 3 continuation docs,
despite all 3 naming doc1 as parent — a reader following only doc1's own frontmatter has no path to ~30 more
escalation entries in the chain.

**Finding F — Line-cap proximity warning (P3, informational).** doc1 (998/1000 lines) and doc2 (989/1000 lines) are
within single-digit lines of the HARD cap — both already self-document redirecting new entries elsewhere, so not a
current violation, but flagged for the next writer.

**Finding G — Stale path in a CODE comment (P3, out of plan_reconciler's `plans/**`-only write scope).**
`features-service/scripts/quality-gates.sh:~43` cites `plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`,
which has since moved to `plans/archive/2026_08/...` — a code-comment fix, not a plan-doc fix; noting only, not
actioned by this run.

**Missed flips / contradictions**: none found beyond what's noted above (doc3's todo1 bundling a landed-tracking
clause with a not-yet-resolved recurrence clause is a wording nit, not a hidden-evidence violation). **Archive
candidates**: none — every doc has ≥1 genuinely open checkbox.

### Batch F candidate ledger (misc cluster 2) — pre-verification

**F-A — Missed flip (P2), HARD evidence, wrong-repo-guessed.**
`git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17.md:77-82`'s 2 open todos ("locate the
ahead-count computation, likely agent-orchestrator... fix it to compare against each repo's own tracked branch")
already shipped — 6 days BEFORE this doc was even filed — but in a different repo than the todos guessed:
`unified-trading-pm/scripts/dev/slot-git-status-report.sh:312-326` (commit `b92d9ba52fe`, 2026-08-11, "fix:
unified-trading-ci false git-health ahead warning" — special-cases `unified-trading-ci` → `main`). Doc stays
`status: open`, `assigned_vm: planning` (AO-dispatchable) with no Progress Log entry acknowledging the fix exists —
risks a future AO dispatch re-investigating an already-fixed mechanism in the wrong repo.

**F-B — NEW finding (P2), not covered by any existing todo — the real mechanism behind THIS run's own boot-time
false-positive nudge.** This run's own slot-1 boot heartbeat received `unified-trading-pm: AHEAD=1 unpushed` when
the repo was actually clean seconds later. Doc 1's diagnosed mechanism does NOT explain this (PM carries no
`integration_branch` override in `workspace-manifest.json`, so comparing against `live-defi-rollout` is correct for
PM — doc 1's fix, even where it applies, wouldn't have prevented this). The REAL gap: `agent-orchestrator/server/worker_liveness/_git_alerts.py:532-534`
(`maybe_nudge_on_red_repos`) fires on the "ahead" branch with **zero age/sustain threshold** — unlike the sibling
`dirty` branch 3 lines later (`age_s > 3600`) and `behind` branch (`age_s > 600`) in the SAME function, and unlike
the sibling Slack-paging function `maybe_alert_git_staleness`, which enforces a 90-min sustain
(`GIT_RED_SUSTAIN_S`) for its own "ahead" case. A momentary ahead=1 reading (e.g. a commit landing slightly before
its push in the normal two-pass ship flow) can fire this in-session nudge on the very next ~5-min-cadence tick —
only a 30-min re-nudge throttle exists (doesn't stop the FIRST fire). Needs a new todo (not a fix to doc 1's
existing ones): add an age/sustain threshold to the "ahead" branch of `maybe_nudge_on_red_repos`, mirroring its own
sibling branches.

**F-C — Contradiction (P2).** `unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md:13-14` claims
"THREE independent, un-synced registries" answer "what branch does repo X integrate on" (enumerates A/B/C only) —
but `slot-git-status-report.sh:313-315` is a 4th, independently hand-maintained copy of the same fact (the one F-A
just fixed) that the doc's problem statement and its still-open `[OPERATOR]` registry-collapse decision don't
account for. Currently correctly populated (no live bug), but the doc undercounts its own problem scope.

**F-D — Hygiene (P3).** Doc 1's `context_scope` cites only the read-only consumer
(`agent-orchestrator/server/worker_liveness/_git_alerts.py`), never the actual fix site
(`slot-git-status-report.sh`) — should be updated once F-A/F-B are resolved.

**F-E — Hygiene (P3, low-confidence, not misleading).** `post_cutover_silent_assumption_sweep_2026_07_23.md` has 2
stale line-citations (content unchanged, just line-shifted from doc growth) — `:139-142` cites
`reconcile_release_tags.py:51` (now L72), `:307-308` cites `ci-cd-flow.md:1413` (now L1456).

**Missed flips (other) / contradictions (other)**: none beyond F-A/F-C. **Archive candidates**: none — all 4 docs
have genuine open work (doc 3's `sequential: true` gating is correctly holding, verified against its own 8
na-eligibility-audit passes).

### Batch C candidate ledger (quickmerge/glue-runner/CI infra cluster) — pre-verification

**G1 — Contradiction (P2), rationale-accuracy not reclassification.**
`quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`'s sole open todo (step 3, broaden the
branch-check) repeatedly cites (2026-08-09/10/18 audit entries) "gated on `scripts/quickmerge.sh` ownership
contention with `ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s own todo 1" as its blocker — but
`plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md:118-126` shows that contention was
CLEARED 2026-08-09 ("BOTH blockers cleared, ready for batch-5 extraction... `scripts/quickmerge.sh` is free
again"), and batch4 itself is `status: complete`, archived. The recommended follow-up ("batch-5 or later should
extract it") was never executed — batch5/6/15 all just carry the stale framing forward. The UNDERLYING disposition
is correct (step 3 genuinely still undone — live-verified `qg-environment.sh` still checks only `branch == "main"`,
its own header comment says "deliberately" pending this doc) — this is a stale REASON-CITED, not a wrong verdict.
Fix: correct the doc to cite only the still-live "awaiting operator design ruling" reason, drop the stale
"ownership contention" framing.

**G2/G3 — Hygiene (P3).** `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`'s `context_scope`
lists `quickmerge.sh` but not `qg-environment.sh` (now the actual single-source-of-truth per its own header
comment); stale `last_updated` in `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`
(2026-08-07 vs. Progress Log through 2026-08-18) and `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`
(2026-08-14 vs. 2026-08-18 audit entry, low confidence — several sibling docs have no `last_updated` field at all,
so this may not be a corpus-wide convention).

**G4 — FYI, not a contradiction (P3).** 2 open todos in different docs ask the identical design question
(standing repo-visibility/runner-registration-drift alert on `unified-trading-ci`) — already self-aware
cross-referenced, just worth merging into one tracked item when ruled on.

No missed flips, no zero-checkbox/archive candidates, no codex-alignment drift found in either direction (checked
`/codex/08-workflows/ci-cd-flow.md`'s sentinel/retry + `unified-trading-ci` hosting sections against live code —
both match exactly).

### Batch E candidate ledger (misc cluster 1) — pre-verification

**F1 — HEADLINE FINDING (P1), AUTO-RESOLVE class (provable, hunter RAN the check).**
`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md:307-309`'s sole open todo ("investigate why
`update-dependency-version.yml`'s primary cascade has been dormant since 2026-06-28") is **empirically false as of
today** — live `gh run list` (run by the hunter this session) shows the cascade firing multiple times/day across
all 3 of the doc's own named sample repos (`execution-service`: 3 successful runs today alone; `agent-orchestrator`:
5 successful runs today; `ml-service`: successful runs through today), all `conclusion: success`. Likely resumed as
a side effect of `post_cutover_silent_assumption_sweep_2026_07_23.md`'s F2 fix (semver-agent retarget, already in
this doc's own `context_scope`) — the hunter did not trace the exact resuming commit, so cite "resumed, cause not
definitively traced" rather than asserting the F2 causal chain as certain. Needs STEP 4 re-verification (re-run
`gh run list` myself) then close/re-scope the todo — doc may become a genuine archive candidate.

**F2 — Contradiction (P3, low-medium confidence, low stakes — todo already closed either way).**
`build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md:103-104` ("the semver-agent... is dead,
deliberately") vs. `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md:8` (semver-agent running
successfully fleet-wide, filed 2 weeks later) — hunter's own hedge: these likely describe two different payloads
(semver-agent's `version-bump` dispatch vs. `quality-gates-v2.yml`'s separate `qg-passed` dispatch, the latter
confirmed live to still omit `version`) — the doc's core technical claim is independently true, only the causal
attribution is in tension. Low priority given the todo is already closed/not-a-bug.

**F3 — Codex-alignment drift (P2), codex is stale.** `ci_alert_failure_resolution_linkage_2026_08_16.md` shipped a
new `streak_start_sha` Firestore field + alert-linkage mechanism (`unified-trading-ci@7000ac0`) whose cited SSOT
`/codex/04-architecture/ci-alerting.md` has zero mentions of it (measured: `grep -c`). No todo in the source doc
covers documenting this — needs a new todo, not use of the mechanical-staleness carve-out (this is missing
content, not a single-fact correction).

**F4-F7 — Hygiene (P2-P3).** Stale/missing `last_updated` in 4 docs
(`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`,
`build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` — field absent entirely,
`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`,
`ff_pull_fleet_drift_rca_2026_08_11.md` — mildest, 1 week).

**F8 — Truncation, ADD TO EXISTING FILED DOC + SCALE UPDATE (P2, important).** 3 more confirmed instances
(byte-verified via `tail -c`, not just Read-tool artifacts):
`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md:296`,
`build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md:229`,
`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md:344`. **Critically**: a corpus-wide grep this
session found **116 docs** carrying a `"na-eligibility-audit 2026-08-18"` entry — the already-filed
`na_eligibility_audit_marker_text_silently_truncated_2026_08_19.md` currently cites only 2 instances and its own
todo 3 (corpus-wide sweep) hasn't run — the true blast radius is almost certainly much larger than currently
tracked. This scale finding needs to reach that issue doc directly.

**F9 — Possible NA misclassification (P3, low confidence, flagged not asserted).**
`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` todo 7 (wire `consumer-qg-gate` into
`pin_branch_protection_rulesets.py`) reads as bounded/deterministic single-repo script work — the exact shape
na-eligibility-audit's own rubric flags as "simply defaulted to NA." The hunter could not see the 2026-08-18 pass's
own reasoning for keeping it NA (right where the entry truncates, per F8) — worth a second look, not confidently
asserting a reclassification.

**Missed flips**: none (F1 is a different class — an open todo falsified by EXTERNAL reality, not by the doc's own
text). **Zero-checkbox/archive candidates**: none currently — `digest_drift_sweep...` may become one once F1
resolves.

## Coverage (hunters / batches / docs) — final

All 6 hunter batches returned, 31/31 dispatched docs covered (5+5+6+6+5+4). Combined with the 7 docs Phase -1
investigated directly = **all 38 writable docs** in this run's 56-doc tranche read in full this run (18 were
grace-protected, read-only context). Phase -1 additionally closed out 2 predecessor findings docs. Approx combined
hunter spend: ~1.3M tokens across 6 batches, ~122 tool calls, wall-clock ~8-11 min per batch (parallel).

**Phase 5.9 NO-MISS LEDGER**: `routed_to_operator` = 1 blocked question (`BLK-ed97af99`, covering 2 codex-alignment
findings) == `parked_in_issue_doc` = 1 (same 2 findings, filed in this doc's own Doc-drift section) — **balanced,
1 == 1**. `agent_skips`: 0 sub-agents returned a skip this run (all 6 hunters completed their full assigned batch;
no verifier sub-agents were spawned — all STEP-4 verification was done inline by the orchestrator with fresh tool
calls, per this doc's own `model: sonnet`/effort-max frontmatter authorizing inline verification for a candidate
count this size). Every count above is a fresh measurement from this run's own tool calls, not carried forward
from a hunter's unverified claim.

## Plans not reached

None — full tranche coverage achieved (38/38 writable docs read; 18/18 grace-protected docs correctly left
untouched). 3 minor P3 hygiene classes were consciously NOT pursued to completion this pass (see Filed section's
"Not pursued this pass" note) — that is a scoping choice, not a coverage gap; every doc was read, not every
cosmetic finding within an already-read doc was individually corrected.

## Verification (STEP 4)

_(populated after hunters return)_

## Flips verified

All 7 priority candidates independently re-verified this session (fresh tool calls, not trusting hunter citations
alone) and applied:

1. `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md` — 60-min clean-window bar todo: **DONE**,
   re-verified `ci_satellite_ao_dispatch_batch13_2026_08_13.md:163` + confirmed the finalize doc's deferred
   reconciliation never happened (0 grep hits) — flipped directly.
2. `git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17.md` — both original todos: **DONE**,
   re-verified `unified-trading-pm@b92d9ba52fe` reachable + the `unified-trading-ci` special-case still live in
   `slot-git-status-report.sh:312-326` — flipped, plus filed a NEW todo 3 for a genuinely separate live gap (see
   Contradictions/NEW-findings below).
3. `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` — dormant-cascade todo: **DONE**, re-ran
   `gh run list --workflow=update-dependency-version.yml` myself — 3 successful runs today alone, cascade
   unambiguously not dormant. Doc now 1/1 done — zero-checkbox archive candidate (see Archive candidates below).
4. `ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` — self-hosted-runner-security `[OPERATOR]`
   todo: **DONE on superseding evidence** (not the originally-scoped artifact) — re-verified
   `/codex/07-security/self-hosted-runner-security-posture.md:80-89` states the revert-based remediation is the
   adopted standing posture; the harden-and-keep-self-hosted path this todo scoped was never applied and is now
   moot.

## Contradictions (confirmed + fixed)

1. `github_actions_operator_gated_followups_2026_07_17.md:266` — MTDS-promote-blocked table row: **FIXED**,
   re-verified live `market-tick-data-service` git log (10 successful `chore(promote)` merges in the last 10
   entries, 5 dated today) — struck through with corrected note, historical trail kept per row-9's own pattern.
2. `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md:177-184` — stale "ownership contention"
   blocker citation: **FIXED** (rationale-accuracy correction, not a reclassification) — re-verified
   `plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md:118-126` confirms the contention
   cleared 2026-08-09 and batch4 is archived/`status: complete`; corrected to cite only the still-live
   design/judgment-call reason for staying NA.

**NEW finding filed (not a contradiction, no existing todo covered it)**: `git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17.md`
todo 3 — `agent-orchestrator/server/worker_liveness/_git_alerts.py:532-534`'s "ahead" branch has zero age/sustain
threshold, unlike its sibling `dirty`/`behind` branches in the same function and unlike the sibling Slack-paging
function's 90-min sustain for the same "ahead" case — independently confirmed via direct code read (lines 500-560).
This is the real mechanism behind this run's own boot-time false-positive git-status nudge.

## Doc-drift

**Codex-alignment drift — routed, not auto-applied (adds new content, not a single-fact substitution; doesn't
qualify for the STEP 5.f2 mechanical-staleness carve-out):**

1. `/codex/06-coding-standards/quality-gates.md`'s "Sanctioned timeout overrides" section documents only
   `IGNORE_TIMEOUT`/`PYRIGHT_TIMEOUT` — zero mentions of `PYTEST_TIMEOUT_SECONDS`/`PYTEST_TIMEOUT`/
   `PYTEST_TIMEOUT_RETRIES` despite a ~2,900-line 5-doc incident chain living on exactly those knobs (confirmed
   live in `base-library.sh`/`base-service.sh`, used across 7+ repos). Recommend adding a row for each.
2. `/codex/04-architecture/ci-alerting.md` has zero mentions of `streak_start_sha`, a new Firestore field +
   alert-linkage mechanism shipped `unified-trading-ci@7000ac0` per
   `ci_alert_failure_resolution_linkage_2026_08_16.md`. Recommend documenting the shipped mechanism.

Both routed via `/blocked` (STEP 6) with a recommendation, not applied autonomously.

**STEP 8 update**: operator answered `BLK-ed97af99` = **A** (author both now) at 2026-08-19T19:13:29Z. Applied
both same-turn: `/codex/06-coding-standards/quality-gates.md`'s "Sanctioned timeout overrides" section now
documents `PYTEST_TIMEOUT_SECONDS`/`PYTEST_TIMEOUT`/`PYTEST_TIMEOUT_RETRIES` (cited against
`base-library.sh`/`base-service.sh` + the shipping commit `unified-trading-pm@52a85d6c7`);
`/codex/04-architecture/ci-alerting.md` gained a new "Failure↔resolution linkage — `streak_start_sha`" section
documenting the mechanism shipped `unified-trading-ci@7000ac0`, cited against
`ci_alert_failure_resolution_linkage_2026_08_16.md` (read in full before writing, not paraphrased from the hunter's
summary alone).

## Hygiene fixes

_(populated after verification)_

## Filed

1. `unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md`'s `[OPERATOR]` P3 registry-collapse todo
   (L206-208) — annotated with the 4th un-synced registry Batch F found (`slot-git-status-report.sh`), so the
   eventual operator decision accounts for it. Not a flip (still genuinely a design call), a scope correction.
2. `na_eligibility_audit_marker_text_silently_truncated_2026_08_19.md` todo 3 (corpus-wide sweep) — 11 more
   confirmed instances + the 116-doc scale finding folded in (see Phase -1/hunter sections above; also see
   `unified-trading-pm@19deb57bef`).
3. 2 codex-alignment gaps routed via `BLK-ed97af99` (see Doc-drift above) — durably filed in this doc's own
   Doc-drift section per STEP 6(b) (no separate issue doc needed, the run-findings doc IS the durable record).

**Not pursued this pass (time/scope, honestly reported per Phase 5.9(e), not silently dropped):**
- ~15 stale/missing `last_updated` frontmatter fields across the docs this run's hunters read (per-batch detail
  above). Multiple docs show a "corrected once by plan_reconciler 2026-08-16, already stale again by 2026-08-19"
  pattern — manual re-correction each run is whack-a-mole; better served by an automated fix (e.g. a hook that
  bumps `last_updated` on any commit touching a doc's own Progress Log) than by this run chasing each instance by
  hand. Recommend as a follow-up design question, not filed as a todo here (would just be another instance of the
  same whack-a-mole).
- Batch B Finding E (`pytest_timeout_60s_flaky_under_contention_2026_07_29.md`'s `related:`/`context_scope`
  missing its 3 own continuation docs) — cosmetic navigation gap, low value relative to remaining run budget.
- Various P3 `context_scope` gaps noted per-batch above (e.g. `quickmerge_environment_autodetect...`'s missing
  `qg-environment.sh` entry) — left for the next `context-scout` pass, which owns this maintenance routinely.

## Archive candidates (operator review)

- `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` — **ARCHIVED this pass**. Flipping its sole
  open todo (see Flips verified) left it 0-open/all-done, unlocked, non-grace. The pre-commit `check_archive_candidates`
  hook correctly caught this as a hard gate before it would let the commit through. Ran the 6-step ritual: `status:
  archived` + `resolved_by:` set, `git mv` to `plans/archive/issues/`, repointed 2 structured referrers
  (`ci_consolidated_closeout_2026_07_25.md:128` markdown link, `ci_satellite_ao_dispatch_batch15_2026_08_16.md`
  ×2 — a `context_scope`-style leading-slash ref and a backtick-quoted no-slash prose ref, both caught and
  fixed), left the remaining referrers untouched (13 already-archived docs = historical narrative;
  `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s bare-filename prose mention; the 2 machine-generated
  `ci_master` index/report files, left for the next natural regen).

## Refuted (dropped by verify)

None this run — every candidate that reached STEP 4 verification (7 priority items) was independently confirmed
with fresh tool-call evidence and applied. No hunter finding was found to be wrong on re-check.

## Coverage (hunters / batches / docs)

_(populated after run)_

## Plans not reached

_(populated after run, if applicable)_

## Progress Log

- **2026-08-19 (dispatch agt-f212cb, slot 1)**: Run started. FF'd PM + 30 sibling repo clones (all clean except
  `unified-trading-ci`, transient network slowness on first attempt, succeeded on retry — not a real FF-clean
  failure). Ran `run_hygiene_sweep.sh --ci` (1 hard failure: corpus-wide `assigned_vm:NA` ratchet, not ci-tranche
  specific — `/na-eligibility-audit`'s disjoint remit; 1 soft warning). Phase -1 reconciled both prior ci findings
  docs to genuine closure (archived both, PM@b30280613a). Computed fresh tranche inventory (56 docs) + grace set (18
  docs). This doc created to capture the run.
- **2026-08-19 (same dispatch, continued)**: STEP 3 dispatched 6 parallel hunter batches over the 31 non-grace docs
  not already covered by Phase -1; all 6 returned with substantial candidates. STEP 4 independently re-verified 7
  priority candidates with fresh tool calls (git log/show, gh run list, direct code reads, codex reads) — all 7
  confirmed, none refuted. STEP 5 applied all 7: 6 fixes across 6 docs (PM@fcb094b7c6) + 1 archival
  (`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`, made archive-ready by its own flip, same
  commit) + folded 11 new truncation-bug instances + a 116-doc scale finding into the already-filed
  `na_eligibility_audit_marker_text_silently_truncated_2026_08_19.md` (PM@19deb57bef) + 1 scope-correction
  annotation on `unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17.md`'s registry-collapse todo.
  STEP 6 routed 2 codex-alignment gaps via `BLK-ed97af99` (trust-mode's own carve-out: codex edits always route,
  never auto-apply, regardless of evidence strength). Branch was extremely hot throughout (double-digit
  branch-drift retries on nearly every commit — 8-10 sibling tranche/epic reconciler dispatches active
  same-day); every commit eventually landed clean via the standard pull-rebase-autostash recovery, no data lost,
  confirmed via `git merge-base --is-ancestor` after each. Moving to STEP 7/8.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
