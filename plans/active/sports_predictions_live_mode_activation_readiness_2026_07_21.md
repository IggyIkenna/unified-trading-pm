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
asset_group:
  [sports] # corrected 2026-08-13 (/ag-closeout-audit full sweep) -- was [sports, prediction]. parent_epic:
  # sports_master; 5 of 6 original todos build sports-only live-trading infra, the doc's own text says prediction
  # is out of scope -- independently reached by 3 prior audits (batch3/batch3_finalize/batch5, 2026-07-26) and
  # reconfirmed by prediction batch6's own Deferred section.
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
    /plans/archive/2026_08/sports_group_c_execution_backtest_harness_2026_07_21.md,
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
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/archive/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md,
    /plans/archive/2026_07/data_completion_sports_history_2026_07_24.md,
    /plans/archive/2026_08/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-29"
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
context_scope:
  [
    /codex/04-architecture/promote-workflow-architecture.md,
    /plans/archive/2026_08/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md,
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
  ]
---

> **✅ OPERATOR RULING 2026-08-08 — live trading REMAINS a hard-stop, and is now formally gated on the sports
> canonicalisation chain.** Reconfirmed: no real-capital sports activation. This is a permanent standing hard-stop
> requiring the operator's own explicit sign-off. It is additionally now **blocked on prerequisites**, so it stops
> surfacing as an unanswered operator question in every audit sweep: (1) raw sports capture was measured DEAD since
> 2026-07-26 and is restored by `/plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`; (2) ✅
> DONE 2026-08-08 — the arb same-operator guard was measured BROKEN on canonical venue values and has been fixed +
> archived (`/plans/archive/2026_08/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md`; measured blast
> radius on the historical record was zero); (3) the venue/data_type taxonomy migration and derived-layer backfill (13
> of ~2,250 days covered) are P2/P4 of that chain. Do not re-raise activation as an open question until the remaining
> gates land.

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

> **🟡 Operator ruling 2026-07-29:** continue to hold the live go-ahead (readiness ladder incomplete — Todo 6 below
> stays open/held), but ensure concrete build specs exist and are linked for every missing piece — see the 4 corrected
> references below (live-odds MTDS connector, live launchers, FSS live handler, Group-C harness) and their linked docs
> in `related:` (`sports_live_availability_and_source_latency_2026_07_24.md`,
> `gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md`,
> `data_completion_sports_history_2026_07_24.md`,
> `mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`).

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

> **UPDATE 2026-07-29: this section's premise is now PARTIALLY superseded — see the corrected Todos 2-4 below.** A live
> sports-odds source IS now integrated and running (`odds_api_ws.py` + the `mtds-live-sports-odds-api-trades` VM,
> `LIVE_ODDS_API` is a declared `SOURCE_MODE_CAPABILITY` member), and the FSS live handler is shipped/CLI-wired. What
> remains is NOT "wire it up" from scratch — it's landing the P0 live-writer shape-mismatch fix, confirming resumed
> production polling + the api_football second source, and the cross-cutting MDPS+features launcher exec-dispatch gap
> (see Todos 2-4). The paragraph below is left as originally written (2026-07-21) for historical context on why this
> plan differs from the cefi/defi precedent; do not treat it as the current state.

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
`master_to_live_defi_2026_05_23.md`. For sports/prediction, the SAME shape applies once each layer is ready (**UPDATE
2026-07-29 — items 1 and 3 below are DONE, not still-to-build; see the corrected Todos 2-4**):

1. **Data layer (MTDS)** — **DONE**: the live sports-odds ingestion path exists and runs today via the generic
   `launch-mtds-live.sh --asset-group sports --shard-spec sports:odds_api:trades` (VM
   `mtds-live-sports-odds-api-trades`); `live_odds_api` is a declared `SOURCE_MODE_CAPABILITY` member. Remaining gap:
   the P0 shape-mismatch fix + quota/second-source confirmation (Todo 2).
2. **Processing layer (MDPS)** — already has `LiveModeHandler` (per `batch-live-architecture.md` §4's service audit
   matrix, MDPS supports `--mode batch|live` today) — remaining gap is the cross-cutting `launch-mdps-features-live.sh`
   exec-dispatch wiring (Todo 3), not a sports-specific launcher.
3. **Features layer (FSS)** — **DONE**: the live handler is already shipped + CLI-wired
   (`features_service/sports/cli/handlers/live_handler.py`, Todo 4) — not "post-cutover"/unbuilt as originally written
   here. Remaining gap is production deployment, the same launcher-wiring dependency as item 2 above.
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

