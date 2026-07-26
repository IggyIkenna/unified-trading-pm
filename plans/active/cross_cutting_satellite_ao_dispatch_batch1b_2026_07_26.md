---
doc_type: plan
title:
  Cross-cutting satellite AO batch 1 — first Phase-1/Phase-3 triage of the cross-cutting closeout-orphan corpus (part 2
  of 2)
summary: >-
  Second half of the cross-cutting tranche's first AO-dispatch batch — see
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` for the full Phase-1/Phase-3 audit summary, the Deferred
  conflict-gated/operator-gated/time-gated sections (not duplicated here), and the 7 mistags/2 archivable_now notes.
  This doc carries the remaining 15 of the 31 conflict-cleared todos, split purely to stay under the workspace's
  1000-line hard cap after prettier reformatting.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-service,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-1, satellite-docs, fresh-triage]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 — sibling half of cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
  split for the 1000-line hard cap.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 1 (part 2 of 2) — fresh triage extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review, together with its sibling `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`. All 15 todos
> below are same-priority-independent and touch distinct files/docs, except the `smoke_matrix.py` pair (todo citing
> `features_service_coverage_and_script_canon_2026_06_10.md`) which carries inline coordination text with its sibling in
> batch1 — do not strip that text if editing before dispatch.

## Todos

- [ ] [MONITOR] P2. **Bake `deployment-service:latest`'s terraform default forward so it matches the live wave-launcher
      runtime pin** (target repo: `deployment-service`). The `uts-prod-tradfi-wave-launcher` Cloud Run job was
      runtime-re-pinned to `deployment-api@56f2060e` (carries `_write_last_run_sentinel`), but its terraform default
      (`deployment-service:latest`) is still a SEPARATE, older image — a future `tofu apply` would silently revert the
      pin and stop the wave-launcher's host-cron sentinel write, producing a false `DP_CRON_DID_NOT_FIRE` page once the
      6h seed budget lapses. Trigger the `deployment-service-jobs-image-build` Cloud Build trigger from LDR (or confirm
      it already rebuilt on a subsequent LDR push) so `deployment-service:latest` carries the sentinel-writer code, then
      verify the terraform default (`terraform/gcp/` wave-launcher job resource) now resolves to an image containing
      `_write_last_run_sentinel` (grep the built image's digest manifest or `gcloud run jobs describe` post-apply) so
      the runtime pin can safely revert without regressing. **Done when**: `deployment-service:latest`'s pushed digest
      is confirmed to contain `_write_last_run_sentinel`, and the checkbox for this item in
      `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` is flipped `[x]` citing the build id / commit sha
      verified. Source: `dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md`.
- [ ] [SCRIPT] P2. **features-service coverage/script-canon cleanup** — three bounded follow-ups from the 2026-06-10
      coverage session: (1) fix the per-module `pytest --cov=features_service.<module>` scipy/numpy/pytest-cov
      double-import crash on Python 3.13 (pin/patch the version triad or add a tracked conftest pre-import; the
      whole-package `--cov=features_service` CI gate is unaffected — this only unblocks local per-module TDD); (2)
      relocate the smoke/e2e harnesses (`scripts/*/smoke_matrix.py` ×8, `scripts/e2e/*`) from features-service to
      `e2e-testing/scripts/<domain>/` per `/codex/06-coding-standards/script-homes.md`, rewiring them to the
      primary-consumer QG (STEP 5.65) — note this is a physical relocation, distinct from the separate already-open
      "repoint smoke_matrix.py SSOT citations" todo (`mdps_features_deadcode_consolidation_2026_07_20.md` #7 /
      duplicated across the cefi/tradfi/defi/prediction closeout docs), do not touch that doc's citation-only scope;
      **Coordinate with the sibling `silent_wrong_answer_audit_candidates_2026_07_20.md` todo above — it recovers a
      stash fix touching `smoke_matrix.py` before this relocation; sequence this relocation AFTER that stash-recovery
      lands (or re-verify no conflict if this lands first).** (3) run the `script-homes.md` "Per-repo cleanup sweep"
      (classify → relocate/fold-into-CLI/delete-dead, GCS-orphan-verify before any migration-script delete) across every
      repo's `scripts/` EXCLUDING features-service's smoke/e2e harnesses already handled in (2). Source:
      `plans/active/issues/features_service_coverage_and_script_canon_2026_06_10.md`. Done when: per-module coverage
      runs green on Python 3.13 locally; the 8 smoke_matrix.py + e2e/* files exist under `e2e-testing/scripts/<domain>/`
      and no longer under features-service, wired to that repo's QG; every repo's `scripts/` directory has been
      classified per the script-homes canon with dead scripts deleted and relocatable scripts moved, each carrying the
      required lifecycle marker.
- [ ] [CODE] P2. Close the 4 remaining fixable-bug residuals from `fleet_data_acquisition_health_2026_06_21.md`: **(a)
      sports** — recheck `mtds-backfill-odds-*` ODDS_API source-completeness (item #4: manifest flags
      `complete=False missing=['ODDS_API']` despite 8.5K rows across 22 bookmaker shards) and verify the sports-odds
      SOURCE_PRIORITY entry is correct; fix if the completeness-check itself is wrong, or the cred/source registration
      if that's the real gap. **(b) sports** — item #5's `footystats-fwd-*` 0-byte `run.log` (VM startup/log-upload
      never emitted): check a current footystats forward-fetch VM's startup + heartbeat-uploader path; fix the bug if
      still reproducible, or confirm-and-log if it self-resolved. **(c) unified-api-contracts** — fix the
      `book_snapshot` vs `book_snapshot_5` SOURCE_PRIORITY key mismatch (live connectors emit
      `data_type="book_snapshot_5"` but `SOURCE_PRIORITY` keys `("cefi","book_snapshot")`, leaving book writes
      source-unvalidated): register `("cefi","book_snapshot_5")` additively (or rename to one canonical spelling), and
      sweep other asset_groups for the same book_snapshot/book_snapshot_5 key-drift pattern. **(d)
      market-tick-data-service** — verify whether the mtds pyproject↔manifest version-surface drift that blocked
      LDR→staging `quality-gates.sh` on 2026-06-21 (pyproject 0.31.0 vs workspace-manifest 0.25.0 vs repositories.mtds
      0.20.0) is still reproducible today; if still blocking, run the sanctioned
      `scripts/repo-management/run-version-alignment.sh --fix` (never hand-bump); if already resolved by routine
      semver-agent automation, cite evidence it's clear. Source: `fleet_data_acquisition_health_2026_06_21.md`. Done
      when: each of the 4 items has either a shipped fix (repo@sha cited) or a confirmed-resolved/no-longer-reproducible
      note, logged into the doc's body/Progress Log, and its `status:` frontmatter updated to `resolved` if all 4 close.
- [ ] [UTL] P2. **Bound the un-evicted `_CANONICAL_CACHE` to stop the manifest-read OOM (Option A, lowest-risk)** — in
      `unified_trading_library/manifest_writer/_state.py`'s `_invalidate_index_cache` (~L142-166), cap
      `_CANONICAL_CACHE` to the single current bucket: on a bucket-change, `del` the prior bucket's cached DataFrame
      before caching the new one, instead of leaving every visited bucket's merged index pinned in the process-global
      cache forever. This targets the confirmed root cause of the DeFi multi-day batch-backfill OOM (exit_code=137 on
      `e2-standard-4`): the slow per-VM fan-in merge path (`_read_and_merge_per_vm_shards`,
      `manifest_writer/_read_index.py:429-481`) produces a multi-GB merged DataFrame per bucket that `_CANONICAL_CACHE`
      never evicts, so RSS climbs unbounded across a day-loop. Do NOT touch `_read_and_merge_per_vm_shards` itself (that
      is the separate, larger Option B streaming-merge fix — out of scope for this todo) and do NOT remove the
      `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` DeFi-launcher config mitigation (Option C) that already routes most
      runs around the slow path. Add/adjust a UTL unit test asserting that after a bucket switch, the prior bucket's
      entry is gone from `_CANONICAL_CACHE` (e.g. via a size/identity check), and re-run the existing sports-warm-cache
      regression test to confirm the same-bucket warm-read path (`~27s` avoided re-read) is unaffected — this is
      cross-cutting shared code on the LIVE cefi/sports/tradfi manifest-read path, so the no-regression check on the
      warm-cache win is mandatory, not optional. Source:
      `plans/active/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md`. Done when: the per-bucket eviction is
      implemented in `_state.py`, the new eviction unit test and the existing sports warm-cache test both pass,
      `quality-gates.sh` is green, and the change is shipped via quickmerge with the issue doc's frontmatter `status`
      flipped to reflect the resolved Option A (leaving Option B noted as a still-open, separately-scoped follow-on if
      desired, not silently implied done).
- [ ] [DOC] P2. Close the mechanical/AO-eligible remainder of `mtds_plan_reconciliation_2026_06_29.md`'s live findings
      (Section F): (a) **M-C1/M30.5** flip M7 IN-FLIGHT→LANDED in the doc's Section A ledger + fix codex
      `pipeline-mode-partition.md` normative prose (still teaches `live_websocket`, ~lines 84/124/167-180) to reflect
      the verified `live_<source>` runtime state (cefi: 15,993 `live_<source>` rows, 0 `live_websocket`); (b) **M30.3**
      execute the reader legacy-fallback removal in market-tick-data-service `reader.py` (drop the unconditional
      non-`pipeline_mode=` base-path append) — first verify `READER_FELL_BACK_TO_LEGACY_PATH`=0 has held 7d; if not yet,
      report the metric instead of forcing the removal; (c) **M-C4** seed the `_honest_coverage_clusters.py` cluster
      registry for Kalshi CQG (or confirm `cluster_extractor`/`expected_root_clusters` kwargs are wired for it) before
      any Kalshi `prediction_canonical_question_group` write ships, to prevent a `MissingClusterValidationError`; (d)
      **M-C3** residuals: migrate `carry_staked_basis_funding_scan_experiment`'s env-less
      `lst-rates-central-…`/`lending-indices-central-…` bucket reads to `resolve_bucket_name(...)`, and replace the
      (archived) `defi_manifest_canonicalisation`'s G1 `gsutil ls` step with a UTL GCS helper wherever that logic now
      lives; (e) **M-C10** update the 2 still-active v1-coverage consumer plans —
      `data_status_tab_and_downloads_remediation_2026_06_16.md` and
      `issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` — to the codex `honest-coverage-model.md`
      two-layer/Layer-1-gate coverage model instead of the flat `captured/(c+e+f+eu)` formula (the other 3 named M-C10
      consumers — downstream_services/cefi_manifest/defi_manifest canonicalisation — are already archived/superseded;
      skip them). Explicitly OUT OF SCOPE: **M-C7** (warm-GCS-parts live-persistence sink) — real new-code architecture
      work the doc states is "decided, NOT yet built — awaiting greenlight to implement"; that stays a separate
      operator-gated item, not bundled here. Source: `plans/active/issues/mtds_plan_reconciliation_2026_06_29.md`
      (Section A ledger, Section F M-C1/M-C3/M-C4/M-C10, Progress Log). Done when: (a)-(e) each land with a
      commit/evidence citation in the doc's Progress Log, the M7 ledger flip + codex text fix are committed, and the
      doc's `status:` is reassessed (M-C7 remains explicitly open/deferred, not silently dropped).
- [ ] [DATA] P1. **Close out remaining perp-funding data-semantics/cadence CeFi work: exact discrete funding, cadence
      tracker, Aster backfill + live book, margining reverify.** Five independent legs from the same source doc (repos
      market-tick-data-service + unified-api-contracts unless noted): (a) make exact discrete per-settlement funding
      readable — persist funding settlements timestamped to the charge instant (matching venue `fundingTime`), or add a
      canonical per-settlement funding data_type, and document `funding_timestamp` semantics across cefi adapters
      (Tardis cefi, hyperliquid, OKX `next_funding_timestamp`). (b) add a historical funding-cadence tracker in GCS
      (canonical-from-docs or inferred from observed settlement frequency per instrument/day) so a venue cadence change
      doesn't silently mis-annualise historical windows. (c) run the Aster perp-funding backfill VM
      (`deployment-service/scripts/vm/launch-mtds-perp-funding-backfill-vm.sh --perp-protocols aster`, start 2023-07-22,
      default SPOT) — the write path is production-verified-ready (e2e↔production parity confirmed 2026-06-17); this is
      a safe, idempotent write-only historical backfill (no deletes), so no `[OPERATOR]` gate needed; label pre-2024
      rows as Binance-proxied Astherus funding per the doc's genesis note. (d) add a live Aster `book_snapshot_5`
      WS/poll connector mirroring the existing `live/connectors/aster_ws.py` trades connector (REST fallback
      `AsterAdapter.fetch_depth`, `normalize_aster_orderbook` for the 5-level shape, register via
      `register_ws_feed_connector(venue="ASTER", ...)`). (e) re-verify Aster's margining model (`venue_collateral.py`,
      USDC/USDT-only, no spot/LST collateral) against live Aster docs before any cash-and-carry sizing decision.
      **Excludes** (do not duplicate): the pre-funding-genesis Aster trades backfill (explicitly blocked on GAP4 in the
      source doc, and GAP4 itself is already an open `[ ]` todo in `instruments_completion_tracker_2026_07_06.md` Stage
      2a/2b) and the latent cefi `ohlcv_*` direct-write capability (explicitly deferred by the source doc until a
      trades-less cefi venue exists — no current need). Source: `perp_funding_data_semantics_and_cadence_2026_06_16.md`.
      **Done when**: (a)+(b) land as code + tests in mtds/uac with `quality-gates.sh` green; (c)'s VM run reaches
      STOPPED with new Aster `derivative_ticker` shards visible in the manifest for the backfill range; (d) lands with a
      unit test asserting the 5-level book write + manifest record at `pipeline_mode=live_aster`; (e) is recorded as a
      Progress Log finding (confirmed unchanged, or a new dated issue doc if Aster's collateral rules changed).
- [ ] [BUG] P0. **Recover the 2 features-service DEFERRED stash fixes and resolve Finding #2's gas-fee data-location
      question.** (1) In features-service, `git stash list` to find
      `features-safe-survivor-fixes-2026-07-20-DEFERRED-peer-contention-on-smoke_matrix-allhandlers`, `git stash apply`,
      then reconcile the two contained fixes: the `paired_dispatch.py:246` `paired_price_dispersion` delta-one
      `by_date/`→Fold-A `delta_one/` prefix fix (already tested, 29 green) and the `smoke_matrix.py:204`
      feature_group-scoping fix — the latter overlaps landed peer commit `features-service@9ce1f4ab` ("extend
      smoke_matrix with --all-handlers per-handler coverage validation"), so re-diff against that commit and
      rework/dedupe rather than blind-reapply; run features-service QG green, then ship both via quickmerge (or, if
      genuine unresolved overlap remains after reconciliation, leave DEFERRED and record why in this doc, not a silent
      drop). **Coordinate with the sibling `features_service_coverage_and_script_canon_2026_06_10.md` todo below — that
      one relocates `smoke_matrix.py` files to `e2e-testing/`; land THIS stash-recovery fix to `smoke_matrix.py` first
      (or check whether the relocation already landed and re-target the recovered diff accordingly) to avoid editing a
      file mid-move.** (2) For Finding #2 (`pnl_input_builder.py:56,94` — `_load_gas_fee_data` reads
      `gas_fees/chain_id=…/`, a prefix confirmed to exist in NO bucket, so DeFi PnL gas cost is hardcoded to 1 gwei),
      investigate where DeFi gas-fee data is actually captured today (grep MTDS `gas_fee_handler.py` and its writer
      path, check GCS for any gas-fee-bearing prefix across DeFi buckets) and append the answer to this doc: either the
      real bucket/prefix to point `_load_gas_fee_data` at (do NOT ship a blind path-string guess), or a documented
      conclusion that gas-fee data is never captured (file as its own scoped issue/BLOCKED-CREDENTIALS if a new capture
      path is needed — do not fix the read path without a confirmed write-side source). Source:
      `silent_wrong_answer_audit_candidates_2026_07_20.md`. Done when: both stash fixes are either landed (QG green,
      commit sha cited) or explicitly re-DEFERRED with a stated reason in this doc, AND Finding #2 has a documented
      gas-fee-data-location answer (source found + path fix landed, or a BLOCKED/new-issue-doc conclusion) appended to
      this doc.
- [ ] [SCRIPT] P3. Close the stale `strategy_store_split_brain_2026_07_13.md` issue doc — its two remaining reader-code
      legs are already shipped, the doc frontmatter just never flipped. Verify both live: (1)
      `deployment-api/deployment_api/deployment_api_config.py` `effective_strategy_store_{cefi,tradfi,defi}_bucket` all
      default via `resolve_bucket_name(kind="strategy-store")` (the flat unified bucket, no per-AG hardcode) — landed
      `deployment-api@ff1c691` (bucket_fold_closeout_2026_07_17.md loose-end 4c, 2026-07-19); (2)
      `unified-api-contracts/scripts/enumerate_envelope.py` (~line 1060) reads
      `GCS_BUCKET = f"strategy-store-prd-{_PROJECT_ID}"` — no `strategy-store-cefi` hardcode remains (loose-end 4d,
      2026-07-19, UAC tree clean). Once both confirmed, flip `strategy_store_split_brain_2026_07_13.md` frontmatter
      `status: open` → `status: resolved` with `resolved_by:` citing the two shas/dates above, append a closing dated
      note, and run the plan archival ritual (migrate to `plans/archive/2026_07/`, no DEFERRED items to carry, no other
      doc references this path that need updating). Source:
      `plans/active/issues/strategy_store_split_brain_2026_07_13.md`. Done when: both reader-code legs re-verified live
      in current `deployment-api`/`unified-api-contracts` trees, the issue doc's status is `resolved` (or archived) with
      cited evidence, and Track 13 of `cross_cutting_consolidated_closeout_2026_07_25.md` no longer needs this doc as an
      open dependency.
- [ ] [SCRIPT] P1. Reconcile + close the stale-verbatim-carryover checkboxes in
      `legacy_bucket_dual_write_decommission_2026_07_24.md` and land 2 small non-gated hygiene fixes it still owns: (1)
      verify current code state of the two lead "still open" SCRIPT items —
      `unified-trading-library/unified_trading_library/core/cloud_constants.py::get_bucket_name` (confirmed live code:
      the duplicate implementation flagged as the foot-gun was already deleted 2026-07-20, `get_bucket_name` is now the
      sole SSOT-delegating implementation with real cross-repo importers in
      strategy-service/features-service/deployment-service/mtds/instruments-service/ml-service — do NOT delete; instead
      audit each importer and redirect only genuinely-legacy no-env-shape call sites to `resolve_bucket_name`, closing
      the item as done where already fixed) and MTDS `_instruments_metadata.py`/`engine/orchestrator/__init__.py`
      env-LESS instruments-store readers (confirmed live code: all `_instruments_metadata.py` sites already call
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group=...)`, not `build_bucket()`, and the named
      `_sports_instr_bucket`/`_cefi_instr_bucket`/etc. helpers no longer exist in `orchestrator/__init__.py` — mark this
      item DONE with an evidence citation, or find+redirect any residual env-LESS call site if one still exists); (2)
      add the "legacy bucket-name dual-write detection" recurring check to
      `plans/audit/instructions/batch_live_symmetry_master_audit_instructions.md` (extends its existing pipeline_mode
      checks; confirmed absent today); (3) add the reopen-note banner to archived
      `plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` pointing at this doc, and update the
      `codex/05-infrastructure/` bucket-naming SSOT doc with the "writer must use resolve_bucket_name, never
      string-concat" rule. Source: legacy_bucket_dual_write_decommission_2026_07_24.md (lines 54-68, 156-164). Done
      when: both lead checkboxes are flipped (closed-with-evidence or narrowed-to-real-residual-sites), the
      audit-instructions doc carries the new recurring check, and both the archived-doc banner + codex SSOT update are
      committed.
- [ ] [INFRA] P1. **Restore the manifest consolidator (R5-fix-5) for `instruments-store-*` (+ the defi data buckets)**,
      currently interim-mitigated by `MANIFEST_ALLOW_STALE_FALLBACK=true` while every IS CLI loud-fails on the stale
      index. Repo: deployment-service (Cloud Run Job + Scheduler). Restart/repair the scheduled consolidator job so
      `instruments-store-*` and the defi data buckets' `_index/availability_index.parquet` refreshes on its normal
      cadence again, then run ≥2 real consolidation cycles and confirm a fresh manifest read succeeds with
      `MANIFEST_ALLOW_STALE_FALLBACK` unset (no stale-fallback needed). Source:
      `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (R5-fix-5, line ~585). Done when: the Cloud Run
      Job + Scheduler are confirmed running on cadence, ≥2 consolidation cycles complete post-fix with fresh `_index`
      timestamps for `instruments-store-*` + defi buckets, and an IS CLI run succeeds without
      `MANIFEST_ALLOW_STALE_FALLBACK=true` set.
- [ ] [BACKEND] P3. Close out the MTDS retry_safe-convention residuals end-to-end, in order: (1) decide the 2 residual
      non-status-path `else True` sites (`onchain/glassnode.py::_get`, `onchain/helius_solana.py::_rpc_call`) — either
      flip to `else False` for full convention consistency, or keep `else True` with an explicit `# lint-allow`
      comment + rationale for the transient-error-only exception, recording the decision in the plan's Progress Log; (2)
      add a QG lint step to `market-tick-data-service/scripts/quality-gates.sh` banning the unsafe
      `classification.retry_safe if classification is not None else True` / `retry_safe if classification else True`
      fallback idioms in `market_tick_data_service/`, ratchet-baselined to the count decided in (1) (0 if flipped, 2 if
      whitelisted); (3) evaluate generalizing that lint into the shared PM `scripts/quality-gates-base/base-service.sh`
      codex-compliance section — implement if a trivially portable pure-`rg` step, otherwise record why repo-local is
      correct; (4) update `/codex/04-architecture/shard-level-failure-isolation.md` with the finalized convention
      (unclassified venue error defaults `retry_safe=False`; unregistered-venue HTTP errors branch on status before
      consulting the classifier; cross-link the QG lint + fix commits mtds@b8218f8a/f82f29c1); (5) verify parent issue
      doc `issues/mtds_perp_funding_backfill_hang_2026_07_14.md` has no remaining open todos, set its `resolved_by:` to
      this plan + fix shas, and run the issue-doc lifecycle. Repos: `market-tick-data-service`, `unified-trading-pm`.
      Source: `plans/active/mtds_retry_safe_default_audit_2026_07_14.md`. Done when: all 5 original todos in that doc
      are checked with evidence, the QG lint is live and green in `market-tick-data-service`, the codex SSOT reflects
      the finalized convention, and the parent issue doc is resolved/archived.
- [ ] [CODE] P2. **DeFi multi-chain adapter `venue` property still bare, not aligned to the decided PROTOCOL-CHAIN grain
      — align adapter/writer/manifest shard key.** Confirmed still-open 2026-07-26 (live code check):
      `instruments-service/instruments_service/reference_data/adapters/defi/aave_v3.py:214-216` `venue` property returns
      `self._protocol_slug` (bare, e.g. `"aave_v3"`) while records are tagged
      `venue_tag = f"{self._venue_prefix}-{self._chain}"` (PROTOCOL-CHAIN, e.g. `AAVE_V3-OPTIMISM`) at the call site —
      the same bare-vs-chain-suffixed split the 2026-06-19 `_index` reconcile (grain DECIDED = PROTOCOL-CHAIN, UAC
      `ALL_DEFI_VENUES` 150/159 protocol-chain) fixed for STORED data but never fixed at the WRITER, so a fresh capture
      from any multi-chain adapter can silently re-introduce a bare-spelling `_index` row that the reconcile already
      collapsed. Grep `instruments_service/reference_data/adapters/defi/*.py` for the same `venue` property pattern
      (bare `self._protocol_slug`/`self._venue_prefix` returned instead of the chain-suffixed tag used at record-build
      time — `morpho.py` and other multi-chain DeFi adapters are the likely siblings) and make the adapter `venue`
      property, `InstrumentRecord.venue`, and the `unified-trading-library` manifest shard key all emit the canonical
      PROTOCOL-CHAIN id consistently, so new writes match the canonicalised `_index` with no re-reconcile needed. Repos:
      instruments-service, unified-trading-library. Source:
      `plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` (line ~220). Done when: every
      multi-chain DeFi adapter's `venue` property returns the same PROTOCOL-CHAIN string used for its records'
      venue_tag, the manifest shard key derivation uses that same value, a fresh live-fetch smoke test for at least one
      previously-affected venue (e.g. AAVE_V3-OPTIMISM or MORPHO-ETHEREUM/BASE) writes a canonical-form row with no new
      bare-spelling row in the `_index`, and instruments-service QG is green.
- [ ] [CODE] P2. Ship the two remaining AO-eligible residuals from `mvp_scope_catalogue_tagging_2026_06_08.md`: **(a)**
      implement `FeaturesMvpRule` + `StrategiesMvpRule` in UAC's `mvp_scope.py` (replacing the `FeaturesModelsMvpStub`
      placeholders for `features`/`strategy` only — leave `models` stubbed, its MVP taxonomy is
      BLOCKED-OPERATOR-DECISION per the source doc), wire them into a features_service data-status coverage consumer
      (extend the existing `scope=mvp|could_exist|all` pattern from `deployment-api@3390c98` to features/strategy
      coverage), and add unit coverage (MVP-scoped group included, non-MVP excluded, stub-untouched for models). **(b)**
      Re-check the 5 per-AG instruments-consolidator `_index` heartbeat status (already confirmed ENABLED as of
      `mvp_catalogue_finalization_v10_2026_06_27.md` G0 2026-06-27 — re-verify it's still current, not stale) and then
      run the real-data MVP-toggle denominator verify: with `scope=mvp` ON, data-status shows ~100% for captured MVP
      cells and does NOT count non-MVP catalogued instruments as missing; with it OFF, the full could-exist universe
      renders (gap stays honest, not hidden). Source: `mvp_scope_catalogue_tagging_2026_06_08.md`. Done when: (a)
      `FeaturesMvpRule`/`StrategiesMvpRule` land in UAC with a features-service data-status consumer reading them +
      passing tests, and (b) a real-data run against current prod data confirms the mvp ≤ could_exist ≤ all monotonicity
      holds with the correct MVP-cell readout, both cited with commit SHAs/evidence in the source doc's todo lines.
- [ ] [DOCS] P1. **Reconcile the remaining pipeline_mode/live codex docs to the shipped M1-BREAKING + M5 contract**
      (source doc §#7 doc-coherence audit, REMAINING scope). `pipeline_mode-and-batch-live-reconciliation.md`
      (`codex/02-data/`) still frames the `live_websocket` alias as the CURRENT transitional live value ("until the
      `live_<source>` object migration lands", lines ~73/95/117/164/174/211-213) and
      `availability-manifest-and-data-status.md` still documents a `pipeline_mode=live_websocket` worked example (lines
      ~1084-1107) as if it's the live standard — but the source doc's own GATE-0 log shows M1-BREAKING SHIPPED (0
      `live_websocket`/`LIVE_WEBSOCKET` fleet-wide, confirmed by `rg "live_websocket|LIVE_WEBSOCKET" --type py`), so
      these two docs now contradict the live system: update them to describe `live_<source>` as the standard and
      `live_websocket` as a RETIRED/historical alias (do not delete the historical framing, mark it past-tense). Also
      sweep `honest-absence-downstream-handling.md` and `external-data-always-available-rule.md` for the same stale
      `pipeline_mode==source` / pre-source-aware assumptions the source doc's pre-audit (2026-06-05, agent E) flagged,
      and check `CLAUDE.md` + `SUB_AGENT_MANDATORY_RULES.md` for any stale `live_websocket`/pipeline_mode==source claims
      (the `source=` provenance rule and pipeline_mode partition one-liners already look current — confirm, don't
      rewrite if already correct). OUT OF SCOPE: per-AG plan-corpus sweep and CICD-scope items already flagged for
      migration to the cicd plan — do not touch those. Source:
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` §#7. Done when:
      `rg -in "live_websocket" /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md /codex/02-data/availability-manifest-and-data-status.md /codex/02-data/honest-absence-downstream-handling.md /codex/02-data/external-data-always-available-rule.md`
      shows only past-tense/retired-alias framing (no current-standard claims),
      `CLAUDE.md`/`SUB_AGENT_MANDATORY_RULES.md` are confirmed to carry no contradicting claims (note in the commit if
      no edit was needed), changes ship via quickmerge with a real commit sha, and the source doc's §#7 todo
      (line 459) + the "REMAINING" note (line 473-476) are flipped `[x]` citing the sha.
- [ ] [CODE] P2. features-service calendar batch orchestrator: register the two orphaned calculator groups — add
      `"yield_curve"` and `"economic_results"` to `CALENDAR_FEATURE_GROUPS` in
      `features_service/calendar/cli/handlers/batch_handler.py` (currently `["time_features", "economic_events"]`), and
      mirror in `_CALENDAR_FEATURE_GROUPS` in `live_handler.py`. Both calculators (`yield_curve_calculator.py`,
      `economic_results_calculator.py`) already exist and are registered in `feature_builder_registry.py`
      (`group_name="yield_curve"` / `"economic_results"`) but are never dispatched by the `compute` operation, so they
      have been silently 0-shard since inception. Verify the standalone `economic_results_handler.py`
      (`--operation economic_results --mode batch`) does not double-write once folded into the batch loop — pick one
      dispatch path, not both. Source: `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md`. Done
      when: `CALENDAR_FEATURE_GROUPS` includes both groups, a batch `--operation compute` run produces non-zero
      `yield_curve`/`economic_results` shards for at least one recent day, and `quality-gates.sh` is green.
