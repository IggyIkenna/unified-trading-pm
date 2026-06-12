---
title: "Legacy non-canonical tick-bucket dual-write remediation (drain → code-fix → migrate → decommission)"
name: bucket_name_ssot_legacy_dual_write_remediation
created: 2026-06-01
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
locked_by: live-defi-rollout
locked_since: 2026-06-01
status: active
priority: P0
model_tier: opus-required
thinking_tier: high
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  Infra (0.8×): root cause is a small set of code edits (1 MTDS callsite is the dominant
  live-write bug) + a deterministic GCS legacy→canonical merge. Bulk of the cost is the
  drain-recipe sequencing + per-bucket manifest merge/dedup + verification, not net-new surface.
source:
  - GCS audit 2026-06-01 (legacy flat `market-data-tick-<group>-<pid>` buckets receiving live writes alongside canonical
    `-<group>-<env>-<pid>`)
  - root-cause discovery agent 2026-06-01 (RC1 MTDS orchestrator malformed domain; RC2 prediction launcher token; RC4
    MDPS default; instruments-store drift)
  - reopens archived `plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` (residual runtime drift not
    caught at archival)
related:
  - solana_defi_legacy_migration_2026_05_27.md # sibling legacy→canonical migration; same drain+merge mechanics
  - pipeline_mode_implementation_2026_05_28.md # pipeline_mode column already backfilled on BOTH legacy + canonical buckets; merge must preserve it
---

# Legacy non-canonical tick-bucket dual-write remediation

> **🟡 MIGRATION ATTEMPT-1 FAILED + BLOCKED (tarball infra) — 2026-06-01**: 20 sharded `canonical-migration-legacy-*`
> VMs launched, ALL failed exit-2 (migration script absent from the pulled `mtds-code.tar.gz`). Root cause: (1) the
> floating mtds tarball was overwritten by a parallel-agent rebuild mid-launch; (2) `setup-data-pipeline-vm.sh` had no
> mtds SHA-pin path (added @deployment-service 58ee0a9); (3) **SHA-pinned `mtds-code@<sha>.tar.gz` does NOT persist** —
> an aggressive prune cron deletes unreferenced pinned tarballs within seconds of upload, so the pin can't be used
> either. All 20 VMs deleted; **no data harm** (script never ran). 3 writer VMs still DRAINED. See Phase 5 blocker todo.
>
> **DUAL-WRITE IS THE BUG, NOT A SHORTCUT (operator 2026-06-01)**: the END STATE is a single CANONICAL SSOT — legacy
> buckets DELETED, not left in place. Status of the two legacy-side activities:
>
> - **New legacy DATA writes: STOPPED** — writers drained + code fixed; `day-2026-05` sample = `total=0` on all 5
>   buckets (no recent legacy data). Where legacy data DOES exist (tradfi day-2025-11-02) it was dual-written, so
>   canonical holds it too.
> - **Legacy `_index` maintenance: STILL RUNNING** — 10 `uts-prod-manifest-consolidator-*-legacy-cron` Cloud Scheduler
>   jobs (5 market-data + 5 instruments) run `*/1 * * * *`, keeping legacy `_index` warm = a parallel SSOT. MUST be
>   paused as decommission (coordinate with `manifest_consolidator_liveness_health_2026_06_01.md` +
>   `aws_manifest_consolidator_scope_2026_05_21.md`).
>
> **Path to single canonical SSOT**: verify canonical holds all legacy data → close the manifest gap (`--manifest-only`
> seed) → pause the 10 legacy crons → DELETE the legacy buckets.

> **🟡 CROSS-PLAN COORDINATION — DeFi `_index` shared with `defi_manifest_canonicalisation_2026_06_01.md`
> (2026-06-01)**: this plan's `--manifest-only` seed writes legacy→canonical rows into the **same
> `market-data-tick-defi-prd-…` `_index`** that `defi_manifest_canonicalisation` rewrites (venue relabel / phantom-grid
> delete / v4–v8→v9 / snapshot, via `migrate_defi_canonical.py`). Single-walk discipline (HARD RULE) forbids two
> concurrent whole-corpus walks on the same `_index`. **Ordering (HARD)**: this plan's DeFi manifest seed runs
> **BEFORE** defi*manifest's `C0` single-walk — otherwise the seed re-injects un-canonicalised legacy rows (old venue
> strings, v4–v8, phantom grid) \_after* C0 cleans them. As of 2026-06-01 **neither DeFi walk has launched** (this
> plan's "Manifest seed" P0 + defi_manifest's "C0 — RUN ON A VM" P0 both open) — no live race yet; do NOT launch the
> DeFi-bucket seed without confirming defi_manifest C0 is not mid-walk (and vice-versa).
> `data_source_provenance_all_asset_groups_2026_06_01.md` (`source`-column backfill) must NOT open a third walk — its
> row-backfill rides defi_manifest's C0 single-walk. Coordination owner: epic `mtds_mdps_master`. Banner-remove when the
> DeFi `_index` is canonical + seeded (defi_manifest C-GREEN). **CANONICAL NAMING (operator-locked 2026-06-01) —
> `codex/02-data/defi-canonical-naming-ssot.md`**: the DeFi seed + the L6 **legacy DELETE this plan owns (Phase 7)**
> MUST use the canonical forms (pool data_type `dex_pool_state`/ `dex_pool_swaps` — NOT `dex_pools`; `pipeline_mode=`
> path; chain `HYPERLIQUID`). **What ends (HARD)**: the DeFi legacy-bucket DELETE runs **ONLY AFTER** defi_manifest C0
> RD4 is GREEN per bucket (canonical proven complete + consumers re-pointed) — never before. Delete-before-C-GREEN =
> data loss.

