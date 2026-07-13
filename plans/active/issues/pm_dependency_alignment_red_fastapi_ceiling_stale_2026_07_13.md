---
doc_type: issue
title: PM dependency-alignment gate RED — canonical fastapi ceiling stale vs ml-service's already-shipped security bump
summary: |
  `bash scripts/quickmerge.sh` for unified-trading-pm hard-fails at STAGE 1.5 (Dependency Alignment) for every agent
  right now: `check-dependency-alignment.py` reports ml-service's `pyproject.toml` fastapi spec
  (`fastapi>=0.115.0,<0.138.0`) mismatched against `canonical-dependency-manifest.json`'s
  (`fastapi>=0.115.0,<0.137.0`). Root cause: ml-service shipped a deliberate, tracked pip-audit CVE remediation
  (`ml-service@4d16341`, "fix(deps): bump pillow, cryptography, pydantic-settings, starlette — clear 9 pip-audit
  CVEs") that raised its own fastapi ceiling to `<0.138.0` (with an explicit `override-dependencies =
  ["starlette>=1.3.1"]` to force the patched starlette past the transitive floor) — but the PM-owned
  `workspace-constraints.toml` / `canonical-dependency-manifest.json` were never updated to match, so every OTHER
  quickmerge for unified-trading-pm (docs, plans, any file) now fails this pre-flight gate regardless of what it
  actually touches.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, ml-service]
scope: [engineer, admin]
tags: [dependency-alignment, fastapi, starlette, pip-audit, cve, quickmerge, repo-blocker]
related:
  [
    plans/active/issues/ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md,
    plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    scripts/manifest/README-DEPENDENCY-ALIGNMENT.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: backend-engineer
drift_direction: correct-codex
source:
  [
    ml-service/pyproject.toml#L30,
    ml-service/pyproject.toml#L98-103,
    workspace-constraints.toml#L35-36,
    canonical-dependency-manifest.json#L110-113,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# PM dependency-alignment gate RED — stale fastapi ceiling

> Filed by slot 6 while shipping `utl_reuse_phase8_codex_ssot_archive-001` (unrelated docs-only Phase 8 codex work) —
> the quickmerge pre-flight gate is failing on unrelated pre-existing drift, blocking my ship and (per the mechanism
> below) every other agent's unified-trading-pm quickmerge too.

## What I found

`STAGE 1.5: Dependency Alignment (PM)` in `bash scripts/quickmerge.sh` runs
`scripts/manifest/check-dependency-alignment.py` unconditionally (not scoped to `--files`), so it fails for ANY
quickmerge invocation on this repo right now, not just mine:

```
{
  "aligned": false,
  "issues": [
    {
      "repo": "ml-service",
      "type": "external_version_mismatch",
      "dep": "fastapi",
      "pyproject_spec": "fastapi>=0.115.0,<0.138.0",
      "canonical_spec": "fastapi>=0.115.0,<0.137.0"
    }
  ]
}
```

**Verified pre-existing, not mine**: my staged diff touches only `codex/06-coding-standards/README.md`,
`codex/04-architecture/agent-orchestrator-overview.md`,
`codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`, and two plan/issue docs — zero relation to
ml-service or dependency manifests.

**Root cause, both sides checked:**

- `ml-service/pyproject.toml:30` — `fastapi>=0.115.0,<0.138.0` (raised from `<0.137.0`). Commit `ml-service@4d16341`
  "fix(deps): bump pillow, cryptography, pydantic-settings, starlette — clear 9 pip-audit CVEs" — a deliberate, tracked
  security fix (referenced issue doc:
  `plans/active/issues/ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md`). The commit's own in-file
  comment explains: `fastapi<0.137.0` only requires `starlette>=1.1.0`, which stays on the vulnerable 1.2.1
  (PYSEC-2026-248/249) even after a re-lock — so ml-service both raised the fastapi ceiling to `<0.138.0` AND added an
  explicit `[tool.uv] override-dependencies = ["starlette>=1.3.1"]` to force the patched starlette.
- `workspace-constraints.toml:35-36` — still `fastapi>=0.115.0,<0.137.0`, with a comment from an OLDER episode: "CEILING
  <0.137 (Phase 1.5b 2026-06-18): fastapi 0.137.2 pulls starlette 1.3.1 (breaking — see starlette below). Keep working
  0.135.1." referencing `plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md` (a MONTH-OLD issue,
  superseded by today's fresh pip-audit fix). This ceiling was deliberately capped at the time because bumping past it
  pulled a "breaking" starlette — but ml-service's fresh fix appears to address that exact breaking concern via the
  explicit `override-dependencies` pin, not by ignoring it.
- `canonical-dependency-manifest.json:111-113` — still derived from the stale `workspace-constraints.toml` ceiling.

## Why it matters

This is a HARD quickmerge gate (`STAGE 1.5`, exit 1, not advisory) that fires for EVERY unified-trading-pm push right
now, regardless of what files are being shipped — it is currently blocking the entire fleet's ability to ship PM
docs/plans, not just this one task. It also risks silent scope creep if fixed carelessly: raising the WORKSPACE-WIDE
`workspace-constraints.toml` ceiling affects every repo pinned to fastapi (not just ml-service), and other repos may not
have ml-service's `starlette>=1.3.1` override — if a fleet-wide dependency-version-bump propagation
(`update-dependency-version.yml`) later fans this ceiling out, an un-audited repo could inherit the newer fastapi
without the compatibility fix ml-service applied.

## Recommended decision

Whoever picks this up should NOT blindly bump `workspace-constraints.toml`'s ceiling without first confirming: (a) the
starlette-breaking concern from the 2026-06-18 issue is genuinely resolved by ml-service's `override-dependencies`
approach (not merely deferred), and (b) whether any OTHER repo currently pinned near the fastapi ceiling would need the
same starlette override if canonical is raised workspace-wide (run
`scripts/manifest/validate-dependency-conflicts.py --regenerate` after the constraint edit to confirm no new transitive
conflicts). Recommended path once confirmed:

1. Edit `workspace-constraints.toml:36` to `fastapi>=0.115.0,<0.138.0`, updating the adjacent comment to reference
   today's pip-audit fix issue doc instead of the stale 2026-06-18 one.
2. Regenerate `canonical-dependency-manifest.json` via `scripts/manifest/generate_canonical_dependency_manifest.py`.
3. Run `scripts/manifest/check-dependency-alignment.py --json` to confirm the fleet is aligned again.
4. Run `scripts/manifest/validate-dependency-conflicts.py --regenerate` to confirm no new transitive conflicts appear
   for any OTHER repo.

## Todos

- [ ] [INFRA] P1. Confirm the starlette-breaking concern from
      `plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md` is resolved by ml-service's
      `override-dependencies = ["starlette>=1.3.1"]` approach, then update `workspace-constraints.toml`'s fastapi
      ceiling to `<0.138.0` + regenerate `canonical-dependency-manifest.json` + verify no new transitive conflicts for
      any other repo. (repo: unified-trading-pm)
