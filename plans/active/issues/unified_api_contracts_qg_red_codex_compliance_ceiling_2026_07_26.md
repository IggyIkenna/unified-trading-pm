---
doc_type: issue
title: unified-api-contracts QG RED — Codex compliance ceiling (3 violations, max allowed 2)
summary: >-
  unified-api-contracts's quality-gates.sh fails "Codex compliance FAILED: 3 violations (max allowed: 2)". Discovered
  while rolling out an unrelated scripts/setup.sh fix (infra_satellite_ao_dispatch_batch1-002) — confirmed pre-existing
  and unrelated to that change.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [quality-gates, coding-standards, codex-compliance]
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
source:
  [
    "unified-api-contracts quality-gates.sh run 2026-07-26 (slot-11, task infra_satellite_ao_dispatch_batch1-002)",
    "unified_api_contracts/canonical/partition_paths.py (1297L)",
    "scripts/setup.sh (pip-install fallback pattern)",
  ]
---

## What I found

Running `bash scripts/quality-gates.sh` on `unified-api-contracts` fails at the CODEX COMPLIANCE ceiling check:

```
❌ Codex compliance FAILED: 3 violations (max allowed: 2)
```

The 2 contributing findings:

1. `❌ Files exceed 900 lines: ./unified_api_contracts/canonical/partition_paths.py: 1297 L` — pre-existing, unrelated
   to any change in this session.
2. `❌ Use 'uv pip install' not 'pip install' in scripts` on `scripts/setup.sh`'s pip fallback line. Confirmed
   **pre-existing**: `git show 7e90f42e:scripts/setup.sh` (the commit immediately before my fix) already had
   `"$PYTHON_CMD" -m pip install uv --quiet` at line 362 — the same violation class existed before my change; my
   fleet-wide `scripts/setup.sh` sync (task `infra_satellite_ao_dispatch_batch1-002`, source:
   `issues/uv_pin_fleet_drift_2026_06_22.md`) intentionally keeps a pip fallback as the documented "last resort" path,
   so this specific finding is unavoidable in the new template too and was already present in the old one.

This repo's ceiling (`max allowed: 2`) is evidently already fully consumed by other pre-existing debt, so any commit to
this repo — including my content-neutral setup.sh sync — now trips it into RED.

## Why it matters

Blocks the `scripts/setup.sh` fleet-rollout leg for `unified-api-contracts` (part of
`plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md`) and blocks every other pending commit to this repo
under the green-tree rule until either the ceiling is raised or `partition_paths.py` is split under 900 lines.

## Recommended decision

Split `unified_api_contracts/canonical/partition_paths.py` (1297L) under the 900-line cap, OR bump this repo's
`max allowed` codex-compliance ceiling by 1 if the maintainer judges the pip-fallback line acceptable long-term (it's
the documented last-resort branch, not a first-choice call site).

- [ ] [SCRIPT] P2. Split `unified_api_contracts/canonical/partition_paths.py` (1297L) into cohesive sub-modules to bring
      it under the 900-line file cap, OR explicitly raise this repo's codex-compliance violation ceiling by 1 to account
      for the setup.sh pip-fallback line (last-resort branch, same pattern already present pre-fix). **Done when**:
      `bash scripts/quality-gates.sh` in `unified-api-contracts` no longer fails the codex-compliance ceiling check.
      Repo: unified-api-contracts.