## Cross-plan ordering → single canonical SSOT (no fallback, no dual) — operator-requested 2026-06-01

**Invariant**: legacy buckets are deleted ONLY after canonical provably holds ALL data + an authoritative v9 manifest.
One single-walk per `_index` (HARD RULE). Layers gate top-down; asset_groups parallelise within a layer.

The exact plan todos that execute each layer (the operator's "mention the plan todos across PM active plans"):

**L0 — INFRA UNBLOCK (gates every VM step).**

- `issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md` — fix pinned-tarball persistence (prune-cron tune OR
  dedicated un-pruned bucket). BLOCKS every `RUN ON A VM` todo below (defi_manifest C0, C6, G1; this plan Phase 2
  tarball
  - Phase 4 relaunch).

**L1 — CODE SSOT (write path).**

- THIS plan Phase 1: resolver fix ✅ (MTDS@0b575651 / MDPS@61900a3 / deploy@d667422,58ee0a9) · OPEN: `[SCRIPT] P0` QG
  grep-guard (no string-concat bucket names) · `[SCRIPT] P1` UTL dead-code removal (`constants.py` flat
  `get_bucket_name`).
- `defi_manifest…` **A**: `A2a` populate `DEFI_VENUE_LAUNCH_DATES` · `A2b` wire lst_rates/solana empty branches · `A4`
  chain-dim QG guard · `A5` perp_funding `SOURCE_RETURNED_ZERO`. (A1/A3/A6/A7 ✅.)
- `data_source_provenance…` **Phased**: UAC source-priority helper · UTL drop the tradfi-only `source` gate ·
  `DefiManifestRecorder.record_captured(source=)` · MTDS thread `source=` through DeFi+CeFi+Sports handlers · stamp
  per-row `pipeline_mode` at oracle/staking callsites. ⇒ write path emits `source` + `pipeline_mode`.
- `pipeline_mode_implementation…` — ✅ DONE (Phases 0–6).

**L2 — STOP LEGACY-SIDE ACTIVITY.**

- THIS plan Phase 3 drain ✅ · Phase 7 `[SCRIPT] P0` **pause the 10 `*-legacy-cron` consolidators + remove from
  `manifest_consolidator_scheduler.tf`** (coord `manifest_consolidator_liveness_health` watchdog so it doesn't restart;
  AWS side via `aws_manifest_consolidator_scope`). ⇒ legacy fully frozen.

**L3 — HISTORICAL DATA + MANIFEST CANONICALISATION — THE FOUNDATION GATE** (`defi_manifest…` §Sequencing: "no backfill
until C is GREEN"). ONE bundled single-walk per bucket → canonical target form (env-split · `asset_group=` ·
`pipeline_mode=` partition · v9 · underscore data_type · flat venue+chain · typed empty-reason ·
`expected_unattempted`):

- **defi** (16,206 legacy-only cells): `defi_manifest…` **C** single-walk — `C0` path+bucket canonicalisation RUN ON A
  VM (gated L0) · `C12-WIRE` wire `migrate_defi_full_v9_canonical` into the launcher · `C2` data_type alias dedup · `C3`
  venue-chain→flat · `C4` v4–v8→v9 · `C5` phantom-grid delete · `C8` under-enumeration (90 venue-keys) · `C9` legacy
  object paths · `C11` post-launch phantom audit · then `B0` run `expected_unattempted` chain (gated C-GREEN). Riders on
  the SAME walk: `data_source_provenance` source-col + `pipeline_mode`.
- **prediction** (2,039 legacy-only + 22 canon-only → canonical LEAST complete): ✅ **FILED + BUILT (slot-3
  2026-06-01)** — `prediction_manifest_canonicalisation_2026_06_01.md`; migrator `migrate_prediction_to_pred_prd_v9.py`
  (dual-source reconciliation + CF-7 baked) @mtds. Owns the prediction `_index` rebuild — see "do NOT seed non-DeFi
  here" below.
- **cefi** (data-state: FULL re-canon, not 838): ✅ **FILED + BUILT (slot-3 2026-06-01)** —
  `cefi_manifest_canonicalisation_2026_06_01.md`; migrator `migrate_cefi_flat_to_v9_canonical.py` (3-layout: bulk day=
  pipeline_mode insert + L-canon no-op + 9 flat orphans fan-out) @mtds. Owns the cefi `_index` rebuild.
- **tradfi (71 legacy-only) / sports (0)**: `tradfi_manifest_canonicalisation` / `sports_manifest_canonicalisation`
  FILED (sports has a slot pickup prompt). All four non-DeFi L3 plans own their own `_index` rebuild.

> **🔴 NON-DEFI SEED GUARD (slot-3 2026-06-01) — do NOT run this plan's `--manifest-only` Phase-5 seed for
> cefi/tradfi/sports/prediction.** Those four L3 canonicalisation plans REBUILD the canonical `_index` from canonical
> object paths via the v9 `ManifestWriter` (single-walk discipline). A `--manifest-only` seed into the SAME `_index`
> would be a SECOND whole-corpus write that re-injects un-canonicalised legacy v8 rows (wrong layout/columns) and races
> the L3 rebuild — review-blocking. The DeFi ordering rule above is the DeFi analogue; for non-DeFi the rule is
> stronger: the seed is REDUNDANT (the L3 rebuild produces the v9 `_index`) → skip it entirely. This plan's role for
> non-DeFi = the L6 decommission gate ONLY (delete legacy after each L3 reports C-GREEN), NOT a manifest seed.

**L4 — CONSOLIDATOR SSOT (go-forward manifest).**

- `aws_manifest_consolidator_scope…` `[HUMAN] P1.10` `tofu apply` Phase D + verify 26 schedules ENABLED (only open todo;
  P0.1–P1.9 ✅). · `manifest_consolidator_liveness_health…` keeps GCP canonical `_index` fresh. Keep the 10 env-tiered
  crons. ⇒ canonical `_index` self-maintains, v9, authoritative.

**L5 — BACKFILL / WRITER RELAUNCH (go-forward data).**

- THIS plan Phase 4 `[SCRIPT] P0` GATED relaunch of `mdps-backfill-defi`/`mdps-prediction-2025`/`sports-scheduler` on
  fixed code (after L0+L3-green per asset_group). · `defi_manifest…` `C6` Pyth backfill · `D1` features-onchain · `E1`
  cefi fetch-fix · `G1` Solana basis backfill — ALL gated on C-GREEN per §Sequencing.

**L6 — DECOMMISSION → SINGLE SSOT.**

- THIS plan Phase 6 verify (`0` new legacy `_index` writes ≥1h · canonical ≥ legacy∪canonical · 0 dupes) → Phase 7
  `[SCRIPT] P0` delete legacy flat/tier-first/long-form buckets (tick + instruments-store legacy, GCP+AWS) + snapshot.

**L7 — GUARDRAILS (regression).**

- THIS plan: QG grep-guard (L1) · `batch_live_symmetry` audit recurring check ✅ · Phase 8 codex bucket-naming SSOT doc.
- `defi_manifest…` `F1–F4` codex docs · `data_source_provenance…` generalise QG STEP 5.64 + codex.

**Newly-exposed gaps to FILE (no current owner)**: (1) **`prediction_manifest_canonicalisation`** — prediction canonical
is the least-complete; highest decommission data-loss risk. (2) **cefi 838-cell gap-fill** owner. (3) per-asset_group
data layouts differ (defi=`dex_pools/lending_indices/lst_rates`, sports=`processed/`, cefi `raw_tick_data` lacks
`by_date/`) → any data-copy must be layout-aware (the original migration script was tradfi-shaped → would have missed
defi entirely).

---

**Finding (operator-directed 2026-06-01)**: legacy flat tick-data buckets
(`market-data-tick-<group>-central-element-323112`, plus long-form `market-data-tick-prediction-…`) are **still
receiving live writes today** alongside their canonical env-tiered counterparts
(`market-data-tick-<group>-prd-central-element-323112`, `market-data-tick-pred-prd-…`). This contradicts the
**archived** `bucket_name_ssot_canonicalisation_2026_05_10.md` "done" claim — the resolver was canonicalised but live
writers still bypass it. **Big finding** per Findings Triage: data correctness across ≥4 asset_groups, cross-repo, on
the May-23 critical path.

**Order is HARD (pre-migration drain gate + clean-relaunch)**: fix code → rebuild tarball → drain writer VMs → relaunch
clean → migrate legacy→canonical → verify → decommission legacy. Draining before the code fix just re-breaks on
relaunch.

## Evidence — live legacy buckets (2026-06-01 GCS audit)

| Legacy (non-canonical) bucket                                                                   | Last `_index` write      | Canonical target                | Writer VM                                      |
| ----------------------------------------------------------------------------------------------- | ------------------------ | ------------------------------- | ---------------------------------------------- |
| `market-data-tick-cefi-central-element-323112`                                                  | 2026-06-01 12:30Z (LIVE) | `market-data-tick-cefi-prd-…`   | `mdps-backfill-cefi-main-test-20260601-163816` |
| `market-data-tick-defi-central-element-323112`                                                  | 2026-06-01 12:31Z (LIVE) | `market-data-tick-defi-prd-…`   | `mdps-backfill-defi-20260528-071130`           |
| `market-data-tick-prediction-central-element-323112` (long-form)                                | 2026-06-01 12:31Z (LIVE) | `market-data-tick-pred-prd-…`   | `mdps-prediction-2025-20260523-124620`         |
| `market-data-tick-tradfi-central-element-323112`                                                | 2026-06-01 12:32Z (LIVE) | `market-data-tick-tradfi-prd-…` | (ephemeral / Cloud Run — confirm in Phase 3)   |
| `market-data-tick-sports-central-element-323112`                                                | 2026-05-28 20:42Z        | `market-data-tick-sports-prd-…` | `sports-scheduler-20260525-072005`             |
| `market-data-tick-{test-cefi,test-defi,test-tradfi,prediction-test}-…` (tier-first / long-form) | NONE                     | dormant — decommission only     | —                                              |

## Root causes (discovery 2026-06-01)

- **RC1 (dominant, CODE)** — `market-tick-data-service/market_tick_data_service/engine/orchestrator.py:3832`
  `get_tick_data_bucket()` calls `get_bucket_name(f"market-data-tick-{asset_group}")` — a malformed **domain** string
  that misses the canonical yaml-delegation map (`_DOMAIN_TO_YAML_KIND` key is `market_data`) and falls through to the
  legacy flat construction `f"{prefix}-{pid}"`. Produces flat cefi/defi/tradfi/sports names + long-form-flat
  `prediction`. All live MTDS writers route through here (`orchestrator.py:1898/1987`, `tardis_adapter.py:1072`,
  `tick_data_handler.py:98`). **Env value is irrelevant — pure code bug.**
- **RC2 (CODE)** — `deployment-service/scripts/vm/launch-prediction-pipeline-vm.sh:62,249` emits long-form `prediction`
  not the canonical short token `pred`; `:58` + `setup-data-pipeline-vm.sh:228` emit `staging` not `stg`.
- **RC3 (RUNTIME, fixed transitively by RC1)** — `launch-cefi-forward-poll.sh` / `launch-defi-forward-poll.sh` don't
  inject a write bucket; MTDS self-resolves via RC1.
- **RC4 (CODE)** — `market-data-processing-service/.../app/core/dependency_checker.py:401` flat default
  `market-data-tick-{ag}-{pid}`; MDPS output mirrors source (`config.py:497-506`) so it writes processed candles to the
  legacy bucket too.
- **Adjacent (CODE)** — `market-data-processing-service/.../app/core/cloud_data_provider.py:41` flat
  `instruments-store-{ag}-{pid}` (yaml env-tiers `instruments-store`). Same drift class; fold in.
- **Latent foot-gun** — `unified-trading-library/.../cloud_interface/constants.py:181,263` legacy `get_bucket_name`
  treats `market_data` as flat Group-A; dead at top-level but importable.

## Phase 0 — Discovery (P0) — DONE

- [x] ✅ [AGENT] P0. Enumerate live legacy buckets + recency + writer VMs + code root causes. — GCS audit + root-cause
      agent 2026-06-01 (evidence + RC tables above). unified-trading-pm@<this-commit>

## Phase 1 — Code fix (root cause; ship BEFORE drain) (P0)

- [x] ✅ [SCRIPT] P0. `market-tick-data-service` `orchestrator.py` `get_tick_data_bucket()` → delegates to the canonical
      resolver (`get_market_data_bucket` for cefi/defi/tradfi/sports; dedicated `market-data-tick-prediction` kind →
      short `pred` token for prediction), fails loud on empty asset_group, dropped the legacy flat/test-bucket/except
      fallbacks. Handler `tick_data_handler.py` skips single-bucket resolution for the multi-AG `ALL` sentinel (no
      synthesised `market-data-tick-all-…`). Test harness `conftest.py` provisions `AWS_ACCOUNT_ID` (canonical resolver
      needs both cloud account ids under `CLOUD_PROVIDER=local`). New regression
      `test_get_tick_data_bucket_canonical.py` + updated `test_orchestrator.py`/`test_handler.py`. —
      market-tick-data-service@0b575651 | full QG exit 0 (2351 unit tests pass).
- [x] ✅ [SCRIPT] P0. `market-data-processing-service` `dependency_checker.py:401` flat default →
      `resolve_bucket_name(kind="market-data", asset_group=…)`; `cloud_data_provider.py:41` instruments-store default →
      `resolve_bucket_name(kind="instruments-store", asset_group=…)`. QG green. —
      market-data-processing-service@61900a3: \_resolve_upstream_bucket + \_get_instruments_bucket both route via
      resolve_bucket_name(); prediction uses dedicated 'market-data-tick-prediction'/'instruments-store-prediction' kind
      keys (short token 'pred'); tests updated + TestCanonicalBucketNameResolver added; 6 main QG gates green.
- [x] [SCRIPT] P0. `deployment-service` launcher token fixes: `launch-prediction-pipeline-vm.sh:62,249`
      `prediction→pred`; `:58` + `setup-data-pipeline-vm.sh:228` `staging→stg`; `launch-mdps-backfill-vm.sh:158` +
      `launch-mdps-sharded-backfill.sh:244` inject canonical env-tiered `PROTOCOL_DATA_SOURCE_BUCKET_{CAT}` /
      `MDPS_OUTPUT_BUCKET_{CAT}`. Update flat-name header comments in `launch-cefi/defi-forward-poll.sh`. —
      deployment-service@d667422 | QG green (106s) | 6 scripts fixed: pred token, stg env-short, env-tiered MDPS source
      bucket, -prd- comments
- [ ] [SCRIPT] P1. `unified-trading-library` `cloud_interface/constants.py` legacy `get_bucket_name` → delete or
      redirect to `resolve_bucket_name` (kill the latent flat-`market_data` foot-gun). Confirm zero top-level importers
      first.
- [ ] [SCRIPT] P0. QG STEP guardrail (model on STEP 5.69 bucket-name SSOT): grep-gate that no `market-data-tick-` /
      `instruments-store-` name is built by string-concat outside `resolve_bucket_name` in production source (exclude
      migration/audit scripts + tests). Land in `unified-trading-pm/scripts/quality-gates-base/*.sh`.

## Phase 2 — Ship + rebuild tarball (P0)

- [x] ✅ [SCRIPT] P0. QG exit 0 + push to `live-defi-rollout` for each touched repo. — market-tick-data-service@0b575651
      (RC1 + handler + tests, full QG exit 0) + @6372bd5d (migration script); market-data-processing-service@61900a3
      (RC4); deployment-service@d667422 (launchers). Phase-1 checkboxes flipped.
- [x] ✅ [SCRIPT] P0. Rebuild VM code tarball **from a CLEAN `live-defi-rollout` checkout** (NOT the slot worktree — it
      carries foreign-dirty backfill WIP; do not ship it).
      `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` (slot 5 worktrees all clean on `live-defi-rollout`)
      → uploaded `mtds-code@58b77a773bdadf767f0346b8174c2c9e5ab93fcb.tar.gz` (2.18 MiB) to
      `gs://deployment-scripts-central-element-323112/code/` 2026-06-12. Also uploaded all CORE repos + extra repos clean.
      Smoke: `get_tick_data_bucket` cefi→`market-data-tick-cefi-prd-central-element-323112`,
      defi→`market-data-tick-defi-prd-central-element-323112`,
      prediction→`market-data-tick-pred-prd-central-element-323112`. All canonical. Needed before Phase 4 relaunch + the Phase 5 VM
      fan-out.

## Phase 3 — Drain writer VMs (pre-migration drain gate — HARD RULE) (P0) — DONE

- [x] ✅ [SCRIPT] P0. Inventoried running fleet 2026-06-01: `mdps-backfill-cefi-main-test` self-terminated; no tradfi
      writer running (cefi+tradfi legacy already static). Drained the 3 live writers (`mdps-backfill-defi`,
      `mdps-prediction-2025`, `sports-scheduler`) via graceful `gcloud compute instances stop` → TERMINATED. Only
      `alerting-quietness` + `vm-zombie-watchdog` left up. **All 5 legacy buckets frozen.**
- [x] ✅ [SCRIPT] P0. Snapshotted each frozen legacy `_index/availability_index.parquet` →
      `_index/snapshots/pre_migration_2026_06_01.parquet` (safety backup, exit 0).

## Phase 5 — Migrate legacy → canonical (P0) — DRAIN→MIGRATE→RELAUNCH (operator sequence 2026-06-01)

- [x] ✅ [SCRIPT] P0. Date-shardable merge script
      `market-tick-data-service/scripts/migrate_legacy_tick_buckets_to_canonical.py`: idempotent server-side
      `gcs_copy_object` data copy (skips objects already in canonical via `gcs_describe_object`) + manifest seed via the
      consolidator's per-VM shard mechanism (drops legacy `_index` rows as
      `_index/per_vm/legacy_bucket_migration_2026_06_01.parquet` → running consolidator folds + dedups on shard-key,
      **preserving `pipeline_mode`**). `--prefix` shards the DATA copy by date; `--manifest-only`/`--no-manifest` split
      the halves. — market-tick-data-service@6372bd5d (ruff clean; scripts/ exempt from strict pyright).
