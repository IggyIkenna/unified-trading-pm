---
title: "Legacy non-canonical tick-bucket dual-write remediation (drain → code-fix → migrate → decommission)"
name: bucket_name_ssot_legacy_dual_write_remediation
created: 2026-06-01
parent_epic: epics/mtds_mdps_master.md
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

- [ ] [SCRIPT] P0. `market-tick-data-service` `orchestrator.py:3832` `get_tick_data_bucket()` → resolve via the
      canonical path: `get_market_data_bucket(asset_group.lower())` /
      `resolve_bucket_name(kind="market-data", asset_group=…)`. Rework the `is_test_run` branch (3829-3830) + `except`
      fallback (3833-3834) to canonical. Add a unit test asserting cefi→`…-cefi-prd-…`, prediction→`…-pred-prd-…` (NOT
      `…-prediction-…`). QG green.
- [ ] [SCRIPT] P0. `market-data-processing-service` `dependency_checker.py:401` flat default →
      `resolve_bucket_name(kind="market-data", asset_group=…)`; `cloud_data_provider.py:41` instruments-store default →
      `resolve_bucket_name(kind="instruments-store", asset_group=…)`. QG green.
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

- [ ] [SCRIPT] P0. `bash scripts/quality-gates.sh` exit 0 for each touched repo (MTDS, MDPS, deployment-service, UTL) +
      cross-repo consumers. Commit + push to `live-defi-rollout`. Flip each Phase 1 checkbox same-turn.
- [ ] [SCRIPT] P0. Rebuild VM code tarball with fixed code:
      `bash deployment-service/scripts/vm/create-code-tarballs.sh`. Verify the new tarball resolves canonical names
      (smoke `get_tick_data_bucket` per asset_group).

## Phase 3 — Drain writer VMs (pre-migration drain gate — HARD RULE) (P0)

- [ ] [SCRIPT] P0. Inventory all GCP **and** AWS fleet writers via `vm_zombie_watchdog.py`; confirm the legacy-writing
      set: `mdps-backfill-cefi-main-test`, `mdps-backfill-defi`, `mdps-prediction-2025`, `sports-scheduler` + identify
      the tradfi legacy writer (ephemeral/Cloud Run). Add `> 🟢 VM DRAINING` banner to affected active plans.
- [ ] [SCRIPT] P0. Per-prefix graceful SIGTERM → wait for STOPPED event (STARTED-within / progress / STOPPED contract);
      run manifest consolidator; snapshot to `_index/snapshots/pre_migration_2026_06_01.parquet` per bucket. NO
      fire-and-forget.

## Phase 4 — Relaunch clean (P0)

- [ ] [SCRIPT] P0. Relaunch the drained writers from the Phase 2 tarball; T+10min verify each writes ONLY to the
      canonical bucket (`_index` mtime advances on `-prd-`, NOT on the flat legacy name).

## Phase 5 — Migrate legacy → canonical (P0)

- [ ] [SCRIPT] P0. One-shot merge script (per CLAUDE.md GCS object ops — `gcs_copy_object` / `gcs_describe_object`,
      NEVER gsutil per-object): copy every parquet from each legacy bucket into its canonical target; merge `_index`
      availability manifests with dedup on the shard row-key; **preserve `pipeline_mode`** (already backfilled on legacy
      rows). Idempotent, `--dry-run` default, `--verify` count-only.
- [ ] [SCRIPT] P0. Run the merge for cefi, defi, tradfi, sports, prediction (main `_index` + `_index/per_vm/` shards).
      Run-to-completion (not smoke-green): manifest-verified row parity + sample-inspected parquets.

## Phase 6 — Verify (P0)

- [ ] [SCRIPT] P0. Legacy buckets receive **0** new `_index` writes for ≥1h post-relaunch (writers fully canonical).
- [ ] [SCRIPT] P0. Canonical row count ≥ pre-migration (legacy ∪ canonical), zero `pipeline_mode IS NULL`, zero
      shard-key dupes. Per-asset_group A3 manifest-divergence check clean.

## Phase 7 — Decommission legacy buckets (P1)

- [ ] [SCRIPT] P1. After verification + a 48h soak: empty + delete (or lifecycle-tombstone) the legacy flat +
      tier-first + long-form buckets. Remove any lingering references. Record decommission in
      `_index/snapshots/decommission_2026_06_0X.md`.

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
