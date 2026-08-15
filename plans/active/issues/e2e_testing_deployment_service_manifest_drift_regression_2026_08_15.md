---
doc_type: issue
title: >-
  quickmerge STAGE 1.5 dependency-alignment is RED for every unified-trading-pm push — a "fixed" commit reintroduced the
  e2e-testing→deployment-service manifest drift it claimed to resolve
summary: >-
  `quickmerge.sh`'s PM-only STAGE 1.5 (Dependency Alignment) currently fails for ANY unified-trading-pm push, confirmed
  byte-identical before/after an unrelated change. Root cause: `unified-trading-pm@3f3fd16221` ("fix
  e2e-testing/deployment-service manifest drift") removed the `deployment-service` manifest entry that
  `unified-trading-pm@c098b02fe5` had added for e2e-testing's Phase-6 revocation black-box tests — but left the actual
  `pyproject.toml` dependency declaration + the 4 test files that import it untouched, so
  `check-dependency-alignment.py` immediately finds the exact same drift again. Re-adding the manifest entry is blocked
  by `fix-internal-dependency-alignment.py`'s own TIER_VIOLATION check (e2e-testing importing deployment-service breaks
  the tier DAG) — a genuine, unresolved tension between e2e-testing's black-box-testing design and the generic tier
  enforcement, not a simple manifest-sync bug.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, e2e-testing, deployment-service]
scope: [engineer, admin]
tags: [cross-repo, ci-cd, quickmerge, dependency-alignment, tier-dag, e2e-testing, manifest-drift]
related:
  [
    /plans/active/issues/self_hosted_runner_billing_migration_wave2_remaining_2026_08_15.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch14_2026_08_15.md,
  ]
created: "2026-08-15"
author: slot-7
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-08-15 (slot 7) while shipping ci_satellite_ao_dispatch_batch14_2026_08_15.md item 6 — quickmerge
    STAGE 1.5 blocked the push; verified pre-existing by checking out HEAD~1 (identical failure) before/after",
  ]
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    scripts/quickmerge.sh,
    scripts/manifest/check-dependency-alignment.py,
    scripts/manifest/fix-internal-dependency-alignment.py,
  ]
---

# quickmerge STAGE 1.5 dependency-alignment RED for every PM push — a claimed fix reintroduced the drift

## What I found

While shipping an unrelated `.github/workflows/sit-unlock.yml` change (`ci_satellite_ao_dispatch_batch14_2026_08_15.md`
item 6), `bash scripts/quickmerge.sh ... --agent --files '.github/workflows/sit-unlock.yml'` failed at **STAGE 1.5:
Dependency Alignment (PM)** with:

```
[unified-trading-pm] ❌ Dependency alignment FAILED
```

`python3 scripts/manifest/check-dependency-alignment.py --json` reports exactly one issue:

```json
{ "repo": "e2e-testing", "type": "internal_in_pyproject_not_manifest", "dep": "deployment-service" }
```

**Verified pre-existing, not caused by my change**: checked out `HEAD~1` content (before my commit), re-ran the same
check — byte-identical failure. This blocks STAGE 1.5 for **any** unified-trading-pm push right now, not just mine.

**Root cause, traced via `git log --all`:**

1. `unified-trading-pm@c098b02fe5` ("register e2e-testing -> deployment-service dependency (Phase 6 revocation black-box
   tests)") added a `deployment-service` entry to e2e-testing's manifest dependency list — correctly, since
   `e2e-testing/pyproject.toml` genuinely declares `deployment-service>=0.132.0,<1.0.0` (with an explicit comment citing
   `alert_driven_dependency_revocation_2026_08_12.md` Phase 6) and 4 test files under `tests/integration/revocation/`
   actually import `deployment_service` internals for black-box testing.
2. `unified-trading-pm@3f3fd1622195` ("...fix e2e-testing/deployment-service manifest drift...") **removed that exact
   manifest entry** (`git show 3f3fd16221 -- workspace-manifest.json` — a clean 5-line deletion, nothing else touched in
   the manifest). The commit message claims this FIXES the drift; it actually reintroduces the exact drift `c098b02fe5`
   had fixed, because `pyproject.toml`'s `deployment-service` dependency (and the 4 importing test files) were left
   untouched — `check-dependency-alignment.py` now finds the manifest missing an entry the pyproject.toml (correctly)
   still declares.
