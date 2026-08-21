---
doc_type: issue
title:
  docs-reconcile 2026-08-02 — 17 genuinely-dead/ambiguous links + README.md broader staleness + freshness-ratchet design
  note
summary: >-
  Residue from the 2026-08-02 docs-reconcile sweep that is NOT auto-fixable (no confident successor target, despite real
  investigation) and NOT an authority question (so not parked as BLOCKED-OPERATOR-DECISION either) -- P1/P2 findings for
  someone to either write the missing prose/doc or delete the dead reference, per the skill's own routing rule. Also
  captures two lower-priority design observations found along the way: root README.md has broader staleness beyond the
  one claim already fixed, and the codex freshness ratchet is count-only (can mask simultaneous improvement+regression).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, broken-links, retrieval-layer, readme, freshness-ratchet]
related: [doc_body_link_checker_blind_to_backtick_citations_2026_08_02, docs_reconcile_operator_decisions_2026_08_02]
created: 2026-08-02
author: unknown
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
context_scope: [/plans/archive/2026_08/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md, /plans/active/issues/docs_reconcile_operator_decisions_2026_08_02.md, scripts/quality_gates/check_doc_body_links.py, scripts/plan-hygiene/check_reference_paths.py, scripts/quality_gates/check_codex_doc_freshness.py]
supersedes:
superseded_by:
depends_on:
source: [docs-reconcile autonomous sweep, dispatch agt-0b4ee1, 2026-08-02]
assigned_role: infra
drift_direction: advance-docs
---

# docs-reconcile 2026-08-02 — remaining broken-link + staleness residue

Every item below was investigated (not just flagged) — each has a note on why no confident fix was applied. Everything
that COULD be confidently fixed already shipped in the sweep's 4 commits (unified-trading-pm@7de163bf1, @50f2e668b,
@c9dc2cfb5, @809a28c97).

## Genuinely dead links — no successor found anywhere in the repo (verified via `find`, not just grep-0)

- [x] ✅ [DOCS] P2. `.cursor/rules/core/provider-api-version-manifest.mdc` cited the ARCHIVED `unified-trading-codex`
      repo's `02-data/provider-api-version-manifest.md`. **Fixed 2026-08-05 (docs-reconcile, dispatch agt-d8ef73)**:
      dropped the dead `CODEX:` pointer line — the rule's own body (frontmatter description + `## Rule summary`) is
      already self-sufficient, and the live content-of-record is a YAML config, not a doc, so no new stub was invented.
      `unified-trading-pm@72b0f5724`.
- [x] ✅ [DOCS] P3. `/codex/00-getting-started/E2E_WORKFLOW_UNIFIED.md` cited a transient `.cursor/plans/` artifact,
      `phase_0_cod_service_specs_f0a0afbd.plan.md`. **Fixed 2026-08-05**: dropped the dead link, annotated
      `_(transient Cursor-generated artifact, never durable — dead historical link)_` matching this same doc's own
      established convention for the 2 sibling dead links 6 lines above (`PROJECT_STRUCTURE_REFERENCE.md`,
      `COMPREHENSIVE_SUMMARY.md`). `unified-trading-pm@72b0f5724`.
- [ ] [DOCS] P2. `/codex/04-architecture/README.md` (×4: `BATCH-LIVE-SYMMETRY.md`, `communication-patterns.md`,
      `compute.md`, `scaling.md`) + `/codex/04-architecture/batch-live-architecture.md` (`communication-patterns.md`) —
      the README's own ToC clearly intended these as sibling docs fanned out from it, but none were ever created; the
      content lives entirely inline in README.md instead (control-verified: `concurrency.md`, linked from the same
      table, DOES exist — so this is a real gap, not a resolution-logic bug). Fix: either extract the relevant README
      sections into the 4 real files, or strip the dead ToC/inline links and note the content is inline. **Re-verified
      2026-08-05 (docs-reconcile): still no confident successor, left open.** **Re-verified 2026-08-17 (docs-reconcile,
      hunter-5 broken-link triage): still no confident successor via `find` across the whole repo, left open.**
- [ ] [DOCS] P3. `/codex/06-coding-standards/README.md` (×3: `./PREK_MIGRATION_WALKTHROUGH.md`,
      `configuration-management.md`, `formatting-standards.md`) — same table already has a precedent fix (line 61: a
      broken `STANDARDS.md` link was redirected to `adapter-dead-code-and-fallback-ban.md` on 2026-07-24), but no
      confident redirect target was found for these 3 (checked `config-types.md` as a candidate for #2 — it's itself a
      redirect stub pointing back at this same README, so using it would create a cycle). Needs a human who knows what
      these 3 were meant to cover. **Re-verified 2026-08-05 (docs-reconcile): still no confident successor, left open.**
      **Re-verified 2026-08-17 (docs-reconcile, hunter-5 broken-link triage): still no confident successor, left
      open.**
- [x] ✅ [DOCS] P3. `/codex/06-coding-standards/ui-testing-layers.md` cited `../../../.claude/rules/workspace-workflow.md`
      — no `rules/` subdir under `cursor-configs/`, no file named `workspace-workflow.md` anywhere in the repo.
      **Fixed 2026-08-17 (docs-reconcile)**: repointed to `/codex/08-workflows/ci-cd-flow.md`'s current branch-model
      section (`#branch-model--ldr-trunk--main-direct-staging-dormant-reversible`), with the citing prose updated to
      describe the current staging-dormant model rather than the old "three-tier... staging convergence" framing.
      `unified-trading-pm@ea375c7182`.
- [x] ✅ [DOCS] P3. `/codex/07-security/mev-protection.md` cited the retired `plans/questions/` dir's
      `defi_readiness_catalogue_2026_05_08.md`. **Fixed 2026-08-05**: repointed to the retirement record
      (`plans/archive/questions_README_retired_2026_05_20.md`), which names the 2 real successors
      (`defi_catalogue_chain_primitives_2026_05_10.md`, `defi_simulation_realism_2026_05_10.md`) — used the retirement
      record itself as the link target rather than either successor alone, since the original doc's content split across
      both. `unified-trading-pm@72b0f5724`.
- [ ] [DOCS] P3. `/codex/09-strategy/architecture-v2/README.md` cites `templates/archetype-doc.md` — no `templates/` dir
      exists under `architecture-v2/`; the real `archetypes/` dir holds ~19 fully-written archetype docs with no shared
      template file ever created. **Re-verified 2026-08-05 (docs-reconcile): still no confident successor, left open.**
- [ ] [DOCS] P3. `/codex/15-runbooks/custody-onboarding-checklist.md` cites a `plans/active/` slug,
      `fireblocks_copper_client_integration_2026_06_01.md` — no plan under this or any similar slug exists anywhere.
      Plausibly this custody/wallet-adjacent plan was simply never authored.
- [ ] [DOCS] P3. `codex/README.md` cites `.github/PRE_COMMIT_SETUP.md` — `.github/` contains only `actionlint.yaml`,
      `actions/`, `workflows/`; no pre-commit doc under any name/case. **Re-verified 2026-08-05 (docs-reconcile): still
      genuinely dead, no successor found anywhere (incl.
      `plans/archive/pre_commit_to_gha_version_bump_2026_03_11.plan.md` — thematically close but a migration PLAN, not
      the setup doc itself, so not used as a substitute target). Left open — this specific one needs prose written or
      the link dropped, no evidence-backed target exists to repoint to.** **Re-verified 2026-08-17 (docs-reconcile,
      hunter-5 broken-link triage): still genuinely dead, no successor found, left open.**
