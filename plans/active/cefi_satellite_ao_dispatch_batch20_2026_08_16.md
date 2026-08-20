---
doc_type: plan
title: cefi satellite AO dispatch batch 20 — 2026-08-16
summary: >-
  Extraction batch from the cefi tranche's 2026-08-16 /na-eligibility-audit run — originally 18 conflict-cleared,
  bounded/deterministic todos pulled from 8 source docs; items 5 and 7 were dropped during authoring (a concurrent
  worker independently shipped both fixes — `deployment-service@6f2f8e02bf` — while this batch was being drafted,
  discovered via a genuine rebase conflict on `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` and resolved
  by taking the concurrent worker's DONE content; item numbering below is left with gaps at 5/7 rather than
  renumbering, to avoid re-touching every source doc's citation). **16 todos live**, from 8 source docs
  (RECLASSIFY_SPLIT bounded items; each source doc's remaining open items stay assigned_vm: NA and are unaffected).
  Each todo cites its exact source doc; the source docs
  themselves are NOT touched by this batch's own dispatch (checkbox reconciliation back into each source doc happens
  in the paired finalize plan) — this run DID flip the extracted checkbox in each source doc at authoring time to
  cite this batch, matching the na-eligibility-audit skill's Phase 3 "per-todo split" extraction mechanics (a
  stronger guarantee than waiting for the finalize plan to do it). Conflict-checked against every existing active
  batch/finalize plan for this tranche via the shared four-surface protocol before drafting — no item here duplicates
  ground an existing dispatched todo already claims. One additional RECLASSIFY_SPLIT candidate
  (`data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`) was found in CONFLICT against `batch19` (10 of its 12
  proposed items are already-shipped duplicates with stale checkboxes) and is deliberately NOT included here — see
  that doc's own Progress Log for the stale-checkbox fix applied instead.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, satellite-batch, na-eligibility-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /plans/active/issues/cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md,
    /plans/active/issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_003_manifest_recon_cefi_silent_death_unsliced_manifest_read_2026_08_15.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md,
    /plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md,
    /plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-19"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3.6
estimate_calibrated_ai_days: 1.44
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
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-16 cefi-tranche /na-eligibility-audit run (autonomous, dispatch agt-e26aea). status:
  active from the start (not draft) per the skill's 2026-08-10 no-double-gate ruling — na-eligibility-audit's own
  RECLASSIFY verdict + conflict-check IS the authorization to dispatch (unlike /ag-closeout-audit's batches, which
  stay draft pending separate operator approval).
---

# cefi satellite AO dispatch batch 20 — 2026-08-16

> Every todo below was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call)
> by the 2026-08-16 cefi-tranche na-eligibility-audit run and conflict-checked against every existing active
> batch/finalize plan in this tranche (plus `cefi_consolidated_closeout_2026_07_18.md` and prior-run satellite
> drafts) before being drafted here. Each source doc's OWN checkbox for the extracted item was flipped at authoring
> time citing this batch; the source doc's remaining (non-extracted) items stay `assigned_vm: NA`.

## Todos

- [ ] [SCRIPT] P3. Exempt `aggregate_from_15s_efficient` from a false-positive "adapter density bug" NaN warning
      (market-data-processing-service, `fast_candle_aggregation.py:333-359`) that fires on every liquidations shard
      with any zero-liquidation window (659,791+ occurrences) — confirmed false positive (liquidations is inherently
      sparse/event-driven; a null open/close on a zero-liquidation window is correct honest-absence, not a density
      bug). Give it the same `_honest_absence_frame` exemption `derivative_ticker` already has, keyed on
      `liquidation_count`/`liquidation_notional_usd` presence (or widen the existing check). Source:
      `plans/active/issues/cefi_inverse_contract_size_wrong_and_missing_2026_08_12.md`. Done-when: the WARNING no
      longer fires on a zero-liquidation window in a re-run, and quality-gates.sh stays green.
