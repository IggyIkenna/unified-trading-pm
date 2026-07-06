---
doc_type: plan
title: Foundation gate sign-offs + capture-to-100% (Stages 4-5, cefi-first) — AO Plan 5
summary:
  The Layer-2 completion work once the denominator is honest — formalize the cefi foundation spine (reconcile the heavy
  checkbox-vs-reality drift and take the G2-G5 sign-offs, do NOT redo what already ran) and drive capture toward 100%
  (DeFi risk_params handler, the DEDUP folded-in tail, the defi completeness oracle design, the cross-AG never-seeded
  backlog check). One item runs EARLY and ungated — the systemic unregistered-handler audit — because Plan 4's
  re-measure depends on it (a built-but-unwired handler must not read as a real coverage gap). The rest is Layer-2 and
  waits on the Stage-3 certification (Plan 4), enforced by the per-task PREREQ note. Source detail lives in
  instruments_foundation_completeness + data_completion_to_100_all_ag.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [foundation-gate, capture, layer-2, cefi-first, handler-audit, risk-params, oracle, instruments-completion]
related:
  [
    instruments_completion_tracker_2026_07_06.md,
    instruments_foundation_completeness_2026_06_24.md,
    data_completion_to_100_all_ag_2026_06_21.md,
    prediction_venue_perps_and_live_clob_depth_2026_06_20.md,
    ../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# Foundation gate sign-offs + capture-to-100% (Stages 4-5) — AO Plan 5

> **🤖 AO PLAN 5 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Sonnet / high.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stages 4-5).
>
> **⚖️ The one law — Layer-1 gates Layer-2.** Everything here EXCEPT the handler audit is Layer-2 (capture) or a
> foundation sign-off that reads the certified numbers, so it **PREREQs on the Stage-3 certification (Plan 4)** — do not
> chase capture % before the denominator is certified honest. This plan is deliberately **NOT machine-gated
> (`gate_on_depends`) on Plan 4** because the handler audit must run BEFORE Plan 4's re-measure (gating it on Plan 4
> would deadlock) — ordering is by the per-task `PREREQ:` note, enforced by the review agent.
>
> **Foundation = reconcile, NOT redo.** `instruments_foundation_completeness` has heavy checkbox-vs-reality drift — much
> of G2/G3 actually ran. Grep-verify what already happened before working an item; the job is reconciling + signing off,
> not re-running.
>
> **Worker guards (HARD):** (1) **grep-then-READ, not grep-then-conclude** — a foundation checkbox that looks open may
> already be done. (2) **smoke-first** on any backfill/re-capture; **backfill VMs default SPOT**; no fire-and-forget.
> (3) capture-correctness is the heartbeat — an audit's issues are fixed in FULL; only operator-gated BLOCKED-\* defer.
> (4) ship via quickmerge; flip + Progress-Log in the same turn.

## Codex SSOTs (read before touching)

- `codex/02-data/honest-coverage-model.md` — two-layer / instrument-gates-download model.
- `codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`; `source=` crosscutting; never
  silent placeholders; single-walk discipline.

## Run EARLY + ungated (Plan 4 depends on this)

- [x] ✅ [SCRIPT] P0. **Systemic unregistered-handler audit** (generalizes the Deribit C5 bug). Diff every handler class
      in `market-tick-data-service/.../cli/handlers/` against the `operations={…}` dispatcher keys in `cli/main.py` to
      find handlers **built but never wired** (silent `captured=0`). The MTDS QG live-coverage roll-up flags
      `blocked-not-registered` counts (cefi 104 · defi 1225 · sports 70 · tradfi 40). Distinguish **built-but-unwired**
      (fix like C5 — register + regression test) from **genuinely-not-built** (new handler / honest-absence). **PREREQ:
      none — run FIRST.** Gate: every built handler is either wired (with a test) or filed; feeds Plan 4's re-measure so
      a wiring bug is not mislabelled a coverage gap. — `market-tick-data-service@015abaf5` (register both handlers) +
      `market-tick-data-service@efd658c8` (regression tests) + Progress-Log entry with the venue-WSFeedConnector
      follow-up finding.
