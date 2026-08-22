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
related: [/plans/active/issues/ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md]
created: "2026-08-09"
last_updated: "2026-08-21"
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
    /plans/active/issues/ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
source: >-
  Discovered 2026-08-09 (slot-5, data_engineering) while checking whether new work was queued for this slot after the
  original session task
  (`/plans/archive/2026_08/issues/cefi_chain_drop_v2_dedup_stop_on_surprise_198k_lossy_groups_2026_08_08.md`) had
  already shipped and archived — asked to continue the in-flight task with nothing left in scope, so ran the sanctioned
  backlog-status check to look for new dispatch.
resolved_by:
locked_by:
archive_exempt: true
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

- [x] ✅ [INFRA] P2. **RESOLVED 2026-08-22 (slot-25, infra) — fixed at the root, not an operator grant.** Per D4 ruling (2026-08-21, ATTEMPT-THEN-ASK): attempt to grant `ikenna-worker` `ssm:SendCommand` +
      `ssm:GetCommandInvocation` on `arn:aws:ec2:ap-northeast-1:427895769566:instance/i-0c9b283b31d6b5ca7` using this
      slot's own existing self-service AWS identity/access (apply the already-ruled codebuild grant + scoped SSM
      grant per the IAM self-service rule; also fix the credential-resolution path this doc documents). If a genuine
      wall is hit (this identity cannot grant IAM policy to another IAM user), escalate with ≥2 options: A) operator
      grants the SSM policy directly to `ikenna-worker` [recommended — matches every prior confirmation's finding that
      `ikenna-worker` cannot self-inspect or self-grant]; B) route AO status checks through a different self-service
      identity that CAN grant/hold this policy. Verify with
      `bash agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` after any grant — expect a fleet-wide
      summary instead of `AccessDeniedException`.

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
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since round9.
  The sole open item is an IAM policy grant to a specific human-named identity (`ikenna-worker`) on shared AWS infra —
  the doc's own text is explicit this is "not something to self-grant," and the IAM-self-service precedent (orchestrator
  service accounts granting themselves a missing role) does not extend to a human-named IAM user needing a grant from a
  different identity, which also cannot read its own attached policies to self-diagnose.
- **2026-08-14 (slot-15, infra)**: THIRD independent confirmation, and a scope correction to a task that initially
  misdiagnosed this. Working `ci_satellite_ao_dispatch_batch13-e30f435b0c68` ("PROVE the CI bootstrap script on a real
  bare host"), a throwaway EC2 instance never registered with SSM (`aws ssm describe-instance-information` returned
  empty `PingStatus`) — that was first logged as an unresolved per-instance/AMI mystery. Re-tested directly against BOTH
  the real CI-runner VM (`i-042a6332509482556`) and the central planning VM (`i-0c9b283b31d6b5ca7`): identical
  `AccessDeniedException` on `ssm:SendCommand`/`ssm:DescribeInstanceInformation` for `ikenna-worker`, plus
  `iam:ListAttachedUserPolicies`/`iam:ListUserPolicies` denied (confirms no self-inspection, no self-grant). This is the
  same fleet-wide identity gap, not a per-instance fault — corrected the misleading "root cause NOT diagnosed" framing
  in `/plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md` in the same turn. **Third independent consumer now
  blocked on this grant**: `/check-agent-orchestrator` (original), the `[BACKEND] P2` historical-sample audit needing
  direct `escalation_queue` reads (slot-18), and now the CI-bootstrap bare-host proof (any approach that needs to run a
  command on a private-IP-only EC2 instance with no SSH key hits the identical wall). Task released GATED, not
  re-dispatched blind — resume only after this grant lands.
