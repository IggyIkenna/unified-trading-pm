---
doc_type: issue
title:
  "ao-self-pull.sh silently stalled for 2+ hours on the orchestrator VM -- 2 untracked accounts.json backup files were
  never gitignored"
summary:
  "Credential/self-service re-triage pass (2026-07-29) found the agent-orchestrator repo's own dispatch-sequential-gate
  verification needed live SSM access to i-0c9b283b31d6b5ca7 (the orchestrator VM) -- while there, found ao-self-pull.sh
  (the */15 cron that keeps the VM's checkout current with origin/live-defi-rollout) had been logging 'is dirty
  (non-churn) -- skip (manual review)' on EVERY tick since at least 17:00 UTC that day (2+ hours, likely longer). Root
  cause: 2 untracked backup files -- data/config/accounts.json.bak-pre-sub-e-2026-07-28 and ...-f-2026-07-28
  (2055B/2537B, dated 2026-07-28, clearly deliberate pre-substitution safety backups of the gitignored accounts.json
  SSOT, not accidental litter) -- were never added to .gitignore, so the dirty-tree check never cleared. This meant the
  VM's deployed code could silently fall behind origin for however long the tree stayed dirty, with no alert
  (self-pull's skip is a silent no-op by design, not a paged failure)."
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, self-pull, git-health, gitignore, silent-stall, observability-gap]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/ao_residuals_after_dispatch_hardening_2026_07_17.md,
  ]
created: 2026-07-29
priority: P2
parent_epic: agent_operating_framework_master
source: "Found while live-verifying dispatch_sequential_gate_fix_2026_07_24.md's [BACKEND] P1 todo via SSM, 2026-07-29"
resolved_by: agent-orchestrator@b5fb9fc, agent-orchestrator@61b7a4f
locked_by:
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# ao-self-pull.sh silently stalled 2+ hours -- 2 untracked backup files never gitignored

