---
doc_type: plan
title:
  Sports satellite docs — AO dispatch batch 2 (36 AO-eligible todos extracted from 15 human-only satellite plans/issues)
summary: >-
  22 sports-AG satellite plans/issues were confirmed `assigned_vm: NA` / `execution_scope: local-only` — referenced by
  `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s discoverability index for human visibility only,
  never AO-dispatchable (that index deliberately uses non-checkbox markers so AO's regen_backlog parser can't ingest
  it). This plan extracts every genuinely AO-eligible todo from those 22 docs (concrete, determinable by a worker alone,
  no open operator/design judgment call) into one real AO-dispatchable plan, mirroring the
  `sports_closeout_batch1_ao_ready_2026_07_24.md` pattern. 37 todos (corrected 2026-07-25 plan-reconcile, was 36) from
  15 source docs. Internally-sequential multi-step chains (e.g. a 5-step GCS migration recovery procedure, a 4-step
  census→copy→reprocess→swap execution sequence) are combined into single todos rather than fanned out — AO's per-todo
  model has no mechanism to mechanically gate step N on step N-1 within one plan short of `sequential: true` for the
  WHOLE plan, and this plan's other todos genuinely benefit from concurrent dispatch, so combining same-job chains into
  one todo each is the safe choice, not a fragile cross-todo ordering promise. 4 real AO-eligible items were
  deliberately EXCLUDED (not lost — flagged in their source docs) because they depend on either another todo below
  landing first (a 5-repo-spanning parity test; a UI relabel gated on its own backend todo) or a human/operator decision
  that has not yet been made (the SportsMatchingEngine-vs-L0Matcher design call blocks all 3 of
  `sports_group_c_execution_backtest_harness_2026_07_21.md`'s todos; a manifest-perf verify-speedup todo depends on 2
  sibling implementation todos both landing). 7 of the 22 source docs contributed ZERO AO-eligible todos (either 100%
  human-only design/operator-decision work, or already fully done) and are untouched by this plan.
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    strategy-service,
    execution-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, satellite-docs, batch-2, plan-hygiene]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/archive/sports_legacy_cutover_closeout_tasks_2026_07_24.md,
    /plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md,
    /plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md,
    /plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md,
    /plans/archive/issues/sports_legacy_duplicate_triage_2026_07_22.md,
    /plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md,
    /plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md,
    /plans/archive/issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md,
    /plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/archive/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 9.2
estimate_calibrated_ai_days: 7.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "All 37 todos complete, reconciled by sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md; archived 2026-08-04."
depends_on: []
source: >-
  Operator request 2026-07-24: satellite docs referenced by the sports consolidated closeout's discoverability index
  were confirmed to be structurally un-ingestable by AO. All 22 left-over active/open sports satellite docs were triaged
  per-todo (via a 22-agent verification workflow) for real AO-eligibility, distinguishing concrete worker-executable
  todos from open operator/design judgment calls. This plan is the extraction of the AO-eligible subset, mirroring the
  sports_closeout_batch1_ao_ready_2026_07_24.md pattern for the master closeout plan.
context_scope:
  [
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/2026_07/sports_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/epics/sports_master.md,
  ]
---

# Sports satellite docs — AO dispatch batch 2

> **Why this plan exists.** Every todo below already exists, fully specified, in one of the 15 source docs listed in
> `related:`. None of that work is new — it was simply invisible to AO because its home doc is `assigned_vm: NA`. This
> plan does not duplicate or re-decide anything; it re-hosts already-decided, already-scoped work on an AO-dispatchable
> track. Once a todo here ships, flip the CORRESPONDING checkbox in its source doc too (cite this plan's commit as
> evidence there), the same reconciliation discipline `sports_closeout_batch1_finalize_2026_07_24.md` uses for batch 1.

> **Concurrency note.** No two todos below touch the same file (verified programmatically across all 36 before this plan
> was authored) — safe for AO's default same-priority-concurrent dispatch. Where a source doc's todos had a real
> ordering dependency, they are combined into ONE todo here (documented in that todo's own text as ordered sub-steps for
> the executing worker) rather than split and fanned out — this plan is intentionally `sequential: false` (todos below
> are independent of EACH OTHER; internal step-order within a combined todo is the worker's job to respect, per that
> todo's own text).

## Todos

### From `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`

- [x] ✅ [DATA] P0. **Eliminate the bare/legacy dual-layout** (operator: "legacy needs canonicalising or deleting —
      that's the whole point") — per-league entities that have BOTH a per-league split AND bare files for older days
      (`gcs_paths.py:96`) carry a stale parallel layout. For each: canonicalise the bare→per-league (in-retention) OR
      DELETE (pre-retention). Distinguish from the by-design bare entities (XG/WEATHER/player_values-bulk) which stay
      bare. (repo: instruments-service; read-only reference: unified-api-contracts `gcs_paths.py` `SportsLayout`).
      **Done when**: every per-league entity with a dual bare+per-league layout is canonicalised (in-retention) or
      deleted (pre-retention), snapshot-first; by-design bare entities left untouched. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`. — VERIFIED CLEAN 2026-07-25 (slot
      2): the dual-layout condition does not currently exist for any of the 15 `PER_DAY_PER_LEAGUE` entities — zero
      canonicalize/delete action needed. Full census in Progress Log.
