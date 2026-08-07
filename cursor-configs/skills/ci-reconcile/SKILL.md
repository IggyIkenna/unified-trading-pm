---
name: ci-reconcile
description:
  Reconcile the whole fleet's CI/CD pipeline to actually-green, at the root cause — not just re-reading the ci-failures
  Slack channel. Cross-checks every repo's REAL GitHub Actions state against what Slack/ci_status claims (Slack
  timestamps and declared states are not ground truth and go stale fast), classifies every red/lagging item by root
  cause (fleet template-rollout breakage / genuine code regression / transient self-hosted-runner flake / dependency
  phantom-clone / alert-accuracy bug / promotion-lag / provenance-gate block / runner-fleet or Cloud-Build infra
  health), fixes each at the root via the correct documented recovery path, cross-checks whether the AO
  `ci_failure_watcher` escalation should have caught it and didn't, and re-sweeps the full fleet before declaring done.
  Needs no Slack read access at all — every signal it checks (quality-gates-v2 runs, promotion lag, provenance gate,
  self-hosted runner API health, Cloud Build triggers) has a directly-queryable system of record via `gh`/ `gcloud`, so
  it runs identically whether invoked interactively or dispatched to AO (which has no Slack access and can't be pasted
  into). Always auto-fixes — no separate `--fix` flag, no propose-then-wait; it ships corrections directly (quickmerge /
  reprovenance_bypass.sh / a reviewed template rollout) the same way this workspace's background agents already do, and
  reports what it found + did + verified. A genuinely foreign/bulk/design-level decision (bulk-blessing someone else's
  bypass commits, a branching-model change) still stops for an operator decision with structured options — auto-fix
  means "don't ask before shipping an obvious fix," not "never ask." Trigger on `/ci-reconcile`, "unblock the CI
  alerts", "fix these Slack CI alerts at the root", "reconcile the pipeline", "why is Slack saying X but CI shows Y",
  "is the pipeline actually unblocked", "check if CI escalation caught this", "check the runner fleet / Cloud Build
  health".
---

# /ci-reconcile — fleet CI/CD reconciliation and root-cause fix

Answers one question with evidence, then fixes what's actually broken: **is the fleet's CI/CD pipeline really green, and
where exactly is it not — at the root, not the symptom?** Built from the 2026-08-07 incident where a fleet-wide
workflow-template rollout broke `quality-gates-v2` on 8 repos; by the time the Slack wall of alerts was read, 6 of the 8
had already self-recovered, one had a genuine unrelated dependency bug masquerading as a code regression, and the
"resolved" Slack message for the last one was posted while the repo's own gate was still red.

**Always auto-fixes.** This is not a diagnose-and-wait skill (unlike `/data-pipeline-reconciliation`'s read-only
contract) — ship every root-caused fix the same way this workspace's background agents already do
(`quickmerge.sh --agent --files`, `reprovenance_bypass.sh`, a reviewed template rollout), then verify, then report.
Don't stop mid-sweep to ask "should I fix this?" — the findings-triage HARD RULE (in-your-file → fix in same commit;
outside-plan small+clear → ≤30 min) already covers the judgment calls; escalate only a genuinely big/ambiguous finding
per that rule.

## 0. Ground truth first — Slack/ci_status is a claim, GitHub Actions is the fact

**Never act on a Slack alert's stated state.** Before touching anything, re-derive current reality directly:

```bash
# Repo registry — never hardcode a repo list, read the real one
python3 -c "import json; [print(r) for r in json.load(open('unified-trading-pm/workspace-manifest.json'))['repositories']]"

# Per repo, the actual latest conclusion on the trigger branch (usually live-defi-rollout)
gh run list --repo IggyIkenna/<repo> --branch live-defi-rollout --limit 3 --json status,conclusion,name,headSha,createdAt
```

A repo named in an old alert may have already self-recovered (measured: 6/8 repos in the 2026-08-07 incident were green
again within 90 minutes, via a fix commit nobody re-announced). Build the CURRENT red/lagging list from this sweep, not
from the alert text — the alert text tells you where to START looking, not what's still true.

## 0b. The `ci-failures` channel also carries runner-fleet and Cloud-Build infra alerts — sweep those directly too

Not every `ci-failures` post is a `quality-gates-v2`/promotion signal. `glue-runner-health-monitor`,
`glue-runner-crash-loop-watchdog`, `cloud-build-router`, and `cloud-build-failure-watcher` check a DIFFERENT underlying
system (self-hosted runner fleet health, GCP Cloud Build triggers) — same principle applies: query the real system
directly rather than trusting the alert text, and every one of these has a direct query, no Slack needed:

```bash
# Same call the runner-health monitor makes — a 403 here is either a transient token hiccup (check if the NEXT
# scheduled run already recovered before treating it as broken) or a real permissions regression
gh api repos/IggyIkenna/unified-trading-pm/actions/runners?per_page=100
gh run list --workflow=glue-runner-health-monitor.yml --limit 8 --json conclusion,createdAt

# Cloud Build trigger existence/config — a "trigger did not fire" alert branches on whether the trigger exists at all
# (NOT_FOUND → recreate it, mirror a working repo's config) vs exists-but-invocation-failing (check
# cloud-build-router.yml's own trigger-invocation logic first, don't assume the trigger is gone)
gcloud builds triggers describe <trigger-name> --project=<project> --region=<region>
gh run list --workflow=cloud-build-router.yml --limit 6 --json conclusion,createdAt
```

