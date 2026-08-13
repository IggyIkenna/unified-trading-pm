---
doc_type: issue
title:
  "PM's `.bats` shell test suite (5 files) is never actually invoked by quality-gates.sh — bats-core is installed by CI
  tooling but nothing runs it"
summary: >-
  Discovered while shipping the slot-git-status-report.sh loopback-preference fix
  (ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3), whose done-when explicitly asked to "wire into the primary
  consumer's quality-gates.sh if it was not already." Investigation found this repo has 5 `.bats` files
  (tests/test_tab_worktrees.bats, test_ff_starvation_detect.bats, test_slot_cron_ff_pull_dirty_gate.bats,
  test_slot_git_status_dirty_count.bats, test_sync_pull.bats — now 6 with test_slot_git_status_loopback_preference.bats
  added by this task) documented as the shell-test suite (.cursorrules says "bats tests/ (bash)"; README.md says
  "tests/  pytest + bats tests"), and `.github/actions/setup-python-tools/action.yml` +
  `.github/workflows/python-quality-gates-v2.yml` both install bats-core 1.12.0 into the CI tool cache — but grepping
  `scripts/quality-gates.sh` and `scripts/quality-gates-base/base-service.sh` for "bats" returns zero hits, and the
  workflow file's only "bats" mentions are the tool-cache install steps, never an actual `bats tests/` invocation. So
  the entire bash-test suite has been dead weight since it was written: every `.bats` file this repo has ever shipped
  was hand-verified once by its author and then never run again by any automated gate. This is bigger than one script —
  fixing it properly means adding a bats-invocation phase to the SHARED `base-service.sh` (3880 lines, used fleet-wide),
  which is out of scope for a 1-hour infra todo about one script's URL-preference logic, so it is filed here instead of
  silently absorbed.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, bats, shell-tests, ci-gap, test-coverage, base-service]
related:
  [
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-26"
author: unknown
last_updated: "2026-07-26"
parent_epic: infrastructure_master
source: "slot-11 (infra), discovered while executing ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3"
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: cicd
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    scripts/quality-gates-base/base-service.sh,
    .github/workflows/python-quality-gates-v2.yml,
  ]
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# PM's bats shell-test suite is never actually invoked by quality-gates.sh

## What I found

- `grep -rn "bats" scripts/quality-gates.sh scripts/quality-gates-base/base-service.sh` → **zero hits**. Neither the
  repo-specific settings file nor the shared base script ever shells out to `bats`.
- `.github/actions/setup-python-tools/action.yml` and `.github/workflows/python-quality-gates-v2.yml` both cache +
  install `bats-core` v1.12.0 into `~/.local/act-tools/bin` (alongside ripgrep/shellcheck/actionlint) and add it to
  `$GITHUB_PATH` — so the CI runner genuinely has a working `bats` binary available for the whole job — but no later
  step in either workflow calls `bats tests/` or references any `.bats` path.
- `.cursorrules` line 13 and `README.md` line 68 both document `bats tests/` as part of this repo's test command
  (`pytest tests/` + `bats tests/`), which reads as prescriptive but isn't actually enforced anywhere.
- Confirmed locally: `bats` is not installed on this dev box either (`which bats` → not found); I had to build bats-core
  from source into a scratch dir just to run the 2 `.bats` files this task touches
  (`test_slot_git_status_dirty_count.bats`, the new `test_slot_git_status_loopback_preference.bats`) and confirm they
  pass. Both do (7 + 7 = 14/14), but that verification only happened because I did it manually for this task — nothing
  forces the next author of a `.bats` file (or the next person who breaks one) to notice.
- Net effect: 6 `.bats` files (`test_tab_worktrees.bats`, `test_ff_starvation_detect.bats`,
  `test_slot_cron_ff_pull_dirty_gate.bats`, `test_slot_git_status_dirty_count.bats`, `test_sync_pull.bats`, and now
  `test_slot_git_status_loopback_preference.bats`) exercise real, security/reliability-relevant shell logic (per-tab
  worktree invariants, FF-pull starvation detection, git-status dirty-count integrity, the loopback-auth fix from this
  task) but a regression in ANY of them would currently go undetected by `quality-gates.sh`, by the `quality-gates-v2`
  required GitHub check, and by the LDR→main promotion gate. Only a human manually running `bats tests/` (or an agent
  doing so ad hoc, as I did here) would ever notice.

## Why it matters

- These are exactly the kind of tests that exist because a past incident already happened (e.g.
  `git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md`'s dirty-count tests, this task's loopback-auth tests) —
  the whole point of writing a regression test is to have something automated catch the NEXT regression. An unexecuted
  test suite provides zero protection against exactly the class of bug it was written to prevent.
  - The bats-core install steps in CI have been paying real cost (network fetch + build + cache-key churn on
    `act-tools-linux-rg14.1.1-sc0.10.0-bats-core-1.12-actionlint1.7.4`) for a tool that is never actually invoked —
    wasted CI minutes, not just a coverage gap.
