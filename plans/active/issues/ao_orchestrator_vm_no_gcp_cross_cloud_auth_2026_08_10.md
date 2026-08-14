---
doc_type: issue
title:
  "AO orchestrator VM (AWS EC2) has zero GCP credential — blocks Slack read-access and any other GCP-dependent
  script/skill from running on it"
summary: >-
  Direct verification via AWS SSM (`i-0c9b283b31d6b5ca7`, `agent-orchestrator-vm-1`) on 2026-08-10 found the AO
  orchestrator VM has NO GCP authentication configured at all: `gcloud auth list` → "No credentialed accounts",
  `GOOGLE_APPLICATION_CREDENTIALS` unset, no service-account key file on disk. `gcloud` itself IS installed
  (`/snap/bin/gcloud`), but there is no identity for it to use. This blocks `scripts/dev/slack-read-channel.py` (and by
  extension `/data-pipeline-alerts-reconcile`, which is explicitly interactive-session-only today for this reason) plus
  any other GCP-Secret-Manager/GCS/etc-dependent capability from ever running FROM the orchestrator VM itself — a real,
  standing gap, not a quick IAM-binding grant (there's no identity on the VM to grant a binding TO).

  A same-day codex doc (`/codex/05-infrastructure/agent-slack-read-access.md`) had claimed this was already working
  fleet-wide including the AO VM — that claim was aspirational/unverified and has been corrected in-place with this
  finding's evidence.
status: open
nature: issue
asset_group: [meta, ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao, cross-cloud, gcp, aws, iam, workload-identity-federation, slack, access-gap]
related:
  [
    /codex/05-infrastructure/agent-slack-read-access.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
context_scope:
  [
    /codex/05-infrastructure/agent-slack-read-access.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
created: 2026-08-10
author: unknown
priority: P2
parent_epic: orchestrator_master
source: >-
  Operator asked for direct verification of whether AO's orchestrator VM already had GCP Secret Manager access for Slack
  reading, 2026-08-10. Verified live via AWS SSM send-command (read-only, redacted — never printed the secret value,
  only its access-attempt exit code).
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
---

## Evidence

Via `aws ssm send-command` (`AWS-RunShellScript`, read-only) against `i-0c9b283b31d6b5ca7` (`ap-northeast-1`):

```
=== active gcloud identity ===
(unset)
=== secret access test (exit code only, value redacted) ===
EXIT_CODE=1
=== gcloud installed? ===
/snap/bin/gcloud
=== gcloud auth list ===
No credentialed accounts.
=== ADC env var ===
GOOGLE_APPLICATION_CREDENTIALS=unset
=== any GCP SA key files on disk? ===
(none found)
```

## Why this matters beyond Slack read-access

Any future skill/capability that needs the AO orchestrator VM itself (not a dispatched worker on a GCP-hosted slot) to
directly call GCP Secret Manager, GCS, or any other GCP API will hit this exact same wall. Slack read-access is the
first concretely-blocked case (`/data-pipeline-alerts-reconcile` skill's own § 0 already documents "AO cannot run this
skill autonomously today" as a known limitation), but it's a general capability gap, not Slack-specific.

## Recommended fix (not attempted here — real infra decision)

**Workload Identity Federation (AWS → GCP)** is the right pattern: no long-lived static key deployed to a production VM,
matches this workspace's general anti-static-credential posture (`orchestrator-cloud-identity-self-service.md`). A
static service-account JSON key would work faster but is explicitly the wrong tradeoff for a VM this central — flagging
so nobody takes the fast-but-wrong shortcut under time pressure.

## Todos

- [ ] [OPERATOR] P2. Decide: set up WIF (AWS IAM role ↔ GCP workload identity pool) for the AO orchestrator VM's
      instance role, or explicitly decide this gap is acceptable for now (Slack read stays interactive-session-only).
      Either is a real decision, not a default.
- [ ] [INFRA] P2. Once WIF (or an equivalent decision) is made: implement + grant the `SLACK_ALERTS_READER_BOT_TOKEN`
      secret's `secretmanager.versions.access` to whatever new identity is provisioned, then re-run this same SSM
      verification to confirm `gcloud secrets versions access` succeeds live from the orchestrator VM before declaring
      it fixed — do not trust a Terraform apply alone, re-verify exactly like this issue doc did.
- [ ] [DOC] P3. Once fixed, update `/codex/05-infrastructure/agent-slack-read-access.md` and
      `/data-pipeline-alerts-reconcile`'s SKILL.md § 0 to drop the "AO cannot run this today" caveat, with the
      verification evidence cited in both places (same discipline this issue doc followed).

## Progress Log

- 2026-08-10: Filed after direct SSM verification contradicted a same-day codex doc's optimistic claim. Codex doc
  corrected in the same session (see `related`). No fix attempted — this is a real infra/architecture decision (WIF
  setup), correctly left for operator/infra scoping rather than an ad-hoc SSM-deployed key.
- **context-scout 2026-08-14**: populated context_scope (2 entries).
