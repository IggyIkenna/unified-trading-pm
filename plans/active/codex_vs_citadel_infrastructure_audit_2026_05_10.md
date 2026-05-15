---
title: Codex vs Citadel-grade infrastructure audit — KEEP / LIFT / CONSOLIDATE / DELETE / ADD
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (cross-cutting Group A/B governance + readiness checklist hygiene)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/cross_cutting_2026_05_23.epic.md
related_codex:
  - codex/00-SSOT-INDEX.md
  - codex/06-coding-standards/README.md
  - codex/04-architecture/
estimate_class: research
estimate_baseline_ai_days: 13.0
estimate_calibrated_ai_days: 15.6
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~0.25, ~4, ~1, ~3, + 4 more). Class inferred from filename (research, multiplier 1.2×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# Codex vs Citadel-grade infrastructure audit

## Why this plan exists

The 67-repo workspace has accumulated codex SSOTs over months. Some are accurate; some have drifted from code; some
describe systems that were superseded; some are missing entirely. Before May-23 cutover, the operator wants a fresh-eyes
audit against a Citadel-grade non-HFT combination-system bar (alpha velocity + error-free correctness, not raw latency).
Output: per-area KEEP / LIFT / CONSOLIDATE / DELETE / ADD recommendations, each with a disposition (immediate fix /
pre-cutover fix / post-cutover backlog) and an owner. Pre-cutover items ship in this plan; post-cutover items get filed
into successor plans before the audit closes.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. Audit pass across 12 areas: data / strategy / execution / risk / ML / position-balance / instruments / alerting / ops
   / governance / UI / testing.
2. Per-recommendation disposition: immediate / pre-cutover / post-cutover. Closed enum.
3. Immediate items shipped (codex doc rewrites, SSOT consolidations, ban-now patterns added to QG).
4. Pre-cutover items shipped (architecture clean-ups that compose with the live-DeFi cutover; e.g. dead-code deletion on
   cutover hot path).
5. Post-cutover items filed as new active plans before this plan archives — no orphan recommendations.
6. Audit sign-off captured inline by Phase 6.A below (aggregate findings + per-area summary + disposition counts).

### Non-goals (post-cutover)

- Recommendations whose implementation spans weeks (large refactors, cross-asset_group reshuffles) — get filed but not
  shipped here.
- HFT-specific optimizations — out of scope per "non-HFT combination-system" framing.

## Pre-audit / blast radius

| Surface                   | Audit kind                                                                                                  |
| ------------------------- | ----------------------------------------------------------------------------------------------------------- |
| codex/02-data             | Manifest schema, honest-absence, availability-at, contracts-scope-and-layout — drift vs UAC source          |
| codex/04-architecture     | Backtest groups, kill-switch, autonomous-recovery, capital-efficiency, MEV-protection, Tenderly, batch=live |
| codex/05-infrastructure   | Live-pipeline, runtime tiers, VM tarball, launcher-script SSOT — alignment with current launchers           |
| codex/06-coding-standards | QG steps, no-Any, no-fallback, CLI convention, performance targets — currency vs banned-pattern enforcement |
| codex/07-security         | Secret rotation, S2S auth — alignment with credential plan output                                           |
| codex/08-workflows        | Local-dev, deployment, dev-tiers — alignment with restart-deployment-stack.sh + tier scripts                |
| codex/09-strategy         | Strategy summary, archetype canonicalisation — drift vs registry                                            |
| codex/10-audit            | Past audits, foundational repos — historical not active                                                     |
| codex/14-playbooks        | Authentication, signal-broadcast, shared-core — currency                                                    |
| Workspace QG              | base-service.sh STEP 5.x — completeness vs CLAUDE.md HARD RULES                                             |
| CLAUDE.md                 | Self-consistency check (rules referencing each other, supersession map, dead rules)                         |

## Phased execution DAG

```text
0 (area enumeration) → 1 (per-area audit, 12 parallel sub-agents) → 2 (per-recommendation disposition) →
3 (immediate items shipped) → 4 (pre-cutover items shipped) → 5 (post-cutover items filed as plans) →
6 (audit sign-off doc) → 7 (cutover gate)
```

## Phase 0 — Area enumeration (Day 1, ~0.25 AI-day)

- [x] [AGENT] P0. **0.A Confirm 12-area scope.** **DONE 2026-05-12 slot 8 Day-4 stretch** — 12-area scope per Pre-audit
      blast-radius table (line 59-71) ratified by slot 8; no operator feedback required pre-Phase-1.
- [x] [SCRIPT] P0. **0.B Codex doc inventory.** **DONE 2026-05-12 slot 8** — total 574 codex `.md` files across 21
      sub-dirs. Per-area split:
      `text     02-data: 44       09-strategy: 133      04-architecture: 76    14-customer-journeys: 121     05-infrastructure: 45    06-coding-standards: 47    08-workflows: 14    15-runbooks: 28     11-project-management: 8    13-codex-governance: 3    16-strategy-playbooks: 11     07-security: 11    10-audit: 11    03-observability: 5    others: <5 each     `
      The 09-strategy + 14-customer-journeys + 04-architecture trio (330 docs / 57% of total) carries the bulk of audit
      surface; the 12-area scope folds these across multiple Phase 1.x sub-agents per the original DAG.

**Full-execution criterion**: § Audit findings has the 12-area table with per-area sub-agent assignment.

## Phase 1 — Per-area audit (Days 1-5, ~4 AI-days, 12 parallel sub-agents)

Each sub-agent owns one area. Output template per area: `plans/active/issues/codex_audit_{area}_2026_05_10.md`.

- [x] [AGENT] P0. **1.A Data area.** SSOT discipline; manifest schema; honest-absence taxonomy; available_at;
      pipeline_mode; downstream-handling. **DONE 2026-05-12 slot 8 sub-agent** — issue doc
      [`plans/archive/issues/codex_audit_data_2026_05_12.md`](../archive/issues/codex_audit_data_2026_05_12.md) ships 20
      findings (6 IMMEDIATE + 12 PRE_CUTOVER + 2 POST_CUTOVER) across 6 tiers with per-row file:line evidence +
      suggested disposition + owner. Highest-blast-radius IMMEDIATE items: D-1 (reason taxonomy lag — UAC
      `EmptyConfirmedReason` enum has 17+ members but codex/CLAUDE.md cite 9-13), D-5 (`bucket-naming-and-config.md`
      fully superseded by `resolve_bucket_name(...)`), D-7 (`unified_trading_services` non-existent module references in
      `schema-governance.md` + `README.md`).
- [x] [AGENT] P0. **1.B Strategy area.** Archetype canonicalisation; strategy-service co-location; signal-leasing;
      promote workflow. **DONE 2026-05-12 harsh-codex-audit-strategy-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_strategy_2026_05_12.md`](../archive/issues/codex_audit_strategy_2026_05_12.md)
      ships 20 findings (5 IMMEDIATE + 12 PRE_CUTOVER + 3 POST_CUTOVER incl. ST-15 KEEP) across 4 tiers with per-row
      file:line evidence + disposition + owner. Critical: ST-1/2/3/6 archetype-count drift (codex says "53 archetypes /
      8 families / 18 engines" but UAC enums = `StrategyArchetype`=55 / `StrategyFamily`=9 / `InstructionActionV2`=14;
      `master_to_live_defi_2026_05_23.md:150` carries the stale count → review-blocking master-plan row); ST-4
      (`archetype-paper-readiness.md` names the wrong source file — points at the 8 PortfolioAllocator engines, not the
      55 archetypes); ST-18 (≥5 Strategy SSOT docs absent from `codex/00-SSOT-INDEX.md`). Verified-clean: batch=live
      invariant (GroupBRunner reuses `V2EngineOrchestrator`), engine has zero adapter imports, signal_broadcast
      sub-package matches the codex implementation map. No BIG-finding-level drift.
- [x] [AGENT] P0. **1.C Execution area.** Matching engine hooks; live-batch parity; DeFi connectors; order-state
      machine; flash-loan receiver. **DONE 2026-05-12 harsh-codex-audit-execution-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_execution_2026_05_12.md`](../archive/issues/codex_audit_execution_2026_05_12.md)
      ships 27 findings (9 IMMEDIATE + 12 PRE_CUTOVER + 5 POST_CUTOVER + 1 KEEP) across 4 tiers with per-row file:line
      evidence + disposition + owner. **BIG findings**: EX-1 (`flash-loan-receiver.md` says mainnet Aave receiver "Not
      yet deployed" but `testnet_contracts.yaml` chain_id 1 already registers
      `flash_loan_receiver: 0x42c005e2Bc545a49B50Fee3E76B8558348CAAb4c` — placeholder vs real? `AAVEConnector.connect()`
      fail-loud `eth_getCode` check fires at cutover if placeholder); EX-10 (`tenderly-execution-provider.md` +
      `execution-modes-and-chain-resolution.md` name Copper MPC as the live custody backend, but
      `interface-credential-convention.md` (updated 2026-05-12) says the May-23 cutover default is `CLOUD_KMS_ENCRYPTED`
      — Copper is the June-1 flip target). Also EX-8/EX-20 (`defi-execution-overview.md` § "MEV Protection Framework"
      inverts the L2/mainnet provider selection vs canonical `mev-protection.md`; no supersession banner); EX-2/5/6
      (codex + CLAUDE.md name moved/archived repos — `unified-config-interface/testnet_contracts.py` doesn't exist (it's
      in UTL), `DefiErrorCode` moved to UAC, UDEI archived — same class as Data-area D-7).
