---
doc_type: issue
title: ag-closeout-audit defi parked findings — 2026-08-07
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-07, tranche=defi, slot 7). 6 findings: 1
  orphaned_never_touched (0 covering plans), 1 not_covered (batch9 completed-todo cites but drafts nothing), 3
  orphaned_partial_coverage (batch9/10 cover some but not all open items), 1 informational tag-finding (2 docs mistagged
  [defi] instead of [ui]). ~5 AO-eligible candidates identified for next scheduled batch (batch11).
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, defi, orphan]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/active/defi_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_06.md,
  ]
created: 2026-08-07
parent_epic: defi_master
assigned_vm: NA
priority: P3
last_updated: 2026-08-07
source: >-
  ag_closeout_auditor scheduled run 2026-08-07 (tranche=defi, slot 7, DISPATCH_ID=agt-6f12db)
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/issues/defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md,
    /plans/active/issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md,
    /plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md,
    /plans/archive/2026_08/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md,
    /plans/active/defi_satellite_ao_dispatch_batch10_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# ag-closeout-audit defi parked findings — 2026-08-07

## Finding 1 — genuine orphan: `defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md`

**Category**: conflict-gated (re-triageable — orphaned because no covering plan cites it, not because of a competing
claim)

**What**: This doc (created 2026-08-04) has 2 remaining open todos:

- `[DIAG] P2` — determine whether SOME venues still got written on 08-02/03/04 before the Cloud Run OOM crash (per-venue
  processing order in `lst_rates_handler.py` vs recent `written_at` in manifest) → bounded, checkable, AO-eligible
- `[INFRA] P2` — prod terraform state holds 26 add/17 change/2 destroy of un-applied drift → deliberately human-gated by
  the doc's own text

Zero covering plans (consolidated closeout, all 5 active batch plans, both track plans, data_completion,
lst_rate_honest_coverage, pipeline_e2e) cite this doc.

**Why orphaned**: The doc was created after the 2026-08-06 audit's Phase 0 discovery window, or was missed by it. It's a
natural Cloud Run OOM incident doc filed from a data_pipeline_failure escalation.

**Recommendation**: Fold the DIAG todo (venue-level data-loss assessment) into the next scheduled batch (batch11). Do
NOT extract the terraform todo — the doc itself says it needs human review before `tofu apply`. Mark this doc
`archivable_after_planned_work` once batch11 drafts and claims the DIAG item.

**Options**:

- **A (recommended)**: No new batch for a single-item orphan; note for batch11 inclusion. The DIAG outcome is
  determinate (total-vs-partial data loss verdict) and checkable (manifest `written_at` probe). Batch11 will draft it
  naturally.
- **B**: Draft a thin batch11 now with just this one todo. Downside: very thin batch for the overhead; better to let the
  next scheduled audit sweep it in with any other post-batch10 orphans.
- **C**: Do nothing. Downside: the doc rots orphaned until the next scheduled ag-closeout-audit.

## Finding 2 (informational) — suspicious single-tag docs: likely `ui`/`cross-cutting` mistags

Two docs carry bare `asset_group: [defi]` but their content is not defi-specific:

- `architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` — repos [unified-api-contracts,
  unified-trading-system-ui], content is strategy-archetype subsystem DRIFT venue cleanup (cross-cutting architecture).
  Tag should be `[ui]` or `[cross-cutting]`.
- `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` — repos [deployment-ui, unified-api-contracts],
  content is stale deployment-ui bundled capability data. Tag should be `[ui]`.

Both carry `tags: [drift, pacifica, solana, ...]` — likely auto-tagged `defi` because DRIFT/Pacifica are Solana DeFi
venues. Neither is actually scoped to the defi asset_group. Both are **well-covered** by the defi covering set (5
covering plans each cite them), so they are NOT orphaned — they're just in the wrong tranche.

**Recommendation**: Retag both to `[ui]` (their repos scope is deployment-ui / UAC UI-registry). A dedicated
`ui`-tranche audit can then pick them up. This is a quick fix — retag + re-run `check_ag_closeout_linkage.py`.

## Finding 3 — not covered: `defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`

**Category**: orphaned_never_touched (batch9 cites it in a completed todo that only filed the doc — neither of the doc's
2 open todos is drafted anywhere)

**What**: This doc (created 2026-08-06) has 2 open `- [ ]` items:

