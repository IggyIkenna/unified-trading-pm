# Contract Validation Lane Metrics

Four validation lanes protect the system against contract drift and regression. Each lane emits Prometheus counters for
observability dashboards and alerting.

## Lanes

### 1. Smoke Lane

**Trigger:** Every PR (CI-blocking). **Scope:** Pydantic schema parse validation -- ensures payloads round-trip through
models. **Counter:** `contract_smoke_total{repo, result}` **Labels:** `result` in `{pass, fail}`

### 2. Replay Lane

**Trigger:** On-demand via `contract-replay.yml` (reusable workflow). **Scope:** Replays VCR cassettes against current
Pydantic models. Catches schema changes that break existing recorded interactions. **Counter:**
`contract_replay_total{repo, cassette, result}` **Labels:** `result` in `{pass, fail, skip}`

### 3. Live Lane

**Trigger:** Nightly or on-demand. **Scope:** Calls live/staging APIs and validates responses against contract schemas.
Detects upstream API changes before they reach production. **Counter:** `contract_live_total{repo, venue, result}`
**Labels:** `result` in `{pass, fail, timeout}`

### 4. Drift Lane

**Trigger:** Nightly via `contract-drift-record.yml`. **Scope:** Re-records cassettes and diffs against committed
versions. Creates approval-gated PRs when drift is detected. **Counter:** `contract_drift_total{repo, result}`
**Labels:** `result` in `{clean, drifted, error}`

## Alerting Thresholds

| Metric                                   | Condition      | Severity              |
| ---------------------------------------- | -------------- | --------------------- |
| `contract_smoke_total{result="fail"}`    | Any occurrence | P0 -- blocks merge    |
| `contract_replay_total{result="fail"}`   | Any occurrence | P1 -- investigate     |
| `contract_live_total{result="fail"}`     | 2+ consecutive | P1 -- upstream change |
| `contract_drift_total{result="drifted"}` | Any occurrence | P2 -- review PR       |
