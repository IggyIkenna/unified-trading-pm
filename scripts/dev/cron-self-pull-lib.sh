#!/usr/bin/env bash
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
#   - SYNTAX-GATE the <script_relpath> (H6): stream the candidate via `git show` to a temp,
#     `bash -n` it, and only `mv` + `chmod 755` into place if it parses — so one bad commit can
#     never propagate fleet-wide and stop the cron in <=5 min; on any failure keep the last-good
#     local copy. (chmod 755 AFTER mv: mktemp is 0600, so without it the script lands non-exec
#     AND mode-dirty vs HEAD -> the FF-pull/status crons then see the clone dirty + SKIP it.)
#   - direct-checkout each <data_relpath> (DATA, not a script -> no bash -n needed; lands at the
#     real path so a BASH_SOURCE-relative sibling still resolves).
#   - `|| true` so an offline tick falls back to the last-good local copy, never skips a tick.
#
# Literal `$(mktemp)` / `$t` are kept LITERAL in the emitted line (single-quoted printf format) —
# cron writes them verbatim and /bin/sh expands them at run time.
emit_cron_self_pull() {
    local pm_dir="$1" branch="$2" script="$3"; shift 3
    local data_checkouts="" d
    for d in "$@"; do
        data_checkouts+=" git checkout -q origin/${branch} -- ${d} 2>/dev/null;"
    done
    printf 'cd "%s" && { git fetch -q origin %s 2>/dev/null; t=$(mktemp); if git show origin/%s:%s > "$t" 2>/dev/null && bash -n "$t" 2>/dev/null; then mv "$t" %s && chmod 755 %s; else rm -f "$t"; fi;%s } || true' \
        "${pm_dir}" "${branch}" "${branch}" "${script}" "${script}" "${script}" "${data_checkouts}"
}