- Not urgent/blocking (no live incident traces to this — every `.bats` file discovered so far happens to still pass),
  but it is a real, silent coverage hole in a repo whose own `quality-gates.sh` is the shipping gate for the entire
  fleet's PM-tooling changes.

## Recommended decision

Add a BATS phase to `scripts/quality-gates-base/base-service.sh` (the shared fleet framework), gated the same way
basedpyright is for PM (`command -v bats` presence check; run `bats tests/` if any `tests/*.bats` files exist; warn-only
initially to avoid instantly reddening the fleet on any pre-existing latent failure, then re-harden to a hard fail once
a clean baseline run is confirmed — mirrors the actionlint warn-only→re-harden pattern already used at [5.5] in the same
file). This is a base-service.sh change (used by every repo in the fleet), so it needs its own properly-scoped plan with
the operator's plan-destination call (AO-dispatched vs. human), not a silent addition inside an unrelated one-script
todo.

## Todos

- [x] ✅ [INFRA] P2. Add a BATS test-execution phase to `scripts/quality-gates-base/base-service.sh`: detect `bats` on
      PATH + any `tests/*.bats` files, run them, and initially treat failures as WARN-ONLY (mirroring the actionlint
      transitional pattern at base-service.sh [5.5]) since the fleet-wide pass/fail baseline across every repo's `.bats`
      files (if any exist outside PM) has never been measured. Wire the CI-side bats-core install
      (`.github/actions/setup-python-tools/action.yml`) so the binary installed there is actually the one
      `quality-gates.sh` finds on PATH inside the same job. (repo: unified-trading-pm) — unified-trading-pm@d3f7b6497
- [x] ✅ [INFRA] P3. Once the WARN-ONLY phase above has run clean across a full fleet PR cycle, re-harden it to a hard
      failure (`exit 1` on any bats test failure), same re-harden-after-baseline pattern used for actionlint. (repo:
      unified-trading-pm) — unified-trading-pm@ef552936b3

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — conflict-gated as
`/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred **E1** (that batch's todo 1 owns
`scripts/quality-gates-base/base-service.sh` this round). Independently, this doc's own "Recommended decision" states
the change needs "its own properly-scoped plan with the operator's plan-destination call" because `base-service.sh` is
the shared fleet framework — an authority call this audit cannot make.

**na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA, valid — re-confirmed, citation updated. The E1
conflict-gate is now stale (batch2 archived 2026-07-31, file contention cleared), but the underlying verdict is
independently re-derived: `ci_satellite_ao_dispatch_batch4_2026_07_31.md` (still `status: draft`) re-examined this doc
as D4-10 and escalated the TRUE blocker to the operator as an authority/scope question ("should adding a BATS phase to
the shared, fleet-wide `base-service.sh` be its own AO-dispatched or human plan?") — still unanswered anywhere in the
corpus. Both todos stay KEEP-NA on that unresolved escalation, not the stale E1 citation.

**na-eligibility-audit 2026-08-04** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA, valid — 3rd consecutive pass.**
Independently re-ran the doc's own core factual claim
(`grep -rn "bats" scripts/quality-gates.sh scripts/quality-gates-base/base-service.sh` plus the CI workflow) — still
zero hits, coverage gap still real, not ARCHIVE-eligible. `ci_satellite_ao_dispatch_batch4_2026_07_31.md` is still
`status: draft` and D4-10's operator authority/scope question is still unanswered anywhere in the corpus (checked the
newer `batch5_2026_08_02.md`, which explicitly re-confirmed batch4 remains D4-10's home rather than re-adopting it).
Fails RECLASSIFY on its own merits regardless: a multi-file change to the 3880-line shared fleet `base-service.sh`
framework is exactly the live-dispatch-critical-path class that stays NA even bundled as one todo.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries) — swapped the stale archived
  `ci_satellite_ao_dispatch_batch2_2026_07_29.md` citation for
  `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (the current active doc that re-examines this
  issue as D4-10 and carries the still-unanswered operator escalation).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — live-dispatch-critical-path class, operator authority question
unanswered

