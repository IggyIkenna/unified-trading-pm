---
doc_type: issue
title: Sports enrichment gap-closer misses Christmas/today false-positive classes; gap-fill launcher lacks SPOT
summary:
  While closing the legacy-CAS aggregate-manifest-gate investigation todo
  (sports_consolidated_native_ao_extract_2026_07_25.md), a fresh dry-run of
  close_stale_enrichment_expected_unattempted_cells_2026_07_19.py showed 1,171 stuck (expected_unattempted,
  blank-reason) cells left untouched — far above the ~205-227 the plan expected. Breaking the set down by date shows
  1,091 of 1,171 (93%) fall on exactly 3 dates (2026-08-03 = today; 2024-12-24/2024-12-25/2025-12-25 = Christmas Eve/Day
  across 2 seasons) — near-certainly NOT genuine pending-fetch gaps (today = same-day pipeline lag; Christmas = the same
  off-season/ no-fixture false-positive class the 2026-07-19 investigation already diagnosed, just not covered by this
  closer's independently-provable bar). The genuine remainder is ~80 cells across 6 dates in 2026-07-03..07-14, which
  were re-fetched via launch-sports-is-gap-fill.sh (no --provisioning-model=SPOT flag exists on that launcher — a
  second, smaller finding against the workspace's "Backfill VMs default to SPOT" HARD RULE).
status: open
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [sports, manifest, honest-absence, gap-closer, vm-launcher, spot]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
  ]
created: "2026-08-03"
parent_epic: sports_master
priority: P3
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source: [sports_consolidated_native_ao_extract_2026_07_25.md Track S2 legacy-CAS-question + 205-227-cell-refetch todo]
last_updated: "2026-08-03"
context_scope:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
---

# Sports enrichment closer misses holiday/today false-positive classes; gap-fill launcher has no SPOT option

## What I found

Running `instruments-service/scripts/close_stale_enrichment_expected_unattempted_cells_2026_07_19.py` (dry-run,
read-only, 2026-08-03) against `instruments-store-sports-prd-central-element-323112` reported:

```
5,356 stuck (expected_unattempted, blank-reason) enrichment cells
1,866 would close as EXPECTED_NO_PROVIDER_COVERAGE
2,319 would close mirroring FIXTURES' own empty reason
1,171 left untouched (genuine pending-fetch gaps, not this script's concern)
```

Breaking the 1,171 "left untouched" cells down by date:

| date                               | count | why almost certainly NOT a genuine gap                                   |
| ---------------------------------- | ----- | ------------------------------------------------------------------------ |
| 2026-08-03                         | 316   | TODAY — same-day fixtures naturally not yet enriched (pipeline lag)      |
| 2024-12-24                         | 316   | Christmas Eve — off-season/no-fixture across most leagues (winter break) |
| 2024-12-25                         | 316   | Christmas Day — same                                                     |
| 2025-12-25                         | 143   | Christmas Day, one year later — same pattern recurs                      |
| (6 other dates, 2026-07-03..07-14) | 80    | genuine — no seasonal/same-day explanation, real pending-fetch gaps      |

1,091 of 1,171 (93%) are the 4 holiday/today dates. This is the SAME off-season/no-fixture false-positive class the
2026-07-19 investigation (`sports_p2_history_apifootball_2015_to_present_2026_06_27.md`, archived) diagnosed and built
this closer for — the closer's "independently provable" bar (provider-no-coverage, or FIXTURES' own manifest row for the
identical date/league already `empty_confirmed`) evidently isn't satisfied for these 4 specific dates, likely because
FIXTURES itself hasn't been stamped `empty_confirmed` for them either (a genuinely-no-fixture day still needs ITS OWN
honest-absence stamp before the mirror rule can fire).

**Only the remaining 80 cells (2026-07-03..07-14, 6 dates) are genuine gaps** — re-fetched this session via
`deployment-service/scripts/vm/launch-sports-is-gap-fill.sh` for all 4 entities (FIXTURE_STATS, FIXTURE_EVENTS,
FIXTURE_LINEUPS, PLAYER_STATS), narrow `--start-date 2026-07-03 --end-date 2026-07-14` window (manifest-skip makes the
wider window free for already-captured days).

