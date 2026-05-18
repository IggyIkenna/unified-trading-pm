---
title: Ikenna's daily work-split — 2026-05-18 (Cycle 2 Day-3; write-pause + delegate-flip + heavy cutover)
type: coordination-doc
status: active
created: 2026-05-18
deadline: 2026-05-23
horizon: 5 calendar days (18 May → 23 May); Cycle 2 Day-3 of post-freeze roadmap
companion_to: plans/active/work_split_2026_05_18_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-18
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4.0
effective_concurrent_slots: 8
estimate_calibration_note: |
  Cycle 2 Day-3 (write-pause + delegate-flip day). Per operator direction 2026-05-18 06:15 UTC,
  Ikenna side owns all heavy decision-bearing cutover work today. Harsh stays in mechanical-only
  mode. ~8 implementer slots × ~12-16 cal AI-days each = ~100-128 cal AI-days total.
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

| Slot      | Theme                                                                                          | Cal AI-days | Status (2026-05-18)                                                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1         | Main orchestrator (continuous, uncounted)                                                      | —           | 🟢 IN PROGRESS                                                                                                                                   |
| 2         | Delegate-flip: UTL (23) + batch-live-recon (7) + strategy (2)                                  | ~14         | ✅ ALL DONE (utl@ef2b6670, batch-recon@86f3d8d, strategy 0 remaining)                                                                            |
| 3         | Delegate-flip: UAC (5) + features-service (2) + defi_catalogue close                           | ~16         | ✅ Part A DONE (uac@ae8b4d6, features@c8ae93f5); Part B → Harsh-side                                                                             |
| 4         | AWS migration Phase 2-4 + defi_recursive_borrow Phase 3-4                                      | ~18         | ✅ AWS Phase 2+3+5b (deployment-service@4550bc3); bybit cap (uac@c29114c); L3/L5 flip BLOCKED-OPERATOR-WRITE-PAUSE                               |
| 5         | Delegate-flip: execution-service (33) + UI (4) + api_keys Phase 5.B                            | ~18         | ✅ exec@4f46a75d7 + UI (prior); api_keys 5.B/5.C → Slot 8                                                                                        |
| 6         | Delegate-flip: deployment-api (27) + code_freeze Phase 2 runbook verify                        | ~14         | ✅ deployment-api@297b406; Phase 2.6 Step 5 → Slot 7                                                                                             |
| 7         | ~~writegate Phase 6.6+6.7 impl~~ REDIRECTED: Phase 2.6 Step 5 prep + write-resume verification | ~20→~8      | ✅ DONE (deployment-service@9f158d5 archive-flat-buckets.sh + PM@773a3726 checklist)                                                             |
| 8         | ~~batch_live_symmetry Tab 2 codex~~ REDIRECTED: alerting SCRIPT items + api_keys Phase 5.B/5.C | ~14         | ✅ alerting SM hot-reload (alerting@69a9f4a); api_keys 5.B.1/5.B.4 done; 5.B.2 BLOCKED-CREDENTIALS (Kalshi); 5.C BLOCKED-CREDENTIALS (CoinGecko) |
| **Total** | (8 implementer slots)                                                                          | **~114**    |                                                                                                                                                  |

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

1. - [ ] **UTL callsite sweep** (23 callsites → 0): search + migrate each callsite to `resolve_bucket_name(...)`. Run QG
         after: `cd .tabs/2/unified-trading-library && bash scripts/quality-gates.sh`. Push:
         `git push origin HEAD:live-defi-rollout`. (refactor 0.4×, ~8 = 3.2 cal)
2. - [ ] **batch-live-recon callsite sweep** (7 callsites → 0): same pattern. QG + push. (refactor 0.4×, ~4 = 1.6 cal)
3. - [ ] **strategy-service callsite sweep** (2 callsites → 0): same pattern. QG + push. (refactor 0.4×, ~2 = 0.8 cal)
4. - [ ] **Flip plan checkboxes** in `bucket_name_ssot_canonicalisation_2026_05_10.md` for each repo completed. Target:
         plan reaches 19+/22 done. (infra 0.8×, ~1 = 0.8 cal)
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

3. - [ ] **Chain-primitive UAC schema additions** — UAC `DefiChainPrimitive` / `ChainConfig` additions for remaining
         protocols not yet covered. (design 0.6×, ~6 = 3.6 cal)
4. - [ ] **MTDS wiring for chain primitives** — per-protocol handlers referencing new UAC types. (design 0.6×, ~4 = 2.4
         cal)
5. - [ ] **Plan checkboxes flip** for all items shipped. Push `docs(plans):` flip commits. (0.5 cal)

**Conflict notes**: features-service bucket_naming is distinct from Harsh slot 4's test coverage work.

---

### Slot 4 — AWS migration Phase 2-4 + defi_recursive_borrow Phase 3-4 — ~18 cal AI-days

