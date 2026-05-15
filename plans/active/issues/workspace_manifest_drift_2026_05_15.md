---
title: workspace-manifest.json dependency drift — 10 misalignments
created: 2026-05-15
author: slot-8
source:
  - scripts/manifest/check-dependency-alignment.py
locked_by: live-defi-rollout
---

## What I found

`python3 scripts/manifest/check-dependency-alignment.py` reported **10 misalignments** across 2 repos.

### unified-trading-library — 1 issue

| Type | Dep | pyproject | canonical |
|---|---|---|---|
| external_version_mismatch | freezegun | `>=1.5.0,<2.0.0` | `>=1.2.2,<2.0.0` |

**Root cause**: UTL intentionally requires a newer freezegun floor (1.5.0) for test utilities
that rely on newer `tick()` behavior. MTDS uses the canonical `>=1.2.2`. Updating canonical to
`>=1.5.0` would break MTDS alignment.

**Recommended fix**: Update UTL's `pyproject.toml` freezegun lower bound down to `>=1.2.2` (safe
— no UTL code uses <1.5.0-specific APIs), OR update MTDS to `>=1.5.0` in the same PR.
**Owner**: UTL + MTDS — coordinate pyproject.toml update in a single dep-bump PR.

### e2e-testing — 9 issues

#### Internal deps in manifest but not in pyproject (5 items)

The manifest's `repositories.e2e-testing.dependencies` lists these internal repos, but
`e2e-testing/pyproject.toml` does not import them directly (likely removed during a prior refactor
without updating the manifest):

- `unified-api-contracts`
- `execution-service`
- `strategy-service`
- `risk-and-exposure-service`
- `position-balance-monitor-service`

**Recommended fix**: Remove these 5 entries from `workspace-manifest.json`
`repositories.e2e-testing.dependencies` — they are test-runner imports, not install-time deps.
**Owner**: e2e-testing owner (check that removing doesn't break `check-dep-alignment` CI step).

#### External version mismatches (4 items)

| Dep | pyproject | canonical |
|---|---|---|
| httpx | `>=0.27` | `>=0.28.1,<1.0.0` |
| pytest | `>=8.0` | `>=9.0.3,<10.0.0` |
| pytest-asyncio | `>=0.24` | `>=0.25.0,<2.0.0` |
| websockets | `>=13.0` | `>=14.0,<15.0.0` |

**Root cause**: e2e-testing pyproject.toml has loose lower bounds that predate the workspace
canonical update. The canonical versions are newer and stricter.

**Recommended fix**: Update `e2e-testing/pyproject.toml` to pin to canonical versions:
```
httpx>=0.28.1,<1.0.0
pytest>=9.0.3,<10.0.0
pytest-asyncio>=0.25.0,<2.0.0
websockets>=14.0,<15.0.0
```
**Owner**: e2e-testing (low risk — these are test-only deps).

## Why it matters

Loose version floors in e2e-testing mean CI could silently install older versions that diverge
from the versions actually used in service repos. The freezegun mismatch means alignment checks
fail, masking real future drift.

## Recommended decision

- P1 (this week): Fix e2e-testing pyproject.toml external pins (4 changes, ~30 min).
- P1 (this week): Clean manifest `e2e-testing.dependencies` of 5 stale internal entries.
- P2 (next cycle): Align freezegun across UTL + MTDS in a coordinated dep-bump PR.

DAG SVG regenerated at `WORKSPACE_MANIFEST_DAG.svg` (no structural changes — same dep graph,
just confirming regeneration ran clean).
