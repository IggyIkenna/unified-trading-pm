---
doc_type: plan
title: Sports taxonomy P2 — migrate GCS + manifest to the canonical venue/data_type/horizon model
summary: >-
  Phase 2 of the sports canonicalisation chain — the data migration that makes the P1 contracts true on disk. Re-stamps
  the largest population in the sports estate (375,257 `trades` shards over 6 years → `odds`), lowercases the whole
  19-token instruments-service reference vocabulary, purges the retired `exchange_odds`/`fixed_odds` instrument_type
  values from both manifest rows and GCS objects, removes ODDS_API/FOOTYSTATS from the venue axis, and cleans the
  phantom populations the audit found (20,785 KALSHI cross-AG rows, 2,490 blank-venue IS rows, 111 `trades_inplay`
  fossils). GATED on BOTH P1's contracts AND the in-flight API-Football entity campaign — renaming the registry while
  that campaign's two remaining all-leagues backfills are running would make the fetch loop write tokens the registry no
  longer expects. Prod deletes run agent-autonomously via the delete-safety §3a reversibility path (fresh same-run
  soft-delete-retention check), per operator ruling 2026-08-08 — NOT via [OPERATOR] tags.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [sports, migration, canonicalisation, gcs, manifest, re-stamp, delete-safety, reversibility-qualified]
related:
  [
    /plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/sports_taxonomy_p4_backfill_2026_08_08.md,
    /plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p1_capture_and_contracts_2026_08_08, sports_af_full_entity_completion_2026_08_03]
gate_on_depends: true
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    market-tick-data-service/scripts/sports/restamp_sports_bookmaker_venue_2026_07_27.py,
  ]
source: ["sports venue/data-type audit, 2026-08-08 interactive session — 27 operator rulings"]
locked_by:
locked_since:
---

# Sports taxonomy P2 — the data migration

> **🔴 DOUBLE-GATED.** `gate_on_depends: true` on BOTH
> `/plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md` (contracts must exist first) AND
> `/plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md` (the in-flight API-Football campaign
> must converge first). That second gate is not optional — see below.

## Why the API-Football gate exists

`sports_af_full_entity_completion_2026_08_03.md` is `assigned_vm: planning`, `sequential: true`, running now, with 3
open todos: launch `FIXTURE_LINEUPS` all-leagues backfill (58,523 shards), launch `INJURIES` all-leagues backfill
(62,709 shards), and a P0 re-census of all 8 in-scope entities before it can close.

All three write and measure shards keyed on the UPPERCASE IS tokens this phase lowercases. Renaming the registry
mid-flight would make the fetch loop write a token the registry no longer expects — minting phantom
`expected_unattempted` rows — and would leave that doc's P0 re-census measuring the pre-rename axis. Letting it converge
first means this migration makes ONE pass over a finished corpus. A cross-plan banner recording this ordering was added
to that doc 2026-08-08 (`unified-trading-pm@3bb3214bdf`).

## Delete posture — §3a, not [OPERATOR]

Operator ruling 2026-08-08: **AO-dispatched, no operator step on deletes.** This is implementable via
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (2026-07-26, extended 2026-07-28): an agent may execute
a prod delete itself, with no human step, once a **FRESH, same-run** `gcs_bucket_soft_delete_retention_seconds(bucket)`
check returns **≥ 604800** (7 days). The codex records every `-prd-` GCP bucket at 604800 with 0 gaps at audit time.

**Every delete/purge todo below therefore carries that fresh check as an in-run precondition.** Fresh means queried in
the same execution as the delete — never assumed, never carried over from a prior run or from this plan's text. If a
bucket's check returns < 604800, that delete falls back to approve-executes and the todo must stop and say so rather
than proceeding.

---

## Todos

### Consumer enumeration (must complete before any re-stamp)

- [ ] [REVIEW] P0. **Enumerate every consumer of each token being renamed, per the P1-authored codex rename rule.**
      Minimum surfaces to enumerate — do NOT stop at a grep, READ each candidate consumer (features-service reads
      bucketed odds by PATH PREFIX, not by data_type column, so a data_type grep will miss it): MTDS writers + rebuild
      scripts, MDPS `canonical_writer`/`canonical_writer_shaping`, IS producers + `enumerate_expected_universe.py`,
      features-service `sports_feature_loader._ODDS_BUCKETED_PREFIXES`, ml-service sports loaders, deployment-api
      distinct-values + data-status, and the honest-coverage measurer. Output a checked-in consumer inventory; the
      re-stamp todos below cite it. **This todo gates every todo in the next section.**

