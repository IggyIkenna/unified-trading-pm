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
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
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
   excluded here, it is being removed entirely by `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) never
   requests `inputTokens { symbol }` from the subgraph -- full analysis in
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

- [x] ✅ [SCRIPT] P2. **Purge orphaned lst_rates `_migrated_*` markers** for COINBASE/SWELL/MAKER/ETHENA (all
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
                                                                              for the PURGE half of this todo. **The purge itself remains un-executed but is now agent-executable, not
                                                                              `[OPERATOR]`-gated. Reversibility-verified** (finding T, `task_template.md`): object-level delete only
                                                                              (specific `_migrated_*` marker objects, never the bucket), target
                                                                              `market-data-tick-defi-prd-central-element-323112` -- `gcs_bucket_soft_delete_retention_seconds(...)`
                                                                              returned `604800` (7 days) fresh-checked 2026-07-27 per
                                                                              `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. Re-query fresh before running, not from
                                                                              this citation -- the content-correctness gate (twin coverage, live-reader fix) is independently satisfied
                                                                              per the table above. Full detail (VM name/zone/mode, resume-log caveat, 12-leaf spot-check): this plan's
                                                                              Progress Log below.

- [x] ✅ [BACKEND] P1. **Fix the `messari_basic` subgraph query** in
      `market_tick_data_service/cli/handlers/dex_pools_handler.py` -- add `inputTokens { symbol }` (and
      `fees {     feePercentage feeType }` to match `_MESSARI_DEX_QUERY`'s shape) to
      `_CURVE_QUERY`/`_CURVE_QUERY_FILTERED`, and switch `curve`/`sushiswap`/`velodrome_v2`/`trader_joe_v2` (NOT `gmx`
      -- see context above) in `_dex_pools_subgraph.py`'s protocol table from `self._parse_curve` to
      `self._parse_messari_dex`. Verify the Messari `liquidityPoolDailySnapshots` schema actually exposes `inputTokens`
      uniformly across all 4 subgraphs before assuming this is a drop-in change. Done-when: a live test query against
      each of the 4 subgraphs returns a populated `inputTokens` array for at least one known pool. (repo:
      market-tick-data-service) ✅ **2026-07-27**: shipped `market-tick-data-service@63199601`. Root cause was TWO-FOLD,
      not just the missing query fields: `_parse_curve` (the pre-existing parser bound to the `messari_basic` entry)
      never read token symbols from the pool object AT ALL, regardless of what the query requested -- so even adding
      `inputTokens`/`fees` alone would not have fixed anything without also switching the parser to `_parse_messari_dex`
      (which already correctly extracts `token0/token1` symbols + fee tier from that exact shape). **Live-verified** all
      4 real subgraphs via `gateway.thegraph.com` (not assumed): curve ("Curve GEAR/ETH"), sushiswap ("SushiSwap AXON
      Finance/Tether USD"), trader_joe_v2 ("Trader Joe HUNDRED/USD Coin") all returned populated `inputTokens`/`fees` on
      the first query; velodrome_v2 hit a transient `bad indexers` gateway error on the first attempt, reproduced
      populated `inputTokens`/`fees` ("Velodrome Finance V2 sAMMV2-alETH/WETH") on retry -- confirming it was
      indexer-availability noise, not a schema gap. All 4 subgraphs confirmed uniform. Updated the 2 existing
      dispatch-wiring unit tests (`test_query_and_parse_velodrome_v2_uses_messari_basic`,
      `test_query_and_parse_trader_joe_v2_uses_messari_basic`) to mock `inputTokens`/`fees` and assert the resulting
      `token_a`/`token_b` columns are correctly populated (previously they only asserted non-empty + `pool_id`, so they
      would NOT have caught this class of bug). `_parse_curve` itself is untouched and still tested/available
      (`test_parse_curve_full`) -- left in place since the todo didn't call for its removal and a future protocol could
      still need the bare (non-inputTokens) Messari shape.
- [x] ✅ [DATA] P1. **Live-test whether 2022-era pool metadata is still indexed**, per subgraph, for
      curve/sushiswap/velodrome_v2/trader_joe_v2 -- before committing to a full historical backfill. Precedent both
      ways: Messari subgraphs are typically full-history (plausibly recoverable), but
      `EmptyConfirmedReason.EXPECTED_SUBGRAPH_DEINDEXED` is a real, shipped precedent for a subgraph going permanently
      unrecoverable (CURVE/OPTIMISM `dex_pool_swaps`, a different shard, see
      `instruments-service/scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py`). Done-when: a
      documented per-subgraph verdict (recoverable / partially-recoverable / deindexed) in this plan's Progress Log.
      (repo: market-tick-data-service) ✅ **2026-07-27**: shipped `market-tick-data-service@0f40a69f`
      (`scripts/live_test_2022_dex_pool_subgraph_indexing_2026_07_27.py`, a read-only live-network diagnostic, no GCS
      writes). Full per-subgraph verdicts in the Progress Log below -- summary: curve/ETHEREUM, curve/AVALANCHE,
      sushiswap/ARBITRUM, trader_joe_v2/AVALANCHE all RECOVERABLE (real 2022 data, live-verified). curve/OPTIMISM
      DEINDEXED (independently reconfirms the existing `dex_pool_swaps` precedent -- same dead subgraph id, same "no
      allocations" error, now shown to also hold for this different data_type/query). velodrome_v2/OPTIMISM is
      RECOVERABLE but has genuinely ZERO 2022 data -- not a fault, the protocol's real launch window is ~2023-06/07
      (subgraph confirmed healthy via populated 2024/2025 snapshots); the next todo's backfill range for velodrome_v2
      must start there, not fabricate a 2022 start.
- [x] ✅ [BACKEND] P1. **Re-backfill `dex_pool_state` for curve/sushiswap/velodrome_v2/trader_joe_v2** across the full
      historical range using the fixed query (todo above), on an in-region VM per the heavy-I/O rule, scoped only to the
      ranges confirmed recoverable in the prior todo. Done-when: the manifest shows a populated `symbol`/ `pool_address`
      for the previously-unattributed cells within the confirmed-recoverable range. (repo: market-tick-data-service) ✅
      **2026-07-28**: `mtds-dex-pools-symbolfix-batch1c` completed cleanly (`DEPLOYMENT_COMPLETED exit_code=0`,
      self-deleted) after walking its full assigned range (2025-04-02→2026-07-27) for curve/sushiswap/trader_joe_v2 —
      full detail in the Progress Log below.
- [ ] [SCRIPT] P1. **Purge the now-superseded old data** for curve/sushiswap/velodrome_v2/trader_joe_v2 dex_pool_state
      -- the old FLAGGED `_migrated_*` markers AND the still-current-but-unattributed address-keyed per-instrument
      leaves (e.g. `0x00836fe5....parquet`-style names), now replaced by the backfill's properly symbol-named leaves.
      **Gated on the backfill todo above landing + being spot-checked first** (a content-correctness prerequisite,
      independent of the reversibility check below -- NOT yet satisfied as of this edit, this plan's `sequential: true`
      chain still has the backfill todo unchecked). **Reversibility-verified, no `[OPERATOR]` gate needed** (finding T,
      `task_template.md`): object-level delete only, target `market-data-tick-defi-prd-central-element-323112` --
      `gcs_bucket_soft_delete_retention_seconds(...)` returned `604800` (7 days) fresh-checked 2026-07-27 per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. Re-query fresh before running, not from this
      citation. Done-when: zero unattributed (address-keyed) `dex_pool_state` leaves remain for these venues within the
      confirmed-recoverable range, and re-running `delete_migrated_defi_markers_2026_07_23.py`'s dry-run shows these
      venues' FLAGGED count at (near) zero. (repo: market-tick-data-service)

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
  - **What remains**: todo 1's PURGE half stays un-executed, un-checked -- per this dispatch's hard scope (fold/copy
    only, never a GCS delete). The disposition is now `yes-after-verify` (both blockers closed). **2026-07-27 update**:
    the PURGE half no longer needs `[OPERATOR]` sign-off either -- see the reversibility-verified clause on todo 1 above
    (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, `market-data-tick-defi-prd-central-element-323112`
    fresh-checked at `604800`s retention) -- a worker re-runs `delete_migrated_defi_markers_2026_07_23.py --dry-run` (or
    trusts this session's exhaustive re-verify above), re-queries the bucket's retention fresh, and executes the purge
    directly.

- **2026-07-27 -- todo 1 PURGE half executed + verified (closes todo 1).**
  - **Code**: `delete_migrated_defi_markers_2026_07_23.py` had no venue/data_type filter -- its `discover_markers()`
    globs the ENTIRE `raw_tick_data/**/_migrated_*.parquet` corpus (all clusters, all venues), so an unscoped `--apply`
    would also have touched the still-gated dex_pool_state markers for curve/sushiswap/velodrome_v2/trader_joe_v2 (todo
    5 below, explicitly NOT ready -- gated on its own backfill landing first). Added an optional client-side
    `--venues`/`--data-types` post-discovery filter (`_marker_venue_and_data_type()` / `filter_markers_by_scope()`) so
    this run could be scoped to exactly `lst_rates` × `{COINBASE,SWELL,MAKER,ETHENA}` without a second GCS listing pass
    and without any risk to the dex_pool_state cluster. Default (no filter) is unchanged full-corpus behavior, so the
    same script remains usable as-is for todo 5 once it's unblocked. 7 new unit tests (path-parsing + filter-combination
    coverage), full QG green, shipped `market-tick-data-service@e378643b`.
  - **Fresh retention re-check** (immediately before `--apply`, not trusted from the 2026-07-26 citation):
    `gcs_bucket_soft_delete_retention_seconds('market-data-tick-defi-prd-central-element-323112')` returned `604800` (7
    days) -- reversibility qualification reconfirmed live.
  - **Scoped dry-run** (`--venues COINBASE,SWELL,MAKER,ETHENA --data-types lst_rates`): discovery found 5066 markers in
    scope (COINBASE 1623 + MAKER 1276 + SWELL 1192 + ETHENA 975, matching the todo-1 table above exactly). First pass
    showed 1 marker `FLAGGED_NO_SIBLINGS_NO_BACKUP` on a transient GCS `503 ServiceUnavailable` reading its
    `_needs_attribution` fallback; a clean re-run (fresh resume-log) reproduced **0 FLAGGED** -- 4957 `SAFE` + 109
    `SAFE_NEEDS_ATTRIBUTION_COVERED`, confirming the first FLAGGED result was transient network noise, not a real
    content-loss finding.
  - **Apply**: ran with `--apply`, scoped to the same venue/data_type filter. (Session interruption mid-run --
    resume-log at time of write showed 1245 `deleted` entries, a partial capture; the resume-log mechanism means a
    session death mid-`--apply` is safe to re-run/resume by design, per the script's own RESUMABLE contract.)
  - **Verification (authoritative, not the resume-log)**: direct fresh GCS `match_glob` re-listing of
    `raw_tick_data/**/venue={VENUE}/**/data_type=lst_rates/_migrated_*.parquet` for each of the 4 venues, post-apply --
    **COINBASE 0, SWELL 0, MAKER 0, ETHENA 0** remaining. Done-when satisfied: zero `_migrated_*` lst_rates markers
    remain for these 4 venues in GCS. (Manifest side: these markers were never manifest-registered in the first place --
    `rebuild_defi_manifest.py`'s `scan_and_rebuild()` explicitly skips every `_`-prefixed leaf per the script's own
    module docstring -- so there was no manifest row to purge.)
  - Shipped: `market-tick-data-service@e378643b` (scope-filter code + tests). Plan checkbox flipped same turn.

- **2026-07-27 -- todo 3 live-test executed (closes todo 3): per-subgraph 2022-indexing verdict.**
  - **Method**: shipped `market-tick-data-service@0f40a69f`
    (`scripts/live_test_2022_dex_pool_subgraph_indexing_2026_07_27.py`, read-only, no GCS writes -- no delete-safety
    gating applies). For every `(protocol, chain)` pair the UAC registry declares for
    curve/sushiswap/velodrome_v2/trader_joe_v2, queried `gateway.thegraph.com` directly with the SAME `_CURVE_QUERY`
    (messari_basic `liquidityPoolDailySnapshots`) the just-fixed handler now uses in production (todo 2,
    `market-tick-data-service@63199601`), for two 2022 sample dates (2022-01-15, 2022-06-15). A subgraph returning a
    GraphQL error is DEINDEXED; one returning 0 rows for both 2022 dates with no error is disambiguated against later
    dates (2024-08-01, 2025-01-15) to tell "genuinely broken" apart from "protocol simply didn't exist yet in 2022".
  - **Results** (live-run output, `market-tick-data-service@0f40a69f`):

    | Protocol/Chain          | Subgraph ID                                    | 2022-01-15                                                                      | 2022-06-15            | Verdict                             |
    | ----------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------- | --------------------- | ----------------------------------- |
    | curve/ETHEREUM          | `3fy93eAT56UJsRCEht8iFhfi6wjHWXtZ9dnnbQmvFopF` | 62 snapshots (named pools, e.g. "Curve.fi DAI/USDC/USDT", "Curve.fi ETH/stETH") | 116 snapshots         | **RECOVERABLE**                     |
    | curve/OPTIMISM          | `CXDZPduZE6nWuWEkSzWkRoJSSJ6CneSqiDxdnhhURShX` | GraphQL error: `subgraph not found: no allocations`                             | same error            | **DEINDEXED**                       |
    | curve/AVALANCHE         | `2Vt8WtdXNZUEeaVtzyEd1dpioJf44nvomzkd4HhubfKS` | 15 snapshots (e.g. "Curve.fi avDAI/avUSDC/avUSDT")                              | 23 snapshots          | **RECOVERABLE**                     |
    | sushiswap/ARBITRUM      | `9tSS5FaePZnjmnXnSKCCqKVLAqA6eGg6jA2oRojsXUbP` | 74 snapshots (e.g. "SushiSwap Wrapped Ether/USD Coin (Arb1)")                   | 84 snapshots          | **RECOVERABLE**                     |
    | velodrome_v2/OPTIMISM   | `A4Y1A82YhSLTn998BVVELC8eWzhi992k4ZitByvssxqA` | 0 snapshots, no error                                                           | 0 snapshots, no error | **RECOVERABLE_BOUNDED** (see below) |
    | trader_joe_v2/AVALANCHE | `H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K` | 567 snapshots (e.g. "Trader Joe Wrapped AVAX/Tether USD")                       | 532 snapshots         | **RECOVERABLE**                     |

  - **curve/OPTIMISM DEINDEXED -- cross-confirms the existing precedent, doesn't just repeat it**: this run queries
    `liquidityPoolDailySnapshots` (the messari_basic `dex_pool_state` shape, todo 2's fix), a DIFFERENT query/data_type
    from the prior `dex_pool_swaps` cascade-exhaustion finding
    (`instruments-service/scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py`) that first
    identified this subgraph id as dead. Both queries hit the identical `"subgraph not found: no allocations"` error on
    the SAME subgraph id -- confirming the indexer-economics condition is subgraph-wide (no indexer allocations at all),
    not specific to one query shape. So the confirmed-recoverable range for curve EXCLUDES OPTIMISM entirely; only
    ETHEREUM and AVALANCHE are in scope for the next todo's backfill.
  - **velodrome_v2/OPTIMISM disambiguated, not left ambiguous**: 0 snapshots at both 2022 dates with NO GraphQL error
    (unlike curve/OPTIMISM) meant the subgraph itself needed a health check before concluding anything. Probed
    2024-08-01 (380 snapshots, e.g. "Velodrome Finance V2 sAMMV2-msETH/WETH") and 2025-01-15 (366 snapshots) -- both
    healthy and real, proving the subgraph is NOT deindexed. Bisected the actual launch window live: 2023-01-01 (0),
    2023-02-01..2023-06-01 (all 0), 2023-07-01 (133, real). So Velodrome V2 on Optimism genuinely has no history before
    ~2023-06/07 -- there is no 2022 data to recover because the protocol didn't exist yet, not because the subgraph lost
    it. **Actionable for the next todo**: velodrome_v2's backfill range must start at ~2023-06/07, not 2022 -- scoping
    it to 2022 would just be a guaranteed-empty scan, not a correctness issue but a wasted pass.
  - **Confirmed-recoverable range for the next todo (backfill)**: curve (ETHEREUM, AVALANCHE only -- NOT OPTIMISM),
    sushiswap (ARBITRUM), trader_joe_v2 (AVALANCHE) -- full historical range, live-verified as far back as 2022-01-15.
    velodrome_v2 (OPTIMISM) -- recoverable from ~2023-06/07 forward only.

- **2026-07-28 -- todo 4 backfill IN PROGRESS (checkpoint, not yet closed): 2 scoped SPOT VMs launched with the fixed
  query/parser.**
  - **Pre-existing conflict found + resolved without touching the other plan's VM**: at launch time, a STANDING VM
    `mtds-dex-pools-backfill` (owned by `mvp_backfill_defi_onchain_v10_2026_06_27.md`, relaunched 2026-07-25, walking
    2020-01-19->2026-06-25 across the FULL default 16-protocol list) was already RUNNING with PRE-FIX code (launched
    before the 2026-07-27 query/parser fix), actively re-writing more unattributed address-keyed leaves for these same 4
    protocols every day. Verified via code read that this is safe to run alongside (not touch, not stop): each write is
    a distinct timestamped file (never an overwrite), manifest writes are per-VM-sharded (no cross-VM conflict), and the
    already-planned todo-5 purge cleans up ANY residual address-keyed leaves regardless of which VM/timestamp wrote
    them. Proceeded in parallel with a DISTINCT `--shard-index` (0 and 1, vs the standing VM's 250) to avoid TheGraph
    key-pool collision.
  - **Launch 1** `mtds-dex-pools-symbolfix-batch1`:
    `--protocols curve,sushiswap,trader_joe_v2 --start 2020-01-20 --end 2026-07-27 --shard-index 0 --fleet-vms 2 --force`
    (force needed only to bypass the VM-name-prefix collision check against the unrelated standing VM above). SPOT, zone
    `asia-northeast1-c`. Tarballs freshly republished + SHA-pinned before launch: MTDS `fa4c731bdbda` (includes the
    63199601 query/parser fix + the 0f40a69f live-test script), UAC `d7fe3499d687`, UTL `5f48d47fb7cc`,
    deployment-service `9652d703e104`.
  - **Launch 2** `mtds-dex-pools-symbolfix-batch2`:
    `--protocols velodrome_v2 --start 2023-06-01 --end 2026-07-27 --shard-index 1 --fleet-vms 2 --force` -- start date
    chosen from todo 3's live-verified launch window (real data begins ~2023-07-01; 2023-06-01 gives a small inclusive
    margin rather than fabricating a 2022 start).
  - **batch2 (velodrome_v2) COMPLETE, verified correct**: `DEPLOYMENT_COMPLETED exit_code=0` at 2026-07-28T02:10:30Z, no
    preemption (`gcloud compute operations list` shows only `insert`/`delete`, both DONE), 1153 total results across the
    full 2023-06-01..2026-07-27 range. **Manifest spot-check**:
    `raw_tick_data/by_date/day=2026-07-27/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=VELODROME_V2/chain=OPTIMISM/instrument_type=pool/data_type=dex_pool_state/VELODROME_V2-OPTIMISM:POOL:ETHFI-WETH-30.0.parquet`
    -- properly symbol-named leaf, columns confirmed populated (`symbol=ETHFI-WETH-30.0`, `token_a=WETH`,
    `token_b=ETHFI`, `fee_rate_bps=3000`), not just `pool_id`/`pool_address`.
  - **Investigation + false-alarm correction (lesson for future spot-checks)**: an initial spot-check of
    `trader_joe_v2/AVALANCHE` on a day with confirmed real captures (2021-12-15, 492 records logged) found ONLY
    address-keyed filenames (`0x00979bd1....parquet`) and no `token_a`/`token_b` columns -- looked like the fix wasn't
    working. Root cause: **that address-keyed leaf was created 2026-07-26T08:20:41Z -- before this VM launched
    (2026-07-27T23:18Z) and before the fix itself shipped (2026-07-27)**. It was a PRE-EXISTING orphan from the standing
    `mtds-dex-pools-backfill` VM (or an earlier historical run), not this VM's output. Checking the SAME day/venue/chain
    path for symbol-shaped filenames found 470 properly-attributed leaves (e.g.
    `TRADER_JOE_V2-AVALANCHE:POOL:105-AVAX-USDC.e-3000.parquet`, confirmed created 2026-07-28T00:51:19Z -- squarely
    inside this VM's run window) alongside 711 old address-keyed orphans. **Takeaway: when spot-checking a backfill that
    runs alongside pre-existing data, always check blob CREATION TIMESTAMP (`gcloud storage ls -l`), not just
    presence/absence of a properly-named leaf** -- coexisting old+new files at the same path is the EXPECTED shape here
    (todo 5's purge is what removes the old ones), not a sign the new run is broken.
  - **batch1 (curve/sushiswap/trader_joe_v2) STILL RUNNING as of this checkpoint** (2026-07-28, mid-run) -- healthy, no
    crash-loop, no preemption, manifest entries climbing steadily (~600k+ per-VM shard entries and counting). Confirmed
    curve/OPTIMISM (explicitly excluded from the confirmed-recoverable range) correctly resolves to honest
    `record_zero_rows` on every attempt (`"subgraph not found: no allocations"` GraphQL error ->
    `_execute_subgraph_query` returns `None` -> empty df -> zero-rows, never `attempted_failed`) -- no special-case
    exclusion code was needed for this dead subgraph.
  - **What remains before todo 4 can be checked done**: batch1 finishing its full 2020-01-20..2026-07-27 walk (ETA
    several more hours from this checkpoint), then a manifest spot-check for curve/ETHEREUM + curve/AVALANCHE +
    sushiswap/ARBITRUM mirroring the velodrome_v2/trader_joe_v2 verification above (timestamp-checked against this VM's
    run window). Todo 5 (purge) is explicitly gated on this todo landing + being spot-checked first, per its own text --
    do not start it early.
  - **Incidental finding, filed separately (not blocking)**: batch2's shutdown hit an untracked `IAM_PERMISSION_DENIED`
    on `pubsub.topics.publish` for the `run-ledger` topic (post-completion observability telemetry only -- does not
    affect data correctness or this todo's done-when). Filed as
    `issues/vm_run_ledger_publish_iam_permission_denied_2026_07_28.md` since it is generic VM-launcher shutdown code,
    not specific to this plan.
  - **batch1 SPOT-preempted at ~07:38 UTC, recovered per the preemption-recovery HARD RULE (two attempts, first one
    WRONG -- correcting the record).** Confirmed via `gcloud compute operations list` (`compute.instances.preempted`,
    not a clean `DEPLOYMENT_COMPLETED`) -- last confirmed processing day was 2025-01-14 (~87% through the
    2020-01-20..2026-07-27 range, ~1.13M manifest entries written).
    - **First relaunch attempt (WRONG, corrected within minutes)**: relaunched with the IDENTICAL original
      `--start 2020-01-20` on the (mistaken) assumption that `ManifestFreshnessCache`'s skip-if-fresh check would
      recognize the ~1.13M already-captured (venue,chain,date) cells and fast-skip through them, resuming real work near
      the preemption point. **This did not happen** -- the relaunch's log showed REAL subgraph queries being re-issued
      starting from day 2020-01-22 (the very beginning of the range), not a fast skip. Root cause (inferred, not
      exhaustively proven): `ManifestFreshnessCache.is_now_skip_worthy()` depends on `read_availability_index()` finding
      the target day already captured in the CONSOLIDATED manifest index -- and this bucket's manifest consolidator was
      independently observed to be stale/behind during this same session (the `ManifestConsolidatorStaleError` already
      noted on batch2's log, `vm_run_ledger...` is unrelated but the consolidator-staleness condition is the same one).
      When the consolidated index can't be read fresh, the skip check appears to fail open to "not captured" rather than
      skip -- meaning a same-start-date relaunch would have silently REDONE the entire ~87%-complete range from scratch
      (~7+ more wasted hours), producing correct but massively redundant output (per-instrument shard filenames are
      stable/symbol-keyed, so a redo overwrites rather than duplicates -- not a correctness bug, but a severe efficiency
      one this specific handler's `ttl_seconds=60` per-day cache construction does not protect against across a VM
      restart). **Caught within ~5 minutes** (before any of the ~7h of wasted redo work accrued) by checking the
      relaunched VM's own log tail rather than assuming the skip mechanism worked.
    - **Corrected relaunch**: deleted the wrongly-restarting VM immediately, relaunched scoped to `--start 2025-01-10`
      (last confirmed processing day 2025-01-14, minus a few days' safety margin for any partially-written day at the
      moment of preemption) `--end 2026-07-27` -- i.e., resuming from MEASURED PROGRESS per the letter of the codex HARD
      RULE, not from the original START_DATE. This is the ~13% remaining tail (~563 days vs. the original ~2380),
      cutting the remaining runtime from ~7h+ to an estimated ~1-1.5h.
    - **Lesson for future preemption recoveries on this handler family**: do NOT assume `ManifestFreshnessCache`
      transparently makes a same-start-date relaunch safe/efficient -- verify the relaunch's own log shows real skips
      (or manifest-entry-count barely moving while advancing many days quickly) within the first few minutes; if it's
      re-issuing real subgraph queries for already-done early dates, kill and rescope to the measured resume point
      immediately rather than trusting the mechanism to self-correct.
    - Tarball freshness check warned STALE for 3 repos on both relaunch attempts (other slots pushed newer unrelated
      commits in the interim) -- verified via `git merge-base --is-ancestor` that the actually-deployed tarball SHA
      (`33fa3b58`) still descends from the query/parser fix commit (`63199601`), so no re-publish was needed before
      trusting either relaunch's output.
    - **SECOND preemption at ~08:31 UTC** (`compute.instances.preempted`, confirmed via
      `gcloud compute operations list`) after only ~38 minutes of runtime on the rescoped VM -- last confirmed
      processing day ~2025-04-06/07 (2025-04-07 partially in progress at preemption, per the log's per-day
      `DEX pools collection complete` / `_instruments_metadata: loaded ...` ordering). This zone (`asia-northeast1-c`)
      showed elevated SPOT preemption frequency this session (2 preemptions in ~1.5h of wall-clock monitoring) -- not
      itself an action item (SPOT is the correct default per the backfill-VM HARD RULE and idempotent shards tolerate
      it), just an observation for anyone reading this log wondering why there are 3 launch entries for one todo.
      Relaunched a THIRD time, scoped to `--start 2025-04-03` (a few days' margin before the last confirmed day)
      `--end 2026-07-27` -- verified via the VM's own serial console (`get-serial-port-output`, not just trusting the
      launcher's echoed flags) that the actual `--start-date 2025-04-03` reached the process command line, and via
      `gcloud storage cat .../code/mtds-code.manifest.json` + `git merge-base --is-ancestor` that the tarball SHA
      redeployed by ANOTHER slot in the interim (`0413e5cdf89e`) still descends from the fix commit. Confirmed via log
      tail that this third launch is correctly processing from day 2025-04-05 onward (not repeating the
      first-recovery-attempt mistake of silently replaying from 2020-01-20).
    - **THIRD preemption at ~08:38 UTC**, only ~4 minutes after that launch's own task start -- confirmed via
      `gcloud compute operations list` (`compute.instances.preempted`). Three preemptions in ~2h of wall-clock
      monitoring, with STRICTLY DECREASING runtime each time (~8.3h -> ~38min -> ~4min), is a clear signal of a real
      SPOT capacity crunch in `asia-northeast1-c` at this time, not a fluke. **Switched to on-demand for the final
      push** (`--on-demand` / `ON_DEMAND=true` on `launch-mtds-dex-pools-backfill-vm.sh`) -- this is the codex's own
      sanctioned opt-out from the SPOT-default HARD RULE, and with only ~480 remaining days of work left, the on-demand
      price premium for a single ~1-1.5h run is clearly cheaper than continuing to lose 4-40 minutes of progress to
      repeated preemptions. Relaunched scoped to `--start 2025-04-02` (last confirmed complete day ~2025-04-04, small
      safety margin) `--end 2026-07-27`, verified `[on-demand]` in the launcher's own creation output (empty
      `PREEMPTIBLE` column, not `true`) and via `git merge-base --is-ancestor` that the tarball redeployed yet again by
      another slot (`b2cb7bc05ba0`) still descends from the fix commit.
    - **As of this checkpoint (2026-07-28, session still monitoring)**: the on-demand relaunch is RUNNING. Todo 4 is NOT
      yet checked done -- still awaiting this VM's completion + a manifest spot-check for curve/ETHEREUM,
      curve/AVALANCHE, sushiswap/ARBITRUM (mirroring the velodrome_v2/trader_joe_v2 verification already done above),
      then the checkbox flip + `/done`. If this session's context is compacted before that happens, the next session
      should: (1) check
      `gcloud compute instances describe mtds-dex-pools-symbolfix-batch1 --zone=asia-northeast1-c --project=central-element-323112`
      for RUNNING/gone: since this launch is ON-DEMAND, "gone" now most likely means genuine completion (self-delete on
      `DEPLOYMENT_COMPLETED`), not preemption -- but still verify via `gcloud compute operations list` before assuming
      success, since an on-demand instance can still be manually stopped/deleted by someone; (2) if it completed cleanly
      (`DEPLOYMENT_COMPLETED exit_code=0`), do the manifest spot-check for the remaining 3 protocols and finish the
      todo; (3) if somehow still gone without a clean completion log, relaunch scoped to the measured last day (same
      recipe as above -- do NOT replay from 2020-01-20, 2025-01-10, or 2025-04-03).

- **2026-07-28 (final) -- `mtds-dex-pools-symbolfix-batch1c` completed; todo 4 verified + closed.**
  - **Completion**: monitored via a background watchdog (VM status + `run.log` tail every ~50s). VM finished cleanly at
    11:27:18Z -- `[vm-exec] command exited rc=0`, `DEPLOYMENT_COMPLETED 10a69b7c... (exit_code=0)`, self-deleted
    (`VM_SHUTDOWN_ON_COMPLETION=true`). Confirmed via `run.log`'s own `date=` progression that it walked the FULL
    assigned range through to the target end date (`2026-07-27`), not a partial/truncated run. The only warning was the
    already-tracked, non-blocking `pubsub.topics.publish` IAM gap on `run-ledger`
    (`issues/vm_run_ledger_publish_iam_permission_denied_2026_07_28.md`) -- observability-only, no effect on data
    correctness. No preemption during this final leg (on-demand, no `compute.instances.preempted` operations).
  - **Manifest spot-check** (creation-timestamp-verified against the VM's run window, per the lesson logged earlier in
    this session about coexisting old address-keyed orphans):
    - `curve/ETHEREUM` + `curve/AVALANCHE` at `day=2026-07-27`: symbol-named leaves (e.g.
      `CURVE-ETHEREUM:POOL:CRV-AAVE.parquet`, `CURVE-AVALANCHE:POOL:USDC-USDT.parquet`) created
      `2026-07-28T11:27:04-05Z` -- squarely inside batch1c's run window.
    - `trader_joe_v2/AVALANCHE`: `day=2026-07-27` itself had zero results that specific day (matches the log's own
      per-day count, trader_joe_v2 snapshots are sparse -- only 19/482 days nonzero in this VM's window), so
      spot-checked a confirmed-nonzero day instead: `day=2025-11-28` ->
      `TRADER_JOE_V2-AVALANCHE:POOL:WAVAX-ANI-30.0.parquet` created `2026-07-28T10:22:15Z`, matching the log's
      `trader_joe_v2_AVALANCHE: 1` result for that exact processing pass.
    - `sushiswap/ARBITRUM`: **investigated a real-looking anomaly, resolved as expected behavior, not a bug.** Every
      single one of batch1c's 482 processed days logged `sushiswap_ARBITRUM: 0` -- initially looked like the fix wasn't
      working for this protocol. Root-caused via `_catalogue_filter.py`'s own docstring (`market-tick-data-service`):
      the catalogue-as-filter design is INTENTIONAL -- the handler only queries the subgraph for pool addresses the IS
      catalogue currently lists in-window (4 pools for sushiswap/ARBITRUM), and a catalogued pool the subgraph returns
      nothing for on a given day is a legitimate `EXPECTED_NOT_ENOUGH_TVL` empty (recorded via
      `record_catalogue_residual_empty_typed`), not a fabricated/silent gap. Confirmed the fix genuinely works for
      sushiswap when the catalogued pools DO have activity: `day=2022-01-15` and `day=2022-06-15` (captured by the
      ORIGINAL pre-preemption `mtds-dex-pools-symbolfix-batch1` run, before this VM's own 2025-04-02+ range) both have
      real symbol-named leaves (`SUSHISWAP-ARBITRUM:POOL:$SLURP-USDC-3000.parquet`,
      `SUSHISWAP-ARBITRUM:POOL:$SLURP-WETH-3000.parquet`). Conclusion: sushiswap/ARBITRUM's 4 catalogued pools have
      simply been dormant (no snapshot-worthy activity) since roughly mid-2022 through the present -- a genuine
      real-world data pattern, not a defect in this plan's query/parser fix or in the backfill run. No issue doc filed;
      this was a resolved investigation, not an open defect.
    - `velodrome_v2/OPTIMISM`: already verified complete in the earlier `mtds-dex-pools-symbolfix-batch2` checkpoint
      above (batch2 finished first, independently).
  - **Done-when satisfied**: the manifest shows populated `symbol`/`pool_address` for previously-unattributed cells
    within the confirmed-recoverable range, verified per-protocol as above, across the full assigned historical range
    (2020-01-20 through 2026-07-27 for curve/sushiswap/trader_joe_v2 across the batch1/batch1c continuity; 2023-06-01
    through 2026-07-27 for velodrome_v2 via batch2). Todo 5 (purge) remains gated -- it is the next dispatchable todo in
    this `sequential: true` chain and is NOT executed by this todo.
  - No code shipped for this todo (pure VM-execution + verification; the query/parser fix itself shipped under todo 2).

- **2026-07-28 (later) -- `mtds-dex-pools-symbolfix-batch1` found genuinely STALLED (not preempted), root-caused,
  killed + relaunched as `mtds-dex-pools-symbolfix-batch1c`. New cross-cutting finding filed.**
  - **Symptom**: verified via direct `pandas.read_parquet` on
    `gs://market-data-tick-defi-prd-central-element-323112/_index/per_vm/mtds-dex-pools-symbolfix-batch1.parquet` that
    the per-VM manifest shard's total row count was FLAT at exactly `1196916` for 35+ minutes after the VM's own launch,
    while `run.log` repeated `ManifestWriter: per-VM shard updated (1196916 total entries, 1 new, ...)` every ~12s. CPU
    100-130%, RSS 1.7-3.8GB, no errors, no new day-processing log lines past the VM's first day (2025-04-02).
    `strace -c` on the live PID showed 83% of syscall time in `futex`, confirming genuine internal
    contention/computation, not an external hang. `gcloud compute operations list` showed no new preemption event since
    this VM's own launch -- this was a stall, not the SPOT-preemption pattern from earlier in this same session.
  - **Root cause** (full detail: new issue doc
    `issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md`, `unified-trading-pm@d7f6b3e59`):
    `unified_trading_library/manifest_writer/_writer_io.py`'s per-VM shard flush path (`_flush_per_vm_pending`) does a
    full read-merge-reserialize-upload of the ENTIRE existing per-VM shard on every debounced flush --
    O(existing-shard-size), not O(new-rows). This VM inherited ~1.2M rows accumulated across its 3 prior preempted
    incarnations (all sharing the same `VM_NAME`, the intended preemption-recovery pattern). Once the shard passed
    roughly 1M rows, a single flush round-trip exceeded the 5-second/50-entry debounce window, so the debounce could
    never batch multiple rows together -- every flush paid the full O(N) cost to drain ~1 pending row at a time
    (matching the observed `1 new`). The DeFi dex_pools handler makes this land hard because it writes a
    per-catalogue-pool "empty" manifest marker for every pool a day's subgraph query returned no data for (up to ~384
    for curve/ETHEREUM, ~294 for trader_joe_v2/AVALANCHE, in a SINGLE day), each going through
    `DefiManifestRecorder.record_empty` -> `ManifestWriter.add()` individually (`batch_size=1`, intentional per its own
    docstring for SIGKILL-durability -- NOT the bug, just what made this land fast). Confirmed via a background Explore
    agent's independent code read (`_dex_pools_subgraph.py:799-815`, `_dex_swaps_queries.py:241-254`,
    `_defi_manifest.py:129-134`) plus my own direct read of `_writer_io.py:694-783` -- not a deadlock, not a missing
    subgraph timeout (the 300s per-shard ceiling only wraps the fetch stage, irrelevant here).
  - **Action taken (mitigation, not a fix)**: killed `mtds-dex-pools-symbolfix-batch1`
    (`gcloud compute instances delete`, confirmed gone) and relaunched the SAME remaining range
    (`--start 2025-04-02 --end 2026-07-27 --protocols curve,sushiswap,trader_joe_v2`, on-demand, `--force` alongside the
    unrelated standing `mtds-dex-pools-backfill` VM) under a FRESH `VM_NAME=mtds-dex-pools-symbolfix-batch1c` so its own
    per-VM shard starts empty instead of inheriting the 1.2M-row backlog -- per-VM shards are plural-by-design and
    consolidated centrally later, so a name split is normal, not a special case. Tarballs were stale again (other slots
    pushed in the interim) -- verified via `git merge-base --is-ancestor 63199601 dcbed674242f...` that the deployed
    MTDS SHA still descends from the query/parser fix commit before trusting the launch.
  - **Fix VERIFIED, not just launched**: within ~90 seconds of the new VM's task actually starting, it had already
    processed 5 days (2025-04-02 through 2025-04-07, ~15s/day) -- matching the ORIGINAL pre-preemption run's throughput,
    vs. the killed VM's 35-minutes-stuck-on-day-1. Manifest per-VM shard growing normally (`3149 total entries` ->
    `3935 total entries, 786 new` across consecutive flushes). This is real, measured forward progress, not just "VM is
    RUNNING."
  - **Filed the underlying fix as tracked work, not left in chat**:
    `issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md` (`unified-trading-pm@d7f6b3e59`) --
    3 todos (P2/P3) proposing an append-only delta-shard pattern or an entries-dominant debounce for large shards, both
    in `unified-trading-library` (shared infra, out of this plan's scope; affects any long-running per-VM-shard
    backfill, not just DeFi). This plan's todo 4 is NOT blocked on that fix landing -- the fresh-VM-name mitigation is
    sufficient to complete THIS backfill; the issue doc's fix is for future backfills that would otherwise hit the same
    wall once their own per-VM shard grows large again.
  - **What remains**: `mtds-dex-pools-symbolfix-batch1c` continues its ~480-day remaining range (ETA ~2h at the verified
    ~15s/day rate). If this session compacts before completion, the next session should: (1) check
    `gcloud compute instances describe mtds-dex-pools-symbolfix-batch1c --zone=asia-northeast1-c --project=central-element-323112`
    for RUNNING/gone (on-demand, so "gone" likely means clean completion -- verify via `gcloud compute operations list`
    before assuming success); (2) if complete, spot-check the manifest for curve/ETHEREUM, curve/AVALANCHE,
    sushiswap/ARBITRUM (mirroring the already-done velodrome_v2/trader_joe_v2 verification), confirming symbol-named
    leaves with populated `token_a`/`token_b`/`fee_rate_bps` and checking blob CREATION TIMESTAMP against this VM's run
    window (not just presence, since old address-keyed orphans coexist by design until todo 5's purge); (3) flip todo
    4's checkbox + `/done`; (4) if somehow stalled/gone without clean completion, do NOT blindly relaunch under the SAME
    `VM_NAME` again without first checking its OWN per-VM shard size -- if it's again approaching ~1M rows, use yet
    another fresh name rather than repeating the same mitigation indefinitely, and reference the issue doc for the real
    fix. **[STALE -- superseded, see the 2026-07-28 entries below: batch1c completed cleanly and todo 4 is DONE.]**

- **2026-07-28 -- todo 5 (purge) IN PROGRESS (checkpoint before a context compact, not yet closed): script built, real
  bug found+fixed, catalogue-undercoverage finding filed, real --apply run currently RUNNING with confirmed progress.**
  - **Category-1 purge (redundant `_migrated_*` markers) NOT yet run for this cluster** -- todo 5's own text covers BOTH
    the old markers AND the still-current unattributed address-keyed leaves; only the second category has been tackled
    so far (see below).
    `delete_migrated_defi_markers_2026_07_23.py --venues CURVE,SUSHISWAP,VELODROME_V2,TRADER_JOE_V2 --data-types dex_pool_state`
    (safe to run for the FULL venue including CURVE/OPTIMISM -- it only removes redundant bundle-backup copies via the
    existing sibling/needs_attribution content-verification, never the actual per-instrument leaves) is still
    outstanding -- next session should `--dry-run` first, review, then `--apply` per the same reversibility citation as
    todo 1.
  - **New script shipped**: `market-tick-data-service@249dc019`
    (`scripts/one_offs/purge_superseded_dex_pool_address_keyed_leaves_2026_07_28.py` + 21 unit tests, full QG green).
    Per-shard-directory content verification: an address-keyed leaf is SAFE to delete only if a symbol-named sibling in
    the SAME (day, venue, chain) directory has a matching `pool_address` column value. Scope deliberately excludes
    CURVE/OPTIMISM (deindexed subgraph, confirmed via todo 3, no replacement ever possible -- purging its old data would
    be permanent loss). Manually cross-verified the SAFE/FLAGGED logic against real GCS content before trusting it (a
    known-SAFE address's replacement sibling located and confirmed by direct read).
  - **VM launcher wired**: `deployment-service@32f1361` added the `defi-dex-pool-leaf-purge` category to
    `launch-canonical-migration-vm.sh` (reuses the existing `canonical-migration-defi-` registry prefix, no new
    registration needed).
  - **Dry-run executed + verified** (`canonical-migration-defi-dex-pool-leaf-purge-20260728-130051`, full
    2020-01-01..2026-07-28 range, all 4 tarballs fresh-verified before launch): completed cleanly, `rc=0`, self-deleted.
    Result: **190,955 leaves SAFE** (content-verified superseded) / **541,890 leaves FLAGGED_NO_MATCHING_REPLACEMENT**
    (no replacement -- correctly retained). One false-alarm stall investigated mid-run (GCS-uploaded log copy lagged
    ~3-5 min behind the VM's own local log under a dense content window; SSH-verified the process was genuinely alive
    via growing CPU time -- not a real stall).
  - **MAJOR FINDING: the plan's own todo 5 done-when ("zero unattributed leaves remain") is UNSAFE to pursue
    literally.** 541,890 of the historically-captured address-keyed leaves (~74%) have NO catalogue-covered symbol-named
    replacement and never will under the current instruments-service catalogue population -- e.g. sushiswap/ARBITRUM's
    catalogue lists only 4 pools vs 100+ distinct historically-captured addresses. Purging those would be permanent,
    uncompensated data loss, violating the exact delete-safety principle this whole plan is built on. Filed
    `issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md` (`unified-trading-pm@2f50f916`)
    documenting the full finding + 2 follow-up todos (quantify the gap for the other 12 default protocols; an
    `[OPERATOR]` decision on catalogue-expansion policy). **Todo 5 is being completed against the SAFETY-CORRECT
    done-when instead**: purge the 190,955 content-verified-superseded leaves; the 541,890 no-replacement leaves are
    correctly, permanently retained (a deliberately bounded purge, not a partial/incomplete one).
  - **REAL BUG found + fixed before any live deletes happened**: the launcher's `_defi_dex_pool_leaf_purge_cmd()`
    originally used the SAME `RESUME_SEED_GS` path regardless of dry vs full mode. The first `--apply` launch
    (`canonical-migration-defi-dex-pool-leaf-purge-20260728-132858`) pulled down the COMPLETED dry-run's resume-log
    (which records every shard as "processed" with `action=would_delete`, never `deleted`) and silently no-op'd the
    entire run -- 0 shards processed, 0 deletes, `rc=0`. **Confirmed safe**: this was a no-op, not a destructive bug --
    nothing was deleted that shouldn't have been, but nothing was deleted at all either. Root-caused via direct log read
    (`resume log: ... (12005 shard(s) already processed)`, `0 to process this run`). Fixed
    (`deployment-service@d629197`): the resume filename/seed path now includes the mode (`.dry.resume.jsonl` vs
    `.apply.resume.jsonl`), so dry and full runs use disjoint state. Full QG green, shipped.
  - **MONITORING LESSON (2nd bug this session, on the monitoring side not the VM)**: after launching the real `--apply`
    run, `gcloud compute instances describe` calls started failing with a PERMISSION error (not "not found") under the
    `github-deploy` service account (the ambient `gcloud config` identity had drifted to it mid-session, away from
    `unified-trading-sa`) -- a background watchdog script's `|| STATUS="GONE_OR_ERROR"` fallback misread that permission
    failure as "the VM is gone," triggering a false "VM completed/preempted" conclusion. **The VM was never gone -- it
    was running the whole time.** Caught by re-running `gcloud compute operations list` (which showed only an `insert`
    op for this VM, no `delete`) and then re-`describe`ing after
    `gcloud config set account unified-trading-sa@central-element-323112.iam.gserviceaccount.com` -- confirmed `RUNNING`
    with real progress in the log. **Lesson for any future VM watchdog on this workspace**: a
    `describe`/`operations list` PERMISSION_DENIED is not evidence of VM state at all (unlike a clean "was not found",
    which IS real evidence of deletion) -- verify the active `gcloud config get-value account` is `unified-trading-sa`
    (or another identity with `compute.admin`) before trusting ANY negative/error VM-status read, especially one feeding
    an automated "VM_GONE" conclusion.
  - **Real `--apply` run CONFIRMED RUNNING with real progress** (after the resume-path fix, both `deployment-service`
    - `market-tick-data-service` tarballs republished + fresh-verified):
      `canonical-migration-defi-dex-pool-leaf-purge-20260728-134427`, started 2026-07-28T13:44:27Z (actual task start
      13:47:15Z after boot). Fresh retention check passed (`retention_seconds=604800`). Confirmed via direct log read
      (under the correct `unified-trading-sa` identity) processing normally: ~3000/12005 shards in 27s, matching the
      dry-run's own pace closely, `SAFE`/`FLAGGED` counts tracking the dry-run's proportions. **STATUS AS OF THIS
      CHECKPOINT (pre-context-compact): RUNNING, healthy, real progress confirmed -- NOT yet complete.** If this session
      compacts before completion, the next session MUST:
    1. **First**: `gcloud config set account unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (per the
       monitoring lesson above) before any VM status check.
    2. Check
       `gcloud compute instances describe canonical-migration-defi-dex-pool-leaf-purge-20260728-134427 --zone=asia-northeast1-c --project=central-element-323112`
       for RUNNING/gone. SPOT VM -- if genuinely gone, verify via
       `gcloud compute operations list --zones=asia-northeast1-c --project=central-element-323112 --filter="targetLink~canonical-migration-defi-dex-pool-leaf-purge-20260728-134427"`
       for a real `delete` op (preemption or self-delete) before concluding anything.
    3. If gone with a clean `DEPLOYMENT_COMPLETED exit_code=0` in
       `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-dex-pool-leaf-purge-20260728-134427/run.log`,
       check the `=== SUMMARY ===` block: expect `SAFE: 190955` matching the dry-run exactly (same scope, same
       verification logic) and `deleted` action counts matching. If the counts differ, investigate before trusting it.
    4. Spot-check a handful of the SAFE leaves' paths (from the resume-log, copied back to
       `gs://deployment-scripts-central-element-323112/canonical-migration-defi-dex-pool-leaf-purge/resume-seed/purge_superseded_dex_pool_address_keyed_leaves_2026_07_28.apply.resume.jsonl`)
       via `gcloud storage ls` to confirm they are actually GONE from GCS (not just marked `deleted` in the log without
       the real GCS call succeeding).
    5. If preempted/stalled: relaunch via
       `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh --env prod defi-dex-pool-leaf-purge 2020-01-01 2026-07-28 full`
       (republish tarballs first if stale) -- the fixed launcher's resume-log is RESUMABLE (per-shard, skips
       already-processed), so a relaunch naturally continues; no measured-progress start-date computation needed (unlike
       todo 4's backfill).
    6. Once the apply run confirms `SAFE: 190955` deleted matching the dry-run, flip todo 5's checkbox with evidence,
       then run category-1's marker purge (see top bullet) before todo 5 is FULLY closed, unless split into its own
       follow-up todo.
  - **Not yet done**: category-1 marker purge (see top bullet); confirming the `--apply` run's own completion + verified
    delete counts; flipping todo 5's checkbox; the finalize plan
    (`defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md`) remains correctly gated (depends_on + machine
    gate) until ALL 5 todos are done, including this one.
