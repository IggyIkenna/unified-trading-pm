---
doc_type: issue
title: >-
  check_prosewrap_padding.sh's --only mode throws "sort: Illegal byte sequence" under the default shell locale and
  false-flags byte-identical HEAD content as a NEW violation
summary: >-
  `scripts/plan-hygiene/check_prosewrap_padding.sh --only` (the pre-commit-hook path added 2026-08-09, rec. A of
  `prosewrap_padding_precommit_gate_blocks_already_affected_files_2026_08_09.md`) pipes UTF-8 content (em-dashes,
  checkmarks, curly quotes) through `sort`/`comm` to compute the HEAD-vs-staged content-diff that distinguishes a
  genuinely new violation from prose that merely got reflowed past the threshold this pass. Under this shell's default
  locale, `sort` throws `sort: Illegal byte sequence` and silently produces a truncated/empty comparison set — every
  over-indent hit then reads as "not found in HEAD" and gets flagged as NEW, even when the file is byte-identical to
  HEAD (reproduced: checked out a file at exactly HEAD, ran the checker against it unmodified, got a false failure).
  `LC_ALL=C` fixes it — the same command against the same file with `LC_ALL=C bash check_prosewrap_padding.sh --only
  <file>` passes cleanly. Independently hit and root-caused twice today (main coordinating session + a dispatched
  sub-agent both spent significant time on it before finding the same fix), each initially chasing it as a real content
  problem via manual whack-a-mole re-indentation before discovering it was a pure environment artifact.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, prosewrap, locale, false-positive, pre-commit, quality-gates, worktree]
