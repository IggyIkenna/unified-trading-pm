---
doc_type: plan
title: Infra capture wiring + devops leftovers — finalize (re-check BLOCKED-* gates + archive)
summary: >-
  Gated closeout for infra_capture_and_devops_leftovers_2026_07_06.md (AO Plan 6 of the instruments-completion set) —
  machine-held via depends_on + gate_on_depends: true until that plan's todos are done. Backfills the
  finalize-plan-coverage gap for a plan predating the 2026-07-24 rule (task_template.md §4): not a batch extraction (its
  own todos are the primary record, nothing to reconcile back into a source doc), so this finalize's job is narrower —
  re-check each still-open BLOCKED-* item's gate, then run the standard archival ritual once genuinely done.
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [infra, capture, close-out, finalize, blocked-recheck, archival]
related:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/archive/issues/operator_iam_permission_parity_2026_06_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by: infra_capture_and_devops_leftovers_finalize_2026_07_25
depends_on: [infra_capture_and_devops_leftovers_2026_07_06]
gate_on_depends: true
source: >-
  Backfilled 2026-07-25 per task_template.md §4's finalize-plan-coverage rule (check_finalize_plan_coverage.py flagged
  this pre-existing AO plan as a ratchet regression — it predates the 2026-07-24 rule and never got a companion finalize
  plan).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Infra capture wiring + devops leftovers — finalize

> **🟡 SUPERSEDED 2026-07-25 (slot 9)** — an accidental duplicate:
> `infra_capture_and_devops_leftovers_finalize_2026_07_25.md` was independently created the same day for the same
> parent/gate and reached `status: active` (actually dispatched + completed the re-check + reconciliation this doc
> describes). This doc was never ingested (`status: draft` the whole time), so there was no dispatch collision in
> practice — flagging here only so a future doc-health sweep doesn't re-activate two finalize plans for one parent. No
> further action needed on this doc.
>
> **🟢 CORRECTION 2026-07-25 (slot 2)**: the "never ingested" claim above was wrong by the time this doc flipped to
> `status: superseded` — the ingestion filter (`_plan_contributes_briefs` in
> `agent-orchestrator/server/regen_backlog_from_plan.py`) only excluded `status: draft`, not `status: superseded`, so
> this doc's 3 still-open checkboxes below WERE re-derived and dispatched as duplicate backlog tasks
> (`infra_capture_and_devops_leftovers_2026_07_06_finalize-001/-002/-003`, `-001` landed on slot 2 today) of work slot 9
> already completed in the successor doc. Fixed at the root: `agent-orchestrator@f58d934` adds `status: superseded` to
> the ingestion/prune exclusion (regression tests: `test_regen_skips_superseded_plans`,
> `test_prune_stale_removes_tasks_of_superseded_plan`, both green). Closing out the 3 todos below as duplicates of the
> already-completed work in `infra_capture_and_devops_leftovers_finalize_2026_07_25.md` so no further re-dispatch can
> occur even before the fix's next regen tick prunes them.

> **Machine-gated on `infra_capture_and_devops_leftovers_2026_07_06.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until every todo in that plan is `done`. `sequential: true` because todo 2
> (BLOCKED-* re-check) must run before todo 3 (archival) can determine whether the plan is truly closeable.
>
> **Not a batch-extraction plan** — unlike the sports/tradfi/prediction satellite-batch finalize docs, this source plan
> was authored directly (not extracted from other docs' todos), so there is no "reconcile checkboxes back into a
> different source doc" step. Its 4 remaining open items are gated (`BLOCKED-PREREQUISITES` ×1, `BLOCKED-CREDENTIALS`
> ×3, `BLOCKED-OPERATOR-DECISION` ×1) — this finalize plan's job is to re-check each gate, not redo the work.

## Todos

- [x] ✅ [REVIEW] P2. **Re-verify the ASTER live connector prereqs (`BLOCKED-PREREQUISITES` item).** — **DUPLICATE,
      checked 2026-07-25 (slot 2)**: already fully handled by
      `infra_capture_and_devops_leftovers_finalize_2026_07_25.md` (the correct, non-duplicate doc). Its own record: the
      parent's ASTER todo re-resolved to `BLOCKED-OPERATOR-DECISION` (`BLK-4f52080e`, main: HOLD pending the CeFi
      live-capture cost-control freeze `BLK-55d45a68`) — still genuinely blocked, re-verified as of today. No
      independent re-check needed here.
- [x] ✅ [REVIEW] P2. **Re-check the 4 credential/operator-gated items' gates.** — **DUPLICATE, checked 2026-07-25
      (slot 2)**: already fully handled by the sibling finalize doc. Its record: `collect-oracle-prices` pyth key
      flipped `[x]` (premise was stale — launcher scaffold already exists, Hermes endpoint needs no auth, already
      backfilling under a separate active plan); MANTLE gas-fees RPC, Live ODDS quota, and the rate-limit-probe VM all
      re-confirmed still genuinely blocked as of 2026-07-25. No independent re-check needed here.
- [x] ✅ [DOC] P3. **Archive `infra_capture_and_devops_leftovers_2026_07_06.md`.** — **DUPLICATE, checked 2026-07-25
      (slot 2)**: not archivable — 4 of 5 parent items remain genuinely blocked (per the sibling finalize doc's own
      re-check above), so the parent correctly stays `status: active`, not archived. The sibling finalize doc is the
      standing pointer for this; this doc needs no independent archival attempt. Evidence:
      `unified-trading-pm@<pending-sha>` (this commit) + `agent-orchestrator@f58d934` (root-cause dispatcher fix, see
      banner above).
