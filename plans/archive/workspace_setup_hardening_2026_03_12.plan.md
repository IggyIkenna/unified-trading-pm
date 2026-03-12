---
id: workspace_setup_hardening_2026_03_12
status: done
created: 2026-03-12
priority: P1
repos:
  - unified-trading-pm
  - features-delta-one-service
tags: [workspace, setup, linux, python-version, ci-cd, hardening]
---

# Workspace Setup Hardening (2026-03-12)

## Motivation

A collaborator on a new Linux machine hit a cluster of env-setup failures that were not caught by existing
bootstrap/setup scripts:

1. **Missing editable internal deps** — `features-calendar-service`, `cross-instrument-service`,
   `features-delta-one-service` had internal workspace deps installed from Artifact Registry (wheel), not path-editable.
   Root cause: `[tool.uv.sources.*]` entries were missing and `uv sync` pulled from registry.

2. **pyenv global → deleted Python** — `pyenv global` pointed to `3.13.7` which had been deleted from the filesystem.
   All pyenv shims were broken. Neither bootstrap nor `setup.sh` detected this.

3. **Patch version not enforced** — `setup.sh` only checked `python3.13` (major.minor). If `3.13.7` or `3.13.8` was on
   PATH, setup passed. `3.13.9` was the required patch.

4. **No venv self-heal on broken `pyvenv.cfg`** — When the uv Python cache was wiped, existing `.venv` dirs had a
   `home=` pointing to a deleted path. `uv pip install` would silently use the wrong interpreter or fail cryptically.

5. **OpenBB architectural violation** — `features-delta-one-service` contained `FundamentalsCalculator` making live HTTP
   calls to FMP/Intrinio via OpenBB directly, inside a feature service. This violates the "services never do their own
   external data acquisition" rule (URDI boundary). Also caused `uv lock` failure due to `openbb>=4.0.0` vs
   `ruff==0.15.0` irreconcilable conflict.

## Changes Made

### Phase A — Architectural fix (features-delta-one-service) [DONE]

- **[a1] DONE** Delete `fundamentals.py` and `_openbb_types.py`
- **[a2] DONE** Remove `FundamentalsCalculator` from `__init__.py` (imports, `__all__`, registry)
- **[a3] DONE** Remove `FUNDAMENTALS` from `FeatureGroup` enum in `models.py`
- **[a4] DONE** Remove `fundamentals` assertion from `tests/unit/test_models.py`
- **[a5] DONE** Remove `openbb` optional dep group from `pyproject.toml` (resolves `uv lock` conflict)

> Future: `FundamentalsCalculator` should be re-implemented in `unified-reference-data-interface` (URDI) as a proper
> interface, with the feature service consuming pre-fetched fundamentals from GCS/BigQuery via URDI, not making live
> HTTP calls.

### Phase B — Python version enforcement [DONE]

- **[b1] DONE** `setup.sh`: add `REQUIRED_PYTHON_FULL=3.13.9`; exact patch check in step [1]; warn if Python resolves
  from `~/.local/share/uv/python/`; call `pyenv rehash`
- **[b2] DONE** `setup.sh` step [4]: pyvenv.cfg `home=` self-heal — delete and recreate `.venv` if `home=` dir is
  missing or Python patch version doesn't match
- **[b3] DONE** `workspace-bootstrap.sh`: pyenv health check — detect `pyenv global` pointing to deleted version;
  auto-install `3.13.9` + set global + rehash (or print instructions)
- **[b4] DONE** `workspace-bootstrap.sh`: warn when PYTHON_CMD resolves from uv cache; print all 6 protective env var
  exports

### Phase C — uv.lock resilience [DONE]

- **[c1] DONE** `setup.sh` step [6]: graceful `uv lock` fallback — if `uv lock` fails, set `UV_LOCK_FAILED=true` and
  fall through to direct `uv pip install` in step [8]

### Phase D — CI/CD script hardening [DONE]

- **[d1] DONE** `rollout-quality-gates-unified.py`: add `--skip-missing` flag — repos not cloned locally are a warning
  (not an error); useful on new-machine / partial checkouts
- **[d2] DONE** `run-all-setup.sh`: Phase 0 rollout failures are non-fatal — logged in `ROLLOUT_WARNINGS[]`, setup
  continues; re-run prompt shown
- **[d3] DONE** `run-all-setup.sh`: pre-flight block — checks `.venv-workspace/pyvenv.cfg` `home=` validity; warns if
  `UV_PYTHON_DOWNLOADS != never`
- **[d4] DONE** `validate-internal-editable.py`: distinguish 3 error states:
  - `None` → not installed → "run setup.sh"
  - `""` → from Artifact Registry (wheel) → "add [tool.uv.sources.*] then uv sync"
  - `str` → editable but outside workspace → "editable path outside workspace"
- **[d5] DONE** `run-version-alignment.sh`: step [0.8/4] uv.lock drift detection — check if `pyproject.toml` newer than
  `uv.lock`, or if `uv.lock` has uncommitted changes; warn or `--strict` fatal

### Phase E — Documentation [DONE]

- **[e1] DONE** `CI-CD-FLOW.md`: Linux prerequisites section with `~/.bashrc` snippet and explanation of all 6 env vars
  (`PYENV_ROOT`, `PATH`, `UV_PYTHON`, `UV_PYTHON_PREFERENCE`, `UV_PYTHON_DOWNLOADS`, `PYENV_VIRTUALENV_DISABLE_PROMPT`)
- **[e2] DONE** `workspace-bootstrap.sh` final summary: Linux/pyenv shell config block

### Phase F — git fetch drift report [DONE]

- **[f1] DONE** `run-all-setup.sh --sync-git`: `git fetch origin` in all repos (parallel), then report which branches
  are behind/diverged from their remote tracking ref. Read-only — never merges, never touches working tree. Safe on any
  branch topology. Diverged repos (feature branches with local commits) are reported separately from cleanly-behind
  repos. Setup continues with current local state regardless.

## Affected Files

| File                                                                                     | Change                                                          |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `features-delta-one-service/features_delta_one_service/app/calculators/fundamentals.py`  | DELETED                                                         |
| `features-delta-one-service/features_delta_one_service/app/calculators/_openbb_types.py` | DELETED                                                         |
| `features-delta-one-service/features_delta_one_service/app/calculators/__init__.py`      | Remove FundamentalsCalculator                                   |
| `features-delta-one-service/features_delta_one_service/models.py`                        | Remove FUNDAMENTALS enum                                        |
| `features-delta-one-service/tests/unit/test_models.py`                                   | Remove fundamentals assertion                                   |
| `features-delta-one-service/pyproject.toml`                                              | Remove openbb optional dep                                      |
| `unified-trading-pm/scripts/setup.sh`                                                    | Python patch enforcement + venv self-heal + uv lock fallback    |
| `unified-trading-pm/scripts/workspace/workspace-bootstrap.sh`                            | pyenv health check + Linux env vars                             |
| `unified-trading-pm/scripts/repo-management/run-all-setup.sh`                            | Pre-flight checks + non-fatal Phase 0 + --sync-git fetch/report |
| `unified-trading-pm/scripts/repo-management/run-version-alignment.sh`                    | Step [0.8] uv.lock drift                                        |
| `unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py`                | --skip-missing flag                                             |
| `unified-trading-pm/scripts/manifest/validate-internal-editable.py`                      | 3-state error messages                                          |
| `unified-trading-pm/docs/repo-management/CI-CD-FLOW.md`                                  | Linux prerequisites section                                     |
