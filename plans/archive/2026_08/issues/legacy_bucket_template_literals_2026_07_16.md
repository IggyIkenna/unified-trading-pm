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
status: complete
nature: issue
asset_group: [infrastructure]
stage: [data]
repos:
  [unified-trading-pm, unified-trading-library, deployment-service, features-service, execution-service, ml-service]
scope: [engineer]
tags: [bucket-canonicalisation, quality-gate, ratchet, baseline, tech-debt, gcs, round-9-reclassify]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ../bucket_name_ssot_canonicalisation_2026_05_10.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
author: unknown
last_updated: 2026-08-09
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
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

> **🟢 ARCHIVED 2026-08-09** — sole todo `[x]`, `locked_by:` empty. All 15 baselined (file, literal) keys resolved (9
> genuine code fixes routing through `resolve_bucket_name(...)` or deleting dead code, 6 already fixed by unrelated fold
> migrations, baseline-JSON-only). Baseline emptied to `"allow": []`; `check_no_explicit_project_id_bucket.py` passes
> clean with 0 non-baselined occurrences fleet-wide. See the todo's Shipped line for per-repo SHAs.

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

- [x] ✅ [INFRA] P2. **Pay down the 15 baselined legacy bucket-name TEMPLATE literals** (features-onchain/calendar/
      store/sports + instruments-store-tradfi) — route each through `resolve_bucket_name(...)` and remove its baseline
      entry. **Timing-gate CLEARED 2026-08-09 (round-9 sweep)**: all 5 flat legacy bucket names are confirmed 404 (live
      `gcloud storage buckets describe`, re-verified this pass — matches
      `bucket_estate_consolidation_closeout_2026_07_24.md`'s 2026-07-31 finding) — the code paths referencing these
      literals are dead/unreachable, so this is now a pure, zero-live-risk code cleanup (repoint each of the 15 (file,
      literal) locations at `check_no_explicit_project_id_bucket_baseline.json` through `resolve_bucket_name(...)`,
      remove the corresponding baseline entry, confirm `check_no_explicit_project_id_bucket.py` still passes with a
      shrunk baseline). Done when: baseline JSON is empty (or reduced to only genuinely-still-live entries, if any
      surface) and the QG passes clean. **Shipped 2026-08-09**: `unified-trading-library@4bbd12f7e` (deleted dead
      `features_source_bucket_template`/ `features_source_bucket_computed`, zero production callers),
      `ml-service@0c7b6ac85` (deleted dead inference
      `features_source_bucket_template`/`_resolve_features_source_bucket`/`get_resolved_features_bucket`; repointed
      training's sports bucket default to the env-tiered `features-sports-prd-{project_id}` form),
      `deployment-service@10600a80` (catalog.py + manifest_reader.py onchain→`kind=features,     asset_group=defi` /
      calendar→`kind=features-calendar`, via new `_SERVICE_FORCED_ASSET_GROUP`), `execution-service@dda3128f1` (onchain
      upstream dep repointed via `resolve_bucket_name()` + `asset_group=defi`). The other 6 of the 15 baselined keys
      were already fixed by earlier, unrelated fold migrations (registry.py's 4 entries — no `sports` entries actually
      exist in that file, contradicting this doc's original table; features-service and ml-service training
      `dependency_checker.py` onchain entries were already hand-repointed to `features-defi-prd-{project_id}`) — those
      needed only baseline-JSON pruning, no code change. Baseline JSON emptied to `"allow": []` in this same commit
      (unified-trading-pm, see git log for this file's SHA).
      `check_no_explicit_project_id_bucket.py --baseline /dev/null` confirmed 0 non-baselined occurrences fleet-wide
      across all 5 repos post-fix, and each repo's full `quality-gates.sh` passed green on the committed HEAD.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Sole todo is explicitly
  timing-gated by the doc's own Disposition section on other asset groups' own legacy-bucket decommission timing, not
  yet reached.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — still accurate against current content.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item remains dependency-blocked.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **legacy_bucket_template_literals-49bf4f182cae dispatch 2026-08-09**: all 15 baselined (file, literal) keys resolved —
  9 needed genuine code fixes (deployment-service catalog.py ×2 + manifest_reader.py ×2, execution-service
  dependency_checker.py ×1, ml-service inference/config.py ×1 + training/config.py ×1, unified-trading-library
  ml_config.py ×1), 6 were already fixed by prior unrelated fold migrations and needed only baseline-JSON pruning.
  Baseline emptied to `"allow": []`. See the todo's Shipped line for per-repo SHAs.

- **round-9 RECLASSIFY sweep 2026-08-09**: RECLASSIFY — `assigned_vm: NA → planning`,
  `execution_scope: local-only → orchestrator-agent`. The sole open todo's timing-gate ("as each asset group reaches its
  own legacy-bucket decommission") was carried forward as still-open by every prior audit (na-eligibility-audit
  2026-07-30/08-07, infra_consolidated_closeout 2026-08-01) — but `bucket_estate_consolidation_closeout_2026_07_24.md`'s
  2026-07-31 todo already found all 5 flat legacy bucket names
  (`features-onchain`/`features-calendar`/`features-store`/`features-sports`/`instruments-store-tradfi`-
  central-element-323112) return 404 live, and this pass independently re-verified the same result today (fresh
  `gcloud storage buckets describe` on all 5, all 404). No prior pass connected that finding to THIS doc's own gate — it
  was recorded as a reason the risk class is lower, not as clearing the blocker. Re-reading the Disposition section: the
  gate's purpose was to avoid touching code for a bucket an asset group might still be actively reading/writing during
  its own migration; with the buckets already deleted, that risk no longer exists — the remaining work is a pure,
  zero-live-risk code cleanup (repoint 15 literal locations through `resolve_bucket_name(...)`, shrink the baseline).
  **Conflict-check**: no `assigned_vm: planning` plan or `infra_satellite_ao_dispatch_batch*` doc (batch6/7/9/10/11/12,
  the current corpus) claims this item; `infra_consolidated_closeout_2026_07_25.md` only name-checks this doc for
  linkage-discoverability, does not claim the work. Single-todo doc — per the established "single-todo carve-out"
  precedent (`infra_consolidated_closeout_2026_07_25.md`'s batch4 note: "no finalize twin per the single-todo
  carve-out"), no separate finalize twin authored; this doc IS the dispatchable unit and archives directly once its one
  todo lands.
