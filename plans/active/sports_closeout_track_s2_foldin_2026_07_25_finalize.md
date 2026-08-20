---
doc_type: plan
title: Sports closeout Track S2 fold-in — finalize (reconcile parent pointer + re-check gates + archive)
summary: >-
  Gated closeout for sports_closeout_track_s2_foldin_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all of that plan's dispatchable todos are done. Reconciles evidence back into
  sports_consolidated_closeout_2026_07_19.md's Track S2 pointer, re-checks whether any of the plan's own
  BLOCKED-PREREQUISITES/`[OPERATOR]` items have since cleared (CF-8 window, the K1/K2 delete, the batch2 INJURIES
  enrichment), then runs the standard archival ritual on the Track S2 plan. Mirrors
  sports_consolidated_native_ao_extract_2026_07_25_finalize.md's re-check-then-archive pattern.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, track-s2, finalize, archival]
related:
  [
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-08-20"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_closeout_track_s2_foldin_2026_07_25]
gate_on_depends: true
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan,
  mirroring the sports_consolidated_native_ao_extract-finalize precedent (which also re-checks excluded/gated items).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports closeout Track S2 fold-in — finalize

> **Machine-gated on `sports_closeout_track_s2_foldin_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until every dispatchable task in that plan is `done`. Several of that plan's
> own items are `BLOCKED-PREREQUISITES`/`[OPERATOR]`-tagged and therefore never ingested at all — todo 2 below re-checks
> those explicitly, since `gate_on_depends` only ever waits on tasks the backlog actually created.

## Todos

- [ ] [REVIEW] P1. **Flip `sports_consolidated_closeout_2026_07_19.md`'s Track S2 "MOVED 2026-07-25" pointer to a ✅ DONE (or partial-DONE) line**, citing the Track S2 plan's shipped commits for every completed item — verify each
      cited commit exists (`git log`, not the source plan's own claim alone). If any `BLOCKED-PREREQUISITES`/
      `[OPERATOR]` item is still unresolved when this finalize plan runs, the parent's pointer stays partial and must
      name exactly which items remain open. **Done when**: the parent's Track S2 pointer line accurately reflects done
      vs. still-open items, with commits cited for every done one.
- [ ] [REVIEW] P1. **Re-check whether any of the plan's own gated items have cleared**: (1) the E8 delete-gate item —
      has the parent's Track H CF-8 maintenance-window todo landed? (2) the P2c/P2d chain — have P2a and P2b (and then
      P2c) landed? (3) the features-recompute/ML-readiness-reverify pair — has
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s INJURIES enrichment landed? (4) the `DP_RUN_MOSTLY_EMPTY`
      post-DELETE re-check — has the parent's Track V K1/K2 DELETE executed? For any that have cleared, the
      corresponding todo in the Track S2 plan becomes dispatchable (or, if this finalize plan runs after the source plan
      is already fully archived, spin the newly-clearable item into a fresh tracked todo rather than silently dropping
      it). **Done when**: each of the 4 gates above has an explicit current-status note (cleared + follow-up filed, or
      confirmed still blocked).
- [ ] [DOC] P1. **Archive `sports_closeout_track_s2_foldin_2026_07_25.md`** via the standard 6-step ritual: confirm todo
      2 above resolved every gated item (migrate any newly-clearable item to a tracked follow-up) → add the archive
      banner → codex-alignment check (no new codex doc was created by this extraction, so this is a no-op confirmation,
      not a skip) → grep the corpus for every referrer of `sports_closeout_track_s2_foldin_2026_07_25` (including this
      finalize doc's own filename) and fix each path to the archived location → clear `locked_by` (already empty,
      confirm) → archive this finalize doc alongside it in the same commit. **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc is archived in the
      same commit.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — added `sports_satellite_ao_dispatch_batch2` (todo
  2's INJURIES-enrichment re-check target) and the archival-ritual codex SSOT in place of the parent epic; code-free
  finalize gate, no source path applicable.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