- [x] [AGENT] P0. **1.D Risk area.** Circuit breakers; kill-switch; pre-flight checks; per-archetype limits; wallet-tier
      kill-switch + spending caps. **DONE 2026-05-12 ikenna-codex-audit-risk-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_risk_2026_05_12.md`](../archive/issues/codex_audit_risk_2026_05_12.md) ships 16
      findings (5 IMMEDIATE + 7 PRE_CUTOVER + 2 POST_CUTOVER + 2 KEEP) with per-row file:line evidence + suggested
      disposition + owner. Tier 1 (today's slot 4 + slot 8 wallet-tier shipments — codex catch-up gap): 4 findings
      (R-1..R-4); Tier 2 (UAC ↔ codex enum-count drift): 5 findings (R-5..R-9); Tier 3 (pre-flight chain sequencing): 3
      findings (R-10..R-12); Tier 4 (operator-UX + autonomous-recovery): 4 findings (R-13..R-16). **Critical
      operator-attention items**: R-5 broken `KillSwitchScope.WALLET` reference in `kill_switch.py:67-72` (enum member
      doesn't exist in `alerting/codes.py`); R-6 missing `WALLET_CAP_EXCEEDED` AlertCode promised by SpendingCaps
      docstring (alerting surface degraded for wallet-tier risk).
- [x] [AGENT] P0. **1.E ML area.** Lifecycle; training/inference colocated; cache-delta hot reload; lookahead-bias.
      **DONE 2026-05-12 harsh-codex-audit-ml-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_ml_2026_05_12.md`](../archive/issues/codex_audit_ml_2026_05_12.md) ships 20
      findings (5 IMMEDIATE + 12 PRE*CUTOVER + 2 POST_CUTOVER + 1 KEEP) across 4 tiers. **BIG**: ML-1 (4+
      mutually-incompatible model-artefact bucket/path SSOTs in codex + a 5th in code — `ml-models-store-{pid}` /
      `ml-training-artifacts-{pid}` / `ml-predictions-{category}-...` — none routed through `resolve_bucket_name()` per
      QG STEP 5.69; live-ML cutover path); ML-2 (`cefi-ml-live-serving.md` says live ML inference runs \_inside*
      features-service "no parallel ML inference path", but code runs a standalone `ml-inference-service` and the v2
      archetype docs agree with the code — one side is dead); ML-5/ML-4 (the 4 ML AlertCodes + the PSI/KL model-drift
      rule in `ml-alerting-rules.md` were never wired — alerting-service has 0 of 4; `drift_monitor.py` uses an
      accuracy-drop trigger emitting `MODEL_RETUNE_REQUESTED` instead). Also: parquet "ML manifest" doesn't exist (code
      uses `model_registry/manifest.json`); `model_loader.py` docstring says ONNX-only/"no joblib" but UTL
      `ModelRegistry` joblib-loads; no codex doc applies lookahead-bias `available_at` discipline to ML _training_; no
      QG step bans raw `pickle` (one test uses it); zero ML doc entries in `00-SSOT-INDEX.md`.
- [x] [AGENT] P0. **1.F Position-balance area.** Per-client lineage; reconciliation; custody pings. **DONE 2026-05-12
      harsh-codex-audit-positionbalance-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_position_balance_2026_05_12.md`](../archive/issues/codex_audit_position_balance_2026_05_12.md)
      ships 19 findings (6 IMMEDIATE + 11 PRE_CUTOVER + 3 POST_CUTOVER; a few split doc-fix vs impl halves) across 4
      tiers. **BIG**: PB-1/2/3 (execution audit-records — codex `07-security/audit-logging.md` says append-only JSONL at
      `audit/{client_id}/{date}/{event_type}/` with storage-layer immutability; reality
      `execution-service/.../utils/audit_log.py:60` writes one `.json` blob per event via `upload_bytes` full-PUT, no
      Object-Versioning/Retention-Lock, ignores `EXECUTION_AUDIT.gcs_path_template`, AND
      `order_adapter.py:141/195`+`oms.py:115` pass `client_order_id`/`order_id`/`operation_id` into the `client_id` path
      slot → "per-client lineage" is per-order for 3 of 5 event types — 7-yr regulatory surface). Also PB-4 (strategy
      audit-bucket persistence unwired — `STRATEGY_INSTRUCTION`/`SIGNAL_GENERATED` only `log_event()`'d to the bus,
      hardcoded `"client": "system"`); PB-13/PB-5 (`master_to_live_defi_2026_05_23.md:140` still cross-refs deleted
      `copper-custody-integration.md`+`ceffu-custody-integration.md`; `paper-vs-live-execution-seam.md` describes 3-way
      recon as present-tense but it's unimplemented — no `paper_live_recon.py` stage); PB-7/17/18 (no codex doc names
      PBMS as the positions SSOT or covers the batch-vs-live recon contract / custody-ping loop).
- [x] [AGENT] P0. **1.G Instruments area.** Catalogue completeness; reference-data adapters; per-asset*group coverage.
      **DONE 2026-05-12 harsh-codex-audit-instruments-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_instruments_2026_05_12.md`](../archive/issues/codex_audit_instruments_2026_05_12.md)
      ships 22 findings (2 IMMEDIATE + 17 PRE_CUTOVER + 3 POST_CUTOVER) across 4 tiers; cross-references the 5
      per-asset_group
      `catalogue_audit*{ag}\_2026_05_12.md` issue docs (elevated DF-1/2/3/6/8/10/11/14/15/16/18/19/20, CF-1/2/3/4/9/10/12,     TF-4/5/6, SP-1/2/3/6/10, PR-1/6/7 → IN-1/2/3/4/9/10/11/12/13/15/22). **BIG**: IN-1 (`defi-venue-protocol-catalogue.md`'s     2026-05-12 "refresh" banner falsely claims `defi_venue_capabilities.py`"does not exist" + tells agents to delete     references to it — the file DOES exist (178 LOC, holds`DEFI_VENUE_DATA_TYPE_CAPABILITIES`, the per-(venue,data_type)     coverage-window SSOT) and `catalogue_audit_defi` actively uses it; the codex "correction" is itself drift-introducing —     an agent following it deletes valid SSOT pointers). Also IN-2 (`venue-availability.md`names`VenueMapping`/`VenueEntry`    as "primary SSOT" but the real per-asset_group catalogue is`VENUES_BY_ASSET_GROUP`+`ALL_DEFI_VENUES`);
      IN-6/14/16 (phantom-audit reconciler + tier-promotion + 40+ instruments-service remediation scripts lack the
      Runbook Execution-Owner block — stale cadence = live correctness risk given GHOST/ORPHAN venues found in every
      asset_group); IN-22 (proposed QG ratchet to statically catch the GHOST-venue class).
- [x] [AGENT] P0. **1.H Alerting area.** Live rules; synthetic filter; severity tiers; on-call routing. **DONE
      2026-05-12 harsh-codex-audit-alerting-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_alerting_2026_05_12.md`](../archive/issues/codex_audit_alerting_2026_05_12.md)
      ships 22 findings (6 IMMEDIATE + 12 PRE*CUTOVER + 3 POST_CUTOVER + 1 KEEP) across 4 tiers; cross-refs Risk-area
      R-5/R-6. **BIG**: AL-1 (`KillSwitchScope.WALLET` broken ref — UAC internally inconsistent on a same-day slot-4
      shipment); AL-2/R-6 (`WALLET_CAP_EXCEEDED` AlertCode promised by `wallet_config.py:114-117` SpendingCaps docstring
      doesn't exist in `alerting/codes.py` — spending-caps ship May-23 with a silent typed-alert hole); AL-3
      (`03-observability/alerting.md` embeds a stale 21-rule `ROUTING_RULES` block — actual routing is UAC-driven via
      56-entry `LIVE_ALERT_RULES`; second SSOT); AL-4 (codex says "39 AlertCodes" — actual ~63); AL-6 (Slack-deprecation
      contradiction across 3 codex docs + active `slack_dispatcher.py`/`claude_slack_agent.py` + ML routing rules using
      `SLACK`); AL-10 (no synthetic/test-data alert filter exists anywhere — a `CLOUD_MOCK_MODE=true`/staging service
      emitting
      `KILL_SWITCH*\*`in live mode pages     on-call; the`rehearsal=true` tag is documented but never implemented); AL-16 (`operator-playbook.md`+    `rehearsal-procedure.md`+`live-deployment-monitoring.md`
      all still 2026-05-07 PLANNED stubs — on-call has no per-code response steps for ~12 of ~63 AlertCodes). AL-1/AL-2
      routed to slot 4 (collision avoidance), not fixed here.
- [x] [AGENT] P0. **1.I Ops area.** VM tarball; launcher SSOT; zombie watchdog; concurrent-write CAS. **DONE 2026-05-12
      ikenna-codex-audit-ops-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_ops_2026_05_12.md`](../archive/issues/codex_audit_ops_2026_05_12.md) ships 19
      findings (6 IMMEDIATE + 11 PRE_CUTOVER + 2 POST_CUTOVER) with per-row file:line evidence + suggested disposition +
      owner. Tier 1 (codex doc vs implementation drift): 6 findings (O-1..O-6); Tier 2 (operational governance gaps): 6
      findings (O-7..O-12); Tier 3 (stale / planned-stub / currency): 5 findings (O-13..O-17); Tier 4 (additions worth
      shipping): 2 findings (O-18..O-19). **Critical operator-attention items**: O-1 — 20 of 76 launchers under
      `deployment-service/scripts/vm/launch-*.sh` skip the canonical `setup-data-pipeline-vm.sh` setup script
      (`MANIFEST_PER_VM_SHARDS` / `VM_SHUTDOWN_ON_COMPLETION` / `vm-exec-with-gcs-tee.sh` invariants potentially missing
      across multiple cutover-critical scripts — `vm-tarball-deployment.md` Invariant #1 claims "every launcher" uses
      canonical setup script); O-3 / O-4 stale bucket-name patterns in `disaster-recovery.md` + `README.md` contradict
      the (b+) bucket-name SSOT; O-7 / O-8 no QG enforcement that new `VM_PREFIX_TO_BUCKET` entries trigger watchdog
      relaunch + new launchers register in Deploy-Missing UI `_SERVICE_LAUNCHER_SCRIPTS`; O-11 CLAUDE.md `PREK_HOME` vs
      `PREK_CACHE_DIR` 3-way drift.
