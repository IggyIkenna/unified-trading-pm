---
doc_type: audit-result
title: A3 v2 — Manifest divergence across ALL services (GCP + AWS)
summary:
  A3 v2 manifest-index presence + v8 compliance across 27 GCS + 7 AWS buckets (MTDS/IS/features/strategy/execution/ml) —
  0% v8 rows in every bucket with data; 9 GCS service buckets ERROR (no consolidated index); AWS side 2 exist-with-index
  vs 5 missing, prompting R21 operator decision on AWS S3 index maintenance.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [audit, manifest, single-walk, data-correctness, migration, data-status]
related:
  [
    /plans/audit/results/archive/manifest_divergence_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_v8_compliance_2026_05_20_summary.md,
    /plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md,
  ]
created: 2026-05-20
audited_scope:
  27 GCS + 7 AWS buckets across 6 service kinds (MTDS, instruments, features-*, strategy, execution, ml) — manifest
  index presence, row/schema_version distribution, capture_status breakdown, v8 compliance %
date: 2026-05-20
auditor: semver
parent_epic: manifest_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# A3 v2 — Manifest divergence across ALL services (GCP + AWS)

_Generated: 2026-05-20T12:35:08.236245+00:00_

GCS buckets probed: 27 AWS buckets probed: 7

## GCS bucket inventory + manifest index presence

| asset_group | service_kind        | bucket                                                | index? |      rows |  v8 |       v<8 |    NULL |  captured |     empty |    failed |
| ----------- | ------------------- | ----------------------------------------------------- | ------ | --------: | --: | --------: | ------: | --------: | --------: | --------: |
| cefi        | mtds                | `market-data-tick-cefi-prd-central-element-323112`    | OK     | 2,626,157 |   0 | 2,626,157 |       0 | 1,301,853 |     3,296 | 1,321,008 |
| defi        | mtds                | `market-data-tick-defi-prd-central-element-323112`    | OK     | 1,036,790 |   0 |   319,930 | 716,860 |   312,731 |   723,771 |       288 |
| tradfi      | mtds                | `market-data-tick-tradfi-prd-central-element-323112`  | OK     |   133,081 |   0 |   106,368 |  26,713 |    98,573 |    29,157 |     5,351 |
| sports      | mtds                | `market-data-tick-sports-prd-central-element-323112`  | OK     |   157,500 |   0 |   157,500 |       0 |   157,174 |       326 |         0 |
| prediction  | mtds                | `market-data-tick-pred-prd-central-element-323112`    | OK     |    15,352 |   0 |    14,532 |     820 |    14,491 |       861 |         0 |
| cefi        | instruments         | `instruments-store-cefi-prd-central-element-323112`   | OK     |    29,822 |   0 |    29,822 |       0 |    17,698 |         0 |         0 |
| defi        | instruments         | `instruments-store-defi-prd-central-element-323112`   | OK     |   127,896 |   0 |   127,896 |       0 |    70,430 |         0 |         0 |
| tradfi      | instruments         | `instruments-store-tradfi-prd-central-element-323112` | OK     |    20,198 |   0 |    20,198 |       0 |     8,897 |         0 |         0 |
| sports      | instruments         | `instruments-store-sports-prd-central-element-323112` | OK     | 2,130,028 |   0 | 2,128,772 |   1,256 |   498,533 | 1,559,875 |    65,125 |
| prediction  | instruments         | `instruments-store-pred-prd-central-element-323112`   | OK     |     3,799 |   0 |     3,799 |       0 |       795 |         0 |         0 |
| cefi        | features-delta-one  | `features-delta-one-cefi-central-element-323112`      | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| defi        | features-delta-one  | `features-delta-one-defi-central-element-323112`      | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| tradfi      | features-delta-one  | `features-delta-one-tradfi-central-element-323112`    | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| sports      | features-delta-one  | `features-delta-one-sports-central-element-323112`    | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| cefi        | features-volatility | `features-volatility-cefi-central-element-323112`     | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| defi        | features-volatility | `features-volatility-defi-central-element-323112`     | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| defi        | features-onchain    | `features-onchain-defi-central-element-323112`        | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| sports      | features-sports     | `features-sports-prd-central-element-323112`          | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| shared      | features-calendar   | `features-calendar-prd-central-element-323112`        | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| cefi        | strategy            | `strategy-store-cefi-central-element-323112`          | OK     |         7 |   0 |         7 |       0 |         0 |         0 |         0 |
| defi        | strategy            | `strategy-store-defi-central-element-323112`          | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| tradfi      | strategy            | `strategy-store-tradfi-central-element-323112`        | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| cefi        | execution           | `execution-store-cefi-central-element-323112`         | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| defi        | execution           | `execution-store-defi-central-element-323112`         | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| tradfi      | execution           | `execution-store-tradfi-central-element-323112`       | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| shared      | ml-artifacts        | `ml-artifacts-central-element-323112`                 | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |
| shared      | ml-training         | `ml-training-artifacts-central-element-323112`        | ERROR  |         0 |   0 |         0 |       0 |         0 |         0 |         0 |

