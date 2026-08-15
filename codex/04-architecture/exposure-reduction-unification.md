---
doc_type: codex-ssot
title: Exposure Reduction — one mandate, three triggers, one executor
summary:
  Close-all, flatten-on-producer-silence and margin deleverage are the same operation at three points on one axis. This
  is the SSOT for unifying them onto a single UAC mandate contract and a single execution-service reducer, and the
  migrate-then-delete order for the four fragmented implementations that exist today (three of which are unreachable).
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [risk, flattening, deleverage, close-all, positions, inert-code, ssot-consolidation]
related:
  [
    /plans/active/producer_silence_flatten_protocol_2026_08_14.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/tier-and-import-architecture.md,
  ]
created: 2026-08-15
authoritative_for: [exposure-reduction mandate model and the close-all/flatten/deleverage consolidation order]
referenced_by:
owner:
last_reviewed: 2026-08-15
code_refs:
  [
    execution-service/execution_service/algo_library/,
    strategy-service/strategy_service/position/,
    strategy-service/strategy_service/close_all/,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/flatten_readiness.py,
  ]
---

# Exposure Reduction

## The problem this resolves

Measured 2026-08-15. Four separate mechanisms exist for "reduce our exposure". **Three of them cannot run**, and no two
share a vocabulary:

| Concern                                       | Where it lives                                          | Reachable today?                                                      |
| --------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------------------- |
| Cross-venue positions, risk groups, net delta | `strategy_service/position/` (PBMS)                     | Yes — but **CO-LOCATED** in strategy-service (see below)              |
| Margin-triggered deleverage tactics           | `execution_service/algo_library/deleverage_executor.py` | **No** — `handle()` has no caller, no subscriber, no order path       |
| Close-everything scripts                      | `strategy_service/close_all/`                           | Partially — 2 concrete subclasses, `current_positions` is an ARGUMENT |
| Local position cache                          | `execution_service/engine/live/positions.py`            | Yes, but fed by its OWN fills — not a truth source                    |
| Flatten semantics                             | UTL `ledger/materialize.py` + strategy-service fills    | Two duplicated frozensets, ledger-side only                           |

The failure mode is not that any one of these is wrong — each is individually reasonable and individually tested. It is
that **"reduce exposure" has no single owner**, so each trigger grew its own half-implementation and none acquired a
caller. This is the same defect class as the revocation actuator that shipped through six green phases with no
production call site: completeness of a component says nothing about its reachability.

## The unifying observation

**Close-all, flatten and deleverage are one operation at three points on one axis.** They differ only in how much
exposure to remove, how fast, and what to leave alone:

| Trigger                                   | Target                       | Protected legs      | Aggressiveness    |
| ----------------------------------------- | ---------------------------- | ------------------- | ----------------- |
| Margin breach (`MarginEvent`)             | enough to satisfy margin     | none specifically   | severity-derived  |
| Producer silence (strategy went quiet)    | net delta → 0 per underlying | hedges, spread legs | strategy-declared |
| Drawdown auto-close-all / SEV0 / operator | everything → 0               | none                | maximal           |

Once that is stated, the design follows: **one mandate type, three triggers, one executor.** A second executor is the
thing to prevent, not a second trigger.

## Target architecture

### 1. UAC owns the vocabulary and the decision

`unified_api_contracts.flatten` (today) generalises to the exposure surface. It carries no service logic — only the
types both sides must agree on **while one of them is unreachable**, which is exactly why it cannot live in either
service:

- `ExposureLeg` — instrument, venue, **underlying** (the netting key), **intent** (directional / hedge / spread leg),
  signed quantity, delta per unit.
- `ExposureSnapshot` — the pre-published position picture plus the strategy's declared aggressiveness, with a staleness
  budget. Published on every instruction so the last-known value is always local.
- `ReductionMandate` — `{per-underlying target net delta, aggressiveness, protected intents, trigger, scope}`.
- `ReductionTrigger` — `MARGIN_BREACH | PRODUCER_SILENCE | DRAWDOWN_AUTO_CLOSE_ALL | LIQUIDATION_IMMINENT | OPERATOR`.

The three behaviours then differ only by construction, not by code path:

```
close_all   = ReductionMandate(targets={u: 0 for u in all}, protected_intents=frozenset())
flatten     = ReductionMandate(targets={u: 0 for u in all}, protected_intents={HEDGE, SPREAD_LEG})
deleverage  = ReductionMandate(targets=derived_from(margin_severity), protected_intents=frozenset())
```

**Netting counts every leg; only TRADING is restricted by intent.** A hedge is what makes the net small, so excluding it
from the measurement overstates exposure and provokes a reduction against risk that is already offset. Conflating the
two is the most likely implementation error here.

### 2. Position truth arrives by EVENT, never by RPC — because PBMS is CO-LOCATED

**PBMS is not a separate service and does not need to become one.** It is mounted inside strategy-service —
`strategy_service/api/main.py:182`, `app.mount("/position", _create_position_app())` — and served by the same uvicorn
process (`CMD ["uvicorn", "strategy_service.api.main:app", …]`). It is deployed wherever strategy-service is.

