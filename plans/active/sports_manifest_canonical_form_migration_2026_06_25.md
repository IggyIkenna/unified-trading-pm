---
title: "Sports manifest + GCS canonical-form migration — single source of truth (IS + MTDS)"
created: 2026-06-25
parent_epic: sports_master
assigned_vm: planning
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

- [x] ✅ [CODE] P0. **UAC — align `SPORTS_DATA_TYPE_TO_SOURCE` to `SOURCE_PRIORITY`**: `TEAMS`/`STANDINGS` → api_football;
      keep `MATCHES`/`PREDICTIONS`/`ODDS` = footystats (ODDS removed coherently in #6, not piecemeal — dropping the map
      entry alone breaks validity-matrix reachability vs SOURCE_PRIORITY). — uac@400d2729 (LDR; Tier-C drain → staging).
- [x] ✅ [OPS] P0. **Killed the running non-canonical sports + cross-AG instruments VMs (operator 2026-06-25 "stick to
      your asset group sports; launch separately per-AG").** Deleted `sports-ref-v3-1/2/3/e1/e2` (full sports
      instruments-reference backfills, 2014→2026 date-sharded, ALL data_types, running the OLD UAC = footystats
      TEAMS/STANDINGS → re-polluting + racing the migration). No cross-AG instruments VM running (`instr-backfill-cefi-*`
      self-deleted; `instr-backfill-defi` is per-AG defi — left). Their per-VM shards were already consolidated (no
      loss).
- [x] ✅ [INFRA] P1. **Retire the cross-AG SHARED instruments backfill launcher → per-AG launchers (operator 2026-06-25).** — instruments-service@04b8e31
      `instr-backfill-cefi-*` captures the full instruments universe in ONE pass and writes ALL FOUR per-AG buckets
      (run.log: flushed sports/cefi/defi/tradfi) — this contradicts the foundation per-AG gating (it captures sports
      while sports is gated behind cefi) and mis-labels alerts (cefi). **Root cause: `InstrumentsHandler.cleanup()` hardcoded
      all 4 AGs in its ManifestWriter flush loop.** Fix: scope flush to `self.args.asset_group` (same pattern as `preflight()`);
      "ALL" or unset still flushes all 4. Processing was already per-AG scoped; only cleanup was broken. `setup-data-pipeline-vm.sh`
      already passes `--asset-group $VM_ASSET_GROUP` so per-AG gating is now enforceable + alerts attribute correctly.
      Test updated: `test_cleanup_flushes_manifest_writers_and_emits_coordination_events` now asserts only 1 bucket flushed
      for `--asset-group SPORTS`. (cefi/infra track — documented from the sports track.)
- [x] ✅ [SCRIPT] P0. **Migrated sports `_index` + `_legacy_seed` mis-sourced rows to canonical (snapshot-first)** —
      `instruments-service/scripts/migrate_sports_teams_standings_canonical_source_2026_06_25.py --apply`: re-stamped
      footystats TEAMS/STANDINGS → `source=api_football`/`pipeline_mode=batch_api_football` IN PLACE in BOTH the
      consolidation source (`_legacy_seed.parquet`, 288,657 rows) AND the canonical index (243,560 rows, 0 lost). source/
      pm are NOT consolidator dedup keys so this is a pure column edit. Snapshots:
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
- [x] ✅ [SCRIPT] P0. **DEFERRED-subsumed: original "migrate mis-sourced rows" todo** —
      re-stamp `source`/`pipeline_mode` for every sports row whose stamped `(data_type → source/pipeline_mode)` differs
      from the canonical `SOURCE_PRIORITY`-derived form (TEAMS/STANDINGS the dominant set), then **dedup** on the
      canonical shard key `(date, data_type, league_id, source)` keeping best status (captured > empty_confirmed >
      expected_unattempted > attempted_failed). Verify: phantom TEAMS/STANDINGS heal (candidate hits on disk) + captured
      count consistent + NO row lost. Single `_index` read+write (no whole-corpus GCS walk).
      — **SUBSUMED** by targeted TEAMS/STANDINGS canonical migration (items 3+4): 288,657 seed + 243,560 index rows
      re-stamped; 134,327 phantoms healed; prod-verified footystats-remaining=0 for both; captured=577,771.
