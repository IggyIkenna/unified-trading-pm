---
doc_type: issue
title:
  STAGE 1.5 dependency-alignment RED for 9 repos (fastapi/pillow/click) — blocks every PM push, recurrence beyond the
  ml-service exception
summary: |
  check-dependency-alignment.py currently reports 9 external-version mismatches (fastapi ceiling on
  unified-trading-library, alerting-service, greeks-service, market-tick-data-service, deployment-api,
  agent-orchestrator; pillow floor on execution-service, strategy-service; click floor on features-service) — a wider
  recurrence of the same class of drift that canonical_fastapi_ceiling_stale_vs_ml_service_2026_07_13.md fixed
  narrowly (ml-service only, via a PER_REPO_EXTERNAL_EXCEPTIONS entry). This hard-blocks the STAGE 1.5 gate for EVERY
  unified-trading-pm push right now. No repo-blocker was open for it (`GET /api/repo-blockers` returned empty) despite
  it blocking every push fleet-wide — the prior attempt to file this (slot 6, commit 510be6e9a, "docs(plans): file
  issue for stale PM fastapi ceiling blocking all quickmerges") was itself silently discarded by the
  slot11_silent_branch_reset_data_loss bug before it ever landed (confirmed via slot 6's own clone reflog — see
  slot11_silent_branch_reset_data_loss_2026_07_13.md UPDATE 3's per-slot table).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    ml-service,
    unified-trading-library,
    alerting-service,
    greeks-service,
    market-tick-data-service,
    deployment-api,
    agent-orchestrator,
    execution-service,
    strategy-service,
    features-service,
  ]
scope: [engineer, admin]
tags: [dependency-alignment, fastapi, pillow, click, ssot-contradiction, canonical-manifest, quickmerge-blocked]
related:
  [
    plans/active/issues/canonical_fastapi_ceiling_stale_vs_ml_service_2026_07_13.md,
    plans/active/issues/slot11_silent_branch_reset_data_loss_2026_07_13.md,
    workspace-constraints.toml,
    canonical-dependency-manifest.json,
    scripts/manifest/check-dependency-alignment.py,
  ]
created: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
source: [slot 15, discovered while shipping slot11_silent_branch_reset_data_loss_2026_07_13.md VERIFY todo]
resolved_by:
locked_by:
drift_direction: unclear
depends_on: []
---

# STAGE 1.5 dependency-alignment RED for 9 repos — blocks every PM push

## What I found

Ran `.venv/bin/python scripts/manifest/check-dependency-alignment.py --json` from a clean `unified-trading-pm` tree
(HEAD `b4d92443b`, my 2 changed files were `plans/active/issues/*.md` + `scripts/dev/audit-fleet-reflog-resets.sh` —
neither touches any manifest/pyproject file, so this is pre-existing, not caused by my commits). Result:
`"aligned": false"`, 9 issues, all `external_version_mismatch`:

| Repo                     | Dep     | Repo's pyproject spec | Canonical spec       |
| ------------------------ | ------- | --------------------- | -------------------- |
| unified-trading-library  | fastapi | `>=0.115.0,<0.138.0`  | `>=0.115.0,<0.137.0` |
| alerting-service         | fastapi | `>=0.115.0,<0.138.0`  | `>=0.115.0,<0.137.0` |
| execution-service        | pillow  | `>=12.2.0,<13.0.0`    | `>=12.3.0,<13.0.0`   |
| features-service         | click   | `>=8.3.1,<9.0.0`      | `>=8.3.2,<9.0.0`     |
| greeks-service           | fastapi | `>=0.115.0,<0.138.0`  | `>=0.115.0,<0.137.0` |
| market-tick-data-service | fastapi | `>=0.115.0,<0.138.0`  | `>=0.115.0,<0.137.0` |
| strategy-service         | pillow  | `>=12.2.0,<13.0.0`    | `>=12.3.0,<13.0.0`   |
| deployment-api           | fastapi | `>=0.115.0,<0.138.0`  | `>=0.115.0,<0.137.0` |
| agent-orchestrator       | fastapi | `>=0.115.0,<0.138.0`  | `>=0.115.0,<0.137.0` |

This is `STAGE 1.5: Dependency Alignment (PM)` inside `scripts/quickmerge.sh` — a hard gate, not a warning. It fails for
ANY PM push right now, regardless of what the push actually touches, since it scans every sibling repo clone in the slot
vs the canonical manifest.

Two distinct sub-patterns:

1. **fastapi `<0.138.0` on 6 repos** — same shape as the already-resolved `ml-service` case (which pip-audit-fixed 2
   CVEs by widening its own ceiling to `<0.138.0` + forcing `starlette>=1.3.1` via `override-dependencies`). The
   resolved issue explicitly found fastapi `0.137.x` itself (not starlette) breaks `app.include_router` routing, and
   only fixed the ONE repo (`ml-service`) via a hardcoded `PER_REPO_EXTERNAL_EXCEPTIONS` entry — explicitly NOT
   generalized fleet-wide. These 6 repos independently raised the SAME ceiling (likely their own pip-audit CVE fixes,
   unverified here) and are not yet covered by that exception dict, so they now red-gate PM the same way ml-service did
   before its fix landed.
2. **pillow `>=12.2.0` (2 repos) / click `>=8.3.1` (1 repo) BELOW a canonical FLOOR that was already bumped UP**
   (`0e5ecd929 chore(deps): bump fleet-canonical click>=8.3.2 and add pillow>=12.3.0 floor`) — these 3 repos simply
   haven't picked up the canonical bump yet. This is the more common/expected direction of drift (repo lagging
   canonical) and likely just needs `fix_external_dependency_alignment.py --apply` for these 3 specifically — but I did
   not run it (see "Why I didn't just fix it").