- [x] ✅ [DOCS] P2. `cursor-rules/architecture/feature-producer-consumer-contract.mdc` cites codex `04-architecture`'s
      `feature-dictionary.md` — file does not exist anywhere in the repo, not a rename. **MOOT — the citing rule is no
      longer live.** `unified-trading-pm@b45eab084`/`@d4f7fab9d` (2026-08-02) archived the entire top-level
      `cursor-rules/` tree to `plans/archive/cursor-rules_2026_08_02/`; `.cursor/rules/` (a wholly separate, canonical,
      150-file tree with zero overlap — see `docs_reconcile_operator_decisions_2026_08_02.md`) is the sole
      live/symlinked source. Verified 2026-08-03 (na-eligibility-audit): `cursor-rules/` absent at the top level, the
      archived copy present at the cited archive path.
- [x] ✅ [DOCS] P2. `cursor-rules/testing/tradfi-path-builder-byte-identity.mdc` cites codex `04-architecture`'s
      `path-canonicalization.md` — file does not exist anywhere in the repo, not a rename. **MOOT** — same archival
      event as the item above; this file also independently verified moved to
      `plans/archive/cursor-rules_2026_08_02/testing/tradfi-path-builder-byte-identity.mdc`.

## New from 2026-08-03 sweep — genuinely dead links, no successor (verified via direct invocation of the live checkers, not re-implemented logic)

- [x] ✅ [DOCS] P2. `plans/audit/results/archive/AUDIT_2026_05_15_harsh_side_completion.md` cited 6 dead targets, all
      the same shape: `../../harsh_orchestrator/pings/slot_{2,5,6,7,8,9}.md`. Git archaeology confirmed all 6 were
      **deliberately, permanently deleted** by commit `890ef4b86` (2026-06-24, "operator-deleted... no longer needed") —
      not a rename, no successor exists. **Fixed 2026-08-05 (docs-reconcile)**: converted all 6 to plain-text
      `pings/slot_N.md` citations with a deletion note, dropping the dead hyperlink syntax while preserving the
      historical "where the evidence used to live" mention. `unified-trading-pm@72b0f5724`.
- [x] ✅ [DOCS] P3. `plans/epics/agent_operating_framework_master.md` (`related:` frontmatter) cited
      `../active/orchestrator_v07_multi_vm_topology_2026_05_21.md` — no file under this or any similar slug exists
      anywhere in the repo; multi-VM dispatch itself was deprecated 2026-06-27 in favor of the single-VM architecture,
      so there was no "current" successor to point to, only a retired concept. **Already resolved by the time of the
      2026-08-05 pass** (the Progress Log below recorded this as "found ALREADY ABSENT... no action needed" that day,
      but the checkbox itself was never flipped — closed now, 2026-08-08, with a fresh live re-verification:
      `grep -A15 '^related:' plans/epics/agent_operating_framework_master.md` no longer contains the dead slug, and
      `scripts/plan-hygiene/doc_reference_baseline.yaml`'s `known_broken` list is empty, consistent with there being no
      outstanding frontmatter-reference debt).

## Genuinely ambiguous — broken, but no confident single target (P2, report-only per the skill's own severity guidance — not an authority question)

- [ ] [DOCS] P2. `codex/validators/QUICK_REFERENCE.md` (status: current) redirects to
      `/codex/10-audit/VALIDATOR_COVERAGE_MATRIX.md` as one of its two "actual SSOTs" — that target resolves fine as a
      FILE (not a broken link), but its own content admits `status: stale` and its own summary says "Service/UI lists
      use retired repo names and are stale" (title still dated "2026-02-21", no `superseded_by:` pointer). So a current
      doc's redirect target is itself stale with no named successor — this is a content-staleness gap one layer behind a
      link check, not a broken link per se. Needs a human who can either refresh the matrix (retired repo names →
      current fleet) or determine there's no live consumer left and archive it with QUICK_REFERENCE.md repointed
      elsewhere.
