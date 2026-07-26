---
doc_type: plan
title: CeFi satellite AO batch 2 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch2_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 17 of that plan's todos are done. Mirrors batch1-finalize's pattern (reconcile each distinct source
  doc's checkboxes independently once its batch-2 todo lands, then re-check the Deferred operator-gated/time-gated/
  human-only items for any that have since cleared), then archives batch2 via the standard 6-step ritual. Also carries
  the follow-up for batch2's 2 non-actioned findings (3 mistag retags + 1 archivable_now doc).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch2_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan, mirroring the cefi batch1 + sports batch2-5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi satellite AO batch 2 — finalize

> **Machine-gated on `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 17 tasks in that plan are `done`. `sequential: true` because todo 2
> (deferred re-check) needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 17 distinct source docs' checkboxes.** For each of
      `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in its
      named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-2 commit(s) that shipped it —
      verify the actual shipped commit exists before citing it. For each source doc: after flipping, re-check whether it
      now has 0 open todos remaining (checkbox AND prose-form — do not trust checkbox count alone). Only flip a doc's
      `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 17 source-doc checkboxes/sections
      are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped to
      `status: resolved`. — **DONE 2026-07-26 (slot-2, review).** Audited all 17 todos' source docs against
      `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`. **15 of 17 were already correctly reconciled** by the executing
      workers as part of doing the work (checkboxes flipped in-line, commits verified to exist:
      `execution-service@1267290`, `instruments-service@ee19f6f3`/`@d2796158`/`@81bf5e17` [via UAC],
      `deployment-service@d5fde721`/`@54aa6f5`, `market-tick-data-service@ec0df878`/`@ed102ef8`/`@08f15f26`/`@31958a05`,
      `unified-api-contracts@c144f975`/`@54325576`/`@b0547c36`, `deployment-service@3d99865`/`@6eed099`, and the
      DERIBIT-gate re-verify re-confirming genuine FAIL). **2 genuine gaps found + fixed**: (1)
      `data_completion_cefi_2026_07_15.md`'s "E6 CF-7 relabel" checkbox (item -002's source) was still `[ ]` — flipped
      `[x]` with the diagnostic evidence citation
      (`issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`). (2)
      `cefi_residual_followups_after_honest_done_2026_07_17.md` (item -010's source, 4 sub-items) had ZERO of its 4
      sub-items annotated: flipped sub-item 2 (features-service image build, `features-service@586a5cea`/`@8661a7af`
      verified) and sub-item 4 (codex SSOT reconciliation, `unified-trading-pm@8e435b425` verified) to `[x]`; annotated
      sub-items 1 and 3 as **STILL OPEN**, correctly NOT flipped (real remaining work, spun to
      `issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` todos 1/3). **No doc reached 0 open todos** — every
      source doc checked (17 distinct todos across 18 physical doc files, since item -015 cites 2 sibling docs) carries
      genuine remaining prose or checkbox work (verified past checkbox-count alone — e.g.
      `cefi_universe_capture_rule_2026_06_23.md` shows 0 unchecked boxes but has a real prose-form open TODO, a
      scaffolded live-liquidity hook + an unactioned side-finding, so it correctly stays `status: open`, not flipped to
      `resolved`) — so no `status: resolved` flips were made this pass.
- [x] ✅ [REVIEW] P1. **Re-check the 10 operator-gated + 1 time-gated + 1 human-only Deferred items from batch2's own
      doc**, now that time has passed and batch2's own todos have landed. For each of the 12 Deferred items: re-read the
      specific gating ground (operator decision, elapsed-time condition, or design-session need) to check if it has
      since cleared — if so, extract it as a new tracked todo in a follow-up `batch3` (do not draft it directly here,
      this finalize plan's own scope is reconciliation not fresh drafting); if still genuinely unresolved, leave it
      explicitly deferred (not speculative) — do not re-surface an already-asked operator question a second time, just
      note the re-check happened and it's still awaiting an answer. **Done when**: each of the 12 Deferred items has
      either (a) a note that it's ready for `batch3` extraction because its gate cleared, or (b) an explicit re-verified
      confirmation the gate is still open. — **DONE 2026-07-26 (slot-2, review).** Re-checked all 12 Deferred items —
      **11 of 12 remain genuinely open, no gate change** (verified via `last_updated`/live prerequisite-condition
      re-checks, not assumption): `aster_and_cefi_rolling_adv_feature_2026_07_21.md` (design conversation still not
      held), `crypto_alpha_research_2026_07_24.md` (no operator triage occurred),
      `cefi_backfill_per_day_catalogue_reload_2026_07_20.md` (Option-A gate — the OOM investigation it's contingent on,
      `cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`, still has 2 open items),
      `cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md` (no policy ruling),
      `cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md` +
      `onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` (both gated on batch1's EXTENDED-STARKNET
      characterization todo, confirmed still `[ ]` unchecked in `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`),
      `instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` (Option A/B DESIGN todo unchanged since 2026-07-08),
      `l2_book_microstructure_capture_2026_07_13.md` (live-WS relaunch decision — the referenced pause-confirmation doc
      `cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md` resolved the outage-vs-intentional AMBIGUITY in
      2026-07-14, not the "should the pause lift" decision itself, which is still open; the backlog-hygiene park item is
      also still uncovered/operator-gated), `vol_dvol_backtestable_engines_2026_07_13.md` (`BLK-011c84cb` still
      standing), `cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md` (time-gated —
      `cefi-recapture-sweep-complete` condition confirmed still `value: false` via live `/api/state`),
      `fail_hard_canonical_enforcement_design_2026_07_20.md` (the genuine `[DESIGN] P1` §5-gaps todo still needs a
      dedicated design session — but flipped its 3 stale checkboxes [items 1/3/5] to `[x]` per batch2's own
      recommendation, since `market-tick-data-service@e49e1395` + `unified-api-contracts@989e9d16` verified already
      shipped them). **1 of 12 gate genuinely cleared, but not into a batch3 todo** —
      `cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12.md`'s "PACIFICA-SOLANA historical depth" 3-option design
      fork is now **MOOT**: PACIFICA-SOLANA was permanently culled/quarantined venue-wide on 2026-07-16 (before batch2
      even ran), so there is no more "how do we backfill it" decision to make — option 3 (accept honest absence) is the
      outcome by construction. Annotated a `⛔ MOOT` banner in that doc rather than drafting a batch3 todo, since there
      is no work to extract (the decision evaporated, it wasn't answered). That doc's OTHER item (1, BLOCKED-CREDENTIALS
      Tardis-lighter entitlement) remains genuinely open, unaffected.
- [x] ✅ [DOC] P2. **Action batch2's 2 non-batched findings.** (1) Retag the 3 mistagged docs named in batch2's "Note —
      3 mistags found" section (`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`,
      `mtds_ungated_test_families_2026_07_17.md`, `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`)
      — read each doc's real content to decide the correct `asset_group` (likely `cross-cutting` or `meta` for all 3,
      confirm per-doc, do not assume), fix the frontmatter, and re-run
      `scripts/plan-hygiene/check_ag_closeout_linkage.py` after each retag (a doc just retagged can be newly orphaned
      within its NEW ag family if nothing there references it yet — add a one-line link to that ag's aggregated-sources
      digest if so). (2) Archive `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` (batch2's "Note — 1 doc
      found archivable_now") via the standard 6-step ritual. **Done when**: all 3 mistagged docs carry a corrected
      `asset_group` with `check_ag_closeout_linkage.py` passing 0 new orphans, and the archivable_now doc is moved to
      `plans/archive/2026_07/` with every corpus referrer fixed. — **DONE 2026-07-26 (slot-6, data_engineering).** (1)
      All 3 retagged `asset_group: [cross-cutting]` (per the ag-closeout-audit skill's own ruling that ao/ci/infra-class
      content — CI/tooling breaking-change-differ + MTDS test-gating hygiene + multi-agent worktree-collision — stays
      tagged `cross-cutting`, no dedicated ao/ci/infra enum value exists; verified per-doc, not assumed: all 3 are
      generic CI/multi-agent-safety concerns, not cefi-specific despite cefi-triggering incidents).
      `check_ag_closeout_linkage.py` confirms 0 orphans (baseline 0) — `cross-cutting` is EXEMPT by construction from
      this check (docspec: multi-value/cross-cutting/meta/infrastructure asset_group is exempt), so no digest-link
      needed. (2) `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` — verified all todos genuinely `[x]` closed
      (0 remaining `- [ ]`), both original gaps (OKX options_chain real rows 2026-07-13; DERIBIT-COMBO catalogue
      backfill + MVP-scope decision 2026-07-14/16) confirmed shipped. 6-step ritual: no genuine open DEFERRED prose →
      archive banner added + `status: resolved` (`resolved_by` stamped) → codex-alignment check confirmed
      `/codex/02-data/mvp-scope-canonical.md` (v16 entry) + `/codex/02-data/honest-absence-downstream-handling.md`
      already correctly reflect this doc's shipped contract, no update needed → no new durable contract to add → 3 live
      corpus referrers fixed to the new path (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`,
      `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`, `tardis_concurrent_ip_lockout_2026_07_12.md`; 1 frozen
      historical note in `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s own "Note" section + `plans/archive/**`
      mentions correctly left alone per the batch1-finalize precedent) → `locked_by` confirmed empty. `git mv` to
      `plans/archive/2026_07/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`. `check_frontmatter_schema.py`
      (1794 docs, 0 violations) and `check_reference_paths.py` (existence: 947 ≤ baseline 956, shrinking) both green
      post-change. — `unified-trading-pm@(this commit)`.
- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all 12 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `cefi_satellite_ao_dispatch_batch2_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
