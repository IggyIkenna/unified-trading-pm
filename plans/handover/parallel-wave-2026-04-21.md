# Parallel sports / manifest program — handover (coordinator SSOT)

Generated during orchestration. **Plan file paths:** `unified-trading-pm/plans/active/*_2026_04_21.plan.md`. **Codex:**
`unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` §12.

## Phase 0 — preflight quality gates + baseline (2026-04-21)

| Repo                        | `bash scripts/quality-gates.sh` | Notes                                                                                                                                                                                                        |
| --------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `features-sports-service`   | PASS                            |                                                                                                                                                                                                              |
| `deployment-api`            | Not clean                       | MTDS tests updated locally; full QG also hits codex / bucket-template limits unrelated to this handover.                                                                                                     |
| `deployment-service`        | Not clean                       | Codex: hardcoded project id, schema provenance, deep UAC imports (see prior QG log).                                                                                                                         |
| `deployment-ui`             | Not clean                       | ESLint: `DataStatusDrilldown.tsx` refactored (`InstrumentsModal` / `InstrumentsModalStandard`) so hooks are valid; run full QG in repo (many unit tests failed in this workspace snapshot — verify locally). |
| `instruments-service`       | Not clean                       | Coverage 77.81% vs fail-under 78% at last run.                                                                                                                                                               |
| `unified-trading-library`   | Not clean                       | Production-readiness validators / workspace-manifest (run `python3 unified-trading-pm/scripts/run_validators.py --scope all` from workspace root).                                                           |
| `unified-trading-system-ui` | Not clean                       | Site-header test aligned to `CALENDLY_URL`; coverage floor failed (<70%) in this environment — confirm `MIN_UI_COVERAGE` / run locally.                                                                      |
| `unified-trading-pm`        | Not clean                       | Codex: deep imports / empty-fallback rules on `scripts/propagation/generate-strategy-instances-fixture.py` (import path adjusted toward shallower `strategy_service` import).                                |

**Coordinator action:** Re-run Phase 0 per repo after syncing venvs; use `bash scripts/quickmerge.sh` per repo once each
repo is independently green and `git status` is clean.

## Wave 1 — same-repo overlap (before parallel Task dispatch)

| Repo                                                             | Wave-1 plans touching it                                                                                                                                               |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `deployment-service`                                             | `apifootball_enrichment_historical_backfill`, `non_apifootball_provider_backfill_launchers`, `sports_scheduler_cron_activation`, `features_sports_pipeline_deployment` |
| `instruments-service`                                            | `utl_manifest_migration_primitives`, `instruments_service_orchestrator_reliability_fixes`                                                                              |
| `unified-trading-library`                                        | `utl_manifest_migration_primitives`                                                                                                                                    |
| `deployment-api` / `deployment-ui` / `unified-trading-system-ui` | `upcoming_fixtures_ui_view`                                                                                                                                            |
| `unified-trading-pm`                                             | `vm_observability_codex_update`                                                                                                                                        |

**Parallelism rule:** Do not run two agents that edit the same _file_ concurrently. Batching suggestion: **batch A** —
data VM/deploy (`deployment-service` single owner or sequential PRs); **batch B** — `instruments-service` +
`unified-trading-library` (tight coupling on UTL manifest work — often sequential: UTL first, then instruments).

## Wave 1 — sub-agent results (merged 2026-04-21)

Eight parallel sub-agents ran with the §12.7 bundle. Summaries below; confirm SHAs on each repo’s branch before treating
work as landed.

| workstream_id                                        | status  | headline                                                                                                                    |
| ---------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------- |
| `utl_manifest_migration_primitives`                  | blocked | UTL + instruments changes reported; UTL prod-readiness validators + instruments coverage below 78%.                         |
| `apifootball_enrichment_historical_backfill`         | blocked | Phase 0 plan doc updates; VM blocked on upstream QG / §12.8 preflight.                                                      |
| `non_apifootball_provider_backfill_launchers`        | partial | Four launchers + commit `9b24eed` on `live-defi-rollout` reported; deployment-service codex + quickmerge preflight blocked. |
| `instruments_service_orchestrator_reliability_fixes` | partial | Bugs 1–3 and 6–7 work reported; coverage still below threshold; UAC/instruments merges not verified here.                   |
| `sports_scheduler_cron_activation`                   | partial | Commits `c8e70f6` + PM `95d1153e` reported; GCP deploy phases + codex debt remain.                                          |
| `features_sports_pipeline_deployment`                | partial | Service/API changes reported; Cloud Run + backfill + green QG not completed.                                                |
| `upcoming_fixtures_ui_view`                          | partial | API/UI work reported; full-repo QG not green; some phases skipped per agent.                                                |
| `vm_observability_codex_update`                      | partial | Docs + commit `9155112` on `live-defi-rollout` reported; PM QG blocked on script codex.                                     |

## Gate — P9 (`sports_manifest_shard_migration_cleanup`)

Requires **`utl_manifest_migration_primitives`** = `done` and **instruments bugs 6–7** merged with green QG.

**Check (2026-04-21): gate not met** — `utl_manifest_migration_primitives` is **blocked**; instruments stream is
**partial** with coverage/merge caveats. **Skip P9** until coordinator re-runs Wave 1 dependencies to `done`.

## Wave 2 / 3

**Not run** — P9 gate failed. When green, execute `sports_manifest_shard_migration_cleanup_2026_04_21.plan.md` then
`sports_data_status_fixture_level_drilldown_2026_04_21.plan.md` with the same §12.7 bundle + JSON handoff.
