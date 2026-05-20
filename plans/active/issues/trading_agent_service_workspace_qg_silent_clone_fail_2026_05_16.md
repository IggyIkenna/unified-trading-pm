---
title: "trading-agent-service workspace-qg clone step silently fails to clone unified-trading-library"
created: 2026-05-16
author: ikenna-main (workspace-qg Phase B failure-mode sweep)
source:
  - github.com/IggyIkenna/trading-agent-service/actions/runs/25970374394 (post-fix retrigger)
  - github.com/IggyIkenna/trading-agent-service/actions/runs/25969164753 (pre-fix initial)
locked_by: live-defi-rollout
locked_since: 2026-05-16
severity:
  P0 — trading-agent-service on May-23 architecture-unlock path per operator directive 2026-05-20; CI green required for
  layer-7 service
---

## What I found

trading-agent-service's workspace-qg fails at "Install dependencies" with:

```
error: Distribution not found at: file:///home/runner/work/trading-agent-service/unified-trading-library
```

(GH Actions log shows `trading***agent***service` due to overly-aggressive secret masking — likely the GH_PAT contains
substring patterns that match the repo name. Real path is `trading-agent-service`.)

Both pre-fix run (18:21) and post-PM-fix re-trigger (19:06) fail the same way. The trigger-retry at 19:06 was an empty
commit after `unified-trading-pm@c6419752` shipped the transitive-deps BFS fix.

trading-agent-service's `workspace-qg.yml` correctly declares
`dep_repos: "unified-trading-library unified-api-contracts"` (direct deps == transitive — leaf nodes). So the fix didn't
change its template; the failure is in the clone step itself.

The clone-step log truncates at `##[endgroup]` after the heredoc — NO actual clone command output visible. Either:

1. The heredoc script has a syntax error specific to this repo's invocation context (unlikely — same template across 20
   other repos that work)