> **Correction, 2026-08-15.** An earlier revision of this doc claimed PBMS was "deployed as a service in NO
> environment". That was wrong: the probe searched Cloud Run for a service NAMED pbms/position and concluded absence
> without reading the consumer. Recorded because the wrong version briefly carried an `[OPERATOR]` todo to "deploy
> PBMS", which would have been work against a non-problem. See
> `/codex/12-agent-workflow/measurement-claims-discipline.md` § absence-from-one-probe.

**The co-location is the real constraint, and it is sharper than the imagined one.** The producer whose silence triggers
a reduction and the position picture needed to respond are the SAME PROCESS: one crash, hang or rolling deploy removes
both together. So an RPC for position state at decision time is guaranteed to fail exactly when it is needed — not
because there is no endpoint, but because the endpoint dies with its caller's reason for calling.

Hence: PBMS publishes `ExposureSnapshot` on the UTL event bus and execution-service holds the last-known value. This
also satisfies the no-service↔service-dependency rule (`/codex/04-architecture/tier-and-import-architecture.md`). PBMS
keeps its HTTP surface for humans and DART; that is a read surface, not an integration point.

**The independent leg is `batch-live-reconciliation-service`** — its own Cloud Run job, unrelated to strategy-service's
lifecycle. That, not PBMS, is what "reconciliation is up" means in the producer-silence protocol, and it is what makes
the flatten branch reachable at all. Splitting PBMS out into its own service is therefore NOT required: the snapshot
covers availability and the reconciliation service covers independent verification.

`UnifiedPositionTracker` (execution-local, fill-derived) is **retained**, with a role it did not previously have: it is
the fallback when no snapshot has arrived, and **its divergence from the snapshot is itself a reconciliation signal**.
Two independent derivations of the same quantity disagreeing is information, and today it is discarded.

### 3. One executor, EXPANDED not paralleled

`deleverage_executor.py` already holds real, asset-group-aware domain knowledge that nothing supersedes: `repay_debt` /
`top_up_collateral` (defi), `close_risky_leg` reduce-only (cefi), `unwind_to_mm` (tradfi), `cap_bound_block`
(sports/prediction). **That table is the asset.** The module's defect is its intake — one trigger, no caller — not its
tactics.

So it grows a mandate intake, a candidate generator, and a post-trade-leverage selector; `handle_margin_event()` becomes
a thin adapter that builds a `ReductionMandate` and calls the same core. Nothing is deleted to achieve this.

**Selection is by post-trade leverage, not by delta alone.** Reducing a long and increasing a short can be
delta-equivalent while differing materially in leverage afterwards — that is the choice worth making, and it is the
reason a candidate generator exists at all rather than a direct close list.

## Migrate-then-delete order

The standing rule is: **never delete something with nothing superseding it.** Each deletion below is gated on its
replacement being live, in this order.

1. **Build** `ReductionMandate` + `ReductionTrigger` in UAC, extending the existing flatten contract. Deletes nothing.
2. **Expand** `deleverage_executor` to accept a mandate; keep `handle_margin_event` as an adapter. Deletes nothing.
3. **Wire** a real caller and a `margin-events` subscriber. This is what makes the module non-inert; until it exists,
   steps 1-2 have only moved inert code around.
4. **Publish `ExposureSnapshot` from PBMS** on the event bus, and enable `PBMSPositionPublisher` (defaults
   `enabled=False`) so execution fills reach PBMS for reconciliation. No deployment work is needed — PBMS already ships
   inside strategy-service. Until the snapshot flows, execution-service holds nothing to act on and every reduction path
   correctly takes its refuse-to-act branch.
5. **Migrate** the two `close_all` concrete scripts to emit mandates. **Then** delete `close_all/_template.py`'s
   `ClosePosition`/`CloseAllPlan` — superseded by `ExposureLeg`/`ReductionMandate`, not before.
6. **Replace** the duplicated `_FLATTEN_SIDES` (UTL `ledger/materialize.py`) and `_FLAT_SIDES` (strategy-service
   `benchmark_fills.py`) with the UAC enum. **Then** delete both frozensets.

`UnifiedPositionTracker` and `PBMSPositionPublisher` are **not** on the deletion list — the first gains the fallback and
divergence-signal role above, and the second is the reverse direction (execution fills → PBMS) that PBMS needs to
reconcile. `PBMSPositionPublisher` defaults `enabled=False` and should be turned on as part of step 4.

## Anti-inertness is a build requirement here, not a review step

Three systems in this estate were individually complete, individually tested and collectively unreachable; a fourth
(`deleverage_executor`) is documented above. Every component added under this SSOT ships with a caller-guard test **in
the same commit** — the pattern proven three times now (`test_actuate_has_a_production_caller`,
`test_release_has_a_production_caller`, `test_dependency_health_not_inert`): an AST assertion that the component has a
non-test caller, `xfail(strict=True)` while known-inert so that wiring it forces the marker's removal.

The generalisation, learned from the revocation registry gap on 2026-08-15: **any closed-set keyed dispatch also needs
an "every emitted key resolves" test** (`deployment-service/tests/unit/test_registry_id_closed_set.py`). A component
with a caller can still be unreachable if the caller speaks a key the callee cannot look up — that failure is silent,
because the lookup error is caught and logged rather than raised.
