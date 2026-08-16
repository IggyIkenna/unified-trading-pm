---
doc_type: issue
title: "check_doc_body_links flags a known FALSE-POSITIVE placeholder row as a NEW broken link — regression from the 2026-08-16 bare-ref leading-slash migration commit"
summary: >-
  A documented FALSE-POSITIVE placeholder row in codex_plan_diff_scan_2026_05_22.md started
  tripping check_doc_body_links.py as a NEW broken link, blocking quickmerge's Stage-5 re-gate
  fleet-wide on unified-trading-pm; fixed same-session via --update-baseline.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, false-positive, doc-body-links, ci-red]
related: [/plans/active/infra_consolidated_closeout_2026_07_25.md]
created: "2026-08-16"
author: slot-13
last_updated: "2026-08-16"
parent_epic: infrastructure_master
priority: P2
source: >-
  Hit live 2026-08-16 shipping an unrelated fix (30 QG checkers missing .claude worktree
  exclusion, plans/active/issues/qg_checkers_missing_claude_worktree_exclusion_2026_08_06.md)
  — quickmerge's post-rebase re-gate failed on check_doc_body_links, blocking an otherwise-green
  commit that never touched the failing doc.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: unified-trading-pm@<pending-quickmerge-sha>
depends_on: []
---

> **ARCHIVED — resolved same-session 2026-08-16.** Baselined the false-positive link via
> `--update-baseline`; see Fix + Progress Log below.

# check_doc_body_links regression on a documented false-positive row

## What I found

`plans/audit/results/codex_plan_diff_scan_2026_05_22.md` line 62 is a table row whose own text
documents it as a **known FALSE-POSITIVE**: a template placeholder path
(`codex/09-strategy/architecture-v2/archetypes/<placeholder>.md`) quoted in backticks, explicitly
"De-fanged here so it no longer regex-matches as a real cross-doc reference." Despite that stated
intent, `scripts/quality_gates/check_doc_body_links.py`'s bare-backtick-path extractor (which matches
any backtick-quoted `codex/...\.md` token, `<placeholder>` notwithstanding) still parses it as a real
citation and flags it as a NEW broken link (not in `doc_body_link_baseline.yaml`).

This surfaced live 2026-08-16: commit `a5ad008366418472435040e507b5489d974f7813` (slot-7,
"docs(plans): fix 47 bare related: refs to leading-slash form, ratchet format_count baseline 81->0")
landed on `live-defi-rollout` shortly before an unrelated commit of mine (30 QG checkers gaining a
`.claude` worktree exclusion). Quickmerge's Stage-5 re-gate (which re-runs full QG against the
just-rebased tree) failed on this pre-existing regression — confirmed pre-existing because my own
diff never touches `codex_plan_diff_scan_2026_05_22.md`, and the failing row's own body text already
existed verbatim before my change.

## Why it matters

Any agent's quickmerge attempt on `unified-trading-pm` after this commit lands will hit the same
Stage-5 re-gate failure until it's fixed — a fleet-wide shipping blocker on this repo, not scoped to
one task.

## Recommended decision

Either (a) further de-fang the placeholder row's backtick span (e.g. break the `codex/...` token with
a zero-width marker or move it out of backticks entirely), or (b) run
`python3 scripts/quality_gates/check_doc_body_links.py --update-baseline` to add this specific
already-known-false-positive to the baseline (the doc's own row already carries the FALSE-POSITIVE
disposition — baselining it is the same triage decision the checker's baseline mechanism exists for).
Option (b) is the faster, lower-risk fix given the row is a documented false positive.

## Fix

- [x] ✅ [SCRIPT] P2. In `plans/audit/results/codex_plan_diff_scan_2026_05_22.md`, re-defang the
      line-62 placeholder row so `check_doc_body_links.py`'s bare-backtick-path extractor no longer
      matches it (or run `python3 scripts/quality_gates/check_doc_body_links.py --update-baseline`
      from the `unified-trading-pm` repo root to add it to `doc_body_link_baseline.yaml`), then verify
      `scripts/quality_gates/test_check_doc_body_links.py::test_live_corpus_has_zero_new_broken_body_links`
      passes clean. — Fixed same-session, option (b): ran `--update-baseline`, added
      `plans/active/issues/doc_body_link_regression_placeholder_archetype_2026_08_16.md::codex/09-strategy/architecture-v2/archetypes/<placeholder>.md`
      to `doc_body_link_baseline.yaml` (2 line diff).

## Progress Log

- **slot-13 2026-08-16**: found + fixed same session (baselined via `--update-baseline`); no
  separate fix-worker dispatch needed.
