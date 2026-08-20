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
    /plans/epics/security_and_cross_cutting_master.md,
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
    /plans/epics/security_and_cross_cutting_master.md,
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
      every active epic. `unified-trading-pm@ca8851438a`.
- [x] [DOCS] P1. ✅ DONE 2026-08-18 — authored `/codex/11-project-management/epic-html-report-format.md`,
      generalizing the AO Provider Dispatch Ledger's section structure into a reusable spec (10 sections, several
      explicitly optional/omit-if-empty), plus a design-token approach that deliberately does NOT reuse one shared
      stylesheet across epics (each epic's report picks its own palette per `artifact-design`, to avoid the
      every-report-looks-the-same smell). `unified-trading-pm@ca8851438a`.
- [x] [DOCS] P2. ✅ DONE 2026-08-18 — fixed `mtds_mdps_master.md`'s title from "Data pipeline master coordination —
      2026-05-20" to "MTDS/MDPS Master — Market Data Pipeline Coordination". `unified-trading-pm@ca8851438a`.
- [x] [DOCS] P2. ✅ DONE 2026-08-19 — refreshed `plans/epics/README.md`'s epic-registry table: 23→22 rows, dropped
      the stale "Assigned VM" column (superseded by single-VM role-based dispatch), regenerated `Owns` descriptions
      from live `epics/*.md` frontmatter `title:`/`tier:` fields. The table's own `scripts this regeneration` todo
      (README.md's own line ~225) stays open — this was a manual refresh, not the automation.

### Phase 2 — zero/low-reference epic folds (≤2 referencing docs each, low blast radius)

- [x] [DOCS] P1. ✅ DONE 2026-08-18 (pending lead-session ship) — folded `trading_agent_master.md` (42 lines, 0
      references) into `execution_master.md` as a new "Folded-in epic: Trading Agent Master" subsection (owns
      line, repos, assigned-active-plans note, archived-plans pointer all carried over); `trading_agent_master.md`
      flipped `status: superseded` with a banner pointing to `execution_master.md`. 0 open todos existed in the
      source (verified via `grep -c "^\- \[ \]"` = 0), none lost. `unified-trading-pm@cf7489d077`.
- [x] [DOCS] P1. ✅ DONE 2026-08-18 (pending lead-session ship) — folded `dart_and_promote_master.md` (0
      references) and `global_ledger_pnl_attribution_master.md` (0 references) into `strategy_master.md` as two new
      "Folded-in epic:" subsections (full substance: owns, scope-inherited, UI verification contract / codex SSOTs
      / cross-epic handshakes / archived plans / VM notes / continuous-verification table, not just links); both
      source files flipped `status: superseded` with banners pointing to `strategy_master.md`. Both sources had 0
      open todos (verified), none lost. `unified-trading-pm@cf7489d077`.
- [x] [DOCS] P1. ✅ DONE 2026-08-18 (pending lead-session ship) — folded `escalation_and_disaster_recovery_master.md`
      (193 lines, 1 reference) into `observability_master.md` as a new "Folded-in epic: Escalation & Disaster
      Recovery Master" subsection (all 8 open todos preserved verbatim: 6 P1 escalation-pipeline-MVP + 2 P2
      deferred E2/E3 — confirmed via line-count diff, observability_master.md's open-todo count went 2→10);
      `escalation_and_disaster_recovery_master.md` flipped `status: superseded` with a banner. Found the 1
      referencing doc via `rg -l "^parent_epic: escalation_and_disaster_recovery_master" plans/active/
      plans/active/issues/` →
      `plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`; its `parent_epic:`
      frontmatter updated to `observability_master` in the same pass. `unified-trading-pm@cf7489d077`.

### Phase 3 — the big split: ci_master + uac_master carve-out, infrastructure_master rename

- [x] [SCRIPT] P0. ✅ DONE 2026-08-18 (pending lead-session ship) — content-classified all `parent_epic:
      infrastructure_master` docs into 3 buckets: **58 CI-bound**, **5 UAC-bound**, **234 remainder**
      (security/cross-cutting). Actual corpus count at Step 1 time was **297** (not 296 — 1 doc of real-time drift
      since the plan's research pass; the corpus is under heavy concurrent multi-agent edit). Classification used
      title/summary/tags topic-keyword scoring (weighted 3x over body-text scoring, to avoid false triggers from
      boilerplate workspace-process mentions like "ship via quickmerge" appearing incidentally in nearly every doc)
      plus manual read-based adjudication of every borderline/tied case — full per-doc reasoning and the explicit
      tie-break rules applied (Rule A-E) are in this entry's continuation below. **2 docs flagged AMBIGUOUS** (a
      genuine judgment call, not forced): `ao_ci_aws_to_ionos_migration_2026_08_18.md` (spans AO-VM +
      CI-escalation-runner-VM migration equally) and `repo_scripts_governance_audit_2026_06_18.md` (spans general
      script governance + the quickmerge carve-out definition) — both defaulted to `security_and_cross_cutting_master`
      per the "safe stays-where-it-was" rule, flagged here for human follow-up reclassification.
      `unified-trading-pm@13cd3e5a82..2e733b3303` (the reclassification + recovery batch range, see final
      Progress Log entry for the full 12-commit ship list).
- [x] [DATA] P0. ✅ DONE 2026-08-18 — extended `/codex/12-agent-workflow/epic-keyword-surface.yaml` with new
      `ci_master:` and `uac_master:` entries (keywords derived from the classification), and renamed the
      `infrastructure_master:` entry to `security_and_cross_cutting_master:` with a narrowed keyword list (added
      `ratchet`/`basedpyright` to make the QG-debt-vs-CI-pipeline boundary explicit). `check_parent_epic_alignment.py`
      run against the reclassified corpus: `ci_master` 58 docs / 4 WARN (6.9%), `uac_master` 5 docs / 2 WARN (40%,
      small-sample genuine dual-topic tension already reasoned through in the classification, not a keyword-surface
      defect), `security_and_cross_cutting_master` 235 docs / 52 WARN (22.1%) — at parity with the corpus-wide
      baseline (773 docs / 172 WARN = 22.3%), i.e. no NEW systemic mismatch introduced. `unified-trading-pm@<see
      Progress Log>`.
- [x] [SCRIPT] P0. ✅ DONE 2026-08-18 — created `plans/epics/ci_master.md` (`tier: L4`, `priority: P0`,
      `assigned_vm: NA`), populated with real P0-P3 "Assigned active plans" blocks (all 58 CI-bound docs, real
      titles/status/estimates) and a Scope/Current-state narrative summarizing the 7 recurring failure classes
      actually found in the corpus (self-hosted-runner capacity, promotion-pipeline livelock, workflow-template
      drift, release-tagging stalls, cross-repo gate blind spots, ship-script mechanism bugs, the 2 active
      build-out plans). 446 lines, well under the 2000-line epic cap. `unified-trading-pm@cf7489d077`.
- [x] [SCRIPT] P0. ✅ DONE 2026-08-18 — created `plans/epics/uac_master.md` (`tier: L1`, `priority: P1`,
      `assigned_vm: NA`), populated from the 5-doc UAC-bound bucket (all sourced from former `infrastructure_master`
      referrers — the `client_isolation_and_governance_master` UAC cross-reference had zero actual referrer docs of
      its own, see next todo). Small bucket by design, not omission — documented in the epic's own "Why this epic
      exists" section. `unified-trading-pm@cf7489d077` (epic file) / `unified-trading-pm@13cd3e5a82..2e733b3303` (the 419-doc
      parent_epic rewrite, see final Progress Log entry for the full commit list).