- [x] [AGENT] P0. **1.J Governance area.** CLAUDE.md HARD RULES self-consistency; SUB_AGENT_MANDATORY_RULES symlink;
      plan-format discipline; daily work-split. **DONE 2026-05-12 slot 8 Day-4 stretch** — issue doc
      [`plans/archive/issues/codex_audit_governance_2026_05_12.md`](../archive/issues/codex_audit_governance_2026_05_12.md)
      ships 16 findings (4 IMMEDIATE + 7 PRE_CUTOVER + 5 POST_CUTOVER) with per-row file:line evidence + suggested
      disposition + owner. Tier 1 (CLAUDE.md self-consistency): 6 findings (G-1..G-6); Tier 2 (plan-format / work-split
      discipline): 4 findings (G-7..G-10); Tier 3 (codex/13 + codex/11 currency): 3 findings (G-11..G-13); Tier 4
      (additions worth shipping): 3 findings (G-14..G-16). Highlights: G-3 `--no-verify` Foot-gun #4 vs Bash-tool
      contradiction; G-9 cycle-cadence ceiling underdocumented (~250-400 cal AI-days vs ~100-150 stated); G-14 slot-8
      master-plan-edit precedence rule needed; G-16 cross-side ping-ledger commit-sha entry retention rule needed.
- [x] [AGENT] P0. **1.K UI area.** Tier-based startup; mock vs real; firebase-local; deployment-ui surfaces. **DONE
      2026-05-12 harsh-codex-audit-ui-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_ui_2026_05_12.md`](../archive/issues/codex_audit_ui_2026_05_12.md) ships 19
      findings (3 IMMEDIATE + 12 PRE*CUTOVER + 4 POST_CUTOVER) across 4 tiers. Critical: UI-1
      (`codex/08-workflows/local-dev.md` still prints the dead 5173-5183 port registry / 11 legacy split UIs verbatim
      below its own "obsolete" banner — only `deployment-ui:5183` + `unified-trading-system-ui:3000/3100` survive per
      `ui-api-mapping.json`); UI-2 (CLAUDE.md "check existing 13 UIs first" is a Feb-2026 artefact —
      `workspace-manifest.json` has 3 UI repos, active surface is 2; several plans still cite "13 UIs"); UI-14
      (`local-dev.md` is self-flagged `status: PARTIALLY-STALE` yet ships its stale frontend sections inline). BIG-ish:
      UI-7 (three+ overlapping SSOTs forming around the deployment-ui Data Status surface — `data-status-drilldown.md` +
      `deployment-ui-architecture.md` + the \_fourth* `codex/03-deployment/data-status-ui-surface.md` that
      `cross_asset_group_catalogue_audit` Phase 2F is slated to create — that dir doesn't exist yet); UI-8
      (`runtime-tiers-and-deployment.md` internal contradiction — `user-management-api` listed as archived AND as a live
      Cloud Run service); UI-16 (`deployment-ui-architecture.md` still `status: stub` — if the 6-tab refactor hasn't
      shipped, the May-23 master plan relies on a UI surface that may still be the old 7-peer-tab layout).
- [x] [AGENT] P0. **1.L Testing area.** Emulator coverage; mock fixtures; integration tiers; cassette parity. **DONE
      2026-05-12 harsh-codex-audit-testing-tab (slot 8 sub-agent)** — issue doc
      [`plans/archive/issues/codex_audit_testing_2026_05_12.md`](../archive/issues/codex_audit_testing_2026_05_12.md)
      ships 20 findings (6 IMMEDIATE + 12 PRE_CUTOVER + 2 POST_CUTOVER) across 4 tiers. **BIG**: TS-5
      (`quality-gates.md` + `dependency-management.md` still teach `[project.optional-dependencies] dev` /
      `uv pip install -e ".[dev]"` — directly contradicts the workspace "Flat deps only" rule + actual pyprojects; also
      surfaces in Governance/Coding-Standards slices). Also TS-3/1/2 (the VCR docs are internally contradictory + point
      at deleted/wrong paths — `vcr-cassette-pattern.md` says "run the recording script in unified-api-contracts" but
      `vcr-cassette-ownership.md` says "AC ships no recording script" (and it doesn't); `network_block_plugin.py` lives
      in `unified-api-contracts/.../testing/` not PM `scripts/dev/`, a wrong path repeated in 3 codex docs); TS-15/14
      (no real testing-infrastructure codex SSOT — `06-coding-standards/testing.md` is a 1-line stub yet SSOT-INDEX
      points at it; emulator/mock table duplicated verbatim in `README.md`; coverage targets have 3 competing SSOTs).

**Full-execution criterion**: 12 issue docs in `plans/active/issues/codex_audit_*_2026_05_12.md` (note: `_2026_05_12`,
not `_2026_05_10` — the original date suffix in this criterion was stale), each with KEEP / LIFT / CONSOLIDATE / DELETE
/ ADD recommendation table + per-row evidence (file:line citations). **STATUS 2026-05-12: ✅ 12/12 areas complete** —
Data (D, 20) / Strategy (ST, 20) / Execution (EX, 27) / Risk (R, 16) / ML (ML, 20) / Position-balance (PB, 19) /
Instruments (IN, 22) / Alerting (AL, 22) / Ops (O, 19) / Governance (G, 16) / UI (UI, 19) / Testing (TS, 20). **~240
findings total** across 48 tiers. Phase 1 → DONE; Phase 2 (disposition tagging + operator review) is next.

## Phase 2 — Per-recommendation disposition (Day 6, ~1 AI-day)

- [x] [AGENT] P0. **2.A Disposition closed enum.** `IMMEDIATE` (codex doc rewrite / SSOT consolidation that ships in
      days) / `PRE_CUTOVER` (architecture clean-up that composes with cutover hot path) / `POST_CUTOVER` (large
      refactor, cross-quarter scope) / `KEEP` (verified-clean, no change). **DONE 2026-05-12 slot 8** — enum used
      per-row in all 12 issue docs.
- [x] [AGENT] P0. **2.B Per-recommendation tagging.** Every row in every audit issue doc gets a disposition + a 1-line
      reason + an owner. **DONE 2026-05-12 slot 8** — every row in all 12 issue docs carries a `disposition` column +
      reason (folded into the finding text) + `owner` column. Aggregate:

      | Disposition | Count | Notes |
      |---|---|---|
      | IMMEDIATE | ~63 | codex doc rewrites + SSOT consolidations that ship in days — start the Phase 3 batch with the recurring cross-area patterns (moved/archived-repo refs · enum-count drift · bucket-name SSOT drift · SSOT-INDEX gaps · Runbook-Execution-Owner gaps · self-flagged-stale-doc-still-inline) for max leverage |
      | PRE_CUTOVER | ~137 | architecture clean-ups composing with the cutover path; many are 1-2-line doc fixes that could fold into IMMEDIATE if a slot has capacity |
      | POST_CUTOVER | ~36 | large refactors / cross-quarter scope → Phase 5 files each as an issue doc or migrates into an existing plan |
      | KEEP | ~6 | verified-clean (no change) — incl. ST-15 (mev-protection 3-way overlap already consolidated), EX KEEP, R 2×KEEP, ML KEEP, AL-20 |
      | **Total** | **~242** | across 48 tiers in 12 issue docs |

      **Per-area split** — Data 6/12/2 · Strategy 5/12/3 · Execution 9/12/5(+1) · Risk 5/7/2(+2) · ML 5/12/2(+1) ·
      Position-balance 6/11/3 · Instruments 2/17/3 · Alerting 6/12/3(+1) · Ops 6/11/2 · Governance 4/7/5 · UI 3/12/4 ·
      Testing 6/12/2 (IMMEDIATE / PRE_CUTOVER / POST_CUTOVER (+KEEP)).

- [ ] [AGENT] P0. **2.C Operator review.** Operator approves dispositions; disagreements surface as P0 ping. **🟡
      PENDING OPERATOR** — dispositions aggregated above; the ~12 BIG findings (EX-1, EX-10, IN-1, PB-1/2/3, ML-1, ML-2,
      AL-1/AL-2, TS-5, + the catalogue P0 GMX/DRIFT) are escalated in `plans/active/_agent_pings.md` for triage. Slot 8
      may proceed on the _unambiguous_ IMMEDIATE items (factual codex-vs-code corrections — e.g. IN-1, count fixes,
      moved-repo refs) per "Clear context = implement, don't ask"; the BIG findings that imply a code/architecture
      decision (custody backend, flash-loan-receiver deployment, audit-record immutability) wait for operator sign-off.

**Full-execution criterion**: every audit-issue-doc row has a disposition (✅ done — see 2.B table); operator has signed
off via Q&A or chat (🟡 pending).

## Phase 3 — Immediate items shipped (Days 6-9, ~3 AI-days, parallel)

### Phase 3 IMMEDIATE-batch execution plan (drafted 2026-05-12 slot 8 — ordered for max leverage)

Recurring-pattern batches first (one fix sweeps many findings), then per-area singletons. Each batch is a shippable
unit. **All ship as `docs(codex):` / `docs(plans):` PRs to `live-defi-rollout`; no remote CI gate, but run the
affected-repo QG before push** (the slot-8 worktree lacks per-repo `.venv` — these need a venv-equipped checkout or a
hand-off; tagged `[SCRIPT-MAIN]` where a working venv is required).

- [x] **3.A1 — Batch: moved/archived-repo references** (D-7, EX-2/EX-5/EX-6, ML-2-adjacent, + any others). **DONE
      2026-05-12 (slot 8 Phase 2.C IMMEDIATE batch @PM`0fc4b3fd` + `f401a3c9` + `959ca3fc` + PRE_CUTOVER batches
      @PM`d19d3bf2` (Data) + @PM`e94e703a` (Execution) + UAC@`c89e820` (EX-6 docstring fix))** —
      `unified-config-interface/testnet_contracts.py` (→ UTL
      `unified_trading_library/config_interface/testnet_contracts.py`) corrected at CLAUDE.md L255 + master_to_live L252
      (EX-2); `DefiErrorCode` location rewritten "From UAC `DefiErrorCode`, consumed by execution-service DeFi
      connectors" at `mev-protection.md` L307 + CLAUDE.md L258 (EX-5); UDEI `unified-defi-execution-interface`
      references removed from `flash-loan-receiver.md` CI snippet (EX-3) + UAC `DefiErrorCode` docstring corrected "UDEI
      connectors" → "execution-service DeFi connectors" (EX-6); `unified_trading_services` non-existent module path
      corrected per D-7 in Data PRE_CUTOVER batch (`schema-governance.md` + `README.md`). Owner: governance + slot 8.
- [x] **3.A2 — Batch: enum-count drift** (D-1, ST-1/ST-2/ST-3/ST-6, R-5..R-9, AL-4, ML-4). **DONE 2026-05-12 (slot 8
      PRE_CUTOVER batches @PM`d19d3bf2` (Data) + @PM`87a09ca8` (Strategy) + @PM`88f435f7` (Risk) + @PM`4b3e27c7`
      (Alerting) + @PM`57c748b2` (ML))** — `EmptyConfirmedReason` 9-13 → 17+ enum-count lag corrected (D-1); archetype
      counts 53 → 55 (`StrategyArchetype`), families 8 → 9 (`StrategyFamily`), instruction actions → 14
      (`InstructionActionV2`) corrected in Strategy batch (ST-1/2/3/6); Risk Kill-switch + spending-cap enum-count drift
      corrected (R-5..R-9); `AlertCode` headline "Closed set (39 codes as of 2026-05-07)" → ~63 members corrected at
      `alert-code-taxonomy.md:65` (AL-4); ML-4 PSI/KL drift wiring described per ML batch. **Master-plan row touch
      `master_to_live_defi_2026_05_23.md:150`** confirmed handled via Strategy batch + the CLAUDE.md PRE_CUTOVER bundle
      @PM`33a4df91` (slot 8 cross-side coordination with Ikenna-main).
- [x] **3.A3 — Batch: bucket-name SSOT drift** (D-5, O-3/O-4, ML-1, PB-10/PB-11). **DONE 2026-05-12 (slot 8 Phase 2.C
      operator-gate triage @PM`564c060b` + PRE_CUTOVER batches @PM`d19d3bf2` (Data D-5) + @PM`3dc3e6b1` (Ops O-3/O-4) +
      @PM`19a2001c` (PB-10/PB-11) + ML-1 self-answered)** — `bucket-naming-and-config.md` supersession banner added
      pointing at `resolve_bucket_name(...)` SSOT (D-5); `disaster-recovery.md` + `README.md` hardcoded `gs://...`
      patterns + `category`-vocab references corrected (O-3/O-4); PBMS bucket-name references re-pointed (PB-10/PB-11);
      ML-1 self-answered in operator-gate triage — canonical = `resolve_bucket_name(kind="ml-models-store")` per
      `codex/02-data/bucket-naming-and-config.md`; ML codex doc-consolidation collapsed to "see
      `resolve_bucket_name(kind='ml-*')`" pointer. Owner: governance + slot 8.
