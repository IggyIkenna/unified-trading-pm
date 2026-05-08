---
name: codex-refactor-2026-05-08
plan_type: meta
asset_group: cross-cutting
type: doc-only
status: active
created: 2026-05-08
last_updated: 2026-05-08
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-08
owner: ikenna

overview: >-
  Comprehensive codex SSOT refactor consolidating findings from 7 directory audits (Wave 1 + Wave 2 cross-directory
  synthesis, 2026-05-08 session). The audits confirmed that ALL drift between codex docs and the active workspace plans
  resolves in favour of the plans (per CLAUDE.md "If this doc disagrees with active plans, the plans win" + "doc → plan
  → code"). This plan enumerates every codex file requiring changes, every cross-doc reference update needed when
  consolidations happen, and structures phases for parallel-agent execution. P0 phases are silent-correctness drift
  (must ship before May-23 cutover); P1 phases are consolidation that reduce drift surface; P2 phases are cosmetic /
  structural moves that can ship after cutover.

depends_on:
  - writegate-honest-coverage-endtoend-2026-05-06
  - manifest-v7-schema-migration-design-2026-05-08
  - live-pipeline-mtds-mdps-features-2026-05-08
  - features-repo-consolidation-2026-05-08
  - alerting-service-live-rules-2026-05-07
  - master-to-live-defi-2026-05-23

repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

completion_gates:
  code: C0
  deployment: none
  business: none
---

# Codex SSOT Refactor — comprehensive worklist (2026-05-08)

## Why

The 2026-05-08 codex audit (7 sub-agents, one per directory + cross-directory synthesis) identified:

- **17 cross-directory drifts**, of which 7 are P0 silent-correctness (manifest schema version drift, 4-state taxonomy
  collision, CIRCUIT_BREAKER naming triple-drift, 9/53 archetype count, 3 live-transport models, execution-service mode
  contradiction, features-\* deployment count drift).
- **12 high-value consolidation clusters** (e.g. data-status-drilldown duplicate, 4-doc path-layout overlap, 5-doc
  sports overlap, 7-doc topology cluster, custody triplet, validation/error chapter, batch-live principle merge).
- **3 structural moves** (14-playbooks split into customer-journeys / runbooks / strategy-playbooks; rename
  `09-strategy/cross-cutting/` to disambiguate from `architecture-v2/cross-cutting/`; rename
  `02-data/per-category-bucket-layouts.md` to use the `asset_group` vocabulary).
- **~200 files** carrying the stale `POST_PLAN_BANNER_2026_05_06_FINAL` (workspace-wide sweep candidate; 2 of the 3
  banner-named active plans no longer exist).
- **~12 stub docs** under 500 bytes in `06-coding-standards/` that fail the workspace S5.4 stub gate.
- **~10 stale repo references** (UMI archived, unified-internal-contracts renamed, Pyth unbanned for Solana, UTS alias
  retired, etc.).

The operator approved all "refactors that neaten and make docs easier to track" in advance (2026-05-08 chat), and
explicitly requested this plan list **every single file and point so parallel agents can fix it all without forgetting
anything**.

## Plan principles

1. **Every phase is a shippable unit** — each phase QGs cleanly on its own and is committed + pushed in one logical unit
   per the workspace Commit + Push + Flip rule.
2. **Phases marked PARALLEL run concurrently within their layer** — the parent agent fans out one sub-agent per phase.
   Phases marked SEQUENTIAL must wait for predecessors.
3. **Reference updates are listed inline** — when a doc gets consolidated, the "References to update in OTHER docs"
   sub-table is part of the phase deliverable.
4. **No ad-hoc consolidations** — only the 12 clusters audited in Wave 2. New consolidation candidates discovered
   mid-execution get logged as plan todos per the workspace "Capture discoveries as plan todos immediately" HARD RULE,
   not silently shipped.
5. **Filename casing** — when a phase ships, it commits via `docs(codex):` prefix per CLAUDE.md "Half 2 — Flip plan
   checkboxes" rule (PM@e3457a08 precedent).

## Phase priority labels

| Label          | Meaning                                                       |
| -------------- | ------------------------------------------------------------- |
| **P0**         | Silent-correctness drift; ship before May-23 live cutover     |
| **P1**         | High-value consolidation reducing future drift surface        |
| **P2**         | Cosmetic / structural; can defer past May-23                  |
| **PARALLEL**   | Can run concurrently with other PARALLEL phases in same layer |
| **SEQUENTIAL** | Must wait for predecessor (declared in `after:`)              |

---

## LAYER A — P0 silent-correctness fixes (parallel; ship first)

All Layer A phases are **PARALLEL** and shippable independently. They do NOT consolidate docs; they only fix factual
drift.

### Phase A.1 — Manifest schema version unification — PARALLEL — P0

- [ ] [SCRIPT] P0. Single-pass sweep: every codex doc claiming a manifest schema version must cite the canonical version
      per `manifest_v7_schema_migration_design_2026_05_08.md` (current = v7; target = v8). UTL `manifest_writer.py`
      `MANIFEST_SCHEMA_VERSION` is the runtime SSOT.

  **Files to update** (verified in audit):
  - [ ] `02-data/availability-manifest-and-data-status.md:228` — replace `MANIFEST_SCHEMA_VERSION = 6` with the actual
        UTL constant; reconcile the "v7 job_id" + "v8 pipeline_mode" body sections (ll.31, 293-300) with the version
        constant.
  - [ ] `02-data/per-category-bucket-layouts.md:27` — drop the v7 job_id banner, point at availability-manifest doc.
  - [ ] `02-data/partitioning.md:27` — same.
  - [ ] `02-data/prediction-schema-paths.md:27` — same.
  - [ ] `02-data/shard-granularity-cefi.md:27` — same.
  - [ ] `02-data/sports-scheduling-and-sharding.md:27` — same.
  - [ ] `02-data/pipeline-coverage-matrix.md:80` — replace `v6 — current` with current.
  - [ ] `02-data/data-lineage-MTDS-features-ml.md:34` — replace `v4` reference with current.
  - [ ] `02-data/data-status-drilldown.md:65,131-148` — verify schema reference points at correct version.
  - [ ] `04-architecture/shard-level-failure-isolation.md` — verify any version cites match.

  **Acceptance**: every doc citing a manifest schema version cites the same number (the UTL constant); no doc carries
  inline "v7 job_id" or "v8 pipeline_mode" banners that contradict its own version line.

### Phase A.2 — Capture taxonomy 4-state alignment — PARALLEL — P0

- [ ] [SCRIPT] P0. Sweep: every codex doc enumerating the `capture_status` closed set MUST list 4 states:
      `captured / empty_confirmed / attempted_failed / expected_unattempted` (per writegate Phase 3.D.5 + CLAUDE.md
      "Availability manifest v5 (honest-coverage)").

  **Files to update**:
  - [ ] `02-data/availability-manifest-and-data-status.md:278` — dataclass docstring says 3-state ("captured /
        empty_confirmed / attempted_failed"); add `expected_unattempted`.
  - [ ] `02-data/data-status-drilldown.md:76` — list says
        `"captured" | "empty_confirmed" | "attempted_failed" | "missing"`; replace `"missing"` with
        `"expected_unattempted"`.
  - [ ] `04-architecture/shard-level-failure-isolation.md` — verify any taxonomy reference includes 4 states.
  - [ ] `06-coding-standards/error-handling.md` — verify any taxonomy reference includes 4 states.
  - [ ] `06-coding-standards/validation-patterns.md` — verify any taxonomy reference includes 4 states.

  **Acceptance**: no doc lists a 3-state taxonomy; no doc lists `"missing"` as a closed-set value.

### Phase A.3 — CIRCUIT_BREAKER naming alignment to UAC — PARALLEL — P0

- [ ] [SCRIPT] P0. Three-way naming drift: UAC `events.py:94-96` defines
      `CIRCUIT_OPEN / CIRCUIT_HALF_OPEN / CIRCUIT_CLOSED` (no `_BREAKER_` prefix). All codex docs must align to the UAC
      names.

  **Files to update**:
  - [ ] `03-observability/lifecycle-events.md:328-329` — replace `CIRCUIT_BREAKER_OPENED / CIRCUIT_BREAKER_CLOSED` with
        `CIRCUIT_OPEN / CIRCUIT_CLOSED` + add `CIRCUIT_HALF_OPEN`.
  - [ ] `03-observability/alerting.md:128,138,141,142` — replace `CIRCUIT_BREAKER_OPEN`, `CIRCUIT_BREAKER_BACKOFF_*`,
        `CIRCUIT_BREAKER_DEGRADED`, `CIRCUIT_BREAKER_CLOSED`. The `BACKOFF_ESCALATED` and `DEGRADED` codes don't exist
        in UAC — either add to UAC or rewrite the alert routing rule to use `CIRCUIT_OPEN` only.
  - [ ] `04-architecture/alerting-batch-live.md` — verify CIRCUIT\_\* references match UAC.
  - [ ] `04-architecture/autonomous-recovery-matrix.md` — verify CIRCUIT\_\* references match UAC.
  - [ ] `04-architecture/kill-switch-circuit-breaker.md` — verify all CIRCUIT\_\* names match UAC.
  - [ ] `14-playbooks/alerting/alert-code-taxonomy.md` — verify CIRCUIT\_\* taxonomy matches UAC.
  - [ ] `14-playbooks/alerting/threshold-tuning.md` — verify any code references match.

  **Acceptance**: workspace-wide grep for `CIRCUIT_BREAKER_` returns zero hits in codex/. UAC enum members are the only
  canonical names.

### Phase A.4 — Family/archetype count refresh to 9/53 — PARALLEL — P0

- [ ] [SCRIPT] P0. UAC `StrategyArchetype` enum is the SSOT. All codex docs must cite 9 families × 53 archetypes
      (verified PM@d6d0cd57 refreshed strategy-summary.md but residuals remain).

  **Files to update**:
  - [ ] `09-strategy/README.md:19` — `8 families × 18 archetypes × 7 axes × 10 cross-cutting` →
        `9 families × 53 archetypes × ... axes × ... cross-cutting concerns`. Verify axis + cross-cutting counts against
        UAC enums.
  - [ ] `09-strategy/architecture-v2/README.md:28-29` — `1 of 8 families` / `1 of 18 archetypes` → `1 of 9 / 1 of 53`.
  - [ ] `09-strategy/architecture-v2/README.md:61` — section heading `## 8 Families` → `## 9 Families`; expand the 8-row
        table to include `PORTFOLIO`.
  - [ ] `09-strategy/architecture-v2/README.md:97,113` — `## 18 Archetypes` / `Total: 18 archetypes` →
        `## 53 Archetypes` (or "53 archetypes spanning 9 families"); expand the table to include the Phase 9 additions:
        4 ARBITRAGE*MEV*_, 1 ARBITRAGE*CROSS_DOMAIN_EVENT, 5 MARKET_MAKING*_ new, 3 DEFI*LP*\_, 17 expanded VOL\_\_, 4
        PORTFOLIO\_\*.
  - [ ] `09-strategy/architecture-v2/category-instrument-coverage.md:17,1422` —
        `every one of the 18 v2 strategy archetypes` / `All 18 archetypes` →
        `every one of the 53 v2 strategy archetypes` / `All 53 archetypes`. Expand the matrix to cover post-Phase-9
        archetypes (or explicitly bound the doc to "May-23 live + immediate-backtest subset" with a successor-plan
        reference).
  - [ ] `09-strategy/cross-cutting/dart-manual-trade-spec.md:67-69, 72-75` — drop the explicit count or pin to "the full
        UAC archetype set" instead of "18 ... at 46". The 11 vs 13 InstructionActionV2 count at lines 42-44 also needs
        fixing per audit (13 per `strategy-summary.md:30-31`).

  **Acceptance**: workspace-wide grep for `8 families` / `18 archetypes` / `46 archetypes` returns zero hits in codex/.
  UAC enum member counts are SSOT.

### Phase A.5 — Live transport SSOT alignment to Redis Stream — PARALLEL — P0

- [ ] [SCRIPT] P0. `live_pipeline_mtds_mdps_features_2026_05_08.md` confirms Redis Stream cascade
      (CANDLE_BOUNDARY_CROSSED + CANDLE_COMPUTED) is the post-2026-05-08 SSOT for the inner-loop live cascade. Older
      codex docs claiming PubSub-only or embedded-only need banners pointing at the new SSOT.

  **Files to update**:
  - [ ] `04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md:99-117` — the "If producer is live AND consumer is live → PubSub"
        rule applies to CROSS-SERVICE signalling, not the inner-loop cascade. Add a banner pointing to
        `05-infrastructure/live-pipeline-architecture.md` + the Redis Stream section in
        `03-observability/coordination-events.md`.
  - [ ] `04-architecture/batch-live-symmetry.md:21-29` — TL;DR table says `live mode Data transport = PubSub`. Replace
        with "Redis Stream (inner-loop) + PubSub (cross-service)" + cross-link.
  - [ ] `04-architecture/deployment-topology-diagrams.md:96-193` — "GCS for persistence only, not for inter-service" +
        "embedded package" framing predates Redis Stream cascade. Update diagrams to show Redis Stream cascade between
        MTDS → MDPS → features-service.
  - [ ] `04-architecture/README.md:21-23` — verify "two distinct concerns" framing matches the post-2026-05-08 model.
  - [ ] `03-observability/coordination-events.md` — already updated 2026-05-08 to mention Redis Stream cascade
        (PM@d212f4e6); verify no further drift.

  **Acceptance**: every doc that names the live transport mechanism agrees with
  `05-infrastructure/live-pipeline-architecture.md` as the SSOT.

### Phase A.6 — execution-service batch+live mode contradiction — PARALLEL — P0

- [ ] [SCRIPT] P0. CLAUDE.md "Batch = Live: Unified Pipeline Architecture" + the
      `04-architecture/batch-live-pipeline.md` matching engine + UAC `BatchExecutionMode` enum confirm execution-service
      runs in BOTH batch (matching engine fills) and live (real venue). The contrary claim must be removed.

  **Files to update**:
  - [ ] `04-architecture/batch-live-symmetry.md:185` — row says
        `execution-service: live only, Batch Handler n/a, "Execution is always live; no batch mode"`. Replace with
        `MatchingEngineHandler / ExecutionLiveHandler` pair (batch matches engine, live = real venue).
  - [ ] `06-coding-standards/integration-testing-layers.md` — verify execution-service test layer references include
        batch mode (matching engine).
  - [ ] `09-strategy/architecture-v2/archetypes/*.md` — verify any archetype that says "execution is live-only" gets
        corrected.

  **Acceptance**: no codex doc claims execution-service is live-only.

### Phase A.7 — features-service consolidation alignment — PARALLEL — P0

- [ ] [SCRIPT] P0. `features_repo_consolidation_2026_05_08.md` is the SSOT — single `features-service` repo with
      sub-packages (per asset_group + cross-cutting), single CLI surface, single launcher per cluster shape,
      `feature_family` UAC axis as primary shard key. Older codex docs claiming N separate features-\* repos are stale.

  **Files to update**:
  - [ ] `04-architecture/README.md:24-27` — "Live deployments: 7-8 standalone processes" enumeration includes
        `features-onchain-service` standalone. Replace with "1 consolidated `features-service` repo deployed per
        asset_group cluster + 1 cross-cutting cluster".
  - [ ] `04-architecture/deployment-topology-diagrams.md:114-138` — Deploy 4 (Delta-One), Deploy 5 (Volatility), Deploy
        6 (Onchain) shown as separate. Replace with single features-service deployment topology.
  - [ ] `05-infrastructure/launcher-script-ssot.md` — verify launcher list reflects per-cluster
        `launch-features-{asset_group}-vm.sh` not 5-6 per-repo launchers.
  - [ ] `05-infrastructure/deployment-clusters-live-vs-batch.md` — verify cluster topology matches.

  **Acceptance**: no codex doc enumerates 5+ separate `features-*-service` repos as the live deployment shape.

---

## LAYER B — Workspace-wide mechanical sweeps (parallel; ship after Layer A or in parallel with it)

### Phase B.1 — POST_PLAN_BANNER_2026_05_06 sweep (workspace-wide) — PARALLEL — P0

- [ ] [SCRIPT] P0. Banner cites 3 plans: writegate-honest-coverage (still active), predictions-canonical_question_group
      (archived per MEMORY, folded into predictions_master), data-status-multi-axis-shard (no longer findable). 2 of 3
      banner-named plans no longer exist; banner is workspace-wide stale.

  **Scope**: ~200 files across all codex sub-trees carry the banner.

  **Implementation**:
  - [ ] Find every codex/\*.md containing `POST_PLAN_BANNER_2026_05_06_FINAL`.
  - [ ] Per directory (one sub-agent per dir for safety): bulk-remove the banner from every file in that directory.
        Single commit per directory (`docs(codex): sweep POST_PLAN_BANNER_2026_05_06 from <dir>/`).
  - [ ] Operator approves the sweep before execution (large blast radius).

  **Files affected** (counts from audit):
  - `02-data/`: ~20 files
  - `04-architecture/`: ~30 files (estimated)
  - `05-infrastructure/`: ~10 files
  - `06-coding-standards/`: most non-NEW docs (~20)
  - `09-strategy/`: ~40 files (every archetype + family + architecture-v2/cross-cutting)
  - `14-playbooks/`: 129 files (the largest cluster)
  - Other small dirs: estimated ~10

  Total: **~250 files**.

  **Acceptance**: workspace-wide grep `POST_PLAN_BANNER_2026_05_06_FINAL` returns zero hits in codex/.

### Phase B.2 — Plan filename convention sweep (.plan.md → .md in active/) — PARALLEL — P1

- [ ] [SCRIPT] P1. CLAUDE.md "Plan Filename Convention" says `plans/active/` uses `.md`, `plans/archive/` uses
      `.plan.md`. Many codex docs reference `plans/active/<x>.plan.md` (legacy convention).

  **Files to update** (sample from audit; full sweep):
  - [ ] `09-strategy/architecture-v2/archetypes/carry-staked-basis.md:302` —
        `plans/active/carry_staked_basis_structure_axis_2026_05_04.plan.md` → file is at `plans/archive/...plan.md`.
        Update path.
  - [ ] `09-strategy/architecture-v2/archetypes/carry-staked-basis.md:102` —
        `plans/ai/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.plan.md` → file is at
        `plans/active/...md`. Update both path and extension.
  - [ ] `06-coding-standards/validation-patterns.md:229-232` — multiple `plans/active/<x>.plan.md` references.
  - [ ] `06-coding-standards/service-hardening-checklist.md:14,222-223,225-227` —
        `phase3_service_hardening_integration.plan.md`, `phase2_library_tier_hardening.plan.md`.
  - [ ] `06-coding-standards/pre-sprint-baseline.md:16` — `phase0_standards_enforcement.plan.md`.
  - [ ] `06-coding-standards/orphan-audit.md:17` — `orphan_audit_policy_2026_04_21.plan.md`.
  - [ ] `06-coding-standards/error-handling.md:181` — `writegate_honest_coverage_endtoend_2026_05_06.plan.md`.
  - [ ] `06-coding-standards/terminology-ssot.md:85-86` —
        `dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`.

  **Implementation**:
  - [ ] Workspace-wide grep `plans/active/.*\.plan\.md` → flag every hit.
  - [ ] For each: verify the file is in `plans/active/` (rewrite to `.md`) or `plans/archive/` (keep `.plan.md`, rewrite
        path prefix).
  - [ ] Single commit per directory.

  **Acceptance**: workspace-wide grep `plans/active/.*\.plan\.md` in codex/ returns zero hits.

### Phase B.3 — Stale repo / provider reference sweep — PARALLEL — P1

- [ ] [SCRIPT] P1. Multiple stale references identified across audits.

  **Renames to apply (workspace-wide)**:
  - [ ] `unified-market-interface` → `market-tick-data-service/market_tick_data_service/market_interface` (UMI archived;
        CLAUDE.md confirms). Affected files include `09-strategy/cross-cutting/prediction-markets.md:25-36`,
        `06-coding-standards/service-orchestration-patterns.md:29,41,364-372,401,415,494,497,574,586`,
        `06-coding-standards/integration-testing-layers.md:71,83,164,233`,
        `06-coding-standards/vcr-cassette-pattern.md:41,57`, `06-coding-standards/dockerfile-standards.md:78`,
        `06-coding-standards/README.md:548,725`.
  - [ ] `unified-internal-contracts/` → `unified_api_contracts.internal` (per UAC Citadel Architecture rule). Affected:
        `04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md:441-454`.
  - [ ] `(UTS)` alias → `(UTL)` (unified-trading-services rename completed). Affected:
        `06-coding-standards/service-hardening-checklist.md:213`. Strike `unified-trading-services` from any
        service-list (it's a library not a service): `06-coding-standards/cod-deadlock-verification-report.md:39`.
  - [ ] `unified-feature-calculator-library` references — verify against `features_repo_consolidation_2026_05_08.md`
        whether the library survives as inner-package or consolidated. Affected:
        `06-coding-standards/feature-service-pattern.md:24,173,194`,
        `06-coding-standards/service-hardening-checklist.md:214`, `06-coding-standards/pre-sprint-baseline.md:73`.
  - [ ] `unified-trading-codex/` path prefix → `unified-trading-pm/codex/`. Affected:
        `06-coding-standards/feature-service-pattern.md:196,197`,
        `06-coding-standards/service-hardening-checklist.md:225-227`,
        `06-coding-standards/pre-sprint-baseline.md:17-19`.

  **Removed-providers list correction**:
  - [ ] `02-data/venue-availability.md:99-103` — Pyth listed as removed; per CLAUDE.md "Pyth UNBANNED 2026-05-06" for
        Solana. Move from removed list to a "Pyth (Solana-only)" entry.
  - [ ] `02-data/availability-manifest-and-data-status.md:953-955` — verify "Removed bookmakers: Smarkets / Betdaq /
        OddsJam" against current UAC. Update if any are still active.

  **Project ID placeholder leakage**:
  - [ ] `05-infrastructure/README.md:73,77,148` — `test-project` placeholder rotted into prod-looking docs. Replace with
        `central-element-323112` (verified canonical via vm-tarball-deployment, runtime-tiers, firebase-split-topology)
        OR explicit `{project_id}` placeholder syntax.
  - [ ] `05-infrastructure/auth-setup.md` — same.
  - [ ] `05-infrastructure/library-setup-checklist.md` — same.
  - [ ] `05-infrastructure/ucs-docker-image-issues.md` — same.

  **MTDS phantom-audit script naming**:
  - [ ] `02-data/sports-schema-paths.md:186` — references older `reconcile_phantom_manifest_rows.py`; update to
        `reconcile_phantom_manifest_rows_all.py` (multi-asset_group, per CLAUDE.md "Manifest phantom audit").

  **Acceptance**: zero hits for the renamed paths in codex/; no removed-providers list contains Pyth.

### Phase B.4 — Stub-doc cleanup (06-coding-standards) — PARALLEL — P2

- [ ] [SCRIPT] P2. 12 stub docs in `06-coding-standards/` under 500 bytes — per S5.4 these would block their own QG
      gate. Each: delete OR expand to meaningful SSOT.

  **Operator decision required per file** — list:
  - [ ] `06-coding-standards/accurate-codebase-analysis.md` (482 bytes) — delete or expand.
  - [ ] `06-coding-standards/audit-remediation-guide.md` (528 bytes) — delete or expand.
  - [ ] `06-coding-standards/code-cleanup-deslop.md` (477 bytes) — delete or expand.
  - [ ] `06-coding-standards/config-types.md` (468 bytes) — delete or expand.
  - [ ] `06-coding-standards/contribution-guide.md` (474 bytes) — delete or expand.
  - [ ] `06-coding-standards/cursor-rules-system.md` (475 bytes) — delete or expand.
  - [ ] `06-coding-standards/file-splitting-guide.md` (476 bytes) — delete or expand.
  - [ ] `06-coding-standards/sub-agent-workflow.md` (506 bytes) — delete or expand.
  - [ ] `06-coding-standards/testing.md` (527 bytes) — delete or expand.
  - [ ] `06-coding-standards/thin-adapters-pattern.md` (507 bytes) — delete or expand.
  - [ ] `06-coding-standards/token-optimization.md` (474 bytes) — delete or expand.
  - [ ] `06-coding-standards/service-structure-standards.md` (13 lines after revert) — already a stub; either delete
        (content was meant to live in README per audit C7 below) or expand.

  **Acceptance**: no codex doc under 500 bytes (excluding intentional README stubs documented as such in
  `_ssot-rules/`).

### Phase B.5 — SOURCE_COVERAGE_START dedup — PARALLEL — P2

- [ ] [SCRIPT] P2. UAC `unified_api_contracts.sports.SOURCE_COVERAGE_START` is the canonical SSOT. Codex docs duplicate
      the values in 4 places.

  **Files to update**:
  - [ ] `02-data/availability-manifest-and-data-status.md` — keep ONE table here as canonical reference (already
        comprehensive).
  - [ ] `02-data/sports-data-source-coverage-matrix.md:43-50` — replace explicit dates with cross-link to
        availability-manifest doc.
  - [ ] `02-data/sports-schema-paths.md:163-172` — same.
  - [ ] `02-data/mtds-data-source-coverage-matrix.md` — add cross-link if not present.
  - [ ] All consumer docs: cite via cross-link, never redeclare values.

  **Acceptance**: only ONE codex doc enumerates the literal `SOURCE_COVERAGE_START` values; all others link to it. UAC
  code remains the runtime SSOT.

---

## LAYER C — Easy consolidations (parallel; just-shipped docs that fold cleanly)

### Phase C.1 — Delete `05-infrastructure/cloud-agnostic-migration.md` stub — PARALLEL — P1

- [ ] [SCRIPT] P1. The 05-infrastructure version is 501 bytes redirecting to
      `04-architecture/cloud-agnostic-migration.md`. Delete the stub; redirect incoming refs.

  **Implementation**:
  - [ ] `git rm codex/05-infrastructure/cloud-agnostic-migration.md`.
  - [ ] Update `codex/05-infrastructure/README.md:171` (and any other incoming refs in 05-infra) to point at
        `04-architecture/cloud-agnostic-migration.md`.
  - [ ] Workspace-wide grep `codex/05-infrastructure/cloud-agnostic-migration.md` → rewrite all refs.

  **Acceptance**: stub deleted; no broken links.

### Phase C.2 — Fold `deployment-ui-environment-tiers.md` into `deployment-ui-architecture.md` — PARALLEL — P1

- [ ] [SCRIPT] P1. The new `deployment-ui-environment-tiers.md` (4K, shipped today) duplicates env-resolution-by-domain
      content already at `deployment-ui-architecture.md:117-141`. Plus the Tier 0/1/2/3 naming conflicts with
      `runtime-tiers-and-deployment.md` T0–T6.

  **Implementation**:
  - [ ] Move the hostname → port routing detail (lines 24-31 of environment-tiers) into `deployment-ui-architecture.md`.
  - [ ] Move the Tier 0/1/2 vs Tier 3 distinction (lines 16-21) into `deployment-ui-architecture.md` BUT rename axis to
        use UAC `EnvironmentTier` (DEV/STAGING/PROD) instead of the conflicting "Tier N" naming.
  - [ ] `git rm codex/05-infrastructure/deployment-ui-environment-tiers.md`.
  - [ ] Update incoming refs: `14-playbooks/authentication/firebase-local.md` (if it references the env-tiers doc), the
        NEW docs from PM@9d873547 that cited it.

  **Acceptance**: doc deleted; deployment-ui-architecture.md is the single SSOT for deployment-UI tier model.

### Phase C.3 — Fold `launcher-script-consolidation-2026-05-07.md` into `launcher-script-ssot.md` — PARALLEL — P1

- [ ] [SCRIPT] P1. The migration-tracker doc is dated; once the 30 ad-hoc launchers finish migrating, the tracker
      becomes obsolete. The launcher-script-ssot.md already has a "Migration in flight (2026-05-07)" section that
      captures the same data at higher level.

  **Implementation**:
  - [ ] Append the migration table from `launcher-script-consolidation-2026-05-07.md` § "Migration table" into
        `launcher-script-ssot.md` § "Migration in flight".
  - [ ] `git rm codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md`.
  - [ ] Update incoming refs (workspace-wide grep).

  **Acceptance**: launcher SSOT doc has the full migration table; tracker deleted.

---

## LAYER D — Medium consolidations (sequential or partly-parallel; coordinate cross-doc refs)

### Phase D.1 — data-status-drilldown duplicate merge — PARALLEL — P1

- [ ] [SCRIPT] P1. Merge `data-status-drilldown.md` (215L) + `data-status-drilldown-hierarchy.md` (105L) into a single
      doc.

  **Target shape** (`data-status-drilldown.md`):
  - §1 Overview / API surface
  - §2 Per-asset_group depth table (from -hierarchy.md)
  - §3 Shard-class matrix (from -drilldown.md)
  - §4 ShardDetailModal endpoint contract (from -drilldown.md)
  - §5 Hierarchical drill endpoint (from -hierarchy.md)
  - §6 Cross-references

  **Cross-doc references to update** (verified in audit):
  - [ ] `02-data/availability-manifest-and-data-status.md` — drill-down hierarchy section pointing at -hierarchy.md →
        point at merged doc § "Per-asset_group depth table".
  - [ ] `02-data/deployment-ui-drilldown-depth-audit.md:55` — same.
  - [ ] `06-coding-standards/cli-convention.md:147` — same.
  - [ ] `06-coding-standards/test-coverage-data-status.md:55` — same (doc shipped today PM@9d873547).
  - [ ] `04-architecture/data-flow-map.md` — same.
  - [ ] `09-strategy/cross-cutting/dart-manual-trade-spec.md` — verify any drilldown reference.
  - [ ] Any plan in `plans/active/` referencing -hierarchy.md.

  **Implementation**:
  - [ ] Create merged file content.
  - [ ] `git rm codex/02-data/data-status-drilldown-hierarchy.md`.
  - [ ] Workspace-wide grep `data-status-drilldown-hierarchy.md` → rewrite all refs.

  **Acceptance**: only one drill-down doc; no broken links.

### Phase D.2 — Sports 5-doc consolidation → 3 docs — PARALLEL — P1

- [ ] [SCRIPT] P1. Per audit C3, sports docs collapse 5 → 3.

  **Keep**:
  - `02-data/sports-data-source-coverage-matrix.md` (coverage SSOT — unchanged).
  - `02-data/sports-scheduling-and-sharding.md` (timing SSOT — unchanged but body needs the multi-axis-banner
    reconciliation per audit 1c, see Phase D.3 below).
  - `02-data/sports-adapter-dependency-order.md` (T0/T1 dependency graph — unchanged).

  **Delete**:
  - [ ] `02-data/sports-data-migration.md` — superseded by `per-category-bucket-layouts.md` + reality of shipped sports
        buckets. Migrate any unique content (verify) before deletion.
  - [ ] `02-data/sports-schema-paths.md` — GCS path SSOT now lives in UAC `gcs_paths.py` +
        `per-category-bucket-layouts.md`. Migrate the SOURCE_COVERAGE_START table (already done via Phase B.5) before
        deletion.

  **Cross-doc references to update**:
  - [ ] All `14-playbooks/sports/*` if any reference the deleted docs.
  - [ ] `04-architecture/sports-integration-plan.md` — verify.
  - [ ] `09-strategy/architecture-v2/archetypes/{ml-directional,market-making,rules-directional,event-driven}-event-settled.md`
        — verify any reference.
  - [ ] Any plan in `plans/active/` referencing the deleted docs.

  **Acceptance**: only 3 sports docs in `02-data/`; no broken links.

### Phase D.3 — Multi-axis correction body-text reconciliation — SEQUENTIAL after A.1, A.2 — P0

- [ ] [SCRIPT] P0. The MULTI_AXIS_CORRECTION banner declares `fixture_id` and `market_id` are row-level columns NOT
      shard axes. But the same files contain pre-correction body text. Sweep body text to match banner.

  **Files to update** (verified in audit 1c):
  - [ ] `02-data/sports-scheduling-and-sharding.md:55-56` — "Per-fixture shard atom (writegate Phase 2.B):
        `(asset_group=sports, source, data_type, league_id, fixture_id, day)`" — `fixture_id` is shard axis here.
        Reconcile with banner OR confirm with operator that writegate Phase 2.B made it canonical.
  - [ ] `02-data/availability-manifest-and-data-status.md:198-201` — same restatement.
  - [ ] `02-data/per-category-bucket-layouts.md:101` — per-fixture path.
  - [ ] `02-data/prediction-schema-paths.md:114` — `market_id` shown as shard axis.

  **Operator decision required**: which is canonical — banner (row-level) or body (shard-axis)? Cross-check with
  `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 2.B + UTL `manifest_writer.py` `record_captured` shard_key
  signature for sports/prediction.

  **Acceptance**: banner + body text agree; one shard-atom shape per asset_group documented.

### Phase D.4 — Custody triplet → custody-providers.md SSOT — SEQUENTIAL after A.1 — P1

- [ ] [SCRIPT] P1. Per audit C5, fold `copper-custody-integration.md` (245L) and `ceffu-custody-integration.md` (95L
      stub) into `custody-providers.md` (193L, protocol SSOT) as per-provider §s.

  **Target shape** (`custody-providers.md`):
  - §1 Overview / pluggable interface
  - §2 Provider implementations: Copper / CEFFU / LocalKey / Mock — each as a sub-§
  - §3 Coverage matrix per (asset_group, venue) — which provider backs which
  - §4 Mode matrix (testnet / paper / live)

  **Cross-doc references to update**:
  - [ ] `09-strategy/architecture-v2/archetypes/carry-staked-basis.md:33` — references UAC venue_collateral; verify path
        still works.
  - [ ] `14-playbooks/defi/venue-collateral-2026-05-07.md` — should cross-link to custody-providers doc (and to
        `04-architecture/copper-custody-integration.md` was reverted by linter — verify final state).
  - [ ] `plans/active/master_to_live_defi_2026_05_23.md` Group F item 19 — references both copper + ceffu docs.
  - [ ] `04-architecture/interface-credential-convention.md` — references credential injection per provider.
  - [ ] `04-architecture/wallet-hierarchy-and-capital-flow.md` — verify.
  - [ ] All NEW docs from PM@9d873547 + PM@d212f4e6 that cross-linked the per-provider docs.

  **Implementation**:
  - [ ] Migrate Copper content → `custody-providers.md § Copper`.
  - [ ] Migrate CEFFU stub content → `custody-providers.md § CEFFU` (mark as planned where stubs).
  - [ ] `git rm codex/04-architecture/copper-custody-integration.md`.
  - [ ] `git rm codex/04-architecture/ceffu-custody-integration.md`.
  - [ ] Workspace-wide grep both deleted filenames → rewrite all refs.

  **Acceptance**: single custody doc; no broken links.

### Phase D.5 — Validation/error chapter merge → `validation-and-errors.md` — SEQUENTIAL after A.2 — P1

- [ ] [SCRIPT] P1. Per audit C6, merge `error-handling.md` (181L) + `validation-patterns.md` (241L) +
      `schema-validation.md` (83L) into `validation-and-errors.md`. Eliminates write-gate-quartet duplication +
      error-class naming drift (`SchemaMismatchError` vs `SchemaValidationFailedError`).

  **Target shape** (`06-coding-standards/validation-and-errors.md`):
  - §1 4-category empty-output decision (from error-handling)
  - §2 Write-gate quartet (single SSOT, currently duplicated)
  - §3 Per-row schema validation (from schema-validation)
  - §4 available_at + LookaheadBias (current split is muddled — split error class)
  - §5 InstrumentsWriteGate
  - §6 Per-shard try/except pattern

  **Cross-doc references to update**:
  - [ ] `02-data/availability-manifest-and-data-status.md` — references manifest semantics + write-gate quartet.
  - [ ] `02-data/honest-absence-downstream-handling.md` — references the 4-category decision.
  - [ ] `04-architecture/shard-level-failure-isolation.md` — references the per-shard try/except pattern.
  - [ ] `14-playbooks/alerting/threshold-tuning.md` — references SCHEMA_VALIDATION_FAILED reason.
  - [ ] All NEW docs that cited `06-coding-standards/schema-validation.md` (PM@9d873547).

  **Implementation**:
  - [ ] Create merged file.
  - [ ] `git rm codex/06-coding-standards/error-handling.md`.
  - [ ] `git rm codex/06-coding-standards/validation-patterns.md`.
  - [ ] `git rm codex/06-coding-standards/schema-validation.md`.
  - [ ] Update all cross-doc refs.

  **Acceptance**: single validation/errors doc; no broken links; one error-class hierarchy per concern.

### Phase D.6 — batch-live principle merge → `batch-live-architecture.md` — SEQUENTIAL after A.5, A.6 — P1

- [ ] [SCRIPT] P1. Per audit C9, merge `batch-live-pipeline.md` (195L) + `batch-live-symmetry.md` (263L) into
      `batch-live-architecture.md`. Major overlap on principle.

  **Target shape** (`04-architecture/batch-live-architecture.md`):
  - §1 Principle (from pipeline)
  - §2 The 4 seams (from symmetry)
  - §3 Anti-drift guards (from symmetry)
  - §4 Service audit matrix (from symmetry, post-A.6 fix)
  - §5 Matching engine + book matchers table (from pipeline)
  - §6 Strategy alpha vs execution alpha (from pipeline)
  - §7 Sports-specific notes (from pipeline)
  - §8 Anti-patterns fixed (from pipeline)
  - §9 Instruments-live exception (from pipeline, NEW today)
  - §10 References + cross-refs

  **Cross-doc references to update** (~15 incoming refs):
  - [ ] `02-data/honest-absence-downstream-handling.md`.
  - [ ] `02-data/pipeline-mode-partition.md`.
  - [ ] `04-architecture/instruments-live-architecture.md`.
  - [ ] `04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`.
  - [ ] `04-architecture/features-service-architecture.md`.
  - [ ] `04-architecture/seamless-cloud-switch.md`.
  - [ ] `04-architecture/research-service-and-dart-integration.md`.
  - [ ] `04-architecture/live-strategy-config-hot-reload.md`.
  - [ ] `04-architecture/ml-experiment-lifecycle.md`.
  - [ ] `05-infrastructure/live-pipeline-architecture.md`.
  - [ ] `06-coding-standards/feature-service-pattern.md`.
  - [ ] `06-coding-standards/integration-testing-layers.md`.
  - [ ] `09-strategy/architecture-v2/cross-cutting/benchmark-fills.md` (and any sibling).
  - [ ] All plans referencing either deleted doc.
  - [ ] CLAUDE.md references (review before changing).

  **Implementation**:
  - [ ] Create merged file.
  - [ ] `git rm codex/04-architecture/batch-live-pipeline.md`.
  - [ ] `git rm codex/04-architecture/batch-live-symmetry.md`.
  - [ ] Update all cross-doc refs (workspace-wide grep both filenames).

  **Acceptance**: single batch-live doc; no broken links.

### Phase D.7 — Service-standards consolidation → README chapter — SEQUENTIAL — P1

- [ ] [SCRIPT] P1. Per audit C7, delete `service-structure-standards.md` (stub), fold D1-D5 progression from
      `service-hardening-checklist.md` into `06-coding-standards/README.md § Production Readiness Checklist`.

  **Implementation**:
  - [ ] `git rm codex/06-coding-standards/service-structure-standards.md` (already a 13-line stub after revert).
  - [ ] Move D1-D5 content from `service-hardening-checklist.md` into `README.md`.
  - [ ] Convert `service-hardening-checklist.md` to a redirect stub (or `git rm` if README absorbs all content).
  - [ ] Update incoming refs: 04-arch + 05-infra docs + plans.

  **Acceptance**: README is the single SSOT for service hardening; stub gone.

### Phase D.8 — Path-layout 4-doc consolidation — SEQUENTIAL after A.1 — P1

- [ ] [SCRIPT] P1. Per audit C2, sub-tree restructure for path layouts.

  **Keep as SSOT**:
  - `02-data/per-asset-group-bucket-layouts.md` (renamed from `per-category-bucket-layouts.md` per S3) — path-shape
    divergences SSOT.

  **Collapse to pointers**:
  - `02-data/partitioning.md` § Path Templates → short pointer.
  - `02-data/hive-schema-compatibility.md` § Partitioning Strategy → short pointer (retain unique parquet+BQ rationale).
  - `02-data/pipeline-coverage-matrix.md` § bucket topology → short pointer.

  **Cross-doc references to update**:
  - [ ] `02-data/instrument-pipeline-defi.md:40-41`.
  - [ ] `02-data/data-lineage-MTDS-features-ml.md:153`.
  - [ ] `02-data/chart-candle-delivery-flow.md:33`.
  - [ ] `02-data/prediction-schema-paths.md:41`.
  - [ ] `09-strategy/architecture-v2/category-instrument-coverage.md` (also rename-aware per S3).
  - [ ] `14-playbooks/instruments-live/t1-audit-discrepancy.md`.
  - [ ] All NEW docs (PM@9d873547) that cited `per-category-bucket-layouts.md`.

  **Operator decision required**: confirm filename rename `per-category-bucket-layouts.md` →
  `per-asset-group-bucket-layouts.md` per S3 + asset_group vocabulary rule.

  **Acceptance**: per-asset-group-bucket-layouts.md is the single path-layout SSOT; other docs cite it.

---

## LAYER E — Heavy structural moves (sequential; operator-decision required per move)

### Phase E.1 — Topology 7-doc cluster reorganisation — OPERATOR APPROVAL — P1

- [ ] [DOC] P1 (BLOCKED on operator approval — heaviest blast radius). Per audit C4,
      `04-architecture/{RUNTIME_TOPOLOGY_DECISIONS, TIER-ARCHITECTURE, service-family-scope, deployment-topology-diagrams, pipeline-service-layers, api-services-cluster, PROTOCOL-INJECTION}`
      → 3 docs.

  **Target shape**:
  - `04-architecture/tier-and-import-architecture.md` (TIER-ARCHITECTURE + PROTOCOL-INJECTION + import rules).
  - `04-architecture/runtime-deployment-topology.md` (RUNTIME_TOPOLOGY §1-9 + deployment-topology-diagrams +
    api-services-cluster + pipeline-service-layers).
  - `04-architecture/commercial-service-families.md` (rename from service-family-scope; this is commercial/UX, not
    architecture).

  **Blast radius**: ~30 references across 02-data, 05-infra, 09-strategy, 14-playbooks. Full grep + per-file rewrite.

  **Why blocked**: heaviest cross-doc impact. Operator should explicitly approve before this lands; consider deferring
  past May-23 cutover.

### Phase E.2 — 14-playbooks split into 3 directories — OPERATOR APPROVAL — P2

- [ ] [DOC] P2 (BLOCKED on operator approval — workspace-wide doc-tree change). Per audit S1, `14-playbooks/` mixes 4
      genres. Proposed split:
  - `14-customer-journeys/` (rename) — experience/, playbooks/, commercial-model/, demo-ops/, authentication/,
    environments/, page-triage/, presentations/, roadmap/, implementation-mapping/, \_ssot-rules/, glossary, IA, README,
    dart/, shared-core/, cross-cutting/-as-playbook-concepts/.
  - `15-runbooks/` (NEW) — alerting/, instruments-live/, smoke-testing-playbook, backfill-completion-playbook + future
    per-archetype runbooks.
  - `16-strategy-playbooks/` (NEW) — defi/, strategy/, ml/, infra-spec/.

  **Why blocked**: top-level directory rename; affects every codex doc cross-linking into 14-playbooks/ and every
  CLAUDE.md reference.

### Phase E.3 — 09-strategy cross-cutting collapse — OPERATOR APPROVAL — P2

- [ ] [DOC] P2 (BLOCKED on operator approval). Per audit S2, two parallel `cross-cutting/` directories in 09-strategy:
  - Move v2-content (`dart-manual-trade-spec`, `operational-modes-matrix`, `pnl-attribution`, `prediction-markets`,
    `leverage-and-volatility`, `restaking-reward-economics`, `reward-lifecycle`, `rate-impact-model`) into
    `architecture-v2/cross-cutting/`.
  - Rename remaining `09-strategy/cross-cutting/` → `09-strategy/operational/` (5 files: onboarding-checklist,
    client-onboarding, client-strategy-config, instrument-filtering, prediction-markets-codification-gaps).

  **Why blocked**: cross-doc impact + ambiguity if other agents are mid-flight in these dirs.

### Phase E.4 — Filename rename: per-category-bucket-layouts → per-asset-group-bucket-layouts — OPERATOR APPROVAL — P1

- [ ] [DOC] P1 (BLOCKED on operator approval). Per audit S3 + workspace asset_group vocabulary rule. The file body uses
      both `category` and `asset_group` inconsistently. Rename + body-sweep.

### Phase E.5 — Audit-style doc moves out of 06-coding-standards — OPERATOR APPROVAL — P2

- [ ] [DOC] P2. Move `cod-deadlock-verification-report.md` (Feb 2026 dated, stale)
  - `orphan-audit.md` (UI architecture concern) out of `06-coding-standards/`. Either to `codex/15-audits/` (NEW
    directory) or archive. Operator picks.

---

## LAYER F — Cosmetic + index updates (parallel; ship anytime)

### Phase F.1 — quality-gates.md ToC — PARALLEL — P2

- [ ] [SCRIPT] P2. `quality-gates.md` is 1667 lines / 73K with no top-of-file ToC.

  **Implementation**:
  - [ ] Add numbered ToC at top linking to STEP 5.X anchors.
  - [ ] Cross-reference STEP numbers from CLAUDE.md (5.10/5.11/5.22/5.34/5.61/5.62/5.64/5.66) into a single "QG STEP
        cross-reference" table.

### Phase F.2 — UI infra rename + collapse — PARALLEL — P2

- [ ] [SCRIPT] P2. `UI-FUNCTIONALITY-REQUIREMENTS.md` (32K) + `UI-DEPENDENCY-MATRIX.md` (15K) — all-caps filenames are
      unique to this dir. Rename to lowercase-kebab. Bulk of content is "ARCHIVED — reference only" notes; consider
      collapsing to one `ui-archive-reference.md`.

### Phase F.3 — Severity tier glossary — PARALLEL — P1

- [ ] [SCRIPT] P1. Per audit (14-playbooks A): codex enum (CRITICAL/HIGH/WARN/INFO) vs PagerDuty (P0/P1/P2/P3) vs
      `AlertSeverity.WARN` (Python). Add a single glossary table at top of `14-playbooks/alerting/README.md` (or
      `03-observability/alerting.md`) mapping all three. Other docs cite.

### Phase F.4 — `aws_migration_cost_analysis_2026_05_07.md` extract + archive — PARALLEL — P2

- [ ] [SCRIPT] P2. 53K research-grade doc, recommendation paragraph explicitly superseded. Extract per-resource cost
      tables → `aws-migration-cost-snapshot-2026-05-07.md` (~10-15K). Move full original to `plans/archive/` or
      `codex/15-audits/`.

### Phase F.5 — README.md cleanup (05-infrastructure) — PARALLEL — P2

- [ ] [SCRIPT] P2. `05-infrastructure/README.md:171,176-177,184-185` link to non-existent files (`terraform.md`,
      `ci-cd.md`, `docker.md`, `versioning-rollback.md`, `batch/README.md`, `live/README.md`). Either create or remove.

### Phase F.6 — 09-strategy READMEs refresh — PARALLEL — P1

- [ ] [SCRIPT] P1 (combines with Phase A.4). Ensure `09-strategy/README.md` and `09-strategy/architecture-v2/README.md`
      reflect 9/53 throughout (counts already in A.4; this phase is the doc-shape pass).

---

## LAYER G — Final cross-directory consistency check

### Phase G.1 — Final cross-directory audit — SEQUENTIAL after every other phase — P0

- [ ] [AGENT] P0. After all phases land, spawn one cross-directory audit agent (same shape as the Wave 2 synthesis but
      post-execution) to verify:
  1. Every claim made in Layer A P0 fixes is now consistent across the workspace.
  2. Every consolidated doc has no broken incoming refs (workspace-wide grep for deleted filenames).
  3. Every banner-removed doc is internally consistent (no dangling references to archived plans).
  4. Every cross-directory dependency from the Wave 2 report has been resolved or explicitly deferred.

  **Output**: a final consistency report. Any unresolved findings become new plan todos here per the workspace "Capture
  discoveries as plan todos immediately" rule.

---

## Codex SSOT updates this plan owns

Per CLAUDE.md "Post-Plan-Phase Codex Audit HARD RULE", every plan that lands a contract / pattern / architectural change
MUST list the codex docs it touches. This is a doc-only plan, so the affected codex docs ARE the plan deliverables —
listed inline per phase.

NEW docs created mid-execution (if any phase generates them): add to this section as discovered.

NEW codex docs explicitly created by this plan:

- [ ] `codex/04-architecture/batch-live-architecture.md` (Phase D.6, replaces 2)
- [ ] `codex/04-architecture/tier-and-import-architecture.md` (Phase E.1, IF approved)
- [ ] `codex/04-architecture/runtime-deployment-topology.md` (Phase E.1, IF approved)
- [ ] `codex/04-architecture/commercial-service-families.md` (Phase E.1, IF approved)
- [ ] `codex/06-coding-standards/validation-and-errors.md` (Phase D.5, replaces 3)

DELETED codex docs by this plan:

- [ ] `codex/05-infrastructure/cloud-agnostic-migration.md` (Phase C.1, stub)
- [ ] `codex/05-infrastructure/deployment-ui-environment-tiers.md` (Phase C.2)
- [ ] `codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md` (Phase C.3)
- [ ] `codex/02-data/data-status-drilldown-hierarchy.md` (Phase D.1)
- [ ] `codex/02-data/sports-data-migration.md` (Phase D.2)
- [ ] `codex/02-data/sports-schema-paths.md` (Phase D.2)
- [ ] `codex/04-architecture/copper-custody-integration.md` (Phase D.4)
- [ ] `codex/04-architecture/ceffu-custody-integration.md` (Phase D.4)
- [ ] `codex/06-coding-standards/error-handling.md` (Phase D.5)
- [ ] `codex/06-coding-standards/validation-patterns.md` (Phase D.5)
- [ ] `codex/06-coding-standards/schema-validation.md` (Phase D.5)
- [ ] `codex/06-coding-standards/service-structure-standards.md` (Phase D.7, stub)
- [ ] `codex/04-architecture/batch-live-pipeline.md` (Phase D.6, replaced)
- [ ] `codex/04-architecture/batch-live-symmetry.md` (Phase D.6, replaced)
- [ ] Some/all 12 stub files in `codex/06-coding-standards/` (Phase B.4, per-file decision)
- [ ] Topology 7-doc cluster (Phase E.1, IF approved): `RUNTIME_TOPOLOGY_DECISIONS.md`, `TIER-ARCHITECTURE.md`,
      `service-family-scope.md`, `deployment-topology-diagrams.md`, `pipeline-service-layers.md`,
      `api-services-cluster.md`, `PROTOCOL-INJECTION.md`.

---

## Open questions

### Q1 — [main, 2026-05-08] — Multi-axis correction: banner or body canonical?

**Status**: 🟡 BLOCKED — operator answer needed before Phase D.3.

The MULTI_AXIS_CORRECTION banner declares `fixture_id` (sports) and `market_id` (prediction) are row-level, NOT shard
axes. But ~5 docs in 02-data have body text saying the writegate Phase 2.B contract uses them as shard axes. Which is
canonical?

**Decision criteria**: cross-check with `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 2.B + UTL
`manifest_writer.py` `record_captured` shard_key signature for sports

- prediction. If shard_key includes `fixture_id`/`market_id`, the body is correct and the banner is stale. If not, the
  banner is correct and the body is stale.

### Q2 — [main, 2026-05-08] — POST_PLAN_BANNER sweep: per-directory or workspace-wide single commit?

**Status**: 🟡 BLOCKED — operator preference.

~250 files. Single-commit workspace-wide sweep is cleaner audit history. Per-directory sweep is safer if a commit breaks
(smaller revert surface).

**Default**: per-directory (one commit per dir; 7 commits total).

### Q3 — [main, 2026-05-08] — Heavy structural moves (E.1/E.2/E.3/E.4/E.5): pre or post May-23?

**Status**: 🟡 BLOCKED — operator decision.

These have cross-doc blast radius. Pre-May-23: agents touching these dirs collide with the rename. Post-May-23: cleanup
happens after the cutover.

**Recommendation**: defer E.1 + E.2 + E.5 to post-May-23. Ship E.3 + E.4 pre-May-23 as they are smaller and fix
correctness drift (the dual cross-cutting/ + the category/asset_group filename inconsistency).

### Q4 — [main, 2026-05-08] — `unified-feature-calculator-library` survival post-features-consolidation?

**Status**: 🟡 BLOCKED — verify against `features_repo_consolidation_2026_05_08.md`.

Phase B.3 sweep needs to know whether the library survives as inner-package or is fully consolidated. Operator or
features-consolidation plan author to confirm.

---

## Cross-plan coordination

Reads: `manifest_v7_schema_migration_design_2026_05_08.md` (manifest schema SSOT),
`writegate_honest_coverage_endtoend_2026_05_06.md` (capture taxonomy + reason taxonomy SSOT),
`live_pipeline_mtds_mdps_features_2026_05_08.md` (live transport SSOT), `features_repo_consolidation_2026_05_08.md`
(features-\_ deployment SSOT), `alerting_service_live_rules_2026_05_07.md` (CIRCUIT\_\_ + severity tier SSOT),
`master_to_live_defi_2026_05_23.md` (custody / live-monitoring SSOT).

Writes-to: codex/ exclusively. No code changes. No plan changes outside this plan file (per HARD RULE: only edit your
own plan-of-record).

## Why this plan structure

The phases are sized so each is a shippable unit (per CLAUDE.md "Commit + Push + Flip Plan Checkboxes"). Layer A phases
run in parallel and ship independently. Layer B phases are workspace-wide mechanical sweeps that don't conflict with
each other or with Layer A (different files / different concerns). Layer C phases are just-shipped doc collapses with
minimal ref churn. Layer D phases are medium consolidations with explicit cross-doc ref tables. Layer E phases are heavy
moves needing operator approval. Layer F is cosmetic/index work. Layer G is the final verification gate.

Parallel agents pick a phase, execute it end-to-end (including ref updates), commit

- push as one logical unit, flip the checkbox in this plan file. The plan-file structure follows the workspace
  work-split pattern — each phase is self-contained, with explicit Acceptance criteria.