- [x] [SCRIPT] P0. ✅ DONE 2026-08-18 — `git mv plans/epics/infrastructure_master.md
      plans/epics/security_and_cross_cutting_master.md`; updated `name:`/`title:` frontmatter + added a rename
      banner; stripped the 6 CI-bound "Assigned active plans" entries that moved to `ci_master.md` (0 UAC-bound
      entries existed in the body list) from both the frontmatter `related_plans:` list and the body P1/P2 sections
      — verified via `grep` post-edit, zero duplication. Trimmed `client_isolation_and_governance_master.md`'s
      "🔴 canonical instrument_id — UAC-schema governance angle" P2 section to a pointer at `uac_master.md` (it had
      **0 actual referrer docs** of its own — "no new plan filed under this epic" per its own original text — so
      nothing needed re-parenting, only the narrative pointer needed updating) and its "UAC schema evolution"
      Extension-scope bullet similarly repointed. `unified-trading-pm@cf7489d077` (epic file) / `unified-trading-pm@13cd3e5a82..2e733b3303` (the 419-doc
      parent_epic rewrite, see final Progress Log entry for the full commit list).
- [x] [SCRIPT] P0. ✅ DONE 2026-08-18 — bulk-rewrote the `^parent_epic: infrastructure_master$` frontmatter LINE ONLY
      (verified regex-safe: exact full-line match, never a body-text substring sub) across all 297 Step-1 docs (58→
      `ci_master`, 5→`uac_master`, 234→`security_and_cross_cutting_master`) via a one-off Python script (safer +
      faster than 297 manual Edits, zero misses on the first pass). **Real-time drift caught by Step 6's recursive
      re-verify** (the plan's own specified Step 1 command, `rg -l ... plans/active/*.md plans/active/issues/*.md`,
      uses shell GLOBS that miss nested subdirectories — a real gap, not just corpus drift): found + reclassified 4
      more docs to `security_and_cross_cutting_master` — 1 new doc created mid-task by a concurrent session
      (`deployment_network_egress_ingress_observability_2026_08_18.md`) + 3 docs nested under
      `plans/active/issues/stash_audit_reports/` (a subdirectory the flat glob never reaches). Done-when confirmed:
      `rg -c "^parent_epic: infrastructure_master$" plans/active/ plans/active/issues/` → 0 (quoted in Progress Log).
      `unified-trading-pm@cf7489d077` (epic file) / `unified-trading-pm@13cd3e5a82..2e733b3303` (the 419-doc
      parent_epic rewrite, see final Progress Log entry for the full commit list).
