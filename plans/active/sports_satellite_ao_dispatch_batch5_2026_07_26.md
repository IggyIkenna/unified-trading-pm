---
doc_type: plan
title: Sports satellite AO batch 5 — fresh Phase-1/Phase-3 triage of the sports closeout-orphan corpus
summary: >-
  Fifth AO-dispatch batch for sports, produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) +
  Phase-3 (conflict-check + draft) triage over all 60 sports AG-primary docs not already covered by the consolidated
  closeout, batch2/3/4 (+finalize), or the 4 line-cap-split forks/finalize (2026-07-26). 44 docs came back orphaned (21
  partial coverage, 23 never touched, 1 exclude_cross_cutting dropped); Phase 3's conflict check cleared 25 of them into
  fresh AO-dispatch todos (2 near-duplicate pairs merged into single combined todos citing both sources), found 1
  (`sports_trades_attempted_failed_2026_07_23.md`) already fully covered by two 2026-07-25-dated docs Phase-1's
  citation-grep had missed, and left 4 genuinely conflict-gated + 12 operator-gated items in the Deferred sections below
  for the next iteration or an explicit operator ruling, per the skill's non-batchable taxonomy.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    unified-trading-system-ui,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-5, satellite-docs, fresh-triage]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (interactive, operator-approved scope) — Phase 1 classified all 60 sports
  AG-primary docs not already in the covering-plan set via a Workflow fan-out (60 agents), Phase 3 ran a conflict-check
  + candidate-todo draft over the 44 orphaned docs via a second Workflow fan-out (44 agents), per the skill's documented
  methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports satellite AO batch 5 — fresh triage extraction

> **Status: active — operator-approved 2026-07-26.** Dispatched per CLAUDE.md's plan-destination rule and the
> ag-closeout-audit skill's autonomous-mode guidance (a skill-drafted AO batch is never auto-shipped; this flip followed
> explicit operator review). All 25 todos below are same-priority-independent and touch distinct files/docs EXCEPT the
> two todos both citing `migrate_sports_canonical_v9.py` (the T6.8 retirement todo and the E8 `--drop-stale`
> implementation todo) — both carry inline coordination text so a worker on either one checks the other's state first;
> do not strip that text if editing before dispatch.

## Todos

- [x] ✅ [DATA] P1. **Historical audit of api_football per-fixture `empty_confirmed` rows possibly mismasking hard fetch
      failures.** Now that the swallow-to-`[]` bug is fixed (`instruments-service@f31fb2e9` — the 4 per-fixture adapters
      `get_fixture_statistics`/`get_fixture_events`/`get_fixture_lineups`/`get_fixture_player_stats` re-raise hard
      failures instead of returning `[]`), scope a census (manifest-only, no new GCS walk) over
      `capture_status=empty_confirmed` / `EXPECTED_NO_FIXTURE` / `EXPECTED_NO_PROVIDER_COVERAGE` rows on
      `FIXTURE_STATS`/`FIXTURE_EVENTS`/`FIXTURE_LINEUPS`/`PLAYER_STATS` (source=api_football) whose `attempted_at` falls
      inside a window correlatable to a known api_football hard-failure event (cross-reference `ADAPTER_FETCH_FAILED`
      log/event history if retained, or re-probe a representative sample against the live API to confirm whether data
      genuinely exists there now). Re-flag genuine false positives to `attempted_failed` so they re-enter the normal
      re-fetch path. This audit is complementary to (not a duplicate of)
      `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`, which covers rows already correctly
      marked `attempted_failed` — this covers the opposite failure mode (rows that should have been `attempted_failed`
      but were silently written `empty_confirmed`); coordinate with that doc's findings rather than re-deriving shared
      machinery. Repo: instruments-service. Source:
      `issues/api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md`. **Done when**: the census is
      run and its match count reported (0 matches → note the exposure window was smaller than feared, no relabel needed;
      N matches → each genuine false positive is relabeled `attempted_failed` with the relabel count and query cited in
      a new dated section of this issue doc, and the doc's `status` is updated to reflect the audit's completion). —
      **DONE 2026-07-26 — 0 matches, no relabel needed** (the buggy code path fired live but its retry loop stalled
      before ever reaching the write step, so no bad rows landed). Full census + evidence:
      `issues/api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md` (`status: resolved`).
