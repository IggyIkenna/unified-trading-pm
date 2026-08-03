---
doc_type: issue
title: >-
  The orchestrator VM's shared gcloud active-account gets poisoned by GitHub Actions self-hosted-runner job steps,
  breaking every gcloud/gsutil call fleet-wide until manually repointed — third occurrence, same SA, one week apart
summary: >-
  On 2026-07-25 a worker slot's `gcloud compute instances stop` failed with "Unable to retrieve Identity Pool subject
  token: job is already completed" -- the same failure class documented in
  `vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md` and
  `gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md` (both filed the same day). Root cause,
  reconstructed via git history + the self-hosted-runner scripts: the planning VM is deliberately dual-purposed as both
  the AO worker host AND a GitHub Actions self-hosted runner pool for unified-trading-pm's "glue" CI (runs as the same
  `ubuntu` OS user, `HOME` deliberately not redirected -- `scripts/self-hosted-runners/README.md` explicitly accepts
  this as low-incremental-risk since "AO already runs as ubuntu with the same ambient creds"). Several glue workflows
  (`cloud-build-router.yml` among them) authenticate to GCP as `github-actions-deploy@central-element-323112` via
  job-scoped Workload Identity Federation. When such a job runs, its `google-github-actions/auth` step overwrites the
  SHARED `~/.config/gcloud` active account with a credential that cannot outlive the GitHub Actions job -- so any LATER
  shell on that same user (including an AO worker slot) inherits it as the active account and every subsequent
  gcloud/gsutil call fails. This exact mechanism already caused a 2.5-hour fleet-wide outage on 2026-07-18
  (`unified-trading-pm@e170e6ccf`/`52d8f234b`), whose fix isolated only the runner WRAPPER's own internal token calls
  into a private `CLOUDSDK_CONFIG`, explicitly NOT the workflow job steps themselves (rejected exporting the isolation
  to the environment: "would invite jobs to write their credentials INTO the private config"). It recurred exactly as
  predicted, one week later, via the untouched gap.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [gcp, gcloud, workload-identity-federation, self-hosted-runner, credentials, auth, recurring, orchestrator-vm]
related:
  [
    /plans/archive/issues/vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md,
    /plans/archive/issues/gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /codex/07-security/gha-wif-migration.md,
  ]
created: 2026-07-25
last_updated: 2026-08-01
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: devops
drift_direction: advance-code
depends_on: []
source: >-
  Hit live 2026-07-25 by a worker slot trying to stop a backfill VM (`gcloud compute instances stop
  af-backfill-20260725-032253`); root-caused this session by tracing the self-hosted-runner scripts + the 2026-07-18
  outage postmortem commits, cross-referenced against the two same-day sibling issue docs that hit the identical symptom
  via different call sites (gsutil upload, gcloud storage/compute create).
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/issues/vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md,
    /plans/archive/issues/gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /codex/07-security/gha-wif-migration.md,
    agent-orchestrator/scripts/bootstrap_vm.sh,
  ]
locked_since:
---

# gcloud active-account poisoning — WIF job steps overwrite the shared config (third hit, one week apart)

## What actually happened this time

A worker slot ran `gcloud compute instances stop af-backfill-20260725-032253 --zone=asia-northeast1-c` to stop a
backfill VM that was actively writing corrupted data (a separate, already-fixed bug —
`issues/api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md`). The command failed:

```
Unable to retrieve Identity Pool subject token: job is already completed
```

`gcloud auth list` showed the active account was `github-actions-deploy@central-element-323112.iam.gserviceaccount.com`
(a CI-only Workload Identity Federation service account) instead of `unified-trading-sa@central-element-323112` (the SA
every AO worker is provisioned with at VM boot, per `agent-orchestrator/scripts/bootstrap_vm.sh` STEP 5.5).

## Root cause

1. `agent-orchestrator@0febb19` (2026-05-29) establishes the intended baseline: every orchestrator VM authenticates as
   `unified-trading-sa@central-element-323112`, provisioned via a Secret Manager key (`ORCHESTRATOR_VM_GCP_ADC`) at
   boot, activated with `gcloud auth activate-service-account` + `gcloud config set account`.
