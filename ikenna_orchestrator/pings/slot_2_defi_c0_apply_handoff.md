# Resume prompt — Slot 2 / DeFi lane / C0 v9 canonical migration **APPLY + DELETE** (handoff 2026-06-02)

You are **slot 2** (DeFi lane) in `.tabs/2`, branch `tab/ikennaigboaka/2` tracking `origin/live-defi-rollout` (LDR).
Operator: Ikenna. **Read this whole file + the SSOTs it names before doing anything.** Boot:
`cd .tabs/2 && for r in unified-trading-pm market-tick-data-service deployment-service unified-api-contracts features-service market-data-processing-service instruments-service; do git -C $r fetch origin live-defi-rollout -q && git -C $r pull --ff-only origin live-defi-rollout 2>/dev/null; done`

## Mission

The DeFi C0 single-walk migrates 6 legacy DeFi buckets → ONE canonical v9 SSOT, then **deletes the legacy** so
data-status shows true gaps. \*\*The migration TOOL is built, validated, and the entire ecosystem
(readers/writers/UAC/IS

- docs) is already aligned to the locked canonical naming.** YOUR job is the operationally-shipped half: **re-dry →
  apply (write canonical -prd) → RD4 completeness+CF gate → RD5 delete legacy per bucket → then DeFi-lane
  §A/B/D/E/F/G\*\*.

## READ THESE FIRST (do not act from memory)

- **`codex/02-data/defi-canonical-naming-ssot.md`** — the AUTHORITATIVE naming SSOT (data_type/chain/instrument_type/
  path/bucket/columns) + per-surface status + HARD sequencing. **This is the single source; everything aligns to it.**
- **`plans/active/defi_manifest_canonicalisation_2026_06_01.md`** — §C0-RD1…RD5 (the migration spec) + §C0-CN (the
  naming reconciliation, all flipped done) + §A–G (the rest of the DeFi lane). §MASTER coordinates cross-plan.
- **`plans/audit/results/defi_c0_datastate_audit_2026_06_01.md`** — the data-state truth (3 layouts, per-bucket
  structure, schema divergence, manifest grain).
- **`codex/05-infrastructure/gcs-object-operations.md`** — migration perf + completeness/uniform/legacy-deletion
  contract.
- The migration tool: `market_tick_data_service/scripts/migrate_defi_full_v9_canonical.py`.

## What is DONE + SAFE (do not redo)

**Migration tool — complete, canonical, validated** (`mtds@699c58e9`):

- Enumerates ALL 3 source layouts (L1 `{dir}/date=`, L2 `day=/category=`, L3 `raw_tick_data/by_date/`); per-bucket
  cell-keying (path for dex/lending; **row-split** by token/protocol/feed/chain for lst/oracle/perp).
- **Superset-union conform** (operator-chosen lossless) — baked `_CANONICAL_UNION` (53/31/43/20/17/17 cols, the
  exhaustive footer scan) so it SKIPS the ~612s discovery; **loud-fail guard** if any object has a column outside the
  union.
- Dedup (most-rows→freshest layer→latest ts). perp funding-DERIVED from L1 OI. Unattributable rows →
  `_needs_attribution/` (held, never deleted, never guessed).
- **Canonical output** (operator-locked): path
  `{stem}-prd-{pid}/raw_tick_data/by_date/day={D}/pipeline_mode={mode}/ asset_group=defi/venue={V}/chain={C}/instrument_type={IT}/data_type={DT}/{venue}_{chain}_{day}.parquet`;
  data_type **`dex_pool_state`/`dex_pool_swaps`** (collapsed everywhere, NOT dex_pools), `lst_rates`/`lending_indices`/
  `oracle_prices`/`perp_funding`; chain `HYPERLIQUID`; `instrument_type=perpetual` valid for DeFi.
- Perf contract: `--phase discover|migrate|all`, `--buckets`, `--start/--end` date-shard, `--workers`, `--apply` (DRY by
  default), per-phase timing + obj/s, **LOUD error exit (exit 1 + banner if any walk error)**.

