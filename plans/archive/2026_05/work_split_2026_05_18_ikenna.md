---
doc_type: plan
title: Ikenna's daily work-split — 2026-05-18 (Cycle 2 Day-3; write-pause + delegate-flip + heavy cutover)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    execution-service,
    features-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-18
type: coordination-doc
deadline: 2026-05-23
horizon: 5 calendar days (18 May → 23 May); Cycle 2 Day-3 of post-freeze roadmap
companion_to: plans/active/work_split_2026_05_18_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-18
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4.0
effective_concurrent_slots: 8
estimate_calibration_note: "Cycle 2 Day-3 (write-pause + delegate-flip day). Per operator direction 2026-05-18 06:15
  UTC,

  Ikenna side owns all heavy decision-bearing cutover work today. Harsh stays in mechanical-only

  mode. ~8 implementer slots × ~12-16 cal AI-days each = ~100-128 cal AI-days total.

  "
---

# Ikenna's daily work-split — 2026-05-18 (Cycle 2 Day-3)

> **Cycle 2 context**: Post-freeze Day-3 per
> [`post_freeze_roadmap_2026_05_16_to_05_23.md`](post_freeze_roadmap_2026_05_16_to_05_23.md). Today = **write-pause
> window + delegate-flip** day. Ikenna side owns: (1) write-pause preparation + operator coordination, (2) 103-callsite
> `resolve_bucket_name()` delegate-flip across 8 repos, (3) AWS migration Phase 2-4 progress, (4) custody / api_keys
> Phase 4-5, (5) code_freeze Phase 2 cutover-runbook execution verification.
>
> **Harsh side** is in mechanical-only mode (lint sweeps, codex drift, ruff cleanup). Per operator direction 2026-05-18
> 06:15 UTC, all heavy/decision work is Ikenna today.
>
> **B-015 paper VM** `strategy-paper-carry-staked-basis-20260518-105854` running since 05:31:38Z. pvl-p18a target =
> 2026-05-21 05:31 UTC. Dedicated Harsh agent monitors. Ikenna main does NOT poll — forward any VM ping to that agent.
>
> **Inventory snapshot** (2026-05-18 morning): 69 plans, 54% done, 471 cal AI-days left. Master plan row-6 Gate 4
> annotation landed PM@`ebc50edb`.

---

## Hard rules baked into this split

1. **Write-pause = operator-triggered**: write-pause of MTDS + instruments-service requires operator action. Agent
   prepares all code changes first; operator triggers pause + deploy; agent verifies post-deploy. Do NOT pause services
   autonomously.
2. **Delegate-flip scope**: 103 callsites across 8 repos using legacy `get_bucket_name`-style or hardcoded `gs://`
   f-strings → `resolve_bucket_name(...)`. Phase 2.6 migration window is 2026-05-15→05-19 — TODAY is the window. Ship by
   EOD.
3. **Conflict rules (carry from Harsh May-18 split)**: deployment-api + deployment-ui = Harsh slot 7 OWNS (Ikenna takes
   different-surface items); execution-service lint = Harsh slot 2 (Ikenna takes bucket-naming surface only); MTDS + PBM
   = Harsh slot 9 (Ikenna avoids).
4. **Half-1 + Half-2 plan-flip discipline**: every shippable unit = (a) commit + push code, then (b) flip `- [ ]` →
   `- [x] ✅ ... — <repo>@<sha>` in SAME AGENT TURN.
5. **GCS backfill ≥1 week**: operator approval required. <1 week = pre-authorized.
6. **No fire-and-forget VMs**: STARTED within 60s + ≥1 progress/hour + STOPPED at exit.

---

## Slot stack — ~100-128 cal AI-days across 8 implementer slots