- [x] ✅ [BACKEND] P2. **VERIFY-ONLY — DONE 2026-08-17 (slot-12, backend_engineer)**. Pulled + read `run.log` for
      `mdps-cefi-2019-20260810-043116` via `_gcs_tail.read_terminal_exit_code`/`read_text_tail` (SDK, tail-capped —
      `read_terminal_exit_code` moved from `_gcs.py` to `_gcs_tail.py` 2026-08-15, run.log blobs measured up to
      12.2GB). `exit_code=1` confirmed. **Root cause: the SAME bug**
      `plans/archive/2026_08/mdps_cefi_chain_bundle_delay_features_timestamp_float_compare_2026_08_12.md` already
      diagnosed + fixed (`market-data-processing-service@cc65f076ae`) — the run.log's exact 2
      `Handler returned non-zero exit code` lines (`cefi/liquidations/PERPETUAL: ALL FAILED (2/2)`,
      `cefi/trades/FUTURE: ALL FAILED (4/4)`) are both the `'>' not supported between instances of 'Timestamp' and
      'float'` TypeError (8 occurrences in the log) on the shard's final date `2019-12-31`. This VM (launched
      2026-08-10 04:31, pre-fix) is a 3rd confirmed pre-fix instance within the archived doc's own
      blast-radius-audited 19-VM set (same `mdps-cefi-2019-*` / 2026-08-10..11 window). No other error class in this
      VM's log (`SCHEMA_VALIDATION_FAILED` ×10, `MalformedTickFieldError` ×1627 — pre-existing DERIBIT-options
      honest-drop handling, `recovery=fail_fast`) caused a handler exit. **The archived fix already covers this — no
      new code needed.** Adjacent finding (relaunch-chain status is stale in the source issue doc) folded into that
      doc's own Progress Log rather than this todo's scope. Source:
      `plans/active/issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-17 (slot-16, backend_engineer)** — Threaded a slim `columns=` list through
      `reconcile_phantom_manifest_rows_all.py`'s `merge_canonical_with_outstanding_shards(...)` call (line 1719, now
      gated on `args.unphantom_only` and none of the `--report-*` dry-run flags), gated strictly to
      `--unphantom-only` mode. **`instruments-service@c23907c454`.**

      Added `_UNPHANTOM_ONLY_COLUMNS` (module-level, right above `_row_identity_cols`), built from
      `_ROW_IDENTITY_BASE_COLS` + `_ROW_IDENTITY_OPTIONAL_COLS` (the same identity-key set
      `_relocate_indices_by_identity` reads for the staleness-guard relocation) plus `capture_status`/`error_reason`
      (the reverse-revalidation mask) and `pipeline_mode` (the sports cross-bucket audit path) — enumerated by tracing
      every `df` column access reachable from the `--unphantom-only` branch (mask build → `_audit_generic`/
      `_audit_sports` → `_relocate_indices_by_identity`; the `venue`/`data_type` scope filters and the
      `up_df.groupby(["data_type"])` distribution are covered by the same set). The gate also excludes the 4
      `--report-*` dry-run passes (chain-level-defi / legacy-venue-defi / pyth-oracle / lending-indices
      ghost-failures) since those read the SAME initial `df` before the `unphantom_only` branch and need the full
      schema — confirmed by reading each report function's column accesses. The staleness-guard re-read immediately
      before write-back (line ~1886, now ~1897) and the full (non-`--unphantom-only`) mode are untouched — both still
      pass `columns=None` (full schema), per the todo's explicit "do NOT slim the full write-back mode" instruction.

      Verified: `quality-gates.sh` green (Pass-1 + Pass-2 sentinel), `basedpyright` clean. **Not verified this
      session**: a live re-run against the DP-VM-003 cefi shard proving identical unphantom output at lower memory —
      that requires launching a VM-scale reconciliation run (`launch-manifest-recon-all-vm.sh cefi
      UNPHANTOM_ONLY=true`), which is beyond this todo's scoped backend_engineer craft (VM launch/verification is
      infra craft) and wasn't launched this session. The column set was derived by exhaustively tracing every `df`
      access on the `--unphantom-only` code path (not guessed), so functional-equivalence confidence is high, but the
      at-scale memory-reduction + output-parity proof is still open — flagged in this doc's own Progress Log rather
      than left unstated. Source:
      `plans/active/issues/dp_vm_003_manifest_recon_cefi_silent_death_unsliced_manifest_read_2026_08_15.md` (that
      doc's own todo for this item left un-flipped here — this batch plan is the live checkbox per its frontmatter;
      the source doc's checkbox was already flipped to EXTRACTED at authoring time).
- [x] ✅ [CODE] P1. **DONE 2026-08-17 (slot-18, backend_engineer)** — Backfill historical CeFi/TradFi manifest rows
      with the corrected per-`instrument_type` split. Source:
      `plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (line 516).
      **`instruments-service@5efb94424e`.**

      **Live re-verify found the todo's premise stale before writing any fix.** DERIBIT (cefi) and CME
      (tradfi) — the two venues this doc's own live-evidence section named — were BOTH already fully split
      by real `instrument_type` for every pre-2026-07-07 date (DERIBIT: 2019-03-30..2026-07-06,
      OPTION/FUTURE/PERPETUAL/COMBO/SPOT_PAIR, genuine multi-row-per-date structure; CME: 0 captured+blank
      rows), presumably via prior forward-work re-touching those dates. A corpus-wide sweep of the FULL
      cefi (85,214 rows) + tradfi (27,579 rows) manifests for `capture_status==captured AND
      instrument_type=='' AND date<2026-07-07` found exactly **1 residual row across both asset groups**:
      `BITFINEX-SPOT`, `2023-12-16`, `instrument_count=284` — every other BITFINEX-SPOT row (2,697 of
      them) correctly carries `SPOT_PAIR`, confirming a single-type venue with one never-stamped row, not
      a genuine multi-type blend.

      Wrote `scripts/backfill_cefi_tradfi_instrument_type_split_2026_08_16.py` (safe single-type-venue
      inference: backfills a blank row only when every OTHER row for that venue carries exactly one
      distinct non-blank `instrument_type`; a genuinely ambiguous multi-type venue would be left untouched
      + reported loudly — none found live). Dry-run confirmed the 1-row scope; `--apply --confirm` shipped
      it with the standard captured-count safety gate (56,732 before/after, unchanged) and a post-run
      re-read verification. **Done-when satisfied**: a fresh manifest read over both asset groups shows 0
      blank captured rows for `date < 2026-07-07` — the corrected per-instrument_type split, not
      blended/blank rows.
