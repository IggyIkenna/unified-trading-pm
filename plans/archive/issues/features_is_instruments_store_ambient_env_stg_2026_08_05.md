---
doc_type: issue
title: >-
  IS instruments-store catalogue reads leak ambient DEPLOYMENT_ENV_SHORT (stg 404) — onchain fixed, volatility +
  cross_instrument need the sweep
summary: >-
  The IS instruments-store catalogue reads in features-service resolve kind="instruments-store" without forcing
  deployment_env. Under a --env staging VM launch (benchmark/test runs set the IAM-safe tier env) they resolve the
  never-seeded instruments-store-defi-stg-* / -cefi-stg-* tier and 404 — observed live 2026-08-05 on the DEFI:onchain
  benchmark relaunch (0 instruments -> IS_CATALOGUE_EMPTY -> no real compute). Same ambient-env class as the market-data
  input-bucket sweep (features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md), but for the instruments-store
  kind (a separate bucket family). onchain fixed inline (features-service@58702715); volatility + cross_instrument sites
  remain.
status: resolved # (was: open) 2026-08-06 RB-04f4f852 archival: all todos [x], no locked_by
nature: issue
asset_group: [defi, cefi, tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags:
  [
    features-e2e,
    benchmark,
    bucket-resolution,
    staging,
    env-tiered,
    deployment_env,
    instruments-store,
    is-catalogue,
    data-pipeline,
  ]
related:
  - /plans/archive/issues/features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md
created: 2026-08-05
author: slot-9
source:
  [
    "DEFI:onchain benchmark relaunch 2026-08-05 — features-e2e-defi-20260805-223356-060995 run.log; live 404 on
    instruments-store-defi-stg-central-element-323112",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
parent_epic: infrastructure_master
drift_direction: advance-code
resolved_by:
context_scope:
  [
    /codex/05-infrastructure/bucket-isolation-model.md,
    /plans/archive/issues/features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md,
    features-service/features_service/onchain/cli/handlers/batch_handler.py,
    features-service/features_service/volatility/cli/handlers/batch_handler.py,
    features-service/features_service/cross_instrument/engine/cefi_wire_bridge.py,
    unified-trading-library/unified_trading_library/startup_validation.py,
  ]
depends_on: []
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# IS instruments-store catalogue reads leak ambient DEPLOYMENT_ENV_SHORT

## What I found

1. **CONFIRMED + FIXED inline (onchain family, 2026-08-05).**
   `features_service.onchain.cli.handlers.batch_handler. _count_is_defi_instruments` (line 53) and
   `OnchainFeaturesConfig.get_io_input_bucket` resolved `kind="instruments-store"` with the ambient
   `DEPLOYMENT_ENV_SHORT`. A `--env staging`-launched features-e2e VM (benchmark/test runs set the IAM-safe tier env)
   resolved `instruments-store-defi-stg-central-element-323112` — a bucket that does NOT exist (the kind is
   `-prd-`/`-test-` seeded only; the `-stg-` tier is never provisioned) — and 404'd. `_count_is_defi_instruments`
   catches the exception and returns 0 → the onchain compute ran with `IS_CATALOGUE_EMPTY` → 0 instruments → the
   benchmark "completed" (exit_code=0) with ZERO real feature compute. Observed live on
   `features-e2e-defi-20260805-223356-060995` (2026-08-05): "IS DEFI catalogue read failed for 2026-08-02: 404 ...
   instruments-store-defi-stg-central-element-323112", then "IS DEFI catalogue returned 0 instruments —
   IS_CATALOGUE_EMPTY, skipping". This is the SAME ambient-env bug class as the market-data input-bucket sweep
   (`features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md`, features-service@ba385100), but for the
   `instruments-store` kind — a separate bucket family the -001 sweep did not cover. **Fixed inline (features-service
   @58702715)**: both sites now force `deployment_env="prod"` (read-only upstream reference resolution — `-prd-` is
   always correct), with regression tests pinning the kwargs. Verified the real prd catalogue exists (85
   `instruments.parquet` venue shards under `instruments-store-defi-prd-central-element-323112/.../day=2026-08-02/`).

2. **Same class, NOT yet fixed — sibling instruments-store sites** (resolve `kind="instruments-store"` without forcing
   `deployment_env`; under a `--env staging` launch they resolve the non-existent `-stg-` tier and 404 → 0 instruments):
   - `features_service/volatility/cli/handlers/batch_handler.py:52` —
     `resolve_bucket(kind="instruments-store", asset_group=asset_group.lower())` (TRADFI/CEFI volatility)
   - `features_service/cross_instrument/engine/cefi_wire_bridge.py:133` —
     `resolve_bucket(kind="instruments-store", asset_group="cefi")` (CEFI cross_instrument)
   - `sports/config.py:74` + `sports/data/gcs_paths.py` — same fallback, but the features-e2e driver already overrides
     sports' instruments-store via `--source-bucket` (`_resolve_source_bucket` forces the `-prd-` reference bucket), so
     sports is covered at launcher level; still worth aligning the config fallback for direct non-driver launches.

3. **NEW 2026-08-05 (slot-9, 3rd DEFI:onchain relaunch `features-e2e-defi-20260805-225415-060995`) — the onchain compute
   path leaks ambient env through TWO more resolution functions** (the 3rd launch reached real compute — gate PASSED,
   `IS DEFI catalogue: 6034 instruments` — but 7/13 feature groups 404'd on the -stg- tier):
   - **Raw-tick data reader**: `features_service/onchain/adapters/mtds_canonical_reader.py:203` uses
     `get_bucket_name("market_data", "defi")` (UTL `cloud_constants.get_bucket_name` — NO `deployment_env` override
     exists), which resolves `market-data-tick-defi-stg-*` under a staging launch → 404 on every `raw_tick_data` read
     (rewards / flash_loan_availability / health_factor / liquidation_events groups).
   - **IS availability startup validation**: `unified_trading_library/startup_validation.py` (~line 290) resolves the
     `instruments-store` bucket for the "instruments-service availability check" without forcing prod → 404 on
     `instruments-store-defi-stg-*` (logged at VM start, non-fatal). These are a systemic ambient-env leak under
     `--env staging` benchmark launches, spanning features-service + UTL.

## Why it matters

`data_pipeline_check_mdps_features-056` needs genuine per-family throughput numbers. TRADFI:volatility and
CEFI:cross_instrument benchmark relaunches would silently compute over ZERO instruments under a staging launch (same
IS_CATALOGUE_EMPTY trap the DEFI:onchain relaunch just hit) — a wasted billable VM run that "succeeds" with no real
data. The DEFI:onchain benchmark now unblocked on this axis (fix shipped).

## Recommended decision

1. Sweep the sibling `instruments-store` sites (volatility batch_handler.py, cross_instrument cefi_wire_bridge.py) to
   force `deployment_env="prod"` on the read-only catalogue resolve, mirroring the onchain fix (@58702715) — with
   per-site regression tests pinning `deployment_env="prod"`.
2. Align sports' config fallback (`sports/config.py` + `sports/data/gcs_paths.py`) to force `-prd-` for consistency
   (already covered at driver level, but a direct non-driver launch would hit the same trap).

## Progress Log

### 2026-08-05 (slot-4, data_engineering) — fixed the 3rd-relaunch onchain compute-path ambient-env leaks (todo 2)

Two leaks surfaced on the 3rd DEFI:onchain relaunch (`features-e2e-defi-20260805-225415-060995`): the raw-tick reader
and the startup-validation IS-availability check both resolved buckets with the ambient `DEPLOYMENT_ENV` (no override
existed). Added `deployment_env=` to UTL `get_bucket_name` + `get_instruments_bucket` (threads to `resolve_bucket_name`,
WINS over ambient env; backward compatible — default None preserves behavior), then pinned `deployment_env="prod"` at
both sites: `mtds_canonical_reader.read_canonical_defi_parquets` (every `raw_tick_data` read now hits
`market-data-tick-defi-prd-*`) and `startup_validation.validate_upstream_instruments` (`instruments-store-*-prd-*`).
Runtime-verified the override flips `-stg-`→`-prd-` under an ambient `DEPLOYMENT_ENV=stg`; 4 regression tests (2 UTL
resolution-under-stg + 1 startup_validation kwarg-pin + 1 features reader kwarg-pin). Ship: features-service@21119021 +
unified-trading-library@b078d5ba, QG green both repos, SHAs verified on origin/live-defi-rollout. Benchmark re-run for a
clean full-throughput number tracks -056.

### 2026-08-05 (slot-9, data_engineering) — found + fixed inline on onchain during the DEFI:onchain benchmark relaunch (-004)

The -004 DEFI:onchain benchmark relaunch (`features-e2e-defi-20260805-223356-060995`, 2nd launch after the stale-tarball
failure) ran to exit_code=0 but with `IS_CATALOGUE_EMPTY`: the IS DEFI catalogue read 404'd on
`instruments-store-defi-stg-central-element-323112` (ambient DEPLOYMENT_ENV_SHORT=stg under `--env staging`), so
`_count_is_defi_instruments` returned 0 and the compute skipped. Root cause:
`resolve_bucket(kind="instruments-store", asset_group="defi")` without `deployment_env` (same class as the market-data
sweep). Fixed both onchain sites (`batch_handler._count_is_defi_instruments` + `config.get_io_input_bucket`) to pin
`deployment_env="prod"`; 2 regression tests. Ship: features-service@58702715. Evidence:
`features-e2e-defi-20260805-223356-060995` run.log (404 + empty catalogue); `gcloud storage ls` of
`instruments-store-defi-prd-*` (85 shards for 08-02).

## Todos

- [x] ✅ [DATA] P2. Sweep the remaining `instruments-store` catalogue sites in features-service to force
      `deployment_env="prod"` (repo: features-service) — volatility `cli/handlers/batch_handler.py:52` +
      cross_instrument `engine/cefi_wire_bridge.py:133` (sports config fallback for consistency), mirroring
      `_count_is_defi_instruments` @58702715; per-site regression tests pin `deployment_env="prod"` regardless of
      ambient env. QG green + quickmerge — features-service@4b2edbd5
- [x] ✅ [DATA] P2. Fix the onchain compute-path ambient-env leaks found on the 3rd DEFI:onchain relaunch (repo:
      features-service + unified-trading-library) — (a) `onchain/adapters/mtds_canonical_reader.py:203`
      `get_bucket_name("market_data", "defi")` has no `deployment_env` override → resolves `-stg-` under a staging
      launch; switch to `resolve_bucket_name(kind="market-data", asset_group="defi", deployment_env="prod")` (or add the
      override to UTL `get_bucket_name`) so every `raw_tick_data` read (rewards / flash_loan_availability /
      health_factor / liquidation_events) hits the real `-prd-` bucket; (b)
      `unified_trading_library/startup_validation.py` IS-availability check → force `-prd-` instruments-store.
      Regression tests pin prod under ambient staging. QG green + quickmerge both repos. Then re-run the DEFI:onchain
      benchmark for a clean full-throughput number (tracks -056). — features-service@21119021 +
      unified-trading-library@b078d5ba; benchmark re-run for a clean number remains tracked by
      `data_pipeline_check_mdps_features-056`.

- **context-scout 2026-08-06**: populated context_scope (6 entries).
