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

  if printf '%s' "${base}" | grep -qiE 'quality-gates' || has pull_request; then
    verdict="KEEP"; keep=$((keep+1))
  elif [ -n "${heavy}" ]; then
    verdict="KEEP*"; keep=$((keep+1)) # kept because it builds locally (heavy compute)
  else
    verdict="MOVE"; move=$((move+1))
  fi
  printf '%-40s %-6s %s\n' "${base}" "${verdict}" "${trig}"
done
echo
printf 'MOVE (→ self-hosted glue): %d   KEEP (→ GitHub-hosted): %d  [KEEP* = kept due to local build/heavy compute]\n' "${move}" "${keep}"
echo 'Flip only MOVE workflows: runs-on: ubuntu-latest → runs-on: [self-hosted, glue]. Migrate one first.'
