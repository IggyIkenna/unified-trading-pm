---
title: Ikenna's daily work-split — 2026-05-11 (Phase 1 code-freeze push to 2026-05-15 freeze gate)
type: coordination-doc
status: active
created: 2026-05-11
deadline: 2026-05-15
horizon: 4-day cycle
companion_to: plans/active/work_split_2026_05_11_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Ikenna's daily work-split — 2026-05-11

> **Companion (Harsh side):** [`work_split_2026_05_11_harsh.md`](work_split_2026_05_11_harsh.md). Cross-side handshakes
> are mirrored in both files; edit one, mirror the other.

## Why this split exists today

We are 4 days from the **Phase 1 code-freeze gate (2026-05-15)** of
[`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md). After
that gate fires, Phase 2 (one-shot physical migrations 2026-05-15→05-19: manifest v8 schema bump + GCS bundled
migration + AWS DeFi-first parity + cross-asset rescan) and Phase 3 (resume backfills 2026-05-19→05-23) run in sequence.
**Every Phase 1 blocker that misses the gate forces a re-migration tax** — millions of parquets walked twice, manifest
rewritten twice, May-23 live-DeFi cutover at risk.

This cycle's Ikenna scope: drive the **cross-cutting / multi-repo / governance / human-approval** half of Phase 1 to
done. Harsh covers features-repo-consolidation + per-adapter mechanical wiring + workspace-wide audits in
[`work_split_2026_05_11_harsh.md`](work_split_2026_05_11_harsh.md).

**Rolled forward from yesterday's stale splits** (`work_split_2026_05_08_ikenna.md` was never archived per the EOD rule
— flag for sweep; this plan supersedes scope-wise but does NOT auto-archive the old file): writegate slice (b) schema
work, available_at completion umbrella ownership, live-pipeline Phase 4-5 design-ahead, master plan refresh.

## Working model

**Model A — 5 thematic slots** (slot 1 = main orchestrator + on-call, slots 2-5 = thematic implementers, slots 6-8 held
in reserve for mid-cycle spawn). Phase 1 work is pre-decided via the 7 blocker plans, so the dynamic Model B (1-main +
dynamic spawn) overhead isn't justified. **Tabs run to their done-definitions, not to 2026-05-15** — agents finish
faster than humans; whoever closes their scope picks up carryover from the same-side reserve list (or cross-side helps
with explicit handshake).

## Today's slot assignments

> **Per-tab worktree model**
> ([`codex/05-infrastructure/per-tab-worktrees.md`](../../codex/05-infrastructure/per-tab-worktrees.md)). Each slot is a
> permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/ikennaigboaka/<N>`. Slot count: 8 already
> provisioned (per `setup-tab-worktrees.sh --list` 2026-05-11). Before any slot reassignment from yesterday's theme, run
> `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>`.

| Slot | Theme                                                                                 | Plan-of-record                                                                                                                 | AI-day budget |
| ---- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------- |
| 1    | main orchestrator + on-call governance                                                | [LEDGER](../../ikenna_orchestrator/LEDGER.md) + Phase 1 freeze-gate audit + master plan refresh + cross-plan banner sweep      | continuous    |
| 2    | **CRITICAL PATH** — writegate slice (b) Phase 5.1-5.7 (UAC v8 schema columns)         | [writegate_honest_coverage_endtoend_2026_05_06.md](writegate_honest_coverage_endtoend_2026_05_06.md) slice (b)                 | ~5            |
| 3    | available_at completion Phase 0 (bar boundary contract) + Phase 4-5 audits            | [available_at_lookahead_bias_completion_2026_05_08.md](available_at_lookahead_bias_completion_2026_05_08.md)                   | ~4            |
| 4    | live pipeline Phase 4-5 design-ahead (gated) + Phase 11 deployment-UI live tab design | [live_pipeline_mtds_mdps_features_2026_05_08.md](live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4-5 + 11                | ~3            |
| 5    | DeFi Phase 1.E sequencing readiness + cross-plan coordination                         | [code_freeze_migrate_backfill_sequencing_2026_05_10.md](code_freeze_migrate_backfill_sequencing_2026_05_10.md) Phase 1.E audit | ~3            |
| 6    | (reserve) — spawn for mid-cycle finding                                               | —                                                                                                                              | —             |
| 7    | (reserve) — spawn for mid-cycle finding                                               | —                                                                                                                              | —             |
| 8    | (reserve) — spawn for mid-cycle finding                                               | —                                                                                                                              | —             |

**Total active scope: ~15 AI-days across 4 thematic slots over a 4-day cycle.** Beefier than thin per CLAUDE.md sizing —
under-utilisation is fine, mid-cycle collision is not.

## Tab registry (per-tab full brief)

### Slot 1 — main orchestrator + on-call governance

- **Identity**: this session (Ikenna's main orchestrator agent, slot 1 worktree at `.tabs/1/`).
- **Scope**:
  - **P0**. Daily ledger sweep at start: read `ikenna_orchestrator/_agent_pings.md` + `plans/active/_agent_pings.md`,
    triage 🟡 BLOCKED Qs >24h, ack STARTED pings, verify DONE pings.
  - **P0**. Phase 1 freeze-gate audit cadence: at every shippable unit landing on slots 2-5, re-check the 8 freeze-gate
    bullets in
    [code_freeze_migrate_backfill_sequencing_2026_05_10.md:135-148](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L135-L148);
    update [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group D + F + G readiness columns.
  - **P0**. Cross-plan coordination banner sweep: ensure `🟡 IN-FLIGHT REFACTOR — code-freeze sequencing` banners are
    present on the 9 plans listed in
    [code_freeze:328-339](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L328-L339) — most landed PM@1b9e6451
    yesterday, verify still present + add any missed.
  - **P1**. Stale work-split sweep: archive `work_split_2026_05_08_*.md` (3 days old, never archived per EOD rule) to
    `plans/archive/`. Roll-forward any open items into today's tab scopes.
  - **P1**. Operator Q&A dispatch: route 🟡 BLOCKED Qs from slots 2-5 to operator chat; route operator decisions back to
    plan-of-record `## Open questions` sections.
- **Plan-of-record**: this file + [LEDGER](../../ikenna_orchestrator/LEDGER.md) +
  [code_freeze](code_freeze_migrate_backfill_sequencing_2026_05_10.md).
- **Repos owned (collision boundary)**: `unified-trading-pm/plans/active/*` (work-split + master + code_freeze) +
  `unified-trading-pm/ikenna_orchestrator/*` + `unified-trading-pm/plans/active/_agent_pings.md` (cross-side ledger
  curation). Does NOT touch UAC / UTL / service repos.
- **Read-first**: CLAUDE.md § "Daily Work-Split Process" + § "Findings Triage Discipline" + § "Cross-Plan Coordination
  Banners".
- **Sub-agent fan-out**: minimal — main agent does NOT implement; spawn Explore agents for status probes.
- **Collision risk**: slot 1 edits the work-split + LEDGER + master plan; slot 5 edits `code_freeze` audit table; agree
  surgical `git add -p` on shared files.
- **Done-definition**:
  - ✅ Ledger sweep done at start of cycle + every 4-6 hours while operator active.
  - ✅ Master plan readiness columns reflect today's shipments at EOD.
  - ✅ Cross-plan banners verified present on 9 plans.
  - ✅ Yesterday's stale work-splits archived.
- **Full-execution criterion**:
  - ✅ Phase 1 freeze-gate bullets audited at EOD; status published to operator chat.
    - **What ran**: live read of UAC/UTL/PM commits + manifest spot-check + per-tab DONE blocks.
    - **Verification**: `git log --oneline origin/live-defi-rollout --since "2026-05-11 00:00"` + LEDGER tab statuses.

### Slot 2 — Writegate slice (b) Phase 5.1-5.7 (UAC v8 schema columns) — CRITICAL PATH

- **Identity**: `ikenna-writegate-slice-b-tab` (slot 2 worktree at `.tabs/2/`).
- **Scope** (per [writegate plan §5.1-5.7](writegate_honest_coverage_endtoend_2026_05_06.md), the v8 schema column
  declaration the Phase 2.1 manifest atomic rename consumes):
  - **P0 Phase 5.1** — Declare UAC manifest v8 schema columns: `service_emission_state`, `pipeline_mode`,
    `feature_family`. Update
    [`unified_api_contracts/canonical/manifest/`](../../../unified-api-contracts/unified_api_contracts/canonical/manifest/)
    schema definitions; types frozen + dataclass-style + StrEnum for closed sets.
  - **P0 Phase 5.2** — Add `manifest_completeness` UTL helper computing
    `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` per drilldown level. SSOT for
    the 3 derived %s
    ([`measure-honest-coverage.py` is the per-data_type measurement script](../../codex/02-data/availability-manifest-and-data-status.md);
    the helper is the in-process compute).
  - **P0 Phase 5.3** — Wire `manifest_completeness` into deployment-api `/api/data-status/leaf-stats` endpoint (already
    shipped @3b0477a per [LEDGER 2026-05-08 evening](../../ikenna_orchestrator/LEDGER.md) — extend with the new helper
    output as additional fields).
  - **P0 Phase 5.4** — Add `service_emission_state` column to deployment-ui DataStatusTab venue summary line (extends
    @8f630a6 / @621f0b3 per LEDGER); badge stack rendering for the 4 ServiceEmissionPolicy enum values.
  - **P1 Phase 5.5** — Codex SSOT update: extend
    [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
    "v8 schema" section; document the 3 new columns + their write-time semantics.
  - **P1 Phase 5.6** — Add CLAUDE.md key-rule entry under "Availability manifest v5 (honest-coverage)" extending it to
    v8 (`service_emission_state` + `pipeline_mode` + `feature_family`).
  - **P1 Phase 5.7** — UAC + UTL + deployment-api QG green workspace-wide; basedpyright + ruff clean.
- **Plan-of-record**:
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) slice (b).
- **Repos owned**: `unified-api-contracts` (canonical/manifest schema) + `unified-trading-library`
  (manifest_completeness helper) + `deployment-api` (leaf-stats endpoint extension) + `deployment-ui` (DataStatusTab
  rendering) + PM (codex doc + plan flips + CLAUDE.md key rule).
- **Read-first**: CLAUDE.md § "Availability manifest v5 (honest-coverage)" + § "Honest absence vs fake placeholders" + §
  "Cluster validation MANDATORY at record_captured".
- **Sub-agent fan-out**: send 1 message with 4 parallel `Task` blocks at boot:
  1. UAC v8 schema column declarations (Phase 5.1).
  2. UTL `manifest_completeness` helper + tests (Phase 5.2).
  3. deployment-api leaf-stats endpoint extension + tests (Phase 5.3).
  4. deployment-ui DataStatusTab rendering + tests (Phase 5.4). Then serially: codex doc (5.5) + CLAUDE.md (5.6) +
     workspace QG sweep (5.7).
- **Collision risk**:
  - **vs slot 4 (live-pipeline)**: slot 4 declares `pipeline_mode` enum facade in UAC; slot 2 declares the manifest
    column type that uses it. **Hard sync**: slot 4 ships UAC `PipelineMode` facade FIRST (already shipped UAC@b643c9a
    per LEDGER 2026-05-08 evening); slot 2 imports + uses it. Verify still on origin before starting.
  - **vs Harsh slot 3 (wave3x)**: Track A `HALF_DAY_SESSIONS` already shipped UAC@bdc84ed per available_at memory
    2026-05-08; Tracks B/C/D/E don't touch manifest schema, no collision.
  - **vs Harsh slot 6 (workspace QG sweep)**: Phase 5.7 hands off to Harsh QG sweep at ship; coordinate via cross-side
    ping ledger.
- **Done-definition**:
  - ✅ All 3 UAC v8 columns declared + dataclass + StrEnum types + 100% test coverage.
  - ✅ UTL `manifest_completeness` helper + unit tests + property tests.
  - ✅ deployment-api endpoint extension green; existing 7-test suite still passes.
  - ✅ deployment-ui DataStatusTab renders new badges; component tests green.
  - ✅ Codex doc + CLAUDE.md updated; UAC+UTL+deployment-\* QG green.
- **Full-execution criterion**:
  - ✅ A live deployment-api `/api/data-status/leaf-stats` query against a real GCS-mounted manifest returns the v8
    columns + completeness percentages.
    - **What ran**: deployment-api smoke against `gs://central-element-323112-availability-index/`.
    - **Verification**: HTTP 200 + JSON contains `service_emission_state` / `pipeline_mode` / `feature_family` keys with
      non-null values; completeness percentages sum-check matches manifest counts.
  - ✅ A v8 manifest atomic rename rehearsal (dry-run only — no write) shows zero schema-validation failures.

### Slot 3 — Available_at completion Phase 0 + Phase 4-5 audits

- **Identity**: `ikenna-available-at-tab` (slot 3 worktree at `.tabs/3/`).
- **Scope** (per
  [available_at_lookahead_bias_completion_2026_05_08.md](available_at_lookahead_bias_completion_2026_05_08.md)):
  - **P0 Phase 0** — Foundational: 5 sub-todos (bar boundary contract in UAC + `compute_bar_close_boundary` helper in
    UTL + MDPS bar-boundary audit + reconciler + write-gate enforcement + QG check). Blocker for Phase 1 per-asset-group
    adapter wiring downstream (Harsh slot 4 picks up the per-adapter halves once Phase 0 lands).
  - **P0 Phase 4** — `FEATURE_REQUIRED_INPUTS` expansion in UAC across sports / cefi / tradfi / predictions / defi.
    Currently 10 defi entries only ([line 324-343](available_at_lookahead_bias_completion_2026_05_08.md#L324-L343));
    expand to ~50-80 entries spanning all 5 asset_groups. Drives the LookaheadBiasError gate.
  - **P0 Phase 5** — `AVAILABILITY_AT_SEMANTICS` workspace-wide audit. Read every UAC source-priority entry; verify each
    `(source, data_type)` has an `AVAILABILITY_AT_SEMANTICS` declaration; add missing entries.
  - **P1 Phase 8** — QG static check (CI step that walks every `record_captured(` callsite and asserts an `available_at`
    stamping helper is invoked in the surrounding scope; second CI step asserts every features-\* compute has the
    LookaheadBiasError strict-mode gate in its inner loop).
- **Plan-of-record**:
  [`available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md).
- **Repos owned**: `unified-api-contracts` (FEATURE_REQUIRED_INPUTS + AVAILABILITY_AT_SEMANTICS + bar boundary) +
  `unified-trading-library` (compute_bar_close_boundary + QG steps) + `market-data-processing-service` (bar audit +
  reconciler) + PM (plan flips + CLAUDE.md updates).
- **Read-first**: CLAUDE.md § "Live = batch — same data, same fields, same timing semantics" + § "Honest absence vs fake
  placeholders" + § "Shard-granularity SSOT" / "available_at is a write-time column, never derived at read-time".
- **Sub-agent fan-out**: 3 parallel at boot:
  1. UAC bar boundary contract + UTL helper + tests (Phase 0).
  2. UAC FEATURE_REQUIRED_INPUTS expansion across 5 asset_groups (Phase 4).
  3. Workspace-wide AVAILABILITY_AT_SEMANTICS audit + missing entry adds (Phase 5). Then MDPS bar audit + reconciler
     serially (Phase 0 finishing).
- **Collision risk**:
  - **vs Harsh slot 4 (per-adapter wiring)**: Harsh's slot 4 finishes Phase 1 per-asset-group adapter stamping AFTER
    Phase 0 lands. **Hard sync**: ping `_agent_pings.md` cross-side when Phase 0 lands; Harsh slot 4 then unblocks.
  - **vs Harsh slot 3 (wave3x Track E)**: Track E sports stamping cascade is folded into available_at Phase 1 per
    [wave3x:12-20](wave3x_residual_ssots_2026_05_08.md#L12-L20). Harsh slot 3 ships the per-source helpers; slot 3
    integrates them into AVAILABILITY_AT_SEMANTICS audit. Coordinate via plan-of-record.
- **Done-definition**:
  - ✅ Phase 0 5 sub-todos shipped + UTL+MDPS QG green.
  - ✅ FEATURE_REQUIRED_INPUTS expanded to ≥50 entries across 5 asset_groups.
  - ✅ AVAILABILITY_AT_SEMANTICS audit complete; missing entries added.
  - ✅ Cross-side ping landed when Phase 0 done so Harsh slot 4 can start per-adapter wiring.
- **Full-execution criterion**:
  - ✅ A LookaheadBiasError strict-mode pytest run against a representative features-\* calculator fixture (with a
    deliberate lookahead-bias row injected) raises the error and FAILS the test correctly.
    - **What ran**: `cd features-onchain-service && bash scripts/quality-gates.sh` against fixture.
    - **Verification**: pytest output shows `LookaheadBiasError` raised with correct row context.

### Slot 4 — Live pipeline Phase 4-5 design-ahead + Phase 11 deployment-UI live tab design

- **Identity**: `ikenna-live-pipeline-tab` (slot 4 worktree at `.tabs/4/`).
- **Scope** (per [live_pipeline_mtds_mdps_features_2026_05_08.md](live_pipeline_mtds_mdps_features_2026_05_08.md); Phase
  4-5 are gated on Harsh's features-consolidation Phase 7 — design-ahead while gated):
  - **P0 Phase 4 design** — Draft MDPS streaming aggregation contract (`MDPSStreamingAggregator` class signature +
    UTC-aligned candle boundaries + watermark + grace + replay handoff). Land as design-only commit + UTL stubs; full
    implementation lands once Harsh slot 2 ships features-consolidation Phase 7.
  - **P0 Phase 5 design** — Draft features-service asset-scoped streaming contract (per-asset_group flavor +
    cross-cutting flavor); land as design-only stub + UTL helper signatures.
  - **P0 Phase 11 design** — Draft deployment-UI live tab schema: `/api/live-status` endpoint contract + frontend
    component scaffold + integration with existing Health-API extension (Phase 8 already shipped).
  - **P1 Phase 14** — Codex SSOT updates: extend
    [`codex/05-infrastructure/live-pipeline-architecture.md`](../../codex/05-infrastructure/live-pipeline-architecture.md)
    with Phase 4-5 streaming aggregation design + Phase 11 UI surface.
- **Plan-of-record**: [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md)
  Phases 4-5 + 11 + 14.
- **Repos owned**: `unified-api-contracts` (live-streaming contract types) + `unified-trading-library` (aggregator
  signatures + UTL stubs) + `deployment-api` (live-status endpoint) + `deployment-ui` (live tab scaffold) + PM (codex
  doc updates + plan flips).
- **Read-first**: CLAUDE.md § "ARCHITECTURE 2026-05-08 — Live pipeline" + § "Batch = Live: Unified Pipeline
  Architecture"
  - the live-pipeline plan body + memory entry on Tab 2 LIVE-PIPELINE 2026-05-08 (4 UTL primitives shipped).
- **Sub-agent fan-out**: 3 parallel at boot:
  1. Phase 4 design + UTL stub.
  2. Phase 5 design + UTL helper signatures.
  3. Phase 11 endpoint + UI scaffold. Then codex SSOT updates serially.
- **Collision risk**:
  - **vs Harsh slot 2 (features-consolidation)**: Harsh slot 2 ships Phase 7 (consolidated features-service deployable);
    slot 4's Phase 5 design imports the consolidated package. **Hard sync**: cross-side ping when Harsh Phase 7 lands;
    slot 4 then promotes design-only commits to full implementation in next-cycle work-split.
  - **vs Harsh slot 5 (live-pipeline service wiring)**: Harsh slot 5 picks up Phase 3-5 service wiring once
    features-consolidation unblocks. **Sync**: slot 4 designs the contract; Harsh slot 5 implements per-service
    consumers. Coordinate via plan-of-record `## Open questions`.
- **Done-definition**:
  - ✅ Phase 4 + 5 contract types declared in UAC + UTL stubs landed (compile-clean, type-clean, no implementation).
  - ✅ Phase 11 endpoint contract + UI scaffold; smoke renders empty state correctly.
  - ✅ Codex SSOT extended with Phase 4-5-11 designs.
- **Full-execution criterion**:
  - ✅ A `from unified_trading_library.streaming import MDPSStreamingAggregator` import resolves + the class signature
    matches the design contract (instantiation may raise NotImplementedError since this is design-ahead).
    - **What ran**:
      `python -c "from unified_trading_library.streaming import MDPSStreamingAggregator; help(MDPSStreamingAggregator)"`.
    - **Verification**: signature matches plan body Phase 4 contract.

### Slot 5 — DeFi Phase 1.E sequencing readiness + cross-plan coordination

- **Identity**: `ikenna-defi-phase-1e-tab` (slot 5 worktree at `.tabs/5/`).
- **Scope** (per [code_freeze:120-126](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L120-L126), the Phase 1.E
  P0 DeFi-specific code-complete blockers):
  - **P0** — Audit [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md): is
    chain genesis + protocol launch + token metadata final state declared? If not, stub the SSOT in UAC + raise to
    operator chat for triage.
  - **P0** — Audit
    [`arbitrage_price_dispersion_finalisation_2026_05_09.md`](arbitrage_price_dispersion_finalisation_2026_05_09.md): is
    the canonical_question_group for ARBITRAGE_PRICE_DISPERSION final? Per anti-sequencing rule
    ([code_freeze:303](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L303)) any new canonical group landing post
    Phase 2.2 = second rekey walk.
  - **P0** — Audit [`cme_polymarket_arb_2026_05_08.md`](cme_polymarket_arb_2026_05_08.md): is
    `InstrumentType.EVENT_CONTRACT` enum value in v8 schema declaration? Per
    [code_freeze:304](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L304) the new enum MUST land in v8 (slot 2
    owns the schema; slot 5 owns the enum value addition).
  - **P0** — Audit [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md):
    are recursive-borrow archetype definitions code-shipped? Per defi_master Phase 9 dependency.
  - **P1** — Refresh anti-sequencing audit table at
    [code_freeze:298-313](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L298-L313) with today's status of every
    plan listed; add new plans created during today's cycle.
  - **P1** — Cross-plan coordination banner sweep (helper to slot 1 P0 banner verification): walk the 9 banner targets
    and add any banners still missing.
- **Plan-of-record**:
  [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) Phase
  1.E + anti-sequencing audit + [`defi_master_2026_05_07.md`](defi_master_2026_05_07.md) for cross-reference.
- **Repos owned**: PM (audit findings + plan flips + banner adds) + `unified-api-contracts` (any enum additions per
  Phase 1.E P0 findings — `EVENT_CONTRACT`, new canonical_question_group entries, etc.).
- **Read-first**: CLAUDE.md § "Plans must capture full codebase impact upfront" + § "Citadel-Grade Planning Standards" +
  § "Cross-Plan Coordination Banners".
- **Sub-agent fan-out**: 4 parallel Explore reads at boot (one per Phase 1.E plan); synthesis + audit table refresh
  serially. Banner sweep last.
- **Collision risk**:
  - **vs slot 1**: both edit master plan + code_freeze audit table. Surgical `git add -p` mandatory; slot 1 owns "freeze
    gate audit" subsection, slot 5 owns "anti-sequencing audit table."
  - **vs slot 2**: any UAC enum additions land in same UAC files slot 2 edits for v8 schema. Coordinate: slot 5's
    additions go in `unified_api_contracts/canonical/instruments/` (separate from `manifest/`), no overlap.
- **Done-definition**:
  - ✅ All 4 Phase 1.E plans audited; status captured in audit table.
  - ✅ Any UAC enum additions for Phase 1.E P0 findings shipped or routed to operator chat.
  - ✅ Anti-sequencing audit table refreshed.
  - ✅ Banner sweep complete (9 plans verified or banners added).
- **Full-execution criterion**:
  - ✅ Audit table reflects current state; reviewers can trust it as the SSOT for "what Phase 1.E work is still open."
    - **What ran**: per-plan grep for shipped commits + per-plan checkbox state read + UAC enum grep.
    - **Verification**: zero `unknown` cells in the audit table; every row has a current status + decision.

## Cross-tab handshakes (within Ikenna side)

- **Slot 4 → Slot 2**: UAC `PipelineMode` facade already shipped UAC@b643c9a per LEDGER; slot 2 imports it for v8
  schema. Verify on origin before slot 2 boot.
- **Slot 3 → Slot 2 (P1)**: any new manifest column declarations from slot 3's Phase 0 bar boundary contract should be
  routed through slot 2's v8 schema PR (single SSOT). Coordinate via plan-of-record.
- **Slot 5 → Slot 2 (P0)**: any new `InstrumentType` enum value (`EVENT_CONTRACT`) lands in v8 schema declaration. Slot
  5 ships the enum; slot 2 references it in the manifest column declaration.
- **Slot 1 → Slots 2-5**: continuous Q&A dispatch + freeze-gate audit cadence. Every shippable unit on slots 2-5 → slot
  1 re-audits gate.

## Cross-side handshakes (Ikenna ↔ Harsh — mirrored in [harsh's split](work_split_2026_05_11_harsh.md))

- **Hard-gate: Harsh slot 2 (features-consolidation Phase 7) → Ikenna slot 4 (live-pipeline Phase 4-5)**. Harsh ships
  Phase 7 (consolidated features-service deployable, deadline 2026-05-13). Ikenna slot 4 promotes design-ahead commits
  to full implementation in next-cycle work-split. **Signal**: Harsh slot 2 cross-side ping in
  [`plans/active/_agent_pings.md`](_agent_pings.md) when Phase 7 lands.
- **Hard-gate: Ikenna slot 3 (available_at Phase 0) → Harsh slot 4 (per-adapter wiring)**. Ikenna ships Phase 0 bar
  boundary contract + UTL helper. Harsh slot 4 unblocks Phase 1 per-asset-group adapter stamping. **Signal**: Ikenna
  slot 3 cross-side ping when Phase 0 lands.
- **Hard-gate: Ikenna slot 2 (writegate v8 schema) → Harsh slot 6 (workspace QG sweep)**. Ikenna ships v8 columns; Harsh
  slot 6 runs the workspace-wide QG green check. **Signal**: Ikenna slot 2 cross-side ping when Phase 5.7 lands.
- **Coordinate: Ikenna slot 3 (AVAILABILITY_AT_SEMANTICS audit) ↔ Harsh slot 3 (Wave3x Track E sports stamping)**.
  Track E folded into available_at Phase 1 — Harsh ships per-source helpers, Ikenna integrates into
  AVAILABILITY_AT_SEMANTICS.
- **Banner-add: Ikenna slot 1 (banner sweep) → both sides**. Slot 1 ensures every plan that touches Phase 1 / Phase 2 /
  Phase 3 work has the cross-plan banner pointing back at code_freeze umbrella.

## Collision-risk callouts

| Files / dirs                                                          | Collision tabs                                                                             | Mitigation                                                                                            |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `unified-api-contracts/unified_api_contracts/canonical/manifest/*`    | slot 2 (v8 schema columns) + slot 4 (live-pipeline contract types may add manifest fields) | Slot 2 owns canonical manifest columns; slot 4 routes any manifest-touching contracts through slot 2. |
| `unified-api-contracts/unified_api_contracts/canonical/instruments/*` | slot 5 (EVENT_CONTRACT enum) + slot 3 (FEATURE_REQUIRED_INPUTS expansion may touch types)  | Slot 5 ships the enum; slot 3 references it. Surgical `git add -p`.                                   |
| `unified-trading-library/unified_trading_library/manifest/*`          | slot 2 (manifest_completeness helper) + slot 3 (compute_bar_close_boundary helper)         | Distinct file paths within manifest/; both can edit in parallel.                                      |
| `unified-trading-pm/plans/active/code_freeze_migrate_backfill_*.md`   | slot 1 (freeze-gate audit) + slot 5 (anti-sequencing audit)                                | Distinct sections; surgical `git add -p`. Or slot 1 commits first, slot 5 rebases.                    |
| `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md`   | slot 1 (Group D + F + G readiness columns) + slot 5 (banner adds)                          | Slot 1 owns the readiness table; slot 5 only adds top-of-file banner if missing.                      |
| `unified-trading-pm/cursor-configs/CLAUDE.md`                         | slot 2 (key-rule entry for v8 manifest)                                                    | Slot 2 sole writer this cycle; nobody else edits CLAUDE.md.                                           |
| `deployment-api/deployment_api/api/data_status/*`                     | slot 2 (leaf-stats endpoint) + slot 4 (live-status endpoint)                               | Distinct endpoint files; both can edit in parallel.                                                   |
| `deployment-ui/src/components/DataStatusTab/*`                        | slot 2 (badge rendering) + slot 4 (live tab scaffold for separate Live tab)                | Distinct component files; slot 4's Live tab is a NEW component, not edits to DataStatusTab.           |

**Per-slot worktree isolation** (per
[`codex/05-infrastructure/per-tab-worktrees.md`](../../codex/05-infrastructure/per-tab-worktrees.md)) makes cross-slot
races on `.git/index` unrepresentable; the table above is for SHARED-FILE-CONTENT collisions when slots push and pull
each other's commits.

## Spawn prompts (paste-ready into fresh Claude Code / Cursor tabs)

> **Operator usage**: open a fresh Cursor / Claude Code tab inside the slot N worktree
> (`cd ${WORKSPACE_ROOT}/.tabs/<N>/`), then paste the matching prompt. The agent reads the slot's plan-of-record +
> LEDGER bootstrap on its own.

### Slot 2 spawn prompt (writegate slice b — CRITICAL PATH)

```text
You are Tab 2 — a sub-agent spawned by Ikenna's main orchestrator agent (slot 1, a separate
Claude Code session on the SAME machine).

Your slot is 2. Your worktree is at ${WORKSPACE_ROOT}/.tabs/2/ on branch tab/ikennaigboaka/2.
All work happens INSIDE that worktree — opening Cursor / Claude Code there gives you an isolated
.git/index from every other slot. Today's theme for slot 2: writegate slice (b) Phase 5.1-5.7
(UAC v8 manifest schema columns) — CRITICAL PATH for the 2026-05-15 Phase 1 freeze gate.

BEFORE doing anything else, read in order:
  1. plans/active/work_split_2026_05_11_ikenna.md § "Slot 2 — Writegate slice (b) ..." — full task brief.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md — 3-tier isolation model.
  4. unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md — reconciliation
     protocol when your push surfaces a rebase conflict.
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  6. plans/active/writegate_honest_coverage_endtoend_2026_05_06.md — your plan-of-record.
  7. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella you serve.

Your agent-tag for ping-ledger entries: ikenna-writegate-slice-b-tab.

ORCHESTRATION RULES (full text in CLAUDE.md):
  1. Per-slot worktree — cross-slot races unrepresentable. WITHIN your slot, sub-agents you spawn
     share your worktree's .git/index, so pre-commit check (git status + git diff --cached --stat
     NO PATH ARG) still mandatory before EVERY commit. Use `git add -p` for shared files; never
     `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into writegate plan's `## Open questions` section
     (status 🟡 BLOCKED), append ping in ikenna_orchestrator/_agent_pings.md, continue with
     what you CAN do.
  3. Conditional push — per shippable unit: commit locally, fetch + check incoming, zero
     incoming → push, any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — checkbox flip + `<repo>@<sha>` evidence
     stamped in body, NOT batched at session end.
  5. Findings Triage Discipline (HARD RULE) — case-1-to-5 routing per CLAUDE.md.
  6. Cross-side ping mandatory when Phase 5.7 lands (workspace QG green) so Harsh slot 6 can
     start workspace QG sweep.

YOUR TASK: ship writegate slice (b) Phase 5.1-5.7 (UAC v8 manifest schema columns +
manifest_completeness UTL helper + deployment-api leaf-stats endpoint extension +
deployment-ui DataStatusTab badge rendering + codex SSOT update + CLAUDE.md key rule +
workspace QG green). Full task brief in this work-split § "Slot 2".

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push.
Final: append a "DONE-2026-05-11" block at the bottom of writegate plan body listing every
code + plan-flip commit sha. EOD-audit (per CLAUDE.md "Capture Discoveries As Plan
Todos Immediately" § "End-of-cycle audit clause"): every deferral in your final summary
MUST already be a `- [ ]` plan todo or a `**DEFERRED**` annotation in plans/active/. Run
`grep -n "<distinctive phrase>" plans/active/*.md plans/active/issues/*.md` per deferral
line — match → cite file:line in summary; no match → STOP, add the todo, push the flip,
then resume. Then go quiet — don't pick up new work autonomously.
```

### Slot 3 spawn prompt (available_at completion Phase 0 + Phase 4-5 audits)

```text
You are Tab 3 — a sub-agent spawned by Ikenna's main orchestrator agent (slot 1).

Your slot is 3. Your worktree is at ${WORKSPACE_ROOT}/.tabs/3/ on branch tab/ikennaigboaka/3.
Today's theme for slot 3: available_at completion Phase 0 (bar boundary contract) +
Phase 4 (FEATURE_REQUIRED_INPUTS expansion) + Phase 5 (AVAILABILITY_AT_SEMANTICS audit).

BEFORE doing anything else, read in order (same files as Slot 2 spawn prompt + your
plan-of-record):
  1. plans/active/work_split_2026_05_11_ikenna.md § "Slot 3 — Available_at ..." — full task brief.
  2-5. (same as slot 2: CLAUDE.md, per-tab-worktrees, plan-aware-merge, SUB_AGENT_MANDATORY_RULES).
  6. plans/active/available_at_lookahead_bias_completion_2026_05_08.md — your plan-of-record.
  7. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella you serve.

Your agent-tag for ping-ledger entries: ikenna-available-at-tab.

ORCHESTRATION RULES: same as slot 2 spawn prompt.

Cross-side ping mandatory when Phase 0 lands (bar boundary contract + UTL helper) so Harsh
slot 4 can start per-asset-group per-adapter wiring.

YOUR TASK: full task brief in this work-split § "Slot 3".

REPORT-BACK: same as slot 2 — per-shippable-unit commit+push+flip; final DONE-2026-05-11 block;
EOD-audit; then go quiet.
```

### Slot 4 spawn prompt (live pipeline Phase 4-5 design-ahead)

```text
You are Tab 4 — a sub-agent spawned by Ikenna's main orchestrator agent (slot 1).

Your slot is 4. Your worktree is at ${WORKSPACE_ROOT}/.tabs/4/ on branch tab/ikennaigboaka/4.
Today's theme for slot 4: live-pipeline Phase 4-5 design-ahead (gated on Harsh's
features-consolidation Phase 7) + Phase 11 deployment-UI live tab scaffold + Phase 14 codex
SSOT updates.

BEFORE doing anything else, read in order:
  1. plans/active/work_split_2026_05_11_ikenna.md § "Slot 4 — Live pipeline ..." — full task brief.
  2-5. (standard: CLAUDE.md, per-tab-worktrees, plan-aware-merge, SUB_AGENT_MANDATORY_RULES).
  6. plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md — your plan-of-record.
  7. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella.

Your agent-tag: ikenna-live-pipeline-tab.

ORCHESTRATION RULES: same as slot 2.

Hard-sync constraint: Phase 4-5 IMPLEMENTATION (not design) is BLOCKED until Harsh slot 2
ships features-consolidation Phase 7. While gated, ship DESIGN-ONLY commits (UAC contracts +
UTL stubs) so consumers can compile against the shape. When Harsh's cross-side ping lands
(Phase 7 done), promote design to implementation in the next-cycle work-split.

YOUR TASK: full task brief in this work-split § "Slot 4".

REPORT-BACK: same as slot 2.
```

### Slot 5 spawn prompt (DeFi Phase 1.E sequencing readiness)

```text
You are Tab 5 — a sub-agent spawned by Ikenna's main orchestrator agent (slot 1).

Your slot is 5. Your worktree is at ${WORKSPACE_ROOT}/.tabs/5/ on branch tab/ikennaigboaka/5.
Today's theme for slot 5: Phase 1.E DeFi sequencing readiness audit (defi_catalogue_chain_primitives
+ arbitrage_price_dispersion + cme_polymarket_arb + defi_recursive_borrow_archetypes) +
anti-sequencing audit table refresh + cross-plan banner sweep.

BEFORE doing anything else, read in order:
  1. plans/active/work_split_2026_05_11_ikenna.md § "Slot 5 — DeFi Phase 1.E ..." — full task brief.
  2-5. (standard).
  6. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — your plan-of-record.
  7. plans/active/defi_master_2026_05_07.md — DeFi domain umbrella for cross-reference.

Your agent-tag: ikenna-defi-phase-1e-tab.

ORCHESTRATION RULES: same as slot 2.

Per CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" HARD RULE: when auditing whether a
Phase 1.E feature ships, do NOT conclude "missing" from a literal grep of zero hits. Read
the consumer code + check for runtime-resolved patterns (registries, factories, regex
dispatch). Reference incident: Cluster 9 audit 2026-05-08 reported 4 features missing that
were already shipped via runtime-resolved patterns.

YOUR TASK: full task brief in this work-split § "Slot 5".

REPORT-BACK: same as slot 2.
```

## Daily sync points

- **Boot (operator opens fresh tabs)** — slot 1 reports state to operator; slots 2-5 boot independently and ack to
  operator chat.
- **Mid-cycle (every 4-6 hours while operator active)** — slot 1 polls intra-side ping ledger; reports tab statuses to
  operator chat; routes cross-side handshakes through `plans/active/_agent_pings.md`.
- **EOD checkpoint** — every active slot ships a DONE-2026-05-11 block in its plan-of-record body listing today's
  commits; slot 1 audits Phase 1 freeze-gate state + reports % gate items green.
- **Hard sync gates** (block downstream work until upstream ships):
  - Slot 4 → slot 2 (UAC PipelineMode facade — already shipped, verify on origin).
  - Slot 5 → slot 2 (EVENT_CONTRACT enum addition lands in v8 schema declaration).
  - Slot 3 → Harsh slot 4 (Phase 0 bar boundary lands; cross-side ping unlocks per-adapter wiring).
  - Harsh slot 2 → Ikenna slot 4 (features-consolidation Phase 7 lands; cross-side ping unlocks live-pipeline Phase 4-5
    implementation promotion).

## Defer post-deadline (out of scope this cycle)

These items are explicitly deferred behind the 2026-05-15 Phase 1 freeze gate and not picked up in this work-split:

- **writegate slice (c) Phase 6.1-6.9** — per-service rollout (8 service adapter migrations + sports match_end_time
  cascade). Scheduled 2026-05-13 but Phase 2 buffer is only 2 days; per
  [code_freeze:93](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L93) audit recommends NOT in scope for Phase 1
  freeze gate.
- **hard_schema_enforcement Phase 1** — `blocked_by: tradfi-master-2026-05-07` per its frontmatter; sequenced AFTER
  tradfi futures-expiry ships. Out of scope until tradfi unblocks (Harsh covers tradfi master ownership).
- **available_at Phase 1 (DeFi/TradFi/Predictions per-asset-group adapters)** — deferred to respective asset_group
  master plans (defi_master, tradfi_master, predictions_master) per
  [available_at_lookahead_bias_completion:250-278](available_at_lookahead_bias_completion_2026_05_08.md#L250-L278).
- **live-pipeline Phase 3 (MTDS websocket rollout) + Phase 6 (features cross-cutting) + Phase 13 (VM launchers) + Phase
  15 (full QG sweep)** — DEFERRED-AFTER-FEATURES-CONSOLIDATION per
  [code_freeze:1162-1165](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L1162-L1165). Harsh slot 5 picks up
  Phase 3-5 service wiring once features-consolidation Phase 7 unblocks; Phase 13/14/15 land in next-cycle.

## Composes with

- CLAUDE.md § "Daily Work-Split Process" — the canonical process this plan instantiates.
- CLAUDE.md § "Per-Tab Worktrees" — the 3-tier isolation model.
- CLAUDE.md § "Commit + Push + Flip Plan Checkboxes" — per-shippable-unit cadence + pre-commit check + scoreboard rule.
- CLAUDE.md § "Plans Run To Actual Completion, Not Smoke-Test Green" — every tab's done-definition has a Full-execution
  criterion.
- CLAUDE.md § "Cross-Plan Coordination Banners" — slot 1 + slot 5 own banner sweep.
- CLAUDE.md § "Findings Triage Discipline" — case-1-to-5 routing for surprises mid-cycle.
- [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) — the
  upstream sequencing umbrella this work-split serves.
- [`work_split_2026_05_11_harsh.md`](work_split_2026_05_11_harsh.md) — companion split (mirrored cross-side handshakes).
