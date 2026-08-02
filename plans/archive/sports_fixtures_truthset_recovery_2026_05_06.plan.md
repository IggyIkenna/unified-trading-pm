---
doc_type: plan
title: sports-fixtures-truthset-recovery-2026-05-06
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    instruments-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-06"
overview:
  Use api_football per-(league, season) enumeration as the truth-set to detect (a) league-mapping breakage — leagues
  that exist but were never fetched — and (b) phantom-write-on-fixture-day cases — dates that DO have fixtures per
  api_football but were silently recorded as empty/failed/zero-row in our manifest. Then targeted-fetch the diff. Then
  run downstream chain. Honest coverage end-to-end.
type: code
epic: epic-sports-honest-coverage
locked_by: live-defi-rollout
locked_since: 2026-05-06
companion_plan: sports_phantom_fixtures_recovery_2026_05_06.md
supersedes_phases:
  [
    sports_phantom_fixtures_recovery_2026_05_06.md § relaunch-fixtures-backfill-category-a (replaced — VM-based re-fetch
    was the wrong shape),
    sports_phantom_fixtures_recovery_2026_05_06.md § audit-and-flip-stale-empties (replaced — this plan is a stronger
    version),
  ]
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: instruments-service, code: C5, deployment: none, business: none }
  - { repo: deployment-service, code: C0, deployment: none, business: none }
depends_on: [sports_phantom_fixtures_recovery_2026_05_06.md]
---

## Deferred work — migrated to: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`,

`plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` — successor:
data_completion_to_100_all_ag_2026_06_21, sports_pipeline_to_100pct_golden_window_first_2026_06_27 (the AF-enrichment
downstream-chain/drift-audit/spot-check cluster is superseded by the golden-window plan's Gate-ALL-PASS backfill
[af-backfill-20260627-182057, 2903/2904 shards resolved]; the orchestrator-bug re-smoke/unit-test/e2e-smoke cluster is
STALE — the per-league empty-loop pattern is now implemented + tested across all sports adapter modules; the Phase-5
UI-verification + backup-blob-cleanup items are superseded by the 2026-07-21 2020-06 data-floor wipe, which covers most
of this plan's original recovery window. NOTE: `locked_by: live-defi-rollout` was never cleared at archival — flagged
for operator `[unlock-plan]` cleanup.)

# Sports FIXTURES truth-set recovery — 2026-05-06

## Why this plan exists

After multi-iteration phantom-recovery work, the user surfaced TWO concerns the prior approach didn't address:

