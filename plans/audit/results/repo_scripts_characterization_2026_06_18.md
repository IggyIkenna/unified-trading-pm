---
title: Repo scripts/ characterization — fleet-wide audit (Phase 1)
name: repo_scripts_characterization_2026_06_18
type: audit-result
epic: infrastructure_master
parent_plan: plans/active/repo_scripts_governance_audit_2026_06_18.md
created: 2026-06-18
author: harshkantariya [autonomous scripts audit]
assigned_vm: vm-cross-cutting
method:
  6 read-only Opus sub-agents, one per repo-cluster; per-script skim (docstring + key imports + filename) + git
  last-modified date + red-flag grep
---

# Repo scripts/ characterization — fleet audit (Phase 1)

> **Read-only characterization** of every SERVICE repo's `scripts/` (excludes `unified-trading-pm` — the tooling host).
> Each script classified: `KEEP-PERMANENT` (standing tooling) · `KEEP-ONEOFF` (live, active-campaign) · `DELETE`
> (ran-once-DONE) · `DEPRECATE` (out-of-shape, fix-in-place) · `PROMOTE-TO-CLI`. **No deletions this pass** — the delete
> EXECUTION is a reviewed follow-up (Phase 1 second todo of the parent plan), and it is **campaign-gated** (see Finding
> 1).

## Fleet tally (~820 scripts, `.py` + `.sh`, 21 service repos)

| Disposition                       | ~count | Notes                                                                                                                                                                                                                                                                                                          |
| --------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **KEEP-PERMANENT**                | ~620   | The vast majority — per-family dev quintet (`quality-gates.sh`/`setup.sh`/`setup-workspace.sh`/`seed_mock_data.py`/`smoke_matrix.py`), deployment-service's ~230 VM launchers + lifecycle + recovery + provisioning, e2e-testing's ~78 verification harnesses, UAC/UTL codegen+QG checkers. **Not throwaway.** |
| **KEEP-ONEOFF** (active campaign) | ~65    | Live in-flight migration/tracer scripts whose parent plan is still in `plans/active/` — **must NOT be deleted** (esp. the `*_2026_06_01.py` canonicalisation set + the May-23 DeFi tracers).                                                                                                                   |
| **DELETE** (ran-once-DONE)        | ~127   | Dated 2026-03/04/05 migrations/backfills/reconciles/purges/flips. **HEAVILY campaign-gated** — see Finding 1. Only ~40 are immediately safe.                                                                                                                                                                   |
| **DEPRECATE** (out-of-shape)      | ~75    | The systemic `google.cloud`-direct / hardcoded-`central-element-323112` / inline-`gs://` pattern — fix in place (Finding 2).                                                                                                                                                                                   |
| **PROMOTE-TO-CLI**                | ~8     | Recurring production logic living as a loose script (Finding 3).                                                                                                                                                                                                                                               |

> Counts are summed from the 6 per-repo agent tallies (approximate at the margins). `.sh` is included — that's why the
> total (~820) far exceeds the earlier `.py`-only inventory (~647 incl. PM). deployment-service alone is ~270 (≈217
> `.sh` VM launchers, legitimately permanent).

---

## Finding 1 (🔴 the gating rule) — DO NOT mass-delete mid-campaign

The big DELETE cohort (instruments-service **64**, MTDS **22**) reads as dead — old dated migrations — **but the 2026-06
manifest-canonicalisation campaign is ACTIVE** (its plans are still in `plans/active/`:
`master_data_canonicalisation_migration_catalogue_2026_06_07`, `*_manifest_canonicalisation_2026_06_01` per-AG,
`defi_venue_name_canonicalisation_and_reth_2026_06_17`, `solana_defi_legacy_migration_2026_05_27`,
`migration_verification_orphan_safety_2026_06_10`). Two consequences flagged by both data-repo agents:

1. **The `*_2026_06_01.py` scripts are IN-FLIGHT campaign deliverables → `KEEP-ONEOFF`, not delete** (e.g. MTDS's 8
   `defi_*_2026_06_01.py`, `migrate_legacy_solana_defi_to_canonical.py`, `gate3_solana_manifest_reconcile.py`).
