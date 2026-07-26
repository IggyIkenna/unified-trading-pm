---
doc_type: plan
title: TradFi satellite AO batch 3 — fresh Phase-1/Phase-3 triage of the tradfi closeout-orphan corpus
summary: >-
  Third AO-dispatch batch for tradfi, produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) +
  Phase-3 (conflict-check + draft) triage over all 22 tradfi AG-primary docs not already covered by the consolidated
  closeout, satellite batch1 (+finalize), satellite batch2 (+finalize, both still `status: draft`, undispatched), and
  the forked children (manifest-content-recovery-completion, backfill-throughput-followups, phase-d-terminal-gate,
  registry-coverage-and-ao-readiness+finalize, native-ao-extract+finalize) (2026-07-26). 13 docs came back orphaned (9
  partial coverage, 4 never touched) — the lowest orphan rate of any AG audited this session, since batch1+batch2
  already cover most ground. Phase 3's conflict check cleared 9 into fresh AO-dispatch todos (zero cross-todo file
  collisions); left 1 conflict-gated, 2 operator-gated (1 of which — `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08`
  — is a well-established, repeatedly-confirmed operator-gated item with its own live re-check mechanism already in
  `tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`), and 1 too-large-or-risky item in the Deferred section
  below.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    deployment-service,
  ]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-3, satellite-docs, fresh-triage]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (interactive, operator-approved scope) — Phase 1 classified all 22 tradfi
  AG-primary docs not already in the covering-plan set via a Workflow fan-out (22 agents), Phase 3 ran a conflict-check
  + candidate-todo draft over the 13 orphaned docs via a second Workflow fan-out (13 agents, 1 retried individually
  after an API connection error), per the skill's documented methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 3 — fresh triage extraction

> **Status: active — operator-approved 2026-07-26.** Dispatched per CLAUDE.md's plan-destination rule and the
> ag-closeout-audit skill's autonomous-mode guidance (a skill-drafted AO batch is never auto-shipped; this flip followed
> explicit operator review). All 9 todos below are same-priority-independent and touch distinct files/docs (verified —
> zero cross-todo file collisions).

## Todos

