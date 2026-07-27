---
doc_type: issue
title: Orchestrator/glue-runner VM's AWS IAM role is account-wide over-privileged AND self-escalating
summary: >-
  Investigating whether quality-gates-v2 (the real pull_request-triggered pytest suite) could safely move to self-hosted
  runners, verified the ACTUAL AWS identity the self-hosted glue-runner host already carries via EC2 IMDS
  (arn:aws:sts::427895769566:assumed-role/uts-orchestrator-epic-role — the same role the glue-runner setup script locks
  its GCP WIF federation to). It is far broader than the deliberately-scoped GCP-side credential path
  (glue-runner-gh-pat SA, secretmanager.secretAccessor on GH_PAT only) suggested: attached AWS-managed policies grant
  account-wide AmazonS3FullAccess / AmazonRDSFullAccess / AmazonECS_FullAccess / AmazonDynamoDBFullAccess; an inline
  policy (uts-orchestrator-epic-policy) grants secretsmanager:GetSecretValue directly on GH_PAT, ORCHESTRATOR_ENV_LOCAL,
  and ORCHESTRATOR_VM_GCP_ADC; and a second inline policy (self-manage-own-policies) grants
  iam:AttachRolePolicy/PutRolePolicy/DetachRolePolicy on the role's OWN ARN -- a privilege-escalation primitive (any
  process on the box can attach AdministratorAccess to itself). This is reachable via plain EC2 IMDS by ANY process on
  the host, not gated by which GCP credential a given job chooses to use -- so it is the REAL ambient blast radius for
  every self-hosted CI job already running there today, not a hypothetical future risk.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
created: 2026-07-27
assigned_vm: NA
parent_epic: deployment_and_user_management_master
resolved_by:
locked_by:
source: [operator question "whats the tradeoff for quality gates v2" -- verifying blast radius before answering]
related:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
tags: [security, iam, aws, self-hosted-runner, privilege-escalation, orchestrator-vm]
priority: P0
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# Orchestrator/glue-runner VM's AWS IAM role is account-wide over-privileged AND self-escalating

## What was verified (not inferred)

Live `aws iam` calls against account `427895769566` (2026-07-27):

```
aws iam list-attached-role-policies --role-name uts-orchestrator-epic-role
```

Attached AWS-managed policies:

- `AmazonS3FullAccess` — full read/write/delete on **every S3 bucket in the account**
- `AmazonRDSFullAccess` — full control over every RDS instance
- `AmazonECS_FullAccess` — full control over every ECS cluster/service/task definition
- `AmazonDynamoDBFullAccess` — full read/write/delete on every DynamoDB table
- `AmazonEC2ContainerRegistryPowerUser` — push/pull to any ECR repo
- `uts-orchestrator-epic-policy` (customer-managed, v2) — see below

Inline policies (`aws iam list-role-policies` + `get-role-policy` per name):

- **`uts-orchestrator-epic-policy`**: `secretsmanager:GetSecretValue` directly on
  `arn:aws:secretsmanager:ap-northeast-1:427895769566:secret:GH_PAT*`, `...:secret:ORCHESTRATOR_ENV_LOCAL*`,
  `...:secret:ORCHESTRATOR_VM_GCP_ADC*` — i.e. the workflow-capable GitHub PAT, the orchestrator's own local env
  secrets, and **the orchestrator VM's GCP ADC credential** (which may itself carry broader GCP access than the
  narrowly-scoped `glue-runner-gh-pat` SA built specifically for CI). Plus S3 read/write on the orchestrator
  creds/events/state buckets and `ssm:*Session*` (SSM Session Manager control/data channels).
- **`orchestrator-state-s3-rw`**: read/write/list on `uts-orchestrator-state-427895769566` (the orchestrator's own
  operating state).
