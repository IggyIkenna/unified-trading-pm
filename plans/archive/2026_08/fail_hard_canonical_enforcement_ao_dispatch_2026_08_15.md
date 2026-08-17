---
doc_type: plan
title: Fail-hard canonical enforcement — sanity check, then implement Gaps 1-2
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A, round 2) — run the quick
  operator/engineering sanity check §5b flagged as recommended-but-not-yet-confirmed, then
  proceed with implementing Gap 1 (derivative/chain-bundle column gate) and Gap 2 (TARDIS-only
  column==manifest-by-construction) from fail_hard_canonical_enforcement_design_2026_07_20.md.
  Gap 3 already shipped. **CANCELLED 2026-08-16 — both implementations turned out already shipped one day earlier
  via `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`; this doc was never dispatched.**
status: complete
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [cefi, canonicalization, fail-hard, manifest]
related:
  [
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 2, 2026-08-16"
locked_by:
context_scope:
  [/plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md]
locked_since:
resolved_by:
---

# Fail-hard canonical enforcement — sanity check, then implement Gaps 1-2

## Todos

- [x] ✅ [REVIEW] P2. **CANCELLED — moot, target already shipped (2026-08-16).** Run the "quick operator/engineering
      sanity check" §5b of `fail_hard_canonical_enforcement_design_2026_07_20.md` flagged as
      recommended-but-not-yet-confirmed, before either implementation todo below proceeds. Nothing left to
      sanity-check — both implementations below were already shipped, reviewed, and QG-green a day BEFORE this doc
      was drafted. (repo: unified-api-contracts)
- [x] ✅ [WRITER] P2. **CANCELLED — already shipped elsewhere (2026-08-16 reconciliation,
      `cefi_satellite_ao_dispatch_batch19_2026_08_13_finalize.md`, slot 21).** Implement Gap 1's resolution (§5b): add
      a row-level column-value gate for bundle-shaped writers (derivative/chain-bundle column gate). **SHIPPED
      market-tick-data-service@c1626c5dbd** (+ prerequisite UAC ID_FORM-oracle widening
      `unified-api-contracts@8b81dd78bb`), 2026-08-15, via `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` — one
      day BEFORE this doc was drafted. The 2026-08-16 na-eligibility-audit follow-up Q&A round that created this doc
      didn't catch the prior-day shipment. See the source doc's own reconciled checkbox for full evidence. No code
      shipped by this doc (none needed).
- [x] ✅ [WRITER] P2. **CANCELLED — already shipped elsewhere (2026-08-16 reconciliation,
      `cefi_satellite_ao_dispatch_batch19_2026_08_13_finalize.md`, slot 21).** Implement Gap 2's resolution (§5b):
      make the live/on-chain lane's manifest key a deterministic function instead of relying on TARDIS-only
      column==manifest-by-construction. **SHIPPED market-tick-data-service@d518aca80d**, 2026-08-15, via
      `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` — same prior-day-shipment gap as Gap 1 above. No code
      shipped by this doc (none needed).

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 2, operator ruling)**: extracted from
  `fail_hard_canonical_enforcement_design_2026_07_20.md`. Gap 3 already shipped (checked in source doc); Stage 2
  schema v10 `instrument_id_form` backfill authorization was not separately ruled this round and stays with the
  source doc as still-open.
- **2026-08-16 (reconciliation, `cefi_satellite_ao_dispatch_batch19_2026_08_13_finalize.md`, slot 21)**: while
  reconciling batch19's shipped Gap 1/Gap 2 evidence back into `fail_hard_canonical_enforcement_design_2026_07_20.md`,
  found this doc duplicates already-shipped work — both implementations landed via
  `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` on 2026-08-15, one day before this doc's 2026-08-16 na-eligibility-audit
  drafting session (which never claimed/dispatched any of these 3 todos — Progress Log shows only the drafting
  entry). All 3 todos cancelled as moot; archiving this doc + its finalize in the same commit, zero open todos, never
  dispatched.
