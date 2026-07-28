---
doc_type: issue
title: >-
  plan-discipline ratchet (A-deferred-no-banner) regressed 0→1 on qg_host_adaptive_resource_governor_2026_07_14.md —
  blocks unrelated commits to unified-trading-pm
summary: >-
  `bash scripts/quickmerge.sh` for an unrelated docs-only commit (sports Track H denominator prereqs gating) failed its
  post-gate re-run on `plan-discipline` (exit non-zero, "Regression: 1 > baseline 0"). Verified pre-existing (clean
  `git diff`/`git log` on the flagged file show no touch of mine). The trigger is
  `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md:228` — `"**RESOLVED-BY-RULING, DEFERRED — cleaned
  2026-07-28 (stale-tag audit; this was never a live `[OPERATOR]` gate...)**"` — matching the checker's bare-marker
  regex (`\bDEFERRED\b\s+[—-]`). This is the SAME recurring false-positive class already fixed twice at the checker
  level (`plan_discipline_quoted_deferred_false_positive_2026_07_26.md`,
  `plan_discipline_deferred_banner_false_trip_june_vintage_2026_07_27.md` — resolved by exempting the
  `DEFERRED-BY-DESIGN` qualifier from the live-marker check): a CLOSED, resolved ruling ("this was never live,
  cleaned") with no successor to migrate to, just phrased as bare `DEFERRED — ` prose instead of the
  `DEFERRED-BY-DESIGN`/`RESOLVED-BY-RULING` qualifier forms the exemption already covers.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-discipline, quality-gates, ratchet, false-positive, repo-blocker]
related:
  [
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/archive/issues/plan_discipline_deferred_banner_false_trip_june_vintage_2026_07_27.md,
    /plans/archive/issues/plan_discipline_quoted_deferred_false_positive_2026_07_26.md,
    /plans/archive/issues/plan_discipline_archive_no_successor_regression_2026_07_25.md,
  ]
created: 2026-07-28
source: [data_engineering slot-12, 2026-07-28, discovered while shipping sports_track_h_denominator_prereqs-001]
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-28
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# plan-discipline false positive — `RESOLVED-BY-RULING, DEFERRED —` bare-marker form not covered by the existing exemption

## What I found

`check_plan_discipline.py` directly:

```
Scanned plans/active/ (264 plans) + issues + archive — 1 violation(s).
Per-rule: {'A-deferred-no-banner': 1}
  - [A-deferred-no-banner] unified-trading-pm/plans/active/qg_host_adaptive_resource_governor_2026_07_14.md: contains
    DEFERRED but no '## Deferred work — migrated to:' banner
```

Verified NOT caused by my staged change: `git diff --stat` on the flagged file is empty, `git log` shows its last touch
predates my session. The flagged line (228): `"**RESOLVED-BY-RULING, DEFERRED — cleaned 2026-07-28 (stale-tag audit;
this was never a live `[OPERATOR]` gate, just an inline label describing an already-made decision.)**"` — semantically a
CLOSED ruling (explicitly says "cleaned," "never a live gate"), the same category the checker's own comments already
carve out for `DEFERRED-BY-DESIGN` (no successor to migrate to, so demanding a migration banner is a category error).
The regex `_DEFERRED_RE` matches the BARE `DEFERRED\s+[—-]` form here (this line uses an em-dash after `DEFERRED`, not
the `DEFERRED-<QUALIFIER>` no-space form the `RESOLVED-BY-RULING`/`DEFERRED-BY-DESIGN` exemption pattern-matches on),
so it falls outside the existing exemption.

## Why it matters

Ratchet gate (baseline=0) — blocks EVERY subsequent unified-trading-pm quickmerge commit from ANY slot until resolved,
not just mine. Declaring per RULES.md § 4b (repo-blocker, backend-owned wait) rather than hand-editing a doc I don't
own (actively-worked infra plan, mid-session per its own recent commits) or waiting silently.

## Recommended decision

Same fix shape as the prior two resolutions: either (a) extend the checker's existing `DEFERRED-BY-DESIGN` exemption
to also recognize `RESOLVED-BY-RULING, DEFERRED —` as a closed-ruling marker (no successor to migrate to), or (b) the
doc owner rephrases line 228 to use the `DEFERRED-BY-DESIGN`/`RESOLVED-BY-RULING-` qualifier form the exemption already
covers. Not doing either myself — not my doc, and the checker-level fix is the more durable one per both prior
instances of this exact false-positive class.

## Todos

- [ ] [PM] P2. Extend `check_plan_discipline.py`'s closed-ruling exemption to cover the bare `RESOLVED-BY-RULING,
      DEFERRED — <past-tense-cleanup verb>` phrasing (or fix `qg_host_adaptive_resource_governor_2026_07_14.md:228` to
      use the already-exempted qualifier form) — either unblocks unified-trading-pm quickmerge for everyone.
      (repo: unified-trading-pm)