- [ ] [DATA] P2. **player_stats nested-schema normalization + 1,298 manifest/GCS-mismatch investigation (Finding-1
      follow-ups)** — two items surfaced during the 2026-07-25 player_stats de-dup pass, not previously tracked as
      remediation todos anywhere in the sports covering-plan set: (1) ~3,274/26,687 (~12%) canonical `player_stats`
      cells carry a NESTED schema (`[team, players, fixture_id, available_at]`, `players` = list-of-dicts per team) that
      the dedup script correctly skipped rather than guess at — normalize these into the flat one-row-per-player
      canonical shape, mirroring the fixture_events schema-normalization approach already used for Finding 2/the
      fixture_events re-fetch campaign (repo: instruments-service). (2) 1,298/26,687 (~4.9%) manifest-`captured`
      `PLAYER_STATS` cells have NO corresponding GCS object, concentrated in the 2019 writer-generation era —
      investigate root cause (read-only census: manifest row vs live GCS listing, cross-reference the 2019-era
      writer-generation quirks already on file) and either reconcile the manifest entries to an honest status or
      document why they're unrecoverable; do NOT silently re-mark them without evidence. Both are
      read/investigate-then-fix passes over disjoint cell sets from the same follow-up note, safe to run as one combined
      unit (no shared-file race). **Done when**: (1) a re-census of the 3,274 nested-schema cells shows 0 remaining
      nested-schema `player_stats` objects (or a documented unrecoverable subset), full `quality-gates.sh` green on any
      writer/normalization code touched; (2) the 1,298 missing-GCS cells have a written root-cause finding + manifest
      reconciliation action (or explicit non-actionable ruling) landed as a follow-up note in this issue doc or a linked
      issue doc. Source: `plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (Finding 1 —
      RESOLVED 2026-07-25 section, "Two things found during this pass").
- [ ] [DIAG] P3. Escalate the confirmed 2026-06-21..24 odds_api raw-ingestion gap (MDPS `odds_horizon_bucket` shard4
      reprocess: all 4 dates have only `instrument_type=sport` meta-snapshot objects under
      `pipeline_mode={batch,live}_odds_api` in the raw bucket — zero real `instrument_type=odds` `data_type=trades`
      objects, directly verified via `gcloud storage ls -r`) to the odds_api raw-ingestion pipeline owner. Write a short
      escalation issue doc under `plans/active/issues/` (e.g. `odds_api_raw_ingestion_gap_2026_06_21_24_<date>.md`,
      repo: market-tick-data-service) that: (1) cites the 4 exact dates + the raw GCS paths checked (both pipeline_mode
      variants) as evidence of the meta-only gap; (2) states this was surfaced as a `RAW_ODDS_SHAPE_UNRECOGNIZED` /
      `attempted_failed` classification during the MDPS `odds_horizon_bucket` league_id-casing-migration reprocess
      (source doc below), not a script defect; (3) cross-links back to
      `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md` and notes the P2 shard4 retry item there
      stays open/time-gated until this gap is resolved upstream. Do NOT attempt to backfill or re-derive any data — this
      todo is escalation/documentation only. Source:
      `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md` (P3 item). **Done when**: the new
      escalation issue doc exists with the 3 required elements above, is committed, and is cross-linked from both
      directions (new doc → source doc's `related:` frontmatter gets the new doc added; new doc's `related:` cites the
      source doc).
- [ ] [DATA] P3. **Root-cause, measure, and (if material) de-dup canonical sports MDT odds poll-key duplicate rows**
      (repo: market-tick-data-service). Step 1: on a fresh reproducible sample (or manifest-driven population
      measurement — single-walk discipline, do not re-walk the corpus ad hoc), confirm the duplication mechanism
      (writer-side retry/multi-write vs. merge-time artifact) and the true affected-object rate/count for canonical
      `market-data-tick-sports-prd-central-element-323112` odds objects on poll key
      `(event, market, outcome, bm_time, price, fetch_utc)`. Step 2: if the measured scope is material, run a scoped
      one-off de-dup rewrite mirroring the already-shipped `player_stats` fix pattern (`instruments-service@210d4567`,
      `scripts/dedup_canonical_player_stats_2026_07_25.py` — safe no-op on already-clean objects), reading affected
      objects, de-duping on the poll key, re-writing, and verifying by content. If step 1 finds the scope immaterial,
      stop there and record the measured rate as the resolution (no rewrite needed). Source:
      `mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md`. **Done when**: the population-wide duplication
      rate/mechanism is measured and reported, AND either (a) scope was immaterial and that's recorded as the closing
      rationale, or (b) a re-run over the affected population confirms 0 poll-key duplicates remain.
- [x] ✅ [DATA] P1. Determine whether the canonical `batch_odds_api` sports capture pipeline is STILL susceptible to the
      confirmed 2022-09-07…2022-10-01 capture-outage pattern (the doc's own re-measurement superseded the original "92%
      under-capture over 2022-03-07…2023-04-30" headline — the real, re-measured gap is 550,062 legacy-only keys on 32
      of 1,837 days, dominated by that contiguous outage). The legacy `market-data-tick-sports` bucket that held the
      missing rows was permanently deleted 2026-07-17 (operator-confirmed deliberate abandonment 2026-07-25) — recovery
      of the lost rows is NOT possible and NOT in scope; this todo is forward-looking only: (a) inspect the current
      odds-capture adapter/scheduler logic (`odds_api_adapter.py` + whatever orchestrates the `batch_odds_api`
      June-campaign-successor capture) for a mechanism that could silently skip/under-fetch the pre-match horizon grid
      for a contiguous multi-day window the way the 2022-09 outage did; (b) measure recent (last 90 days) canonical
      pre-match key density per day against the same whole-day KEY-LEVEL containment method this doc used
      (`or5b_wholeday_check.py`-style: legacy... N/A now, so instead check day-over-day density/count anomalies in the
      canonical `batch_odds_api` capture itself) to see if any day drops to near-zero density the way the outage days
      did; (c) write a short disposition (root cause found + fixed / root cause found + still live + operator flagged /
      no reproducible mechanism found, campaign healthy) into a new issue doc
      `sports_batch_odds_api_capture_outage_recurrence_check_<date>.md`, citing this doc's SUPERSEDED-banner numbers (32
      days / 550,062 keys) as ground truth, not the original 92%/14-month headline. Source:
      `mdt_legacy_canonical_row_gap_2026_07_16.md` (Loose ends #1, "BIG FINDING → operator + own issue doc"). Done when:
      the new issue doc exists with a stated verdict on whether the outage mechanism is still live, and — if it is — the
      operator has been notified per the data-pipeline-correctness-hard-rule big-finding trigger. **Resolution
      (2026-07-26, slot 8)**: NOT the same 2022 mechanism (that one — the swallowed per-timestamp fetch error in
      `odds_api_adapter.py` — was traced and found largely mitigated by an independent sentinel safeguard) — a
      DIFFERENT, currently-live, more severe bug was found and fixed: `TickDataHandler._check_early_exit`'s future-date
      guard blocked 100% of same-day sports odds capture, unconditionally, since ≥2026-06-11 (live-verified via GCP
      logs: every dispatch today logged `DATA_NOT_AVAILABLE: date=2026-07-26 is in the future`). 90-day manifest density
      confirmed a ~94% collapse vs the same calendar window in 2024/2025. Fixed + tested + shipped
      `market-tick-data-service@410d7569`. Full writeup + operator-decision items (deploy confirmation + historical-gap
      backfill call) in `plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` —
      `unified-trading-pm@7c94a8d14`.
- [ ] [SCRIPT] P3. Root-cause WHY `quality-gates.sh`'s function/class/method SIZE CHECK (phase 5) didn't block the
      2026-07-16 sports-orchestrator function-size regression at commit time (candidate commits `a66fc295`, `493393c8`,
      `86cc71ff`, all instruments-service, same day) — determine whether it was the green-content SENTINEL SKIP
      (tree-identical-to-last-green reuse) vs a `QG_SLICE`-scoped gate run that excluded phase 5 vs a different
      mechanism, by inspecting the actual quickmerge/CI run logs or sentinel state for those commits. Then check whether
      `qg_sentinel_environment_blind_2026_07_23.md`'s planned sentinel-hardening fix (binding `ENVIRONMENT`, and
      generally gate-affecting config, into the sentinel hash) would also have caught/prevented this class, or whether
      this is an independent sentinel-skip mechanism needing its own separate fix — note which, citing the specific
      sentinel/gate code path. Source: `qg_size_gate_sentinel_skip_root_cause_2026_07_25.md`. Done when: the doc is
      updated with (a) the confirmed mechanism (sentinel-skip / scoped-gate / other) that let the 2026-07-16 regression
      ship, (b) an explicit verdict on whether `qg_sentinel_environment_blind_2026_07_23.md`'s fix subsumes this gap or
      this needs its own fix, and (c) if it needs its own fix, a follow-up todo/issue doc is filed for it (or the doc is
      marked resolved if no further code change is needed) — both acceptance-list checkboxes flipped `[x]` with
      evidence.
- [ ] [DATA] P1. **Refresh the batch_footystats/ODDS_API orphan-object disposition to `yes-twin-confirmed` and close the
      doc's provenance gap.** (1) Run the already-built, already-smoke-tested read-only census script
      `market-tick-data-service@c03890b3`'s
      `scripts/sports/league_id_relocation/census_footystats_orphan_content_2026_07_25.py` over a `--days-file` covering
      the remaining ~1,616 days (the archived doc `sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`'s
      original 1,815-day scope minus the 199 already-merged gain days) — do not re-derive the comparison logic, the
      script already exists and matches this doc's manual findings on 2022-06-15/2024-12-01. Refresh the doc's
      5-part-proof `Part 2 content` line from sample-based to exhaustive, and flip `Disposition` to `yes-twin-confirmed`
      if the full run reconfirms 0 unique-legacy-keys; if it finds drift (new non-duplicate days), report that as a
      distinct finding instead of silently keeping the stale disposition. (2) Separately re-examine the archived doc's
      280-day "adds-keys-but-zero-derive-gain" bucket (excluded from this doc's delete-suggestion) and record its own
      disposition (does NOT change the delete recommendation for the 1,616-day pure-duplicate bucket). (3) Trace the
      exact commit/process (candidates: `prune_phantom_soccer_manifest_rows_2026_07_22.py` or
      `manifest_swap_2026_07_22.py --apply-prod` per `unified-trading-pm@8c0f34b31`'s Progress Log) that purged the
      42,476 mis-stamped manifest rows between 2026-07-17 and 2026-07-25, and record the finding for the record (not
      blocking). Update this doc's three `- [ ]` todos to `[x]` with evidence as each completes; do NOT execute or stage
      any actual GCS delete — that remains human-only per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §
      3.1 and is explicitly out of scope for this todo. Source:
      `sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md`. **Done when**: the census script has
      run against all remaining ~1,616 days with output recorded in the doc, the 280-day bucket has its own recorded
      disposition, the manifest-purge commit is identified (or the search is documented as exhausted with no commit
      found), and the doc's 3 todos are flipped to `[x]` (leaving only the still-human-gated actual delete decision
      open).
- [ ] [DOC] P2. Close out `issues/sports_batch_footystats_swap_wrong_script_2026_07_25.md` as superseded: its claim that
      `merge_migrated_odds_into_canonical_2026_07_17.py` was never run (based on one missing manifest shard path) is
      contradicted and outweighed by two independently-corroborating, same-day re-verifications —
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s "Step (4) batch_footystats copy+swap — CORRECTED 2026-07-25
      (slot 7)" section (citing `market-tick-data-service@75f226e8`, 0 rows lost, acceptance-tested) and
      `issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md` (independent manifest census
      confirming ZERO rows remain for the `source=ODDS_API`/`pipeline_mode=batch_footystats` population, plus a
      content-compare on `day=2022-06-15` confirming pure duplication). Do NOT run the merge script again (would be a
      wasted/risky duplicate PROD write against already-migrated data). Verify: (a) confirm commit `75f226e8` exists in
      `market-tick-data-service` history and touches the relevant merge path, (b) re-run the manifest census check from
      the orphan-delete-staging doc to confirm the `source=ODDS_API`/`batch_footystats` population is still at zero
      rows. If both hold, flip this doc's `status` to `resolved`, strike all 3 open todos with a note pointing to
      `issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md` as the sole remaining
      (human-gated PROD-delete) work, and do NOT separately edit batch2's todo text (todo #3 here) since batch2 already
      self-corrected via its own "CORRECTED 2026-07-25" addendum. Source:
      `sports_batch_footystats_swap_wrong_script_2026_07_25`. Done when: the doc's frontmatter `status` is `resolved`,
      its 3 todos are struck/annotated as superseded, and it cites both corroborating docs as the resolution.
- [ ] [DATA] P2. Add the 4 leagues unique to slot-9's diverged unpushed commit (71d6a787) that origin's current
      `unified_api_contracts/canonical/domain/sports/league_data_other.py` still lacks — `FAROE_ISLANDS_PREMIER_LEAGUE`,
      `FAROE_ISLANDS_CUP`, `WALES_PREMIER_LEAGUE`, `WALES_FAW_CHAMPIONSHIP` — following the existing curated-universe
      entry pattern (same top-flight/below/cup WebSearch-verification rigor slot-9 used); bump the two sports
      structural-gap test counts (`tests/unit/sports/test_sports_structural_gaps.py`, `tests/unit/test_mvp_scope.py`) by
      +4 (not +43 — do NOT rebase+push 71d6a787 wholesale, it would duplicate the 23 league_ids origin already has via
      a04996fd). Ship via quickmerge to unified-api-contracts. Then, liveness-gate slot-9's worktree
      (`.tabs/9/unified-api-contracts`, dead worker last_ping 2026-07-25T04:15Z) to confirm it is still dead, and if so
      reset it to origin/live-defi-rollout (its committed work is now fully superseded: 23 dup + 4 re-added properly, so
      nothing unique is lost). Source: `sports_curated_universe_faroe_wales_leagues_missing_slot9_dup_2026_07_25.md`.
      Done when: all 4 league_ids resolve in the origin curated universe, the sports structural-gap tests pass with
      counts adjusted by exactly +4, and slot-9's worktree is confirmed either still-live (skip reset, re-note) or reset
      to origin with no unique commits lost.
- [x] [OPERATOR] P2. Purge the always-empty manifest rows/shards left behind by the § A2 dead-dimension deletion
      (features-service@d564bf6f already deleted `export_players`/`export_coaches`/`export_referees`/`export_rounds` and
      their column registrations — DONE, verified) for the four dimension groups PLAYERS / COACHES / REFEREES / ROUNDS
      (~4,216 `empty_confirmed` dates each, ~16,864 manifest rows total) so they stop inflating the sports coverage
      denominator. Dry-run first (list the exact manifest keys targeted, confirm each is `empty_confirmed` with zero
      real captured rows for that group), then delete via the standard manifest-purge path per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (manifest-only mutation — no GCS objects exist for
      these groups since they were structurally unpopulatable stubs, never real writes). Source:
      `plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md` § A2. Done when: a post-purge manifest
      census shows zero PLAYERS/COACHES/REFEREES/ROUNDS rows remaining for sports, and the sports coverage-denominator
      calculation no longer counts them (confirm via the honest-coverage tooling / data-status view). **DONE —
      features-service@bf088de1 (2026-07-24T21:09Z, checkbox-drift-only fixup 2026-07-26).** The purge already ran to
      completion 2 days before this batch was drafted; this todo had gone unflipped. Re-verified live 2026-07-26:
      pre-purge backup
      `gs://features-sports-prd-central-element-323112/_index/purge_backups/_index__availability_index.parquet.20260724-203626.bak.parquet`
      confirms the exact pre-state — 16,864 rows across `feature_group` in `{players,coaches,referees,rounds}` (4,216
      each), **100% `capture_status=empty_confirmed`, zero real captured rows** — matching this todo's predicate
      exactly. Current live consolidated index (`_index/availability_index.parquet`, 242,065 rows) + the sole per-VM
      shard (`_index/per_vm/legacy_seed.parquet`) both show **0** rows for all four `feature_group` values — the
      coverage denominator (computed directly off this index) no longer counts them by construction. No further action
      needed; not re-running `--apply` (would be a no-op against an already-empty target). **Note**: the source A2 issue
      doc's own mirror checkbox was NOT flipped in this pass — `sports_features_layer_findings_sweep_2026_07_18.md` is
      already 1,846 lines (pre-existing, over the plans/active/ 1,000L hard cap), and `check_line_caps.sh`'s prek gate
      blocks staging ANY edit to an already-over-cap file, regardless of diff size — this is a pre-existing
      corpus-hygiene debt unrelated to this todo, out of scope to fix here (would require splitting that doc).
