---
doc_type: issue
title:
  MDPS odds_horizon_bucket reprocess — launch prep done 2026-07-25; EXECUTED 2026-07-25 (slot 7) + INDEPENDENTLY
  RE-CONFIRMED 2026-07-27 (slot 9, duplicate dispatch — see stale-todo issue doc)
summary: >-
  Prep work for sports_satellite_ao_dispatch_batch2_2026_07_24.md's league_id casing migration todo (the MDPS
  odds_horizon_bucket reprocess step, 109,312 objects) was completed and verified 2026-07-25. **This doc's own todo was
  never flipped when the actual reprocess ran** (2026-07-25, slot 7, VMs `mdps-sports-bucket-20260725-*`, results in
  `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`) — the backlog re-derived it as a fresh task
  and it was DUPLICATED 2026-07-27 (slot 9, VMs `mdps-sports-bucket-20260727-*`). Harmless (the reprocess is `--force`
  idempotent; the 2nd run independently reproduced the identical residual-failure signature, which is a nice bonus
  confirmation) but wasteful — see
  `issues/mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md` for the root-cause writeup.
  Closing this doc now (status: resolved) to prevent a third dispatch.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [sports, league-id, mdps, vm-launcher, migration, launch-prep]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md,
    /plans/active/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/active/issues/mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md,
  ]
created: 2026-07-25
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
source: sports_satellite_ao_dispatch_batch2_2026_07_24.md, league_id casing migration todo, step (3)
resolved_by:
  market-data-processing-service (reprocess_sports_odds.py, 2026-07-25 slot 7, re-confirmed 2026-07-27 slot 9)
locked_by:
drift_direction: advance-code
depends_on: []
---

# MDPS odds_horizon_bucket reprocess — launch prep done, not yet launched

## What I verified (2026-07-25T02:42Z, slot 9, data_engineering)

