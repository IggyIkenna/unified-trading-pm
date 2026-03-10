# Plan: Live vs Batch Mode Protocol Completeness Audit

status: active priority: P1 owner: backend target: 2026-03-17

## Context

`unified-cloud-interface` defines `RuntimeMode.BATCH` and `RuntimeMode.LIVE`. The codex (`batch-live-symmetry.md`)
requires every service to support both modes with correct transport protocol switching (live → PubSub, batch → GCS). In
practice: `live_mode_handler.py` exists only for IS and MTDH; `batch_handler.py` exists for FCS/FVS/FDS/FOS but not all
others. No systematic test verifies all 14 T4 services work in both modes. A service that works in batch backfill but
fails in live mode will only be discovered at live trading — unacceptable. Goal: audit matrix shows all 14 services × 2
modes = 28 combinations GREEN; every combination has a handler, unit test, and integration test.

---

## Phase 0: Audit matrix

Run audit and fill this matrix:

| Service                          | live_handler | batch_handler | CLI --mode flag | Transport switches | Unit test live | Unit test batch | Integration test |
| -------------------------------- | ------------ | ------------- | --------------- | ------------------ | -------------- | --------------- | ---------------- |
| instruments-service (IS)         | ✅           | ✅            | ?               | ?                  | ?              | ?               | ?                |
| market-tick-data-history (MTDH)  | ✅           | ?             | ?               | ?                  | ✅             | ?               | ?                |
| market-data-processing (MDPS)    | ✅           | ?             | ?               | ?                  | ✅             | ?               | ?                |
| features-delta-one (FDS)         | ?            | ✅            | ?               | ?                  | ?              | ✅              | ?                |
| features-volatility (FVS)        | ?            | ✅            | ?               | ?                  | ?              | ✅              | ?                |
| features-calendar (FCS)          | ?            | ✅            | ?               | ?                  | ?              | ✅              | ?                |
| features-onchain (FOS)           | ?            | ✅            | ?               | ?                  | ?              | ✅              | ?                |
| features-commodity (FCM)         | ?            | ?             | ?               | ?                  | ?              | ?               | ?                |
| features-cross-instrument (FCIS) | ?            | ?             | ?               | ?                  | ?              | ?               | ?                |
| features-multi-timeframe (FMTF)  | ?            | ?             | ?               | ?                  | ?              | ?               | ?                |
| features-sports (FSS)            | ?            | ?             | ?               | ?                  | ?              | ?               | ?                |
| ml-training-api (MLTR)           | ?            | ✅            | ?               | ?                  | ?              | ?               | ?                |
| ml-inference-api (MLIN)          | ✅           | ?             | ?               | ?                  | ✅             | ?               | ?                |
| strategy-service (STR)           | ✅           | ✅            | ?               | ?                  | ?              | ✅              | ?                |

Output: `unified-trading-pm/audits/batch_live_mode_audit_2026_03_10.md`

---

## Phase 1: Fill handler gaps

### P1.1 — Reference patterns

**Reference live_mode_handler** (from `market-data-processing-service`):

```python
class LiveModeHandler:
    def __init__(self, config: ServiceConfig) -> None:
        self._transport = get_pubsub_client()  # UCI — PubSub in live
        self._freshness = FreshnessMonitor(contract=LIVE_FRESHNESS_CONTRACT)

    async def run(self) -> None:
        log_event(STARTED, mode="live")
        asyncio.create_task(self._freshness.monitor(self._get_last_update))
        async for message in self._transport.subscribe(self._input_topic):
            result = await self._process(message)
            await self._transport.publish(self._output_topic, result)
            log_event(DATA_BROADCAST, mode="live", count=1)
        log_event(STOPPED, mode="live")
```

**Reference batch_handler** (from `features-calendar-service`):

```python
class BatchHandler:
    def __init__(self, config: ServiceConfig) -> None:
        self._storage = get_storage_client()  # UCI — GCS in batch

    async def run(self, start_date: date, end_date: date) -> None:
        log_event(STARTED, mode="batch")
        for day in date_range(start_date, end_date):
            data = await self._storage.read(self._input_path(day))
            result = await self._process(data)
            await self._storage.write(self._output_path(day), result)
        log_event(PROCESSING_COMPLETED, mode="batch")
```

### P1.2 — Create missing handlers

For each `?` in the audit matrix, create the handler using the reference patterns above. Services needing both created:
FCM, FCIS, FMTF, FSS (likely all need live_mode_handler).

