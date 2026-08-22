---
doc_type: issue
title: Signal-leasing counterparty registry was never wired into the running broadcaster
summary: >-
  strategy-service's `_get_config()` startup path hardcoded `counterparties=[]` on both the mock-mode and
  production branches of `start_signal_broadcast_reloaders(...)` — since 2026-04-20 through 2026-08-21. Nothing
  else ever called `replace_counterparties`/re-invoked `start_signal_broadcast_reloaders` with a real list, so
  `SignalRouter.counterparties_for(slot_label)` always returned an empty list regardless of what UAC's
  `COUNTERPARTY_REGISTRY` said. A counterparty flipped to `CounterpartyStatus.ACTIVE` in UAC would still receive
  zero emissions in production — the entire signal-leasing request path downstream of routing (depth projection,
  HMAC signing, webhook dispatch, the 6 REST endpoints) was correct and tested in isolation, but genuinely
  unreachable end-to-end. Fixed in strategy-service (this session) by reading `active_counterparties()` from the
  UAC facade at startup instead of hardcoding `[]`. Residual, cross-repo, NOT fixed here: UAC's
  `COUNTERPARTY_REGISTRY` is a hardcoded Python tuple in `unified_api_contracts/internal/domain/signal_broadcast/registry.py`
  (`_COUNTERPARTY_SEED`), not a persisted/config-driven store — so onboarding a real counterparty still requires
  editing that UAC file + a strategy-service redeploy to pick up the change (no hot-reload once running), not the
  "status row + credentials, no code change" bar the operator asked for. The codex SSOT doc for this surface also
  claims `deployment-service/configs/signal-broadcast/counterparties.yaml` and
  `deployment-service/scripts/provision-signal-broadcast-secrets.sh` exist as the deploy-time provisioning path —
  neither exists anywhere in `deployment-service` (grep-confirmed, 0 hits), so that part of the implementation map
  is aspirational, not shipped.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [signal-leasing, signal-broadcast, counterparty-registry, config-reloader-pattern, client-disclosure]
related:
  [
    /codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md,
    /plans/active/walkthrough_feedback_checkpoint_2026_08_21.md,
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
  ]
created: 2026-08-22
last_updated: "2026-08-22"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Found + partially fixed 2026-08-22 verifying the signal-leasing chain end to end per an operator directive on the
  client-facing docs' "How you connect" section (Signals framing). Confirmed via direct code read:
  `grep -rn "COUNTERPARTY_REGISTRY\|replace_counterparties" strategy_service/` had zero production call sites
  populating the router from the UAC registry before this session's fix.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    strategy-service/strategy_service/cli/service_entry.py,
    strategy-service/strategy_service/signal_broadcast/config_reloaders.py,
    strategy-service/strategy_service/signal_broadcast/router.py,
    unified-api-contracts/unified_api_contracts/internal/domain/signal_broadcast/registry.py,
  ]
---

# Signal-leasing counterparty registry was never wired into the running broadcaster

## What was found

`strategy_service/cli/service_entry.py::_get_config()` called `start_signal_broadcast_reloaders(signal_broadcast_config,
counterparties=[], ...)` on BOTH the mock-mode and production branches — a hardcoded empty list, not a read from the
UAC registry. The stale comment above it claimed "hot-reloaded via the UAC registry wiring in deployment-service
(Phase 4)" — no such wiring exists anywhere in `deployment-service` (grep-confirmed: zero files matching
`signal-broadcast`/`signal_broadcast` in that repo).

Consequence, traced through the real code: `SignalBroadcaster.build(counterparties=[])` →
`SignalRouter(counterparties=[])` → `SignalRouter.counterparties_for(slot_label)` always returns `[]` →
`SignalEmitter.emit_signal()` short-circuits at its first line (`if not counterparties: return EmissionResult(dispatched=0, ...)`)
before rate-limiting, schema-depth projection, HMAC signing, or webhook dispatch ever run. This was true regardless
of what `CounterpartyStatus` a counterparty carried in UAC's registry — even a real, fully-provisioned, `ACTIVE`
counterparty with valid `endpoint`/`hmac_secret_ref` would never receive a signal in production, because the
running broadcaster never saw it in the first place.