- [x] [SCRIPT] P1. ✅ DONE 2026-08-18 — corpus-wide sweep for `infrastructure_master`. **Major additional finding not
      anticipated by this todo's original scope**: the actual live docspec gate (`check_frontmatter_schema.py`)
      ALSO validates `plans/audit/results/**/*.md` + `plans/audit/instructions/**/*.md` (118 more docs carrying
      `parent_epic: infrastructure_master`, entirely outside Step 1's stated `plans/active/` scope) — all 118
      reclassified to `security_and_cross_cutting_master` (none showed genuine CI/UAC topic signal; they're mostly
      historical 2026-05/06 one-shot audit results + per-AG data-pipeline reconciliation audits). Fixed every
      docspec-flagged dangling `related:`/`context_scope:`/`referenced_by:` path reference (13 docs) + the master
      `cursor-configs/CLAUDE.md` rules file (1 live SSOT pointer) + 16 codex SSOT docs with live "planned delta"/
      "SSOT:"/"tracked under" pointers + the `cross_cutting_may_23_SUPERSEDED_2026_05_21.md` epic's 3 dead prose
      links (path-only fix, historical narrative text left untouched). **NOT fully exhausted — flagged as a
      follow-up todo below**: a corpus-wide `rg -l "infrastructure_master" --glob '!plans/archive/**'` still returns
      ~780 hits, of which ~694 are `# Epic: infrastructure_master` script-lifecycle-marker header comments spread
      across `scripts/` + `tests/` (a same-scale-or-larger undertaking than this doc-reclassification pass, clearly
      out of this todo's original scope), plus a smaller residual of `plans/active/`/`plans/audit/` prose mentions
      (mostly historical Progress-Log-style narrative, lower actionability). See the new follow-up todos below.
      `unified-trading-pm@cf7489d077` (epic file) / `unified-trading-pm@13cd3e5a82..2e733b3303` (the 419-doc
      parent_epic rewrite, see final Progress Log entry for the full commit list).
- [x] [REVIEW] P0. ✅ DONE 2026-08-18 — ran `python3 scripts/plan-hygiene/check_frontmatter_schema.py` (the real
      docspec/`check_frontmatter_schema` gate `quality-gates.sh`'s Post-gates PM-level sequence calls) over the full
      live corpus post-rename. **Result, quoted verbatim**: `❌ check_frontmatter_schema: 1 doc(s) with frontmatter
      violations: plans/active/deployment_network_egress_ingress_observability_2026_08_18.md: locked_by: optional
      key absent — add present-but-empty / locked_since: optional key absent — add present-but-empty` — this ONE
      remaining violation is a pre-existing SOFT (optional-key) gap on a doc created by an unrelated concurrent
      session, NOT caused by this rename/split. **Zero new HARD violations** — confirmed by iterating: before the
      Step-7 dangling-reference fixes the gate reported 13 docs with `related`/`context_scope` HARD violations citing
      the dead `/plans/epics/infrastructure_master.md` path; after fixing them, only the 1 unrelated SOFT item
      remains. Done-when criterion met. `unified-trading-pm@cf7489d077` (epic file) / `unified-trading-pm@13cd3e5a82..2e733b3303` (the 419-doc
      parent_epic rewrite, see final Progress Log entry for the full commit list).
- [x] ✅ [DOCS] P2. Update `plans/epics/README.md`'s registry table for the Phase 3 changes (2 new epics, 1 renamed,
      folding in Phase 2's changes too if not already done). **DONE 2026-08-19** — completed in Phase 6's "final
      cross-epic sweep" (Progress Log: "README registry refreshed (23→22, dropped the stale 'Assigned VM' column)").
      Verified live: `plans/epics/README.md` rows 10/14/18 carry `uac_master`/`ci_master`/`security_and_cross_cutting_master`.
- [ ] [SCRIPT] P1. **NEW — follow-up finding, not in original Phase 3 scope.** Sweep the ~694 `# Epic:
      infrastructure_master` script-lifecycle-marker header comments across `scripts/` (per
      `/codex/06-coding-standards/script-homes.md`'s convention) + `tests/` and reclassify each to `ci_master` /
      `uac_master` / `security_and_cross_cutting_master` using the same content-based methodology as this plan's
      doc sweep (a script's OWN functional area, e.g. `scripts/cicd/*` and `scripts/self-hosted-runners/*` are
      strong `ci_master` candidates; most of `scripts/quality_gates/*`/`scripts/dev/*`/`scripts/plan-hygiene/*`/etc.
      are almost certainly `security_and_cross_cutting_master`, since script `# Epic:` headers track code ownership
      by domain, not doc topic). Scale note: this is comparable to or larger than this plan's own 297+118-doc sweep
      — size it as its own dispatch batch (or a dedicated sub-plan), not a quick tack-on. Verify via
      `rg -c "^# Epic: infrastructure_master$" scripts/ tests/` → must reach 0.
- [ ] [SCRIPT] P2. **NEW — follow-up finding.** Finish the residual `plans/active/`/`plans/audit/`/`plans/epics/`
      prose-mention sweep for `infrastructure_master` beyond the 13 docspec-flagged + 16 codex + 1 CLAUDE.md +
      1 SUPERSEDED-epic fixes already landed this pass — roughly 60-70 `plans/` files remain (mostly
      Progress-Log-style historical narrative describing past decisions, lower actionability than the codex/CLAUDE.md
      pointers already fixed, but not individually triaged). Also decide whether `plans/audit/instructions/
      infrastructure_master_audit_instructions.md`'s FILENAME itself should be renamed to match (a live,
      standing audit-instruction file whose name no longer matches its `parent_epic:`, deliberately NOT renamed
      this pass since a file rename has its own referrer-tracing implications).
- [ ] [SCRIPT] P2. **NEW — found during the ship, 2026-08-18.** 3 docs' `parent_epic: infrastructure_master`
      reclassification could NOT ship this pass, each for a distinct, pre-existing reason unrelated to this
      restructure's own content:
      1. `plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` — already 1092L (over the
         1000L hard cap) on origin BEFORE this pass touched it; a bare 1-line `parent_epic:` value substitution
         doesn't match any of `check_line_caps.sh`'s 4 existing narrow carve-outs (whitespace-only, small-marker-
         append, link-repoint, single-todo-flip — see the script's own comments) since none of them cover a bare
         frontmatter-VALUE substitution. Needs either a real split (95 todos, real content decision) or a 5th
         operator-ruled carve-out added to `check_line_caps.sh` before this one line can land.
      2. `plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md` — has a pre-existing
         dangling reference (a `codex/02-data` doc path with "manifest-writer-ssot" in the name, confirmed via
         `find` — no such doc exists
         anywhere in the corpus under any name) unrelated to this session's content; `check_reference_paths.py`
         blocks the whole staged commit on it. Needs the dangling ref repointed or removed (historical-narrative
         text left untouched, just the broken link) before the parent_epic fix can land.
      3. `plans/active/deployment_network_egress_ingress_observability_2026_08_18.md` — **RESOLVED, verified live
         2026-08-20**: `parent_epic:` now reads `security_and_cross_cutting_master` (fixed as part of Phase 6's
         "final cross-epic sweep" per the Progress Log). Items 1-2 below remain blocked, unchanged.
      Done-when: `rg -c "^parent_epic: infrastructure_master$" plans/active/ plans/audit/results/
      plans/audit/instructions/ plans/epics/ codex/` → 0 (currently 2 — items 1-2 above; item 3 cleared 2026-08-20.
      A live re-run also surfaces 5 more recently-created docs carrying `parent_epic: infrastructure_master` that
      postdate this plan's sweep — natural corpus drift, not this todo's original 3-item scope).

### Phase 4 — `/plan-reconcile` extension: epic scope + HTML artifact generation

- [x] [INFRA] P1. ✅ DONE 2026-08-18, pending lead-session ship — added a new "Epic-scoped runs" section to
      `cursor-configs/skills/plan-reconcile/SKILL.md` (after "Topic-scoped (sharded) runs", before "Modes"):
      argument-resolution order (`all`/no-arg → tranche literal → live `plans/epics/*.md` registry match → fail
      loudly listing both valid tranches and valid epic slugs), the `parent_epic`-frontmatter scope definition
      (`rg "^parent_epic: <slug>$"` across `plans/active/*.md` + `plans/active/issues/*.md`), and an explicit
      contrast with `regenerate_active_plan_inventory.py`'s broken filename-substring approach, citing this plan's
      own Why section. Bare `/plan-reconcile` keeps its unchanged `all` behavior; epic-scoped is documented as an
      additional entry point, not a replacement. `unified-trading-pm@13cd3e5a82` (SKILL.md landed in reclassification batch 1).
- [x] [INFRA] P1. ✅ DONE 2026-08-18, pending lead-session ship — same SKILL.md section documents the proactive
      `parent_epic`-validity check: Phase 0's existing `run_hygiene_sweep.sh` → `check_parent_epic_alignment.py` /
      `docspec.py` registry-typed HARD check already covers this at QG time; the new instruction is to surface it
      PROACTIVELY and, when epic-scoped, report only that epic's own children rather than the whole corpus, with a
      verify-before-trusting-green step (point at a doc with a deliberately-broken `parent_epic` value). No new code
      needed — this reuses the existing mechanical check, scoped and run earlier in the pipeline.
      `unified-trading-pm@13cd3e5a82` (SKILL.md landed in reclassification batch 1).
- [x] [INFRA] P1. ✅ DONE 2026-08-18, pending lead-session ship — built the HTML-generation phase: new
      "Phase 5.95 — HTML artifact generation" section in SKILL.md (which-epics-in-scope logic for epic- vs
      tranche/`all`-scoped runs, 7 concrete steps: gather data → load `artifact-design` → build HTML per the 10
      sections → write `plans/epics/html/<slug>.html` → publish via `Artifact` (`url` param on re-run to update the
      SAME artifact) → store the URL in a `## Report` body section → report the link in Phase 6). New helper
      `scripts/plan-hygiene/epic_report_data.py` (confirmed `count_open_tasks.py` has no epic-scoping CLI flag
      before writing it — only `--pm-root`/`--json`) replicates its exact dedup methodology (same
      `AGGREGATOR_MARKERS`, same open/done regexes) scoped to one epic's `parent_epic`-matched children via
      `plans/active/*.md` + `plans/active/issues/*.md`, plus verbatim `[OPERATOR]`/`BLOCKED-OPERATOR` open-item
      extraction; validates `--epic` against the live `plans/epics/*.md` registry (same set `docspec.py`'s
      `load_registries()` builds), failing loudly with the full valid-slug list on a miss. Verified against the
      real `mtds_mdps_master` epic — see this plan's Progress Log for the actual output.
      `unified-trading-pm@bd5d8acce9` (`scripts/plan-hygiene/epic_report_data.py`) /
      `unified-trading-pm@13cd3e5a82` (`cursor-configs/skills/plan-reconcile/SKILL.md`).
- [x] [DOCS] P2. ✅ DONE 2026-08-18, pending lead-session ship — updated SKILL.md's `*_SUMMARY.md`-ban line (end of
      Phase 5, the line that actually carries the ban text) with a clarifying note that Phase 5.95's HTML artifact
      is additive, not a substitute for the chat report, and doesn't conflict with the ban (ban targets ad hoc
      unpublished summaries; the HTML report is structured, explicitly requested, and published with a shareable
      link). Also added a reinforcing pointer in Phase 6 itself ("report") to include the Phase 5.95 link(s).
      `unified-trading-pm@13cd3e5a82` (SKILL.md landed in reclassification batch 1).

### Phase 5 — QG hardening for the new structure

- [x] [SCRIPT] P1. ✅ DONE 2026-08-18, pending lead-session ship — built
      `scripts/plan-hygiene/check_epic_html_freshness.py` (new file, sibling to `check_line_caps.sh`/
      `check_parent_epic_alignment.py`): for every active, non-superseded epic under `plans/epics/*.md` (skips
      `README.md` + `status: superseded`), WARNs if `plans/epics/html/<slug>.html` doesn't exist, and WARNs "stale —
      epic changed since last report" if it does but its embedded `<!-- generated: YYYY-MM-DDTHH:MM:SSZ -->` comment
      predates the epic doc's `last_updated` frontmatter. Reuses `scripts/docs/docspec.py`'s `parse_frontmatter()`
      (same dynamic-load pattern as `check_frontmatter_schema.py`) rather than a second hand-rolled parser. Warn-only
      soft-launch (mirrors `check_parent_epic_alignment.py`'s contract exactly): exit 0 always unless `--strict` AND
      at least one warning fired. Live-run against the pre-Phase-3/pre-Phase-6 corpus: 22 active non-superseded
      epics checked (2 fewer than the 24 counted at plan-authoring time — `dart_and_promote_master` and
      `trading_agent_master` flipped to `status: superseded` by Phase 2's concurrent agent mid-session, confirmed by
      re-reading their live frontmatter, not a script bug), all 22 WARN "no HTML report" (0 artifacts exist yet, as
      expected), exit 0. `--strict` run: same 22 warnings, exit 1 (confirms the flag flip works). Helper-function
      unit checks (date coercion across real-date/quoted-string/blank/invalid `last_updated` shapes, and
      fresh/stale/missing `<!-- generated: … -->` comment parsing) all passed against synthetic fixtures — the
      corpus itself has no HTML files yet to exercise the fresh/stale branches for real.
      `unified-trading-pm@bd5d8acce9` (code quickmerge).
- [x] [SCRIPT] P1. ✅ DONE 2026-08-18, pending lead-session ship — wired the new check into `scripts/quality-gates.sh`'s
      Post-gates PM-level sequence (the same block that runs `FRONTMATTER_SCHEMA_CHECKER`/`check_frontmatter_schema.py`
      i.e. the "docspec" gate this todo referred to — `check_line_caps.sh`/`check_parent_epic_alignment.py` are
      actually invoked from `run_hygiene_sweep.sh`, not `quality-gates.sh`, per a live grep; flagged below since the
      plan's own premise was slightly off). New `EPIC_HTML_FRESHNESS_CHECKER` block added directly after the
      Archive-safety-ratchet block, before the Conflict-marker gate — calls the script with `--quiet` (no `--strict`,
      matching the soft-launch contract) and never fails the gate, mirroring the frontmatter-auto-fixer block's
      "informational, exit 0 always" style. `bash -n scripts/quality-gates.sh` confirms no syntax breakage.
      `unified-trading-pm@bd5d8acce9` (code quickmerge).
- [ ] [DOCS] P2. Update CLAUDE.md's "Plans — format + authoring discipline" section with a one-line pointer to the
      new epic-taxonomy codex doc + the HTML-artifact convention (condense, don't duplicate, per this file's own
      maintenance rules). **NOT done this pass — see Progress Log finding**: `cursor-configs/CLAUDE.md` measured at
      40,942/40,960 B (18 B of headroom, already past the 95% WARN threshold `check_agent_rules_size_cap.py` enforces)
      at the time this todo was picked up — the minimal honest one-line addition (~155 B) cannot land without a real
      condensation pass elsewhere in the file first, and unilaterally trimming existing HARD-RULE prose in a
      shared, every-agent-depends-on file without operator sign-off was judged too risky for this todo's own P2
      scope. Left `[ ]` rather than force-flipped or silently dropped.

### Phase 6 — first full run

- [x] [REVIEW] P1. ✅ DONE 2026-08-19 — ran full `/plan-reconcile <slug>` for all 22 active, non-superseded epics
      (the 9-domain epics + the 5 untouched asset-group epics + `plan_hygiene_master`, `manifest_master`,
      `instruments_master`, `batch_live_symmetry_master`, `system_readiness_master`, `features_and_ml_master`,
      `uac_master`, `ci_master` — 22 total); every one has a live HTML artifact linked from its own `## Report`
      section (`ci_master`'s link was recovered separately this pass — the report existed and shipped 2026-08-18,
      but its `## Report` section link was missing until now). Full URL index below.
- [x] [DOCS] P2. ✅ DONE 2026-08-19 — collected all 22 artifact links (grepped directly from each shipped epic's own
      `## Report` section, not from memory) and reported the full list back to the operator in-chat, grouped by
      tier. `ci_master`'s link was missing from its own file (report shipped 2026-08-18 but the `## Report` section
      link never got added) — recovered from the published-artifacts list and added.

## Progress Log

- **2026-08-19 (Phase 6 + final cross-epic sweep, lead session)**: closed out Phase 6 — full `/plan-reconcile <slug>`
  ran for all 22 active epics (dispatched via background Agent-tool sub-agents in 5 batches, sonnet-5, DO-NOT-SHIP
  constraint; every finding independently ratified by the lead session — file-list cross-check against
  `git status`, SHA claims re-verified via `git merge-base --is-ancestor` against real local repo clones,
  cross-doc citations spot-checked — before shipping). All 22 shipped, all publish a live HTML report linked from
  their own `## Report` section. Caught and recovered a genuine content-loss incident mid-run:
  `agent_operating_framework_master`'s sub-agent's ~49 corrections across 26 files got swept into a stash by an
  overlapping ship's quarantine mechanism (this checkout's 70+-entry stash pile triggers a full-tree quarantine on
  every ship) — recovered in full via `git stash show --name-only "stash@{0}"` + targeted `git checkout` per file,
  cross-verified the recovered content didn't clobber an already-landed sibling fix. Also caught a real safety
  finding in `sports_master`'s pass (a ~144K-275K-object prod GCS delete todo marked "AUTHORIZED" that the doc's own
  Progress Log showed was never actually operator-confirmed — retagged `[OPERATOR]` before it could ship as
  false-authorized). README registry refreshed (23→22, dropped the stale "Assigned VM" column). Final cross-epic
  sweep (narrower than a full per-epic pass, per the operator's own guidance — "capture the high-level
  contradictions... it's easier") found + fixed: a fold-destination contradiction (README said
  `global_ledger_pnl_attribution_master` folded into `batch_live_symmetry_master`/`system_readiness_master`;
  `strategy_master.md`'s own "Folded-in epic" section says `strategy_master` — corrected to match the two
  authoritative primary sources), `infrastructure_master.md` left `status: active` with no SUPERSEDED-BY banner
  unlike its 4 sibling folds (fixed), 3 stale `epic-keyword-surface.yaml` entries for folded epics (removed), and 4
  docs still anchoring `parent_epic: infrastructure_master` (3 retargeted to `security_and_cross_cutting_master`, 1
  to `plan_hygiene_master`). One of those 4 (`cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`) could NOT
  ship — its parent_epic fix is a same-line comment addition (0 new lines), which passes the corpus-wide
  baseline-ratcheted `check_line_caps.sh`, but the file is 1092L (over the 1000L hard cap) and the STAGED-file
  pre-commit variant of the same check has no baseline tolerance — blocks unconditionally regardless of whether the
  violation predates this commit. Reverted that one file's edit and shipped the other 6; this parent_epic fix
  remains open, same class as the plan's own pre-existing tracked follow-up for this exact file (needs a real
  content split or a 5th narrow `check_line_caps.sh` carve-out — not something to force through same-line-comment
  tricks). Aggregate sanity check (corpus-wide `count_open_tasks.py` vs. summed per-epic `epic_report_data.py`
  figures) came back +78%/+92% over — expected DIRECTION (epic sums include aggregator/batch plans the corpus-wide
  count excludes by filename pattern) but flagged, not silently accepted, since the magnitude is large; root-causing
  the exact double-count source is out of this pass's scope. All ships independently gate-checked
  (`check_line_caps.sh`, `check_archive_candidates.sh`, `check_reference_paths.py`, `check_frontmatter_schema.py`,
  `check_ag_closeout_linkage.py`, YAML parse) before shipping — several ship-time-only gate failures were found and
  fixed live (a `resolved_by:`-required-but-empty frontmatter gap on 2 separate `status: resolved` flips triggering
  a genuine 6-step archival, an `[OPERATOR]`-ruling-evidence citation pushed >300 chars from its source doc by an
  edit's own added length, 2 missing-leading-slash reference paths, 2 missing `check_ag_closeout_linkage` links on
  new issue docs, and a stale-vs-live-`origin` dangling reference caused by a peer session archiving a doc between
  ship attempts). Epic-taxonomy restructure initiative is now COMPLETE — all 22 epics reconciled + reported, README
  regenerated, cross-epic contradictions resolved. Remaining open items, all pre-existing/tracked, none new: this
  plan's own batch13 parent_epic fix (above), the aggregate-sanity-check double-count root cause, and each epic's
  own individually-filed findings docs (operator-decision items, out of trust-mode scope by design).

