---
doc_type: issue
title: >-
  safe-doc-push isolated worktree deleted mid-run by a concurrent cleanup → false "YOUR EDITS ARE NO LONGER ON DISK"
  exit 10 (three runs at once, 2026-08-22 08:19Z)
summary: >-
  At 2026-08-22T08:19:22-27Z three concurrent safe-doc-push runs in slot 6 (pids 64625 / 45558 / 73509; a fourth at
  07:47:56Z) all failed within five seconds with "fatal: Unable to read current working directory" on every git call,
  then exit 10 — the script's content-vanished verdict — listing every named file as ABSENT and telling the caller to
  recover content from a stash. Nothing had vanished — the caller's files were still on disk with byte-identical hashes
  to the entry fingerprint (6e586919fe / 65dbe6060c / 5dd3f0d8fd re-verified minutes later, no stash entry held them).
  The script's isolated worktree under ${TMPDIR:-/tmp}/sdp-iso-$$ (the per-user macOS temp root) was deleted out from
  under it mid-run, and the fingerprint check runs relative to that now-missing cwd, so every path reads ABSENT. Proven
  workaround — TMPDIR pointed at an unswept directory — landed the same files on the next attempt (9663fa9cf5,
  76ed5a242f). Recurrence risk is every session in a contended slot; the false verdict is worse than a plain failure
  because it sends the operator digging through 97 stash entries for content that never moved.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, isolated-worktree, multi-agent, slot-contention, tmpdir, false-positive, git-discipline]
related:
  [
    /plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
    /plans/archive/2026_08/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md,
    /plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    unified-trading-pm/scripts/dev/safe-doc-push.sh,
    unified-trading-pm/scripts/dev/test-safe-doc-push-concurrency.sh,
    /plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
    /plans/archive/2026_08/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md,
    /plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
source: [interactive session 2026-08-22 slot 6 — shipping trading_pipeline_smoke_and_shard_telemetry_2026_08_22]
---

# safe-doc-push isolated worktree deleted mid-run → false content-vanished verdict (exit 10)

## Evidence (all measured, 2026-08-22)

- Forensic snapshots in `~/.cache/sdp-forensics/`: `revert-20260822T081922Z-64625.log`, `revert-20260822T081924Z-45558.log`,
  `revert-20260822T081927Z-73509.log` (three distinct runs, five seconds apart) and `revert-20260822T074756Z-11550.log`.
- Each log's "current disk fingerprint" section reads `ABSENT` for every named file and every subsequent git call prints
  `fatal: Unable to read current working directory: No such file or directory` — the cwd
  (`$TMPDIR/sdp-iso-<pid>/.tabs/6/unified-trading-pm`) no longer existed.
- Re-checked by absolute path minutes later: all three files present, `git hash-object` equal to the entry fingerprint;
  `git stash list` top entries contained none of them. The "recover from a stash" instruction was wrong for this case.
- Slot state at the time: 10 concurrent `safe-doc-push` / `run_hygiene_sweep` processes, 97 stash entries, four stale
  `sdp-iso-*` worktrees listed by `git worktree list` (peers' earlier runs).
- Workaround that worked: `TMPDIR=$HOME/.cache/sdp-work-slot6 bash scripts/dev/safe-doc-push.sh …` — both subsequent
  pushes landed (`unified-trading-pm@9663fa9cf5`, `@76ed5a242f`).

## Root cause (mechanism proven; deleter not yet named)

The isolated worktree parent is `${TMPDIR:-/tmp}/sdp-iso-$$` (`scripts/dev/safe-doc-push.sh`, `_sdp_iso_parent`). On
macOS that is the per-user `/var/folders/…/T` root, which slot-wide cleanup tooling and peers' own worktree cleanup
touch. Something removed several `sdp-iso-*` directories simultaneously at 08:19:2xZ. The script's
`_sdp_warn_if_content_vanished` fingerprint then runs from the deleted cwd, so relative paths resolve to nothing and the
verdict collapses to "every file ABSENT" → exit 10, whose message asserts the caller's content changed.

- [ ] [INFRA] P1. **Name the deleter** — correlate the four forensic timestamps with `scripts/dev/cleanup-stale-*.sh`
      runs, launchd/cron entries, and peer `safe-doc-push` cleanup (`git worktree remove --force` / `prune` in the
      script's own trap). Done-when: the deleting command + trigger is cited with a log line, not inferred.
- [ ] [INFRA] P1. **Fingerprint from the caller's absolute repo root, never from the isolated cwd** — capture
      `git rev-parse --show-toplevel` at entry and run `_sdp_warn_if_content_vanished` against it; if the isolated
      worktree itself vanished, emit a distinct verdict/exit code ("isolation dir removed mid-run — retry") instead of
      exit 10. Done-when: `scripts/dev/test-safe-doc-push-concurrency.sh` gains a case that deletes the iso dir
      mid-run and asserts the new verdict; `check_strict_quickmerge` + prek green.
- [ ] [INFRA] P1. **Default the isolation parent to an unswept location** (e.g. `${XDG_CACHE_HOME:-$HOME/.cache}/sdp-iso/`),
      keeping `TMPDIR` as an explicit override, and prune only this script's OWN worktree in its trap. Done-when:
      shipped + one contended-slot run lands without the override.
- [ ] [DOC] P2. **Codex**: `/codex/05-infrastructure/per-tab-worktrees.md` ship-script section documents exit 10's two
      causes (genuine content change vs isolation dir removed) and the TMPDIR workaround. Done-when: doc merged.

## Progress Log

- **2026-08-22 (interactive session, slot 6)**: Filed from a live occurrence while shipping
  `trading_pipeline_smoke_and_shard_telemetry_2026_08_22`; content verified intact by hash; workaround proven on the next
  two pushes.
