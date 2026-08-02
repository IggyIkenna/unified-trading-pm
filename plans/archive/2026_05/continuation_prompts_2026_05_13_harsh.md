---
doc_type: plan
title: Harsh-side Day-4 continuation prompts — paste-ready spawn prompts for 10-slot fan-out
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, e2e-testing, execution-service, features-service, instruments-service, market-data-processing-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
type: coordination-doc
companion_to: plans/active/work_split_2026_05_13_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

# Day-4 continuation prompts (Harsh-side, 2026-05-13)

> **Paste one prompt per fresh Claude Code session** in `cd .tabs/<N>/`. Each prompt is self-contained — agent reads
> onboarding + work-split + plan-of-record + boots itself with a status ack to `harsh_orchestrator/pings/slot_<N>.md`.
>
> **For ALL slots**: paste `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` content at the top of every
> sub-agent Task call. Sub-agents inherit nothing.

---

## Slot 2 — Propagation chain Phase 3+4+2.A (🔴 CRITICAL PATH — Gate 1)

```
You are Harsh-side slot 2, Day-4 (2026-05-13) of the 4-day cycle to 2026-05-15 freeze gate. Today is Harsh-side
ONLY — Ikenna is on connecting flights all day. Your slot inherits Ikenna slot 4's unfinished work.

MODEL DIRECTIVE: Opus 4.7, thinking: high. Cross-repo design sweep + 9-sub-agent fan-out qualifies for Opus.

READ in order (full reads — do not skim):
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 2"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 2"
5. unified-trading-pm/plans/active/expected_unattempted_propagation_chain_2026_05_12.md (FULL READ — >50KB; the
   plan body is your spec, do not act from summary)
6. unified-trading-pm/ikenna_orchestrator/pings/slot_4.md (Ikenna slot 4 session-close handover from yesterday)

SCOPE (~2.5 cal AI-days, 9-sub-agent fan-out):
A. Phase 3.1-3.N (6 sub-agents — PARALLEL): features-service per-module. One sub-agent per family:
   delta_one / calendar / onchain / volatility / sports / commodity. Pattern: Option A runtime comparison at
   _get_instruments() call — compare instruments-service catalog vs post-filter set, write
   expected_unattempted(EXPECTED_OUTSIDE_PROCESSING_SCOPE) for `all - in_scope`. NO UAC frozenset.
B. Phase 4 (2 sub-agents — PARALLEL with A): ml-training-service + ml-inference-service. Same Option A pattern.
C. PART C / writegate 2.A (1 sub-agent — PARALLEL with A+B): market-data-processing-service.
   Delete `_create_empty_output`; route empty_confirmed→forward-fill, attempted_failed→NaN,
   expected_unattempted→propagate via 4-state output.

SUB-AGENT FAN-OUT: send all 9 Task calls in ONE message. Paste SUB_AGENT_MANDATORY_RULES.md at top of every Task
prompt. Each sub-agent commits + pushes own slice to `live-defi-rollout` independently.

DONE-DEFINITION (must ALL be true):
- 8 services + MDPS routing all shipped to origin/live-defi-rollout
- 4 unit tests per service pass
- Plan checkboxes flipped (`docs(plans):` commit)
- Cross-side ping filed in plans/active/_agent_pings.md: "GATE 1 FIRED — propagation chain Phase 3+4+2.A complete"

CRITICAL: ping slot 1 main IMMEDIATELY when Gate 1 fires — slots 3 + 6 are blocked on this.

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_2.md per AGENT_ONBOARDING template.
Use `date -u` for all timestamps (machine clock is IST). Conditional-push pattern per CLAUDE.md.
Don't reassign your slot — finish through to DONE.
```

---

## Slot 3 — Bucket SSOT residuals

