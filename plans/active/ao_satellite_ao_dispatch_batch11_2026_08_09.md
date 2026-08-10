---
doc_type: plan
title: AO satellite AO batch 11 — fix_frontmatter.py's summary-truncation bug (agent_operating_framework_master epic)
summary: >-
  ELEVENTH AO-dispatch batch for the `ao` topic tranche — a single-item satellite extraction from
  `docs_reconcile_remaining_broken_links_2026_08_02.md`, a 12-open-todo `assigned_vm: NA` doc whose remaining items are
  otherwise all genuine human-judgment/design calls (which dead link gets which successor, a root-README onboarding
  pass, an authority-adjacent content-staleness gap). Split into its own batch rather than folded into batch10 because
  its `parent_epic` is `agent_operating_framework_master` (doc/plan-hygiene tooling), not `orchestrator_master` (the AO
  service itself) — per the naming-and-conflict-check SSOT's grouping rule, `parent_epic` is the clean axis for which
  batch an item belongs to. The extracted item is `scripts/plan-hygiene/fix_frontmatter.py`'s
  `get_first_paragraph_after_heading()` hard-truncating a doc's auto-backfilled `summary:` field at exactly 197 chars
  with no word/sentence-boundary awareness — the source doc's own 2026-08-08 `na-eligibility-audit` pass already flagged
  this exact item `MISCLASSIFIED_LIKELY_AO_ELIGIBLE`, naming the function, the bug, and a recommended fix, while
  correctly keeping the whole doc `NA` because its 11 sibling items are genuine judgment calls.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-11, satellite-docs, satellite-extraction, docs-tooling]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch11_finalize_2026_08_09.md,
    /plans/active/issues/docs_reconcile_remaining_broken_links_2026_08_02.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/docs_reconcile_remaining_broken_links_2026_08_02.md,
    scripts/plan-hygiene/fix_frontmatter.py,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
source: >-
  Satellite-batch-extraction pass, 2026-08-09, mirroring `/ag-closeout-audit`'s satellite-batch pattern per operator
  instruction — a targeted per-item extraction over the 21 `ao`-tranche `assigned_vm: NA` docs a same-day RECLASSIFY
  sweep read end-to-end without a whole-doc flip. This item was independently flagged bounded/AO-eligible by the source
  doc's own 2026-08-08 `na-eligibility-audit` Progress Log entry (quoted in the todo below) before this batch ever ran —
  this extraction acts on that prior flag rather than re-deriving the classification from scratch.
---

# AO satellite AO batch 11

> **`status: draft`** — pending operator approval, same convention as batch5-10: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

`docs_reconcile_remaining_broken_links_2026_08_02.md` carries 12 open todos, 11 of which are genuine human-judgment
calls (which dead link gets which successor / prose target, a root-README onboarding-doc pass explicitly scoped out "to
avoid an under-verified rewrite," and a design observation the doc's own text says "not proposing a fix here"). The 12th
— a `[SCRIPT] P2` item added 2026-08-08 — is different in kind: it names the exact function, the exact bug, and a
specific recommended fix, with no remaining judgment. The doc's own 2026-08-08 `na-eligibility-audit` verdict already
caught this ("MISCLASSIFIED_LIKELY_AO_ELIGIBLE... flagging for a future partial split rather than acting on it here")
but correctly did not act on it, since a single skill invocation doesn't split docs — that partial split is what this
batch performs.

## Rules for every worker on this plan

- **Do not edit the source doc's remaining 11 checkboxes** or this todo's own redirect-pointer beyond appending your
  evidence when done. The paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch11_finalize_2026_08_09.md`)
  reconciles evidence back into the source doc.
- This is a shared frontmatter-tooling script every `docs-reconcile`/`na-eligibility-audit`/`fix_frontmatter.py` caller
  depends on — run the full `scripts/plan-hygiene/` test suite, not just a new unit test for this function.

## Todos

- [x] ✅ [SCRIPT] P2. **Fix `scripts/plan-hygiene/fix_frontmatter.py`'s `get_first_paragraph_after_heading()` hard
      truncation.** — unified-trading-pm@2022f4142f. **Evidence**: replaced hard `result[:197] + "..."` with
      sentence-boundary-aware truncation (prefers `.`/`!`/`?` + space before 197 chars, falls back to word boundary,
      last resort hard cut). 6 regression tests (sentence-boundary, word-boundary, short/no-op, exactly-200,
      unbroken-token-hard-cut, no-paragraph-returns-None) all pass; existing 20 fix_frontmatter tests stay green;
      `bash scripts/quality-gates.sh` ALL QUALITY GATES PASSED.

## Codex SSOTs (read before starting)

`/codex/11-project-management/doc-frontmatter-schema.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

## Progress Log

- **2026-08-09** — Authored by a satellite-batch-extraction pass over the 21 `ao`-tranche `assigned_vm: NA` docs named
  in the parent RECLASSIFY sweep's candidate list. Conflict-check before drafting: grepped `plans/active/*.md` for
  `get_first_paragraph_after_heading`/`fix_frontmatter.py` — 2 hits (`defi_consolidated_closeout_2026_07_18.md`,
  `lst_rate_honest_coverage_2026_07_21.md`), both about an UNRELATED `last_updated` auto-fill defect in the same script,
  not this summary-truncation bug — no overlap, clear to extract. Split into its own batch (rather than folded into
  `ao_satellite_ao_dispatch_batch10_2026_08_09.md`) solely because its source doc's
  `parent_epic: agent_operating_framework_master` differs from batch10's `orchestrator_master` group — per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2, `parent_epic` (not `asset_group`) is
  the grouping axis. A 1-item batch is sanctioned by `task_template.md` §4 ("Fewer is fine; group RELATED items") and
  has direct precedent (`ao_satellite_ao_dispatch_batch9_2026_08_08.md`, also 1 todo).
