---
scope: [operator, admin]
created: 2026-05-15
---

# Deployment Flow — Operator Perspective

> Covers the promotion path from local development through staging to main, with QG gates, version graduation,
> and the paper-to-live strategy promotion path. Complements `ci-cd-flow.md` (engineer view).
>
> Cross-references: `codex/08-workflows/ci-cd-flow.md`; `codex/08-workflows/version-graduation.md`;
> `codex/04-architecture/promote-workflow-architecture.md`; `CLAUDE.md` § "Git discipline".

---

## Overview: Three-Gate Promotion Model

```
Local work (feat/* or LDR)
  │
  ├─ Pass 1: bash scripts/quality-gates.sh
  │
  ├─ Pass 2: bash scripts/quickmerge.sh "msg" --agent  →  staging
  │                                                          │
  │                                        Full CI + SIT ────┤
  │                                                          │
  └──────────────────────────────────────────────────────► main
                                                            │
                                              semver-agent: bump + image build
```

Every promotion through a gate requires the previous gate to be green. No bypassing.

---

## Gate 1 — Local Quality Gates (Pass 1)

```bash
cd <repo>
bash scripts/quality-gates.sh
```

Runs in order: ruff format → ruff check → basedpyright → bandit → vulture → pytest → codex audit. All must pass.

**Agent shortcut** (`--agent`): Pass 1 runs full QG. Pass 2 quickmerge skips act + tests (already passed in Pass 1).

---

## Gate 2 — Staging via Quickmerge (Pass 2)

```bash
bash scripts/quickmerge.sh "feat: description"              # standard → staging
bash scripts/quickmerge.sh "feat!: breaking" --to-staging    # breaking change → staging
bash scripts/quickmerge.sh "feat: work" --agent              # agent session
bash scripts/quickmerge.sh "fix: dep" --dep-branch "feat/X"  # cross-repo feature
```

Quickmerge: fast-forwards staging to HEAD, creates PR targeting main, triggers full CI.

**Operator safety checklist before pushing to staging**:
- `git fetch` first — 0 incoming on staging before pushing
- Never `git push` directly — quickmerge is the only sanctioned path
- Breaking change (`feat!:`)? Use `--to-staging` to avoid premature main promotion
- Cross-repo dep update? Use `--dep-branch` to bundle feature + dep in one PR

---

## Gate 3 — Main Promotion + Semver Bump

CI on staging triggers `semver-agent.yml`:
1. Parses latest commit prefix (`feat:` → minor, `fix:` → patch, `feat!:` → minor on 0.x.x)
2. Calls `update-dependency-version.yml` in downstream repos via `repository_dispatch`
3. On success: bumps version in `pyproject.toml` → creates staging commit → CI runs again → if green, promotes to main

**Major bumps** are blocked from auto-promotion:
- `request-major-bump.yml` creates an Issue with `major-bump-pending` label
- Operator comments `/approve` on the issue to execute
- See `codex/08-workflows/version-graduation.md` for full 1.0.0 graduation procedure

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

When repo A is promoted and bumped:
1. `semver-agent.yml` in repo A emits `repository_dispatch` to downstream repos B, C, D
2. `update-dependency-version.yml` in B/C/D updates pyproject.toml minimum pin → staging commit
3. B/C/D CI runs → if green, their semver-agents trigger cascading to their own downstreams

Minor/patch bumps: direct commit to staging with `[skip ci]` to avoid unbounded cascade.
Major bumps: create branch + PR requiring human review (breaking change could need code changes).

See `codex/08-workflows/dependency-cascade.md` for topology and cap rules.

---

## Emergency Procedures

| Scenario | Action |
|---|---|
| Staging CI broken | Fix root cause + push fix to staging. Never skip CI. |
| Wrong version bumped | `gh workflow run request-major-bump.yml` to repin, then investigate semver-agent config |
| Cascading dependency failure | Add `dependency_caps` entry in workspace-manifest.json to stop cascade at that repo |
| Force-sync needed | Run `run-version-alignment.sh` first, then `admin-force-sync-all-to-main.sh` — warns of semver-agent revert risk |
| Live strategy kill switch | Human-only. Use deployment-ui kill-switch panel or `gcloud compute instances stop <vm>` |

**Hard-stop list (human-only, never agent)**: wallet keys, kill-switch arming, force-push to main, version 1.0.0 graduation.

---

## Monitoring After Promotion

- **CI status**: `gh run list --branch main --repo IggyIkenna/<repo> --limit 5`
- **Version**: `cat pyproject.toml | grep ^version`
- **Image build**: GCP Artifact Registry `asia-northeast1-docker.pkg.dev/<project>/<repo>/<repo>:latest`
- **VM health**: `bash deployment-service/scripts/vm/vm_zombie_watchdog.py --dry-run`
- **Strategy liveness**: Deployment UI → Active Strategies → uptime + last heartbeat
