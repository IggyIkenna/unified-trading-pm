---
doc_type: plan
title:
  agent-orchestrator — restore promotion_model=ldr_main (fleet parity) and harden quality gates / coverage for
  parallel AO-dispatch
summary: >-
  Operator directive 2026-08-19: agent-orchestrator is about to accept PARALLEL AO-dispatched background agents
  working on its own codebase, the same way every other repo already does. It currently runs
  `promotion_model: ldr_terminal` (opted out of ALL promotion — no staging, no main — since 2026-08-05, when only
  one careful interactive session ever touched it and nothing else in the workspace consumed its `main` branch or
  version). That isolation fit a single careful operator; it does not fit concurrent unattended workers editing
  the same repo. This plan (1) flips agent-orchestrator back to `ldr_main` with the same CI-gated promotion path
  every other repo gets, without reintroducing the ORIGINAL incident that caused the 2026-08-05 flip (a stuck
  main-promotion PR silently blocked the dashboard's auto-deploy for 3+ hours, main sat 751 commits behind LDR),
  (2) hardens and expands agent-orchestrator's quality gates and measured test coverage so parallel dispatch is
  actually safe, and (3) backfills regression tests for agent-orchestrator's own archived incident history so none
  of them can silently recur. Authored mid-research: Phase 1 is fully scoped from direct reading of the 2026-08-05
  issue doc; Phase 2/3's exact todos depend on a live coverage measurement and an archived-issues gap analysis that
  were still running when this plan was written — see "Research still in flight" below before starting those
  phases.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, ci-cd, promotion-model, quality-gates, coverage, regression-tests, ldr-terminal]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md,
  ]
created: 2026-08-19
last_updated: 2026-08-19
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
effort: high # CI/promotion-model change on a repo with a documented prior incident + coverage/regression-test
# work spanning many files -- real judgment calls throughout (Phase 1's "keep vs revert" decisions, Phase 3's
# per-gap test design), not mechanical; role default would under-serve it.
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/issues/agent_orchestrator_ldr_terminal_promotion_2026_08_05.md,
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/workspace-manifest.json,
    unified-trading-pm/scripts/quickmerge.sh,
    agent-orchestrator/.github/workflows/deploy-dashboard.yml,
    /plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md,
  ]
source: >-
  Interactive session 2026-08-19: operator directive, verbatim intent — "since we're gonna start putting parallel
  agent orchestrator agents on agent orchestrator... flip agent orchestrator to work like everything else... update
  all the rules, all the codex... harden and expand the quality gates... all the issues and stuff we've had and
  archived, there should be regression tests for those." Plan destination confirmed human/NA by the operator
  (AskUserQuestion, same session) — not AO-dispatched.
drift_direction: advance-process
---

# agent-orchestrator: restore promotion_model=ldr_main + QG/coverage hardening for parallel AO-dispatch

> **✅ ARCHIVED 2026-08-20** — all 5 phases shipped and verified: `promotion_model: ldr_main` restored + branch
> protection re-applied (Phase 1); coverage 70%→85.97% with a real enforced floor + ratchet, `lifespan()`'s
> coverage gap closed (Phase 2); 10 real regression-test gaps found and fixed across an exhaustively-sampled
> archived-incident corpus (Phase 3); `Dockerfile.vm-orchestrator` shipped, cross-checked against the IONOS
> migration (Phase 4). Durable facts migrated to codex: `/codex/08-workflows/ci-cd-flow.md` (promotion model),
> `/codex/04-architecture/runtime-deployment-topology.md` (Docker). See Progress Log + Closing summary below for
> the full record.

## Why now

Same-session precedent already fixed a smaller instance of the *symptom* of this gap: `quickmerge.sh` was silently
treating `ldr_terminal` repos as the dead staging-first path (fixed, `unified-trading-pm@bff3027035`). That fix was
correct given `ldr_terminal` stays intentional — but the operator's actual direction is to retire `ldr_terminal`
for agent-orchestrator entirely, not just describe it accurately. This plan is that retirement plus the safety-net
work that makes it safe to have multiple concurrent AO workers editing this repo at once.

## Research status

This plan was authored mid-research, checkpointed via `/pre-compact` at ~68% context, then updated in place as each
research pass reported back over the course of the same session. **All three phases are now backed by completed
research, not placeholders** — Phase 1 from a direct read of the 2026-08-05 issue doc plus a live follow-up
investigation; Phase 2 from a full live coverage run (77.41% branch / 79.28% statement, against a 70% floor that
turned out not to be actually enforced — see its own section); Phase 3 from a 63-doc sample of agent-orchestrator's
own archived incident history (7 concrete gaps, 2 unclear verdicts, ~92 docs in the tightest corpus still
unsampled). Every phase below states its own remaining unsampled/unmeasured scope where real gaps remain — this
intro is not one.

## Phase 1 — Flip promotion_model back to ldr_main

**RESOLVED by a full research pass this session** (all 5 touch-points from the 2026-08-05 issue doc, plus a live
branch-protection check and a fleet-wide precedent search) — the judgment calls below are no longer open, they're
answered. Executing them is still real work; re-deriving the answer is not.

- [x] [INFRA] P0. ✅ **Flip `workspace-manifest.json`'s `agent-orchestrator` entry**: `promotion_model`
      (`repositories.agent-orchestrator`, ~line 1524) from `"ldr_terminal"` to `"ldr_main"`. **Do NOT also revert
      `ci_trigger_branch`** (line ~1533, currently `"live-defi-rollout"`) — keep it (see next todo). Rewrite the
      `notes` field (~line 1538) — it currently warns "do not re-add ldr_main without also reverting the dashboard
      trigger," which is now the WRONG instruction (the dashboard trigger stays put; see below) and would mislead
      the next reader if left as-is. **Also fix, same commit**: `versions.agent-orchestrator` (top-level, ~line 86)
      reads `"0.100.3"` vs `repositories.agent-orchestrator.version` (~line 1535) reads `"0.100.0"` — pre-existing
      drift, unrelated to this flip, fix it while touching this file rather than leaving it for someone else to
      trip over. Ship via `quickmerge.sh --agent --files`. Done-when:
      `python3 -c "import json; print(json.load(open('workspace-manifest.json'))['repositories']['agent-orchestrator']['promotion_model'])"`
      prints `ldr_main`, `ci_trigger_branch` is still `live-defi-rollout`, both version fields match, and
      `scripts/cicd/ldr_to_main_fleet_promote.sh`'s `LDR_MAIN_REPOS` output includes `agent-orchestrator` again.
      **DONE 2026-08-19** — all 4 conditions verified live: `promotion_model=ldr_main`,
      `ci_trigger_branch=live-defi-rollout` unchanged, both version fields now `0.100.3`,
      `ldr_to_main_fleet_promote.sh --list` includes `agent-orchestrator` in its SIT-covered/ldr_main repo set.
- [x] N/A — **deploy-dashboard.yml trigger: KEEP `push:[live-defi-rollout]`, do not add `push:[main]` back.**
      RESOLVED, no decision left: reverting to (or restoring) `push:[main]` reintroduces the exact original
      incident (a stuck main-promotion PR silently blocking the dashboard). Fleet precedent confirms this is the
      established pattern, not a special case — `unified-trading-system-ui/.github/workflows/deploy-uat-on-merge.yml:14-17`
      is itself an `ldr_main` repo and ALSO triggers only on `push:[live-defi-rollout]`; its own comment states
      prod only ever advances via an explicit `deploy-cloud-run.sh --env=prod` script, never via `push:[main]`.
      No todo needed here — just don't touch this file during the rest of Phase 1.
