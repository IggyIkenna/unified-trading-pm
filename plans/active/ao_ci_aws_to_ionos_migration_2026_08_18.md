---
doc_type: plan
title: Migrate AO + CI Runner from AWS to IONOS Cloud Cubes
summary:
  Move agent-orchestrator-vm-1 and ci-escalation-runner-vm-1 off AWS EC2 to IONOS Cloud Cubes for cost — building the
  first-ever VM create/bootstrap/decommission launcher for either box as a provider-abstracted shim so a future move to
  another cloud is a config change, not a rewrite.
status: draft
nature: design
asset_group: [ao, ci, infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [migration, cost, cloud-agnostic, ionos, aws, vm-launcher, infra]
related:
  [
    /plans/active/defi_compute_gcp_migration_2026_08_08.md,
    /plans/active/ci_vm_exposure_remediation_2026_08_06.md,
    /codex/11-project-management/cloud-spend-forecast-and-credits-2026-08.md,
    /codex/05-infrastructure/cloud-agnostic-script-pattern.md,
    /codex/05-infrastructure/cloud-agnostic-build-lineage.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 13
assigned_role: infra
effort: high
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
source: [operator request 2026-08-18, "let's create the plan for migrating both AO and CI on this new cloud provider"]
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/cloud-agnostic-script-pattern.md,
    /codex/05-infrastructure/cloud-agnostic-build-lineage.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /codex/11-project-management/cloud-spend-forecast-and-credits-2026-08.md,
    /codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md,
    agent-orchestrator/scripts/bootstrap_vm.sh,
    unified-trading-pm/scripts/self-hosted-runners/setup-glue-runners.sh,
  ]
locked_by:
locked_since:
---

# Migrate AO + CI Runner from AWS to IONOS Cloud Cubes

**Human plan — not AO-dispatched** (`execution_scope: local-only`). Touches production cutover of the AO VM itself,
credential re-provisioning, and a live DNS/traffic cutover — judgment calls, not bounded worker todos.

## Decision log (this plan overrides a live, more-senior commitment — read before executing)

- **2026-08-18, operator decision**: target cloud is **IONOS**, not GCP, *despite* `cloud-spend-forecast-and-credits-2026-08.md`
  (created/reviewed 2026-08-09) committing this exact AWS spend to migrate to GCP as leverage in an active 3-year, $2M
  GCP-credits negotiation. Surfaced to the operator directly before this plan was authored; confirmed as an informed
  override, not an oversight. Todo in §6 updates that doc so it stops reading as the live commercial position for this
  spend — do not skip it.
- **2026-08-18, operator decision**: plan destination is human-driven (`assigned_vm: NA`), not AO-dispatched — AO
  workers run on the box this plan migrates, so dispatching the migration to AO mid-flight risks the dispatcher and the
  target being the same VM.
- **Prior, unrelated**: `defi_compute_gcp_migration_2026_08_08.md` explicitly carved AO + CI-runner OUT of its GCP
  migration scope ("stay on AWS per operator instruction, already right-sized this same session") — that carve-out is
  what this plan now reverses, ten days later, for cost reasons that plan didn't weigh.

## Why (cost baseline from this session's research)

Current AWS spend on these two boxes ≈ **$1,700/mo** (CI VM ~$550 + AO ~$1,000 + ~$200 misc, per the cloud-spend-forecast
doc), including a **real, AWS-billed internet-egress line item of ~$213/mo** (~1.97TB, ap-northeast-1, confirmed via
Cost Explorer, not the inflated CloudWatch `NetworkOut` metric which also counts private/internal VPC traffic).
Projected on IONOS Basic Cube XL ($65.52/mo, 16vCPU/32GB/960GB NVMe, first 2TB/mo egress pooled-free per contract):
~$65.52 × 2 boxes + near-zero egress overage at current traffic, materially cheaper even before weighing CI-runner
right-sizing.

## Full-execution criterion (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE)

- ✅ AO's DNS name resolves to a running IONOS box serving real dispatch/worker traffic for a real observation window
  (§4), not just a smoke-tested boot.
  - **What ran**: `bootstrap_vm.sh --cloud-provider ionos` on a provisioned Basic Cube XL; AutoSpawnLoop + the 9
    scheduled-job systemd timers observed live.
  - **Verification**: `curl https://api.agent-orchestrator.odum-research.com/health` → 200, sustained over the
    observation window; at least one real scheduled-job dispatch logged.
- ✅ CI-runner claims and completes a real GitHub Actions job from the IONOS box, not just `setup-glue-runners.sh status`
  reporting healthy.
  - **What ran**: a canary workflow (`reconcile-release-tags`) targeting `self-hosted,glue`.
  - **Verification**: the GHA run URL, showing SUCCESS, claimed by the new runner's hostname/label.
- ✅ Both AWS boxes are terminated (not just stopped) after their confidence windows, and the DR snapshot restore path is
  proven against the new provider.
  - **Verification**: `aws ec2 describe-instances --region ap-northeast-1` shows `terminated`; a real
    `restore_from_gcs.sh --vm-id <id>` dry-run against the IONOS box's own snapshot succeeds.
- ✅ Zero session-transcript or eval-results history is lost in the cutover — the two backup gaps found this session
  (§2) are closed and verified BEFORE either AWS box stops, not discovered missing after.
  - **Verification**: for each AWS box, a transcript/results file present locally immediately pre-stop is confirmed
    present at its GCS/S3 key immediately after.

**Handoff exception**: the IONOS-side WIF-equivalent research (§1) may reveal no clean replacement exists in time: if
so, the CI-runner credential todo may ship with the documented `GH_PAT`-literal fallback and a follow-up todo — state
that explicitly in the Progress Log if it happens, don't silently ship a weaker posture.

---

## §1. Design decisions (resolve before building — each is a genuine judgment call, not bounded work)

- [ ] [DESIGN] P0. Decide AO's secrets backend: consolidate the `aws secretsmanager get-secret-value` calls in
      `bootstrap_vm.sh` (currently fetching `GH_PAT` / `ORCHESTRATOR_ENV_LOCAL` / `ORCHESTRATOR_VM_GCP_ADC` /
      `gh-app-ci-poller-*`) onto **GCP Secret Manager only**, since GCP ADC is already provisioned on the box regardless
      of compute cloud. Done-when: a Progress Log entry names the target GSM secret names for each migrated secret.
- [ ] [DESIGN] P0. Decide CI-runner's GitHub credential replacement. Today's GCP Workload Identity Federation provider
      is bound to the AWS EC2 instance role via IMDSv2
      (`arn:aws:sts::427895769566:assumed-role/uts-orchestrator-epic-role`, `setup-glue-runners.sh`) — breaks outright
      off AWS. Evaluate: (a) a WIF provider bound to whatever attestation IONOS exposes, (b) a GCP service-account key
      file provisioned via bootstrap + GSM instead of WIF, (c) fallback to a rotated `GH_PAT` literal (already flagged
      elsewhere as the weaker option). Done-when: a Progress Log entry names the chosen mechanism + why.
- [ ] [DESIGN] P1. Decide CI-runner's remote-access model to replace AWS SSM (today's *only* remote-exec path — zero
      SSH, zero inbound security-group rules). IONOS has no SSM equivalent. Evaluate SSH with key-based auth restricted
      to an admin IP allowlist (IONOS Cloud Firewall) vs. a jump host vs. an agent-based tool. Done-when: a written
      decision on access model + firewall posture, logged in the Progress Log.
