#!/usr/bin/env bash
# rollout-agent-symlinks-fleet.sh — make the root CLAUDE.md + skills symlinks live on EVERY VM.
#
# WHAT IT DOES (per VM, via AWS SSM SendCommand → AWS-RunShellScript):
#   1. FF-pull unified-trading-pm to origin/live-defi-rollout (gets the regen helper + fixed scripts)
#   2. Refresh the INSTALLED /usr/local/bin/pm-pull-ff.sh to the self-regen version (so future
#      5-min pm-pull advances keep the symlinks fresh on their own)
#   3. Run scripts/dev/regen-agent-symlinks.sh ONCE → lays down, for the main workspace root AND
#      every slot root (.tabs/<N>/): top-level CLAUDE.md → PM/cursor-configs/CLAUDE.md + .claude/skills/*
#
#   It does NOT re-run install_pm_pull.sh, so it does NOT restart orchestrator.service — no blip on
#   the central VM. This is the light, non-disruptive payload.
#
# WHY A SEPARATE SCRIPT: pm-pull-ff.sh only fast-forwards git; it never executed setup, so the
# symlinks added in PM@cb52027c2 / @d64d64996 reach a running VM's git tree but don't become live
# links until a quality-gates run (QG post-gate hook) or this rollout fires. This makes it immediate.
#
# WHERE TO RUN: ANY identity that can call ssm:SendCommand in the fleet region. Two work today
# (both verified 2026-06-16): (1) the CENTRAL / orchestrator VM (i-0c9b283b31d6b5ca7) via its
# uts-orchestrator-epic instance profile; (2) an OPERATOR LAPTOP whose ~/.aws default is the admin
# IAM user `admin_od` (arn:aws:iam::427895769566:user/admin_od) — full ssm:SendCommand to the live
# fleet, so the rollout runs straight from the laptop, no need to hop to the central VM. The fenced
# slot/worker role (IAM user `ikenna-worker`) is intentionally denied SSM and CANNOT run this. The
# preflight identity check below fails fast with guidance if the current identity lacks SSM.
#
# TARGETS: derived from orchestrator_vm_registry.yaml (the SSOT) at runtime — no hardcoded list to
# drift. Self (the VM running this) is skipped. Instances not registered/online in SSM are reported
# UNREACHABLE and skipped, never fatal.
#
# USAGE:
#   PREFLIGHT=1 bash scripts/orchestrator/rollout-agent-symlinks-fleet.sh   # read-only audit, no changes
#   bash scripts/orchestrator/rollout-agent-symlinks-fleet.sh               # real rollout
#   ONLY="i-05805eb07fdf180b6 i-02294132088f23e50" bash ...                 # restrict to specific ids
#
# Env: AWS_REGION (default ap-northeast-1) · SSM_WAIT_S (per-VM poll budget, default 150)
set -uo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
SSM_WAIT_S="${SSM_WAIT_S:-150}"
PREFLIGHT="${PREFLIGHT:-0}"
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SELF_DIR}/../.." && pwd)"
REGISTRY="${PM_DIR}/orchestrator_vm_registry.yaml"
PM_REMOTE_PATH="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"

RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; BLU='\033[0;34m'; NC='\033[0m'
ok(){ echo -e "${GRN}✅ $*${NC}"; }; warn(){ echo -e "${YLW}⚠️  $*${NC}"; }; err(){ echo -e "${RED}❌ $*${NC}"; }; info(){ echo -e "${BLU}ℹ️  $*${NC}"; }

command -v aws >/dev/null || { err "aws CLI not found"; exit 1; }
[ -f "$REGISTRY" ] || { err "registry not found: $REGISTRY"; exit 1; }

# Preflight identity check — fail fast with a clear message if this host lacks SSM (e.g. ikenna-worker).
if ! aws ssm describe-instance-information --region "$REGION" --max-results 5 >/dev/null 2>&1; then
    err "This identity cannot call ssm:DescribeInstanceInformation in $REGION."
    info "Run this from the CENTRAL VM (i-0c9b283b31d6b5ca7) which has the uts-orchestrator-epic instance profile."
    aws sts get-caller-identity --query Arn --output text 2>/dev/null | sed 's/^/  current identity: /'
    exit 1
fi

