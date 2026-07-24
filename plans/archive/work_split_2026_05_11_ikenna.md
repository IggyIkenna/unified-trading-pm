---
doc_type: plan
title: Ikenna's daily work-split — 2026-05-11 (Phase 1 code-freeze push to 2026-05-15 freeze gate)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-11
type: coordination-doc
deadline: 2026-05-15
horizon: 4-day cycle
companion_to: plans/active/work_split_2026_05_11_harsh.md
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

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
> ([`/codex/05-infrastructure/per-tab-worktrees.md`](/codex/05-infrastructure/per-tab-worktrees.md)). Each slot is a
> permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/ikennaigboaka/<N>`. Slot count: 8 already
> provisioned (per `setup-tab-worktrees.sh --list` 2026-05-11). Before any slot reassignment from yesterday's theme, run
> `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>`.

| Slot | Theme                                                                                                                                                                                                                 | Plan-of-record                                                                                                                                                                                                                                                                                           | AI-day budget   |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1    | main orchestrator + on-call governance                                                                                                                                                                                | [LEDGER](../../ikenna_orchestrator/LEDGER.md) + Phase 1 freeze-gate audit + master plan refresh + cross-plan banner sweep                                                                                                                                                                                | continuous      |
| 2    | **CRITICAL PATH** — writegate slice (b) Phase 5.1, 5.3-5.7 (UTL helper + MDPS POC + UI surfaces; v8 columns moved to final-gate per operator 2026-05-11)                                                              | [writegate_honest_coverage_endtoend_2026_05_06.md](writegate_honest_coverage_endtoend_2026_05_06.md) slice (b) + [manifest_schema_final_gate_2026_05_09.md](manifest_schema_final_gate_2026_05_09.md)                                                                                                    | ~5              |
| 3    | available_at completion Phase 0 (bar boundary contract) + Phase 4-5 audits                                                                                                                                            | [available_at_lookahead_bias_completion_2026_05_08.md](available_at_lookahead_bias_completion_2026_05_08.md)                                                                                                                                                                                             | ~4              |
| 4    | live pipeline Phase 4-5 design-ahead (gated) + Phase 11 deployment-UI live tab design                                                                                                                                 | [live_pipeline_mtds_mdps_features_2026_05_08.md](live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 4-5 + 11                                                                                                                                                                                          | ~3              |
| 5    | DeFi Phase 1.E sequencing readiness + cross-plan coordination                                                                                                                                                         | [code_freeze_migrate_backfill_sequencing_2026_05_10.md](code_freeze_migrate_backfill_sequencing_2026_05_10.md) Phase 1.E audit                                                                                                                                                                           | ~3              |
| 6    | **CRITICAL PATH** — manifest_schema_final_gate Phase 1 (UAC v8 schema columns + ServiceEmissionPolicy next_state + EXPECTED_KNOWN_SOURCE_GAP enum) — newly canonical per F3 decision 2026-05-11; gate item #1 unblock | [manifest_schema_final_gate_2026_05_09.md](manifest_schema_final_gate_2026_05_09.md) Phase 1                                                                                                                                                                                                             | ~3 (aggressive) |
| 7    | Phase 1.D blockers — alerting + risk + DR (3 plans, sub-agent fan-out)                                                                                                                                                | [alerting_service_live_rules_2026_05_07.md](alerting_service_live_rules_2026_05_07.md) Phase 1 + [risk_simulations_limits_alerting_2026_05_10.md](risk_simulations_limits_alerting_2026_05_10.md) + [disaster_recovery_circuit_breakers_2026_05_10.md](disaster_recovery_circuit_breakers_2026_05_10.md) | ~5 (aggressive) |
| 8    | writegate slice (c) Phase 6.1-6.9 — 37-callsite migration (no longer deferred per operator 2026-05-11 aggressive May-15 push)                                                                                         | [writegate_honest_coverage_endtoend_2026_05_06.md](writegate_honest_coverage_endtoend_2026_05_06.md) slice (c)                                                                                                                                                                                           | ~5 (aggressive) |

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

### Slot 2 — Writegate slice (b) ✅ DONE → RE-TASKED to manifest_schema_final_gate Phase 2 (UTL v8 ManifestWriter) — CRITICAL PATH

> **🟢 RE-TASK BRIEF #2 (added 2026-05-11 PM by slot 1 main on operator approval)** — Slot 2's primary scope (writegate
> slice (b) Phase 5.1, 5.3-5.7) ✅ DONE per PM@`2b207442` (5.1) + PM@`b0b01d9c` (5.3+5.4) + PM@`152db218` (5.5) +
> PM@`40aca8b4` (5.6+5.7) + PM@`2b7e4932` (DONE block). Slot 2 surfaced 4 self-proposed re-task options; operator picked
> **Option 2 (manifest_schema_final_gate Phase 2 — UTL v8 ManifestWriter)** with adjacent quick-win on slot 8's Q2
> Bug 1. Re-task is critical-path for the 2026-05-15 freeze gate Phase 2.1 atomic v8 rename.
>
> **Step 1 (~10 min) — Adjacent quick win: clear slot 8's Q2 Bug 1 (UAC service-name typo)** in
> `unified-api-contracts/unified_api_contracts/canonical/crosscutting/service_emission_policy.py:163-168`. All 6 keys +
> docstring at `:216` use `"market-data-pipeline-service"`; actual service is `market-data-processing-service` (MDPS).
> Replace 6 + docstring + update
> `market-data-processing-service/tests/unit/test_canonical_writer_ohlcv_1h_policy.py:199` if it references the old
> name. **Note for slot 8: Q2 Bug 2 (book_snapshot_5 key-shape) was ✅ RESOLVED** by operator at PM@`fa806abe` (option
> α: source-conceptual data_type tokens, NOT per-cadence — UAC code already matches this; the commit was the CLAUDE.md
> ratification). Ack to slot 8 via plan-of-record (`writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.2 +
> `plans/active/issues/writegate_uac_emission_policy_seed_dict_keys_mismatch_2026_05_11.md`) that Q2 is now fully
> cleared → slot 8 can resume Phase 6.2 wiring of `publish_with_manifest_lookup` at MDPS data_types.
>
> **Step 2 (~10-12 hrs) — Phase 2 (manifest_schema_final_gate UTL v8 ManifestWriter)** per
> [`manifest_schema_final_gate_2026_05_09.md:266-285`](manifest_schema_final_gate_2026_05_09.md):
>
> - **Phase 2.A (~3 hrs)** — `unified_trading_library/manifest_writer.py`: extend `record_captured` / `record_empty` /
>   `record_failed` / `record_expected_empty` / `record_expected_unattempted` with 3 new kwargs
>   (`service_emission_state` / `last_emission_decision_at` / `expected_window_completeness_fraction`), all defaulting
>   to `None` for back-compat with existing callsites. Phase 4 sweeps the callsites; default REMOVED at end of Phase 4
>   (explicit-or-fail).
> - **Phase 2.B (~2 hrs)** — `emission_publisher.py` integration: extend `publish_with_policy` to compute
>   `service_emission_state` via Phase 1.B `next_state(...)` resolver (slot 6 shipped at `UAC@174f401`) + pass to
>   ManifestWriter. Wired at the same publish boundary as existing `EmissionDecision` flow. Natural extension of the
>   `manifest_completeness` helper slot 2 just shipped.
> - **Phase 2.C (~2 hrs)** — Reader fallback: `manifest_reader_fallback.py` tolerates v7 (3 columns missing) for ≤30d
>   post-Phase-7. Emit `READER_BACKFILLED_V8_COLUMNS_AS_NULL` event per row. After 30d zero-event window, fallback
>   deleted (workspace "no double SSOT" rule).
> - **Phase 2.D (~3 hrs)** — NEW `manifest_migrations/v7_to_v8.py` helper: walks canonical
>   `_index/availability_index.parquet` per bucket, adds 3 NULL columns to every existing row, writes per-VM shard at
>   `_index/per_vm/v7_to_v8_migrate_{VM_NAME}.parquet`. Per-VM shard isolation MANDATORY per CLAUDE.md "Per-VM shard
>   isolation for concurrent backfills."
> - **Done-definition** (per plan body): `unified-trading-library@<sha>` shipped + 11+ unit tests + back-compat with v7
>   rows.
>
> **Why slot 2** — natural UAC+UTL context fit (slot 2 just shipped the `manifest_completeness` helper which Phase 2
> extends + integrates); slot 6's Phase 1 v8 column declarations (`UAC@174f401`) are the prereq, now shipped; slot 8 has
> Phase 6.2 (separate scope, no collision). Phase 2 is currently UNOWNED per the post-pull state; no other agent has
> touched Phase 2.A-D commits. Critical path: without it, the Phase 2.1 atomic v8 rename (2026-05-15→05-19 window) has
> nothing to land — the rescan can't write rows in v8 shape if `ManifestWriter` can't accept the new kwargs.
>
> **Original scope context preserved below** (primary writegate slice (b) — ✅ DONE; previously also held UAC v8 column
> declaration scope which was MOVED OUT 2026-05-11 to `manifest_schema_final_gate` per operator F3 decision):
>
> **⚠️ SCOPE UPDATE 2026-05-11** (operator decision resolving codex_audit F3 + work-split phase-number drift): the "UAC
> manifest v8 schema columns" item is **MOVED OUT** of slot 2's scope — it's now owned by
> [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md). Slot 2's remaining scope =
> writegate slice (b) Phase 5.1 (UTL `manifest_completeness` helper) + Phase 5.3-5.4 (MDPS `ohlcv_1h:current` +
> `:historical` wire-in) + Phase 5.5 (deployment-api `/leaf-stats` + deployment-ui DataStatusTab surfaces) + Phase 5.6
> (codex + CLAUDE.md) + Phase 5.7 (ship-gate). Note: writegate's own phase numbering is canonical (5.1 = UTL helper, 5.2
> = UAC columns SUPERSEDED, etc.); the work-split's prior 5.1/5.2 swap is corrected below.

