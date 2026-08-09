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
    /plans/active/issues/dp_reprobe_empty_oom_regression_unbounded_manifest_read_2026_08_09.md,
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

- [x] ✅ [CODE] P1. **Ship the e2e `_dp_common.file_escalation_issue` actionable-issue half via the D16 dirty-deps
      direct-push carve-out.** Source: `data_pipeline_self_healing_completion_residual_2026_07_24.md` (its `[CODE] P1`
      "Ship the e2e `_dp_common.file_escalation_issue` actionable-issue half" todo). **PREMISE WAS STALE — already
      shipped, no push needed.** Re-verified 2026-08-09: `strategy-service` is clean (0 dirty files) in this slot's
      worktree, but that's moot — `e2e-testing/scripts/audit/_dp_common.py::file_escalation_issue` already carries the
      `parent_epic`/`assigned_vm` frontmatter (lines 512-513) + a real `- [ ] [CODE] P1.` todo naming `target_repo`
      (lines 469, 549-552) + `_commit_and_push_pm_artifacts` wiring (lines 561-566), and
      `tests/unit/test_dp_audit.py::test_file_escalation_issue_is_actionable` (line 1229) asserts exactly this shape —
      all landed **e2e-testing@821b73a** (2026-06-23) and confirmed an ancestor of `origin/live-defi-rollout` HEAD
      (`git merge-base --is-ancestor 821b73a HEAD` → true, verified in this slot's fresh-pulled e2e-testing clone at
      HEAD `47efe7d`). `assigned_vm` has since been updated to `planning` (post-2026-06-27 single-VM refactor;
      `_ISSUE_ASSIGNED_VM = "planning"` at line 125) and the test explicitly asserts `"assigned_vm: planning" in body` —
      further proof this is live, maintained code, not dead WIP. The separate commit-and-push gap this todo's Done-when
      implicitly depends on (artifacts written but never committed on local runs) was found, fixed, and verified live
      2026-07-12 (`plans/archive/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md`,
      `status: resolved`, evidence `unified-trading-pm@ad1fa6bc2`). Conclusion: the dirty-dep block cleared and this
      landed through the normal quickmerge path sometime between 2026-06-23 and now — the source doc's checkbox was
      simply never updated to reflect it. No D16 carve-out push was needed; nothing to ship today. Repo: e2e-testing (no
      code change — verification only).
- [x] ✅ [INFRA] P2. **Rebuild `e2e-audit:latest` from clean LDR so the daily reprobe cron loads all 5 per-AG hooks.**
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
      the next `uts-prod-dp-reprobe-empty` execution). Repo: e2e-testing, deployment-service. — **DONE 2026-08-09
      (slot-18, infra)**: built from a clean `e2e-testing@78f7f2b` (`origin/live-defi-rollout` HEAD, confirmed all 5
      per-AG hook modules present — `_REPROBE_HOOK_MODULES` lists `reprobe_cefi/defi/sports/tradfi/prediction`; the
      plan's cited `5db3860` SHA predates an August history rewrite and no longer resolves, but the content is confirmed
      live via direct source read, not just SHA ancestry). Build `1057b974-93b2-4d54-8540-a9c18757f43a`
      (asia-northeast1) SUCCESS in 2m8s. Digest changed
      `sha256:6b52baca...`→`sha256:0fc05321d5790b35875d1330424348abc0abc4be873b17a449b44b909458e3ce`. In-build smoke
      confirmed all 3 audit scripts (`data_pipeline_daily_digest.py`, `manifest_hygiene_daily.py` ×2 modes,
      `reprobe_new_empty_confirmed.py`) import + arg-parse OK inside the image. Cron pickup verified WITHOUT waiting for
      the next scheduled run: the job spec references the `:latest` tag (not a pinned digest, per this doc's own todo 3
      "bonus finding" that Cloud Run Jobs re-resolve `:latest` per-execution), so a manual
      `gcloud run jobs execute uts-prod-dp-reprobe-empty --wait` immediately confirmed the new digest was picked up
      (execution `uts-prod-dp-reprobe-empty-r2gsn`). That execution still failed with a pre-existing, UNRELATED memory
      OOM (same failure on the 3 prior natural daily runs, 2026-08-07/08/09, both before and after this rebuild) — filed
      as its own issue, `/plans/active/issues/dp_reprobe_empty_oom_regression_unbounded_manifest_read_2026_08_09.md`,
      root-caused to `reprobe_new_empty_confirmed.py` never getting the `columns=` restriction `daily_digest.py` already
      shipped for the same manifest-read antipattern — out of this todo's scope (a code fix, not an image rebuild).
      Evidence: cloudbuild=1057b974-93b2-4d54-8540-a9c18757f43a
