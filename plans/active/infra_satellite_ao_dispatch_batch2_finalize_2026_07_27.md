---
doc_type: plan
title: Infra satellite AO dispatch batch 2 — finalize (reconcile source-doc checkboxes + archive)
summary: >-
  Gated closeout for infra_satellite_ao_dispatch_batch2_2026_07_27.md, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24). Once each of the 9 batch todos is done, reconciles the
  corresponding checkbox back into its true source doc (mdps_features_deadcode_consolidation_2026_07_20.md,
  candle_feature_canonical_path_divergence_2026_07_20.md, backfill_smoke_write_path_canonical_audit_2026_07_20.md) and
  checks whether any source doc now has zero open todos and is itself an archival candidate.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, na-eligibility-audit, finalize, batch-2]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [infra_satellite_ao_dispatch_batch2_2026_07_27]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
supersedes:
superseded_by:
source: >-
  Authored alongside its parent batch, /na-eligibility-audit interactive dry-run 2026-07-27, per the standing
  finalize-plan-coverage rule (every assigned_vm:planning plan needs a gated finalize twin).
---

# Infra satellite AO dispatch batch 2 — finalize

> **Machine-gated on `infra_satellite_ao_dispatch_batch2_2026_07_27.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue this plan's todo until the parent's 9 todos are done.

## Todos

- [ ] [DOC] P2. **Reconcile source-doc checkboxes + check archival eligibility for all 3 sources.** Once the parent
      batch's 9 todos are `[x]`: (1) for each of `issues/mdps_features_deadcode_consolidation_2026_07_20.md`,
      `issues/candle_feature_canonical_path_divergence_2026_07_20.md`,
      `issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md` — close the corresponding checkbox(es) this batch
      extracted, citing the parent batch todo's actual commit sha (re-verify it exists, do not trust the batch doc's own
      copy of the evidence line). (2) For each source doc, grep its remaining `- [ ]` items: if the closures above left
      zero open todos, that source doc is now itself an archival candidate — run the standard 6-step archival ritual on
      it (migrate DEFERRED → banner → codex-alignment check → corpus-wide referrer-path fixup → clear lock), not just
      the checkbox flip. If any source doc still has genuine judgment-call items open (expected for at least
      `mdps_features_deadcode_consolidation_2026_07_20.md`, which keeps todos 1-3/8 NA per the na-eligibility-audit's
      own verdict), leave it `status: active`, `assigned_vm: NA` — do not archive prematurely. (3) Re-check the
      `## Deferred` item in the parent batch (the `tradfi_backfill_throughput_followups_2026_07_24.md` hold-back): if
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s combined todo has landed by the time this finalize runs,
      confirm its own "Done when" clause actually flipped those checkboxes — if not, file a follow-up rather than
      silently trusting it landed. (4) Run the standard 6-step archival ritual on THIS finalize plan + its parent once
      all of the above is done. **Done when**: every one of the 3 source docs' checkbox state matches reality (closed
      with a verified commit sha, or explicitly left open with a re-confirmed judgment-call reason), any source doc left
      with zero open todos has been through the 6-step archival ritual, and this finalize plan + its parent are
      themselves archived.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
