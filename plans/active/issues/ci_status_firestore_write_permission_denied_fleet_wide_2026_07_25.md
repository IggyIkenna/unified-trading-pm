---
doc_type: issue
title:
  "ci_status Firestore writer (`unified-trading-sa`) is 403 PermissionDenied fleet-wide — SIT-gated LDR→main promotion
  silently stalled for every ldr_main repo"
summary: >-
  `ci-status-update.yml` (`unified-trading-pm`) has been failing 100% of the time since at least 2026-07-25T10:36Z (last
  observed success) with `google.api_core.exceptions.PermissionDenied: 403 Missing or insufficient permissions` on the
  Firestore transaction write to `ci_status/{repo}`. Reproduced live from the same self-hosted-runner ambient ADC
  identity (`unified-trading-sa@central-element-323112.iam.gserviceaccount.com`) via a direct REST PATCH — same 403.
  Because `sit_validated_tree` (the fleet's `ldr-to-main-promote-fleet.yml` SIT gate input) is written ONLY by this
  workflow, EVERY SIT-covered repo (21 repos, incl. `deployment-api`, `agent-orchestrator`, `unified-trading-library`,
  `instruments-service`, …) whose promote gate needs a fresh SIT stamp is now fail-CLOSED and re-dispatching
  `full-workspace-sit` on every ~5 min tick with zero forward progress — the SIT jobs themselves pass and log `"stamped
  SIT_VALIDATED <repo> @ <sha> (tree ...)"`, but that log line only reflects a successful `repository_dispatch` POST
  (fire-and-forget), not a successful downstream Firestore write, so the fleet has been silently believing SIT
  validation is landing when it is not.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, firestore, ci_status, promote-gate, sit-gate, permissions, fleet-wide, incident]
related:
  [
    deployment_registry_reaper_not_draining_stale_entries_2026_07_24,
    sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20,
  ]
created: 2026-07-25
priority: P0
parent_epic: infrastructure_master
source:
  "discovered 2026-07-25 (slot 5, infra) while chasing why deployment-api's LDR→main promote of a fix-carrying digest
  bump stayed SIT-gate-blocked despite a SIT run completing and logging success."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by: slot-3 (infra), 2026-07-25
---

# ci_status Firestore writer is 403'ing fleet-wide (2026-07-25)

## What I found

Working `deployment_registry_reaper_not_draining_stale_entries-002` (re-verify a deployment-api fix now that its
base-image digest was refreshed and pushed to LDR@`108e2fd`), the LDR→main promote kept SIT-gate-BLOCKing with the SAME
stale `sit_validated_tree` across three consecutive manual `ldr-to-main-promote-fleet.yml` triggers (13:46, 13:54,
13:57), even though a `full-workspace-sit` run (`system-integration-tests` run `30160408041`) completed successfully at
13:52 and logged `"stamped SIT_VALIDATED deployment-api @ 0badf575... (tree c2bd5b9c...)"` — the exact tree the promote
gate was waiting for.

Traced the gap:

1. `full-workspace-sit.yml`'s stamp step (`system-integration-tests/.github/workflows/full-workspace-sit.yml:158-175`)
   is fire-and-forget: it POSTs a `ci-status-update` `repository_dispatch` to `unified-trading-pm` and echoes
   `"stamped SIT_VALIDATED ..."` purely because the `curl` HTTP call succeeded — it never checks whether the downstream
   workflow run actually completes, let alone whether its Firestore write succeeds.
2. Read the LIVE Firestore doc directly (`GET .../documents/ci_status/deployment-api` via REST):
   `updateTime: 2026-07-25T07:00:30Z` — over 7 hours stale, `sit_validated_tree` still the OLD value (`2584a2d8...`),
   confirming the 13:52 stamp never actually landed.
