---
title:
  Human-work backlog 2026-05-20 — Ikenna + Harsh interactive task split with data_pipeline_master_coordination
  supervision
status: active
created: 2026-05-20
updated: 2026-05-20 # split principles + Phase 7/14 sub-splits + supervision-checkpoint wiring
co-operators: [harsh]
related:
  - cursor-configs/CLAUDE.md § "Human-vs-Agent work split"
  - plans/active/data_pipeline_master_coordination_2026_05_20.md # phase-of-record for the heartbeat work
  - plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md
  - plans/active/issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md
  - codex/08-workflows/deployment-flow.md # CI/CD + main-via-staging-and-sit path Harsh owns
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-05-21
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
---

# Human-work backlog — slots 1 (Ikenna) + 2 (Harsh) — 2026-05-20 r2

> **Operator 2026-05-20 r2**: "deeper human actions around credentials and exactly how strategy archetype works need to
> be ikenna. things like backfilling after migration and getting deployment UI fully audited for data status and
> launching VMs on GCP harsh could do. also AWS copies of GCP functionality (manifest, data migrations to AWS etc) he
> could do. the CI/CD pipeline quickmerge and getting repos to main via staging and SIT harsh could also do. for the
> rest we could Q&A and decide how to allocate. main point is that
> `unified-trading-pm/plans/active/data_pipeline_master_coordination_2026_05_20.md` is going on regardless but needs
> some supervision checkpoints which is where ikenna and harsh splits come in."
>
> The principle: **human judgment work** (audits, architectural decisions, archetype design, plan curation, operator UX)
> ≠ **agent work** (QG sweeps, Phase X execution, code cleanup, doc rollout). Both are tracked in backlog.yaml, but
> human work goes to slot 1 (Ikenna's mac) or slot 2 (Harsh's pc) where Claude Opus interactive sessions claim them. The
> dashboard shows them with the same accountability as agent work.

## Split principle (r2)

| Side                            | Owns                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Why                                                                                                                                                                                                         |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ikenna (slot 1)**             | (a) Credentials — operator-facing vendor signups / account creation / paid-tier negotiation per `External Data Is Always Available` rule. (b) Strategy archetype mechanics — exactly-how-it-works calls (allocator math, collateral/liquidation, cross-venue transfer, venue restriction, deployment topology). (c) Cross-repo architectural calls (HARD-RULE codification, deprecation decisions, contract design). (d) Phase 7b DIVERGENT_EMPTY triage (per-cell label-flip-vs-rebackfill judgment). (e) Phase 14 design (dynamic-config + accounts/clients topology shape).                                                                                                                               | Each requires operator-specific context (vendor relationships, archetype intent, custody/legal boundaries, archetype-audit dimension expertise) that doesn't transfer cleanly to an execute-from-spec slot. |
| **Harsh (slot 2)**              | (a) Backfilling after migration — Phase 11 operational data backfill scripts + sample-verify. (b) Deployment UI audit for data status — Phase 9 denominator/numerator fix end-to-end. (c) GCP VM launches — Phase 6 Docker rebuild + writer fleet redeploy + Phase 11 backfill VMs. (d) AWS copies of GCP functionality — Phase 5 AWS bucket migration + manifest consolidator AWS-side. (e) CI/CD pipeline — quickmerge runs + main-via-staging-and-SIT promotion path per `codex/08-workflows/deployment-flow.md`. (f) Phase 7a schema migration (mechanical v<8 → v8 row rewrite). (g) Phase 14 execution (validation harness once Ikenna codifies topology). (h) Per-repo workspace-wide QG green sweep. | All execute-from-spec / run-script-and-verify / single-repo edit shape. Each has a clear cutover criterion that doesn't require the operator's domain context to validate.                                  |
| **Co-owned, bandwidth-claimed** | Adapter scaffolding for BLOCKED-CREDENTIALS items (Helius paid / Glassnode / Kaiko / Polygon.io / Sportradar / The-Odds-API / etc.). Whoever has slot capacity picks up; integration tests stay skipped until Ikenna lands the matching credential.                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Operator decision r2: each adapter scaffold is a standalone backlog task; no fixed split. Trade-off accepted: faster fan-out at the cost of less-clear ownership for unblock-chasing.                       |

## Supervision checkpoint cadence (r2)

**Operator decides per-phase as it lands** (operator decision r2 — no fixed cadence). Mechanism:

- Both Ikenna (slot 1) AND Harsh (slot 2) maintain phase-of-record updates in their own `_agent_pings.md` whenever a
  phase of `data_pipeline_master_coordination_2026_05_20.md` lands GREEN on their side.
- Operator reads both sides' ping ledgers + flags any phase boundary requiring a supervision sync (e.g. "ikenna, look at
  harsh's Phase 5 AWS bucket diff before he kicks off the actual aws s3 sync"). The trigger is operator-set, not
  automatic.
