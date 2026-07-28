---
doc_type: issue
title:
  GCS path resolution centralization audit — SPORTS + PREDICTION rounds (continuation of the CEFI/DEFI/TRADFI audit)
summary: >-
  Continuation doc for /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md (the parent doc, now
  at 586 lines — split here to stay clear of the plan line cap rather than grow the parent past it). Same recurring bug
  class (hand-rolled GCS prefixes silently drifting from the canonical `pipeline_mode=`/`asset_group=` hive-partitioned
  shape), same 4-round audit methodology, scoped to SPORTS and PREDICTION per the operator's original expanded directive
  (CEFI/DEFI/TRADFI/SPORTS/PREDICTION, batch+paper+live, under /autonomous).
status: open
nature: issue
asset_group: [sports, prediction]
stage: [meta]
repos:
  [
    unified-trading-library,
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    execution-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [gcs, path-resolution, pipeline-mode, silent-failure, canonical-paths, centralization]
related:
  [
    /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md,
    /plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md,
  ]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  split off /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md (parent doc) once it reached 586
  lines after rounds 1-3 (CEFI/DEFI/TRADFI); continues the operator's original expanded-scope directive for SPORTS +
  PREDICTION under /autonomous.
resolved_by:
depends_on: []
---

# GCS path resolution centralization audit — SPORTS + PREDICTION

## Origin

See the parent doc (`/plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md`) for the full origin
story, the canonical SSOT description, and rounds 1-3 (CEFI/DEFI/TRADFI) findings. This doc exists ONLY to keep the
parent under its line cap while continuing the same audit for the two remaining asset groups the operator named: SPORTS
and PREDICTION.

**SPORTS-specific context worth knowing before auditing**: this asset group already had a real, resolved investigation
this same day — `/plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Update 13 found and fixed a
`pipeline_mode=`-omission bug in MDPS's `_check_existing_outputs` (the bug that KICKED OFF this entire audit) and
reclassified/backfilled 1,944+3,055 sports odds-horizon-bucket manifest rows for the exact same root cause. Any
SPORTS-round agent should read that doc first so it doesn't re-discover the same ground — the question for this round is
whether OTHER sports code paths (not `orchestration_scanner.py`, already fixed) have sibling instances of the same bug
class, plus the batch/paper/live centralization question the operator asked for generally.

**PREDICTION-specific context**: the original P2 fix that started this whole audit
(`market-data-processing-service@df02dd0`) already covers one PREDICTION data point (Kalshi/Polymarket prediction
markets share MDPS's `_check_existing_outputs`, now fixed). Round 1's CEFI audit also flagged (but did not resolve) a
MTDS finding: `_perp_funding_kalshi_polymarket.py`'s "CeFi paths carry no pipeline_mode" comment possibly applying to
prediction-shaped perp-funding writers — that open DESIGN todo lives in the parent doc, cross-reference it rather than
re-deriving.

## Audit round 4 (SPORTS-scoped)

_Not yet run — dispatch pending._

## Audit round 5 (PREDICTION-scoped)

_Not yet run — dispatch pending._

## Todos

- [ ] [SCRIPT] P1. **Round 4 (SPORTS-scoped) audit** — same methodology as rounds 1-3 (hand-rolled prefix hunt, live GCS
      spot-check, registry-staleness check, batch/paper/live coverage), scoped to the SPORTS bucket family across
      MDPS/MTDS/features-service/strategy-service/execution-service/instruments-service. Cross-reference against
      `mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` first — don't re-discover the already-fixed
      `_check_existing_outputs` bug or the already-reclassified/backfilled manifest rows. (repo: all of the above)

- [ ] [SCRIPT] P1. **Round 5 (PREDICTION-scoped) audit** — same methodology, scoped to KALSHI/POLYMARKET's
      `pipeline_mode` conventions. Build from the already-confirmed `market-data-processing-service@df02dd0` data point
      and the parent doc's open MTDS DESIGN todo (Deribit/Kalshi-Polymarket perp-funding `pipeline_mode` ruling) rather
      than re-deriving either. (repo: all of the above)
