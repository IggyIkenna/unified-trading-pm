---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 22 — 2026-08-21
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-21 `/na-eligibility-audit` sweep (batch 3 of 3, disjoint
  doc list) — 4 conflict-cleared, bounded/deterministic items pulled from 3 source docs (RECLASSIFY per-todo split
  each). Pure mechanical/bounded-engineering tasks with no open design or judgment call left in the extracted scope;
  each source doc's own remaining items stay `assigned_vm: NA` for genuinely gated/investigative work. Conflict-
  checked against every cross-cutting satellite batch (1b, 13-21) and the consolidated closeout doc before drafting
  — no item here duplicates ground an existing dispatched todo already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, satellite-docs, na-eligibility-audit]
related:
  [
    /plans/active/issues/walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/plan_reconciler_full_corpus_sweep_2026_08_20.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch22_2026_08_21_finalize.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.0
assigned_role: backend_engineer
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/plan_reconciler_full_corpus_sweep_2026_08_20.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
source: >-
  na-eligibility-audit 2026-08-21 (cross-cutting tranche, batch 3 of 3) — RECLASSIFY-per-todo-split extraction from
  3 source docs whose remaining open work is a MIX of bounded/mechanical items (extracted here) and genuinely
  gated/investigative items (left NA on the source doc).
---

# cross-cutting satellite AO dispatch batch 22

> **Status: active.** 4 items, conflict-checked clean against every active `assigned_vm: planning` doc and every
> prior cross-cutting satellite batch (1b, 13-21). Each item cites its exact source todo; do NOT re-derive scope
> from the source doc's other (NA-staying) items.

## From `walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md`

- [x] ✅ [BACKEND] P1. **Add a pre-write safety snapshot for agent-authored client-artefact edits.** Before a
      single-file structure-pass agent begins editing a large, contested file (the pattern that produced 2 of the 3
      losses this issue documents), snapshot its current content (content-hashed, timestamped) to a location
      outside the shared working tree — a scratchpad or a dedicated GCS prefix, not another spot in the same
      contended checkout — so a repeat working-tree loss has a designed recovery path instead of a lucky scratchpad
      find. Done when: the snapshot mechanism exists, is exercised by at least one real edit session, and its
      recovery path is exercised once (restore from a snapshot, confirm content matches). Source:
      `walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md` todo 2 (the pre-write safety snapshot
      item — NOT todo 1 "determine the actual reset mechanism" or todo 3 "investigate whether this file is
      unusually contended," both genuine root-cause investigation left on the source doc). ✅
      `unified-trading-pm@d079c9322e` — `scripts/dev/pre-write-safety-snapshot.sh` (snapshot/list/latest/restore),
      snapshots stored content-hashed + timestamped outside any repo's working tree (default
      `$HOME/.uts-pre-write-snapshots`). Exercised end-to-end this session against this very plan doc: snapshot
      taken pre-edit, then restored and confirmed byte-identical (sha256-verified) against the pre-edit content.
- [ ] [DOC] P2. **Add the 2026-08-20 shared-checkout content-loss incident to
      `/codex/05-infrastructure/per-tab-worktrees.md`** as a concrete case study alongside the existing
      multi-agent-collision documentation — the existing guidance anticipates loss occurring via a git operation
      this session performed; this incident's losses occurred independently of one (a working-tree reset with no
      corresponding commit history, and an agent's direct edits never surviving to a commit). Cite the source doc's
      full "What happened, in order" section verbatim as the case study's basis. Source:
      `walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md` todo 4.

## From `venue_readiness_and_registry_hardening_2026_08_16.md`

- [ ] [AGENT] P1. **Declare capability for the 3 conflict-free undeclared DeFi venues** —
      `FLUID-ARBITRUM`/`SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM` only. Registered in `ALL_DEFI_VENUES` but no
      entry in `VENUE_DATA_TYPE_CAPABILITIES`, so they're invisible to the (venue, data_type) denominator and to
      `generate_venue_consumability_report.py`'s step-17 sweep. Add capability records (dex-swaps/dex-pools data
      types, per the MTDS sub-bucket that already backfills them) so the denominator and the consumability report
      both see them. **Do NOT also add the 5 `ALCHEMY-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}` gas-fee-oracle
      spellings from the same source todo** — the 2026-08-17 na-eligibility-audit pass on the source doc found
      these 5 directly contradict a shipped fix (`unified-api-contracts@21a7e5c305`, 2026-08-09) that deliberately
      deleted these exact composite-spelling keys as phantom declarations no writer can match; re-adding them needs
      an explicit operator ruling, still open on the source doc as `BLOCKED-OPERATOR-DECISION`. Done when:
      `VENUE_DATA_TYPE_CAPABILITIES` carries the 3 Fluid/Sushiswap entries (not the 5 Alchemy ones), the
      denominator/consumability-report scripts pick them up without further edits, `unified-api-contracts`
      quality-gates green. Source: `venue_readiness_and_registry_hardening_2026_08_16.md`, "Declare capability for
      the 8 undeclared DeFi venues" todo (narrowed to its conflict-free 3-venue subset only).

