---
doc_type: issue
title:
  generate_na_doc_tranche_inventory.py's ao/ci/infra membership branch cross-contaminates tranches via bare closeout-doc
  citation (related:/footnote links treated as ownership) — same root-cause family as the sibling
  generate_ag_closeout_audit_candidates.py bug, distinct manifestation
summary: >-
  Discovered running `/na-eligibility-audit infra` (autonomous, 2026-07-29, na_eligibility_auditor scheduled worker,
  slot 7) Phase 0 inventory step. `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py --tranche infra --json`
  returned 64 docs; an independent direct-frontmatter cross-check (same technique used to catch the sibling `ci`
  zero-candidate bug the same day) found 5 of the 64 are false positives and 1 genuine infra doc is a false negative.
  Root cause: the script's `else` branch for `ao`/`ci`/`infra` tranche membership still implements the RETIRED
  2026-07-25→27 citation-grep mechanism (`CITE_RE` basename matching inside each tranche's own
  `{tranche}_consolidated_closeout_2026_07_25.md` body) instead of testing `asset_group` directly — the same stale
  mechanism
  `plans/archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`
  already flagged for the sibling script earlier the same day, but manifesting differently here: instead of a hard zero,
  ordinary `related:`-frontmatter links and footnote citations between the tranches' own coordinator docs get treated as
  membership claims, so coordinator docs leak INTO other tranches and lose their OWN tranche tag. A second, independent
  logic bug in the same script's `cross-cutting` branch (a `peer_cited` self-veto that is a tautological no-op)
  compounds this — a cross-cutting doc that qualifies for `cross-cutting` only via citation can never actually receive
  that tag. Since this ONE script computes membership for all 9 `/ag-closeout-audit`+`/na-eligibility-audit` tranches
  simultaneously, the same failure class likely also corrupts `ao`/`ci`/`cross-cutting` tranche runs, not just `infra` —
  confirmed directly for `ao` and `cross-cutting` while tracing this session's 6 anomalous docs, though a full 9-tranche
  sweep was not run (out of this session's scope).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    na-eligibility-audit,
    ag-closeout-audit,
    plan-hygiene,
    script-bug,
    asset-group,
    tranche-membership,
    silent-misclassification,
  ]
related:
  [
    /plans/archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/asset_group_ao_ci_infra_schema_expansion_2026_07_27.md,
  ]
created: "2026-07-29"
author: unknown
last_updated: "2026-08-17"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: none
assigned_role: infra
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
locked_by:
resolved_by:
depends_on: []
source: >-
  `/na-eligibility-audit infra` run 2026-07-29 (na_eligibility_auditor scheduled worker, slot 7) — Phase 0 inventory
  verification step, cross-checked against a direct frontmatter sweep after the sibling `ci`-tranche issue doc (filed
  earlier the same day) raised doubt about the whole `non_ag_cited`/citation-grep mechanism's soundness.
