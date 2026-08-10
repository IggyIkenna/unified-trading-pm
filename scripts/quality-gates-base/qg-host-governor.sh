#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# qg-host-governor.sh — host-level concurrency governor for quality-gates.sh.
#
# Plan: plans/active/quality_gates_resource_contention_speedup_2026_06_02.md (todo: qg-governor)
#
# WHY (the core fix)
#   The dev host runs 8 slots × 2 operator sides of parallel agents. When several slots'
#   quality-gates.sh hit the heavy phases (pytest/basedpyright) AT ONCE the box oversubscribes:
#   CPU steal climbs, it swaps, EVERY concurrent run slows. Measured ceilings that make this
#   acute: unified-trading-library peaks at 5.27 GB and execution/features at ~1.9 GB per run.
#   This governor caps how many QG runs may be in their heavy phase concurrently across ALL
#   slots — converting an N-way thrash into orderly queueing. No added parallelism; p95 drops.
#
# MECHANISM
#   Token bucket of K tokens implemented as K flock(1) lockfiles in a host-shared dir. A run
#   acquires one token (blocking until one frees), holds it for the heavy phase, releases it.
#   K defaults to max(2, floor(physical_cores / 4)) — overridable via QG_HOST_CONCURRENCY.
#   The acquiring process tree is de-prioritised (nice + ionice) so a held QG never starves
#   interactive work.
#
# USAGE
#   A) Sourced (from base-service.sh, around the heavy phases):
#        source "<this file>"
#        qg_governor_acquire        # blocks until a host token is free; holds it
#        ... pytest / basedpyright ...
#        qg_governor_release        # frees the token (also auto-freed on process exit)
#
#      qg_governor_acquire also sets QG_GOVERNOR_WAIT_SECONDS (0 if never throttled)
#      — the caller's MAX_DURATION wall-clock check subtracts this from billable
#      duration, so queueing behind the shared token cannot fail an otherwise-green
#      run purely for having queued (qg_host_governor_severe_contention_2026_07_13.md).
#
#   A2) TOTAL-INSTANCE gate (from base-service.sh, wraps the WHOLE run):
#        qg_governor_acquire_total_instance   # once, right after sourcing this file
#        ... BOOTSTRAP / LINT / CODEX COMPLIANCE / TESTS / TYPECHECK ...
#        qg_governor_release_total_instance   # from the caller's EXIT trap
#
#      Closes the scope gap named in
#      plans/active/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md
#      (2026-08-09): (A) only brackets TESTS+TYPECHECK — everything else (dependency
#      bootstrap, lint/autofix, the large CODEX COMPLIANCE phase) previously ran with
#      NO concurrency bound at all, so a host could carry far more live
#      quality-gates.sh processes than the heavy-phase K ever capped (12-19 observed
#      against a live K<=6). This gate bounds TOTAL concurrent script instances
#      host-wide, nesting around (A) rather than replacing it.
#
#   B) Wrapper CLI (wrap any command under one token):
#        bash qg-host-governor.sh -- <command> [args...]
#
#   C) Introspection:
#        bash qg-host-governor.sh --status   # K, dir, currently-held tokens (both gates)
#
# ENV
#   QG_HOST_CONCURRENCY   override K (max concurrent heavy QG phases host-wide)
#   QG_GOVERNOR_DIR       token dir (default ${TMPDIR:-/tmp}/qg-host-governor)
#   QG_GOVERNOR_DISABLE   set to "true" to make acquire/release no-ops (CI / single-run)
#   QG_GOVERNOR_NICE      nice increment applied to the QG tree (default 10)
#   QG_TOTAL_INSTANCE_CAP override the total-instance gate's cap (default: physical
#                         cores, floored at 4)
#   QG_TOTAL_GOVERNOR_DIR total-instance token dir (default: host-shared dir, same
#                         placement rule as the RAM ledger — see _qg_shared_root)
#   QG_TOTAL_GOVERNOR_DISABLE  set to "true" to make the total-instance gate a no-op
#   QG_HOST_SHARED_LEDGER_ROOT  override the ONE shared root both interactive slots
#                         (.tabs) AND glue-runner CI (/opt/github-glue-runners*)
#                         collapse to for ledger placement (default
#                         ${HOME:-/home/ubuntu}/unified-trading-system-repos — NOT
#                         /opt, which is outside every interactive slot's sandboxed
#                         ReadWritePaths) — see _qg_shared_root
#   QG_HOST_RAM_ABORT_PCT       runtime-abort-monitor trip point, host-used % (default 80)
#   QG_WATCHDOG_INTERVAL_SECONDS  poll interval for the runtime abort-monitor (default 15)
#   QG_WATCHDOG_CONSECUTIVE_HITS  consecutive over-threshold samples before abort (default 2)
#   QG_GOVERNOR_WATCHDOG_DISABLE  set to "true" to disable the runtime abort-monitor (reservation mode only)
#
# Safe to source repeatedly; functions are idempotent. No effect on correctness — purely
# a scheduling throttle, so a missing flock(1) degrades gracefully to "no governor".

# ── default K = max(2, floor(physical_cores / 4)) ────────────────────────────
# Floor RAISED 1 → 2 (operator 2026-06-05): the host must be able to run 2 full QGs
# at once, not just 1. RAM-safe by the documented sizing rule (per-VM RAM ≥ peak-RSS
# × K): the UTL ceiling 5.27 GB × 2 = ~10.6 GB still fits a 16 GB worker; service
# repos (~1.9 GB) are trivial. On the macOS operator host lscpu+nproc are both absent
# → cores degrades to 4 → floor(4/4)=1 → the min-2 floor lifts it to exactly 2 (the
# desired Mac cap); bigger boxes keep their higher floor(cores/4) (24-core → 6).
_qg_governor_default_k() {
    local cores
    # physical cores if lscpu is available, else logical (nproc), else 4
    cores="$(lscpu -p=core 2>/dev/null | grep -vc '^#')"
    [[ "${cores:-0}" -ge 1 ]] || cores="$(nproc 2>/dev/null || echo 4)"
    local k=$(( cores / 4 ))
    (( k >= 2 )) || k=2
    echo "$k"
}

_qg_governor_k() { echo "${QG_HOST_CONCURRENCY:-$(_qg_governor_default_k)}"; }
_qg_governor_dir() { echo "${QG_GOVERNOR_DIR:-${TMPDIR:-/tmp}/qg-host-governor}"; }

