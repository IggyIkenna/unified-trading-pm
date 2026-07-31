#!/usr/bin/env bash
# Epic: cicd_mvp_ldr_to_main_pipeline_2026_06_30
# Lifecycle: permanent
# Delete-when: NA
#
# ldr-to-main-promote-heartbeat.sh — deterministic 15-min heartbeat that force-dispatches
# the LDR->main promoter workflows via `gh workflow run`, instead of relying solely on
# GitHub Actions' `schedule:` trigger.
#
# WHY (operator decision 2026-07-27/28, Option A of
# plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md Phase-2 "Cron reliability"):
# GHA silently drops a meaningful fraction of scheduled ticks under load (measured ~37% at
# one point; corrected to ~80-90% 2026-07-21 per codex/08-workflows/ci-cd-flow.md — but even
# at 80-90% delivery, a run of dropped ticks can still stretch an intended 15-min drain
# cadence out to 30-90 min). `gh workflow run` (workflow_dispatch via the GitHub API) is a
# direct synchronous call, not a GHA-internal scheduler tick — it either succeeds or errors
# loudly, so a cron that calls it is a DETERMINISTIC top-up, not a replacement for the
# workflows' own `schedule:` triggers (both stay in place; this just closes the gap between
# ticks the scheduler drops).
#
# WHY a VM heartbeat and not a tighter `cron:` interval: the promoter workflows already tried
# that (`ldr-to-main-promote-fleet.yml` over-declares to `*/5` for exactly this reason — see
# its own top-of-file comment) and it still isn't fully reliable. This VM (the orchestrator,
# id `planning`) already runs other cron-driven automation (reap_stale_blockers.py,
# slot-cron-ff-pull.sh) via systemd timers, so this follows the SAME sanctioned pattern.
#
# Dispatches BOTH promoter workflows every tick (both suffer the same schedule: unreliability
# and are both idempotent -- a workflow_dispatch on an already-current tip is a safe no-op
# re-check; both workflows reuse/re-arm an existing frozen-head PR rather than opening a
# duplicate):
#   - ldr-to-main-promote-fleet.yml   (fleet-wide: drains every promotion_model=ldr_main repo)
#   - ldr-to-main-promote.yml         (PM-only: PM's own standing LDR->main PR, Option-B)
#
# Usage (systemd — see install_ldr_to_main_promote_heartbeat.sh):
#   bash scripts/orchestrator/ldr-to-main-promote-heartbeat.sh
#
# Manual test (safe — workflow_dispatch on both is idempotent):
#   bash scripts/orchestrator/ldr-to-main-promote-heartbeat.sh
#
# Env overrides:
#   WORKSPACE_ROOT   — root containing the unified-trading-pm checkout
#                       (default: /home/ubuntu/unified-trading-system-repos, matches the
#                        other orchestrator systemd units e.g. reap-stale-blockers.service)
#   PM_REPO_OWNER    — GitHub owner (default: IggyIkenna)
#   PROMOTE_REF      — ref to dispatch workflow_dispatch against (default: live-defi-rollout)
#
# SSOT: plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md Phase-2 "Cron reliability".

set -uo pipefail # deliberately NOT -e: one workflow's dispatch failing must not skip the other

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/home/ubuntu/unified-trading-system-repos}"
PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
OWNER="${PM_REPO_OWNER:-IggyIkenna}"
REF="${PROMOTE_REF:-live-defi-rollout}"
WORKFLOWS=("ldr-to-main-promote-fleet.yml" "ldr-to-main-promote.yml")

if [ -f "${PM_DIR}/scripts/workspace/load-gh-token.sh" ]; then
  # shellcheck source=/dev/null
  WORKSPACE_ROOT="${WORKSPACE_ROOT}" source "${PM_DIR}/scripts/workspace/load-gh-token.sh"
else
  echo "WARN: ${PM_DIR}/scripts/workspace/load-gh-token.sh not found -- relying on ambient gh auth" >&2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "FATAL: gh CLI not found on PATH -- cannot dispatch promoter workflows" >&2
  exit 1
fi

STATUS=0
for wf in "${WORKFLOWS[@]}"; do
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if gh workflow run "${wf}" --repo "${OWNER}/unified-trading-pm" --ref "${REF}" 2>&1; then
    echo "[${ts}] heartbeat: dispatched ${wf} @ ${REF}"
  else
    echo "[${ts}] WARN heartbeat: dispatch FAILED for ${wf} @ ${REF}" >&2
    STATUS=1
  fi
done

exit "${STATUS}"
