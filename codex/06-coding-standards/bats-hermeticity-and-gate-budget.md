---
doc_type: codex-ssot
title: Bats suites — hermeticity under parallelism, and what the gate budget actually measures
summary: >-
  `bats -j` cuts WALL time (measured 663s -> 115s on PM's 211 tests) but does NOT reduce CPU, which is what the
  quality-gate budget enforces — only removing work moves that number. Enabling parallelism also exposed seven distinct
  hermeticity defects that were invisible serially: three fixed shared paths, an order-dependent state machine, a
  host-wide production lock taken by tests, cwd-relative script paths, and one over-specified assertion. None were
  caused by parallelism; it revealed they were never isolated. Includes the rule that a suite must pass N consecutive
  parallel runs before its gate may be hard-failed.
authoritative_for: [bats-hermeticity, bats-parallelism, qg-duration-budget, inter-run-shared-state]
status: current
nature: guideline
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [bats, quality-gates, parallelism, flaky-tests, cpu-budget]
related:
  [/codex/06-coding-standards/quality-gates.md, /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md]
created: 2026-08-10
last_updated: "2026-08-12"
owner: infrastructure
last_reviewed: "2026-08-12"
code_refs: [unified-trading-pm/tests, unified-trading-pm/scripts/quality-gates-base/base-service.sh]
referenced_by: []
---

# Bats hermeticity and the gate budget

## The budget is CPU, not wall — parallelism does not help it

`MAX_DURATION` is enforced against `DUR_BILLABLE`, which is **CPU** (user+sys of waited-for children), deliberately, so
host contention cannot false-positive it. Wall is kept only as a loose hang detector at 4x. Consequences, both measured
2026-08-10:

- Parallelising bats cut **wall** 663s -> 115s and left **CPU** unchanged. Latency improved; the budget did not move. A
  claim that parallelism "fixed the cap" is wrong.
- PM's gate breached the cap on CPU alone (658s vs 600s), **blocking every ship from the host regardless of content**.
  The cause was one fixture: a 50,000-iteration bash loop that re-opened its output file on every append, called by
  three tests, ~108s of the suite's ~484s. Replaced by a single `yes "$line" | head -n "$n"` pipeline (output verified
  byte-identical with `cmp`): that file went 108s -> 1s and the gate went to 212s.

**Measure before optimising.** The structural hypothesis — that the 48 tests building a git repo per test dominated —
was wrong. `bats -T` prints per-test durations and finds the real consumer in one pass.

## Seven hermeticity defects parallelism exposed

Serial execution hides shared state, because there is never a second claimant.

| #   | defect                                                               | symptom                                                |
| --- | -------------------------------------------------------------------- | ------------------------------------------------------ |
| 1   | fixed shared fixture path (`$BATS_TMPDIR/workspace`)                 | shifting failures across files sharing the helper      |
| 2   | fixed probe path inside `plans/active/`                              | one test's teardown deleting a file another asserts on |
| 3   | fixture `cp`-ing a script deleted months earlier                     | 42 tests dying in `setup`, asserting nothing           |
| 4   | order-dependent state machine sharing file-scoped state              | 2-3 failures that MOVED between runs                   |
| 5   | tests taking a host-wide production lock (`push-host-governor`, K=8) | exit codes depending on unrelated fleet activity       |
| 6   | cwd-relative script paths + a `cd` that can silently land elsewhere  | passed 5/5 serially, failed ~1 in 3 parallel           |
| 7   | over-specified assertion (`-eq 3` on a retry count)                  | red while the thing under test worked perfectly        |

**Fixes, in preference order:**

- Make the path unique per test (`$BATS_TEST_TMPDIR`, or `$$`/`$BATS_TEST_NUMBER` when the file must live in a specific
  directory for the code under test to see it).
- Derive paths from `$BATS_TEST_FILENAME`, never from the working directory — a `cd` whose input comes from a subprocess
  (`git rev-parse`) can silently land elsewhere under load.
- Never let a test take a real host lock. Use the documented bypass (`PUSH_GOV_DISABLE=true`); a hermetic test must not
  participate in production concurrency control.
- `export BATS_NO_PARALLELIZE_WITHIN_FILE=true` in `setup_file()` for suites that genuinely walk a state machine across
  tests. Parallelism across files is unaffected.
- Assert the **property**, not an implementation detail. `-eq 3` on a consecutive-failure counter pinned machine timing;
  the real claim was "short-circuits instead of burning all 6 retries" (`>=3` and `<6`), and the exit code plus messages
  already pinned the behaviour precisely.

