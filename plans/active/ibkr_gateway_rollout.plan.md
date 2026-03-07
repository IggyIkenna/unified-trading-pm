---
name: IBKR Gateway — Single Source Rollout
overview: |
  Create ibkr-gateway-infra as the single IB Gateway process for all IBKR connectivity.
  Consolidate the four duplicated IBKR adapter connection/auth implementations in UMI, UTEI,
  UPI, and URDI into thin shims that connect to a single long-lived gateway process.
  Resolve the open TWS test-mocking design decision (HTTP VCR does not apply to the TWS
  socket protocol — mock at the ib_insync Python object level instead).
todos:
  - id: ibkr-repo-create
    content:
      "Create ibkr-gateway-infra repo (GitHub + local). Follow new-repo-setup.mdc. Add docs/ARCHITECTURE.md,
      docs/DEPLOYMENT_GUIDE.md, README.md, QUALITY_GATE_BYPASS_AUDIT.md per infrastructure-canonical doc_standard. Add
      Dockerfile or Cloud Run YAML for the IB Gateway Java process. Add scripts/start_gateway.sh and
      scripts/health_check.sh."
    status: todo
  - id: ibkr-config-in-ucc
    content:
      "Add IB Gateway config fields to UnifiedCloudConfig in unified-config-interface: ibkr_gateway_host (str),
      ibkr_gateway_port (int), ibkr_client_id_base (int). Do not use os.getenv. Use get_secret_client for the IBKR
      credentials secret (ibkr-account-credentials in Secret Manager)."
    status: todo
  - id: ibkr-adapter-refactor-urdi
    content:
      "Refactor unified-reference-data-interface/adapters/ibkr.py: remove inline IB() connection setup; inject a
      connected IB object via constructor parameter. Add integration test using mock IB() object (not HTTP VCR — TWS is
      socket-based). Verify no duplicate auth logic vs other adapters."
    status: todo
  - id: ibkr-adapter-refactor-umi
    content:
      "Refactor unified-market-interface/adapters/ibkr_adapter.py: same pattern — inject IB object, remove inline
      connection. Add integration test with mock IB()."
    status: todo
  - id: ibkr-adapter-refactor-utei
    content:
      "Refactor unified-trade-execution-interface/adapters/ibkr_tradfi.py: inject IB object, remove inline connection.
      Add integration test with mock IB()."
    status: todo
  - id: ibkr-adapter-refactor-upi
    content:
      "Refactor unified-position-interface/adapters/ibkr.py: inject IB object, remove inline connection. Add integration
      test with mock IB()."
    status: todo
  - id: ibkr-mock-pattern-codex
    content:
      "Document the IB() mock pattern in unified-trading-codex/02-data/vcr-cassette-ownership.md under an IBKR section:
      use unittest.mock.MagicMock(spec=IB) or ib_insync AsyncMock fixtures; never use HTTP VCR for TWS. Add a shared
      pytest fixture to each interface repo's conftest.py."
    status: todo
  - id: ibkr-gateway-infra-deploy
    content:
      "Wire ibkr-gateway-infra into deployment-service: add to runtime-topology.yaml, add Cloud Run service definition.
      Ensure IB Gateway credentials (ibkr-account-credentials) are in Secret Manager before deploy."
    status: todo
  - id: ibkr-sm-credentials
    content:
      "Add IBKR credentials to GCP Secret Manager as 'ibkr-account-credentials'. Resolves the [EXTERNAL] blocker in
      INDEX.md (IBKR key not in SM)."
    status: todo
  - id: ibkr-runtime-topology
    content:
      "Update unified-trading-pm/configs/runtime-topology.yaml (canonical SSOT): add ibkr_gateway_connectivity section
      documenting live path (ibkr-gateway-infra → ib_insync → UMI/UTEI/UPI/URDI adapters) and batch path
      (matching-engine-library synthetic callbacks → same adapter interfaces). Document the invariant: adapters are
      written against EWrapper callback protocol — MEL and IB Gateway both satisfy that protocol."
    status: todo
  - id: ibkr-index-blocker-resolve
    content:
      "After sm-credentials and mock-pattern-codex are complete: remove the IBKR blocker row from INDEX.md ('IBKR key
      not in SM + TWS VCR strategy undefined'). Update api_keys_and_auth.plan.md phase-2-ws IBKR row to 'resolved'."
    status: todo
isProject: true
---

# IBKR Gateway — Single Source Rollout

**Day:** 2–3 (TradFi completion path; parallel with Phase 1 Stream A) **Scope:** ibkr-gateway-infra (new), URDI, UMI,
UTEI, UPI, deployment-service, SM **Completion path:** tradfi **Blocks:** TradFi live trading (execution-service IBKR
orders, market-tick-data-service IBKR feed)

## Context

Four T2 interfaces (UMI, UTEI, UPI, URDI) each have their own `ibkr_*.py` adapter with duplicated connection/auth code.
IB Gateway allows limited simultaneous connections — maintaining four independent auth implementations is a DRY
violation and a reliability risk.

`ibkr-gateway-infra` is a T0 infra leaf (merge_level 2, no unified-\* deps) that deploys the long-lived IB Gateway Java
process. All IBKR connectivity routes through it.

## Design Decision: TWS Test Mocking

**HTTP VCR does not apply.** IB Gateway uses a proprietary binary socket protocol (EClient/EWrapper via ib_insync), not
HTTP. Standard VCR cassette recording/replay cannot capture TWS messages.

**Canonical test approach:** Mock at the `ib_insync` Python object level.

```python
from unittest.mock import MagicMock, AsyncMock
from ib_insync import IB, Contract, Trade

@pytest.fixture
def mock_ib():
    ib = MagicMock(spec=IB)
    ib.reqContractDetails.return_value = [...]
    return ib

def test_ibkr_adapter(mock_ib):
    adapter = IBKRReferenceAdapter(ib=mock_ib)
    result = adapter.get_contract_details(symbol="AAPL")
    mock_ib.reqContractDetails.assert_called_once()
```

Each adapter constructor accepts `ib: IB` as a parameter (injected). In production, the caller creates one connected
`IB()` instance pointing at the `ibkr-gateway-infra` host/port. In tests, the caller injects a mock.

## Adapter Pattern (after refactor)

```python
# Before (bad — each adapter creates its own connection)
class IBKRMarketAdapter:
    def __init__(self, config: UnifiedCloudConfig):
        self._ib = IB()
        self._ib.connect(config.ibkr_host, config.ibkr_port, clientId=1)

# After (correct — connection injected, single gateway)
class IBKRMarketAdapter:
    def __init__(self, ib: IB):
        self._ib = ib  # caller owns the lifecycle
```

## Acceptance Criteria

- `ibkr-gateway-infra` repo exists with Dockerfile, deployment config, docs
- All four adapters accept injected `IB` object; no inline `IB().connect()` calls
- Integration tests for all four adapters use `MagicMock(spec=IB)` fixtures
- IBKR credentials in Secret Manager (`ibkr-account-credentials`)
- `ibkr_gateway_host`, `ibkr_gateway_port`, `ibkr_client_id_base` in `UnifiedCloudConfig`
- IBKR blocker row removed from INDEX.md
- No duplicate IB Gateway connection code anywhere in the workspace
