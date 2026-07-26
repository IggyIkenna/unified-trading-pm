---
doc_type: plan
title: CeFi satellite AO batch 2 — fresh Phase-1/Phase-3 triage of the cefi closeout-orphan corpus
summary: >-
  Second AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) +
  Phase-3 (conflict-check + draft) triage over all 43 cefi AG-primary docs not already covered by the consolidated
  closeout, aggregated-sources index, batch1 (+finalize), the 4 line-cap-split forked tracks (migration-cutover,
  track2-coverage-backfill, track7-candle-namespace, misc-audits-and-hygiene, each +finalize), the native-ao-extract
  doc(+finalize), the 4surface migration execution-log, and the bybit-spot-manifest-remediation plan(+finalize)
  (2026-07-26). 29 docs came back orphaned (17 partial coverage, 12 never touched); 3 turned out to be cefi-tagged
  mistags whose real content is cross-cutting/generic (excluded, flagged below for a follow-up retag); 1 was fully
  closed already (`cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`, archive candidate, not actioned by this
  batch). Phase 3's conflict check cleared 17 of the 29 into fresh AO-dispatch todos (zero cross-todo file collisions,
  zero duplicate-ground conflicts found); left 10 operator-gated, 1 time-gated, and 1 human-only item in the Deferred
  sections below for the next iteration or an explicit operator ruling, per the skill's non-batchable taxonomy.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    deployment-api,
    deployment-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-2, satellite-docs, fresh-triage]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (interactive, operator-approved scope) — Phase 1 classified all 43 cefi
  AG-primary docs not already in the covering-plan set via a Workflow fan-out (43 agents), Phase 3 ran a conflict-check
  + candidate-todo draft over the 29 orphaned docs via a second Workflow fan-out (29 agents), per the skill's documented
  methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# CeFi satellite AO batch 2 — fresh triage extraction

> **Status: active — operator-approved 2026-07-26.** Dispatched per CLAUDE.md's plan-destination rule and the
> ag-closeout-audit skill's autonomous-mode guidance (a skill-drafted AO batch is never auto-shipped; this flip followed
> explicit operator review). All 17 todos below are same-priority-independent and touch distinct files/docs (verified —
> zero cross-todo file overlap found beyond the shared `quality-gates.sh` command, which is not a collision).

## Todos

- [ ] [BACKEND] P2. **Execute the COINBASE bare-name execution-service caller migration** (S1-S3 of
      `coinbase_bare_name_migration_execution_service_2026_07_10.md`, whose prerequisite parent plan
      `coinbase_bare_name_migration_2026_07_06.md` is already `status: complete`): (1) grep execution-service's
      external-facing surfaces (API route handlers, order-routing request schemas) for any caller still passing bare
      `"COINBASE"`; if none found, delete the `execution_service/instruments/registry.py:178-179` UAC-facing
      backward-compat branch (leave the Nautilus-boundary map at `utils.py:239` / `nautilus_compatibility.py:17` /
      `trade_execution/factory.py:104` / `engine/backtest/preflight.py:90` untouched — these are a permanent
      Nautilus-venue convention, not UAC drift); if an external caller is still found, KEEP the resolver and document
      why in a code comment citing this plan; (2) re-key bare `"COINBASE"` → `"COINBASE-SPOT"` in
      `execution_service/services/execution_cost_estimator.py:32`, `execution_service/algo_library/algorithms/sor.py`
      (cost-snapshot dict only, lines 27/29/34/153/169), `execution_service/trade_execution/venue_mapping.py`, and
      `configs/expected_start_dates.yaml`; (3) grep `execution_service/engine/handlers/trade_handler.py` and
      `execution_service/results/serializer.py` for bare `COINBASE` usage — re-key if it's a lookup, leave if it's a
      label/comment. Source: `coinbase_bare_name_migration_execution_service_2026_07_10.md`. Done when:
      `grep -rn '"COINBASE"' execution-service/execution_service/ --include='*.py'` (excluding the deliberately-kept
      Nautilus-boundary files listed above) returns 0 hits, the registry.py decision is documented with grep evidence in
      that plan's Progress Log, and execution-service `bash scripts/quality-gates.sh` is green on the final commit.
- [x] ✅ [DATA] P1. **DONE 2026-07-26 (slot-7, `data_engineering`) — CeFi E6 CF-7 diagnostic.** Live read of
      `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (9,138,791 rows, single read,
      no corpus walk, no `--apply`). **(a) relabel candidates**: `COINBASE` bare-venue = **0 rows** (already fully
      canonical: COINBASE-SPOT/FUTURES/CDE all in use) — no relabel needed. Blank-venue = 6 rows (negligible).
      Blank-`data_type` = **9,750 rows**, all `capture_status=captured`, all `market-tick-data-service`, spanning
      2019-2026 — genuinely new, not previously tracked, filed as a P3 follow-up. **(b) 1.33M/50% figure RETIRED AS
      STALE** — current measurement is **11.61% (1,060,613 rows)** of 9,138,791 total (denominator grew ~3.5x from the
      ~2.64M cited elsewhere while the numerator dropped modestly). Root-cause: 75.2% is the Tardis-403 family, DERIBIT
      alone = 54.7% of all cefi attempted_failed — confirmed via exact-match cross-reference against
      `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s 2026-07-23 numbers (113,593/112,600 DERIBIT
      options_chain/futures_chain, essentially unchanged) that this is the SAME already-open P0 population
      (`tardis_concurrent_ip_lockout_2026_07_12.md`, `deribit_options_chain_af_g4_blocker_2026_07_03.md`) — no new
      mechanism, confirmed no overlap with the ASTER regression / futures_chain-122,585-debunked /
      Tardis-impossible-combo items per the todo's own instruction. Full write-up + the P3 follow-ups:
      `plans/active/issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`.
- [ ] [SCRIPT] P1. **cefi instruments-pipeline hygiene sweep — 6 bounded fixes from the closed-out G1→G5 gate-execution
      doc.** Execute each sub-item (independent files, run sequentially in one todo to avoid a same-doc worker
      collision): (a) **Disable/update the dead-CLI legacy daily Workflow** — `services/instruments-service/gcp/main.tf`
      `instruments-service-daily` (09:00 UTC) still invokes the retired `--operation instrument --CEFI/--TRADFI/--DEFI`
      CLI form (current CLI is `--operation instruments --asset-group <ag>`); either update its args to the current CLI
      or disable/remove the dead schedule. Repo: instruments-service / deployment-service. (b) **Fix the all-AG (no
      `--asset-group`) t1-recon producer crash** — the `is_all` branch in `instruments_handler.py` (~line 367,
      SPORTS/CEFI/DEFI/TRADFI) exits 1 within ~1 min with no traceback when `--asset-group` is omitted; root-cause and
      fix so one 00:00 job can capture all AGs. Repo: instruments-service. (c) **Codify the t1-recon Cloud Run JOB specs
      in IaC** — only the schedulers are terraformed (`t1_batch_scheduler.tf`); the JOB definitions (image/args) are
      imperative, which is how the cefi date-drift and the missing all-AG job went invisible previously. Add the job
      specs to terraform (or a tracked deploy script referenced from terraform) so they can't silently rot. Repo:
      deployment-service. (d) **Reconcile `lifecycle-catalogue-regen-prediction` registry gap** — it is present in the
      terraform `for_each` (5 AGs) but absent from `cloud_run_job_registry.py::_LIFECYCLE_CATALOGUE_JOBS` (4 AGs); add
      the missing entry (or remove the TF instance if prediction genuinely has no catalogue-regen job) so the
      drift-guard test stops flagging it. Repo: deployment-service. (e) **Align the on-chain-cefi-perp venue form
      (LIGHTER-ZKSYNC/EXTENDED-STARKNET)** — currently GLUED in the by_date PATH (the SoT) but SPLIT
      (`venue=LIGHTER chain=ZKSYNC`) in `_index` + `prod/catalog.parquet`, which will desync as new captures land glued.
      Per the doc's own recommendation, standardize on GLUED (matching `_CEFI_VENUES` + the by_date path): stop
      `build_instrument_catalogue.py::build_catalogue_dataframe` from splitting these two venues, and one-time re-glue
      the existing `_index` rows (snapshot-first). Repo: instruments-service. NOTE: PACIFICA-SOLANA was culled
      2026-07-16 — do not include it. (f) **Build MTDS-cefi market-data capability for LIGHTER** — only EXTENDED has a
      UAC cefi `SourceCapability` (`_cefi.py`); LIGHTER has none, so its cefi market-data capture is unbuilt (IS
      instrument-reference side is already cefi-correct). Add the LIGHTER `SourceCapability` + adapter wiring so
      LIGHTER-ZKSYNC market data can be captured under cefi. Repo: market-tick-data-service. NOTE: PACIFICA is culled,
      do not build for it. Source: instruments_cefi_g1_g5_gate_execution_2026_07_24.md (items: dead-CLI legacy Workflow
      / all-AG producer crash / t1-recon IaC gap / lifecycle-catalogue-regen-prediction registry gap /
      on-chain-cefi-perp venue-form FINDING / MTDS-cefi capability gap — none cited or dispatched in any other cefi
      covering-set doc). Done when: (a) the daily Workflow either runs the current CLI or is disabled — no more silent
      daily failure; (b) the all-AG t1-recon path runs successfully end-to-end for at least one day across all 5 AGs;
      (c) the t1-recon job specs are terraform-managed (or scripted+tracked) with a verifying re-apply; (d) the registry
      drift-guard test passes with prediction reconciled; (e) `_index` + catalogue both show GLUED form for
      LIGHTER/EXTENDED with 0 residual SPLIT rows, and a fresh capture writes glued; (f) LIGHTER cefi market-data
      capture runs and writes at least one verified shard. QG-green on every touched repo.
