---
doc_type: issue
title: >-
  deployment-ui: prettier version skew between quickmerge.sh's forced npx pin and the repo's ACTIVE git hook repeatedly
  triggers a lint-staged "prevented empty commit" failure, blocking quickmerge
summary: >-
  quickmerge.sh's pre-format step force-fetches `npx --yes prettier@3.9.5` on every `--files` path before staging (the
  fleet-wide PRETTIER_MIN_VERSION=3.9.5 floor, codified after the 2026-07-14 markdown-mangling incident). But
  deployment-ui's ACTIVE commit hook is `.husky/pre-commit` -> `npx lint-staged` -> unpinned local `prettier` (resolved
  3.8.4 from package.json's `^3.6.2`), because `core.hooksPath=.husky/_` makes the prek/pre-commit-framework hook at
  `.git/hooks/pre-commit` (which DOES carry the correct PRETTIER_MIN_VERSION=3.9.5 guard, in prettier-autostage.sh) dead
  code — installed but never invoked. When any file in a quickmerge --files list has a construct 3.8.4 and 3.9.5 format
  differently (found: one `Array.from(...)` call in mock-api.ts), the two prettier runs within a single quickmerge
  invocation fight each other to a net-zero diff, and lint-staged's built-in "prevented an empty git commit" safeguard
  fires, hard-failing the ship. Reproduced 4 times in a row (2026-07-21, slot 9) shipping
  deployment_ui_date_range_filter_and_search_2026_07_20 todo -009 — worked around by excluding the unrelated file from
  that quickmerge's `--files` list (it was already committed via an earlier commit, so omitting it from `--files` skips
  the M1 pre-format pass entirely and the ship succeeded). Bumping deployment-ui's `prettier` devDependency to `^3.9.5`
  DOES close the version gap, but `prettier --check` then flags 97 files across the repo as stale-formatted — too large
  a blast radius to fold into an unrelated feature ship, so it was reverted rather than applied inline.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: [quickmerge, prettier, husky, pre-commit, ci-cd, tooling-defect, lint-staged]
related: [/plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md]
created: 2026-07-21
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-07-21 (slot 9) shipping deployment_ui_date_range_filter_and_search_2026_07_20 todo -009 —
    quickmerge --agent failed 4× in a row on deployment-ui with 'lint-staged prevented an empty git commit'",
  ]
resolved_by:
locked_by:
---

# deployment-ui prettier version skew blocks quickmerge

## What I found

1. `quickmerge.sh` (STAGE 5, `unified-trading-pm/scripts/quickmerge.sh:1421-1460`) pre-formats every `--files` path with
   a hard-pinned `npx --yes prettier@3.9.5 --write` BEFORE staging — this mirrors the `PRETTIER_MIN_VERSION=3.9.5` floor
   in `scripts/hooks/prettier-autostage.sh:73` (the fix for
   `prettier_emphasis_mangling_corpus_corruption_2026_07_14.md`).
2. deployment-ui's `.pre-commit-config.yaml` DOES declare a `prettier-autostage` hook that wraps that same
   `prettier-autostage.sh` (with its own 3.9.5-floor self-heal via `npx -y prettier@$PRETTIER_MIN_VERSION` fallback).
   But `git config core.hooksPath` on this clone is `.husky/_` — so git's actual active pre-commit hook is
   `.husky/pre-commit` (`npx lint-staged || exit 1`), NOT the prek-installed `.git/hooks/pre-commit` that would run
   `prettier-autostage`. The prek hook file exists on disk but is **dead code** — `core.hooksPath` routes every commit
   around it.
3. `lint-staged`'s own config (`package.json` `"lint-staged"` block) calls plain `prettier --write --ignore-unknown` —
   no version pin — which resolves whatever is in `node_modules/.bin` (package.json declares `"prettier": "^3.6.2"`;
   `package-lock.json` resolves it to `3.8.4`).
4. `3.8.4` and `3.9.5`/`3.9.6` disagree on how to wrap at least one construct in `src/lib/mock-api.ts`
   (`...Array.from({ length: 125 }, (_, i): Row => [...])` around line 2718) — 3.8.4 wants it wrapped across multiple
   `Array.from(...)` argument lines, 3.9.5/3.9.6 wants the callback body's array literal broken out instead. Neither is
   wrong; they are simply two different prettier releases' opinion on the same ambiguous case.
