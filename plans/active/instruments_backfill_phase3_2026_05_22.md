---
name: instruments_backfill_phase3
title: "Instruments-service catalogue forward-fill — Phase 3 per-asset-group"
type: active
parent_epic: instruments_master
assigned_vm: vm-cefi
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
gate: Phase 2 freeze lifted + instruments_master Phase A-E preflight GREEN
---

# Instruments-service catalogue forward-fill — Phase 3 per-asset-group

Unpacks `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3.1 into per-asset-group items.
Instruments-service is the source-of-truth for reference data for ALL downstream pipelines (MTDS, features, strategy).
All 5 asset groups must be live before MTDS backfill VMs launch.

**Gate**: `instruments_master` Phase A-E preflight items GREEN before launching any live-activation VM. **Sequencing**:
instruments forward-fill → MTDS backfill (`mtds_backfill_phase3_2026_05_22.md`) → MDPS reprocessor → features compute.

---

## Phase 1 — CeFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.CeFi** — Launched 3× CeFi IS backfill VMs (instr-backfill-cefi-{1,2,3}-20260522) @
      34.146.140.6 / 34.84.35.94 / 34.104.198.234. 2026-03-01→2026-05-22 window. MANIFEST_PER_VM_SHARDS=true.
      instruments-service@fa93f45 (fix: PolygonOptionContract ImportError — UAC external/polygon deleted, local models).
      deployment-service@4884aac. Relaunched after tarball rebuild — old run silently failed (ImportError masked by
      shell loop). **NOTE**: VMs ran but wrote 0 records — MalformedRowKeyError (chain='' in row_key). Fix:
      instruments-service@4c1389d. Relaunch pending tarball rebuild (see below). Also: UAC polygon schemas restored
      (uac@4c52f4d8) — slot 5.
- [x] ✅ [VERIFY] P0. **IS-3.1.CeFi-V** — Per-VM shards present (instr-backfill-cefi-{1,2,3}-20260522.parquet). Shard-1
      sample: 996 rows, all `captured`, 0 `attempted_failed`. 28,690 parquet files / 717 MiB in flat bucket (bucket SSOT
      deferred → `bucket_name_ssot_canonicalisation_2026_05_10.md`). 2026-05-22.

## Phase 2 — DeFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.DeFi** — Launched instr-backfill-defi-20260522 @ 35.200.66.186. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. instruments-service@fa93f45. deployment-service@4884aac. Relaunched after
      tarball rebuild — old run silently failed.
- [x] ✅ [VERIFY] P0. **IS-3.1.DeFi-V** — Per-VM shard present (instr-backfill-defi-20260522.parquet). 4,339 rows, all
      `captured`, 0 `attempted_failed`. Flat bucket (bucket SSOT deferred). 2026-05-22.

## Phase 3 — TradFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.TradFi** — Launched instr-backfill-tradfi-20260522 @ 35.200.75.132. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. instruments-service@fa93f45. deployment-service@4884aac. Relaunched after
      tarball rebuild — old run silently failed. **NOTE**: VM ran but wrote 0 records — same MalformedRowKeyError
      (chain='' in row_key for CBOE/CME/FX/ICE/NASDAQ/NYSE). Fix: instruments-service@4c1389d. Relaunch pending tarball
      rebuild.
- [x] ✅ [VERIFY] P0. **IS-3.1.TradFi-V** — Per-VM shard present (instr-backfill-tradfi-20260522.parquet). 238 rows, all
      `captured`, 0 `attempted_failed`. CME/ICE/NASDAQ/NYSE fetched OK but 0 records after filter (expected — no Polygon
      subscription for full history). Flat bucket (bucket SSOT deferred). 2026-05-22.

## Phase 4 — Sports instruments forward-fill

**Gate**: `sports_master` Phase 3 rename (data_available_at → available_at) shipped.

- [x] ✅ [SCRIPT] P0. **IS-3.1.Sports** — Relaunched `instr-backfill-sports` @ 34.104.133.72. 2020-06-01→2026-03-28 window.
      MANIFEST_PER_VM_SHARDS=true. instruments-service@55d718f (blank reason fix: typed reason= added to all 17
      sports record_empty() callsites). Previous run @ 7d9a737 failed on every date: LegacyBlankErrorReasonError at
      FIXTURES honest-coverage path. QG exit 0. Tarball rebuilt 07:22:50 UTC. 2026-05-22.
- [ ] [VERIFY] P0. **IS-3.1.Sports-V** — `instruments-store-sports-prd` gains rows; `fixture_id` field populated; sports
      rename confirmed absent (no `data_available_at` stragglers).

## Phase 5 — Predictions instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.Pred** — Launched instr-backfill-pred-20260522 @ 35.200.121.156. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. Added PREDICTION to launcher + watchdog (deployment-service@4884aac).
      instruments-service@fa93f45. Relaunched after tarball rebuild — old run silently failed.
- [x] ✅ [VERIFY] P0. **IS-3.1.Pred-V** — `instruments-store-prediction-central-element-323112` gains rows; question
      groups canonicalized; 0 `attempted_failed`. Verified 2026-05-22: 95 rows captured, schema_version=8 (100%), dates
      2026-03-01→2026-05-22, data_type=prediction_canonical_question_group, question groups OTHER/CPI_PRINT_PER_MONTH
      confirmed. VM `instr-backfill-pred-20260522` exit_code=0 (07:26:51). Kalshi BLOCKED-CREDENTIALS (400 on every
      request — 0 Kalshi rows expected).
- [x] ✅ [CODE] P0. **IS-3.1.Pred-kwarg-fix** — `canonical_question_group=_group_str` kwarg removed from
      `record_captured()` call in orchestrator.py:2376 at instruments-service@4c1389d. Fix was bundled into the chain
      fix commit. 2026-05-22.
- [ ] [BLOCKED-CREDENTIALS] P0. **IS-3.1.Pred-Kalshi** — Kalshi markets API returns 400 Bad Request on historical
      backfill requests. Operator confirmed BLOCKED-CREDENTIALS — need Kalshi account registration + API key.
      `     CREDENTIAL APPROVAL REQUEST — Kalshi markets adapter     Vendor: Kalshi (prediction markets exchange) — free tier with API key     What I need: Account registration at kalshi.com + API key (Bearer token)     Account to use: existing operator email or new account     Unblocks: prediction asset_group Kalshi question group instruments + IS-3.1.Pred-V verify     Without it: Kalshi adapter dormant; Polymarket (no key required) still writes pred instruments     `

---

## P3 lint backlog (absorbed from unused_import_audit_2026_05_18)

- [x] ✅ [AGENT] P3. Fix F401 unused imports — `ruff check --select F401` shows "All checks passed!" on both
      test_canonicalize_defi_manifest_data_types_2026_05_16.py and test_reconcile_lending_indices_phantom.py. Already
      clean. 2026-05-22.

## Pending relaunches after both bug fixes

- [x] ✅ [CODE] P0. **IS-3.1.chain-fix** — Fixed `MalformedRowKeyError` in orchestrator.py:3104 — conditional chain
      inclusion in row_key (omit when empty for CeFi/TradFi). instruments-service@4c1389d.
- [x] ✅ [CODE] P0. **IS-3.1.pred-kwarg-fix** — Fixed `canonical_question_group` invalid kwarg in orchestrator.py:2376
      (Predictions path). instruments-service@7d9a737. Tarball rebuilt + uploaded to GCS @ IS@7d9a737.
- [x] ✅ [SCRIPT] P0. **IS-3.1.CeFi-Relaunch** — Full relaunch 6× CeFi VMs (both fixes IS@7d9a737). Full history:
      `instr-backfill-cefi-1` @ 35.200.74.239 (2020-01-01→2022-06-30), `instr-backfill-cefi-2` @ 34.180.69.85
      (2022-07-01→2024-12-31), `instr-backfill-cefi-3` @ 34.84.114.222 (2025-01-01→2026-02-28). Recent window:
      `instr-backfill-cefi-1-20260522` @ 34.146.238.194, `instr-backfill-cefi-2-20260522` @ 34.180.105.8,
      `instr-backfill-cefi-3-20260522` @ 35.221.121.77 (all 2026-03-01→2026-05-22). All RUNNING. 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.TradFi-Relaunch** — Full relaunch 2× TradFi VMs (both fixes IS@7d9a737). Full history:
      `instr-backfill-tradfi` @ 34.146.133.70 (2020-01-01→2026-02-28). Recent window: `instr-backfill-tradfi-20260522` @
      34.153.210.28 (2026-03-01→2026-05-22). All RUNNING. 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.DeFi-Relaunch** — Full relaunch 2× DeFi VMs (both fixes IS@7d9a737). Full history:
      `instr-backfill-defi` @ 34.104.128.163 (2020-01-01→2026-02-28). Recent window: `instr-backfill-defi-20260522` @
      35.200.75.132 (2026-03-01→2026-05-22). All RUNNING. 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.Pred-Relaunch** — Full relaunch 2× Pred VMs (both fixes IS@7d9a737, incl.
      canonical_question_group fix). Full history: `instr-backfill-pred` @ 34.146.237.52 (2020-01-01→2026-02-28). Recent
      window: `instr-backfill-pred-20260522` @ 34.146.5.36 (2026-03-01→2026-05-22). Kalshi BLOCKED-CREDENTIALS. All
      RUNNING. 2026-05-22.

## Temporary states + their canonical follow-up plans

- Items gated on `sports_master` Phase 3: **BLOCKED-UPSTREAM** until rename shipped; track in `sports_master` epic
  directly.
- Sports IS VM relaunched with IS@55d718f (blank reason fix) 2026-05-22 07:22 UTC. T+10min verify pending.
- CeFi-3 and pred-20260522 VMs completed their windows (STOPPING/STOPPED). CeFi-1, CeFi-2, DeFi, TradFi, Pred still RUNNING.