- [ ] [SCRIPT] P2. **Resolve the ASTER MTDS `attempted_failed` regression per the batch1 DIAG evidence, then close the
      issue doc.** Depends on (gate on) `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s `[DIAG] P1` todo having
      appended its three sub-check findings to `issues/aster_mtds_failure_count_regression_2026_07_07.md`'s Progress Log
      first. Read that evidence: (a) if sub-check (b)/(c) show the `attempted_failed` rows are the SAME rows carried
      over from the 2026-05-13 incident (stale manifest-source/index read, not new failures) — re-run the documented
      recovery mechanism: re-launch the `mtds-perp-funding-backfill` VM
      (`deployment-service/scripts/vm/launch-mtds-perp-funding-backfill-vm.sh`) against ASTER over its captured range so
      live re-fetch overwrites the stale `attempted_failed` rows in place (per
      `emerging_perp_venue_adapters_broken_2026_05_13.md`'s resolution note — no separate reconciliation needed once
      re-fetched); (b) if the rows carry recent timestamps (genuinely new failures), file a fresh dated issue doc
      diagnosing the new adapter break (do NOT reuse this doc — it's scoped to the regression-vs-recovery question, not
      a new failure mode) and reference it here. Either branch: re-run the live turbo query
      (`GET /api/data-status/turbo?...&asset_group=CEFI&include_sub_dimensions=true`) post-fix and record the new
      `ASTER.failure_pillars.failed_other` count in this doc's Progress Log. **Done when**: either (i) the count is back
      down near the 2026-06-22 baseline (~3,491, not 17,675) with the before/after recorded, and `status:` flipped to
      `resolved`, or (ii) a new dated issue doc exists for the genuinely-new-failure branch and this doc's Progress Log
      links to it with `status:` flipped to `resolved` (superseded by the new doc) — either way this doc no longer sits
      open with unresolved P1/P2 todos. Source: `issues/aster_mtds_failure_count_regression_2026_07_07.md`.
- [ ] [BACKEND] P1. Fix `_normalize_instrument_id_for_match`
      (`deployment_api/services/data_status/instrument_coverage.py:37-64`) so OPTION/dated-FUTURE `instrument_id`s stop
      colliding into a handful of dict keys. Use direction (b) from the doc — make the `@`-suffix strip
      instrument_type-aware: keep stripping for instrument_types confirmed suffix-divergent-only
      (PERPETUAL/SPOT_PAIR/COMBO — measured 1.00x collision-safe in the doc's table), pass through the full raw id
      (whitespace-collapsed/uppercased only, no `@`-split) for OPTION and dated-FUTURE instrument_types, since their
      `@`-suffix encodes real distinguishing identity (expiry/strike/side), not a settlement tag — direction (b) is
      preferred over (a)'s enumerated-tag-suffix approach because it doesn't require maintaining a hardcoded tag
      allowlist that new settlement/chain tags could silently fall outside of. Add unit test coverage in the same change
      for `per_instrument_coverage`/`_normalize_instrument_id_for_match` using at least one real OPTION id
      (`DERIBIT:OPTION:BTC-USD@INV-20190405-3250-C` shape) and one real dated-FUTURE id
      (`DERIBIT:FUTURE:AVAX-USDC@LIN-20260401` shape) — the 8 tests added in `89e31a0` are all PERPETUAL/SPOT-shaped,
      which is why this collision shipped uncaught. Re-verify DERIBIT `options_chain` `completion_pct` against real data
      moves off the false `100.0%` clamp (was `expected_shards=210` against a true ~264,550-option universe) and that
      `instrument_windows=None` parity now correctly reproduces `n_instruments * n_dates` (not
      `n_distinct_normalized_keys * n_dates`) for OPTION/FUTURE instrument_types, per the doc's measured collision
      table. Source: `plans/active/issues/bug_c_normalize_id_collision_options_futures_2026_07_22.md`. Done when:
      `_normalize_instrument_id_for_match` is instrument_type-aware per direction (b), new OPTION/dated-FUTURE unit
      tests pass, the doc's two P1/P2 fix+test todos are checked off, and a live re-check of DERIBIT `options_chain`
      `completion_pct` (or a mocked-equivalent regression test asserting the corrected denominator math) confirms the
      false-100% clamp is gone.
- [ ] [BACKEND] P2. Isolate the dominant memory contributor behind the CeFi raw-tick recon Cloud Run job's OOM (measured
      `peak_rss=8646.5MB` against the old 8Gi limit, now mitigated by a 16Gi bump) via a real memory profile of an
      actual execution — `tracemalloc` or a Cloud Profiler session against
      `uts-prod-market-tick-data-service-cefi-t1-recon` — to confirm whether `market-tick-data-service@a6e974b6`'s
      `HyperliquidS3Downloader` per-day cache (`self._trades_cache`, all 24 hourly S3 objects fetched concurrently +
      fully materialized before parsing) is the dominant contributor vs. the 429K-row catalogue load or normal per-venue
      fan-out growth. Once isolated, land the permanent fix for whichever is confirmed: for the HyperLiquid case, either
      cache/retain only the coins this run actually needs (not every coin HL published that day) or stream the 24 hourly
      fetches (parse-then-discard per hour) instead of materializing all 24 decompressed texts up front. Repo:
      market-tick-data-service. Source: `issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`. Done
      when: a memory profile of a real execution is captured and attached/cited in the source doc's Progress Log
      identifying the dominant contributor, AND a code fix bounding that contributor is committed + shipped
      (quality-gates green), with the source doc's corresponding todo flipped and evidence cited.
- [ ] [SCRIPT] P3. **Confirm the sharded `--apply` cefi content-canonicalisation fleet completed corpus-wide, then
      delete the abandoned oneoff dry-run pilot script per its own Delete-when marker.** Check whether the ~44-48-way
      date-range-sharded `canonical-migration-cefi-content-NN-20260719-*` `--apply` fleet (launched ~1hr after the
      unsharded pilot VM `canonical-migration-cefi-content-20260719-121302` was killed at 0.31% done) ran the cefi
      content instrument_id catalogue-canonicalisation to completion + verified corpus-wide (grep
      `vm-logs/canonical-migration-cefi-content-*/run.log` for terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY`/non-zero
      `patched` stats across all shards, cross-check against the availability manifest /
      `cefi_consolidated_closeout_2026_07_18.md`'s Phase-1 corpus-migration record). If confirmed complete, delete
      `market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` per its own
      docstring header (`# Lifecycle: oneoff`,
      `# Delete-when: cefi content instrument_id catalogue-canonicalisation applied + verified corpus-wide`). If NOT
      complete or ambiguous, leave the script in place and record the gap instead of deleting. Source:
      `issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md` (Recommendation item 4). Done when: either the
      script is deleted with cited fleet-completion evidence (run.log grep + manifest check), or a documented finding
      explains why completion could not be confirmed and the script was left in place.