5. Net effect inside ONE `quickmerge.sh --agent` invocation whose `--files` includes `mock-api.ts`: quickmerge's own
   3.9.5 pass reformats the file → stages a real diff → `git commit -m ...` fires the active husky hook → lint-staged's
   unpinned 3.8.4 reformats it BACK to the original style → the staged diff nets to zero vs `HEAD` → lint-staged's
   built-in empty-commit guard fires → `husky - pre-commit script failed (code 1)` → quickmerge reports
   `❌ Commit failed`. This reproduced identically 4 times in a row (with and without `--build`, and again after I
   manually pre-added the `Quickmerge: agent` trailer to sidestep the OTHER amend path) — always the same file, always
   the same construct.
6. Confirmed the fix boundary is real by testing both directions:
   - `npm install prettier@^3.9.5 --save-dev` (resolved 3.9.6) makes `mock-api.ts` clean under local prettier, BUT
     `npx prettier --check "src/**/*.{ts,tsx,json,css}"` then flags **97 files** across the whole repo as
     stale-formatted vs 3.9.6 — a repo-wide reformat far outside the blast radius of a single feature ship, so I
     reverted the devDependency bump rather than fold it in.
   - Manually re-formatting just that one construct to 3.9.5's preference and committing it hits the SAME "prevented
     empty commit" failure on a plain `git commit` (not just inside quickmerge) — because the active husky/lint-staged
     hook flips it right back using the local 3.8.4 binary. So this cannot be fixed file-by-file without either skipping
     the hook (`--no-verify`, banned without explicit operator ask) or fixing the version pin itself.
7. **Workaround used to ship** (deployment_ui_date_range_filter_and_search_2026_07_20 todo -009, deployment-ui@1880424):
   `mock-api.ts` was already committed (with my real feature diff) in an earlier commit on the same branch tip;
   re-running `quickmerge.sh --agent --files '<other 3 files>'` (omitting `mock-api.ts` from `--files`) meant
   quickmerge's M1 pre-format pass never touched it, so no spurious diff was created and the "already committed, N
   commits ahead of main" fast-path pushed cleanly. This only works because the file was ALREADY on HEAD via a prior
   commit — it is not a fix, just a way to avoid re-triggering the bug on a file with no NEW changes in that particular
   quickmerge call.

## Why it matters

- This will hard-block ANY future `quickmerge --agent` call whose `--files` list includes `mock-api.ts` (or any other
  file where 3.8.4 vs 3.9.5+ disagree) while it carries genuinely NEW changes — the workaround above only works when the
  file has nothing new to commit in that specific invocation.
- The `prettier-autostage.sh` 3.9.5-floor self-heal (the actual fix for the 2026-07-14 markdown-corruption incident) is
  silently inert on this repo because of the `core.hooksPath` routing — any OTHER version-sensitive prettier behavior
  that fix was meant to guard against is equally unprotected here.
- Worth checking whether other UI repos cloned via the same `setup-tab-worktrees.sh` / prek-install flow have the same
  `core.hooksPath=.husky/_` vs dead `.git/hooks/pre-commit` split — this looks like a setup-order artifact (husky's
  `prepare` script `installs` last and points `core.hooksPath` at itself), not something specific to deployment-ui.

## Recommended decision

Two independent fixes, either sufficient to close the immediate ship-blocking bug (do both for defense in depth):