- [x] [DATA] P1. ✅ 2026-07-26 — `instruments-service@e0b48bc2`. Root-cause and resolve the 4,991 phantom
      `capture_status=captured` FIXTURE_EVENTS manifest rows (concentrated 2019-2020, instruments-service) that have NO
      backing GCS object at any candidate path (canonical, pipeline_mode-aware, or legacy
      `sports_reference_v1_archive`). Sample `written_at`/`enumerator_run_id` on the affected rows against deploy
      history for that era to determine whether the 2019-2020 writer ever persisted these objects or marked `captured`
      without a write. Then, per row: (a) if the fixture is recoverable, genuinely re-fetch from api-football via the
      same `--recovery-fixture-ids` mechanism used by the fixture_events schema-heterogeneity re-fetch campaign
      (coordinate scheduling with any then-active fixture_events re-fetch VM to avoid launch contention / quota
      collision — see `issues/sports_fixture_events_refetch_progress_2026_07_25.md` for that campaign's live state), or
      (b) if genuinely unrecoverable, flip `capture_status` to `attempted_failed`/`expected_unattempted`
      (honest-absence, CAS-safe write) — never leave a row silently mis-marked `captured`. Also note whether the same
      era's writer-generation bug explains the related `instrument_count` semantic-drift finding in
      `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`. (repo: instruments-service). Source:
      `sports_fixture_events_phantom_manifest_rows_2026_07_25.md`. **Done when**: root cause is documented, and every
      one of the 4,991 rows either has a real backing object or an honest non-`captured` status, confirmed via a
      re-census.
- [x] [OPERATOR] P2. Fold the sibling `entity=fixtures` and `entity=fixtures_outcomes` non-canonical
      `league=169`/`league=235` GCS objects (21 rows: 12 `FIXTURES` + 9 `FIXTURES_OUTCOMES`, same 12-date/2-league
      cohort already folded for `entity=fixtures_schedule` in `instruments-service@4412e576`) into their canonical
      `league=CHINA_SUPER_LEAGUE`/`league=RUSSIA_PREMIER_LEAGUE` counterparts (repo: instruments-service). The fold
      script is already written and dry-run verified against live prod GCS (21/21 sources found, 21/21 canonical targets
      absent — pure move, zero overwrite risk): `instruments-service@1511b672`,
      `scripts/fold_china_russia_league_raw_id_folders_fixtures_siblings_2026_07_24.py`. **`[OPERATOR]` justification
      (stated safe-idempotent basis, no separate design decision needed)**: the prior escalation (`BLK-4c0c944b`) asked
      whether a manifest-consolidator cron pause was needed before `--apply`; follow-up research already answered this —
      the sibling precedent (`instruments-service@4412e576`, `entity=fixtures_schedule`) used the same
      per-VM-shard-writer pattern with NO cron pause, this fold's write pattern is structurally disjoint from the
      canonical index (cannot race the consolidator), and the general TOCTOU race class is separately fixed fleet-wide
      (`unified-trading-library@14301571`) — so `--apply` runs directly using the identical backup-copy →
      `record_captured()` → verify → delete recipe as the already-completed `fixtures_schedule` fold, with an explicit
      backup snapshot under `sports_reference/_purge_backups/` as the safety net (this bucket has no soft-delete).
      **Done when**: all 21 canonical objects exist and verify (size+crc32c parity vs. backup), all 21 raw-id
      (`league=169`/`league=235`) originals for `entity IN (fixtures, fixtures_outcomes)` are gone, 21 backup snapshots
      exist under `_purge_backups/`, and the manifest carries 21 `captured` rows for the canonical
      `(date, entity, league)` keys — independently verified via a fresh GCS listing, not just the script's own internal
      checks. Source: `sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24`. **DONE 2026-07-26T01:54Z
      — `--apply` executed (operator-authorized in-session; the plan's own `[OPERATOR]` justification only covered
      skipping a consolidator-cron pause, not the delete-safety codex's independent prod-bucket-delete hard stop —
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1 — so this required an explicit same-turn
      operator authorization naming that specific stop, obtained before `--apply` ran).** Fresh dry-run re-verify
      immediately prior to `--apply` reconfirmed 21/21 sources present, 21/21 canonical targets absent, 0 aborts.
      `--apply` output: `FOLD COMPLETE — 21/21 shard(s) copied+recorded+deleted, 0 remaining raw-id     objects.`
      **Independent fresh-listing verification (not the script's own internal checks)**: 21/21 canonical objects
      present; 21/21 raw-id (`league=169`/`league=235`) originals confirmed gone; 21/21 backup snapshots under
      `sports_reference/_purge_backups/2026_07_24_league_fold_fixtures_siblings/` present with size+crc32c parity vs.
      the canonical objects; the per-VM manifest shard (`_index/per_vm/league-fold-fixtures-siblings-20260724.parquet`)
      carries exactly 21 rows, all `capture_status=captured`, keyed to the canonical `(date, data_type, league_id)`
      triples.
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot-7, `data_engineering`) — this todo's own VM reference was STALE; the issue
      doc had already moved past it.** `af-backfill-20260726-000946` (this todo's named VM) died `exit_code=137` hours
      before I picked this up and was superseded TWICE in the issue doc's own Progress Log (→
      `af-backfill-20260726-004904` e2-highmem-8 → root-caused a SECOND, deeper bug (OOM + a freshness-routing mismatch)
      → `af-backfill-20260726-013313`, the fix-verified VM). The issue doc's own P1 checkbox was ALREADY `[x]` with a
      "Re-scoped done-when": VM-to-full-terminal-completion is explicitly NOT this issue doc's done-when anymore —
      that's `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s curated-universe-backfill todo (weeks-scale, already
      tracking `-013313` as its own "step 2"). Live-verified anyway (`gcloud compute     instances list` + `run.log`
      tail, 2026-07-26T01:23Z): `-013313` RUNNING, healthy, `last_completed_date=2020-07-06`,
      `0 entities = 0 calls queued` (zero-leak, entity-scoped), no action needed here. **P2 audit done**: (a) the 08:12Z
      quota exhaustion (`af-backfill-20260725-032253`) was a DIFFERENT, already-tracked bug (per-fixture
      hard-failure-swallowed-as-`[]`), not this mechanism; (b) `-013313` is the ONLY currently-running sports backfill
      VM and is confirmed fix-safe — no other in-flight VM to check/stop. Flipped both remaining todos +
      `status: resolved` in the issue doc itself:
      `sports_freshness_preflight_stale_scope_escape_burns_shared_quota_2026_07_25.md`.
- [ ] [DATA] P2. Backfill the 3 odds-api league gaps surfaced by the api_football wipe — `soccer_uefa_champs_league`,
      `soccer_china_superleague`, `soccer_russia_premier_league` (2025-H2 golden window + any in-scope gap-dates behind
      the former 112,653 api_football failures) — via odds-api (`batch_odds_api`, the canonical sports-odds source), not
      api_football. UEFA Champions League is the notable/highest-priority league. Source:
      `sports_golden_window_attempted_failed_remediation_2026_06_24.md` (Fixes item "#5 odds-api backfill gaps",
      RE-TRIAGE 2026-07-23 confirms still open). Done when: `batch_odds_api` manifest rows for all 3 leagues show 0
      `attempted_failed`/gap-days across the golden window (2025-09-01..2025-11-30) and any other in-scope 2025-H2
      gap-dates, verified against the `_index` manifest (not a re-derived count).
- [ ] [CODE] P1. **Close the 3 non-blocked, non-superseded open items from
      `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`'s RE-TRIAGE ("Open Todos" section, re-verified 2026-07-25).**
      Three independent fixes, different files/services, safe as one combined todo (do NOT further fan out): (a)
      **`_apply_ht_odds_pit_gate` default-cutoff branch unreachable in prod** —
      `features_service/sports/exporters/odds_features_exporter.py` guards the only call site with
      `if ht_break_minutes:`, so the `if not ht_break_minutes:` default `-55` branch never runs, meaning post-kickoff
      odds flow into HT features completely ungated whenever HT-break times are unknown (measured: 12,463 T-0 rows at
      `bm < -55`, worst -374.6 min). Either call `_apply_ht_odds_pit_gate` unconditionally (letting its documented
      default apply) or delete the dead default branch — pick whichever preserves existing gate behavior for the
      `ht_break_minutes`-known case, add/extend a regression test proving the gate now fires when `ht_break_minutes` is
      falsy. (b) **Re-calibrate `verify_ml_readiness.py`'s flat 95% non-NULL threshold**
      (`features_service/sports/compute/ml_readiness_check.py:29`, `NON_NULL_THRESHOLD: float = 0.95`) — post-purge,
      T-24h rows legitimately carry NULL for all closing-derived columns
      (`clv_*`/`odds_movement_*`/`velocity_*_1h_to_0`/`steam_*`), so the flat threshold is now structurally unmeetable
      (currently fails 1,683/1,860 dates at ~69-80%) and measures the wrong thing. Re-base the gate per-horizon on the
      columns each horizon can honestly know (`FEATURE_HORIZONS[h]` / the `min_horizon` registry) — do NOT just lower
      the number, that's the anti-pattern this todo explicitly forbids. (c) **Retrain the CLV models** (ml-service) now
      that their stated prerequisite — the ODDS_FEATURES recompute (1,524/1,861 dates purged, 2026-07-17) — is confirmed
      done. The 3 currently-quarantined artifacts (`ml-service@c0603cb`) stay in place as the reference for what the
      leak produced; do not promote or cite them until the retrain lands and is independently verified. Explicitly OUT
      OF SCOPE for this todo (do not touch): the doc's item (2) blank-`fixture_id` upstream-writer fix — very likely
      ALREADY FIXED by `market-tick-data-service@3401c0ab` (batch2, `_build_fixture_rows()` now stamps `fixture_id`
      alongside `af_fixture_id` at the exact write path the doc names) even though the doc's own re-triage text (same
      day, order ambiguous) still calls it open — verify against `market-tick-data-service@3401c0ab` before doing any
      further work here, do not duplicate; and the doc's item (4) T-0 shard manifest reconciliation — structurally
      blocked on the sports legacy-bucket-cutover's T6.1 merge of `_index/per_vm/cutover-move-20260716.parquet`,
      confirmed still unmerged as of the cutover's own 2026-07-24 history doc — not eligible for dispatch until that
      merge lands. Source: `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`. **Done when**: (a) a regression test
      proves the PIT gate fires on the `ht_break_minutes`-unknown path and the chosen fix (unconditional call vs.
      dead-branch delete) is committed; (b) `ml_readiness_check.py` computes its non-NULL threshold per-horizon against
      the honest matrix (not a flat 0.95) and the gate's pass/fail on the current corpus is re-measured and reported;
      (c) a CLV retrain run completes post-ODDS_FEATURES-recompute, is independently re-verified (not just claimed), and
      the 3 quarantined artifacts remain untouched/unpromoted; `quality-gates.sh` green on every touched repo.
