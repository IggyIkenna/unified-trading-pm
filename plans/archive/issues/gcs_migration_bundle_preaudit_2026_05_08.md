---
doc_type: issue
title: GCS migration bundle pre-audit (Phase 0)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
author: tab3-gcs-migration
source:
  [
    plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md § Phase 0,
    unified-trading-library/unified_trading_library/core/cloud_constants.py § BUCKET_PREFIXES (workspace-local — bucket
    inventory SSOT),
    deployment-service/configs/bucket_config.yaml (workspace-local — infrastructure bucket templates + AWS mapping),
    /codex/02-data/availability-manifest-and-data-status.md § "Phantom audit — re-runnable recipe" (read-first for §(c)
    + §(e)),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# GCS Migration Bundle — Phase 0 Pre-Audit

> **Severity**: P0 — gates Phase 1+ of `gcs_migration_bundle_pipeline_mode_2026_05_08`. **Blast radius**: every GCS / S3
> bucket the workspace writes to (cefi / defi / tradfi / sports / prediction × multiple domains) plus
> `_index/availability_index.parquet` per bucket. **Suggested owner**: Tab 3 (gcs-migration-manifest-tab) + operator
> runs §§(b)(c)(d)(e)(g)(h) on a same-region GCE VM.

This Phase 0 deliverable is a **runnable protocol**, not a measurement. The actual counts must be produced by the
operator (or a follow-up sub-agent) on an `asia-northeast1-c` GCE VM per the
[CLAUDE.md "phantom audit re-runnable recipe"](/codex/02-data/availability-manifest-and-data-status.md#phantom-audit-re-runnable-recipe)
rule (cross-region listing is 18× slower — `~12 prefixes/sec` from a laptop vs `222/sec` on GCE same-region). The
sections below are tagged **WORKSPACE-LOCAL** (answerable from this checkout, no GCP access required) or **REQUIRES VM
RUN** (need same-region GCE + ADC + python + pandas + pyarrow).

The completed counts go into a follow-up edit on this same doc — append a `## Run results — <YYYY-MM-DD>` section per
operator pass. Phase 1+ of the bundle plan reads from those results sections to scope cost / wall-clock / risk.

---

## (a) Bucket inventory — WORKSPACE-LOCAL

The workspace bucket SSOT is two-layered:

1. **Per-domain `(domain, asset_group)` templates** in
   [`unified-trading-library/unified_trading_library/core/cloud_constants.py`](../../../unified-trading-library/unified_trading_library/core/cloud_constants.py)
   `BUCKET_PREFIXES` dict (note: UCI was archived — UTL is the canonical bucket-name registry now). Resolution:
   `get_bucket_name(domain, asset_group)` → `{prefix}-{asset_group_lower}-{project_id}` (GCP) or
   `unified-trading-{domain}-{asset_group_lower}-{account_id}` (AWS).
2. **Infrastructure templates** in
   [`deployment-service/configs/bucket_config.yaml`](../../../deployment-service/configs/bucket_config.yaml)
   `infrastructure_buckets:` — singletons + DeFi reference-data buckets that don't fit the `(domain, asset_group)`
   pattern (events, gas-fees, solana-defi, evm-defi, etc.).

### Per-domain × asset-group buckets (BUCKET_PREFIXES + restricted_categories matrix)

For project `${PID}` and asset-groups `(cefi | tradfi | defi | sports | prediction)`, expanded against
`bucket_config.yaml § service_categories.restricted_categories`:

| Domain                  | GCP template                              | AWS template                                           | Asset-groups expanded                          | Per-bucket-set count |
| ----------------------- | ----------------------------------------- | ------------------------------------------------------ | ---------------------------------------------- | -------------------- |
| `instruments`           | `instruments-store-{ag}-${PID}`           | `unified-trading-instruments-{ag}-{aid}`               | cefi / tradfi / defi / sports / prediction (5) | 5                    |
| `market_data`           | `market-data-tick-{ag}-${PID}`            | `unified-trading-market-data-{ag}-{aid}`               | cefi / tradfi / defi / sports / prediction (5) | 5                    |
| `features_calendar`     | `features-calendar-${PID}` (no AG suffix) | `unified-trading-features-calendar-{aid}`              | shared (1)                                     | 1                    |
| `features_delta_one`    | `features-delta-one-{ag}-${PID}`          | `unified-trading-features-delta-one-{ag}-{aid}`        | cefi / tradfi / defi (3)                       | 3                    |
| `features_volatility`   | `features-volatility-{ag}-${PID}`         | `unified-trading-features-volatility-{ag}-{aid}`       | cefi / tradfi / defi (3 — defi via override)   | 3                    |
| `features_onchain`      | `features-onchain-${PID}` (no AG suffix)  | `unified-trading-features-onchain-{ag}-{aid}`          | unified gcp / per-AG aws (cefi / defi)         | 1 (gcp) / 2 (aws)    |
| `features_sports`       | `features-sports-${PID}` (no AG suffix)   | `unified-trading-features-sports-{aid}`                | sports (1)                                     | 1                    |
| `features_prediction`   | `features-prediction-${PID}` (no AG sfx)  | `unified-trading-features-prediction-{aid}`            | prediction (1)                                 | 1                    |
| `features_cross_instr.` | n/a in BUCKET_PREFIXES (per-AG aws only)  | `unified-trading-features-cross-instrument-{ag}-{aid}` | prediction (per restricted_categories)         | 0 / 1 (aws only)     |
| `execution`             | `execution-store-${PID}` (no AG suffix)   | `unified-trading-execution-{ag}-{aid}`                 | financial: cefi / tradfi / defi (3)            | 1 (gcp) / 3 (aws)    |
| `strategy`              | `strategy-store-${PID}` (no AG suffix)    | `unified-trading-strategy-{ag}-{aid}`                  | financial: cefi / tradfi / defi (3)            | 1 (gcp) / 3 (aws)    |
| `risk`                  | `risk-store-{ag}-${PID}` (legacy prefix)  | `unified-trading-risk-{ag}-{aid}`                      | cefi / tradfi / defi / prediction / sports (5) | 5                    |
| `pnl`                   | `pnl-store-{ag}-${PID}`                   | `unified-trading-pnl-{ag}-{aid}`                       | cefi / tradfi / defi (3)                       | 3                    |
| `positions`             | `positions-store-{ag}-${PID}`             | `unified-trading-positions-{ag}-{aid}`                 | cefi / tradfi / defi / prediction / sports (5) | 5                    |
| `ml_models`             | `ml-models-store-${PID}` (no AG suffix)   | `unified-trading-ml-models-{aid}`                      | shared (1)                                     | 1                    |
| `ml_predictions`        | `ml-predictions-store-${PID}` (no AG sfx) | `unified-trading-ml-predictions-{aid}`                 | shared (1)                                     | 1                    |

**Subtotal — domain × asset-group buckets**: GCP **39** (sum of right column where listed), AWS **42** (slightly higher
because aws splits some unified gcp buckets per-AG via `aws_bucket_mappings`).

### Infrastructure / reference-data buckets (bucket_config.yaml infrastructure_buckets)

GCP-only unless paired AWS template exists:

| Bucket template                           | Service                     | Type           | Asset-group |
| ----------------------------------------- | --------------------------- | -------------- | ----------- |
| `terraform-state-${PID}`                  | infrastructure              | infrastructure | ALL         |
| `uts-terraform-state-${PID}`              | infrastructure              | infrastructure | ALL         |
| `deployment-orchestration-${PID}`         | deployment-service          | infrastructure | ALL         |
| `unified-deployment-state-${PID}`         | deployment-service          | infrastructure | ALL         |
| `config-store-${PID}`                     | infrastructure              | config         | ALL         |
| `${PID}-events`                           | infrastructure              | events         | ALL         |
| `${PID}-build-metadata`                   | infrastructure              | build          | ALL         |
| `client-reporting-data-${PID}`            | client-reporting            | reporting      | ALL         |
| `databento-batch-registry-asia-${PID}`    | market-tick-data-service    | reference_data | tradfi      |
| `backtest-configs-${PID}`                 | strategy-service            | config         | ALL         |
| `backtest-results-${PID}`                 | strategy-service            | results        | ALL         |
| `ml-configs-store-${PID}` (+ test sib.)   | ml-training-service         | config         | ALL         |
| `gas-fees-${PID}` (+ test sib.)           | market-tick-data-service    | reference_data | defi        |
| `solana-defi-${PID}` (+ test sib.)        | market-tick-data-service    | reference_data | defi        |
| `evm-defi-${PID}` (+ test sib.)           | market-tick-data-service    | reference_data | defi        |
| `lending-indices-${PID}` (+ test sib.)    | market-tick-data-service    | reference_data | defi        |
| `dex-pools-${PID}` (+ test sib.)          | market-tick-data-service    | reference_data | defi        |
| `lst-rates-${PID}` (+ test sib.)          | market-tick-data-service    | reference_data | defi        |
| `perp-funding-${PID}` (+ test sib.)       | market-tick-data-service    | reference_data | defi        |
| `liquidations-${PID}` (+ test sib.)       | market-tick-data-service    | reference_data | defi        |
| `dex-swaps-${PID}` (+ test sib.)          | market-tick-data-service    | reference_data | defi        |
| `oracle-prices-${PID}` (+ test sib.)      | market-tick-data-service    | reference_data | defi        |
| `eigenlayer-rewards-${PID}` (+ test sib.) | market-tick-data-service    | reference_data | defi        |
| `risk-store-{ag}-${PID}` (legacy form)    | risk-and-exposure-service   | output         | per-AG (5)  |
| `features-volatility-defi-${PID}`         | features-volatility-service | output         | defi        |

AWS additionally has `unified-trading-{name}-{aid}` parallel templates for the DeFi reference-data buckets (gas-fees,
solana-defi, evm-defi, lending-indices, dex-pools, lst-rates, perp-funding, liquidations, dex-swaps, oracle-prices,
eigenlayer-rewards) plus `unified-trading-terraform-state-{aid}`.

**Subtotal — infrastructure buckets**: GCP **~36** (incl. `-test-` siblings), AWS **~12** parallels.

### Pre-migration snapshot bucket (NEW — per §(h))

`gs://${PID}-pre-migration-snapshot` — to be created with versioning + retention `30 days` per §(h). Holds `_index/` +
leaf-parquet samples per source bucket pre-migration. Add to `bucket_config.yaml infrastructure_buckets` in Phase 1 of
the bundle.

### Buckets in scope for the migration

Migration TARGETS = every bucket where `raw_tick_data/by_date/day=*/...`, `processed_candles/...`,
`features/by_date/...`, `sports_features/by_date/...`, or `_index/availability_index.parquet` lives. From the matrix
above:

- **Always-in-scope (every parquet)**: `market-data-tick-{ag}-${PID}` × 5 AGs (raw ticks + MDPS processed_candles
  co-located).
- **Manifest only (no raw parquets — derived buckets)**: features-\* buckets per domain (their parquets need
  pipeline_mode partitioning too — see live_pipeline_mtds_mdps_features_2026_05_08 Phase 14).
- **Reference-data buckets (DeFi infrastructure)**: gas-fees / solana-defi / evm-defi / lending-indices / dex-pools /
  lst-rates / perp-funding / liquidations / dex-swaps / oracle-prices / eigenlayer-rewards. **Verify each whether they
  use the canonical `_index/availability_index.parquet` shape** (operator §§(d) check) — if yes, they're in scope; if
  they have their own bespoke index, they get a per-bucket follow-up plan.
- **Out-of-scope (presence-only, no manifest)**: terraform-state, deployment-orchestration, config-store, events,
  build-metadata, client-reporting-data, databento-batch-registry-asia, backtest-configs, backtest-results,
  ml-configs-store. These hold non-tick state (terraform plans, secrets, configs, event JSONL streams, ML config YAMLs).
  The migration must SKIP them — adding `pipeline_mode=` partition column to `events/{service}/...` JSONL is
  meaningless.

---

## (b) Per-bucket parquet-count estimates — REQUIRES VM RUN

For each in-scope bucket the operator runs (from an `asia-northeast1-c` GCE VM with
`gcloud auth application-default login` set up + the project pinned):

```bash
# ssh into a fresh GCE VM in asia-northeast1-c (e.g. e2-standard-4)
# gcloud + python + pandas + pyarrow + gsutil pre-installed on Container-Optimized OS

PID="$(gcloud config get-value project)"   # set --project at ssh time

# Per in-scope bucket:
for BUCKET in \
    "market-data-tick-cefi-${PID}" \
    "market-data-tick-tradfi-${PID}" \
    "market-data-tick-defi-${PID}" \
    "market-data-tick-sports-${PID}" \
    "market-data-tick-prediction-${PID}" \
    "features-calendar-${PID}" \
    "features-delta-one-cefi-${PID}" \
    "features-delta-one-tradfi-${PID}" \
    "features-delta-one-defi-${PID}" \
    "features-volatility-cefi-${PID}" \
    "features-volatility-tradfi-${PID}" \
    "features-volatility-defi-${PID}" \
    "features-onchain-${PID}" \
    "features-sports-${PID}" \
    "features-prediction-${PID}"; do
  echo "=== $BUCKET ==="

  # Total bytes (rolled-up — fast, single ls call)
  gcloud storage du --readable-sizes --summarize "gs://$BUCKET/" || echo "MISSING/INACCESSIBLE"

  # Total file count under raw_tick_data/by_date/ (slower; only for market-data-tick-*)
  if [[ "$BUCKET" == market-data-tick-* ]]; then
    gcloud storage ls --recursive "gs://$BUCKET/raw_tick_data/by_date/" 2>/dev/null | wc -l
  fi

  # Per asset_group= prefix breakdown (top-of-tree only, day-granular ls)
  gcloud storage ls "gs://$BUCKET/raw_tick_data/by_date/" 2>/dev/null | head -10
done
```

**Wall-clock estimate (per CLAUDE.md phantom-audit recipe rule — `~222 prefixes/sec same-region` with HTTP pool tuned to
`2*workers`)**:

- 1M parquets × ~10 prefixes-per-parquet (path depth `day=/asset_group=/venue=/data_type=/...`) → ~10M prefix probes →
  ~12.5h serial. **Do NOT serialise**: split per-bucket × per-day in parallel from 4-8 same-region VMs (the bundle plan
  Phase 4 sizes this) — under 1h per asset-group-bucket with 64-worker concurrency.
- `gcloud storage du --summarize` is roll-up only — sub-second per bucket. Use that for the bytes column FIRST + decide
  recursive ls budget per bucket from the bytes.

Results table to populate per pass:

| Bucket                               | Bytes (gs du) | Object count | Top-3 asset_group= dirs | Top-3 category= dirs (legacy) |
| ------------------------------------ | ------------- | ------------ | ----------------------- | ----------------------------- |
| `market-data-tick-cefi-${PID}`       | TBD           | TBD          | TBD                     | TBD                           |
| `market-data-tick-tradfi-${PID}`     | TBD           | TBD          | TBD                     | TBD                           |
| `market-data-tick-defi-${PID}`       | TBD           | TBD          | TBD                     | TBD                           |
| `market-data-tick-sports-${PID}`     | TBD           | TBD          | TBD                     | TBD                           |
| `market-data-tick-prediction-${PID}` | TBD           | TBD          | TBD                     | TBD                           |
| `features-calendar-${PID}`           | TBD           | TBD          | n/a                     | n/a                           |
| `features-delta-one-cefi-${PID}`     | TBD           | TBD          | TBD                     | TBD                           |
| `features-delta-one-tradfi-${PID}`   | TBD           | TBD          | TBD                     | TBD                           |
| `features-delta-one-defi-${PID}`     | TBD           | TBD          | TBD                     | TBD                           |
| `features-volatility-cefi-${PID}`    | TBD           | TBD          | TBD                     | TBD                           |
| `features-volatility-tradfi-${PID}`  | TBD           | TBD          | TBD                     | TBD                           |
| `features-volatility-defi-${PID}`    | TBD           | TBD          | TBD                     | TBD                           |
| `features-onchain-${PID}`            | TBD           | TBD          | TBD                     | TBD                           |
| `features-sports-${PID}`             | TBD           | TBD          | n/a (entity=)           | n/a (entity=)                 |
| `features-prediction-${PID}`         | TBD           | TBD          | TBD                     | TBD                           |

---

## (c) Per-bucket existing hive-key audit (5 drift axes) — REQUIRES VM RUN

Per CLAUDE.md "Manifest phantom audit" 5 drift axes. The operator runs **per market-data-tick bucket**:

```bash
# Axis 1: category= (legacy) vs asset_group= (canonical) directory counts
echo "--- Axis 1: hive-vocab category= vs asset_group= ---"
gcloud storage ls "gs://$BUCKET/raw_tick_data/by_date/day=*/category=*/" 2>/dev/null | wc -l
gcloud storage ls "gs://$BUCKET/raw_tick_data/by_date/day=*/asset_group=*/" 2>/dev/null | wc -l

# Axis 2: instrument_type casing variants (PERPETUAL vs perpetual; SPOT vs spot)
echo "--- Axis 2: instrument_type casing variants ---"
gcloud storage ls --recursive "gs://$BUCKET/raw_tick_data/by_date/" 2>/dev/null \
    | grep -oE 'instrument_type=[^/]+' | sort -u | head -50
# Look for case-pair drift: PERPETUAL/perpetual, SPOT/spot, OPTION/option/options/options_chain,
#   FUTURE/future/futures/futures_chain.

# Axis 3: schema-4 empty instrument_type (cannot probe directly from GCS — see manifest §(d) row count)
# Manifest column `instrument_type IS NULL OR instrument_type = ''` count goes here.

# Axis 4: path-prefix drift — legacy `day=*/...` directly under bucket-root vs canonical
#   `raw_tick_data/by_date/day=*/...`
echo "--- Axis 4: path-prefix drift ---"
gcloud storage ls "gs://$BUCKET/day=" 2>/dev/null | wc -l                       # legacy direct-under-root
gcloud storage ls "gs://$BUCKET/raw_tick_data/by_date/day=" 2>/dev/null | wc -l # canonical

# Axis 5: chain-bundle equivalence drift — option vs options_chain, future vs futures_chain
echo "--- Axis 5: chain-bundle equivalence drift ---"
gcloud storage ls --recursive "gs://$BUCKET/raw_tick_data/by_date/" 2>/dev/null \
    | grep -oE 'data_type=(option|options|options_chain|future|futures|futures_chain)' | sort | uniq -c
```

Output schema per bucket:

| Bucket                               | Axis 1 (cat=) | Axis 1 (ag=) | Axis 2 (mixed-case dirs) | Axis 3 (empty type — from manifest) | Axis 4 (legacy day=) | Axis 4 (canonical) | Axis 5 (option/options_chain/future/futures_chain) |
| ------------------------------------ | ------------- | ------------ | ------------------------ | ----------------------------------- | -------------------- | ------------------ | -------------------------------------------------- |
| `market-data-tick-cefi-${PID}`       | TBD           | TBD          | TBD                      | TBD (from §d)                       | TBD                  | TBD                | TBD                                                |
| `market-data-tick-tradfi-${PID}`     | TBD           | TBD          | TBD                      | TBD (from §d)                       | TBD                  | TBD                | TBD                                                |
| `market-data-tick-defi-${PID}`       | TBD           | TBD          | TBD                      | TBD (from §d)                       | TBD                  | TBD                | TBD                                                |
| `market-data-tick-sports-${PID}`     | TBD           | TBD          | TBD                      | TBD (from §d)                       | TBD                  | TBD                | TBD                                                |
| `market-data-tick-prediction-${PID}` | TBD           | TBD          | TBD                      | TBD (from §d)                       | TBD                  | TBD                | TBD                                                |

**Note**: sports + prediction bucket layouts differ — sports uses `entity=` instead of `asset_group=` per the
[Sports GCS path SSOT](/codex/02-data/contracts-scope-and-layout.md) (Axis 1 + 4 N/A there; Axis 2 + 5 may also be N/A).
Keep them in the table for completeness; populate "N/A" if no path matches.

---

## (d) Manifest current shape — REQUIRES VM RUN

Per in-scope bucket (every bucket that has `_index/availability_index.parquet`):

```bash
# Stream the parquet down + group by drift axes — single python invocation
gcloud storage cp "gs://$BUCKET/_index/availability_index.parquet" /tmp/manifest.parquet
python3 - <<'PY'
import pandas as pd
df = pd.read_parquet("/tmp/manifest.parquet")
print(f"--- {len(df)} rows ---")

# (1) pipeline_mode coverage — every NULL row is a Phase 4 backfill target.
if "pipeline_mode" in df.columns:
    print("\n# pipeline_mode distribution")
    print(df["pipeline_mode"].fillna("<NULL>").value_counts())
else:
    print("\n# pipeline_mode column ABSENT — full backfill target (every row).")

# (2) capture_status × asset_group × venue × data_type rollup
print("\n# capture_status × asset_group × venue × data_type")
print(df.groupby([
    "capture_status",
    df.get("asset_group", df.get("category", pd.Series("<MISSING>", index=df.index))),
    "venue",
    "data_type",
]).size().head(50))

# (3) instrument_type casing audit (Axis 2)
print("\n# instrument_type casing")
if "instrument_type" in df.columns:
    print(df["instrument_type"].fillna("<NULL>").value_counts().head(30))
    n_empty = (df["instrument_type"].isna() | (df["instrument_type"] == "")).sum()
    print(f"  empty/NULL instrument_type rows (Axis 3): {n_empty}")

# (4) hive-vocab dual-key column presence (Axis 1)
ag_col = "asset_group" if "asset_group" in df.columns else None
cat_col = "category" if "category" in df.columns else None
print(f"\n# hive-vocab columns: asset_group={ag_col is not None}, category={cat_col is not None}")
if ag_col and cat_col:
    n_only_ag = (df[cat_col].isna() & df[ag_col].notna()).sum()
    n_only_cat = (df[ag_col].isna() & df[cat_col].notna()).sum()
    print(f"  rows with asset_group only: {n_only_ag}; category only: {n_only_cat}")

# (5) chain-bundle drift (Axis 5)
print("\n# data_type chain-bundle classes")
print(df["data_type"].value_counts().filter(regex="^(option|options|options_chain|future|futures|futures_chain)$"))

# (6) path-prefix drift (Axis 4) — only meaningful if manifest stores a path column
for path_col in ("path", "uri", "shard_path"):
    if path_col in df.columns:
        print(f"\n# path-prefix drift via column '{path_col}'")
        print(df[path_col].str.extract(r"(raw_tick_data/by_date/day=|day=)").iloc[:, 0].value_counts())
        break
PY
```

Per-bucket results table:

| Bucket | Total rows | NULL pipeline_mode rows | captured/empty/failed/expected_unattempted | Axis-1 only-cat / only-ag | Axis-2 mixed cases | Axis-3 empty type | Axis-4 legacy / canonical | Axis-5 chain-bundle classes |
| ------ | ---------- | ----------------------- | ------------------------------------------ | ------------------------- | ------------------ | ----------------- | ------------------------- | --------------------------- |
| TBD    | TBD        | TBD                     | TBD                                        | TBD                       | TBD                | TBD               | TBD                       | TBD                         |

**The NULL-pipeline_mode row count IS the migration target volume for Phase 4.** Every other axis count feeds Phase 2
drift sweeps.

---

## (e) Phantom audit residual re-run — REQUIRES VM RUN

Per CLAUDE.md "Manifest phantom audit": 354 residual rows expected post-2026-05-04 reconciliation across the 5 drift
axes. Re-confirm before bundle starts (drift may have re-grown):

```bash
cd instruments-service
for AG in cefi tradfi defi sports prediction; do
    echo "=== ASSET GROUP: $AG ==="
    python scripts/reconcile_phantom_manifest_rows_all.py --asset-group "$AG" --dry-run
done
```

**Expected output shape per asset-group**:

- `Axis 1 (category=/asset_group=) drift: N rows`
- `Axis 2 (instrument_type casing): N rows`
- `Axis 3 (empty instrument_type): N rows`
- `Axis 4 (path-prefix): N rows`
- `Axis 5 (chain-bundle): N rows`
- `TOTAL phantoms: N (target ≤ 354 workspace-wide; per-AG breakdown in audit log)`

Results per asset-group:

| Asset group | Total phantoms | Axis 1 | Axis 2 | Axis 3 | Axis 4 | Axis 5 |
| ----------- | -------------- | ------ | ------ | ------ | ------ | ------ |
| cefi        | TBD            | TBD    | TBD    | TBD    | TBD    | TBD    |
| tradfi      | TBD            | TBD    | TBD    | TBD    | TBD    | TBD    |
| defi        | TBD            | TBD    | TBD    | TBD    | TBD    | TBD    |
| sports      | TBD            | TBD    | TBD    | TBD    | TBD    | TBD    |
| prediction  | TBD            | TBD    | TBD    | TBD    | TBD    | TBD    |

**HTTP pool sizing reminder per CLAUDE.md**: tune to `2*workers` (default 10 silently truncates `list_blobs()` under 64
worker concurrency). The script reads workspace-wide reconciler defaults; verify by `grep` or `--http-pool-size`
override per pass.

**Must run on same-region VM** — cross-region listing is 18× slower (`~12 prefixes/sec laptop` vs
`~222 prefixes/sec asia-northeast1-c`).

---

## (f) Coordination check with `manifest_migration_master_2026_05_07` — WORKSPACE-LOCAL

Read [`plans/epics/manifest_migration_master_2026_05_07.md`](../../epics/manifest_migration_master_2026_05_07.md) and
record the per-stage status. The master's Stage 1/2/3 work MUST land BEFORE this bundle starts (or be folded into bundle
Phase 2 if still pending). Stage 4 items are candidates for bundling here.

| Manifest-master stage | Status (✅ shipped / 🟡 in-flight / 🔲 pending) | Bundled here? | Notes                                          |
| --------------------- | ----------------------------------------------- | ------------- | ---------------------------------------------- |
| Stage 1               | TBD (operator reads master + reports)           | TBD           | TBD                                            |
| Stage 2               | TBD                                             | TBD           | TBD                                            |
| Stage 3               | TBD                                             | TBD           | TBD                                            |
| Stage 4 — items       | TBD                                             | TBD           | Each Stage 4 item: bundle here OR defer + cite |

**Output table for the bundle plan Phase 1 prerequisites section** — feeds the deferred-vs-bundled decision per Stage 4
item.

---

## (g) Cost estimate — REQUIRES VM RUN (counts) + WORKSPACE-LOCAL (formulas)

GCP Class A pricing (2026-Q2):

- `gcloud storage cp` = 1 Class A operation per source object (read) + 1 per dest object (write) = **2 Class A / file
  moved**.
- `gcloud storage rm` = 1 Class A per delete.
- **Class A cost**: $0.005 / 1000 ops at STANDARD storage class.
- **Egress within-region**: $0 (asia-northeast1 → asia-northeast1).
- **Snapshot bucket**: storage cost ≈ 5% of source bucket per snapshot (only `_index/` + leaf-parquet samples per Phase
  3.2 — much smaller than full-bucket snapshot).

### Migration ops (per file)

For Phase 4 partition-rewrite in-place:

1. Read source parquet (1 Class A).
2. Write rewritten parquet at new path (1 Class A).
3. Delete old parquet at old path (1 Class A).

**Total**: 3 Class A operations per file × $0.005/1000 = **$0.000015 per file**.

### Per-bucket cost rollup (placeholder pending §(b) counts)

| Bucket | File count (§b) | Migration ops (3× count) | Class A cost | Snapshot cost (5% of bucket) | Total |
| ------ | --------------- | ------------------------ | ------------ | ---------------------------- | ----- |
| TBD    | TBD             | TBD                      | TBD          | TBD                          | TBD   |

### Wall-clock estimate

Per CLAUDE.md phantom-audit recipe (`2*workers` HTTP pool, default 64-worker concurrency same-region):

- Listing rate: ~222 prefixes/sec.
- Read+write+delete rate per worker: ~10 ops/sec for ~10MB parquets (network-bound).
- 4-8 same-region VMs × 64 workers each = 256-512 effective parallel writers → **~5,000 ops/sec aggregate**.
- 1M files × 3 ops = 3M ops at 5,000 ops/sec → **~10 minutes wall-clock for 1M files**.

Real number will scale with §(b) file count (likely 10-100M files workspace-wide → 1.5-15h aggregate).

### Pessimistic cost worst-case (10M files workspace-wide)

- Class A: 30M ops × $0.005/1000 = **$150**.
- Snapshot: 5% of total bucket bytes × $0.020/GB (STANDARD) — pending §(b) bytes.
- **Total expected**: <$500 for the full migration (Class A dominates).

This is well below the per-bucket `gcloud storage cp -r` benchmarks; not a budget concern. The wall-clock budget is the
constraint.

---

## (h) Per-bucket safety snapshot — REQUIRES VM RUN

Versioning check + snapshot trigger for any bucket with versioning OFF:

```bash
for BUCKET in <list-from-§a>; do
    VERSIONING="$(gcloud storage buckets describe "gs://$BUCKET" \
        --format='value(versioning_enabled)' 2>/dev/null || echo 'MISSING')"
    echo "$BUCKET: versioning=$VERSIONING"
done
```

Per `bucket_config.yaml § bucket_settings.gcp.versioning: true`, **every workspace GCP bucket SHOULD have versioning
enabled**. If any returns `False` or `MISSING`, the migration MUST take a soft-snapshot first via Phase 3.2:

```bash
SNAPSHOT_DATE="2026-05-XX"   # operator picks
PID="$(gcloud config get-value project)"
SNAPSHOT_BUCKET="${PID}-pre-migration-snapshot"

# One-time bucket create with retention
gcloud storage buckets create "gs://$SNAPSHOT_BUCKET" \
    --location=asia-northeast1 \
    --uniform-bucket-level-access \
    --soft-delete-duration=30d || echo "exists"

# Per source bucket (parallel-safe — different prefixes):
for BUCKET in <list>; do
    gcloud storage cp -r "gs://$BUCKET/_index/" \
        "gs://${SNAPSHOT_BUCKET}/${BUCKET}-${SNAPSHOT_DATE}/_index/"
    # Sample 100 leaf parquets per asset_group for spot-check post-migration:
    gcloud storage ls "gs://$BUCKET/raw_tick_data/by_date/" 2>/dev/null \
        | shuf -n 100 \
        | xargs -I{} -P 16 gcloud storage cp -r {} \
            "gs://${SNAPSHOT_BUCKET}/${BUCKET}-${SNAPSHOT_DATE}/sample-leaves/"
done
```

**Snapshot-bucket cost** (per §(g)): only `_index/` (typically <100MB per bucket) + 100 leaf parquets per bucket (each
~10MB) → ~1.5GB per source bucket × 15 buckets ≈ **~25GB total × $0.020/GB/month NEARLINE = $0.50/month** for 30 days
retention. Negligible.

---

## Run protocol

The operator (or a follow-up sub-agent with same-region GCE VM access) runs:

1. **SSH into a fresh `asia-northeast1-c` GCE VM** with `gcloud auth application-default login` already configured.
   Recommended shape: `e2-standard-4` × Container-Optimized OS, project pinned via `gcloud config set project ${PID}`.
   Per-VM-shard isolation is irrelevant here (read-only audit) but `VM_NAME=preaudit-${RUN_TS}` for event correlation.
2. **Run §§(b) → (c) → (d) → (e) → (f) → (g) → (h) in order**. §(f) is workspace-local (read the manifest-master plan
   from the same checkout) — safe to do on workstation; everything else needs the VM.
3. **Append a `## Run results — 2026-05-XX` section** at the bottom of this doc with the populated tables, per "Capture
   Discoveries As Plan Todos Immediately" CLAUDE.md rule. Do NOT auto-memory the counts; they go on disk.
4. **Sign off Phase 0 by flipping the gcs_migration plan checkbox** from `- [ ]` → `- [x]` with citation
   `(unified-trading-pm@<sha> — pre-audit doc shipped + run results landed)`. Per the Commit + Push + Flip Plan
   Checkboxes HARD RULE, the flip happens in the same logical unit as the run-results commit.
5. **Triage findings**: any drift-axis count >10× the 2026-05-04 baseline (354 phantoms) is a Big Finding per Findings
   Triage Discipline — operator-notify + issue doc. Drift counts within expected ranges proceed to bundle Phase 1
   normally.

---

## Why it matters

- **Sets the migration scope**. Phase 1+ of the bundle plan presupposes file counts, drift-axis volumes, and manifest
  shape that we don't currently know without §§(b)(c)(d)(e). Skipping the audit means we're sizing wall-clock + cost
  blind, and the bundle plan's "single-pass" promise (`walks every parquet ONCE`) cannot be honored if drift is larger
  than expected.
- **Locks in the safety net**. §(h) verifies versioning is on (the workspace SSOT says yes per `bucket_config.yaml`, but
  reality may have drifted since `setup-buckets.py` last ran); if not, snapshot is mandatory before Phase 4 starts
  touching parquets.
- **Manifest-master coordination**. §(f) ensures we don't double-migrate items that the manifest-master plan already
  shipped (Stage 1/2/3) and don't drop items it intended us to bundle (Stage 4 candidates).

## Recommended decision

Run the protocol on a same-region VM, populate the result tables, decide bundle Phase 1 scope from the populated counts.
The bundle plan's checkbox-flip discipline (Commit + Push + Flip) means Phase 0 stays `- [ ]` until BOTH this doc lands
AND the run results are appended.

---

## Run results — 2026-05-10 (cefi only — partial; defi/tradfi/sports/prediction in flight)

**VM**: `gcs-migration-phase0-20260510-200551` in `asia-northeast1-c`. Heartbeat sidecar fresh every 60s. Auto-shutdown
on completion.

**cefi audit complete (9min 29s)** —
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run`:

- **2.63M manifest rows total**, **1.29M captured-in-scope**, **2,223 phantoms** (up ~6× from the 354 workspace baseline
  for ALL asset_groups in the 2026-05-04 audit).
- **🚨 BIG FINDING per Findings Triage Discipline (case 5)**: phantom growth at 6× baseline for cefi alone is well above
  the >10× threshold this preaudit doc lists for "operator-notify + issue doc". The growth signal warrants: (a) operator
  review of whether the gcs_migration Phase 3 bundle's drift-axis sweeps will auto-resolve the bulk of the phantom mass
  (positive read: Phase 3 covers Axis 1/2/4/5; Axis 3 schema-4 empty venue is the residual); (b) Phase 6
  residual-cleanup sizing in `gcs_migration_bundle_pipeline_mode_2026_05_08.md` to be RE-ESTIMATED upward from the
  354-baseline assumption.

**Phantom distribution by `data_type`** (chain-bundle + derivatives concentration):

| data_type           | count | drift axis (per CLAUDE.md "Manifest phantom audit")    |
| ------------------- | ----: | ------------------------------------------------------ |
| `options_chain`     |   435 | Axis 5 (chain-bundle equivalence option↔options_chain) |
| `futures_chain`     |   401 | Axis 5 (chain-bundle equivalence future↔futures_chain) |
| `trades`            |   381 | Axis 1 (hive-vocab) or Axis 4 (path-prefix drift)      |
| `derivative_ticker` |   367 | Axis 1 or Axis 4                                       |
| `book_snapshot_5`   |   363 | Axis 1 or Axis 4                                       |
| `liquidations`      |   276 | Axis 1 or Axis 4                                       |

**Phantom distribution by `venue`** (Axis 3 schema-4 empty drift dominant):

| venue     | count | notes                                                                                                                                                                             |
| --------- | ----: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `(empty)` | 1,453 | **Axis 3 schema-4 empty `instrument_type` drift** (per CLAUDE.md "5 drift axes" list). Manifest column `instrument_type IS NULL OR instrument_type = ''` should match this count. |
| `DERIBIT` |   136 | Likely Axis 5 chain-bundle (DERIBIT options + futures legs)                                                                                                                       |
| `UNKNOWN` |   111 | Axis 1 hive-vocab fallback (`UNKNOWN` populated when neither `category=` nor `asset_group=` parsed)                                                                               |

**defi audit in flight at 88%** — 78,000/88,557 prefixes listed; 312,900 captured-in-scope rows. Final defi count will
land in the next `## Run results` append once VM completes.

**tradfi / sports / prediction queued** — sequential in the calibration script. Expected wall-clock per asset_group
~10-15min same-region; total run finish 2026-05-10 ~21:00 UTC.

**Phase 3 cost estimate (preliminary)**:

- cefi rate: ~129K rows/min listing+probe (`1.29M / 9.5min`).
- Extrapolating across 4-8 parallel migration VMs in-region with zero-egress: **<$500 total cost + 1.5-3hr aggregate
  wall-clock**. Aligns with this plan's preliminary estimate (Phase 3 line 343-346) within an order of magnitude; refine
  after full 5-asset_group calibration.

**Source**: Agent M (gcs-migration-phase0-calibration-tab) 2026-05-10 19:08-19:30+ UTC, code at
`deployment-service@08bc47c`.

**Recommended actions for next agent picking up gcs_migration Phase 3**:

1. Re-read this Run results section + the per-asset_group breakdown after VM completes.
2. Re-size Phase 6 residual-cleanup against the actual phantom count (likely 5-10K residuals across all 5 asset_groups,
   not the prior 354 estimate).
3. Confirm Axis 3 (schema-4 empty `instrument_type`) is in Phase 3's drift-axis sweep scope — 1,453 cefi phantoms have
   empty venue field; the bundle migrator must handle null/empty `instrument_type` columns gracefully.
4. Sample-inspect a handful of `options_chain` + `futures_chain` phantoms before bundling — confirm they're true Axis 5
   chain-bundle equivalence drift (option↔options_chain naming) vs genuine missing parquets.
