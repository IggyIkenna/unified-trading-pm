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
status: resolved
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
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [batch4_strategy_ui_archived_plan_residuals-004]
resolved_by:
  slot-9 (2026-07-21) — both todos shipped (unified-trading-pm@dd23d1d20 gate fix; unified-trading-system-ui@94c7b25b +
  @fce0861a cleanup), verified clean
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

- [x] ✅ [BACKEND] P2. Fix `base-ui.sh:337`'s `[ -d "src" ]` gate (and the `[3.5/6] ... skipped` message at line 428) to
      also detect a Next.js App-Router layout (`[ -d "app" ]` or similar) and target the rg checks at that root instead
      of hardcoding `src/`. Verify against both `deployment-ui` (src/ layout, must stay green) and
      `unified-trading-system-ui` (app/ layout, must now actually run). (repo: unified-trading-pm) —
      `unified-trading-pm@dd23d1d20`. Introduced `_CODEX_ROOTS` array resolution (`src/` if present, else `app/` +
      whichever of `components/`/`lib/` exist) and switched every exclude glob from `!src/**/...` to root-agnostic
      `!**/...` so they match regardless of which root fired. `deployment-ui` (`src/` layout) verified byte-identical
      green on a full `quality-gates.sh` run (66s, all 6 `[3.5/6]` checks pass as before — zero regression).
      `unified-trading-system-ui` (`app/` layout, no `src/` at all) verified the gate now actually resolves
      `_CODEX_ROOTS=(app components lib)` and finds real violations (84 `console.*` calls, 55 any-types, missing
      `lib/chart-theme.ts`) instead of silently skipping — direct-tested the resolved rg logic since the repo's
      pre-existing, unrelated `.next/` stale-cache typecheck failure blocks a full sequential `quality-gates.sh` run
      from reaching `[3.5/6]` (not something this task should also fix). **Consequence, called out explicitly**:
      `unified-trading-system-ui`'s full `quality-gates.sh` run will now correctly FAIL at `[3.5/6]` until the cleanup
      todo below lands — this is the fix working as intended (a real, previously-invisible gap now visible), not a
      regression. `--test`/`--lint`/`--quick` modes are unaffected. Corrected the sibling cleanup todo's violation-count
      estimate with the numbers measured while verifying this fix.
- [x] ✅ [UI] P2. Once the gate fires for `unified-trading-system-ui`, fix the violations it surfaces. **Corrected count
      (superseding the estimate above, measured with the actual fixed gate)**: 84 `console.*` calls across 49 files and
      55 `: any`/`<any>`/`as any` occurrences in `app/`/`components/`/`lib/` (excluding tests) — materially larger than
      first estimated, genuinely a multi-session cleanup, not a quick pass. Plus add `lib/chart-theme.ts` for its
      `recharts` usage (`package.json:117`) matching `deployment-ui/src/lib/chart-theme.ts`'s pattern. **Note**: the
      gate fix (todo above) ships ahead of this cleanup — `unified-trading-system-ui`'s `quality-gates.sh` will show
      `[3.5/6] UI CODEX CHECKS FAILED` on any full run until this lands; `--test`/`--lint`/`--quick` modes are
      unaffected (they already skip `[3.5/6]` for every repo). (repo: unified-trading-system-ui) — **SHIPPED** across
      two commits: `unified-trading-system-ui@94c7b25b` (55 any-types across 22 files + `lib/chart-theme.ts`) and
      `unified-trading-system-ui@fce0861a` (all 84 `console.*` calls swept to a new shared `lib/logger.ts`, wired via
      `CODEX_CONSOLE_EXCLUDE_GLOBS=(!**/lib/logger.ts !**/components/shared/error-boundary.tsx)`;
      `codex_ui_violation_baseline.json` ratcheted `console: 84→0`). Verified 2026-07-21 (slot-9): a fresh
      `rg 'console\.(log|warn|error|debug|info)'` sweep over `app/components/lib` (excluding `logger.ts`) finds exactly
      1 hit left (`error-boundary.tsx`, the one sanctioned exception — React error boundaries structurally can only use
      raw `console.error`, same rationale as `deployment-ui`'s own `ErrorBoundary.tsx` exclusion), and
      `bash scripts/quality-gates.sh --lint` passes clean. Colour (1076 remaining, down from 1082) + localhost (30)
      counts are a SEPARATE, not-yet-done backlog — tracked in
      `plans/active/issues/unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21.md` todo 3, not
      this todo's original scope.

## Codex SSOTs

`/codex/06-coding-standards/ui-testing-layers.md`, `/codex/06-coding-standards/quality-gates.md`.