2. The clone command silently fails (`|| true` at end of `clone_repo`) and uv sync then can't find the deps
3. The clone produces a directory but in the wrong location (e.g. `cwd` differs in this repo's checkout)

## Why it matters

trading-agent-service workspace-qg green is a per-repo continuous-verification target. Without it, the repo has no
automated QG gate. Pre-existing QG state was `[main]`-only (manual PR check); the regression is from unification
surfacing this issue.

## Recommended decision

Slot owner (whoever owns trading-agent-service per work-split) should:

1. Reproduce locally: `cd .tabs/N/trading-agent-service && bash scripts/quality-gates.sh`
2. If repo's QG passes locally, the issue is GHA-specific. Inspect the `clone_repo` invocation context.
3. Confirm whether the `path = "../unified-trading-library"` in pyproject's `[tool.uv.sources]` resolves to the expected
   location given GHA checkout's working-directory layout.

**Workaround**: if reproducing locally green, the slot owner can
`gh workflow run workspace-qg -R IggyIkenna/trading-agent-service` to re-trigger; if it still fails, file a deeper
issue.

Cross-link: `plans/active/issues/workspace_qg_yml_redesign_2026_05_15.md` § "PHASE B FULLY ROLLED OUT" + "POST-PHASE-B
FIX".

## UPDATE 2026-05-17 01:35 UTC (slot-1-main) — root cause + fix

**Root cause** (via gh run view 25970374394 --log-failed): the `clone_repo` function in
`unified-trading-pm/.github/workflows/python-quality-gates.yml` had `|| true` + `2>/dev/null` swallowing all clone
errors. When the clone silently failed, `uv sync` downstream reported the confusing
`Distribution not found at file:///.../unified-trading-library` with no upstream signal.

**Fix shipped at `unified-trading-pm@c953d778`**: removed silencing — `git clone` now exits non-zero on failure so the
real error (auth, missing branch, etc.) surfaces in the GHA log. Re-triggered the workflow at
`trading-agent-service@2cf553d` (empty commit). Next run will either:

1. Pass (if the clone actually works and the prior issue was transient) — close this issue.
2. Fail with VISIBLE clone error message — diagnose the real cause from the new log.

The fix is generalised to ALL 21 Python repos via the reusable workflow (`uses: ... @live-defi-rollout`), so the
visibility benefit applies across the board.

## CONFIRMED ROOT CAUSE — GH_PAT secret on trading-agent-service is INVALID/expired

After the visibility fix at PM@c953d778, the next workflow run on trading-agent-service@2cf553d
(`gh run view 25976833431 --log-failed`) surfaced the real error:

```
Cloning unified-trading-pm at branch live-defi-rollout (fallback)
fatal: Authentication failed for 'https://github.com/IggyIkenna/unified-trading-pm.git/'
WARN: Branch 'live-defi-rollout' clone failed for unified-trading-pm — falling back to main
fatal: Authentication failed for 'https://github.com/IggyIkenna/unified-trading-pm.git/'
##[error]Process completed with exit code 128.
```

The clone of the PM repo fails on BOTH branch + main fallback with 401 Auth Failed. The `GH_PAT` secret IS set on the
repo (`gh secret list` shows it at `2026-03-07T06:43:48Z`) but the value is rejected.

20 other Python repos that use the same workflow template successfully clone PM from `live-defi-rollout` — their
`GH_PAT` secrets are functionally identical (one example: mtds's GH_PAT at `2026-03-06T09:54:49Z` works). The difference
is the actual token value behind the secret on trading-agent — it may be:

- A different token that's lost its scope for unified-trading-pm (fine-grained PAT scope drift)
- An expired classic PAT (90-day default)
- A token typo (extra whitespace, partial copy at the time it was set)

**OPERATOR ACTION REQUIRED** (slot-1-main cannot read existing secret values via gh):

```bash
# Use the same GH_PAT value as a working repo (e.g. mtds). Cannot extract via gh CLI — read from
# wherever the operator keeps the canonical token (1Password / keychain / .env-deploy-secret) and:
gh secret set GH_PAT --repo IggyIkenna/trading-agent-service --body "$VALID_FINE_GRAINED_PAT"
# Then re-trigger:
gh workflow run workspace-qg.yml --repo IggyIkenna/trading-agent-service --ref live-defi-rollout
```

Filed in: `plans/active/master_to_live_defi_2026_05_23.md` § "Credential asks awaiting operator" (deferred to operator
return; non-blocking for May-23 — trading-agent-service is post-cutover work per work-split). Marked
`BLOCKED-CREDENTIALS`.

**Status of original issue closes**: silent-clone-fail symptom is now LOUD (visibility fix shipped); the underlying
credential issue is a routine operator-rotation task that doesn't block May-23 cutover.

---

## Triage — 2026-05-18

**Status**: OPEN **Triaged by**: slot-8 triage sweep **Reason**: BLOCKED-CREDENTIALS; visibility fix shipped but
credentials gap remains

---

## Triage update — 2026-05-20 (operator directive: architecture unlocked)

**Status**: OPEN-P0 (was BLOCKED-CREDENTIALS-deferred-post-cutover) **Reason**: trading-agent-service now on May-23
architecture-unlock path. CI hygiene fix needed for layer-7 continuous verification. **Slot owner**: assigned to
architecture-unlock plan Phase 7 (CI hygiene). **Operator ask** (CREDENTIAL APPROVAL REQUEST per CLAUDE.md "External
Data Is Always Available" rule):

- Rotate `GH_PAT` secret on `IggyIkenna/trading-agent-service` to match the working value on `IggyIkenna/mtds`
- `gh secret set GH_PAT --repo IggyIkenna/trading-agent-service --body "$VALID_FINE_GRAINED_PAT"`
- Without it: trading-agent-service workspace-qg stays red; architecture unlock is "shipped but unverified by CI"
  **Workaround until unblock**: per-repo `bash scripts/quality-gates.sh` local invocation by the implementing slot.
