---
doc_type: issue
title:
  Kalshi execution-service adapter's expected Secret Manager names don't match what's actually provisioned — paper-order
  flow can never have worked
summary: >-
  execution_service/adapters/sports_factory.py hardcodes the Kalshi adapter's secrets as
  api_key_secret="kalshi-api-key-id" + secondary_secret="kalshi-private-key-pem" (two separate plain-string secrets —
  the SAME convention every other venue adapter in routing.py uses: Betfair app_key+session_token, Polymarket
  api_key+api_secret+wallet_address, Matchbook username+api_key). NEITHER secret exists in GCP Secret Manager
  (central-element-323112) — confirmed via `gcloud secrets versions access`: NOT_FOUND for both. A DIFFERENT secret,
  `kalshi-api-credentials`, DOES exist and contains the real key material bundled as one JSON object under different
  field names. Any real Kalshi order attempt today fails immediately at secret-load time (SecretNotFoundError) — this is
  the likely reason the Kalshi execution paper- order flow "was never actually verified end-to-end"
  (kalshi_live_capture_regression_and_drift_ 2026_07_13.md): it is not that nobody got to it, it is that the wiring is
  broken and would fail the moment anyone tried.
status: open
nature: issue
asset_group: [prediction]
stage: [execution]
repos: [execution-service]
scope: [engineer, admin]
tags: [kalshi, execution, secret-manager, credential-wiring, prediction, config-drift]
related:
  [
    /plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-7, data_engineering) while attempting the Kalshi paper-order-flow end-to-end verification
    half of prediction_satellite_ao_dispatch_batch3-001; escalated live as BLK-c2d1fff9 (main/operator answer pending as
    of filing).",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Kalshi execution credential secret-name mismatch

## What I found

`execution_service/adapters/sports_factory.py`:

```python
api_key_secret="kalshi-api-key-id",
secondary_secret="kalshi-private-key-pem",
```

`execution_service/sports_execution/routing.py::_build_kalshi` loads both via `self._load_secret(...)` (a plain-string
GCP Secret Manager fetch — same helper every other venue in this file uses, no JSON-parsing variant exists in
`routing.py`).

Live-verified against GCP Secret Manager (`central-element-323112`):

- `kalshi-api-key-id` — `NOT_FOUND`
- `kalshi-private-key-pem` — `NOT_FOUND`
- `kalshi-api-credentials` — **exists**, contains the real key material as one bundled JSON object (field names differ
  from what the code expects — not reproduced here, this doc intentionally does not repeat secret VALUES).

So `_load_secret("kalshi-api-key-id")` 404s the instant anyone tries to build a live `KalshiAdapter` — the whole
execution path is currently non-functional, not merely unverified.

## Why it matters

This is exactly the gap `kalshi_live_capture_regression_and_drift_2026_07_13.md` flagged as "still genuinely open...
Kalshi execution-service paper-order flow was never actually verified end-to-end (only the URL swap shipped; no
test/log/commit found)" — now root-caused. Nobody could have verified it without hitting this exact
`SecretNotFoundError` first.

## Recommended decision (genuine architecture/ops call — NOT auto-resolved here)

Two directions, both viable, not adjudicated by this doc:

- **(A) Re-provision two separate secrets** (`kalshi-api-key-id`, `kalshi-private-key-pem`) from the existing
  `kalshi-api-credentials` material — keeps `routing.py` untouched and consistent with every OTHER venue's
  single-plain-string-secret convention in the same file. Requires an operator (or a worker with Secret Manager WRITE
  access) to re-provision from the already-live credential — touching real exchange-trading credential material, treated
  as wallet-key-adjacent (CLAUDE.md hard-stop class), so this step is human-gated.
- **(B) Adapt `routing.py::_build_kalshi`** to parse the existing bundled `kalshi-api-credentials` JSON secret instead
  of two separate fetches — no new secret provisioning, but diverges from the established per-venue convention (every
  other adapter in this file expects N separate plain-string secrets), and is itself a small code change that needs
  picking exact field names to parse.

## Recommended decision

- [ ] [OPERATOR] P1. Decide (A) re-provision as two separate secrets, or (B) adapt `routing.py` to the bundled secret
      shape. (repo: execution-service, + GCP Secret Manager if (A))
- [ ] [DATA] P1. Once the credential wiring is fixed, place a real Kalshi paper order through execution-service
      end-to-end (order submit → fill/ack → position update) against the elections-subdomain host and capture
      logs/commit evidence it works — this is the ORIGINAL verification
      `kalshi_live_capture_regression_and_drift_2026_07_13.md` asked for, gated on the todo above. (repo:
      execution-service)
