---
doc_type: plan
title: Finalize — MTDS venue-key casing canonicalization
summary: Gated finalize companion for mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cross-cutting, finalize]
related:
  [
    /plans/archive/2026_08/mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md,
    /plans/archive/issues/mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-18"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 10, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/archive/2026_08/mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md,
    /plans/archive/issues/mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
locked_since:
resolved_by:
---

> **✅ ARCHIVED 2026-08-18 (complete)** — review independently verified the canonicalization (see Progress Log
> below) and confirmed the source plan's todo was correctly flipped by slot-8 on 2026-08-17. Fallback removal
> remains open, correctly tracked (not lost) at
> `/plans/active/issues/mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md` (P3,
> `[OPERATOR]`-gated) — that doc, not this one, is where to look for the one remaining step.

# Finalize — MTDS venue-key casing canonicalization

- [x] ✅ [REVIEW] P2. Confirm the canonicalization landed with evidence (QG green, fallback removed, no live
      venue-key lookup miss); flip the source todo to done; archive this plan once done and unlocked. —
      **Independently verified 2026-08-18 (review)**: source todo already flipped `[x]` by slot-8
      2026-08-17 (source plan archived alongside this one). Canonicalization VERIFIED live (not
      trusted from self-report) via direct `git show --stat` + `git merge-base --is-ancestor` on both cited
      SHAs plus a corpus-wide `grep -rn register_ws_feed_connector` across `live/connectors/`: curve/orca/
      raydium/morpho/jito/phoenix all dual-registered (canonical UPPERCASE + legacy lowercase); kalshi
      correctly single-registered under canonical `KALSHI` via `kalshi_clob_ws.py` only (its sibling
      `kalshi_ws.py` carries an explicit docstring note not to dual-register there); polymarket's two-connector
      dual-casing confirmed intentional via `polymarket_clob_ws.py`'s own docstring. QG VERIFIED: 8/8 most
      recent `quality-gates-v2` runs green on `live-defi-rollout`; both shipped commits carry `Quickmerge:
      agent` trailers. No live venue-key lookup miss: every venue resolves via canonical key or the
      still-present fallback (double-covered). **"fallback removed" in this todo's original wording is NOT
      literally true** — the fallback is deliberately still in place, correctly deferred pending one
      `[OPERATOR]` decision on polymarket's dual-casing (tracked, not lost — see banner above); closing this
      finalize task on the substantive completion rather than blocking on that one operator-gated,
      already-tracked decision. **Found + fixed in passing**: the source plan's checkbox misattributed the
      curve/orca/raydium/morpho/jito dual-registration to `767c4208a8` (actually an unrelated kalshi-docstring
      commit) — corrected there to the real source, pre-existing `44db26bc` (2026-08-14).

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **2026-08-18 (review, slot-7)**: independently re-verified every claim in the source plan's checkbox against
  live code rather than trusting the self-report (per review's evidence-backed-completion HARD RULE) —
  see the checkbox annotation above for the full verification trail. Found and fixed one evidence-citation
  error in the source plan (`767c4208a8` mis-cited as the source of the 5-venue dual-registration; corrected
  to `44db26bc`). Flipped this task's checkbox and archived both this finalize plan and its now-fully-verified
  source plan together — nothing left open in either; the one remaining step (fallback removal) was already
  correctly split into its own `[OPERATOR]`-gated issue doc by the prior session, confirmed still present and
  well-formed (`assigned_vm: NA`, validated KEEP-NA by na-eligibility-audit 2026-08-17).
