---
doc_type: issue
title:
  "Global QG pytest --timeout=60 (base-library.sh) flakes on GH Actions CI — 2nd confirmed instance of the
  60s-wall-clock-under-contention bug class, this time on a hosted CI runner, not just local shared-host"
summary: >-
  unified-api-contracts' quality-gates-v2 went RED on live-defi-rollout (commit f50defe3, an unrelated ASTER-collateral
  registry fix) because tests/test_cassette_offline_check.py::test_vcr_cassette_interactions_is_list[bybit/ticker.yaml]
  hit `Failed: Timeout (>60.0s) from pytest-timeout.` — 1 of 12125 tests. That test only parses a 2KB, pure-offline YAML
  fixture (docstring: "run without any live network calls"); isolated re-run measured 0.04s. The 60s budget comes from a
  HARDCODED, non-overridable `--timeout=60` in the SHARED `unified-trading-pm/scripts/quality-gates-base/
  base-library.sh` PARGS line (used by every repo's pytest slice, unlike the two sibling knobs on the same line block —
  PYTEST_WORKERS/PYTEST_UNIT_DIR — which ARE env-overridable). Two subsequent LDR gate runs on later commits came back
  green (via content-sentinel skip). This is the same bug CLASS as
  `/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md` (a fixed
  60s `run_timeout` wall-clock wrapper flaking under shared-host I/O contention) — but that issue's own todo 3 left open
  "does GH Actions CI see the same contention profile, or is this slot-worktree-local only?" This occurrence answers it:
  YES, the pattern also fires on GH Actions-hosted `quality-gates-v2` runs, not only local multi-slot hosts — likely via
  intra-job `pytest-xdist -n auto` worker contention (CI branch of the same PARGS line auto-scales workers to the
  runner's core count) rather than cross-job host sharing.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist]
related: [/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md]
created: 2026-07-29
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
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
  cicd-role escalation agt-fa86c9 (WALL_TYPE=ldr_qg_failure), triaging GH Actions run
  https://github.com/IggyIkenna/unified-api-contracts/actions/runs/30424080892 (2026-07-29T05:05:52Z, 48m56s,
  headSha=f50defe3bf3c41dd8c6005a328a9387e7b2961fb). Diagnosed via job-log grep (qg_red_reason=pytest, single FAILED
  line), reading tests/test_cassette_offline_check.py (docstring confirms no-network), file size (2019 bytes / 50
  lines), an isolated local re-run of the exact test id (0.04s, PASSED), and grep of
  unified-trading-pm/scripts/quality-gates-base/base-library.sh line 391 for the literal `--timeout=60`. Confirmed the
  LDR gate is currently green (runs 30429850246 and 30441849098, both content-sentinel skips on later commits
  d4045838/62d3aa03/3a8c845b — unrelated fixes from a different slot) — no unified-api-contracts code/test change was
  needed for THIS occurrence; filed as its own issue per findings-triage (outside my escalation's repo scope: the fix
  location is the shared PM script, not unified-api-contracts).
---

# Global QG `--timeout=60` (base-library.sh) flakes on GH Actions CI, not just local shared hosts

## What was found

While resolving `ldr_qg_failure` escalation `agt-fa86c9` for `unified-api-contracts` (LDR RED at commit `f50defe3`,
"fix(registry): correct ASTER collateral haircuts + add BTC/ETH rows"), the failing GH Actions run (`30424080892`,
`QG slice (tests)` job) showed:

```
FAILED tests/test_cassette_offline_check.py::test_vcr_cassette_interactions_is_list[bybit/ticker.yaml] - Failed: Timeout (>60.0s) from pytest-timeout.
= 1 failed, 12125 passed, 741 skipped, 5 xfailed, 2 warnings in 686.98s (0:11:26) =
```

One test, out of 12125, timed out. `test_cassette_offline_check.py`'s own module docstring: "Canary offline check —
validate ALL cassette YAML structure without network calls... These checks run without any live network calls." The
specific fixture (`unified_api_contracts/external/bybit/mocks/ticker.yaml`) is 2019 bytes / 50 lines. Re-running just
that test id in isolation (same tree, same worktree, moments later):

```
tests/test_cassette_offline_check.py::test_vcr_cassette_interactions_is_list[bybit/ticker.yaml] PASSED [100%]
1 passed, 157 deselected in 0.04s
```

0.04s vs a 60s budget — a >1000x margin. There is no plausible code path in this test (pure `yaml.load` via the C
`CSafeLoader` + an `isinstance` check) that legitimately takes anywhere near 60s on a 2KB file. The commit that
triggered the escalation (`f50defe3`) touched only `unified_api_contracts/registry/venue_collateral.py` and its own unit
test — an unrelated subsystem. This was not a regression; it was a scheduling-induced wall-clock timeout.

