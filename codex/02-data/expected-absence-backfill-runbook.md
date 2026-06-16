---
scope: [engineer, admin]
title: Expected-Absence Backfill Runbook
status: shipped
created: 2026-05-07
last_reviewed: 2026-05-17
execution:
  owner: "UTL maintainer (honest_coverage subsystem)"
  cadence: "per asset_group, one-shot post writegate Phase 5; re-run on legacy null-reason discovery"
  verifier: "python3 -m unified_trading_library.honest_coverage.classify_legacy_empty_row --dry-run --asset-group <ag>"
  last_executed: "writegate Phase 5 closeout (per per-asset-group reconciler runs in writegate plan body)"
authoritative_for:
  Per-asset-group runbook for back-filling `record_expected_empty(reason=...)` rows over legacy null-reason manifest
  entries AND for enumerating the structurally-empty universe (chain pre-genesis / venue pre-launch / source
  pre-coverage / non-trading-day) that has no manifest row at all. Pairs the on-the-fly UTL
  `classify_legacy_empty_row()` helper with two batch passes that materialise the closed-set `EXPECTED_<REASON>`
  taxonomy on disk.
referenced_by:
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
related:
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/manifest-migration-coordination.md
last_reviewed: 2026-05-17
---

# Expected-Absence Backfill Runbook

> **Status:** SHIPPED — Phase 3.D.4 enumerator + 3.D.1 reconciler ran across all 5 asset_groups 2026-05-07
> (PM@79e47874 + PM@341bb285). 1,455,901 enumerator rows landed; per-VM shards merged 18:07-18:14 UTC. Quarterly re-run
> cadence applies thereafter.

## Purpose

The reader-side UTL helper `classify_legacy_empty_row()` (shipped UTL@c5c2669e) classifies legacy null-reason rows
on-the-fly so deployment-api never returns an unclassified `empty_confirmed`. That's a runtime fallback — the canonical
fix is to materialise a real `error_reason` on disk. This doc is the runbook for executing the two batch backfills that
drive on-disk honesty: the **reconciler** stamps reasons on existing legacy rows, and the **enumerator** writes new rows
for tuples that never had a manifest entry at all.

## Two complementary passes

### Pass 1 — Reconciler (`reconcile_expected_absence_reasons.py`)

Stamps a typed `error_reason` on rows where `capture_status=empty_confirmed AND error_reason IS NULL`.

- Code: `instruments-service/scripts/reconcile_expected_absence_reasons.py` (Tier 3D.1, shipped 2026-05-07
  instruments-service@1f93745).
- Per-asset-group classifier dispatch lifted into UTL `classify_legacy_empty_row()` (Tier 3D.2, shipped UTL@c5c2669e);
  reconciler imports from UTL — no inline duplicate.
- Default scan-only; `--apply-flips` requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>`.

### Pass 2 — Enumerator (`enumerate_expected_universe.py`)

Walks the cross-product `(asset_group catalog) × (data_types) × (dates_in_window)`, identifies tuples with NO manifest
row, and writes `record_expected_empty(reason=EXPECTED_<X>)` for the structurally-empty cases (chain pre-genesis, venue
pre-launch, source pre-coverage, non-trading-day). This is what closes the rollup-vs-drilldown denominator gap.

- Code: `instruments-service/scripts/enumerate_expected_universe.py` (Phase 3.D.4, shipped 2026-05-07
  instruments-service@8e404c8 / @d1c9928 / @a936a28).
- Launcher: `deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh` (deployment-service@dcc5c87 /
  @38b7a58 with `--max-writes-per-run` cap pass-through).
- Default scan-only (CSV report); `--apply-write` requires the same per-VM shard isolation envvars.

## Per-asset-group volume + invocation order

Run order is TradFi → Sports → CeFi → Prediction → DeFi (cheapest first; DeFi last because it dominates volume). Single
VM per asset_group; consolidator merges per-VM shards into canonical within ~5 min of VM shutdown.

| Asset group | Enumerator rows (2026-05-07 sweep) | Top reason mix                                                                  |
| ----------- | ---------------------------------: | ------------------------------------------------------------------------------- |
| TradFi      |                             35,033 | 32,825 `EXPECTED_WEEKEND` + 2,208 `EXPECTED_HOLIDAY`                            |
| Sports      |                             13,176 | 13,176 `EXPECTED_PRE_SOURCE_COVERAGE_START`                                     |
| CeFi        |                            119,152 | 119,152 `EXPECTED_PRE_VENUE_LAUNCH` (real impl per UAC@ac218dc, 13 venues)      |
| Prediction  |                              2,280 | 2,280 `EXPECTED_PRE_VENUE_LAUNCH` (974 POLYMARKET + 1,306 KALSHI)               |
| DeFi        |                          1,286,260 | 688,220 `EXPECTED_PRE_GENESIS_CHAIN` + 598,040 `EXPECTED_INSTRUMENT_NOT_LISTED` |
| **Total**   |                      **1,455,901** |                                                                                 |

## Invocation recipe

### Scan-only (default — no manifest mutation)

```bash
bash deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh tradfi
# capture VM_NAME from stdout, e.g. expected-universe-enum-tradfi-{ts}
sleep 90
gcloud storage ls gs://central-element-323112-events/events/instruments-service/$(date -u +%Y-%m-%d)/expected-universe-enum-tradfi-*/
# verify ENUMERATOR_STARTED event landed within 90s
```

### Apply-write (after operator review)

```bash
# default cap is 1M; bump per-asset-group when the universe genuinely exceeds it (DeFi did, used 5M).
bash deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh defi --apply-write 5000000
# launcher injects MANIFEST_PER_VM_SHARDS=true + VM_NAME=<unique-tag> automatically.
# wait for ENUMERATOR_COMPLETED event with written>0
```

### Verification

After each VM shutdown:

1. **Per-VM shard exists**:
   `gcloud storage ls gs://market-data-tick-{asset_group}-{env}-{pid}/_index/per_vm/expected-universe-enum-{asset_group}-*.parquet`
