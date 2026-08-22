---
doc_type: issue
title: >-
  ci_reconciler's ambient AWS identity is `ikenna-worker` (static IAM user), not `uts-orchestrator-epic-role` —
  §0c host-dispatched-watchdog SSM verification structurally unavailable every hourly run
summary: >-
  The `ci_reconciler` scheduled role's boot doc states "SSM is still required for the §0c host-dispatched watchdogs...
  no AWS SSM needed for AO's own API" — implying `aws ssm send-command` against the glue-runner host
  (`i-042a6332509482556`, `ap-northeast-1`) just works from the orchestrator VM. It does not: `aws sts
  get-caller-identity` resolves to `arn:aws:iam::427895769566:user/ikenna-worker` (a static shared-credentials-file IAM
  user), not the orchestrator's documented self-service AWS identity `uts-orchestrator-epic-role`
  (`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) — confirmed by a failed `sts:AssumeRole`
  attempt (`AccessDenied`) in addition to the direct `ssm:SendCommand` `AccessDeniedException`. Per that SSOT, a
  permission gap is only self-fixable when hit while acting AS one of the two named orchestrator identities
  (`unified-trading-sa` GCP / `uts-orchestrator-epic-role` AWS) — `ikenna-worker` is a genuinely different identity, so
  this run correctly did NOT self-grant `ssm:SendCommand` to it. Net effect: every `/ci-reconcile` §0c sweep run under
  this credential set cannot directly verify `glue-runner-crash-loop-watchdog.sh` / `ci-vm-resource-watchdog.sh` host
  state via SSM, and must fall back to indirect evidence (Slack alert/recovery history, GH Actions dispatch history)
  which the skill itself flags as weaker than a live check.
status: open
nature: issue
scope: [engineer, admin]
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
tags: [ci-reconcile, ssm, iam, aws, permission-gap, coverage-gap, host-dispatched-watchdog]
related:
  [
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /plans/active/issues/check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md,
  ]
context_scope:
  - /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md
  - scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh
  - scripts/self-hosted-runners/ci-vm-resource-watchdog.sh
  - /plans/active/issues/check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md
created: 2026-08-16
author: claude-agent
last_updated: 2026-08-21
parent_epic: ci_master
priority: P2
source: ci-reconcile skill, scheduled hourly ci_reconciler dispatch agt-17f258 (slot 20)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# ci_reconciler's ambient AWS identity blocks §0c SSM verification

## Evidence (2026-08-16, ~03:40-03:45 UTC, slot 20)

```
$ aws sts get-caller-identity
{"UserId": "AIDAWHIETJHPNCDXGM6BX", "Account": "427895769566",
 "Arn": "arn:aws:iam::427895769566:user/ikenna-worker"}

$ aws ssm send-command --instance-ids i-042a6332509482556 ...
AccessDeniedException: User: .../user/ikenna-worker is not authorized to perform: ssm:SendCommand
  on resource: arn:aws:ec2:ap-northeast-1:427895769566:instance/i-042a6332509482556

$ aws sts assume-role --role-arn arn:aws:iam::427895769566:role/uts-orchestrator-epic-role ...
AccessDenied: User: .../user/ikenna-worker is not authorized to perform: sts:AssumeRole
  on resource: arn:aws:iam::427895769566:role/uts-orchestrator-epic-role
```

`aws configure list` confirms these are static keys from a shared-credentials-file (`~/.aws/credentials`), not
EC2-instance-metadata-derived — i.e. this dispatch's shell is NOT actually authenticating as the orchestrator VM's
instance-profile role the way `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` describes for
every AO worker.

## Why this wasn't self-fixed this run

The self-service SSOT is explicit: self-grant is sanctioned only for a gap hit while acting AS `unified-trading-sa`
(GCP) or `uts-orchestrator-epic-role` (AWS) — "reserve `[OPERATOR]`/`BLOCKED-CREDENTIALS` for a gap on a genuinely
DIFFERENT identity this worker cannot assume." `ikenna-worker` is such a different identity (confirmed — cannot even
`AssumeRole` into the orchestrator's role), so granting `ssm:SendCommand` directly to `ikenna-worker` would be acting
outside that sanctioned scope, not exercising it.

## Impact this run

Fell back to indirect evidence for the one host-dispatched alert in the sweep window
(`glue-runner-crash-loop-watchdog` CRITICAL, 08-15 15:49Z, `github-glue-runner-unified-api-contracts@glue-1.service`
on `i-042a6332509482556`, 26.3h continuous-active): a 24h Slack sweep found this alert fired exactly once with no
matching recovery post and no recurrence — consistent with either a genuine one-off resolved outside the alert
channel, or a watchdog that's still silently red. Could not be verified either way live. Same gap applies to
`ci-vm-resource-watchdog.sh`'s target, not separately re-attempted (identical credential blocker).

## Disposition

Filing as a structural coverage gap rather than attempting a fix — granting AWS permissions to a human-named IAM user
identity is an operator-scoped IAM decision (this is exactly the class of identity change the self-service doc
deliberately does NOT cover), not a routine self-service action. Suggested resolution paths for the operator to choose
from: (a) grant `ikenna-worker` a scoped `ssm:SendCommand` on the specific glue-runner/CI-VM instances if this
credential set is the intended ambient identity for `ci_reconciler` dispatches going forward, or (b) fix whatever is
causing `ci_reconciler` dispatches to pick up `ikenna-worker`'s static keys instead of the orchestrator VM's own
`uts-orchestrator-epic-role` instance-profile credentials (the latter would restore the boot doc's stated "no AWS SSM
needed" assumption and fix this for every future hourly run, not just this one).

## Todos

- [ ] [INFRA] P2. Attempt to apply the already-ruled scoped `ssm:SendCommand` grant (+ codebuild grant) to this
      slot's own AWS identity for `i-0c9b283b31d6b5ca7`/the glue-runner host, and fix why `ci_reconciler`
      dispatches resolve to `ikenna-worker`'s static keys instead of the orchestrator VM's own
      `uts-orchestrator-epic-role` instance-profile credentials — with existing access (IAM self-service rule,
      per D4 ruling); if a genuine wall (no AWS admin path from this identity), escalate with options
      (a) grant `ikenna-worker` scoped `ssm:SendCommand` directly, or (b) fix the credential-resolution path so
      dispatches inherit the orchestrator VM's own instance-profile role. Done when: `aws sts get-caller-identity`
      from a `ci_reconciler` dispatch resolves to `uts-orchestrator-epic-role` (or an operator-approved alternate),
      and a live `aws ssm send-command` against the glue-runner/CI-VM instances succeeds.

## Progress Log

- 2026-08-16: Filed by `ci_reconciler` (agt-17f258, slot 20) during a routine hourly sweep. No CI/CD items required a
  fix this run (full fleet + monitor sweep all green/self-resolved) — this was the only unresolved item.
- 2026-08-16 (triage pass): confirmed still open, operator-gated (IAM identity decision, not self-fixable per the
  self-service SSOT). Added a tracked `- [ ]` Todos section (doc previously carried only prose disposition —
  hygiene fix per the "every follow-up is a tracked todo" rule). No live re-check attempted this pass.
- 2026-08-16 (agt-135424, slot 16, ~18:00Z hourly sweep): confirmed still open and unchanged —
  `aws sts get-caller-identity` still resolves to `arn:aws:iam::427895769566:user/ikenna-worker`, and
  `agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` (§5's own worker-liveness check, a second,
  DIFFERENT SSM target — the orchestrator VM `i-0c9b283b31d6b5ca7` itself, not just the glue-runner host from the
  original filing) hit the identical `AccessDeniedException` on `ssm:SendCommand`. So the gap is broader than
  originally scoped: it blocks BOTH the §0c host-dispatched-watchdog check AND the §5 AO worker-liveness check, any
  time a `ci_reconciler` dispatch needs to reach EITHER of the two AWS-SSM-fronted hosts. Did not attempt a
  self-grant (same identity, same reasoning as the original filing). Substituted INDIRECT evidence for §5 this run:
  `GET /api/escalations/active` showed one escalation move `queued` (created 18:01:25Z) → `dispatched` (18:01:34Z,
  to slot 33) in 9 seconds, and `GET /api/healthz` returned `{"status":"ok","mode":"live","uptime_seconds":427}` —
  consistent with a live, actually-spawning dispatch loop (not just a healthy HTTP process), though this is a
  weaker signal than the direct `tmux list-sessions` check §5 calls for and should not be treated as a full
  substitute going forward.

- **context-scout 2026-08-17**: refreshed context_scope (4 entries) -- added `check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md`
  (fingerprint match: byte-identical `AccessDeniedException`/`ssm:SendCommand`/`ikenna-worker` evidence against the SAME
  instance ARN `i-0c9b283b31d6b5ca7`, already cross-linked bidirectionally via `related:`).
- **na-eligibility-audit 2026-08-18** (infra tranche) [body-hash:1edc21d8ba34f2a7]: KEEP-NA, valid — first audit
  pass (no prior marker). Sole open item is explicitly `[OPERATOR]`-tagged: a genuine AWS IAM identity decision
  (grant `ikenna-worker` scoped SSM access, vs. fix why this dispatch shape isn't inheriting the orchestrator VM's
  own `uts-orchestrator-epic-role` instance-profile credentials) — not worker-determinable alone per the
  self-service SSOT's own explicit carve-out for a genuinely different, non-assumable identity.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries) — the self-service SSOT, both watchdog scripts,
  and the sibling access-denied issue all resolve and remain the doc's coverage.

- **2026-08-21 — ruling D4 (AWS access for worker identities)**: ATTEMPT-THEN-ASK — apply the already-ruled
  codebuild grant + scoped SSM grant from this slot's AWS identity (IAM self-service rule); fix the
  credential-resolution path. Only if AWS admin is genuinely absent here, escalate. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
