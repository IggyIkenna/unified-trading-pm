---
doc_type: plan
title: Migrate AO + CI Runner from AWS to IONOS Cloud Cubes
summary:
  Move agent-orchestrator-vm-1 and ci-escalation-runner-vm-1 off AWS EC2 to IONOS Cloud Cubes for cost — building the
  first-ever VM create/bootstrap/decommission launcher for either box as a provider-abstracted shim so a future move to
  another cloud is a config change, not a rewrite. AWS boxes are stopped, not terminated — retained as a documented,
  agent-executable disaster-recovery standby (90-day minimum floor).
status: draft
nature: design
asset_group: [ao, ci, infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [migration, cost, cloud-agnostic, ionos, aws, vm-launcher, infra, disaster-recovery]
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
last_updated: 2026-08-19
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 17
estimate_calibrated_ai_days: 14
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
- **2026-08-18, operator decision**: AO/CI's cloud-agnosticism reuses the existing `CLOUD_PROVIDER` + UCI-factory
  pattern (`/codex/05-infrastructure/cloud-agnostic-script-pattern.md`) rather than inventing a parallel mechanism —
  `bootstrap_vm.sh`'s own `CLOUD_PROVIDER` toggle (already cleanly separate from UTL's storage-client selection; AO's
  server code never branches storage on it) gets `ionos` added directly as a third value. Whether AO/CI should instead
  depend on a slimmed standalone cloud-abstraction package rather than full `unified_trading_library` (avoids the
  scipy/pandas dependency weight — relevant if AO/CI is ever leased or self-hosted separately from the core trading
  system) was raised and deliberately deferred: `cloud_interface` stays inside UTL for now, extraction to its own
  package scoped as a **~March 2027** initiative, not blocking this migration. Logged as an Open Question in
  `cloud-agnostic-script-pattern.md` for future pickup.
- **2026-08-18, operator decision**: neither AWS box is terminated. Both are **stopped and retained as a documented,
  agent-executable disaster-recovery standby**, minimum **90-day** retention floor (re-evaluate no earlier than
  **2026-11-16**, `[OPERATOR]`-gated — continued retention vs. termination is a human call each time, never an
  automatic follow-on). Rationale: AWS's observability/debug tooling (CloudWatch, SSM, Cost Explorer) is more mature
  than anything IONOS offers or that this plan builds fresh — going all-in on a single, newly-adopted provider for both
  compute boxes felt premature. This reverses §4/§5's original "terminate" framing — see the rewritten §4/§5 P3 todos
  and the new §6 DR-runbook todo. EBS volumes, Elastic IPs, and the existing CloudWatch/EventBridge config are all
  retained on both AWS boxes specifically so restart-and-serve stays a real option, not a from-scratch rebuild.
