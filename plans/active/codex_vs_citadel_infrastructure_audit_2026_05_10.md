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
      [`plans/active/issues/codex_audit_data_2026_05_12.md`](issues/codex_audit_data_2026_05_12.md) ships 20 findings (6
      IMMEDIATE + 12 PRE_CUTOVER + 2 POST_CUTOVER) across 6 tiers with per-row file:line evidence + suggested
      disposition + owner. Highest-blast-radius IMMEDIATE items: D-1 (reason taxonomy lag — UAC `EmptyConfirmedReason`
      enum has 17+ members but codex/CLAUDE.md cite 9-13), D-5 (`bucket-naming-and-config.md` fully superseded by
      `resolve_bucket_name(...)`), D-7 (`unified_trading_services` non-existent module references in
      `schema-governance.md` + `README.md`).
- [x] [AGENT] P0. **1.B Strategy area.** Archetype canonicalisation; strategy-service co-location; signal-leasing;
      promote workflow. **DONE 2026-05-12 harsh-codex-audit-strategy-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_strategy_2026_05_12.md`](issues/codex_audit_strategy_2026_05_12.md) ships 20
      findings (5 IMMEDIATE + 12 PRE_CUTOVER + 3 POST_CUTOVER incl. ST-15 KEEP) across 4 tiers with per-row file:line
      evidence + disposition + owner. Critical: ST-1/2/3/6 archetype-count drift (codex says "53 archetypes / 8
      families / 18 engines" but UAC enums = `StrategyArchetype`=55 / `StrategyFamily`=9 / `InstructionActionV2`=14;
      `master_to_live_defi_2026_05_23.md:150` carries the stale count → review-blocking master-plan row); ST-4
      (`archetype-paper-readiness.md` names the wrong source file — points at the 8 PortfolioAllocator engines, not
      the 55 archetypes); ST-18 (≥5 Strategy SSOT docs absent from `codex/00-SSOT-INDEX.md`). Verified-clean: batch=live
      invariant (GroupBRunner reuses `V2EngineOrchestrator`), engine has zero adapter imports, signal_broadcast sub-package
      matches the codex implementation map. No BIG-finding-level drift.
- [x] [AGENT] P0. **1.C Execution area.** Matching engine hooks; live-batch parity; DeFi connectors; order-state
      machine; flash-loan receiver. **DONE 2026-05-12 harsh-codex-audit-execution-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_execution_2026_05_12.md`](issues/codex_audit_execution_2026_05_12.md) ships 27
      findings (9 IMMEDIATE + 12 PRE_CUTOVER + 5 POST_CUTOVER + 1 KEEP) across 4 tiers with per-row file:line evidence +
      disposition + owner. **BIG findings**: EX-1 (`flash-loan-receiver.md` says mainnet Aave receiver "Not yet deployed"
      but `testnet_contracts.yaml` chain_id 1 already registers `flash_loan_receiver: 0x42c005e2Bc545a49B50Fee3E76B8558348CAAb4c`
      — placeholder vs real? `AAVEConnector.connect()` fail-loud `eth_getCode` check fires at cutover if placeholder);
      EX-10 (`tenderly-execution-provider.md` + `execution-modes-and-chain-resolution.md` name Copper MPC as the live
      custody backend, but `interface-credential-convention.md` (updated 2026-05-12) says the May-23 cutover default is
      `CLOUD_KMS_ENCRYPTED` — Copper is the June-1 flip target). Also EX-8/EX-20 (`defi-execution-overview.md` § "MEV
      Protection Framework" inverts the L2/mainnet provider selection vs canonical `mev-protection.md`; no supersession
      banner); EX-2/5/6 (codex + CLAUDE.md name moved/archived repos — `unified-config-interface/testnet_contracts.py`
      doesn't exist (it's in UTL), `DefiErrorCode` moved to UAC, UDEI archived — same class as Data-area D-7).
