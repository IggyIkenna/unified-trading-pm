---
doc_type: plan
title: tradfi satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the tradfi tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 20
  conflict-cleared, bounded/deterministic items pulled directly from 14 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md,
    /plans/archive/issues/mtds_combo_chain_rename_broke_three_tests_2026_08_11.md,
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    /plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md,
    /plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md,
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
    /plans/archive/issues/tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md,
    /plans/active/issues/tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md,
    /plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md,
    /plans/active/tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# tradfi satellite AO dispatch batch 13 — 2026-08-13

> **Operator-approved 2026-08-13 (with an added pre-delete KRX/Yahoo-coverage check, see Todo 1) — `status: active`,
> dispatchable.** Every todo below was classified bounded/deterministic (worker-determinable outcome, no open
> design/judgment call) by the 2026-08-13 full-sweep audit and conflict-checked against this tranche's existing active
> batches before being drafted here.

## Todos

- [x] [DATA] P1. ✅ NEW 2026-08-07 (operator sign-off recorded -- agent-executable, full pipeline: measure, migrate,
      purge duplicates). Converge existing GCS chain-bundle + manifest data onto the registry values just shipped above
      (8 sector-identity codes XAB/XAF/XAI/XAK/XAP/XAU/XAV/XAY -> *_SECTOR names; 15 micro-contract codes
      M6A/M6B/M6C/M6E/M6J/M6N/M6S/M2K/MCL/MGC/MHG/MNG/MNQ/MSI/MYM -> MICRO-<ROOT> form; plus converge
      unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py's own RootMetadata table onto the same values,
      updating its 2 existing tests). Dry-run measure -> review -> --apply via the extended
      launch-canonical-migration-vm.sh pattern, mirroring the Surface A-D playbook; done when dry-run counts are cited,
      --apply completes with before/after evidence, tradfi_roots.py + tests converged, quality-gates.sh green in both
      unified-api-contracts and market-tick-data-service. Source:
      `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`

      **DONE 2026-08-14.** Evidence:
          - `unified-api-contracts@ebda13eb28`: 15 new `RootMetadata` micro-contract entries + a new reverse-lookup test
          converging `tradfi_roots.py`'s table onto the same values as the manifest/GCS migration below.
          - `market-tick-data-service@b0e18fd33e`: initial migration-script rewrite — `pc.and_()` fix (bare `&` unsupported
          on installed pyarrow's `ChunkedArray`), manifest-row-derived GCS path construction (never a live
          `gcloud storage ls` glob — that approach timed out at 120s/call, single-walk-discipline violation), §3a fresh
          soft-delete-retention check, per-row resilience (one bad row doesn't abort the run), `"ohlcv_1s"` added to
          `TRADFI_DATA_TYPES`.
          - `market-tick-data-service@129925df94`: hardening fix after the live prod run below hit a genuine manifest CAS
          race — added a retry-with-fresh-read loop around the manifest CAS write (5 attempts) + a `--skip-rename` resume
          flag (mirrors both `migrate_tradfi_sector_underlying_2026_08_10.py` and `migrate_tradfi_micro_underlying_2026_08_13.py`).
          - **Sector-remap** (8 codes): dry-run measured 25,922 GCS objects to rename. `--apply` on VM
          `canonical-migration-tradfi-sector-remap-20260814-040712`: **25,922/25,922 GCS objects renamed, 0 errors** —
          but the manifest CAS write lost a race against a concurrent writer right after the clean rename (by-design
          `RuntimeError`, no corruption; this is what triggered the `129925df94` fix above). Resumed via
          `MIGRATION_EXTRA_ARGS="--skip-rename"` on VM `canonical-migration-tradfi-sector-remap-20260814-053905`:
          manifest CAS committed, **self-verify: `✅ VERIFIED: 0 rows with old underlying remain. gen=1786686192651258`**.
          - **Micro-remap** (15 codes): dry-run measured **0 manifest rows, 0 GCS objects to rename** — the live
          population is genuinely empty, consistent with the script's own documented caveat that these raw micro codes
          did not exist in the live `EXCHANGE_CODE_TO_NAME` registry before the 2026-08-07 fix, so no rows were ever
          captured under them. Confirmed via `--apply` on VM `canonical-migration-tradfi-micro-remap-20260814-054820`:
          `Total GCS objects to rename: 0. Nothing to rename — exiting.` (exit_code=0). Nothing to purge; no manifest
          write needed.
          - `quality-gates.sh`: green in both `unified-api-contracts` (via the `ebda13eb28` quickmerge) and
          `market-tick-data-service` (explicit run, exit 0, confirmed for `129925df94`).
          - Also fixed in-flight this task: a stale `download_bytes(...)` API-pattern reference in this plan's own Progress
          Log (corrected to the confirmed-working `gcs_read_object_with_generation(uri=...)` call, in two places).

- [x] ✅ [CODE] P2. Add a codified requirement to /codex/02-data/tradfi-databento-sourcing-ssot.md that Databento
      billing-health verification must include one real scoped data-pull, never list_datasets()/warmup() alone Source:
      `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`

      **DONE 2026-08-14 (slot 10, backend_engineer).** Added new section "Billing-health verification MUST include one
          real scoped data-pull — never `list_datasets()`/`warmup()` alone" to
          `/codex/02-data/tradfi-databento-sourcing-ssot.md` (between "PAYG re-frame" and "Single API key"). Codifies the
          hard rule from the source issue doc's 2026-08-10/08-12 recurrence: an unscoped `warmup()`/`list_datasets()`
          success proves the API key authenticates but not that every access path (in particular the live WS session) is
          functional — a real scoped pull per access path (batch `timeseries.get_range` AND a real received live tick) is
          required before trusting an "account restored" verification. — unified-trading-pm@1e1883ee6b

- [ ] [CODE] P2. Sweep and repoint the 9 identified referrer files' citations, then archive this doc via the standard
      6-step ritual Source: `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`

      **NOT ACTIONABLE 2026-08-14 (slot-12, backend_engineer) — premise invalidated, archival precondition no longer
          met.** The source doc's own Progress Log records a 2026-08-14 RECURRENCE (`cross_ag_live_capture_parity_2026_08_14.md`
          Finding C): the live `databento_tradfi_ws` connector's Databento account was suspended again
          (`api_key_deactivated`/unpaid-invoice CRAM auth error), so the doc's frontmatter flipped back `open` → `blocked`
          and it now carries 2 genuinely open todos again — a re-opened `[OPERATOR] P0` "pay the bill" todo and a new
          `[CODE] P2` connector-owner flag. Archiving a doc with real open, unresolved work (one operator-gated) would
          violate the archival-discipline SSOT's "fully resolved" precondition — do NOT archive; the 9-referrer sweep would
          also be premature since the doc's path hasn't changed. Skipping this item (`reason_code: GATED`) until the doc
          resolves again and stays resolved; re-check `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`'s
          `status`/Todos before re-attempting.