1. **League-mapping breakage**: if `canonical_league_id → af_league_id` mapping was missing/broken for some leagues at
   the time of original capture, the orchestrator never called api_football for them, URDI never captured them, and our
   manifest now incorrectly records them as `empty_confirmed` (= "no fixtures, honest absence" — but actually wrong,
   fixtures existed in api_football, we just couldn't find them).

2. **Phantom-write on fixture-days**: the original `manifest.add(row_count=0)` bug fired even on dates where fixtures
   DID exist. The orchestrator wrote 0 rows somewhere mid-flow even when api_football returned data. URDI then has an
   empty/wrong parquet for that day. VM-based manifest reconciliation reading URDI for that day finds the empty parquet
   → marks `empty_confirmed`. Same wrong outcome.

**Neither concern is detectable without asking api_football directly.** The prior FIXTURES backfill VMs
(af-backfill-20260506-122705 / -124157 / -125413 / -130727 / -131302 / -135454, all killed) trusted URDI/disk and just
reconciled manifest rows. They did not call api_football and so could not detect mapping or phantom-write gaps.

This plan ships the smart audit: 1 api_football call per (league, season) ≈ 960 calls total ≈ 3h of Pro-tier quota →
produces a truth-set we then diff against current manifest → targeted re-fetch only the diff → downstream chain only for
fixtures we now know are real.

## What's already in place from prior work (DO NOT redo)

| Component                                                                                                 | Commit                        | Status                                                 |
| --------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------ |
| Writer fix (root cause) — `manifest.add(row_count=0)` → `record_empty(row_key=...)` for zero-fixture days | instruments-service `f36651c` | ✅ shipped                                             |
| `flip_phantom_fixtures_zero_rows.py` (initial flip — wrong, wrote `empty_confirmed`)                      | instruments-service `962982e` | ✅ shipped, then superseded                            |
| `flip_phantom_to_attempted_failed.py` (corrective re-flip)                                                | instruments-service `2821111` | ✅ shipped, then superseded                            |
| `write_phantom_reflip_per_vm_shard.py` (per-VM mirror)                                                    | instruments-service `2d18d0d` | ✅ shipped                                             |
| `delete_phantom_rows_from_shards.py` (DELETE 176k phantom rows)                                           | instruments-service `73be000` | ✅ shipped + production --apply done 2026-05-06 13:07Z |
| Orchestrator pre-flight patch (defer to per-entity handlers for sports per-league)                        | instruments-service `d73565a` | ✅ shipped + tarball refreshed                         |
| Launcher OOM fix (default e2-standard-4 + MACHINE_TYPE override)                                          | deployment-service `b7c5d8e`  | ✅ shipped                                             |
| Chain runner script for sequential downstream entity backfills                                            | deployment-service `5be53a7`  | ✅ shipped                                             |
| Consolidator memory fix (4 CPU + 16Gi via TF)                                                             | deployment-service `3e3edcc`  | ✅ shipped + applied                                   |

**Live state at handover (2026-05-06 ~14:15 UTC):**

- All FIXTURES backfill VMs (`af-backfill-20260506-*`) **killed**. None running.
- Sports manifest backups retained at
  `gs://instruments-store-sports-central-element-323112/_index/availability_index.20260506-{111222,112347}.bak.parquet` +
  10 per-VM `.20260506-120021.bak.parquet` siblings. **Do not delete** until this plan completes + verifies.
- Canonical manifest fresh (mtime updates every ~1 min via the now-working consolidator).
- Manifest current state: 100k+ phantom (date, league) FIXTURES rows DELETED entirely (orchestrator sees as missing).
  75k cap-zero per-fixture downstream rows DELETED.
- 119 leagues affected per the phantom audit. ~3041 dates per league.
- footystats backfill VM `fs-backfill-20260506-083546` still running (different source, different quota — **not
  competing**).

## Architecture

```
Phase 1: Smart audit (writes truth-set + diff to GCS)
        │
        ▼
Phase 2: Targeted FIXTURES recovery (writes per-(date, league) fixture parquets +
         correct manifest captured rows; uses truth-set data — minimal extra API calls)
        │
        ▼
Phase 3: Downstream chain (PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS /
         FIXTURE_LINEUPS / INJURIES) for the recovered fixtures
        │
        ▼
Phase 4: Drift audit (cross-check residual ~223k empty_confirmed rows on
         per-fixture entities vs new FIXTURES truth)
        │
        ▼
Phase 5: deployment-UI verification (turbo cache clear + screenshot)
```

## Phase 1 — Smart audit (~30-60 min implementation, ~3h runtime)

Build `instruments-service/scripts/audit_fixtures_via_api_football.py`.

### Inputs

- UAC `canonical → api_football` league-id mapping (lives in
  `unified-api-contracts/unified_api_contracts/sports/api_football_ids.py` or similar — confirm exact module). The 119
  affected leagues from the phantom audit.
- Season range: 2018-01-01 → 2026-05-04 (approximately seasons 2017 through 2026; api_football's "season=YYYY"
  represents the START year of European leagues' Aug-May seasons, calendar year for Brazilian/Japanese/MLS).
- api_football API key from Secret Manager (existing UTL ApiKeyReloader pattern; reuse from the orchestrator's adapter).

### Logic

1. Read canonical league set + active af_league_id mapping. **Flag any canonical leagues with no mapping** (these are
   the mapping-breakage cases — unable to fetch, mark for operator follow-up).
2. For each (canonical_league_id, season_year) where mapping exists:
   - Call `GET /fixtures?league={af_id}&season={year}`
   - Parse response → list of fixtures with `fixture_id`, `date`, `home_team`, `away_team`, scores, status.
   - Persist fixtures into in-memory dict: `truth_set[canonical_league_id][season_year] = list[fixture]`.
3. Also persist the truth-set to GCS at
   `gs://instruments-store-sports-central-element-323112/_audits/fixtures_truthset_2026_05_06_{run_ts}.parquet` with
   columns: `canonical_league_id`, `af_league_id`, `season`, `date`, `af_fixture_id`, `status_short`, `home_score`,
   `away_score`. This is reusable by Phase 2 to avoid re-calling api_football for the same (league, season).
4. Read current canonical manifest. For each (date, canonical_league_id) in truth-set:
   - Look up the manifest row keyed by `(date=date, data_type='FIXTURES', league_id=canonical_league_id)`.
   - Classify:
     - **truth_present + manifest_captured + ic > 0** → CORRECT (skip, no action).
     - **truth_present + manifest_empty_confirmed** → SILENT-DROP (truth says fixtures exist, manifest says no). Flag
       for re-fetch.
     - **truth_present + manifest_attempted_failed** → RETRY (failed before). Flag for re-fetch.
     - **truth_present + manifest_missing (no row)** → MISSING (the DELETE'd phantom set OR mapping-broke-set). Flag for
       re-fetch.
     - **truth_absent + manifest_empty_confirmed** → CORRECT (honestly empty).
     - **truth_absent + manifest_captured + ic > 0** → STRANGE (we have fixtures but api_football doesn't). Flag for
       operator inspection (probably stale data from before api_football retired a league/fixture; rare).
5. Output two artifacts:
   - **Diff CSV** at `gs://...//_audits/fixtures_diff_{run_ts}.csv`: one row per (date, canonical_league_id,
     classification, ic_in_manifest, fixtures_in_truth). Operator inspects.
   - **Recovery list parquet** at `gs://...//_audits/fixtures_recovery_set_{run_ts}.parquet`: filtered to SILENT-DROP +
     RETRY + MISSING. Used by Phase 2.

### Cost + safety

- ~960 api_football calls total (120 leagues × 8 seasons). Pro-tier rate ≈ 7,500/day → ~3h to complete.
- Idempotent — re-running produces the same truth-set + diff. Output paths timestamped so multiple runs don't clobber.
- Read-only on the manifest. Phase 2 does the writes.
- **Singleton-locked**: refuse to launch if another `af-` prefix VM is running (api_football per-key rate limit). Use
  the existing `launch-api-football-backfill-vm.sh` singleton-lock pattern.

### Run mode

Run on a same-region GCE VM via a new launcher `deployment-service/scripts/vm/launch-fixtures-truthset-audit-vm.sh`
mirroring `launch-api-football-backfill-vm.sh` (e2-standard-4, asia-northeast1-c). Or invoke from a long-lived shell
with the existing tarball setup. **Apply the no-fire-and-forget rule**: 90s STARTED check, periodic progress polling,
STOPPED-or-FAILED at exit.

## Phase 2 — Targeted FIXTURES recovery

Build `instruments-service/scripts/recover_fixtures_from_truthset.py`.

### Inputs

- The recovery-set parquet from Phase 1.
- The truth-set parquet (provides the actual fixture records — no extra api_football calls needed for these).

### Logic

1. Read recovery-set: list of (date, canonical_league_id) pairs to fix.
2. For each pair:
   - Pull the fixture list for that (date, league) from the truth-set parquet.
   - **No api_football call needed** — the truth-set already has the records.
   - Construct the canonical fixtures parquet content (32-column shape — see existing fixtures parquet at
     `sports_reference/by_date/day=2020-06-06/entity=fixtures/fixtures.parquet` for reference).
   - Write to `sports_reference/by_date/day={date}/entity=fixtures/league={canonical_league_id}/fixtures.parquet`.
     (Verify exact path layout against UAC `candidate_parquet_paths` for FIXTURES — sports has per-league
     sub-partitioning; the existing day-level fixtures.parquet bundles all leagues.)
   - **Decision pending**: do we write per-league sub-partitioned parquets, OR do we re-write the day-level bundled
     fixtures.parquet (replacing the existing one)? The shard-key matrix says sports is
     `(asset_group=sports, source, data_type, league_id, fixture_id, day)` — per-league or per-fixture. Day-level
     bundles are legacy. Operator decides; default to per-league sub-partition since the manifest already keys by
     league_id.
   - Write manifest row:
     `record_captured(row_key={date, data_type=FIXTURES, league_id, venue=API_FOOTBALL}, instrument_count=len(fixtures))`.
3. After all writes, run `flush_all_live_writers()` to persist per-VM shard.
4. Trigger the consolidator (or wait for next cron tick) to roll into canonical.

### Cost

- Zero api_football calls (uses truth-set from Phase 1).
- GCS writes: ~thousands of small parquets + manifest rows. Cost negligible.
- ~30 min to write + 1-2h runtime.

## Phase 3 — Downstream chain

After Phase 2 completes the FIXTURES truth-set is correctly populated in the manifest. Now run the existing chain runner
shipped 2026-05-06 (deployment-service `5be53a7`):

```bash
tmux new-session -d -s phantom-chain bash deployment-service/scripts/vm/run-sports-phantom-downstream-chain.sh \
    --start-date 2020-06-06 --end-date 2026-05-04
```

This launches 5 sequential VMs (one per entity: PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS /
INJURIES). Each enumerates fixtures from the now-correct manifest and per-fixture fetches from api_football. ~30-60 min
per entity, ~3-5h total.

Cost: ~50k api_football calls (10k real fixtures × 5 entities, but many entities share the per-fixture call).

## Phase 4 — Drift audit (post-Phase 3)

For each per-fixture entity (PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES):

- Filter manifest to `capture_status IN ('empty_confirmed', 'attempted_failed')`.
- Cross-reference (date, league_id) against the now-correct FIXTURES manifest. If FIXTURES says fixtures-exist for that
  (date, league) but the per-fixture entity's row says empty/failed → flip to `attempted_failed` so orchestrator
  re-fetches.

Pattern mirrors the existing `flip_phantom_*` scripts. ~30 min implementation.

## Phase 5 — UI verification

- `curl -X POST http://localhost:8004/api/data-status/turbo/clear`
- Open deployment-UI, drill to SPORTS data-status tab.
- Expect:
  - FIXTURES coverage rises for every Cat A league (AUSTRIAN_BUNDESLIGA / GREEK_SUPER_LEAGUE / EPL / SERIE_A / etc.)
    from 0%-real to genuine match-day count.
  - PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES match the FIXTURES coverage shape.
  - Cat B leagues (POLAND_I_LIGA / J2_LEAGUE / cups) stay low coverage with HONEST `empty_confirmed` rows (not
    phantoms).
- Take a screenshot for the session log.

## Todos

- [x] [AGENT] P0. Implement Phase 1 audit script. ~30-60 min. **Shipped instruments-service `58b71fe` 2026-05-06.**
- [x] [AGENT] P0. Smoke test on 1 league x 1 season (e.g., EPL x 2024). Verify truth-set has expected fixtures. **Done —
      EPL 2024 returned 380 fixtures (20 teams x 38 matchdays = expected).**
- [x] [AGENT] P0. Build VM launcher `launch-fixtures-truthset-audit-vm.sh` + widen api-football-backfill singleton lock
      to catch `af-audit-` + register prefix in `vm_zombie_watchdog.py`. **Shipped deployment-service `c23d4a9`
      2026-05-06.**
- [x] [AGENT] P0. Phase 1 audit run completed on `af-audit-20260506-163544`. Truth-set + diff + recovery-set written to
      `_audits/*_20260506-153914.{parquet,csv}`. **182,263 truth-set rows; 39,429 recovery-set rows (RETRY=26,893 +
      SILENT_DROP=11,526 + MISSING=1,010); 0 mapping-breakage cases.**
- [x] [AGENT] P0. Implement Phase 2 recovery script `recover_fixtures_from_truthset.py`. **Shipped instruments-service
      `bfc4893` (initial) + `36aefed` (refactor flip-empty to per-VM shard).**
- [x] [AGENT] P0. Build Phase 2 launcher `launch-fixtures-recovery-vm.sh` + register `af-recover-` in watchdog dict.
      **Shipped deployment-service `326bb84`.**
- [x] [AGENT] P0. Phase 2 recovery run completed on `af-recover-20260506-175258`. **34,583 days written / 112,192
      fixtures recovered across 423 (league, season) pairs in ~37 min, 0 failed pairs. 69,149 ATTEMPTED_FAILED_NO_TRUTH
      rows flipped to empty_confirmed via per-VM shard.**
- [x] [AGENT] P1. UTL fix: consolidator now reads `consolidator_run_at` GCS metadata marker instead of `blob.updated`
      for the incremental-merge cutoff. **Shipped UTL `0ab7432a` 2026-05-06. Closes the silent-skip bug where
      out-of-band canonical writes invalidated the cutoff. 4 new tests added.** Reference incident: recovery shard at
      17:33:23 UTC was skipped on every consolidator cycle for 2+h after the original flip-empty step bumped canonical
      mtime to 17:33:36 UTC; manual mtime-bump on the recovery shard unblocked the merge.
- [x] [AGENT] P1. Verified canonical reflects recovery: 34,583 FIXTURES rows with `venue=API_FOOTBALL`
      `capture_status=captured` now in canonical (captured FIXTURES count: 29,273 → 63,856). Spot-check on ALLSVENSKAN
      2018-04-01 confirms 4 real fixtures with full 32-column schema + correct `data_available_at = kickoff − 7d`.
- [ ] [HUMAN] P0. Operator triggers Phase 3 chain runner via:
      `tmux new-session -d -s phantom-chain bash deployment-service/scripts/vm/run-sports-phantom-downstream-chain.sh     --start-date 2020-06-06 --end-date 2026-05-04`.
      Runs PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES sequentially against the
      now-correct FIXTURES manifest. ~3-5h total.
- [ ] [AGENT] P1. Implement + run Phase 4 drift audit (cross-check residual `empty_confirmed` rows on per-fixture
      entities vs the now-correct FIXTURES truth — flag any gaps to `attempted_failed` for re-fetch).
- [ ] [HUMAN] P1. Phase 5 UI verification — clear deployment-api turbo cache + open SPORTS data-status.
- [ ] [HUMAN] P1. After verification, delete the manifest backup blobs (`*.bak.parquet`).

## Critical reads before starting

- `unified-trading-pm/cursor-configs/CLAUDE.md` — workspace rules + Shard-granularity SSOT + No-fire-and-forget VM
  launches + Manifest concurrency + Sports source coverage windows + Honest absence vs fake placeholders.
- `unified-trading-pm/plans/active/sports_phantom_fixtures_recovery_2026_05_06.md` — full phantom recovery history (this
  plan supersedes 2 of its phases).
- `unified-trading-pm/plans/archive/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` — coordinate with the
  parallel architectural stream; sports per-league shard atom is
  `(asset_group=sports, source, data_type, league_id, fixture_id, day)`.
- Memory: `project_sports_phantom_fixtures_recovery_2026_05_06.md` — session log of the phantom recovery.
- Memory: `feedback_orchestrator_freshness_per_league_granularity.md` — the freshness-check-too-coarse finding (now
  patched in instruments-service `d73565a`).
- Memory: `feedback_check_shard_freshness_ignores_capture_status.md` — UTL freshness ignores capture_status.
- Memory: `feedback_manifest_reader_staleness_per_vm_fallback.md` — 120s mtime threshold gotcha.

## Key files to reuse

- `unified-api-contracts/unified_api_contracts/sports/` — canonical league IDs, source coverage windows, candidate
  parquet paths.
- `instruments-service/instruments_service/adapters/api_football/` — existing api_football adapter (handles auth + rate
  limiting). **Reuse, do NOT re-implement.**
- `instruments-service/scripts/flip_phantom_to_attempted_failed.py` — pattern for one-shot manifest mutation scripts.
- `instruments-service/scripts/delete_phantom_rows_from_shards.py` — pattern for canonical + per-VM shard mutation.
- `unified-trading-library/unified_trading_library/manifest_writer.py` — `ManifestWriter`, `record_captured`,
  `record_empty`, `record_failed`. Use `per_vm_shards=True` for fresh shards.

## Anti-patterns to avoid

- **Don't trust URDI/disk as ground truth.** That's exactly what VM v6 did wrong. The whole point of this plan is to use
  api_football as ground truth.
- **Don't write to canonical manifest directly without also writing a per-VM shard** — the 120s reader staleness gotcha
  (see feedback memo). Use ManifestWriter API.
- **Don't pass --force to the orchestrator and call it done** — that's 254k api_football calls vs. our targeted ~5-10k.
  Wasteful.
- **Don't re-implement api_football auth / rate limiting** — reuse the existing adapter with ApiKeyReloader.
- **Don't kill the running fs-backfill VM** — it's footystats (different source, different quota), not competing with
  api_football.
- **Don't delete manifest backup blobs (`*.bak.parquet`)** until Phase 5 verification confirms the recovery is correct.

## Verification

After Phase 5:

- Run `python -c "from google.cloud import storage; ..."` to spot-check a few leagues:
  - AUSTRIAN_BUNDESLIGA 2024 — should have ~36 captured FIXTURES rows (one per match-day).
  - EPL 2024 — should have ~38 captured FIXTURES rows.
  - POLAND_I_LIGA 2024 — should have either real captures (if api_football covers it) or all empty_confirmed (if it's
    Cat B tier-limited).
- deployment-UI SPORTS coverage at the data-type level: FIXTURES + 5 per-fixture downstreams should all show similar %
  coverage (the shape after recovery should be consistent across the 6 entities for any given league).
- Manifest sanity: zero rows with
  `capture_status='captured' AND data_type IN sports_data_types AND instrument_count == 0`.

## Absorbed from sibling plans (2026-05-06)

Items folded in from `apifootball_enrichment_historical_backfill_2026_04_21` (since archived). The truthset cluster
absorbs api_football enrichment verification because both rely on the same api_football direct-call truth-set:

- [ ] [AGENT] P0. Monitor + rescan + audit. Verify the detached chain orchestrator completes and the manifest reflects
      api_football enrichment correctly (was in-progress at orchestrator handoff per the source plan).
- [ ] [AGENT] P0. Query deployment-api data-status endpoint. Confirm SPORTS category attempted ≥ 50%, captured ≥ 45%.
- [ ] [AGENT] P0. Spot-check 3 random dates per entity (INJURIES / FIXTURE_STATS / FIXTURE_LINEUPS / PLAYER_STATS /
      FIXTURE_EVENTS) for data quality: row counts plausible, fields populated.

Items folded in from `instruments_service_orchestrator_reliability_fixes_2026_04_21` (since archived). 6 open Phase 5/6
todos for AF enrichment per-league empty-loop pattern + smoke verification — overlaps the truthset recovery's same 5+1
entities and same root-cause (`manifest.add(row_count=0)` vs `record_empty(row_key=...)`):

- [ ] [AGENT] P0. Re-smoke after writer fix `f36651c` lands on a forward-poll VM: confirm Bug 1 (Pydantic future-fixture
      goals nullable) + Bug 2 (UnboundLocalError on `get_leagues_needing_refresh`) + Bug 3 (404 on
      instrument_availability for future dates) are gone.
- [ ] [AGENT] P0. Apply the per-league empty-loop pattern (Bug 6 fix, line 1682 in orchestrator) to AF enrichment
      entities (FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / PLAYER_STATS / INJURIES / STANDINGS) — Bugs 7-8 in
      source plan; partially overlaps writer fix `f36651c` already covering FIXTURES.
- [ ] [AGENT] P0. Unit tests per entity: synthetic adapter response covering 2 in-season leagues out of 6 expected →
      assert per-league `record_empty` for the 4 not present + `manifest.add` for the 2 present.
- [ ] [AGENT] P0. End-to-end smoke: fire AF backfill on a known mixed-coverage date, verify per-league rows for all 6
      entities.
- [ ] [AGENT] P0. Launch fresh forward-poll VM, tail GCS log, assert zero warnings/errors of the three Bug 1-3 classes.

## Out of scope

- footystats / understat / transfermarkt / SFI / open_meteo backfills — those have their own coverage pipelines.
- Mapping repair: if Phase 1 surfaces canonical leagues with no af*league_id mapping, document them but defer the fix to
  a follow-up plan (`sports_canonical_league_id_mapping_repair*\*.md`).
- The original phantom recovery's MTDS-side downstream-empty cleanup (separate plan).
