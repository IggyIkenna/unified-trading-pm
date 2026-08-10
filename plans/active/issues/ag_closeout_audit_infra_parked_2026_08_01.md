---
doc_type: issue
title:
  "Parked findings from the 2026-08-01 /ag-closeout-audit infra run (3 new findings: 1 stale draft-banner, 1 tooling
  self-referential-citation blind spot, 1 likely asset_group mistag; plus re-verification of 3 carried-forward
  2026-07-31 findings, all still open)"
summary: >-
  Three NEW mechanically-verified findings surfaced by the 2026-08-01 `/ag-closeout-audit infra` run (scheduled daily
  run, slot 5) that this skill's own `does_not` scope excludes it from fixing directly, plus re-verification of the 3
  findings from `issues/ag_closeout_audit_infra_parked_2026_07_31.md` (all still open/unresolved, no drift). Finding 4
  is a stale in-body `status: draft` banner contradicting `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s own
  frontmatter (`status: active`, with real shipped work) — a `/plan-reconcile`-class doc-hygiene fix. Finding 5 is a
  tooling gap in `generate_ag_closeout_audit_candidates.py`'s cheap Phase-0 pre-filter: a Progress Log entry that NAMES
  a never-cited doc for reporting purposes is itself picked up by the citation regex on the next run, silently removing
  a genuinely-orphaned/mistagged doc from future never-cited lists. Finding 6 is a second likely `asset_group` mistag
  (real owner `ao`, not `infra`) found via the corpus-wide new-doc sweep, reported per the skill's
  concurrent-sharded-worker rule (only the owning tranche may write the retag). All evidence-backed, not judgment calls
  — recorded here per the "Parked findings ALWAYS get a durable issue doc" hard rule.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-ui, deployment-api]
scope: [engineer, admin]
tags: [infra, ag-closeout-audit, plan-reconcile, false-unchecked, parked-findings, tooling-gap]
related:
  [
    /plans/archive/issues/ag_closeout_audit_infra_parked_2026_07_31.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch5_2026_08_01.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/issues/qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
created: "2026-08-01"
author: unknown
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
archive_exempt: true # 2026-08-10: 0 open todos, full archival deferred (grace-locked referrer) -- see Progress Log
source: >-
  `/ag-closeout-audit infra` run 2026-08-01 (ag_closeout_auditor scheduled worker, slot 5). Phase 0 re-derived the
  covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (39 members, 1 never-cited) and ran the
  skill's iterative-drain step 1 (re-check batch1/batch3's tracked Deferred gates + the prior parked-findings doc)
  before fresh triage.
context_scope:
  [
    /plans/archive/issues/ag_closeout_audit_infra_parked_2026_07_31.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
---

# Parked findings — 2026-08-01 `/ag-closeout-audit infra` run

## New findings this run

### 4. `infra_satellite_ao_dispatch_batch3_2026_07_30.md` — stale in-body `draft` banner contradicts its own `status: active` frontmatter

**Doc state**: frontmatter `status: active` (line 18), `assigned_vm: NA`, `execution_scope: local-only`. Todo 1 is
already `[x]` ✅ shipped (`unified-trading-pm@78a3740bf`, verified real work — the
`sync-gitignore-cursorignore.py --dry-run` gating fix with a regression test and a live 25-repo verification sweep). Yet
the doc's own body (line 62) still reads:

> **⚠️ STATUS: `draft`** — NOT dispatched, NOT ingested. Flipping this (and its finalize twin) to `status: active` is
> the operator's call...

This banner was accurate when the doc was drafted 2026-07-30, but the frontmatter has since flipped to `active` and real
work has shipped under it — the banner text was never updated to match. A reader trusting the in-body banner over the
frontmatter would wrongly conclude nothing has been dispatched or shipped here.

**Recommendation [WORKER REC]**: update or remove the stale banner to match the frontmatter (`status: active`, 1 of 2
todos done). Do not treat this as a reason to re-derive whether the doc SHOULD be active — that decision already
happened; this is a text-accuracy fix only, `/plan-reconcile`'s territory, not a re-litigation of the dispatch decision.

### 5. `generate_ag_closeout_audit_candidates.py` — self-referential citation blind spot in the never-cited pre-filter

**Found**: this run's candidate set (`--tranche infra`) reports only 1 never-cited candidate, down from the 2026-07-31
21:26 run's finding that `issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` was the tranche's one
persistently-never-cited, non-self-dispatched candidate (see finding 3 below — still unretagged, still
`asset_group: [infrastructure]`). That doc no longer appears in this run's never-cited list. Root cause:
`infra_consolidated_closeout_2026_07_25.md`'s own Progress Log (the 2026-07-31 ~21:26 UTC entry) NAMES the doc in prose
while reporting the finding —
`"The one never-cited candidate (\`ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md\`) is a likely
asset_group
mistag..."`— and the script's`CITE_RE` regex (`[a-z0-9_]+_20\d\d_\d\d_\d\d(?:_finalize)?\.md`) matches ANY occurrence of a date-suffixed filename substring anywhere in a covering doc's text, with no distinction between a real dispatch citation (a todo's `Source:`line) and a narrative mention describing that the doc is NOT covered. Verified directly:`grep
-n 'ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30' plans/active/infra_consolidated_closeout_2026_07_25.md`
returns exactly one hit, at the Progress Log line quoted above — not a todo, not a dispatch, just the act of reporting
the prior finding.

**Why this matters**: the tool's own docstring already caveats that a citation "can be a stale reference, a partial-
coverage mention, or a genuine close" — but a narrative self-report of "this is never-cited" is a NEW failure mode the
docstring doesn't cover: it makes the tool's own output about a finding retroactively hide that same finding from future
runs. Every tranche hub that follows the same "name the orphan candidate in the Progress Log to report it" convention
(which this skill's own "Parked findings ALWAYS get a durable issue doc" rule and general hygiene both encourage) will
reproduce this on its own never-cited/mistagged candidates going forward — this is not a one-off, it's systemic to how
the tool + the reporting convention interact. **Verified the underlying finding is still accurate independent of the
tool**: finding 3 below confirms `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` is still genuinely
uncovered by any real infra dispatch (only mentioned in prose, never `Source:`-cited by a todo) — the tool's "cited"
signal is a false positive for coverage purposes even though it's a true positive for "the filename string appears in
the file."

**Recommendation [WORKER REC]**: harden `CITE_RE` matching (or the covering-doc text it scans) to exclude Progress Log
narrative mentions from counting as citations — e.g. only count a filename match when it appears as a `Source:` citation
or within a todo line, not in prose sections like `## Progress Log`. This is a real, scoped, bounded code fix to a
single script (`scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`), not a design judgment call — but it is
outside this skill's own `does_not` scope (this skill classifies and reports, it does not patch its own tooling
mid-audit) and outside infra's remit specifically (the script is corpus-wide shared tooling, used by every tranche).
Flagging for whichever plan owns `plan_hygiene_master`/this script's own lifecycle marker to pick up.