2. `unified-trading-pm/scripts/self-hosted-runners/` (2026-07-15 onward) turns the SAME VM into a pool of GitHub Actions
   self-hosted "glue" runners for `unified-trading-pm`'s CI, running as the same `ubuntu` OS user with `HOME`
   deliberately NOT redirected (`README.md`: redirecting it "would break `$HOME/.config/gcloud` ADC resolution").
3. Several glue workflows (e.g. `cloud-build-router.yml`, `service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}` =
   `github-actions-deploy@central-element-323112`) call `google-github-actions/auth` when they run. That action writes a
   job-scoped `external_account` credential into `~/.config/gcloud` and makes it the CLI's active account. Because the
   credential's subject token comes from GitHub's own `actions-run-service` OIDC broker, it is valid ONLY for the
   lifetime of that specific job -- once the job ends, any later shell reading the same shared config inherits a
   credential that can never be refreshed.
4. This is not a new failure mode: `unified-trading-pm@e170e6ccf` documents this exact mechanism causing a 2.5-hour
   fleet-wide outage on 2026-07-18, and the very next commit (`52d8f234b`) confirms the specific poisoned SA
   (`github-actions-deploy@`). The fix shipped that day isolated the runner WRAPPER's own internal calls
   (`refresh-gh-token.sh`, `glue-runner-run.sh`) into a launcher-private `CLOUDSDK_CONFIG`, passed as a command prefix
   -- and explicitly did NOT extend that isolation to the workflow JOB STEPS themselves (rationale: "exporting
   `CLOUDSDK_CONFIG` would invite jobs to write their credentials INTO the private config, worse than the bug"). That is
   precisely the gap this incident fell through, one week later, for the same SA.
5. Two OTHER slots hit the identical symptom the SAME day via different call sites (`gsutil` in
   `create-code-tarballs.sh`'s upload step; `gcloud storage`/`gcloud compute instances create`) --
   `vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md` and
   `gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md`. A partial fix landed for the `gsutil` upload
   path specifically (`deployment-service@3ba14ff9`, rewired through UTL's ADC-backed `google-cloud-storage` client) --
   it does NOT touch bare `gcloud compute` calls, which remain exposed exactly as this incident shows.

## Why this is NOT an IAM/permissions problem (do not "fix" it with an IAM grant)

`unified-trading-sa` already holds every role it needs (`storage.objectAdmin`, `secretmanager.secretAccessor`,
`bigquery.dataEditor`, `pubsub.editor`, `run.invoker`, confirmed 2026-05-29). "Unable to retrieve Identity Pool subject
token" is an AUTHENTICATION failure -- the CLI cannot obtain a credential at all -- not an authorization (403) failure.
Granting more roles to either SA does nothing.

## The fix that unblocked this specific incident (not a durable fix)

On the VM: fetched the SA key fresh from Secrets Manager (`ORCHESTRATOR_VM_GCP_ADC`) and re-ran bootstrap's own
activation recipe:

```bash
GCP_SA_JSON=$(aws secretsmanager get-secret-value --secret-id ORCHESTRATOR_VM_GCP_ADC --query SecretString --output text)
printf '%s' "$GCP_SA_JSON" > ~/.config/gcloud/application_default_credentials.json
gcloud auth activate-service-account --key-file=~/.config/gcloud/application_default_credentials.json --project=central-element-323112
gcloud config set account unified-trading-sa@central-element-323112.iam.gserviceaccount.com
```

Verified working (`gcloud auth print-access-token`, `gcloud compute instances list`) before the blocking VM stop was
re-attempted and succeeded. **This is a manual, one-shot repoint** -- it will be poisoned again the next time a glue
workflow job step runs `google-github-actions/auth` on this host, which happens routinely (CI runs constantly).

## Todos

- [ ] [OPERATOR-DECISION] P1. Decide the durable direction. Candidates, none adopted yet: (a) extend the 2026-07-18
      fix's `CLOUDSDK_CONFIG` isolation to wrap the WORKFLOW JOB STEPS too, not just the runner wrapper's internal calls
      (the exact thing that fix explicitly declined to do, for a stated reason -- re-evaluate whether that reason still
      holds); (b) move `unified-trading-sa`'s activation to a NON-shared location (e.g. a dedicated
      `GOOGLE_APPLICATION_CREDENTIALS` env var pointed at a private key file that AO code always references explicitly,
      never relying on `gcloud`'s ambient active-account resolution at all); (c) stop dual-purposing this VM as a
      self-hosted runner pool (moves the runners elsewhere, removes the collision entirely, likely the highest-cost
      option); (d) a periodic self-heal cron that detects the poisoned account (compares
      `gcloud config get-value account` against the expected SA) and silently repoints it, treating poisoning as an
      accepted, self-correcting condition rather than eliminating the collision.
- [ ] [BACKEND] P2 (blocked on the decision above). Implement the chosen direction + a way to verify it holds under a
      real glue-workflow CI run, not just a synthetic test.
- [ ] [BACKEND] P3. Extend the `deployment-service@3ba14ff9` ADC-backed-client fix pattern to bare `gcloud compute`
      calls used by AO workers (VM stop/start/create), not just the `gsutil` upload path -- or at minimum, document the
      `CLOUDSDK_AUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)` per-command workaround (already
      proven working for `gcloud storage`/`gcloud compute instances create` per the sibling issue doc) as the sanctioned
      stopgap for any `gcloud compute` call until (a)-(d) above lands.

## Notes

- Did not attempt any of options (a)-(d) myself -- this is a shared-infrastructure auth design decision affecting every
  CI job that runs on this host, not a narrow bugfix.
- The VM stop this incident was blocking on succeeded once the manual repoint above completed; no data-correctness
  impact from the auth failure itself (the underlying VM-stop urgency was about a separate bug, not this one).
- **2026-07-30 corroborating evidence (slot-15)**: hit this exact mechanism THREE times in one session while running
  `gcloud compute instances create/delete/list` for `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`'s VM
  fleet recovery — each time `gcloud config get-value account` showed a poisoned account instead of
  `unified-trading-sa`. Two occurrences were `github-actions-deploy@...` (matches this doc); the THIRD was a **different
  SA, `github-deploy@central-element-323112.iam.gserviceaccount.com`** — a second glue-workflow identity poisoning the
  shared config the same way, not previously named in this doc's root-cause section (worth checking which workflow's
  `service_account:` maps to `github-deploy` vs `github-actions-deploy` when scoping fix option (a)).
  `gcloud config set account unified-trading-sa@...` fixed it each time (this incident's stopgap, not the
  activate-service-account recipe — the ADC key/token itself was never invalid in my case, only the active-account
  pointer). Did not hit the todo-3 `CLOUDSDK_AUTH_ACCESS_TOKEN` per-command stopgap this session; a bare
  `gcloud config set account` sufficed each time (worth noting as a lighter-weight alternative fix for the
  active-account-pointer-only poisoning case, vs. the todo-3 workaround's presumed scope of a fully invalid/expired
  credential).
- **2026-07-30 follow-up (slot-15, same session, later cycle)**: hit a FOURTH occurrence, and it is qualitatively worse
  than the three above — `gcloud config configurations list` showed the system-wide active configuration had flipped
  from this slot's own `slot15-work` to a DIFFERENT slot's isolated config, `slot11-work` (not just `default`). AND,
  separately, `slot15-work` itself was found with its stored `account` mutated to `github-deploy@…` (not
  `unified-trading-sa@…`). This means the earlier working hypothesis — "give each slot its own named config and the
  isolation holds" — is disproven with direct evidence: a foreign CI job or another slot's session mutated a DIFFERENT
  slot's named-config account property, not just the shared `default`/active-selector. Whatever writes
  `gcloud config set account` (or edits the underlying `~/.config/gcloud/configurations/config_*` files directly) is not
  scoped to the invoking job's own config file. Fixed via `gcloud config configurations activate slot15-work` +
  `gcloud config set account unified-trading-sa@…`. This raises the priority of option (a)/(d) in the head todo —
  per-slot config isolation (already deployed) is NOT a sufficient mitigation on its own.

- **2026-08-01 corroborating evidence (slot-2, infra role)**: hit this exact mechanism (active account poisoned to
  `github-actions-deploy@central-element-323112.iam.gserviceaccount.com`) mid-session while doing live-verification work
  for `bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md`'s P0 IAM-condition fix — a
  `gcloud config get-value account` check earlier in the same session confirmed `unified-trading-sa` was active (used
  successfully for a `tofu apply` and two IAM grants), then a later
  `gcloud iam service-accounts remove-iam-policy-binding` call failed with `PERMISSION_DENIED` under
  `github-actions-deploy`'s identity — the flip happened with zero action from this session, consistent with a
  concurrent glue-workflow job step (or another slot) overwriting the shared `~/.config/gcloud` state, as this doc's
  root cause describes. Fixed via explicit `--account=` on the two blocked `gcloud` calls (pinning the identity
  per-invocation rather than correcting the shared active pointer) — both reverts then succeeded first try. This is a
  lighter-weight variant of the todo-3 stopgap already proven for `gcloud storage`/`gcloud compute instances create`
  (`CLOUDSDK_AUTH_ACCESS_TOKEN=...`): a bare `--account=` flag sufficed here because the underlying credential for
  `unified-trading-sa` was never invalidated, only the ambient active-account pointer was overwritten (same shape as the
  2026-07-30 slot-15 finding that a bare `gcloud config set account` was enough when the key itself stayed valid). No
  data-correctness or fix-quality impact — the actual terraform apply + IAM-policy reads that mattered for that task ran
  while the correct identity was still active, confirmed at the time via an explicit account check. 5th documented
  occurrence; still consistent with the open `[OPERATOR-DECISION]` gate, no new candidate direction — logged as further
  frequency evidence only.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — the head todo carries an explicit
`[OPERATOR-DECISION]` tag and enumerates four unadopted candidate directions (a)-(d) for a shared-infrastructure auth
design affecting every CI job on the host; the doc's own Notes confirm none was attempted for exactly that reason. Todo
2 is stated blocked on that decision, and todo 3 is a partial mitigation of the same surface.

**na-eligibility-audit 2026-07-31** (tranche `ci`, autonomous): **CONFIRMS the verdict above, unchanged — new evidence
reinforces rather than weakens it.** Two purely-additive Notes landed since: a THIRD occurrence (2026-07-30 13:41)
naming a second poisoning SA variant not previously identified, and a FOURTH occurrence (2026-07-30 16:12) that is
qualitatively worse — cross-slot poisoning where a foreign job flipped another slot's active config AND mutated its
stored `account` property, directly disproving the working hypothesis that per-slot config isolation alone mitigates
this. Neither commit touched the Todos section; the commit message itself states this "raises priority of options
(a)/(d)" in the still-open `[OPERATOR-DECISION]` todo. This is new information feeding the same unresolved decision, not
progress toward a mechanical fix — correctly stays NA, no reclassification. (Doc-hygiene: `last_updated:` frontmatter
corrected below, was stale at `2026-07-25` despite the two 2026-07-30 body edits.)

**na-eligibility-audit 2026-08-02** (tranche `ci`, autonomous): **CONFIRMS the verdict above, unchanged — the one new
edit is additive evidence, not progress.** This doc was in scope this run because `last_updated` advanced to 2026-08-01;
the change is a single new Notes entry recording a **5th** documented occurrence (slot-2, infra role, mid- session
poisoning to `github-actions-deploy@…` during unrelated IAM work, worked around with a per-invocation `--account=` pin).
That entry explicitly self-classifies as "no new candidate direction — logged as further frequency evidence only", and
the Todos section is untouched. The head todo still carries `[OPERATOR-DECISION]` with four unadopted directions (a)-(d)
for a shared-infrastructure auth design affecting every CI job on the host; todo 2 is still stated blocked on that
decision; todo 3 is still a partial mitigation of the same surface.

## Progress Log (context-scout)

- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged from prior scout — still accurate: the 2
  sibling same-day incident docs, the 2 codex SSOTs the root-cause section cites, and `bootstrap_vm.sh` STEP 5.5).
  Correctly NA.