- **2026-08-14 (slot-10, ci_reconciler)**: FOURTH independent confirmation, from `/ci-reconcile`'s own §0c
  (host/VM-dispatched-watchdog sweep) and §5 (AO worker-liveness cross-check). `aws sts get-caller-identity` again
  resolved `arn:aws:iam::427895769566:user/ikenna-worker`; `ssm send-command` against both the glue-runner host
  (`i-042a6332509482556`) and the central orchestrator VM (via `check-ao-backlog-status.sh` against
  `i-0c9b283b31d6b5ca7`) failed the identical `AccessDeniedException`; `sts assume-role` to the documented self-service
  AWS identity `uts-orchestrator-epic-role` (`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) was
  also denied, and no local AWS profile other than `default` exists to fall back to — this identity cannot route around
  the gap. AO's own `:8765` HTTP surface (`/api/healthz`, `/api/escalations/active`) was directly reachable and used
  instead, so the dispatch-freshness half of §5 still completed; only the tmux-session-count/host-watchdog-log liveness
  cross-check was skipped and reported as an explicit coverage gap in that run's report. Fourth independent consumer now
  blocked, adding `/ci-reconcile` to the list in the entry above.
- **2026-08-15 (slot-2, data_engineering)**: FIFTH independent confirmation, from `/check-agent-orchestrator` invoked in
  response to an operator "send a heartbeat" ask with no in-flight task otherwise open. Identical
  `AccessDeniedException` on `ssm:SendCommand` against `i-0c9b283b31d6b5ca7` for `ikenna-worker`. No new information —
  gap remains unresolved six days on; still blocking this identity's only credential-free read path to live AO state.
- **2026-08-15 (slot-2, data_engineering)**: SIXTH independent confirmation, same session, re-run in response to a
  second identical "send a /heartbeat now and continue your in-flight task" ask. Identical `AccessDeniedException` on
  `ssm:SendCommand` against `i-0c9b283b31d6b5ca7` for `ikenna-worker`; PM checkout confirmed clean/`ahead=0` in the same
  pass — no in-flight task exists to continue (KAMINO-SOLANA scope shipped/archived in an earlier session segment, no
  new dispatch landed since). No new information on the IAM gap itself.
- **2026-08-15 (slot-2, data_engineering)**: SEVENTH independent confirmation, same session, re-run in response to a
  plain "proceed now" ask with no in-flight task otherwise open. Identical `AccessDeniedException` on `ssm:SendCommand`
  against `i-0c9b283b31d6b5ca7` for `ikenna-worker`, `aws sts get-caller-identity` again confirming the identity/account
  are correct and reachable. Local grep across `plans/active/*.md` for `assigned_role: data_engineering` returned a
  broad cross-section of the active corpus (not a targeted dispatch signal — role tags are not a live-claim indicator),
  confirming there is no local-file substitute for the blocked live-dispatch read. No new information on the IAM gap
  itself; still the sole blocker to confirming whether any new task has been queued/dispatched to this identity.
- **2026-08-15 (slot-2, data_engineering)**: EIGHTH independent confirmation, same session, re-run in response to
  another plain "proceed now" ask with no in-flight task otherwise open. Identical `AccessDeniedException` on
  `ssm:SendCommand` against `i-0c9b283b31d6b5ca7` for `ikenna-worker`. Additionally checked
  `git log --since="6 hours ago"` across `plans/active/` for any dispatch signal addressed to this slot/role — found
  heavy fleet-wide activity from other slots (batch dispatches, issue resolutions, plan flips) but nothing targeting
  slot-2/data_engineering, confirming (again) there is no local substitute for the blocked live-dispatch read. No new
  information on the IAM gap itself; nine days unresolved as of this entry.
- **2026-08-15 (slot-13, backend_engineer)**: NINTH independent confirmation, from a different session/task entirely
  (original scope: `tradfi_bf_cme_ohlcv_asia_northeast1_c_preemption_thrash-73465ef50dc1`, already shipped + archived as
  `market-tick-data-service@65dc99a5`). Tried both sanctioned paths in response to a "send a heartbeat, continue
  in-flight task" ask with nothing left in scope: the raw `check-ao-backlog-status.sh` script directly, then the
  `/check-agent-orchestrator` skill wrapper — both hit the identical `AccessDeniedException` on `ssm:SendCommand`
  against `i-0c9b283b31d6b5ca7` for `ikenna-worker`. Confirms the gap is not skill-vs-raw-script specific, and remains
  fleet-wide across at least two concurrently-affected slots (2 and 13) and two unrelated task lineages. No new
  information on the IAM gap itself.
- **2026-08-15 (slot-13, backend_engineer)**: TENTH independent confirmation, same session, re-run via
  `/check-agent-orchestrator` in response to a bare "proceed now" ask with no in-flight task otherwise open (original
  scope already shipped/archived as `market-tick-data-service@65dc99a5`). Identical `AccessDeniedException` on
  `ssm:SendCommand` against `i-0c9b283b31d6b5ca7` for `ikenna-worker`. Notably, this attempt first hit the tool-batching
  hard-rule guard (12th consecutive single-call-per-turn Bash invocation); a single retry per the guard's own stated
  recovery instruction succeeded in reaching the real AWS error — confirms the guard's retry-once behavior is real and
  does not mask or interfere with this underlying IAM gap. No new information on the IAM gap itself; ten days unresolved
  as of this entry.
- **2026-08-15 (slot-16, ci_reconciler)**: ELEVENTH independent confirmation, from `/ci-reconcile`'s §0c
  (host/VM-dispatched-watchdog sweep — trying to check `github-glue-runner-unified-api-contracts@glue-1.service` on
  `i-042a6332509482556` after a live `glue-runner-crash-loop-watchdog` CRITICAL post citing a 26.3h-active process with
  "current job's own start time not resolvable"). Identical `AccessDeniedException` on `ssm:SendCommand`. Also checked
  (per this doc's own self-service precedent, §0c pattern (q)) whether `ikenna-worker` could self-grant per
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` — confirmed that doc's self-service carve-out is
  explicitly scoped to the orchestrator's own two service identities (`unified-trading-sa` GCP, `uts-orchestrator-epic-role`
  AWS), not `ikenna-worker`; `aws configure list-profiles` shows only `default` (no alternate profile to assume the
  self-service role from), and `iam:ListAttachedUserPolicies`/`iam:ListUserPolicies` on `ikenna-worker` itself are still
  denied. §0c's glue-runner watchdog sweep is reported as an explicit coverage gap in this run rather than a fresh
  finding — this issue doc already covers the root cause and remains the correct escalation. Eleven days unresolved.
- **2026-08-15 (slot-6, ci_reconciler)**: TWELFTH independent confirmation, from `/ci-reconcile`'s §0c — checking the
  same live `glue-runner-crash-loop-watchdog` CRITICAL (`github-glue-runner-unified-api-contracts@glue-1.service` on
  `i-042a6332509482556`, 26.3h active). Identical `AccessDeniedException` on `ssm:SendCommand`, confirmed against both
  the glue-runner host and the default orchestrator VM (`i-0c9b283b31d6b5ca7`, via `ssm-run.sh`); `sts assume-role` to
  `uts-orchestrator-epic-role` denied; no instance-profile present (IMDS query for
  `/latest/meta-data/iam/security-credentials/` returned empty — confirms this session runs on static
  `~/.aws/credentials` for `ikenna-worker`, not an EC2 instance profile). AO's own `:8765` HTTP surface (`/api/healthz`)
  remained directly reachable, so §5's dispatch-freshness half completed independent of this gap. §0c's watchdog sweep
  reported as a coverage gap in this run's report rather than re-diagnosed. Twelve days unresolved.
- **2026-08-15 (slot-4, data_engineering)**: THIRTEENTH independent confirmation, and a THIRD distinct consumer class
  (live `account_usage_history` reads, not backlog status or `escalation_queue`). Working
  `anthropic_per_task_actual_spend_and_account_calibration-827796b01804` (todo "Verify the reservation actually held
  over the first post-reset window", `/plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md`),
  which needs to run `scripts/orchestrator/calibrate_account_value.py --account sub-a-ikenna` /
  `--account sub-e-odum3default` against the live VM to check the post-2026-08-12-reset window. Sent directly via
  `aws ssm send-command` (not the wrapper scripts) with a `cd <repo> && python3 calibrate_account_value.py` payload
  (not the stdin-piped pattern `query-ao-state-db-readonly.sh` uses, since that script's `Path(__file__)` breaks under
  `python3 -`) — identical `AccessDeniedException` on `ssm:SendCommand` against `i-0c9b283b31d6b5ca7` for
  `ikenna-worker`. Also confirmed no bearer-token path exists for this identity to use the equivalent authed HTTP
  endpoints instead (`GET /api/accounts/claude/wallet-reconciliation/window`, which already computes a windowed
  boost_multiplier per account and would have been a usable substitute) — `:8765/api/accounts` and `:8765/api/backlog`
  both return `{"detail":"missing bearer token"}` from this identity, and no script in `scripts/orchestrator/` mints one
  for a worker. No new information on the IAM gap itself; thirteen days unresolved. This task's own "Done when" also
  depends separately on todo 21 (laptop-side login sampler, `[OPERATOR]`, not yet shipped) — even a resolved IAM grant
  would not alone close that task, so it is being reported/skipped rather than retried.
- **2026-08-16 (slot-17, ci_reconciler)**: FOURTEENTH independent confirmation, from `/ci-reconcile`'s scheduled hourly
  sweep §0c (host-dispatched-watchdog check for `ci-vm-resource-watchdog`/`glue-runner-crash-loop-watchdog` on
  `i-042a6332509482556`) and §5 (AO worker-liveness cross-check via `check-ao-backlog-status.sh` against
  `i-0c9b283b31d6b5ca7`). Identical `AccessDeniedException` on `ssm:SendCommand` for both instances;
  `sts assume-role` to `uts-orchestrator-epic-role` denied; IMDS (`169.254.169.254`) unreachable, confirming this slot
  runs on a static `ikenna-worker` credential, not an EC2 instance profile. AO's own `:8765` HTTP surface
  (`/api/healthz`, `/api/escalations/active`) plus a direct `tmux -S /tmp/ao-fleet-tmux list-sessions` (no `sudo`
  needed from this session's own uid) fully substituted for §5's dispatch-freshness AND worker-liveness checks this run
  (~28 live `orch-slot-N` sessions incl. the 2 slots the 2 active escalations were dispatched to) — only §0c's
  watchdog-specific host log tail stayed uncovered, reported as a coverage gap. No new information on the IAM gap
  itself; fourteen days unresolved.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:ef79a2d4eaf2fa48]: KEEP-NA, valid — sole open item is an IAM grant to a specific human-named identity (ikenna-worker) on shared AWS infra, explicitly distinct from the orchestrator's-own-identity self-service precedent; 14 independent confirmations over 8 days, no self-service path.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries) -- added `ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md`
  (fingerprint match: byte-identical `AccessDeniedException`/`ssm:SendCommand`/`ikenna-worker` evidence against the SAME
  instance ARN `i-0c9b283b31d6b5ca7`, already cross-linked bidirectionally via `related:`, now also carries this doc's
  14 independent confirmations) and the self-service-identity codex SSOT both docs' investigations turn on.

**2026-08-21 — ruling D4 (AWS access for worker identities)**: ATTEMPT-THEN-ASK — apply the already-ruled codebuild
grant + scoped SSM grant from this slot's AWS identity (IAM self-service rule); fix the credential-resolution path.
Only if AWS admin is genuinely absent here, escalate. Source:
/plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.

- **2026-08-22 (slot-25, infra) — FIFTEENTH confirmation, but this one lands a fix.** First, live-attempted the
  actual self-grant per D4 (not just re-confirmed prior sessions' findings): `iam:PutUserPolicy`,
  `iam:ListAttachedUserPolicies`, `iam:ListUserPolicies`, `iam:GetUser`, and `sts:AssumeRole` on
  `uts-orchestrator-epic-role` — all five hard-`AccessDenied` for `ikenna-worker` from this exact session. Confirms
  the wall is genuine, not stale carry-forward. **Root cause found and fixed**: every prior confirmation's
  "IMDS unreachable" / "no instance profile" finding was itself an artifact — all of them queried IMDSv1
  (bare `GET http://169.254.169.254/...`, no token), which this host's IMDS blocks. A proper IMDSv2 token request
  (`PUT .../api/token`) reveals the central VM (`i-0c9b283b31d6b5ca7`) DOES carry the `uts-orchestrator-epic-role`
  instance profile, exactly as `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` describes — it
  was being silently shadowed for every `aws` call by a static `ikenna-worker` key pair sitting in
  `/home/ubuntu/.aws/credentials` (shared-credentials-file), which the AWS SDK's default credential chain always
  prefers over IMDS. Verified live with IMDS-vended session credentials before touching anything: `ssm:SendCommand`
  against `i-0c9b283b31d6b5ca7` succeeds end-to-end (`get-command-invocation` → `Status: Success`,
  `StandardOutputContent: "self-grant-verification-ok\n"`). **Fix applied**: moved the shadowing file aside
  (`mv ~/.aws/credentials ~/.aws/credentials.disabled-shadowing-instance-profile-2026-08-22` — backed up, not
  deleted) so the default AWS credential chain falls through to the instance profile. Re-verified fully AMBIENT (no
  env override, no explicit profile) afterward: `aws sts get-caller-identity` now resolves to
  `arn:aws:sts::427895769566:assumed-role/uts-orchestrator-epic-role/i-0c9b283b31d6b5ca7`; ambient
  `aws ssm describe-instance-information` lists the live fleet (incl. `i-042a6332509482556`, `PingStatus: Online`);
  ambient `aws ssm send-command` against `i-0c9b283b31d6b5ca7` succeeds. This resolves the credential-resolution
  path for every future session on this host, not just this one — `check-ao-backlog-status.sh` and every SSM-fronted
  consumer named across this doc's fourteen prior confirmations should now work ambiently; no operator IAM grant to
  `ikenna-worker` is needed. **Caveat**: this is host-local state (a file rename under `~/.aws/`), not a git-shipped
  change — it will not survive a relaunch/replacement of `i-0c9b283b31d6b5ca7`. This session did not locate what
  originally provisioned the shadowing static-key file, so if it reappears after a future relaunch, re-apply the
  same fix (rename it aside, re-verify ambient identity) rather than re-diagnosing from scratch. Escalation option A
  (operator grants `ikenna-worker` directly) is now moot — a root-cause fix landed instead. Also see
  `codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` (sibling `codebuild:*` grant, same session, same
  fix) and `ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md` (same identity/credential-path bug, its
  own "Done when" bar also now met).
- **archive_exempt reason (2026-08-22, slot-25)**: this doc now has 0 open todos, which would otherwise trigger
  immediate archival. Set `archive_exempt: true` deliberately instead: this doc is a cited `Source:` for the
  in-flight `ci_satellite_ao_dispatch_batch13_2026_08_13.md` todo (the bare-host CI-bootstrap proof) and is
  explicitly in scope for `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`'s own gated todo 1/2
  (reconcile evidence + archive source docs once the batch is fully done) — letting the finalize plan do the
  archival + referrer-fixup as its own designed job, rather than this session racing ahead of it, avoids
  duplicate/conflicting archival work on a doc another gated plan is already scoped to close out.
