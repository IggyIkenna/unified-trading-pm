# Agent prompt — Signal Leasing Phase 11 (observability ingest populator)

Copy-paste the block below into the next agent's first turn. It is self-contained: workspace rules are loaded at the
top, spec SSOT is referenced, commit + push discipline is explicit, and success criteria are bounded.

---

## PROMPT START

You are a sub-agent. Before any action, read
`/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
and follow ALL rules. Also read `/Users/ikennaigboaka/Code/unified-trading-system-repos/.claude/CLAUDE.md` for workspace
rules.

## Workspace

- Workspace root: `/Users/ikennaigboaka/Code/unified-trading-system-repos/`
- Primary target repo: `strategy-service` (sub-dir, independent git repo)
- Secondary (tests reference only): `unified-api-contracts`, `unified-trading-library`
- Branch on every sub-repo: `live-defi-rollout` (already checked out; NEVER switch)
- Parent plan SSOT: `unified-trading-pm/plans/active/signal_leasing_broadcast_architecture_2026_04_20.plan.md` § Phase
  11 (the full scope is pre-written there — do NOT re-debate, just execute)

## State update 2026-04-22 (prior agent killed mid-investigation — re-dispatch)

A first attempt at Phase 11 was dispatched 2026-04-22 and killed before writing any strategy-service code. The only
deliverable that landed from that attempt is the UTL events commit. Concretely:

**Partially done — skip this step:**

- **UTL** `unified-trading-library@2676ce2d` — `OBSERVABILITY_INGEST_STARTED` / `OBSERVABILITY_INGEST_COMPLETED` /
  `OBSERVABILITY_INGEST_FAILED` already registered in `STANDARD_LIFECYCLE_EVENTS`. Do NOT add them again. Just import
  via `from unified_trading_library.events import log_event` and use the event name strings.

**Still to do — your scope:**

- `strategy_service/signal_broadcast/observability_ingest.py` — file does not exist yet
- `SignalBroadcastConfig.observability_refresh_interval_seconds` / `observability_window_days` — not added
- `config_reloaders.py` — no ingest wiring
- `SignalBroadcaster` scheduler lifecycle hooks — not added
- `SignalBroadcaster.data_freshness()` — doesn't yet include `observability_last_ingest_at`
- Unit tests — none written
- Integration test (BQ emulator) — not written
- Plan checkboxes for Phase 11 — all still `- [ ]` (12 items in the `- [ ] [AGENT]` count)
- Memory entry — not written

**Concurrent cross-repo drift to read before you build:**

- `strategy-service@4fe8e02` ("Counterparty Phase 3 migration") finalised the V2 Counterparty shape. Re-read
  `strategy_service/signal_broadcast/router.py` + `broadcaster.py` + `emitter.py` before coding — the per-counterparty
  `schema_depth` + `rate_limit` now live on `CounterpartyEntitlementProfile` (accessed via `router.profile_for(cp_id)` /
  `router.schema_depth_for(cp_id)`), NOT on `Counterparty`. Current V2 Counterparty fields are exactly: `id`, `name`,
  `status`, `endpoint`, `allowed_slots`, `hmac_secret_ref`, `rate_limit_ref`, `created_at`, `updated_at`. Use
  `is_counterparty_active(cp)` from `router.py` (already a thin `cp.status == CounterpartyStatus.ACTIVE` check
  post-migration).

Rest of this document stands unchanged.

## What's already shipped (DO NOT rebuild)

- **UI** (`unified-trading-system-ui@51382fa`): `/services/signals/dashboard` calls 4 REST-pull hooks;
  `BacktestComparisonPanel` renders 3-way (backtest / paper / live). Mock/live branch on `NEXT_PUBLIC_MOCK_API`. Out of
  your scope.
- **UAC** (`unified-api-contracts@bdc9ca0`): `DeliveryHealth` / `BacktestPaperLiveRow` / `PnlAttributionRow` + envelopes
  in `unified_api_contracts/signal_broadcast/observability.py`. Frozen, `extra="forbid"`. DO NOT touch.
- **Strategy-service** (`strategy-service@6e6fd8d`): 4 REST-pull endpoints live (`/signal_broadcast/delivery-health` /
  `/backtest-paper-live` / `/pnl-attribution` GET + POST). 3 in-process stores:
  - `DeliveryHealthTracker` — populated ONLINE by `WebhookTransport` on every dispatch attempt ✓ already works
  - `BacktestPaperLiveStore` — batch store with `replace_rows(cp_id, rows)` writer. Currently nobody calls it → endpoint
    returns `[]`. **This is what you ship.**
  - `PnlAttributionStore` — populated via counterparty POST. No batch wiring needed.
- **Broadcaster wiring**: `SignalBroadcaster.health_tracker` / `backtest_store` / `pnl_store` are exposed as public
  properties. `SignalBroadcaster.start()` / `stop()` manage daemon-thread lifecycle for the credential reloader — follow
  that pattern for your new scheduler.
- **Counterparty model post-V2 migration**: `cp.status == CounterpartyStatus.ACTIVE`, `cp.id`, `cp.allowed_slots`,
  `cp.hmac_secret_ref`. Per-counterparty payload depth now lives on `CounterpartyEntitlementProfile.payload_depth`
  resolved via `SignalRouter.schema_depth_for(cp_id)`. Use `is_counterparty_active(cp)` from `router.py`.

## Your task (Phase 11 — observability ingest populator)

Ship one new module + one typed-config extension + tests + commit. No UI, no UAC, no new endpoints.

### 1. New module — `strategy_service/signal_broadcast/observability_ingest.py`

Class `BacktestPaperLiveIngest`:

```python
class BacktestPaperLiveIngest:
    def __init__(
        self,
        *,
        broadcaster: SignalBroadcaster,
        maturity_reader: MaturityLedgerReader,   # Protocol, injectable
        bq_reader: EmissionBqReader,             # Protocol, injectable
        window_days: int = 30,
        refresh_interval_seconds: float = 900.0,
    ) -> None: ...

    def ingest_once(self) -> None:
        """One pass over all counterparties. Per-counterparty failure isolation."""

    def start(self) -> None:
        """Start the background daemon thread. Idempotent."""

    def stop(self) -> None:
        """Signal shutdown via threading.Event + join. Idempotent."""
