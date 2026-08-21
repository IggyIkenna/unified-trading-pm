---
doc_type: issue
title:
  docs-reconcile 2026-08-17 — archived-summary generation script bugs (2 root causes, ~1,115 affected docs), an
  archival-path self-consistency gap, and 2 new dead body-links
summary: >-
  From the 2026-08-17 docs-reconcile autonomous sweep (multi-agent Phase 1 semantic hunt). NOT auto-fixable this run:
  (1) two root-cause bugs in the frontmatter-seeding/truncation scripts that produced ~1,115 inadequate summaries,
  concentrated almost entirely in plans/archive/ (dead history, not the live retrieval corpus) -- fixing the scripts is
  small, but a decision on whether to backfill 1,115 archived docs is a scope call, not a mechanical fix; (2) a codex SSOT
  (plan-completion-and-archival-discipline.md) that claims an "unambiguous" two-way archival path split while its own
  worked examples cite 316 real files at an undescribed third path form -- an archival-convention authority question,
  plan_reconciler-adjacent, not something this skill resolves unilaterally; (3) 2 genuinely-dead body-links with no
  successor found anywhere in the repo, not previously tracked in the 2026-08-02 sibling doc.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, doc-integrity, retrieval-layer, summary-quality, broken-links, archival-convention]
related:
  [
    /plans/active/issues/docs_reconcile_remaining_broken_links_2026_08_02.md,
    /plans/active/issues/docs_reconcile_operator_decisions_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-17
last_reviewed: 2026-08-17
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/plan-hygiene/fix_frontmatter.py,
    scripts/docs/seed_frontmatter.py,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/ao_satellite_ao_dispatch_batch23_2026_08_17.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: [docs-reconcile autonomous sweep, dispatch agt-192c24, 2026-08-17]
assigned_role: infra
drift_direction: advance-docs
---

# docs-reconcile 2026-08-17 — summary-generation script bugs, an archival-path gap, and 2 new dead links

Multi-agent Phase-1 semantic sweep (5 parallel hunters: authoritative_for collisions, summary-quality, doctrine-
consistency, broken-link baseline triage, internal self-consistency + structural integrity) against the live PM
checkout. Everything auto-fixable per the skill's Phase-3 table shipped directly in this sweep's commits (a
`last_reviewed:` frontmatter fix, a duplicated/self-contradicting block in `manifest-consolidator-ssot.md`, a moved
broken link in `ui-testing-layers.md`, a rotting hardcoded count in `data-pipeline-alerts.md`, and a placeholder summary
on one active issue doc). This doc captures what's NOT auto-fixable this run.

## Zero confirmed findings (reported for completeness, not action items)

- `authoritative_for` collisions: **0 confirmed** across 758 `status: current` docs / 693 topic claims (906 codex docs
  scanned). 2 soft cross-doc CONTENT-DRIFT observations surfaced along the way (not retrieval collisions): (a)
  `/codex/01-domain/market-making-strategy.md` vs `codex/09-strategy/architecture-v2/archetypes/market-making-
  inventory-skew.md` use different inventory-skew formulas while both are `status: current`; (b)
  `/codex/04-architecture/incident-gateway-state-machine.md` and `codex/15-runbooks/alerting/audit-acknowledgement-
  flow.md` both reproduce the identical SLA-timing table verbatim (a future edit to one won't propagate to the other).
  Neither is this skill's finding type (not a retrieval ambiguity) -- noting so a future content-accuracy sweep doesn't
  have to rediscover them.
- Stale retrieval-doctrine references in `.cursor/rules/*.mdc` + `agents/*.md`: **0 confirmed** across all 30 files
  swept (5 rules + 25 role-charters).

## Todos

- [x] ✅ [SCRIPT] P2. **Fix `fix_frontmatter.py`'s summary-truncation logic** — extracted (conflict-checked, clear) to
      `ao_satellite_ao_dispatch_batch23_2026_08_17.md` item 2. Track dispatch/completion there, not here.
- [ ] [OPERATOR] P3. **Decide whether to backfill the ~1,115 inadequate archived-doc summaries this produced.**
      1,114 of 1,115 confirmed-inadequate summaries (from a corpus-wide sweep of 5,235 in-scope docs) are in
      `plans/archive/` -- dead history outside the live L0-L4 retrieval flow, not the codex/agents/active-plans
      corpus (which came back clean). Root cause for the ~1,072 that are simply EMPTY (not truncated):
      `scripts/docs/seed_frontmatter.py` line ~126 seeds `summary:` present-but-empty "deferred to the later content
      pass" for legacy docs, and that pass never happened before ~796 of them were archived (the other ~276 have a
      legacy `overview:` field carrying the real content, never migrated into `summary:`). This is a genuine scope
      question (is archived-doc summary quality worth a dedicated backfill pass, or is it acceptable dead-history
      debt) rather than something this skill should decide unilaterally by either doing it or ignoring it silently.
      Options: (A) accept as permanent archive debt, do nothing further [no cost, but the gap never closes]; (B)
      one bounded follow-up pass that migrates the 276 `overview:`-bearing docs' content into `summary:` (cheap,
      mechanical, closes 25% of the gap) and leaves the other 796 as accepted debt; (C) a full backfill pass across
      all 1,115 (real cost, full closure). [WORKER REC: B -- cheap, non-zero progress, leaves the genuinely-expensive
      796-doc content-authoring gap as an explicit, visible accepted-debt line rather than either silently doing 3
      days of archive-doc archaeology or silently doing nothing].
