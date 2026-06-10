---
title: "QG sentinel is SHA-based → unwinnable race vs concurrent LDR writers; content-hash + slicing would restore fast-ship"
created: 2026-06-10
source:
  - slot-3 live experience 2026-06-10 shipping deployment-api data-status STEP 5.90 fix + flaky-test fix
  - deployment-api QG ran ~5× and lost the sentinel race each time to unrelated slot-2 commits
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

The two-pass quickmerge gate keys on a **commit-SHA sentinel**: `quality-gates.sh` stamps
`.qg_last_passed_sha = HEAD`, and `quickmerge` refuses unless `sentinel == HEAD`. When another agent (or the
promotion automation / backmerge-bot) pushes to `live-defi-rollout` during your QG run, quickmerge's not-behind
gate fast-forwards your HEAD, the sentinel goes stale, and it refuses — **even though the incoming commits do not
touch a single line of the files you are shipping**.

Observed 2026-06-10: shipping a one-line comment marker + a 15-line test fixture to deployment-api took ~5 full QG
runs (7–8 min each) because slot-2 was committing `repo_ci` work every ~2 min. Each unrelated commit invalidated a
green gate. The deployment-api change only landed when slot-2 paused for ~8 min (22:06–22:14).

By contrast, the **carve-out direct push** for the non-Python PM change (bash gate + markdown codex) landed in
**seconds** — confirming the latency is the two-pass sentinel itself, not git, the network, or the gate logic.

Root multipliers:

1. **SHA-based, not content-based** — an unrelated LDR advance stales a still-valid green QG.
2. **Gate latency (7–8 min)** — a full QG (basedpyright + ~4k pytest + ruff + dozens of STEP checks) runs even for a
   markdown/comment change, widening the race window every attempt.
3. **Concurrency** — multiple agents + semver-agent + backmerge-bot all write the same LDR; latency × writers makes
   the race effectively unwinnable for slow gates.

## Why it matters

This is the dominant velocity tax right now. Small, correct, QG-green changes turn into multi-cycle grinds where the
agent spends most of its time re-running quality gates and losing quickmerge races, not engineering. It scales the
WRONG way: the more agents we run concurrently (the whole point of the fleet), the worse the thrash. It also pushes
agents toward carve-out direct pushes to escape the race, which erodes the two-pass discipline the gate exists to
enforce.

## Recommended decision

1. **Content-hash sentinel (highest leverage).** Stamp + verify a hash of the *exact tracked file contents being
   shipped* (or `git diff` of the `--files` set) instead of the commit SHA. An unrelated LDR fast-forward then does
   NOT invalidate a green QG — quickmerge re-verifies the content hash, not the parent commit. This alone kills ~80%
   of the race.
2. **QG slicing by change type.** A pure docs/markdown/comment or bash-only change should not run the pytest suite or
   full basedpyright — gate only the affected slice (the `QG_SLICE` machinery already exists; wire it to the
   `--files` change set). Shrinks the window and the cost per attempt.
3. **(Optional) merge queue for LDR** so concurrent pushes serialize instead of thrashing each other's sentinels.

Owner: cicd / vm-cross-cutting. Pairs with the LDR-trunk promotion-decoupling work already in flight. Until landed,
non-Python changes should use the sanctioned carve-out path (it is v2-gated at LDR→main anyway).
