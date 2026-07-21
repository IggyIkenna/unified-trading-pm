---
doc_type: issue
title: PM quality-gates.sh RED — plan-discipline ratchet (121 > baseline 120) + frontmatter-schema violation
summary: >-
  unified-trading-pm's quality-gates.sh fails repo-wide on 2 pre-existing, unrelated checks (plan-discipline ratchet 121
  > baseline 120; a frontmatter-schema gap on sports-2020-06-data-floor.md), blocking the green-tree ship gate for any
  non-docs(plans) PM commit.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, plan-discipline, frontmatter-schema, governance]
related: []
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
resolved_by:
locked_by:
source: [deployment_ui_vm_log_viewer_2026_07_20.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

Running `bash scripts/quality-gates.sh` in `unified-trading-pm` (needed to ship an unrelated 1-line
`configs/cloud-providers.yaml` sync fix) fails on 2 pre-existing, unrelated checks:

1. **Plan discipline regression** — `scripts/quality_gates/check_plan_discipline.py` reports 121 violations vs the
   committed baseline of 120 (`scripts/quality_gates/plan_discipline_baseline.yaml`). Breakdown:
   42×`A-deferred-no-banner` (a plan contains `DEFERRED` but no `## Deferred work — migrated to:` banner), 79×
   `C-archive-no-successor`. This is off-by-one over baseline — some plan committed since the baseline was last written
   tipped it over (fleet-wide plan churn, not attributable to any single commit I can find without a full `git bisect`
   across dozens of concurrent slots).
2. **Frontmatter schema violation** — `codex/02-data/sports-2020-06-data-floor.md`: `referenced_by` optional key is
   absent (schema requires present-but-empty, not fully absent).

Verified pre-existing: my only staged change was `configs/cloud-providers.yaml` (a data-only sync, see
`unified-api-contracts@83506de0` / `unified-trading-library@e22e40f1` for the same fix in the other 2 copies of this
file). Neither failing check references that file.

# Why it matters

`unified-trading-pm`'s `quality-gates.sh` gates EVERY quickmerge ship through this repo (plan authoring, cross-repo
`docs(plans):` flips land via raw push and are unaffected, but any non-plan PM commit — like this config sync — needs
the full gate green to get a quickmerge sentinel). With ~50+ backlog tasks draining concurrently across slots, this repo
is high-churn; a ratchet regression here silently blocks anyone who needs a non-`docs(plans):` PM commit to ship
normally.

# Recommended decision

- Re-run `scripts/quality_gates/check_plan_discipline.py` to enumerate the 121 current violations, diff against
  `plan_discipline_baseline.yaml`, and either (a) add the missing `## Deferred work — migrated to:` banners / archive
  successor refs for the 1 (or more) new offenders, or (b) if the regression is legitimate accumulated debt from many
  small plan edits fleet-wide, re-baseline with `--baseline-write` per the check's own remedy text, with an operator
  sign-off note on why the ratchet moved.
- Add the missing `referenced_by: []` (or equivalent empty-but-present key) to
  `codex/02-data/sports-2020-06-data-floor.md` frontmatter.

## Todos

- [x] [DOCS] P2. ✅ Fix `codex/02-data/sports-2020-06-data-floor.md` frontmatter — add the missing `referenced_by` key
      (present-but-empty is enough to pass `scripts/docs/seed_frontmatter.py --apply`) — unified-trading-pm@3122de370.
      Ran the remedy tool as-instructed; it also seeded the elective `implementation_status` key.
      `check_frontmatter_schema.py` now reports zero violations across all 1739 docs; full `quality-gates.sh` for this
      repo now passes clean end-to-end (both todos in this issue doc closed — plan-discipline ratchet fix landed
      @522dcdf92). (repo: unified-trading-pm)
