---
doc_type: issue
title:
  "cloud-build-router's Cloud Build 'regional fallback' (Task 7) has retried the SAME region as primary since 2026-04-15
  — CLOUD_BUILD_FALLBACK_REGION was silently regressed to equal CLOUD_BUILD_REGION, and the true fallback region
  (us-central1) has zero Cloud Build triggers provisioned anyway"
summary: >-
  Dispatched to resolve escalation agt-cb29da (cloud_build_router_failure, wall_type=cloud_build_router_failure,
  instruments-service prod, "primary region asia-northeast1 failed, build ran in fallback region"). Verified LIVE that
  this specific escalation is a STALE re-dispatch of an ALREADY-FIXED false positive: commit be54f43dac (slot-26,
  2026-08-13 19:19:33Z, "fix(ci): router trigger_build_in_region emits only build ID on stdout") explicitly names
  escalation agt-cb29da as the false-positive it fixed — a diagnostic `echo` to stdout inside `trigger_build_in_region`
  corrupted the captured BUILD_ID, which zeroed out `build_region`/`build_exit_code`/`build_failure_reason` at job
  level, which then spuriously fired `escalate-regional-fallback` even though the real Cloud Build SUCCEEDED in the
  primary region. Confirmed via `gcloud builds list --project=central-element-323112 --region=asia-northeast1
  --filter="substitutions._REPO_NAME=instruments-service"`: builds have gone SUCCESS in asia-northeast1 continuously
  before AND after the fix (last 10, 2026-08-12T14:50 through 2026-08-14T01:19, all SUCCESS) — the primary region was
  never actually unavailable. cloud-build-router itself has no auto-poll resolution for this wall type
  (`escalation.py`'s `_QG_SIGNAL_WALLS` doesn't include it, per cicd.md's documented known gap), so the already-fixed
  instance re-dispatched a fresh worker (me) on the deadline-reescalation cycle. No further fix needed for THIS
  escalation — closing as resolved-on-arrival.

  SEPARATE finding made while diagnosing the above (same file): `CLOUD_BUILD_FALLBACK_REGION` has been set equal to
  `CLOUD_BUILD_REGION` (both `asia-northeast1`) since commit f44be2f7ae (semver-rollout[bot], 2026-04-15, buried inside
  an unrelated 15-file "chore: snapshot today's work" bulk commit whose message claims "cloud-build-router fix"). Prior
  to that commit the fallback was `us-central1` — a genuinely different region. Checked live: `gcloud builds triggers
  list --project=central-element-323112 --region=us-central1` returns ZERO triggers (vs 31 in asia-northeast1), so even
  reverting the env var to `us-central1` would not restore real regional redundancy today — every fallback attempt there
  would hit the same `NOT_FOUND`-class failure the `trigger_build_in_region` function already handles. Task 7's
  "Regional fallback for Cloud Build" (workflow header, added 2026-03-13) is therefore currently same-region
  retry-on-transient-error only, not genuine cross-region redundancy — which is a reasonable fallback behavior on its
  own merits (retries clear transient quota/429/503 blips, which is what actually happened here) but is mislabeled
  everywhere it's surfaced (env var name, Telegram/escalation message text both say "fallback region" and imply a
  different region), which is exactly what made this escalation's wording read as a regional outage when it was not one.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, cloud-build-router, regional-fallback, escalation, false-positive, stale-escalation]
related:
  [/codex/08-workflows/ci-cd-flow.md, /plans/archive/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md]