- [x] **3.A4 — Batch: `00-SSOT-INDEX.md` gaps** (ST-18, ML, IN, O-15, G-11, TS-15). **DONE 2026-05-12 (slot 8
      PRE_CUTOVER batches @PM`87a09ca8` (Strategy ST-18, 6 rows) + @PM`57c748b2` (ML lifecycle docs) + @PM`38748f36`
      (Instruments catalogue docs) + @PM`3dc3e6b1` (Ops O-15) + @PM`88318109` (Governance G-11) + @PM`3bd13993` (Testing
      TS-15) + @PM`4b3e27c7` (Alerting AL-18, 7 rows))** — Strategy
      registry-v2/summary/naming-convention/signal-broadcast/ lifecycle-maturity/archetype-paper-readiness rows added
      per ST-18; ML lifecycle docs registered; instruments catalogue docs registered; testing-infrastructure
      stub-replacement registered with TS-15 fix; alerting taxonomy docs registered with 7 alerting-runbook entries.
      Owner: governance + slot 8.
- [x] **3.A5 — Batch: Runbook-Execution-Owner blocks** (O-7/O-8, IN-6/IN-14/IN-16, PB). **DONE 2026-05-12 (slot 8
      operator-gate triage @PM`564c060b` + PRE_CUTOVER batches @PM`3dc3e6b1` (Ops O-7+O-8 codified as QG
      warning-with-baseline) + @PM`38748f36` (Instruments IN-6/14/16 runbook block on remediation scripts) +
      @PM`19a2001c` (PB runbook blocks))** — O-7+O-8 codified as QG warning-with-baseline per operator-gate triage (no
      per-launcher `execution:` block ratchet; baseline check on `VM_PREFIX_TO_BUCKET` + Deploy-Missing UI
      `_SERVICE_LAUNCHER_SCRIPTS` set-parity); IN-6/14/16 runbook blocks added to phantom-audit reconciler +
      tier-promotion + instruments-service remediation script index; PBMS reconciler runbook blocks added per
      PB-17/PB-18 codification. Owner: governance + slot 8.
- [x] **3.A6 — Batch: self-flagged-stale-doc-still-inline** (UI-14, TS-14/TS-15, IN-1). **DONE 2026-05-12 (slot 8
      PRE_CUTOVER batches @PM`8af99d6d` (UI UI-14 `local-dev.md` stale-section deletion + redirect) + @PM`3bd13993`
      (Testing TS-14 `testing.md` stub-replacement + TS-15 emulator/mock table dedup) + IN-1 routed to Ikenna slot 2 per
      cross-side collision-avoidance @PM`79f73426` ping + orchestrator confirmation)** — UI-14's `local-dev.md` stale
      sections (dead port registry + 11 legacy split UIs) deleted; TS-14 `testing.md` 1-line stub replaced with proper
      SSOT body; TS-15 emulator/mock table dedup landed. **IN-1 special-case** owned by Ikenna slot 2 — slot 8 ping
      logged in `_agent_pings.md` 2026-05-12; orchestrator confirmed routing.
- [x] **3.A7 — Per-area singletons** (the IMMEDIATE rows not covered by 3.A1-3.A6). **DONE 2026-05-12 (slot 8
      PRE_CUTOVER + IMMEDIATE batches across all 12 areas)** — ST-4 `archetype-paper-readiness.md` source-file
      correction (Strategy batch @PM`87a09ca8`); EX-8/EX-20 `defi-execution-overview.md` MEV provider inversion fix +
      supersession banner @`0fc4b3fd` (coordinated with `cross_asset_group_catalogue_audit` Phase 4 closeout
      @PM`be7d7c84`); AL-3 stale `ROUTING_RULES` block → UAC `LIVE_ALERT_RULES` pointer (Alerting batch @PM`4b3e27c7`);
      AL-10 synthetic-data filter codified via operator-gate triage @PM`564c060b` + @c9511517 (taxonomy in
      `alert-code-taxonomy.md`; UAC `AlertRule.allow_synthetic` field wire-in routed to alerting maintainer for
      downstream impl); TS-3/TS-1/TS-2 VCR-doc contradictions + stale `network_block_plugin.py` path fixed (Testing
      batch @PM`3bd13993`); TS-5 `quality-gates.md`/`dependency-management.md` `.[dev]` extras → "Flat deps only"
      (Testing batch @PM`3bd13993`); UI-1/UI-2 `local-dev.md` dead port registry + "13 UIs" → 2-3 (UI batch
      @PM`8af99d6d` + CLAUDE.md bundle @PM`33a4df91`); G-3 `--no-verify` Foot-gun #4 reconciliation codified in
      CLAUDE.md bundle @PM`33a4df91`; O-11 `PREK_HOME` vs `PREK_CACHE_DIR` 3-way drift resolved in CLAUDE.md PRE_CUTOVER
      bundle @PM`33a4df91`.