```
You are Harsh-side slot 3, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Theme: bucket-name
SSOT residuals — provision manual-audit buckets + apply Q5 features rename + PART B apply-flips when Gate 1 fires.

MODEL DIRECTIVE: Sonnet 4.6, thinking: high.

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 3"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 3"
5. unified-trading-pm/plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md (FULL READ — Q5+Q7 sections;
   Phase 0c provisioning)
6. unified-trading-pm/ikenna_orchestrator/pings/slot_8.md § "manual-audit bucket provisioning handoff" (Ikenna
   slot 8 → slot 4 handoff yesterday; you absorb that work)

SCOPE (~1.5 cal AI-days):
A. Provision 6 manual-audit buckets (3 envs × 2 clouds GCP+AWS). Apply ≥7-year retention lock (GCP Object
   Retention Lock; AWS S3 Object Lock COMPLIANCE). Coldline/Glacier-IA after 90d. Operator has ADC admin perms;
   you do not pause for approval.
B. Apply Q5 features-cross-instrument + features-multi-timeframe rename (A5 operator-resolved 2026-05-11 = Option
   1 aliased): edit cloud-providers.yaml + update UTL bucket_naming resolver + refresh parity test snapshot.
C. PART B apply-flips reconciler — POLL the cross-side _agent_pings.md every ~5 min for slot 2's "GATE 1 FIRED"
   ping. When it lands, run reconcile_legacy_blank_to_typed_reason.py --apply-flips for cefi/defi/tradfi on
   same-region GCE VM. Triage sports/prediction residuals as separate findings (slot 9 owns classifier extension).
D. Q7(b) pnl/positions/risk-store-defi shape — if Ikenna's answer lands mid-shift via cross-side ping or
   operator chat, ship the rename in same logical unit; otherwise leave item unchecked with annotation.

DONE-DEFINITION:
- `gcloud storage buckets list | grep manual-audit` → 3 buckets each on GCP + AWS, retention verified
- Q5 yaml shipped, parity test green
- If Gate 1 fires: apply-flips run with before/after counts in plan body

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_3.md.
```

---

## Slot 4 — defi_simulation_realism Phases 4-6 + Harsh carry-forward

```
You are Harsh-side slot 4, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Theme: AMM simulation
realism — Phase 4-6 implementation (Ikenna slot 6 yesterday's design ↔ your implementation).

MODEL DIRECTIVE: Sonnet 4.6, thinking: high.

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 4"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 4"
5. unified-trading-pm/plans/archive/defi_simulation_realism_2026_05_10.md (FULL READ — Phase 1A/2A/3 design from
   Ikenna PM@3b76a5ef + d66b0f9f; your scope = Phases 4-6 + 5B/5C/6B/6C)
6. unified-trading-pm/codex/04-architecture/amm-slippage-simulation.md (full design spec from Ikenna)

SCOPE (~2 cal AI-days):
A. Phase 4-6 per-pool-class modules: NEW curve.py / balancer.py / solana_clmm.py / solidly_fork.py / aggregator.py
   in execution-service/amm/. Refactor engine.py:_amm_match_impl (currently hardcoded UniswapV2Pool at line 471)
   into PoolMatcher dispatcher.
B. Golden test set: per-PoolShape JSON fixtures under
   execution-service/tests/integration/fixtures/amm_golden_swaps/. Pytest harness per design.
C. Phases 5B/5C/6B/6C (Harsh carry-forward): self-contained per plan body.

CRITICAL CORRECTION (from Ikenna's design notes): V2/V3/V4 pool classes ALREADY EXIST in amm.py:52,259,403 —
Phase 2A is Protocol-conformance refactor + dispatcher rewrite, NOT greenfield V3/V4 build.

DONE-DEFINITION:
- 5 new pool-class modules shipped + Protocol-conformance tests pass
- Golden fixtures + harness shipped; ≥1 fixture per pool-class smoke-tests against expected swap output
- Plan checkboxes flipped

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_4.md.
```

---

## Slot 5 — Audit-records PB-1/2/3 all 3 pre-cutover (NEW PLAN)

