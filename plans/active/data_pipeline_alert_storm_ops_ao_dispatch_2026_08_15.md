---
doc_type: plan
title: AO VM cross-cloud WIF + chain-relabel part 2 dispatch + combo_chain expiration ruling
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A, round 2) — three items from
  data_pipeline_alert_storm_root_cause_batch_2026_08_10.md: stand up cross-cloud Workload
  Identity Federation for the AO VM, re-verify then dispatch the chain relabel migration part
  2 execution plan, and record the combo_chain expiration ruling (each leg's own instrument_id
  already carries expiration, matching the options_chain/futures_chain precedent — no separate
  chain-level field needed).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta, data]
repos: [agent-orchestrator, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [ao, observability, wif, canonicalization, combo_chain]
related:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 2, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
locked_since:
resolved_by:
---

# AO VM cross-cloud WIF + chain-relabel part 2 dispatch + combo_chain expiration ruling

## Todos

- [x] [INFRA] P1. **Stand up cross-cloud Workload Identity Federation for the AO VM** — DONE 2026-08-16 (slot 6), WIF
      infra built + fully verified, live cutover partially blocked (see below). Built GCP Workload Identity Pool
      `aws-orchestrator-pool` + AWS provider `aws-orchestrator-provider` (account 427895769566),
      attribute-condition-restricted to EXACTLY `arn:aws:sts::427895769566:assumed-role/uts-orchestrator-epic-role`
      (this VM's own EC2 instance role, confirmed live via IMDSv2 on `i-0c9b283b31d6b5ca7`), bound
      `roles/iam.workloadIdentityUser` on `unified-trading-sa` scoped to that exact principalSet only. Generated the
      federated credential config with `--enable-imdsv2` (REQUIRED — this instance enforces IMDSv2-only, confirmed
      401 on an unauthenticated IMDS call; the flag adds `imdsv2_session_token_url`, which fixed BOTH the region
      lookup and the role-name lookup — the resulting config is fully self-contained, no `AWS_REGION` env var needed).
      **Verified working end-to-end 3 times**: token exchange, `gcloud projects describe`, and a real
      `gcloud secrets list` call returning the actual live secret names (`AGENT_ORCHESTRATOR_SLACK_APP_ID` etc.) —
      matching the original motivating gap in `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` line 307
      exactly. **Cut over the credential file**: backed up the old static SA key JSON
      (`private_key_id 4af7b762c69e34eda225428a0979c039db4ad18a`) to
      `~/.config/gcloud/application_default_credentials.json.static-key-backup.20260816T184438Z`, then replaced the
      well-known ADC file (`~/.config/gcloud/application_default_credentials.json`) with the verified WIF config —
      re-verified working via the DEFAULT credential discovery path (zero env overrides needed). **Could NOT force
      the live `orchestrator.service` process to pick this up immediately** — this worker session has no sudo/root
      (`systemctl restart orchestrator` fails: "the 'no new privileges' flag is set, which prevents sudo from
      running as root"); confirmed via `/api/backlog` that the service is otherwise unaffected and still running
      fine on its existing in-memory credential state (no restart = no disruption). Two follow-up todos filed below
      to close this out safely. Repo: agent-orchestrator (no code diff — pure GCP/host infra standup; evidence here
      + the live GCP IAM state is the artifact).
- [ ] [INFRA] P1. **New follow-up from the WIF standup above**: verify the live `orchestrator.service` process has
      actually picked up the new WIF credential (needs operator/root — this worker session had no sudo), either after
      its next natural restart (`ao-self-pull.sh`'s restart-on-HEAD-move) or a manual `systemctl restart orchestrator`
      — check `/proc/<MainPID>/environ` for no stale state and confirm a live GCP-dependent call (e.g. a Secret
      Manager read) succeeds post-restart. **Done when**: confirmed live, cited here. Repo: agent-orchestrator
      (host-level, `planning` VM).
- [ ] [INFRA] P2. **Gated on the todo above landing**: once the live cutover to WIF is confirmed, formally revoke the
      old static SA key (`gcloud iam service-accounts keys delete 4af7b762c69e34eda225428a0979c039db4ad18a
      --iam-account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com`) — deliberately NOT done in
      this pass, since revoking a key possibly still relied on elsewhere is the one truly irreversible step here and
      needs the cutover confirmed live first. Delete the local backup file only after the key itself is revoked
      GCP-side. Repo: agent-orchestrator (host-level, `planning` VM).
- [ ] [INFRA] P3. **New finding, out of scope for this pass**: `~/.aws/credentials` on the `planning` VM carries a
      SEPARATE static AWS IAM user credential (`ikenna-worker`, long-lived access key) that takes priority over the
      VM's own `uts-orchestrator-epic-role` instance-profile role in the AWS SDK's default credential chain — this is
      a residual static-credential risk independent of the GCP-side fix above (the WIF setup above correctly targets
      the instance role, not this user key, so it is unaffected by and does not depend on this finding). Investigate
      whether anything actually needs this static user key vs. the ambient instance role, and if not, retire it.
      Repo: infra (host-level, `planning` VM).
- [ ] [DATA] P1. Re-verify the chain relabel migration part 2 execution plan is still current against live state
      (per line 332 — direction already approved), then dispatch execution. Given how much has landed on this
      branch recently, do not trust a stale citation — re-measure before executing. (repo: instruments-service)
- [ ] [DOCS] P3. Record the combo_chain expiration ruling: `combo_chain` is a chain-type shard (same
      `CEFI_CHAIN_INSTRUMENT_TYPES`/`TRADFI_CHAIN_INSTRUMENT_TYPES` frozenset as `options_chain`/`futures_chain` in
      `unified_api_contracts/canonical/_partition_path_canonicality.py`) — each leg-row carries its own full
      `instrument_id` with its own embedded expiration, matching the established sibling-type precedent. No separate
      chain-level expiration field is needed. Update the combo_chain schema doc/docstring to state this explicitly so
      the question (line 804) doesn't get re-asked. (repo: unified-api-contracts)

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 2, operator ruling)**: extracted from
  `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`. Combo_chain ruling was verified live against
  `unified_api_contracts/canonical/_partition_path_canonicality.py` before being recorded — not taken on the
  operator's framing alone.
- **2026-08-16 (slot 6, infra worker, AO-dispatched)**: Stood up + verified AWS→GCP Workload Identity Federation for
  the orchestrator VM end-to-end (pool/provider/binding/cred-config, hit and fixed two real bugs along the way —
  a 256-char description limit and a missing `--enable-imdsv2` flag needed on this IMDSv2-only-enforced instance).
  Cut over the well-known ADC credential file to the verified WIF config (old static SA key backed up, not deleted).
  Could not force the live orchestrator.service process to reload it — this worker session has no sudo. Filed 2 new
  gated follow-ups (verify live cutover post-restart; then formally revoke the old key) + 1 new lower-priority
  finding (a separate static AWS user credential also present on the host). Full evidence in the flipped checkbox
  above.
