---
doc_type: issue
title:
  sports league_id namespace — canonicalise-at-write SHIPPED; 214,842 historical rows still raw, 75,432 of them on an
  ambiguous name
summary: >-
  The sports manifest stored raw api-football display names as league_id (PREMIER_LEAGUE, 2._BUNDESLIGA) while every
  consumer keys on the canonical LEAGUE_REGISTRY slug (EPL, BUNDESLIGA_2) — 214,842 rows joined to nothing. Operator
  chose canonicalise-at-write (2026-07-20); shipped in mtds@ad4f1872 resolving by NUMERIC api_football_id. Measurement
  proved that choice necessary: six raw names are ambiguous and a name-keyed alias map would MERGE distinct leagues
  (SERIE_A = Italian + Brasileirao). History is NOT yet migrated — the manifest carries no numeric id, but the
  underlying parquet carries home_team/away_team, which resolves every sampled collision.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [sports, canonical, league-id, namespace, manifest, coverage, migration]
related: [../sports_consolidated_closeout_2026_07_19.md, ../sports_consolidated_audit_2026_07_19.md]
created: "2026-07-20"
source: operator decision 2026-07-20 (canonicalise at the write path)
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# sports `league_id` namespace — write path canonical, history still raw

## The defect

The availability manifest stored the RAW api-football display name as `league_id`, produced by `OddsApiAdapter` as
`league_cls.name.upper().replace(" ", "_")` — `PREMIER_LEAGUE`, `PRIMERA_DIVISION`, `2._BUNDESLIGA`, `FIRST_DIVISION_A`.
Every consumer keys on the canonical `LEAGUE_REGISTRY` slug — `EPL`, `ARGENTINA_PRIMERA`, `BUNDESLIGA_2`, `JUPILER_PRO`
— so those rows **joined to nothing**: absent from the coverage denominator, invisible to the gates, mis-bucketed in the
data-status UI.

Measured in the live sports manifest (1,974,679 rows): **214,842 rows carry a non-canonical `league_id`** across 60
distinct values. Top offenders: `CHAMPIONSHIP` 27,887 · `PREMIER_LEAGUE` 27,761 · `PRIMERA_DIVISION` 26,587 ·
`FIRST_DIVISION_A` 23,745 · `2._BUNDESLIGA` 22,127 · `SUPER_LEAGUE` 20,958 · `SUPERLIGA` 20,168 · `PREMIERSHIP` 16,404.

## Why canonicalise-at-write, not an alias map (the measurement that decided it)

Six raw display names are **genuinely ambiguous** — one name, two real leagues:

| raw name           | resolves to                                  |
| ------------------ | -------------------------------------------- |
| `BUNDESLIGA`       | `BUNDESLIGA` + `AUSTRIAN_BUNDESLIGA`         |
| `SERIE_A`          | `SERIE_A` + `BRASILEIRAO`                    |
| `SERIE_B`          | `SERIE_B` + `BRASILEIRAO_SERIE_B`            |
| `CHAMPIONSHIP`     | `ENG_CHAMPIONSHIP` + `SCOTTISH_CHAMPIONSHIP` |
| `PRIMERA_DIVISION` | `ARGENTINA_PRIMERA` + `CHILE_PRIMERA`        |
| `SUPER_LEAGUE`     | `GREEK_SUPER_LEAGUE` + `SWISS_SUPER_LEAGUE`  |

**A name-keyed alias map cannot resolve these — it would silently MERGE distinct leagues** (Italian Serie A with the
Brasileirão). Only the numeric `api_football_id` separates them, and that id is in hand at write time. This is the
concrete justification for the operator's choice.

## What shipped (write path — DONE)

`market-tick-data-service@ad4f1872`. `_canonical_league_id()` resolves via `get_league_by_api_football_id()`:

