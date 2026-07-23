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
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
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

- [x] ✅ [INFRA] P2. Determine why `eslint.config.base.js` isn't imported by either UI repo's live flat-config and
      either fix `rollout-quality-gates-unified.py --ui-only` to wire it in correctly for ESLint 9 flat-config, or
      update the base file itself to the flat-config format both repos actually use, then propagate. (repo:
      unified-trading-pm, unified-trading-system-ui, deployment-ui) — **partially accomplished, 2 of 3 repos done,
      unified-trading-system-ui deferred to todo 3 below (do not re-close this scope until that lands)**. Root cause was
      the base file's format (legacy `.eslintrc` CommonJS `module.exports`), not the propagation script per se: replaced
      with `eslint.config.base.cjs` (flat-config-compatible, unambiguously CommonJS regardless of a consumer's
      `package.json` `"type"`) + fixed `rollout-quality-gates-unified.py`'s `propagate_eslint_config()` to
      reference/copy it and clean up stale `.js` copies — `unified-trading-pm@a6128da10`.
      `deployment-ui/eslint.config.js` now imports + spreads the base rules — `deployment-ui@01e455f` (confirmed
      independently by slot-9 in todo 2 below). `unified-trading-system-ui`: only the dead `eslint.config.base.js` was
      removed (`unified-trading-system-ui@7d6f3129d`); the base rules were **deliberately NOT wired** into its
      `eslint.config.mjs` — see todo 3.
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
- [ ] [FRONTEND] P2. Wire `eslint.config.base.cjs`'s rules into `unified-trading-system-ui/eslint.config.mjs` (import +
      spread `uiBaseRules.rules`, scoped to `files: ["**/*.ts", "**/*.tsx"]` — nextConfig's own `@typescript-eslint`
      plugin registration is itself scoped that way, so an unscoped block errors on files where the plugin isn't
      registered). Blocked on a real cleanup first: a live trial wiring (2026-07-21) surfaced **2610** `error`-level
      `no-unused-vars`/`no-console` violations across the codebase — the prior any-type sweep
      (`unified-trading-system-ui@94c7b25b`) only covered `no-explicit-any`, not these two rules. Needs its own sweep(s)
      (likely split: one for `no-unused-vars`, one for `no-console`, given the volume) before the wiring can land
      without redding `quality-gates.sh` for the whole repo. Also add `eslint.config.base.cjs` to the repo's `ignores`
      list when re-adding the file (it isn't covered by `nextConfig`'s own file-pattern globs —
      `js/jsx/mjs/ts/tsx/mts/cts` omits `.cjs` — so linting it directly throws a plugin-resolution error; the exact diff
      was drafted and verified working 2026-07-21 but reverted before shipping once the violation count was known —
      re-derive it, it's cheap to redo). (repo: unified-trading-system-ui)
- [x] ✅ [INFRA] P3. `unified-trading-system-ui`'s shared `.pre-commit-config.yaml` (rolled out from
      `unified-trading-pm/scripts/pre-commit-templates/ui.pre-commit-config.yaml`) pins
      `pre-commit/mirrors-eslint@v8.56.0` for the `Lint with ESLint` hook. That ESLint 8.56.0 build's flat-config
      auto-discovery only recognizes a file literally named `eslint.config.js` — NOT `eslint.config.mjs`. Confirmed
      2026-07-21 by reproducing on an untouched, unrelated `next.config.mjs` (not part of this issue's diff at all):
      `prek run eslint --files next.config.mjs` fails with `ESLint couldn't find a configuration file`. This means **any
      commit that stages a new/modified `.mjs`/`.js`/`.ts`/`.tsx`/`.jsx`/`.cjs` file in this repo hits a hard pre-commit
      failure**, independent of that file's actual content — `deployment-ui` is unaffected only because its own
      flat-config entrypoint happens to be named `eslint.config.js` (not `.mjs`), so this is
      unified-trading-system-ui-specific today but is a template-level bug that would bite ANY future UI repo whose
      package.json defaults to CommonJS (forcing an `.mjs`-named ESM config, same as this repo). This is a genuine
      pre-existing latent bug, not caused by this issue's work — it was simply never triggered before because no prior
      commit staged a matching file type through the `prek`/pre-commit path. Fix in the TEMPLATE
      (`unified-trading-pm/scripts/pre-commit-templates/ui.pre-commit-config.yaml`), not the local copy — either bump
      `rev:` to an ESLint 9-based mirror tag that understands flat config natively, or add an `exclude:` pattern for
      root-level `*.config.mjs` tooling files (the actual application `.ts`/`.tsx` linting coverage is unaffected either
      way since app code isn't `.mjs`-named) — then re-propagate via `scripts/propagation/rollout-pre-commit-configs.sh`
      to all UI-template consumers. (repo: unified-trading-pm, unified-trading-system-ui) — **removed the hook entirely
      rather than patching it, after establishing it never provided real coverage in EITHER repo, not just an
      .mjs-naming edge case.** Deeper investigation (via the actual git-commit hook path, not just
      `prek run     --files`, which under-reported): the mirror hook's own upstream manifest hard-restricts matched file
      types independently of a consumer's local `types_or:` override — proven by the sibling `prettier-autostage` hook,
      which uses the IDENTICAL `types_or: [javascript, jsx, ts, tsx, ...]` list and correctly matches `.ts`/`.tsx`.
      Confirmed on a REAL, obviously-violating `.tsx` file with an unused variable in `deployment-ui` (whose
      `eslint.config.js` DOES resolve by name, ruling out the config-discovery issue as the cause) — the hook reported
      "no files to check" every time, meaning `.ts`/`.tsx` were never even attempted, in either repo, ever. Getting real
      TypeScript coverage out of this hook would additionally require per-repo `additional_dependencies` mirroring each
      project's own `eslint`/`typescript-eslint`/`eslint-config-next` versions (the isolated hook environment has none
      of them) — a maintenance burden defeating the point of a shared template, duplicating a check `quality-gates.sh`'s
      own `npm run lint` (each repo's REAL, correctly-configured, already-mandatory-gated ESLint 9) already does
      correctly. Removed the hook block from `unified-trading-pm/scripts/pre-commit-templates/ui.pre-commit-config.yaml`
      (`unified-trading-pm@62dfd4009`), re-propagated via `rollout-pre-commit-configs.sh --repo <name>` to both
      consumers: `deployment-ui@58b7ead58`, `unified-trading-system-ui@88192658b`. Caught + preserved a pre-existing
      repo-local customization the full-file template propagation would have silently stripped:
      `unified-trading-system-ui`'s `check-added-large-files` exclude for 2 UAC-generated JSON mirrors that still exceed
      1MB — re-added by hand after the propagation script ran, not part of the shared template.
      `unified-trading-system-ui`'s propagation also converted `.gitleaks.toml` from a stale committed copy to a symlink
      (matching `deployment-ui`'s existing state) as a normal side effect of the same rollout run. Full
      `quality-gates.sh` green on both repos before shipping.

## Codex SSOTs

`/codex/06-coding-standards/ui-testing-layers.md`, `/codex/06-coding-standards/quality-gates.md`.
