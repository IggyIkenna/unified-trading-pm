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
- [ ] [BACKEND] P1. **Re-backfill `dex_pool_state` for curve/sushiswap/velodrome_v2/trader_joe_v2** across the full
      historical range using the fixed query (todo above), on an in-region VM per the heavy-I/O rule, scoped only to the
      ranges confirmed recoverable in the prior todo. Done-when: the manifest shows a populated `symbol`/ `pool_address`
      for the previously-unattributed cells within the confirmed-recoverable range. (repo: market-tick-data-service)
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
  - **batch1 SPOT-preempted at ~07:38 UTC, recovered per the preemption-recovery HARD RULE.** Confirmed via
    `gcloud compute operations list` (`compute.instances.preempted`, not a clean `DEPLOYMENT_COMPLETED`) -- last
    confirmed processing day was 2025-01-14 (~87% through the 2020-01-20..2026-07-27 range, ~1.13M manifest entries
    written). Relaunched immediately with the IDENTICAL original params (same `--start`/`--end`/`--protocols`, no
    `--force`/redo-all flag on the handler itself) so the manifest freshness-cache skip-if-fresh logic resumes near the
    preemption point rather than re-walking from 2020-01-20 -- per codex's HARD RULE that a relaunch replaying original
    params is correct for skip-enabled (non-force) runs. The relaunch's tarball freshness check warned STALE for 3 repos
    (other slots pushed newer unrelated commits in the interim) -- verified via `git merge-base --is-ancestor` that the
    actually-deployed tarball SHA (`33fa3b58`) still descends from the query/parser fix commit (`63199601`), so no
    re-publish was needed before trusting this relaunch's output.