## From `plan_reconciler_full_corpus_sweep_2026_08_20.md`

- [ ] [SCRIPT] P2. **Normalize non-standard checkbox markers (`[~]`) and bare status lines with no `[ ]`/`[x]`
      marker at all to standard `[ ]`/`[x]` syntax**, corpus-wide. Confirmed in 6+ docs at sweep time:
      `bucket_fold_ml_2026_07_17.md`, `bucket_fold_features_2026_07_17.md`, `data_completion_defi_2026_07_15.md`,
      `sports_cf8_available_at_backfill_regression_2026_07_13.md` (a "CANCELLED" line),
      `mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md`, and one more from the defi cluster
      (re-grep for the exact non-standard-marker signature before fixing — the 6 named docs may have already been
      touched by other work since the 2026-08-20 sweep; re-verify each is still non-standard before editing).
      Mechanical, no judgment call — normalize the marker to `[x]` if the surrounding text marks the item done,
      `[ ]` otherwise; do not change any item's done/open status, only its marker syntax. Both classes are invisible
      to the standard checkbox-grep every audit/backlog tool in this corpus uses, silently undercounting open-todo
      totals. Done when: a corpus-wide grep for `- \[~\]` and for a bare status line with no `[ ]`/`[x]` marker
      returns 0 hits in `plans/active/`. Source: `plan_reconciler_full_corpus_sweep_2026_08_20.md`, "Non-standard
      checkbox markers" todo (operator-approved as a single grep-and-fix pass).

## Progress Log

- **2026-08-21**: drafted by na-eligibility-audit (cross-cutting tranche, batch 3 of 3). All 4 items conflict-
  checked against every existing cross-cutting satellite batch (1b, 13-21) and the consolidated closeout — no
  duplication found. The other 3 items on `plan_reconciler_full_corpus_sweep_2026_08_20.md` that describe similar-
  looking "class-level" fixes (`locked_by` boilerplate root-cause, context-scout append-corruption repair,
  near-complete auto-fold, 16 archive candidates, 153 P3 long-tail) were deliberately NOT extracted here — none of
  them carry an enumerated, currently-verified target list in that doc's own text (the raw per-finding transcripts
  from that one-off sweep were explicitly not preserved), so a worker picking them up would need to re-derive the
  candidate set first rather than execute against a fixed list — not the bounded-outcome bar this split applies.
- **2026-08-21 (slot 13)**: item 1 shipped — `unified-trading-pm@d079c9322e` adds
  `scripts/dev/pre-write-safety-snapshot.sh` (snapshot/list/latest/restore subcommands; content-hashed +
  timestamped snapshots under `$HOME/.uts-pre-write-snapshots`, outside any repo's working tree). Shipped as a
  direct-push dirty-deps carve-out — quickmerge Stage 1.5 fails fleet-wide right now on the pre-existing,
  unrelated `deployment_api_imports_deployment_service_tier_violation_2026_08_21.md` tier violation;
  `quality-gates.sh` was green on this exact change before the push. Mechanism exercised end-to-end this session
  (snapshot → list → latest → restore, sha256-verified byte-identical match) against this plan doc's own edit.