- [x] ✅ [SCRIPT] P1. **Follow-up — venue-level WSFeedConnector registration audit** (surfaced by the C5 handler audit,
      2026-07-06). The blocked-not-registered counts cited above (cefi 104 · defi 1225 · sports 70 · tradfi 40) are
      classified by `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py::check_live_l1` — a DIFFERENT
      bug class from the operations-dispatcher C5 (per-VENUE `WSFeedConnector` factory, not per-HANDLER operation key).
      The C5 audit closed 2 handler-registration gaps but does NOT reduce those cell counts. Audit
      `_live_connector_factories` / venue key coverage per asset_group; distinguish `built-but-unregistered` (add to
      factory registry + regression test) from `genuinely-no-connector-yet` (file). Gate: every VENUE with a canonical
      batch expected_unattempted cell is either wired to a WS factory (with a test) or filed. **AUDIT DONE 2026-07-06
      (Opus, slot-4)**: 31 registered venue keys after `register_all()`; 73 unregistered venues (cefi 13 · tradfi 4 ·
      defi 49 · sports 7 · prediction 0) cross-verified against UAC `VENUES_BY_ASSET_GROUP` via the smoke-matrix's own
      `resolve_live_venue_key`; cell counts match the QG roll-up (1,439 = 104 + 1225 + 70 + 40). **0 built-but-
      unregistered** (the 11 "unregistered" `_ws.py` files are all data-type-specific helpers imported by their base
      venue's factory — the C5-class bug does NOT recur at the WS layer). Filed as
      `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` with per-AG actionable todos (bare-venue triage,
      per-venue build, DeFi live-connector naming policy, BLOCKED-CREDENTIALS scaffolds).

## Foundation gate sign-offs (cefi-first — reconcile drift, take the sign-offs)

- [ ] [CODE] P1. **cefi G1.2** — `record_failed` routing + the 2026-06-26 re-capture (foundation §G1.2). Gate:
      `record_failed` routes correctly; the 06-26 re-capture cells reflect real status.
- [ ] [DATA] P1. **cefi G1.3 follow-up** — the on-chain-CeFi-perp venue FORM issue (foundation finding 2026-06-27).
      Gate: on-chain-CeFi-perp venues carry the canonical venue form.
- [ ] [SCRIPT] P0. **G2 → G5 reconcile + sign-off (cefi)** — G2 (backfill all venues×days×years, observable), G3
      (aggregate + scheduler-runs-latest-code), G3b (dated instruments `available_to`=venue-truth + expiry oracle), G4
      (MTDS filters the catalogue per-day), G5 (cefi MTDS coverage rises day-by-day via SSOT). **Reconcile the drift
      first (much already ran), then take the formal sign-offs.** **PREREQ: Plan 4 certified cefi Layer-1.** Gate: G2-G5
      signed off with evidence; no redo of already-run work.
- [ ] [DESIGN] P1. **DeFi completeness ORACLE design** — "do we have ALL instruments?" = on-chain truth (foundation
      §DeFi oracle). Gate: an oracle design that answers defi could-exist completeness from chain state, not the
      manifest.

## Capture to 100% (Layer-2 — PREREQ: Plan 4 certified Layer-1)

- [ ] [CODE] P1. **DeFi `risk_params` MTDS handler** — 193,042 `expected_unattempted` cells with no handler today.
      Build + register + regression test (avoid the C5 unwired class). **PREREQ: Plan 4 (defi Layer-1 certified) + the
      handler audit above.** Gate: `risk_params` captures; the 193k EU cells resolve to captured or honest-absence.
- [ ] [DATA] P1. **Reconcile the DEDUP-flagged folded-in tail** (from the merged `path_to_100pct` → `data_completion`) —
      **do NOT double-run.** **PREREQ: Plan 4.** Gate: the folded-in tail reconciled; no duplicate capture.
- [ ] [VERIFY] P2. **2e follow-on — cross-AG never-seeded backlog check (cefi / tradfi / pred)** — the scan-only
      investigation split from the defi 2e seeding (Plan for defi already shipped +1.38M). Scan only; file findings.
      Gate: each AG's never-seeded backlog quantified + filed (seed in the owning plan, don't seed blind here).