- [ ] [DESIGN] P1. Decide the AO metrics/recovery replacement for the AWS CloudWatch agent (mem/swap/disk) and the
      EventBridge+Lambda auto-reboot-on-alarm mechanism (`agent-orchestrator-api-host.md`) — both AWS-native, no IONOS
      equivalent. Evaluate a plain systemd/self-hosted metrics exporter driving recovery off the existing
      `GET localhost:8765/health` endpoint instead of a cloud-native alarm. Done-when: a written decision.
- [ ] [DESIGN] P1. Design the provider-abstraction shape for VM lifecycle (create/start/stop/delete + floating-IP +
      firewall) covering AWS EC2 and IONOS Cloud API today, shaped so a third provider is a new case, not a rewrite —
      extend the `--cloud-provider {aws,gcp}` convention already threaded through `bootstrap_vm.sh` rather than
      inventing a parallel mechanism. Done-when: a short design note (Progress Log or a codex stub) names the
      abstraction's shape and which ad hoc AWS/GCP branches it replaces.
- [ ] [DESIGN] P1. Decide CI-runner's IONOS sizing. Current `m8i.2xlarge` is 8vCPU/32GB; no exact Cube tier matches
      (Basic Cube L = 8vCPU/16GB, Basic Cube XL = 16vCPU/32GB). Done-when: a written decision (accept over-provisioned
      XL, downsize to L's 16GB RAM, or evaluate IONOS Memory Cubes) with the cost delta noted.

## §2. Build — the portable launcher + bootstrap extension (depends on §1 decisions landing first)

- [ ] [INFRA] P1. Author `scripts/vm-launch.sh --provider {aws,ionos} --role {ao,ci-runner}` provisioning compute +
      floating/public IP + firewall rules + boot disk on either provider — net-new for **both** clouds (no launcher
      exists today even for AWS; AO's EIP/SG/EBS were hand-provisioned per `docs/ikenna-vm-setup.md`). Done-when:
      running it against IONOS produces a reachable Basic Cube XL with SSH open only to the §1 admin allowlist.
- [ ] [INFRA] P1. Extend `bootstrap_vm.sh`'s `--cloud-provider` branch with `ionos` (or the generalized path from §1)
      for: IMDSv2-equivalent metadata lookup, external-IP resolution, and self-registration private-IP lookup — each
      currently AWS/GCP-only with an `unknown-vm` fallback already present. Done-when:
      `bootstrap_vm.sh --cloud-provider ionos` completes on a fresh Cube with zero AWS-specific call failures.
- [ ] [INFRA] P1. Replace the AWS Secrets Manager calls in `bootstrap_vm.sh` with the GCP-Secret-Manager-only path from
      §1; keep the AWS branch working unchanged for any box still on AWS mid-transition. Done-when: a fresh IONOS
      bootstrap fetches every needed secret with zero AWS API calls in its trace.
- [ ] [INFRA] P2. Drop the CloudWatch agent install from the `ionos` branch; wire the §1 metrics/recovery replacement.
      Done-when: `systemctl status` on the IONOS box shows the replacement running, no `amazon-cloudwatch-agent` unit
      present.
- [ ] [INFRA] P2. Author the paired `scripts/vm-winddown.sh --provider {aws,ionos} --instance <id>` — also net-new
      (today's cost control is a manual `aws ec2 stop-instances`) — that snapshots final state (reusing the existing
      `restore_from_gcs.sh`-compatible SnapshotLoop artifact), deregisters DNS if applicable, and stops/deletes the
      instance. Done-when: run against a disposable test box on either provider, nothing left billing, a resumable
      snapshot left in GCS.
- [ ] [INFRA] P2. Fix every hardcoded reference to AO's Elastic IP `13.113.200.22` to resolve through the DNS name
      `api.agent-orchestrator.odum-research.com` instead — named instances: `orchestrator_vm_registry.yaml`,
      `install_ldr_to_main_promote_heartbeat.sh`, `install_qg_baseline_daily_promote.sh`,
      `install_template_drift_daily_check.sh`, `cron_liveness_watchdog.py`. Done-when: grepping the literal IP across
      `unified-trading-pm/` and `agent-orchestrator/` returns zero hits outside DNS-zone config itself.
- [ ] [INFRA] P2. Extend `setup-glue-runners.sh` / `glue-runner-run.sh` to use the §1 credential mechanism instead of
      the AWS-instance-role-bound WIF provider. Done-when: a runner registered from an IONOS box claims and completes a
      real GHA job end-to-end.
- [ ] [INFRA] P2. Repoint `resource-history-sampler`'s durable backup off `ORCHESTRATOR_S3_BUCKET`-only (S3 has no
      IONOS equivalent; this is already an open todo in `ci_vm_exposure_remediation_2026_08_06.md`) onto GCS. Done-when:
      a sample run writes to GCS and the object reads back correctly.
- [ ] [INFRA] P1. Close a real backup gap found this session: Claude Code session transcripts
      (`~/.claude-configs/*/projects/**/*.jsonl` + `~/.claude/projects/**/*.jsonl`, main AND subagent transcripts —
      the filename is the `claude_session_id`) are the only surviving record of per-turn token usage and which model
      served each turn (`message.usage`, per `server/context_probe.py`'s own docstring — this covers every model
      backend routed through Claude Code, not just Anthropic's own: DeepSeek and anything else on the same harness
      write the identical transcript format) — and are currently NOT covered by `gcs_sync.py`'s `SnapshotLoop`
      (verified by reading it in full: it uploads only `state.json`, SQLite `state.db`, `resource_history.jsonl`, and
      the resource-watchdog log/snapshots). Add `upload_claude_transcripts_to_gcs`/`_s3` to `gcs_sync.py`, mirroring
      the existing `resource_history` upload pattern (`transcripts/<vm_id>/<date>/...` key layout under the same
      bucket) — called **once, at migration time, not on a periodic cadence** (operator directive 2026-08-18: this
      data only needs a one-time capture when actually moving clouds, not a standing 30-min backup). Note transcripts
      carry full conversation content (code, tool output, anything typed) — reuse the existing bucket's access
      boundary rather than widening it, but flag if tighter scoping is wanted. Done-when: running the new function
      against the live VM uploads every transcript file present to its GCS/S3 key.
- [ ] [INFRA] P1. Close the second gap found this session: `omniroute-eval/results/` — the live model-provider
      bake-off's actual output (`provider-matrix.sh`, one JSONL row per model×task cell; this is the in-progress
      "compare context tokens/turns across providers" work) — is git-ignored
      (`agent-orchestrator/.gitignore:193`) and uploaded nowhere; local-only. Add a GCS/S3 upload (same key-layout
      pattern, `eval-results/<vm_id>/<date>/...`) — also a **one-time, migration-time call only**, not wired into any
      periodic loop or per-run hook (same operator directive as above). Done-when: running the new function uploads
      every results file currently on disk to GCS/S3.