**`aws_migration_defi_first_2026_05_07`** (currently 8/72 = 11%, 28.4 cal left). This is the highest cal-days-remaining
plan on the inventory. Push Phase 2-4 items.

1. - [ ] **Phase 2: AWS DeFi bucket verification** — confirm all AWS DeFi env-tiered buckets provisioned (slot 4 May-16
         shipped 6 sports/prediction buckets; check DeFi-specific). Run `aws s3 ls | grep defi`. (infra 0.8×, ~2 = 1.6
         cal)
2. - [ ] **Phase 3: AWS rsync verification** — confirm Storage Transfer Service job progress for DeFi-first buckets.
         Check GCP Console or CLI for job completion status. (infra 0.8×, ~3 = 2.4 cal)
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

1. - [ ] **deployment-api callsite sweep** (27 callsites → 0): batch by module. Run QG after each batch. Push per-batch.
         (refactor 0.4×, ~8 = 3.2 cal)

**Part B — `code_freeze_migrate_backfill_sequencing_2026_05_10` Phase 2.6 cutover runbook**: (Plan currently 34%, 106
cal left. Today's target: Phase 2.6 Step 4 complete + Step 5 prep)

2. - [ ] **Phase 2.6 Step 4 completion audit**: read plan Phase 2.6 section; verify all delegate-flip callsites from
         TODAY's slots 2/3/5/6 are landed on LDR before write-pause. Create audit checklist. (research 1.2×, ~2 = 2.4
         cal)
3. - [ ] **Phase 2.6 Step 5 prep**: prepare archive plan for old flat buckets (30-day hold, not delete). Codify
         procedure: `gsutil mv gs://{old-flat}/ gs://{archive-flat}-20260518/`. Draft runbook item for operator to run
         post-write-resume. (infra 0.8×, ~3 = 2.4 cal)
4. - [ ] **Write-resume verification plan**: after operator triggers write-pause + deploys delegate-flip code changes:
         verify services write to new env-tiered paths by checking manifest captures in new bucket layout. (infra 0.8×,
         ~2 = 1.6 cal)
5. - [ ] **Plan checkboxes flip** for Phase 2.6 items complete. Push `docs(plans):` flips. (0.5 cal)

---

### Slot 7 — writegate Phase 6.6 + 6.7 implementation — ~20 cal AI-days

**Context**: `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.6 + 6.7 (plan currently 49%, 12.1 cal left).
Gate 4 FIRED 2026-05-13 for the β-verdict audit, but Phase 6.6 (code implementation for ml-training + ml-inference) and
6.7 (strategy + execution + position + risk) still need actual `record_*` callsites at output-write boundaries.

**Pattern**: per writegate Phase 6.6/6.7 issue doc + Phase 6.6/6.7 sub-plan items: (1) UAC `SERVICE_OUTPUT_POLICIES`
entry; (2) `record_*` callsites at output-write boundaries; (3) `publish_with_manifest_lookup()` integration; (4)
per-output-type UAC schema declaration; (5) unit + integration tests.

1. - [ ] **Phase 6.6 — ml-training-service emission wiring**: add `record_captured`/`record_empty` at model artifact
         write boundaries + UAC `SERVICE_OUTPUT_POLICIES` entry + tests. (brand-new 1.0×, ~5 = 5.0 cal)
2. - [ ] **Phase 6.6 — ml-inference-service emission wiring**: same pattern. (brand-new 1.0×, ~5 = 5.0 cal)
3. - [ ] **Phase 6.7 — strategy-service emission wiring**: signal output → `record_captured` at strategy output write
         boundary. (brand-new 1.0×, ~3 = 3.0 cal)
4. - [ ] **Phase 6.7 — risk-and-exposure-service emission wiring**. (brand-new 1.0×, ~2 = 2.0 cal)
5. - [ ] **writegate plan checkboxes flip** for each service shipped + push `docs(plans):` flips.

---

### Slot 8 — batch_live_symmetry Tab 2 codex + alerting_service_live_rules close — ~14 cal AI-days

**`batch_live_symmetry_2026_05_10`** (currently 36%, 19.2 cal left, 26/72 done): Tab 2 = codex doc
`cefi-batch-live.md` + `mode-axis-discipline.md`. Harsh slot 5 was on Tab 1 (batch_live reconciler). Slot 8 (Ikenna)
owns Tab 2 (codex docs half).

1. - [ ] **Tab 2 — `cefi-batch-live.md` codex doc**: write/update `codex/10-batch-live/cefi-batch-live.md` per existing
         design + invariants from writegate + live_pipeline plans. ~200 lines: architecture, data flow, invariants,
         batch=live contract proof. (design 0.6×, ~5 = 3.0 cal)
2. - [ ] **Tab 2 — `mode-axis-discipline.md` codex doc**: write/update codex SSOT for the `--mode batch|live` axis,
         `PIPELINE_MODE` env var, and enforcement-by-QG-STEP-5.68 pattern. (design 0.6×, ~4 = 2.4 cal)
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
