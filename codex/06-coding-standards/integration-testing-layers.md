---
doc_type: codex-ssot
title: Integration Testing Layers
summary:
  The 5-layer integration-testing strategy — Layer 0 contract-alignment (AC↔UIC) → 1 schema-robustness → 1.5
  per-component mocked-deps → 2 infra-verify → 3a/3b smoke+E2E, plus Layer 4 cross-repo SIT invariants (negative-control
  proven); which layers run in quickmerge vs post-deploy, the emulator-vs-mock decision matrix, and the credential-free
  hermetic (--block-network) gate.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-api,
    deployment-service,
    execution-service,
    instruments-service,
    market-tick-data-service,
  ]
scope: [engineer]
tags: [integration-testing, quality-gates, ci-cd, uac, verification, smoke-test]
related:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/02-data/vcr-cassette-ownership.md,
    /codex/06-coding-standards/feature-branch-workflow.md,
  ]
created: 2026-03-27
authoritative_for: [five-layer integration-testing strategy (Layers 0-4)]
referenced_by:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/05-infrastructure/contracts-integration.md,
    /codex/15-runbooks/sit-runbook.md,
    /codex/05-infrastructure/unified-libraries/INTERNAL_DEPENDENCY_GRAPH.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/feature-branch-workflow.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Integration Testing Layers

**Last Updated:** 2026-05-12 (currency refresh per TS-7 audit; was 2026-03-04). **SSOT for:** The 5-layer integration
testing strategy across all repos. **Cross-refs:**

- Repo registry: `unified-trading-pm/workspace-manifest.json`
- Plan: `unified-trading-pm/plans/archive/cicd_mock_hardening_2026_03_11.plan.md` (archived; folded forward into
  `06-coding-standards/README.md` § "Test Infrastructure" + `quality-gates.md` § GCP Emulator / Moto / Cassette parity)
- Cursor rule: `cursor-rules/testing/testing-requirements-integration.mdc`
- Tier architecture: `04-architecture/tier-and-import-architecture.md`
- Topology DAG: `04-architecture/TOPOLOGY-DAG.md`

---

## Overview

Five testing layers, each with a distinct purpose, location, dependency profile, and trigger point. Layers are
cumulative: Layer N+1 is meaningless if Layer N fails.

```
Layer 0:   Contract Alignment         (T0, no credentials, no cloud, fast)
Layer 1:   Schema Robustness          (per-service, no credentials, fast)
Layer 1.5: Per-Component Integration  (per-service, mocked deps, no live infra, fast)
Layer 2:   Infrastructure Verify      (deployment-service, needs GCP creds, medium)
Layer 3:   Pipeline Smoke & E2E       (system-integration-tests, needs GCP sandbox, slow)
           ├── 3a: Smoke (fast, pre-deploy gate)
           └── 3b: Full (thorough, post-deploy validation)
```

---

## Layer 0 — Contract Alignment

**Question answered:** Do all schemas describing the same data agree with each other across repos?

**What it tests:**

- Every producer schema and consumer schema for the same entity are structurally compatible
- Field names, types, required/optional alignment
- AC external schemas → AC normalized schemas → UIC internal schemas form a valid chain
- Bidirectional: AC validates against UIC; UIC validates against AC

**Where it lives:**

- `unified-api-contracts/tests/unit/test_contract_alignment.py` — canonical surface internal consistency (coverage
  tracked in AC)
- `unified-api-contracts/tests/integration/test_ac_internal_alignment.py` — canonical→internal schema pairs (co-located
  in AC for coverage)
- `unified-api-contracts/unified_api_contracts/internal/tests/unit/test_contract_alignment.py` — internal subpackage
  consistency
- `unified-api-contracts/unified_api_contracts/internal/tests/integration/test_internal_ac_alignment.py` —
  internal→canonical schema pairs

**Schema and cassette endpoint definitions:**

