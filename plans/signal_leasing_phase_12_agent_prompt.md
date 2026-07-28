# Agent prompt — Signal Leasing Phase 12 (concrete observability readers + service-entry wiring)

Copy-paste the block below into the next agent's first turn.

---

## PROMPT START

You are a sub-agent. Before any action, read
`/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
and follow ALL rules. Also read `/Users/ikennaigboaka/Code/unified-trading-system-repos/.claude/CLAUDE.md` for workspace
rules.

## Workspace

- Workspace root: `/Users/ikennaigboaka/Code/unified-trading-system-repos/`
- Primary target repo: `strategy-service` (sub-dir, independent git repo)
- Branch on every sub-repo: `live-defi-rollout` (already checked out; NEVER switch)
- Parent plan SSOT: `unified-trading-pm/plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md` § Phase
  12 — full scope is pre-written there; do NOT re-debate, just execute.

## What's already shipped (DO NOT rebuild)

- **Phase 11** (`strategy-service@3078c4a`): `BacktestPaperLiveIngest` class + `MaturityLedgerReader` /
  `EmissionBqReader` Protocols + `BacktestSummary` / `PaperSummary` / `LiveCounts` dataclasses + scheduler thread + 18
  unit + 3 integration tests. All in `strategy_service/signal_broadcast/observability_ingest.py`. The Protocols are at
  lines 98 + 110; dataclasses at 68 / 76 / 85. DO NOT touch any of this.
- **Config-reloader hooks**: `start_signal_broadcast_reloaders(maturity_reader=None, bq_reader=None)` already accepts
  the readers as params. The `if maturity_reader is not None and bq_reader is not None` branch instantiates
  `BacktestPaperLiveIngest` and starts the scheduler. You only need to PASS the readers in.
- **`SignalBroadcaster.data_freshness()`** already exposes `observability_last_ingest_at`.
- **UI** + **UAC** + **endpoints** + **stores** all shipped — out of scope.

## Your task — Phase 12

Ship 2 concrete reader classes + 2 config fields + service-entry wiring + tests. No UI, no UAC, no endpoint changes.

### 1. New file — `strategy_service/signal_broadcast/observability_readers.py`

Two concrete classes implementing the Phase-11 Protocols:

```python
class StrategyAvailabilityMaturityReader:
    """Concrete MaturityLedgerReader — projects strategy_service.availability
    StrategyMaturity rows to BacktestSummary / PaperSummary."""

    def __init__(self, store: AvailabilityStoreLike) -> None: ...

    def backtest_summary(self, counterparty_id: str, slot_label: str) -> BacktestSummary | None:
        # cp_id is currently unused — slot maturity isn't per-counterparty yet.
        # Look up store row for slot_label. Return None if absent or maturity < BACKTESTED.
        # Otherwise project sharpe + return_pct from the stored summary.
        ...

    def paper_summary(self, counterparty_id: str, slot_label: str) -> PaperSummary | None:
        # Return PaperSummary only when StrategyMaturityPhase ∈ {PAPER_1D, PAPER_14D, PAPER_STABLE, LIVE_EARLY, LIVE_STABLE}
        ...


class BigQueryEmissionReader:
    """Concrete EmissionBqReader — runs parameterised SQL over the
    STRATEGY_SIGNAL_EMITTED_EXTERNAL + STRATEGY_SIGNAL_ACKNOWLEDGED BQ tables
    that EmissionAuditor already writes to (Phase 3)."""

    def __init__(
        self,
        *,
        bq_client: bigquery.Client,
        emission_table: str,
        ack_table: str,
    ) -> None: ...

    def live_counts(
        self,
        counterparty_id: str,
        slot_label: str,
        window_start: datetime,
        window_end: datetime,
    ) -> LiveCounts:
        # SELECT COUNT(*) AS n, COUNTIF(ack.status IN ('received','processed')) AS hits
        # FROM emission e LEFT JOIN ack ON e.emission_id = ack.emission_id
        # WHERE e.counterparty_id = @cp AND e.slot_label = @slot
        #   AND e.emission_timestamp >= @start AND e.emission_timestamp < @end
        # Empty result → LiveCounts(0, 0.0); divide-by-zero guarded.
        ...
