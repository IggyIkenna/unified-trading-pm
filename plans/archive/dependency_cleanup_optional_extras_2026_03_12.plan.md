---
id: dependency_cleanup_optional_extras_2026_03_12
status: done
created: 2026-03-12
completed: 2026-03-12
priority: P1
repos:
  - unified-cloud-interface
  - unified-trading-library
  - unified-config-interface
  - unified-ml-interface
  - execution-service
  - strategy-service
  - ibkr-gateway-infra
  - market-tick-data-service
  - unified-api-contracts
  - unified-internal-contracts
  - ml-inference-api
  - ml-training-api
  - features-multi-timeframe-service
  - client-reporting-api
  - unified-domain-client
  - batch-audit-api
  - unified-market-interface
  - unified-reference-data-interface
  - unified-trading-pm
tags: [dependencies, setup, cleanup, optional-extras, egg-info]
---

# Dependency Cleanup — Optional Extras & Fresh-Machine Setup Fix (2026-03-12)

## Motivation

A collaborator hit `unified-trading-library` setup failures on a fresh machine that did not manifest on the original
developer's machine. Root cause analysis:

1. **UCI optional extras gap** — `unified-cloud-interface/factory.py` unconditionally imports both `providers/gcp.py`
   and `providers/aws.py` at module level (lines 32–51), making `google-cloud-*` and `boto3` hard runtime requirements.
   These were declared as `[gcp]`/`[aws]` optional extras. `setup.sh` never requested optional extras, so fresh installs
   silently skipped them. The original developer's machine worked only because GCP packages had accumulated from prior
   installs.

2. **Additive venv** — `setup.sh` never wipes the venv unless `--force` is passed or Python version mismatches. This
   masked the bug.

3. **Dead optional extras** — 58 repos had `[project.optional-dependencies]` sections. Most extras (aws, gcp,
   split-libraries, api, observability, tws, monitoring, streaming, validation, testing, viz, plotting) were either
   redundant with base deps, should have been in dev, or were dead code with zero callers.

4. **egg-info legacy** — 54 `.egg-info` dirs in repo roots from old `pip install -e .` / `python setup.py develop`
   invocations. Modern uv uses `.dist-info` + `.pth` files. Stale egg-info could cause setuptools to read wrong metadata
   during `uv lock`.

5. **Direct cloud SDK violations** — 3 repos declared `google-cloud-*` or `boto3` directly, bypassing UCI as the sole
   cloud-SDK boundary.

## Changes Made

### Phase A — UCI base deps (root fix) [DONE]

- **[a1] DONE** `unified-cloud-interface/pyproject.toml`: moved all GCP packages (`google-cloud-storage`,
  `google-cloud-secret-manager`, `google-cloud-pubsub`, `google-cloud-logging`, `google-auth`, `PyJWT`,
  `google-cloud-bigquery`, `gcsfs`) and AWS packages (`boto3`, `botocore`) from optional `[gcp]`/`[aws]` extras to base
  `dependencies`. Added comment: "UCI is the sole cloud-SDK boundary — no other repo should declare google-cloud-\* or
  boto3 directly."
- **[a2] DONE** `unified-cloud-interface`: removed `[gcp]`, `[aws]`, `[cache]` optional extras entirely. Stripped
  redundant cloud packages from `dev` (kept `google-cloud-build`, `boto3-stubs`, `moto`, `vcrpy` as dev-only).
- **[a3] DONE** `uv lock` in `unified-cloud-interface` → resolved 120 packages.

### Phase B — Fix 8 repos using `[gcp]`/`[gcp,aws]` refs [DONE]

Changed `unified-cloud-interface[gcp]` → `unified-cloud-interface` (bare) in all 8 repos:

- **[b1] DONE** `client-reporting-api/pyproject.toml`
- **[b2] DONE** `unified-ml-interface/pyproject.toml`
- **[b3] DONE** `unified-domain-client/pyproject.toml`
- **[b4] DONE** `strategy-service/pyproject.toml`
- **[b5] DONE** `batch-audit-api/pyproject.toml`
- **[b6] DONE** `unified-market-interface/pyproject.toml`
- **[b7] DONE** `unified-reference-data-interface/pyproject.toml`
- **[b8] DONE** `unified-trading-library/pyproject.toml` (also fixed `[all]` extra)

### Phase C — Fix 3 direct cloud SDK violation repos [DONE]

- **[c1] DONE** `ml-inference-api/pyproject.toml`: removed `google-auth`, `google-cloud-bigquery`,
  `google-cloud-storage` (already had `unified-cloud-interface` in base deps).
- **[c2] DONE** `ml-training-api/pyproject.toml`: removed `google-auth`, `google-cloud-storage`; added
  `unified-cloud-interface>=0.11.0,<1.0.0` to base deps.