**Root cause**: `unified-trading-pm/scripts/quality-gates-base/base-library.sh:391`:

```bash
PARGS="-n ${_PYTEST_N} --timeout=60 -q -r a --tb=short --no-header --durations=25"
```

`--timeout=60` is a literal, hardcoded value with **no env-var override** — unlike its two neighbors on the surrounding
lines, `PYTEST_WORKERS` (line 384: "Explicit PYTEST_WORKERS wins") and `PYTEST_UNIT_DIR` (line 395,
`"${PYTEST_UNIT_DIR:-tests/unit/}"`), both of which follow the established per-repo-override pattern this repo already
uses elsewhere in the same file. This flag is applied to **every test, in every repo**, via the shared library every
`scripts/quality-gates.sh` sources.

## Why this matters / relation to the precedent issue

This is the same bug CLASS as
`/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md`: a fixed 60s
wall-clock timeout that fires under contention regardless of whether the underlying check would have passed, on a
completely unrelated diff. That issue diagnosed the mechanism as **shared-host I/O contention** (3-7 concurrent
`quality-gates.sh` processes across slots on the same physical host) and fixed it by raising the specific script's
`run_timeout` 60→300 in each of 4 repos' own `scripts/quality-gates.sh` copies (a repo-local, low-blast-radius change
each time, since `no_adapter_contract_regression.sh`'s wrapper is duplicated per-repo, not shared).

That issue's todo 3 explicitly left open: _"If GH Actions / promote-PR CI also runs this same QG step, confirm whether
CI runners see the same contention profile — if CI is single-tenant per run, the flake may be slot-worktree-specific
only."_ **This occurrence answers that question**: the failing run here was a hosted GH Actions `quality-gates-v2` job
(`30424080892`), not a local slot — so the 60s-timeout-under-contention pattern is NOT limited to local multi-slot
shared hosts. The likely mechanism differs slightly: `base-library.sh` sets `_PYTEST_N="auto"` when `GITHUB_ACTIONS` is
set (line 386-387), so GH Actions runs `pytest-xdist -n auto` — one worker per detected core, all sharing the runner's
CPU/IO. With 12125 tests fanned across `auto` workers, a genuinely-instant test can still be **descheduled** past the
60s wall-clock budget if a sibling worker on the same runner is CPU/IO-heavy at that moment — contention from sibling
xdist workers within the SAME job, rather than sibling jobs/slots on a shared host. Either way, the fix philosophy from
the precedent issue applies unchanged: raising (or making overridable) a **wall-clock** timeout that guards against
genuine hangs, to absorb realistic scheduling variance, is not "weakening" the check — the check's actual assertion
(cassette structural validity) is untouched; only the unrelated deadline is adjusted.

Unlike the precedent issue, the fix location here is **not** repo-local — `--timeout=60` lives once, in the SHARED
`unified-trading-pm/scripts/quality-gates-base/base-library.sh`, sourced by every repo's `scripts/quality-gates.sh`.
Editing it changes the pytest wall-clock budget workspace-wide in one commit — out of scope for a single-repo
`ldr_qg_failure` escalation response (which is bounded to fixing `$REPO` on its merits), and warranting the same
deliberate, tracked treatment the precedent issue gave its own (smaller-blast-radius) fix.

## Current state of the triggering wall

No unified-api-contracts action was needed for this specific occurrence: `live-defi-rollout` is already green — two
subsequent `quality-gates-v2` runs (`30429850246`, `30441849098`) both succeeded (content-sentinel skip: the tree state
after commits `d4045838`/`62d3aa03`/`3a8c845b`, from an unrelated slot's work, was already locally QG-verified before
those commits landed). The escalation's own repo-blocker list (`GET /api/repo-blockers`) had no open entry for
`unified-api-contracts` at investigation time.

## Todos

