---
doc_type: issue
title: 15 of 16 migrate_*_2026_07*.py executors lack PROGRESS.json checkpoint — SPOT preemption resumes from zero
summary: >-
  Full census of the market-tick-data-service/scripts/migrate_*_2026_07*.py family (16 scripts found, 15 missing the
  PROGRESS.json/record_vm_progress checkpoint). Only migrate_cefi_content_instrument_id_catalogue_2026_07_17.py carries
  the pattern. The 3 scripts flagged in the 2026-07-29 P3 census have since been deleted; 2 NEW scripts have been added
  since, so the gap is growing, not closing. 10 date-loop scripts can adopt record_vm_progress directly; 5 non-date
  scripts need a different object-index checkpoint. None are currently in active multi-hour SPOT campaigns, so each is a
  tracked P2 follow-up todo rather than an inline fix.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [infra, spot-vm, preemption, checkpoint, migration, audit]
created: 2026-08-04
assigned_vm: planning
parent_epic: infrastructure_master
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
resolved_by: ""
locked_by: ""
source:
  [
    "slot-12 audit of migrate_*_2026_07*.py family, task tradfi_satellite_ao_dispatch_batch5-008",
    "/plans/archive/issues/mtds_chain_bundle_migration_no_progress_checkpoint_2026_07_27.md (prior P3 census, resolved)",
  ]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
    /plans/archive/issues/mtds_chain_bundle_migration_no_progress_checkpoint_2026_07_27.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
---

# 15 of 16 `migrate_*_2026_07*.py` executors lack PROGRESS.json checkpoint

## What I found

Full census of `market-tick-data-service/scripts/migrate_*_2026_07*.py` (16 scripts found; 1 already has the pattern, 15
missing):

| #   | Script                                                                            | Date-loop? | Status                        |
| --- | --------------------------------------------------------------------------------- | ---------- | ----------------------------- |
| 1   | `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`                      | yes        | ✅ HAS checkpoint (reference) |
| 2   | `migrate_aster_cefi_defi_bucket_2026_07_13.py`                                    | yes        | ❌ MISSING                    |
| 3   | `migrate_cefi_dated_perps_margin_marker_2026_07_09.py`                            | yes        | ❌ MISSING                    |
| 4   | `migrate_cefi_tardis_filename_canonical_2026_07_17.py`                            | yes        | ❌ MISSING                    |
| 5   | `migrate_dex_pool_symbol_shape_2026_07_09.py`                                     | yes        | ❌ MISSING                    |
| 6   | `migrate_legacy_gas_fees_venue_2026_07_30.py`                                     | yes        | ❌ MISSING (NEW, post-census) |
| 7   | `migrate_live_sanitized_stem_to_canonical_2026_07_20.py`                          | yes        | ❌ MISSING                    |
| 8   | `migrate_prediction_trades_legacy_bundle_2026_07_28.py`                           | yes        | ❌ MISSING (NEW, post-census) |
| 9   | `sports/k1k2_casing_revert_2026_07_27/migrate_sports_casing_revert_2026_07_27.py` | yes        | ❌ MISSING                    |
| 10  | `sports/league_id_relocation/migrate_sports_casing_2026_07_22.py`                 | yes        | ❌ MISSING                    |
| 11  | `sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`       | yes        | ❌ MISSING                    |
| 12  | `migrate_onchain_perp_perpetual_canonical_2026_07_08.py`                          | no         | ❌ MISSING                    |
| 13  | `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py`                       | no         | ❌ MISSING                    |
| 14  | `migrate_tradfi_manifest_itype_semantic_relabel_2026_07_27.py`                    | no         | ❌ MISSING                    |
| 15  | `migrate_tradfi_manifest_usd_lin_2026_07_18.py`                                   | no         | ❌ MISSING                    |
| 16  | `migrate_tradfi_single_leg_product_root_lin_2026_07_09.py`                        | no         | ❌ MISSING                    |

**Growth**: the 2026-07-29 P3 census (in the now-archived source issue doc) found 3 scripts, all missing, all since
deleted. 2 NEW scripts have been added since (`migrate_legacy_gas_fees_venue_2026_07_30.py`,
`migrate_prediction_trades_legacy_bundle_2026_07_28.py`) — both also missing. The gap is growing, not closing.

**Reference pattern** (in the one script that has it): `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`
(lines 83, 516-575): import `record_vm_progress` from `unified_trading_library.manifest_writer._vm_progress`, track
per-day remaining files with a `Counter`, call `record_vm_progress(day)` when every file for a day completes (gated on
`apply` — dry-run must never advance the resume frontier). SSOT: `/codex/05-infrastructure/spot-vms-for-backfill.md` §
"Preemption recovery MUST resume from PROGRESS, never replay START_DATE".

