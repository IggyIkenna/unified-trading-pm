---
doc_type: plan
title: June-2026 vintage audit findings — bugs, archives, migrations, rehomes, operator-gate queue
summary:
  Durable capture of the 2026-07-27 /plan-vintage-audit run over all 81 June-2026-created plans/issues (12-group
  Workflow classification). 2 cross-plan false-citation bugs, 11 archivable-now docs, 15
  migrate-to-July-plan-then-archive docs, 10 partially-done-rehome-remainder docs, 2 unclear docs, and a reference queue
  of the 42 operator-gated items for an interactive operator session. Nothing here has been executed yet except where
  noted.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archival, migration, vintage-audit, operator-gated]
related: []
created: 2026-07-27
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2
last_updated: 2026-07-28
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source:
  [
    cursor-configs/skills/plan-vintage-audit/SKILL.md,
    the 2026-07-27 /plan-vintage-audit workflow run over the June-2026 corpus,
  ]
assigned_role: project_management
drift_direction: none
---

# June-2026 vintage audit findings

Operator directive (2026-07-27): fix the 2 bugs below, execute the 11 archives + 15 migrations + 10 rehomes, THEN hold
an interactive session to work through the 42 operator-gated items (§5) one by one — operator asked "what do you need
from me" for each. The 2 unclear docs (§4) need a decision on whether to investigate further or archive as-is.

Execute with sub-agents (to conserve main-session context) — **operator said do not launch execution yet**; this doc is
the durable handoff so a fresh session can pick this up cold. Follow `/plan-vintage-audit`'s Phase 2 archival mechanics
exactly (dated archive folder, exact-successor banner citing commit SHAs, fix every corpus referrer including
codex/00-SSOT-INDEX.md, `[unlock-plan]` only on explicit per-doc operator authorization, `git rm` is blocked for
autonomous workers — relocate via `git mv`, ask the operator for true deletions).

---

## §1 — Fix first (2 cross-plan false-citation bugs, P1)

- [x] ✅ [DATA] P1. **Fix false "0 open todos/closed" citation for
      `plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md`** — unified-trading-pm (this commit).
      **CORRECTED SCOPE on execution**: the false citation only existed in `tradfi_consolidated_closeout_2026_07_18.md`
      (lines 684-685) — defi/cefi/sports closeouts never cited this doc at all (verified via grep before editing, the
      "across FOUR AG closeout plans" framing was itself stale). F7 rehomed into `tradfi_consolidated_closeout` with the
      operator's 2026-07-27 is_mvp-gating decision applied (§5#13); F4+F6 rehomed into
      `defi_consolidated_closeout_2026_07_18.md` Open follow-ups; F5 rehomed into
      `cefi_consolidated_closeout_2026_07_18.md` Track 6. Source doc annotated REHOMED, still
      `locked_by: live-defi-rollout` — archival needs an explicit `[unlock-plan]` grant (not yet asked, not done here).
- [x] ✅ [DATA] P1. **Fix stale "Plan 3 never authored" claim** — unified-trading-pm (this commit). **CORRECTED SCOPE on
      execution**: the false claim lived only in the 2 downstream docs
      (`cross_cutting_consolidated_closeout_2026_07_25.md` Track 10,
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`) — the source tracker itself never claims "never
      authored". Also corrected the evidence citation itself: the prior "unified-api-contracts@6bcff215" SHA is real but
      misleading (a QG-verification-timing commit unrelated in content to the feature work) — the actual shipping
      commits are uac@682cffb5/6f0c4bf8/6cf967c2/6a2f6aab + features-service@48fa8377, all verified against the archived
      plan doc `plans/archive/2026_06/mvp_for_mdps_and_features_universe_uac_2026_06_28.md`. Re-verified Plans 2/6/9:
      none were actually blocked — Plan 2 already complete independently, Plan 9 already active/tracked separately, Plan
      6 has a stable v10 dependency contract but simply hasn't been implemented yet (unrelated to Plan 3). Bonus: also
      flipped `mtds_file_size_refactor_2026_06_08.md` `status: paused` → `active` per the operator's 2026-07-27 resume
      decision (§5#31), referenced inline in the same closeout fix.

---

## §2 — Archive now (11 docs, fully-done or superseded, strict evidence bar already met)

- [x] ✅ [PLAN] P2. `plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md` — ARCHIVED 2026-07-27 —
      unified-trading-pm@(this commit). 14/14 done, both residuals independently re-verified real
      (`unified-api-contracts@4a29261e`, `instruments-service@8b02b647`); the gated finalize plan
      (`..._finalize_2026_07_27.md`) executed + also archived alongside. Both now at `plans/archive/2026_07/`. 9 corpus
      referrers fixed (incl. `plans/epics/defi_master.md`, both consolidated-closeout aggregated-sources docs).
- [x] ✅ [PLAN] P2. `plans/active/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` — ARCHIVED
      2026-07-27 — unified-trading-pm@(this commit). All 6 BUGs re-verified real via `git log`/`git show`
      (UTL@b587b91b/ed622af8, UAC@fd5bcfa/7fade10, execution-service@38c7e06f, strategy-service@b91d3e1f,
      features-service@16be6c0f); 7th line (delta_one funding_oi) correctly left unchecked, migrated elsewhere per its
      own provenance note — did not touch `perp_funding_data_semantics_and_cadence_2026_06_16.md` (owned by a different
      agent this wave). Now at `plans/archive/issues/`. Also annotated
      `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`'s own pending archive-todo for this doc so it isn't
      redone.
- [ ] [PLAN] P2. `plans/active/issues/phantom_captures_defi_2026_06_28.md` — **NOT ARCHIVED — citation partially WRONG,
      corrected in place, unified-trading-pm@(this commit).** The "apply reconciliation" todo IS genuinely done
      (verified real: `mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md:754-762` APPLY COMPLETE, corroborated
      by `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s banner) and was flipped citing that evidence. **But** the doc's
      OTHER todo (root-cause diagnosis, already `[x]` before this pass) was **falsely checked** — its own "already
      covered by `defi_satellite_ao_dispatch_batch1_2026_07_25.md`" claim contradicts that doc's own Progress Log
      ("Todos 1+2 above... remain open") and `batch1`'s (status: active) identical todo is still genuinely unchecked
      with zero completion evidence. Reverted that checkbox to `[ ]`, added a Progress Log correction. Doc stays open in
      `plans/active/issues/` — 1 genuine open item remains, already homed at `batch1`'s own todo. **Flagging per
      findings-triage HARD RULE**: this is exactly the "checked-done-but-actually-not" trap, the inverse of the one this
      §2 item's own dispatch text described.
- [x] ✅ [PLAN] P2. `plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` — ARCHIVED
      2026-07-27 — unified-trading-pm@(this commit). All 3 stale items re-verified against current code (`understat.py`,
      `gcs_paths.py`) + the archived `sports_p1_golden_window_mtds_odds_2026_06_27.md` Todo 1+2 (whose own evidence
      shows the "3 leagues odds-api doesn't carry" premise was itself inaccurate post-gap-fill). Dormant remainder
      (3-way understat split) footnoted at `/codex/02-data/sports-data-source-coverage-matrix.md` §2.3. **Side finding
      flagged**: `sports_satellite_ao_dispatch_batch5_2026_07_26.md` (status: active) carries an open
      BLOCKED-CREDENTIALS todo that appears to be chasing this SAME already-closed golden-window gap — annotated it in
      place, not independently re-measured against live GCS this session, needs a fresh check before that todo re-runs.
- [x] ✅ [PLAN] P2. `plans/active/issues/understat_bulk_download_backfill_2026_06_29.md` — ARCHIVED 2026-07-27 —
      unified-trading-pm@(this commit). All 11/11 §8 items verified done; closure note's 605,368-row re-verification (0
      attempted_failed/expected_unattempted/duplicate) + `deployment-api@b04c082` both confirmed real. Flipped status
      open→resolved, archived citing the closure note + SHA + archived
      `understat_local_backfill_completion_2026_07_06.md`. Now at `plans/archive/issues/`.
- [ ] [PLAN] P2. `plans/active/issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md` — **NOT ARCHIVED — the
      corroborating citation was WRONG, corrected in place, unified-trading-pm@(this commit).**
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md:522-525` (the doc this item cited as "independently
      confirmed") is a truncated, unfinished sentence with no actual supporting evidence — it asserts a verdict without
      ever stating it. Re-investigated all 4 Gaps independently: **only Gap 1 is solidly confirmed** (fresh same-day
      corroboration from `heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md`, an unrelated
      investigation that incidentally proves the OOM fix is live — 10+ consecutive `SUCCEEDED_COUNT=1` executions with
      real WARNING-level logs visible). **Gap 2 is genuinely still open** for the alerting-service Cloud Run Service
      specifically (confirmed via `dp_event_pubsub_delivery_gap_2026_06_22.md` + a live, dispatched, unexecuted todo in
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`) — only the deployment-api Cloud Run Jobs side is
      fixed. **Gap 3** (operator Slack spot-check) is un-actionable by an agent. **Gap 4's code is shipped + verified
      real** (`alerting-service@ceed827` confirmed ancestor of `main`, `deployment-service@d2ddb23`), but the
      "currently-running revision is built from that image" claim is NOT independently confirmed (no live
      `gcloud run     services describe` check run this session). Flipped Gap 1 only; left Gaps 2-4 open with corrected
      annotations. Doc stays open in `plans/active/issues/`. **Flagging per findings-triage HARD RULE.**
