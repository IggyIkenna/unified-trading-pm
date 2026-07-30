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
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, self-pull, git-health, gitignore, silent-stall, observability-gap]
related:
  [
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/ao_residuals_after_dispatch_hardening_2026_07_17.md,
  ]
created: 2026-07-29
priority: P2
parent_epic: agent_operating_framework_master
source: "Found while live-verifying dispatch_sequential_gate_fix_2026_07_24.md's [BACKEND] P1 todo via SSM, 2026-07-29"
resolved_by:
locked_by:
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# ao-self-pull.sh silently stalled 2+ hours -- 2 untracked backup files never gitignored

> **🟡 STATUS CORRECTED 2026-07-30** (`/plan-reconcile` autonomous sweep) — frontmatter said `status: resolved` while
> the doc still carries an OPEN `- [ ]` [INFRA] P3 todo (the self-pull staleness alert), so
> `check_terminal_status_archived` demanded an archive the doc is not actually ready for. Aligned frontmatter to reality
> per the skill's "frontmatter status contradicting body completion" auto-fix class: `status: resolved` → `open`,
> `resolved_by:` cleared. **The original incident IS fixed** — see § "Fix (shipped same session)" below (gitignore
> change + live-verified VM HEAD match on 2026-07-29); what remains open is only the follow-up alerting gap. Re-flip to
> `resolved` and archive once that todo closes.

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

- `agent-orchestrator@<gitignore-fix-sha>` — added `data/config/accounts.json.bak-pre-sub-*` to `.gitignore`, same
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
