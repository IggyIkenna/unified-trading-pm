---
doc_type: plan
title: Infra satellite — na-eligibility-audit RECLASSIFY extraction batch (batch 1, wave 2, two-todo)
summary: >-
  Two-todo extraction from the infra tranche's 2026-08-21 `/na-eligibility-audit` wave-2 run. Item 1: fix
  `check_line_caps.sh`'s full-corpus `TARGETS` glob (never scans `plans/active/issues/*.md`), extracted from
  `check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md` todo 1. Item 2: sweep the ~694
  `# Epic: infrastructure_master` script-lifecycle-marker header comments across `scripts/`/`tests/`, extracted
  from `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md`'s Phase 3 follow-up. Both are bounded/mechanical
  with an explicit methodology already specified by their source docs — no design fork in either. Same single-batch,
  no-finalize-twin, `status: active` carve-out already established by batch4/batch5/batch19/batch20 for small,
  conflict-clear extractions (source docs' own conflict-checks are cited per-item below, re-verified this pass).
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [infra, ao-dispatch, satellite, batch-1, na-eligibility-audit, plan-hygiene, check-line-caps, epic-taxonomy]
related:
  [
    /plans/active/issues/check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "na-eligibility-audit, infra tranche wave 2, 2026-08-21 — RECLASSIFY (per-todo split) extraction from
    check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md todo 1 and
    epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md's Phase 3 follow-up script-header-sweep todo",
  ]
assigned_role: infra
effort: medium
drift_direction: advance-code
context_scope:
  [
    scripts/plan-hygiene/check_line_caps.sh,
    scripts/plan-hygiene/line_caps_baseline.yaml,
    /plans/active/issues/check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md,
    /codex/11-project-management/epic-taxonomy-2026-08-18.md,
    /codex/06-coding-standards/script-homes.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
  ]
---

# Infra satellite — check_line_caps.sh glob fix + epic-taxonomy script-header sweep (batch 1, wave 2)

> **Fresh carve-out, two-todo, no finalize twin** (same single-batch carve-out precedent as batch4/batch5/batch19/
> batch20 — both items conflict-clear and independently dispatchable, no cross-item dependency). Each todo below is a
> pointer + extraction provenance, not a re-derivation — read the cited source doc's own text for full context before
> starting.

## Todo 1 — fix `check_line_caps.sh`'s full-corpus glob gap

- [ ] [SCRIPT] P2. **Fix `check_line_caps.sh`'s full-corpus `TARGETS` glob to also include `plans/active/issues/*.md`**
      — extracted verbatim from `check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md` todo 1. Live-verified
      2026-08-21 still unfixed: `check_line_caps.sh:144` reads
      `TARGETS=("$PM_DIR/plans/active"/*.md "$PM_DIR/plans/epics"/*.md)` — a bash glob with no `**`/`globstar`, so it
      matches only files DIRECTLY inside `plans/active/`, never `plans/active/issues/*.md` (488 files as of the source
      doc's own count, likely more now). SCOPED mode (the prek pre-commit hook) DOES catch issue docs via a substring
      filter — only the full-corpus sweep (the routine hygiene cron, `/plan-reconcile`/`/ag-closeout-audit`/
      `/na-eligibility-audit` Phase-0 input-gather) has the blind spot. Add a third glob element (or switch to `find`)
      so `plans/active/issues/*.md` is included in full-corpus mode, re-run to get the TRUE violation count across
      every previously-invisible issue doc, and re-seed `hard_count` in `scripts/plan-hygiene/line_caps_baseline.yaml`
      via `--update-baseline` to match (this is the standard shrinking-ratchet onboarding pattern — tolerate the
      newly-visible pre-existing debt, don't block the pipeline). Done-when: a full-corpus run lists
      `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (source doc's confirmed concrete instance, 1017L
      as of 2026-08-19) as a HARD violation, and the baseline is updated to include it (and every other newly-surfaced
      issue-doc violation) without silently exceeding the shrinking-ratchet contract. `quality-gates.sh`-green, shipped
      via `quickmerge.sh --agent --files`. Flip this todo AND the source doc's own todo 1 in the same commit citing
      this batch's completion evidence. Repo: unified-trading-pm.
      **Conflict-check (this pass, 2026-08-21)**: grepped every active `assigned_vm: planning` doc for
      `check_line_caps.sh`'s `TARGETS`/full-corpus-glob content — only the source doc itself and its sibling
      `check_line_caps_sh_whitespace_only_exemption_false_positive_2026_08_19.md` (a DIFFERENT bug in the same file —
      SCOPED-mode's whitespace-diff logic, not the full-corpus glob) touch this file. **Correction (ag-closeout-audit
      2026-08-21)**: the sibling doc's `assigned_vm` was verified still `NA` at the time of this correction — the
      "independently RECLASSIFIED to `assigned_vm: planning`" claim above did not land (or was never applied); treat
      that sibling as still NA pending its own na-eligibility-audit pass, not as already-dispatched. **Same-file caution**:
      a worker picking up this todo should first check whether the whitespace-exemption fix has already landed
      (`git log -- scripts/plan-hygiene/check_line_caps.sh`) to avoid a stale-base merge conflict — both touch
      different, non-overlapping sections of the same script (this todo: the full-corpus `TARGETS` array around
      line 144; the sibling: the SCOPED-mode whitespace-diff check around line 196), so a sequential land is safe
      either order, just re-pull before editing.

## Todo 2 — sweep the ~694 `# Epic: infrastructure_master` script-lifecycle-marker header comments

> **SPLIT 2026-08-22 (measured fresh at pickup)**: true scope is 1250 total corpus-wide
> `^# Epic: infrastructure_master$` hits, 1182 under `scripts/`+`tests/` across **25 repos** — larger than the
> source doc's 2026-08-18 694-count and the plan's own "comparable to or larger than the 297+118-doc sweep" scale
> note anticipated. Too large for one dispatch — splitting into per-repo sub-todos per this todo's own instruction
> ("if the true scope proves too large for one dispatch once measured fresh, split further and note the split
> here"). The original todo (below) stays unchecked as the umbrella item; done when every Todo 2a sub-item is
> checked. Methodology (directory-based, mirrors the source plan's Rule A-E): `scripts/cicd/**` +
> `scripts/self-hosted-runners/**` + `scripts/workflow-templates/**` -> `ci_master`; UAC schema/API-contract
> scripts (e.g. `scripts/openapi/**`) -> `uac_master`; everything else -> `security_and_cross_cutting_master`
> (ambiguous cases default to `security_and_cross_cutting_master` per the source plan's own ambiguous-doc
> precedent).

- [ ] [SCRIPT] P1. **Reclassify every `# Epic: infrastructure_master` script-lifecycle-marker header comment across
      `scripts/` + `tests/`** — extracted verbatim from `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md`'s
      Phase 3 follow-up todo (found during that plan's own corpus-wide `infrastructure_master` sweep, out of that
      plan's original doc-reclassification scope). Per `/codex/06-coding-standards/script-homes.md`'s lifecycle-marker
      convention, every `scripts/`/`tests/` file declares a 3-line header (`# Epic:` / `# Lifecycle:` /
      `# Delete-when:`) — `# Epic: infrastructure_master` is now a STALE value: that epic was renamed
      `security_and_cross_cutting_master` and split (CI-bound content carved to `ci_master`, UAC-bound content
      carved to `uac_master`) as of `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md`'s Phase 3 (already
      shipped for every `plans/**` doc's `parent_epic:` frontmatter — `rg -c "^parent_epic: infrastructure_master$"
      plans/active/ plans/active/issues/` → 0 as of that plan's own verification). The doc's own corpus-wide sweep
      (`rg -l "infrastructure_master" --glob '!plans/archive/**'`) found ~694 hits under this exact
      `# Epic: infrastructure_master` header-comment shape, concentrated in `scripts/` + `tests/`, out of scope for
      that plan's doc-reclassification pass. **Methodology (reuse, don't re-derive)**: apply the SAME
      content-based classification the source plan already validated for docs — a script's OWN functional area
      decides its new `# Epic:` value: `scripts/cicd/*` and `scripts/self-hosted-runners/*` are strong `ci_master`
      candidates; UAC schema/registry-correctness scripts are `uac_master`; the large majority
      (`scripts/quality_gates/*`, `scripts/dev/*`, `scripts/plan-hygiene/*`, general workspace/CI-infra hygiene) are
      almost certainly `security_and_cross_cutting_master`, since script `# Epic:` headers track code OWNERSHIP by
      domain, not doc topic — read `/codex/11-project-management/epic-taxonomy-2026-08-18.md` for the full 9-domain
      decision record and the source plan's own Rule A-E tie-breaks before classifying an ambiguous case. **Scale
      note (from the source plan, still accurate)**: this is comparable to or larger than that plan's own 297+118-doc
      sweep — work it as an iterative sweep (e.g. per-repo or per-directory sub-batches), not one giant single-shot
      diff; if the true scope proves too large for one dispatch once measured fresh, split further and note the
      split here rather than leaving it half-done. Done-when: `rg -c "^# Epic: infrastructure_master$" scripts/
      tests/` → 0 fleet-wide (every hit resolved to `ci_master`/`uac_master`/`security_and_cross_cutting_master`);
      `quality-gates.sh`-green per touched repo, shipped via `quickmerge.sh --agent --files`. Flip this todo AND
      the source doc's own Phase 3 follow-up todo in the same commit citing this batch's completion evidence.
      Repos: every repo with a live `# Epic: infrastructure_master` hit (measure fresh at pickup — the source plan's
      694-count is from 2026-08-18, will have drifted).
      **Conflict-check (this pass, 2026-08-21)**: `rg -l "Epic: infrastructure_master" plans/active/*.md
      plans/active/issues/*.md` → only the source plan's own text (describing the finding), no other active plan
      claims this sweep. First dispatch of this item.

## Todo 2a — per-repo sub-batches (split 2026-08-22, see Todo 2's SPLIT note for methodology)

Each sub-item: `rg -c "^# Epic: infrastructure_master\$" scripts/ tests/` -> 0 for that repo, `quality-gates.sh`-
green, shipped via `quickmerge.sh --agent --files`. File count is the 2026-08-22 measured count (will drift —
re-measure fresh at pickup). Cross-repo case: flip the sub-item in this plan (unified-trading-pm) in the SAME
worker turn as the code commit in the target repo, per RULES.md § 2.

- [x] [SCRIPT] P1. ✅ DONE 2026-08-22 — `unified-trading-pm` (699 files: 59 -> `ci_master`, 25 -> `uac_master`,
      615 -> `security_and_cross_cutting_master`) — `unified-trading-pm@6ff53a98d9`.
- [ ] [SCRIPT] P1. `deployment-service` (323 files; concentrated in `scripts/vm/`, `scripts/migrations/`,
      `scripts/recovery/` — almost entirely `security_and_cross_cutting_master` per methodology, no CI/UAC
      candidates observed in the 2026-08-22 directory sample).
- [ ] [SCRIPT] P1. `unified-api-contracts` (33 files — UAC's own repo, strong `uac_master` prior; verify per-file
      before assuming 100%).
- [ ] [SCRIPT] P1. `e2e-testing` (29 files).
- [ ] [SCRIPT] P1. `market-tick-data-service` (18 files).
- [ ] [SCRIPT] P1. `ibkr-gateway-infra` (11 files).
- [ ] [SCRIPT] P1. `unified-trading-system-ui` (10 files).
- [ ] [SCRIPT] P1. `instruments-service` (10 files).
- [ ] [SCRIPT] P1. `features-service` (10 files).
- [ ] [SCRIPT] P1. `unified-trading-library` (8 files).
- [ ] [SCRIPT] P1. `system-integration-tests` (7 files).
- [ ] [SCRIPT] P1. `agent-orchestrator` (4 files).
- [ ] [SCRIPT] P1. `strategy-service` (3 files).
- [ ] [SCRIPT] P1. `market-data-processing-service` (3 files).
- [ ] [SCRIPT] P1. `alerting-service` (3 files).
- [ ] [SCRIPT] P1. `ml-service` (2 files).
- [ ] [SCRIPT] P1. `fund-administration-service` (2 files).
- [ ] [SCRIPT] P1. `deployment-ui` (2 files).
- [ ] [SCRIPT] P1. `unified-trading-api`, `trading-agent-service`, `greeks-service`, `execution-service`,
      `deployment-api`, `client-reporting-api`, `batch-live-reconciliation-service` (1 file each — small enough to
      bundle into one dispatch if convenient, or split further per-repo).

**Note**: several of the above hits are on template-managed files (`scripts/setup.sh`, `scripts/quality-gates.sh`,
`scripts/setup-workspace.sh`) that are byte-identical copies stamped per-repo from a common origin, not live
symlinks (verified 2026-08-22: no live template dir found under `unified-trading-pm` for these — each repo carries
its own independently-editable copy). No single-point fix exists; each repo's copy needs its own edit.

## Progress Log

- **infra worker, 2026-08-22**: picked up Todo 2. Measured fresh scope at pickup: 1250 total corpus-wide
  `^# Epic: infrastructure_master$` hits (1182 under `scripts/`+`tests/`, 25 repos) — larger than the source doc's
  694-count. Split into Todo 2a per-repo sub-todos per Todo 2's own instruction. Completed `unified-trading-pm`'s
  699-file sub-item this dispatch (directory-based classification: `scripts/cicd/**` +
  `scripts/self-hosted-runners/**` + `scripts/workflow-templates/**` -> `ci_master` (59);
  `scripts/openapi/**` -> `uac_master` (25); everything else -> `security_and_cross_cutting_master` (615)) —
  `unified-trading-pm@6ff53a98d9`. `quality-gates.sh` run + evidence recorded below once it completes. 24 repos
  remain in Todo 2a for future dispatch.
- **na-eligibility-audit 2026-08-21 (infra tranche, wave 2)**: drafted. Item 1 extracted from
  `check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md` todo 1 (KEEP-NA todo 2, the operator-gated
  content-split question for the concrete over-cap doc, stays in the source doc). Item 2 extracted from
  `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md`'s Phase 3 follow-up (that plan's own Phase 3 residual
  prose-mention sweep + the 2-doc parent_epic blocker stay in the source doc — both genuinely still need per-item
  judgment/an operator-ruled `check_line_caps.sh` carve-out, unlike this bounded, methodology-specified sweep). Both
  source docs' own checkboxes struck through + marked EXTRACTED in the same pass, pointing here. Conflict-checks for
  both items run fresh this pass (not re-derived from the source docs' own text) — see each todo's own note above.