- **Identity**: `ikenna-writegate-slice-b-tab` (slot 2 worktree at `.tabs/2/`).
- **Scope** (per [writegate plan §5.1, 5.3-5.7](writegate_honest_coverage_endtoend_2026_05_06.md)):
  - **P0 Phase 5.1** — Add `manifest_completeness` UTL helper computing
    `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` per drilldown level. SSOT for
    the 3 derived %s
    ([`measure-honest-coverage.py` is the per-data_type measurement script](/codex/02-data/availability-manifest-and-data-status.md);
    the helper is the in-process compute).
  - **P0 Phase 5.3** — Wire `manifest_completeness` into deployment-api `/api/data-status/leaf-stats` endpoint (already
    shipped @3b0477a per [LEDGER 2026-05-08 evening](../../ikenna_orchestrator/LEDGER.md) — extend with the new helper
    output as additional fields).
  - **P0 Phase 5.4** — Add `service_emission_state` column to deployment-ui DataStatusTab venue summary line (extends
    @8f630a6 / @621f0b3 per LEDGER); badge stack rendering for the 4 ServiceEmissionPolicy enum values.
  - **P1 Phase 5.5** — Codex SSOT update: extend
    [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
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
- **Sub-agent fan-out**: send 1 message with 3 parallel `Task` blocks at boot:
  1. UTL `manifest_completeness` helper + tests (writegate Phase 5.1). The UAC v8 schema column declaration item that
     was previously in slot 2 is now owned by `manifest_schema_final_gate_2026_05_09.md` per operator decision
     2026-05-11; coordinate via cross-side ping when the final-gate plan ships v8 columns so slot 2's helper consumes
     them.
  2. MDPS `ohlcv_1h:current` + `:historical` wire-in (writegate Phase 5.3-5.4) — uses `publish_with_manifest_lookup()`
     at the real-time emission + historical re-emission boundaries.
  3. deployment-api `/leaf-stats` + deployment-ui DataStatusTab surface extension (writegate Phase 5.5). Then serially:
     codex + CLAUDE.md (writegate Phase 5.6) + ship-gate (writegate Phase 5.7).
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

### Slot 3 — Available_at completion Phase 0 + Phase 4-5 audits — **RE-TASKED 2026-05-11**

> **🟢 RE-TASK BRIEF (added 2026-05-11 by slot 1 main on operator approval; updated 2026-05-11 PM to deconflict with
> slot 6)** — original scope (Phase 0.1/0.2 + Phase 4 partial + Phase 5 both) ✅ DONE per PM@`9bc57fcb` + PM@`c628eee7`.
> Slot 3 went quiet legitimately at done-definition met. Operator re-tasks slot 3 to absorb two carryover items in its
> UAC/UTL competency:
>
> 1. **Flip sports `available_at` Phase 1 todo** in `available_at_lookahead_bias_completion_2026_05_08.md` per Harsh
>    slot 4's ship at `market-tick-data-service@c186ecb` (`stamp_available_at_odds_snapshot` wired into
>    `_process_sports_venue_with_leagues` with shard-level failure isolation + 5 tests).
> 2. **Answer 4 design Qs in `plans/active/issues/mtds_sports_available_at_wiring_2026_05_11.md` § "Open design
>    questions"**: Q-A (odds `available_at` rule: `bm_time` vs `bm_time + emission_latency_ms_for_source(src)`); Q-B
>    (does MTDS sports write path need `assert_available_at_present`-equivalent guard, given it uses
>    `record_captured_from_counts` not `record_captured(df)`); Q-C (do all sports adapters —
>    betfair/matchbook/sfi/footystats — emit `bm_time` or equivalent publication-time col); Q-D (is there a
>    `SOURCE_PRIORITY` / `emission_latency_ms_for_source` entry for sports sources in UAC, and is it a pre-req).
>
> **DECONFLICT 2026-05-11 PM**: the `EXPECTED_KNOWN_SOURCE_GAP` UAC enum addition was originally bundled into this
> re-task but is now **owned by slot 6** (its spawn prompt assigns it explicitly per the extra-hands commit `2e7cfeea`).
> Slot 3 skips the enum add; cross-reference slot 6's plan-of-record (`manifest_schema_final_gate_2026_05_09.md`
> Phase 1) if needed.
>
> Estimated effort: ~1-2 hrs. Stays in slot 3's repos (UAC + UTL + PM).

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

