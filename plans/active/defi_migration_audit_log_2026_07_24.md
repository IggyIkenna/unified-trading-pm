---
doc_type: plan
title:
  DeFi migration audit log — G2/G4 readiness verdicts, PRE-APPLY audit, data_type coverage matrix, orphan-coverage
  drilldown (extracted from the master coordinator)
summary:
  Verbatim DeFi-specific migration audit trail (WAVE-2 G2-defi readiness verdict, APPLY-READY verdict, PRE-APPLY ①–⑫
  audit, data_type MIGRATION-COVERAGE matrix, ORPHAN-COVERAGE drilldown) extracted from
  master_data_canonicalisation_migration_catalogue_2026_06_07.md to bring that coordinator back under the 2000-line
  umbrella cap.
status: active
nature: process
asset_group:
  [defi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # this doc's own summary says "Verbatim DeFi-specific migration audit trail" -- it inherited the parent
  # master-coordinator's cross-cutting tag on extraction instead of being corrected to its real single-AG scope
stage: [meta]
repos:
  [
    agent-orchestrator,
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    e2e-testing,
  ]
scope: [engineer, admin]
tags: [coordinator, migration, manifest, data-layer, pipeline-mode, catalogue, defi, audit-log]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md #16 (bucket-d would-be-(c) split for
    master_data_canonicalisation_migration_catalogue_2026_06_07, operator-approved unlock+fix)",
    "/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md (origin of this content; verbatim
    extraction 2026-07-24)",
  ]
drift_direction: advance-code
context_scope:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
  ]
---

# DeFi migration audit log

