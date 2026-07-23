---
doc_type: issue
title: Bug-D-prime — Drift backfill VM silent data loss + bucket-name SSOT drift for sig index [SUPERSEDED 2026-06-01]
summary:
status: superseded
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-31
superseded: 2026-06-01
source:
  [
    "vm-log: gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log",
    mtds@7e09b2ab (fix),
    deployment-service@29f4bc4 (paired fix),
  ]
parent_epic: mtds_mdps_master
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
priority: P2
---

> **SUPERSEDED 2026-06-01.** The entire Helius sig-walking path this issue documents (sig-index VM loop, 28GB parquet,
> bucket-name SSOT drift between flat and `-prd` env-suffixed buckets, Bug 1/2/3 cascade) is **OBSOLETE for Drift V2
> historical**. Per `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` Phase 1, Drift V2 historical now flows
> via the **Drift Velocity Data API** (`data.api.drift.trade`, free tier, no auth) — the `DriftV2HistoricalIngester`
> shipped at mtds@0f70f376 + the `--live --continuous` flag at mtds@1d35c7f2.
>
> The sig-index infrastructure (`build_drift_v2_sig_index.py` + the 6293-part parquet on
> `gs://market-data-tick-defi-central-element-323112/_index/drift_v2_sig_index_parts/`) is COLD INFRASTRUCTURE — kept in
> the repo for potential future use (e.g., independent backfill of `tradeRecords` outside Velocity API rate limits) but
> NOT on any critical path. The `mtds-solana-drift-backfill` VM workflow is OBSOLETE; do NOT relaunch it.
>
> Full design: `/codex/04-architecture/drift-v2-data-sources.md` (NEW 2026-06-01). Operational follow-ups:
> `plans/active/defi_manifest_canonicalisation_2026_06_01.md` § G (Solana basis MVP operationalisation — G1 backfill VM,
> G2 live snapshotters, G3 paper trade, G4 live wallet promotion).
>
> No further work needed on this issue doc; it stays archived-in-place as historical record of the Bug-D saga (8 bug
> iterations 2026-05-29 → 2026-06-01) that motivated the design-before-code Velocity Data API discovery.

# Bug-D-prime — Drift backfill VM silent data loss + bucket-name SSOT drift

## What I found

The `mtds-solana-drift-backfill` VM (rebuilt with OOM fix at `mtds@e431e483` / underlying fix at `mtds@93acab34`)
self-exited at 2026-05-31 11:04Z with exit code 1 after 4 minutes. Root cause was TWO compounding bugs surfaced by the
operator-directed verify pass:

### Bug 1 — Missing `drift` in `PerpFundingHandler._chain_map`

`market_tick_data_service/cli/handlers/perp_funding_handler.py` had only `hyperliquid`/`aster`/`pacifica`/`lighter` in
`_chain_map`. When `--perp-protocols drift` was passed, `chain_for_manifest` defaulted to `""`. The `_build_row_key()`
call constructed `row_key={chain: ''}`, then `freshness_cache.is_now_skip_worthy(row_key)` invoked UTL `_coerce_row_key`
which raised `MalformedRowKeyError` (per Phase 4 hard schema enforcement).

### Bug 2 — `_build_row_key` + freshness lookup outside per-protocol try/except

The row_key construction and freshness lookup were on lines 300-306 BEFORE the `try:` block at line 325. So the
`MalformedRowKeyError` propagated up to the framework's per-payload outer catch (`_adapter.py:82-90`), which logged a
`WARNING` and incremented `failed` counter — but emitted **ZERO** `recorder.record_failed` calls for any of the 507
attempted dates. Pure silent data loss + double-violation of CLAUDE.md "Manifest + Honest Absence" hard rule.

### Bug 3 (discovered during verify) — bucket-name SSOT drift for Drift V2 sig index

The OOM-fix code reads sig index from `get_write_bucket_name("market_data", "DEFI")` =
`market-data-tick-defi-prd-${PID}` (prd-env-suffixed). But the parts/ uploads from the 2026-05-29 sig-index builder run
landed in `market-data-tick-defi-${PID}` (legacy, no env suffix). Result: VM correctly emits `attempted_failed` for
every date 2025-01-09 → 2026-05-30 (137 rows so far) with reason
`drift_v2_sig_index.parquet missing — build via build_drift_v2_sig_index.py`.

**Verified via**:

