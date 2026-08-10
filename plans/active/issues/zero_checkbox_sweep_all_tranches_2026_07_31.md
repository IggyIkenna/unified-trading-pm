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
author: unknown
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
context_scope:
  [
    /codex/11-project-management/issue-doc-lifecycle.md,
    /plans/active/task_template.md,
    /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md,
    cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
---

# Zero-checkbox sweep — all 9 tranches

## Standing owner + cadence (this is the part the predecessor lacked)

| Field             | Value                                                                                                                                                                                                                                                                                                                                             |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Owner**         | `/plan-reconcile` (the `plan-reconciler.timer` scheduled job) — it already owns the corpus-wide contradiction / false-unchecked sweep, and this is the same class of defect.                                                                                                                                                                      |
| **Cadence**       | Monthly, folded into the first `/plan-reconcile` full-corpus run of each month (it already walks every active doc, so the marginal cost is one extra predicate).                                                                                                                                                                                  |
| **Verifier**      | `grep -LE '^[[:space:]]*- \[[ xX]\]' plans/active/*.md plans/active/issues/**/*.md` — the count of non-exempt hits must be 0, or every hit must be classified in this doc.                                                                                                                                                                        |
| **Last executed** | 2026-08-02 (`/plan-reconcile` whole-corpus run — see § "Re-run 2026-08-02"). Prior: 2026-07-31 (authoring run). **The monthly full-corpus pass for 2026-08 is still OUTSTANDING** — the 2026-08-06 `/plan-reconcile ao` run measured the verifier corpus-wide but only had authority to convert its own tranche (see § "Measurement 2026-08-06"). |

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
2. `plans/archive/issues/deployment_api_artifact_pipeline_health_test_date_drift_flake_2026_07_29.md` — "Fix direction
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

## Measurement 2026-08-06 — `/plan-reconcile ao` (TOPIC-SCOPED run — NOT the monthly full pass)

Verifier re-run exactly as specified in the table: **12 hits, up from 8 on 2026-08-02.** The population is GROWING, so
this register is doing its job of making that visible.

| Doc                                                                                                                                                                                                                                               | Class                              | Disposition                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------- |
| `_agent_pings.md` · `INDEX.md` · `task_template.md`                                                                                                                                                                                               | structurally exempt (3, unchanged) | no action — correct as-is                                                                   |
| `ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md`                                                                                                                                                                                           | **`ao` tranche — genuine work**    | CONVERTED this run: its 3 "Open questions for whoever picks this up" became canonical todos |
| `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` · `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md`                                                                                                      | defi                               | **NEW since 2026-08-02** — not this run's tranche, unclassified                             |
| `client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md`                                                                                                                                                                                 | cross-cutting/ci                   | **NEW** — unclassified                                                                      |
| `instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md`                                                                                                                                                                          | sports/instruments                 | **NEW** — unclassified                                                                      |
| `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md` · `/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` · `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` | mtds/cefi                          | **NEW** — unclassified                                                                      |
| `sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md`                                                                                                                                                            | sports                             | **NEW** — unclassified                                                                      |

**8 non-exempt hits remain unclassified**, all outside the `ao` tranche. A topic-scoped run has no authority to convert
another tranche's docs, so they are recorded here rather than silently skipped — the 2026-08 monthly full-corpus pass
must pick them up. Note the shape of the growth: 6 of the 8 are `mtds`/`defi`/`sports` incident write-ups filed in the
last 4 days, i.e. the class regenerates fastest in fresh incident docs, exactly where prose-only "open questions" get
written under time pressure.

## Re-run 2026-08-02 — `/plan-reconcile` whole-corpus (unscoped) run

Verifier re-run exactly as specified in the table above, over `plans/active/*.md` + `plans/active/issues/**/*.md`. **8
hits** (down from 11 on 2026-07-31 — the 5 converted docs correctly no longer hit). Of the 8: **6 are the same 6 this
doc already classified** (3 structurally exempt + 3 deliberate/informational — all re-confirmed unchanged, including the
`sports_fixture_events_refetch_progress_2026_07_25.md` TRAP, which still correctly has no checkbox). **2 are NEW since
2026-07-31**:

| New doc                                                                                               | Verdict                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`         | **CONVERTED.** Real remaining work, all prose: an unruled A-vs-B operator decision (finding 2) plus two open crash findings (3 and 4) whose own text enumerates "Not yet done" next steps. 6 canonical todos added in place. `execution_scope: local-only`, so these do NOT enter the AO backlog — no duplicate-dispatch risk.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `plans/active/issues/cefi_content_migration_fleet_half_incomplete_progress_log_archive_2026_07_31.md` | **RECORDED, not changed** (4th member of the deliberate/informational class), as of this sweep's 2026-07-31 date. It is a pure verbatim relocation of a live parent doc's early Progress Log, extracted only to keep `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` under its 1000-line hard cap. It holds zero work by construction; a todo here would be fabricated. Its parent is live, so at the time of this sweep it was NOT archived either. **Update 2026-08-04 (na-eligibility-audit, cefi tranche): now archived** to `/plans/archive/issues/cefi_content_migration_fleet_half_incomplete_progress_log_archive_2026_07_31.md`, independent of its still-open parent — a companion appendix does not need its parent done first (see `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). |