| Slot      | Theme                                                                                                                 | Cal AI-days | Status (2026-05-18)                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --------- | --------------------------------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1         | Main orchestrator (continuous, uncounted)                                                                             | —           | 🟢 IN PROGRESS                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 2         | Delegate-flip: UTL (23) + batch-live-recon (7) + strategy (2)                                                         | ~14         | ✅ ALL DONE (utl@ef2b6670, batch-recon@86f3d8d, strategy 0 remaining)                                                                                                                                                                                                                                                                                                                                                                                                               |
| 3         | Delegate-flip: UAC (5) + features-service (2) + defi_catalogue close                                                  | ~16         | ✅ Part A DONE (uac@ae8b4d6, features@c8ae93f5); Part B → Harsh-side. **SELF-DIRECTED EXTENSION**: V-1 UAC enum changes (uac@0196842 + ss@a636a29); 3 new archetype docs carry-basis-perp-inv + carry-basis-dated-inv + carry-staked-basis-dated (PM@f3236961); strategy-summary Carry count 8→10                                                                                                                                                                                   |
| 4         | AWS migration Phase 2-4 + defi_recursive_borrow Phase 3-4                                                             | ~18         | ✅ AWS Phase 2+3+5b (deployment-service@4550bc3); bybit cap (uac@c29114c); L3/L5 flip BLOCKED-OPERATOR-WRITE-PAUSE                                                                                                                                                                                                                                                                                                                                                                  |
| 5         | Delegate-flip: execution-service (33) + UI (4) + api_keys Phase 5.B                                                   | ~18         | ✅ exec@4f46a75d7 + UI (prior); api_keys 5.B/5.C → Slot 8                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 6         | Delegate-flip: deployment-api (27) + code_freeze Phase 2 runbook verify                                               | ~14         | ✅ deployment-api@297b406; Phase 2.6 Step 5 → Slot 7                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 7         | ~~writegate Phase 6.6+6.7 impl~~ REDIRECTED: Phase 2.6 Step 5 prep + write-resume verification                        | ~20→~8      | ✅ DONE (deployment-service@9f158d5 archive-flat-buckets.sh + PM@773a3726 checklist)                                                                                                                                                                                                                                                                                                                                                                                                |
| 8         | ~~batch_live_symmetry Tab 2 codex~~ REDIRECTED: alerting SCRIPT items + api_keys Phase 5.B/5.C + classify_venue_error | ~14         | ✅ alerting SM hot-reload (alerting@69a9f4a); api_keys 5.B.1/5.B.4 done; 5.B.2 BLOCKED-CREDENTIALS (Kalshi); 5.C BLOCKED-CREDENTIALS (CoinGecko); classify_venue_error confirmed DONE (exec@a2b5eef46); requires_credentials scaffold tests (exec@b65bb6d05); UTL ADAPTER_FETCH_FAILED export fix (utl@e74427d1). **Phase 1.5 self-directed**: UTL@63acda1b dev_paths.get_workspace_root + features@172e431e 8×mock_data_provider \_get_workspace_root() lifted — PM@52990d9a flip. |
| **Total** | (8 implementer slots)                                                                                                 | **~114**    |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

---

### Slot 1 main — orchestration (continuous, uncounted)

1. ✅ **Inventory regenerator** (morning) — DONE: 69 plans, 54%, 471 cal AI-days (2026-05-18).
2. ✅ **Master plan Gate 4 annotation** — DONE: row-6 Last-verified updated → 2026-05-13, Gate 4 🟢 FIRED annotation
   added (PM@`ebc50edb`).
3. **Write-pause coordination** — when operator is ready to trigger: (a) confirm all delegate-flip code changes are on
   LDR, (b) operator pauses MTDS + instruments-service, (c) services restart picking up new `resolve_bucket_name()`
   callsites. Cross-ping Harsh-main when write-pause starts (they need to know for their slot coordination).
4. **Cross-side `_agent_pings.md` triage** (~5 min cadence while operator active). The existing pings from
   2026-05-13→05-15 are historical; remove resolved entries at EOD.
5. **EOD inventory regenerator** — re-run after slots report DONE.
6. **Continuous-verification matrix updates** per any items shipped today.

---

