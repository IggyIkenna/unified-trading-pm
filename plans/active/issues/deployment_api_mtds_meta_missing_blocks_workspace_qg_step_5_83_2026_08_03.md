---
doc_type: issue
title:
  "deployment-api local checkout missing mtds_meta.py (157 commits behind) fails workspace-wide QG STEP 5.83 for every
  repo on this host"
summary: >-
  While shipping an execution-service fix (ibkr_tradfi.py close() bare-except narrowing), `bash
  scripts/quality-gates.sh` STEP [5.83/6] ADAPTER CONTRACT-CALL REGRESSION RATCHET failed with
  "deployment-api/deployment_api/services/data_status/mtds_meta.py: 0 contract calls < baseline 5 (file missing or
  renamed)". Root cause: the local `deployment-api` sibling checkout on this shared host is 157 commits behind
  `origin/live-defi-rollout` and does not contain `mtds_meta.py` at all (zero git history for that path, `git log
  --follow` empty) — while `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` still expects it at
  count>=5. STEP 5.83 scans `${WORKSPACE_ROOT}` (all sibling repo checkouts on the SAME host), so this blocks
  `quality-gates.sh` — and therefore `quickmerge.sh`, which requires a fully green run — for EVERY repo shipped from
  this host until deployment-api's checkout is caught up. A safe `git pull --ff-only` in deployment-api was attempted as
  a non-destructive diagnostic and refused cleanly (another agent's uncommitted, ~94-hour-old modification to
  `deployment_api/routes/data_status/_distinct_values.py` would be overwritten by the incoming 157 commits) — left
  untouched per the multi-agent safety HARD RULE (never discard/overwrite another agent's WIP).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, deployment-api, execution-service]
scope: [engineer, admin]
tags: [quality-gates, adapter-contract-regression, shared-host-drift, deployment-api, blocking]
related:
  [
    /plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md,
    /plans/archive/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-08-03 while shipping a targeted fix in execution-service
  (execution_service/trade_execution/adapters/ibkr_tradfi.py close()). Two consecutive full `bash
  scripts/quality-gates.sh` runs, both green through the repo's own [6/6] steps ("ALL QUALITY GATES PASSED"), both then
  hard-failed at the later workspace-wide [5.83/6] step for the same reason. Confirmed unrelated to the shipped diff
  (deployment-api was never touched by either edit). Confirmed via `find deployment-api -iname mtds_meta.py` (no hits)
  and `git log --oneline --follow -- deployment_api/services/ data_status/mtds_meta.py` (empty) in the local
  deployment-api checkout; `git status --branch` there showed `behind 157`. Diagnostic `git pull --ff-only` in
  deployment-api (non-destructive, read-first via `git fetch`) was attempted and refused cleanly by git itself (would
  overwrite another agent's uncommitted, ~94h-old change to `deployment_api/routes/data_status/_distinct_values.py`) —
  no further action taken there, per HARD RULE against touching another agent's WIP.
context_scope:
  [
    scripts/qg/no_adapter_contract_regression.sh,
    unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml,
    /plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md,
  ]
---

# deployment-api local checkout missing mtds_meta.py blocks workspace-wide QG STEP 5.83 for every repo shipped from this host

## What was found

Shipping an unrelated, scoped fix in `execution-service`
(`execution_service/trade_execution/adapters/ibkr_tradfi.py::close()` — narrowing a bare `except BaseException:` to
`except ConnectionError:` and bumping the log level `debug`→`warning`), `bash scripts/quality-gates.sh` run from
`execution-service` passed its own repo-scoped [1-6/6] gates cleanly (`✅ ALL QUALITY GATES PASSED`, sentinel written),
then failed later in the same script run at the workspace-wide peripheral step:

```
── [5.83/6] ADAPTER CONTRACT-CALL REGRESSION RATCHET ──
[FAIL] deployment-api/deployment_api/services/data_status/mtds_meta.py: 0 contract calls < baseline 5 (file missing or
renamed). Patterns tracked: classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty |
record_zero_rows | record_failed | record_catalog_unavailable | record_shard_failure.
[check_adapter_contract_regression] 1 file(s) regressed below baseline.
```

Overall script exit code: 1. Reproduced identically on two separate full runs (before and after a test-file fix made in
the same session), confirming it is not caused by, or sensitive to, the execution-service diff being shipped.

Root cause isolated in the local `deployment-api` sibling checkout on this shared host:

- `find deployment-api -iname mtds_meta.py` → no hits anywhere in the tree.
- `git log --oneline --follow -- deployment_api/services/data_status/mtds_meta.py` → empty (no history reachable from
  this checkout's HEAD at all, not just "recently deleted").
- `git status --branch` in deployment-api → `## live-defi-rollout...origin/live-defi-rollout [behind 157]`.
- `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` still carries
  `deployment-api/deployment_api/services/data_status/mtds_meta.py: count: 5` alongside sibling entries
  (`coverage_metrics.py: count: 1`, `sports_helpers.py: ...`) that DO exist in the local checkout — so this is not a
  wholesale-missing-directory issue, just this one baselined path.

STEP 5.83 (`no_adapter_contract_regression.sh`) scans `${WORKSPACE_ROOT}` — i.e. every sibling repo checked out
alongside the repo whose `quality-gates.sh` is running, on the SAME host — not a fresh/canonical clone. That means
**any** `quality-gates.sh` run from **any** repo on this specific host will hit this same failure until the local
`deployment-api` checkout is brought forward, independent of what the shipping repo's own diff touches.

A non-destructive diagnostic was run to see if this was a trivial "just needs a pull" situation: `git fetch` (read only)
confirmed 157 commits behind; `git pull --ff-only` was then attempted and refused cleanly by git itself:

```
error: Your local changes to the following files would be overwritten by merge:
	deployment_api/routes/data_status/_distinct_values.py
Please commit your changes or stash them before you merge.
```

That modified file is another agent's uncommitted WIP (mtime ~94 hours old at time of check — a dead/stale claim by the
SUB_AGENT_MANDATORY_RULES.md liveness heuristic, but still not mine to stash/discard/commit on someone else's behalf
without knowing what it is). No further action was taken on `deployment-api` — left exactly as found.

## Why this matters

- Blocks `quickmerge.sh` for every repo on this host (quickmerge requires a fully green `quality-gates.sh` exit code;
  this workspace-wide peripheral step is bundled into that same script run and hard-fails the whole thing).
- Likely a **host-local staleness** issue rather than a genuine cross-repo content regression: `mtds_meta.py` was
  probably renamed/split as part of ongoing `deployment-api` `data_status/` refactor work upstream (a sibling `mtds.py`
  exists with active recent history — `feat(data-status): ...` commits), and this host's checkout simply hasn't caught
  up. If so, either (a) a routine `git pull --ff-only` once the dirty file is resolved will make it disappear, or (b) if
  `origin/live-defi-rollout` genuinely no longer has `mtds_meta.py` under that name, the baseline YAML itself needs
  updating (`--regenerate-baseline`, per the script's own guidance, only after confirming the rename is a legitimate,
  intentional refactor and not a lost regression).
- Not attributable to, or fixable from within, any single repo's own scoped diff — it is a workspace/host
  environment-state problem.

## Todos

- [ ] 1. [INFRA] P1. Resolve the stale `deployment-api` checkout on this host: identify/contact the owner of the dead
      WIP on `deployment_api/routes/data_status/_distinct_values.py` (or confirm it's safe to stash-by-name per the
      liveness-gated inherited-dirty-WIP rule), then `git pull --ff-only` to bring the checkout current. Verify
      afterward whether `mtds_meta.py` reappears (rename false-positive, self-resolves) or is genuinely gone upstream
      (needs baseline regeneration).
- [ ] 2. [INFRA] P2. If `mtds_meta.py` is confirmed genuinely renamed/split upstream (not a local-staleness artifact),
      regenerate `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` for the new path(s) via the
      script's own `--regenerate-baseline` flag, citing the specific upstream commit that performed the rename as
      justification (never regenerate blind to mask a real regression).
- [ ] 3. [INFRA] P3. Consider whether STEP 5.83 should validate against a canonical/fresh state (e.g.
      `git show     origin/<branch>:<path>` for sibling repos) rather than each shipping repo's local, possibly-stale
      sibling checkouts on a shared multi-tenant host — so one host's checkout drift doesn't block shipping from every
      OTHER repo on that same host. Cross-reference
      `/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md` (same
      STEP 5.83 check, different flake class — timeout-under-contention vs missing-file-under-drift; both point at the
      same check being fragile to shared-host state it doesn't fully control).

## Progress Log

- **2026-08-03** — Filed while shipping `execution_service/trade_execution/adapters/ibkr_tradfi.py::close()` exception
  narrowing (tradfi_adapter_dead_code_fallback_audit_2026_07_25.md Finding E-3). execution-service's own fix/tests/QG
  are complete and correct (both files diffed cleanly, targeted test updated to match the narrower except clause,
  repo-scoped [1-6/6] QG green); shipping via quickmerge is blocked pending this cross-repo item. Did not attempt to fix
  `deployment-api` beyond the safe, non-destructive `git fetch`/`git pull --ff-only` diagnostic (refused cleanly, no
  data touched) — out of scope for the delegated task and would require handling another agent's uncommitted WIP.
- **2026-08-03 (corroboration)** — Hit byte-identical while shipping an unrelated `instruments-service` fix (same parent
  audit's Finding I-1: 3 unlogged silent-fallback catch blocks in
  `reference_data/adapters/tradfi/databento/{adapter.py,sessions.py}`). Two full
  `bash scripts/quality-gates.sh --no-fix` runs from `instruments-service` both passed the repo's own [0-6/6] gates
  clean (tests: 5159 passed) then hard-failed at the same `[5.70/6] IS-MTDS CONTRACT INTEGRITY` /
  `check_adapter_contract_regression` step on the identical
  `deployment-api/deployment_api/services/data_status/mtds_meta.py` line. Confirmed via `quickmerge.sh --agent`: STAGE
  0.4 auto-pulled 1 new origin commit mid-run, invalidating the Pass-1 sentinel, forcing a genuine Pass-2 regate that
  hit the same failure and correctly refused to ship ("❌ Re-gate FAILED against the current tree — this is a REAL
  failure, not a lost race") — no commit/push happened, working tree left clean of any partial state. This confirms the
  block is host-wide and NOT specific to execution-service's diff or repo. instruments-service's own code change is
  complete/correct and shipping is deferred until this INFRA item (todo 1) resolves. Did not touch `deployment-api`.
