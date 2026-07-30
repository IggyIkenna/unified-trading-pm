---
doc_type: plan
title: Instruments satellite AO dispatch batch 1 — finalize (reconcile source-doc checkboxes + archive)
summary: >-
  Gated closeout for instruments_satellite_ao_dispatch_batch1_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 5 batch todos is done, reconciles the
  corresponding checkbox back into honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md and checks
  whether it now has zero open todos and is itself an archival candidate.
status: complete
nature: process
asset_group: [cefi, defi, tradfi, prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [instruments, ao-dispatch, na-eligibility-audit, finalize, batch-1]
related:
  [
    /plans/active/instruments_satellite_ao_dispatch_batch1_2026_07_27.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: [instruments_satellite_ao_dispatch_batch1_2026_07_27]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Authored alongside its parent batch, /na-eligibility-audit interactive dry-run 2026-07-27, per the standing
  finalize-plan-coverage rule (every assigned_vm:planning plan needs a gated finalize twin).
---

# Instruments satellite AO dispatch batch 1 — finalize

> **🗄️ ARCHIVED 2026-07-29** — gate satisfied: parent's 5 todos all done, reconciled into the source doc, this
> finalize's own todo IS the archival action, now done. Archived per
> /codex/12-agent-workflow/plan-completion-and-archival-discipline.md.

> **Machine-gated on `instruments_satellite_ao_dispatch_batch1_2026_07_27.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue this plan's todo until the parent's 5 todos are done.

## Todos

- [x] ✅ [DOC] P2. **DONE 2026-07-29.** (1) Closed the 5 corresponding checkboxes in
      `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`, each citing the parent batch
      todo's evidence (todo 1: BYBIT/BINANCE-DELIVERY spot-check; todo 2: deployment-api@554cde9 +
      deployment-ui@8f6c4bc; todo 3: DERIBIT live breakdown pull, OPTION healthy; todo 4: MTDS/reference-data conflation
      audit, POLYGON fixed via `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`, FRED never conflated; todo 5:
      writer-fix scope, already venue-agnostic, no code needed). (2) Re-grepped the source doc: exactly 8 `- [ ]` items
      remain, matching the 2026-07-27 snapshot (Finding 1 leaf re-verify, phantom OPTION removal, CEFI resharding
      design, BINANCE-DELIVERY tooltip, DERIBIT-COMBO retirement, market_metadata axis move, breakdown-link rename,
      historical manifest backfill) — all still genuinely judgment/operator-gated, none silently resolved elsewhere;
      source doc left `status: active`/NA, NOT archived. (3) Ran the standard 6-step archival ritual on this finalize
      plan + its parent (banner, status→complete, moved to `plans/archive/2026_07/`, no new codex contract needed, no
      other live referrer paths found needing a fix). — `unified-trading-pm` (this batch).
