# Plan: Composite Action — Quality Gates Inheritance

**Status:** ACTIVE **Priority:** P2 **Created:** 2026-03-12 **Owner:** Platform

## Problem

Each of ~52 service repos has a ~100-line `quality-gates.yml` that is mostly boilerplate. Currently propagated by
`rollout-quality-gates-ci-workflows.py` (one-shot script) — drift accumulates between rollouts.

There is also a broken reference: service repos use
`IggyIkenna/unified-trading-pm/.github/actions/setup-python-tools@main` but `.github/actions/` does not exist in PM.

## Goal

- Centralise stable boilerplate into composite GHA actions in PM
- Per-repo workflows become thin callers (10–20 lines)
- Changes in PM actions take effect for all repos instantly on next CI run
- No more rollout scripts for boilerplate changes

## Architecture

### Actions to create in `unified-trading-pm/.github/actions/`

| Action                          | Replaces                                                                                  |
| ------------------------------- | ----------------------------------------------------------------------------------------- |
| `setup-python-tools/action.yml` | Set up Python, install uv, install ruff/basedpyright/pytest tools, add tools to PATH      |
| `run-quality-gates/action.yml`  | Run `bash scripts/quality-gates.sh --no-fix` with correct env, PATH, and record CI status |

### What stays per-repo

The dep-clone step (each repo clones its own library deps) cannot be centralised because dep lists differ per repo. This
stays in each repo's workflow.

### Target per-repo quality-gates.yml shape (~20 lines)

```yaml
name: Quality Gates
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python CI tools
        uses: IggyIkenna/unified-trading-pm/.github/actions/setup-python-tools@main
        with:
          python-version: "3.13.9"

      - name: Checkout dependencies
        env:
          GH_PAT: ${{ secrets.GH_PAT }}
          DEP_BRANCH: ${{ github.head_ref || github.ref_name }}
        run: |
          # per-repo dep clone (kept here — varies per repo)
          ...

      - name: Run quality gates
        uses: IggyIkenna/unified-trading-pm/.github/actions/run-quality-gates@main
        env:
          GH_PAT: ${{ secrets.GH_PAT }}
```

## Implementation Steps

### P0 — Create `setup-python-tools` action (fixes broken reference)

- [ ] Create `.github/actions/setup-python-tools/action.yml`
- Inputs: `python-version` (default: `"3.13.9"`)
- Steps: `actions/setup-python@v5`, install uv, cache tools (rg, shellcheck, bats, actionlint), install tools, add to
  PATH
- Test: push to PM main, verify alerting-service CI uses it successfully

### P1 — Create `run-quality-gates` action

- [ ] Create `.github/actions/run-quality-gates/action.yml`
- Steps: install dev deps (`uv sync --extra dev`), run `quality-gates.sh --no-fix`, record CI status on push to main
- Env: `CLOUD_MOCK_MODE=true`, `CLOUD_PROVIDER=local`, `GCP_PROJECT_ID=test-project`
- The `uv sync` step needs the `.venv` from a prior install-deps step OR the action installs deps itself (preferred —
  keeps action self-contained)

### P2 — Rollout thin callers to all repos

- [ ] Create `rollout-composite-action-workflows.py` — generates thin per-repo `quality-gates.yml` from a Jinja/text
      template
- [ ] Template: `scripts/propagation/templates/quality-gates-composite.yml` (with `{{SERVICE_NAME}}` and
      `{{DEP_CLONE_BLOCK}}` placeholders)
- [ ] The dep-clone block for each repo is read from `workspace-manifest.json` `local_deps` field (already present)
- [ ] Dry-run against all 52 repos before applying
- [ ] Stage and commit all 52 repos' updated workflows in a single PR per repo using quickmerge

### P3 — Deprecate rollout-quality-gates-ci-workflows.py

- [ ] Once all repos use composite actions, the rollout script is only needed for legacy repos
- [ ] Add deprecation comment to the script
- [ ] Remove from quality gates checks

## Testing Plan

1. Push `setup-python-tools` to PM main
2. Open a PR in `alerting-service` — verify CI uses the composite action
3. Verify basedpyright version, Python version, tool versions are all correct
4. Run rollout dry-run across all 52 repos
5. Apply to 3 pilot repos (alerting-service, execution-service, unified-trading-library), validate CI passes
6. Apply to all remaining repos
7. Run `python3 check-workflow-tokens.py --workspace` — should be 0 violations

## Risks

- Composite actions load from `main` of PM — a bad push to PM breaks ALL repos simultaneously. Mitigation: PM has its
  own quality gates; consider using SHA-pinned refs for stability (e.g. `@v1` tag on PM)
- The dep-clone block per repo requires accurate `local_deps` in `workspace-manifest.json` — audit before rollout

## Notes

- `setup-python-tools` already referenced by service repos but doesn't exist — P0 fix is urgent (though CI doesn't error
  because the reference is in a step that may be skipped or repos have fallback PATH install)
- `check-workflow-tokens.py --workspace` is the acceptance test for GH_PAT correctness post-rollout