## Why it matters

- **Blocks every `unified-trading-pm` push, full stop** — todo-flip commits, issue docs, plan edits, all of it, until
  this clears. My own VERIFY-todo shipment for `slot11_silent_branch_reset_data_loss_2026_07_13.md` is currently stuck
  behind this exact gate.
- **No operator visibility**: `GET /api/repo-blockers` returned `{"open": []}` — nothing is currently tracking this as a
  live blocker, despite it blocking the entire fleet's PM-push path right now.
- **A previous attempt to report this was itself lost to the reflog-reset bug**: slot 6 committed
  `unified-trading-pm@510be6e9a` ("docs(plans): file issue for stale PM fastapi ceiling blocking all quickmerges",
  declaring repo-blocker `RB-ba8daa5a`) at 2026-07-13 12:51:03 UTC. That commit never reached origin — it shows as
  `DISCARDED(reflog-only)` in slot 6's own clone reflog (see `slot11_silent_branch_reset_data_loss_2026_07_13.md` UPDATE
  3's per-slot table). So this exact blocking condition has gone unreported for ~2 hours not because nobody noticed, but
  because the noticing agent's report was silently destroyed — a live, concrete example of why the reflog-reset bug is
  dangerous beyond code-loss: it can also swallow the incident reports about itself.

## Why I didn't just fix it

Per `scripts/manifest/README-DEPENDENCY-ALIGNMENT.md` and the resolved ml-service issue's own stated reasoning: fastapi
`0.137.x` is a **confirmed-broken** version (routing `_IncludedRouter.path` regression, verified in that issue's
Progress Log) — blindly running `fix_external_dependency_alignment.py --apply` would silently downgrade these 6 repos'
ceilings back to `<0.137.0`, which may re-open CVEs they deliberately fixed (unverified — needs a per-repo check of WHY
each raised its ceiling, same as the ml-service investigation did). Conversely, raising the canonical ceiling to match
them would let any repo's resolver land on the confirmed-broken `0.137.x`. This is the same judgment-call category the
ml-service issue exists to route, not something to script through under time pressure — so filing it, not auto-fixing
it. The pillow/click floor-lag (pattern 2) looks safely `--apply`-able (canonical went UP, repos just haven't caught up)
but I left it alone too, to keep this fix atomic and reviewable rather than mixing a safe auto-fix with 6 judgment calls
in one commit under a gate I can't currently ship through anyway.

## Recommended decision

1. For the 6 fastapi-`<0.138.0` repos: for each, verify (same method as the ml-service investigation) whether its ACTUAL
   locked resolution lands below `0.137.0` (safe, like ml-service) or on `0.137.x`/`0.138.x` (reproduces the routing
   break). Add a `PER_REPO_EXTERNAL_EXCEPTIONS` entry per repo that's confirmed safe; for any that reproduce the break,
   downgrade that repo's ceiling back to `<0.137.0` instead (re-closes its CVE fix — coordinate with whichever
   plan/issue originally justified that repo's bump, if any exists).
2. For the 3 pillow/click floor-lag repos: `python3 scripts/manifest/fix_external_dependency_alignment.py --apply`
   scoped to just those 3, then verify `check-dependency-alignment.py` clears them.
3. Consider whether `PER_REPO_EXTERNAL_EXCEPTIONS` should become a documented, lighter-weight process (a YAML list + a
   short justification field) rather than hand-edited Python dict entries, given this is now the 2nd occurrence in the
   same day — the current fix-one-repo-at-a-time pattern doesn't scale if repos keep independently patching CVEs ahead
   of canonical.
4. Route the reflog-reset bug's incident-report-eating behavior (this issue's own near-loss) back into
   `slot11_silent_branch_reset_data_loss_2026_07_13.md` INFRA todos as corroborating urgency — already added as that
   doc's UPDATE 4.

## Todos

- [ ] [BACKEND] P0. Investigate each of the 6 fastapi-`<0.138.0` repos (unified-trading-library, alerting-service,
      greeks-service, market-tick-data-service, deployment-api, agent-orchestrator): confirm locked resolution is safely
      below `0.137.0` (add a `PER_REPO_EXTERNAL_EXCEPTIONS` entry, ml-service pattern) or reproduces the routing break
      (downgrade that repo's own ceiling to `<0.137.0`). Unblocks STAGE 1.5 for real. (repo: unified-trading-pm + the 6
      named repos)
- [ ] [BACKEND] P1. `fix_external_dependency_alignment.py --apply` scoped to execution-service, strategy-service
      (pillow) and features-service (click) to pick up the already-bumped canonical floor. (repo: unified-trading-pm)
- [ ] [INFRA] P2. Evaluate a lighter-weight per-repo-exception process (YAML + justification) so this doesn't require a
      hand-edited Python dict entry every time a repo patches a CVE ahead of canonical. (repo: unified-trading-pm)