- [x] ✅ 1. [INFRA] P2. In `unified-trading-pm/scripts/quality-gates-base/base-library.sh`, make the pytest `--timeout=`
      value follow the same override pattern as its `PYTEST_WORKERS`/`PYTEST_UNIT_DIR` neighbors on the same line block
      — e.g. `PYTEST_TIMEOUT_SECONDS="${PYTEST_TIMEOUT_SECONDS:-60}"` feeding `--timeout=${PYTEST_TIMEOUT_SECONDS}` —
      AND raise the workspace default to a value that absorbs realistic GH-Actions-xdist + shared-host scheduling
      variance (120-180s, per the precedent issue's 60→300 for the analogous `run_timeout`) without meaningfully
      delaying detection of a genuinely hung test. Verify on a real GH Actions `quality-gates-v2` run (not just local)
      since that is where this instance actually fired. — unified-trading-pm@cedef544b: added
      `PYTEST_TIMEOUT_SECONDS="${PYTEST_TIMEOUT_SECONDS:-150}"` feeding `--timeout=${PYTEST_TIMEOUT_SECONDS}` at
      `scripts/quality-gates-base/base-library.sh:394-395` (default raised 60→150) + documented the new override in the
      file's header comment block. GH-Actions verification is the separate todo 3 (watch the next 5-10
      `quality-gates-v2` runs), not re-done here.
