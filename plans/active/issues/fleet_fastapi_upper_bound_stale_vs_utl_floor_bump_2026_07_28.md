---
doc_type: issue
title:
  unified-trading-library's fastapi>=0.137/starlette>=1.3.1 bump CONTRADICTS the canonical-dependency-manifest SSOT — QG
  broken repo-wide
summary: >-
  unified-trading-library@3b99d19d bumped its own pyproject.toml fastapi/starlette floor to >=0.137.0/>=1.3.1, but
  unified-trading-pm's canonical-dependency-manifest.json (the fleet SSOT) still pins fastapi<0.137.0/starlette<1.3.0 —
  confirmed via the PM's own check-dependency-alignment.py, which flags unified-trading-library AND client-reporting-api
  as the ones drifted from canonical (not the ~10 other repos still on the old bound). This blocks quality-gates.sh
  fleet-wide the moment a repo's .venv is refreshed: either uv sync fails outright (direct pyproject conflict) or a
  stale pre-bump .venv raises ImportError: iter_route_contexts on any unified_trading_library import. Direction (roll
  canonical forward vs revert UTL) is a genuine open-ended judgment call, not something a worker should decide
  unilaterally.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library, client-reporting-api, market-tick-data-service]
scope: [engineer, admin]
tags: [dependencies, fastapi, starlette, ssot-contradiction, quality-gates, cross-repo]
related: [/codex/06-coding-standards/quality-gates.md]
created: 2026-07-28
priority: P0
parent_epic: infrastructure_master
source:
  "slot-3, data_engineering, discovered while verifying defi_satellite_ao_dispatch_batch1-007 (market-tick-data-service
  Orca tick-array decode)"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

> **BIG FINDING — cross-repo SSOT contradiction, operator/main judgment needed on direction.** Filed per CLAUDE.md §
> Governance HARD RULES "Findings triage" (big finding = cross-repo / SSOT contradiction → notify + issue doc). Do NOT
> auto-resolve by picking a direction — see "Recommended decision" below for why this is genuinely ambiguous.

## What I found

`unified-trading-library@3b99d19d` ("fix(service_framework): fastapi>=0.137/starlette>=1.3.1 _IncludedRouter
route-introspection") bumped UTL's own `pyproject.toml` fastapi floor to `fastapi>=0.137.0,<1.0.0`. UTL is an
`editable = true` path dependency (`tool.uv.sources.unified-trading-library`) for essentially every service repo, so
this is a fleet-wide floor bump, not a local one.

At least 10 consuming repos still cap fastapi at the OLD `fastapi>=0.115.0,<0.137.0` upper bound (verified via
`grep '"fastapi>=' pyproject.toml` across the fleet on a fresh `origin/live-defi-rollout` pull, 2026-07-28):

- market-tick-data-service
- execution-service
- features-service
- deployment-service
- strategy-service
- agent-orchestrator
- alerting-service
- deployment-api
- fund-administration-service
- greeks-service
- unified-trading-api

Only `client-reporting-api` has already been bumped to `fastapi>=0.137.0,<1.0.0` (matching UTL). `instruments-service`
and `market-data-processing-service` don't declare a fastapi bound at all (unaffected or resolved differently — not
verified further here).

