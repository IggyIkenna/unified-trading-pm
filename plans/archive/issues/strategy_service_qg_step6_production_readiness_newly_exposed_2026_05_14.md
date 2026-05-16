---
title: "strategy-service QG step 6 production readiness validators fail — newly exposed after step 3.5 fixed"
created: 2026-05-14
author: harsh-main-review
source:
  - harsh_orchestrator/pings/slot_4.md
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## What I found

Slot 4 (2026-05-14 04:50 UTC) reported that after fixing the step 3.5 import-pattern violations
(strategy-service@3ff75a2), a pre-existing step 6 "production readiness validators" failure became visible. The failure
was hidden behind the step 3.5 error. Slot 4 noted it as "pre-existing, not caused by my changes; needs PM-level triage"
but did not file an issue doc.

Step 6 in `base-service.sh` runs
`unified-trading-pm/codex/scripts/run-all-validators.sh --asset-group all --failed-only` and fails with "fix
unified-trading-pm/workspace-manifest.json and plans/active/\*.md". The exact validator output was not captured in the
ping — needs a QG run to get the full failure message.

Note: strategy-service already sets `MANIFEST_ALIGNMENT_SKIP=true` (for the import-alignment step 4), but step 6 is the
separate production-readiness validators check.

## Why it matters

Step 6 failure causes `bash scripts/quality-gates.sh` to exit non-zero for strategy-service. This means Pass 1 QG is
currently broken for strategy-service, which blocks quickmerge and prevents CI-clean merges. Any slot working on
strategy-service will hit this failure.

## Recommended decision

1. Run `cd strategy-service && bash scripts/quality-gates.sh 2>&1 | grep -A5 "PRODUCTION READINESS"` to capture the
   exact failure.
2. If the failure is a stale `workspace-manifest.json` ci_status field, update it via the PM-level validator script or
   fix the manifest entry for strategy-service.
3. If it is a plan-validator failure (plans/active/\*.md out of spec), triage the offending plan.
4. Re-run QG to confirm green after fix.

execution: owner: slot 4 cadence: one-shot verifier: bash scripts/quality-gates.sh exit code 0 in strategy-service
last_executed: 2026-05-16 (validators ran clean — see Resolution below)

## RESOLVED — 2026-05-16 (slot 4 cross-slot pickup)

Re-ran `bash codex/scripts/run-all-validators.sh --asset-group all --failed-only` on rebased PM tab today; all 3
production-readiness validators return OK:

```text
OK: All checklists have phase_9_deployable_enhancements (items 38-41)
OK: workspace-manifest.json valid (schema + topological)
OK: No broken links in plans/active/*.md
```

The 2026-05-14 failure was a transient state from in-flight manifest/plan churn during the freeze-gate cycle.
Subsequent slot 1 main + slot 8 commits (workspace-manifest refresh + plan-archival sweep + cross_asset_group audit
phase shipments) brought the workspace back to OK. Issue closeable at next archive sweep.

Cross-link: PM workspace-validators clean as of `unified-trading-pm@HEAD` 2026-05-16 20:08 UTC.
