#!/usr/bin/env bash
# load-gh-token.sh — export a WORKFLOW-CAPABLE GH_TOKEN for gh + git in EVERY context.
#
# Why this exists (codified 2026-06-01): the gh CLI keyring login token (`gho_…`) carries
# scopes `repo, read:org, gist, admin:public_key` — it has **NO `workflow` scope**, so any
# gh-API / HTTPS push that creates or updates `.github/workflows/*.yml` is silently refused
# ("refusing to allow … without `workflow` scope"). That blocked a 7-repo CI v1→v2 migration.
# The `GH_PAT` secret (Secret Manager / AWS SM) IS workflow-capable (fine-grained PAT with
# "Workflows: read/write"). This helper makes that PAT the active GH_TOKEN so gh + git never
# stop on a permission gap — on slots, the main worktree, and orchestrator VM workers alike.
#
# Usage (idempotent; safe to source repeatedly):
#   source unified-trading-pm/scripts/workspace/load-gh-token.sh
# After sourcing, GH_TOKEN + GITHUB_TOKEN are exported (env beats the keyring for both gh + git).
#
# SSH note: git push over SSH (a user key) is NOT subject to the workflow-scope restriction, so
# ssh-protocol slots can already push workflow files. This helper covers the gh-API / HTTPS path
# (gh workflow run, gh api contents PUT, https clones/pushes) which IS restricted.

_uts_load_gh_token() {
  # Respect an already-exported workflow-capable token.
  if [ -n "${GH_TOKEN:-}" ]; then
    [ -z "${GITHUB_TOKEN:-}" ] && export GITHUB_TOKEN="${GH_TOKEN}"
    return 0
  fi

  local _pat=""
  # GCP Secret Manager (asia/central project) first, then AWS Secrets Manager (fleet).
  if command -v gcloud >/dev/null 2>&1; then
    _pat="$(gcloud secrets versions access latest --secret=GH_PAT \
      --project="${GCP_PROJECT_ID:-central-element-323112}" 2>/dev/null || true)"
  fi
  if [ -z "${_pat}" ] && command -v aws >/dev/null 2>&1; then
    _pat="$(aws secretsmanager get-secret-value --secret-id GH_PAT \
      --query SecretString --output text 2>/dev/null || true)"
  fi

  if [ -n "${_pat}" ]; then
    export GH_TOKEN="${_pat}"
    export GITHUB_TOKEN="${_pat}"
    unset _pat
    return 0
  fi

  echo "WARN [load-gh-token] GH_PAT unavailable from GCP/AWS Secret Manager — gh/git will fall" >&2
  echo "     back to the keyring login token, which LACKS 'workflow' scope. Workflow-file edits" >&2
  echo "     via gh-API/HTTPS will be refused. Fix: grant SM access OR set GH_TOKEN manually." >&2
  return 1
}

_uts_load_gh_token

# Optional self-check: confirm the active token can write workflows (non-mutating probe).
# Enable with UTS_GH_TOKEN_VERIFY=1 (skipped by default to keep shell init fast).
if [ "${UTS_GH_TOKEN_VERIFY:-0}" = "1" ] && [ -n "${GH_TOKEN:-}" ]; then
  _code="$(curl -s -o /dev/null -w '%{http_code}' -X PUT \
    -H "Authorization: token ${GH_TOKEN}" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/IggyIkenna/unified-trading-pm/contents/.github/workflows/quality-gates-v2.yml" \
    -d '{"message":"probe","content":"eA==","sha":"0000000000000000000000000000000000000000","branch":"live-defi-rollout"}' 2>/dev/null)"
  # 409/422 = permission OK (failed only at the bogus sha); 403 = missing Workflows:write.
  case "${_code}" in
    409|422) echo "[load-gh-token] GH_TOKEN is workflow-capable ✓" >&2 ;;
    403)     echo "[load-gh-token] ⚠️  GH_TOKEN LACKS Workflows:write (HTTP 403) — workflow edits will block" >&2 ;;
    *)       echo "[load-gh-token] workflow-capability probe inconclusive (HTTP ${_code})" >&2 ;;
  esac
  unset _code
fi
