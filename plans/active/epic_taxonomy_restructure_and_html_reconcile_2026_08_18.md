---
doc_type: plan
title: Epic taxonomy restructure (9-domain service layer) + /plan-reconcile HTML artifact mode
summary:
  Re-cut the non-asset-group epic layer (L1-L5, 19 epics) onto 9 named service/subsystem domains (ao, ci, strategy
  service, deployment & observability, execution service, UAC & reference-data/instruments, market data &
  processing, features & ML, security & cross-cutting) — folding 4 zero/low-reference epics into siblings, carving
  ci_master and uac_master out of infrastructure_master/client_isolation_and_governance_master's ~300 combined
  references, and renaming the infrastructure_master remainder to security_and_cross_cutting_master. Asset-group L0
  epics (cefi/defi/tradfi/predictions/sports) are untouched — orthogonal axis, not part of this restructure. Extends
  /plan-reconcile with an `--epic <slug>` scope (using docspec.py's real registry-validated parent_epic, not
  regenerate_active_plan_inventory.py's broken filename-substring "orphan" check — a real bug found and flagged
  during this plan's own research), and a new HTML-artifact-generation phase generalizing the "AO Provider Dispatch
  Ledger" report built by hand this session into a reusable per-epic template, published so a shareable link exists.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [epics, plan-reconcile, html-artifact, taxonomy, quality-gates, plan-hygiene]
related:
  [
    /plans/epics/README.md,
    /plans/epics/infrastructure_master.md,
    /plans/epics/client_isolation_and_governance_master.md,
    /plans/PLAN_FORMAT.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/12-agent-workflow/epic-keyword-surface.yaml,
    cursor-configs/skills/plan-reconcile/SKILL.md,
    scripts/plan-hygiene/check_line_caps.sh,
    scripts/plan-hygiene/check_parent_epic_alignment.py,
    scripts/docs/docspec.py,
    scripts/plans/regenerate_active_plan_inventory.py,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    /plans/epics/infrastructure_master.md,
    /plans/epics/client_isolation_and_governance_master.md,
    /codex/12-agent-workflow/epic-keyword-surface.yaml,
    cursor-configs/skills/plan-reconcile/SKILL.md,
    scripts/plan-hygiene/check_parent_epic_alignment.py,
    scripts/docs/docspec.py,
  ]
---

# Epic taxonomy restructure (9-domain service layer) + /plan-reconcile HTML artifact mode

## Why

Operator decision (interactive session, 2026-08-18), building directly on this session's AO multi-provider audit
work: recut the epic layer onto 9 named domains (ao, ci, strategy service, deployment & observability, execution
service, UAC & reference-data/instruments, market data & processing, features & ML, security & cross-cutting), reuse
the "AO Provider Dispatch Ledger" HTML report built earlier this session as the universal per-epic report template,
and extend `/plan-reconcile` so `/plan-reconcile <epic_name>` reconciles one epic and regenerates+publishes its HTML
ledger, while bare `/plan-reconcile` (no arg) does this for everything.

Research (this session, general-purpose sub-agent, full findings in this doc's Progress Log) established the actual
current state: 29 files under `plans/epics/` (28 epics + README), 15,669 total lines, 21 of 24 active epics actually
referenced by the corpus's 836 plan/issue docs. `parent_epic` coverage is already ~99.6% (only 2 structural index
docs + 1 legacy pre-frontmatter doc lack it) — so this is NOT an orphan-backfill problem, it's a **taxonomy**
problem: `infrastructure_master` alone absorbs 296/833 (35.5%) of all `parent_epic` references despite its own
summary framing it narrowly, no epic owns CI or UAC directly, and 4 epics are effectively dead weight (0-1
references each) or genuinely duplicate a sibling (`agent_operating_framework_master` vs `orchestrator_master`, both
L5/meta, near-identical summaries).

**A real bug found along the way, not part of this plan's own scope to fix inline but tracked here since it
directly affects Phase 4's orphan-check design**: `scripts/plans/regenerate_active_plan_inventory.py`'s "orphan"
concept is a filename-substring match against each epic's raw body text / `related:` list — it does **not** read
`parent_epic:` frontmatter at all. Sampled 4 real AO-dispatch-batch plans, each with fully valid, registry-resolving
`parent_epic:` — 3 of 4 would register as `**orphan**` under this script's logic purely because epics' `related:`
lists don't track AO-dispatch-batch churn. The actual hard enforcement already lives correctly in `docspec.py`
(`FieldSpec("parent_epic", Req.R, "registry", registry="epic")`, `Sev.HARD` on an unresolvable slug) — Phase 4 below
builds the new orphan check on `docspec.py`'s logic, not the inventory script's.

## Non-goals

- The 5 asset-group L0 epics (`cefi_master`, `defi_master`, `tradfi_master`, `predictions_master`, `sports_master`)
  are **not** touched by this restructure — orthogonal axis (vertical/market vs. service/subsystem), operator
  confirmed this reading is correct by not naming them in the 9-domain list.
- Not fixing `regenerate_active_plan_inventory.py`'s broken orphan logic in place — Phase 4's new `/plan-reconcile
  --epic` orphan check bypasses it entirely by using `docspec.py` instead. Retiring/fixing the inventory script
  itself (which still feeds a live twice-daily Cloud Scheduler job) is out of scope here; flagged as a follow-up.
- Not attempting a byte-for-byte literal merge of `agent_operating_framework_master` + `orchestrator_master`'s prose
  in this pass — both stay as separate files under the same `ao` domain grouping (Phase 2), a full content merge is
  flagged as a deferred follow-up given real overlap-resolution risk on two 450+-line files with 61 and 63 live
  references respectively.

## Design summary — the 9-domain mapping

| # | Domain | Epic(s) after this plan | Disposition |
|---|---|---|---|
| 1 | AO | `orchestrator_master` (63 refs) + `agent_operating_framework_master` (61 refs) | Both kept, grouped under one domain tag — not merged (see Non-goals) |
| 2 | CI | **NEW** `ci_master` | Carved from `infrastructure_master`'s CI-topic references (Phase 3) |
| 3 | Strategy service | `strategy_master` (14 refs) + `dart_and_promote_master` (0 refs) + `global_ledger_pnl_attribution_master` (0 refs) | The two 0-reference epics folded in (Phase 2) |
| 4 | Deployment & observability | `deployment_and_user_management_master` (17 refs) + `observability_master` (40 refs) + `escalation_and_disaster_recovery_master` (1 ref) | Escalation folded into observability (Phase 2) |
| 5 | Execution service | `execution_master` (1 ref) + `batch_live_symmetry_master` (12 refs) + `trading_agent_master` (0 refs) | trading_agent_master folded in (Phase 2) |
| 6 | UAC & reference-data/instruments | `instruments_master` (29 refs) + **NEW** `uac_master` | uac_master carved from infrastructure_master + client_isolation_and_governance_master's UAC-topic references (Phase 3) |
| 7 | Market data & processing | `mtds_mdps_master` (17 refs) + `manifest_master` (20 refs) | Title/slug mismatch on mtds_mdps_master fixed (Phase 1) |
| 8 | Features & ML | `features_and_ml_master` (4 refs) | No change |
| 9 | Security & cross-cutting | `security_and_cross_cutting_master` (renamed from `infrastructure_master`, minus its CI/UAC carve-outs) + `client_isolation_and_governance_master` (3 refs, minus its UAC carve-out) + `system_readiness_master` (4 refs) | The big rename + split (Phase 3) |

Untouched, no domain (confirmed non-goal): `cefi_master`, `defi_master`, `tradfi_master`, `predictions_master`,
`sports_master`. Untouched, historical only: the 3 `*_SUPERSEDED_*.md` epic files. `plan_hygiene_master` (21 refs,
this plan's own parent) stays its own thing — it's process/tooling-about-plans, not a service domain; not forced
into any of the 9.

## Codex SSOTs

- `/codex/11-project-management/epic-taxonomy-2026-08-18.md` (NEW, Phase 1) — the decision record for the table
  above, superseding the implicit L0-L5 tier framing wherever it conflicts.
- `/codex/11-project-management/epic-html-report-format.md` (NEW, Phase 1) — the universal per-epic HTML report
  template spec, generalized from the AO Provider Dispatch Ledger.
- `/codex/11-project-management/doc-frontmatter-schema.md` — read before touching any epic frontmatter (`name`,
  `tier`, `parent` fields); this plan does not change the schema itself.
- `/codex/12-agent-workflow/epic-keyword-surface.yaml` — extended, not replaced, in Phase 3.

## Todos

### Phase 1 — design docs + safe mechanical fixes (no reclassification risk)

- [x] [DOCS] P1. ✅ DONE 2026-08-18 — authored `/codex/11-project-management/epic-taxonomy-2026-08-18.md`, the
      decision record: the 9-domain table, the "why not the 5 asset-group epics" non-goal, and the disposition of
      every active epic. `unified-trading-pm@<see Progress Log>`.
- [x] [DOCS] P1. ✅ DONE 2026-08-18 — authored `/codex/11-project-management/epic-html-report-format.md`,
      generalizing the AO Provider Dispatch Ledger's section structure into a reusable spec (10 sections, several
      explicitly optional/omit-if-empty), plus a design-token approach that deliberately does NOT reuse one shared
      stylesheet across epics (each epic's report picks its own palette per `artifact-design`, to avoid the
      every-report-looks-the-same smell). `unified-trading-pm@<see Progress Log>`.
- [x] [DOCS] P2. ✅ DONE 2026-08-18 — fixed `mtds_mdps_master.md`'s title from "Data pipeline master coordination —
      2026-05-20" to "MTDS/MDPS Master — Market Data Pipeline Coordination". `unified-trading-pm@<see Progress Log>`.
- [ ] [DOCS] P2. Refresh `plans/epics/README.md`'s epic-registry table — **deferred to Phase 6** (not done here):
      it's already flagged stale with its own tracked todo (line ~225, "script this regeneration so the registry
      can't drift again"), and Phase 2/3 will change the epic set again (2 folds→removals, 2 new epics, 1 rename) —
      doing one clean regeneration after all of that lands avoids 3 redundant edits to the same table.

### Phase 2 — zero/low-reference epic folds (≤2 referencing docs each, low blast radius)

- [ ] [DOCS] P1. Fold `trading_agent_master.md` (42 lines, 0 references) into `execution_master.md` — merge its
      content as a new subsection, then mark `trading_agent_master.md` `status: superseded` with a banner pointing
      to `execution_master.md` (same pattern as the 3 existing `*_SUPERSEDED_*.md` files — do not delete). Done
      when: 0 open todos lost, `execution_master.md` reads coherently with the merged content.
- [ ] [DOCS] P1. Fold `dart_and_promote_master.md` (0 references) and `global_ledger_pnl_attribution_master.md` (0
      references) into `strategy_master.md` — same merge-then-supersede pattern. Done when: both source files
      `status: superseded`, `strategy_master.md` reads coherently.
- [ ] [DOCS] P1. Fold `escalation_and_disaster_recovery_master.md` (193 lines, 1 reference) into
      `observability_master.md` — merge content, `status: superseded` banner, and **update the 1 referencing doc's
      `parent_epic:` frontmatter** from `escalation_and_disaster_recovery_master` to `observability_master` (find it
      via `rg -l "^parent_epic: escalation_and_disaster_recovery_master" plans/active/ plans/active/issues/`). Done
      when: that 1 doc's frontmatter is updated and `docspec.py` still resolves it cleanly.

### Phase 3 — the big split: ci_master + uac_master carve-out, infrastructure_master rename

- [ ] [SCRIPT] P0. Grep-classify all `parent_epic: infrastructure_master` docs (296) plus any UAC-topic docs
      currently under `client_isolation_and_governance_master` (grep body text for "UAC"/"unified-api-contracts"/
      "canonical instrument_id" within that epic's own "Assigned active plans" links, and cross-check each linked
      doc's own body) into three buckets — CI-bound, UAC-bound, remainder (security/cross-cutting) — using keyword
      rules seeded from `infrastructure_master.md`'s own existing "Assigned active plans" section (it already groups
      `ci_*`-named plans together, e.g. `ci_consolidated_closeout_2026_07_25`, `ci_pipeline_speed_and_cost_redesign`,
      `ci_vm_exposure_remediation`, `ci_satellite_ao_dispatch_batch*` — these are unambiguous CI-bound seeds; expand
      the keyword net from there, not from a blank slate). Done when: every one of the 296 (+ N client_isolation UAC
      docs) has a bucket assignment, with a documented (not silent) "ambiguous, needs a human call" bucket for
      anything the keyword net can't confidently place — do not force a 100%-automated classification if genuine
      judgment calls remain; list them instead.
- [ ] [DATA] P0. Extend `/codex/12-agent-workflow/epic-keyword-surface.yaml` with new `ci_master:` and `uac_master:`
      entries (keyword lists derived from the classification above), and update `infrastructure_master:`'s entry to
      reflect the narrowed remainder (or add it fresh under the new `security_and_cross_cutting_master:` key if the
      rename happens in the same commit — see next todo). Done when: `check_parent_epic_alignment.py --emit-surface`
      run against the reclassified corpus shows no new systemic mismatches for the 3 epics.
- [ ] [SCRIPT] P0. Create `plans/epics/ci_master.md` (new epic file, correct frontmatter per
      `doc-frontmatter-schema.md`'s epic spec: `name: ci_master`, a `tier`, `priority`, `assigned_vm`, `parent`) —
      populate its "Assigned active plans" section from the CI-bound bucket above, and its narrative sections
      (scope/current-state/critical-path) summarized from what those plans actually cover, not invented.
- [ ] [SCRIPT] P0. Create `plans/epics/uac_master.md` (new epic file, same frontmatter discipline) — populate from
      the UAC-bound bucket (spans both former `infrastructure_master` and `client_isolation_and_governance_master`
      referrers).
- [ ] [SCRIPT] P0. `git mv plans/epics/infrastructure_master.md plans/epics/security_and_cross_cutting_master.md` —
      update its own `name:`/`title:` frontmatter to match, strip out the sections/links that moved to `ci_master`/
      `uac_master` (don't just leave them duplicated), and update `client_isolation_and_governance_master.md` to
      strip whatever UAC-specific section moved to `uac_master.md`.
- [ ] [SCRIPT] P0. Bulk-update `parent_epic:` frontmatter across every doc in the CI-bound and UAC-bound buckets
      (297+N docs) to point at `ci_master`/`uac_master` respectively — the remainder (still pointing at
      `infrastructure_master`) needs its literal string value updated to `security_and_cross_cutting_master` too,
      since the slug changed. Batch by file-safe scripted `sed`/frontmatter-aware rewrite, never a blind global
      find-replace across full file bodies (only the `parent_epic:` line, never prose that happens to mention
      "infrastructure"). Done when: `rg -c "^parent_epic: infrastructure_master"` returns 0 across the whole corpus.
- [ ] [SCRIPT] P1. Corpus-wide grep for any OTHER reference to the literal string `infrastructure_master` (codex
      docs, `related:` fields, prose citations, `depends_on:`) and fix each per the "a doc/pointer that misled you is
      a finding — fix it in the same turn" HARD RULE. Done when: `rg -l "infrastructure_master"` returns only the
      renamed file itself (as a redirect/history note, if one is left) and this plan's own Progress Log.
- [ ] [REVIEW] P0. Run `quality-gates.sh` (PM-level, the `docspec`/`check_frontmatter_schema` step specifically) over
      the whole corpus post-rename — confirm 0 new HARD `parent_epic`-unresolvable violations. Done when: green,
      cited with the actual QG run evidence, not assumed.
- [ ] [DOCS] P2. Update `plans/epics/README.md`'s registry table for the Phase 3 changes (2 new epics, 1 renamed,
      folding in Phase 2's changes too if not already done).

### Phase 4 — `/plan-reconcile` extension: epic scope + HTML artifact generation

- [ ] [INFRA] P1. Add an epic-scoped mode to `/plan-reconcile` — `/plan-reconcile <epic_slug>` resolves the epic via
      the live registry under `plans/epics/` (fail loudly on an unknown slug, don't silently fall back to a tranche
      guess), then finds its children via `rg "^parent_epic: <slug>$"` across `plans/active/*.md` +
      `plans/active/issues/*.md` — this is the docspec-aligned, frontmatter-driven definition, NOT the substring
      matcher (see Why). Bare `/plan-reconcile` (no arg) keeps its current `all` tranche-sweep behavior but ALSO now
      iterates every active epic for the new orphan check below. Update `cursor-configs/skills/plan-reconcile/
      SKILL.md` to document the new mode alongside the existing tranche modes — don't replace the tranche mode, add
      to it (some docs, e.g. asset-group ones, are better swept by tranche; epic-scoped is the new option for the
      9-domain layer + the asset-group L0 epics alike).
- [ ] [INFRA] P1. Add the real orphan check: every doc under `plans/active/*.md` + `plans/active/issues/*.md` (types
      plan/issue/audit-result/audit-instruction per `docspec.py`'s `Req.R` on `parent_epic`) already gets this HARD
      gate at QG time — `/plan-reconcile`'s new job is to run it PROACTIVELY (not just wait for a commit to trip it)
      and, when scoped to one epic, report only that epic's own children's status rather than the whole corpus. Done
      when: a deliberately-broken test doc (bad `parent_epic` value) is caught by the new check before QG would have
      caught it.
- [ ] [INFRA] P1. Build the HTML-generation phase, following `/codex/11-project-management/epic-html-report-format.md`
      (Phase 1) — reads the epic's child docs (open/done counts, `[OPERATOR]`-tagged items, aggregator exclusion per
      the existing `/open-task-count` convention), renders the report, writes it to `plans/epics/html/<slug>.html`
      (new directory, alongside `plans/epics/`), and publishes it via the Artifact-publish mechanism so a shareable
      link exists — the skill's final chat report includes that link, not just a local file path. On a RE-RUN for
      the same epic, update the SAME artifact (don't create a new URL each time) — mirrors how this session's AO
      ledger was iteratively updated across multiple republishes.
- [ ] [DOCS] P2. Update `SKILL.md`'s own Phase 6 ("report") language — it currently states "NEVER create
      `*_SUMMARY.md` — the final report is chat text"; clarify that the new HTML artifact is NOT a `*_SUMMARY.md`
      (it's a structured, published report with a shareable link, explicitly requested by the operator) and doesn't
      conflict with that ban — the ban is about ad hoc unpublished summary docs cluttering the repo, not this.

### Phase 5 — QG hardening for the new structure

- [ ] [SCRIPT] P1. Add a new quality-gate check (extend `check_line_caps.sh`'s sibling script family under
      `scripts/plan-hygiene/`, or a new `check_epic_html_freshness.py`) — every active, non-superseded epic under
      `plans/epics/*.md` must have a corresponding `plans/epics/html/<slug>.html` file, and it must not be older than
      the epic `.md` file's own `last_updated` (staleness = the HTML predates the epic doc's last real content
      change). Warn-only initially (mirrors `check_parent_epic_alignment.py`'s soft-launch pattern), `--strict` for a
      future hard flip once the corpus is caught up.
- [ ] [SCRIPT] P1. Wire the new check into `quality-gates.sh`'s PM-level gate sequence, in the same block as the
      existing `check_line_caps.sh`/`docspec` calls.
- [ ] [DOCS] P2. Update CLAUDE.md's "Plans — format + authoring discipline" section with a one-line pointer to the
      new epic-taxonomy codex doc + the HTML-artifact convention (condense, don't duplicate, per this file's own
      maintenance rules).

### Phase 6 — first full run

- [ ] [REVIEW] P1. Run `/plan-reconcile <slug>` once for every active, non-superseded epic post-Phase-3 (the 9-domain
      epics + the 5 untouched asset-group epics + `plan_hygiene_master` — ~22 total) — generate + publish each HTML
      ledger. Done when: every epic has a live artifact link.
- [ ] [DOCS] P2. Collect all ~22 artifact links into a single index (either a new section in
      `plans/epics/README.md` or a small standalone HTML index page alongside `plans/epics/html/`) and report the
      full list back to the operator.

## Progress Log

- **2026-08-18 (design research)**: general-purpose sub-agent surveyed the full epic corpus (29 files, 15,669
  lines), the current `/plan-reconcile` SKILL.md, all epic-structural QG scripts, and exact `parent_epic` coverage
  (836 docs, ~99.6% populated). Found the `regenerate_active_plan_inventory.py` orphan-check bug (filename-substring
  vs. frontmatter) described in Why. Operator resolved two open design forks: infrastructure_master split happens
  now in one pass (not deferred), UAC gets its own new epic (not folded into instruments_master). This plan authored
  from those findings + decisions.
