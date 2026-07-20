---
doc_type: issue
title: >-
  Change-freeze calendar is largely decorative — NFP misses its release 7 of 12 months, ECB/BOE 2027 dates are
  synthetic, BOJ is a Saturday + half its meetings, options expiry misses the venue it names by 11h
summary: >-
  The freeze windows are DST HEDGES, not risk estimates — every dated row is hardcoded UTC and the dst_note column is
  read into a shell variable and never used, so the generator compensates by making windows wide enough to straddle both
  DST alignments. That hedge is already broken in several places, so the calendar today blocks deploys at times that do
  not contain the event it names. MEASURED - NFP is fixed at 13:25-14:00Z (the EST alignment) while the BLS print is
  12:30Z under EDT, so 7 of 12 months the freeze protects NOTHING; ECB and BOE 2027 dates are each exactly 364 days
  after 2026 (a uniform 52-week shift = fabricated, not published schedules); BOJ_2026_01 falls on a SATURDAY and BOJ is
  encoded quarterly (4/yr) when it holds 8 policy meetings; options expiry lists deribit FIRST in affects_venues but its
  19:00-21:30Z window is ~11h away from Deribit's 08:00Z settlement. Blocks the operator's 30-min shortening directive -
  a 30-min window on an unverified date is cap-compliant, DST-correct and still protects nothing.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [change-freeze, ci-cd, prod-deploy, market-events, data-correctness]
related: [uac_value_only_config_change_breaks_utl_untested_2026_07_20.md]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  ["surfaced 2026-07-20 while implementing the operator directive to cap every change-freeze window at 30 minutes"]
locked_by:
locked_since:
resolved_by:
---

# The change-freeze calendar mostly does not freeze the thing it names

## Why the windows are wide (this is the key insight)

The widths are **DST hedges, not risk estimates**. Every dated row emits `"dst_note": ""`
(`scripts/ops/generate-freeze-calendar.py:213, 241, 302`) and the column is read into a shell variable at
`change-freeze-check.yml:84` / `freeze-deferred-build-replay.yml:64` and **never referenced again** — one grep hit per
file. There is no DST branch anywhere in either evaluator. So the generator compensates by making each window wide
enough to straddle both the summer and winter UTC alignment of the same local-time event: FOMC `18:00-20:30Z` spans the
EDT statement through the EST presser; options `19:00-21:30Z` spans both closes.

**This is why the operator's 30-min cap cannot be applied on its own.** 30 minutes cannot straddle a 60-minute offset
ambiguity. Capping without DST-awareness converts a wide-but-overlapping window into a narrow one pointed at the wrong
hour for half the year.

## Measured defects (all verified 2026-07-20)

| #   | Defect                                                       | Evidence                                                                                                                                                                                                     |
| --- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **NFP protects NOTHING 7 of 12 months**                      | Window fixed `13:25-14:00Z` (EST alignment); BLS prints 08:30 ET = **12:30Z under EDT**. Apr-Oct 2026 the window opens 55 min AFTER the release.                                                             |
| 2   | **ECB + BOE 2027 dates are synthetic**                       | 2027 entries are each **exactly 364 days** after 2026 (uniform 52-week shift, all 8 of 8 for both). Real central-bank calendars do not shift uniformly. The shift preserves weekday, so they look plausible. |
| 3   | **BOJ_2026_01 is a Saturday**                                | `date(2026,1,24).strftime('%A')` = Saturday. BOJ does not announce on Saturdays.                                                                                                                             |
| 4   | **BOJ encoded quarterly (4/yr); it holds 8 policy meetings** | `BOJ_DATES` has 4 entries per year (`:270-273`), `recurrence="quarterly"` (`:365`).                                                                                                                          |
| 5   | **Options expiry misses the venue it lists first**           | `affects_venues="deribit,ibkr,databento"` (`:244`) but window is `19:00-21:30Z` while Deribit settles **08:00Z** — ~11h away. The AM-settled/triple-witching SET (~13:30Z EDT) is also never covered.        |

Defect 2 is the gating one: a 30-min window on an unverified date is cap-compliant, DST-correct, and still protects
nothing. That is strictly worse than a wide window, because it reads as coverage.

