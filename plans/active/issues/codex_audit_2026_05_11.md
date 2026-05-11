---
title: "Codex SSOT audit pass — 2026-05-11 (freeze-gate item 9 readiness)"
created: 2026-05-11
author: harsh-workspace-qg-tab (slot 6)
source:
  - plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — Phase 1 freeze gate item 9 ("Codex SSOTs
    updated per CLAUDE.md 'Post-Plan-Phase Codex Audit' HARD RULE — every doc that the Phase 1 plans should have touched
    is current")
  - plans/active/work_split_2026_05_11_harsh.md § "Slot 6" — freeze-gate items 8 + 9
  - the 25 Phase 1 plans enumerated in code_freeze § "Phase 1 — Code-complete inventory" (Phase 1.A-1.F)
execution:
  owner:
    slot 6 (harsh-workspace-qg-tab) — runs all 4 days of the 2026-05-11→05-15 cycle; days 2-4 deepen the per-doc
    currency spot-checks; per-plan codex docs are owned by each Phase 1 plan's own codex phase
  cadence: daily refresh until the 2026-05-15 Phase 1 freeze gate fires
  verifier:
    code_freeze freeze-gate item 9 flippable ⟺ every row in the "pending codex work" table below resolved OR explicitly
    deferred post-cutover
  last_executed: "2026-05-11"
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Codex SSOT audit pass — 2026-05-11

> **Severity**: P1 — gates `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 1 freeze gate item 9
> (2026-05-15 hard freeze). **Blast radius**: PM repo (`codex/`) + the 25 Phase 1 plans' codex phases. **Suggested
> owner**: this doc is the running inventory; the actual codex-doc creation/updates are owned by each Phase 1 plan's own
> "Codex SSOT updates" phase (slots 2-6 Harsh-side + Ikenna-side slots). Slot 6 refreshes this inventory daily +
> spot-checks doc currency.

## What this is

Per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE + the code_freeze plan's Phase 1 freeze gate item 9. Walks every
codex doc the 25 Phase 1 plans declare they touch, checks present-vs-missing + (for present docs) stub-vs-full +
currency-vs-frozen-state. The output is two things: (1) the **freeze-gate-9 readiness checklist** — which codex docs
still need to land before 2026-05-15; (2) **findings** — codex docs that exist but are stale/behind the code, or
plan↔doc drift worth a reconcile.

**Method note** (per CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude"): the "missing" docs below were each
cross-checked against their owning plan — every one is an _unchecked_ `- [ ]` todo in the owning plan, i.e.
expected-pending Phase-1 work, **not** a broken commitment. The two genuine findings (F2, F3) were verified by reading
the actual UTL code + the referenced plans, not by grep alone.

## Inventory summary

- **25 Phase 1 plans** scanned (all of `code_freeze` § "Phase 1.A-1.F").
- **91 distinct codex doc paths** referenced across those plans.
- **58 present** / **33 referenced-but-not-yet-created** (all 33 are unchecked `- [ ]` items in their owning plans —
  expected pending Phase-1 work; the freeze gate is the deadline for them).
- Core schema/manifest/pipeline codex docs spot-checked: **healthy** (see § "Spot-check results").

## Pending codex work for freeze-gate item 9 (the 33 not-yet-created docs, grouped by owning plan)

| Owning Phase 1 plan                                  | Codex docs still to create (all `- [ ]` in the plan today)                                                                                                                                                                                                                                                                                                                    | Notes                                                                                                        |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `writegate_honest_coverage_endtoend_2026_05_06.md`   | `codex/02-data/service-output-emission-semantics.md` (NEW)                                                                                                                                                                                                                                                                                                                    | ServiceEmissionPolicy SSOT; slice (b) Phase 5.x.                                                             |
| `hard_schema_enforcement_2026_05_08.md`              | `codex/06-coding-standards/error-handling.md`, `codex/06-coding-standards/schema-validation.md`                                                                                                                                                                                                                                                                               | NEW; SCHEMA_VALIDATION_FAILED enum + write-boundary hard enforcement.                                        |
| `features_repo_consolidation_2026_05_08.md`          | `codex/02-data/data-status-drilldown-hierarchy.md`                                                                                                                                                                                                                                                                                                                            | Note: `codex/02-data/data-status-drilldown.md` exists — possible rename/intent mismatch; verify with slot 2. |
| `risk_simulations_limits_alerting_2026_05_10.md`     | `codex/04-architecture/risk-rule-taxonomy.md`, `codex/04-architecture/risk-preflight-flow.md`, `codex/04-architecture/risk-breaker-seam.md`                                                                                                                                                                                                                                   | NEW (7.A / 7.B / 7.E todos; 7.E "RATIFIED 2026-05-10 cross-plan audit Q9").                                  |
| `disaster_recovery_circuit_breakers_2026_05_10.md`   | `codex/04-architecture/circuit-breaker-rule-taxonomy.md`, `codex/04-architecture/kill-switch-event-bus.md`                                                                                                                                                                                                                                                                    | NEW; cutover-MVP circuit-breaker + kill-switch.                                                              |
| `promote_workflow_may23_cli_path_2026_05_10.md`      | `codex/04-architecture/promote-workflow-architecture.md`, `codex/05-infrastructure/strategy-vm-launcher-shape.md`, `codex/04-architecture/live-deployment-manifest.md`, `codex/09-strategy/operational/cli-promote-paths.md`, `codex/14-customer-journeys/promote-pipeline-backend.md`                                                                                        | All NEW (`[ ]` todos); plus `custody-providers.md` UPDATE (exists).                                          |
| `topology_qgroup_gap_closure_2026_05_09.md`          | `codex/04-architecture/matching-engine-assumptions.md`, `codex/04-architecture/matching-engine-mode-dispatch.md`, `codex/04-architecture/ml-lifecycle.md`, `codex/04-architecture/multi-mode-wallet-isolation.md`, `codex/04-architecture/strategy-ensemble-topology.md`                                                                                                      | 18 GAPs + 2 WATCH + 1 ISSUE before May-23; several NEW codex docs.                                           |
| `defi_recursive_borrow_archetypes_2026_05_10.md`     | `codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked-config-variants.md`, `codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md`                                                                                                                                                                                                             | NEW; carry_staked_basis Phase 9. (`carry-recursive-staked.md` + `carry-staked-basis.md` already exist.)      |
| `defi_simulation_realism_2026_05_10.md`              | `codex/04-architecture/concentrated-liquidity.md`                                                                                                                                                                                                                                                                                                                             | NEW; DeFi matching-engine extension. (`amm-slippage-simulation.md` already exists.)                          |
| `deployment_ui_lifecycle_tabs_2026_05_08.md`         | `codex/05-infrastructure/deployment-ui-environment-tiers.md`                                                                                                                                                                                                                                                                                                                  | NEW; EnvironmentTier enum doc. (`deployment-ui-architecture.md` shipped @PM`ebe5cc09`.)                      |
| `api_keys_wallets_accounts_readiness_2026_05_10.md`  | `codex/04-architecture/custody-architecture.md`, `codex/05-infrastructure/aws-iam-matrix.md`, `codex/05-infrastructure/credentials-matrix.md`, `codex/05-infrastructure/hsm-wallet-signing.md`, `codex/05-infrastructure/per-archetype-wallet-isolation.md`, `codex/05-infrastructure/secret-manager-naming.md`, `codex/14-customer-journeys/credentials/rotation-runbook.md` | 7 NEW codex docs; credential provisioning for May-23 cutover.                                                |
| `wallet_treasury_client_flow_2026_05_10.md`          | `codex/04-architecture/client-lifecycle-state-machine.md`, `codex/04-architecture/treasury-custody-flow.md`                                                                                                                                                                                                                                                                   | NEW; wallet/treasury/client lifecycle MVP.                                                                   |
| `client_reporting_pnl_attribution_mvp_2026_05_10.md` | `codex/04-architecture/client-reporting-architecture.md`                                                                                                                                                                                                                                                                                                                      | NEW. (`backtest-groups.md`, `pnl-attribution.md`, `capital-efficiency-patterns.md` already exist.)           |

**Total: 33 codex docs across 13 plans must land (or be explicitly deferred post-cutover) before freeze-gate item 9
flips on 2026-05-15.** The bulk are recent (2026-05-09/10) Phase 1.D-1.F plans
(risk/DR/promote/topology/defi/credentials/ treasury/client) — codex stubs not yet started, which is the normal flow for
in-flight plans. The Phase 1.A-1.C schema/manifest/pipeline core is in better shape (one NEW doc pending:
`service-output-emission-semantics.md`).

## Findings (verified)

### F2 — `codex/02-data/availability-manifest-and-data-status.md` v8 dataclass is behind the code on `feature_family`

**Severity**: P2 — doc-vs-code drift; not a correctness bug. **Owner**: `features_repo_consolidation_2026_05_08.md`
codex phase (slot 2 — that plan already lists `codex/02-data/availability-manifest-and-data-status.md` in its
codex-update phase).

**Evidence**: The `AvailabilityRecord` dataclass snippet in `availability-manifest-and-data-status.md` (the "Schema v8"
section) shows `feature_group` / `model_family` / `training_period` in the Feature/ML block but **no `feature_family`
field**. The actual UTL code already has it: `unified-trading-library/unified_trading_library/manifest_writer.py:757` →
`feature_family: str = ""` (shipped features_repo_consolidation Phase 1B @UTL`c16cef3` per LEDGER), and
`manifest_writer.py:788` includes `"feature_family"` in the column list. The code_freeze plan (`:139`) also explicitly
lists `feature_family` as a v8 column. The codex doc should add it to the dataclass snippet + the "v8 — feature_family"
comment block.

### F3 — v8 manifest-schema declaration ownership is ambiguous: `code_freeze` says "writegate slice (b) Phase 5.1"; `availability-manifest-and-data-status.md` + `manifest_schema_final_gate_2026_05_09.md` say the final-gate plan

**Severity**: P2 — plan↔doc divergence on which plan is the v8-schema SSOT. Risk: two plans (or their agents) both
think they own the v8 column declaration → double-SSOT, the very thing CLAUDE.md "No double SSOT" + the code_freeze
plan's `(NOT a separate manifest_v8_schema_migration_design file)` clause are guarding against. **Owner**: needs an
operator/slot-1 call on which plan is canonical; the loser gets a `> SUPERSEDED — see <X>` banner. The code_freeze plan
body line 139 + 174-179 may need a small update to point at `manifest_schema_final_gate_2026_05_09.md` (slot 1 PM-body
territory).

**Evidence**:

- `code_freeze_migrate_backfill_sequencing_2026_05_10.md:139` — _"Column declaration is owned by writegate slice (b)
  Phase 5.1 (NOT a separate `manifest_v8_schema_migration_design` file — design intentionally bundled per operator
  direction ...)"_. Same plan `:174-179` — _"the v8 design lives in: Schema column declaration —
  `writegate_honest_coverage_endtoend_2026_05_06.md` slice (b) Phase 5.1 ... There is therefore no 'v8 schema design'
  gap"_.
- `codex/02-data/availability-manifest-and-data-status.md` "Schema v8" section — _"v8 (maximalist final gate per
  [`manifest_schema_final_gate_2026_05_09.md`](.../manifest_schema_final_gate_2026_05_09.md):8-15)"_.
- `plans/active/manifest_schema_final_gate_2026_05_09.md` overview — _"One-shot maximalist plan that lands the BEST
  manifest (v8 with all designed columns) ... slice b spec landed as part of this plan"_,
  `spawned_from: plans/questions/backfill_manifest_schema_freeze_gate_2026_05_08.md`.

These are clearly distinct artifacts. `manifest_schema_final_gate_2026_05_09.md` (created 2026-05-09) IS effectively a
"v8 schema migration design" plan and it claims to OWN the slice-b spec; the code_freeze plan (created 2026-05-10, one
day later) says slice-b spec lives in writegate slice (b) Phase 5.1 and "(NOT a separate ... file)". Either (a)
`manifest_schema_final_gate` and writegate slice (b) Phase 5.1 are the same work referenced two ways → say so explicitly
in both; or (b) one supersedes the other → banner + reconcile. Not slot 6's call.

## Observations (informational — not findings)

- **`availability-manifest-and-data-status.md` calls v8 "(current; ratified 2026-05-09)" while the code is at
  `MANIFEST_SCHEMA_VERSION = 7`** (`manifest_writer.py:131`) and the code*freeze freeze-gate item "Schema columns
  frozen" is still `- [ ]`. In a doc-leads-code workspace ("docs are the intent; codex SSOTs are ahead of the code")
  this is arguably the convention — the doc reflects the \_frozen intent* (v8), which is what the freeze gate wants. The
  prose code snippet inside that section says `MANIFEST_SCHEMA_VERSION = 7` while the surrounding prose says `= 8` — a
  doc-internal inconsistency, but harmless (the snippet is illustrative). Worth a one-line clarification ("v8 = the
  frozen target; the version constant bumps to 8 when the Phase 2 migration runs") when whoever owns the next edit to
  that doc touches it. Not raising as a finding.
- Core schema/manifest/pipeline codex docs all carry proper `> STATUS` headers + plan back-references + "if this doc
  disagrees with the active plan, the plan wins" disclaimers — exactly the stub-vs-full discipline CLAUDE.md "Stub vs
  full content" prescribes. No premature-full-content or orphan-doc issues found in the core area.

## Spot-check results (core docs that the schema freeze hinges on)

| Codex doc                                                              | State                                                    | Verdict                                                                                                                            |
| ---------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `codex/02-data/availability-manifest-and-data-status.md`               | full (1139L)                                             | Healthy; has v8 "Schema v8 (current; ratified 2026-05-09)" section. **F2 + observation above.**                                    |
| `codex/02-data/honest-absence-downstream-handling.md`                  | full (307L)                                              | Healthy; reason taxonomy (9-value `EMPTY_CONFIRMED_REASONS` closed set) codified 2026-05-07 — matches CLAUDE.md.                   |
| `codex/02-data/pipeline-mode-partition.md`                             | stub-with-progress (137L)                                | Healthy; STATUS header + migration-owner ref + shipped-progress table. Appropriate in-flight state.                                |
| `codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` | stub (NEW)                                               | Healthy; STATUS header + plan back-ref (live_pipeline Phase 10). Appropriate.                                                      |
| `codex/05-infrastructure/live-pipeline-architecture.md`                | stub (192L, NEW)                                         | Healthy; STATUS header + plan back-ref + prerequisite plan refs. Appropriate.                                                      |
| `codex/05-infrastructure/replay-subsystem.md`                          | stub (NEW)                                               | Healthy; STATUS header + plan back-ref (live_pipeline Phase 7). Appropriate.                                                       |
| `codex/04-architecture/features-service-architecture.md`               | full-ish (`status: stable`, `last_reviewed: 2026-05-08`) | Healthy; matches the consolidated-features-service design. **(Re-verify `feature_family` mention once F2 lands.)**                 |
| `codex/04-architecture/batch-live-architecture.md`                     | full (438L)                                              | Healthy; "POST-2026-05-08 SSOT" annotation, Redis Stream inner-loop, pipeline_mode mentions, live-pipeline topology refs. Current. |

## Open questions

### Q1 — [harsh-workspace-qg-tab, 2026-05-11 07:00 UTC] — F3: which plan is the canonical v8 manifest-schema declaration owner?

**Status**: ✅ RESOLVED — option (b): `manifest_schema_final_gate_2026_05_09.md` is canonical; writegate slice (b) Phase 5.2 SUPERSEDED.

#### A1 — [ikenna-main, 2026-05-11] — option (b) per operator direction

Operator decision: `manifest_schema_final_gate_2026_05_09.md` is the canonical v8 manifest-schema column declaration owner. Writegate slice (b) Phase 5.2 ("UAC manifest schema columns") is SUPERSEDED. Actions shipped this commit:

- Writegate plan: SUPERSEDED banner added under `#### Slice (b)` header pointing at the final-gate plan; slice (b) retains the UTL `manifest_completeness` helper (Phase 5.1) + MDPS `ohlcv_1h` POC (Phase 5.3-5.4) + deployment-api/ui surfaces (Phase 5.5) + codex/CLAUDE.md (Phase 5.6) + ship-gate (Phase 5.7).
- `code_freeze_migrate_backfill_sequencing_2026_05_10.md:56-57, :145, :180-183, :198, :379` updated to point at `manifest_schema_final_gate_2026_05_09.md` instead of writegate slice (b) Phase 5.1.
- `work_split_2026_05_11_ikenna.md` slot 2 brief re-threaded: v8 column declaration item MOVED OUT of slot 2 scope; remaining scope = UTL helper + MDPS POC + deployment-* surfaces + codex/CLAUDE.md + ship-gate.
- Companion operator-approved Phase 1 addition: new `EXPECTED_KNOWN_SOURCE_GAP` value for UAC `EmptyConfirmedReason` (covers VIX 15m mid-history gap + sports `KNOWN_COVERAGE_GAPS`) — lands in `manifest_schema_final_gate_2026_05_09.md` in the same Phase 1 window per `wave3x_track_d_findings_2026_05_11.md` TL;DR #2.

F2 (`availability-manifest-and-data-status.md` v8 dataclass missing `feature_family`) remains routed to slot 2's `features_repo_consolidation` codex phase — no new action.

#### Original question (preserved for audit trail)

`code_freeze_migrate_backfill_sequencing_2026_05_10.md` (`:139`, `:174-179`) says the v8 manifest-schema column
declaration is owned by `writegate_honest_coverage_endtoend_2026_05_06.md` slice (b) Phase 5.1 and explicitly "(NOT a
separate `manifest_v8_schema_migration_design` file ...)". But `codex/02-data/availability-manifest-and-data-status.md`
and the plan `manifest_schema_final_gate_2026_05_09.md` (created 2026-05-09; "slice b spec landed as part of this plan")
both point at `manifest_schema_final_gate_2026_05_09.md` as the v8 owner — which functionally IS a "v8 schema migration
design" plan. These are distinct artifacts → double-SSOT risk per CLAUDE.md "No double SSOT". **Decision needed**: (a)
they're the same work referenced two ways → say so explicitly in both code_freeze + the final-gate plan; or (b) one
supersedes → banner the loser + update code_freeze's body line 139 + 174-179 to point at the canonical plan. Slot 1
PM-body territory either way.