- [x] ✅ [OPS] P0. **DONE 2026-07-26 (slot-4, `data_engineering`) — confirmed NOT running; confirmed launching would be
      WRONG right now, not just premature.** `gcloud compute instances list` (all zones, project
      `central-element-323112`): no VM matching deribit/wave/tardis. Fresh manifest read
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`): DERIBIT
      `options_chain`/`futures_chain` still 113,615/112,728 `attempted_failed`, unchanged since 2026-07-23 apart from an
      unrelated 56-row 404 tail on 2026-07-25 (not a Wave-3 run — a real wave touches tens of thousands of rows). **This
      todo's premise is stale**: `cefi_consolidated_closeout_2026_07_18.md`'s Track 2 was forked 2026-07-25 to
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` (subsumes the old per-venue "Wave-3 DERIBIT LIGHT"
      concept into one consolidated resume-backfill todo) — that forked plan is `status: draft`, `gate_on_depends: true`
      on `cefi_migration_cutover_and_track8_completion_2026_07_25.md` finishing, explicitly because launching early
      "would fight the consolidator." The gating plan itself is `status: draft`, all 5 todos unchecked, no Progress Log
      — Track 1 hasn't started. Launching now would violate the plan authors' own explicit sequencing gate. **Did not
      launch anything.** Full evidence in `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s newly-added
      Progress Log + its own todo (now flipped).
- [ ] [SCRIPT] P2. **unified-api-contracts** — add the missing cefi `DATA_TYPE_CAPABILITY_REGISTRY` entries for
      KRAKEN-SPOT / KRAKEN-FUTURES / BITGET-SPOT / BITGET-FUTURES / BITFINEX-SPOT / BITFINEX-FUTURES / ASTER (currently
      only BINANCE/BYBIT/OKX/DERIBIT/COINBASE/HYPERLIQUID/UPBIT have entries — these 7 venues show EMPTY
      `venue_data_types` in the catalogue CSV export because they're absent from the registry, the SSOT for per-venue
      batch data_types). Add each venue's supported `data_type` set to `DATA_TYPE_CAPABILITY_REGISTRY` (mirror the shape
      of an existing entry, e.g. BINANCE/BYBIT) so the catalogue export and any downstream per-venue capability gate
      resolve non-empty for these 7. Source: /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md (line
      ~183, provenance: cefi full-catalogue CSV export 2026-06-23). Done when: `unified-api-contracts`
      `DATA_TYPE_CAPABILITY_REGISTRY` has a populated entry for all 7 listed venues, `quality-gates.sh` is green, and a
      catalogue export (or the registry's own unit test) confirms `venue_data_types` is non-empty for each.
- [ ] [BACKEND] P0. **Close the four bounded, decision-free residuals from
      `cefi_residual_followups_after_honest_done_2026_07_17.md` that no covering cefi plan cites** (Phase 0b
      DEPLOY-reader-bridge / features image-build fix / Phase 1 OKX-FUTURES itype mislabel / Phase 2 codex
      reconciliation — verified 2026-07-26 as uncovered by every currently-active cefi AO plan, incl.
      `cefi_migration_cutover_and_track8_completion_2026_07_25.md` which only covers the Phase-1
      parquet-content-backfill/rename/manifest-completion/residual-#3/drain items). Do all four (independent files, safe
      as one worker's sequential pass):
  1. **DEPLOY the D3 reader-bridge build to the 4 in-scope narrow-read consumers** (MTDS `reader.py`, MDPS,
     features-service `raw_data_loader.py`/`batch_handler.py`, execution-service `algo_library/mtds_book_provider.py` —
     the last needs only a redeploy, no code change). The bridge code is already shipped on `origin/main` per the doc's
     2026-07-18 Progress Log ("Reader-bridge VERIFIED READY") — this is the deploy/redeploy step, not new development.
     (repos: market-tick-data-service, market-data-processing-service, features-service, execution-service)
  2. **Fix the features-service image build** — `cefi_wire_bridge.py:59 import CeFiWireCanonicalMap` ImportError because
     the pinned `BASE_IMAGE_DIGEST` predates the UAC symbol. Bump `BASE_IMAGE_DIGEST` to a base image with fresh UAC, OR
     switch features to COPY-fresh-UAC-source like its MTDS/MDPS/execution siblings (worker's engineering choice, not a
     design decision). (repo: features-service)
  3. **Correct the OKX-FUTURES manifest `instrument_type` mislabel** — ~116,742 dated-futures rows (`XRP-USD-240329`
     etc.) manifest-tagged `PERPETUAL` while the catalogue has them as `FUTURE`; relabel PERPETUAL→FUTURE for dated
     symbols only (mostly delisted historical — a data-quality fix, not a cutover blocker, no drain needed).
     Snapshot-first per the manifest delete-safety protocol. (repo: instruments-service)
  4. **Resolve the four named codex↔plan SSOT contradictions**: `chart-candle-delivery-flow.md:274` ("Filename is the
     bare symbol" → canonical target + SUPERSEDED/forward-pointer banner); `read-time-filter-pushdown.md` (update the
     substring-match assumption for now-canonical filenames); `availability-manifest-and-data-status.md` ("immutable
     wire-form contract" superseded for the manifest key); `per-asset-group-bucket-layouts.md:135` (`ticks.parquet`
     bundle vs per-instrument stem split). (repo: unified-trading-pm) **Done when**: all 4 consumers confirmed running
     the reader-bridge build (redeploy logs/version check); features-service image build is green
     (`bash scripts/quality-gates.sh` / CI); a re-run of the OKX-FUTURES itype census shows 0 dated-future rows still
     tagged PERPETUAL, snapshot recorded; all 4 codex docs carry the corrected/superseded content with forward-pointer
     banners where applicable. Source: `cefi_residual_followups_after_honest_done_2026_07_17.md` (Phase 0b "DEPLOY the
     reader bridge…" + "Fix the features-service image build…" todos; Phase 1 "Manifest instrument_type mislabel
     cleanup…" todo; Phase 2 "Resolve the codex↔plan SSOT contradictions…" todo).
- [ ] [IS][OPERATOR] P0. Finish the IS-layer full-catalogue work + the flagged manifest reclassification for the CeFi
      capture rule: (1) drop the `CEFI_BASE_ASSET_UNIVERSE` cap from the IS Tardis adapter `_passes_asset_filter` so IS
      enumerates EVERY instrument per venue (full reference, no universe/perp-gate at the IS layer); (2) force-run
      fetch+aggregate (full enumeration) and export the per-venue `operator_check` CSV (full catalogue + data_types per
      venue) for the operator_check gate; (3) [OPERATOR] re-run the manifest reclassification script
      `market-tick-data-service/scripts/reclassify_cefi_manifest_mvp_universe_2026_06_23.py --apply` to pick up the new
      mvp cells in the honest-coverage denominator — this mutates ~5.49M manifest rows (dry-run measured
      `out_of_mvp_removed=3,651,839 · in_mvp_kept=1,842,949 · empty_confirmed→expected_unattempted=206,673`), so cite
      the script's built-in pre-write snapshot (`_index/snapshots/pre_mvp_reclassify_<UTC>.parquet`) as the
      delete-safety justification and get an explicit operator go before running `--apply` (dry-run first to confirm
      current-day counts still match the 2026-06-23 measurement before applying). Source:
      plans/active/issues/cefi_universe_capture_rule_2026_06_23.md. Done when: (a) `_passes_asset_filter` no longer
      references `CEFI_BASE_ASSET_UNIVERSE` as a cap, IS enumerates all instruments per venue, and the per-venue
      operator_check CSV is exported and reviewed; (b) the reclassification script has been re-run with `--apply` (post
      explicit operator approval) with a pre-write snapshot on disk, and the live manifest's in-MVP row count matches
      the (re-verified) dry-run projection; both remaining unchecked `[IS]` P0 boxes and the flagged "Orchestrator
      follow-up" note in this doc's Progress Log are checked off / resolved.
- [ ] [REVIEW] P1. **Audit the DERIBIT options-chain handler's manifest bookkeeping post-v6-fix, then migrate any
      legacy-shape prod objects.** After `deribit_options_chain_handler.py::_write_shard`'s v6 canonical-path rewrite
      lands (`cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s "Rewrite
      deribit_options_chain_handler.py::_write_shard" todo — which also fixes `record_captured`'s `instrument_type`
      argument from `"option"`→`"options_chain"`), do the FULL audit this doc's todo 3 actually asked for (not just the
      one-field fix already shipped): confirm the handler's `manifest_recorder`/honest-absence bookkeeping shard-atom
      (venue/instrument_type/data_type/day/underlying key, not only the `instrument_type` string) matches the corrected
      v6 object path end-to-end — fix any remaining mismatch found. Then resolve this doc's todo 4: using the object
      count from `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s "Confirm whether the legacy
      pipeline_mode=live_deribit path has any prod objects" todo, if that count is non-zero, migrate the legacy-shape
      objects to the v6 canonical path (copy → verify row/column parity → `[OPERATOR]`-only purge of the legacy-shape
      originals, per `/codex/05-infrastructure/gcs-and-manifest-delete-safety-protocol.md`; note this doc's own analysis
      found one-file-per-write means no fan-in collision risk here, but re-confirm before assuming). If the count is
      zero, this todo closes with no migration needed. Repo: market-tick-data-service. **Done when**: a written
      confirmation (or fix commit) that the manifest shard-atom matches the v6 path for this handler; AND either (a) a
      written zero-object finding closes todo 4 with no migration performed, or (b) legacy-shape objects are copied to
      the v6 path, verified row/column-identical, and the legacy originals are purged only via the `[OPERATOR]` step
      with evidence cited; `quality-gates.sh` green if code changed. Source:
      `issues/deribit_live_options_chain_path_noncanonical_2026_07_21.md`.
- [x] ✅ [DATA] P0. **DONE 2026-07-26 (slot-4, `data_engineering`) — recorded FAIL verdict; correctly did NOT force a
      premature close or file a redundant issue doc.** Fresh manifest read
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`): DERIBIT
      `options_chain` `attempted_failed=113,615` (empty_confirmed=10,096, captured=1); `futures_chain`
      `attempted_failed=112,728` (empty_confirmed=10,983, captured=0) — both essentially unchanged from the 2026-07-15
      baseline (113,595/112,727), both ≫1,000. **Verdict: FAIL, gate still blocked.** Did NOT follow the doc's original
      two prescribed next-steps literally, because both are stale: (1) the "escalate for Tardis rate-limits/sizing"
      resolution-gate text was already superseded by this doc's own 2026-07-18 correction banner (root cause is the
      per-symbol capture gap / bundle-never-built, not rate limits); (2) "file a new issue doc if still ~100% af after
      the backfill ran" doesn't apply because **the coverage backfill has not run at all** — this session's sibling task
      (`cefi_satellite_ao_dispatch_batch2-008`) already traced why: Track 2 was forked to
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, gated on
      `cefi_migration_cutover_and_track8_completion     _2026_07_25.md`, which hasn't started. Filing a new issue doc
      would misrepresent a not-yet-attempted backfill as a failed one. Left the issue doc `status: open` with a dated
      2026-07-26 re-verify section explaining exactly this — the correct re-check trigger is the Track-2 plan's
      POST-BACKFILL checkpoint landing, not another reprobe now.