- [x] [DOCS] P2. ✅ Triage the 121 plan-discipline violations (42 `A-deferred-no-banner` + 79 `C-archive-no-successor`)
      against baseline 120 in `scripts/quality_gates/plan_discipline_baseline.yaml` — unified-trading-pm@522dcdf92. Real
      fix, not a blind re-baseline: enumerated all 121, classified each by whether an honest templated banner applies.
      19/79 archived `C-archive-no-successor` plans had **zero open `- [ ]` items** (100%-closed) — applied the
      established `## Deferred work — migrated to: **None** — successor: not applicable` banner (same template as
      precedent commit `835ef6114`). This is the ONLY subset a scripted fix can honestly close — everything else needs
      real per-plan judgment: 60/79 archived plans still have open items (1–139 each) and 42/42 active
      `A-deferred-no-banner` plans have un-qualified DEFERRED mentions, both requiring a human/plan-owner call on the
      actual successor, not a generic banner. Net: 121 → 102 violations, comfortably clears baseline 120 without gaming
      it (an improvement, not just a ratchet raise) — re-baselined 120 → 102 via `--baseline-write` to codify. Remaining
      102 (42 A + 60 C) is genuine accumulated fleet-wide plan-corpus debt, not attributable to one commit; tracked as a
      fresh P3 follow-up todo below rather than force-fit into this P2 task's scope. (repo: unified-trading-pm)
- [x] [DOCS] P3. ✅ Cleared 35/42 of the `A-deferred-no-banner` active plans — unified-trading-pm@\<pending\>. Read
      every one of the 42 plans' actual DEFERRED context (not just presence/absence) to distinguish genuinely
      undocumented deferrals from regex false-positives on unrelated prose (e.g. "deferred-import" = a lazy-import code
      pattern, "freeze-deferred-build-replay" = a GHA workflow name — neither is an actual backlog-item deferral). All
      35 had every real DEFERRED mention already carrying a recorded disposition (an inline qualifier, a named
      successor/repo/commit, an in-doc "below"/"next item" pointer, a cross-plan reference, or the plan's own
      session-end Deferred table) — just missing the banner the checker looks for — so added the established
      `## Deferred work — migrated to:` banner (precedent `f6df716e7`) to each, naming the specific evidence:
      `prediction_venue_perps_and_live_clob_depth_2026_06_20`, `defi_consolidated_closeout_2026_07_18`,
      `l2_book_microstructure_capture_2026_07_13`, `monitoring_control_plane_master_2026_06_10`,
      `cicd_mvp_ldr_to_main_pipeline_2026_06_30`, `carry_staked_basis_funding_scan_experiment_2026_06_16`,
      `bucket_estate_consolidation_to_sub100_2026_07_13` (points at its own CLAUDE.md-format
      `## Deferred work after <date>` table — the checker's banner-regex doesn't recognise that format, a real
      checker-false-positive class, not fabricated debt), `data_status_tab_and_downloads_remediation_2026_06_16`,
      `qg_host_adaptive_resource_governor_2026_07_14`, `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20`,
      `migration_verification_orphan_safety_2026_06_10`, `features_sports_service_consolidation_deploy_2026_07_15`,
      `data_completion_defi_2026_07_15`, `data_pipeline_alerts_batch_remediation_2026_07_15`,
      `data_feed_sla_registry_and_active_self_healing_2026_06_19`,
      `data_status_page_ux_and_canonicalisation_2026_07_16`, `mvp_backfill_defi_onchain_v10_2026_06_27`,
      `prediction_canonical_identity_migration_2026_07_08`, `ao_worker_lifecycle_dispatch_context_2026_07_21`,
      `ao_fleet_observability_kpis_2026_07_20`, `mtds_file_size_refactor_2026_06_08`,
      `bucket_iam_write_protection_per_tier_2026_06_09`, `cefi_ml_directional_continuous_live_2026_06_20`,
      `master_data_canonicalisation_migration_catalogue_2026_06_07`, `capability_wizard_and_manifest_2026_06_11`,
      `sports_manifest_canonicalisation_2026_06_01`, `tradfi_consolidated_closeout_2026_07_18`,
      `instruments_mtds_subset_consistency_remediation_2026_06_17`, `distinct_values_noncanonical_audit_2026_07_20`,
      `data_completion_tradfi_2026_07_15`, `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`,
      `pipeline_mode_partition_migration_2026_06_01`, `artifact_pipeline_observability_2026_07_17`,
      `features_service_e2e_pipeline_test_2026_05_26`, `data_completion_to_100_all_ag_2026_06_21` (11/13 mentions
      qualified; the other 2 are genuinely open operator-decision items, tracked honestly — not claimed resolved).
      Deliberately left 6 plans un-bannered because their ONLY DEFERRED-matching text is a checker regex
      false-positive on unrelated prose, not a real backlog deferral (`data_pipeline_hardening_self_monitoring_2026_06_22`
      + `infra_capture_and_devops_leftovers_2026_07_06`: "deferred-import" = lazy-import code pattern;
      `github_actions_cost_reduction_options_analysis_2026_07_15` + `github_actions_ci_cost_reduction_2026_07_15`:
      "freeze-deferred-build-replay.yml" = a GHA workflow filename; `utl_uac_reuse_consolidation_remediation_2026_06_10`:
      "deferred to call/construction time" = lazy-init code description; `sports_data_sources_canonical_completion_2026_07_13`:
      "deferred-freshness path" = a code mechanism name) — fabricating a banner on these would be false documentation.
      `master_to_live_defi_2026_05_23` (111 DEFERRED mentions) is left untouched — too large for a responsible read in
      one sitting. Verified via `check_plan_discipline.py` after every batch: 102 → 95 → 80 → 68 → 67 violations (7 A +
      60 C remaining); re-baselined 102 → 67 via `--baseline-write` to codify the improvement (not a ratchet raise).
      `quality-gates.sh` green end-to-end on this commit (once unblocked from the unrelated RB-b1b969f6 repo-blocker).
      (repo: unified-trading-pm)
