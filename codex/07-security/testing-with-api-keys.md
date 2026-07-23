---
doc_type: codex-ssot
title: Testing with Live API Keys
summary:
  SSOT for the `INTEGRATION_TEST_MODE` convention (live records cassettes / vcr replays / unset skips) + the GCP-auth
  integration-test pattern; the embedded VCR cassette matrix is historical pre-collapse — live cassette SSOT is
  `02-data/vcr-cassette-ownership.md`.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [vcr, quality-gates, validation, uac]
related:
  [
    /codex/02-data/vcr-cassette-ownership.md,
    /codex/07-security/secrets-management.md,
    /codex/06-coding-standards/vcr-cassette-pattern.md,
  ]
created: 2026-03-27
authoritative_for: [INTEGRATION_TEST_MODE convention]
referenced_by: [/codex/06-coding-standards/vcr-cassette-pattern.md]
owner:
last_reviewed:
code_refs:
---

# Testing with Live API Keys

**SSOT for:** `INTEGRATION_TEST_MODE` convention, VCR cassette matrix per interface, GCP auth integration test pattern.

---

## INTEGRATION_TEST_MODE Convention

All integration tests that touch external APIs or cloud services must respect this env var:

```bash
INTEGRATION_TEST_MODE=live    # hit real endpoints, record VCR cassettes
INTEGRATION_TEST_MODE=vcr     # replay cassettes only (default in CI)
INTEGRATION_TEST_MODE=unset   # skip integration tests entirely (default in unit runs)
```

**Rule:** If `INTEGRATION_TEST_MODE` is not set, integration tests are skipped silently (not failed). This lets
`pytest tests/unit/` run cleanly without cloud credentials.

**In CI (quickmerge):** Always `INTEGRATION_TEST_MODE=vcr`. Cassettes must be committed. Tests fail if cassette is
missing.

**For live recording:** Run locally with `INTEGRATION_TEST_MODE=live` and valid credentials. Commit the recorded
cassette. Scrub auth tokens before committing (see VCR cassette ownership: `02-data/vcr-cassette-ownership.md`).

---

## GCP Auth Integration Test Pattern

```python
# tests/integration/test_gcp_auth.py
import os
import pytest

INTEGRATION_MODE = os.environ.get("INTEGRATION_TEST_MODE", "unset")

@pytest.mark.skipif(INTEGRATION_MODE == "unset", reason="Set INTEGRATION_TEST_MODE=live|vcr to run")
class TestGCPAuth:
    def test_secret_manager_read(self):
        """Verify UCI SecretClient can read a test secret."""
        from unified_cloud_interface.factory import get_secret_client
        client = get_secret_client()
        # vcr mode: cassette replays the response
        # live mode: hits real Secret Manager
        value = client.get_secret("test-secret-key")
        assert value is not None
```

Credential injection: set `GOOGLE_APPLICATION_CREDENTIALS` to a workspace service account JSON for local live runs.
Never commit credentials. See `07-security/secrets-management.md`.

---

## VCR Cassette Matrix

> **DERIVED-MATRIX BANNER (codified 2026-05-12 per TS-8 audit)** — this table was a 2026-Q1 pre-collapse layout that
> referenced interfaces (UMI/UTEI/UPI/instruments-service/USEI/UDEI/UCI) and cassette paths
> (`unified-api-contracts/mocks/<iface>/`) that no longer exist. The interface repos collapsed into `execution-service`
> / `instruments-service` / `position-balance-monitor-service` / `market-tick-data-service`; cassettes live at
> `unified_api_contracts/external/<venue>/mocks/*.yaml` (per
> [`02-data/vcr-cassette-ownership.md`](/codex/02-data/vcr-cassette-ownership.md) "Current Cassettes" — ~22 VALIDATED
> cassettes across crypto/sports/databento/onchain venues). **Treat this table as historical**; the live cassette matrix
> is in `vcr-cassette-ownership.md` § "Current Cassettes", and the per-source path SSOT is the canonical
> `external/<venue>/mocks/` layout (TS-2 fix). Inline rewrite of this table tracked as a P2 doc-clean.

Historical layout (pre-collapse, 2026-Q1; retained for archival reference only — all rows are stale):

| Interface                                                                | Venues Covered                                    | Cassette Location                                  | Status  |
| ------------------------------------------------------------------------ | ------------------------------------------------- | -------------------------------------------------- | ------- |
| UMI (market-tick-data-service/market_tick_data_service/market_interface) | binance, deribit, coinbase, hyperliquid           | `unified-api-contracts/mocks/umi/`                 | pending |
| UTEI (unified-trade-execution-interface)                                 | binance, deribit, ibkr                            | `unified-api-contracts/mocks/utei/`                | pending |
| instruments-service (formerly unified-reference-data-interface)          | databento, polygon                                | `unified-api-contracts/mocks/instruments-service/` | pending |
| UPI (unified-position-interface)                                         | binance, ibkr                                     | `unified-api-contracts/mocks/upi/`                 | pending |
| USEI (unified-sports-execution-interface)                                | betfair, pinnacle, polymarket                     | `unified-api-contracts/mocks/usei/`                | pending |
| UDEI (unified-defi-execution-interface)                                  | aave, uniswap, thegraph                           | `unified-api-contracts/mocks/udei/`                | pending |
| UCI (unified-cloud-interface)                                            | gcp (sm, gcs, bq, pubsub), aws (sm, s3, dynamodb) | `unified-cloud-interface/tests/cassettes/`         | pending |

**Cassette requirements per venue (still apply):** at minimum one cassette per endpoint called in normal operation
(instrument list, order submit, position query, market data snapshot). Current cassette inventory + status:
`vcr-cassette-ownership.md` § "Current Cassettes" (canonical SSOT).

---

## References

- `02-data/vcr-cassette-ownership.md` — who records, where cassettes live, how to contribute to AC's `mocks/`
- `api_keys_and_auth.plan.md` — implementation plan for cassette recording + GCP auth tests
- `07-security/secrets-management.md` — how API keys are stored in Secret Manager