- [x] ✅ [INFRA] P3. **RULED 2026-07-28: YES — pursue it.** Was `[OPERATOR] P3` "Decide whether to pursue a live
      sports-odds ingestion path at all." Reasoning: (1) the operator has already ruled, in this exact same corpus and
      timeframe (`sports_live_availability_and_source_latency_2026_07_24.md`'s Live-ODDS quota decision, 2026-07-28), to
      proceed with resuming live sports-odds ingestion generally — that data-capture path is being actively invested in,
      not abandoned; (2) the general theme's "opt for full completions, no shortcuts, full functionality" favors
      building the plumbing properly over settling for batch-only when a live path is buildable; (3) this decision's own
      downstream risk is low — the actual live-TRADING activation (real capital) stays behind Todo 5's permanent,
      un-liftable `[OPERATOR]` hard-stop below regardless of this ruling, so saying "yes, scope it" only unblocks
      READINESS/plumbing work, not capital risk. This does NOT cancel the plan; it converts Todo 1 into "yes" and folds
      directly into Todo 2 below (no separate action needed — Todo 2 already reads "Once Todo 1 is a yes: scope...").
- [x] ✅ [INFRA] P3. **CORRECTED 2026-07-29 (was: "scope the MTDS live-odds connector ... as its own follow-up plan")**
      — the connector already exists and is shipped, not merely scoped: `odds_api_ws.py`'s `WSFeedConnector`
      (market-tick-data-service) + the `LIVE_ODDS_API` `SOURCE_MODE_CAPABILITY`/`SOURCE_PRIORITY` UAC entries are live
      in code, and a real VM is running it (`mtds-live-sports-odds-api-trades`, launched via
      `launch-mtds-live.sh --asset-group sports --shard-spec sports:odds_api:trades` —
      `/plans/archive/2026_07/data_completion_sports_history_2026_07_24.md`). No follow-up scoping plan is needed. The
      genuinely remaining work is tracked in 2 other docs, not here: ~~**(a)** the P0 todo in
      `/plans/archive/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md` — "Fix MTDS's
      live-mode sports odds writer shape mismatch BEFORE the live connector runs" (`live/websocket_runner.py`'s non-CeFi
      `live_tick_blob_path` + `live/connectors/odds_api_ws.py::_parse_fixture_response` must write one shard per
      (bookmaker, league, fixture) matching the batch `venue_fetch.py::_build_sports_shard_path` shape, instead of one
      nested-JSON-bundled file per sport — bumped P2→P0 now that the rotated `odds-api-key` lets the connector actually
      authenticate and write)~~; **STALE (na-eligibility-audit 2026-08-03)** — part (a) is done: the cited doc's own
      resolved summary confirms "the P0 live-mode sports odds writer shape fix shipped
      (market-tick-data-service@d6d539a8)" before it archived. **(b)** the open P2 todo in
      `/plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md` — "Live ODDS quota decision +
      cheap second source" — done when the api_football `/odds` in-play second source is wired as a fallback/supplement
      AND the live sports-odds ingestion is confirmed resumed (a fresh poll cycle succeeding against the live key in
      production, not just a direct-API-call verification) — **remains genuinely open** (checked live 2026-08-03: that
      doc's own item now additionally reports the api_football second-source half STRUCK/superseded 2026-08-02
      (BLK-b969f5f0, not pursued) and a NEW blocker — the `odds-api-key` quota went exhausted 2026-08-02, 4 days after
      provisioning, root cause untracked as its own P1 finding). Checkbox stays open on (b) alone. (repo:
      market-tick-data-service, unified-api-contracts)

      **UNBLOCKED 2026-08-07 (operator)**: the quota-exhaustion blocker is resolved — "now we have 15m credits on the
                                                                                      api key so all good unblocked." Root cause of the 4-days-to-exhaustion still not independently tracked as its own
                                                                                      finding (unchanged from the note above). **Checkbox NOT flipped** — this todo's own done-when additionally
                                                                                      requires "a fresh poll cycle succeeding against the live key in production, not just a direct-API-call
                                                                                      verification," which has not been independently confirmed here; the api_football second-source half also remains
                                                                                      STRUCK/not-pursued. Whoever next touches this doc should re-verify a live poll cycle before closing.

                                                                                              **na-eligibility-audit 2026-08-07 — UNRESOLVED TENSION, flagging not closing**: found
                                                                                              `/plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md` already `status: complete`,
                                                                                              archived 2026-08-04 — "All 8 todos complete; the final remaining todo (Live-ODDS quota/second-source) was verified
                                                                                              done 2026-08-03 (live VM healthy, api_football half struck per `BLK-b969f5f0`)," with that doc's own Progress Log
                                                                                              (2026-08-03, slot 7) citing a live-verified poll cycle: "found `mtds-live-sports-odds-api-trades-20260803-172841`
                                                                                              already RUNNING ... 35+ min of clean run.log with zero ERROR/401/OUT_OF_USAGE_CREDITS." This predates (by 3-4
                                                                                              days) the operator's 2026-08-07 UNBLOCKED note directly above, which describes resolving a quota-exhaustion
                                                                                              blocker as though still open at that later date — unclear whether this is a SECOND, later quota exhaustion (the
                                                                                              key ran dry again after 08-03/04) or a delayed answer to an already-self-resolved question. Did not independently
                                                                                              re-verify a live poll cycle to break the tie (recovering an interrupted prior run's uncommitted WIP from a
                                                                                              git-stash conflict, not doing fresh sports-tranche analysis). **Leaving checkbox open per the operator's explicit
                                                                                              instruction above** rather than closing on the archived doc's older evidence — next sports-tranche pass should
                                                                                              re-verify a live poll cycle now and resolve this explicitly either way.

