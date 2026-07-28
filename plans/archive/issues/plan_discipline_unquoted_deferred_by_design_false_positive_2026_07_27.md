---
doc_type: issue
title:
  "check_plan_discipline.py rule A-deferred-no-banner false-positives on an UNQUOTED report-prose mention of another
  doc's 'DEFERRED-BY-DESIGN' status — the quoted-reference exclusion doesn't cover this phrasing variant"
summary: >-
  `plans/active/june_2026_vintage_audit_findings_2026_07_27.md:378` reads "confirmed stays DEFERRED-BY-DESIGN, no
  timeline." with no quote marks around the token, reporting a DIFFERENT doc's (`e2e_defi_config_taxonomy_wizard_
  roundtrip_2026_06_17.md`) own deferred-by-design status inside a vintage-audit findings report. `_has_live_deferred_
  marker()`'s quoted-reference exclusion (added 2026-07-26 for `plan_discipline_quoted_deferred_false_positive_2026_
  07_26.md`) only excludes a DEFERRED token immediately preceded by an opening quote char — it does not cover this
  unquoted reporting-prose phrasing, so the checker demands a `## Deferred work — migrated to:` banner on a vintage-
  audit report doc that has no actual deferred work of its own. Same false-positive CLASS as the 07-26 issue, a fresh
  phrasing variant the existing exclusion regex doesn't catch. Regressed PM's `plan-discipline` post-gate (baseline 0 ->
  1), discovered while shipping an unrelated `sports_shard_enumeration_cartesian_blowup_2026_07_20.md` doc correction
  (worked around via the CLAUDE.md "pure doc/plan-flip -> prek only" carve-out, which does not run this corpus-wide
  check).
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-discipline, quality-gates, false-positive, checker-calibration]
related:
  [
    /plans/active/june_2026_vintage_audit_findings_2026_07_27.md,
    /scripts/quality_gates/check_plan_discipline.py,
    /plans/archive/issues/plan_discipline_quoted_deferred_false_positive_2026_07_26.md,
  ]
created: 2026-07-27
last_updated: 2026-07-28
parent_epic: agent_operating_framework_master
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
depends_on: []
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
resolved_by: unified-trading-pm@ddf138deb (2026-07-27, already shipped before this doc's own todo was verified)
source: ["slot 8, data_engineering, 2026-07-27, discovered while shipping sports_satellite_ao_dispatch_batch3-011"]
---

> **✅ RESOLVED — `unified-trading-pm@ddf138deb`.** Already fixed by a concurrent session before this doc's todo was
> picked up: `_DEFERRED_BY_DESIGN_RE` fullmatch exclusion added, covering exactly this unquoted-report-prose class,
> with a regression test using this doc's own cited text. Archived.

## What I found

`scripts/quality_gates/check_plan_discipline.py`'s `_has_live_deferred_marker()` excludes a `DEFERRED` token only when
it is immediately preceded by an opening quote character (`_QUOTE_CHARS`). Line 378 of
`plans/active/june_2026_vintage_audit_findings_2026_07_27.md` reads "5. e2e_defi_config_taxonomy D1 — confirmed stays
DEFERRED-BY-DESIGN, no timeline." — no quote marks — reporting that a DIFFERENT doc
(`e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`) remains deferred-by-design, inside this doc's own
vintage-audit findings report. The vintage-audit doc has no deferred work of its own; the check nonetheless demands a
`## Deferred work — migrated to:` banner. This regressed the `plan-discipline` post-gate (baseline 0 → 1), which blocks
full `quality-gates.sh` for any agent touching unrelated `plans/active/*.md` files (the check scans the whole corpus,
not just staged files).

## Why it matters

Same false-positive class as `plan_discipline_quoted_deferred_false_positive_2026_07_26.md` (resolved 2026-07-26), a
fresh phrasing variant the fix's exclusion regex doesn't cover (unquoted reporting prose, not a quoted citation). It
blocks the corpus-wide `plan-discipline` post-gate for anyone running full `quality-gates.sh`, forcing reliance on the
`pure doc/plan-flip → prek only` carve-out rather than a genuine fix.

## Recommended decision

Extend `_has_live_deferred_marker()`'s exclusion to also treat a DEFERRED token as a quoted/reported reference when it
follows report-prose verbs commonly used to describe ANOTHER doc's status (e.g. "confirmed stays", "remains", "stays") —
or, more robustly, only treat a DEFERRED token as a live in-doc marker when it appears inside an actual open `- [ ]`
todo line for THIS doc (vintage-audit / consolidated-findings report docs enumerate other docs' items as prose, not as
their own todos). Re-baseline `plan_discipline_baseline.yaml` to 0 after the fix.

- [x] [SCRIPT] P3. ✅ **STALE-CONFIRMED-DONE (2026-07-28)** — already fixed by a concurrent session, prior to this pickup:
      `unified-trading-pm@ddf138deb` ("plan-discipline DEFERRED-BY-DESIGN false-positive fix") added
      `_DEFERRED_BY_DESIGN_RE = re.compile(r"\bDEFERRED-BY-DESIGN\b")` + a `fullmatch` exclusion in
      `_has_live_deferred_marker()` for exactly this class (any first-party `DEFERRED-BY-DESIGN` token, quoted or not —
      it's a closed/permanent ruling, not a live marker needing a migration banner), plus a regression test
      (`tests/unit/test_check_plan_discipline.py::test_deferred_by_design_is_not_live`, using the EXACT
      `june_2026_vintage_audit_findings_2026_07_27.md:378` text this issue cites) and a companion
      `test_deferred_by_design_does_not_mask_a_real_marker_elsewhere`. Re-verified live: full-corpus
      `check_plan_discipline.py --workspace-root <ws>` → `Scanned plans/active/ (252 plans) + issues + archive — 0
      violation(s). ✅ At baseline (0).`; `pytest tests/unit/test_check_plan_discipline.py` → 10 passed. No new code
      needed — confirming + citing the existing fix.