A `glue-runner-crash-loop-watchdog` "recovered" message is informational, not an open finding — it means an existing
automated watchdog already un-wedged a runner service; no action needed unless the SAME runner keeps recurring (that
crosses into a genuine flake vs a real host-level problem worth its own finding). A Cloud-Build alert that references an
existing dated issue doc (check `plans/active/issues/` and `plans/active/` — including `plans/archive/issues/` for ones
already closed) is a pre-existing, separately-tracked condition, not part of THIS sweep's incident — confirm its current
state briefly (don't just assume the archived doc means it's still resolved) and note it in § 7's report without
re-diagnosing it from scratch unless it's now genuinely different from what the doc describes.

## 1. Classify each still-red item before touching it

For every repo whose current `quality-gates-v2` conclusion is `failure`, pull the real log
(`gh run view <id> --log-failed`) and classify:

- **(a) Fleet template-rollout breakage** — the triggering commit is a `rollout-workflow-templates.sh`-generated
  `chore(ci): roll out …` commit that touched only `.github/workflows/*.yml`, and the failure is a workflow-YAML
  parse/step error. Root fix is in the SOURCE template (`unified-trading-pm/scripts/workflow-templates/`), never a
  hand-edit of the per-repo copy — see § 3.
- **(b) Genuine code regression** — the failing selector (`tests`/`typecheck`/`lint-codex`) traces to an actual
  application-code change. Fix the code, ship via `quickmerge.sh --agent --files`.
- **(c) Dependency phantom-clone** — **a CI-only commit (no app code touched) that still fails `typecheck`/`lint-codex`/
  `tests`** is the tell. The QG workflow clones sibling repos (UTL/UAC/etc.) at a resolved version to typecheck/test
  against; a version-tag-resolution race can silently clone the WRONG version, producing spurious `reportUnknown*`/
  `reportAny` typecheck floods or unrelated test failures that are not real bugs in the repo under test. Confirm by
  diffing the failing repo's `.github/workflows/quality-gates-v2.yml` clone/version-resolution logic against a
  currently-green repo's copy, and by reading the actual error content (not just the aggregate `qg_red_reason`, which
  can itself be wrong — cross-check against which QG slice artifacts actually uploaded `qg-slice-failed-*`).
- **(d) Transient self-hosted-runner flake** (cache race, `uv sync --frozen` cache contention) — only re-run after you
  understand why; a blind retry that happens to pass is not a root-cause fix and will recur.
- **(e) Alert-accuracy bug** — `ci_status` (Firestore-SSOT, written by `ci-status-update.yml`) declared a "resolved"
  state (e.g. `SIT_VALIDATED`) for a sha whose OWN `quality-gates-v2` run is still `failure`. Before calling this a bug:
  check whether `SIT_VALIDATED` is legitimately a decoupled signal (system-integration-tests against a different
  snapshot) vs the repo's own unit-level gate — read `scripts/self-hosted-runners/hosted-baseline/ci-status-update.yml`
  for the actual state-machine transition logic. If it's a real inconsistency (a "resolved" status posted while the
  same-sha gate is still red), that's a template bug — see § 3. If it's a real but confusingly-worded distinct signal,
  fix the message wording, same path.

## 2. Fix (b), (c), (d) directly in the target repo

Standard single-repo fix path: root-cause, fix, `bash scripts/quality-gates.sh --no-fix`,
`quickmerge.sh "fix: …" --agent --files '<paths>'`, then re-poll `gh run list` until the sha is green. No template/fleet
blast radius here — ship it the moment you're sure of the root cause, per findings-triage.

## 3. Fix (a) and (e) via the template, never a per-repo hand-edit

**Never hand-edit a per-repo `.github/workflows/*.yml` copy** — it will be silently overwritten by the next rollout and
the fix is invisible to every OTHER repo carrying the same bug. The correct path:

1. Find the source template in `unified-trading-pm/scripts/workflow-templates/` (the `.yml.tmpl` the broken per-repo
   file was generated from).
