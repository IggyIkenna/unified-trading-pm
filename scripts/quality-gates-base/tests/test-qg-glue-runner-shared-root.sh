#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the glue-runner-topology branch of _qg_shared_root() in
# qg-host-governor.sh (plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md).
#
# WHY: on the GHA self-hosted glue-runner host, quality-gates.sh's own
# `WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"` resolves to a
# per-repo-job path under the repo's own POOL_TAG-suffixed runner dir
# (/opt/github-glue-runners[-<repo>]/glue-N/_work/<repo>) — confirmed live 2026-08-02 to
# defeat cross-repo ledger coordination the same way a raw per-slot WORKSPACE_ROOT would
# defeat cross-slot coordination (the bug _qg_shared_root() already fixes for .tabs).
#
# Covers:
#   1. two DIFFERENT simulated repos' runner workdirs resolve to the IDENTICAL shared root
#   2. a THIRD pool tag (including PM's own untagged pool) resolves to the same root too
#   3. the .tabs slot-worktree branch is UNCHANGED (no regression)
#   4. an unrelated WORKSPACE_ROOT is UNCHANGED (no false-positive match)
#   5. the empty-WORKSPACE_ROOT fallback is UNCHANGED
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-glue-runner-shared-root.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
# shellcheck source=/dev/null
source "$GOV"
FAILS=0

eq() {
    if [[ "$2" == "$3" ]]; then
        echo "PASS: $1 ($3)"
    else
        echo "FAIL: $1 — expected '$2' got '$3'"
        FAILS=$((FAILS + 1))
    fi
}

# (1)+(2) three different repos' glue-runner job workdirs — one untagged (PM's own pool),
# two POOL_TAG-suffixed — all collapse to the SAME shared root.
export WORKSPACE_ROOT="/opt/github-glue-runners/glue-1/_work/unified-trading-pm"
r1="$(_qg_shared_root)"
export WORKSPACE_ROOT="/opt/github-glue-runners-ml-service/glue-2/_work/ml-service"
r2="$(_qg_shared_root)"
export WORKSPACE_ROOT="/opt/github-glue-runners-ao/glue-1/_work/agent-orchestrator"
r3="$(_qg_shared_root)"

eq "PM untagged pool resolves to the shared root" "$_QG_GLUE_RUNNER_SHARED_ROOT" "$r1"
eq "ml-service pool resolves to the SAME shared root as PM" "$r1" "$r2"
eq "ao pool resolves to the SAME shared root as PM" "$r1" "$r3"

# (3) .tabs slot-worktree branch unaffected (regression guard)
export WORKSPACE_ROOT="/home/ubuntu/unified-trading-system-repos/.tabs/3"
r4="$(_qg_shared_root)"
eq ".tabs slot-worktree still strips to the pre-.tabs parent" \
    "/home/ubuntu/unified-trading-system-repos" "$r4"

# (4) an unrelated absolute path (no .tabs, not under /opt/github-glue-runners) is echoed
# back unchanged — the pre-existing catchall behavior.
export WORKSPACE_ROOT="/home/ubuntu/some-other-workspace"
r5="$(_qg_shared_root)"
eq "unrelated WORKSPACE_ROOT is unaffected (no false-positive match)" \
    "/home/ubuntu/some-other-workspace" "$r5"

# (5) empty WORKSPACE_ROOT still falls back to TMPDIR/tmp, unaffected.
unset WORKSPACE_ROOT
export TMPDIR=/fake/tmp
r6="$(_qg_shared_root)"
eq "empty WORKSPACE_ROOT still falls back to TMPDIR" "/fake/tmp" "$r6"

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
