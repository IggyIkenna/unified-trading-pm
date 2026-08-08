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
context_scope:
  [
    /plans/active/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md,
    /plans/active/issues/docs_reconcile_operator_decisions_2026_08_02.md,
    scripts/quality_gates/check_doc_body_links.py,
    scripts/plan-hygiene/check_reference_paths.py,
    scripts/quality_gates/check_codex_doc_freshness.py,
  ]
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
      2026-08-05 (docs-reconcile): still no confident successor, left open.**
- [ ] [DOCS] P3. `/codex/06-coding-standards/README.md` (×3: `./PREK_MIGRATION_WALKTHROUGH.md`,
      `configuration-management.md`, `formatting-standards.md`) — same table already has a precedent fix (line 61: a
      broken `STANDARDS.md` link was redirected to `adapter-dead-code-and-fallback-ban.md` on 2026-07-24), but no
      confident redirect target was found for these 3 (checked `config-types.md` as a candidate for #2 — it's itself a
      redirect stub pointing back at this same README, so using it would create a cycle). Needs a human who knows what
      these 3 were meant to cover. **Re-verified 2026-08-05 (docs-reconcile): still no confident successor, left open.**
- [ ] [DOCS] P3. `/codex/06-coding-standards/ui-testing-layers.md` cites `../../../.claude/rules/workspace-workflow.md`
      — no `rules/` subdir under `cursor-configs/`, no file named `workspace-workflow.md` anywhere in the repo.
      **Re-verified 2026-08-05 (docs-reconcile): still absent everywhere, left open.**
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
      the link dropped, no evidence-backed target exists to repoint to.**
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

- [ ] [DOCS] P2. Root `README.md` (the PM repo's own top-level onboarding doc) has multiple stale claims beyond the
      `cursor-rules/` sync claim already corrected (unified-trading-pm@c9dc2cfb5):
  - Cites `scripts/workspace/sync-rules-pull.sh` in its "Key Scripts" table — this file **does not exist** (confirmed
    via `find`).
  - Describes `unified-trading-codex` as a live sibling repo ("standards and specifications") in its "Required Workspace
    Structure" diagram — that repo is ARCHIVED (SSOT = this repo's own `codex/`, per CLAUDE.md).
  - The "Required Workspace Structure" diagram shows `~/repos/unified-trading-system-repos/` as the workspace root —
    doesn't match the current `/home/ubuntu/unified-trading-system-repos/` + `.tabs/<slot>/` per-slot worktree layout
    (Path-B, live since 2026-06-08).
  - This needs a real onboarding-doc pass (verify every script/path/repo reference against current reality), not a
    narrow link repoint — deliberately out of scope for this sweep to avoid an under-verified rewrite of a
    highly-visible root file under time pressure.

## Design observation — codex freshness ratchet is count-only (P2, informational — not this skill's gate to change)

- [ ] [SCRIPT] P3. `check_codex_doc_freshness.py`'s ratchet (`scripts/quality_gates/check_codex_doc_freshness.py`)
      compares `len(violations) > baseline` — a pure COUNT comparison, not a set comparison. Verified during this sweep:
      on 2026-08-02, 4 docs newly lost their `last_reviewed` field/went stale
      (`cross-reference-path-     convention.md`, `local-tmux-precompact-watcher.md`, `lst-exchange-rate-surfaces.md`,
      `plan-priority-tier-and-dispatch-ordering.md`) while 4 DIFFERENT docs got genuinely fixed
      (`claude-code-settings-symlink.md`, `gcs-object-operations.md`, `issue-doc-lifecycle.md`,
      `manifest-consolidator-ssot.md`) — net count unchanged (24=24), so the gate reported "✅ At baseline" the whole
      time, silently masking the churn. Not proposing a fix here (freshness-gate design is explicitly outside this
      skill's charter to change unilaterally per its own "never weakened by either mode" rule) — just recording the
      observation so it's visible if/when the freshness-gate design is revisited.

## New from 2026-08-08 sweep — 1 dead link with no confident target, 1 script root-cause finding

- [ ] [DOCS] P3. `.cursor/rules/core/plans-prompts-index.mdc` (`alwaysApply: false`, self-branded "SSOT for where agent
      prompts and task entry points live") — its "Task Entry Points" table cites
      `unified-trading-pm/plans/tasks/cursor/START_HERE.md` and `unified-trading-pm/plans/tasks/claude-code/START.md`;
      `plans/tasks/` does not exist anywhere in the repo (confirmed via `find`). Every OTHER table in this same file
      (Phase Prompts ×3, Sports ×1, the `CODEX:` pointer) resolves correctly — this is an isolated staleness, not a
      wholesale-obsolete rule. Not auto-fixed: unlike the `04-architecture/README.md` ToC cluster above, there's no
      equivalent doc elsewhere in the corpus using this "Cursor vs Claude Code START_HERE/START" convention to confirm
      whether the right fix is (a) write the two missing onboarding docs, (b) repoint to `plans/active/task_template.md`
      (the CLAUDE.md-current plan-authoring entry point, but not a strict semantic match — that's for authoring a NEW
      plan, not general "task entry"), or (c) strip the table because the per-tool-onboarding-doc concept itself was
      retired without anyone updating this index. Needs a human who knows whether these were ever built.
- [ ] [SCRIPT] P2. **Root cause of most of this doc's own truncated-summary findings, identified 2026-08-08**:
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
      review before it ships, rather than silently landing a partial sentence.

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
