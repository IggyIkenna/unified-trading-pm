---
title: "honest-coverage cron reads -prd while CeFi tick data is in flat (Phase 2.6 not yet run)"
created: 2026-05-25
author: harsh + Claude Opus 4.7 (1M)
source:
  - audits/data_quality_backfill_status_audit_instructions.md (DQ-05)
  - instruments-service/scripts/measure_honest_coverage.py
  - plans/active/mtds_backfill_phase3_2026_05_22.md (Deferred work table)
  - plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md (Phase 2.6)
locked_by: live-defi-rollout
parent_epic: epics/mtds_mdps_master.md
status: active
---

# honest-coverage cron reads `-prd` while CeFi tick data is still in flat

## What I found

**CORRECTION (2026-05-25): the flat-bucket write is EXPECTED, not a bug.** Initially flagged this as a
backfill-writes-to-wrong-bucket divergence; on reading the plans, it is a **known, deferred** item:

> `mtds_backfill_phase3_2026_05_22.md` § Deferred work: _"Bucket naming: MTDS writes to flat bucket
> (`market-data-tick-{ag}-{pid}`) instead of prd bucket … UTL `get_write_bucket_name` uses legacy `cloud_constants.py`
> BUCKET_PREFIXES, not `resolve_bucket_name()`."_ — **Status: DEFERRED** → successor
> `bucket_name_ssot_canonicalisation_2026_05_10.md` **Phase 2.6 migration** (flat→env-tiered, with a write-pause
> cutover).

So the plan of record is: **keep writing to the flat bucket now, migrate everything to env-tiered `-prd` in Phase 2.6.**
The CeFi backfill writing to flat is intended-for-now. (DeFi reads `-prd` because its on-chain handlers use a different
write path — `write_defi_rows`/`DefiManifestRecorder` — already on `-prd`; the CeFi Tardis tick path via
`get_write_bucket_name` is the one still on flat. That explains the cross-AG flat-vs-`-prd` asymmetry.)

## The genuinely-new defect (narrowed scope)

`instruments-service/scripts/measure_honest_coverage.py` hardcodes the `-prd` bucket per asset_group
(`_MANIFEST_BUCKETS`). For CeFi this reads the (near-empty/stale, 36 MB) `-prd` index while the live backfill writes the
flat (172 MB, ~55% coverage) bucket — so the daily `honest-coverage-daily` cron **measures the wrong bucket for CeFi**
and reports stale/low coverage. The reader assumes Phase 2.6 already ran.

## Why it matters

The coverage cron is the SSOT for the data-status %/gap surface. Until reconciled, any CeFi coverage number it produces
is wrong (under-counts the real backfill). Not a data-correctness issue (data is fine, in flat), but a
**measurement-correctness** one.

## Recommended fix (small, in-lane)

Make `measure_honest_coverage.py` read the **same bucket the writers actually use** rather than hardcoding `-prd` — i.e.
resolve via UTL `get_write_bucket_name(...)` (the function the backfill writers use). That tracks the writers regardless
of migration state: flat today, `-prd` automatically after Phase 2.6. Smoke-test by running
`--asset-group cefi --output-path /tmp/cov.json` and confirming it reads the populated (flat) bucket. No bucket config
or backfill change — the Phase 2.6 migration itself stays owned by the bucket-SSOT plan.

## Update 2026-05-25 — coverage-reader fix written + smoke-tested (NOT pushed); deeper residual found

Implemented in `instruments-service/scripts/measure_honest_coverage.py` (UNCOMMITTED on disk): replaced the hardcoded
`-prd` `_MANIFEST_BUCKETS` with `_MANIFEST_BUCKET_CANDIDATES` (both `-prd` + flat per AG) and rewrote `_read_manifest`
to read whichever candidate has the most rows (the live bucket) — robust to the migration, auto-corrects after Phase
2.6. Smoke-test (cefi): correctly selected the FLAT index (34.9M rows) over `-prd` (2.6M). `get_write_bucket_name` alone
was insufficient — it returns flat for ALL AGs, but DeFi's live data is `-prd` (different write path), so a max-rows
pick is required.

**Deeper residual (NEW — consolidator domain, Ikenna):** even with the right bucket, cefi coverage reads **6.69%** vs
the **~55%** from per-VM aggregation, because the consolidated `availability_index.parquet` LAGS the `_index/per_vm/`
shards (audit Gotcha 1). The manifest consolidator (Cloud Run, targets `-prd`) is not folding the flat-bucket per-VM
shards into the flat-bucket index. Accurate mid-backfill coverage needs the consolidator to fold flat per-VM (or the
reader to aggregate per-VM directly — but that duplicates the consolidator). This is consolidator/migration-pipeline
territory, not the coverage reader.

**NOT pushed:** instruments-service local `.venv` is broken (no pandas/basedpyright) + workspace venv lacks basedpyright
→ cannot run repo QG locally (merge prereq). Change held on disk for QG + push on a working host.

## Status

Bucket-write behaviour = WORKING-AS-DEFERRED (Phase 2.6 owns the migration). Coverage-reader bucket-selection fix =
WRITTEN + smoke-tested, HELD (QG blocked by broken venv). Accurate-number = BLOCKED on consolidator-lag residual
(Ikenna/consolidator). DQ-05 in the audit doc points here.
