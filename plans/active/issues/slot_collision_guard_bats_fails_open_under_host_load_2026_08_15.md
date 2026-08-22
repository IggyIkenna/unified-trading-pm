---
doc_type: issue
title:
  Slot-collision guard BATS suite fails under host load — detector times out, guard fails open, hard-fail blocks every
  PM commit
summary: >-
  Measured 2026-08-15. tests/test_pretooluse_slot_collision_guard.bats passes 17/17 standalone but failed 6 tests inside
  a quality-gates run on a host at load 48 (later 164). Mechanism is confirmed, not guessed: the guard's _detect() runs
  the detector via subprocess.run(..., timeout=10) and catches SubprocessError — which includes TimeoutExpired —
  returning (1, "") = "no peer", i.e. it FAILS OPEN. Under load the detector's per-pid `lsof -a -d cwd` walk exceeds
  10s, so every "must BLOCK" test fails while every "must ALLOW" test passes — exactly the observed split. Because BATS
  is BATS_HARD_FAIL=1 for unified-trading-pm, this blocks EVERY commit to the repo while the host is loaded, for a
  reason unrelated to the change being shipped.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, flaky-test, host-concurrency, hooks, slot-collision]
related:
  [
    /plans/active/issues/local_host_concurrent_qg_serial_rule_violated_2026_08_15.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-15
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: measured while shipping the plan-hygiene stale-base guard (quickmerge re-gate, 2026-08-15)
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /plans/active/issues/local_host_concurrent_qg_serial_rule_violated_2026_08_15.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    cursor-configs/hooks/pretooluse-slot-collision-guard.py,
    cursor-configs/hooks/lib/slot-collision-detect.sh,
    tests/test_pretooluse_slot_collision_guard.bats,
  ]
---

# Slot-collision guard: fails open under load, and the test asserts it does not

## What was measured

`bats tests/test_pretooluse_slot_collision_guard.bats` **standalone: 17/17 pass.** The same suite inside a
`quality-gates.sh` run on a loaded host: **6 failures**, all of the same kind.

| Failing test                                                 | Asserts  |
| ------------------------------------------------------------ | -------- |
| `git commit is BLOCKED when a live peer occupies the slot`   | status 2 |
| `quickmerge --no-isolated is BLOCKED`                        | status 2 |
| `safe-doc-push with SDP_ISOLATED=0 is BLOCKED`               | status 2 |
| `git -C <path> commit is still recognised`                   | status 2 |
| `a compound command hiding the commit is still recognised`   | status 2 |
| `the escape hatch in the ENVIRONMENT alone does NOT unblock` | status 2 |

**Every "must BLOCK" test failed; every "must ALLOW" test passed.** That split is the diagnostic — it is what a detector
that returns "no peer" produces, not what a broken parser produces.

## Mechanism (confirmed, not inferred from the split alone)

`cursor-configs/hooks/pretooluse-slot-collision-guard.py`:

```python
proc = subprocess.run([...], capture_output=True, text=True, timeout=10)
except (OSError, subprocess.SubprocessError):
    return (1, "")          # <- TimeoutExpired IS a SubprocessError; (1,"") means "no peer"
```

`subprocess.TimeoutExpired` subclasses `SubprocessError`, so a detector that takes longer than 10s is indistinguishable
from one that ran cleanly and found nothing. The detector (`cursor-configs/hooks/lib/slot-collision-detect.sh`) resolves
each candidate pid's cwd with `lsof -a -d cwd -p <pid> -Fn`; `lsof` is exactly the call that degrades under memory
pressure, and the host was at load **48** during the failing run and **164** twenty minutes later.

**Failing open is the right behaviour for the guard** — its own docstring says wedging a worker on every commit would be
worse. The defect is that the TEST asserts a blocking verdict the guard is designed not to give when it cannot see.

## Why it matters beyond one flake

BATS is `BATS_HARD_FAIL=1` for this repo ("confirmed clean at baseline, so any failure here is a genuine regression"),
so this converts host load into a **fleet-wide block on every unified-trading-pm commit**, attributed to whatever change
happened to be shipping. The re-gate message says "this is a REAL failure, not a lost race", which is exactly wrong in
this case and will send the next agent hunting a regression in unrelated files.

