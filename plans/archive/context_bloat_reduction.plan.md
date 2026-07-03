---
doc_type: plan
title: Cursor Context Bloat Reduction
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-09
archived: '2026-03-09'
archiveReason: 'Completed — always-apply token budget reduced from 25,559 to ~12,000 tokens (52% reduction) via PR #47.'
overview: "Every new agent/chat in this workspace starts at ~55–70K tokens before any user message\nis typed. The always-apply cursor rules alone contribute ~25,559 tokens across 46 files.\nThis plan reduces that to ~10,000–12,000 tokens by:\n  1. Demoting large, specialised rules from alwaysApply:true → alwaysApply:false\n     (agent-requestable / tag-triggered only).\n  2. Trimming verbose always-apply rules by extracting large tables/examples into\n     requestable companion files.\n  3. Keeping a compact always-apply core that covers safety-critical guardrails only.\n\nTarget: always-apply budget ≤ 12,000 tokens (down from 25,559).\nNothing important is dropped — all rules remain available, just not injected by default.\n"
updated: 2026-03-09
isProject: false
todos:
- {id: phase1-demote-schema-rules, content: 'Phase 1 — Demote 8 large schema/import rules to alwaysApply:false', status: done}
- {id: phase2-demote-breaking-change, content: 'Phase 2 — Demote breaking-change-major-version-protocol to alwaysApply:false', status: done}
- {id: phase3-trim-verbose-always-apply, content: Phase 3 — Trim verbose sections from 8 medium always-apply rules, status: done}
- {id: phase4-token-opt-self-ref, content: 'Phase 4 — Fix token-optimization.mdc self-contradiction (says alwaysApply:true but describes @tag activation)', status: done}
- {id: phase5-verify, content: 'Phase 5 — Verify always-apply budget is ≤12K tokens, run quality gates', status: done}
---

# Context Bloat Reduction Plan

## Problem

| Source                                | Tokens             | Notes                           |
| ------------------------------------- | ------------------ | ------------------------------- |
| Always-apply rules (46 files)         | **25,559**         | Loaded every turn               |
| Requestable rules (80 files)          | 27,706             | Only when referenced            |
| AGENTS.md × 57 repos                  | ~12,039            | All workspace repos, every turn |
| Git status × 59 repos                 | ~10,000            | Injected by Cursor system       |
| Per-repo `.cursorrules` (active file) | 4,000–18,000       | Depends on open file            |
| **Session start total**               | **~55,000–70,000** | Before any user message         |

Always-apply rules are the only thing we can directly control. Everything else (AGENTS.md, git status, `.cursorrules`)
is Cursor system injection.

---

## Completed

- [x] Removed 61 broken symlinks from `unified-trading-pm/.cursor/rules/` (broken symlinks → 0 tokens, deletion has no
      effect on loaded rules)

---

## Phase 1 — Demote 5 Large Schema/Import Rules (saves ~4,579 tokens)

These rules cover schema placement and import direction for UAC/UIC. They are essential when writing schema code, but
irrelevant when working on CI scripts, docs, plans, or debugging. They should be **requestable** (via tag or description
match), not always injected.

| File                                       | Tokens | Action               |
| ------------------------------------------ | ------ | -------------------- |
| `core/schema-governance-index.mdc`         | 1,341  | `alwaysApply: false` |
| `imports/no-schema-outside-contracts.mdc`  | 1,208  | `alwaysApply: false` |
| `imports/service-domain-schema-in-uic.mdc` | 899    | `alwaysApply: false` |
| `imports/uic-may-import-uac.mdc`           | 705    | `alwaysApply: false` |
| `imports/adapter-models-belong-in-uac.mdc` | 612    | `alwaysApply: false` |
| `core/canonical-schema-semver.mdc`         | 615    | `alwaysApply: false` |
| `core/provider-api-version-manifest.mdc`   | 564    | `alwaysApply: false` |
| `core/schema-service-owned.mdc`            | 435    | `alwaysApply: false` |

**Safeguard:** Keep a 3-line always-apply pointer in `core/schema-governance-index.mdc` that says "for schema work, see
schema-governance-index" — the full rule content moves to requestable. This preserves discoverability without the token
cost.