3. `gh run list --repo IggyIkenna/unified-trading-pm --workflow=ci-status-update.yml` shows the dispatched runs queuing
   up (self-hosted glue-writer-pool capacity) and then **ALL failing** — sampled 100 recent runs: 95 `failure`, 0
   `success`, earliest failure in that window `2026-07-25T13:48:04Z`. Paginated further back: the **last successful run
   was `2026-07-25T10:36:47Z`** — i.e. this has been broken for **at least ~3.5 hours** before discovery, likely longer
   (100-run window doesn't reach further back at this dispatch volume).
4. Every sampled failure has the SAME traceback:
   `google.api_core.exceptions.PermissionDenied: 403 Missing or insufficient permissions` inside
   `ci_status_store.py::set_status`'s Firestore transaction (`client.transaction()` → `begin_transaction`). The job runs
   on the self-hosted glue-writer pool and relies on **ambient ADC**
   (`~/.config/gcloud/application_default_credentials.json`, SA
   `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`) — the per-run `google-github-actions/auth@v3`
   step was deliberately DROPPED for this job on 2026-07-17 (comment in `ci-status-update.yml`: "PROBED on the box
   before dropping ... Firestore write+read+delete OK").
5. **Reproduced independently, live, from this session** (same box, same ADC identity) via a direct Firestore REST
   `PATCH` to `ci_status/_probe_slot5` using `gcloud auth application-default print-access-token` (confirmed via
   `tokeninfo` to be minted for `unified-trading-sa`'s `client_id`, not a different active gcloud account): **same
   `403 PERMISSION_DENIED`**. So this is not runner-flakiness or a stale/expired individual CI run — the SA itself
   currently lacks the Firestore write permission it had when probed on 2026-07-17. Root cause NOT further diagnosed —
   reading the SA's current IAM bindings requires `resourcemanager.projects.getIamPolicy`, which neither of this
   session's two active gcloud identities (`github-actions-deploy@...`, and `ikenna@odum-research.com` — reauth failed
   non-interactively) could exercise here. Candidate causes, not verified: (a) a `roles/datastore.user` (or equivalent)
   binding was removed/replaced for this SA in an unrelated IAM cleanup; (b) an org-policy or VPC-SC change scoped
   Firestore access; (c) the ADC key file on the runner box is stale/rotated out from under a live SA key rotation.
6. Side-effect also observed (separate symptom, same box, NOT yet confirmed same root cause): the
   `cloud-build-router.yml` "Persist CI/CD event" step's `gsutil cp` GCS write also failed ("Your credentials are
   invalid. Please run `$ gcloud auth login`") in an UNRELATED run (`unified-trading-pm` run `30159646779`, 13:24:19Z) —
   a DIFFERENT symptom (gcloud CLI creds, not ADC) on what may be the same or a sibling self-hosted runner. Flagging as
   a possible second data point for the same underlying credential/IAM incident, not confirmed to share a root cause.
   **RESOLVED (slot 6, 2026-07-25T14:xx): does NOT share this incident's root cause.** Evidence: (a) different SA —
   `cloud-build-router.yml`'s `route-build` job authenticates via `google-github-actions/auth@v3` WIF to
   `execution-service-sa@central-element-323112.iam.gserviceaccount.com` (`GCP_SERVICE_ACCOUNT` secret, per
   `/codex/07-security/gha-wif-migration.md`), NOT `unified-trading-sa` (this doc's affected SA, ambient ADC, no per-run
   auth step). (b) different failure signature — "Your credentials are invalid. Please run `$ gcloud auth login`" is
   `gsutil`'s classic parse failure on a WIF-issued `external_account` credential file (the legacy Python `gsutil`
   binary frequently can't consume short-lived WIF tokens the way `gcloud storage`/native SDK calls can — same failure
   class independently documented in
   `plans/active/issues/vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md` for a different workflow),
   NOT Firestore's `403 PermissionDenied` (an IAM-binding-missing signature). (c) different onset — the `gsutil` failure
   reproduces as far back as run `30094405633` (2026-07-24T12:48:27Z, over 22h before this incident's earliest observed
   Firestore failure at 2026-07-25T10:36Z) and is STILL reproducing on the latest `cloud-build-router.yml` run as of
   2026-07-25T14:03:14Z (well after this incident began) — a pre-existing, continuously-failing, unrelated tooling
   issue, not a new symptom of this SA's permission change. The step has `continue-on-error` semantics (job conclusion
   stays `success` despite the internal gsutil failure), which is why it silently persisted this long. Filed as its own
   follow-up:
   `[INFRA] P3. cloud-build-router.yml's "Persist CI/CD event" gsutil call fails under WIF auth for execution-service-sa — switch to \`gcloud
   storage cp\` or otherwise make WIF-compatible (repo: unified-trading-pm)` — separate from this incident's remediation
   chain.
