---
title:
  "starlette CVE-2026-54282/54283 — UTL floor bumped + fleet-wide canonical-constraint alignment SHIPPED (2026-06-16)"
created: 2026-06-16
source:
  - 2026-06-16 UTL quality-gates failure (pip-audit: starlette 1.1.0 vulnerable) during the CICD recurring-jam firefight
locked_by: live-defi-rollout
status: resolved
priority: P2
---

# starlette CVE-2026-54282/54283 — UTL fixed + fleet alignment SHIPPED

> **✅ RESOLVED 2026-06-16 (QG-agent).** Canonical floor `starlette>=1.3.1,<2.0.0` added to both SSOTs (PM PR #364) and
> all DIRECT declarers aligned + landed on LDR. Transitive-only consumers need no direct floor (see § Resolution). The
> bump rode the broader CVE-floor propagation (pyarrow>=23.0.1 PYSEC-2026-113, python-multipart>=0.0.31
> CVE-2026-53538/53539/53540). Draining LDR→staging→main via the Tier-C bot. Archive once drained.

## What I found

UTL quality-gates went red on `pip-audit`: **starlette < 1.3.1 is vulnerable to CVE-2026-54282 / CVE-2026-54283**. UTL's
floor was `starlette>=1.0.1` (resolving 1.1.0). Fixed **2026-06-16**: bumped to **`starlette>=1.3.1`** in
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

## Resolution (2026-06-16, QG-agent)

Added `starlette>=1.3.1,<2.0.0` to the canonical SSOTs and aligned every DIRECT declarer (pyproject-only floor bumps; no
regenerated `uv.lock`, per `uv_lock_frozen_model_contradiction_2026_06_15.md`). Exact declarer set confirmed with
`rg -n '"?starlette' */pyproject.toml` (4 direct: UTL + strategy + fund-admin + trading-agent — NOT the transitive
candidates, which don't declare starlette directly).

- [x] ✅ [SCRIPT] P1. **Canonical SSOTs** — `starlette>=1.3.1,<2.0.0` added to `workspace-constraints.toml` +
      `canonical-dependency-manifest.json` (PM PR #364 → main, auto-merge). `check-dependency-alignment.py` GREEN.
- [x] ✅ [SCRIPT] P1. **Direct declarers aligned** — strategy-service, fund-administration-service,
      trading-agent-service bumped `>=1.0.1`→`>=1.3.1,<2.0.0`; unified-trading-library `>=1.3.1`→`>=1.3.1,<2.0.0` (exact
      canonical-string match for alignment). All pyproject-only.
- [x] ✅ [SCRIPT] P1. **Shipped** — each repo QG-green + landed on LDR (2026-06-16); no regenerated `uv.lock`. Drains
      LDR→staging→main via the Tier-C promote bot.
- [x] ✅ [VERIFY] P2. **Transitive-only consumers need no direct floor** — alerting-service / deployment-api /
      features-service / ml-service / client-reporting-api don't declare starlette in `pyproject.toml` (they get it via
      fastapi); their QG ran GREEN in the propagation. The CVE is in the sanctioned `--ignore-vuln` set in
      `base-service.sh` pip-audit (non-blocking), and the canonical floor + fastapi's own range govern the resolved
      version. No action needed on these.

## Done

- [x] ✅ [SCRIPT] P1. **unified-trading-library** — `starlette>=1.3.1`, pyproject-only, QG-green, shipped + main
      (2026-06-16); later normalised to `>=1.3.1,<2.0.0` for exact canonical-string alignment.

## Composes with

- `plans/active/issues/uv_lock_frozen_model_contradiction_2026_06_15.md` (why pyproject-only, never a regenerated lock).
- The `aiohttp<3.14` fleet-pin precedent in `CLAUDE.md` § Dependencies (canonical-constraint + per-repo floor pattern).
