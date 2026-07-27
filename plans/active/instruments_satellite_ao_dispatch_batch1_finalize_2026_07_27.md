---
doc_type: plan
title: Instruments satellite AO dispatch batch 1 — finalize (reconcile source-doc checkboxes + archive)
summary: >-
  Gated closeout for instruments_satellite_ao_dispatch_batch1_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 5 batch todos is done, reconciles the
  corresponding checkbox back into honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md and checks
  whether it now has zero open todos and is itself an archival candidate.
status: active
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

> **Machine-gated on `instruments_satellite_ao_dispatch_batch1_2026_07_27.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue this plan's todo until the parent's 5 todos are done.

## Todos

- [ ] [DOC] P2. **Reconcile source-doc checkboxes + check archival eligibility.** Once the parent batch's 5 todos are
      `[x]`: (1) in `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`, close the 5
      corresponding checkboxes this batch extracted, citing each parent-batch todo's actual commit sha (re-verify it
      exists, do not trust the batch doc's own copy of the evidence line). (2) Grep the source doc's remaining `- [ ]`
      items: as of 2026-07-27 it has 8 genuine judgment-gated items expected to remain open (Finding 1 leaf re-verify,
      phantom OPTION removal, CEFI resharding design, BINANCE-DELIVERY tooltip, DERIBIT-COMBO retirement,
      market_metadata axis move, breakdown-link rename, historical manifest backfill) — do not archive while any of
      these remain genuinely open; re-verify each is still actually gated (not silently resolved elsewhere) rather than
      assuming the 2026-07-27 snapshot still holds. Only if ALL open items (the 5 extracted here plus the 8
      judgment-gated ones) are closed does the doc become an archival candidate — run the standard 6-step archival
      ritual only then. (3) Run the standard 6-step archival ritual on THIS finalize plan + its parent once step (1) is
      done, regardless of the source doc's own archival status (the batch's own completion is what gates this plan, not
      the source doc's). **Done when**: `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`'s
      checkbox state matches reality (5 closed with verified commit shas, remaining items re-confirmed still genuinely
      gated or flagged if not), and this finalize plan + its parent are themselves archived.