**Confirmed broken in market-tick-data-service** (reproduced on a clean tree, my own diff stashed away first): `uv sync`
fails outright with `No solution found when resolving dependencies` (MTDS's `<0.137.0` directly conflicts with UTL's
`>=0.137.0`). The STALE `.venv` (resolved before UTL's bump, fastapi 0.135.1 installed) still boots, but
`from unified_trading_library import setup_events` (used by `tests/conftest.py` and directly by
`orca_whirlpool_state_handler.py`) now raises at import time:

```
ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'
```

because UTL's `service_framework/fastapi_factory.py` now imports `iter_route_contexts`, which only exists in
fastapi>=0.137. `bash scripts/quality-gates.sh` fails at TEST COLLECTION (before any test runs) with this exact
traceback. This blocks **every** test in market-tick-data-service, not just ones touching my file — a hard repo-wide QG
red.

**This is not a simple "10 repos are stale" gap — `unified-trading-library` itself is the one out of alignment with the
workspace SSOT.** `unified-trading-pm/canonical-dependency-manifest.json` (generated from `workspace-constraints.toml`,
the declared fleet-wide external-dependency SSOT) still pins:

```
fastapi>=0.115.0,<0.137.0
starlette>=1.1.0,<1.3.0
```

Running the PM's own `scripts/manifest/check-dependency-alignment.py --json` on a fresh `live-defi-rollout` pull
confirms **`unified-trading-library` AND `client-reporting-api`** are the ones that drifted from canonical (not the
other ~10 repos, which correctly still match canonical):

```json
{"repo": "unified-trading-library", "type": "external_version_mismatch", "dep": "fastapi",
 "pyproject_spec": "fastapi>=0.137.0,<1.0.0", "canonical_spec": "fastapi>=0.115.0,<0.137.0"}
{"repo": "unified-trading-library", "type": "external_version_mismatch", "dep": "starlette",
 "pyproject_spec": "starlette>=1.3.1,<2.0.0", "canonical_spec": "starlette>=1.1.0,<1.3.0"}
{"repo": "client-reporting-api", "type": "external_version_mismatch", "dep": "fastapi",
 "pyproject_spec": "fastapi>=0.137.0,<1.0.0", "canonical_spec": "fastapi>=0.115.0,<0.137.0"}
```

So my first-pass framing (below, kept for the reproduction evidence) had the direction backwards.

## Why it matters

Whichever direction is correct, this is currently a live SSOT contradiction blocking `quality-gates.sh` fleet-wide:
`unified-trading-library`'s actual runtime code (`service_framework/fastapi_factory.py`) now imports
`iter_route_contexts`, which genuinely only exists in fastapi>=0.137 — so UTL's bump wasn't cosmetic, it tracks a real
code dependency the commit (`3b99d19d`, "fix(service_framework): fastapi>=0.137/starlette>=1.3.1 _IncludedRouter
route-introspection") needed. Every OTHER repo that still matches the canonical `<0.137.0` bound and depends on UTL
(editable path dependency) now either (a) fails `uv sync` outright once its `.venv` needs a fresh resolve (direct
pyproject conflict), or (b) silently runs a STALE pre-bump `.venv` that raises `ImportError: iter_route_contexts` the
moment it imports anything from `unified_trading_library` — exactly what happened to my own
`defi_satellite_ao_dispatch_batch1-007` task (implement Orca Whirlpool tick-array decode in market-tick-data-service),
verified pre-existing via `git stash` + re-run on a clean HEAD.

## Recommended decision — genuinely ambiguous, needs operator/main judgment

Two structurally different fixes, and picking wrong either wastes work or leaves the fleet on a stale/vulnerable fastapi
indefinitely:

- **(A) Roll UTL's bump forward into canonical**: if fastapi>=0.137/starlette>=1.3.1 is the correct fleet target (e.g.
  the old floor has a known issue, or 0.137 is required for other reasons beyond this one route-introspection fix),
  update `workspace-constraints.toml` + regenerate `canonical-dependency-manifest.json` to the new floor, then bump +
  `uv lock`/`uv sync`/full-QG EVERY consuming repo still on the old bound (≥10, listed below) to match. This is real,
  fleet-wide work.
- **(B) Revert UTL's bump, find a narrower fix**: if the `_IncludedRouter route-introspection` fix genuinely doesn't
  need a floor bump this wide (e.g. `iter_route_contexts` could be avoided, or the compatibility issue only affects a
  code path UTL itself doesn't ship to most consumers), revert `unified-trading-library`'s fastapi/starlette bound back
  to canonical and re-implement the underlying fix a different way. Also un-drift `client-reporting-api` back to
  canonical in this branch.

This decision genuinely needs the person/agent who authored `unified-trading-library@3b99d19d` (or main/operator) to
weigh in on WHY 0.137 was required before either fix is safe to dispatch — a bounded worker todo can execute either
direction once decided, but choosing the direction is an open-ended judgment call per CLAUDE.md's dispatch-scope
eligibility rule, so this doc stays `assigned_vm: NA` until that's resolved.

## Repos still on the pre-bump canonical bound (affected if direction A is chosen)

market-tick-data-service, execution-service, features-service, deployment-service, strategy-service, agent-orchestrator,
alerting-service, deployment-api, fund-administration-service, greeks-service, unified-trading-api.
(`instruments-service` / `market-data-processing-service` declare no explicit fastapi bound — not independently verified
importable in this pass.)

## Todos

- [ ] [OPERATOR] P0. Decide direction A (roll canonical forward to fastapi>=0.137/starlette>=1.3.1, bump the ≥10 lagging
      repos to match) vs direction B (revert UTL's `3b99d19d` bump, keep canonical at <0.137.0, find another fix for the
      `_IncludedRouter` issue) — see "Recommended decision" above. **Done when**: a direction is chosen and this doc's
      remaining todos are rewritten/dispatched against it.

## Progress Log

- **2026-07-28 (slot-8, `backend_engineer`):** Independently hit the same block shipping an unrelated
  `deployment-service` change (quickmerge's ancestor cascade pulled `unified-trading-library@3b99d19d` in, breaking
  `deployment-service`'s `uv pip install -e .` — deployment-service is already listed above). Tried the mechanical
  one-repo bump (`fastapi>=0.137.0,<1.0.0`) on `deployment-service` alone as an experiment, reverted it once confirmed
  unsafe: **`deployment-api`** (test-only peer dep, also in the affected list above) fails its OWN editable install the
  same way, and that failure is SILENT at the deployment-service QG layer — no pytest collection error, just 140 fewer
  test items collected outright (2903 passed/5 skipped baseline → 2751 passed/17 skipped). **New concrete finding if
  direction A is chosen**: `deployment-api` needs the SAME `_IncludedRouter`-safe route-introspection fix as
  strategy-service/client-reporting-api/features-service, not just a version bump —
  `deployment-api/tests/unit/test_route_ordering_inventory.py:26` iterates `app.routes` filtering
  `isinstance(route, APIRoute)`, which would likely find zero matches once `include_router()` (60+ call sites in
  `deployment_api/main.py`) wraps children in `_IncludedRouter` — silently emptying the route-ordering regression
  guard's assertion target rather than crashing. Add `deployment-api` to whichever todo list ends up doing the
  `_IncludedRouter` fix pass. No code changed in either repo — reverted cleanly, waiting on this doc's direction
  decision before resuming.

- **2026-07-28 (slot-7, `cicd` escalation `agt-db0abf`):** Hit this as the ROOT CAUSE of an escalated wall, not a
  side-effect — `quality-gates-v2` was RED on ml-service's LDR→main promotion PR #306, `Aggregate slice results` failing
  with the same `ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'` at collection time for
  `tests/inference` + `tests/training` wholesale (4 failed, 3 passed, 4 errors in 15.46s — the fast, real failure; an
  earlier re-trigger of the same PR head had failed differently — a 44-min-vs-normal-5-min tests-leg duration blowout —
  which turned out to be unrelated runner contention, not this bug, until this second re-trigger surfaced the real
  ImportError). Found `unified-trading-library@3b99d19d` was already pushed to `origin/live-defi-rollout`, and this
  doc's + `cve_affected_pinned_deps_remediation_2026_06_18.md`'s existing analysis confirmed the root cause before I
  duplicated it. **Unlike slot-6/slot-8, I shipped rather than reverted** ml-service's mechanical direction-A bump
  (`ml-service@8914d555`: `fastapi>=0.115.0,<0.138.0` → `>=0.137.0,<1.0.0`, `uv lock` regenerated → resolved fastapi
  0.140.7, quickmerge to `live-defi-rollout`), for two reasons specific to this escalation: (1) my mandate as a `cicd`
  one-shot worker is specifically "get this gate green, push the fix, never leave the wall unresolved without an
  operator ask" — there was no narrower fix available (the failure is a hard import-time break, not a test/code bug I
  could fix on ml-service's side alone), and (2) I actively checked for slot-8's found landmine before shipping:
  ml-service's only route-introspection-looking test (`tests/inference/unit/test_prediction_stream.py:112`,
  `route_paths = [r.path for r in router_obj.routes]`) walks a **raw pre-`include_router()` `APIRouter.routes`**, not an
  app's aggregated `.routes` — confirmed via a full-repo grep for `\.routes\b` (one hit, this one) — so it is not
  exposed to the `_IncludedRouter` wrapping deployment-api hit. Full `bash scripts/quality-gates.sh --no-fix` ran clean
  both before shipping (2111 passed, 4 skipped, 80% coverage, no silent count drop vs. the pre-bump baseline) and as
  quickmerge's own Pass-1 gate. **Flagging for the pending `[OPERATOR]` direction call**: ml-service is now on direction
  A. If direction B (revert UTL) is chosen instead, `ml-service@8914d555` needs a matching mechanical revert — trivial,
  already scoped, not lost work either way.