```

**Read first:**

- `strategy_service/availability/store.py` + `strategy_service/availability/__init__.py` — understand the
  `StrategyMaturity` + `StrategyMaturityPhase` enum + the `_StrategyAvailabilityStore` (or whatever the canonical name
  is) `get(slot)` accessor.
- `strategy_service/signal_broadcast/audit.py` — confirm exact event shape that lands in BQ (`details=` dict structure).
  The BQ table schema is implied by the events sink; if it's flat columns, query the columns directly; if it's
  `details JSON`, use `JSON_VALUE(details, '$.counterparty_id')` etc.
- `unified-cloud-interface/unified_cloud_interface/` — find `get_bigquery_client()` or equivalent. NEVER
  `from google.cloud import bigquery` directly in service code; use `unified-cloud-interface`. SSOT in workspace
  `CLAUDE.md`.

**Define a small `AvailabilityStoreLike` Protocol in this new file** so the reader's constructor stays narrow. Don't
bind it to the concrete class — keeps the test mocks tiny.

### 2. Config extension

Extend `strategy_service/signal_broadcast/config.py` `SignalBroadcastConfig`:

```python
bq_emission_events_table: str = "signal_broadcast.strategy_signal_emitted_external"
bq_acknowledgement_events_table: str = "signal_broadcast.strategy_signal_acknowledged"
```

No magic strings in the reader implementation — read these from config.

### 3. Service-entry wiring

In `strategy_service/cli/service_entry.py` (the call site is around line 674 where `start_signal_broadcast_reloaders`
runs), instantiate both readers BEFORE the call + pass them in:

```python
if not service_config.cloud_mock_mode:
    bq_client = get_bigquery_client(project_id=service_config.gcp_project_id)
    bq_reader = BigQueryEmissionReader(
        bq_client=bq_client,
        emission_table=signal_broadcast_config.bq_emission_events_table,
        ack_table=signal_broadcast_config.bq_acknowledgement_events_table,
    )
    maturity_reader = StrategyAvailabilityMaturityReader(store=availability_store)
    start_signal_broadcast_reloaders(
        signal_broadcast_config,
        counterparties=[],
        project_id=service_config.gcp_project_id,
        maturity_reader=maturity_reader,
        bq_reader=bq_reader,
    )
else:
    logger.warning(
        "signal_broadcast: skipping observability ingest in mock mode "
        "(readers omitted; scheduler will not run)"
    )
    start_signal_broadcast_reloaders(
        signal_broadcast_config,
        counterparties=[],
        project_id=service_config.gcp_project_id,
    )
```

Use whatever `availability_store` reference already exists in `service_entry.py` — search for `AvailabilityStore` /
`availability_for` / similar wiring nearby. If none exists yet, instantiate the canonical store same way other
call-sites in the file do.

### 4. Tests

**Unit** — `tests/unit/signal_broadcast/test_observability_readers.py`, ≥ 90% coverage:

- `StrategyAvailabilityMaturityReader.backtest_summary` returns `None` for `CODE_NOT_WRITTEN`, `None` for
  slot-not-found, `BacktestSummary(sharpe, return_pct)` for `BACKTESTED+`.
- `paper_summary` returns `None` when phase < PAPER*1D, `PaperSummary(...)` for PAPER*\*+ phases.
- `BigQueryEmissionReader.live_counts` — `unittest.mock.patch` the `bq_client.query` method:
  - assert SQL params bind correctly (counterparty_id, slot_label, window_start, window_end)
  - assert `LiveCounts(0, 0.0)` on empty result
  - assert correct hit-rate on mixed ack statuses
  - assert divide-by-zero guarded (count=0 → hit_rate=0.0, not NaN)

**Integration** — `tests/integration/signal_broadcast/test_observability_readers_bq.py`:

- Use `BIGQUERY_EMULATOR_HOST=localhost:9050` per workspace testing infra rule
- Seed 4 emission rows + 3 ack rows for one (counterparty, slot) pair across the window
- Call `BigQueryEmissionReader.live_counts(...)` — assert the count + hit-rate match seed shape
- `@pytest.mark.allow_network` on the test (BQ emulator is local but the marker is required)

**Wire-through integration** — `tests/integration/signal_broadcast/test_service_entry_ingest_wiring.py`:

- Build a synthetic config with `cloud_mock_mode=False` + BQ emulator pointer + an in-memory availability store fixture
- Call `start_signal_broadcast_reloaders(..., maturity_reader=..., bq_reader=...)` directly (skip the full service_entry
  boot for test isolation)
- Register one staging counterparty via `_router.replace_counterparties([cp])`
- Call `get_observability_ingest().ingest_once()` once
- Assert `get_signal_broadcaster().backtest_store.rows_for(cp.id)` returns non-empty rows

### 5. QG + commits

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/strategy-service
bash scripts/quality-gates.sh
```

