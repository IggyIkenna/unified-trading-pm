---
doc_type: issue
title: >-
  deployment-ui's vitest --coverage gate fails broadly on live-defi-rollout HEAD (24-25% vs the 64-70% thresholds across
  all 4 metrics) — pre-existing, unrelated to any one change, blocks quickmerge for the whole repo
summary: >-
  Found while trying to quickmerge an unrelated, single-line-scoped `scripts/setup.sh` change
  (`ui_build_warm_cache_2026_06_17.md`'s pre-warm-build-cache todo). `quickmerge.sh`'s re-gate step failed on Unit Tests
  with global coverage far below the configured thresholds (lines 25.11% vs 70%, functions 22.58% vs 67%, statements
  24.42% vs 70%, branches 16.16% vs 64%) — dozens of components (`ValueCensus.tsx`, `BreakdownsAccordion.tsx`,
  `CLIPreview.tsx`, `InstanceExplorer.tsx`, `TradingButton.tsx`, `LiveValuesPanel.tsx`, `PillarStack.tsx`, and many
  more, per the coverage table) show 0-20% coverage. Confirmed via `git stash` (removing the unrelated setup.sh diff
  entirely) that the failure is 100% pre-existing on `live-defi-rollout` HEAD (`7224165`), not caused or worsened by the
  setup.sh change. The repo's own `.qg_last_passed_sha` sentinel (`0e0aa3ac...`) does not match current HEAD
  (`7224165`), meaning no fully-green `quality-gates.sh` run has landed since whatever commit last touched that sentinel
  — the tree has drifted red since then, most likely from a wave of new/changed components shipped without matching test
  coverage (consistent with the heavy concurrent multi-agent load this repo is under).
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, vitest, coverage, quality-gates, quickmerge-blocked]
related: [/plans/active/ui_build_warm_cache_2026_06_17.md]
created: 2026-07-29
last_updated: 2026-07-29
parent_epic: deployment_and_user_management_master
source: >-
  Discovered while attempting to quickmerge deployment-ui's half of ui_build_warm_cache_2026_06_17.md's pre-warm-build
  todo, 2026-07-29. Confirmed pre-existing via `git stash` + a clean `npx vitest run --coverage` re-run with the
  unrelated diff fully removed — identical failure numbers with or without the change.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
assigned_role: ui_developer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "deployment-ui@3c7e2a8"
---

> **🟢 ARCHIVED 2026-07-30** — status=resolved, 0 open todos. Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule.

# deployment-ui vitest coverage gate is broadly red — blocks ALL quickmerges into this repo right now

## What I found

`bash scripts/quickmerge.sh ... --agent --files 'scripts/setup.sh'` (a one-file, unrelated shell-script change) failed
its re-gate step on Unit Tests:

```
Coverage summary
Statements   : 24.42% ( 693/2837 )
Branches     : 16.16% ( 401/2480 )
Functions    : 22.58% ( 168/744 )
Lines        : 25.11% ( 634/2524 )
ERROR: Coverage for lines (25.11%) does not meet global threshold (70%)
ERROR: Coverage for functions (22.58%) does not meet global threshold (67%)
ERROR: Coverage for statements (24.42%) does not meet global threshold (70%)
ERROR: Coverage for branches (16.16%) does not meet global threshold (64%)
```

Verified this is **not caused by the setup.sh change**: `git stash` (removing the diff entirely) and re-running
`npx vitest run --coverage` directly on `live-defi-rollout` HEAD (`7224165`) reproduces the identical numbers.
`.qg_last_passed_sha` (`0e0aa3acd104d1857d2d79a2d74af9e1bc787b8a`) does not match HEAD — the last verified-green
`quality-gates.sh` run is stale relative to the current tree.

Per-file coverage (excerpt from the full table) shows many components at or near 0%: `InstanceExplorer.tsx` (6.02%),
`TradingButton.tsx` (2.63%), `PillarStack.tsx`/`ChainBreakdown.tsx` (0%), `SchemaModal.tsx` (0%), `LifecycleCards.tsx`
(2.85%), `ReadinessPanel.tsx` (0%), `DetailPanel.tsx` (0%), `AttentionCard.tsx` (6.25%) — a broad spread across
`components/`, not a single offending file.

## Why it matters

