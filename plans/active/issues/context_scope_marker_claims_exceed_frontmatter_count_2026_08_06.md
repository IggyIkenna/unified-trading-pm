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
    /plans/archive/2026_08/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
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
    scripts/plan-hygiene/generate_context_scope_marker_sweep.py,
    /plans/active/data_completion_defi_2026_07_15.md,
    scripts/plan-hygiene/check_line_caps.sh,
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
- [x] ✅ [SCRIPT] P2. **Corpus-wide sweep**: for every doc in the full ~644-doc in-scope population, parse its
      context-scout marker's claimed count (regex `\((\d+) entries?\)`) vs. the live `context_scope` list length and
      report every disagreement — beyond just today's 13-doc STALE sample. **Done when**: a report of every mismatched
      doc in the full corpus exists (this may surface instances beyond the 4 found here, since a doc can carry this bug
      while still reading UP_TO_DATE). — unified-trading-pm@a4bc3a0c8e
- [x] ✅ [DOC] P2. **Close the detection gap** (gated on todo 1's root-cause finding): decide whether
      `scripts/plan-hygiene/generate_context_scope_inventory.py`'s Phase 0 STALE/UP_TO_DATE verdict logic should be
      extended to also flag a marker-count-vs-actual-count mismatch as its own verdict (e.g. `COUNT_MISMATCH`), so this
      class self-heals via the normal daily incremental pass instead of requiring an ad-hoc audit like this one to
      notice it. **Done when**: either the script gains this check (with a test fixture reproducing one of the 4
      confirmed instances), or a documented decision that it's not worth adding (e.g. if todo 1 finds this was a
      one-time batch bug already fully remediated, not an ongoing risk). — unified-trading-pm@a4fbf7f61
- [ ] [OPERATOR] P1. **Human line-cap trim of `data_completion_defi_2026_07_15.md`** (sits at the 1000L hard cap — the
      one remaining mismatched doc from the sweep), then restore the 2 dropped context_scope entries
      (`data_completion_to_100_all_ag_2026_06_21.md` + `migrate_defi_full_v9_canonical.py`) and align the 2026-08-01
      marker's claimed count (repo: unified-trading-pm).

## Corpus-wide sweep results (2026-08-06)

Executed with the new standing tool `scripts/plan-hygiene/generate_context_scope_marker_sweep.py` (task -002, slot 6),
which loads `generate_context_scope_inventory.py` for identical corpus/marker/verdict definitions and applies this
issue's `\((\d+) entries?\)` spec. Population: 723 in-scope docs; 659 carry a `context-scout YYYY-MM-DD` marker; 606 of
those have a parenthetical count claim on the latest marker; 53 do not (prose-form or no count — hand-glanced, see
below).

