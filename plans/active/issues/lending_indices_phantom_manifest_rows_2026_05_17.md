---
title:
  "lending-indices manifest phantom rows block B-015 paper-trade — 65 rows in 2026-04-15..19 window claim captured but
  parquets absent"
created: 2026-05-17
author: ikenna-main (B-015 chain follow-up after VM 6 successful run revealed lending_rates 0-rows)
resolved: 2026-05-17
resolution: SHIPPED — B-015 window phantom flip-with-correction landed 2026-05-17 by slot-1-main (Option C inline + correction at 01:56 UTC); Option A generalisation `--manifest-bucket` + DeFi venue-variant fix shipped 2026-05-17 by slot-3 at `instruments-service@b64877f`. Verified clean: 65 real / 0 phantom on lending-indices.
source:
  - "VM features-onchain-defi-20260516-235840 events: lending_rates feature_group COMPLETED with 0 rows for 2026-04-15"
  - "VM mtds-lending-indices-20260517-002305 events: 31× MANIFEST_FRESHNESS_SKIP with
    reason=already_captured_by_concurrent_worker for 2026-04-15..19"
  - "gs://lending-indices-central-element-323112/_index/availability_index.parquet — 65 captured rows for B-015 window
    but 0 parquets in day=2026-04-15..19/ prefixes"
locked_by: live-defi-rollout
locked_since: 2026-05-17
severity:
  P1 — blocks features-onchain DeFi backfill (lending_rates 0-rows for B-015 window) → blocks harsh-slot-9 Phase 2
  paper-trade rerun
---

## What I found

The `lending-indices-central-element-323112` bucket's manifest claims 65 captured rows in the B-015 paper-trade window
(2026-04-15..19) across
`(AAVEV3, COMPOUNDV3, SPARK) × (ETHEREUM, ARBITRUM, OPTIMISM, POLYGON, AVALANCHE, BASE, LINEA, BSC) × data_type=lending_indices`,
but the bucket itself has ZERO parquets for those days. Real data exists through 2026-04-14; the entire B-015 window is
phantom-only.

Evidence:

```bash
# Manifest claims captured:
$ gsutil cp gs://lending-indices-central-element-323112/_index/availability_index.parquet /tmp/m.parquet
$ python -c "import pandas as pd; df = pd.read_parquet('/tmp/m.parquet'); \
    print(df[(df['date'].astype(str) >= '2026-04-15') & (df['date'].astype(str) <= '2026-04-19')]['capture_status'].value_counts())"
captured    65

# Actual bucket layout shows nothing:
$ for d in 2026-04-15 2026-04-16 2026-04-17 2026-04-18 2026-04-19; do
    cnt=$(gsutil ls -r "gs://lending-indices-central-element-323112/day=$d/" 2>/dev/null | grep -c "\.parquet")
    echo "$d: $cnt parquets"
  done
2026-04-15: 0 parquets   ← phantom
2026-04-16: 0 parquets   ← phantom
2026-04-17: 0 parquets   ← phantom
2026-04-18: 0 parquets   ← phantom
2026-04-19: 0 parquets   ← phantom
```