- **All 30 write-path prediction leagues resolve; 0 unresolved.** 13 of 30 change value.
- Unresolvable id → falls back to the raw name, so an unregistered league still captures (honest absence) rather than
  aborting the fetch loop.
- The `--leagues` filter now accepts BOTH the raw and canonical form. Without that, every existing launcher/runbook
  invocation (which passes the old raw name) would have silently fetched nothing — a change that fails closed and
  quietly.
- 3 regression tests, including one asserting the six collisions resolve to DISTINCT slugs (i.e. that the numeric id
  genuinely separated them rather than collapsing them).

## What remains: the historical migration

**The manifest has no numeric id.** Its only other provenance column is `venue` (a bookmaker: `ODDS_API`, `SKYBET`,
`BETVICTOR`), which cannot identify a league. So for the **75,432 rows sitting on an ambiguous name**, the manifest
alone is insufficient.

**But the underlying parquet resolves it.** `fixture_id` is empty and `sport_key` is only the display name, however
`home_team` / `away_team` ARE populated, and colliding leagues have disjoint squads. Sampled 2026-07-20:

| raw `league_id`    | teams found in the shard                                       | unambiguous league   |
| ------------------ | -------------------------------------------------------------- | -------------------- |
| `CHAMPIONSHIP`     | Barnsley, Birmingham City, Blackburn Rovers, Brentford, Fulham | `ENG_CHAMPIONSHIP`   |
| `PRIMERA_DIVISION` | Argentinos Juniors, San Lorenzo, Vélez Sarsfield, Huracán      | `ARGENTINA_PRIMERA`  |
| `SUPER_LEAGUE`     | BSC Young Boys, FC Zürich                                      | `SWISS_SUPER_LEAGUE` |

**Proposed migration** (not yet executed):

1. For the 139,410 UNAMBIGUOUS non-canonical rows, map raw name → canonical slug directly (a name-keyed map is safe
   precisely because those names have exactly one referent).
2. For the 75,432 AMBIGUOUS rows, resolve per `(day, league_id, venue)` shard by reading the parquet's team set and
   matching it against the reference team registry for each candidate league. Require a decisive majority match; leave
   unresolved shards UNTOUCHED and log them (never guess).
3. Snapshot the manifest before any write; the same `_index/snapshots/` mechanism already in use.
4. **GCS path exposure** — `league_id=` is a live Hive partition segment in the raw-tick bucket
   (`.../venue={BM}/league_id={L}/...`) and transitively in the MDPS `processed/` derivation. Canonicalising the
   manifest without relocating the objects would desynchronise path and manifest, so the migration is a **relocation**,
   not a manifest rewrite. Size the object count before committing to an approach.

## Related surface not covered by the shipped fix

The instruments-service per-fixture path (`sports_reference_fixtures.py:224-229`) has an independent instance of the
same defect: the `fx.league.league_id` branch always wins over the numeric-id `elif`, making the id-based resolution
dead code, and `build_league_id()` falls back to a bare slug when `country` is empty. Live evidence of leakage already
on disk: `.../entity=injuries/league=235/` — a bare numeric id sitting as a real partition value. Needs the same
treatment.

## Consumer-breakage survey (2026-07-20) — three design constraints + one live pre-existing bug

A read-only consumer sweep (one agent; the adversarial verifier did not complete — findings below are marked CONFIRMED
where I independently re-measured, REPORTED where they rest on the agent's cited file:line + the codebase's own
comments). These change the migration design, so they gate execution even though the operator has signed off on the
relocation in principle.

**Constraint 1 — the relocation MUST delete the old raw-keyed manifest rows, not just add canonical ones (CONFIRMED).**
The live manifest consolidator dedups on a key that INCLUDES `league_id`
(`unified-trading-library/.../manifest_consolidator.py:525`). Writing canonical-keyed rows via the normal shard path
without removing the old raw-keyed rows makes the consolidator treat old-raw and new-canonical as two distinct groups →
the same shard is **double-counted** in `_index/availability_index.parquet`. The codebase already documents this exact
failure mode: `deployment-service/scripts/rebuild_sports_manifest.py:200-201` — _"Without this, old non-canonical
league_id values persist alongside new canonical ones because the ManifestWriter dedup key includes league_id."_ So the
migration must rewrite-in-place (delete-old + write-new atomically per shard), and reuse that script's
`_clean_stale_league_entries` rather than reinventing it.

