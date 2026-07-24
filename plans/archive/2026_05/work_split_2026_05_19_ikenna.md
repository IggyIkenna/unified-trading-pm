---
doc_type: plan
title: Ikenna's daily work-split — 2026-05-19 (Cycle 2 Day-4; full backlog sweep — all May-23 + no-deadline)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service, features-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-19
type: coordination-doc
deadline: 2026-05-23
horizon: 4 calendar days (19 May → 23 May); Cycle 2 close + Cycle 3 paper-smoke
companion_to: plans/active/work_split_2026_05_19_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-19
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
effective_concurrent_slots: 8
estimate_calibration_note: "Full-sweep day. All May-23-deadline + no-deadline backlog allocated across 8 implementer

  slots. Ikenna owns ~231 cal AI-days (2× Harsh's 116). Carries every deferred item from

  May-15 / May-16 / May-18 splits. Critical blocker: operator must trigger write-pause

  window FIRST (L3 + L5 flips gate on it). Inventory as of 2026-05-19 08:26 UTC:

  462 total / 236 May-23 critical-path / 97 no-deadline = 333 spreadable.

  "
---

# Ikenna's daily work-split — 2026-05-19 (full backlog sweep)

> **Today = Cycle 2 Day-4 (last day).** Must close Cycle 2 by EOD: write-pause window + L3/L5 delegate-flip + archive
> old flat buckets + manifest re-sync + write-resume. Cycle 3 (paper-smoke) starts 2026-05-20.
>
> **P0 operator action required before slot 2 can proceed**: trigger MTDS + instruments-service write-pause (~30 min
> window). All delegate-flip pre-checks were green as of 2026-05-18 10:40 UTC.
>
> **Carries forward**: all open items from May-18 Ikenna split (slots 4/6/7/8 = 34 items), plus any May-15/16 deferrals
> still showing open in inventory (confirmed via inventory regeneration 2026-05-19).

---

## 🔴 TOP PRIORITY DISPATCH 2026-05-19 ~14:00 UTC — Repo consolidation push

Strategy + ML repo consolidations (filed earlier today, pre-cutover race for 2026-05-23) take priority over previously
assigned themes for slots 3-9. Existing themes DEFERRED to Cycle 3 (2026-05-20+ work-split) — original slot sections
preserved below with `🔴 THEME DISPLACED` banners; do not pick up the deferred items unless your reassigned phase ships
early.

**Plans (filed 2026-05-19; Phase 0 audits DONE; Phase 1+ unblocked)**:

- [`plans/active/strategy_repo_consolidation_2026_05_19.md`](./strategy_repo_consolidation_2026_05_19.md) — 12
  cal-AI-days. Pre-audit artifact:
  [`plans/active/issues/strategy_repo_consolidation_preaudit_2026_05_19.md`](./issues/strategy_repo_consolidation_preaudit_2026_05_19.md).
- [`plans/active/ml_repo_consolidation_2026_05_19.md`](./ml_repo_consolidation_2026_05_19.md) — 6 cal-AI-days. Pre-audit
  artifact:
  [`plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md`](./issues/ml_repo_consolidation_preaudit_2026_05_19.md).

**Reassignment table** (slots 3-9; slot 1 + slot 2 unchanged):

| Slot | Reassigned theme                                                                                                                                                                         | Plan                        | Phases      | Cal AI-days | Depends on     |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ----------- | ----------- | -------------- |
| 3    | strategy: pyproject conflict resolution → UAC/UTL schema prep → in-place scaffold                                                                                                        | strategy_repo_consolidation | 0.5 / 1 / 2 | ~2          | —              |
| 4    | strategy: subtree-merge + import-rewrite (colocated_engine.py FIRST — May-23 critical-path consumer)                                                                                     | strategy_repo_consolidation | 3 / 4       | ~4          | slot 3 Phase 2 |
| 5    | strategy: UTL lifts — `ConfigReloaderBase` (4× ~688 LOC) + `KillSwitchBusSubscriberBase` (4× ~80 LOC)                                                                                    | strategy_repo_consolidation | 5           | ~2          | slot 4 Phase 4 |
| 6    | strategy: Phase 6 parity (boot + QG + functional) → Phase 7 archive 3 source repos                                                                                                       | strategy_repo_consolidation | 6 / 7       | ~2          | slot 4 Phase 4 |
| 7    | strategy: Phase 8A deployment-service sweep (~90 hits, Terraform destroy/apply sequencing)                                                                                               | strategy_repo_consolidation | 8A          | ~3          | slot 6 Phase 7 |
| 8    | **ML consolidation full plan** (single-slot ownership, all 10 phases — reassigned 2026-05-19 ~15:30 UTC from slot 9; slot 8 already shipped Phase 0+1 organically)                       | ml_repo_consolidation       | 0–10        | ~6          | —              |
| 9    | 🟢 **STANDING DOWN** — slot not booted today (operator opened only 8 slots). Worktree reset to LDR + ml-service worktree provisioned (`tab/ikennaigboaka/9`). Available for future boot. | —                           | —           | —           | —              |

**NOTE on strategy Phase 9 + 10** (codex sweep + workspace QG): previously assigned to slot 8 before ML reassignment.
Now PENDING — slot 1 main will dispatch in next reallocation pass (likely slot 3 once Phase 0.5+1+2 ships, or slot 6
after Phase 7 archive).

**Dependency DAG** (revised 2026-05-19 ~15:30 UTC):

```
Slot 3 (Phase 0.5+1+2)  →  Slot 4 (Phase 3+4)  →  Slot 5 (Phase 5)         ┐
                                              →  Slot 6 (Phase 6+7)        ┤→  Slot 7 (Phase 8A)  →  PENDING (Phase 9+10 codex sweep)
Slot 8 (ML full plan, independent — was slot 9)
Slot 9 (standing down — not booted)
```

**Critical-path callout**: Slot 4 must rewrite `e2e-testing/scripts/defi/colocated_engine.py` FIRST in Phase 4 (a)
sed-sweep. This file is the primary May-23 promote-CLI path per CLAUDE.md; breaking it mid-cutover blocks live trading.
Verify it boots green BEFORE proceeding to the other 6 external-consumer rewrites.

**Auto-flip BLOCKED-CUTOVER**: if slot 6 Phase 6 parity gate is RED at 2026-05-22 EOD, plans auto-flip to
`BLOCKED-CUTOVER` and Phase 7 archive defers to post-cutover. Sub-packages remain merged (correctness preserved), source
repos remain un-archived. No late-binding hacks.

**Outstanding ops on this push**:

- ✅ Operator decision on ml-service flat-deps rule (RESOLVED 2026-05-19 ~14:00 UTC — Option 2 picked, single flat-deps
  Docker image).
- ✅ Per-slot ping files updated (slot_3.md through slot_9.md notified of theme change).

**Slot 2 overflow rule**: slot 2's code_freeze Phase 2.6 close is operator-gated. If slot 2 finishes early (write-pause
completes + L3/L5 flips landed), overflow capacity goes to slot 7 (Phase 8A) — the largest single piece of remaining
work.

---

## Hard rules

1. **Write-pause = operator-triggered.** Do NOT pause services autonomously. Slot 2 waits on operator go-ahead before
   executing L3/L5 flips.
2. **Half-1 + Half-2 discipline**: every shippable unit = (a) commit + push, then (b) flip checkbox with `docs(plans):`
   prefix commit, IN SAME AGENT TURN.
3. **Slot 1 precedence**: only slot 1 main edits `master_to_live_defi_2026_05_23.md`.
4. **Conflict check**: `git fetch` before every execution-service / deployment-api / UTL commit.
5. **pvl-p18a monitor**: Harsh dedicated slot is polling; Ikenna main does NOT poll.
6. **GCS backfill ≥1 week**: requires operator approval. <1 week = pre-authorized.