- Schema/contract definitions live in `unified-api-contracts` (both canonical/external and `internal/` subpackage)
- VCR cassette endpoint definitions live in `unified-api-contracts/vcr_endpoints.py`
- Contract alignment tests are co-located in `AC/tests/` for coverage tracking

**VCR-based integration test execution:**

VCR-based integration tests do NOT run standalone from AC. They EXECUTE from within the owning consumer repos
(reconciled 2026-05-12 per TS-18 audit):

- `unified-cloud-interface` (cloud SDK adapters)
- `market-tick-data-service/market_tick_data_service/market_interface` (UMI consumer post-collapse — market data)
- `instruments-service` (reference data — formerly unified-reference-data-interface)
- `execution-service` (UTEI/USEI/UDEI consumer post-collapse — trade + sports + DeFi execution)
- `position-balance-monitor-service` (UPI consumer post-collapse — position balance)

Each declares `unified-api-contracts` as a dependency and provides the normalization layer under test. This ensures the
cassette replays are exercised against the actual adapter code, not in isolation.

See [`vcr-cassette-ownership.md`](/codex/02-data/vcr-cassette-ownership.md) for the canonical recording workflow +
cassette inventory (the earlier `vcr-cassette-pattern.md` was deprecated 2026-05-12 per TS-3 audit; its content is
folded into ownership.md).

**Tier:** T0 (unified-api-contracts is the T0 pure leaf covering both surfaces)

**Credentials needed:** None

**Trigger:** Every quickmerge of AC (canonical or internal subpackage), or any owning interface repo
(`unified-cloud-interface`, `market-tick-data-service/market_tick_data_service/market_interface`, `instruments-service`
(reference data — formerly unified-reference-data-interface)). Part of STEP B at TIER 0 in the meta-flow.

**Implementation pattern:**

```python
from unified_api_contracts.databento.schemas import DatabentoOhlcvBar
from unified_api_contracts.internal.market_data import InternalOhlcvBar

def test_ohlcv_field_alignment():
    ac_fields = set(DatabentoOhlcvBar.model_fields.keys())
    uic_fields = set(InternalOhlcvBar.model_fields.keys())
    shared = ac_fields & uic_fields
    for field in shared:
        ac_type = DatabentoOhlcvBar.model_fields[field].annotation
        uic_type = InternalOhlcvBar.model_fields[field].annotation
        assert ac_type == uic_type, f"Type mismatch on {field}: AC={ac_type}, UIC={uic_type}"
```

**Why both directions:** AC owns external/normalized schemas; UIC owns internal messaging schemas. A rename in one
without the other creates silent data loss at service boundaries.

---

## Layer 1 — Schema Robustness (Per-Service)

**Question answered:** Does this service fail fast on bad input and handle optional fields correctly?

**What it tests:**

- Required field missing → `ValidationError` raised immediately
- Optional field absent → passes with default, no exception
- Wrong type → fails loudly (no silent coercion)
- Boundary values (empty strings, zero, negative, extreme timestamps)
- Corner cases specific to the service's domain

**Where it lives:**

- Each service's own test suite: `tests/unit/test_schema_robustness.py`
- Each T1/T2 library's test suite where that library defines schemas consumers depend on

**Tier:** Same tier as the owning repo. A T4 service tests its own schema handling. A T2 library tests schemas it
exports.

**Credentials needed:** None

**Trigger:** Every quickmerge of that repo. Part of STEP B in the meta-flow at the owning tier.

**Implementation pattern:**

```python
import pytest
from pydantic import ValidationError
from my_service.schemas import InputRecord

class TestSchemaRobustness:
    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            InputRecord(optional_field="present")

    def test_optional_field_absent_ok(self):
        record = InputRecord(required_field="value")
        assert record.optional_field is None

    @pytest.mark.parametrize("bad_value", ["", None, -1, "not-a-timestamp"])
    def test_invalid_types_rejected(self, bad_value):
        with pytest.raises((ValidationError, TypeError)):
            InputRecord(required_field=bad_value)
```

**Hypothesis property-based tests encouraged** for services with complex input domains (features, ML).

---

