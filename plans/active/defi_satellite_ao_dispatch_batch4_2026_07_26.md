---
doc_type: plan
title: DeFi satellite AO batch 4 — the 2-item delta a concurrent batch3 did not claim
summary: >-
  Fourth AO-dispatch batch for defi, and deliberately a small one. A second `/ag-closeout-audit defi` run executed
  concurrently with the scheduled `ag_closeout_auditor` on 2026-07-26; by the time this run reached Phase 3, that
  sibling had already published `defi_satellite_ao_dispatch_batch3_2026_07_26.md` (12 todos) plus its gated finalize.
  Rather than clobber a same-named file or re-draft competing todos, this run restored the colliding paths untouched,
  re-ran its conflict check against batch3 as a covering plan, and kept only what batch3 provably does NOT claim: two
  bounded `unified-trading-pm` doc-hygiene items on distinct files. Everything else this run found was either already in
  batch3, already dispositioned by it, or non-batchable. Also records three findings batch3 does not carry — a
  duplicate-resolution lesson on the glued-instrument-id doc, an under-report correction, and the residual orphan count
  (21) after batch3 is counted as covering.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-4, satellite-docs, doc-hygiene]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous/AO-dispatched mode, operator away and unreachable), run
  concurrently with the scheduled ag_closeout_auditor's own defi pass. Phase 0 rebuilt the defi membership set (74
  defi-primary docs of 609 corpus-wide), Phase 1 classified per-doc by reading, Phase 3 ran the mandatory conflict check
  twice — once against the pre-batch3 covering set, then again after discovering batch3 on origin.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 4 — the 2-item delta

> **`status: draft` — NOT dispatched.** Per the `/ag-closeout-audit` skill's autonomous-mode rule and CLAUDE.md's "Plan
> destination — ASK BEFORE CREATING" HARD RULE, a skill-drafted AO batch is never auto-flipped to `active`. Flipping
> this (and its gated finalize sibling) to `active` is the operator's explicit call.

> **Concurrency note — read before dispatching.** This plan is the residue of a same-day double-run. The scheduled
> auditor's `/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md` is the primary batch and should be reviewed
> first; this one exists only because two of its author's findings were genuinely uncovered by it. Both todos below are
> `unified-trading-pm` doc operations on DIFFERENT files, so they are safe to run concurrently with each other and with
> every batch3 todo (batch3 touches no `plans/active/issues/defi_code_codex_drift_*` or `…/aave_rate_impact_*` file).

## Todos