# ── TOTAL-INSTANCE gate — bounds ALL concurrent quality-gates.sh PROCESSES, not just
# the heavy TESTS+TYPECHECK phase K above governs (scope gap named in
# plans/active/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md,
# 2026-08-09: BOOTSTRAP/AUTO-FIX/LINT and the large CODEX-COMPLIANCE phase run fully
# UNGATED, so a host can carry many more live script instances than the heavy-phase K
# ever caps — 12-19 observed against a live K<=6). Default cap = physical cores (a
# looser bound than the heavy-phase K, since most of a run's wall-clock is lighter than
# pytest/basedpyright), floored at 6 (operator ruling 2026-08-09, matching the measured
# safe cross-repo ceiling on the shared dev host — was 4; raised alongside the new
# per-repo sub-cap below, since the two now compose instead of one flat number doing
# both jobs). Overridable via QG_TOTAL_INSTANCE_CAP; separate lock dir from the
# heavy-phase token dir above so the two gates never collide.
_qg_total_default_cap() {
    local cores; cores="$(_qg_physical_cores)"
    local k="$cores"
    (( k >= 6 )) || k=6
    echo "$k"
}
_qg_total_k() { echo "${QG_TOTAL_INSTANCE_CAP:-$(_qg_total_default_cap)}"; }
_qg_total_dir() { echo "${QG_TOTAL_GOVERNOR_DIR:-$(_qg_shared_root)/.benchmarks/qg-governor-total}"; }

# ── PER-REPO sub-cap (operator ruling 2026-08-09) ────────────────────────────────
# WHY: the flat total-instance cap above answers "how many quality-gates.sh processes
# host-wide" but not "how many are the SAME repo" — measured live 2026-08-09: ~24
# concurrent AO-dispatched slots all committing/QG-running on unified-trading-pm at
# once produced sustained git-index-lock contention and branch-drift-retry storms this
# gate alone cannot see (it only counts PROCESSES, not which repo they belong to). PM
# specifically both tolerates and needs more headroom than a single service repo (its
# own commit velocity is the fleet's shared bottleneck), so it gets a higher sub-cap;
# every other (service) repo gets 1 — never two concurrent QG runs on the SAME service
# repo on one host, since those virtually always collide on the SAME git ref. The two
# caps COMPOSE (both must have room) rather than replace each other: the per-repo cap
# stops one repo from monopolising the flat cap; the flat cap stops the WHOLE host from
# oversubscribing even if every repo's own sub-cap would individually allow it.
_qg_repo_name() {
    # SLOT-AGNOSTIC BY DESIGN (2026-08-09, second incident same day — see
    # plans/active/issues/qg_governor_repo_bucketing_falls_back_to_slot_number_2026_08_09.md).
    # The first fix here only reordered PRECEDENCE (`PROJECT_ROOT:-REPO_ROOT` instead of
    # the reverse) — it still depended on PROJECT_ROOT being POPULATED by the time this
    # function runs, and a bare `bash scripts/quality-gates.sh --no-fix` invocation
    # reproduced the identical slot-number bucketing the SAME day with PROJECT_ROOT
    # apparently still empty at this call site (exact sourcing-order gap not fully
    # traced — see the issue doc's Root Cause section). Querying git directly sidesteps
    # the entire "which caller-populated env var, set in what order" class of bug — no
    # env var needs to be populated at all, so this is immune to call-time ordering:
    #   1. `git remote get-url origin`, basename minus the `.git` suffix — the repo's
    #      actual GitHub identity. Correct from the main per-slot clone AND from a
    #      nested worktree (.claude/worktrees/<branch>/) of the SAME repo, since a git
    #      worktree shares its parent repo's remotes — `git rev-parse --show-toplevel`
    #      would instead return the worktree's OWN directory (e.g. a branch/session hash),
    #      wrongly treating it as a different "repo" than its own main clone (verified
    #      live against a real worktree checkout while fixing this).
    #   2. `git rev-parse --show-toplevel`, basename — falls back here only if there is no
    #      `origin` remote (rare/test fixtures); still immune to slot number and worktree
    #      nesting since it reads the actual working-tree root, not a caller-supplied path.
    #   3. PROJECT_ROOT / REPO_ROOT / pwd, basename — final fallback only if git itself is
    #      unavailable or this isn't a git working tree at all (matches this file's
    #      existing graceful-degradation posture — a governor failure must never block
    #      the run it's meant to be scheduling).
    local url root
    url="$(git remote get-url origin 2>/dev/null)"
    if [[ -n "$url" ]]; then
        basename "$url" .git
        return 0
    fi
    root="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [[ -n "$root" ]]; then
        basename "$root"
        return 0
    fi
    root="${PROJECT_ROOT:-${REPO_ROOT:-}}"
    [[ -n "$root" ]] && basename "$root" || echo "unknown"
}
_qg_repo_instance_default_cap() {
    [[ "$(_qg_repo_name)" == "unified-trading-pm" ]] && echo 4 || echo 1
}
_qg_repo_instance_k() { echo "${QG_REPO_INSTANCE_CAP:-$(_qg_repo_instance_default_cap)}"; }
_qg_repo_instance_dir() { echo "$(_qg_total_dir)/repo/$(_qg_repo_name)"; }

# ── HOST CAPACITY INTROSPECTION (Phase 2) ────────────────────────────────────
# Reads the host's real capacity so the (Phase-3) admission gates can size
# themselves per host instead of a fixed K. Portable + bash 3.2-safe: Linux via
# /proc + lscpu, macOS via sysctl + vm_stat. ADDITIVE — nothing here is wired
# into acquire/release yet; `--probe` just prints capacity + derived budgets.
# SSOT: plans/active/qg_host_adaptive_resource_governor_2026_07_14.md
_qg_is_macos() { [[ "$(uname -s 2>/dev/null)" == "Darwin" ]]; }

# Total physical RAM, in KB. QG_MEMINFO_PATH overrides the source for tests.
_qg_mem_total_kb() {
    [[ -n "${QG_FORCE_MEM_TOTAL_KB:-}" ]] && { echo "$QG_FORCE_MEM_TOTAL_KB"; return; } # test / cross-host sim
    if _qg_is_macos; then
        local b; b="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
        echo $(( b / 1024 ))
    else
        awk '/^MemTotal:/{print $2; exit}' "${QG_MEMINFO_PATH:-/proc/meminfo}" 2>/dev/null || echo 0
    fi
}

# Reclaimable-inclusive available RAM, in KB. Linux exposes MemAvailable directly;
# macOS has no equivalent, so approximate with the pages the kernel can hand out
# without swapping — free + inactive + purgeable + file-backed — times page size.
_qg_mem_available_kb() {
    [[ -n "${QG_FORCE_MEM_AVAIL_KB:-}" ]] && { echo "$QG_FORCE_MEM_AVAIL_KB"; return; } # test / cross-host sim
    if _qg_is_macos; then
        local ps vms free inact purge filed pages
        ps="$(sysctl -n hw.pagesize 2>/dev/null || echo 4096)"
        vms="$(vm_stat 2>/dev/null)"
        free="$(printf '%s\n' "$vms" | awk '/^Pages free/{gsub(/\./,"",$NF);print $NF;exit}')"
        inact="$(printf '%s\n' "$vms" | awk '/^Pages inactive/{gsub(/\./,"",$NF);print $NF;exit}')"
        purge="$(printf '%s\n' "$vms" | awk '/^Pages purgeable/{gsub(/\./,"",$NF);print $NF;exit}')"
        filed="$(printf '%s\n' "$vms" | awk '/^File-backed pages/{gsub(/\./,"",$NF);print $NF;exit}')"
        pages=$(( ${free:-0} + ${inact:-0} + ${purge:-0} + ${filed:-0} ))
        echo $(( pages * ps / 1024 ))
    else
        awk '/^MemAvailable:/{print $2; exit}' "${QG_MEMINFO_PATH:-/proc/meminfo}" 2>/dev/null || echo 0
    fi
}