## Layer 1.5 — Per-Component Integration Tests

**Question answered:** Does this component correctly interact with its direct dependencies (adapters, event sinks,
config sources) in isolation from live infrastructure?

**What it tests:**

- A service correctly calls its UMI adapter with the expected parameters
- Event publication correctly invokes `EventSink` with the right topic and payload shape
- Config loading works correctly against a mock `SecretClient`
- Adapter wiring: the component under test connects to its declared dependency, not a stub of itself
- No live external calls, no live cloud resources — all dependencies are mocked or faked

**Where it lives:**

- `tests/integration/test_<component>_integration.py` in each repo

**Tier:** Same tier as the owning repo.

**Credentials needed:** None (all external dependencies are mocked)

**Run command:**

```bash
pytest tests/integration/ -v --timeout=30
```

**Trigger:** Blocking in quickmerge — the last local gate before Layer 2 post-deploy verification. Runs after Layer 1
(unit/schema) tests pass.

**NOT in scope for Layer 1.5:**

- Live infrastructure (GCS, PubSub, Secret Manager)
- Live trading venues or data sources
- Cross-service calls (those belong in Layer 3)

**Implementation pattern:**

```python
# tests/integration/test_market_data_service_integration.py
import pytest
from unittest.mock import MagicMock, call
from my_service.market_data_service import MarketDataService

@pytest.mark.integration
def test_service_calls_umi_adapter_with_correct_params():
    mock_adapter = MagicMock()
    mock_adapter.get_candles.return_value = []
    service = MarketDataService(adapter=mock_adapter)

    service.fetch("BTCUSDT", "1h", limit=10)

    mock_adapter.get_candles.assert_called_once_with("BTCUSDT", "1h", limit=10)

@pytest.mark.integration
def test_event_publication_invokes_event_sink():
    mock_sink = MagicMock()
    service = MarketDataService(event_sink=mock_sink)

    service.publish_tick({"symbol": "BTCUSDT", "price": 50000.0})

    assert mock_sink.publish.called
    topic, payload = mock_sink.publish.call_args[0]
    assert topic == "market-data-ticks"
    assert payload["symbol"] == "BTCUSDT"
```

#### Emulator vs Mock Fixture Decision Matrix

| Test scenario                          | Recommended tool                          | Reason                                                                                      |
| -------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| GCP Pub/Sub event propagation          | `PUBSUB_EMULATOR_HOST`                    | Protocol-faithful gRPC; SDK auto-detects                                                    |
| GCS bucket lifecycle / signed URLs     | `STORAGE_EMULATOR_HOST` (fake-gcs-server) | LocalStorageProvider skips ACLs and signed URLs                                             |
| BigQuery analytics queries             | `BIGQUERY_EMULATOR_HOST`                  | SQL query validation (avoid window functions)                                               |
| AWS S3 / Secrets / SQS                 | `@mock_aws` (moto)                        | SDK-level intercept; no emulator process needed                                             |
| Exchange REST APIs (Hyperliquid, etc.) | `responses` library (`passthrough=False`) | HTTP-level intercept; proves zero live calls                                                |
| WebSocket market data feeds            | `MockWebSocketFeed` (UMI)                 | In-process WS server; deterministic tick replay                                             |
| DeFi on-chain protocols                | Sim mode + `responses passthrough=False`  | Pure in-process arithmetic; assert zero I/O                                                 |
| DeFi on-chain integration              | Tenderly VNet fork fixture                | Real EVM state; fixture in `execution-service/tests/defi_execution/integration/conftest.py` |
| IBKR TWS gateway                       | `MagicMock(spec=IB)`                      | IBKR SDK is stateful; spec mock prevents attribute drift                                    |
| VCR cassette re-use                    | vcrpy cassette in UAC                     | Protocol-faithful for REST; use for external API contracts                                  |

**Key rule**: If the GCP/AWS SDK is on the call path, use an emulator or moto — not `unittest.mock.patch` on internals.
If only HTTP is on the call path, use `responses` or `aioresponses`.