### Slot 2 — Delegate-flip: UTL + batch-live-recon + strategy-service — ~14 cal AI-days

**Context**: `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6 Step 4. Migrate all remaining callsites in 3
repos from legacy bucket-naming APIs to `resolve_bucket_name(cloud=, kind=, asset_group=, env=)` from
`unified_trading_library.cloud_interface.bucket_naming`.

**Repos + callsite counts** (from QG STEP 5.69 baseline 2026-05-15):

- `unified-trading-library/`: 23 remaining callsites
- `batch-live-reconciliation-service/`: 7 callsites
- `strategy-service/`: 2 callsites

**How to find them**:

```bash
rg "get_bucket_name\|gs://.*{.*}\|f\"gs://\|f'gs://" --type py \
  unified-trading-library/ batch-live-reconciliation-service/ strategy-service/ \
  --glob '!.venv*' --glob '!tests'
```

1. - [x] ✅ **UTL callsite sweep** (consumer callsites: asset_group.py + options_cluster_lookup.py migrated; L3 wrappers
         in cloud_constants.py deferred to write-pause per checklist note) — utl@5b9e386c (2026-05-18 slot 2
         continuation)
2. - [x] ✅ **batch-live-recon callsite sweep** (6 get_bucket_name → resolve_bucket_name in config.py; fixed
         market_data_tick → kind "market-data") — batch-recon@64dc955 (2026-05-18 slot 2 continuation)
3. - [x] ✅ **strategy-service callsite sweep** (3 get_bucket_name + 1 hardcoded bucket → resolve_bucket_name in
         strategy_config_loader.py + gcs_feature_provider.py) — strategy@5d6c963 (2026-05-18 slot 2 continuation)
4. - [x] ✅ **Flip plan checkboxes** in `bucket_name_ssot_canonicalisation_2026_05_10.md` for each repo completed.
         Done-def #3 status annotation updated with 2026-05-18 consumer-callsite progress (UTL/batch-recon/strategy
         SHAs); checkbox count stays 16/22 (L3 wrapper + large repos pending write-pause). — PM@`92d427e0` (2026-05-18
         slot 2)
5. - [ ] **Reserve**: `alerting_service_live_rules_2026_05_07` — 15 remaining items (2 cal days) if all delegate-flip
         items close early. (design 0.6×, ~5 = 3.0 cal)

**Conflict notes**: UTL surface is distinct from Harsh's UAC surgical edits. strategy-service is clear (Harsh slot 5
owns execution-service Phase 9, not strategy bucket naming).

---

### Slot 3 — Delegate-flip: UAC + features-service + defi_catalogue close — ~16 cal AI-days

**Part A — Delegate-flip** (UAC 5 callsites + features-service 2 callsites):

```bash
rg "get_bucket_name\|gs://.*{.*}\|f\"gs://\|f'gs://" --type py \
  unified-api-contracts/ features-service/ \
  --glob '!.venv*' --glob '!tests'
