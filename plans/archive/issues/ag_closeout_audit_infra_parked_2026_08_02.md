---
doc_type: issue
title:
  "Parked findings from the 2026-08-02 /ag-closeout-audit infra run (2 new findings: 1 dispatch-blocking assigned_vm:NA
  anomaly on an active AO batch, 1 minor dual-tag; plus classification of 4 newly-surfaced ex-meta tranche members and
  re-verification of all 6 carried-forward 2026-07-31/08-01 findings, all still open)"
summary: >-
  Two NEW mechanically-verified findings surfaced by the 2026-08-02 `/ag-closeout-audit infra` run (scheduled daily run,
  slot 11) that this skill's own `does_not` scope excludes it from fixing directly, plus classification of 4 tranche
  members that joined `infra`'s candidate set for the first time this run (retagged `asset_group: [meta]` →
  `[infrastructure]` on 2026-07-31 by a corpus-wide meta-fold-in sweep, never before evaluated by any infra covering
  doc), plus re-verification of all 6 findings from `issues/ag_closeout_audit_infra_parked_2026_08_01.md` (all still
  open/unresolved, no drift). Finding 7 is the most consequential: `infra_satellite_ao_dispatch_batch3_2026_07_30.md`
  carries `status: active` but `assigned_vm: NA`, meaning its one remaining `[BACKEND] P3` todo will never actually be
  picked up by AO dispatch despite living inside a nominally-covering "AO dispatch batch" doc — a live dispatch gap, not
  just the already-tracked stale-banner text issue (finding 4 from 2026-08-01). Finding 8 is a minor asset_group
  dual-tag (`[infrastructure, meta]`) that doesn't affect membership but is a tag-hygiene inconsistency. All
  evidence-backed, not judgment calls — recorded here per the "Parked findings ALWAYS get a durable issue doc" hard
  rule.
status: superseded
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ag-closeout-audit, plan-reconcile, false-unchecked, parked-findings, dispatch-gap, meta-fold-in]
related:
  [
    /plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_01.md,
    /plans/archive/issues/ag_closeout_audit_infra_parked_2026_07_31.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/git_health_not_clean_since_pinned_constant_2026_07_27.md,
    /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/archive/2026_08/issues/host_root_disk_full_transient_2026_07_13.md,
    /plans/archive/2026_07/issues/plan_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/archive/2026_07/issues/production_readiness_checklist_file_missing_2026_07_24.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-02"
author: unknown
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-08-02 (ag_closeout_auditor scheduled worker, slot 11). Phase 0 re-derived the
  covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (grew 39→43 members mid-run after a `git
  pull --ff-only` picked up a same-day corpus-wide meta-retag sweep). Ran the skill's iterative-drain step 1 (re-check
  batch1/batch3's tracked Deferred gates + the 2026-08-01 parked-findings doc) before a fresh Phase 1 Workflow (39-agent
  fan-out) over the pre-existing 39 members, plus direct classification of the 4 net-new members.
context_scope:
  [
    /plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_01.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: superseded` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. All 4 todos CLOSED as resolved/superseded (na-eligibility-audit 2026-08-06); 'later registers
> hold the still-live findings' — content absorbed by the 08-03/08-04 parked registers. Moved by the 2026-08-06 AO
> issue-doc archive sweep.

# Parked findings — 2026-08-02 `/ag-closeout-audit infra` run

## New findings this run

### 7. `infra_satellite_ao_dispatch_batch3_2026_07_30.md` — `assigned_vm: NA` on an active-status "AO dispatch batch" doc silently blocks its own remaining todo from ever being dispatched

**Doc state**: frontmatter `status: active`, `assigned_vm: NA`, `execution_scope: local-only`. Contrast with sibling
batches `infra_satellite_ao_dispatch_batch1_2026_07_26.md` and `infra_satellite_ao_dispatch_batch2_2026_07_27.md`, both
`status: active` AND `assigned_vm: planning` — the combination that actually makes AO's `regen_backlog_from_plan.py`
derive a dispatchable task from an open checkbox. Batch3 has 1 of 2 todos done (`[x]` ✅ the
`sync-gitignore-cursorignore.py --dry-run` gating fix, shipped `unified-trading-pm@78a3740bf`) and 1 still open:

> `- [ ] [BACKBEND] P3. Root-cause the fleet git-health \`not_clean_since\` pinned-constant and record a verdict`

This todo is tagged `[BACKEND]`, worded as a normal actionable item (not `[OPERATOR]`), and its source doc
(`issues/git_health_not_clean_since_pinned_constant_2026_07_27.md`) is cited as "covered" by batch3 in this run's
candidate generator output — but per CLAUDE.md's documented contract (`assigned_vm ∈ {planning, NA}`: `planning` =
orchestrator VM executes; `NA` = not dispatched), an `assigned_vm: NA` doc's checkboxes do not get turned into backlog
tasks regardless of `status`. **That "coverage" is therefore illusory in practice**:
`git_health_not_clean_since_pinned_ constant_2026_07_27.md`'s remaining work is cited by a doc that cannot actually
execute it.

