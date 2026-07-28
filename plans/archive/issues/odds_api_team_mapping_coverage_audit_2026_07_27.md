---
doc_type: issue
title: odds_api_team_mapping.parquet coverage audit — 59 gaps resolved + confirmed, 72 residual unmappable names
summary: >-
  Coverage census (stride-sampled, 204 days across the 2020-06-06 data floor, 2,193 shard reads) of
  `sports_reference/mappings/odds_api_team_mapping.parquet` against distinct home/away team-name strings actually
  present in MDPS's bucketed-odds shards (`pipeline_mode=batch_mdps_odds_horizon_bucket`). Found 131 distinct gap names.
  Resolved 59 of them with confirmed (not guessed) `af_team_id` identity via the SAME alias resolver the live pipeline
  already uses (`unified_api_contracts...team_mappings.validate_team_resolution`) cross-referenced against
  `team_mapping_v2.parquet`, and applied them to the live table (658 -> 717 rows), including the confirmed 2026-07-14
  gap (`Burgos CF`). The remaining 72 names are genuinely unmappable today (no alias dict entry, or resolved id absent
  from team_mapping_v2) and are left dropping at ml-service merge time, per the plan's own accepted behavior — not
  fabricated.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [sports, odds, team-mapping, coverage-audit, data-correctness]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/archive/issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md,
  ]
created: 2026-07-27
assigned_vm: NA
parent_epic: sports_master
execution_scope: local-only
priority: P3
estimate_class: refactor
source:
  sports_satellite_ao_dispatch_batch3_2026_07_25.md, "Audit instruments-service's odds_api_team_mapping.parquet
  coverage" todo
resolved_by:
  "instruments-service/scripts/odds_api_team_mapping_coverage_audit_2026_07_27.py --apply; mapping table 658->717 rows,
  verified 0 nulls / 0 duplicate keys post-apply; doc's own text: 'No operator decision needed to close this doc' —
  residual 72 unmappable names are the plan's own accepted behavior, not a gap"
locked_by:
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

# odds_api_team_mapping.parquet coverage audit

## What I found (2026-07-27, slot 2, data_engineering)

Ran a read-only coverage census (script:
`instruments-service/scripts/odds_api_team_mapping_coverage_audit_2026_07_27.py`) against MDPS's bucketed-odds shards
(`processed/by_date/day={D}/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/ league_id={L}/timeframe={T}/bucketed.parquet`,
bucket `market-data-tick-sports-prd-central-element-323112`).

**Methodology (honest disclosure — this is a stride SAMPLE, not an exhaustive corpus walk, per the single-walk
discipline)**: sampled every 11th day (a prime step so the sampled weekday rotates) from the 2020-06-06 sports data
floor to today — 204 sample days, 180 with data, 2,193 shard reads (one timeframe file per (day, league) pair, since all
timeframes for a given day+league share the same fixture roster). Team rosters recur weekly within a season, so this
captures the large majority of names used historically without a full 1,941-day walk, but is not guaranteed 100%
exhaustive — a much finer stride would find additional rare gaps at proportionally higher GCS cost.

**Census result**: 734 distinct `home_team`/`away_team` strings observed across the sample; 131 were absent from the
658-row mapping table's `od_team_name` keys (the confirmed 2026-07-14 gap, `Burgos CF`/SEGUNDA_DIVISION, was among them,
confirming the census methodology is sound).

**Resolution (no guessing)**: each gap name was resolved via
`unified_api_contracts.external.api_football.team_mappings.validate_team_resolution(name, provider="odds_api")` — the
SAME alias resolver the live `odds_api_adapter` pipeline already uses to build fixture rows (per
`market-tick-data-service/.../fixture_id_resolver.py`'s own docstring) — to a `canonical_team_id`, then looked up in
`team_mapping_v2.parquet`'s `canonical_team_id -> api_football_id` map (6,245 teams x 5 providers, static reference
file). The `af_league_id` for each new row was taken by an UNAMBIGUOUS majority vote from the ALREADY-mapped teams
observed in the same (day, GCS `league_id`) sample — reusing real existing table data, never invented; when the vote was
ambiguous or no already-mapped team existed in that league sample, the name was left residual rather than guessed.

**Outcome**: 59 distinct names resolved with confirmed identity and applied
(`gs://instruments-store-sports-prd-central-element-323112/sports_reference/mappings/odds_api_team_mapping.parquet`, 658
-> 717 rows, 0 duplicate `od_team_name` keys, 0 null `af_team_id`). `Burgos CF` -> `af_team_id=9580`, `af_league_id=140`
(consistent with the existing table's own established — if division-collapsed — convention for Spanish teams;
`af_league_id` is provenance metadata only, not consumed by the ml-service merge join, which keys solely on
`af_team_id`/`od_team_name`).

**72 names remain genuinely unmappable** (not fabricated — matches the plan's accepted "residual honestly-unmappable
names ... drop at ml-service merge time" outcome):

- 47 raised `TeamResolutionError` — no entry in any alias dict at all (mostly smaller-league / non-English-script names,
  e.g. Austrian second-tier, Greek, and South American club names — confirms the plan's own hypothesis that
  "smaller-league spellings are likely under-covered generally").
- 56 resolved a `canonical_team_id` but that id is absent from `team_mapping_v2.parquet`'s 6,245-team static reference
  (that file itself is incomplete for smaller leagues).
- 27 resolved `af_team_id` but had no unambiguous already-mapped teammate in their GCS league sample to vote an
  `af_league_id` from. (Note: 21 names appear in more than one league-sample context with a mixed resolved/residual
  outcome — a name that resolved successfully in at least one context was applied; the residual count above is
  per-context, not per-name.)

## Why it matters

`odds_api_team_mapping.parquet` gates which odds rows `ml-service`'s `sports_feature_loader` can attach a `fixture_id`
to (`_attach_fixture_ids_to_odds`, `dropna(subset=["home_af","away_af"])`) — an unmapped team name means that team's
odds rows are silently (but honestly, per the existing `logger.warning` + drop, not fabricated) excluded from ML
training data. Closing genuinely-resolvable gaps directly increases usable training coverage for smaller leagues.

## Recommended decision

No operator decision needed to close this doc — the plan's own Done-when explicitly accepts residual unmappable names as
documented behavior, and this audit's resolved set has already been applied. Two optional, non-blocking follow-ups for
whoever next touches this surface (not spawned as their own todos here — genuinely low-priority, no deadline, and NOT
part of this plan's scope):

- The 47 `TeamResolutionError` names are candidates for new `_CROSS_PROVIDER_ALIASES` entries in
  `unified-api-contracts/unified_api_contracts/external/api_football/team_mappings.py` (a human should confirm each
  identity before adding — this doc does not do that, to avoid guessing).
- `team_mapping_v2.parquet` (6,245 teams) appears to have no live writer/builder anywhere in the workspace (grep
  returned zero hits) — if it needs periodic refresh, that is a separate, larger scoping question, out of this audit's
  bounds.

## Evidence

- Script: `instruments-service/scripts/odds_api_team_mapping_coverage_audit_2026_07_27.py` (read-only census + `--apply`
  gap-fill, run 2026-07-27).
- Applied mapping table: 717 rows (was 658), verified via a fresh post-apply read-back (0 nulls, 0 duplicate keys,
  `Burgos CF` present).
