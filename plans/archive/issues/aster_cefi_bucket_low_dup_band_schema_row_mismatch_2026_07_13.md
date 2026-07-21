---
doc_type: issue
title:
  ASTER CeFi-bucket "duplicates" in the low_dup band (2025-06-16 -> 2026-06-05) are the SAME narrower-schema,
  row-deficient copies already fixed for high_dup — never re-migrated
summary: >
  A fresh, full (not sampled) per-object parity re-check ahead of aster_cefi_data_defi_bucket_migration_2026_07_13.md's
  Phase-4/Deferred-work deletion step found 4,536 DeFi-bucket ASTER objects (355 distinct days, 2025-06-16 ->
  2026-06-05, a 6.3% conflict rate within that window) whose CeFi-bucket "canonical" copy is NOT byte-identical.
  Spot-checking 3 samples confirms the EXACT same root cause already root-caused and fixed for the high_dup band
  (2024-01-01 -> 2025-06-15) in aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md: the CeFi-bucket copy
  carries only 10 columns (missing
  ask_price/bid_price/day_ntl_volume/funding_timestamp/index_price/instrument_key/last_price/mid_price/
  next_funding_timestamp/open_interest/open_interest_value/predicted_funding_rate/prev_day_price/schema_version/
  volume_24h) vs the DeFi-bucket original's 23, and is often one row short. The prior operator ruling (BLK-4032eac4,
  Option A: re-migrate with --force, making the DeFi-bucket shape authoritative) was explicitly scoped to the high_dup
  band only — this window was never covered. The deletion script correctly refuses to delete any of these 4,536
  DeFi-bucket originals (parity-conflict = never delete), so they remain safely in place pending this decision; nothing
  has been lost.
status: resolved
nature: notes
asset_group: [cefi, defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [migration, data-correctness, cefi, defi, aster, schema-drift, big-finding]
related:
  [
    plans/archive/2026_07/aster_cefi_data_defi_bucket_migration_2026_07_13.md,
    plans/active/issues/aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md,
  ]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  aster_cefi_data_defi_bucket_migration-001 dispatch (Deferred-work "own the deletion end-to-end" todo), slot 5,
  2026-07-13 — surfaced by delete_aster_cefi_defi_bucket_originals_2026_07_13.py's fresh full-population pre-delete
  parity re-check (not a sample), which is exactly why it caught what the prior 45-sample spot-check missed (that check
  found only 1/15 low_dup-band mismatches and treated it as "isolated, not investigated further").
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by: operator (BLK-15137c02, Option A confirmed) + slot 5, 2026-07-13, executed same-session
---

# ASTER CeFi-bucket "duplicates" in the low_dup band are the same narrower-schema issue, unresolved

## What I found

Building the delete plan for `aster_cefi_data_defi_bucket_migration_2026_07_13.md`'s Deferred-work "own the deletion
end-to-end" todo, I re-verify EVERY object's parity fresh (size + crc32c HEAD comparison, full 116,942-object
population, not a sample) before allowing a delete — deliberately not trusting the plan's prior spot-check audits, since
this plan's own history shows sampling already missed a real conflict once (the `low_dup`-band 2026-02-17 LINKUSDT
mismatch noted in `aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md` and never re-migrated).

**Result: 112,406/116,942 objects (96.1%) are byte-identical and safe to delete. 4,536 (3.9%) are NOT** — every single
one is in the `low_dup` band or its transition edge:

| Band                                              | Conflicts | Notes                                                                |
| ------------------------------------------------- | --------- | -------------------------------------------------------------------- |
| `zero_dup` (2023-11-01 -> 2023-12-31)             | 0         | Freshly copied by the original `--apply`, trivially byte-identical   |
| `high_dup` (2024-01-01 -> 2025-06-15)             | **0**     | Option A `--force` re-migration (slot 6) fully held, confirmed clean |
| `low_dup` / transition (2025-06-16 -> 2026-06-05) | **4,536** | 355 distinct days, 6.3% conflict rate within this window             |