#### Cassette Parity & Drift

- Every cassette is validated against UAC models on each commit:
  `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py`
- Nightly drift detection re-records cassettes and alerts on schema changes (alerting-only, not blocking)

**Execution-owner blocks (codified 2026-05-12 per TS-11 audit + Runbook Execution-Owner SSOT HARD RULE):**

```yaml
# Cassette schema parity check
execution:
  owner: UAC repo per-commit QG (bash scripts/quality-gates.sh) + per-PR GitHub Actions
  cadence: per-commit + per-PR
  verifier: exit code 0 + ~256 tests in ~2s (per quality-gates.md:1838)
  last_executed: every UAC commit on live-defi-rollout

# Nightly cassette drift check
execution:
  owner: UAC repo .github/workflows/cassette-drift-check.yml
  cadence: nightly (cron schedule in workflow file)
  verifier: GitHub Actions job status + alerting-service alert on schema diff
  last_executed: <verify in GitHub Actions → workflow runs tab>

# Cassette orphan checker
execution:
  owner: UAC repo per-commit QG (bash scripts/quality-gates.sh)
  cadence: per-commit
  verifier: exit code 0 (unified_api_contracts/testing/cassette_orphan_checker.py output)
  last_executed: every UAC commit on live-defi-rollout
```

#### CI Hermeticity (Credential-Free Gate)

All tests must pass with `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`. To prove zero live network calls:

```bash
pytest --block-network  # from unified-api-contracts/unified_api_contracts/testing/network_block_plugin.py
```

Tests connecting to LOCAL emulators use `@pytest.mark.allow_network`. This opt-out must be commented explaining it is an
emulator (not a live API). Each opt-out emits a CI warning.

> **QG-enforcement gap (PRE_CUTOVER backlog, codified 2026-05-12 per TS-9 audit)** — today `--block-network` is wired
> only into `system-integration-tests` per the archived `cicd_mock_hardening_2026_03_11` h8-credential-free-gate. Most
> service test suites have the plugin available via UAC's `testing/network_block_plugin.py` but DO NOT register it in
> their root `conftest.py`. **Proposed QG STEP**: scan every `*_service/tests/conftest.py` for explicit registration of
> the network gate (or an explicit allowlist comment); fail any service that lacks either. **Status**: unbacked — owner
> is governance + QG-template maintainer; design tradeoff between hard-fail vs warning. Reference incident class:
> 2026-05-05 MDPS emitted STARTED+STOPPED with garbage output (a hermetic-test gate catches a different failure mode but
> mirrors the "code-shipped is not operationally-shipped" lesson).

---

## Layer 2 — Infrastructure Connectivity Verification

**Question answered:** Are all GCS buckets, PubSub topics, Secret Manager entries, and IAM permissions actually
provisioned so that the deployed services can communicate?

**What it tests:**

- All GCS buckets defined in `configs/` exist and have correct IAM
- All PubSub topics defined in `unified_api_contracts.internal` exist with correct subscriptions
- Service accounts have the permissions they need
- Secret Manager entries exist (not their values — just existence)
- BigQuery datasets referenced by UDC exist and are accessible

**Where it lives:**

- `deployment-service/scripts/verify_infra.py`
- Exposed as `deployment-api` endpoint: `GET /infra/health`

**Tier:** T5 (deployment-service is the orchestrator tier)

**Credentials needed:** GCP project credentials (service account with read-only access to buckets, topics, secrets)

**Trigger:** Automatically by `deployment-api` before declaring a deployment "successful." If Layer 2 fails, the
deployment is marked "deployed but unhealthy" — Layer 3 does not run.

**Ordering:** Layer 2 runs AFTER deployment, BEFORE Layer 3. It is NOT part of quickmerge.

**Sports vertical (Phase 3):** `verify_infra.py` must include sports GCS buckets (sports-reference-data,
sports-odds-data, sports-processed-odds, sports-features, sports-strategy, sports-executions), PubSub topics
(sports-reference-data-updated, sports-odds-updated, sports-processed-odds-updated, sports-arbitrage-detected,
sports-features-computed, sports-bet-orders, sports-bet-executions), and Secret Manager entries for sports API keys.
Health endpoint: `GET /infra/health` with `.sports` checks.