**Savings: ~6,379 tokens**

---

## Phase 2 — Demote Breaking-Change Protocol (saves ~3,366 tokens)

`dependencies/breaking-change-major-version-protocol.mdc` is the single largest always-apply rule at **3,366 tokens
(13KB)**. It contains extensive tables covering every type of breaking change, commit format examples, and tier-ordered
migration instructions.

This rule is only relevant when making a library breaking change — a relatively rare event. It should be requestable,
not injected every turn.

**Action:** `alwaysApply: false`

**Safeguard:** `core/conventional-commits.mdc` (807 tokens, stays always-apply) already contains the commit format rule.
It links to the protocol for the full breaking-change protocol. Discoverability preserved.

**Savings: ~3,366 tokens**

---

## Phase 3 — Trim Verbose Sections from Medium Always-Apply Rules (saves ~2,500 tokens)

These rules must stay always-apply (they prevent critical mistakes every session), but their current content includes
large tables, extensive examples, and history sections that could be trimmed or moved to a companion requestable file.

### 3a. `core/always-use-quickmerge.mdc` (816 tokens → target 350)

- Keep: RULE, Three-Tier Branch Model table, DO/NEVER.
- Move to requestable companion: full key-flags reference, nothing-to-commit pattern, detailed staging vs main decision
  tree.

### 3b. `core/instruments-domain-and-api-keys.mdc` (850 tokens → target 400)

- Keep: Import pattern blocks, API key secret names, NEVER list.
- Move to requestable: full narrative explanation of Service→UDS→UCS boundary.

### 3c. `core/event-logging.mdc` (405 tokens → target 200)

- Keep: import pattern, setup_service pattern, DO/NEVER.
- Move: full list of 11+12 lifecycle events with descriptions.

### 3d. `core/anti-patterns-quick-reference.mdc` (673 tokens → target 400)

