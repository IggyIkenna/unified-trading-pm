---
doc_type: issue
title: >-
  escalation_queue_reconciler's Step-1 SSM check is blocked — the only AWS identity available in a worker session
  (ikenna-worker) lacks ssm:SendCommand on the orchestrator instance
summary: >-
  On this role's first observed live dispatch (2026-08-08, slot 9, dispatch agt-c5db55 — the role was only built
  2026-08-07), `/escalation-queue-reconcile` Step 1's `aws ssm send-command` against i-0c9b283b31d6b5ca7 failed:
  `AccessDeniedException` for `arn:aws:iam::427895769566:user/ikenna-worker`. `ikenna-worker` is the ONLY AWS identity
  available in this worker session (single `default` profile, no env-var override, IMDS unreachable — this worker does
  not run with an EC2 instance-role). Confirmed `ikenna-worker` cannot self-remediate and is NOT the codex-documented
  self-service identity: `iam:ListAttachedUserPolicies`/`ListUserPolicies`/`ListGroupsForUser` on itself all DENIED, and
  `sts:AssumeRole` into `uts-orchestrator-epic-role` (the actual self-service AWS identity per
  `orchestrator-cloud-identity-self-service.md`) is also DENIED. Precedent confirms `ikenna-worker`/`harsh-worker`
  permission gaps are operator-decision territory, not agent self-service: `billing-cost-observability.md`'s 2026-07-08
  note that `ce:GetCostAndUsage` was DENIED for the checked `ikenna-worker` identity (left as documented, non-blocking
  drift, never self-granted), and `operator_iam_permission_parity_2026_06_18.md` where the equivalent gaps for
  `harsh-worker` were closed only via an explicit human operator session with real IAM-admin power. Unlike those two
  precedents, THIS gap is fully blocking — Step 1 cannot run at all — and it is the SAME documented SSM pattern used by
  `check-ao-backlog-status.sh` (its own header says "Requires: AWS CLI configured against account 427895769566 with
  ssm:SendCommand + ssm:GetCommandInvocation. No orchestrator credentials needed.") and the `/check-agent-orchestrator`
  skill, so any other role/skill relying on this same pattern from a similarly-provisioned worker session is equally
  blocked. No fix attempted — self-granting IAM on a human-tied, deliberately narrow-scoped identity is out of this
  role's authorized scope (does not match either of the two self-service identities named in the codex SSOT).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [iam, aws, ssm, escalation_queue_reconciler, ikenna-worker, permission-gap, agent-orchestrator, self-service-identity]
related:
  [
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/05-infrastructure/billing-cost-observability.md,
    /plans/archive/issues/operator_iam_permission_parity_2026_06_18.md,
  ]
created: 2026-08-08
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: flat
last_updated: 2026-08-08
source:
  [
    "escalation_queue_reconciler dispatch agt-c5db55, slot 9, 2026-08-08 — first live Step-1 SSM attempt since the
    role's 2026-08-07 creation",
  ]
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    unified-trading-pm/cursor-configs/skills/escalation-queue-reconcile/SKILL.md,
    agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
---

# 2026-08-08: escalation_queue_reconciler blocked on missing ssm:SendCommand for ikenna-worker

## What happened

Dispatched as `escalation_queue_reconciler` (slot 9, `agt-c5db55`), I ran `/escalation-queue-reconcile` Step 1 exactly
as documented:

```bash
aws ssm send-command --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1 \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["curl -s -m 10 localhost:8765/api/escalations/active"]'
```

Result:

```
AccessDeniedException: User: arn:aws:iam::427895769566:user/ikenna-worker is not authorized to perform:
ssm:SendCommand on resource: arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7
```

## Verified before filing (so this isn't a "just retry" or a duplicate)

1. **No alternate credential path exists in this session**: `env | grep AWS_` empty, `~/.aws/credentials` has exactly
   one profile (`default` → `ikenna-worker`), and the EC2 metadata service is unreachable (`169.254.169.254` times out)
   — this worker session is not itself running with an instance-role identity to fall back to.
2. **`ikenna-worker` cannot self-remediate**: `iam:ListAttachedUserPolicies`, `iam:ListUserPolicies`,
   `iam:ListGroupsForUser` on itself all return `AccessDenied` — it cannot even read its own grants, let alone modify
   them. `sts:AssumeRole` into `uts-orchestrator-epic-role` — the actual AWS self-service identity per
   `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` — is also `AccessDenied`. So this is a
   genuinely different identity from the one the self-service carve-out covers, not a naming coincidence.
3. **Not a stale/already-fixed finding** (learned to check this from two OTHER stale messages in this same session's
   boot heartbeat — see Progress Log): grepped `plans/active/` + `plans/archive/` for prior reports of this exact gap,
   found none. `git log --grep` for the skill's own creation shows only the 2026-08-07 build commit (`34d99d599`) — no
   evidence this Step-1 SSM path has ever successfully executed from a worker session.
4. **Not blocking by design** (unlike the CE precedent) — `check-ao-backlog-status.sh`'s own header states this SSM call
   is the ONLY reachable path to the orchestrator's API (direct HTTP to the VM's public IP:8765 has no inbound rule, by
   design) — there is no fallback endpoint to try instead.

