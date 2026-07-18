---
doc_type: issue
title: "data-status /download-catalogue-csv returns HTTP 500 for sports + tradfi (large-catalogue build error)"
summary:
  Surfaced 2026-07-18 by the Phase-E CSV-download smoke (data_status_tab_and_downloads_remediation). The deployment-api
  catalogue-CSV download works (HTTP 200, real CSV) for defi / cefi / prediction and for MTDS/defi, but returns HTTP 500
  ("Internal server error. Check server logs.") for asset_group=sports and asset_group=tradfi on instruments-service.
  The DeFi 502 path-drift the plan's §A fix targeted does NOT reproduce; the remaining break is sports+tradfi.
status: open
nature: issue
asset_group: [sports, tradfi]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [data-status, downloads, csv, deployment-api, sports, tradfi, 500]
related: [data_status_tab_and_downloads_remediation_2026_06_16.md]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: "Phase-E CSV-download smoke 2026-07-18 (data_status_tab_and_downloads_remediation_2026_06_16.md)"
---

## What I found (2026-07-18 CSV-download smoke)

Prod
`https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app/api/data-status/download-catalogue-csv?service=…&asset_group=…`
(unauth reads work). HTTP code + bytes per asset_group:

| service / asset_group            | result                                                                   |
| -------------------------------- | ------------------------------------------------------------------------ |
| instruments-service / defi       | **200** text/csv (941,845 b) ✅                                          |
| instruments-service / cefi       | **200** text/csv (32,879,539 b) ✅                                       |
| instruments-service / prediction | **200** text/csv ✅                                                      |
| market-tick-data-service / defi  | **200** text/csv ✅ (the 502-prone chain/protocol path WORKS — no drift) |
| **instruments-service / sports** | **500** application/json ⚠️                                              |
| **instruments-service / tradfi** | **500** ⚠️                                                               |

Error body:
`{"error":{"code":"HTTP_500","message":"Internal server error. Check server logs."},"request_id":"bee0103f-…"}`.

## Root-cause pointer (from Cloud Run logs)

Traceback in `deployment-api/deployment_api/routes/data_status/_catalogue.py:566` → `_build_catalogue_rows(...)` inside
`download_catalogue_csv` (caught by the `except (OSError, RuntimeError, ValueError)` → 500). The multi-line traceback is
truncated in Cloud Logging (only the first 2 frames survive), so the exact exception is not yet captured.
`_build_catalogue_rows` is the shared builder for both `/catalogue` and `/download-catalogue-csv`, so `/catalogue` for
sports/tradfi likely fails identically. Likely a sports/tradfi-specific catalogue-shape assumption in the row builder
(sports keys on `(data_type, league_id)`; tradfi has its own shape), or a build-time OOM/timeout on the largest
catalogues — needs the full un-truncated traceback (reproduce locally against the sports/tradfi `prod/catalog.parquet`,
or read the request-id log with full payload).

## Todos

- [ ] [BACKEND] P2. Reproduce `_build_catalogue_rows(service="instruments-service", asset_group="sports")` locally
      against the real sports catalogue to capture the un-truncated exception; same for tradfi.
- [ ] [BACKEND] P2. Fix the sports/tradfi-specific failure in `_catalogue.py::_build_catalogue_rows` (or the CSV
      serialization) so both return 200 + real CSV; add a per-asset_group download smoke regression.

## Progress Log

- **2026-07-18** — Filed from the Phase-E CSV-download smoke in
  `data_status_tab_and_downloads_remediation_2026_06_16.md` (which confirmed the DeFi 502 path-drift is resolved; this
  sports+tradfi 500 is a separate, newly-surfaced break).
