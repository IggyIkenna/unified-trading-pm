---
doc_type: issue
title: >-
  context-scout Progress Log markers claim more context_scope entries than the live frontmatter actually contains — 4
  confirmed instances in one 13-doc daily-incremental sample
summary: >-
  Today's daily-incremental `/context-scout` pass (13 STALE-verdict docs, 0 NEVER_SCOUTED, 631 UP_TO_DATE) found that 4
  of the 13 docs (31%) carry a PRIOR context-scout Progress Log marker whose prose claims N entries were
  populated/refreshed, while the doc's actual `context_scope` frontmatter at read-time contained FEWER than N — content
  was silently lost between the marker being written and today, with nothing flagging the discrepancy (Phase 0's STALE
  check only compares the marker's DATE to the doc's last-touched date; it never cross-checks the marker's claimed COUNT
  against the live list length). Confirmed instances: `data_completion_defi_2026_07_15.md` (marker 2026-08-01 claims 5,
  frontmatter had 3 — M-1 parent doc + a heavily-cited migration script both missing; NOT fixed this run, doc is at the
  literal 1000L cap with zero safe edit path), `perp_funding_data_semantics_and_cadence_2026_06_16.md` (marker
  2026-08-03 claims 4, frontmatter had 3 — the `carry-venue-live-integration-reference.md` codex SSOT missing; fixed),
  `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` (marker 2026-08-03 claims 6, frontmatter had 3 —
  the grandparent issue doc and successor `continued3` both missing; fixed), and
  `sports_consolidated_closeout_2026_07_19.md` (marker 2026-08-03 claims 5, frontmatter had 3 — the native-extract child
  plan and the Track C root-cause source file both missing; fixed). This is DISTINCT from the already-known "cohort-5
  marker-skip" bug (`lst_rate_honest_coverage_2026_07_21.md`, fixed same-day by commit `021d0dabf` — that bug was a
  trimmed list with NO marker written at all, i.e. a false-negative on STALE detection). This bug is the inverse shape:
  a marker WAS written, and its claimed count is simply wrong relative to what actually landed — a false sense that the
  doc is fully scouted when a real content regression sits underneath it.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, context-scout, context_scope, data-integrity, regression, mvi]
