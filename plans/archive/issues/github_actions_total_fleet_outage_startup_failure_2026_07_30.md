---
doc_type: issue
title:
  GitHub Actions is completely down fleet-wide, right now — every workflow on every repo hitting "startup_failure" with
  0 jobs created; strong evidence this is a GitHub Actions spending-limit cap, not a code or infrastructure problem
summary: >-
  While investigating a spike in `ldr_qg_failure` escalations for `instruments-service`, found its `quality-gates-v2`
  runs failing with GitHub's generic `"This run likely failed because of a workflow file issue"` and **0 jobs created**
  (`gh api .../runs/<id>/jobs` → `total_count: 0`) — the signature of GitHub rejecting the run before ever instantiating
  jobs, not a real YAML/schema problem (confirmed: `.github/workflows/quality-gates-v2.yml` parses as valid YAML
  locally, and is near-byte-identical to a currently-unaffected... except it ISN'T unaffected, see below).

  Escalated the check to confirm scope: **every repo checked shows the same signature**, right now —
  `market-tick-data-service`, `features-service` (both protected-6 self-hosted), `unified-trading-pm` itself (the OWNER
  of the shared reusable workflow every other repo calls), and `deployment-ui` (a completely different stack — no
  self-hosted runners, no Python reusable workflow, Vercel-triggered). PM specifically: **all 60 of its last 60 runs
  (2026-07-29T22:15Z → 2026-07-30T00:27Z, ~2h12m) are `startup_failure`** — a sustained, total, ongoing outage, not a
  transient blip.

  Checked the GitHub Actions Enhanced Billing API (`github-billing-token` secret, `GET
  /users/IggyIkenna/settings/billing/usage`) for July 2026: **net Actions spend $1,112.69** across 1,618 usage-line
  entries — closely matching the "~$1,150-1,200/mo baseline" measured earlier in the original CI-cost-reduction audit
  (2026-07-15). GitHub's personal-account "spending limit" setting (Settings → Billing → Plans and usage → Spending
  limits) is **not readable via the REST API** (the old `/users/{user}/settings/billing/actions` endpoint that used to
  expose limits is deprecated, HTTP 410) — could not directly confirm the cap value or whether it's been hit, only that
  the spend is in the right range for this to be exactly that. The combination of (a) spend near a plausible monthly
  cap, (b) an INSTANT, zero-jobs, org-wide failure across every repo and workflow type simultaneously, and (c) no code
  change that correlates with the failure window is strong circumstantial evidence for a spending-limit block, but this
  is a **hypothesis, not a confirmed root cause** — needs a human to check the GitHub billing UI directly (the one view
  this session has no API path to).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, instruments-service, market-tick-data-service, features-service, deployment-ui]
