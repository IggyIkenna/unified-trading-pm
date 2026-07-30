---
doc_type: issue
title: cefi Era-B population has 0 captured rows — plan's physical-object-copy premise was wrong; manifest dedup+restamp is the real fix
summary:
  cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md's cefi CF-1/CF-4/CF-5/Era-B todo (split off by slot-6,
  2026-07-29) specified a physical GCS object copy of "~491,146 raw_tick_data objects" from data_type=options_chain/ to
  data_type=trades/ to close cf_manifest_audit.py's Era-B check. A fresh live dry-run (slot-12, 2026-07-30) of the
  migrator built to do that copy found the premise does not match live data — 0 of the 491,324 Era-A
  (data_type in {options_chain, futures_chain}) manifest rows are capture_status=captured, so there is nothing physical
  to copy. 482,927 of those rows are duplicate bookkeeping entries whose (date, venue, instrument_type) cell already has
  an independent, correctly-labeled data_type=trades row (53,308 of those counterparts are genuinely captured); the
  remaining 8,397 have no trades counterpart. The corrected fix is a manifest-only CAS transform (drop the 482,927
  duplicates, restamp the 8,397 non-colliding rows to data_type=trades) — never touches any GCS raw_tick_data object.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [cefi, manifest, era-b, data-correctness, plan-premise-correction, dedup, delete-safety]
related: [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26]
created: 2026-07-30
author: slot-12 (data_engineering)
source: [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md]
assigned_vm: NA
---

## What I found

`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s cefi CF-1/CF-4/CF-5/Era-B todo (slot-6, 2026-07-29 split)
stated: "the Era-B open question was ANSWERED as a genuine PHYSICAL on-disk fact... COPIES the ~491,146 affected cefi
raw_tick_data objects from data_type=options_chain/... to a NEW data_type=trades/ location." That conclusion was reached
by reading the WRITER's path-building code (`symbol_rules.py`'s `_MERGED_DATA_TYPE_MAP`), never by reading the actual
live manifest's `capture_status` distribution for the affected population.

I built the migrator to do exactly that (physical object copy + manifest re-point) and, before running any `--apply`,
ran its dry-run against the LIVE cefi manifest (`market-data-tick-cefi-prd-central-element-323112`,
`_index/availability_index.parquet`, 9,928,221 total rows). Results (verified twice, ~40 min apart, numbers stable):

- **491,324 rows** carry `data_type` in `{options_chain, futures_chain}`.
- **0 of them are `capture_status=captured`** — the full breakdown is `expected_unattempted=259,650`,
  `attempted_failed=229,378`/`229,070` (± the live-shift between my two reads), `empty_confirmed=2,296`. There is no
  backing GCS object for ANY of these rows — nothing to copy.
- `instrument_type` for the overwhelming majority is `PERPETUAL`/`OPTION`/`FUTURE` (uppercase, singular) — not the
  chain-bundle `options_chain`/`futures_chain` token. Only ~2,150 rows carry a genuine chain-bundle `instrument_type`.
  `underlying`/`quote_asset`/`margin_type` are BLANK on 100% of these rows (0/491,324 populated) — the v6 chain-bundle
  path (which requires all three) was never actually exercised for this population; these are legacy per-symbol
  capture-ATTEMPT bookkeeping rows mis-tagged with the old chain `data_type` vocabulary.
- Cross-referencing each row's `(date, venue, instrument_type)` key against the manifest's `data_type=trades`
  population: **482,927 of the 491,324 rows are DUPLICATES** — their cell already has an independent, correctly-labeled
  `data_type=trades` row (53,308 of those counterparts are genuinely `captured`). Restamping the old row's `data_type`
  in place (the originally-planned Phase 1 "manifest re-point" step) would have created a SECOND row for the same
  shard-atom key, corrupting the manifest.
- The remaining **8,397 rows** have no `data_type=trades` counterpart and are safe to restamp in place.

## Why it matters

The parent plan's stated design (VM-scale physical GCS copy of ~491k objects, followed by a manifest re-point that
would have collided with 482,927 already-correct rows) was both (a) unnecessary — a multi-VM, multi-hour, real-money
GCS-copy operation for objects that don't exist — and (b) if executed as speced, would have corrupted the manifest by
duplicating 482,927 shard-atom keys. This is exactly the kind of premise error the data-correctness HARD RULE exists to
catch before a VM launch, not after.

## What I did

Rewrote the migrator (`market-tick-data-service/scripts/migrate_cefi_era_b_chain_data_type_relabel_2026_07_29.py`) as a
pure manifest CAS transform — never touches a GCS raw_tick_data object:

1. DROP the 482,927 duplicate rows (confirmed 0 `captured` among them — no real data is discarded; the correct state
   for that cell already lives on the surviving `data_type=trades` row).
2. RESTAMP the 8,397 non-colliding rows' `data_type` to `trades` in place.
3. Single CAS write (generation-matched), snapshot-first to `_index/backups/`, self-verify 0 Era-A rows remain
   post-mutation, STOP-ON-SURPRISE on row count / unexpected `captured` rows in the drop set.

Delete-safety (`codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — manifest-row deletion is in scope): this
qualifies for the reversibility carve-out without an `[OPERATOR]` tag — the bucket's fresh
`gcs_bucket_soft_delete_retention_seconds()` measured `604800` (exactly the 7-day floor) in the same run immediately
before the write, plus the pre-mutation snapshot. Never touches a row with `capture_status=captured`; never a
whole-bucket destroy.

Unit-tested (7 tests: duplicate-drop, non-colliding restamp, non-Era-A rows untouched, mixed population, captured-row
stop-on-surprise, idempotency, no-op). Dry-run-verified twice against live prod before `--apply`.

## Recommended decision

No further decision needed — this doc is filed as the record of the finding + correction. The parent todo's checkbox
in `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` is flipped in the same session citing this doc + the
`--apply` evidence (manifest CAS write generation + row-count delta) once the fix lands.

- [x] [SCRIPT] P1. Rewrite the migrator as a manifest-only dedup+restamp (no GCS object copy) — done, this session
      (market-tick-data-service@<pending-sha>, see commit evidence on the parent plan todo).
