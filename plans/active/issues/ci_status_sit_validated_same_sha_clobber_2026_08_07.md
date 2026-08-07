---
doc_type: issue
title: >-
  ci_status_store.resolve_status() let a same-sha SIT_VALIDATED stamp silently clobber a FAILING for the IDENTICAL
  commit — misleading "SIT PASSED" recovery message while quality-gates-v2 was still genuinely red
summary: >-
  resolve_status()'s rank comparison had no same-commit guard: a SIT_VALIDATED write (rank 3) for the exact same sha as
  a stored FAILING (rank 0) advanced the stored status, because full-workspace-sit.yml only proves cross-repo
  API-surface contracts — not this repo's own tests — yet its stamp outranks FAILING regardless of which commit each
  write was for. Measured 2026-08-07: batch-live-reconciliation-service@9beb2f73 failed quality-gates-v2 at 06:25Z and
  07:31Z; full-workspace-sit restamped SIT_VALIDATED for the SAME sha at 07:43Z; the store advanced FAILING ->
  SIT_VALIDATED and ci-status-update.yml posted an affirmative "SIT PASSED ... clear to promote" Slack message at 8:44am
  while the repo's own gate was still red for that identical commit. instruments-service hit the identical clobber
  pattern in the same incident wave (systemic, not a one-off). Confirmed misleading-signal only, NOT a promotion-safety
  hole — the LDR->main promote gate re-runs a fresh quality-gates-v2 on the promote PR itself regardless of the stored
  ci_status label, so nothing broken could land on main through this path. Fixed in unified-trading-pm@5737bbd317:
  resolve_status() gained a same-commit guard (SIT_VALIDATED cannot clear a FAILING for prev_sha==new_sha; a SIT stamp
  for a NEWER/fixed sha is unaffected and still advances normally), the set_status() call site now threads
  prev_sha/new_sha through, and ci-status-update.yml's Slack wording was corrected to state SIT proves cross-repo
  contracts, not this repo's own quality-gates-v2.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, ci-status, sit, false-positive, alerting-accuracy, quality-gates]
related:
  [
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: 2026-08-07
author: unknown
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-08-07 while auditing the SIT_VALIDATED restamp on batch-live-reconciliation-service@9beb2f73 and
    instruments-service's identical-pattern hit in the same incident wave",
  ]
locked_by:
locked_since:
resolved_by: unified-trading-pm@5737bbd317
context_scope:
  [
    scripts/cicd/ci_status_store.py,
    .github/workflows/ci-status-update.yml,
    tests/unit/test_ci_status_store.py,
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
  ]
---

# ci_status_store same-sha SIT_VALIDATED clobber

## The bug

`resolve_status()` (`scripts/cicd/ci_status_store.py`) is a rank-based no-downgrade compare-and-set: `SIT_VALIDATED` is
rank 3, `FAILING` is rank 0. The existing guards handle two carve-outs (a non-main red can't clobber `MAIN_GREEN`; a
non-main green can't clear a main-originated `FAILING`), but neither one is scoped to the actual COMMIT each write is
about. So a `SIT_VALIDATED` write for the SAME sha as a stored `FAILING` — on the same non-main branch, no `main`
provenance involved — fell through to plain rank comparison and advanced, even though `full-workspace-sit.yml`'s own
header comment disclaims that SIT proves only cross-repo API-surface contracts, not the repo's own test suite.

## Measured incident (2026-08-07)

| Time (UTC) | Event                                                                                  |
| ---------- | -------------------------------------------------------------------------------------- |
| 06:25Z     | `batch-live-reconciliation-service@9beb2f73` fails `quality-gates-v2`                  |
| 07:31Z     | Same sha fails `quality-gates-v2` again                                                |
| 07:43Z     | `full-workspace-sit.yml` stamps `SIT_VALIDATED` for the SAME sha `9beb2f73`            |
| 8:44am     | `ci-status-update.yml` posts "✅ SIT PASSED ... → SIT_VALIDATED" to Slack (misleading) |

`instruments-service` hit the identical clobber pattern in the same incident wave — confirms this is systemic (a
property of `resolve_status()`'s rank logic), not a one-off flake.

## Why this is misleading, not a promotion-safety hole

The stored `ci_status` label is what Slack and deployment-ui's Repo-CI table read, so the clobber produced a false "all
clear" signal for on-call attention. It does NOT let anything broken land on `main`: the LDR→main promote gate
(`ldr-to-main-promote-fleet.yml` / `ldr-to-main-promote.yml`) re-runs a FRESH `quality-gates-v2` on the promote PR
itself, independent of whatever label is stored in `ci_status` — so a still-red repo cannot promote through this path
regardless of the Slack message's wording.

## Fix — `unified-trading-pm@5737bbd317`

1. `scripts/cicd/ci_status_store.py` — `resolve_status()` gained a `prev_sha`/`new_sha` parameter pair and a same-commit
   guard inserted right after the `FAILING` block (before the existing main-provenance symmetric guard): `SIT_VALIDATED`
   may not clear a stored `FAILING` when `prev_sha == new_sha` (both non-empty). A SIT stamp for a NEWER (already-fixed)
   sha is unaffected and still advances normally. The `set_status()` call site now threads the stored doc's `sha` and
   the incoming write's `sha` through as `prev_sha`/`new_sha`. Confirmed the
   `sit_validated_tree`/`sit_validated_workspace_digest` merge-preserve logic stays keyed off the INCOMING `status`
   parameter (not the resolved `written` value) — this guard only changes the displayed status label, never the SIT
   tree-fingerprint data the promote gate actually trusts.
2. `.github/workflows/ci-status-update.yml` (`build-message` job) — the "✅ SIT PASSED" Slack wording now says the stamp
   is "cross-repo API-surface contracts green on the LDR tree — NOT proof this repo's own quality-gates-v2 passed",
   instead of implying the repo's own tests passed.
3. Tests added to `tests/unit/test_ci_status_store.py`: same-sha `FAILING → SIT_VALIDATED` attempt is suppressed (stays
   `FAILING`); a different (newer) sha's `SIT_VALIDATED` still advances normally; the guard fails open when either sha
   is unknown/empty (legacy callers, unattributed docs); an end-to-end `set_status()` test proves the call-site wiring
   (stored doc's `sha` vs the incoming write's `sha`).

## Cross-repo relevance

This affects three consumers of the stored `ci_status` label: the Slack recovery message (`ci-status-update.yml`),
deployment-ui's Repo-CI table (reads `ci_status_store.get_all()` / `resolve_ci_status_map()`), and the Tier-A
promote-gate read (`get_doc()` — though as noted above, the promote gate's OWN fresh `quality-gates-v2` re-run is the
actual safety backstop, not the stored label).