---

## Slot stack — ~231 cal AI-days across 8 implementer slots

> **🔴 SLOT FREEZE 2026-05-20 (operator directive)**: Per new data-pipeline correctness HARD RULE
> ([CLAUDE.md](../../cursor-configs/CLAUDE.md) § "Data Pipeline Correctness Is The Heartbeat" +
> [codex SSOT](/codex/02-data/data-pipeline-correctness-hard-rule.md)), slots **6, 7, 9** FROZEN from prior themes
> (deployment UI / simulation scenarios / promote workflow) until mega-audit Phase A1-A6 GREEN for their asset_groups.
> All 3 were doubling down on layer-N+1 work on top of a workspace with only 3.66% in-scope cells confirmed `captured` +
> 0% manifest rows at v8. Reassigned to A3 remediation per epics + A6 BATCH_ONLY remediation. See per-slot sections
> below for new scope.

| Slot      | Theme                                                                                                                                         | Cal AI-days | Plans owned                                                                    |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------ |
| 1         | Main orchestrator (continuous, uncounted) + mega-audit Phase A coordination                                                                   | —           | This LEDGER + mega_audit_and_plan_beefup_progression                           |
| 2         | code_freeze Phase 2.6 close — KEEP (layer-3 manifest substrate)                                                                               | ~35         | code_freeze §2.6                                                               |
| 3         | code_freeze Phase 2.0–2.5 gaps + batch_live_symmetry T1-3 — KEEP (layer-3)                                                                    | ~35         | code_freeze §2.0–2.5, batch_live_symmetry                                      |
| 4         | api_keys Phase 3–4 + defi_recursive_borrow Phase 3–4 — KEEP (credentials unblock data)                                                        | ~34         | api_keys, defi_recursive_borrow                                                |
| 5         | writegate Phase 6.6/6.7 + live_pipeline P3-5 — KEEP + own v8-backfill extension                                                               | ~30         | writegate (+ NEW v8-backfill phases), live_pipeline                            |
| **6**     | **🔴 FROZEN — was deployment_ui_lifecycle_tabs. REASSIGNED to A3 DeFi MISSING_EXPECTED remediation**                                          | ~30         | defi_upstream_46day_full_backfill (extended)                                   |
| **7**     | **🔴 FROZEN — was sim_scenarios + defi_master P2-3. REASSIGNED to A3 Sports + A2 off-season gap**                                             | ~27         | sports_master (extended)                                                       |
| 8         | defi_catalogue close — KEEP (layer-1 reference)                                                                                               | ~29         | defi_catalogue, defi_simulation_realism, dex_perp_and_venue_data               |
| **9**     | **🔴 FROZEN — was batch_live_symmetry T4-7 + cme_polymarket_arb + promote_workflow. REASSIGNED to A3 Prediction/TradFi/CeFi + A6 BATCH_ONLY** | ~31         | predictions_master, tradfi_master, cefi_master, batch_live_symmetry (extended) |
| **Total** |                                                                                                                                               | **~251**    |                                                                                |

### Slot 6 — REASSIGNED 2026-05-20 to A3 DeFi MISSING_EXPECTED remediation (~30 cal AI-days)

**Why frozen**: deployment-UI lifecycle restructure is layer-N+1 — surfaces data status to operator while the data
underneath is RED (3.66% captured + 0% v8).

**New scope**:

1. Walk every `MISSING_EXPECTED` cell in `plans/audit/results/manifest_divergence_2026_05_20.parquet` filtered to
   `asset_group=='defi'` (184,512 cells). Group by (venue, data_type).
2. For each (venue, data_type) pair with >100 missing cells, root-cause: handler wired in MTDS orchestrator scope? IS
   catalogue exposing required `InstrumentRecord`s? Credentials provisioned per `External Data Is Always Available`?
3. Fix root cause + run backfill. Manifest-verify v8 rows landing per new writegate v8 phases.
4. Re-run A3 against affected cells; assert 0 `MISSING_EXPECTED` post-fix.

**Plan-of-record**: `defi_upstream_46day_full_backfill_2026_05_16.md` (extended 2026-05-20).

### Slot 7 — REASSIGNED 2026-05-20 to A3 Sports + A2 off-season gap (~27 cal AI-days)

**Why frozen**: simulation_scenarios_topology assumes data exists. Sports A3 shows 25,652 MISSING_EXPECTED across ALL 11
bookmaker × data_type combos — simulation fits nothing.

**New scope**:

1. Build sports off-season calendar gap fix per A2 sidecar `expected_coverage_calendar_decisions_2026_05_20.md` §
   "Sports off-season + no-fixture calendars". Pair with IS fixture data per recommendation.
2. Re-run A2 + A3 against sports cells; honest-down off-season days (not real MISSING_EXPECTED).
3. For residual real MISSING_EXPECTED cells, walk each (bookmaker, data_type) + root-cause per slot-6 recipe.
4. Manifest-verify v8 rows for sports.

**Plan-of-record**: `epics/sports_master.md` (extended 2026-05-20).

### Slot 9 — REASSIGNED 2026-05-20 to A3 Prediction/TradFi/CeFi + A6 BATCH_ONLY (~31 cal AI-days)

**Why frozen**: promote_workflow + cme_polymarket_arb both presume captured + verified data exists. A3 shows 7,115
TradFi + 3,442 Prediction + 16,171 CeFi MISSING_EXPECTED — promotion cannot honestly happen.

**New scope**:

1. **Prediction (KALSHI/POLYMARKET trades — 3,442 cells)**: root-cause + backfill per `epics/predictions_master.md`
   extension.
2. **TradFi (ICE/CME/NYSE/NASDAQ/YAHOO/FX — 7,115 MISSING + 1,546 ATTEMPTED_FAILED)**: root-cause + backfill per
   `epics/tradfi_master.md` extension. Investigate YAHOO_FINANCE ATTEMPTED_FAILED concentration.
3. **CeFi (OKX/COINBASE/UPBIT + DERIBIT/BINANCE-FUTURES/BYBIT/ASTER chains — 33k MISSING+FAILED)**: per
   `epics/cefi_master.md` extension.
4. **A6 BATCH_ONLY remediation (13 cells)**: build live equivalents per A6 CSV. Wire via existing
   `batch_live_symmetry_2026_05_10.md`.

**Plans-of-record**: `predictions_master`, `tradfi_master`, `cefi_master`, `batch_live_symmetry` (all extended
2026-05-20).

---

### Slot 1 — Main orchestrator (continuous)

1. **Write-pause coordination** — once operator signals ready: (a) confirm all delegate-flip code on LDR, (b) cross-ping
   Harsh-main to suspend any conflicting commits, (c) ack slot 2 to proceed.
2. **Cross-side ping triage** — respond to any outstanding pings in `_agent_pings.md` +
   `ikenna_orchestrator/_agent_pings.md`. May-18 12:17 UTC ping to Harsh (features_tick_observation_audit
   - StrategyDecisionContext correlation_id) needs Harsh-side ack — check and follow up.
3. **EOD inventory regenerator** — re-run after all slots report DONE.
4. **Master plan continuous-verification matrix** — flip `Last verified` per item shipped today.
5. **Harsh-side S3-S20 SUSTAIN sweep coordination** — ensure no surface conflicts.

---

### Slot 2 — code_freeze Phase 2.6 close (write-pause window) — ~35 cal AI-days

**BLOCKER**: wait for operator write-pause signal before executing L3/L5 flips.

