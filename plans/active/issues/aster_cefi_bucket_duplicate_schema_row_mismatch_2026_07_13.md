---
doc_type: issue
title:
  ASTER CeFi-bucket "duplicates" (high-dup era 2024-01→2025-06) are narrower-schema, row-deficient copies — not true
  duplicates
summary: >
  Post-apply parity verification for aster_cefi_data_defi_bucket_migration_2026_07_13.md found that the CeFi-bucket
  objects the migration's idempotency check treated as "already migrated" (43,817 parity-conflict, not-overwritten
  objects, concentrated in the 2024-01→2025-06 high-duplication era) are NOT byte-identical duplicates of the
  DeFi-bucket originals: they carry a narrower schema (10 columns vs 23 — missing mark_price/bid_price/ask_price/
  index_price/mid_price/open_interest/volume_24h and more) AND, in a majority of sampled cases, fewer rows (a consistent
  off-by-one deficit, e.g. 4 DeFi rows vs 3 CeFi rows). This means the DeFi-bucket originals in this era are the MORE
  COMPLETE copy, not a redundant duplicate — Phase 4's planned cleanup (delete the DeFi-bucket originals once parity is
  "green") would delete the richer data and keep the poorer one if it proceeds on the existing "object presence =
  migrated" assumption.
status: open
nature: notes
asset_group: [cefi, defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [migration, data-correctness, cefi, defi, aster, schema-drift, big-finding]
related: [plans/active/aster_cefi_data_defi_bucket_migration_2026_07_13.md]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  aster_cefi_data_defi_bucket_migration-006 dispatch (Phase 2 Todo 3, post-apply verification), slot 14, 2026-07-13
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
---

# ASTER CeFi-bucket "duplicates" are narrower-schema, row-deficient — not true duplicates

## What I found

Ran `scripts/verify_aster_cefi_defi_bucket_migration_2026_07_13.py` (new script, this dispatch) against the full 948-day
migration scope, two checks:

**1. Existence completeness** — PASSED. All 117,176 DeFi-bucket ASTER objects now have SOMETHING at their canonical
CeFi-bucket target (73,359 from the `--apply` copy + 43,817 pre-existing "duplicates" the migration correctly declined
to overwrite). 0 objects missing.

**2. Row/byte parity spot-check** — 45 samples (15 per band) across the three duplication-period bands:

| Band                            | n   | row_count_matches | byte_identical |
| ------------------------------- | --- | ----------------- | -------------- |
| zero_dup (2023-11→2023-12)      | 15  | 15/15             | 15/15          |
| **high_dup (2024-01→2025-06)**  | 15  | **5/15**          | **0/15**       |
| low_dup (2025-06-18→2026-06-05) | 15  | 14/15             | 14/15          |

The `zero_dup` band is 100% clean by construction (every object there was freshly copied by `--apply`, so it's a
server-side exact copy — trivially byte-identical). The `low_dup` band is also nearly clean (1/15 mismatch,
`day=2026-02-17 LINKUSDT`: defi=4 rows vs cefi=3 rows — isolated, not investigated further here).

**The `high_dup` band is the real problem** — this is the plan's own "steady 98-99% duplication" era, the LARGEST slice
of the corpus by object count (~545 of 948 days). 10/15 sampled objects show a row-count deficit in the CeFi-bucket copy
(consistently the DeFi copy has exactly ONE more row: 4-vs-3, 7-vs-6 — a regular pattern, not random corruption). 0/15
are byte-identical even where row counts DO match.

**Root-caused the schema gap directly** (not just row counts) by downloading and comparing one full pair
(`day=2024-02-14 PYTHUSDT`, 3 rows both sides — matching row count, still non-identical):

- **DeFi-bucket source: 23 columns** —
  `instrument_key, venue, timestamp, last_price, mark_price, index_price, mid_price, prev_day_price, funding_rate, predicted_funding_rate, next_funding_timestamp, funding_timestamp, open_interest, open_interest_value, day_ntl_volume, bid_price, ask_price, volume_24h, schema_version, symbol, data_type, instrument_id, available_at`
  (all `object` dtype — the DeFi-bucket writer never applied canonical typing).
- **CeFi-bucket "duplicate": only 10 columns** —
  `timestamp, funding_rate, mark_price, symbol, venue, data_type, instrument_type, underlying, instrument_id, available_at`
  (properly typed: `timestamp`/`available_at` are `datetime64[ns, UTC]`, `funding_rate`/`mark_price` are `float64`).
- **15 columns exist ONLY in the DeFi-bucket copy**:
  `mid_price, day_ntl_volume, funding_timestamp, next_funding_timestamp, ask_price, last_price, open_interest_value, predicted_funding_rate, index_price, volume_24h, open_interest, instrument_key, prev_day_price, bid_price, schema_version`.
- 2 columns exist only in the CeFi-bucket copy (`instrument_type`, `underlying`) — likely added by whatever later
  canonicalization pass produced the CeFi-bucket copy, at the cost of dropping the 15 richer fields above.

## Why it matters

- This is a **data-correctness finding**, not a migration-mechanics bug — the migration script itself behaved correctly
  (its `(size, crc32c)` idempotency check correctly detected these as NOT byte-identical and declined to overwrite,
  exactly as designed; this issue is about what those pre-existing CeFi-bucket objects actually ARE).
- **Directly affects Phase 4** (`aster_cefi_data_defi_bucket_migration_2026_07_13.md`'s cleanup step, currently
  `BLOCKED-OPERATOR-DECISION`, gated on "Phase 2's parity verification is fully green"): if Phase 4 proceeds on the
  premise that a CeFi-bucket "duplicate" existing = safe to delete the DeFi-bucket original, it would delete the MORE
  COMPLETE data (23 cols, correct row count) and permanently keep the LESS COMPLETE data (10 cols, sometimes short a
  row) for ~545 days / a large fraction of the corpus's high-dup era. That is a real, hard-to-reverse data loss, not a
  cleanup.
- Affects any downstream consumer currently reading the CeFi-bucket copy for this era and assuming it has
  `bid_price`/`ask_price`/`open_interest`/`volume_24h` etc. — those columns are silently absent for ~545 days of ASTER
  history in the canonical location, even though the raw data exists (in the DeFi bucket, un-consumed by anything
  expecting the canonical path).

## Recommended decision

Did not attempt a fix or a re-migration decision here — this needs an operator/architecture call on which schema is
authoritative going forward (the raw 23-column DeFi-bucket shape, or a canonicalized-but-narrower 10-column shape),
which is exactly the kind of decision Phase 4's own gating language already anticipates but had not yet identified a
concrete reason to invoke. Two options for whoever picks this up:

- **(A)** Re-run the migration for the `high_dup` band specifically with `--force` (overwrite), replacing the narrower
  CeFi-bucket copies with the richer DeFi-bucket originals — but this changes the CeFi-bucket schema for ~545 days,
  which may break downstream readers expecting the current 10-column shape; needs a consumer audit first.
- **(B)** Leave both as-is, update Phase 4's cleanup criteria to explicitly EXCLUDE the `high_dup` band from any future
  DeFi-bucket-original deletion (since deleting them there would be lossy) — narrower fix, defers the schema question
  indefinitely.

## Todos

- [ ] [DATA] P1. Operator/architecture decision: for the `high_dup` era (2024-01-01→2025-06-15), is the 23-column
      DeFi-bucket shape or the 10-column CeFi-bucket shape authoritative going forward? Audit downstream consumers of
      the CeFi-bucket ASTER `derivative_ticker` data for this era before deciding (repo: market-tick-data-service +
      consumers).
- [ ] [DATA] P2. Once decided: either re-migrate the `high_dup` band with `--force` (option A) or add an explicit
      Phase-4 exclusion for this band (option B) to `aster_cefi_data_defi_bucket_migration_2026_07_13.md`. (repo:
      unified-trading-pm)
