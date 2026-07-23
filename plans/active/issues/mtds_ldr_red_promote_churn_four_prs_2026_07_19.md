---
doc_type: issue
title:
  market-tick-data-service LDR→main promote PRs churn (4 PRs / 4h) because live-defi-rollout is red on quality-gates-v2
  at source
summary:
  The ldr_qg_failure escalation on market-tick-data-service has re-minted four LDR→main promote PRs (#632-#635) over ~4h
  (01:49Z-05:40Z 2026-07-19) with no escalation_resolved event. Root cause is NOT four independent worker fix-attempts
  failing — live-defi-rollout ITSELF is red on quality-gates-v2 (run 29674309292), so the standing ldr-to-main-promote
  cron re-mints a fresh promote PR every ~15min off a red LDR, each inheriting the same "QG slice (checks)" leg failure.
  Routine worker re-dispatch cannot clear it; the fix belongs on live-defi-rollout.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [ci-cd, quality-gates-v2, ldr-promote, promote-churn, ldr_qg_failure, escalation, market-tick-data-service]
related:
  - plans/active/issues/ao_open_issues_consolidated_close_out_2026_07_17.md
  - plans/active/issues/mtds_sentinels_qg_red_2026_07_13.md
created: 2026-07-19
parent_epic: infrastructure_master
priority: P1
source: [review-agent escalation msg 1456 + main-agent gh investigation]
assigned_vm:
resolved_by: unified-trading-pm@26b16c83
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-19
---

## What review flagged (msg 1456, 2026-07-19 ~06:04Z)

market-tick-data-service `ldr_qg_failure` has gone through FOUR distinct PR attempts (#632, #633, #634, #635) across ~4
hours (01:49Z–05:40Z), re-dispatched every ~15–50 min, with no `escalation_resolved` since the one-off fix at 23:38Z the
prior day. Review asked whether this is (a) a hard-to-fix root cause eluding each attempt or (b) something
flaky/environmental in the QG itself, and recommended a human look at #635 or a check of whether the failure signature
changed between attempts.

## What the investigation found (main agent, gh, repo `IggyIkenna/market-tick-data-service`)

Neither (a) nor (b) as framed — it is a **red-LDR promote loop**:

- #634 (head `37ac8a64b032`, **closed**) and #635 (head `c805e6cb27f6`, **open**) are both auto-minted
  `chore(promote): LDR → main (Option-B direct)` PRs — i.e. the standing `ldr-to-main-promote` automation, not worker
  feature PRs.
- **`live-defi-rollout` itself is red on `quality-gates-v2`** — run **29674309292 = failure** (branch
  `live-defi-rollout`). The promote PR carries `quality-gates-v2`, so every promote PR minted off a red LDR fails the
  same wall.
- The failing leg on the promote head (run **29674594581**, #635) is:
  `Quality Gates / QG slice (checks) → Run quality gates (leg checks)` → then
  `quality-gates-v2 → Aggregate slice results (gate the required context)`.
- Cadence fits: the promote cron re-mints a fresh promote PR every ~15 min → four PRs in four hours, each inheriting the
  identical checks-leg failure. This is **one stuck condition re-attempted**, not four independent fix attempts.

## Consequence

Routine worker re-dispatch of the promote PR **cannot** resolve this — the defect is on `live-defi-rollout`, not in the
promote PR. Do **not** keep re-dispatching #635. The LDR→main promote pipeline for market-tick-data-service is stalled
until LDR's checks-leg failure is repaired at source; the next promote PR then passes automatically.

## Evidence gap (needs repo-scoped access)

Main's workflow token 403s on `check-runs` and `gh run view --log-failed` returned empty, so the exact assertion could
not be extracted. To close the (a)-vs-(b) question definitively, someone with repo access should run:

```
gh run view 29674309292 --repo IggyIkenna/market-tick-data-service --log-failed   # the LDR run
gh run view 29674594581 --repo IggyIkenna/market-tick-data-service --log-failed   # the #635 promote run
```

If the same checks-leg signature appears on both → confirmed stuck-at-source (fix on LDR). If the LDR run's signature
differs run-to-run → environmental/flaky in the checks leg (harden the gate, not the code).

## Suggested resolution path

1. Pull the LDR checks-leg signature (commands above); identify the failing check(s) in the `checks` slice.
2. Fix the root cause on `live-defi-rollout` via a worker quickmerge (normal path).
3. Once LDR `quality-gates-v2` is green, let the next auto-minted promote PR carry through; close #635 and the
   `ldr_qg_failure` escalation.
4. Independent of the fix: consider making the promote automation **skip re-minting a promote PR while LDR's own
   `quality-gates-v2` is red** (avoids the 4-PR-in-4h churn signature that masked the real root cause).

## Cross-refs

- Consolidated tracking: `ao_open_issues_consolidated_close_out_2026_07_17.md`.
- Main↔review thread: orchestrator messages 1456 (review), 1458 (main reply with this diagnostic).

## Resolution (2026-07-22) — suggestion #4 implemented

`unified-trading-pm@26b16c83`. The historical #632-635 churn on market-tick-data-service is stale (resolved days ago);
what remained open was suggestion #4 — making the promote automation skip re-minting while LDR itself is red.
Investigation found this was **already partially built**: `ldr-to-main-promote-fleet.yml`'s Tier-A gate already blocks
on `ci_status=FAILING`, but it read ONLY the `workspace-manifest.json` cache — the HOURLY consolidator projection
(`codex/08-workflows/ci-cd-flow.md`: "manifest stays a fallback cache, read Firestore for live state"). That cache lag
is exactly why 4 PRs got minted against a genuinely-red LDR: `ci_status` hadn't caught up yet. Fixed by adding a LIVE
Firestore read (`ci_status_store.py get-doc --repo <repo>`, the SAME call the SIT gate a few lines down already trusts)
alongside the cached read — Tier-A now blocks if EITHER signal is `FAILING`, degrading safely to the cache alone if
Firestore is transiently unavailable (`get-doc` emits `{}` on failure, never silently reading as healthy). Verified:
both files' YAML parses clean, the live `ci_status_store.py get-doc` call was smoke-tested directly (correctly emits
`{}` + a logged warning when the Firestore SDK is unavailable, matching its documented fail-safe contract). Full PM
`quality-gates.sh` green.

**New finding, not fixed here (separate scope)**: `.github/workflows/ldr-to-main-promote-fleet.yml` (the deployed,
executing copy) has drifted significantly from its own `scripts/self-hosted-runners/hosted-baseline/` template — the
deployed copy is AHEAD by several undocumented-in-the-baseline fixes (self-hosted `[glue]` runner migration, the
2026-07-20 `breaking_scan_dir` source-dir fix, the 2026-07-20 HEAD-REF pin fix, the 2026-07-21 SIGPIPE fix). This fix
was applied identically to BOTH files to avoid adding to the drift, but the underlying baseline-staleness is the same
class of risk as `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` — a blind rollout from the
baseline would regress 4 real fixes. Worth its own audit/reconciliation pass; not attempted here given the scope and the
size of this specific workflow (~980 lines).
