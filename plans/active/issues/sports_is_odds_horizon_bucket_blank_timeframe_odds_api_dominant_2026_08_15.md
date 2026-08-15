---
doc_type: issue
title:
  "IS surface: 899,508 (84%) of odds_horizon_bucket rows have blank timeframe, 99.8% under venue=ODDS_API — far larger
  and older than the CF-8 500-row test population, root cause not yet confirmed"
summary:
  "Auditing whether CF-8's timeframe-drop bug (sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md) also hit
  the IS surface's 500-row test found a population 1800x larger than expected: 899,508 / 1,070,440 (84.03%) of
  instruments-store-sports-prd's odds_horizon_bucket rows have blank timeframe. 898,181 of those (99.8%) are
  venue=ODDS_API (900,969 total ODDS_API rows, only 2,788 non-blank = 0.3% populated). A separate ~dozen
  uppercase-cased bookmaker venues (BETVICTOR, WILLIAMHILL, FANDUEL, UNIBET, SKYBET, PADDYPOWER, PINNACLE, SPORT888,
  MATCHBOOK, DRAFTKINGS, BETONLINEAG, BET888SPORT) are ALSO ~100% blank, while a DIFFERENT set of uppercase bookmaker
  venues (BETRIVERS, BETSSON, BETFAIR_SB_UK, CORAL, VIRGINBET, LIVESCOREBET, BETFAIR_EX_UK, CASUMO, UNIBET_UK,
  BETFAIR_EX_EU, LADBROKES_UK, LADBROKES, SMARKETS) are 100% non-blank. written_at spans 2026-06-19 through
  2026-08-15, dominated by two spikes on 2026-08-08 (188,941) and 2026-08-09 (519,565) — 78.8% of the population,
  BEFORE this session started and not explainable by today's 500-row test (which accounts for ~359-386 rows/day in the
  2026-08-11..15 range). The 2026-08-08/09 timing correlates with rebuild_sports_manifest_v9.py's v9 migration (also
  calls _write_captured_rows(), the function CF-8 fixed at e0b34e77fd) but this is NOT confirmed. 0/5000 sampled blank
  rows have any non-blank-timeframe sibling under the coarse row-identity key. Root cause is genuinely undetermined
  between two very different explanations: (a) the same _write_captured_rows() bug, triggered by an earlier
  migration/backfill run before today's fix landed — in which case the blank rows may be non-destructive duplicates
  (originals may still exist, just not matching the sibling-check's coarse key) or may reflect a DESTRUCTIVE
  supersession that lost real timeframe data; or (b) venue=ODDS_API (and the ~dozen affected uppercase bookmaker
  venues) never populated timeframe via a wholly separate, older write path unrelated to CF-8 at all — in which case
  blank-timeframe is the correct/expected state and no data was lost. UPDATE (2026-08-15, later same session):
  todo 1 done — exhaustive grep found _write_captured_rows() has exactly 3 production callers repo-wide, all
  sharing the same bug, whose 3 fix commits all landed 2026-08-15 15:07-17:21 (after every spike date); no separate
  per-venue writer exists. Hypothesis (a) (CF-8-bug-triggered) is now the dominant, code-evidenced explanation, not
  an open toss-up. Exact per-date/per-script attribution and destructive-vs-additive status remain open (todos 2-3)."
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data]
scope: [engineer, admin]
tags:
  [
    sports,
    odds_horizon_bucket,
    timeframe,
    instruments-store,
    odds_api,
    data-correctness,
    venue-casing,
    cf8,
  ]
related:
  [
    /plans/active/issues/sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md,
    /plans/active/issues/sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md,
    /plans/active/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md,
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_sports_write.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
    market-tick-data-service/scripts/audit_sports_is_captured_phantom_timeframe_2026_08_16.py,
  ]
created: "2026-08-15"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source:
  "data_engineering worker, slot 2, dispatched on sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md's IS-surface
  audit sub-step, 2026-08-15"
repos: [market-tick-data-service]
scope_note: "root-cause investigation required before any cleanup scope — NOT AO-eligible as-is (open-ended judgment call)"
locked_by:
drift_direction: none
context_scope:
  [
    /plans/active/issues/sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md,
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_sports_write.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py,
  ]
depends_on: []
---

# IS surface: 899,508 blank-timeframe odds_horizon_bucket rows, 99.8% venue=ODDS_API — scope far larger than the CF-8 500-row test, root cause open

## What I found

