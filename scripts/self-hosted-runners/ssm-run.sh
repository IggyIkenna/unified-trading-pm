#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: the glue host is retired (B2/B3) or gains a normal inbound path
#
# ssm-run.sh — run a shell snippet on the glue/orchestrator VM and get its stdout, stderr and REAL
# exit code back. Reads the snippet from stdin.
#
# ┌─ WHY THIS EXISTS ──────────────────────────────────────────────────────────────────────────────┐
# │ The orchestrator VM has NO inbound SSH and no open :8765 — AWS SSM is the only way in. Every    │
# │ deploy/verify step of this epic went through this, ~30+ invocations. It is written down because │
# │ it encodes TWO gotchas that cost real time to find and that a fresh session would hit again.    │
# └────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# GOTCHA 1 — AWS-RunShellScript runs your snippet under /bin/sh (DASH), not bash.
#   Symptom: `set: Illegal option -o pipefail` on line 1, and every other bashism dies.
#   Fix: we prepend a `#!/bin/bash` shebang to the payload. Do not remove it.
#
# GOTCHA 2 — the snippet must travel as a JSON parameter FILE, not an inline --parameters string.
#   Inline quoting mangles anything with quotes/newlines/$ (i.e. every real script). We serialise
#   via python json.dump to a temp file and pass file://.
#
# GOTCHA 3 (a reporting one, but it bit twice) — `aws ssm get-command-invocation --query Status`
#   returns Success for a command that produced NO output if the payload was mangled to empty. Always
#   look at the actual stdout, not just status. This wrapper prints stdout and the ResponseCode, and
#   exits with the REAL remote exit code so `&&`/`||` work.
#
# NOTE ON PRIVILEGE: SSM runs as ROOT. That matters more than it looks — gcloud ADC is PER-USER and
# root on this box has NONE, so anything touching GCP must `sudo -u ubuntu`. See secret_access() in
# setup-glue-runners.sh for the same rule.
#
#   echo 'hostname; whoami' | ./ssm-run.sh
#   cat <<'EOF' | ./ssm-run.sh
#   set -euo pipefail
#   systemctl --no-pager list-units 'github-glue-runner@*'
#   EOF
#
# Env: SSM_INSTANCE (default: the orchestrator VM) · SSM_REGION (default ap-northeast-1)
set -uo pipefail

INSTANCE="${SSM_INSTANCE:-i-0c9b283b31d6b5ca7}" # agent-orchestrator-vm-1 — NOT i-0dd9812a96cdda5dc (the human box)
REGION="${SSM_REGION:-ap-northeast-1}"

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

# Force bash (gotcha 1) + serialise safely (gotcha 2).
python3 -c 'import json,sys; json.dump({"commands":["#!/bin/bash\n"+sys.stdin.read()]}, open(sys.argv[1],"w"))' \
  "${TMP}/p.json"

CID="$(aws ssm send-command --region "${REGION}" --instance-ids "${INSTANCE}" \
  --document-name AWS-RunShellScript --parameters "file://${TMP}/p.json" \
  --query 'Command.CommandId' --output text)" || { echo "ssm-run: send-command failed" >&2; exit 90; }

for _ in $(seq 1 150); do
  ST="$(aws ssm get-command-invocation --region "${REGION}" --command-id "${CID}" \
        --instance-id "${INSTANCE}" --query 'Status' --output text 2>/dev/null || echo Pending)"
  case "${ST}" in Success | Failed | Cancelled | TimedOut) break ;; esac
  sleep 2
done

J="$(aws ssm get-command-invocation --region "${REGION}" --command-id "${CID}" \
     --instance-id "${INSTANCE}" --output json)"
python3 - "$J" <<'PY'
import json, sys
d = json.loads(sys.argv[1])
sys.stdout.write(d.get("StandardOutputContent", ""))
err = d.get("StandardErrorContent", "")
if err.strip():
    sys.stderr.write("--- stderr ---\n" + err)
PY
RC="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("ResponseCode", 91))' "$J")"
echo "[ssm-run] status=${ST} exit=${RC}" >&2
exit "${RC}"