**Also routing-only (no decision needed)**: F2 (codex doc `availability-manifest-and-data-status.md` v8 dataclass
missing `feature_family` which UTL code already has @`c16cef3`) → route to slot 2's
`features_repo_consolidation_2026_05_08.md` codex phase; slot 2 already lists that doc in its codex-update phase.

## Days 2-4 follow-up (slot 6)

- Deepen currency spot-checks on the remaining ~50 present codex docs the Phase 1 plans touch — especially the Phase 1.D
  (alerting/risk/DR) + 1.E (DeFi) + 1.F (UI/credentials) clusters as their plans land changes.
- Re-check this inventory each morning; flip rows as Phase 1 plans ship their codex phases.
- When a Phase 1 plan flips its codex-phase checkbox `[x]`, verify the doc actually landed (per CLAUDE.md "Plans Run To
  Actual Completion" — code-shipped ≠ doc-shipped).
- Hand the residual list to slot 1 ~2026-05-14 so any still-pending codex docs are visible before the 2026-05-15
  freeze-gate-9 check.

## Composes with

- CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — this is the audit pass that rule prescribes, run at the Phase 1
  boundary of `code_freeze`.
- CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" HARD RULE — the "missing" docs were each verified against their
  owning plan's checkbox state before being classed as pending-not-finding.
- CLAUDE.md "Findings Triage Discipline" — F2 routed to its owning plan (slot 2); F3 routed to operator/slot-1 (needs a
  decision).
- `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 1 freeze gate item 9 — this doc is its readiness
  checklist.