## Services without consolidated manifest (review-blocking — they emit but have no index)

_All probed buckets have a consolidated manifest._

## v8 schema-version compliance (extends A4)

| asset_group | service_kind | bucket                                                |     total |  v8 % |  v<8 rows | NULL rows |
| ----------- | ------------ | ----------------------------------------------------- | --------: | ----: | --------: | --------: |
| cefi        | mtds         | `market-data-tick-cefi-prd-central-element-323112`    | 2,626,157 | 0.00% | 2,626,157 |         0 |
| defi        | mtds         | `market-data-tick-defi-prd-central-element-323112`    | 1,036,790 | 0.00% |   319,930 |   716,860 |
| tradfi      | mtds         | `market-data-tick-tradfi-prd-central-element-323112`  |   133,081 | 0.00% |   106,368 |    26,713 |
| sports      | mtds         | `market-data-tick-sports-prd-central-element-323112`  |   157,500 | 0.00% |   157,500 |         0 |
| prediction  | mtds         | `market-data-tick-pred-prd-central-element-323112`    |    15,352 | 0.00% |    14,532 |       820 |
| cefi        | instruments  | `instruments-store-cefi-prd-central-element-323112`   |    29,822 | 0.00% |    29,822 |         0 |
| defi        | instruments  | `instruments-store-defi-prd-central-element-323112`   |   127,896 | 0.00% |   127,896 |         0 |
| tradfi      | instruments  | `instruments-store-tradfi-prd-central-element-323112` |    20,198 | 0.00% |    20,198 |         0 |
| sports      | instruments  | `instruments-store-sports-prd-central-element-323112` | 2,130,028 | 0.00% | 2,128,772 |     1,256 |
| prediction  | instruments  | `instruments-store-pred-prd-central-element-323112`   |     3,799 | 0.00% |     3,799 |         0 |
| cefi        | strategy     | `strategy-store-cefi-central-element-323112`          |         7 | 0.00% |         7 |         0 |

## AWS-side manifest index presence

| asset_group | service_kind  | bucket                                               | status            |
| ----------- | ------------- | ---------------------------------------------------- | ----------------- |
| cefi        | mtds-aws      | `unified-trading-market-data-cefi-427895769566`      | MISSING:          |
| defi        | mtds-aws      | `unified-trading-market-data-defi-427895769566`      | EXISTS_WITH_INDEX |
| tradfi      | mtds-aws      | `unified-trading-market-data-tradfi-427895769566`    | MISSING:          |
| defi        | evm-defi-aws  | `unified-trading-evm-defi-prd-427895769566`          | EXISTS_WITH_INDEX |
| cefi        | execution-aws | `unified-trading-execution-cefi-prod-427895769566`   | MISSING:          |
| defi        | execution-aws | `unified-trading-execution-defi-prod-427895769566`   | MISSING:          |
| tradfi      | execution-aws | `unified-trading-execution-tradfi-prod-427895769566` | MISSING:          |

**Operator decision needed** (R21 in audit doc): are AWS S3 manifest indexes still actively maintained, or deprecated in
favour of GCP? Either:

- If active: wire consolidator + extend A3 to read them per-cell (current A3 only reads GCS).
- If deprecated: archive AWS section of `cloud-providers.yaml` + remove from bucket-name SSOT.
