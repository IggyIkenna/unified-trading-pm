---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2025-12-20)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2025-12-20: total=117 passed=0 failed=81 ambiguous=0 skipped=36"
status: fail
nature: record
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-08-21
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2025-12-20, legs=force,skip,canonical"
date: 2026-08-21
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2025-12-20
generated_at: 2026-08-21T00:09:10.505327+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2025-12-20)

**Legs:** force, skip, canonical  
**Started:** 2026-08-20T23:40:32.443520+00:00  **Finished:** 2026-08-21T00:09:10.450368+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2025-12-20: total=117 passed=0 failed=81 ambiguous=0 skipped=36

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:3ET:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:3ET:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:3ET:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BET888SPORT:odds | force | failed | not_applicable | - | 0 | - | not_checked | leg_raised:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BET888SPORT:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | leg_raised:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BET888SPORT:odds | skip | failed | not_applicable | - | 0 | - | not_checked | leg_raised:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETDEX:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BETDEX:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BETDEX:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BETFAIR_EX_EU:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_EU:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_EU:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_UK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_UK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_UK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_SB_UK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_SB_UK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_SB_UK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETMGM:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETMGM:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETMGM:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETONLINEAG:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETONLINEAG:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETONLINEAG:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETOPENLY:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BETOPENLY:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BETOPENLY:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BETRIVERS:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETRIVERS:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETRIVERS:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETSSON:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETSSON:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETSSON:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETVICTOR:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETVICTOR:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETVICTOR:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETWAY:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETWAY:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETWAY:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BOVADA:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BOVADA:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BOVADA:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BROKER5:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BROKER5:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:BROKER5:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:CASUMO:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CASUMO:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CASUMO:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CORAL:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CORAL:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CORAL:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CROWN:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:CROWN:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:CROWN:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:DRAFTKINGS:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:DRAFTKINGS:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:DRAFTKINGS:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:FANDUEL:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:FANDUEL:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:FANDUEL:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:IBC:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:IBC:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:IBC:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:LADBROKES:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LADBROKES:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LADBROKES:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LIVESCOREBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LIVESCOREBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LIVESCOREBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:MATCHBOOK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:MATCHBOOK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:MATCHBOOK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:NOVIG:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:NOVIG:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:NOVIG:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:ONEXBET:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:ONEXBET:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:ONEXBET:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:PADDYPOWER:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PADDYPOWER:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PADDYPOWER:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PINNACLE:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PINNACLE:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PINNACLE:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PROPHETX:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:PROPHETX:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:PROPHETX:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:SBO:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:SBO:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:SBO:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:SHARPBET:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:SHARPBET:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:SHARPBET:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:SKYBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SKYBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SKYBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SMARKETS:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SMARKETS:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SMARKETS:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_EU:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_EU:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_EU:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_UK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_UK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_UK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:VIRGINBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:VIRGINBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:VIRGINBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:VX:odds | force | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:VX:odds | skip | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:VX:odds | canonical | skipped | not_applicable | - | 0 | - | not_checked | no_captured_data_for_cell |
| SPORTS:WILLIAMHILL:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:WILLIAMHILL:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:WILLIAMHILL:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| SPORTS:3ET:odds | force | `-` | `-` | - |
| SPORTS:3ET:odds | skip | `-` | `-` | - |
| SPORTS:3ET:odds | canonical | `-` | `-` | - |
| SPORTS:BET888SPORT:odds | force | `-` | `-` | - |
| SPORTS:BET888SPORT:odds | canonical | `-` | `-` | - |
| SPORTS:BET888SPORT:odds | skip | `-` | `-` | - |
| SPORTS:BETDEX:odds | force | `-` | `-` | - |
| SPORTS:BETDEX:odds | skip | `-` | `-` | - |
| SPORTS:BETDEX:odds | canonical | `-` | `-` | - |
| SPORTS:BETFAIR_EX_EU:odds | force | `-` | `-` | - |
| SPORTS:BETFAIR_EX_EU:odds | canonical | `-` | `-` | - |
| SPORTS:BETFAIR_EX_EU:odds | skip | `-` | `-` | - |
| SPORTS:BETFAIR_EX_UK:odds | force | `-` | `-` | - |
| SPORTS:BETFAIR_EX_UK:odds | canonical | `-` | `-` | - |
| SPORTS:BETFAIR_EX_UK:odds | skip | `-` | `-` | - |
| SPORTS:BETFAIR_SB_UK:odds | force | `-` | `-` | - |
| SPORTS:BETFAIR_SB_UK:odds | skip | `-` | `-` | - |
| SPORTS:BETFAIR_SB_UK:odds | canonical | `-` | `-` | - |
| SPORTS:BETMGM:odds | force | `-` | `-` | - |
| SPORTS:BETMGM:odds | skip | `-` | `-` | - |
| SPORTS:BETMGM:odds | canonical | `-` | `-` | - |
| SPORTS:BETONLINEAG:odds | force | `-` | `-` | - |
| SPORTS:BETONLINEAG:odds | skip | `-` | `-` | - |
| SPORTS:BETONLINEAG:odds | canonical | `-` | `-` | - |
| SPORTS:BETOPENLY:odds | force | `-` | `-` | - |
| SPORTS:BETOPENLY:odds | skip | `-` | `-` | - |
| SPORTS:BETOPENLY:odds | canonical | `-` | `-` | - |
| SPORTS:BETRIVERS:odds | force | `-` | `-` | - |
| SPORTS:BETRIVERS:odds | skip | `-` | `-` | - |
| SPORTS:BETRIVERS:odds | canonical | `-` | `-` | - |
| SPORTS:BETSSON:odds | force | `-` | `-` | - |
| SPORTS:BETSSON:odds | skip | `-` | `-` | - |
| SPORTS:BETSSON:odds | canonical | `-` | `-` | - |
| SPORTS:BETVICTOR:odds | force | `-` | `-` | - |
| SPORTS:BETVICTOR:odds | skip | `-` | `-` | - |
| SPORTS:BETVICTOR:odds | canonical | `-` | `-` | - |
| SPORTS:BETWAY:odds | force | `-` | `-` | - |
| SPORTS:BETWAY:odds | skip | `-` | `-` | - |
| SPORTS:BETWAY:odds | canonical | `-` | `-` | - |
| SPORTS:BOVADA:odds | force | `-` | `-` | - |
| SPORTS:BOVADA:odds | skip | `-` | `-` | - |
| SPORTS:BOVADA:odds | canonical | `-` | `-` | - |
| SPORTS:BROKER5:odds | force | `-` | `-` | - |
| SPORTS:BROKER5:odds | skip | `-` | `-` | - |
| SPORTS:BROKER5:odds | canonical | `-` | `-` | - |
| SPORTS:CASUMO:odds | force | `-` | `-` | - |
| SPORTS:CASUMO:odds | skip | `-` | `-` | - |
| SPORTS:CASUMO:odds | canonical | `-` | `-` | - |
| SPORTS:CORAL:odds | force | `-` | `-` | - |
| SPORTS:CORAL:odds | skip | `-` | `-` | - |
| SPORTS:CORAL:odds | canonical | `-` | `-` | - |
| SPORTS:CROWN:odds | force | `-` | `-` | - |
| SPORTS:CROWN:odds | skip | `-` | `-` | - |
| SPORTS:CROWN:odds | canonical | `-` | `-` | - |
| SPORTS:DRAFTKINGS:odds | force | `-` | `-` | - |
| SPORTS:DRAFTKINGS:odds | skip | `-` | `-` | - |
| SPORTS:DRAFTKINGS:odds | canonical | `-` | `-` | - |
| SPORTS:FANDUEL:odds | force | `-` | `-` | - |
| SPORTS:FANDUEL:odds | skip | `-` | `-` | - |
| SPORTS:FANDUEL:odds | canonical | `-` | `-` | - |
| SPORTS:IBC:odds | force | `-` | `-` | - |
| SPORTS:IBC:odds | skip | `-` | `-` | - |
| SPORTS:IBC:odds | canonical | `-` | `-` | - |
| SPORTS:LADBROKES:odds | force | `-` | `-` | - |
| SPORTS:LADBROKES:odds | skip | `-` | `-` | - |
| SPORTS:LADBROKES:odds | canonical | `-` | `-` | - |
| SPORTS:LIVESCOREBET:odds | force | `-` | `-` | - |
| SPORTS:LIVESCOREBET:odds | skip | `-` | `-` | - |
| SPORTS:LIVESCOREBET:odds | canonical | `-` | `-` | - |
| SPORTS:MATCHBOOK:odds | force | `-` | `-` | - |
| SPORTS:MATCHBOOK:odds | skip | `-` | `-` | - |
| SPORTS:MATCHBOOK:odds | canonical | `-` | `-` | - |
| SPORTS:NOVIG:odds | force | `-` | `-` | - |
| SPORTS:NOVIG:odds | skip | `-` | `-` | - |
| SPORTS:NOVIG:odds | canonical | `-` | `-` | - |
| SPORTS:ONEXBET:odds | force | `-` | `-` | - |
| SPORTS:ONEXBET:odds | skip | `-` | `-` | - |
| SPORTS:ONEXBET:odds | canonical | `-` | `-` | - |
| SPORTS:PADDYPOWER:odds | force | `-` | `-` | - |
| SPORTS:PADDYPOWER:odds | skip | `-` | `-` | - |
| SPORTS:PADDYPOWER:odds | canonical | `-` | `-` | - |
| SPORTS:PINNACLE:odds | force | `-` | `-` | - |
| SPORTS:PINNACLE:odds | skip | `-` | `-` | - |
| SPORTS:PINNACLE:odds | canonical | `-` | `-` | - |
| SPORTS:PROPHETX:odds | force | `-` | `-` | - |
| SPORTS:PROPHETX:odds | skip | `-` | `-` | - |
| SPORTS:PROPHETX:odds | canonical | `-` | `-` | - |
| SPORTS:SBO:odds | force | `-` | `-` | - |
| SPORTS:SBO:odds | skip | `-` | `-` | - |
| SPORTS:SBO:odds | canonical | `-` | `-` | - |
| SPORTS:SHARPBET:odds | force | `-` | `-` | - |
| SPORTS:SHARPBET:odds | skip | `-` | `-` | - |
| SPORTS:SHARPBET:odds | canonical | `-` | `-` | - |
| SPORTS:SKYBET:odds | force | `-` | `-` | - |
| SPORTS:SKYBET:odds | skip | `-` | `-` | - |
| SPORTS:SKYBET:odds | canonical | `-` | `-` | - |
| SPORTS:SMARKETS:odds | force | `-` | `-` | - |
| SPORTS:SMARKETS:odds | skip | `-` | `-` | - |
| SPORTS:SMARKETS:odds | canonical | `-` | `-` | - |
| SPORTS:UNIBET:odds | force | `-` | `-` | - |
| SPORTS:UNIBET:odds | skip | `-` | `-` | - |
| SPORTS:UNIBET:odds | canonical | `-` | `-` | - |
| SPORTS:UNIBET_EU:odds | force | `-` | `-` | - |
| SPORTS:UNIBET_EU:odds | skip | `-` | `-` | - |
| SPORTS:UNIBET_EU:odds | canonical | `-` | `-` | - |
| SPORTS:UNIBET_UK:odds | force | `-` | `-` | - |
| SPORTS:UNIBET_UK:odds | skip | `-` | `-` | - |
| SPORTS:UNIBET_UK:odds | canonical | `-` | `-` | - |
| SPORTS:VIRGINBET:odds | force | `-` | `-` | - |
| SPORTS:VIRGINBET:odds | skip | `-` | `-` | - |
| SPORTS:VIRGINBET:odds | canonical | `-` | `-` | - |
| SPORTS:VX:odds | force | `-` | `-` | - |
| SPORTS:VX:odds | skip | `-` | `-` | - |
| SPORTS:VX:odds | canonical | `-` | `-` | - |
| SPORTS:WILLIAMHILL:odds | force | `-` | `-` | - |
| SPORTS:WILLIAMHILL:odds | skip | `-` | `-` | - |
| SPORTS:WILLIAMHILL:odds | canonical | `-` | `-` | - |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:BET888SPORT:odds | force | failed | not_applicable | - | 0 | - | not_checked | leg_raised:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BET888SPORT:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | leg_raised:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BET888SPORT:odds | skip | failed | not_applicable | - | 0 | - | not_checked | leg_raised:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_EU:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_EU:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_EU:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_UK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_UK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_EX_UK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_SB_UK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_SB_UK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETFAIR_SB_UK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETMGM:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETMGM:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETMGM:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETONLINEAG:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETONLINEAG:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETONLINEAG:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETRIVERS:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETRIVERS:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETRIVERS:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETSSON:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETSSON:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETSSON:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETVICTOR:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETVICTOR:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETVICTOR:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETWAY:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETWAY:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BETWAY:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BOVADA:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BOVADA:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:BOVADA:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CASUMO:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CASUMO:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CASUMO:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CORAL:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CORAL:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:CORAL:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:DRAFTKINGS:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:DRAFTKINGS:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:DRAFTKINGS:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:FANDUEL:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:FANDUEL:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:FANDUEL:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LADBROKES:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LADBROKES:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LADBROKES:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LIVESCOREBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LIVESCOREBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:LIVESCOREBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:MATCHBOOK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:MATCHBOOK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:MATCHBOOK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PADDYPOWER:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PADDYPOWER:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PADDYPOWER:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PINNACLE:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PINNACLE:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:PINNACLE:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SKYBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SKYBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SKYBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SMARKETS:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SMARKETS:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:SMARKETS:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_EU:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_EU:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_EU:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_UK:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_UK:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:UNIBET_UK:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:VIRGINBET:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:VIRGINBET:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:VIRGINBET:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:WILLIAMHILL:odds | force | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:WILLIAMHILL:odds | skip | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |
| SPORTS:WILLIAMHILL:odds | canonical | failed | not_applicable | - | 0 | - | not_checked | sample_live_instrument_error:OSError:Could not find a suitable TLS CA certificate bundle, invalid path: /home/ubuntu/unified-trading-system-repos/.tabs/19/market-tick-data-service/.venv/lib/python3.13/site-packages/certifi/cacert.pem |