Ruff + basedpyright clean on signal_broadcast scope. Pre-existing QG failures OUTSIDE signal_broadcast scope (e.g.
allocator_enforcement RUF043, deployment-service codex violations) are NOT yours to fix — report them, move on.

Parent session authorises `--no-verify`. Small commits, push immediately:

```
git add strategy_service/signal_broadcast/observability_readers.py \
        strategy_service/signal_broadcast/config.py \
        strategy_service/cli/service_entry.py \
        tests/unit/signal_broadcast/test_observability_readers.py \
        tests/integration/signal_broadcast/test_observability_readers_bq.py \
        tests/integration/signal_broadcast/test_service_entry_ingest_wiring.py
git commit --no-verify -m "feat(signal_broadcast): concrete observability readers + service-entry wiring (Phase 12)"
git push origin live-defi-rollout
```

### 6. Plan checkbox flip + memory

Flip all Phase 12 checkboxes in
`unified-trading-pm/plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md` from `- [ ]` to `- [x]`.
Commit + push PM with `--no-verify`.

Write project memory at
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/project_signal_broadcast_phase_12_readers_2026_04_22.md`
with commit SHAs + the SQL query string used + scheduler-running-in-prod confirmation. Add a one-line index entry to
`MEMORY.md`.

## Hard rules (do not break)

- NO `os.getenv()` — `UnifiedCloudConfig` / typed `SignalBroadcastConfig` only
- NO `from google.cloud import bigquery` directly — use `unified-cloud-interface` `get_bigquery_client()`
- Shard-level failure isolation already handled by the Phase-11 ingest loop — your readers can raise; the loop catches
  per-counterparty
- `datetime.now(timezone.utc)` — never naive datetimes
- No `try/except ImportError` fallback imports
- Flat deps only — no `[project.optional-dependencies]`
- NEVER bump versions manually — semver-agent on merge to main
- Push immediately after each commit (orchestrator patch-restore drift)
- `git status` across UAC + UTL + strategy-service + PM before any commit; if another repo is dirty for unrelated
  reasons, work only in your own repo
- No emojis. No `.md` summary files unless explicitly asked.
- If you hit the token limit mid-task, push whatever is clean + commit-ready first.

## Reporting back

Return under 400 words:

1. Commit SHAs (strategy-service + PM plan flip + memory)
2. Final test count per file (all green)
3. The exact SQL query string `BigQueryEmissionReader.live_counts` runs
4. Confirmation that `get_observability_ingest()` returns a non-`None` instance after one full `service_entry` boot in
   the wire-through integration test
5. Any blockers + any pre-existing QG drift you chose NOT to fix

## Success criteria

- Phase 12 plan checkboxes all `- [x]`
- `cd strategy-service && bash scripts/quality-gates.sh` passes on signal_broadcast scope
- New tests all green; signal_broadcast suite total bumps from 101 → ≥ ~110+
- Production startup with `cloud_mock_mode=False` + BQ creds creates a live ingest scheduler that populates
  `BacktestPaperLiveStore` on a 15-min cadence
- UI dashboard `GET /signal_broadcast/backtest-paper-live?counterparty_id=X` returns real rows (not `[]`) once
  strategy-service is redeployed in staging

Get going.

## PROMPT END
