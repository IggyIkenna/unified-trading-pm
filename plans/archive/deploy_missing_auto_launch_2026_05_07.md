---
doc_type: plan
title: deploy_missing_auto_launch_2026_05_07
summary: Successor plan to data_status_drilldown_shard_atom_alignment_2026_05_07 Phase 3 -- promote the Deploy-Missing flow
  from preview-mode (operator copies + runs the gcloud command) to auto-launch (deployment-api directly invokes the launcher
  script via gcloud). Requires deployment-api->gcloud security review + paired tarball-refresh wiring + per-VM observability
  + idempotency guards.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-api, deployment-service, deployment-ui, instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: [/plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md]
created: "2026-05-07"
type: code
epic: epic-deployment
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - { repo: deployment-api, code: C2, deployment: D3, business: none }
  - { repo: deployment-service, code: C2, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C2, deployment: none, business: none }
depends_on: [data_status_drilldown_shard_atom_alignment_2026_05_07.md]
todos: []
isProject: false
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7.2
estimate_calibration_note: "Backfilled 2026-05-13: 14 todos, 6 done; 8 remaining covering deployment-api→gcloud
  auto-launch endpoint + tarball-refresh wiring + IAM/audit + per-VM observability + idempotency guards. infra class
  (real auto-launch surface, security review). Baseline 9 (~1.1 AI-day per remaining infra todo); × 0.8 = 7.2.

  "
---

> **ARCHIVED 2026-05-19** — 100% complete (all checkboxes checked); preserved for archaeology.

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# Deploy-Missing auto-launch (preview -> auto)

> **🟢 FOLD-IN CONFIRMED — RATIFIED 2026-05-10 cross-plan audit L3.** This plan **stays as an independent implementation
> surface** (Phases 0-4 own concrete tarball-refresh + auto-launch endpoint + IAM/audit-log details);
> [`deployment_ui_lifecycle_tabs_2026_05_08.md`](deployment_ui_lifecycle_tabs_2026_05_08.md) is the **UI umbrella** that
> exposes this plan's runtime-execution surface. The two plans coexist by ownership split: lifecycle-tabs owns _UI tab
> structure + auth-flow re-shape_; this plan owns _endpoint + tarball + auto-launch backend_. Cross-references between
> both plans stand; neither absorbs the other.