- `[DATA] P2` — Relaunch `mdps-defi-2025` and `mdps-defi-2026` SPOT VMs via
  `launch-mdps-sharded-backfill.sh defi --year 2025 2026 --env prod` (idempotent skip-if-fresh) → AO-eligible, bounded,
  checkable (manifest-verified row counts)
- `[DATA] P3` — Investigate raising per-date subprocess timeout from 1800s for DeFi years with 10K+ instruments →
  AO-eligible DIAG, bounded

Batch9's citation is a COMPLETED todo that only filed this doc; neither open todo is covered.

**Recommendation**: Both AO-eligible. Include in next scheduled batch (batch11). Standard SPOT VM + DIAG pattern.

## Finding 4 — RESOLVED 2026-08-09: `defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md` (now archived)

**Category**: orphaned_partial_coverage (batch9 covers item 1 but not items 2-3) — **source doc fully closed, all 12
todos done**, archived to
`/plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`.

**What was unclaimed at audit time** (now resolved):

- Item 2: Land stranded `market-tick-data-service` STALLED_HEAD runtime detection — SHIPPED 2026-08-09 as
  `market-tick-data-service@5d633923` (QG cleared after fixing several genuine repo-specific gate failures; see the
  archived doc's Progress Log for the full landing narrative).
- Item 3: Retry-fixable historical `attempted_failed` residue for now-healthy pairs — status not re-verified by this
  edit; re-check the archived doc's own todo list before assuming it's still open (it was closed alongside the other 11
  by the time of archival).

## Finding 5 — partially covered: `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`

**Category**: orphaned_partial_coverage (ownership resolved but SOLBLAZE lst_rates gap backfill unclaimed)

**What**: Sole remaining `- [ ]`: `[DATA] P2. Backfill 2026-08-01..08-03 lst_rates gap for SOLBLAZE-SOLANA` (OOM
window). Operator already ruled Option A (2026-08-06). Backfill is unbounded work until drafted.

**Recommendation**: AO-eligible — standard backfill launcher. Same OOM root cause as Finding 1. Include in next batch.

## Finding 6 — partially covered: `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md`

**Category**: orphaned_partial_coverage (batch10 lists as "archivable_now" but verification gap unclaimed; still
`status: open`)

**What**: Residual: live-manifest verification for `venue=KAMINO_LENDING` rows (case variants) — bounded index read. May
auto-resolve with one more day's cron captures.

**Recommendation**: Mark for re-check in next audit. `assigned_vm: NA` + writer fix already shipped suggests natural
resolution.

## Todos

- [ ] [DOC] P3. **Retag `architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`** from `[defi]` to `[ui]`
      or `[cross-cutting]` (Finding 2) — repos `[unified-api-contracts, unified-trading-system-ui]`, content is
      strategy-archetype subsystem DRIFT venue cleanup (cross-cutting architecture), not defi-specific. Verified
      2026-08-10: still tagged `[defi]`, and — unlike its Finding-2 sibling
      `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` — NOT listed in
      `ui_consolidated_closeout_2026_07_30.md`'s corpus-wide retag todo, so it is genuinely untracked anywhere. Quick
      fix: retag + re-run `check_ag_closeout_linkage.py`.
- [ ] [DATA] P3. **Investigate raising `defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`'s per-date subprocess
      timeout** from 1800s for DeFi years with 10K+ instruments (Finding 3, item 2) — confirmed 2026-08-10 this remains
      the doc's sole open item (its `[DATA] P2` relaunch item is already `[x]`) and is confirmed NOT covered by
      `defi_satellite_ao_dispatch_batch11_2026_08_09.md` (batch11's own "Not extracted this batch" section explicitly
      lists this doc as outside its 18-doc scope). Include in the next scheduled defi batch.

**Already resolved (Finding 1)**: `defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md`'s DIAG todo completed
2026-08-07 (verdict: total data loss for the 3 failed cron dates) and the doc is now fully archived
(`plans/archive/2026_08/issues/defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md`) — no action needed.

**Already resolved (Finding 2, `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` half)**: already
tracked in `ui_consolidated_closeout_2026_07_30.md`'s corpus-wide retag todo — not duplicated here (see the new
`architecture_v2_drift_leg_specs` todo above for the untracked half of this finding).

