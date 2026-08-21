---
doc_type: plan
title: sports-integration-03-features-provider-integration
summary: 'FSS reads reference data + cross-provider mappings from instruments-service GCS,

  odds data from MTDS GCS. Uses mappings to resolve provider-specific IDs (footystats_id,

  understat_name) and calls features-interface adapters for enrichment data.

  FSS never fetches reference data directly from APIs.

  NOTE: FSS CLI entrypoint needs fixing (L3 validation blocker). Cross-provider mappings

  now exist for ALL 33/33 leagues in UAC (completed 2026-03-30).'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: D1, business: B1}
repo_gates:
- {repo: features-sports-service, code: C0, notes: Replace direct API fetch with GCS reader + mapping-based enrichment}
- {repo: unified-features-interface, code: C0, notes: 'Verify UnderstatAdapter, FootystatsAdapter work with provider-specific IDs'}
depends_on: [sports-integration-01-reference-data-pipeline, sports-integration-02-odds-market-data-pipeline]
isProject: false
todos:
- {id: p1-gcs-reader, content: '- [x] [AGENT] P0. gcs_reader.py created in FSS data/ directory (~1100+ LOC). Reads from instruments-service and MTDS GCS buckets.

    ', status: done, note: features_sports_service/data/gcs_reader.py exists and is substantial}
- {id: p2-mapping-resolution, content: '- [x] [AGENT] P0. _fetch_runner.py updated — run_fetch_providers calls read_all_reference_data from GCS reader for mapping resolution

    ', status: done, note: _fetch_runner.run_fetch_providers calls read_all_reference_data}
- {id: p3-wire-exporters, content: "- [ ] [AGENT] P1. Replace stub exporters with GCS-backed + enrichment data.\n  File: features_sports_service/exporters/exports.py\n  Each export function reads from GCS-backed loader:\n    export_fixtures() -> GCS reference data\n    export_fixture_stats() -> enrichment from footystats\n    export_venues() -> GCS reference data\n  All non-stub, all producing real rows.\n", status: pending, blocked_by: p2-mapping-resolution}
- {id: p4-validation, content: "- [ ] [AGENT] P0. Run FSS for 2026-03-22 with all providers.\n  Verify: reference data read from GCS (not fetched from API)\n  Verify: enrichment data fetched via mappings\n  Verify: all entity types exported with non-zero rows\n  Verify: 4+ providers contributing data\n  QG: cd features-sports-service && bash scripts/quality-gates.sh\n", status: pending, blocked_by: p3-wire-exporters}
- {id: p4b-footystats-backfill, content: "- [ ] [SCRIPT] P1. Backfill FootyStats match-level data to GCS.\n  FootyStats has per-half data (ht_goals, 2hg_goals, fh_corners, 2h_corners,\n  per-half xG) that no other source provides. UMI FootystatsAdapter exists but\n  is BLACKLISTED_NO_ACCESS (no API key).\n  Steps: 1) Obtain FootyStats API key. 2) Implement fetch_matches() in adapter.\n  3) Backfill 33 prediction leagues x 5.8 years.\n  4) Write to GCS with entity=footystats_matches partition.\n  BLOCKER: Need FootyStats API key before any work can proceed.\n", status: pending}
- {id: p5a-fss-manifest, content: "- [ ] [AGENT] P0. Verify FSS ManifestWriter tracks feature computation per date.\n  ManifestWriter exists in FSS batch_handler.py. Verify: writes availability_index\n  with date, feature_group, row_count, provider_count. --force overwrites, else skip.\n", status: pending, blocked_by: p4-validation}
- {id: p5b-one-month-features, content: "- [ ] [SCRIPT] P0. Run features pipeline for 1 month (2025-03-01 to 2025-03-31).\n  FSS reads reference data + odds from GCS, computes all feature groups.\n  Verify: manifest shows 100% date coverage for the month.\n  Verify: all feature groups have non-zero rows per matchday.\n  Only proceed to full rollout after 1-month passes.\n", status: pending, blocked_by: p5a-fss-manifest}
- {id: p5c-full-period-features, content: "- [ ] [SCRIPT] P1. Roll out features to full period (2020-06-01 to 2026-03-28).\n  Run FSS with --force=False (skip dates already in manifest).\n  Completeness target: >= 99% of matchdays with complete features.\n  Report per-calculator coverage. Flag gaps for --force re-run.\n", status: pending, blocked_by: p5b-one-month-features}
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.md](./consolidated_sports_prediction_pipeline_2026_04_15.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Sports Integration Plan 3: Features Provider Integration

Part of the 6-plan sports integration series. Depends on Plan 1 (reference data in GCS) and Plan 2 (odds in GCS).

## Success Criteria

- FSS reads reference data from instruments-service GCS (no direct API fetch)
- FSS uses TeamMapping/FixtureMapping to resolve provider IDs
- FootyStats, Understat, Soccer-Football-Info, Open-Meteo data flowing
- All exporters produce non-zero rows
- Manifest tracks 100% of dates with feature group counts
- 1-month validation passes before full-period rollout
- Full period (2020-06-01 to 2026-03-28) >= 99% feature coverage