- [ ] [DATA] P0. **Root-cause the CEFI Tardis download-path memory blow-up and make `mtds_chunk_loop.sh` fail loud
      instead of silently wedging on a child OOM-kill.** Confirmed: identical `--chunk-days 1` chunks for the same
      9-symbol/3-venue CEX-spot set showed 6GB vs 14.6GB RSS on consecutive days (kernel OOM-killed the second), ruling
      out simple date-span scaling. (a) Read `market_tick_data_service`'s CEFI Tardis download path and determine which
      of the three hypotheses in the source doc explains the variance — genuine per-day data-volume outlier for one
      symbol, an unbounded-buffer/retry-storm path that only fires under certain response conditions, or a
      within-process resource leak — via code read plus at least one reproduction attempt (small VM launch reproducing
      the known bad day, `2022-08-26`, for the same symbol/venue set); patch the identified cause if a concrete fix is
      findable, otherwise document the narrowed-down finding with evidence. (b) Independently of (a)'s outcome, fix
      `mtds_chunk_loop.sh` (and its heartbeat/uploader orchestration) to detect a child process OOM-kill or any
      non-zero/killed exit and either fail loud (page/alert, non-zero exit, clear log line) or skip-and-continue to the
      next chunk — never silently freeze the whole VM with no further log/heartbeat/upload activity. Source:
      issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md ("Suggested next steps" items 1 and 2). Done when:
      (a) a findings/fix commit exists in market-tick-data-service documenting or resolving the memory-variance root
      cause, AND (b) a code change to `mtds_chunk_loop.sh`/the wrapping orchestration ships that demonstrably surfaces
      (loud failure or skip-continue) a killed child process instead of going silent — verified via a test that kills a
      chunk's child process mid-run and confirms the loop reacts (does not hang).
- [ ] [DATA] P1. **Fix the 3 MTDS tests broken by UAC's embedded-`:` `build_instrument_id` strictness (Bitfinex
      `ADAF0:USTF0` perpetual + DeFi `WETH:USDC` pool).** Resolve the venue-native colon-bearing symbol against the
      relevant catalogue/wire-map BEFORE calling `build_instrument_id`, or route the genuinely-unresolvable case through
      the UAC quarantine model (`unified_api_contracts.canonical.quarantine`) per the new validator's own error message
      — pick whichever direction fits each call site (do not leave the "sanitize-before-build vs validator-allowlist"
      fork undecided; the quarantine/wire-map route is the one the UAC error message itself signals as intended). Fix
      both call sites:
      `market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py::derive_row_instrument_id`'s
      disabled-by-default fallback (`ADAF0:USTF0`), and
      `market_tick_data_service/market_interface/adapters/defi/canonical_write.py::write_defi_rows` (`WETH:USDC` POOL
      case). Re-check `tests/unit/test_canonical_stem_live_batch_parity.py::test_slash_id_never_forges_a_path_segment`
      separately — confirm whether it's the same fix or a distinct downstream defi-filename-canonical-stem gap. Repo:
      market-tick-data-service. **Done when**: all 3 previously-failing tests
      (`test_slash_id_never_forges_a_path_segment`, `test_decoded_leaf_equals_r1_forward_writer_leaf[WETH:USDC]`,
      `test_disabled_by_default_output_is_byte_identical[BITFINEX-FUTURES-PERPETUAL-ADAF0:USTF0-...]`) pass; full
      `bash scripts/quality-gates.sh` is green for market-tick-data-service (unblocking the fleet-wide MTDS quickmerge
      blocker this regression currently causes); shipped via quickmerge. Source:
      `mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md` (reproduction record; the same fix is also
      tracked with fuller call-site detail in the sibling
      `uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md`, which this todo supersedes/closes as its
      actionable execution — mark both docs resolved on completion).
