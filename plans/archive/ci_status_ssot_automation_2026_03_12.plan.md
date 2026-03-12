---
id: ci_status_ssot_automation_2026_03_12
status: done
created: 2026-03-12
priority: P2
repos:
  - unified-trading-pm
  - all-python-repos
tags: [ci-cd, manifest, automation, quality-gates, observability]
---

# CI Status SSOT Automation (2026-03-12)

## Motivation

`workspace-manifest.json` `ci_status` field was either manually maintained or set inconsistently by `run-qg-baseline.sh`
(using `PASSING`/`FAILING` strings inconsistent with the manually-set `BASELINE_RECORDED`). 46/65 repos had a status;
the rest were `BASELINE_PENDING`, `HAS_QG`, `NOT_CONFIGURED`, `NO_QG`, or `FAILING` — with no automated path to keep
them current. Every CI run was silent as far as the manifest was concerned.

## Changes Made

### Phase A — PM-side handler [DONE]

- **[a1] DONE** `scripts/ci/record-ci-status.py` — atomic writer: takes `--repo`, `--status`, `--sha`; updates
  `ci_status` + `ci_last_sha` in `workspace-manifest.json`
- **[a2] DONE** `.github/workflows/ci-status-record.yml` — new PM workflow: handles
  `repository_dispatch: [ci-status-update]`; calls `record-ci-status.py`; commits to manifest. Uses
  `concurrency: group: manifest-ci-status` (cancel-in-progress: false) to serialise concurrent dispatches without
  dropping any.

### Phase B — Per-repo injection [DONE]

- **[b1] DONE** `rollout-quality-gates-ci-workflows.py` — extended with `_ensure_ci_status_step()`: injects "Record CI
  status" step after "Run quality gates" in every repo's `quality-gates.yml`. Step fires `ci-status-update` dispatch to
  PM on every push to `main` (`if: always()` — captures both pass and fail). `STATUS` is derived from
  `${{ job.status }}`.
- **[b2] DONE** Propagated to all 52 eligible repos (15 skipped: 13 UI-only + 2 manually excluded).

### Phase C — Local baseline tool [DONE]

- **[c1] DONE** `run-qg-baseline.sh` — updated to call `record-ci-status.py` instead of inline Python for consistency;
  removed `quality_gate_status` field (redundant with `ci_status`).

## Flow

```
repo quality-gates.yml (push to main)
  └─ "Run quality gates" passes or fails
  └─ "Record CI status" (if: always)
       └─ curl → PM repository_dispatch: ci-status-update {repo, status, sha}
            └─ ci-status-record.yml
                 └─ record-ci-status.py
                      └─ workspace-manifest.json ci_status = PASSING|FAILING
                           └─ git commit → main
```

## Affected Files

| File                                                                           | Change                                        |
| ------------------------------------------------------------------------------ | --------------------------------------------- |
| `unified-trading-pm/scripts/ci/record-ci-status.py`                            | NEW — manifest writer                         |
| `unified-trading-pm/.github/workflows/ci-status-record.yml`                    | NEW — PM dispatch handler                     |
| `unified-trading-pm/scripts/propagation/rollout-quality-gates-ci-workflows.py` | Extended with fix 4: ci status step injection |
| `unified-trading-pm/scripts/run-qg-baseline.sh`                                | Updated to use record-ci-status.py            |
| `<52 repos>/.github/workflows/quality-gates.yml`                               | "Record CI status" step injected              |