- [ ] [DOC] P3. **Flip the provably-completed `[~] [INFRA] P3` D2 item in
      `/plans/active/issues/defi_code_codex_drift_2026_05_27.md` to `[x]`.** The item reads "delete legacy `lst_rates/`,
      `lending_indices/`, `dex_pools/` prefixes in `market-data-tick-defi-prd` (via `gcs_delete_object`) after dedicated
      buckets confirmed authoritative" and carries an in-item deferral: "`lending_indices/` + `dex_pools/`: deferred
      until Gate 2 Solana migration completes". That deferral is resolved — those two prefixes were folded to canonical
      and then operator-prod-DELETED on 2026-07-21, re-probed at 0 objects. **This todo records history; it authorises
      nothing and must run no delete of any kind — it is read-only on GCS, and any prod-bucket delete is human-only per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`.** Re-verify all four citations still resolve before
      flipping: (1) `/codex/02-data/non-canonical-path-inventory.md`'s dated "The DO-NOT-DELETE below is HISTORY"
      banner; (2) CLAUDE.md's "`dex_pools/` + `lending_indices/` — FOLDED + DELETED 2026-07-21" line; (3)
      `/plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`'s frontmatter `status: resolved`; (4) the
      spawned residual `/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`, also
      `status: resolved`. The `lst_rates/` leg is already recorded done (2026-05-28, 1,200 parquets deleted, 64,373
      stale manifest rows pruned) in the item's own text, so all three legs are closed. **Explicitly OUT OF SCOPE — do
      not touch in this or any commit**: `/codex/05-infrastructure/bucket-isolation-model.md`, which still declares
      those same prefixes DO-NOT-DELETE. Whether that codex paragraph or the inventory doc is the stale side is a live
      parked operator question (codex-SSOT edit, blast-radius-gated); this todo must not pre-empt it. Repo:
      unified-trading-pm. Source: `/plans/active/issues/defi_code_codex_drift_2026_05_27.md` (D2). **Done when**: D2
      reads `- [x]` with a dated one-line completion note citing at least two of the four sources above by path, all
      re-verified this pass; no codex file is in the diff; the change ships as a `docs(plans):` commit.
- [ ] [DOC] P3. **Archive `/plans/active/issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md` —
      it reached zero remaining work hours after it was filed.** Filed 2026-07-26 with zero checkboxes and a prose
      "Recommendation" section whose two stated durable-close conditions were both then shipped by
      `/plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s `[BACKEND] P1`: (1) migrate
      `AaveRateImpactCalculator.fetch_data()` off the structurally-zero DefiLlama Yields borrow field onto MTDS
      `lending_indices` (`features-service@b0845d83`), and (2) re-point `strategy_service/pnl/engine/orchestrator.py` to
      the writer's real `feature_group="rate_impact"` (`strategy-service@59dd0638`). **First re-verify, then archive** —
      confirm both SHAs are ancestors of `origin/live-defi-rollout` in their own repos and that a fresh full read of the
      issue doc finds no prose residual beyond those two items; if either check fails, do NOT archive, and instead
      record why in the doc. Then run the standard 6-step archival ritual, including step 6 — grep the corpus for every
      referrer of `aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26` and repoint each to
      `/plans/archive/issues/` (batch2's own shipped `[BACKEND] P1` cites it as `Source:` and will need repointing).
      Repo: unified-trading-pm. Source:
      `/plans/active/issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md`. **Done when**: both
      SHAs are verified on `origin/live-defi-rollout`, the doc is at `plans/archive/issues/` with `status: resolved` and
      a populated `resolved_by:`, and every corpus referrer resolves to the archived path (or the todo is closed with a
      written reason it was NOT archived).

## Deferred — dropped by the conflict check against batch3 (cite, do not re-draft)

Three candidates this run had drafted were dropped once batch3 was discovered on origin. Recorded so a future run does
not re-derive them:

- **The three read-only audits in `/plans/active/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`** —
  batch3's `[DATA] P3` at its "Two read-only reconciliation checks" todo already claims sub-items (a) the three
  `_DEFAULT_PROTOCOLS` lists versus `SUBGRAPH_IDS`, and (b) the FRAX-ETHEREUM `vault_share_price` scheduling check, with
  the same read-only and no-`fluid`-without-a-collector guardrails. Sub-item (c), the MORPHO-ARBITRUM/OPTIMISM/POLYGON
  `SUBGRAPH_IDS` scoping re-verification, is dispositioned by batch3 as `skip_covered` — routed to
  `/plans/active/defi_expected_unattempted_seeder_design_2026_07_26.md`'s `[OPERATOR] P0`. That routing is arguably wide
  (a scoping re-read is bounded; the `[OPERATOR] P0` is the capability-versus-collectibility judgment), but it IS a
  stated disposition, and drafting a competing todo against it is exactly what the conflict check forbids. Flagged for
  the operator's eye, not re-drafted.
- **The agent-orchestrator M3 done-gate exception** — batch3 drafted it directly as an explicitly `[CROSS-AG]`-tagged
  `[INFRA] P3`. This run had instead routed it out to the `ao` tranche. Batch3's approach is live; no competing todo.
- **The targeted single-day glued-instrument-id manifest re-verify** — a clear duplicate of the consolidated closeout's
  own open todo; see the Notes section for the full resolution, since it is the most instructive of the three.

## Deferred — non-batchable orphans (21 residual, unchanged)

With batch1, batch2, batch3, the consolidated closeout, the aggregated-sources digest and every forked child counted as
covering, **21 defi-primary docs remain orphaned** and every one of their remaining items is from the non-batchable
taxonomy: 13 operator-gated, 3 time-gated, 1 too-large-or-risky, 3 human-only, 1 conflict-gated (whose only batchable
half is this plan's first todo). The per-doc breakdown with evidence lives in
`/plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md` and
`/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s own Deferred sections — this plan references them
rather than duplicating a third copy. **defi has reached the skill's documented stop condition**: report the residual to
the operator as "needs direct human action, not another batch" rather than spinning a batch5 that cannot extract
anything new.

Two additions this run makes to those lists, not present in either:

- **`/plans/active/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`** — operator-
  gated. Its one open todo is a `[DESIGN] P1` "demote `perp_funding` from a captured raw type to a DERIVED interval
  view", self-tagged `[OPERATOR-DECISION]`, already queued as entry 4 in
  `/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`, and explicitly excluded by batch1 as never
  AO-eligible. Its own as-written gate ("todo 4's parity results") is unsatisfiable — todo 4 closed MOOT 2026-07-16 with
  no parity check ever run. Do not re-ask; it is already in the operator queue.
- **`/plans/active/defi_expected_unattempted_seeder_design_2026_07_26.md`** — operator-gated by explicit ruling
  BLK-3221d4b3. All 4 todos sit behind its own `[OPERATOR] P0`. Correctly a human plan (`assigned_vm: NA`).

## Notes — findings recorded, not actioned

1. **A zero-citation doc that is NOT orphaned — the most instructive result of this run.**
   `/plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md` scored ZERO covering-plan
   citations by filename across all 17 covering docs, and carries prose-only residual with no checkbox ("Not yet done:
   the 12 CURRENT glued objects need one more targeted rebuild pass (single-day, 2026-07-22, cheap), re-verify 0 glued
   ids") — i.e. it tripped every heuristic for "orphaned_never_touched with real work". The conflict check nonetheless
   dropped it: `/plans/active/defi_consolidated_closeout_2026_07_18.md` carries an OPEN `[DATA] P2` ("21 glued-id rows
   found in the 2026-07-23 manifest rebuild — writer fix SHIPPED, re-verify pending") that claims exactly that ground
   under a different framing, and further records that the 12-`liquidations` half is ANSWERED and fixed
   (`market-tick-data-service@f2e3ad41`; verify tool promoted to `scripts/one_offs/verify_defi_glued_ids_2026_07_24.py`
   at `70b9a81a`). Verified independently in the live repo rather than taken from the doc: `liquidations_handler.py:546`
   now carries a `del ts_label` with the comment "no longer embedded in the empty-marker filename", and
   `_rebuild_defi_n5.py:36-38`'s `ROWCOUNT_VERIFIED_DATA_TYPES` is the expanded 6-type frozenset (`vault_share_price`,
   `liquidations`, `lending_indices`, `lst_rates`, `risk_params`, `dex_pool_swaps`). **Lesson for the skill: a
   filename-citation count of 0 does not prove orphaned** — covering plans routinely describe the same work in their own
   words. Grep-then-READ, never grep-then-conclude.
2. **An under-report corrected.** `/plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md` was
   in no Deferred section of batch2, which extracted only its one trivial test-import-alias fix. Its real residual is
   prose-only and large: the "5 NEW, still-unfixed bugs found" section (66 catalog rows across
   `RULES_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_EVENT_SETTLED`, `ML_DIRECTIONAL_EVENT_SETTLED`,
   `MARKET_MAKING_EVENT_SETTLED`, `VOL_TRADING_OPTIONS`, each `xfail(strict=True)` in `strategy-service@03310bdf`) plus
   its "What's still needed" items 1 and 2. Batch3 has since drafted the mechanical archetype-slot sweep and the
   strategy-side legs from this doc, which is a real improvement, but the 5 xfail archetypes each still need a
   per-archetype trading-parameter/design decision before the mechanical fix becomes dispatchable — human-only for now.
   **Scope caveat worth an operator glance**: 4 of those 5 archetypes are sports/prediction/options, not DeFi, so this
   doc's residual is largely CROSS-AG despite its `asset_group: [defi]` tag and a defi-only batch structurally cannot
   own it.
3. **Two same-named files were NOT clobbered.** This run had authored `defi_satellite_ao_dispatch_batch3_2026_07_26.md`
   and its `_finalize` sibling before discovering the scheduled auditor had already published both paths to
   `origin/live-defi-rollout`. Both were restored to origin's content and removed from this worktree's contribution
   entirely (never staged, never force-pushed), and this batch4 pair was authored instead. Recorded because the
   near-miss is the interesting part: two independent `/ag-closeout-audit <tranche>` runs on the same tranche on the
   same day collide on a deterministic `batchN_<date>` filename, and nothing in the skill currently warns about it. A
   future skill revision should either check origin for an existing `<tranche>_satellite_ao_dispatch_batch*_<date>`
   before choosing N, or take a lease.

## Coverage caveats (stated, not hidden)

- **No Workflow or sub-agent dispatch tool was exposed to this worker**, so the skill's Phase-1 per-doc fan-out ran
  INLINE and single-threaded. Coverage was prioritised rather than uniform: every doc batch2 deferred, every doc with
  zero or weak covering-plan citations, and every doc created after batch2's Phase-0 window was read directly; docs
  batch2 had already classified as covered with cited evidence were spot-verified against their covering todo rather
  than re-read end to end.
- **A defi-only shard is structurally blind to cross-tranche contradictions** (the skill's own warning). Two are flagged
  above rather than fixed: the cross-AG residual in Notes item 2, and the agent-orchestrator M3 todo now living inside a
  defi batch.

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — why todo 1 records history and authorises nothing; the
  prefix delete it closes was operator-executed 2026-07-21, and no agent may run a prod-bucket delete regardless.
- `/codex/11-project-management/cross-reference-path-convention.md` — the leading-slash repo-root-relative form every
  referrer repointed by todo 2's step 6 must use.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (Dispatch-scope eligibility) — the test every
  Deferred entry above was classified with.

## Deferred work — migrated to: N/A (this plan itself is not deferred/migrated)

Each Deferred section above cites its own source doc or batch3 directly as the successor reference; none of them claims
this plan was migrated elsewhere.
