# iCloud Corrupt Files — Per-Repo Migration Report

Generated from `find . -type f -exec stat -f "%b %z %N" {} \; 2>/dev/null | awk '$1==0 && $2>0 {print $3}'` (0 blocks, size>0 = iCloud placeholder/corrupt).
SSOT: unified-trading-pm/workspace-manifest.json

## Context

Repos were copied to iCloud (iDrive); many files became corrupt placeholders (0 blocks allocated, size>0).
Code path `/Users/ikennaigboaka/Code/unified-trading-system-repos/` has fresh git clones but some are 2–12 days old.
Local iCloud working copy is often newer. Goal: migrate non-corrupt files to Code, track corrupt ones for rebuild.

## Symlinked repos (already migrated)

These point to Code — no iCloud corruption in workspace.

- **deployment-api**
- **deployment-service**
- **deployment-ui**
- **settlement-ui**
- **unified-trading-pm**

---

## Repos WITH corrupt files (cleanup before copy)

### archive (268 corrupt)

**Files to remove (corrupt placeholders):**

- `./archive/sports-betting-services-previous/data/soccer_football/README.md`
- `./archive/sports-betting-services-previous/docs/CLI_MIGRATION.md`
- `./archive/sports-betting-services-previous/docs/FEATURES_CLI_MIGRATION_PLAN.md`
- `./archive/sports-betting-services-previous/docs/arbiterage/VIG_ANALYSIS_GUIDE.md`
- `./archive/sports-betting-services-previous/docs/arbiterage/arbs_explanation.md`
- `./archive/sports-betting-services-previous/docs/archive/Features.md`
- `./archive/sports-betting-services-previous/docs/archive/chat_gpt_features.md`
- `./archive/sports-betting-services-previous/docs/archive/chat_gpt_features_2.md`
- `./archive/sports-betting-services-previous/docs/archive/feature_3.md`
- `./archive/sports-betting-services-previous/docs/archive/features_2.md`
- `./archive/sports-betting-services-previous/docs/archive/features_friend.md`
- `./archive/sports-betting-services-previous/docs/cli/API_CLIENTS_OVERVIEW.md`
- `./archive/sports-betting-services-previous/docs/cli/CLIENT_COMPARISON.md`
- `./archive/sports-betting-services-previous/docs/cli/COMPLETE_ENDPOINT_SUMMARY.md`
- `./archive/sports-betting-services-previous/docs/cli/DATA_SOURCES_AND_ENDPOINTS.md`
- `./archive/sports-betting-services-previous/docs/cli/FOOTYSTATS_API.md`
- `./archive/sports-betting-services-previous/docs/cli/FOOTYSTATS_CLI.md`
- `./archive/sports-betting-services-previous/docs/cli/FOOTYSTATS_CLI_UPDATE.md`
- `./archive/sports-betting-services-previous/docs/cli/OPEN_METEO.md`
- `./archive/sports-betting-services-previous/docs/cli/OPEN_METEO_SUMMARY.md`
- `./archive/sports-betting-services-previous/docs/cli/README.md`
- `./archive/sports-betting-services-previous/docs/cli/SOCCER_FOOTBALL_INFO.md`
- `./archive/sports-betting-services-previous/docs/cli/SOCCER_FOOTBALL_INFO_API_ENDPOINTS.md`
- `./archive/sports-betting-services-previous/docs/cli/SOCCER_FOOTBALL_INFO_CLI_UPDATE.md`
- `./archive/sports-betting-services-previous/docs/cli/SOCCER_FOOTBALL_PIPELINE.md`
- `./archive/sports-betting-services-previous/docs/cli/UPDATE_COUNTS.md`
- `./archive/sports-betting-services-previous/docs/cli/location.md`
- `./archive/sports-betting-services-previous/docs/core/CONTRACTOR_AGREEMENT_HARSH.md`
- `./archive/sports-betting-services-previous/docs/core/DATA_ARCHITECTURE.md`
- `./archive/sports-betting-services-previous/docs/core/DEPLOYMENT_GUIDE.md`
- `./archive/sports-betting-services-previous/docs/core/FEATURE_ENGINEERING.md`
- `./archive/sports-betting-services-previous/docs/core/HARSH_IMPLEMENTATION_GUIDE.md`
- `./archive/sports-betting-services-previous/docs/core/INSTRUMENT_KEY.md`
- `./archive/sports-betting-services-previous/docs/core/LEAGUE_CLASSIFICATION.md`
- `./archive/sports-betting-services-previous/docs/core/ML_MODELS.md`
- `./archive/sports-betting-services-previous/docs/core/instrument_keys.md`
- `./archive/sports-betting-services-previous/docs/data`
- `./archive/sports-betting-services-previous/docs/data`
- `./archive/sports-betting-services-previous/docs/data`
- `./archive/sports-betting-services-previous/docs/data`
- `./archive/sports-betting-services-previous/docs/data`
- `./archive/sports-betting-services-previous/docs/data`
- `./archive/sports-betting-services-previous/docs/deployment/DEPLOYMENT_GUIDE.md`
- `./archive/sports-betting-services-previous/docs/deployment/UV_WORKSPACE_SETUP.md`
- `./archive/sports-betting-services-previous/docs/deployment/cloud_batch_deployment_framework.md`
- `./archive/sports-betting-services-previous/docs/features/FEATURE_AUDIT_REPORT.md`
- `./archive/sports-betting-services-previous/docs/features/FEATURE_IMPLEMENTATION_STATUS.md`
- `./archive/sports-betting-services-previous/docs/features/HARSH_IMPLEMENTATION_GUIDE.md`
- `./archive/sports-betting-services-previous/docs/features/ML_MODELS.md`
- `./archive/sports-betting-services-previous/docs/features/REQUIRED_LIBRARIES.md`
- `./archive/sports-betting-services-previous/docs/features/raw_data_spec.md`
- `./archive/sports-betting-services-previous/docs/features/reference_data_spec.md`
- `./archive/sports-betting-services-previous/docs/tools/NOTEBOOK_OUTPUT_STRIPPING.md`
- `./archive/sports-betting-services-previous/docs/tools/setup-precommit-rs.sh`
- `./archive/sports-betting-services-previous/examples/example_compute_features.py`
- `./archive/sports-betting-services-previous/examples/open_meteo_quickstart.py`
- `./archive/sports-betting-services-previous/extra/CONFLICTS_SUMMARY.md`
- `./archive/sports-betting-services-previous/extra/CSV_VERIFICATION_FINAL_REPORT.md`
- `./archive/sports-betting-services-previous/extra/LEAGUE_CONFIG_DISCREPANCIES.md`
- `./archive/sports-betting-services-previous/extra/VERIFICATION_SUMMARY.md`
- `./archive/sports-betting-services-previous/extra/apply_csv_corrections.py`
- `./archive/sports-betting-services-previous/extra/improved_ff_mappings.ipynb`
- `./archive/sports-betting-services-previous/extra/improved_team_matcher.py`
- `./archive/sports-betting-services-previous/extra/league_classification_config.py`
- `./archive/sports-betting-services-previous/extra/league_classification_config_backup_before_csv_verification.py`
- `./archive/sports-betting-services-previous/extra/league_data_sources_dict.py`
- `./archive/sports-betting-services-previous/extra/rounds.py`
- `./archive/sports-betting-services-previous/extra/update_league_config.py`
- `./archive/sports-betting-services-previous/extra/verify_league_config.py`
- `./archive/sports-betting-services-previous/extra/weather.py`
- `./archive/sports-betting-services-previous/footballbets/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/arbitrage/analyze.py`
- `./archive/sports-betting-services-previous/footballbets/arbitrage/analyze_bookmaker_vig.py`
- `./archive/sports-betting-services-previous/footballbets/arbitrage/arbiterage.ipynb`
- `./archive/sports-betting-services-previous/footballbets/arbitrage/generate_report.py`
- `./archive/sports-betting-services-previous/footballbets/arbitrage/odds.ipynb`
- `./archive/sports-betting-services-previous/footballbets/arbitrage/odds.py`
- `./archive/sports-betting-services-previous/footballbets/arbitrage/odds_analyse.ipynb`
- `./archive/sports-betting-services-previous/footballbets/cli/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/cli/api_football_cli.py`
- `./archive/sports-betting-services-previous/footballbets/cli/common.py`
- `./archive/sports-betting-services-previous/footballbets/cli/footystats_cli.py`
- `./archive/sports-betting-services-previous/footballbets/cli/location.py`
- `./archive/sports-betting-services-previous/footballbets/cli/market_tick_data_cli.py`
- `./archive/sports-betting-services-previous/footballbets/cli/odds_api_cli.py`
- `./archive/sports-betting-services-previous/footballbets/cli/soccer_football_info_cli.py`
- `./archive/sports-betting-services-previous/footballbets/cli/understat_cli.py`
- `./archive/sports-betting-services-previous/footballbets/clients/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/clients/api_football.py`
- `./archive/sports-betting-services-previous/footballbets/clients/footystats.py`
- `./archive/sports-betting-services-previous/footballbets/clients/open_meteo.py`
- `./archive/sports-betting-services-previous/footballbets/clients/soccer_football.py`
- `./archive/sports-betting-services-previous/footballbets/clients/understat.py`
- `./archive/sports-betting-services-previous/footballbets/core/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/core/config.py`
- `./archive/sports-betting-services-previous/footballbets/core/database.py`
- `./archive/sports-betting-services-previous/footballbets/core/feature_models.py`
- `./archive/sports-betting-services-previous/footballbets/core/logging_service.py`
- `./archive/sports-betting-services-previous/footballbets/core/mapping.py`
- `./archive/sports-betting-services-previous/footballbets/core/models.py`
- `./archive/sports-betting-services-previous/footballbets/features/FEATURE_TESTING_README.md`
- `./archive/sports-betting-services-previous/footballbets/features/README.md`
- `./archive/sports-betting-services-previous/footballbets/features/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/features/advanced_stats.py`
- `./archive/sports-betting-services-previous/footballbets/features/base.py`
- `./archive/sports-betting-services-previous/footballbets/features/data_loader.py`
- `./archive/sports-betting-services-previous/footballbets/features/docs/FEATURE_IMPLEMENTATION_STATUS.md`
- `./archive/sports-betting-services-previous/footballbets/features/docs/FEATURE_STATUS_AND_PLAN.md`
- `./archive/sports-betting-services-previous/footballbets/features/docs/core/FEATURES_DOMAIN_GUIDES.md`
- `./archive/sports-betting-services-previous/footballbets/features/feature_tests/dummy_odds_feature_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/feature_tests/goal_timing_feature_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/feature_tests/h2h_feature_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/feature_tests/referee_feature_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/feature_tests/team_feature_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/feature_tests/venue_context_feature_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/feature_tests/weather_feature_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/goal_timing.py`
- `./archive/sports-betting-services-previous/footballbets/features/h2h.py`
- `./archive/sports-betting-services-previous/footballbets/features/halftime.py`
- `./archive/sports-betting-services-previous/footballbets/features/league.py`
- `./archive/sports-betting-services-previous/footballbets/features/multisource_xg.py`
- `./archive/sports-betting-services-previous/footballbets/features/odds.py`
- `./archive/sports-betting-services-previous/footballbets/features/pipeline_test.py`
- `./archive/sports-betting-services-previous/footballbets/features/player_lineup.py`
- `./archive/sports-betting-services-previous/footballbets/features/poisson_xg.py`
- `./archive/sports-betting-services-previous/footballbets/features/referee.py`
- `./archive/sports-betting-services-previous/footballbets/features/season_context.py`
- `./archive/sports-betting-services-previous/footballbets/features/team.py`
- `./archive/sports-betting-services-previous/footballbets/features/team_oop.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/README.md`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/advanced_stats_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/feature_status.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/goal_timing_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/h2h_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/halftime_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/league_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/odds_market_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/player_lineup_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/poisson_xg_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/season_context_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/team_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/utils.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/venue_context_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/tracking/weather_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/venue_context.py`
- `./archive/sports-betting-services-previous/footballbets/features/visualization/README.md`
- `./archive/sports-betting-services-previous/footballbets/features/visualization/VISUALIZATION_FRAMEWORK_SUMMARY.md`
- `./archive/sports-betting-services-previous/footballbets/features/visualization/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/features/visualization/view_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/visualization/view_features_sql.sql`
- `./archive/sports-betting-services-previous/footballbets/features/visualization/visualize_features.py`
- `./archive/sports-betting-services-previous/footballbets/features/visualization/visualizer.py`
- `./archive/sports-betting-services-previous/footballbets/features/weather.py`
- `./archive/sports-betting-services-previous/footballbets/main.py`
- `./archive/sports-betting-services-previous/footballbets/scripts/README.md`
- `./archive/sports-betting-services-previous/footballbets/scripts/SOCCER_FOOTBALL_SCRIPT_GUIDE.md`
- `./archive/sports-betting-services-previous/footballbets/scripts/audit_features.py`
- `./archive/sports-betting-services-previous/footballbets/scripts/check_db_size.py`
- `./archive/sports-betting-services-previous/footballbets/scripts/feature_status.py`
- `./archive/sports-betting-services-previous/footballbets/scripts/fetch_api_football_data.sh`
- `./archive/sports-betting-services-previous/footballbets/scripts/fetch_footystats_data.sh`
- `./archive/sports-betting-services-previous/footballbets/scripts/fetch_soccer_football_data.sh`
- `./archive/sports-betting-services-previous/footballbets/scripts/fetch_understat_data.sh`
- `./archive/sports-betting-services-previous/footballbets/scripts/pipeline_test.py`
- `./archive/sports-betting-services-previous/footballbets/scripts/test_progressive_data.py`
- `./archive/sports-betting-services-previous/footballbets/tests/test_championship_flatten.py`
- `./archive/sports-betting-services-previous/footballbets/tests/test_footystats_endpoints.py`
- `./archive/sports-betting-services-previous/footballbets/tests/test_match_details.py`
- `./archive/sports-betting-services-previous/footballbets/tests/test_open_meteo_client.py`
- `./archive/sports-betting-services-previous/footballbets/tests/test_progressive_data.py`
- `./archive/sports-betting-services-previous/footballbets/utils/README_PLAYER_MAPPING.md`
- `./archive/sports-betting-services-previous/footballbets/utils/README_TEAM_MAPPING.md`
- `./archive/sports-betting-services-previous/footballbets/utils/__init__.py`
- `./archive/sports-betting-services-previous/footballbets/utils/create_player_mapping.py`
- `./archive/sports-betting-services-previous/footballbets/utils/create_team_mapping.py`
- `./archive/sports-betting-services-previous/footballbets/utils/footystats_analyzers.py`
- `./archive/sports-betting-services-previous/footballbets/utils/footystats_normalizers.py`
- `./archive/sports-betting-services-previous/footballbets/utils/footystats_parsers.py`
- `./archive/sports-betting-services-previous/footballbets/utils/footystats_team_mapping.py`
- `./archive/sports-betting-services-previous/footballbets/utils/mapping.py`
- `./archive/sports-betting-services-previous/footballbets/utils/match_fixtures.py`
- `./archive/sports-betting-services-previous/footballbets/utils/team_name_changes.py`
- `./archive/sports-betting-services-previous/market-tick-data-service/COMPLETION_SUMMARY.md`
- `./archive/sports-betting-services-previous/market-tick-data-service/IMPLEMENTATION_STATUS.md`
- `./archive/sports-betting-services-previous/market-tick-data-service/QUICK_START.md`
- `./archive/sports-betting-services-previous/market-tick-data-service/README.md`
- `./archive/sports-betting-services-previous/market-tick-data-service/docs/INCREMENTAL_BOOK_L2.md`
- `./archive/sports-betting-services-previous/market-tick-data-service/market_tick_data/__init__.py`
- `./archive/sports-betting-services-previous/market-tick-data-service/market_tick_data/adapters/__pycache__/tardis_adapter.cpython-313.pyc`
- `./archive/sports-betting-services-previous/market-tick-data-service/market_tick_data/config/__init__.py`
- `./archive/sports-betting-services-previous/market-tick-data-service/market_tick_data/config/__pycache__/__init__.cpython-313.pyc`
- `./archive/sports-betting-services-previous/market-tick-data-service/market_tick_data/schemas/__pycache__/__init__.cpython-313.pyc`
- `./archive/sports-betting-services-previous/market-tick-data-service/tests/__init__.py`
- `./archive/sports-betting-services-previous/market-tick-data-service/tests/test_adapters.py`
- `./archive/sports-betting-services-previous/market-tick-data-service/tests/test_config.py`
- `./archive/sports-betting-services-previous/migrations/add_counts_fetched_to_sf_leagues.sql`
- `./archive/sports-betting-services-previous/migrations/add_sf_match_events_dominance_tables.sql`
- `./archive/sports-betting-services-previous/migrations/add_sf_progressive_tables.sql`
- `./archive/sports-betting-services-previous/migrations/add_soccer_football_info_columns.sql`
- `./archive/sports-betting-services-previous/migrations/cleanup_sf_match_columns.sql`
- `./archive/sports-betting-services-previous/migrations/data_updates.sql`
- `./archive/sports-betting-services-previous/migrations/fix_percentage_columns.sql`
- `./archive/sports-betting-services-previous/notebooks/canonical_key.ipynb`
- `./archive/sports-betting-services-previous/notebooks/mapping_ft_fixtures.ipynb`
- `./archive/sports-betting-services-previous/notebooks/mapping_ft_teams.ipynb`
- `./archive/sports-betting-services-previous/notebooks/mapping_od_fixtures.ipynb`
- `./archive/sports-betting-services-previous/notebooks/mapping_sf_fixtures.ipynb`
- `./archive/sports-betting-services-previous/notebooks/mapping_sf_teams.ipynb`
- `./archive/sports-betting-services-previous/notebooks/mapping_tm_teams.ipynb`
- `./archive/sports-betting-services-previous/notebooks/mapping_us_teams.ipynb`
- `./archive/sports-betting-services-previous/notebooks/pipeline_af.ipynb`
- `./archive/sports-betting-services-previous/notebooks/pipeline_ft.ipynb`
- `./archive/sports-betting-services-previous/notebooks/pipeline_od.ipynb`
- `./archive/sports-betting-services-previous/notebooks/pipeline_tm.ipynb`
- `./archive/sports-betting-services-previous/notebooks/pipeline_us.ipynb`
- `./archive/sports-betting-services-previous/notebooks/schemas.py`
- `./archive/sports-betting-services-previous/notebooks/verify_fixture_mappings.ipynb`
- `./archive/sports-betting-services-previous/scripts/quickmerge.sh.bak`
- `./archive/sports-execution-service/sports_execution_service.egg-info/PKG-INFO`
- `./archive/sports-execution-service/sports_execution_service.egg-info/SOURCES.txt`
- `./archive/sports-execution-service/sports_execution_service.egg-info/dependency_links.txt`
- `./archive/sports-execution-service/sports_execution_service.egg-info/requires.txt`
- `./archive/sports-execution-service/sports_execution_service.egg-info/top_level.txt`
- `./archive/sports-execution-service/sports_execution_service/__init__.py`
- `./archive/sports-execution-service/sports_execution_service/adapters/__init__.py`
- `./archive/sports-execution-service/sports_execution_service/adapters/broadcast_sink.py`
- `./archive/sports-execution-service/sports_execution_service/adapters/live_data_source.py`
- `./archive/sports-execution-service/sports_execution_service/engine.py`
- `./archive/sports-execution-service/tests/unit/test_imports.py`
- `./archive/sports-odds-data-service/sports_odds_data_service.egg-info/PKG-INFO`
- `./archive/sports-odds-data-service/sports_odds_data_service.egg-info/SOURCES.txt`
- `./archive/sports-odds-data-service/sports_odds_data_service.egg-info/dependency_links.txt`
- `./archive/sports-odds-data-service/sports_odds_data_service.egg-info/requires.txt`
- `./archive/sports-odds-data-service/sports_odds_data_service.egg-info/top_level.txt`
- `./archive/sports-odds-data-service/sports_odds_data_service/__init__.py`
- `./archive/sports-odds-data-service/sports_odds_data_service/adapters/__init__.py`
- `./archive/sports-odds-data-service/sports_odds_data_service/adapters/broadcast_sink.py`
- `./archive/sports-odds-data-service/sports_odds_data_service/adapters/live_data_source.py`
- `./archive/sports-odds-data-service/sports_odds_data_service/engine.py`
- `./archive/sports-odds-data-service/tests/unit/test_imports.py`
- `./archive/sports-odds-processing-service/sports_odds_processing_service.egg-info/PKG-INFO`
- `./archive/sports-odds-processing-service/sports_odds_processing_service.egg-info/SOURCES.txt`
- `./archive/sports-odds-processing-service/sports_odds_processing_service.egg-info/dependency_links.txt`
- `./archive/sports-odds-processing-service/sports_odds_processing_service.egg-info/requires.txt`
- `./archive/sports-odds-processing-service/sports_odds_processing_service.egg-info/top_level.txt`
- `./archive/sports-odds-processing-service/sports_odds_processing_service/__init__.py`
- `./archive/sports-odds-processing-service/sports_odds_processing_service/adapters/__init__.py`
- `./archive/sports-odds-processing-service/sports_odds_processing_service/adapters/broadcast_sink.py`
- `./archive/sports-odds-processing-service/sports_odds_processing_service/adapters/live_data_source.py`
- `./archive/sports-odds-processing-service/tests/unit/test_imports.py`
- `./archive/sports-reference-data-service/sports_reference_data_service.egg-info/SOURCES.txt`
- `./archive/sports-reference-data-service/sports_reference_data_service/adapters/__init__.py`
- `./archive/sports-reference-data-service/sports_reference_data_service/adapters/broadcast_sink.py`
- `./archive/sports-reference-data-service/sports_reference_data_service/adapters/live_data_source.py`
- `./archive/sports-reference-data-service/sports_reference_data_service/engine.py`
- `./archive/sports-reference-data-service/tests/unit/test_imports.py`
- `./archive/sports-strategy-service/sports_strategy_service.egg-info/PKG-INFO`
- `./archive/sports-strategy-service/sports_strategy_service.egg-info/SOURCES.txt`
- `./archive/sports-strategy-service/sports_strategy_service.egg-info/dependency_links.txt`
- `./archive/sports-strategy-service/sports_strategy_service.egg-info/requires.txt`
- `./archive/sports-strategy-service/sports_strategy_service.egg-info/top_level.txt`
- `./archive/sports-strategy-service/sports_strategy_service/__init__.py`
- `./archive/sports-strategy-service/sports_strategy_service/adapters/__init__.py`
- `./archive/sports-strategy-service/sports_strategy_service/adapters/broadcast_sink.py`
- `./archive/sports-strategy-service/sports_strategy_service/adapters/live_data_source.py`
- `./archive/sports-strategy-service/sports_strategy_service/engine.py`
- `./archive/sports-strategy-service/tests/unit/test_imports.py`

### execution-algo-library (1 corrupt)

**Files to remove (corrupt placeholders):**

- `./execution-algo-library/execution_algo_library/exit_algos/__init__.py`

### execution-analytics-ui (2 corrupt)

**Files to remove (corrupt placeholders):**

- `./execution-analytics-ui/.cursor/scripts/check-import-patterns.py`
- `./execution-analytics-ui/tests/smoke/navigation.spec.ts`

### execution-service (285 corrupt)

**Files to remove (corrupt placeholders):**

- `./execution-service/configs/comprehensive_matrix/CEFI_BTC_momentum-macd_ADAPTIVE_TWAP.json`
- `./execution-service/configs/comprehensive_matrix/CEFI_BTC_momentum-macd_ALMGREN_CHRISS.json`
- `./execution-service/configs/comprehensive_matrix/CEFI_BTC_momentum-macd_BENCHMARK_FILL.json`
- `./execution-service/configs/comprehensive_matrix/CEFI_BTC_momentum-macd_TWAP.json`
- `./execution-service/configs/comprehensive_matrix/CEFI_BTC_momentum-macd_VWAP.json`
- `./execution-service/configs/comprehensive_matrix/DEFI_ETH_comprehensive-defi_ADAPTIVE_TWAP.json`
- `./execution-service/configs/comprehensive_matrix/DEFI_ETH_comprehensive-defi_ALMGREN_CHRISS.json`
- `./execution-service/configs/comprehensive_matrix/DEFI_ETH_comprehensive-defi_BENCHMARK_FILL.json`
- `./execution-service/configs/comprehensive_matrix/DEFI_ETH_comprehensive-defi_TWAP.json`
- `./execution-service/configs/comprehensive_matrix/DEFI_ETH_comprehensive-defi_VWAP.json`
- `./execution-service/configs/comprehensive_matrix/TRADFI_SPY_momentum-macd_ADAPTIVE_TWAP.json`
- `./execution-service/configs/comprehensive_matrix/TRADFI_SPY_momentum-macd_ALMGREN_CHRISS.json`
- `./execution-service/configs/comprehensive_matrix/TRADFI_SPY_momentum-macd_BENCHMARK_FILL.json`
- `./execution-service/configs/comprehensive_matrix/TRADFI_SPY_momentum-macd_TWAP.json`
- `./execution-service/configs/comprehensive_matrix/TRADFI_SPY_momentum-macd_VWAP.json`
- `./execution-service/configs/comprehensive_matrix/comprehensive_batch_results.json`
- `./execution-service/configs/representative_algos/BENCHMARK_FILL_V1.json`
- `./execution-service/configs/representative_algos/ICEBERG_refresh_interval_secs10_visible_pct0.03_V1.json`
- `./execution-service/configs/representative_algos/POV_DYNAMIC_max_pov0.5_min_pov0.01_target_pov0.1_V1.json`
- `./execution-service/configs/representative_algos/TWAP_horizon_secs300_interval_secs30_num_slices10_V1.json`
- `./execution-service/configs/representative_algos/VWAP_num_intervals12_volume_profileU_SHAPED_V1.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_ADAPTIVE_TWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_ALMGREN_CHRISS.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_BENCHMARK_FILL.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_HYBRID_OPTIMAL.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_ICEBERG.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_PASSIVE_AGGRESSIVE_HYBRID.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_POV_DYNAMIC.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_TWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-deribit_VWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_ADAPTIVE_TWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_ALMGREN_CHRISS.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_BENCHMARK_FILL.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_HYBRID_OPTIMAL.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_ICEBERG.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_PASSIVE_AGGRESSIVE_HYBRID.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_POV_DYNAMIC.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_TWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_BTC_momentum-macd_VWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_ADAPTIVE_TWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_ALMGREN_CHRISS.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_BENCHMARK_FILL.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_HYBRID_OPTIMAL.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_ICEBERG.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_PASSIVE_AGGRESSIVE_HYBRID.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_POV_DYNAMIC.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_TWAP.json`
- `./execution-service/configs/representative_matrix/CEFI_ETH_momentum-macd_VWAP.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_ADAPTIVE_TWAP.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_ALMGREN_CHRISS.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_BENCHMARK_FILL.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_HYBRID_OPTIMAL.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_ICEBERG.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_PASSIVE_AGGRESSIVE_HYBRID.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_POV_DYNAMIC.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_TWAP.json`
- `./execution-service/configs/representative_matrix/DEFI_ETH_comprehensive-defi_VWAP.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_ADAPTIVE_TWAP.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_ALMGREN_CHRISS.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_BENCHMARK_FILL.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_HYBRID_OPTIMAL.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_ICEBERG.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_PASSIVE_AGGRESSIVE_HYBRID.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_POV_DYNAMIC.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_TWAP.json`
- `./execution-service/configs/representative_matrix/TRADFI_SPY_momentum-macd_VWAP.json`
- `./execution-service/configs/representative_matrix/batch_results.json`
- `./execution-service/configs/smoke_test/README.md`
- `./execution-service/configs/smoke_test/cefi_l2_smoke.json`
- `./execution-service/configs/smoke_test/defi_amm_smoke.json`
- `./execution-service/configs/smoke_test/tradfi_l1_smoke.json`
- `./execution-service/configs/ssot/README.md`
- `./execution-service/configs/ssot/cefi_btc_trade.json`
- `./execution-service/configs/ssot/cefi_btc_trade_huf.json`
- `./execution-service/configs/ssot/defi_comprehensive.json`
- `./execution-service/configs/ssot/defi_comprehensive_huf.json`
- `./execution-service/configs/ssot/tradfi_spy_trade.json`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/config.json`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/equity_curve.parquet`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/execution_alpha.json`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/fills.parquet`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/orders.parquet`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/positions.parquet`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/summary.json`
- `./execution-service/data/sample/CEFI_ETH_momentum-macd_SCE_5M_V2_202305230000-202305230400_16e89b/timeline.json`
- `./execution-service/docs/battle-testing/BATTLE_TEST_CHECKLIST.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-08_PHASEB_SPEED_CLOSEOUT.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-08_PHASEC_DEEP_DIVE_GCS_CLIENT_SYNC.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-08_PHASEC_LOCAL_EXEC_ALPHA_HOTFIX.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-08_PHASEC_VISUALIZER_DEBUG_CLOSEOUT.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-08_RUNTIME_SAFETY_AND_SIZING.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-09_PHASEC_D2_D3_PRICE_SCALE_GUARD.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-09_PHASEC_FULLPATH_MATRIX_AND_CLOSEOUT_PLAN.md`
- `./execution-service/docs/battle-testing/PR_REPORT_2026-02-09_PHASEC_VISUALIZER_LOCAL_DEFAULT_AND_GCS_HEALTH.md`
- `./execution-service/docs/plans/order_matching_fix.md`
- `./execution-service/docs/specs/ALGORITHM_PARAMS.md`
- `./execution-service/docs/specs/CONFIG_SCHEMA.md`
- `./execution-service/docs/specs/DATA_SCHEMAS.md`
- `./execution-service/docs/specs/GCS_STRUCTURE.md`
- `./execution-service/docs/specs/README.md`
- `./execution-service/docs/specs/RESULT_SCHEMA.md`
- `./execution-service/docs/specs/examples/CONFIG_CEFI_EXAMPLE.json`
- `./execution-service/docs/specs/examples/CONFIG_DEFI_COMPREHENSIVE_EXAMPLE.json`
- `./execution-service/docs/specs/examples/CONFIG_DEFI_SWAP_EXAMPLE.json`
- `./execution-service/docs/specs/examples/CONFIG_TRADFI_EXAMPLE.json`
- `./execution-service/execution_service/algorithms/ALGORITHM_MARKET_ASSUMPTIONS.md`
- `./execution-service/execution_service/algorithms/ALPHA_CALCULATION_ASSUMPTIONS.md`
- `./execution-service/execution_service/algorithms/README.md`
- `./execution-service/scripts/benchmark_runners/run_fresh_benchmark.sh`
- `./execution-service/scripts/benchmark_runners/run_fresh_benchmark_comparison.sh`
- `./execution-service/scripts/config_generation/README.md`
- `./execution-service/scripts/demos/README.md`
- `./execution-service/scripts/instruction_generation/README.md`
- `./execution-service/scripts/migrations/migrate_to_unified_execution_bucket.sh`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_15M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_15M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_15M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_5M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_5M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_5M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_HUF_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_15M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_15M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_15M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_5M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_5M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_5M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-deribit_SCE_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_15M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_15M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_15M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_5M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_5M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_5M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_HUF_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_15M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_15M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_15M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_5M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_5M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_5M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_BTC_momentum-macd_SCE_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_15M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_15M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_15M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_5M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_5M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_5M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_HUF_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_15M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_15M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_15M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_5M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_5M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_5M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/CEFI_ETH_momentum-macd_SCE_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_15M_V2/2024-01-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_HUF_5M_V2/2024-01-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_15M_V2/2024-01-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_5M_V1/day-2023-05-23/instructions.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_5M_V1/day-2023-05-24/instructions.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_5M_V1/day-2023-05-25/instructions.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_comprehensive-defi_SCE_5M_V2/2024-01-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_staking-only_HUF_1H_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_staking-only_HUF_1H_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_staking-only_HUF_1H_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_staking-only_SCE_1H_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_staking-only_SCE_1H_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_staking-only_SCE_1H_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_HUF_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_HUF_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_HUF_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_HUF_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_HUF_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_HUF_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_SCE_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_SCE_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_SCE_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_SCE_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_SCE_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_ETH_swap-routing_SCE_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_USDT_pure-lending_HUF_1H_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_USDT_pure-lending_HUF_1H_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_USDT_pure-lending_HUF_1H_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/DEFI_USDT_pure-lending_SCE_1H_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/DEFI_USDT_pure-lending_SCE_1H_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/DEFI_USDT_pure-lending_SCE_1H_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_HUF_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_HUF_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_HUF_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_HUF_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_HUF_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_HUF_5M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_SCE_15M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_SCE_15M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_SCE_15M_V2/2023-05-25.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_SCE_5M_V2/2023-05-23.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_SCE_5M_V2/2023-05-24.parquet`
- `./execution-service/standard_test_instructions/TRADFI_SPY_momentum-macd_SCE_5M_V2/2023-05-25.parquet`
- `./execution-service/tests/algos/01_test_TWAP_cefi.sh`
- `./execution-service/tests/algos/02_test_VWAP_cefi.sh`
- `./execution-service/tests/algos/03_test_ICEBERG_cefi.sh`
- `./execution-service/tests/algos/04_test_ADAPTIVE_TWAP_cefi.sh`
- `./execution-service/tests/algos/05_test_ALMGREN_CHRISS_cefi.sh`
- `./execution-service/tests/algos/06_test_POV_DYNAMIC_cefi.sh`
- `./execution-service/tests/algos/07_test_HYBRID_OPTIMAL_cefi.sh`
- `./execution-service/tests/algos/08_test_PASSIVE_AGGRESSIVE_HYBRID_cefi.sh`
- `./execution-service/tests/algos/09_test_TWAP_tradfi.sh`
- `./execution-service/tests/algos/10_test_VWAP_tradfi.sh`
- `./execution-service/tests/algos/11_test_ICEBERG_tradfi.sh`
- `./execution-service/tests/algos/12_test_ADAPTIVE_TWAP_tradfi.sh`
- `./execution-service/tests/algos/13_test_ALMGREN_CHRISS_tradfi.sh`
- `./execution-service/tests/algos/14_test_POV_DYNAMIC_tradfi.sh`
- `./execution-service/tests/algos/15_test_HYBRID_OPTIMAL_tradfi.sh`
- `./execution-service/tests/algos/16_test_PASSIVE_AGGRESSIVE_HYBRID_tradfi.sh`
- `./execution-service/tests/algos/CONFIG_STRATEGY_SIGNALS.md`
- `./execution-service/tests/algos/PRODUCTION_GRADE_CHECKLIST.md`
- `./execution-service/tests/algos/QUICK_START.md`
- `./execution-service/tests/algos/README.md`
- `./execution-service/tests/algos/TEST_LIST.md`
- `./execution-service/tests/algos/check_and_show_results.sh`
- `./execution-service/tests/algos/run_all_tests.sh`
- `./execution-service/tests/backtest/DEFI_ISSUES_FIXED.md`
- `./execution-service/tests/backtest/ERROR_ANALYSIS.md`
- `./execution-service/tests/backtest/FIXES_APPLIED.md`
- `./execution-service/tests/backtest/PNL_CALCULATION_ISSUE.md`
- `./execution-service/tests/backtest/README.md`
- `./execution-service/tests/backtest/TEST_VERIFICATION_REPORT.md`
- `./execution-service/tests/backtest/UNISWAP_FIX_ANALYSIS.md`
- `./execution-service/tests/backtest/test_alpha_verification_all_domains.sh`
- `./execution-service/tests/backtest/test_backtest_progression_cefi.sh`
- `./execution-service/tests/backtest/test_backtest_progression_cefi_l1.sh`
- `./execution-service/tests/backtest/test_backtest_progression_cefi_l2.sh`
- `./execution-service/tests/backtest/test_backtest_progression_defi.sh`
- `./execution-service/tests/backtest/test_backtest_progression_tradfi_l1.sh`
- `./execution-service/tests/backtest/test_three_domain_backtests.sh`
- `./execution-service/tests/e2e/README.md`
- `./execution-service/tests/integration/README.md`
- `./execution-service/tests/live/README.md`
- `./execution-service/tests/performance/README.md`
- `./execution-service/tests/performance/run_performance_test.sh`
- `./execution-service/tests/regression/README.md`
- `./execution-service/tests/unit/README.md`

### features-cross-instrument-service (9 corrupt)

**Files to remove (corrupt placeholders):**

- `./features-cross-instrument-service/.git/objects/00/4ec977c50f339ceb411a776d39b6b590ee6b97`
- `./features-cross-instrument-service/.git/objects/5d/7a1457f45f9d796f934efba789f7ff00abf124`
- `./features-cross-instrument-service/.git/objects/74/dc6e335e81feaaa574fc7a2803e3f511f2b714`
- `./features-cross-instrument-service/.git/objects/7d/ac67d23b9cd973114aeff851d3696a319b51a9`
- `./features-cross-instrument-service/.git/objects/ab/d11abc2045903709e0c6ae3134c54a89b7dc49`
- `./features-cross-instrument-service/.git/objects/d3/4c57a26192e1b2bc15bfe41a188850f5211dc1`
- `./features-cross-instrument-service/.git/objects/de/e80913046b975cad6dd8aac1fcc45fb7566ec8`
- `./features-cross-instrument-service/.git/objects/ef/c5fd91373726fea85f4c946a827a9a623b4ced`
- `./features-cross-instrument-service/.git/refs/heads/main`

### features-delta-one-service (24 corrupt)

**Files to remove (corrupt placeholders):**

- `./features-delta-one-service/.git/filter-repo/already_ran`
- `./features-delta-one-service/.git/filter-repo/changed-refs`
- `./features-delta-one-service/.git/filter-repo/first-changed-commits`
- `./features-delta-one-service/.git/filter-repo/suboptimal-issues`
- `./features-delta-one-service/.git/hooks/applypatch-msg.sample`
- `./features-delta-one-service/.git/hooks/commit-msg`
- `./features-delta-one-service/.git/hooks/commit-msg.sample`
- `./features-delta-one-service/.git/hooks/post-update.sample`
- `./features-delta-one-service/.git/hooks/pre-applypatch.sample`
- `./features-delta-one-service/.git/hooks/pre-commit`
- `./features-delta-one-service/.git/hooks/pre-push.sample`
- `./features-delta-one-service/.git/hooks/pre-receive.sample`
- `./features-delta-one-service/.git/hooks/prepare-commit-msg.sample`
- `./features-delta-one-service/.git/hooks/push-to-checkout.sample`
- `./features-delta-one-service/.git/hooks/update.sample`
- `./features-delta-one-service/.git/logs/HEAD`
- `./features-delta-one-service/.git/objects/45/2004dbadd4e67380a9ada6c7305dac3e65691b`
- `./features-delta-one-service/.git/objects/4c/32241e55240050b29ccb3b8606ca9787d5b015`
- `./features-delta-one-service/.git/objects/8d/830fa24e02f1b539236b2f159d65d41903b1d4`
- `./features-delta-one-service/.git/objects/e9/e4f61568b3a4eb91b30f0465ab3d978cad3805`
- `./features-delta-one-service/.git/objects/ee/38688d2736aca2bdf629401085989df613d30d`
- `./features-delta-one-service/.git/objects/info/commit-graph`
- `./features-delta-one-service/.git/objects/pack/pack-1e4759e0c547c853b44a1aee4de0c7f268884f20.idx`
- `./features-delta-one-service/data/mock/BTCUSDT.csv`

### features-volatility-service (7 corrupt)

**Files to remove (corrupt placeholders):**

- `./features-volatility-service/.git/logs/refs/stash`
- `./features-volatility-service/.git/objects/30/108a0f170e29281e745021129a849f705a8cc4`
- `./features-volatility-service/.git/objects/73/d438f418d0ba37a91fe19d3f5f994d9581dc59`
- `./features-volatility-service/.git/objects/info/commit-graph`
- `./features-volatility-service/.git/objects/info/packs`
- `./features-volatility-service/.git/objects/pack/pack-bfb418bdf20f5b146c31d668fab98c18897804ca.idx`
- `./features-volatility-service/.git/refs/heads/fix/p0-security-credential-gitignore`

### instruments-service (23 corrupt)

**Files to remove (corrupt placeholders):**

- `./instruments-service/data/regression_after/2026-01-01/venue-AAVE_V3_ETH.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-BALANCER-ETH.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-CURVE-ETH.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-ETHENA.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-ETHERFI.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-EULER-PLASMA.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-FLUID-PLASMA.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-LIDO.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-MORPHO-ETHEREUM.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-UNISWAPV2-ETH.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-UNISWAPV3-ETH.parquet`
- `./instruments-service/data/regression_after/2026-01-01/venue-UNISWAPV4-ETH.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-AAVE_V3_ETH.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-BALANCER-ETH.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-ETHENA.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-ETHERFI.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-EULER-PLASMA.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-FLUID-PLASMA.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-LIDO.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-MORPHO-ETHEREUM.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-UNISWAPV2-ETH.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-UNISWAPV3-ETH.parquet`
- `./instruments-service/data/regression_before/2026-01-01/venue-UNISWAPV4-ETH.parquet`

### live-health-monitor-ui (14 corrupt)

**Files to remove (corrupt placeholders):**

- `./live-health-monitor-ui/.cursor/scripts/check-import-patterns.py`
- `./live-health-monitor-ui/src/api/manualTrading.ts`
- `./live-health-monitor-ui/src/auth/GoogleAuth.tsx`
- `./live-health-monitor-ui/src/auth/RequireAuth.tsx`
- `./live-health-monitor-ui/src/components/ContractHealth.tsx`
- `./live-health-monitor-ui/src/components/ManualTradingControls.tsx`
- `./live-health-monitor-ui/src/components/ManualTradingPanel.tsx`
- `./live-health-monitor-ui/src/components/PositionMonitor.tsx`
- `./live-health-monitor-ui/src/components/RiskMetrics.tsx`
- `./live-health-monitor-ui/src/hooks/useManualTradingForm.ts`
- `./live-health-monitor-ui/src/pages/SystemHealth.tsx`
- `./live-health-monitor-ui/tests/smoke/README.md`
- `./live-health-monitor-ui/tests/smoke/dashboard.spec.ts`
- `./live-health-monitor-ui/tests/smoke/navigation.spec.ts`

### market-data-processing-service (2 corrupt)

**Files to remove (corrupt placeholders):**

- `./market-data-processing-service/docs/batch_processing/HFT_FEATURES_SPECIFICATION.md`
- `./market-data-processing-service/docs/batch_processing/quality_gate_features.md`

### market-tick-data-service (2 corrupt)

**Files to remove (corrupt placeholders):**

- `./market-tick-data-service/tests/mock_data/candles/BTC-USDT_1m_2024-01-01.parquet`
- `./market-tick-data-service/tests/mock_data/ticks/BTC-USDT_trades_2024-01-01.parquet`

### matching-engine-library (7 corrupt)

**Files to remove (corrupt placeholders):**

- `./matching-engine-library/.cursor/scripts/check-import-patterns.py`
- `./matching-engine-library/docs/.temp-audit/LIBRARY_HARDENING.md`
- `./matching-engine-library/tests/unit/test_amm_math_edge_cases.py`
- `./matching-engine-library/tests/unit/test_amm_pools.py`
- `./matching-engine-library/tests/unit/test_matching_partial_fills.py`
- `./matching-engine-library/tests/unit/test_uniswap_v3_specifics.py`
- `./matching-engine-library/tests/unit/test_uniswap_v4_hooks.py`

### strategy-service (121 corrupt)

**Files to remove (corrupt placeholders):**

- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1123.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1126.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1209.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1221.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1234.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1237.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1248.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1252.json`
- `./strategy-service/data/analysis/leveraged_restaking_USDT_summary_usdt_100k_20251001_1326.json`
- `./strategy-service/data/blockchain_data/gas_data_orchestrator_report_2024-01-01_2025-09-26.json`
- `./strategy-service/data/blockchain_data/gas_prices/alchemy_fast_report_2024-01-01_2025-09-26.json`
- `./strategy-service/data/blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-26.csv`
- `./strategy-service/data/blockchain_data/gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv`
- `./strategy-service/data/blockchain_data/gas_prices/operation_gas_costs_summary_2024-01-01_2025-09-26.json`
- `./strategy-service/data/blockchain_data/onchain_gas_data_report_2024-01-01_2025-09-26.json`
- `./strategy-service/data/csv/BTC_USDT_5m.csv`
- `./strategy-service/data/csv/ETH_USDT_5m.csv`
- `./strategy-service/data/csv/SOL_USDT_5m.csv`
- `./strategy-service/data/execution_costs/execution_cost_orchestrator_report_2024-01-01_2025-09-18.json`
- `./strategy-service/data/execution_costs/execution_cost_simulation_results.csv`
- `./strategy-service/data/execution_costs/execution_cost_summary.json`
- `./strategy-service/data/execution_costs/lookup_tables/execution_costs_lookup.json`
- `./strategy-service/data/manual_sources/aave_params/aave_current_v3_prams_etherum_mainnet.csv`
- `./strategy-service/data/manual_sources/benchmark_data/ethena_susde_historical_20250923.csv`
- `./strategy-service/data/manual_sources/etherfi_distributions/bar-chart-supply-apy-2025-09-29-eeth.csv`
- `./strategy-service/data/manual_sources/etherfi_distributions/eigen_distributions_raw.csv`
- `./strategy-service/data/manual_sources/etherfi_distributions/ethfi_topups_raw.csv`
- `./strategy-service/data/manual_sources/etherfi_distributions/seasonal_drops.csv`
- `./strategy-service/data/manual_sources/etherfi_distributions/seasonal_drops.md`
- `./strategy-service/data/market_data/cex_data_orchestrator_report_2020-01-01_2025-09-26.json`
- `./strategy-service/data/market_data/cex_data_orchestrator_report_2024-01-01_2025-09-18.json`
- `./strategy-service/data/market_data/cex_data_orchestrator_report_2024-01-01_2025-09-30.json`
- `./strategy-service/data/market_data/cex_data_orchestrator_report_2024-05-01_2025-09-01.json`
- `./strategy-service/data/market_data/cex_data_orchestrator_report_2024-06-01_2024-07-01.json`
- `./strategy-service/data/market_data/cex_data_orchestrator_report_2024-08-01_2024-08-31.json`
- `./strategy-service/data/market_data/cex_data_orchestrator_report_2025-09-01_2025-09-18.json`
- `./strategy-service/data/market_data/ml/binance_BTCUSDT_perp_5m_2020-01-01_2025-10-13.csv`
- `./strategy-service/data/market_data/pool_data_orchestrator_report_2020-01-01_2025-09-27.json`
- `./strategy-service/data/market_data/spot_prices/spot_data_download_report_20250927_1933.json`
- `./strategy-service/data/ml_data/README.md`
- `./strategy-service/data/ml_data/predictions/btc_predictions.csv`
- `./strategy-service/data/ml_data/predictions/usdt_predictions.csv`
- `./strategy-service/data/protocol_data/aave/aave_calibration_report_20250929_1144.json`
- `./strategy-service/data/protocol_data/aave/aave_calibration_report_20250929_1219.json`
- `./strategy-service/data/protocol_data/aave/aave_calibration_summary_20250929_1144.json`
- `./strategy-service/data/protocol_data/aave/aave_calibration_summary_20250929_1219.json`
- `./strategy-service/data/protocol_data/aave/aave_pipeline_report_2024-01-01_2025-09-18_20250929_1144.json`
- `./strategy-service/data/protocol_data/aave/aave_pipeline_report_2024-01-01_2025-09-29_20250929_1218.json`
- `./strategy-service/data/protocol_data/aave/aave_pipeline_report_2024-01-01_2025-09-29_20250929_1219.json`
- `./strategy-service/docs/specs/strategies/01_PURE_LENDING_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/02_BTC_BASIS_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/03_ETH_BASIS_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/04_ETH_STAKING_ONLY_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/05_ETH_LEVERAGED_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/06_USDT_ETH_STAKING_HEDGED_SIMPLE_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/07_USDT_ETH_STAKING_HEDGED_LEVERAGED_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/08_ML_BTC_DIRECTIONAL_USDT_MARGIN_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/09_PURE_LENDING_ETH_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/10_ML_BTC_DIRECTIONAL_BTC_MARGIN_STRATEGY.md`
- `./strategy-service/docs/specs/strategies/DELTA_TRACKING_TEMPLATE.md`
- `./strategy-service/frontend/dist/assets/index-Be3PcsHv.js`
- `./strategy-service/frontend/dist/assets/index-CoIYj0ZD.css`
- `./strategy-service/frontend/dist/index.html`
- `./strategy-service/frontend/public/csv_data/demo_backtest_equity_curve.csv`
- `./strategy-service/frontend/src/App.tsx`
- `./strategy-service/frontend/src/main.live.tsx`
- `./strategy-service/frontend/src/main.tsx`
- `./strategy-service/frontend/src/services/liveMonitorService.ts`
- `./strategy-service/frontend/src/types/index.ts`
- `./strategy-service/frontend/src/utils/constants.ts`
- `./strategy-service/frontend/src/utils/formatters.ts`
- `./strategy-service/frontend/src/vite-env.d.ts`
- `./strategy-service/results/bt_1762243549771_588y3nvgn/config.json`
- `./strategy-service/results/bt_1762243549771_588y3nvgn/equity_curve.csv`
- `./strategy-service/results/bt_1762243549771_588y3nvgn/pnl_history.csv`
- `./strategy-service/results/bt_1762243583796_xaj1861pj/config.json`
- `./strategy-service/results/bt_1762243583796_xaj1861pj/equity_curve.csv`
- `./strategy-service/results/bt_1762243583796_xaj1861pj/pnl_history.csv`
- `./strategy-service/results/bt_1762243616286_63f9qv2is/config.json`
- `./strategy-service/results/bt_1762243616286_63f9qv2is/equity_curve.csv`
- `./strategy-service/results/bt_1762243616286_63f9qv2is/pnl_history.csv`
- `./strategy-service/results/bt_1762244289455_ildb6jfjl/config.json`
- `./strategy-service/results/bt_1762244289455_ildb6jfjl/equity_curve.csv`
- `./strategy-service/results/bt_1762244289455_ildb6jfjl/pnl_history.csv`
- `./strategy-service/results/bt_1762247821114_416kozqo2/config.json`
- `./strategy-service/results/bt_1762247821114_416kozqo2/equity_curve.csv`
- `./strategy-service/results/bt_1762247821114_416kozqo2/pnl_history.csv`
- `./strategy-service/results/test_backtest/equity_curve.csv`
- `./strategy-service/results/test_backtest/pnl_history.csv`
- `./strategy-service/results/test_csv_20251104_073957/equity_curve.csv`
- `./strategy-service/results/test_manual_20251104_073856/equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/charts/strategy_equity_curves.png`
- `./strategy-service/strategy_analysis_presentation/charts/strategy_roe_comparison.png`
- `./strategy-service/strategy_analysis_presentation/charts/strategy_roe_comparison_grouped.png`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/BTC_Basis_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/ETH_Basis_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/ETH_Leveraged_All_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/ETH_Leveraged_EIGEN_Only_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/ETH_Leveraged_No_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/ETH_Staking_Only_All_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/ETH_Staking_Only_EIGEN_Only_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/ETH_Staking_Only_No_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/Pure_Lending_ETH_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/Pure_Lending_USDT_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/USDT_ETH_Staking_Hedged_Leveraged_All_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/USDT_ETH_Staking_Hedged_Leveraged_EIGEN_Only_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/USDT_ETH_Staking_Hedged_Leveraged_No_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/USDT_ETH_Staking_Hedged_Simple_All_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/USDT_ETH_Staking_Hedged_Simple_EIGEN_Only_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/USDT_ETH_Staking_Hedged_Simple_No_Rewards_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/bt_1762243549771_588y3nvgn_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/bt_1762243583796_xaj1861pj_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/bt_1762243616286_63f9qv2is_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/bt_1762244289455_ildb6jfjl_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/bt_1762247821114_416kozqo2_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/test_csv_data_20251104_074255_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/csv_data/test_filter_20251104_075547_equity_curve.csv`
- `./strategy-service/strategy_analysis_presentation/code/strategy_equity_curves.png`
- `./strategy-service/strategy_analysis_presentation/code/strategy_roe_comparison.png`
- `./strategy-service/strategy_analysis_presentation/code/strategy_roe_comparison_grouped.png`
- `./strategy-service/strategy_analysis_presentation/documentation/TECHNICAL_METHODOLOGY.md`

### strategy-validation-service (9 corrupt)

**Files to remove (corrupt placeholders):**

- `./strategy-validation-service/.git/logs/refs/heads/main`
- `./strategy-validation-service/.git/objects/07/70b37811680f5f75ef2c01d39de1b0595c9fa5`
- `./strategy-validation-service/.git/objects/08/ed2bd369dbb43d9645d3f3b0ecab96adfc21d4`
- `./strategy-validation-service/.git/objects/26/fa9979e628230383561dc9b57488dbae92fc75`
- `./strategy-validation-service/.git/objects/42/78a191ed8550145c7c6d63eef45b86a221156a`
- `./strategy-validation-service/.git/objects/4b/c37972d046426f62720bfcb7a7bb0c15fe131b`
- `./strategy-validation-service/.git/objects/8f/a94dacb93bae8846d01096bd53254d9c21ed2b`
- `./strategy-validation-service/.git/objects/e8/5e0b04eabcdd7e86fe2be0f72fb1033f70c486`
- `./strategy-validation-service/.git/refs/heads/main`

### system-integration-tests (10 corrupt)

**Files to remove (corrupt placeholders):**

- `./system-integration-tests/.git/hooks/commit-msg.sample`
- `./system-integration-tests/.git/hooks/fsmonitor-watchman.sample`
- `./system-integration-tests/.git/hooks/post-update.sample`
- `./system-integration-tests/.git/hooks/pre-applypatch.sample`
- `./system-integration-tests/.git/hooks/pre-commit.sample`
- `./system-integration-tests/.git/hooks/pre-rebase.sample`
- `./system-integration-tests/.git/objects/64/485aeafa2ab1d4fbf6025d81b549e995084c0a`
- `./system-integration-tests/.git/objects/78/c5d76947535d2bbbcdcd3a9e8ae40d3191156c`
- `./system-integration-tests/.git/objects/89/554f0bd83bc35c999a5b816212998e58541e75`
- `./system-integration-tests/.git/refs/heads/main`

### trading-analytics-ui (10 corrupt)

**Files to remove (corrupt placeholders):**

- `./trading-analytics-ui/src/pages/OrderBook.tsx`
- `./trading-analytics-ui/test-results/.playwright-artifacts-0/10a3dad8918997d87198da7be0709267.png`
- `./trading-analytics-ui/test-results/.playwright-artifacts-0/1e651d50c5558d26104225408397b687.png`
- `./trading-analytics-ui/test-results/.playwright-artifacts-0/2aa6fbb3879959f1b1558d07b496f44d.png`
- `./trading-analytics-ui/test-results/.playwright-artifacts-0/6fff1b0986e26bb0e605e4b977ee7418.png`
- `./trading-analytics-ui/test-results/.playwright-artifacts-0/958a59045406093086c002e41e44d7e7.png`
- `./trading-analytics-ui/test-results/.playwright-artifacts-0/dc2326528abea526c7a6847b25c1fa94.png`
- `./trading-analytics-ui/tests/smoke/README.md`
- `./trading-analytics-ui/tests/smoke/home.spec.ts`
- `./trading-analytics-ui/tests/smoke/navigation.spec.ts`

### unified-sports-execution-interface (1 corrupt)

**Files to remove (corrupt placeholders):**

- `./unified-sports-execution-interface/tests/fixtures/html/coral_match_page.html`

### unified-trading-library (23 corrupt)

**Files to remove (corrupt placeholders):**

- `./unified-trading-library/.git/hooks/applypatch-msg.sample`
- `./unified-trading-library/.git/hooks/commit-msg.sample`
- `./unified-trading-library/.git/hooks/fsmonitor-watchman.sample`
- `./unified-trading-library/.git/hooks/post-update.sample`
- `./unified-trading-library/.git/hooks/pre-merge-commit.sample`
- `./unified-trading-library/.git/hooks/pre-push.sample`
- `./unified-trading-library/.git/hooks/pre-receive.sample`
- `./unified-trading-library/.git/hooks/prepare-commit-msg.sample`
- `./unified-trading-library/.git/hooks/push-to-checkout.sample`
- `./unified-trading-library/.git/hooks/update.sample`
- `./unified-trading-library/.git/info/refs`
- `./unified-trading-library/.git/objects/05/9a747ec5af63b33d156c0ded0bc1d80cdb527d`
- `./unified-trading-library/.git/objects/2d/1023de2b4dfaea55b5cf81387d0c2b7ce0ff44`
- `./unified-trading-library/.git/objects/4a/18fc52d84d05343c7c26c27d2b57e2d99aab96`
- `./unified-trading-library/.git/objects/51/0adf8f13b7874d77c7418462b67bcd230c65fd`
- `./unified-trading-library/.git/objects/89/e6b178c700fbc91ac1d3545c202deb5499d4d3`
- `./unified-trading-library/.git/objects/aa/6fd82bfb14e45f4c6518bacbc2537ddd92fa5c`
- `./unified-trading-library/.git/objects/ad/fc80158656fa63d6077e86be151ee0a8f63021`
- `./unified-trading-library/.git/objects/b7/a9132b9f87dae32cda87e96c612a239c5289e0`
- `./unified-trading-library/.git/objects/d7/af06c788d634b8556108415d6ab88ebfba6bfa`
- `./unified-trading-library/.git/objects/de/a2abbe31043b1202548270c968ed598c6c4570`
- `./unified-trading-library/.git/objects/info/commit-graph`
- `./unified-trading-library/.git/objects/pack/pack-f792af0636414c76d1c7cc5754a4cb6475c4682e.idx`

---

## CLEAN repos (ready for full copy to Code)

Zero corrupt files. Safe to copy iCloud → Code (exclude .gitignore/.cursorignore per need).

- **alerting-service**
- **batch-audit-ui**
- **client-reporting-api**
- **client-reporting-ui**
- **execution-results-api**
- **features-calendar-service**
- **features-multi-timeframe-service**
- **features-onchain-service**
- **features-sports-service**
- **ibkr-gateway-infra**
- **logs-dashboard-ui**
- **market-data-api**
- **ml-inference-service**
- **ml-training-service**
- **ml-training-ui**
- **onboarding-ui**
- **pnl-attribution-service**
- **position-balance-monitor-service**
- **risk-and-exposure-service**
- **strategy-ui**
- **unified-api-contracts**
- **unified-cloud-interface**
- **unified-config-interface**
- **unified-defi-execution-interface**
- **unified-domain-client**
- **unified-events-interface**
- **unified-feature-calculator-library**
- **unified-internal-contracts**
- **unified-market-interface**
- **unified-ml-interface**
- **unified-position-interface**
- **unified-reference-data-interface**
- **unified-trade-execution-interface**
- **unified-trading-codex**
- **unified-trading-deployment-v3**
- **unified-trading-ui-auth**

---

## Summary

- Total corrupt files: 818
- Repos with corrupt files: 18
- Clean repos (ready for copy): 36
- Symlinked (already at Code): 5

## Notable .git corruptions

Repos with corrupt `.git/*` (consider `git clone` fresh at Code, then copy working tree):

- unified-sports-execution-interface (1 file: fixture)
- features-delta-one-service (.git/\*)
- unified-trading-library (.git/\*)
- system-integration-tests (.git/\*)
- features-cross-instrument-service (.git/\*)
- features-volatility-service (.git/\*)
- strategy-validation-service (.git/\*)

onboarding-ui: listed in manifest, no corrupt files in scan (may be clean).
