---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 1 strategy-service risk/HWM compose (CRITICAL)
summary:
  Compose (not delete) strategy-service's 3 risk-computation engines with UTL's rule-aggregation gate — dedupe the twin
  threshold/equity helper, migrate the legacy portfolio-gate branch to UTL RiskRules, route comparison checks through
  UTL rules.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, risk, hwm, split]
related:
  [
    plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md,
    plans/active/utl_reuse_phase0_guardrails_2026_07_13.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on: [utl_reuse_phase0_guardrails_2026_07_13]
gate_on_depends: true
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend_engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 1 strategy-service risk/HWM (CRITICAL) — COMPOSE, do not delete

> **Split provenance (2026-07-13):** Phase 1 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (finding #1, CRITICAL). One item already shipped there (`strategy-service@67ecc156`, the `account_equity_proxy()`
> constant-5.0-leverage bug fix) — reproduced below as done. **Machine-held** until
> [`utl_reuse_phase0_guardrails_2026_07_13.md`](utl_reuse_phase0_guardrails_2026_07_13.md) lands its golden risk-eval
> fixture (`depends_on` + `gate_on_depends: true`).

> **Verified reality:** the three "duplicate engines" are the metric-**computation** layer; UTL `risk.rule_evaluator` /
> `risk_preflight` / `family_aggregator` is the **comparison/aggregation** layer (every input arrives pre-computed in
> `RuleEvalContext`). All three local engines are LIVE and feed the UTL gate — they are NOT superseded. UTL HWM
> (`post_trade.hwm_invariants`/`hwm_periods`) is **fee-crystallization HWM**, a different domain from the equity-curve
> drawdown peak — do **not** collapse them.

**Guiding rule (CLAUDE.md conflict-resolution SSOT):** _Align = the MERGED COMBINATION, never "take mine / take
theirs"._ Where two implementations both carry genuine work, keep both; where one is a strict superset, adopt it and
preserve the residual; where the lib lacks a load-bearing local control, extend the lib first, then delete local.

## Todos

- [x] ✅ [AGENT] P0. **Dedupe the twin threshold/equity helper.** `risk/core/risk_calculator.py` and
      `risk/engine/risk_metrics.py` carry near-identical `get_threshold_status` + equity/concentration/peak computation.
      Collapse to ONE shared pure helper (keep the **stateless** `risk_metrics` form for batch=live symmetry); have
      `RiskCalculator.calculate_drawdown` wrap it with its per-`client_id` peak dict. Preserve: per-client peak store,
      UAC `RiskMetrics`/`RiskStatus` assembly, `assert_client_allowed`. — SHIPPED `strategy-service@2b2e326c` |
      `get_threshold_status`/`compute_drawdown` extracted as shared pure helpers in `risk_calculator.py`;
      `risk_metrics.py` imports them (no more inline reimplementation); `account_equity_proxy` gained the
      `max_leverage<=0` guard `risk_metrics.py` already had, for behaviour parity | full risk suite (718 tests) + Phase
      0 golden fixture green | `quality-gates.sh` exit 0, sentinel verified.
- [x] ✅ [AGENT] P0. **Migrate the one genuine same-layer duplication — RE-SCOPED 2026-07-13 (slot-13).** Original
      wording assumed daily-loss/drawdown/family-cap were all cleanly migratable + that
      `MaxDailyLossTrigger`/`MaxDrawdownTrigger`/a family-cap trigger needed to be CREATED. Investigation found: **(1)**
      `MaxDailyLossTrigger`/`MaxDrawdownTrigger` already exist, pre-seeded at `PER_ACCOUNT` scope in
      `unified-api-contracts/registry/risk_rules/account.py` — no UAC-side work needed. **(2)**
      `FAMILY_GROSS_EXPOSURE_CAP`/ `FAMILY_NET_EXPOSURE_CAP` also already exist at `PER_STRATEGY_FAMILY` scope — but
      `PortfolioContext.family_exposure_cap_usd` is keyed by `StrategyFamily` (strategy-architecture-v2 **mechanism**
      axis, e.g. `VOL_TRADING`) while the registry's family rules are keyed by `StrategyFamilyId` (the
      **risk-aggregation** axis, e.g. `LST_LEVERAGE_FAMILY`) — a documented, non-overlapping taxonomy with no mapping
      between them. Family-cap is NOT a migratable duplicate (verified NON-finding) — kept local-only, do not re-flag in
      a future reuse audit. **(3)** `_run_legacy_portfolio_gates` has ZERO production callers
      (`FourLayerGateOrchestrator` is unused scaffolding); its only spec is `tests/risk/unit/v2/test_v2_risk.py`, which
      encodes DYNAMIC caller-supplied thresholds (`PortfolioContext.max_daily_loss_usd`/`max_drawdown_bps` set per-call)
      — a fundamentally different threshold-sourcing model from the registry's STATIC per-account seeds. Given no live
      caller depends on the dynamic values, composed (not replaced) per the plan's own "COMPOSE, do not delete" rule:
      when the (new) `account_id` param is supplied, the registry's `PER_ACCOUNT` daily-loss/drawdown seeds now evaluate
      ADDITIONALLY as a static safety-net floor (most-restrictive wins, existing REJECTED>RESIZED>APPROVED composition),
      while the dynamic local check stays for the caller's own tighter operational limit. `_run_legacy_portfolio_gates`
      itself is UNCHANGED (still runs daily-loss/drawdown/family-cap) — it was never actually deletable to
      "recon-staleness only" because the dynamic-threshold behavior has no registry equivalent. Also fixed a
      pre-existing latent bug in passing: `run_layer2_preflight` was passing `family.value` (mechanism axis) as
      `strategy_family_id` to the registry lookup — silently never matched any `PER_STRATEGY_FAMILY` rule; now passes
      `None` explicitly with a comment, since no valid mapping exists. Shipped `strategy-service@0beadebe` (4 new
      composition tests + 1 existing-test-adjustment, `basedpyright` clean, 731 pre-existing risk tests + golden fixture
      still green). **Separate finding filed, not fixed in this todo** (cross-repo, outside this plan's
      `repos:     [strategy-service]`): `GLOBAL_DATA_STALENESS_HALT` misuses `MaxDrawdownTrigger(cap_bps=1)`, colliding
      with the real `current_drawdown_bps` field my `account_id` composition now populates — latent kill-switch
      false-positive risk once real drawdown data is wired into execution-service's live order path. See
      `plans/active/issues/global_data_staleness_halt_drawdown_field_collision_2026_07_13.md`
      (`unified-trading-pm@8acd22e5d`).