# Self instance-id (IMDSv2) so we skip ourselves. --connect-timeout so this fails fast (not ~150s)
# when run off-EC2 (e.g. the operator laptop, which has no metadata endpoint) — SELF_ID stays empty.
SELF_ID=""
_tok=$(curl -s --connect-timeout 1 -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" 2>/dev/null || true)
[ -n "$_tok" ] && SELF_ID=$(curl -s --connect-timeout 1 -H "X-aws-ec2-metadata-token: $_tok" "http://169.254.169.254/latest/meta-data/instance-id" 2>/dev/null || true)

# Targets: all aws_instance_id from the registry (dependency-free extract), minus self, minus ONLY filter.
ALL_IDS=$(awk '/aws_instance_id:/ {print $2}' "$REGISTRY" | grep -oE 'i-[0-9a-f]{8,}' | sort -u)
ONLY="${ONLY:-}"

# ── Remote payload (heredoc body sent verbatim to AWS-RunShellScript) ──────────────────────────────
read -r -d '' PAYLOAD_APPLY <<REMOTE || true
set -e
PM=${PM_REMOTE_PATH}
WS=\$(dirname "\$PM")
cd "\$PM"
sudo -u ubuntu git fetch -q origin live-defi-rollout
sudo -u ubuntu git merge --ff-only -q origin/live-defi-rollout
cp scripts/dev/pm-pull-ff.sh /usr/local/bin/pm-pull-ff.sh && chmod +x /usr/local/bin/pm-pull-ff.sh
sudo -u ubuntu bash scripts/dev/regen-agent-symlinks.sh
echo "PM=\$(git rev-parse --short HEAD) host=\$(hostname)"
for r in "\$WS" "\$WS"/.tabs/*/; do [ -d "\$r" ] || continue; printf '  %s CLAUDE.md=%s\n' "\${r%/}" "\$([ -e "\$r/CLAUDE.md" ] && echo OK || echo MISSING)"; done
REMOTE

read -r -d '' PAYLOAD_PREFLIGHT <<REMOTE || true
PM=${PM_REMOTE_PATH}
WS=\$(dirname "\$PM")
[ -d "\$PM" ] || { echo "PM MISSING at \$PM"; exit 1; }
echo "PM=\$(cd "\$PM" && git rev-parse --short HEAD) host=\$(hostname) installed-pull=\$([ -f /usr/local/bin/pm-pull-ff.sh ] && grep -q regen-agent-symlinks /usr/local/bin/pm-pull-ff.sh && echo self-regen || echo OLD)"
for r in "\$WS" "\$WS"/.tabs/*/; do [ -d "\$r" ] || continue; printf '  %s CLAUDE.md=%s skills=%s\n' "\${r%/}" "\$([ -e "\$r/CLAUDE.md" ] && echo OK || echo MISSING)" "\$([ -e "\$r/.claude/skills/autonomous" ] && echo OK || echo MISSING)"; done
REMOTE

if [ "$PREFLIGHT" = "1" ]; then PAYLOAD="$PAYLOAD_PREFLIGHT"; MODE="PREFLIGHT (read-only)"; else PAYLOAD="$PAYLOAD_APPLY"; MODE="APPLY"; fi

# Encode the multi-line payload as proper JSON. The `--parameters commands=<shorthand>` form's list
# parser breaks on the payload's embedded newlines → every send-command failed silently (verified
# 2026-06-16: describe works + send works with JSON, but shorthand+multiline does not). Build
# {"commands":["<payload>"]} and pass it as a --parameters JSON string instead.
command -v python3 >/dev/null || { err "python3 required to JSON-encode the SSM payload"; exit 1; }
PARAMS_JSON="$(printf '%s' "$PAYLOAD" | python3 -c 'import json,sys; print(json.dumps({"commands":[sys.stdin.read()]}))')"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  rollout-agent-symlinks-fleet — mode: $MODE  region: $REGION"
echo "  self: ${SELF_ID:-unknown (not on EC2?)}  | targets from: $(basename "$REGISTRY")"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PASS=0; FAIL=0; SKIP=0
for iid in $ALL_IDS; do
    [ -n "$ONLY" ] && ! grep -qw "$iid" <<<"$ONLY" && continue
    if [ "$iid" = "$SELF_ID" ]; then info "$iid: self — skipped (run locally instead)"; SKIP=$((SKIP+1)); continue; fi

    cid=$(aws ssm send-command --region "$REGION" --instance-ids "$iid" \
        --document-name "AWS-RunShellScript" \
        --comment "rollout agent root symlinks ($MODE)" \
        --parameters "$PARAMS_JSON" \
        --query 'Command.CommandId' --output text 2>/tmp/ssm_send_err) || {
            warn "$iid: send failed — $(head -1 /tmp/ssm_send_err) (UNREACHABLE/not in SSM?)"; SKIP=$((SKIP+1)); continue; }

    # Poll until terminal or budget exhausted.
    status="Pending"; waited=0
    while [ $waited -lt "$SSM_WAIT_S" ]; do
        sleep 5; waited=$((waited+5))
        status=$(aws ssm get-command-invocation --region "$REGION" --command-id "$cid" --instance-id "$iid" \
            --query 'Status' --output text 2>/dev/null || echo "Pending")
        case "$status" in Success|Failed|Cancelled|TimedOut) break;; esac
    done

    out=$(aws ssm get-command-invocation --region "$REGION" --command-id "$cid" --instance-id "$iid" \
        --query 'StandardOutputContent' --output text 2>/dev/null || true)
    errout=$(aws ssm get-command-invocation --region "$REGION" --command-id "$cid" --instance-id "$iid" \
        --query 'StandardErrorContent' --output text 2>/dev/null || true)

    if [ "$status" = "Success" ]; then
        ok "$iid: $status"; PASS=$((PASS+1))
    else
        err "$iid: $status"; FAIL=$((FAIL+1))
    fi
    [ -n "$out" ]    && printf '%s\n' "$out"    | sed 's/^/      /'
    [ -n "$errout" ] && printf '%s\n' "$errout" | sed 's/^/      [stderr] /'
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  done — ✅ $PASS  ❌ $FAIL  ⏭ $SKIP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
[ "$FAIL" -eq 0 ]