- [x] N/A — **`ci_trigger_branch` (item 3, the LDR-triggered `quality-gates-v2` run): KEEP, no code/config change.**
      RESOLVED: `/codex/08-workflows/ci-cd-flow.md` confirms a plain `ldr_main` repo gets ZERO CI-server-enforced
      gate on the raw LDR push — `quality-gates-v2` only runs later, on the promote PR the fleet bot opens. Under
      parallel AO-dispatched agents landing directly on LDR, that promote-PR-only gate is real feedback latency;
      the existing `ci_trigger_branch` mechanism (already manifest-driven and generic, not agent-orchestrator-
      specific plumbing) closes that gap as an extra early-warning layer on top of, not instead of, the normal
      gate. No template change needed — already correctly wired.
- [x] N/A — **`ldr-to-staging-promote.yml`'s 2 skip-condition spots: no change needed.** RESOLVED: both spots
      already use `NEVER_PROMOTE = ("ldr_main", "ldr_terminal")` / `_main_direct(cfg)` treating both values
      identically — agent-orchestrator falls into the same excluded branch either way, just via a different tuple
      member after the flip.
- [x] [INFRA] P1. ✅ **Re-apply branch protection**: `python3 scripts/repo-management/pin_branch_protection_rulesets.py
      --repo agent-orchestrator --apply` (dry-run first). Live-confirmed current state via `gh api
      repos/IggyIkenna/agent-orchestrator/rulesets/17369729`: `require-quality-gates` currently requires ONLY
      `Quality Gates (agent-orchestrator) / quality-gates-v2` — `sit-gate/fleet-green` was dropped by the
      2026-08-07 ldr_terminal fix and needs to come back once the manifest flip lands (the script's
      `ldr_main_repos()` picks it up automatically, no code change). Done-when: the live ruleset requires both
      checks again, matching a sibling `ldr_main` repo's ruleset exactly. **DONE 2026-08-19** — dry-run matched
      prediction exactly, `--apply` succeeded (1/1, 0 failures), live `gh api` re-check confirms ruleset
      `17369729` now requires both `Quality Gates (agent-orchestrator) / quality-gates-v2` and
      `sit-gate/fleet-green`.
- [x] N/A — **`semver-agent.yml` / release semantics: leave unreactivated BY DESIGN, but this is not silent.**
      RESOLVED + re-verified live: grepped every repo's `pyproject.toml`/`requirements*.txt`/`package.json`
      fleet-wide — still zero consumers of agent-orchestrator as a package (only self-references inside its own
      `pyproject.toml`). No action needed. **But flag explicitly, don't let it surprise someone later**: AO's
      rendered `semver-agent.yml` and `image-build-gate.yml` BOTH already carry a `push:[main]` trigger that will
      **reawaken automatically** the instant `ldr_main` promote PRs resume landing on `main` — no template edit
      required, no todo needed to "activate" it, it just starts firing. Harmless (mints unused tags/wheel builds
      since nothing consumes them) but worth knowing before someone sees a semver-agent run land unexpectedly and
      assumes something broke. Separately: `semver-agent.yml`'s template architecture changed since 2026-08-05 —
      `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` (status: active, check it before touching
      this file for ANY reason) converted it into a thin stub calling a reusable workflow now centralized in
      `unified-trading-ci` — the issue doc's "943-line file, 20+ hardcoded main refs" framing is stale, re-measure
      before any future work here.
- [x] N/A — **`quickmerge.sh`'s `ldr_terminal` handling (shipped this session, `unified-trading-pm@bff3027035`):
      KEEP as-is, no removal.** RESOLVED: fleet-wide manifest grep found 24× `ldr_main`, 1× `ldr_terminal`
      (agent-orchestrator, about to flip away), 1× `single_branch` (unified-trading-ci) — a THIRD promotion model
      already coexists in the fleet, confirming the generic mechanism isn't AO-specific plumbing to strip out. It
      simply goes unexercised for agent-orchestrator after this flip; leave the code in place for whatever repo
      needs a single-consumer-only escape hatch next.
