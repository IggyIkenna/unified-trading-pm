---
title: Ikenna's daily work-split — 2026-05-19 (Cycle 2 Day-4; full backlog sweep — all May-23 + no-deadline)
type: coordination-doc
status: active
created: 2026-05-19
deadline: 2026-05-23
horizon: 4 calendar days (19 May → 23 May); Cycle 2 close + Cycle 3 paper-smoke
companion_to: plans/active/work_split_2026_05_19_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-19
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
effective_concurrent_slots: 8
estimate_calibration_note: |
  Full-sweep day. All May-23-deadline + no-deadline backlog allocated across 8 implementer
  slots. Ikenna owns ~231 cal AI-days (2× Harsh's 116). Carries every deferred item from
  May-15 / May-16 / May-18 splits. Critical blocker: operator must trigger write-pause
  window FIRST (L3 + L5 flips gate on it). Inventory as of 2026-05-19 08:26 UTC:
  462 total / 236 May-23 critical-path / 97 no-deadline = 333 spreadable.
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

| Slot      | Theme                                                                                             | Cal AI-days | Plans owned                                                            |
| --------- | ------------------------------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------------- |
| 1         | Main orchestrator (continuous, uncounted)                                                         | —           | This LEDGER                                                            |
| 2         | code_freeze Phase 2.6 close (write-pause + L3/L5 + archive)                                       | ~35         | code_freeze §2.6                                                       |
| 3         | code_freeze Phase 2.0–2.5 gaps + batch_live_symmetry Tabs 1–3                                     | ~35         | code_freeze §2.0–2.5, batch_live_symmetry                              |
| 4         | api_keys Phase 3–4 + defi_recursive_borrow Phase 3–4                                              | ~34         | api_keys, defi_recursive_borrow                                        |
| 5         | writegate Phase 6.6/6.7 + live_pipeline Phase 3–5                                                 | ~30         | writegate, live_pipeline                                               |
| 6         | deployment_ui_lifecycle_tabs (full 6-tab restructure)                                             | ~30         | deployment_ui_lifecycle_tabs                                           |
| 7         | cross_cutting_deliverables (12.4) + simulation_scenarios_topology (7.6) + defi_master Phase 2–3   | ~27         | cross_cutting_deliverables, simulation_scenarios_topology, defi_master |
| 8         | defi_catalogue close (27.2 remaining, 87%) + defi_simulation_realism final (0.7) + dex_perp close | ~29         | defi_catalogue, defi_simulation_realism, dex_perp_and_venue_data       |
| 9         | batch_live_symmetry Tabs 4–7 + cme_polymarket_arb Phase 1 + promote_workflow_may23 residuals      | ~31         | batch_live_symmetry, cme_polymarket_arb, promote_workflow_may23        |
| **Total** |                                                                                                   | **~251**    |                                                                        |

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

1. - [ ] **L3 flip — UTL `get_bucket_name` → `resolve_bucket_name`** (36+ consumers in
         `unified_trading_library/cloud_interface/cloud_constants.py` + wrappers). Run QG. Push. (refactor 0.4×, ~8 =
         3.2 cal)
2. - [ ] **L5 flip — deployment-api `_BUCKET_TEMPLATES`** → `resolve_bucket_name()`. Run QG. Push. (refactor 0.4×, ~3 =
         1.2 cal)
3. - [ ] **Write-resume verification** — after operator redeploys: confirm manifest rows landing in env-tiered paths via
         `gcloud storage ls gs://{env-tiered-bucket}/` spot-check. (infra 0.8×, ~2 = 1.6 cal)
4. - [ ] **Archive old flat buckets** — run
         `bash deployment-service/scripts/archive-flat-buckets.sh    --env prod --cloud both` (30-day hold, not delete).
         (infra 0.8×, ~2 = 1.6 cal)
5. - [ ] **GAP-2.0.B** — Confirm Stage 0 drain covers BOTH GCP + AWS VM fleets. Doc update. (research 1.2×, ~1 = 1.2
         cal)
6. - [ ] **GAP-2.0.C** — Update CLAUDE.md "No fire-and-forget" HARD RULE with pre-migration drain addendum. (design
         0.6×, ~1 = 0.6 cal)
7. - [ ] **Reconcile phantoms** — run
         `python scripts/reconcile_phantom_manifest_rows_all.py    --asset-group cefi --dry-run` + repeat per
         asset_group. (infra 0.8×, ~2 = 1.6 cal)
8. - [ ] **Phase 2 freeze gate** — flip all remaining `- [ ]` gate items in code_freeze §2. Push `docs(plans):` flip
         commit. (design 0.6×, ~1 = 0.6 cal)

---

### Slot 3 — code_freeze Phase 2.0–2.5 gaps + batch_live_symmetry Tabs 1–3 — ~35 cal AI-days

**Part A — code_freeze remaining Phase 2 gaps** (open `[GAP]` items not covered by slot 2):

1. - [ ] **GAP-2.2.B** — Update CLAUDE.md "Honest absence" HARD RULE with Phase 2.2 GCS migration reference. (design
         0.6×, ~1 = 0.6 cal)
2. - [ ] **GAP-2.3.A** — Append Phase 2.X OHLCV legacy filename rename sub-section to code_freeze plan. (design 0.6×, ~2
         = 1.2 cal)
3. - [ ] **GAP-2.3.B** — Audit features-service readers for `ticks.parquet` literal path references. (research 1.2×, ~2
         = 2.4 cal)
4. - [ ] **Phase 2.5** — Run `manifest_cross_asset_rescan_design_2026_05_08.md` cross-asset `--apply-flips` sequence per
         the plan. (infra 0.8×, ~3 = 2.4 cal)
5. - [ ] **gcs_migration_bundle Phase 3** — Complete remaining items in
         `gcs_migration_bundle_pipeline_mode_2026_05_08.md` (plan at 2026-05-15 overdue, 4.8 cal left). Read plan for
         open `- [ ]` items. (infra 0.8×, ~6 = 4.8 cal)

**Part B — batch_live_symmetry Tabs 1–3** (plan at 34%, 19.7 cal left):

Read `batch_live_symmetry_2026_05_10.md` for open Tab 1/2/3 items. Tab 1 = codex SSOT batch, Tab 2 = UAC + UTL J1
helper + L7 sweep, Tab 3 = QG STEPs L2/L3/L7.

6. - [ ] **Tab 1 — codex SSOT batch** (cefi-batch-live.md + mode-axis-discipline.md). ~200 lines each. (design 0.6×, ~5
         = 3.0 cal)
7. - [ ] **Tab 2 — UAC J1 helper + L7 sweep** per batch_live_symmetry plan §Tab 2. (brand-new 1.0×, ~5 = 5.0 cal)
8. - [ ] **Tab 3 — QG STEPs L2/L3/L7 AST sweeps** per batch_live_symmetry plan §Tab 3. (refactor 0.4×, ~4 = 1.6 cal)
9. - [ ] **Plan checkboxes flip** for all items shipped. (0.5 cal)

---

### Slot 4 — api_keys Phase 3–4 + defi_recursive_borrow Phase 3–4 — ~34 cal AI-days

**Part A — api_keys_wallets_accounts_readiness Phase 3 (Copper) + Phase 4 (DeFi mainnet)** (plan at 63%, 23.7 cal left):

1. - [ ] **Phase 3.A — Copper real-fund-movement test** — Execute small-amount transfer to confirm Copper API is live.
         Verify idempotency + response schema. (infra 0.8×, ~2 = 1.6 cal)
2. - [ ] **Phase 3.B — CEFFU integration** — Start CEFFU KYB / API key sub-deliverables. Read api_keys §Phase 3.B for
         the sub-task list. (brand-new 1.0×, ~4 = 4.0 cal)
3. - [ ] **Phase 4.A — UAC DeFi wallet schema** — `WalletConfig` + `ChainWallet` + per-chain RPC wiring. (brand-new
         1.0×, ~3 = 3.0 cal)
4. - [ ] **Phase 4.B — PBM position-health endpoint** — per api_keys §4.C.B. (brand-new 1.0×, ~2 = 2.0 cal)
5. - [ ] **Phase 4.C — UTL shared pre-flight helper** — per api_keys §4.C.C. (brand-new 1.0×, ~2 = 2.0 cal)
6. - [ ] **Phase 4.D + 4.E — execution-service + DART wire-in** — per api_keys §4.C.D + 4.C.E. (brand-new 1.0×, ~1.5 =
         1.5 cal)

**Part B — defi_recursive_borrow Phase 3–4** (plan at 75%, 10.5 cal left):

7. - [ ] **Phase 3 — Sim contract integration** — wire Aave/Compound flash-loan receiver into sim engine. Read plan for
         open items. (design 0.6×, ~4 = 2.4 cal)
8. - [ ] **Phase 4 — Per-family backtest scenarios** — carry + recursive-borrow scenario sets. (design 0.6×, ~6 = 3.6
         cal)
9. - [ ] **Plan flips** for all shipped items. (0.5 cal)

---

### Slot 5 — writegate Phase 6.6/6.7 + live_pipeline Phase 3–5 — ~30 cal AI-days

**Part A — writegate Phase 6.6/6.7** (plan at 52%, 11.5 cal left):

1. - [ ] **Phase 6.6 — ml-training-service emission wiring** — `record_captured`/`record_empty` at model artifact write
         boundaries + UAC `SERVICE_OUTPUT_POLICIES` entry + tests. (brand-new 1.0×, ~5 = 5.0 cal)
2. - [ ] **Phase 6.6 — ml-inference-service emission wiring** — same pattern. (brand-new 1.0×, ~5 = 5.0 cal)
3. - [ ] **Phase 6.7 — strategy-service emission wiring** — signal output → `record_captured`. (brand-new 1.0×, ~3 = 3.0
         cal)
4. - [ ] **Phase 6.7 — risk-and-exposure-service emission wiring**. (brand-new 1.0×, ~2 = 2.0 cal)

**Part B — live_pipeline_mtds_mdps_features Phase 3–5** (15.0 cal budget):

Read `live_pipeline_mtds_mdps_features_2026_05_08.md` for remaining open items. Focus on:

5. - [ ] **Phase 3 MTDS real-time adapter** — pick 4–5 highest-priority live-mode items. (brand-new 1.0×, ~5 = 5.0 cal)
6. - [ ] **Phase 4 MDPS live consumer** — admission control wiring (Phase 2 of mdps_streaming unblocked by slot-2's
         Phase 1.2B ship on May-18). (brand-new 1.0×, ~3 = 3.0 cal)
7. - [ ] **Plan flips** for all shipped items. (0.5 cal)

---

### Slot 6 — deployment_ui_lifecycle_tabs (full 6-tab restructure) — ~30 cal AI-days

**Plan**: `deployment_ui_lifecycle_tabs_2026_05_08.md` (30.0 cal, no progress yet — TBD baseline).

This is the cross-cutting 6-tab restructure of the deployment UI. Read the full plan before starting. Key tabs: Deploy,
Status, Logs, Strategy, Kill-switch, Config.

1. - [ ] **Pre-audit** — read plan + identify current UI tab structure vs target. Grep for existing tab components in
         `unified-trading-system-ui/`. (research 1.2×, ~1 = 1.2 cal)
2. - [ ] **Tab 1 — Deploy lifecycle** — wiring VM launch events to UI deploy tab. (brand-new 1.0×, ~5 = 5.0 cal)
3. - [ ] **Tab 2 — Status / data-freshness** — per-service health + manifest freshness feed. (brand-new 1.0×, ~5 = 5.0
         cal)
4. - [ ] **Tab 3 — Logs / event-stream** — WebSocket log tail per VM / service (Harsh slot-7 shipped WebSocket VM
         streaming May-18; wire it into this tab). (brand-new 1.0×, ~5 = 5.0 cal)
5. - [ ] **Tab 4 — Strategy panel** — promote / demote / paper → live controls. (brand-new 1.0×, ~5 = 5.0 cal)
6. - [ ] **Tab 5 — Kill-switch** — manual emergency halt per strategy / per service. (brand-new 1.0×, ~4 = 4.0 cal)
7. - [ ] **Plan flips** for each tab shipped. (0.5 cal)

---

### Slot 7 — cross_cutting_deliverables + simulation_scenarios_topology + defi_master — ~27 cal AI-days

**Part A — cross_cutting_may23_deliverables** (plan at 60%, 12.4 cal left):

Read `cross_cutting_may23_deliverables_2026_05_08.md` for open `- [ ]` items. Focus on:

1. - [ ] **Strategy catalogue** — populate archetype × venue matrix in UAC. (design 0.6×, ~4 = 2.4 cal)
2. - [ ] **Strategy IDs** — stable ID schema in UAC + registry for each catalogue row. (design 0.6×, ~4 = 2.4 cal)
3. - [ ] **Client model + accounts** — wire capital allocation matrix per (client, archetype, venue). (brand-new 1.0×,
         ~3 = 3.0 cal)

**Part B — simulation_scenarios_topology** (plan at 62%, 7.6 cal left):

4. - [ ] **Phase 3 — scenario-runner integration** — per the May-12 design-shipped spec. Wire scenario fan-out into
         risk + alerting. (brand-new 1.0×, ~5 = 5.0 cal)
5. - [ ] **Phase 4 — per-scenario fixture sets** — 10 scenarios × fixture each. (brand-new 1.0×, ~3 = 3.0 cal)

**Part C — defi_master Phase 2–3** (plan at 33%, 9.4 cal left):

6. - [ ] **Phase 2 — MTDS wiring for chain primitives** — per-protocol handlers referencing new UAC `ChainKind` + chain
         configs (shipped May-18 UAC@9aea2b7). (design 0.6×, ~4 = 2.4 cal)
7. - [ ] **Phase 3 — instruments-service CLOB adapters** — per defi_master open items. (design 0.6×, ~3 = 1.8 cal)
8. - [ ] **Plan flips** for all shipped items. (0.5 cal)

---

### Slot 8 — defi_catalogue close + defi_simulation_realism + dex_perp — ~29 cal AI-days

**Part A — defi_catalogue_chain_primitives** (plan at 87%, 27.2 cal left):

Read plan for the 9 remaining open items. Most are Phase 6 backfills + Phase 7 instrument wiring.

1. - [ ] **Phase 6 — per-chain backfill scripts** (items 6J, 7E unblocked — upstream shipped). Run backfill for each
         chain primitive. (infra 0.8×, ~6 = 4.8 cal)
2. - [ ] **Phase 7.I — defi_catalogue instruments cross-ref** — owned by slot 1 per May-18 annotation; check if slot 1
         released it; if yes proceed. (design 0.6×, ~3 = 1.8 cal)
3. - [ ] **Remaining open items** — read plan body and ship all remaining `- [ ]` items in order. (mixed, ~10 = 8.0 cal)
4. - [ ] **Close defi_catalogue** — flip all remaining checkboxes; mark plan `status: complete` if all done. Push. (0.5
         cal)

**Part B — defi_simulation_realism** (plan at 98%, 0.7 cal left — 1 item):

5. - [ ] **Final item** — read plan for the single remaining `- [ ]` and ship it. (brand-new 1.0×, ~1 = 1.0 cal)

**Part C — dex_perp_and_venue_data** (plan at 94%, 0.5 cal left):

6. - [ ] **Final 2 items** — read plan for open items and ship. (brand-new 1.0×, ~1 = 1.0 cal)

**Part D — hard_schema_enforcement** (no-deadline, 4.8 cal):

7. - [ ] **Open items** — read `hard_schema_enforcement_2026_05_08.md` and ship remaining items. (design 0.6×, ~8 = 4.8
         cal)

---

### Slot 9 — batch_live_symmetry Tabs 4–7 + cme_polymarket_arb + promote_workflow_may23 — ~31 cal AI-days

**Part A — batch_live_symmetry Tabs 4–7** (continuation from slot 3's Tabs 1–3):

1. - [ ] **Tab 4 — features-service ModeHandler lift (4 families)** — commodity / cross_instrument / multi_timeframe /
         calendar. Per plan §Tab 4. (brand-new 1.0×, ~6 = 6.0 cal)
2. - [ ] **Tab 5 — feature emission wiring** — per plan §Tab 5. (brand-new 1.0×, ~5 = 5.0 cal)
3. - [ ] **Tabs 6–7** — remaining plan tabs. Read plan for items. (brand-new 1.0×, ~4 = 4.0 cal)

**Part B — cme_polymarket_arb Phase 1** (no-deadline, 15.0 cal):

4. - [ ] **Phase 1 — InstrumentType.EVENT_CONTRACT + UAC schema** — per `cme_polymarket_arb_2026_05_08.md`. (brand-new
         1.0×, ~5 = 5.0 cal)
5. - [ ] **Phase 2 — MTDS Polymarket + CME adapter scaffolds** — per plan Phase 2. (brand-new 1.0×, ~5 = 5.0 cal)

**Part C — promote_workflow_may23 residuals** (plan at 62%, 1.6 cal left):

6. - [ ] **Remaining open items** — read `promote_workflow_may23_cli_path_2026_05_10.md` and ship all remaining `- [ ]`
         items. (design 0.6×, ~3 = 1.6 cal)
7. - [ ] **Plan flips** for all shipped. (0.5 cal)

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