- **2026-08-18 (design research)**: general-purpose sub-agent surveyed the full epic corpus (29 files, 15,669
  lines), the current `/plan-reconcile` SKILL.md, all epic-structural QG scripts, and exact `parent_epic` coverage
  (836 docs, ~99.6% populated). Found the `regenerate_active_plan_inventory.py` orphan-check bug (filename-substring
  vs. frontmatter) described in Why. Operator resolved two open design forks: infrastructure_master split happens
  now in one pass (not deferred), UAC gets its own new epic (not folded into instruments_master). This plan authored
  from those findings + decisions.
- **2026-08-18 (Phase 5, sub-agent, uncommitted)**: built `scripts/plan-hygiene/check_epic_html_freshness.py` +
  wired it into `scripts/quality-gates.sh`'s Post-gates PM-level sequence (next to the `FRONTMATTER_SCHEMA_CHECKER`
  "docspec" block). Correctness proof: live run against the corpus, exit 0, 22 epics checked, all WARN "no HTML
  report" (0 artifacts exist yet, expected); `--strict` run exits 1 on the same warnings; synthetic-fixture unit
  checks on the date-coercion + generated-comment-parsing helpers all passed. **Findings**: (1) the plan's own
  premise that `check_line_caps.sh`/`check_parent_epic_alignment.py` are called from `quality-gates.sh` doesn't hold
  — a live grep shows both are only invoked from `run_hygiene_sweep.sh`; the new check was wired next to
  `check_frontmatter_schema.py` (the actual "docspec" gate inside `quality-gates.sh`) instead, which is the closer
  match to the intended PM-level-gate vicinity. (2) `dart_and_promote_master.md` and `trading_agent_master.md` were
  observed flipping from `status: active` to `status: superseded` mid-session (a concurrent Phase-2 agent's live
  edit, confirmed by re-reading their frontmatter directly) — the script's live re-run correctly tracked the change
  (24→22 checked), no bug. (3) `cursor-configs/CLAUDE.md` measured at 40,942/40,960 B (18 B headroom, past the 95%
  WARN threshold) at the time Phase 5's third todo was picked up — the one-line epic-taxonomy pointer could not be
  added without a real condensation pass first; that todo was left `[ ]` rather than force-flipped or risked as an
  unreviewed trim of shared HARD-RULE prose. Flagging for the lead session / operator: CLAUDE.md needs a genuine
  size-diet pass soon regardless of this plan — 18 B of headroom is the same near-miss shape as the 2026-08-07
  incident the cap script's own docstring describes.
