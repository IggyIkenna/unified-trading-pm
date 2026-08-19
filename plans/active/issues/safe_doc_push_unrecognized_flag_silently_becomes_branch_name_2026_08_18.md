---
doc_type: issue
title: safe-doc-push.sh has no --agent flag — an unrecognized flag silently becomes the target BRANCH, corrupting every internal git fetch/pull/push this run
summary: >-
  Live-hit 2026-08-18 by plan_reconciler (infra tranche, agt-830118): invoking `scripts/dev/safe-doc-push.sh "<msg>"
  --agent --files '<paths>'` — the exact convention CLAUDE.md documents for `quickmerge.sh` and that
  `SUB_AGENT_MANDATORY_RULES.md` generalizes to "Ship scripts... always-on in safe-doc-push" — silently corrupts the
  run. `safe-doc-push.sh`'s argument-parsing loop (lines 187-200) has no `--agent` case at all; its wildcard `*)`
  branch (line 196) does `BRANCH="$1"`, so `--agent` (an unrecognized token) gets assigned as the target branch name.
  Every subsequent `git fetch -q origin "$BRANCH"` call (lines 480, 1629) then becomes `git fetch -q origin
  "--agent"`, which git correctly rejects with `error: unknown option \`agent'` — printed in full (~60 lines of `git
  fetch --help`) on EVERY retry attempt, for all 6 attempts, before the script gives up with exit 5 ("Exhausted 6
  attempts... a genuine race (fetch/pull/push contention) that did not settle... re-running is safe" — a MISLEADING
  diagnosis; this is 100% deterministic, not a race, and re-running as-is fails identically every time, confirmed by
  reproducing it twice). The script's own usage line (line 181) never documents `--agent` as a real flag: `Usage: $0
  "<commit message>" --files "path1 path2 ..." [branch]` — only `--files` and a bare positional `[branch]` are real.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, ship-script, argument-parsing, agent-footgun, robustness]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md, /plans/active/infra_consolidated_closeout_2026_07_25.md]
created: "2026-08-18"
author: plan_reconciler
source: agt-830118 (infra tranche daily reconciliation)
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: fix
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope: [/scripts/dev/safe-doc-push.sh]
---

# safe-doc-push.sh silently treats an unrecognized `--agent` flag as the target branch name

## What happened (measured, not inferred)

```
$ bash scripts/dev/safe-doc-push.sh "docs(plans): ..." --agent --files '<paths>'
── attempt 1/6 ──
  fetch failed, retrying:
error: unknown option `agent'
usage: git fetch [<options>] [<repository> [<refspec>...]]
...
── attempt 2/6 ── (identical error)
...
── attempt 6/6 ── (identical error)
❌ Exhausted 6 attempts. ... Your named file(s) are byte-identical to what you handed this script, so re-running is
   safe. READ the last error below first rather than assuming transience:
EXIT_CODE=5
```

Reproduced twice in the same session, both times identical (6/6 attempts, same error, exit 5 both times) — confirming
this is deterministic content/argument failure, not the transient "fetch/pull/push contention" the exit-5 message
itself claims.

## Root cause

`scripts/dev/safe-doc-push.sh:177-200`:

```bash
MSG=""
BRANCH="live-defi-rollout"
FILES=()
...
MSG="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --files)
      shift
      FILES=($1)
      shift
      ;;
    *)
      BRANCH="$1"
      shift
      ;;
  esac
done
```

There is no `--agent)` case. Any token that isn't `--files` — including a plausible-looking flag like `--agent` —
falls into the wildcard `*)` branch and overwrites `BRANCH`. The script never validates that the resulting `BRANCH`
value looks like a real branch name (e.g. rejecting anything starting with `-`), so the corruption is silent at
parse time; it only surfaces later, indirectly, as a confusing git error deep inside the retry loop
(`scripts/dev/safe-doc-push.sh:480,1629`, `git fetch -q origin "$BRANCH"`).

## Why this is a real, live footgun — not a hypothetical

- **CLAUDE.md's own documented convention actively primes this mistake.** `quickmerge.sh` genuinely takes `--agent`
  (`bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` — CLAUDE.md § "Ship via..."). An agent who has
  correctly internalized "always pass `--agent`" for one ship script has no textual signal that the sibling
  `safe-doc-push.sh` doesn't share the flag — CLAUDE.md's own line "Ship scripts COMMIT FROM AN ISOLATED WORKTREE...
  always-on in safe-doc-push" (§ Git discipline) reads as reinforcing parity between the two scripts, not warning of
  a divergence.
- **`SUB_AGENT_MANDATORY_RULES.md` § "Ship CODE: two-pass" also only shows the quickmerge form** — a sub-agent reading
  only that file (its entire context, by design) has zero signal that `safe-doc-push.sh` differs.