- [ ] [DATA] P1. Resolve the sports odds manifest-routing regression opened by the 2026-07-24 addendum to
      `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`: (1) grep+READ the manifest-write target
      resolution in the sports capture path in market-tick-data-service (same class of `_resolve_manifest_bucket()`
      logic documented in `sports_phantom_audits_reference_not_marketdata_2026_07_14.md`) to determine whether
      `market-data-tick-sports-prd`'s manifest writes for `batch_odds_api` (and every other sports `pipeline_mode`) were
      DELIBERATELY re-routed to `instruments-store-sports-prd` around 2026-07-20/21 (a real code/config change) or are
      an unintended regression -- confirm across the full population, not just the two data points the addendum
      measured; (2) separately investigate the 2026-07-21→2026-07-23 GCS-side writer gap for
      `pipeline_mode=batch_odds_api/asset_group=sports/` (zero venue prefixes on disk for those 3 dates, confirmed by
      direct listing) -- a real fetch/write gap distinct from the manifest-routing question; (3) once (1) is answered,
      record a disposition recommendation for `market-data-tick-sports-prd`'s now-possibly-stale `_index/`: either (a)
      leave it as a documented stale historical artifact, or (b) backfill/repoint it so single-bucket tools (orphan
      sweep, this skill's default Phase-0 methodology, any future `market-data-tick-sports-prd`-scoped reconciliation)
      stop producing a false orphan signal for sports specifically -- if the right disposition is genuinely undecidable
      from the code/data alone (not just unimplemented), state that explicitly and stop rather than picking one
      autonomously. Repo: market-tick-data-service (routing investigation + gap investigation); unified-trading-library
      / market-tick-data-service (disposition, if a code change is warranted). **Done when**: todo 6's manifest-routing
      question is answered (deliberate change vs regression) with a fix or documented rationale if regression; todo 7's
      3-day GCS gap is investigated and its cause reported (or explicitly marked unexplained with evidence gathered);
      todo 8's `_index/` disposition is either implemented or, if it needs an operator call, escalated with the
      recommendation stated rather than left silent; all three findings are recorded as a new dated section in
      `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`, and the doc's frontmatter `status` is
      flipped to `resolved` if all three are closed (or left `open` with the remaining item named). Source:
      `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`.
- [ ] [DATA] P3. Flip the still-unchecked "NEW compute: add per-bookmaker raw decimal-odds retention...
      `decimal_odds_<outcome>_<venue>`" todo (`- [ ]` at line ~110-114) in
      `plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md` to `[x]` with a SHIPPED annotation citing
      `features-service@b03a6de4` (the commit that added `_pivot_bucketed_to_fixture()`'s per-bookmaker
      `odds_decimal_<outcome>_<venue>` emission + the `export_odds_features()` merge-back fix, per
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s own SHIPPED ledger for this exact todo) — this is a
      checkbox-drift-only fix on the PARENT plan (its own checkbox never got flipped even though the work shipped and
      batch2's separate copy of the checklist did get marked SHIPPED there). Verify current repo state first (grep
      `features_service/sports/calculators/odds_columns.py`/`odds_features_exporter.py` for `odds_decimal_` columns)
      before flipping, in case of further drift since 2026-07-25T14:20Z. Source:
      `sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25` (issue doc's Recommended-next-step
      item 1). Done when: the parent plan's line-110 todo reads `[x]` with a commit citation matching real repo state,
      and `quality-gates.sh` (prek-only, doc change) is green on the plan-file edit.
- [ ] [DATA] P2. **market-tick-data-service + market-data-processing-service + features-service: execute the zombie-tick
      purge/re-derive + close out ML-readiness verification, using batch4's sweep report as input.** Once
      `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s read-only P1 sweep todo (source: this doc) has produced its
      contamination report — repeated (fixture_id, bookmaker_key, kickoff_utc) tuples spanning multiple `day=`
      partitions in
      `processed/by_date/*/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/`,
      discriminated from honest single-snapshot-real-fixture rows via `staleness_seconds`/`|fetch_utc − kickoff_utc|`
      (years-scale = zombie, ≤~26h = genuine, per this doc's tick-4 refinement) — (a) snapshot the identified
      contaminated shards first, then purge/re-derive them plus their downstream `odds_features` and manifest rows via
      the manifest index (single-walk discipline: no fresh whole-corpus GCS walk), re-deriving through the
      now-staleness-cap-fixed `bucket_assignment_adapter.py` (`mdps@aa6e8ac`) so the corrected pipeline regenerates
      clean buckets; (b) re-run
      `verify_ml_readiness.py --start-date 2025-09-01 --end-date 2025-11-30 --bucket features-sports-prd-central-element-323112`
      and confirm the 17 originally-failing dates clear or shrink to genuine honest-absence-only misses; (c) implement
      the two-part gate-semantics fix this doc specifies: zero-in-window-fixture days pass vacuously (or skip via an
      expected-fixture count derived from instruments-service fixtures) instead of scoring as failed-empty, and the
      per-date non-null-cell-count check exempts `WRITE_GATE_CONFIG.sparse_columns["odds_features"]` prefixes (the
      already-verified 43-column always-null cluster set, 0 unmatched against that config) — this also fixes the
      shallow-ladder partial days (e.g. 2025-10-20 at 91.1%). Do NOT purge the single-snapshot real-fixture class (e.g.
      the 2025-10-23 China Superleague pair) — honest data, not contamination. Source:
      `sports_odds_stale_fixture_reinjection_2026_07_14.md`. Done when: the sweep-identified contaminated shards are
      purged/re-derived with a before/after manifest census showing only the intended cells changed,
      `verify_ml_readiness.py` re-run output is posted showing the 17-date failure set cleared/shrunk with the remainder
      attributable to genuine honest-absence, and the two-part gate-semantics fix is shipped + QG-green with a
      regression test covering a zero-in-window-fixture day passing vacuously and a sparse-column day no longer flagged.
- [ ] [CODE] P2. **Build the remaining Part 3 safety tooling (excluding the CAS mechanism, already tracked) and unskip
      §2.2's data_type vocabulary guard.** Direction is fully decided (§4.3 ✅ DECIDED 2026-07-22 — lowercase
      `data_type` canonical; §4.1/4.2/4.4 also closed) — nothing left here is a judgment call, only unbuilt
      implementation. Scope: (a) build the three still-missing Part 3 safety-tooling pieces the RE-TRIAGE (2026-07-23)
      names as genuinely unbuilt — row-identity assertions for the purge/relabel/drop scripts, a consolidator-paused
      pre-flight check, and a `coverage_drift.py` pre-notify mechanism — plus a `--dry-run` mode on the 3.2/3.3/3.4
      remediation scripts; (b) in `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`,
      remove the uppercase `"ODDS"`-family case-variant entries from `DATA_TYPES_BY_ASSET_GROUP["sports"]` (keep only
      the lowercase forms) and un-skip `unified-api-contracts/tests/unit/test_sports_data_type_vocabulary.py` (drop the
      `_SKIP_REASON_K0B` gate) per §2.2. Do NOT build or duplicate the cross-object-CAS+alarm mechanism itself — that is
      already a tracked open todo (`sports_consolidated_closeout_2026_07_19.md`, "NEW 2026-07-23 (decision 12)"). Do NOT
      execute any actual manifest purge/relabel/drop against prod (3.2/3.3/3.4 remain gated on the standing human-only
      execution trigger per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) — this todo is build-only.
      Source: `sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (RE-TRIAGE 2026-07-23 section + §2.2). Done
      when: the four safety-tooling pieces exist as reviewable code/scripts (dry-run mode included) with unit tests, the
      uppercase `ODDS`-family entries are removed from the sports data_type registry,
      `test_sports_data_type_vocabulary.py` runs unskipped and green, and both repos' `quality-gates.sh` are green —
      with no manifest/GCS write performed.
- [x] ✅ [BACKEND] P2. **DONE 2026-07-26 (slot-7, `backend_engineer`) — Close the T6.8 one-off-retirement residual
      (items 1 + 3; item 2 already done).** (a) v9 cluster: workspace-wide import-graph (all repos) found only docstring
      hits outside the cluster. **KEPT** `migrate_sports_canonical_v9.py` + its 2 imported helpers
      (`_migrate_mdps_reconcile.py`/`_migrate_sports_reconcile.py`) + tests — E8 below still needs to implement
      `--drop-stale` in this exact file (confirmed still a log-stub, E8 not landed). **DELETED** the self-consistent
      2026-07-13 sub-cluster, each Delete-when re-verified against the archived canonicalisation plan's progress log:
      `migrate_sports_instruments_legacy_gap_2026_07_13.py` (`written_captured=31301/31301`, IS L6-REAL residual=0),
      `fix_sports_instrument_count_zero_anomaly_2026_07_13.py` (49/49 verified, 28/77 honest accepted-phantom),
      `write_sports_instruments_legacy_gap_manifest_2026_07_13.py` (same L6=0 evidence, leaf), and
      `fix_sports_fixtures_venue_blank_2026_07_13.py` (718 rows applied, audit-verified 0 FIXTURES legacy-only, leaf).
      Shipped `market-tick-data-service@f1bfd991`. (b) All 6 instruments-service one-offs hardcode
      `BUCKET_NAME="instruments-store-sports-central-element-323112"`, permanently deleted 2026-07-16 (T5.4) —
      live-reconfirmed 404 this session, no `--bucket` override anywhere. **DELETED all 6** + orphaned test + 2 report
      JSONs (same disposition as the already-deleted `verify_v1_archive_row_coverage_2026_06_27.py`). Shipped
      `instruments-service@4987e465`. Dropped the 2 deleted files from `sports_consolidated_closeout_2026_07_19.md`
      Track E's repoint list (moot). Tooling gap found + filed (not fixed, outside craft scope):
      `quickmerge.sh --agent --files` errors on an already-fully-committed pure-deletion commit —
      `plans/active/issues/quickmerge_agent_files_pure_deletion_gap_2026_07_26.md`. Source:
      `sports_t6_8_oneoff_retirement_residual_2026_07_25.md`.

- [x] ✅ [SCRIPT] P0. **DONE 2026-07-26 (slot-4, `data_engineering`) — Understat bulk backfill — close out the full
      sequential chain (§4/§6/§8).** Discovery: every substantive step of this chain was ALREADY completed via the
      sibling/successor plan `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md` (archived
      2026-07-13, literal 0/0/0 close-out) — the source issue doc's own §8 checkboxes were simply never flipped, which
      is why this AO-dispatch batch's fresh triage flagged it as orphaned. Verified (not assumed) that the 2026-07-13
      closure has held: (1) confirmed the §9.2 consolidator fix (`unified-trading-library@f5ec2291f`) is live in the
      deployed Cloud Run job `uts-prod-manifest-consolidator-instruments-sports` via image→base-image→commit ancestry
      (base UTL 0.57.0 built 2026-07-25 contains `_dedup_key_sql`); (2) fresh manifest read
      (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 5,584,073 rows)
      shows 0 duplicate groups, 0 `attempted_failed`, 0 `expected_unattempted` for big-5 XG/XG_SHOTS (captured
      6,675/6,666, ratio 0.9984) — unchanged from the 2026-07-13 baseline, 13 days later; (3) the bulk writer + full
      backfill run were both already done per the archived plan's 2026-07-06/07-08 Progress Log entries; (4) the ONE
      genuinely-open sub-item — `SPORTS_DATA_TYPE_META` registration for `XG_SHOTS` (deployment-api) — was still blocked
      on a red LDR HEAD; re-ran deployment-api QG fresh (now green), re-authored + shipped `deployment-api@b04c082`; (5)
      re-confirmed the `understat-vm-xg-complete` gate state is still green (flipped 2026-07-12, literal-0/0/0
      re-verified 2026-07-13, and again today). Full evidence + closure narrative in
      `plans/active/issues/understat_bulk_download_backfill_2026_06_29.md` §8 (all checkboxes flipped) + its 2026-07-26
      Progress Log entry.
- [ ] [DATA] P1. **Implement Sports E8 legacy-delete (`migrate_sports_canonical_v9.py --drop-stale`) + delete
      `sports_reference_v1_archive/` under an operator gate.** Implement the currently-unimplemented `--drop-stale` stub
      (line 886-891 raises) as a twin-verified per-surface delete — for both `instruments-store-sports-prd-*` and
      `market-data-tick-sports` surfaces, delete a legacy (no-`pipeline_mode`) object ONLY when its canonical
      `pipeline_mode=`-partitioned twin exists and is readable (matches the already-verified
      `migrate_sports_canonical_v9.py --apply` 1:1 legacy↔canonical parity check) — OR ship an equivalent standalone
      `gcs_delete_object` sweep with the same twin-verification. Snapshot-first (manifest `_index` snapshot before any
      delete). Include `sports_reference_v1_archive/` in the same gated sweep — already verified safe-to-delete
      2026-06-24 (archive `af_fixture_id` ⊆ canonical `af_fixture_id` across a 5-day/2018-2026 sample, canon-only=0; the
      v1 wide-denormalized bare-layout archive's data is fully represented by the v2 canonical store-id/derive-name
      pattern) — no further verification needed for that sub-scope. [OPERATOR]: the actual delete execution
      (`--apply`/`--drop-stale` firing) is IRREVERSIBLE and requires explicit operator sign-off per the doc's own
      "operator gate (IRREVERSIBLE)" note and the workspace GCS-delete-safety rule — implement + dry-run the script, do
      NOT fire the real delete without that sign-off logged in this todo's completion evidence. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` (line 289). **Done when**:
      `--drop-stale` (or the standalone sweep) is implemented + unit-tested + dry-run-verified 0-orphan/twin-safe on
      both surfaces, `sports_reference_v1_archive/` deletion is included in the plan, and either (a) operator sign-off
      is obtained + the delete executes + is verified (object counts drop, canonical reads unaffected), or (b) the todo
      is left checked-complete-for-code with an explicit `BLOCKED-OPERATOR` note pending sign-off if the operator has
      not yet approved.
- [x] [UI] P3. ✅ 2026-07-26 — `deployment-ui@66cc06d`. Relabel `FixturesBrowser.tsx`'s window note and remove the stale
      `MAX_SPAN_DAYS=120` span-cap warning now that `deployment-api/services/fixtures_browser.py` serves the
      full-history single catalogue source (`prod/catalog.parquet`, deployment-api@dbbf64c, shipped via
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`) instead of the old ≤120-day day-walk — the 120-day bound no
      longer exists. Source: `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`. Done when:
      `FixturesBrowser.tsx` no longer references `MAX_SPAN_DAYS` or shows the 120-day cap warning, the window note
      reflects the real full-history coverage (2019-01-01→present), the `[UI]` + `pw:L2` regression spec (per
      `/codex/06-coding-standards/ui-testing-layers.md`) passes, and `quality-gates.sh` is green. Removed
      `MAX_SPAN_DAYS`/`spanDays`/`span` (all dead once the cap was gone); note now reads "(catalogue covers full
      history, 2019-01-01→present — no range-length limit)." Updated the vitest test + added a new pw:L2 spec
      (`tests/e2e/data-status-fixtures-browser-full-history-note.spec.ts`, verified passing 1/1). `quality-gates.sh`
      green (101 tests, 75.53% coverage).
- [x] [DATA] P0. ✅ 2026-07-26 — unified-api-contracts@82db8f8f + market-tick-data-service@f6ea0010. **Close out
      `sports_mtds_odds_trades_index_correctness_followup_2026_07_24`'s two open findings (T2.9 schema-contract drift +
      T2.10 phantom-row disposition).** (1) **T2.9**: canonical's OWN native live-written `(sports, odds, trades)`
      objects already fail the registered MDT schema contract
      (`ts_event, fixture_id, market_type, outcome, odds_decimal, broker, client, data_source`) against the real emitted
      fields (`bm_time, market_key, outcome_name, price, fetch_utc, …`) — since the mismatch is on currently-correct
      native live writers (not a defect in moved/legacy objects), UPDATE the registered contract to match the real
      schema (do not touch the writers); verify ≥1 native canonical object now validates clean under
      `_resolve_strict_validation`. (2) **T2.10**: re-query the CURRENT `market-data-tick-sports-prd` manifest for
      `source=api_football AND data_type=trades` on BOTH surfaces separately — the merged index AND the
      `_index/per_vm/_legacy_seed.parquet` shard (do not assume the merged index proves the seed is clean; the
      2026-07-17 SLOT-3 finding showed the seed re-introduces phantoms every consolidator cycle even after a
      merged-index-only purge). If 0 rows remain on BOTH surfaces, close T2.10 citing
      `issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`'s 2026-07-23 CAS-safe wipe
      (`market-tick-data-service@e9d9dec0`) as the resolution. If any remain, strip them from `_legacy_seed.parquet`
      with the source-filtered predicate (`source=='api_football' AND data_type=='trades'`, NULL-safe COALESCE — the
      real `odds_api × trades` population, 211,313+, MUST survive untouched), back up first, let the consolidator
      re-merge, then verify by content in a separate read process. Source:
      `sports_mtds_odds_trades_index_correctness_followup_2026_07_24`. **Done when**: the MDT `(sports,odds,trades)`
      schema contract validates ≥1 native canonical object AND the manifest (both merged index and
      `_legacy_seed.parquet` shard) shows 0 `api_football × trades` `captured` rows with nonzero `instrument_count`,
      with a written disposition recorded (contract-fix commit sha; T2.10 outcome stated as either "0 remaining, closed
      via 2026-07-23 wipe" or "N phantom rows stripped from seed, verified by content, consolidator re-merge
      confirmed").
- [ ] [DATA] P2. Migrate 4 ml-service files still using pre-migration odds-feature names (missed by the earlier
      ml-service migration commits `unified-api-contracts@689efa54`/`ml-service@91f031a`, which covered only the
      `OddsFeaturesMixin` schema/loader, not mock-data generation or target generation):
      `ml_service/training/engine/mock_data_provider.py`, `ml_service/training/app/core/sports_target_generator.py`,
      `tests/training/unit/test_sports_feature_loader.py`, `tests/training/unit/test_horizon_gate_shield.py`. Apply the
      same generative naming scheme + UAC `OddsFeaturesMixin` ground-truth mapping used by the already-shipped
      features-service migration (features-service@0ded2449/e240eca2/0ab873b3) — re-derive names from the scheme table,
      don't hand-guess. Watch for the same f-string dynamically-built-column-name gap that bit the earlier FSS pass (a
      quoted-literal-only search misses `f"clv_{outcome}"`-style construction) and for the same-string-different-schema
      trap (verify which schema a given `df` actually carries before renaming a read of it — a synthetic/raw-data column
      can coincidentally share an old feature-name string). (repo: ml-service). Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`. Done when: a repo-wide grep of ml-service for any of
      the old `ODDS_COLUMNS` names (quoted-literal AND f-string-prefix forms) returns zero hits in these 4 files, and
      `quality-gates.sh` is green.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md`**: Confirmed the Phase-1 gap: §7 todo 1
  ([OPERATOR] P1, "Rule on the 1,492 v2 pre-floor rows: fold into the existing pre-floor-wipe scope … or confirm they're
  already covered by a follow-up pass") is the sole remaining uncovered item — todos 2-5 are done or explicitly closed
  by batch2 (grep-confirmed above), and the 2026-07-23 RE-TRIAGE section reconfirms it as still open/unexecuted. GENUINE
  CONFLICT found on the SAME underlying data (not just "is it cited" — a different mechanism is prescribed for the same
  rows). Two live docs carry an unexecuted `[ ]` todo to bulk-delete the entire `sports_reference_v2/by_date/` tree on
  the premise that it is "dead / frozen 2026-04-20 / no entities": - `sports_consolidated_closeout_2026_07_19.md`
  (status: active) lines 437-438: "Snapshot-then-cull the dead `sports_reference_v2/by_date/` dual-layout … Confirm no
  reader consumes it first." - `sports_consolidated_native_ao_extract_2026_07_25.md` (status: draft) lines 122-128
  mirrors the same todo verbatim as an AO-dispatch-ready "Track S" item, explicitly marked **"Self-justified, not
  [OPERATOR]-gated"** with its ONLY safety gate being a reader-check (no twin-existence check), Done-when =
  "reader-check recorded AND snapshot+delete executed with post-delete 0-objects listing." This directly collides with
  this triage doc's own finding: 1,492 of the v2 rows (the pre-floor subset) are NOT dead inert bytes — they were
  verified to still exist (15/15 sampled) with ZERO canonical twin at any path variant, i.e. they are the sole surviving
  copy of that data, and the triage doc's own 5-part delete-safety proof explicitly routes them to an OPERATOR ruling on
  folding them into the separately-already-ruled pre-floor wipe scope, NOT a generic reader-check-gated tree cull. The
  cull todo's "no entities" / "dead" premise is stale for this specific slice — a reader-check alone does not satisfy
  the delete-safety protocol's twin-existence part that this triage doc found FAILING for exactly these 1,492 rows. If
  the snapshot-then-cull todo executes first (it is unexecuted, unchecked `[ ]` in both hosting docs), it would delete
  the 1,492 rows without ever routing through the OPERATOR ruling this triage doc calls for, and without the protocol's
  twin-existence proof — a real, evidenced risk of silent data loss executed under a "self-justified" safety label that
  doesn't actually cover this sub-population. Recommended resolution (not self-executing — flagging for the
  operator/plan-owner): (1) do NOT draft this as a fresh batchable todo — drafting a competing "rule on 1,492 rows" todo
  alongside an active unexecuted "snapshot-then-cull the whole tree" todo would race two different deletion policies
  against the same objects. (2) Instead, the `sports_consolidated_native_ao_extract_2026_07_25.md` Track S todo (still
  status: draft, not yet dispatched) should be amended before it ships to either (a) exclude the pre-floor date range /
  explicitly gate on this triage doc's §7 todo 1 resolving first via `depends_on`, or (b) fold the OPERATOR ruling
  directly into its own Done-when clause (replace "Self-justified, not [OPERATOR]-gated" with an actual [OPERATOR] gate
  for the pre-floor slice specifically, leaving the post-floor/already-migrated portion self-justified). (3)
  `sports_consolidated_closeout_2026_07_19.md`'s parent copy of the same todo should get the same amendment or a
  cross-reference note pointing at this conflict. This is a plan-authoring fix (amend an existing draft/active todo's
  safety gate), not new batchable work — no candidate_todo drafted per the conflict_gated branch instructions.
- **`plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`**: Confirmed the two remaining
  items from Phase 1: (1) building a data_type-aware cross-bucket branch in `_audit_sports()`
  (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:283`) to fix the
  `trades`/`odds_horizon_bucket`/PLAYER_VALUES phantom false-positives, and (2) the unexamined ~1,335-row (0.19%)
  STANDINGS/TEAMS/XG/WEATHER/MATCHES/FIXTURES residual spot-check. Conflict check: item (2) is NOT merely uncited — it
  is already an ACTIVE, EXPLICITLY-TRACKED conflict in the covering set.
  `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s Deferred section and
  `autonomous_session_operator_decisions_2026_07_25.md` entry #8 state the residual "may share a root cause with Track
  S2's still-open 'decision 16' day-partition investigation; genuine ambiguity, not resolvable from evidence alone" —
  i.e. another in-flight track (Track S2 foldin) may already be about to resolve the same underlying mechanism via a
  different route, and which side should execute is explicitly awaiting an operator ruling.
  `batch4_finalize_2026_07_25.md` todo 2 is already machine-gated to re-check this exact item once the operator answers
  entries #5-8. Drafting a competing todo here would race that already-queued resolution path. Item (1), the
  cross-bucket branch, has zero citations anywhere in the 17-doc covering set (grepped for "_audit_sports",
  "_BUCKET_KIND_MAP", "cross-bucket", "two-card", "audit-split" — no hits outside the target doc itself), so on
  citation-overlap grounds alone it would look batchable. But it fails the dispatch-scope eligibility test on a
  different axis: the doc's own "Decision" section records an explicit operator ruling (2026-07-14): "leave code as-is,
  document only. No bucket-map change, no `--apply`, no market-data sports phantom path added in this session. This doc
  tracks the inconsistency and the unverified count for a future deliberate fix." The 2026-07-23 RE-TRIAGE reconfirms
  nothing has changed and explicitly frames the fix as still needing "a future deliberate fix" — i.e. a design/judgment
  decision the operator has not yet authorized executing, not a bounded checkable task a worker can just go build.
  Dispatching it now would reverse a standing operator decision without a fresh go-ahead — exactly the "figure out how X
  should look"/judgment-call pattern CLAUDE.md's dispatch-eligibility rule excludes from AO-eligibility. Recommended
  resolution: fold both remaining items into the operator-decisions doc as a combined ask (or extend entry #8) — the
  operator needs to (a) rule on the Track-S2/residual-spot-check sequencing already queued, and (b) explicitly authorize
  proceeding with the cross-bucket `_audit_sports()` fix (superseding the 2026-07-14 "leave as-is" decision) before
  either becomes AO-dispatchable. No candidate todo drafted; this doc stays open, awaiting the operator's ruling via the
  existing batch4/batch5 conflict-resolution pipeline.
- **`plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md`**: Genuine, currently-unresolved conflict — do
  not draft a competing AO todo. Side A (target doc): the 3 remaining ACTIVE-scope todos (manifest-schema extension for
  per-fixture capture presence; build_sports_fixture_catalogue_from_manifest(); extend catalog build to invoke
  reference-data adapters incl. api_football_reference.py fixtures/betfair.py runners) all write/derive from reference
  data under a bare `entity={fixtures,teams,injuries}/` path, and the manifest-schema design explicitly depends on
  correct `league_id` resolution. Side B (sports_consolidated_closeout_2026_07_19.md, Track S/Track E/Track V, all P1,
  currently open/active): Track S has an open todo to "Eliminate (or document) the legacy bare `entity=fixtures/` (no
  pipeline_mode=) write path" — the SAME path string the target doc's adapter-invocation todo would write more data
  into; the closeout's own Canonical-target section declares that bare path FROZEN since 2026-05-23 and explicitly names
  this exact target doc as one of 3 live artifacts currently violating that freeze. Track E is actively repointing ~9
  consumers off bare `entity=fixtures` onto the split `fixtures_schedule`/`fixtures_outcomes` naming — directly
  contradicting the target doc's plan to keep writing the bare path. Track V still tracks `league_id` canonical-form
  migration as UNRESOLVED — the exact prerequisite the target doc's manifest-schema-extension design needs and does not
  currently account for. This is not stale/superseded on either side: both are dated 2026-07-19/07-23/07-25 and both are
  open P1/P2 items today. Confirming the conflict is genuinely still open (not merely cited):
  sports_closeout_track_x_hygiene_2026_07_25.md's only todo touching the target doc is an explicit cross-link/awareness
  note whose own text says "Neither doc's design is decided by this todo; it only makes the collision/dependency
  visible... do NOT implement either resolution." The target doc itself carries a 2026-07-23 banner instructing readers
  not to design or ship its manifest-schema extension or entity path "against a stale read of either plan" and to check
  the closeout's Track C/S/E/V state first. Recommended resolution (for the operator, not auto-executable by a worker):
  decide, in one place, (1) whether the target doc's fixture-grain reference-data writes should move onto the closeout's
  `fixtures_schedule`/`fixtures_outcomes` split naming instead of `entity={fixtures,teams,injuries}/` before any
  manifest-schema-extension design starts, and (2) sequence the manifest-schema-extension design to START AFTER (not
  concurrently with) Track V's league_id canonical-form migration lands, since the schema design's own correctness
  depends on it. Until that ruling exists, none of the target doc's 3 remaining ACTIVE-scope todos are independently
  AO-dispatch-eligible — dispatching any of them risks writing/designing against the frozen path the closeout is
  actively eliminating, or against a league_id form the closeout may still change under it.
- **`plans/active/sports_legacy_fixtures_path_migration_2026_07_24.md`**: Confirmed via direct read: the doc's 7 open
  todos are P0 per-date/league census, P1 schema-mapping spot-check, P1 migration-script dry-run, P1 --apply migration,
  P1 fallback-function removal, P2 [OPERATOR] snapshot-then-delete, P2 doc-sync. Only the P0 census is even referenced
  anywhere in the covering set (Phase-1 finding), and that reference is a genuine, already-adjudicated OPEN conflict,
  not a stale/superseded mention. `sports_satellite_ao_dispatch_batch3_2026_07_25.md` (line ~257) and
  `batch4_2026_07_25.md` (line ~150) both independently flag "3 conflicts, all still open" for this exact census
  candidate against `sports_consolidated_closeout_2026_07_19.md`'s own OPEN ground: (1) Track S (closeout line ~435) —
  "Eliminate (or document) the legacy bare `entity=fixtures/` write path still active today" — if that writer is still
  live, the census's snapshot could be stale/repopulated after migration; (2) Track E (closeout line ~460) — "Repoint
  the remaining stale `entity=fixtures` consumers" (9-file sweep) — unconfirmed whether these call sites are genuinely
  disjoint from this doc's own `sports_fixtures.py` fallback-removal scope, i.e. two plans could independently touch
  overlapping consumers; (3) Track C1 (closeout line ~274, checked `[x]` but explicitly PARTIAL — 282,231/337,464
  restamped, 55,233 dedup-key collisions unresolved, tracked in
  `issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md`, still `status: open` with no operator
  DELETE-policy ruling) — the census's `data_type=="FIXTURES"` population could systematically miscount
  label-only-restamped rows as "already covered" without a real GCS object-read check.
  `autonomous_session_operator_decisions_2026_07_25.md` entry #7 formalizes this as a live, unresolved operator fork:
  Option A (worker-recommended) = dispatch the census now with an explicit scope-correction folded into its Done-when
  (verify "canonical empty" via a real GCS object read, not the manifest label alone, closing the C1 gap) vs. Option B =
  hold the census entirely until the operator first rules on the 55,233-row DELETE-policy question in the C1 residual
  doc, so the census and the eventual migration plan design together in one pass. Entry #7's **Status is `open`** — no
  ruling has been made as of this audit. This is exactly the CONFLICT CHECK step-3 case: two docs (this plan's census +
  `sports_consolidated_closeout_2026_07_19.md` Track S/E/C1) prescribe/imply different orderings for the same underlying
  fixtures-path ground, and the ordering is NOT resolvable from evidence alone — it needs the operator to pick A or B.
  The remaining 6 todos (schema-mapping spot-check through doc-sync) are all sequentially downstream of the census's
  output (the census produces the load-bearing (date, league) set every later todo consumes), so they are transitively
  gated on the same unresolved decision — none of them can be usefully batched ahead of entry #7 resolving. No
  candidate_todo drafted; this doc's orphaned work is fully accounted for as already-flagged, still-open conflict_gated
  ground (entry #7), not a fresh gap to fold into a new AO-dispatch batch.

## Note — found fully covered on re-check (Phase-1 verdict superseded, not orphaned)

- **`plans/active/issues/sports_trades_attempted_failed_2026_07_23.md`**: Not a genuine unresolved conflict — a
  duplicate-coverage finding that supersedes the Phase-1 "partial coverage" verdict. Re-grepping the full covering set
  (including the two docs Phase-1's evidence apparently didn't check, both dated 2026-07-25, one day after Phase-1's own
  2026-07-23 doc) shows BOTH remaining open items are already claimed, not just one: (1) the [DESIGN] P3 "flag
  check_high_attempted_failed owner" runbook-note item is covered verbatim by
  `sports_consolidated_native_ao_extract_2026_07_25.md` lines 280-285 — a `[DATA] P3` todo titled "Track S2 — write the
  check_high_attempted_failed runbook note for deployment-service", citing the identical
  87.2%-ratio/K1-K2-denominator-shrink content, "Done when: the runbook note is added", sourced from
  `sports_consolidated_closeout_2026_07_19.md:951-955` (status: draft, but explicitly included in the operator-supplied
  covering set as an active/draft AO-dispatch doc). (2) the [VERIFY] P3 "re-check ratio once K1/K2 fully flips + DELETE
  lands" item is covered by `sports_closeout_track_s2_foldin_2026_07_25.md` lines 200-205 as a
  `[DATA] P3 BLOCKED-PREREQUISITES` todo, explicitly "Filed: sports_trades_attempted_failed_2026_07_23.md", gated on the
  parent's Track V K1/K2 DELETE. Cross-checked both extraction docs against each other and against the parent
  `sports_consolidated_closeout_2026_07_19.md` (source of both) — `sports_closeout_track_s2_foldin_2026_07_25.md`'s own
  "Overlap reconciliation" header explicitly enumerates item (7) as "the check_high_attempted_failed runbook note
  (excluding the sibling re-check once K1/K2 DELETE executes sub-part — carried here below)", i.e. the two 2026-07-25
  docs were deliberately authored as a matched split of exactly these two items — no overlap between them, no
  different-approach conflict, both are live/consistent with each other and with the original doc's phrasing. No new
  candidate_todo should be drafted: doing so would create a genuine third duplicate of already-claimed ground. This doc
  has zero residual orphaned work once the full (including 2026-07-25-dated) covering set is considered; Phase-1's
  "orphaned_partial_coverage" verdict was based on a covering-set snapshot that predated/missed these two docs.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/data_completion_sports_2026_07_24.md`**: Confirmed the two genuinely uncovered items (lines 397-406
  rate-limit calibration probe; line 797 API-Football daily-quota bump) are NOT cited or overlapped by any doc in the
  covering set. Grep of calibrate_source_rate_limit.py / ramp-to-429 / SOURCE_RATE_LIMITS_RPM / SOURCE_PER_IP_LIMITS
  across all 16 covering-set docs returns zero hits outside the target doc itself. Grep of 'API-Football' + 'daily
  cap/quota/Custom300/1.5M' hits batch2 (lines 168, 265, 501, 702-722) and sports_consolidated_closeout_2026_07_19.md
  line 614, but those are DIFFERENT concerns: batch2's hits describe (a) enrichment coverage percentages by data-type as
  diagnostic context, and (b) a VM-stop/relaunch incident triggered by hitting the SAME daily quota ceiling
  operationally -- not a proposal to bump the ceiling itself; sports_consolidated_closeout line 614 is a scope-boundary
  ruling for the UNRELATED 2013-2018 historical window ('no further api-football spend' there), not a ruling on the
  current ~34%-honest-coverage quota-bump lever. So no duplicate/competing todo exists anywhere -- this is a clean
  no-overlap case, not a conflict_gated one. Both remaining items, however, fail the dispatch-scope eligibility test on
  operator-decision grounds rather than conflict grounds: (1) Rate-limit calibration probe (line 397-406): the doc's own
  text labels it explicitly operator-gated ('operator-gated; blast from an IP, see when banned -- one-time test'). It
  requires launching an ephemeral VM whose PURPOSE is to intentionally trigger 429/bans against live third-party
  providers (understat, transfermarkt, open_meteo, soccer_football_info, polymarket_clob, polymarket_gamma_api) to find
  the break-rate -- an action with real external-facing consequences (temporary IP bans, provider ToS exposure) that the
  doc's author already withheld from unconditional dispatch. Per CLAUDE.md's VM-launch gating rule, this needs an
  explicit [OPERATOR] authorization, not a worker's unilateral judgment call on acceptable-risk thresholds. (2)
  API-Football daily-quota bump (line 797): the doc frames this as an explicit EITHER/OR -- 'operator bump to 1.5M/day
  OR multi-day skip-fresh re-runs.' The bump itself is a spend-authorization ask (300k/day -> 1.5M/day is a 5x cost
  increase on a metered API) squarely matching the operator_gated 'credential/spend ask' pattern. The doc does not
  resolve which branch to take, so a worker cannot determine the bounded action without that ruling first. Both items
  therefore route to the SAME gate (an operator ruling on acceptable external-facing risk / spend), so this doc as a
  whole classifies operator_gated rather than yielding a batchable todo. Recommended resolution: raise a single operator
  question bundling both asks (probe-VM go-ahead + quota-bump-vs-skip-fresh choice) in the next operator-decision-needed
  batch; once ruled, a follow-up pass can draft the now-bounded todo(s) against whichever branch is authorized.
- **`plans/active/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`**: Confirmed the
  Phase-1 uncovered item: todos 12/13/14 (the manifest-consolidator TOCTOU fix, its deploy, then a re-run+hold-verify of
  the cross_ag_prediction remediation) are not cited or covered by any doc in the covering set. Todo 15 (the separate
  market-data-tick-sports-prd KALSHI empty_confirmed population) IS fully covered by
  sports_satellite_ao_dispatch_batch3_2026_07_25.md, which explicitly scopes itself as read-only classification and
  explicitly defers todos 12-14's fix as "explicitly BLOCKED-OPERATOR-DECISION" — so batch3 does not attempt to cover
  12-14 either. CONFLICT CHECK finding (genuine, resolves by logic, not a competing-fix situation): todo 12's exact
  prescribed fix — capture unified-trading-library's manifest_consolidator._write_consolidated()'s CAS
  `if_generation_match` token from the SAME read that produces the merge payload (via download_bytes_with_generation),
  instead of a late blob.reload() — has ALREADY SHIPPED as unified-trading-library@14301571, closing the identical
  TOCTOU race in the same shared function, resolving the sibling issue docs
  plans/archive/issues/sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md and
  sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md (both status:resolved, full
  quality-gates green, 98/98 + 60/60 tests passing). Because _write_consolidated is a single shared library function
  used by every asset_group's consolidator (per our target doc's own ROUND 6 scope note), this fix's code-level content
  directly satisfies todo 12's ask — it is not a different/competing fix, it is the SAME fix, already merged. This is
  corroborated by plans/active/sports_consolidated_closeout_2026_07_19.md's Track V section, which cites the same commit
  fixing a TOCTOU revert on a DIFFERENT population (the league_id swap) and confirms it verified stable across 5
  consolidator cycles in production — i.e. the fix is not just merged but observed working live. What is NOT yet
  independently confirmed by anything in the covering set: (a) whether the specific
  uts-prod-manifest-consolidator-instruments-sports Cloud Run job (the one serving the instruments-store-sports-prd
  bucket this doc's bleed lives in, as opposed to the market-data-sports consolidator job the sibling docs verified) has
  actually been rebuilt+redeployed with the unified-trading-library@14301571-containing image (= todo 13), and (b) todo
  14's re-run of remediate_cross_ag_prediction_bleed_round3_2026_07_24.py against THIS specific bleed population plus
  the required multi-cycle hold-verify, which has never been attempted since the fix shipped. Why this stays
  operator_gated rather than batchable despite todo 12 likely already being satisfied: the target doc itself states, in
  its own frontmatter summary and in ROUND 7 body text, an explicit standing gate — "BLOCKED-OPERATOR-DECISION on
  scheduling that work... Do NOT re-attempt manifest remediation until it ships" and "this needs operator sign-off
  before any code/job change, not an autonomous patch" — because this is a manifest WRITE to a live,
  continuously-consolidating 5.5M+ row production index that has already silently reverted TWICE (once after ~30h43m,
  once after ~5min) under a fix that (at the time of writing) had not yet shipped. Even though the underlying library
  fix now appears to have shipped and been proven stable on a sibling bucket, confirming that + authorizing a third
  remediation attempt on THIS specific index is exactly the "code/job change sign-off" scenario the doc's own words gate
  on an operator decision, not a worker's unilateral judgment call — a worker re-running a manifest-write remediation
  script against a live production index with a documented double-failure history, based on the worker's own inference
  that a sibling fix "probably" covers this doc's bucket too, is the kind of irreversible-adjacent, high-blast-radius
  action task_template.md's dispatch-scope-eligibility rule reserves for human sign-off. Recommended operator decision
  to unblock: (1) confirm/deploy the unified-trading-library@14301571-containing image to the instruments-sports
  consolidator Cloud Run job specifically (verifying image build timestamp / library version pinned in that job's
  manifest vs. the commit's merge time), and if not yet deployed, authorize that deploy; (2) once deployed, authorize
  re-running remediate_cross_ag_prediction_bleed_round3_2026_07_24.py (already built, reusable, REMOVE-only) against the
  instruments-store-sports-prd bucket and the required multi-cycle (>=2 real consolidator cycles, not just immediate
  verify) hold-check before re-closing this doc. Once the operator gives that go-ahead, todos 13+14 collapse into a
  single bounded, checkable AO-eligible todo (verify-deploy -> run script -> poll N cycles -> record result) that a
  worker could execute without further judgment calls.
- **`plans/active/issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md`**: Confirmed via full doc read:
  the doc's single open [DIAG] P2 todo asks to "decide + execute the resolution" for 55,233 duplicate legacy FIXTURES
  manifest rows, among three explicitly-offered options — (1) leave as permanent noise, (2) scoped verified DELETE
  against the real prod manifest bucket (instruments-store-sports-prd-central-element-323112), or (3) investigate/build
  a tombstone mechanism that isn't verified to exist yet. The doc itself states this "is a genuine design call, not
  something to decide unilaterally." Conflict check: grepped every doc in the covering set for "55,233" / the doc's
  slug. Three hits are pure citations, not competing/executing todos: sports_consolidated_closeout_2026_07_19.md (line
  ~321) just marks the parent restamp todo PARTIAL and points at this issue doc as the open tracker;
  sports_satellite_ao_dispatch_batch4_2026_07_25.md's todo (lines ~92-111) explicitly does a _reconciliation-only_ pass
  on a sibling doc (fixtures_manifest_legacy_backfill_2026_07_24.md) — its own "Conflict-check clearance (2026-07-25
  re-check)" note confirms it deliberately defers the actual delete-vs-leave call to this doc and performs zero
  production mutation; the "operator-decisions doc entry #7" reference (line ~150-152) confirms this exact fork is
  already logged as a pending, unruled operator decision elsewhere, not something any AO plan has taken on itself to
  resolve. No doc in the covering set proposes or attempts a different resolution path, so there is no genuine two-sided
  conflict — just consistent, correct non-resolution pending the operator. Given option (2) is an irreversible prod-data
  DELETE against 55,233 manifest rows and option (3) requires verifying/building tooling that may not exist, and the
  three-way choice itself needs explicit sign-off per the doc's own words, this fails the dispatch-scope eligibility
  test (not a worker-determinable bounded outcome) and is correctly operator_gated, not batchable. Recommended
  resolution: surface this to the operator as a single decision request — "leave-as-noise (zero risk, permanent tech
  debt) vs. scoped-verified-DELETE (closes SCHEDULE_DEFINING_DATA_TYPES narrowing, requires extending the
  f14b13ae/8e783d70 resurrection-safety verification to this bucket first) vs. tombstone (unverified feasibility)" —
  once ruled, the resulting concrete action (e.g. "run the verified-delete procedure" or "record the leave-as-noise
  decision in the doc") becomes a clean, batchable AO todo in the next dispatch batch.
- **`plans/active/issues/sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`**: Conflict check: grepped
  the consolidated closeout (sports_consolidated_closeout_2026_07_19.md) and every batch2/3/4(+finalize) doc for the
  target objects (`day=all/entity=teams/teams.parquet`, `day=all/entity=venues/venues.parquet`) and the delete mechanism
  (`_legacy_archive`). Only batch2 (sports_satellite_ao_dispatch_batch2_2026_07_24.md) mentions these paths at all, and
  strictly to close ITS OWN investigation todo as "resolved-as-investigated" — it explicitly punts the actual delete,
  stating it "needs explicit operator sign-off... not a unilateral fold-that-can't-work or an irreversible delete." No
  genuine overlap/duplicate exists; nothing else claims this ground with a different approach. So there is no conflict
  to gate on. Eligibility: the single remaining todo is tagged `[OPERATOR] P2` and its own text states "Prod-bucket
  delete, human-gated — no agent runs this." This is a soft-delete=0 (irreversible) GCS delete against a PROD bucket
  (`instruments-store-sports-prd`), which per workspace HARD RULE is human-only regardless of scope-boundedness (the
  mechanical steps — backup-copy, verify, delete, verify-gone — are well-specified, but execution authority is
  explicitly withheld from agents by the doc author and by the corpus-wide prod-bucket-delete-is-human-only rule). The
  operator already gave in-session Option-A authorization (2026-07-25 banner) — what remains is not a design/judgment
  decision but literal execution of an irreversible prod delete, which stays human-only regardless. This is NOT a
  batchable AO todo; it cannot be drafted as a worker-executable candidate. Recommended resolution: this item stays
  parked as an `[OPERATOR]`-only action item for the operator (or an operator-supervised session) to physically execute
  per the doc's already-written backup→verify→delete→verify-gone steps; no new plan/todo should be drafted to route it
  through AO dispatch.
- **`plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`**: Confirmed the doc's 4 remaining
  open todos: (A) manifest-slice replacement for check_api_football_dependency() [shipped in batch2,
  instruments-service@bd1da540 — Phase-1's covered item], (B) share path-template constants between writer and checker,
  (C) VERIFY real backfill speedup, (D) NEW mapping-coverage gap in _build_fixture_league_map_from_gcs needing an
  operator/architecture decision. Conflict check on B and C turned up real overlap that changes the Phase-1 picture for
  both, so neither should get a freshly-drafted competing todo: - B ("share path-template constants") — the SAME batch2
  commit that shipped item A explicitly states, in its own evidence text: "path-template duplication is moot since the
  hot path no longer touches them, per this todo's own anticipated outcome"
  (sports_satellite_ao_dispatch_batch2_2026_07_24.md:503-505). Once `_manifest_shows_fixtures_captured()` became the
  PRIMARY check and the hardcoded-path probe became a rare fallback-only path, the original rationale for unifying the
  templates (avoiding silent desync on a hot, frequently-exercised path) no longer applies with the same urgency — this
  is a same-batch, later-dated, on-the-record assessment that provably supersedes B's original framing, even though the
  target doc's own checkbox for B is still unchecked (doc not updated post-shipment). Drafting a new AO todo to "share
  path templates" would just re-litigate a call the shipping commit already made. Recommend only a doc-hygiene note (not
  an AO todo): flip the target doc's progress log to record B as resolved-by-side-effect of the batch2 fix, or
  explicitly re-affirm it's still wanted for defense-in-depth on the now-rare fallback path — that's a judgment call for
  the doc owner, not new dispatchable engineering work. - C ("confirm real backfill speedup") — batch2 explicitly
  deferred this because it was "gated on 2 sibling implementation todos" (the check_api_football_dependency()
  manifest-slice fix and the sports_fixtures.py:356 batching fix). Both of those sibling todos are now shipped (batch2's
  own todos, both `[x]`). Critically, sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md already carries an OPEN
  (`- [ ]`, not yet executed) todo whose entire job is to re-check exactly this gate and extract C as a new dispatchable
  todo once cleared: "(3) the `sports_dependency_check` real-backfill timing verification (gated on 2 sibling
  implementation todos) — same treatment... Done when: each of the 4 deferred items has either (a) a new tracked
  todo/plan created and dispatched because its gate cleared, or (b) an explicit, re-verified confirmation that its gate
  is still open" (batch2_finalize:88-100). Drafting a second, parallel todo for C here would race that existing finalize
  todo — same underlying fix, same file/mechanism (the doc's own VERIFY todo), no genuine ambiguity about which one is
  "right," just duplicate dispatch. The correct move is to let batch2_finalize's todo #88 do its job (it will land C as
  a new todo once it runs), not front-run it. That leaves D as the only item with no existing coverage and no in-flight
  resolution mechanism anywhere in the covering set (grep-0 for `_build_fixture_league_map_from_gcs` outside the target
  doc and the aggregated-sources inventory list, which is audit-only). D is explicitly NOT a bounded worker-executable
  outcome — the doc's own text says it "needs an operator/architecture decision on whether the mapping should use the
  broader Prediction+Features+Reference set (matching `_fetch_fixture_ids_via_api`'s fallback-path scope) or whether
  `fixture_ids_override`'s real callers only ever pass fixture_ids that already have a working non-GCS league source,
  making this dead weight — real verification of which, before choosing a fix, is required." This is a genuine
  two-option design fork (broaden the league-set the mapping draws from vs. conclude the gap is dead weight for real
  callers) that determines the shape of the eventual fix; it cannot be resolved by a worker alone. Recommend: raise to
  the operator as "should `_build_fixture_league_map_from_gcs`'s af_league_id→canonical mapping use the broader
  Prediction+Features+Reference league set, or is the current narrow `get_prediction_leagues()` scope fine because
  `fixture_ids_override`'s real callers never hit the gap in practice (needs a real-caller-usage check to confirm)?" —
  once ruled, the resulting fix becomes a normal bounded AO todo.
- **`plans/active/issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`**:
  The remaining work in this issue doc cannot be batched into an AO-dispatch todo because it is explicitly
  operator-gated by the doc's own text: the [CODE] P2 todo says 'do NOT touch VENUE_DATA_TYPE_CAPABILITIES or the golden
  regression until' the operator's FINAL decision on retire-vs-scaffold, and a /blocked question requesting that
  sign-off was posted 2026-07-24 (slot 5) but remained PENDING as of the doc's latest content. The decision matters
  because retiring the capability declaration shrinks the sports honest-coverage denominator (an operator-visible metric
  change), so this is a genuine human decision point, not a determinable worker outcome. Recommended resolution: this
  doc should stay open and orphaned until the operator answers the pending /blocked question (BLK-c545ae54 referenced in
  the doc). Once answered, the resulting [CODE] P2 todo becomes trivially batchable (bounded: edit one registry dict +
  one golden JSON regression file, OR scaffold+BLOCKED-CREDENTIALS per the external-data-always-available rule) and
  should be picked up in the next AO-dispatch batch at that point. No conflicting work exists elsewhere in the covering
  set — the two doc hits found during the conflict check touch a different registry (DATA_TYPES_BY_ASSET_GROUP casing
  revert) and an already-resolved separate MDPS consumer-check, not this doc's retire/scaffold decision.
- **`plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`**: Confirmed Phase-1: all 8 [DESIGN] P3
  todos (§1 decay-window statistic/window/data-source/output-shape, §2
  gate-statistic/sample-size/threshold-value/acceptance-test) remain unchecked with no later RE-TRIAGE/RESOLVED section.
  Conflict check: grepped every covering-set doc (consolidated closeout, audit, 3 closeout forks + finalizes,
  native_ao_extract + finalize, batch2/3/4 + finalizes) for
  arb-decay/alpha-gate/SportsArbDutchingEngine/decay_window/edge_bps_remaining. Only one hit:
  sports_satellite_ao_dispatch_batch2_2026_07_24.md mentions `SportsArbDutchingEngine` twice, but both are UNRELATED — a
  decimal-odds-field migration for features-service and a legacy-engine-migration todo — neither touches decay-window
  measurement or the alpha gate's pass/fail criteria. No genuine overlap; nothing else claims this ground. However this
  doc's own frontmatter (`assigned_vm: NA`, `execution_scope: local-only`) and body are explicit: it exists BECAUSE of
  operator ruling BLK-b567ce7d (2026-07-21) that this is brand-new zero-spec feature work requiring operator sign-off on
  acceptance criteria/thresholds BEFORE any implementation OR further spec-drafting dispatches. §3 "Open questions for
  operator sign-off before implementation dispatches" lists three unresolved judgment calls baked into the 8 todos
  themselves: (1) which assigned_role/repo-split owns eventual implementation (quant_dev vs backend_engineer,
  single-repo vs two-repo split), (2) p25-tail-aware vs mean for the §2 gate statistic — "a real risk-appetite decision,
  not a mechanical one" per the doc's own words, (3) whether the operator wants a provisional fixture-derived threshold
  value or insists on real paper-run soak data before any code ships. Every one of the 8 todos is phrased as "Define X,
  recommend Y" — i.e. the doc proposes a design and asks the operator to bless it, not a checkable/executable outcome a
  worker can determine alone. This is the textbook "figure out how X should look" pattern the dispatch-scope-eligibility
  rule excludes from AO batching (CLAUDE.md § Plans — operator ruling 2026-07-23). Drafting a competing/pre-empting AO
  todo here would violate the very ruling that spawned this doc.
- **`plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md`**: Confirmed via direct read: the doc has 5
  open todos, none overridden by a later dated section. Conflict check: grepped every
  batch2/3/4(+finalize)/consolidated-closeout/fork/foldin/hygiene/native-ao-extract doc for
  "SportsMatchingEngine"/"sports_matching" and for "BACKTESTS.md"/"backtest-groups verification". Result — no genuine
  conflict, only partial acknowledgment: batch2's dispatch plan (sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  lines 17-22 and 905-908) explicitly names todos 1/2/4 (run_sports_backtest CLI, fixture wiring, hermetic alpha_bps
  test) as EXCLUDED pending the SportsMatchingEngine-vs-L0Matcher decision (todo 3), and its finalize plan
  (batch2_finalize, lines 93-100) carries a re-check-and-extract-new-batch mechanism gated on that same decision
  landing. Batch3/batch4 (+finalizes, both status: draft) contain zero mentions of
  group_c/backtest_harness/run_sports_backtest — they don't touch this doc at all, so no overlap there either. Todo 5
  (DESIGN — decide backtest-groups verification-surface placement / docs/BACKTESTS.md) is mentioned nowhere in any
  covering plan except a bare re-listing in sports_consolidated_closeout_aggregated_sources_2026_07_24.md with no
  resolving or gating todo — it is completely untouched, not even acknowledged-and-excluded. So there is no
  competing/duplicate prescription anywhere in the covering set for either uncovered item — this is pure gap, not
  conflict. The two genuinely uncovered items are BOTH the plan's own [DESIGN] todos (3 and 5): todo 3 = resolve
  SportsMatchingEngine (dead code, zero callers) vs L0Matcher duplication — an architectural call between deleting
  unused code or wiring it in as the sports-specific matcher, which gates todos 1/2/4; todo 5 = decide whether the
  future harness belongs in the routine docs/BACKTESTS.md verification surface (currently dead per a sibling
  investigation) or stays a manual one-off, given sports is explicitly backtest-only/not-on-critical-path. Neither is a
  bounded, worker-determinable outcome — both are open-ended judgment/design calls per CLAUDE.md's
  dispatch-scope-eligibility rule (an audit/design todo is AO-eligible only when its outcome is a checkable fact or
  scoped change, never "figure out how X should look"). Todo 3 additionally is a hard prerequisite already correctly
  modeled by batch2/batch2_finalize's re-check-and-conditionally-extract mechanism — nothing new to draft there beyond
  what's already tracked. Todo 5 has no tracking mechanism anywhere, but is likewise a pure human design call
  (docs-placement / verification-surface strategy for sports), not something an AO worker can resolve alone. Recommended
  resolution: this doc needs an operator/architect ruling on both DESIGN items (ideally in one sitting since todo 3
  gates the implementation todos and todo 5 is independent-but-related scope-placement); once ruled, batch2_finalize's
  existing re-check todo already covers re-extracting todos 1/2/4, and todo 5 should be added as an explicit line item
  to that same re-check (or a follow-up doc) at that time. No new AO-dispatch todo should be drafted now — doing so
  would either restate the design question as a fake "todo" (violating the eligibility rule) or duplicate the re-check
  mechanism batch2_finalize already owns.
- **`plans/active/sports_live_availability_and_source_latency_2026_07_24.md`**: Confirmed uncovered item (lines
  134-138): "[DATA] P2. Live ODDS quota decision + cheap second source" — size The Odds API Starter tier (~$10/mo, 50k
  credits) for the live league set and/or wire api_football `/odds` in-play as a second forward source, so LIVE_ODDS /
  odds_horizon_bucket keeps feeding CLV/steam features forward without exhausting quota. The todo is explicitly tagged
  **BLOCKED-OPERATOR-DECISION (book set + quota tier)** in the source doc itself — it is a spend/product decision (which
  paid tier to commit to, which books to cover), not a determinable technical outcome a worker can execute alone.
  Conflict check: grepped the consolidated closeout (2026_07_19) and every batch2/3/4(+finalize) doc for "odds
  api"/"live.odds"/"book.set"/"quota tier"/"odds_horizon"/"LIVE_ODDS". All hits found
  (sports_consolidated_closeout_2026_07_19.md:516, batch2:812/826/847/867/878/898/962/978, batch4:112/116) concern the
  MDPS `odds_horizon_bucket` REPROCESS/canonicalization migration (109,312-object league_id-casing reprocess of
  already-captured historical odds_horizon_bucket data) and a separate fixture_id-blank collapse diagnostic — a distinct
  mechanism (historical data correctness/migration) from the target's concern (live-VM polling cost/quota-tier sizing
  for forward LIVE_ODDS capture going forward). No file/mechanism overlap; no conflict to gate on. Once the operator
  rules on book set + quota tier, the resulting connector-tuning + VM-cadence change (market-tick-data-service +
  deployment-service) is itself a bounded, worker-executable AO todo — but drafting it now would bake in an unmade
  decision, so it stays operator_gated rather than batchable.
- **`plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`**: The doc's entire remaining-work
  surface is a single sequential chain gated at its first step by an unresolved OPERATOR decision (pursue live
  sports-odds ingestion or not), with every downstream todo explicitly conditioned on that yes/no, and the chain's
  terminal step is itself a second OPERATOR go-ahead gate. No sub-slice is independently checkable/executable by a
  worker without that decision landing first, so this fails the dispatch-scope eligibility test at the very first todo —
  it is a human decision wearing a todo's clothes, exactly the pattern CLAUDE.md's plan-authoring rule calls out. The
  conflict check found the doc's cited blocker (cross-AG bleed bug) is already correctly owned by the consolidated
  closeout + batch3, with no competing-fix duplication against this doc's own todos, so nothing needs folding in from
  that angle either. Result: operator_gated, no candidate_todo drafted.</parameter>
  <parameter name="conflict_or_defer_note">Confirmed via full read: the doc has 6 open todos forming a strictly
  sequential chain, all P3, all human-plan-by-construction per operator ruling BLK-9d3a208c. Todo 1 is the load-bearing
  gate: "[OPERATOR] P3. Decide whether to pursue a live sports-odds ingestion path at all" — sports has zero live-odds
  infrastructure today (MTDS is architecturally batch/download-only per batch-live-architecture.md §4; no
  `live_odds_api` SOURCE_MODE_CAPABILITY exists), so this is a real infrastructure-investment decision, not a flag flip.
  Todos 2-6 (scope the MTDS live-odds connector, build launch-mtds-live-sports.sh/launch-mdps-features-live-sports.sh,
  build the FSS live handler, run the promote-workflow chain, and finally an [OPERATOR] go-ahead to flip to live) are
  each explicitly gated "Once Todo 1 is a yes" / depend on the prior step landing — none of them is independently
  dispatchable without that decision, and the terminal todo is itself another [OPERATOR] gate (full readiness-ladder
  Groups A-H sign-off). There is no bounded, worker-executable subset here: even Todo 2 ("scope the MTDS live-odds
  connector... as its own follow-up plan") is conditioned on Todo 1's yes/no, which is undecided. CONFLICT CHECK:
  grepped sports_consolidated_closeout_2026_07_19.md and batch2/batch3 dispatch docs for overlap on this doc's own
  mechanisms (live_odds_api, launch-mtds-live-sports.sh, promote-workflow activation) — no hits; the only overlapping
  ground is the doc's own SCOPE-OVERLAP banner's cited hard BLOCKER (the cross-AG prediction/sports instruments-index
  bleed bug, ROUND 4+), which IS actively owned elsewhere: sports_consolidated_closeout_2026_07_19.md tracks the bleed
  as a Canon-track item (lines 227-234, 407-414) and sports_satellite_ao_dispatch_batch3_2026_07_25.md (lines 133-146)
  has an active read-only classification todo citing the same ROUND 4-7 TOCTOU bug, explicitly noting the ROUND 6/7
  remediation is BLOCKED-OPERATOR-DECISION. That is the correct owner for the blocker itself — this doc's own Todo 1
  does not duplicate it (Todo 1 is about live-odds ingestion strategy, not the bleed fix), so no competing-fix conflict
  exists; the bleed bug is simply a stated pre-req, already tracked, not something to re-batch here. Separately, batch2
  (lines 397-402) already SHIPPED the `SportsArbDutchingEngine` naming migration (strategy-service@4c55438c), which is
  unrelated to the factory-dispatch-wiring bug this doc cites as a Group-B prerequisite
  (`sports_arb_dutching_engine_not_wired_to_factory_2026_07_21.md`) — different issue, no overlap, and that issue doc is
  out of this doc's own todo scope anyway (a "prerequisites tracked elsewhere" bullet, not this plan's todo).
  Recommended resolution: this doc stays correctly orphaned-but-uncoverable by AO dispatch — it needs the operator to
  answer Todo 1 (pursue live sports-odds ingestion: yes/no) before any of its remaining work becomes batchable. Until
  then, none of Todos 2-6 should be drafted as AO-dispatch candidates since they're contingent on an undecided fork, and
  Todo 1 itself is explicitly tagged [OPERATOR]. Suggest surfacing this single question to the operator as a standalone
  decision ask (not a plan-of-work): "Pursue live sports-odds ingestion (new MTDS live connector +
  SOURCE_MODE_CAPABILITY entry) — yes, scope it as a follow-up plan, or no, mark this plan `status: cancelled`?"
- **`plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md`**: Confirmed against the doc text (todo 2, lines
  85-92): the C3 pre-launch-window corpus (10,345 objects) requires an explicit operator ruling between two mutually
  exclusive actions with real blast radius — (a) extend UAC coverage windows (SOURCE_COVERAGE_START["footystats"]
  2019-01-01→2018-01-01 + api_football DATA_TYPE_COVERAGE_START sub-entity windows) and re-run
  backfill_orphan_class_e_sports.py to manifest the corpus, or (b) ratify the corpus as permanently outside-window
  (becomes a CF-21-style cleanup candidate). A window change affects backfill orchestrators
  (clip_dates_to_source_coverage), data-status denominators, and the phantom audit — this is not a worker-determinable
  outcome, it is a two-option fork needing operator sign-off, exactly as the doc itself labels it ("operator-gated").
  Conflict check: grepped the consolidated closeout (sports_consolidated_closeout_2026_07_19.md) and every
  batch2/3/4(+finalize)/fork/foldin/hygiene/native-ao-extract doc for
  C3/footystats/SOURCE_COVERAGE_START/orphan_sweep_sports/backfill_orphan_class_e_sports/pre-launch-window. Found one
  substantive hit: sports_satellite_ao_dispatch_batch2_2026_07_24.md lines 550-567, a SHIPPED (checked,
  instruments-service@6cf44d31) fix to migration_orphan_sweep_sports.py's classifier ordering
  (is_covered_sports-before-_is_pre_launch bug causing stale pre-floor rows to misclassify as B_legacy_duplicate instead
  of C3_pre_launch_window). This is a classification-correctness bugfix, not a resolution of the underlying policy
  question — its own completion note explicitly says the "covered wins" semantics on the by_date-tree branch are
  "deliberately left untouched — a different, already-decided policy question (the v2 pre-floor 728-row disposition,
  issue doc §7 todo 1, [OPERATOR]-gated)", i.e. it corroborates rather than resolves that a separate operator decision
  remains open. No genuine conflict: the batch2 item fixes HOW rows get counted/labeled into the C3 bucket; the target
  doc's item 2 is WHAT TO DO with the C3 bucket once counted (extend windows vs ratify permanently outside-window).
  Different mechanisms, complementary not competing, no ordering ambiguity. Todo 1 (CF-5 relabel) is fully closed per
  Phase-1 evidence (batch2 line 462) and needs no further action here. Recommended resolution: this doc stays open
  pending an explicit operator ruling on the C3 window-extend-vs-ratify-permanently-outside-window fork; once ruled,
  whichever branch is chosen becomes a bounded, batchable AO todo (backfill_orphan_class_e_sports.py re-run + UAC window
  edit, or a CF-21-style cleanup/delete plan) — draft that follow-up only after the operator answers.
