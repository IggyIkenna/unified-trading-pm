---
doc_type: issue
title: "execution-service: migrate aioresponses test mocks → adapter-layer mocks, then bump aiohttp 3.14"
summary:
  The 2026-06-23 fleet bump moved 17 of 18 repos to `aiohttp>=3.14.1` (vcrpy 8.2.1 unblocked the VCR cassette suites).
  **execution-service is the lone holdout**, held on aiohttp **3.13.5** via a `[to...
status: resolved
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [execution, testing, refactor, cve, dependencies, quality-gates]
related:
  [
    plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md,
    plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
  ]
created: 2026-06-23
parent_epic: execution_master
priority: P2
source:
  [
    plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md,
    plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    aiohttp 3.14 fleet bump 2026-06-23 (execution-service held back as the lone <3.14 holdout),
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# execution-service: aioresponses → adapter-layer mocks (unblock aiohttp 3.14)

> **✅ ARCHIVED (archived 2026-07-27)** — sole todo done 2026-07-27 (slot-8), execution-service@`9ce159a7` (confirmed
> ancestor of `origin/live-defi-rollout`). The operator's standing "do not refactor execution-service tests
> mid-active-development" gate that held this doc back was lifted the same day
> (`/plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED #18/19). Archived together with its parent
> `/plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` in the same pass. Per
> `/plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §2.

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

- [x] ✅ [TEST] P2. execution-service — migrate the 8 `aioresponses` test files to adapter-layer mocking — DONE
      2026-07-27 (slot-8), execution-service@9ce159a7. Patched each adapter's own HTTP-issuing method directly
      (`_post_json`/`_get_json`/`_delete` on `KalshiAdapter`/`PolymarketCLOBAdapter`/`OneXBetAdapter`, `_post_json` on
      `JitoBundleProvider`, `_make_request` on `MatchbookAdapter`) or, for connectors that construct
      `aiohttp.ClientSession`/`_make_session` inline with no such wrapper (Hyperliquid connector + bridge, the 5 Solana
      protocol connectors), a shared `FakeAiohttpSession`/`FakeAiohttpResponse` test double + `patch_aiohttp_session()`
      context manager added at `execution-service/tests/aiohttp_test_utils.py` — preserves every original assertion
      incl. error-injection paths (179 tests green). Removed `aioresponses` from `pyproject.toml`
      `[project.dependencies]` + `workspace-constraints.toml` + `canonical-dependency-manifest.json`
      (unified-trading-pm@0f9dc00b4). Removed the `aiohttp>=3.13.4,<3.14.0` line from execution-service's
      `[tool.uv]     override-dependencies`, `uv lock --upgrade-package aiohttp` → 3.14.3. Dropped the 11 aiohttp
      `--ignore-vuln` entries (CVE-2026-34993/47265/50269/54273–54280) — these now live in `QG_PIP_AUDIT_COMMON_IGNORES`
      (`scripts/quality-gates-base/qg-common.sh`, consolidated from the separate base-service.sh/base-library.sh copies
      this todo was written against). QG-green execution-service (full `quality-gates.sh`, 181s) + PM; shipped via
      quickmerge. UAC/UTL untouched — neither declared aioresponses or the override.

## Composes with

`aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (the fleet bump that left this holdout) +
`cve_affected_pinned_deps_remediation_2026_06_18.md` (the broader one-by-one external-dep remediation).