7. Cross-ref: `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` documents a DIFFERENT failure mode
   on the same `sit_validated_tree` gate (a breaking-delta repo needs LDR quiescent across a full SIT round-trip, or the
   fingerprint never matches the moving tip) — that doc predates this incident and its root cause (SIT round-trip
   timing) is distinct from this one (Firestore write 403). Flagging only because BOTH manifest as "SIT gate never
   satisfies, repo re-dispatches SIT forever" from the outside — a future diagnosis of a stuck promote should check THIS
   doc's `ci-status-update.yml` run history first (cheap: `gh run list --workflow=ci-status-update.yml`) before assuming
   the treadmill's slower LDR-quiescence cause applies. SSOT for the `ci_status` Firestore-SSOT design:
   `/codex/08-workflows/ci-cd-flow.md`.

## Why it matters

- **Every SIT-covered `ldr_main` repo's promotion from LDR to `main` is silently stalled.** The promote gate design
  explicitly fails CLOSED on a missing/stale `sit_validated_tree` (correct, conservative behavior) — but the SIT stamp
  step's fire-and-forget logging makes the fleet BELIEVE stamps are landing, so nobody would notice this without
  directly reading the Firestore doc's `updateTime`, exactly as done here. This is the same failure CLASS as the earlier
  `unified-trading-library-prod` Cloud Build trigger incident
  (`utl_prod_cloud_build_trigger_missing_fleet_stale_base_image_2026_07_25.md`) — a downstream step silently swallowing
  a real failure behind an apparently-green log line.
- Directly blocking my current task (`deployment_registry_reaper_not_draining_stale_entries-002`): the `deployment-api`
  gunicorn/reaper P0 fix chain (`deployment-api@3fea307` → digest refresh `108e2fd`) is fix-complete on LDR but cannot
  reach `main`/Cloud Run until this clears.
- Per CLAUDE.md's "Data pipeline correctness is the heartbeat" / SSOT-contradiction escalation rule, a fleet-wide CI/CD
  promotion stall silently masquerading as healthy is a NOTIFY-OPERATOR-grade finding, not a routine backlog item.

## Recommended decision

1. **[OPERATOR]** Diagnose + restore `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`'s Firestore
   write permission (likely `roles/datastore.user` on project `central-element-323112`, or whatever role covers
   `ci_status` — grep `ci_status_firestore_side_store_2026_06_10.md` for the originally-granted role) — this needs
   `resourcemanager.projects.getIamPolicy`/`setIamPolicy`, which this session's identities don't have. Cross-check the
   ADC key file on the affected self-hosted runner box(es) hasn't silently rotated out from under a live SA key
   rotation.
2. **[INFRA]** Once permissions are restored, verify `ci-status-update.yml` runs go green again
   (`gh run list --workflow=ci-status-update.yml` — expect `success`, not `failure`), then confirm `deployment-api`'s
   `sit_validated_tree` Firestore field actually advances to `c2bd5b9c...` (or the LDR tree current at fix time).
