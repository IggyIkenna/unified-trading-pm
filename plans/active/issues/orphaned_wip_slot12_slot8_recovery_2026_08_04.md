---
doc_type: issue
title:
  "Orphaned worktree WIP from the 2026-08-03/04 kill window: slot-12 (killed) holds 3 clean unpushed commits + slot-8's
  bd0e231f (MTDS) stranded 6x on a missing-QG-sentinel — all wip-preserved (zero loss), need mechanical worker rescue"
summary: >-
  Review worktree-health (msg #3630, 2026-08-04 00:06Z) flagged the dead-slot-with-unpushed-WIP case for the current
  kill window. Slot 12 was killed (tmux_session_lost 23:50:31Z) holding THREE small, clean, well-scoped unpushed commits
  its own cascade-verification re-confirmed STILL-ORPHANED at 00:02Z: unified-trading-library c927ec58
  (point_in_time.py, net 0 delta), unified-api-contracts 06c8e90b (defi_venues.py, net 0 delta), deployment-service
  0e62096f (pyproject.toml+uv.lock, net +1). Separately, slot 8's bd0e231f (market-tick-data-service) has been
  reclaimed/preserved SIX times over ~21min (23:38-23:59Z) with a DIFFERENT error than the MTDS qg_red block: 'no
  matching .qg_last_passed_sha sentinel' — i.e. nobody has ever run a SUCCESSFUL quality-gates.sh against that exact
  commit, so fresh-pull's ff-only check won't surface it (ahead-only, non-dirty state reads as nothing-to-do). Main
  agt-1756f6 independently verified 2 of the 4 as real orphans (c927ec58, 06c8e90b — NOT ancestors of
  origin/live-defi-rollout, both meaningful changes despite net-0 line delta); the other 2 (0e62096f, bd0e231f) are
  review-cascade-verified but not in main's orchestrator-host clones so not independently re-checked here. Zero
  data-loss risk — all four are safety-net-preserved on origin/wip-preserve/* refs. Main cannot respawn slots
  (backend-owned) or push code (quickmerge is worker-side), hence worker-rescue todos.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library, unified-api-contracts, deployment-service, market-tick-data-service]
scope: [admin]
tags: [orphan-rescue, per-tab-worktrees, wip-preserve, git-health, worktree-health]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /codex/08-workflows/ci-cd-flow.md]
created: 2026-08-04
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
source:
  "review worktree-health finding msg #3630 (2026-08-04 00:06Z), cascade-verification STILL-ORPHANED verdicts
  00:02:14-18Z; c927ec58 + 06c8e90b independently orphan-verified by main agt-1756f6 via git merge-base --is-ancestor"
drift_direction: advance-process
estimate_class: refactor
depends_on: []
---

# Orphaned worktree WIP (slot-12 x3 + slot-8 bd0e231f) — mechanical worker rescue

## The finding (dead-slot / stranded-WIP, wip-preserved)

Per the per-tab-worktrees LIVENESS-gated inherit rule, a DEAD slot's unpushed WIP is inherit-and-ship. These four are
past that gate (slot 12 killed; slot 8's commit stranded across repeated reclaims) but haven't landed, so they need an
explicit reconcile.

| Repo                     | Commit   | Content                                    | Verified                                      |
| ------------------------ | -------- | ------------------------------------------ | --------------------------------------------- |
| unified-trading-library  | c927ec58 | point_in_time.py (net 0; doc fix)          | **main-verified orphan** (not on LDR)         |
| unified-api-contracts    | 06c8e90b | defi_venues.py (net 0; AAVE-PLASMA → live) | **main-verified orphan** (not on LDR)         |
| deployment-service       | 0e62096f | pyproject.toml + uv.lock (net +1)          | review-cascade-verified (not in main's clone) |
| market-tick-data-service | bd0e231f | (slot-8; see QG-sentinel note)             | review-cascade-verified (not in main's clone) |

All four are safety-net-preserved on `origin/wip-preserve/*` (zero loss). "net 0 delta" ≠ no-op: 06c8e90b flips the
AAVE-PLASMA phase pipeline to live and c927ec58 fixes stale `lst_staking_yields` — both real, worth landing.

## bd0e231f is a different problem than the MTDS qg_red block

Review's earlier assumption (that bd0e231f would clear when MTDS's repo-blocker resolved) did NOT hold: the watchdog
reclaimed/preserved it 6x over ~21min with `no matching .qg_last_passed_sha sentinel` — meaning no SUCCESSFUL
`quality-gates.sh` has ever run against that exact commit (orthogonal to whether the repo is green). Slot 8 was
mid-respawn (fresh-pull) at flag time; **fresh-pull's ff-only check will NOT surface an ahead-only, non-dirty state as
needing action**, so a respawned slot 8 may silently move to a new task and strand bd0e231f indefinitely. Main is
watching slot 8 post-boot (see Progress Log); if it doesn't self-resolve, the todo below covers it.

## Todos

- [ ] [BACKEND] P2. Rescue the 3 orphaned slot-12 commits onto `origin/live-defi-rollout`, one repo at a time. For each
      of (unified-trading-library c927ec58, unified-api-contracts 06c8e90b, deployment-service 0e62096f): `cd <repo>`,
      `git fetch origin 'refs/wip-preserve/*:refs/remotes/origin/wip-preserve/*'`, confirm the slot-12 wip-preserve ref
      resolves to the SHA and is still NOT an ancestor of origin/live-defi-rollout; cherry-pick (or
      format-patch/`git     am`, or re-derive if it conflicts) onto a fresh LDR-tip branch; run repo
      `bash scripts/quality-gates.sh` green; ship via
      `bash scripts/quickmerge.sh "<original commit subject> (rescue orphaned slot-12 WIP)" --agent --files     '<the commit's files>'`.
      Done-when: each SHA's change is an ancestor of origin/live-defi-rollout. (repos: unified-trading-library,
      unified-api-contracts, deployment-service)
- [ ] [BACKEND] P2. Reconcile slot-8's stranded `market-tick-data-service@bd0e231f` — ONLY if main confirms slot 8 did
      not self-resolve it post-boot (see Progress Log). The key difference: bd0e231f has never had a successful QG, so
      it MUST get a fresh `bash scripts/quality-gates.sh` green run against the reconciled commit (that IS the missing
      `.qg_last_passed_sha` sentinel), then quickmerge. Verify it's a real orphan first
      (`git merge-base --is-ancestor     bd0e231f origin/live-defi-rollout` → not-ancestor) before landing. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P3. Rescue slot-4's orphaned `market-data-processing-service` throttle fix `~036c568` (proactive GCS-429
      avoidance) — a small untracked improvement that never landed; only the earlier crash-prevention `db055ba` is on
      origin, so crash risk is already mitigated and this is genuinely low-priority (hence P3). Review agt-8fee2f
      verified it (msg #3648); main could NOT independently re-check (not in main's orchestrator-host clone). Locate the
      commit (wip-preserve ref or slot-4's worktree), confirm it's a real orphan
      (`git merge-base --is-ancestor     036c568 origin/live-defi-rollout` → not-ancestor), reconcile onto LDR tip, QG
      green, quickmerge. Done-when: the 429-avoidance change is an ancestor of origin/live-defi-rollout (or, if it turns
      out already-superseded/landed, close with that note). (repo: market-data-processing-service)

## Progress Log

- **2026-08-04 ~00:08Z (main agt-1756f6)**: Filed from review worktree-health #3630. Independently orphan-verified
  c927ec58 + 06c8e90b (not on LDR); 0e62096f + bd0e231f are review-cascade-verified, not in main's orchestrator-host
  clones so not re-checked here. P2 (non-urgent, all wip-preserved, zero loss). Main did NOT respawn slot 12
  (backend-owned; AutoSpawn should recycle it — if a respawned/inheriting slot lands the WIP first, close this) and did
  NOT push (worker-side quickmerge). **Watch item main owns**: confirm slot 8 resolves bd0e231f's ahead-state after its
  respawn boots rather than stranding it; if it strands, the 2nd todo above covers it.
- **2026-08-04 ~02:35Z (main agt-1756f6)** — added the slot-4 mdps throttle-fix orphan (`~036c568`, P3) from review
  #3648 so it doesn't get dropped from active tracking. Same orphaned-slot-WIP class as the slot-12/slot-8 items;
  review-verified only (not in main's clone). P3 because the crash-risk half (`db055ba`) already landed — this is the
  proactive-429-avoidance refinement, a nice-to-have not a fix.
- **2026-08-04 ~00:11Z (main agt-1756f6)** — **slot-8 watch discharged: it stranded.** Next tick after filing, slot 8
  was again `worker_alive=false` (task=None) having died without landing bd0e231f — so it did NOT self-resolve
  post-boot. Combined with review's structural point (fresh-pull's ff-only check cannot surface an ahead-only, non-dirty
  state), repeated AutoSpawn respawns will keep stranding it, not fix it. **The 2nd todo's gate is therefore SATISFIED**
  — a worker should now reconcile bd0e231f per that todo (fresh successful QG to mint the missing `.qg_last_passed_sha`
  sentinel, then quickmerge). Still zero-loss (wip-preserved).
