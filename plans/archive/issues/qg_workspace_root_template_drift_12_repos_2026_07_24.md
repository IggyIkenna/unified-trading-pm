---
doc_type: issue
title:
  12 repos' deployed scripts/quality-gates.sh carry the vulnerable `WORKSPACE_ROOT="${WORKSPACE_ROOT:-...}"` inheritance
  pattern even though their own SOURCE TEMPLATES (quality-gates-service-template.sh / quality-gates-library-template.sh)
  already use the safe fresh-derivation form — a rollout/drift gap, not a template bug
summary: >-
  Found while implementing the fix for
  qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md (the confirmed root cause: an
  inherited WORKSPACE_ROOT/PROJECT_ROOT/REPO_ROOT env var can silently redirect QG gate paths at a stale MAIN clone).
  `codex/06-coding-standards/quality-gates-service-template.sh` and `quality-gates-library-template.sh` already use the
  SAFE pattern (`WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"`, no `${VAR:-...}` inheritance) —
  only `quality-gates-ui-template.sh` still has the vulnerable form. But 12 repos' DEPLOYED `scripts/quality-gates.sh`
  copies still carry the OLDER vulnerable `${WORKSPACE_ROOT:-...}` pattern, meaning their own template must have been
  fixed at some point AFTER these repos' copies were last rolled out, and the fix never propagated. This is a
  template-drift gap, not a template defect.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    fund-administration-service,
    greeks-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    trading-agent-service,
    unified-trading-system-ui,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [quality-gates, worktree-isolation, path-resolution, template-drift, rollout, infra]
related: [/plans/archive/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md]
created: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
  "unified-trading-pm@6e791d478 (template) + 12 per-repo shas (see todos), completed 2026-07-29 once
  market-tick-data-service's live conflict cleared (market-tick-data-service@dc82b08d). Fresh grep confirms zero
  remaining vulnerable-pattern matches across all 12 repos."
source:
  "found scoping the fix for qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md,
  2026-07-24"
priority: P3
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
---

> **🟢 ARCHIVED 2026-07-29** — status=resolved, both todos done (11/12 repos 2026-07-28, market-tick-data-service
> 2026-07-29 once its live concurrent conflict cleared). Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule.

# 12 repos' quality-gates.sh drifted from their own already-fixed templates

## What I found

Confirmed via direct grep (2026-07-24): 12 repos' own `scripts/quality-gates.sh` top-level `WORKSPACE_ROOT=` line still
reads:

```bash
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}"
```

— the vulnerable inheritance form (if `WORKSPACE_ROOT` is already set in the invoking shell, e.g. a stale/persistent
export, this line KEEPS that value verbatim instead of re-deriving). But
`codex/06-coding-standards/ quality-gates-service-template.sh` (line 16) and `quality-gates-library-template.sh`
(line 14) — the SOURCE OF TRUTH these 12 repos were presumably rolled out from — already use the SAFE form:

```bash
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
```

No `${VAR:-...}` inheritance — always derives fresh. This means the templates were fixed at some point, but the fix was
never rolled out to these 12 already-deployed repos. `quality-gates-ui-template.sh` (line 17) is the ONE template that
still has the vulnerable form — it needs the same template-level fix `quality-gates-service-template.sh` already has, in
addition to the same rollout gap for its own consumer repos (`deployment-ui`, `unified-trading-system-ui`).

Affected repos (verified by grep, `${WORKSPACE_ROOT:-` present in `scripts/quality-gates.sh`): `client-reporting-api`,
`deployment-api`, `deployment-service`, `deployment-ui`, `features-service`, `fund-administration-service`,
`greeks-service`, `market-data-processing-service`, `market-tick-data-service`, `ml-service`, `trading-agent-service`,
`unified-trading-system-ui`.

## Why it matters

This is the SAME vulnerability class as
`qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md` — a stale/persistent
`WORKSPACE_ROOT` export in any of these 12 repos' invoking shells would silently redirect their `quality-gates.sh` run
at a different clone (typically the shared bare MAIN clone) rather than the worktree under test. The `qg-common.sh`
worktree-identity guard shipped for the parent issue (unified-trading-pm@e70a0d18e) catches this class ONCE it's the
copy that gets loaded — but a `WORKSPACE_ROOT`-polluted invocation from one of these 12 repos would source
`base-service.sh`/`qg-common.sh` from wherever the polluted `WORKSPACE_ROOT` points, which may or may not have the guard
depending on THAT location's own freshness. Fixing the top-level `WORKSPACE_ROOT=` assignment in each of these 12 repos
closes the gap at its earliest point (matches Option A from the parent issue doc, applied narrowly to just this one
already-templated line — not a full rollout of every template file, which risks overwriting legitimate repo-specific
accumulated content beyond this one line).

## Recommended decision

**Do NOT run a full `rollout-quality-gates-unified.py` wholesale re-copy** — each repo's `scripts/quality-gates.sh`
likely carries repo-specific customizations beyond the shared boilerplate header, and a wholesale re-copy risks silently
stripping those. Instead: a surgical one-line fix per repo, replacing the vulnerable line with the exact line already
proven correct in `quality-gates-service-template.sh`/`quality-gates-library-template.sh`. Also fix
`quality-gates-ui-template.sh` itself (the one template still carrying the vulnerable form) so future UI-repo rollouts
don't reintroduce this.

## Todos

- [x] [CODE] P3. Fix `codex/06-coding-standards/quality-gates-ui-template.sh`'s `WORKSPACE_ROOT=` line to the safe
      fresh-derivation form (matching `quality-gates-service-template.sh`/`quality-gates-library-template.sh`
      already-correct pattern) — no `${WORKSPACE_ROOT:-...}` inheritance. — unified-trading-pm@6e791d478. Verified:
      `codex/06-coding-standards/quality-gates-ui-template.sh:17` now reads the safe fresh-derivation form.
- [x] [CODE] P3. Surgically fix the top-level `WORKSPACE_ROOT=` line in each of the 12 named repos'
      `scripts/quality-gates.sh` to match their own already-correct source template. — 11/12 shipped 2026-07-28
      (`client-reporting-api@5f73511`, `deployment-api@7273844`, `deployment-service@ae767cb`, `deployment-ui@c8c3f90`,
      `features-service@9b3a55e6`, `fund-administration-service@0018391`, `greeks-service@65c5841`,
      `market-data-processing-service@0c8d98f`, `ml-service@a43ea4e`, `trading-agent-service@b09e4d2`,
      `unified-trading-system-ui@14c434a3`); `market-tick-data-service` was blocked at the time by live concurrent WIP
      in that repo, completed 2026-07-29 once clear (`market-tick-data-service@dc82b08d`). Verified: fresh grep for
      `WORKSPACE_ROOT:-` across all 12 repos' `scripts/quality-gates.sh` returns zero matches.