## Why I did not attempt a fix

`ikenna-worker` is not one of the two identities `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`
authorizes for agent self-service IAM grants (`unified-trading-sa` / `uts-orchestrator-epic-role`), and structurally
cannot self-grant regardless (no `iam:*` permissions on itself). Two precedents confirm gaps on this class of identity
are operator-decision territory: `billing-cost-observability.md` documents a DENIED `ikenna-worker` permission as
accepted drift rather than self-granting it, and `operator_iam_permission_parity_2026_06_18.md`'s equivalent
`harsh-worker` gaps were closed only via an explicit human operator session with real IAM-admin power (Owner +
`admin_od`), not by an agent.

## Recommended fix (least-privilege, mirrors the existing resource-scoped pattern)

Grant `ikenna-worker` (or a shared identity/group all worker sessions actually run as, if that differs from
`ikenna-worker` — worth confirming) an inline policy scoped to exactly this:

```json
{
  "Effect": "Allow",
  "Action": ["ssm:SendCommand", "ssm:GetCommandInvocation"],
  "Resource": [
    "arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7",
    "arn:aws:ssm:ap-northeast-1::document/AWS-RunShellScript"
  ]
}
```

This mirrors `uts-orchestrator-epic-role`'s existing pattern of a narrowly resource-scoped inline policy rather than a
broad managed policy. Re-verify live (not just IAM-policy-read-back) via the same Step 1 curl before closing.

## Todo

- [ ] [OPERATOR] P1. Grant `ikenna-worker` (confirm first whether other worker sessions run as a different/shared
      identity — if so, grant that one instead or additionally) the scoped `ssm:SendCommand` +
      `ssm:GetCommandInvocation` inline policy above, then re-verify LIVE via the Step 1 curl in
      `/escalation-queue-reconcile` (not just an IAM-policy read-back) before marking this resolved.

## Blast radius

Every future 3-hourly `escalation_queue_reconciler` dispatch will hit this same wall until fixed — the safety-net this
role exists to provide (catching a genuinely stuck escalation row) has had this blind spot since the role's creation
2026-08-07. Also blocks any other worker-session use of `check-ao-backlog-status.sh` / `/check-agent-orchestrator` from
an identically-provisioned session.

## Progress Log

- 2026-08-08 (slot 9, `agt-c5db55`): Filed. Step 1 could not execute; no fix attempted (operator-decision identity, see
  above). Two OTHER stale/already-resolved messages surfaced in this same session's boot heartbeat (a git-status nudge
  already clean, and a "direct instruction from main" exit_code=5 fix already shipped by slot-2 2026-08-07 — commit
  `27fd5779`) — both confirmed resolved and required no action, unrelated to this finding.
