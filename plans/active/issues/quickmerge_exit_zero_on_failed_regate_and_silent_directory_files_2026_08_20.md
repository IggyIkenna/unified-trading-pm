---
doc_type: issue
title: quickmerge.sh exits 0 on a failed re-gate, and silently stages nothing for a directory in --files
summary: >-
  Measured 2026-08-20 across five consecutive real ship attempts. TWO independent defects in scripts/quickmerge.sh.
  (1) A failed re-gate prints "❌ Re-gate FAILED" and then EXITS 0 — three attempts reported success while landing
  nothing (lint; codex-compliance; the empty-string-fallback ratchet). (2) A DIRECTORY path passed to --files stages
  nothing for it, silently and without warning, so a commit that names a package directory lands a PARTIAL change set.
  Together these produced a broken live-defi-rollout: strategy-service@1bda20fb landed factory.py referencing
  strategy_service.engine.strategies.v2.portfolio while the portfolio package itself was never staged, and the
  script's recovery pass additionally REVERTED the unstaged test edits in the working tree. Repaired by @3eb96f35.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, shipping, ci, false-progress, agent-safety]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
created: "2026-08-20"
last_updated: 2026-08-20
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P0
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Measured 2026-08-20 while shipping the T3 archetype-registration wave — five consecutive real quickmerge attempts
  on strategy-service, three of which reported exit 0 while landing nothing, and one of which landed a partial commit
  that broke live-defi-rollout.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md,
    scripts/quickmerge.sh,
    scripts/dev/safe-doc-push.sh,
  ]
---

# quickmerge.sh: exit 0 on failed re-gate + silent directory drop in `--files`

Found while shipping the T3 archetype-registration wave
(`/plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md`). Both defects are in the ship path every
agent is required to use, and both produce **false progress** — the single failure mode the commit-push-flip rule
exists to prevent.

## Defect 1 — exit 0 on a failed re-gate

Three consecutive attempts printed a red verdict and still exited 0:

| attempt | gate that failed | landed? |
| --- | --- | --- |
| 1 | `❌ Lint FAILED` (trailing whitespace + import order) | nothing |
| 2 | `❌ Codex compliance FAILED: 4 violations (max allowed: 3)` | nothing |
| 3 | `❌ STEP 5.101` empty-string-fallback ratchet (168 > baseline 166) | nothing |

Each ended `[strategy-service] ❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost
race.` followed by `exited with code 0`.

**Why this is P0 for agents specifically.** An agent backgrounds the ship and is re-invoked on completion with an
exit code. Exit 0 plus a "Landed" line is the whole signal. An agent that trusts it reports shipped work that does
not exist, and — worse — flips the plan checkbox with a fabricated SHA. The rule "`ahead=0` + clean tree ≠ landed"
already covers the swept/destroyed cases; it does not cover "the ship script told me it succeeded".

**Fix**: propagate the re-gate's failure to the script's exit status. A non-zero exit is the contract every caller
already assumes.

## Defect 2 — a directory in `--files` stages nothing, silently

`--files 'a/b/c.py some/package tests/some/dir'` stages `a/b/c.py` and **silently drops the two directories** — no
warning, no refusal, and the commit proceeds with whatever else was named. The result is a PARTIAL commit.

Measured consequence: `strategy-service@1bda20fb` landed `factory.py` with four references to
`strategy_service.engine.strategies.v2.portfolio` while the `portfolio/` package (6 files, passed as a directory)
was never staged, and the v2 test directory (also a directory) was never staged either. LDR was left where:

- resolving any `PORTFOLIO_*` archetype raised `ModuleNotFoundError`; and
- the old tests still asserted the VOL/MM engines must NOT be registered — which the same commit had just made false.

`safe-doc-push.sh` REFUSES a wildcard outright (`Refusing: --files '<space-separated paths>' is required -- this
script never stages by wildcard`). quickmerge accepting a directory and dropping it is strictly more dangerous,
because refusing costs one retry whereas dropping costs a broken shared branch.

**Fix**: refuse a non-file path in `--files` with a structured error, matching `safe-doc-push.sh`'s behaviour.
Expanding the directory instead would be worse — it would silently widen the commit's scope beyond what was named,
which is what `--files` exists to prevent.

## Defect 2b — the recovery pass reverted unstaged edits

In the same run, edits to the (unstaged, because directory-dropped) test files were **reverted in the working
tree**. They had to be re-applied by hand from the original patches. Whatever restore/quarantine path ran during
the commit treated tracked-but-unstaged modifications as discardable.

