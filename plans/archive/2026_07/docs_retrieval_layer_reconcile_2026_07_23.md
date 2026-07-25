---
doc_type: plan
title: Docs retrieval-layer reconcile — AGENTS.md doctrine gap + schema/generator parity QG + /docs-reconcile skill
summary:
  Closes a real gap found while checking whether the L0/L1/L2 grep-native doc-retrieval design (DOC_INDEX.generated.md)
  is still followed — AGENTS.md never actually carried the "grep DOC_INDEX first" doctrine despite a claim that it did,
  so Codex/Cursor agents never got it. Adds the missing instruction, a QG parity check guarding gen_doc_index.py against
  silently drifting from docspec's schema, and a new /docs-reconcile skill scoped to retrieval-layer + codex doc health
  (distinct from /plan-reconcile's plan-lifecycle scope).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [doc-retrieval, l0-index, docspec, agent-operating-framework, quality-gates, docs-reconcile]
related:
  [
    agent_operating_framework_master,
    l0_doc_index_generator_2026_06_24,
    doc_frontmatter_schema_and_validator_2026_06_24,
    plan-reconcile,
  ]
created: 2026-07-23
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
last_updated: 2026-07-23
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "operator conversation 2026-07-23 — Slack thread on the DOC_INDEX L0/L1/L2 retrieval design, forwarded by operator"
assigned_role: infra
drift_direction: advance-code
---

# Docs retrieval-layer reconcile

## Why

Slack thread (harsh → ikenna, forwarded 2026-07-23): harsh built the grep-native L0→L1→L2→L3 doc-retrieval design
(`DOC_INDEX.generated.md` as L0, frontmatter as L1, the doc body as L2/L3) and said "agents are asked to grep this one
first via AGENTS.md file... havent checked in a while if there is any deviations from this." Checking turned up a real
deviation: **the grep-first instruction lives only in `cursor-configs/CLAUDE.md`** (Claude Code's own file) —
`AGENTS.md` (the file explicitly documented as "Shared instructions for all agents (Claude Code, Codex, Cursor)"),
`.cursorrules`, and `cursor-rules/` all have zero mentions of `DOC_INDEX`. So Codex/Cursor agents never actually
received the doctrine.

Separately: frontmatter-schema _structural_ correctness (required fields, closed-vocab enums) is already a hard-blocking
PM QG step (`check_frontmatter_schema.py`, docspec-backed, since 2026-07-04) — that part is NOT the gap. The gap is
retrieval-layer _mechanics_: (1) the doctrine's cross-surface reach, and (2) `gen_doc_index.py`'s hand-maintained
`_PER_TYPE_FACETS` dict silently drifting from `docspec.py`'s `PER_TYPE`/`DOC_TYPES` if the schema grows a new doc_type
or a per-type field gets renamed — nothing currently catches that class of drift.

## Scope

- Fix the concrete AGENTS.md gap directly (not just detect it going forward).
- Add a QG check that keeps `gen_doc_index.py` honest against `docspec.py` (the schema's machine SSOT) and keeps the
  doctrine's cross-surface presence from silently regressing again.
- Author a new `/docs-reconcile` skill, scoped to retrieval-layer + codex doc health — kept SEPARATE from
  `/plan-reconcile` (already a dense 317-line skill tightly scoped to plan-lifecycle contradictions/archival; bolting a
  different corpus + different failure class onto it blurs scope for both).

## Todos

- [x] 1. ✅ [SCRIPT] P1. Add a "Doc retrieval (L0→L4, grep-native)" section to `AGENTS.md` mirroring
      `cursor-configs/CLAUDE.md`'s — closing the gap where Codex/Cursor agents never received the grep-DOC_INDEX-first
      instruction. — unified-trading-pm@fdbad80ab
- [x] 2. ✅ [SCRIPT] P1. Write `scripts/quality_gates/check_doc_retrieval_layer_parity.py`: (a) asserts every non-exempt
      `docspec.DOC_TYPES` value has a `gen_doc_index._PER_TYPE_FACETS` entry whose facet names are real per-type fields
      in `docspec.PER_TYPE`; (b) asserts the DOC_INDEX grep-first doctrine is referenced in both
      `cursor-configs/CLAUDE.md` and `AGENTS.md`. — unified-trading-pm@fdbad80ab
- [x] 3. ✅ [SCRIPT] P1. Wire the new checker into `quality-gates.sh` post-gates as a hard-fail step, following the
      existing frontmatter-schema/codex-freshness call pattern (`_post_gate_fail`). — unified-trading-pm@fdbad80ab
- [x] 4. ✅ [SCRIPT] P2. Add paired unit tests (`test_check_doc_retrieval_layer_parity.py`) covering: live corpus is
      clean, an injected missing/renamed facet is caught, an injected missing-doctrine-mention is caught. —
      unified-trading-pm@fdbad80ab
- [x] 5. ✅ [SCRIPT] P1. Author `cursor-configs/skills/docs-reconcile/SKILL.md` — retrieval-layer + codex doc health
      audit (index/schema parity, cross-agent-instruction parity, `authoritative_for` collision sweep, codex-freshness
      scope widening as report-only), explicitly out of `/plan-reconcile`'s plan-lifecycle scope. —
      unified-trading-pm@fdbad80ab
- [x] 6. ✅ [SCRIPT] P0. Run the new checker + its tests directly, and the PM frontmatter-schema/freshness gates over
      the touched files, and confirm green before commit. — verified via 5x full `bash scripts/quality-gates.sh` local
      runs, final run EXIT_CODE=0 with `Doc retrieval-layer parity check passed` + `1331 passed, 2 skipped` (no PM QG
      failures).
- [x] 7. ✅ [SCRIPT] P0. Commit + push via `quickmerge.sh --agent`, citing `<repo>@<sha>` evidence, and flip every todo
      checkbox above in the same turn. — unified-trading-pm@fdbad80ab (PR #1384, auto-merge enabled targeting main).

## Progress Log

- 2026-07-23: Plan authored (human/local track per operator's explicit "human plan" ruling). Scope decided:
  `/docs-reconcile` as a NEW skill rather than extending `/plan-reconcile` — see "Scope" above for the reasoning
  (different corpus, different failure class, plan-reconcile already dense).
- 2026-07-23: All todos shipped in one commit (unified-trading-pm@fdbad80ab, PR #1384). Two adjacent findings surfaced
  and were handled outside this plan (not scope-creep into it, per findings-triage): (1) a separately-flagged hardcoded
  `/home/ubuntu/...` absolute path in `cursor-configs/settings.json`'s hook `command` strings — fixed locally to
  `$CLAUDE_PROJECT_DIR`-relative, then DISCARDED unstaged when `ps aux` showed two other slots (.tabs/3, .tabs/4)
  actively committing their own fix for the identical lines from the same operator thread; their landed fix used the
  same `$CLAUDE_PROJECT_DIR` convention, confirming the approach without duplicating the commit. (2) Shipping the commit
  took 12 quickmerge attempts — the shared branch was under unusually heavy concurrent-agent commit pressure (multiple
  slots landing `docs(plans):` commits every ~20-30s), each attempt racing `check-branch-drift` against quickmerge's own
  ~1-2min internal pass; resolved via the documented pull-`--ff-only`-then-retry loop (never the human-only
  `SKIP_BRANCH_DRIFT` override) until a gap opened.

> **✅ COMPLETE — archived by plan_reconciler (agt-be8370, 2026-07-25).** All todos verified done (0 open checkboxes),
> unlocked, no un-migrated deferrals (STEP 5f archive ritual).

## Deferred work — migrated to:

none
