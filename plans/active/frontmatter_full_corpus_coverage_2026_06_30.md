---
doc_type: plan
title: Full-corpus frontmatter coverage — seed + enum-normalize every live doc_type to the schema
summary: Extend the mechanical frontmatter rollout from plans/active to the WHOLE live corpus (codex, issues, epics, audit-results, audit-instructions, cursor-rules, agent-roles) AND add the enum-normalization pass the bare seeder cannot do (cross-asset->cross-cutting, data-ingestion->data, ...), so docspec.py is HARD-green on every non-exempt live doc. summary/tags/authoritative_for content stays present-but-empty (deferred content pass).
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [frontmatter, docspec, grep-native, enum-normalization, doc-governance, full-corpus]
related: [plans_active_frontmatter_mechanical_rollout_2026_06_27.md, doc_frontmatter_schema_and_validator_2026_06_24.md, ../epics/agent_operating_framework_master.md, ../../codex/11-project-management/doc-frontmatter-schema.md]
created: 2026-06-30
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.25
last_updated: 2026-06-30
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [plans_active_frontmatter_mechanical_rollout_2026_06_27]
source: [operator request 2026-06-30 — roll the frontmatter coverage out across ALL live doc_types while there is no collision risk; reuses scripts/docs/seed_frontmatter.py + docspec.py shipped by the W2/W3 plans]
assigned_role: infra-engineer
drift_direction: advance-code
---

# Full-corpus frontmatter coverage

The `plans/active` mechanical rollout (`plans_active_frontmatter_mechanical_rollout_2026_06_27`) covered only the 123
top-level active plans. This plan finishes the corpus: every other live `doc_type` gets the same structural seed, **plus**
the enum-normalization pass that the bare seeder cannot do (it preserves existing values, so legacy closed-vocab values
survive HARD-red).

## Two jobs

1. **Structural seed** — `seed_frontmatter.seed_fields` fills `doc_type` + derivable universal-core/per-type fields,
   preserves existing values, leaves `summary`/`tags`/`authoritative_for` present-but-empty (deferred content pass).
2. **Enum normalization** (the seeder will NOT do this) — rewrite legacy closed-vocab values to the schema enum (§5):
   `asset_group: cross-asset → cross-cutting` (151), `crypto → [cefi, defi]` (operator 2026-06-30), upper→lower casing;
   `stage: data-ingestion → data`, `feature-eng → features`, `infra → meta`; `nature: audit → record`, `bug/investigation
   → notes`, `contract → spec`; drop non-audience `scope` leakage → `[engineer, admin]`; strip `.md` + infer a missing
   `parent_epic` for issues/audit docs (per-doc by filename token, default `infrastructure_master`).

Verification target per tree: `python3 scripts/docs/docspec.py --check <glob>` exits 0 on HARD. SOFT (empty
`summary`/`tags`/`authoritative_for`) is the deferred content pass — out of scope here, same as the W3 rollout.

## Codex SSOTs

- [`codex/11-project-management/doc-frontmatter-schema.md`](../../codex/11-project-management/doc-frontmatter-schema.md)
  — universal-core + per-type fields + the §5 closed-vocab enums this pass targets.
- Tooling: `scripts/docs/seed_frontmatter.py` (`--apply`) + `scripts/docs/docspec.py` (`--check`).

## Baseline (docspec, 2026-06-30, non-exempt live docs)

| doc_type | location | non-exempt | clean | needs work |
| --- | --- | ---: | ---: | ---: |
| codex-ssot/runbook | `codex/**` | 807 | 10 | 797 |
| cursor-rule | `**/*.mdc` | 179 | 0 | 179 |
| plan | `plans/active/*.md` | 121 | 27 | 94 |
| audit-result | `plans/audit/results` | 84 | 5 | 79 |
| issue | `plans/active/issues` | 81 | 9 | 72 |
| epic | `plans/epics` | 27 | 1 | 26 |
| audit-instruction | `plans/audit/instructions` | 20 | 5 | 15 |
| agent-role | `agent-orchestrator/agents` | 15 | 14 | 1 |

Out of scope: `plans/archive/` + `plans/ai/` (validator returns `doc_type: None` by design — frozen historical state).

## Todos

- [x] ✅ [SCRIPT] P2. **Fix the one malformed-YAML doc.** `codex/15-runbooks/vm-log-observability-verify.md` had a
      backtick-started `verifier:` value (invalid YAML) — now double-quoted + seeded. **Gate**: docspec parses + HARD=0.
- [x] ✅ [SCRIPT] P2. **plans/active (top-level) — enum-normalize.** Ran the fix over `plans/active/*.md` (mostly already
      seeded; was failing on `cross-asset`/`data-ingestion`). **Gate**: `docspec --check plans/active/*.md` HARD=0 on all
      121 files I may touch (lone holdout `master_to_live_defi` is foreign-dirty WIP — skipped, not mine).
- [x] ✅ [SCRIPT] P2. **plans/active/issues — seed + normalize + parent_epic backfill.** **Gate**: `docspec --check
      plans/active/issues/*.md` HARD=0 (82 docs); every issue carries a real `parent_epic` (38 inferred by filename
      token, default `infrastructure_master`).
- [x] ✅ [SCRIPT] P2. **plans/epics — seed (legacy name/type → doc_type).** Kept `name` (the one place it survives),
      retired legacy `type:`, broke the related/related_plans YAML anchor. **Gate**: `docspec --check plans/epics/*.md`
      HARD=0 (27 docs).
- [x] ✅ [SCRIPT] P2. **plans/audit/results + instructions — seed + normalize.** Seeded 84 results + 20 instructions
      (30 results had no frontmatter at all); rehomed prose `scope`→`audited_scope`; inferred parent_epic where stale
      (e.g. cutover-master ref). **Gate**: docspec HARD=0 on both.
- [x] ✅ [SCRIPT] P2. **codex/** — seed + normalize (the 797).** Seeded 806 codex docs (ssot + runbook). **Gate**:
      `docspec --check $(find codex -name '*.md')` — 0 HARD-failing files.
- [ ] [SCRIPT] P2. **cursor-rules (.mdc) — add `doc_type: cursor-rule`.** **Gate**: docspec HARD=0 on all `.mdc`.
- [ ] [SCRIPT] P2. **agent-orchestrator/agents — finish the 1 straggler.** **Gate**: docspec HARD=0.
- [x] ✅ [SCRIPT] P3. **Fix the stale stage vocabulary in PLAN_FORMAT.md** (line ~89 comment listed `data-ingestion,
      feature-eng, ml` — contradicted the docspec enum). Now matches §5: `data, features, strategy, backtest, paper,
      live, execution, reporting, meta`. — unified-trading-pm PLAN_FORMAT.md

## Success criteria

- `docspec.py --check` is HARD-green across every non-exempt live doc tree (8 doc_types).
- Only mechanical/derivable fields + enum normalization changed; no `summary`/`tags`/`authoritative_for` content written;
  archive/ai untouched.

## Progress Log

- 2026-06-30 — Plan authored (operator request). Baseline measured with docspec: 1263 of 1334 non-exempt live docs need
  work, dominated by the never-seeded codex tree (797) + the `cross-asset → cross-cutting` enum mismatch (151 corpus-wide).
  Verified the normalization direction is code-safe (no code uses `cross-asset`/`cross-cutting`; pipeline `--asset-group`
  is only `cefi/defi/tradfi/sports/prediction`). Tool: a one-shot `fm_fix.py` (seed + normalize in one idempotent pass)
  kept in scratchpad, not committed.