**UPDATE 2026-08-03 (same-day follow-up, closing the parent todo's own done-when) — 3 of the 6 "genuine gap" dates were
themselves a 3rd false-positive sub-class, not a fetch-execution gap.** A fresh, filtered manifest read
(`read_availability_index(..., filters=[("date",">=","2026-07-03"),("date","<=","2026-07-14")])`) after the re-fetch
above showed FIXTURE_LINEUPS/FIXTURE_STATS/PLAYER_STATS fully resolved (0 stuck) but **FIXTURE_EVENTS still had 162
stuck cells, 100% concentrated on 2026-07-12 (64) / 07-13 (2) / 07-14 (96)** — their `written_at`/`attempted_at` were
unchanged from original seeding, proving the just-run VM never actually attempted them. Re-launched a scoped follow-up
(`instr-backfill-sports-fixture-events-20260803-024441`,
`--entity FIXTURE_EVENTS --start-date 2026-07-12 --end-date 2026-07-14`, completed rc=0) to rule out a simple
under-scoping bug — its own log shows **0 API calls queued** for 2026-07-14 (23 candidate fixtures, all 23
skip-classified: 8 policy-scope, 3 observed-out-of-coverage, 12 pre-fetch-already-captured), and the stuck-cell count
was **byte-identical before and after** (162/64/2/96). This is the SAME "no genuine fixture that date+league"
false-positive class as the Christmas/today dates above, just for a different league population (SWISS_CHALLENGE_LEAGUE,
MLS, AUSTRIAN_BUNDESLIGA, EKSTRAKLASA, SCOTTISH_PREMIERSHIP, SUPER_LIG, NORWEGIAN_CUP, BUNDESLIGA_2, LA_LIGA,
SUPERCOPPA_ITALIANA, and others — 96 distinct leagues) — not an execution bug, and not fixable by re-running the same
fetch again. Folded into the "Recommended decision" todo below rather than filed as a separate doc (identical root
cause + identical fix).

**Second, smaller finding**: `launch-sports-is-gap-fill.sh`'s `gcloud compute instances create` call
(deployment-service/scripts/vm/launch-sports-is-gap-fill.sh:125-136) has no `--provisioning-model=SPOT` flag — it always
launches on-demand, violating the workspace's "Backfill VMs default to SPOT (HARD RULE)"
(`/codex/05-infrastructure/spot-vms-for-backfill.md`). Low blast-radius (this launcher's jobs are short, narrow-window,
`VM_SHUTDOWN_ON_COMPLETION=true`) but still a real cost-hygiene gap on a launcher that gets reused.

## Why it matters

- The 07-25 plan's "~205-227 residual" estimate is now stale by ~5x on the raw left_untouched count, but the STRUCTURAL
  scope (genuine pending-fetch gaps) is actually close to the original estimate once holiday/today noise is excluded —
  the raw dry-run count alone is a misleading progress signal for this closer without this date breakdown.
- Christmas/today cells will keep re-appearing in every future dry-run of this closer (holidays recur annually; "today"
  is definitionally always in the left_untouched set) unless FIXTURES itself gets honest-absence-stamped for genuinely
  no-fixture holiday dates, or the closer gains a dedicated no-fixture-that-day rule.

## Recommended decision

- [ ] [DATA] P3. Extend `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s (or its underlying
      `instruments_service.engine.orchestrator.sports_reference_core._close_stale_enrichment_expected_unattempted_cells`)
      independently-provable bar to also close a cell when FIXTURES' OWN row for the identical (date, league) is
      `expected_unattempted` with zero fixtures scheduled that day per the provider's schedule endpoint (not just
      `empty_confirmed`) — OR file a targeted FIXTURES honest-absence backfill for the 4 Christmas dates first, then
      re-run this closer (the mirror rule should then fire on its own). **Scope now also covers** the 162 FIXTURE_EVENTS
      2026-07-12/13/14 cells found in the 2026-08-03 follow-up above (same root cause, 96 different leagues) — one fix
      closes both populations. (repo: instruments-service)
- [ ] [INFRA] P3. Add a `--provisioning-model` flag (default `SPOT`, `--on-demand` opt-out) to
      `deployment-service/scripts/vm/launch-sports-is-gap-fill.sh`, matching the pattern other backfill launchers use,
      to close the SPOT-default gap. (repo: deployment-service)