- **`self-manage-own-policies`**: `iam:GetRolePolicy` / `ListRolePolicies` / `ListAttachedRolePolicies` /
  **`PutRolePolicy`** / **`AttachRolePolicy`** / **`DetachRolePolicy`** scoped to
  `arn:aws:iam::427895769566:role/uts-orchestrator-epic-role` itself — **this role can grant itself MORE permissions at
  runtime**, up to and including attaching `AdministratorAccess` to itself. There is no meaningful ceiling on this
  role's effective privilege; whatever is attached today is a floor, not a cap.

## Why this matters right now (not just for a hypothetical quality-gates-v2 move)

`scripts/self-hosted-runners/setup-glue-runners.sh` locks its GCP Workload Identity Federation to
`arn:aws:sts::427895769566:assumed-role/uts-orchestrator-epic-role` — i.e. **this is the identity of the same host the
self-hosted glue-runner CI jobs already execute on**. The GCP-side scoping built for those jobs
(`glue-runner-gh-pat@central-element-323112.iam.gserviceaccount.com`, `secretmanager.secretAccessor` on `GH_PAT` only)
is real and was clearly a deliberate least-privilege design — but **it only narrows the GCP side**. EC2 Instance
Metadata Service (IMDS) credential retrieval for the AWS role is available to **any process on the box**, independent of
which GCP credential a job's own steps choose to use. So the actual ambient blast radius for anything running on this
host today is the full list above, not the narrower GCP SA.

This was surfaced while answering an operator question about whether `quality-gates-v2` (the real pytest suite,
currently kept on GitHub-hosted runners specifically because self-hosted here carries ambient credentials) could safely
move to self-hosted — the honest answer turned out to require actually measuring what "ambient credentials" means on
this specific host, and it is far more severe than a general "some cloud access" framing would suggest.

## Not yet done (deliberately, pending operator triage)

- Did not check what `orchestrator-state-s3-rw` / `uts-orchestrator-events-427895769566` / the accounts/config buckets
  actually contain (could hold further sensitive material — client credentials, wallet-adjacent config, etc. — out of
  scope for this pass, flagged not investigated).
- Did not check whether this role is scoped down elsewhere (e.g. a permissions boundary) that would cap the practical
  effect of `self-manage-own-policies` — `aws iam get-role` did not show a `PermissionsBoundary` field in the sampled
  output, suggesting none is set, but this was not exhaustively re-verified across all IAM path types (session policies,
  SCPs if this account sits under an AWS Organization).
- Did not check whether `AmazonS3FullAccess` reaches production trading-data buckets specifically (vs. only
  infra/CI-adjacent ones) — full access means it structurally could, but which buckets exist and what's in them was not
  enumerated here.

## Operator decision — ✅ DECIDED 2026-07-27: ACCEPTED AS KNOWN RISK, do not remediate

Operator ruling: these permissions are genuinely load-bearing — the same VM uses this identity for other legitimate
end-of-day operations (deploying, deleting data) that need this breadth. **Do not narrow the IAM policy; do not re-raise
this as an open remediation item.** The exposure described above is real and known, not a bug to fix.

This changes the calculus for the adjacent `quality-gates-v2` self-hosting question
(`github_actions_operator_gated_followups_2026_07_17.md`): since the IAM scope is staying as-is, moving the real test
suite to this host means accepting the full blast radius above (not a narrower, post-remediation version of it) as the
standing cost of that move — see that doc's operator-decision note for the still-open call on whether to proceed there.

## Recommendation (SUPERSEDED by the operator decision above — kept for reference, do not action)

~~1. Remove `self-manage-own-policies` entirely if nothing legitimately needs it.~~ ~~2. Replace the four `*FullAccess`
AWS-managed policies with scoped, resource-level policies.~~ ~~3. Re-run this `aws iam` verification after any change.~~

These three steps are what a remediation pass WOULD look like if the operator ever revisits this — kept as reference,
not as an active todo. Do not action them; the operator has ruled the current scope stays.
