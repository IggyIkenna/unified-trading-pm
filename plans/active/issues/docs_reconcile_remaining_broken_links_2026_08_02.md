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

- [ ] [DOCS] P2. `.cursor/rules/core/provider-api-version-manifest.mdc` cites the ARCHIVED `unified-trading-codex`
      repo's `02-data/provider-api-version-manifest.md` (via `../../unified-trading-codex/`). The live content-of-record
      for this topic is a YAML file, not a doc:
      `unified-api-contracts/unified_api_contracts/config/provider_api_versions.yaml` (confirmed via the sibling rule
      `.cursor/rules/config/provider-manifest-ssot.mdc`). Fix: either write the missing stub doc pointing at the YAML,
      or drop the dead `CODEX:` pointer line.
- [ ] [DOCS] P3. `/codex/00-getting-started/E2E_WORKFLOW_UNIFIED.md` cites a transient `.cursor/plans/` artifact,
      `phase_0_cod_service_specs_f0a0afbd.plan.md` — `.cursor/plans/` doesn't exist; the hash-suffixed filename is a
      transient Cursor-generated artifact, never durable. Fix: delete the dead link.
- [ ] [DOCS] P2. `/codex/04-architecture/README.md` (×4: `BATCH-LIVE-SYMMETRY.md`, `communication-patterns.md`,
      `compute.md`, `scaling.md`) + `/codex/04-architecture/batch-live-architecture.md` (`communication-patterns.md`) —
      the README's own ToC clearly intended these as sibling docs fanned out from it, but none were ever created; the
      content lives entirely inline in README.md instead (control-verified: `concurrency.md`, linked from the same
      table, DOES exist — so this is a real gap, not a resolution-logic bug). Fix: either extract the relevant README
      sections into the 4 real files, or strip the dead ToC/inline links and note the content is inline.
- [ ] [DOCS] P3. `/codex/06-coding-standards/README.md` (×3: `./PREK_MIGRATION_WALKTHROUGH.md`,
      `configuration-management.md`, `formatting-standards.md`) — same table already has a precedent fix (line 61: a
      broken `STANDARDS.md` link was redirected to `adapter-dead-code-and-fallback-ban.md` on 2026-07-24), but no
      confident redirect target was found for these 3 (checked `config-types.md` as a candidate for #2 — it's itself a
      redirect stub pointing back at this same README, so using it would create a cycle). Needs a human who knows what
      these 3 were meant to cover.
- [ ] [DOCS] P3. `/codex/06-coding-standards/ui-testing-layers.md` cites `../../../.claude/rules/workspace-workflow.md`
      — no `rules/` subdir under `cursor-configs/`, no file named `workspace-workflow.md` anywhere in the repo.
- [ ] [DOCS] P3. `/codex/07-security/mev-protection.md` cites the retired `plans/questions/` dir's
      `defi_readiness_catalogue_2026_05_08.md` — `plans/questions/` was wholesale retired 2026-05-20, but unlike the
      sibling case already fixed in this sweep (`per-venue-paper-policy.md`, resolved via a concurrent process to the
      plan it spawned), no spawned successor for THIS specific slug is discoverable anywhere in `plans/active/` or
      `plans/archive/`.
- [ ] [DOCS] P3. `/codex/09-strategy/architecture-v2/README.md` cites `templates/archetype-doc.md` — no `templates/` dir
      exists under `architecture-v2/`; the real `archetypes/` dir holds ~19 fully-written archetype docs with no shared
      template file ever created.
- [ ] [DOCS] P3. `/codex/15-runbooks/custody-onboarding-checklist.md` cites a `plans/active/` slug,
      `fireblocks_copper_client_integration_2026_06_01.md` — no plan under this or any similar slug exists anywhere.
      Plausibly this custody/wallet-adjacent plan was simply never authored.
- [ ] [DOCS] P3. `codex/README.md` cites `.github/PRE_COMMIT_SETUP.md` — `.github/` contains only `actionlint.yaml`,
      `actions/`, `workflows/`; no pre-commit doc under any name/case.
- [ ] [DOCS] P2. `cursor-rules/architecture/feature-producer-consumer-contract.mdc` cites codex `04-architecture`'s
      `feature-dictionary.md` — file does not exist anywhere in the repo, not a rename.
- [ ] [DOCS] P2. `cursor-rules/testing/tradfi-path-builder-byte-identity.mdc` cites codex `04-architecture`'s
      `path-canonicalization.md` — file does not exist anywhere in the repo, not a rename.

## New from 2026-08-03 sweep — genuinely dead links, no successor (verified via direct invocation of the live checkers, not re-implemented logic)

- [ ] [DOCS] P2. `plans/audit/results/archive/AUDIT_2026_05_15_harsh_side_completion.md` cites 6 dead targets, all the
      same shape: `../../harsh_orchestrator/pings/slot_{2,5,6,7,8,9}.md`. Git archaeology confirms all 6 were
      **deliberately, permanently deleted** by commit `890ef4b86` (2026-06-24, "operator-deleted... no longer needed") —
      not a rename, no successor exists or should be invented. Fix: delete the 6 dead links from the citing doc (it's
      already an `archive/` doc itself, so this is pure link cleanup with no content implication).
- [ ] [DOCS] P3. `plans/epics/agent_operating_framework_master.md` (`related:` frontmatter) cites
      `../active/orchestrator_v07_multi_vm_topology_2026_05_21.md` — no file under this or any similar slug exists
      anywhere in the repo; multi-VM dispatch itself was deprecated 2026-06-27 in favor of the single-VM architecture,
      so there is no "current" successor to point to, only a retired concept. Fix: drop the dead `related:` entry (the
      epic's other `related:` entries remain valid).

## Genuinely ambiguous — broken, but no confident single target (P2, report-only per the skill's own severity guidance — not an authority question)

- [ ] [DOCS] P2. `codex/validators/QUICK_REFERENCE.md` (status: current) redirects to
      `/codex/10-audit/VALIDATOR_COVERAGE_MATRIX.md` as one of its two "actual SSOTs" — that target resolves fine as a
      FILE (not a broken link), but its own content admits `status: stale` and its own summary says "Service/UI lists
      use retired repo names and are stale" (title still dated "2026-02-21", no `superseded_by:` pointer). So a current
      doc's redirect target is itself stale with no named successor — this is a content-staleness gap one layer behind a
      link check, not a broken link per se. Needs a human who can either refresh the matrix (retired repo names →
      current fleet) or determine there's no live consumer left and archive it with QUICK_REFERENCE.md repointed
      elsewhere.
- [ ] [DOCS] P3. `/codex/02-data/contracts-scope-and-layout.md` cites the `plans/active/` slug
      `uac_citadel_architecture_2026_05_07.md` — `plans/archive/INDEX.md` (line 177) tracks this exact slug's
      disposition as "Superseded by completed execution plan," naming `uac_citadel_implementation_execution` as the
      successor ("Complete (79/79)") — but neither slug corresponds to any actual file on disk anywhere in `plans/`.
      These read as pure status-table labels, not filenames. Whoever picks this up should start from
      `plans/archive/INDEX.md`'s citadel section rather than guessing.
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
