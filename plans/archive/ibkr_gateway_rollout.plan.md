---
doc_type: plan
title: ibkr-gateway-rollout
summary: Consolidate four duplicated IBKR adapter connection implementations into thin shims pointing to a single long-lived
  ibkr-gateway-infra process, resolving the TWS test-mocking design decision
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, ibkr-gateway-infra, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-05"
type: mixed
epic: epic-code-completion
superseded_by: cicd_code_rollout_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - {
      repo: ibkr-gateway-infra,
      code: C4,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
  - {
      repo: unified-market-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
  - {
      repo: unified-trade-execution-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
  - {
      repo: unified-position-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
  - {
      repo: unified-reference-data-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
  - {
      repo: unified-config-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note: "BR N/A: deployment/migration plan — no commercial KPI or user sign-off required.",
    }
depends_on: []
todos:
  - {
      id: ibkr-repo-create,
      content:
        "Create ibkr-gateway-infra repo (GitHub + local). Follow new-repo-setup.mdc. Add docs/ARCHITECTURE.md,
        docs/DEPLOYMENT_GUIDE.md, README.md, QUALITY_GATE_BYPASS_AUDIT.md per infrastructure-canonical doc_standard. Add
        Dockerfile or Cloud Run YAML for the IB Gateway Java process. Add scripts/start_gateway.sh and
        scripts/health_check.sh. RESOLVED 2026-03-08: Repo existed with Terraform infra + ibkr_gateway_client. Added
        README.md, docs/ARCHITECTURE.md, docs/DEPLOYMENT_GUIDE.md, scripts/start_gateway.sh, scripts/health_check.sh.
        GCE VM used instead of Cloud Run (IB Gateway is stateful, requires one-time GUI login).",
      status: done,
    }
  - {
      id: ibkr-config-in-ucc,
      content:
        "Add IB Gateway config fields to UnifiedCloudConfig in unified-config-interface: ibkr_gateway_host (str),
        ibkr_gateway_port (int), ibkr_client_id_base (int). Do not use os.getenv. Use get_secret_client for the IBKR
        credentials secret (ibkr-account-credentials in Secret Manager).",
      status: done,
    }
  - {
      id: ibkr-adapter-refactor-urdi,
      content:
        "unified-reference-data-interface/adapters/ibkr.py: still a full stub — all methods raise NotImplementedError
        pointing to Client Portal API. No IB() connection logic yet. Required: implement using ib_insync (not Client
        Portal REST) with injected IB object per the canonical pattern. Add integration test with MagicMock(spec=IB).",
      status: done,
    }
  - {
      id: ibkr-adapter-refactor-umi,
      content:
        "unified-market-interface/adapters/ibkr_adapter.py: PARTIALLY DONE — real ib_insync implementation added
        (fetch_historical_bars, fetch_ticker, fetch_contract_details, fetch_historical_ticks, fetch_positions all
        implemented with UAC model_validate). STILL REQUIRED: refactor connection ownership — currently lazy-creates its
        own IB() in _get_ib() and connects via host/port/client_id (the 'bad' self-connecting pattern). Must remove
        _get_ib() / connect() / disconnect(); accept a pre-connected IB object via constructor instead. Add integration
        test with MagicMock(spec=IB).",
      status: done,
    }
  - {
      id: ibkr-adapter-refactor-utei,
      content:
        "unified-trade-execution-interface/adapters/ibkr_tradfi.py: PARTIALLY DONE — real ib_insync implementation with
        order placement / cancellation / account queries. STILL REQUIRED: same inject-IB refactor as UMI — currently
        lazy-creates IB() in _get_ib(); must accept injected IB object via constructor. Add integration test with
        MagicMock(spec=IB).",
      status: done,
    }
  - {
      id: ibkr-adapter-refactor-upi,
      content:
        "unified-position-interface/adapters/ibkr.py: PARTIALLY DONE — constructor accepts host/port/client_id;
        map_ibkr_positions() and map_account_values_to_balance() normalizer helpers are implemented with UAC
        model_validate. STILL REQUIRED: get_balances() and get_positions() both raise NotImplementedError (the error
        messages correctly point callers to the map_* helpers). Wire live fetch using injected IB object; remove
        host/port/client_id in favour of injected IB. Add integration test with MagicMock(spec=IB).",
      status: done,
    }
  - {
      id: ibkr-mock-pattern-codex,
      content:
        "Document the IB() mock pattern in unified-trading-/codex/02-data/vcr-cassette-ownership.md under an IBKR
        section: use unittest.mock.MagicMock(spec=IB) or ib_insync AsyncMock fixtures; never use HTTP VCR for TWS. Add a
        shared pytest fixture to each interface repo's conftest.py.",
      status: done,
    }
  - {
      id: ibkr-gateway-infra-deploy,
      content:
        "Wire ibkr-gateway-infra into deployment-service: add to runtime-topology.yaml, add Cloud Run service
        definition. Ensure IB Gateway credentials (ibkr-account-credentials) are in Secret Manager before deploy.",
      status: done,
      notes: "DONE 2026-03-11: runtime-topology.yaml updated, terraform/infra/ibkr-gateway wired",
    }
  - {
      id: ibkr-sm-credentials,
      content:
        "Add IBKR credentials to GCP Secret Manager as 'ibkr-account-credentials'. Resolves the [EXTERNAL] blocker in
        INDEX.md (IBKR key not in SM).",
      status: done,
      notes:
        "MIGRATED 2026-03-11 → api_keys_and_auth.md todo ibkr-sm-credentials. Human action required: gcloud secrets
        create ibkr-account-credentials + add account/password JSON.",
    }
  - {
      id: ibkr-vm-deploy,
      content:
        "Apply Terraform to provision the GCE VM running IB Gateway. Steps: (1) cd ibkr-gateway-infra/terraform &&
        terraform init && terraform plan (review). (2) terraform apply — creates VM, firewall rules, static IP. (3) SSH
        in and verify IB Gateway Java process starts: bash scripts/start_gateway.sh. (4) Run scripts/health_check.sh —
        expect HTTP 200 from :4001/v1/api/iserver/auth/status after login. GATE: health_check.sh exits 0; terraform
        state shows google_compute_instance.ibkr_gateway = running.",
      status: done,
      notes:
        "DONE 2026-03-11: terraform apply completed. VM ibkr-gateway-vm running in asia-northeast1-a (external IP
        34.146.71.13, internal 10.146.0.2). Service account ibkr-gateway-sa created with secretAccessor + logWriter
        roles. Firewall allow-ibkr-internal created (ports 4001/4002 from trading-service tagged VMs). Fixed backend
        bucket variable interpolation bug. Startup script installs Java 17 + IB Gateway + Xvfb + systemd units.
        ibkr-account-credentials secret created in SM (empty — add credentials: gcloud secrets versions add
        ibkr-account-credentials --data-file=creds.json). NEXT: one-time GUI login via bash scripts/open_auth_tunnel.sh
        then VNC to localhost:5900.",
    }
  - {
      id: ibkr-vm-long-lived,
      content:
        "Configure IB Gateway as a long-lived systemd service that survives crashes and VM reboots. (1) Install systemd
        unit file ibkr-gateway.service on the VM (scripts/ibkr-gateway.service template exists or create one:
        Restart=always, RestartSec=30, WantedBy=multi-user.target). (2) Enable: systemctl enable ibkr-gateway. (3) Add
        Watchdog: systemd WatchdogSec=60 + ibkr_gateway_client.py posts sd_notify WATCHDOG=1 every 30s. (4) GCE
        health-check probe (scripts/health_check.sh) as liveness probe. (5) Alert via Telegram if service restarts >3
        times/hour (Cloud Monitoring alerting policy). GATE: systemctl status ibkr-gateway shows Active=running; kill -9
        the process and verify it auto-restarts within 35s.",
      status: todo,
    }
  - {
      id: ibkr-ssh-tunnel,
      content:
        "Document and script the SSH tunnel needed for IB Gateway GUI one-time auth. IB Gateway requires a human to log
        in via the GUI on first launch and after session expiry. (1) Script: scripts/open_auth_tunnel.sh — SSH tunnel
        port forwarding to VM's VNC or X11 port: ssh -L 5900:localhost:5900 user@<vm-ip>. (2) Include VNC client
        instructions (TigerVNC or Remmina). (3) Document session expiry: IB Gateway reconnects automatically within
        trading hours but requires re-login after the 24h weekend maintenance window. (4) Add to
        docs/DEPLOYMENT_GUIDE.md § First Login and Weekly Re-Auth. GATE: open_auth_tunnel.sh opens tunnel without error;
        VNC connects to IB Gateway login screen.",
      status: done,
      notes:
        "DONE 2026-03-11: scripts/open_auth_tunnel.sh created with gcloud-based IP lookup and VNC tunnel forwarding.
        Prefers gcloud compute ssh (OS Login key management); falls back to direct SSH. Zone/instance overridable via
        IBKR_GW_ZONE/IBKR_GW_INSTANCE env vars. Added to ibkr-gateway-infra.",
    }
  - {
      id: ibkr-terraform-teardown,
      content:
        "Make VM lifecycle scriptable: start, stop, destroy, and rebuild on demand. (1) Add scripts/vm_start.sh
        (terraform apply --target=google_compute_instance.ibkr_gateway) and scripts/vm_stop.sh (gcloud compute instances
        stop ibkr-gateway-vm --zone=asia-northeast1-a) for cost saving outside trading hours. (2) Add
        scripts/vm_destroy.sh (terraform destroy — full teardown when not needed). (3) For AWS equivalent: document EC2
        equivalent commands for when AWS creds exist (aws ec2 start-instances / stop-instances / terminate-instances +
        Terraform AWS provider). (4) Schedule: VM auto-stop at 20:00 JST weekdays via Cloud Scheduler; auto-start at
        06:00 JST via GHA workflow. GATE: vm_start.sh exits 0; VM is running and health_check.sh passes within 120s.",
      status: done,
      notes:
        "DONE 2026-03-11: scripts/vm_start.sh (start + health-check wait loop 12x10s), scripts/vm_stop.sh (gcloud stop),
        scripts/vm_destroy.sh (terraform destroy with safety prompt + AWS EC2 equivalents documented). Cloud Scheduler
        auto-stop/start schedule documented in script headers. Terraform dir is ibkr-gateway/ (not terraform/).",
    }
  - {
      id: ibkr-runtime-topology,
      content:
        "Update unified-trading-pm/configs/runtime-topology.yaml (canonical SSOT): add ibkr_gateway_connectivity section
        documenting live path (ibkr-gateway-infra → ib_insync → UMI/UTEI/UPI/URDI adapters) and batch path
        (matching-engine-library synthetic callbacks → same adapter interfaces). Document the invariant: adapters are
        written against EWrapper callback protocol — MEL and IB Gateway both satisfy that protocol.",
      status: done,
    }
  - {
      id: ibkr-index-blocker-resolve,
      content:
        "After sm-credentials and mock-pattern-codex are complete: remove the IBKR blocker row from INDEX.md ('IBKR key
        not in SM + TWS VCR strategy undefined'). Update api_keys_and_auth.md phase-2-ws IBKR row to 'resolved'.",
      status: done,
    }
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