- [x] [AGENT] P0. **1.D Risk area.** Circuit breakers; kill-switch; pre-flight checks; per-archetype limits; wallet-tier
      kill-switch + spending caps. **DONE 2026-05-12 ikenna-codex-audit-risk-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_risk_2026_05_12.md`](issues/codex_audit_risk_2026_05_12.md) ships 16 findings (5
      IMMEDIATE + 7 PRE_CUTOVER + 2 POST_CUTOVER + 2 KEEP) with per-row file:line evidence + suggested disposition +
      owner. Tier 1 (today's slot 4 + slot 8 wallet-tier shipments — codex catch-up gap): 4 findings (R-1..R-4); Tier 2
      (UAC ↔ codex enum-count drift): 5 findings (R-5..R-9); Tier 3 (pre-flight chain sequencing): 3 findings
      (R-10..R-12); Tier 4 (operator-UX + autonomous-recovery): 4 findings (R-13..R-16). **Critical operator-attention
      items**: R-5 broken `KillSwitchScope.WALLET` reference in `kill_switch.py:67-72` (enum member doesn't exist in
      `alerting/codes.py`); R-6 missing `WALLET_CAP_EXCEEDED` AlertCode promised by SpendingCaps docstring (alerting
      surface degraded for wallet-tier risk).
- [x] [AGENT] P0. **1.E ML area.** Lifecycle; training/inference colocated; cache-delta hot reload; lookahead-bias.
      **DONE 2026-05-12 harsh-codex-audit-ml-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_ml_2026_05_12.md`](issues/codex_audit_ml_2026_05_12.md) ships 20 findings (5
      IMMEDIATE + 12 PRE_CUTOVER + 2 POST_CUTOVER + 1 KEEP) across 4 tiers. **BIG**: ML-1 (4+ mutually-incompatible
      model-artefact bucket/path SSOTs in codex + a 5th in code — `ml-models-store-{pid}` / `ml-training-artifacts-{pid}`
      / `ml-predictions-{category}-...` — none routed through `resolve_bucket_name()` per QG STEP 5.69; live-ML cutover
      path); ML-2 (`cefi-ml-live-serving.md` says live ML inference runs *inside* features-service "no parallel ML
      inference path", but code runs a standalone `ml-inference-service` and the v2 archetype docs agree with the code —
      one side is dead); ML-5/ML-4 (the 4 ML AlertCodes + the PSI/KL model-drift rule in `ml-alerting-rules.md` were
      never wired — alerting-service has 0 of 4; `drift_monitor.py` uses an accuracy-drop trigger emitting
      `MODEL_RETUNE_REQUESTED` instead). Also: parquet "ML manifest" doesn't exist (code uses `model_registry/manifest.json`);
      `model_loader.py` docstring says ONNX-only/"no joblib" but UTL `ModelRegistry` joblib-loads; no codex doc applies
      lookahead-bias `available_at` discipline to ML *training*; no QG step bans raw `pickle` (one test uses it); zero ML
      doc entries in `00-SSOT-INDEX.md`.