**Ecosystem aligned to canonical (all QG green, on LDR)** — so the migrated data is READABLE + live=batch:

- UAC `uac@dad96e42`: `build_defi_partition_path(pipeline_mode=)` canonical; `to_canonical_chain_wire` HL→`HYPERLIQUID`;
  `DEFI_ONCHAIN_INSTRUMENT_TYPES`+=`PERPETUAL`.
- MTDS handlers `mtds@0a3a7071`: `_DATA_TYPE` → `dex_pool_state`/`dex_pool_swaps`; write `pipeline_mode=` partition.
- features-onchain `features-service@dec1b687`: reader pipeline_mode-aware (probe `pipeline_mode=`→bare→legacy);
  `_PATH_DATA_TYPE` identity; bucket-domain rekeyed.
- MDPS `mdps@4b9e6e5`: scanner accepts canonical data_type under `pipeline_mode={batch|live}` + legacy back-compat.
- IS: verified no change (already produces DeFi `perpetual`; UAC owns validation).
- Codex: `defi-canonical-naming-ssot.md` (new) + `defi-data-types-catalog.md` D14 banner (resolved → dex_pool_state).
- Cross-plan banners in `solana_defi_legacy_migration`, `bucket_name_ssot_legacy_dual_write_remediation`,
  `pipeline_mode_partition_migration` (each states what starts/ends).

**NOTHING DELETED. All 6 source buckets intact.** `_index` snapshotted →
`_index/snapshots/pre_migration_2026_06_01.parquet`.

## Measured ETA (full-range dry, mtds@db6d947d, all 6 buckets, one VM)

**148,146 canonical cells total**, 0 errors. dex-pools 58,609 / dex-swaps 28,761 / lending 28,411 / perp 4,682 / lst
18,205 (needs_attr 917) / oracle 9,478 (needs_attr 5,187). One-VM dry = ~35 min. \*\*Sharded apply (6 VMs one-per-bucket

- date-shard dex-pools/lending) ≈ ~12–15 min wall.\*\* <1 hour with margin.

## YOUR remaining work (in order)

