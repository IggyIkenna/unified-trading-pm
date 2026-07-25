---
doc_type: issue
title: test_build_index_is_deterministic races against concurrent doc-corpus writes on the shared branch
summary: >-
  scripts/docs/test_gen_doc_index.py::test_build_index_is_deterministic asserts `build_index(pm_root) ==
  build_index(pm_root)` — two live filesystem walks of the SAME pm_root with no snapshot in between. On this workspace's
  heavily concurrent shared working tree (many slots/agents committing to plans/active/issues/*.md at once), a doc's
  frontmatter can change between the two calls, producing a spurious diff and a false-negative QG failure. Observed
  directly 2026-07-25: the diff was exactly one issue doc's `status=resolved` -> `status=open` (a concurrent edit
  landing mid-test), not a real determinism bug in build_index()'s own logic.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [testing, flaky, doc-index, concurrency, quality-gates]
related:
  - /plans/active/task_template.md
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: agent_operating_framework_master
assigned_vm:
priority: P3
locked_by:
resolved_by:
source: >-
  Discovered 2026-07-25 during quickmerge of cursor-configs/skills/ag-closeout-audit/SKILL.md — Stage 3 re-gate failed
  on this test, retry with no code change passed clean.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# test_build_index_is_deterministic races against concurrent doc-corpus writes

## What happened

Ran `bash scripts/quickmerge.sh ... --files cursor-configs/skills/ag-closeout-audit/SKILL.md` (a doc-only add, no
relation to `gen_doc_index`). Stage 3's re-gate pass failed on:

```
scripts/docs/test_gen_doc_index.py:25: in test_build_index_is_deterministic
    assert build_index(pm_root) == build_index(pm_root)
E   AssertionError: assert '# UTS docume...ority=P2]\n\n' == '# UTS docume...ority=P2]\n\n'
E     - er status=resolved nature=issue tags=deployment-registry,oom,... priority=P0]
E     + er status=open nature=issue tags=deployment-registry,oom,... priority=P0]
```

The diff is exactly one issue doc's `status` field flipping between the two `build_index()` calls inside the same assert
statement — i.e. another concurrent agent committed a `status: resolved` -> `status: open` edit to that doc in the
narrow window between the test's two live filesystem walks. Retrying the identical quickmerge command immediately after
(no code change) passed clean. This is the SAME class of transient failure this session hit repeatedly on
`check-branch-drift` (heavy concurrent multi-agent write pressure on `live-defi-rollout`), just surfacing through a
different gate.

## Root cause

`scripts/docs/test_gen_doc_index.py::test_build_index_is_deterministic` (line 25) calls
`build_index(gen_doc_index._pm_root())` twice back-to-back and asserts byte-equality, walking LIVE disk state both times
with no snapshot/fixture in between. The test's actual intent (per its own comment, line 24: "the whole point of
consumer-side-local + gitignored: two regens are byte-identical") is to prove `build_index()`'s ALGORITHM is
deterministic for a fixed input — it accidentally also asserts the _input corpus itself_ doesn't change between the two
calls, which is false on this workspace under normal concurrent-agent load.

## Recommended fix (not applied — outside this session's scope, filing for whoever picks this up)

Make the test corpus-invariant instead of racing live disk:

- Build the index ONCE from live `pm_root`, then assert calling `build_index` again **on a `tmp_path` fixture seeded
  with a frozen copy of a handful of representative docs** is stable — proves the algorithm is deterministic without
  depending on the live, mutable corpus staying still for the test's duration.
- Simpler alternative: snapshot `pm_root`'s file list + mtimes immediately before both calls and skip (not fail) if it
  changed between them — an explicit "corpus mutated mid-test, inconclusive" skip is honest; a bare AssertionError is
  not.

## Impact

Low severity (P3) — this is a nuisance flaky-retry, not a correctness bug in the index generator itself (confirmed: the
diff is real concurrent state, not corrupted output). But it costs every slot a full ~76s re-gate + investigation each
time it fires, on a branch with confirmed heavy concurrent write pressure all session. Worth fixing opportunistically,
not urgent.

## Todos

- [ ] [SCRIPT] P3. Rewrite `test_build_index_is_deterministic` to build from a frozen `tmp_path` fixture (or
      snapshot+skip-on-mutation) instead of two live walks of the shared `pm_root`, per the recommended fix above.
      **Done when**: the test no longer reads live `plans/active/**` twice within its own body, and a manual repro
      (touch a doc's frontmatter between the two `build_index` calls via a debugger/sleep) no longer fails it.
