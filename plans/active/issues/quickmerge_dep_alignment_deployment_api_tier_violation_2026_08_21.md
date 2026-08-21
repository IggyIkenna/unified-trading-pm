---
doc_type: issue
title: quickmerge STAGE 1.5 dependency-alignment fleet-wide blocker — deployment-api/deployment-service tier violation
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, deployment-api, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, dependency-alignment, tier-violation, blocked]
created: 2026-08-21
author: cicd worker (escalation agt-614918, slot 1)
related: [/codex/08-workflows/ci-cd-flow.md, /codex/04-architecture/tier-and-import-architecture.md]
summary: "`scripts/quickmerge.sh`'s STAGE 1.5 (\"Dependency Alignment (PM)\") requires `check-dependency-alignment.py --json` to report `\"aligned\": true` across the **entire** fleet (every sibling repo ..."
execution_scope: orchestrator-agent
priority: P2
parent_epic: ci_master
assigned_vm: NA
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    scripts/quickmerge.sh,
    scripts/manifest/check-dependency-alignment.py,
    scripts/manifest/fix-internal-dependency-alignment.py,
    deployment-api/deployment_api/clients/deployment_service_client.py,
  ]
source: >-
  Discovered while resolving escalation agt-614918 (wall_type=ldr_qg_failure, repo=unified-trading-pm):
  quality-gates-v2 was RED on live-defi-rollout for unrelated reasons (deep UAC imports + a pip-audit finding). Both
  were fixed and verified green locally, but shipping the fix via quickmerge hit this separate, pre-existing STAGE 1.5
  blocker. A bounded 2-minute /blocked question to main (BLK-710d4d8d) went unanswered, so this was filed instead of
  force-bypassed.
---

# quickmerge STAGE 1.5 dependency-alignment fleet-wide blocker

## Summary

`scripts/quickmerge.sh`'s STAGE 1.5 ("Dependency Alignment (PM)") requires
`check-dependency-alignment.py --json` to report `"aligned": true` across the
**entire** fleet (every sibling repo checked out under the workspace), not just
the repo/files being shipped, before it will push **any** change to
`unified-trading-pm` via quickmerge. As of 2026-08-21 this reports `aligned:
false` due to a pre-existing, unrelated issue:

```json
{"repo": "deployment-api", "type": "internal_in_manifest_not_pyproject", "dep": "deployment-service"}
```

`workspace-manifest.json` records `deployment-api` as depending on
`deployment-service`, and `deployment-api`'s source genuinely imports it live
(`deployment_api/clients/deployment_service_client.py`, `settings.py`,
`config_loader.py`, `workers/_deployment_processor_cloud_run.py`,
`workers/deployment_worker.py`, `routes/strategy_shard.py`,
`routes/ml_experiment_launch.py`, `routes/chaos_injections.py`, and more) — this
is not stale manifest metadata, it is a real, live dependency.
`scripts/manifest/fix-internal-dependency-alignment.py` refuses to auto-fix it:

```
TIER_VIOLATION (architectural change required):
  [deployment-api] imports [deployment-service] — add_to_pyproject would violate tier DAG
  Fix: move shared code to a lower tier, or restructure dependency.
```

This is a genuine violation of the "NO service↔service deps" rule
(`/codex/04-architecture/tier-and-import-architecture.md`) that predates this
session and is unrelated to the change that surfaced it.

## Impact

**Any** quickmerge push to `unified-trading-pm` from a full-workspace checkout
currently fails at STAGE 1.5, regardless of what is being shipped. This is not
visible in recent PM activity because most recent `unified-trading-pm` traffic
has been `docs(plans):` plan-flip commits, which land via the exempted direct-push
carve-out (CLAUDE.md § "Git discipline + shipping pipeline") and never invoke
quickmerge/STAGE 1.5 at all. A real quickmerge-based PM ship (code, pyproject.toml,
uv.lock, etc.) hits this immediately.

## How this was found

Escalation `agt-614918` (`wall_type=ldr_qg_failure`, `repo=unified-trading-pm`):
`quality-gates-v2` was RED on `live-defi-rollout` due to (1) deep
`unified_api_contracts.canonical.*`/`registry.*` imports in
`scripts/docs/gen_api_reference_data_history.py` and (2) a `pip-audit` finding
(`PYSEC-2026-3721`, fixed upstream in pip 26.2). Both are fixed and verified
green locally (`bash scripts/quality-gates.sh`: PM lint-codex slice PASSED 34s;
`unified-api-contracts` full run PASSED 270s after adding the missing
`venue_instrument_type_triples` facade export the PM fix depended on). The fix
is committed on `unified-trading-pm`'s local `live-defi-rollout`
(`385db085b7`, `1a8e99419e`, both `ahead of origin`) but could not be pushed via
quickmerge because of this unrelated STAGE 1.5 blocker. A bounded (2-minute)
`/blocked` question to the main agent (`BLK-710d4d8d`) went unanswered, so per
the cicd one-shot contract I stopped rather than force-bypass the gate.

`unified-api-contracts`'s companion fix (the missing
`venue_instrument_type_triples` facade export) **did** ship successfully —
`unified-api-contracts@b12c133894`, landed and ancestry-verified on
`live-defi-rollout`.

## Recommended resolution paths (pick one — architectural call, not mine to make)

1. **Real fix**: restructure `deployment-api`/`deployment-service` so the
   dependency respects the tier DAG (move the shared client code to a lower
   tier, per the fixer script's own suggestion).
2. **Scoped exception**: if this dependency is an accepted, intentional
   exception to the tier rule, add it to whatever per-repo exception list
   `check-dependency-alignment.py` supports (see
   `PER_REPO_EXTERNAL_EXCEPTIONS`-equivalent for internal deps, if one exists)
   so the gate stops flagging it fleet-wide.
3. **Gate scoping**: STAGE 1.5 could scope its "aligned" requirement to the
   files/repos actually being shipped rather than the whole fleet, so an
   unrelated pre-existing violation elsewhere doesn't block every PM push.

## Follow-up todos

- [ ] [OPERATOR] P0. Decide the resolution path for the deployment-api ↔
      deployment-service tier violation (options 1–3 above) —
      `plans/active/issues/quickmerge_dep_alignment_deployment_api_tier_violation_2026_08_21.md`
- [ ] [SCRIPT] P0. Once resolved, ship the already-committed
      `unified-trading-pm` fix for `agt-614918`
      (`live-defi-rollout` local commits `385db085b7`, `1a8e99419e` — facade
      imports + pip PYSEC-2026-3721) via
      `bash scripts/quickmerge.sh --agent --files 'pyproject.toml uv.lock scripts/docs/gen_api_reference_data_history.py'`
      and verify `quality-gates-v2` goes green on `live-defi-rollout` for
      `unified-trading-pm`

## Progress Log

- 2026-08-21 (cicd, escalation agt-614918, slot 1): filed after a bounded
  2-minute `/blocked` wait (BLK-710d4d8d) went unanswered. PM's own fix is
  ready to ship the moment this blocker clears.