- [ ] [SCRIPT] P1. **Sweep the sports `_index` for ALL other non-canonical-form rows** — blank `data_type` (127),
      retired data_types in-bucket (`TRANSFERMARKT_LEAGUES` 75,929 · `SFI_LEAGUES` 12,769 · `SFI_STANDINGS` 42 ·
      lowercase `odds` 887), and any `asset_group`/`source`/`pipeline_mode` blank-or-legacy stamp. Each → migrate to
      canonical OR delete-if-retired (snapshot-first). A retired data_type still in the manifest is a two-SoT defect.
- [ ] [SCRIPT] P1. **MTDS parity sweep** — the same canonical-form audit over the MTDS sports tick manifest
      (`market-tick-data-*` sports): any wrong source/pipeline_mode/path/asset_group → migrate. (Odds-api ODDS lives in
      MTDS; confirm its rows are canonical-form.)
- [ ] [INFRA] P1. **Alert asset_group attribution = the failing SHARD's AG, not the VM-name prefix (operator 2026-06-25).**
      The shared instruments-backfill VM (`instr-backfill-cefi-*`) captures ALL asset_groups in one run (run.log:
      `ManifestWriter cleanup: flushed buffers for [sports, cefi, defi, tradfi]`), but `DP_*` alerts derive
      `Asset group:` from the VM-name prefix (cefi) via `VM_PREFIX_TO_BUCKET`/`classify_deployment_target` → a sports
      api_football 429 on that VM is mis-labelled `cefi`. Fix: the `DP_SOURCE_RATE_LIMITED` / `DP_*` alert (deployment-
      service no-capture-reason path) must read the asset_group from the failing shard/venue (run.log per-shard AG +
      the manifest row's `asset_group`), not the launch-AG name prefix; the shared cross-AG instruments VM should be
      classified multi-AG (or per-bucket). Provenance: operator Slack 2026-06-25 (`instr-backfill-cefi-2`
      DP_SOURCE_RATE_LIMITED tagged cefi while flushing sports).
- [ ] [SCRIPT] P1. **Verify single-SoT end to end** — after migration: `compute_honest_coverage` number == raw-GCS
      recompute (§2.3 reconciliation guard) AND the deployment-UI `/data-status` sports number matches, per (source,
      data_type). Key-overlap climbs / phantom drops (§6.1), never a raw count.

## Non-football canonical leagues (operator 2026-06-25 "only football; delete others + all api_football attempts; coverage excludes non-football") — VERIFIED CLEAN, no action
The 7 non-football canonical leagues (ATP/WTA=TENNIS, MLB=BASEBALL, NBA/EUROLEAGUE=BASKETBALL, NFL=AMERICAN_FOOTBALL,
NHL=ICE_HOCKEY) are ALREADY fully excluded from api_football: `api_football_id=None` + `data_sources=frozenset()` →
never enumerated/fetched; **0 manifest rows**; `get_expected_leagues_for_source("api_football")` = exactly the **94
football leagues** (coverage denominator excludes all 7). They stay in `LEAGUE_REGISTRY` as inert MVP placeholders for
their own sports. No data to delete, no code attempts to remove — VERIFIED 2026-06-25.

## MVP-scope: the 1,438 NON-CANONICAL football leagues (the real delete)
api_football's by-date endpoints return the WHOLE football universe; the IS writer already filters to the 94 via
`_is_in_canonical_write_universe` (CF-7 write-path) — so the **1,438 non-canonical leagues = 1.23M legacy manifest rows**
(840,078 expected_unattempted + 338,469 empty_confirmed + 49,525 captured + 447 failed) are pre-filter pollution.
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

- [ ] [CODE] P1. **#6 ODDS=MTDS removal — COHERENT atomic unit (UAC staged as active WIP, IS + wipe pending).** UAC edits DONE in
      working tree (not shipped): `league_data.py` drop `"ODDS"` from `SPORTS_DATA_TYPE_TO_SOURCE`;
      `_source_priority_data.py` drop `("sports","ODDS")`; `test_valid_data_types_by_instrument_type.py` updated
      (`assert "ODDS" not in result`) — 101 UAC validity tests pass. **IS pending** (ship UAC+IS together, one QG each):
      (1) `engine/orchestrator/process_enrichment.py:~238-255` remove the `await _orch._fetch_footystats_odds(...)` call;
      (2) `engine/orchestrator/footystats.py` remove `_fetch_footystats_odds` (690+) + `_load_scheduled_footystats_fixture_map`
      (630, odds-only helper) + the `__all__` entry (31); (3) `engine/orchestrator/__init__.py:453,745` remove the
      re-exports + drop `"ODDS"` from `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE`; (4) `engine/orchestrator/sports_fixtures.py:60-68`
      remove `"footystats_odds":"footystats"`; (5) update IS tests (test_sports_reference_v9_path /
      test_backfill_orphan_class_e / test_orchestrator_write_gate / test_migration_orphan_sweep — the ones exercising the
      odds path). **Then WIPE** the remaining canonical-league IS footystats ODDS rows + GCS objects (the non-canonical
      ODDS already removed by the MVP delete — remaining ≈116k of the original 194,789), snapshot-first, mirroring the #3
      api_football wipe. KEEP footystats PREDICTIONS.
- [ ] [SCRIPT] P1. **OBSERVABLE BATCH sports backfill re-launch (§0.5) — AFTER the canonical code lands + VM tarball rebuilt.**
      The old `sports-ref-v3-*` fleet was killed (old code, re-polluting). A NEW per-AG (`VM_ASSET_GROUP=SPORTS`)
      backfill must be a registered `DeploymentTarget` + `ServiceBootstrap` heartbeat + persisted terminal `exit_code` +
      log-mtime + `/deployments` BATCH click-through. Scope: drain the 160,488 canonical `expected_unattempted` + re-run
      the 67,877 `attempted_failed` (normal re-run, NOT blanket --force) + the 2015–2017 holes (scoped `--force` IFF the
      probe says backfill-bug). **Pre-req: `create-code-tarballs.sh` rebuild from clean LDR with uac@(TEAMS/STANDINGS +
      #6) so the new shards stamp canonical** (else it re-writes footystats teams/standings/odds). Monitor `exit_code` +
      captured-climb + log-mtime, never RUNNING-count (the prior monitor's blind spot that missed the abnormal exit).
- [ ] [DATA] P2. **2015–2017 diagnosis** — one direct api_football probe (e.g. EPL 2016) → real tier/subscription history limit
      (record honest absence + fix `SOURCE_COVERAGE_START`) vs backfill-bug (scoped `--force` in the observable backfill).
- [ ] [CODE] P2. **#2c understat 3-way + #5 candidate_parquet_paths shapes; fixture-completeness ORACLE; G3 catalogue + scheduler;
      G-verify honest coverage UI-aligned (key-overlap not count).** Per the foundation plan + the oracle plan.
- [ ] [SCRIPT] P1. **Commit the prod one-off scripts** (`migrate_sports_teams_standings_canonical_source_2026_06_25.py` +
      `delete_noncanonical_sports_leagues_2026_06_25.py`) via an IS QG batch (lifecycle: oneoff; ruff-clean).

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
- 2026-06-25 — **MVP-SCOPE DELETE shipped + verified (prod).** `delete_noncanonical_sports_leagues_2026_06_25.py --apply`:
  deleted **1,283,171** canonical-index + **1,280,228** seed rows (the 1,438 non-canonical football leagues) + 5,265
  league-partitioned GCS objects (shared bare/season files safely skipped), snapshot-first. Manifest now scoped to the
  **94 canonical leagues**: total 2,783,846 rows · 473,876 captured · 2,081,605 empty · 160,488 expected · 67,877 failed
  · non-canonical-league rows = **0**. (Pruned the ~840k non-canonical `expected_unattempted` noise the prior backfill
  had seeded.)
- 2026-06-25 — #6 UAC staged (active WIP, tests pass); IS orchestrator removal + wipe + observable-backfill relaunch +
  G2/oracle/G3 captured above for the loop.
