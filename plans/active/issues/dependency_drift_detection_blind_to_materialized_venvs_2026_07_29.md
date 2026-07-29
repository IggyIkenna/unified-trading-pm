---
doc_type: issue
title:
  Dependency-drift detection (`check-dependency-alignment.py`) only validates declared `pyproject.toml` specs — it has
  no visibility into an already-materialized `.venv` silently running a stale pre-bump dependency
summary: >-
  Found while resolving the fleet fastapi/starlette floor-bump incident
  (`plans/archive/issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md`, archived 2026-07-29):
  `check-dependency-alignment.py` reported the fleet "aligned" throughout the incident because it only checks declared
  `pyproject.toml` version specs against the manifest/canonical constraints — it never inspects what is ACTUALLY
  installed in a long-lived materialized `.venv`. Three independent instances of the same failure class hit during that
  incident, each invisible to the checker until something broke at runtime: (1) ml-service's persistent
  self-hosted-runner venv kept masking the break until its runner was reverted; (2) a host-cron root-clone `.venv`
  (`deployment-service/.venv`, NOT a `.tabs/N` slot, used directly by a host cron) had never been resynced and was still
  on `fastapi==0.136.3` from before the bump; (3) the shared `.venv-workspace` independently drifted stale on
  `pydantic-core`, a different package, same root cause class. Plain `uv lock` doesn't refresh an already-materialized
  `.venv`, so a long-lived cached venv (self-hosted-runner cache, or a host-cron root-clone `.venv` used directly by a
  cron rather than a fresh CI resolve) is an additional, currently-undetected drift vector — independent of which repos'
  declarations are aligned.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [dependency-drift, venv, ci, tooling-gap, self-hosted-runner]
related:
  [
    /plans/archive/issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md,
    /plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
  ]
created: 2026-07-29
parent_epic: infrastructure_master
priority: P2
source:
  [
    "found while resolving plan_health gate escalation agt-b6a120 (2026-07-29), triaging archive-candidate
    fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md's Progress Log — a genuine finding already present
    in that doc's text at archival time but never turned into its own tracked todo",
  ]
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
execution_scope: local-only
drift_direction: worsening-slowly
depends_on: []
---

# Dependency-drift detection is blind to already-materialized venvs

## What I found

`scripts/manifest/check-dependency-alignment.py` (and the fleet-wide `check-dependency-alignment` CI step it backs)
verifies that each repo's `pyproject.toml` **declarations** are aligned with the canonical version floor/cap
constraints. It does not, and structurally cannot, tell you whether a specific **already-materialized** `.venv` actually
has that declared version installed. Two distinct places this gap matters, both hit during the 2026-07-28/29
fastapi/starlette floor-bump incident:

1. **Self-hosted-runner caches** (e.g. ml-service's persistent runner) reuse the same `.venv` across CI runs; a floor
   bump that lands in `pyproject.toml` does not force that cached venv to re-resolve, so CI can keep running old code
   against the stale dependency indefinitely while `check-dependency-alignment.py` reports green (it only reads the
   declaration file, not the runner's actual site-packages).
2. **Host-cron root-clone venvs** — a plain root-level repo clone (not a `.tabs/N` slot, not a fresh CI checkout) whose
   `.venv` is used directly by a host-level cron job. `deployment-service/.venv` and the shared `.venv-workspace` both
   hit this: `uv lock` regenerates the lockfile but does not resync an already-materialized venv, so the cron kept
   running against a pre-bump dependency version until someone happened to notice a runtime `ImportError`.

Both vectors are invisible to the same declaration-only check, and both are inherently silent until something breaks at
runtime (an `ImportError` on a symbol the new floor version removed/renamed, in the observed incident).

## Why it matters

Every future floor/cap bump (CVE remediation, a routine dependency update) can recur this exact failure class on any
self-hosted-runner cache or host-cron root-clone venv, on any repo, with zero automated warning — the fleet reads
"aligned" the whole time. The observed incident found 3 independent instances in one sweep; there is no reason to
believe that was exhaustive.

## Recommendation (not built here — real scope, not a drive-by)

Extend drift detection beyond `pyproject.toml` declarations to actually-materialized venvs: e.g. a periodic check (cron
or CI step) that runs `pip list --format=json` (or `uv pip list`) against each known long-lived venv (the
self-hosted-runner caches' persistent venvs, plus any host-cron root-clone `.venv`/`​.venv-workspace` enumerated by
path) and diffs the installed versions against the same canonical floor/cap constraints `check-dependency-alignment.py`
already uses — flagging a materialized-but-undeclared drift the same way a declaration mismatch is flagged today.

## Todos

- [ ] [INFRA] P2. Design + build a materialized-venv drift check (see Recommendation above) covering at minimum the 3
      concrete venvs this incident found stale: ml-service's self-hosted-runner venv, `deployment-service/.venv`
      (host-cron root clone), and the shared `.venv-workspace`. Repo: unified-trading-pm (tooling) + deployment-service
      (if a scheduled job is the chosen mechanism).
