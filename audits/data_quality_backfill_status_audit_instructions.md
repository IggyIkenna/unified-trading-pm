---
name: data_quality_backfill_status_audit_instructions
type: audit-instructions
scope: cross-cutting (all asset_groups — MTDS raw ticks + MDPS candles + backfill completeness)
owner: harsh
tier: L1
last_updated: 2026-05-25
last_executed: 2026-05-25 (cefi + defi)
---

# Data Quality & Backfill Status — Audit Instructions

## Scope

Verifies, across all asset_groups (cefi / defi / tradfi / sports / prediction): (1) **backfill completeness** — what
fraction of the expected shard universe is `captured`, and which venues/data_types/chains are failing; (2) **per-shard
data quality** — parquets have real rows, full time span, ~0% NaN (not silent-zero / NaN-fill placeholders); (3) the
upstream→downstream gate (MTDS raw ticks → MDPS candles → features) is respected.

**Two signals are mandatory, never one alone:** manifest `capture_status` AND an actual parquet read. The manifest can
say `captured` over a zero-row/all-NaN placeholder (silent-zero); a parquet can have rows the manifest never recorded
(phantom).

## Triggers

- Whenever a backfill fleet is in flight (cadence: per active-investigation, not idle).
- Before declaring any pipeline layer GREEN, and before launching a downstream layer (features gated on MDPS — see
  §gate).
- Weekly minimum when backfills are ongoing.
- After a new MTDS/MDPS adapter ships or a writegate phase change.

## Checklist

- [ ] (a) **Inventory the running fleet.** Run:
      `gcloud compute instances list --project=central-element-323112 --filter="status=RUNNING" --format="value(name,creationTimestamp.date('%m-%d %H:%M'))" | sort`.
      Group by prefix to see venues/asset_groups in flight + VM ages (stall candidates = age ≫ expected ETA).

- [ ] (b) **Current coverage % per asset_group — aggregate per-VM shards, NOT the consolidated index** (see Gotcha 1).
      Download `gs://<bucket>/_index/per_vm/*.parquet`, then:

      ```python
      import pandas as pd, numpy as np, glob
      df = pd.concat([pd.read_parquet(f) for f in glob.glob("/tmp/pervm/*.parquet")], ignore_index=True)
      df = df[df['service_name']=='market-tick-data-service']           # tick coverage (IS rows = expected-universe)
      df['written_at'] = pd.to_datetime(df['written_at'], errors='coerce', utc=True)
      keys = ['date','venue','data_type','chain','instrument_type','timeframe']
      df = df.sort_values('written_at').drop_duplicates(subset=[k for k in keys if k in df], keep='last')
      v = df['capture_status'].value_counts()
      cap,af,eu = v.get('captured',0), v.get('attempted_failed',0), v.get('expected_unattempted',0)
      print('coverage_pct =', round(100*cap/max(cap+af+eu,1),2))   # excludes empty_confirmed
      ```

      Compare against the baseline (§Baseline). Coverage should be climbing, not flat, during a live backfill.

- [ ] (c) **Per-venue / per-data_type / per-chain breakdown.** Pivot the deduped frame
      `index=venue|data_type|chain, columns=capture_status`. **Flag any venue/type at 0% captured or with high
      `attempted_failed`** — those are adapter/credential failures, not progress.

- [ ] (d) **Freshness — confirm the CURRENT fleet is writing** (not a prior run). Run:
      `gcloud storage ls -l "gs://<bucket>/raw_tick_data/by_date/day=<recent>/.../<DT>/" | head` and compare the object
      write-timestamp against the VM `creationTimestamp` from (a). ⚠️ A date-partition existing is NOT proof of
      freshness.

- [ ] (e) **Parquet row + NaN spot-check (the silent-zero check).** Sample ≥1 shard per asset_group + a sparse type
      (e.g. `liquidations`). Run (MTDS venv has pyarrow; workspace venv does not):

      ```bash
      PY=/active/unified-trading-system-repos/market-tick-data-service/.venv/bin/python3
      gcloud storage cp "gs://<bucket>/<...>/<SYMBOL>.parquet" /tmp/s.parquet
      "$PY" -c "import pyarrow.parquet as pq; df=pq.read_table('/tmp/s.parquet').to_pandas(); \
      print('rows',len(df)); print((df.select_dtypes('number').isna().mean()*100).round(1).to_dict())"
      ```

      Pass: rows > 0, full-day span, NaN% ~0 on price/volume. Sparse types legitimately have few rows — that is correct.