**Self-demonstrated live, same run**: this run's own new docs (`infra_satellite_ao_dispatch_batch5_2026_08_01.md`'s
summary + this doc's own "New findings this run" section below) name
`deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md` in prose while reporting it as never-cited — and
because `infra_satellite_ao_dispatch_batch5_2026_08_01.md` matches `_covering_paths()`'s glob, that prose mention now
makes `generate_ag_closeout_audit_candidates.py --tranche infra` report that doc as "cited" too (verified directly:
re-running the candidate generator after this session's docs were written shows
`deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md` no longer in the never-cited list, and total
members rose 39→40 as this doc's own two new docs joined the candidate pool). The doc's REAL state is unchanged — it is
still `assigned_vm: NA`, status `open`, with its one `[INFRA] P3` todo still genuinely undispatched; only the mechanical
pre-filter's signal is now wrong. This is not a hypothetical risk, it is this exact run reproducing the bug on a second
doc within the same session that first identified it — strengthening rather than illustrating the case for the fix. A
future run should not trust a "not in the never-cited list" result alone for this doc; the `/na-eligibility-audit`
skill's own `assigned_vm: NA` sweep (which does not depend on this citation mechanism) is the safety net that keeps this
doc visible regardless.

### 6. `issues/qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md` — `asset_group: [meta]`, likely real owner `ao`

**Found**: 2026-08-01 sweep of newly-created docs since the 2026-07-31 21:26 run (git log `--since` scan), checked
against the skill's own "Total-coverage gap" rule (`asset_group: meta` must be swept and folded into its real tranche by
content on every single-tranche run, not just `all` mode).

