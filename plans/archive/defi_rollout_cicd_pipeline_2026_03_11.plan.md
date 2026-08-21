---
doc_type: plan
title: defi-rollout-cicd-pipeline
summary: Wire the live-defi-rollout feature branch into the full CI/CD pipeline — manifest-driven branch name, auto-merge
  to staging on QG pass, and semver bump on main post-SIT.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
type: code
epic: epic-deployment
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C5, deployment: none, business: none, readiness_note: 'All changes live in PM: manifest (active_feature_branch), quickmerge.sh (branch from manifest, dep-branch guard), CLAUDE.md, SUB_AGENT_MANDATORY_RULES.md, feature-branch-to-staging.yml template, semver-agent.yml updated to main trigger.

    '}
depends_on: []
todos:
- {id: manifest-active-branch, content: 'Add active_feature_branch: live-defi-rollout to workspace-manifest.json', status: done, note: DONE 2026-03-11 — field added before staging_status}
- {id: quickmerge-manifest-branch, content: Update quickmerge.sh to read active_feature_branch from manifest instead of auto-generating auto/ branch, status: done, note: DONE 2026-03-11 — fallback to auto/ if manifest has no entry; dep-branch still overrides for humans}
- {id: quickmerge-dep-branch-guard, content: Add --dep-branch + --agent guard to quickmerge.sh (exit 1 with clear message), status: done, note: DONE 2026-03-11 — agents attempting --dep-branch get explicit error; dep-conflict message split into HUMAN / AGENT paths}
- {id: feature-to-staging-template, content: Create feature-branch-to-staging.yml propagation + canonical template, status: done, note: DONE 2026-03-11 — QG pass on live-defi-rollout → PR to staging with auto-merge; staging-lock aware}
- {id: semver-agent-main-trigger, content: 'Update semver-agent.yml templates (propagation + canonical) to trigger on main QG pass, not staging', status: done, note: 'DONE 2026-03-11 — dispatches branch=main; bump computed after SIT promotion, not at staging time'}
- {id: agent-rules-dep-branch, content: Update SUB_AGENT_MANDATORY_RULES.md and CLAUDE.md to prohibit --dep-branch for agents, status: done, note: DONE 2026-03-11 — §2 and §7 updated; CLAUDE.md Key Rules updated; symlink means one edit covers both}
---

## Summary

Full pipeline for the DeFi rollout:

```
live-defi-rollout
  → [QG pass] feature-branch-to-staging.yml → PR to staging (auto-merge, staging-lock aware)
  → [QG pass on staging] SIT (system-integration-tests)
  → staging-to-main.yml → main
  → [QG pass on main] semver-agent.yml → version bump dispatched to PM
```

Branch name is the SSOT in `workspace-manifest.json#active_feature_branch`. To switch the active feature branch for the
next initiative, update one field in the manifest — all agents and quickmerge pick it up automatically.

`--dep-branch` is now enforced as human-only: passing it with `--agent` is a hard `exit 1`.