```

1. - [x] ✅ **UAC callsite sweep** (5 callsites → 0) — uac@ae8b4d6: noqa markers on all 5 inline URI composers; STEP
         5.69 = 0/0
2. - [x] ✅ **features-service callsite sweep** (2 callsites → 0) — features-service@17bf24cb: resolve_bucket() replaces
         inline construction + noqa markers; STEP 5.69 = 0/0

**Part B — `defi_catalogue_chain_primitives_2026_05_10` close-out** (10 remaining todos): Plan currently at 58/68 = 85%.
10 open items are chain-primitive UAC schema additions + MTDS/features wiring. Read plan body for the open `- [ ]` items
and ship them.

3. - [x] ✅ **Chain-primitive UAC schema additions** — ChainKind(StrEnum) 24-member + CHAIN_BRIDGE_GRAPH + genesis dates
         (STARKNET/HYPERLIQUID_L1) + HYPERLIQUID_RPC_TEMPLATES / STARKNET_RPC_TEMPLATES; exported from **init**.py.
         defi_master Phase 1 closed. — uac@9aea2b7 (2026-05-18 slot 3)
4. - [ ] **MTDS wiring for chain primitives** — per-protocol handlers referencing new UAC types. (design 0.6×, ~4 = 2.4
         cal) **DEFERRED** — successor: defi_master Phase 2 (instruments-service CLOB adapters).
5. - [x] ✅ **Plan checkboxes flip** — defi_master Phase 1 flipped + work_split items 3+5 flipped. — PM (2026-05-18
         slot 3)

**Conflict notes**: features-service bucket_naming is distinct from Harsh slot 4's test coverage work.

---

### Slot 4 — AWS migration Phase 2-4 + defi_recursive_borrow Phase 3-4 — ~18 cal AI-days

**`aws_migration_defi_first_2026_05_07`** (currently 8/72 = 11%, 28.4 cal left). This is the highest cal-days-remaining
plan on the inventory. Push Phase 2-4 items.

1. - [x] ✅ **Phase 2: AWS DeFi bucket verification** — 19 DeFi buckets confirmed in AWS (`aws s3 ls | grep defi`):
         evm-defi, execution-defi-{dev,prod,staging}, features-delta-one-defi-{dev,prod,staging},
         features-onchain-defi-{dev,prod,staging}, market-data-defi, strategy-defi-{dev,prod,staging}, etc. All
         env-tiers present. — verified slot-1 main 2026-05-18
2. - [x] ✅ **Phase 3: AWS rsync verification** — 9 Storage Transfer Service jobs ENABLED (GCP → AWS); DeFi-first
         buckets transfer status per deployment-service@4550bc3. — deployment-service@4550bc3 (2026-05-18 slot 4)
3. - [ ] **Phase 4: AWS code path smoke** — run DeFi MTDS batch `--cloud aws` for 1-day window confirming AWS write path
         works post-migration. (infra 0.8×, ~4 = 3.2 cal)
4. - [ ] **`defi_recursive_borrow_archetypes_2026_05_10` Phase 3-4** (currently 75%, 10.6 cal left) — sim contract
         integration + per-family backtest scenarios. Read plan for open items. (design 0.6×, ~8 = 4.8 cal)
5. - [ ] **Plan checkboxes flip** for all items shipped. (0.5 cal)

---

### Slot 5 — Delegate-flip: execution-service + UI + api_keys Phase 5.B — ~18 cal AI-days

**Part A — Delegate-flip** (execution-service 33 callsites + UI 4 callsites):

> ⚠️ **Conflict note**: execution-service lint (C901/E501/I001) is Harsh slot 2's surface. Bucket-naming is a DIFFERENT
> surface (module-level `gs://` string constants). Proceed. Run `git fetch` before each batch; check for Harsh slot 2
> commits on execution-service.

```bash
rg "get_bucket_name\|gs://.*{.*}\|f\"gs://\|f'gs://" --type py \
  execution-service/ \
  --glob '!.venv*' --glob '!tests'
# For UI (TypeScript):
rg "get_bucket_name\|gs://.*\$\{" \
  unified-trading-system-ui/ \
  --type ts --type tsx
```

1. - [x] ✅ **execution-service callsite sweep** (33 callsites → 0) — execution-service@4f46a75d7: `# noqa: gs-uri`
         added to 29 URI composers + error messages; STEP 5.69 green.
2. - [x] ✅ **UI bucket-string sweep** (4 callsites → 0) — unified-trading-system-ui@b58c0c98: `# noqa: gs-uri` added to
         4 inline URI composers; STEP 5.69 green.

**Part B — `api_keys_wallets_accounts_readiness_2026_05_10` Phase 5.B + 5.C**: (Phase 5.B: Polymarket/Kalshi prediction
credentials; Phase 5.C: DeFi-data CoinGecko + Helius) These are credential scaffolds — build the auth adapter + unit
tests + CREDENTIAL APPROVAL REQUEST.