related:
  [
    /cursor-configs/skills/context-scout/SKILL.md,
    /scripts/plan-hygiene/generate_context_scope_inventory.py,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-08-06
author: context_scout_auditor (dispatch agt-23f116, slot 4)
last_updated: 2026-08-06
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found incidentally while running the scheduled `/context-scout` daily-incremental dispatch (2026-08-06,
  agent-orchestrator slot 4, dispatch agt-23f116). Each of the 4 read-only Phase-1 scouting sub-agents independently
  re-derived a proposed context_scope list from the doc's own body citations, then compared it against the existing
  frontmatter AND the doc's own most recent context-scout Progress Log entry — 4 of the 13 assigned docs surfaced this
  same mismatch shape unprompted, without being told to look for it. Filed as its own issue per CLAUDE.md
  findings-triage ("outside every plan" + cross-cutting tooling/data-integrity class) rather than folded into any one
  doc's own Progress Log, since it's a property of the context-scout mechanism itself, not any single doc's content.
depends_on: []
context_scope:
  [
    /cursor-configs/skills/context-scout/SKILL.md,
    /scripts/plan-hygiene/generate_context_scope_inventory.py,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
  ]
---

# context-scout markers claim more entries than the live frontmatter contains

## What I found

Running the skill's Phase 0 inventory (`generate_context_scope_inventory.py --json`) against the full ~644-doc in-scope
corpus returned 13 STALE-verdict docs (0 NEVER_SCOUTED, 631 UP_TO_DATE) — the expected daily-incremental steady state.
Four read-only Phase-1 scouting sub-agents were dispatched (one per doc-batch) to re-derive each doc's correct
`context_scope`. Independently, without being asked to check for this specifically, each sub-agent that hit one of these
4 docs flagged the same anomaly: the doc's own most recent context-scout Progress Log entry states a specific entry
count and often names what was added, but the live frontmatter — read fresh, same session — has fewer entries than
claimed, and is missing exactly the item(s) the marker says were added.

### The 4 confirmed instances

| Doc                                                                  | Marker date | Marker claims | Frontmatter had | Missing                                                                                                                                                                        |
| -------------------------------------------------------------------- | ----------- | ------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `data_completion_defi_2026_07_15.md`                                 | 2026-08-01  | 5 entries     | 3               | `data_completion_to_100_all_ag_2026_06_21.md` (M-1 parent, doc's own header says "Read M-1 first"); `migrate_defi_full_v9_canonical.py` (cited by 8 open todos as "same walk") |
| `perp_funding_data_semantics_and_cadence_2026_06_16.md`              | 2026-08-03  | 4 entries     | 3               | `/codex/02-data/carry-venue-live-integration-reference.md`                                                                                                                     |
| `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` | 2026-08-03  | 6 entries     | 3               | `pytest_timeout_60s_flaky_under_contention_2026_07_29.md` (grandparent, doc's own opening paragraph names it explicitly)                                                       |
| `sports_consolidated_closeout_2026_07_19.md`                         | 2026-08-03  | 5 entries     | 3               | `sports_consolidated_native_ao_extract_2026_07_25.md` (child plan); `canonical_writer_shaping.py` (Track C root-cause file, cited 6x with line numbers)                        |

All 4 markers date to **2026-08-01 or 2026-08-03** — clustered, not spread evenly across the corpus's scouting history,
which is itself a clue toward a specific batch/commit being the origin rather than random ongoing drift.
`data_completion_defi_2026_07_15.md` was NOT fixed this run (see "Why one is still open" below); the other 3 were
restored to their correct entry count as part of this session's Phase 2 apply (commit `f3dea2d55` /
`94ca81908c7ad771d3f7b5b1ebc0dfb769a76236` on `live-defi-rollout`).

### Why this is distinct from the known cohort-5 bug

`lst_rate_honest_coverage_2026_07_21.md` had a related-but-different bug, already found and fixed same-day (commit
`021d0dabf`, 2026-08-06 02:00 UTC, message: "context-scout — fix cohort-5 marker-skip on lst_rate_honest_coverage
(context_scope trimmed without marker)"): a prior cohort trimmed the list but wrote NO marker at all, so Phase 0
correctly caught it as STALE (no dated marker at/after last-touched) and a later pass fixed it properly. **This issue's
bug is the inverse**: the marker WAS written, with a specific claimed count, but the actual list is shorter. Phase 0's
STALE check only inspects the marker's DATE against the doc's last-touched date — it has no mechanism to notice that the
marker's claimed COUNT disagrees with the ACTUAL current list length. A doc in this state can sit `UP_TO_DATE` (marker
date is fresh) while quietly missing real content, for as long as nothing else touches the doc.

### Why one is still open (`data_completion_defi_2026_07_15.md`)

This doc is at exactly 1000 lines (the corpus hard cap) and its existing marker is the LITERAL LAST LINE of the file —
there is no other content after it to anchor an in-place edit against, and any net-positive line delta (the minimum
being the 2 new context_scope entries, `+2` lines, before even considering the marker) fails `check_line_caps.sh`'s
SCOPED-mode small-marker-append exception, which only forgives a doc that was ALREADY over cap (`>1000`) before the
commit — this doc is AT 1000, not over, so the exception's own arithmetic (`PRE_COMMIT_LINES = lines - ADDED`, requiring
`PRE_COMMIT_LINES > 1000`) never qualifies. The doc needs a human trim pass first (it's `nature: process`, split
2026-07-15 out of a 5000+-line parent doc for exactly this reason, and has likely regrown compressible content since)
before its `context_scope` regression can be safely restored.

## Why this matters

The entire point of `context_scope` is that a future worker can trust a short, curated reading list instead of
re-deriving it via a fresh cold grep (that's the skill's whole MVI premise). A marker that says "populated 5 entries"
next to a frontmatter that only has 3 is worse than an honest STALE flag — it reads as verified-current to both a human
skimming the Progress Log AND to Phase 0's own freshness check, while silently omitting exactly the citations a worker
most needs (in 3 of the 4 cases: the parent/grandparent doc the doc's own prose says to read first). Given 4 of 13 docs
in one small daily sample show this shape, it is plausibly NOT rare in the wider ~644-doc corpus — most docs currently
read `UP_TO_DATE` and would not surface this without someone specifically re-deriving and diffing against the live
frontmatter, exactly as today's Phase 1 sub-agents did incidentally.

## Todos

- [x] ✅ [DOC] P1. **Root-cause the 4 confirmed instances**: `git log -p` / `git blame` across
      `data_completion_defi_2026_07_15.md`, `perp_funding_data_semantics_and_cadence_2026_06_16.md`,
      `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md`, and
      `sports_consolidated_closeout_2026_07_19.md` around their respective marker-write commits (2026-08-01 /
      2026-08-03) to find the exact commit(s) where the marker text and the frontmatter list diverged — was it a single
      batch/cohort commit that wrote the marker but only partially applied the list edit, or a LATER unrelated commit
      that trimmed/reformatted context_scope without touching the marker? **Done when**: a root-cause hypothesis is
      stated with the specific commit SHA(s) cited as evidence, or a documented "inconclusive, evidence trail does not
      survive in history" verdict. — unified-trading-pm@see-progress-log-2026-08-06
- [ ] [SCRIPT] P2. **Corpus-wide sweep for the same shape beyond today's 13-doc sample**: for every doc among the full
      ~644 in-scope population (not just today's STALE set), parse its most recent context-scout Progress Log marker's
      claimed entry count (regex on `\((\d+) entries?\)`) and compare against the live `context_scope` list length;
      report every doc where they disagree, regardless of whether Phase 0 currently calls it STALE or UP_TO_DATE. **Done
      when**: a report of every mismatched doc in the full corpus exists (this may surface instances beyond the 4 found
      here, since a doc can carry this bug while still reading UP_TO_DATE).
- [ ] [DOC] P2. **Close the detection gap** (gated on todo 1's root-cause finding): decide whether
      `scripts/plan-hygiene/generate_context_scope_inventory.py`'s Phase 0 STALE/UP_TO_DATE verdict logic should be
      extended to also flag a marker-count-vs-actual-count mismatch as its own verdict (e.g. `COUNT_MISMATCH`), so this
      class self-heals via the normal daily incremental pass instead of requiring an ad-hoc audit like this one to
      notice it. **Done when**: either the script gains this check (with a test fixture reproducing one of the 4
      confirmed instances), or a documented decision that it's not worth adding (e.g. if todo 1 finds this was a
      one-time batch bug already fully remediated, not an ongoing risk).

## Progress Log

- **2026-08-06 (context-scout, dispatch agt-23f116, slot 4)**: filed immediately upon the 4th independent instance
  turning up in a single 13-doc sample (pattern recognized after instance 2). 3 of the 4 affected docs fixed in the same
  run's Phase 2 apply (see `related:` for the exact restored entries); `data_completion_defi_2026_07_15.md` left open
  pending a human line-cap trim, since no safe edit path existed within this run's mandate (context_scope + marker only,
  never body content).
- **na-eligibility-audit 2026-08-06**: RECLASSIFY, conflict-cleared — all 3 todos bounded/deterministic (each with an
  explicit done-when, todo 3 pre-specifying both acceptable resolutions); flipped `assigned_vm: NA -> planning`,
  `execution_scope: local-only -> orchestrator-agent`. Conflict-check clear: the 3 active `assigned_vm: planning` docs
  in `parent_epic: plan_hygiene_master` use `context_scope` normally (not an instance of this bug) or fix a disjoint
  code path (`na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md`'s CHECKBOX_RE bug —
  confirmed `generate_context_scope_inventory.py` has no checkbox-counting logic at all); no sibling candidate or
  cross_cutting_consolidated_closeout overlap either. `assigned_role: data_engineering` (already correctly set at
  filing) left unchanged.
- **2026-08-06 (infra, slot 4, task context_scope_marker_claims_exceed_frontmatter_count-001)**: **Root-cause
  confirmed** — all 4 instances follow the same shape: a **subsequent context-scout batch/cohort commit edited the
  existing `context_scope` frontmatter list (removing entries judged redundant or stale by that later pass) WITHOUT
  updating the Progress Log marker from the prior scout run.** The prior marker's claimed count was accurate when it was
  written; the mismatch was introduced entirely by the later entry-drop commit that left the marker stale.

  Per-instance evidence:

  | Doc                                                                  | Marker-write commit (correct at time of writing)                                                                                          | Entry-drop commit (created the mismatch)                                                                                                                                                                                                                                         |
  | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `data_completion_defi_2026_07_15.md`                                 | `9bf4fd50a` (2026-08-01, "context_scope backfill residual, 90 docs") — wrote 5-entry list + "5 entries" marker                            | `98651a2b7` (2026-08-05, "context-scout cohort 1/5 batch b — refresh context_scope (19 docs)") — removed `data_completion_to_100_all_ag_2026_06_21.md` + `migrate_defi_full_v9_canonical.py`, leaving 3; no marker update (file was at 1000L cap)                                |
  | `perp_funding_data_semantics_and_cadence_2026_06_16.md`              | `3fac05949` (2026-08-03, "context-scout rescout batch 4/6") — wrote 4-entry list + "4 entries" marker                                     | `f968e4937` (2026-08-06, "context-scout batch — refresh context_scope (16 docs)") — removed `carry-venue-live-integration-reference.md`, leaving 3; no marker update                                                                                                             |
  | `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` | `4bf5416cb` (2026-08-03, "context-scout pass over residual STALE doc (batch 2/2)") — wrote 6-entry list + "6 entries" marker              | `76acd63be` (2026-08-06, "context-scout batch — refresh context_scope (15 docs)") — removed `pytest_timeout_60s_flaky_under_contention_2026_07_29.md` + `deployment-service/scripts/quality-gates.sh` + `features-service/scripts/quality-gates.sh`, leaving 3; no marker update |
  | `sports_consolidated_closeout_2026_07_19.md`                         | `d5c1eb454` (2026-08-03, "context-scout full corpus re-scout, updated methodology (batch 6/7)") — wrote 5-entry list + "5 entries" marker | `a74dea524` (2026-08-06, "context-scout cohort 5/5 batch 6/6") — removed `sports_consolidated_native_ao_extract_2026_07_25.md` + `canonical_writer_shaping.py`, leaving 3; no marker update                                                                                      |

  **This is NOT a one-time batch anomaly** — four distinct entry-drop commits on two separate dates (2026-08-05 and
  2026-08-06) each independently reproduced the same omission: edit the frontmatter list, skip the marker update. This
  confirms the pattern is **systemic** (any context-scout pass that removes or replaces entries in an existing
  `context_scope` list omits the marker update step), not a single bad commit. Todo 3 (detection-gap fix) is unblocked
  by this finding: the root cause is ongoing, not a one-time event already fully remediated.
