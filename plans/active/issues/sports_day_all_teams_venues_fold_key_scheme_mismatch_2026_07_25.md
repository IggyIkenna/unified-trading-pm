---
doc_type: issue
title:
  Sports `day=all` teams/venues "fold into FLAT" is not mechanically executable — disjoint venue-key schemes, no live
  FLAT layout for TEAMS, and zero live readers of the legacy path
summary: >-
  The task premise ("fold day=all TEAMS/VENUES into SportsLayout.FLAT + dedup") does not survive contact with the real
  GCS objects. Confirmed via direct read: (1) UAC's SSOT only maps VENUES to a FLAT layout — TEAMS is PER_DAY_PER_LEAGUE
  only, so "fold into FLAT" is inapplicable to TEAMS as stated; (2) the legacy day=all/entity=venues object uses raw
  numeric api_football venue_id keys (e.g. 1456) while the live FLAT venues.parquet uses slugified string keys derived
  independently by the live writer (e.g. OLD_TRAFFORD) — zero overlap across 3,445 legacy vs 2,860 live keys, so there
  is no join key to "dedup" against; (3) no code in the 6 core sports repos reads the day=all path at all — the live
  writer (_write_venues_from_teams) regenerates FLAT venues.parquet independently from live TEAMS data and never
  consumes the legacy object. This looks like dead/orphaned legacy data rather than a live reconciliation target, but
  instruments-store-sports-prd has soft-delete=0 (irreversible delete) and the original plan author explicitly flagged
  "do NOT blind-delete (would break team/venue resolution)" — that risk can't be fully ruled out by an in-repo grep
  alone (an offline ML-training/notebook consumer outside these repos is possible), so this needs an explicit operator
  call, not a unilateral delete or a fold that has no valid join key.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, data-correctness, legacy-cleanup, gcs-delete, reference-data, teams, venues, blocked-operator-decision]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-25