```
You are Harsh-side slot 5, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Theme: execution-service
audit-records — fix 3 bugs (overwrite, retention-lock gap, wrong-customer-ID-path) all pre-cutover per operator
decision 2026-05-13.

MODEL DIRECTIVE: Sonnet 4.6, thinking: high.

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 5"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 5"
5. unified-trading-pm/plans/archive/issues/codex_audit_position_balance_2026_05_12.md § PB-1, PB-2, PB-3
6. unified-trading-pm/cursor-configs/CLAUDE.md § "Observability" — "Audit records: append-only, immutable, in
   GCS audit/{client_id}/{date}/{event_type}/"

SCOPE (~2.5 cal AI-days):
A. FILE NEW PLAN at plans/active/audit_records_pb_1_2_3_pre_cutover_2026_05_13.md (Phase 1 = scope + grep audit,
   Phase 2 = implementation, Phase 3 = retention-lock provisioning). Frontmatter: estimate_class=brand-new,
   estimate_calibrated_ai_days=2.5, deadline=2026-05-22 (pre-cutover).
B. PB-1 (overwrite → append-only JSONL): refactor execution-service audit-writer to write
   `audit/{client_id}/{date}/{event_type}/{client_order_id}_{ts}.jsonl` (one event per file, NOT same-key blob
   overwrites).
C. PB-2 (retention-lock): provision audit-records bucket via UTL resolve_bucket_name(kind="audit-records") +
   apply ≥7-year retention (GCP Object Retention Lock + AWS S3 Object Lock COMPLIANCE).
D. PB-3 (wrong customer-ID path): currently `client_order_id` is being filed where `client_id` should be in the
   path slot. Fix the path layout function in execution-service audit-writer.

DONE-DEFINITION:
- New plan filed + Phases 1-3 implemented
- Write-same-key-twice test: both events appear in append-only JSONL
- gcloud storage buckets describe shows retentionPolicy.retentionPeriod ≥ 220752000s (7 years)
- Integration test verifies path layout `audit/{client_id}/...` not `audit/{client_order_id}/...`

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_5.md.
```

---

## Slot 6 — TradFi phantom-audit Databento-aware + manifest reconciliation operational

```
You are Harsh-side slot 6, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Theme: manifest
reconciliation — extend phantom audit (TradFi Databento-aware) + run 15 dry-runs (5 AGs × 3 reconcilers) + apply-flips
when Gate 1 fires + phantom audit on GCE VM (Gate 3).

MODEL DIRECTIVE: Sonnet 4.6, thinking: high.

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 6"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 6"
5. unified-trading-pm/plans/archive/2026_05/manifest_cross_asset_rescan_design_2026_05_08.md
6. unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md § "Phantom audit"
7. instruments-service/scripts/reconcile_phantom_manifest_rows_all.py (current Databento gaps in drift-axes)

SCOPE (~2 cal AI-days):
A. Extend reconcile_phantom_manifest_rows_all.py with Databento-aware drift-axes: per-schema-bundle paths, sports
   per-league SSOT + UAC date-clips, cross-asset venue-less. Per-cluster real-vs-false-pos verify (the previous
   4.3% TradFi phantom rate was ≈ stale-audit-path false-positives).
B. Launch same-region GCE VM (asia-northeast1) + run 15 dry-runs:
   - reconcile_legacy_blank_to_typed_reason.py --asset-group {cefi,defi,tradfi,sports,prediction} --dry-run
   - reconcile_expected_absence_reasons.py --asset-group ... --dry-run
   - reconcile_phantom_manifest_rows_all.py --asset-group ... --dry-run
   Upload logs to gs://deployment-scripts-{pid}/recon-logs/2026-05-13/.
C. POLL cross-side ping for Gate 1 fire (slot 2). When fires: run --apply-flips for cefi/defi/tradfi (NOT
   sports/prediction — those go to slot 9 once classifier extension lands).
D. Phantom audit (Gate 3): same-region GCE VM run with full manifest read. Triage real phantoms; file follow-ups
   for non-trivial.

DONE-DEFINITION:
- 15 dry-run logs uploaded
- Phantom-recon plan updated with per-AG real-vs-FP table
- Apply-flips run for cefi/defi/tradfi (if Gate 1 fires today) with before/after manifest counts
- Phantom audit Gate 3 results table

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_6.md.
```

---

## Slot 7 — AlertCodes + Breakers + Telegram channel split + mock_data tail