2. **Consolidator merge**: within ~5 min, the per-VM shard rows are visible in
   `gs://market-data-tick-{asset_group}-{env}-{pid}/_index/availability_index.parquet`.
3. **Spot-check on the canonical manifest**:
   ```python
   import pandas as pd
   df = pd.read_parquet("gs://market-data-tick-tradfi-prd-{pid}/_index/availability_index.parquet")
   weekend = df[df["error_reason"] == "EXPECTED_WEEKEND"]
   assert len(weekend) > 0
   sample = weekend.iloc[0]  # e.g. venue=BARCHART day=2018-01-06 (Saturday) — correct
   ```
4. **deployment-ui rollup-vs-drilldown panel**: percentages should agree within rollup cache TTL (default 5 min) for the
   asset_group whose `--apply-write` just landed.

## Operational hazards (lessons from 2026-05-07 sweep)

- **Default `--max-writes-per-run` cap of 1M is right-sized for tradfi / sports / cefi / prediction**. DeFi routinely
  exceeds 1M (true universe ~1.286M); the launcher's third positional arg passes `--max-writes-per-run` through, e.g.
  `5000000` for the May-7 DeFi run.
- **Per-VM shard isolation is non-negotiable for apply-write**. Without `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=...`,
  `ManifestWriter.__init__` raises `MultiWorkerWithoutShardIsolationError`. The launcher injects both correctly.
- **Schema drift can break consolidator merge**. Phase 3.D.4 hit a P0
  (`ArrowTypeError: Expected bytes, got a 'int' object` on the `instrument_count` column) because the enumerator was
  filling missing canonical columns with empty string regardless of dtype. Fix shipped at instruments-service@a936a28
  (per-column dtype inspection + type-appropriate nullable defaults: `Int64` / `Float64` / `boolean` / `datetime64`).
  Resolved-issue tracking: `plans/active/issues/manifest_consolidator_arrow_typeerror_2026_05_07.md` (PM@341bb285).
- **VMs auto-shutdown on completion** (`VM_SHUTDOWN_ON_COMPLETION=true`) so SSH-tail is impractical for verifying the
  run; rely on the events stream + the per-VM shard's manifest rows after consolidation.
- **CSV report is local-only by default** — the script writes to `tempfile.gettempdir()` on the VM, which dies with the
  VM at shutdown. The events log captures the distribution-by-reason summary, but row-by-row inspection requires either
  SSH-before-shutdown (race) or the optional `--gcs-report-bucket` flag (Phase 3.D.4 follow-up [SCRIPT] P1).

## Cross-references

- **Plan(s) implementing this:**
  [`writegate_honest_coverage_endtoend`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) § Phase
  3.D.4 (enumerator) + § Phase 3.D.1/3.D.2 (reconciler).
- **Related codex SSOTs:** [`honest-absence-downstream-handling`](./honest-absence-downstream-handling.md),
  [`availability-manifest-and-data-status`](./availability-manifest-and-data-status.md) § "Rollup-vs-drilldown
  denominator divergence" Half 2, [`manifest-migration-coordination`](./manifest-migration-coordination.md).
- **Code:** `instruments-service/scripts/enumerate_expected_universe.py` (Phase 3.D.4 enumerator),
  `instruments-service/scripts/reconcile_expected_absence_reasons.py` (Phase 3.D.1 reconciler),
  `unified-trading-library/legacy_reason_classifier.py` (UTL classifier dispatch),
  `deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh` (launcher).

## Re-run cadence

- **Reconciler**: quarterly. New `empty_confirmed AND error_reason IS NULL` rows should not appear once Phase 2.E.2
  orchestrator pre-skips emit `record_expected_empty(reason=...)` directly. The reconciler is a safety-net, not a
  primary path.
- **Enumerator**: quarterly OR after any structural change (new venue listing, new chain, new source onboarding,
  data-type rollout). The cross-product changes only when one of those axes evolves.

## Open follow-ups

- **CSV report upload to GCS before VM auto-shutdown** ([SCRIPT] P1, Phase 3.D.4 follow-up). Add `--gcs-report-bucket`
  to the script + launcher pass-through. Low priority because the events log captures the distribution; only needed if
  the operator wants to inspect specific candidate rows.
- **Per-asset-group unit tests** ([TEST] P0, Phase 3.D.4) — at least one fixture-based test per asset_group (TradFi
  calendar / DeFi chain-genesis / Sports source-coverage / CeFi venue-launch / Prediction venue-launch). Tracks under
  instruments-service tests/.
- **CeFi v2 fine-grained instrument lifecycle** (Phase 3.D.5) — current enumerator covers `EXPECTED_PRE_VENUE_LAUNCH`
  only; per-instrument `EXPECTED_INSTRUMENT_NOT_LISTED` / `EXPECTED_INSTRUMENT_DELISTED` requires the
  instruments-service catalog with per-instrument `available_from` / `available_to` / `expiry`. Tracked under
  `cefi_master.md`.
- **Prediction v2 per-(canonical_question_group, day)** (Phase 3.D.5) — blocked on UAC `PREDICTION_GROUPS` registry per
  `predictions_master.md`.
- **Sports per-league enumeration** (Phase 3.D.4 deferred) — current covers source-coverage-start; per-league granular
  enumeration needs sports-leagues catalog read. Tracked under `sports_master.md`.