**Already resolved (Finding 4, item 3)**: `defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md` is now
fully archived with `status: resolved` and 0 open / 12 closed checkboxes — item 3 (retry-fixable `attempted_failed`
residue) confirmed closed alongside the rest, not left open as the prior edit's hedge suggested.

**Already resolved (Finding 5)**: `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`'s SOLBLAZE-SOLANA backfill
completed 2026-08-07 (GCS-verified, `deployment-service@46eddc9` + 3 Cloud Run executions) and the doc is fully
archived (all 7 todos `[x]`) — no action needed.

**Already tracked elsewhere (Finding 6)**: the KAMINO_LENDING live-manifest verification gap is already a real open
todo — `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04_finalize_2026_08_09.md`'s `[DATA] P3`
"Reconcile" todo covers exactly this (bounded VM-backed manifest-index read for the accumulation window, done-when
criterion cites flipping the source doc's checkbox). No duplicate todo needed here.

---

**Parked count reconciliation**: 6 findings = 1 genuine orphan-never-touched + 1 not-covered + 3 partially-covered + 1
informational tag-finding. All 6 written to this doc. ✓

**AO-eligible candidates for next batch (batch11)**: Findings 1/3/4-item-3/5 = ~5 extractable todos. Finding 6 may
auto-resolve. Finding 2 is a tag correction, not a todo.

## Progress Log

- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — 0 checkboxes (audit-report doc); all 6 findings
  re-verified still open/unexecuted, no `batch11` drafted yet. Finding 6 (Kamino) independently re-investigated this
  pass: `bd153821` (the actual venue-fix commit) confirmed NOT yet on `main` (only `live-defi-rollout`), so this doc's
  "may auto-resolve" framing is optimistic — see
  `issues/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md`'s own new Progress Log entry for the
  full re-check + the tracked follow-up todo added there.
- **context-scout 2026-08-07**: populated context_scope (6 entries) — the 4 next-batch AO-eligible findings' target docs
  (1/3/4/5), the `batch10` draft this report checks coverage against, and SKILL.md for process context. Findings 2's 2
  mistag targets and finding 6's target dropped to stay within the minimal-list budget (lower-priority: tag-only fix /
  likely auto-resolving respectively).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — 0 checkboxes (audit-report doc); this
  skill dispatches from real todos, not an `/ag-closeout-audit` finding ledger. Superseded by the 2026-08-08
  `ag_closeout_audit_defi_parked_2026_08_08.md` run's own "Finding 1" re-verification (findings 1/5 archived, finding 3
  item 1 done, finding 6 still correctly NA-gated). No action.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 0 checkboxes -- another scheduled
  /ag-closeout-audit report, 6 findings about OTHER docs' orphaned/partial coverage. Cross-checked against the
  2026-08-08 sibling doc, which re-verified live state: findings 1+5 now resolved+archived, finding 3 item 1 done,
  others still open. Findings ledger, not a task doc. Doc stays `assigned_vm: NA`.
- **2026-08-10 (prose-findings formalization sweep)**: converted 2 prose findings into 2 formal todos (4 already
  resolved/tracked-elsewhere, cited inline). Findings 1/5 confirmed fully archived+resolved; finding 4 item 3 confirmed
  closed (0 open checkboxes in the now-archived source doc); finding 6 confirmed already tracked as a real todo in the
  kamino finalize plan; finding 2's `deployment_ui_capability_bundle_stale_drift_pacifica` half already tracked in
  ui_consolidated_closeout, but its `architecture_v2_drift_leg_specs_and_manifest_residue` half was genuinely untracked
  anywhere — now a real todo; finding 3's item 2 (timeout investigation) confirmed still open and NOT covered by
  batch11 — now a real todo.
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up)**: KEEP-NA, valid — neither open todo is bounded.
  Todo 1 (retag `architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`) names two candidate target tags
  ("to `[ui]` or `[cross-cutting]`") rather than committing to one — the finding's own text is genuinely split between
  a repos-scope reading (`[ui]`) and a content-shape reading (`[cross-cutting]`), so picking the correct tag is a
  judgment call, not a deterministic outcome. Todo 2 ("investigate raising ... per-date subprocess timeout") is
  explicit investigation/design work by its own verb, exactly the class this audit's own instructions flag as
  correctly staying NA even when freshly formalized. Doc stays NA.