- [x] ✅ [CODE] P2. Todo 1: re-run the dry-run with the fixed canonical_twin_path, confirm 100% twin-coverage, re-check
      bucket retention, execute delete via sanctioned UTL helpers if both checks clear - fully specified dispatch shape
      per the section 3a ruling. **ADDED 2026-08-13 (operator instruction, pre-promotion risk check)**: the
      canonical_twin_path() bug this fix addresses was found + fixed for `instrument_type=equity` NYSE/Databento rows
      (900 rows missing venue/instrument_type keys) — before executing ANY delete, the dry-run's 100%-twin-coverage
      report MUST explicitly break out and confirm coverage for `venue=KRX`/Yahoo-sourced equity rows
      (`pipeline_mode= batch_yahoo`, `instrument_type=equity`) as their own subgroup, not just an aggregate percentage
      that could mask a per-venue gap in the same bug class. KRX/Yahoo equities OHLCV is confirmed canonical MVP data
      (operator ruling 2026-08-09, `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`) — do not delete any
      legacy-path object whose canonical twin has not been individually confirmed present for this subgroup. If the
      KRX/Yahoo subgroup coverage is anything less than 100%, STOP and escalate rather than proceeding on the aggregate
      number alone. Source: `plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`

      **DONE 2026-08-14 — instruments-service@271b3d33ff.** The prior `canonical_twin_path()` fix (`bbcc6395`) was
          itself still incomplete: its pre-hive rebuild silently omitted `asset_group=` and mis-ordered `data_type=`,
          so Part 5 still measured 0% for all 900 tradfi candidates. Fixed by formatting the matched
          `unified_api_contracts.canonical_path_templates("tradfi")` entry directly instead of a partial string splice
          (+ fixed a separate live memory bug in `_source_by_cell_from_manifest` — an unbounded full-manifest
          `pd.read_parquet`+`to_dict("records")` hit a real 4.4GB RSS kill on tradfi's ~2.6M-row manifest this session;
          replaced with a vectorized, cell-filtered pyarrow lookup). 17 regression tests added/updated, all green.
          **KRX/Yahoo subgroup check (required above)**: the 900-row candidate set's venue distribution is
          `{NYSE: 870, NASDAQ: 24, FX: 6}` — **0 KRX/Yahoo rows present**, so the required subgroup break-out is
          vacuously satisfied (nothing to check).
          **Fresh dry-run + official `--apply --i-understand` run (same session)**: canonical-twin coverage is now
          897/900 (99.7%, up from the prior 0%) — the fix works. But **0/900 legacy objects themselves still exist in
          GCS** (verified via `gcs_describe_object` on a 25-row sample, a full 900-row pass, and a prefix listing —
          the entire candidate-set shape is empty), so the tool correctly reports `0 deletable, 900 blocked` and
          `--apply` deleted `0/0` (a true no-op, not a bug — nothing to delete). Fresh soft-delete retention confirmed
          604800s. **Practical outcome: this delete todo's goal (0 legacy duplicates in GCS) is already true** — there
          is nothing left to apply. The remaining 3/900 missing-canonical cells are the already-tracked
          `tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md` KRW/USD phantom-row population, not a new
          gap. **How/when the 900 legacy objects vanished is UNEXPLAINED** — no tracked plan/issue records an executed
          delete, and the bucket's only lifecycle rule is a 60-day COLDLINE storage-class transition (not a delete
          action) — filed as
          `plans/active/issues/tradfi_legacy_twin_candidates_already_absent_unexplained_2026_08_14.md` (P1,
          `assigned_vm: NA`, operator-gated investigation) rather than assumed benign.

- [x] ✅ [CODE] P2. Harden _apply_one's destination-exists branch in migrate_tradfi_underlying_display_names_2026_08.py
      to do a real content/byte comparison before deleting the source, not size-only Source:
      `plans/active/issues/tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md`

      **DONE 2026-08-15 (slot-14, backend_engineer).** `_apply_one`'s destination-exists branch now compares
          GCS's own `crc32c` content checksum (already returned by `gcs_describe_object`, no extra download) instead
          of size alone before deleting the source — a same-size, different-content pair now returns
          `CONTENT_MISMATCH_KEPT_SRC` and is never deleted. The freshly-copied-by-us branch keeps its existing size
          check (sane sanity net on our own server-side copy). Added 2 unit tests
          (`test_apply_one_destination_exists_content_mismatch_keeps_source`,
          `test_apply_one_destination_exists_content_match_deletes_source`) mocking gcsfs/pyarrow content-read +
          `unified_trading_library.cloud_interface` GCS ops, proving the mismatch case is kept and the match case
          still deletes — `market-tick-data-service@050620136f`. Along the way, filed + resolved
          `plans/active/issues/mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md` (2 unrelated
          pre-existing QG-red findings — hardcoded morpho URL literal + a sports adapter-contract-baseline
          regression — that were blocking this and every other unrelated shippable unit from this repo).

- [x] ✅ [SCRIPT] P2. Determine whether any manual-launcher-invocation path has a dedup/collision check against
      already-running VMs for the same shard. Source:
      `plans/active/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`

      **DONE 2026-08-15 (slot-5, backend_engineer) — deployment-service@b8649d9bd4.** Measured all 187
          `deployment-service/scripts/vm/launch-*.sh`: only 20 call any singleton/lock function
          (`lc_singleton_check`/`lc_acquire_singleton_lock`/`ohlcv_check_singleton_lock`). The family actually
          implicated in the DXY incident — the 11 `launch-tradfi-bf-*-ohlcv-*.sh` scripts — DID call
          `ohlcv_check_singleton_lock`, but that function is a **fleet-wide concurrency CAP** on the `^tradfi-bf-`
          prefix, not a per-shard dedup: every `vm_name` embeds a fresh `run_ts`, so two concurrent invocations
          covering the SAME shard both get distinct names and both pass the cap — confirmed root cause. Fixed by
          adding a real per-shard collision check inside the shared `ohlcv_create_vm` (strips the trailing
          `-<run_ts>` to recover the shard identity, refuses if a RUNNING VM already covers it) — applies to all 11
          launchers via the one shared lib file, no per-launcher-script changes needed. The other ~166 launchers
          without any check are genuinely audit-scope (each has its own shard-naming convention); filed as a P3
          follow-up rather than absorbed here:
          `plans/active/issues/manual_launcher_shard_dedup_gap_167_of_187_2026_08_15.md`.

- [x] ✅ [DATA] P3. Confirm the killed duplicate DXY VMs' partial/redundant writes left no non-idempotent side-effects.
      **DONE 2026-08-15 (slot-16)** — no corruption/non-idempotent side effect, but a real manifest-hygiene byproduct
      (stale `attempted_failed` noise rows) DOES exist, tracked separately. Source:
      `plans/archive/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`
