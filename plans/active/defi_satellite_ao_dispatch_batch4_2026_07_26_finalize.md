---
doc_type: plan
title: DeFi satellite AO batch 4 — finalize (reconcile the 2 source docs + confirm the stop verdict + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch4_2026_07_26.md — machine-held via depends_on plus gate_on_depends:
  true until both of that plan's todos are done. Small by construction, mirroring the batch2-finalize and
  batch3-finalize pattern: reconcile the two source docs, re-check batch4's dropped-by-conflict-check items in case
  batch3's competing claims changed, record an explicit stop-or-continue verdict for the defi tranche with its residual
  orphan count, then archive batch4. Also status: draft until the operator approves batch4 itself.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch4_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md section 4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the defi batch1, batch2 and batch3 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 4 — finalize

> **`status: draft` — NOT dispatched**, and additionally machine-gated on
> `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26.md` (`depends_on` plus `gate_on_depends: true`),
> so even once flipped `active` no todo below is queued until both batch4 todos are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation first and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P3. **Reconcile both source docs — DONE 2026-07-31.** (1)
      `/plans/active/issues/defi_code_codex_drift_2026_05_27.md` — **confirmed**: D2 reads `- [x]` with a dated note
      ("CLOSED 2026-05-28 leg + FOLDED+DELETED 2026-07-21 for the remaining two, re-verified 2026-07-28") citing all
      four of batch4's named sources. The flip landed in `unified-trading-pm@fdbafb3be` — a large same-day batch commit
      ("archive 22 zero-todo docs, flip 22 doc-only-quick fixes...") that also touched 13 OTHER codex files
      (`canonical-cutover-register.md`, `cross-asset-canonical-target-ssot.md`, `defi-canonical-naming-ssot.md`,
      `defi-data-type-taxonomy.md`, `defi-data-types-catalog.md`, `four-surface-reconciliation-procedure.md`,
      `gcs-and-manifest-delete-safety-protocol.md`, `honest-coverage-model.md`, `mvp-scope-canonical.md`,
      `reconciliation-finding-taxonomy.md`, `sports-data-types-catalog.md`, `solana-defi-coverage.md`,
      `deployment-observability.md`) — so the literal "no codex file touched in that commit" premise does not hold for
      the commit as a whole; **but the one codex file this check exists to protect,
      `/codex/05-infrastructure/bucket-isolation-model.md` (the parked DO-NOT-DELETE operator question), is NOT among
      them** — `git show --stat fdbafb3be | grep bucket-isolation-model` returns nothing, so the substantive concern
      (this todo silently pre-empting the parked operator question) did not occur. Re-read the doc end to end: the only
      remaining `- [ ]` is D15 (HYPERLIQUID/ASTER `DEFI_VENUE_PHASE`/legacy-corpus migration) — its classification half
      was already operator-ruled 2026-07-27 (keep both venues pure CEFI), but the legacy-corpus migration itself is
      unscoped and its adjacent `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` cross-reference
      is flagged (not blocking) as needing an operator confirmation — so the doc correctly stays `status: open`, not
      flipped. (2) `/plans/archive/issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md` —
      **confirmed directly** (no fallback reason needed): the file is now at `plans/archive/issues/` with frontmatter
      `status: resolved` and `resolved_by: features-service@b0845d83, strategy-service@59dd0638` populated — the 6-step
      archival ritual batch4's own todo 2 had explicitly left incomplete ("NOT done: the file was NOT moved... this pass
      was scoped to verify-and-flip only") was completed in the SAME `PM@fdbafb3be` batch commit as the D2 flip above
      (`git log --follow --name-status` shows an `R083` rename `plans/active/issues/... → plans/archive/issues/...` in
      that commit), with a small referrer-path follow-up in `PM@090ce516b` ("archive onchain manifest backfill issue
      doc"). **Done**: both source docs' states confirmed by reading, one-line note each above.
- [ ] [REVIEW] P3. **Re-check batch4's three dropped-by-conflict-check items against batch3's live state.** Batch4
      dropped them because batch3 claimed the same ground. Re-read batch3's corresponding todos: if any has since been
      cancelled, superseded, or re-scoped away from that ground, the dropped item becomes uncovered again and must be
      re-tracked (name it here; do NOT draft it in this finalize plan). Pay particular attention to the MORPHO-ARBITRUM/
      OPTIMISM/POLYGON `SUBGRAPH_IDS` scoping re-verification, which batch3 dispositioned as `skip_covered` by routing
      it to `/plans/active/defi_expected_unattempted_seeder_design_2026_07_26.md`'s `[OPERATOR] P0` — if that
      `[OPERATOR] P0` is resolved in a way that does not actually answer the scoping question, the bounded read-only
      re-verification is genuinely orphaned and needs a home. **Done when**: each of the three has either a confirmation
      batch3 still covers it, or a named re-track recommendation.
- [ ] [REVIEW] P3. **Record an explicit stop-or-continue verdict for the defi tranche.** Batch4's assessment is STOP:
      after batch3 is counted as covering, 21 defi-primary docs remain orphaned and every one of their remaining items
      is from the non-batchable taxonomy (13 operator-gated, 3 time-gated, 1 too-large-or-risky, 3 human-only, 1
      conflict-gated whose only batchable half batch4 already shipped). Re-test that after todo 2: if no gate cleared
      and no new orphan appeared, write the stop verdict into this doc with the current residual count so a future
      scheduled invocation does not spin a batch5 that cannot extract anything. If a gate DID clear, name the
      candidate(s) instead. **Done when**: an explicit stop-or-continue verdict with the current residual orphan count
      is written into this doc, dated.
- [ ] [DOC] P3. **Archive `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26.md`** via the standard
      6-step ritual: migrate any still-live Deferred item to a tracked todo elsewhere (todos 2 and 3 above should have
      resolved or re-confirmed each — verify none silently vanish) → add the archive banner → run the codex-alignment
      check (batch4 introduces no new durable contract; confirm that is still true) → grep the corpus for every referrer
      of `defi_satellite_ao_dispatch_batch4_2026_07_26` and repoint each path per the leading-slash convention → confirm
      `locked_by` is empty. **Done when**: the plan is in `plans/archive/2026_07/`, every corpus referrer resolves to
      the new path, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/11-project-management/cross-reference-path-convention.md` — the reference form todos 1 and 4 must preserve.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — the reason todo 1 verifies no codex file was touched:
  the DO-NOT-DELETE paragraph in `/codex/05-infrastructure/bucket-isolation-model.md` is a parked operator question, not
  batch4's to resolve.
