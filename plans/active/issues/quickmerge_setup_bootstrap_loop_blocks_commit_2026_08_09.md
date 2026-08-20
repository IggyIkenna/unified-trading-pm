---
doc_type: issue
title: quickmerge re-enters setup.sh after the quality audit and exits without committing
summary: >-
  On this host (Ikenna slot-2 macOS), quickmerge.sh clears Stage 1 (path deps) and Stage 2 (quality audit) then
  re-enters "Ensuring env ready (setup.sh)", bootstraps uv repeatedly, and exits WITHOUT reaching the commit stage.
  Reproduced 4/4 times on 2026-08-09, including with --unit-only. Files stay untracked, ahead stays 0, no error is
  printed. PARTIALLY EXPLAINED 2026-08-09 — the commit being attempted carried invalid YAML frontmatter, which fails the
  plan-hygiene gate; that accounts for the rejection but NOT for the silent exit or the setup.sh re-entry, which remain
  real and are the actual bug.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, ci, tooling, blocked, commit-flow]
related: [/codex/08-workflows/ci-cd-flow.md]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: ci_master
source: interactive-session
resolved_by: unified-trading-pm@c389fe9dc (loop); frontmatter fixed in-session
locked_by:
context_scope:
  [
    scripts/setup.sh,
    scripts/quickmerge.sh,
    scripts/quality-gates-base/base-library.sh,
    /codex/08-workflows/ci-cd-flow.md,
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
assigned_role: cicd
effort: low
drift_direction: unknown
depends_on: []
---

# quickmerge re-enters setup.sh after the quality audit and exits without committing

## Symptom

`bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'` run from
`/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/2/unified-trading-pm`:

1. Stage 0/1 pass — pre-flight audit OK, "No path dependencies found".
2. Stage 2 quality audit runs and **passes** visible checks (`E722 not in global ignore`,
   `No hardcoded project IDs in tests`, `No files >1500 lines`).
3. Execution then returns to `Ensuring env ready (setup.sh)` and prints the `setup.sh — unified-trading-pm` banner
   **again**, re-running `[1] Python version` / `[2] Architecture check` / `[3] Bootstrap uv`.
4. The process exits. **No commit is created, nothing is pushed, no error is printed.**

`git rev-list --count origin/live-defi-rollout..HEAD` stays `0`; the `--files` paths stay `??` untracked.

## Reproduction — 4/4 on 2026-08-09

| #   | Invocation                                         | Outcome                                                                              |
| --- | -------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 1   | `--agent --files …` (900s timeout)                 | Killed by my own timeout, still in setup                                             |
| 2   | `--agent --files …` (detached)                     | Killed deliberately to apply an edit                                                 |
| 3   | `--agent --files …` (detached, waited to exit)     | **Exited on its own, nothing committed**                                             |
| 4   | `--agent --unit-only --files …` (detached, waited) | Got furthest — cleared Stage 2 gates — then looped and **exited, nothing committed** |

`--unit-only` (= `--quick --no-pr`) demonstrably gets further than the plain form. It is NOT sufficient.

## ROOT CAUSE OF THE LOOP — FIXED by a peer session, 2026-08-09

`unified-trading-pm@c389fe9dc` — _"fix(scripts): portable UV_VERSION parse (grep -oP -> sed -E) + host-scoped push
governor"_ — touching `scripts/setup.sh`, `scripts/quickmerge.sh`, `scripts/quality-gates-base/base-library.sh`,
`scripts/dev/safe-doc-push.sh`. (SHA corrected 2026-08-09 — originally cited as `a766aabc8d`, which does not resolve to
a real commit in this clone; content-matched against the actual git log and confirmed `c389fe9dc...`, ancestor-verified,
is the real commit that shipped this exact change — fixed independently by two concurrent sessions, converged on the
same commit. See `plans/archive/issues/pm_qg_red_audit_batch10_finalize_2026_08_09.md`.)

**`grep -oP` is a GNU extension and does not exist in macOS BSD grep.** The UV_VERSION parse in `setup.sh` therefore
failed on this host, `[3] Bootstrap uv` never completed, and the script re-entered env-prep — which is exactly the
observed "re-enters `Ensuring env ready (setup.sh)`, bootstraps uv repeatedly, exits silently" symptom. It reproduced
4/4 here and would reproduce on any macOS host while never reproducing on the Linux AO VM, which is why todo P3 below
(is-it-host-specific) was the right question.

**Both blockers were real and independent** — this loop, AND the invalid frontmatter recorded below. Fixing either alone
would not have landed the commit.

## SECOND, INDEPENDENT BLOCKER — my own payload, 2026-08-09

**Correction to the original report below: it was partly my own fault, and the doc said otherwise.** The commit being
attempted carried **invalid YAML frontmatter** —
`/codex/11-project-management/cloud-spend-forecast-and-credits-2026-08.md` had a plain-scalar `summary:` containing
`": "` (`…the FINAL position taken: an 80% effective discount…`), which YAML parses as a mapping.
`check_frontmatter_yaml` rejects it, and the issue doc here separately failed `check_frontmatter_schema`
(`status: active` is not a valid _issue_ status; `parent_epic`/`source` missing). Both are hard failures in the
plan-hygiene pre-commit hook.

So the **rejection** is explained and was legitimate. What is **still unexplained and still a real bug**:

- the **silent exit** — a hard gate failure should print the violation and exit non-zero, not return to
  `Ensuring env ready (setup.sh)` and stop with no message;
- the **setup.sh re-entry** — nothing about a frontmatter violation should re-run env bootstrap;
- the fact that an agent could not tell "blocked by a gate" from "succeeded" without running `git ls-files` afterwards.

The lesson generalises past this issue: **when a shipping tool fails silently, suspect your own payload before the
tool.** Running the hooks directly (`prek run --files <paths>`) surfaced both violations in one shot after four
quickmerge attempts had produced no diagnostic at all. Do that FIRST next time.

## What this is NOT

- **Not the foreign-staged-file problem.** A concurrent session had staged plan edits, but `--files` scopes staging and
  the run never reached staging.
- **Not a dirty-dependency block.** Stage 1 explicitly reported no path dependencies.
- ~~Not a gate failure.~~ **This claim was wrong** — see the partial root cause above. The gates the _visible_ stages
  ran did pass, which is what misled the original diagnosis; the plan-hygiene gate that actually rejected the commit
  never printed anything.

## Open work

- [x] [DEVOPS] P1. ✅ **Diagnosed and FIXED — `grep -oP` is GNU-only, absent in macOS BSD grep**
      (unified-trading-pm@c389fe9dc, peer session; SHA corrected 2026-08-09, was mis-cited as `a766aabc8d`). Original
      text: **Diagnose why quickmerge re-enters setup.sh after Stage 2 and exits silently** — instrument with `bash -x`,
      or bisect the stage that returns control to env-prep. The silent exit with no error is the worst part: an agent
      cannot distinguish "blocked" from "succeeded" without checking `git ls-files` afterwards.
- [ ] [DEVOPS] P2. **Make quickmerge fail loudly when it exits without committing** — a non-zero exit and a printed
      reason. A silent no-op that leaves files untracked is how work gets lost.
- [x] [DEVOPS] P2. ✅ **Done — stale on re-check 2026-08-09.** All three `scripts/finops/` tools
      (`measure_agent_fleet_tokens.py`, `cloud_spend_forecast_2026_08.py`, `llm_and_research_unit_economics.py`) are now
      tracked and committed — confirmed via `git ls-files` (all three present) and `git log` (landed together in
      `unified-trading-pm@0f6087516f`, "docs(finops): three-year tapering GCP proposal + DART-led restructure + finops
      tooling", verified ancestor of `origin/live-defi-rollout`). No action needed; this todo was simply not reconciled
      after a later session landed the files by another path.
- [ ] [DEVOPS] P3. **Check whether this is host-specific** — if it reproduces on the AO VM it blocks the whole agent
      commit flow, not just interactive work from this laptop.

## Workaround used

Pure-doc content was landed via `scripts/dev/safe-doc-push.sh` (the sanctioned docs fast path). That does not cover
`scripts/**`, so the Python tooling remains uncommitted pending the fix above.

## Provenance

Found during the 2026-08-09 Google Cloud spend-forecast session while trying to commit
`/codex/11-project-management/cloud-spend-forecast-and-credits-2026-08.md` and its tooling. Four attempts consumed a
material share of that session's budget — hence this doc, so the next session does not repeat them.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (4 entries).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:bb54de155acb8854]: RECLASSIFY_WHOLE —
  `assigned_vm: NA` → `planning`. Root cause already fixed (`unified-trading-pm@c389fe9dc`); both remaining open
  todos (fail-loudly on silent no-commit exit; check AO-VM host-specificity) are bounded and deterministic, no gate
  found.
