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
status: open # todo 1 (the blocking item) RESOLVED 2026-08-03; todo 3 (design-hardening follow-up) remains open, non-blocking
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, deployment-api, execution-service]
scope: [engineer, admin]
tags: [quality-gates, adapter-contract-regression, shared-host-drift, deployment-api, blocking]
related:
  [
    /plans/archive/2026_07/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md,
    /plans/archive/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-03
author: unknown
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
    scripts/quality_gates/adapter_contract_baseline.yaml,
    deployment-api/deployment_api/services/data_status/mtds_meta.py,
    /plans/archive/2026_07/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md,
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

- [x] ✅ 1. [INFRA] P1. Resolve the stale `deployment-api` checkout on this host — RESOLVED 2026-08-03: by the time
      shipping was retried, the `deployment_api/routes/data_status/_distinct_values.py` dead WIP was gone (someone else
      committed/cleared it) and `git status --branch` in `deployment-api` read
      `## live-defi-rollout...origin/live-defi-rollout` (no longer behind). `find deployment-api -iname mtds_meta.py`
      now finds `./deployment_api/services/data_status/mtds_meta.py` — confirms hypothesis (a): pure host-local checkout
      staleness, not a genuine upstream rename. No baseline change was needed. Verified via a fresh full
      `bash scripts/quality-gates.sh` run from `execution-service`:
      `[5.83/6] ADAPTER CONTRACT-CALL REGRESSION     RATCHET` now reads
      `[check_adapter_contract_regression] OK — 328 baselined file(s) at or above minimum.`, exit code 0. The deferred
      `execution-service` fix (`execution_service/trade_execution/adapters/ibkr_tradfi.py::close()`) then shipped clean
      via quickmerge — `execution-service@4485e0bd`.
- [x] ✅ 2. [INFRA] P2. N/A — `mtds_meta.py` was never actually renamed/removed upstream (see todo 1); this conditional
      baseline-regeneration step does not apply.
- [ ] 3. [INFRA] P3. Consider whether STEP 5.83 should validate against a canonical/fresh state (e.g.
      `git show     origin/<branch>:<path>` for sibling repos) rather than each shipping repo's local, possibly-stale
      sibling checkouts on a shared multi-tenant host — so one host's checkout drift doesn't block shipping from every
      OTHER repo on that same host. Cross-reference
      `/plans/archive/2026_07/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md`
      (ARCHIVED 2026-08-04, all todos done — same STEP 5.83 check, different flake class — timeout-under-contention vs
      missing-file-under-drift; both pointed at the same check being fragile to shared-host state it doesn't fully
      control).

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
- **2026-08-03 (resolved)** — Retried shipping the deferred `execution-service` fix. `deployment-api`'s local checkout
  had caught up to `origin/live-defi-rollout` (the dead WIP file was gone, `mtds_meta.py` present) — todo 1 done, no
  baseline regeneration needed (todo 2 N/A). Full `quality-gates.sh` from `execution-service` passed clean (exit 0, STEP
  5.83 `OK`) and `quickmerge.sh --agent` shipped `execution-service@4485e0bd`. Blocking scope of this issue is closed;
  leaving `status: open` only for the still-outstanding, non-blocking todo 3 design-hardening suggestion.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): KEEP-NA, valid — first audit pass on this
doc (filed today). The sole open item (todo 3, `[INFRA] P3`) is a genuine undecided architecture tradeoff: whether STEP
5.83 should validate against a canonical/fresh state (`git show origin/<branch>:<path>`) instead of each shipping repo's
local, possibly-stale sibling checkouts — adds per-run network/git-show cost vs. accepting host-checkout staleness, no
decision made either way. Checked the cross-referenced sibling
`adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md` (`assigned_vm: planning`,
active): its own open todo is about making the file-walk faster/lighter, a related but distinct concern (speed, not
source-of-truth staleness) — no duplication. Not RECLASSIFY-eligible (the outcome isn't worker-determinable without a
design call). No ARCHIVE.

- **context-scout 2026-08-03**: populated context_scope (4 entries) — added the actual `mtds_meta.py` target file and
  dropped the redundant `unified-trading-pm/` repo prefix on the baseline-yaml entry (this doc's own repo).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — undecided architecture tradeoff, not worker-determinable

**round-11 RECLASSIFY sweep 2026-08-09** (tranche `ci`): KEEP-NA, valid — re-checked against today's accumulated
precedents (IAM self-service, D16 all-repos, S5.1 tiering, AO-dispatch-by-default, escalation-N=3-days,
reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks); none apply. The sole open item (todo
3, `[INFRA] P3`) is still an undecided architecture tradeoff ("Consider whether STEP 5.83 should validate against a
canonical/fresh state... rather than each shipping repo's local, possibly-stale sibling checkouts") — a design call with
no stated decision, not a bounded outcome a worker can execute. No RECLASSIFY, no satellite- extraction. No ARCHIVE.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:45b026ac7efc1ece]: KEEP-NA,
valid — The doc's actual blocking scope (todo 1, deployment-api checkout staleness) was fully resolved same-day
2026-08-03, verified via a clean quality-gates.sh re-run and a shipped quickmerge (execution-service@4485e0bd); todo 2
is N/A (no baseline regen was needed since mtds_meta.py was never actually renamed upstream). status: open is
deliberately retained only for the non-blocking todo 3. The sole remaining open item is explicitly phrased 'Consider
whether STEP 5.83 should validate against a canonical/fresh state... rather than each shipping repo's local,
possibly-stale sibling checkouts' -- an undecided architecture tradeoff (per-run network/git-show cost vs. accepting
host-checkout staleness) with no decision made and no stated done-when.
