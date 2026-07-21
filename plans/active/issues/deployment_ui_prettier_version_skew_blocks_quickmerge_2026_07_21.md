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
related: [prettier_emphasis_mangling_corpus_corruption_2026_07_14.md]
created: 2026-07-21
parent_epic: agent_operating_framework_master
assigned_vm: planning
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

- [ ] [INFRA] P2. Pin `.husky/pre-commit`'s lint-staged prettier invocation to the same floor quickmerge.sh enforces —
      either bump deployment-ui's `prettier` devDependency to `^3.9.5` (repo: deployment-ui) AND, in a SEPARATE
      dedicated commit (never bundled with a feature diff), run `npx prettier@3.9.5 --write` across the whole `src/`
      tree once to absorb the 97-file reformat cleanly, or change the `lint-staged` config's prettier invocation to
      `npx -y prettier@3.9.5 --write --ignore-unknown` (pinned, matching quickmerge.sh's own pin) so lint-staged and
      quickmerge always agree regardless of what's in `node_modules`.
- [ ] [INFRA] P2. Investigate why `core.hooksPath=.husky/_` routes around the prek-installed `.git/hooks/pre-commit`
      (which carries the correct `prettier-autostage` 3.9.5-floor guard) on this clone (repo: deployment-ui) — either
      make husky's hook delegate to `prek`/`pre-commit run` instead of calling `lint-staged` directly, or confirm this
      dual-hook-manager split is intentional and document why lint-staged (not prettier-autostage) is meant to be
      authoritative for UI repos in `codex/06-coding-standards/quality-gates-ui-template.sh`'s SSOT doc.
- [ ] [INFRA] P3. Audit other UI repos (`unified-trading-system-ui`, `agent-orchestrator`'s dashboard package, any other
      repo with a `package.json` + husky) for the same `core.hooksPath` vs prek dead-hook split (repo:
      unified-trading-pm, cross-repo scan) — if it's fleet-wide, fix it once in the shared setup script rather than
      per-repo.
