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
  `02-data/per-asset-group-bucket-layouts.md` to use the `asset_group` vocabulary; renamed in Phase E.4).
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

### Phase A.1 — Manifest schema version unification — PARALLEL — P0 — SHIPPED 2026-05-08 (PM@bcd83823 merge)

- [x] [SCRIPT] P0. Single-pass sweep: every codex doc claiming a manifest schema version must cite the canonical version
      per `manifest_v7_schema_migration_design_2026_05_08.md` (current = v7; target = v8). UTL `manifest_writer.py`
      `MANIFEST_SCHEMA_VERSION` is the runtime SSOT. **Confirmed UTL constant**: `MANIFEST_SCHEMA_VERSION = 7` at
      `unified-trading-library/unified_trading_library/manifest_writer.py:131`.

  **Files audited + updated where drift existed**:
  - [x] `02-data/availability-manifest-and-data-status.md` — already correct: § "Schema v7 (current)" line 222,
        `MANIFEST_SCHEMA_VERSION = 7` line 233, v8 in design block line 297-305. No edit needed.
  - [x] `02-data/per-asset-group-bucket-layouts.md` (renamed in Phase E.4 from `per-category-bucket-layouts.md`) — only
        multi-axis correction banner at line ~13, no version conflict. No edit needed.
  - [x] `02-data/partitioning.md` — only multi-axis correction banner, no version conflict. No edit needed.
  - [x] `02-data/prediction-schema-paths.md` — only multi-axis correction banner, no version conflict. No edit needed.
  - [x] `02-data/shard-granularity-cefi.md:15` — Status line said "v6 columns active... manifest schema v6 shipped"
        without anchoring current overall = v7. **Edited** to add "Current overall schema is **v7**" + v8 design
        pointer + canonical SSOT reference; preserved v6 column rollout history (this doc owns the v6 column reference).
  - [x] `02-data/sports-scheduling-and-sharding.md` — only multi-axis correction banner, no version conflict. No edit
        needed.
  - [x] `02-data/pipeline-coverage-matrix.md:80-82` — already correct: `### Manifest schema (v7 — current)` +
        `MANIFEST_SCHEMA_VERSION = 7`. No edit needed.
  - [x] `02-data/data-lineage-MTDS-features-ml.md:33` — already correct: `**Manifest shard dims (v7 — current)**` with
        v5 / v6 / v7 history + v8 design pointer. No edit needed.
  - [x] `02-data/data-status-drilldown.md:76` — JSON enumerates v5 4-state `capture_status` taxonomy (unchanged under
        v7); no version conflict.
  - [x] `04-architecture/shard-level-failure-isolation.md:27,80,106` — already correct: cites "v7 manifest column" + "v7
        manifest row key" + "full v7 row key per asset_group". No edit needed.

  **Bonus drift caught beyond the audit list (case 1 finding — fixed in same shippable unit)**:
  - [x] `02-data/venue-availability.md:8` — said "(v4)" inline. **Edited** to "(v7 — current;
        `MANIFEST_SCHEMA_VERSION = 7` in UTL `manifest_writer.py`)".
  - [x] `02-data/manifest-migration-coordination.md:19` — said "next manifest-schema bump (v5 → v6) is planned".
        **Edited** to v7 → v8 design pointer + canonical runtime SSOT line.
  - [x] `05-infrastructure/vm-tarball-deployment.md:232` — said "Honest-coverage schema v5". **Edited** to
        "Honest-coverage `capture_status` taxonomy (introduced at schema v5; current schema v7)" so the historical
        reference doesn't read as the current schema version.

  **Acceptance met**: every doc citing a manifest schema version cites v7 (UTL `MANIFEST_SCHEMA_VERSION = 7`); no doc
  carries inline "v7 job_id" or "v8 pipeline_mode" banners that contradict its own version line.

  **Shipped via**: PM@bcd83823 merge commit (parallel-agent / prek-shield merge bundled this work alongside foreign
  edits; my 4 files are byte-identical with the spec drafted in this session —
  `git show origin/live-defi-rollout:<file>` verified).

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

### Phase A.3 — CIRCUIT_BREAKER naming alignment to UAC — PARALLEL — P0 — SHIPPED 2026-05-08 (PM@b257804a)

- [x] [SCRIPT] P0. Three-way naming drift: UAC `events.py:94-96` defines
      `CIRCUIT_OPEN / CIRCUIT_HALF_OPEN / CIRCUIT_CLOSED` (no `_BREAKER_` prefix). All codex docs must align to the UAC
      names. **DISCOVERY**: original premise was incomplete — UAC has TWO enums with intentionally different naming:
      `LifecycleEvent` (short, no prefix) at `internal/events.py:94-96` AND `AlertCode` (with `_BREAKER_` prefix) at
      `canonical/crosscutting/alerting/codes.py:42-45`. Both are SSOTs and don't conflict — LifecycleEvent for emitted
      events / PubSub topics / JSONL `.event` fields; AlertCode for alerting-service routing rules / runbook
      code+pattern fields / "correlated codes" cross-refs. Phase A.3 shipped fixes context-specific drift only.

  **Files updated** (PM@b257804a):
  - [x] `03-observability/lifecycle-events.md:328-329` — replaced past-tense `CIRCUIT_BREAKER_OPENED/CLOSED` with UAC
        LifecycleEvent names `CIRCUIT_OPEN / CIRCUIT_HALF_OPEN / CIRCUIT_CLOSED`.
  - [x] `03-observability/alerting.md:128,135,141,142` — **NO CHANGE**: these are alert routing rules; the patterns
        match UAC AlertCode `rules.py` SSOT verbatim (`CIRCUIT_BREAKER_OPEN`, `CIRCUIT_BREAKER_BACKOFF_*`,
        `CIRCUIT_BREAKER_DEGRADED`, `CIRCUIT_BREAKER_CLOSED` all exist as AlertCode enum members; `BACKOFF_ESCALATING`
        is the present-tense canonical, matching `BACKOFF_*` glob).
  - [x] `04-architecture/alerting-batch-live.md:66` — **NO CHANGE**: `event_name` field in alert record = AlertCode.
  - [x] `04-architecture/autonomous-recovery-matrix.md:245` — `subscribe to CIRCUIT_BREAKER_OPEN` → `CIRCUIT_OPEN`
        (PubSub subscribe = LifecycleEvent).
  - [x] `04-architecture/kill-switch-circuit-breaker.md:116, 158, 280-283` — PubSub publish + Emits narrative + PubSub
        Events table aligned to LifecycleEvent. Removed `CIRCUIT_BREAKER_DEGRADED / BACKOFF_ESCALATED / ORDER_THROTTLED`
        rows (none exist in UAC `LifecycleEvent` enum). Added Lifecycle-vs-Alert taxonomy note documenting the dual
        SSOT.
  - [x] `04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md:708` — `publishes CIRCUIT_BREAKER_OPEN` →
        `publishes CIRCUIT_OPEN     (UAC LifecycleEvent)`. (Already shipped in Phase A.5 PM@77e1978a.)
  - [x] `14-playbooks/alerting/alert-code-taxonomy.md:82` — **NO CHANGE**: describes AlertCode pattern.
  - [x] `14-playbooks/alerting/circuit_breaker_open.md:66-68, 81, 86, 89` — JSONL `.event` field references aligned to
        LifecycleEvent names; title/Code/Pattern (line 2/17/32/33) preserved as `CIRCUIT_BREAKER_OPEN` (AlertCode).
  - [x] `14-playbooks/alerting/kill_switch_venue_disconnect.md:88` — JSONL `select(.event=="...")` filter aligned to
        `CIRCUIT_CLOSED`. Line 75 "correlated codes" `CIRCUIT_BREAKER_OPEN` preserved (AlertCode).
  - [x] `14-playbooks/alerting/{service_degraded,defi_feature_stale,order_rejection_spike}.md` — **NO CHANGE**:
        "correlated codes" references are AlertCode patterns, correctly aligned with UAC `codes.py` SSOT.
  - [x] `14-playbooks/alerting/threshold-tuning.md` — verified, no CIRCUIT_BREAKER references in current file.

  **Acceptance** (revised): workspace-wide grep for `CIRCUIT_BREAKER_` in codex/ returns 19 hits — all legitimate
  AlertCode references. Zero LifecycleEvent drift remains (verified via grep of past-tense `CIRCUIT_BREAKER_OPENED`,
  `CIRCUIT_BREAKER_HALF_OPEN`, `CIRCUIT_BREAKER_BACKOFF_ESCALATED` past-tense, `CIRCUIT_BREAKER_ORDER_THROTTLED`, and
  JSONL `select(.event=="CIRCUIT_BREAKER...")` patterns — all return zero hits).

### Phase A.4 — Family/archetype count refresh to 9/53 — PARALLEL — P0 — SHIPPED 2026-05-08 PM@9e90239c