```
You are Harsh-side slot 7, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Theme: alerting +
breakers — 12 enum extensions pre-cutover (operator decision 2026-05-13) + Telegram channel split + mock_data Phase
3.C/3.D tail.

MODEL DIRECTIVE: Sonnet 4.6, thinking: high.

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 7"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 7"
5. unified-trading-pm/plans/archive/2026_05/alerting_service_live_rules_2026_05_07.md Phase 1.E
6. unified-trading-pm/plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md Phase 1.A + Phase 4
7. unified-trading-pm/plans/active/mock_data_pipeline_benchmarking_2026_05_10.md Phase 3.C + 3.D
8. unified-trading-pm/plans/active/_agent_pings.md [2026-05-12 19:35 UTC slot 7 → harsh-main] — original 12-gap surface

SCOPE (~2 cal AI-days):
A. 8 AlertCode StrEnum extensions (UAC canonical/crosscutting/alerting.py): VENUE_HALTED / LENDING_POOL_PAUSED /
   LENDING_BORROW_CAP_REACHED / LENDING_UTILIZATION_HIGH / MARKET_DATA_STALE / GAS_PRICE_SPIKE /
   GAS_BUDGET_EXCEEDED / KILL_SWITCH_ORACLE_DIVERGENCE. Add route entries in alerting-service route map.
B. 4 CircuitBreakerId + BreakerConfig extensions (UAC): ORACLE_STALENESS_SECONDS, per-chain RPC_OUTAGE_SECONDS,
   ARBITRAGE_PRICE_DISPERSION `applies_to` seed for RPC_OUTAGE_SECONDS, LENDING_POOL_UNAVAILABLE_SECONDS.
C. Telegram channel split: change alerting-service notifier to read NEW env var TELEGRAM_CHAT_ID_OPS for runtime
   alerts; existing TELEGRAM_CHAT_ID stays for CI/QG. If operator hasn't provided new chat_id yet (cross-side or
   chat ping), use existing TELEGRAM_CHAT_ID as fallback + ADD new env var slot in alerting-service config so
   when operator provides the chat_id, it's a 5-min change.
D. mock_data Phase 3.C/3.D: per-reader threading for 4 stages (mdps_compute / features / ml_inference /
   matching_engine) that exit nonzero. Re-run benchmark VM matrix once threading lands.

DONE-DEFINITION:
- 12 enum entries shipped to UAC + alerting-service routing wired + unit tests
- Telegram routing tested via dry-run notify-telegram.yml invocation
- mock_data benchmark report shows 4 previously-nonzero stages exit 0

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_7.md.
```

---

## Slot 8 — 🆕 GMX/DRIFT venue capability refactor (REVERT axis_override)

```
You are Harsh-side slot 8, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Theme: GMX/DRIFT
venue capability refactor — REVERT yesterday's axis_override approach (UAC@7c8482e) per operator+Ikenna chat 11:22
IST. Make perp-eligibility a CAPABILITY, not an asset_group filter.

MODEL DIRECTIVE: Sonnet 4.6, thinking: high. 3-sub-agent fan-out (UAC + strategy-service + MTDS).

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 8"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 8"
5. unified-trading-pm/plans/archive/cross_asset_group_catalogue_audit_2026_05_10.md (Phase 1C — re-opens with new
   shape; lines 206-208 + status table 537/567)
6. unified-trading-pm/plans/active/_agent_pings.md [2026-05-13 06:00 UTC GMX/DRIFT direction CORRECTION] — operator
   guidance verbatim

SCOPE (~2.5 cal AI-days, 3-sub-agent fan-out — send all 3 Task calls in ONE message):

Sub-agent A (UAC revert + venue cleanup):
- Drop DEFI_VENUE_AXIS_OVERRIDES dict from unified_api_contracts/registry/defi_venues.py (added by UAC@7c8482e)
- Drop cross-ref comment in defi_venue_capabilities.py:130
- Remove GMX-ARBITRUM / GMX-AVALANCHE / DRIFT-SOLANA from VENUES_BY_ASSET_GROUP["cefi"]
  (market_data_categories.py — CF-1/CF-2/CF-9/CF-10 in catalogue audit)
- Verify VENUES_BY_ASSET_GROUP["defi"] includes them (add if missing)
- Verify defi_venue_capabilities.py entries intact (perp_funding / liquidations / oracle_prices)
- Flip catalogue audit Phase 1C from "✅ DONE axis_override" back to unchecked with new shape narrative

Sub-agent B (strategy-service capability query):
- carry_staked_basis + arbitrage_price_dispersion archetype perp-hedge venue eligibility: change from
  `asset_group == "cefi"` filter to capability check (`perp_funding in DATA_TYPE_CAPABILITIES[venue]`)
- Same for cross-venue funding arb selector
- Grep `asset_group == "cefi"` / `VENUES_BY_ASSET_GROUP["cefi"]` workspace-wide; refactor each where semantic
  intent is "perp-eligible venues"
- Tests: assert GMX-ARBITRUM + DRIFT-SOLANA appear in perp-hedge eligible set for both archetypes

Sub-agent C (MTDS perp_funding_handler audit):
- Audit market-tick-data-service for cefi-only assumptions in perp_funding handler (or equivalent)
- Make asset_group-agnostic if needed; verify GMX/DRIFT data flows correctly
- Test: dry-run a 1-day batch for GMX-ARBITRUM; verify manifest writes land under
  gs://market-data-tick-defi-prd-{pid}/ (NOT cefi bucket)

DONE-DEFINITION:
- UAC revert pushed + downstream tests pass
- Strategy-service perp-eligibility unit tests pass for both archetypes including GMX/DRIFT
- MTDS dry-run for GMX-ARBITRUM produces parquet under defi bucket
- Cross-side ping filed: "GMX/DRIFT capability refactor COMPLETE — axis_override REVERTED + capability-check
  shipped + MTDS routing verified DeFi"

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_8.md.
```

