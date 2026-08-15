---
doc_type: plan
title: Legacy-twin GCS deletes (defi/prediction) + fresh sports twin-coverage re-verify
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — execute the legacy-twin delete-after-copy for asset
  groups that pass the 5-part delete-safety proof (defi, prediction; tradfi already tracked separately, cefi already
  done), excluding sports (0 of 34,385 rows passed as of the 2026-07-22 triage). Operator separately asked for a FRESH
  sports re-check, believing the current picture may be more solid — that is its own todo here, not assumed to pass.
status: active
nature: process
asset_group: [defi, prediction, sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [manifest, canonicalization, gcs-delete, legacy-twin]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /plans/archive/issues/sports_legacy_duplicate_triage_2026_07_22.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/archive/issues/sports_legacy_duplicate_triage_2026_07_22.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# Legacy-twin GCS deletes (defi/prediction) + fresh sports twin-coverage re-verify

## Todos

- [ ] [DATA] P1. Re-verify the defi and prediction legs of the legacy-twin `B_legacy_duplicate` population still pass
      the full 5-part delete-safety proof (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1), then execute
      the delete-after-copy for those two asset groups only. Tradfi is already tracked separately
      (`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`) — do not duplicate it here. Cefi is already done.
      Sports is explicitly OUT of scope for this todo — see the next todo. (repo: instruments-service)
- [ ] [DATA] P1. **Fresh sports twin-coverage re-check** (operator request 2026-08-15: "check sports one more time, it's
      looking more solid now — update the doc"). The 2026-07-22 triage (`sports_legacy_duplicate_triage_2026_07_22.md`,
      now archived) found 0 of 34,385 rows passing, root-caused to TWO still-live code call sites reading from the
      legacy path — `instruments-service/instruments_service/engine/ orchestrator/sports_reference_fixtures.py:139`
      (`_ensure_canonical_fixtures_for_override`) and
      `deployment-service/deployment_service/cli/utils/data_status_sports.py:42,74` (`_load_fixture_counts_for_date`'s
      fallback) — which fail Part 4 (no-live-reader) regardless of Part 5's twin-coverage %. Re-check whether those two
      call sites still read the legacy path today; if either has since been removed/refactored, re-run Part 5's
      twin-coverage measurement fresh (`verify_twins.py` / the exhaustive `v2_postfloor_exhaustive.py` check per the
      triage doc's own methodology) and update `instruments_completion_tracker_2026_07_06.md`'s legacy-twin todo with
      the fresh numbers. Do NOT assume sports now passes — measure it. (repos: instruments-service, deployment-service)

## Progress Log

- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `instruments_completion_tracker_2026_07_06.md`'s legacy-twin todo. Operator explicitly asked for the sports re-check
  as a real verification task, not a rubber-stamp — todo 2 is written as a measure-then-report task, not a pre-decided
  outcome.