- Keep: the table (it's a reference, dense format is fine).
- Remove: verbose duplicate explanations that repeat rules already in other files.

### 3e. `core/no-backward-compat-shims.mdc` (694 tokens → target 350)

- Keep: RULE, prohibited examples (2), required example (1), exception.
- Remove: Quality Gate Check bash snippet (redundant — QG enforces this automatically).

### 3f. `core/delete-deprecated.mdc` (637 tokens → target 300)

- Keep: Core rule, NO backward compat section, NEVER list.
- Remove: "When to delete" examples list (redundant with NEVER list).

**Savings: ~2,500 tokens**

---

## Phase 4 — Fix token-optimization.mdc Self-Contradiction (saves ~1,083 tokens)

`core/token-optimization.mdc` is tagged `alwaysApply: true` but its description says _"use @token-optimization to
activate"_ — it was designed as a tag-triggered rule, not an always-apply rule. This is a self-contradiction that costs
1,083 tokens every turn. The rule instructs the agent to be token-efficient, which is ironic.

**Action:** `alwaysApply: false`

The token-optimization instructions are only needed when explicitly working in high-token-cost sessions. The
`@token-optimization` tag activates it on demand.

**Savings: ~1,083 tokens**

---

## Phase 5 — Verify Budget

After all phases:

| Phase                             | Saves  | Running Total      |
| --------------------------------- | ------ | ------------------ |
| Baseline                          | —      | 25,559 tokens      |
| Phase 1 (schema rules demoted)    | −6,379 | 19,180 tokens      |
| Phase 2 (breaking-change demoted) | −3,366 | 15,814 tokens      |
| Phase 3 (trim verbose)            | −2,500 | 13,314 tokens      |
| Phase 4 (token-opt demoted)       | −1,083 | **~12,231 tokens** |

Target: **≤ 12,000 tokens** always-apply. This is achievable within these phases.

### Verification command

```bash
RULES="/path/to/unified-trading-pm/cursor-rules"
always_bytes=$(grep -rl "alwaysApply: true" "$RULES/" | xargs cat | wc -c)
echo "Always-apply: $((always_bytes/4)) tokens"
```

---

## Rules That Must Stay Always-Apply (non-negotiable)

These are session-safety guardrails. If the agent forgets any of these even once, it causes real damage (data loss,
broken CI, security issues):

| Rule                                               | Tokens             | Why always-apply                           |
| -------------------------------------------------- | ------------------ | ------------------------------------------ |
| `core/never-revert-local-changes.mdc`              | 635                | git reset --hard destroys work             |
| `core/no-summary-docs.mdc`                         | 637                | Creates unwanted files every session       |
| `core/runtime-verification-required.mdc`           | 188                | Prevents false "done" claims               |
| `core/always-use-quickmerge.mdc`                   | 816                | Wrong git command breaks CI                |
| `core/delete-deprecated.mdc`                       | 637                | Parallel code paths = silent bugs          |
| `core/no-backward-compat-shims.mdc`                | 694                | Re-exports cause invisible drift           |
| `core/agents-follow-cursor-rules.mdc`              | 264                | Sub-agents need explicit rule injection    |
| `core/search-before-implementing.mdc`              | 362                | Prevents duplicating library code          |
| `core/cloud-agnostic.mdc`                          | 426                | Direct SDK imports break cloud portability |
| `core/external-import-standards.mdc`               | 403                | Wrong import paths break 30+ repos         |
| `core/utc-datetime.mdc`                            | 191                | Naive datetimes = silent partition bugs    |
| `core/conventional-commits.mdc`                    | 807                | Wrong commit format = no version bump      |
| `core/rule-amnesia-detection.mdc`                  | 172                | Catch context loss early                   |
| `core/parallel-agent-execution.mdc`                | 187                | Core workflow efficiency                   |
| `core/accurate-codebase-analysis.mdc`              | 367                | Wrong analysis wastes sessions             |
| `core/plan-placement.mdc`                          | 723                | Plans in wrong place = lost coordination   |
| `core/anti-patterns-quick-reference.mdc`           | 673 (→350 trimmed) | Daily reference                            |
| `core/basedpyright-safety.mdc`                     | 216                | OOM kills from wrong command               |
| `core/event-logging.mdc`                           | 405 (→200 trimmed) | Required in every service                  |
| `core/batch-live-symmetry.mdc`                     | 315                | Architecture invariant                     |
| `quality-gates/quality-gates-propagation-risk.mdc` | 534                | SSOT edits get overwritten                 |
| `core/single-project-id-env-var.mdc`               | 252                | CI breaks on wrong var name                |
| `workflow/plans-to-deployable-workflow.mdc`        | 424                | Workflow SSOT reference                    |
| `core/rollout-tracking.mdc`                        | 230                | Prevents "plan done" on 1 repo             |
| `core/sub-agent-workflow-standard.mdc`             | 182                | Agent launch protocol                      |
| `core/strict-quality-gates.mdc`                    | 193                | Blocking gate awareness                    |
| `config/workspace-venv-fallback.mdc`               | 479                | Prevents env confusion                     |
| `core/mandatory-setup-sh.mdc`                      | 293                | Repo setup invariant                       |
| `core/concurrency-max-workers.mdc`                 | 311                | OOM prevention                             |
| `core/async-http-aiohttp.mdc`                      | 219                | Blocks event loop                          |
| `core/hook-tooling-policy.mdc`                     | 234                | Hook consistency                           |
| `core/context7-usage.mdc`                          | 236                | Prevents stale API usage                   |
| `core/cloud-build-test-in-image.mdc`               | 285                | Test artifact not source                   |
| `core/ui-service-separation.mdc`                   | 163                | Architecture boundary                      |
| `core/instruments-domain-and-api-keys.mdc`         | 850 (→400 trimmed) | Domain access pattern                      |
| `README.md`                                        | 712                | Rules index                                |

---

## Implementation Notes

- Changes are one-line edits: `alwaysApply: true` → `alwaysApply: false`
- Trimming phases require careful editing — preserve all RULE/DO/NEVER content, only remove extended examples and tables
  that duplicate other sources
- After each phase, run the verification command and confirm token count drops
- Commit via `bash scripts/quickmerge.sh "chore(cursor-rules): reduce always-apply token budget"`
- Teammate gets the changes via `git pull` on unified-trading-pm