- [ ] [OPERATOR] P2. **Resolve `plan-completion-and-archival-discipline.md`'s archival-path self-consistency gap.**
      Step 6 (current line ~68-70) claims: "this doc previously contradicted itself... the authoritative, internally
      consistent SSOT for issue-doc archival path, stated unambiguously" -- asserting a clean two-way split (issue
      docs -> flat `plans/archive/issues/`; everything else -> dated `plans/archive/<YYYY_MM>/`). But the SAME doc's
      own worked examples (current lines ~172, ~259) cite real files that exist ONLY at a third, undescribed hybrid
      form: `plans/archive/<YYYY_MM>/issues/`. Verified on disk (2026-08-17): 316 issue docs currently live at this
      exact third form fleet-wide (vs 1,513 at the flat form, 0 at a bare-dated non-issues form). Options: (A) the
      third form is actually fine/intentional (a dated-cohort issues subfolder) -- update the doc to describe THREE
      valid forms instead of claiming two, and stop citing worked examples that contradict its own stated rule; (B)
      the third form is drift that should be migrated to the flat form -- file a bounded migration (316 `git mv`s +
      referrer sweep) and keep the doc's two-way claim as the enforced target. [Not resolving this myself -- picking
      between "316 files are fine as-is" and "316 files need migrating" is an archival-convention authority call
      squarely adjacent to plan_reconciler's corpus, not a docs-retrieval-layer correctness call this skill can settle
      by reading the doc harder.] Cross-ref: `issue-doc-lifecycle.md`'s parallel state-machine table has the same
      softer gap (states the flat rule as unambiguous while its own cited corpus measurement shows ~17% of issue docs
      aren't there) -- supporting evidence, not an independent second finding.
- [ ] [DOCS] P3. **2 new genuinely-dead body-links, not covered by the sibling 2026-08-02 tracking doc** (verified via
      `find` across the whole repo, not just grep-0 -- resolution algorithm per `check_doc_body_links.py::_resolve()`):
  - `/codex/14-customer-journeys/shared-core/strategy-version-governance.md` cites
    a `post-mortem-template.md` file under a `codex/12-incidents` directory -- that directory doesn't exist at all (only
    `12-agent-workflow`). The citing doc already self-flags this in its own prose ("no leading slash -- template not
    yet created") and points to `/codex/15-runbooks/incidents/README.md` as the current index; that dir exists (24
    runbook files) but has no post-mortem template and its README doesn't mention one. Genuinely still missing, exactly
    as the citing doc already admits -- either write the template or drop the forward-reference.
  - `plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md` (×2 occurrences, lines ~135
    prose + ~599 table) cites a `manifest-writer-ssot.md` file under `codex/02-data` as a proposed-but-never-created
    new file (2026
    -05-20 audit item R14). The intended content instead landed inline in the EXISTING
    `/codex/02-data/availability-manifest-and-data-status.md` (confirmed: its "SSOT Locations" table, current lines
    ~305-320, documents `manifest_writer.py`'s `AvailabilityRecord`/`ManifestWriter`/`read_availability_index()` in
    detail). Not fixed this run -- the citing doc is 2026-05-20 archived audit history (dead, not live-retrieved), same
    proportionality call as the archived-summary backlog above; repoint target is confirmed and ready whenever someone
    picks this up.

## Note — not a finding, FYI only

While shipping this sweep's fixes, `quickmerge.sh` quarantined an UNRELATED uncommitted edit
(`plans/active/issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md`, not touched by this
sweep's `--files` scope) into a `safety-snapshot: pre-reconcile quarantine` autostash during its rebase-reconcile
(origin had moved 5 commits during this session). This is the expected, already-hardened recovery behavior documented
in the now-resolved `/plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`
(quarantine + inform, not silent loss) -- content is recoverable via `git stash list` / `git show 'stash@{N}:<path>'`,
not destroyed. Not this sweep's content to reapply (unrelated doc, no context on the intended diff); flagging only so
whoever owns that MDPS finding sees the breadcrumb if they come looking for their edit. Separately: quickmerge's own
"Landed on live-defi-rollout" message cites the recovery SSOT above at its OLD path
(`plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`) -- that doc archived
2026-08-14 and now lives at `/plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_
2026_08_10.md`. A hardcoded path string in `scripts/quickmerge.sh`'s own output, not a doc-corpus finding -- too small
to chase down the exact call site in this sweep, noting so it doesn't re-mislead the next agent who greps for it.

## Progress Log

- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:dcddeb426a48300f]: RECLASSIFY (per-todo split) — the `fix_frontmatter.py` summary-truncation fix is conflict-checked clear and extracted to `ao_satellite_ao_dispatch_batch23_2026_08_17.md` item 2; the 2 [OPERATOR] scope-decision items and the half-bounded dead-link item stay KEEP-NA.
- **context-scout 2026-08-17**: populated context_scope (4 entries) — corrected a pre-existing entry
  (`manifest-consolidator-ssot.md`) that had no connection anywhere in this doc's own body, swapped for the active
  satellite batch now owning the one already-shipped fix's landing citation.
- **na-eligibility-audit 2026-08-18 (ao tranche)**: KEEP-NA, valid — re-affirms 2026-08-17 verdict. All 3 remaining open items are genuine operator-gated/judgment calls (2 explicit [OPERATOR] scope decisions, 1 half-bounded dead-link item bundling a judgment sub-link); the doc's one genuinely bounded item was already extracted to `ao_satellite_ao_dispatch_batch23_2026_08_17.md` and correctly stays closed here.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