- [x] [SCRIPT] P0. UAC `StrategyArchetype` enum is the SSOT. All codex docs cite 9 families × 53 archetypes (PM@d6d0cd57
      refreshed strategy-summary.md; residuals refreshed PM@9e90239c).

  **Files to update**:
  - [x] `09-strategy/README.md:19` — `8 families × 18 archetypes × 7 axes × 10 cross-cutting` →
        `9 families × 53 archetypes × 7 axes × 10 cross-cutting`. Axis + cross-cutting counts verified unchanged against
        UAC + strategy-summary.md. (PM@9e90239c.)
  - [x] `09-strategy/architecture-v2/README.md:28-29` — `1 of 8 families` / `1 of 18 archetypes` → `1 of 9 / 1 of 53`.
        TL;DR action types also refreshed `(11 action types)` → `(14 action types per UAC InstructionActionV2 SSOT)`.
        (PM@9e90239c.)
  - [x] `09-strategy/architecture-v2/README.md:61` — section heading `## 8 Families` → `## 9 Families`; table extended
        with `PORTFOLIO` row; decision tree extended to 9 questions. (PM@9e90239c.)
  - [x] `09-strategy/architecture-v2/README.md:97,113` — `## 18 Archetypes` / `Total: 18 archetypes` →
        `## 53 Archetypes` / `Total: 53 archetypes`; table expanded to 9 family rows with full Phase 9 additions (4
        `ARBITRAGE_MEV_*` + 1 `ARBITRAGE_CROSS_DOMAIN_EVENT` + 5 new `MARKET_MAKING_*` + 3 `DEFI_LP_*` + 17 expanded
        `VOL_*` + 4 `PORTFOLIO_*`). 5-Layer Identity Model + Document Layout legend counts also updated;
        `## Polymorphic StrategyInstruction (11 action types)` → `(14 action types)` with `CONVERT_DUST` / `LP_MINT` /
        `LP_BURN` rows added. (PM@9e90239c.)
  - [x] `09-strategy/architecture-v2/category-instrument-coverage.md:17,1422` — `18 v2 strategy archetypes` →
        `53 v2 strategy archetypes` (line 17). Banner added documenting that the matrix body covers the May-23 live +
        immediate-backtest subset; full per-cell Phase 9 materialisation DEFERRED to Phase B (per-archetype subsection
        generation under `architecture-v2/archetypes/`). Changelog entry added 2026-05-08. (PM@9e90239c.)
  - [x] `09-strategy/cross-cutting/dart-manual-trade-spec.md:42-44, 67-75` — `11 action types` callout reworded to point
        at UAC `InstructionActionV2` SSOT (14 members enumerated; matrix below covers the 11 actions in scope for
        May-23, with `CONVERT_DUST` / `LP_MINT` / `LP_BURN` deferred alongside DeFi LP archetype activation).
        `18 archetypes ... at 46 archetypes` paragraph rewritten to point at the UAC SSOT without explicit count.
        `### 18 archetype docs referenced` heading rewritten to track the May-23 subset. The action-count drift in
        `strategy-summary.md:30-31` (`13 action types`) is a separate fix vs the UAC enum of 14; that drift is owned by
        the broader `strategy-summary.md` refresh under PM@d6d0cd57's continuation. (PM@9e90239c.)

  **Acceptance** (verified PM@9e90239c): workspace-wide
  `grep -rE "8 families|18 archetypes|46 archetypes" codex/09-strategy/` returns zero current-state hits (the only
  `18 archetypes` reference is in the 2026-04-19 changelog entry of `category-instrument-coverage.md`, which is a
  faithful historical record). UAC enum member counts (`StrategyFamily=9`, `StrategyArchetype=53`,
  `InstructionActionV2=14`) are SSOT.

### Phase A.5 — Live transport SSOT alignment to Redis Stream — PARALLEL — P0 — SHIPPED 2026-05-08

- [x] [SCRIPT] P0. `live_pipeline_mtds_mdps_features_2026_05_08.md` confirms Redis Stream cascade
      (CANDLE_BOUNDARY_CROSSED + CANDLE_COMPUTED) is the post-2026-05-08 SSOT for the inner-loop live cascade. Older
      codex docs claiming PubSub-only or embedded-only need banners pointing at the new SSOT.

  **Files updated**:
  - [x] `04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` — POST-2026-05-08 SSOT banner added to § 3 Messaging Rules; Core
        Rule + Transport Decision Matrix updated to name Redis Stream (inner-loop) + PubSub (cross-service) explicitly.
        Cross-links to `05-infrastructure/live-pipeline-architecture.md` + `03-observability/coordination-events.md`.
  - [x] `04-architecture/batch-live-symmetry.md` — TL;DR transport row updated to "Redis Stream (inner-loop) + PubSub
        (cross-service)"; "Live: PubSub as Message Bus" section retitled to "Redis Stream (inner-loop) + PubSub
        (cross-service) as Message Bus" with the per-transport-class breakdown. POST-2026-05-08 SSOT banner cross-links
        the live-pipeline + coordination-events docs.
  - [x] `04-architecture/deployment-topology-diagrams.md` — "Live Deployment" section retitled to "Redis Stream
        Cascade + Consolidated features-service"; package-embedding diagram explicitly framed as historical
        (pre-2026-05-08); post-2026-05-08 update block at end of "Key characteristics" describes the XADD / XREADGROUP
        cascade contract + cross-links live-pipeline-architecture + features-service-architecture.
  - [x] `04-architecture/README.md` — "two distinct concerns" framing rewritten: feature calculation runs in the
        consolidated features-service (asset-scoped + cross-cutting), data transport split between Redis Stream
        (inner-loop) + PubSub (cross-service). Cross-links live-pipeline-architecture + features-service-architecture.
  - [x] `03-observability/coordination-events.md` — already updated 2026-05-08 to mention Redis Stream cascade
        (PM@d212f4e6); verified — § "Redis Stream cascade (inner-loop live pipeline)" already names
        CANDLE_BOUNDARY_CROSSED + CANDLE_COMPUTED + XREADGROUP semantics + replay handoff. No further drift.

  **Acceptance**: every doc that names the live transport mechanism agrees with
  `05-infrastructure/live-pipeline-architecture.md` as the SSOT. ✅ verified.

### Phase A.6 — execution-service batch+live mode contradiction — PARALLEL — P0 — SHIPPED 2026-05-08

- [x] [SCRIPT] P0. CLAUDE.md "Batch = Live: Unified Pipeline Architecture" + the
      `04-architecture/batch-live-pipeline.md` matching engine + UAC `BatchExecutionMode` enum confirm execution-service
      runs in BOTH batch (matching engine fills) and live (real venue). The contrary claim must be removed.

  **Files updated**:
  - [x] `04-architecture/batch-live-symmetry.md` § "Per-Service Implementation Matrix" — execution-service row updated:
        Batch Handler = `MatchingEngineHandler`, Live Handler = `ExecutionLiveHandler`, mode = `batch / live`, test
        coverage = `unit + integration`, notes describe matching-engine fills (UAC `BatchExecutionMode`) vs real venue
        with cross-link to `batch-live-pipeline.md` for execution-alpha = live − simulated.
  - [x] `06-coding-standards/integration-testing-layers.md` — verified: no contradictory "execution = live only" claim.
        Doc references execution test layers without asserting live-only.
  - [x] `09-strategy/architecture-v2/archetypes/*.md` — verified via workspace grep: no archetype doc contains
        "execution is live-only" or equivalent contradiction. Acceptance met.
  - [x] `10-audit/repos/execution-service.yaml` — verified: `deployment_modes: ["batch", "live"]` +
        `business_modes: ["batch", "live"]` already declared correctly. No update needed.

  **Acceptance**: no codex doc claims execution-service is live-only. ✅ verified.

### Phase A.7 — features-service consolidation alignment — PARALLEL — P0 — SHIPPED 2026-05-08

- [x] [SCRIPT] P0. `features_repo_consolidation_2026_05_08.md` is the SSOT — single `features-service` repo with
      sub-packages (per asset_group + cross-cutting), single CLI surface, single launcher per cluster shape,
      `feature_family` UAC axis as primary shard key. Older codex docs claiming N separate features-\* repos are stale.

  **Files updated**:
  - [x] `04-architecture/README.md` — "Live deployments: 7-8 standalone processes" enumeration replaced with the
        consolidated shape: ONE `features-service` repo (8 family sub-packages) deployed in two flavors (asset-scoped
        colocated with MDPS + cross-cutting standalone), plus MTDS / instruments / strategy / execution. Cross-link to
        `features-service-architecture.md` + `live-pipeline-architecture.md`.
  - [x] `04-architecture/deployment-topology-diagrams.md` — Live Deployment section retitled (per Phase A.5 work); added
        explicit "Deploys 4-6 collapse to one consolidated features-service" sub-block in the post-2026-05-08 update
        describing the asset-scoped + cross-cutting flavors with feature_family dispatcher contract.
  - [x] `05-infrastructure/launcher-script-ssot.md` — verified: parallel agent already added § "features-service
        consolidation (2026-05-08)" describing the single `launch-features-vm.sh` parameterised by `--feature-family` +
        `--asset-group`, replacing the pre-2026-05-08 8 per-family launchers. No further drift.
  - [x] `05-infrastructure/deployment-clusters-live-vs-batch.md` — verified: doc already uses `features-*` (now meaning
        feature families within the consolidated repo); single passing mention of "features-sports input pipeline" is
        harmless prose. No update needed.

  **Acceptance**: no codex doc enumerates 5+ separate `features-*-service` repos as the live deployment shape. ✅
  verified.

