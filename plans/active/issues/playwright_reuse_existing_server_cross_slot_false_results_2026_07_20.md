---
doc_type: issue
title:
  "Playwright reuseExistingServer silently attaches to ANOTHER SLOT's dev server — false pass/fail against foreign code"
summary:
  "Every slot's playwright.config.ts defaults to the same fixed port (deployment-ui 5199, unified-trading-system-ui its
  own fixed ports) with reuseExistingServer enabled. With 11 per-slot clones on one host, a Playwright run in slot N
  silently ATTACHES to whichever slot got there first and runs its specs against THAT slot's code. Measured 2026-07-20:
  a run on 5199 attached to tab-3's server and produced a FALSE failure; re-running on PLAYWRIGHT_PORT=5210 passed.
  Failure is silent — Playwright reports a normal pass/fail with no indication the code under test was not yours."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, unified-trading-system-ui, unified-trading-pm]
scope: [engineer]
tags: [playwright, multi-agent, per-slot-worktrees, false-negative, test-isolation, ui-testing-layers]
related: [promotion_queue_conflict_wall_pileup_2026_06_17]
created: 2026-07-20
priority: P2
parent_epic: agent_operating_framework_master
source: "Observed during IS/UI work, slot-1, 2026-07-20"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
assigned_vm:
resolved_by:
---

# Playwright `reuseExistingServer` crosses slot boundaries

## Symptom

A Playwright run in one slot produces a pass/fail verdict **against another slot's source tree**, with no warning.
Measured 2026-07-20: a `deployment-ui` run on the default port 5199 attached to the dev server already owned by tab-3
and reported a FALSE failure. Re-running the identical specs with `PLAYWRIGHT_PORT=5210` passed.

The dangerous direction is the inverse: a slot whose own code is broken can **pass** because it silently tested a
neighbour's working tree.

## Mechanism

`deployment-ui/playwright.config.ts`:

```ts
const PORT = process.env.PLAYWRIGHT_PORT ?? "5199";
...
webServer: {
  command: `npm run dev -- --port ${PORT} --strictPort`,
  url: BASE_URL,
  reuseExistingServer: true,
  env: { VITE_MOCK_API: "true" },
}
```

`unified-trading-system-ui/playwright.config.ts` sets `reuseExistingServer: true` in three webServer blocks on its own
fixed ports.

The config's existing comment reasons that a dedicated 5199 is safe because "on the dedicated 5199 a reused server is
always mock-mode". That was written against the **single-checkout** hazard it was fixing (incident 2026-06-17: reusing
the operator's live non-mock stack on 5183). It is still true that a reused 5199 server is mock-mode — but under
per-slot worktrees the relevant invariant is not "is it mock-mode", it is **"is it MY code"**, and that one does not
hold.

This host has **11 slot clones** (`.tabs/1` … `.tabs/11`), each a full independent checkout, all resolving
`PLAYWRIGHT_PORT` to the same 5199 default. First writer wins the port; every later slot silently attaches to it.
`--strictPort` makes this worse, not better: it guarantees the port never auto-increments away to a private one, so a
late-arriving slot can only ever attach to the incumbent.

## Why it stays silent

- `reuseExistingServer: true` is a normal, expected code path — no warning is emitted.
- The reused server IS mock-mode and IS healthy, so the `url` health check passes immediately.
- Specs then run green-or-red against foreign code. Nothing in the report names the serving worktree.
- It is intermittent and ordering-dependent — it reproduces only when another slot happens to hold the port, which is
  exactly the profile that gets written off as "flaky" and re-run until green.

This directly undercuts the `pw:L2 ✓` gate in `/codex/06-coding-standards/ui-testing-layers.md`: a cited passing
regression spec is only evidence if it ran against the citing slot's code.

## Recommended fix

**A — per-slot port derivation [RECOMMENDED].** Derive the default port from the slot number instead of a constant, so
slots can never collide and no agent has to remember an env var. Slot-N is already derivable from the path — the SSOT is
`scripts/hooks/slot-identity-lib.sh` (used for commit attribution). Roughly:

```ts
// slot-N from the checkout path (…/.tabs/<N>/…); 0 when not in a slot clone.
const SLOT = Number(process.cwd().match(/\/\.tabs\/(\d+)\//)?.[1] ?? 0);
const PORT = process.env.PLAYWRIGHT_PORT ?? String(5199 + SLOT);
```

Keeps `reuseExistingServer: true` (fast local iteration, the reason it exists) while making the reused server
necessarily your own. Apply to `deployment-ui` and to all three `unified-trading-system-ui` webServer blocks.

**B — `reuseExistingServer: false` under agent runs.** e.g. `reuseExistingServer: !process.env.CLAUDECODE`. Strictly
correct isolation, but pays a full dev-server boot on every agent run.

**C — both.** Per-slot port as the default, plus `false` under CI/agent runs. Most robust; recommended if A alone proves
insufficient.

A fix should also log the resolved port and whether a server was reused, so a foreign attach is at least visible in the
run output rather than invisible.

## Interim guidance for agents

Until this is fixed, **always pass an explicit unique port** when running Playwright in a slot:

```bash
PLAYWRIGHT_PORT=$((5199 + <slot-N>)) npx playwright test
```

Treat any Playwright failure on a default port as unverified until re-run on a unique port — and treat a **pass** on a
default port with the same suspicion.