**Do NOT** fix these by sharing one fixture across tests in a file. It is cheaper and reintroduces exactly this class.
Build the fixture per test; if that is expensive, build a template once in `setup_file()` and `cp -R` it per test — one
process instead of ten, isolation intact.

## An eighth defect, structurally invisible to that sweep: shared state across RUNS, not across tests

The seven above were exposed by `bats -j` — parallelism **within** one run. A defect whose second claimant is a
_different invocation of the whole suite_ cannot be found that way, no matter how many times you run `bats -j`. On a
multi-slot host that second claimant is routine: two slots gating at the same time run the same suite concurrently.

Measured 2026-08-12, and it had survived the 2026-08-10 sweep untouched:

```bash
tmp_ping="$(mktemp /tmp/slot_test_XXXX.md)"   # ← creates the LITERAL path /tmp/slot_test_XXXX.md
```

**`mktemp` substitutes only TRAILING X's.** With any suffix after them (`.md`, `.log`), BSD `mktemp` treats the template
literally, so every caller on the host gets the _same_ filename. Two overlapping runs then collide 100% of the time
(`mkstemp failed on /tmp/slot_test_XXXX.md: File exists`), and a run that dies before its cleanup leaves the file
behind, wedging **every** later run host-wide until someone deletes it by hand. Verify with
`mktemp /tmp/probe-XXXXXX.log` — it prints `/tmp/probe-XXXXXX.log`, unsubstituted.

It cost two consecutive PM gate failures while a peer slot gated concurrently, and four call sites carried it
(`tests/test_tab_worktrees.bats` ×2, `scripts/workspace/workspace-bootstrap.sh`,
`scripts/validation/pre-push-watcher.sh`). Fix: trailing X's with no suffix (`mktemp /tmp/name-XXXXXX`), or a unique
DIRECTORY when the extension matters (`mktemp -d /tmp/name-XXXXXX` then build the file inside it).

**Why this class survives, and the diagnostic rule that catches it.** It presents as a flake, and re-running genuinely
works — whenever the other run has finished. So the standing advice ("transient, re-run it") is locally correct and
globally wrong, and the defect persists indefinitely. Two rules:

- **Two IDENTICAL consecutive failures mean the condition is stable.** Stop re-running and diagnose. A _different_
  failure each time is contention; the _same_ failure twice is a defect.
- **An empty `/tmp` is not evidence of "random collision".** The first diagnosis here checked for leftovers, found zero,
  and concluded a rare random clash — but zero leftovers is _equally_ consistent with a fixed filename that exists only
  while a run is in flight. The distinguishing test is one line: run `mktemp` with the template and read the output.

Generalise past `mktemp`: any test-adjacent artifact keyed on a **constant** name in a host-shared location (`/tmp`, a
host lock, a fixed port, `~/.cache/<tool>`) is inter-run shared state. `$BATS_TEST_TMPDIR` solves the intra-run case and
does nothing for this one.

## Before hard-failing a warn-only suite: N consecutive green runs

A suite whose gate is `NON-FATAL transitional` must pass **at least three consecutive full parallel runs with an
identical (ideally empty) failure set** before the gate is re-hardened. One green run is not evidence.

The tell is the **failure SET, not the count**. On 2026-08-10 the count fell 60 -> 17 -> 12 -> 6 -> 5 -> 1 while
membership kept changing — that shifting membership is the signature of flakiness, and each "final" number was reported
too early. Repeat-runs should start the first time the set moves, not at the end. Hard-failing a gate against an
intermittently-red suite is worse than leaving it warn-only: it blocks ships at random and trains people to bypass it.

## A test whose subject is gone does not fail loudly — it dies in setup

42 of PM's 60 bats failures were one fixture `cp`-ing `scripts/sync-rules-push.sh`, deleted 2026-03-02. Those tests
failed in `setup` before any assertion, so for five months they asserted nothing and could never go green — absorbed
into a warn-only count nobody read. Two were genuinely obsolete and were deleted; the third tested live code and was
revived by narrowing the fixture.

**Make fixtures fail loudly when their subject disappears** rather than silently setting up an empty world:

```bash
if [ ! -f "$REAL_SCRIPTS_DIR/_workspace-lib.sh" ]; then
    echo "setup: subject missing — delete this suite or restore it" >&2
    return 1
fi
```

Related trap: never locate anything by hardcoded line number. `FN_DEFS_END_LINE=712` extracted a script's helper
definitions; the script grew past 1000 lines, the cut landed mid-function, the prefix stopped parsing, and six tests
failed with errors that read as though the code under test were broken. Use a marker the file itself carries, so
removing it fails loudly instead of rotting silently.