**Plan**: `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.6.

```bash
# Pre-write-pause (can do now while waiting):
cd .tabs/2/unified-trading-library
rg "get_bucket_name" --type py --glob '!.venv*' --glob '!tests'
# Identify the 36+ L3 consumers in cloud_constants.py et al.
```

1. - [x] ✅ **L3 flip — UTL `get_bucket_name` → `resolve_bucket_name`** (36+ consumers in
         `unified_trading_library/cloud_interface/cloud_constants.py` + wrappers). Run QG. Push. (refactor 0.4×, ~8 =
         3.2 cal) — UTL@f5e472e8 pushed to LDR 2026-05-19. Cherry-picked from slot2/l3-flip-staged@5418b1a7 onto current
         HEAD (gcs_blob_ops); no file conflicts; QG pre-verified (3755 passed at stage time).
2. - [x] ✅ **L5 flip — deployment-api `_BUCKET_TEMPLATES`** → `resolve_bucket_name()`. Run QG. Push. (refactor 0.4×, ~3
         = 1.2 cal) — deployment-api@a15f425 pushed to LDR 2026-05-19. Rebased over 8 incoming commits cleanly; foreign
         dirty files (log_stream.py + uv.lock) stashed+popped safely.
3. - [ ] **Write-resume verification** — after operator redeploys: confirm manifest rows landing in env-tiered paths via
         `gcloud storage ls gs://{env-tiered-bucket}/` spot-check. (infra 0.8×, ~2 = 1.6 cal)
4. - [ ] **Archive old flat buckets** — run
         `bash deployment-service/scripts/archive-flat-buckets.sh    --env prod --cloud both` (30-day hold, not delete).
         (infra 0.8×, ~2 = 1.6 cal)
5. - [x] **GAP-2.0.B** — Confirm Stage 0 drain covers BOTH GCP + AWS VM fleets. Doc update. ✅ pm@`2af45259`
6. - [x] **GAP-2.0.C** — Update CLAUDE.md "No fire-and-forget" HARD RULE with pre-migration drain addendum. ✅
         pm@`2af45259`
7. - [x] ✅ **Reconcile phantoms** — run
         `python scripts/reconcile_phantom_manifest_rows_all.py    --asset-group cefi --dry-run` + repeat per
         asset_group. (infra 0.8×, ~2 = 1.6 cal) All 5 asset_groups show **0 phantoms** as of 2026-05-19: cefi=0/1290706
         (128k prefixes, 34min), defi=0/311602 (89k prefixes, 23min), tradfi=0/245907, sports=0/559961,
         prediction=0/14403. Axes 7-9 fixes shipped 2026-05-13 (IS@1a62547) eliminated all false-positives from previous
         2026-05-11 run. Manifest is clean across all 5 groups.
8. - [ ] **Phase 2 freeze gate** — flip all remaining `- [ ]` gate items in code_freeze §2. Push `docs(plans):` flip
         commit. (design 0.6×, ~1 = 0.6 cal)

---

### Slot 3 — code_freeze Phase 2.0–2.5 gaps + batch_live_symmetry Tabs 1–3 — ~35 cal AI-days

> **🔴 THEME DISPLACED 2026-05-19 ~14:00 UTC** — see top-of-file § "🔴 TOP PRIORITY DISPATCH". Slot 3 NEW theme:
> **strategy_repo_consolidation Phase 0.5 + 1 + 2** (pyproject conflict resolution → UAC/UTL schema prep → in-place
> scaffold) — ~2 cal-AI-days, unblocks slot 4. Below items DEFERRED to Cycle 3 work-split (2026-05-20+). Do NOT pick
> them up unless your Phase 2 scaffold ships before EOD.

**Part A — code_freeze remaining Phase 2 gaps** (open `[GAP]` items not covered by slot 2):

1. - [x] ✅ **GAP-2.2.B** — Update CLAUDE.md "Honest absence" HARD RULE with Phase 2.2 GCS migration reference. (design
         0.6×, ~1 = 0.6 cal) — PM@`22d632c4`
2. - [x] ✅ **GAP-2.3.A** — Append Phase 2.X OHLCV legacy filename rename sub-section to code_freeze plan. (design 0.6×,
         ~2 = 1.2 cal) — PM@`1467b823`
3. - [x] ✅ **GAP-2.3.B** — Audit features-service readers for `ticks.parquet` literal path references. (research 1.2×,
         ~2 = 2.4 cal) — PM@`1467b823` (no breaking changes; 3 bundled-type paths safe)
4. - [ ] [BLOCKED-OPERATOR-APPROVAL] **Phase 2.5** — Run `manifest_cross_asset_rescan_design_2026_05_08.md` cross-asset
         `--apply-flips` sequence per the plan. (infra 0.8×, ~3 = 2.4 cal) cefi/defi/tradfi already done 2026-05-13.
         Sports (99,620 phantoms) + prediction (50) require operator approval per ≥1 week backfill rule. Launcher
         `launch-cross-asset-rescan-vm.sh` **now complete** with `--pass 1|2|3|4` sequential enforcement
         (deployment-service@880bc3a
   - instruments-service@5a0b115, 2026-05-19). Secondary blocker RESOLVED. Unblocks when operator approves
     sports/prediction apply-flips (operator [ack] required — use `bash launch-cross-asset-rescan-vm.sh --apply cefi`).
