---
doc_type: issue
title:
  "Parked findings from the 2026-08-06 /ag-closeout-audit infra run (2 new observations: cloud_run_traffic_pin
  false-complete [x] leaves the Slack-routing half unclaimed; batch4/5 lack finalize twins. NO batch8 drafted — every
  net-new orphan's work is operator-gated, time-gated, or already claimed by defi batch9. Linkage fixed 2→0)"
summary: >-
  The 2026-08-06 `/ag-closeout-audit infra` run (scheduled daily run, slot 8, dispatch agt-42686f) re-verified all 3
  carried-forward `[OPERATOR]` findings live (F6 ao_self_pull mistag — 4th day; F10 batch3 blank `assigned_vm` — 5th
  day; F11 missing stash-backup bundle — 3rd day; all unchanged) and confirmed the 4-batch draft backlog (F14) still
  sits at 4 (batch4 6 days old, combined 7 todos). Classified all 6 net-new candidates since the 2026-08-04 baseline (57
  members vs 50): 2 operator-gated (ci_pipeline_speed_and_cost_redesign — sole open todo "Do NOT roll out until
  understood"; cloud_run_traffic_pin — prose-gated (a)(b)(c) inside a checked todo), 2 operator-directed/time-gated
  (self_hosted_runner_public_repo_revert, shared_ci_workflow_repo_extraction — the latter actively executing, Waves 1-2
  shipped today), 1 escalation-tracked self-dispatched (client_reporting_api_promote_wedge), 1 now COVERED by the defi
  tranche's same-day batch9 draft (defi_gas_fees gsutil-hang DIAG — conflict check: clear duplicate, not re-drafted).
  NEW findings: F15 (cloud_run_traffic_pin's checked todo contains explicit NOT-DONE (a) Slack webhook secret [operator]
  + (b) bridge deploy + (c) canary verify — zero open checkboxes means nothing dispatches them; operator-gated chain)
  and F16 (batch4/batch5 lack finalize twins; single-todo carve-out keeps the QG gate green, draft the twins when
  flipping those batches active). NO batch8 drafted this run — the tranche's bottleneck is now operator review
  throughput, not extraction. Linkage fix shipped: added the 2 infra-tagged unlinked docs (cloud_run_traffic_pin,
  smoke_matrix) to the closeout doc's Sources → `check_ag_closeout_linkage.py` infra orphans 2→0 (corpus-wide 87-vs-69
  regression tracked separately in `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ag-closeout-audit, parked-findings, batch-approval-backlog, linkage, false-complete]
related:
  [
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_04.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch5_2026_08_01.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch6_2026_08_02.md,
    /plans/active/infra_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/active/issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md,
    /plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
author: slot-8 (ag_closeout_auditor, infra tranche, dispatch agt-42686f)
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_04.md,
    /plans/active/issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md,
    /plans/archive/issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md,
    /plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
source: >-
  `/ag-closeout-audit infra` run 2026-08-06 (ag_closeout_auditor scheduled worker, slot 8, dispatch agt-42686f,
  one-shot). Phase 0 re-derived the covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (13
  covering docs, 57 members vs 50 on 2026-08-04, 4 never-cited — all 4 net-new). Ran the skill's iterative-drain step 1
  (re-checked all carried-forward findings live) before a targeted Phase 1 direct-read of the 6 net-new candidates
  (matching this tranche's established delta-read precedent; the last comprehensive baseline sweep was 2026-08-03). Ran
  the Phase 3 conflict check against the one batch candidate surfaced (defi_gas_fees DIAG items) — resolved as
  clear-duplicate against `defi_satellite_ao_dispatch_batch9_2026_08_06.md` (same-day defi draft), so no infra batch8
  was drafted. Applied the skill-prescribed linkage remedy for the 2 infra-tagged unlinked docs (cloud_run_traffic_pin →
  Track 2, smoke_matrix → Track 3) in `infra_consolidated_closeout_2026_07_25.md` and re-ran
  `check_ag_closeout_linkage.py` (infra 2→0).
---

# Parked findings — 2026-08-06 `/ag-closeout-audit infra` run

## New findings this run

### 15. [WORKER REC] `cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md` — checked todo contains explicit "NOT DONE (needs operator) (a)(b)(c)"; the Slack-delivery half of the alert wiring is unclaimed (false-complete `[x]`)

All 3 of that doc's todos are `[x]`, but todo 1's own text carries: "NOT DONE (needs operator): (a) store Slack
#ci-failures webhook URL in Secret Manager as `cloud-monitoring-slack-ci-failures-webhook`, (b) deploy the bridge as a
Cloud Run service with a push subscription on the Pub/Sub topic, (c) trigger a canary rollback against a disposable/UAT
service to verify end-to-end Slack delivery." The doc is `assigned_vm: planning` + `status: open` (self-dispatched) but
has **zero open checkboxes** — the AO backlog derives tasks from open checkboxes, so nothing is actually dispatching
(b)/(c), and the drift check (todo 2, shipped) only makes the condition detectable, not paging. Net state: the alert
policy + bridge code + drift check all shipped; the actual Slack page is still not wired.

- **Taxonomy**: operator-gated chain — (a) needs the operator/credential (webhook secret); (b)+(c) are worker-doable
  bounded items but are gated on (a) landing.
- **Options**: A (recommended): operator stores the webhook secret (a), then (b)+(c) fold into the next infra batch (or
  a follow-up dispatch) as one combined todo — the code + topic + policy all already exist. B: operator completes
  (b)+(c) interactively in the same session as (a) (it's ~30 min of Cloud Run deploys + a canary trigger). C: leave
  as-is and mark the doc's todo 1 as genuinely incomplete (un-check it) until (a) lands — the current `[x]` is a
  false-complete.

### 16. [DOCS] `infra_satellite_ao_dispatch_batch4_2026_07_31.md` and `batch5_2026_08_01.md` have NO finalize twins (both single-todo drafts)

`check_finalize_plan_coverage.py`'s single-todo carve-out keeps this from being a QG violation today, but per
`task_template.md` §4 every AO-dispatch batch needs a `depends_on: [<batch-slug>] + gate_on_depends: true` finalize twin
— batch1/3/6/7 all have theirs (batch6/7's twins exist even though those batches are still draft). If either batch grows
past 1 todo, or is flipped `active`, the missing twin becomes a real coverage gap with no reconcile-and-archive vehicle.

- **Taxonomy**: time/operator-gated (the twin can't usefully run until the batch is approved + done).
- **Options**: A (recommended): draft both finalize twins (`status: active`, gate-held) when the operator reviews
  batches 4/5/6/7 together (finding 14's single-pass recommendation) — one 10-minute addition to that review. B: the
  next audit run drafts them once either batch flips active. C: leave as-is (gate stays green via the carve-out).

### 17. [WORKER REC] NO infra batch8 drafted this run — every net-new orphan's open work is operator-gated, time-gated, operator-directed, or already claimed by defi batch9

Phase 1 classified all 6 net-new docs; Phase 3's conflict check ran against the only batchable-looking candidate (the
defi_gas_fees `[DIAG]` items) and resolved it as a **clear duplicate**:
`defi_satellite_ao_dispatch_batch9_2026_08_06.md` (drafted same-day by the concurrent defi-tranche worker) already
merges the gsutil-hang root-cause + relaunch + purge completion into one todo citing both source docs. Per the conflict
protocol, no competing infra todo was drafted. The remaining net-new docs are non-batchable:
ci_pipeline_speed_and_cost_redesign (sole open todo explicitly "Do NOT roll out until this is understood", on-VM
diagnosis), cloud_run_traffic_pin ((a)(b)(c) — finding 15), self_hosted_runner (todo 24 operator-directed live-infra;
todo 20 time-gated), shared_ci_workflow_repo_extraction (actively-executing operator-directed migration, Waves 1-2
shipped today, `[OPERATOR]` items on other machines), client_reporting_api (escalation record, fleet-recovery-tracked).
**The tranche's binding constraint is now operator review throughput**: 4 drafted batches (7 todos) awaiting one review
pass, oldest 6 days — more extraction drafts would not close any work.

- **Taxonomy**: operator-gated (review backlog) — this is a recommendation to the operator, not a worker action.
- **Options**: A (recommended): single operator pass over batches 4/5/6/7 (7 todos, all P2/P3, all pre-conflict-checked)
  — clears the queue and re-enables extraction next run. B: operator declines/supersedes the backlogged batches and
  directs the remaining work differently. C: no action — the audit keeps reporting the same carried items (accurate
  signal, growing age).

## Carried forward from 2026-08-04 (re-verified live this run)

All 4 items carried into the 08-04 doc remain **OPEN, unchanged**:

1. **`issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`'s `asset_group` mistag** (finding 6,
   originally flagged 2026-07-31, **4th consecutive day**) — re-checked: line 23 still reads
   `asset_group: [infrastructure]`, not `[ao]`. Tranche-level `BLOCKED-OPERATOR-DECISION` with 3 unresolved options (A:
   authorize the tranche that CAN see it to retag; B: corpus-wide non-sharded retag pass; C: change `owning_tranche()`
   fallback). Not this skill's to fix directly (owning-tranche-writes-only rule).
2. **`infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s `assigned_vm` flip** (finding 10, **5th consecutive day**) —
   re-checked via direct raw read: line 39 still `assigned_vm:` with no value (`cat -A` confirms `assigned_vm:$`, YAML
   null), not `planning`. The `[BACKEND] P3` todo remains genuinely undispatched. Not re-applied (flipping `assigned_vm`
   on an already-`status: active` plan needs fresh operator confirmation each time).
3. **`issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md`'s missing stash-backup bundle**
   (finding 11, **3rd consecutive day**) — re-checked via a fresh
   `find /home/ubuntu -iname "*agentwork-sports-2026-07-13*"` and
   `find /home/ubuntu -iname "*instruments-service-agentwork*"` sweep: zero hits, still genuinely absent anywhere on
   this host. Operator-only: confirm durable relocation vs. unrecovered loss.
4. **Draft-batch review backlog** (finding 14, **5th day**) — re-verified: `infra_satellite_ao_dispatch_batch4` (draft,
   6 days old), `batch5` (draft, 5 days), `batch6` (draft, 4 days; 1 of 2 todos resolved-elsewhere), `batch7` (draft, 2
   days, 3 todos) — combined 7 todos, all still `status: draft`, zero flipped since drafting.

Findings 12 (`self_dispatched_orphan_count` tooling suggestion) and 13 (`CITE_RE` hardening design +
`repo_scripts_governance_audit_2026_06_18.md` L208/L213) carry forward unchanged — neither was re-scoped this run.

## This run's Phase 1 classification (6 net-new candidates, all created 2026-08-05/06)

- **`ci_pipeline_speed_and_cost_redesign_2026_08_05.md`** — `orphaned_never_touched`-technical, but correctly,
  permanently non-batchable: its sole open todo (warm git-object cache for JIT-ephemeral runner checkouts) carries an
  explicit "Do NOT roll out to additional pools until this is understood" constraint, a deployed-but-no-op mystery
  needing on-VM diagnosis, and 2 documented live incidents from touching this runner infra — operator/live-infra
  judgment, not worker-determinable (matches the 2026-08-06 na-eligibility-audit's KEEP-NA ruling). ci-owned content
  (dual tag `[ci, infrastructure]`).
- **`issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md`** — `orphaned_partial_coverage` (finding
  15): all checkboxes `[x]` but todo 1's prose explicitly leaves (a)(b)(c) NOT DONE; nothing dispatches them.
  Infra-primary (tag `[infrastructure]` only). Linkage-fixed this run (added to closeout Track 2).
- **`issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`** —
  `orphaned_never_touched`-technical as of the infra covering set, but the open `[DIAG]`/`[DATA]` work is now claimed by
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md` (same-day defi draft — conflict check resolved as clear-duplicate,
  no competing infra todo drafted). The `[DATA]` relaunch/purge is operator-gated (delete-safety + VM launch); the
  `[DATA]` P2 doc-update is gated on purge completion. Dual tag `[defi, infrastructure]`, defi owns the extraction.
- **`self_hosted_runner_public_repo_revert_2026_08_05.md`** — `orphaned_never_touched`-technical, but the 2 open todos
  are non-batchable: todo 24 (PM's own revert — operator-directed per-file live-infra work, documented "not
  AO-dispatched") and todo 20 (billing/load re-measurement — time-gated). ci-owned content (dual tag
  `[ci, infrastructure]`).
- **`issues/client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md`** — self-dispatched (planning/open)
  escalation record, zero todos; resolution (merge_conflict wall for #646) is in flight with the fleet-level CI
  recovery, not batch machinery. ci-owned content (promotion mechanics; dual tag `[ci, infrastructure]`).
- **`shared_ci_workflow_repo_extraction_2026_08_06.md`** — `orphaned_never_touched`-technical, but permanently
  non-batchable: a large, actively-executing operator-directed multi-machine migration (Waves 1-2 shipped today,
  `[OPERATOR]` items for Harsh's laptop + human-planning VM, deletion/SSOT-write steps sequenced last). Matches the
  too-large-or-risky taxonomy verbatim. ci-owned content (dual tag `[ci, infrastructure]`).

**Ledger**: 3 new parked findings this run (15, 16, 17) + 3 entries written above — **balanced** (also 4 carried-forward
items re-verified, all still open, 0 resolved; 6 net-new docs classified; 1 linkage fix shipped — not counted as parked
findings since each produced either a durable entry here or a shipped fix).

## Todos

- [x] ✅ [OPERATOR] P1. **RESOLVED (verified by na-eligibility-audit 2026-08-07, infra tranche)** — direct read of
      `infra_satellite_ao_dispatch_batch3_2026_07_30.md` line 39 confirms `assigned_vm: planning` (no longer blank).
      **Re-apply `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s `assigned_vm` flip correctly** (finding 10, was
      FIFTH consecutive day open) — set line 39 to `assigned_vm: planning` (currently blank), then verify the
      `[BACKEND] P3` todo actually reaches the live AO backlog (live-backlog dispatch itself not independently
      re-verified this pass — the frontmatter fix is the mechanical fact this audit checks).
- [x] ✅ [OPERATOR] P1. **CLOSED 2026-08-08 (na-eligibility-audit, round7 RECLASSIFY sweep) — RESOLVED 2026-08-07,
      operator accepted the loss.** `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md`
      is now archived with `status: resolved` and `resolved_by:` recording the operator's ruling ("unrecovered loss,
      accepted, no further investigation. Both the source directory and the stash-backup bundle are confirmed genuinely
      absent; the operator declined recovery."). Original text preserved below for record. Was: **Investigate the
      missing stash-backup bundle** (finding 11, third consecutive day confirmed absent) — confirm whether
      `instruments-service-agentwork-sports-2026-07-13-stashes.bundle` (67.8 MB) was relocated to a durable location or
      represents an unrecovered loss. Update
      `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` with the outcome either way.
- [x] ✅ [OPERATOR] P1. **CLOSED 2026-08-08 (na-eligibility-audit, round7 RECLASSIFY sweep) — RULED 2026-08-07 (verified
      by `ag_closeout_audit_infra_parked_2026_08_07.md`'s own todo).**
      `issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` is now live `asset_group: [ao]` (confirmed
      via direct `grep '^asset_group:'` this pass — was `[infrastructure]`). The operator ruled option B+C combined
      ("make it correct"): retagged both live instances of this mistag class (this doc +
      `ao_deepseek_provider_model_telemetry_mislabeled_2026_08_06.md`) and added authoring-time guidance to
      `plans/active/task_template.md`'s `asset_group` field so the pattern stops recurring. Original text preserved
      below for record. Was: **Resolve `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`'s `asset_group`
      mistag** (finding 6, fourth consecutive day) — pick one of the 3 parked options (authorize tranche retag /
      corpus-wide non-sharded pass / `owning_tranche()` fallback change).
- [x] ✅ [OPERATOR] P2. **RESOLVED 2026-08-06 (governance sweep, commit `unified-trading-pm@de1d795de1`).** All 4
      batches reviewed and flipped `status: active`. The "missing finalize twins for batch4/batch5" sub-note is moot —
      `check_finalize_plan_coverage.py` passed with 0 violations post-activation, confirming both correctly qualify for
      the single-todo carve-out (`task_template.md` §4) and need no separate finalize plan. Original text preserved
      below for record. **Review + approve/decline the 4 backlogged drafted infra batches** (findings 14/17) —
      `infra_satellite_ao_dispatch_batch4` (1 todo), `batch5` (1), `batch6` (2, 1 resolved-elsewhere), `batch7` (3) —
      combined 7 todos, all pre-conflict-checked; oldest 6 days.
- [x] ✅ [OPERATOR] P2. **KEEP-NA-STALE — already re-tracked (verified by na-eligibility-audit 2026-08-07, infra
      tranche)** — `issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md` now carries a real open
      `## Follow-ups` checkbox (`- [ ] [INFRA] P2. Store the Slack #ci-failures webhook...`) covering this exact
      (a)/(b)/(c) work, and that doc is `assigned_vm: planning` (already self-dispatched/AO-visible) — closing here to
      avoid two open asks for the same work; the live tracking location is that doc's Follow-ups section, not this one.
      **Complete the traffic-pin Slack routing** (finding 15, option A recommended) — store the
      `cloud-monitoring-slack-ci-failures-webhook` secret (a); then dispatch/execute the bridge deploy (b) + canary
      verify (c), which become a clean batch candidate once (a) lands.
- [ ] [DOCS] P3. **Consider a `self_dispatched_orphan_count` addition to `generate_ag_closeout_audit_candidates.py`**
      (finding 12, carried). Design/tooling-priority call, not urgent.
- [ ] [DOCS] P3. **Scope + conflict-check the 2 flagged batch-era candidates** (finding 13, carried: `CITE_RE` hardening
      design; `repo_scripts_governance_audit_2026_06_18.md`'s L208/L213) before any future run drafts them.

## Progress Log

- **2026-08-06** — `/ag-closeout-audit infra` run (autonomous mode, scheduled daily run, slot 8, dispatch agt-42686f).
  Re-derived the candidate set (13 covering docs, unchanged; 57 members, up from 50 on 2026-08-04; 4 never-cited, all
  net-new). Re-checked all carried-forward findings live (0 resolved, 4 still open, unchanged). Direct-read all 6
  net-new docs (targeted delta read, matching this tranche's established precedent). Phase 3 conflict check: the sole
  batchable-looking candidate (defi_gas_fees `[DIAG]`) resolves as clear-duplicate against the same-day defi batch9
  draft → **no infra batch8 drafted**. Linkage fix shipped: 2 infra-tagged unlinked docs added to the closeout doc's
  Sources (Track 2: cloud_run_traffic_pin; Track 3: smoke_matrix) → `check_ag_closeout_linkage.py` infra orphans 2→0.
  **Ledger**: 3 new parked findings + 4 re-verified carry-forwards (all still open) + 6 net-new docs classified
  - 1 linkage fix, 3 entries written above — balanced.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, stale items — closed 2 of 4 open todos with
  hard evidence: (1) finding 11's stash-backup-bundle investigation — the source doc is now archived,
  `status: resolved`, operator ruling recorded (2026-08-07, unrecovered loss accepted); (2) finding 6's `asset_group`
  mistag — `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` is now live `asset_group: [ao]`, confirmed
  by direct grep this pass, per the operator's 2026-08-07 B+C ruling recorded in the successor
  `ag_closeout_audit_infra_parked_2026_08_07.md`. Left findings 12/13 (`[DOCS] P3` design/scoping calls) open — checked
  against today's operator-Q&A cheat sheet, no precedent applies to either. Doc stays NA.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) -- replaced the batch9/hub-only pair with
  the two oldest still-open carried findings' direct targets (finding 11's stash-clone doc, finding 6's ao_self_pull
  mistag doc), kept the predecessor doc + this run's own headline finding-15 target + the tranche hub.
- **context-scout 2026-08-07 (batch 7 verification pass)**: added `generate_ag_closeout_audit_candidates.py` (now 6
  entries) -- 2 of the doc's 5 open todos (findings 12/13: `self_dispatched_orphan_count` addition, `CITE_RE` hardening)
  are specifically about hardening/extending that exact script, named explicitly in both findings' own text, and it was
  missing from the prior pass's list.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, stale items — closed 2 of 6 open todos with hard
  evidence: (1) the batch3 `assigned_vm` flip is genuinely done (direct read confirms line 39 = `planning`); (2) the
  traffic-pin Slack-routing item is already re-tracked as a real open checkbox in an `assigned_vm: planning` doc
  (`cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md`'s `## Follow-ups`) — closing here avoids a duplicate
  open ask. Left the remaining 4 items OPEN and UNCHANGED: the asset_group-mistag (finding 6) and stash-backup-bundle
  (finding 11) items are also restated in the successor `ag_closeout_audit_infra_parked_2026_08_07.md`, but restatement
  in a newer doc is not evidence of resolution — closing them here on that basis alone would manufacture a
  false-complete, the exact anti-pattern this doc's own finding-15 was filed to catch. The 2 `[DOCS] P3`
  tooling-suggestion items (12/13) are genuine open design calls, also correctly left open. Doc stays `assigned_vm: NA`
  (its remaining content is real operator-judgment work, not a mis-default).
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
