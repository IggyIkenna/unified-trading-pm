---
doc_type: issue
title:
  Claude Code assumes a ~200K window for DeepSeek and auto-compacts every DeepSeek worker at ~17% of its real 1M
  capacity
summary: >-
  DeepSeek V4-Pro and V4-Flash are 1M-context models (vendor spec, operator ruling 2026-08-10; confirmed by direct API
  probe — pro served 635,309 tokens in a single request, HTTP 200). Claude Code does not recognise the DeepSeek model
  string and applies a ~200K window instead, so it auto-compacts DeepSeek sessions at ~166-190K — roughly 17% of what
  the model can actually hold. Measured over 1,342 DeepSeek transcripts: 125 flash auto-boundaries (max preTokens
  190,798) and 22 pro auto-boundaries (max 259,441), while only 1 of 604 flash sessions and 0 of 756 pro sessions ever
  got past 468K. Every DeepSeek worker is therefore being compacted roughly 6x more often than necessary, and by the
  CLI's raw auto-summary rather than AO's cooperative /pre-compact checkpoint — so the fleet pays twice, in wasted
  re-priming tokens and in worse context handoffs. AO itself is now correct (it uses the 1M spec), so this is purely
  about the CLI's own belief.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, deepseek, cost, worker-lifecycle, context-probe]
related:
  [
    /plans/archive/issues/ao_deepseek_context_window_unknown_and_self_repoisoning_2026_08_10.md,
    /plans/archive/2026_08/issues/ao_deepseek_provider_model_telemetry_mislabeled_2026_08_06.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by: agent-orchestrator@ac9ba18 + agent-orchestrator@8f1a08ad53 + unified-trading-pm@dad266ff61
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Split out of ao_deepseek_context_window_unknown_and_self_repoisoning_2026_08_10 on its resolution (2026-08-10), which
  fixed AO's own window arithmetic but could not fix the CLI's.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_probe.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/accounts.py,
  ]
---

# The CLI assumes ~200K for DeepSeek and compacts it at ~17% of capacity

## What is established (do not re-litigate these)

| fact                                                   | evidence                                                                |
| ------------------------------------------------------ | ----------------------------------------------------------------------- |
| Pro and Flash are both 1M-context                      | vendor spec + operator ruling 2026-08-10                                |
| Pro genuinely serves ≫468K in ONE request              | direct API probe: 600,109 input + 35,200 cache_read = 635,309, HTTP 200 |
| No DeepSeek session was EVER refused on context length | scan of all 1,342 DeepSeek transcripts — zero rejections                |
| The CLI compacts DeepSeek at ~166-190K                 | 125 flash auto-boundaries (max preTokens 190,798), 22 pro (max 259,441) |
| Sessions almost never get high                         | 1/604 flash and 0/756 pro sessions ever exceeded 468K                   |

The `--model` flag is deliberately suppressed for non-Anthropic providers (`accounts.py::model_flag_for_provider`, from
`ao_deepseek_model_flag_misalignment_2026_08_05`), so the CLI has no model identity to size its window from and falls
back to a default. That suppression is correct for its own purpose — this issue is about giving the CLI the window
without re-breaking it.

## Why this costs real money

A worker that compacts at 190K instead of ~950K re-primes its context ~5x more often over the same amount of work, and
each compaction is itself an expensive summarisation turn. It also means AO's cooperative `/pre-compact` ritual is
almost never what actually runs — the CLI's own auto-summary fires first, losing the structured checkpoint the ritual
exists to produce.

## Todos