- [x] ✅ [BACKEND] P2. **DONE 2026-08-17 (slot-8, backend_engineer) — REFUTED.** Re-derived the original "four
      preemptions" narrative directly from the raw `uts-prod-dp-exit-code-monitor` Cloud Run Job source log text
      (`gcloud logging read` on `resource.type="cloud_run_job" resource.labels.job_name="uts-prod-dp-exit-code-monitor"`,
      2026-08-15T13:55-14:35Z, `project=central-element-323112`). Raw log text names the exact terminated-VM instances
      (run-ts included, not just the year): `mdps-cefi-2019-20260815-050114` (dispatch logged 14:02:43Z),
      `mdps-cefi-2020-20260815-041556` (14:09:33Z), `mdps-cefi-2021-20260815-020059` (14:15:58Z),
      `mdps-cefi-2022-20260815-050114` (14:22:23Z), plus a 5th in the same window,
      `mdps-cefi-2022-20260815-050859` (14:28:50Z). **These run-ts values are DIFFERENT instances from the ones the
      source doc's own "Correlation" section cited as the watchdog's kill victims in this window**
      (`mdps-cefi-{2019,2020,2021,2022}-20260815-120236`/`120941`, all run-ts `12xxxx` — launched around noon, vs. the
      actually-preempted VMs' `05xxxx`/`04xxxx`/`02xxxx` run-ts, launched pre-dawn) — the doc's "VM-identity match is
      exact" claim does not hold once the raw log is read for full VM names, not just year. Cross-checked all 5 exact
      VM names against three independent Cloud Logging sources spanning the full day
      (2026-08-15T00:00-23:59Z): (1) GCE audit log `protoPayload.methodName="compute.instances.preempted"` — **HIT for
      all 5**, each with a genuine GCE-system-issued preemption operation HOURS before the monitor's own dispatch log
      (e.g. `mdps-cefi-2019-20260815-050114` preempted per audit log at 05:28:31Z, monitor dispatched relaunch at
      14:02:43Z — consistent with relaunch-budget/backoff lag, not a same-moment coincidence); (2) watchdog's own
      `textPayload:"reason=zombie_finished_not_shutdown"` kill-log — **ZERO hits** for any of the 5 exact VM names,
      full day; (3) GCE audit log `v1.compute.instances.delete` by `uts-prd-sa` — **ZERO hits** for any of the 5 exact
      VM names, full day. Also traced the code path generating the "preempted (SPOT reclaim)" log line
      (`deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py` → `_classify.py` →
      `_compute_ops.make_preemption_op_checker`): the `is_preempted` signal is sourced either from an in-guest
      shutdown-script GCS marker gated on the GCE metadata server's `instance/preempted` value
      (`scripts/vm/lib/launcher_common.sh:825-827`, `[[ "$PREEMPTED" == "true" ]] || exit 0`) or the Operations-API
      `was_instance_preempted` fallback querying for a `compute.instances.preempted` operation specifically — both
      are GCE-system-authoritative signals a `compute.instances.delete` call (what the watchdog issues) structurally
      cannot produce. **Verdict: REFUTED.** The four (five) specific dispatch events this doc's original text cited
      as evidence for the explosion were genuine GCE SPOT reclaims, confirmed via a real
      `compute.instances.preempted` system operation for each exact VM, not the watchdog false-kill bug — the
      doc's own "likely the actual trigger" correlation theory does not survive re-derivation against the raw
      per-VM Cloud Logging text. Bug 1/Bug 2's fixes remain necessary regardless (unaffected by this verdict — see
      source doc). Full evidence + exact `gcloud logging read` filters in the source doc's own Progress Log.
      Source: `plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-18 (slot-17, backend_engineer)** — Mirrored execution-service's
      `LiveExecutionHandler._load_bybit_trade_credentials` fallback into `validate_api_keys_for_venues`
      (`unified_trading_library/startup_validation.py`). Added module-level `_SCOPED_SECRET_UNSCOPED_FALLBACK` (scoped
      secret name → unscoped fallback secret name, currently just `"bybit-trade-api-key" -> "bybit-api-key"`); the
      per-venue secret-fetch loop now retries the unscoped name whenever the scoped one is absent/blank before
      recording it as missing, so `get_required_secrets`'s deterministic scoped-name mapping (UAC's
      `DATA_SOURCE_TO_SECRET["bybit"] = "bybit-trade-api-key"`) is left untouched — the fallback lives in the
      runtime lookup, same layering execution-service already uses (config maps the scoped name, the handler resolves
      the fallback). **`unified-trading-library@e7c2baee5f`.** 7 new unit tests
      (`tests/unit/test_startup_validation_api_keys.py`): scoped-present-used-directly, scoped-absent-falls-back,
      scoped-blank-falls-back, neither-present-raises (CLOUD_MOCK_MODE pinned false via monkeypatch — ambient QG env
      defaults it true, which silently degrades the raise to a warning), scoped-preferred-over-unscoped, and two
      "other venues unaffected" tests (Aster, no fallback entry, still hard-fails on a missing key) confirming the
      fallback is scoped to Bybit only. `quality-gates.sh` green (sentinel=e7c2baee5fab6beb3019d6df91a2454b71d06fe0);
      one unrelated flaky test (`test_harness_auto_resolves_params_from_specs`, a 300s-timeout-marked synthetic-harness
      benchmark) failed on the first QG run under shared-host contention and passed clean on immediate re-run —
      confirmed unrelated to this change (no overlap with `startup_validation.py` or the new test file). Source:
      `plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`. Done-when satisfied: a capture
      run with only the unscoped `bybit-api-key` present now resolves via the fallback instead of raising
      `StartupValidationError`.
- [ ] [SCRIPT] P2. Re-run the corpus-wide GCS VM-log grep (Script 1, cefi content-migration summary) across all 44
      cefi-content-migration shards now that shard 24 landed `EXIT_STATUS=0` 2026-08-15; settle 44/44, flip both
      target docs' remaining todos, and delete `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` per its
      own `Delete-when` marker. Source: `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`.
      Done-when: 44/44 confirmed, target docs' todos flipped with evidence, script deleted.
- [ ] [SCRIPT] P2. Live-check 2 confirmed-gone VMs (`mdps-backfill-cefi-20260808-095136`,
      `pipeline-e2e-check-mtds-20260815-172227-4ffa29`) whose gating docs are 5+ days stale — read the named GCS
      report path via the sanctioned SDK to confirm outcome and flip the 3 affected docs' todos. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: all 3 affected docs' todos are
      flipped with a cited GCS report path.
- [ ] [DOC] P2. Proactively split `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` (confirmed exactly
      1000 lines via `wc -l`, zero headroom under the hard line-cap) before its actively-accumulating 9th relaunch
      attempt (launched 2026-08-15) appends past the gate. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: the doc is under the 1000-line
      hard cap with a child doc holding the split-out content and `depends_on`/`related` wired correctly.
- [ ] [SCRIPT] P2. Identify/confirm the NEW 19-VM HYPERLIQUID fleet found running 2026-08-16 that no task in
      `coverage_floor_registries_no_cross_propagation_2026_07_17.md` launched (that doc's sole open todo re-points to
      it) before assuming progress. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: the fleet's origin is confirmed
      (which launcher/dispatch started it) and the source doc's todo is updated accordingly.
- [ ] [DOC] P3. `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` has ≥11 link-TEXT/href mismatches
      (href correct, display text stale) needing a bulk find-replace, and is missing a reference to
      `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: all link text matches its href
      and the missing reference is added.