**Implementation pattern:**

```python
from google.cloud import storage, pubsub_v1, secretmanager

def verify_infrastructure(config: DeploymentConfig) -> InfraHealthReport:
    results: list[CheckResult] = []
    for bucket in config.required_buckets:
        exists = storage_client.bucket(bucket).exists()
        results.append(CheckResult(resource=f"gs://{bucket}", ok=exists))
    for topic in config.required_topics:
        try:
            publisher.get_topic(topic=topic)
            results.append(CheckResult(resource=topic, ok=True))
        except NotFound:
            results.append(CheckResult(resource=topic, ok=False))
    return InfraHealthReport(checks=results, healthy=all(r.ok for r in results))
```

---

## Layer 3 — Pipeline Smoke & E2E

**Question answered:** Does mock data actually flow through the full service pipeline end-to-end without error?

### Layer 3a — Smoke (fast, pre-deploy gate)

**What it tests:**

- Happy path: one date, one venue, one instrument through the full pipeline
- Schema round-trip: data written by producer is readable by consumer
- Service-to-service auth flows work (OAuth tokens accepted)
- All API endpoints return 200 with valid mock input

**pytest marker:** `@pytest.mark.smoke`

**Runtime:** <5 minutes

**Trigger:** Can be triggered manually before staging merge as a confidence check. Also runs as the first phase of the
post-deploy validation.

### Layer 3b — Full E2E (thorough, post-deploy validation)

**What it tests:**

- Corner case data: missing optional fields, boundary values, multi-venue
- Multi-date pipeline: validates date partitioning and alignment
- Auth edge cases: expired tokens, wrong scope, revoked permissions
- Infrastructure interactions: PubSub publish→subscribe round-trip, GCS write→read
- Data completeness: all expected output files/topics populated
- Performance baseline: pipeline completes within expected time bounds

**pytest marker:** `@pytest.mark.full_e2e`

**Runtime:** 15–30 minutes

**Trigger:** Automatically by `deployment-api` AFTER a successful deployment AND Layer 3a passes. Sequential: 3a must
pass before 3b starts. If 3a fails, 3b is skipped and the deployment is flagged.

### Where it lives

`system-integration-tests/` — a standalone repo, NOT part of the tier DAG.

**Repo characteristics:**

- Topological position: L10 in the workspace DAG — after all services and UIs have been deployed
- Zero cross-service Python imports — interacts via HTTP, GCS, and PubSub only
- Discovers live services via `deployment-api GET /services` rather than hardcoding endpoints
- pytest markers: `@pytest.mark.smoke` (Layer 3a, <5 min) and `@pytest.mark.full_e2e` (Layer 3b, 15–30 min)
- Created as part of the UTD V3 four-way split (Phase 1 Stream B)

```
system-integration-tests/
├── tests/
│   ├── layer3a_smoke/
│   │   ├── test_pipeline_happy_path.py
│   │   ├── test_schema_round_trip.py
│   │   └── test_auth_flows.py
│   └── layer3b_full_e2e/
│       ├── test_corner_case_data.py
│       ├── test_multi_date_pipeline.py
│       ├── test_auth_edge_cases.py
│       ├── test_pubsub_round_trip.py
│       └── test_performance_baseline.py
├── fixtures/
│   ├── mock_ohlcv_data.parquet
│   ├── mock_tick_data.parquet
│   └── mock_corner_cases/
├── conftest.py           # GCP sandbox project, test bucket lifecycle
├── pyproject.toml
└── scripts/
    └── quality-gates.sh
```

**Credentials needed:** GCP sandbox project credentials. Test buckets and topics are created/destroyed by `conftest.py`.