- [x] ✅ [BACKEND] P1. **It IS settable: `CLAUDE_CODE_MAX_CONTEXT_TOKENS`.** Found by enumerating env-var symbols in the
      VM's own CLI binary (2.1.202, a 261 MB compiled bundle — `grep -a`, the local 1.0.112 JS bundle does not have it),
      then proven behaviourally rather than by reading strings: `/context` on a throwaway DeepSeek session reports
      `21.9k / 200k (11%)` unset and `21.9k / 1m (2%)` with the variable set. That baseline also confirms the ~200K
      assumption exactly. Two neighbours exist and were NOT used — `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and
      `CLAUDE_CODE_DISABLE_1M_CONTEXT`.
- [x] ✅ [BACKEND] P1. Wired into every DeepSeek spawn — `agent-orchestrator@ac9ba18`. The export is emitted in
      `tmux_spawn._start_session` AFTER `source <env_file>` (so it beats anything the account file sets) and keyed off
      the `ANTHROPIC_MODEL` that file already defines, rather than plumbing the provider through ~13 spawn call sites;
      all of them funnel through that one command builder. Set to 1,000,000, below the measured 1,048,565 hard ceiling
      so the CLI's own auto-compact keeps headroom. Tests: `test_a_deepseek_spawn_gets_the_real_window`,
      `test_an_anthropic_spawn_is_left_alone`, `test_an_unset_model_is_left_alone`,
      `test_the_value_stays_below_the_measured_hard_ceiling`.
- [x] ✅ [BACKEND] P1. **Confirmed on the live fleet — both halves of the done-when.** The VM checkout has pulled the
      rollout (`server/tmux_spawn.py` carries the export, `model_tier.py` the 1M prior, and it already has
      `8f1a08ad53`'s gate guards). Measured across 293 DeepSeek sessions active in the last 6h: **15 sessions passed
      400K**, against a pre-fix baseline where only 1 of 604 flash and 0 of 756 pro sessions had EVER exceeded 468K.
      Three cited transcripts passed 400K with **no `compact_boundary` at all**: `35eb0bef-9264-4132-ba20-c2e8e636887c`
      (586,999 tokens), `66d49498-9722-4085-ae01-472526bbbe0b` (532,419) and `48f745c5-7d3a-4d71-a037-4fa2e4712155`
      (529,352). The second half is the more decisive one: the single post-rollout `auto` boundary,
      `c2d3cbea-0ee2-431b-92f1-38d03ccc4f2b`, fired at **preTokens 935,549** — ~93.5% of the 1,000,000 we set, where
      every pre-fix `auto` boundary sat in the 166-190K band (max observed 190,798 flash / 259,441 pro). So the CLI's
      own auto-compact is now operating at the model's real capacity rather than at 17% of it, and the ~150K band has
      stopped producing DeepSeek `auto` boundaries. Sessions at 724,284 and 673,555 tokens show `manual` boundaries only
      — AO's cooperative `/pre-compact` doing the work the raw auto-summary used to pre-empt, which was the second cost
      this issue was filed for.
- [x] ✅ [BACKEND] P2. Not needed — the "if it is NOT settable, compensate" branch is moot now that it is settable. AO's
      own arithmetic was already corrected separately (1M prior + `context_window_for` taking it outright for DeepSeek),
      so the two numbers no longer contradict each other in the dashboard.
- [x] ✅ [BACKEND] P2. Re-keying the registry on per-session belief is NO LONGER NEEDED, and this is a deliberate
      decision not to build it. The oscillation it was meant to cure came from DeepSeek readings with different CLI
      beliefs overwriting one key; DeepSeek is now excluded from calibration (`e943d72`) AND from the learned read path
      entirely, so it writes no `calibrated_window` and `calibrated_window_abrupt_move` (`c730f46`) cannot fire for it.
      Once the spawn export lands fleet-wide, the beliefs converge anyway. Re-open if the alert fires for a NON-DeepSeek
      model, which would mean a genuinely different cause.
- [x] ✅ [BACKEND] P2. Auto-`compact_boundary` `preTokens` is now a first-class registry signal —
      `agent-orchestrator@ac9ba18`. `read_context_snapshot` extracts it (filtered to `trigger: auto`; a MANUAL boundary
      is AO's own forced `/compact` and bounds nothing), `observe()` stores it, and `context_window_for` ranks it ABOVE
      the high-water mark with no confirmation count — a ceiling event is self-confirming where a watermark is only "as
      far as one session got". Stored undivided: measured preTokens/window ratios vary in BOTH directions (sonnet-4-6
      0.94, opus-4-8 1.05), so a `_WATERMARK_TO_WINDOW`-style divisor would inflate the models that already overshoot.
      Tests: `test_an_auto_boundary_sets_the_window_without_needing_confirmation`,
      `test_a_manual_boundary_is_not_a_window`, `test_the_auto_boundary_outranks_the_high_water_mark`,
      `test_pane_calibration_still_outranks_an_auto_boundary`,
      `test_the_measured_sonnet_46_auto_boundary_reproduces_its_real_window`.
- [x] ✅ [BACKEND] P2. **Root-caused: the isolated gate was running on the SYSTEM interpreter, and now fails closed
      instead — `agent-orchestrator@8f1a08ad53`.** The 6 "failures" in `tests/test_done_gate_quickmerge_provenance.py`
      were never a worktree-path problem (my first hypothesis, and it was WRONG — the same worktree with a working
      interpreter gives 4 passed). `quality-gates.sh` gated its `.venv` PATH export on `[ -d .venv/bin ]`, which is
      **false for a dangling symlink**, so `python -m pytest` silently ran against the system python. `pip-audit`
      skipped itself for the same missing interpreter and SAID so; the test step just ran on the wrong one. The file's
      own 2026-06-10 comment predicted exactly this. Two guards, both fail-closed, because a gate that cannot resolve
      its toolchain has not verified anything: no usable `.venv/bin/python` → abort naming the unresolved symlink target
      (`QG_ALLOW_SYSTEM_PYTHON=1` overrides); `dashboard/package.json` present but `dashboard/node_modules` absent →
      FAIL rather than "dashboard checks SKIPPED", which had let a UI change pass an isolated quickmerge without tsc,
      vitest or Playwright ever running (`QG_ALLOW_SKIP_DASHBOARD=1` overrides).
- [x] ✅ [SCRIPT] P2. **Provision the isolation venv + node_modules in `quickmerge.sh` (the other half of the same
      bug).** The `.venv` symlink is created but the cache directory it points at never is, so it dangles by
      construction — `~/.cache/qm-iso-venv/<repo>` did not exist at all. Repos whose `quality-gates.sh` sources
      `base-service.sh` get `uv sync` for free; ones that deliberately do not (agent-orchestrator says so in its header)
      have nothing that would ever create it. Fix is written and validated locally (`mkdir -p` +
      `UV_PROJECT_ENVIRONMENT=… uv sync --frozen`, plus a per-repo `node_modules` cache seeded by **copy**, never a link
      — `uv sync` PRUNED a shared `.venv` on 2026-08-10 and a link would let `npm ci` do the same to the operator's real
      tree). **BLOCKED-CONCURRENT-EDIT**: a peer session is shipping `scripts/quickmerge.sh` right now
      (`fix(infra): stop isolated pushes stranding untracked duplicates`), and same-file concurrent editing is banned —
      my restore was reverted 3x in ~20 min by their pull/rebase cycle. Rebase onto their landed version, then ship.
      Patch preserved outside the shared checkout so it survives the next revert. Done-when: a fresh isolated quickmerge
      in a repo with no prior cache gates on a REAL venv with dashboard deps present. **✅ DONE —
      `unified-trading-pm@dad266ff61`.** Rebased onto the peer's landed `f71c12e40a` with no conflict (the two changes
      are disjoint). Done-when met by the shipping run itself: it printed
      `isolation: provisioning private venv for unified-trading-pm (first run — one-time cost)` and the re-gate then
      reported `✅ Python 3.13` **inside the worktree**, where before it would have silently used the system
      interpreter.
- [x] ✅ [SCRIPT] P2. **Quickmerge's isolated mode cannot ship at all — it dies on a branch collision.** Observed:
      `fatal: 'live-defi-rollout' is already used by worktree at '<main clone>'`. The worktree is created correctly with
      `--detach` (line ~551), but the shared branch-selection stage then runs `git checkout "$BRANCH"` INSIDE it, and
      git refuses to check out a branch another worktree holds. So isolation is currently unusable on the very branch
      every agent ships to, which is why this change had to fall back to `--no-isolated` — and `--no-isolated` is
      exactly what exposes you to the peer-revert race above. **`safe-doc-push.sh` already solves this and is the
      pattern to copy**: it creates the worktree `--detach` at `origin/$BRANCH` (line ~281) and pushes an explicit
      refspec `git push origin "HEAD:${BRANCH}"` (line ~963), never checking out the branch name. Done-when: an isolated
      quickmerge onto `live-defi-rollout` completes while the main clone holds that branch, with a regression test
      covering the collision. **✅ DONE — `unified-trading-pm@dad266ff61`, and it proved itself by shipping ITSELF
      through isolated mode.** `_qm_checkout_ship_branch()` stays detached when `QM_IN_ISOLATION=1` (staying at the
      existing detached HEAD rather than re-detaching onto `origin/$BRANCH`, deliberately — the caller's named files are
      already in the worktree as uncommitted modifications, and moving HEAD under them risks a checkout conflict against
      the very files being committed), and the push uses `HEAD:refs/heads/$BRANCH`. That second half is not cosmetic:
      from a detached HEAD the old `-u origin $BRANCH` pushes the SHARED clone's stale ref and can exit 0 having shipped
      none of your work — a silent no-op ship, covered by its own test. Also repaired a consequence the fix newly made
      reachable: `_PM_BRANCH` resolves to the literal `HEAD` when detached, so `git pull origin HEAD` would have been
      the wrong pull when shipping PM itself. 5 bats tests in `/tests/test_quickmerge_isolated_branch_collision.bats`,
      hermetic (a second local repo is "origin"), including one that reproduces the original `already used by worktree`
      fatal and one that proves the pre-fix push form left the commit behind. Live evidence from the shipping run:
      `detached HEAD — skipping not-behind gate`, no collision,
      `✅ post-push ancestry verified — dad266ff6 is an ancestor of origin/live-defi-rollout`.

## Progress Log

- 2026-08-10 (close-out) — RESOLVED, every todo evidence-backed. The fleet effect is measured, not inferred: DeepSeek
  workers now run to ~935K before the CLI compacts them, against 166-190K before, and 15 sessions passed 400K in a
  single 6h window where only 1 of 1,342 transcripts had EVER exceeded 468K. Two ship-tooling defects found on the way
  out were fixed rather than logged: the isolated gate was running on the system interpreter (so it could report
  failures for a tree whose tests pass), and isolated mode could not complete a ship at all on the shared branch. Note
  what is NOT fixed and cannot be by us: Claude Code still does not recognise the DeepSeek model string. We are
  overriding its belief with `CLAUDE_CODE_MAX_CONTEXT_TOKENS`, so if that undocumented variable is ever renamed or
  removed, every DeepSeek worker silently reverts to compacting at 17% of capacity with no error — the failure mode is a
  cost regression, not a crash, which is exactly the kind that goes unnoticed. The `auto`-boundary registry signal
  shipped in `ac9ba18` is the tripwire: a DeepSeek `auto` boundary reappearing in the ~150-200K band means the override
  has stopped working.

- 2026-08-10 (later) — Shipped the fail-closed gate guards (`agent-orchestrator@8f1a08ad53`) and split the remaining
  ship-tooling work into two precisely-scoped todos above. Two lessons worth more than the fix: (1) **a skipped check
  that announces itself is safer than one that silently substitutes** — `pip-audit` printing "skipped, no python" is why
  the interpreter fault was findable at all, while the test step ran on the wrong interpreter and reported confident
  failures; (2) **`| tail` masks a script's exit code** — a `safe-doc-push.sh … | tail -25` reported exit 0 while the
  plan-hygiene gate had hard-failed and nothing had been pushed. Verify a ship against `origin`, never against the
  pipeline's exit status. Also: this checkout reverted my working-tree edits three times in ~20 minutes (peer `git pull`
  cycles while a peer shipped the same file), so anything not yet committed belongs outside it.
- 2026-08-10 — Split out of the parent issue on its resolution. The parent fixed AO's arithmetic (1M prior +
  `context_window_for` taking that prior for DeepSeek outright); nothing in it could fix the CLI's own belief, which is
  what actually truncates the sessions. Probe method for anyone re-checking the window: POST `/v1/messages` at
  `api.deepseek.com` with a large filler prompt and `max_tokens: 16` — the filler runs ~6 chars/token, so size the
  payload accordingly (3.6 MB yielded 600K input tokens).