Dispatched to close CF-8's open sub-step: "audit whether the same phantom-row class exists on IS (the 500-row test
population there has not been checked)." Wrote a memory-bounded, row-group-streamed audit script (IS's
`_index/availability_index.parquet` is 15.7M rows / 237MB — a naive full read has already been measured to OOM at
14G RSS on this host, per `_sports_is_captured_stream_read_2026_08_15.py`'s own docstring) and ran it dry-run against
production. Deliberately did not assume a `written_at` window (the IS 500-row test's exact timestamp was never
logged this session) — instead reported the full blank-timeframe population's distribution.

**Measured facts** (full corpus scan, not sampled, `audit_sports_is_captured_phantom_timeframe_2026_08_16.py`):

- `data_type=odds_horizon_bucket` on IS: 1,070,440 rows total, 899,508 (84.03%) blank-timeframe.
- Venue split of the FULL population (blank + non-blank):
  - `ODDS_API`: 900,969 rows total, only 2,788 non-blank (0.31% populated) — accounts for 898,181 of the 899,508
    blank rows (99.85%).
  - Also ~100% blank (appear in the full-population venue list at their real count, but do NOT appear at that count
    in the non-blank breakdown — only a much smaller LOWERCASE-cased duplicate of each carries real timeframe
    values): `BETVICTOR` (16,451), `WILLIAMHILL` (16,295), `FANDUEL` (14,974), `UNIBET` (11,784), `SKYBET` (10,445),
    `PADDYPOWER` (10,219), `PINNACLE` (8,149), `SPORT888` (7,365), `MATCHBOOK` (7,323), `DRAFTKINGS` (6,982),
    `BETONLINEAG` (6,791), `BET888SPORT` (5,744).
  - By contrast, 100% NON-blank (their non-blank count exactly equals their total count): `BETRIVERS` (5,665),
    `BETSSON` (5,275), `BETFAIR_SB_UK` (5,217), `CORAL` (4,684), `VIRGINBET` (3,683), `LIVESCOREBET` (2,923),
    `BETFAIR_EX_UK` (2,904), `CASUMO` (2,808), `UNIBET_UK` (2,691), `BETFAIR_EX_EU` (2,171), `LADBROKES_UK` (2,148),
    `LADBROKES` (1,890), `SMARKETS` (1,015).
  - The lowercase-cased duplicates of the "~100% blank" venue list (e.g. `betvictor` 184, `williamhill` 137,
    `fanduel` 60, ...) DO carry real timeframe values — small row counts (46-264 each), but 100% populated.
- `written_at` range: 2026-06-19T15:15:47Z to 2026-08-15T01:31:45Z. NOT a single-session cluster. By-day histogram
  has two dominant spikes: **2026-08-08 (188,941 rows) and 2026-08-09 (519,565 rows) = 708,506 rows, 78.8% of the
  total blank population** — both days BEFORE this session (2026-08-15) started. Other spikes: 2026-06-28 (130,715),
  2026-07-13 (30,089), 2026-07-25 (7,785). This session's own window (2026-08-11 through 2026-08-15, when the IS
  500-row test ran) accounts for only 384+383+383+386+359 = 1,895 rows total across those 5 days — 0.2% of the
  blank population, NOT the dominant source.
- Sibling check (5,000-row random sample, seed 42): 0/5,000 sampled blank-timeframe rows have ANY non-blank-timeframe
  sibling under the coarse `(date, venue, league_id, data_type, service_name)` key.
- `date` (the underlying match date, not `written_at`) range across the blank population: 2018-01-01 to 2026-08-15 —
  spans nearly the entire historical corpus, not a recent slice.

## Why this is NOT simply "the CF-8 bug found on IS too" (or at least, not confirmed to be)

CF-8's own doc already found a smaller, analogous case on MDPS (14,982 out-of-window blank-timeframe rows, root
cause not yet closed there either — see that doc's open P1 todo) and, separately, root-caused a 959-row no-sibling
subset as **legitimately pre-existing** (timeframe was never populated for those rows even before CF-8's bug
existed — sibling absence there was expected, not evidence of loss). This IS finding could be the same class of
pre-existing legitimate-blank population, just far larger in the IS surface's case. One fact still points at least
partly this direction:

- The uppercase/lowercase venue-casing duplication pattern here closely resembles
  `sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md` and
  `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`'s ALREADY-CONFIRMED writer-casing-bug
  class on this exact codebase (`SPORTS_VENUE_FOLD` bypassed at specific call sites) — this pattern may still be a
  CONTRIBUTING factor to *which* venues/rows appear in each rewrite's touched set, even if it is not the cause of
  the blank `timeframe` itself (see below).

