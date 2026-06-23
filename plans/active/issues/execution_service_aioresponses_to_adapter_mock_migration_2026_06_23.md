---
title: "execution-service: migrate aioresponses test mocks → adapter-layer mocks, then bump aiohttp 3.14"
created: 2026-06-23
status: active
priority: P2
source:
  - plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md
  - plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md
  - "aiohttp 3.14 fleet bump 2026-06-23 (execution-service held back as the lone <3.14 holdout)"
locked_by: live-defi-rollout
---

# execution-service: aioresponses → adapter-layer mocks (unblock aiohttp 3.14)

## What I found

The 2026-06-23 fleet bump moved 17 of 18 repos to `aiohttp>=3.14.1` (vcrpy 8.2.1 unblocked the VCR cassette suites).
**execution-service is the lone holdout**, held on aiohttp **3.13.5** via a `[tool.uv] override-dependencies` entry,
because **8 test files use `aioresponses`** to mock aiohttp HTTP calls, and **aioresponses 0.7.8 (latest on PyPI, no
3.14 fix) cannot build aiohttp-3.14's `ClientResponse`** (3.14 added required `writer` / `stream_writer` kwargs) →
`TypeError: ClientResponse.__init__() missing 'stream_writer'`.

The 8 files (all hand-written synthetic-response unit tests — auth-header construction, canonical-order mapping, error
injection — NOT record/replay):

- `tests/unit/defi_execution/mev/test_jito_bundle.py`
- `tests/unit/defi_execution/test_hyperliquid_available_margin.py`
- `tests/unit/defi_execution/test_hyperliquid_bridge.py`
- `tests/defi_execution/unit/test_solana_connectors.py` (~1732 L)
- `tests/sports_execution/unit/test_kalshi_adapter.py`
- `tests/sports_execution/unit/exchanges/test_matchbook_adapter.py`
- `tests/sports_execution/unit/exchanges/test_polymarket_clob_adapter.py`
- `tests/sports_execution/unit/bookmaker_api/test_onexbet_adapter.py`

## Why it matters

- execution-service stays on aiohttp 3.13.5 = it keeps the 11 aiohttp cookie CVEs
  (CVE-2026-34993/47265/50269/54273–54280), and the fleet `--ignore-vuln` block in `base-service.sh`/`base-library.sh`
  is **retained solely for it** (no-op for the 17 repos on 3.14). The override + the ignores both drop the moment
  execution-service reaches 3.14.
- aioresponses is barely maintained (0.7.8 is latest, no aiohttp-3.14 fix in sight), so a conftest shim would be
  open-ended tech-debt. vcrpy is **not** the right replacement — these are synthetic-response/error-injection logic
  tests, not record/replay; vcrpy is for recorded real interactions (execution-service already uses vcrpy correctly for
  its `tests/*/integration/test_vcr_*schema*` schema-fidelity tests).

## Recommended decision

Mock at the **adapter HTTP-call boundary** (patch the adapter method that issues the aiohttp request to return the
synthetic payload) instead of mocking aiohttp's wire layer. This drops the aioresponses dependency entirely, doesn't
misuse vcrpy, and removes all coupling to aiohttp internals (survives this + future aiohttp bumps). Do it when
execution-service's active development settles (operator 2026-06-23: do not refactor its tests mid-active-development).

## Todos

- [ ] [TEST] P2. execution-service — migrate the 8 `aioresponses` test files to adapter-layer mocking (patch the
      adapter's HTTP method to return synthetic payloads; preserve every assertion incl. error-injection paths). Remove
      `aioresponses` from `pyproject.toml` `[project.dependencies]` + `workspace-constraints.toml` +
      `canonical-dependency-manifest.json`. Then **remove the `aiohttp>=3.13.4,<3.14.0` line from execution-service's
      `[tool.uv] override-dependencies`**, `uv lock` (resolves aiohttp 3.14.1), and **drop the 11 aiohttp
      `--ignore-vuln` entries** (CVE-2026-34993/47265/50269/54273–54280) from `base-service.sh` + `base-library.sh`.
      QG-green execution-service + UAC + UTL, then ship. Repo: execution-service + unified-trading-pm. Cold-start
      context: read this doc + the aiohttp issue doc; the override + ignores exist ONLY because of these 8 files.

## Composes with

`aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (the fleet bump that left this holdout) +
`cve_affected_pinned_deps_remediation_2026_06_18.md` (the broader one-by-one external-dep remediation).