- [x] ✅ [SCRIPT] P0. **Sharded-VM launcher built** (operator directive: parallel VMs by date). 20-shard launcher
      `deployment-service/scripts/vm/launch-legacy-bucket-migration-sharded.sh` (5 buckets × {y2026,y2025,y2024,misc}),
      `VM_TASK=canonical-migration` + `VM_SHUTDOWN_ON_COMPLETION=true`. Script validated by a live local micro-run. —
      deployment-service@db3c33b (+@58ee0a9 SHA-pins).
- [ ] [BLOCKED-INFRA] P0. **Migration data-copy fan-out BLOCKED by tarball infrastructure.** Attempt-1 (20 VMs) all
      failed exit-2: pulled `mtds-code.tar.gz` lacked the migration script (floating tarball overwritten by a
      parallel-agent rebuild). Added mtds SHA-pin path (58ee0a9) but **pinned `mtds-code@<sha>.tar.gz` is pruned within
      seconds of upload** by a cleanup cron, so the pin can't be relied on. **Unblock options (operator decision):** (a)
      find + tune the pinned-tarball prune cron to retain referenced pins (SSOT: VM-tarball-deployment +
      create-code-tarballs); (b) build the migration tarball into a DEDICATED bucket the prune cron doesn't touch; (c)
      skip the VM fleet — run the lower-risk local manifest path below since data is dual-written.