1. **DEPLOY the reader fixes first** (HARD — else consumers can't read the new path). The features/mdps reader fixes are
   on LDR but must reach the LIVE features-onchain + MDPS services (next service deploy, or trigger one). Verify the
   live readers are pipeline_mode-aware BEFORE deleting any legacy. (Apply can proceed before this; DELETE cannot.)
2. **Rebuild the tarball** at current HEADs:
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --allow-dirty-tarball` (from `.tabs/2`). Note the new
   `mtds-code@<sha>`, `unified-api-contracts-code@<sha>`, `unified-trading-library-code@<sha>` pins (the build prints
   them) + verify `gsutil ls gs://deployment-scripts-central-element-323112/code/mtds-code@<sha>.tar.gz`.
3. **Re-dry** (canonical data_type sanity, fast — baked union skips discovery):
   `export UAC_TARBALL_SHA=<new> UTL_TARBALL_SHA=<new> MTDS_TARBALL_SHA=<new>` then
   `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh defi 2024-06-01 2024-06-07 dry`. Confirm 0
   errors, data_type=`dex_pool_state`/`dex_pool_swaps`, `pipeline_mode=batch/` in PLAN paths, needs_attr as expected.
4. **Resolve the `_needs_attribution` (oracle 5,187 + lst 917)** BEFORE apply or accept them as held (they block RD4 if
   they represent real cells). oracle = flat pre-Pyth Chainlink rows with no chain → needs a Chainlink feed/`contract`→
   chain registry (build it, align to IS); lst = tokens not in UAC `LST_VENUE_TO_TOKENS` (add them). Honest-hold is OK
   interim; do NOT guess-then-delete.
5. **Pre-migration drain (HARD RULE)** + confirm the `bucket_name_ssot` DeFi manifest seed is NOT mid-walk (its banner:
   seed runs BEFORE C0). Snapshot already taken; re-snapshot if stale.
6. **Apply** (date-shard for <1h, same-region asia-northeast1-c, monitor robustly — single
   `gcloud instances list --filter` call + warmup guard): efficient flow uses the launcher's
   `MIGRATION_EXTRA_ARGS`/`VM_NAME_SUFFIX` (shipped `deployment-service@9dce260`): one `--phase discover` per bucket → N
   `--phase migrate --buckets <one> --start <s> --end <e>` date-shards. Or simplest: 6 VMs `defi <full-range> full`
   one-per-bucket via `--buckets`. **No fire-and-forget** (STARTED<60s, ≥1 progress/hr, STOPPED at exit, T+10min RUNNING
   check). Loud errors → exit 1 → that bucket fails RD4.
7. **RD4 completeness+uniformity+CF gate per bucket**: `-prd` distinct-cell count ≥ union of 3 source layouts; exactly
   ONE schema per data_type; CF-1…12 GREEN via `audit_canonical_form.py` on the rebuilt `-prd` `_index` (re-run the
   consolidator first); 0 errors; needs_attr=0 or operator-acked. **Only then C-GREEN for that bucket.**
8. **RD5 delete legacy per bucket** — ONLY after that bucket's RD4 is GREEN AND the live readers are pipeline_mode-aware
   (step 1). The delete is owned by `bucket_name_ssot` Phase 7 (gated on C-GREEN) — coordinate. One v9 SSOT end-state.
9. **Then the rest of the DeFi lane**: §A writer fixes (A2a/A2b/A4/A5), §B consolidation/data-status (B0 run the
   expected_unattempted chain), §D features backfill, §E cefi-perp hedge, §F docs, §G Solana basis MVP.

## Hard-won lessons / gotchas (honour these)

- **Naming is operator-LOCKED** — `dex_pool_state`/`dex_pool_swaps` (NOT dex_pools), `pipeline_mode=` in path,
  `HYPERLIQUID` chain, DeFi `perpetual` valid. `dex_pool_state` is the **EVM+Solana union** (instrument_type+chain
  discriminate). Do NOT "normalize" to dex_pools or split Solana out — that was the regression the naming audit caught.
- **VERIFY data-state, never a constant.** The baked union came from an EXHAUSTIVE footer scan; the loud-fail guard
  catches drift. If a new column appears → the walk errors loud → re-run `--phase discover` to refresh
  `_CANONICAL_UNION`.
- **Discovery footer-scan is the cost** (eliminated via baked union). **Migrate is fast.** Date-shard the 2 big buckets.
- **needs_attribution is HELD, never lost, never guessed** — review before RD4; resolve via the real registry (IS/UAC).
- **local `gcsfs` DNS is flaky** — heavy GCS work runs on the in-region VM, NOT locally. `gcloud`/`gsutil` work locally.
- **Rebuild the tarball after ANY mtds/uac commit** + verify the `@sha` pin before launch (launcher forwards the SHA
  env-vars so the VM provably runs your code).
- **Monitor robustly**: one `gcloud compute instances list --filter="name~canonical-migration-defi"` call (per-VM
  describe flakes → false GONE); warmup guard (PROVISIONING at poll-1 → false done). VMs auto-shutdown on completion.
- **Cross-plan ordering**: solana_defi Gate-2 and your C0 are MUTUALLY EXCLUSIVE on the DeFi `_index`; bucket_ssot seed
  BEFORE C0, its delete AFTER your RD4-GREEN. Banners in each plan.
- **Git**: LDR (esp. PM) is HOT → rebase-loop on push; stash foreign `*.svg`/`uv.lock` by name before rebase; prek
  auto-restore → `--no-verify`; stage by name (never `git add .`); run QG on touched repos.

## Tarball pins from the last build (rebuild to refresh — these are from mtds@db6d947d, now stale after the canonical commits)

`MTDS_TARBALL_SHA` was `db6d947d…` — REBUILD for `mtds@699c58e9`. `UAC` was `6b98c9d9…` — REBUILD for `uac@dad96e42…`.
`UTL` `009f76e3…` (unchanged unless UTL moved). Always rebuild + re-verify the pin before the apply VM.
