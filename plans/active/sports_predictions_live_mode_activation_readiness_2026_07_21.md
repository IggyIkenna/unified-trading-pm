---
doc_type: plan
title: Sports/predictions live-mode activation readiness — scoped chain + gates (no activation)
summary: >-
  Scopes the full MTDS/MDPS/FSS/strategy-service live-mode activation chain for asset_group=sports and
  asset_group=prediction so a plan is READY, not to activate live trading now — both asset groups are deliberately
  backtest-only today per the May-23 readiness ladder (BLK-9d3a208c operator ruling, resolving
  sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md's last open todo). The actual flip to live
  is gated behind an explicit [OPERATOR] go-ahead todo, not autonomous-safe work.
status: active
nature: design
asset_group: [sports, prediction]
stage: [data, strategy, execution]
repos:
  [
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    execution-service,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [sports, prediction, live-mode, activation-chain, readiness-ladder, mtds, mdps, fss, promote]
related:
  [
    plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    /plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md,
    plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md,
    plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/sports-batch-live.md,
    /codex/04-architecture/sports-live-odds-connectivity.md,
    /codex/04-architecture/prediction-batch-live.md,
    /codex/04-architecture/promote-workflow-architecture.md,
    /codex/04-architecture/backtest-groups.md,
    plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "operator ruling BLK-9d3a208c (2026-07-21): human plan, assigned_vm: NA, NOT AO-dispatched — a plan whose terminal
    action is a human go/no-go on live trading activation is the human-plan class by construction",
  ]
assigned_role: infra
drift_direction: advance-code
---

# Sports/predictions live-mode activation readiness — scoped chain + gates

> **🟡 SCOPE OVERLAP — read `sports_consolidated_closeout_2026_07_19.md` before acting on either doc (found during the
> 2026-07-23 plan-reconciliation audit; this plan was an orphan, never linked to the closeout despite the overlap).**
> This plan scopes new live MTDS/prediction connector infrastructure for sports/prediction with **zero visibility** into
> the closeout's active cross-AG `asset_group=prediction` bleed bug (rows meant for `prediction` writing into sports'
> instruments index) — a real correctness defect in the exact data path this plan's Todo 2/3 would build new live
> ingestion on top of. **UPDATE 2026-07-25 (was: "fixed and verified ... ruled GO ... gated on confirming durable" — the
> durability check has since FAILED, not just pending):** the closeout's 2026-07-23 root-cause sweep initially fixed and
> verified the bleed bug (`market-tick-data-service@a7ff45f9`, manifest-bucket root cause `@299ef540`), but a 2026-07-24
> RE-TRIAGE ROUND 3 (`plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md:133`) found the exact
> same 11,727 bleed rows back in the sports instruments index despite the earlier "VERIFY PASSED: 0 remaining" claim —
> the fix did NOT hold durably. `status` was reverted to `open` in
> `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`, and this plan's go-live pre-req is now a
> **hard BLOCKER**, not an unconfirmed pre-req — do not proceed past it until ROUND 4 (root-cause the manifest
> consolidator's reassertion mechanism + ship a durable fix, verified across a real consolidation cycle) lands. **Do not
> resolve this conflict unilaterally from this document alone** — check the closeout's current Track sections (Track X /
> the 2026-07-24 re-triage + decision-record sections) for the latest state before treating either doc's status as
> final.

## Why this plan exists, and what it is NOT

This is a **readiness/scoping plan**, not an activation plan. Per the operator's own asset-group readiness ladder
(`plans/archive/2026_07/master_to_live_defi_2026_05_23.md:688-699`), sports and prediction sit BELOW live trading today:

| Asset group    | Current rung (May-23 ladder) | Rungs still ahead                                                      |
| -------------- | ---------------------------- | ---------------------------------------------------------------------- |
| **sports**     | ML pipeline running          | Live trading (perp hedge leg only) → Live trading on real wallet       |
| **prediction** | Features pipeline running    | ML pipeline running → Live trading (hedge leg) → Live trading (wallet) |

Nothing in this plan authorizes moving either asset group up a rung. Its job is to have the chain and its gates **named
and sequenced** so that when an operator eventually decides to pursue live mode for sports/predictions, the work is a
checklist, not a fresh investigation.

## The structural blocker this plan does NOT try to solve

Unlike cefi/defi (which had a real live venue feed to wire up), **sports has no in-play live odds source integrated
today** — confirmed in `/codex/04-architecture/sports-batch-live.md` §1: every current sports source
(`api_football`/`footystats`/`odds_api`/`understat`/`soccer_football_info`/`transfermarkt`/`open_meteo`) is
`{BATCH, REPLAY}`-only in UAC's `SOURCE_MODE_CAPABILITY`; "a `live_<source>` capability lands only when a sports in-play
live archetype exists — the capability matrix is the gate, not an aspiration." The one live-ish path that DOES exist —
The Odds API aggregator (`/codex/04-architecture/sports-live-odds-connectivity.md`, REST poll, near-real-time) — is not
yet declared as a `live_odds_api` capability or wired into an MTDS live-mode ingestion loop; MTDS itself is
architecturally a **download/batch service, with no live streaming mode**, per
`/codex/04-architecture/batch-live-architecture.md` §4's service audit matrix. Wiring a live MTDS ingestion path for
sports odds is real, separate infrastructure work — this plan names it as a prerequisite (Todo 1) rather than designing
it, since it's its own scoped effort once an operator decides to pursue it.

Prediction's live-odds/CLOB connectivity (Polymarket/Kalshi) is a separate question, out of this plan's immediate scope
(`/codex/04-architecture/prediction-batch-live.md` describes the CLOB matching-engine seam architecturally, but
prediction hasn't reached "ML pipeline running" yet per the ladder above — activation readiness there is further out
than sports').

## The activation chain, reusing the cefi/defi-proven pattern (not inventing a new one)

The precedent — `plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md` (landed for cefi/defi) — used
per-asset_group launcher scripts (`launch-mtds-live-{asset_group}.sh`, `launch-mdps-features-live-{asset_group}.sh`),
gated by the 7-group/23-item per-service readiness checklist (Groups A Code health, B Data correctness, C Runtime
parity, D Coverage & shard, E Operability, F Trading prerequisites, G Operator UX, H per-client isolation) in
`master_to_live_defi_2026_05_23.md`. For sports/prediction, the SAME shape applies once each layer is ready:

1. **Data layer (MTDS)** — a live sports-odds ingestion path must exist first (the structural blocker above).
   `market-tick-data-service` gets a `launch-mtds-live-sports.sh` analogous to the cefi/defi launchers, once
   `live_odds_api` (or whichever source) is a declared `SOURCE_MODE_CAPABILITY` member.
2. **Processing layer (MDPS)** — already has `LiveModeHandler` (per `batch-live-architecture.md` §4's service audit
   matrix, MDPS supports `--mode batch|live` today) — the gap is a sports-specific live config, not new code
   architecture. `launch-mdps-features-live-sports.sh` per the same precedent.
3. **Features layer (FSS)** — currently `batch`-only for the sports family; "Live handler is post-cutover" per the same
   service-audit matrix — FSS needs its live handler built for sports before this layer can activate. Depends on
   MTDS/MDPS above landing first (features can't compute live signals from data that isn't arriving live).
4. **Strategy/execution layer** — the CLI-primary promote workflow
   (`/codex/04-architecture/promote-workflow-architecture.md`) already exists and is asset-group-agnostic:
   `run-paper.sh` → `preflight-cutover.sh` → `launch-strategy-paper-vm.sh` (paper), then after ≥7 days passing,
   `run-live.sh` → `launch-strategy-live-vm.sh` (live), state-machined via
   `StrategyMaturityPhase: IDEATION → CANDIDATE → PAPER_1D → LIVE_EARLY`. This layer is REUSABLE once a sports archetype
   has a real `CANDIDATE`-phase backtest pass (gated on the Group-B/Group-C prerequisites below) — no new
   promote-workflow engineering needed here, just running the existing CLI chain for a sports archetype.

## Prerequisites already tracked elsewhere (this plan does not duplicate them)

Per the SSOT-direction rule, these stay owned by their existing docs — this plan only sequences them:

- **Group-B backtest harness** — PARTIALLY restored this session
  (`sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`'s own earlier todo,
  `strategy-service@9a7de7f8`: fixture + `run_sports_arb_backtest.py`, proven end-to-end for
  `ML_DIRECTIONAL_EVENT_SETTLED`/`SPORTS_VALUE_BETTING`). A real, currently-open bug blocks the ORIGINAL "sports arb"
  archetype specifically: `plans/active/issues/sports_arb_dutching_engine_not_wired_to_factory_2026_07_21.md`
  (`SportsArbDutchingEngine` not in the factory dispatch table).
- **Group-C execution-alpha harness** — **decided YES, genuinely needed** (resolved, not open — corrected 2026-07-24 per
  the plan-reconciliation audit; the parent issue doc's Group-C decision-todo is checked `[x]`: "~~Decide whether
  sports/predictions actually needs a Group-C execution-alpha harness~~ — **decision: YES, genuinely needed (not a
  category error like the sibling Group-B/C conflation todo above) — scoped as its own plan, not built now.**"
  `L0Matcher` already generically routes sports/prediction `BookmakerCategory`/`"BET"` sources to `BookType.L0_TOB`, so
  the missing piece is purely a `run_sports_backtest` CLI entrypoint, not a from-scratch harness). Scoped — not yet
  built — in `sports_group_c_execution_backtest_harness_2026_07_21.md`, sitting for operator review/dispatch, same as
  the arb-decay-window design doc below.
- **Arb-decay-window + paper-trade alpha gate** — spec'd (design-only, no implementation) in
  `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` (BLK-b567ce7d), pending operator review/dispatch.
- **FSS/ML/strategy schema naming** — the 4-way `spread_calculator`-adjacent naming mismatch is ruled (BLK-a1ce4719, UAC
  `SportsFeatureVector` canonical) with its own migration plan,
  `sports_odds_feature_naming_canonicalization_2026_07_21.md`, not yet executed.
- **UI signal-surfacing check** — a separate open todo in the parent issue doc (repo: unified-trading-system-ui),
  independent of this plan's data/strategy chain.

## Todos

- [ ] [OPERATOR] P3. Decide whether to pursue a live sports-odds ingestion path at all (the structural blocker above) —
      this is a real, scoped infrastructure investment (a new MTDS live-mode connector + a declared
      `SOURCE_MODE_CAPABILITY` entry), not a flag flip. Until this is decided yes, none of the chain below can start; if
      decided no (sports stays batch-only for the foreseeable future), this plan should be marked
      `status:     cancelled` with that ruling recorded, not left open indefinitely.
- [ ] [INFRA] P3. Once Todo 1 is a yes: scope the MTDS live-odds connector (which source — `odds_api` aggregator is the
      only currently-viable live-ish path per `sports-live-odds-connectivity.md` — REST poll, near-real-time, no
      login) + the UAC `SOURCE_MODE_CAPABILITY`/`SOURCE_PRIORITY` entries it needs, as its own follow-up plan (this plan
      only names it — building it is real, separately-estimated work). (repo: market-tick-data-service,
      unified-api-contracts)
- [ ] [INFRA] P3. Once the MTDS connector lands: build `launch-mtds-live-sports.sh` +
      `launch-mdps-features-live-sports.sh`, mirroring the cefi/defi precedent
      (`plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md`); MDPS's `LiveModeHandler` already exists,
      so this is primarily a sports-specific config + launcher, not new MDPS architecture. (repo:
      market-tick-data-service, market-data-processing-service, deployment-service)
- [ ] [DATA] P3. Build the FSS live handler for the sports feature family (currently batch-only, "post-cutover" per
      `batch-live-architecture.md` §4) — depends on the MDPS live feed above actually arriving. (repo: features-service)
- [ ] [REVIEW] P3. Run a sports archetype through the existing CLI-primary promote workflow (`run-paper.sh` →
      `preflight-cutover.sh` → `launch-strategy-paper-vm.sh`, ≥7 days, then `run-live.sh` →
      `launch-strategy-live-vm.sh`) once it reaches `CANDIDATE` phase via a passing Group-B backtest AND the Group-C
      execution-alpha harness (decided YES-needed per
      `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md` — scoped but not yet built in
      `sports_group_c_execution_backtest_harness_2026_07_21.md`, which must land first) — no new promote-workflow
      engineering, just executing the existing chain. (repo: strategy-service, execution-service)
- [ ] [OPERATOR] P3. Final explicit go-ahead to flip sports (and separately, prediction, once it reaches this rung) from
      paper to live trading — requires the full readiness-ladder checklist (Groups A-H,
      `master_to_live_defi_2026_05_23.md`) passing for the asset group, same bar cefi/defi cleared. **This is the actual
      activation step; nothing above it authorizes live trading on its own.**

## Codex SSOTs

`/codex/04-architecture/batch-live-architecture.md`, `/codex/04-architecture/sports-batch-live.md`,
`/codex/04-architecture/sports-live-odds-connectivity.md`, `/codex/04-architecture/prediction-batch-live.md`,
`/codex/04-architecture/promote-workflow-architecture.md`, `/codex/04-architecture/backtest-groups.md`.

## Progress Log

- 2026-07-21 (slot 7): Plan authored per operator ruling BLK-9d3a208c on
  `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`'s last open todo. LOCAL/human track
  (`assigned_vm: NA`) — the operator explicitly ruled this class of work (terminal action = human go/no-go on live
  trading) is human-plan-by-construction. Grounded in real precedent (cefi/defi's landed live-pipeline-activation plan +
  the existing promote-workflow CLI) via a dedicated research pass, not invented from scratch — see the "structural
  blocker" section for why this genuinely differs from the cefi/defi case (no live odds source exists for sports today,
  vs. cefi/defi which had one to wire up).
- 2026-07-24: **Corrected per the 2026-07-23/24 plan-reconciliation audit
  (`plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`)** — the "Prerequisites already tracked
  elsewhere" section's Group-C bullet wrongly said the harness need was "not decided yet"; the parent issue doc
  (`sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`) actually has that exact decision-todo
  checked `[x]` with "decision: YES, genuinely needed", which spawned
  `sports_group_c_execution_backtest_harness_2026_07_21.md` (now added to `related:`). Also corrected Todo 5's "Group-C
  if Todo below rules one is needed" phrasing, which assumed the same stale undecided state.