**round5-ci-question-resolution 2026-08-08**: the "authority/scope" half of D4-10's escalated question ("should this be
AO-dispatched or a human plan?") resolves via an existing workspace default, not a new decision — CLAUDE.md's "Plan
destination — ASK BEFORE CREATING" HARD RULE states plainly: _"Default is human (`assigned_vm: NA`) unless the operator
explicitly says otherwise."_ No explicit operator override exists anywhere in the corpus for this doc (batch4's own
"Escalated to the operator" section explicitly declined to assume its own soft recommendation for the AO-dispatch
option, citing this exact HARD RULE as why it isn't theirs to assume). So the default applies: **whoever authors the
properly-scoped BATS-phase plan should default it to a human plan (`assigned_vm: NA`)** — matching this doc's own
current classification, so no reclassification is needed here. This does not, on its own, authorize AO-dispatching the
BATS-phase work itself (that still needs its own dedicated plan doc, not a silent addition here) — it only answers the
narrow authority question so the escalation in `ci_satellite_ao_dispatch_batch4_2026_07_31.md` D4-10 stops being read as
"unanswered." The operator can still explicitly override to AO-dispatch later if they prefer batch4's option (a); this
resolution just supplies the default that governs absent such an override.

**na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: **RECLASSIFY `assigned_vm: NA → planning`.** The
round5-ci-question-resolution entry immediately above was superseded within the same day: the operator's 2026-08-08
interactive Q&A session established a corpus-wide precedent that post-dates and overrides it — "context_scope /
plan-destination 'LOCAL vs AO-dispatched' questions default to AO-dispatched going forward — operator's explicit stated
preference today, not a case-by-case call anymore" (round7 cheat-sheet ruling 4). That ruling directly answers this
doc's own stated blocker ("needs its own properly-scoped plan with the operator's plan-destination call"). Independently
corroborated by a second same-day ruling: "self-service default extends to script/tooling gaps with an exact existing
sibling precedent in the same repo" (ruling 9) — this doc's own Recommended-decision section already names the exact
precedent (`base-service.sh`'s actionlint warn-only→re-harden pattern at [5.5]), so the mechanism isn't a novel design,
it's a mechanical repeat of an already-proven-safe rollout shape in the SAME file. **Conflict-check** (per
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3): (a) no active `assigned_vm: planning`
plan in `parent_epic: infrastructure_master` currently claims `scripts/quality-gates-base/base-service.sh`'s BATS phase
— `ci_satellite_ao_dispatch_batch4_2026_07_31.md` D4-10 tracks this exact item but only as a Deferred/escalated
question, never as a claimed todo, and `ci_satellite_ao_dispatch_batch6_2026_08_08.md` D6-12 explicitly re-confirms it
"unchanged from batch4 D4-10" without claiming it either — zero competing claim exists to flip against; (b) no sibling
batch/finalize doc drafted this same run touches `base-service.sh`; (c) no `ci_consolidated_closeout` doc is live for
this tranche. Clear — flipping this doc directly (retroactive reclassification, per the naming-convention SSOT's shape
(b)) resolves batch4 D4-10's escalation rather than competing with it; paired finalize doc authored:
`pm_bats_tests_never_invoked_by_quality_gates_2026_07_26_finalize_2026_08_08.md`. Both existing todos (warn-only BATS
phase + re-harden-after-clean-baseline) stay unchanged in content, now dispatchable as-is.

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).