- [ ] [SCRIPT] P3. **Extend UAC's `build_leg()` with an opt-in venue-omission mode.** Currently TradFi combo-leg
      construction bypasses UAC's real shared `build_leg()`
      (`unified_api_contracts.internal.reference.canonical_id_builder`) and instead uses a local `_build_leg_key()`
      helper, because `build_leg()` always includes a venue prefix and TradFi legs deliberately drop it (`TYPE:SYMBOL`
      only, no `VENUE:` prefix — see the doc's shipped P1 "drop venue prefix" fix for the full rationale). Add an opt-in
      parameter/flag to `build_leg()` (e.g. `include_venue: bool = True`) so venue-less-leg consumers (TradFi combos
      today, any future venue-less-leg consumer) can route through the real shared builder instead of maintaining a
      local duplicate helper. Cross-repo: unified-api-contracts (the builder change) + market-tick-data-service or
      instruments-service (swap TradFi's `_build_leg_key()` call site over to `build_leg(include_venue=False)`, delete
      the local helper once parity is proven). Done when: `build_leg()` supports the venue-omission mode with a unit
      test proving byte-identical output to the current `_build_leg_key()` output for existing TradFi combo legs, the
      TradFi call site is migrated to call `build_leg()` directly, the local `_build_leg_key()` helper is deleted, and
      `quality-gates.sh` is green in both repos. Source:
      canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md.
- [x] ✅ [DATA] P1. **Audit R1/R2 legacy-decommission safety after the completed 2026-07-06 v9 apply.**
      `data_completion_tradfi_2026_07_15.md` line 183 (E7) reports the no-env legacy `market-data-tick-tradfi` bucket
      was ALREADY permanently deleted 2026-07-06, but line 298's R1 runbook item requires that deletion to have been
      preceded by an `--also-legacy` migrator run covering the bucket's 2,008-day corpus — and that flag's use was never
      confirmed in this doc's Progress Log. Determine from the 2026-07-06 apply's actual invocation/logs (VM run.log,
      deployment-service launch args, or `tradfi_v9_stage1_finish_2026_07_06.md`'s own evidence) whether `--also-legacy`
      was passed; if it was NOT, this is a data-loss finding (open a `plans/active/issues/` doc + notify operator per
      the governance HARD RULE, do not silently close). Separately audit R2's 3 still-unconfirmed DELETE-AFTER targets
      (line 304: bare `day=*/asset_group=tradfi/` paths without `pipeline_mode=`, old `processed_candles`,
      instruments-store E6 bare paths) for current object-count/existence in `tradfi-prd` +
      `instruments-store-tradfi-prd` — report each as already-clean (0 objects) or still-present with a counted
      inventory for a follow-on `[OPERATOR]`-gated delete. Repos: market-tick-data-service, instruments-service
      (read-only GCS listing only — no deletes in this todo). **Done when**: the `--also-legacy` verdict (confirmed-safe
      or data-loss-flagged) is recorded with its evidence citation, the R1/R2 checkboxes (lines 298, 304) are updated to
      reflect the audited state, and any R2 target still present gets a counted-object inventory appended for operator
      sign-off. Source: `data_completion_tradfi_2026_07_15.md`. — **DONE 2026-07-26 — R1 DATA-LOSS FLAGGED (P0,
      escalated), R2 CLEAN.** Code-verified the completing 2026-07-06 apply's launcher
      (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh`@`77cfcda`) never passes `--also-legacy`; the one
      attempt that did (`canonical-migration-tradfi-20260629-053023`) OOM-crashed after copying only ~1% (37k/3.8M) and
      was never resumed with the flag; the legacy bucket is confirmed permanently deleted (ADC
      `bucket.exists() == False`). R2's 3 checked targets are all 0-objects/clean. Full write-up + operator decision
      request: `issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md`. R1/R2 checkboxes in
      the source doc updated to reflect this (R1 stays open P0 pending operator; R2 flipped done).
- [x] ✅ [SCRIPT] P1. **Tradfi instruments-foundation residual cleanup pass — 4 independent, conflict-clear candidates
      from `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`, bundled into ONE todo because all 4 would otherwise
      edit the SAME doc file concurrently** (mirrors batch2's 7-item combine on this doc): (1) **G1.g MVP tags** — add
      MVP tags to the tradfi MVP universe (VX futures + basis tickers) per the doc's G1.g bullet, repo
      instruments-service. (2) **by_date capture-freeze diagnosis** — root-cause the tradfi `by_date` capture anomaly
      (fleet-wide freeze ~2026-05-21, tradfi degraded from ~2026-05-04, 16K→2/day writes) and add a coverage-horizon
      staleness check to the producer/audit path so a future freeze surfaces loudly instead of silently. (3) **MTDS
      massive.py futures-endpoint fix** — `massive_tradfi_rest_connector.py` maps futures to
      `/v3/reference/futures/contracts` (404s); repoint to the working `/futures/vX/contracts` (+ `/futures/vX/products`
      for contract size), repo market-tick-data-service. (4) **Tombstone dropped Databento instruments** — run
      `reconcile_manifest_after_entity_change.py --mode remove --asset-group tradfi` for the dropped ICE roots
      (BRN/G/DX, softs CT/CC/KC/SB/OJ; datasets IFEU.IMPACT/IFUS.IMPACT): dry-run → audit CSV → apply, then a phantom
      sweep, repo instruments-service. **Excluded from this bundle (stay deferred/gated, do not fold in)**: the G1
      retirement 4-leg purge (ICE/CBOE-OPRA/CBOE-VX-spread/NASDAQ-NYSE-misclass) — needs explicit operator purge
      sign-off; the ICE-futures + CME-futures-options reference-source ask — BLOCKED-CREDENTIALS, needs an operator
      decision on a new data source or unblocking Databento billing; the CME futures reference-gap re-probe —
      BLOCKED-UPSTREAM-OUTAGE, gated on Massive's `/futures/vX/{products,contracts}` endpoint actually recovering.
      **Done when**: (1) MVP tags present on the VX-futures/basis-ticker universe and verified via a catalogue query;
      (2) the freeze root cause is documented (or confirmed self-resolved with evidence) and the staleness check lands +
      is QG-green; (3) the corrected endpoint is verified to return non-404 and quality-gates.sh is green in
      market-tick-data-service; (4) the tombstone dry-run/audit/apply completes with a recorded before/after row count
      and a clean phantom sweep — AND this doc's corresponding checkboxes (G1.g bullet, the by_date/massive.py/tombstone
      rows in the "Folded-in tradfi residuals" section) are flipped in the SAME commit. Source:
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`. — **DONE 2026-07-26.** (1) VERIFIED already done — the
      UAC tradfi `underliers` set already includes VX + the 7 basis-commodity roots; live catalogue query confirms
      `mvp=True` at 100% for all of them. (2) root cause already documented in the source doc (Massive removal broke
      `by_date`; Databento re-feed not yet run — reconfirmed still degraded, ~10-15 writes/day vs the historical
      16-18K); the coverage-horizon staleness check (`_warn_coverage_horizon` / `CATALOGUE_STALE_BY_DATE`) already
      shipped `instruments-service@5d31994a` (2026-07-03), applies per-AG generically incl. tradfi, QG-green in
      production. (3) MOOT — `massive_tradfi_rest_connector.py` no longer exists; Massive was removed entirely as a
      tradfi source 2026-07-19, superseding this fix. (4) shipped — 390,799 rows tombstoned (BRN+G, DXY explicitly
      protected from the venue-level tool's blast radius), phantom sweep clean; also fixed a real Path-B path-resolution
      bug in the tombstone script itself (`instruments-service@8d03893b`). This doc's corresponding checkboxes (G1.g MVP
      tags, massive.py futures-endpoint, tombstone dropped Databento instruments) flipped in the same session.
- [x] ✅ [CODE] P1. **Root-cause the legacy writer that stamped numeric/empty `underlying=` on tradfi combo/chain
      objects (12/13/23, garbled 2-4-char fragments) and add a write-time canonical guard rejecting the same on all NEW
      tradfi chain writes.** — **DONE 2026-07-26.** Investigation found the write-time guard + row-drop already shipped
      2026-07-20 (`mtds@f645ea02` + `uac@7e179ae8`, one day after the issue was filed) —
      `is_recognized_tradfi_underlying` gates `_classify_row` (drops unrecoverable COMBO rows) AND independently gates
      the write-time `canonical_path_violations`/`_tradfi_path_violations` guard that `_get_writer`
      (`market_tick_data_service/engine/orchestrator/partitioned_writer.py`) calls on every tradfi write — covering BOTH
      chain and combo bundles, not chain-only. Existing tests already prove numeric/empty rejected + a real root passing
      (`test_partitioned_writer_tradfi_filename_canonical.py::test_tradfi_chain_numeric_underlying_write_raises` +
      `::test_assert_canonical_chain_path_rejects_numeric_and_empty_underlying`,
      `test_partition_path_is_canonical.py::test_tradfi_chain_numeric_underlying_rejected` +
      `::test_tradfi_combo_opaque_ud_underlying_rejected`) — satisfying done-criteria (b)+(c) with no new code needed.
      Root-caused the historical mechanism via git archaeology: `classify_databento_symbol`'s CBOE `UD:1V:` regex was
      widened `[A-Z]{2,4}`→`[A-Z0-9]{1,4}` (`mtds@c4dc28b4`, 2026-04-18) to accept numeric Globex codes with NO
      downstream root validation — the exact 3-month gap (2026-04-18→2026-07-20) that produced the 189,830-object
      garbage-underlying corpus. Documented this inline at the classifier call site (`uac@8080b645`) and
      cross-referenced it at the enrichment call site (`mtds@377dd90c`), satisfying (a). Updated the issue doc's
      Remediation section (all 3 items struck through/done, `resolved_by` populated), satisfying (d) —
      `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md` (doc is `locked_by: live-defi-rollout`, so left
      status/lock/archival untouched). Repos: market-tick-data-service, unified-api-contracts.
- [ ] [CODE] P2. Evaluate switching aiohttp sessions in market-tick-data-service's Databento/tradfi fetch paths to an
      `aiodns`-backed `AsyncResolver` (in place of the default `ThreadedResolver`, which still runs `getaddrinfo` on the
      shared default executor). If viable (check `aiodns` is already an available/addable dependency, no platform
      blockers), implement it; if not viable, document the blocker inline in the issue doc. This removes DNS resolution
      from the thread-pool executor entirely, making the whole DNS-starvation bug class structurally impossible rather
      than relying on the dedicated-executor convention landed in `mtds@ac857`. Source:
      `issues/databento_default_executor_dns_starvation_risk_2026_07_17.md` ([CODE] P2 todo). Done when:
      aiodns/AsyncResolver is either adopted (with the sessions switched + a quick smoke test confirming DNS resolution
      still works) or a documented decision-not-to (with rationale) is appended to the issue doc, and the doc's [CODE]
      P2 checkbox is flipped to `[x]` accordingly.
- [x] ✅ [BACKEND] P0. **RESCOPED (slot-3, 2026-07-26): Finding 1's write-path root cause fixed + verified; historical
      re-stamp, billing-guard confirmation, and all of Finding 2 (FX instrument_id) remain genuinely open — split to
      `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s Deferred-work table (2026-07-26 Progress Log
      entry) as fresh todos rather than claimed done.** Root-cause and fix the two tradfi FX/live-source write-path
      defects in `tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`. (1) Find the write path stamping
      ICE/KRX/FX `ohlcv_24h` captures as `source=databento` when the SSOT (`tradfi-databento-sourcing-ssot.md`) says
      Yahoo-only — same defect class as the already-fixed 2026-06-19 CBOE `_VENUE_SOURCE_EXCLUSIONS` bug; add the
      missing exclusion(s) for `("ICE","ohlcv_24h")` / `("KRX","ohlcv_24h")` / FX `ohlcv_24h`, re-stamp the
      confirmed-affected historical rows (4 ICE + 12 KRX + 802 FX, likely more on a full walk), and confirm/rule out an
      actual Databento billing-guard call for these off-allowlist venues. **DONE (root cause + fix, not the
      exclusion-table approach originally suggested): traced the actual defect to
      `unified_trading_library.pipeline_mode_resolver     .derive_pipeline_mode_for_row`'s explicit-`--source` branch
      trusting a shared run-level `--source databento` (legitimate for CME/CBOE `ohlcv_1m`/`1s` in the same VM run per
      `launch-tradfi-forward-poll.sh:132`) without re-validating capability for the SPECIFIC (venue, data_type) the
      manifest-finalize call was writing — fabricating `batch_databento` for genuinely Yahoo-sourced ICE/KRX/FX
      `ohlcv_24h`. `_VENUE_SOURCE_EXCLUSIONS` entries would have been redundant (`databento` isn't even registered for
      `ohlcv_24h`); fixed by re-validating via `is_source_capable_for_venue` before trusting the explicit source
      (`unified-trading-library@f237b75a`, regression tests added, QG green). Historical re-stamp + billing-guard
      confirmation NOT done — need a fresh full-history census first.** (2) Find why the FX `SPOT_PAIR` manifest-writer
      call never receives a populated `instrument_id` (unlike every other single-instrument tradfi venue — the real GCS
      parquet content IS correctly id'd), fix the write path, then backfill the manifest `instrument_id` column for the
      4,310 affected historical FX rows via a manifest-only re-stamp
      (`record_captured`/`merge_canonical_with_outstanding_shards`-style — GCS parquet content does not need to change).
      **NOT DONE — untouched this pass, a fully separate write path.** Repos: market-tick-data-service,
      unified-api-contracts. Source: `plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`.
      Original done-when: new captures for both write paths land with correct `source`/`pipeline_mode` and a populated
      `instrument_id`; the cited historical rows are re-stamped/backfilled with before/after evidence counts;
      `quality-gates.sh` green in market-tick-data-service.
- [ ] [BACKEND] P1. Add a manifest-vs-disk consistency check in market-tick-data-service: for a sample/scheduled sweep
      of `capture_status=="captured"` rows in the tradfi tick availability manifest, verify the corresponding GCS object
      actually exists on disk and fail loudly (structured error/alert, not silent) when a captured row has zero backing
      object. This closes the detection gap that let both the 16,389-row contaminated phantom candidate list and the
      3,615 confirmed true-phantom rows accumulate undetected. Repo: market-tick-data-service. Source:
      `tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`. Done when: the check runs (CLI flag or
      scheduled job) against the live `market-data-tick-tradfi-prd` `_index`, correctly flags a synthetic
      captured-row-with-no-object test case, and passes quality-gates.sh.
- [ ] [DESIGN] P2. Give `deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py`'s
      `check_high_attempted_failed` a "known-dead, expected-coverage-narrowed" marker so a deliberately-deferred
      stale-residue cell (whole-manifest-history, no-recency-window count) stops re-paging `DP_RUN_MOSTLY_EMPTY` every
      30 min without requiring an immediate data-purge. Source the marker from cells whose `expected_coverage.py`/UAC
      entry has already been narrowed (e.g. the CBOE `ohlcv_15m` cell narrowed 2026-07-15,
      `unified-api-contracts@78b9e899`) with zero new `attempted_at` activity since the narrowing date — mirrors the
      same open ask already flagged for the sibling `mbp_10`/`corporate_action_confirmed`/`earnings_result`
      stale-residue cells in `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s "Why
      the alert keeps firing anyway" section, so implement one shared mechanism, not a CBOE-only special case. Repo:
      deployment-service. Source: `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`. Done when:
      `check_high_attempted_failed` (or its config) supports flagging a (venue, data_type) cell as known-dead
      post-coverage-narrowing, the CBOE `ohlcv_15m` cell is flagged as the first real instance and stops appearing in
      `DP_RUN_MOSTLY_EMPTY` pages, a regression test covers the new suppression path, and `quality-gates.sh` is green in
      deployment-service.
- [ ] [VERIFY] P3. Trace the manifest-write/orchestrator classification layer for TRADFI's
      `_DATABENTO_SUPPORTED_DATA_TYPES`-filtered-out cells (`mbp_10`, `ohlcv_15m`, `ohlcv_24h`) to confirm exactly how a
      requested-but-filtered data_type is recorded in the tick manifest — `attempted_failed` vs `empty_confirmed` — and
      document the concrete write-site (`market-tick-data-service`'s `venue_fetch.py`/`umi_tick_provider.py` dispatch
      chain plus the manifest-record call it feeds) with file:line citations. Cross-reference this doc's own
      "Verification addendum" finding that `deployment-service`'s `_read_attempted_failed_cells` (DP-FETCH-009,
      `meta_watchers.py`) counts `attempted_failed` over the whole manifest with no date-recency window, to determine
      whether that alone explains why the stale 2026-07-07 rows keep paging, or whether a separate write-time
      classification decision point also exists. Read-only trace, no code changes. Source:
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`. Done when: the classification
      decision point(s) are cited with file:line, a short writeup records the decision logic and whether it accounts for
      the observed stale-row alert persistence, and this doc's `[VERIFY] P3` checkbox is flipped with evidence.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`plans/active/tradfi_multisource_backfill_2026_06_22.md`**: The uncovered item — "[BACKFILL] P1. Run the FX yahoo
  backfill to completion" (line 141, `launch-tradfi-bf-fx-ohlcv-24h.sh` per-year drain to fill remaining
  `expected_unattempted` FX ohlcv_24h manifest rows) — genuinely conflicts with
  `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`, which is STILL OPEN (verified live: `status:...

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`**: No genuine conflict found (see
  reasoning) — this resolves as operator_gated, not conflict_gated. Two operator decisions are needed before any AO todo
  for this doc's remaining work can be drafted: (1) which of the two disagreeing `EXCHANGE_CODE_TO_NAME` dicts
  (`tradfi_instrument_universe.py` vs `tradfi_symbology.py`) is authoritative, or whether...
- **`plans/active/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`**: Not a fresh finding — already triaged
  repeatedly across the covering-plan corpus. The doc's own first todo is an explicit [DECISION] operator call (wire
  mvp_mode live vs. delete dead code) blocking items 2/3. 5 covering docs independently confirm operator_gated;
  tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md (**`status: draft` — corrected 2026-07-26 by
  /plan-reconcile; this entry previously read "(active)", contradicting this same doc's own summary above, which already
  states batch2 "+finalize, both still `status: draft`, undispatched"**) already CARRIES the todo for re-checking this
  doc against autonomous_session_operator_decisions_2026_07_25.md and spinning a follow-up todo once the operator rules
  — but being draft it is NOT ingested/dispatched, so nothing is actively working it. Flipping batch2+batch2_finalize to
  `status: active` is an operator decision (CLAUDE.md § "Plan destination"); until that happens this deferral has no
  live owner.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`**: Not a genuine two-sided conflict (no
  covering-set doc claims this ground) but the doc's own premise is stale: the BLOCKED-OPERATOR-DECISION on the P0
  MDPS/build-continuous item was actually resolved 2026-06-29 (Option B adopted, mdps@cc63d1b +
  features-service@34a5d4ff + mdps@7d630a3, per the now-archived...
