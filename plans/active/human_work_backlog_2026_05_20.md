---
title:
  Human-work backlog 2026-05-20 — Ikenna + Harsh interactive task split with data_pipeline_master_coordination
  supervision
type: organizing-plan
status: active
created: 2026-05-20
updated: 2026-05-20 # split principles + Phase 7/14 sub-splits + supervision-checkpoint wiring
operator: ikenna
co-operators: [harsh]
related:
  - cursor-configs/CLAUDE.md § "Human-vs-Agent work split"
  - plans/active/data_pipeline_master_coordination_2026_05_20.md # phase-of-record for the heartbeat work
  - plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md
  - plans/active/issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md
  - codex/08-workflows/deployment-flow.md # CI/CD + main-via-staging-and-sit path Harsh owns
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

2. **HUMAN-IKENNA-MEGA-AUDIT-PROGRESSION** — `issues/mega_audit_and_plan_beefup_progression_2026_05_20.md`. Master audit
   tracker; needs ongoing curation as items close. Est: 1 cal-AI-day rolling.

3. **HUMAN-IKENNA-DATA-PIPELINE-COORDINATION-SUPERVISION** — `data_pipeline_master_coordination_2026_05_20.md`. Phase
   sequencing decisions when blockers surface + Phase 7b DIVERGENT_EMPTY triage (per-cell label-flip-vs-rebackfill calls
   on the 765 cells from A3) + Phase 14 topology design. Est: 0.5 cal-AI-day rolling + 2 cal-AI-days for Phase 7b once
   reached + 2 cal-AI-days for Phase 14 design once Phase 13 lands.

4. **HUMAN-IKENNA-CROSS-CLIENT-ISOLATION-AUDIT** —
   `issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md`. HARD RULE codified 2026-05-20; needs
   validation pass across existing code. Est: 1 cal-AI-day.

5. **HUMAN-IKENNA-PROMOTE-WORKFLOW-REVIEW** — review the promote workflow architecture before May-23 cutover.
   Critical-path call: paper_1d → live_early tonight, live_full post-cutover. Est: 0.5 cal-AI-day.

6. **HUMAN-IKENNA-CREDENTIALS-UNBLOCK-TRACK** — operator-facing credential asks: Helius (paid Solana RPC), Glassnode /
   Kaiko / IntoTheBlock (on-chain analytics), Polygon.io / Databento (tradfi ticks), Sportradar / Footystats /
   The-Odds-API (sports odds), Polymarket / Kalshi (prediction spreads). Per `External Data Is Always Available` rule:
   each adapter scaffold ships pre-credential (co-owned per-adapter); credential ask is filed via `pings/slot_1.md` with
   the CREDENTIAL APPROVAL REQUEST format. Status taxonomy: `BLOCKED-CREDENTIALS` until acked. Est: 0.2 cal-AI-day per
   credential × ~10 = 2 cal-AI-days rolling.

7. **HUMAN-IKENNA-CUSTODY-PROVIDER-DECISIONS** — Copper + CEFFU June-1 onboarding decisions (May-23 ships on
   `CLOUD_KMS_ENCRYPTED`). Cayman vs UK jurisdiction calls per `project_trading_entities` memory + venue-bans-UK gating.
   Est: 1 cal-AI-day rolling.

### Harsh (slot 2) — backfills / deployment-UI / GCP VMs / AWS copies / CI/CD / Phase 7a+14-exec

8. **HUMAN-HARSH-WORKSPACE-QG-GREEN-SWEEP** — Phase -1 of coordinator: per-repo `bash scripts/quality-gates.sh` exit 0
   workspace-wide. Composes with: `Quality Gates Are A Merge Prerequisite` HARD RULE. Cluster split (per
   `work_split_2026_05_20_ikenna.md` Slots 9-11): A=UAC+UTL+IS / B=MTDS+features+MDPS / C=strategy+execution+ml. Est: 3
   cal-AI-days (1 per cluster).

9. **HUMAN-HARSH-PHASE-5-AWS-BUCKET-MIGRATION** — Phase 5 of coordinator: `aws s3 sync` from current bucket names →
   target symmetric names per Phase 1 inventory CSV. Per-asset-group, single-walk discipline. Composes with:
   `aws_migration_defi_first_2026_05_07.md` + Phase 1 cloud-providers.yaml AWS-side templates (already shipped
   2026-05-20 per coordinator Phase 1 GREEN). Est: 5 cal-AI-days.

10. **HUMAN-HARSH-PHASE-6-DOCKER-VM-FLEET-REDEPLOY** — Phase 6 of coordinator: Docker image build + writer fleet VM
    restart so steady-state writers produce v8 rows. Composes with: `writegate_honest_coverage_endtoend_2026_05_06.md` §
    Phase 7.A. Verification: 100 newest manifest rows per bucket sampled, ALL at `schema_version=8`. Est: 2 cal-AI-days.

