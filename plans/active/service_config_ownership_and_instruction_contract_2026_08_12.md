---
doc_type: plan
title: >-
  Service config ownership — the instruction contract, per-service config.py, and hot reload everywhere
summary: >-
  Establishes the target the operator set 2026-08-12: the strategy↔execution contract is the INSTRUCTION (trade / swap /
  back-lay / atomic) plus a strategy-sent reference price, execution-service owns algo selection entirely via its own
  per-client config, and each service centralises schema + defaults in its own config.py with the instance in GCS and
  everything hot-reloadable including API keys. The audit behind this plan found the target much closer than expected —
  and blocked in three specific places. Already right: `StrategyInstructionEnvelope` carries `execution_policy_ref`,
  `urgency`, `eligible_venues` and `venue_constraints`, so strategy already opts into execution behaviour BY REFERENCE;
  `execution_policies.py` is already a content-hashed, versioned, first-match-wins algo rule-table gated on instruction
  action; `select_algorithm()` already accepts a config-supplied algo and validates it per instruction type;
  execution-service already hot-reloads instruments, CLIENTS and rate-limits, plus API keys. The three blockers: (1) the
  execution-policy registry has ZERO consumers, no client/slot keying, no GCS loader and no hot reload; (2)
  `reference_price` exists only on `QuoteInstruction`, so the benchmark-fill assumption that makes strategy-only
  backtests possible has no field to travel on for trade/swap; (3) strategy-service does not wire `ClientDomainConfig`
  at all, which is exactly why API keys hot-reload while a client leverage change needs a restart.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, execution-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [config, hot-reload, execution-policy, instruction-contract, per-client-isolation, backtest, service-boundary]