**Doc state**: `asset_group: [meta]`, `status: open`, `assigned_vm: NA`,
`parent_epic: agent_operating_framework_master`, 1 open todo. Content: a QG check script
(`check_runbook_execution_owner.py`) performs a full-workspace `rglob` that descends into every `.tabs/*/.venv` tree
before post-filtering, I/O-thrashing the shared host and hanging `quality-gates.sh` inside `quickmerge` for 13+ minutes
— diagnosed as the likely root cause of a separately-tracked sustained-git-red pattern.

**Why not infra**: this doc's content is squarely about the quickmerge/QG pipeline mechanics, and its `parent_epic`
(`agent_operating_framework_master`) is the skill's own cited hint for the `ao` tranche
(`ao ≈ orchestrator_master + agent_operating_framework_master`), not any of infra's 3 live tracks (repo/script
governance+CVE, org/account admin+terraform, PM plan-hygiene tooling). It does not squarely match `ci`'s hint epics
either (`infrastructure_master`/`deployment_and_user_management_master`/`strategy_master`/`plan_hygiene_master`) — the
`parent_epic` signal points specifically at `ao`. Read as a genuine `meta`-tag-needs-folding case, most likely
`ao`-owned, not an infra mistag.

**Why not fixed here**: same concurrent-sharded-worker rule as finding 3 below — only the real owning tranche
(apparently `ao`) may write the retag. This run only reports it (it was never actually an infra candidate — it's
`asset_group: [meta]`, not `[infrastructure]`, so it never appeared in
`generate_ag_closeout_audit_candidates.py --tranche infra`'s output; found via the separate meta-sweep the skill's own
Phase 0.3 requires).

**Recommendation [WORKER REC]**: the `ao`-tranche's own `/ag-closeout-audit ao` run (or a corpus-wide `meta`-fold-in
pass) should retag `asset_group: [meta]` → `[ao]` after confirming ownership, and fold this doc into
`ao_consolidated_closeout_2026_07_25.md`'s membership.

## Carried forward from 2026-07-31 (re-verified today, unchanged — see the original doc for full evidence)

All 3 findings in `issues/ag_closeout_audit_infra_parked_2026_07_31.md` were re-checked live this run and remain open,
no drift:

1. **`codex_violations_ratchet_to_five_2026_06_10.md`'s `delta_proxy_repricer.py` checkbox** — still `- [ ]` at
   line 373. Still false-unchecked per the original finding (`execution-service@980a6ad0` already wires it in).
2. **`issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` todo 3** — still `- [ ]`.
   Re-checked the filesystem again this run: `.tabs/3/instruments-service-agentwork-sports-2026-07-13/` and
   `.tabs/3/stash-bundles/` are STILL absent from this sandbox, same as 2026-07-31's observation — no new information,
   the original finding's caveat (confirm on the real target host, not just this sandbox) still stands.
3. **`issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`** — still `asset_group: [infrastructure]`,
   not retagged to `[ao]`. See finding 5 above for why this run's mechanical pre-filter no longer flags it automatically
   — it is still a real, live, unretagged mistag, confirmed by direct re-read this run.

## Todos

