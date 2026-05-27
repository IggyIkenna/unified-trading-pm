---
title: bucket_name_ssot residual drift — 2026-05-20 audit
created: 2026-05-20
priority: P2
status: active
locked_by: live-defi-rollout
blocked_on: bucket_name_ssot_phase2.6
parent_epic: infrastructure_master
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — CAPTURED — residuals tracked in `plans/epics/manifest_master.md` (L2
> probe templates, L3 get_bucket_name consumers, Phase 0d flat→env-tiered, workspace-grep audit); parent plan
> bucket_name_ssot_canonicalisation already archived.
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

# bucket_name_ssot residual drift — 2026-05-20 audit (slot 1, task R-006)

> **Source**: workspace-wide grep audit run 2026-05-20. Commands:
>
> ```
> rg 'gs://\{' --type py -g '!.venv*' -g '!tests' .tabs/1/
> rg '"bucket_template"' --type py -g '!.venv*' -g '!tests' .tabs/1/
> rg 'get_bucket_name\(' --type py -g '!.venv*' -g '!tests' .tabs/1/
> ```
>
> Full table also in `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` § "2026-05-20 grep audit".

## Inline `gs://\{` f-strings — 0 violations

All grep hits are intentional:

- `batch-live-reconciliation-service` (8 hits): all `# noqa: gs-uri`-annotated error messages where bucket is
  pre-resolved.
- `unified-trading-library/dependency_checker.py`: `# noqa: gs-uri` — URI composer, bucket already resolved.
- Remaining hits: infra scripts (setup-buckets.py, verify_infra.py) operating on already-resolved names;
  docstrings/comments.

QG STEP 5.69 v2 AST-walk enforces no new inline URI patterns.

## `"bucket_template"` inline strings — 29 active entries, all BLOCKED

### L2-tail: dependency_checker.py probe templates (BLOCKED-UTL-MIGRATION)

These must migrate to `BaseDependencyChecker` in UTL once that class is built. Cannot migrate before Phase 2.6
flat→env-tiered data migration because the probe template must match the on-disk bucket name.

| Repo                   | File                                                        | Lines      | Templates                                                                                                   |
| ---------------------- | ----------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------- |
| `ml-inference-service` | `ml_inference_service/app/core/dependency_checker.py`       | 32, 37     | `ml-training-store-{category_lower}-{project_id}`, `features-delta-one-store-{category_lower}-{project_id}` |
| `execution-service`    | `execution_service/utils/dependency_checker.py`             | 209–242    | `strategy-store`, `market-data-tick`, `instruments-store`, `features-onchain` (5 entries)                   |
| `features-service`     | `features_service/delta_one/app/core/dependency_checker.py` | 62, 74     | `market-data-tick-{ag}-{pid}` (prod + test)                                                                 |
| `features-service`     | `features_service/onchain/app/core/dependency_checker.py`   | 57–104     | `market-data-tick`, `lending-indices`, `oracle-prices`, `perp-funding`, `lst-rates` (8 entries)             |
| `features-service`     | `features_service/volatility/core/dependency_checker.py`    | (multiple) | `market-data-tick-{ag}-{pid}` (prod + test)                                                                 |

### L5: deployment-service catalog.py templates (BLOCKED-PHASE-2.6)

These are the deployment-service's internal bucket resolution layer. Must flip to `resolve_bucket_name()` during Phase
2.6 reader-repoint (GAP-2.4.D) alongside deployment-api.

| Repo                 | File                            | Lines                                                 | Templates                                                                                                            |
| -------------------- | ------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `deployment-service` | `deployment_service/catalog.py` | 135, 142, 153, 159, 186, 192, 199, 206, 219, 226, 232 | 11 entries: instruments-store, market-data-tick, features-{family}, ml-models-store, strategy-store, execution-store |

## `get_bucket_name()` consumers — 13 service-code + ~10 script-only, all BLOCKED-PHASE-2.6

### Service code (write-path critical)

| Repo                      | File:Line                                                               | Call                                          |
| ------------------------- | ----------------------------------------------------------------------- | --------------------------------------------- |
| `instruments-service`     | `instruments_service/reference_data/utils/evm_creation_resolver.py:174` | `get_bucket_name("instruments", "defi")`      |
| `instruments-service`     | `instruments_service/reference_data/adapters/tradfi/tradfi_live.py:142` | `get_bucket_name("instruments", "tradfi")`    |
| `instruments-service`     | `instruments_service/reference_data/adapters/defi/_solana_utils.py:79`  | `get_bucket_name("instruments", "defi")`      |
| `pnl-attribution-service` | `pnl_attribution_service/engine/pnl_input_builder.py:48`                | `get_bucket_name("gas-fees")`                 |
| `pnl-attribution-service` | `pnl_attribution_service/engine/orchestrator.py:233`                    | `get_bucket_name("execution", "cefi")`        |
| `execution-service`       | `execution_service/instruments/definitions_loader.py:54`                | `gcs.get_bucket_name("instruments")`          |
| `unified-trading-library` | `unified_trading_library/core/seed_writer.py:291`                       | `get_bucket_name(domain)`                     |
| `deployment-service`      | `deployment_service/shard_builder.py:253`                               | `loader.get_bucket_name(domain, ag)`          |
| `deployment-service`      | `deployment_service/cli/utils/manifest_reader.py:160`                   | `get_bucket_name("instruments", "CEFI", ...)` |

### Scripts only (lower-priority; deferred alongside service code)

- `instruments-service/scripts/` — 7 hits (verify_instrument_manifest_coverage.py, rebuild_cefi_manifest.py,
  migrations/\*.py, fix_manifest_venue_casing.py, smoke_matrix.py)
- `unified-trading-pm/scripts/migration/delete-gcs-data-for-dates.py:122,127`

## Follow-up recommendation

Create a single follow-up task **after Phase 2.6 write-pause completes**:

> Title:
> `bucket_name_ssot final delegate flip — replace all get_bucket_name() + dependency_checker.py bucket_template strings with resolve_bucket_name()`
>
> Scope: flip the 13 service-code rows above + script-only rows. Run `inline_bucket_uri_baseline.yaml` QG to assert 0
> remaining. Flip the `- [ ] **[AGENT] P1**` checkbox in `bucket_name_ssot_canonicalisation_2026_05_10.md`. This is the
> gate that closes Done-def #6 of the SSOT plan.
>
> Prereqs: code_freeze Phase 2.6 write-pause window completed; flat→env-tiered data migration done; L3 delegate flip
> (step 2.6.4) landed.
