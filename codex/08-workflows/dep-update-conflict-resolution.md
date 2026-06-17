---
scope: [engineer, admin]
title: Resolving a dep-update → staging conflict (worker playbook)
type: workflow
status: active
---

# Resolving a `dep-update/*` → staging conflict (worker playbook)

> **Audience:** an agent-orchestrator worker escalated a CONFLICTING `dep-update/<dep>-<version>` → `staging` PR (event
> `merge-conflict-detected` → `escalate-to-orchestrator`). This is the playbook the escalation context points you to. It
> exists because the generic conflict-resolution context ("resolve ON live-defi-rollout") is **wrong** for a dep-update
> conflict — these resolve on the dep-update topic branch, not LDR. SSOT for the surrounding model:
> `codex/08-workflows/ci-cd-flow.md` § "Convergence + conflict-resolution model"; incident:
> `plans/active/issues/promotion_queue_conflict_wall_pileup_2026_06_17.md`.

## What these PRs are + why they conflict

The dependency-update fan-out (`update-dependency-version.yml`) opens a `dep-update/<dep>-<version>` PR in a consumer
repo on a **breaking/major** internal bump — it bumps the consumer's `pyproject.toml` dependency **floor**
(`"<dep>>=X,<1.0.0"`) + refreshes the Dockerfile `ARG BASE_IMAGE_DIGEST`, base = `staging`, with v2-gated auto-merge
armed. The branch is cut from `staging` at open time; `staging` then keeps advancing (other promotes), so by the time it
tries to merge, the branch's `pyproject.toml`/`uv.lock` lines conflict with the newer `staging` →
`mergeable_state == dirty` (a "conflict wall"). `gh … /update-branch` returns **422** (real conflict), so a plain
rebase-button won't clear it. (Going forward this is rarer: a **non-breaking minor/patch** internal bump is now
digest-only — no floor churn — so `staging`'s floor stays stable.)

## Deterministic resolution (the common case — a floor / lock conflict)

The conflict is almost always just the dep floor line + the lock. Resolve it on the **dep-update branch**:

```bash
git clone <repo> && cd <repo>
git fetch origin staging "$SOURCE_BRANCH"            # SOURCE_BRANCH = dep-update/<dep>-<version>
git checkout "$SOURCE_BRANCH"
git rebase origin/staging                            # replay the dep bump onto current staging
# On a pyproject.toml conflict: KEEP THIS BRANCH'S floor for <dep> (the higher floor it is bumping to —
# that is the PR's entire purpose), TAKE STAGING for every other line. On a uv.lock conflict, do NOT
# hand-merge the lock — regenerate it:
uv lock                                              # re-sync uv.lock to the merged pyproject
git add pyproject.toml uv.lock Dockerfile 'Dockerfile.*' 2>/dev/null
git rebase --continue
# A dep-update branch is a throwaway TOPIC branch — force-with-lease is correct here (NEVER force-push
# staging/main/live-defi-rollout):
git push --force-with-lease origin "HEAD:$SOURCE_BRANCH"
```

The PR's armed `quality-gates-v2` re-runs on the new head and (if green) auto-merge drains it to `staging`.

**Sanity checks before pushing:** the only intended content change vs `staging` is the `<dep>` floor bump (+ the digest
ARG if present); grep that your bump survived AND that you didn't drop any `staging`-side line. If the dep version the
branch targets is already ≤ `staging`'s floor, the PR is **superseded** — close it (the `supersede-stale-dep-update-prs`
bot normally does this) rather than rebase.

## Can't resolve deterministically → escalate to the operator (do NOT force-merge)

If it is **not** a clean floor/lock conflict — a genuine source conflict, a test that now fails against the new dep
(e.g. the dep had a real breaking change the consumer must adapt to), or any judgment call — **stop**:

1. Do **not** force-merge or `--admin` merge. Leave the PR open.
2. Post a Slack `#ci-failures` alert:
   `dep-update conflict needs operator input — <repo>#<pr> (<dep> <ver>): <one-line why>`.
3. Surface the question in your **orchestrator slot** (the agent-orchestrator dashboard at
   `agent-orchestrator.odum-research.com`) so the operator can answer and unblock you — state exactly what decision you
   need (e.g. "UTL 0.12.0 changed `<symbol>`; should the consumer adopt the new behaviour or pin below it?"). The
   operator replies in the UI; resume on their answer.

This is the intended loop: the worker resolves the mechanical 90%, and the operator only sees the genuine judgment calls
(with a direct UI link to respond), instead of a silent multi-hour conflict-wall pile-up.

## Owner / escalation chain (who feeds you this)

`supersede-stale-dep-update-prs.yml` (PM, `*/2h`) is the OWNER of `dep-update/*` PR hygiene: it closes superseded
older-version PRs, and for a surviving CONFLICTING (`dirty`) one it dispatches `merge-conflict-detected` →
`conflict-resolution-agent.yml` → `escalate-to-orchestrator` (this worker), with this playbook as the context.
Detection/visibility is doubled by `promotion_lag_monitor.py` (pages on any promote/dep-update PR `dirty` beyond the
SLA). The strict-quickmerge / promotion HARD RULES are unchanged.