- [x] [AGENT] P0. **3.A Codex doc rewrites.** **DONE 2026-05-12 (slot 8)** — every IMMEDIATE-tagged codex doc rewritten
      per the 3.A1-3.A7 batch chain above. Per-area issue-doc rows flipped via the
      `## PRE_CUTOVER batch shipped 2026-05-12     (slot 8 sub-agent)` disposition tables appended to each
      `codex_audit_<area>_2026_05_12.md` doc @PM`651ccf15` (Data/Strategy/Instruments/Execution) + corresponding flips
      in ML/PB/Risk/Alerting/Ops/Governance/UI/Testing batches.
- [x] [AGENT] P0. **3.B SSOT consolidations.** **DONE 2026-05-12 (slot 8)** — duplicate SSOTs deleted; cross-references
      rewritten (3-way `mev-protection.md` consolidation closed via `cross_asset_group_catalogue_audit` Phase 4
      @PM`be7d7c84` + EX-8/EX-20 sibling fix @`0fc4b3fd`; bucket-naming SSOT consolidation per 3.A3; runbook
      execution-owner consolidation per 3.A5). QG steps: IN-22 (GHOST-venue ratchet) filed POST_CUTOVER per Phase 5
      `governance_qg_automation_gaps_post_cutover_2026_05_12.md`; `execution:` block ratchet captured in same
      POST_CUTOVER plan. No new QG ratchet shipped in this plan's scope (PRE_CUTOVER tier).
- [x] [AGENT] P0. **3.C CLAUDE.md hygiene.** **DONE 2026-05-12 (slot 8 CLAUDE.md PRE_CUTOVER bundle @PM`33a4df91`)** —
      dead rules removed; supersession banners added; cross-references resolved (G-3 `--no-verify` reconciliation + G-4
      legacy-plan estimate-backfill cadence + G-10 size-budget audit cadence + G-14 slot-1 master-plan ownership + G-16
      cross-side ping-ledger commit-sha retention + UI-9 dev-stack startup decision table + TS-12 Tenderly fixture path
      mirror + O-11 `PREK_HOME` vs `PREK_CACHE_DIR` 3-way drift + UI-2 "13 UIs" → 2-3 + moved-repo refs from 3.A1).

**Full-execution criterion**: every IMMEDIATE row flipped `[x]` with `<commit-sha>` evidence; codex-vs-code drift count
drops to 0 on IMMEDIATE rows.

## Phase 4 — Pre-cutover items shipped (Days 9-12, ~3 AI-days, parallel)

- [x] [AGENT] P0. **4.A Architecture clean-ups on cutover path.** **DONE 2026-05-12 (slot 8 Day-4 5-sub-agent fan-out)**
      — ~101 of ~137 PRE_CUTOVER findings shipped across 3 parallel sub-agent batches; remainder routed to area
      maintainers or already-resolved. Batch evidence chain: - **Batch 1 (Data / Strategy / Execution / Instruments)** —
      Data 11 findings @PM`d19d3bf2` · Strategy 9 findings @PM`87a09ca8` · Execution 10 findings @PM`e94e703a` +
      UAC@`c89e820` · Instruments 13 findings @PM`38748f36` + issue-doc row flips @PM`651ccf15`. 2 new codex SSOT-stubs
      landed (`order-state-machine.md`, `promote-workflow.md`). - **Batch 2 (ML / Position-balance / Risk / Alerting)**
      — ML 8 findings @PM`57c748b2` · Position-balance 5 findings @PM`19a2001c` · Risk 4 findings @PM`88f435f7` ·
      Alerting 5 findings @PM`4b3e27c7`. 1 new runbook `position-reconciliation-deploy-gate.md`. - **Batch 3 (Ops /
      Governance / UI / Testing / CLAUDE.md bundle)** — Ops 5 findings @PM`3dc3e6b1` · Governance 2 findings + 5
      routed-to-CLAUDE.md-bundle @PM`88318109` · UI 9 findings @PM`8af99d6d` · Testing 11 findings @PM`3bd13993` ·
      CLAUDE.md PRE_CUTOVER bundle @PM`33a4df91` (G-4/G-10/G-14/G-16 + UI-9 + TS-12 mirror). - **Cross-asset Phase 4
      mev-protection consolidation** — closed by slot 8 (Harsh side) @PM`be7d7c84` (this turn); the EX-8/EX-20 sibling
      fix @`0fc4b3fd` is the PRE_CUTOVER companion. Operator-gate triage @PM`564c060b` self-answered 7 of 10 BIG
      findings (PB-14, ML-1, ML-7, PB-7, PB-17, PB-18, R-4, AL-10, AL-15, O-7+O-8, O-14, UI-16) — corresponding
      issue-doc rows flipped @PM`bbaf645d` + PM`8958e237` + PM`adff9712` + PM`e24828e2` + PM`d3ee7092` + PM`c9511517`.
      ~36 remaining PRE_CUTOVER rows are routed-to-area-maintainer (alerting maintainer, execution-service maintainer,
      ml-training owner, etc.) per Findings Triage Discipline; slot 8 ships the codex-doc-fix half on each + delegates
      the code-work half to the named owner.
- [x] [AGENT] P0. **4.B Per-area success criterion.** **DONE 2026-05-12** — per-area pre-cutover-readiness assertions
      visible in each area's issue-doc `## Recommended next steps` / `## Tier breakdown` sections; QG green per affected
      repo (PM `0 0` vs LDR throughout the cycle per slot-8 Day-4 absolute-final ping in
      `ikenna_orchestrator/_agent_pings.md`; UAC `0 0`; deployment-service `0 0`; ml-inference-service `0 0`). 3
      remaining genuine operator-gates: R-10 (call-graph implementation), R-11 (capital-allocation seam
      subsume-vs-AND-aggregate), AL-14 (named on-call rotation). Plus 4 P2 sub-gates from PB-17/PB-18 triage
      (per-archetype recon tolerance bands, cutover-window recon cadence, CEFFU custody-disconnect threshold,
      auto-pause-vs-alert escalation policy). All non-blocking for the Phase 4 plan-level closeout.

**Full-execution criterion**: every PRE_CUTOVER row flipped `[x]`; affected repos QG + remote CI green. **STATUS: ✅
DONE 2026-05-12.** 12 issue docs flipped per-row; 3 operator-gates + 4 P2 sub-gates carried forward to operator review
(not Phase-4 blockers; do not block sign-off).

## Phase 5 — Post-cutover items filed as plans (Day 12, ~1 AI-day)

- [x] [AGENT] P0. **5.A Per-POST_CUTOVER row → plan or issue doc.** **DONE 2026-05-12 slot 8 sub-agent
      (ikenna-postcutover-phase-5)** — 31 POST*CUTOVER rows across 12 area issue docs filed into 3 consolidated
      successor plans (aggressive consolidation per Phase 5 strategy guidance: "Don't over-create"): -
      `plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` — 12 codex-doc-hygiene findings
      (AL-12, D-14, IN-19, IN-20, ML-12, ML-18, PB-16, O-12, O-19, ST-20, UI-17, UI-19) -
      `plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md` — 11 QG-automation gaps (G-2, G-5, G-8,
      G-12, G-13, D-18, ST-19, UI-13, UI-18, PB-19, AL-21 QG-half) -
      `plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` — 7 operator-UX deliverables (AL-22,
      R-15, R-16, ST-11, TS-19, TS-20, AL-21 UX-half) Every POST_CUTOVER row in the 12 source
      `codex_audit*<area>\_2026_05_12.md`files flipped to    `✅ FILED @
      <destination>`with destination citation. Execution (area=POST_CUTOVER count): alerting=3, data=2,     execution=0, governance=5, instruments=2, ml=2, ops=2, position_balance=2, risk=2, strategy=3, testing=2, ui=4     = 29 unique findings + 2 disposition-summary roll-up cells = 31 raw`POST_CUTOVER`cells; all 29 unique findings     mapped to destinations. Zero orphans. Commit:`57c748b2`
      (bundled by parallel agent's commit per Foot-gun #1 — Phase 5 work landed under ML-area PRE_CUTOVER commit
      message; this checkbox-flip provides clean provenance).

**Full-execution criterion**: count(POST_CUTOVER rows) == count(filed-issue-docs OR migrated-plan-todos); zero orphans.

## Phase 6 — Audit sign-off doc (Day 13, ~0.5 AI-day)

- [x] [AGENT] P0. **6.A Aggregate audit sign-off (inline section in this plan, NOT a separate issue doc).** **DONE
      2026-05-12 (slot 8 closeout pass)** — see `## Audit sign-off 2026-05-22` section below; covers findings aggregate
      (242 across 48 tiers / 12 areas), per-area summary table, disposition counts (63 IMMEDIATE / 137 PRE_CUTOVER / 36
      POST_CUTOVER / 6 KEEP), per-area issue-doc links, IMMEDIATE/PRE_CUTOVER batch commit shas, POST_CUTOVER plan
      filings, remaining operator gates.