```

**Data sources:**

- **Maturity ledger** — reference `strategy_service.availability.*` (the per-slot maturity store shipped per prior plan
  work — see `strategy_service/availability/` dir). For each `(counterparty_id, slot_label)`, look up the latest
  `BACKTESTED`-stage summary for `backtest_sharpe` + `backtest_return_pct`, and the latest `PAPER_TRADING` /
  `PAPER_TRADING_VALIDATED` summary for `paper_sharpe` / `paper_return_pct` / `paper_signal_count`. If the slot has not
  reached that maturity stage, return `None`.
- **BQ audit sink** — `STRATEGY_SIGNAL_EMITTED_EXTERNAL` events already land in BQ via `EmissionAuditor` (Phase 3).
  Aggregate over the rolling window: `live_signal_count` = count of emissions per `(counterparty_id, slot_label)`;
  `live_signal_hit_rate` = count where matching ack has `status IN ('received', 'processed')` / total.
- **P&L attribution** — read via `broadcaster.pnl_store.rows_for(cp_id)`. Only set `live_return_pct` when a matching row
  exists for the window; otherwise `None`.
- **Window** — `window_end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)`;
  `window_start = window_end - timedelta(days=window_days)`.

**Failure-isolation rule (D10 + shard-level-failure-isolation SSOT):** Per-counterparty try/except around the full
row-build. On exception: `classify_venue_error(exc)` →
`log_event("ADAPTER_FETCH_FAILED", details={counterparty_id, slot_label?, error_code, action, retry_safe})`. NEVER raise
to the scheduler loop. Other counterparties must continue.

**Injectable readers (Protocol classes):**

```python
class MaturityLedgerReader(Protocol):
    def backtest_summary(self, counterparty_id: str, slot_label: str) -> BacktestSummary | None: ...
    def paper_summary(self, counterparty_id: str, slot_label: str) -> PaperSummary | None: ...

class EmissionBqReader(Protocol):
    def live_counts(
        self,
        counterparty_id: str,
        slot_label: str,
        window_start: datetime,
        window_end: datetime,
    ) -> LiveCounts: ...
```

`BacktestSummary` / `PaperSummary` / `LiveCounts` are small dataclasses local to the ingest module (not UAC — these are
internal projections, not inter-service contracts).

### 2. Config extension

Extend `strategy_service/signal_broadcast/config.py` `SignalBroadcastConfig`:

```
observability_refresh_interval_seconds: float = 900.0
observability_window_days: int = 30
```

Update `config_reloaders.py` to construct `BacktestPaperLiveIngest` + call `.start()` in `get_signal_broadcaster()`
AFTER the broadcaster is built; call `.stop()` on shutdown. No `object` type, no `getattr` — use the typed
`SignalBroadcastConfig` directly.

### 3. Broadcaster freshness

Extend `SignalBroadcaster.data_freshness()` (already exists in `broadcaster.py`) to include
`observability_last_ingest_at` alongside `last_emission_at`. Add an `observability_last_ingest_at: datetime | None`
property on the ingest class; broadcaster reads it through a constructor-injected reference.

### 4. Lifecycle events — ALREADY SHIPPED IN UTL `2676ce2d`, DO NOT RE-LAND

The 3 events (`OBSERVABILITY_INGEST_STARTED` / `OBSERVABILITY_INGEST_COMPLETED` / `OBSERVABILITY_INGEST_FAILED`) are
already in UTL `STANDARD_LIFECYCLE_EVENTS`. In your ingest module, just call:

```python
from unified_trading_library.events import log_event