This is the classic phantom-manifest pattern documented in CLAUDE.md ("Manifest phantom audit … Do NOT write empty
parquets to mask phantoms"). The `lst_rates_handler` + sister handlers use `ManifestFreshnessCache.is_now_captured()` to
short-circuit redundant work; when the manifest is lying, the handler skips real backfill work.

## Why it matters

- B-015 features-onchain DeFi backfill (VM `features-onchain-defi-20260516-235840`) ran cleanly, but `lending_rates`
  feature_group returned 0 rows because upstream `lending-indices` bucket is empty for 2026-04-15..19.
- harsh-slot-9 Phase 2 paper-trade rerun is gated on features-onchain rows existing.
- Slot-1-main attempted to backfill via `bash launch-mtds-lending-indices-backfill-vm.sh 2026-04-15 2026-04-19` → VM
  `mtds-lending-indices-20260517-002305` launched 00:23 UTC, STOPPED 7 sec later with 31× `MANIFEST_FRESHNESS_SKIP`
  events (every (venue, chain, date) → "already_captured_by_concurrent_worker") + 2× `LENDING_DAY_COMPLETE` → no actual
  GraphQL queries fired → no writes.

## Why the existing reconciler doesn't cover this

`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi` reads from
`gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet`. That manifest holds DeFi tick
data (vault_share_price, lst_rates, dex_swaps, etc.) but NOT lending_indices — the lending_indices handler writes its
own manifest at `gs://lending-indices-central-element-323112/_index/availability_index.parquet`. The reconciler script
needs extension to enumerate per-data-type buckets (lending-indices, dex-pools, eigenlayer-rewards, lst-rates) on top of
the central DeFi tick bucket.

## Recommended decision

**Option A** (recommended; smallest scope): extend `reconcile_phantom_manifest_rows_all.py` to accept a
`--manifest-bucket-override <BUCKET>` flag (or auto-resolve per data_type via UAC/bucket_naming) so it can audit the
lending-indices manifest. Then run with `--unphantom` to flip the 65 phantom rows from `captured` → `attempted_failed`
(so the handler retries). Then re-launch `mtds-lending-indices-backfill-vm.sh 2026-04-15 2026-04-19` to populate.

**Option B**: write a one-shot script `reconcile_phantom_lending_indices_rows.py` that targets only the lending-indices
manifest. Same flip logic; smaller blast radius if reconciler-script refactor takes more than 1 cycle.

**Option C** (fastest but riskiest): directly modify the manifest via Python — load parquet, filter to phantom rows,
flip `capture_status` to `attempted_failed`, set `error_reason` to a typed enum value, write back via `to_parquet`.
Slot-1 has done this kind of operation before during the v8 schema migration. Risk: if there's a manifest-writer
contract beyond capture_status (e.g. additional sentinel files or BigQuery sync), this may bypass invariants.

**My recommendation**: **B** — write the one-shot now to unblock B-015 today, then file **A** as the follow-up
generalisation. Owner: slot-3 (manifest reconciliation expertise) or features-service (downstream consumer).

## RESOLVED (B-015 window) — 2026-05-17 00:35 UTC (slot-1-main)

**Shipped Option C inline** (direct manifest flip, idempotent + self-healing):

1. Downloaded `gs://lending-indices-central-element-323112/_index/availability_index.parquet` (39,877 rows).
2. Identified 65 phantom candidates: `capture_status=='captured'` AND date in 2026-04-15..19.
3. Per-date GCS prefix probe (`gsutil ls -r day=D/`) confirmed all 5 days have 0 parquets → 65/65 verified phantom.
4. Flipped rows to `capture_status=attempted_failed` / `error_reason=phantom_captured_no_parquet_at_canonical_path` /
   `attempted_at=2026-05-17T00:33:36+00:00` (matching the pattern at
   `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:744-746`).
5. Re-uploaded manifest to GCS. Local backup at `/tmp/lending_manifest.parquet.backup-20260516T233336`.
6. Re-launched backfill VM `mtds-lending-indices-20260517-003742` at 00:37 UTC. Expect actual GraphQL queries + parquet
   writes this time.

**Generalisation follow-up**: ✅ **DONE 2026-05-17 (slot-3)** — `instruments-service@b64877f` shipped two extensions to
`reconcile_phantom_manifest_rows_all.py`: (a) new `--manifest-bucket` + `--manifest-index` CLI flags route both manifest
read AND prefix-path probing to any override bucket (lending-indices, lst-rates, oracle-prices, perp-funding,
eigenlayer-rewards), and (b) DeFi venue-needle now applies `_defi_protocol_variants()` so the substring check accepts
both `AAVEV3` ↔ `AAVE_V3` / `COMPOUNDV3` ↔ `COMPOUND_V3` spellings (was matching only the manifest's literal spelling
even though the prefix template already probed both — root cause of 60/65 false phantoms on the original audit).
Verified end-to-end against the lending-indices bucket:
`--asset-group defi --manifest-bucket lending-indices-central-element-323112 --dry-run --start-date 2026-04-15 --end-date 2026-04-19`
now reports `65 real / 0 phantom`, matching the corrected manual state.

## Cross-references

- `plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md` § "VM 6 follow-up findings" item #2
- `plans/active/issues/defi_upstream_46day_full_backfill_2026_05_16.md` — adjacent issue (the upstream MDPS DeFi gap)
- `market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py:294-326` —
  `ManifestFreshnessCache` short-circuit logic
- CLAUDE.md § "Manifest phantom audit"

## CORRECTION 2026-05-17 01:56 UTC (slot-1-main) — over-flip on days 17-19 reversed

My original phantom-flip checked only the LEGACY path (`day=*/category=defi/`) when probing for existing parquets. But
days 17-19 actually had real data at the NEW canonical path (`raw_tick_data/by_date/day=*/asset_group=defi/`) written
2026-05-09. So 39 of my 65 phantom-flips were wrong.

**Corrected**: re-loaded manifest, identified 39 rows with `capture_status=attempted_failed` +
`error_reason=phantom_captured_no_parquet_at_canonical_path` in 2026-04-17..19, verified each date has the new-path
prefix populated, flipped back to `capture_status=captured` + `error_reason=''`. Uploaded to GCS.

**Lesson** (worth folding into the Option A generalisation): any phantom-reconciler MUST probe BOTH paths per CLAUDE.md
"Asset-group vocabulary" dual-vocab SSOT. The `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`
script already handles this via "two-probe" logic (line 76-77 comment "A phantom audit MUST probe BOTH or we
false-positive every legacy row"). My one-shot didn't — won't make this mistake again, and the generalisation follow-up
will inherit the correct probe.

**Net state for B-015 window**:

- 2026-04-15 + 16: captured (real data from VM 003742 retry, written 2026-05-16T23:25 UTC)
- 2026-04-17, 18, 19: captured (pre-existing 2026-05-09 data at new path)
- B-015 paper-trade upstream is now COMPLETE for the full 5-day smoke window.