related:
  [
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
    /codex/04-architecture/execution-policy.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 5
assigned_role:
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12, operator statement of target architecture: "exec_algo configuration lives in execution
  service. the contract between strategy and execution is the instructions (trade, swap, back/lay, atomic etc). and
  strategy sends the ref price, execution layer marks underlying against either statically or updates as ul moves.
  execution also strategy client config tells it which algos to use for each strategy instruction type etc. so no
  execution direct config is handled by strategy at all really or shouldn't be, hence we can do strategy backtests using
  just strategy service and the upstream data from data pipeline given the benchmark fill assumption it makes." Plus:
  "hot reload for execution config same as strategy config including api keys and all other params centralised to each
  service in their config.py should be the goal."
---

# Service config ownership — instruction contract, per-service `config.py`, hot reload everywhere

> **Read the audit first (§ A).** The headline is that the ARCHITECTURE is already right and mostly built; what is
> missing is wiring, in three specific places. Do not redesign what § A marks ✅.

## Codex SSOTs

`/codex/04-architecture/execution-policy.md` (the algo rule-table contract) ·
`/codex/06-coding-standards/config-reloader-pattern.md` (typed config reloaders) ·
`/codex/04-architecture/tier-and-import-architecture.md` (no service↔service deps) ·
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md` (the ε=0 spine the ref price feeds)

## § A. Audit 2026-08-12 — how close the reality is to the target

### Already correct (do NOT rebuild)

| Target property                                                | Reality                                                                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Contract is the instruction, and strategy opts in BY REFERENCE | `StrategyInstructionEnvelope` carries `execution_policy_ref` — a reference, never the policy body. It also already carries `urgency`, `deadline_utc`, `eligible_venues`, `venue_constraints`, `venue_routing_mode`, `target_venue`, `chain`                                                                  |
| Execution owns algo selection, keyed by instruction type       | `execution_service/v2/execution_policies.py`: immutable **content-hashed, versioned** artifacts; `AppliesTo` gates on `actions` (InstructionActionV2) / `urgency` / `venue_categories` / `instrument_types`; `PolicyRule.when → then_algo + then_params`; document-order, first-match-wins, **default-deny** |
| Algo validity is per instruction type                          | `select_algorithm(instruction_type, …, config_algorithm)` already validates a config-supplied algo against UAC `ALGOS_BY_INSTRUCTION_TYPE` (8 types, different valid sets — `TRADE` 8, `ZERO_ALPHA` 1)                                                                                                       |
| Execution config hot-reloads                                   | execution-service runs **three** `DomainConfigReloader`s — instruments, **clients**, rate-limits — plus `ApiKeyReloader` (Hyperliquid) and a separate `_BybitKeyReloader`                                                                                                                                    |
| A per-client hot-reloadable substrate exists                   | UTL `ClientDomainConfig`: `active_clients` + `client_configs: dict[client_id, dict[…]]`, reloading via the `config-domain-clients` domain                                                                                                                                                                    |

### The three blockers

- **B1 — the execution-policy registry has no consumers.** `ExecutionPolicyArtifact` / `PolicyRule` appear only in
  `v2/__init__.py` re-export plumbing. No `client_id` or `slot_label` keying, no GCS loader, no hot reload; `register()`
  is in-memory. So the correct artifact exists and nothing evaluates it.
- **B2 — `reference_price` exists only on `QuoteInstruction`.** `TradeInstruction` carries `max_price`, which is a
  BOUND, not a benchmark. So "strategy sends the ref price, execution marks the underlying against it" has **no field to
  travel on** for trade/swap — and the benchmark-fill assumption that makes strategy-only backtests possible therefore
  cannot be expressed on the contract.
- **B3 — strategy-service does not wire `ClientDomainConfig`.** It runs reloaders for `StrategyDomainConfig` and
  `InstrumentDomainConfig` only. **This is the precise reason API keys hot-reload while a client leverage change is a
  restart** — the substrate is in UTL and already used next door, just not subscribed to here.

### The systemic pattern worth naming

B1 is the **third** instance found in one session of the same shape: a well-formed contract built ahead of its loader —
`WalletMappingConfig` (zero consumers), `ClientsYaml` (zero consumers), `ExecutionPolicyArtifact` (zero consumers). The
shapes being right is genuinely good news; the risk is that "declared" keeps reading as "done". Every todo below that
wires one of these must also delete or update whatever doc claims it is already live.

### Corrected in flight

- [x] [AGENT] P0. ✅ **Removed the execution section from strategy-service's param schema —
      `strategy-service@4762c211ab`, gate green (exit measured via redirect).** An earlier commit the same day
      (`664f5b42b2`) had added `exec_algo` / `exec_urgency` / `exec_max_participation_pct` / `exec_max_slippage_bps`
      there. That was wrong on the operator's correction: it created a **second source of truth** for the
      execution-policy artifact, and `urgency` was already a first-class envelope field, so the param was redundant as
      well as misplaced. Replaced with a `reference_price` section, which strategy genuinely DOES own —
      `refprice_mark_mode` (`STATIC_AT_SEND` | `UPDATE_AS_UNDERLYING_MOVES`, both operator-named modes),
      `refprice_source`, `refprice_max_drift_bps`. A regression test now fails if anyone re-adds execution config to
      strategy-service.

## § B. Make the execution-policy registry real (unblocks B1)

- [ ] [AGENT] P0. **Key execution policies by `(client_id, slot_label)`** so "execution's strategy-client config tells
      it which algos to use per instruction type" is expressible. Reuse the pair the event tag already carries; do not
      invent a third identity.
- [ ] [AGENT] P0. **Give the registry a GCS loader + `DomainConfigReloader` subscription**, so a policy change is
      dynamic rather than a deploy. Follow execution-service's existing three-reloader pattern rather than a new
      mechanism.
- [ ] [AGENT] P0. **Wire policy evaluation into the live execution path** and have `select_algorithm()` take its
      `config_algorithm` from the resolved policy. The parameter already exists and already validates per instruction
      type, so this is connection, not design.
- [ ] [AGENT] P1. **Reject an unknown `execution_policy_ref` loudly.** Default-deny is already the rule-evaluation
      semantic; make an unresolvable REF equally loud rather than silently falling back to a default algo, which would
      hide a misconfigured client.

## § C. Put the reference price on the contract (unblocks B2, and the backtest property)

- [ ] [AGENT] P0. **Add the reference price to the shared instruction envelope**, not just `QuoteInstruction` — with the
      mark mode (static at send vs updating as the underlying moves) so execution knows which to apply. This is the
      field the `refprice_*` params shipped in `4762c211ab` configure, and they are inert until it exists.
- [ ] [AGENT] P0. **State the benchmark-fill assumption in one place and cite it from both services.** It is what makes
      a strategy-only backtest legitimate; today it is an assumption with no written contract, which is how a backtest
      and live execution drift apart without anyone noticing.
- [ ] [AGENT] P1. **Prove the standalone-backtest property with a test**, not an argument: run a strategy backtest using
      only strategy-service + pipeline data, asserting no execution-service import and no execution config read. That
      test is the guard on the whole service boundary — if it ever needs execution config to pass, the boundary has
      leaked.
- [ ] [AGENT] P1. **Reconcile the ref price with the ε=0 spine.** `UPDATE_AS_UNDERLYING_MOVES` means the benchmark is
      time-varying, so a batch rerun must re-derive the same series — pin it to the same tick source and add it to the
      `paper(W) == batch-rerun(W)` assertion rather than assuming it reproduces.

## § D. Per-service config centralisation + hot reload (unblocks B3)

- [ ] [AGENT] P0. **Subscribe strategy-service to `ClientDomainConfig`.** The single highest-value item in this plan: it
      is what turns a client leverage change from a restart into a hot reload, and the substrate already exists in UTL
      and is already used by execution-service. Pair it with the param-change callback and versioned-event discipline in
      [per-client config keying](/plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md) §
      "Dynamic param updates" — a silent swap breaks the ε=0 proof.
- [ ] [AGENT] P1. **Give `client_configs` a typed schema.** It is `dict[str, dict[str, DomainConfigValue]]` — the
      transport, keying and reload are right, but the payload is an untyped bag, so nothing validates a client's
      leverage is a number in range. Type it against the governing schema so the wizard and the reloader agree.
- [ ] [AGENT] P1. **Resolve execution-service's missing `config.py`.** The operator's goal is schema + defaults in each
      service's `config.py`; execution-service has **no such file** — its typed config is
      `service_config.py::ExecutionServicesConfig(UnifiedCloudConfig)`. Decide rename-vs-document and apply it
      consistently across services, so "look in config.py" is true everywhere or nowhere.
- [ ] [AGENT] P1. **Close the Bybit API-key reload asymmetry.** Hyperliquid reloads via the shared `ApiKeyReloader`;
      Bybit needs a bespoke `_BybitKeyReloader` because UAC's `DATA_SOURCE_TO_SECRET` registry cannot express it. Fix
      the registry so one mechanism serves both — two reloaders for the same job is how one of them silently stops being
      maintained.
- [ ] [AGENT] P2. **Inventory every remaining `config.py`-shaped knob per service** and state, per knob, whether it is
      hot-reloadable. The goal is "everything centralised and hot-reloadable"; without the inventory there is no way to
      say how far along that is, and partial coverage reads as full coverage.

## § G. Execution-service change surface — measured 2026-08-12, exhaustive

> Operator asked to be "fully sure even for the execution service stuff what the changes needed are". This section is
> that answer. **The headline: the benchmark-fill architecture — the load-bearing piece — is already built, and only
> three things are genuinely missing.**

### Already built, and better than expected

| Capability                          | What exists                                                                                                                                                                                                                                                                                                                              |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **The benchmark fill itself**       | `BenchmarkMatcher` with `BookType.ALPHA_ZERO`, **always-fill** — the benchmark-fill assumption is implemented, not assumed                                                                                                                                                                                                               |
| **The two-layer attribution split** | `pnl_attribution/rows.py` builds rows from a PAIR of (benchmark, live) `MatchResult`s: **STRATEGY layer** = benchmark-fill decomposition at benchmark price (delta/funding/basis/carry/financing/greeks/settlement/fx); **EXECUTION layer** = `live_fill − benchmark_fill` residual → `SLIPPAGE` + `FEES` (surprise = actual − modelled) |
| **Slippage**                        | Computed, correctly signed and layered: `slippage = sign * (benchmark.fill_price - live.fill_price) * filled_quantity`, emitted as `PnLFactor.SLIPPAGE` / `PnLLayer.EXECUTION`                                                                                                                                                           |
| **Alpha, with statistical rigour**  | `benchmark/metrics.py` (328 lines): `StatisticalMetrics` (mean, std, standard error, 95% CI, `ci_width`, `is_reliable`) and `PathAwareMetrics` (`early_alpha_bps` / `mid_alpha_bps` / `late_alpha_bps` + `cumulative_alpha_curve`)                                                                                                       |
| Surrounding benchmark tooling       | `comparison.py`, `enhanced_comparison.py`, `ranking.py`, `regimes.py`, `storage.py`, `html_report.py`                                                                                                                                                                                                                                    |

**Why this matters more than any other finding in the plan**: the STRATEGY-layer / EXECUTION-layer split is _exactly_
why a strategy-only backtest is legitimate. The strategy-attributable PnL is computable at benchmark price with no
execution involvement; everything execution adds or destroys is the residual. That is the property the service boundary
exists to protect, and it is already implemented rather than aspirational.

### The three real gaps

- [ ] [AGENT] P0. **G1 — feed `config_algorithm`; nothing supplies it.** The hook is threaded through THREE levels —
      `selector.select_algorithm(instruction_type, requested_algorithm, config_algorithm)`, the
      `HandlerRegistry.select_algorithm()` wrapper that forwards it, and validation against `ALGOS_BY_INSTRUCTION_TYPE`
      — and **zero call sites supply it** (the only `requested="TWAP"` is a docstring example, not live code). So the
      change is: resolve the per-`(client_id, slot_label)` policy, pass its `then_algo` as `config_algorithm`. **No new
      plumbing** — the parameter, the validation and the fallback chain already exist.
- [ ] [AGENT] P0. **G2 — add instruction-level `received_at` / `sent_at`; latency is the ONLY missing analytic.** Alpha
      and slippage are built; latency has nothing to compute from. The timestamps that exist are unrelated —
      `received_at_mark_price_eth` (restaking rewards), `token.received_at_utc` (dust quote sources), `submitted_at` (an
      order-adapter idempotency cache). **There is no instruction-level received/sent pair in either service.** Both
      sides need it, per the operator, so define it once in UAC on the envelope and the fill record rather than twice.
- [ ] [AGENT] P0. **G3 — reconcile WHO owns the benchmark price, because today both sides could.** execution-service
      currently derives its own benchmark via `BenchmarkMatcher`; the target has **strategy sending the ref price**. If
      both compute independently they can disagree on the benchmark itself, which would silently break the
      backtest-vs-live comparison while every individual number still looks right. So § C's envelope field is not
      plumbing — it is what makes the two sides' benchmark provably identical. Decide: strategy-sent is authoritative
      and `BenchmarkMatcher` consumes it, or `BenchmarkMatcher` stays authoritative and strategy's ref price is
      advisory. **Recommendation: strategy-sent is authoritative**, since the whole point is that the strategy's own
      assumption is what its backtest was measured against.

### Smaller execution-service items

- [ ] [AGENT] P1. **Unify the algo vocabulary — there are two.** `engine/instruction_convert.py` does
      `algorithm = (algo or "MARKET").upper()`, and **`"MARKET"` does not exist in UAC `EXECUTION_ALGOS`** at all; it
      also re-implements TWAP slicing params inline. That is a second naming system on the manual-instruction path,
      invisible to the selector's validation. Either register the manual path's names in UAC or route it through the
      selector.
- [ ] [AGENT] P1. **Wire the execution-policy evaluator** (see § B) — `ExecutionPolicyArtifact` / `PolicyRule` appear
      only in `v2/__init__.py` re-export plumbing, so the rule evaluator that already implements first-match-wins /
      default-deny is never called.
- [ ] [AGENT] P2. **Confirm the benchmark module's own consumers.** `metrics.py` is imported only by its siblings
      (`enhanced_comparison.py`, `ranking.py`) — verify the chain reaches a live/reporting caller rather than
      terminating in the benchmark package, so the alpha metrics are actually surfaced somewhere.

## § E. Codex reconciliation (do AFTER § B–D land, per operator sequencing)

- [ ] [AGENT] P1. **Update `/codex/04-architecture/execution-policy.md`** to state the `(client_id, slot_label)` keying
      and the loader/reload story once § B lands — and to say plainly that the registry was declared-but-unwired until
      then, so the doc stops implying a live mechanism.
- [ ] [AGENT] P1. **Write the service-boundary contract into codex**: instruction + reference price is the whole
      surface; execution config never crosses; the standalone-backtest property is the test of it. No codex doc
      currently states this in one place, which is why it took a code audit to answer.
- [ ] [AGENT] P2. **Reconcile `/codex/06-coding-standards/config-reloader-pattern.md`** against the measured reality —
      three reloaders in execution-service, two in strategy-service, and the per-service `config.py` inconsistency.

## § F. Artifacts (do LAST, per operator sequencing)

- [ ] [AGENT] P2. **Update the three artifacts once § B–E land.** Operator instruction: artifacts follow plans and
      codex, never lead them. The service-boundary story is genuinely good material — the contract is narrow and the
      standalone-backtest property is a real engineering claim — but it must describe what is wired, so it cannot be
      written until § B–D are done. Artifacts: platform overview, carve-out spec, deep dive.

## Progress Log

- **2026-08-12** — Authored from the operator's statement of target architecture plus a same-session audit. The audit's
  most useful result was negative: **almost nothing here needs designing.** The envelope already opts in by reference,
  the policy artifact is already content-hashed and versioned with the right gating axes, the selector already validates
  per instruction type, and execution-service already hot-reloads three domains including clients. Three gaps do the
  damage, and B3 (strategy-service not subscribing to `ClientDomainConfig`) is a one-line-shaped fix behind a
  determinism requirement. Also corrected a same-day error of mine: execution params had been added to
  strategy-service's param schema hours earlier and are now removed (`strategy-service@4762c211ab`) with a regression
  guard, because they competed with the execution-policy artifact for the same responsibility.
