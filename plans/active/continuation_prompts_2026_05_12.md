---
title: "Continuation prompts — 2026-05-12 — density-push cycle (3.5-4 AI-days/slot/day)"
type: orchestration-doc
status: active
created: 2026-05-12
horizon: 4-day cycle through 2026-05-15 freeze gate
companion_to: plans/active/work_split_2026_05_12_ikenna.md + plans/active/work_split_2026_05_12_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Continuation prompts — 2026-05-12 — density-push cycle

> **Why this doc**: 2026-05-12 split is a thematic reset for slots 2-8 (Ikenna side). Density target = 14-16 calibrated
> AI-days/slot over the 4-day cycle (1.7× yesterday's already-aggressive load). Each slot gets a paste-ready CONTINUE
> prompt with: (a) status-line-first preamble to ack/close 2026-05-11 scope before pivoting, (b) new theme + plan-of-record,
> (c) Half-1+2+4 cadence, (d) sub-agent fan-out guidance, (e) "don't stop at nice-haves" framing, (f) cross-tab/cross-side
> handshake pointers. References lean `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (10KB), not 211KB CLAUDE.md.
>
> **Operator directive 2026-05-11 PM** (carry-forward): _"don't stop even at nice-haves; we're moving faster than planned + need
> to start migrating buckets and manifests for v8 and start getting data again."_ Phase 1 freeze gate at 2026-05-15 is the
> hard constraint. ~530 calibrated AI-days remaining vs 12 days runway → 44 AI-days/day workspace-wide pace required.

## Universal preamble — every slot does this first (5-10 min)

```text
STATUS-LINE FIRST. Before pivoting to today's theme, post a 1-line status in
unified-trading-pm/ikenna_orchestrator/_agent_pings.md as the slot's first commit of the day:

  [2026-05-12 HH:MM UTC] [slot N → main] STATUS-2026-05-11: ✅ DONE <scope> / ⚪ PARTIAL <what closed vs deferred> / 🟡 BLOCKED on <Q>

Then commit + push:
  git add unified-trading-pm/ikenna_orchestrator/_agent_pings.md && \
    git commit --no-verify -m "docs(orchestrator): slot N STATUS-2026-05-11 line" && \
    git push origin tab/ikennaigboaka/N --no-verify && \
    git push origin tab/ikennaigboaka/N:live-defi-rollout --no-verify

Cadence per shippable unit (per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" Half 1+2+4):
  git add <specific files> && \
    git commit --no-verify -m "..." && \
    git push origin tab/ikennaigboaka/N --no-verify && \
    git push origin tab/ikennaigboaka/N:live-defi-rollout --no-verify

Plan-flip checkboxes in same logical unit as code commit. EOD-audit + DONE-2026-05-15 block per CLAUDE.md.
```

## Ikenna slot 2 — `defi_catalogue_chain_primitives` Phases 1-3 design lead — CRITICAL PATH

```text
You are Tab 2 (Ikenna). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/2/ on branch tab/ikennaigboaka/2.

PRIOR CYCLE: 2026-05-11 manifest_schema_final_gate Phase 2/3/4/5 ✅ MAJOR SHIP (12 commits / 5 repos per PM@1dae5dbf).
You're freed from manifest scope; pivot to defi_catalogue.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_ikenna.md § Today's slot assignments → row 2
  3. unified-trading-pm/plans/active/defi_catalogue_chain_primitives_2026_05_10.md Phases 1-3
  4. unified-trading-pm/plans/active/defi_recursive_borrow_archetypes_2026_05_10.md Phase 0 (dependency-on-you direction)

Agent-tag: ikenna-defi-catalogue-tab.

SCOPE (~16 calibrated AI-days; design-class 0.6× over 4 days):
  Phase 1 — chain × protocol matrix completion (Ethereum/Arbitrum/Optimism/Base/Polygon/BSC/Avalanche/Linea × AAVE/Compound/
            Spark/Morpho/Radiant/Venus/etc). Per-pair: bridge-availability + liquidity floor + oracle + listing-date.
  Phase 2 — per-protocol shard atom decisions. Document which protocol families share a shard vs split (lending-vs-DEX,
            v2-vs-v3, single-chain-vs-cross-chain). Codex SSOT update if shard granularity shifts.
  Phase 3 — lending-indices fix (defi_recursive_borrow Phase 0 prereq). Today's defi #5 lending-indices VM landed earlier;
            close any remaining index-construction gaps.

CRITICAL PATH HANDSHAKES:
  • slot 5 (defi_recursive_borrow Family 1) — Phase 3 lending-indices fix is their Day-3 dependency. Publish Phase 3 spec
    artefact by EOD Day 2 (2026-05-13). Slot 5 starts Family 1 design Day 1 in parallel; pulls fix Day 3.
  • Cross-side ↔ Harsh slot 2 — Ikenna designs (Phases 1-3), Harsh implements (Phases 2-6 across protocols). Publish
    per-protocol shard-atom decision by Day 1 EOD per family. Surgical `git add -p` on shared plan body + UAC schema.

SUB-AGENT FAN-OUT (recommended Phase 1 expansion):
  Fan out 6-8 Task blocks in ONE message (one per chain) for the chain × protocol matrix research. Each sub-agent:
  enumerate protocol presence + liquidity floor + listing date for assigned chain. Reconcile into single Phase 1
  matrix artefact at end of Day 1.

DON'T STOP at nice-haves. If matrix + shard decisions + lending-indices fix all close before Day 4, look for adjacent
items: protocol-config schema additions (UAC), catalog refresh tests, codex doc 04-architecture/ updates.

CARRY-FORWARD FROM 2026-05-11: 4 lending-indices residuals slot 3 handed off (per `defi_master` Priority #5 close-out
PM@`e160a364`) — fold into Phase 3 lending-indices fix work.

DONE: append DONE-2026-05-15 block in defi_catalogue plan body. EOD-audit per CLAUDE.md "End-of-cycle audit clause".
```

## Ikenna slot 3 — `code_freeze_migrate_backfill` Phase 1 audit + Phase 2 dry-run — CRITICAL PATH

```text
You are Tab 3 (Ikenna). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/3/ on branch tab/ikennaigboaka/3.

PRIOR CYCLE: 2026-05-11 defi_master Priority #5 lending-indices LINEA/BSC ✅ DONE per PM@e160a364 (4 residuals handed off).
Status-line first per universal preamble.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_ikenna.md § Today's slot assignments → row 3
  3. unified-trading-pm/plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md Phase 1.E + Phase 2 dry-run
  4. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md (the dependency Phase 1 audit checks)

Agent-tag: ikenna-codefreeze-audit-tab.

SCOPE (~14 calibrated AI-days):
  Phase 1.E — freeze-gate item closure audit. 6 items per code_freeze_migrate_backfill_sequencing:142-149. CONFIRM each
            either ✅ shipped (with commit SHA) or 🟡 BLOCKED with named owner + ETA. Open items per yesterday's audit:
            • Phase 4.MTDS pipeline_mode sweep (Q1-Q5 blocked) — pursue operator decision or scope-cut
            • Phase 4.FEATURES (gated on features-consolidation merge — verify status)
            • Phase 4.GREP-VERIFY (workspace-wide AST-walk)
            • Phase 4.DEFAULT-REMOVAL (transitional None defaults removal)
            • Phase 0.B (run measure-honest-coverage.py on prod manifests)
            • LookaheadBiasError strict-mode at features-* (freeze-gate item #6)
  Phase 2 dry-run — sequence the 2026-05-15→05-19 cutover window. Provision + rsync + write-pause + delegate flip + archive
            (5-step Phase 2.6 Done-def #3 sub-sequence per bucket_name_ssot § A6). For each step: list the exact CLI command
            + verifier + expected duration + rollback path. Output: Phase 2 runbook section in code_freeze plan body.
  Cross-plan banner sweep — every plan referencing Phase 1/Phase 2 surface gets `🟢 IN-FLIGHT` or `🟡 BLOCKED-ON-X` banner.

CRITICAL PATH HANDSHAKES:
  • slot 8 (manifest Phase 3 consumer sweep) — your Phase 1.E go/no-go signal gates their Phase 3 ramp. Publish by EOD
    Day 2 (2026-05-13).
  • Cross-side ↔ Harsh slot 3 — Harsh implements Phase 1 service-level closures (writegate slice (c) callsites, bucket_ssot
    Phase 0 tail, manifest v8 wire-in). Daily sync at EOD on freeze-gate item closures.

SUB-AGENT FAN-OUT (recommended Phase 1.E expansion):
  Fan out 6 Task blocks in ONE message — one sub-agent per freeze-gate item. Each: grep + read + verify ✅/🟡/❌ status +
  return commit SHA or named blocker. Reconcile into single audit table in code_freeze plan body Phase 1.E section.

DON'T STOP at nice-haves. If audit + Phase 2 dry-run + banner sweep all close before Day 4, pick up Phase 2 detailed
playbook: per-bucket migration order, per-VM-prefix rsync sizing, manifest re-sync scheduling.

CARRY-FORWARD FROM 2026-05-11: (1) TradFi 4.3% phantom audit P0-triage (per slot 6 audit PM@`17d0b9c6`) — surface as
Phase 1.E sub-audit item. (2) Phase 4.MTDS Q1-Q5 (PM@`237d00b7`) — your audit collects + escalates operator decision.

DAY-2 P0 INJECTED 2026-05-12 (operator triage decisions received):
  Operator approved both Q1 + Q2 from your Phase 1.E audit cross-side ping (PM@<your-audit-ship-commit>):
    • Q1 = (α) — migrate `DefiManifestRecorder.record_captured` legacy `ManifestWriter.add()` → v8 `record_captured()` path.
    • Q2 = (A) — extend UAC `PipelineMode` enum + `SOURCE_PRIORITY` with 6 missing values: `BATCH_YAHOO` / `BATCH_BARCHART` /
      `BATCH_FOOTYSTATS` / `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` / `BATCH_CHAINLINK`.
  Issue docs flipped ✅ RESOLVED with operator decisions inline:
    • `plans/active/issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md`
    • `plans/active/issues/mdps_vix_15m_yahoo_barchart_pipeline_mode_gap_2026_05_12.md`
    • `plans/active/issues/footystats_pipeline_mode_gap_2026_05_12.md`
  **Scope you ship (~60 min mechanical sweep)**:
    1. UAC: extend `unified_api_contracts/canonical/crosscutting/pipeline_mode.py` + `source_priority.py` with 6 new enum
       values + SOURCE_PRIORITY entries (per existing per-source layering convention). Update facade re-exports if any.
       UAC unit tests covering new enum members + SOURCE_PRIORITY entries.
    2. UTL: deprecate / remove `DefiManifestRecorder.record_captured` legacy `ManifestWriter.add()` path; route all callers
       through v8 `record_captured()` with explicit `pipeline_mode=`.
    3. MTDS: 102 callsites across 26 files now get explicit `pipeline_mode=PipelineMode.BATCH_<source>` (the previously
       ambiguous `BATCH_YAHOO` / `BATCH_BARCHART` / `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` / `BATCH_CHAINLINK`
       callsites flip from workaround → exact match).
    4. MDPS: 1 VIX-gap callsite at `orchestration_writer.py:343` flips to `pipeline_mode=PipelineMode.BATCH_YAHOO` (or
       `BATCH_BARCHART` depending on which fetcher emitted that day's empty).
    5. instruments-service: ~7 footystats orchestrator callsites + 2 backfill scripts flip to `pipeline_mode=PipelineMode.BATCH_FOOTYSTATS`.
    6. Phase 4.DEFAULT-REMOVAL prerequisite cleared — remove `pipeline_mode: PipelineMode | None = None` default in UTL
       `ManifestWriter` once sweep is workspace-clean.
  **Sub-agent fan-out**: 5 Task blocks (one per repo surface: UAC + UTL + MTDS + MDPS + instruments-service). Reconcile
  into single workspace sweep table; flip Phase 4.MTDS / Phase 4.MDPS / Phase 4.INSTRUMENTS / Phase 4.DEFAULT-REMOVAL
  checkboxes in `manifest_schema_final_gate_2026_05_09.md` + freeze-gate item #3 in `code_freeze` plan.
  **Unblocks**: Phase 4.DEFAULT-REMOVAL → 2026-05-15 Phase 1 freeze gate (was blocking item).

DONE: append DONE-2026-05-15 block. EOD-audit. Banner-cleanup owned by you when Phase 1.E flips closed.
```

## Ikenna slot 4 — `api_keys_wallets_accounts_readiness` design lead

```text
You are Tab 4 (Ikenna). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/4/ on branch tab/ikennaigboaka/4.

PRIOR CYCLE: 2026-05-11 live-pipeline Phase 4-5 design-ahead was carry-forward; status uncertain per main-orch audit.
Status-line first — confirm what closed vs deferred.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_ikenna.md § Today's slot assignments → row 4
  3. unified-trading-pm/plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md Phases 1-3
  4. codex/14-customer-journeys/ relevant entries (Copper KYB, Fireblocks)

Agent-tag: ikenna-keys-wallets-tab.

SCOPE (~16 calibrated AI-days):
  Phase 1 — Copper KYB onboarding kickoff. Document the operator-action checklist (KYB form fields, doc upload list,
            ETA per stage). File operator-action issue doc if any step requires human input we don't have yet.
  Phase 2 — Fireblocks decision dispatch (R9 operator gate). Surface the decision in cross-side ping or via
            AskUserQuestion. If operator already decided, codify in plan + propagate to defi_master.
  Phase 3 — wallet provisioning schema. UAC additions for per-wallet config (chain + protocol + signing surface +
            allowlist + spending cap + kill-switch hook). Schema-validation tests.

CRITICAL PATH HANDSHAKES:
  • slot 5 (defi_recursive_borrow archetype config) — uses your wallet schema. Publish schema artefact by Day 1 EOD.
  • slot 8 (cross_cutting deliverable #4 DART manual surfaces) — also uses wallet schema for client-surface design.
    Same Day-1 EOD publication.
  • Cross-side: Harsh side has zero direct dependency on this scope.

SUB-AGENT FAN-OUT: limited surface here; sequential better than parallel for design-class work. If extending UAC schema,
fan out 2-3 Task blocks (schema + tests + codex doc) at the implementation moment.

DON'T STOP at nice-haves. If Phases 1-3 close, pick up Phase 4 (Fireblocks integration spec) or Phase 5 (kill-switch
wallet-tier wiring).

DONE: append DONE-2026-05-15 block. EOD-audit per CLAUDE.md.
```

## Ikenna slot 5 — `defi_recursive_borrow_archetypes` Phases 1-2 design

```text
You are Tab 5 (Ikenna). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/5/ on branch tab/ikennaigboaka/5.

PRIOR CYCLE: 2026-05-11 RE-TASK EXPANSION Tier 1 + Tier 2 — partial ship per PM@c71b10c7+7ba139f5+ etc. Status-line first
to disambiguate which Tier 1 items closed (Step 5 MDPS / Phase 6.5 features-*) vs deferred. defi_catalogue 45 pairs +
Stream C C-enum.1+2 ✅ DONE; .3+.4 deferred to backport.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_ikenna.md § Today's slot assignments → row 5
  3. unified-trading-pm/plans/active/defi_recursive_borrow_archetypes_2026_05_10.md Phases 1-2
  4. unified-trading-pm/plans/active/defi_catalogue_chain_primitives_2026_05_10.md Phase 3 (slot 2's dep on you for Day 3)

Agent-tag: ikenna-recursive-borrow-tab.

SCOPE (~14 calibrated AI-days):
  Phase 1 — Family 1 archetype topology (recursive supply-borrow loop on AAVE-family lenders). Per-chain config: collateral
            asset, debt asset, LTV ceiling, target leverage, rebalance thresholds, oracle dependencies.
  Phase 2 — Family 2 archetype topology (cross-protocol delta-hedged borrow w/ perp short). Same per-chain config grid.

CRITICAL PATH HANDSHAKES:
  • slot 2 (defi_catalogue Phase 3) — lending-indices fix is your Day-3 dependency. Slot 2 publishes by EOD Day 2. You
    start Family 1 Day 1 design INDEPENDENT of fix; pull fix Day 3 for index-construction wire-in.
  • slot 4 (wallet schema) — uses for archetype config. Pull Day 2 morning.
  • Cross-side: zero direct Harsh dependency.

SUB-AGENT FAN-OUT: fan out 2-3 Task blocks per Phase for parallel chain-specific design (Ethereum + Arbitrum + Base
in parallel for Family 1 Day 1). Reconcile end-of-day into single Family-1 spec.

DON'T STOP at nice-haves. If Phases 1-2 close, pick up Phase 3 (sim contract integration w/ slot 6) or Phase 4
(per-family backtest scenario set).

CARRY-FORWARD FROM 2026-05-11: Stream C C-enum.3+4 deferred to backport plan — if time on Day 4, close them.

DONE: append DONE-2026-05-15 block. EOD-audit.
```

## Ikenna slot 6 — `defi_simulation_realism` Phases 1-3 design

```text
You are Tab 6 (Ikenna). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/6/ on branch tab/ikennaigboaka/6.

PRIOR CYCLE: 2026-05-11 phantom audit all-5 asset_groups ✅ DONE per PM@17d0b9c6 (items 8+9 partial handed off).
Status-line first to confirm items 8+9 status.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_ikenna.md § Today's slot assignments → row 6
  3. unified-trading-pm/plans/active/defi_simulation_realism_2026_05_10.md Phases 1-3

Agent-tag: ikenna-defi-sim-realism-tab.

SCOPE (~14 calibrated AI-days):
  Phase 1 — AMM family matrix (Uniswap-v2 / v3 / v4 / Curve-stableswap / Balancer-weighted / Velodrome-ve(3,3) / Aerodrome).
            Per-family: pricing function + slippage model + fee tier + tick/range mechanics + liquidity-concentration model.
  Phase 2 — simulation contract. Unified pre-trade quote interface across families. Slippage + fee + price-impact estimation.
            Integration shape w/ execution-service matching engine.
  Phase 3 — golden test set. Per-family fixtures (sample LPs + sample trades + expected fills/slippage). For backtest fidelity.

CRITICAL PATH HANDSHAKES:
  • slot 7 (simulation_scenarios topology shocks) — your AMM family matrix feeds AMM-flavoured topology shocks. Publish
    matrix by Day 2 noon; slot 7 starts AMM-flavoured shocks Day 2 afternoon.
  • Cross-side ↔ Harsh slot 4 — Ikenna designs AMM family matrix + sim contract; Harsh implements per-AMM family connectors.
    Spec handoff EOD Day 2.

SUB-AGENT FAN-OUT (Phase 1 expansion):
  Fan out 7 Task blocks in ONE message — one per AMM family. Each sub-agent: enumerate the family's pricing function +
  fee model + sample testnet pool + golden fixture seed. Reconcile end-of-Day-1 into single AMM matrix artefact.

DON'T STOP at nice-haves. If Phases 1-3 close, pick up Phase 4 (matching-engine integration spec) or Phase 5 (multi-hop
routing realism for DEX-aggregator surfaces).

CARRY-FORWARD: phantom audit items 8+9 (if not closed today) — close before pivoting fully into sim work.

DONE: append DONE-2026-05-15 block. EOD-audit.
```

## Ikenna slot 7 — `simulation_scenarios_topology_price_shocks` Phases 1-2

```text
You are Tab 7 (Ikenna). New theme today. Worktree: ${WORKSPACE_ROOT}/.tabs/7/ on branch tab/ikennaigboaka/7.

PRIOR CYCLE: 2026-05-11 absorbed Harsh slot 5 live-pipeline carry-forward (Round 1-4 ✅, Phase 3.1/3.3/3.4 shipped at
mtds@97b2224). Status-line first to confirm Phase 3.5/5/6/15 closure status from yesterday's absorption brief.

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_ikenna.md § Today's slot assignments → row 7
  3. unified-trading-pm/plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md Phases 1-2
  4. unified-trading-pm/plans/active/risk_simulations_limits_alerting_2026_05_10.md (handshake target)
  5. unified-trading-pm/plans/active/disaster_recovery_circuit_breakers_2026_05_10.md (handshake target)

Agent-tag: ikenna-scenarios-topology-tab.

SCOPE (~14 calibrated AI-days):
  Phase 1 — topology shock scenarios (per-venue-down, per-chain-down, per-protocol-paused, oracle-stale, gas-spike,
            mempool-congestion). Per-scenario: trigger condition + observable signature + expected risk-engine response.
  Phase 2 — price-shock scenarios (flash crash, basis blowout, funding-rate spike, depeg). Per-scenario: magnitude curve
            + duration distribution + cross-venue correlation assumption.
  Handshakes — risk_simulations (per-axis registry) + DR (circuit-breaker arming) integration shape.

CRITICAL PATH HANDSHAKES:
  • slot 6 (defi_simulation_realism AMM matrix) — pulls Day 2 PM for AMM-flavoured shock scenarios. Day 2 noon dep.
  • Cross-side ↔ Harsh slot 5 — Ikenna designs scenarios + risk-limit-axis matrix; Harsh implements alerting wiring +
    circuit-breaker logic. Daily sync on scenario coverage.

SUB-AGENT FAN-OUT:
  Fan out 6 Task blocks (one per topology shock type for Phase 1) in ONE message. Reconcile end-of-Day-1.

DON'T STOP at nice-haves. If Phases 1-2 + handshakes close, pick up Phase 3 (scenario-runner integration spec) or
Phase 4 (per-scenario test fixture set).

CARRY-FORWARD FROM 2026-05-11: (1) Phase 3.5/5/6/15 of live-pipeline from yesterday's Harsh-slot-5 absorption (PM@`91a24ecc`).
(2) Slot 4's Phase 4-5 design-ahead carry-forward (status uncertain — STATUS-2026-05-11 line resolves; if open, extend to
Phase 4-5 implementation). (3) Phase 13/14/15 DEFERRED-AFTER-PHASE-3-5 — pick up if Phase 3-5 closes early. (4) Phase 6
(features cross-cutting) — 🟡 BLOCKED on features-consolidation Phase 7 (Harsh slot 2 Q6+Q7); unblocks when that ships.

DONE: append DONE-2026-05-15 block. EOD-audit.
```

## Ikenna slot 8 — `cross_cutting_may_23` #4 + `manifest_schema_final_gate` Phase 3 — CRITICAL PATH

```text
You are Tab 8 (Ikenna). Same theme as yesterday (manifest Phase 3) PLUS cross_cutting #4 add-on. Worktree:
${WORKSPACE_ROOT}/.tabs/8/ on branch tab/ikennaigboaka/8.

PRIOR CYCLE: 2026-05-11 absorbed Harsh slot 4 bucket_name_ssot Phase 0f + Phase 0h carry-forward. Status-line first to
confirm: Phase 0f VM-launcher env-awareness shipped? Phase 0h sync script first-execution scheduling?

DAY-1 VERIFICATION ✅ DONE BY MAIN (slot 1, 2026-05-12 boot):
  Phase 3.D rescan VM ✅ COMPLETED end-to-end. After slot 3's 2-iteration fix sequence (PM@`7a11b747` + `73f4a7ec`),
  `cross-asset-rescan-20260511-172749` ran 16:30:41→16:47:11Z (16m 30s) with all 5 asset_groups return_code=0 and
  phantom_line_count=0 across cefi/defi/tradfi/sports/prediction (dry-run). triage.jsonl is 0 bytes = healthy signal
  = manifest in clean state per rescan algorithm. NO action required from you — skip verify, proceed directly to
  Phase 3 consumer sweep + cross_cutting #4. Cross-side ping in `plans/active/_agent_pings.md` documents completion.
  (Operator decision pending: should we run a `--apply-flips` non-dry-run pass to actually flip any manifest rows the
  rescan might have identified in a longer/larger date-window sweep? Default = no, dry-run signal is conclusive.)

READ (in order):
  1. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md (lean 10KB)
  2. unified-trading-pm/plans/active/work_split_2026_05_12_ikenna.md § Today's slot assignments → row 8
  3. unified-trading-pm/plans/active/issues/phase_3d_rescan_cli_dispatcher_gap_2026_05_11.md (✅ RESOLVED — verify-only)
  4. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md Phase 3 (consumer sweep)
  5. unified-trading-pm/plans/active/cross_cutting_may_23_deliverables_2026_05_08.md deliverable #4 (DART manual surfaces)
  6. unified-trading-pm/plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md Phase 0f + 0h (your carry-forward)

Agent-tag: ikenna-manifest-phase3-tab.

SCOPE (~14 calibrated AI-days):
  Day-1 verification — Phase 3.D rescan VM (above; ✅ resolved upstream, just verify completion + triage landing)
  Phase 3 consumer sweep — every workspace consumer of v8 manifest columns audited + wired. Pickup from slot 2's
            Phase 4.MDPS/INSTRUMENTS/DEPLOYMENT-API/E2E/PM-SCRIPTS shipped + Phase 4.FEATURES/MTDS open. Fan out
            audit-tasks per consumer surface.
  Cross_cutting #4 — DART manual surfaces. Per deliverable, what operator UI controls + manual-action API endpoints
            + audit-log shape we need pre-cutover. Plan body sections + UAC stubs for the surfaces.
  Group F/G master plan refresh — fields per item per master plan continuous-verification matrix.
  Carry-forward (2026-05-11 scoreboard):
            • bucket_name_ssot Phase 0f (operational verification of VM launcher env-awareness)
            • bucket_name_ssot Phase 0h (first sync execution — post-Phase-2.6 cutover step)
            • Writegate slice (b) Phase 5.X remainder (post-5.A/B tail)
            • Writegate Phase 6.2 PARTIAL scaffolding from mdps@`ae0cada` (152 LOC ohlcv_1m/24h/book_snapshot_5 helpers
              shipped to `tab/ikennaigboaka/8` ONLY; NOT FF'd to LDR) — FF to LDR + complete consumer wiring + unit tests.

CRITICAL PATH HANDSHAKES:
  • slot 3 (code_freeze Phase 1.E audit) — gates your Phase 3 ramp. Wait for go-signal EOD Day 2. Phase 3.D quick-win
    is independent + can ship Day 1.
  • slot 4 (wallet schema) — pull Day 2 for client-surface design.
  • Cross-side ↔ Harsh slot 6 — Ikenna designs DART manual surfaces + Group F/G readiness fields; Harsh implements
    consumer sweep for manifest v8 + client_reporting service stubs.

SUB-AGENT FAN-OUT (Phase 3 expansion):
  Fan out 4-6 Task blocks (one per consumer surface category: MDPS / instruments / deployment-api / e2e / features-svc /
  pm-scripts) for the audit pass. Reconcile end-of-Day-2 into single Phase 3 consumer-sweep table.

DON'T STOP at nice-haves. If Phase 3 + #4 + Group F/G refresh close before Day 4, pick up additional cross_cutting
deliverables (#5, #6 if present) or reserve list item (client_reporting_pnl_attribution_mvp).

DONE: append DONE-2026-05-15 block in EACH plan body (manifest_schema_final_gate + cross_cutting + bucket_name_ssot).
EOD-audit per CLAUDE.md.
```

## 🟢 SCOPE EXTENSION — Day 1 EOD pace check (2026-05-12 PM update)

**Observed**: slots shipping 3-5× calibrated pace. Multiple slots ✅ DONE entire 4-day Cycle-1 scope on Day 1
(slot 2 defi_catalogue Phases 1-3 + Phase 1B-1H all shipped; slot 4 api_keys_wallets Day-1 DONE block + Day-2-4 plan;
slot 5 defi_recursive_borrow Phases 1-11 design batch; slot 6 defi_simulation_realism Phases 1-5 + Phase 9B/9C
continuation; slot 7 simulation_scenarios Phases 1-2 design SHIPPED Day 1).

**Deadline UNCHANGED**: 2026-05-15 Phase 1 freeze gate (external; cannot shift). **Scope-within-cycle EXPANDS** to
absorb idle Day-2-4 capacity. Per-slot Day-2-4 extensions:

| Slot | Day-1 status | Day-2-4 extension scope |
|---|---|---|
| 2 | ✅ defi_catalogue Phases 1-3 DONE | (a) cross_asset_group_catalogue_audit fan-out (~31 calibrated; per-asset_group catalog drift reconcile, 5-sub-agent fan-out per asset_group); (b) **DefiManifestRecorder ManifestFreshnessCache wire-in P1** (operator-confirmed bug from lending-indices VM ungraceful exit — extend to sibling MTDS DeFi backfill handlers `gas_fees` / `lst_rates` / `dex_pools` / `liquidations` / `perp_funding`). |
| 3 | ✅ Phase 1.E audit + Phase 2.6 cutover dry-run + DAY-2 P0 PipelineMode sweep (operator-approved Q1+Q2) | After PipelineMode sweep closes Day 2: (a) workspace QG full sweep (freeze-gate item #5 partial); (b) full codex SSOT currency pass (~50 docs, freeze-gate item #6 partial); (c) Phase 2.6 detailed playbook (per-bucket migration order + per-VM-prefix rsync sizing + manifest re-sync scheduling). |
| 4 | ✅ Day-1 DONE + Day-2-4 plan already drafted by slot itself | Slot 4 self-extended; let them keep momentum. Their Day-2-4 plan should be reviewed Day 2 morning by slot 1 to verify scope alignment with master plan Group F items 19+22. |
| 5 | ✅ defi_recursive_borrow Phases 1-11 design batch | (a) Phase 12 backtest harness implementation (`recursive_borrow_paper_smoke.py` per `e2e-testing/scripts/defi/`); (b) Phase 4-6 implementation (sim contract integration + per-family backtest scenarios); (c) reserve list pickup `client_reporting_pnl_attribution_mvp_2026_05_10` (Group F item 22). |
| 6 | ✅ defi_simulation_realism Phases 1-5 + Phase 9B/9C continuation | (a) Phase 6-7 (golden test set landing + matching-engine integration); (b) Phase 9C+9D (operator-runnable detail for Harsh slot 4); (c) reserve list pickup `mock_data_pipeline_benchmarking_2026_05_10` (~7 calibrated). |
| 7 | ✅ simulation_scenarios Phases 1-2 (10 scenarios) | (a) Phase 3-4 (scenario-runner integration + per-scenario test fixtures); (b) Phase 5+ (per-archetype scenario coverage matrix); (c) handshake-driven fold-in of Harsh slot 5 risk + DR scenario test coverage. |
| 8 | ⚪ ACTIVE on manifest Phase 4 consumer sweep | Keep going — Phase 3 consumer sweep is substantial (8+ services × per-service v8 column wire-in). Day-2 add-on: **DAY-2 P0 INJECTED PipelineMode sweep coordination** with slot 3 (Phase 4.MTDS / 4.MDPS / 4.INSTRUMENTS callsite migration overlap — see slot 3 prompt). Reserve list `codex_vs_citadel_infrastructure_audit_2026_05_10` (~15 calibrated; hygiene) as Day-4 stretch. |

**Allocation principle**: extend within plan (Phases 4+) → pull reserve list (precedence per work_split § Reserve list)
→ pull confirmed P1 bugs. Always finish current-cycle's directly-named scope before pulling forward.

**Cycle 2 work-split (2026-05-16+) re-drafted at 2026-05-15 EOD** per `post_freeze_roadmap_2026_05_16_to_05_23.md`
will account for whatever lands in Day-2-4 extension. Don't pull Cycle 2 cutover scope forward (sequentially blocked
on Phase 1 closure).

## 🟢 SCOPE EXTENSION 2 — Cycle 2 PREP work (2026-05-13/14/15 backfill)

**Observed 2026-05-12 EOD**: 5 of 7 Ikenna slots ✅ FULL CYCLE CLOSE on Day 1 (slot 2 17-commit defi_catalogue; slot 4
api_keys_wallets full-cycle; slot 5 defi_recursive_borrow Phases 1-11+12; slot 6 defi_simulation_realism Phases 1-5
+ Phase 9C/9D; slot 8 11-ship-lots / ~12 cal AI-days). Slot 3 still on Day-2 P0 PipelineMode sweep. Slot 7 active on
scenarios.

**Cycle 1 calendar-time-remaining = 3 days (2026-05-13 / 14 / 15)** of capacity for slots already closed. Cycle 2
cutover EXECUTION is sequentially blocked on Phase 1 closure (2026-05-15), but Cycle 2 **PREP** work CAN happen
pre-freeze. Per-slot Day-3-4 layer:

| Slot | Cycle 2 PREP layer (pre-cutover; safe to ship pre-freeze) |
|---|---|
| 2 | (a) Bucket provisioning script review + dry-run (no actual creates) per `code_freeze` Phase 2.6 step 1; (b) per-bucket migration order + sizing tables per `bucket_name_ssot_canonicalisation` Phase 0c; (c) **DefiManifestRecorder ManifestFreshnessCache wire-in P1** — ship NOW (not Cycle-2 blocked, operator-confirmed bug). |
| 3 | (after PipelineMode sweep closes Day-2): (a) workspace-wide cutover runbook polish per Phase 2.6 dry-run; (b) per-VM-prefix rsync sizing tables; (c) manifest re-sync scheduling matrix; (d) write-pause coordination protocol — 5-min p99 latency design across 7 services. |
| 4 | (after Day-2-4 plan closes): (a) Copper KYB onboarding checklist closure (operator-pending if R9 still open); (b) Fireblocks integration spec (Phase 4+); (c) kill-switch wallet-tier wiring (Phase 5+). |
| 5 | (after Phase 12 backtest harness + Phase 4-6 impl): (a) per-archetype paper-trade smoke harness (Phase 13 design); (b) reserve list `client_reporting_pnl_attribution_mvp` ship; (c) DeFi Family 3+ archetype topology design (Cycle 6 prep). |
| 6 | (after Phase 6-7 + 9C/9D): (a) matching-engine integration spec (Phase 10+); (b) `mock_data_pipeline_benchmarking` reserve ship; (c) AMM family matrix Cycle 2 verification readiness (post-Harsh-4 connector ship). |
| 7 | (after Phase 3-5 + risk/DR fold-in): (a) scenario-runner integration spec (Phase 6+); (b) live-monitor dashboard prep for Cycle 5 (Phase 13 monitor mode); (c) cutover communication template + rollback procedure documentation. |
| 8 | (parallel with manifest Phase 3 consumer sweep): (a) DART manual surfaces post-cutover UI verification readiness; (b) `codex_vs_citadel_infrastructure_audit_2026_05_10` ship; (c) per_agent_worktrees Phase 4.5 R1/R2/R3 design spec (no code yet — design for Cycle 6 implementation). |

**Cycle 6 design-ahead** (pull-forward for slots with capacity to spare):
- `expected_universe_v2_design_2026_05_08` enumerator implementation spec (was BLOCKED on v8; unblocks Cycle 1)
- `per_agent_worktrees_2026_05_10.md` Phase 4.5 P1 detailed implementation plan (per Ikenna input shipped earlier today)
- Reserve list audit + per-plan pickup-precedence refinement

**Allocation principle (updated)**: Cycle 1 directly-named scope → Cycle 1 scope-extensions → reserve list →
**Cycle 2 PREP** (pre-cutover, NOT execution) → Cycle 6 design-ahead → P1 bugs. NO Cycle 2 EXECUTION (gate-locked).

**Day-of cadence**: at 2026-05-13 EOD, slot 1 main reviews who has shipped Cycle 1 + scope extensions + decides per-slot
which Cycle 2 PREP work to assign Day 3 morning. Same review at 2026-05-14 EOD for Day 4. Master goal: arrive at
2026-05-15 freeze gate with **maximum pre-cutover prep banked** so 2026-05-16 cutover execution can launch fast.

## Coordination + cleanup

After all slots post their STATUS-2026-05-11 lines, slot 1 (main) sweeps the ping ledger:
- ✅ DONE entries from yesterday → archive to plan-body DONE blocks (already done overnight for most).
- ⚪ PARTIAL / 🟡 BLOCKED → escalate to operator if blocks 2026-05-15 freeze gate.
- Banner-sweep: every plan touched in 2026-05-12 cycle gets correct `🟢 IN-FLIGHT` / `🟡 BLOCKED-ON-X` / `✅ SHIPPED` banner.

Slot 1 polls the ledger every ~1 min when operator active, ~5 min when quiet. Cross-side mirror at 17:00 daily into
`plans/active/_agent_pings.md`.

## Re-pointing if a slot finishes early

If slot N closes its scope before Day 4 EOD, pickup precedence per `work_split_2026_05_12_ikenna.md` § Reserve list:
1. `client_reporting_pnl_attribution_mvp_2026_05_10`
2. `wallet_treasury_client_flow_2026_05_10`
3. `mock_data_pipeline_benchmarking_2026_05_10`
4. `bucket_name_ssot_canonicalisation_2026_05_10` Phase 0i tail
5. `cross_asset_group_catalogue_audit_2026_05_10`
6. `codex_vs_citadel_infrastructure_audit_2026_05_10`

Slot picks up the highest-precedence un-claimed plan, files `[slot N → main] PICKING UP: <plan>` in ping ledger.
