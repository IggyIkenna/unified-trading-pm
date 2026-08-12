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

- [ ] [BACKEND] P2. **Convert codex_doc_freshness from a hard ship blocker to a warn-with-digest.** It is a
      review-cadence reminder, not a correctness gate — nobody asserts a stale doc is WRONG, only unread. Emit the stale
      list as a daily/weekly digest to an owner (the `owner:` frontmatter field exists for this), keep it non-blocking
      in the ship path. Done-when: an aging cohort produces a digest and zero blocked ships, and the baseline stops
      being written by agents mid-ship.
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