- [ ] [CODE] P1. **Prediction live token-universe fix** — live=0 today; the stale IS token universe. **Owned by
      `prediction_venue_perps_and_live_clob_depth_2026_06_20`** — this is a cross-plan pointer; coordinate, don't
      duplicate. Gate: prediction live token universe refreshed; live capture > 0.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — **✅ Task 010 DONE — WSFeedConnector venue-level audit filed as issue** (Opus, slot-4). Ran
  `register_all()` on `mtds@HEAD` (post C5 fix); 31 registered venue keys. Cross-referenced UAC `VENUES_BY_ASSET_GROUP`
  via the smoke matrix's own `resolve_live_venue_key`
  (`e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py:201`): **73 unregistered venues** total — cefi 13
  · tradfi 4 · defi 49 · sports 7 · prediction 0. Cell counts reconcile exactly to the QG roll-up: 13·8=104
  - 49·25=1225 + 7·10=70 + 4·10=40 = 1,439 `blocked-not-registered` cells. **0 built-but-unregistered** — the 11
    `_ws.py` files on disk that `register_all()` doesn't import are ALL data-type-specific helpers imported by their
    base venue's factory (binance_futures_book_ticker_ws → binance_futures_ws; deribit_book_ticker_ws → deribit_ws;
    hyperliquid_l2book_ws + hyperliquid_ticker_ws → hyperliquid_ws; kalshi_trades_ws → kalshi_clob_ws;
    polymarket_trades_ws → polymarket_clob_ws; coinbase_book_ws → coinbase_spot_ws; bybit/kraken/okx `_book_ticker`
    variants → their base modules; tardis_machine_ws is intentional opt-in fallback). The C5-class bug does NOT recur at
    the WS layer. **Filed** `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` with per-AG actionable todos
    (bare-venue triage · per-venue build · DeFi live-connector naming policy call · BLOCKED-CREDENTIALS scaffolds).
    **Interpretation for Plan 4:** the 1,439 `blocked-not-registered` cells are a live-transport rollout gap, not a
    wiring bug — Layer-2 capture % should not be dragged down by them if the underlying batch REST capture is
    honest-complete.
- **2026-07-06** — Systemic unregistered-handler audit (item 1) **shipped**. Grep-audited the 34 `class *Handler`
  classes under `market_tick_data_service/cli/handlers/` against the 32 keys in `ServiceBootstrap(operations={…})` in
  `market_tick_data_service/cli/main.py`. Found 2 unwired handlers, both C5-class (built + unit-tested but missing from
  the dispatcher): `BookMicrostructureHandler` (cefi Phase D P2b, derives `order_flow_imbalance` from L5
  `book_snapshot_5`; queue_position + depth_of_book_10 stay honest-gap) and `GovernanceProposalsHandler`
  (defi_simulation_realism Phase 4A, writes UAC `GovernanceProposal` rows for Aave V3 / Compound V3 / Spark / Lido).
  Registered as `derive-book-microstructure` and `collect-governance-proposals` + two regression tests mirroring
  `test_deribit_options_chain_operation_registered` — `market-tick-data-service@015abaf5` (register both handlers) +
  `market-tick-data-service@efd658c8` (regression tests). Zero GENUINELY-NOT-BUILT handlers found in `cli/handlers/`;
  audit Gate met.

  **Follow-up finding (filed as new plan todo above)**: the plan cited the QG batch+live smoke-matrix
  `blocked-not-registered` counts (cefi 104 · defi 1225 · sports 70 · tradfi 40) as the motivating signal, but a code
  read of `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py::check_live_l1` shows those cells are
  classified by per-VENUE `WSFeedConnector` factory registration (`no WSFeedConnector registered for venue`), NOT by the
  operations-dispatcher C5 class this audit covers. Running the QG after the two-handler fix confirms the counts are
  unchanged: cefi 104 / defi 1225 / sports 70 / tradfi 40. Those counts will only fall after a per-VENUE WS-connector
  audit — captured as the P1 follow-up todo above so Plan 4's re-measure interprets them correctly (they are a
  live-transport gap, not a handler wiring bug).

- **2026-07-06** — Plan authored + dispatched to AO (Plan 5 of the instruments-completion set). Combines Stage-4
  foundation sign-offs (reconcile, not redo) + Stage-5 capture-to-100% data work. The unregistered-handler audit runs
  early + ungated (Plan 4 depends on it); the rest PREREQs on Plan 4's Layer-1 certification.