- **2026-08-19, cross-plan input (not an operator decision, a design note from a sibling effort)**: AO's server is
  being containerized under `/plans/archive/2026_08/agent_orchestrator_ldr_main_promotion_and_qg_hardening_2026_08_19.md`
  (archived 2026-08-20; the Docker wrap-not-replace decision is now also captured durably in
  `/codex/04-architecture/runtime-deployment-topology.md`) Phase 4,
  explicitly motivated by making cross-cloud moves easier — this migration is its first real test. The
  containerization decision itself: Docker **wraps** the existing self-pull/restart deploy model, it does not
  replace `ao-self-pull.sh`'s mechanics — "how a new version reaches the running box" still flows through the
  same self-pull-detects-a-new-LDR-commit trigger, just rebuilding/restarting a container instead of restarting a
  bare uvicorn process. This plan's own §1/§2 VM-lifecycle-abstraction and `bootstrap_vm.sh` `ionos`-branch design
  work was authored before this existed — not wrong, but should account for it when picked up (see the updated §1
  todo). This plan does NOT need to change its own sequencing or scope for this now; it's context for whoever
  next touches §1/§2, not a new blocking dependency (§3's IONOS account signup is still the actual blocker).

## Why (cost baseline from this session's research)

Current AWS spend on these two boxes ≈ **$1,700/mo** (CI VM ~$550 + AO ~$1,000 + ~$200 misc, per the cloud-spend-forecast
doc), including a **real, AWS-billed internet-egress line item of ~$213/mo** (~1.97TB, ap-northeast-1, confirmed via
Cost Explorer, not the inflated CloudWatch `NetworkOut` metric which also counts private/internal VPC traffic).
Projected on IONOS Basic Cube XL ($65.52/mo, 16vCPU/32GB/960GB NVMe, first 2TB/mo egress pooled-free per contract):
~$65.52 × 2 boxes + near-zero egress overage at current traffic, materially cheaper even before weighing CI-runner
right-sizing.

**DR-standby overhead (new, 2026-08-18 decision)**: keeping both AWS boxes stopped (not terminated) is not free —
EBS volume storage keeps billing at the stopped rate, and Elastic IPs bill ~$0.005/hr each regardless of attach state
since Feb 2024. Rough estimate (not a live AWS quote): AO's 700GiB EBS + EIP ≈ $65-70/mo; CI-runner's 290GB EBS + EIP
≈ $30/mo — **~$95-105/mo combined** during the retention window. Net savings vs. today's ~$1,700/mo AWS spend are
still ~$1,470/mo (~86%) even carrying both boxes as a standby; confirm the exact figure against the real invoice per
§6's existing invoice-reconciliation todo, extended to net out this overhead too.

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
- ✅ Both AWS boxes are **stopped (not terminated)** after their confidence windows and retained as documented DR
  standbys, with a proven ≤1-hour agent-executable failback runbook — not decommissioned.
  - **Verification**: `aws ec2 describe-instances --region ap-northeast-1` shows `stopped` (not `terminated`) for both
    boxes; a real timed dry-run of the §6 failback runbook completes within 1 hour, elapsed time logged.
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
      elsewhere as the weaker option). **Operator-confirmed 2026-08-18**: try (a) first, per the Handoff exception
      above; fall back to (b)/(c) only if genuinely blocked. Done-when: a Progress Log entry names the chosen mechanism
      + why.
