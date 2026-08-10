---
doc_type: issue
title:
  "Plan Alignment Check fails with npm EACCES (exit 243) on [self-hosted, glue] — `npm install -g
  @anthropic-ai/claude-code` cannot replace the ROOT-owned global package; template fixed, per-repo propagation still
  outstanding"
summary: >-
  Measured live 2026-08-10 (~18:16-18:46Z). Every `Plan Alignment Check` failure on the fleet that evening shared one
  root cause, and none of them were repo content: the glue self-hosted runners already carry `@anthropic-ai/claude-code`
  installed as ROOT, the runner user (`ubuntu`) cannot rename over it, and the workflow's bare `npm install -g`
  therefore dies `EACCES ... rename '/usr/local/lib/node_modules/@anthropic-ai/claude-code'` and exits 243. Hit
  execution-service (x2, 18:16Z + 18:31Z), strategy-service (18:46Z), and market-tick-data-service (surfaced as the
  `Plan Alignment Check` FAILURE on promote PR #939). LDR `quality-gates-v2` was GREEN in all three repos at the same
  time, which is the tell that this is an environment fault rather than a code one. The SSOT template
  `scripts/templates/plan-alignment-agent.yml` is FIXED (unified-trading-pm@d901c4e050) — it now prefers the install,
  accepts a working pre-existing CLI on EACCES, and still fails CLOSED when no CLI exists at all. The per-repo copies
  were then propagated the same day, surgically rather than by rendering the template (which was measured to carry
  unrelated passengers): execution-service@62ca29a43, features-service@5e7f2fe3, market-tick-data-service@89cdd578,
  strategy-service@86696b7e. Scope correction worth keeping: only FOUR repos run `[self-hosted, glue]` —
  `instruments-service` and `market-data-processing-service` are `ubuntu-latest` and never had this bug.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    execution-service,
    strategy-service,
    market-tick-data-service,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, workflow-templates, npm, permissions, plan-alignment]
related:
  [
    /plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md,
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
  ]
created: 2026-08-10
author: claude (interactive session, slot-3 CI audit)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-08-10 auditing every CI failure since midnight; the three failing repos were reached from `gh run
    list` conclusions, and the shared cause from `gh run view --log-failed` on strategy-service run 31420755852 — not
    from the Slack alert text, which named only the check",
  ]
resolved_by:
locked_by:
locked_since:
context_scope: [scripts/templates/plan-alignment-agent.yml, scripts/propagation/rollout-agent-workflows.sh]
---

# Plan Alignment Check dies on an environment detail, not on repo content

## What was measured

```
npm ERR! code EACCES
npm ERR! syscall rename
npm ERR! path /usr/local/lib/node_modules/@anthropic-ai/claude-code
npm ERR! dest /usr/local/lib/node_modules/@anthropic-ai/.claude-code-1devilah
##[error]Process completed with exit code 243
```

`runs-on: [self-hosted, glue]` in both the template and every per-repo copy. The `dest` being a `.claude-code-<rand>`
staging name is the tell: npm is trying to REPLACE an existing install, not create one — the package is already there,
owned by root, and the runner user cannot move it aside.

Failures, all the same trace: execution-service runs 31418211671 (18:16Z) and 31419480221 (18:31Z), strategy-service
31420755852 (18:46Z), market-tick-data-service as the `Plan Alignment Check` FAILURE on promote PR #939. In every case
that repo's own `quality-gates-v2` on `live-defi-rollout` was SUCCESS at the same time — an environment fault wearing a
per-repo check's name.

Not a promotion blocker: `Plan Alignment Check` is advisory, not one of the three required LDR→main gates
(`sit-gate/fleet-green` + `quality-gates-v2` + quickmerge-provenance, per CLAUDE.md). The cost is alert noise and a red
check that trains people to ignore red checks — which is why it is worth closing rather than tolerating.

## Fix shape (already in the template)

Prefer the install; accept a WORKING pre-existing CLI when the global install is refused; fail CLOSED when there is no
usable CLI at all, so this can never silently green a run that never had the agent available. Shipped to the SSOT in
unified-trading-pm@d901c4e050 — YAML parses, `bash -n` clean, actionlint unchanged at 3 pre-existing findings.

## Todos

- [x] [DEVOPS] P2. **Propagate the guard to the affected per-repo copies.** ✅ Done 2026-08-10, surgically, NOT via the
      template renderer. Evidence: execution-service@62ca29a43 · features-service@5e7f2fe3 ·
      market-tick-data-service@89cdd578 · strategy-service@86696b7e — each `-1/+16`, each gated
      (`quality-gates.sh --no-fix` green, sentinel == HEAD) and shipped by `quickmerge --agent --files`, guard verified
      present on the remote in all four via `git ls-remote` + `git show origin/…`. **The scope was WRONG in the first
      draft of this doc and the correction is the point**: only **4** repos run `[self-hosted, glue]`.
      `instruments-service` and `market-data-processing-service` are `ubuntu-latest`, where the runner user owns the
      global prefix and the install succeeds — they never had this bug and were deliberately left untouched. The earlier
      "5 of 6 matched the template byte-for-byte at 84 lines" was derived from LINE COUNT, not content; equal length is
      not equal content, and checking the actual removed lines is what exposed it. **Why not
      `rollout-agent-workflows.sh`**: rendering the SSOT template over these copies was measured to carry passengers
      into a commit labelled as a one-line npm fix — `runs-on: ubuntu-latest` → `[self-hosted, glue]` for the two
      unaffected repos (an infrastructure migration), `actions/checkout` v4→v5 in market-tick-data-service, and the
      `claude --print` invocation plus `GH_ORG` form in execution-service. Separately the script has NO per-template
      filter, so a blanket run also syncs `agent-audit.yml` into ~13 repos from market-tick-data-service's live copy
      (`PROTOTYPE_AUDIT`, line 78 — there is no `scripts/templates/agent-audit.yml`), and that is NOT benign: the MTDS
      prototype is a migrated "canonical thin form" while strategy-service still carries the legacy
      full-autonomous-agent version, a 134-line functional divergence. One fix, no passengers. **Keep this lesson**: the
      TEMPLATE was itself the stale side of a drift — strategy-service had a `concurrency:` block the template lacked,
      so a render would have SILENTLY STRIPPED it. Adopted into the template in unified-trading-pm@90069a38ba (now a
      superset of every live copy) and confirmed preserved on strategy-service's remote after shipping. "Never hand-edit
      a per-repo copy" is usually framed as protecting the template; this is the same rule pointing the other way.
      **Re-run the superset check before any future rollout of this template.** To re-apply the guard by hand if a
      future render ever strips it, copy the `Install Claude Code CLI` step verbatim out of
      `scripts/templates/plan-alignment-agent.yml` — that is the SSOT and it stays current, whereas the one-off patch
      script written for this propagation was deliberately not promoted (all four repos are done; a tool with no
      remaining consumer is debt). Repo: unified-trading-pm.
- [ ] [DEVOPS] P3. **Decide whether the runner image should stop shipping a root-owned global
      `@anthropic-ai/claude-code` at all.** The workflow guard makes the symptom survivable, but the underlying setup —
      a root-installed global package that the runner user is then asked to update on every run — will keep producing
      this class. Either drop it from the image (let each run install into a user-writable prefix) or pin it in the
      image and remove the install step entirely. Needs the runner-image owner. Repo: unified-trading-pm.

## Why unified-trading-pm itself is NOT in scope

PM's own `rules-alignment-agent.yml` carries the same bare `npm install -g`, but runs on `ubuntu-latest`, where the
runner user owns the global prefix and the install succeeds. It has not failed and does not need the guard. Noted
because an obvious "fix every copy of this line" sweep would touch it for no reason — and because
`scripts/self-hosted-runners/hosted-baseline/rules-alignment-agent.yml` is a GENERATED snapshot (rebuilt by
`hosted-baseline.sh snapshot`, used by `restore` to put the hosted form back), not a source template: editing it changes
nothing in CI and is overwritten on the next snapshot. Both were established the hard way this session.