related:
  [
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
    /plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-16"
author: interactive-session (main coordinator) + dispatched sub-agent, independently
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: infra
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: unified-trading-pm@e4818c6747 (both todos done — LC_ALL=C pinning + _sort_or_die exit-code checking)
source: >-
  Discovered independently by two concurrent workers in the same session today (2026-08-09) while trying to land
  unrelated `docs(plans):` commits — both initially spent real time manually re-indenting content that turned out to
  already be correct, before tracing the actual failure to a `sort` locale crash rather than genuine prosewrap
  corruption.
context_scope:
  [
    scripts/plan-hygiene/check_prosewrap_padding.sh,
    plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
  ]
---

> **🟢 ARCHIVED 2026-08-16** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:`. The corpus-wide prosewrap-padding remediation
> backlog (unrelated to this doc's own detector bug) lives on in
> [`/plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md`](/plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md).

# check_prosewrap_padding.sh `--only` mode: locale-dependent false positive

## What was found

`check_prosewrap_padding.sh --only <file>` is the pre-commit-hook path (added 2026-08-09, per
`prosewrap_padding_precommit_gate_blocks_already_affected_files_2026_08_09.md`'s rec. A) that distinguishes a genuinely
new prosewrap-padding violation from pre-existing prose that merely got reflowed past the `INDENT_THRESHOLD` (14 spaces)
by this pass's mandatory `prettier-autostage` run. Its detection logic (lines ~127-186) computes `comm -23` between the
current over-indent hits and a content-preview of every line in `HEAD`'s version of the file, both piped through
`sort -u` first.

Under the default shell locale in this session's worktree environment, any input containing multi-byte UTF-8 characters
(em-dashes `—`, curly quotes, checkmarks `✅`) makes `sort` fail with `sort: Illegal byte sequence`. The script does not
check `sort`'s exit code, so this failure is silent — `comm` then compares against a truncated or empty set, and every
over-indent hit reads as "absent from HEAD," triggering a false "NEW violation" verdict.

**Reproduced cleanly**: checked out a file at exactly `HEAD` (zero working-tree diff, confirmed via `git status`), ran
`check_prosewrap_padding.sh --only <file>` against the unmodified file, and it still reported "1 staged file(s) with a
NEW prosewrap-padding instance." Running the identical command with `LC_ALL=C` prepended passed cleanly
(`0 new violation(s)`).

## Impact

Two independent workers in today's session (2026-08-09) each hit this on unrelated commits, and each initially treated
it as a real content problem — manually re-indenting paragraphs that were already correct, retrying the commit, watching
the gate flag a _different_ paragraph the next pass (since `prettier-autostage`'s own non-idempotent reflow bug, the
subject of the two related docs above, genuinely does touch a different paragraph each run on a large enough file), and
concluding — wrongly — that the file was in an unwinnable whack-a-mole state. Real time was lost before the locale root
cause was found. Given the shared-checkout, multi-session nature of this workspace today, other concurrent sessions
plausibly hit the same wall silently and either gave up or routed around it some other way.

## Recommended fix

- [x] ✅ [BACKEND] P2. Add explicit locale pinning (`LC_ALL=C` or equivalent) to every `sort`/`comm` invocation inside
      `check_prosewrap_padding.sh`'s `--only` branch (and check the corpus-wide mode for the same gap), OR set
      `LC_ALL=C` once at the top of the script before any content processing. Verify the fix with a UTF-8-heavy fixture
      (em-dash, checkmark, curly quote) under a non-`C` locale, both before (reproduce the crash) and after (confirm
      clean). — unified-trading-pm@fa34c097e: added `export LC_ALL=C` right after `set -uo pipefail` (covers the
      `--only` branch's sort/comm calls; corpus-wide mode never calls sort/comm, so no separate change needed there).
      Could not reproduce the literal "Illegal byte sequence" crash on this host — the available locales (`C`, `C.utf8`,
      `POSIX`, `en_US.utf8`) all handled the em-dash/checkmark/curly-quote fixture without erroring
      (glibc/locale-gen-set difference from the originating session); applied the fix defensively per the issue's own
      "OR set LC_ALL=C once at the top" option regardless, since it's strictly correct here (only exact-match set
      membership is needed, never locale-aware ordering) and eliminates the whole failure class. Verified no regression:
      `--only` still correctly flags a genuinely new over-indent line and still passes a byte-identical HEAD file
      cleanly (0 new violations) under both `C.UTF-8` and `en_US.utf8`; corpus-wide total is unchanged before/after
      (4656 vs baseline 4472 — pre-existing debt tracked in
      `/plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md`, not a regression from this change).
- [x] ✅ [SCRIPT] P3. Check `sort`'s exit code explicitly wherever this script pipes through it, so a future
      encoding/locale regression fails loudly (a hard error) instead of silently degrading into a false positive that
      looks like a real content issue. — unified-trading-pm@e4818c6747: added a `_sort_or_die` helper (right after the
      `export LC_ALL=C` line) that every `sort -u` call in the script now routes through — it checks sort's own exit
      code and, on failure, prints a diagnostic pointing at this issue doc and hard-exits (2) instead of letting the
      caller silently continue on truncated/empty sort output. The `--only` mode's backtick-padding and over-indent
      detectors first capture their pre-sort content via the existing `grep | sed` pipe (tolerating grep's normal
      "no matches" exit 1 with `|| true`, unchanged from before), THEN pipe that captured content through a separate,
      isolated `printf | _sort_or_die` 2-stage pipe — deliberately NOT chaining `_sort_or_die` directly onto the
      grep/sed pipe, because pipefail's aggregate exit status cannot distinguish grep's ordinary no-match exit 1 from
      a genuine sort failure once both are stages of the same pipe (confirmed by an earlier draft of this fix: it
      falsely hard-failed on totally normal input with zero violations). Verified: (1) normal `--only` run against
      this script itself still passes cleanly (0 new violations, exit 0); (2) full corpus-wide baseline mode
      (`--quiet`) and `--diff-base HEAD` mode both still pass unchanged; (3) fault-injected a fake `sort` binary ahead
      in `PATH` that fails with `Illegal byte sequence` (the exact real-world crash this issue documents) — confirmed
      the script now prints the diagnostic and hard-exits 2, instead of the prior silent-degradation false positive.

## Progress Log

- **2026-08-09**: found independently by the main coordinating session and a dispatched sub-agent within the same
  working session, both diagnosing what looked like an unwinnable prettier whack-a-mole before tracing it to this locale
  bug. Filed as its own issue rather than folded into the sibling prosewrap docs, since the root cause here is unrelated
  to prettier's own reflow bug — it's a bug in the _detector_ meant to tolerate that reflow bug, not the reflow bug
  itself.
- **2026-08-16**: both todos now done (P2 `LC_ALL=C` pinning landed 2026-08-09; P3 explicit `sort` exit-code checking via
  a `_sort_or_die` helper landed this session, `unified-trading-pm@e4818c6747`). Archiving per the
  plan-completion-and-archival-discipline hard rule.
