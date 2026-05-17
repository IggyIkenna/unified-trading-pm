---
title: "trading-agent-service workspace-qg clone step silently fails to clone unified-trading-library"
created: 2026-05-16
author: ikenna-main (workspace-qg Phase B failure-mode sweep)
source:
  - github.com/IggyIkenna/trading-agent-service/actions/runs/25970374394 (post-fix retrigger)
  - github.com/IggyIkenna/trading-agent-service/actions/runs/25969164753 (pre-fix initial)
locked_by: live-defi-rollout
locked_since: 2026-05-16
severity: P2 — single-repo failure; workspace-qg Phase B succeeded for the other 20
---

## What I found

trading-agent-service's workspace-qg fails at "Install dependencies" with:

```
error: Distribution not found at: file:///home/runner/work/trading-agent-service/unified-trading-library
```

(GH Actions log shows `trading***agent***service` due to overly-aggressive secret masking — likely the GH_PAT
contains substring patterns that match the repo name. Real path is `trading-agent-service`.)

Both pre-fix run (18:21) and post-PM-fix re-trigger (19:06) fail the same way. The trigger-retry at 19:06 was an
empty commit after `unified-trading-pm@c6419752` shipped the transitive-deps BFS fix.

trading-agent-service's `workspace-qg.yml` correctly declares `dep_repos: "unified-trading-library unified-api-contracts"`
(direct deps == transitive — leaf nodes). So the fix didn't change its template; the failure is in the clone step
itself.

The clone-step log truncates at `##[endgroup]` after the heredoc — NO actual clone command output visible. Either:
1. The heredoc script has a syntax error specific to this repo's invocation context (unlikely — same template
   across 20 other repos that work)
2. The clone command silently fails (`|| true` at end of `clone_repo`) and uv sync then can't find the deps
3. The clone produces a directory but in the wrong location (e.g. `cwd` differs in this repo's checkout)

## Why it matters

trading-agent-service workspace-qg green is a per-repo continuous-verification target. Without it, the repo
has no automated QG gate. Pre-existing QG state was `[main]`-only (manual PR check); the regression is from
unification surfacing this issue.

## Recommended decision

Slot owner (whoever owns trading-agent-service per work-split) should:

1. Reproduce locally: `cd .tabs/N/trading-agent-service && bash scripts/quality-gates.sh`
2. If repo's QG passes locally, the issue is GHA-specific. Inspect the `clone_repo` invocation context.
3. Confirm whether the `path = "../unified-trading-library"` in pyproject's `[tool.uv.sources]` resolves to
   the expected location given GHA checkout's working-directory layout.

**Workaround**: if reproducing locally green, the slot owner can `gh workflow run workspace-qg -R IggyIkenna/trading-agent-service`
to re-trigger; if it still fails, file a deeper issue.

Cross-link: `plans/active/issues/workspace_qg_yml_redesign_2026_05_15.md` § "PHASE B FULLY ROLLED OUT" + "POST-PHASE-B FIX".

## UPDATE 2026-05-17 01:35 UTC (slot-1-main) — root cause + fix

**Root cause** (via gh run view 25970374394 --log-failed): the `clone_repo` function in
`unified-trading-pm/.github/workflows/python-quality-gates.yml` had `|| true` + `2>/dev/null` swallowing all clone
errors. When the clone silently failed, `uv sync` downstream reported the confusing
`Distribution not found at file:///.../unified-trading-library` with no upstream signal.

**Fix shipped at `unified-trading-pm@c953d778`**: removed silencing — `git clone` now exits non-zero on failure so
the real error (auth, missing branch, etc.) surfaces in the GHA log. Re-triggered the workflow at
`trading-agent-service@2cf553d` (empty commit). Next run will either:

1. Pass (if the clone actually works and the prior issue was transient) — close this issue.
2. Fail with VISIBLE clone error message — diagnose the real cause from the new log.

The fix is generalised to ALL 21 Python repos via the reusable workflow (`uses: ... @live-defi-rollout`), so the
visibility benefit applies across the board.
