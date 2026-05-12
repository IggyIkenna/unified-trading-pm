---
title: "Slot-worktree `bash scripts/quality-gates.sh` resolves the wrong repo root (runs PM's tests when PM is a sibling worktree)"
created: 2026-05-11
author: harsh-workspace-qg-tab (slot 6, flagged to slot 1)
source:
  - harsh_orchestrator/pings/slot_6.md (2026-05-11 07:28 UTC)
  - scripts/setup-tab-worktrees.sh (per-tab worktree provisioning)
  - the PM-template base-service.sh repo-root resolution logic (in each repo's scripts/quality-gates.sh)
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Slot-worktree `quality-gates.sh` resolves the wrong repo root

> ✅ **RESOLVED 2026-05-12** via Option (i) at PM@`3b6e0ae3`. `qg-common.sh` now resolves `PROJECT_ROOT` by walking
> UP from the caller stub's directory until the nearest `pyproject.toml` (instead of `dirname dirname` of `scripts/`).
> Adds a diagnostic banner `[quality-gates] <repo> @ <PROJECT_ROOT>` (yellow warning if `SERVICE_NAME != basename(PROJECT_ROOT)`)
> so operator can spot wrong-resolution at a glance. Suppress via `QG_BANNER_SUPPRESS=true`. Smoke-tested from
> `.tabs/6/market-tick-data-service` — `PROJECT_ROOT` resolves to the MTDS worktree (not slot's PM sibling).

> **Severity**: P1 — affects every slot's pre-push QG under the per-tab worktree model. Not a data-correctness bug;
> it's a "QG ran against the wrong repo" bug — slots may push code that `bash scripts/quality-gates.sh` *looked* green
> on but never actually checked. **Blast radius**: every `.tabs/<N>/<repo>/scripts/quality-gates.sh` run on this
> machine. **Suggested owner**: Ikenna (owns `setup-tab-worktrees.sh` + the `base-service.sh` PM-template repo-root
> resolution).

## What slot 6 found (2026-05-11)

Running `cd ${WORKSPACE_ROOT}/.tabs/6/market-tick-data-service && bash scripts/quality-gates.sh` ran **PM's**
`tests/` + import-pattern checks instead of MTDS's. The `base-service.sh` repo-root resolution (the bit that figures
out "which repo am I in" — usually `git rev-parse --show-toplevel` or walking up to the nearest `pyproject.toml`) gets
confused when the per-tab worktree layout has `unified-trading-pm` as a *sibling worktree* under `.tabs/<N>/`: it may
resolve to PM (which has a `scripts/quality-gates.sh` of a different shape) rather than the repo the script was invoked
from. Likely affects all slots, all repos — slot 6 only spotted it on MTDS.

## Why it matters

Under the merge model, each slot runs `bash scripts/quality-gates.sh` on its own repo before pushing (Pass 1 QG). If
that command silently runs PM's QG instead of the repo's, the slot's "QG green" signal is meaningless for the repo it's
actually editing → it can push code that was never type-checked / lint-checked / tested. Pre-worktree this didn't happen
(repos were standalone clones, not sibling worktrees of one another).

## Workaround until fixed

- Slots: run QG with an explicit repo path / from the repo dir AND verify the QG banner names the right repo
  (`[quality-gates] <repo-name>`); if it says `unified-trading-pm` you're in the wrong-resolution case — `cd` deeper or
  set whatever env var `base-service.sh` honours for the repo root.
- OR: until fixed, rely on the remote-CI gate (which runs in-image and resolves correctly) — but `live-defi-rollout`
  pushes don't trigger remote CI, so that's not a real safety net for feature-branch work. So: be careful + check the
  banner.

## Recommended fix (Ikenna territory)

`base-service.sh` repo-root resolution should prefer the *invocation directory's* nearest `pyproject.toml` / `.git`
(walking UP from `$PWD`, stopping at the first repo boundary) over any `git rev-parse --show-toplevel` that might jump
to a sibling worktree's root. OR: `setup-tab-worktrees.sh` could write a `.repo-root` marker / set an env var in each
slot-repo's `.envrc`. Either way it's a `setup-tab-worktrees.sh` + `base-service.sh`-template change → cross-side ping
to Ikenna posted 2026-05-11.

## Triage target

Fold into the per-tab-worktree plan (`plans/active/per_agent_worktrees_2026_05_10.md`) as a follow-up, or fix
standalone in `base-service.sh` + propagate. Ikenna-side decision.
