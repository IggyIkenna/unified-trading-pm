---
doc_type: plan
title: MTDS sports odds/trades index-correctness followup — T2.9 schema drift + T2.10 phantom rows
summary: >-
  Forked from sports_legacy_bucket_cutover_2026_07_16.md's Phase 2 (MOVE) findings — the MDT `(sports, odds, trades)`
  schema contract is drifted from the real canonical schema (T2.9), and 47,253 `api_football x trades` phantom
  `captured` rows in the MDT canonical index need a purge decision entangled with the `_legacy_seed.parquet` / OR-4 /
  OR-5b resolution (T2.10).
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    deployment-service,
    market-tick-data-service,
    instruments-service,
    deployment-api,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [migration, manifest, sports, data-correctness, mtds, schema-drift]
related:
  [
    /plans/active/sports_legacy_bucket_cutover_2026_07_16.md,
    /plans/active/sports_legacy_cutover_closeout_tasks_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    "Forked 2026-07-24 from sports_legacy_bucket_cutover_2026_07_16.md via the plan-hygiene line-cap remediation triage
    (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 24, bucket (c))",
  ]
---

# MTDS sports odds/trades index-correctness followup

> **Forked 2026-07-24** from
> [`sports_legacy_bucket_cutover_2026_07_16.md`](/plans/active/sports_legacy_bucket_cutover_2026_07_16.md) via the
> plan-hygiene line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 24, bucket (c))
> — the parent plan's ~2700 lines of completed cutover history stay in place; these were its last 2 open Phase-2 (MOVE)
> todos, moved here **verbatim, unedited**. Todo IDs (T2.9, T2.10) and every cross-reference inside them (T2.5, T2.6,
> T2.7, T3.1, OR-4, OR-5b, R-11, `_legacy_seed.parquet`, etc.) are defined and discussed at length in the parent plan —
> **read it for full context before acting on either todo below**, especially the parent's own updated top-of-file
> banner (as of 2026-07-17) which reports `OR-5b RESOLVED` and the `market-data-tick-sports-central-element-323112`
> bucket already **DELETED**, and separately states _"T2.10 seed phantoms purged (`odds_api` intact)"_ as part of that
> later resolution. **T2.10 in particular may already be stale against that later banner** — the checkbox below is moved
> exactly as it stood at its 2026-07-16/17 authoring point (still unchecked in the source); verify current state on real
> infra before executing rather than assuming the text below is still accurate. This plan does not resolve that
> discrepancy — it is flagged here for whoever picks up T2.10 to check first.

## Codex SSOTs (read before executing)

| SSOT                                                      | Governs                                                                  |
| --------------------------------------------------------- | ------------------------------------------------------------------------ |
| `/codex/02-data/availability-manifest-and-data-status.md` | 4-state `capture_status`; per-VM shards; consolidator contract           |
| `/codex/02-data/honest-absence-downstream-handling.md`    | Phantom vs real absence; never fake `record_captured`                    |
| `/codex/02-data/pipeline-mode-partition.md`               | `{mode}_{source}` segment placement; `source=` crosscutting REQUIRED     |
| `/codex/05-infrastructure/manifest-consolidator-ssot.md`  | Consolidator merge/reap semantics referenced by the T2.10 SLOT-3 finding |

## Todos

- [ ] [DATA] P0. **T2.9 — MDT `(sports, odds, trades)` schema contract is DRIFTED from reality (BIG FINDING, T2.7).**
      _Mechanism_: the registered contract requires
      `ts_event, fixture_id, market_type, outcome, odds_decimal, broker,     client, data_source`; the REAL canonical
      data carries `bm_time, market_key, outcome_name, price, fetch_utc, …`. **Canonical's OWN native live-written
      objects FAIL the same contract** (verified directly, not inferred) — so this is contract-vs-reality drift, not a
      defect in the moved objects. With `_resolve_strict_validation(None)==True`, any caller that validates these cells
      RAISES. Decide: fix the contract to match the real schema, or fix the writers to emit the contracted schema. T2.7
      wrote its 6,110 rows in documented warn-only mode (mismatch LOGGED, row truthfully reflects a crc32c-verified
      object) rather than let a stale contract assert a false absence. _Gate_: contract and real data agree on ≥1 native
      canonical object. _ABORT_: none (analysis).
