---
doc_type: plan
title:
  Cross-cutting satellite AO batch 10 — manifest_master bounded residual (8-venue CeFi non-canonical-id census)
  extracted from the round11 2026-08-09 sweep
summary: >-
  Tenth AO-dispatch batch for the cross-cutting tranche, produced by the round11 2026-08-09 RECLASSIFY +
  satellite-extraction sweep. Pulls 1 bounded item out of `data_pipeline_reconciliation_skill_2026_07_20.md`
  (`manifest_master`, the operator-designated standing `/data-pipeline-reconciliation` skill reference doc): measure the
  historical per-venue non-canonical row count for the 8 CeFi live-spot venues whose code-level fix already shipped in
  `cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md` (archived, resolved) — that fix stopped NEW rows
  from being wrong but never measured the SIZE of the pre-fix non-canonical population, a number needed to size any
  historical backfill/repair decision. This doc's own 2026-08-03 na-eligibility-audit pass already called this item
  "bounded, worker-determinable... a future dedicated pass could reclassify that one item on its own" — this is that
  pass. The source doc's other open item (sports orphan back-fill citation) was a stale-checkbox citation fix, verified
  and corrected directly in the source doc in this same sweep, not extracted here. The source doc itself stays
  `assigned_vm: NA` (operator-designated standing reference surface,
  `autonomous_session_operator_decisions_2026_07_25.md` entry #10) — only this one item is dispatched.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [e2e-testing, market-tick-data-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-10, satellite-docs, manifest-master, cefi, census]
related:
  [
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch10_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /codex/02-data/reconciliation-census-and-compute-tiers.md,
    /cursor-configs/skills/data-pipeline-reconciliation/SKILL.md,
  ]
source: >-
  round11 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting + ui tranches) — this item was already
  flagged 2026-08-03 by the source doc's own na-eligibility-audit as ready for "a future dedicated pass"; today's pass
  is that dedicated pass.
assigned_role: data_engineering
effort: low
sequential: false
drift_direction: advance-docs
---

# Cross-cutting satellite AO batch 10 (manifest_master) — bounded-item extraction

> **Status: active.** Single independent todo — no `sequential`/`gate_on_depends` needed.

## Todos

- [ ] [DATA] P2. **Measure the historical per-venue non-canonical row count for the 8 CeFi live-spot venues fixed in
      `cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md`** (archived, resolved). Source:
      `data_pipeline_reconciliation_skill_2026_07_20.md`'s `[DATA] P2` "Measure the historical per-venue non-canonical
      row count..." todo. That issue's code-level fix (BINANCE/COINBASE/OKX/UPBIT/BITFINEX/BITGET/BYBIT/KRAKEN-SPOT now
      emit canonical `SPOT_PAIR` + `BASE-QUOTE` ids) shipped without ever measuring the SIZE of the pre-fix
      non-canonical population — the census that originally found the class only measured the aggregate
      `instrument_type=spot` lowercase axis (4,923 rows across ALL cefi), never the id-FORM/hyphenation dimension per
      venue. Run the `/data-pipeline-reconciliation` skill's distinct-value census (§ 3f, `get_axis_value_census`)
      scoped to `asset_group=cefi`, filtered to these 8 venues, comparing `is_canonical_instrument_id()` pre-fix-shape
      vs post-fix-shape row counts — read-only, manifest-driven, no new whole-corpus GCS walk. Done when: a real,
      per-venue non-canonical-row-count number is produced and written back into
      `data_pipeline_reconciliation_skill_2026_07_20.md`'s Progress Log (the number this todo exists to produce), sized
      enough to inform any future historical backfill/repair decision. Repo: e2e-testing (skill invocation) /
      market-tick-data-service (if a repair follow-on is later filed — NOT this todo's scope, measurement only).

## Codex SSOTs

`/codex/02-data/reconciliation-census-and-compute-tiers.md` (the census mechanism this todo invokes),
`/codex/02-data/four-surface-reconciliation-procedure.md` (the skill's core loop).

## Progress Log

- **2026-08-09**: Batch authored via the round11 cross-cutting+ui RECLASSIFY + satellite-extraction sweep. 1 item
  extracted from `data_pipeline_reconciliation_skill_2026_07_20.md` (`manifest_master`) — already flagged 2026-08-03 by
  that doc's own audit as ready for a dedicated reclassification pass; today's pass is that pass. The source doc's
  sibling open item (sports orphan back-fill) was verified this same sweep to be a stale citation (the referenced
  `estate_orphan_assessment_2026_07_21.md` todos 1-2 are both already `[x]` DONE 2026-07-22, exact row-count match:
  214,319 + 34,385) and corrected directly in the source doc, not extracted here.