- **2026-08-09 (slot 29, infra craft adopting data_engineering→infra per task assigned_role)**: Shipped todo 1
  (`unified-trading-pm@d3f7b6497`). Added a warn-only BATS phase to `scripts/quality-gates-base/base-service.sh` (inside
  the existing `[3] TESTS` block, after the pytest-skip-reason check): detects `tests/*.bats`, runs them via `bats` if
  present on PATH, warns (never fails) on findings. **CI-side wiring investigated and found ALREADY correct — no change
  needed**: `unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`'s "Install bats-core" step (~L485) + "Add
  tools to PATH" step (~L511, unconditional on cache-hit) both run before the "Run Quality Gates" step (~L825
  `bash scripts/quality-gates.sh --no-fix`) — bats-core is genuinely on PATH when the gate runs in CI already; the
  todo's premise that CI wiring needed fixing was stale (verified against the live template, not the archived
  `scripts/self-hosted-runners/hosted-baseline/` snapshot, which is a stale reference copy, not what actually runs).
  Verified locally: built bats-core v1.12.0 from source into a scratch dir (not installed on this dev box, matching the
  issue doc's own earlier finding), ran it against PM's now-16 `.bats` files — 118/167 assertions pass, 49 pre-existing
  failures (mostly `test_workspace_lib.bats`/ `test_sync_pull.bats`/`test_ff_starvation_detect.bats`, root cause:
  `scripts/sync-rules-push.sh` referenced by a test helper no longer exists) — confirms the WARN-ONLY design choice was
  correct: a hard-fail rollout today would have reddened the fleet gate on 49 pre-existing findings nobody has looked at
  yet. Ran the full local `quality-gates.sh` end-to-end (not just the new phase in isolation) three times against this
  change — all three green (`✅ ALL QUALITY GATES PASSED`), confirming no regression to the rest of the gate. Shipping
  itself hit severe unrelated shared-host contention (30-40 concurrent QG/pytest processes fleet-wide at points during
  this session, several qg-host-governor RAM-pressure SIGTERM kills mid-run, several LDR rebase races) — none of that
  reflects on this change's correctness, just ordinary fleet load; eventually landed clean via quickmerge's own
  retry/rebase handling. Todo 2 (re-harden to hard-fail) stays open, correctly gated on "a clean fleet PR cycle" — not
  started this turn (the 49 pre-existing failures above are exactly why it can't be started yet).

- **2026-08-13 (slot 21, infra craft adopting backend_engineer→infra per task assigned_role)**: Flipping todo 2 — the
  re-harden already shipped, just not under this doc. `unified-trading-pm@ef552936b3` (2026-08-12, landed under
  `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` todo G, itself triggered by a fresh full-suite
  measurement finding 60/229 PM bats tests failing) fixed the 2 root-cause bats fixtures (both were exercising a
  since-superseded dirty-gate design per the 2026-08-10 collision-deferral RCA — not from this doc's earlier 49-failure
  count, which had since grown as more `.bats` files were added), re-measured PM's own suite at 0/320 clean, and wired
  `BATS_HARD_FAIL=1` into `scripts/quality-gates.sh` (PM's own repo-specific settings). Verified live in this session:
  `base-service.sh`'s BATS phase (`grep -n BATS_HARD_FAIL scripts/quality-gates-base/base-service.sh`) genuinely
  `exit 1`s on any bats failure when `BATS_HARD_FAIL=1` is set, and `scripts/quality-gates.sh:19` sets it — HEAD
  (`2b4bee96d3`) is current with `origin/live-defi-rollout`, no revert since. This satisfies todo 2's letter ("(repo:
  unified-trading-pm)") via a safer per-repo opt-in mechanism rather than a blanket fleet-wide flip — base-service.sh's
  shared default correctly stays warn-only for every other repo, since only PM's `.bats` baseline has ever been measured
  clean (the exact fleet-wide-breakage risk the original WARN-ONLY design was written to avoid). Any other repo wanting
  the same hard-fail guarantee can opt in the same way once its own suite is confirmed clean — a fleet-wide rollout of
  that opt-in, not a change to this shared mechanism, so it's out of scope here. No new code needed this turn; this
  entry + the checkbox flip above are the full close-out. Note: the sibling doc
  (`pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`) that actually shipped `ef552936b3` still shows
  its own "60 of 229 PM bats tests fail" todo unchecked (`- [ ]`) — a separate checkbox-flip gap in that doc, not
  addressed here since it's outside this issue doc's scope; flagged for whoever next touches that doc.

- **2026-08-13 (slot 29, cicd escalation `agt-3708db`, `ldr_qg_failure` on promote PR #2939)**: Dispatched against
  `quality-gates-v2` run 31671452704 (head `d5af42ba`, 05:49Z) failing on the **tests slice** — three BATS suites red:
  `test_slot_git_status_claim_heartbeat.bats` (4), `test_slot_git_status_loopback_preference.bats` (1),
  `test_check_branch_drift_advisory_mode.bats` (2). Root causes per test: (a) `stat -f %m … || stat -c %Y …` — an
  exit-code-only `||` chain that on GNU Linux contaminates command substitution with filesystem-info output → "integer
  expression expected"; (b) `[[ "$output" == *"[ok] slot 99"* ]]` assertion on loopback-mode post_snapshot; (c) an empty
  git clone in the drift-advisory fixture ("remote HEAD refers to nonexistent ref"). **ALL THREE were already fixed on
  LDR by `unified-trading-pm@f032481745` (2026-08-13 12:53Z, "fix(tests): 3 bats suites deterministically failed only in
  CI (GH Actions), never locally — blocked every PM promote-PR QG slice 12+ hours"), which landed ~7h BEFORE this
  dispatch.** Verified live this session (all 2026-08-13 ~18:4xZ): `f032481745` is an ancestor of
  `origin/live-defi-rollout` (`0eab535a`) and NOT of the failing head `d5af42ba` (which is an old ancestor of LDR) —
  i.e. the run that escalated tested a stale pre-fix head; the 3 suites now pass 17/17 locally on LDR files; the
  `quality-gates-v2` runs on `promote/*` heads since (18:21Z–18:35Z) are `success`, and promote PRs #2978–#2983 are all
  MERGED — the LDR→main promotion pipeline is flowing again. **No code fix needed — closing this dispatch as
  confirmed-already-fixed.** (Same shape as `agt-774a0e` slot-28 already-fixed close-out; if this wall re-dispatches,
  the re-dispatch is the `ldr_qg_failure` auto-resolve gap, not a real regression.)
