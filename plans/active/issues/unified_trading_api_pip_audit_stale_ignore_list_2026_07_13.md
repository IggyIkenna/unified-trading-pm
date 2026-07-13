---
doc_type: issue
title: unified-trading-api pip-audit gate RED — stale --ignore-vuln baseline (5 unignored CVEs)
summary: |
  quality-gates.sh pip-audit step fails on unified-trading-api (Codex compliance FAILED: 1 violations, max allowed 0).
  Confirmed pre-existing (byte-identical on clean live-defi-rollout HEAD via stash+re-run) — 5 CVEs (click, cryptography,
  idna, pydantic-settings, starlette) are not covered by the repo's PIP_AUDIT_EXTRA_ARGS ignore list, which only has 2
  stale entries. Blocks every shippable unit in this repo from a green full QG run, not just the auth-migration work
  that surfaced it.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-api]
scope: [engineer]
tags: [pip-audit, dependency-vulnerability, quality-gates, repo-blocker]
related: [utl_reuse_phase2_api_auth_dedup_2026_07_13.md]
created: "2026-07-13"
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
source:
  [utl_reuse_phase2_api_auth_dedup_2026_07_13.md — discovered while shipping the unified-trading-api auth migration]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

`unified-trading-api`'s `quality-gates.sh` fails `pip-audit` (Codex compliance FAILED: 1 violations, max allowed 0) on a
**pre-existing** state — confirmed by stashing my in-flight diff and re-running `pip_audit` against clean
`live-defi-rollout` HEAD (`7f72b92`), which shows the identical 7 findings byte-for-byte.

`scripts/quality-gates.sh` line 35 carries a stale ignore list:

```
PIP_AUDIT_EXTRA_ARGS="--ignore-vuln PYSEC-2024-277 --ignore-vuln PYSEC-2025-183"
```

Current `pip_audit` output (clean tree):

```
Name              Version ID                  Fix Versions
----------------- ------- ------------------- ------------
click             8.3.1   PYSEC-2026-2132     8.3.3
cryptography      46.0.7  GHSA-537c-gmf6-5ccf 48.0.1
idna              3.11    PYSEC-2026-215      3.15
idna              3.11    PYSEC-2026-215      3.15
pydantic-settings 2.13.1  GHSA-4xgf-cpjx-pc3j 2.14.2
starlette         1.1.0   PYSEC-2026-249      1.3.1
starlette         1.1.0   PYSEC-2026-248      1.3.0
```

None of these are in the current ignore list, so every `quality-gates.sh --no-fix` full run on this repo is permanently
RED until either (a) the packages are bumped to their fix versions, or (b) each CVE is triaged and added to the ignore
list with a documented reason (per the pattern already used in sibling repos, e.g. alerting-service's
`PIP_AUDIT_EXTRA_ARGS` carries a much longer curated `--ignore-vuln` list).

# Why it matters

This blocks EVERY shippable unit in `unified-trading-api` from reaching a green full QG run (the merge-prerequisite
gate), not just my auth-migration work. It's a repo-health issue, not scoped to my plan.

# Recommended decision

Triage each of the 5 CVEs:

- `click 8.3.1` → `PYSEC-2026-2132` (command injection in `click.edit()`) — bump to `>=8.3.3` (patch bump, low risk) or
  ignore if `click.edit()` isn't reachable from untrusted input in this service.
- `cryptography 46.0.7` → `GHSA-537c-gmf6-5ccf` — check severity/reachability; likely bump to `>=48.0.1`.
- `idna 3.11` → `PYSEC-2026-215` — bump to `>=3.15`.
- `pydantic-settings 2.13.1` → `GHSA-4xgf-cpjx-pc3j` — bump to `>=2.14.2`.
- `starlette 1.1.0` → `PYSEC-2026-249` / `PYSEC-2026-248` — bump to `>=1.3.1` (FastAPI's transitive dep; verify FastAPI
  pin compatibility before bumping).

## Todos

- [ ] [BACKEND] P1. Triage + bump `click`, `idna`, `pydantic-settings`, `starlette`, `cryptography` in
      `unified-trading-api/uv.lock` to their fix versions (or add curated `--ignore-vuln` entries with a dated reason
      per CVE, matching the sibling-repo pattern) so `quality-gates.sh` pip-audit step goes green. (repo:
      unified-trading-api)