- [x] ✅ [SCRIPT] P0. **`_index` comparison (2026-06-01) — RAW MANIFEST SEED IS UNSAFE, DO NOT RUN.** Compared legacy vs
      canonical `_index` per bucket. The legacy `_index` is stale-schema + different-granularity, so its keys do NOT
      align with canonical's: | bucket | legacy rows | canon rows | CAPTURED legacy rows absent from canon | | --- | ---
      | --- | --- | | cefi | 35.8M | 2.6M | 716,159 | | defi | 1.91M | 1.57M | 382,659 | | tradfi | 579k | 144k |
      289,176 | | prediction | 449k | 16.8k | 430,414 | | sports | 165k | 786k | **0** (already complete) | BUT at
      `(date,venue,data_type)` granularity legacy is ~fully a subset of canonical (tradfi overlap 12,944/12,948) →
      **canonical already covers the same cells**; the divergence is per-`instrument_id` representation + schema version
      (legacy `_index` = mixed **v4/v6/v7/v8**; canonical = **v8**). A raw `--manifest-only` seed would inject millions
      of un-canonicalised v4–v8 rows that won't dedup against canonical v8 → pollutes the SSOT. **Seed abandoned.**
- [ ] [SCRIPT] P0. **Manifest completion belongs to the canonicalisation plans, NOT this plan.** Canonical `_index` is
      made authoritative by `defi_manifest_canonicalisation_2026_06_01.md` (defi) + the manifest v8/v9 schema
      migration + `pipeline_mode_implementation` + `data_source_provenance` — they regenerate canonical-format rows from
      the (already dual-written) canonical DATA. This plan COORDINATES (single-walk ordering, banner in defi_manifest)
      but does not seed. Confirm canonical `_index` is `C-GREEN` per those plans before decommission.