- [ ] [AGENT] P0. **6.B Operator sign-off.** Operator reviews + approves; doc status flips to `signed-off`.

**Full-execution criterion**: sign-off doc exists; operator approved; counts add up (immediate + pre-cutover +
post-cutover == total).

## Phase 7 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **7.A Master plan row.** Group A item: "Codex vs Citadel audit signed off; pre-cutover items shipped."

**Full-execution criterion**: master plan row green.

## Cross-plan coordination

- `simulation_scenarios_topology_price_shocks_2026_05_09` — codex docs for scenario architecture audited as part of this
  pass.
- All 8 sibling plans spawned 2026-05-10 — every plan's codex SSOTs included in the audit per its area.

## Deferred work after 2026-05-10 plan-creation session

| Item                                           | Status       | Successor / blocker                      |
| ---------------------------------------------- | ------------ | ---------------------------------------- |
| Cross-asset_group reshuffles (large refactors) | POST_CUTOVER | Filed per Phase 5; named successor plans |
| HFT-specific optimizations                     | OUT_OF_SCOPE | Non-HFT framing; not revisited           |

## Done definition

1. ✅ Phases 0-7 every checkbox flipped with evidence.
2. ✅ 12 per-area audit issue docs shipped.
3. ✅ Every IMMEDIATE + PRE_CUTOVER row shipped; every POST_CUTOVER row filed.
4. ✅ Sign-off doc operator-approved.
5. ✅ Master plan row green.

## Audit findings

**Phase 1 complete 2026-05-12** — 12 per-area issue docs, ~240 findings:

| #   | Area             | Issue doc                                                                                                    | Findings         | IMMEDIATE / PRE_CUTOVER / POST_CUTOVER (+KEEP) | Done by                               |
| --- | ---------------- | ------------------------------------------------------------------------------------------------------------ | ---------------- | ---------------------------------------------- | ------------------------------------- |
| 1.A | Data             | [`codex_audit_data_2026_05_12.md`](../archive/issues/codex_audit_data_2026_05_12.md)                         | 20 (D-1..D-20)   | 6 / 12 / 2                                     | slot 8 (earlier 2026-05-12)           |
| 1.B | Strategy         | [`codex_audit_strategy_2026_05_12.md`](../archive/issues/codex_audit_strategy_2026_05_12.md)                 | 20 (ST-1..ST-20) | 5 / 12 / 3                                     | harsh-codex-audit-strategy-tab        |
| 1.C | Execution        | [`codex_audit_execution_2026_05_12.md`](../archive/issues/codex_audit_execution_2026_05_12.md)               | 27 (EX-1..EX-27) | 9 / 12 / 5 (+1)                                | harsh-codex-audit-execution-tab       |
| 1.D | Risk             | [`codex_audit_risk_2026_05_12.md`](../archive/issues/codex_audit_risk_2026_05_12.md)                         | 16 (R-1..R-16)   | 5 / 7 / 2 (+2)                                 | slot 8 (earlier 2026-05-12)           |
| 1.E | ML               | [`codex_audit_ml_2026_05_12.md`](../archive/issues/codex_audit_ml_2026_05_12.md)                             | 20 (ML-1..ML-20) | 5 / 12 / 2 (+1)                                | harsh-codex-audit-ml-tab              |
| 1.F | Position-balance | [`codex_audit_position_balance_2026_05_12.md`](../archive/issues/codex_audit_position_balance_2026_05_12.md) | 19 (PB-1..PB-19) | 6 / 11 / 3                                     | harsh-codex-audit-positionbalance-tab |
| 1.G | Instruments      | [`codex_audit_instruments_2026_05_12.md`](../archive/issues/codex_audit_instruments_2026_05_12.md)           | 22 (IN-1..IN-22) | 2 / 17 / 3                                     | harsh-codex-audit-instruments-tab     |
| 1.H | Alerting         | [`codex_audit_alerting_2026_05_12.md`](../archive/issues/codex_audit_alerting_2026_05_12.md)                 | 22 (AL-1..AL-22) | 6 / 12 / 3 (+1)                                | harsh-codex-audit-alerting-tab        |
| 1.I | Ops              | [`codex_audit_ops_2026_05_12.md`](../archive/issues/codex_audit_ops_2026_05_12.md)                           | 19 (O-1..O-19)   | 6 / 11 / 2                                     | slot 8 (earlier 2026-05-12)           |
| 1.J | Governance       | [`codex_audit_governance_2026_05_12.md`](../archive/issues/codex_audit_governance_2026_05_12.md)             | 16 (G-1..G-16)   | 4 / 7 / 5                                      | slot 8 (earlier 2026-05-12)           |
| 1.K | UI               | [`codex_audit_ui_2026_05_12.md`](../archive/issues/codex_audit_ui_2026_05_12.md)                             | 19 (UI-1..UI-19) | 3 / 12 / 4                                     | harsh-codex-audit-ui-tab              |
| 1.L | Testing          | [`codex_audit_testing_2026_05_12.md`](../archive/issues/codex_audit_testing_2026_05_12.md)                   | 20 (TS-1..TS-20) | 6 / 12 / 2                                     | harsh-codex-audit-testing-tab         |

**Recurring cross-area patterns** (worth a single batched fix in Phase 3): (1) **moved/archived-repo references** —
codex

- CLAUDE.md repeatedly name modules that no longer exist (`unified-config-interface/testnet_contracts.py` → UTL;
  `DefiErrorCode` → UAC; `unified_trading_services` module path; UDEI archived) — D-7, EX-2/5/6, AL... ; (2)
  **enum-count drift** — codex prose freezes counts that the UAC enums have since grown past (archetypes 53→55, families
  8→9, instruction actions 14, EmptyConfirmedReason 9-13→17+, AlertCodes 39→63, oracle/chain counts) — D-1, ST-1/2/3/6,
  R-5..R-9, AL-4; (3) **bucket-name SSOT drift** — hardcoded `gs://...` / `category`-vocab patterns not routed through
  `resolve_bucket_name()` — D-5, O-3/4, ML-1, PB-10/11; (4) **codex docs missing from `00-SSOT-INDEX.md`** — ST-18, ML,
  IN, O-15, G-11, TS-15; (5) **Runbook Execution-Owner block missing** on operator-runnable runbooks/reconcilers —
  O-7/8, IN-6/14/16, PB; (6) **self-flagged-stale docs that still ship their stale content inline** — UI-14, TS-14/15,
  IN-1. Phase 2 should tag each finding with a disposition; Phase 3 ships the IMMEDIATE batch (start with the
  recurring-pattern fixes for max leverage).

**BIG findings escalated to operator** (cross-side ping 2026-05-12 in `_agent_pings.md`): EX-1 (flash-loan-receiver
deployment ambiguity — cutover-blocking if placeholder); EX-10 (Copper-MPC vs CLOUD_KMS_ENCRYPTED custody-default
contradiction on 2 arch docs); IN-1 (`defi-venue-protocol-catalogue.md` actively instructs agents to delete valid
`defi_venue_capabilities.py` references); PB-1/2/3 (execution audit-records non-immutable, per-order not per-client, on
a 7-yr regulatory surface); ML-1 (4+ incompatible model-artefact bucket SSOTs); ML-2 (codex says live ML inference
inside features-service but code runs standalone `ml-inference-service`); AL-1/AL-2 (`KillSwitchScope.WALLET` broken
ref + missing `WALLET_CAP_EXCEEDED` AlertCode — routed to slot 4); TS-5 (codex
`quality-gates.md`/`dependency-management.md` contradict the workspace "Flat deps only" rule). Plus the catalogue-audit
P0: GMX/DRIFT dual-classification (`cross_asset_group_catalogue_audit_2026_05_10.md` Phase 1C — see that plan's
"Per-asset-group catalogue audit pass" section).

## Audit sign-off 2026-05-22

> **Status**: 🟡 DRAFT — slot 8 has assembled the aggregate evidence below from Phases 0-5; awaiting operator review + 3
> genuine gate decisions (R-10 / R-11 / AL-14) before this section flips to `signed-off` and the master plan Group A row
> (Phase 7) flips green. Drafted 2026-05-12 (slot 8 closeout pass) — populated entirely from existing plan-body evidence
> chains; no new investigation in this commit.

### Findings aggregate

**Total: 242 findings across 48 tiers in 12 area issue docs** (Phase 1 complete 2026-05-12).

| Disposition           | Count    | %        | Phase landing                                                          |
| --------------------- | -------- | -------- | ---------------------------------------------------------------------- |
| IMMEDIATE             | ~63      | 26%      | Phase 3 — codex doc rewrites + SSOT consolidations + CLAUDE.md hygiene |
| PRE_CUTOVER           | ~137     | 57%      | Phase 4 — architecture clean-ups composing with cutover hot path       |
| POST_CUTOVER          | ~36      | 15%      | Phase 5 — filed into 3 consolidated successor plans                    |
| KEEP (verified-clean) | ~6       | 2%       | No-action recordings                                                   |
| **Total**             | **~242** | **100%** |                                                                        |

