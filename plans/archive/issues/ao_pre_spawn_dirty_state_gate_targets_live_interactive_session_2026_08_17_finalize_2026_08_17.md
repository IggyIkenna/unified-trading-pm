---
doc_type: issue
title: Finalize — AO pre-spawn dirty-state gate fired against a live interactive session
summary: >-
  Gated finalize for the retroactive RECLASSIFY of
  `ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md` (assigned_vm flipped NA ->
  planning in place, name unchanged, per the na-eligibility-audit reclassification pairing convention).
  Verifies the 3 landed fixes actually close the near-miss (a live re-trigger test, not just a code read), then
  archives the source doc.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, finalize, na-eligibility-audit, agent-orchestrator]
related:
  [
    /plans/archive/issues/ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
parent_epic: orchestrator_master
created: "2026-08-17"
last_updated: "2026-08-19"
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: review
drift_direction: advance-code
depends_on: [ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "interactive session, slot 3, 2026-08-19 — agent-orchestrator@ad00fb7b38"
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/issues/ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md,
  ]
source: >-
  Mandatory finalize companion for a na-eligibility-audit retroactive RECLASSIFY, per the naming/pairing
  convention in `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1(b).
---

# Finalize — AO pre-spawn dirty-state gate fired against a live interactive session

> **🟢 RESOLVED 2026-08-19** — both todos closed. Live-verified all 3 source-doc fixes with real, non-mocked
> reproductions of the original failure shape (real background process for the liveness probe; real bare-remote
> git clone for the push-verification + realign-scoping fixes) — see each todo below for the full transcript
> summary. `agent-orchestrator@ad00fb7b38`. Archived alongside its source doc,
> `plans/archive/issues/ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md`.

- [x] [REVIEW] P1. ✅ Verify the 3 fixes actually resolve the near-miss, not just that the code changed: (1) the
      liveness-check fix — confirm it against a real or faithfully-simulated live interactive session with no
      recent commit, not just a unit test of the check in isolation; (2) `DirtyStateResolution.COMMIT_AND_PUSH` —
      confirm a genuinely-dead predecessor's orphan-wip commit actually reaches `origin` now, live; (3) the
      reset-to-origin scoping decision — confirm whatever was decided (keep, remove, or condition it) behaves as
      intended. Done-when: each of the 3 has a live-verification citation, not a code-read-only claim. —
      **agent-orchestrator@ad00fb7b38**, verified 2026-08-19 by running actual, non-mocked reproductions (not just
      the shipped unit tests) against the exact failure shape:
      (1) **Liveness** — spawned a REAL background process (`python3 -c "import time; time.sleep(60)"`, no
      filesystem path anywhere in its own argv — the exact "bare interactive REPL" shape) with `cwd` set to a
      throwaway slot directory, on THIS session's own macOS host, with no `.agent-claim` and `recent_edit=False`
      (matching `_sweep_dirty_slots`'s call shape). `classify_maker_liveness(..., replacing_session=None,
      worker_alive_fn=lambda _: False)` correctly read **`live`** while the process was running (via the new
      `_default_proc_cwd_live` → `psutil` triangulation), then correctly flipped to **`absent`** immediately after
      the process was killed — confirming both directions, not just "always says live." Also directly confirmed
      `ls /proc` fails on this host (`No such file or directory`) — live, concrete proof the OLD `/proc`-based
      implementation was structurally incapable of ever producing the `live` verdict here, i.e. would have
      reproduced the exact false-dead misclassification the incident describes.
      (2)+(3) **Push verification + realign scoping** — built a real bare-remote + Path-B clone (mirroring the
      test harness), dirtied a file, and called `commit_and_push_dirty_repos(..., replacing_session=None,
      protect_live_peer=False)` for real (no mocks). Result: `OrphanCommit(pushed=True, error=None)`; `git reflog`
      on the clone shows ONLY the two real commits (`seed`, `chore(orphan-wip): ...`) — **no `checkout`/`reset`
      entries at all**, unlike the incident's own reflog signature; HEAD is genuinely ahead of
      `origin/live-defi-rollout` (not reset to match it); `git log --oneline` shows the orphan commit directly as
      HEAD (recoverable with zero reflog archaeology); and `git ls-remote --exit-code origin
      'refs/heads/wip-preserve/*'` independently confirms the preserve ref is genuinely reachable on origin with
      the matching sha — proving the verification step reflects reality, not just a trusted return code. Full
      transcripts of both live repros are in this session's tool-call history (agent-orchestrator working tree,
      2026-08-19); the shipped commit also carries `test_orphan_skips_realign_when_no_replacing_session` and
      `test_orphan_skips_realign_and_flags_error_when_push_verification_fails` as permanent regression coverage
      for the exact same shapes.
- [x] [DOC] P2. ✅ Once every todo in the source doc is `[x]` and unlocked, run the standard 6-step archival ritual
      on `ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md`, then archive this
      finalize doc alongside it. — Done this same pass: codex updated
      (`/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Pre-spawn dirty-state gate hardening",
      `unified-trading-pm@<see next doc-push evidence>`), the one live `related:`-adjacent referrer with a hard
      path (`plans/active/cefi_tardis_date_concurrency_2026_08_16.md`) repointed to the archive path + the codex
      section, both docs banner-stamped and moved to `plans/archive/issues/` (flat, per `doc_type: issue`).

## Progress Log

- **2026-08-17 (na_eligibility_auditor, dispatch agt-7e78e2, slot 28)**: drafted alongside the source doc's
  RECLASSIFY (whole-doc) per the mandatory finalize-plan rule.
