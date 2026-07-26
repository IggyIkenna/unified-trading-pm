---
doc_type: plan
title: Fix dex-pools subgraph symbol-resolution bug, backfill, purge superseded/orphaned DeFi historical data
summary:
  Operator decision 2026-07-25 -- delete the bad unattributed TRADER_JOE_V2/VELODROME_V2/CURVE dex_pool_state data, fix
  the subgraph-query bug that caused it (see issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md),
  then re-backfill with proper symbols. Also purge the orphaned lst_rates `_migrated_*` markers
  (COINBASE/MAKER/SWELL/ETHENA) -- superseded by the current canonical RPC-based lst_rates_handler.py capture
  (re-derivable from any historical block on demand) or, for MAKER/ETHENA, already reclassified into
  vault_share_price_handler.py.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [defi, subgraph, symbol-resolution, dex-pools, lst-rates, backfill, cleanup]
related:
  [
    defi_consolidated_closeout_2026_07_18,
    defi_migrated_marker_flagged_root_cause_clusters_2026_07_25,
    defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25,
  ]
created: 2026-07-25
last_updated: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on: []
source:
  [
    "operator decision 2026-07-25, made during a /autonomous session's FLAGGED-marker root-cause investigation -- 'seems
    best thing is to delete the bad data, purge manifest then and fix the query and re-backfill' for the
    TRADER_JOE_V2/VELODROME_V2/CURVE cluster, and 'orphaned ones are artifacts again to purge from manifest and gcs
    data' for the lst_rates cluster",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Fix dex-pools subgraph symbol bug, backfill, purge orphaned data

## Context (read before dispatching any todo)

Two independent findings from the 2026-07-25 FLAGGED-marker investigation, both operator-decided the same way (purge the
bad/orphaned data, keep only what's canonical going forward):

1. **dex_pools_handler.py's `messari_basic` query** (used by curve/sushiswap/velodrome_v2/trader_joe_v2 -- gmx is
   excluded here, it is being removed entirely by `defi_gmx_venue_removal_2026_07_25.md`) never requests
   `inputTokens { symbol }` from the subgraph -- full analysis in
   `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md`. This produced years of unattributed
   (address-keyed) `dex_pool_state` data for these venues, both the old `_migrated_*` markers AND (for CURVE
   specifically, confirmed live) still-current address-keyed leaves.
2. **lst_rates** `_migrated_*` markers for COINBASE/SWELL/MAKER/ETHENA are all legitimate-but-orphaned single-row
   snapshots -- the CURRENT canonical `lst_rates_handler.py` captures via direct on-chain RPC `eth_call` at a
   _historical block number_, meaning any past date's rate is exactly re-derivable on demand from the (permanent)
   blockchain state -- these old markers have no unique irreplaceable content worth preserving. MAKER/ETHENA
   (sDAI/sUSDe) are additionally obsolete: reclassified out of `lst_rates` into `vault_share_price_handler.py` by a
   2026-07-23 fix already shipped.

**This plan is `sequential: true`** -- todos 2-5 form a genuine dependency chain (fix the query before backfilling,
backfill before purging the now-superseded old data); todo 1 (lst_rates purge) is independent but placed first since it
is quick and doesn't block anything.

## Todos

- [ ] [OPERATOR] P2. **Purge orphaned lst_rates `_migrated_*` markers** for COINBASE/SWELL/MAKER/ETHENA (all
      `raw_tick_data/**/venue={COINBASE,SWELL,MAKER,ETHENA}/**/data_type=lst_rates/_migrated_*.parquet` objects) + their
      manifest rows, in `market-data-tick-defi-prd-central-element-323112`. **Corrected 2026-07-25**: venue segments are
      UPPERCASE in real GCS paths (canonical convention, confirmed by direct listing) -- the original lowercase glob
      here would have matched zero real objects. Prod-bucket delete, human-gated per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- no agent runs this. **BLOCKED-DATA-CORRECTNESS
      (2026-07-25 five-part-proof, disposition `no-migrate-first`)**: NOT safe to execute yet, independent of the casing
      fix above. Two real blockers found: (1) a LIVE, unfiltered reader --
      `features-service/features_service/onchain/app/core/data_loader.py:121-138` (`_probe_mtds_blobs`) -- currently
      matches `_migrated_*.parquet` objects (no underscore-prefix exclusion), wired into production via
      `onchain/engine/orchestrator.py:462,877`; (2) sampled canonical-twin coverage is only 91% (COINBASE 76% / MAKER
      92% / ETHENA 96% / SWELL 100%), short of the required 100% before any asset_group's delete list executes. Full
      evidence + the reader-bug issue doc: `unified-trading-pm@72d40de44`
      (`issues/defi_lst_rates_migrated_marker_unfiltered_live_reader_2026_07_25.md`). **Sequencing**: fix the reader
      filter first, re-verify coverage, THEN this purge can move to `yes-after-verify`. Done-when: zero `_migrated_*`
      lst_rates markers remain for these 4 venues in GCS or the manifest. (repo: market-tick-data-service) **UPDATE
      2026-07-26 (blocker 2 CLOSED, blocker 1 already CLOSED)**: the reader-fix (blocker 1) shipped 2026-07-25
      (`features-service@69753a7c88ba2d33b2def282632ce853d3739dee`, see the issue doc). The twin-coverage gap
      (blocker 2) is now ALSO closed by a fold-not-purge one-off (agent-executable per delete-safety-protocol § 5 --
      copy-only, never deletes) run on an in-region SPOT VM (`canonical-migration-defi-lst-rates-fold-20260726-003855`,
      `market-tick-data-service@9150bc9fae4fe71b1961f4c46ed1c01933b6df5c`): all 346 previously-FLAGGED markers were
      folded (rc=0) and independently RE-VERIFIED (not sampled -- all 346, via the sanctioned `verify_marker()` oracle)
      to now read `SAFE`. Exact per-venue twin coverage, before -> after:

      | Venue    | Total markers | FLAGGED (before) | Coverage before | FLAGGED (after) | Coverage after |
          | -------- | ------------- | ----------------- | --------------- | ----------------- | -------------- |
          | COINBASE | 1623          | 202                | 87.55%           | 0                  | **100.00%**    |
          | MAKER    | 1276          | 132                | 89.66%           | 0                  | **100.00%**    |
          | SWELL    | 1192          | 5                  | 99.58%           | 0                  | **100.00%**    |
          | ETHENA   | 975           | 7                  | 99.28%           | 0                  | **100.00%**    |

          "Total markers" = every `_migrated_*` lst_rates object for that venue (server-side `match_glob` listing over
          the FULL 2020-2026 range, independent of the marker-cleanup VM's own scan progress). All 4 venues are now at
          genuine 100% verified twin coverage -- the disposition can move from `no-migrate-first` to `yes-after-verify`
          for the PURGE half of this todo. **The purge itself remains un-executed and un-checked** (prod-bucket delete,
          human-gated, per this doc's own hard scope -- an agent folds, a human deletes). Full detail (VM name/zone/mode,
          resume-log caveat, 12-leaf spot-check): this plan's Progress Log below.

- [ ] [BACKEND] P1. **Fix the `messari_basic` subgraph query** in
      `market_tick_data_service/cli/handlers/dex_pools_handler.py` -- add `inputTokens { symbol }` (and
      `fees {     feePercentage feeType }` to match `_MESSARI_DEX_QUERY`'s shape) to
      `_CURVE_QUERY`/`_CURVE_QUERY_FILTERED`, and switch `curve`/`sushiswap`/`velodrome_v2`/`trader_joe_v2` (NOT `gmx`
      -- see context above) in `_dex_pools_subgraph.py`'s protocol table from `self._parse_curve` to
      `self._parse_messari_dex`. Verify the Messari `liquidityPoolDailySnapshots` schema actually exposes `inputTokens`
      uniformly across all 4 subgraphs before assuming this is a drop-in change. Done-when: a live test query against
      each of the 4 subgraphs returns a populated `inputTokens` array for at least one known pool. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **Live-test whether 2022-era pool metadata is still indexed**, per subgraph, for
      curve/sushiswap/velodrome_v2/trader_joe_v2 -- before committing to a full historical backfill. Precedent both
      ways: Messari subgraphs are typically full-history (plausibly recoverable), but
      `EmptyConfirmedReason.EXPECTED_SUBGRAPH_DEINDEXED` is a real, shipped precedent for a subgraph going permanently
      unrecoverable (CURVE/OPTIMISM `dex_pool_swaps`, a different shard, see
      `instruments-service/scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py`). Done-when: a
      documented per-subgraph verdict (recoverable / partially-recoverable / deindexed) in this plan's Progress Log.
      (repo: market-tick-data-service)
- [ ] [BACKEND] P1. **Re-backfill `dex_pool_state` for curve/sushiswap/velodrome_v2/trader_joe_v2** across the full
      historical range using the fixed query (todo above), on an in-region VM per the heavy-I/O rule, scoped only to the
      ranges confirmed recoverable in the prior todo. Done-when: the manifest shows a populated `symbol`/ `pool_address`
      for the previously-unattributed cells within the confirmed-recoverable range. (repo: market-tick-data-service)
- [ ] [OPERATOR] P1. **Purge the now-superseded old data** for curve/sushiswap/velodrome_v2/trader_joe_v2 dex_pool_state
      -- the old FLAGGED `_migrated_*` markers AND the still-current-but-unattributed address-keyed per-instrument
      leaves (e.g. `0x00836fe5....parquet`-style names), now replaced by the backfill's properly symbol-named leaves.
      Prod-bucket delete, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- do this only
      after the backfill todo above has landed and been spot-checked. Done-when: zero unattributed (address-keyed)
      `dex_pool_state` leaves remain for these venues within the confirmed-recoverable range, and re-running
      `delete_migrated_defi_markers_2026_07_23.py`'s dry-run shows these venues' FLAGGED count at (near) zero. (repo:
      market-tick-data-service)

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- governs both purge todos.
- `/codex/05-infrastructure/vm-launcher-runbook.md` -- heavy-I/O rule, governs the backfill todo (in-region VM,
  `canonical-migration-defi-*`-family launcher or a new category on `launch-canonical-migration-vm.sh`, per the same
  registry-first convention used for `defi-marker-cleanup` this session).

## Progress Log

- **2026-07-26 -- lst_rates FLAGGED-marker fold executed + verified (closes twin-coverage blocker on todo 1).**
  - **New launcher category**: `deployment-service` gained `defi-lst-rates-fold` on
    `scripts/vm/launch-canonical-migration-vm.sh` (no new `VM_PREFIX_TO_BUCKET`/registry entry needed -- the
    `canonical-migration-defi-` prefix already covers it). Shipped
    `deployment-service@92b99481b541523926f985e057edf462adb9d03d`.
  - **Fold script shipped + fixed**: `market-tick-data-service@d0a478298a9165e8339237cf1d15c023c8d2cff1` (initial ship
    of `scripts/one_offs/fold_lst_rates_migrated_markers_2026_07_25.py` + its unit tests, from the prior session's
    build). **Live-fire finding (2026-07-26)**: the FIRST VM launch crashed instantly with
    `ModuleNotFoundError: No module named 'scripts.one_offs'` -- root cause: `scripts` is a top-level, non-namespaced
    regular package (`scripts/__init__.py`) in MULTIPLE sibling repos this VM family installs side-by-side
    (`deployment-service` AND `unified-api-contracts` both ship one), and `deployment-service` sorts first
    alphabetically in the editable-install `.pth` processing, so its `scripts` package wins `import scripts`
    workspace-wide on this VM -- shadowing MTDS's own `scripts.one_offs.delete_migrated_defi_markers_2026_07_23`
    submodule. Invisible in every local/CI run because MTDS's own `.venv` never installs `deployment-service` alongside
    it. **Fixed** (`market-tick-data-service@9150bc9fae4fe71b1961f4c46ed1c01933b6df5c`): load the sibling delete-script
    by FILE PATH (`importlib.util.spec_from_file_location`, mirroring the test file's own already-safe pattern) instead
    of the dotted `scripts.one_offs...` import -- immune to the cross-repo top-level-package collision regardless of
    `.pth` sort order. Verified locally by shadowing `scripts` with a fake empty package earlier on `PYTHONPATH`
    before/after the fix (repro'd the crash pre-fix, clean pre-fix on post-fix). The FIRST VM
    (`canonical-migration-defi-lst-rates-fold-20260726-002051`) self-deleted cleanly with zero side effects (the crash
    was at import time, before any GCS write) -- no cleanup needed. Related, NOT fixed here (out of this todo's scope,
    logged for awareness): two other pre-existing MTDS scripts use the same vulnerable `from scripts.<subpkg>... import`
    shape (`scripts/sports/league_id_relocation/prune_phantom_soccer_manifest_rows_2026_07_22.py`,
    `scripts/migrate_cefi_v2.py`) -- neither is currently wired into any `canonical-migration-vm.sh` category, so
    neither is live-broken today, but either would hit the identical crash if launched via this VM family.
  - **Fold run (SECOND launch, after the fix)**: `canonical-migration-defi-lst-rates-fold-20260726-003855`, zone
    `asia-northeast1-c`, `e2-standard-8`, SPOT provisioning, all 4 code tarballs SHA-pinned (UAC `cd37b9951280`, UTL
    `666c73d8dda4`, MTDS `9150bc9fae4f`, deployment-service `933864fe77c3`) and verified fresh before launch. VM reached
    RUNNING within seconds of `gcloud compute instances create`; the fold task itself launched ~2m17s after that (normal
    GCE boot + editable-install time for this VM family, matches every prior `canonical-migration-*` launch this
    closeout). Ran `--apply --workers 16` against the tool's own built-in 346-marker known-cluster population (no
    `--markers-file`/`--rediscover` -- zero discovery I/O). Progress (via the VM's GCS-teed `run.log`):
    50/100/150/200/250/300/346 processed in 13s total, `=== SUMMARY === folded: 346`, `command exited rc=0`,
    `DEPLOYMENT_COMPLETED exit_code=0`, VM self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`) within ~25s of completion.
    `run.log`:
    `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-lst-rates-fold-20260726-003855/run.log`.
  - **Known gap (documented, not a correctness issue)**: unlike the sibling `defi-marker-cleanup` category, the
    `_lst_rates_fold_cmd()` builder does not sync the tool's own local `--resume-log` JSONL to GCS every N minutes --
    harmless for a 13-second/346-marker run (a SPOT preemption mid-run would just lose the local resume-log and a
    relaunch would re-process a handful of already-folded markers as a cheap idempotent no-op, since `verify_marker()`
    would see them already `SAFE` and skip), but worth adding if this category is ever pointed at a much larger
    `--markers-file`/`--rediscover` population.
  - **Independent re-verification (exhaustive, not sampled)**: re-ran the sanctioned `verify_marker()` oracle (imported
    from `delete_migrated_defi_markers_2026_07_23.py`, never re-implemented) against all 346 known markers from this
    session (not the VM) -- **0 still-FLAGGED, 0 exceptions**, disposition breakdown
    `COINBASE: SAFE=202, MAKER: SAFE=132, SWELL: SAFE=5, ETHENA: SAFE=7` (sums to exactly 346).
  - **Content spot-check** (12 leaves, 3 per venue, read back directly -- not trusting the log alone): every sampled
    leaf (`cbETH.parquet` / `sDAI.parquet` / `swETH.parquet` / `sUSDe.parquet`) has `row_count=1`, the full 22-column
    wide/legacy schema preserved (`total_staked`/`ts_event`/`schema_version=9` etc., nulls and all -- never projected
    down), and real non-empty content (`exchange_rate`/`block_number`/`contract`/`protocol` populated per row); the
    original `_migrated_*` marker is confirmed still present, byte-untouched, beside each new leaf (fold-not-purge,
    never a rename/delete).
  - **Exact before/after twin-coverage** (see the updated table on todo 1 above): COINBASE 87.55%->100.00%, MAKER
    89.66%->100.00%, SWELL 99.58%->100.00%, ETHENA 99.28%->100.00%. All 4 venues now at genuine, independently
    re-verified 100% twin coverage -- zero markers could not be folded, zero gap to report.
  - **What remains**: todo 1's PURGE half stays `[OPERATOR]`, un-executed, un-checked -- per this dispatch's hard scope
    (fold/copy only, never a GCS delete) and per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
    (prod-bucket deletes are human-only). The disposition is now `yes-after-verify` (both blockers closed); a human
    re-runs `delete_migrated_defi_markers_2026_07_23.py --dry-run` (or trusts this session's exhaustive re-verify above)
    and executes the purge at their discretion.
