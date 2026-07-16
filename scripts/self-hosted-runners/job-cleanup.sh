#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue host retired (B2/B3)
#
# job-cleanup.sh — ACTIONS_RUNNER_HOOK_JOB_COMPLETED for the LONG-LIVED (writer) pool.
#
# The JIT-ephemeral pool wipes _work in its ExecStart wrapper, which is correct there because one
# process serves exactly one job. The writer pool serves MANY jobs in ONE process, so that wrapper
# line runs once per boot and never again → _work would grow unbounded. The runner's own post-job
# hook is the right mechanism: it fires after EVERY job on this runner.
#
# The runner invokes this with cwd somewhere inside _work, so we cd to the runner root first (the
# wrapper exports GLUE_RUNNER_DIR precisely so we don't have to guess it from RUNNER_WORKSPACE).
set -euo pipefail

: "${GLUE_RUNNER_DIR:?job-cleanup.sh: GLUE_RUNNER_DIR not set (exported by glue-runner-run.sh)}"
cd "${GLUE_RUNNER_DIR}"

rm -rf _work/* _diag/*.log 2>/dev/null || true
echo "[job-cleanup] wiped _work + _diag in ${GLUE_RUNNER_DIR}"