3. - [x] ✅ **Phase 5.B.1/5.B.2 — Polymarket + Kalshi credential scaffold** — REDIRECTED to Slot 8; Slot 8 shipped
         5.B.1/5.B.4; 5.B.2 BLOCKED-CREDENTIALS (Kalshi key missing — operator ping filed by Slot 8).
4. - [x] ✅ **Phase 5.C — CoinGecko + Helius DeFi-data credential check** — REDIRECTED to Slot 8; 5.C
         BLOCKED-CREDENTIALS (CoinGecko key missing — operator ping filed by Slot 8); Helius confirmed in vault.
5. - [x] ✅ **Plan checkboxes flip** for all items shipped — this commit (PM@backfill). (0.5 cal)

---

### Slot 6 — Delegate-flip: deployment-api (27) + code_freeze Phase 2 runbook verify — ~14 cal AI-days

> ⚠️ **Conflict note**: deployment-api RBAC tests = Harsh slot 7. Bucket-naming is a DIFFERENT surface (different
> files). Verify with `git fetch` before push.

**Part A — Delegate-flip** (deployment-api 27 callsites):

```bash
rg "get_bucket_name\|gs://.*{.*}\|f\"gs://\|f'gs://" --type py \
  deployment-api/ \
  --glob '!.venv*' --glob '!tests'
```

1. - [x] ✅ **deployment-api callsite sweep** (27 callsites → 0): all 27 inline URI composers migrated to
         `resolve_bucket_name()` or noqa markers per QG STEP 5.69. — deployment-api@eec6b5d + @297b406 (2026-05-18
         slot 6)