3. Attempting the straightforward re-fix (`python3 scripts/manifest/fix-internal-dependency-alignment.py --apply`, under
   `.venv` — the bare system `python3` is missing `tomli_w`, a separate minor footgun) does **not** just re-add the
   entry: it refuses, printing
   `TIER_VIOLATION (architectural change required): [e2e-testing] imports [deployment-service] — add_to_manifest would violate tier DAG. Fix: move shared code to a lower tier, or restructure dependency.`
   So `3f3fd1622195`'s author likely hit this same TIER_VIOLATION and "fixed" it by removing the manifest registration
   rather than the (still-present, still-imported) dependency — leaving the alignment checker and the tier-DAG checker
   in permanent disagreement: one wants the entry present (pyproject.toml has it), the other refuses to let it be added
   (tier DAG).
4. A **stale claim** already exists in the corpus:
   `plans/active/issues/self_hosted_runner_billing_migration_wave2_remaining_2026_08_15.md` line 60-61 lists
   "e2e-testing/deployment-service manifest drift" as one of two "unrelated pre-existing blockers" that
   `unified-trading-pm@3f3fd16221` fixed — per this investigation, that specific claim is now false (or was already
   false at the time — the removal IS that commit's own diff).

## Why it matters

- **Blocks every unified-trading-pm quickmerge push** (STAGE 1.5 runs unconditionally for PM) — high blast radius, not
  scoped to CI docs; any worker landing a code or workflow change to PM hits this.
- **e2e-testing's Phase-6 revocation black-box tests are a genuine, intentional design** (per the doc's own comment)
  that legitimately needs to import a service's internals for black-box coverage — the generic tier-DAG check has no
  test-repo exemption, so this is a real architecture-vs-tooling tension, not a simple sync bug. Silently re-adding the
  manifest entry would just re-trip the tier-DAG gate elsewhere; silently leaving it removed leaves STAGE 1.5
  permanently red.

## Recommended decision

Two independent fixes, different scopes:

1. **[DOC] Correct the stale claim** in `self_hosted_runner_billing_migration_wave2_remaining_2026_08_15.md` (line
   60-61) — the "e2e-testing/deployment-service manifest drift" fix claim is not currently true; either strike it or
   annotate that it regressed.
2. **[OPERATOR] Resolve the tier-DAG vs. e2e-testing-black-box-testing tension** — pick one: (a) special-case
   e2e-testing (or `assigned_role: e2e`/testing-tier repos generally) as exempt from the tier-DAG check in
   `fix-internal-dependency-alignment.py`/`check-dependency-alignment.py`'s tier model, since black-box integration
   tests importing service internals is the repo's whole purpose; (b) restructure the revocation tests to depend on a
   published test-fixture/interface package instead of `deployment-service` directly, preserving the tier DAG; (c)
   accept the drift permanently and make STAGE 1.5 warn-only for this one named (repo, dep) pair. This is an
   architectural call, not a mechanical fix — needs operator direction before a worker implements either option.

## Todos

- [ ] [OPERATOR] P1. **Decide the tier-DAG vs. e2e-testing-black-box-testing resolution path** (see "Recommended
      decision" option a/b/c above) — genuine architectural judgment call, not worker-determinable. Gate: an operator
      ruling recorded here, then re-tag `[OPERATOR]` → the implementing craft tag.
- [ ] [DOC] P2. **Correct the stale "e2e-testing/deployment-service manifest drift" fix claim** in
      `plans/active/issues/self_hosted_runner_billing_migration_wave2_remaining_2026_08_15.md` (line 60-61) — annotate
      that `unified-trading-pm@3f3fd1622195` actually reintroduced this drift (see this doc's "What I found" §2), not
      fixed it. Gate: the referenced line no longer claims this is fixed without qualification.

## Progress Log

- **2026-08-15 (slot 7)**: filed while shipping `ci_satellite_ao_dispatch_batch14_2026_08_15.md` item 6 — quickmerge
  STAGE 1.5 blocked the unrelated ship; root-caused via `git log --all` + `git show`, confirmed pre-existing via a
  HEAD~1 byte-identical re-check. Did not attempt either fix option myself (both need operator judgment or touch files
  outside this task's scope) — used the documented dirty-deps direct-push carve-out
  (`Quickmerge: direct-carveout-dirty-deps`) to land the unrelated sit-unlock.yml fix instead of blocking on this.
