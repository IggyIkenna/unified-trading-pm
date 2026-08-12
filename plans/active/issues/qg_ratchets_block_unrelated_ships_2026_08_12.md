---
doc_type: issue
title:
  Time- and corpus-triggered QG ratchets block unrelated ships, and make concurrent agents race the same generated
  baseline
summary: >-
  codex_doc_freshness is a review-cadence reminder implemented as a HARD ship blocker. Docs were written in batches, so
  they age in COHORTS and the ratchet fires in clumps on consecutive days — the 05-12 cohort (2 docs) blocked ships on
  2026-08-11, the 05-13 cohort (6 docs) blocked them on 2026-08-12, and the 05-14 cohort will do the same next. Nobody
  changed anything; the clock moved. Whoever happens to be shipping that day inherits the debt, and because the baseline
  is a GENERATED file, two agents hitting the same cohort simultaneously both regenerate it and collide (observed: a UU
  conflict on codex_doc_freshness_baseline.yaml on 2026-08-12). Measured over one session, six ship attempts on a
  tests-only change were blocked by six different gates and only two were the author's.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, ratchet, ship-blocker, multi-agent, codex-freshness]
related:
  [
    /codex/06-coding-standards/quality-gates.md,
    /codex/12-agent-workflow/ship-tooling-silent-success.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Observed 2026-08-11/12 while shipping unrelated bats-hermeticity and codex-doc work; the same ratchet blocked ships on
  two consecutive days with no content change in either case.
depends_on: []
context_scope:
  [
    unified-trading-pm/scripts/quality_gates/check_codex_doc_freshness.py,
    unified-trading-pm/scripts/quality_gates/codex_doc_freshness_baseline.yaml,
  ]
---

# QG ratchets block unrelated ships

## The measurement

Six consecutive ship attempts on a **tests-only** change were blocked by six different gates. Only two were the author's
fault:

| gate                    | cause                                                  | author's?    |
| ----------------------- | ------------------------------------------------------ | ------------ |
| commit-SHA evidence     | a peer's local-only commit never reached origin        | no           |
| **codex doc freshness** | 2 docs tipped 90d→91d — the CLOCK moved                | **nobody's** |
| frontmatter schema      | plan vocabulary used in a codex doc                    | yes          |
| doc body links (×2)     | a `codex/`-prefixed CLAUDE.md shorthand read as a path | no           |
| AO dispatch-visibility  | zero-dispatchable docs 9→13 from the day's plan flips  | no           |

## Why freshness is the worst of them

- **It fires on the calendar, not on a change.** Nothing was edited; the docs simply aged past 90d.
- **It fires in COHORTS.** Docs written in a batch share a `last_reviewed`, so they cross the threshold together:
  2026-05-12 cohort → blocked 08-11; 2026-05-13 cohort (6 docs) → blocked 08-12; 05-14 next.
- **It creates a multi-agent race.** The baseline is generated. Two agents hitting the same cohort both run
  `--baseline-write` and collide — a `UU` conflict on 2026-08-12, resolved only by regenerating (hand-merging two
  generator outputs would produce a baseline matching neither run).
- **The absorb-it path is corrosive.** `--baseline-write` is the documented remedy, so the rational move under time
  pressure is to absorb someone else's review debt into the baseline. Done repeatedly, the ratchet stops meaning
  anything.

## Todos

- [x] ✅ [BACKEND] P2. **Convert codex_doc_freshness from a hard ship blocker to a warn-with-digest.** SHIPPED
      2026-08-12 — `unified-trading-pm@9498b9f3a5`. Was blocked for a day on
      `/plans/archive/issues/cloudbuild_drift_deployment_api_blocks_all_pm_code_ships_2026_08_12.md` (SUPERSEDED
      2026-08-12 by `/plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`), which failed
      PM `quality-gates.sh` and so denied `quickmerge` its sentinel for ALL PM code; cleared by
      `deployment-api@b928d173b5` reverting the offending step (drift back to `[OK] 16 == baseline`, verified before
      shipping).

      **Merged, not overwritten.** While this sat blocked, origin moved 168 commits and independently rewrote all three
          target files: a *different* fix to the same problem landed — the retired-doc exemption
          (`_is_retired_with_successor`), which refactored `_check_doc` into `_check_parsed`, exactly where this change
          lives. The stashed copies were therefore NOT applied (doing so would have reverted that work); the agency split
          was re-implemented against the new shape. The two compose rather than collide: the exemption removes docs nobody
          should re-read, this stops the remainder blocking unrelated ships. Neither alone sufficed — the exemption still
          left live docs tipping on the calendar. That relationship is recorded in the module docstring and the test header
          so a later reader does not mistake one for a supersession of the other.

          Implementation — `partition_by_agency()` splits violations by cause: `stale` (the clock moved) is advisory and
          prints an owner-grouped digest; the three authoring reasons (`no-frontmatter`, `no-last_reviewed-field`,
          `invalid-last_reviewed-format`) still block, because those are caused by the change in hand. Partition fails
          CLOSED — any reason not explicitly listed in `CLOCK_DRIVEN_REASONS` blocks, so a future check can't ship as a
          silent no-op. Measured end-to-end, all four exit codes captured directly (not inferred): aging cohort (30d window,
          68 newly-stale) → exit 0; normal run (90d) → exit 0; authoring defect (missing `last_reviewed`) → exit 1;
          `--strict` (30d) → exit 1. The 30d run is the real proof: 68 docs newly past the window produced a routed digest
          and **did not block**, where before it was 68 hard failures. `--strict` still fails on everything — that is the
          mode a scheduled digest/audit job uses. Also fixed the summary line, which printed "0 new violations" while the
          digest above it listed 68; it now says "0 new BLOCKING violations … 68 new advisory". Evidence: **33/33 unit tests
          green** on the merged base (27 pre-existing incl. the exemption's own, 6 new, one being a fail-closed guard that
          an unclassified reason BLOCKS rather than silently downgrading to a warning). All four exit codes and the tests
          were re-measured after the merge, not carried over from the pre-merge run — the re-application dropped one edit
          (the summary line still read "0 new violations"), which only the re-measurement caught.

- [ ] [BACKEND] P3. **De-cohort the thresholds** so a batch of docs written the same day does not expire the same day —
      e.g. jitter the limit per doc (90d + hash(path) % 14) or stagger `last_reviewed` on bulk authoring. Without this,
      even a digest arrives as a once-a-quarter flood rather than a trickle.
- [ ] [DOCS] P3. Record the distinction the absorb-path needs: a **correctness** ratchet (commit-SHA evidence — asserts
      a claim is TRUE) must never be re-baselined by a passer-by, while a **hygiene** ratchet (freshness, link-prose)
      may be, with the debt named in the commit. Both were hit in one session and treated differently on purpose; that
      reasoning currently exists only in commit messages.

## Progress Log

- 2026-08-12 — Filed. Two consecutive days of clock-triggered blocking, plus a generated-baseline race between two
  agents who both did the correct thing independently. The immediate instances were absorbed into the baseline with the
  debt named in each commit, which is the sanctioned remedy but not a fix.
- 2026-08-12 — Warn-with-digest **SHIPPED** as `unified-trading-pm@9498b9f3a5` once the cloudbuild blocker cleared. Two
  things worth carrying forward from the unblock. (1) **A blocked change is not a frozen change** — origin moved 168
  commits while this waited, and a different fix to the same problem landed in the same functions. Popping the stash
  would have silently reverted it; the split had to be re-implemented on the new base. Anything parked for a day needs a
  re-read of its target files before shipping, not a replay. (2) **The gate sentinel can go stale mid-gate on a shared
  slot** — `slot-cron-ff-pull` fast-forwarded HEAD twice during a 4-minute `quality-gates.sh` run, so the gate passed
  but `sentinel != HEAD` and quickmerge would have refused. Running gate and quickmerge as one chained invocation
  shrinks that window from minutes to seconds; two separate turns loses the race whenever the gate outlasts the 5-minute
  cron.
- 2026-08-12 — Warn-with-digest implemented + verified, then **not yet shipped** (blocked on the deployment-api
  cloudbuild drift, which denies every PM code ship its gate sentinel). The useful reframe was that "freshness" is not
  one thing: three of its four violation reasons are authoring defects the author can fix in seconds, and only `stale`
  is the calendar. Splitting on CAUSE keeps the gate meaningful for what a change controls while removing the part that
  punished people for the passage of time. That split also removes the incentive that was corroding the ratchet — with
  staleness non-blocking, nobody needs `--baseline-write` mid-ship, so the baseline-regeneration race between concurrent
  agents has no reason to occur. Remaining todos (de-cohorting, the ratchet taxonomy doc) are unblocked but not done.