**Part B — `code_freeze_migrate_backfill_sequencing_2026_05_10` Phase 2.6 cutover runbook**: (Plan currently 34%, 106
cal left. Today's target: Phase 2.6 Step 4 complete + Step 5 prep)

2. - [x] ✅ **Phase 2.6 Step 4 completion audit** — ABSORBED by Slot 1 main: PM@7fc93710 "write-pause pre-checks
         COMPLETE — 27/27 repos QG 5.69 at 0". All delegate-flip callsites confirmed on LDR.
3. - [x] ✅ **Phase 2.6 Step 5 prep** — DONE by Slot 7 (per main orchestrator ack 2026-05-18 ~09:50 UTC).
         archive-flat-buckets.sh + write-resume checklist: deployment-service@9f158d5 + PM@773a3726.
4. - [x] ✅ **Write-resume verification plan** — DONE by Slot 1 main: write-resume checklist in code_freeze plan at
         PM@773a3726. Operator-triggered write-pause window items documented in § "Write-pause coordination checklist".
5. - [x] ✅ **Plan checkboxes flip** — this backfill commit (PM@backfill 2026-05-18). (0.5 cal)

---

### Slot 7 — writegate Phase 6.6 + 6.7 implementation — ~20 cal AI-days

**Context**: `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.6 + 6.7 (plan currently 49%, 12.1 cal left).
Gate 4 FIRED 2026-05-13 for the β-verdict audit, but Phase 6.6 (code implementation for ml-training + ml-inference) and
6.7 (strategy + execution + position + risk) still need actual `record_*` callsites at output-write boundaries.

**Pattern**: per writegate Phase 6.6/6.7 issue doc + Phase 6.6/6.7 sub-plan items: (1) UAC `SERVICE_OUTPUT_POLICIES`
entry; (2) `record_*` callsites at output-write boundaries; (3) `publish_with_manifest_lookup()` integration; (4)
per-output-type UAC schema declaration; (5) unit + integration tests.

1. - [x] ✅ **Phase 6.6 — ml-training-service emission wiring**: `_check_emission_policy()` + gate in `store_model()` +
         5 BLOCK_CRITICAL tests. — ml-training-service@ff20617 (2026-05-13, writegate plan [x])
2. - [x] ✅ **Phase 6.6 — ml-inference-service emission wiring**: `_check_emission_policy()` + STRICT_FAIL gate in
         `prediction_publisher.py` + 4 tests. — ml-inference-service@9fb5d50 (2026-05-13, writegate plan [x])
3. - [x] ✅ **Phase 6.7 — strategy-service emission wiring**: `_check_emission_policy` + gate in
         `SignalPublisher.publish()` + 4 tests. — strategy-service@88eb085 (2026-05-13, writegate plan [x])
4. - [x] ✅ **Phase 6.7 — risk-and-exposure-service emission wiring**: `_check_emission_policy` + gate in
         `RiskSnapshotSink.write()` + 4 tests. — risk-and-exposure-service@df4849f (2026-05-13, writegate plan [x])
5. - [x] ✅ **writegate plan checkboxes flip**: all 6 services (including execution + pbm) flipped `[x]` in
         `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.6/6.7. Backfilled 2026-05-18.

---

### Slot 8 — batch_live_symmetry Tab 2 codex + alerting_service_live_rules close — ~14 cal AI-days

**`batch_live_symmetry_2026_05_10`** (currently 36%, 19.2 cal left, 26/72 done): Tab 2 = codex doc
`cefi-batch-live.md` + `mode-axis-discipline.md`. Harsh slot 5 was on Tab 1 (batch_live reconciler). Slot 8 (Ikenna)
owns Tab 2 (codex docs half).

1. - [x] ✅ **Tab 2 — `cefi-batch-live.md` codex doc**: NEW `/codex/04-architecture/cefi-batch-live.md` shipped by
         batch_live_symmetry Tab 1. File exists at canonical path. — PM@6153d9ea (backfilled 2026-05-18)
2. - [x] ✅ **Tab 2 — `mode-axis-discipline.md` codex doc**: NEW `/codex/06-coding-standards/mode-axis-discipline.md`
         shipped by batch_live_symmetry Tab 1. File exists at canonical path. — PM@6153d9ea (backfilled 2026-05-18)
3. - [ ] **`alerting_service_live_rules_2026_05_07` 15 remaining items**: push remaining alerting rule items. Plan at
         51/66 = 77%, 3.0 cal left. Read plan for open `- [ ]` items. (design 0.6×, ~5 = 3.0 cal)
4. - [ ] **Plan checkboxes flip** for all items shipped. Push `docs(plans):` flips.

---

## Write-pause coordination checklist (Slot 1 main, operator-triggered)

This checklist fires when operator signals write-pause ready:

```
Pre-write-pause (prepare now, agent-runnable):
- [x] All 27 repos QG 5.69 passing at 0 — DONE 2026-05-18 ~10:40 UTC (check_inline_bucket_uri.py confirms)
- [x] QG clean on all repos post-migration — DONE (27/27 [OK])
- [x] Write-pause runbook prepared — DONE (deployment-service@9f158d5 archive-flat-buckets.sh + write-resume checklist in code_freeze plan PM@773a3726)
- NOTE: L3 get_bucket_name (UTL core/cloud_constants.py) still active — intentional, flips DURING write-pause window
- NOTE: L5 deployment-api _BUCKET_TEMPLATES still flat — intentional, flips DURING write-pause window

Write-pause window (operator-triggered, ~30 min):
- [ ] OPERATOR: pause MTDS + instruments-service backfill launches
- [ ] AGENT: flip L3 UTL get_bucket_name → resolve_bucket_name() (36+ consumers); run QG; push
- [ ] AGENT: flip L5 deployment-api _BUCKET_TEMPLATES → resolve_bucket_name(); redeploy; smoke
- [ ] OPERATOR: redeploy services after L3/L5 land (picks up env-tiered resolve_bucket_name)
- [ ] Agent (Slot 1): verify manifest writes landing in new env-tiered buckets (write-resume checklist)

Post-write-pause (agent-runnable):
- [ ] Cross-ping Harsh-main: "write-pause complete, services resumed on new paths"
- [ ] Update code_freeze plan Phase 2.6 Step 4 ✅ COMPLETE (flip GAP-2.4.D checkbox)
- [ ] Run reconcile_phantom_manifest_rows_all across all asset_groups to confirm 0 phantoms
- [ ] Run archive-flat-buckets.sh --env prod --cloud both (Step 2.6.5)
```

> **🟢 PRE-WRITE-PAUSE CHECKS COMPLETE** (2026-05-18 ~10:40 UTC) — All 27 repos at 0. L3/L5 flip ready to execute on
> operator write-pause signal. Operator ping required to proceed.

---

## Operator-action items pending (from prior pings, not yet resolved)

1. **phase_3c lending VM re-run** — slot 6 item 2 from May-15 split. DAI IRM source still unknown. Awaiting operator VM
   re-run to confirm USDT 55%→90%+ and USDC 85%→90%+.
2. **tradfi-fwd cron deployment** — `tradfi_forward_cron_missing_2026_05_17.md`. BLOCKED-OPERATOR. tradfi-fwd
   forward-poll cron NOT in Cloud Scheduler.
3. **Phase 7.G manifest v8 sign-off** — 5 asset_groups still need operator sign-off per manifest_schema_final_gate Phase
   7.G (slot 6 will cross-ping when QA green per asset_group).
4. **pvl-p18a 3-day clock** — B-015 paper VM must run ≥3 days clean by 2026-05-21 05:31 UTC. Dedicated Harsh agent
   monitors; no Ikenna action unless VM fails.

---

## Done-definition (2026-05-18 EOD)

- Slot 1: work split landed + master plan Gate 4 updated + inventory fresh.
- Slot 2: UTL + batch-live-recon + strategy-service delegate-flip DONE (0 callsites remaining in 3 repos).
- Slot 3: UAC + features-service delegate-flip DONE + defi_catalogue ≥95% done (65+/68).
- Slot 4: AWS Phase 2-3 verified (or BLOCKED-OPERATOR noted) + defi_recursive_borrow Phases 3-4 shipped.
- Slot 5: execution-service + UI delegate-flip DONE + api_keys Phase 5.B scaffold landed.
- Slot 6: deployment-api delegate-flip DONE + Phase 2.6 Step 4 audit complete + write-resume plan ready.
- Slot 7: writegate Phase 6.6 (ml-training + ml-inference) fully wired + Phase 6.7 strategy started.
- Slot 8: batch_live_symmetry Tab 2 codex docs shipped + alerting 10+ of 15 remaining items done.

**All 103 delegate-flip callsites on LDR by EOD** = critical-path gate for write-pause tomorrow (or later today if
operator is available).

---

## Spawn prompt — paste into each tab (slot N)

```text
You are slot N (Ikenna side). Today is 2026-05-18 (Cycle 2 Day-3 — delegate-flip day).

Boot:
1. SYNC TO LDR — from .tabs/<N>/:
     for d in */; do
       (cd "$d" && [ -d .git -o -f .git ] && git fetch origin live-defi-rollout --quiet && \
        git merge --ff-only origin/live-defi-rollout 2>/dev/null) ;
     done

2. Read unified-trading-pm/ikenna_orchestrator/AGENT_ONBOARDING.md

3. Read unified-trading-pm/plans/active/work_split_2026_05_18_ikenna.md § "Slot <N>"

4. Read your top plan-of-record.

5. Boot ack at unified-trading-pm/ikenna_orchestrator/pings/slot_<N>.md using `date -u`.

CRITICAL RULES:
* Plan-flip discipline: every shippable unit = (Half 1) commit + push, then (Half 2) flip
  checkbox in SAME AGENT TURN with docs(plans): prefix commit.
* Delegate-flip: bucket_name_ssot — use resolve_bucket_name(cloud=, kind=, asset_group=, env=)
  from unified_trading_library.cloud_interface.bucket_naming. Never inline gs:// f-strings.
* QG before push: bash scripts/quality-gates.sh (Pass 1). Then push.
* Conflict: git fetch before every execution-service/deployment-api commit; check for Harsh
  slot 2/7 commits on those repos.

Now begin.
```