2. **Some "done-looking" 2026-05 reconcilers may be re-run if the campaign re-touches their asset_group.**

**Gating rule for the delete-execution phase:** delete a repo's dated one-offs for an asset_group **only after that AG's
`*_manifest_canonicalisation_2026_06_01.md` plan is archived**, and only after the Script-Homes check (GCS orphan-sweep
= 0 for that script's targets). **No fleet-wide `git rm` sweep.** This is exactly why Phase 1 is read-only first.

---

## Finding 2 (🟠 systemic, validates the ruff decision + extends it) — the `scripts/` cloud-discipline rot

**~75 scripts** carry one or more of: `from google.cloud import storage` (instead of UCI `get_storage_client()`);
hardcoded `PROJECT_ID = "central-element-323112"` (instead of `GCP_PROJECT_ID` via `UnifiedCloudConfig`); inline
`gs://…` f-strings (instead of `resolve_bucket_name()`); a couple of `import boto3` direct +
`os.environ.setdefault("GOOGLE_CLOUD_PROJECT")` (banned env name). Because `scripts/` is outside the main QG gate,
**this is invisible rot** — precisely the gap the operator's "are scripts checked?" question surfaced.

- **Worst concentrations:** instruments-service (~58, mostly inside DELETE-cohort scripts → moot on deletion),
  strategy-service DeFi tracers (8 — `run_2yr_config_grid_backtest`, `capture_phase_9_evidence`, `phase_d_gate`,
  `trace_*`), MTDS (~16), e2e-testing (~9 Python harnesses), execution-service (4), client-reporting-api (2), MDPS (3).
- **Disposition:** for DELETE-cohort scripts it's moot (removal moots the flaw). For **KEEP/PROMOTE** scripts that carry
  it (the strategy tracers, `seed_demo_client`, `run_client_reporting_cutover`, `run_amm/lending_validation`,
  `backfill_vix_yahoo`, `run_weekly_pipeline`) it's a **fix-in-place** remediation.
- **Recommendation (feeds Phase 2):** ruff-lint alone won't catch `google.cloud`-vs-UCI (that's a TID251/import-surface
  concern, not a ruff style rule). So Phase 2 should **(a)** add the cheap ruff pass, AND **(b)** extend the existing
  cloud-SDK-direct (TID251) + `os.getenv`/`GOOGLE_CLOUD_PROJECT` ratchets to cover `scripts/` (baselined,
  counts-only-down), so this rot can't silently grow. Do this AFTER the DELETE pass so the baseline isn't inflated by
  soon-deleted scripts.

---

## Finding 3 — PROMOTE-TO-CLI (recurring prod logic living as a script — Script-Homes rule 1)

| Script                                   | Repo                 | Why                                                                                             |
| ---------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------- |
| `daily_update.py`                        | client-reporting-api | **clearest** — "hourly incremental update", recurring production runtime                        |
| `collect_lst_seasonal_rewards_daily.py`  | features-service     | self-says "scheduler invokes once per day"                                                      |
| `measure_honest_coverage.py`             | instruments-service  | the canonical coverage formula (`captured/(captured+failed+expected_unattempted)`), 2 plan refs |
| `verify_instrument_manifest_coverage.py` | instruments-service  | recurring coverage-verification logic                                                           |
| `run_weekly_pipeline.py`                 | e2e-testing          | recurring sports L0+L1 batch orchestration                                                      |
| `backfill_vix_yahoo.py`                  | e2e-testing          | VIX 15m is standing coverage (CLAUDE.md)                                                        |
| `check_pipeline_completeness.py`         | features-service     | recurring cross-service completeness check                                                      |

These should become `<service> CLI --operation <verb>` subcommands (gated as part of `$SOURCE_DIR`), not loose scripts.

---

## High-value cheap fixes — DEAD checkers / stale-reference tooling (fix or delete now, low risk)

These are _tooling_ scripts pointed at deleted/renamed/archived paths — they silently no-op:

- `unified-api-contracts/scripts/check_schema_organization.py` — globs the **DELETED `unified_api_contracts/schemas/`**
  dir → collects 0 schemas every run. Dead no-op. (Not wired into QG, so silent.)