> **Extracted verbatim 2026-07-24** from `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s
> `## vm-defi (slot-2) status + findings — 2026-06-07` section, as part of the line-cap remediation split
> (`/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` #16). That section contained an exact ~160-line
> verbatim-duplicated verdict block (the "G2-defi readiness verdict" + "🟢 DeFi APPLY-READY VERDICT" pair appeared twice
> byte-for-byte identically in the source, at the original file's lines 1541-1701 and 2011-2171) — the later copy is
> kept below; the earlier duplicate was dropped. Zero content was lost (verified via `diff` before deletion — the two
> copies were byte-identical). See `master_data_canonicalisation_migration_catalogue_2026_06_07.md` for the live
> gate-board + dependency DAG this content feeds into (this doc is a historical/audit record, not itself gating
> anything).

> **na-eligibility-audit 2026-08-01**: MIXED — re-read end to end (15 open items). 14 stay KEEP-NA valid (dated operator
> rulings, still-open cross-plan gates, operator-sign-off-gated GCS deletes, design/scope judgment calls). 1 item (the
> QG-harness rootdir finding) was assessed and NOT extracted — see its inline note below (already declined by
> `defi_satellite_ao_dispatch_batch6_2026_07_30.md` as under-evidenced). Doc stays `assigned_vm: NA`.

## vm-defi (slot-2) status + findings — 2026-06-07

> Progress on the **G0 C-PATH WRITE** (defi migrator/rebuild source-aware) + **G1-defi IS-catalogue** rows of the gate
> board. Code-ready facts + the gates verified; ship of the code unit is **blocked on a pre-existing MTDS QG-red** (see
> the finding below), not on the change itself.

**G0 C-PATH WRITE — CODE-READY (pending ship):** `migrate_defi_full_v9_canonical.py` + `rebuild_defi_manifest.py` now
derive the SOURCE-AWARE `{batch}_{source}` pipeline_mode PER SHARD via UTL
`derive_pipeline_mode_for_row(venue,"defi", data_type)` (the cefi/tradfi pattern), stamp `source` (=
`source_string_for(pm)`, C-#6-consistent) **+ a `transport` column** (`default_transport_for_source`, no path suffix),
in BOTH the PATH key and the manifest/parquet column. The coarse `DEFAULT_PIPELINE_MODE="batch"` /
`_DEFAULT_PIPELINE_MODE="batch"` / `_PIPELINE_MODES` are RETIRED; the rebuild day-probe lists `pipeline_mode=` (covers
every source-aware mode) + bare legacy; bare/legacy-coarse paths auto-derive source-aware; per-shard isolation added to
the rebuild `add()` loop. Tests rewritten + GREEN (25/25, credential-free). Verified per-shard: DEX
state→`batch_onchain_subgraph`, perp→`batch_hyperliquid`, oracle CHAINLINK→`batch_chainlink` / PYTH→`batch_pyth_hermes`.
**Single-walk safety GREEN**: GCS probe confirmed NO coarse `pipeline_mode=batch/` data was ever applied (dest `*-prd-`
trees are pre-pipeline_mode bare; rebuild bucket 2340 days all bare) — so upgrading the migrator before any G4 apply
does not require a second whole-corpus walk.

**G1-defi IS-catalogue — gates verified, seed apply correctly GATED (dry-run only):**

- A (slot-7 PART C code) GREEN · B (DeFi IS instrument backfill) GREEN · D (UAC chain-genesis / `*_VENUE_LAUNCH_DATES` /
  `PROTOCOL_LAUNCH_DATES`) GREEN.
- **C (defi instruments-store `_index` v9-canonical) 🔴 RED**: the `_index` is **0% v9** — schema_version distribution
  **v4=33,869 / v8=20,686 / v6=14,330** (68,885 rows), missing `source`/`asset_group`/`transport` columns. The defi
  instruments-store §H walk (`defi_manifest_canonicalisation` §H + `instruments_manifest_canonicalisation`) has NOT run.
- Catalogue **dry-run executed** (`build_instrument_catalogue --asset-group defi --dry-run`, read-only, exit 0) but
  rolled up **0 rows** — `instrument_availability/by_date/` in `instruments-store-defi-prd-*` is EMPTY (the 4,339-row IS
  backfill + the 68,885-row `_index` live in the NON-prd bucket; env-tier bucket split per
  `bucket_name_ssot_legacy_dual_write_remediation`). So the G1.run `--apply-write` seed is doubly gated → NOT run.

- [ ] [DATA] P1. **G1.run-defi seed — BLOCKED on GATE C**: do NOT `--apply-write` the defi could-exist seed until (c)
      the `instruments-store-defi` `_index` is v9-canonical (currently 0% v9) AND the defi
      `instrument_availability/by_date/` is populated in the bucket the catalogue producer reads (`-prd-` is empty).
      Owner: vm-defi, after the defi §H instruments-store walk. Repo: instruments-service. parent_epic: manifest_master.
- [ ] [UAC] [MTDS] P1. **Era-B legacy retirement — the per-AG v8→v9 migrator drops ALL `data_type=options_chain`/
      `futures_chain` recognition as its FINAL ATOMIC STEP, right after it relabels the on-disk rows to `trades`** 🟢
      **SAFETY GUARD SHIPPED (uac@93961df3, slot-7 2026-06-08)**: `assert_era_b_purge_safe()`
      (`canonical/crosscutting/era_b_legacy_purge.py`) simulates the legacy drop in-memory + asserts every closed-set
      round-trip survives (SOURCE_PRIORITY↔AVAILABILITY symmetry · PipelineMode · emission latency); the per-AG
      migrators MUST call it immediately before their atomic drop. Test proves the closed-set is purge-ready TODAY. The
      actual DROP stays G4-gated (coupled to cefi+tradfi `--apply` complete) — only the GUARD is landed here. (operator
      2026-06-07: "break old paths is the point of the migration" — couple-to-G4, do NOT lead the data). The could-exist
      PRODUCER is already Era-B (`uac@ae70338d`/`is@74df991d`); this retires the legacy-READ surface that still parses
      un-migrated v8 `data_type=options_chain` rows. **Removing it BEFORE the relabel would loud-fail every read of
      un-migrated v8 data (deployment-api/preflight KeyError / unknown DataType) — heartbeat break — so it is sequenced
      AFTER, inside the same migrator walk.** Full surface to drop atomically once an AG's rows are relabeled (all
      cascade-coupled — a partial purge breaks the closed-set round-trips): - UAC: `SOURCE_PRIORITY` +
      `AVAILABILITY_AT_SEMANTICS` (4 entries each — bidirectional round-trip) + `expected_coverage` venue lists
      (DERIBIT/BINANCE-FUTURES/BYBIT) + capability `coverage_start[options_chain/futures_chain]` +
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]` + `MVP_VENUE_DATA_TYPES`/`DERIBIT_MVP_INSTRUMENT_TYPE_DATA_TYPES` +
      `BASE_GRANULARITY_BY_DATA_TYPE` + the `DataType` enum `OPTIONS_CHAIN`/`FUTURES_CHAIN` + the snapshot
      `SchemaContract`s `(ag, options_chain, options_chain)`/`(ag, futures_chain, futures_chain)` +
      `venue_data_types.yaml` + flip the asserting tests (`test_market_data_asset_groups_use_tick_timestamp` cefi/tradfi
      options_chain lines, `test_every_datatype_has_at_least_one_schema_contract`, the snapshot-contract tests). - MTDS:
      `orchestrator.py` chain partition/data_type-merge (lines 44/692-700) — confirm fully Era-B (see the
      orchestrator.py finding below). GATED on cefi+tradfi G4 apply complete. Repos: unified-api-contracts +
      market-tick-data-service. parent_epic: manifest_master.
- [x] ✅ [MTDS] P0. **CLOSED 2026-06-08 (slot-2 GCS byte-probe) — the writer IS uniformly Era-B (code audit + on-disk
      confirmed).** Slot-7's code audit + the byte-probe below agree; the relabel `--apply` is no longer gated by Era-A
      residue. Original audit retained: 🟢 **PROGRESS (slot-7 2026-06-08, mtds@<pending>)**: (1) **OBJECT-WRITE path
      RE-CONFIRMED Era-B** (tardis_shared `_LEGAL_DATA_TYPES` raises on `options_chain`; databento
      `_PARTITION_INSTRUMENT_TYPE` maps FUTURE→`futures_chain` string + `data_type=trades`). (2)
      **`tradfi_catalog_reader.py:226-230` Era-A hint FIXED** → `data_type=trades` for FUTURE/OPTION (the chain bundle
      is carried by the instrument_type partition token, not the data_type) — **zero-risk**: a full read proved
      `CatalogRow.data_type` is NEVER consumed for seeding (orchestrator uses only `.venue`/`.instrument_id`, and
      `orchestrator.py:3548-3553` ALREADY SKIPS options_chain/futures_chain as data_types when seeding
      `record_expected_unattempted` — so NO Era-A data_type ever reached the manifest either). (3) The orchestrator
      `_MERGED_DATA_TYPE_MAP`/`_DATA_TYPE_TO_INSTRUMENT_TYPE` + `MVP_VENUE_DATA_TYPES`/`DERIBIT_MVP`
      options_chain/futures_chain entries stay **G4-gated** — the MVP config DRIVES the live DERIBIT chain DOWNLOAD
      (orchestrator.py:2440 filters `venue_data_types` to the DERIBIT_MVP data_type values), so dropping them now breaks
      DERIBIT capture; they retire atomically with the adapter migration at cefi+tradfi G4 (the era_b_legacy_purge guard
      enables it). **✅ gate (a) CLOSED — GCS byte-probe (slot-2, 2026-06-08, central-element-323112)**: real-prod
      `market-data-tick-cefi-prd` `day=2025-12-31` DERIBIT shards — `options_chain`/`futures_chain` appear ONLY as
      `instrument_type=`, the data_types are `trades`/`book_snapshot_5`/`derivative_ticker`,
      `pipeline_mode=batch_tardis` (source-aware), and **`data_type=(options_chain|futures_chain)` count = 0** → on-disk
      is uniformly Era-B, zero Era-A residue. **tradfi confirmed too** — `market-data-tick-tradfi-prd` `day=2025-12-31`:
      `futures_chain`/`options_chain` only as `instrument_type`, `data_type=trades` (722), Era-A chain count = 0. BOTH
      AGs uniformly Era-B on disk → gate fully closed.
  - **Live TICK-WRITE path = Era-B for cefi+tradfi chains (GOOD).** Both route through `tardis_shared.py` /
    `tradfi_shared.py` `finalise_and_write_cefi_shards`, whose `_LEGAL_DATA_TYPES` (tardis_shared.py:65) EXCLUDES
    `options_chain`/`futures_chain` and **raises** on `data_type=options_chain` (≈652) — it writes
    `instrument_type=options_chain|futures_chain` + a legal `data_type` (`trades`). The tradfi Databento adapter writes
    via `PartitionedTickWriter` with `_PARTITION_INSTRUMENT_TYPE` setting
    **instrument_type**=options_chain/futures_chain
    - `data_type=trades` (databento_adapter.py:111-120). The orchestrator `_MERGED_DATA_TYPE_MAP`
      (orchestrator.py:693) + `_resolve_partition_data_type` (:737) + write path (:1109/:1137) Era-A merge fires ONLY if
      a caller passes `data_type∈{options_chain,futures_chain}` — **no current tick adapter does**, so it is
      dead/defensive on the tick path. slot-3's GCS probe (cefi on-disk `data_type=trades`) corroborates. So the tick
      objects are Era-B.
  - **BUT residual Era-A surfaces remain → NOT a clean "uniformly Era-B" sign-off:**
    1. 🔴 **`market_tick_data_service/engine/tradfi_catalog_reader.py:226-230`** stamps
       `CatalogRow.data_type = "futures_chain"|"options_chain"` (FUTURE/OPTION) — this is the **MTDS could-exist /
       `record_expected_unattempted` preflight grain**, so it seeds expected rows at `data_type=options_chain` (Era-A)
       that DIRECTLY clash with the Era-B enumerate seed (`data_type=trades`, `uac@ae70338d`/`is@74df991d`) → the same
       cell double-grains (Era-A preflight row + Era-B enumerate row). **This is the concrete relabel-inconsistency
       risk.**
    2. 🟠 **UAC `MVP_VENUE_DATA_TYPES["DERIBIT"]` + `DERIBIT_MVP_INSTRUMENT_TYPE_DATA_TYPES`**
       (market_data_categories.py:485/493) still list `options_chain`/`futures_chain` as **data_types** (consumed by
       orchestrator.py:2436/2441) — the config that, if fed to the Era-A merge, re-introduces `data_type=options_chain`.
    3. 🟠 **orchestrator.py:693/737/1109/1137** Era-A merge map + `:44` docstring — dead-but-live; should be retired so
       a future caller can't re-introduce Era-A. `tardis_adapter.py:2541/2549` passes inbound
       `data_type="futures_chain"` (canonicalised to Era-B by finalise, but Era-A-shaped at the boundary).
  - **GATING before first `--apply` (BOTH required):** (a) **GCS probe** a recent cefi+tradfi chain shard to
    byte-confirm the on-disk `data_type=` dir (slot-7 lacks GCS creds in this slot — owner with creds runs it); (b)
    **retire the Era-A could-exist surface** — fix `tradfi_catalog_reader.py:226-230` to `data_type=trades` +
    `instrument_type=futures_chain|options_chain` (match the Era-B seed) and drop `options_chain`/`futures_chain` from
    `MVP_VENUE_DATA_TYPES`/`DERIBIT_MVP` as **data_type** values (keep them as instrument_types). Until both, the
    relabel double-grains tradfi/cefi chain cells. Repos: market-tick-data-service + unified-api-contracts. parent_epic:
    mtds_mdps_master.
- [x] ✅ [UAC] P2. **DeFi `SOURCE_PRIORITY` registry gaps — DONE (uac@28114692, slot-7 2026-06-08)**: registered
      `(defi, "n")` (the canonical dex-swaps data_type; legacy `dex_pool_swaps` retired) → `["onchain_subgraph"]` (the
      uniswap_v3/curve adapters read swaps from The Graph subgraph — `uniswap_v3_adapter.py` "primary for pools, swaps,
      liquidity" — so subgraph, matching `dex_pool_state`; it had fallen to the defi `BATCH_ONCHAIN_RPC` asset-group
      fallback). Added the matching `AVAILABILITY_AT_SEMANTICS` entry (closed-set symmetry holds; UAC QG green).
      **Non-Hyperliquid perp venues (LIGHTER→tardis) deliberately NOT added to `(defi, perp_funding)`** — they resolve
      per-shard via `pipeline_mode_resolver._VENUE_OVERRIDES["LIGHTER"]→BATCH_TARDIS` (BEFORE the SOURCE_PRIORITY
      lookup); adding tardis would flip `source_required(defi, perp_funding)`→True + break the Hyperliquid-native
      single-source auto-stamp (documented inline). **🔔 vm-defi (slot-2): the migrator now derives
      `batch_onchain_subgraph` for dex-swaps (was the `batch_onchain_rpc` fallback) — re-verify your G2 dry-run.** Repo:
      unified-api-contracts (`canonical/crosscutting/source_priority.py` + `availability_semantics.py`). parent_epic:
      manifest_master.
- [x] ✅ [INFRA] P2. **MTDS local `--no-fix` QG pre-existing-RED — ROOT-CAUSED + RESOLVED (slot-7 2026-06-08)**: the
      gate-0 blocker was the committed **`uv.lock`↔`pyproject.toml` desync** (slot-5 finding (b) below) —
      `uv lock --check` FAILED so QG aborted at its FIRST gate before file-size/basedpyright/tests ran. **FIX: `uv lock`
      (adds the 4 stub pkgs pyarrow-stubs + mypy-boto3-{logs,sns,sqs}, +52 LOC) — landed on LDR (mtds@dbbbef8a, peer;
      slot-7's identical re-lock dropped as a patch-id duplicate on rebase).** With it,
      **`bash scripts/quality-gates.sh --no-fix` now exits 0 and WRITES `.qg_last_passed_sha`** (verified slot-7: "All
      checks passed!", sentinel==HEAD) — the ~16 `❌` list was STALE (the >900 files were already split + the rest gated
      behind the uv.lock abort). The e2e-testing prediction basedpyright errors are a PERIPHERAL-consumer warning,
      non-blocking. MTDS QG is GREEN. Repo: market-tick-data-service. `parent_epic`: `mtds_mdps_master`. _(Original
      finding retained below for provenance.)_ ~16 `❌` on current LDR — 6 files >900 lines (5 unrelated:
      `migrate_sports_canonical_v9`/`rebuild_sports_manifest_v9`/`rebuild_prediction_manifest`/`solana_lst_archival`/
      `websocket_runner`), deep-UAC-imports / asyncio.run-in-loop / raw-response.json / empty-fallbacks in untouched
      handlers, STEP 5.85 inline-`pipeline_mode=` literals across the migration scripts, + macOS-environmental
      false-positives (574s>300s timing, BSD `grep -P` errors, no systemd cap). The defi C-PATH WRITE change adds ZERO
      net-new failures (its 25 unit tests pass; ruff clean; basedpyright-neutral). Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master. > **FINDING (slot-5 prediction, 2026-06-08) — two updates to this MTDS-QG-red
      item:** > (a) **`rebuild_prediction_manifest.py` is now SPLIT** (954→692 L, mtds@c571445d) → REMOVE it from
      the >900 list; > the remaining >900 files are non-prediction. (b) **NEW gate-0 blocker not previously listed: a
      committed > `uv.lock`↔`pyproject.toml` desync on the MTDS LDR HEAD.** `uv lock --check` FAILS — the committed
      `pyproject.toml` > declares `pyarrow-stubs` + `mypy-boto3-{logs,sns,sqs}` that are absent from the committed
      `uv.lock`, so the QG > aborts at its FIRST gate (`❌ uv.lock out of sync`) BEFORE file-size/basedpyright/tests
      even run. Mechanical > re-sync (`uv lock` adds the 4 stub pkgs, ~52 LOC; precedent mtds@10930dbd "re-sync uv.lock
      to pyproject"). Until > this lands, NO MTDS `quality-gates.sh` reaches green regardless of the file-length work —
      fix it FIRST in this > slot-2 sweep. (Slot-5 did not fix it: it completes another commit's incomplete dep edit —
      out of prediction AG + > FM1 foreign-work-bundling risk.) **✅ RESOLVED 2026-06-08 (slot-2, operator decision
      A):** (0) **gate-0 re-locked** (mtds@d544f15c — `uv lock` to current pyproject; `uv lock --check` green) BUT this
      is **recurring lock-drift** (the type-stubs flip-flop in pyproject between agents; `dbbbef8a` added them, a later
      commit removed them) → **handed to the dep/CI lane** (slot-1 `update-dependency-version.yml` prevention + settle
      the type-stub flip-flop); NOT a thing to keep manually re-locking. (1) **file-size = 15 pre-existing
      non-`scripts/` files** (orchestrator.py 4219 etc.) → **DEFERRED to the named successor
      `plans/active/mtds_file_size_refactor_2026_06_08.md`** (post-migration; splitting the migration's own
      `orchestrator.py` pre-apply is high-risk for zero migration benefit). **NOT migration-blocking**: file-size loop
      excludes `./scripts/*` (migration code clean); MTDS migration code ships via basedpyright-on-touched; `--apply`
      runs from VM/tarball not the sentinel. (The hollow-sentinel harness finding below is the related ship-hygiene
      item.)

### 🔵 DeFi PRE-APPLY ①–⑫ AUDIT — slot-2 2026-06-08 (post-drain, fresh real-prod re-verify)

> Re-ran the formal ①–⑫ framework on real-prod GCS (central-element-323112) AFTER the 2026-06-08 drain. **One
> migrator-output data-correctness BUG found + FIXED** (the dex-swaps source `n`-typo, below); one **live-write-path
> manifest-stamp drift** found + tracked (does NOT corrupt the `--apply` data — migrator+rebuild re-derive over it).

**🟢 FIXED this pass — dex-swaps source mis-stamp (① ⑨ migrator-output correctness, uac):** `source_priority.py` +
`availability_semantics.py` registered the dex-swaps source under a **dead literal key `("defi", "n")`** (slot-7
uac@28114692 typo — even the commit msg said "register defi dex-swaps 'n' source"; "n" matches no real shard). The real
canonical swaps data_type is **`dex_pool_swaps`** (the migrator bucket-spec `canonical_dt`
`migrate_defi_full_v9_canonical.py:112`, operator-locked; on-disk `data_type=dex_pool_swaps` in `dex-swaps-*`). So
`dex_pool_swaps` was UNREGISTERED → fell through the defi asset-group fallback to `batch_onchain_rpc`/`onchain_rpc`,
while the plan FALSELY claimed "the v9 migrator now derives batch_onchain_subgraph for dex-swaps". **Fixed**:
`("defi","n")` → `("defi","dex_pool_swaps"): ["onchain_subgraph"]` in BOTH registries (uniswap_v3/curve fetch
pools+swaps+liquidity from the SAME subgraph → matches `dex_pool_state`). **Verified on real prod**: scoped migrator
dry-run `--buckets dex-swaps --start-date 2024-05-15` → all 21 swap cells now project
`pipeline_mode=batch_onchain_subgraph/…/data_type=dex_pool_swaps`, 0 errors (was `batch_onchain_rpc`); UAC 109 targeted
tests + full suite green (only the `<720s` laptop META-time-gate tripped → `IGNORE_TIMEOUT=true` sanctioned). Without
this the irreversible single-walk `--apply` would have baked `source=onchain_rpc` into every dex-swaps shard. **Shipped:
`uac@012ccec1`** (committed + pushed to `tab/ikennaigboaka/2`, tab ⊇ LDR so the tab-mirror FFs it to LDR for the VM
`--apply`; the LDR→staging PR opens when the UTL breaking-change cascade STAGING LOCK clears — quickmerge STAGE-1.5
blocked since 2026-06-08T08:26Z, BLOCKED-UPSTREAM, re-quickmerge/automation promotes on unlock). Repo:
unified-api-contracts.

- [x] ✅ [MTDS] P1. **DeFi subgraph live handlers stamped `BATCH_ONCHAIN_RPC` for The-Graph-subgraph data — FIXED
      (mtds@2c259101, slot-2 2026-06-08).** The migrator + `rebuild_defi_manifest` RE-DERIVE `pipeline_mode`/`source`
      via `derive_pipeline_mode_for_row` (correct), and UTL `ManifestWriter.add()` only auto-derives when
      `pipeline_mode` is **blank** (`manifest_writer.py:1937/1943`) — so a NON-blank hardcoded value PERSISTS. Three
      handlers stamped `BATCH_ONCHAIN_RPC` while fetching via The Graph subgraph, contradicting `SOURCE_PRIORITY`+the
      migrator+the sibling `dex_swaps_handler` (correctly `BATCH_ONCHAIN_SUBGRAPH`): (a) `dex_pools_handler`
      (dex_pool_state), (b) `lending_indices_handler` (lending_indices, Aave/Spark/Compound), (c) `evm_defi_handler`
      (lending_indices). **Fixed → `BATCH_ONCHAIN_SUBGRAPH`** (all 12 record-call sites; subgraph data matches
      `SOURCE_PRIORTY=onchain_subgraph` + C-#6 consistent with the auto-stamped `source=onchain_subgraph`). Verified:
      104 handler tests + 0 basedpyright on the 3 files; no pinning test touched. **(e) `oracle_prices_handler` was a
      FALSE ALARM — already correct**: CHAINLINK rows use `BATCH_CHAINLINK`+`source="chainlink"` and PYTH rows use
      `BATCH_PYTH_HERMES`+`source="pyth_hermes"` per venue (oracle_prices_handler.py:758/767/782/791, comment notes the
      prior mislabel was already corrected). **Still open (folded into the orphan remediation above — those handlers
      write to NON-migrated orphan buckets, so the stamp-fix rides their bucket REDIRECT)**: (d)
      `aggregator_route_handler` (`BATCH_ONCHAIN_RPC`, pinned by
      `test_aggregator_route_handler_a12h_pipeline_mode.py:146`) + the Solana handler stamps → the P1-redirect +
      P2-Solana (`BATCH_DEFILLAMA`) orphan todos. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
      Provenance: slot-2 ⑪ pre-apply audit 2026-06-08.
- [ ] [UAC] P2. **`SOURCE_PRIORITY` is CHAIN-AGNOSTIC per `(asset_group, data_type)` → mis-attributes SOLANA DeFi source
      — RULED 2026-07-28 (retagged away from its prior operator-decision gate): adopt the per-venue mapping below.**
      `solana_defi_handler` fetches ORCA/RAYDIUM/KAMINO pools + Kamino/Marginfi/Solend lending via **Solana RPC / Helius
      / DeFiLlama** (NOT The Graph), but `SOURCE_PRIORITY(defi,dex_pool_state)` / `(defi,lending_indices)` resolve to
      `onchain_subgraph` for ALL chains → `derive_pipeline_mode_for_row(ORCA,defi,dex_pool_state)` =
      `batch_onchain_subgraph` (verified). So both the migrator AND a derive-based live handler would stamp
      `source=onchain_subgraph` on genuinely Solana-RPC/DeFiLlama data — a coarse provenance mislabel (the DATA is
      correct; only the `source` label is wrong). NOT introduced by the migration (pre-existing model coarseness it
      bakes). **Ruling**: adopt the per-venue mapping already sketched in this same audit (line ~498 below) as the
      canonical taxonomy — `ORCA`/`RAYDIUM`/`PHOENIX`/`KAMINO`/`MARINADE`/`JITO` → `solana_rpc`; `DRIFT` → `helius`;
      `MARGINFI`/`SOLEND` → `defillama`. Reasoning: this is canonicalisation work (correcting a provenance label to
      match the real fetch source), not a hack — the general mandate for this pass is to do canonicalisation properly,
      no shortcuts, so the concrete mapping is adopted rather than left as an open design question. Full-completion
      scope (no partial fix): add per-chain (or per-venue) source resolution to `SOURCE_PRIORITY`/
      `derive_pipeline_mode_for_row` for every venue in the mapping, not just a sample; see the sibling P2 todo below
      (line ~498) for the exact enum-member + override implementation this folds into. Repo: unified-api-contracts
      (`source_priority.py` + `pipeline_mode_resolver.py`). parent_epic: manifest_master. Provenance: slot-2 ⑪ pre-apply
      audit 2026-06-08.

#### ①–⑫ AUDIT VERDICT — DeFi pre-apply (slot-2, 2026-06-08, real-prod data-state)

| #   | Point                                                   | Verdict             | Evidence (sampled-vs-walked)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --- | ------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ①   | Migrator dry-run source-aware path+col                  | 🟢                  | scoped real-prod dry-run `migrate_defi_full_v9_canonical --buckets dex-swaps --start-date 2024-05-15` → 21/21 swap cells `pipeline_mode=batch_onchain_subgraph/asset_group=defi/…/data_type=dex_pool_swaps`, 0 errors (SAMPLED day; the prior all-6-bucket dry-run day=2024-06-01 covered pools/oracle/etc.). v9·`asset_group=`·`pipeline_mode=` LEFT of `asset_group`·per-row `available_at`·typed data_type — all confirmed. **Era-B relabel N/A (defi has no option/future chains, see ⑩).**                                                                                                                                                                           |
| ②   | Rebuild dry-run agrees                                  | 🟢                  | `rebuild_defi_manifest._resolve_pmst:207-217` uses path source-aware pmode verbatim else DERIVES via the SAME `derive_pipeline_mode_for_row` as the migrator; `source=source_string_for(pm)` C-#6-consistent by construction (WALKED the code).                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ③   | 4-state pre-flight (writer-materialised, consumer-read) | 🟢                  | `record_expected_unattempted` (orchestrator.py:3558) + IS `_enumerate_v2_defi`; consumers read 4-state (`dependency_checker.py:199`, `manifest_allocation_guard.py:65` — empty/expected→no-alert, failed→alert).                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ④   | Empty/partial honest + downstream handles               | 🟢                  | `DefiManifestRecorder.record_zero_rows` (\_defi_manifest.py:376) → `EXPECTED_PRE_VENUE_LAUNCH`/`SOURCE_RETURNED_ZERO` venue-launch-aware; `record_failed`→`classify_venue_error`+`ADAPTER_FETCH_FAILED`; no `except: return []` swallow; no silent placeholder.                                                                                                                                                                                                                                                                                                                                                                                                           |
| ⑤   | Read==write paths, prefix-match `batch_*`               | 🟢                  | features `mtds_output_config._MTDS_OUTPUT_BUCKET_DOMAINS` maps `dex_pool_swaps`→`dex-swaps` / `dex_pool_state`→`dex-pools` → `get_bucket_name` → `dex-swaps-prd-…` = the migrator's `base_prd` write target (READ==WRITE confirmed). `rg 'pipeline_mode=(batch\|live)([/\"'\'']\|$)'` across mtds/mdps/features/strategy/execution/deployment-api → 0 functional coarse hits (2 mtds hits are docstrings of the RETIRED coarse mode).                                                                                                                                                                                                                                     |
| ⑥   | IS+UAC validity matrix vs impossible cells              | 🟢 (P3)             | defi validity derived from `PROTOCOL_CAPABILITIES` (market_data_categories.py:847-858); grain `leaf` for all defi types; no odds/oracle leak into POOL. Residual: POOL row union-coarse (tracked P3); on-disk `instrument_type=a_token` (Aave) present alongside the 6 enumerated types — minor coverage edge, dominant cells pool/lending.                                                                                                                                                                                                                                                                                                                               |
| ⑦   | deployment-api/UI numerator+denominator = could-exist   | 🟢                  | G3 UNION read-path SHIPPED (deployment-api@4dd2575 `data_status_union.union_reduce_to_cells` + drilldown; deployment-ui@0dc40eb) — coverage % = captured/(captured+empty+failed+expected_unattempted) over could-exist denominator, READ not re-derived. (UI tick [BLOCKED-PLAYWRIGHT].)                                                                                                                                                                                                                                                                                                                                                                                  |
| ⑧   | IS-catalogue completeness (CF-14)                       | 🟢 (mechanism)      | `-prd-` by_date populated (64,724 parquets, 2020-01…2026-05); shape-aware `_enumerate_v2_defi`; all 6 defi instrument_types map cleanly. Full rollup candidate-COUNT = gated G1.run VM (VM-scale; downstream of the gated catalogue WRITE).                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ⑨   | pipeline_mode source-aware (CF-13)                      | 🟢                  | deterministic derivation check (14 defi cells): every cell source-aware, `source_string_for(pm)==source` True, transport populated; `dex_pool_swaps`→`batch_onchain_subgraph` after the fix.                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ⑩   | Era-B on-disk                                           | 🟢 N/A              | GCS probe `market-data-tick-defi-prd day=2024-06-01`: instrument_types = pool/lending/a_token/lst/yield_bearing; **zero `data_type=options_chain\|futures_chain`** (chains are cefi/tradfi-only). N/A for defi.                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ⑪   | ★ Batch=live symmetry                                   | 🟢 (migration side) | NO defi live-only data_types (one code path); `available_at` per-row write-time; live writer + migrator both derive via `derive_pipeline_mode_for_row`. **Migrated `--apply` data is correct + source-aware (① verified); `rebuild_defi_manifest` re-derives the manifest from object paths (overwriting any live stamp), `source` always C-#6-consistent → no persistent split.** Residual (tracked P1, NON-`--apply`-corrupting, rebuild-reconciled): several live handlers (dex_pools/lending/evm_defi/aggregator stamp `BATCH_ONCHAIN_RPC` for subgraph data; oracle stamps `BATCH_CHAINLINK` for Pyth rows) — transient live-manifest drift, self-healed by rebuild. |
| ⑫   | Rollback ready                                          | 🟢                  | `_index/snapshots/pre_migration_2026_06_08.parquet` confirmed in BOTH `market-data-tick-defi-prd` + `instruments-store-defi-prd` (gcloud probe); migrator `base_prd` + `ASSET_GROUP_CONFIG[defi].prefix_tpls` cover the v9 `raw_tick_data/by_date/day=/pipeline_mode=/asset_group=defi/` shape (the doubled-`day=` instruments-store object tail is the open P1 §H object-migration gate, not an index/manifest blocker).                                                                                                                                                                                                                                                 |

**REGRESSION RISK: NONE for the DeFi batch migration `--apply`.** The single migrator-output bug (dex-swaps `n`-typo →
swaps would bake `source=onchain_rpc`) is FIXED + verified on real prod. The live-handler manifest-stamp drift (⑪
residual, P1) does NOT corrupt the `--apply` migrated data — `rebuild_defi_manifest` re-derives the manifest from object
paths and is C-#6-consistent by construction; it self-heals on each rebuild. Remaining gates to the real `--apply` are
the prior OPERATIONAL ones (GATE C instruments-store v9 WRITE, IS backfill, the doubled-`day=` §H object fix, drain ✓
done) + the tracked P1/P2 live-track handler-derive remediation (post-migration, not a batch-`--apply` blocker).

### 📊 DeFi data_type MIGRATION-COVERAGE MATRIX — ALL 25 accounted (slot-2, 2026-06-09)

> Operator 2026-06-09: "did we account for the remaining data types not migrated?" — full accounting of every
> `DATA_TYPES_BY_ASSET_GROUP["defi"]` entry (25) vs the migrator `_SPECS`. Each row: migrator-covered? + has-data? +
> disposition. Verdict: **8 MIGRATED · 3 DATA-BEARING-ORPHAN (fold) · 14 NO-DATA scaffolds (collection gaps)** — nothing
> unaccounted. (Migrator specs went 6→8 this turn: gas-fees + liquidations added, mtds@01fda7ce.)

| data_type               | migrator spec        | data on disk?                                               | disposition                                                                                           |
| ----------------------- | -------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| dex_pool_state          | ✅ dex-pools         | yes                                                         | **MIGRATED**                                                                                          |
| dex_pool_swaps          | ✅ dex-swaps         | yes                                                         | **MIGRATED** (source fixed: `n`→dex_pool_swaps→subgraph)                                              |
| lending_indices         | ✅ lending-indices   | yes                                                         | **MIGRATED**                                                                                          |
| perp_funding            | ✅ perp-funding      | yes                                                         | **MIGRATED**                                                                                          |
| lst_rates               | ✅ lst-rates         | yes                                                         | **MIGRATED**                                                                                          |
| oracle_prices           | ✅ oracle-prices     | yes (incl LST/LRT: stETH/wstETH/weETH/cbETH/rETH)           | **MIGRATED** — LST/LRT prices ride this existing data_type                                            |
| gas_fees                | ✅ gas-fees ⬅NEW     | yes (`gas-fees-central`)                                    | **MIGRATED** (this turn, mtds@01fda7ce)                                                               |
| liquidations            | ✅ liquidations ⬅NEW | yes (`liquidations-central`)                                | **MIGRATED** (this turn, mtds@01fda7ce)                                                               |
| vault_share_price       | ❌                   | YES — in `market-data-tick-defi` orphan (active 2026-05-01) | **ORPHAN-FOLD** (P1) — fold into a dedicated bucket + migrate                                         |
| risk_params             | ❌                   | YES — in `market-data-tick-defi` orphan                     | **ORPHAN-FOLD** (P1)                                                                                  |
| utilization             | ❌                   | YES — in `market-data-tick-defi` orphan                     | **ORPHAN-FOLD** (P1)                                                                                  |
| eigenlayer_rewards      | ❌                   | NO (`eigenlayer-rewards{,-prd}` EMPTY)                      | **COLLECTION GAP** — adapter exists, not producing; spec when data lands                              |
| staking_yields          | ❌                   | NO (`staking-yields` empty)                                 | **COLLECTION GAP**                                                                                    |
| native_staking_rates    | ❌                   | NO                                                          | **COLLECTION GAP** (multi-source solana_rpc/helius)                                                   |
| bridge_events           | ❌                   | NO                                                          | scaffold (no data; no dedicated/tick-data bucket exists) — deprioritized (2026-08-08 operator ruling) |
| flash_loan_events       | ❌                   | NO                                                          | scaffold — deprioritized (2026-08-08 operator ruling)                                                 |
| flash_loan_availability | ❌                   | NO                                                          | scaffold — deprioritized (2026-08-08 operator ruling)                                                 |
| governance_events       | ❌                   | NO                                                          | **MVP SCOPE (2026-08-08 operator ruling)** — wire a real source                                       |
| liquidation_events      | ❌                   | NO                                                          | **MVP SCOPE (2026-08-08 operator ruling)** — wire a real source (distinct from `liquidations`)        |
| mev_events              | ❌                   | NO                                                          | scaffold — deprioritized (2026-08-08 operator ruling)                                                 |
| position_data           | ❌                   | NO                                                          | scaffold — deprioritized (2026-08-08 operator ruling)                                                 |
| token_transfers         | ❌                   | NO                                                          | **MVP SCOPE (2026-08-08 operator ruling)** — wire a real source                                       |
| rewards                 | ❌                   | NO                                                          | scaffold / computed-downstream — deprioritized (2026-08-08 operator ruling)                           |
| vault_apy               | ❌                   | NO                                                          | scaffold / computed-downstream                                                                        |
| vault_tvl               | ❌                   | NO                                                          | scaffold / computed-downstream                                                                        |

**So no data_type is silently dropped:** the migrator now covers all 8 data-bearing DEDICATED-bucket data_types; the 3
data-bearing-in-the-orphan-bucket ones (`vault_share_price`/`risk_params`/`utilization`) ride the market-data-tick-defi
FOLD (P1 below — they're written to the orphan bucket by `vault_share_price_handler` + Solana/legacy writers, so they
migrate once that bucket is folded into dedicated buckets); the remaining 14 have **NO GCS data** (adapters scaffolded
but not producing) → **collection gaps** (external-data-always-available: wire the source / operator credential-ask, NOT
a migration gap). Probe basis: `gcloud storage` bucket sweep + `market-data-tick-defi` day-samples (2024-06-01 +
2026-05-01); `tick-data-*` buckets 404 (the scaffold handlers' `kind="tick-data"` has no bucket → no data).

- [ ] [DATA] P1. **FOLD the 3 data-bearing orphan data_types into dedicated buckets + migrate** (vault_share_price /
      risk_params / utilization — data ONLY in `market-data-tick-defi` (orphan), so they ride the market-data-tick-defi
      redirect+fold below; either give each a dedicated bucket + spec, OR add market-data-tick-defi as a per-data_type
      migrator source routing to dedicated dests). vault_share_price is MVP-relevant (carry vault NAV). Repo:
      market-tick-data-service. Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2 coverage matrix
      2026-06-09.
- [ ] [DATA] P2. **Retagged 2026-07-29 (corpus hygiene pass): mostly false-positive — verified
      `eigenlayer_rewards_handler.py` (Alchemy RPC + free DefiLlama), `native_staking_handler.py` (free public Solana
      RPC + free Jito Kobe MEV API) and `staking_yields_handler.py` (free Lido/EtherFi/DefiLlama APIs) are ALL complete,
      non-stub implementations already reusing existing free/already-provisioned credentials —
      `staking_yields_handler.py`'s own docstring states "this operation has ZERO scheduled Cloud Scheduler jobs as of
      2026-07-24", confirming its gap is SCHEDULING, not credential. Only a narrow sub-feature of
      `native_staking_handler.py` (per-validator staking breakdown, vs. the aggregate rate it already produces)
      genuinely needs a new `helius-api-key` — Helius has a FREE tier (instant self-signup), so even that is not a
      paid-credential blocker.** DeFi collection gaps — 14 scaffolded data_types with NO GCS data (eigenlayer_rewards,
      staking_yields, native_staking_rates, bridge_events, flash_loan_events, flash_loan_availability,
      governance_events, liquidation_events, mev_events, position_data, token_transfers, rewards, vault_apy, vault_tvl).
      Handlers exist but produce nothing — per external-data-always-available these are COLLECTION gaps (wire the source
      / credential-ask to the operator), NOT migration gaps. ~~Triage: MVP-relevant (eigenlayer_rewards restaking
      yield + native_staking_rates for carry_staked_basis) → BLOCKED-CREDENTIALS source-ask~~ — revised triage:
      eigenlayer_rewards + the aggregate native_staking_rates are code-complete and need only a Cloud Scheduler job
      wired to start producing (no credential); only the per-validator native_staking_rates breakdown needs a free-tier
      `helius-api-key` self-signup; the rest → confirm in/out of MVP scope. _*Correction 2026-08-08:
      `eigenlayer_rewards` HALF of the "still needs scheduling" framing is stale —
      `deployment-service/terraform/gcp/defi_collection_scheduler.tf` has had a live `collect-eigenlayer-rewards` Cloud
      Scheduler cron (`45 1 * * *`) since `7b1490f7` (2026-04-25, "wire 11 daily DeFi collect-* Cloud Run Jobs +
      Scheduler crons"), confirmed still present live 2026-08-08 — no scheduling gap remains for this data_type.
      `native_staking_rates` genuinely still has NO scheduler entry in that same file (confirmed via a fresh grep
      2026-08-08) — that half of the claim holds._* Each gets a migrator spec ONLY once it produces data. Repo:
      market-tick-data-service + UAC. Owner: vm-defi. parent_epic: defi_master. Provenance: slot-2 coverage matrix
      2026-06-09. **"confirm in/out of MVP scope" RESOLVED 2026-08-08 (operator ruling)**: of the remaining untriaged
      scaffolds (`bridge_events`/`flash_loan_events`/`flash_loan_availability`/`governance_events`/
      `liquidation_events`/`mev_events`/`position_data`/`token_transfers`/`rewards`/`vault_apy`/`vault_tvl`) —
      `liquidation_events`, `token_transfers`, `governance_events` are now MVP scope (3 concrete wire-a-source todos
      filed immediately below); the other 8 stay deprioritized scaffolds unless the operator says otherwise. Coverage
      matrix table above updated to match.

- **[DATA] P2. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** Wire a real source for
  `liquidation_events` (MVP scope, 2026-08-08 operator ruling) — distinct from the already-migrated `liquidations`
  data_type (which carries protocol-level liquidation EVENT SUMMARIES from the dedicated `liquidations-central` bucket);
  `liquidation_events` is the currently-unproduced per-event scaffold (no GCS data at all today, handler-if-any produces
  nothing). Determine the real on-chain source (Aave/Compound/Morpho liquidation-call event logs via existing
  RPC/subgraph access already used elsewhere in this asset_group — check
  `_dex_factory_registry.py`/`solana_defi_handler.py`-style precedent before assuming a new credential is needed) and
  wire a collector that writes real rows, following the same `record_captured`/`record_zero_rows`/`record_failed`
  honest-absence contract every other DeFi handler uses. Repo: market-tick-data-service. parent_epic: defi_master.
  Done-when: a real `liquidation_events` manifest row lands for at least one live venue/day.
- **[DATA] P2. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** Wire a real source for
  `token_transfers` (MVP scope, 2026-08-08 operator ruling) — currently a no-data scaffold. Determine the real source
  (EVM `Transfer` event logs via existing Alchemy/RPC access, or a subgraph if one of the already-registered
  `SUBGRAPH_IDS` protocols exposes transfer history) and wire a collector writing real rows via the standard
  `record_captured`/honest-absence contract. Repo: market-tick-data-service. parent_epic: defi_master. Done-when: a real
  `token_transfers` manifest row lands for at least one live venue/day.
- **[DATA] P2. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** Wire a real source for
  `governance_events` (MVP scope, 2026-08-08 operator ruling) — currently a no-data scaffold. Determine the real source
  (on-chain governance-contract event logs — proposal created/voted/executed — for the DeFi protocols this asset_group
  already tracks governance for, e.g. via the existing `_defi_chain_data`/`SOLANA_RPC_TEMPLATES`-style RPC registry, or
  a governance subgraph) and wire a collector writing real rows via the standard `record_captured`/honest-absence
  contract. Repo: market-tick-data-service. parent_epic: defi_master. Done-when: a real `governance_events` manifest row
  lands for at least one live venue/day.

### 🗑️ DeFi ORPHAN-COVERAGE DRILLDOWN — GCS data NOT covered by the migrator + delete-after plan (slot-2, 2026-06-08)

> **Operator ask (2026-06-08): no orphaned data.** The `migrate_defi_full_v9_canonical` migrator reads ONLY the **6
> dedicated SOURCE buckets** (stems `dex-pools` / `dex-swaps` / `lending-indices` / `perp-funding` / `lst-rates` /
> `oracle-prices`; `base={stem}-{pid}` → `dest={stem}-prd-{pid}`). **Every other DeFi GCS bucket with real market data
> is OUTSIDE migration scope → orphan-candidate.** Real-prod `gcloud storage` enumeration (slot-2 2026-06-08) found **6
> data-bearing LEGACY orphan buckets + 2 empty**, PLUS a **7th DEDICATED bucket the migrator simply OMITS: `gas-fees`**
> (a proper dedicated source bucket like the 6, but absent from `_SPECS` → `gas-fees-prd` is empty/un-migrated; P0
> below). Drilldown + dup-vs-unique + delete-after below so nothing is silently left behind on the irreversible cutover.

**Root cause (the orphan SOURCE):** the live DeFi handlers write to INCONSISTENT buckets — only 5 write to the dedicated
migrated buckets; **4 write to non-migrated buckets**: `dex_swaps_handler`→`market-data` (=`market-data-tick-defi`),
`solana_defi_handler`→`market_data`(=`market-data-tick-defi`), `evm_defi_handler`→`evm-defi`,
`aggregator_route_handler`→`aggregator-routes`. So new writes keep CREATING orphans. (See the handler→bucket map in the
P1 redirect todo below.)

**Per-bucket drilldown (real-prod, central-element-323112):**

| Bucket                                                                                                                                         | Data / path shape                                                                                                                                                                                              | Format                                                                                              | Migrator covers?                                    | Dup-vs-unique                                                                                                                                                                                                         | Disposition                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `dex-pools-{,prd-}` · `dex-swaps-{,prd-}` · `lending-indices-{,prd-}` · `perp-funding-{,prd-}` · `lst-rates-{,prd-}` · `oracle-prices-{,prd-}` | `day=/category=defi/venue=` (lst-rates already `asset_group=`)                                                                                                                                                 | OLD source → migrator normalises to v9 `pipeline_mode={mode}_{source}/asset_group=defi/` in `-prd-` | ✅ YES (MIGRATED-SOURCE→DEST)                       | n/a                                                                                                                                                                                                                   | KEEP. `-prd-` dest = canonical home. (dex-pools-prd/dex-swaps-prd carry partial prior-apply residue + OLD-format residue → the `--apply` overwrites + the legacy old-format objects are deleted by the migrator's RD4 legacy-delete after a green conform.)                                                                                                                                |
| **`gas-fees-{,prd-}`** ← 7th dedicated bucket the migrator OMITS                                                                               | `day=/category=defi/venue=<CHAIN\|ALCHEMY>/chain=<CHAIN>/instrument_type=spot_asset/data_type=gas_fees/` — CHAIN-grain (one shard per chain per day; same for ALL protocols on a chain), data from 2024-05-15+ | OLD source shape (same as the 6); `gas-fees-prd` is **EMPTY** (NOT migrated)                        | ❌ **NO — `_SPECS` has only 6, `gas-fees` missing** | n/a (source bucket; not a dup) — this is a **MIGRATOR COVERAGE GAP**, not a legacy orphan                                                                                                                             | **ADD as the 7th migrator spec** (see P0 below). gas is the per-chain gas PRICE; downstream net-cost = gas_price × gas_units (from execution `estimate_gas`). Source = `onchain_rpc` (Alchemy `eth_gasPrice`) ✓ — the handler's `BATCH_ONCHAIN_RPC` stamp is CORRECT (RPC, not subgraph). Venue-era split (old `venue=<chain>` vs new `venue=ALCHEMY`) needs canonicalisation in the spec. |
| **`market-data-tick-defi-prd`** + `market-data-tick-defi`                                                                                      | `dex_pools/<proto>/<CHAIN>/date=` + `lending_indices/<proto>/` (Solana ORCA/RAYDIUM/KAMINO + lending); **ACTIVELY written 2026-06-08**                                                                         | LEGACY (no hive `day=`, no `category=`/`asset_group=`, no `pipeline_mode=`; bare `date=`)           | ❌ NO                                               | **DUPLICATE** for ORCA/RAYDIUM Solana DEX (present in `dex-pools-` as `venue=ORCA/chain=SOLANA`). ⚠️ **VERIFY KAMINO DEX pools + the Solana `lending_indices`** are in `dex-pools-`/`lending-indices-` before delete. | DELETE-AFTER (post-migration + KAMINO/lending verify). FIRST: stop the writers (redirect `dex_swaps`+`solana` handlers) + migrate any unique KAMINO/Solana-lending shards into `dex-pools-`/`lending-indices-`.                                                                                                                                                                            |
| **`evm-defi-prd`** + `evm-defi`                                                                                                                | `raw_tick_data/by_date/day=/asset_group=defi/venue=AAVE_V3/…/instrument_type=a_token/` (Aave V3 EVM)                                                                                                           | MID (`asset_group=`, no `pipeline_mode=`); stale index 2026-05-12                                   | ❌ NO                                               | **PARTIAL**: post-`2022-11` Aave is DUPLICATE of `lending-indices-` (renamed `instrument_type a_token→lending`); **`2022-03-12…2022-10-31` Aave is UNIQUE** (NOT in `lending-indices-`, which starts 2022-11-01).     | DELETE-AFTER — **but MIGRATE/BACKFILL the unique 2022-03..10 Aave range into `lending-indices-` FIRST** (else ~8 months lost) + redirect `evm_defi_handler`.                                                                                                                                                                                                                               |
| **`solana-defi-prd`** + `solana-defi`                                                                                                          | bare `solana_defi/<proto>/<date>/` (orca/raydium/kamino/**marinade**); stale 2026-05-12                                                                                                                        | LEGACY (no hive keys at all)                                                                        | ❌ NO                                               | **DUPLICATE** for orca/raydium/kamino (≈ `market-data-tick-defi` + `dex-pools-`). ⚠️ **`marinade` (mSOL LST) not observed in any migrated bucket → UNIQUE-suspect.**                                                  | DELETE-AFTER (post-migration + marinade verify). Migrate `marinade` LST into `lst-rates-` if unique.                                                                                                                                                                                                                                                                                       |
| `market-data-tick-defi-test` · `market-data-tick-test-defi` · `*-test-*` Solana/evm                                                            | (empty — 0 objects)                                                                                                                                                                                            | —                                                                                                   | n/a                                                 | EMPTY                                                                                                                                                                                                                 | DELETE (safe; no data).                                                                                                                                                                                                                                                                                                                                                                    |

**Delete-after-migration list (track to closure — nothing deleted until its row is GREEN):**

- [x] ✅ [SCRIPT] P0. **DONE (mtds@01fda7ce, slot-2 2026-06-09) — added `gas-fees` (7th) + `liquidations` (8th) migrator
      specs.** `gas-fees`: row_split, `venue_const="ALCHEMY"`, `chain_col="chain"` (canonicalises the venue-era split →
      ALCHEMY/`batch_onchain_rpc`). `liquidations`: path-grain (`batch_onchain_subgraph`). Both were data-bearing
      dedicated buckets the migrator omitted; now migrate to v9. union derives on-the-fly (`--phase discover` to bake
      for the VM apply). Verified: migrator tests 15 green, basedpyright + ruff clean, full mtds QG green (2679 passed).
      The real-prod dry-run (union footer-scan over 22933 gas objects) is VM-scale, gated with the apply. Original
      finding ↓.
- [x] ✅ [SCRIPT] P0. **(DONE — see ✅ row above; full context retained) `gas-fees` was OMITTED from
      `migrate_defi_full_v9_canonical.py` `_SPECS` (only 6) so `gas-fees-prd` was EMPTY (un-migrated).** gas is on the
      DeFi arb/carry critical path (net-of-gas profitability), so this is a P0 coverage gap, not optional. Add
      `"gas-fees": BucketSpec("gas-fees", "gas_fees", "spot_asset", grain="path")` to `_SPECS` (source shape matches the
      path-cell buckets: `day=/venue=/chain=/instrument_type=spot_asset/data_type=gas_fees/`). gas is CHAIN-grain (one
      shard per chain per day — same for all protocols on a chain). **Canonicalise the venue-era split**: old shards
      have `venue=<chain>` (ARBITRUM/AVALANCHE/BASE/BSC), the current handler writes `venue=ALCHEMY` (provider) — decide
      the canonical venue (recommend `ALCHEMY` provider + `chain=<chain>`, matching the handler) and remap old
      `venue=<chain>` → `ALCHEMY` in the migrator's venue canonicalisation. `gas_fees` is NOT in `_CANONICAL_UNION` →
      either bake it (run `--phase discover --buckets gas-fees`) or let it derive on-the-fly. pipeline_mode derives
      `batch_onchain_rpc` (correct — `SOURCE_PRIORITY(defi,gas_fees)=onchain_rpc`, gas via Alchemy RPC, NOT subgraph).
      Then a dry-run verify + add to the drain/snapshot/RESUME runbook lists (the `gas-fees` cron + bucket). Repo:
      market-tick-data-service. Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2 gas-fees coverage-gap
      audit 2026-06-08 (operator question).
- [x] ✅ [DATA] P1. **DONE — instruments-service@e866ca1ac5 (reconciled via
      `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`).** gas-fees MUST be in the manifest +
      data-status could-exist denominator (operator 2026-06-08).** gas is already RECORDED in the manifest per chain
      (`gas_fee_handler` → `DefiManifestRecorder.record_captured/empty`, `venue=ALCHEMY`/`chain=<chain>`,
      `data_type=gas_fees`, chain-grain) — but two things must follow the 7th-spec migration: (a) the gas-fees `_index`
      MANIFEST is rebuilt to reflect the migrated objects — **NOT automatic**: the migrator writes OBJECTS ONLY (it
      `_keep`-excludes `/_index/`), so the v9 manifest for the migrated gas objects requires a separate manifest rebuild
      over `gas-fees-prd` (see the manifest-rebuild-scope P1 below); (b) the **could-exist denominator** (IS
      `enumerate_expected_universe` + the deployment-api/UI data-status) must include `gas_fees` as a **per-chain
      expected cell** (one per chain × day in `GAS_FEE_CHAIN_START_DATES` coverage) so coverage % reflects gas
      presence/absence per chain — gas is chain-grain (NOT per-instrument), so the denominator is the chain set, not the
      instrument universe. Verify `gas_fees` is in `DATA_TYPES_BY_ASSET_GROUP["defi"]` + the validity matrix
      (`(defi, SPOT_ASSET, gas_fees)` valid) so it is not dropped as impossible. Repos: instruments-service +
      unified-api-contracts + deployment-api. Owner: vm-defi. parent_epic: manifest_master. Provenance: slot-2 gas-fees
      audit 2026-06-08 (operator question).
- [x] ✅ [SCRIPT] P1. **TOOL DONE (mtds@01fda7ce, slot-2 2026-06-09): `rebuild_defi_manifest` now takes `--bucket`** so
      it rebuilds each dedicated `-prd-` bucket's manifest from the migrated objects (run per dedicated bucket as the
      post-`--apply` step — the RUN itself is gated with the apply). Original gap ↓ retained. **MANIFEST-REBUILD SCOPE
      GAP — the migrator migrates OBJECTS but NOTHING rebuilt the dedicated `-prd-` bucket MANIFESTS over the migrated
      data (operator question 2026-06-08).** `migrate_defi_full_v9_canonical` writes OBJECTS only (excludes `/_index/`).
      `rebuild_defi_manifest.py` (the object→manifest rebuilder) is HARDCODED to
      `BUCKET_TEMPLATE="market-data-tick-defi-{project_id}"` (line 76; no `--bucket` arg) — it scans the LEGACY
      market-data-tick-defi bucket, **NOT** the 6+1 dedicated `-prd-` buckets the migrator writes (`dex-pools-prd` /
      `dex-swaps-prd` / `lending-indices-prd` / `perp-funding-prd` / `lst-rates-prd` / `oracle-prices-prd` /
      `gas-fees-prd`). The dedicated-bucket manifests today are built from LIVE handler per-VM shards + the per-bucket
      consolidator (reflecting live captures, NOT the migrated historical backfill). **Consequence**: after the object
      `--apply`, the migrated HISTORICAL rows are present as OBJECTS but ABSENT from the manifest → the deployment-api
      coverage % undercounts (objects exist, manifest blind) until a manifest rebuild runs over the dedicated bucket.
      **Fix**: generalise `rebuild_defi_manifest` to accept a `--bucket`/per-stem target (so it can rebuild each
      dedicated `-prd-` bucket's `_index` from the migrated objects, deriving source-aware pipeline_mode as it already
      does), and run it per dedicated bucket as the post-`--apply` step (paired with the consolidator). Confirm whether
      `market-data-tick-defi` is still a live manifest home or fully superseded by the dedicated buckets (the
      BUCKET_TEMPLATE hardcode suggests an unfinished cutover). This applies to ALL 7 dedicated DeFi market buckets, not
      just gas. Repo: market-tick-data-service. Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2
      object-vs-manifest scope audit 2026-06-08 (operator question).
- [ ] [STRATEGY] P2. **NICE-TO-HAVE — wire the downstream gas NET-COST consumer if absent.** The gas_fees DATA layer
      (per-chain gas PRICE) exists, but a grep of strategy-service/execution-service/features-service/utl found NO
      `gas_price × gas_units` net-of-gas cost computation (`estimate_gas` × gas_fees) — verify (grep-then-READ) whether
      DeFi arb/carry net-of-gas is wired (execution `estimate_gas` for gas_units × the gas_fees price); if missing, the
      gas data is collected but unused for profitability. Repos: strategy-service / execution-service. parent_epic:
      defi_master. Provenance: slot-2 gas-fees audit 2026-06-08.
- [ ] [DATA] P1. **VERIFY-then-MIGRATE the UNIQUE orphan gaps into the canonical dedicated buckets BEFORE any legacy
      delete** (else data loss on the irreversible cutover): (a) `evm-defi-prd` Aave V3 **`2022-03-12…2022-10-31`**
      range → backfill into `lending-indices-` (confirm absent there first via cf_manifest_audit); (b) `solana-defi-prd`
      **`marinade`** (mSOL LST) → confirm absent in `lst-rates-`, migrate if unique; (c) `market-data-tick-defi-prd`
      **KAMINO DEX pools** + the Solana **`lending_indices`** shards → confirm present in
      `dex-pools-`/`lending-indices-` (sampled ORCA/RAYDIUM are; KAMINO/lending unconfirmed), migrate if unique. Repo:
      market-tick-data-service (`scripts/migrate_defi_full_v9_canonical.py` could add these as extra source specs, OR a
      one-off backfill). Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2 orphan audit 2026-06-08.
- [x] ✅ [SCRIPT] P1. **RESOLVED-AS-MOOT 2026-08-14 (reconciled via
      `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`) — the redirect target no longer
      exists.** The "dedicated migrated-bucket" architecture this todo describes was RETIRED by a later decision
      (`gcs_bucket_estate_cleanup_2026_07_10`, `defi_dedicated_bucket_shared_migration_2026_07_13`) — every DeFi writer
      already converges on the ONE shared `market-data-tick-defi-{env}-{pid}` bucket. Full evidence:
      `plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md`. No code change is
      possible or needed. REDIRECT the 4 DeFi live handlers that write to NON-migrated buckets → the dedicated migrated
      buckets, so new writes stop creating orphans** (the orphan SOURCE). Handler→current-bucket map:
      `dex_swaps_handler` (`resolve_bucket_name(kind="market-data")` → `market-data-tick-defi`) → should write
      `dex-swaps`; `solana_defi_handler` (`get_write_bucket_name("market_data","DEFI")` → `market-data-tick-defi`) →
      should write the per-data_type dedicated bucket (`dex-pools`/`lending-indices`/`lst-rates`/`perp-funding`) per
      `_PROTOCOL_TO_DATA_TYPE`; `evm_defi_handler` (`get_write_bucket_name("evm-defi")`) → `lending-indices`;
      `aggregator_route_handler` (`get_write_bucket_name("aggregator-routes")`) → **RESOLVED 2026-08-08**: keep
      `aggregator-routes` a distinct, separately-migrated bucket — add it as a 9th migrator spec, do NOT fold.
      Rationale: `aggregator_route` is its own registered canonical UAC data_type
      (`unified-api-contracts/unified_api_contracts/registry/data_type_capability.py:802-813`, "DEX aggregator quote
      capture for batch replay via AggregatorRouteMatcher" — RouteLeg quote data, not raw swaps/pool-state),
      content-wise distinct from every existing bucket's data_type; this matches the SAME precedent this doc already
      applied to `gas-fees` (7th spec) and `liquidations` (8th spec) above — a confirmed-distinct dedicated-source
      data_type gets its own bucket, never folded into an unrelated one. Until redirected, this bucket keeps diverging
      from the canonical home that features/strategy read. Repo: market-tick-data-service. Owner: vm-defi. parent_epic:
      mtds_mdps_master.
- [x] ✅ [SCRIPT] P2. **DONE — market-tick-data-service@795ddf39e1 (reconciled via
      `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`).** Add `aggregator-routes` as the 9th
      `migrate_defi_full_v9_canonical.py` migrator spec** (per the 2026-08-08 decision above) mirroring the
      `gas-fees`/`liquidations` additions: register a `BucketSpec` for `aggregator-routes` → `aggregator-routes-prd`,
      confirm the source path shape, dry-run then `--apply`, rebuild the manifest over the migrated objects (same
      post-apply step already established for the other 8 dedicated buckets). Repo: market-tick-data-service. Owner:
      vm-defi. parent_epic: mtds_mdps_master.
- [x] ✅ [MTDS] P0. **M-COORD-7 — 41 coarse `pipeline_mode="batch"` OBJECT-PATH literals in DeFi handlers (batch≠live
      regression + STEP-5.85 ship-blocker) — FIXED (mtds@57242af5, slot-2 2026-06-08).** Filed by slot-4 while shipping
      the sports fix: mtds STEP 5.85 hard-failed on 41 pre-existing coarse `pipeline_mode="batch"` literals in 25 DeFi
      CLI handlers (the `write_defi_rows(...)` OBJECT writes), causing (a) a **batch≠live regression** — DeFi live
      objects landed coarse `pipeline_mode=batch/` while the migrator (mtds@f80c50f1) writes source-aware — and (b)
      **blocked every mtds code ship** (no QG-green sentinel). **Root-cause fix (centralised)**: `write_defi_rows`
      (`canonical_write.py`) now UPGRADES a coarse `"batch"`/`None` `pipeline_mode` to the source-aware
      `{mode}_{source}` via the SAME `derive_pipeline_mode_for_row` the v9 migrator + `rebuild_defi_manifest` use →
      live/batch OBJECTS land canonical (`pipeline_mode=batch_<source>/`), byte-identical to the migrated batch data
      (Batch=Live by construction); all **41 coarse literals removed** from the handler call sites (→ `None` → derive) +
      the now-stale "coarse ingestion" comments removed. STEP 5.85 = **0 coarse literals** (unblocks mtds ships). **22
      handler-test path assertions + 4 old-migrator-test assertions updated** to the derived source-aware paths (e.g.
      dex_pool_state/lending_indices/lst_rates/vault/eigenlayer→`batch_onchain_subgraph`; perp_funding (incl. Solana
      DRIFT, ASTER, GMX, PACIFICA)→`batch_hyperliquid`; oracle CHAINLINK→`batch_chainlink`, PYTH→`batch_pyth_hermes`).
      **1359 tests green; 0 coarse literals; basedpyright clean.** Repo: market-tick-data-service. parent_epic:
      mtds_mdps_master. Provenance: slot-4 M-COORD-7 → slot-2 fix 2026-06-08.
- [ ] [DATA] P1. **DELETE the duplicate/legacy DeFi orphan buckets AFTER (1) migration GREEN + (2) the unique-gap
      migrations above complete + (3) the redirects land + (4) a final cf_manifest_audit confirms 0 unique rows
      remain**: `market-data-tick-defi{,-prd}` · `solana-defi{,-prd}` · `evm-defi{,-prd}` (post unique-gap migration) ·
      the 4 empty `*-test-*` DeFi buckets (delete now — 0 objects). Use `gcs_delete_object` / bucket lifecycle, NOT
      `gsutil` per-object. Snapshot each `_index` to `_index/snapshots/pre_delete_<date>.parquet` first (rollback).
      Owner: vm-defi (operator sign-off on the bucket deletes — destructive). parent_epic: manifest_master. Provenance:
      slot-2 orphan audit 2026-06-08.
- [ ] [UAC] [SCRIPT] P2. **Solana DeFi source = actual names (folds the prior P2 + the live-handler Solana stamp).**
      Once Solana writes land in the dedicated buckets (redirect above), the migrator/rebuild + live handlers must stamp
      the ACTUAL Solana source, not the chain-agnostic `onchain_subgraph`: add Solana venue overrides to UTL
      `_VENUE_OVERRIDES` (ORCA/RAYDIUM/PHOENIX/KAMINO/MARINADE/JITO→`BATCH_SOLANA_RPC`; DRIFT→`BATCH_HELIUS_RPC`;
      MARGINFI/SOLEND→**`BATCH_DEFILLAMA`**) **+ ADD the missing `BATCH_DEFILLAMA`/`LIVE_DEFILLAMA`/`REPLAY_DEFILLAMA`
      enum members** to UAC `pipeline_mode.py` (+ `source_string_for` `defillama` + `default_transport_for_source`
      `defillama→rest` + the closed-set symmetry tests). Then drop the handler hardcodes so
      `derive_pipeline_mode_for_row` is the single SSOT. Repos: unified-trading-library + unified-api-contracts +
      market-tick-data-service. Owner: vm-defi. parent_epic: manifest_master. Provenance: slot-2 ⑪/P2 audit 2026-06-08.
      **EXTENDED 2026-06-08 — multi-VENUE perp has the same coarseness**:
      `SOURCE_PRIORITY(defi, perp_funding)=[hyperliquid]` (single) so `derive_pipeline_mode_for_row` returns
      `batch_hyperliquid` for ALL defi perp venues — ASTER, GMX, PACIFICA, **Solana DRIFT** all resolve to
      `batch_hyperliquid`/`source=hyperliquid` (only LIGHTER has an override → `batch_tardis`). This is CONSISTENT
      (object==manifest==migrator all derive the same, so the M-COORD-7 fix + the migration are correct) but the source
      LABEL is wrong for non-Hyperliquid perp DEXs. **RULED 2026-07-28 (retagged — this per-venue source decision is no
      longer operator-gated): add real per-venue overrides — `ASTER` → `batch_aster` (source `"aster"`, new
      `BATCH_ASTER` enum member — ASTER funding is fetched from ASTER's own API, not Hyperliquid), `DRIFT` →
      `batch_helius_rpc` (source `"helius"`, consistent with DRIFT's DEX-side label above — same Solana RPC/Helius
      provenance for its funding data), `PACIFICA` → `batch_pacifica` (source `"pacifica"`, new `BATCH_PACIFICA` enum
      member).** Reasoning: same as the Solana dex/lending ruling above — this is canonicalisation, not a hack; the
      mandate is to do it properly rather than leave the coarse-but-consistent label in place indefinitely.
      Full-completion scope: add the missing `BATCH_ASTER`/`BATCH_PACIFICA` (and `BATCH_DEFILLAMA`/`LIVE_DEFILLAMA`/
      `REPLAY_DEFILLAMA` from the Solana side) enum members to UAC `pipeline_mode.py`, wire `source_string_for` +
      `default_transport_for_source` for each, add the venue overrides to UTL `_VENUE_OVERRIDES`, drop the handler
      hardcodes so `derive_pipeline_mode_for_row` is the single SSOT, and update the closed-set symmetry tests — no
      partial rollout that leaves some venues on the coarse `hyperliquid`/`onchain_subgraph` label and others fixed.
      (GMX dropped from this list — REMOVED 2026-07-25, see
      `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; no `batch_gmx` override needed.)

**Note on the migrated-bucket residue (NOT orphans):** `dex-pools-prd`/`dex-swaps-prd` carry BOTH old-format
`day=/category=defi/` AND partial prior-apply canonical objects (one sample showed `pipeline_mode=BATCH_ONCHAIN_RPC`
UPPERCASE — an OLD partial-apply artifact; the current migrator stamps the lowercase `.value` `batch_onchain_subgraph`).
The `--apply` re-conforms + the RD4 legacy-delete removes the superseded old-format objects in the SAME bucket, so these
are migration-in-flight residue the apply resolves — NOT a separate orphan. (Flagged for the apply-run to confirm the
RD4 legacy-delete covers the UPPERCASE residue too.) parent_epic: mtds_mdps_master. > **FINDING (slot-5 prediction,
2026-06-08) — two updates to this MTDS-QG-red item:** > (a) **`rebuild_prediction_manifest.py` is now SPLIT** (954→692
L, mtds@c571445d) → REMOVE it from the >900 list; > the remaining >900 files are non-prediction. (b) **NEW gate-0
blocker not previously listed: a committed > `uv.lock`↔`pyproject.toml` desync on the MTDS LDR HEAD.** `uv lock --check`
FAILS — the committed `pyproject.toml` > declares `pyarrow-stubs` + `mypy-boto3-{logs,sns,sqs}` that are absent from the
committed `uv.lock`, so the QG > aborts at its FIRST gate (`❌ uv.lock out of sync`) BEFORE file-size/basedpyright/tests
even run. Mechanical > re-sync (`uv lock` adds the 4 stub pkgs, ~52 LOC; precedent mtds@10930dbd "re-sync uv.lock to
pyproject"). Until > this lands, NO MTDS `quality-gates.sh` reaches green regardless of the file-length work — fix it
FIRST in this > slot-2 sweep. (Slot-5 did not fix it: it completes another commit's incomplete dep edit — out of
prediction AG + > FM1 foreign-work-bundling risk.) **✅ RESOLVED 2026-06-08 (slot-2, operator decision A):** (0)
**gate-0 re-locked** (mtds@d544f15c — `uv lock` to current pyproject; `uv lock --check` green) BUT this is **recurring
lock-drift** (the type-stubs flip-flop in pyproject between agents; `dbbbef8a` added them, a later commit removed them)
→ **handed to the dep/CI lane** (slot-1 `update-dependency-version.yml` prevention + settle the type-stub flip-flop);
NOT a thing to keep manually re-locking. (1) **file-size = 15 pre-existing non-`scripts/` files** (orchestrator.py 4219
etc.) → **DEFERRED to the named successor `plans/active/mtds_file_size_refactor_2026_06_08.md`** (post-migration;
splitting the migration's own `orchestrator.py` pre-apply is high-risk for zero migration benefit). **NOT
migration-blocking**: file-size loop excludes `./scripts/*` (migration code clean); MTDS migration code ships via
basedpyright-on-touched; `--apply` runs from VM/tarball not the sentinel. (The hollow-sentinel harness finding below is
the related ship-hygiene item.)

- [x] ⛔ [INFRA] P2. **RESOLVED-NO-ACTION 2026-08-02 (see scoping-read annotation below).** 🔴 LOCAL QG HARNESS collects
      the WRONG test suite for some repos — the green sentinel is HOLLOW (surfaced slot-7 2026-06-08).** Running
      `bash scripts/quality-gates.sh --no-fix` for **instruments-service** AND **market-tick-data-service** on this host
      produced a `[3/6] TESTS` run with `rootdir: …/unified-trading-pm`,
      `configfile: unified-trading-pm/pyproject.toml`, **`collected 6 items`** — it ran only PM's 6
      `tests/integration/test_pm_scripts_integration.py` tests, NOT the repo's own suite (IS has ~3,267 tests; its own
      `pyproject.toml` declares `[tool.pytest.ini_options] testpaths=["tests"]`). The QG still **exits 0 + writes
      `.qg_last_passed_sha`**, so the commit-quality-boundary sentinel for those repos is hollow — a code change can
      ship "QG-green" without its tests ever running (the peer's `mtds@67786887` tradfi-reader change passed this same
      hollow gate). **Contrast**: the UAC QG ran its FULL suite (8,617 passed / 3 pre-existing
      `test_schema_version_matrix.py` failures / 550 skipped) — so it is IS/MTDS-specific (possibly the
      qg-governor-queued subprocess cwd, or a `PROJECT_ROOT`/rootdir mis-resolution when run under contention).
      **Impact**: undermines QG confidence for the migration code on the apply critical path. **Mitigation used this
      session**: slot-7 ran the touched tests directly in each repo `.venv` (IS `enumerate` 88 passed · UAC
      F2+era_b+source_priority 106 passed) to verify before shipping. **Owner: vm-cross-cutting / QG-harness** —
      root-cause the rootdir/cwd resolution (likely `quality-gates-base/base-service.sh` `cd "$PROJECT_ROOT"` vs the
      governed subprocess) so per-repo QGs collect their own suite. Repos: unified-trading-pm
      (`scripts/quality-gates-base/base-service.sh`) + per-repo `quality-gates.sh`. parent_epic: manifest_master.
      Provenance: slot-7 cross-cutting sweep 2026-06-08. **na-eligibility-audit 2026-08-01: not extracted — already
      assessed by `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s Operator-gated/Deferred section: "bounded-sounding
      but under-evidenced (zero coverage found anywhere) — needs a scoping read before it's draftable." Stays KEEP-NA
      pending that scoping read; not re-litigated here.** **Scoping read 2026-08-02
      (`plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01_finalize.md` todo 2, slot-13) —
      RESOLVED-NO-ACTION on code evidence, not re-litigated further.** Read `scripts/quality-gates-base/qg-common.sh`
      (lines 102-136): a **WORKTREE-IDENTITY GUARD** shipped 2026-07-24
      (`qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md`, a related but distinct
      sibling-worktree incident) now hard-fails (`exit 1`) the instant `PROJECT_ROOT` disagrees with
      `git rev-parse     --show-toplevel` for the invoking cwd — exactly the PROJECT_ROOT/rootdir mis-resolution class
      this finding's "Owner" note names as the suspected cause. `base-service.sh:61` `cd "$PROJECT_ROOT"` runs pytest
      from that now-guarded cwd, so pytest's own upward rootdir search would find the REPO's own `pyproject.toml`
      (`testpaths=["tests"]`) first, not PM's — the silent "collected 6 items, exits 0" hollow-pass this finding
      describes can no longer happen unnoticed; a mismatch now aborts the gate loudly instead. **Could not live-repro
      this session**: `uv run pytest --collect-only` in this slot's `instruments-service` stalled past a 90s bound (no
      `.venv` yet, `uv sync` itself hung) — consistent with ordinary shared-host contention, not a repro of the original
      bug, so this is a code-evidence verdict, not a fresh empirical one. If a NEW hollow-pass instance is ever observed
      (a QG run that exits 0 but visibly collects the wrong repo's tests), file a fresh issue doc rather than reopen
      this line.
- [x] ✅ [DATA] P1. **DONE (na-eligibility-audit 2026-08-03)** — `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s
      corresponding todo shipped both fixes: (1) the instruments-service `by_date` writer regression, and (2)
      `migrate_instruments_store_v9.py`'s `canonical_object_rel` doubled-`day=` collapse. Repo: instruments-service.
      `quality-gates.sh` green. **DeFi instruments-store `by_date` has a DOUBLED `day={D}/day={D}/` prefix on the recent
      tail** (~2026-05-05 onward — `day=2026-05-05/07` confirmed doubled; `day=2026-05-03` and ALL earlier days are
      single, canonical `day={D}/venue={V}/instruments.parquet`). Surfaced by the G2 verify dry-run 2026-06-07 (slot-2).
      **TWO defects**: (1) an instruments-service `by_date` WRITER regression that nested a second `day=` for recent
      snapshots
      (`gs://instruments-store-defi-prd-…/instrument_availability/by_date/day=2026-05-07/day=2026-05-07/venue=AAVEV3-ARBITRUM/instruments.parquet`);
      (2) the slot-7 v9 OBJECT migrator (`migrate_instruments_store_v9.py` `canonical_object_rel`) inserts
      `pipeline_mode=/asset_group=` after the FIRST `day=` but does NOT normalise the second → its projected canonical
      path is MALFORMED
      (`day=2026-05-07/pipeline_mode=batch_instruments_service/asset_group=defi/day=2026-05-07/venue=…`). The
      catalogue/enumerate are UNAFFECTED (`build_instrument_catalogue` uses `_DAY_RE.search` + `_VENUE_RE.search` →
      resolves the correct day+venue), so this is a **G4 object-migration gate**, not a CF-14 blocker. **Fix BOTH before
      the gated defi §H object `--apply`**: dedupe/normalise the writer + add a `day=…/day=…` collapse (or a pre-flight
      reject) to `canonical_object_rel`. Repos: instruments-service (writer + slot-7 migrator). parent_epic:
      manifest_master.
- [ ] [UAC] P3. **NICE-TO-HAVE — defi G1-ENUM matrix `POOL` row is union-coarse**: the derived
      `valid_data_types_for_instrument_type("defi","POOL")` is the UNION across all POOL-declaring protocols →
      `{dex_pool_state, dex_pool_swaps, gas_fees, lending_indices, liquidations, perp_funding}`, so a pure-DEX pool
      (e.g. UNISWAP_V3) would seed `expected_unattempted` for `perp_funding`/`lending_indices`/`liquidations` it never
      produces (a perp-DEX like GMX legitimately needs them). NOT an impossible-combo (gate-(a) still passes — no
      `odds`/`oracle_prices` leak into POOL), but a per-protocol grain would tighten the denominator. Repo:
      unified-api-contracts (`registry/capability_declarations/_defi.py` PROTOCOL_CAPABILITIES). parent_epic:
      manifest_master. Provenance: G2 verify 2026-06-07 (slot-2).
- [ ] [SCRIPT] P3. **NICE-TO-HAVE — defi migrator `_list_objects` L1 find is a full-bucket scan** (re-verify 2026-06-07,
      slot-2): `migrate_defi_full_v9_canonical.py:570` always issues `_safe_find(fs, {base}/{dir_name})` for the L1
      layout, but all 6 dedicated source buckets are `day=`-partitioned today (no top-level `{dir_name}/` or
      `raw_tick_data/` tree) → that L1 prefix matches nothing yet gcsfs enumerates the whole bucket (a 3-day local
      dry-run hit a >280 s timeout on it; the L1 `dex_pools` find alone >120 s isolated). NOT a correctness issue
      (returns the correct empty set; date-scoped runs DO complete — the earlier `day=2024-06-01` dry-run finished
      0-errors) and laptop-variable, but it wastes a whole-bucket enumeration per bucket on the in-region VM `--apply`
      too. Gate the L1 find on a cheap existence probe (or drop it) — **validate against the whole corpus on the VM
      first** so a bucket with a genuine L1 tree is never silently skipped (data-loss risk). Repo:
      market-tick-data-service. parent_epic: mtds_mdps_master. **TRIAGED 2026-06-07 (slot-2) → SPEED-NOTE,
      NON-BLOCKING:** the `--apply` does NOT date-shard `_list_objects` (the `launch-canonical-migration-vm.sh` launcher
      runs ONE VM over the full date range → exactly ONE `_list_objects` per bucket = 6 wasted whole-bucket scans total,
      not N×6), and the in-region VM completes whole-bucket scans (the baked-union `discover_union` run over the whole
      corpus proved it). So the L1 find adds wall-clock to the apply but never blocks it. Per the apply-ready criterion
      (fix only if it blocks at scale) this stays a **deferred optimisation**, not an apply-gate. Kept P3.

### G2-defi readiness verdict (WAVE 2 verify pass — slot-2, 2026-06-07)

**VERDICT: defi migration CODE is DRY-RUN-GREEN on LDR — the manifest+data `--apply` is code-ready, correctly GATED.**
Re-run on the WAVE-1 source-aware code against real prod GCS (read-only). No code changed (verify pass = dry-runs only);
this is a `docs(plans):` flip.

- **①+⑨ MTDS migrator dry-run (CF-3/CF-13) GREEN — mtds@f80c50f1.**
  `migrate_defi_full_v9_canonical --start-date 2024-06-01 --end-date 2024-06-01` (dry, all 6 buckets) → 0 errors, 0
  needs_attr. Projected PATHS + in-process `_conform` COLUMNS both verified source-aware:
  `dex_pool_state→pipeline_mode=batch_onchain_subgraph` (source=`onchain_subgraph`), `dex_pool_swaps→batch_onchain_rpc`
  (source=`onchain_rpc`); both `schema_version=9`, `asset_group=defi`, `transport=rest` (separate COLUMN), per-row
  `available_at` (EOD UTC), canonical underscore `data_type`, `pipeline_mode=…/asset_group=defi/` LEFT of `venue=`;
  legacy source `category=defi` correctly migrated. NOT coarse `batch`/blank.
- **②+③ instruments-store v9 index dry-run (CF-1/CF-2/CF-4) GREEN — is@2971a064.**
  `migrate_instruments_store_v9 --asset-group defi --skip-objects` (dry) → prd `_index` **125,242 rows v8→v9 (100%)**:
  schema_version `{9:125242}`, source=`instruments_service`, transport=`rest`,
  pipeline_mode=`batch_instruments_service`, asset_group=`defi`, available_at filled on all rows, `category` dropped.
  cf_manifest_audit projection → CF-GREEN. (Object-walk side: GREEN for canonical single-`day=` objects; the recent
  doubled-`day=` tail is the P1 finding above — a G4 gate, not an index blocker.)
- **③ catalogue + enumerate (CF-14) — mechanism GREEN, candidate-count GATED.**
  `build_instrument_catalogue --asset-group defi --dry-run` on the now-populated prd `instrument_availability/by_date/`
  → **64,724 by_date snapshots enumerated** for rollup (listing GREEN; the prior "0 rows / -prd- empty" finding is
  RESOLVED — by_date is now populated 2020-01-20…2026-05-08). The full LOCAL rollup EXCEEDED a 580s budget downloading
  64,724 small parquets (exit 124, did NOT finish) → the rollup + enumerate candidate-count run needs a VM / longer
  timeout, deferred with the gated G1.run write below (the count is downstream of the gated catalogue WRITE anyway).
  Validity-matrix slice VERIFIED correct (UAC@97c26dbe, enumerate@6ea46565): **all 6 defi instrument_types present in
  by_date map cleanly** — `POOL`/`LENDING`/`SPOT_PAIR`/ `PERPETUAL`/`STAKING`/`YIELD_BEARING`, zero
  unmapped/over-fan/None-fallthrough; `_enumerate_v2_defi` is G1-ENUM shape-aware (genesis/launch/lifecycle +
  bundle-skip). Full enumerate candidate-count is gated on the **G1.run catalogue WRITE** (a `--apply-write`, correctly
  GATED on GATE C below) — not runnable read-only without a persisted catalogue parquet.
- **④⑤⑥⑦⑧ (CF-5/6/7/8/10/11/12)** ride the WAVE-1 code (rebuild `record_zero_rows`/typed reasons, A7 fetch-failure
  classification, batch=live single path) — unchanged this pass; verified by the 25/25 credential-free unit suite.

**Remaining gates for the defi `--apply` (G4) — all correctly held:**

1. **G0 ∧ G1 ∧ G3** (cross-AG coordinator gates).
2. **GATE C — instruments-store-defi `_index` v9 walk** (currently 0% v9 on disk: 125,242 v8; dry-run proves the
   transform is correct — the WRITE is the gated `--apply`).
3. **DeFi IS backfill + the doubled-`day=` writer/migrator fix** (P1 above) before the §H object `--apply`.
4. **Pre-migration drain** (all VMs stopped + consolidated) before any object `--apply`.

Sampled-not-walked disclosure: MTDS dry-run sampled `day=2024-06-01` across all 6 buckets (path+column verified) +
in-process `_conform` of real dex-pools/dex-swaps objects; instruments-store `_index` transform walked all 125,242 rows;
by_date instrument_type coverage sampled across all venues for `day=2025-12-15`+`2026-05-03` (+ a 6-day spread). The
doubled-`day=` boundary was sampled day-by-day across 2026-05-01…08. The full 64,724-parquet catalogue rollup count +
the enumerate candidate-count are deferred to the gated G1.run write.

### 🟢 DeFi APPLY-READY VERDICT + completed 7+2-point audit (slot-2, 2026-06-07)

> **VERDICT: DeFi is APPLY-READY on LDR.** Every G1+G2 dry-run is green and the 7+2-point audit passes; the migration
> CODE is correct and no code change is owed before `--apply`. **The only things between DeFi and the real `--apply` are
> OPERATIONAL gates** (drain + the gated WRITE runs), not code. No `--apply` run in this pass (gated).

**7+2 audit — per-CF verdict (CF-1…CF-14; data-state reads, not constants):**

| CF         | Invariant                                               | defi verdict    | Evidence (sampled vs walked)                                                                                                                                                                                                                               |
| ---------- | ------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CF-1       | schema_version=9                                        | 🟢              | migrator `_conform` stamps `9` on real ORCA parquet (sampled); IS `_index` transform → `{9:125242}` (WALKED all rows)                                                                                                                                      |
| CF-2       | `asset_group=` not `category=` (path+row)               | 🟢              | real source `category=defi`→canonical `asset_group=defi/` path key + column; `category` dropped from `_index` (walked)                                                                                                                                     |
| CF-3/CF-13 | source-aware `pipeline_mode={mode}_{source}` (path+col) | 🟢              | `batch_onchain_subgraph`/`batch_onchain_rpc` per-shard on real paths+cols; coarse `batch`/blank retired; 14-case derivation incl. antipattern-retired `batch_hyperliquid` (sampled)                                                                        |
| CF-4       | `source` COLUMN every external cell                     | 🟢              | `source=onchain_subgraph` on real rows; IS rows `source=instruments_service` (walked). P2 `SOURCE_PRIORITY` registry-gap todo open (derives cleanly via fallback today)                                                                                    |
| CF-5       | typed `EmptyConfirmedReason`                            | 🟢              | defi writers use `DefiManifestRecorder.record_zero_rows` + `EXPECTED_PRE_VENUE_LAUNCH`/`EXPECTED_PRE_GENESIS_CHAIN` (code grep)                                                                                                                            |
| CF-6       | `expected_unattempted` materialised                     | 🟢 (code)       | shape-aware `_enumerate_v2_defi` + `build_instrument_catalogue` produce the could-exist seed; the apply-write RUN is the gated G1.run                                                                                                                      |
| CF-7       | canonical data_type / flat venue+chain / `{VENUE}_V{N}` | 🟢              | input `dex_pools`→typed `dex_pool_state`; `SUSHISWAP`→`SUSHISWAP_V3` on real paths (sampled)                                                                                                                                                               |
| CF-8       | per-row `available_at`, no lookahead                    | 🟢              | real ORCA `available_at=2026-05-28T21:21:46` write-time; IS `available_at` filled on all 125,242 rows (walked)                                                                                                                                             |
| CF-9       | env-split bucket via `resolve_bucket_name`              | 🟢              | migrator/rebuild build buckets via `resolve_bucket_name`; the `gs://` occurrences are docstring/log strings, not f-string bucket construction (grep)                                                                                                       |
| CF-10      | no phantom/date-impossible captured                     | 🟢 (projection) | IS `_index`: 57,466 null→`captured` from `instrument_count>0`, 0 dishonest captured-but-empty (walked); object-presence phantom sweep is `reconcile_phantom_manifest_rows_all` post-apply                                                                  |
| CF-11      | fetch-failure → `attempted_failed`                      | 🟢              | defi handlers (mev/evm_defi/perp_funding) call `record_failed(...)`; no `except: return []` swallow (grep)                                                                                                                                                 |
| CF-12      | batch=live symmetry                                     | 🟢              | one code path (no defi live-only data_types); verified by the 25/25 credential-free unit suite                                                                                                                                                             |
| CF-14/⑧    | IS-catalogue could-exist ROOT green                     | 🟢 (mechanism)  | `-prd-` by_date POPULATED (64,724 parquets); shape-aware producer runs; validity-matrix slice correct (IS adapters emit `POOL`/`STAKING`/`LENDING`/`SPOT_PAIR`/`YIELD_BEARING`, all matrix-covered). Full rollup candidate-count = gated G1.run (VM-scale) |

**Sampled-vs-walked (audit-level)**: WALKED — the full 125,242-row instruments-store `_index` transform (deterministic,
no object probe). SAMPLED — MTDS migrator conform on the latest populated day per bucket + a real 14,093-row ORCA
parquet (the whole-corpus migrator walk runs on the in-region VM); the 64,724-parquet catalogue rollup LISTED but not
fully rolled up locally (VM-scale). Adapter/handler CF-5/9/11/12 verified by code grep, not a corpus walk. **Remaining
gaps**: the full catalogue rollup + enumerate candidate-count (gated G1.run VM run) and the object-presence phantom
sweep (post-apply) — both downstream of the gated WRITE, not code.

**Remaining gates to the real `--apply` — ALL OPERATIONAL (no code owed):**

1. **G0** GREEN ✓ (Phase-0 source-aware writer code landed) · **G3 UNION view SHIPPED ✓** (deployment-api@4dd2575 +
   deployment-ui@0dc40eb, pm@822393880).
2. **GATE C — instruments-store-defi `_index` v9 WRITE**: run `migrate_instruments_store_v9 --asset-group defi --apply`
   (the dry-run proved the 125,242-row transform projects 100% v9; this is the gated WRITE, not a code fix).
3. **DeFi IS backfill complete** + the gated `build_instrument_catalogue`+`enumerate_expected_universe --apply-write`
   G1.run VM run (catalogue/enumerate UNAFFECTED by the doubled-`day=` bug; that bug is a §H **object**-migration gate,
   fixed before the §H object `--apply` only).
4. **Pre-migration drain** (all GCP+AWS VMs stopped + manifest consolidated + snapshot) before any object `--apply`.

No code-correctness blocker remains for the DeFi migrator/rebuild/enumerator. The 3 open todos are: P1 doubled-`day=` (a
§H object-migration gate, instruments-service) · P2 `SOURCE_PRIORITY` registry tidy · P3 POOL union-coarse + P3 L1-find
speed-note (both deferred optimisations, non-blocking).

\*\*Regression re-confirmation (slot-2, 2026-06-07) — STILL APPLY-READY after the shared bundle-grain + sports-catalogue

- matrix changes landed.** Targeted check (the changed surface vs defi, not a blind re-run): the bundle-grain axis
  (`grain_for_instrument_type`, uac@dd7fa100) returns **`leaf` for ALL 6 defi instrument_types**
  (POOL/LENDING/SPOT_PAIR/ PERPETUAL/STAKING/YIELD_BEARING) — only cefi `options_chain`/`option` are
  `bundle_by_underlying`, so defi never collapses to a bundle; the defi validity-matrix slice is **unchanged** (POOL 6 ·
  LENDING 4 · SPOT_PAIR 2 · PERPETUAL 2 · STAKING 2 · YIELD_BEARING 4 dts, zero over-fan). The sports-league fix
  (uac@aff80339) is sports-only. The migrator (`migrate_defi_full_v9_canonical.py`) is unchanged at **mtds@f80c50f1**
  and its derivation deps (`source_string_for`/`default_transport_for_source`/`derive_pipeline_mode_for_row`) were
  untouched by the recent batch → dry-run output is provably identical to the green run above. **No new code owed; HOLD
  stands.\*\* Remaining gates remain purely operational (drain + the gated v9 instruments-store walk + IS backfill).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added dex_swaps_handler.py/canonical_write.py,
  the real handler + writer touched by the open P1 bucket-redirect todo.
- **2026-08-08 (doc-hygiene, digest close-out)**: Corrected the "DeFi collection gaps" retriage todo's stale
  `eigenlayer_rewards` scheduling claim — verified live `deployment-service/terraform/gcp/defi_collection_scheduler.tf`
  has had a `collect-eigenlayer-rewards` cron since `7b1490f7` (2026-04-25); no scheduling gap remains for that
  data_type. `native_staking_rates` confirmed genuinely still unscheduled (fresh grep, same file) — left flagged. Todo
  stays `[ ]` open (the MVP-scope confirmation for the remaining ~10 scaffolds is unchanged, genuinely still needs the
  operator). Aggregator-routes todo and the MVP-triage question itself not touched.
- **na-corpus-digest-closeout 2026-08-08, reconciliation**: this question was answered TWICE the same day by two
  independent passes that didn't know about each other — this round5 entry (keep distinct, precedent-based) vs. a live
  interactive operator session that same day, asked directly with live volume data (aggregator_route currently 0
  captured rows), which picked "fold into an existing bucket for now" reasoning that a dedicated bucket for an empty
  stream is premature. Reconciled (operator unavailable to re-ask, `/autonomous` in effect): **keeping distinct**, i.e.
  this entry's original resolution stands, for a reason neither pass had in view — the redirect cost is symmetric either
  way (`aggregator_route_handler` already writes to its own `aggregator-routes` bucket today; "fold" doesn't avoid a
  redirect, it just redirects to a shared bucket instead of a dedicated one), so the "cheap because nothing to migrate
  yet" premise behind "fold in" doesn't actually differentiate the two options — and keeping distinct preserves
  consistency with the identical gas-fees/liquidations precedent already applied twice in this same doc. Flagged in the
  NA-corpus digest artifact for the operator to override if they disagree; this is the lower-conviction of the two
  answers, not a confident close.
- **round5-na-digest-defi 2026-08-08**: resolved the aggregator-routes bucket-architecture question (redirect todo's
  operator-decision clause) — keep it a distinct, separately-migrated bucket (9th migrator spec), same precedent this
  doc already applied to gas-fees (7th)/liquidations (8th): a confirmed-distinct canonical data_type
  (`aggregator_route`, UAC `data_type_capability.py:802-813`) gets its own dedicated bucket, never folded. Filed the
  mechanical follow-up as a new `[SCRIPT] P2` todo. The "~10 untriaged DeFi collection-gap scaffolds" MVP-scope question
  (bridge_events/flash_loan_events/flash_loan_availability/governance_events/liquidation_events/mev_events/
  position_data/token_transfers/rewards/vault_apy/vault_tvl) stays genuinely operator-gated — a real per-data_type
  product-scope call spanning 11 data types with no blanket precedent (the sibling doc
  `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md` explicitly bars a flat-clip decision for the same class
  of never-collected/out-of-MVP residual, and only speaks generally to 4 of these 11, not all of them individually).
- **round5-na-digest-defi 2026-08-08 (apply pass, item 67)**: the "~10 untriaged scaffolds" MVP-scope question above IS
  now answered (this is a separate operator Q&A round from the same-day entry directly above, which pre-dates this
  answer) — operator ruling: `liquidation_events`, `token_transfers`, `governance_events` move to MVP scope (wire a real
  source); the remaining 8 (`bridge_events`/`flash_loan_events`/`flash_loan_availability`/`mev_events`/
  `position_data`/`rewards`/`vault_apy`/`vault_tvl`) stay deprioritized scaffolds unless the operator says otherwise.
  Updated the coverage-matrix table's disposition column for all 11 rows to match, and filed 3 concrete `[DATA]` P2
  "wire a real source" todos (one per newly-in-scope data_type) immediately below the retagged todo — sources not built
  this session, just properly scoped+filed per the round5 apply-phase instruction.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-read the full open-todo set (17
  items). The doc mixes genuinely bounded items (the 3 new "wire a real source" todos, the aggregator-routes 9th
  migrator-spec todo, the per-venue SOURCE_PRIORITY overrides — already ruled 2026-07-28) with several that remain
  hard-gated: Era-B legacy retirement is explicitly `GATED on cefi+tradfi G4 apply complete`; the delete-after-migration
  bucket purges require `Owner: vm-defi (operator sign-off on the bucket deletes — destructive)`; GATE C
  (instruments-store v9 WRITE) is an operational apply gate, not worker-determinable. Because `assigned_vm` flips
  whole-doc, the destructive-delete-gated items block a clean flip. Flagging for a future round: the 3 "wire a real
  source" todos + the aggregator-routes spec are strong RECLASSIFY candidates if forked into their own child plan
  (mirroring this same doc's own gas-fees/liquidations-spec precedent) — not done this round (scope: classification, not
  authoring a new fork). Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 862-line migration audit-log hub, 14 open items
  (grep-confirmed). Whole-doc RECLASSIFY blocked by 3 genuine gates named in the doc's own 2026-08-08 round7 entry: GATE
  C (instruments-store-defi `_index` v9 write, currently 0% v9, an operational apply-gate), Era-B legacy retirement
  (gated on cefi+tradfi G4 apply complete), and the delete-after-migration bucket purges (explicit operator-sign-off
  owner: vm-defi). Doc stays `assigned_vm: NA`.