assigned_vm: NA
parent_epic: sports_master
execution_scope: local-only
priority: P2
estimate_class: research
source: >-
  sports_satellite_ao_dispatch_batch2_2026_07_24.md todo 2 ("Retention floor = the EXISTING per-source genesis
  registry"), itself sourced from sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md line 163.
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports `day=all` teams/venues fold — blocked on a real design ambiguity + irreversible-delete risk

> **🟢 AUTHORIZED 2026-07-25 (operator, in-session)** — Option A selected: treat `day=all` as confirmed-dead legacy data
> and delete both objects, backup-copy-first per the standard protocol. See the `[OPERATOR]` todo at the end of this doc
> for the tracked delete action.

## What the task assumed vs what's actually there

The assigned todo's premise (authored 2026-06-24): "`day=all` holds `entity=teams` + `entity=venues` (~974KiB),
date-invariant REFERENCE data. But `teams` also appears per-day-per-league → possible dual storage. RECONCILE: canonical
home for date-invariant reference is `SportsLayout.FLAT` ... fold `day=all` into FLAT ... + dedup — do NOT
blind-delete."

Direct GCS read (bucket `instruments-store-sports-prd-central-element-323112`) confirms the byte count (~974KiB) but not
the mechanics assumed:

- `sports_reference/by_date/day=all/entity=teams/teams.parquet` — 1 object, 780,370 bytes, **30,069 rows**, 17 columns
  (team + embedded venue fields + `season` + `af_league_id`). 6,252 unique `team_id`; 22,241 unique `(team_id, season)`
  pairs, seasons 2019–2025. This is a **season-keyed team×venue snapshot**, not a date-keyed one.
- `sports_reference/by_date/day=all/entity=venues/venues.parquet` — 1 object, 217,049 bytes, **3,445 rows**, 13 columns
  (`id`, `venue_id` [raw numeric, e.g. `1456`], `name`, `address`, `city`, `country`, `capacity`, `surface`, `image`,
  `latitude`/`longitude`/`altitude` all-null, `available_at` all-null).

## Finding 1 — TEAMS has no FLAT layout in the current SSOT

UAC `unified_api_contracts/canonical/domain/sports/gcs_paths.py`'s `SPORTS_DATA_TYPE_LAYOUT` maps
`VENUES → SportsPathLayout.FLAT` only. `TEAMS` maps to `PER_DAY_PER_LEAGUE`
(`sports_reference/by_date/day={D}/entity=teams/league={L}/teams.parquet`). There is no `sports_reference/teams/` FLAT
target for the live writer to fold into — "fold day=all teams into FLAT" is not executable today without first deciding
whether to (a) add a net-new FLAT layout for TEAMS to the UAC SSOT (a schema change, not a data-migration task), or (b)
fold `day=all` teams rows into the per-day-per-league structure instead (which the original task text did not consider,
and which needs a `league=`/`day=` assignment strategy for 30,069 rows that have neither).

## Finding 2 — VENUES fold has no valid join key (verified, not assumed)

The live FLAT target (`sports_reference/venues/venues.parquet`, written by `instruments-service`'s
`_write_venues_from_teams()`) has 2,860 rows keyed by a slugified string `venue_id` derived from the venue name (e.g.
`OLD_TRAFFORD`, `ESTADIO_MUNICIPAL_DE_ANGRA_DO_HEROISMO`). The legacy `day=all/entity=venues/venues.parquet` is keyed by
raw numeric api_football `venue_id` (e.g. `1456`, `19939`). Comparing both key sets directly:

```
day=all venue_id count (unique): 3445
live FLAT venue_id count (unique): 2860
intersection: 0
```

Zero overlap. There is no mechanical `dedup`/`fold` operation possible against these two files as-is — any
reconciliation would require fuzzy matching on `name`+`city` (or some other derived join) across ~3,445 legacy rows,
which is itself a data-quality sub-project, not the one-line "fold + dedup" the task described.

## Finding 3 — no live reader of `day=all` found (but not conclusively zero consumers)

Grepped all 6 core sports repos (`instruments-service`, `market-data-processing-service`, `features-service`,
`unified-api-contracts`, `deployment-service`, plus scripts dirs) for `day=all` / the `'all'` sentinel:

- `backfill_sports_per_entity_manifest.py` explicitly **excludes** `day=all` from `_list_days()` and instead treats
  VENUES as a manifest "singleton" emitted at a synthetic `SINGLETON_SENTINEL_DATE = 2024-01-01`.
- `delete_legacy_sports_objects_2026_06_24.py` explicitly **skipped** `day=all` with the comment "needs FLAT reconcile
  first" — i.e. this exact ambiguity was already flagged once before and deferred, not resolved.
- No production writer or reader path touches `day=all` — the live VENUES writer (`_write_venues_from_teams()`)
  regenerates the FLAT file independently from current TEAMS data on every run; it does not read the legacy object.

This is consistent with `day=all` being **dead/orphaned data** from an earlier writer generation (raw api_football
numeric keys predate the current slug-key scheme). It is NOT proof of zero consumers — an offline ML-training notebook
or ad-hoc analysis script outside these 6 repos could still reference it, which is exactly the risk the original plan
author flagged ("would break team/venue resolution").

## Why this can't be resolved unilaterally

`instruments-store-sports-prd` had **soft-delete=0** at the time this doc was authored (confirmed in
`/codex/02-data/sports-2020-06-data-floor.md`'s wipe-campaign status section) — any delete was irreversible, no 7-day
recovery net (unlike `features-sports-prd`). **⚠️ Stale as of 2026-07-27**: this bucket's soft-delete was fixed the same
day as the 2026-07-17 manifest-consolidator incident that prompted it
(`gcloud storage buckets update ... --soft-delete-duration=7d`) — a fresh
`gcs_bucket_soft_delete_retention_seconds(...)` check today returns `604800` (7 days), confirmed via
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a's fleet baseline. This resolves reason (b) below, but
NOT reasons (a)/(c) — those were never about reversibility. Given (a) the fold-as-described is not mechanically possible
(Finding 1/2 — moot for the delete path once the operator selected Option A over B), (b) ~~the alternative (delete as
dead legacy data) is irreversible~~ no longer applies (see above), and (c) my in-repo grep can rule out live-code
consumers but not every possible offline consumer — the judgment call requiring operator sign-off was about WHETHER to
delete at all (reasons a/c), which the operator already resolved by authorizing Option A below; only the delete's
EXECUTION mechanics changed with the reversibility fix, not the judgment call itself.

## Disposition (main, 2026-07-25)

Interim: **leave `day=all` in place** (Option C below) — this investigation is the deliverable; the AO-dispatched todo
(`sports_satellite_ao_dispatch_batch2_2026_07_24.md`) is closed as resolved-as-investigated on that basis. Two items
remain genuinely escalated to the operator, not re-opened as worker-dispatchable work: (1) authorize/decline the delete
of the two `day=all` objects (Option A — was soft-delete=0/no recovery net at the time, now fixed, see below); (2) the
TEAMS FLAT-layout design decision (Option B — net-new UAC layout vs fold into per-day-per-league). This doc stays `open`
until the operator rules on either.

## Options

- **A (recommended). Treat `day=all` as confirmed-dead legacy data and delete both objects** (following the standard GCS
  delete-safety protocol: backup-copy first to a `_legacy_archive/` prefix or equivalent, verify backup, then delete
  originals, then verify gone) — since no live reader exists, the live FLAT venues target already independently covers
  current venue data, and TEAMS per-day-per-league data already independently covers current team data. This resolves
  the "possible dual storage" concern by removing the orphaned copy rather than merging it. Needs explicit operator
  authorization given the zero-recovery-margin bucket.
- **B. Escalate the TEAMS FLAT-layout question to a design decision first** (does TEAMS get a net-new UAC FLAT layout,
  or does day=all fold into per-day-per-league?) before touching VENUES at all — slower, but resolves Finding 1 properly
  instead of leaving TEAMS's canonical home undefined.
- **C. Leave `day=all` in place, do nothing** — lowest risk, but perpetuates the "possible dual storage" ambiguity this
  todo was meant to close, and re-surfaces every time someone re-reads the source plan's retention-cleanup note.

## Note on this todo's OTHER half (pre-genesis anomaly check) — not new work, already tracked

The same parent todo also asked for a "per-source pre-genesis ANOMALIES only... targeted check + delete/relabel" pass.
Manifest census confirms: TEAMS has 131,306 rows dated before the current 2020-06-06 floor (124,239 `captured`), VENUES
has 1,457 pre-floor rows (all `captured`). These are **not new findings** — they are a subset of the already-tracked,
already-deferred **944,776 phantom pre-floor `instruments-store` manifest rows** documented in
`/codex/02-data/sports-2020-06-data-floor.md`'s "DEFERRED — manifest-row-level phantom prune" section, which is
explicitly blocked on a GCS-walk manifest rebuild (`deployment-service/scripts/rebuild_sports_manifest.py`) and
explicitly **not** a hand-edit target ("the index has an active consolidator lock... a hand-edit is the corruption the
protocol forbids"). Building a bespoke delete/relabel script for TEAMS/VENUES specifically would duplicate that
already-owned effort and risk the exact hand-edit violation the floor doc warns against. **No separate action needed
here** — this half of the todo is satisfied by reference to the existing tracked item, not new code.

Also note: the todo's quoted per-source genesis dates (understat 2014-01-01, api_football 2015-01-01,
footystats/transfermarkt/SFI 2019-01-01, open_meteo 2019-03-02) are **stale** — authored 2026-06-24, one month before
the 2026-07-21 operator ruling that collapsed every sports source's `SOURCE_COVERAGE_START` to a uniform `2020-06-06`
floor with a WIPE (not relabel) mandate. Any future work against this todo's text should read the floor doc first, not
the todo's own quoted dates.

## Todos

- [ ] [SCRIPT] P2. **🟢 AUTHORIZED 2026-07-25 (operator, in-session) — Option A.** Delete
      `sports_reference/by_date/day=all/entity=teams/teams.parquet` and
      `sports_reference/by_date/day=all/entity=venues/venues.parquet` in
      `instruments-store-sports-prd-central-element-323112`, following
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`: backup-copy both objects to a `_legacy_archive/`
      prefix (or equivalent) first, verify the backup, then delete the originals, then verify gone. **No longer
      `[OPERATOR]`-gated — reversibility-verified** (finding T, `task_template.md`): object-level delete only (2 named
      objects, never the bucket) — `gcs_bucket_soft_delete_retention_seconds(...)` returned `604800` (7 days)
      fresh-checked 2026-07-27 per §3a (this bucket was the one that had soft-delete disabled at authoring time; fixed
      2026-07-26). Re-query fresh before running, not from this citation. The operator's Option-A authorization already
      covers the judgment call on the residual unconfirmed-offline-consumer risk (Finding 3) — the backup-copy-first
      step stays as extra safety margin regardless. Done-when: both objects removed from the live path, backup copies
      confirmed present, corresponding manifest rows (if any) cleared.
