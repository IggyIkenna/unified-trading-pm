#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1)
# Lifecycle: permanent
# Delete-when: glue host retired (B2/B3)
#
# classify-glue-workflows.sh — for every unified-trading-pm workflow, print whether it should MOVE to
# the self-hosted `glue` runners or STAY on GitHub-hosted, from its TRIGGERS.
#
# Rule: KEEP on hosted if it is a real test gate (quality-gates*) OR is pull_request-triggered
# (CPU-heavy / dev-facing). MOVE if it is IO-bound automation glue (repository_dispatch / schedule /
# push / workflow_dispatch only). Advisory — eyeball the output before flipping any runs-on.
set -euo pipefail

WF_DIR="${WF_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.github/workflows" && pwd)}"
[ -d "${WF_DIR}" ] || { echo "no workflows dir at ${WF_DIR}" >&2; exit 1; }
# fleet workflow-templates dir (rolled out to every repo); may be absent
TMPL_DIR="$(cd "${WF_DIR}/../../scripts/workflow-templates" 2>/dev/null && pwd || true)"

# CROSS-REPO REUSABLES (KEEP-R): workflows called by OTHER repos via
#   `uses: <owner>/unified-trading-pm/.github/workflows/<name>@<ref>`.
# A reusable's jobs run on the CALLER's runners. Our `glue` runners are repo-scoped to PM (personal
# accounts can't register org runners), so they are invisible to the calling repo — flipping runs-on
# here would hang the job in EVERY calling repo (same failure mode as KEEP-T). Regenerate the list:
#   rg -o "uses:.*unified-trading-pm/\.github/workflows/[a-z0-9-]+\.yml" */.github/workflows/ \
#     | sed -E 's#.*/##; s/@.*//' | sort -u
# (python-quality-gates-v2 is already KEEP via the quality-gates match; image-build-validate is the
#  other cross-repo reusable — called by 24 repos' image-build-gate.yml to gate staging→main promote.)
REUSABLE_CROSSREPO="image-build-validate.yml"

# FAILURE-INDEPENDENCE MONITORS (KEEP-M): a dead-man-switch / watcher whose whole value is detecting
# that OUR infra (incl. this very VM) is broken MUST run on infra independent of what it watches. If it
# ran on the glue pool, a VM outage would silently take out BOTH the detection AND the alert (the
# alerter is on the down box). These are light (a few $/mo total) and GitHub-hosted is the right home —
# KEPT HOSTED by operator decision 2026-07-16:
#   - overnight-dead-man-switch:   detects the overnight orchestrator (which runs on this VM) failing.
#   - ci-health:                   fleet-wide workflow-failure detector + stuck-PR auto-recovery.
#   - cloud-build-failure-watcher: the ONLY detector for out-of-band Cloud Build failures.
#   - ldr-ci-monitor:              per-repo "is LDR green?" signal.
#   - branch-health:               promotion-lag / drift / AR-lag monitor.
KEEP_MONITORS="overnight-dead-man-switch.yml ci-health.yml cloud-build-failure-watcher.yml ldr-ci-monitor.yml branch-health.yml"

printf '%-40s %-6s %s\n' "WORKFLOW" "VERDICT" "TRIGGERS (on:)"
printf '%-40s %-6s %s\n' "--------" "------" "--------------"
move=0 keep=0
for f in "${WF_DIR}"/*.yml; do
  base="$(basename "${f}")"
  # extract the `on:` block: from a line starting `on:` up to the next top-level key
  on_block="$(awk '/^on:/{grab=1} grab{print} /^[a-zA-Z]/ && !/^on:/ && grab>1{exit} grab{grab++}' "${f}")"
  has() { printf '%s' "${on_block}" | grep -qE "^[[:space:]]*$1\b"; }
  trig=""
  for t in pull_request repository_dispatch schedule push workflow_dispatch workflow_call; do
    has "${t}" && trig+="${t} "
  done
  [ -z "${trig}" ] && trig="(none/manual)"

  # HEAVY-compute detection: a job that BUILDS locally (docker image / wheel) is CPU/RAM-heavy and must NOT run on the
  # light glue VM — keep it hosted. NOTE: `gcloud builds triggers run` / `codebuild start-build` only DISPATCH to the
  # cloud (light on the runner), so they are NOT heavy.
  heavy=""
  grep -qiE 'docker build|docker buildx|buildx build|docker/build-push|(uv|poetry|python -m) build|twine upload|npm (run )?build|pytest' "${f}" && heavy="1"

  # TEMPLATED detection: this workflow is a fleet template (scripts/workflow-templates/) rolled out to EVERY repo.
  # Only PM has glue runners, so flipping the TEMPLATE runs-on to self-hosted would hang it in the other ~24 repos.
  # And hand-editing PM's per-repo copy is banned. So a templated glue workflow stays HOSTED (or needs a conditional).
  tmpl=""
  if [ -n "${TMPL_DIR}" ] && { [ -e "${TMPL_DIR}/${base}" ] || [ -e "${TMPL_DIR}/${base}.tmpl" ]; }; then
    tmpl="1"
  fi

  if printf '%s' "${base}" | grep -qiE 'quality-gates' || has pull_request; then
    verdict="KEEP"; keep=$((keep+1))
  elif [ -n "${heavy}" ]; then
    verdict="KEEP*"; keep=$((keep+1)) # kept because it builds locally (heavy compute)
  elif [ -n "${tmpl}" ]; then
    verdict="KEEP-T"; keep=$((keep+1)) # templated multi-repo — do NOT flip the template (only PM has runners)
  elif printf '%s\n' ${REUSABLE_CROSSREPO} | grep -qx "${base}"; then
    verdict="KEEP-R"; keep=$((keep+1)) # cross-repo reusable — flipping hangs the calling repos (only PM has glue runners)
  elif printf '%s\n' ${KEEP_MONITORS} | grep -qx "${base}"; then
    verdict="KEEP-M"; keep=$((keep+1)) # failure-independence monitor — must NOT run on the infra it watches
  else
    verdict="MOVE"; move=$((move+1))
  fi
  printf '%-40s %-6s %s\n' "${base}" "${verdict}" "${trig}"
done
echo
printf 'MOVE (→ PM-local direct flip): %d   KEEP (→ GitHub-hosted): %d\n' "${move}" "${keep}"
echo '  KEEP* = local build/heavy compute · KEEP-T = fleet template (multi-repo; only PM has runners → keep hosted)'
echo '  KEEP-R = cross-repo reusable (caller-runner-scoped; flip hangs callers) · KEEP-M = failure-independence monitor'
echo 'Flip only MOVE workflows: runs-on: ubuntu-latest → runs-on: [self-hosted, glue]. Migrate one first.'