---

## Slot 9 — Sports+Prediction reconciler + LookaheadBias 6 wire-ins + strategy-paper VM (slot 9 NEW worktree)

```
You are Harsh-side slot 9, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Slot 9 is a NEW
worktree (provisioned this morning at .tabs/9/ on tab/hk/9). Theme: classifier extensions — sports+prediction
reconciler + LookaheadBias 6 wire-ins + strategy-paper VM verification carry-forward.

MODEL DIRECTIVE: Sonnet 4.6, thinking: high. 6-sub-agent fan-out for LookaheadBias.

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 9"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 9"
5. unified-trading-pm/plans/archive/2026_05/code_freeze_migrate_backfill_sequencing_2026_05_10.md § "freeze-gate item 5"
   (LookaheadBias)
6. unified-trading-pm/plans/archive/2026_05/promote_workflow_may23_cli_path_2026_05_10.md (strategy-paper VM smoke)
7. unified-trading-library/unified_trading_library/legacy_reason_classifier.py (current classifier — extend with
   sports + prediction asset-group rules)

SCOPE (~2.5 cal AI-days):
A. Sports+Prediction classifier extension (~1-2 cal AI-days):
   - Extend legacy_reason_classifier.py with sports rules: EXPECTED_PAUSED_LEAGUE / EXPECTED_PRE_SEASON /
     EXPECTED_POST_SEASON / EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE. Lookup from instruments-service sports SSOT.
   - Prediction rules: MARKET_LIFECYCLE states (pre-launch / resolved / settled) per UAC
     market_lifecycle_event_history.
   - ≥4 unit tests per asset-group rule.
B. LookaheadBias 6 wire-ins (~1 cal AI-day, 6 sub-agents PARALLEL):
   - One sub-agent per feature family: delta_one / volatility / calendar / commodity / cross_instrument /
     multi_timeframe.
   - Flip LookaheadBiasError from "warn" to strict-mode "raise" in each module.
   - Send all 6 Task calls in ONE message. Each commits + pushes own slice independently.
C. Strategy-paper VM verification (~30 min carry-forward from slot 3 Day-3):
   - Re-launch strategy-paper-carry-staked-basis-20260513-AM smoke VM with Phase 2 P0 resolver fix
     (strategy-service@61dc112 + e2e-testing@8427dc0)
   - Verify event stream (STARTED + ≥1 progress event/hour + STOPPED) per CLAUDE.md "No fire-and-forget VM
     launches"
   - Ship 2 deferred items: ServiceBootstrap wire-in into colocated_engine.py + self-delete trap in
     setup-data-pipeline-vm.sh

DONE-DEFINITION:
- Sports + prediction classifier rules + tests pass
- 6 LookaheadBiasError wire-ins shipped + tests pass + freeze-gate item 5 ✅ flipped
- strategy-paper VM emits STARTED/STOPPED + self-deletes; ServiceBootstrap wire-in shipped

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_9.md (NEW per-slot ping file; create with template
from pings/README.md).
```

---

