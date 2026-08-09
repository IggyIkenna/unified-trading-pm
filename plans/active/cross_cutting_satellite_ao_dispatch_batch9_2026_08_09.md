---
doc_type: plan
title:
  Cross-cutting satellite AO batch 9 — observability_master bounded residuals (e2e escalation-issue dirty-dep ship,
  e2e-audit rebuild, consolidator asset_group guard verify) extracted from the round11 2026-08-09 sweep
summary: >-
  Ninth AO-dispatch batch for the cross-cutting tranche, produced by the round11 2026-08-09 RECLASSIFY +
  satellite-extraction sweep (a re-check of docs whose KEEP-NA marker was staleness-only, never re-tested against
  today's accumulated precedents). Pulls 3 bounded items out of
  `data_pipeline_self_healing_completion_residual_2026_07_24.md` (`observability_master`): (1) ship the e2e
  `_dp_common.file_escalation_issue` actionable-issue half — code is written + QG-green but quickmerge has sat 🟡
  BLOCKED on a peer `strategy-service` dirty-dep since 2026-06-23; the D16 all-repos dirty-deps direct-push carve-out
  (operator-ruled 2026-08-08) now covers exactly this case; (2) rebuild `e2e-audit:latest` from clean LDR — already
  flagged 2026-08-07 by this doc's own audit as "MISCLASSIFIED_LIKELY_AO_ELIGIBLE... for a future pass"; (3) verify +
  flip the SCHEDULED consolidator asset_group-guard MTDS-image delivery, which has an explicit, fully mechanical
  Done-when. The source doc's whole-doc RECLASSIFY bar stays unmet — its other 2 open items are a dirty-dep aggregate
  (registry-mode flip gated on confirming each tier is wired) and an explicit `(stretch)` design item with no forcing
  function, neither extracted here.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, deployment-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-9, satellite-docs, observability-master, self-healing, d16]
related:
  [
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch9_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /codex/08-workflows/ci-cd-flow.md,
    e2e-testing/scripts/audit/_dp_common.py,
  ]
source: >-
  round11 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting + ui tranches, 27-doc gap-check on
  docs whose KEEP-NA marker predated today's D16-all-repos / IAM-self-service / 2-new-credentials rulings) — these 3
  items were independently bounded and worker-determinable, found via a full re-read of every candidate doc; item 1
  specifically unblocked by today's D16 all-repos dirty-deps direct-push carve-out ruling.
assigned_role: data_engineering
effort: medium
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 9 (observability_master) — bounded-item extraction

> **Status: active.** All 3 todos below are same-priority-independent and touch distinct files — no
> `sequential`/`gate_on_depends` needed.

## Todos

- [ ] [CODE] P1. **Ship the e2e `_dp_common.file_escalation_issue` actionable-issue half via the D16 dirty-deps
      direct-push carve-out.** Source: `data_pipeline_self_healing_completion_residual_2026_07_24.md` (its `[CODE] P1`
      "Ship the e2e `_dp_common.file_escalation_issue` actionable-issue half" todo). The code (frontmatter
      `parent_epic`/`assigned_vm` + a real `- [ ] [CODE] P1.` todo + `target_repo` routing + the new
      `test_file_escalation_issue_is_actionable` test) is already WRITTEN and QG-green (`quality-gates.sh --no-fix` exit
      0, 31s, in `e2e-testing`) — the only reason it never shipped is that `quickmerge`'s pre-flight refused while a
      peer's `strategy-service` WIP sat uncommitted (a dirty-dep block, dated 2026-06-23). Per the 2026-08-08 operator
      ruling (D16), the dirty-deps direct-push carve-out is now closed all-repos, not PM-only — this is exactly that
      case. Re-verify the peer `strategy-service` tree state first (it may have cleared naturally in the 7 weeks since);
      if still dirty, use the D16 carve-out to land
      `e2e-testing --files 'scripts/audit/_dp_common.py tests/unit/test_dp_audit.py'` directly rather than continuing to
      wait. Done when: the e2e half is live on `origin/live-defi-rollout` and `file_escalation_issue`'s output
      frontmatter carries `parent_epic`/`assigned_vm`/a real todo line, verified against a fresh-filed escalation issue
      doc. Repo: e2e-testing.