Spot-checked 3 random conflicts (`2025-12-25 AVAXUSDT`, `2026-01-03 ARIAUSDT`, `2025-11-15 ADAUSDT`) — all three show
the **identical** pattern already root-caused for `high_dup`: DeFi-bucket original = 23 columns (typed `object`, never
canonically typed); CeFi-bucket "duplicate" = 10 columns, a strict subset plus 2 CeFi-only columns (`instrument_type`,
`underlying`) not present in the DeFi original; DeFi copy consistently 1 row ahead of the CeFi copy. This is not a new
failure mode — it is the SAME write-path-era artifact, just never addressed outside the `high_dup` window the original
audit happened to scope its investigation to.

## Why it matters

- The prior operator decision (`aster_cefi_bucket_duplicate_schema_row_mismatch_2026_07_13.md`, BLK-4032eac4, Option A)
  explicitly resolved this exact question for `high_dup` only: "Re-run the migration for the `high_dup` band
  specifically with `--force`" — the ruling never extended to `low_dup`, and nothing has re-migrated it since.
- The same downstream-consumer risk applies unchanged: `market-data-processing-service`'s `CefiDerivativeAdapter`
  (venue-agnostic, all CeFi venues) and `features-service`'s `FundingOI`/`futures_basis` calculators (explicitly
  documented "NO venue param") read `open_interest`/`index_price` for ALL CeFi derivative_ticker data, including this
  window — they are silently degrading to NaN for these 355 days' worth of ASTER data right now, today, independent of
  this deletion task.
- **This blocks full completion of "own the DeFi-bucket-resident ASTER originals deletion end-to-end"**: the deletion
  script correctly refuses to touch any of these 4,536 DeFi-bucket originals while their CeFi-bucket "twin" is
  unverified/mismatched — deleting them now would be the same class of data-loss regression the prior finding prevented
  for `high_dup`. They remain safely in place; nothing is lost or at risk from the deletion work itself.
- Not resolving this leaves the migration/deletion task permanently ~4% incomplete (4,536 straggler objects), and leaves
  the schema-degradation issue live for the largest remaining unaddressed date window.

## Recommended decision

Given the operator already ruled Option A (re-migrate with `--force`, DeFi-bucket shape authoritative) for the
**identical** issue in `high_dup` — same root cause, same column diff, same consumer-impact analysis already done — the
informed default is to apply the **same** ruling here rather than re-litigating a decision that was already made for
this exact bug. Restating both options for an explicit decision (do not want to assume operator intent extends by
default without confirmation, since the prior ruling's own text scoped it narrowly):

- **(A) — recommended, consistent with the existing ruling.** Re-run
  `migrate_aster_cefi_defi_bucket_2026_07_13.py --apply --force --start-date 2025-06-16 --end-date 2026-06-05` (script
  already supports `--force` from the prior fix; no code change needed), then re-run
  `delete_aster_cefi_defi_bucket_originals_2026_07_13.py --apply` to sweep up the newly-parity-confirmed originals.
- **(B)** Leave the `low_dup` band's 4,536 conflicting DeFi-bucket originals permanently un-deleted and the CeFi-bucket
  copy permanently narrow-schema for this window — narrower fix, but reintroduces the exact silent-NaN degradation the
  operator already rejected once for the same bug.

## Todos

- [x] ✅ [DATA] P1. **RESOLVED (BLK-15137c02, Option A) — DONE, slot 5, market-tick-data-service@`614f276c`.** Operator
      confirmed Option A extends to the `low_dup` band (same root cause, full-population re-check gave high confidence,
      no reader assumes a fixed column count or branches on this date range — re-confirmed via a targeted workspace-wide
      grep of the 4 named consumers + a broader `iloc[:, N]`/`== 10`-column-count/date-literal sweep before executing,
      per the operator's caveat). Ran
      `migrate_aster_cefi_defi_bucket_2026_07_13.py --apply --force --start-date 2025-06-16 --end-date 2026-06-05`:
      `{'force_overwritten': 4536, 'already_migrated_parity_confirmed': 67875, 'skipped_not_in_scope': 0}`, 0 errors —
      the force-overwritten count matches this doc's conflict count exactly. Then re-ran
      `delete_aster_cefi_defi_bucket_originals_2026_07_13.py --apply`: its fresh re-verify (started after the force-fix
      completed) found all 116,942 remaining DeFi-bucket ASTER objects byte-identical to their CeFi-bucket canonical
      target — 0 conflicts, one pass swept the entire corpus. See `aster_cefi_data_defi_bucket_migration_2026_07_13.md`
      Phase 4 / Deferred-work for the full deletion evidence.