- [x] ✅ [INFRA] P3. **CORRECTED 2026-07-29 (was: "build `launch-mtds-live-sports.sh` +
      `launch-mdps-features-live-sports.sh`" — 2 new per-asset-group scripts from scratch)** — `launch-mtds-live.sh`
      already works for sports today: it's the SAME generic (not per-asset-group) launcher used across every asset
      group, invoked as `launch-mtds-live.sh --asset-group sports --shard-spec sports:odds_api:trades`, and it is the
      launcher behind the running `mtds-live-sports-odds-api-trades` VM (see the corrected connector todo above /
      `/plans/archive/2026_07/data_completion_sports_history_2026_07_24.md`) — no new per-asset-group MTDS launcher
      needs building. The remaining launcher work is the OTHER half — `launch-mdps-features-live.sh` — which is
      cross-cutting, not sports-specific: its exec-dispatch was never wired up at all (`setup-data-pipeline-vm.sh` has
      no branch for `VM_TASK=mdps-features-live`, so it falls through to the invalid literal
      `python -m market_data_processing_service+features_service` module path), tracked in
      `/plans/archive/2026_08/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`. Process topology is
      PARTIALLY operator-ruled 2026-07-28 there (option (a): per-shard MDPS processes + per-family features-service
      processes, both subscribing to the same asset_group's `candle_computed` stream) — that issue doc's own
      `[SCRIPT] P2` todo ("add a `VM_TASK == "mdps-features-live"` ... branch to `setup-data-pipeline-vm.sh`'s
      exec-dispatch section") is the actual remaining build spec, not a fresh sports-specific launcher; its
      `[OPERATOR] P2` todo (family↔asset_group mapping for the other 6 feature families) is cross-cutting and does not
      block sports specifically. (repo: market-tick-data-service confirmed working; market-data-processing-service,
      features-service, deployment-service remaining, tracked in the linked issue) **CLOSED (na-eligibility-audit
      2026-08-07)**: `/plans/archive/2026_08/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md` now
      has all 5 of its todos checked `[x]` — the `[SCRIPT] P2` exec-dispatch branch this todo named as "the actual
      remaining build spec" shipped `deployment-service@e7d17f2` 2026-08-03 ("a new `VM_TASK == \"mdps-features-live\"`
      branch discovers MDPS's (venue,data_type) shards at boot ... and generates a self-contained fan-out supervisor").
      That doc's Progress Log (2026-08-04): "All 5 todos in this issue doc are now done; plan is eligible for archival."
      A narrower `[VERIFY] P2` live-launch-confirmation follow-up remains open in that OTHER doc (added by a 2026-08-06
      audit) but is a separately-tracked step, not the build-spec work this checkbox named.
- [x] ✅ [DATA] P3. **CORRECTED 2026-07-29 (code-verified, NOT on any operator decision — was: "Build the FSS live
      handler ... currently batch-only")**: the FSS live handler for the sports feature family is NOT missing — it is
      already shipped, CLI-wired, and unit-tested. `features_service/sports/cli/handlers/live_handler.py`'s
      `LiveHandler` (PubSub source `persist-sports-odds-features-reader` + PubSub sink, same `process_sports_record()`
      engine path as batch) is dispatched via `features-sports-service --operation compute --mode live`
      (`cli/main.py::get_handler_for_mode`), tested in `tests/sports/unit/test_live_handler.py`, and shipped since
      2026-05-08 (features-service@b144552d, maintained through @1b0d1703 2026-07-27). This todo's own premise cited
      `batch-live-architecture.md` §4, which was STALE/WRONG on this point — the correct, already-existing SSOT is
      `/codex/04-architecture/features-service-architecture.md`'s "Live handler status per family" table (2026-05-14):
      sports `live_handler.py` shipped ✅, production deployment ⏳ post-cutover. §4's row + its broken cross-reference
      (pointed at a nonexistent `plans/epics/features_and_ml_master.md` p1-todo-10 — that todo ID does not exist
      anywhere in that epic) are corrected in the same pass. The genuinely remaining gap is NOT building the handler —
      it's production deployment, which is the exact same cross-cutting launcher/exec-dispatch gap the corrected Todo 3
      above already tracks (`/plans/archive/2026_08/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`
      — nothing invokes `features-sports-service --mode live` from a real launcher yet). No separate FSS-specific design
      doc is needed; tracking the deployment gap twice (here and in Todo 3) would duplicate the same open work. (repo:
      features-service — done; deployment-service — remaining, tracked in Todo 3's linked issue)
- [ ] [REVIEW] P3. Run a sports archetype through the existing CLI-primary promote workflow (`run-paper.sh` →
      `preflight-cutover.sh` → `launch-strategy-paper-vm.sh`, ≥7 days, then `run-live.sh` →
      `launch-strategy-live-vm.sh`) once it reaches `CANDIDATE` phase via a passing Group-B backtest AND the Group-C
      execution-alpha harness (decided YES-needed per
      `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md` — scoped but not yet built in
      `sports_group_c_execution_backtest_harness_2026_07_21.md`, which must land first) — no new promote-workflow
      engineering, just executing the existing chain. (repo: strategy-service, execution-service)
- [ ] [OPERATOR] P3. **STILL NEEDS YOUR OWN EXPLICIT GO-AHEAD — deliberately not defaulted, real-money live trading.**
      This is exactly the class of decision the workspace's live-trading-activation HARD RULE reserves for a human's
      personal sign-off, not something I should default or infer from adjacent rulings this session — please review the
      full Groups A-H readiness-ladder checklist directly before deciding. Final explicit go-ahead to flip sports (and
      separately, prediction, once it reaches this rung) from paper to live trading — requires the full readiness-ladder
      checklist (Groups A-H, `master_to_live_defi_2026_05_23.md`) passing for the asset group, same bar cefi/defi
      cleared. **This is the actual activation step; nothing above it authorizes live trading on its own.** **Reviewed
      2026-07-28, confirmed remains a permanent hard-stop — NOT retagged.** Flipping paper→live puts real capital at
      risk; per workspace HARD RULE this always requires a human's explicit, personal go-ahead, same as every other
      live-trading activation (cefi/defi's May-23 gate). No amount of readiness-ladder completion below removes this
      gate.

## Codex SSOTs

`/codex/04-architecture/batch-live-architecture.md`, `/codex/04-architecture/sports-batch-live.md`,
`/codex/04-architecture/sports-live-odds-connectivity.md`, `/codex/04-architecture/prediction-batch-live.md`,
`/codex/04-architecture/promote-workflow-architecture.md`, `/codex/04-architecture/backtest-groups.md`.

## Progress Log

- **na-eligibility-audit 2026-08-07**: KEEP-NA, stale items (sports tranche) — of the 4 open todos, Todo 2 (MTDS
  live-odds connector quota/second-source) and Todo 3 (mdps-features-live launcher exec-dispatch wiring) are both now
  resolved via sibling docs that shipped 2026-08-03/08-04 (`sports_live_availability_and_source_latency_2026_07_24.md`
  archived-complete; `mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md` all 5 todos done,
  `deployment-service@e7d17f2`) — flipped both `[x]` with cited evidence inline. Todo 5 (REVIEW run-promote-workflow,
  gated on the still-unbuilt Group-C execution-alpha harness) and Todo 6 (OPERATOR final go-ahead, reaffirmed permanent
  hard-stop 2026-07-28) remain genuinely open — never re-litigated per the explicit dated ruling on Todo 6. Doc stays
  `assigned_vm: NA` (2 genuine human/design-gated items remain); this is a citation-closure pass, not a
  reclassification.
- 2026-07-29: **Corrected the 4 prerequisite-piece references per operator ruling (see banner above)** — added
  `sports_live_availability_and_source_latency_2026_07_24.md`,
  `gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md`,
  `data_completion_sports_history_2026_07_24.md`, and
  `mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md` to `related:`. Rewrote the MTDS live-odds
  connector todo (connector already shipped + VM running, remaining work is the P0 shape-mismatch fix +
  quota/second-source confirmation, both cited from their owning docs). Rewrote the live launchers todo
  (`launch-mtds-live.sh` already works for sports; remaining work is the cross-cutting `launch-mdps-features-live.sh`
  exec-dispatch bug, not 2 new per-asset-group scripts). **Major finding**: the "FSS live handler" todo's premise was
  factually wrong — `features_service/sports/cli/handlers/live_handler.py` is already shipped, CLI-wired, and
  unit-tested (confirmed by direct code read + git history back to 2026-05-08), and
  `/codex/04-architecture/features-service-architecture.md` already documents this correctly; only
  `batch-live-architecture.md` §4's row + its broken `p1-todo-10` cross-reference were stale. Did NOT file the requested
  new "scope a LiveHandler" design doc (its premise — that no handler exists — is false; filing it would have introduced
  a new incorrect claim into the corpus) — instead corrected §4's row/pointer and flipped this todo to done, since the
  actual remaining gap (production deployment) is already tracked by the corrected launchers todo above. Confirmed the
  Group-C execution-alpha harness piece (`sports_group_c_execution_backtest_harness_2026_07_21.md`) is already fully
  spec'd and linked — no change made there.
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
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — explicit dated operator ruling BLK-9d3a208c in
  `source:` — 'human plan, assigned_vm: NA, NOT AO-dispatched — a plan whose terminal action is a human go/no-go on live
  trading activation is the human-plan class by construction' — reinforced by a 2026-07-29 operator banner (continue to
  hold the live go-ahead) and a permanent `[OPERATOR]` hard-stop todo reviewed + reaffirmed 2026-07-28
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — swapped generic architecture docs + the epic for
  the actual remaining blocker doc (MDPS/features live-launcher exec-dispatch) + its target script + the sibling
  live-availability plan, since 2 of the 3 remaining open todos trace back to those.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 4 open items: 1 genuine work, 2 dependency-blocked, 1 operator
  question.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-verified via
  `grep -n '^\s*- \[ \]'`: exactly 2 open todos live today (Todo 5 REVIEW, Todo 6 OPERATOR — the 2026-08-07 stale-items
  pass above already flipped Todo 2/Todo 3 `[x]` with cited evidence, so the "4 open items" tail-entry count is stale
  relative to the doc's current state, superseded by that same-day KEEP-NA-stale-items entry). This doc now carries a
  fresh dated `✅ OPERATOR RULING 2026-08-08` banner explicitly REAFFIRMING the live-trading hard-stop (Todo 6) and
  additionally sequencing it behind the sports canonicalisation chain
  (`/plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md` etc.) so it "stops surfacing as an
  unanswered operator question in every audit sweep" — an explicit dated operator ruling = KEEP-NA on citation alone,
  never re-litigated. Todo 5 (run a sports archetype through the promote-workflow CLI) remains gated on the Group-C
  execution-alpha harness landing — cross-referencing this pass's OWN sports-tranche RECLASSIFY of
  `sports_group_c_execution_backtest_harness_2026_07_21.md` (now `assigned_vm: planning`): once that harness ships, Todo
  5 becomes ripe, but is not itself reclassified this pass (still gated on unshipped prerequisite work). Doc stays NA,
  unchanged.
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — reconfirmed both open todos unchanged. Todo 5
  (archetype-through-promote-workflow) still gated on `sports_group_c_execution_backtest_harness_2026_07_21.md`,
  re-verified still `status: active` / `assigned_vm: planning` (genuinely in-flight, not stalled) — not yet shipped.
  Todo 6 (operator go-ahead for live-capital trading) is the permanent human-only hard-stop this sweep's own
  instructions require to always stay gated — reaffirmed, not retagged. No new work; doc stays `assigned_vm: NA`.
- **slot 23 (review), 2026-08-11**: **Todo 5 gate-check — Group-C harness LANDED, Group-B blocker RESOLVED → Todo 5 is
  now unblocked on both named prerequisites.** (1) Group-C execution-alpha harness: all 5 parent-plan todos in
  `sports_group_c_execution_backtest_harness_2026_07_21.md` are done with independently-reverified evidence
  (`sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md` todos 1-2, slots 9 + 26, 2026-08-11).
  (2) Group-B backtest: the only named blocker — `sports_arb_dutching_engine_not_wired_to_factory_2026_07_21.md` — is
  `status: resolved` (slot 3, 2026-07-21) and archived under `plans/archive/issues/`. This does NOT flip Todo 5's
  checkbox (that plan owns its own verdict); it records that the gates named in Todo 5's own done-when are now
  satisfied. The operator hard-stop on Todo 6 (live-capital trading) is unchanged and remains gated.