2. Fix the template. Prepare the exact diff.
3. Because this fans out to every repo in `workspace-manifest.json`'s registry (~25 repos) in one shot, do this
   deliberately once: dry-read the rollout script's diff/plan output if it has one, apply, then immediately verify
   across the fleet (§ 5) rather than assuming success. This is still an auto-fix (per this skill's contract) — it is
   not a "propose and wait," but a fleet-wide push earns one clean, careful pass instead of a blind re-run if something
   looks off.
4. Run `bash scripts/workflow-templates/rollout-workflow-templates.sh` per its own usage (read `--help` first — flags
   like scoping to affected repos only, or dry-run, may exist and are cheaper than a full fleet push when only a handful
   of repos actually need the fix).

## 4. Promotion-lag and provenance-gate blocks are in scope

"Unblocked pipeline" includes branches actually propagating, not just the trigger-branch gate being green. Sweep lag:

```bash
gh api repos/IggyIkenna/<repo>/compare/main...live-defi-rollout --jq '.ahead_by'   # LDR ahead of main
gh api repos/IggyIkenna/<repo>/compare/live-defi-rollout...main --jq '.ahead_by'   # main ahead of LDR
```

Or read `scripts/cicd/promotion_lag_monitor.py`'s own output — it's the source of the Slack `branch-health` alert, so
its live state is more current than the alert text.

- **Provenance-gate BLOCKED** (non-quickmerge/bypass commit on LDR, flagged by `check_strict_quickmerge.py`): find the
  real bypass list via `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` — **not** a
  raw `git log main..live-defi-rollout` count, which mixes in every normally-quickmerged commit and can overstate the
  real number by 10-50x. If it's the current LDR **tip** → `quickmerge.sh --agent --files` it properly through the gate.
  If it's **mid-history** (something landed on top since) → `scripts/cicd/reprovenance_bypass.sh <sha> --push` (read its
  `--help`/source first). **Never hand-arm auto-merge** to route around this. **Size/authorship gate before auto-fixing
  this one**: a small number of commits (roughly ≤5), single-author, diff-reviewed, self-contained → reprovenance
  directly, no need to stop. A larger, foreign, multi-subsystem, multi-agent backlog → this is the one case in this
  skill where auto-fix stops and asks first (structured options: bulk-bless-after-review / re-ship each individually /
  show the list and wait) — bulk-blessing code you can't independently verify as promote-ready is a judgment call, not a
  mechanical fix, per this workspace's own established precedent
  (`plans/archive/issues/utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md` and
  `plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`). If the operator
  authorizes the bulk path, still diff-review every commit for anything destructive/secret-leaking/production-credential
  -touching before sweeping it in, and flag-not-sweep anything that fails that screen.
- **Just lagging past the promote cadence, not blocked**: verify the fleet promote cron
  (`scripts/cicd/ldr_to_main_fleet_promote.sh` / the `ldr-to-main-promote-fleet.yml` workflow, `*/15`) is actually
  firing and succeeding (`gh run list --workflow=<it> --limit 5`). If it's healthy and just hasn't ticked yet, don't
  force anything — report expected clear time. If a run is failing, root-cause that same as any other CI failure.

## 5. Cross-check the AO escalation system — don't let a real gap go unfixed silently

For any repo that was still red for a meaningful window (say, >30-60 min) before being fixed: did
`scripts/repo-management/ci_failure_watcher.py`'s auto-recovery actually engage, or did the fix land from a human /
interactive push instead (check the fix commit's author string — `[background-agent]` vs a plain slot/host or
`[unknown]` tag)? A repo that stayed red until an interactive session happened to notice it is an escalation-coverage
gap, not a one-off. If you find a small, clear, obviously-correct bug in the watcher's detection logic, fix it the same
way as any other code fix (§ 2). If the gap is structural (a whole failure class it was never designed to catch, or it
isn't running on the cadence it's supposed to), that's a finding for `plans/active/issues/<slug>_<date>.md` and an
operator notification per the findings-triage HARD RULE — don't quietly patch around agent-orchestrator's own logic
without understanding the design intent first.

## 6. Verify — full-fleet sweep, not just the repos that were named

Re-run § 0's sweep across every repo in `workspace-manifest.json`'s registry, not just the ones the original alert named
(the alert's repo list is itself just a symptom of one incident, not the definition of "the fleet"). Every repo should
show `quality-gates-v2` conclusion `success` on its trigger branch, and every branch-pair from § 4 should be either
caught up or genuinely just waiting on its next scheduled tick with a healthy cron behind it.

## 7. Report

For each item found: root-cause classification (§ 1's letter), evidence (log excerpt / commit sha / diff), what was
shipped (repo + sha, or template diff + rollout confirmation), and post-fix verification (green run id). Explicitly call
out: (1) any alert that was already stale/self-resolved by the time you looked (don't re-fix what's already fixed), (2)
any alert-accuracy issue found and its fix, (3) the AO-escalation verdict from § 5, (4) anything that could NOT be
resolved this pass — file it per findings-triage, never leave it as an unlogged "still broken."

## Under `/autonomous`

No-pause loop: after the full-fleet sweep clears, don't stop and wait for the next Slack alert — re-sweep once more to
confirm stability, then stop (this is an on-demand reconciliation, not a standing watcher; for continuous monitoring
that's `ci_failure_watcher.py`'s job, not this skill's).

## What this skill does NOT do

Does not rewrite `agent-orchestrator`'s escalation logic beyond a trivial, obviously-correct fix (§ 5) — a real
design-level gap is a filed finding, not a same-session rewrite. Does not force-push, does not hand-arm auto-merge, does
not bypass the provenance gate other than via the documented `reprovenance_bypass.sh` recovery path, and does not
hand-edit a per-repo workflow copy outside the template source. Codex SSOTs this skill leans on:
`/codex/08-workflows/ci-cd-flow.md`, `/codex/04-architecture/ci-alerting.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`.