## Why the standard verification did not catch it

Every cheap check passed during the broken window:

| check | result | why it lied |
| --- | --- | --- |
| exit code | `0` | defect 1 |
| script output | `✅ Landed on live-defi-rollout` | printed after the failed re-gate |
| `git status` | clean | the directory-dropped files were reverted, not left dirty |
| `git rev-list --left-right --count HEAD...FETCH_HEAD` | `0 0` | local had been reverted to match origin |
| **`git diff FETCH_HEAD`** | **empty** | **both sides agreed on the WRONG content** |

Only a per-file existence probe against origin's tree found it:

```bash
git fetch -q origin live-defi-rollout
for f in <every path you named>; do
  git cat-file -e FETCH_HEAD:$f 2>/dev/null && echo "OK   $f" || echo "MISS $f"
done
```

**An empty diff against origin is not proof your change landed** — it is equally consistent with your local content
having been reverted underneath you. This is a sharper case than the existing `ahead=0` rule and belongs alongside
it in `/codex/05-infrastructure/per-tab-worktrees.md`.

## Todos

- [ ] [SCRIPT] P0. Make a failed re-gate exit non-zero in `scripts/quickmerge.sh`. **Investigated 2026-08-20 (T5):
      the specific agent-mode re-gate path (`_qm_check_agent_sentinel`'s until-loop, ~L2531) already captures the
      real exit code correctly via `${PIPESTATUS[0]}` and unconditionally `exit 1`s on failure — verified by direct
      code read, not assumed. Reproduced the "exited with code 0" symptom's most likely confound instead: the
      near-universal `bash scripts/quickmerge.sh ... 2>&1 | tee LOG | tail -N` logging convention (used by this
      session and, most likely, by T3's own measurement) returns `tail`'s exit status, not quickmerge.sh's —
      confirmed live: `false 2>&1 | tee /tmp/x | tail -5; echo $?` prints `0`. This does not disprove Defect 1
      outright (the non-agent-mode `--lint --fix`/`--no-fix` phases at L2589-2600 weren't independently traced,
      and a genuinely intermittent path may still exist), but the evidence as measured (exit-code-after-a-pipe) is
      fully explained by the logging convention and does not by itself prove quickmerge.sh fails to propagate.
      Re-measure with `${PIPESTATUS[0]}` captured directly (not through `| tail`) before concluding a further code
      change is needed here — leaving open rather than closing on unconfirmed evidence.**
- [x] ✅ [SCRIPT] P0. Refuse a directory (any non-file path) in `--files` with a structured error, mirroring
      `safe-doc-push.sh`. Do NOT expand it — that would silently widen commit scope. **Fixed 2026-08-20:
      `unified-trading-pm@d0e5a67ee7`, added right after the `--agent` + `--files` requirement check
      (before any staging/gate work runs) — any `-d` path in `FILES_ARG` now exits 1 with a clear message instead
      of reaching the staging loop. Live-tested against a real throwaway directory (`/tmp/qm_dirtest_scratch`):
      refused correctly, zero git state touched (`git status --porcelain` clean after). Root cause of the ORIGINAL
      silent-drop was not fully pinned down (structural read of the staging loop, L2842 `elif [ -e "$f" ]`, suggests
      `git add` on a directory should recurse and stage correctly — the empirical break may trace to the fingerprint
      tracker at L~535 treating a directory as `ABSENT` since it checks `[ -f ]` not `[ -e ]`, which blinds the
      post-push `_qm_assert_entry_change_landed` verifier to directories specifically, masking whatever the real
      failure was rather than causing it) — refusing upfront sidesteps needing to fully explain the intermittent
      mechanism, which was the doc's own recommended fix.**
- [ ] [SCRIPT] P1. Stop the recovery/quarantine path from reverting tracked-but-unstaged modifications, or name
      every file it restores so the loss is visible.
- [x] ✅ [DOC] P1. Add the per-file origin probe + the "an empty diff is not proof" case to
      `/codex/05-infrastructure/per-tab-worktrees.md`, next to the existing `ahead=0` guidance. **Fixed 2026-08-20**:
      new "An empty diff against origin is not proof your change landed" subsection added, citing this doc's own
      2026-08-20 measurement, with the per-file probe snippet and the new directory-refusal behavior noted.

- **context-scout 2026-08-20**: populated context_scope (6 entries).
