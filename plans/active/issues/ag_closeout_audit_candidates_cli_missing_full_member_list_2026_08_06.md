---
doc_type: issue
title: >-
  generate_ag_closeout_audit_candidates.py --json never exposes the full member list — every single-tranche audit run
  re-derives it via a throwaway wrapper script
summary: >-
  `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche <t> --json` prints `covering_paths`,
  `total_members` (a count only), `never_cited` (the small subset), and `cited_somewhere_count` (a count only) — it
  never prints the full `candidates` list `main()` already builds in memory
  (`generate_ag_closeout_audit_candidates.py:180-243`). But `ag-closeout-audit` SKILL.md's own Phase 1 requires
  classifying EVERY AG-primary candidate, not just the never-cited ones ("Given the AG-primary candidate list from Phase
  0.3, launch a `Workflow`... over the doc list"). Since the CLI structurally cannot answer that need, every
  single-tranche run of this skill has to write its own throwaway script that imports the module and re-runs the same
  loop just to print `candidates` instead of dropping it — confirmed this exact workaround was needed for the 2026-08-06
  tradfi run (54 members vs. only 4 never-cited would have printed) and is a near-certain repeat for every tranche this
  skill has ever audited (the CLI's json branch has looked like this since the script existed — not a recent
  regression). This is a real, small, recurring inefficiency, not a one-off.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, ag-closeout-audit, tooling, cli, orphan-detection]
related:
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  [/plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md, /cursor-configs/skills/ag-closeout-audit/SKILL.md]
created: "2026-08-06"
author: slot-3 (ag_closeout_auditor, tradfi tranche, dispatch agt-7d91ed)
last_updated: "2026-08-06"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  /ag-closeout-audit tradfi run, 2026-08-06 (sharded scheduled `ag_closeout_auditor` worker, dispatch agt-7d91ed, slot
  3, operator away) — found during Phase 0.3 candidate discovery when the CLI's `--json` output only returned 4
  never-cited docs instead of the full 54-member candidate list Phase 1 needed, requiring a throwaway wrapper script
  (`importlib`-loading the module and re-running its own `_covering_paths`/`_iter_docs`/`_cited_basenames` loop) to get
  the real list.
depends_on: []
context_scope:
  [scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py, /cursor-configs/skills/ag-closeout-audit/SKILL.md]
---

# generate_ag_closeout_audit_candidates.py --json never exposes the full member list

## What I found

`main()` (`scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py:170-267`) builds a full `candidates` list (one
dict per AG-primary member, with `path`/`basename`/`assigned_vm`/`status`/`cited_in_covering_doc`/`self_dispatched`),
then derives `never_cited`/`cited_somewhere` from it — but the `--json` branch (lines 248-261) only serializes
`covering_paths`, `len(candidates)` (a bare count), `never_cited` itself, and `len(cited_somewhere)` (another bare
count). The full `candidates` list is computed and then discarded. The non-`--json` branch (lines 262-266) is even
narrower — it only prints `never_cited` entries.

This matters because `ag-closeout-audit` SKILL.md's Phase 1 explicitly needs the WHOLE candidate list for its per-doc
classification Workflow, not just the never-cited subset (never-cited is a strong orphan _signal_, but Phase 1's own
classification schema — `archivable_now`/`archivable_after_planned_work`/`orphaned_partial_coverage`/
`orphaned_never_touched`/`exclude_cross_cutting` — requires reading every member doc, including the "cited somewhere"
ones, since a citation doesn't mean full coverage). The tool that SKILL.md itself calls "the definition" of candidate
membership cannot answer the question the very next phase asks of it.

## Why it matters

Every single-tranche `/ag-closeout-audit <tranche>` run (the normal sharded-dispatch shape, one worker per tranche) has
to work around this by writing its own script that duplicates `main()`'s classification loop just to keep the
`candidates` list instead of dropping it — real but small wasted effort (~5-10 min) on every one of the 10 tranches,
every time this skill runs (daily, per the scheduled `ag_closeout_auditor` timer). Confirmed today for tradfi (needed
all 54 members; the CLI would only have surfaced 4). This has almost certainly been re-derived independently by every
prior batch1-6 tradfi run and by the other 9 tranches' own runs too — the CLI's shape hasn't changed since it was
written.

## Recommended fix

Add the full `candidates` list to the `--json` output dict (`generate_ag_closeout_audit_candidates.py:248-261`) — e.g.
`"candidates": candidates` alongside the existing keys. Purely additive (no existing key removed or renamed), so nothing
that already parses this CLI's output today would break. A future `ag_closeout_auditor` dispatch can then read
`candidates` directly instead of writing a fresh `importlib`-based wrapper each time.

## Todos

- [ ] [SCRIPT] P3. Add `"candidates": candidates` to the `--json` output dict in
      `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`'s `main()` (purely additive field). Confirm no
      existing caller depends on the current shape staying exactly as-is (grep the corpus for
      `generate_ag_closeout_audit_candidates.py --json` invocations first). Repo: unified-trading-pm. **Done when**:
      `--tranche <any> --json` includes a `candidates` array matching what `main()` already computes in memory, the
      existing `covering_paths`/`total_members`/`never_cited`/`cited_somewhere_count` keys are unchanged, and
      `quality-gates.sh` is green.