context_scope:
  [
    .github/workflows/cloud-build-router.yml,
    agent-orchestrator/server/escalation.py,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-14
priority: P3
parent_epic: ci_master
source:
  [
    "Dispatched as cicd-role escalation agt-cb29da (wall_type=cloud_build_router_failure, repo=instruments-service),
    slot 15, 2026-08-14. Verified the wall was already resolved by a prior worker's commit and filed this doc per
    cicd.md's 'verify LIVE, note it in the issue doc, close out' instruction for that known gap.",
  ]
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
last_updated: 2026-08-21
---

# cloud-build-router regional-fallback: stale escalation + a real but non-urgent mislabeling gap

## What I found

1. **Escalation agt-cb29da is resolved-on-arrival.** `trigger_build_in_region`'s diagnostic
   `echo "Attempting build trigger in region: $region"` used to go to stdout, polluting the captured `BUILD_ID` and
   zeroing every downstream `$GITHUB_OUTPUT` field. That made `escalate-regional-fallback` fire even when the
   primary-region build genuinely succeeded. Fixed by commit `be54f43dac` (2026-08-13 19:19:33Z, on `origin/main`
   already) — its own commit message names this exact escalation ID. `gcloud builds list` shows the primary region
   (`asia-northeast1`) has been green continuously across the fix boundary (2026-08-12 through 2026-08-14, 10/10 SUCCESS
   sampled) — there was never a real regional outage.
2. **`escalate-regional-fallback` / `cloud_build_router_failure` has no auto-poll close signal** (cicd.md's documented
   gap — not in `escalation.py`'s `_QG_SIGNAL_WALLS`), so this already-fixed wall re-dispatched a fresh worker on the
   deadline-reescalation cycle instead of auto-resolving once the fix landed. This is the SAME known-gap class the
   `utl_prod_cloud_build_trigger_missing_fleet_stale_base_image_2026_07_25.md` issue also hit twice.
3. **Separate, still-live gap**: `CLOUD_BUILD_FALLBACK_REGION` (`.github/workflows/cloud-build-router.yml` line 61) has
   equaled `CLOUD_BUILD_REGION` (both `asia-northeast1`) since 2026-04-15 (`f44be2f7ae`, a bot bulk-commit whose message
   claims "cloud-build-router fix" — previously `us-central1`). `us-central1` currently has 0 Cloud Build triggers
   provisioned (checked live, vs 31 in `asia-northeast1`), so this isn't a simple one-line revert: reverting the env var
   alone would just swap one always-failing fallback path for another. Task 7 ("Regional fallback for Cloud Build",
   workflow header) is effectively same-region retry-on-transient-error today, which is a defensible behavior in its own
   right, but every surface that describes it (`CLOUD_BUILD_FALLBACK_REGION` name, the escalation/Telegram message text
   "primary region X failed, build ran in fallback region Y") still claims cross-region redundancy — exactly the framing
   that made THIS escalation read as "diagnose why the primary region is unavailable" when the primary region was fine
   and no second region was ever actually tried.

## Why it matters

Low urgency (the retry-on-same-region behavior is not currently causing failed deploys — every sampled build recovers
within one retry), but the messaging gap will keep generating confusing "primary region unavailable, diagnose why"
escalations for what is actually a transient-error retry succeeding as designed. A future genuine multi-hour regional
outage in `asia-northeast1` would also get ZERO real redundancy from Task 7 as currently configured, silently — the
same-region "fallback" would just fail the same way the primary did.

## Recommended decision

- [ ] [INFRA] P3. Rename `CLOUD_BUILD_FALLBACK_REGION` (and the escalation + Telegram message wording, both in
      `.github/workflows/cloud-build-router.yml`) to stop claiming cross-region fallback — per D51 ruling
      (ADOPTED-REC 2026-08-21, "no observed failure needed cross-region redundancy; the fix is cheap and prevents
      documented false-alarm triage"): accept same-region retry-on-transient-error as the permanent design (option
      B). Done when: the env var name and both message templates no longer imply a second region exists, and
      `quality-gates.sh` passes green.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (2 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:ff32366ad3f7d910]: KEEP-NA, valid — sole open item is an [OPERATOR] decision between provisioning real 2nd-region infra vs accepting same-region retry as permanent design; doc's own text calls it not worker-determinable.

- **2026-08-21 — ruling D51 (Cloud Build 'fallback' naming)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Rename — no observed failure needed cross-region redundancy; the fix
  is cheap and prevents documented false-alarm triage. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