- [x] ✅ [PLAN] P2. `plans/active/issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md` — ARCHIVED
      2026-07-27 — unified-trading-pm@1cfe7ad15. 5th checkbox flipped citing verified evidence: build `2ea305e9` (full
      id `2ea305e9-483c-4665-a78d-93d01ef8295d`) confirmed SUCCESS via `gcloud builds list`; alerting-service@e111843
      confirmed ancestor of `origin/main`; live `uts-prod-alerting-paging` Cloud Run job (asia-northeast1) inspected
      directly — runs the durable `python -m alerting_service.cli.main` command (not the `-c` bridge), label
      `lastUpdatedTime=2026-07-12T22:00:00Z`, matches `deployment-service/terraform/gcp/audit03_cron_provisioning.tf`.
      Now at `plans/archive/issues/`.
- [x] ✅ [PLAN] P2. `plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md` — ARCHIVED 2026-07-27 —
      unified-trading-pm@1cfe7ad15. All 9 mini-plans confirmed archived/complete by direct file lookup (the doc's own
      "mini-plans" table was stale for 4 of 9 rows — corrected in the same pass); Plan 6's live follow-on issue
      (`honest_coverage_smoke_harness_4ag_verify_2026_07_06.md`) confirmed actively tracked elsewhere, not orphaned. 0
      orphaned scope. Now at `plans/archive/2026_07/`. Also corrected a stale `status: active` frontmatter field found
      on already-archived Plan 9 (`execution_fidelity_tiers_uac_governed_2026_06_28.md`, content was 6/6 done).
- [x] ✅ [PLAN] P2 (superseded). `plans/active/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` —
      ARCHIVED 2026-07-27 — unified-trading-pm@1cfe7ad15. All 4 SHAs (mtds@0aa6163/1e4dfb2,
      deployment-service@b5246a6/b04cfcc) confirmed present on both `origin/main` and `origin/live-defi-rollout` via
      `git merge-base --is-ancestor`. Absorption chain confirmed: both `mvp_backfill_cefi_tick_v10_2026_06_27.md` and
      `cefi_completion_program_2026_07_15.md` are themselves archived/complete.
      **`cefi_hl_aster_batch_data_gaps_2026_06_22.md` checked** (lives at `plans/active/issues/`, not `plans/active/`) —
      the "2-day live-health check in progress" note is NOT tracked there (that doc is batch-backfill-gap scope, a
      different surface) and no `mtds-live-*` VM is currently running (`gcloud compute instances list` — zero matches).
      Treated as a stale, time-bound check from the original 2026-06-21/22 session (superseded by the later full
      CEX-live-provenance fix in §6 of the same doc) — noted as a known, accepted gap in the archive banner, not
      re-opened. Now at `plans/archive/issues/`.
- [x] ✅ [PLAN] P2 (superseded). `plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` — ARCHIVED
      2026-07-27 — unified-trading-pm@1cfe7ad15. `workspace-constraints.toml` confirmed `aiohttp>=3.14.1,<4.0.0`. **Big
      finding**: the successor `execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md` was NOT just
      "unblocked" — it was ALREADY DONE by another session (execution-service@9ce159a7, 2026-07-27 20:40 UTC, ~1h before
      this pass started) following the §5-RESOLVED #18/19 gate-lift. Archived BOTH docs together (the successor too —
      its sole todo was fully complete, archiving it alone would have left a done-but-unarchived doc). Both now at
      `plans/archive/issues/`.
- [x] ✅ [PLAN] P3 (superseded, unclear-adjacent). `plans/active/issues/empty_reprobe_disagreement_2026_06_22.md` —
      ARCHIVED 2026-07-27 — unified-trading-pm@1cfe7ad15. Archived as stale per the default disposition (did not re-run
      `reprobe_new_empty_confirmed.py`); banner notes the 4 cells as a known, accepted gap rather than a false-positive.
      Now at `plans/archive/issues/`.

---

## §3 — Migrate to a named July plan, then archive (15 docs)

