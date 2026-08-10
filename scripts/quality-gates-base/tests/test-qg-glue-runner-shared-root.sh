#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for the glue-runner-topology branch of _qg_shared_root() in
# qg-host-governor.sh (plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md),
# and its 2026-08-10 unification with the interactive-slot (.tabs) branch
# (ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md todo 2).
#
# WHY: on the GHA self-hosted glue-runner host, quality-gates.sh's own
# `WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"` resolves to a
# per-repo-job path under the repo's own POOL_TAG-suffixed runner dir
# (/opt/github-glue-runners[-<repo>]/glue-N/_work/<repo>) — confirmed live 2026-08-02 to
# defeat cross-repo ledger coordination the same way a raw per-slot WORKSPACE_ROOT would
# defeat cross-slot coordination (the bug _qg_shared_root() already fixes for .tabs).
# Both topologies were ALSO found (2026-08-10) to resolve to two genuinely DISJOINT
# directories from each other — same host, same filesystem device id, different inodes
# — so admission control on one side had zero visibility into the other's concurrent
# load even though both call qg_governor_acquire() in reservation mode. Fixed by
# collapsing both branches to the SAME $_QG_HOST_SHARED_LEDGER_ROOT_DEFAULT.
#
# Covers:
#   1. two DIFFERENT simulated repos' runner workdirs resolve to the IDENTICAL shared root
#   2. a THIRD pool tag (including PM's own untagged pool) resolves to the same root too
#   3. a .tabs slot-worktree path now resolves to the SAME shared root as glue-runner CI
#      (the 2026-08-10 fix — previously this stripped to a DIFFERENT, .tabs-private root)
#   4. an unrelated WORKSPACE_ROOT is UNCHANGED (no false-positive match)
#   5. the empty-WORKSPACE_ROOT fallback is UNCHANGED
#   6. QG_HOST_SHARED_LEDGER_ROOT overrides the default for BOTH topologies at once
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

eq "PM untagged pool resolves to the shared root" "$_QG_HOST_SHARED_LEDGER_ROOT_DEFAULT" "$r1"
eq "ml-service pool resolves to the SAME shared root as PM" "$r1" "$r2"
eq "ao pool resolves to the SAME shared root as PM" "$r1" "$r3"

# (3) a .tabs slot-worktree path now resolves to the SAME shared root as glue-runner CI
# (2026-08-10 fix — previously this branch stripped to a DIFFERENT, .tabs-private root,
# which is exactly the disjoint-ledger bug ldr_qg_v2_ci_host_contention_false_wall_2026_08_03.md
# todo 2 fixed).
export WORKSPACE_ROOT="/home/ubuntu/unified-trading-system-repos/.tabs/3"
r4="$(_qg_shared_root)"
eq ".tabs slot-worktree now collapses to the SAME shared root as glue-runner CI" \
    "$_QG_HOST_SHARED_LEDGER_ROOT_DEFAULT" "$r4"

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

# (6) QG_HOST_SHARED_LEDGER_ROOT overrides the default for BOTH topologies at once — this
# is the actual cross-surface coordination mechanism: the reusable CI workflow and the
# interactive-slot shell-env installer can both pin an explicit shared dir.
export QG_HOST_SHARED_LEDGER_ROOT="/tmp/qg-shared-root-override-test"
export WORKSPACE_ROOT="/home/ubuntu/unified-trading-system-repos/.tabs/7"
r7="$(_qg_shared_root)"
export WORKSPACE_ROOT="/opt/github-glue-runners-ao/glue-1/_work/agent-orchestrator"
r8="$(_qg_shared_root)"
unset QG_HOST_SHARED_LEDGER_ROOT
eq "QG_HOST_SHARED_LEDGER_ROOT override applies to the .tabs branch" \
    "/tmp/qg-shared-root-override-test" "$r7"
eq "QG_HOST_SHARED_LEDGER_ROOT override applies to the glue-runner branch too" "$r7" "$r8"

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