- [x] [AGENT] P0. **1.F Position-balance area.** Per-client lineage; reconciliation; custody pings. **DONE 2026-05-12
      harsh-codex-audit-positionbalance-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_position_balance_2026_05_12.md`](issues/codex_audit_position_balance_2026_05_12.md)
      ships 19 findings (6 IMMEDIATE + 11 PRE_CUTOVER + 3 POST_CUTOVER; a few split doc-fix vs impl halves) across 4
      tiers. **BIG**: PB-1/2/3 (execution audit-records — codex `07-security/audit-logging.md` says append-only JSONL at
      `audit/{client_id}/{date}/{event_type}/` with storage-layer immutability; reality `execution-service/.../utils/audit_log.py:60`
      writes one `.json` blob per event via `upload_bytes` full-PUT, no Object-Versioning/Retention-Lock, ignores
      `EXECUTION_AUDIT.gcs_path_template`, AND `order_adapter.py:141/195`+`oms.py:115` pass `client_order_id`/`order_id`/`operation_id`
      into the `client_id` path slot → "per-client lineage" is per-order for 3 of 5 event types — 7-yr regulatory surface).
      Also PB-4 (strategy audit-bucket persistence unwired — `STRATEGY_INSTRUCTION`/`SIGNAL_GENERATED` only `log_event()`'d
      to the bus, hardcoded `"client": "system"`); PB-13/PB-5 (`master_to_live_defi_2026_05_23.md:140` still cross-refs
      deleted `copper-custody-integration.md`+`ceffu-custody-integration.md`; `paper-vs-live-execution-seam.md` describes
      3-way recon as present-tense but it's unimplemented — no `paper_live_recon.py` stage); PB-7/17/18 (no codex doc names
      PBMS as the positions SSOT or covers the batch-vs-live recon contract / custody-ping loop).
- [x] [AGENT] P0. **1.G Instruments area.** Catalogue completeness; reference-data adapters; per-asset_group coverage.
      **DONE 2026-05-12 harsh-codex-audit-instruments-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_instruments_2026_05_12.md`](issues/codex_audit_instruments_2026_05_12.md) ships 22
      findings (2 IMMEDIATE + 17 PRE_CUTOVER + 3 POST_CUTOVER) across 4 tiers; cross-references the 5 per-asset_group
      `catalogue_audit_{ag}_2026_05_12.md` issue docs (elevated DF-1/2/3/6/8/10/11/14/15/16/18/19/20, CF-1/2/3/4/9/10/12,
      TF-4/5/6, SP-1/2/3/6/10, PR-1/6/7 → IN-1/2/3/4/9/10/11/12/13/15/22). **BIG**: IN-1 (`defi-venue-protocol-catalogue.md`'s
      2026-05-12 "refresh" banner falsely claims `defi_venue_capabilities.py` "does not exist" + tells agents to delete
      references to it — the file DOES exist (178 LOC, holds `DEFI_VENUE_DATA_TYPE_CAPABILITIES`, the per-(venue,data_type)
      coverage-window SSOT) and `catalogue_audit_defi` actively uses it; the codex "correction" is itself drift-introducing —
      an agent following it deletes valid SSOT pointers). Also IN-2 (`venue-availability.md` names `VenueMapping`/`VenueEntry`
      as "primary SSOT" but the real per-asset_group catalogue is `VENUES_BY_ASSET_GROUP`+`ALL_DEFI_VENUES`); IN-6/14/16
      (phantom-audit reconciler + tier-promotion + 40+ instruments-service remediation scripts lack the Runbook
      Execution-Owner block — stale cadence = live correctness risk given GHOST/ORPHAN venues found in every asset_group);
      IN-22 (proposed QG ratchet to statically catch the GHOST-venue class).
