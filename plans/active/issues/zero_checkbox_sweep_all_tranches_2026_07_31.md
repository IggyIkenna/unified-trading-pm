---
doc_type: issue
title:
  Zero-checkbox sweep — ALL 9 tranches, whole active corpus (successor to the archived 5-AG-only
  issue_docs_zero_checkbox_sweep_2026_07_24)
summary: >-
  Re-run of the corpus-wide "docs whose remaining work exists only as prose, never as a tracked `- [ ]` checkbox" sweep,
  with the population widened from the archived predecessor's structurally-narrow definition (only issue docs REFERENCED
  BY the 5 asset-group consolidated closeouts, which excluded meta/infrastructure/cross-cutting/ao/ci entirely) to the
  WHOLE active corpus — every `plans/active/*.md` and `plans/active/issues/**/*.md`, all 9 tranches. Swept 641 active
  docs on 2026-07-31; 11 carry zero real `- [ ]`/`- [x]` todo lines, of which 3 are structurally exempt (INDEX,
  underscore-prefixed, the task template), 5 had real actionable prose converted into tracked todos, and 3 are genuinely
  informational/deliberate and are recorded as such — two of them DELIBERATELY checkbox-free to stop
  `regen_backlog_from_plan.py` deriving a duplicate AO dispatch, which is a trap any future re-run must not "fix". Names
  a standing owner + cadence so the class stops losing its owner every time a one-off sweep doc archives.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-quality, issue-docs, todo-format, hygiene-sweep, zero-checkbox, cross-cutting]
related:
  [
    /plans/archive/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md,
    /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/active/task_template.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
  ]
created: 2026-07-31
last_updated: 2026-07-31
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on: []
source:
  "Operator ruling 2026-07-31 (corpus-sweep item 5): the predecessor sweep doc was archived before it could be re-run at
  full width, and its population definition structurally excluded 5 of the 9 tranches. Standing follow-up was recorded
  in /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md's Progress Log, which explicitly noted the class
  'currently has no owning active doc'."
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Zero-checkbox sweep — all 9 tranches

## Standing owner + cadence (this is the part the predecessor lacked)

| Field             | Value                                                                                                                                                                        |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Owner**         | `/plan-reconcile` (the `plan-reconciler.timer` scheduled job) — it already owns the corpus-wide contradiction / false-unchecked sweep, and this is the same class of defect. |
| **Cadence**       | Monthly, folded into the first `/plan-reconcile` full-corpus run of each month (it already walks every active doc, so the marginal cost is one extra predicate).             |
| **Verifier**      | `grep -LE '^[[:space:]]*- \[[ xX]\]' plans/active/*.md plans/active/issues/**/*.md` — the count of non-exempt hits must be 0, or every hit must be classified in this doc.   |
| **Last executed** | 2026-07-31 (this run)                                                                                                                                                        |

**Why it kept going stale**: the class has twice been "owned" by a one-off dated sweep doc that then archived on
completion, taking the ownership with it. A dated doc cannot own a recurring class. The owner above is a standing job,
and this doc is the register it writes to.

## Population definition (the thing the predecessor got wrong)

- **Predecessor (`issue_docs_zero_checkbox_sweep_2026_07_24.md`, archived)**: issue docs **referenced by** the 5
  asset-group consolidated closeouts → 110 filenames, 96 `status: open`. That excludes by construction every
  `meta`/`infrastructure`/`cross-cutting`/`ao`/`ci` doc, because those tranches are not referenced by the 5 AG
  closeouts. Its "zero further gaps found" conclusion was true **only inside that narrow population**.
- **This sweep**: every file matching `plans/active/*.md` + `plans/active/issues/**/*.md` — **641 docs**, all 9
  tranches, no reference-graph filter.
- **Detection**: zero lines matching `^[[:space:]]*- \[[ xX]\]`. Deliberately anchored to real todo-list syntax — an
  unanchored `\[[ xX]\]` match is too loose (it hits `[x]` inside prose and code fences) and under-reports by 8.

## Findings — 11 zero-checkbox docs

### Structurally exempt (3) — no action, correct as-is

