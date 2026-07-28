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
- [ ] [INFRA] P3. **Doubled-path nesting** in the 2026-05-30 migration copy:
      `log-archive/snapshot_20260527_1300/snapshot_20260527_1300/<vm>/...`. Cosmetic; objects are intact + counted.

### From `cefi_venue_backfill_coverage_remediation`

- [ ] [OPERATOR] P3. **Tardis paid key intentionally NOT activated.** All code is coverage-aware (free-only). Paid
      historical CeFi backfill is out of scope until the operator activates `tardis-api-key`. **ANNOTATION ONLY
      (2026-07-28, not unparked)**: the Tardis API-key/billing block described here is now CLEARED — operator ruling
      2026-07-12 (finding 228) activated the paid key + confirmed unlimited access, reconfirmed again 2026-07-27
      (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED general correction, items #3/#12/#25); the paid
      historical CeFi Tardis backfill is dispatched/in-progress elsewhere
      (`cefi_hl_aster_batch_data_gaps_2026_06_22.md`, `data_completion_to_100_all_ag_2026_06_21.md`). This item itself
      stays under the doc's standing 2026-06-01 "let it be" banner and is NOT actioned here — flagged per this wave's
      instructions so the stale "NOT activated" framing isn't read as still-current.
- [ ] [DATA] P3. **GCS manifest migration / 22-day-gap reconcile (2026-05-07→05-24) deferred until operator sees fit.**
      Manifest remains not-fully-trustworthy for a spend decision until phantom-sweep + re-consolidation runs. Playbook
      in `cefi_..._2026_05_27.md` §6I + `bucket_name_ssot_canonicalisation_2026_05_10`.

### TradFi MDPS reprocess + codex marker drift (folded in 2026-06-01, from deleted `mdps_tradfi_backfill_log_findings`)

- [ ] [DATA] P2. **Full tradfi processed_candles reprocess** (~712 days 2020→2026, ~2–4M objects) once backfills resume.
      All 4 code findings already SHIPPED on LDR: Finding 1 session-grid LOCF forward-fill (mdps@b67cddd + 7cb5fab +
      db233e2 — also fixed defi/swap_adapter), Finding 2 429-backoff (UTL `_upload_with_backoff_on_429`), Finding 3
      UNKNOWN-partition re-normalization (canonical_writer), Finding 4 faulthandler (UTL). Reprocess is the only
      remaining step — run with current code, part of the deferred backfill pass.
- [ ] [DOC] P3. **B2 codex marker reconciliation (HARD-RULE SSOT — do deliberately, NOT a find-replace).** Code emits
      carried-forward-bar markers as `staleness_seconds`>0 + `trade_count==0`; codex
      `honest-absence-downstream-handling.md` + `live-pipeline-architecture.md` (Category D) still describe a
      `zero_activity=True` / `ZERO_ACTIVITY_BAR` marker. Reconcile when the honest-absence SSOT is next revised — but
      FIRST rule on the model split: prediction Category-D emits NaN OHLC bars (different marker semantics) vs
      tradfi/cefi session-grid forward-fill (no NaN). The marker column may stay a boolean (renamed) rather than
      collapse to `staleness_seconds`. Verified `zero_activity` has no code consumers (pure doc drift, not a live
      breakage).

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

- [ ] [UI] P3. **Per-item Playwright pw:L2 never ran green in the slot env** (`libatk-1.0.so.0` missing on the EC2
      worker). Specs are written; the §5 full-suite pass (deployment-ui@7bbc270, 140/140) is the standing evidence. If a
      future change touches these surfaces, run the smoke suite where system deps exist before re-ticking.

## Why it matters

The log-archive durability gap is the only one with operational teeth: VM logs older than 14 days will expire because
nothing rolls them into the durable archive. Acceptable while the operator has explicitly deferred — flagged so it is a
known, not a surprise.

## Recommended decision

Leave deferred. Revisit the log-archive crons if/when long-horizon VM-log forensics are needed, and the CeFi migration
when the paid Tardis tier is activated.
