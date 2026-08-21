---
doc_type: issue
title: "Recurring corpus pattern: Progress Log records 'extracted to X', checkbox never flipped to match (4 instances, one tradfi audit pass)"
summary: >-
  na-eligibility-audit (tradfi tranche, 2026-08-16) independently hit the SAME defect shape 4 separate times in one
  run: a doc's Progress Log has a dated entry saying "ruled + extracted to <new AO-dispatch doc>", but the
  corresponding `- [ ]` checkbox was never flipped to `[x]` citing that extraction — so the doc still LOOKS like it
  has open, undispatched work even though the real work already moved to a live, dispatchable AO plan elsewhere. Each
  instance was only caught because this run happened to read the doc's own todos against its own Progress Log
  side-by-side; a mechanical checker doing that cross-check would have caught all 4 without a full agentic re-read.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, na-eligibility-audit, citation-flip-gap, checkbox-format, process-improvement]
related:
  [
    /plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
parent_epic: agent_operating_framework_master
source: "na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b, 2026-08-16 — found incidentally while processing
  KEEP-NA-STALE-DUPLICATED and KEEP-NA-STALE-ITEMS verdicts"
assigned_vm: NA
created: 2026-08-16
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    unified-trading-pm/cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
---

# Recurring pattern: "extracted to X" recorded in Progress Log, checkbox never flipped

## What happened, 4 confirmed instances in one tradfi-tranche run (2026-08-16)

1. `tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md` — sole todo, Progress Log said "extracted
   to `tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md`", checkbox still `- [ ]`. Fixed + archived
   (0 open todos once flipped).
2. `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` — CODE P2 todo, Progress Log said "extracted to
   `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`", checkbox still `- [ ]`. Fixed (1 todo
   remains, genuinely gated).
3. `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` — P2-OPERATOR-DECISION todo, Progress Log said
   "extracted to `tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`", checkbox still `- [ ]`. Fixed.
4. `data_completion_tradfi_2026_07_15.md` — E7 todo, Progress Log said "extracted to
   `tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md`", checkbox still `- [ ]`. Verified real+live but could
   NOT be fixed this pass — the doc sits exactly at the 1000L hard cap (see the sibling issue doc this same run
   filed: `data_completion_tradfi_line_cap_blocks_e7_stale_item_close_2026_08_16.md`).

All 4 share the same root shape: whoever authored the extraction (na-eligibility-audit follow-up Q&A rounds,
2026-08-16, per the Progress Log entries' own dating) wrote the narrative note but stopped one step short of the
mechanical checkbox flip in the SAME doc. Given all 4 landed on the SAME date across DIFFERENT docs, this reads like
a systemic gap in that day's Q&A-round follow-through, not 4 independent one-off misses.

## Why it matters

A doc in this state is doubly wrong: (a) it still counts as "open work" toward the `assigned_vm: NA` corpus size
ratchet even though the real work has moved elsewhere and is already dispatchable, and (b) any future audit pass
(or a human) reading the checkbox alone — without also reading the full Progress Log — will re-diagnose the same
"is this extracted?" question from scratch, exactly the wasted-re-read cost `/na-eligibility-audit`'s incremental
mode exists to avoid.

## Recommended decision

A mechanical checker (not a full agentic re-read) could catch this class directly: for every `assigned_vm: NA` doc
with open todos, grep its own Progress Log for `extracted to` / `RULED` phrasing naming another doc path, then check
whether that SAME doc path appears as a citation on any currently-OPEN checkbox in the SAME file. A hit with no
matching open-checkbox citation is exactly this defect shape. This would surface future instances without needing a
full per-doc agentic classification pass to notice them incidentally, the way this run did.

## Todos

- [x] ✅ [SCRIPT] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 2 (na-eligibility-audit 2026-08-17). Prototype a mechanical checker (standalone script, or a mode on
      `generate_na_doc_tranche_inventory.py`) that flags a doc where the Progress Log's own "extracted to `<path>`"
      / "ruled ... extracted to" phrasing names a doc that is NOT cited on any currently-open checkbox in the same
      file — the exact shape of all 4 instances found this run. Done when: run against the current full NA corpus
      and it re-discovers these 4 (now-fixed) instances as a smoke test, then run for real to find any others still
      outstanding corpus-wide (not just tradfi).
- [ ] [DOC] P3. **Narrowed 2026-08-21 (na-eligibility-audit, cross-cutting) — 1 of 3 instances already resolved, 2
      remain live**, of the 3 instances `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 2's
      checker found: `plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` is now
      MOOT — all 3 of its own todos are `[x]` checked (verified 2026-08-21), so there is nothing left to route for
      that instance. The remaining 2 still need routing to their owning (sports) tranche's next
      `/na-eligibility-audit` pass: `plans/active/issues/sports_track_o_attempted_at_keys_extinct_2026_08_14.md`
      (extracted to `sports_venue_rename_attempted_at_trace_ao_dispatch_2026_08_16.md` — its own 2026-08-17 audit
      entry already noted the extraction, but the raw checkbox at line 68 was still `[ ]` as of 2026-08-21) and
      `plans/active/sports_live_arb_strategy_and_execution_routing_2026_08_14.md` (extracted to
      `mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md` — this doc carries many other genuinely
      open todos beyond the citation issue, so is out of scope for a pure citation-flip pass). Route these 2 to the
      sports tranche rather than fixing them from this doc (cross-cutting tranche is not the owner).

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:092494416dea3b5d]: KEEP-NA, valid -- Self-referential meta doc (about this same audit's own extraction-citation bug). Confirmed it does NOT exhibit its own documented bug: its checker-prototype todo is correctly closed citing cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md item 2. The 1 remaining item (route any further instances the checker finds to their owning tranche) is dependency-blocked on that checker actually running, which hasn't happened yet. Cross-cutting tranche audit.
- **plan_reconciler 2026-08-19** (cross-cutting tranche): **correction — the checker DID run, same day.** This entry's "hasn't happened yet" was stale relative to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 2, which ran the checker for real that same 2026-08-17 and found 3 live instances (see the todo above, now updated with the full list). The remaining item is actionable now, not dependency-blocked.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, stale items — verified the 3 instances the batch14 checker found:
  `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` is now fully resolved (all 3 todos `[x]`),
  narrowing the routing ask from 3 to 2 remaining sports-tranche instances. This doc's own single remaining todo
  stays `assigned_vm: NA` — routing to another tranche's audit pass is coordination work. Doc's own `assigned_vm:
  NA` unchanged. Cross-cutting tranche, batch 2 of 3.