1. **Tarball freshness re-checked and 2 fixed** — despite the earlier "CREDENTIAL BLOCKER RESOLVED... full 5-repo
   republish succeeded" claim, a direct check
   (`gcloud storage cat gs://deployment-scripts-central-element-323112/code/<tarball>.manifest.json`, comparing
   `commit_sha` against each repo's local `git rev-parse HEAD` — NOT the launcher's own `lc_verify_tarball_freshness`,
   which is currently blind per the credential-blocker issue doc's own residual-gap note) found 2 of the 5 repos the
   launcher needs were STALE again (more commits had landed since that republish):
   - `market-data-processing-service`: tarball `aa6e8ac3` vs local HEAD `468d01e3`
   - `market-tick-data-service` (tarball name `mtds-code`): tarball `7e86436c` vs local HEAD `7f1262a0`
   - `unified-api-contracts`, `unified-trading-library`, `deployment-service`: already fresh.

   Republished via
   `bash scripts/vm/create-code-tarballs.sh --include market-data-processing-service --include market-tick-data-service --include unified-api-contracts --include unified-trading-library --include deployment-service`
   (needs `deployment-service/.venv` bootstrapped first — `bash scripts/setup.sh` — for the ADC uploader). Re-verified
   all 5 now byte-exact match current HEAD via the same `gcloud storage cat` method.

2. **TOCTOU fix confirmed included** — `git merge-base --is-ancestor 14301571 HEAD` in `unified-trading-library` returns
   true, confirming the fix that closed the manifest silent-revert bug
   (`sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`) is in the tarball this VM would fetch.

3. **No conflicting VM** — `gcloud compute instances list` showed zero instances with "mdps"/"sports-bucket" in the
   name, running or terminated recently.

4. **Mechanism dry-run-verified on real data** — `reprocess_sports_odds.py --dry-run`:
   - `2026-07-01`→`2026-07-07`: 0/7 success, all "No raw odds data" — genuinely no raw ODDS_API data that recent yet,
     not a script problem (not investigated further, out of scope for this prep — the historical range is what matters
     for this migration).
   - `2025-09-01`→`2025-09-03` (the golden window used elsewhere this session): 2025-09-01 succeeded cleanly (12,405 raw
     rows → 547 bucketed rows across 24 (league, horizon) shards, 22 bookmakers). 2025-09-02/03 hit
     `ADAPTER_RETURNED_EMPTY_OUTPUT` (raw data present — 25,065 and 28,740 rows respectively, with 56 and 94 zombie-tick
     rows dropped — but the adapter's zombie-tick filter removed everything else too). Read the script's own docstring
     (`reprocess_sports_odds.py` lines ~684-690): this is INTENTIONAL honest-absence hardening (the 2026-06-22
     `UnprovenHonestAbsenceError` fix) — raw data existing but filtering to zero rows is NOT an honest absence, so it's
     correctly routed to retriable `attempted_failed`, never a false `empty_confirmed`. Confirmed this is
     working-as-designed, not a bug to fix.

## Why not launched

The full migration scope is `2020-06-06` → present (~2,139 days), 109,312 objects. The launcher's own docstring
recommends sharding across 4-6 VMs to keep wall-clock under ~1hr; a single VM at the cited ~250-350 days/hr throughput
would take ~5.5-7.5hr. Either way this is a multi-hour operation, genuinely not completable within one AO-dispatched
turn. The host was also under heavy concurrent load from sibling slots for most of this session (`uptime` 1-min avg
15-30 on an 8-core box) — did not want to add a large multi-VM launch on top of that blind.

Additionally, given `sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`'s lesson (a previous direct-manifest
write on this exact migration silently reverted due to a race, only caught by re-checking days later), any future
executor of this step should NOT declare it done from the VM's own in-script `verify_swap()`/completion log alone — poll
the live manifest across >=2 consolidator cycles post-completion, exactly as that fix's own recommended follow-up says.

## Ready-to-execute next step

```bash
# Single VM (simpler, ~5.5-7.5hr wall-clock):
bash scripts/vm/launch-mdps-sports-bucket-vm.sh 2020-06-06 2026-07-25 force

# OR sharded across 4-6 VMs (per the launcher's own docstring example, <1hr target):
bash scripts/vm/launch-mdps-sports-bucket-vm.sh 2020-06-06 2021-12-31 force
bash scripts/vm/launch-mdps-sports-bucket-vm.sh 2022-01-01 2023-06-30 force
bash scripts/vm/launch-mdps-sports-bucket-vm.sh 2023-07-01 2024-12-31 force
bash scripts/vm/launch-mdps-sports-bucket-vm.sh 2025-01-01 2026-07-25 force
```

Re-verify tarball freshness again before launching if picked up more than ~1hr after this doc's timestamp (repos are
under active development, tarballs go stale again in hours, not days — see the 2 that had already gone stale since the
prior "resolved" claim). Verify each VM STARTED cleanly (<60s, first log line, no fire-and-forget) before moving on.
After completion, poll `_index/availability_index.parquet` for the `odds_horizon_bucket` league_id distribution
across >=2 manifest-consolidator cycles (~1min cadence) before flipping the parent todo's checkbox.

`batch_footystats` copy+swap (16,970 objects) is a separate step (extend `migrate_sports_league_id_casing_2026_07_21.py`
to that shape) — not started, not part of this VM launch.

## Addendum (2026-07-25, slot 7) — batch_footystats shape is NOT a simple re-run of the odds executor

While the reprocess VMs (below) ran, spot-checked the real `batch_footystats` raw shape on 3 sample days
(`gcloud storage ls -r`, single-object descents, not a corpus walk) to scope the extension ahead of time. It is **not**
a drop-in re-target of `migrate_sports_league_id_casing_2026_07_21.py`'s existing logic — 3 real differences found:

1. **`instrument_type=` is BARE (empty value)** on every object seen, e.g.
   `.../pipeline_mode=batch_footystats/asset_group=sports/venue=ODDS_API/instrument_type=/data_type=odds/league=<L>/...`
   — the odds executor's target casing (`instrument_type=ODDS`) assumes a populated segment; this shape needs that
   decided (backfilled to `ODDS` on write, or is `data_type=odds` itself the intended type-carrier and
   `instrument_type=` is dead weight to drop?) — an architect call, not an execution detail.