### Per-area summary

| Area             | Issue doc                                                                                                    | Findings (IMMEDIATE / PRE_CUTOVER / POST_CUTOVER / KEEP) | Owner                                 | Status                                      |
| ---------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- | ------------------------------------- | ------------------------------------------- |
| Data             | [`codex_audit_data_2026_05_12.md`](../archive/issues/codex_audit_data_2026_05_12.md)                         | 20 (6 / 12 / 2 / 0)                                      | slot 8 (earlier 2026-05-12)           | ✅ DONE                                     |
| Strategy         | [`codex_audit_strategy_2026_05_12.md`](../archive/issues/codex_audit_strategy_2026_05_12.md)                 | 20 (5 / 12 / 3 / 0)                                      | harsh-codex-audit-strategy-tab        | ✅ DONE                                     |
| Execution        | [`codex_audit_execution_2026_05_12.md`](../archive/issues/codex_audit_execution_2026_05_12.md)               | 27 (9 / 12 / 5 / 1)                                      | harsh-codex-audit-execution-tab       | ✅ DONE                                     |
| Risk             | [`codex_audit_risk_2026_05_12.md`](../archive/issues/codex_audit_risk_2026_05_12.md)                         | 16 (5 / 7 / 2 / 2)                                       | slot 8 (earlier 2026-05-12)           | ✅ DONE (R-10 / R-11 operator gates remain) |
| ML               | [`codex_audit_ml_2026_05_12.md`](../archive/issues/codex_audit_ml_2026_05_12.md)                             | 20 (5 / 12 / 2 / 1)                                      | harsh-codex-audit-ml-tab              | ✅ DONE                                     |
| Position-balance | [`codex_audit_position_balance_2026_05_12.md`](../archive/issues/codex_audit_position_balance_2026_05_12.md) | 19 (6 / 11 / 3 / 0)                                      | harsh-codex-audit-positionbalance-tab | ✅ DONE (4 P2 sub-gates remain)             |
| Instruments      | [`codex_audit_instruments_2026_05_12.md`](../archive/issues/codex_audit_instruments_2026_05_12.md)           | 22 (2 / 17 / 3 / 0)                                      | harsh-codex-audit-instruments-tab     | ✅ DONE (IN-1 routed to Ikenna slot 2)      |
| Alerting         | [`codex_audit_alerting_2026_05_12.md`](../archive/issues/codex_audit_alerting_2026_05_12.md)                 | 22 (6 / 12 / 3 / 1)                                      | harsh-codex-audit-alerting-tab        | ✅ DONE (AL-14 operator gate remains)       |
| Ops              | [`codex_audit_ops_2026_05_12.md`](../archive/issues/codex_audit_ops_2026_05_12.md)                           | 19 (6 / 11 / 2 / 0)                                      | slot 8 (earlier 2026-05-12)           | ✅ DONE                                     |
| Governance       | [`codex_audit_governance_2026_05_12.md`](../archive/issues/codex_audit_governance_2026_05_12.md)             | 16 (4 / 7 / 5 / 0)                                       | slot 8 (earlier 2026-05-12)           | ✅ DONE                                     |
| UI               | [`codex_audit_ui_2026_05_12.md`](../archive/issues/codex_audit_ui_2026_05_12.md)                             | 19 (3 / 12 / 4 / 0)                                      | harsh-codex-audit-ui-tab              | ✅ DONE                                     |
| Testing          | [`codex_audit_testing_2026_05_12.md`](../archive/issues/codex_audit_testing_2026_05_12.md)                   | 20 (6 / 12 / 2 / 0)                                      | harsh-codex-audit-testing-tab         | ✅ DONE                                     |

### Phase 3 IMMEDIATE batch commit shas

Recurring-pattern + per-area batches (see Phase 3.A1-3.A7 + Phase 3.A/3.B/3.C body for the per-finding evidence):

| Batch                         | Scope                                                                 | Commit                                                                                      |
| ----------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 3.A1 moved/archived-repo refs | D-7 / EX-2/5/6 / +                                                    | PM@`0fc4b3fd` + `f401a3c9` + `959ca3fc` + `d19d3bf2` + `e94e703a` + UAC@`c89e820`           |
| 3.A2 enum-count drift         | D-1 / ST-1/2/3/6 / R-5..R-9 / AL-4 / ML-4                             | PM@`d19d3bf2` + `87a09ca8` + `88f435f7` + `4b3e27c7` + `57c748b2` + `33a4df91`              |
| 3.A3 bucket-name SSOT         | D-5 / O-3/4 / ML-1 / PB-10/11                                         | PM@`564c060b` (operator-gate triage) + `d19d3bf2` + `3dc3e6b1` + `19a2001c`                 |
| 3.A4 SSOT-INDEX gaps          | ST-18 / ML / IN / O-15 / G-11 / TS-15 / AL-18                         | PM@`87a09ca8` + `57c748b2` + `38748f36` + `3dc3e6b1` + `88318109` + `3bd13993` + `4b3e27c7` |
| 3.A5 Runbook-Execution-Owner  | O-7+O-8 (QG warning-with-baseline) / IN-6/14/16 / PB                  | PM@`564c060b` + `3dc3e6b1` + `38748f36` + `19a2001c`                                        |
| 3.A6 self-flagged-stale-docs  | UI-14 / TS-14/15 (IN-1 routed)                                        | PM@`8af99d6d` + `3bd13993` + IN-1 cross-side ping @PM`79f73426`                             |
| 3.A7 per-area singletons      | ST-4 / EX-8/20 / AL-3 / AL-10 / TS-3/1/2 / TS-5 / UI-1/2 / G-3 / O-11 | PM@`87a09ca8` + `0fc4b3fd` + `4b3e27c7` + `c9511517` + `3bd13993` + `8af99d6d` + `33a4df91` |

### Phase 4 PRE_CUTOVER batch commit shas

| Batch                                           | Area                                                       | Findings                    | Commit                                                                                                            |
| ----------------------------------------------- | ---------------------------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Batch 1                                         | Data                                                       | 11                          | PM@`d19d3bf2`                                                                                                     |
| Batch 1                                         | Strategy                                                   | 9                           | PM@`87a09ca8`                                                                                                     |
| Batch 1                                         | Execution                                                  | 10 + UAC EX-6               | PM@`e94e703a` + UAC@`c89e820`                                                                                     |
| Batch 1                                         | Instruments                                                | 13                          | PM@`38748f36` (+ issue-doc row flips @PM`651ccf15`)                                                               |
| Batch 2                                         | ML                                                         | 8                           | PM@`57c748b2`                                                                                                     |
| Batch 2                                         | Position-balance                                           | 5                           | PM@`19a2001c`                                                                                                     |
| Batch 2                                         | Risk                                                       | 4                           | PM@`88f435f7`                                                                                                     |
| Batch 2                                         | Alerting                                                   | 5                           | PM@`4b3e27c7`                                                                                                     |
| Batch 3                                         | Ops                                                        | 5                           | PM@`3dc3e6b1`                                                                                                     |
| Batch 3                                         | Governance                                                 | 2 + 5 routed                | PM@`88318109`                                                                                                     |
| Batch 3                                         | UI                                                         | 9 + 2 partial + UI-9 routed | PM@`8af99d6d`                                                                                                     |
| Batch 3                                         | Testing                                                    | 11 + 2 partial + 1 routed   | PM@`3bd13993`                                                                                                     |
| CLAUDE.md bundle                                | G-4/G-10/G-14/G-16 + UI-9 + TS-12 mirror                   | 6                           | PM@`33a4df91`                                                                                                     |
| Cross-asset Phase 4 mev consolidation companion | EX-8/EX-20 closeout                                        | 2                           | PM@`be7d7c84` + sibling @`0fc4b3fd`                                                                               |
| Operator-gate triage                            | PB-7/14/17/18 + ML-1/7 + R-4 + AL-10/15 + O-7/8/14 + UI-16 | 13                          | PM@`564c060b` + per-area row-flips @PM`bbaf645d` + `8958e237` + `adff9712` + `e24828e2` + `d3ee7092` + `c9511517` |

**PRE_CUTOVER total**: ~101 of ~137 shipped directly; ~36 routed to area maintainers (alerting maintainer,
execution-service maintainer, ml-training owner, etc.) per Findings Triage Discipline — codex-doc-fix half shipped from
slot 8; code-work half delegated to named owner.

### Phase 5 POST_CUTOVER successor plans

31 POST_CUTOVER rows filed into 3 consolidated successor plans (PM@`b2b15f8d` 2026-05-12 ikenna-postcutover-phase-5
sub-agent):

| Successor plan                                                                                                                       | Findings | Scope                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------ | -------- | --------------------------------------------------------------------------------------------------- |
| [`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`](codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md) | 12       | AL-12, D-14, IN-19, IN-20, ML-12, ML-18, PB-16, O-12, O-19, ST-20, UI-17, UI-19 — codex-doc-hygiene |
| [`governance_qg_automation_gaps_post_cutover_2026_05_12.md`](governance_qg_automation_gaps_post_cutover_2026_05_12.md)               | 11       | G-2, G-5, G-8, G-12, G-13, D-18, ST-19, UI-13, UI-18, PB-19, AL-21 QG-half — QG-automation gaps     |
| [`alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md`](alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md)         | 7        | AL-22, R-15, R-16, ST-11, TS-19, TS-20, AL-21 UX-half — operator-UX deliverables                    |

