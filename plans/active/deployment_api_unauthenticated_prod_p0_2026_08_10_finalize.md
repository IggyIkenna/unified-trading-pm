---
doc_type: plan
title:
  "Finalize — deployment-api unauthenticated-prod P0 (2026-08-10) — independently re-verify the hole is closed, then
  archive the source issue doc"
summary: >-
  Gated companion to `deployment_api_unauthenticated_prod_p0_2026_08_10.md`, per `task_template.md`'s
  finalize-plan-coverage rule. Held by `depends_on` + `gate_on_depends: true` until all 5 P0/P1 todos land. Its job is
  to re-establish the closure INDEPENDENTLY rather than trust the fixing worker's own report — the original finding sat
  open for 4 days precisely because nobody re-checked live state — and then to archive the 2026-08-06 source issue doc
  whose fix-steps this plan absorbed.
status: active
nature: issue
asset_group: [ui]
stage: [meta]
repos: [deployment-api, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [security, p0, deployment-api, unauthenticated-prod, finalize, verification]
related:
  [
    /plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10.md,
    /plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: backend_engineer
effort: high
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [deployment_api_unauthenticated_prod_p0_2026_08_10]
gate_on_depends: true
context_scope:
  [
    /plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10.md,
    /plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md,
  ]
source: >-
  Authored alongside `deployment_api_unauthenticated_prod_p0_2026_08_10.md` on 2026-08-10, per the
  finalize-plan-coverage rule. Gated — does not dispatch until the P0 completes.
---

# Finalize — deployment-api unauthenticated-prod P0

Gated behind `deployment_api_unauthenticated_prod_p0_2026_08_10.md`. Do not start until all 5 of its todos are `[x]`.

## Todos

- [ ] [REVIEW] P1. **Independently re-verify closure against LIVE state, not against the P0 plan's own claims.** Re-run
      the same three checks that established the finding:
      `gcloud run services describe uts-shared-deployment-api     --region asia-northeast1` for `DISABLE_AUTH` /
      `ENVIRONMENT` / `DEPLOYMENT_ENV` / the API key binding; `get-iam-policy` for the `allUsers` invoker binding; and
      the ingress annotation. Then confirm at the application layer that a credential-less request receives 401 and an
      authenticated one succeeds. **Done when**: all values are recorded here with their live output, and any that still
      read the pre-fix value is re-opened as a P0 todo on the source plan rather than explained away.
- [ ] [REVIEW] P1. **Confirm no legitimate caller was broken.** Check Cloud Run request logs for 401s over at least one
      full deploy cycle after enforcement landed, and confirm at least one real end-to-end deploy completed through
      `service-deployed-listener.yml` post-flip. **Done when**: the 401 population is either empty or fully attributed
      to expected/hostile callers, with the reasoning recorded.
- [ ] [DOCS] P2. **Archive `/plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md`** via the standard
      6-step ritual once the above verify clean — its 4 fix-steps were absorbed into the P0 plan, so it must not be left
      `status: open` with stale unchecked boxes. Flip its 4 boxes citing this plan, add the archived banner, and repoint
      every corpus referrer (including the `ag_closeout_audit_cross_cutting_parked_2026_08_07.md` and `_08_08.md`
      entries and `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`'s todo 1). **Done when**: archived, banner
      present, zero dangling referrers (`check_reference_paths.py` no worse than baseline).
- [ ] [DOCS] P3. **Record the detection gap as a durable lesson.** This finding was correct on 2026-08-06 and sat open 4
      days purely because a wrong `asset_group` tag meant no tranche's closeout claimed it — the audit machinery saw it
      every day and routed it nowhere. Capture that in the appropriate codex SSOT (a P0/P1 security finding must not
      depend on tranche tagging to reach an owner) rather than only in this plan. **Done when**: the rule is written to
      codex and cited here, or an explicit decision not to is recorded with reasoning.

## Progress Log

- **2026-08-10** — Authored alongside the P0. Gated via `depends_on` + `gate_on_depends: true`.