## Why the fix is not just "make them 30 minutes"

Adversarial review of the shortening design raised three objections; the date-table one is fatal:

1. **FATAL — synthetic dates.** Precision on fabricated dates is meaningless. Real published schedules are a
   prerequisite, not a follow-up.
2. **SIGNIFICANT — window width was also phase-aligning the replay.** The hourly `freeze-deferred-build-replay` drains
   once the window lifts. A wide FOMC window did two jobs: mask the event AND hold the deferred build until the event
   was fully over. Capping to the statement alone means the deferred build replays into the 14:30 ET press conference —
   converting a deferral into a _targeted injection_ at the highest-vol minutes. Mitigation: emit a separate
   `FOMC_PRESSER` row (still ≤30 min, so the directive holds).
3. **SIGNIFICANT — new rows would be malformed.** `csv.DictWriter` raises on EXTRA keys but silently fills MISSING ones
   from `restval=''`, so any new row omitting `event_type` / `recurrence` / `block_*` emits blank columns — and a blank
   `block_prod_deploy` fails the `= "true"` test, i.e. a freeze row that blocks nothing. Any new-row work needs a
   generator-side assertion that every emitted row's key set equals `set(HEADER)`.

## The honest trade the cap makes (once dates are real)

- **NFP, BOE**: pure improvement — DST-aware 30-min windows FIX currently-broken coverage.
- **Options expiry**: improvement — 150 min becomes up to 3× 30-min rows that actually hit Deribit 08:00Z, the AM SET,
  and the PM close. More freeze _events_, fewer frozen _minutes_.
- **FOMC / ECB**: real loss — the press conference becomes uncovered unless a second presser row is emitted.
- **BOJ**: unavoidable loss. The policy statement has **no pre-announced minute** (typically 11:30-12:30 JST, but
  routinely past 13:00 on contentious meetings, and the delay itself is tradeable). Only the 15:30 JST governor's press
  conference is deterministic. BOJ cannot be point-targeted; it needs an explicit operator exception.

## Todos

- [ ] [DEVOPS] P1. Replace `FOMC_DATES` / `ECB_DATES` / `BOE_DATES` / `BOJ_DATES`
      (`generate-freeze-calendar.py:252-273`) with the PUBLISHED schedules, each entry carrying a source citation, and
      for FOMC/BOJ explicitly the ANNOUNCEMENT day of the two-day meeting. Gating for everything below.
- [ ] [DEVOPS] P1. Make dated rows DST-aware — resolve each occurrence's UTC offset at generation time from its local
      anchor (`08:30 America/New_York`, `14:00 America/New_York`, `14:15 Europe/Berlin`, `12:00 Europe/London`,
      `16:00`/`09:30 America/New_York`), and populate `dst_note` so the CSV shows its own reasoning.
- [ ] [DEVOPS] P1. Apply the ≤30-min cap (operator directive 2026-07-20) once the two above land.
- [ ] [DEVOPS] P2. Emit `FOMC_PRESSER` + `ECB_PRESSER` rows (each ≤30 min) so capping does not inject the deferred build
      into the press conference.
- [ ] [DEVOPS] P2. Split options expiry into Deribit-08:00Z / US-AM-SET / US-PM-close rows; fix BOJ to 8 meetings.
- [ ] [DEVOPS] P2. Add a generator assertion that every emitted row's keys == `set(HEADER)`, and a check that every
      window CONTAINS its event anchor in both DST halves — the current calendar would have failed both.
- [ ] [DEVOPS] P3. Decide the BOJ exception explicitly (keep a wide window as a named carve-out, target the 15:30 JST
      presser and accept statement exposure, or drop it and rely on other controls).

## Progress Log

- **2026-07-20** — Found while implementing the 30-min cap. The cap itself is NOT shipped: it is gated on real date
  tables, since a precise window on a fabricated date protects nothing while looking like coverage. The alerting half of
  the same operator instruction WAS shipped (routine freeze-block advisory removed; stale-deferral guard added so a
  never-draining deferral pages after 6h — that path was previously unalerted entirely).