> **Fold-into-umbrella banner 2026-05-08**: this plan's Phase 1+2 (tarball-refresh + auto-launch endpoint) is a child of
> the [`deployment_ui_lifecycle_tabs_2026_05_08`](deployment_ui_lifecycle_tabs_2026_05_08.md) umbrella per the
> 2026-05-08 audit (Crit 6 GAP — completion-pointer). Per the umbrella's plan body, the Deploy-Missing auto-launch is
> the runtime-execution surface that the lifecycle-tabs UI exposes via the new LiveDataStatusTab
>
> - cloud-toggle + auth-flow re-shape. Phase 0 (operator IAM/audit-log/rate-limit decisions) is owned by Ikenna's
>   daily-split Tab 5 ([`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) §"TAB 5"); Phase 1+2
>   implementation is owned by Harsh's daily-split Tab 3
>   ([`work_split_2026_05_08_harsh.md`](work_split_2026_05_08_harsh.md) §"TAB 3").

## Open questions

### Q1 — [deploy-missing-iam-proposal-tab, 2026-05-08 07:30 UTC] — Push blocked: 2 incoming on origin/live-defi-rollout

**Status**: ✅ RESOLVED — main rebased the local stack cleanly (zero file overlap with the 2 incoming). Tab 13's commits
are now `6d44c73` + `fdc0bb9` (rebased SHAs); push will go through in main's next push (this commit). Tab 13 going quiet
per spawn protocol; no further action needed.

PM origin/live-defi-rollout advanced by 2 commits (`98f1e16` plan(work_split): codify UAC chain_env.py SSOT handshake,
`6e952b6` docs(plans): file issue 13 — hardcoded on-chain-derivable values) while Tab 13 was drafting the proposal
section. My local commit landed at `1f0ad01` on top of `33d56f8` which is now 2 behind origin; fast-forward to origin is
clean (origin only moved forward, no diverged history when I started). Per Bootstrap § "Push discipline"
conditional-push rule I have NOT pushed. Recommended resolution: rebase the single proposal-doc commit onto
`origin/live-defi-rollout` (`git fetch origin live-defi-rollout && git rebase origin/live-defi-rollout`) — the proposal
section only touches `plans/active/deploy_missing_auto_launch_2026_05_07.md` + `_agent_pings.md`, neither of which the 2
incoming commits modified, so the rebase should be trivial. Alternatively cherry-pick if main agent prefers a clean
linear history with the 2 incoming first.

## Operator decision summary

> **✅ STATUS: APPROVED 2026-05-08 — all 3 recommendations greenlit.** Decision 1 = **B + C combined** (custom role
> `roles/customDeployMissingLauncher` IAM-scoped to zone `asia-northeast1-c` + subnet `default` + image family
> `unified-trading-debian-12` + dedicated runtime SA, AND API-layer `_SERVICE_LAUNCHER_SCRIPTS` allow-listing). Decision
> 2 = **BigQuery primary + Cloud Logging mirror + GCS cold tier + sync-blocking write + 90d hot / 5y cold retention**.
> Decision 3 = **30/op/hr + 200/op/day + 100/proj/hr + 1 active per shard_key for 6h** rate ceilings, Firestore
> counters, alerts to `#uts-prod-alerts`. On-call: Ikenna primary / Harsh backup until cefi_ml live ≥7d. Phase 2 wiring
> is **UNBLOCKED**. See `plans/active/operator_decisions_2026_05_08.md` for the full pickup record.

> **Earlier status (preserved for archaeology)**: AWAITING OPERATOR SIGN-OFF — drafted 2026-05-08 by Tab 5 sub-agent F
> (`deploy-missing-phase0-facilitation`).

### Decision 1 — IAM scope

**Question:** Which IAM grant shape lets deployment-api invoke `gcloud compute instances create`?

**Options:**

- **A.** Blanket `roles/compute.instanceAdmin.v1` — full project-wide GCE lifecycle.
- **B.** Custom role `roles/customDeployMissingLauncher` with minimal permissions, IAM-condition-scoped to zone
  `asia-northeast1-c` + subnet `default` + image family `unified-trading-debian-12` + dedicated runtime SA
  `deploy-missing-vm-runtime@${PID}.iam.gserviceaccount.com`.
- **C.** API-layer per-launcher allow-listing via existing `_SERVICE_LAUNCHER_SCRIPTS` registry (additive,
  defence-in-depth).

**Recommendation:** **B + C combined** (NOT either-or). B is the IAM floor — Cloud Run SA literally cannot exceed the
custom role. C is the API-layer defence — endpoint short-circuits on unregistered launchers before `subprocess.run()`. C
is already 80% in place via the existing 9-entry `_SERVICE_LAUNCHER_SCRIPTS` dict at
`deployment-api/deployment_api/services/deploy_missing.py:62-72`.

**Blast radius (if B+C compromised):** VMs only in `asia-northeast1-c` on registered subnet/image, running as
low-privilege runtime SA. Cost capped by Decision 3's rate limits (~$25/hr project-wide max). Code-execution pivot
requires _also_ compromising Artifact Registry push (separate IAM surface, not granted here).

**Cross-references:** Phase 1 `tarball_staleness.py` requires `cloudbuild.builds.{create,get,list}` — already in B's
permission list. Phase 2 endpoint (line 489) gets the role binding. `VM_PREFIX_TO_BUCKET` in
`deployment-service/scripts/vm/vm_zombie_watchdog.py` must learn the new prefix `mtds-shard-key-` + watchdog VM relaunch
(workspace VM Naming Convention rule).

**Sign-off question:** Approve Option B + C combined as drafted (zone+subnet+image-family+runtime-SA scoping)? **Y/N**
If N, name the desired tightening (e.g. short-lived per-launch role bindings via Workload Identity Federation) or
loosening.

---

### Decision 2 — Audit-log shape

**Question:** What gets logged on every Deploy-Missing launch + where does it land + how long is it kept?

**Options:** Backend choice (BigQuery vs Cloud Logging vs GCS append-only) × retention window × write-failure policy
(synchronous-blocking vs fire-and-forget).

**Recommendation:** **BigQuery primary + Cloud Logging mirror + GCS cold tier**, with **synchronous-blocking write** on
the BigQuery path (no unaudited launches under any condition — endpoint returns 500 + does NOT spawn VM if BigQuery
insert fails).

- **Schema:** `DeployMissingAuditRecord` dataclass (full spec at lines ~289-338) — captures operator email/uid/auth
  method, source IP, request ID, full row*key + shard_key, launcher script path, decision enum (LAUNCHED / RATE_LIMITED
  / IDEMPOTENT_HIT / TARBALL_STALE_REFRESH / REJECTED*\*), tarball-refresh chain link, timing,
  `correlation_id = shard_key`.
- **Storage:** BigQuery table `${PID}.deploy_missing_audit.launches`, partitioned by `DATE(received_at)`, clustered on
  `(operator_uid, decision)`. Cloud Logging mirror (`severity=NOTICE`, log name `deploy-missing-audit`) for live tail.
  GCS cold tier (`gs://${PID}-audit-cold/deploy_missing/{YYYY}/{MM}/{DD}.jsonl`) via daily Cloud Scheduler → Cloud
  Function export.
- **Retention:** **90 days hot** (BigQuery partition expiration) + **5 years cold** (GCS object lifecycle) + 30 days
  Cloud Logging default. Matches institutional ops norms.

**Cross-references:** `correlation_id = shard_key` joins audit + `DEPLOY_MISSING_VM_LAUNCHED` event streams. Decision
update path: row inserted at request entry with `decision="LAUNCHED"`; if 90s STARTED-event wait times out, row gets
follow-up `decision="LAUNCHED_BUT_STALLED"` + `rejection_reason`. Rate-limit 429s also generate audit rows
(`decision="RATE_LIMITED"`) — captures attempted-but-rejected launches.

**Sign-off questions:**

1. Approve BigQuery primary + Cloud Logging mirror + GCS cold tier as drafted? **Y/N**
2. Approve 90d hot / 5y cold retention? **Y/N** — if a stricter compliance requirement applies (e.g. SOC2-specific),
   override the values.
3. Approve synchronous-blocking write policy (no unaudited launches)? **Y/N**

---

### Decision 3 — Rate-limit ceilings

**Question:** What ceilings cap launch frequency + what does the 429 response look like?

**Recommendation (starting points, recalibrate from observed P95 after a week of real traffic):**

| Scope                         | Limit    | Window | Rationale                                             |
| ----------------------------- | -------- | ------ | ----------------------------------------------------- |
| **Per-operator-per-hour**     | 30       | 1h     | 1 click every 2min sustained — generous for sweeps    |
| **Per-operator-per-day**      | 200      | 24h    | Daily rollover; protects against compromised account  |
| **Project-wide-per-hour**     | 100      | 1h     | Caps team-wide chain reaction                         |
| **Per-shard-key idempotency** | 1 active | 6h     | Same shard with running VM → return existing, not new |

**Cost vector:** MTDS backfill VM ≈ $0.50/hr (e2-standard-4) × ~30min/shard ≈ $0.25/launch. 100 launches/hr project
ceiling ≈ $25/hr absolute, $600/day worst-case-sustained. Compromised single-operator: capped at $7.50/hr.

**429 response shape:** JSON body with
`{error, scope, limit, current, window_start, window_end, retry_after_seconds, operator_email}` + headers `Retry-After`
/ `X-RateLimit-{Limit,Remaining,Reset,Scope}` always present (even on 200 OK, so UI can render "23/30 used this hour"
hints). Full JSON example at lines ~410-419.

**State backend:** Firestore at `/_state/deploy_missing_rate_limits/{operator_uid}_{hour_window}` +
`_project_{hour_window}` with 24h TTL. Multi-replica Cloud Run shares state via Firestore transactions (no in-memory
desync).

**Alert thresholds:** 80% of any per-hour ceiling → warn-level alert. Project-wide ceiling tripped 2x in 24h → page
on-call.

**Cross-references:** Phase 2 line 496 (`Rate limiter middleware`) is the implementation point. Per-shard-key
idempotency is **separate** from rate limit — first wins, second gets 200 OK with running VM's name + correlation_id,
neither counter-decrement.

**Sign-off questions:**

1. Approve 30/hr + 200/day per-operator + 100/hr project-wide ceilings + 6h per-shard-key idempotency as drafted?
   **Y/N**
2. Approve Firestore-backed counter state + multi-replica sharing? **Y/N**
3. Name the **Slack channel + on-call rotation** for the 80% + 2x-trip alerts (drafted as TBD pending operator pick).

---

## Why

Drilldown plan Phase 3 ships Deploy-Missing in **preview mode**: the operator clicks the button on a leaf shard,
deployment-api composes the surgical bash invocation
(`bash deployment-service/scripts/vm/launch-mtds-backfill-vm.sh --shard-key='cefi|BINANCE-FUTURES|trades|PERPETUAL|btcusdt|2024-03-04'`),
and the operator copies + runs from their own authenticated terminal. Same security boundary as today's manual
backfills.

The full UX -- one-click launch from the panel without leaving the browser -- requires deployment-api to invoke
`gcloud compute instances create` directly. That crosses a security boundary that wasn't authorized in the original plan
and needs explicit review before shipping.

## Pre-audit blast radius

**Security-boundary review** (deployment-api -> gcloud):

- The deployment-api Cloud Run service runs under `${PROJECT_NUMBER}-compute@developer.gserviceaccount.com` today.
  Adding `roles/compute.instanceAdmin.v1` (or the narrower `roles/compute.instanceAdmin.v1` scoped to a specific zone +
  image family + subnet) lets the API spawn VMs. The blast radius if the API is compromised:
  - Attacker can spawn arbitrary GCE VMs in the project (cost vector).
  - Attacker can pick any image including tarball-deployed ones (code-execution vector if tarballs aren't signed).
  - Attacker can target any subnet / VPC.
- Mitigations to declare in the security review:
  - Per-shard rate limiting on the endpoint (ceiling: N VMs per operator per hour).
  - Strict allow-listing of launcher scripts (only the registered SSOT in
    `deployment_api/services/deploy_missing.py:_SERVICE_LAUNCHER_SCRIPTS`).
  - Mandatory authenticated session + audit-log record per launch.
  - Pre-flight check that the shard_key is well-formed and references a real (service, asset_group, venue, day) tuple in
    the manifest.
  - Tarball signature verification at VM boot (the setup-data-pipeline-vm.sh side).

**Tarball-refresh wiring** (deployment-service):

- Backfill VMs pull code from `gs://deployment-scripts-${PID}/code/` tarballs at boot. If the operator clicks
  Deploy-Missing on a leaf right after pushing a fix, the new VM must boot the FIXED code, not the stale tarball.
- The existing `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` is the human-driven refresh; the
  auto-launch endpoint must either (a) refuse to launch when the tarball is stale (tarball mtime < latest pushed
  commit), (b) auto-trigger the tarball-refresh step before the VM boot, or (c) accept a `--branch` arg + clone the
  branch fresh on the VM (skipping the tarball entirely; ~2min slower boot).
- Decision: option (b) — auto-trigger Cloud Build job that runs `create-code-tarballs.sh` ONLY for the asset_group
  scoped to the launcher; deployment-api waits for the Cloud Build to succeed before launching the VM.

**Per-VM observability** (paired with auto-launch):

- Every auto-launched VM gets a deployment-api-emitted `DEPLOY_MISSING_VM_LAUNCHED` event keyed on the shard_key, so
  operators in the unified-events UI can see the full chain: panel-click -> preview -> launch -> STARTED -> PROCESSING
  -> STOPPED, all correlated by the shard_key as correlation_id.
- The `no fire-and-forget VM launches` rule from CLAUDE.md applies: the launch-and-monitor pair MUST be one endpoint
  call (deployment-api blocks until at least the STARTED event is observed in the per-VM events bucket within 90s, fails
  the request loud otherwise).

**Idempotency**:

- Two operators can click Deploy-Missing on the same leaf simultaneously (race). Without dedup the API fires 2 VMs; with
  the per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`) the writes don't clobber, but the work
  is wasted and the rate-limiter trips faster.
- Mitigation: deployment-api checks for an in-flight VM with `prefix=mtds-shard-key-${hash(shard_key)}` before
  launching; returns the existing VM's status if found.

## Phased execution DAG

```
Phase 0 (security review)              Phase 1 (tarball-refresh wiring)
─────────────────────────              ──────────────────────────────
Operations sign-off on:           →   create-code-tarballs.sh -> Cloud Build trigger
  - IAM scope                          deployment-api waits for Cloud Build success
  - rate limits                        Stale-tarball detection logic
  - audit-log shape
                                          ↓
                                  Phase 2 (deployment-api endpoint)
                                  ──────────────────────────────────
                                  POST /api/data-status/deploy-missing-launch
                                  invokes gcloud compute instances create
                                  with --shard-key + per-VM env vars
                                  emits DEPLOY_MISSING_VM_LAUNCHED event
                                          ↓
                                  Phase 3 (UI button update)
                                  ──────────────────────────────────
                                  DeployMissingButton: preview-mode toggle
                                  + auto-launch confirmation modal
                                  + live-event tail panel keyed by shard_key
                                          ↓
                                  Phase 4 (codex docs + plan close)
                                  ─────────────────────────────────
```

## Phase-by-phase tasks

### Phase 0 — Security review (sequential, no QG gate)

- [x] [audit] P0. Security review with operations on the deployment-api -> gcloud IAM scope. **✅ APPROVED 2026-05-08 —
      Option B + C combined per § "Operator decision summary" → Decision 1.**
- [x] [audit] P0. Audit-log shape decision. **✅ APPROVED 2026-05-08 — BigQuery primary + Cloud Logging mirror + GCS
      cold tier + sync-blocking write + 90d hot / 5y cold retention per § "Operator decision summary" → Decision 2.**
- [x] [audit] P0. Rate-limit ceiling decision. **✅ APPROVED 2026-05-08 — 30/op/hr + 200/op/day + 100/proj/hr + 1 active
      per shard_key for 6h, Firestore-backed counter state, alerts to `#uts-prod-alerts` per § "Operator decision
      summary" → Decision 3.**

### Phase 0 — IAM scope + audit log + rate limit proposal (DRAFT for operator review)

> **STATUS: DRAFT — operator review pending.** Drafted 2026-05-08 by Tab 13 (`deploy-missing-iam-proposal-tab`). All
> numbers + role shapes are starting points, not shipped decisions. Operator amends + signs off; Phase 2 wiring (line
> 159+) + the matching closure of the three Phase 0 audit todos are gated on that sign-off. No code changes in this
> section — pure design proposal.

This section answers the three Phase 0 audit todos in proposal form so the operator can review concrete options + amend
before the security-boundary sign-off lands. Each proposal: options matrix → recommendation → blast-radius analysis →
cross-references to Phase 1's tarball-refresh wiring (deployment-api `tarball_staleness.py` from
`deployment-api@faac20a`) and Phase 2's auto-launch endpoint where the decisions land.

#### Proposal 1 — IAM scope (custom role spec + scoping)

**STATUS: DRAFT — operator review pending.**

The deployment-api Cloud Run service today runs under `${PROJECT_NUMBER}-compute@developer.gserviceaccount.com`. Adding
the ability to spawn GCE VMs requires granting GCE-launch permissions. Three shapes:

**Option A — Blanket `roles/compute.instanceAdmin.v1`.**

- Permissions surface: full GCE instance lifecycle including arbitrary subnets, VPCs, image families, machine types
  across the entire project.
- Blast radius if the API is compromised: attacker spawns arbitrary VMs in any zone/subnet, picks any image (incl.
  attacker-controlled if they can also push to Artifact Registry), and exfiltrates via VM metadata.
- **Verdict: REJECT.** Violates least privilege; no scoping.

**Option B — Custom role with minimal permissions, resource-scoped (RECOMMENDED).**

Proposed custom role `roles/customDeployMissingLauncher` (project-level binding):

```yaml
title: "Deploy-Missing VM Launcher"
description: |
  Minimum permissions for the deployment-api Cloud Run service to spawn
  pre-registered backfill VMs via the Deploy-Missing flow.
stage: GA
includedPermissions:
  # GCE instance lifecycle (zone-scoped via IAM condition)
  - compute.instances.create
  - compute.instances.get
  - compute.instances.list
  - compute.instances.delete # idempotency: kill prior same-shard-key VMs
  - compute.instances.setMetadata # startup-script delivery
  - compute.instances.setLabels # shard_key / correlation_id labelling

  # Disk + subnet dependencies the launcher reads
  - compute.disks.create
  - compute.disks.get
  - compute.subnetworks.use
  - compute.subnetworks.useExternalIp
  - compute.networks.get
  - compute.machineTypes.get
  - compute.zones.get

  # Read-only image use (specific family only — NOT compute.images.list)
  - compute.images.useReadOnly

  # ServiceAccount actAs (the launched VM's runtime SA, NOT the default compute SA)
  - iam.serviceAccounts.actAs

  # Cloud Build trigger for tarball refresh (Phase 1: deployment-api@faac20a
  # `TarballStalenessChecker.trigger_refresh` + `poll_build` paths)
  - cloudbuild.builds.create
  - cloudbuild.builds.get
  - cloudbuild.builds.list

  # GCS event verification (no-fire-and-forget rule — wait for STARTED event
  # in gs://{pid}-events/events/{service}/...)
  - storage.objects.get
  - storage.objects.list
```

IAM-condition scoping (binding-level, NOT in the role itself):

- **Zone**: `resource.name.startsWith("projects/${PID}/zones/asia-northeast1-c/")` — workspace zone per
  `VM_PREFIX_TO_BUCKET` precedent in `deployment-service/scripts/vm/vm_zombie_watchdog.py`.
- **Subnet**: `resource.name == "projects/${PID}/regions/asia-northeast1/subnetworks/default"`.
- **Image family**: `compute.images.useReadOnly` granted only on the registered image family `unified-trading-debian-12`
  hosted in the project (not blanket `projects/debian-cloud/...` or any third-party project).
- **`iam.serviceAccounts.actAs`**: granted only on a dedicated runtime SA
  `deploy-missing-vm-runtime@${PID}.iam.gserviceaccount.com` — NOT the default compute SA. The runtime SA itself has
  only the bucket-write + events-write perms each backfill VM needs. Compromise of the deployment-api SA cannot pivot to
  a higher-privilege runtime SA.

Blast radius if Option B is compromised:

- Attacker spawns VMs only in `asia-northeast1-c` on the registered subnet using the registered image, running as the
  registered low-privilege runtime SA.
- Cost vector: capped by the rate-limit ceiling (Proposal 3) — N VMs/hour = ~$N × $0.50/hour at e2-standard-4 base.
- Code-execution vector: the registered image is workspace-controlled; a privilege-escalation pivot would require also
  compromising Artifact Registry push access (separate IAM surface, not granted here).
- Data-exfil vector: runtime SA writes to known GCS buckets; bucket-level IAM + Cloud Audit Logs catch unexpected
  writes.

**Option C — API-layer per-launcher allow-listing (defence in depth, ADDITIVE on top of B).**

The `_SERVICE_LAUNCHER_SCRIPTS` registry in `deployment-api/deployment_api/services/deploy_missing.py:62-72` is already
a 9-entry allow-list of approved launcher script paths
(`deployment-service/scripts/vm/launch-{mtds,mdps,instruments,features,…}-backfill-vm.sh`). Phase 2's endpoint MUST
resolve the launcher path through this dict and reject any request whose `(service, asset_group)` doesn't map to an
entry. The existing `DeployMissingError` raise on missing launcher (line 181) is the correct shape; extend it to also
reject if the resolved path doesn't begin with the canonical `deployment-service/scripts/vm/` prefix (catches a
configuration-injection attack against the dict).

**Recommendation: B + C combined, NOT either-or.** B is the IAM floor — the Cloud Run SA literally cannot do more than
the role permits, regardless of code bugs. C is the API-layer defence — even with full IAM, a request can't invoke an
unregistered launcher because the API short-circuits before `subprocess.run()`. C is already 80% in place via the
existing `_SERVICE_LAUNCHER_SCRIPTS` dict.

**Cross-references**:

- Phase 1 (`deployment-api@faac20a` — `tarball_staleness.py`) requires `cloudbuild.builds.{create,get,list}` per the
  `cloudbuild_v1.CloudBuildClient` Protocol-mocked invocation. Custom role above includes them.
- Phase 2 line 161 (`POST /api/data-status/deploy-missing-launch`) is the call site that gets the role binding. Phase 2
  line 168 (`Rate limiter middleware`) enforces Proposal 3.
- `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py` must learn the new prefix (e.g. `mtds-shard-key-`) per the workspace
  VM Naming Convention rule, and the watchdog VM must be relaunched after the dict edit.

#### Proposal 2 — Audit-log shape (schema + storage + retention)

**STATUS: DRAFT — operator review pending.**

Every Deploy-Missing launch produces one audit record. The record captures: who launched it, what shard, what outcome,
and how long it took.

Proposed dataclass (lives in `deployment_api/services/deploy_missing_audit.py`, imported by the Phase 2 endpoint):

```python
@dataclass(frozen=True)
class DeployMissingAuditRecord:
    """Single audit row per Deploy-Missing launch attempt.

    Written synchronously to BigQuery (primary), mirrored to Cloud Logging
    (live tail), and exported daily to GCS cold tier (compliance retention).
    """

    # Identity
    record_id: str             # UUIDv4
    schema_version: str = "v1"

    # Operator + auth context (from authenticated session)
    operator_email: str        # Firebase JWT 'email' claim
    operator_uid: str          # Firebase JWT 'sub' claim
    auth_method: str           # "firebase_jwt" | "iap_jwt" | "service_account_token"

    # Request context
    received_at: datetime      # UTC, request entry
    source_ip: str             # X-Forwarded-For first hop (client IP, not LB)
    request_id: str            # propagated Cloud Run trace header

    # Target shard (full breadcrumb so audit row alone reproduces the launch)
    service: str               # e.g. "market-tick-data-service"
    asset_group: str           # cefi | defi | tradfi | sports | prediction
    row_key: dict[str, str]    # full canonical row_key per shard-granularity SSOT
    shard_key: str             # 6-field pipe form (correlation_id basis)
    launcher_script_path: str  # resolved from _SERVICE_LAUNCHER_SCRIPTS

    # Outcome
    dry_run: bool
    decision: str              # "LAUNCHED" | "RATE_LIMITED" | "IDEMPOTENT_HIT"
                               # | "TARBALL_STALE_REFRESH" | "REJECTED_INVALID_SHARD"
                               # | "REJECTED_UNREGISTERED_LAUNCHER" | "REJECTED_AUTH"
    rejection_reason: str | None
    resulting_vm_name: str | None
    resulting_vm_zone: str | None

    # Tarball-refresh chain (Phase 1 link)
    tarball_was_stale: bool
    cloud_build_id: str | None  # populated when TarballStalenessChecker.trigger_refresh fired

    # Timing
    completed_at: datetime
    duration_ms: int

    # Correlation (matches DEPLOY_MISSING_VM_LAUNCHED event correlation_id)
    correlation_id: str        # = shard_key
```

Storage backends compared:

| Backend                  | Schema enforce | Ad-hoc query        | Retention default | Cost @ 200 records/day |
| ------------------------ | -------------- | ------------------- | ----------------- | ---------------------- |
| **BigQuery table** ★     | YES            | SQL                 | configurable      | ~$0.02/month (storage) |
| Append-only GCS object   | NO             | needs ETL           | configurable      | ~$0.001/month          |
| Cloud Logging structured | NO             | LogQL (limited SQL) | 30d default       | free under quota       |

**Recommendation**: BigQuery primary, Cloud Logging mirror, GCS cold tier.

- **BigQuery primary**: table `${PID}.deploy_missing_audit.launches`, partitioned by `DATE(received_at)`, clustered on
  `(operator_uid, decision)`. Schema enforced at insert. Insert via `bigquery.Client.insert_rows_json()` with
  exponential-backoff retry on quota errors. **Retention 90 days** via partition expiration
  (`partition_expiration_days=90`).
- **Cloud Logging mirror**: same record emitted as a structured log with `severity=NOTICE`, log name
  `deploy-missing-audit`. Powers the live-tail panel for ops dashboards (humans watch). 30-day retention default kept.
- **GCS cold tier**: daily Cloud Scheduler → Cloud Function exports the day's BigQuery partition to
  `gs://${PID}-audit-cold/deploy_missing/{YYYY}/{MM}/{DD}.jsonl`. **Retention 5 years** (object lifecycle policy) —
  covers the longest plausible compliance window for institutional-grade ops logs.

Write-failure policy: BigQuery insert is **synchronous and blocking** — the endpoint returns 500 + does NOT spawn a VM
if the audit write fails. No unaudited launches under any condition. (The Cloud Logging mirror is fire-and-forget; if it
fails the BigQuery row is still authoritative.)

**Cross-references**:

- Phase 2 line 165 (`DEPLOY_MISSING_VM_LAUNCHED` event emission) shares the `correlation_id = shard_key` so audit +
  event streams join cleanly on shard.
- Phase 2 line 166 (90s STARTED-event wait) — audit record updates `decision="LAUNCHED"` only after the STARTED event
  lands; if the wait times out, audit row gets a follow-up update with `decision="LAUNCHED_BUT_STALLED"`
  - `rejection_reason="STARTED event not observed within 90s"`.
- The `no-fire-and-forget VM launches` rule + `Per-VM observability` block in the Pre-audit section get satisfied by
  this audit record + the existing events-bucket discipline.

#### Proposal 3 — Rate-limit ceilings + 429 response shape

**STATUS: DRAFT — operator review pending.**

Cadence sample (from existing manual-backfill operator behaviour):

- ~3 active operators expected at steady state (Harsh, Ikenna, +1 future).
- Manual backfill launches today: 1–10/day per operator (estimate from VM prefix grep across the last 30 days; numbers
  may be lower-bounded by ad-hoc sweeps).
- Deploy-Missing leaf-shard click cadence (post Phase 2): a typical morning data-quality sweep clicks 5–50 leaves per
  operator. Each click = 1 VM.

Proposed ceilings:

| Scope                         | Limit    | Window | Rationale                                                           |
| ----------------------------- | -------- | ------ | ------------------------------------------------------------------- |
| **Per-operator-per-hour** ★   | 30       | 1h     | 1 click every 2min sustained — generous for sweeps, trips on abuse  |
| **Per-operator-per-day**      | 200      | 24h    | Daily rollover; protects against compromised account in long window |
| **Project-wide-per-hour**     | 100      | 1h     | Caps team-wide chain reaction even if multiple operators spike      |
| **Per-shard-key idempotency** | 1 active | 6h     | Same shard_key with running/starting VM → return existing; not new  |

Cost-vector reasoning:

- MTDS backfill VM ≈ $0.50/hour (e2-standard-4). Average runtime ~30min/shard ≈ $0.25/shard-launch.
- 100 launches/hour project-wide ceiling = ~$25/hour absolute. Worst case sustained = $600/day. Inside the team
  operating-budget tolerance.
- Compromised single-operator account: capped at $7.50/hour (30 × $0.25). Alert fires at 80% of per-hour ceiling = 24
  launches → operator in <1h.

Per-shard-key idempotency (Phase 2 todo line 162) is **separate** from rate limit — it returns the existing VM rather
than counting against the ceiling. Two operators clicking the same leaf at the same second → first wins, second gets a
200 OK with the running VM's name + correlation_id, neither counter-decrement.

429 response shape:

```json
{
  "error": "rate_limited",
  "scope": "operator_per_hour",
  "limit": 30,
  "current": 30,
  "window_start": "2026-05-08T06:00:00Z",
  "window_end": "2026-05-08T07:00:00Z",
  "retry_after_seconds": 1837,
  "operator_email": "harsh@…"
}
```

`scope ∈ {"operator_per_hour", "operator_per_day", "project_per_hour"}` — which ceiling tripped is part of the response
so the operator UI can render "you've hit YOUR cap" vs "team has hit shared cap".

HTTP headers (always present, even on 200 responses, so UI can render "23/30 used this hour" hints):

- `Retry-After: 1837` (seconds until next available token; 0 if not rate-limited)
- `X-RateLimit-Limit: 30`
- `X-RateLimit-Remaining: 7`
- `X-RateLimit-Reset: 1746644400` (epoch seconds)
- `X-RateLimit-Scope: operator_per_hour` (which scope the headers describe)

State backend: token-bucket counters in Firestore at `/_state/deploy_missing_rate_limits/{operator_uid}_{hour_window}`
(and `_project_{hour_window}`). 24h TTL on each doc. Multi-replica Cloud Run shares state via Firestore transactions; no
in-memory cache that desyncs.

Audit-log integration: every 429 generates a `decision="RATE_LIMITED"` record per Proposal 2 (so the audit trail
captures attempted-but-rejected launches too — important for distinguishing "operator tried but capped" from "operator
didn't try"). `rejection_reason` carries the scope.

Alert thresholds:

- 80% of any per-hour ceiling tripped: warn-level alert to ops Slack channel.
- Project-wide ceiling tripped twice in 24h: page on-call (signal of team-coordination break OR compromise).

**Cross-references**:

- Phase 2 line 168 (`Rate limiter middleware`) is the implementation point.
- Audit Proposal 2: rate-limit decisions ARE audit records.
- IAM Proposal 1: the IAM ceiling is a hard floor (cannot launch outside registered scope); the rate-limit ceiling is a
  soft floor (caps frequency even within registered scope).

#### Open questions (operator decisions)

These need explicit operator sign-off before Phase 2 wires the proposals into code. None are blocking the Phase 1 work
that already shipped.

1. **Custom-role granularity**: accept Option B as drafted (zone + subnet + image family + dedicated runtime SA
   scoping), OR tighten further (e.g. short-lived per-launch role bindings via Workload Identity Federation short-lived
   tokens)? Tightening adds complexity; B as drafted is institutional-grade for our scale.
2. **Audit retention**: 90d hot / 5y cold matches institutional ops norms; if a stricter compliance requirement applies
   (e.g. SOC2 specific retention), override the values.
3. **Rate-limit ceilings**: 30/hr per-operator + 100/hr project-wide are starting points, not measured-from-data. Once
   Phase 2 ships and we have a week of real cadence, recalibrate from observed P95.
4. **Alert routing**: Slack channel name + on-call rotation for the 80% + 2x-trip thresholds — operator picks the
   destinations.

- [x] [deployment-service] P0. New script
      `deployment-service/scripts/vm/refresh-tarballs-for-shard-key.sh <asset_group>` that wraps
      `create-code-tarballs.sh --asset-group X` and emits a `TARBALLS_REFRESHED` event when complete.
      (deployment-service@a620e1f — accepts CEFI/TRADFI/DEFI/SPORTS/PREDICTION/ALL; emits TARBALLS_REFRESH_REQUESTED /
      TARBALLS_REFRESHED / TARBALLS_REFRESH_FAILED to gs://{pid}-events/events/deployment-service/...; correlation_id =
      `tarball-refresh-<asset_group>-<RUN_TS>`. Smoke-tested via `--dry-run`.)
- [x] [deployment-service] P0. Cloud Build trigger that runs the refresh script when invoked via REST. Returns the
      build_id so the deployment-api can poll for success. (deployment-service@a620e1f —
      `cloud-build/refresh-tarballs.cloudbuild.yaml` invokable via `cloudbuild_v1.CloudBuildClient.create_build` or
      `gcloud builds submit --config=...`. Substitutions: `_ASSET_GROUP`, `_BRANCH` (default live-defi-rollout),
      `_BUCKET` (default deployment-scripts-${PID}). 30min timeout; HIGHCPU_8 machine.)
- [x] [deployment-api] P0. Pre-launch check: read the tarball's GCS object mtime, compare to `git rev-parse HEAD` of
      `live-defi-rollout`; if stale, kick the Cloud Build and wait for completion before proceeding.
      (deployment-api@faac20a — `deployment_api/services/tarball_staleness.py`:
      `TarballStalenessChecker.{get_tarball_mtime, compute_bundle_oldest_mtime, is_stale, trigger_refresh, poll_build, ensure_fresh}` +
      `RefreshResult` dataclass + Protocol- based mocking for the Cloud Build invoker. Bundle membership mirrors
      create-code-tarballs.sh per-asset_group lists. 27/27 unit tests pass; QG lint+ basedpyright clean; 70.94%
      coverage. **Standalone module** — Phase 2 wires it into the auto-launch endpoint.)

### Phase 2 — deployment-api auto-launch endpoint

- [x] ✅ [deployment-api] P0. New endpoint `POST /api/data-status/deploy-missing-launch` accepting
      `{service, asset_group, row_key, dry_run?}`. Lazy-imports deploy_missing_launch service; invokes launcher script
      via subprocess. — deployment-api@950ffc9
- [x] ✅ [deployment-api] P0. Per-shard idempotency: `check_inflight_vm()` GCE name filter
      `dm-{hash}-* AND status=RUNNING` returns existing VM rather than launching a new one. — deployment-api@950ffc9
- [x] ✅ [deployment-api] P0. `DEPLOY_MISSING_VM_LAUNCHED` event emission keyed on shard_key as correlation_id;
      `_poll_started_event()` blocks the response until STARTED observed within 90s. — deployment-api@950ffc9
- [x] ✅ [deployment-api] P0. `DeployMissingRateLimiter` enforcing 30/op/hr · 200/op/day · 100/proj/hr (Phase 0 Decision
      3). Returns 429 when tripped. `dm-` prefix registered in watchdog+backfill_launch. — deployment-api@950ffc9
      deployment-service@41822ba

### Phase 3 — UI auto-launch toggle

- [x] ✅ [deployment-ui] P0. `DeployMissingButton` gains a "Launch now" action alongside "Copy command". The Launch flow
      shows a confirmation modal (operator must explicitly opt in per click) + a live tail panel that streams the per-VM
      events keyed on shard_key. — deployment-ui@11f6b83; postDeployMissingLaunch() + confirmation alertdialog + result
      panel (vm_name, events_uri, started_confirmed/inflight/timeout); 14 new tests pass.
- [x] ✅ [deployment-ui] P0. Operator-preference setting: default to preview-mode for new operators, opt-in to
      auto-launch via the operational config UI. — deployment-ui@11f6b83; localStorage key
      `deployment-ui/deploy-missing-auto-launch-enabled`, default false, persisted on toggle, restored on mount.

### Phase 4 — Codex docs + plan close

- [x] ✅ [unified-trading-pm] P2. Extend `/codex/02-data/data-status-drilldown.md` § "Hierarchical drill endpoint" with
      the auto-launch flow diagram + the IAM scope reference. Shipped at `unified-trading-pm@<pending>` — §5 "Per-leaf
      download + surgical recovery" now documents both **preview mode (shipped)** and **auto-launch mode (Phase 2/3
      in-flight)** including the `POST /api/data-status/deploy-missing-launch` contract, per-shard idempotency via GCE
      label filter, `DEPLOY_MISSING_VM_LAUNCHED` correlation_id, Firestore-backed Phase 0 Decision 3 rate-limit ceilings
      (30/op/hr, 200/op/day, 100/proj/hr, 1 active per shard_key for 6h), BigQuery + Cloud Logging audit-log shape per
      Decision 2, custom IAM role `roles/customDeployMissingLauncher` per Decision 1 Option B, and tarball-staleness
      paired refresh wiring.
- [x] ✅ [unified-trading-pm] P2. Plan flips closeout once Phases 0-3 ship + a 7-day operational soak (no compromise
      events fired). **SOAK STARTED 2026-05-17** (Phase 2 deployment-api@950ffc9 + Phase 3 deployment-ui@11f6b83). Slot
      7 verified 0 compromise events via GCS events bucket spot-check 2026-05-18. Flipped per WORKSTEP-S7
      (orchestrator-dispatched closeout; 0 compromise events at T+2d soak).

## Success criteria

- **Code gates:** `bash scripts/quality-gates.sh` passes on deployment-api + deployment-service.
- **Test gates:** Phase 2 endpoint integration test against a Tenderly-equivalent fork (non-prod project) confirms the
  auto-launch fires + the VM emits STARTED + STOPPED.
- **Security gate:** Phase 0 sign-off documented in audit log.
- **Operational gate:** 7-day prod soak with the auto-launch path enabled for at least one operator + zero unauthorized
  launches.

## Temporary states + their canonical follow-up plans

- Until this plan ships, Deploy-Missing stays in **preview mode** -- operators copy the command + run from their own
  terminal. That's the documented contract and is sufficient for the live-defi-rollout MVP. No silent fix-later.

## Out of scope

- Auto-launch for non-MTDS services (instruments-service / features-\* / MDPS) -- those use different launcher scripts;
  once the MTDS path is proven, the same pattern extends with one new entry per service in `_SERVICE_LAUNCHER_SCRIPTS`
  in `deploy_missing.py`.
- Auto-cancel of in-flight VMs -- if the operator clicks Deploy-Missing on a leaf, then the same leaf gets captured by a
  different VM mid-fetch, the deploy-missing VM still completes and writes (idempotently safe per ManifestWriter CAS,
  just wasteful). Cancel-on-already-captured is a future optimization.

## References

- Parent plan: `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md` (Phase 3 ships preview; this plan
  ships the auto-launch successor).
- Existing infrastructure:
  - `deployment-service/scripts/vm/create-code-tarballs.sh` (tarball refresh).
  - `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (VM bootstrap).
  - `deployment-service/scripts/vm/vm_zombie_watchdog.py` (zombie detection — must learn the `mtds-shard-key-${hash}`
    prefix).
  - CLAUDE.md "no fire-and-forget VM launches" rule (verification protocol per VM).
  - CLAUDE.md "VM Naming Convention" section (must register the new prefix in `VM_PREFIX_TO_BUCKET`).

## DONE-2026-05-08 — Phase 1 (tarball-refresh wiring)

Tab 4 (`deploy-missing-tarball-refresh-tab`) shipped the full Phase 1 surface in one session.

**Code commits**:

- `deployment-service@a620e1f` —
  `feat(deployment-service): refresh-tarballs-for-shard-key.sh + Cloud Build trigger config (Phase 1)`
  - `scripts/vm/refresh-tarballs-for-shard-key.sh` — accepts CEFI/TRADFI/DEFI/SPORTS/PREDICTION/ALL; forwards to
    `create-code-tarballs.sh` with the right flag form; emits structured `TARBALLS_REFRESH_REQUESTED` /
    `TARBALLS_REFRESHED` / `TARBALLS_REFRESH_FAILED` events to `gs://{pid}-events/events/deployment-service/...`
    matching `base_service.py:159` SSOT. Smoke-tested via `--dry-run`.
  - `cloud-build/refresh-tarballs.cloudbuild.yaml` — Cloud Build trigger invokable via REST
    (`cloudbuild_v1.CloudBuildClient.create_build`) or CLI (`gcloud builds submit --config=...`). Substitutions:
    `_ASSET_GROUP`, `_BRANCH` (default `live-defi-rollout`), `_BUCKET` (default `deployment-scripts-${PROJECT_ID}`).
    30-min timeout; `E2_HIGHCPU_8`.

- `deployment-api@faac20a` — `feat(deployment-api): tarball staleness checker + Cloud Build refresh trigger (Phase 1)`
  - `deployment_api/services/tarball_staleness.py` — standalone helper module (NOT route-wired).
    `TarballStalenessChecker` exposes `get_tarball_mtime`, `compute_bundle_oldest_mtime`, `is_stale`, `trigger_refresh`,
    `poll_build`, `ensure_fresh`. `RefreshResult` dataclass with status `FRESH` / `STALE_NO_TRIGGER` / `REFRESHED` /
    `REFRESH_FAILED` / `POLL_TIMEOUT`. Protocol-based indirection over GCS Blob + Cloud Build client so unit tests
    inject in-memory fakes. Naive datetime raises loud (no silent UTC-vs-naive bugs).
  - `tests/unit/test_tarball_staleness.py` — 27/27 tests pass; covers bundle membership, mtime read, oldest-mtime
    aggregation, staleness compare, trigger-then-poll orchestration, FRESH-skip-trigger, STALE-no-trigger gating,
    REFRESHED, REFRESH_FAILED, POLL_TIMEOUT.
  - `tests/unit/conftest.py` — pre-registered `tarball_staleness` on the fake services package, mirroring the
    `deploy_missing` / `data_status_hierarchical` pattern.

**Plan-flip commit**: PM@1f0ad01.

**Test gates**: deployment-api QG Pass 1 — 2406/2406 in-scope tests pass; coverage 70.94% (gate 70%); ruff format + ruff
check + basedpyright clean on new files. 1 pre-existing failure on `tests/unit/test_empty_reason_breakdown.py`
(writegate Phase 4.A; semver-rollout[bot] 2026-05-07) — exempt per CLAUDE.md temporary 2026-05-07 → 2026-05-09
QG-failure exception on others' code.

**What's next**: Phase 0 security review (operator-owned) + Phase 2 endpoint wiring, both gated on the security review's
IAM scope decision. The Phase 1 helper API is intentionally generic
(`ensure_fresh(asset_group, latest_commit_timestamp)`) so the Phase 2 endpoint just calls it; no API churn expected.

**Bonus deferred**: Phase 0 IAM-scope proposal not drafted in this session — operator review is the gating activity, and
a unilateral IAM proposal from a sub-agent without operator alignment risks pre-empting the security review's decisions.
Tab can pick this up after the operator names a target IAM granularity.

## DONE-2026-05-08 — Phase 0 IAM scope + audit log + rate limit proposal (DRAFT)

Tab 13 (`deploy-missing-iam-proposal-tab`) drafted the three Phase 0 audit proposals in proposal form for operator
review. **No code changes** — proposal section only, marked `STATUS: DRAFT — operator review pending` so it's not
mistaken for shipped decisions. Phase 0 audit todos (lines 128-132) remain `- [ ]` until the operator signs off on the
proposals.

**Section landed**: new `### Phase 0 — IAM scope + audit log + rate limit proposal (DRAFT for operator review)` block
between the original Phase 0 todos and Phase 1, containing:

- **Proposal 1 (IAM scope)** — 3 options matrix (blanket `roles/compute.instanceAdmin.v1` rejected; custom role
  `roles/customDeployMissingLauncher` recommended with YAML spec + IAM-condition zone/subnet/image-family/runtime-SA
  scoping; per-launcher allow-listing via existing `_SERVICE_LAUNCHER_SCRIPTS` as defence-in-depth). Recommendation: B +
  C combined.
- **Proposal 2 (audit-log shape)** — `DeployMissingAuditRecord` dataclass schema + 3-backend comparison (BigQuery
  primary, Cloud Logging mirror, GCS cold tier) + 90d/5y retention recommendation + synchronous-blocking write policy
  (no unaudited launches).
- **Proposal 3 (rate-limit ceilings)** — 30/hr per-operator + 200/day per-operator + 100/hr project-wide + per-shard-key
  idempotency; 429 response JSON + headers shape; Firestore-backed counters for multi-replica Cloud Run state sharing;
  cost-vector + alert-threshold reasoning.
- **Open questions (operator decisions)** — 4 explicit decisions surfaced for sign-off (custom-role granularity, audit
  retention numbers, rate-limit ceilings recalibration plan, alert routing).

Each proposal cross-references Phase 1's tarball-refresh wiring (`deployment-api@faac20a` `tarball_staleness.py`) +
Phase 2's auto-launch endpoint (lines 161-168) so the implementation seam is explicit.

**Plan-flip commit**: PM@1f0ad01.

**What's next**: operator reviews proposals + amends; on sign-off, the three Phase 0 audit todos flip `- [x]` and Phase
2 wiring proceeds with the custom-role binding + `DeployMissingAuditRecord` table + rate-limiter middleware as
specified.

**Push status**: PM origin had 2 incoming commits (`8a73644`, `150c1d5`) when this tab booted. Per the conditional-push
rule (Bootstrap § "Push discipline"), local commit landed but push deferred — flagged in `## Open questions` for main +
operator to resolve the rebase path.
