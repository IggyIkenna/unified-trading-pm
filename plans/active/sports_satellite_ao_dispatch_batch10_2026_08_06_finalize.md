---
doc_type: plan
title: Sports satellite AO batch 10 — finalize (reconcile source docs)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch10_2026_08_06.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Mirrors the batch2-9-finalize pattern: reconcile each of the 4
  distinct source docs' checkboxes once its batch-10 todo(s) land, then archive both docs.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-10, satellite-docs]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch10_2026_08_06]
gate_on_depends: true
source: >-
  /ag-closeout-audit sports tranche run, 2026-08-06, per task_template.md §4's finalize-plan-coverage rule — every
  assigned_vm: planning plan needs a companion gated finalize plan, mirroring the batch2-9 precedent. Authored status:
  active from the start (not draft) per the 2026-07-30 no-double-gate finding recorded in the ag-closeout-audit skill:
  gate_on_depends already machine-holds every todo below regardless of the parent batch's own draft/active status, so a
  second manual flip on this doc would be redundant.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports satellite AO batch 10 — finalize (reconcile source docs)

## Todos

- [ ] [DATA] P3. Reconcile `sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md` — once batch-10 todo 1
      (upstream mojibake trace+fix) lands, flip that doc's P3 todo with the cited evidence, re-verify the P2
      promotion-verification todo's status, and archive the doc if nothing else is open. Source:
      `sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md`. Done when: the doc's checkboxes reflect the shipped
      fix, and the doc is archived (or its remaining open item is a stated operator-hold).
- [ ] [CONFIG] P2. Reconcile `sports_features_layer_findings_sweep_2026_07_18.md` §E — once batch-10 todo 2 (trigger
      tiers + scheduler relaunch) lands, flip the §E [CONFIG] P2 checkbox with the manifest-verification evidence; §E
      [MODEL] P2 + §F [AUDIT] P2 remain parked (operator/conflict-gated). Source:
      `sports_features_layer_findings_sweep_2026_07_18.md`. Done when: the [CONFIG] P2 checkbox is flipped with evidence
      and the residual open items are correctly tagged.
- [x] ✅ [INFRA] P3. **DONE 2026-08-17 (na-eligibility-audit, dispatch agt-1c51ee).** Reconcile
      `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md` — the 2026-08-12 correction's concern is
      satisfied: the source doc already carries a dated `⚠️ CORRECTION 2026-08-08` banner (added the same day
      `sports_taxonomy_p2_migration_2026_08_08_finalize.md` was authored) stating the "0/0 non-canonical, RESOLVED"
      headline was produced by accepted-exceptions, not real canonicalisation, with measured real counts (31
      venues/10 data types vs. the panel's 10/7) and a pointer to the doc that owns genuine canonicalisation
      (`sports_taxonomy_p3_consumers_2026_08_08.md`). The sole remaining `[INFRA] P3` checkbox (LC_TARBALL_FRESHNESS
      proposal) is now flipped citing `sports_satellite_ao_dispatch_batch10_2026_08_06.md` todo 3's DONE status +
      the filed proposal doc. Doc archived to `plans/archive/issues/` this same commit.
- [ ] [DATA] P1. Reconcile `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` — once batch-10 todo 4 (verify-then-fix
      blank fixture_id) lands, flip the doc's blank-fixture_id checkbox per the outcome (fix shipped + evidence, or
      fixed-already + citation); the 2,436-shard reconcile + CLV-retrain items stay open (conflict/time-gated). Source:
      `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`. Done when: the blank-fixture_id checkbox reflects the verified
      outcome and the remaining items are correctly tagged.
- [ ] [PROCESS] P2. Archive `sports_satellite_ao_dispatch_batch10_2026_08_06.md` + this finalize doc once all 4
      reconciliations above are done and the batch's todos are all `[x]`. Done when: both docs sit in
      `plans/archive/2026_08/` with the archive-ritual citation.

## Codex SSOTs

- /plans/active/task_template.md §4 — finalize-plan-coverage rule
- /codex/12-agent-workflow/plan-completion-and-archival-discipline.md — the 6-step archival ritual
- /cursor-configs/skills/ag-closeout-audit/SKILL.md — the no-double-gate finding (finalize ships active)

## Progress Log

- **context-scout 2026-08-07**: populated context_scope (2 entries) — `*_finalize` gate doc, genuinely code-free (every
  todo is a checkbox-reconciliation against 4 named source docs or the archival ritual itself); the gating parent batch
  plus the archival-discipline codex doc are the minimal set.

> **CORRECTED 2026-08-12 (/plan-reconcile)**: the note above (originally claiming the archival-discipline codex path
> "does not resolve") was itself wrong — `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` exists
> and matches the path cited in this doc's frontmatter `source:` field, the "Codex SSOTs" section below, and
> `context_scope` above; all three citations already agree. Evidence:
> `ls /codex/12-agent-workflow/plan-completion-and-archival-discipline.md` → file present (21468 bytes). No path
> correction needed.

- **context-scout 2026-08-17**: re-verified; context_scope unchanged (2 entries, both resolve).
