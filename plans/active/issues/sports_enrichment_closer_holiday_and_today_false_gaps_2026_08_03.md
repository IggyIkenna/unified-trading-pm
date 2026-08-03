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
      re-run this closer (the mirror rule should then fire on its own). (repo: instruments-service)
- [ ] [INFRA] P3. Add a `--provisioning-model` flag (default `SPOT`, `--on-demand` opt-out) to
      `deployment-service/scripts/vm/launch-sports-is-gap-fill.sh`, matching the pattern other backfill launchers use,
      to close the SPOT-default gap. (repo: deployment-service)