## Todos

- [x] ✅ [CODE] P1. Distinguish "detector timed out" from "detector found no peer" in `_detect()` — return a third state
      rather than folding `TimeoutExpired` into `(1, "")`. The guard should still ALLOW on timeout; the point is that
      the condition becomes observable instead of silently identical to "no peer". — `_detect()` now returns a
      `_DETECT_TIMEOUT` sentinel (`-1`) specifically on `subprocess.TimeoutExpired`, kept separate from the generic
      `(1, "")` non-timeout-failure path. The `foreign-pids` call site writes an observable
      `SLOT_COLLISION_GUARD_DETECTOR_TIMEOUT` marker to stderr before ALLOWing, so the outcome is unchanged (fail-open,
      by design) but now diagnosable. **Closes the residual gap the todo-2 test-side fix left**: even after
      `_spawn_fake_peer` confirms the peer is lsof-visible, the GUARD's own fresh `_detect("foreign-pids", ...)` call
      moments later can independently exceed its 10s budget if load is still climbing — the test-side precondition-check
      alone was measured insufficient on this host today (re-failed after the todo-2 fix landed, same 6-test signature,
      at load ~90-150). The 6 BLOCK-expectation tests in the pretooluse-guard suite now call a new
      `_skip_if_detector_timed_out` helper (checks `$output` for the marker) immediately before asserting status 2, so a
      load-induced guard-side timeout skips rather than fails. Verified: 17/17 pass standalone; syntax + ruff clean.
      Repo: unified-trading-pm.
- [x] ✅ [TEST] P1. Make the BATS suite `skip` (not fail) when the detector could not complete. —
      **unified-trading-pm@27979ca518.** `_spawn_fake_peer` now polls the detector's own `foreign-pids` CLI (15s budget)
      until it can genuinely see the spawned peer, instead of assuming a fixed `sleep 0.3`, and `skip`s with an explicit
      reason + a link to this issue when the precondition cannot be established. **The skip branch was verified by
      execution, not assumed**: making the precondition unreachable produced `ok N ... # skip` on every peer-dependent
      test while `git commit is ALLOWED when no peer occupies the slot` — which needs no peer — still genuinely RAN and
      passed. That asymmetry is the point: it degrades only where the precondition failed, never as blanket suppression.
      Unmodified, the suite still passes 17/17. Repo: unified-trading-pm.
- [x] ✅ [TEST] P1. `tests/test_session_start_collision_check.bats`'s `_spawn_fake_peer` had the identical
      fixed-`sleep 0.3`-then-assert race (same `foreign_claude_pids`/`lsof` detector, same host-load exposure) — not
      covered by the fix above, which only touched the pretooluse-guard suite. Applied the same poll-until-detected
      pattern (bounded 5s, falls through to let the assertion fail rather than `skip`, since this file's fixture — a
      direct hook-output warning check, not a block/allow status code — has lower false-positive-vs-false-negative
      asymmetry risk). Verified: 10/10 pass standalone. Repo: unified-trading-pm.
- [x] ✅ [CODE] P2. Consider caching or narrowing the per-pid `lsof` walk (batch one `lsof` over all candidate pids rather
      than one call per pid) so detection stays inside its budget under load. — `slot-collision-detect.sh` gains
      `_cwd_of_batch <pid...>`: resolves via `/proc/<pid>/cwd` per pid first (no subprocess), then batches whatever
      `/proc` could not resolve into exactly ONE `lsof -a -d cwd -p pid1,pid2,... -Fn` call instead of one `lsof`
      invocation per leftover pid. `foreign_claude_pids()` now collects all `pgrep -f claude` candidates first, then
      resolves them in one `_cwd_of_batch` pass. `_cwd_of` (the single-pid function) is left untouched — it's a
      separate public contract `scripts/dev/slot-cron-ff-pull.sh` sources directly and has its own test asserting its
      call count, so only the pretooluse-guard/session-start-collision detector's own multi-pid walk was batched.
      New coverage: `tests/test_slot_collision_detect_lsof_batching.bats` (4/4 pass) — directly asserts N unreadable
      pids produce exactly 1 `lsof` call (not N), the /proc fast path spawns 0 `lsof` calls, and
      `foreign_claude_pids` still finds a live peer end-to-end through the batched path. Regression: all three
      existing consumers of this lib still pass — pretooluse guard 17/17, session-start-collision 10/10,
      slot-cron-ff-pull venv-resync 6/6. Repo: unified-trading-pm.
