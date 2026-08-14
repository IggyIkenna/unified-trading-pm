#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the Phase-2 host-capacity introspection in qg-host-governor.sh
# (plans/active/qg_host_adaptive_resource_governor_2026_07_14.md).
#
# Parses capacity on FIXTURES, never the live host:
#   (a) Linux  — QG_MEMINFO_PATH points at a fixture /proc/meminfo.
#   (b) macOS  — uname/sysctl/vm_stat faked on PATH; asserts the vm_stat
#                available-memory approximation (free+inactive+purgeable+file-backed).
#   (c) shape  — qg_host_capacity emits the expected key=value fields.
#
# OS-branch + command isolation runs in subshells; each subshell EXITS with its
# own failure count so a regression inside it propagates to the parent (a naive
# global counter would be lost across the subshell boundary → false green).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-host-capacity.sh
set -euo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
FAILS=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# eq <label> <expected> <actual> — prints PASS/FAIL, returns non-zero on mismatch.
eq() {
    if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; return 0; fi
    echo "FAIL: $1 — expected '$2' got '$3'"
    return 1
}
have() { # have <label> <needle> <haystack>
    case "$3" in *"$2"*) echo "PASS: $1"; return 0 ;; esac
    echo "FAIL: $1 — '$2' not in output"
    return 1
}

# shellcheck source=/dev/null
source "$GOV"

# ── (a) Linux path via QG_MEMINFO_PATH fixture ───────────────────────────────
cat > "$TMP/meminfo" <<'EOF'
MemTotal:       16384000 kB
MemFree:         1000000 kB
MemAvailable:   11534336 kB
Buffers:          200000 kB
EOF
(
    _qg_is_macos() { return 1; } # force the non-macOS branch regardless of host
    export QG_MEMINFO_PATH="$TMP/meminfo"
    rc=0
    eq "linux MemTotal kB" 16384000 "$(_qg_mem_total_kb)" || rc=1
    eq "linux MemAvailable kB" 11534336 "$(_qg_mem_available_kb)" || rc=1
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (b) macOS path with faked uname/sysctl/vm_stat on PATH ───────────────────
FAKE="$TMP/bin"
mkdir -p "$FAKE"
cat > "$FAKE/uname" <<'EOF'
#!/usr/bin/env bash
echo "Darwin"
EOF
cat > "$FAKE/sysctl" <<'EOF'
#!/usr/bin/env bash
case "${2:-}" in
    hw.memsize)     echo 25769803776 ;;   # 24 GiB in bytes
    hw.pagesize)    echo 16384 ;;         # Apple-silicon 16 KiB page
    hw.physicalcpu) echo 10 ;;
    *)              echo 0 ;;
esac
EOF
cat > "$FAKE/vm_stat" <<'EOF'
#!/usr/bin/env bash
cat <<'OUT'
Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                          100000.
Pages active:                        999999.
Pages inactive:                      80000.
Pages speculative:                   1234.
Pages purgeable:                     20000.
File-backed pages:                   40000.
Anonymous pages:                     555555.
Pages occupied by compressor:        333.
OUT
EOF
chmod +x "$FAKE"/uname "$FAKE"/sysctl "$FAKE"/vm_stat
(
    PATH="$FAKE:$PATH"
    rc=0
    # 25769803776 B / 1024 = 25165824 KB
    eq "macos MemTotal kB" 25165824 "$(_qg_mem_total_kb)" || rc=1
    # (100000+80000+20000+40000)=240000 pages * 16384 B / 1024 = 3840000 KB
    eq "macos MemAvailable kB (free+inactive+purgeable+filebacked)" 3840000 "$(_qg_mem_available_kb)" || rc=1
    eq "macos physical cores" 10 "$(_qg_physical_cores)" || rc=1
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (c) qg_host_capacity output shape + derived budget ───────────────────────
(
    _qg_is_macos() { return 1; }
    export QG_MEMINFO_PATH="$TMP/meminfo"
    out="$(qg_host_capacity)"
    rc=0
    for key in mem_total_gb mem_available_gb cores ram_budget_gb cpu_slots; do
        have "capacity has ${key}=" "${key}=" "$out" || rc=1
    done
    # 16384000 kB * 70% / 1024 / 1024 = 10 GiB budget
    eq "capacity ram_budget_gb (70% of 16 GiB)" "ram_budget_gb=10" \
        "$(printf '%s' "$out" | tr ' ' '\n' | grep '^ram_budget_gb=')" || rc=1
    exit "$rc"
) || FAILS=$((FAILS + 1))

# ── (d) _qg_governor_default_k dedupes hyperthread siblings via _qg_physical_cores
# (regression for the hyperthreading double-count bug — was its own undeduped
# `lscpu -p=core | grep -vc '^#'` inline, plans/active/qg_host_adaptive_resource_governor_2026_07_14.md).
# Fake `lscpu -p=core` simulates 32 physical cores x 2 HT threads = 64 logical rows,
# each physical core id (0-31) appearing twice. The old buggy code would count all
# 64 rows -> K=floor(64/4)=16; the fixed code delegates to _qg_physical_cores's
# sort -u dedup -> 32 physical -> K=floor(32/4)=8.
FAKE_LSCPU="$TMP/bin-lscpu"
mkdir -p "$FAKE_LSCPU"
cat > "$FAKE_LSCPU/lscpu" <<'EOF'
#!/usr/bin/env bash
echo "# comment line"
for i in $(seq 0 31); do echo "$i"; done
for i in $(seq 0 31); do echo "$i"; done
EOF
chmod +x "$FAKE_LSCPU/lscpu"
(
    _qg_is_macos() { return 1; } # force the non-macOS (lscpu) branch
    PATH="$FAKE_LSCPU:$PATH"
    rc=0
    eq "HT-simulated physical cores (deduped)" 32 "$(_qg_physical_cores)" || rc=1
    eq "governor default K uses deduped physical cores, not logical" 8 "$(_qg_governor_default_k)" || rc=1
    exit "$rc"
) || FAILS=$((FAILS + 1))

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL BLOCKS PASSED"; else echo "FAILED BLOCKS: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
