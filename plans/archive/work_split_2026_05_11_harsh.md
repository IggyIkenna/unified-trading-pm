---
doc_type: plan
title: Harsh's daily work-split — 2026-05-11 (Phase 1 code-freeze push to 2026-05-15 freeze gate)
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
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-11
type: coordination-doc
deadline: 2026-05-15
horizon: 4-day cycle
companion_to: plans/active/work_split_2026_05_11_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

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
> ([`/codex/05-infrastructure/per-tab-worktrees.md`](/codex/05-infrastructure/per-tab-worktrees.md)). Each slot is a
> permanent worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/hk/<N>`. **Slot count: 6 — provisioned 2026-05-11
> via `setup-tab-worktrees.sh --init --slots 6`** (`$USER=hk` → branches `tab/hk/1`..`tab/hk/6`, all at the
> `live-defi-rollout` tip; 6 covers the 5 active themes + 1 reserve; grow with `--add-slot` if peak parallel work
> exceeds). Before any slot reassignment from yesterday's theme, run `--reset-slot <N>`.

| Slot | Theme                                                                                                                                                                                                                                                               | Plan-of-record                                                                                                                                                                                                                                      | AI-day budget |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 1    | main orchestrator + on-call                                                                                                                                                                                                                                         | [LEDGER](../../harsh_orchestrator/LEDGER.md) + ping triage + workspace QG sweep coordination                                                                                                                                                        | continuous    |
| 2    | **HARDEST DEADLINE 2026-05-13** — features-repo consolidation Phase 4-7                                                                                                                                                                                             | [features_repo_consolidation_2026_05_08.md](features_repo_consolidation_2026_05_08.md) Phase 4-7                                                                                                                                                    | ~5            |
| 3    | ~~wave3x Tracks B/C/D/E~~ → **defi_master Priority #5** (lending-indices LINEA/BSC routing config + backfill VMs; re-themed 2026-05-11, operator-directed; wave3x all done)                                                                                         | [defi_master_2026_05_07.md](defi_master_2026_05_07.md) `[SCRIPT] P0` "Priority #5" + § "988-missing-dates residuals" (Q1-approved) — _historical: [wave3x_residual_ssots_2026_05_08.md](wave3x_residual_ssots_2026_05_08.md) Tracks B/C/D/E (done)_ | ~2-3 (was ~5) |
| 4    | **(b+) full env-aware bucket architecture** — bucket-name SSOT canonicalisation + env-tier provisioning across both clouds × 3 envs + flat→tiered data migration + sync script + region pinning + VM script env-aware + per-asset-group available_at adapter wiring | [bucket_name_ssot_canonicalisation_2026_05_10.md](bucket_name_ssot_canonicalisation_2026_05_10.md) (Phase 0a-0i) + [available_at_lookahead_bias_completion_2026_05_08.md](available_at_lookahead_bias_completion_2026_05_08.md) Phase 1 per-adapter | ~10-13        |
| 5    | live pipeline Phase 3-5 service wiring (post features-consolidation unblock; mid-cycle activation) + Phase 13/14/15                                                                                                                                                 | [live_pipeline_mtds_mdps_features_2026_05_08.md](live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 3-5 + 13-15                                                                                                                                  | ~5            |
| 6    | workspace QG green sweep + codex audit pass + Phase 1 freeze-gate items 8 + 9                                                                                                                                                                                       | [code_freeze_migrate_backfill_sequencing_2026_05_10.md](code_freeze_migrate_backfill_sequencing_2026_05_10.md) freeze-gate items 8 + 9                                                                                                              | ~3            |

**Total active scope: ~21 AI-days across 5 thematic slots over a 4-day cycle.** Beefier than thin per CLAUDE.md sizing —
under-utilisation is fine, mid-cycle collision is not.

## Tab registry (per-tab full brief)

### Slot 1 — main orchestrator + on-call

- **Identity**: this session (Harsh's main orchestrator agent, slot 1 worktree at `.tabs/1/`).
- **Scope**:
  - **P0**. Daily ledger sweep at start: read `harsh_orchestrator/pings/*.md` (per-slot) +
    `plans/active/_agent_pings.md` (cross-side), triage 🟡 BLOCKED Qs >24h, ack STARTED pings, verify DONE pings.
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

### Slot 3 — ~~Wave3x Tracks B/C/D/E~~ → **RE-THEMED 2026-05-11 (operator-directed): defi_master Priority #5 — Lending-indices LINEA/BSC routing config + backfill VMs**

> **RE-THEME 2026-05-11 (operator-directed; the earlier "do not reassign slot 3" directive lifted).** Wave3x Tracks
> A/B/C/D-audit/E are all DONE (shipped UAC@`bdc84ed`/`e5d82a15`-area + UAC@`7c8b5ad` + UTL@`3fbc6b3`/`2ab3685` +
> instruments-service@`485c57b`; DONE block + deferred-work scoreboard in
> [`wave3x_residual_ssots_2026_05_08.md`](wave3x_residual_ssots_2026_05_08.md); Track-D case-D _implementation_ deferred
> post-cutover). **New theme for slot 3:**
>
> - **Identity**: `harsh-wave3x-tab` (or `harsh-defi-lending-tab` — agent's choice; just a tag). Slot 3 worktree
>   `.tabs/3/`, branch `tab/hk/3`.
> - **Plan-of-record**: [`defi_master_2026_05_07.md`](defi_master_2026_05_07.md) — the `[SCRIPT] P0` "Priority #5" todo
>   (~line 717) + § "988-missing-dates audit residuals". **Q1 APPROVED #5** (defi_master § Open questions Q1 A1, Ikenna
>   2026-05-11). ~576 actionable rows reclaimed; on the May-23 critical path (mid-tier-EVM ≥80% coverage +
>   `carry_staked_basis` LST/lending inputs).
> - **Task**: LINEA + BSC AAVE V3 deployments have routing config absent from the MTDS lending-indices handler/adapter —
>   `market-tick-data-service/.../cli/handlers/lending_indices_handler.py` +
>   `market_interface/adapters/defi/aave_lending.py` (the plan's `adapters/lending_indices/` path is stale). Add LINEA +
>   BSC chain→subgraph entries (Messari graph-network IDs); check the UAC `DATA_TYPES_BY_ASSET_GROUP` / `_defi.py`
>   capability-declaration gate too (per CLAUDE.md "UAC DATA*TYPES_BY_ASSET_GROUP is routing gate"). \*\*NB the
>   AAVE_V3-on-LINEA/BSC \_launch dates* are already corrected in UAC\*\* (defi_master "Batch A" `[x]` — LINEA
>   2025-02-11, BSC 2024-01-23) — slot 3 does NOT re-do the dates, only the routing. Smoke-test 1 day per chain
>   post-launch (verify the subgraph returns >0 real rows, not 1440-NaN placeholders per CLAUDE.md "Honest absence"); if
>   the subgraph genuinely has no data even post-launch, that's `empty_confirmed` per the honest-absence rule and the
>   todo closes that way. Then launch backfill VMs for LINEA + BSC lending-indices (Q1-approved) with full event-stream
>   verification per "No fire-and-forget VM launches" + `MANIFEST_PER_VM_SHARDS=true` + refresh code tarballs first if
>   MTDS code changed.
> - **Not blocked**: distinct workstream from Priority #1 (Ethereum-AAVE*V3 UAC fix — not slot 3's); the bucket-naming
>   (b+) work (slot 4) doesn't touch `lending-indices-{pid}` (Phase 0e env-tiered only
>   market-data/instruments-store/features-calendar/prediction kinds); the launch-date UAC fix is already shipped. **No
>   Ikenna-side overlap**: Ikenna slot 5 = `ikenna-defi-phase-1e-tab` does the Phase-1.E \_sequencing readiness audits*
>   (defi_catalogue / arbitrage_price_dispersion / cme_polymarket / recursive-borrow + (b+) cascade audit +
>   EVENT_CONTRACT enum), NOT the lending-indices routing. If slot 3 needs to touch UAC `_defi.py`
>   (capability-declaration add) → surgical `git add -p` (Ikenna slot 5 may also be in that file for unrelated
>   sequencing-audit edits; distinct lines).
> - **Bootstrap**: operator runs `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot 3`
>   (between-themes reset) OR `/clear` the existing session + tell it to
>   `git fetch origin live-defi-rollout && git rebase origin/live-defi-rollout` (worktree verified clean). Then read
>   `harsh_orchestrator/AGENT_ONBOARDING.md` + the `[main → slot 3]` brief in `harsh_orchestrator/pings/slot_3.md`
>   (`▶ NEW ASSIGNMENT — START HERE`) + CLAUDE.md § "DeFi Execution Architecture" / "No fire-and-forget VM launches" /
>   "VM launcher script SSOT" / "VM Naming Convention" / "Per-VM shard isolation" / "Manifest concurrency principle" /
>   "Honest absence".
> - **Done-definition + full-execution criterion** (per "Plans Run To Actual Completion"): ✅ LINEA + BSC AAVE_V3
>   routing config shipped to `live-defi-rollout` (MTDS@<sha>); ✅ smoke-test passed (1 day/chain — manifest row
>   `captured` with sample-inspected real-data parquet, OR `empty_confirmed` with the subgraph-probe evidence if
>   genuinely empty); ✅ backfill VMs ran to natural shutdown with manifest-verified LINEA/BSC lending-indices rows over
>   the post-launch window (sample-inspect a parquet, not just row counts); ✅ defi_master Priority-#5 checkbox `[x]`
>   with `<repo>@<sha>` + VM-name + manifest evidence + a `## DONE-<date>` block.

---

#### (Historical — Wave3x Tracks B/C/D/E, all DONE 2026-05-11; kept for record)

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

### Slot 4 — (b+) full env-aware bucket architecture + per-asset-group available_at adapter wiring

> **OPERATOR DECISION 2026-05-11 (Ikenna): option (b+) — full env-aware bucket architecture across all buckets in both
> clouds.** Slot 4 + Harsh slot 1 had recommended option (a) (drop the env tier from yaml); operator overrode to (b+) on
> the strategic basis that prod/staging/dev isolation is a Citadel-grade requirement for the May-23 live cutover. **Slot
> 4 scope under (b+) is materially bigger** (~10-13 AI-day vs ~3 under (a)); spans Phase 1 code-complete (deadline
> 2026-05-15) + Phase 2 physical migration window (2026-05-15→05-19). Full Phase 0a-0i breakdown in
> [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md). Cross-side ping
> confirming (b+) lands in [`plans/active/_agent_pings.md`](_agent_pings.md).

- **Identity**: `harsh-bucket-and-adapter-tab` (slot 4 worktree at `.tabs/4/`).
- **Scope (Phase 1 code-complete by 2026-05-15)**:
  - **P0** Phase 0b — yaml additive corrections: missing `prediction`/`sports` keys, GCP `features-calendar` uncomment,
    canonical `-test-` E2E variant.
  - **P0** Phase 0e — yaml extends env tier to ALL `${DEPLOYMENT_ENV}`-MISSING bucket kinds (instruments-store,
    market-data, etc.). Operator confirms which stay env-less (terraform-state likely; secrets definitely).
  - **P0** Phase 0f — VM launcher scripts (~30 under `deployment-service/scripts/vm/`) read `DEPLOYMENT_ENV`; pass to VM
    via metadata. `--env <prod|staging|dev>` CLI flag per launcher OR centralised helper.
  - **P0** Phase 0g — verify deployment UI env-tier shipped ✅ done (per
    `/codex/05-infrastructure/deployment-ui-architecture.md`); cross-check per-env deployment-api resolves env-tiered
    names via resolver.
  - **P0** Phase 0h — sync script `deployment-service/scripts/sync-buckets-prod-to-{staging,dev}.sh` + Cloud Scheduler
    cron. Truncated date window (1-2 yr), same-region enforced, manifest sync post-data-sync. Ships in Phase 1; first
    execution Phase 3 / post-cutover.
  - **P0** Phase 0i — region-pinning audit (GCP all asia-northeast1; AWS all us-east-1 OR ap-northeast-1 per operator
    decision); reject `--location=<other>` in provisioning.
  - **P0** Done-def #2 — L2 config.py migration: per-family `config.py` `*_bucket_template` Field defaults →
    `resolve_bucket_name()` calls. Migration recipe in plan body § Pre-audit manifest.
  - **P0** Done-def #3 — legacy `get_bucket_name` + `BUCKET_PREFIXES` → delegate to `resolve_bucket_name()`.
  - **P0** Done-def #5 — QG STEP 5.69 ratchet for inline `f"gs://{bucket}/..."` formatters (ships AFTER #2 + Phase 0d so
    baseline doesn't bake in pre-migration sites).
- **Scope (Phase 2 physical migration 2026-05-15→05-19)**:
  - **P0** Phase 0c — provision env-tiered buckets across BOTH clouds × 3 envs (staging/prod/development) × all yaml
    kinds. Estimated ~300-400 new buckets. Implementation: extend Terraform
    `deployment-service/terraform/modules/storage_buckets` OR `setup-buckets.sh`. Verification: `gcloud storage ls` /
    `aws s3 ls` per yaml-derived name.
  - **P0** Phase 0d — flat→env-tiered data migration. For every existing flat bucket on GCP + AWS, copy ALL data into
    new env-tiered prod bucket via `gcloud storage cp -r --preserve-symlinks` / `aws s3 sync`. Drift verify ≤0.01%.
    Operator-coordinated write-pause cutover window. Archive flat buckets to `*-archived-flat-2026-05-19/` + 30-day
    retention; delete after manifest + downstream verification.
- **Scope (per-asset-group available_at adapter wiring; carryover from cycle-start scope)**:
  - **P0** Sports adapter stamping (folded with Wave3x Track E from slot 3 — wire Track E's UTL helpers into MTDS sports
    adapters).
  - **P0** Coordinate hand-off pattern with Ikenna slot 3 once Phase 0 bar boundary contract lands.
- **Plan-of-record**:
  [`bucket_name_ssot_canonicalisation_2026_05_10.md`](bucket_name_ssot_canonicalisation_2026_05_10.md)
  - [`available_at_lookahead_bias_completion_2026_05_08.md`](available_at_lookahead_bias_completion_2026_05_08.md) Phase
    1 per-adapter halves.
- **Repos owned**: `unified-trading-library` (`cloud_interface.bucket_naming` resolver — already exists; SSOT =
  `cloud-providers.yaml`) + `unified-trading-library` (QG step) + `features-service` (per-family config.py — coordinate
  with Harsh slot 2 on file paths) + `deployment-service` (setup-buckets.sh) + `market-tick-data-service` (sports
  adapter stamping wiring) + PM (plan flips + audit table).
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
    `python -c "from unified_trading_library.cloud_interface.bucket_naming import resolve_bucket_name; print(resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='cefi'))"`
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

  - **P0 Track-D P0-bug fixes (ADDED 2026-05-11 per operator direction — Track D audit surfaced them, fixes in sight)**:
    - **P0-1** — MTDS honest-coverage sentinel silently aborts: `market_tick_data_service/engine/orchestrator.py:2671`
      (sports sentinel) / `:2808` (Tier-3 per-instrument) / `:2849` (Tier-2 venue-level) +
      `scripts/rebuild_prediction_manifest.py:351` call `record_empty(row_key=...)` with NO `reason=` →
      `LegacyBlankErrorReasonError` → swallowed by the wrapping `except Exception: "non-blocking"` → no
      `empty_confirmed`/`attempted_failed` rows land for CeFi/sports on any zero-data shard date. Fix: pass
      `reason="SOURCE_RETURNED_ZERO"` (or the calendar `EXPECTED_HOLIDAY`/`EXPECTED_WEEKEND`/
      `EXPECTED_PARTIAL_HALF_DAY` where the orchestrator already knows it via `is_non_trading_day`); STOP swallowing the
      manifest-write exception in the wrapping `except` (a `LegacyBlankErrorReasonError` must be loud). Crisp,
      mechanical.
    - **P0-2 (QG-gate half)** — add an AST/grep QG STEP that flags banned NaN-placeholder / bypass-`record_captured`
      patterns: `_create_empty_output` / `_handle_empty_tick_data` / `_create_full_day_empty_output` /
      `_create_closed_market_candle` / `_maybe_write_vix_gap_placeholder` / direct `storage_client.upload_bytes` candle
      writes that don't route through `record_captured`. (The P0-2 _code_ fixes — delete legacy
      `orchestration_writer.py:328 _write_candles`, fix `tradfi/ohlcv_passthrough.py`, flip `output_schemas.py` OHLCV
      nullability, resolve the triple-SSOT — are writegate Phase 2.A scope + Harsh slot 5's live-pipeline MDPS phase,
      NOT slot 6.)
    - **P0-3** — `commodity` phantom-row: investigate as part of the P1 phantom-audit pass above; classify + fix or file
      an issue doc.
    - Source:
      [`plans/active/issues/wave3x_track_d_findings_2026_05_11.md`](issues/wave3x_track_d_findings_2026_05_11.md) (filed
      by Harsh slot 3).

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

| Files / dirs                                                                                                | Collision tabs                                                                          | Mitigation                                                                                    |
| ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `features-service/features_service/*`                                                                       | slot 2 (consolidation), slot 4 (config.py per-family), slot 5 (live-pipeline consumers) | Slot 2 sole writer until Phase 7; slots 4 + 5 wait for hand-off ping.                         |
| `unified-api-contracts/unified_api_contracts/canonical/sports/*`                                            | slot 3 (Wave3x Track B SSOTs)                                                           | Slot 3 sole writer; coordinates with Ikenna slot 5 if any DeFi/cross-asset overlap.           |
| `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py` + `cloud-providers.yaml` | slot 4 (bucket-name SSOT — yaml is the SSOT, resolver in UTL)                           | Slot 4 sole writer.                                                                           |
| `unified-trading-library/unified_trading_library/availability_stamping/*`                                   | slot 3 (Track E sports stamping) + Ikenna slot 3 (Phase 0 helpers)                      | Distinct files within stamping/; both can edit in parallel; surgical `git add -p`.            |
| `market-tick-data-service/*`                                                                                | slot 4 (sports adapter wiring), slot 5 (Phase 3 websocket), slot 6 (audit, read-only)   | Distinct files; slots 4 + 5 surgical staging.                                                 |
| `instruments-service/scripts/*`                                                                             | slot 3 (Track C reconciler)                                                             | Slot 3 sole writer; new script file, no collision.                                            |
| `unified-trading-pm/plans/active/*.md`                                                                      | All slots (plan flips + DONE blocks)                                                    | Each slot edits ONLY its plan-of-record; surgical `git add -p` mandatory; never `git add -A`. |
| `deployment-service/scripts/vm/*.sh`                                                                        | slot 5 (Phase 13 launchers) + slot 6 (audit only)                                       | Slot 5 sole writer.                                                                           |
| `unified-trading-pm/codex/02-data/*`                                                                        | slot 6 (codex audit pass) — read most + may stub follow-up                              | Slot 6 owns audit; if audit finds stale doc, file as issue OR fix in-place if scope-clear.    |

**Per-slot worktree isolation** makes cross-slot races on `.git/index` unrepresentable. The table above is for
SHARED-FILE-CONTENT collisions when slots push and pull each other's commits.

## Spawn prompts (paste-ready)

> **Operator usage**: open a fresh Claude Code session inside the slot's worktree —
> `cd ${WORKSPACE_ROOT}/.tabs/<N>/ && claude` (Option B, one VS Code window at the root + terminal CLIs per slot), or a
> VS Code window at `.tabs/<N>/`. Confirm CWD + branch first: `pwd` → `.../.tabs/<N>`,
> `git -C unified-trading-pm rev-parse --abbrev-ref HEAD` → `tab/hk/<N>`. Then paste the matching prompt below.
>
> **Boot pre-req** (already done 2026-05-11): 6 slot worktrees provisioned via `setup-tab-worktrees.sh --init --slots 6`
> (`$USER=hk` → branches `tab/hk/1`..`tab/hk/6`). Before reassigning a slot to a new theme, run
> `setup-tab-worktrees.sh --reset-slot <N>` first. Full 7-step recipe:
> [`/codex/05-infrastructure/per-tab-worktrees.md`](/codex/05-infrastructure/per-tab-worktrees.md).
>
> **The prompts below are intentionally minimal.** All the common content — role, git discipline (conditional push to
> `live-defi-rollout`, rebase-on-push, plan-aware-merge on conflict), reading order, communication bus (ping ledger +
> plan-of-record Q&A format), pre-commit check, plan-of-record curation duties, sub-agent fan-out discipline, boot-ack
> template — lives ONCE in
> [`../../harsh_orchestrator/AGENT_ONBOARDING.md`](../../harsh_orchestrator/AGENT_ONBOARDING.md) (the SSOT). Each prompt
> just names the per-slot facts (slot number, worktree/branch, theme, agent-tag, plan-of-record, slot-specific notes)
> and points the agent there. Per-slot task briefs (scope items + priorities + repos owned + collision boundaries +
> done-definition + full-execution criterion) are in this file's § "Slot N" sections above.

### Slot 2 spawn prompt — features-repo consolidation Phase 4-7 (HARDEST DEADLINE 2026-05-13)

```text
You are slot 2 — a scoped implementer spawned by Harsh's main orchestrator (slot 1, a separate Claude Code
session on the SAME PC). Your worktree: ${WORKSPACE_ROOT}/.tabs/2/ on branch tab/hk/2. Your agent-tag for
ping-ledger entries: harsh-features-consolidation-tab.

Theme: features-repo consolidation Phase 4-7 — HARDEST DEADLINE 2026-05-13 (Phase 0-3 already shipped:
pre-audit PM@1de574b4, UAC FeatureFamily @7f63ca3, UTL ManifestWriter feature_family kwarg @c16cef3,
features-service skeleton @d3d6e286 pushed + workspace-manifest registered). Phase 4 = import rewrite
(11 ext imports + 51 string refs per the pre-audit); Phase 5 = lift cross-family helpers to UTL; Phase 6 =
pyproject + test consolidation; Phase 7 = single features-service deployable + 8 child repos archived.

Read, in order, BEFORE doing anything:
  1. harsh_orchestrator/AGENT_ONBOARDING.md — role + git discipline + reading order + comms bus + pre-commit
     check + plan-of-record curation + sub-agent fan-out + boot-ack template. (This is the SSOT for all the
     common mechanics; everything not slot-specific is there.)
  2. plans/active/work_split_2026_05_11_harsh.md § "Slot 2 — Features-repo consolidation Phase 4-7" — your
     full task brief (scope/priorities/repos owned/collision boundaries/done-definition/full-execution criterion).
  3. plans/active/features_repo_consolidation_2026_05_08.md — your plan-of-record (todos + checkbox flips +
     ## Open questions for blockers).
  4. The Phase 0 pre-audit manifest at PM@1de574b4 (1286 lines) — exact 11+51 sites for Phase 4.
  (AGENT_ONBOARDING's reading order then takes you through CLAUDE.md, per-tab-worktrees.md,
  plan-aware-merge-resolution.md, SUB_AGENT_MANDATORY_RULES.md.)

Bidirectional comms: after each shippable-unit push (where you `git fetch origin live-defi-rollout && git rebase
origin/live-defi-rollout` anyway), RE-READ your harsh_orchestrator/pings/slot_<N>.md for `[main → slot N]` messages
(slot 1 reaches you there — acks / scope changes / pointers) + your plan-of-record `## Open questions` for new A1s.
See harsh_orchestrator/pings/README.md § "Bidirectional comms". The operator may also nudge you ("take a pull, main
has a message") — same thing.

Slot-2-specific:
  - CROSS-SIDE PING MANDATORY when Phase 7 lands (features-service deployable; 8 child repos archived):
    append a ping in plans/active/_agent_pings.md so Ikenna slot 4 can promote live-pipeline Phase 4-5
    design to implementation.
  - Citadel § 6 requires a workspace-grep audit table for the removed/renamed per-repo import paths.
  - Sub-agent fan-out hint: 4 parallel at boot — Phase 4 import rewrite / Phase 5 UTL helper lift / Phase 6
    pyproject+test consolidation / Phase 7 archive coordination.

Boot ack: append "[YYYY-MM-DD HH:MM UTC] harsh-features-consolidation-tab — STARTED slot 2
(plans/active/features_repo_consolidation_2026_05_08.md)" to harsh_orchestrator/pings/slot_<N>.md (your own per-slot ping file — no collision; see harsh_orchestrator/pings/README.md), then start.
Final: "## DONE-2026-05-11" block at the bottom of the features_repo_consolidation plan body with every
code + plan-flip commit sha + EOD deferral-audit (grep each deferral against plans/active/*.md per
AGENT_ONBOARDING § plan-of-record curation), then go quiet.
```

### Slot 3 spawn prompt — Wave3x Tracks B/C/D/E parallel

```text
You are slot 3 — a scoped implementer spawned by Harsh's main orchestrator (slot 1, a separate Claude Code
session on the SAME PC). Your worktree: ${WORKSPACE_ROOT}/.tabs/3/ on branch tab/hk/3. Your agent-tag:
harsh-wave3x-tab.

Theme: Wave3x Tracks B/C/D/E parallel — (B) sports per-source SSOTs (UNDERSTAT_COVERED_LEAGUES +
TRANSFER_WINDOWS + footystats season bounds, UAC canonical/sports/); (C) reconcile_legacy_blank_to_typed_reason.py
reconciler for instruments-service; (D) ANTI-SEQUENCING-CRITICAL zero-activity-bar adapter audit across MTDS,
MDPS, 8 features-* services; (E) sports per-source stamping helpers (stamp_available_at_lineups / _injuries /
_post_match_cascade / _odds, UTL availability_stamping/). Track A already shipped UAC@bdc84ed; P1 Track A UTL
wire (half-day + session-hours from UAC@bdc84ed).

Read, in order, BEFORE doing anything:
  1. harsh_orchestrator/AGENT_ONBOARDING.md — role + git discipline + reading order + comms bus + pre-commit
     check + plan-of-record curation + sub-agent fan-out + boot-ack template (the SSOT for all common mechanics).
  2. plans/active/work_split_2026_05_11_harsh.md § "Slot 3 — Wave3x Tracks B/C/D/E parallel" — your full task
     brief.
  3. plans/active/wave3x_residual_ssots_2026_05_08.md — your plan-of-record.
  (AGENT_ONBOARDING's reading order then takes you through CLAUDE.md, per-tab-worktrees.md,
  plan-aware-merge-resolution.md, SUB_AGENT_MANDATORY_RULES.md.)

Bidirectional comms: after each shippable-unit push (where you `git fetch origin live-defi-rollout && git rebase
origin/live-defi-rollout` anyway), RE-READ your harsh_orchestrator/pings/slot_<N>.md for `[main → slot N]` messages
(slot 1 reaches you there — acks / scope changes / pointers) + your plan-of-record `## Open questions` for new A1s.
See harsh_orchestrator/pings/README.md § "Bidirectional comms". The operator may also nudge you ("take a pull, main
has a message") — same thing.

Slot-3-specific:
  - Track D is ANTI-SEQUENCING CRITICAL — must complete BEFORE the 2026-05-15 Phase 2 freeze (code_freeze:300).
    If the audit finds a new shard atom dimension OR a new error reason needed → escalate to slot 1 + Ikenna
    slot 5 IMMEDIATELY (they decide v8-schema-now vs deferred-post-cutover).
  - Per CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" HARD RULE: the Track D adapter audit MUST read
    consumer code + check runtime-resolved patterns (regex dispatch, StrEnum lookups, factory registries) —
    do NOT conclude "missing" from a literal grep alone.
  - Sequencing vs slot 2: Track D's audit of the 8 features-* repos should run AFTER slot 2 ships Phase 4
    (import rewrite), or against archived snapshots — coordinate via slot 1.
  - Sub-agent fan-out hint: 5 parallel at boot (one per Track A-UTL / B / C / D / E); Track D benefits from
    ~10-12 sub-sub-agents (one per service repo) for the read-only audit pass.
  - Track D findings doc goes to plans/active/issues/wave3x_track_d_findings_2026_05_11.md with per-adapter
    A/B/C/D classification per CLAUDE.md "Four-category empty-output decision".

Boot ack: append "[YYYY-MM-DD HH:MM UTC] harsh-wave3x-tab — STARTED slot 3
(plans/active/wave3x_residual_ssots_2026_05_08.md)" to harsh_orchestrator/pings/slot_<N>.md (your own per-slot ping file — no collision; see harsh_orchestrator/pings/README.md), then start.
Final: "## DONE-2026-05-11" block in the wave3x_residual_ssots plan body + EOD deferral-audit, then go quiet.
```

### Slot 4 spawn prompt — bucket-name SSOT + per-asset-group available_at adapter wiring

```text
You are slot 4 — a scoped implementer spawned by Harsh's main orchestrator (slot 1, a separate Claude Code
session on the SAME PC). Your worktree: ${WORKSPACE_ROOT}/.tabs/4/ on branch tab/hk/4. Your agent-tag:
harsh-bucket-and-adapter-tab.

Theme: bucket-name SSOT canonicalisation (yaml = canonical per plan; collapse the per-family config.py + UTL
resolver duplicates → bucket_naming.resolve_bucket_name(); workspace QG step for inline f"gs://{bucket}/...";
yaml-vs-resolver parity test; plan-flip audit table) + per-asset-group available_at adapter wiring (sports
adapter stamping — wire slot 3 Track E's UTL helpers into MTDS sports adapters; CeFi already shipped MTDS@4a00bd5).

Read, in order, BEFORE doing anything:
  1. harsh_orchestrator/AGENT_ONBOARDING.md — the SSOT for all common mechanics.
  2. plans/active/work_split_2026_05_11_harsh.md § "Slot 4 — Bucket-name SSOT + per-asset-group available_at
     adapter wiring" — your full task brief.
  3. plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md — primary plan-of-record.
  4. plans/active/available_at_lookahead_bias_completion_2026_05_08.md Phase 1 — secondary plan-of-record.
  (AGENT_ONBOARDING's reading order then takes you through CLAUDE.md, per-tab-worktrees.md,
  plan-aware-merge-resolution.md, SUB_AGENT_MANDATORY_RULES.md.)

Bidirectional comms: after each shippable-unit push (where you `git fetch origin live-defi-rollout && git rebase
origin/live-defi-rollout` anyway), RE-READ your harsh_orchestrator/pings/slot_<N>.md for `[main → slot N]` messages
(slot 1 reaches you there — acks / scope changes / pointers) + your plan-of-record `## Open questions` for new A1s.
See harsh_orchestrator/pings/README.md § "Bidirectional comms". The operator may also nudge you ("take a pull, main
has a message") — same thing.

Slot-4-specific:
  - GATED: bucket-name SSOT migration runs AFTER slot 2 ships Phase 4 (per-family config.py paths stabilise),
    or against the consolidated state. Sports adapter stamping WAITS on (a) slot 3 Track E ship (UTL helpers)
    + (b) Ikenna slot 3 Phase 0 ship (bar boundary contract). While gated, prep test scaffolds + the mechanical
    3-layer-collapse plan.
  - Triple-drift incident reference (2026-05-08 Tab 4 close-out): there are THREE current SSOT layers (yaml +
    per-family config.py + UTL resolver). yaml is canonical; collapse the other two; audit each call site
    before deletion.
  - Sub-agent fan-out hint: 2 parallel — (1) bucket-name SSOT migration; (2) sports adapter stamping wiring (gated).

Boot ack: append "[YYYY-MM-DD HH:MM UTC] harsh-bucket-and-adapter-tab — STARTED slot 4
(plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)" to harsh_orchestrator/pings/slot_<N>.md (your own per-slot ping file — no collision; see harsh_orchestrator/pings/README.md), then start.
Final: "## DONE-2026-05-11" block in the bucket_name_ssot_canonicalisation plan body + EOD deferral-audit, then go quiet.
```

### Slot 5 spawn prompt — live-pipeline Phase 3-5 service wiring (GATED — pre-gate scaffolds now)

```text
You are slot 5 — a scoped implementer spawned by Harsh's main orchestrator (slot 1, a separate Claude Code
session on the SAME PC). Your worktree: ${WORKSPACE_ROOT}/.tabs/5/ on branch tab/hk/5. Your agent-tag:
harsh-live-pipeline-impl-tab.

Theme: live-pipeline Phase 3-5 service wiring (Phase 3 MTDS websocket rollout per asset_group; Phase 4 MDPS
streaming aggregation; Phase 5 features-service asset-scoped streaming) + Phase 13/14/15 (VM launchers +
watchdog dict updates + codex SSOT updates + QG sweep + smoke — likely next-cycle).

Read, in order, BEFORE doing anything:
  1. harsh_orchestrator/AGENT_ONBOARDING.md — the SSOT for all common mechanics.
  2. plans/active/work_split_2026_05_11_harsh.md § "Slot 5 — Live pipeline Phase 3-5 service wiring" — full task brief.
  3. plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md — your plan-of-record (Phases 3-5 + 13-15).
  4. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — the sequencing umbrella you serve.
  (AGENT_ONBOARDING's reading order then takes you through CLAUDE.md, per-tab-worktrees.md,
  plan-aware-merge-resolution.md, SUB_AGENT_MANDATORY_RULES.md.)

Bidirectional comms: after each shippable-unit push (where you `git fetch origin live-defi-rollout && git rebase
origin/live-defi-rollout` anyway), RE-READ your harsh_orchestrator/pings/slot_<N>.md for `[main → slot N]` messages
(slot 1 reaches you there — acks / scope changes / pointers) + your plan-of-record `## Open questions` for new A1s.
See harsh_orchestrator/pings/README.md § "Bidirectional comms". The operator may also nudge you ("take a pull, main
has a message") — same thing.

Slot-5-specific:
  - GATED START: Phase 3-5 IMPLEMENTATION is blocked until BOTH (a) Harsh slot 2 ships features-consolidation
    Phase 7 AND (b) Ikenna slot 4 ships Phase 4-5 design-ahead commits. Watch plans/active/_agent_pings.md for
    both cross-side pings. While gated: ship PRE-GATE scaffolds + integration test fixtures only (read the
    live-pipeline design docs + Ikenna's UTL stubs as they ship; prep MTDS websocket integration scaffolds /
    MDPS streaming consumer hooks / features-service per-asset-group flavors). When BOTH pings land, promote
    scaffolds to implementation (5 parallel sub-agents, one per asset_group).
  - Phase 5 features-service consumers live in the repo slot 2 is consolidating — coordinate file paths;
    merge against the consolidated state.

Boot ack: append "[YYYY-MM-DD HH:MM UTC] harsh-live-pipeline-impl-tab — STARTED slot 5 (pre-gate)
(plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)" to harsh_orchestrator/pings/slot_<N>.md (your own per-slot ping file — no collision; see harsh_orchestrator/pings/README.md), then start.
Final: "## DONE-2026-05-11" block in the live_pipeline plan body + EOD deferral-audit (explicit
DEFERRED-AFTER-PHASE-3-5 annotation if Phase 13/14/15 slip), then go quiet.
```

### Slot 6 spawn prompt — workspace QG green sweep + codex audit pass

```text
You are slot 6 — a scoped implementer spawned by Harsh's main orchestrator (slot 1, a separate Claude Code
session on the SAME PC). Your worktree: ${WORKSPACE_ROOT}/.tabs/6/ on branch tab/hk/6. Your agent-tag:
harsh-workspace-qg-tab.

Theme: workspace QG green sweep (UAC + UTL + every service repo; basedpyright clean; no # type: ignore masking
architectural violations — run after each slot ships a shippable unit, validate) + codex SSOT audit pass per
CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE + freeze-gate items 8 + 9 of
code_freeze_migrate_backfill_sequencing_2026_05_10.md + P1 phantom audit
(instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group all --dry-run — ensure the
354 residual phantoms from the 2026-05-04 baseline haven't grown). Runs all 4 days.

Read, in order, BEFORE doing anything:
  1. harsh_orchestrator/AGENT_ONBOARDING.md — the SSOT for all common mechanics.
  2. plans/active/work_split_2026_05_11_harsh.md § "Slot 6 — Workspace QG green sweep + codex audit pass" — full task brief.
  3. plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md — your plan-of-record (freeze-gate items 8 + 9).
  (AGENT_ONBOARDING's reading order then takes you through CLAUDE.md, per-tab-worktrees.md,
  plan-aware-merge-resolution.md, SUB_AGENT_MANDATORY_RULES.md.)

Bidirectional comms: after each shippable-unit push (where you `git fetch origin live-defi-rollout && git rebase
origin/live-defi-rollout` anyway), RE-READ your harsh_orchestrator/pings/slot_<N>.md for `[main → slot N]` messages
(slot 1 reaches you there — acks / scope changes / pointers) + your plan-of-record `## Open questions` for new A1s.
See harsh_orchestrator/pings/README.md § "Bidirectional comms". The operator may also nudge you ("take a pull, main
has a message") — same thing.

Slot-6-specific:
  - Per CLAUDE.md "QG failure attribution": when a workspace QG failure surfaces, git-blame the failing file.
    Your commit caused it → fix in same logical unit. Foreign-side commit caused it → file an issue doc in
    plans/active/issues/ and continue with your own work (they fix on their own commits).
  - Per CLAUDE.md "Findings Triage Discipline" temporary exception (in effect until QG is workspace-clean):
    QG-failure findings on someone else's code are EXEMPT from the case-3/4/5 documentation requirement —
    they'll be cleaned up in bulk. Non-QG findings (data correctness, in-flight VM bugs, SSOT contradictions)
    stay case-1-to-5 normally.
  - You are read-only across UAC + UTL + every service repo + codex docs; issue docs for failure attribution
    go in plans/active/issues/. Sub-agent fan-out hint: 1-2 sub-agents (one per QG sweep run; one per codex audit pass).

Boot ack: append "[YYYY-MM-DD HH:MM UTC] harsh-workspace-qg-tab — STARTED slot 6
(plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)" to harsh_orchestrator/pings/slot_<N>.md (your own per-slot ping file — no collision; see harsh_orchestrator/pings/README.md), then start.
Final: "## DONE-2026-05-11" block in the code_freeze plan body (freeze-gate items 8 + 9 status) + EOD
deferral-audit, then go quiet.
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

## Deferred work after 2026-05-11 session

End-of-cycle scoreboard per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" Half 3. End-of-shift handover banner:
PM@`d3b7e8d7` — all 5 implementer slots ⚪ DONE primary + per-slot pickup-points handed over to Ikenna's side.
Companion: [`work_split_2026_05_11_ikenna.md`](work_split_2026_05_11_ikenna.md) § same.

| Phase / item                                                                                | Status as of 2026-05-11 EOD                                                                                 | Successor / blocker                                                                                                |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Harsh slot 2 — features-consolidation Q6+Q7 (Phase 4.6/6)                                   | ✅ Q6+Q7 RESOLVED (PM@`1f8f6390`); ⚪ parent Phase 4.6/6 flip PENDING one fresh-green QG-run                | 2026-05-12 Harsh slot 2 (per companion split) — fresh QG-run + plan-flip                                           |
| Harsh slot 3 — defi #5 monitoring                                                           | ✅ DONE (handover PM@`13030665`)                                                                            | Cross-side: Ikenna slot 3 absorbed lending-indices residuals (see Ikenna scoreboard)                               |
| Harsh slot 4 — bucket_name_ssot env-LESS GCP entries + Phase 0h code                        | ✅ DONE primary (deployment-service@`fc1cfa0`); Phase 0f operational + Phase 0h first-execution ⚪ DEFERRED | Cross-side: Ikenna slot 8 absorbed Phase 0f + Phase 0h (see Ikenna scoreboard)                                     |
| Harsh slot 5 — live-pipeline Phase 3.1/3.3/3.4 (mtds@`97b2224`)                             | ✅ DONE primary; Phase 3.5/5/6/15 ⚪ DEFERRED — Q1 reconciling on LDR                                       | Cross-side: Ikenna slot 7 absorbed Phase 3.5/5/6/15 (PM@`91a24ecc`); 2026-05-12 Ikenna slot 7 carries forward      |
| Harsh slot 6 — workspace QG cadence + features-consolidation downstream consumer audit      | ✅ DONE (PM@`8b4a8110`)                                                                                     | —                                                                                                                  |
| Harsh slot 6 — DeFi simulation-realism downstream impl handoff                              | ⚪ DEFERRED — Ikenna designs (slot 6), Harsh implements                                                     | 2026-05-12 Ikenna slot 6 → Harsh slot 4 (per companion split cross-side handshakes)                                |
| live-pipeline Phase 13/14/15 (DEFERRED-AFTER-PHASE-3-5)                                     | ⚪ DEFERRED                                                                                                 | 2026-05-12 Ikenna slot 7 (carries forward Phase 3-5 + 13-15 if Phase 3-5 closes)                                   |
| live-pipeline Phase 6 (cross-cutting features; DEFERRED-AFTER-FEATURES-CONSOLIDATION)       | 🟡 BLOCKED on features-consolidation Phase 7 merge                                                          | 2026-05-12 Ikenna slot 7 (carry-forward); unblocks once Harsh slot 2 closes features-consolidation Q6+Q7 plan-flip |
| wave3x Track A UTL classifier extension (P1)                                                | ⚪ DEFERRED — may slip if Tracks B/C/D/E consumed cycle                                                     | 2026-05-12 reserve list (post-cutover)                                                                             |
| features_repo_consolidation Phase 8 + 9 (manifest migration + Health-API/live-mode flavors) | ⚪ DEFERRED — post-Phase-7 per plan body                                                                    | 2026-05-12 Harsh slot 2 (post Q6+Q7 closure) or post-cutover                                                       |

**Sweep complete**: every line above either ✅ DONE with commit citation or has a named 2026-05-12 successor (own side
or cross-side). No orphans remain after this scoreboard.

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