- `unified-trading-library/scripts/check-ruff-versions.sh` — greps `.github/workflows/quality-gates.yml` — the **retired
  v1 workflow** (gone since 2026-05-29). Checks a path that no longer exists.
- `system-integration-tests/scripts/check-sit-readiness.py` — reads `../unified-trading-codex/10-audit/repos/` — the
  **archived `unified-trading-codex` repo** (folded into PM `codex/`). Silently finds no checklists.
- `market-tick-data-service/scripts/quality-gates.sh:175` — SSOT-points to a non-existent
  `_migrate_tradfi_hyphen_rewriter.py` (closest real file: `migrate_tradfi_to_hive.py`). QG message misdirects
  operators.
- `deployment-service/scripts/aggregate_instruments.py` — self-banners `DEPRECATED` + references the archived codex
  path; superseded by the instruments-service CLI → DELETE.

---

## Immediately-safe DELETE cohort (NOT campaign-gated — old run-once, no active plan)

The ~40 that can be swept now (still verify GCS-orphan=0 per Script-Homes before `git rm`):

- **unified-trading-system-ui (7)** — the cleanest cohort: all 2026-03 run-once `.tsx.bak` splitters + codemods
  (`build-deployment-details-views.py`, `generate-deployment-split.py`, `split-deploy-form.py`,
  `split-deployment-components.py`, `codemods/migrate_page_headers.py`, `codemods/replace-loader2-spinner.py`,
  `dedupe-openapi-operation-ids.py` — _verify the last isn't in the OpenAPI typegen pipeline first_).
- **deployment-service (≤14)** — done bucket-migration `.sh` (`migrate-flat-to-env-tiered.sh`,
  `archive-flat-buckets.sh`, `aws/migrate-bucket-names-*`, `aws/migrate-defi-buckets-prod-to-prd.sh`,
  `vm/relaunch_staged_2026_05_29.sh`) + done `.py` (`migrate_sports_league_sharding.py`, `rebuild_sports_manifest.py`
  [hardcodes v8], `validate_league_migration.py`, `aws/phase5a_aws_object_migrate.py`,
  `sports/{apply_csv_corrections,pipeline_test}.py`, `validate_test_sample.py`, `aggregate_instruments.py`). _(The
  `phaseN-_-vm-fleet.sh` + 4 migration-VM launchers are borderline — operator call.)\*
- **UAC (2)** — `add_api_version_constants.py` (2026-03, constants long-added), `test_mock_loading.py` (2026-03 demo).
- **strategy-service (2)** — `dump_legacy_mapping_to_yaml.py`, `dev/strategy_parity_diff.py` (consolidation shipped).
- **features-service (~5)** — `backfill_funding_30day.sh` + `backfill_lst_yields_30day.sh` (dated window),
  `dump_registry_to_yaml.py`, `sports/migrate_gcs_entity_filenames.sh` (self-banners DEPRECATED + subprocess gsutil),
  `sports/launch_parallel_backfill.sh` (dead tombstone stub).
- **MDPS (3)** — the dated `reconcile_mdps_available_at_*` pair + `reconcile_1440_nan_placeholders.py` (verify
  campaign).
- **UTL (1)** — `migrate_manifest_v8.py` (superseded by the v9 walk).
- **deployment-api (1)** — `cleanup_ghost_venue_manifest_rows.py` (self-described one-shot).
- **agent-orchestrator (1)** — `gen_backlog_2026_05_20.py` — **untracked** working-tree file (not in git), superseded by
  `regen_backlog_from_plan.py`. (Untracked → confirm it's nobody's live WIP before removing.)
- **e2e-testing (~5)** — `common/teardown.sh` (pre-env-short era), the 2026-04 sports oddspapi/api-football rerun
  campaign scripts. _(The `v3` vs non-`v3` launcher pairs need owner confirmation of which is canonical.)_

---

## Per-repo summary (counts: KP / KO / DEL / DEP / CLI)

| Repo                              | total | KP  | KO  | DEL | DEP | CLI | note                                            |
| --------------------------------- | ----- | --- | --- | --- | --- | --- | ----------------------------------------------- |
| instruments-service               | 117   | 17  | 16  | 64  | 18  | 2   | biggest DELETE cohort — **campaign-gated**      |
| market-tick-data-service          | 69    | 13  | 18  | 22  | 16  | 0   | 2026-06-01 defi set is IN-FLIGHT (KEEP)         |
| deployment-service                | 270   | 230 | 0   | 14  | 1   | 0   | ~217 `.sh` launchers = legit permanent          |
| e2e-testing                       | 107   | 78  | 5   | 5   | 16  | 3   | permanent harness bulk (defi/strategy)          |
| features-service                  | 62    | 50  | 0   | 5–6 | 5   | 2   | per-family quintet bulk                         |
| unified-api-contracts             | 33    | 27  | 0   | 2   | 4   | 0   | T1 lib — codegen/QG checkers; 1 dead checker    |
| strategy-service                  | 28    | 13  | 5   | 2   | 8   | 0   | DeFi tracers carry the bucket-discipline gap    |
| execution-service                 | 12    | 4   | 6   | 0   | 2   | 0   | validation runbooks (fix google.cloud)          |
| unified-trading-system-ui         | 17    | 7   | 1   | 7   | 1   | 0   | cleanest pure-DELETE cohort (2026-03 splitters) |
| client-reporting-api              | 9     | 4   | 3   | 0   | 2   | 0   | `daily_update.py` → PROMOTE-TO-CLI              |
| market-data-processing-service    | 10    | 4   | 2   | 3   | 1   | 0   | dated available_at reconcilers                  |
| agent-orchestrator                | 24    | 19  | 3   | 1   | 1   | 0   | self-provisions its fleet (permanent infra)     |
| unified-trading-library           | 9     | 5   | 2   | 1   | 1   | 0   | v8-migrate dead; ruff-version checker stale     |
| ml-service                        | 12    | 10  | 2   | 0   | 0   | 0   | clean (per-family boilerplate)                  |
| unified-trading-api               | 5     | 4   | 1   | 0   | 0   | 0   | clean                                           |
| system-integration-tests          | 7     | 4   | 1   | 0   | 1   | 0   | check-sit-readiness reads archived codex        |
| ibkr-gateway-infra                | 11    | 11  | 0   | 0   | 0   | 0   | **clean — 0 red flags**                         |
| deployment-api                    | 5     | 3   | 0   | 1   | 0   | 0   | ghost-venue one-shot                            |
| alerting-service                  | 5     | 4   | 1   | 0   | 0   | 0   | clean                                           |
| trading-agent-service             | 4     | 4   | 0   | 0   | 0   | 0   | clean boilerplate                               |
| batch-live-reconciliation-service | 4     | 4   | 0   | 0   | 0   | 0   | clean boilerplate                               |

---

## Recommended next steps (feed the parent plan)

1. **Phase 0 (marker convention)** — codify `Epic:`/`Lifecycle:`/`Delete-when:` (already designed in the parent plan).
   The characterization above already assigns each script a lifecycle, so stamping is mechanical.
2. **DELETE execution (Phase 1 second todo) — GATED + REVIEWED:** start with the **immediately-safe ~40** (UI splitters,
   done deployment-service bucket migrations, the dead checkers). The campaign-gated cohort (instruments-service 64 /
   MTDS 22) deletes per-AG only after that AG's canonicalisation plan archives + GCS-orphan-sweep=0. **No fleet-wide
   `git rm`.**
3. **DEPRECATE remediation:** fix the ~10 KEEP/PROMOTE scripts that carry the cloud-discipline gap (UCI +
   `resolve_bucket_name`
   - `GCP_PROJECT_ID`); the rest are moot on deletion.
4. **PROMOTE-TO-CLI:** file the ~8 as their owning service's CLI subcommand (separate small plan items per repo).
5. **Phase 2 ruff + ratchet extension:** ruff-lint `scripts/` AND extend TID251/`os.getenv`/`GOOGLE_CLOUD_PROJECT`
   ratchets to `scripts/` — AFTER the DELETE pass so the baseline isn't inflated.