**Likely root cause**: batch3 was authored 2026-07-30, the same day the skill's own "no double gate" ruling was made
(status:draft is the ONLY safety rail a batch needs; `assigned_vm: NA` was an OLDER convention some earlier batches used
before that ruling). Batch3 was plausibly authored under the pre-ruling convention and never migrated when the
convention changed — its sibling batch1/batch2 (authored slightly earlier, 07-26/07-27) both correctly use
`assigned_vm: planning`.

**Why not fixed here**: flipping `assigned_vm: NA` → `planning` on an already-`status: active` plan is functionally
equivalent to dispatching it — the exact action CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE and this
skill's own `does_not` scope (never flip a batch's dispatch state autonomously) gate behind operator confirmation. This
could be a simple authoring-bug fix (most likely) or could reflect an intentional decision not preserved in the doc's
own text — genuinely ambiguous which, so parking rather than guessing.

**Recommendation [WORKER REC]**: flip `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s `assigned_vm: NA` →
`planning` to match batch1/batch2's convention, so its one remaining todo actually dispatches. Verify
`infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md`'s `gate_on_depends` wiring still holds after the flip (it
should — gating reads the batch's own checkboxes regardless of `assigned_vm`, per the skill's own documented mechanism).

### 8. `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md` — minor `asset_group` dual-tag with `meta`

**Doc state**: `asset_group: [infrastructure, meta]` — carries BOTH the tranche's real tag and the generic `meta`
marker. Per the skill's own authoring rule ("`meta` is not a place to park a doc whose content is really single-tranche
or genuinely cross-AG... `meta` only when it spans everything or nothing"), a doc that is genuinely `infrastructure`-
scoped (as this one is — it's a fleet git-health investigation, squarely infra's own remit) should not also carry
`meta`. **This does NOT create a membership blind spot** (the candidate generator's `t in asset_group` test already
matches on the presence of `infrastructure` regardless of extra co-tags, confirmed: this doc appears correctly in this
run's 39/43-member list) — it is a pure tag-hygiene inconsistency, not a coverage bug.

**Recommendation [WORKER REC]**: drop the redundant `meta` tag, leaving `asset_group: [infrastructure]` alone. Low
priority (P3), no functional impact — bundle into whichever future doc-hygiene pass touches this file next rather than a
dedicated fix.

### 9. Four tranche members joined `infra`'s candidate set for the first time this run (retagged `meta`→`infrastructure` 2026-07-31, never before evaluated by any infra covering doc)

A same-day corpus-wide "meta fold-in" sweep (`unified-trading-pm@0409fa053` region, landed after my Phase 0 discovery
had already started, picked up via a mid-run `git pull --ff-only`) retagged several bare-`[meta]` docs to their real
tranches. Four landed in `infra` (member count 39→43, never-cited count 0→4). None had ever been evaluated by any infra
covering doc before — read each in full this run:

- **`issues/docs_reconcile_autonomous_sweep_2026_07_30.md`** — a prior `/docs-reconcile` run's own parking register.
  Genuinely orphaned (nothing in infra's covering set references it). Carries one **time-sensitive operator decision**
  worth flagging prominently regardless of tranche boundaries: **`check_codex_doc_freshness.py` (a hard PM QG gate)
  projects from 24 to ~168 violations on 2026-08-15** (144 codex docs bulk-stamped `last_reviewed: 2026-05-17` on one
  day all cross the 90-day staleness limit simultaneously) — **13 days from this run's date**, and unresolved this run
  makes it an outage, not a decision, on that date. Options A-D are laid out in the doc itself with a worker
  recommendation (staged, cohort-split re-review). Also carries 2 human-judgment items (4 dead codex doctrine refs
  needing repoint-or-delete judgment; an unterminated-bold-span fix that the doc's own text says routes to
  `/plan-reconcile`, not here) and ONE marginal AO-eligible candidate: retiring 2 genuinely-stale bare-name
  `unified-trading-codex` mentions in `.cursor/rules/ci-cd/act-secrets-setup.mdc:14` and
  `.cursor/rules/testing/test-coverage-targets.mdc:80` (a bounded wording fix, conflict-checked clear against the whole
  active corpus this run).
- **`issues/host_root_disk_full_transient_2026_07_13.md`** — genuinely orphaned. One open `[INFRA] P2` todo bundling an
  operator-permission-gated cron install (confirmed blocked: no crontab-write for this account) with two investigation
  sub-items that are NOT themselves permission-gated: root-causing why `UV_LINK_MODE=hardlink` isn't deduping `.venv`
  across the 16 slots (~150-200G footprint), and (if fixable) building a liveness-aware per-slot prune. The
  investigation half is conflict-checked clear against the whole active corpus this run.
- **`issues/plan_reconcile_autonomous_sweep_2026_07_30.md`** — genuinely orphaned. Its one open todo (`[OPS] P3` fleet-
  host stale-tmp cron audit) was already taken through the full conflict-check by `/na-eligibility-audit` on 2026-07-30
  and deliberately HELD at `assigned_vm: NA` (not flipped) on that skill's own judgment — this run does not re-litigate
  that call (out of this skill's scope per its own "Also NOT `/na-eligibility-audit`" section). Also carries 3
  unresolved prose-only operator-decision items (an `[unlock-plan]` question, a near-complete-plan fold-policy class
  question, a stale-scratch-clone delete question) — none converted to todos, so none show up in any checkbox count.
- **`issues/production_readiness_checklist_file_missing_2026_07_24.md`** — genuinely orphaned. One open `[ENGINEER] P2`
  todo, explicitly and correctly human-judgment-gated per the doc's own text (which of 5 disagreeing item-counts across
  6 files is authoritative has no mechanical answer) — `/na-eligibility-audit` already confirmed KEEP-NA valid
  2026-07-30. Not AO-eligible, not re-litigated here.

**Why not fixed/drafted here (partially)**: the two marginal AO-eligible candidates found (bare-name wording fix;
hardlink-dedup investigation) are conflict-clear and bounded — see this run's Phase 3 section / `batch6` draft (if
drafted) for whether they were extracted. The remaining items in all 4 docs are operator/judgment-gated by their own
prior analysis (2 of the 4 already carry an explicit `/na-eligibility-audit` KEEP-NA verdict) and are reported, not
re-decided, here.

## Carried forward from 2026-08-01 (re-verified today, unchanged — see that doc for full evidence)

All 6 findings in `issues/ag_closeout_audit_infra_parked_2026_08_01.md` (3 new that run + 3 carried from 2026-07-31)
were re-checked live this run and remain open, no drift:

1. **`codex_violations_ratchet_to_five_2026_06_10.md`'s `delta_proxy_repricer.py` checkbox** — still `- [ ]` at
   line 380. Still false-unchecked per the original finding (`execution-service@980a6ad0` already wires it in).
2. **`issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` todo 3** — still `- [ ]`.
   Re-checked the filesystem again this run: `.tabs/3/instruments-service-agentwork-sports-2026-07-13/` and
   `.tabs/3/stash-bundles/` are STILL absent from this sandbox — no new information, the original finding's caveat
   (confirm on the real target host, not just this sandbox) still stands.
3. **`issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`** — still `asset_group: [infrastructure]`,
   not retagged to `[ao]`.
4. **`infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s stale in-body `draft` banner** — still present at line 69
   (`> **⚠️ STATUS: \`draft\`** — NOT dispatched, NOT ingested...`), still contradicting the frontmatter's `status:
   active`. Distinct from (and now compounded by) finding 7 above — the banner text happens to be more accurate than the frontmatter currently implies, in the narrow sense that `assigned_vm:
   NA`really does mean nothing is being dispatched, even though`status`itself is genuinely`active`.
5. **`generate_ag_closeout_audit_candidates.py`'s `CITE_RE` self-referential citation blind spot** — unchanged, still
   not hardened (verified: the regex at line 69 is byte-identical to 2026-08-01).
6. **`issues/qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md`** — still `asset_group: [meta]`,
   not retagged to `[ao]`.

**Batch1 Deferred-gate re-check (iterative-drain step 1, per the skill's methodology)** — re-verified live before fresh
triage:

- **G1/G2 (`base-service.sh`/`base-library.sh` 4-item serialization, batch1 Deferred items 2-3)**: still gated.
  `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` (one of the two competing claims) is now archived, but the OTHER
  side, `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s `[BACKEND] P3` retry_safe-convention item (which
  also edits `base-service.sh`), is still open (`- [ ]`, verified this run). The serialization lock is not fully clear —
  only one of two claimants has released it.