- **[c3] DONE** `features-multi-timeframe-service/pyproject.toml`: removed `google-cloud-pubsub` (already had
  `unified-cloud-interface` in base deps).

### Phase D — Delete all egg-info dirs [DONE]

- **[d1] DONE** Deleted 54 `.egg-info` directories from repo roots (all were from legacy `pip install -e .`).
- **[d2] DONE** Added `*.egg-info/` to `.gitignore` in 2 repos that were missing it (67 already had it).

### Phase E — run-all-setup.sh --force flag [DONE]

- **[e1] DONE** `unified-trading-pm/scripts/repo-management/run-all-setup.sh`: added `FORCE=false` variable, `--force`
  arg parsing, passthrough to each `setup.sh --force`, updated mode display (`FORCE REINSTALL`) and help text.

### Phase F — Flatten/remove remaining optional extras [DONE]

Policy: only `[schema-validation]` in `unified-api-contracts` (VCR cassette recording with live API clients) and
`[databento]` in UTL (heavy data feed SDK) are genuinely optional. Everything else is flattened or removed.

- **[f1] DONE** `unified-trading-library/pyproject.toml`: added UCI, UEI, UCI, and all opentelemetry packages to base
  `dependencies`. Removed `[aws]`, `[gcp]`, `[api]` (fastapi in a library is wrong), `[observability]`,
  `[split-libraries]`, `[all]`. Kept `[databento]`.
- **[f2] DONE** `unified-config-interface/pyproject.toml`: removed `[aws]` extra (boto3/botocore now in UCI base).
- **[f3] DONE** `unified-ml-interface/pyproject.toml`: removed `[aws]` extra.
- **[f4] DONE** `strategy-service/pyproject.toml`: removed `[viz]` extra (matplotlib/seaborn — dead code, zero callers
  in service source; visualization belongs in `trading-analytics-ui`/`strategy-ui` via API).
- **[f5] DONE** `ibkr-gateway-infra/pyproject.toml`: flattened `ib_insync>=0.9.86,<1.0.0` from `[tws]` to base
  `dependencies`; removed `[tws]` extra.
- **[f6] DONE** `unified-api-contracts/pyproject.toml`: removed `[testing]` extra (httpx, pyyaml, pytest — all already
  in `dev`). Kept `[schema-validation]` (live API clients for VCR cassette recording only).
- **[f7] DONE** `unified-internal-contracts/pyproject.toml`: merged `[testing]` unique deps (numpy, pyarrow, pyyaml)
  into `dev`; removed `[testing]`.
- **[f8] DONE** `execution-service/pyproject.toml`: flattened `[api]` (fastapi, uvicorn, python-multipart, slowapi) to
  base `dependencies`; removed `[all]` extra.
- **[f9] DONE** `market-tick-data-service/pyproject.toml`: moved `psutil` to base deps; moved `line-profiler` and
  `memory-profiler` to `dev`; removed `[testing]` (duplicated dev), `[monitoring]` (prometheus-client already in base),
  `[streaming]` (websockets/asyncio-mqtt/tardis-client/docker already in base), `[validation]` (ccxt/ python-dateutil
  already in base), `[plotting]` (dead code — plotly, zero callers), `[performance]` (numba already in base, profilers
  moved to dev), `[all]`.

### Phase G — uv lock all changed repos [DONE]

- **[g1] DONE** Ran `uv lock` in all 17 affected repos. All resolved cleanly:
  - `unified-cloud-interface`: 120 packages
  - `unified-trading-library`: 167 packages
  - `execution-service`: 240 packages
  - `market-tick-data-service`: 227 packages
  - `unified-config-interface`: 113 packages
  - `unified-ml-interface`: 125 packages
  - `strategy-service`: 188 packages
  - `unified-api-contracts`: 96 packages
  - `unified-internal-contracts`: 68 packages
  - `ibkr-gateway-infra`: 59 packages
  - `client-reporting-api`, `unified-domain-client`, `batch-audit-api`, `unified-market-interface`,
    `unified-reference-data-interface`, `ml-inference-api`, `ml-training-api`, `features-multi-timeframe-service`:
    130–181 packages each

## Remaining Optional Extras (Legitimate)

| Repo                      | Extra                 | Reason                                                                                                                |
| ------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`   | `[schema-validation]` | Live API clients (databento, tardis-client, ccxt, ib_insync) for VCR cassette recording only — never in test playback |
| `unified-trading-library` | `[databento]`         | Heavy data feed SDK, not needed by most consumers                                                                     |

## Architecture Rule Reinforced

> UCI (`unified-cloud-interface`) is the **sole cloud-SDK boundary** in this codebase. No other repo shall declare
> `google-cloud-*`, `boto3`, or `botocore` directly. All cloud access routes through UCI factory methods. This is now
> enforced at the package level by moving GCP+AWS to UCI base deps (not optional).
