---
doc_type: issue
title: slot-13 mistakenly re-widened fastapi ceiling to <0.138.0 fleet-wide — reverted, aligns with slot-3's resolution
summary: |
  While shipping the click/pillow pip-audit fix batch (system_integration_tests_pip_audit_red-003), slot-13 hit
  PM's STAGE 1.5 dependency-alignment gate failing because ml-service's fastapi<0.138.0 declaration didn't match
  the canonical <0.137.0. Without first re-syncing against the latest PM state, slot-13 concluded the canonical
  ceiling itself was stale and widened it to <0.138.0, then propagated that widen declaratively across 13 other
  fastapi-consuming repos. This directly contradicted an already-shipped, independently-investigated resolution
  (unified-trading-pm@1ea525c6e, resolved_by slot-3, same day) that deliberately kept canonical at <0.137.0 and
  added a narrow PER_REPO_EXTERNAL_EXCEPTIONS carve-out for ml-service only, because slot-3 had directly verified
  fastapi==0.137.2 + starlette==1.3.1 still reproduces the `_IncludedRouter`/`.path` route-introspection break.
  Discovered mid-batch (7 repos already pushed the widen, 6 more committed locally) via a routine read of the
  Phase-1 strategy-service risk plan, which referenced the exception mechanism. All 13 repos reverted back to
  <0.137.0; the 7 already-pushed repos got explicit revert commits + fresh QG + quickmerge; the 6 unpushed repos
  had the bad commit simply dropped (never left local disk).
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-library,
    agent-orchestrator,
    market-tick-data-service,
    greeks-service,
    alerting-service,
    deployment-api,
    features-service,
    execution-service,
    client-reporting-api,
    fund-administration-service,
    unified-trading-api,
    deployment-service,
    strategy-service,
  ]
scope: [engineer]
tags: [dependency-alignment, fastapi, starlette, ssot-contradiction, canonical-manifest, self-correction]
related:
  [
    plans/active/issues/canonical_fastapi_ceiling_stale_vs_ml_service_2026_07_13.md,
    plans/active/issues/system_integration_tests_pip_audit_red_2026_07_13.md,
    plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    workspace-constraints.toml,
    canonical-dependency-manifest.json,
    scripts/manifest/check-dependency-alignment.py,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source: self-discovered by slot-13 mid-batch, 2026-07-13, while reading utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md
assigned_vm: planning
resolved_by:
  slot-13 (all 5 todos verified/flipped 2026-07-13, closing the loop on work substantially done by slots 7/9/15)
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: revert-to-canonical
depends_on: []
---

## What happened

I (slot-13) was working `system_integration_tests_pip_audit_red-003`: bump click/pillow/soupsieve floors fleet-wide for
pip-audit CVEs. While re-locking, PM's `check-dependency-alignment.py` STAGE 1.5 gate started failing because
ml-service's already-shipped fastapi CVE fix (`fastapi>=0.115.0,<0.138.0` + `override-dependencies starlette>=1.3.1`,
from a **separate**, already-resolved issue) didn't strictly equal the canonical `fastapi>=0.115.0,<0.137.0`.

I treated this as "the canonical is stale, widen it" and, with what I believed was operator sign-off, widened
`workspace-constraints.toml`'s fastapi ceiling to `<0.138.0` and propagated that declaratively (no `uv.lock` re-resolve)
across all 13 other fastapi-consuming repos. **I did not first check whether this exact contradiction had already been
investigated and resolved.** It had: `unified-trading-pm@1ea525c6e` (resolved_by slot-3, same day) is the actual fix —
see
[`canonical_fastapi_ceiling_stale_vs_ml_service_2026_07_13.md`](canonical_fastapi_ceiling_stale_vs_ml_service_2026_07_13.md).
Slot-3 directly tested both combinations in isolated venvs and found:

- `fastapi==0.137.2` + `starlette==1.3.1` (what a canonical `<0.138.0` ceiling permits): **still reproduces** the
  `_IncludedRouter` break (no `.path` attribute on included-router routes).
- `fastapi==0.136.3` + `starlette==1.3.1` (ml-service's _actual_ locked resolution, forced low via
  `override-dependencies`): does **not** reproduce.

