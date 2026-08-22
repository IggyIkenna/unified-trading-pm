#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
# Toggle AWS image builds fleet-wide — the single switch for the AWS build path.
#
#   bash scripts/cicd/toggle-aws-image-builds.sh off          # disable (default state since 2026-07-03)
#   bash scripts/cicd/toggle-aws-image-builds.sh on           # enable fleet-wide
#   bash scripts/cicd/toggle-aws-image-builds.sh on <repo>…   # enable only for the named repos
#   bash scripts/cicd/toggle-aws-image-builds.sh status       # show current state everywhere
#
# What the switch controls (all three AWS build surfaces):
#   1. Per-repo GHA variable AWS_BUILDS_ENABLED — gates the `build-aws` job in the PM-hosted
#      reusable image-build-validate.yml (vars resolve from the CALLING repo, so per-repo).
#   2. PM's AWS_BUILDS_ENABLED — gates `route-build` in cloud-build-router-aws.yml.
#   3. The native GitHub webhook on each AWS CodeBuild project (ap-northeast-1, acct
#      427895769566) — these build on EVERY push independent of GHA and are the real spend;
#      `on` re-creates them, `off` deletes them.
#
# Re-enabling ALSO requires the AWS_BUILD_ROLE_ARN secret (GitHub-OIDC role) which was never
# provisioned — assigned to Ikenna, see ikenna_orchestrator/pings/slot_0.md § CREDENTIAL
# APPROVAL REQUEST — AWS_BUILD_ROLE_ARN. Without it the build-aws job fails at OIDC auth.
#
# Operator decision 2026-07-03 (Harsh): AWS builds were a test; GCP Cloud Build is the
# production path; default = off.
# SSOT: plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md § Phase 2 +
#       codex/05-infrastructure/dual-cloud-image-builds.md
# Epic: ci_master
# Lifecycle: permanent (operational toggle)

set -euo pipefail

OWNER="IggyIkenna"
AWS_REGION="ap-northeast-1"
PM_REPO="unified-trading-pm"

MODE="${1:-}"
shift || true

if [[ "$MODE" != "on" && "$MODE" != "off" && "$MODE" != "status" ]]; then
  echo "usage: $0 on|off|status [repo …]" >&2
  exit 2
fi

# The repos that carry image-build-gate.yml / CodeBuild projects. Named repos (if any) override.
if [[ $# -gt 0 ]]; then
  REPOS=("$@")
else
  mapfile -t REPOS < <(aws codebuild list-projects --region "$AWS_REGION" --query 'projects' --output text | tr '\t' '\n' | sort)
fi

case "$MODE" in
  status)
    echo "PM router switch: AWS_BUILDS_ENABLED=$(gh variable get AWS_BUILDS_ENABLED --repo "$OWNER/$PM_REPO" 2>/dev/null || echo '<unset (off)>')"
    for r in "${REPOS[@]}"; do
      var=$(gh variable get AWS_BUILDS_ENABLED --repo "$OWNER/$r" 2>/dev/null || echo "<unset (off)>")
      hook=$(aws codebuild batch-get-projects --names "$r" --region "$AWS_REGION" --query 'projects[0].webhook.url' --output text 2>/dev/null)
      [[ "$hook" == "None" || -z "$hook" ]] && hook="none" || hook="ACTIVE"
      echo "$r: var=$var webhook=$hook"
    done
    ;;
  on)
    gh variable set AWS_BUILDS_ENABLED --body true --repo "$OWNER/$PM_REPO"
    echo "PM router switch: ON"
    for r in "${REPOS[@]}"; do
      gh variable set AWS_BUILDS_ENABLED --body true --repo "$OWNER/$r"
      aws codebuild create-webhook --project-name "$r" --region "$AWS_REGION" \
        --filter-groups '[[{"type":"EVENT","pattern":"PUSH"}]]' >/dev/null 2>&1 \
        && echo "$r: var=true webhook=created" \
        || echo "$r: var=true webhook=FAILED (create manually or already exists)"
    done
    echo "REMINDER: build-aws still needs the AWS_BUILD_ROLE_ARN secret per repo (Ikenna — see slot_0.md ping)."
    ;;
  off)
    gh variable set AWS_BUILDS_ENABLED --body false --repo "$OWNER/$PM_REPO" 2>/dev/null || true
    echo "PM router switch: OFF"
    for r in "${REPOS[@]}"; do
      gh variable set AWS_BUILDS_ENABLED --body false --repo "$OWNER/$r" 2>/dev/null || true
      aws codebuild delete-webhook --project-name "$r" --region "$AWS_REGION" 2>/dev/null \
        && echo "$r: var=false webhook=deleted" \
        || echo "$r: var=false webhook=none"
    done
    ;;
esac
