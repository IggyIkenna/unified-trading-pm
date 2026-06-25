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
- [ ] [INFRA] P1. **Retire the cross-AG SHARED instruments backfill launcher → per-AG launchers (operator 2026-06-25).**
      `instr-backfill-cefi-*` captures the full instruments universe in ONE pass and writes ALL FOUR per-AG buckets
      (run.log: flushed sports/cefi/defi/tradfi) — this contradicts the foundation per-AG gating (it captures sports
      while sports is gated behind cefi) and mis-labels alerts (cefi). Launch instruments backfills **per asset_group**
      (`VM_ASSET_GROUP`-scoped, single bucket) so gating is enforceable + alerts attribute correctly. (cefi/infra track —
      documented from the sports track.)
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
- [ ] [DATA] P1. **FINDING: 46,844 blank-source STANDINGS empty_confirmed rows + ~32 blank-source TEAMS/STANDINGS
      attempted_failed** — a separate canonical-form defect (blank `source`); fold into the §2 "ALL non-canonical-form"
      sweep (stamp api_football, dedup).
- [ ] [SCRIPT] P0. **DEFERRED-subsumed: original "migrate mis-sourced rows" todo** —
      re-stamp `source`/`pipeline_mode` for every sports row whose stamped `(data_type → source/pipeline_mode)` differs
      from the canonical `SOURCE_PRIORITY`-derived form (TEAMS/STANDINGS the dominant set), then **dedup** on the
      canonical shard key `(date, data_type, league_id, source)` keeping best status (captured > empty_confirmed >
      expected_unattempted > attempted_failed). Verify: phantom TEAMS/STANDINGS heal (candidate hits on disk) + captured
      count consistent + NO row lost. Single `_index` read+write (no whole-corpus GCS walk).
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

## Composes with
- `#6` IS-odds wipe (`sports_golden_window_attempted_failed_remediation_2026_06_24.md`) — ODDS removal is part of the
  canonical alignment (odds = MTDS).
- The MVP-scope non-canonical-league delete (`instruments_foundation_completeness_2026_06_24.md` sports G1) — a
  non-canonical LEAGUE is the league-axis analog of this source-axis canonical defect.

## Codex SSOT updates
- `instruments-foundation-and-catalogue-completeness.md` §3 sports — add the canonical-form-migration rule (source must
  equal the on-disk pipeline_mode; SOURCE_PRIORITY is the SSOT, SPORTS_DATA_TYPE_TO_SOURCE must mirror it).

## Progress log
- 2026-06-25 — Filed per operator directive. Root cause (TEAMS/STANDINGS footystats→api_football mis-attribution)
  measured + UAC map aligned to SOURCE_PRIORITY. Migration script next.
