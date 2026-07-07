---
doc_type: issue
title: 'instruments-service GET /api/data-status is dead code — zero real HTTP consumers, delete-or-document decision needed'
summary:
  'Found 2026-07-07 during an ASTER/CEFI data-status audit: instruments-service own GET /api/data-status endpoint
  (instruments_service/api/data_status.py) returns a flat per-data_type list with no venue or instrument_type
  breakdown. It was built 2026-05-20 as a lean CLI-parity mirror ("expose --operation=status over HTTP") governed by a
  formula-consistency codex contract, not a UI-richness contract. deployment-api built its own, much richer
  venue/instrument_type/honest_coverage computation independently, reading GCS directly — it never called this
  endpoint. Exhaustive grep across the workspace: the only caller is the endpoints own unit test. It is unused, not
  wrong, but undocumented as unused.'
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, deployment-api]
scope: [engineer, admin]
tags: [dead-code, data-status, honest-coverage, hygiene, instruments-service]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    ../../../codex/06-coding-standards/data-status-endpoint-contract.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P2
source: 'ASTER/CEFI instrument-service data-status audit, 2026-07-07 (live API cross-check + code trace)'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: low
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> Filed from an audit that started as "why does the instruments-service data-status dashboard show a per-data-type
> honest-coverage panel that shouldn't be possible for a reference-data service" — the answer turned out to be that
> the dashboard was on the `market-tick-data-service` tab, not `instruments-service`. Tracing the real
> `instruments-service` endpoint down that rabbit hole surfaced this: it exists, it's correct for what it does, and
> nothing calls it.

## What I found

- `instruments-service/instruments_service/api/data_status.py` (`GET /api/data-status`) was created in commit
  `001cf7c3` (2026-05-20): *"Phase 2 P1 of honest_coverage_formula_consolidation_2026_05_19: exposes honest-coverage
  summary over HTTP so deployment-api/UI can consume it without shelling out. Mirrors the `--operation=status` CLI
  path."*
- Its governing codex doc, `codex/06-coding-standards/data-status-endpoint-contract.md`, requires every service's
  `/api/data-status` route to call the canonical `compute_coverage_for_bucket()` / `compute_honest_coverage()` helper
  and return `{"counts": ..., "coverage": float}` — a **formula-consistency** contract (CLI, per-service API, and
  downstream consumers can never drift on the honest-coverage math), not a richness contract. It is satisfied today.
- `deployment-api`'s actual venue / instrument_type / honest_coverage breakdown (the thing the real dashboard renders)
  was built independently and in parallel, in the same May migration, reading GCS directly
  (`deployment_api/services/data_status/instrument_coverage.py:58-59` `resolve_bucket_name(kind="instruments-store")`
  → `read_availability_index`; `deployment_api/services/data_status_drilldown/_core.py:38,103-104`). It never called
  instruments-service's HTTP endpoint.
- Exhaustive grep for callers of this endpoint's path across the workspace: the only hit outside the endpoint's own
  file is `instruments-service/tests/unit/test_api_data_status.py`. `agent-orchestrator/server/mcp/tools.py:202-221`
  has a `data_status()` MCP tool, but its docstring says explicitly it proxies **deployment-api's**
  `/api/data-status/*`, configured via a deployment-api base URL — not instruments-service's.
- Nothing in deployment-api shells out to `python -m instruments_service --operation=status` either, so even the
  "shelling out" alternative this endpoint was meant to obsolete was never actually exercised.

**Net: correct, tested, unused.** It was built to satisfy a real contract but nobody wired it to a real consumer, and
nothing documents that fact — the next engineer who finds it will reasonably assume it's the dashboard's data source.

## Todos

- [ ] [DESIGN] P2. Decide: delete `instruments_service/api/data_status.py` (+ its route registration in
      `instruments_service/api/main.py:20,61` + its unit test), or keep it as an intentional CLI-parity/formula-check
      surface and add a one-line docstring/codex note stating it is **not** the dashboard's data source. Either is
      fine — the contract doc doesn't require the endpoint to exist, only that it's correct if it does.
- [ ] [CODE] P2. Execute whichever the decision above picks. If deleting: confirm the MCP `data_status()` tool and
      any other cross-repo caller genuinely still resolve through deployment-api only (already verified above, but
      re-grep at delete time in case something changed).

## Progress Log

- **2026-07-07** — Filed from the ASTER/CEFI instrument-service data-status audit. No files edited during
  investigation; read-only trace + live API calls only.
