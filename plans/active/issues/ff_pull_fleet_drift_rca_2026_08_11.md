---
doc_type: issue
title: >-
  FF-pull fleet drift RCA — actor/detector collision divergence (fixed), one-off /done ran no clean gate (fixed), and an
  un-attributable multi-clone FF log that caused a false "cron is broken" diagnosis
summary: >-
  On 2026-08-10, 15 repos in slot 2 silently reached 206/113/109 commits behind over three days with no alert. Root
  cause was a rule mismatch: slot-cron-ff-pull.sh skipped on ANY confirmed tracked dirt, while ff-starvation-detect.sh
  only pages on `collision AND (behind>=N OR age>H)` — so non-colliding tracked dirt (one stale, never-committed
  `.github/workflows/semver-agent.yml` per repo, superseded upstream by the unified-trading-ci thin-caller dedup) froze
  every clone on every 5-minute tick while the watchdog stayed silent BY CONSTRUCTION. Both sides are now fixed: the
  actor skips only on a real collision, and the detector gained a cause-agnostic FF-BEHIND BACKSTOP that fires on lag
  alone. A third, independent gap found the same session — Class-B one-off /done ran NO clean-slot gate at all — is also
  fixed. Records one MISDIAGNOSIS for posterity so it is not re-chased: an apparent "the cron will not FF clean repos"
  defect was an artefact of FF log lines carrying no slot/clone identifier, with five clones of each repo reporting into
  one file.
status: open
nature: issue
asset_group: [infrastructure, ci]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ff-pull, fleet-drift, slot-worktrees, starvation, observability, ci-cd, agent-orchestrator]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-08-11
last_updated: "2026-08-11"
parent_epic: infrastructure_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Interactive session, 2026-08-10/11. Found while investigating why the VS Code source-control panel showed most
  workspace repos hundreds of commits behind origin.
---

# FF-pull fleet drift — RCA

## Symptom

15 repos in `.tabs/2` sat 206 / 113 / 109 / 98 / 82 … commits behind `origin/live-defi-rollout` for ~3 days. No alert
fired. The `ff-starvation-detect.sh` watchdog exists precisely for this and stayed silent throughout: the shared marker
dir held 17 `.stash-warn` markers and **zero** `.starved` markers.

## Root cause 1 — actor and detector disagreed on the skip rule (FIXED)

| Dirt shape             | `slot-cron-ff-pull.sh` (actor) | `ff-starvation-detect.sh` (detector) |
| ---------------------- | ------------------------------ | ------------------------------------ |
| untracked only         | proceeds (git arbitrates)      | n/a                                  |
| tracked, colliding     | `skip:dirty`                   | **STARVED** ✅                       |
| tracked, non-colliding | **`skip:dirty`**               | **silent** ❌                        |

The bottom row is the outage. Each repo carried one stale `.github/workflows/semver-agent.yml` — a never-committed
rollout artefact, made obsolete on 2026-08-06 when the workflows were deduped into `unified-trading-ci` as a
`workflow_call` reusable (origin's copy is a 47-line thin caller; the stale local copies were 1,126-line inlined
versions missing the 2026-08-08 char-limit fix). No incoming commit touched that path, so no FF was ever at risk — yet
every tick skipped, and the freeze is self-sustaining because a clone that cannot FF never stops being dirty.

**Fix**: the actor now defers confirmed tracked dirt to a new Step 5.5 (after `origin/<int_branch>` resolves) and skips
only on `dirty paths ∩ incoming diff`, mirroring the detector's own definition. `git merge --ff-only` still refuses any
genuine clobber, so safety is doubly held.

## Root cause 2 — every signal was keyed to a modelled cause (FIXED)

Nothing in the fleet pages on lag alone. **Fix**: `FF-BEHIND BACKSTOP`, a second detector verdict firing on
`behind >= FF_BEHIND_BACKSTOP_COMMITS` (75) **and** oldest-unpulled-commit age `>= FF_BEHIND_BACKSTOP_HOURS` (6),
regardless of dirty/collision/clean, and evaluated **before** the clean-tree exit that used to let a clean far-behind
clone leave silently. The age gate does the real work: this fleet can accumulate 152 commits in 2h, so a commit-count
threshold alone would false-fire constantly.

## Root cause 3 — Class-B one-off `/done` ran no clean gate at all (FIXED)