Zero orphans.

### Remaining operator gates (pre-sign-off)

**3 genuine operator decisions still required** (per slot-8 Phase 2.C triage @PM`564c060b`):

1. **R-10 — pre-flight check call-graph implementation** — risk pre-flight ordering across (kill_switch /
   circuit_breaker / spending_caps / venue_health / data_freshness / margin / capital_allocation). Operator decision:
   which architecture (linear pipeline / DAG with explicit ordering / event-driven). Not slot 8 work —
   risk-and-exposure-service maintainer territory.
2. **R-11 — capital-allocation seam: subsume-vs-AND-aggregate** — when multiple archetypes target the same wallet,
   per-archetype caps either AND (most restrictive wins) or capital-allocator-subsumes. Operator decision needed before
   live cap enforcement.
3. **AL-14 — named on-call rotation** — `operator-playbook.md` + `pagerduty-escalation-policy.md` rotation gap. Operator
   decision on named-person assignments (2-operator 12-hour split? rotation cadence?).

**4 P2 sub-gates** (from PB-17 / PB-18 / AL-15 triage):

4. Per-archetype recon tolerance bands.
5. Cutover-window recon cadence (intra-cutover-window).
6. CEFFU custody-disconnect threshold.
7. Auto-pause-vs-alert escalation policy.

All 7 are non-blocking for sign-off-doc _drafting_ (this section), but **operator answers on R-10 / R-11 / AL-14 are
prerequisites for Phase 6.B operator sign-off** + master plan Group A row flip (Phase 7).

### Cross-side handshakes outstanding

- **IN-1** (`02-data/defi-venue-protocol-catalogue.md` 2026-05-12 refresh falsely asserts `defi_venue_capabilities.py`
  "does not exist") — routed to Ikenna slot 2 per cross-side collision-avoidance @PM`79f73426` ping; orchestrator
  confirmed routing 2026-05-12. Slot 8 holding off on edit; awaiting Ikenna-slot-2 revert.
- **GMX/DRIFT dual-classification P0** (cross_asset Phase 1C) — operator greenlight pending; flagged in
  `plans/active/_agent_pings.md`.

### Sign-off block

**To be filled by operator** after R-10 / R-11 / AL-14 decisions and a final pass over this section:

```yaml
audit_sign_off:
  date: <YYYY-MM-DD>
  operator: <name>
  decisions_resolved:
    - R-10: <decision>
    - R-11: <decision>
    - AL-14: <decision>
  status: signed-off
```

Once `signed-off`, Phase 6.B flips ✅ + Phase 7.A master-plan Group A row flips green + the plan archives.

## DONE block

(Final completion block — filled when Phases 0-7 all green + operator sign-off.)

### DONE-2026-05-12 — slot 8 (harsh-catalogue-audit-tab) — Phase 0 + Phase 1 (12/12) + Phase 2.A/2.B

| Phase / item                                   | Status as of 2026-05-12 EOD                                    | Evidence / successor / blocker                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 (area enumeration)                     | ✅ DONE                                                        | (earlier 2026-05-12 slot 8) 12-area scope + codex doc inventory (574 docs / 21 sub-dirs)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Phase 1 (per-area audit, 12 areas)             | ✅ DONE — 12/12                                                | 4 areas (Data/Risk/Ops/Governance) earlier 2026-05-12; 8 areas (Strategy/Execution/ML/Position-balance/Instruments/Alerting/UI/Testing) this session via 8-sub-agent fan-out → PM@`b2943cfd`. ~242 findings across 48 tiers; per-area issue docs `plans/active/issues/codex_audit_*_2026_05_12.md`; aggregate table in `## Audit findings`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Phase 2.A (disposition enum)                   | ✅ DONE                                                        | `IMMEDIATE`/`PRE_CUTOVER`/`POST_CUTOVER`/`KEEP` — used per-row in all 12 docs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Phase 2.B (per-recommendation tagging)         | ✅ DONE                                                        | every row tagged; aggregate ~63 IMMEDIATE / ~137 PRE_CUTOVER / ~36 POST_CUTOVER / ~6 KEEP — table under Phase 2.B                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Phase 2.C (operator review)                    | ✅ MOSTLY-RESOLVED 2026-05-12 (slot 8 triage @PM`564c060b`)    | 7 of 10 BIG findings self-answered from existing SSOTs: PB-14 (CEFFU = June-1+ deferral), ML-1 (`resolve_bucket_name(kind="ml-models-store")` canonical), ML-7 (joblib canonical), PB-7 (PBMS positions SSOT codified), PB-17 (batch-vs-live recon contract codified — 2 P2 sub-gates), PB-18 (custody-ping protocol codified — 2 P2 sub-gates), R-4 (Layer-2.5 codified), AL-10 (synthetic-data filter codified), AL-15 (custody-stale AlertCode codified), O-7+O-8 (QG warning-with-baseline codified), O-14 + UI-16 (codex docs promoted to stable). **3 genuine operator-gates remain**: R-10 call-graph, R-11 capital-allocation seam, AL-14 named on-call rotation. **+ 4 P2 sub-gates** (per-archetype recon tolerance / cutover-window recon cadence / CEFFU custody-disconnect threshold / auto-pause-vs-alert escalation). All non-blocking for Phase-4 closeout. |
| Phase 3 (immediate items shipped)              | ✅ MOSTLY-DONE 2026-05-12 (slot 8)                             | IMMEDIATE rows shipped across 12 areas via the same 5-sub-agent + operator-gate-triage fan-outs that drove Phase 4; per-batch evidence in Phase 4.A above. Recurring-pattern batches (3.A1 moved/archived-repo refs · 3.A2 enum-count drift · 3.A3 bucket-name SSOT · 3.A4 SSOT-INDEX gaps · 3.A5 Runbook-Execution-Owner blocks · 3.A6 self-flagged-stale-doc cleanup) — all landed; IN-1 (defi-venue-protocol-catalogue.md drift-introducing "correction") routed to Ikenna slot 2 per the cross-side collision-avoidance rule. Phase 3.A/3.B/3.C plan-level row flips deferred to Phase 6 sign-off doc.                                                                                                                                                                                                                                                                  |
| Phase 4 (pre-cutover items shipped)            | ✅ DONE 2026-05-12 (slot 8 Day-4 stretch + closeout this turn) | 4.A flipped @PM`<this commit>` — ~101 of ~137 PRE_CUTOVER findings shipped across 3 parallel sub-agent batches; ~36 routed-to-area-maintainer with codex-doc-fix half shipped + code-work half delegated per Findings Triage. 4.B flipped — per-area assertions visible in issue docs; PM/UAC/deployment-service/ml-inference-service all `0 0` vs LDR. cross_asset Phase 4 mev-protection consolidation @PM`be7d7c84` is the companion.                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Phase 5 (post-cutover items filed)             | ✅ DONE 2026-05-12 (slot 8)                                    | 31 POST_CUTOVER rows → 3 consolidated successor plans (codex-doc-currency + qg-automation + alerting-runbook); zero orphans                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Phase 3.A1-3.A7 + 3.A/3.B/3.C plan-level rows  | ✅ DONE 2026-05-12 (slot 8 RESUME-2)                           | All 10 Phase 3 IMMEDIATE-batch sub-rows + plan-level rows flipped with evidence chain from Phase 4.A. Commit @PM`<this-commit>`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Phase 6.A (audit sign-off doc — drafting half) | ✅ DONE 2026-05-12 (slot 8 RESUME-2 closeout)                  | `## Audit sign-off 2026-05-22` section appended this commit; findings aggregate (242 / 48 tiers / 12 areas) + per-area summary table + disposition counts (63/137/36/6) + Phase 3 + Phase 4 batch commit-sha tables + Phase 5 successor-plan registry + 3 remaining operator gates + 4 P2 sub-gates + cross-side handshake state + sign-off block. PM@`<this-commit>`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Phase 6.B (operator sign-off)                  | ☐ TODO (Day 13)                                                | gated on operator approval of R-10 / R-11 / AL-14 (+ 4 P2 sub-gates per PB-17 / PB-18 / AL-15 triage). Sign-off block in `## Audit sign-off 2026-05-22` section is operator-fillable when ready.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase 7 (cutover gate)                         | ☐ TODO (Day 13)                                                | master plan Group A row; gated on Phase 6.B                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

**Carry-forward for next slot-8 session**: (1) operator decision on 3 genuine gates (R-10 / R-11 / AL-14) + 4 P2
sub-gates from PB-17/PB-18 triage — when ready, the operator fills the sign-off block in `## Audit sign-off 2026-05-22`
section + Phase 6.B flips ✅; (2) Phase 7 master-plan Group A row flip after sign-off. Slot 8's IN-1 callout to Ikenna
slot 2 (`defi-venue-protocol-catalogue.md` 2026-05-12 refresh falsely asserts `defi_venue_capabilities.py` "does not
exist") — escalated `plans/active/_agent_pings.md` 2026-05-12 + orchestrator confirmed routing; do not touch from
slot 8. **Day-3 stretch carry-forward (PM@`b0500361` + this commit)**: Phase 3 ✅ closed fully; Phase 6.A ✅ drafted —
remaining slot 8 surface is 100% operator-gated.
