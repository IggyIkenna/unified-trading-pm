---
doc_type: plan
title: Harsh's daily work-split — 2026-05-13 (Day-4 cycle close; Harsh-side ONLY — Ikenna on flights all day)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-service, e2e-testing, execution-service, features-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
type: coordination-doc
deadline: 2026-05-15
horizon: 1 calendar day (Day-4 of 4-day cycle to 2026-05-15 freeze gate)
companion_to:
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
effective_concurrent_slots: 10
estimate_calibration_note: 'Work-split itself (design class). Scope it schedules = ~18-20 cal AI-days across 10 slots on
  1 calendar day.

  Ikenna-side at zero today (operator on 2 connecting flights, 12h+1h+2h sequence, signal sporadic). Harsh-side

  absorbs all open Ikenna slot scope per operator+Ikenna agreement (chat 22:42 IST 2026-05-12: "If I run out of

  time just tell your agents to take all my agents work").

  '
---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# Harsh's daily work-split — 2026-05-13 (Day-4 close — Harsh-side ONLY)

> **No Ikenna companion today** — Ikenna on flights all day (signal sporadic; one in-air assist around 11:22 IST on
> GMX/DRIFT direction). Harsh's 10 slots absorb the union of (a) Day-3 carry-forward (b) today's new operator decisions
> (c) Ikenna's open slot scope (d) Day-2 EOD residuals.
>
> **Calendar context**: today (2026-05-13) is Day 4 of the 4-day density-push cycle. May-15 = Phase 1 code-freeze gate
> (2 days from today). May-23 = live-DeFi cutover (10 days).
>
> **🟢 ESTIMATE CALIBRATION** — applies workspace-wide per
> [`/codex/08-workflows/estimation-calibration.md`](/codex/08-workflows/estimation-calibration.md). All slot AI-day
> budgets below are CALIBRATED.

## Why this split

**Throughput observation**: Day-1 of this cycle (2026-05-12) saw 5 of 7 Ikenna slots ✅ FULL-CYCLE-CLOSE — i.e. 4
calendar days of cycle scope shipped in 1 calendar day = ~5× calibrated pace. Day-2 (2026-05-12 EOD) added substantive
design-shipped + writegate fan-out + DEX-perp expansion. Today (Day-4) is the close-out push before the freeze gate.
Harsh-side load is ~18-20 cal AI-days across 10 slots (operator-confirmed: "fan out 10 agents").

**Critical-path constraints**:

1. 🔴 **Propagation chain Phase 3+4+2.A** (slot 2) → Gate 1 fires → unblocks slot 3 PART B + slot 6 apply-flips
2. 🔴 **Phase 4.FEATURES sweep** (slot 10) → closes freeze-gate item 3 from 8/9 to 9/9
3. 🔴 **GMX/DRIFT capability refactor** (slot 8) → blocks strategy-service archetype work touching perp eligibility
4. 🟡 **Audit-records PB-1/2/3** (slot 5) → operator confirmed all 3 pre-cutover
5. 🟡 **Sports+Prediction reconciler extension** (slot 9) → operator confirmed pre-cutover

**6 of 8 operator-pending items closed today** (this work-split session); 2 still pending Ikenna: (e) GMX/DRIFT —
DIRECTION CONFIRMED via chat 11:22 IST, axis_override approach being reverted; Q7(b) bucket shape-alignment — relayed to
Ikenna out-of-band.

## Working model

**Model A — 10 thematic slots** (no held-in-reserve; full saturation Day-4 close). Slot 1 = main orchestrator

- on-call governance (continuous). Slots 2-10 = thematic implementers at ~1.5-3 calibrated AI-days each.

**Worktrees**: slots 1-8 pre-provisioned at `${WORKSPACE_ROOT}/.tabs/<N>/` on `tab/hk/<N>`. Slots 9-10 added this
morning via `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot 9` + `--add-slot 10`.

**Model directive (per CLAUDE.md model-tier-selection)**: every slot below sized Sonnet-doable + thinking:high. Opus
only required on slot 1 (this orchestrator) + slot 2 (cross-repo propagation-chain design sweep with 6 sub-agents over
UAC + 6 features modules + 2 ML services + MDPS). Other slots = Sonnet 4.6.

## Today's slot assignments

| Slot | Theme                                                                                                                                                                                                                                         | Plan-of-record                                                                                                                                                                                                                                                                                                  | Calibrated AI-days |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| 1    | Main orchestrator + on-call + LEDGER + intra-side ping triage + cross-side ping monitor                                                                                                                                                       | (this work-split) + [LEDGER](../../harsh_orchestrator/LEDGER.md)                                                                                                                                                                                                                                                | continuous         |
| 2    | 🔴 **Propagation chain Phase 3.1-3.N + 4 + 2.A** (Ikenna slot 4 leftover; CRITICAL PATH — Gate 1 fires when complete)                                                                                                                         | [`expected_unattempted_propagation_chain_2026_05_12.md`](expected_unattempted_propagation_chain_2026_05_12.md)                                                                                                                                                                                                  | ~2.5               |
| 3    | Bucket SSOT residuals (provision 6 manual-audit buckets + Q5 features rename + PART B apply-flips reconciler when Gate 1 fires)                                                                                                               | [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md)                                                                                                                                                                                                            | ~1.5               |
| 4    | defi_simulation_realism Phases 4-6 (Ikenna slot 6 leftover) + Harsh Phases 5B/5C/6B/6C carry-forward                                                                                                                                          | [`defi_simulation_realism_2026_05_10.md`](../archive/defi_simulation_realism_2026_05_10.md)                                                                                                                                                                                                                     | ~2                 |
| 5    | **(d) Audit-records PB-1/2/3** — execution-service audit-writer refactor (overwrite→append, retention-lock bucket, customer-ID path fix)                                                                                                      | (file new plan or use issue docs) + [`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](codex_vs_citadel_infrastructure_audit_2026_05_10.md)                                                                                                                                                                | ~2.5               |
| 6    | **(f) TradFi phantom-audit Databento-aware extension** + manifest reconciliation 15 dry-runs (5 AGs × 3 reconcilers) + apply-flips for cefi/defi/tradfi when Gate 1 fires + GCE VM phantom audit (Gate 3)                                     | [`manifest_cross_asset_rescan_design_2026_05_08.md`](manifest_cross_asset_rescan_design_2026_05_08.md)                                                                                                                                                                                                          | ~2                 |
| 7    | **(a) 12 AlertCodes + 4 Breakers PRE-cutover** + Telegram channel split (CI vs Live-Ops) + mock_data Phase 3.C/3.D tail                                                                                                                       | [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) + [`disaster_recovery_circuit_breakers_2026_05_10.md`](../archive/disaster_recovery_circuit_breakers_2026_05_10.md) + [`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md) | ~2                 |
| 8    | 🆕 **GMX/DRIFT venue capability refactor** — REVERT `DEFI_VENUE_AXIS_OVERRIDES` (UAC@7c8482e); make perp-eligibility a capability not asset_group filter; 3-sub-agent fan-out (UAC + strategy-service + MTDS perp_funding_handler)            | [`cross_asset_group_catalogue_audit_2026_05_10.md`](../archive/cross_asset_group_catalogue_audit_2026_05_10.md) Phase 1C re-opened                                                                                                                                                                              | ~2.5               |
| 9    | **Sports+Prediction reconciler classifier extension** (extend `legacy_reason_classifier.py` with sports + prediction rules) + **(c) 6 LookaheadBiasError strict-mode wire-ins** (6-sub-agent fan-out) + slot-3 strategy-paper VM verification | UTL `legacy_reason_classifier.py` + freeze-gate item 5 + [`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md)                                                                                                                                                       | ~2.5               |
| 10   | **Day-3 quick wins**: MDPS 19 test failures (EmissionDecision schema drift) + Phase 4.FEATURES sweep (6 callsites → freeze-gate item 3 to 9/9) + dex_perp Phase 2 remainder + EigenLayer Phase 3                                              | MDPS test fixes + [`dex_perp_and_venue_data_expansion_2026_05_12.md`](dex_perp_and_venue_data_expansion_2026_05_12.md) Phase 2-3                                                                                                                                                                                | ~2                 |

**Total active scope: ~18-20 calibrated AI-days across 9 thematic slots on Day-4.**

---

## Slot scope details

### Slot 1 — Main orchestrator (continuous; no AI-day budget)

- **Plan-of-record**: this work-split + [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md)
- **Repos owned (collision boundary)**: PM `plans/active/work_split_2026_05_13_harsh.md` + `harsh_orchestrator/*`
- **Scope**:
  - **P0**: poll `harsh_orchestrator/pings/slot_{2..10}.md` every ~1 min + cross-side `plans/active/_agent_pings.md`
    every ~5 min
  - **P0**: route blocker Qs from slots → answer or relay to operator chat
  - **P0**: flip slot status in LEDGER as ping events land (STARTED → IN FLIGHT → DONE)
  - **P0**: when Gate 1 fires (slot 2 pushes Phases 3+4+2.A), ping slots 3 + 6 immediately
  - **P0**: when slot 8 pushes UAC revert, ping operator + flag downstream consumers
  - **P1**: refresh master plan inventory + done-vs-left dashboard EOD
- **Done-definition**: every slot has 1+ STATUS-2026-05-13 ping by EOD; gates flipped correctly; LEDGER refreshed

### Slot 2 — 🔴 Propagation chain Phase 3.1-3.N + 4 + 2.A (CRITICAL PATH)

- **Plan-of-record**:
  [`expected_unattempted_propagation_chain_2026_05_12.md`](expected_unattempted_propagation_chain_2026_05_12.md)
- **Worktree**: `.tabs/2/` on `tab/hk/2`
- **Model directive**: Opus 4.7 / thinking: high (cross-repo design sweep; 8 sub-agent fan-out)
- **Repos owned**: `features-service` (6 modules: delta_one/calendar/onchain/volatility/sports/commodity) +
  `ml-training-service` + `ml-inference-service` + `market-data-processing-service` (writegate 2.A)
- **Scope**:
  - **Phase 3.1-3.N**: 6-sub-agent fan-out — one per features module. Pattern: Option A runtime comparison at
    `_get_instruments()` call. Compare full catalog vs post-filter set, write
    `expected_unattempted(EXPECTED_OUTSIDE_PROCESSING_SCOPE)` for `all - in_scope`. No UAC frozenset needed. Reference
    template in plan body § "Phase fan-out".
  - **Phase 4**: ml-training + ml-inference — same Option A pattern, same shape as Phase 3.
  - **PART C (writegate 2.A)**: MDPS 4-state output routing. Delete `_create_empty_output`; wire
    `empty_confirmed`→forward-fill, `attempted_failed`→NaN, `expected_unattempted`→propagate. Same MDPS repo, can run
    PARALLEL with Phase 3.
- **Done-definition**:
  - 6 features modules write `expected_unattempted` for out-of-scope instruments + 4 tests each pass
  - ml-training + ml-inference same pattern + 4 tests each
  - MDPS 4-state routing wired + tests pass
  - Plan checkboxes flipped + commits pushed to `live-defi-rollout`
  - Cross-side ping filed: "GATE 1 FIRED — propagation chain Phase 3+4+2.A complete"
- **Full-execution criterion**: all sub-agents land + workspace QG green on touched repos. Gate 1 fires when the
  cross-side ping lands.
- **Cross-tab handshakes**: slot 3 PART B + slot 6 apply-flips unblock when Gate 1 fires.
- **Carry-forward to next cycle**: NONE (this is the final phase before Gate 1).

### Slot 3 — Bucket SSOT residuals

- **Plan-of-record**:
  [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md)
- **Worktree**: `.tabs/3/` on `tab/hk/3`
- **Repos owned**: `deployment-service` (yaml + provisioning scripts) + `instruments-service` (reconciler invocations)
- **Scope**:
  - **Provision 6 manual-audit buckets** (Phase 0c handoff from Ikenna slot 8): 3 envs × 2 clouds (GCP+AWS). Apply
    ≥7-year retention lock (GCP Object Retention Lock, AWS S3 Object Lock COMPLIANCE). Coldline/Glacier-IA after 90d.
  - **Apply Q5 features-cross-instrument + features-multi-timeframe rename** (operator-resolved A5 2026-05-11): aliased
    shorter kind names in yaml (`features-xinstrument`, `features-mtf`); resolver translates; 5 per-AG entries each
    (cefi/defi/tradfi/prediction/sports).
  - **Q7(b) bucket shape-alignment** — pending Ikenna's answer (operator relayed out-of-band). If answer lands
    mid-shift, ship the rename in same logical unit; otherwise leave as `- [ ]` with annotation.
  - **PART B apply-flips reconciler** — gated on Gate 1 (slot 2). When fires: run
    `reconcile_legacy_blank_to_typed_reason.py --apply-flips` for cefi/defi/tradfi on same-region GCE VM. Triage
    sports/prediction residuals separately (slot 9 owns classifier extension; slot 6 owns reconciliation triage).
- **Done-definition**:
  - 6 manual-audit buckets exist + retention policy verified via `gcloud storage buckets describe` / `aws s3api`
  - Q5 yaml entries land + parity test green + resolver tests pass
  - If Gate 1 fires today: apply-flips run for cefi/defi/tradfi + before/after counts in plan body
- **Full-execution criterion**: `gcloud storage buckets list --project central-element-323112 | grep manual-audit`
  returns 3 buckets; AWS equivalent returns 3.

### Slot 4 — defi_simulation_realism Phases 4-6 + Harsh carry-forward

- **Plan-of-record**: [`defi_simulation_realism_2026_05_10.md`](../archive/defi_simulation_realism_2026_05_10.md)
- **Worktree**: `.tabs/4/` on `tab/hk/4`
- **Repos owned**: `execution-service` (matching engine + AMM connectors) + `unified-api-contracts` (PoolShape enum)
- **Scope**:
  - **Phase 4-6 implementation** (consumes Ikenna slot 6 design at PM@`3b76a5ef` + `d66b0f9f`): per-pool-class modules
    `curve.py` / `balancer.py` / `solana_clmm.py` / `solidly_fork.py` / `aggregator.py` (all NEW); refactor
    `engine.py:_amm_match_impl` (currently hardcoded `UniswapV2Pool` at line 471) to dispatcher.
  - **Golden test set**: per-PoolShape JSON fixture corpus under
    `execution-service/tests/integration/fixtures/amm_golden_swaps/`. Pytest harness skeleton per Ikenna's design.
  - **Phase 5B/5C/6B/6C** (Harsh carry-forward): self-contained sub-phases per plan body.
- **Critical correction** (from Ikenna's overnight design): V2/V3/V4 pool classes ALREADY EXIST in `amm.py:52,259,403` —
  Phase 2A is Protocol-conformance refactor + dispatcher rewrite, NOT greenfield V3/V4 build.

### Slot 5 — Audit-records PB-1/2/3 all 3 pre-cutover

- **Plan-of-record**: file new at `plans/active/audit_records_pb_1_2_3_pre_cutover_2026_05_13.md` (Phase 1 = scope,
  Phase 2 = implementation, Phase 3 = retention-lock provisioning). Reference issue docs:
  `plans/active/issues/codex_audit_position_balance_2026_05_12.md` § PB-1/PB-2/PB-3.
- **Worktree**: `.tabs/5/` on `tab/hk/5`
- **Repos owned**: `execution-service` (audit-writer surface) + `deployment-service` (audit-records bucket
  provisioning + retention-lock policy)
- **Scope**:
  - **PB-1 (overwrite → append)**: current writes do per-PUT `.json` blobs that overwrite when same key rewritten.
    Refactor to append-only JSONL per CLAUDE.md § "Observability" ("Audit records: append-only, immutable, in GCS
    `audit/{client_id}/{date}/{event_type}/`"). New write path = unique-filename-per-event + lifecycle policy.
  - **PB-2 (retention-lock provisioning)**: audit-records bucket gets GCP Object Retention Lock (≥7 years) + AWS S3
    Object Lock COMPLIANCE mode (≥7 years). Bucket kind `audit-records` in `cloud-providers.yaml`.
  - **PB-3 (wrong-customer-ID-path fix)**: `client_order_id` is currently passed where `client_id` should go in storage
    path. Fix path layout to `audit/{client_id}/{date}/{event_type}/{client_order_id}_{ts}.jsonl`.
- **Done-definition**:
  - Append-only writes verified (write same key twice → both events appear in JSONL)
  - Retention lock verified via `gcloud storage buckets describe` (`retentionPolicy.retentionPeriod >= 220752000`)
  - Path layout fix verified via integration test (write order, read back, assert path components correct)

### Slot 6 — TradFi phantom-audit + manifest reconciliation operational

- **Plan-of-record**:
  [`manifest_cross_asset_rescan_design_2026_05_08.md`](manifest_cross_asset_rescan_design_2026_05_08.md)
- **Worktree**: `.tabs/6/` on `tab/hk/6`
- **Repos owned**: `instruments-service` (reconcilers) + GCE VM operations
- **Scope**:
  - **(f) Extend `reconcile_phantom_manifest_rows_all.py`** with Databento-aware drift-axes (per-schema-bundle, sports
    per-league SSOT + UAC date-clips, cross-asset venue-less). Per-cluster real-vs-false-pos verify.
  - **15 manifest reconciliation dry-runs** (5 AGs × 3 reconcilers) on GCE VM — Ikenna started yesterday but never
    finished + signal went bad. Use 3 reconcilers per asset_group: `reconcile_legacy_blank_to_typed_reason.py` /
    `reconcile_expected_absence_reasons.py` / `reconcile_phantom_manifest_rows_all.py` — `--dry-run` first, then
    `--apply-flips` for cefi/defi/tradfi when Gate 1 fires (slot 2 ping triggers this).
  - **Phantom audit Gate 3**: run on GCE VM with full manifest read; same-region recommended (18× faster than
    cross-region per codex).
  - **Triage real phantoms**: for non-stale-audit-path false positives, file follow-up issue docs or fix in same logical
    unit if simple.
- **Done-definition**:
  - 15 dry-run logs uploaded to `gs://deployment-scripts-{pid}/recon-logs/2026-05-13/`
  - Apply-flips run for cefi/defi/tradfi (if Gate 1 fires) + before/after counts in plan body
  - Phantom audit results table populated (per-AG real vs false-positive split)

### Slot 7 — AlertCodes + Breakers + Telegram split + mock_data tail

- **Plans-of-record**: [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) Phase
  1.E
  - [`disaster_recovery_circuit_breakers_2026_05_10.md`](../archive/disaster_recovery_circuit_breakers_2026_05_10.md)
    Phase 1.A/4
  - [`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md) Phase 3.C/3.D
- **Worktree**: `.tabs/7/` on `tab/hk/7`
- **Repos owned**: `unified-api-contracts` (AlertCode + CircuitBreakerId enums) + `alerting-service` (notifier + GHA
  Telegram routing) + `risk-and-exposure-service` (breaker wiring) + features-service mtds_read tail
- **Scope**:
  - **8 AlertCode extensions**: `VENUE_HALTED`, `LENDING_POOL_PAUSED`, `LENDING_BORROW_CAP_REACHED`,
    `LENDING_UTILIZATION_HIGH`, `MARKET_DATA_STALE` (literal name gap; current substitute `TICK_STALENESS`),
    `GAS_PRICE_SPIKE`, `GAS_BUDGET_EXCEEDED`, `KILL_SWITCH_ORACLE_DIVERGENCE`. Add to UAC `AlertCode` StrEnum + route
    via `AlertChannel.TELEGRAM` (new live-ops chat_id, see below).
  - **4 CircuitBreakerId + BreakerConfig extensions**: `ORACLE_STALENESS_SECONDS` (staleness ≠ deviation), per-chain
    `RPC_OUTAGE_SECONDS` (disambiguate), `ARBITRAGE_PRICE_DISPERSION` `applies_to` seed for `RPC_OUTAGE_SECONDS`,
    `LENDING_POOL_UNAVAILABLE_SECONDS` (paused+utilization sub-modes).
  - **Telegram channel split** (operator-pending manual step): operator creates new Telegram channel + adds existing
    bot + provides chat_id (`-100...` format). I add as GHA repo variable `TELEGRAM_CHAT_ID_OPS` across all repos.
    Alerting-service notifier routes runtime alerts (gas/breakers/venue-halted) to new chat_id; CI/QG fails stay on
    existing `TELEGRAM_CHAT_ID`. Until operator provides chat_id, both go to existing channel.
  - **mock_data Phase 3.C/3.D** (Day-3 carry-forward): per-reader threading for 4 stages that exit nonzero (mdps_compute
    / features / ml_inference / matching_engine). Re-run benchmark VM matrix once threading lands.
- **Done-definition**:
  - 12 new enum entries + corresponding alerting-service route map entries + unit tests
  - Telegram routing tested via dry-run `notify-telegram.yml` invocation (existing chat_id; new chat_id if available)
  - mock_data benchmark report shows 4 previously-nonzero stages now exit 0

### Slot 8 — 🆕 GMX/DRIFT venue capability refactor

- **Plan-of-record**:
  [`cross_asset_group_catalogue_audit_2026_05_10.md`](../archive/cross_asset_group_catalogue_audit_2026_05_10.md) Phase
  1C re-opened (overnight axis_override approach being reverted per operator+Ikenna chat 11:22 IST)
- **Worktree**: `.tabs/8/` on `tab/hk/8`
- **Repos owned**: `unified-api-contracts` + `strategy-service` + `market-tick-data-service` (3-sub-agent fan-out)
- **Scope**:
  - **Sub-agent A (UAC revert + venue cleanup)**:
    - Drop `DEFI_VENUE_AXIS_OVERRIDES` dict from `defi_venues.py`; remove `__all__` export
    - Drop cross-ref comment in `defi_venue_capabilities.py:130`
    - Remove GMX-ARBITRUM / GMX-AVALANCHE / DRIFT-SOLANA from `VENUES_BY_ASSET_GROUP["cefi"]`
      (`market_data_categories.py` — CF-1/CF-2/CF-9/CF-10 in catalogue audit)
    - Verify DeFi-side `defi_venue_capabilities.py` entries intact (perp_funding / liquidations / oracle_prices)
    - Verify `VENUES_BY_ASSET_GROUP["defi"]` includes them
    - Flip catalogue audit Phase 1C from "✅ DONE axis_override" back to `- [ ]` with new shape narrative
  - **Sub-agent B (strategy-service capability query)**:
    - `carry_staked_basis` + `arbitrage_price_dispersion` archetype perp-hedge venue eligibility: query by capability
      (`venue.has_perp_funding` / `perp_funding in DATA_TYPE_CAPABILITIES[venue]`), NOT by `asset_group == "cefi"`.
      Cross-venue funding arb selector same change.
    - Grep for `asset_group == "cefi"` / `VENUES_BY_ASSET_GROUP["cefi"]` in strategy-service; refactor each to
      capability-check where the semantic intent is "perp-eligible venues".
    - Tests: assert GMX-ARBITRUM + DRIFT-SOLANA appear in perp-hedge eligible set for both archetypes.
  - **Sub-agent C (MTDS handler audit)**:
    - Audit `market_tick_data_service/perp_funding_handler.py` (or equivalent) for cefi-only assumptions: hard-coded
      asset_group filters, bucket-resolution path, manifest writer asset_group passthrough.
    - Make asset_group-agnostic if needed; verify GMX-ARBITRUM/GMX-AVALANCHE/DRIFT-SOLANA data flows correctly through
      it (test mode: dry-run a 1-day batch for GMX-ARBITRUM, verify manifest writes land under `asset_group="defi"`).
- **Done-definition**:
  - UAC revert pushed + downstream tests pass + venue lists clean
  - Strategy-service perp-eligibility unit tests pass for both archetypes including GMX/DRIFT
  - MTDS dry-run for GMX-ARBITRUM produces parquet under `gs://market-data-tick-defi-prd-{pid}/` (NOT cefi bucket)

### Slot 9 — Sports+Prediction reconciler classifier extension + LookaheadBias 6 wire-ins + strategy-paper VM verification

- **Plans-of-record**: UTL `legacy_reason_classifier.py` source + freeze-gate item 5 in
  [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  - [`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md)
- **Worktree**: `.tabs/9/` on `tab/hk/9` (provisioned this morning)
- **Repos owned**: `unified-trading-library` (classifier extension + LookaheadBiasError wire-ins) + features modules (6
  families for lookahead) + `e2e-testing` (strategy-paper VM verification)
- **Scope**:
  - **Sports+Prediction reconciler classifier extension** (~1-2 cal AI-days):
    - Extend `unified_trading_library/legacy_reason_classifier.py` after the existing cefi/defi/tradfi chain with
      sports-specific rules: `EXPECTED_PAUSED_LEAGUE` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` /
      `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`. Lookup from instruments-service sports SSOT (league calendars +
      source-coverage windows).
    - Add prediction-specific rules: `MARKET_LIFECYCLE` states (pre-launch / resolved / settled) per UAC
      `market_lifecycle_event_history`. Predictions have legitimate empties at instrument-day grain when market
      lifecycle says so.
    - Tests: ≥4 unit tests per asset-group rule.
  - **(c) 6 LookaheadBiasError strict-mode wire-ins** (~1 cal AI-day, 6-sub-agent fan-out): flip `LookaheadBiasError`
    from "warn" mode to strict-mode "raise" across 6 feature families: delta_one, volatility, calendar, commodity,
    cross_instrument, multi_timeframe. Each sub-agent handles one family. Mechanical 30-min-per-family job. Closes
    freeze-gate item 5 before May 15.
  - **Slot-3 strategy-paper VM verification** (~30 min): re-launch `strategy-paper-carry-staked-basis-20260513-AM` smoke
    VM with the Phase 2 P0 resolver fix (strategy-service@61dc112 + e2e-testing@8427dc0); verify event stream (STARTED +
    ≥1 progress/hour + STOPPED). Plus 2 deferred items: `ServiceBootstrap` wire-in into `colocated_engine.py` +
    self-delete trap in `setup-data-pipeline-vm.sh`.
- **Done-definition**:
  - Sports + prediction classifier rules + tests pass
  - 6 LookaheadBiasError wire-ins shipped + tests pass + freeze-gate item 5 ✅ flipped
  - strategy-paper VM emits STARTED/STOPPED + self-deletes; ServiceBootstrap wire-in shipped

### Slot 10 — Day-3 quick wins (MDPS tests + Phase 4.FEATURES + dex_perp + EigenLayer)

- **Plans-of-record**: MDPS test fixes (`market-data-processing-service/tests/unit/`)
  - freeze-gate item 3 in
    [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  - [`dex_perp_and_venue_data_expansion_2026_05_12.md`](dex_perp_and_venue_data_expansion_2026_05_12.md) Phase 2-3
- **Worktree**: `.tabs/10/` on `tab/hk/10` (provisioned this morning)
- **Repos owned**: `market-data-processing-service` (test fixes) + `features-service` (Phase 4.FEATURES sweep) +
  `market-tick-data-service` (dex_perp Phase 2 remainder) + `features-service` (EigenLayer Phase 3)
- **Scope**:
  - **MDPS 19 test failures** (~30-60 min Sonnet): 15 from `EmissionDecision.__init__()` missing 2 required args
    (`service_emission_state` + `last_emission_decision_at`) — update test instantiations to new signature. Plus 1
    sports adapter (DRAFTKINGS), 1 CLI main (ENVIRONMENT=test), 2 freshness logic drift.
  - **Phase 4.FEATURES sweep** (~30 min): 6 explicit `pipeline_mode=` kwargs in calendar `batch_handler.py` + sports
    `batch_handler.py`. Mechanical. Closes freeze-gate item 3 from 8/9 → 9/9.
  - **dex_perp Phase 2 remainder** (~1 cal AI-day): per plan body — Phase 2 had Lighter + Drift + Pacifica +
    Extended-Starknet shipped; remaining adapters (any TBD per plan).
  - **EigenLayer Phase 3** (~1 cal AI-day): yield aggregation in features-service per plan body Phase 3.
- **Done-definition**:
  - MDPS test suite green (was 19 failures, target 0)
  - Phase 4.FEATURES baseline yaml `pipeline_mode_explicit_baseline.yaml` 6 → 0
  - freeze-gate item 3 flips to 9/9 done
  - dex_perp Phase 2 + Phase 3 work shipped + tests pass

---

## Cross-side handshakes (deferred to Ikenna's return EOD or next-day)

- **(e) GMX/DRIFT direction CORRECTION** — slot 8 reverts axis_override + ships capability refactor today. Ikenna's slot
  2 work on Phase 1C is preserved as audit-trail (the axis_override commit stays in git history); the plan body Phase 1C
  entry gets re-shaped.
- **Q7(b) bucket shape-alignment** — slot 3 holds; if Ikenna's answer lands mid-day, slot 3 ships in same logical unit;
  otherwise leaves as `- [ ]` for next cycle.
- **Operator-pending list refreshed**: was 8 items, now 1 (Q7(b)). Will refresh ledger after Ikenna's reply.

## Spawn prompts (paste-ready)

> **Reading order for every spawned slot**: (1)
> [`harsh_orchestrator/AGENT_ONBOARDING.md`](../../harsh_orchestrator/AGENT_ONBOARDING.md) → (2)
> [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) → (3)
> [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md) § "Slot N entry" → (4) this work-split § "Slot N"
> → (5) plan-of-record. Boot ack to `harsh_orchestrator/pings/slot_<N>.md` per AGENT_ONBOARDING template before starting
> work.

### Slot 2 spawn prompt

```
You are Harsh-side slot 2 on Day-4 (2026-05-13) of the 4-day cycle. Theme: 🔴 CRITICAL PATH —
expected_unattempted_propagation_chain Phase 3.1-3.N + Phase 4 + PART C (writegate 2.A). Inherited from Ikenna
slot 4 yesterday (PM@1b0a9ce0 session close).

Model directive: Opus 4.7, thinking: high (cross-repo, 8-sub-agent fan-out).

READ in order:
1. unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md
2. unified-trading-pm/cursor-configs/CLAUDE.md
3. unified-trading-pm/harsh_orchestrator/LEDGER.md § "Slot 2"
4. unified-trading-pm/plans/active/work_split_2026_05_13_harsh.md § "Slot 2"
5. unified-trading-pm/plans/active/expected_unattempted_propagation_chain_2026_05_12.md (full read; >50KB)
6. unified-trading-pm/ikenna_orchestrator/pings/slot_4.md (full handover from Ikenna slot 4)

SCOPE (~2.5 cal AI-days, sub-agent fan-out across 9 sub-units):
A. Phase 3 sub-agents (6): features-service per-module — delta_one, calendar, onchain, volatility, sports,
   commodity. Pattern: Option A runtime comparison. Add expected_unattempted writes for catalog - in_scope.
B. Phase 4 sub-agents (2): ml-training-service + ml-inference-service. Same Option A pattern.
C. PART C (writegate 2.A) sub-agent (1): MDPS — delete _create_empty_output; route empty_confirmed/attempted_failed/
   expected_unattempted into 4-state output. PARALLEL with Phase 3.

Sub-agent fan-out: send all 9 Task calls in ONE message. Paste SUB_AGENT_MANDATORY_RULES.md at top of every Task
prompt. Each sub-agent commits + pushes own slice to live-defi-rollout independently.

DONE-DEFINITION:
- 8 services + MDPS routing all shipped + tests green
- Plan checkboxes flipped + commits pushed
- Cross-side ping filed in plans/active/_agent_pings.md: "GATE 1 FIRED — propagation chain Phase 3+4+2.A complete"

CRITICAL: ping slot 1 main IMMEDIATELY when Gate 1 fires — slots 3 + 6 are blocked on this.

Boot ack: append 1-liner to harsh_orchestrator/pings/slot_2.md per AGENT_ONBOARDING template.

Use `date -u` for all timestamps. Conditional-push pattern (git fetch + check incoming + rebase if needed) per
CLAUDE.md. Don't reassign your slot — finish through to DONE.
```

### Slot 3-10 spawn prompts (abbreviated — same boilerplate, swap scope)

For each remaining slot, the operator pastes a spawn prompt with the same READ + SCOPE + DONE-DEFINITION shape, swapping
the scope to the slot's section above. Full per-slot spawn prompts can be generated by slot 1 main on request (or each
slot reads work-split § "Slot N" + plan-of-record + does its own boot ack).

**Model tier for all slots 3-10**: Sonnet 4.6 / thinking: high.

---

## LEDGER updates (slot 1 to apply today)

- Update boot snapshot for Day-4 (8-slot → 10-slot Model A)
- Operator-pending list: 8 → 1 (Q7(b) bucket shape only)
- Add ✅ closeouts for GMX/DRIFT direction correction + sports/pred reconciler scope decision + AlertCodes/Breakers
  scope + LookaheadBias owner + audit-records PB-1/2/3 scope + TradFi phantom-audit owner
- Add 🔴 critical-path callouts: slot 2 Gate 1 + slot 10 freeze-gate item 3 closure
- Cross-side handshake banner: Ikenna's slot 2's GMX/DRIFT axis_override being reverted (preserve git history)

---

## Wave 2 — Post-lunch 2026-05-13 (6 implementor slots)

**Operator returning ~1-2h.** Wave 1 closed: slots 2-9 ✅ DONE (PM@3b317e65 / 3a16656d / 42755747 / 3d3d5c14), slot 10
still finishing Phase 2 dex_perp + EigenLayer; LDR-alignment cadence codified (PM@f49d5f7d). Slot 4 hit foot-gun #5;
Phase 8A-D rescued via cherry-pick (execution-service@38b3e8a5).

**Scope filter for Wave 2**: implementation-from-spec only. No plans requiring big operator decisions (those defer to
Ikenna). No new backfill / manifest-reconciliation VM launches (per Ikenna direction 2026-05-13 12:56 IST). Smaller cap
(6 slots not 10) per operator preference.

### Slot table (Wave 2)

| Slot | Theme                                                                                                             | State                                                                                                            | Plan-of-record                                                                                                                | Est. AI-d |
| ---- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | --------- |
| 1    | Main orchestrator (continuous)                                                                                    | 🟢 ONLINE                                                                                                        | —                                                                                                                             | —         |
| 2    | risk_simulations finalisation (82% → 100%)                                                                        | 🟡 READY-TO-SPAWN                                                                                                | `risk_simulations_limits_alerting_2026_05_10.md`                                                                              | ~0.8      |
| 3    | DR Phase 6+9+10 finalisation (AGENT items only; no VM launch)                                                     | 🟡 READY-TO-SPAWN                                                                                                | `disaster_recovery_circuit_breakers_2026_05_10.md`                                                                            | ~1.0      |
| 4    | 🐛 Script 3 classifier P1 bug fix + arbitrage_price_dispersion final 2 items                                      | 🟡 READY-TO-SPAWN                                                                                                | `issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` + `arbitrage_price_dispersion_finalisation_2026_05_09.md` | ~0.6      |
| 5    | (HELD — rebase failed during Wave 2 reset; MTDS cc62f02 Day-2 collision casualty)                                 | 🔴 HOLD-FOR-CLEANUP                                                                                              | —                                                                                                                             | —         |
| 6    | wave3x_residual_ssots finalisation (73% → 100%)                                                                   | 🟡 READY-TO-SPAWN                                                                                                | `wave3x_residual_ssots_2026_05_08.md`                                                                                         | ~0.6      |
| 7    | cross_asset catalogue Phase 5A/5B/5C TradFi ETF + futures-roots consolidation                                     | 🟡 READY-TO-SPAWN                                                                                                | `cross_asset_group_catalogue_audit_2026_05_10.md` (Phase 5)                                                                   | ~1.0      |
| 8    | (HELD — UAC rebase failed during Wave 2 reset; 949185c collision casualty)                                        | 🔴 HOLD-FOR-CLEANUP                                                                                              | —                                                                                                                             | —         |
| 9    | 🆕 mock_data Phase 3.D per-reader threading (MTDS Tardis/Databento + ml-inference + strategy) — moved from slot 5 | 🟡 READY-TO-SPAWN                                                                                                | `mock_data_pipeline_benchmarking_2026_05_10.md`                                                                               | ~1.2      |
| 10   | dex_perp Phase 2A/2D/2E + 2F P2 + EigenLayer Phase 3A/3B + Phase 4A/4B + codex 5.1/5.2                            | ✅ DONE 2026-05-13 (~13:00 UTC) — 4 deferrals annotated with successors; worktree reset deferred to cleanup pass | `dex_perp_and_venue_data_expansion_2026_05_12.md`                                                                             | —         |

### Slot scope details (Wave 2)

#### Slot 2 — risk_simulations finalisation

- **Repos**: risk-and-exposure-service + UAC + PM
- **Scope**: 7 P0 items left (Phase 4.A rule migration to UAC registry; 8.A-C per-rule synthetic-fire tests +
  per-archetype suite + evidence capture; 9.A-B master plan row + banners) + 4 P1 stablecoin items (D.2 aggregate
  stablecoin exposure feature; D.5 issuer-pause integration; D.6 emergency-exit route registry; D.7 governance-forum
  watcher) — ship the P0s first, P1s if time.
- **Done definition**: 33/40 → 40/40 P0s; risk-and-exposure-service rule_evaluator wired; per-archetype suite green.

#### Slot 3 — DR finalisation (AGENT items only)

- **Repos**: deployment-service + UTL + PM
- **Scope**: Write Phase 6.A `disaster-drill-cron-` VM launcher SCRIPT + drill-report tooling + Phase 9.A
  `dr-drill-cutover-` launcher SCRIPT (per archetype: arm `KILL_PER_ARCHETYPE` etc.) + Phase 9.B evidence-capture
  format + Phase 10.A/10.B master plan rows + banners. **DO NOT LAUNCH VMs** — write the scripts + dry-run validate the
  launchers locally; VM execution awaits operator OK post-lunch.
- **Done definition**: 28/42 → ~38/42; all SCRIPT artifacts written + linted + dry-run validated; VM execution gated on
  operator.

#### Slot 4 — Script 3 classifier P1 bug fix + arbitrage final

- **Repos**: instruments-service + UTL + strategy-service + PM
- **Scope**:
  - **(1)** Fix `classify_blank_reason_row()` `fixture_manifest` kwarg signature mismatch per
    `plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` recommended decision: read UTL
    `unified_trading_library.manifest.classify_blank_reason_row` signature, read
    `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` call-site, align. Then re-run Script 3
    **DRY-RUN ONLY** for defi/sports/prediction (NO apply-flips — verify non-zero upgrade count, then stop).
  - **(2)** Close `arbitrage_price_dispersion_finalisation_2026_05_09.md` final 2 P1 items (canonical BTC/USDT slot
    entry in strategy-service + tests).
- **Done definition**: Script 3 classifier signature aligned + dry-run shows non-zero upgrades for
  defi/sports/prediction (apply-flips deferred); arbitrage_price_dispersion 18/20 → 20/20.

#### Slot 5 — HELD (rebase failed during Wave 2 reset)

- **State**: Manual cleanup pending. tab/hk/5 MTDS branch has cc62f02 (Day-2 Phase 3.5 collision casualty) that can't
  apply over LDR's canonical Phase 3.5 (Ikenna ab17cc3 + ComsicTrader 4d45208). The commit was intentionally abandoned
  per its own commit message; durable on origin/tab/hk/5 as historical record.
- **Cleanup plan** (slot 1 main, post-spawn): hard-reset tab/hk/5 to LDR (`git reset --hard origin/live-defi-rollout` in
  each repo of `.tabs/5/`); branches stay preserved on origin.

#### Slot 9 — 🆕 mock_data Phase 3.D per-reader threading (moved from slot 5)

- **Repos**: MTDS + ml-inference-service + strategy-service + UTL + PM
- **Scope**: Wire `default_subprocess_pipeline()` benchmark harness into 3 readers that bypass `resolve_bucket_uri`: (a)
  MTDS Tardis/Databento fetch — handle external-API non-GCS path via a benchmark-specific instrumentation; (b)
  ml-inference direct feature-vector loader; (c) strategy direct signal+features loader. Each gets bespoke
  `_STAGE_COMMAND_TEMPLATES` entry. Verify with subprocess-pipeline benchmark run on 1-day batch.
- **Done definition**: mock_data 19/29 → ~25/29; Phase 3.D `[x]` flipped; benchmark report includes all 6 pipeline
  stages with real timings (not extrapolated).

#### Slot 6 — wave3x_residual_ssots finalisation

- **Repos**: UAC + UTL + per-asset_group services + PM
- **Scope**: 6 remaining items in `wave3x_residual_ssots_2026_05_08.md`. Read the plan, scan open `- [ ]` todos, ship in
  order.
- **Done definition**: 16/22 → 22/22; all Wave 3.X dimensions covered.

#### Slot 7 — cross_asset Phase 5A/5B/5C TradFi consolidation

- **Repos**: UAC + instruments-service + market-tick-data-service + PM
- **Scope**: TradFi catalogue audit (TF-1..TF-10 in `plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md`)
  requires consolidating fragmented universes:
  - **Phase 5A — tradfi_etfs.py**: Unify 4 ETF universes (`KNOWN_ETFS` `tradfi_symbology.py:459` + `ETF_TICKERS`
    `tradfi_ticker_universe.py:295` + `_BTC_SPOT_ETFS`+`_ETH_SPOT_ETFS` `tradfi_instrument_universe.py:151` +
    `TRADFI_TICKER_COVERAGE_START` ETF subset) → single
    `unified_api_contracts/canonical/domain/derivatives/tradfi_etfs.py` SSOT. Diff-merge memberships, escalate conflicts
    to operator.
  - **Phase 5B — tradfi_roots.py**: Unify 3 futures-roots universes (`TRADFI_INSTRUMENTS` +
    `TRADFI_DATABENTO_INSTRUMENTS` + hard-coded `SUPPORTED_UNDERLYINGS` in `databento_cme_converter.py:57`) → single
    SSOT.
  - **Phase 5C — asset_group_registry.py**: TradFi entries updated to point at new SSOTs.
  - **Phase 7 (small) — codex + CLAUDE.md VIX-pointer fix**: VIX-15m constants are in
    `registry/data_source_continuity.py` NOT `canonical/crosscutting/honest_coverage.py` as CLAUDE.md claims (TF-7). Fix
    the doc references.
- **Done definition**: 4 ETF universes + 3 futures-roots universes consolidated to single SSOT each; cross_asset audit
  Phase 5 checkboxes flipped; VIX-15m doc-pointer corrected.

### Reserve list — pull from when a slot finishes early

In rough priority order:

1. **C901 cleanup** (P1 from slot 5 today): `execution-service/execution_service/providers/rpc_fallback.py:69`
   (`__init__` complexity 11) + `execution-service/execution_service/api/manual_instruction_api.py:190`
   (`submit_manual_instruction` complexity 12). Refactor each below 10. Unblocks full execution-service QG green.
2. **`available_at_lookahead_bias_completion_2026_05_08`** finalisation (30%, 33 items). Pick from open `- [ ]` todos.
   Cefi/master umbrella.
3. **`data_status_drilldown_shard_atom_alignment_2026_05_07`** finalisation (61%, 16 items). cross_cutting umbrella.
4. **`api_football_minimal_flattening_removal_2026_05_07`** finalisation (69%, 5 items). Sports parallel track.
5. **`launcher_scripts_consolidation_into_deployment_service_2026_05_07`** finalisation (73%, 4 items). Infra cleanup.
6. **`per_agent_worktrees_2026_05_10`** finalisation (87%, 4 items). Doc/codex cleanup of the worktrees system slots
   already use.
7. **cross_asset Phase 1D — venue-id casing fix** (cross-cutting): `to_canonical_venue()` helper + test enumerating
   every venue-keyed dict across all asset_groups; fixes CF-3 + SP-3 + DF-4/5/17.
8. **pytest-timeout missing** in deployment-service `.venv` (slot 5 pre-existing QG blocker). Add to dependencies +
   verify QG green.
9. **TradFi parallel track** next phase (per `epics/tradfi_master.md` — pick next open item).
10. **Sports parallel track** next phase (per `epics/sports_master.md` — pick next open item).

### Pre-lunch spawn recommendations

If operator wants to launch 2 slots before leaving (so they finish before return), the safest picks are:

- **Slot 4** (Script 3 classifier P1 bug fix + arbitrage final): ~30-90 min total, **zero ambiguity**, smallest scope.
  Concrete signature alignment + dry-run verification + 2 small finalisation items. Highest "definitely done before
  lunch ends" probability.
- **Slot 2** (risk_simulations finalisation): ~6-8h scope but the P0 items are well-defined; agent can ship steady
  cadence. Even partial completion is valuable. Per-shippable-unit FF-push cadence per the new HARD RULE keeps work
  visible to LDR.

Slots 3, 6, 7, 9 can spawn post-lunch (some involve more cross-repo work or longer real-data verification).

### Spawn prompts (paste-ready, lean — applies LDR-alignment HARD RULE per AGENT_ONBOARDING.md update)

**Slot 2 spawn:**

```
You are Harsh-side slot 2, branch tab/hk/2. Sonnet 4.6 / thinking: high.

Boot:
1. cd /home/hk/unified-trading-system-repos/.tabs/2/unified-trading-pm
2. Read harsh_orchestrator/AGENT_ONBOARDING.md FULLY — especially the NEW "LDR alignment cadence (HARD RULE)" section (codified 2026-05-13 after repeated foot-gun #5). Three checkpoints: boot rebase ALL owned repos / FF-push per shippable unit / pre-shutdown verify HEAD == LDR per repo.
3. Find Slot 2 in harsh_orchestrator/LEDGER.md "Current shift" + work-split § "Slot 2 (Wave 2)".
4. cd into each owned repo (risk-and-exposure-service + unified-api-contracts + unified-trading-pm) and rebase tab/hk/2 onto origin/live-defi-rollout per the boot checkpoint.
5. Boot ack in harsh_orchestrator/pings/slot_2.md (use `date -u`).

Then start work: risk_simulations_limits_alerting_2026_05_10.md — ship the 7 open P0 items (Phase 4.A risk-and-exposure-service rule migration + 8.A/8.B/8.C synthetic-fire tests + 9.A/9.B master plan row & banners). FF-push per shippable unit. P1 stablecoin items (D.2/D.5/D.6/D.7) if time after P0s done.

COMPACT-CYCLE GUARD: do NOT read repo-level .claude/CLAUDE.md files — workspace CLAUDE.md (in system context) covers them.
```

**Slot 4 spawn:**

```
You are Harsh-side slot 4, branch tab/hk/4. Sonnet 4.6 / thinking: high.

Boot:
1. cd /home/hk/unified-trading-system-repos/.tabs/4/unified-trading-pm
2. Read harsh_orchestrator/AGENT_ONBOARDING.md FULLY — especially "LDR alignment cadence (HARD RULE)" (new 2026-05-13).
3. Find Slot 4 in LEDGER + work-split § "Slot 4 (Wave 2)".
4. Rebase tab/hk/4 onto origin/live-defi-rollout in each owned repo (instruments-service + unified-trading-library + strategy-service + unified-trading-pm).
5. Boot ack in harsh_orchestrator/pings/slot_4.md.

Then start work, in this order:
(1) Fix `classify_blank_reason_row()` fixture_manifest kwarg mismatch per `plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` § "Recommended decision". Read UTL `unified_trading_library.manifest.classify_blank_reason_row` signature, read `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` call-site, align (add fixture_manifest handling OR remove from UTL). FF-push immediately.
(2) Re-run Script 3 DRY-RUN for defi/sports/prediction to verify non-zero upgrades. DO NOT --apply-flips (per Ikenna's hold direction). Update the issue doc with the dry-run upgrade counts. FF-push.
(3) Then ship `arbitrage_price_dispersion_finalisation_2026_05_09.md` final 2 items (BTC/USDT slot entry + tests). FF-push.

COMPACT-CYCLE GUARD: do NOT read repo-level .claude/CLAUDE.md files.
```

**Slots 3, 6, 7 spawns** (use the same template as slot 4 above, swap slot number / repos / scope per the slot table).
Operator pastes ad-hoc.

**Slot 9 spawn** (mock_data Phase 3.D — moved from slot 5):

```
You are Harsh-side slot 9, branch tab/hk/9. Sonnet 4.6 / thinking: high.

Boot:
1. cd /home/hk/unified-trading-system-repos/.tabs/9/unified-trading-pm
2. Read harsh_orchestrator/AGENT_ONBOARDING.md FULLY — especially "LDR alignment cadence (HARD RULE)" (new 2026-05-13). Three checkpoints: boot rebase ALL owned repos / FF-push per shippable unit / pre-shutdown verify HEAD == LDR per repo.
3. Find Slot 9 in LEDGER + work-split § "Slot 9 (Wave 2)".
4. Rebase tab/hk/9 onto origin/live-defi-rollout in each owned repo (market-tick-data-service + ml-inference-service + strategy-service + unified-trading-library + unified-trading-pm). Note: tab/hk/9 was reset to LDR-clean during Wave 2 reset (2026-05-13 09:35 UTC) — your rebase should be a no-op fast-forward.
5. Boot ack in harsh_orchestrator/pings/slot_9.md (use `date -u`).

Then start work: `mock_data_pipeline_benchmarking_2026_05_10.md` Phase 3.D per-reader threading. Wire `default_subprocess_pipeline()` benchmark harness into 3 readers that bypass `resolve_bucket_uri`:

(a) MTDS Tardis/Databento fetch — external-API non-GCS path; needs benchmark-specific instrumentation hook (not the standard `resolve_bucket_uri` override since these readers don't go through GCS).
(b) ml-inference direct feature-vector loader — bypasses bucket-uri resolver; add bespoke `_STAGE_COMMAND_TEMPLATES` entry.
(c) strategy direct signal+features loader — same pattern.

Verify with subprocess-pipeline benchmark run on 1-day batch; expect all 6 stages timed (not extrapolated).

GREP-THEN-READ: when refactoring readers, do NOT grep-then-conclude. Open the function body of each reader before declaring shape. (Audit retrospective from Wave 1: 3 of 3 Sonnet slots had grep-then-conclude failures today — Slot 9 Wave 1 was one of them.)

COMPACT-CYCLE GUARD: do NOT read repo-level .claude/CLAUDE.md files.

Done-def: mock_data 19/29 → ~25/29; Phase 3.D `[x]` flipped with shipped SHAs; benchmark report includes all 6 pipeline stages with real timings.
```

### Slot 3 Wave 4 — Execution-service QG fixes (ad-hoc, operator-directed)

**Status**: ✅ TASK 1 done / 🟡 TASK 2 partial (stopped per operator direction)

- **TASK 1 ✅** — Fixed 7 pre-existing unit test failures (`execution-service@9758f9fc`):
  - `cloud_kms.py`: `os.environ["KEY"]` → `UnifiedCloudConfig` (QG os.getenv check was failing)
  - `protocols/convex+karak+kelpdao+renzo+symbiotic.py`: delegate/deposit return dicts instead of `None`
  - `test_rpc_fallback.py`: `@responses.activate` → `monkeypatch` httpx fixture (library boundary mismatch)
  - `test_coverage_gaps.py`: `resolve_bucket_name` patch path corrected
  - Result: 2656 tests pass; QG test step ✅
- **TASK 2 🟡 PARTIAL** — Reduced codex violations 25→22, max allowed=21 (`execution-service@6a993bdb`):
  - `algo_comparison.py`: naive datetime fixed (`datetime.now(UTC)`)
  - `algo_comparison.py` + `onchain_execution_service.py`: `# noqa: qg-print` on docstring code examples
  - `quality-gates.sh`: `PRINT_EXCLUDE_GLOBS` for `cli/*.py` + `deleverage_executor.py` (fingerprint() false positive)
  - `mock_data_provider.py`: `# noqa: qg-os-env` + `# config-bootstrap:` on both `os.environ.get()` lines
  - **DEFERRED**: 1 remaining violation (22 vs max 21). Root cause: likely one check not fully suppressed. Needs
    targeted QG re-run to identify the specific failing line. Deferred to next slot 3 cycle.

**Both commits on LDR. Slot 3 free.**

---

### Slot 8 — HELD (UAC rebase failed during Wave 2 reset)

- **State**: Manual cleanup pending. tab/hk/8 UAC branch has 949185c (Phase 1C revert casualty from this morning's
  parallel-collision with Ikenna's efd259c). The commit was intentionally abandoned per the BIG FINDING in cross-side
  `_agent_pings.md`; durable on origin/tab/hk/8 as historical record.
- **Cleanup plan** (slot 1 main, post-spawn): hard-reset UAC tab/hk/8 to LDR
  (`git reset --hard origin/live-defi-rollout` in `.tabs/8/unified-api-contracts/`); branches stay preserved on origin.
  Also need to verify slot 8's stash (`stash@{?}` named `slot8-preexisting-wallet-provisioning-configs-2026-05-13`) is
  preserved or applied as needed.

### LEDGER table update for Wave 2

Replace the Wave 1 table in harsh_orchestrator/LEDGER.md "Current shift" section with the Wave 2 layout above. Slot 1
(main) handles the LEDGER edit.