## Why it matters

Every script in this family that runs on SPOT VMs (the default for backfill/idempotent work per the workspace's SPOT
policy) without a checkpoint restarts from object 0 / day one on EVERY preemption. At corpus scale, a single preemption
mid-run costs hours of re-work; over a campaign's lifetime with multiple preemptions, this can double or triple
wall-clock time and SPOT billing cost. This is exactly the class of waste `/vm-preemption-billing-waste-audit` looks
for, and exactly the gap the already-shipped fix on `rewrite_tradfi_chain_bundle_content_id_2026_07_25.py`
(`market-tick-data-service@261f9abd` + `@5bf8a3c7`) closed for that one executor.

## Recommended decision

Each missing script needs a `record_vm_progress` checkpoint (date-loop scripts) or an object-index checkpoint (non-date
scripts). None are currently in active multi-hour SPOT campaigns, so these are tracked P2 follow-up todos rather than
inline fixes (per the 2026-07-29 P3 census's own conclusion: "revisit if/when one of them runs at fleet scale on SPOT").

### Category A — Date-loop scripts: adopt `record_vm_progress` directly (10 scripts)

- [x] ✅ [DATA] P2. Add `record_vm_progress` checkpoint to `migrate_aster_cefi_defi_bucket_2026_07_13.py`, mirroring
      `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`'s pattern (per-day `Counter` +
      `record_vm_progress(day)` gated on `apply`). Repo: market-tick-data-service@28860a63.
- [x] ✅ [DATA] P2. Add `record_vm_progress` checkpoint to `migrate_cefi_dated_perps_margin_marker_2026_07_09.py`, same
      pattern — market-tick-data-service@e58592a5.
- [x] ✅ [DATA] P2. Add `record_vm_progress` checkpoint to `migrate_cefi_tardis_filename_canonical_2026_07_17.py`, same
      pattern — market-tick-data-service@9acc780e.
- [x] ✅ [DATA] P2. Add `record_vm_progress` checkpoint to `migrate_dex_pool_symbol_shape_2026_07_09.py`, same pattern —
      market-tick-data-service@a4b26ff7.
- [x] ✅ [DATA] P2. Add `record_vm_progress` checkpoint to `migrate_legacy_gas_fees_venue_2026_07_30.py`, same pattern —
      market-tick-data-service@ecca299a.
- [x] ✅ [DATA] P2. Add `record_vm_progress` checkpoint to `migrate_live_sanitized_stem_to_canonical_2026_07_20.py`,
      same pattern — market-tick-data-service@9134ff7e.
- [x] ✅ [DATA] P2. Add `record_vm_progress` checkpoint to `migrate_prediction_trades_legacy_bundle_2026_07_28.py`, same
      pattern — market-tick-data-service@9ba50aa0.
- [ ] [DATA] P2. Add `record_vm_progress` checkpoint to
      `sports/k1k2_casing_revert_2026_07_27/migrate_sports_casing_revert_2026_07_27.py`, same pattern. Repo:
      market-tick-data-service.
- [ ] [DATA] P2. Add `record_vm_progress` checkpoint to
      `sports/league_id_relocation/migrate_sports_casing_2026_07_22.py`, same pattern. Repo: market-tick-data-service.
- [ ] [DATA] P2. Add `record_vm_progress` checkpoint to
      `sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`, same pattern. Repo:
      market-tick-data-service.

### Category B — Non-date scripts: need object-index checkpoint (5 scripts)

- [ ] [DATA] P3. Add object-index checkpoint to `migrate_onchain_perp_perpetual_canonical_2026_07_08.py` (manifest-row
      iterator, no date loop — needs a different checkpoint shape than `record_vm_progress`; design the pattern before
      implementing). Repo: market-tick-data-service.
- [ ] [DATA] P3. Add object-index checkpoint to `migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py`, same
      category. Repo: market-tick-data-service.
- [ ] [DATA] P3. Add object-index checkpoint to `migrate_tradfi_manifest_itype_semantic_relabel_2026_07_27.py`, same
      category. Repo: market-tick-data-service.
- [ ] [DATA] P3. Add object-index checkpoint to `migrate_tradfi_manifest_usd_lin_2026_07_18.py`, same category. Repo:
      market-tick-data-service.
- [ ] [DATA] P3. Add object-index checkpoint to `migrate_tradfi_single_leg_product_root_lin_2026_07_09.py`, same
      category. Repo: market-tick-data-service.

### Category C — Already done (1 script)

- [x] ✅ `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` — already has `record_vm_progress` checkpoint
      (reference implementation).
