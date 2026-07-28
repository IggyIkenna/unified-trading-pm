---
doc_type: issue
title: >-
  plan-discipline ratchet (A-deferred-no-banner) regressed 0→1 on june_2026_vintage_audit_findings_2026_07_27.md —
  blocks unrelated commits to unified-trading-pm
summary: >-
  `scripts/quality_gates/check_plan_discipline.py` (rule A-deferred-no-banner) started failing quickmerge for ANY
  unified-trading-pm commit — verified on a clean stashed tree (no diff of mine) that the violation is pre-existing,
  landed via slot-4's `4051fe697` ("docs(plans): capture interactive operator-gate session results (42/42
  dispositioned)"). The flagged doc (`plans/active/june_2026_vintage_audit_findings_2026_07_27.md`) mentions
  "DEFERRED-BY-DESIGN" three times, all reporting on ANOTHER doc's status, never declaring this doc's own scope deferred
  — the checker's own quote-exclusion logic (`_has_live_deferred_marker` / `_QUOTE_CHARS`, added 2026-07-26 for the
  identical false-positive class) already correctly skips 2 of the 3 (lines 216/282, both `"DEFERRED-BY-DESIGN"` in
  straight double-quotes). The 3rd, line 378, is the SAME kind of third-party-reporting prose (a numbered-list item
  citing an external item's disposition by name) but written without quote marks around the token — so the
  quote-adjacency heuristic doesn't catch it. This is a narrower gap in the existing exclusion, not a totally
  unfingerprinted check. Did not fix in place: (a) I don't own this doc (actively edited by slot-4 minutes before I hit
  this), (b) whether line 378 should be quoted (making it exempt) or genuinely needs a banner (if this doc DOES carry
  real unmigrated scope for that item) is the doc owner's call, not mine to guess.
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-discipline, quality-gates, ratchet, false-positive, repo-blocker]
related: [plans/active/june_2026_vintage_audit_findings_2026_07_27.md, scripts/quality_gates/check_plan_discipline.py]
created: 2026-07-27
parent_epic: plan_hygiene_master
source: [data_engineering slot-2, 2026-07-27, discovered while shipping mvp_backfill_defi_onchain_v10-003]
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-27
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  slot-1, `ddf138deb` ("fix(ci): ldr-ci-monitor... plan-discipline DEFERRED-BY-DESIGN false-positive fix") — a more
  principled fix than either option I proposed: exempts the whole `DEFERRED-BY-DESIGN` qualifier (a closed, permanent
  ruling with no successor to migrate to) from the live-marker check entirely, quoted or not, rather than requiring a
  quote around every instance. Verified: `check_plan_discipline.py` now reports 0 violations after fast-forwarding to
  that commit; reverted my own now-redundant quote-edit to `june_2026_vintage_audit_findings_2026_07_27.md` before it
  landed. Repo-blocker `RB-63a8ee3c` closed.
---

> **🟢 RESOLVED 2026-07-27** — fixed at the checker level by slot-1 (`ddf138deb`), more generally than either option
> this doc proposed. See `resolved_by` above.

## What I found

`bash scripts/quickmerge.sh` for an unrelated docs-only commit
(`plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`) failed its post-gate re-run on `plan-discipline` (exit
non-zero, "Regression: 1 > baseline 0"). Ran `check_plan_discipline.py` directly:

```
Scanned plans/active/ (271 plans) + issues + archive — 1 violation(s).
Per-rule: {'A-deferred-no-banner': 1}
  - [A-deferred-no-banner] unified-trading-pm/plans/active/june_2026_vintage_audit_findings_2026_07_27.md:
    contains DEFERRED but no '## Deferred work — migrated to:' banner
```

Verified this is NOT caused by my own staged change: `git stash push --include-untracked`, re-ran the same check on a
clean tree, same single violation reported. `git log` on the flagged file shows its last touch is `4051fe697`
("docs(plans): capture interactive operator-gate session results (42/42 dispositioned)", slot-4, 2026-07-27 23:41 — ~20
minutes before I hit this).

Read the flagged doc's own regex + exclusion logic (`scripts/quality_gates/check_plan_discipline.py:38-66`) —
`_DEFERRED_RE` matches `DEFERRED-[A-Z][A-Z0-9-]*` (catches `"DEFERRED-BY-DESIGN"`), and `_has_live_deferred_marker`
skips any match immediately preceded by a quote char (`"'"'"`). All 3 occurrences in the flagged doc:

- Line 216: `...is the operator's own "DEFERRED-BY-DESIGN" — see §5.` — QUOTED, correctly excluded.
- Line 282: `operator's own "DEFERRED-BY-DESIGN," no timeline given.` — QUOTED, correctly excluded.
- Line 378: a numbered-list item ("5. e2e_defi_config_taxonomy D1 — confirmed stays [that same qualifier], no
  timeline.") reporting the SAME external item's disposition by name, but with no quote marks around the token this time
  — this is the ONE match `_has_live_deferred_marker` treats as live, tripping the rule.

So the checker's own documented false-positive fix (2026-07-26, cited in its own comments) already covers the quoted
form; line 378 is the identical semantic case (reporting another item's status, not this doc's own scope) just phrased
without quotes, so it falls through the existing heuristic.

## Why it matters

This is a ratchet gate (baseline=0), so it blocks EVERY subsequent unified-trading-pm quickmerge commit from ANY slot
until resolved — not just mine. Declaring per RULES.md § 4b (repo-blocker, backend-owned wait) rather than working
around it or waiting silently.

## Recommended decision

- [x] ✅ [PM] P2. **DONE 2026-07-27 — resolved by slot-1, `ddf138deb`**, superseding my proposed quote-fix (which I
      reverted before it landed, now redundant). Repo: unified-trading-pm.