**This blocks every future quickmerge into deployment-ui**, not just the one this session attempted — per the workspace
HARD RULE ("commit only from a `quality-gates.sh`-green tree"), no agent can land ANY change here via the sanctioned
quickmerge path until this gate is green again. Given the repo is under heavy concurrent multi-agent load (per this
session's own dispatch context), every other in-flight agent working in deployment-ui this session is likely hitting or
will hit the same wall.

## What this is NOT

- Not a bug in any specific component — it's a global threshold gate failing against a broad coverage shortfall, most
  plausibly from newly-added/changed components that shipped without matching `*.test.tsx` files.
- Not caused by this session's `scripts/setup.sh` pre-warm-build change — independently reproduced with that diff fully
  removed.
- Not attempted to fix in this session — writing tests for dozens of under-covered components across
  `components/trading/*`, `components/shared/*`, etc. is real, non-trivial engineering effort, out of scope for the
  single bounded todo (`ui_build_warm_cache_2026_06_17.md`) this was discovered under.

## Todos

- [x] ✅ [UI] P1. Root-cause how the coverage threshold got this far behind (bisect for the commit(s) that pushed it
      below 70%/67%/70%/64%) — deployment-ui@3c7e2a8. Bisect found the "broad coverage collapse" was **not a real
      test-coverage regression** — it was a broken local dependency install caused by a mis-authored
      `pnpm-workspace.yaml` (missing `packages:`). See Progress Log for the full root-cause writeup + evidence. Done:
      `bash scripts/quality-gates.sh` ran green end-to-end on `live-defi-rollout` HEAD (coverage Statements
      72.32%/Branches 64.5%/Functions 68.79%/Lines 74.49%, all ≥ threshold) with a fresh `.qg_last_passed_sha` write
      matching HEAD. Repo: deployment-ui.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **2026-07-30 (slot 16, ui_developer craft)**: ROOT-CAUSED + FIXED — the broad coverage collapse was an **environment
  artifact, not a real test gap**.
  - This slot's fresh `.tabs/16/deployment-ui` clone had no `node_modules` at all. `bash scripts/setup.sh` /
    `pnpm install` failed outright: `ERROR packages field missing or empty`. Traced to `pnpm-workspace.yaml` (added by
    `de5b7af`, the 2026-07-29 npm→pnpm migration commit) declaring only `ignoredBuiltDependencies:` with **no
    `packages:` field** — pnpm 9.15.9 (this host's globally-installed pnpm) hard-refuses ANY install once a
    `pnpm-workspace.yaml` exists without `packages:`.
  - CI stayed green through this the whole time (`gh run list --repo IggyIkenna/deployment-ui` shows unbroken
    `quality-gates-v2` successes since `de5b7af`) because `ui-quality-gates-v2.yml` pins `pnpm/action-setup@v6` at major
    version `"10"` — pnpm 10.x tolerates the missing `packages:` field; pnpm 9.x does not. Verified directly:
    `npx pnpm@9` reproduces the error against the unmodified file, `npx pnpm@10` installs clean against the same file.
  - This means the original issue-reporting session almost certainly ran `npx vitest run --coverage` against a
    **stale/partial pre-migration `node_modules`** (pnpm install would have failed for them too, under whatever pnpm
    major they had) rather than a correctly-resolved dependency tree — producing the reported 24-25% numbers from broken
    module resolution/transforms, not from genuinely uncovered components.
  - Fix shipped: added an explicit `packages: ["."]` to `pnpm-workspace.yaml` — verified to install cleanly under BOTH
    pnpm 9.15.9 and pnpm 10.34.5, so this stops depending on which pnpm major a given dev/agent host happens to have.
  - With a correct install, coverage is and was fine — no test-writing or threshold adjustment was needed:
    `Statements 72.32%|Branches 64.5%|Functions 68.79%|Lines 74.49%` (all ≥ the 70/64/67/70 thresholds), 101 test files
    / 1101 tests passing. `bash scripts/quality-gates.sh` ran green end-to-end post-fix, sentinel written matching HEAD.
  - Shipped: `deployment-ui@3c7e2a8` (`fix(deps): declare packages: in pnpm-workspace.yaml so pnpm 9.x can install`),
    landed on `live-defi-rollout` via quickmerge --agent.