- [x] [AGENT] P0. **1.H Alerting area.** Live rules; synthetic filter; severity tiers; on-call routing. **DONE 2026-05-12
      harsh-codex-audit-alerting-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_alerting_2026_05_12.md`](issues/codex_audit_alerting_2026_05_12.md) ships 22
      findings (6 IMMEDIATE + 12 PRE_CUTOVER + 3 POST_CUTOVER + 1 KEEP) across 4 tiers; cross-refs Risk-area R-5/R-6.
      **BIG**: AL-1 (`KillSwitchScope.WALLET` broken ref — UAC internally inconsistent on a same-day slot-4 shipment);
      AL-2/R-6 (`WALLET_CAP_EXCEEDED` AlertCode promised by `wallet_config.py:114-117` SpendingCaps docstring doesn't
      exist in `alerting/codes.py` — spending-caps ship May-23 with a silent typed-alert hole); AL-3 (`03-observability/alerting.md`
      embeds a stale 21-rule `ROUTING_RULES` block — actual routing is UAC-driven via 56-entry `LIVE_ALERT_RULES`; second
      SSOT); AL-4 (codex says "39 AlertCodes" — actual ~63); AL-6 (Slack-deprecation contradiction across 3 codex docs +
      active `slack_dispatcher.py`/`claude_slack_agent.py` + ML routing rules using `SLACK`); AL-10 (no synthetic/test-data
      alert filter exists anywhere — a `CLOUD_MOCK_MODE=true`/staging service emitting `KILL_SWITCH_*` in live mode pages
      on-call; the `rehearsal=true` tag is documented but never implemented); AL-16 (`operator-playbook.md` +
      `rehearsal-procedure.md` + `live-deployment-monitoring.md` all still 2026-05-07 PLANNED stubs — on-call has no
      per-code response steps for ~12 of ~63 AlertCodes). AL-1/AL-2 routed to slot 4 (collision avoidance), not fixed here.
- [x] [AGENT] P0. **1.I Ops area.** VM tarball; launcher SSOT; zombie watchdog; concurrent-write CAS. **DONE 2026-05-12 ikenna-codex-audit-ops-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_ops_2026_05_12.md`](issues/codex_audit_ops_2026_05_12.md)
      ships 19 findings (6 IMMEDIATE + 11 PRE_CUTOVER + 2 POST_CUTOVER) with per-row file:line evidence + suggested
      disposition + owner. Tier 1 (codex doc vs implementation drift): 6 findings (O-1..O-6); Tier 2 (operational
      governance gaps): 6 findings (O-7..O-12); Tier 3 (stale / planned-stub / currency): 5 findings (O-13..O-17);
      Tier 4 (additions worth shipping): 2 findings (O-18..O-19). **Critical operator-attention items**: O-1 — 20 of
      76 launchers under `deployment-service/scripts/vm/launch-*.sh` skip the canonical
      `setup-data-pipeline-vm.sh` setup script (`MANIFEST_PER_VM_SHARDS` / `VM_SHUTDOWN_ON_COMPLETION` /
      `vm-exec-with-gcs-tee.sh` invariants potentially missing across multiple cutover-critical scripts —
      `vm-tarball-deployment.md` Invariant #1 claims "every launcher" uses canonical setup script); O-3 / O-4 stale
      bucket-name patterns in `disaster-recovery.md` + `README.md` contradict the (b+) bucket-name SSOT; O-7 / O-8
      no QG enforcement that new `VM_PREFIX_TO_BUCKET` entries trigger watchdog relaunch + new launchers register in
      Deploy-Missing UI `_SERVICE_LAUNCHER_SCRIPTS`; O-11 CLAUDE.md `PREK_HOME` vs `PREK_CACHE_DIR` 3-way drift.
- [x] [AGENT] P0. **1.J Governance area.** CLAUDE.md HARD RULES self-consistency; SUB_AGENT_MANDATORY_RULES symlink;
      plan-format discipline; daily work-split. **DONE 2026-05-12 slot 8 Day-4 stretch** — issue doc
      [`plans/active/issues/codex_audit_governance_2026_05_12.md`](issues/codex_audit_governance_2026_05_12.md) ships 16
      findings (4 IMMEDIATE + 7 PRE_CUTOVER + 5 POST_CUTOVER) with per-row file:line evidence + suggested disposition +
      owner. Tier 1 (CLAUDE.md self-consistency): 6 findings (G-1..G-6); Tier 2 (plan-format / work-split discipline): 4
      findings (G-7..G-10); Tier 3 (codex/13 + codex/11 currency): 3 findings (G-11..G-13); Tier 4 (additions worth
      shipping): 3 findings (G-14..G-16). Highlights: G-3 `--no-verify` Foot-gun #4 vs Bash-tool contradiction; G-9
      cycle-cadence ceiling underdocumented (~250-400 cal AI-days vs ~100-150 stated); G-14 slot-8 master-plan-edit
      precedence rule needed; G-16 cross-side ping-ledger commit-sha entry retention rule needed.
- [x] [AGENT] P0. **1.K UI area.** Tier-based startup; mock vs real; firebase-local; deployment-ui surfaces. **DONE
      2026-05-12 harsh-codex-audit-ui-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_ui_2026_05_12.md`](issues/codex_audit_ui_2026_05_12.md) ships 19 findings (3
      IMMEDIATE + 12 PRE_CUTOVER + 4 POST_CUTOVER) across 4 tiers. Critical: UI-1 (`codex/08-workflows/local-dev.md`
      still prints the dead 5173-5183 port registry / 11 legacy split UIs verbatim below its own "obsolete" banner —
      only `deployment-ui:5183` + `unified-trading-system-ui:3000/3100` survive per `ui-api-mapping.json`); UI-2
      (CLAUDE.md "check existing 13 UIs first" is a Feb-2026 artefact — `workspace-manifest.json` has 3 UI repos, active
      surface is 2; several plans still cite "13 UIs"); UI-14 (`local-dev.md` is self-flagged `status: PARTIALLY-STALE`
      yet ships its stale frontend sections inline). BIG-ish: UI-7 (three+ overlapping SSOTs forming around the
      deployment-ui Data Status surface — `data-status-drilldown.md` + `deployment-ui-architecture.md` + the *fourth*
      `codex/03-deployment/data-status-ui-surface.md` that `cross_asset_group_catalogue_audit` Phase 2F is slated to
      create — that dir doesn't exist yet); UI-8 (`runtime-tiers-and-deployment.md` internal contradiction —
      `user-management-api` listed as archived AND as a live Cloud Run service); UI-16 (`deployment-ui-architecture.md`
      still `status: stub` — if the 6-tab refactor hasn't shipped, the May-23 master plan relies on a UI surface that may
      still be the old 7-peer-tab layout).
- [x] [AGENT] P0. **1.L Testing area.** Emulator coverage; mock fixtures; integration tiers; cassette parity. **DONE
      2026-05-12 harsh-codex-audit-testing-tab (slot 8 sub-agent)** — issue doc
      [`plans/active/issues/codex_audit_testing_2026_05_12.md`](issues/codex_audit_testing_2026_05_12.md) ships 20
      findings (6 IMMEDIATE + 12 PRE_CUTOVER + 2 POST_CUTOVER) across 4 tiers. **BIG**: TS-5 (`quality-gates.md` +
      `dependency-management.md` still teach `[project.optional-dependencies] dev` / `uv pip install -e ".[dev]"` —
      directly contradicts the workspace "Flat deps only" rule + actual pyprojects; also surfaces in Governance/Coding-Standards
      slices). Also TS-3/1/2 (the VCR docs are internally contradictory + point at deleted/wrong paths — `vcr-cassette-pattern.md`
      says "run the recording script in unified-api-contracts" but `vcr-cassette-ownership.md` says "AC ships no recording
      script" (and it doesn't); `network_block_plugin.py` lives in `unified-api-contracts/.../testing/` not PM `scripts/dev/`,
      a wrong path repeated in 3 codex docs); TS-15/14 (no real testing-infrastructure codex SSOT — `06-coding-standards/testing.md`
      is a 1-line stub yet SSOT-INDEX points at it; emulator/mock table duplicated verbatim in `README.md`; coverage targets
      have 3 competing SSOTs).

**Full-execution criterion**: 12 issue docs in `plans/active/issues/codex_audit_*_2026_05_12.md` (note: `_2026_05_12`,
not `_2026_05_10` — the original date suffix in this criterion was stale), each with KEEP / LIFT / CONSOLIDATE / DELETE
/ ADD recommendation table + per-row evidence (file:line citations). **STATUS 2026-05-12: ✅ 12/12 areas complete** —
Data (D, 20) / Strategy (ST, 20) / Execution (EX, 27) / Risk (R, 16) / ML (ML, 20) / Position-balance (PB, 19) /
Instruments (IN, 22) / Alerting (AL, 22) / Ops (O, 19) / Governance (G, 16) / UI (UI, 19) / Testing (TS, 20). **~240
findings total** across 48 tiers. Phase 1 → DONE; Phase 2 (disposition tagging + operator review) is next.

## Phase 2 — Per-recommendation disposition (Day 6, ~1 AI-day)

- [ ] [AGENT] P0. **2.A Disposition closed enum.** `IMMEDIATE` (codex doc rewrite / SSOT consolidation that ships in
      days) / `PRE_CUTOVER` (architecture clean-up that composes with cutover hot path) / `POST_CUTOVER` (large
      refactor, cross-quarter scope).
- [ ] [AGENT] P0. **2.B Per-recommendation tagging.** Every row in every audit issue doc gets a disposition + a 1-line
      reason + an owner.
- [ ] [AGENT] P0. **2.C Operator review.** Operator approves dispositions; disagreements surface as P0 ping.

**Full-execution criterion**: every audit-issue-doc row has a disposition; operator has signed off via Q&A or chat.

## Phase 3 — Immediate items shipped (Days 6-9, ~3 AI-days, parallel)

- [ ] [AGENT] P0. **3.A Codex doc rewrites.** Every IMMEDIATE-tagged codex doc gets the recommended rewrite. PRs shipped
      per "Commit + Push + Flip" cadence.
- [ ] [AGENT] P0. **3.B SSOT consolidations.** Duplicate SSOTs deleted; cross-references rewritten; QG steps added if a
      banned-pattern surface emerges.
- [ ] [AGENT] P0. **3.C CLAUDE.md hygiene.** Dead rules removed; supersession banners added; cross-references resolved.

**Full-execution criterion**: every IMMEDIATE row flipped `[x]` with `<commit-sha>` evidence; codex-vs-code drift count
drops to 0 on IMMEDIATE rows.

## Phase 4 — Pre-cutover items shipped (Days 9-12, ~3 AI-days, parallel)

- [ ] [AGENT] P0. **4.A Architecture clean-ups on cutover path.** Each PRE_CUTOVER item gets shipped as a separate
      commit (or folded into an active plan if scope-aligned).
- [ ] [AGENT] P0. **4.B Per-area success criterion.** Each area has a pre-cutover-readiness assertion; QG green per
      affected repo.

**Full-execution criterion**: every PRE_CUTOVER row flipped `[x]`; affected repos QG + remote CI green.

## Phase 5 — Post-cutover items filed as plans (Day 12, ~1 AI-day)

- [ ] [AGENT] P0. **5.A Per-POST_CUTOVER row → plan or issue doc.** Every POST*CUTOVER recommendation gets a
      `plans/active/issues/<slug>*<post_cutover_date>.md`issue doc OR is folded into an existing plan with a`**MIGRATED
      FROM:** codex_vs_citadel_audit_2026_05_10` provenance line. No orphan recommendations.

**Full-execution criterion**: count(POST_CUTOVER rows) == count(filed-issue-docs OR migrated-plan-todos); zero orphans.

## Phase 6 — Audit sign-off doc (Day 13, ~0.5 AI-day)

- [ ] [AGENT] P0. **6.A Aggregate audit sign-off (inline section in this plan, NOT a separate issue doc).** Append a
      `## Audit sign-off 2026-05-22` section to this plan body with findings aggregate, per-area summary, disposition
      counts, links to per-area issue docs + immediate/pre-cutover commit shas + post-cutover plan filings.
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

| # | Area | Issue doc | Findings | IMMEDIATE / PRE_CUTOVER / POST_CUTOVER (+KEEP) | Done by |
|---|------|-----------|----------|------------------------------------------------|---------|
| 1.A | Data | [`codex_audit_data_2026_05_12.md`](issues/codex_audit_data_2026_05_12.md) | 20 (D-1..D-20) | 6 / 12 / 2 | slot 8 (earlier 2026-05-12) |
| 1.B | Strategy | [`codex_audit_strategy_2026_05_12.md`](issues/codex_audit_strategy_2026_05_12.md) | 20 (ST-1..ST-20) | 5 / 12 / 3 | harsh-codex-audit-strategy-tab |
| 1.C | Execution | [`codex_audit_execution_2026_05_12.md`](issues/codex_audit_execution_2026_05_12.md) | 27 (EX-1..EX-27) | 9 / 12 / 5 (+1) | harsh-codex-audit-execution-tab |
| 1.D | Risk | [`codex_audit_risk_2026_05_12.md`](issues/codex_audit_risk_2026_05_12.md) | 16 (R-1..R-16) | 5 / 7 / 2 (+2) | slot 8 (earlier 2026-05-12) |
| 1.E | ML | [`codex_audit_ml_2026_05_12.md`](issues/codex_audit_ml_2026_05_12.md) | 20 (ML-1..ML-20) | 5 / 12 / 2 (+1) | harsh-codex-audit-ml-tab |
| 1.F | Position-balance | [`codex_audit_position_balance_2026_05_12.md`](issues/codex_audit_position_balance_2026_05_12.md) | 19 (PB-1..PB-19) | 6 / 11 / 3 | harsh-codex-audit-positionbalance-tab |
| 1.G | Instruments | [`codex_audit_instruments_2026_05_12.md`](issues/codex_audit_instruments_2026_05_12.md) | 22 (IN-1..IN-22) | 2 / 17 / 3 | harsh-codex-audit-instruments-tab |
| 1.H | Alerting | [`codex_audit_alerting_2026_05_12.md`](issues/codex_audit_alerting_2026_05_12.md) | 22 (AL-1..AL-22) | 6 / 12 / 3 (+1) | harsh-codex-audit-alerting-tab |
| 1.I | Ops | [`codex_audit_ops_2026_05_12.md`](issues/codex_audit_ops_2026_05_12.md) | 19 (O-1..O-19) | 6 / 11 / 2 | slot 8 (earlier 2026-05-12) |
| 1.J | Governance | [`codex_audit_governance_2026_05_12.md`](issues/codex_audit_governance_2026_05_12.md) | 16 (G-1..G-16) | 4 / 7 / 5 | slot 8 (earlier 2026-05-12) |
| 1.K | UI | [`codex_audit_ui_2026_05_12.md`](issues/codex_audit_ui_2026_05_12.md) | 19 (UI-1..UI-19) | 3 / 12 / 4 | harsh-codex-audit-ui-tab |
| 1.L | Testing | [`codex_audit_testing_2026_05_12.md`](issues/codex_audit_testing_2026_05_12.md) | 20 (TS-1..TS-20) | 6 / 12 / 2 | harsh-codex-audit-testing-tab |

**Recurring cross-area patterns** (worth a single batched fix in Phase 3): (1) **moved/archived-repo references** — codex
+ CLAUDE.md repeatedly name modules that no longer exist (`unified-config-interface/testnet_contracts.py` → UTL;
`DefiErrorCode` → UAC; `unified_trading_services` module path; UDEI archived) — D-7, EX-2/5/6, AL... ; (2) **enum-count
drift** — codex prose freezes counts that the UAC enums have since grown past (archetypes 53→55, families 8→9, instruction
actions 14, EmptyConfirmedReason 9-13→17+, AlertCodes 39→63, oracle/chain counts) — D-1, ST-1/2/3/6, R-5..R-9, AL-4;
(3) **bucket-name SSOT drift** — hardcoded `gs://...` / `category`-vocab patterns not routed through `resolve_bucket_name()`
— D-5, O-3/4, ML-1, PB-10/11; (4) **codex docs missing from `00-SSOT-INDEX.md`** — ST-18, ML, IN, O-15, G-11, TS-15;
(5) **Runbook Execution-Owner block missing** on operator-runnable runbooks/reconcilers — O-7/8, IN-6/14/16, PB; (6)
**self-flagged-stale docs that still ship their stale content inline** — UI-14, TS-14/15, IN-1. Phase 2 should tag each
finding with a disposition; Phase 3 ships the IMMEDIATE batch (start with the recurring-pattern fixes for max leverage).

**BIG findings escalated to operator** (cross-side ping 2026-05-12 in `_agent_pings.md`): EX-1 (flash-loan-receiver
deployment ambiguity — cutover-blocking if placeholder); EX-10 (Copper-MPC vs CLOUD_KMS_ENCRYPTED custody-default
contradiction on 2 arch docs); IN-1 (`defi-venue-protocol-catalogue.md` actively instructs agents to delete valid
`defi_venue_capabilities.py` references); PB-1/2/3 (execution audit-records non-immutable, per-order not per-client,
on a 7-yr regulatory surface); ML-1 (4+ incompatible model-artefact bucket SSOTs); ML-2 (codex says live ML inference
inside features-service but code runs standalone `ml-inference-service`); AL-1/AL-2 (`KillSwitchScope.WALLET` broken
ref + missing `WALLET_CAP_EXCEEDED` AlertCode — routed to slot 4); TS-5 (codex `quality-gates.md`/`dependency-management.md`
contradict the workspace "Flat deps only" rule). Plus the catalogue-audit P0: GMX/DRIFT dual-classification
(`cross_asset_group_catalogue_audit_2026_05_10.md` Phase 1C — see that plan's "Per-asset-group catalogue audit pass" section).

## DONE block

(Filled at completion.)
