---
doc_type: issue
title:
  Legacy no-env bucket-name TEMPLATE literals fleet-wide (15 unique / 21 occurrences) — the QG blind-spot class T1.2
  closed, baselined out-of-scope pending broader canonicalisation
summary:
  'T1.2 of the sports legacy bucket cutover extended `check_no_explicit_project_id_bucket.py` (QG STEP 5.72/5.93) to
  also flag module-level string-literal bucket TEMPLATES matching
  `^(instruments-store|market-data-tick|features)-[a-z]+-\{project_id\}$` — the exact blind spot that let
  deployment-service `data_status_sports.py` read the legacy `instruments-store-sports-{project_id}` bucket (the builder
  CALL check never saw the `.format()` template). Proving the tightened gate fleet-wide (autonomous rule 11) surfaced
  **21 pre-existing occurrences (15 unique file+literal keys)** in SSOT-registry / config-default / dependency-checker
  files, ALL for asset groups OUTSIDE this cutover''s delete scope: `features-onchain`, `features-calendar`,
  `features-store`, `features-sports` (the FEATURES bucket, not instruments-store/market-data-tick), and
  `instruments-store-tradfi`. None is `instruments-store-sports-{project_id}` or `market-data-tick-sports-{project_id}`
  (the two buckets THIS cutover deletes), so none blocks the cutover. Per the T1.2 ABORT branch (">5 pre-existing →
  baseline + file an issue doc, do not block the cutover on unrelated repos") they are frozen in
  `check_no_explicit_project_id_bucket_baseline.json` (a ratchet that only goes DOWN). This issue tracks paying them
  down as those asset groups reach their own legacy-bucket decommission.'
status: open
nature: issue
asset_group: [infrastructure]
stage: [data]
repos:
  [unified-trading-pm, unified-trading-library, deployment-service, features-service, execution-service, ml-service]
scope: [engineer]
tags: [bucket-canonicalisation, quality-gate, ratchet, baseline, tech-debt, gcs]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ../bucket_name_ssot_canonicalisation_2026_05_10.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
context_scope:
  [
    scripts/quality_gates/check_no_explicit_project_id_bucket.py,
    scripts/quality_gates/check_no_explicit_project_id_bucket_baseline.json,
    /plans/archive/2026_07/sports_legacy_bucket_cutover_2026_07_16.md,
    /plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md,
    /plans/epics/sports_master.md,
  ]
supersedes:
superseded_by:
resolved_by:
source: [sports legacy bucket cutover T1.2, fleet-wide QG proof 2026-07-16]
---

# Legacy no-env bucket-name TEMPLATE literals fleet-wide — 2026-07-16

## What T1.2 changed

`check_no_explicit_project_id_bucket.py` previously AST-matched only bucket-builder CALLS (`get_bucket_name(...)` /
`get_write_bucket_name(...)`) carrying an explicit `project_id`. A module-level string-literal template like
`_SPORTS_BUCKET_TEMPLATE = "instruments-store-sports-{project_id}"` followed by `.format(project_id=...)` matches
**neither** — it silently reconstructs the legacy no-env bucket that is DELETED at cutover. That was the live blind spot
behind the deployment-service `data_status_sports.py` legacy read (T1.1).

The gate now additionally flags any `ast.Constant` string whose value matches
`^(instruments-store|market-data-tick|features)-[a-z]+-\{project_id\}$` (outside `scripts/`/`tests/`/migration trees;
inline `# QG-allow: reading-legacy-bucket-for-migration` bypass preserved). The env-tiered canonical form carries an env
segment (`…-sports-prd-{project_id}`) whose `-prd-` makes it NOT match — verified.

## Fleet-wide proof (autonomous rule 11)

Run against every repo, the tightened gate surfaced **21 occurrences / 15 unique (file, literal) keys**. Because `>5`
pre-existing surfaced, per the T1.2 ABORT branch they are baselined (not fixed in this cutover) and tracked here. **None
is in this cutover's delete scope** (`instruments-store-sports` / `market-data-tick-sports`).

| File                                                                       | Literal                                 | In cutover delete scope?                              |
| -------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| `deployment-service/deployment_service/catalog.py`                         | `features-calendar-{project_id}`        | no                                                    |
| `deployment-service/deployment_service/catalog.py`                         | `features-onchain-{project_id}`         | no                                                    |
| `deployment-service/deployment_service/cli/utils/manifest_reader.py`       | `features-calendar-{project_id}`        | no                                                    |
| `deployment-service/deployment_service/cli/utils/manifest_reader.py`       | `features-onchain-{project_id}`         | no                                                    |
| `execution-service/execution_service/utils/dependency_checker.py`          | `features-onchain-{project_id}`         | no                                                    |
| `features-service/features_service/onchain/app/core/dependency_checker.py` | `features-onchain-{project_id}` (×3)    | no                                                    |
| `ml-service/ml_service/inference/config.py`                                | `features-store-{project_id}`           | no                                                    |
| `ml-service/ml_service/training/config.py`                                 | `features-onchain-{project_id}`         | no                                                    |
| `ml-service/ml_service/training/config.py`                                 | `features-sports-{project_id}`          | no (features-sports ≠ instruments/market-data sports) |
| `ml-service/ml_service/training/app/core/dependency_checker.py`            | `features-onchain-{project_id}`         | no                                                    |
| `unified-trading-library/.../config_interface/ml_config.py`                | `features-store-{project_id}`           | no                                                    |
| `unified-trading-library/.../config_interface/paths/registry.py`           | `instruments-store-tradfi-{project_id}` | no                                                    |
| `unified-trading-library/.../config_interface/paths/registry.py`           | `features-calendar-{project_id}`        | no                                                    |
| `unified-trading-library/.../config_interface/paths/registry.py`           | `features-onchain-{project_id}` (×2)    | no                                                    |
| `unified-trading-library/.../config_interface/paths/registry.py`           | `features-sports-{project_id}` (×4)     | no                                                    |

## Disposition

- **Baselined** in `unified-trading-pm/scripts/quality_gates/check_no_explicit_project_id_bucket_baseline.json` — a
  frozen ratchet keyed on `(repo/file, literal)`. New occurrences (incl. any reintroduced
  `instruments-store-sports-{project_id}`) fail the gate; the baselined set only shrinks.
- **Pay-down**: as each asset group (`features-onchain`, `features-calendar`, `features-store`, `features-sports`,
  `instruments-store-tradfi`) reaches its own legacy-bucket decommission, route these through `resolve_bucket_name(...)`
  and delete the corresponding baseline entry. `registry.py` `DataSetSpec.bucket_template=` is the highest-value target
  (it is the shared fallback registry — analogous to the already-excluded `cloud_constants.py`/`bucket_naming.py` SSOT
  plumbing, so it may instead warrant a same-class exclusion decision at that time).

## Verification snapshot (2026-07-16)

- current tree fleet-wide → `OK — 0 non-baselined occurrences (21 pre-existing suppressed)`.
- injected reverted-T1.1 literal (`instruments-store-sports-{project_id}` / `market-data-tick-sports-{project_id}`) →
  `FAIL — 2 non-baselined`.
- canonical `-prd-` form (`instruments-store-sports-prd-{project_id}`) → not flagged.

## Todos

- [ ] [INFRA] P2. **Pay down the 15 baselined legacy bucket-name TEMPLATE literals** (features-onchain/calendar/
      store/sports + instruments-store-tradfi) — route each through `resolve_bucket_name(...)` and remove its baseline
      entry as that asset group reaches its own legacy-bucket decommission; none has been paid down yet.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Sole todo is explicitly
  timing-gated by the doc's own Disposition section on other asset groups' own legacy-bucket decommission timing, not
  yet reached.