```bash
gsutil ls gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2*
# CommandException: One or more URLs matched no objects.
gsutil ls -l gs://market-data-tick-defi-central-element-323112/_index/drift_v2_sig_index_parts/ | head
# 9 parquet parts present from 2026-05-29 20:08Z
```

## Why it matters

- Bug 1+2 = the literal Bug-D-prime that wasted the 11:04Z VM run + ate operator's prior fix attempt. Now fixed;
  manifest correctly reflects per-date `attempted_failed` with typed error reason (honest absence).
- Bug 3 = real reason no rows are being captured even after Bug 1+2 fix. The sig index lives in the legacy bucket; the
  prd code can't see it. Without resolution, `arbitrage_price_dispersion` (DeFi archetype) cannot use Drift perp funding
  data for any date past 2025-01-08.

## What was shipped

- **`market-tick-data-service@7e09b2ab`** (live-defi-rollout):
  - Added `"drift": "SOLANA"` to `_chain_map`.
  - Moved `_build_row_key()` + `freshness_cache.is_now_skip_worthy()` inside the per-protocol try/except so any
    setup-time exception (including MalformedRowKeyError, a `ValueError` subclass) routes through
    `recorder.record_failed` → manifest `attempted_failed`.
  - Two new regression tests in `tests/unit/test_perp_funding_handler.py`: `test_drift_chain_for_manifest_is_solana` +
    `test_malformed_row_key_routes_to_record_failed`. Full suite 24 pass / 1 skip.

- **`deployment-service@29f4bc4`** (live-defi-rollout):
  - `scripts/vm/setup-data-pipeline-vm.sh` `VM_TASK=solana-drift-backfill` now routes to
    `--operation collect-solana-defi --solana-drift-backfill --solana-drift-market $VM_DRIFT_MARKET` (i.e.
    `SolanaDefiHandler`), NOT `--operation collect-perp-funding --perp-protocols drift`. Reverts the misinformed 9962fe9
    (which assumed `collect-solana-defi` was deleted in Gate 5 — only the `full-defi-backfill.sh` wrapper was retired;
    the CLI op is intact in MTDS `cli/main.py:436`).

- New MTDS + deployment-service tarballs uploaded
  (`gs://deployment-scripts-central-element-323112/code/mtds-code@7e09b2ab*`
  - `…/deployment-service-code@29f4bc4*`). VM `mtds-solana-drift-backfill` relaunched at 2026-05-31 11:43Z, RUNNING.

## Verify outcome (2026-05-31 11:47Z)

| Criterion                                         | Result                                        |
| ------------------------------------------------- | --------------------------------------------- |
| VM status RUNNING at T+10min                      | ✓ Pass                                        |
| No `MalformedRowKeyError` warnings in new run.log | ✓ Pass                                        |
| Manifest rows carry `chain='SOLANA'`              | ✓ Pass (137/137 rows)                         |
| Manifest rows carry honest `capture_status`       | ✓ Pass (`attempted_failed` with typed reason) |
| ≥5 of first 10 dates with `record_captured`       | ✗ Fail (0 captured)                           |
| ≥1 parquet for `day=2025-08-01` row_count > 0     | ✗ Fail (no parquets written)                  |

**Pass on Bug-D-prime (1+2); fail on Bug 3 (bucket-SSOT for sig index).**

## Status update — Drift sig-index gap-fill walk launched (2026-05-31 21:52Z)

- **State**: Bug-3 buckets are now in sync (prd + legacy both mirror the same `_index/drift_v2_sig_index_parts/` +
  `_parts_b/`), but the sig-index parts collectively cover only `2024-10-31 → 2025-01-15` (`_parts_b/`, 876 parts) +
  `2026-02-06 09:50:47 → 2026-05-29 HEAD` (`_parts/`, 3547 parts). The **12-month gap 2025-01-15 → 2026-02-06** means
  the in-flight Drift backfill VM `mtds-solana-drift-backfill` (RUNNING since 11:43Z on tarball `mtds@7e09b2ab`)
  correctly emits `record_failed(reason="sig index missing")` for every 2025 date — honest absence, no silent loss, but
  no captured rows either.