- [x] ✅ [INFRA] P1. **Verify + flip the SCHEDULED consolidator asset_group-guard MTDS-image delivery.** Source:
      `data_pipeline_self_healing_completion_residual_2026_07_24.md` (its "Later-surfaced self-healing deployment
      residuals" `[INFRA] P1` item, open since 2026-06-23). **VERIFIED 2026-08-09 (slot-8) — all 3 Done-when parts
      confirmed live**, source checkbox flipped in the same commit. Original build id `beb0b08e` aged out of Cloud Build
      list retention, but the doc's own "or a fresher one has since landed" allowance applies:
      `market-tick-data-service@81dbe37` (the `af5f6c1e`→`3f2b47f2` bump) is a confirmed ancestor of HEAD and of every
      build since (`git merge-base --is-ancestor 81dbe37 <sha>` → true for both today's `:latest`-producing build commit
      `7f699fc` and the commit `e24199d` actually running in prod), and the Dockerfile pin has since advanced further
      (`bca66133...`). (a) build SUCCESS: `393127d5-b5f6-4a4e-9543-b1382e43eca2` (commit `7f699fc`) SUCCESS, finished
      2026-08-09T16:36:19Z. (b) digest differs from pre-bump `af5f6c1e`: confirmed (today's digests
      `sha256:90a1c00e...`/`sha256:da82576a...` are unrelated to the old base). (c) consolidator execution exit 0 on the
      new image: `uts-prod-manifest-consolidator-instruments-defi-pt6xw` completed 2026-08-09T16:00:56Z
      `EXECUTION_SUCCEEDED` on digest `sha256:90a1c00e...` (commit `e24199d`, confirmed descendant of `81dbe37`). Bonus
      finding: Cloud Run Jobs re-resolve `:latest` to a fresh digest at EACH execution (not pinned at job-deploy time),
      so the guard has been live in every consolidator run since the ordinary build pipeline first carried it past
      `81dbe37` — not just this one-off check. Repo: market-tick-data-service (no code change — verification only).
      Evidence: cloudbuild=393127d5-b5f6-4a4e-9543-b1382e43eca2

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
- **2026-08-09 (slot-6)**: Flipped item 1 — investigation found the todo's own premise was stale, not the D16 carve-out
  it was written to use. `strategy-service` is clean in this slot's worktree (the dirty-dep block that was live
  2026-06-23 is long gone), but more importantly the e2e code itself (`_dp_common.file_escalation_issue` frontmatter +
  todo + `target_repo` routing + `test_file_escalation_issue_is_actionable`) was already an ancestor of
  `origin/live-defi-rollout` — landed **e2e-testing@821b73a** (2026-06-23) and never reverted; `assigned_vm` was even
  updated to `planning` post-2026-06-27 refactor, proving it's live maintained code. The related commit-and-push gap was
  independently fixed + verified live 2026-07-12
  (`plans/archive/issues/audit_writes_escalation_artifacts_but_never_commits_them_2026_07_06.md`). No push was made
  today (nothing to push) — checkbox flipped citing this evidence. Leaving the source doc's own twin checkbox open per
  this doc's own note (reconciled by the gated finalize twin once all 3 batch-9 items are done).
- **2026-08-09 (slot-8)**: Flipped item 3 (consolidator asset_group-guard MTDS-image delivery) — all 3 stated Done-when
  parts verified live via `gcloud`: (a) build `393127d5` (commit `7f699fc`) SUCCESS finished 2026-08-09T16:36:19Z; (b)
  current `market-tick-data-service:latest` digests (`sha256:90a1c00e...`, `sha256:da82576a...`) differ from the
  pre-bump `af5f6c1e` base; (c) `uts-prod-manifest-consolidator-instruments-defi-pt6xw` completed 2026-08-09T16:00:56Z
  `EXECUTION_SUCCEEDED` on digest `sha256:90a1c00e...` (commit `e24199d`, confirmed descendant of the guard-bump commit
  `market-tick-data-service@81dbe37` via `git merge-base --is-ancestor`). Also flipped the source doc's twin checkbox in
  `data_pipeline_self_healing_completion_residual_2026_07_24.md` with the same evidence (same commit). No code change —
  verification only, both flips in one `docs(plans):` commit.