3. **[INFRA]** Harden `full-workspace-sit.yml`'s stamp step (`:158-175`) so it stops declaring success purely from the
   `curl` HTTP-accept — either poll the dispatched `ci-status-update` run to a terminal state before echoing "stamped",
   or have `ci-status-update.yml` itself post a `sit-stamp-failed` signal back (mirrors the existing "Report SIT result
   to PM" step already in the same file) so a downstream Firestore-write failure surfaces as a page instead of a silent
   no-op. This is the same "verify the write, don't trust the HTTP-accept" lesson as the Cloud Build trigger incident.
4. **[INFRA]** Once (1)-(3) land, re-run `deployment_registry_reaper_not_draining_stale_entries-002`'s remaining chain:
   confirm `deployment-api`'s promote PR (past #377) merges to `main`, a fresh Cloud Build + Cloud Run revision deploys,
   then re-verify `active/` convergence per that issue doc's Todo 5.

## Todos

- [x] ✅ [OPERATOR] P0. Diagnose + restore Firestore write permission for
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` on project `central-element-323112` (reproduce
      via `gcloud auth application-default print-access-token` + a direct Firestore REST `PATCH` from the affected
      self-hosted runner box; confirmed 403 as of 2026-07-25T14:02Z). Check IAM bindings + any recent SA key rotation. —
      resolved by operator; last `ci-status-update.yml` failure observed 2026-07-25T14:11:52Z, first green run
      2026-07-25T14:26:07Z (verified below).
- [x] ✅ [INFRA] P0. Once permissions restored, verify `ci-status-update.yml` (unified-trading-pm) runs green again and
      `ci_status/deployment-api`'s `sit_validated_tree` advances to the current LDR tree (repo: unified-trading-pm). —
      verified live 2026-07-25T14:3xZ: `gh run list --workflow=ci-status-update.yml --limit 50` → 50/50 `success`
      (oldest in window 14:26:07Z, zero failures). `full-workspace-sit.yml` run `30161571001` (using the now-hardened,
      poll-verified stamp step from todo 3) logged
      `stamped SIT_VALIDATED deployment-api @ 0badf575...     (tree c2bd5b9cec217433a63ec7d5dbcceefa5554ccdb)`; the
      dispatched `ci-status-update.yml` run `30161733363` (`conclusion=success`) confirmed in its own log it wrote
      `SIT_VALIDATED_TREE: c2bd5b9cec217433a63ec7d5dbcceefa5554ccdb` for `deployment-api` — the exact tree the promote
      gate was waiting for. (Note: my own session's ADC/SA impersonation of `unified-trading-sa` still 403s on a direct
      Firestore REST read — a narrower, separate permission gap from the runner's WIF-issued
      `google-github-actions/auth@v3` credential; not blocking since the CI run logs themselves are authoritative proof
      the write landed.)
- [x] ✅ [INFRA] P1. Harden `full-workspace-sit.yml`'s stamp step
      (`system-integration-tests/.github/workflows/full-workspace-sit.yml:158-175`) to not declare "stamped
      SIT_VALIDATED" success from a bare `curl` HTTP-accept — verify the downstream `ci-status-update` run actually
      completes + writes, or surface failure loudly (repo: system-integration-tests). —
      system-integration-tests@422baa9: per-repo stamp loop now snapshots existing `ci-status-update.yml` run IDs before
      dispatch, confirms the dispatch POST itself returned HTTP 204, polls (~30s) for the NEW run the dispatch created,
      then polls (~90s) that run to a terminal status — only echoes "stamped SIT_VALIDATED" on `conclusion=success`; a
      failed/timed-out/unidentifiable run emits `::error::` and fails the step (`exit 1`) instead of silently claiming
      success. `quality-gates.sh` green (112s); YAML + embedded bash syntax verified (`python3 -c yaml.safe_load` +
      `bash -n` on the extracted step script).
- [x] ✅ [INFRA] P2. Investigate whether the `cloud-build-router.yml` "Persist CI/CD event" gsutil credential failure
      (run `30159646779`, 13:24:19Z, "Your credentials are invalid") shares a root cause with this incident — same or
      sibling self-hosted runner box (repo: unified-trading-pm). — RESOLVED, does NOT share root cause: different SA
      (`execution-service-sa` via WIF vs `unified-trading-sa` via ambient ADC), different failure signature (gsutil
      WIF-credential parse failure vs Firestore 403 PermissionDenied), different onset (reproduces back to
      2026-07-24T12:48Z, 22h before this incident began, and still reproducing after — pre-existing unrelated tooling
      issue). Full evidence in "What I found" item 6 above. Follow-up filed as new todo below.
- [x] ✅ [INFRA] P3. `cloud-build-router.yml`'s "Persist CI/CD event" step's `gsutil cp` GCS write fails under WIF auth
      for `execution-service-sa@central-element-323112.iam.gserviceaccount.com` ("Your credentials are invalid. Please
      run `$ gcloud auth login`") — pre-existing since at least 2026-07-24T12:48Z (run `30094405633`), still failing as
      of 2026-07-25T14:03Z (run `30160874407`); `continue-on-error` hides it from the job conclusion. Switch to
      `gcloud storage cp` (native ADC/WIF support) or otherwise make the `persist-event` composite action's gsutil call
      WIF-compatible (repo: unified-trading-pm, `.github/actions/persist-event`). — unified-trading-pm@309fc5348:
      swapped `timeout 60 gsutil cp - "$GCS_URI"` for `timeout 60 gcloud storage cp - "$GCS_URI"` in
      `.github/actions/persist-event/action.yml` (same stdin-source syntax — `gcloud storage cp --help` confirms `-`
      reads file content from stdin, a drop-in swap). Reproduced the bug live on this box first
      (`gsutil ls -b gs://unified-trading-cicd-events` → "Your credentials are invalid. Please run
      `$ gcloud auth login`", same signature) then confirmed the fix direction (`gcloud storage buckets     describe`
      succeeded using the SAME ambient credentials) before shipping. End-to-end verified the exact stdin-cp pattern
      against the real bucket: wrote a probe object via `gcloud storage cp -` and read it back with matching content
      (`gs://unified-trading-cicd-events/cicd/events/_verification_probe/1784989225-probe.jsonl`) — left in place
      (harmless, isolated, non-canonical prefix) since single-object GCS deletes are guardrail-blocked for this role.
      `quality-gates.sh` green (sentinel-verified); shipped via quickmerge → PR #1508 (auto-merge to main).