### P1.3 — CLI `--mode` flag

Every service CLI parser must accept `--mode batch|live`. If flag absent: add to each `cli/parser.py` or `cli/main.py`.

```python
parser.add_argument(
    "--mode",
    choices=["batch", "live"],
    default="batch",
    help="Operational mode: batch (GCS) or live (PubSub)"
)
```

---

## Phase 2: Transport protocol verification

### P2.1 — Unit test for transport switching

File per service: `tests/unit/test_mode_switching.py` (if absent)

```python
@pytest.mark.parametrize("mode,expected_transport", [
    ("batch", "GCSTransport"),
    ("live", "PubSubTransport"),
])
def test_correct_transport_selected(mode: str, expected_transport: str) -> None:
    config = ServiceConfig(mode=mode)
    handler = create_handler(config)
    assert type(handler._transport).__name__ == expected_transport
```

### P2.2 — Integration test with mocked deps

File per service: `tests/integration/test_mode_switching.py` (if absent)

```python
@pytest.mark.parametrize("mode", ["batch", "live"])
async def test_handler_produces_valid_output_schema(mode: str, mock_transport) -> None:
    handler = create_handler(mode, mock_transport)
    await handler.run_one_cycle(fixture_input)
    output = mock_transport.get_published()
    # Validate against UAC/UIC schema
    assert_schema_valid(output, SERVICE_OUTPUT_SCHEMA)
    # Verify events emitted correctly
    events = mock_uei.get_events()
    assert any(e.type == "STARTED" for e in events)
    assert any(e.type in ("DATA_BROADCAST", "PROCESSING_COMPLETED") for e in events)
```

---

## Phase 3: SIT batch-live symmetry test

### P3.1 — Symmetry test

File: `system-integration-tests/tests/integration/test_batch_live_symmetry.py`

For each service:

1. Run in batch mode with 1 day of fixture data (from dev seeded data)
2. Run in live mode with same data injected via mock PubSub
3. Compare outputs: schemas identical, values identical (same input = same output)
4. Verify event sequences are correct for each mode

```python
@pytest.mark.parametrize("service_name", [
    "instruments-service",
    "features-delta-one-service",
    "features-volatility-service",
    # ... all 14
])
async def test_batch_live_output_identical(service_name: str, fixture_data) -> None:
    batch_output = await run_service_batch(service_name, fixture_data)
    live_output = await run_service_live(service_name, fixture_data)
    assert batch_output.schema == live_output.schema
    assert batch_output.values == live_output.values  # same data = same result
```

---

## Phase 4: Documentation update

### P4.1 — Update batch-live-symmetry.md

File: `unified-trading-codex/04-architecture/batch-live-symmetry.md`

Add:

- Audit matrix with final results
- Handler pattern with code examples (reference implementations)
- Transport selection diagram
- Freshness monitoring integration (how FreshnessMonitor integrates with live handlers)
- Test pattern for new services

---

## Verification Gates

- [ ] Audit matrix: all 28 combinations (14 services × 2 modes) GREEN
- [ ] `pytest */tests/unit/test_mode_switching.py` — all pass
- [ ] `pytest */tests/integration/test_mode_switching.py` — all pass
- [ ] SIT symmetry test — all 14 services pass batch vs live comparison
- [ ] No service reachable via CLI without `--mode` flag
- [ ] All services: `RUNTIME_MODE` env var respected when no CLI flag

## Files Modified / Created

- Missing `live_mode_handler.py` files (new, per audit findings)
- Missing `batch_handler.py` files (new, per audit findings)
- `*/cli/parser.py` — add `--mode` flag where absent
- `*/tests/unit/test_mode_switching.py` — add where absent
- `*/tests/integration/test_mode_switching.py` — add where absent
- `system-integration-tests/tests/integration/test_batch_live_symmetry.py` (new)
- `unified-trading-codex/04-architecture/batch-live-symmetry.md` (update)
- `unified-trading-pm/audits/batch_live_mode_audit_2026_03_10.md` (new)

## Dependencies

- `data_availability_live_expectations_2026_03_10.plan.md` (FreshnessMonitor wired in live handlers)
- `phase3_service_hardening_integration.plan.md` (service hardening includes mode handler completion)
- `mock_data_dev_project_seeding_2026_03_10.plan.md` (fixture data for symmetry tests)