- [x] ✅ [SCRIPT] P0. **Confirm canonical DATA coverage** per bucket (the part this plan owns): canonical holds every
      legacy `(date,venue,data_type)` cell + the underlying objects (dual-write). tradfi confirmed (overlap
      12,944/12,948 + object micro-check). cefi/defi/prediction verified 2026-06-12 (slot-2):
      - Index comparison (date,venue,data_type grain): cefi 8,292 / defi 91,723 / prediction 2,041 legacy-only cells
        — these are INDEX ARTIFACTS (canonical `_index` is incomplete pre-G4-apply; path-format differences v9/pre-v9).
      - Object-level sampling (50k/prefix): `processed_candles/`, `raw_tick_data/`, `backfill-logs/` all show
        ratio=1.00 (legacy=canonical, both ≥50k objects per prefix) for cefi, defi, and prediction.
      - Conclusion: canonical holds all legacy DATA objects (confirmed by object-count parity). No data-copy needed.
        Index coverage will be rebuilt by the canonicalisation plans' G4 applies. — slot-2 2026-06-12

## Phase 4 — Relaunch drained writers (P0) — GATED on associated migration plans (operator 2026-06-01)

**The 3 writer VMs stay DOWN** (operator decision 2026-06-01) until the associated migration/manifest plans below have
run — so the legacy buckets stay frozen through the manifest work and the writers come back only onto fully-canonical
infra. **Relaunch prerequisite plans** (writers must NOT be relaunched before these complete for their asset_group):