- [x] [DATA] P0. ✅ **RESOLVED-AS-INVESTIGATED 2026-07-25 — interim: leave day=all in place, 2 items escalated to
      operator.** Investigation found the premise doesn't survive contact with the real GCS objects: (a) the day=all
      fold is mechanically blocked — TEAMS has no FLAT layout to fold into, and legacy vs live VENUES data have ZERO key
      overlap (numeric ids vs slugified strings) — no join key exists to dedup against. (b) the pre-genesis anomaly
      (131,306 TEAMS + 1,457 VENUES pre-floor rows) is already covered by the tracked
      `/codex/02-data/sports-2020-06-data-floor.md` phantom-row issue — no separate work needed. Escalated to the
      operator (not this worker's call): (1) authorize/decline the irreversible delete of the 2 day=all objects
      (soft-delete=0); (2) the TEAMS FLAT-layout design decision. Full evidence:
      `sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [x] ✅ [DATA] P0. **Odds-granularity watch-item check** — unified-api-contracts@a32ceb87. Checked whether pre-cutover
      10-min odds snapshots could be misread as missing coverage against a 5-min expectation. **Result: no issue** — no
      code path computes an expected-snapshot-count from a fixed cadence; MDPS bucket assignment uses a 30-90min
      staleness tolerance and the honest-coverage key has no per-minute axis. Recorded the investigation in
      `_endpoint_registry_data.py` for future re-checks; noted the codebase's documented v3→v4 cutover is actually
      ~2023, not ~2024 as this todo's text states. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [x] ✅ [DATA] P0. **Drop 2 out-of-universe numeric `league=` dirs** (`14231`/`315`) — instruments-service@2c4fa059.
      Scope was wider than the source doc's "2 in 2025" claim — 197 real GCS objects (175 in 2025, 22 in 2026) + 166
      stale manifest rows. Snapshot-first (backed up to `sports_reference/_purge_backups/2026_07_25_drop_14231_315/`);
      applied + verified twice: 0 remaining objects, 0 remaining manifest rows. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [x] ✅ [DATA] P0. **94-league enrichment backfill — COMPLETE.** Fresh manifest re-measurement showed 6 of the 7 named
      entities (FIXTURE_EVENTS/STATS/LINEUPS/PLAYER_STATS/MATCHES/XG/XG_SHOTS) already >99% honest-absence
      (`empty_confirmed`, genuinely exhaustively attempted, not a backfill opportunity) — re-launching would burn API
      quota for ~0% real gain. (The canonical closeout plan's own VM tracker citing "months-to-years from gate" was
      STALE — both prior VMs had already completed cleanly by 2026-07-23.) **INJURIES was the one genuine gap** (10,502
      captured / 10,219 `expected_unattempted`, 3.4%): launched targeted `af-backfill-20260725-002739`
      (2018-01-01→2026-07-25, singleton-lock-verified-clear before launch), completed cleanly
      (`exit_code=0`/`DEPLOYMENT_COMPLETED`) 2026-07-25T03:21:57Z. Post-run verification hit an apparent regression
      (both captured + expected_unattempted counts LOWER than baseline) — root-caused as an apples-to-oranges
      methodology artifact (baseline was unfiltered, re-measurement was 94-league-filtered), not a real one: re-ran both
      filtered identically across 3 manifest snapshots, confirming the post-floor INJURIES gap closed 100% (1,745→0
      `expected_unattempted`), with 3 independent signals (byte-identical pre-floor phantom count, monotonic row-count
      growth, monotonic captured growth across all 3 reads) ruling out a lost-update/floor-clamp confound. Also flagged
      (separate issue, not blocking): `create-code-tarballs.sh`'s gsutil upload fails under an expired WIF token.
      Source: `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [x] ✅ [CODE] P1. **UAC canonical registry build/refine** — unified-api-contracts@ce18ff15. Audited every clause of
      the Architecture section against current code before touching anything (most of this program had already shipped):
      name/ids/country/season-start-end-per-year (`season_dates.get_season_start`/`get_season_end`, per-league-per-year)
      and transfer window (`transfer_windows.py`) were already canonical; team cross-source mapping was already
      comprehensive (`team_mapping_data.py`, 6,246-row CSV, all leagues); fixture/player canonical ids already derive
      via `canonical_ids.build_fixture_id`/`build_player_id` (player id already consumed by `understat/normalize.py`);
      annual footystats-id rotation is already handled by a real mechanism — the weekly
      `check_footystats_season_drift.py` CI job (`.github/workflows/weekly-validation.yml`), not a season-year-keyed
      table. Two genuine, scoped gaps closed: (1) added `LeagueDefinition.is_cup` (derived
      `tier==0 and sport=="FOOTBALL"` property — previously only a docstring convention with zero real call sites); (2)
      wired `is_sports_structural_gap()` into `get_expected_leagues_for_source()` — that gap/allowlist SSOT
      (`SPORTS_STRUCTURAL_GAPS`/`SPORTS_SOURCE_LEAGUE_ALLOWLIST`) previously had zero production call sites (test-only),
      so a future `data_sources` hand-curation edit could silently diverge from it; verified a true no-op today
      (before/after `get_expected_leagues_for_source` counts identical across all 7 sources) but closes the ad-hoc-logic
      duplication risk. 4 new regression tests incl. a monkeypatch proving the wiring is real (not just coincidental
      agreement). quality-gates.sh green. (repo: unified-api-contracts). Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [x] ✅ [DATA] P1. **Curated-universe definition → backfill → residual drop (3-step ordered sequence, one worker,
      execute in order).** (1) Define the curated ~300-league reference set (94 + the division below each country +
      continental cups [Champions League, UEFA/UECL, Copa Libertadores/Sudamericana, AFC/CAF equivalents] + major
      internationals [World Cup, Euros, Copa America…]) per the operator's Directive A/B + the 6M-call budget analysis,
      and widen the write-gate (`_is_in_canonical_write_universe` / `get_expected_leagues_for_source`) to it. (2) THEN
      curated-universe backfill (API-Football fixtures + enrichment, 2019→, burn ~6M over weeks; gated + honest-empty
      for no-enrichment leagues). (3) THEN drop residual out-of-curated rows/objects, snapshot-first, twin-verified. Do
      not run steps 2-3 before step 1 lands — same write-gate file, same manifest. (repo: unified-api-contracts league
      registry; instruments-service write-gate + backfill VMs + `_index` + GCS objects). **Done when**: curated list
      stored + write-gate widened; fixtures+enrichment backfilled for the curated set 2019→ with honest-empty for
      no-enrichment leagues; residual out-of-curated rows/objects dropped snapshot-first. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`. — **RECONCILED 2026-07-25 (slot 4,
      data_engineering): checkbox correctly stays unchecked — this todo is ALREADY superseded-by-decomposition, not a
      fresh start.** Step 1's continental-majors slice shipped (`unified-api-contracts@7b13196e`); the 171-country
      domestic-selection slice is split into 11 confederation-batch todos in
      `issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md` (all 11 now `[x]`, see re-verify
      below). Steps 2 (backfill) + 3 (residual drop) are explicitly gated on all 11 landing first. No code touched:
      re-executing step 1 here would duplicate/collide with the already-dispatched batches; this todo's real done-when
      is now "all 11 batches + step 2 + step 3 land," tracked in the issue doc, not re-derived here. — **RE-VERIFIED
      2026-07-25 (slot 4): still unchecked** — step 2 gate MET but launch-BLOCKED on the `af-backfill-*` singleton lock
      (held by `-031`'s fixture_events re-fetch); step 3 deferred. Live tracker: issue doc's final gated item. —
      **RE-VERIFIED 2026-07-25T12:56Z (slot 11): still unchecked** — lock cleared, backfill launched (this todo's
      "2019→" text is stale vs. the 2020-06-06 sports floor, corrected), step 2 in progress, step 3 untouched. Detail in
      the issue doc (P0 fixed+shipped, instruments-service@08387531; archived+resolved:
      `/plans/archive/issues/sports_freshness_preflight_stale_scope_escape_burns_shared_quota_2026_07_25.md`). **SPOT
      preemption recurring** (2x 2026-07-26: `-013313` @04:16Z undetected 5h20m, `-103202` @09:54Z caught in ~10min once
      tightened) — each relaunch resumes cleanly, no data loss. **Enrichment MVP-scope leak found + fixed same-day**
      (per-fixture enrichment was following the 383-league curated-universe denominator instead of the 96-league MVP set
      — `unified-api-contracts@f674033f` + `instruments-service@b00e4433`; this VM is FIXTURES-only, unaffected, no
      relaunch needed): `issues/sports_enrichment_mvp_scope_leak_2026_07_26.md`. **Monitoring-gap tolerance confirmed**:
      a ~4.5hr gap in the monitoring cadence (missed/delayed wakeup) left the VM unwatched but it ran fine throughout —
      no preemption, steady ~1.85min/date pace. One isolated `attempted_failed` cluster (383 rows, all
      `date=2021-07-07`, all within an 8ms window — a single transient API-side blip) self-resolved with zero further
      failures across 8+ subsequent days; not logged as an incident, monitor for recurrence. **New OOM pattern
      2026-07-26T23:37Z**: `af-backfill-20260726-110610` `exit_code=137` at `date=2021-08-28`, after running cleanly
      ~20.5hrs / 2,400+ dates (NOT a repeat of the pre-fix unfiltered-read bug — 0 enrichment calls were queued this
      whole run) — looks like gradual memory accumulation over a long single-process runtime rather than a per-call
      trigger. Shutdown-script self-deleted cleanly, no zombie. Relaunched (default `e2-standard-8`, singleton-lock
      verified clear first) as `af-backfill-20260727-004325`; UAC tarball flagged 1-commit stale but confirmed the
      MVP-scope fix is included and irrelevant anyway (FIXTURES-only path). **Root cause found + fixed
      2026-07-27T01:10Z**: `unified-trading-library` `ManifestWriter._flush_per_vm_pending` does a full read-merge-write
      of the ENTIRE per-VM shard on every flush (a correctness requirement for concurrent same-shard writers, e.g.
      MDPS's per-unit finalize threads) — peak memory/I/O per flush grows linearly with cumulative shard size, so ANY
      single process spanning enough dates eventually OOMs regardless of per-date correctness. Rather than touch that
      concurrency-critical shared library code, routed this launcher's explicit-date-range runs through the EXISTING
      chunked `instruments-backfill` VM_TASK (already used by 4 sibling sports launchers) — 90-day chunks, each a FRESH
      process, memory resets between chunks — via `deployment-service` (launcher-only change, zero
      shared-dispatcher-code touched). Relaunched as `af-backfill-20260727-011039`, verified using the chunked path —
      ran clean through 2 full chunk boundaries (6→7, 7 dates through 2022-02-09) with zero OOM recurrence before a
      genuine SPOT preemption (`compute.instances.preempted` 2026-07-27T04:46:58Z, standard vanish-not-terminate
      pattern, no marker written — unrelated to the OOM fix). **Relaunch hit a NEW, separate issue**: this laptop's
      interactive `gcloud` account (`ikenna@odum-research.com`) had an expired token needing interactive reauth
      (`cannot prompt during non-interactive execution`) — the launcher script silently failed (exit 1, zero output)
      because it shells out to `gcloud` using the ambient active account. Root-caused via `bash -x` trace. Fix:
      `CLOUDSDK_CORE_ACCOUNT=<working-service-account>` env var scoped to just the launch command (NOT
      `gcloud config set account`, which mutates global machine-wide state shared by every concurrent slot on this
      laptop — did that once by mistake mid-diagnosis and immediately reverted it). Relaunched as
      `af-backfill-20260727-055450`, verified RUNNING + chunked task. **2nd SPOT preemption 2026-07-27T05:31:15Z**
      (~44min after the first relaunch, `last_completed_date=2022-02-24` — 1 day short of finishing chunk 7/25) — same
      clean vanish pattern, no OOM, no crash; the persistent local `gcloud` auth issue (interactive account token
      expired, workaround: `--account=`/`CLOUDSDK_CORE_ACCOUNT=1060025368044-compute@developer.gserviceaccount.com` per
      command, never `gcloud config set account` globally) is now a known non-issue baked into the monitoring loop's own
      instructions. Relaunched as `af-backfill-20260727-064958`, verified RUNNING + chunked task resuming correctly.
      Current: `af-backfill-20260727-064958`. **Check-in 2026-07-27T16:36Z (slot 15, data_engineering)**: no code
      changes — verified VM `af-backfill-20260727-064958` RUNNING (status via `gcloud compute instances describe`),
      healthy, monotonic (`run.log` tail: `[[VM_PROGRESS]] last_completed_date=2023-02-07 monotonic=true`, no OOM/error
      lines). Armed a session-local background watchdog (15-min-interval `gcloud`/GCS poll,
      `scratchpad/watch_af_backfill.sh`, NOT committed — deliberately ephemeral, trivially recreatable from this note)
      to catch stall/preemption during this session; **that watchdog dies with this session** — it is not a durable
      monitor, so the NEXT slot to touch this todo should re-verify VM health from scratch (don't assume anything is
      watching it between sessions) rather than trusting a stale "still running" from this entry. No relaunch was needed
      this check-in. Log path for future checks:
      `gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260727-064958/run.log` (note: NOT
      `central-element-323112-vm-logs` — that bucket doesn't exist; the real vm-logs prefix lives under
      `deployment-scripts-central-element-323112`). **Check-in 2026-07-27T17:17Z (slot 12, data_engineering)**:
      re-verified from scratch (per prior note's instruction, not trusting the stale "still running"). All 3
      corroborating signals fresh and consistent: VM `af-backfill-20260727-064958` status=RUNNING; `run.log` tail shows
      `last_completed_date=2023-03-10 monotonic=true` at 17:13:29Z; per-VM manifest shard mtime=17:17:03Z (essentially
      real-time write). No OOM/error lines, no preemption. No relaunch needed. No further action this check-in — next
      slot should still re-verify from scratch rather than trust this note. **Check-in 2026-07-27T19:34Z (slot 5,
      data_engineering)**: re-verified from scratch after an orchestrator restart. All 3 signals fresh: VM
      `af-backfill-20260727-064958` status=RUNNING; `run.log` shows `last_completed_date=2023-05-31 monotonic=true` at
      19:31:24Z (advanced +82 days from slot 12's 2023-03-10 in ~2h14m, ~1.65 min/date — steady) with
      `PIPELINE_HEARTBEAT` fresh through 19:32:30Z; `ManifestWriter` wrote the per-VM shard (164,903 entries, 1.59 MB)
      at 19:31:28Z (real-time); `gcloud compute operations list` shows no `compute.instances.preempted`. No OOM/error,
      no relaunch needed. ETA ~30h to reach the present-day floor-to-now range, so step 2 is still mid-run and step 3
      (residual drop) stays gated — checkbox correctly unchecked. NOTE for next slot: the interactive `gcloud`/`gsutil`
      account token is expired again (`credentials are invalid`) — use
      `CLOUDSDK_CORE_ACCOUNT=github-actions-deploy@central-element-323112.iam.gserviceaccount.com` with `gcloud storage`
      for GCS reads; still re-verify from scratch rather than trust this note. **Check-in 2026-07-27T19:50Z (slot 11,
      data_engineering)**: re-verified from scratch (default ambient `gcloud` account, `unified-trading-sa@…`, worked
      fine this check-in — no auth workaround needed). All 3 signals fresh: VM `af-backfill-20260727-064958`
      status=RUNNING (SPOT); `run.log` tail shows `last_completed_date=2023-06-10 monotonic=true` with
      `PIPELINE_HEARTBEAT` through 19:50:30Z (advanced +10 days from slot 5's 2023-05-31 in ~19min, ~1.9 min/date —
      steady, consistent with prior pace); per-VM manifest shard (`_index/per_vm/af-backfill-20260727-064958.parquet`)
      mtime=19:49:10Z (near-real-time write, 1.54 MiB). `gcloud compute operations list` filtered to this VM shows zero
      `compute.instances.preempted` events. No OOM/error lines. No relaunch needed. Step 2 still mid-run (~1,143 days of
      2023-06-10→2026-07-27 remaining at this pace, still tracking the prior ~30h-ish ETA order of magnitude), step 3
      stays gated — checkbox correctly unchecked. Next slot: re-verify from scratch, don't trust this note as current.
      **Check-in 2026-07-27T20:06Z (slot 11, data_engineering)**: re-verified from scratch (default ambient `gcloud`
      account, no auth workaround needed). All 3 signals fresh: VM `af-backfill-20260727-064958` status=RUNNING (SPOT);
      `run.log` tail shows `last_completed_date=2023-06-19 monotonic=true` with `PIPELINE_HEARTBEAT`-adjacent log lines
      through 20:04:42Z (advanced +9 days from this same slot's own prior 2023-06-10 note in ~14min, ~1.55 min/date —
      steady, consistent with prior pace); per-VM manifest shard (`_index/per_vm/af-backfill-20260727-064958.parquet`)
      Update Time=20:04:41Z (near-real-time write); `gcloud     compute operations list` filtered to this VM's
      targetLink for `compute.instances.preempted` returns zero rows. No OOM/error lines. No relaunch needed. Step 2
      still mid-run, step 3 stays gated — checkbox correctly unchecked. Next slot: re-verify from scratch, don't trust
      this note as current. **Check-in 2026-07-27T20:16Z (slot 9, data_engineering) — brief, cross-check only (slot 11
      re-verified 7min prior, avoiding a redundant full re-verification write-up)**: VM RUNNING; `run.log`
      `last_completed_date=2023-06-24 monotonic=true`, heartbeat 20:14:30Z (+5 days from slot 11's 2023-06-19 in ~10min,
      ~2min/date — consistent); manifest shard Update Time=20:16:52Z; 0 preemption events. Fully consistent with slot
      11's concurrent finding — no drift, no action needed. Step 2 mid-run, step 3 gated, checkbox correctly unchecked.
      This todo is being actively monitored by multiple slots in close succession right now; next slot should check
      timestamps before re-verifying to avoid duplicate work. **Check-in 2026-07-27T20:40Z (slot 5, data_engineering)**:
      re-verified from scratch (ambient `github-actions-deploy@central-element-323112.iam.gserviceaccount.com`, no auth
      workaround needed). All 3 signals fresh: VM `af-backfill-20260727-064958` status=RUNNING (SPOT); `run.log` tail
      shows `last_completed_date=2023-08-31 monotonic=true` with a fresh manifest-flush log line at 20:40:36Z (advanced
      +68 days from slot 9's 2023-06-24 in ~24min, ~21sec/date — notably faster than the prior ~1.5-2min/date pace; log
      shows why, not a fluke: this date range is "Enrichment-only mode... 0 extra API calls" / "0 calls queued,
      skipped_already_captured" — dates already enrichment-captured need no external API round-trips, so throughput
      jumps once the run crosses into already-enriched territory). Manifest shard
      (`_index/per_vm/af-backfill-20260727-064958.parquet`) Update Time=20:40:36Z (real-time write, 1.62MiB).
      `gcloud compute operations list` filtered to this VM's `targetLink` for `compute.instances.preempted` returns zero
      rows. No OOM/error lines. No relaunch needed. Step 2 still mid-run (2023-08-31→2026-07-27 remaining), step 3 stays
      gated — checkbox correctly unchecked. Next slot: re-verify from scratch, don't trust this note as current.
      **Check-in 2026-07-27T21:11Z (slot 14, data_engineering)**: re-verified from scratch. All 3 signals fresh: VM
      `af-backfill-20260727-064958` status=RUNNING; `run.log` tail shows `last_completed_date=2023-09-16 monotonic=true`
      with `PIPELINE_HEARTBEAT` through 21:10:30Z (advanced +16 days from slot 5's 2023-08-31 in ~31min, ~1.9min/date —
      back to the normal pace after that entry's brief enrichment-only fast burst, not a slowdown/regression); manifest
      shard (`_index/per_vm/af-backfill-20260727-064958.parquet`) Update Time=21:11:00Z (near-real-time write).
      `gcloud compute operations list` filtered to this VM's `targetLink` for `compute.instances.preempted` returns zero
      rows. No OOM/error lines. No relaunch needed. Step 2 still mid-run (2023-09-16→2026-07-27 remaining), step 3 stays
      gated — checkbox correctly unchecked. **Dispatch gate added 2026-07-27T21:20Z (slot 14, per main's BLK-cac2757a
      resolution)**: this todo had bounced to 8+ idle slots today for pure re-verify-VM-health check-ins (no action
      possible each time — the backfill walk itself takes days). Rather than continue that per-idle-slot polling
      pattern, added a named AO prerequisite `sports-curated-universe-backfill-walk-complete` (defaults `false` =
      blocking) attached to this task's `prereqs.prerequisites` in `backlog.yaml`, mirroring the cefi-Track-1 /
      sports-S2 completion-condition gate pattern elsewhere in this plan. This task will NOT re-dispatch to idle slots
      until the condition is flipped `true`. **Whoever finishes the curated-universe backfill (step 2) and the residual
      drop (step 3) MUST flip it**:
      `curl -X POST $SERVER_URL/api/prerequisites/sports-curated-universe-backfill-walk-complete -d '{"value": true, "set_by": "<slot>"}'`
      — then this todo will dispatch normally to actually flip the checkbox. Do not delete/rename this condition without
      updating `backlog.yaml`'s `prereqs.prerequisites` for this task accordingly. **Check-in 2026-07-30T08:4xZ
      (interactive session, re-verified from scratch per this section's own instruction)**: the backfill VM
      (`af-backfill-20260727-064958`) is GONE from GCE (`gcloud compute instances     describe` → not found) — checked
      its final `run.log` (`gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260727-064958/run.log`)
      instead of assuming preemption: it **completed successfully 2026-07-28T05:34:06Z** —
      `chunk=25/25     range=2026-05-06→2026-07-25`, `DEPLOYMENT_COMPLETED ... exit_code=0`, clean self-delete on
      completion, not a preemption-vanish. Step 2 (curated-universe backfill) is DONE and has been for over 2 days;
      nobody checked back since the last logged check-in (2026-07-27T21:11Z, ~8h before it actually finished). Confirmed
      the prerequisite is still `false` (`data/config/state.json`'s `prerequisites` entry:
      `set_by: slot-14, set_at:     2026-07-27T21:21:12Z` — unchanged since it was created, i.e. never touched
      post-completion). **Not executed in this check-in** (deliberately — this needs its own careful pass, not a
      tack-on): (a) verify the backfill's actual data completeness against the curated ~300-league set (the run.log
      confirms the WALK finished, not that every league's data is honest-complete — a separate manifest-level check);
      (b) execute step 3 (drop residual out-of-curated rows/objects, snapshot-first, twin-verified per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`); (c) only then flip the prerequisite via the curl
      command above. — **CLOSED 2026-08-04 (slot 16)**: BLK-aa587dbf ruling executed, fix
      `instruments-service@0877f849`, snapshot-first drop of 8,937 rows; full evidence in
      `issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md`. AO prereq flipped `true`.

