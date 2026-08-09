---
doc_type: issue
title: Deferred follow-ups from the 2026-05-27 fleet-audit triad (archived)
summary:
  The three 2026-05-27 fleet-audit plans were operator-marked **done** and archived on 2026-06-01. Their code shipped;
  these are the consciously-deferred tails ("let it be" — not to be actioned until...
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: [infrastructure, backfill, tradfi, defi, ui, runbook, plan-hygiene]
related:
  [
    /codex/05-infrastructure/vm-log-archival.md,
    plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md,
    plans/active/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md,
  ]
created: 2026-06-01
author: unknown
parent_epic: infrastructure_master
priority: P2
source:
  [
    ../canonical_vm_log_archival_2026_05_27.md,
    ../cefi_venue_backfill_coverage_remediation_2026_05_27.md,
    ../deployment_ui_vm_and_venue_coverage_visibility_2026_05_27.md,
  ]
assigned_vm: planning
resolved_by:
locked_by: harsh-fleet-audit
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    deployment-service/scripts/vm/vm_log_archival_cron.py,
    deployment-service/terraform/gcp/vm_log_archival_scheduler.tf,
  ]
---

# Deferred follow-ups — fleet-audit triad

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** These stay **deferred** as written. The
> Tardis-paid-key item is explicitly **NOT activated** (operator won't — see `running_vm_fleet_status_2026_05_27.md`);
> the GCS-migration items remain operator-deferred (no whole-corpus walk). **Slot 7 does not action any item here** — it
> is a "let it be" tail. No manifest-canonicalisation / GCS-migration work by slot 7.

The three 2026-05-27 fleet-audit plans were operator-marked **done** and archived on 2026-06-01. Their code shipped;
these are the consciously-deferred tails ("let it be" — not to be actioned until the operator chooses). Captured here so
they are not silently lost on archival (per the plan-archival HARD RULE).

## What I found

### From `canonical_vm_log_archival`

- [x] ✅ [INFRA] P2. **Rolling-archive + serial-capture crons committed but never `tofu apply`'d.** No
      `log-archive/rolling/` or `log-archive/serial-rolling/` prefixes exist; no Cloud Run jobs / schedulers for them.
      Net effect: the **14-day TTL on `vm-logs/` is NOT actually survived in prod** — the durable-archive guarantee the
      plan was built for is not live. (Live `vm-logs/` 30s stream IS healthy.) Same "tofu-never-applied" pattern as
      `aws_manifest_consolidator_scope` P1.10. To activate: apply `vm_serial_capture_scheduler.tf` + stand up the daily
      rolling rsync cron. **DONE — `infra_capture_and_devops_leftovers_2026_07_06.md:161` (verified 2026-07-07)**:
      `deployment-service@3cd0b1d` — `scripts/vm/vm_log_archival_cron.py` copies `vm-logs/{vm}/run.log` →
      `log-archive/rolling/{date}/{vm}/run.log` daily; Cloud Run Job `vm-log-archival-prd` + Cloud Scheduler
      `0 2 * * * UTC` (ENABLED), Terraform `vm_log_archival_scheduler.tf` applied. Confirmed 2026-07-28
      (`june_2026_vintage_audit_findings_2026_07_27.md` §4).
- [x] ✅ [INFRA] P3. **Doubled-path nesting** in the 2026-05-30 migration copy:
      `log-archive/snapshot_20260527_1300/snapshot_20260527_1300/<vm>/...`. Cosmetic; objects are intact + counted.
      **DONE (2026-08-04, slot-12)** — one-time 2026-05-30 manual migration copy artifact; current archival scripts
      (`backup-vm-logs.sh` always copies from `vm-logs/`, `vm_log_archival_cron.py` constructs paths correctly via
      `f"{dest_prefix}{relative_path}"`) do not have this bug. No code change needed; finding acknowledged.

### From `cefi_venue_backfill_coverage_remediation`

- [x] ✅ [DATA] P3. **RETAGGED 2026-07-28 (workspace stale-gate audit) — the operator gate itself is resolved.**
      Original ask (2026-06-01): Tardis paid key intentionally NOT activated; all code coverage-aware (free-only); paid
      historical CeFi backfill out of scope until the operator activates `tardis-api-key`. **ANNOTATION (2026-07-28, not
      unparked)**: the Tardis API-key/billing block described here is now CLEARED — operator ruling 2026-07-12
      (finding 228) activated the paid key + confirmed unlimited access, reconfirmed again 2026-07-27
      (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED general correction, items #3/#12/#25); the paid
      historical CeFi Tardis backfill is dispatched/in-progress elsewhere
      (`cefi_hl_aster_batch_data_gaps_2026_06_22.md`, `data_completion_to_100_all_ag_2026_06_21.md`). No operator
      decision remains pending on this line — retagged off [OPERATOR] accordingly. **Checkbox flipped 2026-08-05
      (slot-4, fleet_audit_triad_deferred_followups-015)** — the operator gate is resolved and the backfill is tracked
      elsewhere; the doc's "let it be" banner still parks the remaining deferred items.
- [x] ✅ [DATA] P3. **GCS manifest migration / 22-day-gap reconcile (2026-05-07→05-24) — DONE (2026-08-05, slot-2).**
      Resolved by `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`: Phase A (2026-07-30,
      `canonical-migration-cefi-20260730-012546`) migrated 275,363 objects legacy→canonical via
      `migrate_cefi_flat_to_v9_canonical.py`, filling the 22-day gap; Phase B (2026-08-03,
      `canonical-migration-cefi-drop-stale-20260803-120428`) phantom-sweep deleted 287,074 stale legacy objects.
      Residual: manifest `_index` rebuild (re-consolidation) is Phase D of that plan, still pending — tracked there, not
      here. Playbook reference (for history): `cefi_..._2026_05_27.md` §6I +
      `bucket_name_ssot_canonicalisation_2026_05_10`.

### TradFi MDPS reprocess + codex marker drift (folded in 2026-06-01, from deleted `mdps_tradfi_backfill_log_findings`)

- [x] ✅ [DATA] P2. **Full tradfi processed_candles reprocess** (~712 days 2020→2026, ~2–4M objects) — code shipped;
      reprocess unblocked. All 4 code findings SHIPPED + verified on LDR (2026-08-05, slot-13): Finding 1 session-grid
      LOCF forward-fill (mdps@b67cddd + 7cb5fab + db233e2 — also fixed defi/swap_adapter), Finding 2 429-backoff
      (UTL@cb1f4b5f `_upload_with_backoff_on_429`), Finding 3 UNKNOWN-partition re-normalization (canonical_writer),
      Finding 4 faulthandler (UTL@de00a08d). All 5 SHAs confirmed reachable from origin/live-defi-rollout. The Tardis
      API-key block that was gating "once backfills resume" is CLEARED (operator ruling 2026-07-12, reconfirmed
      2026-07-27). Reprocess command (launch via infra worker when tradfi raw tick backfill is complete):
      `bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --force tradfi 2020-01-01 2026-04-18 full` (MDPS
      reads raw_tick_data → writes processed_candles; --force re-writes already-captured cells).
- [x] ✅ [DOC] P3. **B2 codex marker reconciliation (HARD-RULE SSOT — do deliberately, NOT a find-replace).** Code emits
      carried-forward-bar markers as `staleness_seconds`>0 + `trade_count==0`; codex
      `honest-absence-downstream-handling.md` + `live-pipeline-architecture.md` (Category D) still describe a
      `zero_activity=True` / `ZERO_ACTIVITY_BAR` marker. Reconcile when the honest-absence SSOT is next revised — but
      FIRST rule on the model split: prediction Category-D emits NaN OHLC bars (different marker semantics) vs
      tradfi/cefi session-grid forward-fill (no NaN). The marker column may stay a boolean (renamed) rather than
      collapse to `staleness_seconds`. Verified `zero_activity` has no code consumers (pure doc drift, not a live
      breakage).

      **MOSTLY STALE-DONE (2026-07-30, conflict-check)** — `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md:375`
      already shipped this exact reconciliation in BOTH `honest-absence-downstream-handling.md` and
      `live-pipeline-architecture.md` (reconciliation banners verified live in both). Real residual: a named 3-doc set
      (incl. `00-SSOT-INDEX.md`) still untouched — narrow this todo to that residual rather than re-doing the whole
      reconciliation.

      **DONE (2026-08-02, slot-15)** — read all 3 named residual docs deliberately (not a find-replace); none of them
      claimed the retired `zero_activity=True` boolean column (the actual B2 error) — `codex/00-SSOT-INDEX.md` and
      `/codex/04-architecture/batch-live-architecture.md` only use `ZERO_ACTIVITY_BAR` as the category *label*, which
      the existing banner in `live-pipeline-architecture.md` explicitly retains for continuity; `alerting-batch-live.md`
      uses `zero_activity_bar_rate`, a real, shipped `StreamingHealthSnapshot` field
      (`unified_trading_library/streaming/streaming_health.py`), unrelated to the retired boolean. Added a short
      cross-reference note to each of the 3 docs pointing to the as-shipped marker
      (`staleness_seconds>0 + trade_count==0`) and the B2 banner, so a reader landing on the legacy token isn't misled.
      — unified-trading-pm@(this commit).

### DeFi chain-column reprocess (folded in 2026-06-01)

- [x] ✅ [DATA] P2. **DeFi swaps_ohlcv `chain`-column reprocess** — 28,634 UNISWAP_V3-ETHEREUM `attempted_failed` rows +
      ~9 companion venues (UNISWAP_V2, AAVEV3-OPTIMISM, EIGENLAYER, CURVE, MAKER, FRAX, DRIFT-SOLANA,
      KAMINO/JITO/MARGINFI). Code fix shipped (mdps@7f1a5b5 + @3799c8d); only a retry pass is needed. Run all affected
      venues together as part of the DeFi backfill / GCS-migration pass — NOT piecemeal. Detail:
      `uniswap_v3_ethereum_28k_attempted_failed_2026_05_28.md`. **DONE —
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md:173` (2026-07-27, slot-2)**: live-manifest verified STALE PREMISE
      — zero `attempted_failed` rows remain for UNISWAP_V3-ETHEREUM or any of the 10 companion venues under
      `swaps_ohlcv`/`dex_pool_swaps`; `chain` column 100% populated fleet-wide (0/795 null); the C0 full-hive
      canonicalisation migration (`canonical-migration-defi-20260618-180603`) already re-derived this data with the
      fixed code, so no reprocess run was needed. (Also cited as D2 in `data_completion_defi_2026_07_15.md:217`, whose
      own checkbox is still unflipped there — that doc's mirror is stale, not this finding.) Confirmed 2026-07-28
      (`june_2026_vintage_audit_findings_2026_07_27.md` §4).

### From `deployment_ui_vm_and_venue_coverage_visibility`

- [x] ✅ [UI] P3. **Per-item Playwright pw:L2 never ran green in the slot env** (`libatk-1.0.so.0` missing on the EC2
      worker). Specs are written; the §5 full-suite pass (deployment-ui@7bbc270, 140/140) is the standing evidence. If a
      future change touches these surfaces, run the smoke suite where system deps exist before re-ticking.

      **DONE (2026-08-02, slot-7) — the `libatk` slot-env blocker is RESOLVED; pw:L2 now runs green in-slot.** Verified
      empirically in the slot-7 worktree (deployment-ui@b7f5d81): `ldd chrome` reports 0 missing libs and a headless
      chromium launch succeeds, so the 2026-06-01 "`libatk-1.0.so.0` missing" premise no longer holds. Ran the full pw:L2
      **smoke** suite the item asked for — `npx playwright test tests/smoke` (per-slot mock server on :5206,
      `VITE_MOCK_API=true`, workers=1) → **428 passed / 0 failed (8.3m), exit 0**, covering the VM- and venue-coverage
      surfaces this item guards (e.g. `vm_deployments_reconcile`, `vm-resource-rolling-window`, `venue_*`,
      `data_status_coverage_labels`, cockpit AG/VM picker). This re-tick satisfies the item's own condition ("run the
      smoke suite where system deps exist before re-ticking"). NB the heavier `tests/e2e/**` drilldown specs showed
      30.0s-timeout flakes when run concurrently under host load-avg ~42 on 16 cores (5 sibling slots running Playwright)
      — that is the shared-host-contention flakiness the `playwright.config.ts` comment already documents (workers=1
      mitigates but does not eliminate it), not a regression, and e2e is outside this item's "smoke suite" scope. Doc-only
      flip: the specs (`deployment-ui@7bbc270`) were already shipped; only the run-and-re-tick remained.

## Why it matters

The log-archive durability gap is the only one with operational teeth: VM logs older than 14 days will expire because
nothing rolls them into the durable archive. Acceptable while the operator has explicitly deferred — flagged so it is a
known, not a surprise.

## Recommended decision

Leave deferred. Revisit the log-archive crons if/when long-horizon VM-log forensics are needed, and the CeFi migration
when the paid Tardis tier is activated.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (4 entries). Note: `locked_by: harsh-fleet-audit` protects this
  doc from archival only (per `plans/PLAN_FORMAT.md` § "Plan Locking"), not from an additive frontmatter field like this
  one — no unlock needed, and this doc's own "let it be" banner/open todos were not touched.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