- [x] [DOCS] P3. ✅ Cleared all 7 remaining `A-deferred-no-banner` plans — unified-trading-pm@\<pending\>. Root-caused
      the 6 checker false-positives: `_DEFERRED_RE`/`_ARCHIVE_OK_TOKENS_RE` were case-INSENSITIVE, so lowercase
      compound code-identifiers (`deferred-import`, `deferred-freshness`, the `freeze-deferred-build-replay` GHA
      workflow filename, "**deferred** to construction time" prose) matched the same pattern as genuine uppercase
      deferral markers (`**DEFERRED**`, `DEFERRED-BLOCKED`, `[DEFERRED]`). Made both regexes case-sensitive on the
      DEFERRED token (kept `post-cutover`/`out of scope` case-insensitive via a scoped `(?i:...)` group) — verified
      against every lowercase "deferred" mention across all 138 active plans first to confirm none were genuine
      unbannered backlog deferrals hiding behind the false-positive class (all belong to plans that already carry a
      banner, or to the 6 confirmed false-positive files). Also added `## Deferred work after <date>` (the
      CLAUDE.md-mandated session-end table format) to `_BANNER_RE` alongside `— migrated to:`, per the prior todo's
      suggested fix. The 7th case, `master_to_live_defi_2026_05_23` (111 mentions, real from-scratch read as
      instructed — not a skim): confirmed every single mention is an already-closed `[x]` checkbox tagged
      `DEFERRED-FUTURE-WORK`/`DEFERRED-BLOCKED`/`DEFERRED-POST-CUTOVER`/`DEFERRED-NEEDS-DEDICATED-SESSION`, each with
      its own inline disposition (named blocker, "folded from" cross-ref, or explicit "post-cutover plan not yet
      created" note) — added the same precedent banner naming that as a 19-epic rollup this plan has no single
      successor, each item's successor is the specific line it's on. Net effect: rule A 7→0; the regex fix also
      dropped rule C 60→46 as a side effect (14 archived plans had the same lowercase-compound false positive).
      Re-baselined 67 → 46 via `--baseline-write` (a verified improvement, not a ratchet raise). `quality-gates.sh`
      for this repo green end-to-end on this commit. (repo: unified-trading-pm)
- [ ] [DOCS] P3. Remaining plan-discipline debt (baseline now 46, down from 120): all 46 remaining violations are
      `C-archive-no-successor` — archived plans with 1–139 open `- [ ]` items each that still need a real successor
      plan identified (or an explicit decision that the open items are abandoned) before a banner/successor reference
      can be added honestly. Do NOT blanket-apply a "no successor needed" template to these — it would be false for
      plans with real open work (unlike the 19 fully-closed archived plans already handled in the prior baseline
      round). Split across multiple P3 tasks by plan-owner/asset_group if picked up; not a single sitting.
      (repo: unified-trading-pm)