### From `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`

- [x] ✅ [SCRIPT] P0. **Fix `fixture_id=NULL` propagation in the odds_api backfill path** — golden window `trades` data
      has all fixture_ids as NULL, which blocks per-fixture cluster validation entirely. Likely market-tick-data-service
      (`market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` + `fixture_id_resolver.py`, which
      already has partial `af_fixture_id` join scaffolding) — NOT instruments-service despite the source doc's
      frontmatter; confirm exact ownership at execution time (grep both repos for the golden-window trades write path)
      before scoping. (repo: market-tick-data-service). **Done when**: golden-window (2025-09-01..2025-11-30) odds_api
      `trades` rows carry a non-NULL `fixture_id` (or the existing `af_fixture_id` join is confirmed to already satisfy
      this — either outcome is determinable); a regression test proves `fixture_id` is stamped on newly-captured trades
      rows; `quality-gates.sh` green. Source: `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`. — FIXED
      2026-07-25 (slot 7, data_engineering): confirmed ownership is market-tick-data-service, not instruments-service
      (instruments-service only owns the FIXTURES reference table `af_fixture_id_resolver.py` reads from — it has no
      odds_api trades write path at all). Root cause: `_build_fixture_rows()` in `odds_api_adapter.py` correctly
      resolves + stamps `af_fixture_id` on every row (this half already worked, with existing test coverage), but the
      row dict never contained a key literally named `fixture_id` — only `af_fixture_id`. The actual write path,
      `market_tick_data_service/engine/orchestrator/venue_fetch.py::_process_sports_venue_with_leagues()`, normalises
      via `if "fixture_id" not in records_df.columns: records_df["fixture_id"] = ""` and then GROUPS shards by
      `["bookmaker_key", "league_id", "fixture_id"]` — since odds_api rows never had that column, this branch always
      fired, forcing every row's `fixture_id` to `""` and collapsing odds_api into league-level shards instead of
      per-fixture ones (exactly the golden-window symptom; `opticodds_adapter.py` already does this correctly for
      comparison). Fix: `_build_fixture_rows()` now also emits
      `"fixture_id": str(af_fixture_id) if af_fixture_id is     not None else ""` alongside the existing
      `af_fixture_id`, matching the string-shard-key convention `venue_fetch.py`/`opticodds_adapter.py` already use.
      Extended `test_odds_api_fixture_id_join.py` with `fixture_id` assertions on all 4 existing test cases
      (matched/unresolved/no-fixture-data/end-to-end via `download_batch()`) — 6/6 tests pass.
      `quality-gates.sh --no-fix` green (fresh, not cached). — market-tick-data-service@3401c0ab.

### From `sports_odds_feature_naming_canonicalization_2026_07_21.md`

> Sequencing note for AO: the 5 todos below (spanning features-service, unified-api-contracts, ml-service, and
> strategy-service ×2) are each in a DIFFERENT file, safe to dispatch concurrently. A 6th todo from this source doc (the
> cross-repo FSS↔ml-service↔strategy-service parity test) is DELIBERATELY EXCLUDED here because it depends on ALL 5 of
> these landing first and this plan has no mechanical way to gate one todo on 5 siblings without serializing the whole
> plan — add it as a new todo (in this plan or a successor) once these 5 are confirmed shipped.

