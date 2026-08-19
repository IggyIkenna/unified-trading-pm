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

- [ ] [INFRA] P0. **The 70% floor is declared but NOT actually enforced — fix the gate itself first.**
      `scripts/quality-gates.sh` (~line 115) runs `python -m pytest tests/ -q -p no:cacheprovider` with **no
      `--cov` flag at all** — `pyproject.toml`'s `fail_under = 70` never gets checked by the automated gate,
      coverage only reflects reality when someone runs it by hand (as this session's research pass did). This is
      the single highest-value Phase 2 fix: wire `--cov=server --cov-report=term-missing --cov-fail-under=70` (or
      the calibrated new floor from the next todo) into the actual QG pytest invocation. Done-when: a deliberately
      under-70%-covering change fails `quality-gates.sh` locally.
- [ ] [BACKEND] P1. **Raise the enforced floor from 70% toward the measured 77.41%, incrementally** — e.g. 72-73%
      as a first milestone, not straight to the current number (leaves zero regression headroom) and not an
      arbitrary round figure. Wire into the same `--cov-fail-under` flag as the todo above (one combined change if
      convenient). Done-when: QG passes at today's level and fails on a real regression below the new floor.
- [ ] [BACKEND] P1. **Zero-coverage files — the highest-value gap, not the lowest-percentage one.**
      `server/creds_env_poller.py` (0.00%, 106 lines), `server/kimi_balance.py` (0.00%, 46 lines),
      `server/kimi_balance_poller.py` (0.00%, 67 lines) have NO tests at all, not just weak ones. One todo per
      file: write a real test suite (not a smoke test) for each.
- [ ] [BACKEND] P2. **Worst-covered-by-percentage, split per file** (each gets its own todo when picked up, don't
      batch): `server/routes/vms.py` (20.34%, 177/237 missing), `server/gemini_translation_smoke.py` (31.21%,
      147/228), `server/routes/ops.py` (33.59%, 67/110), `server/routes/resource_watchdog.py` (34.58%, 57/93),
      `server/notifications/telegram.py` (37.96%, 68/115), `server/fleet_slot_snapshot_poller.py` (40.00%, 25/51),
      `server/routes/repo_blockers.py` (41.27%, 29/55), `server/worker_liveness/_respawn.py` (42.28%, 108/192),
      `server/auto_park_reconcile.py` (43.59%, 29/58), `server/worktree_setup.py` (45.33%, 31/63).
- [ ] [BACKEND] P1. **Worst-covered-by-VOLUME, prioritize these over the percentage list above** — concurrency/
      dispatch-critical, highest absolute missing-line count, exactly what multi-agent-on-itself dispatch stresses
      hardest: `server/server.py` (37.69%, 325 lines missing), `server/gcs_sync.py` (42.45%, 238 missing),
      `server/tmux_spawn.py` (69% cov but 230 missing — large file, worth it despite a decent %),
      `server/autospawn.py` (83% cov but 216 missing — same reasoning).
- [ ] [INFRA] P2. **Give the suite a real unit/integration split.** All 274 test files sit flat under
      `tests/test_*.py` — no subdirectories, and the existing `unit`/`integration`/`smoke`/`host_load_sensitive`
      pytest markers are each used in only ~1 file, so there is no cheap way to run a fast subset (confirmed
      live: a full-coverage run took 421s with no faster alternative available). This is also why Phase 2's own
      coverage-measurement research pass got stuck twice this session waiting on a full run it had no way to
      shrink. Done-when: a `pytest -m unit` (or equivalent) run completes in well under a minute and covers the
      bulk of fast, non-integration logic.
- [ ] [INFRA] P2. **No coverage baseline/ratchet file exists** (repo-wide grep for one came up empty) — once the
      floor-raising todo above lands, add a shrinking-ratchet baseline (mirrors this workspace's existing pattern
      elsewhere, e.g. `line_caps_baseline.yaml`) so coverage is enforced to only ever go up, not just clear a
      static floor.
- [ ] [INFRA] P3. **Dashboard (`dashboard/`) has no coverage measurement at all** — 19 vitest `*.test.ts` files run
      with no coverage provider configured, plus a separate 36-spec Playwright e2e layer. Lower priority than the
      Python backend (per CLAUDE.md's UI rule, dashboard tests are already tsc/ESLint/vitest/Playwright-only, no
      Python gate applies) but worth a follow-up decision on whether a vitest coverage number is worth adding.
- [ ] [INFRA] P2. **Audit whether `quality-gates.sh` needs a check specific to concurrent-multi-agent-on-itself
      risk** — e.g. no two open AO tasks targeting the same agent-orchestrator file (mirrors this workspace's own
      "concurrent todos MUST touch different files" plan-authoring rule, but for AO's OWN dispatch against its OWN
      code — a structural risk unique to AO working on AO). State whether the generic multi-agent-safety machinery
      already covers this or it's a genuine new gap.

## Phase 3 — Regression tests for agent-orchestrator's own incident history

**RESOLVED with real data, not a placeholder** — a research pass this session sampled 63 of an estimated 155
archived agent-orchestrator issue docs (the tightest high-confidence corpus: single-repo `repos: [agent-orchestrator]`
docs living in an `issues/` subdirectory; ~403 archived docs total mention agent-orchestrator at all, most of them
feature-build plans not incident postmortems). **Coverage is unusually strong already** — AO's suite frequently cites
the issue-doc filename directly in a comment above its regression test — but 7 real GAPs and 2 UNCLEAR verdicts
came out of the sample. ~92 more docs in the tightest corpus, plus ~36 co-listed-repo docs and ~130 non-`issues/`
archived docs, were not yet sampled.

- [ ] [BACKEND] P1. **GAP: operator→agent chat messages silently dropped** — delivery was marked on POLL/drain, not
      on the agent's actual reply (`ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md`). New
      `tests/test_operator_reply_delivery_ack.py`: assert a chat message stays "undelivered" until the agent's next
      `/poll` is followed by a recorded reply, not merely drained.
- [ ] [INFRA] P1. **GAP: `ao-self-pull.sh` silently stalled 2+ hrs** — untracked `accounts.json` backup files
      blocked `git pull --ff-only` (`ao_self_pull_stalled_by_untracked_backup_files_2026_07_29.md`). No test file
      exists for this script at all — add a shell-level (or subprocess-wrapped pytest) test asserting the script
      clears/ignores untracked-file blockers and alerts on stall.
- [ ] [INFRA] P2. **GAP: `quality-gates.sh` never ran `pip-audit`** — silent gap in the gate itself
      (`agent_orchestrator_pip_audit_ungated_2026_07_30.md`). `tests/test_quality_gates_script_contents.py`: assert
      `scripts/quality-gates.sh` contains a `pip-audit`/`pip_audit` invocation — regression-guards the SCRIPT
      CONTENT so this can't silently drop out again, not just today's one-time fix.
- [ ] [INFRA] P1. **GAP: orchestrator's own systemd `MemoryMax` cap went stale vs. actual need** → full API outage,
      HTTP:000 on every endpoint (`orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`). Existing
      `test_tmux_spawn_memory_cap.py` covers a DIFFERENT subsystem (worker-spawned-process memory scoping) — add a
      test asserting the `orchestrator.service` unit's own memory cap tracks deploy-time sizing.
- [ ] [BACKEND] P2. **GAP: `/api/slots/<N>/spawn` silent-failed on an unhandled workspace-trust prompt** (3
      compounding defects, `orchestrator_spawn_tmux_silent_failure_2026_05_20.md`). Add to
      `tests/test_spawn_heartbeat_liveness.py`: spawn must fail LOUDLY, not silently, when the trust prompt isn't
      auto-dismissed.
- [ ] [BACKEND] P1. **GAP: `regen_backlog_from_plan.py` silently drops hand-tuned `prereqs.conditions` + priority
      tuning every regen cycle** (`backlog_regen_drops_handtuned_prereqs_2026_07_12.md`). Only a stray string match
      exists in `test_regen_backlog_from_plan.py`, not a real assertion — add explicit
      `test_regen_preserves_handtuned_prereqs_and_priority`.
- [ ] [DOC] P2. **UNCLEAR → resolve: SQLite lock-storm-triggers-stuck-shutdown causal chain**
      (`ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`) — `test_server_shutdown.py` exists but no
      keyword ties it to this specific causal chain; read both closely and either confirm COVERED or write the gap.
- [ ] [DOC] P2. **UNCLEAR → resolve: unpinned `ORCHESTRATOR_JWT_SECRET` invalidating every token on restart**
      (`orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md`) — `jwt_secret` tests exist
      but restart-persistence of the pinned secret specifically is unconfirmed; read closely and resolve.
- [ ] [INFRA] P3. **Sample the remaining ~92 docs in the tightest corpus** (single-repo `repos: [agent-orchestrator]`
      issue docs not yet read) plus a second pass on the ~36 co-listed-repo docs and ~130 non-`issues/`-folder
      archived docs (`plans/archive/2026_08/` in particular has undated-convention incident writeups outside the
      `issues/` subdirectory worth checking). Same COVERED/GAP/UNCLEAR method as above; split any new GAP into its
      own todo the way this pass's 7 were split, don't batch them into one vague "write more tests" line.
- [ ] [DOC] P3. **Investigate the recurrence pattern, not just the latest fix**: 3 of the sampled docs
      (`ao_backlog_regen_missing_self_declared_not_ao_eligible_guard_2026_08_14.md` and its two predecessors) are
      the SAME underlying regen-dispatch bug recurring 3 times — each fix landed a real test, but the pattern-
      enumeration approach itself (a regex/pattern list needing repeated widening) is the actual defect. Consider
      whether a property-based/fuzzed test (any self-declared-not-eligible phrasing, not an enumerated list) would
      close this class permanently instead of waiting for a 4th recurrence to widen the list again.

## Phase 4 — Containerize agent-orchestrator (Docker), cross-checked against the IONOS migration

Operator directive (same session, added after Phases 1-3 were already checkpointed): package agent-orchestrator to
run as a Docker container inside its VM, specifically to make cross-cloud migration easier. **This plan does not
own the cloud migration itself** — `/plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md` already tracks that
(added to this plan's `related:`) — but containerizing AO is directly relevant to it and must be cross-checked
against whatever that plan currently assumes about how AO is deployed/run.

- [ ] [INFRA] P1. **Read `ao_ci_aws_to_ionos_migration_2026_08_18.md` in full before designing the container build**
      — it may already assume a specific deploy shape (the existing `ao-self-pull.sh` root-cron + `systemctl
      restart` model this plan's Phase 1 confirmed is still current) that a container changes. State explicitly
      whether containerizing REPLACES `ao-self-pull.sh`'s restart mechanism or wraps it (e.g. the container still
      polls LDR internally and restarts its own process, vs. an external supervisor rebuilding/redeploying the
      container on each LDR push).
- [ ] [INFRA] P1. **Design + ship the Dockerfile/image-build workflow** for agent-orchestrator's server. Decide
      build trigger (same `push:[live-defi-rollout]` this plan's Phase 1 confirmed as AO's actual deploy signal, or
      a separate build-only trigger) and registry target (this fleet already has `image-build-gate.yml` precedent
      per Phase 1's semver-agent finding — check whether that's reusable or AO-specific). Done-when: an image
      builds successfully from a real LDR commit and runs the server correctly in a local/test container.
- [ ] [INFRA] P2. **Decide what "runs as a Docker container inside the VM" means for the EC2→IONOS migration
      specifically** — does containerizing make the migration strictly easier (portable image, same container
      runtime on either cloud) or does it need its own IONOS-side prerequisite (a container runtime installed,
      registry access from the new host)? Fold the answer into the IONOS plan itself, don't duplicate it here —
      this todo's done-when is "the IONOS plan's own todos reflect the container model," not new IONOS work here.

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

- [ ] [DOC] P1. **Post-phase codex audit** — once Phases 1-4 are shipped, do the standing "read the codex docs this
      plan depends on and check them against what actually shipped" pass named in CLAUDE.md's plan-authoring rules.
      Update any contract that changed, SUPERSEDED-banner anything invalidated.
- [ ] [DOC] P1. **Archive `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`'s live-state claims are now
      historical, not current** — it's already archived with a resolved banner, so no un-archiving needed, but add
      a one-line dated note at its top ("SUPERSEDED IN PRACTICE 2026-0X-XX by <this plan> — agent-orchestrator is
      ldr_main again") so a future reader doesn't mistake its "What changed" section for current state. Do this
      LAST, only once Phase 1 has actually shipped.
- [ ] [DOC] P0. **Archive this plan** once every todo above is `[x]` and unlocked — standard 6-step ritual, corpus-
      wide referrer-path fixup included.

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