### The re-stamps (each is a four-surface change — path, parquet content, manifest row, catalogue render)

- [ ] [DATA] P0. **Re-stamp `trades` → `odds` across 375,257 shards (2020-06-06 → present).** Largest population in the
      estate. Both the GCS path segment `data_type=trades` and the manifest `data_type` column must move together —
      path==manifest on data_type is the standing MDPS contract. Run in-region on a VM per the VM-launcher runbook,
      never locally; SPOT with progress-checkpoint resume (never replay from START_DATE on preemption). Verify with a
      MEASURED count of target artifacts created, entity-scoped, on `time_created` — not an activity check.
- [ ] [DATA] P0. **Materialise the `in_play` column and retire `trades_inplay`.** 111 rows only (2022-09-07 →
      2022-11-09, blank venue) — a fossil, not a population. **Disposition rule PRE-SPECIFIED**: fold into `odds` with
      `in_play=true` when the backing object exists AND its parquet has `row_count > 0`; delete the manifest row when
      the object is absent or empty (bookkeeping residue). Report the split. Confirm the filename-scoped reader
      (`reprocess_sports_odds.py::_is_consumable_trades_blob` matches on FILENAME `inplay_ticks.parquet`) is updated in
      the same change — this is exactly the consumer a data_type grep misses.