- [x] ✅ [DATA] P1. **New compute, not a rename**: add per-bookmaker raw decimal-odds retention to
      `features_service/sports/calculators/` (whatever calculator currently collapses per-venue quotes into
      `best_odds_*`/`odds_variance_*` — trace it first) so a `decimal_odds_<outcome>_<venue>` shape can actually be
      populated for `SportsArbDutchingEngine`. (repo: features-service). **Done when**: a decimal odds field keyed per
      outcome+venue (final name per the decided scheme, e.g. `odds_decimal_home_pinnacle`) is computed and populated in
      FSS output for real bookmaker/venue combinations. Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`. — SHIPPED 2026-07-25 (slot 7, data_engineering):
      `_pivot_bucketed_to_fixture()` (`odds_features_exporter.py`) now emits one `odds_decimal_<outcome>_<venue>` column
      per bookmaker actually quoting a fixture (venue = the raw lowercase bookmaker_key, e.g.
      `odds_decimal_home_pinnacle`). Critical fix required beyond the tap point alone: `compute_odds_batch()` rebuilds
      its output frame from scratch (`event_id` + its own fixed `ODDS_COLUMNS`), so the new dynamic columns from
      `_pivot_bucketed_to_fixture`'s output would be silently dropped — added an explicit merge-back in
      `export_odds_features()` right after `compute_odds_batch()` runs, the same pattern `available_at` already uses for
      the identical reason. 3 new/extended tests (2 unit-level on `_pivot_bucketed_to_fixture`, 1 end-to-end through the
      REAL `compute_odds_batch` proving the merge-back survives) — 47/47 pass in `test_odds_features_exporter.py`.
      `quality-gates.sh --no-fix` fresh green. — features-service@b03a6de4. **Known limitation, filed as a follow-up
      (not blocking this todo's done-when)**: the new dynamic columns bypass `feature_expectations.py`'s
      `ODDS_COLUMNS`-registry PIT horizon-gating (`apply_horizon_gate()` only walks a fixed list, no prefix match) — see
      the new `[DATA] P2` todo below. **Separate finding filed, NOT part of this todo's scope**:
      `compute_odds_batch()`'s dead-code `bookmaker_home_cols` path silently overwrites `best_odds_*` with a mean
      instead of the correct max — see `issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`.
- [x] ✅ [DATA] P2. **PIT horizon-gating gap for the new `odds_decimal_<outcome>_<venue>` columns** (found while
      shipping the todo above): `feature_expectations.py`'s `ODDS_COLUMNS` registry drives PIT horizon-gating
      (`apply_horizon_gate()`), which only walks a fixed column list — the new dynamic per-venue columns aren't in it
      and so bypass PIT gating entirely (there's no schema allowlist blocking them at the parquet-write boundary either,
      so they DO reach output — just ungated). Add a pattern-match (e.g. `startswith("odds_decimal_")`) to
      `apply_horizon_gate()`/`get_column_horizons()` so these get the same leak protection as every other odds field.
      Add a regression test proving a T-24h row's `odds_decimal_*` doesn't leak a later horizon's value. (repo:
      features-service) — features-service@daa373bd. Extended `apply_horizon_gate()` to pattern-match the
      `odds_decimal_` prefix, gating those dynamic columns at the same horizon as the static "odds" group (read from the
      registry via `_ALWAYS_FULL_GROUPS["odds"][1]`, not duplicated, so a future change to the odds group's horizon
      stays in sync automatically) — `get_column_horizons()` itself stays a static SSOT dict (unchanged contract for
      downstream consumers); the dynamic extension happens only inside the sports `apply_horizon_gate()` wrapper, which
      has the live `df.columns` needed to pattern-match. 2 regression tests: one confirming the columns survive gating
      at T-24h (their real home horizon); one monkeypatching a later horizon and confirming the column then gets NaN'd,
      proving the wiring is genuinely real rather than coincidentally matching the untouched-metadata path. Session
      survived a mid-task session death (this exact fix was lost and had to be reapplied byte-for-byte before shipping —
      verified via git status showing a clean tree post-resume). `quality-gates.sh` green.
- [x] ✅ [DATA] P1. **Rename UAC's `OddsFeaturesMixin`/`SportsFeatureVector` fields** — unified-api-contracts@689efa54 +
      ml-service@91f031a. All 49 fields renamed to the decided scheme, grounded in `features-service`'s actual
      calculator output (`odds_calculator.py`/`odds_velocity.py`) and live consumers, not a blind find-replace — several
      old fields shared a literal string with UNRELATED same-named columns in other layers (MDPS's raw handicap-line
      bucket column, FootyStats' vendor API field, a synthetic mock-odds generator); confirmed via workspace-wide grep +
      context-read before touching anything, so those were correctly left untouched. **Collision resolution**:
      `market_home_odds_best`/`market_away_odds_best` win the `odds_decimal_` slot (this scheme's own worked example,
      `best_odds_home` → `odds_decimal_home`, and what `SportsValueBettingEngine` needs);
      `odds_home_win`/`odds_draw`/`odds_away_win` (a DIFFERENT, currently-live FSS column under the exact same old name)
      got the distinct `odds_moneyline_` metric instead of colliding with it. Same pattern for
      `market_home_away_odds_ratio` vs `odds_home_away_ratio` (a `consensus` qualifier disambiguates the schema-only
      one). **Production-safety carve-out**: `odds_sharp_money_on_home`/`_away` and the 6 fixed-line over/under fields
      were deliberately left UNCHANGED — they exact-match a currently-live FSS producer column today, and renaming them
      would have zeroed out `SportsFeatureLoaderMixin._validate_odds_schema`'s producer/consumer overlap check (an
      already-shipped loud-fail gate) ahead of FSS's own migration (the P2 todo immediately below, not yet landed) with
      no compensating benefit — documented in the class docstring so this isn't rediscovered. New UAC test file (none
      existed for this class before) asserts the exact field set, retired names are gone, and the deliberately-unchanged
      set survives; fixed the 2 hardcoded old-field-name test fixtures + 1 stale docstring reference this rename broke
      in `ml-service`'s `test_sports_feature_loader.py`/`sports_feature_loader.py` (an adjacent, same-turn fix — that
      test suite directly imports `OddsFeaturesMixin`). **Known transitional gap**: several renamed fields (e.g.
      `odds_asian_handicap_line`, `prob_implied_btts_*`) DO exact-match a currently-live FSS column under their OLD
      name, per this scheme's own worked examples — those were renamed anyway (the operator's explicit table example),
      so `SportsFeatureLoaderMixin`'s loud-fail gate will correctly start firing for real `odds_features` loads touching
      those specific fields until the P2 FSS-side migration lands; this is the gate doing its designed job (loud, not
      silent), not a regression, but P2 should be prioritized to close the window. Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`.