| Doc                             | Why exempt                                                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `plans/active/INDEX.md`         | Corpus index, not a tracked doc (`docspec.is_exempt`).                                                 |
| `plans/active/_agent_pings.md`  | Underscore-prefixed; explicitly excluded by `_plan_contributes_briefs`.                                |
| `plans/active/task_template.md` | The authoring template itself — its `- [ ]` examples are intentionally illustrative, not tracked work. |

### Real actionable prose → converted to tracked todos (5)

1. `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md` — §5 "Follow-up todos" was **6 prose bullets**
   (including an explicit `[OPERATOR]` policy call). Its own Progress Log already flagged this as a HARD-RULE violation
   ("every follow-up is a `- [ ]` todo, never prose"). Converted in place.
2. `plans/active/issues/deployment_api_artifact_pipeline_health_test_date_drift_flake_2026_07_29.md` — "Fix direction
   (not yet done)" prose; its Progress Log had already self-nominated for this sweep. Converted.
3. `plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md` — a parking register whose P0-A (a **dated**
   2026-08-15 `check_codex_doc_freshness.py` hard-gate cliff), P1-C, P1-D and P2-E findings were all prose, so a
   repo-wide commit blocker with a known arrival date was invisible to every open-todo count. Converted.
4. `plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md` — "Recommended fix (not actioned
   here)" prose. Converted.
5. `plans/active/issues/sports_g1_noise_population_mismatch_and_scope_bug_2026_07_27.md` — numbered items 2-4 were plain
   prose; the doc's own item 5 said so. Converted to real checkboxes.

### Genuinely informational / deliberately checkbox-free (3) — recorded, NOT changed

1. `plans/active/issues/stash_audit_reports/stash-audit-ip-172-31-5-118-20260730.md` — `status: resolved`,
   `nature: record`. A dated host stash-audit table. Pure historical record; a todo here would be fabricated work.
2. `plans/active/issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` — `status: superseded`.
   Its own "## Todos" section states the bullets are **kept as plain bullets deliberately, so backlog regen does not
   double-dispatch this duplicate**; the real tracked todos live in the superseding doc.
3. `plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md` — **TRAP, read before touching.** Its
   checkbox has been removed **twice** (DEDUP NOTE 2026-07-25T06:44Z and DEDUP NOTE 2 2026-07-29) precisely because
   `regen_backlog_from_plan.py`'s `_UNCHECKED_RE` was deriving a SECOND live AO task tracking the SAME VM as the parent
   plan's own todo — measured at 9 redispatches in ~2h18m. **Adding a checkbox here re-introduces a known, twice-fixed
   duplicate-dispatch bug.** The parent plan's todo is the single dispatch point.

> **Standing instruction for the next run**: "zero checkboxes" is NOT automatically a defect. Three of the eleven hits
> above are correct as they are, and one of those three is actively load-bearing. Always read the doc before adding a
> todo to it.

## Todos

- [ ] [DOC] P2. **Wire the verifier into `/plan-reconcile`'s monthly full-corpus pass** — add the zero-checkbox
      predicate (the `grep -LE` one-liner in the table above) to the `plan-reconcile` skill's corpus walk, so a new
      zero-checkbox doc is reported against THIS register instead of needing a fresh one-off sweep doc. Done-when: the
      skill file names this doc as the register and the predicate runs in its standard pass. (repo:
      `unified-trading-pm`)
- [ ] [DOC] P3. **Re-run the sweep and update the "Last executed" row** at the next monthly pass; if the non-exempt
      unclassified count is 0, record that and leave this doc open as the standing register (it is deliberately NOT
      archive-on-complete — archiving is what orphaned this class twice already). (repo: `unified-trading-pm`)

## Progress Log

- **2026-07-31 (corpus-sweep, operator-ruled item 5)** — authored. Swept 641 active docs (244 plans + 397 issues). 11
  zero-checkbox hits: 3 structurally exempt, 5 converted to tracked todos, 3 recorded as deliberate/informational.
  Predecessor `issue_docs_zero_checkbox_sweep_2026_07_24.md` confirmed ARCHIVED (`plans/archive/issues/`), and its
  narrow population definition confirmed as the reason the 5 non-AG tranches were never swept. Standing owner/cadence
  table added above so the class no longer dies with its sweep doc.