## Slot 10 — Day-3 quick wins: MDPS tests + Phase 4.FEATURES + dex_perp + EigenLayer (slot 10 NEW worktree)

```
You are Harsh-side slot 10, Day-4 (2026-05-13). Today is Harsh-side ONLY — Ikenna on flights. Slot 10 is a NEW
worktree (provisioned this morning at .tabs/10/ on tab/hk/10). Theme: high-leverage Day-3 quick wins — MDPS test
fixes (closes 19-test bug) + Phase 4.FEATURES sweep (closes freeze-gate item 3 to 9/9) + dex_perp Phase 2/3
remainder.

MODEL DIRECTIVE: Sonnet 4.6, thinking: high.

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "▶ NEW SHIFT 2026-05-13" + § "Slot 10"
4. unified-trading-pm/plans/archive/2026_05/work_split_2026_05_13_harsh.md § "Slot 10"
5. unified-trading-pm/plans/archive/2026_05/code_freeze_migrate_backfill_sequencing_2026_05_10.md § "freeze-gate item 3"
   (Phase 4.FEATURES — last sub-item needed for 9/9 closure)
6. unified-trading-pm/plans/archive/2026_05/dex_perp_and_venue_data_expansion_2026_05_12.md Phase 2 + 3
7. market-data-processing-service/tests/unit/test_canonical_writer_ohlcv_1h_policy.py (15 failing tests)
8. unified-trading-pm/plans/active/_agent_pings.md [2026-05-12 BIG FINDING] — MDPS EmissionDecision schema drift

SCOPE (~2 cal AI-days):
A. MDPS 19 test failures (~30-60 min):
   - 15 tests in test_canonical_writer_ohlcv_1h_policy.py: EmissionDecision() missing 2 required args
     (service_emission_state + last_emission_decision_at). Update test instantiations to new signature OR add
     defaults to UTL (prefer fix-the-tests; UTL signature is intentional).
   - 1 test in test_sports_adapters.py: DRAFTKINGS not in expected — sports config change; update expected set.
   - 1 test in test_cli_main.py: ENVIRONMENT=test rejected — likely needs ENVIRONMENT=development.
   - 2 tests in test_check_shard_freshness_granular_rows_only.py: freshness logic drift; investigate + update.
B. Phase 4.FEATURES sweep (~30 min): 6 explicit pipeline_mode= kwargs in features-service calendar batch_handler.py
   + sports batch_handler.py. Mechanical. Updates pipeline_mode_explicit_baseline.yaml from 6→0 → freeze-gate
   item 3 flips to 9/9.
C. dex_perp Phase 2 remainder (~1 cal AI-day): per plan body — remaining adapters after Lighter/Drift/Pacifica/
   Extended-Starknet shipped overnight.
D. EigenLayer Phase 3 (~1 cal AI-day): yield aggregation in features-service per plan body Phase 3.

DONE-DEFINITION:
- MDPS test suite green (was 19 failures, target 0)
- Phase 4.FEATURES baseline yaml 6→0; freeze-gate item 3 flips to 9/9
- dex_perp Phase 2 + 3 work shipped + tests pass

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_10.md (NEW per-slot ping file).
```

---

## Notes for all slots

- **Conditional-push** (mandatory): `git fetch origin` +
  `git rev-list --left-right --count HEAD...origin/live-defi-rollout` BEFORE every push. If incoming touches your files
  → rebase. Don't pipe push through tail (masks non-zero exit).
- **Pre-commit check** (mandatory per CLAUDE.md "Half 1"): `git status` + `git diff --cached --stat` (NO PATH ARGUMENT)
  before every commit. Restore any foreign-staged files.
- **Use `date -u`** for all timestamps (machine clock is IST; UTC is canonical for the workspace).
- **Sub-agent fan-out**: send all Task calls in ONE message. Paste `SUB_AGENT_MANDATORY_RULES.md` at top of every Task
  prompt.
- **CI verification**: pushes to `live-defi-rollout` do NOT trigger remote CI; quality enforced locally. Confirm push
  landed via `git rev-list ... 0 0`.
- **prek auto-restore (foot-gun #4)**: if Edit→commit→push gets reverted by prek patch, `--no-verify` is authorized per
  CLAUDE.md § "Foot-gun #4".