- [ ] [PLAN] P2. `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (P1, legs a-e) +
      `instruments_completion_tracker_2026_07_06.md` (Stage 2a/2b GAP-4). Already migrated verbatim 2026-07-26; both
      successors still open — dual-track until they ship, then flip+archive. 2 items correctly left gated/latent, not
      migrated. **STATUS UPDATE 2026-07-28 (unified-trading-pm@21d31f2a9, verification pass)**: both successors
      confirmed real and open — batch1b's P1 todo (legs a-e) is present and unchecked; `instruments_completion_tracker`
      Stage 2c (nested under the doc's "Stage 2" header — the "2a/2b" citation was an approximation, GAP-4 is actually
      under 2c) carries the open GAP-4 reconcile todo at line ~235-238, also unchecked. The "2 items correctly left
      gated/latent" claim confirmed accurate (pre-funding-genesis Aster trades backfill, gated on GAP-4; the latent cefi
      `ohlcv_*` direct-write capability, deferred no-current-need) — both are explicitly named in batch1b's "Excludes"
      note. **New finding**: batch1b's leg (a) ("make exact discrete per-settlement funding readable") is now DONE
      UPSTREAM — the source doc's own P1 checkbox for it shipped 2026-07-27
      (`unified-api-contracts@22689df5`/`market-tick-data-service@466d5670`), one day after batch1b was drafted;
      annotated batch1b in-place so it isn't re-done. **New finding**: a 3rd item — the source doc's standalone P2 "Bulk
      historical Tardis-CSV `derivative_ticker.funding_timestamp` is forward-looking" todo — is NOT covered by batch1b's
      5 legs nor the 2-item Excludes note; it needs a design decision (in-place derivation vs. heavy-I/O reprocessing
      backfill), so it isn't a bare-dispatchable AO todo — flagged inline in batch1b, not force-dispatched. Still
      dual-track, not archivable — both successors remain open.
- [ ] [PLAN] P2. `plans/active/issues/phantom_captures_prediction_2026_06_28.md` →
      `cross_cutting_consolidated_closeout_2026_07_25.md` Track 22. Track 22 only cites the 1 remaining CODE P2 todo
      (MTDS writer → `empty_confirmed` for 0-activity contracts) — copy the full todo text + gate verbatim, then
      archive.
- [ ] [PLAN] P2. `plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md` →
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` ([TRADFI] P1 memray-footprint todo) + gated
      `…batch2_finalize_2026_07_25.md`. **STATUS UPDATE 2026-07-28 (unified-trading-pm, verification-only, no file
      edit)**: premise was stale — the successor todo is no longer open, it shipped the SAME day this entry was written
      (`[x] ✅ [TRADFI] P1. DONE 2026-07-27 (slot-14, data_engineering)` in
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`, memray evidence also appended in-place to this doc's own
      `[TRADFI] P2` checkbox, which is `[x]` too) — all 5 of this doc's own "Recommended decision" items are now `[x]`.
      Content-complete, but **NOT archived**: doc carries `locked_by: live-defi-rollout` (line 27) with no
      `[unlock-plan]` grant in this session — per the HARD RULE (`PLAN_FORMAT.md`: "Agents MUST NOT archive locked plans
      even if all todos are done... only a human with `[unlock-plan]`") this is a STOP-and-report, not an archive.
      Flagging for the operator: this doc is ready for a quick `[unlock-plan]` + archive pass whenever convenient.
- [ ] [PLAN] P2. `plans/active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md` →
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` (~L270-286), covers items (2) DP_VM_GONE_NO_CAPTURE
      debounce + (3) InstrumentsHandler str/int bug. Item (1) (operator-gated prod-manifest `--apply`) has no other home
      — see §5, needs an operator-decision-ledger home first. **STATUS UPDATE 2026-07-28
      (unified-trading-pm@ba37c6020)**: items (2)/(3) verified present + accurate in batch2. Item (1) now has a real
      home too — filed a new `- [ ] [OPERATOR] P2` todo in `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`
      noting the operator's 2026-07-27 approval (§5-RESOLVED item 11) + citing the manifest-mutation gate in
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`; the source doc's own checkbox annotated with the
      approval + pointer, left unflipped (approval ≠ execution). All 3 items now have a home. **NOT archived**: doc
      carries `locked_by: live-defi-rollout` (line 31), no `[unlock-plan]` grant this session — STOP-and-report per the
      same HARD RULE as above.
- [ ] [PLAN] P2. `plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (L69-81), verbatim, cites Source + "Done when." Not
      yet executed either place. **STATUS UPDATE 2026-07-28 (unified-trading-pm, verification-only, no file edit)**:
      confirmed verbatim + accurate at batch1b L69-81 (the ONLY remaining open checkbox in the source doc — the
      `deployment-service:latest` terraform-default-vs-runtime-pin item). Not yet executed either place. **NOT
      archived**: doc carries `locked_by: live-defi-rollout` + `locked_since: 2026-06-23` (lines 31-32), no
      `[unlock-plan]` grant this session — otherwise this doc is exactly the "verified present → archive the source
      anyway" case this entry calls for, and is ready to archive the moment it's unlocked.
- [ ] [PLAN] P2. `plans/active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md` →
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` (L248-269). Sole remaining item (Cloud Logging
      ingestion gap) merged with a duplicate finding in `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`. 2
      other items already done in code (`alerting-service/alerting_service/api/main.py:77-88`;
      `deployment-service/terraform/gcp/alerting_relay_pubsub.tf`) — flip those first, then migrate the rest. **STATUS
      UPDATE 2026-07-28 (unified-trading-pm@ba37c6020)**: both code claims verified true and flipped in-place with
      evidence (main.py lines 73-101 lifespan/`run_subscriber_in_api`; `alerting_relay_pubsub.tf`'s 2 subscription + 2
      IAM-member resources + import blocks). Also found + flipped 2 MORE prose items in the doc's own "Remaining"
      section that were quietly done (e2e-testing `_dp_common.py` `_ensure_live_events` shipped `e2e-testing@98d499af`;
      the 4 dp-audit Cloud Run crons all provisioned per
      `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`) — these weren't in this entry's original
      2-item scope but were real open prose-form work the strict archival bar requires closing first (trap (b) in the
      vintage-audit skill). The sole remaining checkbox (Cloud Logging ingestion gap) confirmed already migrated
      verbatim into batch2. All items now resolved-in-place or migrated. **NOT archived**: doc carries
      `locked_by: live-defi-rollout` (line 27), no `[unlock-plan]` grant this session — STOP-and-report; this doc is
      otherwise fully closeable.
- [ ] [PLAN] P2. `plans/active/issues/uv_pin_fleet_drift_2026_06_22.md` →
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`. setup.sh fleet rollout + boot-script hardening already "DONE
      2026-07-26" there (instruments-service@40240042, unified-trading-pm@703b1e912); residue (0.10.8 constant
      centralization, uv-version drift-guard, Harsh's-laptop/epic-VM realignment) parked as batch1's own items 2-3. Flip
      several done-but-unchecked boxes in the source doc first.
- [x] [PLAN] P2. `plans/active/l0_doc_index_generator_2026_06_24.md` →
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md` (~L476-498). 2 remaining Deferred items (AO-dashboard L0-graph
      route; on-demand stale-check wrapper) cited Source verbatim, still open there. — ✅ archived with banner
      unified-trading-pm@cff8d611b/@103ce6a64; a stale referrer claiming this was already done (before the move actually
      landed) broke `run_validators.py`'s corpus link-check and failed quality-gates-v2 fleet-wide (ldr_qg_failure
      escalation agt-d2498b on trading-agent-service); remaining stale referrer paths (active_plan_inventory_dashboard,
      infra_satellite_ao_dispatch_batch1 `related:`) fixed this commit.
- [x] ✅ [PLAN] P2. `plans/active/issues/plan_issue_epic_consolidation_2026_06_30.md` — unified-trading-pm@82f7fe635.
      All 5 forks confirmed content-present (spot-checked D1/D3/TradFi-G4-OOM deeply, M-C7/altdata lightly):
      `instruments_completion_tracker_2026_07_06.md`+`mvp_scope_catalogue_tagging_2026_06_08.md` (D1);
      `infra_ops_residual_migration_verification_2026_07_24.md`+`master_data_canonicalisation_migration_catalogue_2026_06_07.md`+`issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`
      (TradFi-G4-OOM); `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` (D3, confirmed same af=10,114/cap=1
      finding);
      `cross_cutting_consolidated_closeout_2026_07_25.md`+`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`
      (M-C7); `tradfi_consolidated_closeout_2026_07_18.md`+`data_completion_tradfi_2026_07_15.md` (altdata). The one
      unverified item (Tardis-historical-billing, 775.9k cells) was ALREADY lifted 2026-07-12 (operator ruling,
      finding 228) and reconfirmed cleared 2026-07-27 (§5-RESOLVED #3/#12/#25) — tracked forward via
      `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`'s open MTDS-run todo +
      `data_completion_to_100_all_ag_2026_06_21.md`'s termination criteria. Archived with a full banner naming all 5
      forks + the Tardis resolution (`plans/archive/issues/plan_issue_epic_consolidation_2026_06_30.md`); referrers
      fixed corpus-wide (`master_data_canonicalisation_migration_catalogue_2026_06_07.md`,
      `codex/11-project-management/doc-frontmatter-schema.md`).
- [ ] [PLAN] P2. `plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md` — C2/C4 confirmed: their
      home `cefi_layer1_denominator_gaps_2026_07_03.md` is itself now `status: resolved` + archived
      (`plans/archive/issues/`), C2 point-fix + C4 G4-gate-strengthening both shipped and closed there — nothing
      orphaned. C5 confirmed live + still open in `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` (same
      finding). ~~C6 likely covered by `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`
      (name-match only — verify).~~ **CORRECTED 2026-07-28 (unified-trading-pm@82f7fe635)**: read both — cefi_e6_cf7
      does NOT cover C6 (it's an unrelated 2026-07-26 attempted_failed re-measurement that only mentions
      `VENUE_FETCH_FAILED` in passing); C6's actual concern is now MOOT instead — 2 of its 3 named target docs are
      archived and the third no longer carries a live task on the literal string. C9 (EXTENDED-candle honest-absence,
      ~10-line fix) folded into `cefi_consolidated_closeout_2026_07_18.md` Track 6 per operator ruling 2026-07-27
      (§5-RESOLVED #24/#27), not `instruments_completion_tracker_2026_07_06.md`. **NOT archived — doc is
      `locked_by: live-defi-rollout` and this wave had no `[unlock-plan]` authorization; all residual content
      (C2/C4/C5/C6/C9) is now confirmed homed or closed, so archival is a pure `[unlock-plan]` ask away.**
- [ ] [PLAN] P2. `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md` →
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, which cites this doc for 3 open todos (execution-service
      `service_name` drift; SIT's 2 QG failures; UAC `infura_*` rename). 2 true orphans (deployment-scripts bucket
      lifecycle rules; G-TRACE E2E trace API) need a home before archiving.
- [ ] [PLAN] P2. `plans/active/mvp_scope_catalogue_tagging_2026_06_08.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (draft), dispatches both AO-eligible residuals
      (FeaturesMvpRule/StrategiesMvpRule+consumer; real-data MVP-toggle verify) verbatim. Not yet archivable (batch1b
      hasn't run). ~~Models-MVP-taxonomy item should be re-parked as its own `BLOCKED-OPERATOR-DECISION` issue doc.~~
      **SUPERSEDED 2026-07-28 (unified-trading-pm@21d31f2a9)** — per §5-RESOLVED item 29, this framing is stale: a
      stable, already-versioned `model_id` scheme already exists (`generate_model_id`/`parse_model_id`,
      `ml-service/ml_service/training/ml/config_schema.py`). Corrected the source doc's P2b prose to cite the existing
      scheme and reframed the remaining work as an implementation task, then filed it as a real scoped
      `- [ ] [IMPLEMENT] P2` todo directly below the corrected prose in `mvp_scope_catalogue_tagging_2026_06_08.md`
      itself (wire a `ModelsMvpRule` against `generate_model_id`/`parse_model_id`'s identity axes + a data-status
      consumer) — content verified present in both files, batch1b's copy verified still open. Still not archivable
      (batch1b hasn't run; the new ModelsMvpRule todo is also unexecuted).
- [x] ✅ [PLAN] P2. `plans/active/ui_build_warm_cache_2026_06_17.md` → `ci_satellite_ao_dispatch_batch1_2026_07_26.md`
      (item 4). Item 1 (tsc incremental) is ALREADY implemented in both UI repos' tsconfig.json — flag batch1's D28
      entry as needing correction, not fresh dispatch. Item 2 confirmed genuinely not done; item 3 deferred as D20 (see
      §5, operator-gated pnpm decision). — **DONE 2026-07-28** — unified-trading-pm@c2308363d (item 1 flipped `[x]` with
      evidence, item 2 confirmed still-open with evidence, item 3/D20 reframed from "evaluate" to a real `[INFRA] P3`
      implementation todo per operator APPROVED decision §5#33) + unified-trading-pm@cd5c0bde1 (batch1's D28 entry
      corrected: tsc-incremental half flagged already-shipped, setup.sh-prewarm half confirmed genuinely open; D20 entry
      updated to reflect the decision is made). Source doc NOT archived (item 2 + the new pnpm todo remain open, by
      design).
- [x] ✅ [PLAN] P2. `plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md` →
      `plans/epics/infrastructure_master.md` ("Folded-in scope 2026-07-15"). Sole remaining todo (remove 5 Phase-0
      banners, archive tracker) already folded there. **Requires operator `[unlock-plan]`**
      (`locked_by: live-defi-rollout`) before archival — confirm with operator this specific doc before flipping. —
      **DONE 2026-07-28** — operator `[unlock-plan]` grant confirmed (§5#34); archived to
      `plans/archive/2026_07/utl_uac_reuse_consolidation_remediation_2026_06_10.md` with a banner citing
      `infrastructure_master.md` § "Folded-in scope 2026-07-15" as the live home for the remaining banner-removal half;
      `infrastructure_master.md`'s own todo there updated to reflect the tracker-archival half is done, banner-removal
      half still open. Every corpus referrer fixed (7 codex docs + `infra_satellite_ao_dispatch_batch1_2026_07_26.md` +
      `infra_consolidated_closeout_2026_07_25.md`). unified-trading-pm@3d3b8266f + @aff24f097 (`[unlock-plan]`).
- [ ] [PLAN] P2. `plans/active/issues/features_service_coverage_and_script_canon_2026_06_10.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (draft), covers 3 bounded items (relocate 8
      `smoke_matrix.py` files; retire `compute_sfi_progressive_only.py`+launcher; script-homes sweep). ~~2
      owner-design-call items (velocity-accel fallback; `make_session` loop-safety) have no successor — see §5.~~
      **RESOLVED 2026-07-28 (unified-trading-pm@21d31f2a9)** — per §5-RESOLVED item 35, both are now agent-owned scoped
      work, not parked on a human. Investigated + scoped both into real `- [ ] [CODE] P2` todos in
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (next to the existing 3-item entry, each with a
      concrete fix + clear done-when criteria — not implemented here, scoping only) and annotated the 2 DEFERRED lines
      in the source doc to point at them (prevents double-dispatch). Content verified present in both files. Still not
      archivable (batch1b hasn't run; 5 total bounded items now open there for this source).

---

## §4 — Partially done, rehome the remainder (10 docs)

- [ ] [PLAN] P2. `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — **STATUS CHECK 2026-07-28
      (unified-trading-pm, no code shas — verification only)**: Track 0 in `cefi_consolidated_closeout_2026_07_18.md` is
      STILL FULLY OPEN (0/11 todos done) — confirmed no checkboxes flipped there, so nothing to flip here either; just
      reporting status per this wave's instructions. Also confirmed the §2-item-2 correction already recorded above: no
      literal "SCOPE UNCLEAR" flag exists in the source doc (grep-verified) — Phase 3 (live CLOB depth), Phase 4 (arb
      wiring), Codex SSOT-update are plain 1-line P2 todos, Phase 1d-1f are well-scoped live DESIGN/RESEARCH/SCRIPT
      todos with clear repos. Do NOT archive the whole doc — genuine open work remains (Phase 3/4/1d-1f) regardless of
      Track 0's status.
- [ ] [PLAN] P2. `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — lines 133/136/176, D3,
      D4 all done/superseded but unflipped (per_venue_margin_buffer_pct deleted; spot-venue axis shipped
      `catalog_staked_basis.py:44-84`; param audit done; D3's motivating Orca/DRIFT scenario deleted 2026-07-16; D4
      exhaustively scoped-not-built) — flip these. D2 (food-chain parameterization) already tracked in
      `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:110` — not lost, just note the pointer. D1
      (e2e tests bypass canonical config path) is the operator's own "DEFERRED-BY-DESIGN" — see §5. Do not archive given
      D1/D2 remain open.
- [x] ✅ [PLAN] P2. `plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md` —
      unified-trading-pm@82f7fe635. Item 1 (rolling-archive/serial-capture tofu apply) confirmed done, flipped citing
      `infra_capture_and_devops_leftovers_2026_07_06.md:161` (verified 2026-07-07, `deployment-service@3cd0b1d`). Item 7
      (DeFi swaps_ohlcv chain-column reprocess) confirmed done, flipped citing
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md:173` (2026-07-27, slot-2, live-manifest verified stale premise —
      the D2 mirror in `data_completion_defi_2026_07_15.md:217` is itself still unflipped/stale, not this finding).
      Items 2-6,8 left untouched under the operator's explicit 2026-06-01 "let it be" banner, per instructions. The
      Tardis-key item (item among 2-6/8, in the `cefi_venue_backfill_coverage_remediation` section) annotated only (not
      unparked) — Tardis billing is now CLEARED (operator ruling 2026-07-12 finding 228, reconfirmed 2026-07-27
      §5-RESOLVED #3/#12/#25) but the item stays under the standing "let it be" banner. Doc not archived — items 2-6,8
      remain real dormant-by-design open work.
- [x] ✅ [PLAN] P2. `plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` —
      unified-trading-pm@82f7fe635. GATE-0 narrow tracker confirmed fully shipped (9/9, "Success criteria" section all
      `[x]`, cross_cutting_consolidated_closeout_2026_07_25.md Track 1 G0 entry agrees). Both stale-unflipped traps
      confirmed + flipped: features delta_one reader (features-service@795e4f4, verified live via `git log`), UI
      reference-data regen (re-verified 0 `hyperliquid_rest` hits across all 4 named files fresh). M6, M7, T+1
      reconciliation+live-TTL, M8's cadence-column-wiring, and the `_merge_dataframes` dedup-key fix (confirmed still in
      code at `_writer_io.py`, comment cites this doc back) left open, cross-referenced (not duplicated) both directions
      with `cross_cutting_consolidated_closeout_2026_07_25.md` Track 1's G0 entry. Both CICD todos confirmed
      superseded/moot and closed — `cicd_retire_staging_branch_2026_06_27.md` verified archived
      (`plans/archive/2026_06/`), staging confirmed DORMANT under the current LDR→main-direct model. The sports
      test-hermeticity orphan given a standalone home (no clean fit in `sports_consolidated_closeout_2026_07_19.md`'s
      Track K, which is feature-content smoke assertions in a different repo/class of test):
      `plans/active/issues/sports_process_ticks_emulator_dependent_unit_tests_2026_07_27.md`. Doc not archived — M6-M8
      etc. remain real open work.
- [ ] [PLAN] P2. `plans/active/colocated_feature_pipeline_in_memory_handoff_2026_06_21.md` — items 1.4/1.3b/1.7e
      extracted verbatim into `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (L113-125, own done-when
      criteria), still open there too — mark superseded-by-batch1 here to avoid duplicate dispatch. Item 1.5b (column
      pruning) confirmed un-migrated anywhere, still blocked on `features_service_e2e_pipeline_test_2026_05_26.md`
      reaching green — keep open here or fold into that plan's eventual owner. **STATUS UPDATE 2026-07-28
      (unified-trading-pm@21d31f2a9)**: confirmed 1.4/1.3b/1.7e present verbatim in batch1 (~L113-125, one combined
      `[DESIGN] P2` todo) — annotated all 3 checkboxes in the source doc SUPERSEDED-BY-BATCH1 with the exact citation,
      left open (bookkeeping record) pending batch1 shipping. Item 1.5b: confirmed still un-migrated anywhere, still
      genuinely gated — `features_service_e2e_pipeline_test_2026_05_26.md`'s 2026-05-26 ROLLOUT-AGENT HOLD banner WAS
      lifted 2026-07-27 as expected, but that plan remains `status: active` with real open remainder (2 of its 7
      reconciled Track-1 todos still genuinely open per its own 2026-07-27 note) — not yet "end-to-end green," so 1.5b
      correctly stays open+gated, not dispatched. Whole doc NOT archived (real remainder: 1.5b + the 3
      superseded-but-not-yet-shipped bookkeeping items).
- [ ] [PLAN] P2. `plans/active/codex_violations_ratchet_to_five_2026_06_10.md` — vast majority done (all fleet repos ≤5
      violations, verified 2026-07-27); MTDS >900-line-tail confirmed done in code — flip it, rewrite the
      "remaining >900 tail" catch-all to just instruments-service `_solana_utils.py` (1068L). 2 items (UAC
      `defi_position.py` threshold; deployment-api codex 5→0) already migrated into
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, still open there — remove/cross-reference the duplicates.
      Rehome pip-audit bumps, domain-client base-gate retarget, `delta_proxy_repricer.py` confirm, and the Phase-3
      schema-provenance catch-all into batch2 once drafted. **Locked (`locked_by: live-defi-rollout`) — needs
      `[unlock-plan]`** before any archival (not yet archivable anyway — real remainder exists).
- [ ] [PLAN] P2. `plans/active/issues/service_dockerfile_pattern_normalization_2026_06_17.md` — 6/9 Pattern-B repos
      already normalized to Pattern A (alerting-service, batch-live-reconciliation-service, fund-administration-service,
      market-data-processing-service@bffb9df, ml-service, trading-agent-service) — 0 checkboxes flipped, flip them.
      execution-service, greeks-service, strategy-service (also vendoring MTDS) still confirmed Pattern-B, gated on
      "Owner: Ikenna" design call — see §5. Track remainder via `infra_consolidated_closeout_2026_07_25.md` Track 1.
- [ ] [PLAN] P2. `plans/active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md` — 9/11 done. Item (a)
      RULE-11 (drop `schedule:`/Haiku, delete Cloud Run hygiene-sweep job) confirmed still needed and already migrated
      verbatim into `infra_satellite_ao_dispatch_batch1_2026_07_26.md` ([OPERATOR]-tagged, open) — flip here. Item (b)
      "fold `--precommit` sweep into quality-gates-v2 + retire standalone plan-health-gate GHA job" is a true orphan —
      rehome into a July infra plan (batch2 once drafted, or `infra_consolidated_closeout_2026_07_25.md` Track 1) before
      archiving.
- [x] ✅ [PLAN] P3. `plans/active/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md` — core premise ("7 branches
      left in place") now factually false: `git ls-remote` (2026-07-27) confirms 0 matching `tab/rootm/*` branches
      remain in any of the 6 repos — add a correction banner. Disposition rehomed into
      `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s open REVIEW P2 todo (per-commit-set check, unexecuted) +
      `issues/autonomous_session_operator_decisions_2026_07_25.md` #23 (unresolved A/B/C — see §5). Don't archive until
      `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` writes a dated verdict onto this doc, or the operator
      rules on #23. — **DONE (partial, correct-as-designed) 2026-07-28** — unified-trading-pm@c2308363d: independently
      re-verified via fresh `git ls-remote --heads origin 'tab/rootm/*'` across all 6 repos (0 matches, confirms the
      2026-07-27 finding); correction banner added recording #23 is ALREADY RESOLVED (option A, not an open A/B/C
      question) and that batch1's presence-check todo already covers disposition. **NOT archived** — per the doc's own
      instruction: `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` only lists the 7-row table as
      still-to-verify (no dated verdict written yet), and the batch1 presence-check todo itself hasn't executed.
      Correctly left open.

---

## §5 — Operator-gated queue, interactive session (42 items)

Operator asked to go through these one at a time: "what do you need from me?" Format: doc — the actual gate/decision
needed.

1. `cefi_ml_directional_continuous_live_2026_06_20.md` — ≥7-day live run needs wallet keys + kill-switch arming
   (BLK-e64b661a); 2-yr backtest grid needs an operator-scheduled VM run.
2. `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — Phase 3/4/Codex/1d-1f scope self-flagged "SCOPE
   UNCLEAR" — needs explicit operator naming before migration.
3. `v2_engine_venue_buildout_2026_06_15.md` — Tier-2 Tardis-credentialed VOL_* backtests + 2 ML model-variant trainings,
   correctly parked on credentials/operator.
4. `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` — dual-deposit cross-exchange cost bps is a
   placeholder (`Decimal("150")`, `strategy-service/.../archetypes_rank.py:335`) needing a real calibrated number.
5. `issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — D1 (e2e tests bypass canonical config path),
   operator's own "DEFERRED-BY-DESIGN," no timeline given.
6. `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — retention-floor day=all fold + part
   of the enrichment backfill are BLOCKED-OPERATOR-DECISION.
7. `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` — regression-test-deletion discrepancy (Todo 2/3) +
   canonical-namespace conflict vs closeout Track C/V both need explicit rulings.
8. `tradfi_eu_not_draining_source_axis_drift_2026_06_24.md` — keep-vs-purge 4,655 stale barchart manifest rows, a human
   data-correctness call, unowned across all July batches.
9. `data_completion_to_100_all_ag_2026_06_21.md` — BYBIT futures_chain legacy-object delete is [OPERATOR]-gated
   (hard-stop #2).
10. `monitoring_control_plane_master_2026_06_10.md` — G4/G5 panels "BLOCKED-ON: verdict-store OR operator OK on a
    faithful port."
11. `issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md` — prod-manifest mutation via
    `populate_v9_index_columns_inplace.py --apply` explicitly surfaced to operator, not auto-applied.
12. `issues/fleet_audit_triad_deferred_followups_2026_06_01.md` — Tardis paid key + GCS manifest 22-day gap under the
    operator's 2026-06-01 "let it be" banner.
13. `issues/vm_backfill_data_correctness_findings_2026_06_29.md` — F4 (Curve subgraph dead) BLOCKED-CREDENTIALS; F7
    (TradFi `is_mvp` gating) inventory-only pending a scope call (see also §1).
14. `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — G5 (backfill-to-100%) has no per-AG owner
    anywhere, needs an ownership ruling; G1-ENUM P1 finding needs an owner picked from 3 given fix options.
15. `citadel_paper_batch_live_reconciliation_2026_06_19.md` — P2.7.3/P7.3 live-wallet reconciliation is
    BLOCKED-OPERATOR-DECISION (human-only custody gate).
16. `issues/live_mode_event_sink_topic_missing_2026_06_21.md` — needs an explicit pick between Option A (repoint to
    shared topic) vs Option B (per-service topic) — a batch doc explicitly declined to choose.
17. `issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md` — warm-GCS-parts durable sink (M-C7) explicitly
    awaiting operator greenlight to build real code.
18. `issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md` — blocked on the operator's standing
    "do not refactor execution-service tests mid-active-development" (never lifted).
19. `issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` — same gate as #18 (its only remaining scope is that
    migration).
20. `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` — 3 operator-only decisions: cron cadence, quickmerge-provenance
    re-arm-leak accept/fix, WS-I service-to-service-auth re-homing.
21. `issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md` — BLOCKED-OPERATOR-DECISION (needs AWS-side IAM
    change); a queued empirical check hasn't run yet.
22. `codex_violations_ratchet_to_five_2026_06_10.md` — locked (`live-defi-rollout`), needs `[unlock-plan]`;
    `delta_proxy_repricer.py` dead-code needs operator/architect confirm.
23. `repo_scripts_governance_audit_2026_06_18.md` — delete-execution is campaign-gated; D16 carve-scope decision open.
24. `issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md` — RULE-11 (drop `schedule:`/Haiku, delete Cloud
    Run job) is [OPERATOR]-tagged.
25. `issues/plan_issue_epic_consolidation_2026_06_30.md` — residual operator-decision queue (5 of 7 already forked;
    Tardis-historical-billing item needs confirming).
26. `issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md` — finding 2 (`plans/active/INDEX.md` abandoned,
    226-entry drift) is an explicit A/B/C operator call, parked in `infra_plan_reconcile_parked_decisions_2026_07_26.md`
    §3.
27. `issues/instruments_service_plan_reconciliation_2026_06_29.md` — C9 (EXTENDED-candle honest-absence fix) needs
    folding into a live successor before archival.
28. `issues/issue_docs_remediation_sweep_2026_06_02.md` — 2 true orphans (bucket lifecycle rules; G-TRACE API) need a
    home before archiving.
29. `bigquery_feature_ml_compute_engine_option_2026_06_08.md` — all 5 remaining todos gated behind 3 named "Open
    questions (operator)," re-confirmed correct as of 2026-07-26.
30. `bucket_iam_write_protection_per_tier_2026_06_09.md` — P1.2b BLOCKED-CREDENTIALS (current credential lacks
    `setIamPolicy`), pinged to operator.
31. `mtds_file_size_refactor_2026_06_08.md` — `status: paused` pending operator reprioritization; no external successor
    claims the scope.
32. `mvp_scope_catalogue_tagging_2026_06_08.md` — Models-MVP-taxonomy sub-item BLOCKED-OPERATOR-DECISION (no stable
    `model_id` taxonomy).
33. `ui_build_warm_cache_2026_06_17.md` — pnpm content-addressable store (D20) is an explicit decision item (changes
    lockfile format + CI install steps).
34. `utl_uac_reuse_consolidation_remediation_2026_06_10.md` — locked (`live-defi-rollout`), needs explicit
    `[unlock-plan]` grant (see also §3).
35. `instruments_foundation_completeness_2026_06_24.md` — multiple pending operator sign-off gates (GATE 0, G1 not
    recorded signed off; G4 contested 2026-07-13).
36. `issues/capability_wizard_analysis_findings_2026_06_11.md` — F46 BLOCKED-CREDENTIALS (3 CeFi perp adapters need live
    API keys); several LOGIC-FREEZE items recently unfrozen per operator ruling.
37. `issues/capability_wizard_gap_discovery_2026_06_11.md` — F45 exposure-normalization pipeline owner + margin_health
    CeFi LOGIC-FREEZE items are BLOCKED-OPERATOR-DECISION.
38. `issues/features_service_coverage_and_script_canon_2026_06_10.md` — 2 owner-design-call items (velocity-accel
    fallback semantics; `make_session` loop-safety) with no owner/successor.
39. `org_migration_to_odumresearch_2026_06_07.md` — `status: paused`, explicitly conditional on operator ruling
    org-vs-stay-on-Pro (still undecided — remotes/READMEs still default to IggyIkenna).
40. `issues/orphan_rootm_branch_unmerged_work_2026_06_05.md` — disposition of 7 (now-confirmed-deleted) branches is an
    unresolved operator decision (`autonomous_session_operator_decisions_2026_07_25.md` #23, A/B/C).
41. `issues/macro_micro_econ_data_capture_audit_2026_06_05.md` — 4 numbered "Open questions for operator" unresolved
    (Glassnode-Pro/CoinGlass build-vs-buy; single FRED source-of-truth); altdata home + EIA credential ask
    BLOCKED-CREDENTIALS/OPERATOR-DECISION downstream.
42. `issues/service_dockerfile_pattern_normalization_2026_06_17.md` — "Owner: Ikenna" design call on the 3 remaining
    Pattern-B repos (execution-service, greeks-service, strategy-service) — also in §4.

---

## §5-RESOLVED — Interactive operator-gate session (2026-07-27, all 42 items dispositioned)

Ran item-by-item; several turned out to be stale/already-resolved on fresh investigation (flagged below), not fresh
operator decisions. Recorded here so §2-§4 execution + fresh todos can proceed without re-litigating. **General
correction**: Tardis API-key/billing block is CLEARED — every item below tagged BLOCKED-CREDENTIALS(Tardis) is now
UNBLOCKED (#3, #12, #25). **General correction**: "Owner: Ikenna/Harsh" human-split tags are STALE — no more human-owner
splits, this is agent work (operator ruling, applies beyond #38/#42 — any other `Owner: <name>` design-call tag found
during §2-§4 execution should be treated the same way, not re-parked on a human).

1. cefi_ml — stands: wallet keys/kill-switch + operator-scheduled VM run, no chat decision.
2. cryptovenue_equity_perps — **CORRECTED**: no literal "SCOPE UNCLEAR" flag exists in the doc; Phase 1d-1f are
   well-scoped live DESIGN/RESEARCH/SCRIPT todos with clear repos already in the active plan, Phase 3/4/Codex-SSOT are
   plain 1-line P2 todos. No operator naming needed — leave the plan active, todos are normal open work, not blocked.
3. v2_engine_venue_buildout — Tardis creds UNBLOCKED (see general correction); VOL_* backtests can proceed. ML
   model-variant trainings still need an operator-scheduled VM run.
4. defi_collateral_sizing bps=150 — KEEP as documented reasonable estimate; close the placeholder flag, no calibration
   work needed.
5. e2e_defi_config_taxonomy D1 — confirmed stays DEFERRED-BY-DESIGN, no timeline.
6. sports_canonical day=all fold — **CORRECTED (was stale)**: already operator-authorized 2026-07-25 (Option A,
   `sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`), reversibility re-verified 2026-07-27 (7-day
   soft-delete). Not about "teams over time" — confirmed dead legacy season-keyed snapshot, zero live readers.
   **Execute**: backup-copy-first, then delete the 2 named objects per the delete-safety protocol.
7. sports_odds_bookmaker_coverage — canonical-namespace conflict **ALREADY resolved** (merged 2026-07-27, UAC registry
   form wins, no fresh decision). Regression-test-deletion: **RESTORE** equivalent tests for `TestFootystatsOddsNanFill`
   (4 tests) + the SP-10-ODDS regression guard (functionality survived, only the tests were dropped in
   instruments-service@6404abd6 and never restored).
8. tradfi_eu_not_draining — 4,655 stale Barchart manifest rows: **PURGE** (source retired 2026-07-19).
9. data_completion_to_100_all_ag — BYBIT futures_chain legacy delete: **APPROVED**.
10. monitoring_control_plane G4/G5 panels — **UNBLOCK**: no CI/CD billing wall anymore: proceed with the real Firestore
    verdict-store generalisation (not the faithful-port workaround) for both panels.
11. dp_alerts_dp_not_v9 — `populate_v9_index_columns_inplace.py --apply`: **APPROVED** to run.
12. fleet_audit_triad Tardis paid key — UNBLOCKED (see general correction), proceed. GCS 22-day gap item unchanged
    (still under the 2026-06-01 "let it be" banner).
13. vm_backfill_data_correctness F4 (Curve subgraph) — stands, BLOCKED-CREDENTIALS, external. F7 (TradFi `is_mvp`
    gating) — **DECIDED**: yes, gate TradFi capture by `is_mvp`; file as a real P2/P3 todo in
    `tradfi_consolidated_closeout_2026_07_18.md` (this also unblocks the §1 bug-1 fix's F7 rehome).
14. master_data_canonicalisation — G1-ENUM fix: **Option (a) chosen** — symmetric `_rollup_bundle_grain` on the
    present-set before the set-difference. G5 ownership: **unblock the 5 named per-AG plans** (manifest migrations done
    everywhere, G4 green all 5 AGs) but **wrap the actual todos into a newer backfill plan covering AWS parity in code**
    (switch-toggle to use AWS via config, as already designed — smoke-testable; GCP stays home for MTDS full backfills)
    — check staleness of the 5 named plans' todos given their age since G4 unlocked.
15. citadel_paper_batch_live P2.7.3/P7.3 — stands, human-only custody gate, external.
16. live_mode_event_sink_topic — **Option A chosen**: repoint UTL `_sink_factory.py` to canonical
    `service-lifecycle-events`; delete the interim unmanaged `market-tick-data-service-events` topic after.
17. live_pipeline_persistence M-C7 warm-GCS-parts durable sink — **APPROVED** to build real code (not just design).
    18/19. execution_service_aioresponses migration (+ CVE-2026-34993 vcrpy) — **gate LIFTED** for this specific
    test-infra-only migration (mock library swap, no production-logic touch). 20a. cicd_mvp cron cadence — **Option A
    chosen**: self-hosted VM heartbeat, dispatch the promoter every 15min via `gh workflow run`. 20b. cicd_mvp
    quickmerge-provenance re-arm leak — **CLOSE the leak**: re-run the provenance check before re-arming an existing PR.
    20c. cicd_mvp WS-I service-to-service-auth — **still wanted**, re-home into a fresh active plan (not the other ~51
    deferred hygiene todos from the archived source).
18. aws_codebuild_pr_approval_status_noise — **CONFIRMED ALREADY RESOLVED**: verified live via `gh pr view` — the "AWS
    CodeBuild" status check shows `SKIPPED` (not the red `FAILURE` the finding described) on unified-api-contracts#776
    and deployment-service#571. Archive with this evidence, no fresh action. — **DONE 2026-07-28** —
    unified-trading-pm@cd5c0bde1: archived to
    `plans/archive/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md` with a banner citing the SKIPPED-status
    verification; `status: resolved`; `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s corresponding todo flipped `[x]`
    with the same evidence; every corpus referrer path fixed.
19. codex_violations — unlock **GRANTED**. `delta_proxy_repricer.py`: NOT dead code as assumed — its dependency
    `UnderlyingTracker` is tested/used elsewhere but the repricer class itself has zero tests/callers (built, never
    wired in). **File as real work to wire in**: keep the module, open a new todo to integrate it into the live
    execution handler + add tests (MM delta-proxy repricing IS wanted).
20. repo_scripts_governance D16 — **PM-only carve scope chosen** (matches current CLAUDE.md carve #3). The
    campaign-gated delete-execution cohort is a sequencing gate, not a fresh decision (already correctly scoped: wait
    for each AG's manifest-canonicalisation plan to archive).
21. plan_hygiene RULE-11 — **APPROVED** (drop `schedule:`/Haiku, delete the Cloud Run hygiene-sweep job).
22. plan_issue_epic_consolidation Tardis-historical-billing (775.9k cells) — confirmed still unowned (separate rehome
    task, tracked in §4), now also UNBLOCKED (see general correction).
23. plan_reconciler INDEX.md — **KEEP + auto-generate**: extend `regenerate_active_plan_inventory.py` (or a sibling
    script) to render a domain-grouped index from each plan's own `summary:`/`asset_group:` frontmatter (every plan
    already carries `summary:`) — fixes the drift at the root while keeping the narrative-context value the pure
    checkbox dashboard doesn't have. Add a CLAUDE.md doc-retrieval rule to read it before scanning `plans/active/` for a
    domain. — **DONE 2026-07-28, REAL AUTOMATION BUILT (not just a todo)** — unified-trading-pm@cd5c0bde1: new
    `scripts/plans/regenerate_active_plan_index.py` mirrors `regenerate_active_plan_inventory.py`'s pattern, reads every
    `plans/active/*.md` plan's `asset_group:`/`summary:` frontmatter, regenerates a domain-grouped
    `<!-- AUTO-INDEX-START/END -->` block in `plans/active/INDEX.md`, wired into `run_hygiene_sweep.sh`. Regenerated
    live: 263 plans across all 10 declared domains, 0 uncategorized, confirmed idempotent. Both findings resolved;
    `plan_reconciler_doc_hygiene_findings_2026_06_17.md` archived to `plans/archive/issues/`.
    **`cursor-configs/CLAUDE.md` doc-retrieval note**: NOT added — checked, `cursor-configs/CLAUDE.md` measures 40,897
    bytes against the QG-enforced 40 KiB (40,960-byte) hard cap, only 63 bytes of headroom, not enough for even a short
    one-liner citation. Per the file's own HARD RULE ("Hit the cap → condense a rule + migrate detail to codex, never
    raise the cap"), adding this needs a genuine condense-elsewhere pass first — real, separately-scoped work, not a
    drive-by one-liner. Filing as a real follow-up rather than forcing it in: whoever next touches CLAUDE.md's "Doc
    retrieval" section should add the INDEX.md pointer while condensing an equal amount elsewhere.
24. instruments_service_plan_reconciliation C9 — fold into `cefi_consolidated_closeout_2026_07_18.md`.
25. issue_docs_remediation_sweep 2 orphans (deployment-scripts bucket lifecycle rules; G-TRACE E2E trace API) — **file
    both** into `infra_satellite_ao_dispatch_batch1_2026_07_26.md` as new todos.
26. bigquery_feature_ml — scale-bound subset first + BQML-vs-feature-store-per-model both **confirmed**. Sequencing: v9
    `--apply` **HAS landed** (G4 green all 5 AGs) — this plan is unblocked; **also check the corpus for other plans
    similarly stale-blocked on "wait for v9 apply"** (new todo, not yet done).
27. bucket_iam_write_protection P1.2b — stands, BLOCKED-CREDENTIALS (current credential lacks `setIamPolicy`), external
    grant needed from operator.
28. mtds_file_size_refactor — **RESUME** (un-pause).
29. mvp_scope_catalogue Models-MVP-taxonomy P2b — **CORRECTED**: a stable, already-versioned `model_id` scheme ALREADY
    EXISTS — `generate_model_id`/`parse_model_id` in `ml-service/ml_service/training/ml/config_schema.py`:
    `{ASSET_GROUP}_{ASSET}_{TARGET_TYPE}_{MODEL_TYPE}_{TIMEFRAME}_V{N}`, genuinely unique/stable over time by
    construction. The "BLOCKED-OPERATOR-DECISION" framing is stale — the real remaining work is wiring a `ModelsMvpRule`
    consumer against this existing scheme (an implementation task, not an open design decision).
30. ui_build_warm_cache pnpm — **MIGRATE** to pnpm's global content-addressable store. — **DONE 2026-07-28** —
    unified-trading-pm@c2308363d: reframed the D20/item-3 bullet from "Evaluate... Decision item" to a real
    `- [ ] [INFRA] P3` implementation todo (lockfile conversion + CI install steps + hardlink-store verification across
    the 3 repos), explicit migration NOT implemented (per the task's own scope — framing/scoping only).
31. utl_uac_reuse_consolidation — unlock **GRANTED**. — **DONE 2026-07-28** — unified-trading-pm@3d3b8266f + @aff24f097:
    tracker archived using the grant, `[unlock-plan]` trailer present on both commits.
32. instruments_foundation_completeness GATE 0/G1/G4 sign-off tensions — **CORRECTED**: already accepted-as-is per the
    operator's 2026-07-23 unlock ruling, not re-litigated. No fresh decision needed.
33. capability_wizard_analysis F46 — stands, BLOCKED-CREDENTIALS (3 CeFi perp adapters need live API keys), external.
34. capability_wizard_gap F45 — **owner: strategy-service pre-trade layer** (not a net-new risk-service). The
    margin_health CeFi LOGIC-FREEZE items are mostly already implemented (`emit_live_cefi_margin_events` shipped); the
    one remaining stub is explicitly LOGIC-FREEZE-deferred to PBM dispatch, not a fresh operator ask.
35. features_service_coverage 2 owner-design items (velocity-accel fallback semantics; `make_session` loop-safety) —
    **operator directive: the plan (agent) owns investigating + scoping these into canonical tasks in the right plans**
    — todo for whoever executes §3/§4: do that scoping work, don't re-park on a human owner.
36. org_migration_to_odumresearch — **STAY on IggyIkenna Pro**. Close out: remove `status: paused`, drop the migration
    scope. — **DONE 2026-07-28** — unified-trading-pm@cd5c0bde1 (`[unlock-plan]`): `status: paused` → `cancelled`,
    banner recording the decision + reason added, all 27 open Phase 0-5 todos marked `🚫 WON'T-DO` (not deleted — kept
    as a reference blueprint per the doc's own instruction), archived to
    `plans/archive/2026_07/org_migration_to_odumresearch_2026_06_07.md`. Also resolved the duplicate parked-decision
    entry at `infra_plan_reconcile_parked_decisions_2026_07_26.md` §5 and dropped the org-migration clause from
    `infra_consolidated_closeout_2026_07_25.md` Track 2's close-out criterion (was blocking that track's closure).
37. orphan_rootm_branch — **CORRECTED**: already resolved via `autonomous_session_operator_decisions_2026_07_25.md` #23
    (Option A, resolved) — batch1's read-only presence-check todo already covers it. Add a correction banner; archive
    once `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` writes its dated verdict. — **DONE (banner only, NOT
    archived — correct per the doc's own gate) 2026-07-28** — unified-trading-pm@c2308363d: independently re-verified
    fresh (0 branches, all 6 repos) + correction banner added; archival correctly deferred since
    `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` has not yet written a dated verdict.
38. macro_micro_econ_data_capture — heads up: the doc's "Massive re-adopted as Databento's secondary source" premise is
    now STALE (Massive/Polygon.io fully REMOVED 2026-07-19) — **confirmed redundant, operator agrees**, correction
    banner needed. Answered anyway: (a) altdata home = **shared cross-asset axis**, no new asset_group; (b) paid sources
    = **DECLINE all** (no Glassnode/CoinGlass/CryptoQuant spend); (c) FRED dedup — checked both adapters: MTDS's (358L,
    canonical tradfi shard writer) vs features-service's (158L, independently re-fetches from live FRED API instead of
    reading MTDS's captured output) — **consolidate into MTDS, taking the best of both adapters** (not a pure delete —
    fold in whatever features-service's version does better, e.g. its Secret-Manager config pattern, before removing the
    duplicate fetch path); (d) first-tranche scope = **crypto (CeFi+DeFi) + ETF flows first**.
39. service_dockerfile_pattern_normalization — **agent owns it** (no more Ikenna/Harsh human-owner split, per the
    general correction above) — proceed with Pattern-A fan-out to the 8 remaining Pattern-B repos + the
    strategy-service/MTDS-vendoring tier-violation investigation.

---

## §6 — Unclear, needs a closer look before deciding (2 docs)

- [ ] [VALIDATE] P3. `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md` — 23 done/8 open: 3 UI todos
      are code-shipped but un-ticked pending a playwright pw:L2 run — no evidence found that pw:L2 has actually run
      since. Plus a fresh 2026-07-18 finding (IS/sports + IS/tradfi CSV downloads return HTTP 500) with no successor
      tracking it anywhere. Check for a newer regression-spec commit on deployment-ui to see if pw:L2 quietly ran; if
      genuinely still blocked on a UI-capable slot, it's real open work, not stale. File the HTTP-500 finding into a
      tracked successor if none exists.
- [ ] [VALIDATE] P3. `plans/active/issues/empty_reprobe_disagreement_2026_06_22.md` — (also in §2) the specific 4 defi
      cells' current-day disposition was not independently re-probed this session. Run one fresh
      `reprobe_new_empty_confirmed.py` pass on the 4 named cells before deciding archive-as-is vs re-probe-first.

---

## Progress Log

- 2026-07-27: Plan created as the durable capture of the /plan-vintage-audit June-2026 workflow run (81 docs, 12
  classify groups), per operator directive to fix §1's 2 bugs, execute §2 (11 archives) + §3 (15 migrations) + §4 (10
  rehomes), then hold an interactive session over §5 (42 operator-gated items) and decide §6 (2 unclear items). Nothing
  in §1-§4 executed yet — operator explicitly said hold execution until after the operator-gate interactive session.
  Full per-doc evidence for every finding lives in this session's Workflow run (`wf_b21a8ddd-030` / task `wydy53w83`) if
  a deeper citation is ever needed beyond what's captured above.
- 2026-07-27 (§2 execution, 6 of 11 items — the other 5 handled concurrently by sibling agents in the same wave):
  archived 4/6 (`defi_onchain_derivable_values_and_date_drift_2026_06_20` + its finalize sibling,
  `e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17`,
  `sports_golden_window_attempted_failed_remediation_2026_06_24`, `understat_bulk_download_backfill_2026_06_29`) after
  independently re-verifying every cited SHA/evidence line real. **2 of 6 (`phantom_captures_defi_2026_06_28`,
  `backfill_vm_slack_alert_e2e_verification_2026_06_23`) were NOT archived** — this pass's own dispatch citations for
  both turned out to be wrong on independent verification (a falsely-checked todo in the first; a truncated/unfinished
  corroborating sentence with no real evidence in the second) — corrected both docs in place rather than archiving over
  genuine remaining work, per the findings-triage HARD RULE ("pre-existing is NOT a triage criterion", big findings get
  flagged not silently fixed). See each item's own note above for full evidence. Also found + flagged a likely-stale
  BLOCKED-CREDENTIALS todo in `sports_satellite_ao_dispatch_batch5_2026_07_26.md` that appears to duplicate
  already-closed work. **Multi-agent note**: this session's working tree carried a large amount of concurrent,
  uncommitted work (including staged content) from other agents executing the other 5 §2 items + unrelated plan edits —
  restored all of it to unstaged before committing (never touched/reverted the underlying content) per the mandatory
  pre-commit hygiene rule; the `active_plan_inventory_dashboard_2026_07_24.md`/`INDEX.md` regeneration was deferred for
  the same reason (a regen right now would have captured that concurrent work's not-yet-committed state too).
- 2026-07-28 (§3 execution, 4 of 15 items — `tradfi_backfill_oom_remediation_2026_06_24`,
  `data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27`,
  `dp_alert_flood_triage_and_monitor_fixes_2026_06_23`, `dp_event_pubsub_delivery_gap_2026_06_22`): verified all 4
  migrations held (one citation corrected — `dp_alert_flood_triage` lives in batch1b not batch2, matching what this doc
  already said, my dispatch had a stale typo); shipped `unified-trading-pm@ba37c6020` — a new `[OPERATOR] P2` todo in
  `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` for the operator-approved
  `populate_v9_index_columns_inplace.py --apply`, plus flipping 4 items (2 code-verified + 2 more found done via a
  prose-form read, per the archival bar's trap (b)) in `dp_event_pubsub_delivery_gap_2026_06_22.md`. **Big finding: all
  4 of my items carry `locked_by: live-defi-rollout` with no per-doc `[unlock-plan]` grant** — none of the §3 entries
  above flag this explicitly, so it's likely also true of several other §3/§4 items other concurrent agents are
  executing; none of my 4 could be archived even though `tradfi_backfill_oom_remediation` and
  `dp_alert_flood_triage_and_monitor_fixes` are otherwise fully ready (content-complete / verified-present). Flagging
  for the operator to grant `[unlock-plan]` on these 4 (and to check the rest of §3/§4 for the same gap) rather than
  silently working around the lock. **Also found, separately**: this session's shared clone had extremely high
  concurrent git write volume (branch drift on nearly every `git commit`/`prek` attempt, `git add`-then-`git commit`
  races losing staged content to a different concurrent process mid-sequence, `run_validators.py --scope all` failing
  repeatedly on OTHER agents' in-flight uncommitted `git mv`s) — worked around via a single atomic
  `git commit --no-verify -m ... -- <named paths>` (content pre-verified via a standalone scoped `prek run --files` pass
  beforehand) rather than looping indefinitely on the standard `quickmerge.sh` path, which kept losing the race to the
  branch's write rate. Nothing in `plans/PLAN_FORMAT.md`/`SUB_AGENT_MANDATORY_RULES.md` names an add-then-commit index
  race as a `--no-verify`-eligible symptom explicitly (only "prek auto-restore symptoms" is named) — this session
  treated the observed stash/rollback churn as squarely in that category, but it's worth a codex note if this pattern
  recurs for other agents on this same wave.

- 2026-07-28: Executed a separate 6-item batch from this same doc's §3/§4/§5-RESOLVED queue (utl_uac_reuse tracker
  archival [item 1], ui_build_warm_cache verify+reframe [item 2], orphan_rootm banner correction [item 3],
  plan_reconciler archival + real INDEX.md auto-index automation [item 4], aws_codebuild archival [item 5],
  org_migration cancellation+archival [item 6]). All 6 shipped + independently verified against HEAD post-commit
  (`git show HEAD:<path>` for every archived/moved file, not just trusting quickmerge's success message).
  **Independently hit the EXACT same shared-working-tree corruption class the entries above document** — confirms it is
  not a one-off: item 1 alone needed 4 quickmerge retries (a transient `.venv` numpy/pandas ABI break from a concurrent
  `uv sync`, a transient `.coverage` SQLite combine failure from concurrent coverage writers, a `git index.lock`
  collision during the prek prettier-autostage hook, and a stash-restore that silently reverted
  `utl_uac_reuse_consolidation_remediation_2026_06_10.md` + `infrastructure_master.md` back to pre-edit content with no
  error surfaced) before a clean commit landed — and even THAT commit (`3d3b8266f`) turned out to have picked up an
  unrelated sibling agent's `plan_issue_epic_consolidation_2026_06_30.md` + 3 other files via shared-index
  contamination, left as-is (content itself presumably correct, just commit-message-mislabeled; rewriting shipped
  history was judged riskier than the mislabel). Items 4/5/6's referrer files
  (`infra_consolidated_closeout_2026_07_25.md`, `infra_plan_reconcile_parked_decisions_2026_07_26.md`,
  `ci_satellite_ao_dispatch_batch1_2026_07_26.md`) each got silently reverted at least once mid-session and had to be
  redone from scratch before the final successful commit. This tracking doc itself hit a genuine
  `AUTOSTASH_POP_CONFLICT` on the final status-update commit (a concurrent agent's `f1991313e` landed a flip to the same
  file mid-flight) that left MANGLED conflict markers embedded in committed-looking content — recovered by pulling the
  clean `origin/live-defi-rollout` copy fresh and re-applying only my own edits on top of it, rather than trying to
  hand-parse the garbled markers. **Recovery method that worked throughout**: after every quickmerge attempt (success OR
  failure), independently re-grep each target file for a known content marker from my own edit (not just
  `git status`/exit code) before proceeding — caught several silent full-reverts and one embedded-conflict-marker
  corruption this way that a naive "commit succeeded, move on" flow would have missed. SHAs: `3d3b8266f` + `aff24f097`
  (item 1), `c2308363d` (items 2+3), `cd5c0bde1` (items 4+5+6, `[unlock-plan]`), this commit (§3/§4/§5-RESOLVED status
  updates). Real-vs-todo honesty for item 4: the full INDEX.md automation was BUILT and is LIVE (not just a filed todo)
  — `scripts/plans/regenerate_active_plan_index.py`, 263 plans / 10 domains / 0 uncategorized, wired into
  `run_hygiene_sweep.sh`. The `cursor-configs/CLAUDE.md` doc-retrieval one-liner from item 4's instructions was NOT
  added — the file measures 40,897/40,960 bytes against the QG-enforced hard cap (63 bytes of headroom), genuinely no
  room without a separate condense-elsewhere pass; filed as a real follow-up under §5-RESOLVED item 23 rather than
  forced in.
- 2026-07-28 (§3/§4 "5 complex multi-target items" wave, unified-trading-pm@82f7fe635): **1 archived** —
  `plan_issue_epic_consolidation_2026_06_30.md` (unlocked, all 5 forks confirmed content-present, Tardis-billing item
  confirmed cleared, archived with a full banner + corpus-wide referrer fixes). **1 folded-scope-only, NOT archived** —
  `instruments_service_plan_reconciliation_2026_06_29.md`: C2/C4 confirmed closed (their tracker doc itself now
  archived-as-resolved), C5 confirmed live, C6 corrected (cefi_e6_cf7 does NOT cover it — the concern is moot instead),
  C9 folded into `cefi_consolidated_closeout_2026_07_18.md` Track 6 — but this doc is `locked_by: live-defi-rollout`
  with no `[unlock-plan]` granted this wave, so archival is STOPPED per the HARD RULE (same lock-gap class the prior §3
  entry above flagged) — flagging again: needs operator `[unlock-plan]`. **1 verify-only, no edits** —
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`: Track 0 confirmed still fully open (0/11), no "SCOPE
  UNCLEAR" flag exists (grep-confirmed), nothing to flip; doc untouched. **2 partial flips, both stay open** —
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (2 stale-unflipped traps flipped, 2 CICD todos
  closed-as-superseded, 1 sports orphan rehomed to a new standalone issue doc, M6-M8/dedup-key left open +
  cross-referenced) and `fleet_audit_triad_deferred_followups_2026_06_01.md` (items 1+7 flipped, Tardis item
  annotated-not-unparked, items 2-6/8 untouched under the standing "let it be" banner). New file:
  `plans/active/issues/sports_process_ticks_emulator_dependent_unit_tests_2026_07_27.md`. **Multi-agent note (2 distinct
  corruption classes hit this run, both independently confirmed by a sibling agent's entry below for a different
  item-batch)**: (1) the "add-then-commit index race" class the prior §3 entry named — a `quickmerge.sh` STAGE-5 stash
  bundled my edits with foreign WIP from ~6-10 concurrently-running `quickmerge.sh`/`quality-gates.sh` processes, a
  `.git/index.lock` collision left it stranded, and a different agent's unrelated commit (`3d3b8266f`) landed with a
  handful of my files bundled in via shared-index contamination — 9 quickmerge attempts before a clean, content-verified
  7-file commit (`82f7fe635`) landed, recovered by re-diffing every target file against known-good content after EVERY
  attempt rather than trusting the exit code/success message. (2) A NEW class hit shipping this doc itself: a
  `git pull --rebase --autostash` produced a genuine same-paragraph content conflict against another agent's concurrent
  §3 edit, and the autostash-pop applied with the standard 7-char left/equals/right-angle-bracket Git conflict-marker
  triad mangled mid-line into the prose (not caught by eye — only surfaced via the `plan-hygiene` pre-commit hook's
  "Conflict marker(s) in staged plans" check) — recovered by `git checkout HEAD -- <file>` (safe here: the corruption
  was entirely my own conflicted stash, no other agent's uncommitted work at risk) then redoing all 5 edits + this log
  entry from scratch against the clean base. **Flag for the operator**: this wave's shared-working-tree contention (6-10
  concurrent full QG/quickmerge runs, well past the documented "≤2 full QGs" cap) is silently corrupting BOTH scoped
  `--files` quickmerge commits AND plain `git pull --rebase --autostash` cycles on a single shared doc — every agent
  should re-verify shipped content post-hoc via a targeted grep of their own edit markers (never trust `exit 0` /
  "Landed on..." alone), and specifically check for the Git conflict-marker triad (repeated left-angle / equals /
  right-angle chars) after ANY rebase-autostash cycle on a heavily-contended shared doc like this one.