| Doc                                                                 | Latest marker | Claims | Live | Shape / disposition                                                                                                                                                                                                               |
| ------------------------------------------------------------------- | ------------- | ------ | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data_completion_defi_2026_07_15.md`                                | 2026-08-01    | 5      | 3    | entry-drop w/o marker update — KNOWN-OPEN, at 1000L cap; human trim tracked as new [OPERATOR] todo                                                                                                                                |
| `data_status_page_ux_and_canonicalisation_2026_07_16.md`            | 2026-08-05    | 5      | 6    | write-time miscount ("unchanged (5 entries)" vs 08-03's 6) — FIXED (marker text → 6)                                                                                                                                              |
| `ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` | 2026-08-05    | 5      | 6    | write-time miscount at populate — FIXED (marker text → 6)                                                                                                                                                                         |
| `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`                 | 2026-08-03    | 6      | 8    | write-time miscount — batch 7/7 commit `14e2a0e1a` appended "re-verified (6 entries)" onto the already-8-entry list; PROSE-form claim (regex-invisible), caught via the no-claim bucket's manual glance — FIXED (marker text → 8) |

All 3 fixes are marker-text count corrections only — the live lists were authoritative (each set by a deliberate prior
pass, every entry resolving); zero frontmatter/body changes, zero line delta.

**Sub-shape note for todo 3**: the original 4 instances were entry-DROP without marker update; all 3 new instances are
markers WRITTEN with a wrong count (write-time miscount by a batch pass). Both shapes leave claim != live list, so a
COUNT_MISMATCH Phase-0 verdict catches both regardless of origin/direction.

**No-claim bucket (53 docs)**: latest markers lacking a parenthetical count. Hand-glanced one-by-one: every prose count
claim ("trimmed from 7 to 6", "now 4 entries", "(6 entries, corrected prior stale count)") matches the live list —
except the `tradfi_satellite_ao_dispatch_batch2` row above, which is exactly why the bucket stays in the tool's output
for a human glance instead of being dropped.

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

- **2026-08-06 (data_engineering, slot 6, task context_scope_marker_claims_exceed_frontmatter_count-002)**: corpus-wide
  sweep shipped (`scripts/plan-hygiene/generate_context_scope_marker_sweep.py`, unified-trading-pm@92bd7b601). 723
  in-scope docs → 4 mismatches total: 3 NEW, all write-time marker miscounts
  (`data_status_page_ux_and_canonicalisation_2026_07_16.md` 5v6,
  `ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` 5v6,
  `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` 6v8 — the last prose-form, regex-invisible, caught via the
  no-claim bucket's manual glance) + the known-open `data_completion_defi_2026_07_15.md` (5v3, 1000L cap). The 3 new
  ones fixed inline as marker-text count corrections (2af352ecf); the open one is now a tracked [OPERATOR] todo. The 53
  no-claim docs hand-verified consistent in prose. Re-run after fixes: 1 mismatch remaining (the known-open). Operator
  2026-08-06 OOM directive acknowledged — no OOM/unbounded-run incidents from this session; the sweep ran under
  `scripts/dev/run-bounded-analysis.sh`.

- **2026-08-06 (data_engineering, slot 6, task context_scope_marker_claims_exceed_frontmatter_count-002) — SHIP BLOCKED,
  upstream in-flight**: the 3 sweep commits (92bd7b601 + 2 docs commits, rebased) are ready, but full PM QG Pass 1 came
  back RED on the post-gate `workflow-template-parity` — 4 NEW drifted copies of `image-build-gate.yml` in
  `agent-orchestrator` / `features-service` / `instruments-service` / `market-tick-data-service` (detector
  `detect_template_drift.py --workflows`, verified byte-diffs). Root cause: NOT this session's commits (zero workflow
  files touched; `git diff origin/live-defi-rollout..HEAD -- .github/` empty) — it is the tracked in-flight extraction
  `plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md`: template re-pointed at `unified-trading-ci`
  (PM@a2feeb4de, 2026-08-06), per-repo migration is that plan's todo 14 (Wave 4, final 5) — unchecked, actively worked.
  Condition is STABLE (not flapping): PM QG is red fleet-wide on this post-gate until Wave 4 lands. NOT fixing myself:
  hand-editing the 4 copies is banned, and completing another session's tracked in-flight rollout would collide with it
  (todo 18 will re-edit the template too). Watch armed (`bidxjckrg`): polls all 4 repos' origin LDR for copies
  byte-matching the SSOT template (90s interval, 90-min cap). Resume when it fires: re-run PM QG → quickmerge Pass 2
  (`--agent --files` for the 5 changed paths) → verify SHA on origin → POST /done.

- **2026-08-06 (data_engineering, slot 6, task context_scope_marker_claims_exceed_frontmatter_count-002) — BLOCK
  CLEARED, ship sequence in flight**: watcher `bidxjckrg` fired "ROLLOUT LANDED" (all 4 `image-build-gate.yml` copies
  byte-match SSOT) → heartbeat (OK, resume) + `/blocked` filed as `BLK-bea57103` per the GIT-STATUS-RED nudge's own "If
  a commit blocks on QG, file /blocked with plan-ref" escape hatch (`can_continue: true`, continue_on = the watcher
  path; not a question — a record of the wait). First QG re-run (`b8xacwwck`) was SIGTERM'd by the `qg-host-governor`
  runtime abort-monitor: host RAM ≥80% for 2 consecutive 15s checks (slot-5's six `scratchpad_4bi` python jobs ≈8.4 GB
  in flight; governor is self-scoped by design — marker `.benchmarks/qg-governor/killed.3351709`). Standing OOM/abort
  directive acknowledged: event recorded here, host pressure now 23%. QG re-run #2 (`bozh63zne`) in flight. Note: QG
  changeset detection is WORKING-TREE-based (base-service.sh:760) — the foreign e2e autofix makes this run DOCS-ONLY
  (skips TESTS+TYPECHECK); no coverage lost for the sweep script (PM `scripts/` are ruff-gated; basedpyright fully
  excluded, quality-gates.sh:26-38, operator ruling 2026-07-27 finding 87).

- **2026-08-06 (data_engineering, slot 6, task context_scope_marker_claims_exceed_frontmatter_count-002) — SHIP BLOCKED
  #2 (post-drift), pre-existing FOREIGN gate violation**: quickmerge Pass 2 re-gate now fails a DIFFERENT post-gate,
  `finalize-plan-coverage` (workflow-template-parity is GREEN — the wave-4 landing held). Standalone
  `check_finalize_plan_coverage.py --workspace-root .tabs/6` AND the pre-drift archive test
  (`git archive c48bf1475~7 plans/active` → checker) BOTH fail with the same 1 violation:
  `plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md` — `assigned_vm: planning`, **0 open / 14 closed
  todos** (a COMPLETED plan; per plan-completion discipline its owner must archive it), no gating
  `depends_on`+`gate_on_depends: true` anywhere (cross-repo grep empty), `locked_by` empty. Ownership: slot-7
  (2026-08-05, `8e39617f9`/`d9d170be3`) + slot-6 context-scout batch touch (`421c69f8d`). NOT my commits (proven: zero
  touches in my diff; pre-drift tree fails identically). Anomaly noted: the 11:15 full-QG green run (`bozh63zne`) PASSED
  this gate on the same tree content — discrepancy not yet explained; the gate is deterministically RED now. NOT fixing
  myself: archiving a foreign slot-7-owned plan (or authoring its finalize plan) is the owner's job. Escalated via
  /blocked (BLK-…) with the owner remediation. Watch armed: poll the checker until exit 0 (→ "FINALIZE COVERAGE GREEN"),
  then re-run QG → quickmerge → /done.

- **2026-08-06 (data_engineering, slot 6, task context_scope_marker_claims_exceed_frontmatter_count-002) — BLOCK #2
  RESOLVED, ship in flight**: operator answered `BLK-fae14e09` with "proceed now" (my option set included "authorize
  slot 6 to archive the foreign done plan myself"). Archival attempted (`git mv` + `status: complete` flip) — the pull
  immediately exposed that the AO-tracker session had ALREADY half-archived the same plan: a `status: resolved` twin
  ADDED to `plans/archive/2026_08/` (with `resolved_by` + ARCHIVED banner) but the `status: active` original LEFT in
  `plans/active/` — a COPY, not a MOVE, which is why the fleet gate stayed red. Autostash-pop conflict resolved by
  taking their canonical version (my duplicate edit discarded; conflict markers cleared via
  `git restore --source=HEAD`). Committed the missing half: `dda85c8cc` deletes the stale active twin (proven necessary:
  checker exit 1 on clean HEAD, exit 0 with the deletion — the FPC checker scans the WORKTREE disk, not the branch).
  Finalize-plan-coverage now GREEN for the whole fleet. Full QG re-run (`b7ow1x4r3`) in flight; on green → quickmerge
  Pass 2 → verify SHA → POST /done. SHAs current as of this bullet: 8 commits ahead (`92bd7b601` sweep, `2af352ecf`
  marker fixes, `15a26a4ab` flip, `85b8ebfc9`/`9e6af71c3` block records, `c14332842` deferred table, `d7b002ba6` block
  #2 record, `dda85c8cc` archival completion).

## Deferred work after 2026-08-06

| Item                                                                                                     | State / why deferred                                                                                                                                                           | Blocked on                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Push 8 ship commits (sweep script + 3 marker fixes + flips + records + archival completion) + POST /done | IN FLIGHT — block #2 resolved (operator "proceed now"; AO-tracker half-archival completed via `dda85c8cc`); finalize-plan-coverage GREEN; full QG re-run (`b7ow1x4r3`) running | QG green → quickmerge Pass 2 `--agent --files '<6 paths>'` → verify SHA → POST `/api/slots/6/done` → flip harness task #4 → close BLK bookends → delete cron `ab0c84cd` |
| `data_completion_defi_2026_07_15.md` marker 5v3 (1000L line cap)                                         | Operator-owned — human line-cap trim                                                                                                                                           | [OPERATOR] P1 todo (above)                                                                                                                                              |
| Todo 3 — COUNT_MISMATCH detection gap in Phase-0 inventory                                               | Not done — owned by the issue's other assignee                                                                                                                                 | —                                                                                                                                                                       |
| `e2e_deepseek_poller_overwrites_hand_seeded_account_blob` doc `+depends_on: []`                          | Knowingly ignored — `fix_frontmatter.py` autofix artifact (quality-gates.sh:651) on a foreign doc; never staged by name                                                        | —                                                                                                                                                                       |

**Lessons (pre-compact Step 6)**: `bash scripts/quality-gates.sh 2>&1 | tail -40` MASKS the exit code (tail's wins) — a
failed QG can report exit 0. Run to a file and check the real `$?` (e.g.
`bash scripts/quality-gates.sh > /tmp/qg.log 2>&1; tail -5 /tmp/qg.log`), or the harness output file.

- **Archival must be a MOVE, not a COPY** — the AO-tracker session added a `status: resolved` twin to
  `plans/archive/2026_08/` while leaving the `status: active` original in `plans/active/`; the dual-tracking left the
  `finalize-plan-coverage` gate red fleet-wide (its checker scans the WORKTREE, exit 1 on the branch's clean tree). The
  completing fix was deleting the stale active twin.
- **Autostash-pop conflict signature**: `git pull --rebase --autostash` on a file upstream also modified can leave
  conflict-block markers (seven-`<` sequence; described, not quoted, because the prek conflict-marker hook greps the
  literal sequence and a doc quoting it trips the hook) in the WORKTREE file WITHOUT `git status` reporting unmerged (U)
  entries — always grep the affected file for those blocks after an autostash pop, and resolve by taking the upstream
  version when it is canonical (their content is already on origin — nothing is lost).
- **Gate verdicts follow the WORKTREE, not the branch**: `check_finalize_plan_coverage.py` (and the QG generally) scans
  disk state; a worktree deletion can flip a gate before the commit exists. Verify against a clean `git archive`
  extraction when a gate verdict seems inconsistent with the branch content.
- **Consecutive-kill → switch mechanism**: two identical harness kills of Bash `run_in_background` until-loop watchers
  (post-compaction) → stop blind-re-arming; use Monitor (persistent) + a self-checking cron instead.

**Recommended next item** (IN FLIGHT — quickmerge re-gate blocked on foreign `finalize-plan-coverage`; watcher
`bidxjckrg2` polls the checker): on "FINALIZE COVERAGE GREEN", re-run PM QG (real exit code) → quickmerge Pass 2
`--agent --files '<6 changed paths>'` (issue doc included) → verify SHA on origin → POST `/api/slots/6/done` → flip
harness task #4 → ✅ CLOSE the `BLK-bea57103` and the new BLK bookends.

- **2026-08-06 (data_engineering, slot 11, task context_scope_marker_claims_exceed_frontmatter_count-003)**:
  COUNT_MISMATCH verdict added to `generate_context_scope_inventory.py` (unified-trading-pm@a4fbf7f61). Decision: ADD
  the check — root-cause finding from task -001 confirmed the class is systemic (4 distinct entry-drop commits on 2
  separate dates, none one-time), so a COUNT_MISMATCH doc would permanently hide behind UP_TO_DATE without it.
  Implementation: new `_latest_marker_info()` (date + position), `_marker_claimed_count()` (extracts parenthetical count
  from the Progress Log bullet window), `COUNT_RE = re.compile(r"\((\d+)\s+entr(?:y|ies)\)")` (handles both "entry" and
  "entries"). `_latest_marker()` refactored as a thin wrapper to preserve the sweep tool's existing API. Verdict fires
  when marker is date-fresh AND claimed count != actual list length — covers both entry-drop (claimed > actual) and
  write-time miscount (claimed < actual) shapes. Test coverage: 4 unit helpers
  (test_latest_marker_info_returns_date_and_position, test_latest_marker_info_none_when_absent,
  test_latest_marker_info_breaks_ties_by_taking_last_occurrence, test_marker_claimed_count_extracts_plural_entries,
  test_marker_claimed_count_returns_none_when_no_parenthetical) + 4 end-to-end fixture cases (COUNT_MISMATCH entry-drop,
  COUNT_MISMATCH write-time miscount, UP_TO_DATE no-count-claim, UP_TO_DATE matching count). 1720 passed / 0 failed on
  PM QG.
- **context-scout 2026-08-07**: refreshed context_scope (4 entries, written and counted with extra care given this doc's
  own subject matter) — swapped the now-fixed `lst_rate_honest_coverage_2026_07_21.md` (distinct, already-closed
  cohort-5 bug, cited for contrast only) for the sole still-open `[OPERATOR]` todo's actual target,
  `data_completion_defi_2026_07_15.md`, plus `check_line_caps.sh` (the gate that todo must clear). Live-checked
  `data_completion_defi_2026_07_15.md` at write time: still 1000L, still carries the stale
  `context-scout 2026-08-01 (5 entries)` marker, but its frontmatter now shows 3 entries with
  `data_completion_to_100_all_ag_2026_06_21.md` ALREADY restored (only `migrate_defi_full_v9_canonical.py` remains
  genuinely missing) — apparently a concurrent, unrelated edit in this shared working tree; that doc is outside this
  batch's scope so left untouched, noted here only.
- **context-scout 2026-08-09**: re-scouted (flagged COUNT_MISMATCH by Phase 0, a known regex false-positive per
  `context_scope_count_mismatch_regex_false_positive_comma_extended_claim_2026_08_08.md` — this doc's own subject matter
  is that bug class, not an instance of it). Live-checked: `context_scope` still accurate for this doc's substance;
  added `scripts/plan-hygiene/generate_context_scope_marker_sweep.py` (the standing corpus-sweep tool this issue's todo
  2 shipped, previously missing from the list) — refreshed context_scope (5 entries). This fresh marker is now the
  latest, which self-heals the false positive for future Phase 0 runs.