### Slot 4 — Live pipeline Phase 4-5 design-ahead + Phase 11 deployment-UI live tab design — **RE-TASKED 2026-05-11**

> **🟢 RE-TASK BRIEF (added 2026-05-11 by slot 1 main on operator approval)** — slot 4's design-ahead scope ✅ DONE per
> UAC@`e55651b` + UTL@`58bfbbeb` + deployment-api@`7d95dc9` + deployment-ui@`f3204ce` + PM@`789201d0` + PM@`e30bc355`.
> **However**: the spawn prompt's "BLOCKED on `features_repo_consolidation_2026_05_08` Phase 7 (Harsh slot 2)" hard-sync
> constraint is **STALE**. Verified 2026-05-11 by slot 1:
>
> - `features_repo_consolidation_2026_05_08.md:678` Phase 7 archival is `- [x]` flipped done.
> - `workspace-manifest.json` shows 8 features-\*-service repos with
>   `"archived_into": "features-service", "archive_date": "2026-05-08"`.
> - `gh api repos/IggyIkenna/<repo> --jq .archived = true × 8` per plan's `## DONE — 2026-05-08 PM session` block.
> - features-service repo exists + skeleton + 8 sub-package subtree merges + 10 workflows pushed at
>   `features-service@d3d6e286` on 2026-05-10.
>
> So slot 4's hard-sync gate cleared 3 days ago. Slot 4 design-shipped instead of implementing as a result of misreading
> the spawn prompt. Promote-to-implementation scope:
>
> 1. **`MDPSStreamingAggregator`** (UTL@`58bfbbeb` stub) → real implementation: UTC-aligned candle boundaries +
>    watermark + grace + replay handoff per the design contract in
>    `/codex/05-infrastructure/live-pipeline-architecture.md`. Add unit tests covering the 4-category empty-output
>    decision matrix per CLAUDE.md.
> 2. **`AssetScopedFeaturesRunner`** (UTL@`58bfbbeb` stub) → real implementation. Per-asset_group flavor
>    (cefi/defi/tradfi/predictions/sports) wired against the now-consolidated `features-service`.
> 3. **`CrossCuttingFeaturesRunner`** (UTL@`58bfbbeb` stub) → real implementation. Cross-cutting fan-in propagation per
>    the codex doc's "cross-cutting fan-in propagation table".
> 4. **`deployment-api /api/data-status/live` endpoint** (deployment-api@`7d95dc9` stub) → wire to real `data_freshness`
>    callback from `unified_trading_library.health.make_health_router`. Pydantic models stay as shipped.
> 5. **`<LiveDataStatusTab/>` deployment-ui** (deployment-ui@`f3204ce` scaffold) → wire to the live API endpoint above
>    instead of mock fixtures.
> 6. **Plan flips**: in `live_pipeline_mtds_mdps_features_2026_05_08.md`, flip Phase 4/5/6 implementation halves from
>    `status: design-shipped` + `**DEFERRED**` annotations to `- [x]` done with `<repo>@<sha>` evidence. Phase 11
>    already partially flipped; complete the implementation half.
>
> Estimated effort: ~6-10 hrs (live-pipeline implementation has integration test surface). Stays in slot 4's repos
> (UAC + UTL + deployment-api + deployment-ui + PM). Coordinate via cross-side ping with Harsh slot 5 (live-pipeline
> service wiring per-service consumers) — they were waiting on slot 4 to promote design to implementation; the slot 4
> spawn-prompt staleness was the actual blocker on both sides.

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
    [`/codex/05-infrastructure/live-pipeline-architecture.md`](/codex/05-infrastructure/live-pipeline-architecture.md)
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
  - **P0 (NEW 2026-05-11)** — **Operator decision (b+) cascade audit**: bucket-name SSOT operator decision
    [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md) Phase 0a
    (option (b+) — full env-aware bucket architecture across both clouds + sync script + region pinning) extends Harsh
    slot 4 scope ~3 → ~10-13 AI-day. Anti-sequencing audit table entry for bucket_name_ssot now flips from "Phase 1.B
    ownership; sequenced before Phase 2.4 AWS migration writes" to "Phase 1 (code-complete: 0a/0b/0e/0f/0g/0h/0i + L2
    config.py + legacy delegate) + Phase 2 (physical migration: 0c provision ~300-400 buckets + 0d data migration with
    ≤0.01% drift verification + write-pause cutover) + Phase 3 (verification: zero readers hit flat names, QG STEP 5.69
    ratchet enforces no new flat refs)." Update the audit table accordingly + extend
    [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group D + F readiness columns to reflect
    the bigger physical migration scope.
  - **P1** — Refresh anti-sequencing audit table at
    [code_freeze:298-313](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L298-L313) with today's status of every
    plan listed (now includes bucket_name_ssot Phase 0c/0d entry per (b+) per
    [code_freeze:GAP-2.4.B/C/E/F/G/H/I](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L222-L228)); add new plans
    created during today's cycle.
  - **P1** — Cross-plan coordination banner sweep (helper to slot 1 P0 banner verification): walk the 9 banner targets
    and add any banners still missing. **NEW per (b+)**: add banner on
    [`aws_migration_defi_first_2026_05_07.md`](aws_migration_defi_first_2026_05_07.md) Phase 2 (already added by slot 1
    PM@<this commit>) + verify on
    [`deployment_ui_lifecycle_tabs_2026_05_08.md`](deployment_ui_lifecycle_tabs_2026_05_08.md) +
    [`simulation_scenarios_topology_price_shocks_2026_05_09.md`](simulation_scenarios_topology_price_shocks_2026_05_09.md)
    - [`client_reporting_pnl_attribution_mvp_2026_05_10.md`](client_reporting_pnl_attribution_mvp_2026_05_10.md) (the
      other plans touching bucket-naming per the 2026-05-11 grep audit).
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
- **Coordinate: Ikenna slot 3 (AVAILABILITY_AT_SEMANTICS audit) ↔ Harsh slot 3 (Wave3x Track E sports stamping)**. Track
  E folded into available_at Phase 1 — Harsh ships per-source helpers, Ikenna integrates into AVAILABILITY_AT_SEMANTICS.
- **Banner-add: Ikenna slot 1 (banner sweep) → both sides**. Slot 1 ensures every plan that touches Phase 1 / Phase 2 /
  Phase 3 work has the cross-plan banner pointing back at code_freeze umbrella.

## Collision-risk callouts

| Files / dirs                                                                 | Collision tabs                                                                             | Mitigation                                                                                            |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `unified-api-contracts/unified_api_contracts/canonical/manifest/*`           | slot 2 (v8 schema columns) + slot 4 (live-pipeline contract types may add manifest fields) | Slot 2 owns canonical manifest columns; slot 4 routes any manifest-touching contracts through slot 2. |
| `unified-api-contracts/unified_api_contracts/canonical/instruments/*`        | slot 5 (EVENT_CONTRACT enum) + slot 3 (FEATURE_REQUIRED_INPUTS expansion may touch types)  | Slot 5 ships the enum; slot 3 references it. Surgical `git add -p`.                                   |
| `unified-trading-library/unified_trading_library/manifest/*`                 | slot 2 (manifest_completeness helper) + slot 3 (compute_bar_close_boundary helper)         | Distinct file paths within manifest/; both can edit in parallel.                                      |
| `unified-trading-pm/plans/active/code_freeze_migrate_backfill_*.md`          | slot 1 (freeze-gate audit) + slot 5 (anti-sequencing audit)                                | Distinct sections; surgical `git add -p`. Or slot 1 commits first, slot 5 rebases.                    |
| `unified-trading-pm/plans/archive/2026_07/master_to_live_defi_2026_05_23.md` | slot 1 (Group D + F + G readiness columns) + slot 5 (banner adds)                          | Slot 1 owns the readiness table; slot 5 only adds top-of-file banner if missing.                      |
| `unified-trading-pm/cursor-configs/CLAUDE.md`                                | slot 2 (key-rule entry for v8 manifest)                                                    | Slot 2 sole writer this cycle; nobody else edits CLAUDE.md.                                           |
| `deployment-api/deployment_api/api/data_status/*`                            | slot 2 (leaf-stats endpoint) + slot 4 (live-status endpoint)                               | Distinct endpoint files; both can edit in parallel.                                                   |
| `deployment-ui/src/components/DataStatusTab/*`                               | slot 2 (badge rendering) + slot 4 (live tab scaffold for separate Live tab)                | Distinct component files; slot 4's Live tab is a NEW component, not edits to DataStatusTab.           |

**Per-slot worktree isolation** (per
[`/codex/05-infrastructure/per-tab-worktrees.md`](/codex/05-infrastructure/per-tab-worktrees.md)) makes cross-slot races
on `.git/index` unrepresentable; the table above is for SHARED-FILE-CONTENT collisions when slots push and pull each
other's commits.

## Spawn prompts (paste-ready into fresh Claude Code / Cursor tabs)

> **Operator usage**: open a fresh Cursor / Claude Code tab inside the slot N worktree, then paste the matching prompt.
> The agent reads the slot's plan-of-record + LEDGER bootstrap on its own.
>
> Two equivalent ways to open the slot in Cursor (both produce identical isolation):
>
> ```bash
> # Option A — Open as folder (flat single-root view):
> code "$WORKSPACE_ROOT/.tabs/<N>"
>
> # Option B — Open as multi-root workspace (named labels per repo, custom emojis):
> code "$WORKSPACE_ROOT/.tabs/<N>/unified-trading-system-repos.code-workspace"
> ```
>
> The `.code-workspace` file is auto-provisioned into each slot dir by `setup-tab-worktrees.sh --init` / `--add-slot`,
> so Option B works immediately. For Claude Code CLI: `cd "$WORKSPACE_ROOT/.tabs/<N>" && claude`. Verify CWD with `pwd`
> (→ `.../.tabs/<N>`) + branch with `git -C unified-trading-pm rev-parse --abbrev-ref HEAD` (→ `tab/ikennaigboaka/<N>`)
> before pasting the spawn prompt.

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

### Slot 5 RE-TASK (after DeFi 1.E audit done ~half day) — hard_schema + available_at DeFi/TradFi/Predictions + PROTOCOL_LAUNCH_DATES research

> **🟢 RE-TASK EXPANSION 2026-05-11 PM (added by slot 1 main on operator approval)** — slot 5 self-declared "freed up"
> after shipping DeFi Phase 1.E audit + hard*schema_enforcement Phase 1 (PM@`79b5258e` + `63413bb9` + `6f9db6ca` +
> `9c73ef57` + `b945e108`). Per operator direction *"reassign anything that was dropped out of 15th May code freeze to
> it since we are moving faster than planned so that it can do more and unblock more other work,"\_ slot 5's scope
> expands with Tier 1 (Phase 1 freeze-gate critical-path closures) + Tier 2 (carryover from original re-task).
>
> **Tier 1 — Phase 1 freeze-gate critical-path closures (~5-6 AI-days, compressible with sub-agent fan-out to ~2-3
> wall-clock days):**
>
> 1. **Step 5 of P0-2 MDPS surgery (~30 min - 1 hr)** — flip
>    `market-data-processing-service/schemas/output_schemas.py:57-66` OHLCV column nullability from `nullable=True` →
>    required for `trades` / `ohlcv` data_types. Closes the LAST item of P0-2 MDPS surgery (slot 8's task brief
>    explicitly deferred Step 5 to `hard_schema_enforcement_2026_05_08.md` per writegate plan body DONE-2026-05-11).
>    Natural extension of slot 5's hard_schema work shipped today.
> 2. **Writegate slice (c) Phase 6.5 — Other features-\* services bundle (~2-3 days w/ 4 parallel sub-agents)** per
>    [`writegate_honest_coverage_endtoend_2026_05_06.md:3123`](writegate_honest_coverage_endtoend_2026_05_06.md). 4
>    sub-agents in parallel (1 per service): features-onchain-defi (LST yield curves / gas-fee aggregates / vault-state
>    summaries) + features-sports (fixture-stat aggregates / transfer-window / line-movement) + features-prediction
>    (canonical-question-group bundle metrics / market-mid time-series) + features-microstructure (book-imbalance /
>    trade-flow toxicity). Each sub-agent: audit emission boundaries for derived/aggregated outputs → extend UAC
>    `SERVICE_OUTPUT_POLICIES` seed dict per finding → wire `publish_with_manifest_lookup()` per Phase 5.3-5.4 MDPS
>    template → unit + integration tests → flip Phase 6.5 sub-checkboxes per service. **Closes ~60% of remaining Phase 1
>    freeze-gate item #3 (37-callsite migration)** — drives gate item from currently-red to ~70% green. Slot 8 has Phase
>    6.2 in parallel; no collision.
> 3. **Promote `expected_universe_v2_design_2026_05_08.md` → active execution plan (~1 day)** per
>    [code_freeze:199](code_freeze_migrate_backfill_sequencing_2026_05_10.md) "P1 deferred behind v8 schema bump." V8
>    just shipped today (`UAC@174f401` slot 6); prereq cleared. Slot 5 promotes the design draft to executable phase
>    shape + ships any inline UAC additions the v2 enumerator needs.
>
> **Tier 2 — Carryover from original re-task (~3-5 AI-days):**
>
> 4. **`available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 — DeFi + TradFi + Predictions per-adapter stamping
>    (~2-3 days)** — original re-task item; NOT yet shipped. Same shape as Harsh slot 4's sports stamping at
>    `MTDS@c186ecb`. Slot 5 has DeFi + TradFi context from Phase 1.E audit.
> 5. **PROTOCOL_LAUNCH_DATES research ~30 (chain, protocol) pairs (~1-2 days w/ 8-10 sub-agent fan-out)** — original
>    re-task item; NOT yet shipped. Per `defi_master Q1 #3`. Pure web-research + UAC dict edit fan-out; ~6,912 rows
>    reclaimed once shipped.
> 6. **DeFi Phase 1.E Stream C remainder (~few hrs)** — PARTIAL today (1 of 3+ archetype enum flips); finish remainder.
>
> **Sequencing recommendation**: Tier 1 item 1 (Step 5 MDPS, ~30min) FIRST — quick win + closes P0-2. Then Tier 1 item 2
> (Phase 6.5 bundle, fan out 4 sub-agents in parallel). Tier 1 item 3 (expected_universe_v2 promotion) in parallel with
> the Phase 6.5 sub-agents (different surface). Tier 2 items pick up if time allows before 2026-05-15 freeze.
>
> **Why slot 5**: slot 5 has the broadest cross-cutting context from today's shipments (DeFi catalogue + hard_schema +
> Phase 1.E audit + cross-plan banner sweep). Phase 6.5 unblocks gate item #3 closure (currently-red);
> expected_universe_v2 unblocks the Phase 2 cross-asset rescan; Step 5 closes the final P0-2 item. All 3 Tier 1 items
> have NO active owner and ALL are critical-path for the 2026-05-15 freeze gate. Slot 8 owns Phase 6.2 only (different
> scope); slot 2 owns manifest_schema_final_gate Phase 2 (different scope); slot 7 owns alerting+risk+DR (different
> scope). No collision.

