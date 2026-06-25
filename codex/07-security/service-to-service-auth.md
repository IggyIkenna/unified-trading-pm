---
scope: [engineer, admin]
---

# Service-to-Service Authentication

**SSOT:** This document defines the S2S auth phases for the Unified Trading System. The **canonical receiver
implementation is the UTL factory** `create_s2s_auth_dependency(service_name)` in
`unified_trading_library/cloud_interface/s2s_auth.py` — every enrolled service imports it instead of maintaining its own
copy. A per-service hand-rolled `verify_service_token` in `{service}/auth_s2s.py` is the **retiring anti-pattern** (see
"Canonical receiver — the UTL factory" below): 17 service modules already consume the factory; the last local copies are
being collapsed onto it (tracked in `plans/active/cicd_consolidated_remaining_2026_06_24.md` ▸ WS-I).

---

## Phase 0 — Static Bearer Token (CURRENT)

**Status:** Implemented in execution-service, risk-and-exposure-service.

All internal service-to-service calls include an `X-Service-Token` header. The expected value is loaded from config via
`UnifiedCloudConfig.service_auth_token` (backed by the `SERVICE_AUTH_TOKEN` env var or Secret Manager secret
`{service}-s2s-token`).

### Pattern

```python
# Caller (e.g. strategy-service calling execution-service)
from unified_config_interface import UnifiedCloudConfig

cfg = UnifiedCloudConfig()
headers = {"X-Service-Token": cfg.service_auth_token or ""}
response = await http_client.post("/internal/submit-order", headers=headers, json=payload)
```

```python
# Receiver (execution-service FastAPI route) — canonical: the UTL factory, NOT a local copy
from unified_trading_library.cloud_interface.s2s_auth import create_s2s_auth_dependency

verify_service_token = create_s2s_auth_dependency("execution-service")

@router.post("/internal/submit-order")
async def submit_order(
    payload: OrderPayload,
    _: None = Depends(verify_service_token),
):
    ...
```

### Token provisioning

Token is stored in Secret Manager as `{service}-s2s-token` (or a single shared `service-mesh-token` for Phase 0). Loaded
at startup — restart required after rotation.

```bash
bash unified-trading-pm/scripts/setup_secret.sh \
  -p "${GCP_PROJECT_ID}" \
  -n "execution-service-s2s-token" \
  -v "$(openssl rand -hex 32)"
```

Set the env var in Cloud Run:

```yaml
env:
  - name: SERVICE_AUTH_TOKEN
    valueFrom:
      secretKeyRef:
        name: execution-service-s2s-token
        key: latest
```

### Bypass behaviour

If `SERVICE_AUTH_TOKEN` is not set on a service, the factory dependency logs at DEBUG and bypasses the check — this
ensures zero downtime during rollout (services enroll incrementally). In **mock mode** (`CLOUD_MOCK_MODE=true`) any
token is accepted (credential-free local/test runs). A present-but-mismatched or missing token on an enrolled service
returns **HTTP 403** and emits an `S2S_AUTH_FAILURE` event (with endpoint + source IP). The expected token is resolved
once at startup and `lru_cache`d — **restart to pick up a rotation**.

---

## Phase 1 — GCP Service Account OAuth (PLANNED)

**Status:** Planned. Will replace Phase 0 after all services are deployed to Cloud Run.

Each service will have a dedicated GCP service account. Callers obtain short-lived OAuth tokens via the metadata server
or `google-auth` library. Receivers validate tokens via Google's tokeninfo endpoint.

```python
# Phase 1 caller pattern (planned)
import google.auth.transport.requests
import google.oauth2.id_token

def get_id_token(audience: str) -> str:
    request = google.auth.transport.requests.Request()
    return google.oauth2.id_token.fetch_id_token(request, audience)

headers = {"Authorization": f"Bearer {get_id_token('https://execution-service-url/')}"}
```

Phase 1 requires:

1. Service accounts provisioned per service (see `CredentialsRegistry.SERVICE_ACCOUNT_MAP`)
2. IAM binding: caller SA has `roles/run.invoker` on receiver Cloud Run service
3. Receiver validates token audience against its own Cloud Run URL

---

## Enrolled Services