- [x] ✅ [INFRA] P2. Pin `.husky/pre-commit`'s lint-staged prettier invocation to the same floor quickmerge.sh enforces
      — deployment-ui@3584da7. Changed `lint-staged`'s prettier target in `package.json` from unpinned
      `prettier --write     --ignore-unknown` to `npx -y prettier@3.9.5 --write --ignore-unknown` (pinned, matching
      quickmerge.sh's own pin), avoiding the 97-file repo-wide reformat blast radius of bumping the `prettier`
      devDependency itself. QG green, shipped via quickmerge --agent.
- [x] ✅ [INFRA] P2. Investigate why `core.hooksPath=.husky/_` routes around the prek-installed `.git/hooks/pre-commit`
      (which carries the correct `prettier-autostage` 3.9.5-floor guard) on this clone (repo: deployment-ui) —
      deployment-ui@3a71ffe. **Real root cause differs from the original framing above**: `.git/hooks/pre-commit` isn't
      what's dead — both husky (via its npm `prepare` lifecycle script) AND prek/pre-commit-framework write to the SAME
      file, `.husky/_/pre-commit`, once `core.hooksPath=.husky/_` is set. Whichever tool's install step runs LAST for a
      given clone overwrites the other's file there — a genuine, non-deterministic race, not an intentional split.
      Confirmed via a research pass across `unified-trading-pm/scripts/`: `setup-tab-worktrees.sh`'s
      `install_prek_precommit_hook` (clone-time), `check-precommit-versions.py`'s `run_precommit_install --apply`, and
      any ad-hoc `prek install`/`pre-commit install` all write into whatever `core.hooksPath` currently resolves to with
      **no husky-awareness guard** — only `slot-cron-ff-pull.sh`'s periodic self-heal (2026-07-08 fix) skips
      `*/.husky/*` hooksPath dirs; the other three install paths do not. The canonical UI pre-commit template itself
      (`scripts/pre-commit-templates/ui.pre-commit-config.yaml:4`, "Setup: `pre-commit install --install-hooks`") still
      tells operators to run the very install that clobbers husky, contradicting the cron-heal's husky-deference. **This
      is worse than the prettier-only framing**: when husky's shim wins the race, git skips not just the
      prettier-version floor but EVERY fleet canonical check — branch-drift, commit-identity, gitleaks secret-scanning,
      conventional-commit validation — running only `lint-staged` instead. Fix: rewrote the tracked `.husky/pre-commit`
      (the file husky's dispatcher actually execs when it wins) to delegate to `prek run --hook-stage pre-commit`
      (falling back to `pre-commit run`, then `lint-staged` only if neither binary is on PATH) — so whichever install
      won the race, the actual checks that fire are always the fleet's canonical set. Verified locally: staged a file,
      ran `.husky/pre-commit` directly — it invoked prek's `check-branch-drift` hook (correctly failed on real drift),
      proving delegation works instead of silently running lint-staged. QG green, shipped via quickmerge --agent. Did
      not touch the `codex/06-coding-standards/` SSOT doc naming lint-staged as authoritative — this plan's
      `drift_direction:     advance-code` scopes this todo to code, not codex; the fleet-wide setup-script race (this
      finding's actual root cause) is out of scope for a per-repo fix and is exactly what todo 3 below should cover.
- [x] ✅ [INFRA] P3. Audit other UI repos (`unified-trading-system-ui`, `agent-orchestrator`'s dashboard package, any
      other repo with a `package.json` + husky) for the same `core.hooksPath` vs prek dead-hook split (repo:
      unified-trading-pm, cross-repo scan) — unified-trading-pm@`<SHA>`. **Audit result**: only two repos in the fleet
      have `.husky/` at all — `deployment-ui` (fixed by todo 2, `@3a71ffe`) and `unified-trading-system-ui`, which
      already carried the identical delegation fix (`.husky/pre-commit` → `exec prek run --hook-stage pre-commit`,
      falling back to `pre-commit run` then `lint-staged`; lint-staged's prettier target already pinned to
      `npx -y prettier@3.9.5`) via a prior fleet-wide-audit pass already on `origin/live-defi-rollout`
      (unified-trading-system-ui@f2bf4db6, @4bc18435, 2026-07-21T15:03Z) — nothing left to change there.
      `agent-orchestrator/dashboard` has a `package.json` but no `.husky/` dir and no `core.hooksPath` override (its
      `.git/hooks/pre-commit` is the live prek hook), so it was never affected. **Also fixed the fleet-wide
      install-order race at its 3 real sources** (repo: unified-trading-pm): (1) `scripts/dev/setup-tab-worktrees.sh`'s
      `install_prek_precommit_hook` now resolves the clone's active hooks dir via
      `git rev-parse --path-format=absolute --git-path hooks` and returns early on a `*/.husky/*` match, mirroring
      `slot-cron-ff-pull.sh`'s 2026-07-08 guard, so clone-time prek install no longer clobbers husky; (2)
      `scripts/manifest/check-precommit-versions.py` gained an `is_husky_managed()` helper (same hooks-dir resolution)
      and the `.git/hooks/pre-commit` existence check now skips husky-managed repos entirely (was a guaranteed false
      positive there, since husky's hook never lives under `.git/hooks/`, and `--apply` would have called `prek install`
      and clobbered `.husky/_/pre-commit`); (3) `scripts/pre-commit-templates/ui.pre-commit-config.yaml:4`'s
      `# Setup: pre-commit install --install-hooks` comment replaced with guidance that husky-managed UI repos must NOT
      run that install (it clobbers husky) and should instead point the tracked `.husky/pre-commit` at the
      `prek run --hook-stage pre-commit` delegation pattern. QG green, shipped via quickmerge --agent.