- **Gap-fill walk launched 2026-05-31 22:52Z** on fresh ephemeral GCE VM
  `mtds-solana-drift-backfill-sigidx-20260531-225220` (`e2-standard-4`, `asia-northeast1-c`, `EPHEMERAL_BATCH`,
  `VM_SHUTDOWN_ON_COMPLETION=true`). Fallback path — vm-ml SSM was Online-but-silently-failing (`echo hello` succeeded
  once, then everything Failed empty even post-reboot), so ephemeral GCE VM per operator-brief fallback.
- **Workload**: canonical `setup-data-pipeline-vm.sh` + `VM_TASK=mdps-backfill`
  - `VM_BACKFILL_CMD="python -m market_tick_data_service.scripts.build_drift_v2_sig_index --back-to 2025-01-14 --chunk-size 100000 --resume"`.
    The script's `--resume` reads existing `_parts/` (default prefix; 3547 parts), finds the oldest signature
    (oldest=2026-02-06 09:50:47), seeds `before=<oldest_sig>` and walks back, writing new parts as
    `part-003547+.parquet`. ETA 6-12h.
- **Operator poll command**:
  ```bash
  gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill-sigidx-20260531-225220/mdps-backfill.log 2>/dev/null | tail -40
  ```
- **CHAIN_COMPLETE signal**: VM auto-shuts-down on script exit (`VM_SHUTDOWN_ON_COMPLETION=true`). To verify completion:
  ```bash
  gcloud compute instances describe mtds-solana-drift-backfill-sigidx-20260531-225220 \
    --zone=asia-northeast1-c --format='value(status)'
  # Expected: TERMINATED (auto-shutdown). Then verify parts cover 2025:
  gsutil ls gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index_parts/ | wc -l
  # Expected: > 3547 (probably 4500-5500).
  ```
  Once parts cover the gap, the running `mtds-solana-drift-backfill` VM transitions from `attempted_failed` → `captured`
  for 2025 dates without restart (handler reads on each per-date `_load_drift_v2_sig_index` call). At that point flip
  **Bug-D ✅** in the next operator turn after re-verifying ≥5 of first 10 2025 dates capture > 0 rows.
- **Do NOT** touch the running `mtds-solana-drift-backfill` VM, the consolidator workstream, or the probe — all running
  cleanly.

## Recommended decision

Two ops, in order:

1. **P0 — `gcs_copy_object` the Drift V2 sig-index parts/ from legacy bucket to prd bucket** (single-walk, ~100 MB).
   After copy, the existing prd VM resumes data capture without restart (handler reads on each per-date
   `_load_drift_v2_sig_index` call).

   ```bash
   gsutil -m rsync gs://market-data-tick-defi-central-element-323112/_index/drift_v2_sig_index_parts/ \
     gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index_parts/
   # Same for drift_v2_sig_index_parts_b/ and drift_v2_sig_index_parts_gap/
   ```

2. **P0 — Workspace-wide bucket-SSOT drift audit for `_index/` files.** Other handler-managed indices
   (availability_index.parquet, per_vm/, snapshots/) may have the same prd-vs-legacy split. Confirm + lift all of them
   in one pass to avoid recurring silent-coverage incidents.

## Side-discoveries (P2/P3 hardening backlog — NOT TODO-FLIPPED HERE)

Surfaced during this incident, captured per CLAUDE.md "Capture Discoveries As Plan Todos Immediately" hard rule:

- [ ] [INFRA] P2. **Stale EXIT_STATUS sentinel** at
      `gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/EXIT_STATUS` remained from
      prior failed VM and would have blocked the relaunch flow if not manually cleaned. Add per-launch sentinel-cleanup
      to `deployment-service/scripts/vm/launch-mtds-solana-drift-backfill-vm.sh` (and standardise across all VM
      launchers via `lib/launcher_common.sh`).

- [ ] [INFRA] P3. **Watchdog silence on 4-min self-exit.** The 11:04Z VM ran 4 minutes then exited with status=failed
      exit_code=1. No alert fired. The `vm_zombie_watchdog.py` lifecycle classification (EPHEMERAL_BATCH) should treat
      "exit with non-zero rc AND zero `record_captured` emissions in same run" as an automatic high-pri operator ping
      (handler-broken signal, not normal completion).