- [ ] (f) **DeFi — read the `-prd` bucket, not the flat `-defi` bucket** (Gotcha 3). Break down `defi-prd` by `chain` +
      `data_type`. **Verify the MVP-archetype inputs explicitly:** `carry_staked_basis` needs `lst_rates` +
      `lending_indices` captured; `arbitrage_price_dispersion` needs `dex_swaps` + `swaps_ohlcv_*` + `oracle_prices`.

- [ ] (g) **attempted_failed triage.** For any failing venue/data_type, read the manifest rows' failure reason
      (`record_failed_reason` / error columns) and trace the adapter. Distinguish: real failure (`attempted_failed`>0,
      fixable) vs expected-empty (0 failed, all `empty_confirmed`, by design).

- [ ] (h) **Cross-check with the existing scripts** (don't reinvent — see table). At minimum run
      `audit_structural_checks.py --asset-group <ag> --checks 4,6` (shard staleness + empty/failed accuracy) and
      `reconcile_phantom_manifest_rows_all.py --asset-group <ag> --dry-run` (phantom = manifest captured but no
      parquet).

- [ ] (i) **Daily coverage report freshness.** Check `gs://central-element-323112-honest-coverage/` has a report for
      today with a recent `generated_at`. If stale, the cron has stopped — recompute or restart it (DQ-05).

### Existing scripts (use first; locations)

| Script                                                                      | Checks                                                                                                        |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `instruments-service/scripts/measure_honest_coverage.py`                    | coverage % per ag/venue/data_type; daily → `gs://central-element-323112-honest-coverage/{date}/coverage.json` |
| `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`        | phantom captures (`--asset-group X --dry-run`)                                                                |
| `market-tick-data-service/scripts/audit_structural_checks.py`               | 6 structural checks (`--checks 1..6`)                                                                         |
| `market-tick-data-service/scripts/validate_manifest_coverage.py`            | manifest vs UAC catalogue false-missing rate                                                                  |
| `market-data-processing-service/scripts/reconcile_1440_nan_placeholders.py` | NaN/placeholder detection (MDPS candles)                                                                      |
| `features-service/scripts/sports/honest_coverage_report.py`                 | sports per-league coverage                                                                                    |

UTL libs: `honest_coverage_ratchet.py`, `manifest_completeness.py`, `manifest_freshness.py`, `manifest_consolidator.py`.

### MTDS→MDPS→features gate

A layer is not GREEN until upstream is GREEN. `features_backfill_phase3` declares
`gate: mdps_backfill_phase3 per-ag verification GREEN`. Never recommend/launch features backfill while MTDS/MDPS are in
flight. SSOT: `codex/11-project-management/foundation-completion-gate-discipline.md`.

## Gotchas (read before running)

1. **Consolidated `_index/availability_index.parquet` LAGS mid-backfill** — only as fresh as the last consolidator run.
   On 2026-05-25 it read CeFi 16% while per-VM aggregation read **55.5%**. Always aggregate `_index/per_vm/*.parquet`
   for live coverage. Filter `service_name=='market-tick-data-service'` (instruments-service rows ≈32M = the
   expected-universe enumeration, not captures).
2. **`coverage_pct` vs `all_shards_pct`.** `coverage_pct = captured/(captured+attempted_failed+expected_unattempted)`
   (excludes empty); `all_shards_pct = captured/total`. DeFi reads ~80% / ~49% because most L2 shards are legitimately
   `empty_confirmed` — not a failure.
3. **DeFi multi-bucket: read `-prd`, not flat.** `market-data-tick-defi-...` (flat) is stale/secondary (ETHEREUM+SOLANA
   only); `market-data-tick-defi-prd-...` is LIVE (all chains incl. L2s). Flat-only makes Arbitrum/Base/Optimism look
   0%.
4. **High-cardinality (CME/tradfi) blows up `ls -lr`** — thousands of instruments/day. Drill targeted paths or use the
   manifest; never recursive-walk.
5. **Partition existence ≠ freshness** — a `day=...` dir can be weeks old. Check object write-time vs VM launch.
6. **Bucket SSOT:** resolve via `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name`; flat
   no-suffix bucket = canonical prod (except DeFi, where prd is live — Gotcha 3).

## Success Criteria

- Coverage % computed from per-VM aggregation for each in-flight asset_group, compared to baseline (climbing).
- Per-venue/type breakdown produced; every 0%-captured or high-`attempted_failed` cell flagged in the findings register.
- ≥1 parquet row/NaN spot-check per asset_group passed (or failure recorded).
- DeFi MVP-archetype inputs (`lst_rates`, `lending_indices`, `dex_swaps`, `swaps_ohlcv_*`, `oracle_prices`) status
  stated.
- Findings register + `last_executed` updated; downstream-layer launches confirmed still gated.

## Findings register

| ID    | Date       | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Status                                        |
| ----- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| DQ-01 | 2026-05-25 | TradFi VMs idle — Databento API quota exhausted (`403 auth_account_locked`); not code. No action until quota resets. `BLOCKED-CREDENTIALS`; stop idle VMs to save spend.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | RESOLVED (operator-confirmed)                 |
| DQ-02 | 2026-05-25 | DeFi carry inputs — RE-DIAGNOSED (was over-stated). The `attempted_failed` (90 lst_rates / 105 lending_indices / 58 perp_funding) are OLD (2022→2025-01) **Solana** rows (Jito/Marinade/Kamino/Marginfi/Solend/Drift) with `error_reason=legacy_bare_name_migrated_to_protocol_solana_2026_05_14` + `LegacyBlankErrorReasonError` = manifest-hygiene, not live failure → fix via `reconcile_legacy_blank_to_typed_reason`. The empties are legit honest-absence (`EXPECTED_PRE_GENESIS_CHAIN`/`EXPECTED_INSTRUMENT_NOT_LISTED` on AAVEV3 venues). Lending leg IS captured under `rate_indices`/`utilization`/`risk_params` (ETH 76k/76k/60k). **Residual:** verify LST staking-APR (Lido/RP/cbETH/Jito/Marinade) is captured — currently 0. | OPEN — verify LST capture + hygiene re-run    |
| DQ-03 | 2026-05-25 | CeFi `ASTER` 0% captured — ROOT CAUSE = stale wrong-URL failures. All 142,547 `attempted_failed` written 04-23→05-04, **0 after the 05-14 URL fix** (`fapi.asterdex.com`, committed 7d45b21). Adapter verified working end-to-end locally (209 historical trades + funding fetched). `book_snapshot_5`/`liquidations` failures = stale unsupported-type rows (capability table excludes them). **No code fix needed — re-run ASTER backfill** (not in current fleet); stale rows superseded on re-capture.                                                                                                                                                                                                                                  | RESOLVED (code) — needs re-backfill           |
| DQ-04 | 2026-05-25 | DeFi venue list contamination (per Ikenna): 42 ETH "protocols" inflated by (a) 6 legacy camelCase↔underscore alias dupes (AAVEV3/AAVE_V3, UNISWAPV2/3/4, MORPHOVAULTS, YEARNV3) — `migrate_mtds_defi_legacy_venue_underscore.py` ran but didn't fully dedup; (b) contamination: `COINBASE-SPOT` (CeFi oracle-source leak into DEFI grid — known filter gap in `oracle-prices-{pid}`), `ALCHEMY`/`ANKR` (RPC providers), `GAS_FEES` (a data_type). Real unique ≈28-30. (CeFi `*F0`-as-venue is the analogous Bitfinex enumerator quirk, IS-rows only.)                                                                                                                                                                                      | OPEN — dedup + filter-gap                     |
| DQ-05 | 2026-05-25 | Daily honest-coverage cron (`honest-coverage-daily`, 00:30 UTC) is ENABLED + fired today but produced no output since 05-18 → triggered run fails to write. ALSO reads `cefi-prd` index (36MB) while CeFi's live backfill writes the **flat** `cefi` bucket (172MB) → CeFi % would be wrong/stale even if it ran. Reads consolidated index (lags per-VM). Usable as trend for defi/sports/prediction (-prd correct); NOT for cefi until bucket reconciled.                                                                                                                                                                                                                                                                                  | OPEN — fix write-failure + cefi bucket target |

## Baseline + last snapshot

**2026-05-18 daily report (baseline):** cefi 49.54% | defi 99.91% (all_shards 19.47%) | tradfi 94.85% | sports 100% |
prediction 100%.

**2026-05-25 snapshot (per-VM aggregation):** cefi **55.5%** (climbing; BINANCE-FUTURES 76.6%, BYBIT 75.1%, OKX-SWAP
68.9%, BINANCE-SPOT 66.8%, UPBIT 64.8%, DERIBIT 57.1%) · defi-prd **80%** coverage (48.8% all_shards; ETHEREUM dense,
L2s mostly empty-by-design) · tradfi blocked (DQ-01).

## Changelog

- 2026-05-25 — created free-form, then reformatted to Style B audit-instructions (per Harsh) + first cefi+defi run.
  Method: per-VM aggregation (index lags), DeFi `-prd` bucket. Findings DQ-01..DQ-05 logged.