- [x] [DESIGN] P1. ✅ Decide CI-runner's remote-access model to replace AWS SSM (today's *only* remote-exec path — zero
      SSH, zero inbound security-group rules). IONOS has no SSM equivalent. **Operator-confirmed 2026-08-19**: plain
      SSH, key-based auth, **no IP-allowlist** — replicate AO's own existing SSH-access pattern
      (`agent-orchestrator-deploy.md`'s "SSH access" section: private key stored in Secrets Manager, fetched to the
      operator's laptop on demand; key possession is the actual access control today, not source IP). Rejected a
      jump-host/IP-allowlist design: the caller here is an operator's laptop/mobile with no stable IP to allowlist, so
      the friction wouldn't buy anything AO's own precedent doesn't already accept — this is a rare, ops-only channel
      (debugging a wedged runner pool, pushing a direct fix), not something needed from a fixed location. Key
      rotation/storage follows §1's secrets-consolidation decision above (GCP Secret Manager). Done-when: a written
      decision on access model + firewall posture, logged in the Progress Log. ✅ met by this entry.
- [ ] [DESIGN] P1. Decide the AO metrics/recovery replacement for the AWS CloudWatch agent (mem/swap/disk) and the
      EventBridge+Lambda auto-reboot-on-alarm mechanism (`agent-orchestrator-api-host.md`) — both AWS-native, no IONOS
      equivalent, needed for the **IONOS** box only. Evaluate a plain systemd/self-hosted metrics exporter driving
      recovery off the existing `GET localhost:8765/health` endpoint instead of a cloud-native alarm. **Note (2026-08-18
      DR-standby decision)**: the AWS box's own existing CloudWatch agent + EventBridge/Lambda config is left running
      untouched — it's part of what makes the retained AWS box a real, monitorable standby, not dead weight. Done-when:
      a written decision for the IONOS replacement.
- [ ] [DESIGN] P1. Design the provider-abstraction shape for VM lifecycle (create/start/stop/delete + floating-IP +
      firewall) covering AWS EC2 and IONOS Cloud API today, shaped so a third provider is a new case, not a rewrite —
      extend the `--cloud-provider {aws,gcp}` convention already threaded through `bootstrap_vm.sh` rather than
      inventing a parallel mechanism. **Dependency scope resolved 2026-08-18** (see Decision log): this is a
      `bootstrap_vm.sh`-local extension only, not a new shared library — `cloud_interface` stays inside
      `unified_trading_library` for now. Target architecture: extract it into a standalone cloud-abstraction package
      (no scipy/pandas dependency chain) that AO/CI would depend on instead of full UTL — scoped as a ~March 2027
      initiative (leasability/self-host argument, see `cloud-agnostic-script-pattern.md` Open Questions), not this
      migration. Done-when: a short design note (Progress Log or a codex stub) names the abstraction's shape and which
      ad hoc AWS/GCP branches it replaces. **Cross-plan input, 2026-08-19 (see Decision log)**: AO's server is being
      containerized (separate effort,
      `/plans/archive/2026_08/agent_orchestrator_ldr_main_promotion_and_qg_hardening_2026_08_19.md` (archived
      2026-08-20; the Docker wrap-not-replace decision is now also captured durably in
      `/codex/04-architecture/runtime-deployment-topology.md`) Phase 4)
      — a Docker image, not the bare `uv`-venv install `bootstrap_vm.sh` provisions today. When this todo is picked
      up, evaluate whether the AWS-vs-IONOS abstraction shrinks to "provision compute + firewall + a container
      runtime, then `docker pull` + `docker run` the image" rather than replicating the full Python-venv bootstrap
      per provider — containerizing was explicitly motivated by cross-cloud portability, so this migration is its
      first real test. Not a mandate to redesign now; just don't design the venv-based abstraction blind to this.
- [ ] [DESIGN] P1. Decide CI-runner's IONOS sizing. Current `m8i.2xlarge` is 8vCPU/32GB; no exact Cube tier matches
      (Basic Cube L = 8vCPU/16GB, Basic Cube XL = 16vCPU/32GB). **Operator-confirmed 2026-08-18**: Basic Cube XL,
      accepting the over-provisioned-cost delta rather than risking memory pressure on the 25-pool runner load at L's
      16GB. Done-when: a Progress Log entry records the confirmed tier + the cost delta vs. L.

## §2. Build — the portable launcher + bootstrap extension (depends on §1 decisions landing first)

- [ ] [INFRA] P1. Author `scripts/vm-launch.sh --provider {aws,ionos} --role {ao,ci-runner}` provisioning compute +
      floating/public IP + firewall rules + boot disk on either provider — net-new for **both** clouds (no launcher
      exists today even for AWS; AO's EIP/SG/EBS were hand-provisioned per `docs/ikenna-vm-setup.md`). Done-when:
      running it against IONOS produces a reachable Basic Cube XL with SSH key-based access per §1's remote-access
      decision (no IP-allowlist).
- [ ] [INFRA] P1. Extend `bootstrap_vm.sh`'s `--cloud-provider` branch with `ionos` (or the generalized path from §1)
      for: IMDSv2-equivalent metadata lookup, external-IP resolution, and self-registration private-IP lookup — each
      currently AWS/GCP-only with an `unknown-vm` fallback already present. Also flip the script's own default off
      `CLOUD_PROVIDER="${CLOUD_PROVIDER:-aws}"` (line 56) once IONOS is primary, or require the flag explicitly — a
      bare invocation must not silently fall into AWS-specific branches on an IONOS box. Done-when:
      `bootstrap_vm.sh --cloud-provider ionos` completes on a fresh Cube with zero AWS-specific call failures, and a
      flagless invocation on an IONOS box fails loud rather than guessing `aws`.
- [ ] [INFRA] P1. Replace the AWS Secrets Manager calls in `bootstrap_vm.sh` with the GCP-Secret-Manager-only path from
      §1; keep the AWS branch working unchanged for any box still on AWS mid-transition (including the retained
      DR-standby boxes, which still need their existing secrets flow to work if ever restarted). Done-when: a fresh
      IONOS bootstrap fetches every needed secret with zero AWS API calls in its trace.
- [ ] [INFRA] P2. Drop the CloudWatch agent install from the `ionos` branch only; wire the §1 metrics/recovery
      replacement there. The AWS branch's CloudWatch agent install stays untouched (needed for the retained AWS
      DR-standby boxes). Done-when: `systemctl status` on the IONOS box shows the replacement running, no
      `amazon-cloudwatch-agent` unit present; the AWS branch is unchanged (diff shows no AWS-path deletions).
- [ ] [INFRA] P2. Author the paired `scripts/vm-winddown.sh --provider {aws,ionos} --instance <id>` — also net-new
      (today's cost control is a manual `aws ec2 stop-instances`) — that snapshots final state (reusing the existing
      `restore_from_gcs.sh`-compatible SnapshotLoop artifact), deregisters DNS if applicable, and **stops** (never
      deletes/terminates — no `--terminate` flag exists on the AWS path; deletion is IONOS-only, for disposable test
      boxes) the instance. Done-when: run against a disposable test box on either provider, nothing left billing on
      IONOS after a delete, a resumable snapshot left in GCS, and the AWS path leaves the instance in `stopped` state
      with its EBS/EIP intact.
- [x] [INFRA] P2. ✅ Fix every hardcoded reference to AO's Elastic IP `13.113.200.22` to resolve through the DNS name
      `api.agent-orchestrator.odum-research.com` instead — named instances: `orchestrator_vm_registry.yaml`,
      `install_ldr_to_main_promote_heartbeat.sh`, `install_qg_baseline_daily_promote.sh`,
      `install_template_drift_daily_check.sh`, `cron_liveness_watchdog.py`. **Resolved 2026-08-19** — did the careful
      per-file read the prior evaluation deferred (see Progress Log). Finding: none of the 5 named files used the bare
      IP as a real connection target, so the original Done-when ("zero hits outside DNS-zone config") was
      unachievable as literally written — it would require scrubbing archived docs (frozen historical record) and the
      new DR-failback runbook, which deliberately hardcodes the AWS IP on purpose. Actual Done-when met: the 4
      comment-only scripts now point at the DNS name instead of the bare EIP so they don't go stale post-migration;
      `orchestrator_vm_registry.yaml`'s `public_ip:` field is unchanged (legitimately needs the current IP; its
      sibling `fqdn:`/`api_url:` fields already carry the DNS name).
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
      boundary rather than widening it, but flag if tighter scoping is wanted. **Code shipped
      `agent-orchestrator@946eeaba51`** (2026-08-18): `upload_claude_transcripts_to_gcs`/`_s3` +
      `_iter_claude_transcript_files` added to `gcs_sync.py`, unit-tested (`tests/test_migration_backup_uploads.py`,
      `quality-gates.sh --no-fix` green: 4118 passed, basedpyright 0 errors). **Not yet checked off** — Done-when
      specifically requires running it against the live VM, which needs `vm-winddown.sh` to exist and call it (see the
      wiring todo below); the function itself is done, its live invocation isn't.
