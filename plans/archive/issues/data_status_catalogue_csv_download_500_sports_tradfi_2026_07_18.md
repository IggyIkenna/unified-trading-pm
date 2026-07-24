---
doc_type: issue
title: "data-status /download-catalogue-csv returns HTTP 500 for sports + tradfi (large-catalogue build error)"
summary:
  Surfaced 2026-07-18 by the Phase-E CSV-download smoke (data_status_tab_and_downloads_remediation). The deployment-api
  catalogue-CSV download works (HTTP 200, real CSV) for defi / cefi / prediction and for MTDS/defi, but returns HTTP 500
  ("Internal server error. Check server logs.") for asset_group=sports and asset_group=tradfi on instruments-service.
  The DeFi 502 path-drift the plan's §A fix targeted does NOT reproduce; the remaining break is sports+tradfi.
status: resolved
nature: issue
asset_group: [sports, tradfi]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [data-status, downloads, csv, deployment-api, sports, tradfi, 500]
related: [/plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md]
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
resolved_by: deployment-api@65f5593
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

- [x] [BACKEND] P2. ✅ Reproduce `_build_catalogue_rows(service="instruments-service", asset_group="sports")` locally
      against the real sports catalogue to capture the un-truncated exception; same for tradfi. — **There is no
      exception.** Measured live 2026-07-20 against the real prod catalogues (ADC, `central-element-323112`): **tradfi**
      `_build_catalogue_rows` SUCCEEDS — 1,060,790 rows (from a 1,391,725-row `prod/catalog.parquet`) → **70,683,707
      bytes (67.41 MiB)** CSV, build 39.7s, no raise; **sports** SUCCEEDS — 5,363 rows → 618,299 bytes (0.59 MiB), build
      34.4s, no raise. The `_catalogue.py:566` traceback pointer in the original report was a red herring.
- [x] [BACKEND] P2. ✅ Fix the sports/tradfi-specific failure so both return 200 + real CSV; add a per-asset_group
      download smoke regression. — deployment-api@65f5593. **Two distinct causes, one symptom:** (1) **tradfi = a real
      bug** — the endpoint built the whole CSV with `DataFrame.to_csv()` and returned it as ONE buffered `Response`; at
      67.41 MiB that exceeds Cloud Run's ~32 MiB (33,554,432 b) BUFFERED-response cap, so the PLATFORM rejected it
      before it reached the client (no Python traceback anywhere). cefi (32,879,539 b) narrowly fits today — the same
      latent bug, not yet tripped. Fixed at the root by emitting a genuinely CHUNKED `StreamingResponse` over bounded
      5,000-row batches (`_iter_catalogue_csv_chunks`), byte-identical to the old `to_csv()` output; no blanket
      try/except. (2) **sports = NOT a code bug** — a transient manifest-consolidator staleness (`RuntimeError`) at
      smoke time; it returns 200 on re-measure. The existing honest-absence guard correctly surfaces a genuine manifest
      read failure as 500 rather than fabricating an empty CSV, and is deliberately preserved. **Regressions**
      (`deployment-api/tests/unit/test_route_data_status_catalogue.py`): `TestDownloadCatalogueCsvPerAssetGroupSmoke`
      (per-asset_group 200 + well-formed rows for cefi/defi/tradfi/prediction/sports, + the
      sports-read-failure-still-500 honesty guard) and `TestDownloadCatalogueCsvStreamingBoundaries` (chunk-boundary
      byte-equivalence vs the pre-fix buffered reference at 0 / 1 / batch-1 / batch / batch+1 / 2·batch+7 rows, + a
      `StreamingResponse`-identity assertion so a regression back to a buffered `Response` fails loudly).

## Progress Log

- **2026-07-18** — Filed from the Phase-E CSV-download smoke in
  `data_status_tab_and_downloads_remediation_2026_06_16.md` (which confirmed the DeFi 502 path-drift is resolved; this
  sports+tradfi 500 is a separate, newly-surfaced break).
- **2026-07-20** — RESOLVED, deployment-api@65f5593. Root-caused live against the real prod catalogues (not from the
  truncated Cloud Logging traceback, which pointed at the wrong place). The row builder never raised for either asset
  group: **tradfi** was a genuine Cloud Run **buffered-response-size** rejection (67.41 MiB > ~32 MiB cap) — fixed by
  streaming the CSV in bounded chunks; **sports** was a transient manifest-consolidator staleness that no longer
  reproduces, and whose 500 is the CORRECT honest-absence behaviour (kept). cefi was found to be **one 0.7 MiB step away
  from the same cliff** (32.88 MiB vs the 32 MiB cap) — the streaming fix removes that class of failure for every
  asset_group, not just tradfi. Regression coverage added per asset_group + at the streaming chunk boundaries.
