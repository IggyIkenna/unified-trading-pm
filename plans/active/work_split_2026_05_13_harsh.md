---
title: Harsh's daily work-split — 2026-05-13 (Day-4 cycle close; Harsh-side ONLY — Ikenna on flights all day)
type: coordination-doc
status: active
created: 2026-05-13
deadline: 2026-05-15
horizon: 1 calendar day (Day-4 of 4-day cycle to 2026-05-15 freeze gate)
companion_to: null
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
effective_concurrent_slots: 10
estimate_calibration_note: |
  Work-split itself (design class). Scope it schedules = ~18-20 cal AI-days across 10 slots on 1 calendar day.
  Ikenna-side at zero today (operator on 2 connecting flights, 12h+1h+2h sequence, signal sporadic). Harsh-side
  absorbs all open Ikenna slot scope per operator+Ikenna agreement (chat 22:42 IST 2026-05-12: "If I run out of
  time just tell your agents to take all my agents work").
---

# Harsh's daily work-split — 2026-05-13 (Day-4 close — Harsh-side ONLY)

> **No Ikenna companion today** — Ikenna on flights all day (signal sporadic; one in-air assist around 11:22 IST
> on GMX/DRIFT direction). Harsh's 10 slots absorb the union of (a) Day-3 carry-forward (b) today's new operator
> decisions (c) Ikenna's open slot scope (d) Day-2 EOD residuals.
>
> **Calendar context**: today (2026-05-13) is Day 4 of the 4-day density-push cycle. May-15 = Phase 1 code-freeze
> gate (2 days from today). May-23 = live-DeFi cutover (10 days).
>
> **🟢 ESTIMATE CALIBRATION** — applies workspace-wide per
> [`codex/08-workflows/estimation-calibration.md`](../../codex/08-workflows/estimation-calibration.md). All slot
> AI-day budgets below are CALIBRATED.

## Why this split

**Throughput observation**: Day-1 of this cycle (2026-05-12) saw 5 of 7 Ikenna slots ✅ FULL-CYCLE-CLOSE — i.e. 4
calendar days of cycle scope shipped in 1 calendar day = ~5× calibrated pace. Day-2 (2026-05-12 EOD) added
substantive design-shipped + writegate fan-out + DEX-perp expansion. Today (Day-4) is the close-out push before
the freeze gate. Harsh-side load is ~18-20 cal AI-days across 10 slots (operator-confirmed: "fan out 10 agents").

**Critical-path constraints**:
1. 🔴 **Propagation chain Phase 3+4+2.A** (slot 2) → Gate 1 fires → unblocks slot 3 PART B + slot 6 apply-flips
2. 🔴 **Phase 4.FEATURES sweep** (slot 10) → closes freeze-gate item 3 from 8/9 to 9/9
3. 🔴 **GMX/DRIFT capability refactor** (slot 8) → blocks strategy-service archetype work touching perp eligibility
4. 🟡 **Audit-records PB-1/2/3** (slot 5) → operator confirmed all 3 pre-cutover
5. 🟡 **Sports+Prediction reconciler extension** (slot 9) → operator confirmed pre-cutover

**6 of 8 operator-pending items closed today** (this work-split session); 2 still pending Ikenna:
(e) GMX/DRIFT — DIRECTION CONFIRMED via chat 11:22 IST, axis_override approach being reverted; Q7(b) bucket
shape-alignment — relayed to Ikenna out-of-band.

## Working model

**Model A — 10 thematic slots** (no held-in-reserve; full saturation Day-4 close). Slot 1 = main orchestrator
+ on-call governance (continuous). Slots 2-10 = thematic implementers at ~1.5-3 calibrated AI-days each.

**Worktrees**: slots 1-8 pre-provisioned at `${WORKSPACE_ROOT}/.tabs/<N>/` on `tab/hk/<N>`. Slots 9-10 added
this morning via `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot 9` + `--add-slot 10`.

**Model directive (per CLAUDE.md model-tier-selection)**: every slot below sized Sonnet-doable + thinking:high.
Opus only required on slot 1 (this orchestrator) + slot 2 (cross-repo propagation-chain design sweep with 6
sub-agents over UAC + 6 features modules + 2 ML services + MDPS). Other slots = Sonnet 4.6.

## Today's slot assignments

| Slot | Theme | Plan-of-record | Calibrated AI-days |
|---|---|---|---|
| 1 | Main orchestrator + on-call + LEDGER + intra-side ping triage + cross-side ping monitor | (this work-split) + [LEDGER](../../harsh_orchestrator/LEDGER.md) | continuous |
| 2 | 🔴 **Propagation chain Phase 3.1-3.N + 4 + 2.A** (Ikenna slot 4 leftover; CRITICAL PATH — Gate 1 fires when complete) | [`expected_unattempted_propagation_chain_2026_05_12.md`](expected_unattempted_propagation_chain_2026_05_12.md) | ~2.5 |
| 3 | Bucket SSOT residuals (provision 6 manual-audit buckets + Q5 features rename + PART B apply-flips reconciler when Gate 1 fires) | [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md) | ~1.5 |
| 4 | defi_simulation_realism Phases 4-6 (Ikenna slot 6 leftover) + Harsh Phases 5B/5C/6B/6C carry-forward | [`defi_simulation_realism_2026_05_10.md`](defi_simulation_realism_2026_05_10.md) | ~2 |
| 5 | **(d) Audit-records PB-1/2/3** — execution-service audit-writer refactor (overwrite→append, retention-lock bucket, customer-ID path fix) | (file new plan or use issue docs) + [`codex_vs_citadel_infrastructure_audit_2026_05_10.md`](codex_vs_citadel_infrastructure_audit_2026_05_10.md) | ~2.5 |
| 6 | **(f) TradFi phantom-audit Databento-aware extension** + manifest reconciliation 15 dry-runs (5 AGs × 3 reconcilers) + apply-flips for cefi/defi/tradfi when Gate 1 fires + GCE VM phantom audit (Gate 3) | [`manifest_cross_asset_rescan_design_2026_05_08.md`](manifest_cross_asset_rescan_design_2026_05_08.md) | ~2 |
| 7 | **(a) 12 AlertCodes + 4 Breakers PRE-cutover** + Telegram channel split (CI vs Live-Ops) + mock_data Phase 3.C/3.D tail | [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) + [`disaster_recovery_circuit_breakers_2026_05_10.md`](disaster_recovery_circuit_breakers_2026_05_10.md) + [`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md) | ~2 |
| 8 | 🆕 **GMX/DRIFT venue capability refactor** — REVERT `DEFI_VENUE_AXIS_OVERRIDES` (UAC@7c8482e); make perp-eligibility a capability not asset_group filter; 3-sub-agent fan-out (UAC + strategy-service + MTDS perp_funding_handler) | [`cross_asset_group_catalogue_audit_2026_05_10.md`](cross_asset_group_catalogue_audit_2026_05_10.md) Phase 1C re-opened | ~2.5 |
| 9 | **Sports+Prediction reconciler classifier extension** (extend `legacy_reason_classifier.py` with sports + prediction rules) + **(c) 6 LookaheadBiasError strict-mode wire-ins** (6-sub-agent fan-out) + slot-3 strategy-paper VM verification | UTL `legacy_reason_classifier.py` + freeze-gate item 5 + [`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md) | ~2.5 |
| 10 | **Day-3 quick wins**: MDPS 19 test failures (EmissionDecision schema drift) + Phase 4.FEATURES sweep (6 callsites → freeze-gate item 3 to 9/9) + dex_perp Phase 2 remainder + EigenLayer Phase 3 | MDPS test fixes + [`dex_perp_and_venue_data_expansion_2026_05_12.md`](dex_perp_and_venue_data_expansion_2026_05_12.md) Phase 2-3 | ~2 |

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

- **Plan-of-record**: [`expected_unattempted_propagation_chain_2026_05_12.md`](expected_unattempted_propagation_chain_2026_05_12.md)
- **Worktree**: `.tabs/2/` on `tab/hk/2`
- **Model directive**: Opus 4.7 / thinking: high (cross-repo design sweep; 8 sub-agent fan-out)
- **Repos owned**: `features-service` (6 modules: delta_one/calendar/onchain/volatility/sports/commodity) +
  `ml-training-service` + `ml-inference-service` + `market-data-processing-service` (writegate 2.A)
- **Scope**:
  - **Phase 3.1-3.N**: 6-sub-agent fan-out — one per features module. Pattern: Option A runtime comparison at
    `_get_instruments()` call. Compare full catalog vs post-filter set, write
    `expected_unattempted(EXPECTED_OUTSIDE_PROCESSING_SCOPE)` for `all - in_scope`. No UAC frozenset needed.
    Reference template in plan body § "Phase fan-out".
  - **Phase 4**: ml-training + ml-inference — same Option A pattern, same shape as Phase 3.
  - **PART C (writegate 2.A)**: MDPS 4-state output routing. Delete `_create_empty_output`; wire
    `empty_confirmed`→forward-fill, `attempted_failed`→NaN, `expected_unattempted`→propagate. Same MDPS repo,
    can run PARALLEL with Phase 3.
- **Done-definition**:
  - 6 features modules write `expected_unattempted` for out-of-scope instruments + 4 tests each pass
  - ml-training + ml-inference same pattern + 4 tests each
  - MDPS 4-state routing wired + tests pass
  - Plan checkboxes flipped + commits pushed to `live-defi-rollout`
  - Cross-side ping filed: "GATE 1 FIRED — propagation chain Phase 3+4+2.A complete"
- **Full-execution criterion**: all sub-agents land + workspace QG green on touched repos. Gate 1 fires when
  the cross-side ping lands.
- **Cross-tab handshakes**: slot 3 PART B + slot 6 apply-flips unblock when Gate 1 fires.
- **Carry-forward to next cycle**: NONE (this is the final phase before Gate 1).

### Slot 3 — Bucket SSOT residuals

- **Plan-of-record**: [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md)
- **Worktree**: `.tabs/3/` on `tab/hk/3`
- **Repos owned**: `deployment-service` (yaml + provisioning scripts) + `instruments-service` (reconciler invocations)
- **Scope**:
  - **Provision 6 manual-audit buckets** (Phase 0c handoff from Ikenna slot 8): 3 envs × 2 clouds (GCP+AWS). Apply
    ≥7-year retention lock (GCP Object Retention Lock, AWS S3 Object Lock COMPLIANCE). Coldline/Glacier-IA after 90d.
  - **Apply Q5 features-cross-instrument + features-multi-timeframe rename** (operator-resolved A5 2026-05-11):
    aliased shorter kind names in yaml (`features-xinstrument`, `features-mtf`); resolver translates; 5 per-AG entries
    each (cefi/defi/tradfi/prediction/sports).
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

- **Plan-of-record**: [`defi_simulation_realism_2026_05_10.md`](defi_simulation_realism_2026_05_10.md)
- **Worktree**: `.tabs/4/` on `tab/hk/4`
- **Repos owned**: `execution-service` (matching engine + AMM connectors) + `unified-api-contracts` (PoolShape enum)
- **Scope**:
  - **Phase 4-6 implementation** (consumes Ikenna slot 6 design at PM@`3b76a5ef` + `d66b0f9f`): per-pool-class
    modules `curve.py` / `balancer.py` / `solana_clmm.py` / `solidly_fork.py` / `aggregator.py` (all NEW);
    refactor `engine.py:_amm_match_impl` (currently hardcoded `UniswapV2Pool` at line 471) to dispatcher.
  - **Golden test set**: per-PoolShape JSON fixture corpus under
    `execution-service/tests/integration/fixtures/amm_golden_swaps/`. Pytest harness skeleton per Ikenna's design.
  - **Phase 5B/5C/6B/6C** (Harsh carry-forward): self-contained sub-phases per plan body.
- **Critical correction** (from Ikenna's overnight design): V2/V3/V4 pool classes ALREADY EXIST in
  `amm.py:52,259,403` — Phase 2A is Protocol-conformance refactor + dispatcher rewrite, NOT greenfield V3/V4 build.

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
  - **PB-2 (retention-lock provisioning)**: audit-records bucket gets GCP Object Retention Lock (≥7 years) +
    AWS S3 Object Lock COMPLIANCE mode (≥7 years). Bucket kind `audit-records` in `cloud-providers.yaml`.
  - **PB-3 (wrong-customer-ID-path fix)**: `client_order_id` is currently passed where `client_id` should go in
    storage path. Fix path layout to `audit/{client_id}/{date}/{event_type}/{client_order_id}_{ts}.jsonl`.
- **Done-definition**:
  - Append-only writes verified (write same key twice → both events appear in JSONL)
  - Retention lock verified via `gcloud storage buckets describe` (`retentionPolicy.retentionPeriod >= 220752000`)
  - Path layout fix verified via integration test (write order, read back, assert path components correct)

### Slot 6 — TradFi phantom-audit + manifest reconciliation operational

- **Plan-of-record**: [`manifest_cross_asset_rescan_design_2026_05_08.md`](manifest_cross_asset_rescan_design_2026_05_08.md)
- **Worktree**: `.tabs/6/` on `tab/hk/6`
- **Repos owned**: `instruments-service` (reconcilers) + GCE VM operations
- **Scope**:
  - **(f) Extend `reconcile_phantom_manifest_rows_all.py`** with Databento-aware drift-axes (per-schema-bundle,
    sports per-league SSOT + UAC date-clips, cross-asset venue-less). Per-cluster real-vs-false-pos verify.
  - **15 manifest reconciliation dry-runs** (5 AGs × 3 reconcilers) on GCE VM — Ikenna started yesterday but never
    finished + signal went bad. Use 3 reconcilers per asset_group:
    `reconcile_legacy_blank_to_typed_reason.py` / `reconcile_expected_absence_reasons.py` /
    `reconcile_phantom_manifest_rows_all.py` — `--dry-run` first, then `--apply-flips` for cefi/defi/tradfi when
    Gate 1 fires (slot 2 ping triggers this).
  - **Phantom audit Gate 3**: run on GCE VM with full manifest read; same-region recommended (18× faster than
    cross-region per codex).
  - **Triage real phantoms**: for non-stale-audit-path false positives, file follow-up issue docs or fix in same
    logical unit if simple.
- **Done-definition**:
  - 15 dry-run logs uploaded to `gs://deployment-scripts-{pid}/recon-logs/2026-05-13/`
  - Apply-flips run for cefi/defi/tradfi (if Gate 1 fires) + before/after counts in plan body
  - Phantom audit results table populated (per-AG real vs false-positive split)

### Slot 7 — AlertCodes + Breakers + Telegram split + mock_data tail

- **Plans-of-record**: [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) Phase 1.E
  + [`disaster_recovery_circuit_breakers_2026_05_10.md`](disaster_recovery_circuit_breakers_2026_05_10.md) Phase 1.A/4
  + [`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md) Phase 3.C/3.D
- **Worktree**: `.tabs/7/` on `tab/hk/7`
- **Repos owned**: `unified-api-contracts` (AlertCode + CircuitBreakerId enums) + `alerting-service` (notifier +
  GHA Telegram routing) + `risk-and-exposure-service` (breaker wiring) + features-service mtds_read tail
- **Scope**:
  - **8 AlertCode extensions**: `VENUE_HALTED`, `LENDING_POOL_PAUSED`, `LENDING_BORROW_CAP_REACHED`,
    `LENDING_UTILIZATION_HIGH`, `MARKET_DATA_STALE` (literal name gap; current substitute `TICK_STALENESS`),
    `GAS_PRICE_SPIKE`, `GAS_BUDGET_EXCEEDED`, `KILL_SWITCH_ORACLE_DIVERGENCE`. Add to UAC `AlertCode` StrEnum +
    route via `AlertChannel.TELEGRAM` (new live-ops chat_id, see below).
  - **4 CircuitBreakerId + BreakerConfig extensions**: `ORACLE_STALENESS_SECONDS` (staleness ≠ deviation),
    per-chain `RPC_OUTAGE_SECONDS` (disambiguate), `ARBITRAGE_PRICE_DISPERSION` `applies_to` seed for
    `RPC_OUTAGE_SECONDS`, `LENDING_POOL_UNAVAILABLE_SECONDS` (paused+utilization sub-modes).
  - **Telegram channel split** (operator-pending manual step): operator creates new Telegram channel + adds
    existing bot + provides chat_id (`-100...` format). I add as GHA repo variable `TELEGRAM_CHAT_ID_OPS` across
    all repos. Alerting-service notifier routes runtime alerts (gas/breakers/venue-halted) to new chat_id; CI/QG
    fails stay on existing `TELEGRAM_CHAT_ID`. Until operator provides chat_id, both go to existing channel.
  - **mock_data Phase 3.C/3.D** (Day-3 carry-forward): per-reader threading for 4 stages that exit nonzero
    (mdps_compute / features / ml_inference / matching_engine). Re-run benchmark VM matrix once threading lands.
- **Done-definition**:
  - 12 new enum entries + corresponding alerting-service route map entries + unit tests
  - Telegram routing tested via dry-run `notify-telegram.yml` invocation (existing chat_id; new chat_id if available)
  - mock_data benchmark report shows 4 previously-nonzero stages now exit 0

### Slot 8 — 🆕 GMX/DRIFT venue capability refactor

- **Plan-of-record**: [`cross_asset_group_catalogue_audit_2026_05_10.md`](cross_asset_group_catalogue_audit_2026_05_10.md)
  Phase 1C re-opened (overnight axis_override approach being reverted per operator+Ikenna chat 11:22 IST)
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
    - `carry_staked_basis` + `arbitrage_price_dispersion` archetype perp-hedge venue eligibility: query by
      capability (`venue.has_perp_funding` / `perp_funding in DATA_TYPE_CAPABILITIES[venue]`), NOT by
      `asset_group == "cefi"`. Cross-venue funding arb selector same change.
    - Grep for `asset_group == "cefi"` / `VENUES_BY_ASSET_GROUP["cefi"]` in strategy-service; refactor each to
      capability-check where the semantic intent is "perp-eligible venues".
    - Tests: assert GMX-ARBITRUM + DRIFT-SOLANA appear in perp-hedge eligible set for both archetypes.
  - **Sub-agent C (MTDS handler audit)**:
    - Audit `market_tick_data_service/perp_funding_handler.py` (or equivalent) for cefi-only assumptions:
      hard-coded asset_group filters, bucket-resolution path, manifest writer asset_group passthrough.
    - Make asset_group-agnostic if needed; verify GMX-ARBITRUM/GMX-AVALANCHE/DRIFT-SOLANA data flows correctly
      through it (test mode: dry-run a 1-day batch for GMX-ARBITRUM, verify manifest writes land under
      `asset_group="defi"`).
- **Done-definition**:
  - UAC revert pushed + downstream tests pass + venue lists clean
  - Strategy-service perp-eligibility unit tests pass for both archetypes including GMX/DRIFT
  - MTDS dry-run for GMX-ARBITRUM produces parquet under `gs://market-data-tick-defi-prd-{pid}/` (NOT cefi bucket)

### Slot 9 — Sports+Prediction reconciler classifier extension + LookaheadBias 6 wire-ins + strategy-paper VM verification

- **Plans-of-record**: UTL `legacy_reason_classifier.py` source +
  freeze-gate item 5 in [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  + [`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md)
- **Worktree**: `.tabs/9/` on `tab/hk/9` (provisioned this morning)
- **Repos owned**: `unified-trading-library` (classifier extension + LookaheadBiasError wire-ins) + features
  modules (6 families for lookahead) + `e2e-testing` (strategy-paper VM verification)
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
  - **(c) 6 LookaheadBiasError strict-mode wire-ins** (~1 cal AI-day, 6-sub-agent fan-out): flip
    `LookaheadBiasError` from "warn" mode to strict-mode "raise" across 6 feature families: delta_one,
    volatility, calendar, commodity, cross_instrument, multi_timeframe. Each sub-agent handles one family.
    Mechanical 30-min-per-family job. Closes freeze-gate item 5 before May 15.
  - **Slot-3 strategy-paper VM verification** (~30 min): re-launch
    `strategy-paper-carry-staked-basis-20260513-AM` smoke VM with the Phase 2 P0 resolver fix
    (strategy-service@61dc112 + e2e-testing@8427dc0); verify event stream (STARTED + ≥1 progress/hour + STOPPED).
    Plus 2 deferred items: `ServiceBootstrap` wire-in into `colocated_engine.py` + self-delete trap in
    `setup-data-pipeline-vm.sh`.
- **Done-definition**:
  - Sports + prediction classifier rules + tests pass
  - 6 LookaheadBiasError wire-ins shipped + tests pass + freeze-gate item 5 ✅ flipped
  - strategy-paper VM emits STARTED/STOPPED + self-deletes; ServiceBootstrap wire-in shipped

### Slot 10 — Day-3 quick wins (MDPS tests + Phase 4.FEATURES + dex_perp + EigenLayer)

- **Plans-of-record**: MDPS test fixes (`market-data-processing-service/tests/unit/`)
  + freeze-gate item 3 in [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  + [`dex_perp_and_venue_data_expansion_2026_05_12.md`](dex_perp_and_venue_data_expansion_2026_05_12.md) Phase 2-3
- **Worktree**: `.tabs/10/` on `tab/hk/10` (provisioned this morning)
- **Repos owned**: `market-data-processing-service` (test fixes) + `features-service` (Phase 4.FEATURES sweep) +
  `market-tick-data-service` (dex_perp Phase 2 remainder) + `features-service` (EigenLayer Phase 3)
- **Scope**:
  - **MDPS 19 test failures** (~30-60 min Sonnet): 15 from `EmissionDecision.__init__()` missing 2 required args
    (`service_emission_state` + `last_emission_decision_at`) — update test instantiations to new signature.
    Plus 1 sports adapter (DRAFTKINGS), 1 CLI main (ENVIRONMENT=test), 2 freshness logic drift.
  - **Phase 4.FEATURES sweep** (~30 min): 6 explicit `pipeline_mode=` kwargs in calendar `batch_handler.py` +
    sports `batch_handler.py`. Mechanical. Closes freeze-gate item 3 from 8/9 → 9/9.
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

- **(e) GMX/DRIFT direction CORRECTION** — slot 8 reverts axis_override + ships capability refactor today. Ikenna's
  slot 2 work on Phase 1C is preserved as audit-trail (the axis_override commit stays in git history); the plan body
  Phase 1C entry gets re-shaped.
- **Q7(b) bucket shape-alignment** — slot 3 holds; if Ikenna's answer lands mid-day, slot 3 ships in same logical
  unit; otherwise leaves as `- [ ]` for next cycle.
- **Operator-pending list refreshed**: was 8 items, now 1 (Q7(b)). Will refresh ledger after Ikenna's reply.

## Spawn prompts (paste-ready)

> **Reading order for every spawned slot**: (1) [`harsh_orchestrator/AGENT_ONBOARDING.md`](../../harsh_orchestrator/AGENT_ONBOARDING.md)
> → (2) [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) → (3) [`harsh_orchestrator/LEDGER.md`](../../harsh_orchestrator/LEDGER.md)
> § "Slot N entry" → (4) this work-split § "Slot N" → (5) plan-of-record. Boot ack to
> `harsh_orchestrator/pings/slot_<N>.md` per AGENT_ONBOARDING template before starting work.

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

For each remaining slot, the operator pastes a spawn prompt with the same READ + SCOPE + DONE-DEFINITION shape,
swapping the scope to the slot's section above. Full per-slot spawn prompts can be generated by slot 1 main on
request (or each slot reads work-split § "Slot N" + plan-of-record + does its own boot ack).

**Model tier for all slots 3-10**: Sonnet 4.6 / thinking: high.

---

## LEDGER updates (slot 1 to apply today)

- Update boot snapshot for Day-4 (8-slot → 10-slot Model A)
- Operator-pending list: 8 → 1 (Q7(b) bucket shape only)
- Add ✅ closeouts for GMX/DRIFT direction correction + sports/pred reconciler scope decision + AlertCodes/Breakers
  scope + LookaheadBias owner + audit-records PB-1/2/3 scope + TradFi phantom-audit owner
- Add 🔴 critical-path callouts: slot 2 Gate 1 + slot 10 freeze-gate item 3 closure
- Cross-side handshake banner: Ikenna's slot 2's GMX/DRIFT axis_override being reverted (preserve git history)