- [ ] [DOC] P3. `per_venue_scope_key_provisioning_incomplete_2026_07_23.md`'s "Remaining open in this doc: 3"
      summary line (dated 2026-08-09) is stale — a 4th todo added 2026-08-14 was never folded in. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: the summary line reflects the
      true current open-todo count.
- [ ] [DOC] P3. `dp_vm_002_cefi_queue_heavy_binancefutu_streaming_writer_progress_gap_2026_08_14.md` frontmatter
      uses non-standard `estimate_baseline:`/`calibrated_ai_days:` keys instead of the
      `estimate_baseline_ai_days:`/`estimate_calibrated_ai_days:` convention. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: the frontmatter keys match
      `plans/PLAN_FORMAT.md`'s schema.
- [ ] [DOC] P3. `prediction_capture_incident_remediation_2026_07_06.md:114-118` cites 2 `unified-trading-library`
      SHAs that are not ancestors of `origin/live-defi-rollout` (rebase-changed-SHA pattern); content is confirmed
      present — needs the same citation fix the doc's own Phase 6 section already self-applied once today. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: both SHAs resolve as ancestors
      of `origin/live-defi-rollout` via `git merge-base --is-ancestor`.
- [ ] [SCRIPT] P2. `cefi_backfill_per_day_catalogue_reload_2026_07_20.md`'s sole open todo text ("neither
      proper-fix option implemented") is stale — `market-tick-data-service@5d428486` ships a 3rd mechanism closing
      the profiled 98.5%-bottleneck, but not a clean flip (doesn't obviously eliminate the per-day-subprocess
      architecture) — needs a re-profile before deciding fully-closed vs. partially-addressed. Source:
      `plans/active/issues/plan_reconciler_findings_cefi_2026_08_16.md`. Done-when: a fresh profile result decides
      fully-closed vs. partially-addressed, and the source doc's todo is updated accordingly.