## Progress Log

- **2026-07-25T14:1xZ (slot 7, infra) — todo 2 dispatched, still BLOCKED on todo 1.** Re-confirmed live, fresh: (a)
  `gh run list --repo IggyIkenna/unified-trading-pm --workflow=ci-status-update.yml --limit 10` — all 10 most recent
  runs `failure` (latest `2026-07-25T14:11:52Z`); (b) direct Firestore REST `GET .../ci_status/deployment-api` via
  `gcloud auth application-default print-access-token` (same ADC identity the issue doc used) → `403 PERMISSION_DENIED`,
  unchanged. Todo 1's `[OPERATOR]` precondition has NOT been met yet — todo 2's own text is "once permissions restored",
  which isn't true right now, so there is nothing for an INFRA worker to verify. Skipping todo 2 (GATED) rather than
  forcing it; todo 3 (harden `full-workspace-sit.yml`'s stamp step) is independently actionable NOW (does not depend on
  todo 1) and is a legitimate separate INFRA P1 pickup.
- **2026-07-25T14:xxZ (slot 6, infra) — todo 4 resolved: does NOT share this incident's root cause.** Also parked todo 2
  the same way (BLK-d5ab20de, main confirmed A: skip until operator restores IAM). For todo 4, pulled both
  `cloud-build-router.yml`'s WIF-authenticated SA (`execution-service-sa`, per `/codex/07-security/gha-wif-migration.md`
  - this run's own `Authenticate to GCP via WIF` step) and the `gsutil` failure's onset (confirmed via direct job-log
    API pull on runs `30094405633` 2026-07-24T12:48Z, `30155923766` 2026-07-25T11:15Z, `30159646779` 13:24Z,
    `30160874407` 14:03Z — same "Your credentials are invalid" signature on every one, spanning >22h before AND after
    this incident's 10:36Z onset). Two independent SAs, two independent auth mechanisms (WIF vs ambient ADC), two
    independent failure signatures, non-overlapping timelines — conclusively unrelated. Filed the gsutil/WIF
    incompatibility as its own P3 follow-up todo (this doc) rather than a new issue doc, since it's already scoped and
    tracked here. Full evidence added to "What I found" item 6.
- **2026-07-25T14:3xZ (slot 3, infra) — todos 1+2 verified live; ALL TODOS NOW COMPLETE, closing as resolved.** Operator
  restored the Firestore write permission for `unified-trading-sa` (last failure `2026-07-25T14:11:52Z`, first green run
  `14:26:07Z`). Verified: (a) `gh run list --workflow=ci-status-update.yml --limit 50` → 50/50 `success`, zero failures
  since restore; (b) `full-workspace-sit.yml` run `30161571001` used the hardened poll-verified stamp step (shipped as
  todo 3) and logged a genuine (not fire-and-forget)
  `stamped SIT_VALIDATED deployment-api @ 0badf575... (tree c2bd5b9cec217433a63ec7d5dbcceefa5554ccdb)`; (c) the
  dispatched `ci-status-update.yml` run `30161733363` (`conclusion=success`) confirmed in its own log body it wrote
  `SIT_VALIDATED_TREE: c2bd5b9cec217433a63ec7d5dbcceefa5554ccdb` for `deployment-api` — matching the tree the promote
  gate needed. Todo 4 was already shipped by a prior slot (unified-trading-pm@309fc5348). All 4 todos now `[x]`;
  flipping doc `status: resolved`. Remaining follow-up (todo 4 of the "Recommended decision" list — re-verify
  `deployment_registry_reaper_not_draining_stale_entries-002`'s remaining chain now that the SIT gate is unblocked) is
  tracked in that issue doc, not this one.