Once slot 5's DeFi 1.E audit lands (it's quick — ~half day), pull aggressive Phase 1 items in:

- **`hard_schema_enforcement_2026_05_08.md` Phase 1** — currently `blocked_by: tradfi-master-2026-05-07`. Slot 5
  unblocks by either: (a) coordinating tradfi futures-expiry fields landing first, or (b) shipping the schema flips with
  conditional-required (allow null until tradfi ships, then flip required). Workspace-wide enforcement via UAC schema
  additions + `record_failed(SCHEMA_VALIDATION_FAILED)` enum extension. ~2 AI-day aggressive.
- **`available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 — DeFi + TradFi + Predictions per-adapter stamping**
  — currently deferred to defi*master / tradfi_master / predictions_master per the plan body. Slot 5 PULLS THESE IN per
  operator 2026-05-11 aggressive May-15 push. Same shape as Ikenna slot 3's Phase 0 + Harsh slot 4's sports stamping
  (already shipped MTDS@c186ecb): identify per-adapter write boundary, wire `stamp_available_at*\*` UTL helpers from
  Wave3x Track E. ~2-3 AI-day across 3 asset_groups.
- **NEW (operator 2026-05-11 fold-in): defi_master Q1 #3 — UAC `PROTOCOL_LAUNCH_DATES` tightening (~30 (chain, protocol)
  pairs in `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`)** — operator-approved 2026-05-11 in principle (defi_master Q1 A1);
  per-protocol launch-date research needed. Pure web-research + UAC dict edit fan-out (1 sub-agent per pair). For each
  pair in
  `unified-api-contracts/unified_api_contracts/registry/chain_env.py:264 _PROTOCOL_LAUNCH_PENDING_INVESTIGATION`:
  WebFetch protocol launch announcement / block explorer first-event / project documentation → propose conservative date
  → add `(chain, protocol): "YYYY-MM-DD"` to `PROTOCOL_LAUNCH_DATES` (line 144) → remove from PENDING set. Coordinate
  with Tab 14 Day-1 audit's 13 PROTOCOL_LAUNCH_DATES drift pairs (single consolidated UAC commit folds them all). ~6,912
  rows reclaimed once shipped from defi_988 audit (4-page evidence in
  `plans/archive/issues/defi_988_missing_dates_audit_2026_05_08.md`). **Sub-agent fan-out**: send 8-10 parallel `Task`
  blocks at boot (one per chunk of 3-4 pairs); each sub-agent researches its pairs + drafts the dict additions; master
  synthesizes into one UAC commit. Lower priority than hard_schema + available_at adapter wiring (those are gate items);
  this is the operator's "defer post-cutover" prevention so it doesn't slip past 2026-05-15. ~1-2 AI-day aggressive.

```text
You are Tab 5 (RE-TASK) — slot 5 finished DeFi Phase 1.E audit; now picking up aggressive Phase 1 closure items per operator decision 2026-05-11 (no items deferred past May-15 freeze gate; we don't want to re-migrate post-freeze).

Your slot is 5. Your worktree is at ${WORKSPACE_ROOT}/.tabs/5/ on branch tab/ikennaigboaka/5.

NEW theme: hard_schema_enforcement Phase 1 (unblock vs tradfi) + available_at completion Phase 1 DeFi/TradFi/Predictions per-adapter wiring + **defi_master Q1 #3 PROTOCOL_LAUNCH_DATES research (~30 pairs, fan-out)** — all per operator 2026-05-11 aggressive May-15 push (no items deferred past freeze).

Read in order:
  1. plans/active/work_split_2026_05_11_ikenna.md § "Slot 5 RE-TASK" — full task brief (this section).
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md.
  4. unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md.
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.
  6. plans/active/hard_schema_enforcement_2026_05_08.md — first plan-of-record.
  7. plans/active/available_at_lookahead_bias_completion_2026_05_08.md — second plan-of-record (Phase 1 DeFi/TradFi/Predictions halves currently deferred per line 250-278).
  8. plans/active/defi_master_2026_05_07.md § Q1 A1 — operator-approved 2026-05-11 PROTOCOL_LAUNCH_DATES tightening; this is your third workstream.
  9. unified-api-contracts/unified_api_contracts/registry/chain_env.py:144 (PROTOCOL_LAUNCH_DATES dict) + :264 (`_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` set — your research targets).
 10. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella.

Your agent-tag: ikenna-aggressive-may15-tab.

ORCHESTRATION RULES: same as slot 2 spawn prompt.

Cross-side coordination: ping Harsh main when ready to coordinate with tradfi_master Q1+Q2 (futures-expiry fields) — aim for parallel land, not sequential. For the PROTOCOL_LAUNCH_DATES research, coordinate with Tab 14's Day-1 audit's 13 drift pairs (see audit doc cited in defi_master Q1 A1) — single consolidated UAC commit folds them all.

YOUR TASK: ship by 2026-05-15:
  (a) hard_schema_enforcement Phase 1 (unblock vs tradfi);
  (b) available_at Phase 1 DeFi/TradFi/Predictions per-adapter stamping (~3 asset_groups). Follow shipped-precedent shapes: CeFi stamping MTDS@4a00bd5 + sports stamping MTDS@c186ecb;
  (c) PROTOCOL_LAUNCH_DATES research fan-out: send 8-10 parallel `Task` blocks at boot — each sub-agent gets 3-4 (chain, protocol) pairs from `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`, WebFetches launch announcement / block-explorer first-event / project docs, proposes a conservative date, drafts the dict additions. You synthesize into ONE UAC commit adding all pairs to PROTOCOL_LAUNCH_DATES (chain_env.py:144) + removing them from PENDING (chain_env.py:264). Coordinate with the existing ASTER addition shipped this session (UAC@77666c8). Reclaims ~6,912 rows of false-flagged missing data per defi_988 audit.

Per CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" HARD RULE: when researching launch dates, verify via at least 2 independent sources (block-explorer first-event + project's official announcement / docs). Conservative dates preferred (over-clipping toward chain genesis is safer than under-clipping per chain_env.py:260-262 docstring).

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push. Final DONE-2026-05-11 block + EOD-audit. Then go quiet.
```

### Slot 6 spawn prompt (NEW — manifest_schema_final_gate Phase 1, CRITICAL PATH)

```text
You are Tab 6 — NEW spawn 2026-05-11 (Ikenna's reserve slot 6 activated for Phase 1 freeze-gate critical path).

Your slot is 6. Your worktree is at ${WORKSPACE_ROOT}/.tabs/6/ on branch tab/ikennaigboaka/6.

YOUR JOB IS THE WORKSPACE'S MOST CRITICAL PATH for the 2026-05-15 Phase 1 freeze gate. Per operator F3 decision PM@39ab61e5: `manifest_schema_final_gate_2026_05_09.md` is the canonical owner of v8 manifest schema columns (writegate slice (b) Phase 5.2 SUPERSEDED). Without your work, Phase 2.1 (manifest atomic v8 rename, window 2026-05-15→05-19) cannot start.

Theme: manifest_schema_final_gate Phase 1 — UAC v8 schema columns (`service_emission_state`, `pipeline_mode`, `feature_family`) + ServiceEmissionPolicy `next_state(...)` resolver + EXPECTED_KNOWN_SOURCE_GAP enum value (operator approved 2026-05-11).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/plans/active/work_split_2026_05_11_ikenna.md § "Slot 6 spawn prompt" — this section.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards (especially "Availability manifest v5 (honest-coverage)" + the new "Bucket-name SSOT operator decision (b+)" key rule).
  3. unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md.
  4. unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md.
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.
  6. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md — your plan-of-record (Phase 1.A + 1.B + 1.C are your scope).
  7. unified-trading-pm/plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella; Phase 2.1 depends on you.
  8. unified-trading-pm/plans/active/issues/wave3x_track_d_findings_2026_05_11.md § TL;DR point 2 — EXPECTED_KNOWN_SOURCE_GAP enum context (VIX 15m gap + sports KNOWN_COVERAGE_GAPS use cases).

Your agent-tag: ikenna-v8-schema-tab.

ORCHESTRATION RULES (full text in CLAUDE.md):
  1. Per-slot worktree isolation; pre-commit check (git status + git diff --cached --stat NO PATH ARG).
  2. Plan-doc Q&A: 🟡 BLOCKED → manifest_schema_final_gate plan's `## Open questions` + ping in unified-trading-pm/ikenna_orchestrator/_agent_pings.md.
  3. Conditional push per shippable unit.
  4. Plan-flip in same logical unit as code.
  5. Findings Triage Discipline HARD RULE.
  6. CROSS-SIDE PING MANDATORY when v8 schema columns shipped — Harsh slot 6 (workspace QG sweep) + Harsh slot 4 (bucket_name_ssot Phase 0c provisioning) need the schema landed before they can finalize.

YOUR TASK:
- Phase 1.A: ratify slice (b) spec inline in the plan body (consume writegate slice b Phase 5.1 design content — it's there, just integrate).
- Phase 1.B: extend `service_emission_policy.py` with `next_state(...)` resolver mapping current_state + event → next_state.
- Phase 1.C: declare manifest schema columns in `unified-api-contracts/canonical/crosscutting/manifest_schema.py` (NEW or extend) — `service_emission_state`, `pipeline_mode`, `feature_family` per the spec.
- ADDITIONAL: add `EXPECTED_KNOWN_SOURCE_GAP` to UAC `EmptyConfirmedReason` enum + 1 unit test (operator-approved 2026-05-11; mid-history accepted gaps for VIX 15m + sports KNOWN_COVERAGE_GAPS).

Skip Phase 2/3/4 — those are downstream consumer-side work for other slots / next cycles.

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push. Final DONE-2026-05-11 block in manifest_schema_final_gate plan body. EOD-audit per CLAUDE.md "Capture Discoveries As Plan Todos Immediately" § "End-of-cycle audit clause". Then go quiet.

This is THE critical-path slot for May-15 freeze. Ship fast.
```

### Slot 7 spawn prompt (NEW — Phase 1.D: alerting + risk + DR, 3 plans parallel)

```text
You are Tab 7 — NEW spawn 2026-05-11 (Ikenna's reserve slot 7 activated for Phase 1.D blockers).

Your slot is 7. Your worktree is at ${WORKSPACE_ROOT}/.tabs/7/ on branch tab/ikennaigboaka/7.

Theme: Phase 1.D blockers — 3 plans in parallel via sub-agent fan-out (you are the master, send 3 Task tool blocks in ONE message at boot per CLAUDE.md "Sub-agent fan-out (within each tab, both models)" rule).

Your 3 plans-of-record:
  1. plans/active/alerting_service_live_rules_2026_05_07.md (~26 open todos out of 56 total — 30 done)
  2. plans/active/risk_simulations_limits_alerting_2026_05_10.md (~40 open todos, none done)
  3. plans/active/disaster_recovery_circuit_breakers_2026_05_10.md (~41 open todos, none done)

BEFORE doing anything else, read in order:
  1. plans/active/work_split_2026_05_11_ikenna.md § "Slot 7 spawn prompt" — this section.
  2. unified-trading-pm/cursor-configs/CLAUDE.md.
  3. unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md.
  4. unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md.
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.
  6-8. Three plans-of-record above.
  9. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md Phase 1.D (your sequencing umbrella).

Your agent-tag: ikenna-phase-1d-tab.

ORCHESTRATION RULES: same as slot 2 spawn prompt.

YOUR TASK: ship Phase 1 closure across the 3 plans by 2026-05-15. Per CLAUDE.md "Sub-agent fan-out": send 3 Task tool blocks in ONE message at boot — one sub-agent per plan. Each sub-agent ships its plan's Phase 1 / Phase 0 items, commits + push, plan-flip in same logical unit. You synthesise + commit master pings + cross-side coordination + per-plan DONE blocks.

If any plan's Phase 1 scope is too big for 4-day window, prioritise: alerting > risk > DR (alerting is closest to "live trading prerequisite"; risk + DR are Group F/G items that compound on alerting).

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push. Final DONE-2026-05-11 block in EACH of the 3 plans' bodies. EOD-audit. Then go quiet.
```

### Slot 8 spawn prompt (NEW — writegate slice (c) 37-callsite migration)

```text
You are Tab 8 — NEW spawn 2026-05-11 (Ikenna's reserve slot 8 activated for writegate slice (c) full migration; no longer deferred per operator 2026-05-11 aggressive May-15 push).

Your slot is 8. Your worktree is at ${WORKSPACE_ROOT}/.tabs/8/ on branch tab/ikennaigboaka/8.

Theme: writegate slice (c) Phase 6.1-6.9 — full 37-callsite migration of MDPS + MTDS adapters from legacy `record_*` shapes to `record_captured` / `record_empty` / `record_failed` / `record_expected_unattempted` 4-pillar gate. Operator 2026-05-11: no longer deferred to Phase 2 buffer; lands by 2026-05-15.

BEFORE doing anything else, read in order:
  1. plans/active/work_split_2026_05_11_ikenna.md § "Slot 8 spawn prompt" — this section.
  2. unified-trading-pm/cursor-configs/CLAUDE.md (especially "Availability manifest v5 (honest-coverage)" + "Honest absence vs fake placeholders" + "Four-category empty-output decision").
  3. unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md.
  4. unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md.
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md.
  6. plans/active/writegate_honest_coverage_endtoend_2026_05_06.md slice (c) Phase 6.1-6.9 — your plan-of-record.
  7. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md gate item #3 (37 callsites — your scope).
  8. plans/active/issues/wave3x_track_d_findings_2026_05_11.md § P0-2 (MDPS dead write-gate context — coordinates with your work).

Your agent-tag: ikenna-writegate-slicec-tab.

ORCHESTRATION RULES: same as slot 2 spawn prompt + ALSO:
  - Sub-agent fan-out heavy: 37 callsites split across 8 services (MDPS / MTDS adapters per asset_group). Send 8 Task tool blocks in ONE message at boot — one sub-agent per service. Each sub-agent migrates its callsites, commits + push, plan-flip.
  - You synthesise + drive cross-service coordination (some callsites depend on UAC enum additions from slot 6 — coordinate via plan-of-record).

YOUR TASK: ship slice (c) Phase 6.1-6.9 by 2026-05-15. 37 callsites is aggressive in 4 days but per operator velocity feedback (workspace shipped a lot in 0.5 days) it's achievable with 8 parallel sub-agents.

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push. Final DONE-2026-05-11 block in writegate plan body slice (c). EOD-audit. Then go quiet.
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

## Deferred work after 2026-05-11 session

End-of-cycle scoreboard per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" Half 3. Companion:
[`work_split_2026_05_11_harsh.md`](work_split_2026_05_11_harsh.md) § same.

| Phase / item                                                                                 | Status as of 2026-05-11 EOD                                                                                                                      | Successor / blocker                                                                                                                                                      |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Slot 2 — manifest_schema_final_gate Phase 2/3/4/5 + writegate slice (b) Phase 5.A/B          | ✅ DONE (PM@`1dae5dbf`; 12 commits / 5 repos)                                                                                                    | —                                                                                                                                                                        |
| Slot 2 — writegate slice (b) Phase 5.X remainder (post-5.A/B)                                | ⚪ PARTIAL — 5.A/B `gcs_migration_bundle` shipped; 5.X tail open                                                                                 | 2026-05-12 slot 8 secondary scope (manifest Phase 3 + cross_cutting #4) — see [`continuation_prompts_2026_05_12.md`](continuation_prompts_2026_05_12.md) § Ikenna slot 8 |
| Slot 3 — defi #5 lending-indices LINEA/BSC + canonical re-consolidation                      | ✅ DONE (PM@`e160a364`)                                                                                                                          | —                                                                                                                                                                        |
| Slot 3 — 4 lending-indices residuals handed off                                              | ⚪ DEFERRED                                                                                                                                      | 2026-05-12 slot 2 (`defi_catalogue_chain_primitives` Phase 3 covers lending-indices fix)                                                                                 |
| Slot 3 — Phase 3.D rescan VM CLI dispatcher fix (extra)                                      | ✅ DONE (PM@`7a11b747`, deployment-service@`03ce073`)                                                                                            | —                                                                                                                                                                        |
| Slot 4 — live-pipeline Phase 4-5 design-ahead carry-forward                                  | ⚪ PARTIAL — status uncertain per main-orch audit                                                                                                | 2026-05-12 slot 7 (already absorbing Harsh slot 5 live-pipeline Phase 3-5/15 carry-forward — extends to 4-5 implementation)                                              |
| Slot 5 — DeFi Phase 1.E audit + hard_schema_enforcement Phase 1                              | ✅ DONE (PM@`79b5258e`/`63413bb9`/`6f9db6ca`/`9c73ef57`/`b945e108`)                                                                              | —                                                                                                                                                                        |
| Slot 5 — Tier 1 item 1 Step 5 P0-2 MDPS output_schemas nullability                           | ⚪ STATUS UNCLEAR — pending slot 5 STATUS-2026-05-11 ack                                                                                         | 2026-05-12 slot 5 carry-forward (defi_recursive_borrow theme) — STATUS-2026-05-11 line resolves                                                                          |
| Slot 5 — Tier 1 item 2 writegate slice (c) Phase 6.5 features-\* bundle                      | ⚪ STATUS UNCLEAR — pending slot 5 STATUS-2026-05-11 ack                                                                                         | 2026-05-12 slot 5 carry-forward; if open, fan to 2026-05-12 reserve list                                                                                                 |
| Slot 5 — Tier 1 item 3 expected_universe_v2 promotion                                        | ✅ DONE (plan frontmatter `status: active`)                                                                                                      | Enumerator implementation deferred — 2026-05-12 reserve list                                                                                                             |
| Slot 5 — Tier 2 item 4 available_at DeFi/TradFi/Pred per-adapter stamping                    | ⚪ PARTIAL                                                                                                                                       | 2026-05-12 slot 5 carry-forward + per-asset-group master plans (defi_master / tradfi_master / predictions_master)                                                        |
| Slot 5 — Tier 2 item 5 PROTOCOL_LAUNCH_DATES ~30 (chain, protocol) pairs                     | ✅ DONE — 45 pairs shipped (PM@`c71b10c7`; exceeds 30 scoped)                                                                                    | —                                                                                                                                                                        |
| Slot 5 — Tier 2 item 6 Stream C C-enum.3+4                                                   | ⚪ DEFERRED-PER-USER (deferred to backport plan; C-enum.1+2 done)                                                                                | Backport plan TBD (post-2026-05-15 freeze gate)                                                                                                                          |
| Slot 6 — phantom audit all-5 asset_groups                                                    | ✅ DONE (PM@`17d0b9c6`; dry-run, no `--apply`; DeFi 0/CeFi 0.17%/TradFi 4.3%-P0-triage/Pred 0.49%/Sports 16.8%)                                  | TradFi 4.3% P0-triage open — 2026-05-12 slot 3 (code_freeze Phase 1.E audit covers)                                                                                      |
| Slot 6 — phantom audit items 8+9 partial                                                     | ⚪ DEFERRED                                                                                                                                      | 2026-05-12 slot 6 (defi_simulation_realism) carry-forward — see [`continuation_prompts_2026_05_12.md`](continuation_prompts_2026_05_12.md) § Ikenna slot 6               |
| Slot 7 — Ikenna alerting/risk/DR Rounds 1-4                                                  | ✅ DONE                                                                                                                                          | —                                                                                                                                                                        |
| Slot 7 — Harsh slot 5 live-pipeline absorption (Phase 3/5/6/15)                              | ⚪ STATUS UNCLEAR — pending slot 7 STATUS-2026-05-11 ack                                                                                         | 2026-05-12 slot 7 (simulation_scenarios theme) carry-forward                                                                                                             |
| Slot 8 — P0-2 MDPS surgery 5/5 incl. EXPECTED_KNOWN_SOURCE_GAP + writegate Phase 6.2 PARTIAL | ✅/⚪ DONE primary + PARTIAL on Phase 6.2 consumer wiring (152 LOC scaffolding at mdps@`ae0cada` ONLY on `tab/ikennaigboaka/8`; NOT FF'd to LDR) | 2026-05-12 slot 8 (manifest Phase 3 owner — natural extension to wire-up scaffolding)                                                                                    |
| Slot 8 — Phase 0f VM-launcher env-awareness absorption                                       | ⚪ STATUS UNCLEAR — pending slot 8 STATUS-2026-05-11 ack                                                                                         | 2026-05-12 slot 8 carry-forward (cross_cutting #4 + manifest Phase 3)                                                                                                    |
| Slot 8 — Phase 0h sync-script first-execution                                                | ⚪ DEFERRED — code shipped (deployment-service@`fc1cfa0` by Harsh slot 4); first-execution = post-Phase-2.6 cutover                              | 2026-05-12 slot 8 carry-forward; first exec lands in Phase 2.6 cutover window (2026-05-15→05-19)                                                                         |
| Q1-Q5 MTDS pipeline_mode (Phase 4.MTDS blocked)                                              | 🟡 BLOCKED on operator decision (PM@`237d00b7`)                                                                                                  | 2026-05-12 slot 3 (`code_freeze` Phase 1.E audit — Phase 4.MTDS triage)                                                                                                  |
| VIX 15m pipeline_mode finding (PM@`a5e5aa4d`)                                                | ⚪ NOTED — issue doc filed, no owner                                                                                                             | 2026-05-12 reserve list (post-cutover)                                                                                                                                   |
| footystats pipeline_mode gap (PM@`6ede1e01`)                                                 | ⚪ NOTED — issue doc filed, no owner                                                                                                             | 2026-05-12 reserve list (post-cutover)                                                                                                                                   |

**Sweep complete**: every line above either ✅ DONE with commit citation or has a named 2026-05-12 successor in
[`work_split_2026_05_12_ikenna.md`](work_split_2026_05_12_ikenna.md) /
[`continuation_prompts_2026_05_12.md`](continuation_prompts_2026_05_12.md). No orphans remain after this scoreboard.

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
