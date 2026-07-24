# Agent Prompt — Phase 1: Foundation & Prep

> Paste this entire prompt into a new agent session to execute Phase 1. Do NOT start Phase 2 until every done criterion
> below is checked.

> **2026-03-24:** Steps referencing **`execution-results-api`** describe **historical** extraction work. The
> consolidated gateway is **`unified-trading-api`**; archived repos are under **`archive/README.md`**.

---

Follow all workspace cursor rules in .cursorrules. No summary docs (no-summary-docs.mdc). uv not pip. quickmerge not git
push. basedpyright <dir>/ not basedpyright. Delete deprecated code; no parallel code paths. Search unified libraries
before implementing anything new.

WORKSPACE_ROOT=${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos All Python/pytest/ruff/basedpyright/QG
commands: cd $WORKSPACE_ROOT
&& source .venv-workspace/bin/activate first.

---

## Standard of Work — Citadel Audit-Worthy

> **When in doubt, assume a senior quant engineer at a top-tier fund (Citadel, Two Sigma, DE Shaw) is reviewing every
> PR. Build accordingly.**

This means:

- No TODO comments in production code — open a GitHub issue instead
- No magic numbers or hardcoded strings — use constants from UCI/AC
- No skipped tests — every code path tested, every skip documented with issue link
- No untested infrastructure changes — every script runs cleanly before commit
- No silent failures — every error logged with `service_name`, `correlation_id`, `timestamp`
- Every secret through Secret Manager — never env vars, never config files
- Every config through `UnifiedCloudConfig` — never `os.getenv()`
- Meaningful error messages — not "an error occurred"
- All public functions/classes have docstrings and full type hints
- If it would fail a Citadel code review, it is not done

---

## Your Mission

Execute **Phase 1 — Foundation & Prep** as specified in:
`unified-trading-pm/plans/active/phase1_foundation_prep.plan.md`

Read that file completely before starting any work. Phase 2 cannot start until all DONE criteria below are met.

---

## SSOT — Read These First

| Source                 | Path                                                             | What it governs                                                |
| ---------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------- |
| Workspace manifest DAG | `unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg`                  | 63 repos, 13 levels (L0-L12) — L0=PM, L1=codex, L2+=code repos |
| Runtime topology       | `deployment-service/configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg` | Runtime service wiring                                         |
| Manifest JSON          | `unified-trading-pm/workspace-manifest.json`                     | Machine-readable repo registry                                 |
| SSOT index             | `unified-trading-codex/00-SSOT-INDEX.md`                         | Maps every topic to its canonical doc                          |

---

## Naming — Zero Tolerance for Old Names

Any old name anywhere is **immediate technical debt**. Fix at every level the moment you see it.

| Wrong (old)                       | Canonical                          |
| --------------------------------- | ---------------------------------- |
| `market-tick-data-handler`        | `market-tick-data-service`         |
| `client-reporting-api`            | `client-reporting-api`             |
| `alerting-service`                | `alerting-service`                 |
| `position-balance-monitor` (bare) | `position-balance-monitor-service` |
| `ml-training-ui`                  | `ml-training-ui`                   |
| `execution-analytics-ui`          | `execution-analytics-ui`           |

**Every rename must be complete at ALL levels simultaneously:**

1. GitHub repo name
2. GCP Artifact Registry package name + all `cloudbuild.yaml` image tags
3. Cloud Build trigger name
4. `pyproject.toml` `[project] name` + all dependent repos' dep entries
5. Python package directory (rename dir + update `__init__.py`)
6. Every `import` / `from X import` across all 57 repos (use `rg`)
7. `workspace-manifest.json` — `name`, `github_url`, `artifact_registry_url`, `package_name`
8. `runtime-topology.yaml` + deployment checklists + `RUNTIME_TOPOLOGY_DECISIONS.md`
9. `.cursor/rules/*.mdc` + `unified-trading-codex/**/*.md`
10. PubSub topic names, Secret Manager secret names, Cloud Run service names

**NEVER:** old name as alias, re-export, `_deprecated.py`, or `try/except ImportError` fallback.

---

## Bottom-Up Rule — Template First, Then Propagate

New CI/CD pattern needed → update `unified-trading-pm/scripts/quickmerge.sh` (SSOT), then propagate. New setup pattern
needed → update `unified-trading-pm/scripts/setup.sh` (SSOT), then propagate. New QG check needed → update
`unified-trading-/codex/06-coding-standards/quality-gates.md` first, then template, then propagate. New cursor rule
needed → create in `.cursor/rules/`, then add to `.cursorrules` if always-apply. New manifest field needed → update
codex schema doc first, then `workspace-manifest.json`.

**Never** add a one-off fix to a single repo that belongs in a shared template.

---

## Pure Import Smoke Test (run during Stream C QG baseline)

In every Python repo, as part of `ci-qg-baseline-run`:

```bash
python -c "import <package_name>" 2>&1
```

Failure = P0 blocking issue. Record in manifest `ci_status` as `FAILING: import_error`. Import failures cascade — they
block all other tests. Record all failures before touching anything else.

---

## Execution Order

Streams A, B, C run in parallel. Within Stream A: A0 → A1 → A2 → A3 strictly sequential.

### Stream A — CI/CD (BLOCKING: Phase 2 cannot start until A3 complete)

**A0 — DAG Validation** (precondition for A1):

- Verify all `workspace-manifest.json` `arch_tier` fields match `WORKSPACE_MANIFEST_DAG.svg`
- Verify 4 API service repos present in manifest (ERA, MDA, CRA + check for 4th)
- Fix MEL visual tier bug in DAG SVG (MEL must show T0)
- Create `dag-enforcement.mdc` cursor rule (see Stream C)

**A1 — Quickmerge + Version-Bump + Setup Rollout** (10 parallel agents, 58 repos, 5–6 repos each):

1. Copy `scripts/quickmerge.sh` from SSOT: `unified-trading-pm/scripts/quickmerge.sh`
2. Copy `.github/workflows/version-bump.yml` from SSOT: `unified-trading-pm/.github/workflows/version-bump.yml`
3. Copy `scripts/setup.sh` from SSOT: `unified-trading-pm/scripts/setup.sh` — replace any existing ad-hoc setup.sh
4. Set `PACKAGE_NAME` in each repo's `setup.sh` (auto-detected from `pyproject.toml` if blank)
5. Verify `pyproject.toml` has `version` field at `0.x.x`
6. Verify no old names in `pyproject.toml`, `cloudbuild.yaml`, `quality-gates.sh` — fix if found
7. Run `bash scripts/setup.sh --check` to verify setup works
8. `git commit 'chore: sync quickmerge + setup.sh + version-bump templates'` → `git push`

**Repo count note:** 58 git repos exist on disk. 51 have `pyproject.toml` (Python), 12 are TypeScript UIs (have
`package.json`). All 58 get quickmerge.sh + version-bump.yml + setup.sh. TypeScript repos skip Python-specific setup
steps (venv, uv, pyproject) automatically.

**A2 — Commit-Msg Hooks** (4 parallel agents, after A1):

- Add commit-msg hook to all 57 repos: validates `feat:|fix:|chore:|docs:|refactor:|test:|ci:|BREAKING CHANGE:` prefix
- Verify all `pyproject.toml` at `0.x.x` (not pre-bumped)
- Confirm GCP AR accepts PEP 440 `+local` versions
- Add `refactor_scope` field to workspace-manifest schema

**A3 — CI/CD Pipeline Wiring** (3 parallel agents, after A2):

- `${DEP_BRANCH:-main}` + `git ls-remote` fallback in all `quality-gates.yml`
- Cloud Build feature branch trigger + version inject (`+feat.BRANCH_SHA`)
- GH Action version bump: reads squash-merge commit prefix → bumps semver on main merge

### Stream B — Deployment Structure (parallel with A)

All items in Stream B are independent — run them in parallel:

1. **arch-visualizer-extract** — Extract `execution-service/visualizer-ui/` → `execution-analytics-ui` repo;
   `execution-service/visualizer-api/` → `execution-results-api`. Delete both from `execution-service`. Update
   `cloudbuild.yaml`.
2. **arch-deployment-split** — Split `unified-trading-deployment-v3` → `deployment-service` + `deployment-api` +
   `deployment-ui` + `system-integration-tests`. Pre-split: fix `orchestrator.py` (672 L) and `config_loader.py` (551 L)
   by SRP first.
3. **arch-ui-audit-full** — Find embedded UI artifacts (`ui/`, `frontend/`, `*.tsx`, `*.jsx`, `package.json`) in all
   service repos. Fix every violation.
4. **integration-system-tests-repo** — Create `system-integration-tests` repo per
   `unified-trading-pm/docs/new-repo-setup.md`
5. **integration-layer2-infra-verify** — Add `deployment-service/scripts/verify_infra.py`; expose as `GET /infra/health`
6. **infra-merge-utdv3** — Move `ibkr-gateway-infra/ibkr-gateway/` → `deployment-service/infra/ibkr-gateway/`. Delete
   `ibkr-gateway-infra/`.
7. **hybrid-live-seam** — Document + implement in-memory adapter seam for `MDPS←MTDH` (under `co_located_vm` profile
   only)

### Stream C — QG Baseline Audit (parallel with A + B)

All items independent — run in parallel:

1. Create `.cursor/rules/cloud-agnostic.mdc` — all cloud I/O via `get_storage_client()`, `get_secret_client()`,
   `GCSEventSink`; `CLOUD_PROVIDER` env var switches provider; test both paths
2. Create `.cursor/rules/dag-enforcement.mdc` — enforce tier boundaries; CI validates `pyproject.toml` deps vs manifest
   `arch_tier`
3. Create `.cursor/rules/ui-service-separation.mdc` — UI code must never live inside a service repo
4. Create `.cursor/rules/mandatory-setup-sh.mdc` — every repo must have `scripts/setup.sh` from SSOT template
5. **ci-manifest-status** — Add `ci_status`, `quality_gate_status`, `coverage_pct`, `bypass_audit_path`,
   `testing_level`, `skipped_gates` to `workspace-manifest.json` for all 57 repos
6. **ci-add-missing-quality-gates** — Add `quality-gates.sh` to 12 repos missing it (see plan for list)
7. **ci-qg-baseline-run** — Run QG + import smoke test on all repos; record pass/fail + coverage % as baseline snapshot
   (do NOT fix failures here — that is Phase 2/3 work)
8. **ci-cloudbuild-audit** — Verify all `cloudbuild.yaml` run tests INSIDE Docker image (not standalone pytest)
9. **ci-aws-parity** — AWS compute stubs, secret naming parity, `buildspec.aws.yaml` for all repos with
   `cloudbuild.yaml`

---

## Done Criteria

- [ ] All 58 repos have `scripts/quickmerge.sh` + `.github/workflows/version-bump.yml` + `scripts/setup.sh`
- [ ] All 58 repos have commit-msg hook; all `pyproject.toml` at `0.x.x`
- [ ] `bash scripts/setup.sh --check` passes on all 58 repos
- [ ] dep-branch clone + Cloud Build feature trigger + GH Action version-bump live
- [ ] `execution-service` has no `visualizer-ui/` or `visualizer-api/`
- [x] `unified-trading-deployment-v3` split into 4 repos (`deployment-service`, `deployment-api`, `deployment-ui`,
      `system-integration-tests`) — DONE 2026-03-03
- [ ] No embedded UI artifacts in any Python service repo
- [ ] `ibkr-gateway-infra/` deleted; Terraform in `deployment-service/infra/`
- [ ] 4 cursor rules created: `cloud-agnostic.mdc`, `dag-enforcement.mdc`, `ui-service-separation.mdc`,
      `mandatory-setup-sh.mdc`
- [ ] `ci_status` fields in `workspace-manifest.json` for all 57 repos
- [ ] QG + import smoke baseline recorded for all repos
- [ ] All 12 repos missing `quality-gates.sh` now have it
- [ ] All `cloudbuild.yaml` run tests inside Docker image
- [ ] `rg` for all old names returns zero hits across all 57 repos

---

## Key Files

- `unified-trading-pm/plans/active/phase1_foundation_prep.plan.md` — full task list
- `unified-trading-pm/workspace-manifest.json` — repo registry
- `unified-trading-pm/scripts/quickmerge.sh` — quickmerge SSOT
- `unified-trading-pm/scripts/setup.sh` — setup.sh SSOT (idempotent dev environment bootstrap; supports `--isolated` for
  standalone repos)
- `unified-trading-pm/scripts/workspace-bootstrap.sh` — full workspace bootstrap for fresh VMs (clones all repos,
  tier-order setup)
- `unified-trading-pm/templates/AGENTS.md` — per-repo caveats template for agents/developers
- `unified-trading-pm/.github/workflows/version-bump.yml` — version-bump SSOT
- `unified-trading-/codex/06-coding-standards/setup-standards.md` — setup.sh documentation (includes isolated mode,
  fresh env, AGENTS.md)
- `unified-trading-codex/00-SSOT-INDEX.md` — canonical SSOT map
- `unified-trading-/codex/06-coding-standards/quality-gates.md` — QG template
- `unified-trading-pm/docs/new-repo-setup.md` — new repo setup guide
