#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# push_creds_to_gcs.sh — push r3 setup-token env files to GCS so every VM
# can pull them during bootstrap (bootstrap_vm.sh step 5a).
#
# r3 auth: each account authenticates via a long-lived setup-token stored in
# ~/.claude-accounts/<id>.env (CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...).
# VMs fetch these from gs://${PROJECT_ID}-orchestrator-creds/accounts/*.env
# at boot time.
#
# Usage:
#   bash push_creds_to_gcs.sh sub-a-ikenna            # push one account
#   bash push_creds_to_gcs.sh --all                   # push all env files
#   bash push_creds_to_gcs.sh --all --dry-run         # print what would happen
#
# Env:
#   PROJECT_ID  — GCP project (default: central-element-323112)
#
# Prereqs:
#   - gsutil on PATH + ADC configured
#   - ~/.claude-accounts/<id>.env must contain CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-central-element-323112}"
ACCOUNTS_DIR="${HOME}/.claude-accounts"
DRY_RUN=false
PUSH_ALL=false
ACCOUNT_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)      PUSH_ALL=true; shift ;;
    --dry-run)  DRY_RUN=true; shift ;;
    --project)  PROJECT_ID="$2"; shift 2 ;;
    -*)         echo "Unknown flag: $1" >&2; exit 2 ;;
    *)          ACCOUNT_ID="$1"; shift ;;
  esac
done

if ! $PUSH_ALL && [[ -z "${ACCOUNT_ID}" ]]; then
  echo "Usage: $0 <account_id> | --all [--dry-run]" >&2
  echo "Example: $0 sub-a-ikenna" >&2
  exit 2
fi

BUCKET="gs://${PROJECT_ID}-orchestrator-creds"
PREFIX="accounts"

_push_one() {
  local id="$1"
  local env_file="${ACCOUNTS_DIR}/${id}.env"

  if [[ ! -f "${env_file}" ]]; then
    echo "SKIP ${id}: ${env_file} not found" >&2
    return 0
  fi

  # Validate it has a valid setup-token
  if ! grep -q "CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-" "${env_file}" 2>/dev/null; then
    echo "ERROR ${id}: ${env_file} missing CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-*" >&2
    return 1
  fi

  local remote="${BUCKET}/${PREFIX}/${id}.env"
  if $DRY_RUN; then
    echo "[dry-run] would push ${env_file} → ${remote}"
  else
    gsutil cp "${env_file}" "${remote}"
    echo "Pushed ${id} → ${remote}"
  fi
}

if $PUSH_ALL; then
  if [[ ! -d "${ACCOUNTS_DIR}" ]]; then
    echo "ERROR: ${ACCOUNTS_DIR} does not exist" >&2
    exit 1
  fi
  shopt -s nullglob
  ENV_FILES=("${ACCOUNTS_DIR}"/*.env)
  shopt -u nullglob
  if [[ ${#ENV_FILES[@]} -eq 0 ]]; then
    echo "No *.env files found in ${ACCOUNTS_DIR}" >&2
    exit 1
  fi
  for f in "${ENV_FILES[@]}"; do
    id="$(basename "${f}" .env)"
    _push_one "${id}"
  done
  echo ""
  echo "Done. All VMs will pull on next bootstrap or manual sync."
else
  _push_one "${ACCOUNT_ID}"
  echo ""
  echo "Done."
fi