Slot-3's conclusion: keep the canonical ceiling at `<0.137.0` fleet-wide (nobody else should risk landing on the broken
`0.137.x` range), and instead added
`PER_REPO_EXTERNAL_EXCEPTIONS = {("ml-service", "fastapi"): "fastapi>=0.115.0,<0.138.0"}` to
`check-dependency-alignment.py` as a narrow, reviewed, single-repo carve-out — with an explicit comment: "do not raise
the canonical fastapi/starlette ceiling fleet-wide off the back of this exception."

My batch did exactly the thing that comment warns against, across 13 repos.

## How I found it

Reading `plans/archive/2026_07/utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md` for an unrelated reason surfaced a
reference to the exception mechanism, which didn't match what I'd just shipped. Diffed my local
`workspace-constraints.toml` against `origin/live-defi-rollout` and found slot-3's commit
(`1ea525c6e fix(deps): resolve fastapi/starlette canonical-ceiling contradiction with ml-service`) had already landed,
with the opposite decision from mine.

## What I fixed

Ground-truth audit of all 13 touched repos (`git log origin/live-defi-rollout..HEAD` per repo, not trusting my own prior
progress notes — those turned out to be stale/inaccurate in a couple of cases, e.g. I'd believed execution-service's and
strategy-service's pillow/click fixes were already pushed; they weren't):

**7 repos had the fastapi widen already pushed to origin** — reverted via a fresh commit + full `quality-gates.sh` +
`quickmerge.sh` cycle each (declarative-only, ceiling text only, no `uv.lock` change): unified-trading-library,
agent-orchestrator, market-tick-data-service, greeks-service, alerting-service, deployment-api, features-service.

**6 repos had the fastapi widen only as an unpushed local commit** — dropped via `git reset --hard` to the pre-widen
commit (nothing ever reached origin, so no revert commit needed); this also uncovered and preserved legitimate,
still-unshipped pillow/click commits underneath the bad fastapi commit in 2 of them (execution-service,
strategy-service) that my own earlier progress narrative had incorrectly logged as already-shipped: execution-service,
client-reporting-api, fund-administration-service, unified-trading-api, deployment-service, strategy-service.

**PM canonical files** (`workspace-constraints.toml`, `canonical-dependency-manifest.json`): reverted the fastapi line
back to `<0.137.0` (matching origin exactly), kept the legitimate click floor bump (`>=8.3.2` → `>=8.3.3`, matching the
corrected PYSEC-2026-2132 fix-version found later in the same batch). Re-ran `check-dependency-alignment.py --json`
after the revert — confirmed the only remaining mismatches are the ones this issue is actively fixing (the 7 repos'
revert commits mid-flight at time of writing).

## Why this is a P1 finding, not just a quiet fix

- It's a cross-repo SSOT contradiction I introduced against another slot's already-shipped, security-driven,
  empirically-verified decision — exactly the CLAUDE.md "big finding" category (cross-repo / SSOT contradiction).
- It touched 7 repos on the shared `live-defi-rollout` branch before being caught.
- Root cause worth naming: I encountered the alignment-gate failure, formed a hypothesis ("canonical is stale"), and
  acted on a large blast-radius fix without first checking whether the specific contradiction had already been triaged
  by someone else working the same file that same day. The fix for next time: **before widening a shared canonical
  constraint to resolve an alignment-gate failure, grep `plans/active/issues/` for the package name first** — a
  same-day, same-file conflict is exactly the kind of thing a fast-moving multi-agent fleet produces.

## Todos

- [x] ✅ [BACKEND] P1. Revert PM canonical files (`workspace-constraints.toml`, `canonical-dependency-manifest.json`)
      fastapi line back to `<0.137.0`; keep the click `>=8.3.3` floor. Verified against `origin/live-defi-rollout`
      byte-for-byte on the fastapi line.
- [x] ✅ [BACKEND] P1. Revert the 6 unpushed repos (execution-service, client-reporting-api,
      fund-administration-service, unified-trading-api, deployment-service, strategy-service) via `git reset     --hard`
      to the pre-widen commit; confirmed no other local work was lost (checked `git log origin/live-defi-rollout..HEAD`
      per repo before resetting).