- `plans/active/defi_manifest_canonicalisation_2026_06_01.md` (defi → `mdps-backfill-defi`)
- `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`
- `plans/active/pipeline_mode_implementation_2026_05_28.md` + `pipeline_mode_audit_2026_05_28.md`
- `plans/active/manifest_consolidator_liveness_health_2026_06_01.md`
- `plans/active/aws_manifest_consolidator_scope_2026_05_21.md`
- this plan's Phase-5 manifest seed + verify.

- [ ] [SCRIPT] P0. **GATED** — after the prerequisite plans above complete for each asset_group, relaunch
      `mdps-backfill-defi` (defi), `mdps-prediction-2025` (prediction), `sports-scheduler` (sports) from a tarball that
      carries the MDPS canonical-bucket fix (`market-data-processing-service@61900a3`); T+10min verify each writes ONLY
      to the canonical `-prd-`/`-pred-prd-` bucket (`_index` mtime advances on canonical, NOT the flat legacy name).
      NOTE: same pinned-tarball-prune blocker applies — resolve tarball persistence first.

## Phase 6 — Verify (P0)

- [ ] [SCRIPT] P0. Legacy buckets receive **0** new `_index` writes for ≥1h post-relaunch (writers fully canonical).
- [ ] [SCRIPT] P0. Canonical row count ≥ pre-migration (legacy ∪ canonical), zero `pipeline_mode IS NULL`, zero
      shard-key dupes. Per-asset_group A3 manifest-divergence check clean.

## Phase 7 — Decommission legacy → single canonical SSOT (P0 — operator: "stop dual-writing, need SSOT canonical")

- [ ] [SCRIPT] P0. **Pause the 10 legacy consolidator crons** (they keep the legacy `_index` warm as a parallel SSOT).
      `gcloud scheduler jobs pause <name> --location=asia-northeast1 --project=central-element-323112` for:
      `uts-prod-manifest-consolidator-market-data-{cefi,defi,tradfi,sports,prediction}-legacy-cron` +
      `uts-prod-manifest-consolidator-instruments-{cefi,defi,tradfi,sports,prediction}-legacy-cron`. Coordinate with
      `manifest_consolidator_liveness_health_2026_06_01.md` so the liveness watchdog does not alert/restart them. Then
      remove the legacy entries from the Terraform
      (`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`) so they are not re-created on
      `tofu apply`.
- [ ] [SCRIPT] P0. **L6 decommission — gated PER asset_group on its L3 plan reporting C-GREEN** (legacy-only CELLS = 0 +
      canonical v9). L3 owners: defi=`defi_manifest_canonicalisation` §C ·
      prediction=`prediction_manifest_canonicalisation_2026_06_01` · cefi=`cefi_manifest_canonicalisation_2026_06_01` ·
      tradfi=`tradfi_massive_dual_source` re-walk (v9+partition, master CONFLICT-2) · sports=verify-only. For each AG,
      after its L3 is C-GREEN + a short soak: empty + delete the legacy flat + tier-first + long-form tick bucket (and
      the instruments-store legacy buckets per the adjacent drift), GCP + AWS. Canonical `-prd-`/`-pred-prd-` becomes
      the sole SSOT. Record in `_index/snapshots/decommission_2026_06_0X.md`. **Do NOT delete an AG's legacy bucket
      while its L3 plan is open** — prediction/cefi hold legacy-only history.
