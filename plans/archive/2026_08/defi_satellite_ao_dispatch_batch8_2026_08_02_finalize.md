---
doc_type: plan
title: DeFi satellite AO batch 8 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch8_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until that plan's todo is done. Mirrors batch1-7-finalize: reconcile the single source doc
  (lst_rate_honest_coverage_2026_07_21.md Phase 3) once the batch-8 todo lands, re-check the 2 Deferred
  classified-but-not-extracted items for whether their blocking condition has since cleared, then archive batch8 via the
  standard 6-step ritual.
status: complete # (was: active) 2026-08-06 archival sweep: all todos [x], no locked_by
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-8, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-05"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/archive/issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch8_2026_08_02]
gate_on_depends: true
source: >-
  `/na-eligibility-audit defi` run 2026-08-02 (autonomous, scheduled na_eligibility_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 8 — finalize

**status: active — gated on batch8's todo via `depends_on` + `gate_on_depends: true`; the dispatcher will not release
these until batch8 is fully done.**

## Todos

- [x] ✅ [DOC] P1. Source-doc reconciliation COMPLETE — batch8's todo landed `[x]` 2026-08-05 (force+skip verified: 54
      canonical parquet files + 56 manifest captured rows to test bucket; skip-leg freshness-cache mechanism confirmed
      wired but can't fire against test bucket). The source doc's Phase-3 `[MTDS] P3` checkbox cannot be PHYSICALLY
      flipped — the doc is 1017L, over the 1000L hard cap, and `check_line_caps.sh`'s marker-only carve-out (operator
      ruling 2026-08-02) explicitly excludes checkbox changes. This is NOT an oversight or gap: the
      `na-eligibility-audit     2026-08-03` marker already records "Phase 3 sample-download superseded by Phase 5's real
      prod force+skip proof," and
      [`lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`](/plans/archive/2026_08/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md)
      carries the ready-to-apply evidence as actionable todos (gated on the `[OPERATOR]` line-cap policy decision in
      [`over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`](/plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md)).
      The batch8 evidence itself is preserved verbatim in batch8's own `[x] ✅` todo. — unified-trading-pm (no code
      change; doc-only reconciliation recorded here and in the cited issue docs).
- [x] ✅ [DOC] P2. Deferred items re-checked: **(a) Composite-venue fold — RESOLVED.** Batch6 shipped
      `market-tick-data-service@13f14b78` (2026-08-01, 5,332/5,332 shards, 0 errors, 324,867 objects + manifest rows).
      The stale-checkbox correction was applied in the `na-eligibility-audit 2026-08-02` run — the issue doc's
      `[DATA] P1` was closed by citation. The sole remaining `[PM] P2` is the **delete-the-legacy-copies phase** only (a
      prod-bucket delete, human-only unless reversibility-qualified per delete-safety-protocol §3a) — a genuinely
      separate, still-valid open item, not something to re-extract. **(b) Catalog-shrink — STILL HELD.** Main's standing
      hold ("hold, apply nothing, await operator go on R3") is live as of 2026-08-02, confirmed by two independent slot
      checks (7 then 5). The `[OPERATOR] P0` decision on R3 relaunch is still unchecked. The vanished-VM forensics
      (`[DATA] P2`) remain gated behind that decision — nothing extractable for a batch9 todo until the operator rules.
      — unified-trading-pm (doc-only; no code change).
- [x] ✅ [DOC] P1. Archive `defi_satellite_ao_dispatch_batch8_2026_08_02.md` via the standard 6-step ritual. **(1)
      DEFERRED items migrated** — both have explicit verdicts above (resolved + still-held), no orphaned prose. **(2)
      Archived banner** — added below. **(3) Codex-alignment** — no new contracts; this was a runtime-verification doc
      (force+skip sample-download), not a pipeline-architecture change. **(4) CLAUDE.md/codex** — no new contract to
      codify. **(5) Referrers updated** — `plans/active/INDEX.md` lines updated to archive paths; issue-doc referrers
      are informational (not execution dependencies) and remain valid pointing at the archived path. **(6) Moved** to
      `plans/archive/2026_08/`. Evidence: batch8 is now at
      [`/plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md`](/plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md).
      — unified-trading-pm.

## Progress Log

- 2026-08-02 (scheduled `na_eligibility_auditor`, tranche=defi, autonomous): Drafted alongside batch8, both
  `status: active`, gated on batch8's todo via `depends_on` + `gate_on_depends: true`. No work started — waiting on
  batch8's todo to land.
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (4 entries).
- **slot-7 (data_engineering) 2026-08-05**: All three todos completed in one session. Todo 1 (source-doc
  reconciliation): batch8's force+skip verification is `[x] ✅` since 2026-08-05 (54 canonical parquet files + 56
  manifest captured rows to test bucket, AAVE oracle + Chainlink + Pyth surfaces verified; skip-leg mechanism confirmed
  wired). The source doc's Phase-3 checkbox cannot be physically flipped — the doc is 1017L (over the 1000L hard cap)
  and the marker-only carve-out excludes checkbox changes. The effective reconciliation is already captured by the
  `na-eligibility-audit 2026-08-03` marker (noting Phase 3 is superseded) and the findings doc with ready-to-apply
  todos. Todo 2 (Deferred items): composite-venue fold confirmed resolved (batch6, 2026-08-01); catalog-shrink confirmed
  still held (main's standing hold live, operator R3 decision pending). Todo 3 (archive batch8): 6-step ritual executed
  — batch8 moved to `plans/archive/2026_08/`, INDEX.md referrers updated. This finalize plan itself is now fully checked
  and eligible for archival (all 3 todos `[x]`, no `locked_by`).
- **context-scout 2026-08-05**: refreshed context_scope (4 entries) -- fixed stale batch8 path (moved to
  plans/archive/2026_08/ by this doc's own todo 3, was still pointing at the deleted plans/active/ path).
