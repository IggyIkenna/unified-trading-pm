---
doc_type: issue
title: market-tick-data-service fastapi constraint misaligned — blocks normal PM quickmerge
summary:
  Discovered 2026-07-28 shipping a docs-only CLAUDE.md change — `scripts/manifest/check-dependency-alignment.py` reports
  market-tick-data-service's `pyproject.toml` fastapi constraint (`>=0.115.0,<0.137.0`) misaligned against the canonical
  spec (`>=0.137.0,<1.0.0`), which fails quickmerge's STAGE 1.5 Dependency Alignment gate for EVERY PM commit, not just
  code changes. Every PM change this session had to route through the `docs(plans):` direct-push carve-out instead of
  normal quickmerge as a result. The installed lock (fastapi 0.135.1) satisfies the OLD constraint but not the canonical
  one, so a real fix needs a `uv lock` regen + MTDS's own quality-gates run, not just a one-line pyproject.toml edit —
  out of scope for the docs session that found it.
status: resolved
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [dependency-alignment, quickmerge, ci, fastapi]
related: [/codex/08-workflows/ci-cd-flow.md]
created: "2026-07-28"
parent_epic: infrastructure_master
source:
  Discovered running quickmerge.sh for a PM docs-only change; confirmed still failing via a direct re-run of
  check-dependency-alignment.py at end of session.
execution_scope: orchestrator-agent
assigned_vm: planning
priority: P1
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: "backend_engineer, slot-8, 2026-07-28"
---

# market-tick-data-service fastapi constraint misaligned — blocks normal PM quickmerge

## Todos

- [x] ✅ [BACKEND] P1. **DONE 2026-07-28.** The `fastapi` constraint was already bumped to `>=0.137.0,<1.0.0` and
      `uv.lock` already regenerated (locked at fastapi 0.140.7) via `market-tick-data-service@52cb0808` ("fix(tests):
      fastapi>=0.137/starlette>=1.3.1 route-introspection via UTL get_route_paths") — confirmed via direct
      `pyproject.toml`/`uv.lock` read at current HEAD `d7df92beb`.
      `python3     unified-trading-pm/scripts/manifest/check-dependency-alignment.py --json` reports
      `"aligned": true, "count": 0`. Local `quality-gates.sh` reruns at HEAD crashed 4× on this shared host's known
      memory contention (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` — pytest worker silently
      killed mid-run at 32-67%, swap exhaustion each time, no code-related traceback) rather than a real test failure.
      Used the stronger, contention-free signal instead: `market-tick-data-service`'s `quality-gates-v2` CI workflow ran
      GREEN at the exact current HEAD `d7df92bebb52df20478b2db036cd432556a7740b` — run
      [30370413969](https://github.com/IggyIkenna/market-tick-data-service/actions/runs/30370413969),
      `conclusion=success`, completed 2026-07-28T14:51:06Z — confirming nothing breaks on the bumped fastapi. No code
      change needed from this task; both halves of the done_definition are satisfied.
