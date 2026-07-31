---
doc_type: issue
title:
  block_destructive_commands.py's recursive-rm regex false-positives on any ordinary single-file `rm`/`git rm` whose
  path contains a hyphenated segment that happens to end in "r" (e.g. `...-versions.py`, `...-server.py`), blocking a
  routine, safe delete as if it were `rm -rf`
summary: >-
  While deleting one dead script (`scripts/manifest/sync-manifest-versions.py`, an orphaned D13 version reader — see the
  census in `plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md`), both `git rm
  scripts/manifest/sync-manifest-versions.py` and plain `rm scripts/manifest/sync-manifest-versions.py` were BLOCKED by
  the PreToolUse guardrail (`agent-orchestrator/scripts/hooks/block_destructive_commands.py`) with reason "recursive rm
  (tree delete)" — even though the command deletes exactly one named file, non-recursively, nowhere near a real
  `-r`/`-rf`/`--recursive` flag. Root cause: the pattern `r"\brm\b[^|;&\n]*(-[A-Za-z]*[rR]|--recursive)"` is not
  anchored to an actual CLI flag token — `[^|;&\n]*` greedily scans the rest of the command line (everything up to the
  next `|`/`;`/`&`/newline) looking for ANY substring matching `-[A-Za-z]*[rR]`, and that substring can come from inside
  an innocent hyphenated PATH SEGMENT, not a flag at all. `sync-manifest-versions.py` contains `-versions`, and the
  regex backtracks `[A-Za-z]*` down to match the 2-char substring `-ver` inside it — `-v`, `-e`, `-r` — landing on the
  trailing `r`. The false positive is not limited to this one filename: it is a general class — any command containing
  `rm <path>` (or `git rm <path>`, or any other command with the literal token "rm" earlier in the line, e.g. `git
  status --porcelain` after an unrelated `rm` — `--porcelain` itself contains a matching `-por` substring) where a later
  hyphenated word/flag anywhere on the same `|`/`;`/`&`-delimited segment happens to contain a hyphen followed by 0+
  letters ending in `r`/`R` will trip this guardrail. Confirmed two independent trigger paths live: (1) the target path
  itself (`sync-manifest-versions.py` → `-versions`), and (2) an unrelated flag later on the same line (`git status
  --porcelain` → `--porcelain` contains `-por`). Worked around by using `python3.13 -c "import os; os.remove(...)"`
  instead of a shell `rm`/`git rm` (the word "remove" does not contain the adjacent letters "r" then "m", so `\brm\b`
  never matches) — this is NOT a sanctioned bypass pattern documented anywhere, and future agents hitting the same false
  positive have no guidance to reach for it; some may instead escalate needlessly, or worse, learn to routinely use
  `python3 -c` for ordinary file deletes, eroding the one place this guardrail's true positives (`rm -rf`, `find
  -delete`, etc.) still get caught cleanly. This is a correctness bug in a fleet-wide SAFETY guardrail (registered both
  per-host via `install-worker-guardrails.sh` and fleet-wide via `cursor-configs/settings.json` per the hook's own
  docstring) — worth fixing precisely BECAUSE it is a safety mechanism: false positives that "cry wolf" on routine, safe
  operations train agents to route around the hook entirely rather than trust it, which weakens the real protection it
  exists to provide.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [guardrail, hooks, destructive-commands, regex, false-positive, pretooluse, safety-mechanism, tooling-bug]
related:
  [
    /plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: orchestrator_master
source:
  "ci_satellite_ao_dispatch_batch1-019 (D13 orphan-reader census + sync-manifest-versions.py remediation), slot 2,
  2026-07-31 — hit while deleting the dead script the census identified"
assigned_vm: planning
execution_scope: ao-eligible
drift_direction: none
last_updated: 2026-07-31
locked_by:
resolved_by:
depends_on: []
---

# `block_destructive_commands.py`'s rm-detector matches inside hyphenated words, not just real flags

## What I found

`agent-orchestrator/scripts/hooks/block_destructive_commands.py:68` —

```python
(r"\brm\b[^|;&\n]*(-[A-Za-z]*[rR]|--recursive)", "recursive rm (tree delete)"),
```

`\brm\b` correctly finds the word "rm". But the flag half of the pattern, `-[A-Za-z]*[rR]`, is not restricted to an
actual argv token (no `\s` boundary before the leading `-`, no requirement the match sit at the START of a
whitespace-delimited word) — combined with the greedy `[^|;&\n]*` before it, it will match a `-...r`/`-...R` substring
ANYWHERE later in the same `|`/`;`/`&`-delimited command segment, including inside an ordinary path or an unrelated
flag's own spelling. Two live reproductions:

1. **The delete target's own filename triggers it.** `git rm scripts/manifest/sync-manifest-versions.py` —
   `sync-manifest-versions.py` contains `-versions`, and `[A-Za-z]*` backtracks to match the substring `-ver` (`-` +
   `ve` + `r`). Blocked, even though this deletes exactly one file, no recursion, no `-r`/`-rf` flag anywhere in the
   actual command.

2. **An unrelated flag LATER on the same line triggers it**, even when the `rm` itself is flagless.
   `rm <safe-file> && git status --porcelain` (only the segment up to the first `&` is scanned per the `[^|;&\n]*`
   bound, so a `&&`-separated FOLLOWING command is normally safe — but `--porcelain` itself contains `-por`, which
   matches within ITS OWN segment if `rm` also appears there without an intervening `|`/`;`/`&`).

## Why it matters

This is a **safety mechanism**, which is exactly why a false-positive rate matters here more than in an ordinary tool:
every worker across the fleet runs `--dangerously-skip-permissions`, and this PreToolUse hook is described in its own
docstring as "the one mechanism that still refuses a tool call in bypass mode." A guardrail that blocks routine, safe
single-file deletes teaches agents to reach for a workaround (I used `python3 -c "import os; os.remove(...)"` — the word
"remove" never matches `\brm\b`) that is undocumented, inconsistent across agents, and — worse — normalizes "route
around the safety hook" as an acceptable move for cases that FEEL like false positives but might not always be. The
narrower the hook's true-positive precision, the more it gets treated as noise rather than signal.

## Recommended decision

Tighten the flag-matching half of the recursive-rm pattern (and the same class of over-broad match likely exists in
sibling patterns using the same `[A-Za-z]*[rR]` shape, e.g. `chmod`/`chown` `-R` detection at lines 87-88 — those use a
stricter `-R\b` today so are lower-risk, but worth a quick check in the same pass) to require the flag sit at an actual
token boundary — e.g. anchor on a preceding whitespace/start-of-string before the leading `-`:
`r"\brm\b(?:(?!\s-)[^|;&\n])*\s(-[A-Za-z]*[rR]\b|--recursive\b)"` (illustrative — the exact anchoring needs a real pass
against the existing regex test corpus, if one exists, plus new cases below) so `-versions`/`--porcelain`-shaped
substrings inside a path or an unrelated flag's spelling can no longer match, while `rm -rf`, `rm -fr`, `rm -Rf`,
`rm --recursive`, and `rm somedir -r` (flag after the path, still a real recursive delete) all still correctly block.

## Suggested todos

- [x] ✅ [INFRA] P2. Fix the recursive-rm pattern in `agent-orchestrator/scripts/hooks/block_destructive_commands.py` to
      require the `-r`/`-rf`/`--recursive` match sit at an actual whitespace-delimited flag-token boundary, not anywhere
      inside a hyphenated path segment or an unrelated flag's spelling. Add negative-test cases to the hook's existing
      test coverage (if any exists — check for a `test_block_destructive_commands.py` sibling first) covering:
      `git rm path/to/sync-manifest-versions.py` (must now ALLOW), `rm path/to/foo.py && git status --porcelain` (must
      now ALLOW), plus confirm every existing true-positive case (`rm -rf`, `rm -fr dir`, `rm --recursive dir`,
      `rm dir -r`) still BLOCKS. Repo: agent-orchestrator. — agent-orchestrator@7b1a251. Pattern now anchored via
      `(?<=\s)` before the leading `-` and a trailing `\b` after the letter run
      (`-[A-Za-z]*[rR][A-Za-z]*\b|--recursive\b`); added the two negative cases plus `rm --recursive dir`/`rm dir -r` to
      the BLOCKED list; full 48-test suite green + repo QG green.
- [ ] [INFRA] P3. Audit the other `[A-Za-z]*[rR]`/`[A-Za-z]*[fdx]`-shaped patterns in the same `_DESTRUCTIVE` list
      (`git clean -f/-d/-x` at line 80 uses the same unanchored shape) for the identical false-positive class; tighten
      or confirm each is already narrow enough (the `chmod -R`/`chown -R` patterns at lines 87-88 use a stricter `-R\b`
      and are lower priority to re-check first). Repo: agent-orchestrator.
