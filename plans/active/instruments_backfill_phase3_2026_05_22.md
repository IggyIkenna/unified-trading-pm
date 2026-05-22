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

- [ ] [SCRIPT] P0. **IS-3.1.Sports** — Launch instruments-service Sports live-activation VM per `instruments_master`
      Phase F-Sports. Trigger-driven: daily fixture re-poll + season-roll + transfer-window + weather. Sources: af / fs
      / sfi / us.
- [ ] [VERIFY] P0. **IS-3.1.Sports-V** — `instruments-store-sports-prd` gains rows; `fixture_id` field populated; sports
      rename confirmed absent (no `data_available_at` stragglers).

## Phase 5 — Predictions instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.Pred** — Launched instr-backfill-pred-20260522 @ 35.200.121.156. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. Added PREDICTION to launcher + watchdog (deployment-service@4884aac).
      instruments-service@fa93f45. Relaunched after tarball rebuild — old run silently failed.
- [ ] [VERIFY] P0. **IS-3.1.Pred-V** — `instruments-store-pred-prd-central-element-323112` gains rows; question groups
      canonicalized; 0 `attempted_failed`. NOTE: Kalshi BLOCKED-CREDENTIALS. NOTE: Original VM (fa93f45) failed with
      `canonical_question_group` unexpected kwarg in record_captured — fixed in 4c1389d. Relaunch pending (see below).
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

## Pending relaunches after MalformedRowKeyError fix

- [x] ✅ [CODE] P0. **IS-3.1.chain-fix** — Fixed `MalformedRowKeyError` in orchestrator.py:3104 — conditional chain
      inclusion in row_key (omit when empty for CeFi/TradFi). instruments-service@4c1389d. ruff+basedpyright clean.
      Tarball rebuild in progress.
- [x] ✅ [SCRIPT] P0. **IS-3.1.CeFi-Relaunch** — Relaunched 3× CeFi VMs with `--force` (instruments-service@4c1389d
      chain fix). `instr-backfill-cefi-1-20260522` @ 34.84.128.69, `instr-backfill-cefi-2-20260522` @ 34.180.72.34,
      `instr-backfill-cefi-3-20260522` @ 34.84.104.165. All RUNNING. 2026-03-01→2026-05-22. 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.TradFi-Relaunch** — Relaunched TradFi VM with `--force` (instruments-service@4c1389d
      chain fix). `instr-backfill-tradfi-20260522` @ 35.200.109.205. RUNNING. 2026-03-01→2026-05-22. 2026-05-22.
- [x] ✅ [SCRIPT] P0. **IS-3.1.Pred-Relaunch** — Relaunched Pred VM with `--force` (instruments-service@4c1389d; fixes
      both chain kwarg + canonical_question_group kwarg). `instr-backfill-pred-20260522` @ 34.146.5.36. RUNNING.
      2026-03-01→2026-05-22. Kalshi still BLOCKED-CREDENTIALS; Polymarket will capture. 2026-05-22.

## Temporary states + their canonical follow-up plans

- Items gated on `sports_master` Phase 3: **BLOCKED-UPSTREAM** until rename shipped; track in `sports_master` epic
  directly.
- CeFi + TradFi VMs relaunch DONE 2026-05-22 with instruments-service@4c1389d (chain fix). T+10min verify pending.