# Physical core count (not logical/HT).
_qg_physical_cores() {
    [[ -n "${QG_FORCE_CORES:-}" ]] && { echo "$QG_FORCE_CORES"; return; } # test / cross-host sim
    local c=0
    if _qg_is_macos; then
        c="$(sysctl -n hw.physicalcpu 2>/dev/null || echo 0)"
    else
        c="$(lscpu -p=core 2>/dev/null | grep -v '^#' | sort -u | grep -c '')"
        [[ "${c:-0}" -ge 1 ]] || c="$(nproc 2>/dev/null || echo 4)"
    fi
    [[ "${c:-0}" -ge 1 ]] || c=4
    echo "$c"
}

# One-line capacity + derived budgets. Fractions are expressed as the documented
# env vars (QG_MEM_SAFETY_FRAC=0.70, QG_CPU_FRAC=0.80) and converted to integer
# percents via awk (bash has no float). Emits GB (integer, floor) for humans.
qg_host_capacity() {
    local frac cpufrac frac_pct cpu_pct mt ma cores ram_budget_kb cpu_slots
    frac="${QG_MEM_SAFETY_FRAC:-0.70}"; cpufrac="${QG_CPU_FRAC:-0.80}"
    frac_pct="$(awk -v f="$frac" 'BEGIN{printf "%d", f*100}')"
    cpu_pct="$(awk -v f="$cpufrac" 'BEGIN{printf "%d", f*100}')"
    mt="$(_qg_mem_total_kb)"; ma="$(_qg_mem_available_kb)"; cores="$(_qg_physical_cores)"
    ram_budget_kb=$(( mt * frac_pct / 100 ))
    cpu_slots=$(( cores * cpu_pct / 100 )); (( cpu_slots >= 1 )) || cpu_slots=1
    printf 'mem_total_gb=%s mem_available_gb=%s cores=%s ram_budget_gb=%s cpu_slots=%s\n' \
        "$(( mt / 1024 / 1024 ))" "$(( ma / 1024 / 1024 ))" "$cores" \
        "$(( ram_budget_kb / 1024 / 1024 ))" "$cpu_slots"
}

# ── RESERVATION LEDGER (Phase 3 — additive; NOT yet wired into acquire/release) ─
# A host-shared, flock-protected record of in-flight QG heavy-phase reservations
# so the upcoming dual-gate admission can bound the SUM of concurrent peak-RSS
# (the 6×UTL stacking case) instead of a fixed count. One row per reservation:
#     <pid> <repo> <rss_mb> <ts>
# SSOT: plans/active/qg_host_adaptive_resource_governor_2026_07_14.md
#
# ONE SHARED ROOT FOR EVERY CALLER TOPOLOGY (fixed 2026-08-10,
# ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md todo 2 — closes the gap todo 1
# on that doc found: interactive slots and glue-runner CI resolved to two genuinely
# DISJOINT directories, so admission control on one side had zero visibility into
# concurrent load from the other, even though both run on the identical shared VM and
# both correctly call qg_governor_acquire() in reservation mode). Previously:
#   - interactive slots (WORKSPACE_ROOT matching `*/.tabs/<N>`) stripped to the
#     per-HOST root (e.g. /home/ubuntu/unified-trading-system-repos) — correct
#     cross-SLOT coordination, but a path private to this topology.
#   - glue-runner CI (WORKSPACE_ROOT matching `/opt/github-glue-runners[-<repo>]/...`,
#     one POOL_TAG-suffixed dir per repo) collapsed to /opt/.qg-governor-glue-shared —
#     correct cross-REPO coordination (plans/archive/2026_08/
#     qg_governor_glue_runner_ledger_coordination_2026_08_03.md), but a path private
#     to THIS topology, never the same as the interactive-slot one above even on the
#     SAME host (live-verified 2026-08-10: same filesystem device id, different
#     inodes — not a symlink, genuinely two ledgers).
# Fix: BOTH topologies now collapse to the identical shared root, so a `--status` run
# from either surface reads the other's live reservations.
#
# WHY THE SHARED ROOT IS /home/ubuntu/unified-trading-system-repos, NOT
# /opt/.qg-governor-glue-shared (rejected during this same 2026-08-10 fix, do not
# revert to it without re-reading this): every interactive agent-orchestrator worker
# process is a descendant of the `orchestrator.service` systemd unit (confirmed via
# `/proc/self/cgroup` → `system.slice/orchestrator.service`), and that unit's own
# `/proc/self/mountinfo` shows `/` bind-mounted `ro` FOR THAT MOUNT NAMESPACE
# specifically (per-mount options `ro,nosuid,relatime` vs. the underlying superblock's
# real `rw,discard,...` — a systemd `ProtectSystem`-style sandbox scoped to
# `ReadWritePaths=` under /home + /tmp, not a real host disk/filesystem incident —
# confirmed live 2026-08-10 by cross-checking that `rsyslogd`/`amazon-ssm-agent`/the AO
# server itself keep writing to /var/log in real time on the SAME host while every
# write attempt from an agent-orchestrator worker shell to /opt, /var, or /etc fails
# EROFS, with and without the Bash tool's own sandbox override). So /opt is
# UNREACHABLE from every interactive slot's shell by design, always — hardcoding the
# shared ledger there would silently degrade admission control to unlocked
# best-effort for the interactive-slot side specifically (via
# _qg_ledger_with_lock's existing mkdir-failure degrade — no hard failure, but zero
# real coordination, defeating the point of this fix). /home IS in the sandbox's
# ReadWritePaths (proven: every interactive slot's own git worktree already lives
# there) and the glue-runner CI systemd unit runs as the SAME OS user (`ubuntu`,
# unsandboxed — it already had /opt access, e.g. its own historical ledger writes up
# to 2026-08-05), so /home/ubuntu is writable by BOTH topologies without any new
# provisioning step.
#
# Overridable via QG_HOST_SHARED_LEDGER_ROOT (env, read fresh on every
# _qg_shared_root() call — not captured to a fixed var at source time — so a caller
# can export it at runtime without re-sourcing this file, e.g. from
# install-qg-governor-shell-env.sh or the reusable CI workflow) for a host with a
# different sandbox/ReadWritePaths shape — falls back to unlocked best-effort ledger
# writes via _qg_ledger_with_lock's existing mkdir-failure degrade, same as any other
# missing-dir/unwritable-dir case, never a hard failure.
_QG_HOST_SHARED_LEDGER_ROOT_DEFAULT="${HOME:-/home/ubuntu}/unified-trading-system-repos"
_QG_LEDGER_FD=220

