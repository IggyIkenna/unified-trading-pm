# AI-GENERATED — awaiting user review and promotion

---

type: code epic: epic-code-completion completion_gates: code: C5 deployment: D2 business: B1

repo_gates:

- repo: unified-api-contracts code: C0 notes: "DATA_SOURCE_TO_SECRET is the SSOT for key names"
- repo: unified-trading-library code: C0 notes: "validate_api_keys_for_venues already does SM lookup — QG check wraps
  it"
- repo: unified-trading-pm code: C0 notes: "QG check script lives in PM validation scripts"

---

## Context

UAC `DATA_SOURCE_TO_SECRET` maps data source IDs to Secret Manager secret names. Example:
`'databento': 'databento-api-key'`, `'thegraph': 'graph-api-key'`.

When `validate_api_keys_for_venues()` runs in preflight, it fetches these secrets. If the secret name is wrong (name
mismatch between UAC and actual SM), the fetch silently fails or throws — the service doesn't start but the error
message is confusing.

**Objective:** Add a QG step that validates the secret names in `DATA_SOURCE_TO_SECRET` actually exist in Secret
Manager. This is a NAMING check — not a value check. It tells us the canonical name is correct before any deployment.

## What Already Exists

- `unified_api_contracts.canonical.canonical_mappings.DATA_SOURCE_TO_SECRET` — the SSOT dict
- `unified_trading_library.validate_api_keys_for_venues()` — already does SM fetch
- `unified-trading-pm/scripts/validation/validate-build-auth.py` — checks GCP_PROJECT_ID exists
- Codex docs reference key names for auth (needs audit to confirm completeness)

## What Is Missing

### 1. Secret Name Drift

From the live run 2026-03-24, found:

- `'thegraph': 'graph-api-key'` in UAC → SM has BOTH `graph-api-key` AND `thegraph-api-key` (same value, redundant
  alias)
- `'betfair': 'betfair-api-key'` in UAC → SM has `betfair-api-key`, `betfair-app-key`, `BETFAIR_APP_KEY` (multiple
  formats, unclear which is canonical)
- `'odds_api'` → NOT in `DATA_SOURCE_TO_SECRET` but `odds-api-key` exists in SM
- `'aster': None` in UAC → but `aster-api-key`, `aster-secret-key` exist in SM

### 2. Proposed QG Check

Add to `unified-trading-pm/scripts/validation/check-secret-names.py`:

```python
"""Validate that DATA_SOURCE_TO_SECRET names exist in Secret Manager.

Run in CI to catch key name drift before deployment.
Does NOT check the key value — just that the name exists.

Usage:
    python check-secret-names.py --project central-element-323112
    python check-secret-names.py --project $GCP_PROJECT_ID --only-named
"""
```

Logic:

1. Load `DATA_SOURCE_TO_SECRET` from UAC
2. For each `(data_source, secret_name)` where `secret_name is not None`:
   - Call `gcloud secrets describe {secret_name} --project={project}` (or equivalent SDK call)
   - If 404: FAIL — secret name in UAC doesn't match SM
3. Report: all PASS, names that FAIL, data sources with `None` (explicitly no key needed)

**This should be an optional QG step** (requires GCP credentials) added to `base-service.sh` as STEP 5.X only when
`RUN_INTEGRATION=true` and GCP auth is available.

### 3. Canonical Name Alignment Audit

Before writing the QG check, audit and fix the drift:

| Data source    | Current UAC name       | Actual SM name                                       | Action                                               |
| -------------- | ---------------------- | ---------------------------------------------------- | ---------------------------------------------------- |
| `thegraph`     | `graph-api-key`        | `graph-api-key` (also `thegraph-api-key`)            | OK — `graph-api-key` is canonical; add note to codex |
| `betfair`      | `betfair-api-key`      | `betfair-api-key`                                    | OK                                                   |
| `api_football` | `api-football-api-key` | `api-football-api-key`                               | OK                                                   |
| `databento`    | `databento-api-key`    | `databento-api-key`                                  | OK                                                   |
| `tardis`       | `tardis-api-key`       | `tardis-api-key`                                     | OK                                                   |
| `aster`        | `None`                 | `aster-api-key`, `aster-secret-key`                  | Add to UAC                                           |
| `odds_api`     | (missing)              | `odds-api-key`                                       | Add to UAC                                           |
| `polymarket`   | `None`                 | `polymarket-api-key`, `polymarket-private-key`, etc. | Define canonical                                     |

### 4. Key Ownership — One System, Not Per Client

As the user confirmed: these API keys are shared infrastructure, not per-client. One key per data source per environment
(mainnet/testnet). The only exception is:

- `databento-api-key` (primary) vs `databento-alt-api-key-1` (backup/rate-limit overflow)

This means `DATA_SOURCE_TO_SECRET` should optionally support:

```python
'databento': 'databento-api-key',   # primary
# fallback handled by validate_api_keys_for_venues() at the UTL level, not service level
```

The testnet variant is handled by `TESTNET_MODE=testnet` in `ServiceRuntime` — UTL should route to testnet key names via
a separate `DATA_SOURCE_TO_SECRET_TESTNET` dict if needed. This is currently not implemented.

## Key Questions for User to Answer Before Implementation

1. Should the QG check be blocking (fail QG) or advisory (warn)?
   - Recommendation: advisory in unit mode (`CLOUD_MOCK_MODE=true`), blocking when GCP auth available
2. For data sources with `None` value (no key needed): should QG still report them?
3. Should `aster` (which has both `aster-api-key` AND `aster-secret-key`) be represented as two separate entries or a
   single entry with the primary key?
4. Is there a testnet-specific key for any data source? If so, where does that mapping live?

## Relationship to UTL Key Handling

`validate_api_keys_for_venues()` in UTL already:

1. Resolves which data sources are needed for the requested venues
2. Looks up secret names from `DATA_SOURCE_TO_SECRET` via UAC
3. Fetches values from Secret Manager

The service code never specifies key names — it's all driven by the UAC registry. The QG check just verifies the
registry names are correct without fetching values.
