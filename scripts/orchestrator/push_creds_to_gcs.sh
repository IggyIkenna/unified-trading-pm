#!/usr/bin/env bash
# push_creds_to_gcs.sh — push the operator's freshly-authed claude credentials to GCS.
#
# §9e of claude_credentials_rotation_in_memory_staleness_2026_05_21.md (Harsh's fix).
# Workflow:
#   1. Operator runs `claude setup-token` (or `claude /login`) on their laptop.
#   2. Operator runs this script with the matching account_id.
#   3. Script reads ~/.claude/.credentials.json + uploads to
#      gs://<bucket>/accounts/<account_id>.json.
#   4. Every VM's GCSCredsPoller pulls within 5 min → new tokens propagate to
#      all worker spawns on all VMs automatically.
#
# Usage:
#   bash push_creds_to_gcs.sh harsh-primary
#   bash push_creds_to_gcs.sh sub-b-iggy2london
#
# Env:
#   ORCHESTRATOR_CREDS_GCS_BUCKET   — required (e.g. "agent-orchestrator-creds-prd")
#   ORCHESTRATOR_CREDS_GCS_PREFIX   — defaults to "accounts"
#
# Prereqs:
#   - `gsutil` on PATH + ADC configured for a GCS-writer account
#   - Bucket must exist + use the shared agent-orchestrator-state-encrypt KMS key
#     (created once per environment by Phase 8 infra setup)

set -euo pipefail

if [[ -z "${1:-}" ]]; then
    echo "Usage: $0 <account_id>" >&2
    echo "Example: $0 harsh-primary" >&2
    exit 2
fi

ACCOUNT_ID="$1"
BUCKET="${ORCHESTRATOR_CREDS_GCS_BUCKET:-}"
PREFIX="${ORCHESTRATOR_CREDS_GCS_PREFIX:-accounts}"
CREDS_FILE="${HOME}/.claude/.credentials.json"

if [[ -z "${BUCKET}" ]]; then
    echo "ERROR: ORCHESTRATOR_CREDS_GCS_BUCKET not set" >&2
    echo "Set it to the per-env credentials bucket, e.g.:" >&2
    echo "  export ORCHESTRATOR_CREDS_GCS_BUCKET=agent-orchestrator-creds-prd" >&2
    exit 1
fi

if [[ ! -f "${CREDS_FILE}" ]]; then
    echo "ERROR: ${CREDS_FILE} not found." >&2
    echo "Run \`claude setup-token\` (or \`claude /login\`) first to populate it." >&2
    exit 1
fi

# Validate the file looks like a claudeAiOauth payload
if ! python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert 'claudeAiOauth' in d and 'accessToken' in d['claudeAiOauth'] and 'refreshToken' in d['claudeAiOauth']" "${CREDS_FILE}" 2>/dev/null; then
    echo "ERROR: ${CREDS_FILE} is missing claudeAiOauth.{accessToken,refreshToken}" >&2
    echo "Is this really a claude /login result? Try \`claude auth status\` to verify." >&2
    exit 1
fi

REMOTE_PATH="gs://${BUCKET}/${PREFIX}/${ACCOUNT_ID}.json"
echo "Uploading ${CREDS_FILE} -> ${REMOTE_PATH}"
gsutil cp "${CREDS_FILE}" "${REMOTE_PATH}"

EXP_MS=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['claudeAiOauth']['expiresAt'])" "${CREDS_FILE}")
EXP_HUMAN=$(python3 -c "import datetime,sys; print(datetime.datetime.fromtimestamp(int(sys.argv[1])/1000, datetime.timezone.utc).isoformat())" "${EXP_MS}")
echo "Done. Access token expires at: ${EXP_HUMAN}"
echo
echo "All VMs running orchestrator will pull within 5 min via GCSCredsPoller."
echo "To force-pull on a specific VM now:"
echo "  curl -X POST https://api-vm-N.agent-orchestrator.odum-research.com/api/accounts/${ACCOUNT_ID}/sync-from-gcs \\"
echo "    -H 'Authorization: Bearer <orch-token>'"
