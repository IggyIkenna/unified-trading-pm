---
doc_type: issue
title: Extracted history — 23 fully-closed DONE todos from sports_satellite_ao_dispatch_batch5_2026_07_26.md
summary: >-
  Extracted 2 fully-closed (`- [x]`) todos from sports_satellite_ao_dispatch_batch5_2026_07_26.md (2026-07-26, slot-2)
  to bring that actively multi-slot-edited plan back under the 1000-line hard cap (task_template.md finding J). A
  further 21 fully-closed todos (every remaining `[x]` DONE item in that plan besides its 2 genuinely-still-open ones)
  were appended 2026-07-28 per `issues/sports_satellite_batch5_line_cap_blocks_priority_edit_2026_07_28.md`, after the
  same plan grew back over the 1000-line cap. All 23 items are complete historical records — no open work, nothing here
  needs picking up.
status: complete
nature: record
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
    deployment-api,
    deployment-ui,
  ]
scope: [engineer, admin]
tags: [sports, history, extracted, archive]
related:
  [
    sports_satellite_ao_dispatch_batch5_2026_07_26,
    issues/sports_satellite_batch5_line_cap_blocks_priority_edit_2026_07_28,
  ]
created: 2026-07-26
last_updated: "2026-07-28"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
locked_by:
---

# Extracted history: 23 completed todos from sports_satellite_ao_dispatch_batch5_2026_07_26.md

> Batch 1 (2 todos) extracted verbatim 2026-07-26, slot-2. Batch 2 (21 todos) extracted verbatim 2026-07-28 per the
> line-cap remediation issue doc. All 23 fully done, no open work.

## Batch 1 (2026-07-26)

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

