#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: the reporter stops needing a bearer token off-VM (see the durable-fix
#              todo in /plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md)
#
# remint-orch-token.sh -- re-mint an expired ~/.orch_token on an OFF-VM host.
#
# WHY THIS EXISTS (2026-08-06, third occurrence of the same outage class):
# slot-git-status-report.sh POSTs each slot's git-status snapshot to the orchestrator.
# On the orchestrator VM it now prefers loopback and needs no token at all, but an
# off-VM host (an operator laptop like `hk`) has no local :8765 -- the public URL plus
# an operator JWT is its ONLY path, and that JWT expires every 30 days
# (auth.DEFAULT_TOKEN_TTL_SECONDS). When it lapses, EVERY slot on that host 401s every
# 5 minutes and the AO Fleet tab silently freezes at the last good report -- stale data
# presented as current, which is worse than an error, since ff-pull keeps working and
# nothing else looks wrong. Measured on `hk` 2026-08-06: 16 slots frozen for ~35h at
# exactly the token's `exp`. Re-deriving this mint procedure from scratch each time is
# what this script exists to stop.
#
# WHAT IT DOES: asks the orchestrator VM (over AWS SSM, CloudTrail-audited) to sign a
# fresh operator JWT with the secret it already holds, verifies the result against the
# LIVE public API, and only then replaces the local token file.
#
# TRAPS -- both of these produce a token that looks perfect and 401s. Do not re-learn:
#
#   1. THE SECRET IS NOT IN THE SHELL. `sudo -u ubuntu python -c "auth.issue_token(...)"`
#      mints happily and the token is well-formed -- but auth._load_secret() falls back to
#      secrets.token_urlsafe(32) when neither ORCHESTRATOR_JWT_SECRET nor
#      ORCHESTRATOR_JWT_SECRET_GCS is set, and those live in the SYSTEMD unit /
#      .env.local, not in ubuntu's profile. The fallback only WARNS (on stderr) and
#      returns an ephemeral per-process secret. Diagnostic: mint twice and hash
#      auth._jwt_secret -- a changing fingerprint means you are on the fallback path.
#      Hence the `set -a; . ./.env.local` below. Do NOT "fix" this by exporting
#      ORCHESTRATOR_JWT_SECRET_GCS instead: the GCS read needs ADC that the sudo shell
#      also lacks, so it silently fails the same way. .env.local sets the literal, and
#      literal-env wins first in _load_secret().
#
#   2. `--output text` ENDS WITH A BLANK LINE. Taking `tail -1` of StandardOutputContent
#      yields an EMPTY token, so curl sends a bare `Bearer ` and the server answers with
#      the same "invalid or expired token" a genuine signing failure gives. Use head -1.
#
# The token is written straight to the output file and NEVER echoed to stdout.
# NOTE: the JWT does transit the SSM command-invocation record, which AWS retains and
# anyone with ssm:GetCommandInvocation on the account can read. That is not a privilege
# escalation (running this at all requires ssm:SendCommand, which is strictly stronger),
# but if the account's SSM readers are ever wider than its operators, mint from the VM
# console instead.
#
# Usage: bash scripts/dev/remint-orch-token.sh [--user harsh] [--out ~/.orch_token]
set -euo pipefail

INSTANCE_ID="${AO_INSTANCE_ID:-i-0c9b283b31d6b5ca7}"
REGION="${AO_REGION:-ap-northeast-1}"
AO_DIR="${AO_DIR:-/home/ubuntu/unified-trading-system-repos/agent-orchestrator}"
ORCH_URL="${ORCH_URL:-https://api.agent-orchestrator.odum-research.com}"
USERNAME="harsh"
OUT="${HOME}/.orch_token"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --user) USERNAME="$2"; shift 2;;
        --out)  OUT="$2"; shift 2;;
        -h|--help) sed -n '2,50p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

for bin in aws jq curl; do
    command -v "${bin}" >/dev/null || { echo "missing required binary: ${bin}" >&2; exit 2; }
done