# .tabs branch keeps its ORIGINAL dynamic `${ws%/.tabs/*}` derivation as the fallback
# (not the fixed default directly) so a synthetic WORKSPACE_ROOT under an isolated test
# root (e.g. test-qg-cross-host.sh's `$TMP/h_.../.tabs/1`) still strips to that test's
# OWN isolated dir, not the real host's shared ledger — on the one real host, that
# dynamic derivation already equals $_QG_HOST_SHARED_LEDGER_ROOT_DEFAULT (WORKSPACE_ROOT
# is always ${HOME}/unified-trading-system-repos/.tabs/<N> there), so production
# unification with the glue-runner branch below still holds; QG_HOST_SHARED_LEDGER_ROOT
# overrides BOTH branches when a caller needs to force agreement explicitly.
_qg_shared_root() {
    local ws="${WORKSPACE_ROOT:-}"
    case "$ws" in
        "")                        echo "${TMPDIR:-/tmp}" ;;
        */.tabs/*)                 echo "${QG_HOST_SHARED_LEDGER_ROOT:-${ws%/.tabs/*}}" ;;
        /opt/github-glue-runners*) echo "${QG_HOST_SHARED_LEDGER_ROOT:-$_QG_HOST_SHARED_LEDGER_ROOT_DEFAULT}" ;;
        *)                         echo "$ws" ;;
    esac
}
_qg_ledger_dir()  { echo "${QG_LEDGER_DIR:-$(_qg_shared_root)/.benchmarks/qg-governor}"; }
_qg_ledger_file() { echo "$(_qg_ledger_dir)/reservations"; }

# Run "$@" holding the ledger lock (explicit numeric FD — bash 3.2-safe). Degrades
# to unlocked (best-effort) if the dir can't be made or flock(1) is absent.
_qg_ledger_with_lock() {
    local dir; dir="$(_qg_ledger_dir)"
    mkdir -p "$dir" 2>/dev/null || { "$@"; return; }
    command -v flock >/dev/null 2>&1 || { "$@"; return; }
    eval "exec ${_QG_LEDGER_FD}>\"\$dir/.lock\"" 2>/dev/null || { "$@"; return; }
    flock "$_QG_LEDGER_FD"
    "$@"; local rc=$?
    flock -u "$_QG_LEDGER_FD" 2>/dev/null || true
    eval "exec ${_QG_LEDGER_FD}>&-" 2>/dev/null || true
    return "$rc"
}

# Prune dead-PID rows in place — crash-safe: a killed QG can't leak its reservation
# (replaces the old flock-auto-release guarantee). UNLOCKED — call under the lock.
_qg_ledger_sweep_unlocked() {
    local f; f="$(_qg_ledger_file)"
    [[ -f "$f" ]] || return 0
    local tmp="${f}.tmp.$$" pid repo mb ts
    : > "$tmp"
    while read -r pid repo mb ts; do
        [[ -n "$pid" ]] || continue
        kill -0 "$pid" 2>/dev/null && printf '%s %s %s %s\n' "$pid" "$repo" "$mb" "$ts" >> "$tmp"
    done < "$f"
    mv -f "$tmp" "$f" 2>/dev/null || rm -f "$tmp"
}

# Sum of LIVE reservations (MB), after a sweep. Public (locks internally).
_qg_ledger_reserved_mb() { _qg_ledger_with_lock _qg_ledger_reserved_mb_unlocked; }
_qg_ledger_reserved_mb_unlocked() {
    _qg_ledger_sweep_unlocked
    local f; f="$(_qg_ledger_file)"
    [[ -f "$f" ]] || { echo 0; return; }
    awk '{s+=$3} END{printf "%d", s+0}' "$f"
}

# Add a reservation. Public (locks internally).
_qg_ledger_add() { _qg_ledger_with_lock _qg_ledger_add_unlocked "$1" "$2" "$3" "${4:-0}"; } # <pid> <repo> <rss_mb> [ts]
_qg_ledger_add_unlocked() { printf '%s %s %s %s\n' "$1" "$2" "$3" "$4" >> "$(_qg_ledger_file)"; }

# Remove all rows for a PID (on release). Public (locks internally).
_qg_ledger_remove() { _qg_ledger_with_lock _qg_ledger_remove_unlocked "$1"; } # <pid>
_qg_ledger_remove_unlocked() {
    local f; f="$(_qg_ledger_file)"
    [[ -f "$f" ]] || return 0
    local tmp="${f}.tmp.$$"
    grep -v "^${1} " "$f" > "$tmp" 2>/dev/null || : > "$tmp"
    mv -f "$tmp" "$f" 2>/dev/null || rm -f "$tmp"
}

# Count of LIVE reservations (running heavy-phase count), after a sweep.
_qg_ledger_count() { _qg_ledger_with_lock _qg_ledger_count_unlocked; }
_qg_ledger_count_unlocked() {
    _qg_ledger_sweep_unlocked
    local f; f="$(_qg_ledger_file)"
    [[ -f "$f" ]] || { echo 0; return; }
    awk 'END{print NR+0}' "$f"
}

# ── DUAL-GATE ADMISSION DECISION (Phase 3b — additive; NOT wired into acquire) ──
# _qg_admit_check is PURE (all inputs explicit, no live reads) so every branch is
# unit-testable. It encodes the two-clause RAM gate + CPU gate + oversize-solo:
#   1. oversize      : this_peak > budget      → SOLO (run alone; wait for reserved==0)
#   2. RAM reserve   : reserved + this > budget → WAIT_RAM_RESERVATION (ledger bound; the 6×UTL stacking cap)
#   3. RAM live      : avail < this + floor     → WAIT_RAM_LIVE (external pressure + climb headroom)
#   4. CPU           : running + 1 > slots      → WAIT_CPU
#   else ADMIT. Echoes the decision token; returns 0 iff the run may proceed now.
# SSOT: plans/active/qg_host_adaptive_resource_governor_2026_07_14.md
_qg_admit_check() {
    local this="$1" reserved="$2" running="$3" budget="$4" avail="$5" floor="$6" slots="$7" min_avail="${8:-0}"
    # 0. Host-pressure valve — refuse ANY admit (regardless of this run's size) if the host is
    #    already past 80 % used, i.e. avail < min_avail (= 20 % of MemTotal). Catches aggregate /
    #    non-QG pressure the per-run clauses miss. min_avail=0 (default/omitted) disables it.
    if (( min_avail > 0 && avail < min_avail )); then echo "WAIT_HOST_PRESSURE"; return 1; fi
    if (( this > budget )); then
        if (( reserved == 0 )); then echo "SOLO_ADMIT"; return 0; fi
        echo "SOLO_WAIT"; return 1
    fi
    if (( reserved + this > budget )); then echo "WAIT_RAM_RESERVATION"; return 1; fi
    if (( avail < this + floor )); then echo "WAIT_RAM_LIVE"; return 1; fi
    if (( running + 1 > slots )); then echo "WAIT_CPU"; return 1; fi
    echo "ADMIT"; return 0
}

# Per-repo peak-RSS (MB) from the committed baseline — max(local, vm) is conservative
# and host-portable. Unmeasured repo → QG_UNMEASURED_PEAK_MB (default 5500 = treat as
# heaviest, never a low guess that would under-reserve). QG_BASELINE_PATH overrides for tests.
_qg_repo_peak_mb() {
    local repo="$1" baseline peak
    baseline="${QG_BASELINE_PATH:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../dev" 2>/dev/null && pwd)/qg_resource_baseline.json}"
    peak="$(python3 - "$baseline" "$repo" 2>/dev/null <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    e = d.get(sys.argv[2], {}) or {}
    vals = [(e.get(k) or {}).get("peak_rss_mb") for k in ("local", "vm")]
    vals = [v for v in vals if isinstance(v, (int, float))]
    print(int(max(vals)) if vals else 0)
except Exception:
    print(0)
PY
)"
    [[ "${peak:-0}" -gt 0 ]] && echo "$peak" || echo "${QG_UNMEASURED_PEAK_MB:-5500}"
}

# Per-repo HARD cgroup cap for QG_MEM_CAP = 1.2 × baseline peak, as a systemd size string
# (e.g. "6600M"). The reservation governor sets QG_MEM_CAP to this so a run that outgrows its
# baseline is OOM-killed in its OWN scope, never the host. Floored at 2048M (never absurdly tight).
_qg_repo_mem_cap() {
    local mb; mb="$(_qg_repo_peak_mb "$1")"
    mb=$(( mb * 12 / 10 ))
    (( mb >= 2048 )) || mb=2048
    echo "${mb}M"
}

# Live admission decision for <repo>: gathers ledger + capacity, calls _qg_admit_check.
# Echoes the decision token; returns 0 iff admit-now. (Not yet wired into acquire.)
_qg_admit() {
    local repo="$1" this reserved running mt ma cores frac_pct cpu_pct budget avail floor slots min_avail
    this="$(_qg_repo_peak_mb "$repo")"
    reserved="$(_qg_ledger_reserved_mb)"
    running="$(_qg_ledger_count)"
    mt="$(_qg_mem_total_kb)"; ma="$(_qg_mem_available_kb)"; cores="$(_qg_physical_cores)"
    frac_pct="$(awk -v f="${QG_MEM_SAFETY_FRAC:-0.70}" 'BEGIN{printf "%d", f*100}')"
    cpu_pct="$(awk -v f="${QG_CPU_FRAC:-0.80}" 'BEGIN{printf "%d", f*100}')"
    budget=$(( mt / 1024 * frac_pct / 100 ))          # MB
    avail=$(( ma / 1024 ))                             # MB
    floor="${QG_MEM_FLOOR_MB:-$(( mt / 1024 / 10 ))}" # MB (default 10% of total)
    (( floor >= 2048 )) || floor=2048
    slots=$(( cores * cpu_pct / 100 )); (( slots >= 1 )) || slots=1
    min_avail=$(( mt / 1024 * 20 / 100 ))             # 20% of MemTotal → host-pressure floor
    _qg_admit_check "$this" "$reserved" "$running" "$budget" "$avail" "$floor" "$slots" "$min_avail"
}

# Base file-descriptor for the token locks. The original used bash >=4.1's
# `exec {fd}>` auto-FD form, which is unparseable on bash 3.2 (the macOS
# operator host) → the governor silently went INACTIVE there, so concurrent
# QG runs on a Mac dev host were never throttled (host thrash / OOM, exit 144).
# Explicit numeric FDs opened via `eval "exec $fd>..."` work on bash 3.2 AND
# bash >=4.1, so the governor is now active on every host. High base (200) to
# avoid colliding with FDs quality-gates.sh holds. A token uses base+i (i=1..K).
_QG_GOV_FD_BASE=200
# Temp FD for the non-blocking probe in --status (must not overlap base+1..base+K).
_QG_GOV_PROBE_FD=199

# De-prioritise the current process tree so a held token never starves interactive work.
_qg_governor_deprioritise() {
    local inc="${QG_GOVERNOR_NICE:-10}"
    renice -n "$inc" -p "$$" >/dev/null 2>&1 || true
    ionice -c2 -n7 -p "$$" >/dev/null 2>&1 || true
}

# ── RESERVATION-MODE ACQUIRE (Phase 3c — opt-in via QG_GOVERNOR_MODE=reservation) ─
# Default mode is "token" (the legacy bucket below), so this path is INERT until the
# flag is set — shipping it changes NO live behavior. When active, admission is the
# ATOMIC check-and-reserve: sweep + read + decide + reserve all under ONE ledger lock,
# so N simultaneous acquirers serialize and can never over-admit past the RAM budget.
# SSOT: plans/active/qg_host_adaptive_resource_governor_2026_07_14.md

# UNLOCKED body — call ONLY via _qg_ledger_with_lock. Decides + reserves atomically.
_qg_try_reserve() { # <repo> <this_peak_mb> <pid>
    local repo="$1" this="$2" pid="$3" f reserved running mt ma cores frac_pct cpu_pct budget avail floor slots min_avail decision
    _qg_ledger_sweep_unlocked
    f="$(_qg_ledger_file)"
    reserved="$( [[ -f "$f" ]] && awk '{s+=$3} END{printf "%d", s+0}' "$f" || echo 0 )"
    running="$( [[ -f "$f" ]] && awk 'END{print NR+0}' "$f" || echo 0 )"
    mt="$(_qg_mem_total_kb)"; ma="$(_qg_mem_available_kb)"; cores="$(_qg_physical_cores)"
    frac_pct="$(awk -v x="${QG_MEM_SAFETY_FRAC:-0.70}" 'BEGIN{printf "%d", x*100}')"
    cpu_pct="$(awk -v x="${QG_CPU_FRAC:-0.80}" 'BEGIN{printf "%d", x*100}')"
    budget=$(( mt / 1024 * frac_pct / 100 )); avail=$(( ma / 1024 ))
    floor="${QG_MEM_FLOOR_MB:-$(( mt / 1024 / 10 ))}"; (( floor >= 2048 )) || floor=2048
    slots=$(( cores * cpu_pct / 100 )); (( slots >= 1 )) || slots=1
    min_avail=$(( mt / 1024 * 20 / 100 ))  # host-pressure floor (20% of MemTotal)
    decision="$(_qg_admit_check "$this" "$reserved" "$running" "$budget" "$avail" "$floor" "$slots" "$min_avail")"
    case "$decision" in ADMIT|SOLO_ADMIT) _qg_ledger_add_unlocked "$pid" "$repo" "$this" 0 ;; esac
    echo "$decision"
}

_qg_governor_acquire_reservation() {
    [[ -n "${_QG_RESERVED_PID:-}" ]] && return 0   # idempotent — already holding a reservation
    local repo this waited=0 decision
    repo="${QG_GOVERNOR_REPO:-${SERVICE_NAME:-unknown}}"
    this="$(_qg_repo_peak_mb "$repo")"
    while true; do
        decision="$(_qg_ledger_with_lock _qg_try_reserve "$repo" "$this" "$$")"
        case "$decision" in
            ADMIT|SOLO_ADMIT)
                _QG_RESERVED_PID=$$
                _qg_governor_deprioritise
                QG_GOVERNOR_WAIT_SECONDS=$(( ${QG_GOVERNOR_WAIT_SECONDS:-0} + waited ))
                [[ "$waited" -gt 0 ]] && echo "[qg-governor] ${repo} reserved ${this}MB (${decision}) after ${waited}s" >&2
                _qg_watchdog_start "$repo"
                return 0 ;;
        esac
        sleep 2; waited=$(( waited + 2 ))
        (( waited % 30 == 0 )) && echo "[qg-governor] ${repo} (${this}MB) waiting: ${decision} ${waited}s" >&2
    done
}

# ── RUNTIME ABORT-MONITOR (Phase 4 hardening) ────────────────────────────────
# Closes the gap named in plans/active/qg_host_adaptive_resource_governor_2026_07_14.md
# ("Global 80% valve — admission side SHIPPED; runtime ABORT of an already-running >80%
# job STILL PENDING") and confirmed live by
# plans/active/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md: the
# dual-gate admission check (_qg_admit_check) runs ONCE, at acquire time — nothing
# previously re-checked an ALREADY-ADMITTED run against host RAM pressure that develops
# from OTHER processes (admitted or non-QG) after admission. The only thing that ever
# intervened was the kernel oom-killer's SIGKILL: uncatchable (no EXIT trap fires), so
# the kill is silent — a worker polling for completion cannot tell "still running" from
# "already dead" (the exact failure mode the issue doc measured 7 times).
#
# SELF-SCOPED BY DESIGN: this watchdog can only ever signal the ONE PID it was started
# for (its own caller's $$, captured before backgrounding) and that PID's OWN descendant
# tree — never another slot's process. A bug here cannot kill someone else's legitimate
# work; worst case it self-aborts its own run early. This trades the plan's "pick exactly
# one offender" refinement for a much simpler, safer, fully self-contained mechanism:
# every admitted run monitors host pressure and, if it stays above QG_HOST_RAM_ABORT_PCT
# for QG_WATCHDOG_CONSECUTIVE_HITS consecutive samples, sends itself (+ its live children)
# a SIGTERM (catchable — unlike SIGKILL, the caller's existing EXIT trap fires, releasing
# the reservation) after writing a loud marker file so a poller can distinguish this from
# a live run.
_qg_watchdog_pressure_hit() {
    local mt ma abort_pct min_avail
    mt="$(_qg_mem_total_kb)"; ma="$(_qg_mem_available_kb)"
    abort_pct="${QG_HOST_RAM_ABORT_PCT:-80}"
    min_avail=$(( mt * (100 - abort_pct) / 100 ))
    (( ma < min_avail ))
}

# SIGTERM the root's live descendants (bottom-up) THEN the root itself. Necessary, not
# cosmetic: bash defers running a pending trap until its CURRENT foreground command
# returns — a bare `kill -TERM $root` while $root is blocked in `wait()` on a foreground
# child (pytest/basedpyright/systemd-run --scope) would sit queued and do nothing until
# that child finishes on its own, defeating the whole point. Killing the child directly
# makes `wait()` return immediately (child died), so bash promptly processes the pending
# trap. Walked via `pgrep -P` (own descendants only — never a process-group signal, which
# could hit unrelated siblings sharing the same PGID, e.g. an interactive tmux pane).
# Missing pgrep degrades to root-only (best-effort, same as the rest of this file's
# graceful-degradation posture).
_qg_watchdog_signal_tree() {
    local root="$1" child
    if command -v pgrep >/dev/null 2>&1; then
        for child in $(pgrep -P "$root" 2>/dev/null || true); do
            _qg_watchdog_signal_tree "$child"
        done
    fi
    kill -TERM "$root" 2>/dev/null || true
}

# Background loop body — polls until either the target dies on its own (nothing left to
# protect) or pressure trips the abort. Never touches any PID but $target_pid.
_qg_watchdog_loop() {
    local target_pid="$1" repo="$2" interval hits_needed hits=0 marker_dir marker
    interval="${QG_WATCHDOG_INTERVAL_SECONDS:-15}"
    hits_needed="${QG_WATCHDOG_CONSECUTIVE_HITS:-2}"
    marker_dir="$(_qg_ledger_dir)"; mkdir -p "$marker_dir" 2>/dev/null
    marker="${marker_dir}/aborted.${target_pid}"
    while true; do
        kill -0 "$target_pid" 2>/dev/null || return 0   # target already gone — nothing to protect
        if _qg_watchdog_pressure_hit; then
            hits=$(( hits + 1 ))
            if (( hits >= hits_needed )); then
                {
                    echo "aborted_by=qg-governor-watchdog"
                    echo "target_pid=${target_pid}"
                    echo "repo=${repo}"
                    echo "reason=host_ram_pressure_ge_${QG_HOST_RAM_ABORT_PCT:-80}pct_for_${hits_needed}_consecutive_checks"
                    echo "mem_total_kb=$(_qg_mem_total_kb)"
                    echo "mem_available_kb=$(_qg_mem_available_kb)"
                    echo "aborted_at_epoch=$(date +%s 2>/dev/null || echo 0)"
                } > "$marker" 2>/dev/null
                echo "[qg-governor-watchdog] ${repo} pid=${target_pid}: host RAM pressure >= ${QG_HOST_RAM_ABORT_PCT:-80}% for ${hits_needed} consecutive checks — sending SIGTERM to its process tree (self-scoped, loud abort; marker: ${marker})" >&2
                _qg_watchdog_signal_tree "$target_pid"
                return 0
            fi
        else
            hits=0
        fi
        sleep "$interval"
    done
}

# Start the watchdog for the CURRENT process ($$), in the background. Reservation mode
# only (token mode has no live ledger/pressure math to hook into). Idempotent.
_qg_watchdog_start() {
    [[ "${QG_GOVERNOR_MODE:-token}" == "reservation" ]] || return 0
    [[ "${QG_GOVERNOR_WATCHDOG_DISABLE:-}" == "true" ]] && return 0
    [[ -n "${_QG_WATCHDOG_PID:-}" ]] && return 0   # already running
    local repo="${1:-${QG_GOVERNOR_REPO:-${SERVICE_NAME:-unknown}}}"
    ( _qg_watchdog_loop "$$" "$repo" ) &
    _QG_WATCHDOG_PID=$!
    disown "$_QG_WATCHDOG_PID" 2>/dev/null || true
}

# Stop a running watchdog (normal release path — nothing left to protect once the
# reservation itself is released). Safe no-op if none is running.
_qg_watchdog_stop() {
    [[ -n "${_QG_WATCHDOG_PID:-}" ]] || return 0
    kill "$_QG_WATCHDOG_PID" 2>/dev/null || true
    wait "$_QG_WATCHDOG_PID" 2>/dev/null || true
    _QG_WATCHDOG_PID=""
}

# Acquire one host token (blocks until free). Holds an flock'd fd for the run's lifetime.
#
# Exposes QG_GOVERNOR_WAIT_SECONDS (global, accumulated across calls — 0 if never
# throttled) so a caller's MAX_DURATION wall-clock check can subtract pure queue
# time from billable work time: queueing under K=1-vs-20-way-demand contention is
# not "the run got slow", it's "the run was waiting its turn", and must not fail
# an otherwise-green run on that basis alone
# (qg_host_governor_severe_contention_2026_07_13.md).
qg_governor_acquire() {
    [[ "${QG_GOVERNOR_DISABLE:-}" == "true" ]] && return 0
    [[ "${QG_GOVERNOR_MODE:-token}" == "reservation" ]] && { _qg_governor_acquire_reservation; return; }
    command -v flock >/dev/null 2>&1 || { echo "[qg-governor] flock(1) absent — running ungoverned" >&2; return 0; }
    [[ -n "${_QG_GOV_FD:-}" ]] && return 0   # already holding a token (idempotent)

    local k dir fd
    k="$(_qg_governor_k)"; dir="$(_qg_governor_dir)"
    mkdir -p "$dir" 2>/dev/null || { echo "[qg-governor] cannot create $dir — ungoverned" >&2; return 0; }

    local waited=0
    while true; do
        local i
        for (( i=1; i<=k; i++ )); do
            fd=$(( _QG_GOV_FD_BASE + i ))
            # Explicit numeric FD opened via eval — parses on bash 3.2 (the macOS operator
            # host) AND bash >=4.1. The previous `exec {fd}>` auto-FD form is bash >=4.1-only,
            # so the governor silently went INACTIVE on a Mac → 8-slot QG thrash / OOM (exit 144).
            # On ANY failure we `continue` (try next slot) or fall through ungoverned, so a
            # botched FD never terminates quality-gates.sh before the sentinel is written.
            eval "exec ${fd}>\"\$dir/slot.\$i\"" 2>/dev/null || continue
            if flock -n "$fd"; then
                _QG_GOV_FD=$fd
                _qg_governor_deprioritise
                QG_GOVERNOR_WAIT_SECONDS=$(( ${QG_GOVERNOR_WAIT_SECONDS:-0} + waited ))
                [[ "$waited" -gt 0 ]] && echo "[qg-governor] token $i/$k acquired after ${waited}s wait" >&2
                return 0
            fi
            eval "exec ${fd}>&-"   # slot busy — close and try next
        done
        sleep 2; waited=$(( waited + 2 ))
        # narrate every ~30s so a long queue is visible, not silent
        (( waited % 30 == 0 )) && echo "[qg-governor] all ${k} tokens busy — queued ${waited}s" >&2
    done
}

# Release the held token/reservation (also released automatically when the process exits —
# reservations by PID-liveness sweep, tokens by flock auto-drop on close).
qg_governor_release() {
    if [[ "${QG_GOVERNOR_MODE:-token}" == "reservation" ]]; then
        _qg_watchdog_stop
        [[ -n "${_QG_RESERVED_PID:-}" ]] || return 0
        _qg_ledger_remove "$_QG_RESERVED_PID"
        _QG_RESERVED_PID=""
        return 0
    fi
    [[ -n "${_QG_GOV_FD:-}" ]] || return 0
    flock -u "$_QG_GOV_FD" 2>/dev/null || true
    eval "exec ${_QG_GOV_FD}>&-" 2>/dev/null || true   # explicit FD (bash 3.2-compatible)
    _QG_GOV_FD=""
}

# Base FDs for the total-instance token locks — well clear of the heavy-phase range
# (200+1..200+K, K bounded by cores/4) and the ledger lock FD (220). Two ranges: the
# flat host-wide cap (300+K, K<=~16 in practice) and the per-repo sub-cap (350+K, K<=4
# today but roomy) — kept separate so a partial-acquire backoff (below) can release
# just one without disturbing FD bookkeeping for the other.
_QG_TOTAL_FD_BASE=300
_QG_REPO_FD_BASE=350

# _qg_try_repo_token / _qg_try_global_token — single non-blocking pass over k numbered
# lockfiles under a dir, using the GLOBAL _QG_REPO_TOTAL_FD/_QG_TOTAL_FD variables
# directly (NOT a return-via-$(command substitution) — that would run the exec+flock
# pair inside a forked subshell, whose exit closes the FD and silently drops the flock
# the instant the substitution completes, before the caller ever gets to use it; a real
# bug caught live in this exact function 2026-08-09 by a contention test that showed a
# same-repo second acquirer sailing straight through instead of queueing). Sets the FD
# var and returns 0 on success; returns 1 with the var left empty on failure (having
# closed every FD it opened along the way, so the caller can retry cleanly).
_qg_try_repo_token() {
    local dir="$1" k="$2" i fd
    _QG_REPO_TOTAL_FD=""
    for (( i=1; i<=k; i++ )); do
        fd=$(( _QG_REPO_FD_BASE + i ))
        eval "exec ${fd}>\"\$dir/slot.\$i\"" 2>/dev/null || continue
        if flock -n "$fd"; then
            _QG_REPO_TOTAL_FD=$fd
            return 0
        fi
        eval "exec ${fd}>&-"
    done
    return 1
}
_qg_try_global_token() {
    local dir="$1" k="$2" i fd
    _QG_TOTAL_FD=""
    for (( i=1; i<=k; i++ )); do
        fd=$(( _QG_TOTAL_FD_BASE + i ))
        eval "exec ${fd}>\"\$dir/slot.\$i\"" 2>/dev/null || continue
        if flock -n "$fd"; then
            _QG_TOTAL_FD=$fd
            return 0
        fi
        eval "exec ${fd}>&-"
    done
    return 1
}

# Acquire a TOTAL-INSTANCE token — gates the WHOLE quality-gates.sh run, held from
# right after this file is sourced until the caller's EXIT trap releases it (see
# base-service.sh's qg_governor_acquire_total_instance / _qg_exit_handler wiring),
# unlike qg_governor_acquire above which brackets only the heavy TESTS+TYPECHECK
# phase. Same flock/explicit-numeric-FD pattern (bash 3.2-safe), separate lock dir +
# FD range so the two gates coexist — a run holds a total-instance token for its full
# lifetime AND, later, a heavy-phase token/reservation nested inside it.
#
# TWO-PHASE / COMPOSED (operator ruling 2026-08-09, see _qg_repo_name's comment above
# for the why): admission requires BOTH this repo's own sub-cap AND the flat host-wide
# cap to have room, checked together each cycle — never hold one while blocked on the
# other (that would let a repo's own slot sit idle mid-wait, starving same-repo peers
# for no reason). A cycle that gets the repo token but not the global one releases the
# repo token immediately and retries both from scratch next tick.
qg_governor_acquire_total_instance() {
    [[ "${QG_TOTAL_GOVERNOR_DISABLE:-}" == "true" ]] && return 0
    command -v flock >/dev/null 2>&1 || { echo "[qg-governor] flock(1) absent — total-instance gate ungoverned" >&2; return 0; }
    [[ -n "${_QG_TOTAL_FD:-}" ]] && return 0   # already holding (idempotent)

    local repo_k repo_dir global_k global_dir repo_name
    repo_name="$(_qg_repo_name)"
    repo_k="$(_qg_repo_instance_k)"; repo_dir="$(_qg_repo_instance_dir)"
    global_k="$(_qg_total_k)"; global_dir="$(_qg_total_dir)"
    mkdir -p "$repo_dir" "$global_dir" 2>/dev/null \
        || { echo "[qg-governor] cannot create governor dirs — total-instance gate ungoverned" >&2; return 0; }

    local waited=0
    while true; do
        if _qg_try_repo_token "$repo_dir" "$repo_k"; then
            if _qg_try_global_token "$global_dir" "$global_k"; then
                QG_GOVERNOR_WAIT_SECONDS=$(( ${QG_GOVERNOR_WAIT_SECONDS:-0} + waited ))
                [[ "$waited" -gt 0 ]] && echo "[qg-governor] total-instance token acquired (${repo_name}: <=${repo_k}, host-wide: <=${global_k}) after ${waited}s wait" >&2
                return 0
            fi
            flock -u "$_QG_REPO_TOTAL_FD" 2>/dev/null || true
            eval "exec ${_QG_REPO_TOTAL_FD}>&-" 2>/dev/null || true
            _QG_REPO_TOTAL_FD=""
        fi
        sleep 1; waited=$(( waited + 1 ))
        (( waited % 30 == 0 )) && echo "[qg-governor] total-instance tokens busy (${repo_name} sub-cap ${repo_k} / host-wide cap ${global_k}) — queued ${waited}s" >&2
    done
}

# Release the held total-instance tokens — BOTH the per-repo sub-cap and the flat
# host-wide cap (also auto-freed on process exit — flock auto-drops on fd close).
# Idempotent, safe no-op if never acquired.
qg_governor_release_total_instance() {
    if [[ -n "${_QG_REPO_TOTAL_FD:-}" ]]; then
        flock -u "$_QG_REPO_TOTAL_FD" 2>/dev/null || true
        eval "exec ${_QG_REPO_TOTAL_FD}>&-" 2>/dev/null || true
        _QG_REPO_TOTAL_FD=""
    fi
    [[ -n "${_QG_TOTAL_FD:-}" ]] || return 0
    flock -u "$_QG_TOTAL_FD" 2>/dev/null || true
    eval "exec ${_QG_TOTAL_FD}>&-" 2>/dev/null || true
    _QG_TOTAL_FD=""
}

# Shared by both status branches below — the total-instance gate is orthogonal to
# MODE (token vs reservation), so it's probed the same way regardless.
_qg_total_status_line() {
    local k dir; k="$(_qg_total_k)"; dir="$(_qg_total_dir)"
    if [[ ! -d "$dir" ]]; then
        echo "  total-instance gate: K=${k}  dir=${dir}  tokens held now: 0/${k} (dir not yet created)"
        return 0
    fi
    local held=0 i tfd="$_QG_GOV_PROBE_FD"
    for (( i=1; i<=k; i++ )); do
        [[ -e "$dir/slot.$i" ]] || continue
        if ! ( eval "exec ${tfd}>\"\$dir/slot.\$i\"" && flock -n "$tfd" ) 2>/dev/null; then
            held=$(( held + 1 ))
        fi
    done
    echo "  total-instance gate: K=${k}  dir=${dir}  tokens held now: ${held}/${k}"
}

_qg_governor_status() {
    # Reservation mode: show live capacity, the dual-gate budgets, and current reservations.
    if [[ "${QG_GOVERNOR_MODE:-token}" == "reservation" ]]; then
        local mt ma cores frac_pct cpu_pct budget avail slots reserved running f pid repo mb ts
        mt="$(_qg_mem_total_kb)"; ma="$(_qg_mem_available_kb)"; cores="$(_qg_physical_cores)"
        frac_pct="$(awk -v x="${QG_MEM_SAFETY_FRAC:-0.70}" 'BEGIN{printf "%d", x*100}')"
        cpu_pct="$(awk -v x="${QG_CPU_FRAC:-0.80}" 'BEGIN{printf "%d", x*100}')"
        budget=$(( mt / 1024 * frac_pct / 100 )); avail=$(( ma / 1024 ))
        slots=$(( cores * cpu_pct / 100 )); (( slots >= 1 )) || slots=1
        reserved="$(_qg_ledger_reserved_mb)"; running="$(_qg_ledger_count)"   # both sweep dead PIDs first
        echo "qg-host-governor: MODE=reservation  ledger=$(_qg_ledger_file)  flock=$(command -v flock >/dev/null 2>&1 && echo yes || echo MISSING)"
        echo "  host: MemTotal=$(( mt/1024/1024 ))GiB  MemAvailable=$(( ma/1024/1024 ))GiB  physical_cores=${cores}"
        echo "  RAM budget (${frac_pct}%): ${budget}MB  reserved: ${reserved}MB  free: $(( budget - reserved ))MB  (live avail ${avail}MB)"
        echo "  CPU slots (${cpu_pct}% x ${cores}): ${slots}  running heavy phases: ${running}  (K runaway-backstop=$(_qg_governor_k))"
        f="$(_qg_ledger_file)"
        if [[ -s "$f" ]]; then
            echo "  live reservations (pid repo mb):"
            while read -r pid repo mb ts; do [[ -n "$pid" ]] && echo "    ${pid}  ${repo}  ${mb}MB"; done < "$f"
        else
            echo "  live reservations: none"
        fi
        _qg_total_status_line
        return 0
    fi
    local k dir; k="$(_qg_governor_k)"; dir="$(_qg_governor_dir)"
    echo "qg-host-governor: MODE=token  K=${k}  dir=${dir}  flock=$(command -v flock >/dev/null 2>&1 && echo yes || echo MISSING)"
    if [[ -d "$dir" ]]; then
        local held=0 i tfd="$_QG_GOV_PROBE_FD"
        for (( i=1; i<=k; i++ )); do
            [[ -e "$dir/slot.$i" ]] || continue
            # a slot is held iff a non-blocking flock fails. Explicit numeric probe FD via
            # eval (bash 3.2-compatible) in a SUBSHELL so the open/lock never leaks into the
            # caller's FD table or holds the lock past the probe.
            if ! ( eval "exec ${tfd}>\"\$dir/slot.\$i\"" && flock -n "$tfd" ) 2>/dev/null; then
                held=$(( held + 1 ))
            fi
        done
        echo "  tokens held now: ${held}/${k}"
    fi
    _qg_total_status_line
}

# ── CLI entrypoint (only when executed directly, not when sourced) ───────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        --status) _qg_governor_status ;;
        --probe) qg_host_capacity ;;
        --)
            shift
            [[ $# -ge 1 ]] || { echo "usage: qg-host-governor.sh -- <command> [args...]" >&2; exit 2; }
            qg_governor_acquire
            trap qg_governor_release EXIT
            "$@"; rc=$?
            qg_governor_release
            exit "$rc"
            ;;
        *) echo "usage: qg-host-governor.sh [--status | --probe | -- <command...>]" >&2; exit 2 ;;
    esac
fi
