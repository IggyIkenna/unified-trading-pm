---
doc_type: plan
title: True-catalogue phase 2 — publish expected_universe.parquet projection (already designed, ready to build)
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 11): dispatch
  data_status_catalogue_true_source_phase2_2026_07_24.md's Phase-2 True-catalogue-source todo. The design is
  already fully worked out on real data (2026-07-17) — the tempting shortcut (extend
  `_IDENTITY_CATALOGUE_ASSET_GROUPS` to read `prod/catalog.parquet` for sports/prediction) was prototyped and
  DELIBERATELY REVERTED: sports identity catalogue has `venue=''` (keys on league_id, no venue), no
  capture_status/error_reason/attempted_at (would fabricate `captured` status on ~25k rows, violating honest-
  absence), and lowercase-legacy `instrument_type='team'`. The real blocker is architectural, not naming:
  `prod/catalog.parquet` only answers "what was ever captured," never "what EXISTS but was never captured" — for
  ANY asset group. The correct shape (already specced): instruments-service publishes a small per-AG
  `_catalogue/expected_universe.parquet` (instrument_id + venue/league_id + instrument_type + lifecycle +
  is_expected) from its existing `enumerate_expected_universe.py`/`expected_universe.py`, and deployment-api
  reads that ONE bounded object alongside the identity catalogue — an artifact-contract integration (T4-safe, no
  service→service import). Prerequisite found while scoping: prediction's `/catalogue` currently collapses
  12,921 non-blank `_index` ids to 79 via `_dedupe_latest` (keys on the cqg BUNDLE, not per-market instrument) —
  fix this first or phase-2 inherits the bug.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, deployment-api]
scope: [engineer]
tags: [cross-cutting, ui, data-status, catalogue, honest-coverage]
related:
  [
    /plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 11, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    instruments-service/scripts/expected_universe.py,
    deployment-api/deployment_api/routes/data_status/_catalogue.py,
  ]
locked_since:
resolved_by:
---

# True-catalogue phase 2 — publish expected_universe.parquet projection

## Todos

- [ ] [BACKEND] P3. **Prerequisite: fix prediction's `_dedupe_latest` collapse.** `/catalogue` for prediction
      reports `total_count=79` on real data because 12,921 non-blank `_index` ids key on the cqg BUNDLE, not the
      per-market instrument, and collapse under `_dedupe_latest`. Fix before building phase-2 on top of this
      path (distinct from `/prediction-catalogue`, which already reads the real 2.67M-row catalogue correctly).
      Repo: deployment-api.
- [ ] [BACKEND] P3. **True-catalogue source — build the expected_universe.parquet projection.** Have
      instruments-service publish a small per-AG `_catalogue/expected_universe.parquet` (instrument_id +
      venue/league_id + instrument_type + lifecycle + `is_expected`) from its existing
      `enumerate_expected_universe.py`/`expected_universe.py`. Have deployment-api read that ONE bounded object
      alongside the identity catalogue, tagging each row `exists_in_catalogue` vs `captured`. Integrate by
      artifact contract (T4-safe) — do NOT extend `_IDENTITY_CATALOGUE_ASSET_GROUPS` to read
      `prod/catalog.parquet` for sports/prediction (already prototyped and reverted — see source doc for why:
      fabricated capture_status, blank venue, lowercase legacy instrument_type). Repos: instruments-service,
      deployment-api.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 11, operator ruling)**: extracted from
  `data_status_catalogue_true_source_phase2_2026_07_24.md` for AO dispatch, since the parent doc stays
  `assigned_vm: NA`. Both naming concerns (venue='', instrument_type='team') the audit flagged as "unresolved
  decisions" turned out to already be resolved REASONS the shortcut was reverted, not open questions — the real
  remaining work is the architectural build already specced in the source doc.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