**Sports pipeline (Phase 3):** Add `tests/smoke/test_sports_pipeline_smoke.py` and
`tests/e2e/test_sports_full_pipeline.py` with markers `@pytest.mark.smoke` and `@pytest.mark.full_e2e`, `-k "sports"`.
Tests: reference data → GCS; odds snapshot → processing → ProcessedOddsOutput; arbitrage → BetOrder; BetOrder →
execution → BetExecution. No `from footballbets`; no PostgreSQL.

**Tier:** `integration` (not T0–T6; sits above all tiers as a consumer of everything)

**Key design constraint:** system-integration-tests does NOT import Python internals from any service. It interacts via:

- HTTP (calling deployment-api, execution-results-api, etc.)
- GCS (reading output files written by services)
- PubSub (subscribing to topics published by services)
- `deployment-api GET /services` (to discover what to test)

This means zero cross-service Python imports. Clean separation.

---

## Layer 4 — Cross-repo invariants (WS-L SIT-rehome, full coverage 2026-06-28)

**Question answered:** Does the PUBLIC CONTRACT of each ldr_main repo still hold when assembled with all its siblings at
their current LDR tips?

This layer was added as part of the LDR→main fleet promoter (`ldr-to-main-promote-fleet.yml`) to give each ldr_main repo
a GENUINE cross-repo breaking gate — the SIT equivalent that staging provided for the staging-based pipeline. Unlike
Layers 1–3b, these invariants are checked in `system-integration-tests/.github/workflows/full-workspace-sit.yml` (the
CI/CD boundary, not a pytest suite), run on the full 21-repo assembly.

### The venue-coverage cascade — operator ruling 2026-08-14

**Where this class of check belongs**: within one repo, `quality-gates.sh`. **Across repos, SIT** — because no single
repo's gate can see the other side of the implication.

The cascade is **directional**, and the direction is the whole point. Each layer's venue coverage is forced by the layer
before it, never the reverse:

| #   | Invariant                                                                                 | Direction                                                                              |
| --- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1   | Every MTDS **batch** capture adapter has a **live** capture adapter                       | batch ⟹ live. **NOT the reverse** — a live venue may legitimately predate its backfill |
| 2   | Every MTDS venue has a strategy-service position reader on **batch, live AND paper**      | MTDS ⟹ strategy, all three paths                                                       |
| 3   | Every venue strategy-service supports (batch/live/paper) has an execution-service adaptor | strategy ⟹ execution                                                                   |

**Why each direction is asymmetric on purpose.** Reverse-implication would be wrong in every case: an execution adaptor
for a venue no strategy trades is harmless dead code, a strategy reader for an uncaptured venue is merely premature, and
a live capture adapter without a batch one is the normal way a venue is onboarded. Only the forward direction represents
a real defect — **capability to ACT without capability to SEE**.

**The defect this exists to catch** (measured 2026-08-14,
`/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`): execution-service ships ~30
DeFi protocol modules while strategy-service ships 3 position adapters, so ~27 protocols could be traded and not
reconciled — including Lido, Marinade, Kamino and Jupiter, i.e. both legs of the two DeFi archetypes shipping real.
Nothing detected it; it took a manual audit. Invariant 3 is the one that would have failed.

**Scope caution for the implementer.** Asserting a venue MODULE exists is not asserting it handles every
`InstructionActionV2` an archetype may emit for that venue — a module that swaps but cannot stake would pass a naive
existence check. Invariant 3 must compare against the instruction ACTIONS the strategy side can emit, not against venue
names alone, or it will score the gap it was built to find as green.

### Pattern: per-repo cross-repo invariant (negative-control-proven)

Each ldr_main repo R contributes one cross-repo invariant to `run_cross_repo_invariants.sh`:

```bash
# Positive control: a VALID cross-repo operation must SUCCEED.
# Negative control: a DELIBERATELY INVALID version must FAIL (proves the invariant isn't vacuous).
#
# Canonical structure (bash, in run_cross_repo_invariants.sh):

echo "INV-N: <REPO> — <description>"
{
  python3 -c "
from <repo_package>.<public_module> import <PublicSymbol>
# positive: valid instantiation / call must succeed
<PublicSymbol>(<valid_args>)
print('PASS positive control')
# negative: deliberately invalid input must raise
try:
    <PublicSymbol>(<bad_args>)
    print('FAIL negative control (expected exception)')
    exit(1)
except (<ExpectedException>,):
    print('PASS negative control')
" || { echo "FAIL INV-N: <REPO>"; exit 1; }
}
echo "PASS INV-N: <REPO>"
```

**Rules:**

- Every repo in `REQUIRED_SIBLINGS` MUST have a genuine invariant (placeholder `echo PASS` is review-blocking).
- `REQUIRED_SIBLINGS` in the workflow MUST equal `sit_cross_repo_validated_repos` in `workspace-manifest.json` (enforced
  by `run_cross_repo_invariants.sh`; drift → `REQUIRED_SIBLINGS_MISMATCH` fail-closed).
- The invariant tests a cross-service contract (imports a public symbol and exercises the interface) — it is NOT a
  per-repo unit test (those live in `tests/unit/` per-repo and run at Layer 1).
- Negative control is **mandatory**: a trivially-passing invariant that never fails provides no protection.

### Full-coverage end-state (all 21 ldr_main repos)

All 21 repos are in `REQUIRED_SIBLINGS` / `sit_cross_repo_validated_repos` (reached 2026-06-28). Adding a new ldr_main
repo = add to `REQUIRED_SIBLINGS` + `sit_cross_repo_validated_repos` + write the invariant.

### Combination fingerprint

The producer (`full-workspace-sit.yml`) computes `sit_validated_workspace_digest` (SHA-256 of all 21 repos' LDR tree
SHAs) at validation time. This captures the exact COMBINATION of sibling versions SIT validated — see
`/codex/08-workflows/ci-cd-flow.md` § "Cross-repo COMBINATION fingerprint" for the full contract.

---

## When Each Layer Runs

| Layer | Trigger                                            | In quickmerge?                 | Credentials   | Blocks                      |
| ----- | -------------------------------------------------- | ------------------------------ | ------------- | --------------------------- |
| 0     | Every AC, UIC, or owning interface repo quickmerge | Yes (unit + integration tests) | None          | T0 green gate               |
| 1     | Every repo quickmerge                              | Yes (unit tests)               | None          | That repo's green gate      |
| 1.5   | Every repo quickmerge (after Layer 1 passes)       | Yes (last local gate)          | None          | That repo's green gate      |
| 2     | Post-deployment (deployment-api trigger)           | No                             | GCP read-only | Layer 3                     |
| 3a    | Post-deployment (after Layer 2 passes)             | No                             | GCP sandbox   | Layer 3b                    |
| 3b    | Post-deployment (after Layer 3a passes)            | No                             | GCP sandbox   | "Deployment healthy" status |

---

## Ordering in the Plan

```
TIER 0: Layer 0 tests are written and pass (AC↔UIC alignment)
TIER 1–4: Layer 1 tests exist per-repo (schema robustness in each service)
TIER 1–4: Layer 1.5 tests exist per-repo (per-component integration tests, mocked deps)
TIER 5 (deployment split):
  - deployment-service extracted with verify_infra.py (Layer 2)
  - system-integration-tests repo created with Layer 3a + 3b
POST-REFACTOR VALIDATION (after all tiers green):
  - Deploy to sandbox
  - Layer 2 runs → passes
  - Layer 3a runs → passes
  - Layer 3b runs → passes
  - System declared healthy
```

---

## References

- **Cursor rule:** `.cursor/rules/integration-testing-layers.mdc`
- **Plan:** `unified-trading-pm/plans/archive/consolidated_remaining_work.plan.md`
- **Manifest:** `unified-trading-pm/workspace-manifest.json`
- **Topology DAG:** `04-architecture/TOPOLOGY-DAG.md`
- **Service pair flows:** `08-workflows/service-pair-flows.md` (SSOT for producer→consumer schema pairs)
