---
title: "starlette CVE-2026-54282/54283 — UTL floor bumped to >=1.3.1; fleet-wide canonical-constraint alignment pending"
created: 2026-06-16
source:
  - 2026-06-16 UTL quality-gates failure (pip-audit: starlette 1.1.0 vulnerable) during the CICD recurring-jam firefight
locked_by: live-defi-rollout
status: active
priority: P2
---

# starlette CVE-2026-54282/54283 — UTL fixed, fleet alignment pending

## What I found

UTL quality-gates went red on `pip-audit`: **starlette < 1.3.1 is vulnerable to CVE-2026-54282 / CVE-2026-54283**.
UTL's floor was `starlette>=1.0.1` (resolving 1.1.0). Fixed **2026-06-16**: bumped to **`starlette>=1.3.1`** in
`unified-trading-library/pyproject.toml`, shipped **pyproject-only** (NOT a regenerated `uv.lock` — committing a
re-resolved internal-editable lock restarts the Tier-C runaway, per
`plans/active/issues/uv_lock_frozen_model_contradiction_2026_06_15.md`; CI/local both re-resolve from the range, nothing
uses `--frozen`), QG-green, then force-synced UTL main=LDR.

The same CVE applies to **every other repo that declares starlette** (direct or transitive). UTL is fixed; the rest are
not yet aligned, and there is no canonical constraint pinning the floor — so a fresh resolve elsewhere can still pull a
vulnerable starlette.

## Why it matters

- Any repo whose QG runs `pip-audit` and resolves starlette < 1.3.1 will go **red** the same way UTL did — a latent
  fleet-wide QG-jam waiting to trip repo-by-repo.
- Without a canonical floor in `workspace-constraints.toml` + `canonical-dependency-manifest.json`, the dependency
  tooling has no SSOT to enforce/propagate the safe floor (mirrors the `aiohttp<3.14` fleet-pin pattern).

## Recommended decision

Add `starlette>=1.3.1` to the canonical constraint SSOTs and align the declaring repos (pyproject-only floor bumps;
**never** commit a regenerated `uv.lock`). Candidate declaring repos to verify + align (grep each `pyproject.toml` for
`starlette` — direct floors AND transitive via fastapi):

- [ ] [SCRIPT] P1. Add `starlette>=1.3.1` (`,<2.0.0`) to PM `cursor-configs`/`configs` `workspace-constraints.toml` +
      `canonical-dependency-manifest.json` (+ the UAC-packaged mirror if it carries starlette). SSOT first.
- [ ] [SCRIPT] P1. Grep the fleet for `starlette` declarations and bump each direct floor to `>=1.3.1`
      (candidates observed: strategy-service, fund-administration-service, trading-agent-service; transitive via fastapi:
      alerting-service, deployment-api, features-service, ml-service, client-reporting-api). Confirm the exact set with
      `rg -n '"?starlette' */pyproject.toml` before editing — no guesswork.
- [ ] [SCRIPT] P1. For each: pyproject-only floor bump, `quality-gates.sh` green, quickmerge → LDR. Do **NOT** commit a
      regenerated `uv.lock` (convergence-safe path; ref `uv_lock_frozen_model_contradiction_2026_06_15.md`).
- [ ] [VERIFY] P2. Confirm each aligned repo's `pip-audit` no longer flags starlette and the floor holds on a fresh
      resolve.

## Done

- [x] ✅ [SCRIPT] P1. **unified-trading-library** — `starlette>=1.3.1`, pyproject-only, QG-green, shipped + main
      (2026-06-16).

## Composes with

- `plans/active/issues/uv_lock_frozen_model_contradiction_2026_06_15.md` (why pyproject-only, never a regenerated lock).
- The `aiohttp<3.14` fleet-pin precedent in `CLAUDE.md` § Dependencies (canonical-constraint + per-repo floor pattern).