- **Item 6 (repo_scripts DEPRECATE, subsumed by `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (k))**:
  still open (`- [ ] [CODE] P2`, verified this run) — unchanged.
- **G3 (`DataStatusTab.tsx`)**: already resolved via `infra_satellite_ao_dispatch_batch5_2026_08_01.md` — no change.
- **G5 (MTDS >900-line file tail)**: already resolved elsewhere per 2026-08-01's own note — no change.

**Batch4/batch5 status**: both still `status: draft`, both unchanged since authoring (07-31 and 08-01 respectively),
both still awaiting operator approval to flip to `active`. Neither has been actioned.

## Todos

- [x] ✅ [DOCS] P2. Flip `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s `assigned_vm: NA` → `planning` (finding 7)
      — **CLOSED 2026-08-06 (na-eligibility-audit)**: now in place — live `assigned_vm: planning` with the 2026-08-02
      correction comment (operator ruling, finding 7 — see
      `/plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md`), verified in batch3 frontmatter.
      OPERATOR CONFIRMATION NEEDED first (this changes live dispatch state). Done when: the field is flipped and the
      remaining `[BACKEND] P3` todo appears in the live AO backlog (verify via `/check-agent-orchestrator` or
      equivalent).
- [x] ✅ [DOCS] P3. Drop the redundant `meta` co-tag from
      `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md` **CLOSED 2026-08-06 (na-eligibility-audit)**:
      resolved by the broader 2026-08-02 operator-ruled retag — live `asset_group: [ao, meta]` with the multi-value kept
      intentionally (comment documents the ruling), verified. (finding 8). Done when: `asset_group: [infrastructure]`
      only.
- [x] ✅ [OPERATOR] P0. **Rule on `docs_reconcile_autonomous_sweep_2026_07_30.md`'s P0-A before 2026-08-15** (finding 9,
      **CLOSED 2026-08-06 (na-eligibility-audit)**: operator-ruled 2026-08-03 (closeout Progress Log: "P0-A 2026-08-15
      cliff operator-ruled"), resolved. re-surfaced from that doc's own prior parking) — the
      `check_codex_doc_freshness.py` 144-doc bulk-stamp cliff. 13 days remaining as of this run's date. See that doc's
      own §P0-A for options A-D.
- [x] ✅ [DOCS] P3. Re-carry forward the 6 still-open 2026-08-01/07-31 findings (delta_proxy_repricer.py checkbox;
      confirm **CLOSED 2026-08-06 (na-eligibility-audit)**: superseded — carried into the 08-03/08-04 parked registers'
      carried-forward lists (batch3 blank-flip re-apply as finding 10, stash-backup bundle as finding 11, plus 12/13
      tooling findings). stash-clone directory's real-host state; retag `ao_self_pull_wedged` + `qg_owner_gate` mistags
      to `[ao]`; fix batch3's stale banner; harden `CITE_RE`) — see
      `issues/ag_closeout_audit_infra_parked_2026_08_01.md`'s own Todos section for the authoritative text; not restated
      here to avoid drift between two copies.

## Progress Log

- **na-eligibility-audit 2026-08-06 (infra tranche)**: **KEEP-NA-STALE-ITEMS — all 4 items closed as resolved/superseded
  (see closes), doc stays NA** as the parked-findings register lineage (later registers hold the still-live findings).

- **2026-08-02** — `/ag-closeout-audit infra` run (autonomous mode, scheduled daily run, slot 11). Re-derived the
  candidate set (`generate_ag_closeout_audit_candidates.py --tranche infra`: 39→43 members mid-run after a same-day
  corpus-wide meta-retag sweep landed via `git pull --ff-only`, never-cited 0→4). Re-checked batch1/batch3's tracked
  Deferred gates + all 6 findings from the 2026-08-01 parked doc live before fresh triage — all unchanged, no drift. Ran
  a 39-agent Phase 1 Workflow over the pre-existing candidate set (results pending/being synthesized into the main audit
  report) plus direct full-text classification of the 4 net-new ex-meta members. Surfaced 2 new findings this run (7-8
  above) plus classification of the 4 new members (9 above). **Ledger**: 2 new parked findings + 1 combined 4-sub-item
  classification note this run, 3 entries written above (7, 8, 9) — balanced.
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run, later the same day): **KEEP-NA, valid.** First
  verdict for this doc (created earlier today, no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **4**,
  matching this verdict's item count. NA is correct on the merits: todo 1 (batch3's `assigned_vm` flip) is self-declared
  "OPERATOR CONFIRMATION NEEDED", todo 3 is `[OPERATOR] P0`, todo 4 is a re-carry-forward pointer with no independent
  content, and only todo 2 (drop a redundant `meta` co-tag) is mechanical — one mechanical item does not make a doc
  dispatchable when flipping it would also expose an explicitly operator-gated P0. **Finding 7 — independent concurrence
  from the skill that actually owns `assigned_vm` verdicts.** `/na-eligibility-audit`'s Phase 3 is the mechanism that
  flips `assigned_vm: NA → planning`, so this run assessed batch3 directly rather than deferring: **HELD NA, agreeing
  with finding 7's park, on two grounds finding 7 did not cite.** (i) Batch3's own body (line 69) still carries a
  `⚠️ STATUS: draft — NOT dispatched, NOT ingested. Flipping this ... is the operator's call` banner; this skill's
  Phase-1 rule treats a do-not-dispatch/redirect banner as KEEP-NA **on the citation alone**, and this banner explicitly
  reserves the call to the operator. (ii) A prior `/na-eligibility-audit` RECLASSIFY of a banner-guarded doc caused
  three real mis-dispatches before it was caught and reverted
  (`regen_positional_task_ids_not_content_stable_2026_07_17.md`, BLK-29884333, 2026-07-31) — that incident is precisely
  why this skill now treats a banner-vs-frontmatter contradiction as an operator question, never a worker inference.
  Finding 7's recommendation stands and is the right one; it needs the operator, so no duplicate park is filed here.
  **Finding 9's `[OPERATOR] P0` (the 2026-08-15 `check_codex_doc_freshness.py` cliff) was re-confirmed live this run** —
  still `- [ ]` at source (`docs_reconcile_autonomous_sweep_2026_07_30.md` todo 1), 13 days out, a hard PM QG gate
  projected 24 → ~168 violations in a single day. Re-surfaced in this run's report rather than only living here.
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (3 entries), still accurate.