scope: [engineer, admin]
tags: [ci-cd, github-actions, outage, billing, spending-limit, fleet-wide, startup-failure, critical]
related:
  [
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
priority: P0
parent_epic: infrastructure_master
source:
  "discovered while investigating instruments-service ldr_qg_failure spike, 2026-07-30 ~00:15-00:30 UTC, interactive
  session slot 1, /autonomous"
execution_scope: local-only
drift_direction: advance-code
context_scope: [/codex/08-workflows/ci-cd-flow.md, /codex/15-runbooks/devops-ci-walls.md]
depends_on: []
assigned_vm: NA
resolved_by: interactive session, 2026-07-31 — GitHub Actions billing wall confirmed cleared via live gh run checks
locked_by:
locked_since:
---

# GitHub Actions fleet-wide outage — likely spending limit, needs operator's billing UI

> **🟢 RESOLVED 2026-07-31** — confirmed cleared via live `gh run` checks in an interactive session.

## Evidence

- `instruments-service` run `30500539587`: `gh run view` → `"This run likely failed because of a workflow file issue."`;
  `gh api repos/IggyIkenna/instruments-service/actions/runs/30500539587/jobs` → `{"total_count": 0, "jobs": []}` — zero
  jobs ever created.
- Local `.github/workflows/quality-gates-v2.yml` parses as valid YAML (`python3 -c "import yaml; ..."` — no error).
  Diffed against `market-data-processing-service`'s copy of the same templated file — only substantive difference is the
  (correct, intentional) `self_hosted_runner_labels` value.
- Same `startup_failure` + presumably-0-jobs signature confirmed on, at time of writing:
  - `market-tick-data-service` (3/3 most recent runs)
  - `features-service` (3/3 most recent runs)
  - `unified-trading-pm` (**60/60** most recent runs, spanning `2026-07-29T22:15:04Z` → `2026-07-30T00:27:05Z`, i.e.
    still ongoing as of this writing)
  - `deployment-ui` (3/3 most recent runs — this repo does not share the Python reusable workflow or self-hosted runners
    with the others, ruling out a code/template-specific cause)
- GitHub Actions Enhanced Billing API, July 2026: `netAmount` sum across `product=actions` line items =
  **$1,112.69** (1,618 usage entries). Matches the previously-measured ~$1,150-1,200/mo baseline closely enough to be a
  plausible spending-limit collision.
- Could NOT confirm the actual spending-limit VALUE or "limit reached" state via API — the classic
  `/users/{user}/settings/billing/actions` endpoint that historically exposed this is deprecated (`410 Gone`,
  `"This endpoint has been moved"`). This is a real capability gap for this session, not a skipped step.

## What this is NOT

- Not a code regression: no commit to any affected repo's `.github/workflows/` correlates with the failure window
  (checked `instruments-service`'s most recent workflow-file commit — 28 hours before the failures began; checked PM's
  reusable-workflow's most recent commit — ~15 hours before). Not caused by this session's own commits (deployment-ui,
  unrelated stack, is also affected).
- Not the self-hosted-runner capacity crisis tracked in `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`
  / `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` — those show REAL job execution that's slow or
  contended; this shows **zero jobs ever created**, a categorically different failure mode, and it affects
  `deployment-ui` which was never part of the self-hosted rollout.
- Not (as far as checked) a GitHub platform-wide outage — no way to confirm this from inside the session without
  external browsing, but the precision of "every workflow, every repo, on ONE account, right as spend crosses a
  plausible monthly figure" points at something account-specific rather than a general GitHub incident.

## Impact

**Every CI run on every repo in this fleet has been failing instantly for 2+ hours as of this writing.** This includes:
quality-gates-v2 (blocks ALL quickmerge → LDR → main promotion), the LDR→main promote-fleet cron, SIT, semver/release
tagging, and Cloud Build dispatch (`qg-passed` → `cloud-build-router`, itself gated on a GREEN quality-gates-v2 that can
never fire right now). Nothing merged or promoted through the normal pipeline can be CI-verified until this clears —
this session's own shipped commits from the last ~2 hours (Cloud Build Dockerfile fixes across 4 repos, the AO
slot-reserve-split, the AO pool-critical-halt feature) were all verified via **local** `quality-gates.sh` (same test
suite, run directly) before shipping, but have NOT had GitHub's own quality-gates-v2 confirm green, and cannot until
this clears.

## Recovery confirmed 2026-07-30 ~06:11 UTC

CI resumed at some point between 2026-07-30T00:27Z (PM's last observed `startup_failure`) and this check. Confirmed via
a fresh, deliberately-triggered run (not just a passive re-check):
`gh workflow run quality-gates-v2.yml --ref live-defi-rollout --repo IggyIkenna/unified-trading-pm` → run `30518827108`,
conclusion `failure` (a REAL failure, not `startup_failure`) — `gh api .../runs/30518827108/jobs` shows **8 real jobs
created** with real names/timestamps (`content sentinel`, `quality-gates-v2`, etc.), the categorically different
signature from the 0-jobs outage this doc tracks. Root cause (spending-limit cap vs. something else) was never confirmed
via API either way — the operator's own billing-UI check (todo below) still stands as the only way to close that out,
but the outage's _symptom_ (fleet-wide zero-jobs rejection) is verified cleared. The fresh run's own `failure`
conclusion is a separate, normal CI concern (not investigated here — this doc tracks the outage, not that specific run's
content).

## Todos

- [x] ✅ **RESOLVED 2026-07-31** — [OPERATOR] P1. This doc's own 06:11 UTC 2026-07-30 self-check below (claiming
      "symptom resolved") turned out to be a transient blip, not real recovery — the sibling doc
      `github_actions_billing_wall_recurrence_2026_07_29.md` independently re-confirmed the wall still fully active at
      the same 06:11-06:16Z timestamp and through the rest of 2026-07-30. Genuinely confirmed cleared 2026-07-31T08:16Z:
      real run durations on `unified-trading-pm` + a full 25m28s `quality-gates-v2` run and clean LDR→main promote chain
      on `instruments-service`. This doc is a duplicate write-up of the same incident as
      `github_actions_billing_wall_recurrence_2026_07_29.md` (the canonical doc, which carries the fuller timeline) —
      resolving both together.
- [x] ✅ [DATA] P1. **DONE 2026-07-30 ~06:11 UTC.** Re-checked whether CI has resumed via a fresh triggered run (not a
      passive check) — confirmed:
      `gh run list --repo IggyIkenna/unified-trading-pm --branch live-defi-rollout     --workflow quality-gates-v2.yml --limit 1`
      now shows real conclusions, not `startup_failure`/0 jobs.
- [x] ✅ **MIGRATED 2026-08-02** (operator ruling, `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 3) — both
      prevention todos below moved into `/plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Migrated
      prevention todos from resolved incidents" section. Original text preserved there verbatim with a source citation
      back to this doc.

## Why P0 / big-finding triage

Cross-repo, blocks the entire fleet's shipping pipeline, and is actively ongoing at time of filing — meets this
workspace's own "big finding" bar (cross-repo, CI/audit-priority) for immediate operator notification rather than quiet
logging.

## Progress Log

- **2026-07-31** — Wall confirmed genuinely cleared (see resolved OPERATOR todo above for evidence + the note on the
  06:11 UTC 2026-07-30 false-positive). `status` flipped to `resolved`. The remaining `[BACKEND]`/`[DATA]` todos
  (re-verify shipped commits went CI-green, separate the outage's contribution to the 2026-07-29 escalation spike) are
  standing hygiene follow-ups, left open.
