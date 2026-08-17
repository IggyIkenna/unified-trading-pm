---
doc_type: issue
title: e2e-testing tier-DAG exemption never actually landed in code despite an archived "resolved" ruling
summary: >-
  Rediscovered the same tier-DAG violation (e2e-testing importing deployment-service) that
  e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md already investigated and archived as
  "resolved" (operator ruling 2026-08-16: exempt e2e-testing in TIER_EXEMPT_REPOS, mirroring deployment-service).
  The archived doc's own Progress Log claims the code change landed and was verified — but the actual
  fix-internal-dependency-alignment.py on disk only had "deployment-service" in TIER_EXEMPT_REPOS, not
  "e2e-testing". The claimed fix never reached the file. Completed it for real this time.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tier-architecture, manifest, dependency-alignment, evidence-backed-completion]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /plans/archive/2026_08/issues/e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-17"
last_updated: 2026-08-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: infra
locked_by:
resolved_by: "this session — added e2e-testing to TIER_EXEMPT_REPOS for real, verified 0 mismatches, shipped"
supersedes:
superseded_by:
source: discovered while shipping self_hosted_runner_billing_migration_wave2_remaining_2026_08_15.md's final todo
drift_direction: advance-code
depends_on: []
---

# e2e-testing tier-DAG exemption never actually landed despite an archived "resolved" ruling

## What was found

Running `python3 scripts/manifest/fix-internal-dependency-alignment.py --apply` still produced a fresh
`TIER_VIOLATION` for `[e2e-testing] imports [deployment-service]` — the exact same failure
`/plans/archive/2026_08/issues/e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md` documents as
resolved via an operator ruling (2026-08-16, "RULED: option (a) — exempt e2e-testing, mirroring deployment-service").
That archived doc's own Progress Log claims: *"Implemented and verified... added `e2e-testing` to
`TIER_EXEMPT_REPOS`... Verified directly: `is_tier_violation('e2e-testing', 'deployment-service', tier_map)` now
returns `False`."*

**The claim was false, or the change was lost.** Reading `scripts/manifest/fix-internal-dependency-alignment.py`
directly showed `TIER_EXEMPT_REPOS = frozenset({"deployment-service"})` — no `"e2e-testing"` entry. Whatever
verification that session ran, the actual file never carried the change (possibly lost to an autostash/rebase
collision — this shared PM checkout has hit several of those this session, see `pm_repo_commit_rate_exceeds_
precommit_hook_duration_2026_08_10.md`).

## Fix (completed, not just claimed)

Added `"e2e-testing"` to `TIER_EXEMPT_REPOS` in `scripts/manifest/fix-internal-dependency-alignment.py`, matching the
already-decided operator ruling. Verified directly this time:

```
$ python3 scripts/manifest/fix-internal-dependency-alignment.py --apply
Planned 0 action(s)
OK: 0 internal mismatches.
$ python3 scripts/manifest/check-dependency-alignment.py --json
{"aligned": true, "issues": [], "count": 0, "disk_absent": [], "disk_absent_count": 0}
```

`workspace-manifest.json` itself needed no change (the exemption means the tool no longer objects to the manifest's
existing state — confirmed via `git diff` showing empty after a canonical-format re-run).

Shipped: `unified-trading-pm@8c4bee9592`.

## Lesson

An archived issue doc's "Implemented and verified" Progress Log entry is not proof the change is actually live —
this workspace's own measurement-claims-discipline rule (`CLAIM ≤ MEASUREMENT`) applies to closed issues too, not
just live claims. Confirmed the fix by reading the actual current file content, not by trusting the archived doc's
narrative.

## Todos

- [x] [DOC] P2. Verify whether the archived doc's "Implemented and verified" claim actually reached the file —
      confirmed FALSE via direct read of `fix-internal-dependency-alignment.py`.
- [x] [SCRIPT] P2. Add `"e2e-testing"` to `TIER_EXEMPT_REPOS`, verify 0 mismatches, ship. DONE —
      `unified-trading-pm@8c4bee9592`.