context_scope:
  [
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    unified-trading-pm/cursor-configs/skills/na-eligibility-audit/SKILL.md,
    unified-trading-pm/cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md,
    unified-trading-pm/scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    unified-trading-pm/scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# `generate_na_doc_tranche_inventory.py` cross-contaminates ao/ci/infra tranches via bare closeout-doc citation

## What was found

Running the Phase-0 pre-filter for the `infra` tranche audit:

```
python3 scripts/plan-hygiene/generate_na_doc_tranche_inventory.py --tranche infra --json
```

returned 64 docs. Because the sibling issue doc filed earlier the same day
(`generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`) had just
proven the retired citation-based ao/ci/infra membership mechanism unsound in a DIFFERENT script, this run independently
cross-checked the 64-doc output against a direct frontmatter test (`assigned_vm: NA` + `status` ∈ `{active, open}` +
`asset_group` literally containing `infrastructure`/`meta`/`ao`/`ci`) instead of trusting the script's tranche
assignment at face value. The two disagree on 6 docs.

### False positives (5 of 64) — docs that do NOT belong in `infra`, included anyway

Each is merely name-dropped inside `infra_consolidated_closeout_2026_07_25.md`'s own `related:` frontmatter list or
narrative prose — the `CITE_RE` regex (`[a-z0-9_]+_20\d\d_\d\d_\d\d(?:_finalize)?\.md`) matches ANY basename-shaped
citation, including a plain reference link, and the script treats that as a membership claim:

| Doc                                                 | Its real `asset_group`                                      | Why it leaked into `infra`                                                                                                                                                                         |
| --------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ag_closeout_audit_rollout_2026_07_25.md`           | `[cefi, defi, tradfi, prediction, sports, cross-cutting]`   | Markdown-linked at `infra_consolidated_closeout_2026_07_25.md:122` ("the meta-plan driving...")                                                                                                    |
| `ao_consolidated_closeout_2026_07_25.md`            | `[ao]` — **ao's own coordinator doc**                       | Cited in `infra_consolidated_closeout_2026_07_25.md`'s `related:` (line 26) + prose (line 195); script assigns it ONLY `infra`, never `ao` — the script never tests `"ao" in asset_group` anywhere |
| `cross_cutting_consolidated_closeout_2026_07_25.md` | `[cross-cutting]` — **cross-cutting's own coordinator doc** | Cited in `infra_consolidated_closeout_2026_07_25.md`'s `related:` (line 25); script assigns it `['ao', 'infra']`, dropping `cross-cutting` entirely (see logic bug below)                          |
| `june_2026_vintage_audit_findings_2026_07_27.md`    | `[cross-cutting]`                                           | Footnote-cited twice in `infra_consolidated_closeout_2026_07_25.md` prose (lines 102, 149); same cross-cutting-dropped bug                                                                         |
| `tradfi_consolidated_closeout_2026_07_18.md`        | `[tradfi]` (correctly kept)                                 | ADDITIONALLY tagged `infra` from a prose citation at `infra_consolidated_closeout_2026_07_25.md:235`                                                                                               |

### False negative (1 doc) — infra's OWN coordinator doc excluded from `infra`

`infra_consolidated_closeout_2026_07_25.md` itself — `asset_group: [infrastructure]`, and its own frontmatter literally
states "This is the `infra` tranche's OWN top-level consolidated-closeout/coordinator doc." The script assigns it
tranche `['ao']` ONLY, because `ao_consolidated_closeout_2026_07_25.md`'s `related:` list (line 29) cites it — a
tranche's own hub doc excluded from its own tranche by the exact same over-broad citation match.

### A second, independent logic bug: `peer_cited` self-veto makes `cross-cutting` unreachable via citation

Tracing why `cross_cutting_consolidated_closeout_2026_07_25.md` and `june_2026_vintage_audit_findings_2026_07_27.md`
both lost their real `cross-cutting` tag surfaced a second bug, distinct from the citation-mechanism staleness above:

```python
non_ag_all_cited = (
    non_ag_cited.get("ao", set()) | non_ag_cited.get("ci", set()) | non_ag_cited.get("infra", set())
)
if "cross-cutting" in asset_group and (parent_epic in DATA_EPICS or basename in non_ag_all_cited):
    if basename not in peer_cited:
        tranches.append("cross-cutting")
```

`peer_cited` (built earlier via `for s in non_ag_cited.values(): peer_cited |= s`) is computed from the exact same three
sets as `non_ag_all_cited` — they are IDENTICAL. So whenever the outer `if`'s citation-based eligibility test
(`basename in non_ag_all_cited`) is satisfied, the inner `if basename not in peer_cited` is a **tautological False** —
this code path can never actually append `"cross-cutting"`. A doc only receives `cross-cutting` when
`parent_epic in DATA_EPICS` is what qualified it (the other half of the `or`); any doc that qualifies purely by being
cited in an ao/ci/infra closeout doc silently loses its real cross-cutting identity and falls through to the
unconditional final loop, which then hands it whichever of ao/ci/infra also happens to cite it — confirmed live on both
docs in the table above.

## Impact

Same class of silent-misclassification risk the sibling issue describes, but broader in one sense: this script computes
membership for **all 9** tranches (`generate_na_doc_tranche_inventory.py --tranche all`) from this same
`non_ag_cited`/`peer_cited` machinery in one pass, so the failure is not confined to `infra`. This session confirmed
concrete cross-contamination into `ao` and `cross-cutting` while tracing just these 6 anomalous docs (not a targeted
search) — a dedicated sweep of the `ao`/`ci`/`cross-cutting` tranches would likely turn up more of the same pattern.
Left uncorrected, a `/na-eligibility-audit` run trusting this script's tranche assignment at face value would spend
Phase 1 classification effort on docs that don't belong to the tranche (wasted sub-agent reads) while silently skipping
the tranche's own genuine coordinator docs (a real audit-coverage gap, not just wasted effort) — worse than the sibling
script's hard-zero failure mode because it does not even look obviously wrong (64 docs returned, not 0). This run was
NOT blocked: the 64-doc population was corrected to 60 (64 − 5 false positives + 1 false negative) via the direct
frontmatter cross-check before Phase 1 classification proceeded.

## Fix direction (not implemented — read-only audit worker, out of dispatch scope)

Same direction as the sibling issue, applied to this script: replace the `non_ag_cited`/`_closeout_paths()`/`CITE_RE`
citation-membership mechanism for `ao`/`ci`/`infra` with a direct enum test — `"ao" in asset_group`,
`"ci" in asset_group`, `"infrastructure" in asset_group or "meta" in asset_group` (retaining the `meta`-tagged
default-fold to `infra` only as the genuine last-resort for docs with no more specific tag) — matching the PRIMARY
membership signal `asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`'s corpus-wide retag already established.
Separately, delete or fix the tautological `peer_cited` self-veto in the `cross-cutting` branch (it should not reference
the same union as the outer `non_ag_all_cited` eligibility test — or the inner veto should simply be removed once the
outer citation signal is dropped per the primary fix). Given `generate_ag_closeout_audit_candidates.py` duplicates the
same `_cited_basenames`/`_closeout_paths`/`CITE_RE`/`NON_AG_TRANCHES` shapes near-verbatim, the two scripts' fixes are
likely a single PR — worth extracting a shared helper at fix time so a third recurrence doesn't reintroduce this bug
class in a third script.

## Todos

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 — unified-trading-pm@6228cff7e.** `ao`/`ci`/`infra` membership branch now tests
      `t in asset_group` directly (via `TRANCHE_ASSET_GROUP_VALUE` mapping `infra`->`infrastructure`), matching the
      corrected 5-AG branches; the retired citation-grep mechanism (`_cited_basenames`/`CITE_RE`/`non_ag_cited`) removed
      entirely. **Done-when confirmed live**: `--tranche infra --json` excludes all 5 confirmed false positives
      (`ag_closeout_audit_rollout`, `ao_consolidated_closeout`, `cross_cutting_consolidated_closeout`,
      `june_2026_vintage_audit_findings`, `tradfi_consolidated_closeout`) and includes
      `infra_consolidated_closeout_2026_07_25.md`. Discovered via `/na-eligibility-audit ci` (this fix's own trigger):
      `--tranche ci --json` went from 0 docs (hard zero, closeout archived 2026-07-28) to 28.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 — unified-trading-pm@6228cff7e.** Tautological `peer_cited` self-veto removed;
      `cross-cutting` now tested via direct tag + `(parent_epic in DATA_EPICS or no other tranche already assigned)`.
      **Done-when confirmed live**: `--tranche cross-cutting --json` includes both
      `cross_cutting_consolidated_closeout_2026_07_25.md` and `june_2026_vintage_audit_findings_2026_07_27.md`.
- [x] ✅ [TEST] P2. **DONE 2026-07-30 — unified-trading-pm@6228cff7e**,
      `tests/unit/test_generate_na_doc_tranche_inventory.py` (7 cases):
      `test_citation_in_a_peer_closeout_doc_does_not_confer_membership` proves both (a)
      `infra_consolidated_closeout_2026_07_25.md` resolves to `['infra']` (a tranche's own closeout doc is always a
      member of its own tranche) and (b) a `ci`-tagged doc merely cited in that same infra closeout's body does NOT also
      pick up `infra`. Plus `test_non_ag_tranche_membership_needs_no_closeout_doc` (parametrized ci/ao/infra, no
      closeout file written at all), `test_infra_tranche_asset_group_value_is_infrastructure_not_infra`,
      `test_ag_tranche_membership_unaffected_by_the_fix`,
      `test_cross_cutting_solo_tag_is_assigned_without_data_epic_or_citation`,
      `test_ag_tagged_doc_with_cross_cutting_is_not_double_counted_unless_data_epic`. All 7 pass.
- [ ] [SCRIPT] P3. Evaluate ~~bundling this fix with the sibling script's fix~~ **STALE (na-eligibility-audit
      2026-08-03)** — the sibling script's own fix already shipped independently, same day, in a separate commit
      (`plans/archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`,
      `unified-trading-pm@e88c41727`, 2026-07-30 — vs. this doc's own fix at `@6228cff7e`, also 2026-07-30); the two
      were never bundled and that opportunity has passed. What remains genuinely open is the underlying idea: consider
      extracting one shared membership-test module both scripts import, to prevent a third recurrence of this bug class.

## Progress Log

- **na-eligibility-audit 2026-07-30** (infra tranche, dispatch agt-30721a): KEEP-NA, valid — 3 of 4 todos already done
  (`unified-trading-pm@6228cff7e` + `a72f78ab5`); the sole remaining item (bundle-vs-extract-shared-helper) is a design
  preference call, not a bounded/deterministic outcome, so it stays NA rather than RECLASSIFY. **Additional evidence for
  this remaining todo, found while running this session's own infra-tranche Phase 0 against the now-fixed script**: this
  run's ORIGINAL (pre-fix, buggy) `--tranche infra --json` population (64 docs, captured before this session pulled
  `6228cff7e`) was diffed against a fresh post-fix run — beyond the 5 false positives + 1 false negative this issue doc
  already documented, 3 MORE false positives surfaced that this doc's own investigation had not caught (scoped to just
  the 6 anomalous docs it happened to trace, not an exhaustive sweep, as its own Impact section already flagged as
  likely): `ao_consolidated_closeout_2026_07_25.md` (`asset_group: [ao]`, not infra),
  `issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md` and
  `issues/sports_mdps_coverage_reader_wrong_bucket_2026_07_28.md` (both `asset_group: [sports, meta]` — the `sports` tag
  should have taken precedence over the `meta` last-resort infra-fold, but the fixed script's `meta` fallback only
  checks `not tranches` at evaluation time, not whether a REAL AG tag is also present in the list; confirmed this is now
  CORRECTLY handled post-fix since the `sports` AG loop runs before the `meta` fallback and populates `tranches` first —
  these 3 were leaks in the OLD buggy citation-grep mechanism, not a residual gap in the new fix). Also found (not acted
  on, no assigned_vm change made): `issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md`,
  `issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`,
  `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (all cefi/multi-AG-tagged, not infra) were also
  present in the stale 64-doc population but only classified (KEEP-NA, no state change), not reclassified — zero harm.
  **Net**: the 3 acted-upon leaks (`ao_consolidated_closeout`, both sports docs) were already read end-to-end and
  RECLASSIFY-verdicted with real conflict-checks by this session before this cross-check ran; per operator-precedent
  (undoing sound, evidenced work over a scope technicality is worse than leaving it, since the correct tranche's own
  future audit will simply find these docs already `assigned_vm: planning` and skip them, no duplicate-dispatch risk) —
  left applied, flagged here for the record rather than reverted. This raises today's confirmed leak count to 8 docs
  total (5 original FP + 1 original FN + 3 new FP), materially more than the issue doc's original estimate — strengthens
  the case for the shared-helper extraction in the remaining P3 todo (a single well-tested membership module is less
  likely to leak silently a third time than two independently-maintained near-duplicates).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added the sibling script
  `generate_ag_closeout_audit_candidates.py`, the near-duplicate the doc's own "Fix direction" and remaining P3 todo
  (shared-helper extraction) name directly.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2 — the `parent_epic` vs `asset_group`
  grouping guidance this bug undermines
- `/cursor-configs/skills/na-eligibility-audit/SKILL.md` — Phase 0, which relies on this script's output
- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the 2026-07-27 schema-migration section both scripts are stale
  against

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — re-read end-to-end; sole open item (`[SCRIPT] P3`,
  bundle-vs-extract-a-shared-membership-test-module) is an explicit design-preference call per the 2026-07-30 marker
  (both scripts' own fixes already shipped independently, so this is purely about future-proofing architecture, not
  urgent or bounded to one clear approach). Checked against the round7-10 precedent set — the self-service-on-
  exact-sibling-script precedent doesn't apply here (this is a NEW shared-module extraction, not a repeat of an
  already-proven-safe rollout on an identical script). Not found in any of batch1-15's citation lists; this is a
  genuine, if minor, gap in the batch series — but the item itself remains a preference, not a bounded task with a
  stated done-when, so no extraction.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since
  round11. Sole open item ([SCRIPT] P3, bundle-vs-extract-a-shared-membership-test-module) remains a design-preference
  call with no stated done-when; not found in any active `ao_satellite_ao_dispatch_batch*` citation list through
  batch17.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