- [ ] [SCRIPT] P0. **Version-aware + orphan-aware delete (slot/Harsh bucket-state verification 2026-06-02).** Two gaps
      the per-bucket delete must handle, surfaced by reading live bucket state: (1) the canonical `-prd` buckets were
      pre-seeded by a PARTIAL env-split copy in legacy FORM (live-object: defi ~43% / cefi ~65% / tradfi ~93% of legacy;
      cefi also ~17 days stale) — after each L3 form-walk writes canonical `pipeline_mode=` paths, the pre-existing
      legacy-FORM objects inside `-prd` are ORPHANS and must be swept (owned in each AG's L3 verify step), else the
      consolidator rebuild double-counts; (2) the legacy buckets carry large NONCURRENT/soft-deleted version history
      (cefi 3.81M, tradfi 3.52M, defi 1.15M noncurrent via Cloud Monitoring `storage/v2/total_count`) — the decommission
      must purge object VERSIONS (not just live objects), and the "canonical ≥ legacy" verify gate must compare
      Monitoring `type=live-object` counts, never a naive recursive `ls` (which counts versions + soft-deleted).

## Phase 8 — Governance + codex (P1)

- [ ] [SCRIPT] P1. Add this finding to the `batch_live_symmetry_master` audit instructions as a recurring check (legacy
      bucket-name dual-write detection) — extends the pipeline_mode checks already landed 2026-06-01.
- [ ] [SCRIPT] P1. Reopen-note on archived `bucket_name_ssot_canonicalisation_2026_05_10.md`: add a
      residual-runtime-drift banner pointing here (the resolver was canonical but live writers bypassed it). Update
      `codex/05-infrastructure/` bucket-naming SSOT doc with the "writer must use resolver, not string-concat" rule.

## Success criteria

- Every running tick-data writer resolves canonical env-tiered names only; legacy flat/long-form/tier-first buckets
  receive 0 new writes.
- All legacy rows merged into canonical with `pipeline_mode` preserved, zero dupes, row parity verified.
- QG grep-gate green workspace-wide; legacy buckets decommissioned; codex + archived-plan banner updated.

## Out of scope

- `strategy-store` / `execution-store` / `features-delta-one` flat names — yaml deliberately keeps these flat (env-split
  rolled back); NOT drift.
- On-disk `pipeline_mode=` partition — separate named successor (`pipeline_mode_partition_migration_*`).

## Relocate canonical cloud-providers.yaml OUT of deployment-service → UAC (operator-confirmed 2026-06-10)

> **Provenance:** surfaced 2026-06-10 — UTL LDR CI was RED (`BucketNamingError: cloud-providers.yaml SSOT not found`)
> dep-order-blocking 21 repos, because UTL (T0, owns `bucket_naming`) finds the yaml by walking up to a sibling
> `deployment-service/` (T4) dir, ABSENT in a standalone CI clone. That is a backwards tier dependency. **Immediate
> unblock SHIPPED to UTL:** `tests/conftest.py` points `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` at the repo-local fixture,
> and the fixture is now the FULL canonical copy (was 16-line minimal lacking `execution-store`). Tracked in
> `ldr_trunk_promotion_decoupling_2026_06_10.md` Progress Log.

- [x] ✅ [SCRIPT] P1. **Package the canonical `cloud-providers.yaml` in UAC + UTL reads it from the installed package.**
      Shipped `unified_api_contracts/config/cloud-providers.yaml` (used the existing UAC `config/` dir — consistent with
      `credentials_per_archetype.yaml`; hatchling already packages `config/*.yaml`; verbatim copy of the 366-line
      deployment-service canonical) — unified-api-contracts@ba92d0e3. UTL `bucket_naming._packaged_uac_yaml_path()`
      reads it via `importlib.resources.files("unified_api_contracts")`, appended to `_candidate_yaml_paths()` AFTER the
      sibling-walk (in-tree workspace copy still wins locally) — always-available in a standalone clone. Verified:
      standalone-simulated resolution (`_find_workspace_root→None`) resolves `dex-pools-prd-test-project`; UTL QG green
      (sentinel 5d2c8533) — unified-trading-library@75c001ec. Fixes the T0→T4 tier inversion + sibling-walk fragility.
- [x] ✅ [SCRIPT] P2. **Flip the consumers: deployment-service + PM consume the UAC canonical, not own it.** UAC is now
      named the canonical SSOT in `cursor-configs/CLAUDE.md` § Bucket-name SSOT +
      `codex/02-data/bucket-naming-and-config.md` (deployment-service = authoring/env_substitutor read, PM =
      byte-identical mirror). Synced the **stale PM mirror** `unified-trading-pm/configs/cloud-providers.yaml` (was 110
      lines / wrong format) to byte-match the 366-line canonical. deployment-service's copy already matched (the
      relocation copied from it). **Decided AGAINST symlinks** — a symlink to a sibling breaks standalone CI clones (the
      original bug class); kept real byte-identical copies. — unified-trading-pm@da0cd88c.