- **2026-08-18 (Phase 4, sub-agent, uncommitted)**: extended `cursor-configs/skills/plan-reconcile/SKILL.md` with
  two new sections — "Epic-scoped runs" (after "Topic-scoped (sharded) runs", before "Modes") and "Phase 5.95 — HTML
  artifact generation" (between the existing Phase 5.9 NO-MISS LEDGER and Phase 6 report) — plus a clarifying note on
  the existing `*_SUMMARY.md`-ban line (end of Phase 5) and a reinforcing pointer in Phase 6 to include the new
  artifact link(s). Also updated the skill's YAML `description`/Trigger list and its "Codex SSOTs" list. Confirmed
  before writing that `count_open_tasks.py` has no epic-scoping CLI flag (only `--pm-root`/`--json`), so built a new
  helper `scripts/plan-hygiene/epic_report_data.py` that replicates its exact dedup methodology (identical
  `AGGREGATOR_MARKERS`, identical dash-only open/done regexes — deliberately not the star-bullet-inclusive variant
  Phase 2's sweep uses, so the two scripts' numbers reconcile) scoped to one epic's `parent_epic`-matched children
  across `plans/active/*.md` + `plans/active/issues/*.md`, plus verbatim `[OPERATOR]`/`BLOCKED-OPERATOR` open-line
  extraction. The epic-slug registry check (`--epic <slug>` against every `plans/epics/*.md` stem except
  `README.md`) mirrors `docspec.py`'s `load_registries()` exactly, so it can never drift from what `parent_epic`
  frontmatter is actually validated against; an unknown slug exits 2 with the full sorted valid-slug list on stderr,
  never a silent tranche fallback. **Real verification** (not required for this pass, but run anyway per the task
  brief): `.venv/bin/python scripts/plan-hygiene/epic_report_data.py --epic mtds_mdps_master` (picked because it is
  NOT a Phase 2/3 fold target or rename target, so safe against concurrent-agent mid-edit collisions) returned 9
  plan children (1 aggregator-excluded: `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`) + 8
  issue children, ALL open=63/done=152, DEDUPED open=56/done=129, 0 `[OPERATOR]`-tagged open items — sane numbers
  matching a manual `rg -c` spot-check of a few of the listed child docs' checkbox counts. Also verified the
  unknown-slug failure path (`--epic not_a_real_epic` → exit 2, 28-slug registry list on stderr) and `--json` mode
  (valid JSON, `deduped_open`/`deduped_done` match the human-readable output). Fixed one bug found during this
  verification before shipping: the simple line-based frontmatter parser (shared design with `count_open_tasks.py`'s
  own parser — "simple scalars only") left a bare `>-`/`>` YAML block-scalar indicator as a doc's `title` when the
  real title used a multi-line folded block; added a fallback to the filename stem in that case rather than printing
  the bare indicator in the report. Left uncommitted per this session's instruction — lead session reviews the diff
  and ships (`scripts/plan-hygiene/epic_report_data.py`, `cursor-configs/skills/plan-reconcile/SKILL.md`, this
  plan's own Phase 4 checkboxes + this entry).
- **2026-08-18 (Phase 2, sub-agent, uncommitted)**: executed all 3 zero/low-reference epic folds. (1)
  `trading_agent_master.md` (0 refs, 42 lines) folded into `execution_master.md` as a new "Folded-in epic: Trading
  Agent Master" subsection. (2) `dart_and_promote_master.md` (0 refs, 141 lines) + `global_ledger_pnl_attribution_master.md`
  (0 refs, 242 lines) folded into `strategy_master.md` as two new "Folded-in epic:" subsections — full substance
  carried over (scope-inherited notes, UI verification contract, codex SSOT tables, cross-epic handshakes, archived
  plans, VM notes, continuous-verification table), not just a link; `strategy_master.md` grew 220→484 lines, still
  well under the 2000-line epic hard cap. (3) `escalation_and_disaster_recovery_master.md` (1 ref, 193 lines) folded
  into `observability_master.md` as a new "Folded-in epic: Escalation & Disaster Recovery Master" subsection — all 8
  open todos preserved verbatim (6 P1 escalation-pipeline-MVP + 2 P2 deferred E2/E3); `observability_master.md`'s
  own open-todo count went 2→10 (`grep -c "^\- \[ \]"`), confirming 0 lost. Found the escalation epic's 1 referrer
  via `rg -l "^parent_epic: escalation_and_disaster_recovery_master" plans/active/ plans/active/issues/` →
  exactly `plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md` (matched twice
  because `plans/active/` recursively covers `plans/active/issues/` too — same file, one hit); its `parent_epic:`
  frontmatter flipped to `observability_master` in the same pass. All 4 source epic files flipped `status:
  superseded` with a banner (same pattern as the 3 pre-existing `*_SUPERSEDED_*.md` files, referenced
  `manifest_evolution_SUPERSEDED_2026_05_21.md` as the format model) pointing at their fold target; none renamed or
  deleted, filenames unchanged (Phase 3's concurrent agent owns renames, on a disjoint file set —
  `infrastructure_master.md`/`client_isolation_and_governance_master.md`/`agent_operating_framework_master.md`/
  `orchestrator_master.md` were not touched). All 3 source epics that had 0 open todos before the fold (trading
  agent, DART/promote, global ledger) confirmed via `grep -c "^\- \[ \]"` = 0 pre-fold. **Verification**:
  `python3 scripts/plan-hygiene/check_frontmatter_schema.py` run both narrowly (the 7 touched epic files + the 1
  retagged issue doc, 8 files) and over the full live corpus (2123 docs) — zero frontmatter violations either way,
  exit 0 both times. `bash scripts/plan-hygiene/check_line_caps.sh` — 2 pre-existing violations within baseline
  (17), not a regression, exit 0; largest touched file is `strategy_master.md` at 484 lines, well inside the
  2000-line epic hard cap. Left uncommitted per this session's instruction — lead session reviews the diff and
  ships via `safe-doc-push.sh` (docs-only). Touched:
  `plans/epics/{execution_master,trading_agent_master,strategy_master,dart_and_promote_master,
  global_ledger_pnl_attribution_master,observability_master,escalation_and_disaster_recovery_master}.md`,
  `plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`, this plan's own Phase 2
  checkboxes + this entry.
- **2026-08-18 (Phase 3, sub-agent, uncommitted — highest blast-radius piece of this restructure, per explicit
  operator instruction NOT shipped by this session)**: executed the full CI/UAC carve-out + `infrastructure_master`
  rename. Full detail below; see Phase 3's own checkboxes above for the per-todo done-notes.

  **Classification methodology**: title/summary/tags topic-keyword scoring (3x-weighted) + manual read-based
  adjudication of every doc scoring ambiguously on both CI and UAC axes, or scoring weakly on one axis with a
  CI/UAC-flavored filename. Explicit tie-break rules applied where content was genuinely dual-topic: **Rule A** — a
  doc about the CI/CD delivery-pipeline MECHANISM itself (quickmerge, sit-gate, promotion, workflow templates,
  self-hosted runners, semver-agent, `detect_breaking_change.py`, Cloud Build/Cloud Run deploy verification — the
  last two per CLAUDE.md's own "CI verification after every push" section explicitly covering them) is CI-bound
  REGARDLESS of what upstream content triggered the gate to fire. **Rule B** — a doc about UAC's OWN schema/
  registry/invariant correctness (locking/versioning, `canonical_path_violations()`, OrderStatus SSOT,
  registry-completeness) is UAC-bound regardless of which downstream pipeline the drift affects. **Rule C** — QG
  STATIC-CHECK/ratchet-debt content (basedpyright ratchet, codex-freshness ratchet, the "no broad except" gate blind
  spot, NA-corpus ratchet) stays `security_and_cross_cutting_master` — it's the coding-standards-gate domain, not the
  delivery-pipeline-mechanism domain, even though the same `quality-gates.sh` script also runs in CI. **Rule D** —
  asset-group data content (DeFi/CeFi/TradFi/sports pipeline bugs, VM/backfill incidents) that merely mentions
  UAC/CI in passing stays `security_and_cross_cutting_master` (this restructure does not reassign asset-group-primary
  docs to their natural asset-group epic — out of scope, non-goal). **Rule E** — broad multi-topic
  audit/closeout/dispatch-batch aggregator docs stay `security_and_cross_cutting_master` (can't cleanly carve one
  domain out of an umbrella doc without breaking its own structure).

  **Final counts (Step 1 corpus, `plans/active/*.md` + `plans/active/issues/*.md`, glob-scoped per the plan's own
  Step 1 command)**: 297 docs total (296 expected, +1 real-time drift) → **58 CI-bound / 5 UAC-bound / 234
  remainder**, **2 AMBIGUOUS** (both defaulted to remainder, see Phase 3 checkbox 1 for names+reasons). Partition
  verified exact: 58+5+234 = 297, zero overlap, zero invalid entries (scripted `comm`-based sanity check).

  **`client_isolation_and_governance_master` UAC angle**: its 3 own referrer docs (`elysium_carveout_stubbed_
  strategy_service_2026_08_12`, `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11`,
  `elysium_sla_v4_support_period_and_stale_dates_2026_08_08` — all Elysium commercial/custody/SLA content) are
  NOT UAC-schema-governance docs and needed zero reclassification; the epic's own "🔴 canonical instrument_id"
  section was pure cross-reference narrative with 0 actual filed docs, trimmed to point at `uac_master.md`.

  **Real-time corpus drift** (this workspace is under heavy concurrent multi-agent edit — 6+ other files were
  already mid-edit by other sessions when this task started, confirmed via `git status` at task start: Phase 2's
  epic folds, Phase 4/5's SKILL.md + new-script work, `quality-gates.sh`'s new gate wiring): Step 6's recursive
  re-verify (`rg -c "^parent_epic: infrastructure_master$" plans/active/`, a directory walk — NOT the flat-glob form
  the plan's own Step 1 command specifies) caught 4 more docs the flat glob structurally cannot reach: 1 brand-new
  doc created mid-task (`deployment_network_egress_ingress_observability_2026_08_18.md`) + 3 docs nested under
  `plans/active/issues/stash_audit_reports/` (a subdirectory `plans/active/issues/*.md` never walks). All 4
  reclassified to `security_and_cross_cutting_master` (workspace-hygiene/VM-observability content, none CI/UAC).
  **This is a real gap in the plan's own Step 1 command, not just corpus drift — flagging for
  `/codex/12-agent-workflow/pre-task-plan-conflict-check.md` or a future plan-authoring note: `plans/active/issues/
  *.md` globs miss nested subdirectories (`stash_audit_reports/`, `vm_reap_lists/` both exist today) — any future
  corpus-wide `plans/active/issues/` sweep should use a recursive walk, not a flat glob.**

  **The audit-tree gap (the single biggest surprise this pass)**: Step 1 scoped classification to `plans/active/`
  only, per the plan's own literal text. The REAL live docspec gate (`check_frontmatter_schema.py`'s `DOC_TREES`)
  additionally validates `plans/audit/results/**/*.md` + `plans/audit/instructions/**/*.md` — 118 more docs carried
  `parent_epic: infrastructure_master` and would have newly HARD-failed the gate at Step 6 if left unfixed. Scored
  + spot-checked all 118: zero showed genuine CI/UAC topic signal (mostly 2026-05/06-era one-shot audit results —
  `infrastructure_master_audit_2026_06_01.md` + its own `_audit_instructions.md`, general completion audits — plus
  per-AG `data_pipeline_reconciliation_*` results where "UAC"/"quickmerge" mentions were incidental, not the
  doc's subject). All 118 → `security_and_cross_cutting_master`.

  **Step 6 verification, quoted verbatim**:
  ```
  $ rg -c "^parent_epic: infrastructure_master$" plans/active/ plans/active/issues/
  (0 matches)
  $ python3 scripts/plan-hygiene/check_frontmatter_schema.py
  ❌ check_frontmatter_schema: 1 doc(s) with frontmatter violations:
    plans/active/deployment_network_egress_ingress_observability_2026_08_18.md:
      - locked_by: optional key absent — add present-but-empty
      - locked_since: optional key absent — add present-but-empty
  ```
  The 1 remaining item is a pre-existing SOFT gap on an unrelated concurrent session's brand-new doc — confirmed by
  checking its creation was untouched by this pass. Before the Step-7 dangling-reference fixes, this same command
  reported **13 docs** with HARD `related`/`context_scope`/`referenced_by` violations citing the now-dead
  `/plans/epics/infrastructure_master.md` path (full list: `/codex/02-data/deployment-ui-drilldown-depth-audit.md`,
  `/codex/06-coding-standards/adr-qg-offload-self-hosted-runners-2026-06-02.md`,
  `plans/active/data_pipeline_check_mdps_features_2026_07_20.md`,
  `plans/active/defi_compute_gcp_migration_2026_08_08.md`(+`_finalize`),
  `plans/active/deployment_network_egress_ingress_observability_2026_08_18.md`(unrelated SOFT, see above),
  `plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md` (this plan's own `related:`/
  `context_scope:`), `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md`(+`_2026_08_18`),
  `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`,
  `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`,
  `plans/audit/instructions/data_pipeline_e2e_check_audit_instructions.md`,
  `plans/epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md`) — all fixed, gate re-run clean.

  **`check_parent_epic_alignment.py` calibration check** (Step 2's own "done when" criterion): `ci_master` 58 docs /
  4 WARN = 6.9% mismatch (well below corpus baseline); `uac_master` 5 docs / 2 WARN = 40% (small-sample, both WARNs
  are genuine dual-topic tension already reasoned through by hand during classification — `canonical_path_oracle_
  blind_to_filename_stem` scores top=`mtds_mdps_master` because its evidence is heavily MTDS/manifest-path-shaped
  even though its SUBJECT is the UAC oracle; `uac_kamino_venue_reachability_cascade_regression` scores
  top=`defi_master` for the analogous reason); `security_and_cross_cutting_master` 235 docs / 52 WARN = 22.1%,
  matching the corpus-wide baseline (773 docs / 172 WARN = 22.3%) almost exactly — **no new systemic mismatch signal
  from this pass's classification.**

  **Corpus-wide `infrastructure_master` sweep (Step 7)** — fixed: the 13 docspec-flagged dangling references above;
  `cursor-configs/CLAUDE.md`'s one live SSOT pointer (§ "Working on DATA / manifest / pipeline?"); 16 codex SSOT docs
  with live "planned delta:"/"SSOT:"/"tracked under" pointers (`/codex/11-project-management/README.md`,
  `/codex/11-project-management/codex-audit-playbook.md`, `/codex/03-observability/data-feed-sla-registry.md`,
  `/codex/06-coding-standards/quality-gates.md`, `/codex/06-coding-standards/testing.md`,
  `/codex/04-architecture/prediction-batch-live.md`, `/codex/04-architecture/tradfi-batch-live.md`,
  `/codex/04-architecture/sports-batch-live.md`, `/codex/04-architecture/cefi-batch-live.md`,
  `/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/defi-venue-protocol-catalogue.md`,
  `/codex/05-infrastructure/synthetic-data-benchmarking.md`, `/codex/05-infrastructure/deployment-and-qg-strategy.md`,
  `/codex/05-infrastructure/cloud-agnostic-build-lineage.md`, `/codex/05-infrastructure/cloud-agnostic-script-pattern.md`,
  `/codex/05-infrastructure/launcher-script-ssot.md`); `plans/epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md`'s
  3 dead markdown-link TARGETS (historical descriptive TEXT deliberately left untouched — only broken link paths
  fixed, per the "legitimate historical, don't rewrite the record" distinction). Explicitly LEFT AS legitimate
  historical (not stale): `plans/archive/**` (960 hits, excluded by design from the live gate, operator decision
  2026-07-04 per `check_frontmatter_schema.py`'s own docstring); `ikenna_orchestrator/pings/*.md` +
  `dispatched_prompts_*` (dated session logs); `/codex/05-infrastructure/pubsub-topic-inventory.md`'s dated
  "Executed: 2026-05-26" record; `orchestrator_vm_registry.yaml` (auto-generated, "DO NOT edit manually" per its own
  header, + the whole epic-VM-ownership model it encodes is independently SUPERSEDED per `plans/epics/README.md`'s
  own banner); this plan's own Why/Design-summary/Todos narrative prose (correctly describes the before-state).

  **NOT completed this pass — 2 new follow-up todos added to Phase 3** (too large for inline fix, per this
  workspace's own "too big for a line → todo" rule): (1) ~694 `# Epic: infrastructure_master` script-lifecycle-marker
  header comments across `scripts/`+`tests/` (`/codex/06-coding-standards/script-homes.md` convention) — confirmed
  via `rg -c "^# Epic: infrastructure_master$" scripts/ tests/` = 694 files, spread near-uniformly across
  `scripts/quality_gates` (103) / `scripts/dev` (76) / `scripts/cicd` (47) / `scripts/plan-hygiene` (38) /
  `scripts/quality-gates-base/tests` (36) / `scripts/validation` (30) / `scripts/orchestrator` (30) / and a dozen
  more subdirs — this is comparable-or-larger in scope to this pass's own 297+118-doc sweep and was judged clearly
  out of this todo's original bounds; (2) a residual ~60-70 `plans/`-tree prose-mention tail (mostly historical
  Progress-Log narrative in `plans/active/`/`plans/audit/results/`/`plans/epics/*` files not individually
  triaged), plus the open question of whether `plans/audit/instructions/infrastructure_master_audit_instructions.md`
  should itself be renamed (its `parent_epic:` was fixed to `security_and_cross_cutting_master`, but the FILENAME
  still says `infrastructure_master`).

  **Files created**: `plans/epics/ci_master.md` (446 lines), `plans/epics/uac_master.md` (161 lines).
  **Files renamed**: `plans/epics/infrastructure_master.md` → `plans/epics/security_and_cross_cutting_master.md`
  (via `git mv`, content preserved, frontmatter + banner + trimmed sections updated).
  **Files with `parent_epic:` frontmatter rewritten**: 297+4+118 = 419 docs (58 → `ci_master`, 5 → `uac_master`, 356
  → `security_and_cross_cutting_master`).
  **Other files edited**: `/codex/12-agent-workflow/epic-keyword-surface.yaml` (renamed + 2 new entries),
  `plans/epics/client_isolation_and_governance_master.md` (UAC section trim, 2 edits),
  `/codex/02-data/lst-exchange-rate-surfaces.md` (1 stray non-schema-governed `parent_epic:` field, fixed for
  consistency though not gate-enforced), `cursor-configs/CLAUDE.md` (1 line), 16 codex SSOT docs (listed above),
  this plan's own `related:`/`context_scope:` (2 entries) + Phase 3 checkboxes + this entry.
  **DELIBERATELY UNCOMMITTED** per this session's explicit brief — highest blast-radius piece of the whole
  restructure (touches ~420 live documents' `parent_epic` frontmatter workspace-wide); lead session reviews the full
  diff (`git status`/`git diff`) before shipping via `safe-doc-push.sh` (docs-only, no code touched).

- **2026-08-18 (lead-session review + ship attempts) — real findings, not fabricated pass claims.** Independently
  re-verified all 4 phases before shipping (never trusted an agent's self-report alone): fixed a regression Phase
  3's own edit introduced — its stale-reference sweep replaced a short `infrastructure_master.md` pointer in
  `cursor-configs/CLAUDE.md` with a longer annotated one, pushing the file from 40,942 to 41,006 bytes, **46 bytes
  over the hard-enforced 40,960-byte (40KB) cap**; trimmed the added parenthetical back out (now 40,956 bytes — only
  4 bytes of margin, a real size-diet pass is still owed independent of this plan, see Phase 5's own finding on the
  same file). Fixed 2 E501 line-length violations Phase 4's `epic_report_data.py` shipped with. Fixed 3 genuinely
  broken inline links `quality-gates.sh`'s `check_doc_body_links` caught (this plan doc's own brace-expansion
  shorthand parsing as invalid paths; 2 stale `infrastructure_master.md` links in
  `plans/audit/results/archive/_AUDIT_2026_05_07_dependency_graph.md` and
  `plans/epics/manifest_migration_SUPERSEDED_2026_05_21.md`, both outside Phase 3's own swept scope). Found and
  removed a `|| true` bypass Phase 5's own `quality-gates.sh` wiring added around the new freshness checker — this
  workspace's QG has a dedicated banned-pattern check for exactly that shape (`|| true` masks a real script crash,
  not just an intentional non-strict exit); redundant anyway since the checker already exits 0 on its own in
  non-strict mode. `quality-gates.sh --no-fix` for `unified-trading-pm` itself (the 4 code files: the two new Python
  scripts, the `quality-gates.sh` edit, `epic-keyword-surface.yaml`) is GREEN — confirmed via `.qg_last_passed_sha ==
  HEAD`, not exit-code-alone (a prior run in this same session showed exit 0 while the real gate had failed further
  up the log — CLAIM ≤ MEASUREMENT applies to reading QG output too, not just to writing it).

  **A real bug in my OWN ship tooling, found before it did damage — worth recording as its own lesson.** Building
  the `--files` list for `safe-doc-push.sh` via `git status --short | awk '{print $2}'` silently mishandles a `git
  mv` rename line — `git status --short`'s rename format is `RM <old> -> <new>`, and `awk '{print $2}'` grabs field
  2, which is the OLD path, not the new one after `->`. The first ship attempt (456 files) consequently NEVER
  included `plans/epics/security_and_cross_cutting_master.md` in `--files`, even though `git status` showed the
  rename as dirty — so inside `safe-doc-push.sh`'s isolated-worktree build (which only materializes named `--files`,
  not the ambient working tree), the renamed file genuinely didn't exist, producing a wall of real-looking but
  root-cause-misleading `DANGLING`/`does not resolve to a real file` errors against every codex doc that correctly
  cited the NEW name. Diagnosed by directly comparing `git status --short`'s raw rename line against what actually
  landed in the constructed file list — the fix is a one-line `grep -v` of the stale old-path entry + appending the
  correct new path. **Any future large multi-file ship built by parsing `git status --short` needs to special-case
  `R`/`RM`/`RA`-prefixed lines** (take the post-`->` path, not field 2) — a plain `awk '{print $2}'` is silently
  wrong for exactly this case and gives no error, only confusing downstream symptoms.

  Re-shipped with the corrected file list (`plans/epics/security_and_cross_cutting_master.md` swapped in for the
  stale `infrastructure_master.md` entry) — see this same Progress Log's next entry (or `git log` on this repo) for
  the outcome, since that ship was still in flight when this entry was written (context budget forced a checkpoint
  mid-ship, per this session's `/pre-compact` ritual — the next session/reader should check `git status` and `git
  log -3` on `unified-trading-pm` FIRST, before assuming anything below this line reflects final state).

- **2026-08-18 (resumed session, lead-session ship — LANDED, 12 commits).** Picked up exactly where the prior
  session's `/pre-compact` checkpoint left off. Operator redirected the shipping strategy mid-flight: after 2 more
  monolithic-batch failures (a false-positive-turned-real content collision on
  `plans/active/strategy_service_centralization_fixes_2026_08_16.md` — adjacent-line adjacency, not a real
  disagreement, resolved by conflict-marker surgery; then a genuine `check_frontmatter_schema` wall of 28
  `parent_epic 'X' not an epic slug` failures caused by `ci_master.md`/`uac_master.md`/
  `security_and_cross_cutting_master.md` not yet being present in that batch's isolated worktree), the operator
  asked: _"i though we were just gonna ship the plans and docs which werent conflicting with remote first, then
  ship the others in batches of maybe 50 at a time."_ Switched strategy: (1) ship the 13 `plans/epics/*.md` files
  ALONE first (`unified-trading-pm@cf7489d077`) so every later batch's `parent_epic` value resolves against a live
  registry; (2) split the remaining 446 reclassification docs into ~50-file batches, shipped sequentially with a
  Monitor watchdog per batch rather than one 458-file attempt.

  **Full commit list (12, in landing order)**: `cf7489d077` (epic registry: rename + 2 new epics + Phase 2 folds),
  `13cd3e5a82` / `e64b0649ce` / `bcfbcab010` / `0257b29e93` / `7d734bf07e` / `6b3f1affa9` / `34721c3136`
  (reclassification batches 1-7 of 9), `ea81f66d5f` / `a4bd0e57e2` / `2e733b3303` (recovery batches 1-3, see
  below), `bd5d8acce9` (code quickmerge: `check_epic_html_freshness.py`, `epic_report_data.py`,
  `quality-gates.sh`'s wiring — `codex/12-agent-workflow/epic-keyword-surface.yaml` had already landed inside
  `13cd3e5a82` since it's a doc, not code, and was swept in by the batch-builder's blanket dirty-file grep).

  **Real findings from this pass, not fabricated pass claims:**

  1. **The epic-registry-first ordering is load-bearing, not cosmetic.** `check_frontmatter_schema.py`'s
     `parent_epic` validation resolves against whatever `plans/epics/*.md` files exist in THAT batch's isolated
     worktree — not the ambient corpus. A batch of reclassified docs shipped before the epic files themselves land
     genuinely fails "not an epic slug," every time, for every doc pointing at a new slug. This is now the
     documented required order for any future epic-rename-plus-reclassification ship.

  2. **A large-scale "your uncommitted edit is GONE" scare was mostly a false alarm, one real recovery needed.**
     Multiple batches reported dozens of unrelated `plans/audit/results/*.md` files and `scripts/quality-gates.sh`
     as "reverted during the reconcile." Root cause: `safe-doc-push.sh`'s isolated-worktree mode commits from a
     PRIVATE index and does NOT auto-advance the local branch's HEAD — so `git diff HEAD` against a stale local
     HEAD (many commits behind origin) looks identical to a genuine revert. A plain `git pull --rebase --autostash`
     resolved the vast majority of these instantly (dirty count 147→5) by catching the local branch up; a fast
     `git checkout "stash@{0}" -- scripts/quality-gates.sh` recovered the one genuinely-reverted file (verified via
     `git diff HEAD "stash@{0}" -- <path>` showing a pure clean addition before trusting the stash content).
     **Lesson for the next large multi-batch ship**: run `git pull --rebase --autostash` between batches, not just
     rely on each batch's own internal reconcile — it resolves the "GONE" false-positive class before it ever needs
     investigating.

  3. **One genuine, repeatable data-loss class DID occur**: 145 legitimately-reclassified docs (mostly the 118
     audit-tree docs from Phase 3's own additional-scope finding) had their `parent_epic:` fix silently reverted to
     `infrastructure_master` by an EARLIER batch's autostash-pop colliding with the docs' own dirty state (real
     content collision, not a stale-HEAD illusion — confirmed via `git show HEAD:<path> | grep parent_epic`
     showing the stale value on the ACTUAL current HEAD, not just a local diff artifact). Recovered 142 of 145 by
     scripting a per-file stash search (`git show "stash@{N}:<path>"` across the 11 most recent autostash entries,
     first non-`infrastructure_master` value wins) + a targeted `sed` fix, then re-shipped in 3 more ~50-file
     batches (`ea81f66d5f`/`a4bd0e57e2`/`2e733b3303`). The remaining 3: `deployment_network_egress_...` (the
     already-known excluded live-WIP file, correctly never touched) and 2 brand-new issue docs
     (`execution_service_pydantic_extra_forbidden_blocks_gcs_fix_2026_08_18.md`,
     `client_reporting_api_invoice_test_failures_block_gcs_fix_2026_08_18.md`) created by another concurrent
     session mid-ship and never covered by any stash — classified fresh (both clearly `security_and_cross_cutting_master`,
     general cross-cutting bug-fix content, no CI/UAC signal) and shipped in the same recovery batch.

  4. **2 more pre-existing-debt files surfaced and were correctly excluded, not force-shipped**:
     `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` (already over the 1000L hard cap on origin,
     unrelated to this pass; none of `check_line_caps.sh`'s 4 narrow carve-outs cover a bare frontmatter-value
     substitution) and `mega_audit_phase_a_issues_human_readable_2026_05_20.md` (a pre-existing dangling reference
     to a codex doc that was confirmed, via `find`, to not exist anywhere in the corpus under any name). Both left
     with their LOCAL working-tree copy carrying the correct `parent_epic` value but unshipped — tracked as a new
     Phase-3 follow-up todo (3 items) rather than force-bypassed or silently dropped.

  5. **Verification, not assumption, closed this out**: final corpus-wide check —
     `rg -l "^parent_epic: infrastructure_master$" plans/active/ plans/audit/results/ plans/audit/instructions/
     plans/epics/ codex/` → exactly 1 hit (`deployment_network_egress_ingress_observability_2026_08_18.md`, the
     one deliberate exclusion) — confirms all 417 of 419 originally-planned reclassifications landed (2 permanently
     rerouted to the new Phase-3 follow-up todo above, not silently lost). `.qg_last_passed_sha == HEAD` was NOT
     re-checked after this specific doc-only ship since `safe-doc-push.sh` runs prek, not full `quality-gates.sh`
     — the code files' own separate `quality-gates.sh --no-fix` run (before the `bd5d8acce9` quickmerge) was
     verified directly by grepping for `❌`/`FAILED` rather than trusting its exit code, which the harness reported
     as 0 while a 2026-08-10-incident-class exit-code lie was independently ruled out by reading the actual
     output — the only 2 `❌` lines found (`VERSION_SPLIT`, `VESTIGIAL_SCALAR_DRIFT`) are fleet-wide release-tag
     manifest drift checks unrelated to any file this session touched, confirmed pre-existing corpus-wide, not a
     regression this pass introduced.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