- Neither side gates the other's phase progression by default — but the coordinator's phase ordering remains HARD (do
  not reorder Phase 4 before Phase 1, etc., per the coordinator plan's "DO NOT REORDER" banner).
- Plan reviewer rejects phase-flip commits in `data_pipeline_master_coordination` that don't reference an LDR
  commit-sha + brief evidence line.

**Anti-pattern (review-blocking)**: any side claiming a phase GREEN without (a) the LDR commit-sha, (b) the
verification-criterion result from the coordinator phase table.

## Slot allocation (2026-05-20 reorganisation, r2 confirmed)

| Slot range | Host             | Operator                             | Work type                                                                                       |
| ---------- | ---------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------- |
| **1**      | Ikenna local mac | Ikenna interactive (Claude Opus 4.7) | Human judgment: credentials, archetype mechanics, cross-repo arch, Phase 7b/14-design           |
| **2**      | Harsh local pc   | Harsh interactive (Claude Opus 4.7)  | Execute-from-spec: backfills, deployment-UI audit, GCP VMs, AWS copies, CI/CD, Phase 7a/14-exec |
| **3-20**   | Centralized (VM) | Spawned Sonnet 4.6 workers           | Agent execution: QG sweeps, Phase X tasks, code cleanup, doc rollout                            |
| (separate) | VM               | Main agent `agt-7eb095` (Opus 4.7)   | Auto-resolve /blocked, dispatch phase progression. NO slot — lives in `/api/agents/`            |

**Tier marker**: human-work items use `tier: human-task` in backlog.yaml. The dispatcher does NOT auto-dispatch these
(target_slot ∈ {1, 2} is operator-claimed only). They appear in the dashboard's slot-1/slot-2 panel.

## Curated human-work items (r2 — split-principle aligned)

Each item ships as a backlog.yaml entry with `target_slot: 1` or `2`, `tier: human-task`, `affinity: high`, plus a
`composes_with:` link to the coordinator plan's phase when applicable.

### Ikenna (slot 1) — credentials / archetype / architecture / Phase 7b+14-design

1. **HUMAN-IKENNA-ARCHETYPE-AUDIT** — `issues/strategy_archetype_logic_audit_2026_05_20.md` D1-D14 dimensions.
   Operator-acked tonight to run in parallel with consolidation. **Status: in-progress (operator session).** Composes
   with: Phase -2 Bucket 4 of coordinator. Est: 8 cal-AI-days.

2. ✅ **HUMAN-IKENNA-MEGA-AUDIT-PROGRESSION** — ARCHIVED 2026-05-22. All A-D phases complete; Phase E started (D6
   shipped); Phase F items migrated to `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase F. Archive:
   `plans/archive/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md`.

3. **HUMAN-IKENNA-DATA-PIPELINE-COORDINATION-SUPERVISION** — `data_pipeline_master_coordination_2026_05_20.md`. Phase
   sequencing decisions when blockers surface + Phase 7b DIVERGENT_EMPTY triage (per-cell label-flip-vs-rebackfill calls
   on the 765 cells from A3) + Phase 14 topology design. Est: 0.5 cal-AI-day rolling + 2 cal-AI-days for Phase 7b once
   reached + 2 cal-AI-days for Phase 14 design once Phase 13 lands.

4. **HUMAN-IKENNA-CROSS-CLIENT-ISOLATION-AUDIT** —
   `issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md`. HARD RULE codified 2026-05-20; needs
   validation pass across existing code. Est: 1 cal-AI-day.

5. **HUMAN-IKENNA-PROMOTE-WORKFLOW-REVIEW** — review the promote workflow architecture before May-23 cutover.
   Critical-path call: paper_1d → live_early tonight, live_full post-cutover. Est: 0.5 cal-AI-day.

6. **HUMAN-IKENNA-CREDENTIALS-UNBLOCK-TRACK** — operator-facing credential asks (updated 2026-05-22):
   - ✅ Helius (paid Solana RPC) — key confirmed in Secret Manager
   - ✅ Databento (TradFi ticks) — key confirmed in Secret Manager
   - ✅ The-Odds-API (sports/prediction) — key confirmed in Secret Manager
   - ✅ Polymarket — live feed wired
   - ✅ Footystats — wired
   - ✅ Glassnode — DELETED from system (defunct provider cleanup 2026-05-20)
   - ✅ Sharpapi — DELETED from system (defunct provider cleanup 2026-05-20)
   - ✅ Kaiko — DELETED from system (uac@4afbea7c + mtds@daeb3d5f, 2026-05-22)
   - ✅ Polygon.io — DELETED from system (uac@4afbea7c + mtds@daeb3d5f, 2026-05-22; Polygon L2 blockchain refs
     preserved)
   - 🟡 Kalshi — **ONLY remaining BLOCKED-CREDENTIALS**; prediction spread adapter scaffold ships; integration tests
     `@pytest.mark.requires_credentials`; credential ask filed. File: `pings/slot_1.md`.
   - IntoTheBlock / Sportradar — deferred; not in May-23 critical path Per `External Data Is Always Available` rule.
     Est: 0.1 cal-AI-day (Kalshi only + Kaiko/Polygon.io removal task).

7. **HUMAN-IKENNA-CUSTODY-PROVIDER-DECISIONS** — Copper + CEFFU June-1 onboarding decisions (May-23 ships on
   `CLOUD_KMS_ENCRYPTED`). Cayman vs UK jurisdiction calls per `project_trading_entities` memory + venue-bans-UK gating.
   Est: 1 cal-AI-day rolling.

### Harsh (slot 2) — backfills / deployment-UI / GCP VMs / AWS copies / CI/CD / Phase 7a+14-exec

8. ✅ **HUMAN-HARSH-WORKSPACE-QG-GREEN-SWEEP** — Phase -1 of coordinator: per-repo `bash scripts/quality-gates.sh` exit
   0 workspace-wide. Composes with: `Quality Gates Are A Merge Prerequisite` HARD RULE. Cluster split (per
   `work_split_2026_05_20_ikenna.md` Slots 9-11): A=UAC+UTL+IS / B=MTDS+features+MDPS / C=strategy+execution+ml. Est: 3
   cal-AI-days (1 per cluster). **CLUSTER A COMPLETE 2026-05-21 slot-11**: UAC @ceeaddd ✅ · UTL @4cbe9612 ✅ ·
   instruments-service @b476663 ✅ (all pass with 0 fixes needed) **CLUSTER B COMPLETE 2026-05-21 slot-11**: MTDS
   @33e6762 ✅ · features-service @7a7d4a4c ✅ · MDPS @a00ce6b ✅ (all pass with 0 fixes needed) **CLUSTER C COMPLETE
   2026-05-21 slot-11**: strategy-service @b303a358 ✅ · execution-service @a848ef61 ✅ · ml-service @ea9c187 ✅ (all
   pass with 0 fixes needed) **client-reporting-api FIXED 2026-05-21 slot-11**: @4eafab6 ✅ — ruff lint
   (RUF002/SIM105/B008), import patterns, test fixes (test_production_guard, test_get_invoice_by_id), pip-audit ignores,
   narrow except ArithmeticError **deployment-ui VERIFIED 2026-05-21 slot-11**: @ef3406b ✅ (0 fixes needed, npm install
   required first) **unified-trading-api FIXED 2026-05-21 slot-11**: @ac8a6b9 ✅ — noqa C901 on seed_all_domains,
   pip-audit ignores PYSEC-2024-277/PYSEC-2025-183 **unified-trading-system-ui FIXED 2026-05-21 slot-11**: @38f3e96e ✅
   — TS errors (4 files), stale test assertions, briefings codex path, Suspense boundaries
   (questionnaire/reset-password/verify-email) **e2e-testing FIXED 2026-05-21 slot-11**: @24daef0 ✅ — add ruff dep,
   noqa C901 (5 integration tests), pip-audit ignores PYSEC-2024-277/PYSEC-2025-183/PYSEC-2026-87, ruff autoformat
   **system-integration-tests VERIFIED 2026-05-21 slot-11**: green (0 fixes needed) **ibkr-gateway-infra VERIFIED
   2026-05-21 slot-11**: green (0 fixes needed) **alerting-service VERIFIED 2026-05-21 slot-11**: green (0 fixes needed)
   **batch-live-reconciliation-service VERIFIED 2026-05-21 slot-11**: green (0 fixes needed) **deployment-api VERIFIED
   2026-05-21 slot-11**: green (0 fixes needed) **trading-agent-service VERIFIED 2026-05-21 slot-11**: green (0 fixes
   needed) **position-balance-monitor-service OBSOLETE 2026-05-28**: merged into strategy-service; the local QG fix
   `@7c5f8b7` (pip-audit ignores PYSEC-2024-277/PYSEC-2025-183) is out of scope — re-apply against strategy-service if
   the same issue still exists there. **pnl-attribution-service OBSOLETE 2026-05-28**: merged into strategy-service; the
   local QG fix `@db18812` (pip-audit ignores + session-scoped setup_events fixture in conftest.py) is out of scope.
   **risk-and-exposure-service OBSOLETE 2026-05-28**: merged into strategy-service; the local QG fix `@d350070` (8
   RiskMetrics field name corrections in `risk_metrics.py::log_event` — concentration_pct→concentration,
   drawdown_pct→drawdown, etc.) **may still need to land in strategy-service** — verify whether the consolidated copy
   has the field names right; port if not. **agent-orchestrator VERIFIED 2026-05-21 slot-11**: arch_tier=external, no
   quality-gates.sh — out of scope for this sweep **deployment-service SKIPPED 2026-05-21 slot-11**: locked by slot-10;
   not verified this sweep **SWEEP COMPLETE 2026-05-21 slot-11**: all in-scope service repos verified or locally-fixed.
   ~~3 archived repos require operator unarchive before LDR merge~~ — **resolved 2026-05-28**:
   position-balance-monitor + pnl-attribution + risk-and-exposure all merged into strategy-service; no unarchive needed.
   **Follow-up**: confirm the risk_metrics.py field-name fix is also in strategy-service's consolidated copy; if not,
   re-apply there.

9. **HUMAN-HARSH-PHASE-5-AWS-BUCKET-MIGRATION** — Phase 5 of coordinator: `aws s3 sync` from current bucket names →
   target symmetric names per Phase 1 inventory CSV. Per-asset-group, single-walk discipline. Composes with:
   `aws_migration_defi_first_2026_05_07.md` + Phase 1 cloud-providers.yaml AWS-side templates (already shipped
   2026-05-20 per coordinator Phase 1 GREEN). Est: 5 cal-AI-days. **SCRIPT READY 2026-05-21 slot-11**:
   deployment-service@de78a42 — `scripts/aws/migrate-bucket-names-unified-to-canonical.sh` ships 61 rename pairs;
   dry-run verified (152,161 dex-pools + 68,703 dex-swaps + 30,114 evm-defi + 5,037 solana-defi objects to sync; all
   target buckets confirmed existing). EXECUTION GATED on coordinator Phase 2 (CODE FREEZE, operator action) → Phase 3
   (drain) → Phase 4 (GCS migration GREEN). Pass `--phase4-green --apply` when gate clears.

10. ✅ **HUMAN-HARSH-PHASE-6-DOCKER-VM-FLEET-REDEPLOY** — Phase 6 of coordinator: Docker image build + writer fleet VM
    restart so steady-state writers produce v8 rows. Composes with: `writegate_honest_coverage_endtoend_2026_05_06.md` §
    Phase 7.A. Verification: 100 newest manifest rows per bucket sampled, ALL at `schema_version=8`. Est: 2 cal-AI-days.
    **SCRIPTS READY 2026-05-21 slot-11**: deployment-service@71b9855 (phase3-drain) + deployment-service@ac97607
    (phase6-restart). Phase 7.A audit: MANIFEST_SCHEMA_VERSION=8 confirmed in UTL@c205166fb012; consolidator keep="last"
    verified (new v8 wins); legacy NULL rows source identified (\_backfill_columns sets schema_version=1). All service
    tarballs rebuilt and uploaded to GCS (2026-05-21 14:32Z): UAC@28ac3cde + UTL@c205166f + MTDS@54f46cab +
    instruments@3d8816465 + MDPS@f8fb8485 + ml@29cc7b20 + strategy@b24556a9 + execution@6b2a186d +
    pnl-attribution@b54c4f5a + risk-exposure@878da65d + position-balance@775d6ef7 + batch-live-recon@36fffbd8. EXECUTION
    GATED on Phase 2 CODE FREEZE (operator) → Phase 3 drain (`--apply`) → Phase 4 GCS → Phase 5 AWS
    (`--phase4-green --apply`) → Phase 6 restart (`--phase5-green --apply`).

11. ✅ **HUMAN-HARSH-PHASE-7A-SCHEMA-MIGRATION** — Phase 7 SCHEMA half of coordinator (Phase 7b triage is Ikenna's).
    Migrate every v<8 row → v8 schema mechanically. Composes with: `d3_manifest_v8_finish_2026_05_20.md` +
    `hard_schema_phase1_field_flip_migration_2026_05_19.md`. Verification: A4 v1 re-run shows 100% v8 + 0 NULL across
    all 10 buckets BEFORE 7b triage begins. Est: 4 cal-AI-days. **SCRIPT + TESTS READY 2026-05-21 slot-11**:
    UTL@ec788bad — `unified_trading_library/migrations/upgrade_manifest_to_v8.py` ships complete migration logic +
    `__main__` CLI (`--asset-group`, `--apply`/dry-run) + 16 unit tests (all pass, basedpyright 0 errors). Invoke:
    `python -m unified_trading_library.migrations.upgrade_manifest_to_v8 --asset-group all --apply`. EXECUTION GATED on
    Phase 6 restart (VMs must be writing v8 steady-state BEFORE bulk migration to avoid race). Verification: re-run A4
    audit after migration; 100% v8 + 0 NULL required before Phase 7b triage begins.

12. ✅ **HUMAN-HARSH-PHASE-9-DEPLOYMENT-UI-DENOMINATOR-FIX** — deployment-ui@643a22e — `HonestCoverageStatusCounts`
    split into 5-field canonical formula (expected_unattempted_known_empty + expected_unattempted_pending_fetch);
    coverage_pct comment corrected; CoverageBar renders 5 segments; tooltip fixed; color thresholds green ≥99%/amber
    ≥95%/red <95%; legend updated; test fixture updated; QG green (68 tests, 0 TS errors). Phase 5 of
    honest_coverage_formula_consolidation complete. Phase 8 (master plan Group H re-pull) is separate item — see plan.

13. ✅ **HUMAN-HARSH-PHASE-11-BACKFILL-TO-100PCT** — deployment-service@e81ad9f —
    `scripts/vm/phase11-backfill-coordinator.sh`: sequences IS → MTDS → features launchers in dependency order across
    all 5 asset_groups; hard gate (--phase6-green + --phase7a-green required before --apply); dry-run default; no
    fire-and-forget (each tier waits TERMINATED before next). Dry-run exit 0 verified (28 launchers listed). EXECUTION
    GATED on Phase 6 + Phase 7A complete. Phase 7b triage CSV from Ikenna → re-invoke with --start/--end per-asset-group
    when gates clear.

14. 🟡 **HUMAN-HARSH-CI-CD-PROMOTION-PIPELINE** — PR #8 (LDR → staging) open at
    https://github.com/IggyIkenna/deployment-ui/pull/8. Six pre-existing CI blockers found and fixed: (a) GitHub
    cross-repo private-repo reusable workflow restriction — fixed by creating local copy
    deployment-ui/.github/workflows/ui-quality-gates.yml (within-repo calls work for private repos); (b)
    workspace-qg.yml called python-quality-gates.yml instead of ui-quality-gates.yml (wrong template); (c)
    notify-telegram.yml had duplicate `inputs:` key — merged into single block; (d) notify-failure job in
    ui/infra-quality-gates.yml had relative `./` path (invalid cross-repo) — removed; (e) GH_PAT: required: true caused
    GitHub to reject the reusable workflow call — changed to required: false; (f) top-level `concurrency` block in local
    reusable workflow causes "workflow file issue" — removed. ~~**BLOCKER**: unified-trading-pm is a private repo.
    GH_PAT is required to clone it for quality-gates.sh. deployment-ui does NOT have GH_PAT in its GitHub Actions
    secrets~~ → **CORRECTED 2026-05-28**: GH_PAT lives in GCP Secret Manager
    (`projects/central-element-323112/secrets/ GH_PAT`, created 2026-03-12); operator policy is to fetch it at workflow
    runtime, not stage it in GHA secrets. Workflow fix shipped at `deployment-ui@23973ce` — workspace-qg.yml now calls
    the local `ui-quality-gates.yml` instead of PM's `python-quality-gates.yml`; both `ui-quality-gates.yml` and the
    `dispatch-cloud-build` job auth to GCP via `GCP_SA_KEY` (the GHA secret deployment-ui DOES have),
    `gcloud secrets versions access`-fetch GH_PAT, `::add-mask::` it, consume it via `steps.gh_pat.outputs.gh_pat`. YAML
    validated locally with PyYAML + `actionlint@1.7.1` — both pass. 🔴 **NEW BLOCKER 2026-05-28**: deployment-ui is hit
    by the same GitHub "BuildFailed ghost" tracked in
    [`issues/workspace_qg_ci_startup_failure_2026_05_26.md`](./issues/workspace_qg_ci_startup_failure_2026_05_26.md).
    Ghost workflow_id 283775720 has been firing on every LDR push since 2026-05-26 14:42 UTC instead of the real
    workspace-qg (id 277985037); my commits `23973ce` + `739c4a3` (Option B rename test) + `2fc3854` (rename revert) all
    hit the ghost. Workflow content is correct; only the GitHub server-side cache blocks execution. Updated the issue
    doc to add deployment-ui to the affected-repos list + the Option B-tried-and-failed evidence. **Operator action**:
    ping GitHub Support on ticket https://support.github.com/ticket/personal/0/4422570 (filed 2026-05-27) to extend the
    clear-ghost request to include deployment-ui's ghost 283775720 + real workflow 277985037. Once cleared, PR #8 CI
    will run on the existing workspace-qg.yml content (no further code change needed).

15. **HUMAN-HARSH-LIVE-PIPELINE-VALIDATION** — Phase 12-13 of coordinator: live-mode adapter behavior matches batch-mode
    (per the live=batch HARD RULE) + batch-live symmetry verification. Composes with:
    `live_pipeline_mtds_mdps_features_2026_05_08.md` + `batch_live_symmetry_2026_05_10.md`. Est: 2 cal-AI-days.

16. 🟡 **HUMAN-HARSH-AWS-MANIFEST-CONSOLIDATOR-COPY** — Sub-plan filed 2026-05-21 slot-11:
    [`aws_manifest_consolidator_scope_2026_05_21.md`](./aws_manifest_consolidator_scope_2026_05_21.md) — 2.5
    cal-AI-days; UTL consolidator is cloud-agnostic + AWS Batch/EventBridge Terraform modules already exist → Terraform
    authoring only; GATED on Phase 5 cross-cloud rsync + Phase 6 ECS Fargate. Decision: sub-plan (not
    BLOCKED-OPERATOR-DECISION) — AWS consolidator is required once Phase 6 VMs run.

17. ~~🟡 **HUMAN-HARSH-LAPTOP-MIGRATION-COMPLETE**~~ — **SUPERSEDED 2026-05-22**: laptop migration is no longer needed
    because all slot capacity now runs on centralised AWS VMs via the agent-orchestrator (`orchestrator_master` epic).
    AWS VM slot tokens already issued (slots 13-20, exp 2026-06-20). Steps 1-7 (laptop-side) are moot; step 8 DNS
    cutover not required (epiphany service decommissioned when AWS VMs took over). No action needed.

### Co-owned (claim by bandwidth) — adapter scaffolding for BLOCKED-CREDENTIALS

Each adapter scaffold is a standalone backlog task with `target_slot: 1` (preferred — Ikenna may take while waiting on
vendor sign-up loops) OR `target_slot: 2` (Harsh takes during downtime between data-pipeline phases). Whoever picks it
up ships:

- UAC contract (schema + endpoints from public docs)
- Auth shape (header / OAuth / API key)
- Retry/backoff/rate-limit semantics
- Error classifier via `classify_venue_error()` + ADAPTER_FETCH_FAILED emission
- Manifest emission per writegate Phase 6.x
- Unit tests against mocked API responses
- Integration tests marked `@pytest.mark.requires_credentials` (skipped until creds land)

Items (updated 2026-05-22): each = ~0.3-0.5 cal-AI-day.

- ✅ `ADAPTER-HELIUS-SOLANA-PAID` (DeFi RPC scale) — key in SM; scaffold + integration wired
- 🗑️ ~~`ADAPTER-GLASSNODE-ONCHAIN`~~ — DELETED (defunct provider cleanup 2026-05-20); no adapter to build
- 🗑️ ~~`ADAPTER-KAIKO-CEX-HISTORICAL`~~ — DELETED from system (uac@4afbea7c + mtds@daeb3d5f, 2026-05-22)
- 🗑️ ~~`ADAPTER-POLYGON-IO-TRADFI-TICKS`~~ — DELETED from system (uac@4afbea7c + mtds@daeb3d5f, 2026-05-22)
- ✅ `ADAPTER-DATABENTO-TRADFI` (TradFi alt) — key in SM; scaffold ships; integration enabled
- `ADAPTER-SPORTRADAR-FEED` (Sports) — BLOCKED-CREDENTIALS; scaffold ships; integration tests skipped
- ✅ `ADAPTER-FOOTYSTATS-FEED` (Sports alt) — wired
- ✅ `ADAPTER-THE-ODDS-API` (Sports/Prediction) — key in SM; scaffold ships
- ✅ `ADAPTER-POLYMARKET-FEED` (Prediction) — live feed wired
- 🟡 `ADAPTER-KALSHI-FEED` (Prediction) — **BLOCKED-CREDENTIALS** (only remaining); scaffold ships; integration tests
  `@pytest.mark.requires_credentials`; credential ask in `pings/slot_1.md`

## Post-May-23 / parallel-prep tracks (concurrent with data-pipeline phases)

> **Operator 2026-05-20 r2 follow-up**: "what about the rest of the epics / plans which aren't allocated yet to
> `data_pipeline_master_coordination_2026_05_20.md` like paper trading defi and batch ml for cefi and tradfi and sports
> and batch strategy and execution for those too and paper trading these are tasks that human probably needs to try and
> audit once data is ready and backfilled? even if outside may 23 still worth having in harsh and ikenna as we can
> concurrently prepare for them."
>
> These items don't block May-23 (the gate is the two DeFi archetypes only — `carry_staked_basis` +
> `arbitrage_price_dispersion` per `master_to_live_defi_2026_05_23.md`). They run **concurrently** with the
> data-pipeline coordinator on centralised VM slots, with the human-judgment supervision points landing on slot 1
> (Ikenna) or slot 2 (Harsh) per the same split principle: archetype mechanics + paper-trade audit = Ikenna; batch
> runs + wiring + sample-verify = Harsh.

### Ikenna (slot 1) — archetype mechanics + paper-trade audit per asset_group

18. **HUMAN-IKENNA-PAPER-TRADE-DEFI-AUDIT** — paper-trade audit for the two May-23 DeFi archetypes once paper_1d →
    live_early flows ship. Read paper trades, validate logic matches archetype intent (collateral, liquidation,
    cross-venue transfer, venue restriction, deployment topology dims 9-14 from archetype audit). 3-trading-day
    operator-gate window per `promote_workflow_may23_cli_path_2026_05_10.md`. Composes with:
    `defi_master_2026_05_07.md` + `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` +
    `issues/strategy_archetype_logic_audit_2026_05_20.md`. Est: 3 cal-AI-days (3 trading-day audit window).

19. **HUMAN-IKENNA-CEFI-ARCHETYPE-DESIGN** — archetype mechanics for CeFi tracks: perp-funding carry + spot-perp basis +
    cross-CEX arbitrage. Allocator math, collateral semantics on perp venues (cross vs isolated margin), liquidation
    safety bands, venue restriction matrix (which CEXes Cayman-only). Composes with: `epics/cefi_master_2026_05_07.md`
    - `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` (CeFi extension). Est: 2 cal-AI-days.

20. **HUMAN-IKENNA-TRADFI-ARCHETYPE-DESIGN** — archetype mechanics for TradFi: ETF/futures basis, cash-and-carry on
    treasuries, calendar spreads on commodity futures. Custody implications (TradFi prime broker), settlement
    asymmetries (T+2 equities vs T+1 futures), Cayman vs UK regulatory split. Composes with:
    `epics/tradfi_master_2026_05_07.md`. Est: 2 cal-AI-days.

21. **HUMAN-IKENNA-SPORTS-ARCHETYPE-DESIGN** — Sports edge model design: odds dispersion across books, in-game line
    movement signals, season-state gating (off-season → no edge, see `epics/sports_master_2026_05_07.md`). Capital
    allocation: typically smaller stake per bet, higher number of concurrent positions. Custody implications (sportsbook
    custody is intrinsic — funds sit at the book). Composes with: `epics/sports_master_2026_05_07.md` +
    `cme_polymarket_arb_2026_05_08.md` (Polymarket overlap). Est: 2 cal-AI-days.

22. **HUMAN-IKENNA-PREDICTION-ARCHETYPE-DESIGN** — Prediction archetype: Polymarket-vs-Kalshi spread design, contract
    expiry mechanics, settlement-source disagreements (which Oracle / when), liquidity-weighted edge thresholds.
    Composes with: `epics/predictions_master_2026_05_07.md`. Est: 2 cal-AI-days.

23. **HUMAN-IKENNA-PAPER-TRADE-AUDIT-CROSS-ASSETGROUP** — once batch backfill for CeFi/TradFi/Sports/Prediction lands +
    paper-trade harness runs (Harsh items 27-30 below), audit each archetype's paper-trade output. Same shape as item 18
    but per asset_group. 1 cal-AI-day per asset_group × 4 = 4 cal-AI-days.

### Harsh (slot 2) — batch ML / batch strategy / batch execution / paper-trade harness per asset_group

24. **HUMAN-HARSH-BATCH-ML-CEFI** — batch ML training runs for CeFi archetypes (perp funding predictor, basis signal
    model, cross-CEX arb stat-arb model). Run from spec once features are ready. Composes with:
    `epics/ml_and_features_master_2026_05_07.md` + `epics/cefi_master_2026_05_07.md`. Est: 3 cal-AI-days.

25. **HUMAN-HARSH-BATCH-ML-TRADFI** — batch ML for TradFi (basis predictor, calendar spread model). Composes with:
    `epics/ml_and_features_master_2026_05_07.md` + `epics/tradfi_master_2026_05_07.md`. Est: 3 cal-AI-days.

26. **HUMAN-HARSH-BATCH-ML-SPORTS** — batch ML for Sports (odds dispersion model, in-game movement model). Composes
    with: `epics/ml_and_features_master_2026_05_07.md` + `epics/sports_master_2026_05_07.md`. Est: 3 cal-AI-days.

27. **HUMAN-HARSH-BATCH-ML-PREDICTION** — batch ML for Prediction (Polymarket-Kalshi spread model, settlement-source
    discrepancy detector). Composes with: `epics/ml_and_features_master_2026_05_07.md` +
    `epics/predictions_master_2026_05_07.md`. Est: 3 cal-AI-days.

28. **HUMAN-HARSH-BATCH-STRATEGY-EXEC-CEFI** — wire batch strategy + execution for CeFi archetypes against features + ML
    outputs. Same shape as DeFi but on CeFi adapters. Composes with: `epics/strategy_and_dart_master_2026_05_07.md` +
    `epics/cefi_master_2026_05_07.md`. Est: 4 cal-AI-days.

29. **HUMAN-HARSH-BATCH-STRATEGY-EXEC-TRADFI** — wire batch strategy + execution for TradFi. Composes with:
    `epics/strategy_and_dart_master_2026_05_07.md` + `epics/tradfi_master_2026_05_07.md`. Est: 4 cal-AI-days.

30. **HUMAN-HARSH-BATCH-STRATEGY-EXEC-SPORTS-PREDICTION** — wire batch strategy + execution for Sports + Prediction
    (bundled — overlap on book selection + settlement handling). Composes with:
    `epics/strategy_and_dart_master_2026_05_07.md` + `epics/sports_master_2026_05_07.md` +
    `epics/predictions_master_2026_05_07.md`. Est: 4 cal-AI-days.

31. **HUMAN-HARSH-PAPER-TRADE-HARNESS-CROSS-ASSETGROUP** — paper-trade harness runs for CeFi/TradFi/Sports/Prediction
    archetypes (same shape as DeFi paper_1d → live_early flow). Run end-to-end on mocked + real data once Harsh's items
    28-30 land. Each archetype's harness output feeds Ikenna item 23 (paper-trade audit). Composes with:
    `live_pipeline_mtds_mdps_features_2026_05_08.md` + `batch_live_symmetry_2026_05_10.md` (extension per asset_group).
    Est: 2 cal-AI-days per asset_group × 4 = 8 cal-AI-days.

### Parallel-prep sequencing principle

These items DO NOT have a hard dependency on the data-pipeline coordinator finishing — they can run concurrently:

- Items 19-22 (Ikenna archetype design) need: archetype-audit dimensions D1-D14 from
  `strategy_archetype_logic_audit_2026_05_20.md` (running tonight). Soft dep — Ikenna can design CeFi/TradFi/Sports/
  Prediction archetypes once DeFi dimensions are validated as the template.
- Items 24-27 (Harsh batch ML) need: features ready per asset_group + ML training infra (mostly available, some
  asset_groups have `BLOCKED-CREDENTIALS` on data sources — see adapter scaffolding track).
- Items 28-30 (Harsh batch strategy+exec) need: items 19-22 design landed + items 24-27 ML outputs.
- Item 31 (paper-trade harness) needs: items 28-30 wired.
- Item 23 (Ikenna paper-trade audit) needs: item 31 output.

**Cycle ordering per asset_group** (parallel across asset_groups):

```
Ikenna design (2 days) → Harsh ML (3 days) → Harsh strategy+exec (4 days) → Harsh paper-trade (2 days) → Ikenna audit (1 day)
```

Total per asset_group: ~12 cal-AI-days. Across 4 non-DeFi asset_groups in parallel: ~12 cal-AI-days wall-clock if all
slots available, ~24 if serialised. Comfortably fits in the post-May-23 window (May-23 → June-1 Copper+CEFFU custody
onboarding gives ~9 days).

## How these flow through the dashboard

- Each item lands in `backlog.yaml` with `tier: human-task`, `target_slot: 1` or `2`, `affinity: high`
- Dispatcher does NOT auto-dispatch them (treats them as operator-claimed)
- Dashboard Fleet tab shows slot 1 with the queued list + slot 2 the same
- Operator/Harsh interactive session reads the slot's current_task on /boot OR queries the backlog manually
- /done flow same as agent workers: SHA + evidence

## Coordinator-phase ↔ owner cross-reference (operator-handoff index)

| Coordinator phase                             | Plan-of-record                                                       | Owner (this plan)                                                  | Composes-with item ID                                                                                       |
| --------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| -2 Bucket 4 (archetype audit)                 | `issues/strategy_archetype_logic_audit_2026_05_20.md`                | Ikenna                                                             | HUMAN-IKENNA-ARCHETYPE-AUDIT (1)                                                                            |
| -1 Workspace QG green                         | per-repo `quality-gates.sh`                                          | Harsh                                                              | HUMAN-HARSH-WORKSPACE-QG-GREEN-SWEEP (8)                                                                    |
| 5 AWS bucket migration                        | `aws_migration_defi_first_2026_05_07.md`                             | Harsh                                                              | HUMAN-HARSH-PHASE-5-AWS-BUCKET-MIGRATION (9)                                                                |
| 6 Docker rebuild + VM redeploy                | `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.A       | Harsh                                                              | HUMAN-HARSH-PHASE-6-DOCKER-VM-FLEET-REDEPLOY (10)                                                           |
| 7a Schema migration (v<8 → v8)                | `d3_manifest_v8_finish_2026_05_20.md`                                | Harsh                                                              | HUMAN-HARSH-PHASE-7A-SCHEMA-MIGRATION (11)                                                                  |
| 7b DIVERGENT_EMPTY triage (per-cell judgment) | `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.D       | **Ikenna**                                                         | HUMAN-IKENNA-DATA-PIPELINE-COORDINATION-SUPERVISION (3) — Phase 7b branch                                   |
| 9 Deployment-UI denominator/numerator         | `honest_coverage_formula_consolidation_2026_05_19.md`                | Harsh                                                              | HUMAN-HARSH-PHASE-9-DEPLOYMENT-UI-DENOMINATOR-FIX (12)                                                      |
| 11 Operational data backfill                  | mega-audit § 6 R1-R5 + DIVERGENT_EMPTY Phase-11 subset               | Harsh                                                              | HUMAN-HARSH-PHASE-11-BACKFILL-TO-100PCT (13)                                                                |
| 12 Live adapter completion                    | `live_pipeline_mtds_mdps_features_2026_05_08.md` + adapter scaffolds | Co-owned (creds=Ikenna, scaffolds=bandwidth-claimed, wiring=Harsh) | ADAPTER-\* track + HUMAN-IKENNA-CREDENTIALS-UNBLOCK-TRACK (6) + HUMAN-HARSH-LIVE-PIPELINE-VALIDATION (15)   |
| 13 Batch-live symmetry verification           | `batch_live_symmetry_2026_05_10.md`                                  | Harsh                                                              | HUMAN-HARSH-LIVE-PIPELINE-VALIDATION (15)                                                                   |
| 14 Strategy + execution topology cleanup      | `strategy_execution_contract_remediation_2026_05_20.md`              | **Ikenna design / Harsh execute**                                  | HUMAN-IKENNA-DATA-PIPELINE-COORDINATION-SUPERVISION (3) — Phase 14 design branch + Harsh validation harness |

**Phases not in the table** (0/1/2/3/4/8/10) — currently assigned to centralised VM slots 3-8 per the coordinator's
slot-dispatch table; this human-work plan does not duplicate those. Operator decides per-phase whether to elevate to
slot 1 or 2 supervision when each lands.

## When to add new human-work items

Any plan/issue that surfaces with one of these signals:

- Frontmatter `locked_by` + decision needed
- `BLOCKED-OPERATOR-DECISION` in body
- Master coordinator phase that says `operator-acked` or `human-only`
- Architectural call (cross-repo design, new module, breaking interface)
- Audit work requiring full-context Opus reasoning (Mega Audit, archetype audit, etc.)
- New `BLOCKED-CREDENTIALS` adapter that needs a vendor signup

Filing recipe: edit `unified-trading-pm/harsh_orchestrator/backlog.yaml` with a new entry; POST `/api/backlog/reload`;
the new task appears in slot 1 or 2's queue on next dashboard refresh.

## Slot 2 takeover plan (next session)

Slot 2 currently has a worker doing Phase 1 bucket symmetry (already GREEN — operator confirmed 2026-05-20). Migration
to Harsh interactive:

1. Wait for worker to /done current commit (or operator-graceful /reassign-park)
2. POST `/api/slots/2/pause` — orchestrator stops dispatching
3. Worker tmux session stays alive — operator/Harsh can attach + claim human tasks from backlog
4. New centralised workers spawn into slots 12-20 to replace the slot-2 worker's capacity

Slot 1 already paused (2026-05-20 evening).

## Composes with (HARD-RULE chain)

- `External Data Is Always Available — Never Silently Defer Adapters` — adapter-scaffolding track is the per-data-source
  operationalisation; credentials = Ikenna unblock channel.
- `Data Pipeline Correctness Is The Heartbeat` — the coordinator plan IS the heartbeat; this human-work plan is the
  Ikenna/Harsh supervision layer over it.
- `Quality Gates Are A Merge Prerequisite` — HUMAN-HARSH-WORKSPACE-QG-GREEN-SWEEP (8) is the explicit
  operationalisation.
- `Plans Run To Actual Completion, Not Smoke-Test Green` — HUMAN-HARSH-PHASE-11-BACKFILL-TO-100PCT (13) runs to 100% per
  asset_group, not "most cells".
- `Commit + Push + Flip Plan Checkboxes As You Ship Each Item` — both sides flip checkboxes in this plan + the
  coordinator plan as items close (Half-2 in the same agent turn).
- `Every Active Ping Must Reference A Plan Item` — every `_agent_pings.md` entry from either side cites either an item
  from this plan (HUMAN-IKENNA-_ / HUMAN-HARSH-_ / ADAPTER-\*) OR the coordinator plan's phase number.