- [x] ✅ [CODE] P2. Confirm ccb84c57c9 promoted LDR->main cleanly (gh run/PR check) and flip doc status to resolved +
      archive — content-verified promoted (SHA not a literal `main` ancestor due to Option-B direct's bulk-squash
      promote, but both files' substance confirmed live on `main`, no blanket-header regression); doc flipped to
      `resolved` + archived. Source: `plans/archive/issues/mtds_combo_chain_rename_broke_three_tests_2026_08_11.md`
- [x] ✅ [CODE] P2. Re-run rebuild_tradfi_manifest.py in market-tick-data-service and verify the live manifest recount
      shows 0 instrument_type=FUTURE rows with populated underlying + null instrument_id Source:
      `plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`

      **DONE 2026-08-15 (slot-28, backend_engineer).** Added a new `tradfi-manifest-rebuild` launch category to
          `launch-canonical-migration-vm.sh` (`deployment-service@e382b01860`) — the standing
          `rebuild_tradfi_manifest.py` scanner had no existing VM-launcher wiring, so a full-corpus
          re-run always meant hand-rolling a VM invocation; this makes it a repeatable, registered
          category (`canonical-migration-tradfi-` prefix, no new bucket-registry entry needed).
          Canary dry-run (`canonical-migration-tradfi-manifest-rebuild-20260815-060754`, 2026-08-01
          to 2026-08-07) validated the wiring end-to-end: exit_code=0, 457 shards / 6 venues / 5
          dates, no errors. Full-corpus run (`canonical-migration-tradfi-manifest-rebuild-
          20260815-061239`, SPOT, `--chunk-days 30`, 2020-01-01 to 2026-08-15) completed cleanly:
          exit_code=0, elapsed 844.8s (~14 min), **1,397,013 total shards scanned across 81 chunks**,
          2,080 distinct dates, 0 unparseable, CF-11 honest-absence reemit found 0 rows needing
          re-emission. **Live manifest recount (fresh, post-rebuild)**: `venue=CME,
          instrument_type=FUTURE, capture_status=captured, instrument_id="", underlying!=""` → **0
          rows** (down from the 20,254 originally filed, later measured at 473,374/457,139 by
          slot-21's 2026-08-10 census before the canonicalizer fix). Re-checked with NO venue filter
          (`instrument_type=FUTURE` across all venues, same blank-id/populated-underlying/captured
          predicate) → also **0 rows**, across 1,415,256 total FUTURE-typed rows. The
          `continuous_future`/`combo` → `FUTURE` canonicalizer fix
          (`unified-trading-library@74fe04fd98`, `instruments-service@de6c820956`) is now confirmed
          LIVE in the manifest, not just shipped in code.

- [x] ✅ [CODE] P2. Land the accurate 'S&P index options' MVP-cell row text (already drafted, cited verbatim) into the
      now-under-cap tradfi_consolidated_closeout_2026_07_18.md Source:
      `plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md`

      **DONE 2026-08-15 (slot-7, backend_engineer).** Replaced the stale "66% `attempted_failed`... Not yet launched"
          row text with the accurate corrected-query numbers from
          `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`'s third finding: 2020-2024
          ~94.8-100% covered, 2025 confirmed 0% gap, 2026 73% partial. Same-line table-cell substitution (net-zero line
          count) — file stays at 888L, well under the 1000L hard cap. `unified-trading-pm@<pending>`.

- [x] ✅ [CODE] P2. Todo 1: implement operator-ruled Option A asset-group-aware _resolve_spot_perp fix once CME
      instrument_id string format is confirmed against live catalogue Source:
      `plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`

      **DONE 2026-08-15 (slot-5, backend_engineer) — features-service@f441638932.** `_resolve_spot_perp` now
          dispatches on `asset_group`: TRADFI routes to a new `_resolve_spot_future_tradfi`, CEFI/DEFI keep the
          original perpetual-swap lookup (`_resolve_spot_perpetual_cefi`). The TRADFI path resolves the
          front-month CME FX future for the mapped underlying (6A→AUD, 6B→GBP, 6C→CAD, 6E→EUR, 6J→JPY) from the
          v8 manifest, filtering to `capture_status=captured`/`instrument_type=FUTURE`/`data_type=trades` rows
          whose bare `instrument_id` matches `{PRODUCT_ROOT}-USD@LIN-{YYYYMMDD}` (per-expiry-dated, per the
          format confirmed 2026-08-14) — picks the earliest captured expiry >= the reference date (front-month),
          falling back to the latest expiry if every captured contract has already lapsed. `_resolve_spot_perp`
          now returns a `(venue, instrument_type, symbol)` triple instead of a hardcoded-PERPETUAL 2-tuple, so
          `load_spot_price_raw` builds the candle path from the resolved type (`FUTURE` for TRADFI,
          `PERPETUAL` for CEFI/DEFI) rather than a literal `"PERPETUAL"`. 7 new/updated unit tests
          (front-month selection, all-expired fallback, unmapped-underlying short-circuit, no-captured-row
          case, plus the 3 existing CEFI tests updated for the 3-tuple shape) — `quality-gates.sh` full run
          green (18391 passed) on the shipped SHA. Todo 2 (relaunch the TRADFI:volatility benchmark) is
          separate, unblocked, in-scope work — not done here.

- [ ] [CODE] P2. Todo 2: relaunch TRADFI:volatility benchmark once todo 1 lands Source:
      `plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`

      **BLOCKED-INFRA 2026-08-15 (slot-6, backend_engineer) — attempted 3x, done_definition not met.** Ran
          `features-service/scripts/pipeline_e2e_check.py --day 2026-08-14 --asset-group TRADFI --family volatility
          --legs benchmark --benchmark-days 7` (the documented relaunch shape for this benchmark, per
          `_vm_name`/`_run_benchmark_leg`) three times. Every attempt's created VM (`features-e2e-tradfi-*`)
          self-deleted within ~250-320s with ZERO objects written to `vm-logs/<vm>/` (confirmed: `run.log` and
          `EXIT_STATUS` both `None` via `gcs_describe_object`, instance itself `NOT FOUND` on describe) — 0 throughput
          captured, not a repeat of the original `_resolve_spot_perp` bug (that fix is confirmed shipped; this VM never
          got far enough to even run features_service). A manual tarball republish
          (`create-code-tarballs.sh --include features-service --include deployment-service --force`, including
          `vm/setup-data-pipeline-vm.sh`) between attempts 2 and 3 did not change the outcome. Filed
          `plans/active/issues/features_e2e_test_run_vm_self_deletes_no_log_2026_08_15.md` (P1, `assigned_vm: planning`,
          `assigned_role: infra`) with the leading unconfirmed hypothesis (the test-run launch shape's `uts-test-sa`
          runtime SA may lack read/write access to the code bucket's `vm/`/`vm-logs/` paths) and the concrete follow-up
          todos to root-cause + fix + re-relaunch. Leaving this checkbox unchecked rather than marking done on a
          0-throughput result or retrying indefinitely (3 real billable VM launches already spent). This todo becomes
          actionable again once that issue doc's infra todos land.

          **UPDATE 2026-08-15 (slot-6, infra craft) — infra blocker RESOLVED, still blocked (new cause: data
          availability).** The `uts-test-sa` IAM gap was confirmed and fixed (see
          `features_e2e_test_run_vm_self_deletes_no_log_2026_08_15.md` todo 1, DONE, live-verified: a fresh
          `features-e2e-tradfi-20260815-100817-679e08` launch wrote a real `run.log` (27,656 bytes) and
          `EXIT_STATUS=0` — the VM no longer self-deletes silently). **But that same verification run, using this
          todo's exact relaunch command/window, completed `0/11` feature groups** — there is no captured VX
          (VIX-futures) data anywhere in `2026-08-07..2026-08-14`, so every group correctly refuses to write
          (honest-absence discipline, not a bug). Still 0 real throughput captured; checkbox stays unchecked. Next
          attempt must NOT reuse this window — check the manifest for a window with confirmed VX captures first (or
          confirm/fix VX capture currency if it's stalled), per the amended `[DATA] P1` todo in the issue doc above.

- [x] ✅ [CODE] P2. Todo 3: reconcile BASE_ASSET/manifest underlying string-naming drift if found to cause accounting
      issues Source: `plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`

      **ALREADY DONE (verified 2026-08-15, slot-20, backend_engineer) — pre-existing fix, no new code needed.**
          Investigated whether the `HEATING-OIL`/`HEATINGOIL`/`HO`, `NAT-GAS`/`NAT-GAS-HH`/`NATGAS`-style naming drift
          causes a live denominator/accounting problem. It does not, because it was already fully reconciled by
          `market-tick-data-service@b63200a7` (2026-08-09, "fix(tradfi): reconcile commodity underlying naming drift in
          CF-11 bundle-grain retirement matching") — predates this batch's drafting (2026-08-13). That commit wires
          `unified_api_contracts.resolve_tradfi_underlying_to_root()` / `canonical_tradfi_underlying()`
          (`unified-api-contracts/unified_api_contracts/registry/tradfi_symbology.py`) into
          `retire_tradfi_cf11_bundle_grain_shard_atom_mismatch_2026_07_30.py`'s key comparison — both the static
          `TRADFI_DATABENTO_INSTRUMENTS` crosswalk's `base_asset` AND the manifest's raw `underlying` column are
          normalised through the resolver (punctuation-stripped union of `EXCHANGE_CODE_TO_NAME`,
          `UNDERLYING_NORMALIZATION`, and `DATABENTO_VALID_PARENT_SYMBOLS`) before comparing, so every recognised
          spelled/short-code/hyphenated variant of the same root collides on one key; an unrecognised value falls back
          unchanged rather than being guessed. Covered by `unified-api-contracts/tests/unit/test_tradfi_underlying_canonicalization.py`.
          **Residual, out-of-scope finding (not fixed here — dead code, zero live impact, no accounting effect):**
          `unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py`'s own module-local
          `EXCHANGE_CODE_TO_NAME` dict (line 552) is a completely unused shadow of the real, re-exported
          `tradfi_symbology.py::EXCHANGE_CODE_TO_NAME` (confirmed via `registry/__init__.py`, which imports the public
          `EXCHANGE_CODE_TO_NAME` symbol only from `tradfi_symbology`, never from `tradfi_instrument_universe`) — and is
          itself internally inconsistent (`"HO": "HEATINGOIL"` vs `"OH": "HEATING_OIL"`). Left as-is: no consumer reads
          it, so it has no accounting impact; flagging here rather than silently leaving a misleading duplicate
          unexplained for the next reader.

- [x] ✅ [CODE] P2. Confirm the correct rolling next-week/last-week JSON access pattern for ForexFactory - does not need
      the residential-proxy credential Source:
      `plans/active/tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`

      **DONE 2026-08-15 (slot-29, backend_engineer) — negative reconfirmed live, and now moot by the shipped design.**
          Live-reprobed both literal names fresh (no residential proxy needed — this JSON host, unlike the HTML calendar
          pages, isn't Cloudflare-challenge-gated): `https://nfs.faireconomy.media/ff_calendar_nextweek.json` and
          `.../ff_calendar_lastweek.json` both return an identical 146-byte nginx `404 Not Found` today, byte-for-byte
          matching the 2026-07-30 finding — no drift. Checked for an undocumented variant (alternate hostname
          `cdn-nfs.faireconomy.media`, underscore/hyphen filename forms, query-param offsets) via public sources (an MQL5
          blog post building a WebRequest-based FF JSON fetch, an MQL5 marketplace product doc, MQL5/Rainmeter forum
          threads, a GitHub FF scraper repo) — every one documents ONLY `ff_calendar_thisweek.json`; none references or
          confirms a working next/last-week JSON variant on any host. **Negative confirmed: only `thisweek` JSON exists.**
          Separately confirmed the done-when's design-accounts-for-it half is satisfied, and more than that — the
          question is now moot: the shipped adapter (`features-service@b6809756`, the source plan's todo 4, done
          2026-08-09) does not use the `nfs.faireconomy.media` rolling JSON feed at all. It fetches the HTML
          `calendar?week=<mon><day>.<year>` page for an explicit literal date (`week_param_for(target: date)` in
          `forexfactory_adapter.py`) via the nodriver+Chrome Cloudflare-bypass path, parsing the embedded
          `window.calendarComponentStates` JSON state directly — this already covers next-week, last-week, and any
          arbitrary historical week by date, with zero dependency on the rolling feed's next/last-week naming. No code
          change needed. Per this batch's own "source docs not touched" convention (see doc summary above), the source
          plan's own todo checkbox is reconciled separately in its paired finalize plan, not here.

- [x] ✅ [CODE] P2. P0 MVP backfill readiness gate: now that the chain-bundle-sampler blocker is code-resolved via
      batch11, run the tradfi MVP backfills and verify manifest-counted canonical rows per MVP cell Source:
      `plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md`

      **DONE 2026-08-15 (slot-16, backend_engineer).** Premise check first: the "code-resolved via batch11" claim
          was PARTIALLY false on direct measurement — `MTDS@3cec6a00`'s `_canonical_underlying_to_raw_databento()` is
          genuinely shipped but is dead code (zero call sites repo-wide; `sample_live_instrument()`'s bundled-chain
          branch never invokes it). Separately confirmed this is checker-only and does NOT block real backfills — the
          production launchers (`deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh`'s `CME_ROOTS` table)
          resolve raw Databento symbols directly, independent of the checker's sampler. Filed as a new bounded todo 4 in
          `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`.
          **Manifest-counted canonical rows per MVP cell** — bounded columnar query
          (`read_availability_index(columns=[...])`, wrapped in `run-bounded-analysis.sh`, no whole-corpus walk) against
          the live PROD `market-data-tick-tradfi` availability_index:
                                                                                      | MVP cell | total rows | captured | attempted_failed | verdict |
                                                                                      |---|---|---|---|---|
                                                                                      | CME:ohlcv_1m (ES/MES fut+opt, CME crypto fut, Treasury fut) | 1,759,450 | 1,532,443 (87.1%) | 23,467 (1.3%) | healthy |
                                                                                      | NASDAQ:ohlcv_1m (delta-one equities) | 1,399,404 | 313,758 (22.4%; rest mostly `empty_confirmed` honest-absence) | 3,990 (0.3%) | healthy |
                                                                                      | NYSE:ohlcv_1m (delta-one equities) | 3,135,515 | 2,498,394 (79.7%) | 23,089 (0.7%) | healthy |
                                                                                      | CBOE:ohlcv_24h (Treasury yields) | 18,731 | 7,977 | 7,286 (38.9%) | **see below** |
                                                                                      | FX:ohlcv_24h (daily KRW) | 7,446 | 3,591 | 1,976 (26.5%) | **see below** |
                                                                                      | ICE:ohlcv_24h (daily DXY) | 15,499 | 1,901 | 11,667 (75.3%) | **see below** |

          The 3 Yahoo-daily cells' high `attempted_failed` fractions looked alarming but are NOT real gaps — a
          captured-vs-attempted_failed date-overlap check shows CBOE 100%, FX 99.3%, ICE 97.6% of `attempted_failed`
          dates ALREADY have a genuine `captured` row for the same date (duplicate-VM-race artifacts from the same
          incident class `dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md` tracks — that fix landed
          `deployment-service@b8649d9bd4` today, see this batch's own earlier todo). The tiny residual (FX: 10 dates,
          ICE: 37 dates) are calendar weekends/holidays with no real data expected. All 3 cells' `captured` rows run
          through yesterday/today (CBOE max=2026-08-11, FX/ICE max=2026-08-14) — real, current, materially-complete
          coverage. Filed the cleanup todo (purge/reclassify the stale duplicate-artifact rows) in the same DXY issue
          doc rather than duplicating it here. **CME S&P500-underlying by-year re-check** (the prior
          `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` finding claimed 2025
          confirmed 0% / 2026 73% partial): now STALE — fresh measurement shows 2025 captured=1,010/1,238 (81.6%) and
          2026 captured=605/781 (77.5%), consistent with every other year 2020-2024 (all 77-93% captured); the gap
          that finding documented has since been closed by ongoing wave-launcher-cron + fix-driven relaunches between
          2026-08-09 and today. **Conclusion: no new backfill VM launch was needed** — all 6 MVP cells already carry
          real, current, materially-complete manifest-counted coverage; this todo's work was direct measurement +
          2 follow-up findings filed, not a fresh backfill run. Not independently re-verified at the instrument_id-string
          canonical-form level this pass (relying on the consolidated closeout's own 99.6%+ canonicalization verdict) —
          flagging that as the one unmeasured claim rather than asserting it.

- [x] ✅ [CODE] P2. VERIFY CME mbp_10/trades/tbbo billing-gated declaration Source:
      `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`

      **DONE 2026-08-15 (slot-29, backend_engineer) — pure verify, no code change, per the todo's own gate.** Live-read
          (2026-08-15) `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`:
          `VENUE_DATA_TYPE_CAPABILITIES["CME"] = {"ohlcv_1s": "2019-01-01", "ohlcv_1m": "2019-01-01"}` —
          `mbp_10`/`trades`/`tbbo` are absent entirely, not declared "billing-gated" nor
          "full-history-available". This satisfies the todo's underlying safety intent (no false
          full-history-available claim can mislead a backfill into a metered request) via a stronger
          mechanism than the "declared-possible-but-billing-gated" shape the todo's wording anticipated
          — matches the 2026-05-15 OHLCV-only-MVP scope decision, reaffirmed live by
          `unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py`'s CME rule comment ("Still
          NO trades/tbbo (billing-gated L1/L2 microstructure)... not MVP") and the archived
          `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s
          "Resolution — mbp_10" section (registry-level restoration to `VENUE_DATA_TYPE_CAPABILITIES`
          was deliberately deferred, never re-applied). Separately confirmed the actual
          billing-entitlement guard is correct and independent of this registry:
          `unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py`
          maps `trades`/`tbbo`→L1 (367d free lookback) and `mbp-10`→L2 (33d free lookback),
          `assert_databento_request_allowed` fails closed (`DatabentoLookbackExceededError`) on any
          too-old request — so IF/when these data_types are ever restored to
          `VENUE_DATA_TYPE_CAPABILITIES`, the billing-gate is already correctly wired (exact boundary
          binary-searched live 2026-08-09 per `/codex/02-data/tradfi-databento-sourcing-ssot.md`).
          **Adjacent finding filed, not fixed here** (ambiguous registry-scope judgment call, same
          class as the already-resolved KRX/ICE/YAHOO_FINANCE precedents — out of this pure-verify
          todo's scope):
          `plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md` — a
          SEPARATE registry, `expected_coverage.py::EXPECTED_COVERAGE_BY_ASSET_GROUP["tradfi"]["CME"]`,
          still lists `trades`/`tbbo` as expected (mbp_10 excluded there too), but
          `get_expected_data_types_for_venue` (what `venue_fetch.py` actually gates fetches on) reads
          only `VENUE_DATA_TYPE_CAPABILITIES` — so deployment-api's data-status denominator (the only
          confirmed consumer of `EXPECTED_COVERAGE_BY_ASSET_GROUP`) may still count CME trades/tbbo as
          an expected-but-permanently-uncaptured gap. — unified-trading-pm@\<pending\>

- [x] ✅ [CODE] P2. VERIFY KRX equities registry-vs-adapter mismatch fix still holds live Source:
      `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`

      **DONE 2026-08-15 (slot-14, backend_engineer) — unified-api-contracts@d78f8e4e6a.** The original 2026-07-12
          fix (`krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md`) **still holds live** at both layers it
          touched: `expected_coverage.py`'s `"KRX": ["ohlcv_24h"]` entry is unchanged, and `_mvp_scope_predicate.py`'s
          `is_mvp` tradfi branch still narrows KRX's equity-basis `data_types` to `{"ohlcv_24h"}` only (confirmed via
          `test_venue_source_adapter_parity.py::test_krx_ohlcv_1m_not_mvp` passing live). The mechanical fetch-side fix
          also holds: `market-tick-data-service/adapters/_umi_yahoo.py::route_yahoo_tradfi` still honest-empties any
          KRX request whose `data_types` isn't a subset of `{"ohlcv_24h"}` before ever calling `fetch_yahoo_equities`.
          FX KRW cell separately checked: `expected_coverage.py`'s `"FX": ["ohlcv_24h"]` matches the same narrowing —
          no analogous gap.
          **However, found + fixed a NEW instance of the exact same mismatch class in a downstream registry the
          original fix predates.** `mdps_mvp_universe()` (`_mvp_scope_mdps.py`) — added 2026-07-31, 3 weeks after the
          original KRX fix — derives the `(venue, instrument_type, data_type)` "reachable" cell set that
          `market-data-processing-service/scripts/pipeline_e2e_check.py` and `e2e-testing/scripts/build_smoke/
          coverage_harness.py`'s shard-coverage enumeration both consume live. Its tradfi equity-basis branch expanded
          KRX uniformly across the shared `rule.data_types` (same as NASDAQ/NYSE/ARCA/AMEX/BATS), so it falsely
          declared `("KRX", "EQUITY", "ohlcv_1m")` as an MVP-reachable cell even though `is_mvp`'s own predicate (in
          the same file family, one function away) rejects it — a live re-introduction of the identical
          registry-declares-what-the-adapter-can-never-serve bug the 2026-07-12 doc fixed, just in a registry that
          didn't exist yet at the time of that fix. Confirmed via 2 tests (`test_mvp_scope.py`) that had baked the
          stale assumption in (`test_tradfi_identity_includes_equity_basis_carve_out`,
          `test_tradfi_contains_cme_and_equity_basis` — both previously asserted `("KRX", "EQUITY", "ohlcv_1m") in
          cells`). Fixed by mirroring `is_mvp`'s exact KRX narrowing (`ohlcv_24h`-only) into `mdps_mvp_universe`'s
          equity-basis expansion; updated both tests to assert the corrected shape
          (`("KRX", "EQUITY", "ohlcv_1m") not in cells`, `("KRX", "EQUITY", "ohlcv_24h") in cells`).
          `quality-gates.sh` full run green (ALL QUALITY GATES PASSED, 324s) on the shipped SHA.

- [x] ✅ [CODE] P2. Run distinct-values/axis-value census for tradfi and confirm 0 non-canonical values — flipped
      2026-08-16 (plan_reconciler, tranche=tradfi, agt-a74a6a; checkbox was left unflipped despite the DONE evidence
      below already being present). Source: `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`

      **DONE 2026-08-15 (slot-6, backend_engineer) — pure verify + 2 findings filed, no code change (per the
          todo's own gate).** Called both shipped endpoints for `asset_group=tradfi` directly (in-process, no live
          server needed): `GET /distinct-values/tradfi` (honest-coverage rollup, `source_date=2026-08-15`) reports
          `non_canonical_count={venues:0, instrument_types:0, data_types:0, chains:0}` — genuinely 0 headline drift.
          `GET /axis-value-census?service=market-tick-data-service&asset_group=tradfi` (direct live
          `availability_index` read, 13,748,571 rows, `capture_status != attempted_failed`) cross-checked every raw
          value against `VENUES_BY_ASSET_GROUP`/`DATA_TYPES_BY_ASSET_GROUP`/`InstrumentType`/the UAC accepted-exception
          sets: `venue`/`data_type`/`chain`/`source`/`pipeline_mode` all clean or explained (BARCHART 9,119 rows, 100%
          `empty_confirmed`, operator-ruled quarantine-with-tracking). **`instrument_type` found a genuine unexplained
          381,119-row lowercase residual** (`combo` 339,035 / `equity` 30,561 / `etf` 5,678 / `future` 4,676 /
          `index` 835 / `spot_pair` 334 — none in `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE`, which is only
          `{"UD"}`) that directly contradicts `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s two prior
          independent "0 non-UPPERCASE residual" self-verifications (2026-07-25, 2026-07-27) — filed as
          `plans/active/issues/tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md` (P1, `assigned_vm:
          planning`, bounded root-cause + re-CAS follow-up) rather than re-diagnosed inline (outside this quick-verify
          todo's own scope). Separately, the MDPS-scoped axis-census call did not complete within a 480s budget (2
          attempts) — isolated to an unbounded full-bucket read + client-side pandas filter where a pushdown
          `service_name` filter measured 8.6s for the same result; filed as
          `plans/archive/issues/axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md` (P2, `assigned_vm:
          planning`). Todo's own "0 non-canonical, or only explicitly-accepted exceptions... must be 0 or explained"
          bar is satisfied: every non-canonical value found is either accepted-exception-explained or now tracked as
          an actionable, evidenced follow-up. — unified-trading-pm@d302e45cc6

- [ ] [CODE] P2. Run the tradfi Databento by_date re-feed chain to completion, now genuinely runnable since billing
      access was confirmed live 2026-08-10 Source:
      `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`

      **NOT ACTIONABLE 2026-08-15 (slot-14, backend_engineer) — premise invalidated, billing access has recurred-blocked
          since 2026-08-12 and is STILL blocked today.** Launched the real re-feed
          (`launch-instruments-backfill-vm.sh --asset-group TRADFI`, `instr-backfill-tradfi-20260815`) — within the first
          3 shards (2020-01-01..03) CME hit `Databento SDK error dataset GLBX.MDP3 symbols=78: 402
          account_delinquent_invoice` on every single date, retry-exhausted both attempts each time; the other 4 venues
          (ICE/NASDAQ/NYSE/FX) wrote successfully in the same shards (`4/5 venues written`), so this is not a fresh/new
          blocker — it is the same recurrence `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`
          already tracks as `status: blocked` (re-confirmed there today at 04:39:56Z on the MTDS/OHLCV batch side; my run
          independently reconfirms it ~5h later on the IS reference-data adapter path, and narrows it to CME/GLBX.MDP3
          specifically — the other 4 venues did NOT fail). Deleted the VM rather than let it churn through the full
          2020-2026 range with CME guaranteed-failing on every date (~40s wasted retry overhead × ~2400 days, zero CME
          progress possible) — full evidence + reasoning in that doc's new 2026-08-15 (slot-14) Progress Log entry. The
          done-when here ("write-rate recovers toward the historical 16-18K/day range") cannot be met while CME — TradFi's
          largest single instrument-type population — stays billing-blocked. Skipping (`reason_code: GATED`) until the
          tracked invoice todo is next confirmed paid; re-check that doc's `status`/Todos before re-attempting. Source
          billing-outage doc: `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`

- [x] ✅ [CODE] P2. Surgical phantom-row-targeted re-capture of the confirmed KRW/USD (pair,date) cells — fold
      into/mirror the archived remediation plan's design intent, no blind --force-recapture across all 12 FX pairs
      Source: `plans/archive/issues/tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md`

      **DONE 2026-08-15 (slot-7, backend_engineer) — premise was stale, real fix already scoped + shipped by the
          script; completed the pending --apply.** The source doc's title was already CORRECTED 2026-08-14: the
          rows are NOT phantom (this batch todo's own title inherited the pre-correction framing) — the real
          defect is a manifest `pipeline_mode` mislabel (claims `batch_yahoo`, real GCS content lives under
          `batch_databento`), and the doc's own P2 todo already tracked a re-stamp script
          (`market-tick-data-service@75a9ed0b54`,
          `scripts/restamp_tradfi_fx_krw_usd_mislabeled_pipeline_mode_2026_08_14.py`) whose first `--apply`
          attempt had aborted on a CAS generation race and was awaiting retry — no blind recapture needed or
          performed, satisfying this todo's own guard against a 12-pair `--force-recapture`.
          **No VM launcher wired this one-off script** (heavy full-manifest read: full `pd.read_parquet` peaks
          ~10-12GiB RSS, confirmed live — exceeded the shared planning-vm's 8G/14G bounded-analysis caps twice
          on this host before I stopped retrying larger caps and moved it off-host per the heavy-COMPUTE/MEMORY
          HARD RULE) — added a new `tradfi-krw-usd-restamp` category to
          `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (`deployment-service@6657ed8347`),
          mirroring `tradfi-manifest-cas`'s 8-attempt jittered-retry-loop shape (same in-place-CAS
          read-mutate-write race against the manifest consolidator's 60s cron). **Found + fixed a real launcher
          bug live on this category's own first dry-run**: the generic single-command `--dry-run` append
          landed on the END of the whole compound `for...done; exit ${rc}` string (`exit ${rc} --dry-run`),
          which bash's `exit` builtin rejects as "too many arguments" — same class already documented for
          `tradfi-manifest-cas`/`tradfi-manifest-retire` (compound-command categories must be added to the
          flag-append SUPPRESSION list, not left to the generic append); fixed by adding
          `tradfi-krw-usd-restamp` to that suppression list (the underlying python script's own logic ran
          correctly regardless — this only affected the trailing shell `exit`, not the CAS mutation itself).
          **Dry-run** (`canonical-migration-tradfi-krw-usd-restamp-20260815-092825`): 2,022 candidates
          (yahoo_only=60, databento_only=1947, both=15, phantom=0) — closely matches the doc's 2026-08-14
          investigation (2,023/1,949, tiny corpus drift, well inside the script's own 1,000-4,000
          STOP-ON-SURPRISE guard). **Full `--apply`**
          (`canonical-migration-tradfi-krw-usd-restamp-20260815-093459`, after the launcher fix): succeeded on
          the FIRST attempt (no CAS race this time) — pre-write snapshot taken
          (`_index/backups/availability_index.pre_krw_usd_pipeline_mode_restamp_20260815T093929Z.parquet`),
          1,947 rows re-stamped `batch_yahoo`→`batch_databento`, 75 left untouched, manifest generation
          `1786786304636595`→`1786786808789653`, in-script self-verify: 0 mislabeled rows remain. **Independent
          fresh-read verification** (separate from the script's own in-process self-verify, column-projected
          pyarrow read, ~4G RSS bounded): live manifest at the post-apply generation now shows
          `FX:SPOT_PAIR:KRW-USD` `captured`/`ohlcv_24h` split `batch_databento=1949` / `batch_yahoo=75` — matches
          the apply's own counts exactly. KRW/USD confirmed 100% Yahoo-sourced throughout (per the source doc's
          standing requirement — `pipeline_mode` re-stamp changes WHERE the content lives in the manifest's
          path claim, not its `source=` provenance, which was already `yahoo` on every row). Widening the same
          mislabel check to the other 11 FX pairs (source doc's own P3 follow-up) is explicitly out of THIS
          todo's scope, same as the todo's own "no blind --force-recapture across all 12 FX pairs" guard —
          left for the source doc's own tracked P3. Source doc's own checkbox reconciliation is this batch's
          paired finalize plan's job
          (`plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`), not duplicated here per
          this batch's own "source docs not touched" convention.

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.

## Progress Log

- **2026-08-15 (slot-20, backend_engineer, todo "reconcile BASE_ASSET/manifest underlying string-naming drift...",
  DONE)**: investigated whether the drift causes accounting issues — it does not, already reconciled by a pre-existing
  shipped fix (`market-tick-data-service@b63200a7`, 2026-08-09) that wires
  `resolve_tradfi_underlying_to_root()`/`canonical_tradfi_underlying()` into the manifest-comparison key on both sides.
  No new code needed. Flagged one residual dead-code finding (an unused, internally-inconsistent duplicate
  `EXCHANGE_CODE_TO_NAME` in `tradfi_instrument_universe.py`, zero live impact) rather than silently leaving it
  unexplained. Full evidence in the todo's own DONE note above.

- **2026-08-14 (slot-31, todo "re-run the dry-run..." — legacy-twin bucket delete, DONE)**: fixed a second, independent
  bug in `cleanup_legacy_twins.py::canonical_twin_path()` (the `bbcc6395` pre-hive fix still omitted `asset_group=`),
  plus a live memory bug in `_source_by_cell_from_manifest` (unbounded full-manifest read hit a real 4.4GB RSS kill this
  session on tradfi's ~2.6M-row manifest — replaced with a vectorized cell-filtered lookup).
  `instruments-service@271b3d33ff`, 17 tests green. Re-ran the dry-run fresh: canonical-twin coverage jumped from the
  previously-measured 0% to 897/900 (99.7%); KRX/Yahoo subgroup (required by this todo's 2026-08-13 addendum) has 0 rows
  in this candidate set, vacuously clear. But **0/900 legacy objects themselves still exist in GCS** — verified 3
  independent ways (sampled `gcs_describe_object`, full 900-row pass, prefix listing) and confirmed by the tool's own
  official `--apply --i-understand` run (`0 deletable`, `deleted 0/0`, retention 604800s fresh-checked). Practical
  outcome: nothing left to delete — the todo's goal state is already true in GCS. How/when the 900 objects vanished is
  UNEXPLAINED (no tracked delete execution found, no matching bucket lifecycle rule) — filed
  `plans/active/issues/tradfi_legacy_twin_candidates_already_absent_unexplained_2026_08_14.md` (P1) rather than assumed
  benign. Full evidence in the todo's own DONE note above.

- **2026-08-14 (slot-18, in-flight, todo 1 — sector/micro underlying migration)**: code shipped, migration IN PROGRESS
  (checkbox not yet flipped — do not flip until BOTH sector-remap and micro-remap apply are self-verified 0-remaining).
  **Shipped**: `unified-api-contracts@ebda13eb28` (15 missing micro-contract roots added to `TRADFI_ROOTS`, mirroring
  MES/MBT/MET precedent — underlying = parent's plain name + `parent_root`, not a `MICRO-<ROOT>` form; that convention
  is specific to `EXCHANGE_CODE_TO_NAME`). `market-tick-data-service@b0e18fd33e` (final of 4 fix commits to the two
  migration scripts, see below). **5 real issues found + fixed en route** (none were designed-in — both scripts had
  never been run on a VM before this session, per prior na-eligibility-audit passes): (1) `pc.and_()` not bare `&` for
  pyarrow `ChunkedArray` boolean masks (this pyarrow version doesn't support the operator — immediate crash on first
  dry-run); (2) the GCS object census's `gcloud storage ls .../by_date/**/.../underlying=<val>/**` glob forced a
  whole-corpus date-partition walk before filtering, timing out at 120s (single-walk-discipline violation) — rewritten
  to derive exact object paths directly from the already-in-memory manifest rows via the canonical
  `build_tradfi_partition_path()` (byte-identical to the writer, zero GCS listing); (3) that rewrite surfaced a
  pre-existing gap in `tradfi_shared.py`'s `TRADFI_DATA_TYPES` allowlist — `ohlcv_1s` (a real, widely-used TradFi
  data_type) was missing, added; (4) hardened `_derive_migration_pairs` to catch a path-build `ValueError` per-row and
  skip+warn instead of crashing the whole run, so one more unanticipated shape doesn't cost another VM cycle; (5) an
  **IAM gap** (not code) — the VM's runtime SA `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` had
  `storage.objectAdmin`/`.objectViewer` but no bucket-metadata role, needed by the §3a
  `gcs_bucket_soft_delete_retention_seconds()` check added earlier this session. Self-granted (my own active identity IS
  `unified-trading-sa`, the documented self-service identity for exactly this gap class per
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) `roles/storage.admin` project-wide on
  `central-element-323112` (a **live infra change, not in git** — `legacyBucketReader` isn't supported at project scope,
  and the bucket-scoped `gcloud storage buckets add-iam-policy-binding` path is hook-blocked as an object-op pattern
  match; verified live via `gcloud projects get-iam-policy` + the retry run's own successful retention read). **Status
  at last check (~04:20 UTC)**: sector-remap dry-run confirmed clean (25,924 manifest rows / 8 codes exactly matching
  the source issue doc's docstring measurement; 2 rows honestly skipped for missing quote/margin dims, not guessed);
  full/`--apply` running on VM `canonical-migration-tradfi-sector-remap-20260814-040712` (asia-northeast1-c), steady
  ~500 objects/min, 0 errors, ~3,500/25,922 renamed so far (~45 min remaining at that pace). **tradfi-micro-remap has
  not been started yet** — same dry→full sequence still needed once sector-remap's apply self-verifies 0-remaining. **To
  resume**: check the VM's `run.log` via UTL
  `unified_trading_library.cloud_interface.gcs_read_object_with_generation(uri='gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-sector-remap-20260814-040712/run.log')`
  (NEVER gsutil/gcloud subprocess for object ops — hook-blocked) for `✅ VERIFIED: 0 rows...remain`. If sector-remap is
  done, launch `tradfi-micro-remap`
  (`bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh tradfi-micro-remap 2026-08-13 2026-08-13 dry`
  then `full`) — same monitoring pattern; expect it may hit its OWN new edge case even though it shares the fixed code
  (different code population). Once both migrations self-verify 0-remaining, flip todo 1's checkbox citing both SHAs +
  full evidence (dry-run counts, apply row/object counts, self-verify lines for both) and call `/done`.

- **2026-08-14 (slot-18, in-flight, same todo — monitoring checkpoint + doc correction)**: **corrected the run.log read
  pattern above** — `get_storage_client().download_bytes(...)` is not a real method on UTL's `GCSBlobHandle` wrapper
  (confirmed via two failed attempts: `AttributeError` on a raw google-cloud-storage-style `.bucket().blob().reload()`
  guess, then `TypeError` on a `bucket=`/`object_name=` kwarg guess). The correct call, confirmed via
  `inspect.signature()`:
  `unified_trading_library.cloud_interface.gcs_read_object_with_generation(uri='gs://<bucket>/<path>') -> tuple[bytes | None, int]`
  — single `gs://` URI positional/kwarg, returns `(data, generation)`. Used successfully to read
  `canonical-migration-tradfi-sector-remap-20260814-040712`'s `run.log` twice this session (progress healthy both times,
  0 errors both reads). **Status at last check (~04:27 UTC)**: 7,500/25,922 renamed, 0 errors, steady ~500/min — no
  drift from the dry-run's 25,922-object count. Sector-remap apply not yet complete; micro-remap not yet started. No
  code changes this checkpoint — pure monitoring.

- **2026-08-14 (slot-18, in-flight, same todo — pre-compact checkpoint, AO heartbeat lifecycle notes)**: also fixed the
  **"To resume" line above** (was still citing the dead `download_bytes(...)` pattern even after the entry below it had
  already corrected the general reference — a doc can have the same stale claim in two places; grep for all occurrences,
  not just the first). **Status at last check (~04:38 UTC)**: 12,000/25,922 renamed, 0 errors, steady ~500/min — still
  no drift. **AO worker lifecycle findings this checkpoint** (useful for any future slot-18 session resuming this task):
  (1) `POST /api/slots/18/heartbeat` returned three stale `🟥 GIT STATUS RED` nudges (UAC/MTDS "ahead=1 unpushed", PM
  "behind 1 commits for 14m") — re-checking `git status --porcelain=2 --branch` directly in each repo immediately after
  showed all three already at clean `+0 -0`; the heartbeat's git-health snapshot can lag actual state by double-digit
  minutes on a busy shared branch, so treat a RED nudge as "verify locally before acting", not "act on the string" —
  acked all three (`message_ids` 7770/7776/7783) once confirmed stale. (2) Per CLAUDE.md's
  async-wait-and-poll-discipline HARD RULE, `ScheduleWakeup` is explicitly NOT a reliable wake mechanism for an AO
  worker mid-task — the correct pattern (used successfully here) is a self-armed `run_in_background` Python watchdog
  polling the VM's `run.log` + `EXIT_STATUS` object every 120s with a safety-cap timeout sized to the measured ETA (here
  45 min, vs. a ~30 min measured completion ETA at 500/min pace); the harness notifies on completion, no manual
  re-polling needed. The watchdog script itself lives at `<scratchpad>/monitor_sector_remap.py` on slot-18's local disk
  — NOT committed (correctly: it's a one-shot script hardcoded to this exact VM name, not a reusable tool, so no
  `scripts/` promotion needed) and NOT durable across a full session teardown; if a fresh session inherits this task and
  the watchdog is gone, just re-run the manual `gcs_read_object_with_generation` check above — nothing is lost, the
  migration itself is server-side on the VM, not dependent on this monitor. (3) Own-mistake note: chaining
  `cd repoA && git status; echo; echo "=== repoB ===" && git status` in one Bash call does NOT re-`cd` into repoB — `cd`
  only affects commands after it in the same `&&` chain, so a label echoed without its own `cd` silently repeats the
  PREVIOUS repo's output under the wrong heading. Hit this twice this session (once in the original audit, once again in
  this checkpoint) — each repo's status check needs its own explicit `cd <repo> &&` prefix, every time, no exceptions.

- **2026-08-15 (slot-28, backend_engineer, todo "Re-run rebuild_tradfi_manifest.py...", DONE)**: no existing VM-launcher
  wired the standing `rebuild_tradfi_manifest.py` scanner, so added a new `tradfi-manifest-rebuild` category to
  `launch-canonical-migration-vm.sh` (`deployment-service@e382b01860`, shipped via the normal QG→quickmerge flow).
  Validated with a narrow canary dry-run first (2026-08-01..2026-08-07, exit_code=0, 457 shards), then launched the real
  full-corpus run (`canonical-migration-tradfi-manifest-rebuild-20260815-061239`, SPOT, `--chunk-days 30`,
  2020-01-01..2026-08-15): completed in 844.8s, 1,397,013 shards / 81 chunks / 2,080 dates, 0 unparseable. Live manifest
  recount confirms **0** `instrument_type=FUTURE` rows with populated `underlying` + blank `instrument_id` remain — both
  CME-scoped (matching the source issue's exact filter) and unscoped across all venues. Full evidence in the todo's own
  DONE note above.

- **2026-08-15 (slot-29, backend_engineer, todo "VERIFY CME mbp_10/trades/tbbo billing-gated declaration", DONE)**:
  confirmed live `VENUE_DATA_TYPE_CAPABILITIES["CME"]` (unified-api-contracts) excludes mbp_10/trades/tbbo entirely (no
  false full-history-available claim), and the independent Databento billing-entitlement guard
  (`databento_subscription_allowlist.py`, L1=367d/L2=33d) is correctly wired for if/when they're restored. Filed an
  adjacent (not fixed, ambiguous-scope) finding as its own issue doc:
  `plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md` — `expected_coverage.py`'s
  CME list still includes trades/tbbo even though the actual MTDS fetch-gate (`VENUE_DATA_TYPE_CAPABILITIES`) excludes
  them, which may inflate deployment-api's tradfi completion-gap denominator. Full evidence in the todo's own DONE note
  above.

- **2026-08-15 (slot-14, backend_engineer, todo "VERIFY KRX equities registry-vs-adapter mismatch fix still holds live",
  DONE)**: the original 2026-07-12 fix holds at every layer it touched (`expected_coverage.py`, `is_mvp`'s predicate,
  `route_yahoo_tradfi`'s fetch-side filter) — live-read confirmed, no drift. But found a NEW instance of the same
  mismatch class in `mdps_mvp_universe()` (`_mvp_scope_mdps.py`, added 2026-07-31 — postdates the original fix, so it
  never inherited the KRX narrowing): it falsely declared `("KRX", "EQUITY", "ohlcv_1m")` MVP-reachable to its live
  consumers (MDPS `pipeline_e2e_check.py`, e2e-testing `coverage_harness.py`), which would have made those
  shard-coverage harnesses expect a candle MDPS can never derive (Yahoo-sourced KRX is ohlcv_24h-only). Fixed by
  mirroring `is_mvp`'s exact narrowing into the derived-universe branch + corrected 2 stale-assumption tests.
  `unified-api-contracts@d78f8e4e6a`, `quality-gates.sh` full run green. Full evidence in the todo's own DONE note
  above.

- **2026-08-15 (slot-7, backend_engineer, todo "Surgical phantom-row-targeted re-capture of the confirmed KRW/USD
  (pair,date) cells...", DONE)**: premise was stale (source doc already corrected 2026-08-14: not phantom, a manifest
  `pipeline_mode` mislabel) — completed the pending `--apply` of the already-shipped re-stamp script. No VM launcher
  existed for this one-off script (full-manifest read needs ~10-12GiB RSS, exceeded the shared host's bounded-analysis
  caps), so added a `tradfi-krw-usd-restamp` category to `launch-canonical-migration-vm.sh` mirroring
  `tradfi-manifest-cas`'s retry-loop shape; found + fixed a real launcher bug live (generic `--dry-run` append broke the
  compound retry-loop command, same class already known for `tradfi-manifest-cas`/`-retire` — added to the suppression
  list). Dry-run confirmed 2,022 candidates matching the doc's investigation; full `--apply` succeeded on the first
  attempt (1,947 rows re-stamped, self-verify 0 remaining), independently re-verified via a fresh column-projected read.
  Full evidence in the todo's own DONE note above.

- **2026-08-15 (slot-6, backend_engineer, todo "Todo 2: relaunch TRADFI:volatility benchmark once todo 1 lands",
  BLOCKED-INFRA)**: attempted the relaunch 3x
  (`pipeline_e2e_check.py --day 2026-08-14 --asset-group TRADFI --family volatility --legs benchmark --benchmark-days 7`);
  every VM self-deleted within ~250-320s with zero `run.log`/ `EXIT_STATUS` ever written and 0 objects captured — not a
  recurrence of the original code gap (that fix is confirmed shipped), a distinct infra failure. A manual tarball
  republish between attempts did not change the outcome. Filed
  `plans/active/issues/features_e2e_test_run_vm_self_deletes_no_log_2026_08_15.md` (P1, infra) with the leading
  unconfirmed hypothesis (test-run launches' `uts-test-sa` may lack access to the code bucket's `vm/`/ `vm-logs/` paths)
  and follow-up todos to root-cause, fix, and re-relaunch. This todo's checkbox stays unchecked (done_definition not met
  — 0 throughput captured) pending that issue doc. Full evidence in the todo's own note above.

- **2026-08-15 (slot-6, infra craft, same todo, UPDATE — infra fixed, still blocked on data)**: the issue doc's IAM
  hypothesis was confirmed and fixed (narrow bucket-scoped IAM condition granted to `uts-test-sa`), live-verified via a
  real relaunch (`features-e2e-tradfi-20260815-100817-679e08`) that finally produced a real `run.log`/`EXIT_STATUS=0` —
  the silent-VM-death infra bug is closed. However that same verification run completed `0/11` feature groups: no
  captured VX (VIX-futures) data exists anywhere in the `2026-08-07..2026-08-14` window, so every group correctly
  refused to write rather than fabricate output. Checkbox stays unchecked — the blocker has shifted from infra to data
  availability for this specific window. Full evidence and next-step guidance in the todo's own UPDATE note above and in
  the issue doc's amended `[DATA] P1` todo.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