# Ship the python over base64+stdin so no layer of quoting survives the SSM JSON hop.
PY_B64="$(printf '%s' "from server import auth
t, _ = auth.issue_token(\"${USERNAME}\", role=\"operator\")
print(t)" | base64 -w0)"
REMOTE="sudo -u ubuntu bash -lc 'cd ${AO_DIR} && set -a && . ./.env.local && set +a && echo ${PY_B64} | base64 -d | .venv/bin/python -'"

PARAMS="$(mktemp)"; TMPTOK="$(mktemp)"
trap 'rm -f "${PARAMS}" "${TMPTOK}"' EXIT
jq -n --arg c "${REMOTE}" '{commands:[$c]}' > "${PARAMS}"

echo "minting a ${USERNAME}/operator JWT on ${INSTANCE_ID} (${REGION}) via SSM..."
CMD_ID="$(aws ssm send-command \
    --instance-ids "${INSTANCE_ID}" --region "${REGION}" \
    --document-name "AWS-RunShellScript" \
    --parameters "file://${PARAMS}" \
    --query 'Command.CommandId' --output text)"

STATUS="Pending"
for _ in $(seq 1 40); do
    STATUS="$(aws ssm get-command-invocation --command-id "${CMD_ID}" \
        --instance-id "${INSTANCE_ID}" --region "${REGION}" \
        --query 'Status' --output text 2>/dev/null || echo Pending)"
    [[ "${STATUS}" == "Success" || "${STATUS}" == "Failed" ]] && break
    sleep 2
done

if [[ "${STATUS}" != "Success" ]]; then
    echo "MINT FAILED (${STATUS}), command-id ${CMD_ID}:" >&2
    aws ssm get-command-invocation --command-id "${CMD_ID}" \
        --instance-id "${INSTANCE_ID}" --region "${REGION}" \
        --query 'StandardErrorContent' --output text >&2
    exit 1
fi

umask 077
# head -1, not tail -1 -- see TRAP 2 above.
aws ssm get-command-invocation --command-id "${CMD_ID}" \
    --instance-id "${INSTANCE_ID}" --region "${REGION}" \
    --query 'StandardOutputContent' --output text | tr -d '\r' | head -1 | tr -d '\n' > "${TMPTOK}"

# TRAP 3 (2026-08-10): `wc -c` pads its output with leading spaces on BSD/macOS
# ("       2"), so this comparison failed against the literal "2" for a PERFECTLY VALID
# token and the script rejected every mint attempted on an operator laptop -- the exact
# host class it exists for (measured: the mint itself returned a well-formed JWT every
# time; only this check was wrong, so the third occurrence of the token-expiry outage
# still needed a hand-rolled mint). `tr -d ' '` makes it portable; GNU wc emits no
# padding, so this is a no-op on the VM.
if [[ ! -s "${TMPTOK}" || "$(tr -cd '.' < "${TMPTOK}" | wc -c | tr -d ' ')" != "2" ]]; then
    echo "minted output is not a JWT (empty or wrong segment count) -- ${OUT} untouched" >&2
    exit 1
fi

# Prove it against the LIVE server BEFORE overwriting the operator's token file, so a
# bad mint can never take down a host that was merely about to expire.
CODE="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer $(cat "${TMPTOK}")" "${ORCH_URL}/api/state")"
if [[ "${CODE}" != "200" ]]; then
    echo "minted token REJECTED by ${ORCH_URL}/api/state (HTTP ${CODE}) -- ${OUT} untouched" >&2
    exit 1
fi

cp "${TMPTOK}" "${OUT}"
chmod 600 "${OUT}"
# One python hop, not a `base64 -d` pipeline: base64 exits non-zero on the JWT's
# stripped padding, and `set -o pipefail` then turns a perfectly good decode into a
# failure -- which under `|| echo unknown` printed BOTH the date and "unknown".
EXP="$(python3 -c '
import base64, datetime, json, sys
seg = open(sys.argv[1]).read().split(".")[1]
claims = json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))
print(datetime.datetime.fromtimestamp(claims["exp"], datetime.timezone.utc).isoformat())
' "${OUT}" 2>/dev/null || echo unknown)"
echo "OK -- ${OUT} replaced (/api/state 200). Expires ${EXP}; re-run this before then."
echo "Confirm recovery: bash scripts/dev/slot-git-status-report.sh   # every slot should print [ok]"