Canonical enrollment = a route module that builds its dependency from the UTL factory
(`verify_service_token = create_s2s_auth_dependency("<service>")`). 17 service modules already do this (alerting,
deployment-service, features-service ×8, mdps, ml-service ×2, trading-agent-service, batch-live-recon, and
strategy-service's own `position` / `pnl` / `risk`). The remaining hand-rolled local copies are the retiring
anti-pattern:

| Service           | Status                                      | Notes                                                                          |
| ----------------- | ------------------------------------------- | ------------------------------------------------------------------------------ |
| strategy-service  | ✅ on factory (`risk`/`pnl`/`position`)     | migrated 2026-06-24                                                            |
| execution-service | ⏳ local `auth_s2s.py` — migrate to factory | near-factory; needs a test rewrite + drops the latent `Request \| None` form   |
| deployment-api    | ⏳ local `auth.py` — operator-decision      | a genuinely different auth contract (401 / `DISABLE_AUTH` / `APIKeyHeader` DI) |

Migration tracker: `plans/active/cicd_consolidated_remaining_2026_06_24.md` ▸ WS-I (contract_hardening #3). Phase 1
target for all enrolled services remains GCP SA OAuth.

---

## Phase 0 Implementation Details

### What SA OAuth Entails (Phase 0)

Phase 0 uses a **static shared bearer token** (not a true service account OAuth token — that is Phase 1). The name "SA
OAuth" in the plan refers to the target direction; Phase 0 is the transitional step:

- A random 32-byte hex string (`openssl rand -hex 32`) serves as the shared secret.
- Stored in Secret Manager as `{service}-s2s-token`.
- Loaded at service startup via `UnifiedCloudConfig.service_auth_token`.
- Sent on every internal HTTP call as `X-Service-Token: <token>`.
- Receiver validates via the UTL factory dependency `create_s2s_auth_dependency("<service>")` (NOT a hand-rolled copy).

This approach requires zero per-call latency (no OAuth round-trip) and is appropriate for the current phase where all
services are in the same VPC. Phase 1 (GCP SA OAuth) replaces this with short-lived Google-signed ID tokens.

### Smoke Test: `auth_smoke_test.py`

Each enrolled service MUST have `tests/smoke/auth_smoke_test.py`. This file validates that the `SERVICE_AUTH_TOKEN`
environment variable is present and meets the minimum security bar before any deployment proceeds.

**Canonical implementation:**

```python
# tests/smoke/auth_smoke_test.py
"""
Phase 0 S2S auth smoke test.

Validates that SERVICE_AUTH_TOKEN is set and meets the minimum security bar.
This test runs in CI (quality-gates.sh --quick) and as a pre-deploy gate.

Phase 0: static bearer token (32-byte hex minimum).
Phase 1 (planned): GCP service account OAuth ID token — this file will be
replaced with SA token validation when Phase 1 is implemented.
"""
import os
import re


def test_service_auth_token_env_var_is_set() -> None:
    """SERVICE_AUTH_TOKEN must be present — absent means SM provisioning was skipped."""
    token = os.environ.get("SERVICE_AUTH_TOKEN")
    assert token, (
        "SERVICE_AUTH_TOKEN must be set. "
        "Provision via: bash unified-trading-pm/scripts/setup_secret.sh "
        "-p $GCP_PROJECT_ID -n {service}-s2s-token -v $(openssl rand -hex 32)"
    )


def test_service_auth_token_minimum_length() -> None:
    """Token must be at least 32 chars (256-bit entropy floor)."""
    token = os.environ.get("SERVICE_AUTH_TOKEN", "")
    assert len(token) >= 32, (
        f"SERVICE_AUTH_TOKEN is only {len(token)} chars — minimum is 32. "
        "Rotate with: openssl rand -hex 32"
    )


def test_service_auth_token_is_hex_string() -> None:
    """Phase 0 tokens MUST be lowercase hex (output of openssl rand -hex 32).

    This catches accidentally provisioned plaintext passwords or base64 blobs
    that would pass the length check but have lower entropy density.
    """
    token = os.environ.get("SERVICE_AUTH_TOKEN", "")
    if not token:
        return  # already caught by test_service_auth_token_env_var_is_set
    assert re.fullmatch(r"[0-9a-f]+", token), (
        "SERVICE_AUTH_TOKEN must be a lowercase hex string. "
        "Generate with: openssl rand -hex 32"
    )
```

**Placement:** `tests/smoke/auth_smoke_test.py` in every enrolled service repo.

**CI execution:** `quality-gates.sh --quick` runs the smoke tier; this test is included automatically when the
`tests/smoke/` directory exists.

**Local execution:**

```bash
SERVICE_AUTH_TOKEN=$(openssl rand -hex 32) pytest tests/smoke/auth_smoke_test.py -v
```

### Canonical receiver — the UTL factory

The receiver dependency is built from the **shared UTL factory** `create_s2s_auth_dependency(service_name)` — services
do **NOT** hand-roll their own `verify_service_token`. The factory lives in
`unified_trading_library/cloud_interface/s2s_auth.py` and is the single source of the Phase-0 validation logic
(mock-mode bypass, token resolution + `lru_cache`, 403-on-mismatch, `S2S_AUTH_FAILURE` event emission,
source-IP/endpoint capture). Each enrolled route module is just:

```python
# {service}/.../auth_s2s.py  (≈5 lines — no logic, just the factory call)
from unified_trading_library.cloud_interface.s2s_auth import create_s2s_auth_dependency

# Bind once; reuse as a FastAPI dependency on every /internal/* route.
verify_service_token = create_s2s_auth_dependency("{service}")
```

The factory's behaviour (defined ONCE, in UTL):

- **Mock mode** (`CLOUD_MOCK_MODE=true`) → accept any token (credential-free local/CI).
- `SERVICE_AUTH_TOKEN` unset → bypass with a DEBUG log (incremental-rollout grace; removed once all services enroll).
- Missing **or** mismatched token on an enrolled service → **HTTP 403** + an `S2S_AUTH_FAILURE` event (endpoint + source
  IP).
- Expected token resolved once at startup via `UnifiedCloudConfig.service_auth_token`, `lru_cache`d → **restart to
  rotate**.
- The dependency takes a **non-optional** `request: Request` (the former `Request | None = None` broke under
  fastapi≥0.136 / starlette≥1.0 — that pattern is a latent bug, not a model to copy).

> **Anti-pattern (retiring):** a per-service module that re-implements the header check inline (its own
> `UnifiedCloudConfig` read, its own 401/403, its own logging). These DRIFT (status codes, mock-mode handling, the
> `Request | None` bug) and are being collapsed onto the factory — never add a new one. See the enrolled-services table
> for the remaining migrations.

### Token Rotation Procedure

```bash
# 1. Generate new token
NEW_TOKEN=$(openssl rand -hex 32)

# 2. Add new version to Secret Manager (old version remains accessible)
bash unified-trading-pm/scripts/setup_secret.sh \
  -p "${GCP_PROJECT_ID}" \
  -n "{service}-s2s-token" \
  -v "$NEW_TOKEN"

# 3. Deploy new service version (picks up latest SM version at startup)
# 4. Verify smoke test passes with new token:
SERVICE_AUTH_TOKEN="$NEW_TOKEN" pytest tests/smoke/auth_smoke_test.py -v
```

---

## Testing

An `auth_smoke_test.py` validates S2S token env var per service. See the **Phase 0 Implementation Details** section
above for the canonical three-test implementation (`env_var_is_set`, `minimum_length`, `is_hex_string`).

**Quick reference:**

```bash
# Run smoke tests locally (simulates CI)
SERVICE_AUTH_TOKEN=$(openssl rand -hex 32) pytest tests/smoke/auth_smoke_test.py -v

# Run as part of quality gates
bash scripts/quality-gates.sh --quick
```

---

## Cross-references

- `unified-trading-library/unified_trading_library/cloud_interface/s2s_auth.py` — **the canonical receiver factory**
  `create_s2s_auth_dependency` (single source of Phase-0 validation logic)
- `unified-cloud-interface/unified_cloud_interface/credentials_registry.py` — `SERVICE_ACCOUNT_MAP`
- `unified-config-interface/unified_config_interface/cloud_config.py` — `service_auth_token` field
- `unified-trading-pm/codex/07-security/secret-naming-convention.md` — naming patterns
- `strategy-service/strategy_service/{risk,pnl,position}/auth_s2s.py` — canonical ≈5-line factory binding (migrated
  2026-06-24)
- `plans/active/cicd_consolidated_remaining_2026_06_24.md` ▸ WS-I — the execution-service / deployment-api migration
  tracker
