---
title: "CeFi tick backfill writes to flat bucket but SSOT canonical is -prd"
created: 2026-05-25
author: harsh + Claude Opus 4.7 (1M)
source:
  - audits/data_quality_backfill_status_audit_instructions.md (DQ-05)
  - instruments-service/scripts/measure_honest_coverage.py
  - deployment-service/configs/cloud-providers.yaml
locked_by: live-defi-rollout
---

# CeFi tick backfill ↔ bucket-SSOT divergence

## What I found

The bucket-name SSOT resolver returns the **`-prd`** bucket as canonical for CeFi (and defi/tradfi/sports) tick data:

```
resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="cefi")
  -> market-data-tick-cefi-prd-central-element-323112
```

But the **live CeFi backfill fleet (≈170 VMs, 2026-05-24/25) is writing to the FLAT bucket**
`market-data-tick-cefi-central-element-323112` (no `-prd` segment):

- Flat `cefi` `_index/availability_index.parquet` = **172 MB**, fresh `_index/per_vm/*.parquet` (newest write 2026-05-25
  06:34), CeFi per-VM coverage ≈ **55.5%** and climbing.
- Canonical `cefi-prd` `_index/availability_index.parquet` = **36 MB**, staler/smaller.

So the two buckets have diverged: the backfill populates flat, the SSOT + downstream readers expect `-prd`.

Confirmed downstream impact: `measure_honest_coverage.py` hardcodes the `-prd` bucket (matches the resolver), so the
daily `honest-coverage-daily` cron measures the **stale `-prd`** data, not the live flat-bucket backfill — explaining
why the coverage report looked stale/low (DQ-05) even though the backfill is healthy.

(DeFi was the mirror image earlier in the audit: `defi-prd` is the LIVE bucket and the flat `defi` is stale — so the
flat-vs-`-prd` "which is live" answer is **inconsistent across asset_groups**, which is the core problem.)

## Why it matters

- **Coverage measurement is wrong for cefi** until reconciled — the cron reads the wrong (stale) bucket, so any
  cefi coverage %, gap report, or downstream gate keyed off `-prd` undercounts the real backfill.
- **Data-location correctness** (Data-Pipeline-Correctness HARD RULE): a backfill writing to a non-canonical bucket
  means the canonical bucket is incomplete; anything reading canonical (features pre-flight, MDPS source, coverage)
  sees a false gap.
- Touches the bucket-SSOT canonicalisation + `code_freeze_migrate_backfill_sequencing` migration state — cross-cutting,
  not a single-script fix.

## Recommended decision (for Ikenna / operator)

Pick one and I'll execute the downstream cleanup:

1. **If `-prd` is canonical** (per resolver): the CeFi backfill launcher/handlers are writing to the legacy flat bucket
   — fix them to resolve via `resolve_bucket_name` (env-tiered `-prd`), and migrate/consolidate the flat-bucket data
   already captured into `-prd` (operator-run migration; not me per "launch nothing").
2. **If flat is intentionally canonical for cefi tick right now** (migration not yet cut over): update the resolver /
   `cloud-providers.yaml` so cefi tick resolves to flat, and point `measure_honest_coverage.py` there — then the
   inconsistency vs defi (`-prd` live) needs an explicit per-AG convention note.

Open question to resolve the inconsistency: **why is defi live on `-prd` but cefi live on flat?** That asymmetry is the
root and should be made uniform (or explicitly documented per-AG).

## Status

PAUSED pending decision. I have NOT touched `measure_honest_coverage.py` or any bucket config. Audit finding DQ-05 in
`audits/data_quality_backfill_status_audit_instructions.md` references this issue.