- [x] ✅ [DOCS] P3. Update or remove the stale `draft` banner in `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s
      body **CLOSED 2026-08-06 (na-eligibility-audit)**: banner already replaced 2026-08-02 by the operator's flip
      commit (dfdb0887f) — batch3 now carries an "ACTIVE + DISPATCHABLE (2026-08-02)" banner, verified live. text
      (finding 4). Done when: the banner matches the frontmatter `status: active` state (or is removed entirely now that
      the doc has real shipped work under it).
- [x] ✅ [SCRIPT] P3. **CLOSED 2026-08-10 (plan_reconciler infra shard, agt-716973) — superseded, not shipped.** This
      item (finding 5, `CITE_RE` hardening) is the SAME item this doc's own 2026-08-08 Progress Log entry (below)
      already confirmed is "the SAME item" as `ag_closeout_audit_infra_parked_2026_08_03.md`'s finding 13 — which has
      itself been carried forward daily since and is now tracked live as finding 13 in
      `ag_closeout_audit_infra_parked_2026_08_09.md:180-181` ("carried, 7th day"), still genuinely open THERE. Closing
      the duplicate copy here per this same doc's own established precedent (see the 2026-08-06 Progress Log entry
      below: "superseded — the findings now live in the 08-02/08-03/08-04 parked registers"). Not double-counted as done
      — the underlying work is still open, just tracked in one place instead of two.
- [x] ✅ [DOCS] P3. Retag `issues/qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md`'s
      `asset_group` **CLOSED 2026-08-06 (na-eligibility-audit)**: done 2026-08-02 by operator ruling
      (`/plans/archive/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 19,
      option A) — live `asset_group: [ao]`, verified. `[meta]` → `[ao]` (finding 6) — owning-tranche fix, leave to the
      `ao`-tranche's own audit or a corpus-wide `meta`-fold-in pass, not this run. Done when: the tag is corrected and
      ~~the doc is folded into `ao_consolidated_closeout_2026_07_25.md`'s membership~~. **STALE (na-eligibility-audit
      2026-08-03)** — `ao_consolidated_closeout_2026_07_25.md` archived 2026-07-30 (`status: complete`); its own
      ARCHIVED banner says it no longer tracks live Sources membership (37/44 orphaned as of that date) and redirects
      membership authority to `ao_satellite_ao_dispatch_batch1_2026_07_26.md` (+ gated finalize) and
      `ao_open_issues_consolidated_close_out_2026_07_17.md` — `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s own
      2026-08-01 Progress Log independently reached the same conclusion for an identical citation on its own todo 11
      ("editing the literal doc this todo named is moot since it archived 2026-07-30 and its own banner already
      redirects membership authority elsewhere"). The retag half of this todo is still open and undone; only the fold-in
      target needs updating to the live doc.
- [x] ✅ [DOCS] P3. Re-carry forward the 3 still-open 2026-07-31 findings/todos (reconcile `delta_proxy_repricer.py`'s
      **CLOSED 2026-08-06 (na-eligibility-audit)**: superseded — the findings now live in the 08-02/08-03/08-04 parked
      registers: delta_proxy_repricer.py checkbox shipped (execution-service@980a6ad0, closeout 08-03); stash-clone
      real-host state + ao_self_pull retag carried as open findings in the newer registers. checkbox; positively confirm
      the stash-clone directory's real-host state; retag
      `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`) — see
      `issues/ag_closeout_audit_infra_parked_2026_07_31.md`'s own Todos section for the authoritative text; not restated
      here to avoid drift between two copies.

## Progress Log

- **na-eligibility-audit 2026-08-09** (infra tranche) [body-hash:b96fda14721769a1]: KEEP-NA, valid — unchanged. Sole
  open item (finding 5, `CITE_RE` self-referential-citation hardening) remains a genuine unresolved shared-tooling
  design gap, consistent with 8+ prior passes.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — unchanged since 2026-08-07. Re-read
  end-to-end; `grep -cE '^- \[ \]'` = 1, matching (the `CITE_RE` self-referential-citation hardening item, finding 5).
  Checked against today's operator-Q&A rulings cheat sheet: no precedent applies. Also checked the sibling
  `ag_closeout_audit_infra_parked_2026_08_03.md`'s finding 13, which carries the SAME item and explicitly states it
  "needs a design decision (e.g., only count a mention inside an actual todo line, or within N lines of a `Source:`
  marker) that this run did not make" — that doc's own 2026-08-03 na-eligibility-audit verdict independently reached the
  same conclusion ("neither clears the bounded/deterministic bar for RECLASSIFY"). Consistent, unchanged. NA correct.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since 2026-08-06. Re-read end-to-end;
  `grep -cE '^- \[ \]'` = 1, matching. The sole remaining open item (harden `generate_ag_closeout_audit_candidates.py`'s
  `CITE_RE` so a Progress Log narrative mention doesn't count as a citation) is still a genuine, unresolved, corpus-wide
  shared-tooling gap outside this tranche's own remit — only a context-scout scope refresh touched the doc since the
  last marker.
- **na-eligibility-audit 2026-08-06 (infra tranche)**: **KEEP-NA-STALE-ITEMS — 3 of 4 closed, doc stays NA.** Closed:
  batch3 stale draft banner (replaced by ACTIVE+DISPATCHABLE banner, verified); qg_owner_gate retag (live `[ao]`,
  verified); re-carry-forward (superseded by the 08-02/08-03/08-04 registers). Item 2 (CITE_RE harden in
  generate_ag_closeout_audit_candidates.py) stays open — genuine still-unresolved tooling gap.

- **2026-08-01** — `/ag-closeout-audit infra` run (autonomous mode, scheduled daily run, slot 5). Re-derived the
  candidate set (`generate_ag_closeout_audit_candidates.py --tranche infra`: 39 members, 10 covering docs, 1
  never-cited). Re-checked batch1/batch3's tracked Deferred gates (G1-G6) live before any fresh triage — found G3
  (`DataStatusTab.tsx` `DATA_PIPELINE_SERVICES` sequencing gate) genuinely cleared (cross-cutting's blocking item
  shipped `deployment-ui@727298b`, 2026-08-01), drafted `infra_satellite_ao_dispatch_batch5_2026_08_01.md` as a result
  (single todo, `status: draft`, operator flip required). Re-verified the 3 carried-forward 2026-07-31 findings live:
  all still open, no drift. Surfaced 3 new findings this run (4-6 above) via (a) reading
  `infra_satellite_ao_dispatch_batch3_2026_07_30.md` in full while re-checking its Deferred gates, (b) investigating why
  a previously-flagged mistag (finding 3) silently dropped out of the mechanical pre-filter's never-cited list, and (c)
  a git-log sweep of docs created since the 2026-07-31 21:26 run, cross-checked against the skill's `asset_group: meta`
  fold-in requirement. **Ledger**: 3 new parked findings this run, 3 entries written above (4, 5, 6) — balanced. The 1
  new never-cited candidate this run (`issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`) is
  not counted as a "parked finding" here — it is a genuine `orphaned_never_touched` Phase-1 classification
  (operator-gated: a live/config terraform drift whose correct direction requires an intent judgment call, plus a
  delete-safety-adjacent apply), but its own existing `[INFRA] P3` todo already fully captures the ask; there is nothing
  new for this run to add beyond confirming the classification, so it is reported in the Phase 2 summary, not duplicated
  into a Todos entry here.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-confirmed context_scope (4 entries, unchanged) -- already includes the real source
  target for the still-open finding-5 tooling fix (generate_ag_closeout_audit_candidates.py).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid.** First verdict for this doc
  (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **4**, matching this verdict's item count. NA is correct
  on the merits for the doc as a whole: it is a parked-findings register whose four todos are each explicitly routed
  elsewhere by their own text — the batch3 stale-banner fix and the `CITE_RE` hardening are named as
  `/plan-reconcile`-class and shared-corpus-tooling work respectively ("outside infra's remit specifically"), the
  `qg_owner_gate` retag is reserved for the `ao` tranche by the owning-tranche-writes-only rule, and todo 4 is a
  re-carry-forward pointer with no independent content. Flipping the doc's `assigned_vm` would dispatch all four
  including the two the doc deliberately declines to own. **Cross-reference for finding 5** (the `CITE_RE`
  self-referential citation blind spot): this run independently confirms that finding's own closing claim — the
  `/na-eligibility-audit` `assigned_vm: NA` sweep does not depend on the citation mechanism, and both docs it names
  (`ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`,
  `deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`) were in this run's candidate set and were read
  and verdicted, so the safety net held as designed.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (4 entries) -- the sole open todo (CITE_RE hardening
  in generate_ag_closeout_audit_candidates.py) is still fully covered.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **2026-08-10 (plan_reconciler infra shard, agt-716973)**: closed the sole remaining open item (finding 5) as a
  superseded duplicate — see the todo above for evidence. Doc is now fully done, unlocked — normally archive-ready, but
  **archival DEFERRED this run**: referrer `ag_closeout_audit_infra_parked_2026_08_03.md` is inside today's 12h grace
  window (actively worked, read-only this run); archiving now would leave that referrer's leading-slash reference
  dangling. A future run (once that doc clears grace) should complete the 6-step archival ritual.