- [x] ✅ 2a. [INFRA] P3. Grep the shared `scripts/quality-gates-base/base-*.sh` scripts specifically for other
      `--timeout=`/PARGS copies of this exact pytest-wall-clock pattern — **answered: it recurs.**
      `base-service.sh` (sourced by every SERVICE repo, e.g. instruments-service, execution-service,
      features-service, market-tick-data-service, deployment-api, ~20 repos total — every repo whose
      `scripts/quality-gates.sh` sources `base-service.sh` rather than `base-library.sh`) had its OWN separate copy
      of the identical PARGS line (`--timeout=${PYTEST_TIMEOUT:-60}`, line ~799) that todo 1's `cedef544b` fix never
      touched (it only edited `base-library.sh`, used by library-type repos). Confirmed via a bounded grep of all 4
      `base-*.sh` files (`base-codex.sh`, `base-library.sh`, `base-service.sh`, `base-ui.sh`) — exactly these 2 had
      the pattern, `base-codex.sh`/`base-ui.sh` don't run pytest this way. Discovered while resolving `ldr_qg_failure`
      escalation `agt-41a9d1` for `instruments-service` promotion PR #1026 (run 30519066074, `Failed: Timeout
      (>60.0s)` — the literal `60.0s`, not `150.0s`, in the failure message was the tell that the base-library.sh fix
      hadn't reached this codepath). Fixed: `unified-trading-pm@<see quickmerge output>` bumps
      `base-service.sh`'s `${PYTEST_TIMEOUT:-60}` → `${PYTEST_TIMEOUT:-150}` (kept the existing `PYTEST_TIMEOUT` var
      name, NOT renamed to `PYTEST_TIMEOUT_SECONDS`, since it is already a live documented override — see
      `plans/active/sports_consolidated_native_ao_extract_2026_07_25.md`).
- [ ] 2b. [INFRA] P3. Broader remaining scope of the original todo 2: a fleet-wide sweep of every INDIVIDUAL repo's
      OWN `scripts/quality-gates.sh` (not just the 4 shared `base-*.sh` files, which 2a already covered) for
      repo-local `run_timeout <N>` calls guarding custom STEP-5.6x-style checks that similarly lack an env-var
      override — e.g. instruments-service's own script has several (`run_timeout 30/60/300 ...` for codex-compliance
      checks). Not yet swept; 2a only closes the shared-script half of the original question.
- [ ] 3. [INFRA] P3. Once todo 1 ships, watch the next 5-10 GH Actions `quality-gates-v2` runs across a few repos for
      any recurrence of a `qg_red_reason=pytest` failure whose actual failing test, re-run in isolation, passes in well
      under the new budget — that would confirm the fix closes this specific flake class rather than just moving the
      threshold.

## Progress Log

- **2026-07-29** — Filed while resolving `ldr_qg_failure` escalation `agt-fa86c9` for `unified-api-contracts`
  (`f50defe3`). Diagnosis root-caused to `base-library.sh:391`'s hardcoded `--timeout=60`; confirmed via isolated 0.04s
  re-run of the specific failing test id. Did not fix inline — the fix location (`unified-trading-pm`'s shared QG
  library) is outside the escalation's target repo (`unified-api-contracts`) and workspace-wide in blast radius, so it
  needs the same dedicated, tracked treatment the precedent issue gave its narrower fix. No code change needed on
  `unified-api-contracts` itself — LDR was already green by the time of investigation (content-sentinel-verified).
- **2026-07-29** — 3rd confirmed instance, 2nd repo: `ldr_qg_failure` escalation `agt-218b27` for `deployment-api`
  promotion PR #425 (`quality-gates-v2` run `30430147179`, `QG slice (tests)` job). Failing test:
  `tests/unit/test_dockerfile_zombie_watchdog_packaging.py::TestVmZombieWatchdogPackaging::test_api_stage_copies_recovery_actuator_package`
  — a pure Dockerfile-text-parsing test (`Path.read_text()` + `str.index()` on a small file, no I/O, no subprocess, no
  network) hit `Failed: Timeout (>60.0s) from pytest-timeout.`, which crashed the pytest-xdist worker
  (`worker_internal_error` → `AssertionError` in the controller's `worker_workerfinished`), failing the whole slice
  despite `2709 passed, 9 skipped` in the same run. Same mechanism as the precedent entries: no legitimate code path in
  this test can take anywhere near 60s: the wall-clock deadline fired under xdist-worker scheduling contention, not a
  real hang. No deployment-api code/test fix applied — confirmed no action was needed: by the time of investigation (~5h
  after the original escalation), the standard 15-min LDR→main promotion cycle had already regenerated fresh promotion
  PRs (#426 closed unmerged, #427 merged 09:16:47Z, #428 merged 12:52:19Z) and `quality-gates-v2` on `live-defi-rollout`
  is green on the latest run (`30456732896`, success). This is exactly the precedent's own outcome ("no action needed...
  LDR already green on a later run") — strengthens todo 3's evidence that the flake is transient and self-clears on
  retry, and that a 2nd repo (`deployment-api`, self-hosted-runner-backed per `8561af1`'s revert commit in its own
  history) reproduces the same class independent of runner type. Still unresolved: todo 1 (the actual
  `PYTEST_TIMEOUT_SECONDS` override + raised default) has not landed — every future occurrence still costs a full ~20min
  CI cycle + a cicd-role escalation until it does.
- **2026-07-30** — Todo 1 shipped: `unified-trading-pm@cedef544b` (`scripts/quality-gates-base/base-library.sh`) adds
  `PYTEST_TIMEOUT_SECONDS="${PYTEST_TIMEOUT_SECONDS:-150}"` feeding `--timeout=${PYTEST_TIMEOUT_SECONDS}`, matching the
  `PYTEST_WORKERS`/`PYTEST_UNIT_DIR` override pattern, default raised 60→150s. Local `quality-gates.sh` green (sentinel
  verified at HEAD), shipped via `quickmerge --agent --files`. Todos 2 (workspace-wide hardcoded-timeout sweep) and 3
  (watch next 5-10 GH Actions `quality-gates-v2` runs for recurrence) remain open, unassigned to this task.
- **2026-07-30 ~07:00Z (cicd escalation `agt-41a9d1`, slot 1) — todo 1's fix confirmed INCOMPLETE, 4th confirmed
  instance, `instruments-service` (2nd repo)**: dispatched for `ldr_qg_failure` on `instruments-service` promotion PR
  #1026 (LDR→main, head `5c1c3ccb`, run `30519066074`). `QG slice (tests)` failed with the exact same signature as
  every prior entry: `Failed: Timeout (>60.0s) from pytest-timeout.` → xdist `worker_internal_error` →
  `RuntimeError: Unexpectedly no active workers available`, despite `1375 passed, 2 warnings in 161.31s` in the same
  run. The literal `60.0s` (not `150.0s`) was the tell that todo 1's fix hadn't reached this codepath — confirmed
  `cedef544b` (05:39:50Z) WAS already an ancestor of the `unified-trading-pm` HEAD this run's "Clone unified-trading-pm
  and dependencies" step fetched (06:40:56Z, 45 commits later), ruling out a stale-clone/propagation-lag explanation.
  Root-caused instead to `base-service.sh` (not `base-library.sh`) carrying an untouched duplicate of the same PARGS
  line — see todo 2a above for the full diagnosis and fix (`unified-trading-pm@<see quickmerge output>`, this same
  commit). PR #1026 itself had already reached `state: MERGED` independently by the time of investigation (~06:59Z,
  presumably via the "Option-B direct" LDR→main push path rather than a literal green PR check — consistent with
  every prior entry's "self-clears via retry/cron before a fix is needed" pattern) — no instruments-service code/test
  change was needed or made. However, a NEW promotion PR cycle was already in flight at diagnosis time (head
  `9a30b6c5`, run `30521486911`, `queued` as of 07:01:20Z) that would have cloned the STILL-unfixed `base-service.sh`
  and could plausibly hit the same flake — shipping this fix promptly (rather than filing it as a pure evidence
  entry like several prior corroborations did) directly protects that in-flight run and every future service-repo
  promotion, not just a retroactive diagnosis. This closes todo 2a's "is the gap a one-off" question definitively:
  no, the exact same un-overridden-hardcoded-wall-clock authoring pattern recurred in a sibling shared script one day
  after the first instance was "fixed," silently leaving ~20 service repos (the majority of the fleet) still exposed.
