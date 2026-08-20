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
last_updated: "2026-08-20"
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
    /plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md,
    unified-api-contracts/unified_api_contracts/canonical/_partition_path_canonicality.py,
    agent-orchestrator/server/auth.py,
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
- [x] ✅ [INFRA] P1. **New follow-up from the WIF standup above**: verify the live `orchestrator.service` process has
      actually picked up the new WIF credential — **CONFIRMED LIVE 2026-08-16 (slot 22, infra)**, no operator/sudo
      needed after all: `orchestrator.service` had ALREADY naturally restarted (Main PID 2575365, `Active: active
      (running) since 2026-08-16T18:46:18Z`) — after the ADC cutover at `18:44:38Z` (matches the backup file's own
      timestamp `application_default_credentials.json.static-key-backup.20260816T184438Z`), so this restart already
      picked up the swap; no manual `systemctl restart` was required.
      - `/proc/2575365/environ`: no `GOOGLE_APPLICATION_CREDENTIALS` override present — the process can ONLY resolve
        via the well-known default ADC path, which is confirmed to be the WIF `external_account` config (not the old
        static-key JSON): `~/.config/gcloud/application_default_credentials.json`, `type: external_account`,
        `audience: .../workloadIdentityPools/aws-orchestrator-pool/...`.
      - **Direct GCP-dependent call, reproducing `agent-orchestrator/server/auth.py::_load_gcs_secret`'s EXACT code
        path** (`get_storage_client(provider="gcp", project_id=...).download_bytes(...)` against
        `gs://central-element-323112-orchestrator-creds/orchestrator/jwt-secret` — the same bucket/blob
        `ORCHESTRATOR_JWT_SECRET_GCS` points at) under the orchestrator's own venv: **succeeded, read 63 bytes.** (Note:
        this specific code path is currently short-circuited in the live deployment by the raw `ORCHESTRATOR_JWT_SECRET`
        env var also being set — `_load_secret()` returns early on `if raw: return raw` before ever calling
        `_load_gcs_secret` — so the orchestrator process itself hasn't actually exercised this GCP call since the
        restart; reproducing the identical call outside the process is the closest available direct proof.)
      - `gcloud secrets list --project=central-element-323112` (same ambient credential resolution, same host) also
        succeeded, returning real live secret names — re-confirms slot-6's original verification still holds post-cutover.
      - `journalctl -u orchestrator` since the restart: zero credential/GCP/exception errors in 9+ minutes of live
        runtime (33 tracked slots, successful dispatches including this task's own `/boot`) — if the ambient
        credential were broken, any GCS/Secret-Manager-touching code path (`gcs_sync.py`, `snapshot_recency.py`,
        `auth.py`) would have logged an exception; none did.
      **Done when met**: confirmed live, cited here. Repo: agent-orchestrator (host-level, `planning` VM) — no code
      diff, host/infra verification only.
- [x] ✅ [INFRA] P2. **Gated on the todo above landing**: once the live cutover to WIF is confirmed, formally revoke
      the old static SA key — **DONE 2026-08-16 (slot 22, infra)**. Re-verified the cutover FRESH before acting
      rather than trusting the prior checkbox's now-hours-old record: `orchestrator.service` had restarted AGAIN
      since that verification (new MainPID `2503824`, active since `22:36:29Z` — ~4h after the `18:46:18Z` restart
      the prior checkbox recorded), which is itself stronger evidence than before since it confirms the WIF
      credential survives a real restart, not just the one already observed. No `GOOGLE_APPLICATION_CREDENTIALS`
      override in the new process env; zero credential/GCP-auth errors in `journalctl -u orchestrator` across 57+ min
      of heavy fleet activity (dozens of slot spawns logged) on this new PID; ADC file still `type: external_account`
      (WIF, not reverted); a fresh `gcloud secrets list --project=central-element-323112` call succeeded on the
      ambient credential. Then ran the exact command this todo specified:
      `gcloud iam service-accounts keys delete 4af7b762c69e34eda225428a0979c039db4ad18a
      --iam-account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com --project=central-element-323112
      --quiet` — succeeded (`deleted key [...] for service account [...]`). Confirmed via
      `gcloud iam service-accounts keys list` that the key is now ABSENT (present pre-delete, gone post-delete; the
      SA's other 6 keys unaffected). Deleted the local backup file
      `~/.config/gcloud/application_default_credentials.json.static-key-backup.20260816T184438Z` per this todo's own
      instruction, only after the GCP-side revocation succeeded. Re-confirmed `orchestrator.service` still `active`
      and a live `gcloud secrets list` call still succeeds post-revocation — zero disruption. Repo: agent-orchestrator
      (host-level, `planning` VM) — no code diff; evidence here + the live GCP IAM key list is the artifact.
- [ ] [INFRA] P3. Investigate whether anything actually needs the separate static AWS IAM user credential
      (`ikenna-worker`, long-lived access key, in `~/.aws/credentials` on the `planning` VM) vs. the VM's own
      `uts-orchestrator-epic-role` instance-profile role — which the static key currently takes priority over in
      the AWS SDK's default credential chain — and retire the static key if not. **New finding, out of scope for
      this pass's WIF work** (independent risk; unaffected by and does not depend on the WIF fix above, which
      correctly targets the instance role, not this user key). No `[OPERATOR]` gate needed (task_template.md
      finding O(a)/U — self-justified: investigate-then-conditionally-retire, and if the audit half finds zero
      live callers depend on the static key, removing it is a safe, reversible cleanup since the instance role
      already provides equivalent access and the key can be recreated from IAM if ever needed). Corrected
      2026-08-19, plan-reconcile observability_master: rewrapped so the action, not just the meta-commentary,
      lands on this todo's first physical line (line-1 completeness, task_template.md §3). Done when: audit
      result stated + key retired-or-justified-kept. Repo: infra (host-level, `planning` VM).
- [x] ✅ [DATA] P1. Re-verified the chain relabel migration part 2 execution plan
      (`plans/active/cefi_chain_relabel_migration_options_futures_2026_08_15.md`) against live state — **still
      current**: every Phase 1 (UAC)/Phase 2 (MTDS) file:line citation individually checked against post-draft
      commits, all still accurate despite 4 intervening MTDS commits + 1 UAC-adjacent commit (none touched the cited
      chain-relabel code paths — see that plan's 2026-08-17 Progress Log for full per-commit evidence). **Dispatched
      execution**: flipped that plan's `assigned_vm: NA` → `planning` + added `sequential: true`, and closed a real
      `[OPERATOR]`-todo sequential-chain gap (`task_template.md` § 4 — a bare `sequential: true` chain skips a
      non-ingested `[OPERATOR]` todo when computing the predecessor) with an explicit dispatchable Phase-4 gate todo,
      so the oracle-narrowing step cannot dispatch before the Phase 3 backfill actually completes. Authored the
      required companion `cefi_chain_relabel_migration_options_futures_2026_08_15_finalize.md` (depends_on +
      gate_on_depends + sequential) per the mandatory finalize-plan hard rule. **Correction**: this todo's own
      `(repo: instruments-service)` tag was wrong — the plan touches none of instruments-service; its real repos are
      market-tick-data-service, unified-api-contracts, market-data-processing-service, deployment-api, deployment-ui
      (per that plan's own `repos:` frontmatter). — unified-trading-pm@93622e3714
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
- **2026-08-16 (slot 22, infra worker, AO-dispatched, this session runs ON the `planning` VM)**: Verified the live
  cutover todo. `orchestrator.service` had already naturally restarted since slot-6's cutover (Main PID 2575365,
  up since 18:46:18Z, ~1.5 min after the 18:44:38Z credential swap) — no manual restart or operator/sudo needed.
  Confirmed no stale `GOOGLE_APPLICATION_CREDENTIALS` override in the live process env, and reproduced
  `auth.py::_load_gcs_secret`'s exact GCS-read call under the orchestrator's own venv (succeeded, 63 bytes) — the
  strongest available direct proof, since that specific call is currently short-circuited in this deployment by the
  raw `ORCHESTRATOR_JWT_SECRET` env var also being set, so the live process hasn't itself exercised the GCS path
  since restarting. Cross-checked with a fresh `gcloud secrets list` (same ambient credential) and 9+ minutes of
  clean (0-exception) orchestrator logs. Next todo (revoke the old static SA key) is now unblocked for the
  dispatcher to pick up as its own separate task.
- **2026-08-16 (slot 22, infra worker, AO-dispatched, resumed session)**: Revoked the old static SA key. Did not
  trust the prior checkbox's verification alone — re-checked live and found `orchestrator.service` had restarted a
  SECOND time since then (new MainPID `2503824`, up since `22:36:29Z`), which is actually stronger evidence: the WIF
  credential now confirmed to survive a real restart, not just the one already on record. Zero credential/GCP-auth
  errors in the journal across 57+ min of heavy fleet activity on the new PID; ADC file still `external_account`; a
  fresh ambient-credential `gcloud secrets list` call succeeded. Ran the exact revoke command from the todo
  (`--quiet`, non-interactive); confirmed via a before/after `gcloud iam service-accounts keys list` diff that the
  target key id is gone and the SA's other 6 keys are untouched. Deleted the local backup file per the todo's own
  gating (only after GCP-side revocation). Re-confirmed `orchestrator.service` active + a live GCP call still
  succeeds post-revocation. Full evidence in the flipped checkbox above. Aside: found `unified-trading-ci` in this
  slot's worktree sitting on branch `main` (not `live-defi-rollout`) with one unpushed commit authored by a
  different slot (`slot-2·laptop`) — checked the content diff against `origin/main`'s tip and it's byte-identical
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
  (already landed upstream under a different SHA), so it's a harmless stale local artifact, not lost work; left
  untouched as out-of-scope for this task.
**context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
