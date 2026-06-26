---
title: "Sports manifest + GCS canonical-form migration — single source of truth (IS + MTDS)"
created: 2026-06-25
parent_epic: sports_master
assigned_vm: NA
estimate_class: refactor
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 4
locked_by: live-defi-rollout
priority: P0
status: active
source:
  - operator directive 2026-06-25 ("should use canonical forms, so migrate"; "if there's any GCS data that's in the
    wrong canonical form ... for instrument service or market(-tick)-data service, when it comes to schemas or paths or
    whatever, it should be migrated so we don't have two sources of truth — manifest lines up with coverage + index +
    data-status + deployment-UI; everything related to asset_group should be updated; document is such in plan")
---

# Sports manifest + GCS canonical-form migration — one SSOT

**Codex SSOT:** `codex/02-data/instruments-foundation-and-catalogue-completeness.md` (§2 layered coverage, §3 sports,
§6.1 key-overlap). Parent foundation plan: `plans/active/instruments_foundation_completeness_2026_06_24.md`. Sibling:
`plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` (the #5 candidate-path framing for
TEAMS/STANDINGS is SUPERSEDED by this plan — see root cause below).

## Operator directive (2026-06-25)

Wherever sports GCS data (instruments-service OR market-tick-data-service) sits in a **non-canonical form** — wrong
`source`, wrong `pipeline_mode`, wrong path/schema, wrong `asset_group` — it must be **migrated to the canonical form**
so we never carry two sources of truth. After migration the **manifest** must line up with its **coverage / `_index`**,
the **data-status**, **deployment**, and the **deployment-UI** — one number, one key. Every `asset_group`-related field
is part of this alignment.

## Root cause found (TEAMS / STANDINGS source mis-attribution) — the first instance

Measured 2026-06-25 on `instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`:

- `SPORTS_DATA_TYPE_TO_SOURCE` mapped `TEAMS`/`STANDINGS` → **footystats**, but the **canonical** SSOT
  `SOURCE_PRIORITY[("sports","TEAMS"|"STANDINGS")] = ["api_football"]` (the ManifestWriter already raised
  `MissingSourceError` on footystats). footystats writes ONLY `footystats_matches/odds/predictions` to disk — it does
  **not** write teams/standings. The real teams/standings parquets live under
  `…/pipeline_mode=batch_api_football/entity={teams,standings}/…`.
- Result: **~137k mis-sourced manifest rows** stamped `source=footystats`/`pipeline_mode=batch_footystats` that can
  never resolve to the on-disk api_football data → flagged `attempted_failed`
  (`phantom_captured_no_parquet_at_canonical_path`): **TEAMS 89,908 + STANDINGS 46,948** phantom, plus **TEAMS 12,411 +
  STANDINGS 12,410** "captured" rows whose candidates only hit at `batch_api_football` (also mis-keyed). The reconciler
  `--unphantom-only` heals **0** of these because it probes the row's (wrong) `pipeline_mode`.
- This is NOT the `candidate_parquet_paths` path-shape gap (#5) — that was a symptom. The fix is **canonical-form
  migration**: re-stamp these rows to `source=api_football`, `pipeline_mode=batch_api_football`, then dedup vs existing
  api_football rows (best-status-wins).

## Phases (DAG)

- [x] ✅ [CODE] P0. **UAC — align `SPORTS_DATA_TYPE_TO_SOURCE` to `SOURCE_PRIORITY`**: `TEAMS`/`STANDINGS` →
      api_football; keep `MATCHES`/`PREDICTIONS`/`ODDS` = footystats (ODDS removed coherently in #6, not piecemeal —
      dropping the map entry alone breaks validity-matrix reachability vs SOURCE_PRIORITY). — uac@400d2729 (LDR; Tier-C
      drain → staging).
- [x] ✅ [OPS] P0. **Killed the running non-canonical sports + cross-AG instruments VMs (operator 2026-06-25 "stick to
      your asset group sports; launch separately per-AG").** Deleted `sports-ref-v3-1/2/3/e1/e2` (full sports
      instruments-reference backfills, 2014→2026 date-sharded, ALL data_types, running the OLD UAC = footystats
      TEAMS/STANDINGS → re-polluting + racing the migration). No cross-AG instruments VM running
      (`instr-backfill-cefi-*` self-deleted; `instr-backfill-defi` is per-AG defi — left). Their per-VM shards were
      already consolidated (no loss).
- [x] ✅ [INFRA] P1. **Retire the cross-AG SHARED instruments backfill launcher → per-AG launchers (operator
      2026-06-25).** — instruments-service@04b8e31 `instr-backfill-cefi-*` captures the full instruments universe in ONE
      pass and writes ALL FOUR per-AG buckets (run.log: flushed sports/cefi/defi/tradfi) — this contradicts the
      foundation per-AG gating (it captures sports while sports is gated behind cefi) and mis-labels alerts (cefi).
      **Root cause: `InstrumentsHandler.cleanup()` hardcoded all 4 AGs in its ManifestWriter flush loop.** Fix: scope
      flush to `self.args.asset_group` (same pattern as `preflight()`); "ALL" or unset still flushes all 4. Processing
      was already per-AG scoped; only cleanup was broken. `setup-data-pipeline-vm.sh` already passes
      `--asset-group $VM_ASSET_GROUP` so per-AG gating is now enforceable + alerts attribute correctly. Test updated:
      `test_cleanup_flushes_manifest_writers_and_emits_coordination_events` now asserts only 1 bucket flushed for
      `--asset-group SPORTS`. (cefi/infra track — documented from the sports track.)
- [x] ✅ [SCRIPT] P0. **Migrated sports `_index` + `_legacy_seed` mis-sourced rows to canonical (snapshot-first)** —
      `instruments-service/scripts/migrate_sports_teams_standings_canonical_source_2026_06_25.py --apply`: re-stamped
      footystats TEAMS/STANDINGS → `source=api_football`/`pipeline_mode=batch_api_football` IN PLACE in BOTH the
      consolidation source (`_legacy_seed.parquet`, 288,657 rows) AND the canonical index (243,560 rows, 0 lost).
      source/ pm are NOT consolidator dedup keys so this is a pure column edit. Snapshots:
      `_index/snapshots/pre_teams_standings_canon_20260625_011753/`. (Did NOT delete+cold-rebuild — the canonical is a
      SUPERSET of the stale seed; cold rebuild would have lost ~19k accumulated rows.)
- [x] ✅ [SCRIPT] P0. **Healed the now-resolvable phantom TEAMS/STANDINGS (reconciler `--unphantom-only --apply`)** —
      re-validated 139,804 phantom rows; **134,327 flipped phantom→captured** (TEAMS 89,815 + STANDINGS 44,512); 5,477
      genuinely-missing left attempted_failed. **Prod-verified**: TEAMS footystats-remaining=0 (103,656 captured),
      STANDINGS footystats-remaining=0 (88,136 captured); total captured 577,771; remaining phantom 5,477 = MATCHES
      2,424 / XG 847 / PREDICTIONS 564 / ODDS 491 / FIXTURES 381 / … (NOT TEAMS/STANDINGS — those are fully healed).
- [x] ✅ [DATA] P1. **FINDING: 46,844 blank-source STANDINGS empty_confirmed rows + ~32 blank-source TEAMS/STANDINGS
      attempted_failed** — a separate canonical-form defect (blank `source`); fold into the §2 "ALL non-canonical-form"
      sweep (stamp api_football, dedup). — instruments-service@65eec99
- [x] ✅ [SCRIPT] P0. **DEFERRED-subsumed: original "migrate mis-sourced rows" todo** — re-stamp
      `source`/`pipeline_mode` for every sports row whose stamped `(data_type → source/pipeline_mode)` differs from the
      canonical `SOURCE_PRIORITY`-derived form (TEAMS/STANDINGS the dominant set), then **dedup** on the canonical shard
      key `(date, data_type, league_id, source)` keeping best status (captured > empty_confirmed >
      expected_unattempted > attempted_failed). Verify: phantom TEAMS/STANDINGS heal (candidate hits on disk) + captured
      count consistent + NO row lost. Single `_index` read+write (no whole-corpus GCS walk). — **SUBSUMED** by targeted
      TEAMS/STANDINGS canonical migration (items 3+4): 288,657 seed + 243,560 index rows re-stamped; 134,327 phantoms
      healed; prod-verified footystats-remaining=0 for both; captured=577,771.
- [x] ✅ [SCRIPT] P1. **Sweep the sports `_index` for ALL other non-canonical-form rows** — instruments-service@023d268
      Retired data_types deleted: TRANSFERMARKT_LEAGUES 75,545 + SFI_LEAGUES 12,469 + SFI_STANDINGS 42 = 88,056. Blank
      data_type deleted: 142. Renamed lowercase `odds` → `ODDS`: 887. Blank asset_group stamped "sports": 191,966. Blank
      source (non-exempt) stamped from SOURCE_PRIORITY: 156,644 (INJURIES 66,427 · STANDINGS 46,844 · FIXTURES 27,129 ·
      PLAYER_STATS 2,588 · + 9 more data_types). Dedup on (date, data_type, league_id, source) removed 73,287
      duplicates. Net: 2,784,066 → 2,622,581 rows (-161,485). Snapshot: pre_noncanonical_sweep_20260625_024500. Also
      resolves [DATA] P1 blank-source STANDINGS (46,844 stamped api_football in this same pass).
- [x] ✅ [SCRIPT] P1. **MTDS parity sweep** — the same canonical-form audit over the MTDS sports tick manifest
      (`market-tick-data-*` sports): any wrong source/pipeline_mode/path/asset_group → migrate. (Odds-api ODDS lives in
      MTDS; confirm its rows are canonical-form.) — market-tick-data-service@2807e9baf Script:
      `scripts/normalize_sports_mtds_data_type_case_2026_06_25.py` (dry-run by default, `--apply` to execute). Audit
      2026-06-25: 20,103 non-canonical rows (ODDS 20,095 footystats + ODDS_MOVEMENT 4 + ODDS_SNAPSHOT 4 odds_api);
      232,098 trades + 109,638 odds_horizon_bucket already canonical (NOT touched). Fix: lowercase data_type in place,
      snapshot-first.
- [x] ✅ [INFRA] P1. **Alert asset_group attribution = the failing SHARD's AG, not the VM-name prefix (operator
      2026-06-25).** — deployment-service@09bb319 `_make_shard_backed_ag_fn` factory: fast-path VM-name match, slow-path
      probes `_index/per_vm/{vm}.parquet` across AG buckets; both `exit_code_fleet_monitor` + `heartbeat_stall_watcher`
      callsites updated; 4 unit tests added. The shared instruments-backfill VM (`instr-backfill-cefi-*`) captures ALL
      asset*groups in one run (run.log: `ManifestWriter cleanup: flushed buffers for [sports, cefi, defi, tradfi]`), but
      `DP*_`alerts derive    `Asset
      group:`from the VM-name prefix (cefi) via`VM*PREFIX_TO_BUCKET`/`classify_deployment_target`→ a sports     api_football 429 on that VM is mis-labelled`cefi`. Fix: the `DP_SOURCE_RATE_LIMITED`/`DP*_`alert (deployment-     service no-capture-reason path) must read the asset_group from the failing shard/venue (run.log per-shard AG +     the manifest row's`asset_group`), not the launch-AG name prefix; the shared cross-AG instruments VM should be     classified multi-AG (or per-bucket). Provenance: operator Slack 2026-06-25 (`instr-backfill-cefi-2`
      DP_SOURCE_RATE_LIMITED tagged cefi while flushing sports).
- [x] ✅ [SCRIPT] P1. **Verify single-SoT end to end** — after migration: `compute_honest_coverage` number == raw-GCS
      recompute (§2.3 reconciliation guard) AND the deployment-UI `/data-status` sports number matches, per (source,
      data_type). Key-overlap climbs / phantom drops (§6.1), never a raw count. market-tick-data-service@b70a97ea | §2.3
      guard PASS: 5 data_types, 0 mismatches; 0 uppercase rows remain (was 20,103); captured=340,080 of 361,839;
      coverage=100% for odds/odds_horizon_bucket/trades/odds_movement/odds_snapshot.

## Non-football canonical leagues (operator 2026-06-25 "only football; delete others + all api_football attempts; coverage excludes non-football") — VERIFIED CLEAN, no action

The 7 non-football canonical leagues (ATP/WTA=TENNIS, MLB=BASEBALL, NBA/EUROLEAGUE=BASKETBALL, NFL=AMERICAN_FOOTBALL,
NHL=ICE_HOCKEY) are ALREADY fully excluded from api_football: `api_football_id=None` + `data_sources=frozenset()` →
never enumerated/fetched; **0 manifest rows**; `get_expected_leagues_for_source("api_football")` = exactly the **94
football leagues** (coverage denominator excludes all 7). They stay in `LEAGUE_REGISTRY` as inert MVP placeholders for
their own sports. No data to delete, no code attempts to remove — VERIFIED 2026-06-25.

## MVP-scope: the 1,438 NON-CANONICAL football leagues (the real delete)

api_football's by-date endpoints return the WHOLE football universe; the IS writer already filters to the 94 via
`_is_in_canonical_write_universe` (CF-7 write-path) — so the **1,438 non-canonical leagues = 1.23M legacy manifest
rows** (840,078 expected_unattempted + 338,469 empty_confirmed + 49,525 captured + 447 failed) are pre-filter pollution.
Deleting is durable (current code won't re-add). DoD: drop the 1.23M rows from seed+canonical (snapshot-first) + delete
the ~49,525 captured GCS objects; verify the api_football coverage denominator + day/depth_coverage exclude them.
Tracked as foundation plan G1.

## Composes with

- `#6` IS-odds wipe (`sports_golden_window_attempted_failed_remediation_2026_06_24.md`) — ODDS removal is part of the
  canonical alignment (odds = MTDS).
- The MVP-scope non-canonical-league delete (`instruments_foundation_completeness_2026_06_24.md` sports G1) — a
  non-canonical LEAGUE is the league-axis analog of this source-axis canonical defect.

## Codex SSOT updates

- `instruments-foundation-and-catalogue-completeness.md` §3 sports — add the canonical-form-migration rule (source must
  equal the on-disk pipeline_mode; SOURCE_PRIORITY is the SSOT, SPORTS_DATA_TYPE_TO_SOURCE must mirror it).

## Remaining tracked work (precise specs for the loop / next fresh-context iteration)

- [x] ✅ [CODE] P1. **#6 ODDS=MTDS removal — COHERENT atomic unit.** UAC shipped (prior slot, uac@8fb1f54f). IS code
      shipped: instruments-service@6404abd (orchestrator bulk removal) + instruments-service@4f6a32e (finalization) +
      instruments-service@2a0be03 (adapter `get_fixture_odds_snapshot` removed + `TestFootystatsAdapterOddsSnapshot`
      tests removed + backfill script ODDS EntitySpec removed). Adapter contract baseline ratcheted:
      `orchestrator/__init__.py 4→3, footystats.py 19→14, sports_fixtures.py 3→2` (already in PM LDR HEAD at ef904d28).
      GCS wipe of ≈116k footystats ODDS rows: see § "GCS wipe TODO" — execute BEFORE §0.5 backfill. KEEP footystats
      PREDICTIONS (untouched).
- [x] ✅ [SCRIPT] P1. **OBSERVABLE BATCH sports backfill re-launch (§0.5) — AFTER the canonical code lands + VM tarball
      rebuilt.** The old `sports-ref-v3-*` fleet was killed (old code, re-polluting). A NEW per-AG
      (`VM_ASSET_GROUP=SPORTS`) backfill must be a registered `DeploymentTarget` + `ServiceBootstrap` heartbeat +
      persisted terminal `exit_code` + log-mtime + `/deployments` BATCH click-through. Scope: drain the 160,488
      canonical `expected_unattempted` + re-run the 67,877 `attempted_failed` (normal re-run, NOT blanket --force) + the
      2015–2017 holes (scoped `--force` IFF the probe says backfill-bug). **Pre-req: `create-code-tarballs.sh` rebuild
      from clean LDR with uac@(TEAMS/STANDINGS + #6) so the new shards stamp canonical** (else it re-writes footystats
      teams/standings/odds). Monitor `exit_code` + captured-climb + log-mtime, never RUNNING-count (the prior monitor's
      blind spot that missed the abnormal exit). — **LAUNCHED 2026-06-25T05:23Z**: 5 VMs RUNNING
      (sports-ref-v3-e1/e2/1/2/3, e2-standard-8, asia-northeast1-c, tarball sha=bd13ee453845). DeploymentUmbrella.BATCH
      via LifecycleClass.EPHEMERAL_BATCH. GCS run.log monitor armed (exit_code + log-mtime ≥45min + captured-climb).
      Background monitor PID 1603151 active.
- [x] ✅ [DATA] P2. **2015–2017 diagnosis** — `SOURCE_COVERAGE_START["api_football"] = date(2015, 1, 1)` in UAC
      `league_data.py:72`. Per-data-type clip: FIXTURE_EVENTS/LINEUPS/STATS/PLAYER_STATS → 2020-06-06
      (`league_data.py:105-108`). Conclusion: **2015-2017 holes are backfill gaps, not tier limits.** No `--force`
      needed — running VMs (e1:2014→2016, e2:2017→2020) are the correct fix. Bare-path fallback WARNING for older dates
      (`no fixture-id column`) is expected and maps to `expected_unattempted` via the per-data-type clip, not
      `attempted_failed`.
- [x] ✅ [CODE] P2. **#2c understat 3-way + #5 candidate_parquet_paths shapes; fixture-completeness ORACLE; G3
      catalogue + scheduler; G-verify honest coverage UI-aligned (key-overlap not count).** Per the foundation plan +
      the oracle plan. — #2c: instruments-service@18398c8 (2-way) + per-league 3-way in understat.py
      (`_failed_league_names` scoping confirmed) | #5: MOOT (all 3 shape gaps verified non-issue) | fixture-completeness
      ORACLE: UAC@400d272 + instruments-service@70548bf + @cba2b9b + @3b7926e + @18361b5 (5 phases done) | G3 catalogue:
      deployment-service cloud_run_job_registry.py `lifecycle-catalogue-regen-sports` registered via asset_group loop |
      G-verify: `_compute_fixtures_depth_coverage()` instruments-service@3b7926e uses oracle denominator
      (`get_expected_fixture_count`) + `row_count`=key-overlap for fixtures (no aliasing), wired to /api/data-status
      SSOT, UI reads verbatim
- [x] ✅ [SCRIPT] P1. **Commit the prod one-off scripts**
      (`migrate_sports_teams_standings_canonical_source_2026_06_25.py` +
      `delete_noncanonical_sports_leagues_2026_06_25.py`) via an IS QG batch (lifecycle: oneoff; ruff-clean). —
      instruments-service@e7eb715 | QG green (--no-fix) | ruff-clean | both scripts lifecycle-marked

## Progress log

- 2026-06-25 — Filed per operator directive. Root cause (TEAMS/STANDINGS footystats→api_football mis-attribution)
  measured + UAC map aligned to SOURCE_PRIORITY.
- 2026-06-25 — **CANONICAL MIGRATION shipped + verified (prod).** Migrated `_legacy_seed` (288,657) + canonical index
  (243,560) footystats TEAMS/STANDINGS → api_football/batch_api_football (snapshot-first, 0 lost); reconciler
  `--unphantom-only --apply` healed **134,327 phantom→captured**. Prod-verified: footystats-remaining=0 for both;
  captured 577,771; 5,477 genuine phantom left (not TEAMS/STANDINGS). UAC map fix shipped `uac@400d2729` (LDR).
- 2026-06-25 — **Killed the old-code sports + cross-AG VMs** (operator-directed); no race.
- 2026-06-25 — **Non-football directive VERIFIED already-clean** (7 leagues api_football_id=None / data_sources empty /
  0 rows / excluded from the 94-league api_football denominator). No action.
- 2026-06-25 — **MVP-SCOPE DELETE shipped + verified (prod).**
  `delete_noncanonical_sports_leagues_2026_06_25.py --apply`: deleted **1,283,171** canonical-index + **1,280,228** seed
  rows (the 1,438 non-canonical football leagues) + 5,265 league-partitioned GCS objects (shared bare/season files
  safely skipped), snapshot-first. Manifest now scoped to the **94 canonical leagues**: total 2,783,846 rows · 473,876
  captured · 2,081,605 empty · 160,488 expected · 67,877 failed · non-canonical-league rows = **0**. (Pruned the ~840k
  non-canonical `expected_unattempted` noise the prior backfill had seeded.)
- 2026-06-25 — #6 UAC shipped (uac@8fb1f54f); IS orchestrator bulk removal (instruments-service@6404abd) +
  cleanup/import-sort (instruments-service@4f6a32ed); IS adapter `get_fixture_odds_snapshot` +
  `TestFootystatsAdapterOddsSnapshot` test class + backfill ODDS EntitySpec removed (instruments-service@2a0be03
  slot-1). Adapter contract baseline corrected to count=3 in PM LDR HEAD (ef904d28). GCS wipe of ≈116k footystats ODDS
  rows: next step (§ "GCS wipe TODO"), before §0.5 backfill.
- 2026-06-25 — **GCS wipe COMPLETE + manifest index cleaned.** `scripts/wipe_footystats_odds_2026_06_25.py`
  (instruments-service@8fbc0cf) ran --apply: **126,683 GCS objects deleted (0 errors)** under
  `sports_reference/by_date/` matching `footystats_odds`; **113,530 manifest rows removed** (74,491 empty_confirmed +
  29,700 captured + 9,256 expected_unattempted + 83 attempted_failed); **2,509,381 rows remain**; **62 odds_api ODDS
  rows preserved intact**. Snapshot at `_index/snapshots/pre_footystats_odds_wipe_index_20260625_051634.parquet`. Script
  bug (GCSBlobHandle.upload_from_filename → gcs_copy_object + client.upload_file + gs:// prefix fix) fixed in same
  commit.
- 2026-06-25 — **VM tarball rebuilt** from clean IS LDR (sha=bd13ee453845, task bcjcmrdn0 exit 0).
  `instruments-service-code.tar.gz` + SHA-pinned copy uploaded to
  `gs://deployment-scripts-central-element-323112/code/`. §0.5 backfill VMs will bake canonical UAC + #6 code. Pre-req
  for #009 DONE.
- 2026-06-25 — **§0.5 backfill RE-LAUNCHED (idempotent) ~05:23Z slot-1.** 5 VMs created (sports-ref-v3-e1/e2/1/2/3,
  e2-standard-8, asia-northeast1-c, tarball sha=bd13ee453845). Prior VMs deleted and recreated. sports-ref-v3-1 +
  sports-ref-v3-3 self-deleted within ~10min (prior run had already captured most of their date ranges; only 6 + 1
  uncaptured dates respectively). 4 VMs (e1, e2, v3-1-new, v3-2) actively processing at T+10min check. Monitor: watch
  GCS vm-logs/sports-ref-v3-\*/run.log exit_code + captured-climb + log-mtime ≥45min.

## GCS wipe — COMPLETE 2026-06-25

~~**Footystats ODDS GCS wipe**: ≈116k manifest rows + their GCS parquet objects remain from before #6 removal.~~ DONE:
126,683 GCS objects deleted, 113,530 manifest rows removed, 62 odds_api rows preserved. Snapshot saved. KEEP: footystats
PREDICTIONS (untouched throughout #6). ✅