- [ ] [CODE] P3. `launch-cefi-sharded-backfill.sh`'s internal `YEARS_OVERRIDE="${YEARS:-}"` (line 681) silently
      stomps a caller-exported `YEARS_OVERRIDE` env var back to empty because the internal working variable and the
      plausible-but-wrong caller-facing name collide. Fix: rename the internal variable (e.g. `_YEARS_SCOPE`), or add
      an explicit guard that errors loudly instead of silently discarding the caller's intent. Source:
      `plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md`.
      Done-when: a caller-exported `YEARS_OVERRIDE` reaches the launcher intact in a re-run, or the loud-error guard
      fires instead of silent discard.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-08-17 (slot-16, backend_engineer)**: Shipped item 3 (`columns=` slim-read for `--unphantom-only`) —
  `instruments-service@c23907c454`, `quality-gates.sh` green. Live at-scale re-verification (VM-launched
  `--unphantom-only` re-run proving identical output at lower memory) still open — infra-craft scope, not launched
  this session; see the checkbox's own note.
- **2026-08-17 (slot-8, backend_engineer)**: Closed item 5 (the "four preemptions" re-derivation) — REFUTED. Raw
  `gcloud logging read` against the Cloud Run Job source log + the GCE audit log resolved the exact 5 VM names the
  monitor logged as preempted in the 14:00-14:30 UTC window, confirmed a real `compute.instances.preempted` GCE
  system operation for every one of them, and confirmed zero watchdog kills / zero `uts-prd-sa` deletes against
  those same 5 exact VM names. See this checkbox's own entry for the full evidence; also appended a correcting note
  to the source doc's "Correlation" section (append-only, doc's own prior content untouched).
- **2026-08-18 (slot-17, backend_engineer)**: Shipped item 8 (Bybit unscoped-key fallback in
  `validate_api_keys_for_venues`) — `unified-trading-library@e7c2baee5f`, `quality-gates.sh` green, 7 new unit tests.
  See the checkbox's own entry for full detail.
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (3 entries) — genuinely code-free dispatch-batch
  coordinator doc (each todo cites its own source doc); the consolidated-closeout hub, the na-eligibility-audit SKILL,
  and the batch-naming/conflict-check codex doc remain the right minimal set.
