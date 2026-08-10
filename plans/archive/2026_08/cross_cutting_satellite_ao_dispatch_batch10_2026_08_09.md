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
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [e2e-testing, market-tick-data-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-10, satellite-docs, manifest-master, cefi, census]
related:
  [
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch10_2026_08_09_finalize.md,
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

> **ARCHIVED 2026-08-09** — sole todo done; census result recorded in
> `data_pipeline_reconciliation_skill_2026_07_20.md`'s Progress Log. Archived via its gated finalize twin
> (`cross_cutting_satellite_ao_dispatch_batch10_2026_08_09_finalize.md`).

> **Status: complete.** Single independent todo — no `sequential`/`gate_on_depends` needed.

## Todos

- [x] ✅ [DATA] P2. **Measure the historical per-venue non-canonical row count for the 8 CeFi live-spot venues fixed in
      `cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30.md`** (archived, resolved) — **2026-08-09,
      `unified-trading-pm` (this batch, docs-only).** Source: `data_pipeline_reconciliation_skill_2026_07_20.md`'s
      `[DATA] P2` "Measure the historical per-venue non-canonical row count..." todo. That issue's code-level fix
      (BINANCE/COINBASE/OKX/UPBIT/BITFINEX/BITGET/BYBIT/KRAKEN-SPOT now emit canonical `SPOT_PAIR` + `BASE-QUOTE` ids)
      shipped without ever measuring the SIZE of the pre-fix non-canonical population — the census that originally found
      the class only measured the aggregate `instrument_type=spot` lowercase axis (4,923 rows across ALL cefi), never
      the id-FORM/hyphenation dimension per venue. Ran a manifest-driven, filtered, column-pruned read of the
      consolidated cefi availability index (`venue`/`instrument_type`/`instrument_id`/`capture_status` only,
      `venue in <8 venues>` — single-walk-exempt, no GCS listing), then `is_canonical_instrument_id()` (id-FORM oracle)
      against each row's `instrument_id` (the plain `instrument_type`-axis census alone reads zero — the manifest
      structural column was already `SPOT_PAIR` everywhere; the defect lives in the id/filename STRING, so id-form was
      the only way to see it). **Result: 2,197 rows confirmed non-canonical id-form + 6,251 rows with a missing
      `instrument_id` (undetermined, legacy rows predating that manifest column) out of 1,957,165 total SPOT_PAIR rows
      across the 8 venues** — full per-venue breakdown + sample bad ids + method written to
      `data_pipeline_reconciliation_skill_2026_07_20.md`'s Progress Log (the number this todo exists to produce).
      Measurement only, per scope — no repair executed. Repo: e2e-testing (skill invocation) / market-tick-data-service
      (if a repair follow-on is later filed — NOT this todo's scope).

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
- **2026-08-09 (cont.)**: sole todo done. Ran the id-form census (manifest-driven, single-walk-exempt) against the 8
  target venues' `SPOT_PAIR` rows in the prod cefi manifest — 2,197 confirmed non-canonical `instrument_id` rows + 6,251
  undetermined (missing `instrument_id`, legacy) out of 1,957,165 total. Full per-venue table + method + sample bad ids
  written to `data_pipeline_reconciliation_skill_2026_07_20.md`'s Progress Log. Read-only measurement; no repair
  executed (out of this todo's scope). Checkbox flipped; this batch is now ready for its gated finalize twin
  (`cross_cutting_satellite_ao_dispatch_batch10_2026_08_09_finalize.md`) to reconcile the source doc + archive.
