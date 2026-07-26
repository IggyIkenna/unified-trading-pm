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
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, bats, shell-tests, ci-gap, test-coverage, base-service]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
source: "slot-11 (infra), discovered while executing ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3"
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
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

- [ ] [INFRA] P2. Add a BATS test-execution phase to `scripts/quality-gates-base/base-service.sh`: detect `bats` on
      PATH + any `tests/*.bats` files, run them, and initially treat failures as WARN-ONLY (mirroring the actionlint
      transitional pattern at base-service.sh [5.5]) since the fleet-wide pass/fail baseline across every repo's `.bats`
      files (if any exist outside PM) has never been measured. Wire the CI-side bats-core install
      (`.github/actions/setup-python-tools/action.yml`) so the binary installed there is actually the one
      `quality-gates.sh` finds on PATH inside the same job. (repo: unified-trading-pm)
- [ ] [INFRA] P3. Once the WARN-ONLY phase above has run clean across a full fleet PR cycle, re-harden it to a hard
      failure (`exit 1` on any bats test failure), same re-harden-after-baseline pattern used for actionlint. (repo:
      unified-trading-pm)