- [x] ✅ [DATA] P1. **Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS`** + the
      odds-features exporter to emit the UAC-chosen field names instead of the current `home_implied_prob`-style
      convention; update exporter tests + downstream fixture files. (repo: features-service). **Done when**: all 180
      `ODDS_COLUMNS` entries + exporter output renamed per the decided scheme; exporter tests and downstream fixtures
      updated; quality-gates green. Source: `sports_odds_feature_naming_canonicalization_2026_07_21.md`. — SHIPPED
      features-service@{0ded2449,e240eca2,0ab873b3}; full detail in source plan.
- [x] ✅ [BACKEND] P2. **Close the silent-agnostic gap in `SportsFeatureLoaderMixin`** — ml-service@07976ae. Added
      `_validate_odds_schema` (checked only for the `odds_features` group): raises `ValueError` when a non-empty frame
      has ZERO columns overlapping UAC `OddsFeaturesMixin`'s known field set — a producer/consumer naming mismatch,
      never honest absence. 3 new regression tests: a deliberately mismatched fixture (real pre-migration FSS names
      `home_implied_prob`/`draw_implied_prob`) raises loudly, a matching fixture (`odds_home_win`) still loads, and
      non-`odds_features` groups are never schema-validated. quality-gates.sh green (2103 passed).
- [x] ✅ [BACKEND] P2. **Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine`** + the legacy
      `sports_feature_subscriber.py` — strategy-service@4c55438c. Renamed `decimal_odds_<outcome>` →
      `odds_decimal_<outcome>`, `decimal_odds_<outcome>_<venue>` → `odds_decimal_<outcome>_<venue>`,
      `fair_prob_<outcome>` → `prob_fair_<outcome>`, `ht_odds_{home,draw,away}_implied` →
      `prob_implied_{home,draw,away}` per the 2026-07-23 decided scheme. Updated the 3 direct unit test files, the
      `ARBITRAGE_SPORTS_DUTCHING` branch of `test_all_catalogued_archetypes_construct_and_fire.py`'s smoke test, and the
      dutching leg of `scripts/run_sports_arb_backtest.py`. Left the generic (non-sports)
      `ml_directional`/`rules_directional` `event_settled.py` engines untouched — they share the OLD `decimal_odds_`
      prefix incidentally but are NOT part of this migration's decided scope. quality-gates.sh green (5583 passed, 5
      pre-existing xfails unrelated to this change). NOTE: this is 1 of 3 independent per-repo renames in the same
      migration (UAC `OddsFeaturesMixin` + FSS's exporter, both still `[ ]` above) — a temporary window where they don't
      all agree is expected per the operator's own sequencing note (sports is backtest-only, no live wiring).

### From `data_completion_sports_2026_07_24.md`

- [x] ✅ [DATA] P1. **Post-backfill entity-coverage relabel — PREMISE RESOLVED, not executed as a relabel; residual
      filed separately.** The 6 named backfill VMs ARE confirmed terminal (0 sports-tagged GCE instances, running or
      otherwise, in `central-element-323112` as of 2026-07-25). But BEFORE running the prescribed relabel, I measured
      the current manifest directly: the diagnosed 789-league/1,027,396-row phantom `expected_unattempted` set in the
      2026-02-20→06-19 window is now **33,905 rows across 96 league_ids — ALL 96 in the current in-universe set, ZERO
      out-of-universe leagues remain in-window** (a ~30x reduction, resolved as a side effect of the intervening
      write-gate + dereg + canonicalize program, instruments-service@0345ffc through 2026-07-21). The prescribed
      "no-coverage pairs → expected_empty" script no longer matches the manifest's actual shape and running it blind
      risks mislabeling genuine post-cutover pending-fetch gaps as false-empty (the residual is dominated by the
      2026-07-14+ `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` split-entity backfill, not raw-league over-enumeration). Also
      found a DIFFERENT, currently-RUNNING sports backfill VM (`af-backfill-20260725-002739`, unrelated to the
      original 6) writing `_index/availability_index.parquet` directly and unsharded — confirms the manifest is not
      safely drained for an unprotected RMW regardless of the premise question. Filed
      `issues/sports_post_backfill_relabel_premise_resolved_residual_gap_2026_07_25.md` with the full measurement + 3
      correctly-scoped follow-up todos rather than force a stale-premise migration against a live-changing production
      manifest. Source: `data_completion_sports_2026_07_24.md`.
- [x] ✅ [DATA] P1. **Relaunch features-sfi-progressive** — code fix already shipped (`features-service@06c44c02`);
      launcher confirmed pointed at `features_service.sports.scripts.compute_sfi_progressive_only`; confirmed
      market-tick-data-service clean; SPORTS tarball rebuilt (all 5 fresh: features-service@26c96a55, mtds@1dbdbb90,
      uac@0b979239, utl@5e89c404, deployment-service@184aa81d). Relaunched via
      `RECOMPUTE_FORCE=true launch-sfi-progressive-features-backfill-vm.sh --force 2020-01-01 2026-07-25` on
      `features-sfi-progressive-20260725-163937` (SPOT, asia-northeast1-c). **Done**: run.log shows zero
      `MissingFeatureFamilyError`/`ERROR` lines, `PROGRESSIVE_DAY_CAPTURED` events throughout,
      `captured_days=2087     failed_days=0`, `command exited rc=0`, `DEPLOYMENT_COMPLETED ... exit_code=0`. (repo:
      deployment-service `scripts/vm/launch-sfi-progressive-features-backfill-vm.sh`,
      `scripts/vm/create-code-tarballs.sh`; features-service
      `features_service/sports/scripts/compute_sfi_progressive_only.py`). **Already-resolved citation (was
      `[OPERATOR]`)**: `RECOMPUTE_FORCE=true --force` overwrote captured prod manifest rows for 2020-01-01→2026-07-25 +
      launched a billed VM — operator go-ahead was already given in-session 2026-07-25 and the run completed cleanly
      (see "Done" above), cite `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. No further sign-off needed;
      kept here only as the historical evidence trail for the already-executed action. Source:
      `data_completion_sports_2026_07_24.md`.

### From `sports_legacy_cutover_closeout_tasks_2026_07_24.md`

- [x] ✅ [DATA] P2. **T6.8 — retire the one-offs + the dead knob + the false-progress tick — SAFE SUBSET SHIPPED,
      residual tracked.** Per-file `Delete-when` + git-history/import-graph verification found the blanket-delete
      premise false for `migrate_sports_canonical_v9.py` (live import chain) and most of the "~26"
      `instruments-service/scripts/**` grep-estimate (permanent-lifecycle / broader-campaign-gated / recently-active /
      unverifiable). Shipped: the doubly-broken gate + 2 named one-offs (market-tick-data-service@f8276e22); full
      `include_legacy_archive` knob retirement after fixing its 1 live caller (unified-api-contracts@887ab894,
      instruments-service@5ff530f9) — `rg 'include_legacy_archive'` → 0 hits workspace-wide; the 5
      independently-verified `instruments-service/scripts/**` one-offs shipped same-day (instruments-service@269440d7);
      v1_archive gate un-tick/correction already done (unified-trading-pm@3aff7f716). Residual (v9-cluster + ~14
      unverified one-offs) tracked, not dropped:
      `/plans/archive/issues/sports_t6_8_oneoff_retirement_residual_2026_07_25.md`. The todo's own literal final gate
      (`rg -c 'sports-central-element-323112'` → 0) is corrected as unachievable — many remaining hits are legitimate
      permanent-lifecycle/doc references; see the source doc for full detail. Source:
      `sports_legacy_cutover_closeout_tasks_2026_07_24.md`.

### From `sports_prelaunch_cf5_verify_residual_2026_07_24.md`

- [x] ✅ [DATA] P1. **Sports CF-5 oracle relabel = ZERO — landed.** — market-tick-data-service@7f1262a0. Confirmed
      `origin/wip-preserve/mtds-346-cf5-trades` (`mtds@d0a15a3`, 2026-06-16) had NOT landed and was too stale to
      cherry-pick wholesale (predates + would regress the 2026-07-13 SFI_PROGRESSIVE_STATS retired-set fix and several
      later CF-11/attempted_at/chain-blank fixes on the same file). Applied the isolated one-line fix
      (`"trades"`→`"TRADES"` in `_PER_FIXTURE_DERIVED_DATA_TYPES`) directly on current HEAD + adapted the wip branch's
      regression test onto current HEAD (not restored wholesale). TDD-verified: confirmed the new test fails against the
      pre-fix lowercase entry and passes with the fix. quality-gates.sh green. Landing required several retries —
      quickmerge's full-suite re-gate hit genuine host-load-induced infra flakiness (pytest-xdist worker crash under
      load 17-30 on an 8-core box, 3+ concurrent slots running full QGs simultaneously), not a content issue; landed
      once host load allowed a clean re-gate pass. (repo: market-tick-data-service). **Done when**: worker confirms
      landed-or-not first (citing the check); if not landed, the fix + its regression test are confirmed present on
      market-tick-data-service main/LDR HEAD, citing the landing commit sha. Source:
      `sports_prelaunch_cf5_verify_residual_2026_07_24.md`.

### From `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`

> The doc's 3rd todo (a `FixturesBrowser.tsx` UI relabel) is EXCLUDED here — it's explicitly gated on the backend todo
> below landing first ("once P10-B backend lands"). Add it as a follow-up once this todo ships.

- [x] ✅ [BACKEND] P2. **Switch `deployment-api/services/fixtures_browser.py` to the single catalogue** —
      deployment-api@dbbf64c. Reads `prod/catalog.parquet` ONCE (schema-aware projection), TTL-cached as a parsed frame
      filtered to `instrument_type=="fixture"` (mirrors `prediction_catalogue.py`'s `_read_catalogue`).
      `fixture_id`=`instrument_id`; `home_team_id`/`away_team_id` parsed from the id's `HOME_v_AWAY` segment;
      `venue_id=""` (honest, not carried). Filters AND groups on `available_from`, not `kickoff_utc`. Deleted
      `_MAX_WINDOW_SPAN_DAYS` (kept `_MAX_WINDOW_SIDE_DAYS` as a sane bound on the relative-window defaults only — no
      longer a read-cost bound). Rewrote `test_fixtures_browser.py` entirely for the new architecture (mocks
      `_read_catalogue_fixture_frame`, not the retired day-walk primitives); added coverage for team-id parsing,
      honest-blank `venue_id`, `instrument_type` filtering, available_from-vs-kickoff-day grouping, and the removed span
      cap. `quality-gates.sh` green (4964 passed).

### From `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`

> The doc's 4th todo (a real-backfill timing verification) is EXCLUDED here — it depends on both todos below landing
> first. Add it as a follow-up once both ship.

- [x] ✅ [DATA] P2. **Manifest-slice replacement for `check_api_football_dependency()`** —
      `instruments-service@bd1da540`. Added `_manifest_shows_fixtures_captured()`: a pyarrow-pushed-down
      `read_availability_index()` slice (`date`/`data_type`/`capture_status`, ~0.1s/call) as the PRIMARY check, matching
      `data_type in {FIXTURES, FIXTURES_SCHEDULE}` + `capture_status == "captured"` — NOT `venue ==     "API_FOOTBALL"`
      per the issue doc's prose: live-data probe found these rows carry an EMPTY `venue` column, api-football identity
      is implied by `data_type` alone. Verified equivalent to the old GCS-probe verdict against 12+ real dates
      (2024-2026, incl. 2 genuine-miss dates) before writing tests. Old GCS-probe KEPT UNCHANGED as fallback
      (manifest-read failure/staleness returns `False`, never raises) — path-template duplication is moot since the hot
      path no longer touches them, per this todo's own anticipated outcome. 9 new/updated unit tests. `quality-gates.sh`
      PASSED. Source: `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`.
- [x] [DATA] P2. ✅ **Cached/batched fix for `sports_fixtures.py:356`** — `instruments-service@2be5698d`. The doc's
      stated path (`instruments_service/reference_data/sports_fixtures.py`) was stale — the real file is
      `instruments_service/engine/orchestrator/sports_fixtures.py`, and the actual per-(entity×league) primitive
      (`_read_existing_per_league_fixture_ids`, called from
      `sports_reference_fixtures.py::_read_captured_per_entity_league`) had ALREADY been fanned out concurrently by a
      prior fix (`api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md`) — wall-clock was
      already fixed, but call COUNT was unchanged (still up to ~4 entities × ~33 leagues individual `.exists()` probes).
      No per-date consolidated parquet exists in the real storage layout (verified: each league is a genuinely separate
      GCS object under `entity={entity}/league={L}/`), so a true single-read-per-date isn't achievable — the real
      ceiling is per-ENTITY batching via the ALREADY-EXISTING shared helper `_read_per_league_entity_df` (same one used
      to fix the other ~9 sites in this issue doc), which lists+downloads every league's data for one entity+date in a
      single pass. Implemented as a new small cohesion module (`sports_fixture_prefetch_skip.py` — kept
      `sports_reference_fixtures.py` under the 900-line ratchet) with `_read_captured_league_fixture_ids_for_entity()`
      (batched per-entity read) + `_captured_fixture_ids_by_league()` (grouping helper); collapses call count from
      O(entities × leagues) to O(entities) — up to ~132 individual `.exists()` probes down to `len(entities)` (typically
      ≤4) `list_blobs` passes. Removed the now-dead `_read_existing_per_league_fixture_ids` (zero remaining callers,
      confirmed via full-repo grep) + its 2 stale `__all__` exports. Rewrote the 2026-07-18 concurrency regression tests
      (`TestGatherPerFixtureRowsBatchedPreFetchSkip`, was `...ConcurrentPreFetchSkip`) to prove the NEW invariant — 1
      batched call per entity regardless of league count (not just wall-clock) — while preserving entity-level
      concurrency coverage; added 3 new direct unit tests for the grouping/batched-read helpers (fid-column fallback,
      no-blobs-found, transport-failure fail-safe-empty). Fixed 4 existing integration-test mock targets (facade path
      changed with the module split). Full `quality-gates.sh` green (4880+ tests, 0 basedpyright errors beyond the
      pre-existing warn-only ceiling, file-size ratchet clean). Source:
      `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`.

### From `issues/sports_legacy_duplicate_triage_2026_07_22.md`

- [x] ✅ [DATA] P1. **Migrate-forward the 58 v2 post-floor rows** (16 days) into canonical per-league `entity=fixtures`
      / `entity=fixture_stats` — reuse `migrate_sports_per_league.py`'s per-fixture-league-join logic, not a delete.
      Re-run the sweep after to confirm these flip to `A_canonical`. (repo: instruments-service —
      `scripts/migrate_sports_per_league.py` logic against bucket `instruments-store-sports-prd`; re-run
      `scripts/migration_orphan_sweep_sports.py --bucket reference` afterward). **Done when**: all 58 rows across the 16
      days have canonical objects written, and a re-run of the orphan sweep reclassifies them as `A_canonical` instead
      of `B_legacy_duplicate`. Source: `issues/sports_legacy_duplicate_triage_2026_07_22.md`. —
      **instruments-service@9d76160f**: 65 new canonical files/145 rows (additive, v2 untouched), verified A_canonical.
- [x] ✅ [CODE] P1. **Repoint or retire the two flat-legacy readers — INSTRUMENTED, not removed** (correctly: ~478 of
      28,100 rows have no canonical twin, sole source is the fallback). (a) instruments-service@693280e7:
      `sports_reference_fixtures.py:139`'s old-path branch now logs a greppable `LEGACY_FLAT_PATH_HIT` warning on every
      hit. (b) deployment-service@734fdd5: `data_status_sports.py`'s level-4 fallback (both duplicate call sites) log
      the same marker. 4 new regression tests (3 DS + 1 IS) prove the marker fires on real hits, stays silent on
      canonical/split-entity hits. `quality-gates.sh` green both repos. Part 4 re-run: 2 live readers unchanged
      (instrumentation ≠ removal) — now measurable via log-based metrics before any delete reconsideration. Source:
      `issues/sports_legacy_duplicate_triage_2026_07_22.md`.
- [x] ✅ [REVIEW] P3. **Rescan `migration_orphan_sweep_sports.py --bucket reference`** to retire the 4,735 stale
      (already-deleted) flat pre-floor rows from the durable audit parquet, and fix the classifier's
      `is_covered_sports`-before-`_is_pre_launch` ordering so pre-floor cells with a stale-captured manifest row
      classify `C3_pre_launch_window` instead of `B_legacy_duplicate` (mirrors the already-shipped E-class fix,
      `unified-api-contracts@46d865df`, on a different branch of the same function). (repo: instruments-service
      `scripts/migration_orphan_sweep_sports.py`; unified-api-contracts classifier mirror). **Done when**: rescan no
      longer surfaces the 4,735 stale rows; classifier ordering fix causes correct classification, mirroring the
      already-shipped E-class pattern. Source: `issues/sports_legacy_duplicate_triage_2026_07_22.md`. —
      **instruments-service@6cf44d31**: `classify_reference_object`'s flat/non-`by_date` branch now checks
      `_is_pre_launch` BEFORE `is_covered_sports` (day-less FLAT singletons unaffected — `_is_pre_launch` returns
      `False` on `day=""`); the pre-existing "covered wins" semantics on the SEPARATE `by_date`-tree branch (tested by
      `test_pre_launch_window_is_c3_not_e`) are deliberately left untouched — a different, already-decided policy
      question (the v2 pre-floor 728-row disposition, issue doc §7 todo 1, `[OPERATOR]`-gated). 36/36 unit tests green
      (incl. new regression `test_flat_legacy_pre_floor_stale_captured_is_c3_not_b`); QG green. Live rescan run against
      `instruments-store-sports-prd-central-element-323112` (2026-07-25): fresh audit parquet written to
      `_index/audit/orphan_sweep_sports.parquet` — verified **0** flat pre-floor `B_legacy_duplicate` rows remain (down
      from 4,735); new counts `B_legacy_duplicate=27,238` / `E_orphan_real=2,179` / `C3_pre_launch_window=800` (30,217
      actionable rows total, 916,394 objects walked).
- [x] [REVIEW] P3. ✅ **Cross-file the archived `sports_master_closeout_2026_07_21.md`'s pending "MANIFEST prune"
      deferred task** — the 944,776 phantom pre-floor manifest rows it already tracks are the root cause of this doc's
      §2 misclassification too. (repo: unified-trading-pm — add a cross-reference note to the archived plan's existing
      pending item). **Done when**: the archived plan's pending MANIFEST-prune item carries an added cross-reference to
      `issues/sports_legacy_duplicate_triage_2026_07_22.md` noting the shared root cause. Source:
      `issues/sports_legacy_duplicate_triage_2026_07_22.md`. Added cross-reference to both
      `plans/archive/2026_07/sports_master_closeout_2026_07_21.md` (PENDING EXECUTION item) and its companion
      `sports_master_closeout_progress_log_2026_07_24.md` (tracking table row) — unified-trading-pm@243998b6c.

### From `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`

- [x] ✅ [DATA] P3. **Fleet-wide sweep for the same seeder-over-captured pattern** — CLEAN, no unguarded asset_group.
      `enumerate_v2()`'s `captured_set` drop-filter is ONE choke point after per-AG dispatch (no `sports`-only gate) —
      structurally universal across all 5 `_V2_ENUMERATORS`. All 5
      `expected-universe-v2-{cefi,defi,tradfi,sports,     prediction}` jobs share ONE terraform image ref; each job's
      most recent (2026-07-25 ~01:30 UTC) execution resolved to the SAME digest `sha256:e88f3ded52…` = current
      `:latest`, tagged `f539945` (built 2026-07-23, 10d after guard commit `ba306543` 2026-07-13) — content-verified
      present (`merge-base --is-ancestor` reads false only due to the LDR→main squash, not a real gap). Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`.
- [x] [CODE] P1. ✅ **Extend the "never emit `empty_confirmed` over a captured atom" guard** to the regular sports
      instruments batch-capture emission path (`sports_fixtures.py`/`sports_reference_core.py` or wherever
      `uts-prod-instruments-service-sports-fixtures`'s `--operation=instruments --mode=batch --asset-group=SPORTS` run
      emits `EXPECTED_NO_FIXTURE`/`EXPECTED_PAUSED_LEAGUE`/etc.) — same guard shape as `ba306543`
      (`enumerate_expected_universe.py`'s `captured_set` check), applied to this SEPARATE code path. (repo:
      instruments-service — exact emission site TBD by worker on read). **Done when**: a `captured_set`-style guard is
      added to the batch-capture emission path; unit tests added and passing; a fresh production run no longer produces
      new masking rows of the observed pattern. Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`. — DONE 2026-07-25: exact emission site found at
      `process_write._write_sports_fixture_venue`'s empty-gap loop
      (`instruments_service/engine/orchestrator/     process_write.py`) — the ACTUAL masking writer named in the issue
      doc's "ROOT CAUSE CORRECTED" section. Added `_manifest_captured_fixture_leagues` (`sports_reference_core.py`, kept
      out of `process_write.py` to stay under the 900-line file cap) — a single filtered manifest read (row-group
      pushdown on date, slim columns) building the set of leagues already CAPTURED for FIXTURES_SCHEDULE on this date;
      unioned into the empty-gap exclusion set. A manifest-read failure returns `None` and the caller skips the whole
      empty-emission pass (fail-safe, mirrors `_AfManifestHooks._presence_guarded_captured_leagues`'s existing contract)
      rather than risk masking. 6 new unit tests (`tests/unit/test_process_write_fixtures_captured_guard.py`) cover the
      guard helper (canonical-captured filtering, empty-index, read-failure fail-safe) and the integration
      (manifest-captured league excluded even with zero this-run captures; this-run-captured league still excluded;
      read-failure skips empty-emission entirely) — QG green (909 sports/fixture/process_write tests passing, full
      quality-gates.sh green). The "fresh production run no longer produces new masking rows" half of done-when is a
      live-verification follow-up for the NEXT real `uts-prod-instruments-service-sports-fixtures` production run (code
      is now shipped to LDR; not independently re-verified against live prod data in this session) —
      instruments-service@450b1b58.
- [x] [INFRA] P3. **Downgrade, don't drop, the original "redeploy expected-universe-v2-sports" todo** — that image IS
      current (`:latest` confirmed to contain `ba306543` as of 2026-07-23T08:07:36Z) and Cloud Run Jobs re-pull a
      mutable tag per execution, so no redeploy is likely needed; the doc's own 2026-07-23 second-pass trace found the
      actual masking writer is a DIFFERENT job entirely (`uts-prod-instruments-service-sports-fixtures`) — do NOT
      dispatch a literal redeploy of `expected-universe-v2-sports`. (repo: instruments-service/deployment-service —
      verification only). **Done when**: `gcloud run jobs describe expected-universe-v2-sports` confirms the job pulls a
      mutable `:latest` tag; verification result recorded; this todo (and the superseded original redeploy todo) marked
      resolved with no further action, or a follow-up filed if pinned. Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`. — ✅ 2026-07-24 VERIFIED:
      `gcloud run jobs describe expected-universe-v2-sports --project=central-element-323112 --region=asia-northeast1`
      confirms the container image is `...instruments-service:latest` (mutable tag, not pinned); 3 most-recent
      executions (2026-07-22/23/24, all 01:30Z) completed successfully. No redeploy needed. Both this todo and the
      original redeploy todo marked resolved in
      `plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md`.

### From `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`

- [x] ✅ [CODE] P1. **Stop stale/zombie ticks at bucket assignment** (fix locus: MDPS, not MTDS raw ingestion). Primary
      fix in `market-data-processing-service/.../adapters/sports/bucket_assignment_adapter.py`: drop rows whose
      `staleness_seconds` (`fetch_utc − bm_time`) exceeds a sane cap (hours-scale, ≥ the largest horizon window) or
      whose `kickoff_utc` is far outside the fetch day's horizon reach, BEFORE horizon assignment — record
      honest-absence/zero rows for that league-day instead. Per the doc's own status: the post-kickoff (`bm_minutes<0`)
      half already landed (`mdps@3bf56ff`); the remaining gap is specifically the `staleness_seconds` cap /
      `kickoff_utc`-vs-fetch-day check in `assign_horizon_bucket()` and `assign_horizon_buckets_vectorised()` — the
      pre-kickoff-positive Russia-Premier-League zombie class (`bm_minutes≈1423≈T-24h`) is confirmed still unfixed as of
      2026-07-23. (repo: market-data-processing-service `app/adapters/sports/bucket_assignment_adapter.py`). **Done
      when**: both functions reject a tick before bucket assignment when `staleness_seconds` exceeds the cap or
      `kickoff_utc` falls outside the fetch day's horizon reach; the known zombie fixtures no longer land in any horizon
      bucket on re-processed days, while a genuine single-snapshot real-fixture case is NOT dropped; covered by a
      unit/regression test for both zombie classes plus the real case. Source:
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`. — SHIPPED 2026-07-25 (slot 7, data_engineering):
      added `STALENESS_CAP_SECONDS` (48h — comfortably ≥ the largest horizon window, 24h/1440min) and
      `KICKOFF_PAST_CAP_SECONDS` (7 days) checks to `_prepare_tick_data()`, the single choke point BOTH
      `process_to_candles()` and `process_to_bucketed_df()` already call before `assign_horizon_bucket(s)` — a **design
      choice, not literally inside those two functions as the todo text implies**: `_prepare_tick_data` is where the
      existing causality filter (`bm_time <= fetch_utc`) already lives, so this mirrors that established pattern and
      protects both entry points identically without duplicating the check. `staleness_seconds` catches the
      Russia-Premier-League zombie class directly (bm_minutes≈1423≈T-24h but bm_time 3.5 years stale);
      `kickoff_utc`/`commence_time` (naming varies by corpus generation, same fallback as `_derive_match_midnight_us`)
      is a second independent signal. 5 new tests (years-stale-bm_time, fresh-scrape-not-dropped,
      partial-drop-still-processes, years-past-kickoff, genuine-near-term-kickoff-not- dropped) — 67/67 pass.
      `quality-gates.sh --no-fix` fresh green (75s, sentinel not cached). market-data-processing-service@aa6e8ac.

### From `issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`

- [x] ✅ [CODE] P1. **WEATHER layout mismatch — confirm, align, reverify (3-step ordered sequence, one worker).** (1)
      Confirm the writer's intended WEATHER layout is `PER_DAY_PER_LEAGUE` (read the IS weather writer
      `instruments_service/engine/orchestrator/weather.py` + confirm no bare `entity=weather/weather.parquet` objects
      are ALSO written via an actual GCS listing, not just the code comment — the 2026-07-23 RE-TRIAGE already cites
      strong code-comment evidence, so this is largely confirmation). (2) THEN align
      `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` in
      `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py:139` to the confirmed layout,
      with a regression test that `candidate_parquet_paths(WEATHER, league=…)` builds the `league=` path (mirror the
      existing PLAYER_VALUES alignment). (3) THEN re-run the sports phantom audit and confirm WEATHER false positives
      (baseline ≥106 proven false-positive rows) drop out of the `instruments-store-sports` phantom count; check for and
      remove any zero-row WEATHER placeholder residue. (repo: instruments-service; unified-api-contracts
      `gcs_paths.py`). **Done when**: layout confirmed via code + GCS listing; `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` set
      to `PER_DAY_PER_LEAGUE` with a passing regression test; phantom audit re-run shows WEATHER no longer contributing
      false positives; any placeholder residue removed or its absence confirmed. Source:
      `issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`. — SHIPPED 2026-07-25
      (slot 4): unified-api-contracts@b73c95d5. Confirmed via code + live GCS listing (league= objects only, zero bare);
      set `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` to `PER_DAY_PER_LEAGUE` + regression test; sports phantom audit re-run:
      12,851 real captures, 0 phantom (exceeds ≥106 baseline). No placeholder residue found. QG green. Full evidence in
      the issue doc.

### From `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`

- [x] [DATA] P1. ✅ **`player_stats` idempotent de-dup rewrite** — `instruments-service@210d4567`. Reference tooling
      (`~/tmp-cutover/t2_4_build_canon_keys.py`) was session-local and gone, so wrote a fresh script
      (`scripts/dedup_canonical_player_stats_2026_07_25.py`) covering ALL 26,687 manifest-tracked
      `PLAYER_STATS`/`captured` cells uniformly (safe no-op on already-clean objects). Object paths via UAC's
      `candidate_parquet_paths(..., pipeline_mode=...)` SSOT; generation-matched CAS writes. **Result: 7,066 objects
      deduped, 808,279 duplicate rows removed; re-run confirmed 0 duplicates remain project-wide** (this todo's own
      done-when). Two incidental findings, left untouched not absorbed: schema heterogeneity also affects ~12% of
      player_stats cells; ~4.9% of captured cells have no GCS object (2019 era). Detail:
      `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (Finding 1, resolved).
- [x] ✅ [DATA] P1. **RESOLVED 2026-08-03**: `fixture_events` re-fetch into the canonical 13-col schema — pass-3
      complete, zero failures; final census `canonical_13col=38,376 degenerate_5col_stub=1,973 af_prefixed_10col=29`.
      The 1,973 figure is NOT a gap (corrected via live-API spot-check: legacy blank-league_id duplicate objects whose
      data already exists in the real per-league canonical objects) — full evidence in
      `issues/sports_fixture_events_refetch_progress_2026_07_25.md`. **🟡 IN PROGRESS (2026-07-25, slot 2)**: full
      census done (12,603/43,233 genuinely non-canonical, recovery-ids parquet built), re-fetch launch blocked on the
      af-backfill singleton lock (INJURIES VM still running) — full state + resume command:
      `issues/sports_fixture_events_refetch_progress_2026_07_25.md`. — **Stale sub-status corrected 2026-07-25T05:38Z
      (slot 11): the INJURIES-VM lock cleared hours ago; the re-fetch VM (`af-backfill-20260725-032253`) has been
      RUNNING since 03:22Z** (launched by slot 4, health-checked healthy by slot 11 at 04:18Z and again now — heartbeat
      fresh, no stall, now in the slower per-fixture event-loop phase covering 16,765 fixtures across 2019→2026-07-25).
      Genuinely hours from terminal; not completable in an AO turn. Full detail in the issue doc above — do not
      re-dispatch a duplicate health-check within the next ~30min. — **Health-checked 2026-07-25T06:43Z (slot 2)**:
      still `RUNNING`, heartbeat 34s old, run.log grew 69,781→79,917 lines (+10,136) since the issue doc's 06:08Z check
      (same doc, more detail there — this parent plan's todo and the issue doc both point at the same VM; resist the
      urge to duplicate full detail in both). Released via `/skip-current-task`, not duplicate-launched. — **🔴
      2026-07-25T08:34Z (slot 7, data_engineering) — CRITICAL: live data-correctness bug found + fixed, VM stop
      escalated.** Health-check found the VM zero-progress since 08:12Z (API-Football DAILY quota exhausted, 8,534
      failed fetches logged, date boundary stuck at `2020-03-22`) and root-caused a real code bug: the 4 per-fixture
      `api_football.py` adapters (`get_fixture_statistics`/`get_fixture_events`/`get_fixture_lineups`/
      `get_fixture_player_stats`) swallowed hard fetch failures internally and returned `[]`, so
      `_gather_per_fixture_rows`'s `entity_failures` tracking never fired and affected leagues/dates were silently
      stamped `empty_confirmed`/`EXPECTED_NO_FIXTURE` instead of `attempted_failed` — the exact honest-absence violation
      this campaign exists to fix. Full evidence:
      `issues/api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md`
      (`unified-trading-pm@ac4ace8b9`, PR #1492 — corrected 2026-08-04, slot-8: prior citation `9022488a2` did not
      resolve to any commit; `gh pr view 1492` confirms the real merge SHA). Filed `/blocked` (`BLK-78a76a51`); main
      ruled **A — stop the VM now** (SPOT+idempotent, safe to relaunch; leaving it running keeps writing false
      `empty_confirmed`, which is WORSE than `attempted_failed` since downstream won't retry it). **Fix shipped**:
      `instruments-service@f31fb2e9` — the 4 adapters now re-raise after `_emit_fetch_failed` instead of swallowing; 4
      unit tests updated (`*_error_returns_empty` → `*_error_propagates`, mirrors the existing
      `get_injuries_error_propagates` precedent); full `quality-gates.sh` green (109s); orchestrator-level
      `TestCF11PerFixtureEntityFailurePath` suite (already correct) confirms `_fetch_one`/`_handle_empty_fixture_entity`
      now actually receive the failure signal. **Not an operator gate (re-tagged 2026-07-28) — a transient local
      credential gap only**: this is the SAME ambient `unified-trading-sa`/`uts-orchestrator-epic-role` identity every
      AO worker runs as, not a genuine cross-identity authorization gap (`task_template.md` finding O/finding ii doesn't
      apply here). Could not execute the VM stop from THIS slot — `gcloud` auth expired mid-session
      (`Unable to retrieve Identity Pool subject token: job is already     completed`, both available accounts,
      non-interactive reauth impossible this session) — dispatch to any worker/slot with a currently-valid `gcloud`
      session to run `gcloud compute instances stop af-backfill-20260725-032253     --zone asia-northeast1-c` directly;
      no operator authorization is structurally required to stop an already-flagged SPOT/idempotent VM. **Do NOT flip
      this checkbox done yet**: (1) VM stop still pending execution, (2) once stopped, relaunch only after the
      API-Football daily quota resets, (3) the window `08:12Z`→stop-time was written under the OLD buggy code — those
      dates' `empty_confirmed` rows must be relabeled/re-fetched (issue doc todo 4), not trusted at face value by the
      eventual re-census. Released via `/skip-current-task {"reason_code":     "GATED"}` — genuinely gated on the
      VM-stop + quota-reset, not undoable from this slot. — **Health-checked 2026-07-28T17:45Z (slot 9,
      data_engineering)**: the re-fetch VM has been relaunched (post fix `f31fb2e9`, quota reset, tarball refresh) as
      `af-backfill-20260728-141821`, launched 2026-07-28T13:22:16Z, `RUNNING` in `asia-northeast1-c` (confirmed via
      `gcloud compute instances list`, `unified-trading-sa` account — `github-deploy` lacks `compute.instances.list`,
      known WIF-poisoning issue, use `unified-trading-sa` or `ikenna@odum-research.com` instead). 2-read progress-metric
      check over ~6min: `run.log` grew 53,041→54,766 lines, distinct `date=` markers 934→956
      (`date=2021-09-15`→`date=2021-09-26`), live per-fixture `Fetched N events for fixture=X` lines interspersed with
      the expected per-minute `rateLimit`/429 sleep-retry cycling (matches the pre-incident healthy pattern, not the
      2026-07-25T08:12Z quota-exhaustion stall signature) — genuine forward progress, no
      `DEPLOYMENT_COMPLETED`/`exit_code` terminal marker (`grep -c` = 0). Not completable this turn (2019-01-01 start,
      ~2021-09 current, range runs to 2026-07-25). Released via `/skip-current-task {"reason_code": "GATED"}`, not
      duplicate-launched. Next dispatch: repeat this health-check (2-read progress-metric — a new `date=` boundary OR
      continued in-date fixture-fetch advance both count as live); once terminal, re-run
      `scripts/census_fixture_events_schema_variants_2026_07_25.py` (full, no `--limit`) per the issue doc's "Next
      action" before flipping this checkbox — also re-verify the `08:12Z`-`stop-time` suspect window from the prior VM
      run was excluded/re-fetched (issue doc item 3), not trusted at face value. — **Health-checked 2026-07-28T23:05Z
      (slot 14, data_engineering)**: re-verified from scratch (`unified-trading-sa` account — `github-deploy` again
      confirmed to lack `compute.instances.list`). VM `af-backfill-20260728-141821` status=RUNNING in
      `asia-northeast1-c`; heartbeat blob fresh (`vm-heartbeat/af-backfill-20260728-141821.txt` ~55s-90s old across both
      reads). 2-read progress-metric check over ~4.5min: `run.log` grew 128,447→129,526 lines (+1,079), `date=` marker
      advanced `2023-04-30`→`2023-05-06` (+6 days) — genuine forward progress, notably faster pace than slot 9's 17:45Z
      check (`2021-09-26`, ~1.5yr of dates covered in the intervening ~5h20m, consistent with the documented
      "enrichment-only / already-captured dates need no API round-trip" fast-pace pattern seen elsewhere in this
      campaign, not an anomaly). No error/traceback lines beyond the expected benign `CANONICAL_LEAGUE_ID_LOOKUP_MISS`
      warnings (non-lossy raw-id passthrough, already documented as expected). No `DEPLOYMENT_COMPLETED`/`exit_code`
      terminal marker (`grep -c` = 0). Not completable this turn (range runs 2019-01-01→2026-07-25, currently ~2023-05).
      Released via `/skip-current-task {"reason_code": "GATED"}`, not duplicate-launched. Next dispatch: repeat this
      health-check; once terminal, re-run `scripts/census_fixture_events_schema_variants_2026_07_25.py` (full, no
      `--limit`) per the issue doc's "Next action" before flipping this checkbox — also re-verify the `08:12Z`-stop-time
      suspect window from the prior (2026-07-25) VM run was excluded/re-fetched (issue doc item 3), not trusted at face
      value. — **Health-checked 2026-07-29T08:59Z-09:01Z (slot 14, data_engineering)**: still RUNNING, `date=` boundary
      at `2026-05-15` — only ~2 months of the `2020-06-06→2026-07-25` range remain (down from ~1.5yr at the prior 05:00Z
      check). Full detail + both reads in `issues/sports_fixture_events_refetch_progress_2026_07_25.md`. Not completable
      this turn; genuinely close now. Released via `/skip-current-task {"reason_code": "GATED"}`. — **Health-checked
      2026-07-29T14:14Z-14:17Z (slot 6, data_engineering)**: still RUNNING, but a NEW finding — API- Football's DAILY
      quota is exhausted (not the usual per-minute 429 sleep-retry), `date=` boundary stuck at `2026-07-12` since
      `13:45Z` with zero successful fetches since `13:14Z` (~1h+ of zero real progress, though the process itself is
      alive/not crashed and every failure correctly surfaces as `ERROR ... recovery=fail_fast`, NOT the 2026-07-25
      silent-swallow bug repeating). Did not stop the VM (SPOT billing is time-based either way; stop buys nothing until
      the vendor quota clears). Only ~13 days of the range remain. Full detail in
      `issues/sports_fixture_events_refetch_progress_2026_07_25.md`. Not completable this turn. Released via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: confirm quota reset + resumed progress, or
      `/blocked` if still stuck at `2026-07-12` many hours from now. — **Health-checked 2026-07-29T20:14Z (slot 4,
      data_engineering)**: the VM (`af-backfill-20260728-141821`) was stop+deleted by the interactive operator session
      at 15:00Z-15:10Z (already documented, independently corroborated via `gcloud compute operations list`); a VM-free
      `/status` quota probe still reads exhausted. Sharpened the reset estimate to `2026-07-30T00:00Z` (the launcher's
      own documented daily-quota reset time) rather than another blind hourly probe. Full detail in
      `issues/sports_fixture_events_refetch_progress_2026_07_25.md`. Not completable this turn. Released via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: not before `2026-07-30T00:00Z`; then re-probe once
      and relaunch (without `--force`) on a clean response. — **Health-checked 2026-07-30T22:20Z (slot 3,
      data_engineering) — re-fetch VM reached terminal completion, ran the mandated VERIFY, done-when NOT met**:
      non-canonical objects dropped 12,603→4,327 (real progress) but not zero; fresh recovery-ids parquet staged to GCS,
      next-recovery-launch blocked only on the af-backfill singleton lock (held by an unrelated task). Full numbers +
      exact resume command in `issues/sports_fixture_events_refetch_progress_2026_07_25.md`. Not flipping this checkbox.
      Released via `/skip-current-task {"reason_code": "GATED"}`.
- [x] ✅ [CODE] P2. **Writer-side de-dup + schema-conformance gate** so neither defect re-accrues — the `player_stats`
      writer rejects/dedupes rows on write; the `fixture_events` writer validates/enforces the canonical 13-col schema
      before accepting new objects. — `instruments-service@f5fa9f8a`. Added a `player_stats` de-dup gate (drop
      within-object exact duplicates on `(fixture_id, player_id)`, mirroring
      `dedup_canonical_player_stats_2026_07_25.py`'s own methodology) in `_prepare_fixture_entity_df`, and a
      `fixture_events` schema-conformance gate (reindex to the canonical UAC 13-col `SPORTS_FIXTURE_EVENTS` contract —
      missing columns null, non-canonical columns dropped) in `_write_fixture_entity_per_league`, applied AFTER the
      league-mapping join so it never strips the join key. Both gates live in a new sibling cohesion module
      (`sports_reference_fixture_entity_gates.py`) to keep `sports_reference_fixtures.py` under the 900-line file-size
      ratchet. 11 new regression tests (`test_sports_reference_fixture_entity_writer_gates.py`) cover: dedup drops
      duplicates / no-ops when already clean / no-ops when key columns absent (nested schema variant); schema gate
      passthrough-when-canonical / fills missing + drops non-canonical columns on the degenerate 5-col stub; end-to-end
      wiring through `_write_per_fixture_entities` proving the gate applies to the object actually handed to
      `_gated_sink_write`. Full existing suite (124 tests across the 4 related test files) + full `quality-gates.sh`
      green. Source: `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.

### From `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`

- [x] ✅ **ABANDONED 2026-07-25 (operator ruling, deliberate) — source bucket deleted before STEP 1 ran, data
      unrecoverable; see `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`.** [DATA] P1. **32-day
      legacy→canonical MDT row recovery (5-step ordered sequence, one worker, execute in order — this is one recovery
      procedure, not 5 independent jobs).** (1) READ-ONLY: re-derive the ~32 gap days by whole-day KEY-LEVEL containment
      (legacy tick keys − canonical tick keys) over the candidate window (2022-09-07..2022-10-01 dominant + a handful of
      2023/2025 days) — do NOT inherit the banner's day-list, confirm it; expect ~32 days / 550,062 legacy-only keys
      (524,486 pre-match + 25,576 in-play) / ~2,081 objects. (2) BUILD: per confirmed gap day, read legacy old-shape
      objects → extract canonical-absent keys → derive canonical segments via `build_instrument_id` (the
      already-validated 100.0000% derivation map — do NOT re-derive) → split pre-match vs in-play by kickoff time →
      MERGE (never overwrite — canonical holds `bookmaker_key`/`fixture_id`/`available_at` legacy lacks) → de-dup on the
      poll key `(event,market,outcome,bm_time,price)` → stamp `available_at` via
      `unified_trading_library.availability_stamping.stamp_available_at_odds_snapshot(df, source="odds_api")`. (2b)
      IN-PLAY QUARANTINE (per the already-ruled OR-5b(c) mechanism — execution, not a design choice): in-play rows land
      under a non-`ticks.parquet` filename with a distinct `data_type=` segment, `pipeline_mode` unchanged
      (`batch_odds_api`), so `reprocess_sports_odds.py::_is_consumable_trades_blob` /
      `orchestration_scanner._matches_data_type` do not sweep them into the pre-match/T-0 path. (3) VERIFY BY CONTENT:
      fresh re-read in a SEPARATE process (never the writer's own return) confirms recovered keys present in canonical
      with matching crc/row counts; a before/after `(data_type,source)` census shows only the intended cells changed.
      (4) T2.10 SEED PURGE: strip 37,114 phantom `api_football × trades` (captured, nonzero IC) from
      `_index/per_vm/_legacy_seed.parquet` with the NULL-safe COALESCE source filter (211,313 real
      `odds_api ×     trades` rows survive) — back up first, let the consolidator re-merge, verify by content. (5) T4.1
      OBJECT-LAYER PROOF: confirm `unique==0` for the legacy bucket (`market-data-tick-sports-central-element-323112`),
      the delete-eligibility precondition. Snapshot/backup before every write step; abort and escalate if any gate fails
      to match expectations rather than proceeding past a mismatch. (repo: market-tick-data-service — new one-off
      migration/audit script under `scripts/`, with lifecycle markers; reads/writes GCS buckets
      `market-data-tick-sports-central-element-323112` (legacy) and `market-data-tick-sports-prd-central-element-323112`
      (canonical); consumes but does not modify `unified_trading_library.availability_stamping`). **Done when**: N/A —
      **BLOCKED 2026-07-25**, source bucket deleted 2026-07-17 pre-STEP1, confirmed deliberate operator decision to
      abandon recovery (ruling 2026-07-25), data unrecoverable. Source:
      `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`,
      `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`.
- [x] ✅ [DOC] P3. **File a new issue doc** for the standalone finding: "30/200 sampled canonical MDT objects carry
      duplicate rows on the poll key (event, market, outcome, bm_time, price, fetch_utc), independent of the OR-5b
      cutover." — `issues/mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md`. Note: the recovery-sequence todo
      above's step 2 dedup was scoped only to the abandoned 32-day recovery's own merged rows, never the wider
      already-existing canonical population this finding covers, and that recovery is now itself ABANDONED (source
      legacy bucket deleted before STEP 1 ran) — so the new doc adds 2 fresh `[DATA]` fix todos (root-cause + measure,
      then de-dup if warranted) rather than treating remediation as already covered elsewhere. Source:
      `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`.

### From `issues/sports_league_id_namespace_migration_2026_07_20.md`

- [x] ✅ [DATA] P0. **Fix the independent per-fixture league_id defect** — unified-api-contracts@d28da985 +
      instruments-service@83b7952b. Root cause: `CanonicalLeague` never carried an `api_football_id` attribute, so the
      2026-07-20 numeric-id-first precedence flip silently no-opped — every fixture kept resolving via the raw ambiguous
      display name. Fixed at the root: added `api_football_id` to `CanonicalLeague`, populated from the raw API
      response. 3 regression tests (numeric resolves correctly; 6 known ambiguous names disambiguate via numeric id;
      unregistered league falls back honestly). Confirmed the write-universe gate (shipped 2026-06-24) already prevents
      any unresolved value from reaching disk going forward. Source:
      `issues/sports_league_id_namespace_migration_2026_07_20.md`.
- [x] ✅ **League_id casing migration — steps 1-4 executed + verified; residual purge is human-only, not blocking.**
      market-tick-data-service@{75f226e8,fb51d86c} + unified-trading-pm@{2705cb4fd,b5bf80d53}. **Casing corrected**
      (decided: lower-case, not the upper-case the executor originally shipped) and re-shipped clean. Along the way:
      fixed a `gsutil`-credential blocker for tarball republish (`deployment-service@3ba14ff`, routes via ADC); found +
      fixed a TOCTOU manifest-swap revert (`unified-trading-library@14301571`), re-applied and verified stable across 5
      consolidator cycles; confirmed the coverage-registry refresh has no drift
      (`is_bookmaker_league_covered("BETFAIR_EX_EU","EPL")` = True as required). **Step 3 (MDPS `odds_horizon_bucket`
      reprocess) EXECUTED + VERIFIED**: 4 sharded SPOT VMs, all completed cleanly — 166,751 shards / ~5.4M bucketed rows
      written; manifest-verified stable across 2 consolidator cycles (408,815 rows / 130 distinct league_ids, no TOCTOU
      revert). Shard4's 22 `attempted_failed` + 4 `LOSS_GUARD_BLOCKED` are honest upstream gaps, not defects (tracked,
      non-blocking: `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`). **Step 4
      (`batch_footystats` copy+swap) — CORRECTED: not a casing task.** The 16,969-object population was mis-stamped
      `batch_odds_api` data, already merged to canonical on 2026-07-17 (`market-tick-data-service@75f226e8`) — no
      copy+swap work remains. What's left is a human-gated orphan-object PURGE (5-part delete-safety proof, staged not
      executed): `/plans/archive/issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md`.
      Full step detail + dry-run baselines: `issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`,
      `issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`. Source:
      `issues/sports_league_id_namespace_migration_2026_07_20.md`.

- **`sports_odds_feature_naming_canonicalization_2026_07_21.md`'s FSS↔ml-service↔strategy-service parity test** — gated
  on all 5 naming-migration todos above landing. Add as a new todo once confirmed shipped.
- **`sports_fixtures_browser_single_catalogue_source_2026_07_24.md`'s `FixturesBrowser.tsx` relabel** — gated on this
  plan's fixtures_browser.py backend todo landing. Add as a new todo once confirmed shipped.
- **`issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`'s real-backfill timing verification** — gated on
  both `sports_dependency.py` todos above landing. Add as a new todo once confirmed shipped.
- **`sports_group_c_execution_backtest_harness_2026_07_21.md`'s 3 todos** (run_sports_backtest, fixture data wiring,
  hermetic alpha-bps test) — ALL gated on a human/architect decision (SportsMatchingEngine vs L0Matcher) that has not
  yet been made. Not dispatchable until that decision lands; do not dispatch speculatively.

## Progress Log

- **2026-07-25 — "Curated-universe definition → backfill → residual drop"**: step 1's domestic-selection slice (145
  countries) decomposed into 11 confederation-batch todos, all now landed. Full investigation detail (not duplicated
  here to protect this plan's line cap): `issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md`.
- **2026-07-25 — "Eliminate the bare/legacy dual-layout"**: verified via a real census (not assumption) across all 15
  `PER_DAY_PER_LEAGUE` entities (2,322 dates + a 13-date/7-entity spot-check + `day=all`) — zero dual-layout instances
  found; see the todo above for the result. Confirmed out of scope for the one `day=all/entity=teams` hit (that's the
  separate "Retention floor" todo's concern).
- **2026-07-25 (slot 7) — League_id casing migration, MDPS `odds_horizon_bucket` reprocess**: launched as a 4-way
  sharded split (`mdps-sports-bucket-20260725-{035949,040027,040053,040119}`, SPOT), all completed cleanly — see the
  casing-migration todo above for final numbers and manifest-stability verification.
- **2026-07-27→28 — FIXTURES backfill OOM, take 2: the chunking fix was insufficient, real fix + relaunch shipped**:
  `af-backfill-20260727-064958` self-reported `exit_code=0` complete, but 14/25 chunks (2023-05-13→2026-07-25) were
  silently OOM-killed mid-range and skipped by the loop's `|| true` — ~832 days of FIXTURES never actually processed.
  Root cause: `VM_NAME` (and the per-VM manifest shard it names) is constant for the VM's whole lifetime, so the
  2026-07-27 chunking fix reset each chunk's process memory but not the shared, ever-growing shard. Real fix shipped
  `deployment-service@20ce4c9`: per-chunk `VM_NAME` suffix (bounds each chunk's shard to its own rows — verified live,
  `af-backfill-20260728-091755`'s chunk 3 shard is `per_vm/{vm}-c3.parquet`, 359 entries, not 280K+) + bounded 4-attempt
  chunk retry. Full root-cause history + the deferred library-fix re-evaluation (would not have helped — doesn't cut
  peak memory): `/plans/archive/issues/per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md`. Relaunched
  `af-backfill-20260728-091755` for the full range (skip-if-fresh fast-forwards chunks 1-12, real work starts at the
  gap, chunk 13+) — monitoring to completion.
- **2026-07-28 — FIXTURES backfill VERIFIED COMPLETE**: `af-backfill-20260728-091755` finished all 25/25 chunks cleanly
  on the first attempt, reaching the target end date `2026-07-25` (`exit_code=0`, clean self-shutdown). Verified via a
  full-log audit (115,631 lines), not just the exit code: zero `Killed`, zero `CHUNK_EXHAUSTED`, zero `CHUNK_RETRY`,
  zero `Traceback` anywhere; exactly 25 `--- Chunk N/25 ---` boundaries and 25 matching `PROGRESS: chunk=N/25`
  completions, no duplicates (no chunk needed a retry). Chunk 14 (2023-08-20→2023-11-17, one of the 14 chunks that died
  in the take-2-insufficient run) completed its full 90-day range this time, confirming the per-chunk `VM_NAME`-suffixed
  shard fix (`deployment-service@20ce4c9`) genuinely resolved the root cause — every chunk's per-VM shard reset to a few
  hundred/thousand rows instead of accumulating the whole backfill's 280K+ rows. `last_completed_date` checkpoint stops
  at `2026-07-11` (not `2026-07-25`) because the final ~2 weeks were already fresh via `SKIP` (kept current by the
  separate rolling/live forward-poll path) — confirmed by the log itself: the very last date processed, `2026-07-25`,
  shows `SKIP date=2026-07-25: all 1 venues/entities already fresh in manifest`, i.e. genuinely captured, not missing.
  One unrelated, non-fatal issue surfaced at shutdown: a `RUN_LEDGER_RECORDED` Pub/Sub publish failed with
  `IAM_PERMISSION_DENIED` (`pubsub.topics.publish` on `projects/central-element-323112/topics/run-ledger`) — a
  downstream completion-bookkeeping record, not a data-write path; does not affect this backfill's correctness, flagged
  as a small separate follow-up if it recurs elsewhere. Full root-cause history (MVP-league-scope leak → OOM take-1
  insufficient chunking → OOM take-2 real per-chunk-shard fix, now verified complete):
  `/plans/archive/issues/per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md`.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: trimmed context_scope to 5 (was 7, over the 2-6 guidance) — no source path added, this
  is a dispatch-batch coordinator whose real content lives in its 15 named source docs (each has its own).

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated on it via
`sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`
(`depends_on: [sports_satellite_ao_dispatch_batch2_2026_07_24]` + `gate_on_depends: true`) — mirroring
`sports_closeout_batch1_finalize_2026_07_24.md`'s pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc. See
each source doc's own "Codex SSOTs" section (where present) for the relevant references.