`done_slot` gates on a clean slot via `_enforce_done_clean_gate`, but delegates to `_done_one_off` and returns
immediately — and its docstring advertised "no task, **no gates**, no auto-dispatch". So `one_shot`/`scheduled` workers,
precisely the population that leaves generated digests, audit output and rollout artefacts behind, could complete and
free a slot while leaving uncommitted WIP. `tuning.done_require_clean` was already `default=True`; the gate simply was
never reachable from that path. **Fix**: the one-off path now calls the same gate with the same BEFORE-any-state-change
contract.

## MISDIAGNOSIS — do not re-chase (RESOLVED, no defect)

This session recorded, then withdrew, a claim that "after the repos were clean, three consecutive sweeps still did not
FF them." **There is no such defect.** FF log lines carry **no slot or clone identifier**, and five clones of each repo
(top-level + `.tabs/1..4`) write into one `/tmp/slot-cron-ff-pull.log`. The `skip:dirty` verdicts read at 19:25/19:30/
19:35 belonged to _other slots'_ still-dirty clones. Verified after the fact: slot-2 repos sat at `behind=0` with HEADs
that had moved 21–39 minutes earlier, i.e. the cron had been fast-forwarding them normally from the moment they were
clean.

A second withdrawn claim: the `*/5` crontab `git checkout origin/… -- scripts/dev/slot-cron-ff-pull.sh` was blamed for
destroying local edits. It cannot — it runs in the **top-level** clone only, and the in-script managed-file auto-clean
restores a file **only when byte-identical to origin**. The actual cause of three separate WIP losses that session was a
peer agent's `pre-reconcile quarantine` stash on the shared slot-2 checkout
(the `prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08` finding, which is itself still uncommitted) —
content was **not** recoverable from those stashes, nor from 89 dangling blobs.

`min-interval` was likewise cleared as a contributor: `cron-repo-min-interval.txt` throttles `unified-trading-pm` only
(900s), never the service repos.

## Todos

- [ ] [SCRIPT] P1. Add slot/clone identification to every `slot-cron-ff-pull.sh` log verdict (e.g. `slot-2/` prefix or
      the resolved `repo_key`). Five clones per repo currently report indistinguishably into one file, which is what
      made the misdiagnosis above possible and will do so again. This is the one genuinely open defect from this RCA.
- [ ] [OPERATOR] P2. Decide whether the `uv.lock` auto-clean should extend from "purely `version =` drift" to also cover
      `[package.metadata] requires-dist` / `provides-extras`-only churn (sibling metadata propagation, equally
      non-authoritative). Guard it on this repo's own `pyproject.toml` being clean, so an in-flight local dependency
      edit is never discarded. NOT done unprompted: getting it wrong silently reverts genuine dependency work.
      Deliberately do NOT add `--frozen`/`--locked` to `scripts/setup.sh`'s `uv lock` — that call is load-bearing (it is
      how a repo picks up sibling workspace bumps that never touch its own `pyproject.toml`).
- [ ] [OPERATOR] P2. 43 archived repos under `archive/` and `_archived/` still carry the stale inlined
      `semver-agent.yml` as uncommitted dirt. Harmless (not ff-pulled, not in CI) but it inflates every workspace-wide
      dirty-repo count and hid the live signal. Decide: bulk-clean or leave.
- [ ] [SCRIPT] P3. `ff-starvation-detect.sh` exits early on a detached HEAD (`[skip:detached]` in the actor). A detached
      clone can therefore drift unboundedly with no verdict from either side. Confirm whether that is intended.

## Progress Log

- **2026-08-10** — Discarded the 15 stale `semver-agent.yml` copies after verifying against origin and against the
  `unified-trading-ci` reusable workflow that they were strictly older (missing the 08-08 char-limit fix) and would
  revert a shipped refactor if committed. Hand-fast-forwarded 18 repos (instruments-service +206, features-service +113,
  execution-service +109, deployment-api +70); slot 2 returned to `behind=0`.
- **2026-08-10** — Root causes 1 + 2 fixed in `unified-trading-pm`; root cause 3 fixed in `agent-orchestrator`
  (`_done_one_off` clean gate + regression test). Verified: `bash -n` both scripts; 10/10 unit cases on the collision
  matcher (rename source vs destination, substring and prefix non-matches, staged add, delete, empty incoming); the
  backstop fires with its full payload on the age gate and stays silent at 152-behind/2h-old; AO 15/15 tests green.
