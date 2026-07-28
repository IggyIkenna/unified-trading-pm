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
status: open
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
resolved_by:
---

# market-tick-data-service fastapi constraint misaligned — blocks normal PM quickmerge

## Todos

- [ ] [BACKEND] P1. In `market-tick-data-service`, bump the `fastapi` dependency constraint in `pyproject.toml` from
      `>=0.115.0,<0.137.0` to the canonical `>=0.137.0,<1.0.0`, regenerate `uv.lock` (the currently-locked 0.135.1 does
      not satisfy the new floor, so this is a real version bump, not just a spec-string edit), then run
      `market-tick-data-service`'s own `quality-gates.sh` to confirm nothing breaks on the newer fastapi before
      shipping. Definition of done: `python3 unified-trading-pm/scripts/manifest/check-dependency-alignment.py --json`
      reports `"aligned": true`, and `market-tick-data-service`'s quality-gates.sh is green on the bumped lock.
