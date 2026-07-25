---
doc_type: plan
title: Sports consolidated closeout — Track D (CODEX doc alignment) history
summary:
  Extracted from sports_consolidated_closeout_2026_07_19.md (which had grown past the 1000-line hard cap) per
  task_template.md's incremental-extraction rule. Track D is fully closed (both items [x]) — the 2026-07-23 codex
  doc-alignment fix pass (6 docs with stale bodies beneath their own banners, fully rewritten not just re-banner'd) and
  the sports_master.md broken-path fix.
status: complete
nature: record
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, codex-alignment, history]
related: [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: "2026-07-19"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
source: "extracted 2026-07-25 during terminal_status_archival_backlog_sweep_2026_07_25.md batch (line-cap remediation)"
resolved_by: "see items inline below"
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports consolidated closeout — Track D history

> Extracted verbatim from `sports_consolidated_closeout_2026_07_19.md`'s Track D section (fully closed, both items
> `[x]`) — see that doc for anything still open.

## Track D — CODEX: doc alignment · P1

- [x] [DOC] P1. ✅ **ACTUALLY FIXED 2026-07-23 (not just re-marked — body rewrites confirmed, not more banners).**
      Original claim ("CORRECTION BANNERS added to all 9 drifted codex docs... full body rewrites are a deliberate
      follow-up") was inaccurate: a 2026-07-23 audit found 3 docs with NO banner at all and 3 more "banner-fixed" docs
      with stale bodies beneath their own banners. All 6 fixed for real this pass, body content verified against the
      current canonical facts (fixtures split, casing revert, the 3-bug venue/instrument_type/chain root cause), not
      just banner text: `sports-adapter-dependency-order.md` (§1/§3/§4.1/§5 rewritten — split entities + T0/T1 gate
      honestly described as non-firing), `sports-scheduling-and-sharding.md` (§9 diagram + schema note rewritten to the
      split layout), `sports-fixtures-lifecycle.md` (available_at table now split by entity),
      `honest-absence-downstream-handling.md` (banner added + `SCHEDULE_DEFINING_DATA_TYPES` verified against live UAC
      source — still `{"FIXTURES"}`, flagged as the forward-looking C1 gap now added above), `sports-batch-live.md`
      (banner added + source table casing/entity fixed), `pipeline-coverage-matrix.md` (confirming banner added +
      league_id/entity annotations). Also picked up the rest of the original Track D scope in the same pass:
      `sports-integration-plan.md` got a SUPERSEDED banner + frontmatter flip, `sports-live-odds-connectivity.md`'s §3
      deleted-scrapers section was rewritten past-tense (14 retired adapters, corrected from the doc's stale "13").
- [x] [DOC] P2. ✅ Fixed via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 18 — `unified-trading-pm@bfb77b46c`
      (verified via `git log`). Found + fixed real staleness (FIXTURES-migration banner claim, the LEAGUE_REGISTRY
      expected-league-count table drift 102→103). `sports_master.md` had 7 broken paths (not 5) — all fixed + verified
      resolving.
