---
doc_type: plan
title: check-staging-lock rulesets in 3 repos still use v1-style required check
summary:
status: RESOLVED 2026-05-29
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui, execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: [plans/active/ci_canonical_v2_migration_2026_05_29.md]
created: 2026-05-29
parent_epic: infrastructure_master
locked_by: live-defi-rollout
priority: P2
---

> **RESOLVED 2026-05-29**: Option A (additive update) applied. All 3 rulesets now require BOTH `check-staging-lock` AND
> `quality-gates-v2`:
>
> - execution-service ruleset 13647462: `['check-staging-lock', 'quality-gates-v2']` ✓
> - instruments-service ruleset 13787597: `['check-staging-lock', 'quality-gates-v2']` ✓
> - deployment-ui ruleset 13787657: `['check-staging-lock', 'quality-gates-v2']` ✓
>
> Verified via `gh api repos/IggyIkenna/<repo>/rulesets/<id>` post-PUT. Workspace-canonical two-pass + staging-lock
> model now enforced on these repos. Issue archives.

## What I found

During Phase 4 of `ci_canonical_v2_migration_2026_05_29` (workspace-wide v2 rollout), three repos were identified with
`require-quality-gates` rulesets enforcing `check-staging-lock` (NOT `quality-gates`) as the required status check:

| Repo                | Ruleset ID | Required Context     | State  |
| ------------------- | ---------- | -------------------- | ------ |
| execution-service   | 13647462   | `check-staging-lock` | active |
| instruments-service | 13787597   | `check-staging-lock` | active |
| deployment-ui       | 13787657   | `check-staging-lock` | active |

These repos' v2 caller files were successfully bootstrapped to main (PRs #202, #388, #9 respectively merged 2026-05-29
18:42-18:44Z), but the ruleset wasn't rotated to require `quality-gates-v2` because the original context wasn't
`quality-gates` (so no ghost-cache issue blocked their PRs).

## Why it matters (and doesn't)

**Doesn't matter**: PRs to these repos are NOT blocked by the ghost cache because the required context
(`check-staging-lock`) is a different workflow that doesn't use the ghost-bound `python-quality-gates.yml` callee. The
Phase 4 admin-merge cycle worked fine for them.

**Does matter (hygiene)**: These repos have v2 quality-gates workflows on main now but the required-check ruleset isn't
enforcing v2. So future PRs to these 3 repos will:

1. Run quality-gates-v2 (it's on main now)
2. Run check-staging-lock (the currently-required check)
3. ONLY check-staging-lock counts as required for merge

That's not a correctness issue but it means quality-gates-v2 is advisory not gating for these repos. Workspace canonical
(per `/codex/08-workflows/ci-cd-flow.md`) is that `quality-gates-v2` SHOULD be the gating check.

## Recommended decision

**Option A** (small, hygiene): Update each ruleset's `required_status_checks.contexts` from `["check-staging-lock"]` to
`["check-staging-lock", "quality-gates-v2"]`. Both checks gate the merge. This is the workspace-canonical "two-pass +
staging-lock" model.

**Option B** (replace): Update each ruleset to `["quality-gates-v2"]` only. Loses the staging-lock guarantee.

**Option C** (leave): Don't touch. Not blocking anything; accept the inconsistency.

## Recommended path

Option A — additive change matches the canonical CI flow doc. Single API call per repo:

```bash
for entry in execution-service:13647462 instruments-service:13787597 deployment-ui:13787657; do
  r=${entry%:*}; rid=${entry#*:}
  gh api "repos/IggyIkenna/$r/rulesets/$rid" > "/tmp/rs_$r.json"
  python3 -c "
import json
with open('/tmp/rs_$r.json') as f: d = json.load(f)
for rl in d['rules']:
  if rl['type'] == 'required_status_checks':
    contexts = [c['context'] for c in rl['parameters']['required_status_checks']]
    if 'quality-gates-v2' not in contexts:
      rl['parameters']['required_status_checks'].append({'context': 'quality-gates-v2'})
for f_ in ['id','_links','source','source_type','node_id','created_at','updated_at']: d.pop(f_, None)
with open('/tmp/rs_${r}_upd.json', 'w') as f: json.dump(d, f)
"
  gh api "repos/IggyIkenna/$r/rulesets/$rid" --method PUT --input "/tmp/rs_${r}_upd.json"
done
```

Effort: <5 min. Verification: re-fetch the ruleset and confirm both contexts present.

## Provenance

Discovered 2026-05-29 during ci_canonical_v2_migration Phase 4 pre-flight (workflow id wap99raio). Operator acked as
"not blocking" but agreed to file for tracking.

## Why it's an ISSUE not a PLAN

Single-action remediation (3 API calls). Not warranted as a phased plan. Once Option A executed and verified, this issue
archives.