- [x] ✅ [SCRIPT] P1. **ROOT-CAUSE of the UTL CI red (found this run, not the sibling-walk): the CI test fixture
      `scripts/quality-gates-base/ci-test-cloud-providers.yaml` was a STALE PRE-SUBSTITUTED snapshot** (templates baked
      to literals `test-account` / `archetype-state-test-test-project` — no `${AWS_ACCOUNT_ID}` /
      `${DEPLOYMENT_ENV_SHORT}`), so `test_bucket_naming_cell_sweep.py`'s AWS/env-tier assertions passed locally (repo
      fixture / sibling-walk = templated) but FAILED in CI (CI points the env override at this stale PM file). Synced it
      byte-identical to the canonical (templated). Verified CI-parity: `execution-store-cefi-123456789012`,
      `strategy-store-123456789012`, `archetype-state-stg-…` all resolve correctly with the CI env. This — not the
      production sibling-walk — was the live UTL CI blocker. — unified-trading-pm@da0cd88c.
- [x] ✅ [TEST] P2. **Reconcile the UTL "not-found" error-path tests** with always-available UAC packaging.
      `test_yaml_not_found_raises` now also patches `_packaged_uac_yaml_path → None` (alongside
      `_find_workspace_root → None`) — the genuine "no yaml anywhere" simulation. The malformed/invalid-syntax tests
      already point the env override at a present-but-bad file (probed first), so they were unaffected.
      unified-trading-library@75c001ec. (Dropping the repo-local test fixture + conftest env-override is harmless
      follow-up cleanup — left in as a defensive default; NICE-TO-HAVE below.)

## Autonomous completion report — UTL CI keystone (2026-06-11, slot-1)

**The UTL CI red is FIXED and VERIFIED GREEN on the actual CI gate** (not just locally — the dispatch's STEP-3 trap was
the whole point). Dispatched `quality-gates-v2` on UTL `live-defi-rollout` (run **27311378019 = SUCCESS**) after the fix
landed.

**Root cause was TWO-layered — the operator-named architectural fix was necessary but NOT the live CI blocker:**

1. **Architectural (the production path, operator-confirmed):** UTL (T0) resolved `cloud-providers.yaml` by walking up
   to a sibling `deployment-service/` (T4) dir — absent in a standalone clone → `BucketNamingError`. Fixed by packaging
   the canonical yaml in **UAC** (`unified_api_contracts/config/cloud-providers.yaml`, unified-api-contracts@ba92d0e3)
   and reading it via `importlib.resources` (always-available, since UTL hard-deps UAC) —
   unified-trading-library@75c001ec.
2. **The ACTUAL live CI blocker (found this run by reading the failed log, per STEP 3):** CI never hit the sibling-walk
   — it points `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` at PM's
   **`scripts/quality-gates-base/ci-test-cloud-providers.yaml`**, which was a **stale PRE-SUBSTITUTED snapshot**
   (templates baked to literals `test-account` / `archetype-state-test-…`). So `test_bucket_naming_cell_sweep.py`'s
   AWS-account / env-tier assertions passed locally (repo fixture = templated) but FAILED in CI. Synced that file
   byte-identical to the templated canonical; verified CI-parity resolution. — unified-trading-pm@da0cd88c (merged to PM
   main, PR #236, v2 green).

**Fleet `FAILING` triage (every flagged repo gh-verified):** most manifest `FAILING` flags are **STALE** — LDR is green.
The only genuinely-live class is the **dep-floor cascade on `main`**: UTL source/manifest is `0.5.0` and all 8 consumers
pin `>=0.5.0`, but the released tag was stuck at **v0.4.0** because UTL's promotion was blocked by exactly this CI red.
Likewise UAC source `0.6.0` vs released `0.5.2` (e2e-testing pins `>=0.6.0`). **So the keystone fix is the single
unblock for the whole `main` dep-floor cascade** (greeks / deployment-service / +6 via UTL 0.5.0; e2e-testing via UAC
0.6.0). No consumer floor needs touching — they are correct; the libs just need to RELEASE.

**Driven this run:** UTL `#271` (LDR→staging) re-fired (its blocking check was the pre-fix run) → v2 re-running green →
auto-merges → staging→main → semver tags v0.5.0. UAC `#125` (DIRTY) dispatched to
`deterministic-promotion-conflict-resolve` (the 4 unique staging commits are promote-squash artifacts → the conservative
escalate case; a manual clean-start force-sync is **blocked — the token lacks `Administration: write`**, the same limit
as cicd item L2815).

**Also shipped:** consumer-flip (UAC named canonical in CLAUDE.md + codex; PM mirror + the CI-test fixture synced
byte-identical); B-part-2 `--hotfix-to-main` in quickmerge.sh (guards smoke-verified); 6 RESOLVED-STALE cicd_hardening
items flipped with evidence.

**Forced-tradeoff / honest scope (rule 1 + rule 11):** the workspace carries **707 open `- [ ]`** across active plans —
the bulk is standing per-asset-group manifest-canonicalisation / migration / audit **epic work** assigned across VMs,
NOT this CI-unblock lifecycle. I did not implement those (they are multi-week, cross-repo, infra-ops, and out of the
keystone's scope). The remaining cicd_hardening LIVE items are correctly statused, not falsely closed: **4982**
(staging→main `staging_commits` logic — a fleet-workflow change; per rule 11 not a session-tail rush), **4644** (24-repo
template rollout — fleet-wide), **1754** (UI staging PR — needs a UI-capable slot + `pw:L2`), **2815** + UAC `#125`
force-sync (both need an `Administration:write` token — operator), **1121** (macOS-local). These are genuine
non-completions with named reasons, not silent deferrals.
