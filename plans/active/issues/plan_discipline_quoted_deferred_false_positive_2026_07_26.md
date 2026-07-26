---
doc_type: issue
title:
  "check_plan_discipline.py rule A-deferred-no-banner false-positives on a DEFERRED token that appears inside a QUOTED
  reference to another document's own annotation, not a live in-doc deferred marker"
summary: >-
  `plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md` line ~530 quotes another issue doc's own annotation
  ("...explicitly annotated in the doc itself as \"DEFERRED —...\"") while describing a Phase-1 finding. The checker's
  `_DEFERRED_RE` matches the bare `DEFERRED —` token regardless of quoting context, so it demands a `## Deferred work —
  migrated to:` banner on a document that has no actual deferred work of its own — adding one would be a fabricated
  banner, not a real fix. This regressed PM's `plan-discipline` post-gate (baseline 0 → 1), blocking `quality-gates.sh`
  for anyone touching unrelated `plans/active/*.md` files (worked around this session via the CLAUDE.md `pure
  doc/plan-flip → prek only` carve-out, which does not run this corpus-wide check).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-discipline, quality-gates, false-positive, checker-calibration]
related:
  [/plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md, /scripts/quality_gates/check_plan_discipline.py]
created: 2026-07-26
priority: P3
parent_epic: agent_operating_framework_master
source: ["slot 6, data_engineering, 2026-07-26, discovered while shipping cefi_satellite_ao_dispatch_batch2-003"]
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
---

## What I found

`check_plan_discipline.py`'s `_DEFERRED_RE` (`\bDEFERRED\b\s+[—-]`) matches a DEFERRED token regardless of whether it
sits inside a quoted reference to another document's annotation. Line ~530 of
`plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md` reads: "...is explicitly annotated in the doc itself as
'DEFERRED —...'" — this is REPORTING that a DIFFERENT doc
(`plans/active/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`) carries a DEFERRED annotation, not
declaring THIS doc's own work deferred. The checker has no in-doc deferred work to point a banner at, so satisfying the
rule would mean adding a `## Deferred work — migrated to:` section that doesn't correspond to anything real.

## Why it matters

This is the same false-positive CLASS already documented in the checker's own comments (quoting/prose vs a live marker)
— this is a fresh instance of it, not a new class. It currently blocks `quality-gates.sh`'s `plan-discipline` post-gate
for ANY agent touching unrelated `plans/active/*.md` files (the check scans the whole corpus, not just staged files),
which is why the `pure doc/plan-flip → prek only` carve-out exists — but that carve-out is a workaround, not a fix, and
doesn't help an agent that genuinely needs the full `quality-gates.sh` green (e.g. shipping code + docs together).

## Recommended decision

- [ ] [SCRIPT] P3. Extend `_DEFERRED_RE`'s exclusion set (or add a companion "quoted" filter) so a DEFERRED token inside
      a markdown-quoted span (`"..."` immediately following "annotated ... as") doesn't count as a live in-doc marker.
      Mirror the precision fixes already applied to `_ARCHIVE_OK_TOKENS_RE` (2026-07-25) — same philosophy, new pattern.
      Alternatively: don't over-engineer the regex — just re-baseline this ONE genuine false-positive after confirming
      (via the same reasoning above) that no real deferred work is being masked, citing this issue doc as the sign-off
      note. Either resolves the current 0→1 regression. (repo: unified-trading-pm)

## Codex SSOTs

None new — this is a checker-calibration bug in `scripts/quality_gates/check_plan_discipline.py`, not a doc-content or
architecture question.
