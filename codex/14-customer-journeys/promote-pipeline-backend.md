---
scope: [engineer, admin]
---

# Promote Pipeline Backend — `/promote` API SSOT

> **Scope**: May-23 subset. Covers the `POST /promote/{strategy_id}/{manifest_id}` endpoint + minimal 5 pre-flight
> gates. Post-cutover Phase 9 extends to the full pre-flight pipeline.
>
> SSOT plan: `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` § Phase U3 Architecture overview:
> `codex/04-architecture/promote-workflow-architecture.md`

---

## Endpoint

```
POST /api/promote/{strategy_id}/{candidate_manifest_id}
```

**Auth**: `X-API-Key` header (operator gate, same as kill-switch routes). Firebase `execution-full` enforcement is at
the UI layer for May-23; post-cutover Phase 9 wires Firebase admin SDK at backend.

### Request Body

```json
{
  "target_phase": "paper_1d",
  "promoter": "ikennaigboaka@gmail.com",
  "reason": "backtest Sharpe 1.8 > threshold 1.5; 2yr OOS clean"
}
```

| Field          | Type  | Values                                                     |
| -------------- | ----- | ---------------------------------------------------------- |
| `target_phase` | `str` | `"paper_1d"` or `"live_early"` (only valid May-23 targets) |
| `promoter`     | `str` | Operator email / identifier                                |
| `reason`       | `str` | Human-readable justification                               |

### Response (200 OK)

```json
{
  "manifest_id": "uuid-string",
  "strategy_id": "carry_staked_basis",
  "strategy_instance_id": "carry_staked_basis/defi/v1",
  "target_phase": "paper_1d",
  "promoter": "operator",
  "promoted_at": "2026-05-23T09:00:00Z",
  "event_emitted": "STRATEGY_PROMOTED_TO_PAPER"
}
```

### Error Responses

| Code | When                                                                       |
| ---- | -------------------------------------------------------------------------- |
| 400  | `target_phase` not `paper_1d` or `live_early`                              |
| 412  | One or more pre-flight gates failed (response body lists `failed_gates[]`) |
| 500  | Internal error (event emission failure, etc.)                              |

---

## Pre-Flight Gates (May-23 — 5 Minimal Gates)

All gates return `None` (pass) in mock mode (`DeploymentApiConfig.is_mock_mode`). In production, each gate function
returns a non-`None` string describing the failure.

| Gate                | Function                   | What it checks                                                           |
| ------------------- | -------------------------- | ------------------------------------------------------------------------ |
| 1. Copper sandbox   | `_gate_copper_sandbox()`   | Copper MPC sub-account reachable (May-23: STUB pass; real check June-1+) |
| 2. Venue API keys   | `_gate_venue_api_keys()`   | Configured API keys present for target venues                            |
| 3. Alerting config  | `_gate_alerting_config()`  | Alerting service configured (Telegram + PagerDuty)                       |
| 4. Kill-switch YAML | `_gate_kill_switch_yaml()` | `kill_switch.yaml` present + valid                                       |
| 5. Recon green      | `_gate_recon_green()`      | Reconciliation endpoint passes (paper: waived; live: required)           |

On gate failure: `HTTP 412` with body:

```json
{
  "detail": "Pre-flight failed",
  "failed_gates": ["Venue API keys not configured", "Kill-switch YAML missing"]
}
```

---

## Event Emission

On success, the endpoint emits one of:

| `target_phase` | Event emitted                |
| -------------- | ---------------------------- |
| `paper_1d`     | `STRATEGY_PROMOTED_TO_PAPER` |
| `live_early`   | `STRATEGY_PROMOTED_TO_LIVE`  |

On gate failure:

- `STRATEGY_PROMOTE_REJECTED` emitted with `failed_gates` in details

All events via `unified_trading_library.events.log_event()`. Constants: `PROMOTE_WORKFLOW_EVENT_TYPES` in
`unified_trading_library.events`.

---

## Source Location

| Artifact          | Path                                                                        |
| ----------------- | --------------------------------------------------------------------------- |
| Route handler     | `deployment_api/routes/promote.py`                                          |
| Registered in     | `deployment_api/main.py` (under `_authenticated_router`, prefix `/api`)     |
| Unit tests        | `tests/unit/api/test_promote.py` (8 tests — 3 classes)                      |
| UI client         | `unified-trading-system-ui/lib/api/promote-client.ts`                       |
| UI hook (context) | `unified-trading-system-ui/components/promote/promote-workflow-context.tsx` |

---

## Post-Cutover Extensions (Phase 9 — NOT May-23)

> **[DELTA 2026-05-22]** **Current state:** May-23 ships with 5 minimal pre-flight gates; Firebase `execution-full` is
> enforced at UI layer only; only `paper_1d` and `live_early` are valid promote targets; VM launch is
> operator-CLI-triggered. **Planned delta:** Phase 9 post-cutover wires Firebase admin SDK at backend, expands to 9+
> pre-flight gates (including live signing dry-run), adds `LIVE_FULL` target support, backend SSE event stream, and
> automatic VM launch via deploy event subscription. **Target:** `plans/active/master_to_live_defi_2026_05_23.md`
> post-cutover phase.

- Firebase admin SDK at backend for `execution-full` role enforcement
- Full pre-flight pipeline (9+ gates including live signing dry-run)
- `LIVE_FULL` maturity phase support
- Backend-driven SSE event stream for UI convergence
- Automatic VM launch via deploy event subscription (vs operator-CLI trigger)
