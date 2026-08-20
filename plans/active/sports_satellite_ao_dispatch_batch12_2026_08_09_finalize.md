---
doc_type: plan
title: Sports satellite AO batch 12 — finalize (reconcile source docs)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch12_2026_08_09.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Mirrors the batch2-11-finalize pattern: reconcile each of the 4
  distinct source docs' checkboxes once its batch-12 todo lands, then archive both docs.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-12, satellite-docs, ag-closeout-audit]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/archive/2026_08/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/archive/2026_08/issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md,
    /plans/archive/2026_08/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch12_2026_08_09]
gate_on_depends: true
source: >-
  ag-closeout-audit sports pass (2026-08-09), per task_template.md §4's finalize-plan-coverage rule — every assigned_vm:
  planning plan needs a companion gated finalize plan. Authored status: active from the start (not draft) per the
  2026-07-30 no-double-gate finding: gate_on_depends already machine-holds every todo below regardless of the parent
  batch's own status (including while it still sits draft), so a second manual flip on this doc would be redundant.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports satellite AO batch 12 — finalize (reconcile source docs)

## Todos

- [x] [DATA] P3. Reconcile `canonical_player_stats_fixture_events_quality_2026_07_16.md` — once batch-12 todo 1 (the
      `--apply-prod` reconciliation pass) lands, flip that doc's `## Follow-ups` `[DATA] P3` checkbox with the cited
      commit + post-write verification output; no other open items remain in that doc once this lands — archive it as
      part of this todo (6-step ritual). Source: `canonical_player_stats_fixture_events_quality_2026_07_16.md`. Done
      when: the checkbox is flipped with evidence and the doc sits in `plans/archive/2026_08/`. **✅ DONE 2026-08-10
      (slot-29)**: Follow-ups checkbox flipped with both commit SHAs + both verification outputs
      (`unified-trading-pm@10c16bb8d1`); doc moved to
      `plans/archive/2026_08/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` with the archive
      banner + `status: resolved`. Corpus referrers with full paths fixed (this doc's `related:`, batch12's `related:` +
      `Source:` citation); the AO-host resource-watchdog codex doc
      (`/codex/05-infrastructure/agent-orchestrator-api-host.md`) updated with the new sandboxed-session kill-diagnosis
      lesson learned while executing batch-12 todo 1.
- [x] [DATA] P3. Reconcile `sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md` — once batch-12
      todo 2 (the `odds_targets` re-export + confirm) lands, flip that doc's `## Follow-ups` `[DATA] P3` checkbox with
      the cited GCS parquet path(s); no other open items remain in that doc once this lands — archive it as part of this
      todo. Source: `sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md`. Done when: the checkbox
      is flipped with evidence and the doc sits in `plans/archive/2026_08/`. **✅ DONE 2026-08-10 (slot-29)**:
      Follow-ups checkbox flipped with the GCS parquet path + confirmed non-null `odds_closing_*` values
      (`unified-trading-pm@904dfa2301` flip, this commit's `git mv` archival); doc moved to
      `plans/archive/2026_08/issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md` with the
      archive banner + `status: resolved`. Corpus referrers with full paths fixed (this doc's `related:`, batch12's
      `related:` + todo 2's `Source:` citation, and batch12's Deferred-work table).
- [ ] [DATA] P3. Reconcile `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` — once batch-12 todo 3 (the
      23-sentinel-free-days investigation) lands, flip that doc's `## Follow-ups` `[DATA] P3` checkbox with the cited
      explanation/evidence; no other open items remain in that doc once this lands — archive it as part of this todo.
      Source: `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`. Done when: the checkbox is flipped with
      evidence and the doc sits in `plans/archive/2026_08/`.
- [ ] [DATA] P3. Reconcile `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — once batch-12
      todo 4 (register `sports-drop-stale` + run the real census) lands, update that doc's item [B] E8 with the measured
      twin-coverage percentage and the launcher-category evidence; **do NOT flip the E8 checkbox itself** — the actual
      `--drop-stale`/`--apply` firing is explicitly excluded from batch-12 todo 4 and stays `[OPERATOR]`-gated, so the
      checkbox stays open pending that separate sign-off. Do not archive this doc (it still has genuinely open work: the
      gated delete). Source: `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`. Done when:
      the census result + launcher evidence is written into the doc's E8 item and the checkbox is confirmed correctly
      left open.
- [ ] [PROCESS] P2. Archive `sports_satellite_ao_dispatch_batch12_2026_08_09.md` + this finalize doc once all 4
      reconciliations above are done and batch-12's own 4 todos are all `[x]`. Done when: both docs sit in
      `plans/archive/2026_08/` with the archive-ritual citation.

## Codex SSOTs

- /plans/active/task_template.md §4 — finalize-plan-coverage rule
- /codex/12-agent-workflow/plan-completion-and-archival-discipline.md — the 6-step archival ritual

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries) -- re-verified both entries still
  resolve on disk; no change.