- [x] ✅ [DOCS] P3. `/codex/02-data/contracts-scope-and-layout.md` cited the `plans/active/` slug
      `uac_citadel_architecture_2026_05_07.md` — `plans/archive/INDEX.md` (line 177) tracks this exact slug's
      disposition as "Superseded by completed execution plan," but neither that slug nor
      `uac_citadel_implementation_execution` (the row directly above) corresponds to any actual file on disk anywhere in
      `plans/` — pure status-table labels, not filenames. **Fixed 2026-08-05 (docs-reconcile)**: rewrote the citing
      prose to state the plan is gone + cite `plans/archive/INDEX.md`'s citadel section by fact rather than link, and
      flagged (not resolved — genuinely out of this skill's scope) an adjacent open question this investigation
      surfaced: whether the circular-import test file this paragraph gates (`test_ac_uic_alignment.py`) has actually
      completed its prescribed move to `unified_api_contracts/internal/tests/` in the sibling `unified-api-contracts`
      repo (found copies at BOTH `tests/internal/test_ac_uic_alignment.py` and
      `tests/internal/unit/test_ac_uic_alignment.py` — didn't read either's actual imports to determine if the exception
      this paragraph describes is now moot, since that's a cross-repo code-correctness question beyond retrieval-layer
      doc health). `unified-trading-pm@72b0f5724`.
- [ ] [DOCS] P3. `/codex/05-infrastructure/workspace-root-variable.md` cites `ci-cd.md` — two plausible readings: (a)
      the same never-created-sibling-doc pattern as the `04-architecture/README.md` cluster above (the citing doc's own
      body table lists `ci-cd.md` alongside two real siblings, `new-repo-setup.md` + `workspace-setup.md`, under "CI/CD
      setup (uses repo-relative paths)" — no such doc exists); or (b) it should redirect to
      `/codex/08-workflows/ci-cd-flow.md` (this workspace's real CI/CD SSOT) — but that doc's scope
      (gates/quickmerge/branch-protection/release) doesn't cleanly match the citing doc's stated scope ("setup,"
      "repo-relative paths"), so this may be a genuine scope mismatch rather than a simple rename.

## README.md — broader staleness beyond the one claim already fixed (P2, not fixed this sweep — scope beyond a mechanical link repoint)

- [x] [DOCS] P2. Root `README.md` (the PM repo's own top-level onboarding doc) has multiple stale claims beyond the
      `cursor-rules/` sync claim already corrected (unified-trading-pm@c9dc2cfb5):
  - Cites `scripts/workspace/sync-rules-pull.sh` in its "Key Scripts" table — this file **does not exist** (confirmed
    via `find`).
  - Describes `unified-trading-codex` as a live sibling repo ("standards and specifications") in its "Required Workspace
    Structure" diagram — that repo is ARCHIVED (SSOT = this repo's own `codex/`, per CLAUDE.md).
  - The "Required Workspace Structure" diagram shows `~/repos/unified-trading-system-repos/` as the workspace root —
    doesn't match the current `/home/ubuntu/unified-trading-system-repos/` + `.tabs/<slot>/` per-slot worktree layout
    (Path-B, live since 2026-06-08).
  - **RE-VERIFIED STALE FINDING, 2026-08-20 (T5)**: all 3 already fixed by another session since this finding was
    filed (2026-08-02) — `sync-rules-pull.sh` is gone from the current Key Scripts table (5 different real
    scripts now listed), `unified-trading-codex` is now correctly labeled `ARCHIVED` in the diagram, and the
    diagram now shows BOTH the generic clone root AND `.tabs/<N>/` per-operator-slot worktrees explicitly. Nothing
    to fix — this finding rotted in the other direction (fixed-but-not-closed, not fixed-but-still-broken).
  - This needs a real onboarding-doc pass (verify every script/path/repo reference against current reality), not a
    narrow link repoint — deliberately out of scope for this sweep to avoid an under-verified rewrite of a
    highly-visible root file under time pressure.

## Design observation — codex freshness ratchet is count-only (P2, informational — not this skill's gate to change)

- [ ] [SCRIPT] P3. `check_codex_doc_freshness.py`'s ratchet (`scripts/quality_gates/check_codex_doc_freshness.py`)
      compares `len(violations) > baseline` — a pure COUNT comparison, not a set comparison. Verified during this sweep:
      on 2026-08-02, 4 docs newly lost their `last_reviewed` field/went stale (`cross-reference-path- convention.md`,
      `local-tmux-precompact-watcher.md`, `lst-exchange-rate-surfaces.md`,
      `plan-priority-tier-and-dispatch-ordering.md`) while 4 DIFFERENT docs got genuinely fixed
      (`claude-code-settings-symlink.md`, `gcs-object-operations.md`, `issue-doc-lifecycle.md`,
      `manifest-consolidator-ssot.md`) — net count unchanged (24=24), so the gate reported "✅ At baseline" the whole
      time, silently masking the churn. Not proposing a fix here (freshness-gate design is explicitly outside this
      skill's charter to change unilaterally per its own "never weakened by either mode" rule) — just recording the
      observation so it's visible if/when the freshness-gate design is revisited.

## New from 2026-08-08 sweep — 1 dead link with no confident target, 1 script root-cause finding

- [ ] [DOCS] P3. `.cursor/rules/core/plans-prompts-index.mdc` (`alwaysApply: false`, self-branded "SSOT for where agent
      prompts and task entry points live") — its "Task Entry Points" table cites `START_HERE.md` under
      `unified-trading-pm/plans/tasks/cursor/` and `START.md` under `unified-trading-pm/plans/tasks/claude-code/`; the
      `plans/tasks/` directory does not exist anywhere in the repo (confirmed via `find`). Every OTHER table in this
      same file (Phase Prompts ×3, Sports ×1, the `CODEX:` pointer) resolves correctly — this is an isolated staleness,
      not a wholesale-obsolete rule. Not auto-fixed: unlike the `04-architecture/README.md` ToC cluster above, there's
      no equivalent doc elsewhere in the corpus using this "Cursor vs Claude Code START_HERE/START" convention to
      confirm whether the right fix is (a) write the two missing onboarding docs, (b) repoint to
      `plans/active/task_template.md` (the CLAUDE.md-current plan-authoring entry point, but not a strict semantic match
      — that's for authoring a NEW plan, not general "task entry"), or (c) strip the table because the
      per-tool-onboarding-doc concept itself was retired without anyone updating this index. Needs a human who knows
      whether these were ever built.
- [x] ✅ [SCRIPT] P2. **Root cause of most of this doc's own truncated-summary findings, identified 2026-08-08**:
      `scripts/plan-hygiene/fix_frontmatter.py`'s `get_first_paragraph_after_heading()` (used to auto-backfill a missing
      `summary:` field) hard-truncates at char 197 + `"..."` with NO sentence/word-boundary awareness (the function
      body: `if len(result) > 200: result = result[:197] + "..."`). Harmless when a doc's first paragraph is under 200
      chars (the common case), but produces a genuinely unusable, mid-word-cut summary whenever it isn't — this is the
      mechanism behind the 12-of-14 exactly-200-char truncations in `docs_reconcile_operator_decisions_2026_08_02.md`
      BLOCKED-OPERATOR-DECISION 3. Not fixed this run (a shared frontmatter-tooling script is more consequential than a
      doc-content edit, and this skill's Phase 3 auto-fix table covers DOC content classes, not doc-TOOLING bugs) —
      filing so it's tracked rather than left to keep silently recurring every time the backfill script runs against a
      doc with a long first paragraph. Recommended fix (not implemented): truncate at the last sentence or word boundary
      before 200 chars, and/or flag any doc where the auto-derived summary got truncated at all for required human
      review before it ships, rather than silently landing a partial sentence. **➡️ EXTRACTED 2026-08-09 to
      `ao_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1 — SHIPPED 2026-08-10: unified-trading-pm@2022f4142f
      (slot-24). Fix replaces hard `result[:197] + "..."` with sentence/word-boundary-aware truncation (sentence
      boundary `.`/`!`/`?` + space → word boundary (last space) → hard-cut fallback). 6/6 regression tests pass
      (`tests/unit/test_fix_frontmatter_summary_truncation.py` — sentence-boundary, word-boundary, short/no-op,
      exactly-200, unbroken-token hard-cut, no-paragraph-returns-None). VERIFIED 2026-08-10 (slot 27, review).**

## New from 2026-08-09 sweep — 3 genuinely-new dead links, 1 self-consistency content-investigation finding

- [ ] [DOCS] P3. `/codex/14-customer-journeys/shared-core/strategy-version-governance.md` cites a template under
      `codex/12-incidents/` named `post-mortem-template.md` — that directory does not exist anywhere in the repo. The
      citing doc already self-flags this as a known gap ("no leading slash — template not yet created; see
      `/codex/15-runbooks/incidents/README.md` instead") — not stale rot, a documented forward-reference to a template
      never written. Needs a human to either write the template under `codex/12-incidents/` (or the existing
      `15-runbooks/incidents/` tree the doc already points readers to as the interim) or drop the forward-reference.
- [ ] [DOCS] P2. `plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` (line 441)
      proposes a new file, `sports-canonical-league-cup-registry.md`, under `codex/02-data/` — never created. This is an
      active plan's own stated deliverable, not stale rot; if the plan doesn't already track it as a `- [ ]` todo, one
      should be added there (not fixed here — out of this skill's `does_not: touch the plans corpus` charter).
- [ ] [DOCS] P3. `plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md`'s R14 finding
      proposes a new file, `manifest-writer-ssot.md`, under `codex/02-data/` — never created under this name.
      `/codex/02-data/availability-manifest-and-data-status.md` is a plausible conceptual successor but the scope isn't
      a confirmed 1:1 match (this is an archived audit result, not a live plan) — needs a human to confirm scope before
      repointing.
- [ ] [DOCS] P1. `/codex/09-strategy/mvp-universe-per-asset-group.md` states TWO different "Total" backtest worker-run
      counts for what both passages frame as the same complete Tier-A (May-23 cutover) config-grid: line 215 ("**Total
      backtest scope**: ~580K-1.3M worker-runs", derived from the per-asset-group table, used at line 219 to compute
      "~28K seconds ≈ 8 hours per full Tier A") vs. line 329 ("**Total**: ~2.6M backtest worker-runs across Tier A by
      May-23", derived from the per-archetype table, used at line 332 to compute "≈ 1.3 days wall-clock for full Tier A
      backtest"). The two totals diverge ~2-4.5x and the doc never reconciles the gap or flags that the two tables
      likely use different accounting (e.g. CeFi coins plausibly counted once under the per-asset-group "CeFi" row AND
      again inside the per-archetype "arbitrage-funding-rate" row). Not auto-fixed: picking a number, or writing a
      reconciliation note asserting WHY the two differ, requires re-deriving both tables' underlying counts — a
      content-accuracy investigation beyond a mechanical doc-health fix. Needs someone with the archetype/asset-group
      sizing context to either reconcile the two totals or add an explicit "these measure different things because X"
      caveat.

## New from 2026-08-14 sweep — 2 genuinely-ambiguous count/content discrepancies, no confident single fix

- [ ] [DOCS] P2. `/codex/06-coding-standards/README.md` states two different service counts for what may or may not be
      the same population: line 51 ("Cloud SDK isolation... **Status:** [IMPLEMENTED] and enforced across all 14
      services") vs line 731 ("T4 | 19 services (instruments-service → monitoring pipeline)" in the Tier promotion
      criteria table). Not auto-fixed: could be genuine drift (the service count grew 14→19 since the Status line was
      last stamped and it was never updated) OR a legitimate scope difference (cloud-SDK-isolation-enforced count vs.
      total current T4-tier count, if some newer services haven't had that specific gate rolled out yet) — determining
      which needs someone who knows the current SDK-isolation rollout state, not a mechanical count reconciliation.
- [ ] [DOCS] P2. `/codex/02-data/defi-data-types-catalog.md`'s "Protocol Coverage Matrix" (near end of file, rows for
      UNISWAP_V2/V3/V4, AAVE_V3, MORPHO) still lists the pre-rename legacy `data_type=` strings verbatim
      (`swap_events, pool_state`, `lending_metrics`) with no "was X" annotation, while the doc's own staleness banner
      (line 49-50) claims these were renamed to `dex_swaps`/`dex_pool_state`/`lending_indices` "in this rev" and every
      other section (§1-3) correctly shows "canonical; was X". Not auto-fixed: this doc's naming history has multiple
      later reversals recorded in its own body (line 65-67: "the `dex_pool_state`→`dex_pools` pending D14 direction is
      REVERSED — `dex_pools`/`dex_swaps` are retired"), so which name the matrix SHOULD show today isn't obvious without
      deeper context on which rename pass the matrix was last synced to.

## Progress Log

- 2026-08-02 (docs_reconciler, dispatch agt-0b4ee1): filed. See sibling issues
  `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md` (the infra gap that let most of the
  cursor-rules/*.mdc fixes in this sweep go undetected until a manual hunt) and
  `docs_reconcile_operator_decisions_2026_08_02.md` (2 genuine authority questions from the same sweep).
- **na-eligibility-audit 2026-08-02** (infra tranche, dispatch agt-fe5e17): KEEP-NA, valid — heterogeneous mix, but the
  large majority of the 15 open items explicitly need human judgment/knowledge this doc's own investigation could not
  resolve ("needs a human who knows what these 3 were meant to cover", "no confident single target", two
  plausible-but-conflicting readings for `ci-cd.md`, a README pass explicitly scoped as needing a human onboarding-doc
  review rather than a mechanical repoint) or are non-actionable design observations (the freshness-ratchet count-only
  note, explicitly "not proposing a fix here"). Stays NA as a whole, same pattern as
  `reference_path_convention_2026_07_23.md`'s own precedent for a mixed bounded/judgment doc. Note for a future split:
  one item (the `.cursor/plans/` artifact `phase_0_cod_service_specs_f0a0afbd.plan.md` dead link — "Fix: delete the dead
  link") reads as individually bounded/mechanical if this doc is ever split; not split here since the doc stays NA in
  full.
- **docs-reconcile 2026-08-03** (dispatch agt-fd4e6d): re-ran both link checkers' `--update-baseline` after fixing the 7
  auto-fixable entries this sweep newly found successors for (mostly a `.plan.md` archival-suffix pattern the
  archive-basename-fallback tier can't catch — flagging that as a worthwhile future improvement to `docspec.py`'s
  resolution tiers, not implemented here since it's a checker-mechanics change beyond this run's doc-fix scope).
  Baselines shrank: `doc_body_link_baseline.yaml` 27→22, `doc_reference_baseline.yaml` 12→1 (9 entries no longer
  reproduced at all — a new tier-5 sibling-repo resolution shipped hours earlier plus an independent frontmatter fix —
  and were dropped as dead weight, not fixed by this sweep). Appended 2 newly-investigated genuine- dead-link findings
  above (the 6 `AUDIT_2026_05_15` slot-file links + 1 `agent_operating_framework_master.md` link) and 1
  genuinely-ambiguous content-staleness finding (`VALIDATOR_COVERAGE_MATRIX.md`) that this doc's 2026-08-02 pass hadn't
  reached yet (only ~16 of the 27 `doc_body_link_baseline.yaml` entries had been individually investigated before
  today).
- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-03** (ao tranche): **MIXED_NO_CLEAN_FLIP — doc stays NA, 2 items closed.** In scope
  because the doc was edited since the 2026-08-02 marker. Independently re-verified all 18 open items live today (not
  just re-read from prior investigation notes). **Closed 2 as STALE_CLOSEABLE above** (the two `cursor-rules/*.mdc`
  dead-link findings, lines ~91/93 pre-edit) — their citing rules were archived out of the live `cursor-rules/` tree on
  2026-08-02 (23:26-23:27Z), mooting the "a live rule cites a dead target" premise; verified via `find`/`git`, not
  inference. Of the 16 survivors, **6 are BOUNDED_RECLASSIFY** — genuinely mechanical dead-link deletions or repoints
  with no open design question, a larger bounded fraction than the 2026-08-02 pass found (it flagged only 1 of 15 as
  individually bounded): the `provider-api-version-manifest.mdc` dead CODEX pointer (already has a confirmed live
  successor named), the transient `.cursor/plans/` artifact citation in `E2E_WORKFLOW_UNIFIED.md`, the
  `mev-protection.md` retired-plan citation (this run closed a research gap the original finding missed —
  `plans/archive/questions_README_retired_2026_05_20.md`'s own retirement table names 2 concrete successors), the 6 dead
  `AUDIT_2026_05_15` slot-file links (verified via `git show --stat` that the cited deletion commit is a superset), the
  `agent_operating_framework_master.md` epic's dead `related:` entry (the epic's OWN body already states its target was
  superseded, no further judgment needed), and the `uac_citadel_architecture` citation in
  `contracts-scope-and-layout.md` (`plans/archive/INDEX.md` already names the exact fact, only a factual rewrite
  needed). **10 remain genuinely VALID_JUDGMENT** (unknown original intent, genuinely ambiguous target, custody/wallet-
  adjacent scoping, or the high-visibility root README.md pass this doc's own text deliberately scoped out to avoid an
  under-verified rewrite). Per this skill's MIXED rubric the doc stays NA as a whole (no clean roll-up either way) —
  flagging the 6 bounded items (doc lines ~55, 61, 78, 98, 103, 119 as of this edit) as candidates for a possible FUTURE
  partial split, matching this doc's own existing `assigned_role: infra`; not drafted by this audit (outside this
  skill's Phase 3 action set for MIXED). Doc-level disposition unchanged from the 2026-08-02 pass; this both closes 2
  genuinely moot items and refines the bounded-item count with fresh verification.
- **docs-reconcile 2026-08-05** (dispatch agt-d8ef73): applied all 6 of the 2026-08-03 na-eligibility-audit's
  BOUNDED_RECLASSIFY items — re-verified each fresh (not trusting the prior audit's claim blindly) then fixed: (1)
  `provider-api-version-manifest.mdc` — dropped the dead `CODEX:` pointer line rather than writing a new stub, lowest-
  risk option since the rule body is already self-sufficient; (2) `E2E_WORKFLOW_UNIFIED.md` — dropped the dead link,
  annotated matching the doc's own established dead-link convention; (3) `mev-protection.md` — repointed to the
  retirement record (had 2 successors, not 1, so linked the record rather than picking one arbitrarily); (4) the 6
  `AUDIT_2026_05_15` slot-ping links — converted to plain-text citations with a deletion note; (5)
  `agent_operating_framework_master.md`'s dead `related:` entry — found ALREADY ABSENT from the current `related:` list
  (fixed sometime between 2026-08-03 and now, no action needed, doc_reference_baseline.yaml is correspondingly empty);
  (6) `contracts-scope-and-layout.md`'s `uac_citadel_architecture` citation — rewrote factually per
  `plans/archive/INDEX.md`, and surfaced (not resolved) an adjacent open question the investigation stumbled onto: the
  paragraph gates a circular-import test exception "until that move lands," and the sibling `unified-api-contracts` repo
  now has copies of `test_ac_uic_alignment.py` at BOTH `tests/internal/` and `tests/internal/unit/` — whether the move
  actually completed (making the exception moot) needs someone to read the actual imports, which is a cross-repo
  code-correctness check beyond this skill's retrieval-layer-doc-health charter. Re-verified all 10 VALID_JUDGMENT
  survivors fresh (still no confident successor for any). `doc_body_link_baseline.yaml` ratcheted 21→11 via
  `--update-baseline` (verified zero NEW breakage first). `unified-trading-pm@72b0f5724`.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **docs-reconcile 2026-08-08** (dispatch agt-bb1c67): live-re-verified all 11 `doc_body_link_baseline.yaml`
  `known_broken` entries via direct filesystem checks (not re-derived logic) — all 11 still genuinely reproduce (no
  successor found anywhere, including a fresh `plans/archive/**` basename search); these map 1:1 onto the 5 open
  findings at lines ~66/73/79/88/94 above (the README.md-cluster, ×3-cluster, ui-testing-layers, architecture-v2, and
  codex/README.md rows). Found and closed one genuine bookkeeping gap: the `agent_operating_framework_master.md`
  `related:` item (above) was already confirmed resolved by the 2026-08-05 Progress Log entry but its checkbox was never
  flipped — flipped now with fresh evidence. The remaining open items (QUICK_REFERENCE.md content-staleness,
  workspace-root-variable.md's `ci-cd.md` ambiguity, root README.md broader staleness, the freshness-ratchet design
  note, and the custody-onboarding-checklist.md / `fireblocks_copper_client_integration` item) are unchanged — none of
  these are tracked in either link-existence baseline, so they were not in scope for this pass's live-reproduction
  check; all remain genuine VALID_JUDGMENT items per the last na-eligibility-audit verdict.
- **na-eligibility-audit 2026-08-08** (ao tranche): KEEP-NA, valid (MIXED, doc stays NA) —
  `grep -cE '^[[:space:]]*[-*] \[ \]'` = **12**, matching. Re-affirms the 2026-08-03 MIXED_NO_CLEAN_FLIP disposition:
  the prior pass's 6 BOUNDED_RECLASSIFY items are now all fixed/closed (docs-reconcile 2026-08-05 + 08-08), leaving 11
  genuine VALID_JUDGMENT/design-observation items unchanged. One NEW item looks individually bounded on this read — the
  `[SCRIPT] P2` `fix_frontmatter.py::get_first_paragraph_after_heading()` truncation fix (added 2026-08-08): the doc
  already names the exact function, the exact bug (`if len(result) > 200: result = result[:197] + "..."`, no
  boundary-awareness), and a specific recommended fix (word/sentence-boundary truncation + flag-for-review) —
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE, flagging for a future partial split rather than acting on it here (doc stays NA in
  full, same as the 2026-08-03 precedent for this exact doc).
- **docs-reconcile 2026-08-08** (third same-day dispatch, one-off boot): full `/docs-reconcile --autonomous` run. Phase
  0 deterministic checks: parity/frontmatter/generator/body-links all clean; `check_codex_doc_freshness.py --strict` =
  25, exactly matching the ratcheted baseline (no gap). Phase 1 semantic sweep (4 parallel sub-agents, read-only): zero
  NEW `authoritative_for` collisions (555 `status: current` docs scanned, corroborating the second-dispatch fix already
  landed today); zero bad `summary:` fields (846 codex docs inspected — corpus already clean from prior remediation);
  **2 genuinely NEW findings, both verified + fixed this run** (not previously surfaced by either of today's earlier
  dispatches): (1) `cursor-configs/cursorrules` — a 4th, differently-scoped doctrine file (distinct from root
  `.cursorrules`, propagated verbatim to every non-PM workspace-root host by
  `scripts/setup-workspace-from-manifest.sh:328-331`) missed the 2026-08-06 doctrine sweep entirely because that sweep's
  "3 sibling surfaces" enumeration never named this file; it still pointed agents at `codex/00-SSOT-INDEX.md` as the
  "canonical entry point" instead of the current grep-native `DOC_INDEX.generated.md` L0-L4 doctrine, and carried a dead
  `OpenClaw/Lobster` section referencing a `.lobster/` dir confirmed absent repo-wide — fixed,
  `unified-trading-pm@bfbc69910`; (2) `/codex/02-data/sports-data-types-catalog.md` self-contradicted within its own
  body (added within the last 24h) — its `executable` predicate section (line ~91-92) states no exchange-type venue has
  a complete adapter as of 2026-08-08 (i.e. `executable=False`), but its Venue Axis section (line 249) labeled the same
  5 exchange venues `executable=True pending credentials` — corrected to `executable=False pending credentials`,
  matching the predicate section and the sibling Fixed-odds-sportsbooks heading's phrasing,
  `unified-trading-pm@71e7f700b`. Broken-link ratchet unchanged from the second dispatch's re-verification earlier today
  (11 `known_broken` in `doc_body_link_baseline.yaml`, all still genuinely reproduce; 0 in
  `doc_reference_baseline.yaml`) — not re-verified a third time same-day, deferring to that already-fresh check. **New
  report-only observation**: computed a freshness-staleness distribution for codex dirs OUTSIDE the 4 cutover-critical
  gated dirs (the existing `check_codex_doc_freshness.py` only scans `02-data`/`04-architecture`/
  `05-infrastructure`/`11-project-management`) — 564 non-gated codex docs, 510 missing `last_reviewed` entirely (0
  flagged as `stale` with a present-but-expired date; the gap is near-universal absence of the field, not expiry).
  Heaviest concentrations: `09-strategy` (184/202), `14-customer-journeys` (126/129), `15-runbooks` (63/75),
  `06-coding-standards` (53/63). Per this skill's own charter this is report-only (widening the freshness gate's scope
  is an operator call, not this skill's to make unilaterally) — flagging the scale here rather than leaving it buried in
  a single run's chat output, consistent with this doc's existing freshness-ratchet design-observation entry above.
- **docs-reconcile 2026-08-08** (fourth same-day dispatch, one-off boot, no `pm_repo_path` in the boot message so this
  slot's own `unified-trading-pm` clone was treated as the target per the role file's fallback). Phase 0 deterministic
  checks re-run fresh: parity/frontmatter (1892 docs)/generator/body-links (1938 docs) all clean; freshness `--strict` =
  25, exactly at the ratcheted baseline (no gap) — identical numbers to the third dispatch above. **Before fanning out a
  full Phase 1 sweep, checked whether one was actually warranted**: `git log 71e7f700b..HEAD` (the third dispatch's
  final commit, ~16:08 UTC, to this run's HEAD ~17:1x UTC) touched **zero** files under `codex/`, `cursor-configs/`,
  `.cursor/rules/`, `AGENTS.md`, or `.cursorrules` — the entire ~1h gap's 38 changed docs were all `plans/**` (routine
  plan-flip/issue-file traffic, explicitly out of this skill's charter per its own `does_not: touch the plans corpus`).
  Since the third dispatch's Phase 1 already scanned the full codex/doctrine surface fresh (555 `status:current` docs
  for collisions, 846 codex docs for summaries) and nothing in that surface changed since, re-running the same 4-agent
  fan-out would have reproduced the identical zero-new-findings result at real token cost for zero marginal signal. Ran
  a direct (non-agent) re-verification of the collision check instead as a cheap sanity floor rather than skipping
  outright: 881 codex docs / 1024 `authoritative_for` claims by `status:current` docs, **0 collisions** — consistent
  with the third dispatch. Broken-link baseline re-checked directly (not re-derived): all 11
  `doc_body_link_baseline.yaml` `known_broken` entries individually probed via `find` for a moved/renamed target — none
  found, all still genuinely dead, matching the third dispatch's numbers exactly (0 in `doc_reference_baseline.yaml`).
  **No new findings, no fixes to apply this run** — the corpus this skill audits was already fully reconciled by the
  immediately-prior dispatch. Flagging the dispatch cadence itself as a minor process observation (not a doc-health
  finding, so not filed as a new issue): 4 separate one-off docs_reconciler boots landed today, the last 2 only ~1h
  apart with zero intervening doc-surface change — a lightweight "skip full fan-out if the last clean run's HEAD sha is
  still an ancestor and no swept path changed since" pre-check (exactly what this entry did by hand) would save real
  cost if this dispatch density continues; not implementing it here since it's an orchestration/dispatch-policy change
  beyond this skill's own charter to alter unilaterally.
- **docs-reconcile 2026-08-08** (fifth same-day dispatch, one-off boot via slot 25). Phase 0: parity/frontmatter (1898
  docs)/generator/body-links all clean; freshness `--strict` = 25, exactly at baseline (no gap). Re-verified all 11
  `doc_body_link_baseline.yaml` `known_broken` entries directly (doc-relative + PM-root-relative + `plans/archive/**`
  basename + a repo-wide `find` by basename) — all 11 still genuinely dead, unchanged from prior dispatches today; `0`
  in `doc_reference_baseline.yaml` (unchanged, empty). Phase 1: 3 parallel read-only hunters swept the 33 codex docs
  touched in the last 24h for structural/self-consistency/summary-quality issues (a narrower, git-diff-scoped sweep than
  the corpus-wide collision/summary passes the 3rd/4th dispatches already ran fresh today) + a direct (non-agent)
  authoritative_for collision re-check (1024 claims, 0 collisions, exact + fuzzy ratio>0.95, all fuzzy hits verified as
  distinct sibling topics sharing template phrasing, not real collisions) + a direct doctrine-consistency check (5 files
  outside the 2 already-covered QG surfaces reference retrieval-layer terminology; all 5 point at the live, current
  `doc-frontmatter-schema.md`, none stale). **5 genuinely NEW findings this run, 4 verified + fixed, 1 routed to the
  owning plan instead of fixed here:**
  1. `/codex/07-security/self-hosted-runner-security-posture.md` — the "Dedicated VM" section overclaimed identity
     decoupling ("ambient identity is now scoped to the runner box alone and no longer doubles as... the
     agent-orchestrator's own identity"), contradicting the doc's own mitigation-ladder item 2 ("Not yet done").
     Verified against `/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` todo 3: the runner
     VM was launched with the SAME AWS IAM instance profile (`uts-orchestrator-epic`) and the SAME GCP service account
     (`unified-trading-sa`, freshly-keyed, not a distinct SA) as the orchestrator box — identity genuinely was NOT
     decoupled, only the VM/box was. Corrected. `unified-trading-pm@27173cdd4`.
  2. `/codex/08-workflows/ci-cd-flow.md` L60-65 — blockquote/list structural break (a continuous 3-item gate-set clause
     split by a blank `>` line + spurious `- ` prefix), the same defect class an earlier 2026-08-08 dispatch fixed in
     sibling docs but missed here. Fixed. `unified-trading-pm@27173cdd4`.
  3. `/codex/08-workflows/ci-cd-flow.md` L204 — stale "PM `scripts/**`" phrasing the doc's own D16 correction (~L810+)
     already superseded with the ratified all-repos framing; L204 wasn't updated when that correction landed. Fixed.
     `unified-trading-pm@27173cdd4`.
  4. `/codex/15-runbooks/alerting/README.md` + `_template.md` — both had genuine free-prose `authoritative_for:` values
     (no list syntax at all) and NO `summary:` field, so the CLAUDE.md-documented L1 retrieval grep
     (`rg -l '^authoritative_for:.*<topic>' codex/`) provably fails to match either doc (tested live). Added a derivable
     `summary:` from the existing prose, normalized `authoritative_for` to a short topic list. Fixed.
     `unified-trading-pm@27173cdd4`.
  5. `/codex/02-data/sports-data-types-catalog.md`'s Venue Axis section ("32 canonical members") diverges substantially
     from the live `VENUES_BY_ASSET_GROUP["sports"]` (31 members, verified via direct import of
     `unified_api_contracts.registry.market_data_categories` — different names on both sides, not just a count
     mismatch). NOT fixed here: the file is mid-migration under the active
     `sports_taxonomy_p1_capture_and_contracts_ 2026_08_08.md` plan (20/23 todos done, `assigned_vm: planning`,
     unlocked), whose own "Codex SSOTs" section already calls this doc "rewritten... now documents the target model" —
     ambiguous whether the doc states a target the registry hasn't fully landed or is simply a stale enumeration, a call
     that needs this chain's full context. Per findings-triage ("fits another plan → annotate it, don't fix — collision
     risk"), added a new `- [ ] [DOCS] P2.` todo to that plan with the full member-list diff instead of editing the
     codex doc directly. Confirmed-not-a-finding (adversarially checked, false positive): `/codex/10-audit/README.md`'s
     missing `summary:`/ minimal frontmatter — verified this is the established convention for every section-level
     `README.md` in the codex (checked 8 siblings: `02-data`, `03-observability`, `04-architecture`, `09-strategy`,
     `11-project-management`, `12-agent-workflow`, `13-codex-governance`, `14-customer-journeys` — all carry only
     `scope:` + no title/summary).
- **docs-reconcile 2026-08-09** (one-off `docs_reconciler` boot, slot 27, no `pm_repo_path` in the boot message so this
  slot's own `unified-trading-pm` clone was treated as the target). Phase 0 all clean (frontmatter 1951 docs, body-links
  1997 docs, retrieval-parity, gen_doc_index 1797 docs; freshness `--strict` = 0/0 across the 4 gated dirs, and a
  report-only sweep of the 570 non-gated codex docs found 515 missing `last_reviewed` — expected, the field isn't
  required outside the 4 gated dirs — plus 1 doc 1 day past the 90d window and 7 deliberately future-stamped). Phase 1:
  7 parallel read-only hunters (1 collision, 1 summary-quality/self-consistency, 1 doctrine-consistency, 1 broken-link
  triage covering all 28 `doc_body_link_baseline.yaml` entries, 3 structural-integrity batches covering all 69 codex
  docs touched in the last 24h). Every candidate independently re-verified by direct file read before acting (not
  trusted from hunter reports alone). **Auto-fixed and shipped this run** (mechanical, no authority call): the mvp-scope
  summary's stale `config version 14` (body says 16); a broken-paren/blank-line/bullet corruption in
  `client-funds-isolation.md`; a garbled 3-column table in `regime-clustering-structure-allocator.md` reconstructed from
  its own fragments; a stale "All three functions produce" claim in `agent-orchestrator-slack-notifications.md`
  (contradicted by the same doc's own 13-Slack/9-Telegram inventory 2 paragraphs above); a table row in
  `per-tab-worktrees.md` exploded across 19 unlinked physical lines, rejoined into one pipe-delimited row; the
  `codex/README.md` Pipeline DAG mermaid diagram, whose `fs` node claimed "consolidated 2026-05-08" while its own edges
  three lines below still referenced 5 undeclared pre-consolidation phantom nodes — routed through `fs`; and a stale
  `LIVE_VENUE`/`MANUAL` enum reference in `paper-vs-live-execution-seam.md`'s own execution-seam diagram, where the
  sibling `operational-modes.md` doc (same 24h review window) already explicitly states "no such member" for both. Also
  applied the 6 `doc_body_link_baseline.yaml` PROVABLY-MOVED repoints the broken-link-triage hunter found (2×
  `orchestrator-multi-vm-topology.md`→`agent-orchestrator-single-vm-architecture.md`, 2× the `naming-convention.md`
  historical citations unlinked rather than repointed since the doc being cited no longer exists as a separate entity —
  it was merged INTO its sibling, so "repointing" would misrepresent the merge as still describing two live docs; 2×
  `codex/.../block-list.md` and 1× `codex/.../defi-canonical-naming-ssot.md` ellipsis-shorthand citations expanded to
  their real full paths); baseline ratcheted 28→22 via `--update-baseline`, verified the drop was exactly those 6 keys
  (git diff), zero unexpected entries added or removed. Re-ran full Phase 0 after all edits — still all clean. Appended
  3 genuinely-new dead-link findings above (not previously tracked) and 1 new content-investigation finding
  (`mvp-universe-per-asset-group.md`'s two-different-totals contradiction — real, verified by direct read, but
  reconciling which total is right needs archetype/asset-group sizing context beyond a mechanical doc fix, so filed
  rather than guessed at). Filed the collision hunter's 1 confirmed P0 finding (`plan-hygiene.md` duplicated verbatim in
  `codex/12-agent-workflow/` and `codex/11-project-management/`, both `status: current`, neither cross-referencing the
  other) as `docs_reconcile_operator_decisions_2026_08_02.md` BLOCKED-OPERATOR-DECISION 5 rather than here (that's the
  doc this corpus already uses for authority calls). Summary-quality and doctrine-consistency hunters: both clean (849
  codex + 719 plans summaries checked; 150 `.cursor/rules/*.mdc` + 22 `agents/*.md` doctrine references checked, none
  stale). Structural-integrity hunters found 8 total candidates across the 69 touched docs (7 fixed above,
  `mvp-universe-per-asset-group.md`'s total-count one filed as a new finding since it needs investigation not a
  mechanical fix) — zero false positives on independent re-verification.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — read end-to-end;
  `grep -cE '^[[:space:]]*[-*] \[ \]'` = **16**, matching. Confirmed the one item this doc's own text flagged
  `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` (the `fix_frontmatter.py` truncation-bug item) is already correctly
  `➡️ EXTRACTED 2026-08-09 to ao_satellite_ao_dispatch_batch11_2026_08_09.md` (verified live: that batch exists,
  `status: active`, `assigned_vm: planning`, its sole todo still genuinely `- [ ]` open — not a stale/dead pointer). The
  remaining 15 items are the same accumulated set of genuine VALID_JUDGMENT calls (ambiguous dead-link successors, a
  root-README pass explicitly scoped out, a design observation the doc's own text says "not proposing a fix here")
  re-verified across 6+ prior audit passes since 2026-08-02 — no new bounded item found on this independent re-read.
- **docs-reconcile 2026-08-14** (one-off `docs_reconciler` boot, slot 10, no `pm_repo_path` in the boot message so this
  slot's own `unified-trading-pm` clone was treated as the target). Phase 0 all clean (parity/frontmatter 2005
  docs/generator/body-links 2051 docs; freshness `--strict` = 5 violations, all either exempt-retired (5) or already
  within the ratcheted baseline / calendar-advisory non-blocking — no gap). `doc_body_link_baseline.yaml` down to 18
  `known_broken` (from 24 on 2026-08-10) — re-verified all 18 directly via `find`, none moved, all still genuinely dead
  or placeholder-prose (per `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md`'s already-tracked
  false-positive class); `doc_reference_baseline.yaml` still empty. Scoped Phase 1 to the ~54 codex/doctrine files
  touched since the last verified-clean point (2026-08-12T21:06, commit `ddfd555ae0` — a docs-reconcile run that, per
  its own commit message, WAS this skill but never logged a Progress Log entry in this or the operator-decisions doc;
  noting the gap, not chasing it further) — 3 parallel structural/self-consistency hunters, every candidate
  independently re-verified by direct read/re-derivation before acting. **7 genuinely-new findings, all confirmed +
  fixed**: (1) `solana-defi-coverage.md` — an orphaned `lst_rates` table-row fragment stranded inside a blockquote
  (broken pipe-table syntax, no header, disconnected from the actual "Restaking data type taxonomy" table 7 lines
  above); (2) `carry-staked-basis.md` — a sentence split by a blank-line paren break + spurious bullet ("(+
  Deribit/stETH" / blank line / "- Bybit/stETH)."); (3) `cursor-configs/CLAUDE.md` itself — a missing opening `**` bold
  marker ("venue lists + adapter KEYS are UAC data**" had no matching opener), verified directly against this session's
  own loaded system-prompt copy of the file; (4) `prediction-markets.md` — its "Integration gaps" section still listed
  G2 ("instrument ID convention") as an open gap in the G1-G7 range, contradicting the SAME doc's own "Instrument ID
  Convention" section 220 lines earlier stating G2 was RESOLVED 2026-08-14 and deleted from the register (cross-checked
  against `prediction-markets-codification-gaps.md`, confirmed no G2 entry); (5)
  `carry-venue-live-integration-reference.md` — frontmatter summary said "13 venues", the funding-endpoints table
  actually has 14 (recounted directly); (6) `defi-venue-protocol-catalogue.md` — `last_reviewed: 2026-09-10`, a FUTURE
  date (impossible for a past-review field, and inconsistent with the doc's own body "Last updated 2026-05-12" four
  lines later) — corrected to match the doc's own self-reported update date; (7) `04-architecture/README.md` —
  "features-service (calendar family)" duplicated as both step 2 and step 5 of the "topologically sorted" Execution
  Order list (a linear ordering can't legitimately repeat a node) — removed the duplicate, renumbered. 2 additional
  candidates investigated and found genuinely ambiguous (needs a human, not a mechanical fix) — filed above as new
  findings rather than guessed at. 1 candidate (the already-tracked `mvp-universe-per-asset-group.md` two-totals P1 item
  above) re-confirmed still open by an independent hunter, not re-filed. Shipping this batch hit a **severe,
  reproducible ship-tooling failure** on 1 of the 7 files (`carry-staked-basis.md`) — 4 consecutive silent no-op ships
  (2× `safe-doc-push.sh` quarantine-drop, 1× `quickmerge.sh` blocked on an unrelated pre-existing red, 1× plain
  `git commit` producing an empty diff despite a positive on-disk `grep` immediately before `git add`) before landing on
  a 5th, fully-atomic attempt — logged as a new, dated instance in
  `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`'s Progress Log (not this doc's scope) since it
  reproduced AFTER that doc's F9 fix and via a code path neither F9 nor its fix touches. The other 6 files shipped
  cleanly via `safe-doc-push.sh` first try: `unified-trading-pm@c7f57a4415`; the 7th landed separately at
  `unified-trading-pm@d307287cf3`. Broken-link/collision/summary-quality/doctrine-consistency hunters not re-run
  corpus-wide this pass (all confirmed clean within the last 4 days by the 2026-08-08/09/10 dispatches; scoped to the
  touched-file set per the established "skip a redundant full fan-out" precedent from 2026-08-08's 4th dispatch).
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:01a5dad404998016]: KEEP-NA, valid — heterogeneous corpus of 16 dead-link/staleness findings, each individually needing human judgment (ambiguous successors, scope-mismatch calls); re-verified clean by 6+ prior audit passes with no new bounded item found on independent re-read.
- **docs-reconcile 2026-08-20** (dispatch agt-9627d5, slot 28): full `/docs-reconcile --autonomous` run — the last
  confirmed full Phase-1 sweep was 2026-08-14, so scope covered the full 6-day gap (~190 codex docs touched
  2026-08-14→now, split across 4 self-consistency-hunter batches) rather than a narrow 24-72h window. Phase 0: all 5
  deterministic checks clean before AND after this run's fixes (parity/frontmatter 2207 docs/freshness `--strict`
  0/324 across the 4 gated dirs/`gen_doc_index` 2053 docs/body-links 2253 docs). **Broken-link residue (this doc's own
  scope) re-verified live**: all 11 real `doc_body_link_baseline.yaml` entries checked via direct `find` + candidate-
  successor investigation (deeper than a bare re-probe — checked `setup-standards.md`/`config-types.md`/
  `dependency-management.md`/`quality-gates.md` as candidate repoint targets for the `06-coding-standards/README.md`
  cluster; none matched closely enough to justify a repoint; `config-types.md` confirmed still a circular redirect
  stub back to the same README). All 11 unchanged from the 2026-08-17 hunter-5 pass — 0 newly-moved, 0 newly-dead,
  0 newly-resolved. Freshness-outside-gated-dirs report: 591 non-gated codex docs (up from 570 on 2026-08-09), 518
  missing `last_reviewed` (expected — field isn't required outside the 4 gated dirs), 60 fresh, 13 stale (oldest:
  `/codex/14-customer-journeys/dart/mode-toggle.md`, 102 days) — consistent growth trend, no action per this skill's
  charter. **Phase 1 (7 parallel hunters: collision/summary/doctrine-consistency all clean full-corpus — 710
  `authoritative_for` claims by `status:current` docs 0 collisions, 2052 in-scope summaries 0 inadequate, 150
  `.cursor/rules/*.mdc` + 26 `agents/*.md` doctrine refs 0 stale; 4 self-consistency batches covering the 6-day gap)
  found 11 genuinely NEW findings this run, all independently re-verified + fixed** (not previously tracked anywhere
  in this or the operator-decisions doc): (1) `non-canonical-path-inventory.md` — 2 table rows split across 6
  physical lines by an embedded raw newline (rows 7+8, "no-migrate-first" disposition table), rejoined; (2)
  `ci-alerting.md` — a `streak_start_sha` paragraph used backslash-escaped backticks inside a single-backtick span
  (invalid Markdown escaping) plus zero-whitespace-adjacent code spans, rendering as mashed-together text — rewritten
  with proper quoting/spacing; (3) `config-dynamic-injection.md` — an em-dash-then-list construction that reads as
  naming the WRONG class as "carries this fix" on first pass (arithmetic was correct, framing was misleading) —
  reworded to name the fixed class (`StrategyDomainConfig`, confirmed via the doc's own prior paragraph) explicitly
  before listing the remaining 8; (4) `epic-assignment-decision-rule.md` — grouped `infrastructure_master` with
  epics that "had 0 active corpus references at fold time," but `epic-taxonomy-2026-08-18.md` (same restructure)
  states it was RENAMED (not folded) to `security_and_cross_cutting_master`, absorbing 296/833 refs (35.5%, the
  LARGEST epic) — corrected, cited the taxonomy doc; (5) `category-instrument-coverage.md` — the `CARRY_BASIS_PERP`
  §6 Coverage table (header + 8 rows) was duplicated verbatim back-to-back with no separator — second copy removed;
  (6) `adv-ranked-universe-scope.md` — a paragraph cited itself ("§ below") promising elaboration on
  `_resolve_start_token`'s fallback that was never written in this doc — found the actual content in
  `carry-staked-basis.md` (already in this doc's own `related:` list) and repointed there; (7)
  `testing/README.md` — the existing 2026-08-15 caveat said `seed-persona.ts` is verified flat (not under
  `helpers/`) but a code-block comment 20 lines below still asserted the `helpers/` path, unchanged — fixed the
  comment to match, and (checked live against the actual `unified-trading-system-ui` checkout in this slot) expanded
  the caveat: `expect-service-tile-locked.ts`/`expect-click-path.ts` don't exist anywhere either, no `helpers/` dir
  exists at all, and the real directory holds ~30 spec files not shown in this doc's tree (the full tree/scaffolding
  rewrite the existing caveat already calls for is still not done — out of a mechanical-fix pass's scope, same
  precedent as the root README.md item above); (8) `custody-onboarding-checklist.md` — the flagged B.2.5 fence
  (opening ` ```bash ` embedded mid-sentence, closing fence + trailing sentence at 82-space indent) turned out to be
  1 of **10** instances of the same collapsed-fence defect in this one file (corpus-wide grep confirmed isolated to
  this file, not systemic) — all 10 found + fixed (B.1.2/B.1.3/B.2.1/B.2.2/B.2.3/B.2.5/B.2.6/B.3.2/B.3.4 shell/python
  blocks reconstructed with proper fences; E.1.3's stray mid-flag whitespace normalized), fence-pair-count verified
  even (28) after the fix; (9) `sports-scheduling-and-sharding.md` — a bold span closed with literal `\*\*`
  (backslash-escaped, doesn't close bold) instead of `**`, fixed; (10) `dependency-health-policy.md` — the escalation
  pseudocode listed 5 conditions as if independent, but they're an ordered if/elif chain (the real
  `alerting_service/rules/connectivity_rules.py::evaluate_dependency_health` was read to confirm) — the no-fallback
  SEV0 floor is checked FIRST, pre-empting WARN/SEV1 in the overlap zone; pseudocode rewritten to show real order +
  cited the source file; (11) `agent-orchestrator-worker-liveness.md` — a 2026-08-15 rewrite (`9786794390`) silently
  dropped 3 sections; one was caught + restored 8h later (`f950580109`) but 2 were not: "Same-VM slot-to-slot
  double-dispatch" (a full section) and the `orphan_reap.py::sweep_orphan_processes` note (a paragraph inside the
  still-live "Kill execution" section) — both restored verbatim from `git show <pre-drop-sha>`, still cited by 2
  other live docs. Every fix independently re-verified against either live filesystem state (UI repo, custody
  checklist self-consistency), the actual source implementation (`connectivity_rules.py`), or git history (the
  worker-liveness drop) before applying — not applied on hunter-report trust alone. Full Phase 0 re-run clean after
  all 11 fixes; shipped as one batch, `unified-trading-pm@101efbe7c7`.
- **context-scout 2026-08-20**: re-verified context_scope (5 entries), unchanged.
