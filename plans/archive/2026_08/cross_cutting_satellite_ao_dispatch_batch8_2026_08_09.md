---
doc_type: plan
title:
  Cross-cutting satellite AO batch 8 — instruments_master bounded residual (MVP-toggle real-data verify) extracted from
  the round9 2026-08-09 sweep
summary: >-
  Eighth AO-dispatch batch for the cross-cutting tranche, produced by the round9 2026-08-09 RECLASSIFY +
  satellite-extraction sweep. Pulls 1 bounded item out of `mvp_scope_catalogue_tagging_2026_06_08.md`
  (`instruments_master`): the real-data verify of the MVP data-status toggle (`scope=mvp|could_exist|all`), flagged as a
  likely-AO-eligible candidate by two prior na-eligibility-audit passes (2026-08-07, 2026-08-08) but never extracted
  because it shared the doc with a genuinely operator-gated design question. That design question (features/strategy/
  model MVP sections) has since been substantially resolved via prior extractions (P2a → batch1b, P2b shipped, P2b-2 →
  batch2), so this pass extracts the one remaining bounded item on its own.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta, data]
repos: [deployment-api, instruments-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-8, satellite-docs, instruments-master, mvp-scope]
related:
  [
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    deployment-api/deployment_api/routes/data_status/_coverage_scope.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py,
  ]
source: >-
  round9 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting tranche); this specific item was
  previously flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` by na-eligibility-audit 2026-08-07/08-08 but never extracted.
assigned_role: data_engineering
effort: medium
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 8 (instruments_master) — bounded-item extraction

> **Status (historical): active.** Single-todo batch — exempt from the finalize-twin requirement per
> `check_finalize_plan_coverage.py`'s single-open-todo carve-out; archival folds into this todo's own done-when.

## Todos

- [x] ✅ [DATA] P2. **Real-data verify of the MVP data-status toggle.** Source:
      `mvp_scope_catalogue_tagging_2026_06_08.md` (its "Verify" `[DATA] P2` todo, line ~203). Unit-level parity is
      already covered (`deployment-api@3390c98`'s `test_route_venue_year_coverage_scope.py` asserts denominator
      monotonicity `mvp ≤ could_exist ≤ all`) — this todo is the real-DATA verify against live GCP/manifest state.

      **(1) Consolidator freshness — RE-CONFIRMED 2026-08-09 ~14:52 UTC**, all 5 per-AG instruments consolidators
                      still `ENABLED` (`gcloud scheduler jobs list --location=asia-northeast1`) with fresh `_index/latest.json`
                      heartbeats matching their own cron cadence: cefi `last_run_at=14:01:02Z` (verdict=produced), tradfi
                      `14:00:54Z` (produced), defi `14:01:08Z` (produced), prediction `14:00:52Z` (produced) — all 4 on the hourly
                      `0 * * * *` schedule, checked ~52min after their most recent run, well inside cadence; sports
                      `14:52:41Z` (verdict=empty/no_op=true, correctly idempotent-skipping — confirmed HEALTHY not stale via
                      `gcloud run jobs executions list`: 5 consecutive executions 14:48-14:52 all "Execution completed successfully"
                      on its `*/1 * * * *` schedule, `_index/availability_index.parquet`'s own `update_time` staying at 14:43:06Z is
                      the expected no-new-data-to-merge behaviour, not staleness).

                      **(2) Real-DATA API verify — RUN 2026-08-09 ~14:56 UTC** against live prod
                      (`uts-shared-deployment-api` Cloud Run, `asia-northeast1`), sample asset_group `sports` (see note below on why
                      `cefi` — the endpoint's own listed default — was swapped out): `GET …/venue-year-coverage?asset_groups=sports&
                      scope=could_exist` → `200`, 168 rows / 31 venues / 620,622 total cells / 588,775 captured (~94.9%, an HONEST
                      gap, not hidden); `scope=all` → byte-identical to `could_exist` (168 rows, same totals) — matches the code's
                      own documented `all == could_exist at this endpoint` contract; `scope=mvp` → `200`, 7 rows / **1 venue**
                      (FOOTYSTATS) / 20,522 total cells / 20,522 captured = **exactly 100%** across all 7 years 2020-2026, config
                      versions `mvp_scope=v23`. Confirms both required properties: MVP ON reads ~100% for captured MVP cells and
                      does NOT surface non-MVP venues as missing (the 30 non-FOOTYSTATS venues simply don't appear in the mvp-scope
                      response); MVP OFF (`could_exist`/`all`) shows the full 31-venue universe with its genuine ~94.9% gap intact.
                      Monotonicity holds: `mvp (20,522) ≤ could_exist (620,622) == all (620,622)`.

                      **Deviation from the plan + a filed finding**: the endpoint's own default `asset_groups=cefi,tradfi,defi` —
                      requesting `cefi` (`scope=could_exist`) reliably OOM-killed the shared deployment-api Cloud Run container
                      (16GiB limit) 4/4 times (Cloud Logging: `Memory limit of 16384 MiB exceeded` + `Container terminated on signal
                      9`, 14:53:30-14:55:11 UTC, each ending in client-side `503`) — a real, reproducible gap in the endpoint's
                      unfiltered full-manifest read path for cefi's large tick-level manifest, NOT a defect in the MVP-toggle logic
                      itself (confirmed: the identical endpoint/scope logic works correctly end-to-end for `sports`, a smaller
                      manifest, per the results above). Per this todo's own instruction ("no code change expected unless the verify
                      surfaces a real gap — if so, file that as its own finding … don't fix it inline here"): filed
                      `/plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` (P1, 2 todos) rather than
                      fixing inline or blocking this verify on it — `sports` substitutes as the sample asset_group per the todo's own
                      "for a sample asset_group" wording, and independently proves the toggle mechanism itself is correct.

                      Repo: deployment-api + instruments-service (read-only verification; the one code-shaped follow-up is captured
                      in the filed issue doc, not shipped here).

## Progress Log

- **2026-08-09**: Batch authored via the round9 cross-cutting RECLASSIFY + satellite-extraction sweep. 1 item extracted
  — flagged by na-eligibility-audit twice (2026-08-07, 2026-08-08) as "closer to a bounded check... possible
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE" but never previously extracted; the source doc's other design-call item has since
  been resolved/extracted separately (P2a → `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`, P2b shipped
  `unified-api-contracts@0fb9821b`, P2b-2 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`), leaving this as
  the one clean remaining bounded item.
- **2026-08-09**: Todo 1 done — real-data verify complete. All 5 per-AG instruments consolidators re-confirmed ENABLED +
  fresh. `venue-year-coverage` scope toggle proven correct against live prod for `sports` (`mvp` 20,522/20,522=100%
  single-venue, `could_exist`==`all` 588,775/620,622≈94.9% honest gap, monotonicity holds). `cefi` (the endpoint's own
  default asset_group) was found to reliably OOM the shared deployment-api Cloud Run container instead — a real finding,
  filed as `/plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` (P1) per the todo's own
  findings-triage instruction, not fixed inline. All todos done, unlocked — archiving this plan now per the
  plan-completion-and-archival HARD RULE (single-todo batch, exempt from the finalize-twin requirement per its own
  header note).