- [ ] [SCRIPT] P2. **Fix `rotate-exchange-keys/main.py`'s venue key-pattern list to match live GCP Secret Manager**,
      using the per-venue match/renamed-target/no-secret-exists evidence table already appended to the issue doc's
      evidence trail by the batch1 read-only verification todo (`central-element-323112`, ~29 entries covering binance,
      deribit, okx, hyperliquid, polymarket, coinbase, kraken, bitfinex, bitget, upbit, bybit, betfair, kalshi). For
      every entry classified `renamed-target`, update the literal secret name(s) in `main.py` to the verified real GCP
      name per the two-axis model (`/codex/05-infrastructure/secret-manager-naming.md`); for entries classified
      `no-secret-exists`, leave a code comment noting the gap rather than inventing a name. Do not touch entries already
      classified `match`. Repo: deployment-service. **Done when**: `main.py`'s venue list has zero remaining mismatches
      against the evidence table (diff-verifiable), QG green, and the issue doc's 3rd checkbox is flipped `[x]` with the
      commit cited; if this closes the doc's last open todo, run the standard archival ritual. Source:
      `issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`.
- [ ] [CODE] P1. **Log the Tardis HTTP-400 error code, then register Tardis codes 140/300 in UAC
      `classify_venue_error`.** Currently `tardis_csv_transport.py:523` logs only `"Tardis HTTP %s error"` with no code,
      so `code=300` (invalid-symbol) and `code=140` (date-not-available) are indistinguishable in logs even though
      `market-tick-data-service@a7569298` already classifies both as structural-absence in the transport's
      `is_structural_absence` gate. (a) Add the numeric Tardis JSON code to that log line (and any equivalent log point
      on the 400 path) so future measurement/debugging can split 140 vs 300 without re-deriving it from raw responses.
      (b) Register Tardis error codes `140` and `300` in UAC's `classify_venue_error(venue, token)` (currently returns
      no Tardis entries — the 400 path falls through as a raw unregistered token) so the honest-absence-vs-fetch-failure
      decision for Tardis is contract-driven in UAC rather than only string/code-matched inside
      `tardis_csv_transport.py`. Keep 5xx/429/`274` classified as transient/`attempted_failed` — do not touch those.
      Repo: unified-api-contracts (registration) + market-tick-data-service (log line). Source:
      `issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`. **Done when**: the 400-path
      log line includes the Tardis JSON code; UAC `classify_venue_error` has explicit entries for Tardis `140` and `300`
      resolving to structural-absence/honest-absence (not `attempted_failed`); a unit test in unified-api-contracts
      covers both codes; QG green in both repos; the two now-covered checkboxes ([CODE] P1 "Log the Tardis error code"
      and [CONTRACT] P2 "Register Tardis error codes in UAC") are flipped in the source issue doc with commit-sha
      evidence.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md`**: Read the target doc to confirm Phase-1 evidence:
  Phase 1 (ADV consumer scaffold) is fully shipped (features-service@8608ea5d, 3/3 todos [x]). Phase 2 (extend MDPS
  candle coverage to ASTER/HYPERLIQUID/LIGHTER/EXTENDED + backfill) is covered by
  cefi_satellite_ao_dispatch_batch1_2026_07_25.md's explicit-source todo (line 93-95,
  `Source: aster_and_cefi_rolling_adv_feature_2026_07_21.md`). Phase 3 has two remaining items, both still [ ]: 1.
  [BACKEND] P2 — "Design + implement the strategy-side consumption of the ADV signal: position-size cap as a % of ADV,
  and the min-7-day-history-to-trade gate" — the doc's own text flags this "_(Left intentionally light — needs a design
  conversation on where in the strategy pipeline this cap applies and what the % ceiling should be; not yet scoped in
  detail.)_" 2. [DATA] P3 (stretch, optional) — wire `book_depth.py`'s unfilled `adv_30d_usd` input to the same Phase-1
  utility with `window_days=30` — doc text: "out of scope for this plan, a candidate follow-up once Phase 1 ships" (i.e.
  speculative, not yet committed scope either). CONFLICT CHECK: grepped all 17 covering-set docs (consolidated closeout,
  aggregated-sources index, satellite batch1+finalize, migration-cutover, track2, track7, misc-audits (+finalize),
  native-ao-extract (+finalize), 4surface log, bybit-spot-manifest-remediation (+finalize)) for
  `book_depth|adv_30d_usd|volume.?cap|rolling.?adv|ADV signal|position-size cap`. Only two hits: (a)
  `cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` line 59 lists the source doc name in a generic
  finalize-scope enumeration (not a Phase-3-specific claim), and (b)
  `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` lines 176-183, which is the same PASSIVE INDEX reference
  already identified in the Phase-1 evidence — it reproduces both Phase-3 bullets verbatim as "remaining items" but does
  not dispatch or claim them in any active/covered todo. No other doc references `book_depth.py`, `adv_30d_usd`, or a
  strategy-side volume cap. No genuine overlap or competing-approach conflict found — this is a clean "cited nowhere as
  active work" gap, matching the Phase-1 verdict. Dispatch-scope eligibility: Item 1 is explicitly an unresolved design
  call — the doc itself states the cap-%/placement decision is "not yet scoped in detail" and needs "a design
  conversation." This is exactly the class of judgment call the workspace rule reserves for a human/operator session
  first (task_template.md finding + operator ruling 2026-07-23: "figure out how X should look" is a human decision
  wearing a todo's clothes). Item 2 is framed even more tentatively ("Consider whether... should be wired... out of
  scope for this plan") — not a committed, scoped unit of work, and it is presented as a downstream candidate that only
  becomes meaningful once Item 1's strategy-side consumption path exists (book_depth.py's adv_30d_usd is itself a
  strategy/feature-input decision point). Neither item is a bounded, worker-determinable outcome today; both need an
  operator/design decision on where and how the ADV cap plugs into the strategy pipeline before a todo can be drafted
  with a concrete "done when."
- **`plans/active/crypto_alpha_research_2026_07_24.md`**: Conflict check: grepped
  cefi_consolidated_closeout_2026_07_18.md + every batch1/migration-cutover/track2/track7/misc-audits doc (+finalize)
  for the target file paths and mechanism names involved (paper_trading, _ledgers.py, _exec_optimize, R8/short gate,
  tsmom/TS-momentum, basis carry, VWAP-walk, momdaily/_mom_tb, HYPE universe, liquidity_scan, maker-WIDTH, RFQ combo,
  $1M column) — zero hits anywhere in the covering set. No duplicate or competing claim exists; the orphan verdict stands clean, no genuine conflict found. Eligibility verdict: the doc's own §C section explicitly self-classifies its 16 core remaining items as "BLOCKED-OPERATOR-DECISION class ... alpha-research + book-SIZING DECISIONS (which legs, what weights, whether to ship the short sleeve) — they need operator trading judgment, not just code." That framing covers the large majority of the ~20 open items: whether/how to weight the short sleeve, whether to wire R8 into production, whether to ship the de-risk overlay+12% short, basis sizing raw-vs-vol-normed, adding the TS-momentum leg, the deployable capital allocator, and universe expansion (HYPE). These are "which legs/what weights/whether to ship" capital-allocation decisions on a live paper/production book requiring operator sign-off before a worker could execute them. A few items are pure bounded bug fixes with no judgment content (P3 _mom_tb.py MOMDAILY_TAG date-gate bug; P3 audit-script $1M-vs-$250k
  column bug), but they are minor, tightly coupled to the surrounding judgment-gated track, and fracturing them off
  without operator triage risks committing effort to code whose relevance is itself gated on undecided trading
  decisions. Recommend an operator triage pass on this doc (which items to greenlight vs shelve) before any AO todo is
  drafted from it.
- **`plans/active/issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md`**: No conflict with any covering-set doc
  — only batch1's dispatch plan and its finalize doc mention this issue at all, and both do so purely as a citation in
  an exclusion list, not as an attempted fix. The genuine blocker is operator-gated: the doc's own "Proper fix (two
  options)" section is an unresolved architectural fork the operator needs to rule on before any AO todo can be scoped —
  (A) range-loop `collect-onchain-perp-batch` inside one process + rewrite the VM startup script's per-day loop to
  per-shard (bigger blast radius, touches the shared startup script, and batch1's triage flags this option as
  potentially colliding with the live cefi OOM-outage investigation — needs operator confirmation it's safe to touch
  concurrently), vs. (B) add a local-disk cross-process cache to `CeFiCatalogReader` keyed on GCS object generation
  (smaller blast radius, but first needs a quick profiling step to confirm the ~17s CPU cost is the cacheable GCS-parse
  and not an in-memory filter over 428k rows that caching wouldn't fix). Recommended resolution: ask the operator to (1)
  rule out or defer option A until the OOM investigation closes, and (2) if choosing option B, greenlight a small
  profiling sub-task first (cheap, could even be scoped as its own AO-eligible todo: "profile whether the 17s CPU-bound
  block in catalogue_symbols_for_venue is GCS-parse time or in-memory filter time") to de-risk which cache design is
  worth building. Until that ruling lands, this doc stays correctly excluded from AO dispatch, consistent with batch1's
  own triage.
- **`plans/active/issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`**: Conflict check: grepped
  all cefi covering-set plans for any claim on _candle_contracts.py CEFI future registration or
  CEFI_CHAIN_INSTRUMENT_TYPES routing; only batch1's already-dispatched todo (corpus-wide scan, cited from this doc)
  touches it, covering only todo 2. No competing claim on todos 1/3. Todo 1 is a genuine two-option policy fork
  requiring human ruling (register a standalone future candle contract vs. confirm/fix chain-bundle-only routing) --
  batch1's own todo explicitly defers to "the pending human policy decision". Todo 3 is downstream of that ruling and
  cannot be drafted until the policy is set. Recommended resolution: after batch1's scan lands, present the operator the
  fork for a ruling, then draft one combined follow-up AO todo for todo1's chosen fix + todo3's
  implementation/regression test.
- **`plans/active/issues/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`**: Read the target doc in full and
  confirmed the Phase-1 evidence exactly: two remaining open items past everything already shipped/verified. (1) The
  unchecked `[ ] [BLOCKED-CREDENTIALS] P1` todo (lines 407-419) — the prod `tardis-api-key` only has
  free-tier/1st-of-month entitlement for the `lighter` exchange, and the doc itself states the resolution is either an
  operator subscription upgrade OR an explicit operator "accepted-limitation" ruling (1st-of-month sampling only / rely
  on live WS going forward). This is a credential/policy ask by definition — no worker-executable code fix exists. (2)
  The "Follow-up: PACIFICA-SOLANA historical depth — design decision required (NOT auto-dispatchable)" prose section
  (lines 287-307) — explicitly a 3-option human/main judgment call (reduced scope vs. Tardis-delegation vs.
  accept-as-honest-absence), with the doc itself recommending it be routed as its own scoped plan once the decision is
  made. Conflict check: grepped the consolidated closeout, aggregated-sources index, and batch1(+finalize) for the same
  target file/mechanism. No genuine conflict found for either item. For (2),
  `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` lines 318-326 already dispatches a `[DATA] P1` fact-finding-only
  todo ("Probe Tardis exchange-info coverage for PACIFICA-SOLANA") that explicitly does NOT implement any of the 3
  design options — this is complementary evidence-gathering for the eventual operator decision, not a competing fix, so
  no conflict. I also found `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` (lines 83, 211, citing
  `onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`) recommending "Quarantine PACIFICA-SOLANA (no valid lane,
  no catalogue rows, venue culled)" — but per batch1's own excluded-docs section this is about a DIFFERENT underlying
  issue (existing mislabeled `batch_tardis`-path OBJECT disposition from a 2026-07-20 mislabeling bug, itself disputed
  between two sibling docs), not our target doc's "should we keep trying to backfill PACIFICA-SOLANA historical depth at
  all" question. Orthogonal topic, not a same-mechanism conflict — but flag it for whoever eventually makes the
  PACIFICA-SOLANA design-decision ruling, since a "venue culled" quarantine recommendation elsewhere is relevant context
  to option (3) (accept near-total historical gap as honest absence). Dispatch-scope eligibility: both remaining items
  fail the AO-eligibility bar — item (1) needs the operator to either upgrade a paid subscription or make an
  accepted-limitation ruling (a policy call, not a checkable worker task); item (2) needs a human/main judgment call
  between 3 concrete design options, which the doc itself flags as "NOT auto-dispatchable." Neither has a bounded,
  worker-determinable outcome. No candidate_todo drafted — this doc's remaining ground is genuinely operator-gated, and
  the one piece that WAS AO-eligible (Tardis-coverage fact-finding for PACIFICA-SOLANA) is already dispatched in batch1.
- **`plans/active/issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`**: No cross-plan conflict — the
  remaining C1 work (steps 2-5) is simply uncited/undispatched anywhere, not contested by a competing approach elsewhere
  in the covering set. The blocker is operator-only: once the batch1 characterization report (step 1, already
  dispatched) lands, the operator must rule on which EXTENDED-STARKNET copy (or which fields from each) is authoritative
  for the 2026-01-01→~2026-06-04 overlap window — given the fabricated batch_tardis lane holds 28 instruments and an
  entire ohlcv_1m data_type absent from the native batch_extended lane, the likely-correct resolution per the doc's own
  text is "keep the content, fix the label" rather than delete either copy outright. Only after that ruling can a
  bounded AO todo be drafted for the actual re-partition (step 3), the ~34,775-object manifest backfill (step 4), and
  the gated --apply (step 5) — and even then, doc §3.6 says this work should be sequenced behind (or bundled with) the
  still-open cefi catalogue-gap closure (658 ambiguous wire-keys + ~422 objects), whose status is listed as "genuinely
  unknown" as of the most recent cefi_4surface_migration_execution_log_2026_07_24.md entry. Recommend surfacing this as
  an explicit operator question in the next cefi status touchpoint: "Which EXTENDED-STARKNET batch_tardis vs
  batch_extended content is authoritative once the characterization report lands, and should the re-partition wait for
  or bundle with the catalogue-gap canonicalisation pass?" No candidate_todo drafted.
- **`plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`**: Confirmed via full read: the P0
  shipping-freeze is resolved (FIX + VERIFY todos are checked, green sentinel re-established, quickmerge unblocked). The
  sole remaining item is the DESIGN P1 todo, an explicit BLOCKED-OPERATOR-DECISION two-option fork: Option A - declare
  OKX-SPOT its own cefi venue in the venue-by-asset-group registry, drop it from instruments-service's venue-fold table,
  re-remove bare-BYBIT SPOT_PAIR, regenerate the expected-universe golden fixture to 73 tuples; vs Option B - formally
  accept the already-shipped interim fix (a permanent 2-tuple bare-BYBIT expected-unattempted phantom denominator
  inflation). This spans 2 repos (unified-api-contracts and instruments-service) and changes the certified cefi
  denominator either way - a values/tradeoff judgment, not a worker-determinable fact, so it is operator-gated per the
  dispatch-scope eligibility rule. Conflict check performed: grepped the venue-fold mechanism, OKX-SPOT, the UAC root
  commit hash, and Option A/B phrasing across the full covering-plan set.
  cefi_consolidated_closeout_aggregated_sources_2026_07_24.md only re-lists the identical DESIGN todo verbatim (no
  execution). cefi_misc_audits_and_hygiene_2026_07_25.md merely notes the decision lives in this doc while archiving a
  sibling, does not adopt or resolve it. Other OKX-SPOT hits (cefi_consolidated_native_ao_extract_2026_07_25.md,
  cefi_4surface_migration_execution_log_2026_07_24.md) reference a DIFFERENT, unrelated OKX-SPOT gap - a catalogue
  fiat-quote-extension shortfall for OKX-SPOT/COINBASE-SPOT fiat pairs - already tracked as its own separate
  operator-gated item elsewhere, not this doc's venue-declaration/fold-table mechanism. No genuine mechanism overlap.
  The doc also cross-references cefi_layer1_denominator_gaps_2026_07_03.md as a duplicate-avoidance note (resolve there
  or here, not both) - that doc was not in the supplied covering-plan set for this AG batch, so it is out of scope here
  but should be checked for staleness if it resurfaces in a future tranche. Recommendation for the operator when this
  surfaces: the doc's own analysis recommends Option A (matches the BYBIT-SPOT precedent, avoids a permanent
  phantom-tuple denominator inflation), but explicitly flags it as the operator's call since it spans 2 repos and
  touches the certified cefi expected-universe count.
- **`plans/active/issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`**: Deeper conflict-check overturns
  the Phase-1 "orphaned_never_touched" verdict: 3 of the 4 closure items are already functionally covered by real,
  active, non-index todos elsewhere in the covering set (even though those todos cite the SIBLING doc,
  cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md, rather than this file by path — Phase-1's citation-only
  check missed this because it checked "cites this file" not "covers this exact underlying work"). (1) LIGHTER-ZKSYNC
  re-partition: cefi_satellite_ao_dispatch_batch1_2026_07_25.md (line ~331) carries an ACTIVE, fully-specified todo
  "Re-partition the pre-~2026-02 LIGHTER-ZKSYNC ohlcv_1m tail out of batch_tardis" using the existing idempotent
  restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py script, with its own conflict-check note explicitly
  addressing this doc's wider "<2026-04-17" framing as "not a data-safety risk... the existing restamp tool is
  idempotent and would no-op." Covered, not orphaned. (2) PACIFICA-SOLANA quarantine:
  cefi_4surface_migration_execution_log_2026_07_24.md (line 105) carries an open, active "[DATA] P2. Register
  PACIFICA-SOLANA (265) in the fail-hard quarantine set" todo, matching the sibling doc's C3-corrected
  (quarantine-not-purge) disposition this file's item 3 also recommends. Covered. (3) Find/fix the mislabeling writer:
  ALREADY FIXED for EXTENDED-STARKNET per two shipped, evidence-cited commits (market-tick-data-service@356457c2
  2026-07-12, unified-trading-library@08662724 2026-07-18) verified live via the resolver in the sibling doc; the
  remaining generalization (fail-loud the cefi->BATCH_TARDIS fallback for any non-Tardis venue) is ALSO already
  dispatched as an active batch1 todo "Close the residual cefi -> BATCH_TARDIS fabrication path" with a full Done-when
  spec. Covered/stale, not orphaned. (4) EXTENDED-STARKNET re-partition: GENUINE CONFLICT confirmed between this doc
  (treats it as a mergeable dedup move) and the sibling doc's C1 finding (the two lanes are CONTENT-DIVERGENT, not
  simple duplicates -- different md5/size on the same shard, the fabricated lane is actually richer by 28 instruments +
  a whole ohlcv_1m data_type -- so a blind dedup-merge could destroy data). The investigative precursor this requires is
  ALREADY dispatched in batch1 ("Characterize the EXTENDED-STARKNET batch_tardis vs batch_extended content divergence,
  read-only"), whose own Done-when clause explicitly "does NOT pick or recommend a winning copy -- reserved for the
  operator." So the one piece of this doc's closure list with no existing coverage is exactly the undecided two-option
  fork (which copy is authoritative / how to merge) that the batch1 authors already correctly routed to a human
  decision, gated behind the not-yet-run characterization report and the catalogue-gap closure. Net result: nothing here
  is safe or useful to draft as a fresh AO todo -- 3 items are duplicates of already-active work (resolved by logic, no
  competing todo needed) and the 4th is irreducibly operator-gated pending the characterization report's findings.
- **`plans/active/l2_book_microstructure_capture_2026_07_13.md`**: Confirmed both remaining open items via full read to
  the doc's actual end (Progress Log through 2026-07-17). Conflict check: grepped the entire covering set for
  "live-ws/dormant/relaunch", "queue_position/book_microstructure/depth_of_book/MDPS column", and
  "priority_override/park.../backlog.yaml" — the only real hits are unrelated: (a) aggregated_sources' "relaunchable
  arg-required launchers" and 4surface_migration_execution_log's VM relaunch chatter concern the 4surface CeFi migration
  fleet VMs, not the CeFi live-WS tick-capture pipeline; (b) satellite_batch1's book_microstructure_handler.py todo
  fixes a narrow `available_at` wall-clock-vs-deterministic-timestamp bug (source:
  issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md), orthogonal to both remaining
  items here. No genuine overlap — proceeded to the eligibility test. Both remaining items fail the batchable bar, for
  different reasons, so this doc as a whole is operator_gated (the more binding of the two blocks): - Todo 5
  (features-service extractor surfacing queue_position/depth_levels__): this is NOT an open technical gap — it was
  already fully resolved 2026-07-14 (operator confirmed Option C via BLK-e5571ccf): leave queue_position/depth_levels__
  as MTDS-only, no features-service consumer for now; Option A (MDPS column-pipeline extension) is agreed as the
  long-term path but explicitly NOT authorized as its own plan until todo 7's engine-backtest gate is picked up. There
  is nothing here for a worker to execute — the checkbox is deliberately left unflipped to represent
  "resolved-deferred", not "open work". Re-dispatching this as an AO todo would just re-litigate an already-answered
  operator decision. The doc's own Progress Log (2026-07-16, slot 7) already identified the real actionable gap: a
  backlog-hygiene fix (park `l2_book_microstructure_capture-005`/`-007` via `priority: 999`+`priority_override: true`+a
  gating prerequisite in `backlog.yaml`, or add a `PATCH /api/backlog/{id}` endpoint) that needs main/operator with
  orchestrator-VM access — grepped the covering set for `priority_override`/`park.../backlog.yaml` and found zero hits,
  so this backlog-hygiene fix is itself uncovered, but it is infra/orchestrator-code work outside this plan's own repos
  (agent-orchestrator, not market-tick-data-service/features-service/UAC) and requires operator-VM access a worker slot
  doesn't have — genuinely operator_gated, not a same-repo AO-eligible todo. - Todo 7 (CeFi live WS capture dormant
  since 2026-06-29): re-verified dormant as recently as 2026-07-16 and traced to an INTENTIONAL pause
  (issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md, BLK-55d45a68) requiring operator context on the
  correct deployment target and whether the pause should lift — relaunching production live-WS infra unilaterally is
  exactly the kind of irreversible-ish, context-dependent action the eligibility test reserves for the operator, not a
  worker-determinable bounded outcome. Net: this doc has no batchable remaining work. Its only genuinely uncovered,
  non-duplicate residual is the backlog-hygiene park mechanism and the live-WS-pipeline relaunch decision — both
  operator-gated, not draftable as a self-contained AO todo. No candidate_todo drafted.
- **`plans/active/vol_dvol_backtestable_engines_2026_07_13.md`**: Conflict check: grepped the full cefi covering-plan
  set for dvol/volatility_index/VOL_CARRY/VOL_ARB_RV_IV. Found two hits in
  cefi_satellite_ao_dispatch_batch1_2026_07_25.md touching the same file (deribit_volatility_index_handler.py) and same
  data_type (volatility_index), but different mechanisms: batch1 fixes an available_at wall-clock bug and registers
  volatility_index in the cefi data-type enumeration dict (DATA_TYPES_BY_ASSET_GROUP), both sourced from separate issue
  docs unrelated to backtesting or engine registration. No overlap with the target doc's remaining items. Not a
  duplicate, not a genuine conflict. Dispatch-scope eligibility: all 5 remaining open items chain behind one unresolved
  operator fork. The OPERATOR P1 todo is an explicit BLOCKED-OPERATOR-DECISION (full 2021-03-24-to-now vs. a shorter
  historical-depth window for the DVOL pull), standing since 2026-07-13 as BLK-011c84cb. The next SCRIPT todo is
  explicitly self-gated "DO NOT WORK THIS TODO until the OPERATOR todo above is checked off" (confirmed by three
  separate slot-dispatch failures 2026-07-13/14/17), and the 2026-07-25 Progress Log entry confirms this is not fixable
  via sequential/depends_on+gate_on_depends at plan-authoring level -- needs a main backlog.yaml prereqs.conditions edit
  or an AO regen code fix, neither landed. The two engine-registration todos and matrix-regen todo are downstream of the
  backtest that cannot run without the historical pull. No independently-batchable slice exists in this doc. No
  candidate_todo drafted.

## Deferred — time-gated (re-check on the next batch iteration)

- **`plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md`**: Blocked on an unmet
  external/time condition, not on missing coverage. The doc's P3 work (run a Layer-1 completeness audit over affected
  Tardis/cefi venues once re-capture lands, then conditionally build a scoped consolidator-coordinated reconciler re-tag
  for genuinely-permanent blank-instrument_type attempted_failed rows) cannot start until the backlog condition
  `cefi-recapture-sweep-complete` flips true — which requires the actual VM-launch re-capture sweep to run (infra craft,
  out of data_engineering scope per this doc's own slot-9 finding) and complete. That condition is currently
  `value: false` with no relaunch/backfill-orchestration commit yet on market-tick-data-service or deployment-service.
  The task is already correctly wired in the live agent-orchestrator backlog
  (`prereqs.prerequisites: [cefi-recapture-sweep-complete]`, `priority_override: true`) so it will self-surface once the
  sweep genuinely completes — drafting a new AO todo now would either (a) duplicate that existing gated entry, or (b) if
  dispatched prematurely, reproduce the exact 11-dispatch thrash-loop and lockout-era-noise problems this doc's own
  history already documented and fixed once. No competing/conflicting fix exists elsewhere in the covering set — the one
  adjacent mention (migration_cutover doc's bare-wire/`:PERP:` canonical-ID rewrite) targets a structurally different
  problem (path canonicalization of existing rows, not re-tagging blank-instrument_type failure rows) and does not
  overlap. Recommended resolution: re-audit this doc once `cefi-recapture-sweep-complete` is observed true in a future
  closeout pass; only then draft the actual Layer-1-audit + conditional-reconciler AO todo.

## Deferred — human-only (needs a dedicated engineering/design session, not an AO todo)

- **`plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md`**: CONFLICT CHECK found the doc's
  checkboxes are stale, not the covering-plan set silently ignoring the work — a real overlap exists with
  plans/active/cefi_4surface_migration_execution_log_2026_07_24.md, which documents that 3 of the 6 unchecked todos
  already SHIPPED under a different mechanism name than this doc uses: - Todo 1 (A-iso per-shard isolation,
  tardis_cefi_shards.py:144) — SHIPPED `market-tick-data-service@e49e1395` ("write-guard + A-iso per-shard write
  isolation"), confirmed in the 2026-07-22 ~19:50Z DELTA. - Todo 3 (pass `violation_classes={STRUCTURAL}` explicitly at
  the 3 write callsites) — SHIPPED as part of the same `e49e1395` batch: "mtds fail-hard write-guard fix
  (STRUCTURAL-only enforce + Stage-0 ID_FORM observe-log)" via the shared `enforce_structural_and_observe_id_form()`
  helper wired into all 3 callsites (`partitioned_writer.py`, `websocket_runner.py`,
  `book_microstructure_handler.py`). - Todo 5 (`is_quarantined_instrument_id` + `ResolutionEvidence` + registry) —
  SHIPPED `unified-api-contracts@989e9d16` (quarantine model + `classify_id_form()`), noted as "standalone module, not
  wired into any write/read guard yet (that's Stage 3, still future work)" — matches the todo's own scope ("composes, no
  fenced-file edit"). - Todo 4 (Stage 0 classify-and-log at every write/manifest/read site) is PARTIALLY done: the
  write-side observe-log landed in the same `e49e1395` batch, but manifest- and read-site classify-and-log were not
  confirmed shipped anywhere in the covering set. This is the "provably stale/superseded" branch of the conflict check
  (same underlying fix, shipped, just never checked off in this issue doc) — not a competing-approach conflict, so no
  duplicate todo should be drafted for items 1/3/5. The genuinely still-open, uncovered item is Todo 2: "Close the three
  §5 gaps (derivative-bundle column gate; live-lane dual-resolver reconciliation; read marker disposition) before
  write-enforce [ships]." The execution log's own 2026-07-22 deferred-work table confirms this explicitly: "Fail-hard
  design doc §5 three gaps ... not done — genuine unresolved DESIGN gaps, explicitly required before Stage 1
  write-enforce can ship; not started this session ... needs a design pass, not yet scoped to an agent." No later delta
  in that file (through 2026-07-24 ~13:35Z) or in any other covering-set doc revisits it. Todo 6 (schema v10
  `instrument_id_form` backfill) is also open but is explicitly sequenced AFTER Stage 1 (which is blocked on Todo 2) and
  after the still-unrun v2 dedup `--apply` (execution log: "The apply itself ... has NOT run yet") — it is not
  independently actionable yet. Dispatch-scope eligibility: Todo 2 is exactly the design-judgment case the eligibility
  test excludes — it requires designing (a) a real column-value gate for the DERIBIT-style derivative/chain-bundle lane
  whose stem/manifest key never touches the multi-id bundle, (b) a reconciliation strategy between the two independent
  id-derivation front-ends (`get_cefi_wire_map().canonical_for()` for the column vs `resolve_cefi_instrument_id()` for
  the manifest) that currently disagree, and (c) a positive on-disk marker scheme for a bare-wire stem the current
  corpus lacks. These are open-ended "figure out how this should work" architecture decisions, not a checkable/bounded
  outcome a worker can execute alone — the doc's own `nature: design` / `[DESIGN]` tag and the execution log's own
  characterization ("needs a design pass") agree. No candidate_todo is drafted; this requires a dedicated
  design/engineering session (locally, then re-verified adversarially per this doc's original workflow pattern) before
  any of it becomes AO-dispatchable. Once that design session resolves the three gaps, the resulting concrete fixes (and
  the now-unblocked Todo 6 schema v10 backfill) would become legitimate batchable candidates for a future audit pass.
  Recommend the operator/next session also flip the 3 stale checkboxes (1/3/5) in this issue doc to reflect the shipped
  commits so future audits don't re-flag them as open.

## Note — 3 mistags found, not actioned here (flag for a follow-up retag)

Per the skill's Orthogonality/mistag checks, these 3 docs are tagged `asset_group: [cefi]` but their real content is NOT
cefi-specific — excluded from this batch's candidate pool as `exclude_cross_cutting`, and should be retagged (not
archived, not folded into a cefi batch):

- `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` — the breaking-change AST
  differ's blind spot to registry data-dict changes is a generic CI/tooling concern, not cefi-scoped, despite being
  triggered by a cefi-venue incident.
- `plans/active/issues/mtds_ungated_test_families_2026_07_17.md` — fixing ungated defi_handlers/barchart/databento test
  families + a fleet-wide QG scope decision is cross-repo CI hygiene, not cefi-specific.
- `plans/active/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md` — a multi-agent-safety /
  worktree-collision incident report, not cefi-scoped despite the triggering incident touching cefi work.

## Note — 1 doc found archivable_now (not actioned here — a separate archival todo, not a batch candidate)

- `plans/active/issues/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` — both original gaps confirmed closed
  end-to-end (OKX options_chain routing shipped + captured, Deribit combo gap resolved). Ready for the standard 6-step
  archival ritual; not drafted as an AO todo here since archival itself needs no AO worker judgment call, just the
  mechanical ritual — left as an operator/main-agent follow-up.