- **The failure mode burns real time without ever landing anything**: 6 attempts × a ~60-line `git fetch --help`
  dump each, then a misleading "this was contention, re-running is safe" message that invites a SECOND identical
  failure (confirmed — that's exactly what happened this session) before anyone thinks to read the actual error text
  instead of the summary.

## Blast-radius note (not fully audited this pass)

In every reproduction this session, the corruption was caught at the FIRST `git fetch` call — before any commit or
push was attempted — so no content was ever pushed to the wrong ref in this specific case. I did NOT exhaustively
audit every other `$BRANCH` usage in the script (it's used in `git pull`/`git push`/branch-drift-check contexts too,
not just the two fetch call sites) to confirm there is no code path where a corrupted `BRANCH` value could reach a
`git push origin "$BRANCH"` and attempt to push to a literal branch named `--agent` (which would likely also fail
loudly, given git's own flag parsing, but this was not independently verified). Whoever fixes this should audit that
too, not just the fetch path.

## Recommended fix (not implemented by this run — outside `plans/**`, per `agents/plan_reconciler.md`'s HARD LIMIT
"NO touching files outside plans/** except reading")

Either (a) explicitly recognize and no-op/consume `--agent` in the parsing loop (mirroring quickmerge's convention,
even if safe-doc-push doesn't need to DO anything different for an agent caller), or (b) make the wildcard branch
strictly reject anything starting with `-`/`--` with a clear "unrecognized flag: $1" usage error instead of silently
adopting it as the branch name. Option (b) is more robust long-term (catches ANY future flag-typo the same way, not
just this one), but either closes the immediate footgun. The misleading exit-5 message ("re-running is safe... a
genuine race") should also be corrected to not claim contention when the actual cause was a rejected git argument —
distinguish "git rejected the command outright" (deterministic, don't blindly retry) from "the network round-trip
timed out" (genuinely transient) in the retry loop's own error classification.

## Todos

- [x] ✅ [SCRIPT] P1. Fix `scripts/dev/safe-doc-push.sh`'s argument parser (lines 187-200) per one of the two options
      above. Add a regression test (mirroring `test-safe-doc-push-concurrency.sh`'s style) asserting `--agent` either
      is accepted as a no-op or produces a clear usage error, never a silent `BRANCH` corruption. Repo:
      unified-trading-pm. — unified-trading-pm@7adc383c84
- [ ] [SCRIPT] P2. Audit every other `$BRANCH` usage in the script (not just the 2 fetch call sites) for the same
      corrupted-value blast radius — confirm a corrupted `BRANCH` can never reach a `git push`/`git pull` call
      unnoticed. Repo: unified-trading-pm.
- [ ] [DOCS] P3. Update `cursor-configs/CLAUDE.md` and/or `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` to explicitly
      state whether `safe-doc-push.sh` accepts `--agent` (once the SCRIPT fix above lands, this becomes a
      documentation-parity fix rather than a workaround note). Repo: unified-trading-pm.

## Progress Log

- **2026-08-18 (plan_reconciler, infra tranche, agt-830118)**: found live while shipping this run's own archival
  checkpoint. Root-caused by reading the script's argument-parsing loop directly rather than guessing. Worked around
  by omitting `--agent` from the invocation (matches the script's real, documented usage line) — the checkpoint
  shipped clean afterward (`unified-trading-pm@4e15ec3b55`). Filed here rather than fixed in-line: the fix touches a
  fleet-wide ship script every doc-only commit depends on, which — per this exact same doc-family's own precedent
  (`safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md`, archived earlier this run) — wants its own
  regression test and blast-radius check rather than a same-session patch buried in an unrelated reconciliation run.
- **2026-08-19 (worker slot-32)**: fixed the P1 argument-parser bug — the parsing loop
  (`scripts/dev/safe-doc-push.sh`) now has an explicit `--agent` no-op case (mirroring quickmerge.sh's convention) and
  rejects any other unrecognized `-*`/`--*` token with a clear "unrecognized flag" usage error instead of silently
  adopting it as `BRANCH`. Added `scripts/dev/test-safe-doc-push-agent-flag-parsing.sh`, mirroring
  `test-safe-doc-push-stash-recovery.sh`'s style: case 1 proves `--agent --files <f>` lands the commit on
  `live-defi-rollout` unmodified; case 2 proves an unrecognized flag (`--bogus-flag`) exits 2 with the new usage
  error instead of corrupting the fetch/pull/push branch. Both cases pass locally. Shipped
  `unified-trading-pm@7adc383c84`. P2 (audit every other `$BRANCH` usage) and P3 (CLAUDE.md/SUB_AGENT_MANDATORY_RULES
  doc-parity update) remain open, tracked above — out of scope for this task.