---

## LAYER B — Workspace-wide mechanical sweeps (parallel; ship after Layer A or in parallel with it)

### Phase B.1 — POST_PLAN_BANNER_2026_05_06 sweep (workspace-wide) — PARALLEL — P0 — SHIPPED 2026-05-08

- [x] [SCRIPT] P0. Banner cites 3 plans: writegate-honest-coverage (still active), predictions-canonical_question_group
      (archived per MEMORY, folded into predictions_master), data-status-multi-axis-shard (no longer findable). 2 of 3
      banner-named plans no longer exist; banner is workspace-wide stale.

  **Scope**: 366 files across all codex sub-trees carried the banner (counted at sweep start). Sweep removed BOTH the
  canonical `POST_PLAN_BANNER_2026_05_06_FINAL` shape AND the longer legacy `POST_PLAN_BANNER_2026_05_06` multi-line
  variant (24 files used the legacy shape; 342 used the FINAL shape).

  **Implementation** (operator-confirmed cadence: per-directory commit):
  - [x] Find every codex/\*.md containing `POST_PLAN_BANNER_2026_05_06[_FINAL]`.
  - [x] Per directory: bulk-remove the banner from every file in that directory. Single commit per directory.
  - [x] Operator approved (Q2 of plan).

  **Per-directory commits**:
  - PM@d094afdc — small dirs bundle (00-SSOT-INDEX + 01-domain + 02-venues + 03-observability + 03-services) — 11 files
  - PM@d14d2591 — 02-data/ (14 files; 4 skipped due to foreign WIP — 2 swept later, 2 absorbed by PM@e641f3f1)
  - PM@489108ce — 04-architecture/ (54 files, my sweep but message-attributed to a parallel agent's Phase C.3 commit
    that hijacked my staging — content correct, attribution muddled, foot-gun #1 incident)
  - PM@f58bc8a9 — 05-infrastructure/ (24 files; one foreign delete bundled, foot-gun #1 incident)
  - PM@06e13ce2 — 06-coding-standards/ (45 files)
  - PM@dedbe935 — 09-strategy/ (84 files)
  - PM@8090d09c — 14-playbooks/ (129 files)
  - PM@e641f3f1 — 02-data/ residual 2 files (`data-lineage-MTDS-features-ml.md` +
    `sports-data-source-coverage-matrix.md`) — absorbed by parallel agent's Phase D.2 sports consolidation, not a
    standalone B.1 commit but ships the same content.

  **Total**: 366 files swept across 8 commits (5 mine clean, 1 mine + 1-foreign-bundle, 1 foreign with my content, 1
  foreign with my redundant content). Workspace-wide grep `POST_PLAN_BANNER_2026_05_06` in codex/ returns zero hits.

  **Acceptance**: workspace-wide grep `POST_PLAN_BANNER_2026_05_06` in codex/ returns zero hits — VERIFIED.

### Phase B.2 — Plan filename convention sweep (.plan.md → .md in active/) — PARALLEL — P1 — SHIPPED 2026-05-08

- [x] [SCRIPT] P1. CLAUDE.md "Plan Filename Convention" says `plans/active/` uses `.md`, `plans/archive/` uses
      `.plan.md`. Many codex docs reference `plans/active/<x>.plan.md` (legacy convention). **SHIPPED PM@d9d023df** —
      124 files changed, 342 rewrites total (per-directory: 14-playbooks 131, 02-data 45, 05-infrastructure 41,
      09-strategy 39, root 32, 06-coding-standards 20, 04-architecture 19, 10-audit 9, 08-workflows 4,
      11-project-management 2). Renames performed: `plans/active/<slug>.plan.md` → `plans/active/<slug>.md` (or
      `plans/epics/<slug>.md` / `plans/epics/<slug>.epic.md` / `plans/archive/<slug>.plan.md` /
      `plans/ai/<slug>.plan.md` based on actual file location). Plus 4 stale-date refs
      (`aws_migration_defi_first_2026_05_06` → `_2026_05_07`) + 5 wildcard/template refs updated to new convention.

  **Files updated** (sample from audit; full sweep done):
  - [x] `09-strategy/architecture-v2/archetypes/carry-staked-basis.md` — both refs updated.
  - [x] `06-coding-standards/validation-patterns.md` — multiple refs updated.
  - [x] `06-coding-standards/service-hardening-checklist.md` — refs updated.
  - [x] `06-coding-standards/pre-sprint-baseline.md` — `phase0_standards_enforcement.plan.md` updated.
  - [x] `06-coding-standards/orphan-audit.md` — `orphan_audit_policy_2026_04_21.plan.md` updated.
  - [x] `06-coding-standards/error-handling.md` — `writegate_honest_coverage_endtoend_2026_05_06.plan.md` updated.
  - [x] `06-coding-standards/terminology-ssot.md` — `dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`
        updated.

  **Implementation**:
  - [x] Workspace-wide grep `plans/active/.*\.plan\.md` → flagged every hit.
  - [x] For each: resolved target file (active → `.md`, epics → `.md`/`.epic.md`, archive → `.plan.md` w/ path prefix
        rewrite, ai → `.plan.md` w/ path prefix rewrite). Unresolved (stale-date) refs were rewritten to the renamed
        plan path.
  - [x] Single sweep commit (124 files in one logical commit).

  **Acceptance**: workspace-wide grep `plans/active/.*\.plan\.md` in codex/ returns 0 hits (verified post-sweep).

### Phase B.3 — Stale repo / provider reference sweep — PARALLEL — P1 — SHIPPED 2026-05-08

- [x] [SCRIPT] P1. Multiple stale references identified across audits. **SHIPPED PM@ec9abecf** (re-sweep after
      PM@c2bc6cd5 only landed 3 files due to prek hook auto-restore — foot-gun #4); the re-sweep landed 157 files
      changed, 329 insertions, 326 deletions in one tight Edit→add→commit→push bundle.

  **Renames applied (workspace-wide)**:
  - [x] `unified-market-interface` → `market-tick-data-service/market_tick_data_service/market_interface` (UMI archived;
        CLAUDE.md confirms). 64 hits across 36 .md files + 2 .svg files (architectures DAG diagrams).
  - [x] `unified-internal-contracts/` → `unified_api_contracts.internal/` (per UAC Citadel Architecture rule). 4 hits
        across 1 file (`04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`).
  - [x] `(UTS)` alias → `(UTL)` (unified-trading-services rename completed). 2 hits across 2 files.
  - [x] `unified-feature-calculator-library` → `unified-trading-library` (UFCL archived 2026-05-08; verified Q4
        resolution; `BaseFeatureServiceV2` migrated into UTL). 24 hits across 13 .md files + 1 .svg
        (WORKSPACE_MANIFEST_DAG.svg). **ALSO** removed stale entry from `workspace-manifest.json:2163`
        `reuses_from_cefi` list — flagged in commit body.
  - [x] `unified-trading-codex/` path prefix → `unified-trading-pm/codex/`. 178 hits across 113 .md files + 8 .sh + 1
        .py file (test_event_logging.py).

  **Removed-providers list correction**:
  - [x] `02-data/venue-availability.md` — removed Pyth from "Removed Venues" deleted-providers row + added new "Pyth —
        UNBANNED 2026-05-06 (Solana-only)" paragraph documenting Hermes + PythNet usage for LST yields
        (jitoSOL/mSOL/bSOL). Other chains continue using Chainlink. Per CLAUDE.md "Pyth — UNBANNED 2026-05-06" rule.
  - [x] `02-data/availability-manifest-and-data-status.md` — verified "Removed bookmakers: Smarkets / Betdaq / OddsJam"
        against current UAC. **Audit conclusion**: accurate as documented; no active venue tables list these. No update
        required.

  **Project ID placeholder leakage**:
  - [x] `05-infrastructure/README.md` — test-project → central-element-323112 (3 substitutions).
  - [x] `05-infrastructure/auth-setup.md` — test-project → central-element-323112 (~20 substitutions).
  - [x] `05-infrastructure/library-setup-checklist.md` — preserves `or "test-project"` fallback strings (legitimate code
        defaults); other prod-looking refs replaced.
  - [x] `05-infrastructure/ucs-docker-image-issues.md` — test-project → central-element-323112 (2 substitutions). Total
        25 substitutions across 4 files.

  **MTDS phantom-audit script naming**:
  - [x] `02-data/sports-schema-paths.md` — file deleted by Phase D.2; skip per plan instructions.

  **Acceptance**: workspace-wide grep in codex/ returns 0 hits for the 5 renamed patterns (verified post-sweep).
  venue-availability.md "Removed Venues" no longer contains Pyth. workspace-manifest.json no longer references
  unified-feature-calculator-library.

### Phase B.4 — Stub-doc cleanup (06-coding-standards) — PARALLEL — P2 — TRIAGED 2026-05-08 (all 12 KEEP, expansion deferred to B.4-bis)

- [x] [SCRIPT] P2. 12 stub docs in `06-coding-standards/` under 500 bytes triaged. **Workspace-wide grep audit** of
      incoming references found that EVERY stub is cited as the canonical SSOT by at least one `.cursor/rules/*.mdc`
      file via a `CODEX: 06-coding-standards/<stub>.md` pointer (e.g. `test-quality-standards.mdc:12` cites
      `testing.md`; `service-structure-standards.mdc:12` cites `service-structure-standards.md`;
      `architecture/thin-adapters.mdc:12` cites `thin-adapters-pattern.md`). Disposition: **all 12 KEEP** as forwarder
      stubs. Deletion would break cursor-rules' CODEX pointers without simultaneously rewriting them; that rewrite is
      out of scope for B.4 (would touch ~15 cursor-rules files + the codex 00-SSOT-INDEX + ssot-reference-mapping +
      MASTER_READINESS_LIVE_DEFI_2026_05_23.md). Expansion (replacing the "see README.md" pointer with substantive
      content) is the right path forward and is deferred to a follow-up phase, since each stub's expansion needs
      domain-aware content the per-file canonical home (README.md) doesn't yet break out as standalone sections.

  **Per-stub disposition** (all KEEP — every stub has incoming refs that treat it as canonical SSOT):
  - [x] `accurate-codebase-analysis.md` (482 B) — KEEP. Cited by `.cursor/rules/core/accurate-codebase-analysis.mdc`.
  - [x] `audit-remediation-guide.md` (528 B) — KEEP. Cited by `.cursor/rules/workflow/audit-remediation-strategy.mdc`.
  - [x] `code-cleanup-deslop.md` (477 B) — KEEP. Cited by `.cursor/rules/ui/ui-smoke-tests-and-deslop.mdc`.
  - [x] `config-types.md` (468 B) — KEEP. Cited by `.cursor/rules/config/config-store-usage.mdc` +
        `unified-trading-system-ui/context/CONFIG_REFERENCE.md`.
  - [x] `contribution-guide.md` (474 B) — KEEP. Cited by `.cursor/rules/core/codex-maintenance.mdc` +
        `unified-trading-system-ui/context/codex/README.md`.
  - [x] `cursor-rules-system.md` (475 B) — KEEP. Cited by `.cursor/rules/README.md` + 3 other rules.
  - [x] `file-splitting-guide.md` (476 B) — KEEP. Cited by `.cursor/rules/quality-gates/code-quality-limits.mdc:12`.
  - [x] `sub-agent-workflow.md` (506 B) — KEEP. Cited by `.cursor/rules/core/sub-agent-workflow-standard.mdc:20` +
        `parallel-agent-execution.mdc:12`.
  - [x] `testing.md` (527 B) — KEEP. Cited by `.cursor/rules/testing/test-quality-standards.mdc:12+70` +
        `core/gcp-auth-in-tests.mdc:90` (with deep-link anchors!) + `codex/00-SSOT-INDEX.md:196` +
        `10-audit/ssot-reference-mapping.md:77`. **Highest-leverage expansion target.**
  - [x] `thin-adapters-pattern.md` (507 B) — KEEP. Cited by `.cursor/rules/architecture/thin-adapters.mdc:12`.
  - [x] `token-optimization.md` (474 B) — KEEP. Cited by `.cursor/rules/core/token-optimization.mdc`.
  - [x] `service-structure-standards.md` (513 B / 13 lines) — KEEP. Cited by
        `.cursor/rules/architecture/service-structure-standards.mdc:12` +
        `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md:116`. Per audit C7 the content was meant to live in
        README; the stub stays as forwarder until the README breaks out a service-structure section.

  **No incoming-ref rewrites.** Decision rule per plan body: "If the stub describes a real concern with no canonical
  home elsewhere: leave it (mark as KEEP in your report) and note in the plan flip body that it needs expansion in a
  future phase." Each stub points at a real canonical home (README.md or similar) that DOES exist, but the cursor-rules
  CODEX pointers expect to land on the stub itself, so the forwarder shape is what makes the cross-reference contract
  work today. **DEFERRED**: Phase B.4-bis (greenfield item) — expand the highest-leverage stubs (`testing.md` first
  since it has deep-link anchors `#mocking-get_secret_client-in-unit-tests-canonical-pattern` +
  `#gcp-authentication-in-tests-standard` that cursor-rules deep-link into) to substantive standalone SSOTs. Order
  candidates by incoming-ref count: testing (4) > service-structure-standards (3) > sub-agent-workflow (2) > others.

  **Acceptance status**: original acceptance criterion "no codex doc under 500 bytes" remains UNMET; the 12 stubs are
  intentional forwarders with incoming SSOT-pointer contracts that require expansion (not deletion) to clear. Acceptance
  is moved to B.4-bis when expansion lands.

### Phase B.5 — SOURCE_COVERAGE_START dedup — PARALLEL — P2 — SHIPPED

- [x] [SCRIPT] P2. UAC `unified_api_contracts.sports.SOURCE_COVERAGE_START` is the canonical SSOT. Codex docs duplicate
      the values in 4 places. **SHIPPED 2026-05-08** — added canonical literal-values table to availability-manifest doc
      (under § "Source coverage start dates (canonical) — `SOURCE_COVERAGE_START` SSOT", new sub-section between
      Sparseness and Data Freshness); cross-linked from sports-data-source-coverage-matrix.md (§2.6 odds_api line),
      mtds-data-source-coverage-matrix.md (top-of-file Cross-refs block), and pipeline-coverage-matrix.md (both SPORTS
      tables — instruments-service §1 + MTDS §2). Verified via grep: only one doc enumerates the literal dates
      (`api_football=2018-01-01`, `footystats=2019-01-01`, `understat=2015-01-16`, `transfermarkt=2019-01-01`,
      `open_meteo=2019-03-02`, `odds_api=2020-06-06`, `soccer_football_info=2020-01-01` override, `api_football`
      per-fixture=2020-06-06 override). `sports-schema-paths.md` already deleted in Phase D.2 (PM@e641f3f1).

  **Files to update**:
  - [x] `02-data/availability-manifest-and-data-status.md` — canonical literal-values table added (§ Source coverage
        start dates (canonical)).
  - [x] `02-data/sports-data-source-coverage-matrix.md:219` — explicit `SOURCE_COVERAGE_START 2020-06-06` replaced with
        cross-link to availability-manifest § Source coverage start dates.
  - [x] `02-data/sports-schema-paths.md:163-172` — N/A, doc deleted in Phase D.2.
  - [x] `02-data/mtds-data-source-coverage-matrix.md` — cross-link added in top-of-file Cross-refs block (UAC SSOT +
        codex literal-values mirror callout).
  - [x] `02-data/pipeline-coverage-matrix.md` — both SPORTS tables (instruments-service §1, MTDS §2) replaced with
        cross-link blockquotes pointing at the canonical table.
  - [x] All consumer docs: cite via cross-link, never redeclare values.

  **Acceptance**: only ONE codex doc enumerates the literal `SOURCE_COVERAGE_START` values; all others link to it. UAC
  code remains the runtime SSOT. **MET**.

---

## LAYER C — Easy consolidations (parallel; just-shipped docs that fold cleanly)

### Phase C.1 — Delete `05-infrastructure/cloud-agnostic-migration.md` stub — PARALLEL — P1 — SHIPPED

- [x] [SCRIPT] P1. The 05-infrastructure version is 501 bytes redirecting to
      `04-architecture/cloud-agnostic-migration.md`. Delete the stub; redirect incoming refs. **SHIPPED 2026-05-08**
      (PM@1e33b423 deletion + 05-infrastructure/README.md:171 already updated to point at 04-architecture in same
      commit).

  **Implementation**:
  - [x] `git rm codex/05-infrastructure/cloud-agnostic-migration.md`.
  - [x] Update `codex/05-infrastructure/README.md:171` (and any other incoming refs in 05-infra) to point at
        `04-architecture/cloud-agnostic-migration.md`.
  - [x] Workspace-wide grep `codex/05-infrastructure/cloud-agnostic-migration.md` → rewrite all refs (PM-internal refs
        verified; sibling-repo refs in deployment-service/terraform/ point at `unified-trading-codex/...` which is a
        sibling-repo path, out of scope for PM).

  **Acceptance**: stub deleted; no broken links.

### Phase C.2 — Fold `deployment-ui-environment-tiers.md` into `deployment-ui-architecture.md` — PARALLEL — P1 — SHIPPED

- [x] [SCRIPT] P1. The new `deployment-ui-environment-tiers.md` (4K, shipped today) duplicates env-resolution-by-domain
      content already at `deployment-ui-architecture.md:117-141`. Plus the Tier 0/1/2/3 naming conflicts with
      `runtime-tiers-and-deployment.md` T0–T6. **SHIPPED 2026-05-08** (PM@2818b6b9 deletion; fold-in already present in
      deployment-ui-architecture.md per `EnvironmentTier` (DEV/STAGING/PROD) section + dev-mode subsection).

  **Implementation**:
  - [x] Move the hostname → port routing detail (lines 24-31 of environment-tiers) into `deployment-ui-architecture.md`.
  - [x] Move the Tier 0/1/2 vs Tier 3 distinction (lines 16-21) into `deployment-ui-architecture.md` BUT rename axis to
        use UAC `EnvironmentTier` (DEV/STAGING/PROD) instead of the conflicting "Tier N" naming.
  - [x] `git rm codex/05-infrastructure/deployment-ui-environment-tiers.md`.
  - [x] Update incoming refs: `14-playbooks/authentication/firebase-local.md` (if it references the env-tiers doc), the
        NEW docs from PM@9d873547 that cited it.

  **Acceptance**: doc deleted; deployment-ui-architecture.md is the single SSOT for deployment-UI tier model.

### Phase C.3 — Fold `launcher-script-consolidation-2026-05-07.md` into `launcher-script-ssot.md` — PARALLEL — P1 — SHIPPED

- [x] [SCRIPT] P1. The migration-tracker doc is dated; once the 30 ad-hoc launchers finish migrating, the tracker
      becomes obsolete. The launcher-script-ssot.md already has a "Migration in flight (2026-05-07)" section that
      captures the same data at higher level. **SHIPPED 2026-05-08** (PM@6a6308b3 — per-launcher migration table folded
      into launcher-script-ssot.md § "Migration in flight (2026-05-07)" under new sub-headings; tracker git rm'd; plan
      reference rewritten in launcher_scripts_consolidation_into_deployment_service_2026_05_07.md).

  **Implementation**:
  - [x] Append the migration table from `launcher-script-consolidation-2026-05-07.md` § "Migration table" into
        `launcher-script-ssot.md` § "Migration in flight".
  - [x] `git rm codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md`.
  - [x] Update incoming refs (workspace-wide grep — only PM-internal refs found, all rewritten).

  **Acceptance**: launcher SSOT doc has the full migration table; tracker deleted.

---

## LAYER D — Medium consolidations (sequential or partly-parallel; coordinate cross-doc refs)

### Phase D.1 — data-status-drilldown duplicate merge — PARALLEL — P1 — SHIPPED 2026-05-08

- [x] [SCRIPT] P1. Merge `data-status-drilldown.md` (215L) + `data-status-drilldown-hierarchy.md` (105L) into a single
      doc. **SHIPPED 2026-05-08** — content merged into single SSOT (PM@c418979d bundled the merge into a foreign-agent
      commit per foot-gun #1; the work landed correctly: 270 inserts in `codex/02-data/data-status-drilldown.md` + 118
      deletes from `codex/02-data/data-status-drilldown-hierarchy.md` at PM@f58bc8a9; cli-convention.md ref rewrite
      bundled into PM@06e13ce2).

  **Target shape** (`data-status-drilldown.md`) — DELIVERED:
  - [x] §1 Overview / API surface (covers per-shard `ShardDetailModal` + hierarchical `HierarchicalShardDrilldown`).
  - [x] §2 Per-asset_group depth table (from -hierarchy.md, including consolidated `feature_family` rows + the
        `pipeline_mode` outermost-partition callout).
  - [x] §3 Shard-class matrix (from -drilldown.md, including DeFi composite venue convention + venue-specific column
        rendering).
  - [x] §4 ShardDetailModal endpoint contract (from -drilldown.md, including write-time validation modes + UI flow per
        category + download semantics + schema coverage gate).
  - [x] §5 Hierarchical drill endpoint (from -hierarchy.md, including backend + frontend + per-leaf download +
        Deploy-Missing surgical recovery + failure modes the drill-down catches).
  - [x] §6 Cross-references.

  **Cross-doc references**:
  - [x] `06-coding-standards/cli-convention.md` — rewritten to merged doc (bundled into PM@06e13ce2).
  - [x] `06-coding-standards/test-coverage-data-status.md` — rewritten to merged doc.
  - [x] `06-coding-standards/feature-service-pattern.md` — rewritten to merged doc.
  - [x] `04-architecture/features-service-architecture.md` (2 refs) — rewritten to merged doc.
  - [x] `00-SSOT-INDEX.md` — sibling-doc citation in pipeline-mode-partition row updated.
  - [x] Active plans `deploy_missing_auto_launch_2026_05_07.md` + `gcs_migration_bundle_pipeline_mode_2026_05_08.md` —
        forward-looking refs updated. Historical commit-evidence citations in
        `data_status_drilldown_shard_atom_alignment_2026_05_07.md`,
        `_SESSION_HANDOFF_drilldown_launcher_ssot_2026_05_07.md`, `ml_and_features_master_2026_05_07.md`, and
        `features_repo_consolidation_2026_05_08.md` Phase 8B/9 historical sub-points left as historical record per
        Findings Triage Discipline (those reference the file as it existed at the cited commit).
  - [x] `02-data/availability-manifest-and-data-status.md` + `02-data/deployment-ui-drilldown-depth-audit.md` +
        `04-architecture/data-flow-map.md` + `09-strategy/cross-cutting/dart-manual-trade-spec.md` — verified: no direct
        `-hierarchy.md` link in body. No edit needed.

  **Implementation** — DONE:
  - [x] Created merged file content.
  - [x] `git rm codex/02-data/data-status-drilldown-hierarchy.md` (bundled into PM@f58bc8a9).
  - [x] Workspace-wide grep — all forward-looking refs rewritten.

  **Acceptance**: only one drill-down doc; no broken links in active codex docs.

### Phase D.2 — Sports 5-doc consolidation → 3 docs — PARALLEL — P1 — SHIPPED 2026-05-08

- [x] [SCRIPT] P1. Per audit C3, sports docs collapse 5 → 3. SHIPPED 2026-05-08 (PM commit forthcoming).

  **Keep**:
  - `02-data/sports-data-source-coverage-matrix.md` (coverage SSOT — unchanged).
  - `02-data/sports-scheduling-and-sharding.md` (timing SSOT — unchanged but body needs the multi-axis-banner
    reconciliation per audit 1c, see Phase D.3 below).
  - `02-data/sports-adapter-dependency-order.md` (T0/T1 dependency graph — unchanged).

  **Delete**:
  - [x] `02-data/sports-data-migration.md` — DELETED. Superseded by `per-asset-group-bucket-layouts.md` (sports
        section) + reality of shipped sports buckets. Post-plan banner (2026-05-06) already disclaimed it; no unique
        content needed migration.
  - [x] `02-data/sports-schema-paths.md` — DELETED. GCS path SSOT lives in UAC `unified_api_contracts.sports.gcs_paths`
        (`candidate_parquet_paths`, `SPORTS_DATA_TYPE_TO_FOLDER`, `SPORTS_DATA_TYPE_LAYOUT`); SOURCE_COVERAGE_START
        table already documented in CLAUDE.md "Sports source coverage windows" workspace rule +
        `availability-manifest-and-data-status.md`; phantom-audit recipe lives in
        `availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe".

  **Cross-doc references rewritten** (6 files):
  - [x] `04-architecture/sports-integration-plan.md` — both refs (line 410 `Migration scripts:` + line 495
        `## References`) repointed to `02-data/per-asset-group-bucket-layouts.md` + UAC `gcs_paths` SSOT.
  - [x] `14-playbooks/backfill-completion-playbook.md:166` — repointed to UAC `gcs_paths` SSOT + phantom-audit recipe in
        `availability-manifest-and-data-status.md`.
  - [x] `05-infrastructure/vm-tarball-deployment.md:402` — manifest consolidator cross-ref repointed to
        `availability-manifest-and-data-status.md`.
  - [x] `02-data/data-lineage-MTDS-features-ml.md:160` — sports paths cross-ref repointed to UAC `gcs_paths` SSOT +
        `per-asset-group-bucket-layouts.md`.
  - [x] `02-data/README.md:253-254` — both file entries removed from directory listing.
  - [x] `02-data/sports-data-source-coverage-matrix.md:33` — `sports-data-migration.md` cross-ref replaced with
        `per-asset-group-bucket-layouts.md`.

  Archived plans (`plans/archive/sports_*`) intentionally NOT modified — frozen historical state per workspace rule.
  Auto-generated `codex/14-playbooks/_generated/scope-manifest.json` will refresh on next codex QG.

  **Acceptance**: only 3 sports docs in `02-data/` (verified `ls codex/02-data/sports-*.md` returns
  `sports-adapter-dependency-order.md`, `sports-data-source-coverage-matrix.md`, `sports-scheduling-and-sharding.md`);
  workspace-wide grep `sports-data-migration\|sports-schema-paths` returns zero hits in `codex/` or `plans/active/`
  (excluding this plan and the auto-generated scope-manifest).

### Phase D.3 — Multi-axis correction body-text reconciliation — SEQUENTIAL after A.1, A.2 — P0

- [x] [SCRIPT] P0. **Resolved 2026-05-08 (Q1)**: banner is canonical. `fixture_id` (sports) and `market_id` (prediction)
      are row-level columns for UI display, NOT hive-partition shard axes. Verified independently via: (i) writegate
      plan line 98 (`fixture_id (display-axis only)`), (ii) writegate plan line 395 (`SPORTS_FIXTURE_CLUSTERS` is
      per-fixture aggregate cluster — clusters live inside files), and (iii) GCS reality at
      `gs://instruments-store-sports-central-element-323112/sports_reference/by_date/day=2025-10-15/entity=footystats_odds/`
      where the deepest partition is `league=BRASILEIRAO/`, with no `fixture=...` subdirectory anywhere.

      **No data migration needed.** Disk shape already matches banner. This phase
      is a doc-only sweep removing stale body text in 02-data.

      **SHIPPED 2026-05-08** — body-text sweep landed (3 of 4 swept files; sports-scheduling-and-sharding.md was already
      cleaned up at HEAD by parallel agent earlier in the session). My intended commit was absorbed by parallel agent's
      commit `c2bc6cd5 docs(codex): Phase B.3 — workspace-wide stale repo/provider reference sweep` — same hunks,
      different commit message (foot-gun #3 incident: parallel agent's prek/prettier hook ran during my commit cycle and
      bundled my staged D.3 hunks into their B.3 commit). Verify via
      `git show c2bc6cd5 -- codex/02-data/availability-manifest-and-data-status.md codex/02-data/per-category-bucket-layouts.md codex/02-data/prediction-schema-paths.md`.
      Acceptance grep on the 4 swept files returns zero true-positive stale shard-axis claims (remaining hits are
      corrective body text explicitly stating "row-level column INSIDE parquet, NOT a hive-partition shard axis").
      CLAUDE.md "Per-asset-group shard-key matrix" remains workspace SSOT. Spillover stale claims in
      `04-architecture/shard-level-failure-isolation.md` / `05-infrastructure/deployment-clusters-live-vs-batch.md` /
      `02-data/shard-granularity-cefi.md` / `02-data/partitioning.md` / `POST_PLAN_REALITY_2026_05_06.md` are out of D.3
      scope (those docs already carry the multi-axis-correction banner; cleanup deferred to adjacent codex_refactor
      phases or follow-up).

  **Files to sweep**:
  - [x] `02-data/sports-scheduling-and-sharding.md` § 1 — already cleaned up at HEAD before D.3 started (parallel agent
        landed it earlier this session); body now states banner-canonical
        `(asset_group=sports, source, data_type, league_id, day)` with `fixture_id` as row-level column +
        cluster-validation cross-link.
  - [x] `02-data/availability-manifest-and-data-status.md` (sports paragraph + predictions-migration paragraph) —
        replaced both stale shard-atom claims (sports + prediction) with banner-canonical shapes; cluster-validation
        cross-link via `SPORTS_FIXTURE_CLUSTERS` + `PREDICTION_GROUPS` (commit `c2bc6cd5`).
  - [x] `02-data/per-asset-group-bucket-layouts.md` (renamed in Phase E.4; lines 71 + 73 — table sibling rows) —
        replaced both SPORTS-post-target and PREDICTION-post-target rows with banner-canonical paths (no `fixture=` / no
        `{market_id}.parquet`) + row-level-column body text (commit `c2bc6cd5`).
  - [x] `02-data/prediction-schema-paths.md` § Target (post-Plan A) — replaced `market_id` shard-axis claim with
        row-level column; per-`canonical_question_group` cluster validation expects N market_ids per cadence (HOURLY=24
        / DAILY=1 / ELECTION=1) INSIDE the file (commit `c2bc6cd5`).

  **Acceptance**: workspace-wide grep `(asset_group=sports.*fixture_id.*day)` and
  `(asset_group=prediction.*market_id.*day)` shard-axis claims return zero hits in codex/. CLAUDE.md "Per-asset-group
  shard-key matrix" remains the workspace SSOT.

### Phase D.4 — Custody triplet → custody-providers.md SSOT — SEQUENTIAL after A.1 — P1

- [x] [SCRIPT] P1. Per audit C5, fold `copper-custody-integration.md` (245L) and `ceffu-custody-integration.md` (95L
      stub) into `custody-providers.md` (193L, protocol SSOT) as per-provider §s. **DONE 2026-05-08 (PM@c4330d9d)** —
      custody-providers.md grew to 486L with §1 protocol + §2.1 Mock / §2.2 LocalKey / §2.3 Copper / §2.4 CEFFU
      (PLANNED) + §3 coverage matrix + §4 mode matrix. 7 cross-refs rewritten across codex/04-architecture/ +
      codex/10-audit/ + plans/active/.

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

### Phase D.5 — Validation/error chapter merge → `validation-and-errors.md` — SEQUENTIAL after A.2 — P1 — SHIPPED 2026-05-08

- [x] [SCRIPT] P1. Per audit C6, merge `error-handling.md` (181L) + `validation-patterns.md` (241L) +
      `schema-validation.md` (83L) into `validation-and-errors.md`. Eliminates write-gate-quartet duplication +
      error-class naming drift (`SchemaMismatchError` vs `SchemaValidationFailedError`). **SHIPPED 2026-05-08
      PM@e8ef9671.**

  **Target shape** (`06-coding-standards/validation-and-errors.md` — DONE):
  - [x] §1 4-category empty-output decision (incl. path D zero-activity-bar from CLAUDE.md operator directive
        2026-05-07).
  - [x] §2 Write-gate quartet (single SSOT, deduplicated).
  - [x] §3 Per-row schema validation.
  - [x] §4 available_at + LookaheadBias (split: §4.1 stamping, §4.2 features enforcement, §4.3 reader enforcement —
        SchemaMismatchError canonical, SchemaValidationFailedError alias removed).
  - [x] §5 InstrumentsWriteGate.
  - [x] §6 Per-shard try/except pattern.

  **Cross-doc references** — DONE:
  - [x] `02-data/shard-granularity-cefi.md` — 2 refs rewritten.
  - [x] `02-data/sports-scheduling-and-sharding.md` — 2 refs rewritten.
  - [x] `04-architecture/shard-level-failure-isolation.md` — 3 refs rewritten.
  - [x] `06-coding-standards/timestamp-ordering.md` — 1 ref rewritten.
  - [x] `06-coding-standards/retry-pattern.md` — 1 ref rewritten.
  - [x] `06-coding-standards/service-hardening-checklist.md` — 1 ref rewritten.
  - [x] `06-coding-standards/README.md` — Document Map row absorbed by parallel agent's `3da88fed`.
  - [x] `02-data/prediction-schema-paths.md` — absorbed by parallel agent's `3da88fed`.
  - [x] `02-data/partitioning.md` — absorbed by parallel agent's `3da88fed`.
  - [x] `05-infrastructure/deployment-clusters-live-vs-batch.md` — absorbed by parallel agent's `3da88fed`.
  - [x] `POST_PLAN_REALITY_2026_05_06.md` — absorbed by parallel agent's `3da88fed`.
  - [x] `plans/active/hard_schema_enforcement_2026_05_08.md` — codex-update todo rewired to point at
        `validation-and-errors.md` (absorbed by parallel agent's commits).

  **Implementation** — DONE:
  - [x] Create merged file (492L final).
  - [x] `git rm codex/06-coding-standards/error-handling.md` (deletion landed via parallel agent's `3da88fed` B.2+B.3
        sweep that absorbed the rm).
  - [x] `git rm codex/06-coding-standards/validation-patterns.md` (same).
  - [x] `git rm codex/06-coding-standards/schema-validation.md` (same).
  - [x] Update all cross-doc refs (PM@e8ef9671 for the 6 in-this-commit; rest absorbed by parallel agent).

  **Acceptance** — MET: single validation/errors doc; no broken links; one error-class hierarchy per concern
  (`SchemaMismatchError` is canonical name, alias removed).

### Phase D.6 — batch-live principle merge → `batch-live-architecture.md` — SEQUENTIAL after A.5, A.6 — P1

- [x] [SCRIPT] P1. Per audit C9, merge `batch-live-pipeline.md` (195L) + `batch-live-symmetry.md` (263L) into
      `batch-live-architecture.md`. Major overlap on principle. **DONE 2026-05-08 (PM@dcd49f24)** —
      batch-live-architecture.md created at 460L with all 10 sections (Principle / 4 seams / anti-drift guards / service
      audit matrix / matching engine + book matchers / strategy alpha vs execution alpha / sports-specific notes /
      anti-patterns fixed / instruments-live exception / references). 23 cross-refs rewritten across codex/02-data/ +
      codex/04-architecture/ + codex/05-infrastructure/ + codex/10-audit/ + codex/14-playbooks/ + plans/active/ +
      plans/epics/.

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

### Phase D.7 — Service-standards consolidation → README chapter — SEQUENTIAL — P1 — SHIPPED 2026-05-08

- [x] [SCRIPT] P1. Per audit C7, fold D1-D5 progression from `service-hardening-checklist.md` into
      `06-coding-standards/README.md § Production Readiness Checklist`. **SHIPPED 2026-05-08 PM@237319f2.**

  **Implementation** — DONE:
  - [x] `service-structure-standards.md` left as previously-shipped forwarder stub (B.4 audit decided KEEP all 12 stubs;
        not deleted — the original todo's `git rm` instruction superseded by B.4).
  - [x] Move D1-D5 content from `service-hardening-checklist.md` into `README.md` § Production Readiness Checklist §
        Service Hardening: D1→D5 progression. Includes: gate matrix (D1-D5), per-gate checklists (D1 ruff/D2
        basedpyright/D3 unit tests/D4 health endpoints/D5 integration+QG), automated scan commands, QG structure
        verification table, tier promotion criteria.
  - [x] Convert `service-hardening-checklist.md` to a redirect stub (operator preference: stub vs `git rm` because
        cursor-rules + master_to_live_defi plan + master readiness doc reference the path; redirect keeps it
        resolvable).
  - [x] Update incoming refs in service-hardening-checklist.md cross-references block to point to README anchor +
        validation-and-errors.md (replaces the stale `error-handling.md` ref).

  **Acceptance** — MET: README is the single SSOT for service hardening (D1-D5 + tier matrix + QG verification);
  service-hardening-checklist.md is a 1-paragraph redirect stub.

### Phase D.8 — Path-layout 4-doc consolidation — SEQUENTIAL after A.1 — P1 — SHIPPED 2026-05-08 PM@a1e134c4

- [x] [SCRIPT] P1. Per audit C2, sub-tree restructure for path layouts. **SHIPPED 2026-05-08 PM@a1e134c4** — three
      sibling docs collapsed to short SSOT pointers; `per-category-bucket-layouts.md` retained as the canonical
      path-layout SSOT (filename rename to `per-asset-group-bucket-layouts.md` shipped in Phase E.4).

  **Keep as SSOT** — DONE:
  - [x] `02-data/per-asset-group-bucket-layouts.md` (renamed in Phase E.4 from `per-category-bucket-layouts.md`) —
        path-shape divergences SSOT.

  **Collapse to pointers** — DONE (PM@a1e134c4):
  - [x] `02-data/partitioning.md` § Path Templates by Service → 17-row per-service table replaced with 6-line "see SSOT"
        pointer.
  - [x] `02-data/hive-schema-compatibility.md` § Partitioning Strategy → positional vs hive-style restatement replaced
        with pointer; retained unique parquet+BQ rationale (cost-optimised external-table queries, partition pruning,
        hive-style is what BigQuery external readers expect).
  - [x] `02-data/pipeline-coverage-matrix.md` § "0. Bucket Topology" → per-bucket-pattern table + hive-key drift
        sub-table replaced with pointer; retained per-service coverage matrix focus + manifest index files /
        consolidator topology below.

  **Cross-doc references**:
  - [x] `02-data/instrument-pipeline-defi.md:215-216`, `02-data/data-lineage-MTDS-features-ml.md:19,146`,
        `02-data/chart-candle-delivery-flow.md:20-22`, `02-data/prediction-schema-paths.md`,
        `09-strategy/architecture-v2/category-instrument-coverage.md`,
        `14-playbooks/instruments-live/t1-audit-discrepancy.md` — verified: refs still resolve correctly via chained
        pointer (the collapsed docs cite per-category-bucket-layouts.md). Not rewritten per Findings Triage Discipline —
        over-fix territory; chained pointer is one extra hop, not a broken link. Future Phase E.4 rename will require a
        workspace-wide grep + rewrite anyway.

  **Operator decision still required**: filename rename per-category-bucket-layouts.md →
  per-asset-group-bucket-layouts.md per S3 + asset_group vocabulary rule. Tracked in Phase E.4.

  **Acceptance**: per-category-bucket-layouts.md is the single path-layout SSOT; the three collapsed docs cite it via
  SSOT pointers.

---

## LAYER E — Heavy structural moves (sequential; operator-decision required per move)

### Phase E.1 — Topology 7-doc cluster reorganisation — SEQUENTIAL after Layer A — P1

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

### Phase E.2 — 14-playbooks split into 3 directories — SEQUENTIAL after E.3 — P1

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

### Phase E.3 — 09-strategy cross-cutting collapse — PARALLEL — P1 — SHIPPED 2026-05-08

- [x] [DOC] P2. Per audit S2, two parallel `cross-cutting/` directories in 09-strategy. **SHIPPED 2026-05-08**:
  - **Commit 1** (PM@4d23b431): moved 8 v2-content files (`dart-manual-trade-spec`, `operational-modes-matrix`,
    `pnl-attribution`, `prediction-markets`, `leverage-and-volatility`, `restaking-reward-economics`, `reward-lifecycle`,
    `rate-impact-model`) into `architecture-v2/cross-cutting/`. Internal-path adjustments (depth +1):
    `../../04-architecture/X` → `../../../04-architecture/X`; `../../../plans/X` → `../../../../plans/X`;
    `../strategy-summary.md` → `../../strategy-summary.md`; `../architecture-v2/README.md` → `../README.md` (sibling-up);
    `../architecture-v2/archetypes/X` → `../archetypes/X`; `../cross-cutting/share-classes.md` →
    `../../_archived_pre_v2/cross-cutting/share-classes.md` (correct broken target — was broken pre-move);
    `../../02-data/X` → `../../../02-data/X` (prediction-markets only). 16 active docs / plans cross-ref-rewritten
    (62 replacements). plans/archive/ untouched per workspace rule.
  - **Commit 2** (PM@b38cb485): renamed remaining `09-strategy/cross-cutting/` → `09-strategy/operational/` (5 files:
    onboarding-checklist, client-onboarding, client-strategy-config, instrument-filtering,
    prediction-markets-codification-gaps). Same depth — no internal path adjustments. Sibling reference inside
    prediction-markets-codification-gaps.md updated to `../architecture-v2/cross-cutting/prediction-markets.md`. 5
    active docs / plans cross-ref-rewritten (10 replacements).

### Phase E.4 — Filename rename: per-category-bucket-layouts → per-asset-group-bucket-layouts — PARALLEL — P1

- [ ] [DOC] P1 (BLOCKED on operator approval). Per audit S3 + workspace asset_group vocabulary rule. The file body uses
      both `category` and `asset_group` inconsistently. Rename + body-sweep.

### Phase E.5 — Audit-style doc moves out of 06-coding-standards — PARALLEL — P1 — SHIPPED 2026-05-08

- [x] [DOC] P2. Move `cod-deadlock-verification-report.md` (Feb 2026 dated, stale) + `orphan-audit.md` (UI architecture
      concern) out of `06-coding-standards/`. **SHIPPED 2026-05-08**:
  - `cod-deadlock-verification-report.md` → `plans/archive/audits/cod-deadlock-verification-report-2026-02-13.md` —
    rename absorbed into PM@2677b3ae rename bundle; archive status block + successor-doc pointer
    (`codex/06-coding-standards/quality-gates.md`) added in PM@25f109e8.
  - `orphan-audit.md` → `codex/04-architecture/orphan-audit.md` (UI architecture policy belongs in 04-architecture/, not
    coding-standards canon). Rename + cross-doc rewrites (3 refs in
    `09-strategy/architecture-v2/strategy-catalogue-3tier.md`
    - 2 refs in `08-workflows/prospect-questionnaire-flow.md` including a previously-broken sibling-relative link)
      absorbed into PM@018b4958 (parallel agent's Phase E.3 commit bundle — staged set was hijacked by foreign `git add`
      seconds before commit fired; content shipped correctly under their commit hash).

---

## LAYER F — Cosmetic + index updates (parallel; ship anytime)

### Phase F.1 — quality-gates.md ToC — PARALLEL — P2 — SHIPPED 2026-05-08 (PM@28ca221b)

- [x] [SCRIPT] P2. `quality-gates.md` is 1667 lines / 73K with no top-of-file ToC. (PM@28ca221b)

  **Implementation**:
  - [x] Add numbered ToC at top linking to STEP 5.X anchors. 26-section ToC enumerating every `## ` heading with anchor
        slugs; positioned immediately after `# Quality Gates` H1, before TL;DR. (PM@28ca221b)
  - [x] Cross-reference STEP numbers from CLAUDE.md (5.10/5.11/5.22/5.34/5.61/5.62/5.64/5.66) into a single "QG STEP
        cross-reference" table. Table has 4 columns: STEP, topic, this-doc anchor, canonical enforcement file
        (`scripts/quality-gates-base/base-service.sh` or `base-library.sh`), CLAUDE.md cross-ref. Steps without a
        dedicated section here (5.34/5.61/5.62/5.64/5.66) point at the enforcement file directly. (PM@28ca221b)

### Phase F.2 — UI infra rename + collapse — PARALLEL — P2

- [ ] [SCRIPT] P2. `UI-FUNCTIONALITY-REQUIREMENTS.md` (32K) + `UI-DEPENDENCY-MATRIX.md` (15K) — all-caps filenames are
      unique to this dir. Rename to lowercase-kebab. Bulk of content is "ARCHIVED — reference only" notes; consider
      collapsing to one `ui-archive-reference.md`.

### Phase F.3 — Severity tier glossary — PARALLEL — P1

- [x] [SCRIPT] P1. Per audit (14-playbooks A): codex enum (CRITICAL/HIGH/WARN/INFO) vs PagerDuty (P0/P1/P2/P3) vs
      `AlertSeverity.WARN` (Python). Add a single glossary table at top of `14-playbooks/alerting/README.md` (or
      `03-observability/alerting.md`) mapping all three. Other docs cite. **SHIPPED 2026-05-08** — glossary added to
      `14-playbooks/alerting/README.md` § "Severity glossary" mapping all three vocabularies (UAC `AlertSeverity`
      CRITICAL/HIGH/WARN/INFO ↔ PagerDuty P0/P1/P2/P3 ↔ routing ↔ time-to-ack ↔ examples). Cross-links added in
      `03-observability/alerting.md` (replaces inline severity table),
      `14-playbooks/alerting/pagerduty-escalation-policy.md` (top banner + reshape "Severity tiers" section to defer to
      glossary; preserves the operational P0-vs-P1 sub-distinction inside CRITICAL), and
      `14-playbooks/alerting/threshold-tuning.md` (top banner citing glossary from the WARNING-only deploy step).

### Phase F.4 — `aws_migration_cost_analysis_2026_05_07.md` extract + archive — PARALLEL — P2 — SHIPPED

- [x] [SCRIPT] P2. 53K research-grade doc, recommendation paragraph explicitly superseded. Extract per-resource cost
      tables → `aws-migration-cost-snapshot-2026-05-07.md` (~10-15K). Move full original to `plans/archive/` or
      `codex/15-audits/`. **SHIPPED 2026-05-08** (PM@166c7f72 — per-resource cost tables extracted to
      `codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`; original git mv'd to
      `plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md` with status block linking back to the
      snapshot + dual-cloud decision plan; 4 incoming refs in active plans rewritten — \_AUDIT_dependency_graph,
      aws_migration_defi_first, master_to_live_defi, work_split_2026_05_08_ikenna).

### Phase F.5 — README.md cleanup (05-infrastructure) — PARALLEL — P2 — SHIPPED

- [x] [SCRIPT] P2. `05-infrastructure/README.md:171,176-177,184-185` link to non-existent files (`terraform.md`,
      `ci-cd.md`, `docker.md`, `versioning-rollback.md`, `batch/README.md`, `live/README.md`). Either create or remove.
      **SHIPPED 2026-05-08** (PM@631ee9ea — verified all 6 files non-existent via ls; removed the 6 dead-link rows from
      the "Related Documents" table in 05-infrastructure/README.md; kept the 9 valid rows).

### Phase F.6 — 09-strategy READMEs refresh — PARALLEL — P1 — SHIPPED 2026-05-08 (no-op; A.4 covered)

- [x] [SCRIPT] P1. Ensure `09-strategy/README.md` and `09-strategy/architecture-v2/README.md` reflect 9/53 throughout.
      **Verified 2026-05-08** — A.4 already shipped the refresh: README.md:13 cites `9 families × 53 archetypes`,
      architecture-v2/README.md:22-23 cite `1 of 9 families` and `1 of 53 archetypes`, and the `Total: 53 archetypes`
      summary at line 122. The single remaining `18 archetypes` mention (line 105) is a historical-changelog reference
      ("2026-04-17 baseline shipped 18 archetypes; the Phase 9 expansion (2026-04-25) added 35 more for full coverage")
      which is contextually correct and must NOT be rewritten. No edits required; phase was a verification pass on top
      of A.4.

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
- [x] `codex/06-coding-standards/validation-and-errors.md` (Phase D.5, replaces 3) — SHIPPED 2026-05-08 PM@e8ef9671

DELETED codex docs by this plan:

- [x] `codex/05-infrastructure/cloud-agnostic-migration.md` (Phase C.1, stub SHIPPED 2026-05-08 PM@1e33b423)
- [x] `codex/05-infrastructure/deployment-ui-environment-tiers.md` (Phase C.2 SHIPPED 2026-05-08 PM@2818b6b9)
- [x] `codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md` (Phase C.3 SHIPPED 2026-05-08 PM@6a6308b3)
- [x] `codex/02-data/data-status-drilldown-hierarchy.md` (Phase D.1 SHIPPED 2026-05-08 — bundled into PM@f58bc8a9)
- [x] `codex/02-data/sports-data-migration.md` (Phase D.2 SHIPPED 2026-05-08)
- [x] `codex/02-data/sports-schema-paths.md` (Phase D.2 SHIPPED 2026-05-08)
- [ ] `codex/04-architecture/copper-custody-integration.md` (Phase D.4)
- [ ] `codex/04-architecture/ceffu-custody-integration.md` (Phase D.4)
- [x] `codex/06-coding-standards/error-handling.md` (Phase D.5 SHIPPED 2026-05-08 — deletion absorbed into parallel
      agent's `3da88fed`)
- [x] `codex/06-coding-standards/validation-patterns.md` (Phase D.5 SHIPPED 2026-05-08 — same)
- [x] `codex/06-coding-standards/schema-validation.md` (Phase D.5 SHIPPED 2026-05-08 — same)
- [ ] `codex/06-coding-standards/service-structure-standards.md` (Phase D.7 — KEPT as forwarder stub per B.4 audit; not
      deleted)
- [ ] `codex/04-architecture/batch-live-pipeline.md` (Phase D.6, replaced)
- [ ] `codex/04-architecture/batch-live-symmetry.md` (Phase D.6, replaced)
- [ ] Some/all 12 stub files in `codex/06-coding-standards/` (Phase B.4, per-file decision)
- [ ] Topology 7-doc cluster (Phase E.1, IF approved): `RUNTIME_TOPOLOGY_DECISIONS.md`, `TIER-ARCHITECTURE.md`,
      `service-family-scope.md`, `deployment-topology-diagrams.md`, `pipeline-service-layers.md`,
      `api-services-cluster.md`, `PROTOCOL-INJECTION.md`.

---

## Open questions — ALL RESOLVED 2026-05-08

### Q1 — Multi-axis correction: banner is canonical (Option A — row-level columns)

**Status**: ✅ RESOLVED 2026-05-08.

Three independent sources of truth all agree:

1. **writegate plan line 98**:
   `data_status_multi_axis_shard_propagation_2026_05_06.md ... Read/display side: fixture_id (display-axis only) + job_id manifest columns`.
2. **writegate plan line 395**: greenfield `SPORTS_FIXTURE_CLUSTERS` is a per-fixture aggregate **cluster** (bookmakers
   per fixture) — clusters live inside files, not as separate folders.
3. **GCS reality** (verified 2026-05-08 against
   `gs://instruments-store-sports-central-element-323112/sports_reference/by_date/day=2025-10-15/entity=footystats_odds/`):
   actual on-disk structure is per-(day, entity, league) parquet with no `fixture=...` subdirectory anywhere. fixture_id
   is a row-level column inside the file.

**No data migration is needed.** Disk reality already matches Option A. Phase D.3 is purely a codex doc-sweep removing
stale body text in ~5 02-data docs that contradict the banner.

Same logic applies to prediction `market_id`: it's a row-level column, with cluster validation per
`(canonical_question_group, day)` enforcing expected market_ids inside the file (HOURLY=24 / DAILY=1 / ELECTION=1 —
already documented in `09-strategy/cross-cutting/prediction-markets.md` per PM@d212f4e6).

### Q2 — POST_PLAN_BANNER sweep cadence: per-directory (7 commits)

**Status**: ✅ RESOLVED 2026-05-08 (operator).

Per-directory cadence: one commit per codex sub-directory. Smaller revert surface if any commit breaks; cleaner per-dir
audit history.

### Q3 — Heavy structural moves: ship all pre-May-23

**Status**: ✅ RESOLVED 2026-05-08 (operator).

E.1 (topology 7-doc cluster), E.2 (14-playbooks split), E.3 (09-strategy cross-cutting collapse), E.4 (per-asset-group
filename rename), E.5 (audit-doc moves out of 06-cs) all ship pre-May-23. The "BLOCKED on operator approval" tag on each
Layer E phase has been removed; phases proceed as PARALLEL or SEQUENTIAL P1 as noted per phase.

### Q4 — `unified-feature-calculator-library` is archived (moot point)

**Status**: ✅ RESOLVED 2026-05-08.

Verification:

- Repo does NOT exist as a sibling under workspace root.
- `archive/unified-feature-calculator-library/` is the only remaining copy.
- Zero non-archive imports of `unified_feature_calculator_library` exist (workspace-wide grep confirmed; only internal
  test imports inside the archive).
- All `BaseFeatureServiceV2` imports across the workspace come from `unified-trading-library` (UTL) — meaning
  `BaseFeatureServiceV2` was migrated into UTL when the library was archived.
- `workspace-manifest.json:2163` still mentions it (stale entry — flagged for cleanup in Phase B.3).

**Resolution**: Phase B.3 sweep adds `unified-feature-calculator-library` → `unified-trading-library` rewrites for every
codex doc reference. Stale workspace-manifest.json entry is also removed as a side-effect (tracked in Phase B.3
acceptance criteria).

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