5. - [x] ✅ **gcs_migration_bundle Phase 2.5 + Phase 3 RELAUNCHED (bug fix)** — Phase 2.5 (OHLCV ticks.parquet →
         {instrument_id}.parquet rename) implemented + 50 tests green + dry-run verified (ohlcv_legacy_filename=1
         detected on real CeFi data). PM@`916742464`. Phase 3 fleet first launched 11:23 UTC, crashed on
         `gcloud    storage ls` (no prefix-match support for hive paths); relaunched 11:58 UTC with fix:
         `gsutil ls -r    **wildcard + graceful zero-match. Also fixed startup script: Python crash no longer prevents shutdown.    31 VMs RUNNING asia-northeast1-c as of 12:06 UTC. PM@`726a3bf` (gsutil fix), deployment-service@`5b917c1`   (startup-shutdown fix). Phase 3 IN-PROGRESS — monitoring VM logs. Phases 6/9 unblock after phantom gate.    **+Phase 7.6 (operator-directed follow-on)** ✅ UTL`gcs_blob_ops.py`helpers shipped —   `unified-trading-library@63f6ebc7`+`unified-trading-pm@253ad8cbb`(2026-05-19). Migration script    refactored to use UTL gcs_copy_object/gcs_delete_object/gcs_describe_object instead of inline GCS client.    New codex doc`/codex/05-infrastructure/gcs-object-operations.md` +
         CLAUDE.md rule added. 250× perf gain.

**RE-DISPATCH 2026-05-19 (Part A items 1-3+5 ✅; item 4 BLOCKED-OPERATOR; new pickup per
[`pings/slot_3.md`](../../ikenna_orchestrator/pings/slot_3.md))**:

> ✅ **CO-DUTY CLOSED 2026-05-19 18:55 UTC**: Phase 3 VM fleet TERMINATED (31/31); Phase 3.6 re-audit ALL 5 CONFIRMED 0
> phantoms. Axis-10 fix (instruments-service@8accb30) + re-audit results: cefi 0/1,290,707 ✅ / defi 0/311,602 ✅ /
> tradfi 0/245,907 ✅ / sports 0/559,961 ✅ / prediction 0/14,403 ✅. Operator action pending: Phase 3 step 7 sign-off
> (HUMAN-ONLY checkboxes in gcs_migration plan § Phase 3). PM@cd9c8027a.

10. - [x] ✅ **code_freeze GAP-2.4.A + Phase 2.4 cross-cloud parity audit** — verify aws_migration_defi_first writes use
          UAC `resolve_bucket_name()` SSOT; build cross-cloud parity matrix per DeFi data_type (🟢/🟡/🔴); sweep
          GAP-2.4.B/C/D pre-readiness checklist. Audit + write-only this session (do NOT run migrations). Runs in
          parallel with Phase 3 VM monitoring. (research 1.2×, ~8 baseline = ~9.6 cal AI-days) — ✅ PM@30b2ce193; 8/8
          DeFi data_types cross-cloud parity 🟢 clean; GAP-2.4.A flipped in code_freeze plan (backfilled 2026-05-19)

**Part B — batch_live_symmetry Tabs 1–3** (plan at 34%, 19.7 cal left):

Read `batch_live_symmetry_2026_05_10.md` for open Tab 1/2/3 items. Tab 1 = codex SSOT batch, Tab 2 = UAC + UTL J1
helper + L7 sweep, Tab 3 = QG STEPs L2/L3/L7.

6. - [x] ✅ **Tab 1 — codex SSOT batch** (cefi-batch-live.md + mode-axis-discipline.md). ~200 lines each. (design 0.6×,
         ~5 = 3.0 cal) — batch_live_symmetry §Tab 1 all ✅; PM@`6153d9ea` (cefi-batch-live + mode-axis-discipline
         shipped) + PM@`9df278ef` (batch-live-architecture updated); full-exec verified: both files present + STEP
         5.75/5.76/5.77/5.78 in base-service.sh
7. - [x] ✅ **Tab 2 — UAC J1 helper + L7 sweep** per batch_live_symmetry plan §Tab 2. (brand-new 1.0×, ~5 = 5.0 cal) —
         batch_live_symmetry §Tab 2 all ✅; UAC@`01c1b59` (BatchExecutionMode + RECON_GREEN_THRESHOLDS + J1 stub) +
         exec@`b30167e2` (node_builder migrated); L7 fix-list documented for Tab 5/MDPS owner
8. - [x] ✅ **Tab 3 — QG STEPs L2/L3/L7 AST sweeps** per batch_live_symmetry plan §Tab 3. (refactor 0.4×, ~4 = 1.6 cal)
         — batch_live_symmetry §Tab 3 all ✅; PM@`5772f57b` (STEP 5.75+5.76) + PM@`fac14af3` (STEP 5.77 L2) +
         PM@`882faaa0` (STEP 5.78 L3); 0 workspace violations pre-flight; L7 sweep complete
9. - [x] ✅ **Plan checkboxes flip** for all items shipped. (0.5 cal) — PM@`450967d4` all slot-3 checkboxes flipped;
         gcs_migration Phase 4 + batch_live_symmetry Tabs 1-3 verified DONE

---

### Slot 4 — api_keys Phase 3–4 + defi_recursive_borrow Phase 3–4 — ~34 cal AI-days

> **🔴 THEME DISPLACED 2026-05-19 ~14:00 UTC** — Slot 4 NEW theme: **strategy_repo_consolidation Phase 3 + 4**
> (subtree-merge + internal import-rewrite + unified CLI). **CRITICAL: rewrite
> `e2e-testing/scripts/defi/colocated_engine.py` FIRST** in Phase 4 (a) sed-sweep — primary May-23 promote-CLI path.
> Verify it boots green BEFORE the other 6 external-consumer rewrites. Pre-audit § (b) has exact file:line list. ~4
> cal-AI-days. Blocked-on: slot 3 Phase 2 scaffold lands first.

**Part A — api_keys_wallets_accounts_readiness Phase 3 (Copper) + Phase 4 (DeFi mainnet)** (plan at 63%, 23.7 cal left):

1. - [ ] **Phase 3.A — Copper real-fund-movement test** — Execute small-amount transfer to confirm Copper API is live.
         Verify idempotency + response schema. (infra 0.8×, ~2 = 1.6 cal)
2. - [x] ✅ **Phase 3.B — CEFFU integration** — Start CEFFU KYB / API key sub-deliverables. Read api_keys §Phase 3.B for
         the sub-task list. (brand-new 1.0×, ~4 = 4.0 cal) — 3.B.3 stub shipped execution-service@027a8153b (OES +
         direct-custody shape-compatible; factory-registered; raises NotImplementedError until POD delivers spec
         June-1); 3.B.1/3.B.2 HUMAN; 3.B.4/3.B.5 blocked on human steps; (backfilled 2026-05-19)
3. - [x] ✅ **Phase 4.A — UAC DeFi wallet schema** — `WalletConfig` + `ChainWallet` + per-chain RPC wiring. (brand-new
         1.0×, ~3 = 3.0 cal) — uac@d721b6a (2026-05-12; WalletProvisioningConfig + SigningSurface + SpendingCaps + 27
         tests; backfilled 2026-05-19)
4. - [x] ✅ **Phase 4.B — PBM position-health endpoint** — per api_keys §4.C.B. (brand-new 1.0×, ~2 = 2.0 cal) —
         uac@1fababa + pbm@e93e3e5 (2026-05-15; GET /positions/health + PositionHealthSnapshot + 5s cache + 11 tests;
         backfilled 2026-05-19)
5. - [x] ✅ **Phase 4.C — UTL shared pre-flight helper** — per api_keys §4.C.C. (brand-new 1.0×, ~2 = 2.0 cal) —
         utl@b1b05343 (2026-05-15; run_wallet_preflight_checks 5-layer short-circuit + audit-log row; 21 tests QG green;
         backfilled 2026-05-19)
6. - [x] ✅ **Phase 4.D + 4.E — execution-service + DART wire-in** — per api_keys §4.C.D + 4.C.E. (brand-new 1.0×, ~1.5
         = 1.5 cal) — execution-service@754b22bf9 (2026-05-15; \_enforce_wallet_preflight + WalletPreflightRegistry +
         /instruction/precheck; 17 tests; backfilled 2026-05-19)

**Part B — defi_recursive_borrow Phase 3–4** (plan at 75%, 10.5 cal left):

7. - [x] ✅ **Phase 3 — Sim contract integration** — wire Aave/Compound flash-loan receiver into sim engine. Read plan
         for open items. (design 0.6×, ~4 = 2.4 cal) — strategy-service@44a8afc (2026-05-17;
         CARRY_RECURSIVE_BORROW_LENDING_ONLY + PERP_HEDGED builders in BUILDERS_BY_ARCHETYPE; tracer math
         net_apr_recursive + net_apr_with_perp_funding; QG green; backfilled 2026-05-19)
8. - [x] ✅ **Phase 4 — Per-family backtest scenarios** — carry + recursive-borrow scenario sets. (design 0.6×, ~6 = 3.6
         cal) — deployment-service@6dfac41 (2026-05-17; RecursiveLeverageReceiver.sol Option A + 11 foundry tests;
         security review passed; mainnet deploy BLOCKED-OPERATOR-DECISION wallet key human-only; backfilled 2026-05-19)
9. - [x] ✅ **Plan flips** for all shipped items. (0.5 cal) — backfill commit this turn
10. - [x] ✅ **Phase 4.C — CCTP bridge adapter** — api_keys §4.C (discovered open during boot, implemented this
          session). uac@a0238d3 + execution-service@05bdad628 (2026-05-19; CCTPBridgeConnector full: burn-and-mint USDC
          bridge, 10 EVM chains, 5 CCTP error codes, testnet_contracts.yaml addresses, 25 unit tests green)
11. - [x] ✅ **Batch-32 method-size refactor — instruments/factory_cefi_defi.py** — all 3 violations (235L, 249L, 95L)
          extracted to private helpers; all public methods now ≤50L; removed from FUNCTION_SIZE_EXTRA_EXCLUDES
          allowlist. execution-service@ca97b10db (2026-05-19; allowlist 12→11, slot-4 cumulative 98 files cleared)
12. - [x] ✅ **Batch-32 method-size refactor — config/grid_v2_registry.py** — all 3 violations (130L, 163L, 205L)
          extracted to private helpers; all public methods now ≤50L; removed from FUNCTION_SIZE_EXTRA_EXCLUDES
          allowlist. execution-service@911b4ffde (2026-05-19; allowlist 11→10, slot-4 cumulative 99 files cleared)
13. - [x] ✅ **Batch-32 method-size refactor — config/grid_generator_v2.py** — all 3 violations (157L, 199L, 215L)
          extracted to 7 additional private helpers (\_build_venue_section, \_build_grid_metadata,
          \_load_strategy_components, \_update_stats, \_accumulate_strategy_configs, \_finalize_gen_output,
          \_setup_gen_context); all public methods now ≤50L; removed from FUNCTION_SIZE_EXTRA_EXCLUDES allowlist.
          execution-service@f27e5fc13 (2026-05-19; allowlist 10→9, slot-4 cumulative 100 files cleared)

**RE-DISPATCH 2026-05-19 (items 1-13 ✅; new pickup per
[`pings/slot_4.md`](../../ikenna_orchestrator/pings/slot_4.md))**:

14. - [x] ✅ **Batch-32 continuation — execution-service allowlist 9→0** — continue same extraction pattern as items
          11-13. Per file: identify >50L methods, extract to private helpers, public methods ≤50L, remove from
          `FUNCTION_SIZE_EXTRA_EXCLUDES`, run QG green, commit + flip checkbox in same agent turn. Once
          execution-service allowlist is 0, scan unified-trading-api/ml-inference/ml-training/strategy-service
          allowlists; pick smallest for next stream. Cumulative target 100 → 109+ by EOD. If recurring pattern across
          services, add one-line codex note to `/codex/06-coding-standards/method-size.md`. (refactor 0.4×, ~12 baseline
          = ~5 cal AI-days) — execution-service@23d8401c6 (8 commits; allowlist now empty `()`; codex stub created PM
          this commit; next stream: scan strategy-service allowlist)

---

### Slot 5 — writegate Phase 6.6/6.7 + live_pipeline Phase 3–5 — ~30 cal AI-days

> **🔴 THEME DISPLACED 2026-05-19 ~14:00 UTC** — Slot 5 NEW theme: **strategy_repo_consolidation Phase 5** — UTL lifts:
> (1) `ConfigReloaderBase` to absorb 4× duplicated `config_reloaders.py` (152/112/112/312 LOC, ~688 LOC total), (2)
> `KillSwitchBusSubscriberBase` to absorb 4× duplicated kill-switch subscriber boilerplate (~80-100 LOC each). Two UTL
> PRs + one strategy-service PR removing local copies. ~2 cal-AI-days. Blocked-on: slot 4 Phase 4 (imports rewritten
> before lifts).
>
> **🟢 STATUS 2026-05-19 ~21:30 UTC** — Phase 4 QG gate DONE (strategy-service@7265289a). Phase 5 UTL lifts DEFERRED to
> post-cutover (UTL changes too risky 4 days before May-23 live DeFi launch). Phase 6 boot+QG parity ✅ (12/12 pairs,
> strategy-service@91f701b0). Phase 7 pre-steps done: DEPRECATION_NOTICE in 3 repos, workspace-manifest updated,
> operator ping filed (PM@e88149a28). Awaiting operator `gh repo archive` for Phase 7 completion. Phases 8A/9/10 blocked
> on Phase 7.
>
> **🔴 STATUS 2026-05-20 — UN-DEFER per operator direction** — Phase 5 UTL lifts REVERSED back to ACTIVE-NOW (cancels
> the never-created post-cutover successor plan). Operator rationale: carrying 4× `config_reloaders.py` + 4×
> `kill_switch_bus_subscriber.py` duplication into cutover defeats the consolidation's SSOT premise; UTL bump is
> additive (patch, no removals), callsites confined to strategy-service after Phase 3 subtree-merge, so blast radius
> bounded. Plan body un-deferred in commit `94c709585`. **Slot 5 picks up immediately** per
> `ikenna_orchestrator/pings/slot_5.md` 2026-05-20 dispatch. Source-repo worktrees (risk/position/pnl across all 11
> tabs + main non-tab) removed 2026-05-20 per Phase 7 archive prep — slot 5 works on strategy-service sub-packages only.
> Compose-with: ML consolidation slot 8 (if ml-service typed-config shapes converge, `ConfigReloaderBase` becomes 5-way
> SSOT — see `pings/slot_8.md` 2026-05-20 note).

**Part A — writegate Phase 6.6/6.7** (plan at 52%, 11.5 cal left):

1. - [x] ✅ **Phase 6.6 — ml-training-service emission wiring** — `_check_emission_policy()` + BLOCK_CRITICAL gate in
         `store_model()`; `training_completeness_fraction` param; 5 tests. — ml-training-service@ff20617 (pre-shipped
         2026-05-13)
2. - [x] ✅ **Phase 6.6 — ml-inference-service emission wiring** — `_check_emission_policy()` +
         `_filter_by_emission_policy()`
   - `_upload_one_mode()` in `prediction_publisher.py`; 4 STRICT_FAIL tests. — ml-inference-service@9fb5d50 (pre-shipped
     2026-05-13)
3. - [x] ✅ **Phase 6.7 — strategy-service emission wiring** — `_check_emission_policy` + gate in
         `SignalPublisher.publish()`; 4 tests. — strategy-service@88eb085 (pre-shipped 2026-05-13)
4. - [x] ✅ **Phase 6.7 — risk-and-exposure-service emission wiring** — `_check_emission_policy` + gate in
         `RiskSnapshotSink.write()`; 4 tests. — risk-and-exposure-service@df4849f (pre-shipped 2026-05-13)

**Part B — live_pipeline_mtds_mdps_features Phase 3–5** (15.0 cal budget):

Read `live_pipeline_mtds_mdps_features_2026_05_08.md` for remaining open items. Focus on:

5. - [x] ✅ **Phase 3 MTDS real-time adapter** — all WSFeedConnectors shipped across defi/cefi/tradfi/sports/prediction;
         Phase 3.5 COMPLETE. — MTDS@99fc7b3 (pre-shipped 2026-05-17)
6. - [x] ✅ **Phase 4 MDPS live consumer** — LiveStreamAggregator + 7 Protocol adapters + consumer wiring shipped. —
         mdps@0068b2f (pre-shipped 2026-05-11)
7. - [x] ✅ **Plan flips** for all shipped items + downstream AUDIT P0 items (ml-training NaN-fill + ml-inference
         gap-blocking). (0.5 cal) — live_pipeline Phase 3+4 [x] confirmed; writegate audit items ml-training@1760 +
         ml-inference@1764 already [x]; backfilled PM@f46c26a50 2026-05-19.

---

### Slot 6 — deployment_ui_lifecycle_tabs (full 6-tab restructure) — ~30 cal AI-days

> **🔴 THEME DISPLACED 2026-05-19 ~14:00 UTC** — Slot 6 NEW theme: **strategy_repo_consolidation Phase 6 + 7**. Phase 6
> = symmetry / parity validation (boot parity for every {operation × asset_group}, QG parity vs source-repo baselines,
> functional parity 7-day live-window sample per surface via `scripts/dev/strategy_parity_diff.py`). Phase 7 =
> `gh repo archive` of risk + position + pnl source repos once parity green. Operator-gated `gh archive` step — file
> ping in `_agent_pings.md`. ~2 cal-AI-days. Blocked-on: slot 4 Phase 4. **Hard stop**: do NOT proceed to Phase 7
> archive if Phase 6 RED — flip plan to `BLOCKED-CUTOVER` and notify operator.
>
> **🟢 STATUS 2026-05-19 ~21:30 UTC (completed by slot-5)** — Phase 6 ✅: boot 12/12 pairs EXIT=0, QG 4059 passed,
> strategy_parity_diff.py shipped strategy-service@91f701b0. Phase 7: DEPRECATION_NOTICE committed to all 3 source
> repos, operator archive ping filed PM@e88149a28. Awaiting operator `gh repo archive` for Phase 7 to complete.

**Plan**: `deployment_ui_lifecycle_tabs_2026_05_08.md` (30.0 cal, no progress yet — TBD baseline).

This is the cross-cutting 6-tab restructure of the deployment UI. Read the full plan before starting. Key tabs: Deploy,
Status, Logs, Strategy, Kill-switch, Config.

1. - [x] ✅ **Pre-audit** — read plan + identify current UI tab structure vs target. Grep for existing tab components in
         `unified-trading-system-ui/`. (research 1.2×, ~1 = 1.2 cal) — deployment-ui@ba009b2 + deployment-api@ffd97c1 +
         utl@424e03af (backfilled 2026-05-19)
2. - [x] ✅ **Tab 1 — Deploy lifecycle** — wiring VM launch events to UI deploy tab. (brand-new 1.0×, ~5 = 5.0 cal) —
         deployment-ui@ba009b2 Phase B.1+B.3 (backfilled 2026-05-19)
3. - [x] ✅ **Tab 2 — Status / data-freshness** — per-service health + manifest freshness feed. (brand-new 1.0×, ~5 =
         5.0 cal) — deployment-ui@ba009b2 Phase B.4+B.5+B.6 (backfilled 2026-05-19)
4. - [x] ✅ **Tab 3 — Logs / event-stream** — WebSocket log tail per VM / service (Harsh slot-7 shipped WebSocket VM
         streaming May-18; wire it into this tab). (brand-new 1.0×, ~5 = 5.0 cal) — deployment-ui@ba009b2 Phase B.8+C.5
         (backfilled 2026-05-19)
5. - [x] ✅ **Tab 4 — Strategy panel** — promote / demote / paper → live controls. (brand-new 1.0×, ~5 = 5.0 cal) —
         deployment-api@ffd97c1 Phase E.1+E.2 (backfilled 2026-05-19)
6. - [x] ✅ **Tab 5 — Kill-switch** — manual emergency halt per strategy / per service. (brand-new 1.0×, ~4 = 4.0 cal) —
         utl@424e03af Phase BB.1+BB.2+BB.3 (backfilled 2026-05-19)
7. - [x] ✅ **Plan flips** for each tab shipped. (0.5 cal) — deployment-ui@ba009b2 Phase G.1 workspace QG (backfilled
         2026-05-19)

> ⚠️ **WORK-SPLIT STALE WARNING**: Items 1-7 above were authored from a stale version of the plan. The actual
> [`deployment_ui_lifecycle_tabs_2026_05_08.md`](deployment_ui_lifecycle_tabs_2026_05_08.md) is **89% done (33/37 ✅)**.
> Plan body shows Phase A.1-A.5 + B.1-B.4 + F.1-F.2 + G.1 all ✅ (incl. 2026-05-19 backfills by slot 6 itself at
> deployment-ui@`ba009b2` + deployment-api@`ffd97c1` + utl@`424e03af`). Only 4 items genuinely open, all
> `[HUMAN]`/`[HUMAN+AGENT]`: F.3 (CLAUDE.md VM naming update), H.4 (Cloud Run provisioning), G.2 (staging deploy), G.3
> (operator sign-off). Re-dispatch per [`pings/slot_6.md`](../../ikenna_orchestrator/pings/slot_6.md):

8. - [x] ✅ **Work-split correction** — flip items 1-7 above to `[x] ✅` with evidence SHAs from plan body. One commit.
         (0.5 cal) — PM this commit
9. - [x] ✅ **F.3 AGENT-half** — draft CLAUDE.md "VM Naming Convention" update text + `lifecycle_class` rule +
         experiment-VM `run_id` suffix rule. Save as `.draft.md` (operator approves landing). (design 0.6×, ~2 = 1.2
         cal) — PM@2816975af (done by slot 6 itself, backfilled 2026-05-19)
10. - [x] ✅ **H.4 AGENT-half** — write `deployment-service/runbooks/deployment-ui-staging-prod-provisioning.md` with
          Cloud Run + Firebase Hosting + DNS + TLS + IAM specs per env tier. Reference existing trading-system-UI
          pattern. Operator-runnable. (design 0.6×, ~3 = 1.8 cal) — deployment-service@10fddb6
11. - [x] ✅ **G.2 AGENT-half** — write `deployment-service/runbooks/deployment-ui-staging-deploy.md` with exact
          `gcloud run deploy` / `firebase deploy` sequence + per-axis verification checklist. (design 0.6×, ~2 = 1.2
          cal) — deployment-service@10fddb6
12. - [x] ✅ **G.3 surface to operator-pending** — add to master plan operator-pending section flagging G.3 as final B6
          gate after G.2 lands. (design 0.6×, ~0.5 = 0.3 cal) — PM this commit

---

### Slot 7 — cross_cutting_deliverables + simulation_scenarios_topology + defi_master — ~27 cal AI-days

> **🔴 THEME DISPLACED 2026-05-19 ~14:00 UTC** — Slot 7 NEW theme: **strategy_repo_consolidation Phase 8A** —
> deployment-service sweep. **LARGEST single-repo edit in the plan**: ~90 hits across Terraform (6 per-service dirs on
> GCP + AWS), cloud-build configs, cluster configs, bucket configs, launchers, bootstrap scripts. Plan
> `terraform destroy` of the 3 retiring service modules in conjunction with `terraform apply` of the updated
> strategy-service module — do NOT leave orphan Terraform-managed resources. Collapse 4 launchers to
> `launch-strategy-vm.sh --operation {risk-monitor,position-recon,pnl-attribution,strategy-batch,strategy-live,backtest}`.
> Update `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`. ~3 cal-AI-days. Blocked-on: slot 6 Phase 7 archive.

**Part A — cross_cutting_may23_deliverables** (plan at 60%, 12.4 cal left):

Read `cross_cutting_may23_deliverables_2026_05_08.md` for open `- [ ]` items. Focus on:

1. - [x] ✅ **Strategy catalogue** — archetype × venue matrix in UAC; STRATEGY_REGISTRY + ArchetypeConfig SSOT. —
         uac@18bdc6e + uac@3cae1c2 (backfilled 2026-05-19)
2. - [x] ✅ **Strategy IDs** — stable ID schema + `parse_strategy_id` / `format_strategy_id` canonical helpers. —
         uac@5083d65 (backfilled 2026-05-19)
3. - [x] ✅ **Client model + accounts** — `CapitalAllocation` frozen dataclass + `CAPITAL_ALLOCATION_SEED` +
         `ClientDefinition` / `ClientRegistry` SSOT; 28 tests. — uac@3591037 + uac@3cae1c2 (backfilled 2026-05-19)

**Part B — simulation_scenarios_topology** (plan at 62%, 7.6 cal left):

4. - [x] ✅ **Phase 3 — scenario-runner integration** — 3.E `AdversarialMatchingEngine`
         (RejectFills/LatencyInject/BookSpoof at fill boundary) + 3.F alerting `synthetic=True` suppression +
         risk/alerting consumers. — execution-service@d0ec76f1 + alerting@3c0d675 (Harsh slot 5, 2026-05-12; backfilled
         2026-05-19)
5. - [x] ✅ **Phase 4 — per-scenario fixture sets** — 10 `ScenarioOverlay` registry instances (2 CeFi + 6 DeFi + 2
         cross_asset); SCENARIO_REGISTRY populated. — uac@33630a6 (slot 7 Day-2 2026-05-12; backfilled 2026-05-19)

**Part C — defi_master Phase 2–3** (plan at 33%, 9.4 cal left):

6. - [x] ✅ **Phase 2 — MTDS wiring for chain primitives** — UAC export surface (HYPERLIQUID/STARKNET RPC templates +
         ChainKind) shipped UAC@fa7e868+36eae39; MTDS `_ChainAnnotatingWriter` + `ONCHAIN_PERP_VENUE_CHAIN` dict +
         per-venue chain annotation wired for LIGHTER/PACIFICA/EXTENDED/HYPERLIQUID. — mtds@705a635 + uac@36eae39
7. - [x] ✅ **Phase 3 — instruments-service CLOB adapters** — Audit 2026-05-19: lighter.py + pacifica.py + extended.py
         all exist in instruments-service; factory.py + orchestrator wired; defi_master Phase 2 checkbox flipped. —
         PM@d40d0f0d6
8. - [x] ✅ **Plan flips** for all shipped items. — PM@d40d0f0d6 + mtds@705a635

**Part D — hard_schema Phase 5 (bonus — picked up after slot items exhausted):**

9. - [x] ✅ **STEP 5.83 Layer-2 checker** — `check_uac_hard_required_fields.py` + base-service.sh STEP 5.83 wired: (a)
         UAC regression guard: asserts `validate_instrument_records` + 3 closed-set rule landmarks in
         `instrument_validation.py` still present; (b) bundled shard-key kwargs AST-walk: literal
         `record_captured(data_type="<bundled>", …)` calls missing required shard-key kwarg → FAIL. Smoke-tested: both
         [OK] against real UAC + empty source. Complements prior base-library.sh STEP 5.83 (PM@03a320846) which guards
         the Pydantic model_validator. — PM@429b64b2b + PM@8427ac070

**Part E — hard_schema Phase 1 design+audit pass (RE-DISPATCH after item-9 close, 2026-05-19):**

10. - [x] ✅ **Phase 1 field-flip design+audit** — PM@16861e1ed. Field inventory (8 InstrumentRecord fields × 5
          asset_groups), consumer-sweep (all 🟢 SAFE / 🟡 DEFENSIVE, zero 🔴 BREAKS), sports `fixture_id` phantom
          verdict (non-optional on all per-fixture schemas; `CanonicalInjury` legitimately optional), back-fill
          migration scope, phased DAG (A–F). Plan file: `hard_schema_phase1_field_flip_migration_2026_05_19.md`. Real
          Phase A gap found: `base_asset_decimals` / `quote_asset_decimals` not yet validator-enforced. (refactor 0.4×,
          ~30 baseline = ~12 cal AI-days)

---

### Slot 8 — defi_catalogue close + defi_simulation_realism + dex_perp — ~29 cal AI-days

> **🔴 THEME DISPLACED + REASSIGNED 2026-05-19 ~15:30 UTC** — Slot 8 NEW theme is now **ml_repo_consolidation FULL
> PLAN** (~6 cal-AI-days, all 10 phases, single-slot ownership). Slot 8 already shipped Phase 0 + Phase 1 organically
> (commits [`1113ffee9`](https://github.com/IggyIkenna/unified-trading-pm/commit/1113ffee9) Phase 1 schema-prep done,
> [`7663f6c80`](https://github.com/IggyIkenna/unified-trading-pm/commit/7663f6c80) BLOCKED-OPERATOR on Phase 2) while my
> earlier dispatch had ML on slot 9. Phase 2 (`gh repo create IggyIkenna/ml-service`) UNBLOCKED 2026-05-19 ~15:09 UTC by
> slot 1 main + worktree provisioned at `.tabs/8/ml-service` on `tab/ikennaigboaka/8`. Slot 8 proceeds with Phase 2
> (b-i) bootstrap next.
>
> **Plan**: [`plans/active/ml_repo_consolidation_2026_05_19.md`](./ml_repo_consolidation_2026_05_19.md). **Pre-audit**:
> [`plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md`](./issues/ml_repo_consolidation_preaudit_2026_05_19.md).
> **Decisions already taken**: Phase 4 (h) = single flat-deps Docker (operator picked Option 2 2026-05-19); Phase 0.5
> (FeatureSubscriber → IoFeatureSubscriber rename) = DONE in `ml-inference-service@042c41d`.
>
> Slot 8's **previous** strategy-twin Phase 9+10 assignment (codex sweep) is REASSIGNED to whichever slot picks it up
> after their strategy consolidation work clears (likely slot 3 once Phase 0.5+1+2 ships, or slot 6 after Phase 7
> archive). Slot 1 main will dispatch in next reallocation pass.
>
> **PREVIOUS BANNER (deferred reassignment context — strategy Phase 9+10 codex sweep)** — Slot 8 NEW theme:
> **strategy_repo_consolidation Phase 9 + 10** — codex SSOT sweep (8 enumerated codex paths from plan Phase 9 a-h: new
> `strategy-service-architecture.md` already stub-created, register in `00-SSOT-INDEX.md`, update
> `promote-workflow-architecture.md`, `launcher-script-ssot.md`, `vm-tarball-deployment.md`, `cli-convention.md`,
> `cli-promote-paths.md`, and bulk-rewrite ~150 incidental codex/cursor-configs refs to the 3 source repo names). Phase
> 10 = workspace QG sweep + cross-plan banner cleanup + inventory regenerator + final commit sweep. ~2 cal-AI-days.
> Blocked-on: slot 7 Phase 8A complete (Terraform must be applied before codex docs reference new launcher topology).

**Part A — defi_catalogue_chain_primitives** (plan at 87%, 27.2 cal left):

Read plan for the 9 remaining open items. Most are Phase 6 backfills + Phase 7 instrument wiring.

1. - [ ] [BLOCKED-OPERATOR] **Phase 6 — per-chain backfill scripts** (6J/7E already done ✅). Remaining: 6C (Pyth Hermes
         Solana LST ≥1yr, BLOCKED-OPERATOR ping filed 2026-05-14), 6D (Lighter/Pacifica — slot 3 owns), 6E
         (vaults+restaking+DEX ≥2yr, needs operator [ack] per ≥1-week backfill rule). Cannot proceed without operator
         backfill approval. (infra 0.8×, ~6 = 4.8 cal)
2. - [x] ✅ **Phase 7.I — defi_catalogue instruments cross-ref** — already `[x] ✅` in plan body (slot 1 shipped
         PM@75560065 2026-05-18; Group F items 17-20 refreshed). No further action.
3. - [ ] [BLOCKED-UPSTREAM] **Remaining open items** — 6C/6E BLOCKED-OPERATOR (backfill approval pending); 8A/8B
         BLOCKED-UPSTREAM (gated on Phase 6 completion); 8C BLOCKED-OPERATOR (human-only hard stop, wallet keys). No
         actionable items without operator unblock. (mixed, ~10 = 8.0 cal)
4. - [ ] [BLOCKED-UPSTREAM] **Close defi_catalogue** — cannot close: 6C/6E/8A/8B/8C all blocked (see item 3). Plan stays
         active at 87% until Phase 6 backfill operator acks land. (0.5 cal)

**Part B — defi_simulation_realism** (plan at 98%, 0.7 cal left — 1 item):

5. - [x] ✅ **Final item** — `defi_simulation_realism_2026_05_10.md` ARCHIVED in `plans/archive/` with 0 open items. All
         items `[x]`. No remaining work.

**Part C — dex_perp_and_venue_data** (plan at 94%, 0.5 cal left):

6. - [ ] **Final 2 items** — (1) VM launcher for Extended OHLCV backfill: `BLOCKED-OPERATOR-DECISION` (ping in plan body
         §2F); (2) Uniswap V3 subgraph research: `DEFERRED NICE-TO-HAVE P3` per plan body §4C. Both items unshippable
         without operator unblock. dex_perp at 94% done.

**Part D — hard_schema_enforcement** (no-deadline, 4.8 cal):

7. - [x] ✅ **Open items — FUTURE+OPTION model_validator rules** — shipped FUTURE+OPTION expiry non-null rules in
         `InstrumentRecord._enforce_per_asset_group_required_fields` (tradfi_master Q1+Q2 gates passed 2026-05-13). 15
         tests in `tests/internal/unit/test_instrument_record_hard_required_fields.py`. QG ✅ ALL PASSED. uac@80aef10
         2026-05-19. (design 0.6×, ~8 = 4.8 cal)

---

### Slot 9 — batch_live_symmetry Tabs 4–7 + cme_polymarket_arb + promote_workflow_may23 — ~31 cal AI-days

> **🟢 STANDING DOWN 2026-05-19 ~15:30 UTC** — Slot 9 not booted today (operator opened only 8 slots). ML consolidation
> theme **REASSIGNED to slot 8** (organic pickup: slot 8 shipped Phase 0 + Phase 1 before reassignment was formalised —
> see slot 8 commits [`1113ffee9`](https://github.com/IggyIkenna/unified-trading-pm/commit/1113ffee9)
>
> - [`7663f6c80`](https://github.com/IggyIkenna/unified-trading-pm/commit/7663f6c80)). Slot 9 worktree provisioned for
>   ml-service + reset to LDR (`tab/ikennaigboaka/9`); ready for future boot if needed. Previous "🔴 THEME DISPLACED"
>   banner content (~6 cal-AI-days ML full-plan dispatch) moved to slot 8 — see Slot 8 section.

**Part A — batch_live_symmetry Tabs 4–7** (continuation from slot 3's Tabs 1–3):

1. - [x] ✅ **Tab 4 — features-service ModeHandler lift (4 families)** — commodity / cross_instrument / multi_timeframe
         / calendar. Per plan §Tab 4. (brand-new 1.0×, ~6 = 6.0 cal) — ALL 4 families DONE: features-service@519625f7
         (confirmed 2026-05-18 backfill); plan checkboxes all ✅
2. - [ ] [BLOCKED-OPERATOR] **Tab 5 — pipeline_mode VM fleet migration** — per plan §Tab 5 (Phases 3/4/9). Phase 4
         consumer sweep already DONE (slot 3); Phase 3 VM migration requires operator cost-audit green-light. (brand-new
         1.0×, ~5 = 5.0 cal)
3. - [x] ✅ **Tabs 6–7** — Tab 6 Service-readiness Group A shipped: blr@9905bde QG pass + PR #5 → staging 2026-05-19.
         Tab 7 (UI ExecutionModeContext) deferred to operator (requires Playwright + dev server). (brand-new 1.0×, ~4 =
         4.0 cal)

**Part B — cme_polymarket_arb Phase 1** (no-deadline, 15.0 cal):

4. - [x] ✅ **Phase 1 — InstrumentType.EVENT_CONTRACT + UAC schema** — confirmed shipped: uac@b95d146
         (InstrumentType.EVENT_CONTRACT enum + Databento BAG classifier + 4 tests). (brand-new 1.0×, ~5 = 5.0 cal)
5. - [x] ✅ **Phase 2 — MTDS Polymarket + CME adapter scaffolds** — Phase 2 (cross-link field) BLOCKED by
         predictions_master Phase 5. Phase 3 (MTDS binary-outcome shard atom) shipped as unblocked proxy. — uac@2751910:
         event_contract registered in BUNDLED_DATA_TYPES + EVENT_CONTRACT_ROOT_CLUSTERS (9 roots) +
         DATA_TYPE_TO_CLUSTER_REGISTRY; 3 tests green. (brand-new 1.0×, ~5 = 5.0 cal)

**Part C — promote_workflow_may23 residuals** (plan at 62%, 1.6 cal left):

6. - [x] ✅ **Remaining open items** — all remaining `- [ ]` items in promote_workflow are OPERATOR-ONLY (run
         preflight-cutover.sh, 2yr backtest, Copper provisioning, testnet smoke, Tenderly fork dry-run). No
         agent-executable items remaining. (design 0.6×)
7. - [x] ✅ **Plan flips** for all shipped. (0.5 cal)

---

## Operator-action items pending (from prior cycles)

| #   | Item                                                                       | Status                 | Ping filed    |
| --- | -------------------------------------------------------------------------- | ---------------------- | ------------- |
| 1   | **Write-pause** — trigger MTDS + instruments-service pause for L3/L5 flips | 🔴 BLOCKING slot 2     | May-18 slot 1 |
| 2   | **tradfi-fwd cron deployment** — tradfi_forward_cron_missing_2026_05_17.md | 🟡 BLOCKED-OPERATOR    | May-17        |
| 3   | **Phase 7.G manifest v8 sign-off** — 5 asset_groups                        | 🟡 BLOCKED-OPERATOR    | May-15        |
| 4   | **Phase 3c lending VM re-run** — USDT/USDC IRM re-run                      | 🟡 BLOCKED-OPERATOR    | May-15        |
| 5   | **Kalshi credential** (5.B.2)                                              | 🟡 BLOCKED-CREDENTIALS | May-18 slot 8 |
| 6   | **CoinGecko credential** (5.C)                                             | 🟡 BLOCKED-CREDENTIALS | May-18 slot 8 |

---

## Done-definition (2026-05-19 EOD)

- Slot 2: L3 + L5 flips on LDR + archive script run + write-resume verified + phantoms clean.
- Slot 3: code_freeze Phase 2.0–2.5 gaps closed + batch_live_symmetry Tabs 1–3 on LDR.
- Slot 4: api_keys Phase 3.A + 4.A–4.E + defi_recursive_borrow Phase 3–4 all on LDR.
- Slot 5: writegate Phase 6.6 (ml-training + ml-inference) + Phase 6.7 (strategy + risk) on LDR.
- Slot 6: deployment_ui_lifecycle_tabs ≥ 3 tabs shipped, plan ≥50% checked off.
- Slot 7: cross_cutting strategy catalogue + strategy IDs + simulation Phase 3 on LDR.
- Slot 8: defi_catalogue ≥95% done + defi_simulation_realism 100% + hard_schema shipped.
- Slot 9: batch_live_symmetry Tabs 4–7 + cme_polymarket_arb Phase 1 on LDR.

---

## Spawn prompt — paste into each tab (slot N)

```text
You are slot N (Ikenna side). Today is 2026-05-19 (Cycle 2 Day-4 — full backlog sweep).