Every other link in the chain (envelope projection, per-counterparty depth filtering, the 6 REST endpoints, HMAC
webhook push + ack, the live-publisher seam at the real `paper-run --env prod` tick path) was verified genuinely
shipped and correctly wired — this was the one missing link, and it made the whole surface end-to-end unreachable
regardless of counterparty configuration.

## Fix shipped (strategy-service, this session)

`_get_config()` now reads `active_counterparties()` from the `unified_api_contracts.signal_broadcast` facade once at
startup and passes that list to both branches of `start_signal_broadcast_reloaders(...)`. `active_counterparties()`
is a pure read over the in-process UAC registry (no GCP creds needed), so this is safe in mock mode too — today it
still resolves to an empty list either way (both seeded counterparties are `SUSPENDED`), so this fix is
behavior-neutral until an operator flips a counterparty to `ACTIVE`, at which point the broadcaster will actually
route to them on the next deploy.

## Residual gap — NOT fixed here, cross-repo, out of this session's scope

The operator's bar was "a counterparty can be activated purely by configuration (a status row plus credentials, no
code change)." The fix above makes activation *reachable* but does not make it *code-change-free*:

1. `COUNTERPARTY_REGISTRY` (UAC `unified_api_contracts/internal/domain/signal_broadcast/registry.py`) is a
   hardcoded Python tuple (`_COUNTERPARTY_SEED`) — onboarding or activating a counterparty still means editing that
   UAC file (a PR + deploy in `unified-api-contracts`), not flipping a config/DB row.
2. Even after that UAC edit lands, strategy-service does not hot-reload it — `active_counterparties()` is read once
   at `_get_config()` startup; nothing re-invokes `start_signal_broadcast_reloaders` on a timer or on a UAC-version
   bump, unlike the credential secrets (which DO hot-reload via `ApiKeyReloader`) or the strategy-instance-lifecycle
   gate (which DOES hot-reload via a Firestore-backed reloader — `strategy_service/availability/instance_lifecycle.py`).
   A strategy-service redeploy is required to pick up a registry change.
3. The codex SSOT doc's implementation map
   (`/codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md`) names
   `deployment-service/configs/signal-broadcast/counterparties.yaml` (deploy-time mirror) and
   `deployment-service/scripts/provision-signal-broadcast-secrets.sh` as already-shipped — neither exists (grep
   0 hits in `deployment-service`). Only the HMAC-secret half of that story is real (Secret Manager +
   `ApiKeyReloader` in strategy-service); the counterparty-registry half of the doc's implementation map is
   aspirational.

True "status row + credentials, no code change" activation requires moving `COUNTERPARTY_REGISTRY` off a hardcoded
Python tuple onto a persisted, config-driven store (Firestore, mirroring the
`strategy_instance_lifecycle` pattern already used one layer up in this same emission path, or the
`deployment-service/configs/signal-broadcast/counterparties.yaml` the codex doc already describes) with a real
hot-reload seam in strategy-service. That is a `unified-api-contracts` + (possibly) `deployment-service` design
change — out of scope for a strategy-service-only session. Filed here rather than silently left as a doc claim.

## Todos

- [ ] [BACKEND] P2. Design + build a persisted (Firestore or deploy-time-config-mirrored) counterparty registry
      store in `unified-api-contracts`/`deployment-service` replacing the hardcoded `_COUNTERPARTY_SEED` tuple, with
      a strategy-service hot-reload seam (mirroring `instance_lifecycle.py`'s pattern) — so a counterparty can be
      activated by a status-row + credentials change alone, no code deploy anywhere in the chain.
- [ ] [DOC] P2. Either build the `deployment-service/configs/signal-broadcast/counterparties.yaml` +
      `scripts/provision-signal-broadcast-secrets.sh` artifacts the codex SSOT doc's implementation map already
      claims exist, or correct the doc's implementation map to state they are not yet built.