- [ ] [INFRA] P2. **Rebuild `e2e-audit:latest` from clean LDR so the daily reprobe cron loads all 5 per-AG hooks.**
      Source: `data_pipeline_self_healing_completion_residual_2026_07_24.md` (its `[INFRA] P2` "Rebuild e2e-audit:latest
      from clean LDR" todo) — already flagged by this same doc's own 2026-08-07 na-eligibility-audit pass as
      "MISCLASSIFIED_LIKELY_AO_ELIGIBLE... for a future pass," never actioned since. The live `e2e-audit:latest` Cloud
      Build image predates `e2e-testing@5db3860`; tradfi/prediction reprobe hooks currently no-op
      (`reached_source=False` regardless), so the missing rebuild is a correctness-completeness gap for defi/cefi/sports
      hook updates, not an active outage. Reuse the existing `cloudbuild-e2e-audit.yaml` build→smoke→push pipeline
      (`gcloud builds submit --config=cloudbuild-e2e-audit.yaml --region=asia-northeast1 .`) from a clean
      `origin/live-defi-rollout` checkout. Done when: the new image digest differs from the currently-deployed one
      (`gcloud artifacts docker images list`), the in-build smoke passes (all 3 audit scripts import + arg-parse inside
      the image), and the daily reprobe cron's next run picks it up (verify via `gcloud run jobs executions describe` on
      the next `uts-prod-dp-reprobe-empty` execution). Repo: e2e-testing, deployment-service.
- [ ] [INFRA] P1. **Verify + flip the SCHEDULED consolidator asset_group-guard MTDS-image delivery.** Source:
      `data_pipeline_self_healing_completion_residual_2026_07_24.md` (its "Later-surfaced self-healing deployment
      residuals" `[INFRA] P1` item, open since 2026-06-23). The v9 blank-`asset_group` self-heal
      (`_asset_group_for_market_data_bucket`, UTL `7b2306c3`/`6acbb9ad`) needed the `market-tick-data-service` base
      Docker image bumped `af5f6c1e`→`3f2b47f2` so the ~40 `uts-prod-manifest-consolidator-*` Cloud Run jobs (which run
      `unified_trading_library.manifest_consolidator` from `market-tick-data-service:latest`) pick it up; the bump was
      committed (`market-tick-data-service@81dbe37`) and a direct build kicked off (`beb0b08e`) but this todo's own
      Done-when was never re-checked. Done when (the doc's own stated bar): (a) the `market-tick-data-service:latest`
      Cloud Build for the digest bump shows SUCCESS (`gcloud builds describe beb0b08e` or the current build for this
      Dockerfile change if a fresher one has since landed), (b)
      `gcloud artifacts docker images describe     market-tick-data-service:latest` shows a digest that differs from the
      pre-bump `af5f6c1e` base, and (c) one consolidator execution (e.g.
      `uts-prod-manifest-consolidator-instruments-defi`) runs exit 0 on the new image
      (`gcloud run jobs executions list` + `describe`) — flip the source checkbox citing the 3-part evidence, or if any
      part fails, file what's actually still broken as a fresh, narrower finding. Repo: market-tick-data-service.

## Codex SSOTs

`/codex/08-workflows/ci-cd-flow.md` (D16 dirty-deps carve-out, all-repos),
`/codex/05-infrastructure/data-pipeline-alerts.md` (the self-healing loop these 3 items complete tail-pieces of).

## Progress Log

- **2026-08-09**: Batch authored via the round11 cross-cutting+ui RECLASSIFY + satellite-extraction sweep. 3 items
  extracted from `data_pipeline_self_healing_completion_residual_2026_07_24.md` (`observability_master`) — the
  surrounding whole-doc RECLASSIFY bar stayed unmet (a dirty-dep-gated registry-mode-flip aggregate and an explicit
  `(stretch)` item remain), but these 3 are individually bounded and worker-determinable. Item 1 is specifically
  unblocked by today's D16 all-repos dirty-deps direct-push carve-out ruling (2026-08-08); items 2-3 were already
  flagged by this source doc's own prior audit passes as extraction-ready and never actioned.