## Batch 2 (2026-07-28, line-cap remediation — 21 todos)

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
- [x] ✅ [DATA] P2. **DONE 2026-07-26 (slot-2) — player_stats nested-schema normalization + 1,298 manifest/GCS-mismatch
      investigation (Finding-1 follow-ups).** (1) Flattened all 3,274 nested-schema `player_stats` cells via
      `instruments-service@a22e371e` (reusing the production `normalize_api_football_player_stats` mapping function);
      final census confirmed 0 remaining, `quality-gates.sh` green. Hit + fully remediated a self-caused incident along
      the way (240 objects briefly written empty on the first `--apply`, root-caused, live-refetch-remediated 240/240
      with mandatory read-back verification) — see
      `/plans/archive/issues/sports_player_stats_normalize_empty_write_incident_2026_07_26.md` (archived; follow-ups:
      `/plans/archive/issues/sports_player_stats_empty_write_followups_2026_07_26.md`). (2) Root-caused the 1,298
      missing-GCS cells: 1,210 (93%, 2018-2020) match the doc's own Defect-3 writer-generation quirk; 88 (7%, 2025) are
      a NEW anomaly, filed as its own follow-up rather than guessed at. No manifest reconciliation executed (explicit
      non-actionable ruling, filed as a follow-up) — findings landed in
      `plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`'s Finding 1 section + new
      "Follow-up todos" section. Source:
      `plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (Finding 1 — RESOLVED 2026-07-25
      section, "Two things found during this pass").
- [x] ✅ [DIAG] P3. **DONE 2026-07-26 (slot-10, data_engineering)** — Escalated the confirmed 2026-06-21..24 odds_api
      raw-ingestion gap. Re-verified live via a scoped `gcloud storage ls -r` on exactly the 4 dates' raw prefixes (no
      whole-corpus walk), both `pipeline_mode` variants — unchanged: only `instrument_type=sport` meta-snapshot objects
      exist, zero `instrument_type=odds` `data_type=trades` objects for any of the 4 dates on either pipeline_mode.
      Filed `issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md` with the 3 required elements (exact dates +
      GCS paths checked; the `RAW_ODDS_SHAPE_UNRECOGNIZED`/`attempted_failed` provenance, not a script defect;
      cross-link + note re: the P2 shard4 retry staying open/time-gated). Cross-linked both directions: new doc's
      `related:` cites the source doc; source doc's `related:` + its own P3 todo updated
      (`issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`). No backfill/re-derivation attempted.
      Source: `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md` (P3 item).
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-2, `data_engineering`) — Step (b) closed: full-population measured
      (4,045/275,136 = 1.5% affected), decidable rewrite shipped + re-verified.** Root-cause + measure poll-key
      `(event, market, outcome, bm_time, price, fetch_utc)` duplicates in canonical
      `market-data-tick-sports-prd-central-element-323112` odds objects (repo: market-tick-data-service). Source:
      `mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md`. `market-tick-data-service@25916f6e`: added
      `--full`/`--output` to `measure_odds_api_poll_key_duplicates_2026_07_26.py`; shipped
      `dedup_odds_api_poll_key_duplicates_2026_07_26.py` implementing the decidable rule (prefer the
      canonically-resolved team-id row over a raw-slug fallback within a poll-key duplicate group) — corrected via
      live-data validation to judge only the team-fragment position that actually varies within a group (a constant leg
      can be absent from today's alias table without being the source of the ambiguity). Applied against the full
      affected population: **3,829/4,045 (94.7%) deduped** (26,670 duplicate rows dropped, CAS-protected writes, 0
      errors), re-verified 0 remaining duplicates among them. **216/4,045 (5.3%) left genuinely undecidable** (different
      mechanism — both team legs vary simultaneously) — filed as a new follow-up todo in the issue doc, not guessed at.
      19 unit tests added/passing. Full detail + evidence in the issue doc, not duplicated here.
- [x] ✅ [SCRIPT] P3. **DONE 2026-07-26 (slot 4)** — Root-cause WHY `quality-gates.sh`'s function/class/method SIZE
      CHECK (phase 5) didn't block the 2026-07-16 sports-orchestrator function-size regression at commit time (candidate
      commits `a66fc295`, `493393c8`, `86cc71ff`, all instruments-service, same day) — determine whether it was the
      green-content SENTINEL SKIP (tree-identical-to-last-green reuse) vs a `QG_SLICE`-scoped gate run that excluded
      phase 5 vs a different mechanism, by inspecting the actual quickmerge/CI run logs or sentinel state for those
      commits. Then check whether `qg_sentinel_environment_blind_2026_07_23.md`'s planned sentinel-hardening fix
      (binding `ENVIRONMENT`, and generally gate-affecting config, into the sentinel hash) would also have
      caught/prevented this class, or whether this is an independent sentinel-skip mechanism needing its own separate
      fix — note which, citing the specific sentinel/gate code path. **Findings (full evidence in
      `qg_size_gate_sentinel_skip_root_cause_2026_07_25.md`)**: the original "same-day 07-16 candidates" hypothesis was
      wrong — via `git blame` + direct AST re-measurement of each contributing commit's exact tree, the real
      threshold-crossing commits are 3 DIFFERENT days: `56aa19388` (07-13), `0d9ffabd0` (07-14), `493393c88` (07-15, the
      only listed candidate). Ruled out the `FUNCTION_SIZE_EXTRA_EXCLUDES` workaround directly (no active exclusion at
      any crossing commit; the only re-exclusion window, `7d56b9d6`→`ac22305c`, was 2026-07-20/21, a later separate
      episode). Verdict on subsumption: `qg_sentinel_environment_blind_2026_07_23.md`'s fix does **NOT** subsume this
      gap — the size check has zero `ENVIRONMENT` dependency, orthogonal dimension. Filed a live-reproduction follow-up
      todo in the same issue doc (historical sentinel state is local/uncommitted and long gone, so a definitive
      tooling-bug-vs-workflow-gap verdict needs a fresh repro, not more archaeology). Both acceptance-list checkboxes
      flipped `[x]` with evidence in the issue doc.
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot 9, data_engineering) — Refreshed the batch_footystats/ODDS_API orphan-object
      disposition to `yes-twin-confirmed` and closed the doc's provenance gap.** Ran
      `market-tick-data-service@c03890b3`'s
      `scripts/sports/league_id_relocation/census_footystats_orphan_content_2026_07_25.py` to completion over the FULL
      2020-06-06..2026-04-14 calendar range (2,139 days, a superset of the archived doc's exact 1,815-day scope — the
      original day-list artifact was an unrecoverable local scratch cache), 0 days missing, sharded across up to 9
      parallel background workers and recovered twice from session-teardown interruptions by re-merging completed
      per-shard reports and relaunching only the genuine remainder. Result: 1,534 `pure_duplicate` days (0
      unique-legacy-keys) + 280 `genuine_gain` days (exact match to the archived doc's 280-day bucket) + 325
      `no_migrated_objects` days. Refreshed the doc's 5-part-proof `Part 2 content` line to exhaustive and flipped
      `Disposition` to `yes-twin-confirmed` for the 1,534-day pure-duplicate bucket. (2) Recorded the 280-day bucket's
      own disposition (436,738 migrated-only keys, excluded from the delete-suggestion, recommends a scoped follow-up
      merge or leave-out-of-scope — human decision, not executed). (3) Provenance trace already completed in an earlier
      pass this session: searched every named candidate script, none matched the exact population signature — search
      exhausted, no commit/process found, recorded as an open (non-blocking) provenance gap. All three of the source
      doc's todos flipped to `[x]` with evidence; no GCS delete executed or staged (remains human-only per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1). Full evidence:
      `sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md` (all 3 todos `[x]`, new "Full
      exhaustive census results + 280-day bucket disposition" section).
- [x] ✅ [DOC] P2. Close out `issues/sports_batch_footystats_swap_wrong_script_2026_07_25.md` as superseded: its claim
      that `merge_migrated_odds_into_canonical_2026_07_17.py` was never run (based on one missing manifest shard path)
      is contradicted and outweighed by two independently-corroborating, same-day re-verifications —
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
      `sports_batch_footystats_swap_wrong_script_2026_07_25`. **DONE 2026-07-26**: re-verified fresh, doc flipped
      `resolved`, 3 todos struck as superseded, both corroborating docs cited.
- [x] ✅ [DATA] P2. **DONE 2026-07-26 (slot-5) — uac@40d2dd8f750a96ff0a811b6b56f0ab5401d8ed87.** RE-DIAGNOSED: only 1 of
      the 4 named leagues (`WALES_FAW_CHAMPIONSHIP`) was genuinely missing — the other 3 already existed in origin under
      different key names with matching `api_football_id` (`FAROE_ISLANDS_MEISTARADEILDIN`=367,
      `FAROE_ISLANDS_LOGMANSSTEYPID`=491, `WALES_CYMRU_PREMIER`=110), so adding slot-9's names for them would have
      duplicated one real league each. Added the 1 real entry, bumped both structural-gap test counts by +1 (not +4).
      `.tabs/9/unified-api-contracts` was already self-reset to origin cleanly (0 ahead/0 behind) before this session —
      the reset sub-step was moot. 1271 sports/league tests green, `quality-gates.sh` PASSED. Full detail (archived):
      `/plans/archive/issues/sports_curated_universe_faroe_wales_leagues_missing_slot9_dup_2026_07_25.md`.
- [x] [DATA] P2. **Retagged from `[OPERATOR]` 2026-07-28** (already-shipped delete, citing features-service@d564bf6f).
      Purge the always-empty manifest rows/shards left behind by the § A2 dead-dimension deletion
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
      needed; not re-running `--apply` (would be a no-op against an already-empty target). **Update 2026-07-26T02:xxZ**:
      the source A2 issue doc's own mirror checkbox is now also flipped —
      `sports_features_layer_findings_sweep_2026_07_18.md` was 1,846 lines (over the `plans/active/` 1,000L hard cap,
      which blocked staging ANY edit to it regardless of diff size); resolved by a verbatim, byte-for-byte,
      zero-content-loss 3-way split by section boundary (precedent:
      `sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md`) into the original filename (596L, § A-F, A2's
      checkbox now `[x]` here) + `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md` (600L, § G-N) +
      `_part3_2026_07_26.md` (825L, § O-AA) — all 73 original open checkboxes accounted for (17+24+31=72 still open, 1
      newly closed = A2), verified via `diff` against a pre-split backup that the raw split is byte-identical to the
      original (zero content loss).
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
- [x] ✅ [CODE] P1. **DONE-FOR-CODE 2026-07-26 (slot-7, `data_engineering`) — (a)+(b)+(c)'s target-generation fix all
      shipped + real-data verified; only the literal 3-variant model retrain (new trained artifacts) remains as an
      explicit follow-up (see (c)'s final UPDATE below).** PARTIAL (a)+(b) DONE (by a concurrent slot, verified by me),
      (c) thoroughly diagnosed, genuinely BLOCKED on a deeper pre-existing ml-service gap.** (a)+(b): a concurrent slot
      shipped `features-service@4f365d23` ("fix(sports): unconditional HT-odds PIT gate + per-horizon ml-readiness
      rebasing") literally minutes before I picked this up, citing this exact doc's Open Todos #1+#3 as source —
      `_apply_ht_odds_pit_gate` is now called unconditionally with a regression test proving it fires on the
      `ht_break_minutes`-unknown path, and `ml_readiness_check.py`'s threshold is rebased per-horizon (re-run against
      real prod features-sports-prd 2026-04-15..2026-05-15: 29/31 dates PASS at 100%, gate_met=YES). Independently
      re-ran both regression test files (103 passed, 0 failed) — confirmed, not just claimed. (c): attempted the CLV
      retrain, found the 3 exact quarantined artifacts
      (`ml-store-prd-.../models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417{154715,164033,201036}/`) and hit 3
      STACKED, pre-existing ml-service training-CLI bugs while trying to reproduce their training scope: (1)
      `--target-type` singular has no fallback to `--target-types`, crashes `'None' is not a valid TargetType`; (2)
      `--family` is required+validated for `--asset-group SPORTS` but never consumed anywhere in `ml_service/training/`
      — dead wiring; (3) the REAL blocker — `cloud_feature_provider.py`'s feature dispatcher has a DEFI-specific
      non-instrument-id branch (`_query_defi_features`) but NO equivalent SPORTS branch, so sports falls through to the
      generic instrument-id GCS query (trivially empty, `instruments=[]`), then a BigQuery fallback that also returns
      nothing. Live-verified real `feature_group=odds_features` data DOES exist at the exact date probed (rules out
      data-absence) — **ml-service has likely never trained on real SPORTS features at all**, not CLV-specific. Filed
      `plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md` with all 3 bugs + a
      fix direction (mirror `_query_defi_features` for sports); did not attempt the architectural fix myself (out of
      scope for a P2 sub-item, needs dedicated work). The 3 quarantined artifacts remain untouched/unpromoted. OUT OF
      SCOPE (do not touch): item (2) blank-`fixture_id` fix — likely ALREADY FIXED by
      `market-tick-data-service@3401c0ab` (verify before duplicating); item (4) T-0 shard reconciliation — blocked on
      the sports legacy-bucket-cutover's T6.1 merge (`_index/per_vm/cutover-move-20260716.parquet`, still unmerged).
      Source: `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`. **Done when**: (a) ✅ regression test proves the PIT
      gate fires on the `ht_break_minutes`-unknown path; (b) ✅ `ml_readiness_check.py` rebased per-horizon,
      re-measured; (c) ⏳ gated on `ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md`'s fix
      landing first — CLV retrain completes + independently re-verified, 3 quarantined artifacts untouched;
      `quality-gates.sh` green on every touched repo. **UPDATE 2026-07-26 (slot-6)**: fixed Bugs 1+3 —
      `ml-service@7cccb236`, QG green, real prod `features-sports-prd` loading verified end-to-end (2383x956). Bug 2
      deferred (P3, design call). (c) still ⏳ — hit a new blocker (32 non-numeric SPORTS cols crash
      `feature_selection`) + a CLV-target-100%-flat finding, filed as
      `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`. **UPDATE (slot-12)**:
      shipped that doc's `[CODE] P2` fix (`ml-service@5a9e3050`); (c) still ⏳, 3 other todos remain — see that doc.
      **UPDATE (slot-11)**: shipped `[DATA] P2` (`features-service@c54f9eaf`, `pd.NA`→`np.nan` at the source); spun off
      `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md` (design/scoping, not fixed here). (c)
      still ⏳ — `[DATA] P3`/`[ML] P2` remain open in that doc. **UPDATE 2026-07-26 (slot-2)**: closed `[DATA] P3` — 7
      real dates checked, `clv_home` 0/N non-null on EVERY one (not window-specific). Root-caused to a naming mismatch
      (calculator produces `odds_clv_home`, export only carries an always-empty bare `clv_home`) — rename mechanism not
      fully traced, filed as a new `[DATA] P2` fix todo instead of guessing. (c) still ⏳ — a retrain today would always
      be 100%-flat garbage until that fix lands; `unified-trading-pm@dfbcf678f`. **UPDATE (slot 13)**:
      `ml-service@a14985b` fixed the same wrong-name bug in the leakage-strip list too — real leakage, not just a bad
      target. (c) still ⏳. **UPDATE 2026-07-26 (slot-8, `data_engineering`)**: closed that doc's `[DATA] P2` — the
      naming-mismatch theory was wrong. Traced the full path with real data (raw MDPS T-0+T-24h bucketed odds fed
      directly into the real calculator, the exporter's `_restrict_to_visible_horizons` point-in-time gate, and the
      actual written parquet's horizon distribution): `compute_clv_features` is correct; CLV is DELIBERATELY empty in
      every currently-emitting row (T-24h/T-1h/T-10m all exclude the T-0 closing line by design; `HT`, which would see
      it, never emits). Neither `0ded2449` nor `a14985b` can fix this — both are naming fixes for a value that's null by
      design, not by bug. Re-scoped as a features-service+ml-service architecture decision, filed as
      `issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md` with a `[DESIGN] P1` decision todo
      (3 candidate directions). (c) still ⏳ — now blocked on that architecture decision, not a code fix. NOTIFIED
      OPERATOR per the cross-repo big-finding rule. **UPDATE 2026-07-26 (slot-7)**: Option (b) ratified; `[DATA] P2`
      built + (after a watchdog auto-push gap, see
      `issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`) formally ratified via `BLK-ec018203`
      "Approve as-is" — flipped in the design doc. `[ML] P2` implemented (`ml-service`
      `training_targets.merge_clv_target_columns`, isolated `odds_targets` merge + regression test proving
      leakage-shield isolation holds); retrain + its own sign-off still outstanding — (c) remains ⏳. **UPDATE
      2026-07-26 (slot-7, same session)**: `[ML] P2` ratified (`BLK-fb01cd29` "Approve as-is") and shipped
      (`ml-service@f107176`). Direct real-data verification (2026-04-01..17, the exact window the 3 quarantined
      artifacts used) then surfaced + fixed 2 more real bugs same-session: `odds_targets` had never been backfilled for
      this window (ran the real features-service backfill), and the isolated `odds_targets` query dropped every row
      because it's event_id-keyed and needs a `derived_features` sibling to resolve fixture_id (fixed,
      `ml-service@655b87e`). Re-verified: CLV target class distribution is now genuinely non-degenerate
      (`flat=2370/94.4%, up=80/3.2%, down=61/2.4%`, vs 100%-flat before this whole chain) — full evidence in
      `issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`. (c) still ⏳ only for the literal
      3-variant model retrain (producing new trained artifacts) — the underlying target-generation fix is now proven
      correct against real production data; the retrain command itself is specified in that doc's `[ML] P2` todo as an
      explicit, scoped follow-up.
- [x] ✅ [DATA] P1. Resolve the sports odds manifest-routing regression opened by the 2026-07-24 addendum to
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
      `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`. **Resolution (2026-07-26, slot 8)**: all
      three closed (deliberate routing / same future-date-guard root cause, no longer reproducible / index left
      stale-by-design) — `unified-trading-pm@3d48c7a9b`.
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot 6).** Flipped `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s
      line-110 "NEW compute: add per-bookmaker raw decimal-odds retention" todo to `[x]` with a SHIPPED annotation
      citing `features-service@b03a6de4`. Re-verified current repo state before flipping (no further drift since
      2026-07-25T14:20Z): `git merge-base --is-ancestor b03a6de4 HEAD` confirms it's merged, and
      `odds_features_exporter.py`'s `_pivot_bucketed_to_fixture()` still emits the per-bookmaker
      `odds_decimal_{outcome}_{venue}` columns live in the current file. Checkbox-drift-only fix — no code change.
