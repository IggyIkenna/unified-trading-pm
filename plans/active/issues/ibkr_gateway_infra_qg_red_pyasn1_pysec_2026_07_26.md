---
doc_type: issue
title: ibkr-gateway-infra QG RED — pyasn1 0.6.3 vulnerable (PYSEC-2026-3455/3456/3457)
summary: >-
  ibkr-gateway-infra's quality-gates.sh fails pip-audit on pyasn1 0.6.3 (3 CVEs, fixed in 0.6.4+). Discovered while
  rolling out an unrelated scripts/setup.sh fix (infra_satellite_ao_dispatch_batch1-002) — confirmed pre-existing and
  unrelated to that change (pip-audit runs against the repo's declared/locked Python deps, untouched by a bash
  bootstrap-script sync).
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [ibkr-gateway-infra]
scope: [engineer]
tags: [quality-gates, security, dependency-bump, pip-audit]
related: []
created: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
priority: P2
depends_on: []
source: ["ibkr-gateway-infra quality-gates.sh run 2026-07-26 (slot-11, task infra_satellite_ao_dispatch_batch1-002)"]
---

## What I found

Running `bash scripts/quality-gates.sh` on `ibkr-gateway-infra` fails pip-audit:

```
❌ pip-audit vulnerabilities found
  pyasn1 0.6.3: PYSEC-2026-3456 — ...
  pyasn1 0.6.3: PYSEC-2026-3457 — ...
  pyasn1 0.6.3: PYSEC-2026-3455 — ...
```

Pre-existing and unrelated to my session's change (a `scripts/setup.sh` bash bootstrap sync — pip-audit scans the repo's
locked Python dependency graph, which I never touched).

## Why it matters

Blocks the `scripts/setup.sh` fleet-rollout leg for `ibkr-gateway-infra` (part of
`plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md`) and blocks every other pending commit to this repo
under the green-tree rule until the dependency is bumped.

## Recommended decision

Bump `pyasn1` to >=0.6.4 (fixes all 3 CVEs) in this repo's `pyproject.toml`/`uv.lock`, re-lock, and verify pip-audit is
clean.

- [ ] [SCRIPT] P2. Bump `pyasn1` to `>=0.6.4` in `ibkr-gateway-infra/pyproject.toml`, re-lock (`uv lock`), and confirm
      `bash scripts/quality-gates.sh` no longer reports PYSEC-2026-3455/3456/3457. Repo: ibkr-gateway-infra.