**UPDATE (2026-08-15, later same session, todo 1 done): the writer-identity hypothesis is now substantially
weakened.** `_write_captured_rows()` (`market_tick_data_service/scripts/_rebuild_sports_write.py:274`) has exactly
**three** production call sites in the whole repo (exhaustive `grep -rn '_write_captured_rows('` across the full
tree, non-test) — there is no separate per-venue or per-bookmaker writer for `odds_horizon_bucket` rows at all:

1. `market_tick_data_service/scripts/rebuild_sports_manifest_v9.py:727` — the v9 canonicalization manifest rebuild.
   Confirmed via `--surface` arg handling (`if surface == "instruments":`) that this script DOES target the IS
   surface directly, not just MDPS. Launched via `deployment-service/scripts/vm/launch-sports-v9-migration-vm.sh`,
   a full-corpus migration — the only one of the three call sites with a plausible 500K+-row blast radius, making it
   the leading candidate for the dominant 2026-08-08/09 spike (708,506 rows, 78.8% of the population).
2. `scripts/sports_captured_available_at_targeted_backfill_2026_07_14.py:252` — already named above; created
   2026-07-14, so cannot explain the 2026-06-28 or 2026-07-13 spikes, but could explain 2026-07-25 or contribute to
   2026-08-08/09 if re-run.
3. `scripts/_sports_is_captured_backfill_from_subset_2026_08_15.py:149` — today's own script (this session's IS
   500-row test path); cannot explain any pre-08-15 spike.

All three route through the identical `_write_captured_rows()` function, and **all three of its timeframe-threading
fix commits landed TODAY, 2026-08-15, between 15:07 and 17:21 UTC** (`ecd30f4d` 15:07, `6ee75b0a` 17:08, `e0b34e77`
17:21 — confirmed via `git show -s --format='%h %ad %s'`). Every one of the blank-population's written_at spikes
(2026-06-28, 2026-07-13, 2026-07-25, 2026-08-08, 2026-08-09) falls BEFORE all three fix commits. This means: **for
the entire period that produced every spike in this population, the ONLY write path for captured `odds_horizon_bucket`
rows on IS was carrying the exact same bug CF-8 already diagnosed and fixed** — there is no evidence of a second,
structurally-different writer that "never populated timeframe by design." The bimodal 100%-blank-vs-100%-non-blank
venue split is now more parsimoniously explained as "which venues' rows happened to be present in a given rewrite's
touched batch" than as a writer-identity effect — though this is not yet proven down to the per-venue level (see
updated todo 2).

**Net effect: hypothesis (a) (CF-8-bug-triggered) is now the dominant, code-evidenced explanation.** What remains
genuinely open is (i) exactly which script(s) ran against IS on which spike dates (todo 2, needs execution logs —
the code-path plausibility is now very high but not log-confirmed), and (ii) whether the loss is destructive — the
0/5,000 sibling-check-miss result already suggests it may be, unlike MDPS's mostly-additive finding, but this needs
the full non-sampled re-check (todo 3) before treating it as confirmed data loss.

## What I did NOT do

- Did not attempt any write, cleanup, or delete — this audit is 100% read-only (no `--apply` flag exists on the
  script).
- Did not check whether `rebuild_sports_manifest_v9.py` or the 2026-07-14 targeted-backfill script actually ran
  against IS on the spike dates (would need VM launch history / Cloud Logging — still open, see todo 2, downgraded
  P1→P2 since it's no longer the root-cause blocker).
- ~~Did not check the `odds_api_adapter.py` / uppercase-bookmaker-venue writer code paths~~ — DONE later this
  session (todo 1): `odds_api_adapter.py` has zero `timeframe` references, and `_write_captured_rows()` has exactly
  3 production callers, all sharing the same bug. See the "UPDATE" in the section above.
- Did not compare this population against the equivalent MDPS surface's venue breakdown (does MDPS show the same
  ODDS_API-dominant blank pattern, or is this IS-specific?) — worth checking, since CF-8's doc's MDPS blast-radius
  numbers were reported by written_at-window, not by venue, so this comparison hasn't been made yet either.

## Recommended decision

Todo 1 (writer-code investigation) is now DONE — see the UPDATE above. Hypothesis (a) (CF-8-bug-triggered) is the
dominant, code-evidenced explanation; no separate "designed to be blank" writer exists. This narrows the remaining
work:

- Treat as (a) (CF-8-bug-triggered, potentially destructive) by default: needs the same rigor CF-8's doc used for
  MDPS — snapshot, full non-sampled sibling audit (not just a 5,000-row sample), and a decision on whether any of
  the 899,508 rows represent genuinely lost data needing backfill from another source, since the sibling-check here
  found ZERO survivors (unlike MDPS's mostly-additive finding). This is now the PRIMARY path, not a conditional one.
- Confirming exact per-date/per-script attribution (todo 2) is still valuable for scoping any backfill/remediation,
  but is no longer a precondition for treating this as CF-8-bug-class data loss — the code-path evidence alone is
  now strong enough to proceed on that assumption.
- Still NOT a P0 blocker on CF-8's own remaining todos (that doc's fix already landed and its own scope is MDPS +
  the original 500-row-test-equivalent IS class) — this is genuinely separate, larger-scoped work, and per the
  workspace's big-finding HARD RULE (data-correctness, cross-repo) the operator has been notified in-chat.

## Todos

- [x] [REVIEW] P1. Read `market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` and whatever
      writes the ~100%-blank uppercase bookmaker venues to determine whether these paths ever populate `timeframe`
      for `odds_horizon_bucket` rows by design, vs. the 100%-non-blank venue set's writer. **DONE (2026-08-15)**:
      `odds_api_adapter.py` has zero `timeframe` references — it does not write `odds_horizon_bucket` rows at all.
      Exhaustive repo-wide grep found exactly 3 production callers of `_write_captured_rows()`
      (`rebuild_sports_manifest_v9.py`, `sports_captured_available_at_targeted_backfill_2026_07_14.py`,
      `_sports_is_captured_backfill_from_subset_2026_08_15.py`), all sharing the one buggy function, whose 3
      timeframe-threading fix commits all landed 2026-08-15 15:07-17:21 — after every spike date. No per-venue
      writer distinction exists; see the UPDATE in "Why this is NOT simply..." above. (repo: market-tick-data-service)
- [ ] [DATA] P2. Check Cloud Logging / VM launch history for whether `rebuild_sports_manifest_v9.py`, the
      2026-07-14 targeted backfill, or another rewrite actually executed against `instruments-store-sports-prd` on
      2026-06-28, 2026-07-13, 2026-07-25, 2026-08-08, or 2026-08-09 — for per-date attribution/scoping only; the
      root-cause question itself (todo 1) is now resolved without this. Downgraded from P1 since it's no longer a
      blocker on treating this as CF-8-bug-class loss. (repo: deployment-service or GCP Cloud Logging)
- [ ] [DATA] P2. Once root cause is determined, re-run the sibling check WITHOUT the 5,000-row sample cap (full
      899,508-row population) if root cause (a) is confirmed — the 200-row/5,000-row samples CF-8 used elsewhere
      turned out to need exact confirmation before any delete scope was trusted (see that doc's own "NARROWED per
      2026-08-15 FULL-POPULATION audit" todo). (repo: market-tick-data-service)
- [ ] [REVIEW] P2. Compare against the equivalent MDPS surface's venue breakdown for `odds_horizon_bucket` blank-
      timeframe rows — is the ODDS_API-dominant pattern IS-specific or does MDPS show the same shape? Not yet
      checked (CF-8's doc reported MDPS's blast radius by written_at-window only, not by venue).

## Progress Log

- **2026-08-15 (slot 2, data_engineering)**: Filed while auditing CF-8's IS-surface open sub-step. Found the
  population 1800x larger than the sub-step's own framing assumed (899,508 vs. an expected ~500-row test
  population). Root cause genuinely undetermined between a CF-8-bug-triggered-by-an-earlier-migration explanation
  and a legitimate/structural venue-writer explanation — filing rather than guessing, per this workspace's
  CLAIM ≤ MEASUREMENT discipline. Not attempting any write/cleanup. Closing CF-8's own narrower sub-step with a
  pointer to this doc (that sub-step's literal question — "does the same phantom-row class exist on IS" — is
  answered: yes, trivially, but the real finding is this much larger, structurally different population this doc
  now owns).
- **2026-08-15 (slot 2, data_engineering, later same session)**: Resolved todo 1. `odds_api_adapter.py` never
  references `timeframe`. Exhaustive repo-wide grep confirms `_write_captured_rows()` has exactly 3 production
  callers (`rebuild_sports_manifest_v9.py`, `sports_captured_available_at_targeted_backfill_2026_07_14.py`,
  `_sports_is_captured_backfill_from_subset_2026_08_15.py`), all routing through the one buggy function; its 3
  timeframe-threading fix commits (`ecd30f4d`/`6ee75b0a`/`e0b34e77`) all landed today 15:07-17:21 UTC, after every
  spike date in the blank population. No separate per-venue/writer-identity bug found — the bimodal venue split is
  explained by which rows a given rewrite touched, not by a structurally-different writer. Root cause substantially
  narrowed toward hypothesis (a); recommended-decision section updated accordingly. Still not attempting any
  write/cleanup this pass. Todo 2 downgraded P1→P2 (attribution-only, no longer a root-cause blocker).