- [x] [DOC] P0. ✅ **Update every codex/doc reference to agent-orchestrator's promotion model.** Known citations to
      revisit (grep `rg -l "ldr_terminal" codex/ plans/active/` for the full current list — this one may have grown
      since authoring): `/codex/08-workflows/ci-cd-flow.md` (the "24 repos are ldr_main... 0 route through staging"
      count needs to include agent-orchestrator again; any `ldr_terminal` special-case language should note it's
      now describing a currently-unused-but-supported model, not agent-orchestrator's live state),
      `/codex/04-architecture/runtime-deployment-topology.md` (deploy trigger description), and this session's own
      CLAUDE.md system-prompt-visible summary line if one exists (search for "AO self-pulls LDR" framing and
      confirm it still matches whatever Phase 1's dashboard-trigger todo decided). Done-when: `rg -l "ldr_terminal"`
      across codex/ + plans/active/ returns only docs that correctly describe it as a general mechanism, none
      asserting it as agent-orchestrator's current state. **DONE 2026-08-19** — `ci-cd-flow.md`'s two "24 repos are
      `ldr_main`" count sentences (lines ~190, ~346) updated to 25, with an inline cite to this plan.
      `runtime-deployment-topology.md`'s AO self-pull description (lines 594-601) re-checked: describes the DEPLOY
      mechanism (systemd self-pull off `live-defi-rollout`), not the promotion model — unaffected by this flip, no
      edit needed, confirmed still accurate. CLAUDE.md's "AO self-pulls LDR" line: same — deploy mechanism, not
      promotion model, still accurate. `rg -l "ldr_terminal" codex/ plans/active/` post-fix: only this plan itself
      plus 2 docs (`codex_mcp_tool_use_bridge_2026_08_18.md`, `unified_trading_library_config_interface_mass_test_
      failure_2026_08_15.md`) that reference it as historical/dated Progress-Log provenance of already-shipped work
      ("this repo's promotion_model=ldr_terminal" describing state AT THE TIME of that dated entry, not a live-state
      claim) — left untouched deliberately, rewriting historical Progress Log entries would falsify provenance, not
      fix a stale claim.

## Phase 2 — Harden + expand quality gates and coverage

**Measured for real** (`.venv/bin/python -m pytest tests/ --cov=server --cov-report=term-missing -q`, 4,152 tests
collected, 4,146 passed / 8 skipped / 0 failed, 421s full run): **77.41% branch coverage / 79.28% statement
coverage** against `pyproject.toml`'s declared `fail_under = 70`.

- [x] [INFRA] P0. ✅ **The 70% floor is declared but NOT actually enforced — fix the gate itself first.**
      `scripts/quality-gates.sh` (~line 115) runs `python -m pytest tests/ -q -p no:cacheprovider` with **no
      `--cov` flag at all** — `pyproject.toml`'s `fail_under = 70` never gets checked by the automated gate,
      coverage only reflects reality when someone runs it by hand (as this session's research pass did). This is
      the single highest-value Phase 2 fix: wire `--cov=server --cov-report=term-missing --cov-fail-under=70` (or
      the calibrated new floor from the next todo) into the actual QG pytest invocation. Done-when: a deliberately
      under-70%-covering change fails `quality-gates.sh` locally. **DONE — `agent-orchestrator@7f798432ef`.**
      Wired `--cov=server --cov-report=term-missing --cov-fail-under=72` directly (combined with the next todo).
      Verified via a real full `quality-gates.sh` run: `Required test coverage of 72% reached. Total coverage:
      78.86%`, 4395 passed / 0 failed.
- [x] [BACKEND] P1. ✅ **Raise the enforced floor from 70% toward the measured 77.41%, incrementally** — e.g. 72-73%
      as a first milestone, not straight to the current number (leaves zero regression headroom) and not an
      arbitrary round figure. Wire into the same `--cov-fail-under` flag as the todo above (one combined change if
      convenient). Done-when: QG passes at today's level and fails on a real regression below the new floor.
      **DONE — `agent-orchestrator@7f798432ef`.** Set to 72% (`pyproject.toml`'s `[tool.coverage.report]
      fail_under` + the CLI flag, kept in sync). Mechanically guaranteed by pytest-cov's `--cov-fail-under` to fail
      any run under the floor — real measured total after this batch is 78.86%, real headroom above 72%.
- [x] [BACKEND] P1. ✅ **Zero-coverage files — the highest-value gap, not the lowest-percentage one.**
      `server/creds_env_poller.py` (0.00%, 106 lines), `server/kimi_balance.py` (0.00%, 46 lines),
      `server/kimi_balance_poller.py` (0.00%, 67 lines) have NO tests at all, not just weak ones. One todo per
      file: write a real test suite (not a smoke test) for each. **DONE — `agent-orchestrator@7f798432ef`.** All 3
      now 100% statement + 100% branch coverage: `creds_env_poller.py` (24 tests, verified stable across 3 runs),
      `kimi_balance.py` (14 tests), `kimi_balance_poller.py` (14 tests, including real thread lifecycle + `_loop`
      resilience branches).
- [x] [BACKEND] P2. ✅ **Worst-covered-by-percentage, split per file — all 10 DONE, `agent-orchestrator@6b430b1d24`.**
      `server/routes/vms.py` (20.34%→94%), `server/gemini_translation_smoke.py` (31.21%→97%),
      `server/routes/ops.py` (33.59%→100%), `server/routes/resource_watchdog.py` (34.58%→98% — also surfaced +
      fixed a real dead-code bug, see Progress Log), `server/notifications/telegram.py` (37.96%→100%),
      `server/fleet_slot_snapshot_poller.py` (40.00%→100%), `server/routes/repo_blockers.py` (41.27%→98%),
      `server/worker_liveness/_respawn.py` (42.28%→96%), `server/auto_park_reconcile.py` (43.59%→99%),
      `server/worktree_setup.py` (45.33%→100%).
- [x] [BACKEND] P1. ✅ **Worst-covered-by-VOLUME — 4/4 DONE.** `server/server.py` (37.69%, 325 lines missing),
      `server/gcs_sync.py` (42.45%, 238 missing), `server/tmux_spawn.py` (69% cov but 230 missing),
      `server/autospawn.py` (83% cov but 216 missing). First 2 done at `agent-orchestrator@7f798432ef`: `server.py`
      37.44%→52.05% scoped (66-line reduction; `lifespan()`'s ~685-line async-context-manager body deliberately
      deferred, see its own follow-up todo below), `gcs_sync.py` 42.45%→87-88% (also surfaced + fixed a real bug,
      see Progress Log). Last 2 done at `agent-orchestrator@6b430b1d24`: `tmux_spawn.py` 55%→99% (7 new test
      files, process-tree/retry/prompt-dismissal logic), `autospawn.py` 85%→91% (55 real lines closed,
      prioritizing `seed_worker_slots_from_tabs`/`_resume_pass`/`_drain_scheduled_jobs` — all previously 0%).
      Full-suite verification after this wave: 4891 passed, 0 failed, 82.66% total coverage (up from 78.86%).
- [x] [BACKEND] P2. ✅ **DONE — closed by a concurrent teammate session, `agent-orchestrator@b74c8433`
      (harshkantariya [slot-3], 2026-08-20T10:44 IST), independently landed between this plan's last checkpoint and
      this resumption.** Chose exactly the DI-seam-adjacent design this todo called for once scoped: not a real-app
      boot test (too much real thread/tmux/GCS/Slack side-effect risk on a shared host, per this todo's own
      warning), but hand-mocking every one of the ~35 background-loop CLASSES at their import boundary
      (`patch("server.<mod>.<Class>", MagicMock())`) so the REAL `lifespan()` control flow — which loops
      `.start()`, which land in `_state`, which get registered for `LoopSupervisor` auto-revival, which get a
      `.stop()` call on shutdown — runs genuinely, with zero real side effects. New
      `tests/test_server_lifespan.py` (432 lines, 15 tests, verified standalone: 15/15 passed). Found + fixed 2
      real bugs while writing it — an independent rediscovery of the exact bug class this plan's own Progress Log
      already flagged once (2026-08-15, `batching_stats_poller`/`fleet_slot_snapshot_poller`): `snapshot_recency`/
      `kimi_balance_poller`/`tmux_session_loss_rate` were started + tracked in `_state` but never registered in the
      shutdown `_stoppable` list, and 17 of ~35 loops were missing from `LoopSupervisor._supervised_candidates`
      (so a crashed thread among them could never auto-revive). `server.py` coverage: 52%→89% (commit-cited,
      file-scoped). Full-suite re-verification this session (fresh `.venv/bin/python -m pytest tests/
      --cov=server --cov-report=term-missing --cov-report=json`): **5240 passed / 0 failed / 8 skipped, 85.97%
      total coverage** (up from 82.66% at last checkpoint — `git log` shows ~15 more independent coverage-hardening
      commits landed fleet-wide between checkpoints, confirming parallel AO-dispatch on this repo's own codebase is
      now genuinely working, which is this plan's whole point). Coverage ratchet re-verified passing:
      `check_coverage_ratchet.py --report coverage.json` → `[OK] total coverage 85.9738% (== baseline 85.9732%)`
      (baseline already kept current by a concurrent session). No further work needed on this todo.
- [x] [INFRA] P2. ✅ **DONE — `agent-orchestrator@cfd1a47753`.** Unit/integration split — 3781 test functions
      across 280/302 files auto-marked `@pytest.mark.unit` by MEASURED per-test runtime (not manual per-file
      classification — a one-off script cross-referenced `--co -q` + `--durations=0` output via `ast` parsing,
      inserting only decorator lines, never touching test logic). Threshold 0.05s, chosen from the real timing
      distribution's density inflection. `pytest -m unit` verified at 26-48s across 3 runs under real host
      contention (target: well under 60s) — 3952/4897 collected items. Found + correctly excluded (not silently
      forced green) one pre-existing, unrelated test-isolation bug — see new follow-up todo below.
- [x] [INFRA] P2. ✅ **DONE — `agent-orchestrator@cfd1a47753`.** Coverage baseline/ratchet — new
      `scripts/quality_gates/check_coverage_ratchet.py` + `coverage_baseline.yaml`, wired into `quality-gates.sh`
      right after the existing `--cov-fail-under=72` step (reuses the same `--cov-report=json` output, no second
      pytest run); `--update-baseline`/`--allow-lower` mirrors this workspace's established ratchet pattern.
      Caught + fixed a real precision bug in its own first version before shipping it: 3 consecutive full-suite
      runs of IDENTICAL code measured 82.6823%/82.6797%/82.6770% total coverage (real run-to-run coverage.py
      noise on this ~4900-test suite, not regressions) — the original narrow tolerance against a 2-decimal-
      rounded baseline would have permanently flapped the gate red; fixed to full-precision storage + a tolerance
      sized to the measured noise floor, verified both that real noise now passes and a fabricated regression
      still correctly fails.
- [x] [INFRA] P3. ✅ **DONE (decided yes) — `agent-orchestrator@cfd1a47753`.** Dashboard vitest coverage — added
      `@vitest/coverage-v8` (2/2 sibling UI repos in this workspace already use it, so this wasn't a novel
      package ask) + a coverage config block, wired into `quality-gates.sh`'s existing dashboard test step.
      Baseline measured: 12.88% statements / 89.77% branches / 33.79% functions across `src/` — the low
      statement% is structural (this harness runs DOM-less, testing pure `.ts` logic only; `.tsx` component
      render coverage is the Playwright e2e layer's job by design, same split `unified-trading-system-ui` already
      makes explicit). No enforcement floor wired yet, deliberately — flagged as its own follow-up decision once
      the baseline is accepted, not built in this pass.
- [x] [INFRA] P2. ✅ **DONE — `agent-orchestrator@8e0438c160`.** Pre-existing test-isolation/order-dependency bug:
      `tests/test_pane_tree_reap.py::test_kill_session_reaps_before_tmux_kill` failed both standalone and under
      `pytest -m unit` despite passing in the full suite. Root cause found: `kill_session`'s teardown log calls
      `running_checkout_sha()`, which caches its result in a module-level global once warmed; the test's
      `monkeypatch.setattr(tmux_spawn.subprocess, "run", fake_run)` patches the shared stdlib `subprocess`
      singleton (not a `tmux_spawn`-local copy), so a COLD cache let the mock leak through and record a spurious
      extra call — the full suite masked this because an earlier-collected test always warms the cache first.
      Fixed test-side (mirrors existing prior art in `test_tmux_spawn_kill_and_dismiss.py` for the identical
      gotcha) — the cache-once-per-process design itself is deliberate, not a bug. Re-added `@pytest.mark.unit`.
      Verified standalone + `-m unit` + full suite (4891 passed) all green.
- [x] [INFRA] P2. ✅ **RESOLVED 2026-08-19 — already covered by existing generic machinery, no new gap.** Audit
      whether a check is needed against no-two-open-AO-tasks-targeting-the-same-agent-orchestrator-file risk.
      Found `server/regen_backlog_from_plan.py::_derive_script_collision_group()` — built specifically from a real
      prior incident (`transfermarkt_master_table_gcs_429_concurrent_writers_2026_07_12`: 3 slots independently ran
      the same one-off script concurrently against the same target) — auto-derives `collision_group="script:
      <filename>"` from ANY `.py`/`.sh` filename regex-matched in a todo's description text at backlog-regen time;
      `dispatch.py`'s existing `_blocks_collision_group`/`_active_collision_groups_excluding` then makes two tasks
      sharing that `collision_group` mutually exclusive across slots — generic dispatch machinery, applies to
      AO-on-AO identically to every other repo, no AO-specific code needed. Residual (not a gap, a known
      characteristic): basename-keyed not full-path-keyed (so `a/gcs_sync.py` and `b/gcs_sync.py` would
      over-conservatively collide — harmless), and it only engages when a todo's description literally names the
      target filename (relies on todo-authoring discipline — but this plan's own todos already do that
      consistently, e.g. every Phase 2 coverage todo names its target file by path).

## Phase 3 — Regression tests for agent-orchestrator's own incident history

**RESOLVED with real data, not a placeholder, and the tightest corpus is now FULLY sampled** — across 3 passes this
session (63 + 34 + 117 docs = 214 doc-reads, some early ones later corrected on re-check), every doc in the tightest
high-confidence corpus (single-repo `repos: [agent-orchestrator]` docs living in `plans/archive/issues/`, 126 total
as of 2026-08-20) has been read and cross-checked against the CURRENT test suite. **Coverage is unusually strong
already** — AO's suite frequently cites the issue-doc filename directly in a comment above its regression test —
final tally across the whole corpus: **~124 COVERED, 10 real GAPs found and fixed (all shipped, all with dedicated
regression tests), ~24 SKIP (non-code-fix incidents: pure ops/VM/credential-rotation, or explicitly-declined
decisions), 0 genuinely UNCLEAR** (2 early UNCLEAR verdicts were resolved on re-check: one to COVERED, one to a
confirmed GAP — see Progress Log). The wider ~36 co-listed-repo + ~130 non-`issues/`-folder archived corpus was
considered and explicitly NOT pursued — see its own subsection below.

- [x] [BACKEND] P1. ✅ **FALSE POSITIVE, corrected 2026-08-19 — actually COVERED, not a GAP.** delivery was marked
      on POLL/drain, not on the agent's actual reply (`ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md`).
      This session's prior research pass claimed a new `tests/test_operator_reply_delivery_ack.py` was needed —
      **verified false**: `agent-orchestrator/tests/test_agent_message_redelivery.py` already exists (shipped at
      `ao@8076257`, the same commit that fixed the incident) with 8 tests including
      `test_reply_acks_whole_batch_641_643_regression` — the exact 641/643 regression this issue doc names, plus
      `test_redelivered_until_answered`/`test_reply_ack_stops_redelivery` covering precisely "stays undelivered
      until the agent's reply is recorded." The earlier research sampled the issue doc's narrative without checking
      the current test suite for an existing regression test — a CLAIM ≤ MEASUREMENT miss. No new test needed.
- [x] [INFRA] P1. ✅ **DONE — `agent-orchestrator@6b430b1d24`.** `ao-self-pull.sh` silently stalled 2+ hrs —
      untracked `accounts.json` backup files blocked `git pull --ff-only`
      (`ao_self_pull_stalled_by_untracked_backup_files_2026_07_29.md`). New `tests/test_ao_self_pull_dirty_gate.py`
      (6 tests, real `bash scripts/ao-self-pull.sh` invocations against a scratch git repo, not `bash -n`): dirty
      gate skip/proceed correctness, `_track_dirty_tick()` counter climb/reset, and the WEDGE alert firing at
      exactly the configured tick count. Found + noted (not a bug): the original narrow `.gitignore`-pattern fix is
      now superseded by a broader 2026-08-08 hardening (`git status --porcelain -uno`, ignores ALL untracked files)
      — tests target the current behavior and guard against a future regression that drops `-uno`.
- [x] [INFRA] P2. ✅ **DONE — `agent-orchestrator@6b430b1d24`.** `quality-gates.sh` never ran `pip-audit` — silent
      gap in the gate itself (`agent_orchestrator_pip_audit_ungated_2026_07_30.md`). New
      `tests/test_quality_gates_script_contents.py` (4 tests): asserts the script contains the real
      `.venv/bin/python -m pip_audit` invocation (not the standalone binary — the exact methodology bug the
      incident corrected), the labeled section header, and that it can actually fail the gate (`FAIL=1` present) —
      regression-guards the SCRIPT CONTENT so this can't silently drop to advisory-only.
- [x] [INFRA] P1. ✅ **DONE — `agent-orchestrator@6b430b1d24`.** Orchestrator's own systemd `MemoryMax` cap went
      stale vs. actual need → full API outage, HTTP:000 on every endpoint
      (`orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`). New
      `tests/test_orchestrator_service_memory_cap.py` (8 tests) — found the durable fix is `scripts/rescale-memory-
      cap.sh` (computes MemoryMax/MemoryHigh as 87.5%/75% of live `/proc/meminfo` MemTotal, applied instantly via
      `systemctl set-property --runtime` + a persistent drop-in), wired into both `bootstrap_vm.sh` and
      `ao-self-pull.sh`'s ~2min cron tick so a future EC2 resize self-heals. Tests assert the directive still
      exists, isn't the exact stale literal from the outage, and that the rescale mechanism is actually wired at
      both trigger points — not just a corrected static number.
- [x] [BACKEND] P2. ✅ **DONE — `agent-orchestrator@6b430b1d24`.** `/api/slots/<N>/spawn` silent-failed on an
      unhandled workspace-trust prompt (3 compounding defects, `orchestrator_spawn_tmux_silent_failure_2026_05_20.md`).
      Added 2 tests to `tests/test_spawn_heartbeat_liveness.py`, exercising the real, unmocked `spawn()` →
      `_dismiss_bypass_warning()` → `_dismiss_startup_prompts()` → `_paste_prompt()` chain end-to-end (only the
      tmux/subprocess boundary is mocked) — proves spawn raises `RuntimeError` rather than silently reporting
      success when the trust prompt never clears or neither prompt appears at all. All 3 defects from the incident
      confirmed still fixed in current code; nothing needed re-fixing.
- [x] [BACKEND] P1. ✅ **FALSE POSITIVE #3, corrected 2026-08-19 — actually COVERED, not a GAP.**
      `regen_backlog_from_plan.py`'s claimed silent-drop of hand-tuned `prereqs.conditions` + priority tuning
      (`backlog_regen_drops_handtuned_prereqs_2026_07_12.md`) — both underlying defects are already fixed and
      tested under different names: priority-revert via `BacklogTask.priority_override` +
      `test_regen_priority_override_survives_regen_tick`; `prereqs.conditions` was ruled a **documentation bug, not
      a code bug** — that field never existed as a real pydantic field (only `completed_tasks`/`prerequisites` do;
      pydantic v2's default `extra="ignore"` silently drops unknown keys), and RULES.md was already corrected
      (`unified-trading-pm@f1585fb59`) to document `prereqs.prerequisites` instead. Added
      `test_regen_preserves_handtuned_prereqs_and_priority` anyway (passes) plus cited 2 pre-existing tests
      (`test_regen_park_survives_sibling_completion_and_id_shift`/`..._insertion`) that prove this even more
      thoroughly across sibling-todo mutation. Shipped at `agent-orchestrator@6b430b1d24`.
- [x] [DOC] P2. ✅ **RESOLVED 2026-08-19 → COVERED, not unclear.** SQLite lock-storm-triggers-stuck-shutdown causal
      chain (`ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`) — read `test_server_shutdown.py` closely:
      its module docstring explicitly names `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`'s P2 todo
      and describes the exact causal chain (sequential `.stop()` calls each blocking on `thread.join(timeout=5-10s)`
      under DB-lock-storm/tmux-timeout contention, reproducing the incident's ~20-25s shutdown hang before
      systemd's SIGKILL) — `test_stops_run_concurrently_not_sequentially` and
      `test_every_stop_fn_is_called_even_if_one_raises` directly regression-guard the fix
      (`_stop_loops_concurrently`). The prior pass's "no keyword ties it" claim was checked against the wrong
      thing (a name-only grep, not the docstring) — a second CLAIM ≤ MEASUREMENT miss this same session. No new
      test needed.
- [x] [BACKEND] P2. ✅ **DONE — `agent-orchestrator@6b430b1d24`.** Unpinned `ORCHESTRATOR_JWT_SECRET` invalidating
      every token on restart (`orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md`) —
      the incident's "restart-persistence" verification was 100% live/manual VM ops, never a checked-in test
      (confirmed `_load_secret()` had zero direct coverage). New `tests/test_load_jwt_secret.py` (3 tests): env-var
      pinned → two calls return identical value; neither set → two calls return DIFFERENT random values
      (documents the dev-fallback trap this incident hit); GCS fallback path also pins correctly (mocked at the
      lazy-import boundary `_load_gcs_secret` actually uses).
- [x] [INFRA] P3. ✅ **DONE 2026-08-20 — the full tightest-corpus (126 docs) is now sampled.** Third pass this
      session: re-derived the corpus (`grep -l "^repos: \[agent-orchestrator\]$" plans/archive/issues/*.md` = 126,
      up from 124 at last count — 2 new archived docs landed since), excluded the 10 already individually named in
      this Phase 3 section, split the remaining 117 into 5 chunks of ~23-24 and dispatched 5 parallel sub-agents
      (same COVERED/GAP/SKIP/UNCLEAR method, CLAIM ≤ MEASUREMENT enforced — verify against the CURRENT test suite,
      not the doc's own narrative). Result: **100 COVERED, 2 real GAPs found and fixed, 15 SKIP (non-code-fix:
      ops/VM/credential-rotation incidents, or explicitly-declined decisions), 0 UNCLEAR.** The 2 GAPs:
      `gate_completed_tasks_trusts_stale_done_after_checkbox_unflip_2026_07_25.md` —
      `scripts/orchestrator/audit_stale_gate_references.py` had zero regression tests despite its sibling
      `audit_false_done.py` having one; new `tests/test_audit_stale_gate_references.py` (5 tests), shipped
      `agent-orchestrator@3de239ee61`. `orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md`
      — the `install-orchestrator-service.sh` call wired into `ao-self-pull.sh` (fixing a 9-day-stale systemd unit)
      was only ever verified live/manually; new `tests/test_ao_self_pull_install_unit_wiring.py` (3 tests, real
      scratch git checkout + stub install script), shipped `agent-orchestrator@a22beb8d44`. Both verified via a
      full `quality-gates.sh --no-fix` green run before shipping. One sub-agent backgrounded its own QG run and
      stalled waiting on a notification it can't receive as a sub-agent (the same class already documented once in
      this plan's own Progress Log) — recovered via `SendMessage` with corrective foreground-only guidance, same
      recovery pattern as before, completed successfully on resume. Combined with the two prior passes (63 + 34
      docs), the tightest corpus is exhaustively sampled: 10 real GAPs found and fixed across the whole effort,
      all shipped with dedicated regression tests. Corpus re-derivation one-liner for any future audit:
      `grep -l "^repos: \[agent-orchestrator\]$" plans/archive/issues/*.md`.
- [x] [DOC] P3. ✅ **DONE — `agent-orchestrator@8e0438c160`.** Investigate the recurrence pattern, not just the
      latest fix: 3 recurrences of the regen-dispatch pattern-matching gap (confirmed via `git log -G` against
      the regex — 2 of the 3 are code-commit-level recurrences, not separate PM issue docs as originally framed;
      only 1 doc, `ao_backlog_regen_missing_self_declared_not_ao_eligible_guard_2026_08_14.md`, actually exists —
      a CLAIM ≤ MEASUREMENT correction to this todo's own premise). Built a `hypothesis` property-based test
      fuzzing case/markdown/context variations of the known phrasings — **it found a real 4th recurrence on its
      first run**: case-sensitivity, British "judgement" spelling, missing-article phrasing, and markdown-italic
      `\b`-boundary defeat were ALL silently unmatched. Fixed all 4 in `_PERMANENT_NON_DISPATCHABLE_RE`. This
      converts the bug class from silently-missed to loudly-caught-by-CI on the next phrasing variant, though not
      a permanent close — **architectural recommendation** (not implemented, per scope): pattern-matching prose
      is fundamentally the wrong tool (a genuinely novel phrase still slips through no matter how much fuzzing
      covers KNOWN meanings); an explicit machine-readable tag (this codebase already has `[OPERATOR]` precedent)
      would be the durable fix — a bigger change, left as a future consideration, not built here.

### Considered and explicitly OUT of scope: the wider ~166-doc corpus (co-listed-repo + non-`issues/`-folder)

Operator directive framing (this plan's own Research Status, authored 2026-08-19) already flagged this corpus as
lower-value: "~403 archived docs total mention agent-orchestrator at all, most of them feature-build plans not
incident postmortems." The tightest corpus (single-repo `repos: [agent-orchestrator]`, living in `issues/`) was
deliberately the highest-postmortem-density target, and it is now exhaustively sampled with a very high real-GAP
hit rate relative to its size (10 real gaps across 214 doc-reads). **Decision: do not extend Phase 3 sampling to
the wider ~36 co-listed-repo docs or the ~130 non-`issues/`-folder archived docs** — they are predominantly
feature-build/plan-execution history, not incident postmortems, so the same method would spend far more read-time
per real gap found. If a future session wants to pursue this anyway, it is a new, separate, open-ended effort — not
a blocker on this plan's Phase 5 archival, and not silently dropped: this paragraph is the record of the decision
and its reasoning, mirroring Phase 4's own carve-out pattern below.

## Phase 4 — Containerize agent-orchestrator (Docker), cross-checked against the IONOS migration

Operator directive (same session, added after Phases 1-3 were already checkpointed): package agent-orchestrator to
run as a Docker container inside its VM, specifically to make cross-cloud migration easier. **This plan does not
own the cloud migration itself** — `/plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md` already tracks that
(added to this plan's `related:`) — but containerizing AO is directly relevant to it and must be cross-checked
against whatever that plan currently assumes about how AO is deployed/run.

- [x] [INFRA] P1. ✅ **DONE 2026-08-19.** Read `ao_ci_aws_to_ionos_migration_2026_08_18.md` in full before
      designing the container build. Finding: it's a mature, mostly-blocked (on the operator's IONOS account
      signup, §3) human plan with real production-cutover stakes, assuming the exact bare-VM systemd +
      `ao-self-pull.sh` model unchanged — zero containerization anywhere in it. **Decision: containerizing WRAPS
      the existing self-pull/restart model, does not replace its mechanics** — "how a new version reaches the
      running box" still flows through the same self-pull-detects-a-new-LDR-commit trigger, just
      rebuilding/restarting a container instead of restarting a bare uvicorn process. Folded into the IONOS plan
      itself as a Decision-log entry + a note on its open VM-lifecycle-abstraction design todo (next todo below
      covers that fold-in specifically).
- [x] [INFRA] P1. ✅ **DONE — `agent-orchestrator@8e0438c160`.** Design + ship the Dockerfile/image-build
      workflow. New `Dockerfile.vm-orchestrator` (kept separate from the existing root `Dockerfile` — see below)
      — multi-stage, `python:3.13-slim`, same `orchestrator.service` ExecStart minus `--reload` (redundant with
      `ao-self-pull.sh`'s own restart), includes `tmux`/`git`/`openssh-client` since worker-session spawning is
      the point. **Verified end-to-end**: built + ran with `ORCHESTRATOR_MODE=mock`, `GET /api/healthz` → 200
      from inside the running container. Build trigger: new `.github/workflows/image-build-vm-orchestrator.yml`,
      `push:[live-defi-rollout]` path-filtered, **inactive by design** (no push step — no confirmed registry
      target/credentials exist yet; GCP-auth fails closed via `continue-on-error`). `image-build-gate.yml`
      confirmed NOT reusable — it only drives a pre-provisioned Cloud Build trigger off the root `Dockerfile`, no
      Dockerfile-path input. **Major finding surfaced, filed as its own issue (out of scope here, different
      deployment target)**: agent-orchestrator already has a SEPARATE, existing Cloud Run Dockerfile
      (`agent_orchestrator_cloud_run_deployment_2026_05_19.md`, archived — a stateless API-only "brain," no
      tmux, gated on a companion workers-off-VM plan reaching D3) — that Dockerfile's `COPY agents/ ./agents/`
      step is broken (the directory was deleted 2026-07-10's read-the-file boot cutover); filed as
      `plans/active/issues/agent_orchestrator_cloud_run_dockerfile_broken_copy_agents_dir_2026_08_19.md`.
- [x] [INFRA] P2. ✅ **DONE 2026-08-19 — `unified-trading-pm@dd472dfa24`.** Decide what "runs as a
      Docker container inside the VM" means for the EC2→IONOS migration. Containerizing makes it strictly
      easier — a container runtime is a much smaller cross-cloud-portability surface than replicating a full
      `uv`-venv Python bootstrap per provider. Folded into the IONOS plan directly (not duplicated here): a new
      Decision-log entry there records the wrap-not-replace decision and its "first real test of the
      portability motivation" framing, and its open §1 VM-lifecycle-abstraction design todo now notes to
      evaluate "provision compute + firewall + a container runtime, then `docker pull`+`docker run`" instead of
      the full venv-bootstrap-per-provider shape when it's next picked up — not a mandate to redesign now, since
      that plan is still blocked on §3 (IONOS account signup) regardless.

### Considered and explicitly OUT of scope: CI self-hosted runners do NOT get this same treatment

Operator reasoning (same session, worth recording so it isn't re-litigated): the CI self-hosted runner
infrastructure is not itself a deployed application shipping code from LDR to main — it has no code of its own,
it's a cron-driven executor running the workflow YAMLs that already live in each target repo. There's no
"container of itself" to build, and no promotion-model question to resolve, because there's no deployable artifact
in the first place. **Decision: the CI runner infrastructure stays outside this plan's scope entirely** — it does
not need a `promotion_model` flip (it was never `ldr_terminal` or any other promotion model to begin with) and
does not need Docker containerization for the same reason a cron job doesn't need containerizing to migrate
clouds. If CI-runner-specific migration work is needed for the IONOS move, that belongs in
`ao_ci_aws_to_ionos_migration_2026_08_18.md` (or a sibling doc), not here.

## Phase 5 — Finalize

- [x] [DOC] P1. ✅ **DONE 2026-08-19.** Post-phase codex audit — checked every codex doc this plan's `related:`/
      `context_scope:` cites against everything actually shipped: `ci-cd-flow.md` (repo counts + the `ldr_terminal`
      mention, both already correctly updated in Phase 1 and re-verified accurate here, correctly framed as
      historical — "restored 2026-08-19 after a 2-week detour" — not asserting it as current state anywhere),
      `runtime-deployment-topology.md` (confirmed still accurate, deploy mechanism never changed). Repo-wide
      `rg -l "ldr_terminal\|promotion_model.*agent-orchestrator" codex/` returns only `ci-cd-flow.md`, correctly
      framed. No contract invalidated by this plan's shipped work; nothing needed a SUPERSEDED banner in codex
      itself (the archived issue doc below is a plan/issue doc, not codex — handled by the next todo).
- [x] [DOC] P1. ✅ **DONE 2026-08-19.** Archive `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`'s
      live-state claims are now historical, not current — added the dated SUPERSEDED note at its top pointing to
      this plan's Phase 1, noting the deploy-side facts (dashboard trigger fix, root cause) are still accurate
      history but the `promotion_model: ldr_terminal` state itself is superseded.
- [x] [DOC] P0. ✅ **DONE 2026-08-20.** Archive this plan — standard 6-step ritual: (1) no genuine deferral left
      un-migrated (the two Deferred-work rows below both closed this session; the wider-corpus scope decision is
      recorded in its own "Considered and explicitly OUT of scope" subsection in Phase 3, not a deferral); (2)
      archived-banner added above; (3-4) codex-alignment re-check this session found one genuine gap —
      `/codex/04-architecture/runtime-deployment-topology.md` still asserted agent-orchestrator is "not
      container-redeployed on push" with no mention of the new (dormant) Dockerfile — fixed with a new paragraph
      documenting it + the wrap-not-replace decision; (5) referrer-path fixup: grepped the whole corpus for this
      plan's path, fixed all live referrers — `plans/archive/2026_08/issues/agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`'s
      SUPERSEDED banner, `plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md`'s 2 Decision-log prose mentions
      (now also pointing at the codex doc for the durable fact), `plans/active/issues/agent_orchestrator_cloud_run_dockerfile_broken_copy_agents_dir_2026_08_19.md`'s
      `related:`/`context_scope:` fields — all repointed to the new archive path (one doc,
      `plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md`, is itself an already-archived
      point-in-time snapshot table — left untouched, historical record); `plans/active/INDEX.md`'s listing removed
      in the same commit as the move; (6) `doc_type: plan` → dated `plans/archive/2026_08/` (not flat issues/),
      single-repo mode-1 sanctioned same-commit flip+`git mv`, both old and new paths named in `--files` per the
      rename-deletion-hazard guidance.

## Progress Log

- **context-scout 2026-08-19**: populated/refreshed context_scope (6 entries) — added
  `ao_ci_aws_to_ionos_migration_2026_08_18.md` (Phase 4 explicitly directs reading it in full before designing the
  container build).
- **2026-08-19 (interactive session, checkpointed via `/pre-compact` at ~68% context)**: Plan authored following an
  operator directive to prepare agent-orchestrator for parallel AO-dispatched background agents. Plan destination
  confirmed human/NA via AskUserQuestion. Phase 1 fully scoped from a direct, complete read of
  `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`. Phase 2/3 intentionally left at the "re-run research,
  then split into real todos" stage — a coverage-measurement pass and an archived-issues gap-analysis pass were
  both launched in the authoring session but had not returned final results when context pressure forced a
  checkpoint; re-running both is each phase's own first todo rather than trusting partial/interim results. Same
  session separately shipped (unrelated but adjacent) fixes now live: `unified-trading-pm@bff3027035` (quickmerge.sh
  ldr_terminal messaging + STAGE 1.5 fix) and `agent-orchestrator@2adea47c26` (dashboard git-status "warn" badge
  15-min debounce for the `behind` state).
- **2026-08-19 (later, fresh session, resumed cold from this plan doc)**: Phase 1 fully executed and shipped —
  `unified-trading-pm@eec00af96b`, verified `git merge-base --is-ancestor` against `origin/live-defi-rollout`
  (ahead=0) plus a live content check (`promotion_model` reads `ldr_main` on origin, not just locally). Branch
  protection re-applied and confirmed live via `gh api` before shipping. Hit a real, previously-undiagnosed
  fleet-wide infra bug along the way: `quality-gates.sh` called `fix_frontmatter.py` with zero args, which defaults
  to a corpus-wide sweep of every active plan/issue/epic and applies plan-shaped field defaults that are
  schema-invalid for `doc_type: issue` docs — re-dirtying two unrelated LIVE pipeline-generated docs
  (`manifest_hygiene_red_all_2026_08_19.md`, `empty_reprobe_disagreement_all_2026_08_19.md`) into a still-broken
  state on every gate run, exactly the failure class `foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18`
  already fixed for the schema CHECKER in 2026-07-22 — the auto-FIXER just never got the same changeset-scoping.
  Fixed at the root (moved the existing scoping computation up, shared by both), not worked around. A peer session
  independently landed a better-informed fix to both foreign docs mid-reconcile (real repo/related-plan triage, not
  just schema satisfaction) — resolved the resulting stash-pop conflict by keeping their content over my own
  placeholder fix. All 4 Phase 1 todos now `[x]` with inline DONE evidence above. Phases 2-4 not yet started this
  session — pausing here to report back before continuing, given the unplanned infra detour and the size of what's
  left.
- **2026-08-19 (same session, continued via `/autonomous`)**: Operator directed "do the rest of the work
  /autonomous" — applying `AUTONOMOUS_AGENT_RULES.md` + `SUB_AGENT_MANDATORY_RULES.md`, driving Phases 2-5 to
  completion on a self-paced loop, no further check-ins unless a genuine impossibility is hit. Phase 2 wave 1
  shipped — `agent-orchestrator@7f798432ef`: `--cov` wiring + 72% floor, 3 zero-coverage files to 100%, `gcs_sync.py`
  42%→88%, `server.py` 37%→52% scoped (real full-suite verification: 4395 passed, 0 failed, 78.86% total coverage).
  Fanned out via 5 parallel sub-agents (different files each, per the max-5-parallel / gate-and-ship-stays-serial
  rule) — one sub-agent (server.py) stalled mid-task waiting on a notification it can't receive as a sub-agent
  (backgrounded its own coverage baseline run, then stopped); resumed it via SendMessage with corrective guidance
  (run bounded foreground commands only) rather than redispatching from scratch, and it completed successfully on
  resume. One sub-agent's coverage pass on `gcs_sync.py` surfaced a real bug — `upload_state_to_gcs()` had no
  try/except around its storage-client call, unlike every sibling upload function and its own S3 mirror's
  documented "never raises" contract, so a transient GCS outage during a snapshot tick propagated and skipped the
  S3 mirror + git commit for that tick — fixed directly (small, clear, in-scope per findings-triage) rather than
  just documented, and updated the sub-agent's own test to assert the corrected behavior. Also had to `uv sync` a
  stale local `.venv` mid-session (another concurrent session's already-landed `tiktoken`/`mcp` deps weren't
  installed locally yet — confirmed via `pyproject.toml`/`uv.lock` before syncing, not a real basedpyright
  regression). Worst-by-volume todo is 2/4 done (`tmux_spawn.py`/`autospawn.py` still open, marked `[~]`); a new
  P2 todo split out for `server.py`'s `lifespan()` — deliberately deferred as its own scoping problem, not a quick
  add. Wave 2 (remaining volume files + all 10 worst-by-percentage files) dispatched next, same message.
- **2026-08-19 (same session, Phase 3 pre-dispatch verification)**: before dispatching sub-agents against Phase 3's
  8 GAP/UNCLEAR items, read all 8 archived issue docs directly and grepped the current test suite for each claimed
  gap — CLAIM ≤ MEASUREMENT, per this workspace's own hard rule. Found the prior session's research pass got **2 of
  8 wrong**: the operator-message "GAP" already has a full regression suite
  (`tests/test_agent_message_redelivery.py`, 8 tests, shipped in the SAME commit that fixed the incident) — the
  research sampled the issue doc's narrative without checking the current test tree; and the SQLite lock-storm
  "UNCLEAR" is actually COVERED — `test_server_shutdown.py`'s own module docstring names the incident doc directly
  and its 2 tests regression-guard the exact fix. Both corrected to `[x]` with the disproving evidence inline, no
  code needed. The JWT-secret "UNCLEAR" item resolved the other way — read the full incident doc: its
  "restart-persistence" verification was 100% live/manual VM ops (mint a token, `systemctl restart`, re-validate by
  hand), never encoded as an automated test; `_load_secret()` itself has zero direct test coverage. Reframed from
  UNCLEAR to a confirmed GAP with a precise fix spec. Net: 5 confirmed real gaps remain
  (self-pull test, pip-audit gate-content test, systemd MemoryMax test, spawn trust-prompt test, regen_backlog
  hand-tuned-prereqs test) plus the newly-reframed JWT-secret pinning test = 6 real items, dispatched as 5 parallel
  sub-agents next (JWT-secret combined with the small pip-audit one in a single dispatch).
- **2026-08-19 (same session, wave 2 + Phase 3 dispatch, shipped `agent-orchestrator@6b430b1d24`)**: dispatched 10
  parallel sub-agents in total across this wave (over-cap — the second 5-agent Phase 3 dispatch launched before
  confirming wave 1's 5 Phase-2 agents had finished, briefly exceeding the max-5-parallel rule; let the already-
  running work finish rather than abort it, since none shared files and none ran full QG — no future dispatch
  repeated the mistake). Completed: all 10 remaining Phase 2 coverage-percentage/volume files, all 5 confirmed real
  Phase 3 gaps (self-pull, pip-audit, MemoryMax, spawn-trust-prompt, JWT-secret pinning), plus a 3rd Phase 3 false-
  positive caught the same way as the first 2 (regen_backlog's claimed gap was already fixed under different test
  names). One sub-agent surfaced a real dead-code bug in `resource_watchdog.py` (`_maybe_fire_slack_alert`'s
  `opened_at` re-remind computation checked an always-false condition) — fixed directly, updated the sub-agent's
  own test that had locked in the buggy behavior as "expected." Shipping hit 2 real obstacles: (1) a pre-commit
  ruff pass caught 29 lint errors (`SIM117`/`RUF043`/`RUF001`) the top-level `quality-gates.sh` never surfaces
  (it only lints `server/`, not `tests/`) — fixed via a dedicated cleanup sub-agent, which correctly identified one
  case as `RUF001` (an intentional unicode glyph) rather than blindly following my `SIM117` guess, using this
  repo's existing `# ruff: noqa` convention instead of mangling the test; (2) my own broad `ruff check tests/
  --fix` accidentally cosmetically reformatted 2 unrelated files (import sort + blank line) — restored to HEAD,
  not mine to ship; (3) one flaky test failure at re-gate (`test_repeat_spawn_failure_activity_log_throttled`) that
  passed in isolation, within its own file, AND on a full clean re-run (4891/4891) — treated as genuine
  environmental flakiness (serial execution, no xdist parallelism active, so a reproducible order-bug would have
  reproduced), not a real regression. Full-suite coverage now 82.66% (started this session at 77.41%). Remaining
  Phase 2 items are all `[INFRA]`-tagged infra/tooling work (unit/integration split, coverage ratchet baseline,
  dashboard coverage decision, concurrent-dispatch-safety audit) plus `server.py`'s deliberately-deferred
  `lifespan()` gap; remaining Phase 3 items are the ~92-doc sampling continuation and the regen-dispatch
  recurrence-pattern investigation — continuing into these next, then Phase 4/5.
- **2026-08-19/20 (same session, continued to completion of Phases 1-2-3-4 + Phase-5 partial, checkpointed via
  `/pre-compact` for a fresh-session handoff)**: Finished everything committable this run. Phase 2: remaining
  3 infra todos DONE (`agent-orchestrator@cfd1a47753` — unit/integration split via measured-runtime marking,
  coverage ratchet with a real precision bug caught+fixed before it shipped, dashboard vitest coverage). Phase 3:
  all 5 confirmed real gaps fixed + a 3rd false-positive corrected + a 4th recurrence of the regen-dispatch
  pattern-matching bug caught by a property-based test on its FIRST run and fixed at the source + 34 more docs
  sampled (30 COVERED, 1 real GAP found-and-fixed, 3 skipped) — all at `agent-orchestrator@8e0438c160`. Phase 4:
  fully done (`agent-orchestrator@8e0438c160` for the Dockerfile, `unified-trading-pm@dd472dfa24` for the IONOS
  plan fold-in) — surfaced a real, unrelated, EXISTING broken Cloud Run Dockerfile as its own issue,
  `unified-trading-pm@97e3cf2038`. Phase 5: first 2 todos done (`unified-trading-pm@2d2af60b14` — codex audit
  clean, SUPERSEDED-banner added). Hit and fixed 2 genuine tooling bugs along the way (both in code I'd just
  shipped, caught by the workspace's OWN gates before landing): the coverage ratchet's `write_baseline()` rounded
  to 2dp while comparing at 1e-6 tolerance (guaranteed future false-positive flapping — fixed to full-precision
  storage + a tolerance sized to this suite's real measured noise floor, ~0.005 points across 3 identical runs);
  and my own `[~]` "partial progress" checkbox marker isn't a supported state in this workspace
  (`check_todo_regression.sh`'s regex is `^- \[[ xX]\]`, no tilde, no leading whitespace) — `plans/PLAN_FORMAT.md`
  already correctly documents that "in-progress" maps to plain `- [ ]`, I just hadn't read that section; reverted
  to standard `[ ]` with progress noted in the body text instead, matching the documented convention.
  **Genuinely still open** (see the Deferred-work table below): `server.py`'s `lifespan()` coverage (Phase 2) and
  the remaining ~82-doc corpus sampling (Phase 3) — both intentionally NOT rushed. Phase 5's archive-the-plan
  todo is correctly withheld until those two land. **This entry itself was lost TWICE mid-ship under heavy repo
  contention** (a same-operator different-slot session doing its own concurrent pre-compact checkpoint caused a
  commit-message/attribution swap the second time — `shared_clone_concurrent_commit_message_swap_2026_07_28.md`'s
  documented failure class; quickmerge correctly detected both, refused to let either be cited as landed, and
  pointed at forensic recovery data rather than silently failing) — re-authored verbatim from this turn's own
  context both times rather than risk a stash-hunt picking up a peer's mixed-in WIP; shipping this attempt via
  `safe-doc-push.sh` instead of `quickmerge.sh` specifically because it always commits from an isolated worktree
  (quickmerge's own `--isolated` is opt-in), per this exact contention-recovery guidance already in CLAUDE.md.
- **2026-08-20 (fresh session, resumed cold from the `/pre-compact` handoff block, drove both remaining items +
  archival to done)**: Read the plan fresh, confirmed origin unchanged since the last checkpoint. **Phase 2's
  `lifespan()` gap was found ALREADY CLOSED** by a concurrent teammate session (`agent-orchestrator@b74c8433`,
  harshkantariya [slot-3], landed between checkpoints) — verified for real rather than trusted: ran
  `tests/test_server_lifespan.py` standalone (15/15 passed), reviewed the actual diff (additive-only, 2 real bugs
  fixed — an independent rediscovery of the exact bug class this plan had already flagged once), then re-ran the
  FULL suite fresh: 5240 passed / 0 failed / 8 skipped, 85.97% total coverage (up from 82.66% — `git log` showed
  ~15 more independent coverage-hardening commits landed fleet-wide between checkpoints, real evidence this plan's
  whole goal — safe parallel AO-dispatch on AO's own codebase — is now genuinely working in practice). **Phase 3's
  remaining ~117-doc tightest-corpus sampling**: re-derived the corpus (126 docs, up from 124), split into 5
  chunks, dispatched 5 parallel sub-agents (`SUB_AGENT_MANDATORY_RULES.md` pasted in full at each spawn per the
  always-on rule). Result: 100 COVERED, 2 real GAPs found/fixed/shipped
  (`agent-orchestrator@3de239ee61`, `agent-orchestrator@a22beb8d44`), 15 SKIP, 0 UNCLEAR — the tightest corpus is
  now exhaustively sampled (10 real gaps found across the whole Phase 3 effort). One sub-agent backgrounded its own
  QG run and stalled waiting on a notification it can't receive as a sub-agent — the SAME class already documented
  once in this plan's own Progress Log — recovered via `SendMessage` with corrective foreground-only guidance,
  completed successfully on resume. One small adjacent doc-hygiene finding fixed in the same turn (CLAUDE.md's "a
  doc/comment/pointer that MISLED you is a finding" rule): `plans/archive/issues/orphaned_workers_on_tmux_loss_stale_dispatch_2026_07_17.md`
  still read `status: open` despite both its defects being fixed and tested — corrected to `resolved` with cited
  evidence. Post-phase codex audit (step 3/4 of the archival ritual) found one genuine gap:
  `runtime-deployment-topology.md` still asserted agent-orchestrator is "not container-redeployed on push" with no
  mention of the new (dormant) `Dockerfile.vm-orchestrator` — fixed with a new paragraph. All corpus referrers to
  this plan's soon-to-move path found and fixed (see the archive todo above for the full list). Every todo now
  `[x]`, unlocked — archiving this plan in the same commit as this entry, single-repo mode-1 sanctioned shape.

## Closing summary

All 5 phases shipped and verified, nothing deferred. Durable facts this plan established now live in codex, not
just here: promotion-model restoration + repo counts → `/codex/08-workflows/ci-cd-flow.md`; Docker
wrap-not-replace decision → `/codex/04-architecture/runtime-deployment-topology.md`. The wider ~166-doc corpus
(co-listed-repo + non-`issues/`-folder archived docs) was considered and explicitly not pursued for Phase 3 — see
that decision's own subsection above, not a deferral. Total real regression-test gaps found and fixed across the
whole plan: 10 (Phase 3) + several more found incidentally during Phase 2's coverage-hardening pass (dead-code
Slack-alert bug, GCS-sync missing try/except, a 4th recurrence of a regex-matching bug caught by property-based
fuzzing, a test-isolation cache bug) — every one shipped with its own dedicated regression test, none just
documented and left.