- [ ] [DATA] P0. **Lowercase the instruments-service reference vocabulary** across all 19 tokens (`FIXTURES`,
      `FIXTURES_OUTCOMES`, `FIXTURES_SCHEDULE`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`, `FIXTURE_STATS`, `INJURIES`,
      `MATCHES`, `ODDS`, `PLAYER_STATS`, `PLAYER_VALUES`, `PREDICTIONS`, `SFI_PROGRESSIVE_STATS`, `STANDINGS`, `TEAMS`,
      `WEATHER`, `XG`, `XG_SHOTS`, `ODDS_HORIZON_BUCKET`). Only after the API-Football campaign has converged (the
      `gate_on_depends` above enforces this, but re-verify at run time — a gate is not a substitute for looking).
- [ ] [DATA] P0. **Fold footystats `ODDS` (6,306 captured) + `odds` (16,207 captured) into a single `odds`.** These are
      the same vendor population under two spellings; `source=footystats` remains the discriminator against the odds_api
      population. Note the UAC comment calling the uppercase set "4 stale empty rows" is FALSE — expect 6,306 real
      shards.
- [ ] [DATA] P0. **Move `odds_horizon_bucket` (135,980 shards) onto the `odds` + `horizon` model.** Three writers emit
      it today (MDPS 121,762 / MTDS 14,656 / IS 1,106) at two different grains — 123,642 attributed to venue=ODDS_API
      plus ~12,000 spread per-bookmaker. Re-attribute to the correct per-bookmaker venue and collapse the double-count;
      state the resulting single grain explicitly.
- [ ] [DATA] P1. **Re-attribute the ODDS_API and FOOTYSTATS venue rows.** ODDS_API's 123,642 `odds_horizon_bucket` + 8
      `trades` and FOOTYSTATS' 22,513 rows must move to `source` with a real per-bookmaker `venue`, or be classified as
      genuinely source-grain rows that need a different home. Do not silently drop them.

### The purges (each requires the §3a fresh check, in-run)

- [ ] [DATA] P0. **Purge the retired `exchange_odds` / `fixed_odds` instrument_type values from manifest rows AND GCS
      objects** (operator ruling 2026-08-08: "derive from venue, retire the split, purge the unnecessary values for
      manifest and objects"). 60,095 shards carry them (`exchange_odds` 35,622 / `fixed_odds` 24,473); `instrument_type`
      is a PATH segment so objects move, not just rows. Note the fork is currently split WITHIN venues — BETFAIR_EX_UK
      has 9,204 `exchange_odds` AND 3,405 pre-fork `odds` — so a partial purge would leave the same venue across two
      tokens; the end state must be ONE token per venue. **§3a fresh check required before any object delete.**
- [ ] [DATA] P0. **Delete the 20,785 KALSHI `empty_confirmed` rows** (source `polymarket_clob`, 2020-06-06 → 2026-05-21)
      from the sports manifest — prediction-market venues seeded into the sports denominator, ~3.4% of the manifest
      being fictitious. Manifest-only; confirm zero backing GCS objects first (if any exist, that is a different and
      larger finding — file it, do not delete). **§3a fresh check required if any object delete is involved.**
- [ ] [DATA] P1. **Delete the 2,490 blank-venue rows** written by instruments-service into the MTDS tick manifest, once
      P1's writer fix has stopped the source. Verify the writer is genuinely fixed before cleanup — cleaning before the
      writer stops just re-pollutes.
- [ ] [DATA] P1. **Delete the `SPORT` instrument_type residue** (8 rows on ODDS_API's `trades`) — junk token, no backing
      model.
- [ ] [DATA] P1. **Sweep the `league=` vs `league_id=` path duplication.** Measured on day=2020-06-06: the same
      FOOTYSTATS shard exists under BOTH `league=BUNDESLIGA/ticks_migrated_*.parquet` AND
      `league_id=BUNDESLIGA/ticks.parquet`. Determine which is canonical (`league_id=` per the path SSOT), census the
      full extent — do NOT assume one day generalises — and purge the non-canonical side. **§3a fresh check required.**

### Added 2026-08-08 (operator, mid-flight) — re-stamp the collapsed derived types

- [ ] [DATA] P0. **Re-stamp `odds_snapshot` (16,521) + `odds_movement` (16,470) onto `data_type=odds` + `timeframe`**,
      per P1's collapse todo. These rows ALREADY carry the grain in `timeframe` (15m/1h), so the re-stamp is dropping a
      redundant data_type token, not inventing an axis — measured live 2026-08-08. Only ~33k shards over 13 days
      (2026-07-25 → 08-06), so this is small NOW and grows with every day P4's backfill adds: doing it before the
      backfill is materially cheaper than after. Both the GCS path segment and the manifest column move together
      (path==manifest on data_type).
- [ ] [REVIEW] P1. **Assert the sports data_type vocabulary has actually collapsed.** Post-migration the sports manifest
      should carry ONE raw type (`odds`) plus the `timeframe`/`horizon`/`in_play` axes — down from the 10 distinct
      data_types the 2026-08-08 audit measured. Report the final distinct set; any surviving derived data_type name is
      an incomplete migration, not an accepted exception.

### Verification

- [ ] [REVIEW] P0. **Four-surface reconciliation after the migration**, per
      `/codex/02-data/four-surface-reconciliation-procedure.md`: GCS object path ↔ parquet content columns ↔ manifest
      shard-atom key ↔ catalogue/data-status render. Use the UAC `canonical_path_violations()` MACHINE ORACLE, never a
      re-implemented rule — and remember it is PATH-STRUCTURE-ONLY and VALUE-BLIND, so check id-form and the
      `instrument_type`/`data_type`/`venue` VALUES separately or state explicitly that they were not checked.
- [ ] [REVIEW] P0. **Assert the accepted-exception sets have genuinely SHRUNK, not been re-populated.** Success
      criterion for this whole chain: `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS`,
      `SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED` and `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` all reach EMPTY. A
      green panel achieved by adding exceptions is the exact failure mode this chain exists to undo — if any set grew,
      the migration is wrong, not the panel.
- [ ] [REVIEW] P1. **Re-run the honest-coverage measurer and confirm the rollup's distinct values equal the manifest's**
      (31 venues / 10 data types today → the canonical set, with nothing hidden). This is the end-to-end proof that the
      panel and the data finally agree.

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — §3a reversibility path governs every delete here.
- `/codex/02-data/four-surface-reconciliation-procedure.md` — the verification procedure + the oracle's blind spots.
- `/codex/02-data/availability-manifest-and-data-status.md` — shard atom identical across
  writer/manifest/status/gate/UI.
- `/codex/05-infrastructure/vm-launcher-runbook.md` — heavy I/O never runs locally; SPOT + progress-checkpoint resume.
- `/codex/05-infrastructure/gcs-object-operations.md` — UTL `gcs_copy_object`/`gcs_delete_object`, never subprocess
  gsutil.

## Progress Log

- **2026-08-08** — Authored. Double-gate on P1 + the API-Football campaign set at authoring time; protective cross-plan
  banner already landed on that campaign (`unified-trading-pm@3bb3214bdf`). Delete posture set to §3a
  reversibility-qualified per operator ruling, NOT [OPERATOR] tags.
