---
doc_type: issue
title: Canonical fastapi ceiling contradicts ml-service's deliberate <0.138.0 security fix — SSOT vs repo mismatch
summary: |
  workspace-constraints.toml pins fastapi<0.137.0 with a dated comment ("Phase 1.5b 2026-06-18: fastapi 0.137.2 pulls
  starlette 1.3.1 (breaking)") explicitly AVOIDING starlette>=1.3.1. ml-service@4d16341 (2026-07-13, same day, resolved
  issue ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md) deliberately raised its OWN fastapi
  ceiling to <0.138.0 + added an override-dependencies starlette>=1.3.1 floor specifically TO FIX 9 pip-audit CVEs —
  the opposite reasoning from the June decision. PM's check-dependency-alignment.py now reports ml-service misaligned
  against the canonical (fastapi<0.137.0), which blocks EVERY PM push (STAGE 1.5 dependency-alignment is a hard gate)
  until resolved.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [ml-service, unified-trading-pm]
scope: [engineer]
tags: [dependency-alignment, fastapi, starlette, ssot-contradiction, canonical-manifest]
related:
  [
    plans/active/issues/ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md,
    plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    workspace-constraints.toml,
    canonical-dependency-manifest.json,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source:
  discovered while shipping a routine PM plan-checkbox flip (utl_reuse_phase0_guardrails-adjacent onchain fix,
  unrelated), 2026-07-13
assigned_vm: planning
resolved_by: slot-3
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: unclear
depends_on: []
---

## What I found

`workspace-constraints.toml:35-36`:

```
# CEILING <0.137 (Phase 1.5b 2026-06-18): fastapi 0.137.2 pulls starlette 1.3.1 (breaking — see starlette below). Keep
# working 0.135.1. SSOT: plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md
fastapi = "fastapi>=0.115.0,<0.137.0"
```

`ml-service/pyproject.toml` (shipped `ml-service@4d16341`, same day, per
`plans/active/issues/ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md` — status `resolved`):

```
"fastapi>=0.115.0,<0.138.0",
...
[tool.uv]
override-dependencies = ["starlette>=1.3.1"]
```

These two decisions directly contradict each other on whether `starlette>=1.3.1` is safe: the June decision calls it
"breaking" and caps fastapi specifically to avoid it; the July fix deliberately forces it (via `override-dependencies`,
scoped to ml-service) to clear 2 CVEs (PYSEC-2026-248/249). Nobody updated
`workspace-constraints.toml`/`canonical-dependency-manifest.json` when the July fix shipped, so
`scripts/manifest/check-dependency-alignment.py` now reports ml-service as misaligned — which blocks the PM
dependency-alignment STAGE 1.5 gate for **every** PM push, not just ones touching ml-service.

I did NOT apply `fix_external_dependency_alignment.py --apply` (which would silently downgrade ml-service's ceiling back
to `<0.137.0`, undoing the resolved security fix) nor hand-edit the canonical ceiling upward (which would propagate
`starlette>=1.3.1` fleet-wide without confirming the June "breaking" finding no longer applies). Per
`scripts/manifest/README-DEPENDENCY-ALIGNMENT.md`: "If the canonical needs to change... edit workspace-constraints.toml
deliberately" — that's a judgment call this issue exists to route, not something to silently script through.

## Why it matters

- **Blocks all PM pushes** via the dependency-alignment hard gate until resolved one way or the other.
- **Genuine unresolved question**: was starlette 1.3.1's "breaking" behavior (June 18 finding) ever root-caused, or just
  avoided? If ml-service's `override-dependencies` forcing starlette>=1.3.1 passed its own full test suite +
  quality-gates.sh clean (per the resolved issue's Progress Log), that's evidence the June "breaking" characterization
  may have been repo-specific or already fixed upstream in starlette 1.3.x — but nobody has re-verified this against
  whatever OTHER repo hit the original June breakage.

## Recommended decision

1. Re-read `plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md` to find which repo/test originally
   observed starlette 1.3.1 as breaking.
2. Confirm whether that specific breakage still reproduces on current starlette 1.3.1 (library may have shipped a patch
   since June 18).
3. If genuinely fixed upstream: raise the canonical fastapi ceiling to `<0.138.0` (`workspace-constraints.toml` +
   regenerate `canonical-dependency-manifest.json` via `generate_canonical_dependency_manifest.py`), propagate to any
   repo needing the bump.
4. If still breaking for that other repo: keep the canonical ceiling as-is, but explicitly carve out ml-service's
   `override-dependencies` pin as a documented, intentional exception (comment in `workspace-constraints.toml` noting
   ml-service is exempted + why), and teach `check-dependency-alignment.py` about the exception so it stops permanently
   red-gating PM.

## Todos

- [x] ✅ [BACKEND] P1. Resolve the canonical fastapi/starlette ceiling contradiction per the recommended decision above
      — either raise the canonical ceiling (if the June breakage is confirmed fixed upstream) or add a documented
      per-repo exception for ml-service (repo: unified-trading-pm) — RESOLVED via option 4 (documented exception),
      `unified-trading-pm@<this commit>`. Directly tested whether the June 18 `_IncludedRouter`/`.path` breakage still
      reproduces, in two isolated venvs:
  - `fastapi==0.137.2` + `starlette==1.3.1` (the exact combo the June note names): **still reproduces** —
    `app.include_router(sub)` produces an `_IncludedRouter` entry in `app.routes` with no `.path` attribute
    (`getattr(r, "path", "<<NO .path ATTR>>")` confirms it). The June finding is real and NOT fixed upstream as of
    2026-07-13.
  - `fastapi==0.136.3` + `starlette==1.3.1` (ml-service's ACTUAL locked resolution, forced via
    `[tool.uv] override-dependencies = ["starlette>=1.3.1"]`): does **not** reproduce — every route resolves as a plain
    `Route`/`APIRoute` with a valid `.path`. The break is specific to fastapi `0.137.x`'s router-wrapping change, not to
    starlette `1.3.1` itself. ml-service is safe today only because its resolver happened to stay below `0.137.0`
    despite its ceiling technically allowing up to `<0.138.0` — that's incidental, not a guarantee, so raising the fleet
    canonical ceiling to `<0.138.0` would let OTHER repos' resolvers land on the broken `0.137.x` and reproduce the June
    breakage.
  - Decision: kept the canonical `fastapi`/`starlette` ceilings in `workspace-constraints.toml` UNCHANGED (still
    `<0.137.0` / `<1.3.0`). Added a `PER_REPO_EXTERNAL_EXCEPTIONS` dict to
    `scripts/manifest/check-dependency-alignment.py` — a single `("ml-service", "fastapi"): "fastapi>=0.115.0,<0.138.0"`
    entry with an inline comment carrying the full investigation + explicit "do not generalize this fleet-wide" warning
    — so the checker recognizes ml-service's declared ceiling as an intentional, reviewed divergence instead of flagging
    it every run. Verified: `check-dependency-alignment.py` (both `--repo ml-service` and the full fleet) now reports
    `OK: All dependencies aligned` — the PM STAGE 1.5 hard gate is unblocked.
