---
doc_type: issue
title:
  base-ui.sh's [3.5/6] UI CODEX CHECKS gate silently skips any UI repo without a src/ directory —
  unified-trading-system-ui (Next.js app/ router) has run every quality-gates.sh pass with this gate never firing
summary: >-
  Found while re-auditing ui_quality_gates_parity_2026_03_16.plan.md's residual items:
  unified-trading-pm/scripts/quality-gates-base/base-ui.sh:337 gates its whole console.log/hardcoded-colour/@ts-ignore/
  chart-theme.ts compliance block behind `[ -d "src" ]`. unified-trading-system-ui uses the Next.js app/ router (no src/
  dir at all), so this block has run as "skipped ... no src/" on every quality-gates.sh invocation for that repo — real
  violations (console.log, any-types) accumulated because the gate that would have blocked them never ran.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer]
tags: [quality-gates, ui, codex-compliance, app-router, gate-blind-spot]
related:
  [
    plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md,
    plans/archive/ui_quality_gates_parity_2026_03_16.plan.md,
    codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [batch4_strategy_ui_archived_plan_residuals-004]
resolved_by:
locked_by:
depends_on: []
---

# UI codex-compliance gate never runs for App-Router UI repos

## What I found

`unified-trading-pm/scripts/quality-gates-base/base-ui.sh:337`:

```bash
if [ "$SKIP_CODEX" = false ] && [ -d "src" ]; then
  log_section "[3.5/6] UI CODEX CHECKS"
  ...
```

The entire `[3.5/6]` block (no-console.\*, no-hardcoded-colours, no-@ts-ignore, no-hardcoded-localhost,
chart-theme.ts-presence, duplicate-test-file detection) is gated on a literal `src/` directory existing at the repo
root. `unified-trading-system-ui` uses the Next.js **App Router** convention — routes/components live under `app/`,
`components/`, `lib/`, never `src/`. So for every `quality-gates.sh` run on that repo, the step prints
`[3.5/6] UI CODEX CHECKS — skipped (--test / --lint / --quick or no src/)` and none of the checks execute — this is not
a one-off miss, it is the gate's permanent behavior for this repo's directory layout.

Confirmed real drift accumulated as a direct result: `unified-trading-system-ui` currently has ~13 real `: any` type
annotations and 4 real `console.log(...)` calls across `app/`, `components/`, `lib/` (excluding test files) — exactly
the two violation classes this gate exists to block. `deployment-ui` (which DOES have a `src/` layout) has zero of
either, confirmed by its own green `[3.5/6]` run (`✅ No console.* in production code`,
`✅ No @ts-ignore in production code`) earlier this session. The gate works; it just structurally can't see this repo.

Also missing as a direct consequence: `unified-trading-system-ui` has `recharts: 2.15.0` as a real dependency
(`package.json:117`) but no `lib/chart-theme.ts` — the `[3.5/6]` block's chart-theme-presence check would have caught
this too, had it run.

Note the `[2/6] LINT` step is NOT affected — it already has an explicit `else npm run lint` fallback for repos without
`src/` (`base-ui.sh:236-242`), so ESLint itself still runs for this repo. Only the rg-based `[3.5/6]` codex-pattern
block lacks that fallback.

## Why it matters

This is a structural blind spot in a gate that serves ALL UI repos workspace-wide, not a one-off bug: any current or
future UI repo built on the Next.js App Router (rather than a `src/`-rooted layout) silently skips the entire
codex-compliance block, with no warning beyond an easy-to-miss log line. `unified-trading-system-ui` is one of only 2
live UI repos today — this isn't a hypothetical edge case, it's already been live-blind for as long as `[3.5/6]` has
existed.

## Recommended decision

Generalize the directory check to detect either layout (`src/` OR `app/` + `components/`/`lib/`), point the rg patterns
at whichever root is actually present, then clean up the violations the gate would have caught.

## Todos

- [ ] [BACKEND] P2. Fix `base-ui.sh:337`'s `[ -d "src" ]` gate (and the `[3.5/6] ... skipped` message at line 428) to
      also detect a Next.js App-Router layout (`[ -d "app" ]` or similar) and target the rg checks at that root instead
      of hardcoding `src/`. Verify against both `deployment-ui` (src/ layout, must stay green) and
      `unified-trading-system-ui` (app/ layout, must now actually run). (repo: unified-trading-pm)
- [ ] [UI] P2. Once the gate fires for `unified-trading-system-ui`, fix the violations it surfaces: ~13 `: any` type
      annotations and 4 `console.log(...)` calls in `app/`/`components/`/`lib/` (excluding tests), plus add
      `lib/chart-theme.ts` for its `recharts` usage (`package.json:117`) matching
      `deployment-ui/src/lib/chart-theme.ts`'s pattern. (repo: unified-trading-system-ui)

## Codex SSOTs

`codex/06-coding-standards/ui-testing-layers.md`, `codex/06-coding-standards/quality-gates.md`.