Boot:
1. SYNC TO LDR — from .tabs/<N>/:
     for d in */; do
       (cd "$d" && [ -d .git -o -f .git ] && \
        git fetch origin live-defi-rollout --quiet && \
        git merge --ff-only origin/live-defi-rollout 2>/dev/null) ;
     done

2. Read unified-trading-pm/ikenna_orchestrator/AGENT_ONBOARDING.md

3. Read unified-trading-pm/plans/active/work_split_2026_05_19_ikenna.md § "Slot <N>"

4. Read your top plan-of-record (listed in the slot section above).

5. Boot ack at unified-trading-pm/ikenna_orchestrator/pings/slot_<N>.md using `date -u`.

CRITICAL RULES:
* Plan-flip discipline: every shippable unit = (Half 1) commit + push code, then
  (Half 2) flip checkbox with docs(plans): prefix commit IN SAME AGENT TURN.
* git fetch before every commit on shared repos (execution-service, UTL, UAC,
  deployment-api, deployment-service).
* QG before push: bash scripts/quality-gates.sh (Pass 1). Then quickmerge or direct push.
* Slot 2 ONLY: do NOT flip L3/L5 until operator signals write-pause is active.
* Slot 6: check for Harsh slot-7 deployment-ui commits before pushing.

Now begin.
```