- [ ] [INFRA] P1. Close the second gap found this session: `omniroute-eval/results/` — the live model-provider
      bake-off's actual output (`provider-matrix.sh`, one JSONL row per model×task cell; this is the in-progress
      "compare context tokens/turns across providers" work) — is git-ignored
      (`agent-orchestrator/.gitignore:193`) and uploaded nowhere; local-only. Add a GCS/S3 upload (same key-layout
      pattern, `eval-results/<vm_id>/<date>/...`) — also a **one-time, migration-time call only**, not wired into any
      periodic loop or per-run hook (same operator directive as above). **Code shipped `agent-orchestrator@946eeaba51`**
      (2026-08-18): `upload_eval_results_to_gcs`/`_s3` added to `gcs_sync.py`, same unit-test file, same green gate run.
      **Not yet checked off** — same reason as above, Done-when needs the live-VM run via `vm-winddown.sh`.
- [ ] [INFRA] P1. Wire BOTH of the above into `vm-winddown.sh` (§2's new decommission script) as the one-time
      pre-stop backup step — this is the ONLY invocation point for either upload (no periodic `SnapshotLoop` wiring,
      per operator directive). Done-when: running `vm-winddown.sh` against a test box confirms its transcripts and
      eval-results both land in GCS/S3 before the instance stops. **§4's and §5's AWS-VM stop todos are gated on this
      landing first** — do not stop either AWS box until this exists and has been verified.
- [ ] [DOC] P2. Document the two closed gaps + the new `transcripts/`/`eval-results/` GCS/S3 key layout in
      `vm-log-archival.md` (the existing canonical-paths SSOT for exactly this class of problem) — note there
      explicitly that these two are one-time migration-triggered backups, unlike every other row in that doc's table
      which is a standing periodic/pre-kill contract. Done-when: the doc's path table gains the two new rows.

## §3. IONOS account setup

- [ ] [OPERATOR] P0. Create the IONOS Cloud contract/account — **signup in progress 2026-08-18**. Remaining: generate
      API credentials for the §2 launcher, store them in GCP Secret Manager per the §1 consolidation decision.
      Done-when: an IONOS API token exists in GSM and `vm-launch.sh --provider ionos --dry-run` authenticates
      successfully.

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
- [ ] [INFRA] P2. After a stability window (7 days), **stop** AWS AO VM `i-0c9b283b31d6b5ca7` via `vm-winddown.sh` —
      this is the point where §2's one-time transcript/eval-results backup actually fires for AO. Done-when: stopped,
      EIP kept allocated (not released), Progress Log records the stop date + confirms the box is the DR standby per
      the Decision log (not a termination candidate).
- [ ] [OPERATOR] P3. **Not termination** — re-evaluate AO's AWS DR-standby status no earlier than **2026-11-16** (90
      days from the stop date). This is a standing review checkpoint, not an automatic action: at that point, decide
      whether to keep retaining it, extend the window, or finally terminate. Done-when: a Progress Log entry records
      the 2026-11-16 (or later) review outcome — do not action this before the date without a fresh operator decision.