- [x] ✅ [AGENT] P0. **Route the 6 comparison checks through UTL rules — PARTIAL, RE-SCOPED 2026-07-13 (slot-10).**
      Investigation (escalated via `/blocked` BLK-9db4a748, main's ruling) found: (1) the plan text is internally
      inconsistent — headline says "6 comparison checks" but the body names only 5
      (`position_size/leverage/gross/net/concentration`); (2) `concentration` has no already-computed source in
      `pre_trade_check_engine.py` (no percentage-of-NAV computation exists anywhere in the file today) — routing it
      would mean inventing new, unspecified NAV/equity-proxy logic on a CRITICAL pre-trade gate, not wiring through an
      existing value; (3) routing threshold **numbers** from the static per-axis UAC registry
      (`unified_api_contracts.risk.iter_applicable_rules`) — the literal reading of "UAC caps" — would silently change
      pre-trade enforcement (e.g. `binance` `MAX_POSITION_SIZE_PER_VENUE`=$20,000,000 vs the Phase 0 golden fixture's
      `RiskLimits.max_position_size`=100 raw units) and drop the check entirely for unregistered clients/venues (no
      fallback), breaking this plan's own "Golden risk-eval identical" acceptance gate. Main's ruling: unify the
      COMPARISON DISPATCH via ad-hoc UAC-typed `RiskRule` objects built per-call, sourcing cap **values** from the
      existing `RiskLimits` config (not the static registry) — same `evaluate_rule` path `risk_preflight_gate.py`
      already uses, preserving the golden-fixture numeric output exactly. SHIPPED for the 4 checks with a clean 1:1 UAC
      `RiskRuleTrigger` match: `position_value` (`MaxPositionSizeTrigger`), `leverage` (`MaxLeverageTrigger`),
      `gross_exposure` (`MaxGrossExposureTrigger`), `net_exposure` (`MaxNetExposureTrigger`) — deleted the superseded
      raw-`>`-comparison for these 4, no parallel old+new path — `strategy-service@1cc449d3` | `quality-gates.sh` exit 0
      (sentinel verified) | Phase 0 golden fixture green (unchanged — cap sourcing preserved) | 731 pre-existing risk
      tests green. **Kept local by design** (no matching UAC trigger type): raw-quantity `position_size` (units, not
      USD), `margin_ratio` (no `MinMarginRatio` trigger in UTL's closed union). **Deferred as a follow-up SPEC todo**
      (not silently dropped): `concentration` + the "6 vs 5" count resolution — see
      `plans/active/issues/pre_trade_check_engine_utl_routing_concentration_gap_2026_07_13.md`.
- [x] ✅ [AGENT] P0. **Fix the local quality bug found in passing** — SHIPPED `strategy-service@67ecc156` | 60 risk
      tests ✓ | basedpyright 0 ✓ | full `quality-gates.sh` exit 0 ✓ | regression:
      `tests/risk/unit/test_pre_trade_check_engine.py::test_leverage_estimate_is_upnl_sensitive_not_constant`.
      `pre_trade_check_engine.py:579` used a hardcoded `equity = new_position_value / Decimal("5")` proxy → made
      leverage a **constant 5.0** for every book, so `leverage > max_leverage` could never fire. Extracted
      `account_equity_proxy()` in `risk_calculator.py` as the equity-formula SSOT (`value/maxlev + uPnL`, floored at 1);
      both `RiskCalculator.estimate_account_equity` and the pre-trade engine now use it; pre-trade bases equity on the
      **post-trade** value (neutral uPnL → `leverage == max_leverage` baseline preserved; negative uPnL → higher
      leverage → can breach). **This also delivers the first slice of the P0 "dedupe twin equity helper" above** (the
      equity-proxy formula is now single-sourced).
- [x] ✅ [AGENT] P1. **Extract one local `equity_curve_drawdown()` helper** for the duplicated peak/max-drawdown loop in
      `engine/core/components/pnl_monitor.py:214-222` and `engine/core/output_builders.py:153-158`. Keep it **local**
      (do NOT route to UTL `hwm_invariants` — wrong domain). Leave fee-crystallization HWM to UTL `post_trade`. —
      SHIPPED `strategy-service@12dc136c`. Added `MetricsCalculator.equity_curve_drawdown()` to `math_utilities.py`
      (returns `(peak_so_far, drawdown_fraction)` per point — a superset shape of the existing numba
      `calculate_max_drawdown()`, which only returns the aggregate + indices and can't serve
      `build_net_equity_timeseries`'s per-row running-HWM need). `PnLMonitor._compute_drawdowns` now derives
      `max_drawdown` via `max(dd for _, dd in ...)`; `build_net_equity_timeseries` derives its per-row peaks by seeding
      the walk with `initial_capital` and dropping the seed entry — both verified bit-identical to the original
      hand-rolled loops via new regression tests (4 for the helper in `test_math_utilities.py`, 4 for
      `PnLMonitor._compute_drawdowns` in new `test_pnl_monitor_drawdown.py`) plus the existing
      `test_output_builders.py`/`test_math_utilities.py` suites (all green) and the Phase 0 golden risk-eval fixture
      (reproduces identically). Local only — did not touch UTL `hwm_invariants`. `quality-gates.sh` exit 0, sentinel
      verified.
- [x] ✅ [AGENT] P2. **Keep `risk/core/correlation_matrix.py` (instrument NxN) as-is — VERIFIED NON-FINDING, optional
      cleanup declined.** Confirmed UTL `family_aggregator.aggregate_family_state` operates on a coarser,
      genuinely-different axis: it buckets archetypes into `StrategyFamilyId` groups, mean-collapses each family's
      `last_returns_30d` into one series, then Pearson-correlates _between families_ into a
      `cross_family_correlation: dict[StrategyFamilyId, float]` fan (not a full symmetric matrix).
      `correlation_matrix.py` is a dense `list[list[float]]` N×N over raw instruments — same "documented,
      non-overlapping taxonomy" pattern already verified for the family-cap NON-finding above (todo 2). No migration
      possible; kept local, do not re-flag. **Optional 3-shape cleanup investigated + declined**: the "3 local
      correlation shapes" are not really duplicative — (1) the instrument-matrix (`correlation_matrix.py`) has ~0
      production consumers (only its own unit test; the Monte-Carlo-VaR wiring the docstring claims doesn't exist); (2)
      the "family-pairwise-dict" (`CorrelationConfigLoader` + `RiskGroupAggregator`) is also unwired in production (the
      `correlation_matrix_json` config field has no instantiation site) and exposes a `Callable[[str,str], Decimal]`
      interface, not a dict — a real API shape difference, not just typing; (3) the "v2 nested-dict" is the only one
      with live production callers (`portfolio_allocator/guard_rails.py` → `service.allocate(correlation=...)`, a real
      external-facing kwarg) and its sibling `risk/v2/correlation_cap.py` — these two already share the identical
      `Mapping[str, Mapping[str, Decimal]]` shape, just with independently-implemented symmetric-lookup helpers (the one
      genuine, but purely cosmetic, dedup opportunity — not attempted here, no behavioural gain). Forcing all 3 into one
      type would require redesigning `RiskGroupAggregator`'s constructor contract or touching `service.allocate`'s
      public kwarg, for zero behavioural benefit — declined per this plan's own "no regressions for no gain" pattern. No
      code change; no quickmerge required (pure verification).
- [x] ✅ [VERIFY] P0. Golden risk-eval fixture from Phase 0 reproduces identically; `quality-gates.sh` green; ship via
      quickmerge. — VERIFIED (2026-07-13, slot-5) against `strategy-service@10943bfd`: pure verification, no code change
      needed. `tests/risk/unit/test_golden_fixture_phase0_risk_eval.py` passes; full `tests/risk/` suite (722 passed, 1
      skipped). Full `quality-gates.sh` exit 0, sentinel verified against `10943bfd`. First attempt hit a transient
      wall-clock resource-budget gate failure (672s > 300s) from shared-host QG contention (multiple slots running full
      QG concurrently) — re-ran once contention cleared, clean pass. This closes out
      `utl_reuse_phase1_strategy_risk_hwm`'s final todo; all 6 todos now done.

## Success criteria

Golden risk-eval identical; 3 engines compose with UTL gate; the `/5` bug fixed; no `max(equity)` collapsed into UTL
HWM.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE) — one checkbox per `quickmerge`.
- Full severity ledger + verified NON-findings list: see the tracker doc.