11. **HUMAN-HARSH-PHASE-7A-SCHEMA-MIGRATION** — Phase 7 SCHEMA half of coordinator (Phase 7b triage is Ikenna's).
    Migrate every v<8 row → v8 schema mechanically. Composes with: `d3_manifest_v8_finish_2026_05_20.md` +
    `hard_schema_phase1_field_flip_migration_2026_05_19.md`. Verification: A4 v1 re-run shows 100% v8 + 0 NULL across
    all 10 buckets BEFORE 7b triage begins. Est: 4 cal-AI-days.

12. **HUMAN-HARSH-PHASE-9-DEPLOYMENT-UI-DENOMINATOR-FIX** — Phase 9 of coordinator: deployment-UI numerator/denominator
    formula consolidation. Composes with: `honest_coverage_formula_consolidation_2026_05_19.md` +
    `data_status_drilldown_shard_atom_alignment_2026_05_07.md` + `deployment_ui_lifecycle_tabs_2026_05_08.md`.
    Verification: spot-check known bucket, math matches; UI shows the 4-state breakdown panel. Est: 4 cal-AI-days.

13. **HUMAN-HARSH-PHASE-11-BACKFILL-TO-100PCT** — Phase 11 of coordinator: operational data backfill against the
    now-clean v8 + correctly-labelled manifest. DeFi 184k + Sports 25k + CeFi 16k + TradFi 7k + Prediction 3k
    MISSING_EXPECTED cells + the Phase-11-rebackfill subset from Ikenna's Phase 7b triage CSV. Single-walk discipline
    (HARD RULE) + every new write at v8 + typed reason. Composes with: mega-audit § 6 R1-R5 +
    `defi_upstream_46day_full_backfill_2026_05_16.md`. Est: 6 cal-AI-days fan-out across asset_groups.

14. **HUMAN-HARSH-CI-CD-PROMOTION-PIPELINE** — quickmerge + main-via-staging-and-SIT promotion path per
    `codex/08-workflows/deployment-flow.md`. Drive a full LDR → staging → SIT → main promotion cycle on a non-critical
    service to validate the flow before May-23 cutover. Composes with: `codex/08-workflows/deployment-flow.md` + the
    PM/Codex fast-path rule (docs/plans → main directly). Est: 1 cal-AI-day.

15. **HUMAN-HARSH-LIVE-PIPELINE-VALIDATION** — Phase 12-13 of coordinator: live-mode adapter behavior matches batch-mode
    (per the live=batch HARD RULE) + batch-live symmetry verification. Composes with:
    `live_pipeline_mtds_mdps_features_2026_05_08.md` + `batch_live_symmetry_2026_05_10.md`. Est: 2 cal-AI-days.

16. **HUMAN-HARSH-AWS-MANIFEST-CONSOLIDATOR-COPY** — AWS-side copy of the GCP Cloud Run manifest consolidator stack (10
    jobs / `*/1 * * * *` schedule per `codex/05-infrastructure/manifest-consolidator-ssot.md`). Currently AWS-side
    consolidation is NOT in scope (per the codex SSOT); this task is to scope + estimate the AWS port. Outcome: either a
    new sub-plan filed + estimated, OR a `BLOCKED-OPERATOR-DECISION` ping with the explicit "leave AWS without
    consolidator" articulation. Est: 0.5 cal-AI-day for scoping.

17. **HUMAN-HARSH-LAPTOP-MIGRATION-COMPLETE** — `codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md` Steps
    1-8. Self-onboarding to the shared agent-orchestrator from `orch.epiphanytechnologies.com`. Est: 0.5 cal-AI-day.

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

Items (initial): each = ~0.3-0.5 cal-AI-day.

- `ADAPTER-HELIUS-SOLANA-PAID` (DeFi RPC scale)
- `ADAPTER-GLASSNODE-ONCHAIN` (DeFi analytics)
- `ADAPTER-KAIKO-CEX-HISTORICAL` (CeFi historical depth)
- `ADAPTER-POLYGON-IO-TRADFI-TICKS` (TradFi)
- `ADAPTER-DATABENTO-TRADFI` (TradFi alt)
- `ADAPTER-SPORTRADAR-FEED` (Sports)
- `ADAPTER-FOOTYSTATS-FEED` (Sports alt)
- `ADAPTER-THE-ODDS-API` (Sports/Prediction)
- `ADAPTER-POLYMARKET-FEED` (Prediction)
- `ADAPTER-KALSHI-FEED` (Prediction)

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
