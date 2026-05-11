---
title: Harsh's daily work-split — 2026-05-11 (Phase 1 code-freeze push to 2026-05-15 freeze gate)
type: coordination-doc
status: active
created: 2026-05-11
deadline: 2026-05-15
horizon: 4-day cycle
companion_to: plans/active/work_split_2026_05_11_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Harsh's daily work-split — 2026-05-11

> **Companion (Ikenna side):** [`work_split_2026_05_11_ikenna.md`](work_split_2026_05_11_ikenna.md). Cross-side
> handshakes are mirrored in both files; edit one, mirror the other.

## Why this split exists today

We are 4 days from the **Phase 1 code-freeze gate (2026-05-15)** of
[`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md). After
that gate fires, Phase 2 (one-shot physical migrations 2026-05-15→05-19) and Phase 3 (resume backfills 2026-05-19→05-23)
run in sequence. **Every Phase 1 blocker that misses the gate forces a re-migration tax** — May-23 live-DeFi cutover at
risk.

This cycle's Harsh scope: drive the **implementation-from-spec / mechanical / single-repo / per-asset-group / audit**
half of Phase 1 to done. Ikenna covers cross-cutting design + governance + multi-repo coordination in
[`work_split_2026_05_11_ikenna.md`](work_split_2026_05_11_ikenna.md).

**Hardest deadline this cycle**: features-repo consolidation Phase 7 lands by **2026-05-13** (2 days), unblocking Ikenna
slot 4 + this side's slot 5 live-pipeline service wiring.

**Rolled forward from yesterday's stale splits** (`work_split_2026_05_08_harsh.md` was never archived per the EOD rule —
flag for sweep): features-consolidation Phase 4-7 carryover, wave3x Tracks B/C/D/E, bucket-name SSOT.

## Working model

**Model A — 5 thematic slots** (slot 1 = main orchestrator + on-call, slots 2-6 = thematic implementers). Phase 1 work
is pre-decided via the 7 blocker plans, so the dynamic Model B (1-main + dynamic spawn) overhead isn't justified. Tabs
run to their done-definitions, not to 2026-05-15.

## Today's slot assignments

> **Per-tab worktree model**
> ([`codex/05-infrastructure/per-tab-worktrees.md`](../../codex/05-infrastructure/per-tab-worktrees.md)). Each slot is a
> permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/hk/<N>`. **Slot count: 6 — provisioned
> 2026-05-11 via `setup-tab-worktrees.sh --init --slots 6`** (`$USER=hk` → branches `tab/hk/1`..`tab/hk/6`, all at the
> `live-defi-rollout` tip; 6 covers the 5 active themes + 1 reserve; grow with `--add-slot` if peak parallel work
> exceeds). Before any slot reassignment from yesterday's theme, run `--reset-slot <N>`.

| Slot | Theme                                                                                                               | Plan-of-record                                                                                                                                                                                                                        | AI-day budget |
| ---- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 1    | main orchestrator + on-call                                                                                         | [LEDGER](../../harsh_orchestrator/LEDGER.md) + ping triage + workspace QG sweep coordination                                                                                                                                          | continuous    |
| 2    | **HARDEST DEADLINE 2026-05-13** — features-repo consolidation Phase 4-7                                             | [features_repo_consolidation_2026_05_08.md](features_repo_consolidation_2026_05_08.md) Phase 4-7                                                                                                                                      | ~5            |
| 3    | wave3x Tracks B/C/D/E parallel                                                                                      | [wave3x_residual_ssots_2026_05_08.md](wave3x_residual_ssots_2026_05_08.md) Tracks B/C/D/E                                                                                                                                             | ~5            |
| 4    | bucket-name SSOT canonicalisation + per-asset-group available_at adapter wiring                                     | [bucket_name_ssot_canonicalisation_2026_05_10.md](bucket_name_ssot_canonicalisation_2026_05_10.md) + [available_at_lookahead_bias_completion_2026_05_08.md](available_at_lookahead_bias_completion_2026_05_08.md) Phase 1 per-adapter | ~3            |
| 5    | live pipeline Phase 3-5 service wiring (post features-consolidation unblock; mid-cycle activation) + Phase 13/14/15 | [live_pipeline_mtds_mdps_features_2026_05_08.md](live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 3-5 + 13-15                                                                                                                    | ~5            |
| 6    | workspace QG green sweep + codex audit pass + Phase 1 freeze-gate items 8 + 9                                       | [code_freeze_migrate_backfill_sequencing_2026_05_10.md](code_freeze_migrate_backfill_sequencing_2026_05_10.md) freeze-gate items 8 + 9                                                                                                | ~3            |

**Total active scope: ~21 AI-days across 5 thematic slots over a 4-day cycle.** Beefier than thin per CLAUDE.md sizing —
under-utilisation is fine, mid-cycle collision is not.

## Tab registry (per-tab full brief)

### Slot 1 — main orchestrator + on-call

- **Identity**: this session (Harsh's main orchestrator agent, slot 1 worktree at `.tabs/1/`).
- **Scope**:
  - **P0**. Daily ledger sweep at start: read `harsh_orchestrator/_agent_pings.md` + `plans/active/_agent_pings.md`,
    triage 🟡 BLOCKED Qs >24h, ack STARTED pings, verify DONE pings.
  - **P0**. Cross-side coordination: route Harsh slot 2 (features-consolidation Phase 7 ship) cross-side ping when it
    lands so Ikenna slot 4 unblocks live-pipeline implementation.
  - **P0**. Workspace QG sweep coordination: when slot 6 ships any QG-green checkpoint, validate Phase 1 gate item 8
    (workspace QG green) + escalate any failure attribution per CLAUDE.md "QG failure attribution" rule.
  - **P1**. Stale work-split sweep: archive `work_split_2026_05_08_harsh.md` (3 days old) to `plans/archive/`. Roll
    forward open items.
  - **P1**. Operator Q&A dispatch: route 🟡 BLOCKED Qs from slots 2-6 to operator chat; route operator decisions back to
    plan-of-record `## Open questions` sections.
- **Plan-of-record**: this file + [LEDGER](../../harsh_orchestrator/LEDGER.md) +
  [code_freeze](code_freeze_migrate_backfill_sequencing_2026_05_10.md).
- **Repos owned (collision boundary)**: `unified-trading-pm/plans/active/work_split_2026_05_11_harsh.md` +
  `unified-trading-pm/harsh_orchestrator/*` + `unified-trading-pm/plans/active/_agent_pings.md` (cross-side ledger
  curation). Does NOT touch UAC / UTL / service repos.
- **Read-first**: CLAUDE.md § "Daily Work-Split Process" + § "Findings Triage Discipline" + § "CI Verification After
  Every Push" + § "Plans Run To Actual Completion".
- **Sub-agent fan-out**: minimal — main agent does NOT implement.
- **Done-definition**:
  - ✅ Ledger sweep done at start + every 4-6 hours.
  - ✅ Cross-side handshake pings landed correctly when slot 2/3/4/5/6 ship hard-gate items.
  - ✅ Yesterday's stale work-splits archived.

### Slot 2 — Features-repo consolidation Phase 4-7 (HARDEST DEADLINE 2026-05-13)

- **Identity**: `harsh-features-consolidation-tab` (slot 2 worktree at `.tabs/2/`).
- **Scope** (per [features_repo_consolidation_2026_05_08.md](features_repo_consolidation_2026_05_08.md), Phase 0-3
  already shipped per yesterday's LEDGER):
  - **P0 Phase 4** — Import rewrite: 11 external Python imports + 51 string refs (per Phase 0 pre-audit @1de574b4 —
    smaller than originally scoped). Workspace-grep audit table required per Citadel-Grade § 6.
  - **P0 Phase 5** — Lift cross-family helpers to UTL: watermark+grace fan-in, available_at stamping (coordinate with
    Ikenna slot 3 Phase 0 + Harsh slot 4), LookaheadBiasError gate, NaN write-gate, ManifestFreshnessCache adoption.
  - **P0 Phase 6** — pyproject unification + test/script consolidation. Parallel with Phase 5.
  - **P0 Phase 7 — DEADLINE 2026-05-13** — Single features-service deployable; 8 child repos archived to read-only.
    Cross-side ping when shipped — Ikenna slot 4 promotes live-pipeline Phase 4-5 design to implementation.
  - **P1 Phase 8** — Manifest migration + version bump (one-shot script).
  - **P2 Phase 9** — Health-API + live-mode flavors (deferred post-Phase-7 per existing plan body).
- **Plan-of-record**: [`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md).
- **Repos owned**: 8 features-\* services (calendar, commodity, cross-instrument, delta-one, multi-timeframe, onchain,
  sports, volatility) → `features-service` (consolidated) + `unified-trading-library` (cross-family helper lifts) +
  `workspace-manifest.json` (registration of features-service URL) + PM (plan flips + codex SSOT updates).
- **Read-first**: CLAUDE.md § "ARCHITECTURE 2026-05-08 — Live pipeline" + § "Shard-granularity SSOT" + §
  "Post-Plan-Phase Codex Audit" + features_repo_consolidation Phase 0 pre-audit manifest @1de574b4 (1286 lines, full
  blast radius).
- **Sub-agent fan-out**: 4 parallel at boot:
  1. Phase 4 import rewrite (mechanical; pre-audit lists exact 11+51 sites).
  2. Phase 5 cross-family helper lift to UTL (~5 helpers).
  3. Phase 6 pyproject unification + test consolidation (parallel with Phase 5).
  4. Phase 7 archive coordination (writes deprecation banners + workspace-manifest registration).
- **Collision risk**:
  - **vs Ikenna slot 4 (live-pipeline design)**: slot 4 imports the consolidated features-service for Phase 5 contract
    types. **Hard sync**: ship Phase 7 ASAP; cross-side ping immediately when done.
  - **vs Harsh slot 5 (live-pipeline service wiring)**: slot 5 cannot start Phase 3-5 implementation until Phase 7
    lands. Slot 5 prepares scaffolds while gated.
  - **vs Harsh slot 6 (workspace QG)**: 8-repo archival → workspace-manifest changes; QG sweep validates new shape.
- **Done-definition**:
  - ✅ Phase 4 import rewrite green; workspace-grep shows zero references to old per-repo paths.
  - ✅ Phase 5 cross-family helpers in UTL with tests.
  - ✅ Phase 6 pyproject + test consolidation done.
  - ✅ Phase 7 features-service deployable; 8 child repos archived (deprecation banners + workspace-manifest entry
    pointing at consolidated repo); live `pip install -e ../features-service` succeeds.
- **Full-execution criterion**:
  - ✅ A live `cd features-service && bash scripts/quality-gates.sh` returns green; ALL 5 asset_groups' feature
    calculators import + run.
    - **What ran**: full QG sweep including pytest + basedpyright + ruff.
    - **Verification**: STATUS_OK exit code; sample feature compute on a test fixture returns correct shape.
  - ✅ Cross-side ping in `plans/active/_agent_pings.md` posted when Phase 7 ships.

### Slot 3 — Wave3x Tracks B/C/D/E parallel

- **Identity**: `harsh-wave3x-tab` (slot 3 worktree at `.tabs/3/`).
- **Scope** (per [wave3x_residual_ssots_2026_05_08.md](wave3x_residual_ssots_2026_05_08.md); Track A already shipped
  UAC@bdc84ed):
  - **P0 Track B** — Sports per-source SSOTs: `UNDERSTAT_COVERED_LEAGUES` + `TRANSFER_WINDOWS` + footystats season
    bounds. UAC `unified_api_contracts/canonical/sports/`. ~2d.
  - **P0 Track C** — `reconcile_legacy_blank_to_typed_reason.py` reconciler script for instruments-service. Walks
    manifest looking for blank `error_reason` rows; classifies via UAC `EMPTY_CONFIRMED_REASONS` taxonomy. ~1d.
  - **P0 Track D — ANTI-SEQUENCING CRITICAL** — Zero-activity-bar adapter audit across MTDS, MDPS, 8 features-\*
    services. Per [code_freeze:300](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L300) anti-sequencing rule: if
    Track D finds new shard atom dimension or new error reason needed → forces second migration walk. MUST complete
    before Phase 2 freeze. ~2d.
  - **P0 Track E** — Sports per-source stamping helpers: `stamp_available_at_lineups` + `stamp_available_at_injuries`
    - `stamp_available_at_post_match_cascade` + `stamp_available_at_odds`. UTL
      `unified_trading_library/availability_stamping/`. Folded into available_at Phase 1 per
      [wave3x:12-20](wave3x_residual_ssots_2026_05_08.md#L12-L20) — coordinate with Ikenna slot 3. ~1-2d.
  - **P1 Track A UTL** — Wire `legacy_reason_classifier.py` for half-day + session-hours from already-shipped
    UAC@bdc84ed. ~0.5d.
- **Plan-of-record**: [`wave3x_residual_ssots_2026_05_08.md`](wave3x_residual_ssots_2026_05_08.md).
- **Repos owned**: `unified-api-contracts` (Tracks A+B SSOTs) + `unified-trading-library` (Tracks A+E stamping + Track C
  reconciler infrastructure) + `instruments-service` (Track C reconciler script) + MTDS / MDPS / 8 features-\* services
  (Track D adapter audit — read-only, finding-only).
- **Read-first**: CLAUDE.md § "Sports source coverage windows" + § "Honest absence vs fake placeholders" + §
  "Four-category empty-output decision" + § "available_at is per-row, write-time, equal to live-pipeline-arrival" +
  Wave3x plan body.
- **Sub-agent fan-out**: 5 parallel at boot (one per Track A UTL / B / C / D / E). Track D especially benefits from
  10-12 sub-sub-agents (one per service repo) for the read-only audit pass.
- **Collision risk**:
  - **vs Ikenna slot 3 (available_at)**: Track E folds into available_at Phase 1; slot 3 ships per-source helpers, slot
    coordinates integration via plan-of-record cross-references.
  - **vs Harsh slot 2 (features-consolidation)**: Track D audits 8 features-\* services that are mid-consolidation;
    coordinate timing — Track D audit can run on archived snapshots OR on the consolidated state. Recommend the latter
    after Phase 4 ships.
- **Done-definition**:
  - ✅ Track B 3 SSOTs shipped + tests + cross-references in CLAUDE.md sports section.
  - ✅ Track C reconciler shipped; dry-run on production manifest successful (no blank reasons reclassified
    incorrectly).
  - ✅ Track D audit complete; findings doc filed in `plans/active/issues/wave3x_track_d_findings_2026_05_11.md` with
    per-service classification.
  - ✅ Track E 4 stamping helpers shipped + tests; integrated into available_at Phase 1 by Ikenna slot 3.
- **Full-execution criterion**:
  - ✅ Track C reconciler dry-run on the canonical manifest produces a delta CSV with zero blank-reason rows after
    classification.
    - **What ran**: `python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --dry-run`.
    - **Verification**: output CSV has 100% of input blank-reason rows mapped to a typed reason.
  - ✅ Track D findings doc enumerates every adapter's classification per CLAUDE.md "Four-category empty-output
    decision" (A/B/C/D categories).

### Slot 4 — Bucket-name SSOT + per-asset-group available_at adapter wiring

- **Identity**: `harsh-bucket-and-adapter-tab` (slot 4 worktree at `.tabs/4/`).
- **Scope**:
  - **P0 bucket-name SSOT** (per
    [bucket_name_ssot_canonicalisation_2026_05_10.md](bucket_name_ssot_canonicalisation_2026_05_10.md); NEVER executed
    per memory):
    - Decide canonical SSOT layer: yaml as canonical (recommendation per plan line 48); migrate per-family `config.py`
      to `bucket_naming.resolve_bucket_name()` calls.
    - Workspace QG step for inline `f"gs://{bucket}/..."` formatters.
    - Extend yaml-vs-resolver parity unit test.
    - Plan-flip audit table verifying zero drift.
  - **P0 per-asset-group available_at adapter wiring** (per
    [available_at_lookahead_bias_completion_2026_05_08.md](available_at_lookahead_bias_completion_2026_05_08.md) Phase 1
    remaining halves; CeFi already shipped MTDS@4a00bd5):
    - Sports adapter stamping (folded with Wave3x Track E from slot 3 — wire Track E's UTL helpers into MTDS sports
      adapters).
    - Coordinate hand-off pattern with Ikenna slot 3 once Phase 0 bar boundary contract lands.
- **Plan-of-record**:
  [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md)
  - [`available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md) Phase
    1 per-adapter halves.
- **Repos owned**: `unified-api-contracts` (bucket_naming resolver) + `unified-trading-library` (QG step) +
  `features-service` (per-family config.py — coordinate with Harsh slot 2 on file paths) + `deployment-service`
  (setup-buckets.sh) + `market-tick-data-service` (sports adapter stamping wiring) + PM (plan flips + audit table).
- **Read-first**: CLAUDE.md § "Bucket-name SSOT" memory entry + § "available_at is per-row" + § "Plans Run To Actual
  Completion" (bucket-SSOT triple-drift incident from Tab 4 close-out 2026-05-08).
- **Sub-agent fan-out**: 2 parallel at boot:
  1. Bucket-name SSOT migration (mechanical 3-layer collapse).
  2. Sports adapter stamping wiring (gated on Wave3x slot 3 Track E + Ikenna slot 3 Phase 0).
- **Collision risk**:
  - **vs Harsh slot 2 (features-consolidation)**: per-family `config.py` paths are mid-consolidation. **Hard sync**:
    bucket-name migration runs AFTER Phase 4 import rewrite stabilises (or runs against the consolidated state).
  - **vs Harsh slot 3 (Wave3x Track E)**: sports stamping helpers come from Track E. Wait for Track E ship signal.
  - **vs Ikenna slot 3 (available_at Phase 0)**: per-adapter wiring needs Phase 0 bar boundary contract. Wait for
    cross-side ping.
- **Done-definition**:
  - ✅ Bucket-name SSOT consolidated to single UAC layer; per-family config.py duplicates deleted.
  - ✅ Workspace QG step for inline bucket-name formatters added; CI green.
  - ✅ Sports adapter stamping wired to MTDS; LookaheadBiasError strict-mode green for sports features-\* compute.
- **Full-execution criterion**:
  - ✅ A live
    `python -c "from unified_api_contracts.bucket_naming import resolve_bucket_name; print(resolve_bucket_name('cefi', 'tradfi'))"`
    returns the canonical bucket name; per-family config.py imports raise `DeprecationWarning`.
    - **What ran**: workspace-wide import + grep audit.
    - **Verification**: zero string literals matching `gs://.+-` outside the resolver module.

### Slot 5 — Live pipeline Phase 3-5 service wiring (gated, mid-cycle activation)

- **Identity**: `harsh-live-pipeline-impl-tab` (slot 5 worktree at `.tabs/5/`).
- **Scope** (per [live_pipeline_mtds_mdps_features_2026_05_08.md](live_pipeline_mtds_mdps_features_2026_05_08.md); Phase
  3-5 IMPLEMENTATION gated on Harsh slot 2 features-consolidation Phase 7 + Ikenna slot 4 Phase 4-5 design):
  - **PRE-GATE work** (do while features-consolidation lands):
    - Read live-pipeline Phase 3-5 design docs + UTL stubs from Ikenna slot 4 as they ship.
    - Prep MTDS websocket client integration scaffolds (Phase 3).
    - Prep MDPS streaming aggregator consumer hooks (Phase 4).
    - Prep features-service per-asset-group flavors (Phase 5).
    - Build test scaffolds + integration test fixtures.
  - **POST-GATE work** (when Harsh slot 2 ships features-consolidation Phase 7 + Ikenna slot 4 ships Phase 4-5 design):
    - **P0 Phase 3** — MTDS websocket rollout per asset_group.
    - **P0 Phase 4** — MDPS streaming aggregation implementation.
    - **P0 Phase 5** — features-service asset-scoped streaming implementation.
  - **POST-PHASE-3-5 (likely next-cycle)**:
    - **P1 Phase 13** — VM launchers + watchdog dict updates.
    - **P1 Phase 14** — Codex SSOT updates.
    - **P1 Phase 15** — QG sweep + smoke.
- **Plan-of-record**: [`live_pipeline_mtds_mdps_features_2026_05_08.md`](live_pipeline_mtds_mdps_features_2026_05_08.md)
  Phases 3-5 + 13-15.
- **Repos owned**: `market-tick-data-service` (Phase 3 websocket) + `market-data-processing-service` (Phase 4 streaming
  aggregator) + `features-service` (Phase 5 streaming consumers — coordinate file paths with Harsh slot 2) +
  `deployment-service/scripts/vm/` (Phase 13 launchers) + `deployment-service/scripts/vm/vm_zombie_watchdog.py` (dict
  updates) + PM (codex SSOTs + plan flips + Phase 15 QG sweep results).
- **Read-first**: CLAUDE.md § "ARCHITECTURE 2026-05-08 — Live pipeline" + § "Per-VM shard isolation for concurrent
  backfills" + § "VM launcher script SSOT" + § "VM Naming Convention" + the live-pipeline plan body.
- **Sub-agent fan-out**:
  - Pre-gate: 3 parallel scaffolders (one per phase 3/4/5).
  - Post-gate: 5 parallel implementers (one per asset_group, since each phase has 5 asset_group flavors).
- **Collision risk**:
  - **vs Harsh slot 2 (features-consolidation)**: Phase 5 features-service consumers live in same repo Harsh slot 2 is
    consolidating. **Hard sync**: wait for Phase 7 ship; merge against consolidated state.
  - **vs Harsh slot 6 (workspace QG)**: Phase 15 QG sweep is shared scope; coordinate which slot owns the final QG run.
- **Done-definition**:
  - ✅ Pre-gate scaffolds + integration fixtures shipped.
  - ✅ Post-gate (assuming features-consolidation ships by 2026-05-13): Phase 3 + 4 + 5 service wiring shipped per
    asset_group.
  - ✅ Phase 13/14/15 may slip to next-cycle; explicit DEFERRED-AFTER-PHASE-3-5 annotation if so.
- **Full-execution criterion**:
  - ✅ A live MTDS→MDPS→features-service in-process handoff smoke (one asset_group, one minute of synthetic data) shows
    end-to-end live emission.
    - **What ran**: smoke harness against `tier 0` local stack.
    - **Verification**: STARTED + progress + STOPPED events landed in event stream; output parquet has populated rows
      with correct `pipeline_mode=live_websocket` partition.

### Slot 6 — Workspace QG green sweep + codex audit pass + freeze-gate items 8 + 9

- **Identity**: `harsh-workspace-qg-tab` (slot 6 worktree at `.tabs/6/`).
- **Scope** (per [code_freeze:135-148](code_freeze_migrate_backfill_sequencing_2026_05_10.md#L135-L148) freeze-gate
  items 8 + 9 — runs all 4 days, validates on-disk state per slot completion):
  - **P0 freeze-gate item 8** — Workspace QG green across UAC + UTL + every service repo; basedpyright clean; no
    `# type: ignore` masking architectural violations. Run after each slot ships a shippable unit; validate.
  - **P0 freeze-gate item 9** — Codex SSOT audit pass per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE. Walk every
    codex doc the Phase 1 plans should have touched; verify the doc layer reflects the frozen schema state.
  - **P1 cross-cutting** — When workspace QG fails, attribute the failure per CLAUDE.md "QG failure attribution" rule:
    if YOUR commit broke it (slot 2-5), fix in same logical unit; if foreign agent broke it, file an issue doc and
    continue.
  - **P1 phantom audit** — Run
    `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group all --dry-run` periodically;
    ensure the 354 residual phantoms (from 2026-05-04 baseline) haven't grown.
- **Plan-of-record**:
  [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
  freeze-gate items 8 + 9.
- **Repos owned**: read-only across UAC + UTL + every service repo + codex docs. Issue docs filed in
  `plans/active/issues/` for any failure attribution.
- **Read-first**: CLAUDE.md § "Post-Plan-Phase Codex Audit" + § "QG failure attribution" + § "Manifest phantom audit" +
  § "CI Verification After Every Push".
- **Sub-agent fan-out**: 1-2 sub-agents (one per QG sweep run; one per codex audit pass).
- **Collision risk**:
  - **vs every other slot**: read-only doesn't cause collision; but findings filed in `issues/` may overlap. Coordinate
    via slot 1.
- **Done-definition**:
  - ✅ Workspace QG green at every Phase 1 freeze-gate audit by slot 1.
  - ✅ Codex SSOT audit pass complete; missing/stale docs flagged per "Post-Plan-Phase Codex Audit" rule.
  - ✅ Phantom audit count ≤ 354 residual (no growth from 2026-05-04 baseline).
- **Full-execution criterion**:
  - ✅ A workspace-wide QG run
    (`for repo in unified-api-contracts unified-trading-library market-tick-data-service ...; do cd $repo && bash scripts/quality-gates.sh; done`)
    returns green for every active repo.
    - **What ran**: full sequential QG sweep.
    - **Verification**: zero non-zero exit codes; QG output logs archived to
      `plans/active/issues/qg_sweep_2026_05_11_*.md`.

## Cross-tab handshakes (within Harsh side)

- **Slot 2 → Slot 5**: features-consolidation Phase 7 ships → slot 5 unblocks live-pipeline Phase 3-5 implementation.
- **Slot 3 (Track E) → Slot 4**: sports stamping helpers ship → slot 4 wires them into MTDS sports adapters.
- **Slot 2 → Slot 4**: per-family config.py paths stabilise (Phase 4 import rewrite) → slot 4 starts bucket-name SSOT
  migration.
- **Slot 6 → Slot 1**: any QG failure attributed to a Harsh-side commit → slot 1 routes to operator chat for resolution.

## Cross-side handshakes (Harsh ↔ Ikenna — mirrored in [ikenna's split](work_split_2026_05_11_ikenna.md))

- **Hard-gate: Harsh slot 2 → Ikenna slot 4**. features-consolidation Phase 7 ships (deadline 2026-05-13). Ikenna slot 4
  promotes live-pipeline Phase 4-5 design-ahead commits to full implementation. **Signal**: Harsh slot 2 cross-side ping
  in [`plans/active/_agent_pings.md`](_agent_pings.md) when Phase 7 lands.
- **Hard-gate: Ikenna slot 3 (available_at Phase 0) → Harsh slot 4 (per-adapter wiring)**. Ikenna ships Phase 0 bar
  boundary contract + UTL helper. Harsh slot 4 unblocks Phase 1 per-asset-group adapter stamping. **Signal**: Ikenna
  slot 3 cross-side ping when Phase 0 lands.
- **Hard-gate: Ikenna slot 2 (writegate v8 schema) → Harsh slot 6 (workspace QG sweep)**. Ikenna ships v8 columns; Harsh
  slot 6 runs workspace-wide QG green check. **Signal**: Ikenna slot 2 cross-side ping when Phase 5.7 lands.
- **Coordinate: Harsh slot 3 (Wave3x Track E) ↔ Ikenna slot 3 (AVAILABILITY_AT_SEMANTICS audit)**. Track E folded into
  available_at Phase 1 — Harsh ships per-source helpers, Ikenna integrates into the audit.

## Collision-risk callouts

| Files / dirs                                                              | Collision tabs                                                                          | Mitigation                                                                                    |
| ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `features-service/features_service/*`                                     | slot 2 (consolidation), slot 4 (config.py per-family), slot 5 (live-pipeline consumers) | Slot 2 sole writer until Phase 7; slots 4 + 5 wait for hand-off ping.                         |
| `unified-api-contracts/unified_api_contracts/canonical/sports/*`          | slot 3 (Wave3x Track B SSOTs)                                                           | Slot 3 sole writer; coordinates with Ikenna slot 5 if any DeFi/cross-asset overlap.           |
| `unified-api-contracts/unified_api_contracts/bucket_naming.py`            | slot 4 (bucket-name SSOT)                                                               | Slot 4 sole writer.                                                                           |
| `unified-trading-library/unified_trading_library/availability_stamping/*` | slot 3 (Track E sports stamping) + Ikenna slot 3 (Phase 0 helpers)                      | Distinct files within stamping/; both can edit in parallel; surgical `git add -p`.            |
| `market-tick-data-service/*`                                              | slot 4 (sports adapter wiring), slot 5 (Phase 3 websocket), slot 6 (audit, read-only)   | Distinct files; slots 4 + 5 surgical staging.                                                 |
| `instruments-service/scripts/*`                                           | slot 3 (Track C reconciler)                                                             | Slot 3 sole writer; new script file, no collision.                                            |
| `unified-trading-pm/plans/active/*.md`                                    | All slots (plan flips + DONE blocks)                                                    | Each slot edits ONLY its plan-of-record; surgical `git add -p` mandatory; never `git add -A`. |
| `deployment-service/scripts/vm/*.sh`                                      | slot 5 (Phase 13 launchers) + slot 6 (audit only)                                       | Slot 5 sole writer.                                                                           |
| `unified-trading-pm/codex/02-data/*`                                      | slot 6 (codex audit pass) — read most + may stub follow-up                              | Slot 6 owns audit; if audit finds stale doc, file as issue OR fix in-place if scope-clear.    |

**Per-slot worktree isolation** makes cross-slot races on `.git/index` unrepresentable. The table above is for
SHARED-FILE-CONTENT collisions when slots push and pull each other's commits.

## Spawn prompts (paste-ready into fresh Claude Code / Cursor tabs)

> **Operator usage**: open a fresh Cursor / Claude Code tab inside the slot N worktree
> (`cd ${WORKSPACE_ROOT}/.tabs/<N>/`), then paste the matching prompt. The agent reads the slot's plan-of-record +
> LEDGER bootstrap on its own.

> **Boot pre-req** (one-time on Harsh's machine, before any slot 2-6 spawn):
>
> ```bash
> # 1. Verify workspace is clean across all repos on live-defi-rollout (per the precondition in
> #    codex/05-infrastructure/per-tab-worktrees.md Step 0).
> # 2. Provision 6 slot worktrees:
> bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 6   ($USER=hk on this machine → tab/hk/1..6; already provisioned 2026-05-11)
> ```
>
> The `--init` step provisions per-repo worktrees + per-slot `.envrc` (PREK_CACHE_DIR isolation per foot-gun #4) AND
> auto-copies `unified-trading-system-repos.code-workspace` into each slot dir (so `File → Open Workspace from File →
> .tabs/<N>/unified-trading-system-repos.code-workspace` works immediately for the multi-root view; or just
> `File → Open Folder → .tabs/<N>/` for flat single-root view — both produce identical isolation).
>
> Verify in a Cursor terminal of each new window:
>
> ```bash
> pwd                                                              # → .../.tabs/<N>
> git -C unified-trading-pm rev-parse --abbrev-ref HEAD            # → tab/hk/<N>
> ```
>
> Full 7-step paste-ready recipe at
> [`codex/05-infrastructure/per-tab-worktrees.md`](../../codex/05-infrastructure/per-tab-worktrees.md).

### Slot 2 spawn prompt (features-repo consolidation Phase 4-7 — DEADLINE 2026-05-13)

```text
You are Tab 2 — a sub-agent spawned by Harsh's main orchestrator agent (slot 1, a separate
Claude Code session on the SAME machine).

Your slot is 2. Your worktree is at ${WORKSPACE_ROOT}/.tabs/2/ on branch tab/hk/2.
Today's theme for slot 2: features-repo consolidation Phase 4-7 — HARDEST DEADLINE 2026-05-13
(2 days from today).

BEFORE doing anything else, read in order:
  1. plans/active/work_split_2026_05_11_harsh.md § "Slot 2 — Features-repo consolidation ..." — full task brief.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards.
  3. unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md — 3-tier isolation model.
  4. unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md — reconciliation
     protocol when your push surfaces a rebase conflict.
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  6. plans/active/features_repo_consolidation_2026_05_08.md — your plan-of-record.
  7. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella you serve.
  8. The Phase 0 pre-audit manifest at PM@1de574b4 (1286 lines / 11 ext imports + 51 string refs).

Your agent-tag for ping-ledger entries: harsh-features-consolidation-tab.

ORCHESTRATION RULES (full text in CLAUDE.md):
  1. Per-slot worktree — cross-slot races unrepresentable. WITHIN your slot, sub-agents you spawn
     share your worktree's .git/index, so pre-commit check (git status + git diff --cached --stat
     NO PATH ARG) still mandatory before EVERY commit. Use `git add -p` for shared files; never
     `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into features_repo_consolidation plan's `## Open
     questions` section (status 🟡 BLOCKED), append ping in harsh_orchestrator/_agent_pings.md,
     continue with what you CAN do.
  3. Conditional push — per shippable unit: commit locally, fetch + check incoming, zero
     incoming → push, any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — checkbox flip + `<repo>@<sha>` evidence
     stamped in body, NOT batched at session end.
  5. Findings Triage Discipline (HARD RULE) — case-1-to-5 routing per CLAUDE.md.
  6. CROSS-SIDE PING MANDATORY when Phase 7 lands (features-service deployable; 8 child repos
     archived) so Ikenna slot 4 can promote live-pipeline Phase 4-5 design to implementation.

YOUR TASK: ship features_repo_consolidation Phase 4-7 by 2026-05-13. Full task brief in this
work-split § "Slot 2".

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push.
Final: append a "DONE-2026-05-11" block at the bottom of features_repo_consolidation plan body
listing every code + plan-flip commit sha. EOD-audit (per CLAUDE.md "Capture Discoveries As Plan
Todos Immediately" § "End-of-cycle audit clause"): every deferral in your final summary MUST
already be a `- [ ]` plan todo or a `**DEFERRED**` annotation in plans/active/. Run
`grep -n "<distinctive phrase>" plans/active/*.md plans/active/issues/*.md` per deferral
line — match → cite file:line in summary; no match → STOP, add the todo, push the flip,
then resume. Then go quiet — don't pick up new work autonomously.
```

### Slot 3 spawn prompt (Wave3x Tracks B/C/D/E)

```text
You are Tab 3 — spawned by Harsh's main orchestrator (slot 1).

Your slot is 3. Worktree: ${WORKSPACE_ROOT}/.tabs/3/ on branch tab/hk/3.
Theme: Wave3x Tracks B/C/D/E parallel — sports per-source SSOTs + reconciler +
zero-activity-bar adapter audit + sports stamping cascade.

BEFORE doing anything: read in order:
  1. plans/active/work_split_2026_05_11_harsh.md § "Slot 3 — Wave3x ..." — full task brief.
  2-5. (standard: CLAUDE.md, per-tab-worktrees, plan-aware-merge, SUB_AGENT_MANDATORY_RULES).
  6. plans/active/wave3x_residual_ssots_2026_05_08.md — your plan-of-record.
  7. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella.

Your agent-tag: harsh-wave3x-tab.

ORCHESTRATION RULES: same as slot 2.

Track D ANTI-SEQUENCING CRITICAL: must complete BEFORE Phase 2 freeze (2026-05-15) per
code_freeze:300. If audit finds new shard atom dimension OR new error reason needed,
escalate to slot 1 + Ikenna slot 5 (Phase 1.E sequencing) IMMEDIATELY — they decide whether
the new finding lands in v8 schema (Ikenna slot 2) or is deferred post-cutover.

Per CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" HARD RULE: Track D adapter audit MUST
read consumer code + check runtime-resolved patterns; do NOT conclude "missing" from literal
grep alone.

YOUR TASK: full task brief in this work-split § "Slot 3".

REPORT-BACK: same as slot 2.
```

### Slot 4 spawn prompt (bucket-name SSOT + per-adapter wiring)

```text
You are Tab 4 — spawned by Harsh's main orchestrator (slot 1).

Your slot is 4. Worktree: ${WORKSPACE_ROOT}/.tabs/4/ on branch tab/hk/4.
Theme: bucket-name SSOT canonicalisation + per-asset-group available_at adapter wiring (sports).

BEFORE doing anything: read in order:
  1. plans/active/work_split_2026_05_11_harsh.md § "Slot 4 — Bucket-name SSOT ..." — full task brief.
  2-5. (standard).
  6. plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md — primary plan-of-record.
  7. plans/active/available_at_lookahead_bias_completion_2026_05_08.md — secondary plan-of-record.

Your agent-tag: harsh-bucket-and-adapter-tab.

ORCHESTRATION RULES: same as slot 2.

Bucket-name SSOT triple-drift incident reference (2026-05-08 Tab 4 close-out): there are
THREE current SSOT layers (yaml + per-family config.py + UTL resolver). Decision per plan
body: yaml is canonical; collapse the other two. Audit each call site before deletion.

Sports adapter stamping WAITS on (a) Wave3x slot 3 Track E ship (UTL helpers); (b) Ikenna
slot 3 Phase 0 ship (bar boundary contract). Wait for cross-side pings. While waiting,
prep test scaffolds.

YOUR TASK: full task brief in this work-split § "Slot 4".

REPORT-BACK: same as slot 2.
```

### Slot 5 spawn prompt (live-pipeline Phase 3-5 implementation, gated)

```text
You are Tab 5 — spawned by Harsh's main orchestrator (slot 1).

Your slot is 5. Worktree: ${WORKSPACE_ROOT}/.tabs/5/ on branch tab/hk/5.
Theme: live-pipeline Phase 3-5 service wiring (post features-consolidation unblock) + Phase
13/14/15 (VM launchers + codex sweep + QG sweep).

BEFORE doing anything: read in order:
  1. plans/active/work_split_2026_05_11_harsh.md § "Slot 5 — Live pipeline ..." — full task brief.
  2-5. (standard).
  6. plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md — your plan-of-record.
  7. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — sequencing umbrella.

Your agent-tag: harsh-live-pipeline-impl-tab.

ORCHESTRATION RULES: same as slot 2.

GATED START: Phase 3-5 IMPLEMENTATION blocked until BOTH (a) Harsh slot 2 ships features-
consolidation Phase 7 AND (b) Ikenna slot 4 ships Phase 4-5 design-ahead commits. While
gated, ship pre-gate scaffolds + integration test fixtures (no actual implementation).
When BOTH cross-side pings land, promote scaffolds to implementation.

YOUR TASK: full task brief in this work-split § "Slot 5".

REPORT-BACK: same as slot 2.
```

### Slot 6 spawn prompt (workspace QG green sweep + codex audit)

```text
You are Tab 6 — spawned by Harsh's main orchestrator (slot 1).

Your slot is 6. Worktree: ${WORKSPACE_ROOT}/.tabs/6/ on branch tab/hk/6.
Theme: workspace QG green sweep + codex audit pass + Phase 1 freeze-gate items 8 + 9
(runs all 4 days, validates on-disk state per slot completion).

BEFORE doing anything: read in order:
  1. plans/active/work_split_2026_05_11_harsh.md § "Slot 6 — Workspace QG ..." — full task brief.
  2-5. (standard).
  6. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — your plan-of-record.

Your agent-tag: harsh-workspace-qg-tab.

ORCHESTRATION RULES: same as slot 2 + ALSO:
  - Per CLAUDE.md "QG failure attribution" rule: when a workspace QG failure surfaces,
    git-blame the failing file. If your commit caused it, fix in same logical unit. If a
    foreign-side commit caused it, file an issue doc in plans/active/issues/ and continue
    with your own work — they fix on their own commits.
  - Per CLAUDE.md "Findings Triage Discipline" temporary exception: QG-failure findings on
    someone else's code during the workspace QG cleanup window are EXEMPT from case-3/4/5
    documentation requirement. They'll be cleaned up in bulk.

YOUR TASK: full task brief in this work-split § "Slot 6".

REPORT-BACK: same as slot 2.
```

## Daily sync points

- **Boot (operator opens fresh tabs)** — slot 1 reports state; slots 2-6 boot independently.
- **Mid-cycle (every 4-6 hours while operator active)** — slot 1 polls intra-side ping ledger; routes cross-side
  handshakes through `plans/active/_agent_pings.md`.
- **EOD checkpoint** — every active slot ships a DONE-2026-05-11 block in its plan-of-record body listing today's
  commits.
- **Hard sync gates** (block downstream work until upstream ships):
  - Slot 2 → Slot 5 (features-consolidation Phase 7 → live-pipeline Phase 3-5 implementation).
  - Slot 3 (Track E) → Slot 4 (sports stamping helpers → MTDS sports adapter wiring).
  - Slot 2 → Slot 4 (per-family config.py paths → bucket-name SSOT migration).
  - Ikenna slot 3 → Harsh slot 4 (Phase 0 bar boundary contract → per-adapter wiring).
  - Ikenna slot 2 → Harsh slot 6 (writegate v8 schema → workspace QG green check).

## Defer post-deadline (out of scope this cycle)

- **features_repo_consolidation Phase 8 + 9** — manifest migration + Health-API/live-mode flavors. Deferred per existing
  plan body to post-Phase-7.
- **wave3x Track A UTL classifier extension** (P1) — half-day + session-hours wire-in. May slip if Tracks B/C/D/E
  consume the cycle.
- **live-pipeline Phase 6 (features cross-cutting)** — DEFERRED-AFTER-FEATURES-CONSOLIDATION; not in scope this cycle.
- **live-pipeline Phase 13/14/15** — likely slip to next-cycle if Phase 3-5 implementation consumes available time.
- **hard_schema_enforcement Phase 1** — `blocked_by: tradfi-master-2026-05-07`; out of scope until tradfi unblocks.

## Composes with

- CLAUDE.md § "Daily Work-Split Process" — the canonical process this plan instantiates.
- CLAUDE.md § "Per-Tab Worktrees" — the 3-tier isolation model.
- CLAUDE.md § "Commit + Push + Flip Plan Checkboxes" — per-shippable-unit cadence + pre-commit check + scoreboard rule.
- CLAUDE.md § "Plans Run To Actual Completion, Not Smoke-Test Green" — every tab's done-definition has a Full-execution
  criterion.
- CLAUDE.md § "QG failure attribution" — slot 6 owns workspace QG cadence; foreign failures get issue docs.
- CLAUDE.md § "Citadel-Grade Planning Standards § 6 Downstream Consumer Updates" — slot 2 (features-consolidation) needs
  workspace-grep audit table per the extended § 6 rule.
- [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) — the
  upstream sequencing umbrella this work-split serves.
- [`work_split_2026_05_11_ikenna.md`](work_split_2026_05_11_ikenna.md) — companion split (mirrored cross-side
  handshakes).