**Constraint 2 — a path-only relocation is insufficient; the `league_id` COLUMN inside the parquet must move too
(CONFIRMED).** MDPS derives its OWN output partition from `df["league_id"][0]` — the row-CONTENT column of the raw
ticks, not the GCS path segment (`market-data-processing-service/.../canonical_writer_shaping.py:467`
`_infer_league_id`). So if we `gcs_copy_object` to a canonical path but leave the parquet's `league_id` column raw, MDPS
re-derivation keeps emitting processed output under the OLD raw partition. The relocation must rewrite the content
column, and any already -materialised MDPS `bucketed.parquet` for historical days needs MDPS reprocessing (it is not
touched by an MTDS-only move).

**Constraint 3 — combine with the K1 casing migration (CONFIRMED — same object path).** `league_id=`,
`instrument_type=odds`, and `data_type=trades` are all segments of the SAME ~2M objects. Doing casing and league_id as
separate relocations copies the same objects twice. One combined relocation to the final canonical target halves the
copy and the exposure window. (Cross-ref the K1 ordering correction in the closeout plan: the MDPS scanner's exact
substring match means a dual-accept read must ship BEFORE any of these segments flip.)

**LIVE PRE-EXISTING BUG (independent of the relocation) — coverage gate misclassifies every canonical league (CONFIRMED
by my own measurement).** The sports v2 sentinel calls `is_bookmaker_league_covered(bm, _canon_lid)` with a CANONICAL
league id (`market-tick-data-service/.../sentinels.py:319`), but the coverage registry `BOOKMAKER_LEAGUE_COVERAGE`
(`unified-api-contracts/.../registry/sports_bookmaker_league_coverage.py`) is keyed on RAW display names. Measured
directly: `EPL in values == False`, `PREMIER_LEAGUE in values == True`, and
`is_bookmaker_league_covered("BETFAIR_EX_EU", "EPL") == False` while `…("BETFAIR_EX_EU", "PREMIER_LEAGUE") == True`. So
**every not-yet-captured (bookmaker, canonical-league, fixture) shard on the LIVE write path is currently mis-stamped
`EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`** instead of surfacing as a real gap — a standing false-negative in coverage
reporting TODAY. The fix is to canonicalise that registry (re-run
`refresh_sports_bookmaker_league_coverage_2026_06_21.py` AFTER the manifest is canonical, or regenerate the JSON from
`ODDS_API_DISPLAY_TO_CANONICAL` now). Filed as its own follow-up todo in the closeout plan.

**Ambiguity gap in the existing name→canonical table** — `ODDS_API_DISPLAY_TO_CANONICAL`
(`unified-api-contracts/.../provider_league_ids.py:655-697`) has **no entry for `FIRST_DIVISION_A`** (23,745 rows) and
resolves `Championship`/`Super League` unconditionally to ONE side (English/Swiss), and relies on accent
(`Primera Division` vs `Primera División`) to split Argentina/Chile — a signal the manifest's `upper().replace(" ","_")`
DESTROYS. This corroborates the team-name disambiguation path as the only reliable route for the ambiguous set, and
means the name→canonical table CANNOT be trusted for the six collisions.

Evidence: `scratchpad/ns_coverage.py`, `scratchpad/collisions.py`, `scratchpad/hist_disambig.py`,
`scratchpad/parquet_provenance.py`, `scratchpad/team_disambig.py`; consumer sweep
`subagents/workflows/wf_664f7ed4-df6/journal.jsonl` (2026-07-20).
