---
doc_type: issue
title: e2e-testing imports deployment-service — tier-DAG violation blocking manifest alignment
summary: >-
  workspace-manifest.json's dependency-alignment tool refuses to auto-add an e2e-testing -> deployment-service
  edge because it violates the tier DAG, but e2e-testing's own pyproject.toml now genuinely declares the import.
  Found as a side effect of an unrelated PM housekeeping ship (orphaned script deletion), not triaged.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tier-architecture, manifest, dependency-alignment]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
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
locked_since:
resolved_by:
supersedes:
superseded_by:
source: discovered while shipping self_hosted_runner_billing_migration_wave2_remaining_2026_08_15.md's final todo
drift_direction: advance-code
depends_on: []
---

# e2e-testing imports deployment-service — tier-DAG violation

## What was found

Running `python3 scripts/manifest/fix-internal-dependency-alignment.py --apply` in `unified-trading-pm` produces:

```
TIER_VIOLATION (architectural change required):
  [e2e-testing] imports [deployment-service] — add_to_manifest would violate tier DAG
  Fix: move shared code to a lower tier, or restructure dependency.
```

`check-dependency-alignment.py --json` confirms the same mismatch:
`{"repo": "e2e-testing", "type": "internal_in_pyproject_not_manifest", "dep": "deployment-service"}` — i.e.
e2e-testing's own `pyproject.toml` genuinely declares a `deployment-service` dependency, but
`workspace-manifest.json` does not (and the tool won't auto-add it, since doing so would encode a
tier-architecture violation into the manifest).

## What is NOT yet known

- **When/why this import was added** — not investigated. Could be a legitimate new test (e2e-testing exercising
  deployment-service's API/behavior directly) or an accidental/leftover dependency from some other change.
- Whether e2e-testing is even subject to the same tier constraints as the service tiers (`/codex/04-architecture/
  tier-and-import-architecture.md` — worth confirming e2e-testing's own tier classification before assuming this
  is a real violation vs. a tool limitation for test-harness repos).
- Whether `workspace-manifest.json` currently reflects the OLD (pre-import) state cleanly, or whether other
  drift has also accumulated there — this session only reverted a local, already-stale realignment attempt from
  an earlier point in the day; it did not investigate the manifest's current overall accuracy.

## Todos

- [ ] [OPERATOR] P2. Determine whether e2e-testing's dependency on deployment-service is legitimate (new test
      coverage) or accidental. If legitimate: either add `e2e-testing` as a tier-exempt case in
      `check-dependency-alignment.py` (if e2e-testing genuinely isn't subject to the same tier DAG as services —
      confirm via `/codex/04-architecture/tier-and-import-architecture.md`), or restructure per the tool's own
      suggestion (move the shared code e2e-testing needs to a lower tier). If accidental: remove the
      `deployment-service` dependency from e2e-testing's `pyproject.toml`. Repo: e2e-testing.
- [ ] [SCRIPT] P2. Once the above is resolved, re-run `python3 scripts/manifest/generate-derived-manifest.py` +
      `fix-internal-dependency-alignment.py --apply` in unified-trading-pm and ship the resulting
      `workspace-manifest.json` change. Repo: unified-trading-pm.