- [x] ✅ [BACKEND] P1. Revert the 7 already-pushed repos (unified-trading-library, agent-orchestrator,
      market-tick-data-service, greeks-service, alerting-service, deployment-api, features-service) via a fresh commit +
      `quality-gates.sh` + `quickmerge.sh` each. Confirmed 2026-07-13 (slot-13): all 7
      `revert(deps): restore fastapi     ceiling to <0.137.0 (undo declarative widen)` commits are on
      `origin/live-defi-rollout` (fresh-pulled each repo, `ahead=0` vs origin) with `pyproject.toml` declaring the
      canonical `fastapi>=0.115.0,<0.137.0` byte-for-byte — unified-trading-library@f5eb0c86,
      agent-orchestrator@77d53bc, market-tick-data-service@fb88b76b, greeks-service@bd1fa4a, alerting-service@50c7032,
      deployment-api@edc9608, features-service@65cae051. Every subsequent `quality-gates-v2` CI run on each repo since
      these commits landed is green (spot-checked unified-trading-library: GH run 29290645816 conclusion=success at
      current HEAD, which descends from f5eb0c86). This matches the P0 VERIFY todo below, which independently confirmed
      the same fleet-wide alignment — that todo's checkbox was already flipped but this one wasn't; closing the gap.
- [x] ✅ [VERIFY] P0. After all 7 revert-quickmerges land, re-run `check-dependency-alignment.py --json` fleet-wide and
      confirm zero mismatches (aside from the intentional ml-service exception). Verified 2026-07-13 (slot 7):
      fresh-pulled all 7 repos (unified-trading-library, agent-orchestrator, market-tick-data-service, greeks-service,
      alerting-service, deployment-api, features-service) to `origin/live-defi-rollout` — each `pyproject.toml` now
      declares `fastapi>=0.115.0,<0.137.0`, matching canonical byte-for-byte, confirming the revert-quickmerges landed.
      Ran `.venv/bin/python scripts/manifest/check-dependency-alignment.py --json` fleet-wide:
      `{"aligned": true, "issues": [], "count": 0, "disk_absent": [], "disk_absent_count": 0}` — zero mismatches. Note:
      the ml-service-only exception this todo anticipated has since been superseded by a broader, separately-resolved
      `PER_REPO_EXTERNAL_EXCEPTIONS` set (`unified-trading-pm@d4ad81d40` + `c5d4a72af`, tracked in
      `dependency_alignment_red_multi_repo_ceiling_drift_2026_07_13.md`, already CLOSED) covering ml-service +
      unified-trading-library + alerting-service + greeks-service + market-tick-data-service + deployment-api +
      agent-orchestrator + unified-trading-api at `<0.138.0` headroom — but since all 7 repos here declare the exact
      canonical `<0.137.0` (not exercising that headroom), the alignment check passes on direct canonical match, not via
      the exception path. No contradiction with this todo's intent.
- [x] ✅ [BACKEND] P1. Resume the original click/pillow/soupsieve batch
      (`system_integration_tests_pip_audit_red_2026_07_13.md`) to completion on the corrected baseline. Confirmed
      2026-07-13 (slot-13): that issue doc is already `status: resolved` with both its own todos checked — slot-15
      shipped the interim per-repo fix (`system-integration-tests@6d7a5b6`), slot-9 shipped the canonical fleet-wide
      bump (`unified-trading-pm@210d448c1`, added the missing `soupsieve>=2.8.4,<3.0.0` floor). Verified the corrected
      baseline holds in `workspace-constraints.toml`: `click>=8.3.3,<9.0.0`, `fastapi>=0.115.0,<0.137.0`,
      `pillow>=12.3.0,<13.0.0`, `soupsieve>=2.8.4,<3.0.0`. Ran
      `.venv/bin/python scripts/manifest/check-dependency-alignment.py --json` fleet-wide:
      `{"aligned": true, "issues": [], "count": 0, "disk_absent": [], "disk_absent_count": 0}` — zero mismatches. No
      further code change needed; this todo was tracking work already completed by other slots under separate issue
      docs.
