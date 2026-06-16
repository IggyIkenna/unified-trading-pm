---
title: deployment-ui jsdom test env broken — html-encoding-sniffer@6 require()s ESM @exodus/bytes (ERR_REQUIRE_ESM)
created: 2026-06-16
author: ikennaigboaka
source:
  - data-status UI fix wave 2026-06-16 (venue re-fetch + de-dupe panels + pagination) — could not pass the UI gate
  - deployment-ui `bash scripts/quality-gates.sh --test` → 80 test files ERR_REQUIRE_ESM
locked_by: live-defi-rollout
---

# deployment-ui jsdom test env broken (ERR_REQUIRE_ESM) — blocks ALL UI test gating

## What I found

`deployment-ui` vitest unit tests fail fleet-wide: **80 test files** (every jsdom render test, incl. unmodified ones
like `tests/unit/components/Header.test.tsx`) fail to start their forks worker with:

```
Error: require() of ES Module .../node_modules/@exodus/bytes/encoding-lite.js
  from .../node_modules/html-encoding-sniffer/lib/html-encoding-sniffer.js not supported.
{ code: 'ERR_REQUIRE_ESM' }
```

Root cause: `html-encoding-sniffer@6.0.0` declares `"@exodus/bytes": "^1.6.0"` and `require()`s it, but the resolved
`@exodus/bytes@1.15.1` is **ESM-only** (`"type": "module"`). Under vitest's `pool: "forks"` (CommonJS worker), the
`require()` throws. `html-encoding-sniffer` is pulled transitively by jsdom (via `whatwg-encoding`), so it hits
**every** test that uses the jsdom environment (i.e. all `render()`-based component tests).

This is **pre-existing** (reproduces on a clean tree — `Header.test.tsx` was not touched) and most likely arrived with
the recent `chore(tooling): align frontend tooling — bump shared pins` (deployment-ui@53083ff) which moved the shared
pins. `tsc --noEmit` and ESLint still pass; only the test step is down. The build step was not separately confirmed.

## Why it matters

- **The deployment-ui test gate cannot go green**, so `quickmerge` (Pass-1 QG) hard-refuses → **no UI change can ship**.
- Blocks the entire TIER-1 UI workstream in `data_status_tab_and_downloads_remediation_2026_06_16.md` (venue re-fetch,
  de-dupe panels, pagination selector, rollup-clarity) AND any other deployment-ui work fleet-wide.
- The `pw:L2` playwright regression gate is also unreachable while the unit env is broken.
- A data-status UI fix bundle is already written + tsc/eslint-clean, preserved at
  `origin/wip-preserve/data-status-ui-fixes-2026-06-16` (deployment-ui@550302c) — recover once the env is fixed.

## Recommended decision

Pick one (UI-owner / operator call — do NOT blind-bump, it may interact with the intentional 53083ff pin move):

1. **Pin `html-encoding-sniffer` to the last CJS major (`^5`)** via a package.json `overrides` block (npm), re-lock,
   re-run the full vitest suite + build. Lowest-risk if jsdom tolerates v5.
2. **Tell vitest to transform the ESM dep** — add `@exodus/bytes` (and `html-encoding-sniffer`) to
   `test.server.deps.inline` (or `deps.optimizer.web.include`) in `vitest.config.*`, so the ESM module is bundled rather
   than `require()`d. No dep change; scoped to the test runner.
3. **Bump jsdom** to a line whose `html-encoding-sniffer` doesn't pull ESM `@exodus/bytes`, if 53083ff under-bumped a
   peer.

Definition of done: `bash scripts/quality-gates.sh` exits 0 (typecheck + lint + **tests** + build), then recover the
wip-preserve branch and finish the data-status UI items (with `pw:L2 ✓` + regression spec per the UI gate). </content>
</invoke>
