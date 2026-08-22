---
doc_type: issue
title: "cefi consolidated availability_index stale >37h — consolidator refusing an unprovable 109k-shard merge (marker stripped by an out-of-band rewrite 2026-08-20T19:29Z)"
summary: >-
  gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet was last written
  2026-08-20T19:29:17Z by an out-of-band rewrite that stripped the consolidator_content_write_at marker (custom
  metadata now empty). Every uts-prod-manifest-consolidator-market-data-cefi execution since fails closed with
  marker_missing_oversized_merge (109,341 per-VM shards > the 50,000 cron cap), exit 1, ~every 15 min. No cefi
  manifest row captured since then is visible in the consolidated index; every cefi VM launch whose setup-script
  OOM-preflight checks the cefi index (default asset group when a launcher omits VM_ASSET_GROUP) dies rc=78.
  Found 2026-08-22 08:28Z while launching a DEFI one-off VM.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-trading-library, deployment-service]
scope: [engineer]
tags: [manifest-consolidator, cefi, stale-index, marker-strip, data-pipeline, incident]
related:
  - /plans/active/cefi_consolidated_closeout_2026_07_18.md
  - /codex/05-infrastructure/manifest-consolidator-ssot.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md
  - /plans/active/defi_distinct_values_canonical_cleanup_2026_08_21.md
created: 2026-08-22
author: slot-3 defi distinct-values cleanup session (/autonomous)
source: setup-data-pipeline-vm.sh §5b OOM-preflight rc=78 on mtds-defi-blanket-perp-stamp-purge; Cloud Run job logs
parent_epic: cefi_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
  ]
---

# cefi consolidated index stale >37h — consolidator fail-closed on an unprovable 109k-shard merge (2026-08-22)

> **Codex SSOT**: /codex/05-infrastructure/manifest-consolidator-ssot.md — § "There is NO fallback for the prune
> cutoff" (a stripped `consolidator_content_write_at` marker = UNPROVABLE → merge everything, prune nothing) and the
> `_UNPROVABLE_MERGE_MAX_SHARDS` cron cap (an unprovable merge > 50,000 shards is refused on the cron; sanctioned
> recovery = `consolidate(bucket, force=True)` on a big-RAM host, or a safe marker restore).

## Measured (2026-08-22, all via UTL `get_storage_client` / `gcloud run` / `gcloud logging`)

- `_index/availability_index.parquet` (cefi prd): `last_modified=2026-08-20T19:29:17.669Z`, size 469,897,537,
  generation 1787254157655029, **custom metadata = None** (no `consolidator_content_write_at`, no
  `consolidator_run_at`). 133,134s stale at 08:28Z (setup-script preflight budget 86,400s).
- Cloud Run job `uts-prod-manifest-consolidator-market-data-cefi` (asia-northeast1): executions at 07:36Z, 07:51Z,
  08:01Z, 08:36Z … all `failedCount=1`, container exit 1. Cron `…-cefi-cron` ENABLED, schedule `0 * * * *`,
  last attempt 08:00:09Z (the sub-hourly executions are retries / a second trigger — not diagnosed).
- Execution `…-94mgh` log (08:01Z): `phase=shards_listed shards=109342` → `WARNING … canonical … has NO
  consolidator_content_write_at marker (out-of-band rewrite?) — merge cutoff UNPROVABLE` → `CRITICAL … fail-closed
  merge spans 109341 per-VM shard(s) (> 50000) — refusing to run a corpus-wide merge on the cron` →
  `success=False … error=marker_missing_oversized_merge` → `Container called exit(1)`.
- Consequence 1 (data): no cefi per-VM shard written after 2026-08-20T19:29Z is consolidated; 109,341 shards are
  pending (none pruned — by design, the fail-closed path never drops a shard). Every consumer of the cefi consolidated
  index (data-status UI/API, honest-coverage rollup, expected-universe gates) is reading a ≥37h-old view.
- Consequence 2 (infra): `setup-data-pipeline-vm.sh` §5b OOM-preflight kills (rc=78, self-delete) any
  `market_tick_data_service` VM whose resolved asset group is CEFI — including any Pattern-A one-off launcher that
  omits `VM_ASSET_GROUP` (defaults to CEFI). Measured on `mtds-defi-blanket-perp-stamp-purge` attempt 1
  (`vm-logs/<vm>/vm-setup.log`); fixed for that launcher by setting `VM_ASSET_GROUP=DEFI`.

## Root cause

An out-of-band rewrite of the cefi `_index` at 2026-08-20T19:29:17Z (writer NOT identified — candidates are the
cefi one-offs / apply VMs active that evening; a plain CAS upload via the sanctioned helpers strips custom metadata,
SSOT § "Gotcha, confirmed 2026-07-21"). The strip itself is designed to cost one full merge, never loss — but the
cefi shard backlog (109k) exceeds the cron's 50k unprovable-merge cap, so the self-heal cannot run on the cron.

## Todos

- [ ] [OPERATOR] P1. 1. **Decide the recovery path and run it**: (a) `consolidate(bucket, force=True)` through the
      consolidator CLI `main()` (NOT a bare `consolidate()` call — SSOT § "Correction (2026-07-26)": missing
      `setup_events()` / `no_op_lock` both silently no-op) on a big-RAM in-region VM (precedent: the 2026-08-19 172k-shard
      recovery cited in `manifest_consolidator.py` next to `_UNPROVABLE_MERGE_MAX_SHARDS`), or (b) a safe marker restore
      (re-stamp `consolidator_content_write_at` = the last PROVEN merge time, which must be ≤ the rewrite's own shard
      cutoff — only if that time is known; otherwise (a)). Pause the cefi cron for the duration; verify
      `custom_fields.consolidator_content_write_at` present + `success=True rows_in>0` + the next ≥4 cron cycles green.
- [ ] [SCRIPT] P2. 2. **Identify the 2026-08-20T19:29Z writer** (bucket audit log / the cefi apply-VM run.logs of that
      evening) and make that writer re-stamp via the sanctioned path (SSOT: run the consolidator CLI `--force` in the
      same operation as any CAS index write). (repo: market-tick-data-service)
- [ ] [INFRA] P2. 3. **Pattern-A launchers must set `VM_ASSET_GROUP` explicitly** (the §5b preflight default is CEFI) —
      audit `deployment-service/scripts/vm/launch-*-vm.sh` with `VM_TASK=canonical-migration` and add the key where
      absent (`launch-perp-funding-manifest-restamp-vm.sh` is one). (repo: deployment-service)
- [ ] [INFRA] P3. 4. **Alert bookend**: `MANIFEST_CONSOLIDATION_FAILED` severity=ERROR fires every ~15 min for cefi —
      confirm it is reaching the data-pipeline-alerts channel with state-transition dedup (not 4×/h), per
      /codex/05-infrastructure/data-pipeline-alerts.md. (repo: deployment-service)

## Progress Log

- **2026-08-22 ~09:50 London (slot 3, filed while executing the DeFi distinct-values cleanup)** — measured as above;
  NOT acted on beyond filing (cefi scope, multi-hour prod merge → operator decision). The DeFi index is NOT in this
  state: its consolidator executions at 08:20-08:23Z succeeded (defi shard count is under the 50k cap, so the
  marker-strip self-heal can run on the cron).
