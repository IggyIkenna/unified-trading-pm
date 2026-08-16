---
doc_type: codex-ssot
title: Deployment Flow — Operator Perspective
summary: >-
  Operator-perspective deployment path: the 3 gates (local quality-gates.sh Pass-1 → quickmerge Pass-2 → main promotion
  + semver bump) through to Cloud Build, the paper→live strategy-promotion CLI/UI paths, emergency procedures, and the
  human-only hard-stop list.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, deployment-ui, e2e-testing]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, quality-gates, verification, observability]
related:
  [
    ./ci-cd-flow.md,
    ./version-graduation.md,
    /codex/04-architecture/promote-workflow-architecture.md,
    ./dependency-cascade.md,
  ]
created: 2026-05-15
authoritative_for:
  [deployment-flow operator gate-walkthrough (3-gate local→staging→main promotion + emergency procedures)]
referenced_by:
  [
    /codex/08-workflows/branch-and-version-reference-model.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/08-workflows/cutover-window-dependency-order.md,
    /codex/08-workflows/dependency-cascade.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Deployment Flow — Operator Perspective

> Covers the promotion path from local development through staging to main, with QG gates, version graduation, and the
> paper-to-live strategy promotion path. Complements `ci-cd-flow.md` (engineer view).
>
> Cross-references: `/codex/08-workflows/ci-cd-flow.md`; `/codex/08-workflows/version-graduation.md`;
> `/codex/04-architecture/promote-workflow-architecture.md`; `CLAUDE.md` § "Git discipline".

---

## Full Pipeline: LDR → Cloud Build

> **The unit of work lands on `live-defi-rollout` (LDR) and stops.** A slot ships via `quickmerge --agent --files`,
> which commits to LDR. The **LDR→main fleet promoter** (`ldr-to-main-promote-fleet.yml`, cron `*/30`) opens a standing
> per-repo promote PR (head=LDR) and auto-merges it when all three MVP gates are green — **directly to `main`, no
> staging hop**. `staging` is KEPT as a branch but is **DORMANT** behind a reversible per-repo toggle
> (`promotion_model: ldr_main` in `workspace-manifest.json`; see `/codex/08-workflows/ci-cd-flow.md` § "Branch model"
> for the full topology + staging re-entry procedure).
>
> This is the operator-facing summary; the engineer-view SSOT with the full mermaid diagram, branch table, and
> per-workflow drill-down is `/codex/08-workflows/ci-cd-flow.md`.

```
1. Push to live-defi-rollout (LDR)
   └─ bash scripts/quality-gates.sh          ← FULL: lint+tests+typecheck+codex+pip-audit
      └─ exit 0, no skip flags → writes .qg_last_passed_sha (SHA fingerprint + the resolved
         ENVIRONMENT/DEPLOYMENT_ENV — appended 2026-07-30, qg_sentinel_environment_blind_2026_07_23.md)
         partial run (--skip-tests etc.)     → sentinel NOT written

2. bash scripts/quickmerge.sh "msg" --agent --files '...'
   └─ reads .qg_last_passed_sha — SHA AND config (ENVIRONMENT/DEPLOYMENT_ENV) must both match
      SHA/config mismatch / missing → EXIT 1 ("Run quality-gates.sh on current HEAD first")
      SHA + config match → skip Pass 2 QG re-runs → commit + push to LDR
      (Pass 1 QG wrote the sentinel on this exact SHA; Pass 2 only ships it)

3. LDR→main fleet promoter picks up the new LDR HEAD
   └─ ldr-to-main-promote-fleet.yml (cron */30) — standing per-repo promote PR (head=LDR, base=main)
      GATE SET (exactly three, all must be green before auto-merge arms):
      a) sit-gate/fleet-green — fleet-shared SIT signal (full-workspace-sit.yml green?)
         → posted as a commit status on every promote-PR head, unconditionally
      b) quality-gates-v2 — per-repo CI on the promote PR (head=LDR, base=main)
      c) quickmerge-provenance — check_strict_quickmerge.py verifies the Quickmerge: trailer
      └─ all 3 green → auto-merge (squash) → main

4. On push to main:
   a) semver-agent.yml — parses commit prefix, mints git tag (vX.Y.Z), bumps pyproject.toml
   b) publish-package dispatcher → AR wheel publish
   c) cloud-build-router.yml → Cloud Build / CodeBuild image build
      └─ clone deps (live-defi-rollout branch)
         docker build
         quality-gates.sh --no-fix --quick inside container (lint+codex only, no tests)
         push to Artifact Registry (tagged :VERSION :SHORT_SHA :latest)
         CVE scan — CRITICAL gate
         notify-deployment dispatch to deployment-service
   d) main-backmerge-to-ldr.yml — FF-only merge of main back into LDR (on push + hourly drift-tick)

5. staging — DORMANT (0 repos route through it today)
   └─ reversible per-repo toggle: flipping a repo off ldr_main routes it LDR→staging→main
      (major/breaking version bump or explicit operator decision — see ci-cd-flow.md § "Staging
      re-entry procedure" for the exact uncomment + manifest-flip steps)
```

**Branch protection enforcement** (`main` only):

- Required status checks on `main`: `quality-gates-v2` + `sit-gate/fleet-green` (for `ldr_main` repos;
  `pin_branch_protection_rulesets.py` requires `sit-gate/fleet-green` ONLY for `promotion_model=ldr_main` repos — never
  `unified-trading-pm` / `system-integration-tests`, whose main-bound path differs).
- `staging` has NO branch protection rulesets — it is dormant (drain crons stopped); if reactivated the same gates apply
  (SIT re-homed onto a frozen LDR snapshot + `quality-gates-v2` + quickmerge-provenance).
- Caller file: `.github/workflows/quality-gates-v2.yml`; callee: `python-quality-gates-v2.yml` in PM.
- v1 `quality-gates`/`workspace-qg` **RETIRED 2026-05-29** — see `/codex/08-workflows/ci-cd-flow.md` § quality-gates-v2.

**Note on LDR:** `live-defi-rollout` has no remote CI — `quality-gates-v2` does NOT trigger on LDR pushes. Local
`quality-gates.sh` + sentinel is the only gate on LDR. This is by design: LDR is a rapid-dev integration trunk; remote
CI fires only at the LDR→main promote-PR boundary.

---

## Gate 1 — Local Quality Gates (Pass 1)

```bash
cd <repo>
bash scripts/quality-gates.sh
```

Runs in order: ruff format → ruff check → basedpyright → pytest → codex audit → pip-audit. All must pass. On clean exit
with **no skip flags**: writes `.qg_last_passed_sha` with the current HEAD SHA plus the resolved
`ENVIRONMENT`/`DEPLOYMENT_ENV` this pass ran under (appended 2026-07-30 — `qg_sentinel_environment_blind_2026_07_23.md`;
see `/codex/05-infrastructure/quickmerge-architecture.md` § "Sentinel integration").

**Enforcement**: `quickmerge --agent` reads this sentinel and exits 1 if the SHA doesn't match OR the sentinel's
recorded configuration doesn't match what this run resolved. Partial runs (`--skip-tests`, `--skip-lint`, `--quick`,
`--skip-codex`) do NOT write the sentinel and cannot unblock a quickmerge. There is no way to fake a full pass.