2. **Filenames are `ticks_migrated_<timestamp>.parquet`**, not the odds executor's `ticks.parquet` — these read as a
   one-time migration dump (2026-05-05 timestamps seen), not this pipeline's live write path; worth confirming whether
   `batch_footystats` is even still actively written before spending migration effort on it. A 2019-08-10 sample day had
   ZERO `batch_footystats` objects at all (day-sparse, unlike `batch_odds_api`'s near-daily coverage).
3. **Raw league values ARE non-canonical, but — CORRECTED after checking — `classification.json` already covers every
   raw value sampled**, so this is smaller than first flagged: `2._BUNDESLIGA` -> `BUNDESLIGA_2` (DEFINITE), `MLS` ->
   `MLS` (DEFINITE, casing-only), `BUNDESLIGA`/`PRIMERA_DIVISION`/`SERIE_A`/`CHAMPIONSHIP` -> `AMBIGUOUS` (per-row split
   via `sport_key`, same as the odds shape's known collision leagues). So the SAME `classification.json` /
   `sportkey_canon_final.json` maps look reusable as-is for the raws checked — no separate classification pass evidenced
   yet (still only a 3-day sample; do not treat as exhaustive coverage proof before `--dry-run`s it for real against the
   full footystats corpus).

Recommend scoping the footystats extension as its own short design pass — mainly (1) decide the `instrument_type=`
disposition and (2) confirm `batch_footystats` write-path liveness (point 2 above) — before an executor spawns code
against it; classification-map reuse now looks likely rather than uncertain. Flagging here rather than guessing under
this VM-launch task's scope.

## Todos

- [x] 1. ✅ [SCRIPT] P0. Launch the MDPS `odds_horizon_bucket` reprocess (single VM or sharded, per above) once tarball
      freshness is re-verified; confirm clean start; poll to completion or health-check across sessions like the
      established af-backfill pattern. (repo: market-data-processing-service, deployment-service) — **originally
      EXECUTED 2026-07-25 (slot 7)**: 4 sharded SPOT VMs (`mdps-sports-bucket-20260725-035949/040027/040053/040119`),
      166,751 shards / ~5.4M bucketed rows, manifest-verified stable across 2 consolidator cycles. Full detail +
      residual-failure classification: `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`. **This
      checkbox was never flipped at the time**, so the backlog re-derived + re-dispatched this same doc's todo 2 days
      later. **DUPLICATE re-run 2026-07-27 (slot 9)**: re-verified tarball freshness (unified-api-contracts had drifted
      stale since the earlier scan — fixed via `refresh_code_tarballs.sh`), launched 4 fresh sharded SPOT VMs
      (`mdps-sports-bucket-20260727-013917/013942/014005/014026`, same 4 date ranges), all started cleanly (<60s to
      first heartbeat, no fire-and-forget) and ran to terminal completion in 24-37 min each. Aggregate: 2242 dates, 1922
      success + 294 genuinely-empty + 22 honest `attempted_failed` + 4 correctly `LOSS_GUARD_BLOCKED` — **the IDENTICAL
      residual-failure signature as the 2026-07-25 run** (same 18 `ADAPTER_RETURNED_EMPTY_OUTPUT` + 4
      `RAW_ODDS_SHAPE_UNRECOGNIZED` (2026-06-21..24) + 4 `LOSS_GUARD_BLOCKED` dates), independently confirming the
      original run's canonicalization is genuinely stable, not a fluke. Manifest re-verified: `odds_horizon_bucket`
      league_id 99.98% canonical (462,131 rows, 87 residual — exactly the honest-absence-skipped dates), stable across 2
      more consolidator cycles (02:24:09Z→02:33:08Z, non-canonical count held at 87). Root-cause of the duplicate
      dispatch + process-fix recommendation:
      `issues/mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md`.
- [x] 2. ✅ [DATA] P0. After the reprocess completes, verify manifest stability across >=2 consolidator cycles before
      declaring done; then run the `batch_footystats` copy+swap (16,970 objects) via
      `migrate_sports_league_id_casing_2026_07_21.py` extended to that shape. (repo: market-tick-data-service) —
      manifest-stability half DONE (folded into todo 1 above, confirmed independently twice: 2026-07-25 and 2026-07-27).
      **`batch_footystats` copy+swap — CORRECTED, not a copy+swap task**: per the parent plan
      (`sports_satellite_ao_dispatch_batch2_2026_07_24.md`), this population turned out to be mis-stamped
      `batch_odds_api` data already merged to canonical on 2026-07-17 (`market-tick-data-service@75f226e8`) — no
      copy+swap work remains. What's left is a human-gated orphan-object PURGE (5-part delete-safety proof, staged not
      executed): `issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md`.