## §5. CI-runner cutover (sequenced; independent of §4 — different files, different box)

- [ ] [INFRA] P1. Provision CI-runner's replacement on IONOS per the §1 sizing decision; run `bootstrap-ci-host.sh` +
      `setup-glue-runners.sh install` against it with the §1 credential mechanism. Done-when:
      `setup-glue-runners.sh status` shows both `glue-N` and `writer-N` pools healthy.
- [ ] [INFRA] P1. Confirm a real canary workflow (`reconcile-release-tags`, per
      `central-vm-relaunch-glue-runner-reinstall.md`'s own verification step) claims and completes a job on the new
      IONOS runner. Done-when: a GHA run URL showing SUCCESS on the new runner's label.
- [ ] [INFRA] P2. Run the IONOS CI-runner in parallel with the AWS one for a real window (7 days) — confirm no missed
      jobs vs. the fleet capacity already tuned in `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`. Done-when:
      7 days logged, job throughput comparable, zero missed dispatches.
- [ ] [INFRA] P3. After the 7-day parallel-run window, **stop** (do not terminate) AWS CI-runner VM
      `i-042a6332509482556` — the CI-runner's one-time §2 backup fires at this stop step, same as AO's; confirm every
      `self-hosted,glue` workflow in `self-hosted-qg-repos.txt` routes only to the IONOS runner. Done-when: stopped
      (not terminated) per `describe-instances`, EBS retained (no public EIP on this box — SSM-only, same as its
      pre-migration access model, per `central-vm-relaunch-glue-runner-reinstall.md`), zero jobs claimed by the old
      instance's runner ID in the trailing week.
- [ ] [OPERATOR] P3. **Not termination** — re-evaluate CI-runner's AWS DR-standby status no earlier than **2026-11-16**
      (90 days minimum, same floor as AO's, standing review checkpoint). Done-when: a Progress Log entry records the
      review outcome — do not action before the date without a fresh operator decision.

## §6. Cleanup, validation, and documentation

- [ ] [INFRA] P1. Verify the 2 stray `ci-bootstrap-verify-*` EC2 instances (`i-00c7135c266ed54b9`, `i-0b896cf7f365c9569`
      — confirmed still running as of 2026-08-17, tied to a blocked todo in `ci_satellite_ao_dispatch_batch13_2026_08_13.md`
      gated on an SSM IAM gap) are genuinely idle, then terminate them; note the cleanup in that batch doc's blocked
      todo so it isn't rediscovered as a surprise. Done-when: both terminated, cross-reference added. (Unrelated to the
      AO/CI-runner DR-standby decision above — these two are disposable verification scratch instances, not the
      production boxes.)
- [ ] [DOC] P1. **New, 2026-08-18**: author the AWS DR-standby failback runbook — `/codex/15-runbooks/aws-dr-standby-failback-ao-ci.md`
      (with `owner`/`cadence`/`verifier`/`last_executed` frontmatter per CLAUDE.md's runbook requirement) — covering,
      for both boxes: `aws ec2 start-instances`, re-verifying CloudWatch/SSM/SnapshotLoop resume cleanly after restart,
      re-pointing DNS (`api.agent-orchestrator.odum-research.com`) back to the AWS EIP if IONOS is the one that's down,
      re-verifying CI-runner's GHA registration and pool health, and a rollback note for un-doing the failback once
      IONOS recovers. Must be written so an agent with zero tribal knowledge of this migration can execute it
      correctly — exact commands, no "you'll know it when you see it" steps. Done-when: a real timed dry-run (starting
      one of the stopped boxes, walking the runbook, confirming it serves real traffic/claims a real job) completes in
      **under 1 hour**, elapsed time and any friction points logged in the Progress Log, then the box is re-stopped.
      **Runbook authored + shipped `unified-trading-pm@6ff00d4ca7`** (2026-08-18) — the doc itself is done; the timed
      dry-run is not (needs a real stopped AWS box to run against, which doesn't exist until §4/§5's stop steps land).
- [ ] [INFRA] P2. After both cutovers, confirm the actual first full-month IONOS invoice against the ~$65.52×2 +
      near-zero-egress projection from this plan's "Why" section, **and** confirm the AWS DR-standby overhead against
      the ~$95-105/mo estimate. Done-when: both invoice totals logged in the Progress Log against their projected
      figures, with deltas explained if any.
- [ ] [DOC] P2. Fill in `cloud-agnostic-build-lineage.md` (currently an unwritten `status: draft` stub) with the
      provider-abstraction pattern actually built in §2 — its own outline item 6 ("VM launchers … resolve
      cloud-specific tarball URI") is exactly this work. Done-when: the stub is replaced with real content citing
      `vm-launch.sh`/`vm-winddown.sh`, `status:` flips off `draft`.
- [ ] [OPERATOR] P2. Update `cloud-spend-forecast-and-credits-2026-08.md` to record that AO+CI-runner moved to IONOS
      rather than GCP as originally committed, citing this plan + the 2026-08-18 decision, and to note the AWS spend
      isn't fully zeroed out (DR-standby overhead ~$95-105/mo). Not a re-litigation of the GCP negotiation — flag to
      whoever owns it, since this changes a number in a live external negotiation. Done-when: the doc no longer reads
      as the current commercial position for this specific spend.

---

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md`, `/codex/05-infrastructure/cloud-agnostic-script-pattern.md`,
  `/codex/05-infrastructure/cloud-agnostic-build-lineage.md` (stub — §6 fills it in), `/codex/05-infrastructure/agent-orchestrator-deploy.md`,
  `/codex/05-infrastructure/vm-tarball-deployment.md`, `/codex/07-security/self-hosted-runner-security-posture.md`,
  `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`,
  `/codex/15-runbooks/aws-dr-standby-failback-ao-ci.md` (new — §6 authors it),
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
- **2026-08-18**: Discussed whether AO/CI's cloud-agnosticism should follow the fleet-wide `CLOUD_PROVIDER`/UCI-factory
  pattern (`cloud-agnostic-script-pattern.md`) and which library it should depend on. Confirmed `bootstrap_vm.sh`'s
  `CLOUD_PROVIDER` toggle is already cleanly separate from UTL's storage-client selection (AO's server code never reads
  it for storage; `gcs_sync.py` hardcodes both GCS+S3 explicitly for its Tier-4 dual-write) — extending it with `ionos`
  is a low-risk, local change, no shared-library rework needed. Raised whether AO/CI should depend on a slimmed
  standalone cloud-abstraction package instead of full UTL (leasability/self-hosting argument — UTL pulls
  scipy/pandas/scikit-learn transitively, already proven painful for the CI VM's resource-history-sampler venv, see
  `ci_vm_exposure_remediation_2026_08_06.md`). Operator decision: defer — `cloud_interface` stays under UTL for now,
  extraction scoped to ~March 2027, not this migration (logged in `cloud-agnostic-script-pattern.md` Open Questions).
  §1's provider-abstraction-shape todo updated to record this. Also flagged: `bootstrap_vm.sh` currently defaults
  `CLOUD_PROVIDER` to `aws` (line 56) — needs to flip once IONOS is primary, else a bare invocation without an explicit
  `--cloud-provider` flag silently tries AWS branches on an IONOS box; folded into §2's bootstrap-extension todo.
- **2026-08-18**: Operator confirmed 3 of §1's open decisions in the interactive chat: (1) CI-runner GH credential —
  try the IONOS WIF-equivalent first per the plan's existing Handoff exception, `GH_PAT` only if genuinely blocked; (2)
  CI-runner sizing — Basic Cube XL, accepting the over-provisioned cost delta; (3) confidence windows — **7-day stop /
  14-day terminate** for both AO and CI-runner. CI-runner's remote-access-model question (SSM replacement) got an
  answer that reads as being about the AO **dashboard's** login/auth (mobile+laptop access, IP-allowlist friction)
  rather than the CI-runner's admin-exec channel the question actually asked about — these are two different surfaces
  (dashboard is already JWT/login-authed over public HTTPS per §4's DNS cutover, not IP-gated; CI-runner remote-exec is
  a rare, admin-only ops path, not something touched from a phone day-to-day). Held open pending clarification.
- **2026-08-18**: Operator revised the "14-day terminate" decision from the entry above — clarified they meant the AWS
  boxes should be **stopped, not terminated at all**, kept as a long-term (**90-day minimum**) disaster-recovery
  standby: AWS's observability/debug tooling is more mature than what IONOS offers or what this plan builds fresh, and
  going all-in on one newly-adopted provider felt premature. Explicit requirement: the failback path must be
  documented clearly enough that an agent (not just the operator) could execute it correctly within an hour. Rewrote
  §4/§5's P3 "terminate" todos into "stop, retain, review-no-earlier-than-2026-11-16" todos; added a new §6 todo to
  author `/codex/15-runbooks/aws-dr-standby-failback-ao-ci.md` and prove it via a real timed (<1hr) dry-run; updated
  the Full-execution criterion, "Why" cost section (added the ~$95-105/mo standby overhead estimate, not yet a live
  quote), and §1's CloudWatch/EventBridge design item to clarify the AWS-side config is kept, not replaced (only the
  IONOS box needs a new metrics/recovery mechanism). Estimate bumped +1 baseline/+1 calibrated day for the new runbook
  + dry-run work. CI-runner's remote-access-model question (previous entry) remains open regardless of this change —
  it's about the admin-exec channel's auth model, orthogonal to the stop-vs-terminate decision.
- **2026-08-18**: Operator directive — do as much of §1/§2's build work as possible before IONOS credentials exist
  (account signup in progress, §3). Authored + shipped `/codex/15-runbooks/aws-dr-standby-failback-ao-ci.md` (the new
  §6 runbook todo — `unified-trading-pm@6ff00d4ca7`), then shipped the two credential-independent §2 backup functions:
  `upload_claude_transcripts_to_gcs`/`_s3` and `upload_eval_results_to_gcs`/`_s3` in `gcs_sync.py`
  (`agent-orchestrator@946eeaba51`), unit-tested via `tests/test_migration_backup_uploads.py`, full
  `quality-gates.sh --no-fix` green (4118 passed, basedpyright 0 errors). Both §2 todos annotated but left unchecked —
  Done-when needs a live-VM run, which is gated on `vm-winddown.sh` existing. Evaluated the "fix hardcoded EIP
  references" §2 todo and held off: none of the 5 named files actually use the IP as a live connection target
  (`orchestrator_vm_registry.yaml`'s `public_ip:` field structurally needs to hold whichever IP is current, not a DNS
  string; the rest are code comments) — not the safe mechanical find-replace the todo implied, needs a more careful
  pass rather than a rushed mass-edit. Remaining credential-independent §2 work (`bootstrap_vm.sh`'s `ionos` branch,
  the AWS-Secrets-Manager-to-GCP-only replacement, `vm-launch.sh`/`vm-winddown.sh` themselves) needs either real IONOS
  API knowledge to do well or touches AO's live bootstrap script directly — higher blast-radius, held for the
  operator's go-ahead rather than rushed.
- **2026-08-19**: Resolved both items the prior Deferred-work table flagged as not blocked on credentials.
  **CI-runner remote-access model** (§1): operator confirmed plain SSH, key-based auth, no IP-allowlist — replicates
  AO's own existing SSH-access pattern (`agent-orchestrator-deploy.md`: private key in Secrets Manager, fetched to the
  operator's laptop on demand; key possession is the real control today, not source IP) rather than building new
  jump-host/allowlist machinery for a caller (an operator's laptop/mobile) with no stable IP to allowlist anyway.
  **Hardcoded-EIP-reference fix** (§2): did the careful per-file read the prior evaluation deferred — read all 5 named
  files plus every other hit of `13.113.200.22` across both repos (~150 total). Finding: none of the 5 used the bare
  IP as a real connection target — `orchestrator_vm_registry.yaml`'s `public_ip:` field legitimately needs to hold the
  current IP (its sibling `fqdn:`/`api_url:` fields already carry the DNS name); the other 4
  (`cron_liveness_watchdog.py`, `install_qg_baseline_daily_promote.sh`, `install_ldr_to_main_promote_heartbeat.sh`,
  `install_template_drift_daily_check.sh`) were header comments naming which VM to run the installer on, not
  executable code. The remaining ~150 hits are archived plans/issue docs (frozen historical record, correctly
  untouched), active-plan logged evidence of past commands (also historical record), or the new DR-failback runbook,
  which deliberately hardcodes the AWS IP on purpose — bypassing DNS during a failback IS the point. Shipped fix:
  updated the 4 comment-only scripts to reference the DNS name + `orchestrator_vm_registry.yaml` instead of the bare
  EIP so they don't go stale post-migration — `unified-trading-pm@9a3471df9c`. No `agent-orchestrator` repo changes
  needed — its 6 hits were comment-only re-derivation examples or the documented DNS-bypass diagnostic in
  `ao_client.sh`, both correct as-is.

## Deferred work after 2026-08-19

| Item                                                                            | State / why deferred                                                                             | Blocked on                                                          |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| §2: `bootstrap_vm.sh` `ionos` branch, AWS-Secrets-Manager→GCP swap, `vm-launch.sh`, `vm-winddown.sh` | Not done — deliberately held back, not attempted blind                                             | Real IONOS API access to build/verify correctly; touches AO's live bootstrap script (operator go-ahead wanted given blast radius) |
| §2: wire transcript/eval-results uploads into `vm-winddown.sh`                   | Cannot be done yet — the functions exist (`agent-orchestrator@946eeaba51`) but have no caller       | `vm-winddown.sh` doesn't exist yet (row above)                          |
| §3: IONOS account/API token                                                      | In progress                                                                                          | Operator (signup underway as of 2026-08-18)                             |
| §4/§5: actual cutover (provision, shadow-observe, DNS, stop)                     | Cannot be done yet                                                                                   | §3's IONOS API token                                                    |
| §6: failback-runbook timed dry-run                                               | Cannot be done yet — the runbook itself is done (`unified-trading-pm@6ff00d4ca7`)                   | A real stopped AWS box, which only exists after §4/§5's stop steps      |
| §6: cloud-spend-forecast doc update, invoice reconciliation                      | Operator-owned / cannot be done yet                                                                 | Operator needs to flag the GCP-negotiation owner; invoice check needs a full IONOS billing cycle |

**Recommended next item**: every item flagged as not-blocked-on-credentials is now resolved. Everything left waits on
§3's IONOS API token landing in GSM — once it does, `vm-launch.sh` + `bootstrap_vm.sh`'s `ionos` branch unblocks the
rest of §2/§4/§5; start there.