---

## Gate 2 — Quickmerge (Pass 2)

```bash
bash scripts/quickmerge.sh "feat: description" --agent --files '...'   # agent session (canonical)
bash scripts/quickmerge.sh "feat: work" --agent                        # agent session (all files)
bash scripts/quickmerge.sh "feat!: breaking" --to-staging               # breaking change → staging (dormant path)
bash scripts/quickmerge.sh "fix: dep" --dep-branch "feat/X"             # cross-repo feature
```

Quickmerge: verifies the Pass 1 sentinel (SHA + config match) → commits + pushes to LDR. That's it — the unit of work
lands on LDR and stops. The LDR→main fleet promoter handles promotion from there. `staging` is NOT the default
destination; `--to-staging` is the dormant exception path for a major/breaking bump routed through staging.

**Operator safety checklist before pushing to LDR**:

- `git fetch` first — ensure your clone is current against `origin/live-defi-rollout`
- Never `git push` directly for code — quickmerge is the only sanctioned path
- Breaking change (`feat!:`)? Default still goes LDR→main direct; `--to-staging` only if a repo is explicitly routed off
  `ldr_main` (see `/codex/08-workflows/ci-cd-flow.md` § "Staging re-entry procedure")
- Cross-repo dep update? Use `--dep-branch` to bundle feature + dep in one PR
- After quickmerge lands, verify: `git merge-base --is-ancestor <SHA> origin/live-defi-rollout`

---

## Gate 3 — Main Promotion + Semver Bump

The LDR→main fleet promoter (`ldr-to-main-promote-fleet.yml`, cron `*/30`) opens a standing per-repo promote PR
(head=LDR, base=main) with a **frozen per-SHA head** — it never rebases, so the gate status stays stable.

