#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# cron-self-pull-lib.sh — shared emitter for the syntax-gated cron self-pull snippet.
#
# SOURCED by cron installers so the self-pull pattern is DRY in source, even though each
# emitted crontab line stays fully self-contained (the crontab line is the immutable anchor —
# it pulls its OWN script from LDR before running, so a stale/dirty PM clone never starves the
# cron of current code). SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller".
#
#   emit_cron_self_pull <pm_dir> <branch> <script_relpath> [data_relpath ...]
#
# Echoes a single-line shell snippet that, BEFORE the cron's real command runs:
#   - cd <pm_dir>; fetch origin/<branch>
#   - CMP-GUARD (2026-07-14): every write below happens ONLY when the working copy differs from
#     the origin/<branch> content. An unconditional every-tick overwrite left the file dirty-vs-HEAD
#     whenever the clone was behind, which made slot-cron-ff-pull's own [skip:dirty] check starve
#     the clone of the FF that would have healed it (root-PM incident 2026-07-14: 1138 commits
#     behind forever). ff_one() carries the matching heal (restore-to-HEAD when byte-identical to
#     origin) for hosts still running an older unguarded crontab line.
#   - SYNTAX-GATE the <script_relpath> (H6): stream the candidate via `git show` to a temp,
#     `bash -n` it, and only `mv` + `chmod 755` into place if it parses — so one bad commit can
#     never propagate fleet-wide and stop the cron in <=5 min; on any failure keep the last-good
#     local copy. (chmod 755 AFTER mv: mktemp is 0600, so without it the script lands non-exec
#     AND mode-dirty vs HEAD -> the FF-pull/status crons then see the clone dirty + SKIP it.)
#   - each <data_relpath> (DATA, not a script -> no bash -n needed): cmp-guarded `git show` to a
#     temp + `mv` into the real path (so a BASH_SOURCE-relative sibling still resolves) + chmod 644.
#     NOT `git checkout origin/<branch> -- <file>` — that also writes the INDEX, leaving a STAGED
#     diff on a behind clone (worse than the unstaged script artifact, same starvation).
#   - `|| true` so an offline tick falls back to the last-good local copy, never skips a tick
#     (offline `git show` emits nothing -> cmp differs -> the write attempt fails -> temp removed).
#
# Literal `$(mktemp)` / `$t` / `$u` are kept LITERAL in the emitted line (single-quoted printf
# format / escaped in the data snippet) — cron writes them verbatim and /bin/sh expands at run time.
emit_cron_self_pull() {
    local pm_dir="$1" branch="$2" script="$3"; shift 3
    local data_checkouts="" d
    for d in "$@"; do
        data_checkouts+=" git show origin/${branch}:${d} 2>/dev/null | cmp -s - ${d} 2>/dev/null || { u=\$(mktemp); git show origin/${branch}:${d} > \"\$u\" 2>/dev/null && mv \"\$u\" ${d} && chmod 644 ${d} || rm -f \"\$u\"; };"
    done
    printf 'cd "%s" && { git fetch -q origin %s 2>/dev/null; if ! git show origin/%s:%s 2>/dev/null | cmp -s - %s 2>/dev/null; then t=$(mktemp); if git show origin/%s:%s > "$t" 2>/dev/null && bash -n "$t" 2>/dev/null; then mv "$t" %s && chmod 755 %s; else rm -f "$t"; fi; fi;%s } || true' \
        "${pm_dir}" "${branch}" "${branch}" "${script}" "${script}" "${branch}" "${script}" "${script}" "${script}" "${data_checkouts}"
}
