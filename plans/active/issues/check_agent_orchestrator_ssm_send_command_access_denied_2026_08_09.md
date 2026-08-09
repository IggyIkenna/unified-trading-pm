---
doc_type: issue
title: >-
  ikenna-worker IAM identity lacks `ssm:SendCommand` on the central orchestrator VM — `/check-agent-orchestrator` fails
  AccessDenied
summary: >-
  The sanctioned read-only AO backlog/dispatch status check (`/check-agent-orchestrator` skill,
  `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh`) dispatches via AWS SSM `send-command` against
  the central orchestrator VM (`i-0c9b283b31d6b5ca7`, ap-northeast-1). From this slot-5 checkout, the call fails with
  `AccessDeniedException`: IAM user `arn:aws:iam::427895769566:user/ikenna-worker` is not authorized to perform
  `ssm:SendCommand` on that instance ARN — no identity-based policy allows it. This is the ONLY sanctioned way to check
  live backlog/dispatch state from a dev checkout (per CLAUDE.md +
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Checking live backlog/dispatch status") —
  with it blocked, this identity has no read path to live AO state at all.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, iam, ssm, aws, access-denied, infra]
related: []
created: "2026-08-09"
last_updated: "2026-08-09"
author: slot-5 (data_engineering)
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.02
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh,
  ]
source: >-
  Discovered 2026-08-09 (slot-5, data_engineering) while checking whether new work was queued for this slot after the
  original session task
  (`/plans/archive/2026_08/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md`) had
  already shipped and archived — asked to continue the in-flight task with nothing left in scope, so ran the sanctioned
  backlog-status check to look for new dispatch.
resolved_by:
locked_by:
---

# `ikenna-worker` lacks `ssm:SendCommand` — `/check-agent-orchestrator` AccessDenied

## What I found

Ran `bash agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` (no filter, fleet-wide summary) exactly as
the `/check-agent-orchestrator` skill directs. `aws sts get-caller-identity` confirmed the account (`427895769566`) is
correct and reachable. The script's own `SendCommand` call failed immediately:

```
[check-ao-backlog-status] dispatching read-only check to i-0c9b283b31d6b5ca7 (ap-northeast-1) via SSM send-command...
aws: [ERROR]: An error occurred (AccessDeniedException) when calling the SendCommand operation: User:
arn:aws:iam::427895769566:user/ikenna-worker is not authorized to perform: ssm:SendCommand on resource:
arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7 because no identity-based policy allows the
ssm:SendCommand action
```

Per the skill's own hard constraint ("If SSM access itself fails ... that's an infra/credentials problem for the
operator, not something to route around by opening a security-group rule or fabricating a token"), I stopped there
rather than attempting a workaround.

## Why it matters

This skill is explicitly the ONLY sanctioned read path to live AO backlog/dispatch state from a dev checkout — the
dashboard JWT isn't provisioned here and the VM's `:8765` has no public inbound rule (both by design). If
`ikenna-worker` can't `ssm:SendCommand`, this identity has **no way at all** to answer "has my plan been ingested / has
a slot claimed my task" without asking the operator directly every time — exactly the manual dependency this skill
exists to remove. Unknown yet whether this is a blanket gap (no worker identity has this permission) or scoped to just
this instance/identity pairing — worth a quick operator-side IAM check either way.

## Recommended decision

Operator grants `ikenna-worker` (or the IAM role/group it inherits from) `ssm:SendCommand` + `ssm:GetCommandInvocation`
scoped to `arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7` (least-privilege: this one instance,
these two actions — matches exactly what the skill's script calls). Left to the operator since it's an IAM policy change
on shared AWS infra, not something to self-grant.

## Todos

- [ ] [OPERATOR] P2. Grant `ikenna-worker` `ssm:SendCommand` + `ssm:GetCommandInvocation` on
      `arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7` (or diagnose why it's currently missing —
      may be a broader policy gap affecting other worker identities too) so `/check-agent-orchestrator` works from this
      checkout. Verify with `bash agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` after the grant —
      expect a fleet-wide summary instead of `AccessDeniedException`.

## Progress Log

- **2026-08-09 (slot-5, data_engineering)** — Filed after `/check-agent-orchestrator` failed AccessDenied while checking
  for new queued work (original session scope already fully shipped/archived). Not self-fixable — an IAM policy change
  on shared AWS infra is operator territory.
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — first audit pass on this doc. The sole `[OPERATOR]`
  item is an IAM policy grant to a specific human-named identity (`ikenna-worker`) on shared AWS infra, distinct from
  the "AO/operator cloud identities are IAM-self-service" precedent (that precedent covers the orchestrator's OWN
  service accounts granting themselves a missing role, not a human-named IAM user needing a grant from another identity)
  — the doc's own text explicitly frames this as "not something to self-grant." No new facts apply.
- **2026-08-09 (slot-18, backend_engineer)**: re-confirmed live — `aws sts get-caller-identity` still resolves to
  `arn:aws:iam::427895769566:user/ikenna-worker` from this checkout, and both `check-ao-backlog-status.sh` and its
  sibling `query-ao-state-db-readonly.sh` (same SendCommand call, different payload) fail the identical
  `AccessDeniedException` on `ssm:SendCommand` against
  `arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7`. Also confirmed `ikenna-worker` cannot even
  read its own attached/inline policies (`iam:ListAttachedUserPolicies`/`iam:ListUserPolicies` both AccessDenied) —
  there is no self-inspection path either, let alone self-grant. This is now also the blocker for
  `cross_cutting_satellite_ao_dispatch_batch7_2026_08_09.md`'s `[BACKEND] P2` historical-sample audit, which needs the
  exact same SSM read path to query `escalation_queue` directly (no HTTP endpoint exposes historical/resolved escalation
  rows — only `POST /api/escalate` and `GET /api/escalations/active`, the latter active-only). Flagging the
  cross-dependency here so the `[OPERATOR]` grant below is understood to unblock two independent tasks, not one.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since
  round9. The sole open item is an IAM policy grant to a specific human-named identity (`ikenna-worker`) on shared AWS
  infra — the doc's own text is explicit this is "not something to self-grant," and the IAM-self-service precedent
  (orchestrator service accounts granting themselves a missing role) does not extend to a human-named IAM user
  needing a grant from a different identity, which also cannot read its own attached policies to self-diagnose.