**The three MVP gates** (the ONLY things that block auto-merge; see `/codex/08-workflows/ci-cd-flow.md` § "The MVP gate
set" for the retired/advisory-only list):

1. **`sit-gate/fleet-green`** — fleet-shared SIT signal. Computed each tick from the last COMPLETED
   `full-workspace-sit.yml` run on `system-integration-tests` and posted as a commit status on every promote-PR head
   unconditionally (fail-CLOSED on any read gap/error).
2. **`quality-gates-v2`** — per-repo CI on the promote PR. The canonical required check on every `ldr_main` repo's main
   ruleset.
3. **quickmerge-provenance** — `check_strict_quickmerge.py` verifies the `Quickmerge:` trailer on every commit in the
   promote-PR diff; only quickmerge'd content reaches main.

All three green → the promoter arms `gh pr merge --auto --squash --delete-branch` and the PR merges to `main`.

**On push to `main`**, `semver-agent.yml` fires:

1. Parses latest commit prefix (`feat:` → minor, `fix:` → patch, `feat!:` → minor on 0.x.x)
2. Mints a git tag (`vX.Y.Z`) on the squashed merge commit
3. Bumps version in `pyproject.toml`
4. Calls `update-dependency-version.yml` in downstream repos via `repository_dispatch`
5. `publish-package` dispatcher publishes the wheel to Artifact Registry
6. `main-backmerge-to-ldr.yml` merges the reconciled `main` back into LDR (FF-only, never force; on push + hourly
   drift-tick) so LDR stays current

**Major bumps** are blocked from auto-promotion:

- `request-major-bump.yml` creates an Issue with `major-bump-pending` label
- Operator comments `/approve` on the issue to execute
- See `/codex/08-workflows/version-graduation.md` for full 1.0.0 graduation procedure

**The `promotion_model` toggle (reversible, per-repo).** Today **24 repos are `ldr_main`** (LDR→main direct) and
**`unified-trading-pm` runs its own dedicated `ldr-to-main-promote.yml` Option-B path**, so **0 repos route through
staging**. Flipping a repo off `ldr_main` (a major/breaking version bump or an explicit operator decision) routes THAT
repo LDR→staging→main again — the gates are UNCHANGED (same three), staging just adds the hop. Do not describe staging
as the default path; it is the dormant exception.

---

## Strategy Promotion: Paper → Live

This is the operator-facing promotion for trading strategies (separate from code deployment).

### CLI Path (Primary — May-23)

```bash
# Paper run with quality check
bash e2e-testing/scripts/defi/run-paper.sh --strategy carry_staked_basis --asset-group defi

# Review paper results, then promote to live
bash e2e-testing/scripts/defi/run-live.sh --strategy carry_staked_basis --asset-group defi
```

### UI Path (Secondary — May-23)

1. Go to Deployment UI → Strategy tab
2. Click **Promote** on a paper-validated strategy
3. `POST /api/promote/{strategy_id}/{manifest_id}` → `MinimalCandidateManifest` in Firestore
4. VM auto-launches with `MANUAL_TRADE_GATE=true` for first 3 trading days
5. `DART ManualTradeGateDialog` prompts before each order for days 1-3

**Valid promote targets for May-23**: `paper_1d` → `live_early` only. `live_full` is post-cutover.

---

## Dependency Cascade Flow

> **Target branch updated for the LDR-direct model**: this section predates the `ldr_main` promotion model above and
> originally described the target as `staging`. Staging is now DORMANT (0 of 24 `ldr_main` repos route through it) — the
> cascade's target is each downstream repo's `live-defi-rollout` branch today, per the same `promotion_model` toggle.
> `/codex/08-workflows/dependency-cascade.md` (linked below) has not yet been re-verified against this update.

When repo A is promoted and bumped:

1. `semver-agent.yml` in repo A emits `repository_dispatch` to downstream repos B, C, D
2. `update-dependency-version.yml` in B/C/D updates pyproject.toml minimum pin → commit to the repo's active integration
   branch (`live-defi-rollout` for `ldr_main` repos; `staging` only for a repo still on that dormant model)
3. B/C/D CI runs → if green, their semver-agents trigger cascading to their own downstreams

Minor/patch bumps: direct commit with `[skip ci]` to avoid unbounded cascade. Major bumps: create branch + PR requiring
human review (breaking change could need code changes).

See `/codex/08-workflows/dependency-cascade.md` for topology and cap rules.

---

## Emergency Procedures

| Scenario                     | Action                                                                                                           |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Staging CI broken            | Fix root cause + push fix to staging. Never skip CI.                                                             |
| Wrong version bumped         | `gh workflow run request-major-bump.yml` to repin, then investigate semver-agent config                          |
| Cascading dependency failure | Add `dependency_caps` entry in workspace-manifest.json to stop cascade at that repo                              |
| Force-sync needed            | Run `run-version-alignment.sh` first, then `admin-force-sync-all-to-main.sh` — warns of semver-agent revert risk |
| Live strategy kill switch    | Human-only. Use deployment-ui kill-switch panel or `gcloud compute instances stop <vm>`                          |

**Hard-stop list (human-only, never agent)**: wallet keys, kill-switch arming, force-push to main, version 1.0.0
graduation.

---

## Monitoring After Promotion

- **CI status**: `gh run list --branch main --repo IggyIkenna/<repo> --limit 5`
- **Version**: `cat pyproject.toml | grep ^version`
- **Image build**: GCP Artifact Registry `asia-northeast1-docker.pkg.dev/<project>/<repo>/<repo>:latest`
- **VM health**: `bash deployment-service/scripts/vm/vm_zombie_watchdog.py --dry-run`
- **Strategy liveness**: Deployment UI → Active Strategies → uptime + last heartbeat