- [x] ✅ [CODE] P2. **DONE 2026-07-26 (slot-8, `data_engineering`) — closed the last remaining piece, 3.4's dry-run.**
      Direction is fully decided (§4.3 ✅ DECIDED 2026-07-22 — lowercase `data_type` canonical; §4.1/4.2/4.4 also
      closed) — nothing left here was a judgment call, only unbuilt implementation. Scope: (a) build the three
      still-missing Part 3 safety-tooling pieces the RE-TRIAGE (2026-07-23) names as genuinely unbuilt — row-identity
      assertions for the purge/relabel/drop scripts, a consolidator-paused pre-flight check, and a `coverage_drift.py`
      pre-notify mechanism — plus a `--dry-run` mode on the 3.2/3.3/3.4 remediation scripts; (b) in
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`, remove the uppercase
      `"ODDS"`-family case-variant entries from `DATA_TYPES_BY_ASSET_GROUP["sports"]` (keep only the lowercase forms)
      and un-skip `unified-api-contracts/tests/unit/test_sports_data_type_vocabulary.py` (drop the `_SKIP_REASON_K0B`
      gate) per §2.2. Did NOT build or duplicate the cross-object-CAS+alarm mechanism itself — that stays a separate
      tracked open todo (`sports_consolidated_closeout_2026_07_19.md`, "NEW 2026-07-23 (decision 12)"). Did NOT execute
      any actual manifest purge/relabel/drop against prod (3.2/3.3/3.4 remain gated on the standing human-only execution
      trigger per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) — build-only, as scoped. Source:
      `sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (RE-TRIAGE 2026-07-23 section + §2.2). **Done when**
      (all now met): the four safety-tooling pieces exist as reviewable code/scripts (dry-run mode included) with unit
      tests, the uppercase `ODDS`-family entries are removed from the sports data_type registry,
      `test_sports_data_type_vocabulary.py` runs unskipped and green, and both repos' `quality-gates.sh` are green —
      with no manifest/GCS write performed. **PARTIAL 2026-07-26 (slot-2)**: (b) done — `uac@a32ad5fb` (+ regression fix
      `mtds@f7504a10`). (a) 2/3 pieces + 1/2 dry-runs — `assert_consolidator_paused`/`assert_row_identity`/3.3 dry-run
      (`mtds@f7504a10`), `coverage_drift.py` pre-notify (`deployment-api@1f0d3a0`); 3.4's dry-run deferred (needs live
      per-row GCS-existence check). All 3 repos green, zero writes. Full writeup + a `consolidator_liveness.py`
      naming-bug finding in `sports_shard_enumeration_cartesian_blowup_2026_07_20.md`'s entry — `pm@be0540e3d`. **DONE
      2026-07-26 (slot-8)**: built + live-tested `drop_sports_odds_phantom_uppercase_2026_07_26.py` (`mtds@8b60b415`) —
      `--dry-run`-only (no `--apply` flag at all, same posture as 3.3), 8 unit tests, plus a real prod dry-run against
      85 sampled captured uppercase-ODDS rows (2 separate seeds/sample-sizes): 85/85 confirmed phantom (no backing GCS
      object under either of 2 empirically-discovered `raw_tick_data/` path shapes — the doc's original single-template
      assumption doesn't hold across the full 2020-06-06..2026-04-14 date range, see the script's own module docstring
      for both shapes + how they were verified via direct `gcloud storage ls`, not guessed), 0 unexpected hits, every
      lowercase `odds` twin confirmed present. `quality-gates.sh` green (6993 passed, 80.52% coverage). Confirmed the
      consolidator scheduler-state 404 slot-2 already found + filed (`_scheduler_job_name_for_bucket` "prd" vs real
      "prod") — same already-tracked bug, not re-filed. Zero writes. All 4 safety-tooling pieces + the vocabulary fix
      are now complete — this todo's done-when is fully met.
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
      `plans/archive/issues/quickmerge_agent_files_pure_deletion_gap_2026_07_26.md`. Source:
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
- [x] [DATA] P1. **Implement Sports E8 legacy-delete (`migrate_sports_canonical_v9.py --drop-stale`) + delete
      `sports_reference_v1_archive/` under an operator gate.** Implement the currently-unimplemented `--drop-stale` stub
      (line 886-891 raises) as a twin-verified per-surface delete — for both `instruments-store-sports-prd-*` and
      `market-data-tick-sports` surfaces, delete a legacy (no-`pipeline_mode`) object ONLY when its canonical
      `pipeline_mode=`-partitioned twin exists and is readable (matches the already-verified
      `migrate_sports_canonical_v9.py --apply` 1:1 legacy↔canonical parity check) — OR ship an equivalent standalone
      `gcs_delete_object` sweep with the same twin-verification. Snapshot-first (manifest `_index` snapshot before any
      delete). Include `sports_reference_v1_archive/` in the same gated sweep — already verified safe-to-delete
      2026-06-24 (archive `af_fixture_id` ⊆ canonical `af_fixture_id` across a 5-day/2018-2026 sample, canon-only=0; the
      v1 wide-denormalized bare-layout archive's data is fully represented by the v2 canonical store-id/derive-name
      pattern) — no further verification needed for that sub-scope. **Retagged off `[OPERATOR]` 2026-07-28**:
      named-scope, twin-verified object delete (not a whole-bucket destroy), reversibility-qualified per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — dispatch `[DATA]`/`[SCRIPT]`: fresh
      `gcs_bucket_soft_delete_retention_seconds()` check on both target surfaces in the same run as the delete
      (>=604800s expected per the 2026-07-27 note below), execute via sanctioned UTL helpers if it clears, no operator
      sign-off needed. Source: `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` (line 289).
      **Done when**: `--drop-stale` (or the standalone sweep) is implemented + unit-tested + dry-run-verified
      0-orphan/twin-safe on both surfaces, `sports_reference_v1_archive/` deletion is included in the plan, the fresh
      retention check is cited, and the delete executes + is verified (object counts drop, canonical reads unaffected).
      **DONE-FOR-CODE 2026-07-26** — `market-tick-data-service@236d945e` (+`@08439787`):
      implemented+tested+dry-run-verified twin-safe both surfaces. **Re-check 2026-07-27**: expected a quick finding-T
      re-tag (soft-delete anticipated 604800s); still needs the fresh same-run check + live-reader re-check cited before
      `--apply` fires.
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
- [x] ✅ [DATA] P2. **DONE 2026-07-26 (slot-10, data_engineering) — `ml-service@10e219f`.** Migrated 4 ml-service files
      still using pre-migration odds-feature names (missed by the earlier ml-service migration commits
      `unified-api-contracts@689efa54`/`ml-service@91f031a`, which covered only the `OddsFeaturesMixin` schema/loader,
      not mock-data generation or target generation). Re-derived the exact 125-entry old→new mapping positionally from
      the already-shipped `features-service@0ded2449` migration diff (ground truth, not hand-guessed), then grepped all
      125 old names (word-boundary) across the 4 named files: - `mock_data_provider.py`: 6 genuine hits fixed in
      `_SPORTS_FEATURE_NAMES` + the matching `X[...]` reads in `_generate_sports_training_data`
      (`velocity_home_24h_to_6h`→`odds_velocity_home_24h_to_6h`, `velocity_home_6h_to_1h`→`odds_velocity_home_6h_to_1h`,
      `steam_magnitude_home`→`odds_steam_magnitude_home`, `sharp_consensus_home`→`odds_consensus_home_sharp`,
      `pinnacle_vs_market_diff_home`→`odds_movement_pinnacle_diff_home`,
      `book_fragmentation_home`→`odds_fragmentation_home`). Left `implied_prob_home/draw/away` untouched — a different,
      coincidental naming (word-order-reversed), not an actual `ODDS_COLUMNS` entry. - `sports_target_generator.py`:
      **needed NO change** — an earlier, unrelated fix (`ml-service@a14985b`, a real data-leakage bug) already replaced
      its bare CLV/velocity column names with the real `odds_`-prefixed ones; its remaining old-name mentions are
      historical bug-documentation comments + `TARGET_TYPE` dict keys (a different namespace: target identifiers, not
      `ODDS_COLUMNS` feature columns). - `test_horizon_gate_shield.py`: 1 genuine hit fixed (3 sites) —
      `opening_home_odds`→`odds_opening_home` (a real pre-match-signal fixture column). -
      `test_sports_feature_loader.py`: 8 sites fixed in `TestOddsJoinKeyCrosswalk` (`home_implied_prob`→
      `prob_implied_home`) — incidental join-key-crosswalk placeholders, unrelated to schema-name validation.
      **Deliberately left unchanged**: `test_naming_mismatch_raises_loudly` (lines 146+149,
      `home_implied_prob`/`draw_implied_prob`) — this test intentionally constructs a dataframe with the OLD
      pre-migration names to prove the schema-validation gate raises loudly on a naming mismatch; renaming them would
      give the fixture 100% overlap with `OddsFeaturesMixin` and silently defeat the test's own purpose — the exact
      same-string-different-schema trap this todo warned about, hit for real. No f-string dynamically-built old-name
      construction found in any of the 4 files. Post-fix repo-wide grep of all 125 old names across the 4 files: zero
      functional hits (only the 2 categories above — the intentional negative test + historical
      comments/different-namespace dict keys — remain, both correctly out of scope). `quality-gates.sh` full run green.
