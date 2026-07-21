---
doc_type: issue
title: >-
  Both UI repos' declared SSOT ESLint config (eslint.config.base.js, no-explicit-any/no-console/no-unused-vars: error)
  is never actually imported by either repo's real flat-config entrypoint — the rule is silently unenforced
summary: >-
  While scoping unified_trading_system_ui_codex_violations_far_exceed_estimate-001 ("sweep ~59 real any-type usages"),
  found that `eslint.config.mjs` (unified-trading-system-ui) and `eslint.config.js` (deployment-ui) never import or
  spread `eslint.config.base.js` — the file both repos carry, headed "SSOT ESLint config for all UI repos... Do NOT edit
  per-repo," declaring `no-explicit-any: error`. Confirmed via a live full `npx eslint .` run on
  unified-trading-system-ui: 0 no-explicit-any results (0 errors, 60 unrelated react-hooks warnings) despite the repo
  having dozens of real `any` usages findable by text grep. deployment-ui's own `eslint.config.js` independently
  hardcodes `no-explicit-any: "warn"` inline, also never referencing the base file. `bash scripts/quality-gates.sh`'s
  LINT step runs `npm run lint` (confirmed in `base-ui.sh`), so this is not a bypassed/skipped step — the actual active
  ruleset is just missing the rule the SSOT file claims is in effect.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui, deployment-ui, unified-trading-pm]
scope: [engineer]
tags: [quality-gates, eslint, ui, codex-compliance, ssot-drift, no-explicit-any, cross-repo]
related:
  [
    plans/active/issues/unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21.md,
    codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [unified_trading_system_ui_codex_violations_far_exceed_estimate-001]
resolved_by:
locked_by:
depends_on: []
---

# What I found

`eslint.config.base.js` exists in both `unified-trading-system-ui` and `deployment-ui`, with this header:

```js
// SSOT ESLint config for all UI repos — owned by unified-trading-pm
// Do NOT edit per-repo. Edit this file and propagate via:
//   python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --ui-only
// Rule philosophy (matches Python zero-warning policy):
//   - no-explicit-any    → error  (was warn; agents must use specific types)
//   - no-console         → error  (enforced by base-ui.sh [3.5] codex check too)
```

It's written in legacy `.eslintrc`-style CommonJS (`module.exports = { extends: [...], rules: {...} }`) — but BOTH
repos' actual active configs are ESLint 9 flat-config (`export default [...]` / `tseslint.config(...)`), and NEITHER
imports or spreads the base file:

- `unified-trading-system-ui/eslint.config.mjs`: spreads `nextConfig` + a react-hooks-warnings override block +
  `eslintConfigPrettier`. Zero reference to `eslint.config.base.js`.
- `deployment-ui/eslint.config.js`: builds its own `tseslint.config(...)` from scratch, hardcoding
  `"@typescript-eslint/no-explicit-any": "warn"` inline (not even the base file's `error`) and `no-unused-vars: "warn"`
  (base file says `error`). Zero reference to `eslint.config.base.js`.

**Live confirmation**: ran `npx eslint .` on `unified-trading-system-ui` (fresh `pnpm install`, full run, ~2 min) —
`✖ 60 problems (0 errors, 60 warnings)`, every single one a `react-hooks/*` rule. Zero `no-explicit-any` hits, despite
the repo having dozens of real `any`-type usages (confirmed separately by text grep, per the sibling issue doc's own
measured count of ~60). The rule simply isn't in the active ruleset for this repo — not suppressed, not baselined, not
disabled by a comment — just never wired in.

# Why it matters

`bash scripts/quality-gates.sh`'s `[2/6] LINT` step runs `npm run lint` (→ `eslint .`) as a REAL gate, not a best-effort
check (`base-ui.sh` lines ~226-238) — so this isn't a bypassed step silently skipped. The gate genuinely cannot detect
`any`-type regressions right now for either UI repo, meaning:

- The sibling issue's "~60 remaining any-type usages" count was only ever discoverable via a manual/ad-hoc text-grep
  audit, not the standing quality gate — anyone shipping a NEW `any` usage after this session's cleanup lands gets a
  green `quality-gates.sh` regardless. A one-time manual sweep (the sibling todo) fixes the symptom but not the
  regression path.
- The base file's own header ("Do NOT edit per-repo... propagate via rollout script") implies a fleet propagation
  mechanism exists (`rollout-quality-gates-unified.py`) that either was never run against these 2 repos' current
  flat-config format, or ran once against the old `.eslintrc` format before both repos migrated to flat-config and was
  never re-run/adapted afterward. Either way, the SSOT's stated single source of truth is currently fiction for both
  live consumers.
- `deployment-ui`'s independent hardcoded `"warn"` (not even error) compounds this — it's drifted from the SSOT in its
  own direction, not just failed to inherit it.

# Recommended decision

This is a cross-repo SSOT-wiring gap, not something to unilaterally fix mid-way through the narrower any-type-sweep todo
— flagging per the workspace's cross-repo/SSOT-contradiction finding rule. Suggest:

1. Determine whether `rollout-quality-gates-unified.py --ui-only` (referenced in the base file's own header) still works
   against ESLint 9 flat-config, or needs updating for the post-migration format.
2. Decide sequencing: wire the base rules into both live flat-configs BEFORE or AFTER the any-type/console.*
   manual-sweep todos land (wiring first would make every remaining violation a hard lint failure immediately, turning
   the "sweep" work into "fix quality-gates.sh red" rather than a discretionary cleanup — likely the more honest
   ordering, but changes the other todos' urgency).
3. Audit whether any OTHER UI-adjacent repos (unified-trading-system-ui/deployment-ui are the only 2 checked this
   session) have the same base-file-present-but-unwired pattern.

## Todos

- [ ] [INFRA] P2. Determine why `eslint.config.base.js` isn't imported by either UI repo's live flat-config and either
      fix `rollout-quality-gates-unified.py --ui-only` to wire it in correctly for ESLint 9 flat-config, or update the
      base file itself to the flat-config format both repos actually use, then propagate. (repo: unified-trading-pm,
      unified-trading-system-ui, deployment-ui)
- [x] ✅ [INFRA] P3. Once wired, reconcile `deployment-ui`'s inline `no-explicit-any: "warn"` (drifted below even the
      pre-fix SSOT) and `no-unused-vars: "warn"` against the base file's `error` level. (repo: deployment-ui) —
      **already accomplished** by the todo-1 wiring work itself: `deployment-ui@01e455f` ("wire deployment-ui
      flat-config to the SSOT .cjs base rules") replaced the hardcoded local rules block with `...uiBaseRules.rules`
      spread from `eslint.config.base.cjs` — there is no remaining local override to reconcile,
      `no-explicit-any`/`no-unused-vars`/`no-console` are now literally the base file's `error` values, not a
      separately-declared match. Verified 2026-07-21 (slot-9), independently: `npm run lint` (the real gate —
      package.json scopes it to `eslint src`, not the whole repo) passes with ZERO output on the current tree;
      deployment-ui genuinely has 0 real `any`-type usages today (confirmed by the original issue's own finding), so
      this todo's deliverable is the rule now being correctly ACTIVE for the next violation, not a backlog of existing
      ones to fix. Note: `unified-trading-system-ui`'s half of todo 1 (the wiring) is NOT yet done — that repo's
      `eslint.config.mjs` still has zero reference to `eslint.config.base.js` as of this check; todo 1 stays open for
      that repo.

## Codex SSOTs

`codex/06-coding-standards/ui-testing-layers.md`, `codex/06-coding-standards/quality-gates.md`.