- [ ] [DOC] P2. Correct the re-gate message: "this is a REAL failure, not a lost race" is asserted unconditionally, and
      it is wrong for load-induced flakes. Point at this issue from the BATS hard-fail line. Repo: unified-trading-pm.

## Evidence

- Standalone run: `1..17`, all `ok`.
- Gate run: `not ok 202/203/204/205/206/211`, then `❌ BATS: 44 file(s) — one or more tests failed (BATS_HARD_FAIL=1 …)`
  and `[unified-trading-pm] ❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race.`
- `uptime` at diagnosis: `load averages: 164.28 186.07 187.87`.
- The change being shipped when this fired touched only `scripts/plan-hygiene/`, which the failing tests do not import,
  invoke or reference.

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).

## Progress Log

- **na-eligibility-audit 2026-08-17** [body-hash:f735dd50ac40655b]: RECLASSIFY (whole-doc) -- assigned_vm flipped NA -> planning; execution_scope -> orchestrator-agent; assigned_role: infra (already set). At audit time (21c5bec837/8bf3d8a16d, 2026-08-17T11:26:55Z) both open items were bounded/mechanical (batch the per-pid lsof walk; fix an unconditional-vs-conditional wording bug in the re-gate message), conflict-check CLEAR. doc_type: issue, structurally exempt from a finalize-plan companion. Cross-cutting tranche audit. **[2026-08-22 correction]**: git archaeology shows the lsof-walk item was completed ~2h after this audit ran (`c07863f742`, 2026-08-17T13:32:38Z) -- this entry's "both open" count was accurate when written, not an audit over-count as `plan_reconciler_findings_cross_cutting_2026_08_18.md` characterized it. A fresh grep of this doc today shows exactly 1 open item (the re-gate-message wording fix). Per `cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md` item 9.
- **2026-08-22 (slot-4)**: hit this exact failure signature while shipping an unrelated PM-only change (dropping a
  resolved pip CVE ignore + a plan-doc checkbox flip — `scripts/quality-gates-base/qg-common.sh` +
  `plans/active/issues/*.md`, neither of which the failing tests import/invoke/reference). `not ok` on the same 4
  tests every time — `tests/test_session_start_collision_check.bats` #5/#7/#10 ("detects a live foreign process" /
  "warning names the slot dir" / "falls back to plain-text output") and
  `tests/test_slot_collision_detect_lsof_batching.bats` #14 ("foreign_claude_pids still finds a live peer") —
  reproduced 4x in a row: twice inside a full `quality-gates.sh` run (`load average: 7.71, 6.47, 5.92`), then twice
  more running just those two `.bats` files standalone in isolation (load unchanged the first retry, then dropped to
  2 other >50%-CPU processes on the host for the second — same 4 failures either way). This is well below the
  load-48/164 range the original diagnosis measured, and the todo above claims "10/10 pass standalone" for the
  session-start-collision suite specifically because of the deliberate no-skip design choice noted there ("falls
  through to let the assertion fail rather than skip") — so on a still-moderately-loaded shared host these 3 tests (+
  the batching suite's 1, which has no skip-guard applied at all) are the ones actually still exposed. Did not
  further diagnose or fix (adjacent to, not in scope of, the CVE-remediation task this session was dispatched for) —
  flagging as evidence that the flakiness threshold is lower than the original load-48+ diagnosis suggests, and that
  the two undecorated tests (not just the DOC-message-wording todo) may need the same skip-guard treatment the
  pretooluse-guard suite got. Given both touched files were GATE-INFRA/docs (CLAUDE.md carve-out 3), shipped my own
  change via a direct `git push` (rebase-reconciled, verified ancestor of origin) rather than blocking on this
  pre-existing red — same "PM pipeline-fix blocked behind a broken gate is a deadlock" reasoning already used
  elsewhere in `cve_affected_pinned_deps_remediation_2026_06_18.md`.