> **🟢 ARCHIVED 2026-07-30** — status=resolved, 0 open todos. The original incident was fixed same-session
> (`agent-orchestrator@b5fb9fc` gitignore fix, live-verified VM HEAD match 2026-07-29); the follow-up staleness-alert
> todo (a `/plan-reconcile` sweep had earlier flagged this doc's `status: resolved` as premature while it was still
> open) is now also shipped (`agent-orchestrator@61b7a4f` — TIME-gated dirty-skip alert, functionally verified).
> Archived per `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule (ACKED-INTO-CODE).

## Evidence

`/var/log/ao-self-pull.log` on `i-0c9b283b31d6b5ca7`, every `*/15 * * * *` tick from at least 17:00:01Z through
19:30:01Z 2026-07-29 (10 consecutive ticks, 2.5h):

```
ao-self-pull: /home/ubuntu/unified-trading-system-repos/agent-orchestrator is dirty (non-churn) — skip (manual review)
```

`git status --porcelain` on that checkout showed exactly 2 untracked files:

```
?? data/config/accounts.json.bak-pre-sub-e-2026-07-28
?? data/config/accounts.json.bak-pre-sub-f-2026-07-28
```

`.gitignore` already covers `data/config/accounts.json` (the SSOT it's a backup of) but had no pattern matching the
`.bak-pre-sub-*` naming — these 2 files were untracked-but-not-ignored, so `git status --porcelain` never came back
clean, and the self-pull dirty-gate (a deliberate safety check — never auto-pull over uncommitted local state) never
cleared.

## Why this wasn't caught sooner

Self-pull's skip is a silent no-op by design (matches this same repo's own prior finding in
`ao_residuals_after_dispatch_hardening_2026_07_17.md` about a 2026-07-12 dirty-gate wedge) — it protects against
clobbering real WIP, but has no alerting for "stuck clean-but-actually-dirty for hours." Nobody was actively watching
this specific VM's self-pull log; it surfaced only because an unrelated todo needed live SSM access to the same host.

## Fix (shipped same session)

- `agent-orchestrator@b5fb9fc` — added `data/config/accounts.json.bak-pre-sub-*` to `.gitignore`, same
  secrets-adjacent-class reasoning as the tracked exclusion it backs up.
- Verified live: VM HEAD now matches the pushed commit exactly (`b5fb9fcaff438f7fc2990678ce1d7edca80da81c`),
  `git status --porcelain` is empty, self-pull's next tick will succeed normally. The 2 backup files were left in place
  untouched (not deleted) — they look like a deliberate safety measure from a real account-substitution operation, not
  litter; gitignoring them (rather than removing them) preserves that safety net while unblocking the pull.

## Todos

- [x] ✅ [INFRA] P3. **Consider adding a self-pull staleness alert** — e.g. if `ao-self-pull.sh` logs "dirty (non-churn)
      — skip" N consecutive times (say, 4 = 1 hour), page or Slack-notify rather than silently repeating forever. This
      exact failure mode (silent multi-hour staleness, only caught by chance) is worth closing structurally, not just
      patching this one instance. Cross-reference the existing dirty-gate design in
      `ao_residuals_after_dispatch_hardening_2026_07_17.md` before building — don't duplicate. — **BUILT 2026-07-30**:
      cross-referenced `ao_residuals_after_dispatch_hardening_2026_07_17.md` first — its dirty-gate content is a
      DIFFERENT, already-fixed 2026-07-12 wedge (a `tempfile.gettempdir()` root cause) plus a UI-half staleness alert
      owned by another agent; no overlap with this ask. Confirmed the existing `_alert_wedge` (fires on every dirty-skip
      tick) is COMMIT-COUNT gated (`AO_DRIFT_ALERT_COMMITS`, default 10) — during a quiet LDR window a dirty tree can
      sit skipped for hours without ever crossing that threshold, exactly this incident's blind spot (time-stuck ≠
      commit-distance-stuck). Added a genuinely new, TIME-gated condition mirroring the file's own existing
      `_track_stale_process`/`_STALE_TICKS_STATE` pattern: `_track_dirty_tick()` + `_DIRTY_TICKS_STATE`
      (`agent-orchestrator/scripts/ao-self-pull.sh`) increments a tick counter on every dirty-skip and fires the
      existing `_post_wedge_slack_alert` dedup path once `AO_DIRTY_ALERT_TICKS` (default 4 = ~1h at the `*/15` cadence,
      matching this todo's own "say, 4 = 1 hour" spec) consecutive dirty ticks are hit; the counter resets to zero the
      moment the tree goes clean. Functionally verified end-to-end against a real scratch git repo (not just read): 4
      consecutive dirty runs correctly climb the tick file 1→2→3→4 and the WEDGE alert fires exactly at tick 4 (not
      before); a subsequent clean run removes the tick file. `shellcheck` clean (both pre-existing warnings on unrelated
      lines, none introduced), `bash -n` syntax-clean. — agent-orchestrator@61b7a4f.

## Progress Log

- 2026-07-29: Found + root-caused + fixed in one session (credential/self-service re-triage pass). Live-verified the fix
  landed and unstuck the VM. Filed the alerting-gap follow-up as its own low-priority todo rather than fixing it in the
  same pass (a genuinely separate, larger piece of work — an alerting mechanism, not a one-line gitignore fix).
- **na-eligibility-audit 2026-07-30**: RECLASSIFY → planning, conflict-cleared — the original incident is already fixed;
  the one open `[INFRA] P3` is a bounded, self-contained addition to `ao-self-pull.sh`: count consecutive
  `dirty (non-churn) — skip` ticks and page/Slack-notify at N (the doc names N=4 ≈ 1 hour). Determinable by the worker
  alone, no operator gate, no design fork; the alerting contract is already SSOT'd in
  `/codex/04-architecture/agent-orchestrator-alerting.md` (state-transition dedup, not every tick). **Phase-2
  conflict-check**: the only `ao-self-pull` hit on the active planning surface is
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s todo 6, which merely READS which ref the script tracks (explicitly
  'READ-ONLY') as part of the sequential-gate verification — no competing change to the script. CLEAR. Set
  `assigned_role: infra`, `execution_scope: orchestrator-agent`. The todo's own instruction to cross-reference
  `ao_residuals_after_dispatch_hardening_2026_07_17.md`'s dirty-gate design before building stands.
- **⚠️ SUPERSEDED — integrator note 2026-07-30.** The RECLASSIFY above was computed against this doc's ACTIVE state;
  while the ao tranche was running, the doc was **resolved and archived** here by `unified-trading-pm@24fda8bfb`. Git
  rename detection silently replayed the tranche's frontmatter flip onto this archived copy, leaving a
  `status: resolved` doc marked `assigned_vm: planning`; the integrator **reverted the flip to `assigned_vm: NA` /
  `execution_scope: local-only`** to match the archived state. The verdict text is kept as an audit record only — it
  does not describe open work.