- [ ] [INFRA] P2. **Manifest consolidator 11-day staleness.** The consolidated `_index/availability_index.parquet` in
      the prd DeFi bucket is not being refreshed on schedule (most recent 2026-05-20 vs today 2026-05-31). Either Cloud
      Run Job + Scheduler is failing silently, or the per-VM shards aren't being collected. Composes with
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` runbook.

- [ ] [INFRA] P3. **Cloud Run stdout truncation symptoms.** The recent burst of subgraph-probe debug commits (`75034c18`
      → `e431e483`) was caused by Cloud Run gen2 swallowing stdout exception traces. Solution shipped at `e431e483` (UTL
      upload_bytes mirror). Codify the diagnostic pattern in `/codex/05-infrastructure/cloud-run-job-gen2-quirks.md` so
      the next agent doesn't repeat the trial-and-error sequence.

## Composed with

- CLAUDE.md HARD RULE "Manifest + Honest Absence" (Bug 1+2 root cause).
- CLAUDE.md HARD RULE "Shard-level failure isolation" (try/except scope).
- CLAUDE.md HARD RULE "Bucket-name SSOT" (Bug 3 root cause).
- CLAUDE.md HARD RULE "Plans Run To Actual Completion" — VM relaunched + manifest-verified, but Bug 3 keeps zero rows
  captured.
- `/codex/02-data/data-pipeline-correctness-hard-rule.md`.

## Status update 2026-06-01T00:14Z — gap-fill VM #3 launched after --resume OOM fix

- **Fix shipped**: `mtds@8b9477f3` — `_load_parts_summary` uses metadata-only two-pass. Pass 1: `pq.read_metadata(...)`
  row-group statistics across all 3547 existing parts to find the global oldest blockTime (no row materialization). Pass
  2: materialize ONLY the single part containing that global min to extract its signature. Constant memory regardless of
  part count. Replaces the prior `pd.read_parquet()` full-load loop that silently OOM-killed the gap-fill VM #2.

- **Gap-fill VM #3**: `mtds-drift-sigidx-gapfill-20260601-001358` (e2-standard-4, asia-northeast1-c, 35.243.119.40),
  created `2026-06-01T00:14:01Z`. Launched via inline `gcloud compute instances create` (no canonical launcher exists
  for this task shape — VM_TASK=mdps-backfill + VM_BACKFILL_CMD metadata).
  - `VM_TASK=mdps-backfill` routes through setup-data-pipeline-vm.sh:1004 which reads VM_BACKFILL_CMD from instance
    metadata.
  - `VM_BACKFILL_CMD="python -m market_tick_data_service.scripts.build_drift_v2_sig_index --back-to 2025-01-14 --chunk-size 100000 --resume"`
  - `VM_SHUTDOWN_ON_COMPLETION=true` — auto-deletes on script exit.
  - Tarball SHA verification: `mtds-code@8b9477f3.tar.gz` confirmed uploaded to
    `gs://deployment-scripts-central-element-323112/code/` at 00:04:46Z, manifest `git_status_clean: true`.

- **Drift backfill VM `mtds-solana-drift-backfill`**: unchanged, still RUNNING + honestly emitting
  `record_failed(reason="sig index missing")` for 2025 dates per the honest-coverage fix (mtds@7e09b2ab). Transitions to
  `record_captured` automatically when the gap-fill walk completes + parts land on GCS (handler reads per-date via
  `_load_drift_v2_sig_index` which globs both `_parts/` and `_parts_b/`).

- **On gap-fill completion** (~6-12h wall-clock per prior rate observations): VM auto-deletes
  (VM_SHUTDOWN_ON_COMPLETION=true). Verify via:
  - `gcloud compute instances describe mtds-drift-sigidx-gapfill-20260601-001358 ...` → TERMINATED
  - `gsutil ls _index/drift_v2_sig_index_parts/ | wc -l` → > 4423 (new parts past 3547)
  - Sample-check `gsutil ls .../day=2025-08-01/.../venue=DRIFT/` → rows > 0
  - If yes → flip Bug-D parent + Bug-D-followup ✅ in `plans/active/solana_defi_legacy_migration_2026_05_27.md`.

- **Poll command**:

  ```
  gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-drift-sigidx-gapfill-20260601-001358/run.log 2>/dev/null | tail -20
  ```

- **Hardening todos still open** (filed earlier this session, do not auto-flip):
  - P0: bucket SSOT drift across other indices
  - P2: VM bootstrap should clear stale EXIT_STATUS
  - P2: manifest consolidator 11-day staleness on DeFi bucket
  - P3: VM watchdog log-uploader silence detection
  - P3: Cloud Run gen2 + slim image STDOUT truncation
