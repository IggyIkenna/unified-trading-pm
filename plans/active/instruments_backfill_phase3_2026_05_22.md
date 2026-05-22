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
- [ ] [VERIFY] P0. **IS-3.1.CeFi-V** — Post-launch: `instruments-store-cefi-prd` gains new rows; `available_at`
      populated; 0 `attempted_failed` after first poll cycle.

## Phase 2 — DeFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.DeFi** — Launched instr-backfill-defi-20260522 @ 35.200.66.186. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. instruments-service@fa93f45. deployment-service@4884aac. Relaunched after
      tarball rebuild — old run silently failed.
- [ ] [VERIFY] P0. **IS-3.1.DeFi-V** — `instruments-store-defi-prd` gains rows; 0 attempted_failed.

## Phase 3 — TradFi instruments forward-fill

- [x] ✅ [SCRIPT] P0. **IS-3.1.TradFi** — Launched instr-backfill-tradfi-20260522 @ 35.200.75.132. 2026-03-01→2026-05-22
      window. MANIFEST_PER_VM_SHARDS=true. instruments-service@fa93f45. deployment-service@4884aac. Relaunched after
      tarball rebuild — old run silently failed. **NOTE**: VM ran but wrote 0 records — same MalformedRowKeyError
      (chain='' in row_key for CBOE/CME/FX/ICE/NASDAQ/NYSE). Fix: instruments-service@4c1389d. Relaunch pending tarball
      rebuild.
- [ ] [VERIFY] P0. **IS-3.1.TradFi-V** — `instruments-store-tradfi-prd` gains rows; VIX instrument present; honest-gap
      coverage for pre-Polygon dates.

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
- [ ] [VERIFY] P0. **IS-3.1.Pred-V** — `instruments-store-pred-prd` gains rows; question groups canonicalized; 0
      attempted_failed. **NOTE**: Kalshi source blocked on credentials (see below).
- [ ] [BLOCKED-CREDENTIALS] P0. **IS-3.1.Pred-Kalshi** — Kalshi markets API returns 400 Bad Request on historical
      backfill requests. Operator confirmed BLOCKED-CREDENTIALS — need Kalshi account registration + API key.
      `     CREDENTIAL APPROVAL REQUEST — Kalshi markets adapter     Vendor: Kalshi (prediction markets exchange) — free tier with API key     What I need: Account registration at kalshi.com + API key (Bearer token)     Account to use: existing operator email or new account     Unblocks: prediction asset_group Kalshi question group instruments + IS-3.1.Pred-V verify     Without it: Kalshi adapter dormant; Polymarket (no key required) still writes pred instruments     `

---

## P3 lint backlog (absorbed from unused_import_audit_2026_05_18)

- [ ] [AGENT] P3. Fix F401 unused imports in
      `instruments-service/tests/scripts/test_canonicalize_defi_manifest_data_types_2026_05_16.py` (`contextlib`, `os`,
      `tempfile`, `pytest`) and `instruments-service/tests/scripts/test_reconcile_lending_indices_phantom.py`
      (`pytest`). Run `ruff check --select F401 --fix <files>` after verifying git status is clean. Issue:
      `plans/archive/issues/unused_import_audit_2026_05_18.md`.

## Pending relaunches after MalformedRowKeyError fix

- [x] ✅ [CODE] P0. **IS-3.1.chain-fix** — Fixed `MalformedRowKeyError` in orchestrator.py:3104 — conditional chain
      inclusion in row_key (omit when empty for CeFi/TradFi). instruments-service@4c1389d. ruff+basedpyright clean.
      Tarball rebuild in progress.
- [ ] [SCRIPT] P0. **IS-3.1.CeFi-Relaunch** — Tarball rebuild in progress (instruments-service@4c1389d). Relaunch 3×
      CeFi VMs: `--asset-group CEFI --start 2026-03-01 --end 2026-05-22`.
- [ ] [SCRIPT] P0. **IS-3.1.TradFi-Relaunch** — Relaunch TradFi VM:
      `--asset-group TRADFI --start 2026-03-01 --end 2026-05-22`.

## Temporary states + their canonical follow-up plans

- Items gated on `sports_master` Phase 3: **BLOCKED-UPSTREAM** until rename shipped; track in `sports_master` epic
  directly.
- CeFi + TradFi VMs ran but wrote 0 records due to MalformedRowKeyError — fix in progress (orchestrator.py:3104),
  relaunch after QG green (above items).