**Scope note for the next run** — `plans/epics/*.md` is in `/plan-reconcile`'s stated audit scope but is NOT in this
register's population definition (which is `plans/active/*.md` + `plans/active/issues/**/*.md` only). Re-derived here
for completeness: **7 of 28 epics carry zero checkboxes** (`batch_live_symmetry_master`, `dart_and_promote_master`,
`deployment_and_user_management_master`, `global_ledger_pnl_attribution_master`, `orchestrator_master`,
`strategy_master`, `trading_agent_master`). These are **NOT defects** — an epic hub is an index over child plans that
carry the todos, and the other 21 epics only have checkboxes incidentally. Recorded so a future run does not re-discover
them as a finding; the population definition is deliberately left unchanged.

## Todos

- [x] ✅ [DOC] P2. **DONE (na-eligibility-audit 2026-08-04)** — Wire the verifier into `/plan-reconcile`'s monthly
      full-corpus pass. Both done-when clauses now hold: the predicate already ran in the skill's standard pass as of
      the 2026-08-02 note below, and the second clause (naming) landed hours later the same day —
      `unified-trading-pm@d872efb3a` added the "Standing register" line at
      `cursor-configs/skills/plan-reconcile/SKILL.md:371`, citing this doc by name. Verified live:
      `grep -rn     "zero_checkbox_sweep_all_tranches" cursor-configs/skills/` returns a hit. (repo:
      `unified-trading-pm`)
- [ ] [DOC] P3. **Re-run the sweep and update the "Last executed" row** at the next monthly pass; if the non-exempt
      unclassified count is 0, record that and leave this doc open as the standing register (it is deliberately NOT
      archive-on-complete — archiving is what orphaned this class twice already). (repo: `unified-trading-pm`)

## Progress Log

- **na-eligibility-audit 2026-08-02**: KEEP-NA, valid -- a STANDING register, deliberately not archive-on-complete
  (archiving is what orphaned this class twice already), whose declared owner is the `/plan-reconcile` scheduled job,
  not AO dispatch. Todo 2 is a recurring monthly-cadence item; flipping `assigned_vm` would have backlog-regen derive a
  perpetual re-dispatch of exactly the duplicate-dispatch trap this doc's own § "Genuinely informational" entry 3 warns
  about. Todo 1's residual (one-line SKILL.md edit naming this register) is bounded but duplicated by
  `plan_reconcile_parked_operator_decisions_2026_08_02.md`'s `[DOC] P2` -- reported as a cross-doc duplicate claim, not
  resolved here.

- **2026-08-02 (`/plan-reconcile` whole-corpus autonomous run)** — re-ran the verifier: 8 hits, 6 already-classified + 2
  new (1 converted, 1 recorded — see § "Re-run 2026-08-02"). **Todo 1 checked and deliberately NOT flipped**: its
  done-when has two clauses and only one holds. The predicate DOES now run in the skill's standard pass —
  `cursor-configs/skills/plan-reconcile/SKILL.md:301` carries a "### 4. ZERO-CHECKBOX docs — this skill's standing
  responsibility, all 10 tranches (added 2026-07-30)" section stating "**This skill OWNS the zero-checkbox sweep**... it
  runs as part of this skill's own periodic run, every run." But the other clause, "the skill file names THIS doc as the
  register", is **false**: `grep -rn "zero_checkbox_sweep_all_tranches" cursor-configs/skills/` returns ZERO hits
  (verified at `unified-trading-pm@ff619d4`). The only pointer to this register reached the 2026-08-02 run through the
  operator's invocation text, not the committed skill — which is precisely the "class loses its owner" failure this doc
  exists to prevent, recurring one level up. Leaving the todo OPEN with the residual now narrowed to a one-line SKILL.md
  edit. Note the skill section also says "all 10 tranches" while this doc's title/body say 9 — cosmetic, the enumerated
  list in SKILL.md is the correct one (`ui` was added 2026-07-30).
- **2026-07-31 (corpus-sweep, operator-ruled item 5)** — authored. Swept 641 active docs (244 plans + 397 issues). 11
  zero-checkbox hits: 3 structurally exempt, 5 converted to tracked todos, 3 recorded as deliberate/informational.
  Predecessor `issue_docs_zero_checkbox_sweep_2026_07_24.md` confirmed ARCHIVED (`plans/archive/issues/`), and its
  narrow population definition confirmed as the reason the 5 non-AG tranches were never swept. Standing owner/cadence
  table added above so the class no longer dies with its sweep doc.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — todo 1 closed above (both done-when clauses now verified live;
  the naming half landed `unified-trading-pm@d872efb3a`, hours after the 2026-08-02 note below was written). Doc stays
  open and NA: it is a deliberately-permanent standing register (own todo 2 / P3: "NOT archive-on-complete — archiving
  is what orphaned this class twice already"), owned by the `/plan-reconcile` scheduled job, not AO dispatch.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-08-04; the sole remaining open todo (P3, re-run
  the sweep at the next monthly `/plan-reconcile` pass) is this doc's own deliberately-permanent standing-register
  cadence item, owned by that scheduled skill, not AO dispatch (archiving/dispatching it is exactly what orphaned this
  class twice before, per this doc's own history).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