log_event("OBSERVABILITY_INGEST_STARTED", details={...})
log_event("OBSERVABILITY_INGEST_COMPLETED", details={"counterparties_processed": N, "rows_written": M, "duration_ms": T})
log_event("OBSERVABILITY_INGEST_FAILED", details={"error_code": "...", "counterparty_id": "..." | None, "duration_ms": T})
```

Do NOT touch UTL.

### 5. Tests

**Unit** — `tests/unit/signal_broadcast/test_observability_ingest.py`, 90%+ coverage:

- Happy path — fake readers return data, `ingest_once()` calls `broadcaster.backtest_store.replace_rows` once per
  counterparty with the expected rows
- One counterparty fails mid-read — other counterparties still get `replace_rows` called
- Slot entitlement filter — only slots in `cp.allowed_slots` appear in the output rows
- BACKTESTED-only slot — `paper_*` fields are `None`, `live_return_pct` is `None` if no P&L attribution
- Scheduler start/stop idempotency — calling `.start()` twice does not spawn two threads; `.stop()` before `.start()` is
  a no-op
- Window boundary — `window_start` / `window_end` are truncated to UTC midnight; rolling `window_days` days back

**Integration** — `tests/integration/signal_broadcast/test_observability_ingest_bq.py` with the BQ emulator:

- Set `BIGQUERY_EMULATOR_HOST=localhost:9050`
- Seed synthetic `STRATEGY_SIGNAL_EMITTED_EXTERNAL` rows for 2 counterparties × 3 slots across the window
- In-memory `MaturityLedgerReader` fixture
- Run `ingest_once()` once + assert `GET /signal_broadcast/backtest-paper-live?counterparty_id=<cp>` returns rows with
  the expected shape

### 6. QG + commit + push

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/strategy-service
bash scripts/quality-gates.sh
```

Ruff + basedpyright clean on the signal_broadcast sub-package. Pre-existing QG failures outside signal_broadcast scope
(e.g. allocator_enforcement RUF043) are NOT yours to fix — report them, move on.

Parent session authorises `--no-verify` for signal-leasing work. Commit small, push immediately:

```
git add strategy_service/signal_broadcast/observability_ingest.py \
        strategy_service/signal_broadcast/config.py \
        strategy_service/signal_broadcast/config_reloaders.py \
        strategy_service/signal_broadcast/broadcaster.py \
        tests/unit/signal_broadcast/test_observability_ingest.py \
        tests/integration/signal_broadcast/test_observability_ingest_bq.py
git commit --no-verify -m "feat(signal_broadcast): observability ingest populator (Phase 11) ..."
git push origin live-defi-rollout
```

(No UTL commit this round — the events already landed in `2676ce2d`.)

### 7. Plan checkbox flip

Flip all Phase 11 checkboxes in
`unified-trading-pm/plans/active/signal_leasing_broadcast_architecture_2026_04_20.plan.md` from `- [ ]` to `- [x]`.
Commit + push PM repo on the same branch.

### 8. Memory update

Write a short project memory at
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/project_signal_broadcast_phase_11_ingest_2026_04_22.md`
with commit SHAs + scheduler cadence + "UI dashboard backtest panel now returns non-empty rows in staging". Add a
one-line index entry to `MEMORY.md`.

## Hard rules (do not break)

- Shard-level failure isolation on every per-counterparty iteration — `classify_venue_error()` + `ADAPTER_FETCH_FAILED`
  event, no raises to the scheduler loop
- `datetime.now(timezone.utc)` — never naive datetimes
- No `os.getenv()` — use `UnifiedCloudConfig` / the typed `SignalBroadcastConfig`
- No `try/except ImportError` fallback imports
- No new schemas defined inline in the service — any shared cross-service type goes to UAC first (but Phase 11
  projections are internal; they stay local)
- Flat deps only — no `[project.optional-dependencies]`
- Commits push immediately after they land (orchestrator patch-restore drift has been seen; don't leave unpushed local
  commits)
- NEVER bump versions manually in `pyproject.toml` — semver-agent handles it on merge to main
- No emojis
- No `.md` summary files unless explicitly asked

## Reporting back

Return under 400 words:

1. Commit SHAs (UTL + strategy-service + PM plan flip + memory)
2. Final test count per file (unit + integration, all green)
3. `SignalBroadcaster.data_freshness()` output format (JSON snippet)
4. Any blockers encountered + any pre-existing QG drift you chose NOT to fix
5. Confirmation that `GET /signal_broadcast/backtest-paper-live` returns non-empty rows after one `ingest_once()` cycle
   in the integration test

## Success criteria

- Phase 11 plan checkboxes all `- [x]`
- `cd strategy-service && bash scripts/quality-gates.sh` passes on signal_broadcast scope
- UTL new events importable + registered in `STANDARD_LIFECYCLE_EVENTS`
- UI dashboard backtest panel renders real 3-way rows when `NEXT_PUBLIC_MOCK_API=false` (once strategy-service is
  redeployed with your commit)
- Scheduler runs every 15 min by default; one counterparty failing does not stall others

Get going.

## PROMPT END