- [ ] [DATA] P0. **T2.10 — 47,253 phantom `api_football × trades` `captured` rows in the MDT canonical index (BIG
      FINDING, T2.7). Same class as T3.1's 123,149 `api_football × ODDS`, other bucket, no todo owns it.** _Mechanism_:
      canonical MDT holds **ZERO** `batch_api_football` trades objects (only `batch_odds_api` 252,163 + `live_odds_api`
      8), yet the index carries 47,253 `api_football × trades` rows with `capture_status=captured` and **nonzero**
      `instrument_count` — i.e. the index claims captured data no object backs. **5,584 of them are superseded/corrected
      in place by T2.7's MDT shard at T6.1** (same dedup key, corrected `source`/`pipeline_mode`); the remaining
      **~41,669 need a purge decision** mirroring T3.1's predicate (`source=='api_football' AND data_type=='trades'`,
      source filter MANDATORY — `odds_api × trades` 362,746 must survive UNTOUCHED). Related: UAC declares **no
      `('sports','trades')` availability semantic** though `cefi`/`tradfi`/`prediction` all map
      `trades →     tick_timestamp`; registering it blind would switch the availability gate ON for the LIVE MDT sports
      fleet — the exact hazard `57bcc7c5` refused for `PLAYER_STATS` and filed for a ruling. **Feeds OR-5b.** _Gate_: a
      written disposition for all 47,253. _ABORT_: purging without the `source` filter → destroys the real `odds_api`
      population → STOP.

> **🔬 SLOT-3 FINDING 2026-07-17 — T2.10 is NOT a T3.1-style merged-index purge; the seed re-introduces the phantoms.
> STILL BLOCKED (entangled with `_legacy_seed`/OR-4/OR-5b).** Measured directly with DuckDB over fresh downloads of BOTH
> `market-data-tick-sports-prd` `_index` objects: the phantom `api_football × trades`
> captured+nonzero-`instrument_count` rows live in the **live `_index/per_vm/_legacy_seed.parquet` shard** (SEED =
> **37,114**; MERGED-INDEX = **38,329**), and the consolidator re-merges that seed EVERY cycle (index generation was
> seconds-fresh at measurement). ⇒ a merged-index-only rewrite (T3.1's mechanism, which the todo above says to "mirror")
> is **NOT durable** here — the next consolidator cycle re-adds the 37,114 from the seed. This is exactly why T3.1's
> ODDS purge held (`api_football × ODDS` is **0** in BOTH the seed and the merged index — nothing to re-introduce) but a
> trades purge would **silently regress**. The consolidators are ENABLED (Phase 6 done), so there is no QUIET window now
> either. **Durable fix must strip the 37,114 phantom captured-trades rows from the SEED itself** (source filter
> MANDATORY — the seed also holds **211,313** real `odds_api × trades` that must survive), then let the consolidator
> re-merge — i.e. it must be done as part of the `_legacy_seed.parquet` / R-8 / OR-4 resolution, which is the live OR-5b
> investigation and gates the MDT-bucket delete. A merged-index purge alone is a **false-progress trap**. _(Not executed
> — read-only measurement; zero objects mutated.)_

> **⚠️ POSSIBLY MOOT (flagged 2026-07-25, NOT independently re-verified — re-query before dispatch):**
> `issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md` documents a CAS-safe wipe
> (`market-tick-data-service@e9d9dec0`, executed 2026-07-23,
> `scripts/sports/wipe_api_football_sports_manifest_2026_07_23.py`) that removed **ALL 1,266,874** `source=api_football`
> rows from this exact `market-data-tick-sports-prd` manifest (filtered on `source` alone, VERIFY PASSED 0 remaining) —
> this necessarily includes T2.10's `api_football × trades` subset. Before executing T2.10, re-query the current
> manifest for `source=api_football AND data_type=trades`; if 0 remain, close T2.10 citing that wipe instead of
> re-running the purge. **Caveat carried forward from the SLOT-3 finding above**: the wipe doc's evidence describes the
> merged/index-level state — confirm the `_legacy_seed.parquet` shard specifically was also covered (not just the merged
> index) before declaring this fully resolved, since a seed-only respawn is exactly the failure mode SLOT-3 warned
> about.

## Sibling plan

Forked alongside
[`sports_legacy_cutover_closeout_tasks_2026_07_24.md`](/plans/active/sports_legacy_cutover_closeout_tasks_2026_07_24.md)
(the other disjoint open-item group carved out of the same parent in the same remediation pass).