- [ ] [INFRA] P1. Wire BOTH of the above into `vm-winddown.sh` (§2's new decommission script) as the one-time
      pre-stop backup step — this is the ONLY invocation point for either upload (no periodic `SnapshotLoop` wiring,
      per operator directive). Done-when: running `vm-winddown.sh` against a test box confirms its transcripts and
      eval-results both land in GCS/S3 before the instance stops. **§4's and §5's AWS-VM stop/terminate todos are
      gated on this landing first** — do not stop either AWS box until this exists and has been verified.
- [ ] [DOC] P2. Document the two closed gaps + the new `transcripts/`/`eval-results/` GCS/S3 key layout in
      `vm-log-archival.md` (the existing canonical-paths SSOT for exactly this class of problem) — note there
      explicitly that these two are one-time migration-triggered backups, unlike every other row in that doc's table
      which is a standing periodic/pre-kill contract. Done-when: the doc's path table gains the two new rows.

## §3. IONOS account setup

- [ ] [OPERATOR] P0. Create the IONOS Cloud contract/account, generate API credentials for the §2 launcher, store them
      in GCP Secret Manager per the §1 consolidation decision. Genuine vendor-signup step only a human can do (payment
      method, account terms). Done-when: an IONOS API token exists in GSM and `vm-launch.sh --provider ionos --dry-run`
      authenticates successfully.

## §4. AO cutover (sequenced — each step follows the last; independent of §5)

- [ ] [INFRA] P1. Provision AO's replacement on IONOS (Basic Cube XL — current usage is 16vCPU/32GB/700GiB EBS, fits
      Cube XL's 960GB NVMe headroom) via the §2 launcher; run `bootstrap_vm.sh --cloud-provider ionos` against it.
      Done-when: `GET /health` returns 200 and the dashboard SPA can reach it directly by IP (pre-DNS-cutover smoke
      test).
- [ ] [INFRA] P1. Run the IONOS AO box in shadow/observation for a real multi-day window (mirroring the
      verify-before-decommission pattern used in `defi_compute_gcp_migration_2026_08_08.md`) — confirm AutoSpawnLoop,
      the 9 scheduled-job systemd timers, `ao-self-pull.sh`, and DR snapshotting all behave identically to the AWS box.
      Done-when: N consecutive days of green health checks + at least one real scheduled-job dispatch observed, dates
      logged in the Progress Log.
- [ ] [OPERATOR] P1. Cut DNS (`api.agent-orchestrator.odum-research.com`) over to the IONOS floating IP. Live-traffic
      cutover with real blast radius — only proceed once the §2 hardcoded-IP fix has landed. Done-when: DNS resolves to
      the new IP and every consumer identified in §2's IP-reference sweep confirms working against the new box.
- [ ] [INFRA] P2. After a stability window (propose 7 days), **stop** (don't yet delete) AWS AO VM
      `i-0c9b283b31d6b5ca7` via `vm-winddown.sh` — this is the point where §2's one-time transcript/eval-results backup
      actually fires for AO. Done-when: stopped, EIP disposition decided, Progress Log records the stop date + a
      rollback note (how to restart it if the IONOS box has a problem).
- [ ] [INFRA] P3. After a second, longer confidence window (propose 30 days), terminate the AWS AO VM and its EBS
      volume for good. Done-when: `aws ec2 describe-instances` shows `terminated`, and the final month's GCS DR
      snapshot is confirmed restorable.

## §5. CI-runner cutover (sequenced; independent of §4 — different files, different box)

- [ ] [INFRA] P1. Provision CI-runner's replacement on IONOS per the §1 sizing decision; run `bootstrap-ci-host.sh` +
      `setup-glue-runners.sh install` against it with the §1 credential mechanism. Done-when:
      `setup-glue-runners.sh status` shows both `glue-N` and `writer-N` pools healthy.
- [ ] [INFRA] P1. Confirm a real canary workflow (`reconcile-release-tags`, per
      `central-vm-relaunch-glue-runner-reinstall.md`'s own verification step) claims and completes a job on the new
      IONOS runner. Done-when: a GHA run URL showing SUCCESS on the new runner's label.
- [ ] [INFRA] P2. Run the IONOS CI-runner in parallel with the AWS one for a real window (propose 7 days) — confirm no
      missed jobs vs. the fleet capacity already tuned in `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`.
      Done-when: N days logged, job throughput comparable, zero missed dispatches.
- [ ] [INFRA] P3. Stop, then (after a longer window) terminate AWS CI-runner VM `i-042a6332509482556` — the CI-runner's
      one-time §2 backup fires at the stop step, same as AO's; confirm every `self-hosted,glue` workflow in
      `self-hosted-qg-repos.txt` routes only to the IONOS runner. Done-when: terminated per `describe-instances`, zero
      jobs claimed by the old instance's runner ID in the trailing week.

## §6. Cleanup, validation, and documentation

- [ ] [INFRA] P1. Verify the 2 stray `ci-bootstrap-verify-*` EC2 instances (`i-00c7135c266ed54b9`, `i-0b896cf7f365c9569`
      — confirmed still running as of 2026-08-17, tied to a blocked todo in `ci_satellite_ao_dispatch_batch13_2026_08_13.md`
      gated on an SSM IAM gap) are genuinely idle, then terminate them; note the cleanup in that batch doc's blocked
      todo so it isn't rediscovered as a surprise. Done-when: both terminated, cross-reference added.
- [ ] [INFRA] P2. After both cutovers, confirm the actual first full-month IONOS invoice against the ~$65.52×2 +
      near-zero-egress projection from this plan's "Why" section. Done-when: invoice total logged in the Progress Log
      against the projected figure, with the delta explained if any.
- [ ] [DOC] P2. Fill in `cloud-agnostic-build-lineage.md` (currently an unwritten `status: draft` stub) with the
      provider-abstraction pattern actually built in §2 — its own outline item 6 ("VM launchers … resolve
      cloud-specific tarball URI") is exactly this work. Done-when: the stub is replaced with real content citing
      `vm-launch.sh`/`vm-winddown.sh`, `status:` flips off `draft`.
- [ ] [OPERATOR] P2. Update `cloud-spend-forecast-and-credits-2026-08.md` to record that AO+CI-runner moved to IONOS
      rather than GCP as originally committed, citing this plan + the 2026-08-18 decision. Not a re-litigation of the
      GCP negotiation — flag to whoever owns it, since this changes a number in a live external negotiation. Done-when:
      the doc no longer reads as the current commercial position for this specific spend.

---

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md`, `/codex/05-infrastructure/cloud-agnostic-script-pattern.md`,
  `/codex/05-infrastructure/cloud-agnostic-build-lineage.md` (stub — §6 fills it in), `/codex/05-infrastructure/agent-orchestrator-deploy.md`,
  `/codex/05-infrastructure/vm-tarball-deployment.md`, `/codex/07-security/self-hosted-runner-security-posture.md`,
  `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`,
  `/codex/11-project-management/cloud-spend-forecast-and-credits-2026-08.md` (§6 updates it).

## Progress Log

- **2026-08-18**: Plan authored after a 4-agent parallel research pass (AO bootstrap internals, prior cloud-agnostic
  work, CI-runner provisioning, runtime topology/credentials). Surfaced + resolved the GCP-commitment conflict and the
  AO-vs-human dispatch question with the operator before writing this file (see Decision log above). Not yet executed.
- **2026-08-18**: Operator asked what gets backed up off the running AO VM specifically, prompted by wanting historical
  token/turn data for an in-progress model-provider comparison. Read `gcs_sync.py`, `transcript_log.py`,
  `context_probe.py`, `config.py`, and the `omniroute-eval` harness in full — confirmed two real, previously-unflagged
  backup gaps (Claude Code session transcripts, and the `omniroute-eval/results/` bake-off output — both local-only,
  neither covered by the existing SnapshotLoop) and added todos to §2 closing them, gated ahead of any AWS VM
  stop/terminate step. Ruled out several other candidates as non-gaps after reading them (learned_context_windows.json,
  process-category-sampler's snapshot cursor, account credential env files) — see §2 todos for the verified reasoning.
- **2026-08-18**: Operator directive — the transcript/eval-results backup does NOT need periodic (30-min) cadence like
  state.json/SQLite; it only needs to run once, at migration time. Revised §2's three transcript/eval-results todos to
  drop all `SnapshotLoop` periodic-tick wiring — `vm-winddown.sh` is now the sole invocation point for both uploads,
  fired once per box at its stop step (§4/§5). Simpler scope: no new background-thread cadence to build or verify,
  just two upload functions plus one call site.
