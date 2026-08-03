---
doc_type: issue
title:
  "Parked findings from the 2026-08-03 /ag-closeout-audit infra run (4 new findings: batch3's operator-approved
  assigned_vm flip landed blank not planning, a scratch-clone backup bundle now genuinely missing anywhere on-host, a
  self-dispatched-doc methodology caveat corroborated by multiple independent Phase-1 agents, and 2 unscoped batch7
  candidates; plus re-verification of all 9 carried-forward 2026-07-31/08-01/08-02 findings — 5 resolved since
  yesterday, 1 still open unchanged)"
summary: >-
  Four NEW findings surfaced by the 2026-08-03 `/ag-closeout-audit infra` run (scheduled daily run, slot 12) after a
  full 45-agent Phase 1 Workflow re-triage of every infra-tranche candidate doc. Finding 10 is the most consequential:
  the 2026-08-02 operator-approved fix (finding 7, flip `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s
  `assigned_vm: NA` -> `planning`) landed as a BLANK value instead of `planning` — the batch's own in-body banner
  falsely claims "ACTIVE + DISPATCHABLE", and this fooled today's own Phase-1 audit agent into reporting the fix as
  "fully DONE" from the banner text alone, without checking the raw frontmatter value. Finding 11 is a real-host
  verification (this shared host, uptime 5+ days, not an ephemeral sandbox — upgrading confidence over every prior run's
  "unconfirmed, check the real host" caveat) that BOTH the stale scratch-clone directory AND its previously "durably
  bundled + verified" stash backup are now absent anywhere under /home/ubuntu — contradicts the todo's own done-when
  (bundle should be the sole remaining trace); needs operator investigation (real data loss vs. an incidental slot-3
  reset sweeping both ad-hoc dirs together). Finding 12 is a methodology caveat: 15 of today's 42 orphaned-verdict docs
  are already self-dispatched (`assigned_vm: planning` + `status: active/open`) and do NOT need batch7 treatment —
  multiple independent Phase-1 agents flagged this unprompted. Finding 13 flags 2 possible batch7 candidates found but
  NOT drafted this run (need dedicated scoping first). Also fixed in-line this run (not parked, already shipped):
  `infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s todo 1 was already resolved independently by today's
  `docs_reconciler` sweep — marked done, `unified-trading-pm` LDR.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ag-closeout-audit, plan-reconcile, parked-findings, dispatch-gap, data-loss-risk, self-dispatched-caveat]
related:
  [
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_02.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_01.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_07_31.md,
    /plans/active/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/active/infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md,
    /plans/active/infra_satellite_ao_dispatch_batch6_2026_08_02.md,
    /plans/active/issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-08-03 (ag_closeout_auditor scheduled worker, slot 12). Phase 0 re-derived the
  covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (13 covering docs, 45 members, 2
  never-cited). Ran the skill's iterative-drain step 1 (re-checked all 9 carried-forward 2026-07-31/08-01/08-02 findings
  live) before a fresh 45-agent Phase 1 Workflow fan-out over the full candidate set.
context_scope:
  [
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_02.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Parked findings — 2026-08-03 `/ag-closeout-audit infra` run

## New findings this run

### 10. `infra_satellite_ao_dispatch_batch3_2026_07_30.md` — the 2026-08-02 operator-approved `assigned_vm` flip landed BLANK, not `planning`; the dispatch gap (finding 7) persists, now compounded by a false banner

**Confirmed via direct raw-file inspection + `git log -p`**, not doc prose: batch3's frontmatter at line 39 currently
reads `assigned_vm:` with **no value at all** (verified `cat -A`: the line is exactly `assigned_vm:$`, i.e. YAML null) —
neither `NA` nor `planning`, worse than the pre-fix state finding 7 originally flagged. `git log --since 2026-07-30 -p`
on this file shows commit `dfdb0887f` (2026-08-03 00:11:38+01:00, message "Finding 7: flip
infra_satellite_ao_dispatch_batch3's assigned_vm NA->planning") diffed `-assigned_vm: NA` / `+assigned_vm:` — the intent
was clearly `planning` (the commit message and the same-commit in-body banner both say so), but the actual YAML edit
landed empty. The banner added in that same commit (lines 77-80) reads:

> **✅ ACTIVE + DISPATCHABLE (2026-08-02).** `status: active` since authoring; `assigned_vm` flipped `NA` → `planning`
> 2026-08-02 (operator ruling, `ag_closeout_audit_infra_parked_2026_08_02.md` finding 7)... The remaining `[BACKEND] P3`
> todo is now genuinely AO-dispatchable.

This is false as written — `regen_backlog_from_plan.py` derives dispatchable tasks from `assigned_vm: planning`
specifically; a blank value does not satisfy that check any more than `NA` did. `check_frontmatter_schema.py` does NOT
flag this (0 violations reported) — the schema check treats a blank value as passing, so this is a live, silent gap: the
one remaining `[BACKEND] P3` todo (root-cause the fleet git-health `not_clean_since` pinned constant) is still not
actually in the AO backlog, exactly as before finding 7's fix was attempted, one day later.

**This also fooled today's own Phase-1 audit**: the sub-agent auditing `ag_closeout_audit_infra_parked_2026_08_02.md`
(which discusses batch3) concluded "Todo 1 (finding 7 ...) is fully DONE: `infra_satellite_ao_dispatch_batch3...`
frontmatter (lines 39-44) and body banner (lines 77-80) confirm the flip landed" — a careful, otherwise-accurate
full-document read that nonetheless inferred success from the banner's prose rather than parsing the literal
`assigned_vm:` value. Worth noting for future runs: a doc's own claimed-resolution banner is not a substitute for
checking the raw frontmatter field it claims to describe.

**Why not fixed here directly**: per this skill's own established precedent for this exact class of action (see finding
7's own "Why not fixed here" section, 2026-08-02) — flipping `assigned_vm` on an already-`status: active` plan is
functionally equivalent to dispatching it, gated behind operator confirmation each time, not a standing blanket approval
to silently re-apply. The fact that the SAME flip was already approved once and still needs a human to physically
complete correctly is itself part of what's being reported.

**Recommendation [WORKER REC]**: re-apply the flip — set `infra_satellite_ao_dispatch_batch3_2026_07_30.md` line 39 to
`assigned_vm: planning` (matching sibling batches 1/2 and the original finding 7 intent) — then verify the
`[BACKEND] P3` todo actually appears in the live AO backlog (`/check-agent-orchestrator` or equivalent) before
considering this closed. Consider whether `check_frontmatter_schema.py` should hard-reject a blank `assigned_vm` on a
`status: active`+`doc_type: plan` document (currently silent) as a durability improvement, since this exact failure mode
(an edit landing empty rather than the intended enum value) evaded both the QG and a careful human- style doc read.

### 11. `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` — the "durably bundled" stash backup is now genuinely absent anywhere on this host, not just unconfirmed

**Upgraded confidence over every prior run's caveat**: 2026-08-01 and 2026-08-02 both noted
`.tabs/3/instruments-service-agentwork-sports-2026-07-13/` and `.tabs/3/stash-bundles/` as absent but explicitly
cautioned this might be "just this sandbox," not the real target host. This run confirmed the host is genuinely the
long-running shared multi-slot host (`hostname` = `ip-172-31-5-118`, `uptime` = 5 days 8+ hours, load average 18-22
consistent with many concurrent agent slots; `.tabs/3/` itself exists and is normally populated with the full standard
sibling-repo set) — not an isolated/ephemeral sandbox. Against that confirmed-real host:

- `.tabs/3/instruments-service-agentwork-sports-2026-07-13/` — **absent** (`ls` → No such file or directory).
- `.tabs/3/stash-bundles/` — **also absent** (same).
- A broader `find /home/ubuntu -iname "*agentwork-sports-2026-07-13*"` and
  `find /home/ubuntu -iname "*instruments-service-agentwork*"` across the ENTIRE home directory (all 16 slots, every
  repo) — **zero hits anywhere**, including for the specific bundle filename
  `instruments-service-agentwork-sports-2026-07-13-stashes.bundle`.

This is a real discrepancy from the open todo's own stated **done-when**: "directory is gone,
`du -sh .tabs/3/stash-bundles/` confirms the bundle is the only remaining trace." The directory being gone is expected
(matches the operator's 2026-07-30 bundle-then-delete ruling) — but the bundle being gone too was NOT part of that plan;
the whole point of bundling first was to make the 10 stash entries recoverable after the source directory's removal. If
the bundle is genuinely gone with no other copy, those 10 stash entries (previously verified present via direct
unbundle + `git cat-file -e` on all 10 SHAs, per the doc's own SCRIPT todo) are very likely permanently lost.

**Two plausible explanations, not distinguishable from this session alone**: (a) the bundle was deliberately moved to a
durable location outside `/home/ubuntu` (a different host, GCS, an external backup) before the source directory was
removed — the safe, intended outcome, just not verifiable from here; or (b) slot 3 was reset/recreated at some point
after the bundle was created, which would wipe both ad-hoc, non-standard directories together as a side effect of
returning the slot to its standard sibling-repo set — in which case the bundle's own protection was moot from the moment
of that reset, regardless of when the "official" delete todo would have run. Not escalating as `BLOCKED-OPERATOR` (no
in-flight work is blocked on this), but flagging clearly since a possible unrecovered data loss of 10 real stash entries
(uncommitted developer WIP) is exactly the kind of thing that should not just quietly sit in a per-tranche audit's
parked list.

**Recommendation [WORKER REC]**: operator confirms whether the bundle was relocated somewhere durable before removal
(check any backup/GCS location it might have been copied to, and whether slot 3 was reset/recreated around
2026-07-30/31). If no durable copy exists, mark the loss explicitly in this doc (rather than silently closing the todo)
so nobody later assumes the 10 stash entries are still recoverable. Either way, the open `[OPERATOR] P2` delete todo
(lines 112-119) can be marked resolved-by-fact (directory is gone) but its stated done-when about the bundle surviving
is NOT met as written — do not flip it to `[x]` without addressing that gap explicitly.

### 12. Methodology caveat, corroborated independently by 7+ of today's 45 Phase-1 agents: a large share of "orphaned" verdicts are for docs that are already self-dispatched and do not need batch7 treatment

Of today's 42 orphaned-verdict docs (32 `orphaned_partial_coverage` + 10 `orphaned_never_touched`), **15 are already
`assigned_vm: planning` + `status: active`/`open`** (`self_dispatched` per `generate_ag_closeout_audit_candidates.py`'s
own coded definition): `codex_vs_repo_docs_ssot_audit_2026_06_01.md`,
`bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md`,
`bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`,
`bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md`,
`ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md`,
`cve_affected_pinned_deps_remediation_2026_06_18.md`,
`deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`,
`deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md`,
`deployment_service_execution_service_plural_naming_gaps_2026_08_03.md`,
`destructive_rm_guardrail_regex_false_positive_on_hyphenated_filenames_2026_07_31.md`,
`migration_vm_hung_detection_monitoring_gap_2026_07_27.md`,
`na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md`,
`quickmerge_stage5_push_loses_fast_forward_race_under_high_churn_2026_07_27.md`,
`unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md`, `vm_launcher_setup_script_freshness_gap_2026_07_31.md`.

`regen_backlog_from_plan.py` globs `plans/active/issues/*.md` (and plan docs) DIRECTLY for `assigned_vm: planning`
checkboxes — a doc does not need to be cited by a satellite batch to be dispatchable, it only needs its own frontmatter
set correctly. This skill's covering-doc-citation test (the mechanism used to compute
`orphaned_partial_coverage`/`orphaned_never_touched`) answers "is this doc mentioned by the closeout/batch machinery,"
which is a genuinely different question from "is this doc's remaining work actually flowing into live dispatch." For a
self-dispatched doc, the honest answer to the second question is usually yes, independent of the first. **Not a
hypothetical concern**: 7 of today's 45 Phase-1 agents flagged this exact caveat unprompted while classifying their own
assigned doc (`migration_vm_hung_detection_monitoring_gap_2026_07_27.md`,
`ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md`,
`deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`,
`destructive_rm_guardrail_regex_false_positive_on_hyphenated_filenames_2026_07_31.md`,
`na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md`,
`unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md`, `vm_launcher_setup_script_freshness_gap_2026_07_31.md`)
— convergent, independent corroboration rather than one agent's isolated opinion.

**Recommendation [WORKER REC]**: `generate_ag_closeout_audit_candidates.py`'s `--json` output already computes
`self_dispatched` per candidate — a small enhancement to also print a `self_dispatched_orphan_count` alongside
`never_cited_count` would let every future run (and its human reader) separate "genuinely needs a batch to become
dispatchable" from "already dispatching on its own, just not cited by the closeout machinery" without re-deriving this
by hand each time. Not fixing the script here (a design/tooling-priority call, not a bounded today's-run fix), but
flagging clearly since it changes how the headline orphan count should be read: **of the 42 raw "orphaned" docs, only 27
are not already self-dispatching.**

### 13. Two possible batch7 candidates identified, NOT drafted this run — need dedicated scoping first

Neither is conflict-clear enough, as scoped today, to draft directly without a closer independent read:

- **`CITE_RE` self-referential citation blind spot** (`generate_ag_closeout_audit_candidates.py`, carried forward from
  finding 5, 2026-08-01, still unchanged) — the citation regex counts ANY dated-filename mention anywhere in a covering
  doc's text (including Progress-Log narrative prose) as a real citation, which is exactly why several docs above show
  "cited but not closed" rather than correctly reading as never-cited. Hardening this needs a design decision (e.g.,
  only count a mention inside an actual `- [ ]`/`- [x]` todo line, or within N lines of a `Source:` marker) that this
  run did not make — flagging for a dedicated look rather than guessing the right rule.
- **`repo_scripts_governance_audit_2026_06_18.md`'s L208 (add `scripts/` to the `ruff-lint` pass in `base-service.sh`)
  and L213 (extend the TID251/`os.getenv` ratchets to `scripts/`)** — read by today's Phase-1 agent as untouched by
  every covering doc and potentially bounded/mechanical, but I have not independently run this skill's own
  conflict-check (grep all 13 covering docs + corpus-wide for the specific files/ratchets these would touch) myself
  before considering them safe to draft — that verification did not happen this run. The same doc's L159/L363 item
  (build `check_script_lifecycle_markers.py`) is explicitly NOT ready (its own fleet measurement found 96+136
  pre-existing violations that would make the checker immediately gate-red if wired now) — a caution that the same doc's
  other "looks bounded" items deserve the same scrutiny before batching, not less.

Per the skill's own "iterative drain, not a one-shot" methodology and its explicit allowance to report a residual as
"needs direct human action, not another batch" rather than forcing one: today's run does not draft
`infra_satellite_ao_dispatch_batch7`. Of the 42 raw orphaned docs, 15 are self-dispatched (finding 12), and of the
remaining 27, every single one is either operator-gated, time-gated, design-preference-gated, conflict-gated against an
active in-flight plan, or this skill's own prior-audit meta-output (a parked-findings doc auditing itself) — see the
full per-doc breakdown carried in this run's `/done` evidence and chat report. These two items are the only "maybe, with
more scoping" candidates found; neither justifies a batch draft on today's evidence alone.

## Carried forward from 2026-08-02 (re-verified live this run)

5 of the 6 items carried into yesterday's doc are now **RESOLVED**:

1. **`codex_violations_ratchet_to_five_2026_06_10.md`'s `delta_proxy_repricer.py` checkbox** — **RESOLVED**, now `[x]`
   (execution-service wiring shipped, per that doc's own 2026-08-02 na-eligibility-audit entry).
2. **`docs_reconcile_autonomous_sweep_2026_07_30.md`'s P0-A (`check_codex_doc_freshness.py` 2026-08-15 cliff)** —
   **RESOLVED**, operator ruled (option A, staged cohort-split re-review); independently re-verified this run
   (`grep -rl "last_reviewed: 2026-05-17" codex/` → 0 matches).
3. **`issues/qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md`'s `asset_group: [meta]`** —
   **RESOLVED**, retagged `[ao]` 2026-08-02 (operator ruling, na-eligibility-audit item 19 option A).
4. **`issues/git_health_not_clean_since_pinned_constant_2026_07_27.md`'s dual `[infrastructure, meta]` tag (finding 8)**
   — **RESOLVED** by a broader retag: now `[ao, meta]` (2026-08-02, `/ag-closeout-audit cross-cutting`, operator-ruled)
   — the doc left the infra tranche entirely, correcting both the redundant-tag issue and its underlying
   tranche-ownership mistag in one move.
5. **`infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s todo 1 (bare-name wording fix)** — **RESOLVED** independently
   by today's `docs_reconciler` autonomous sweep before batch6 was ever dispatched; fixed in-line this run (marked
   `[x]`, shipped `unified-trading-pm` LDR) rather than parked, since batch6 is still `status: draft` and safe to edit
   directly.

1 item is **still open, unchanged**:

6. **`issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`'s `asset_group` mistag**
   (`[infrastructure]` should be `[ao]`) — still not retagged; still parked as a tranche-level
   `BLOCKED-OPERATOR-DECISION` in `infra_consolidated_closeout_2026_07_25.md`'s own Progress Log with 3 unresolved
   options (A/B/C). Not this skill's to fix directly (owning-tranche-writes-only rule — only the `ao` tranche's own run
   may retag it).

**Ledger**: 4 new parked findings this run (10, 11, 12, 13), 4 entries written above — balanced. Plus 1 already- shipped
fix recorded in-line (batch6 todo 1) and 6 carried-forward items re-verified (5 resolved, 1 still open) — not counted as
"new parked findings" since they were already tracked in a prior day's doc.

## Todos

- [ ] [OPERATOR] P1. **Re-apply `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s `assigned_vm` flip correctly**
      (finding 10) — set line 39 to `assigned_vm: planning` (currently blank), then verify the `[BACKEND] P3` todo
      actually reaches the live AO backlog. Second attempt at the same finding-7 fix; OPERATOR CONFIRMATION NEEDED again
      since this is a live dispatch-state change on an active plan.
- [ ] [OPERATOR] P1. **Investigate the missing stash-backup bundle** (finding 11) — confirm whether
      `instruments-service-agentwork-sports-2026-07-13-stashes.bundle` (67.8 MB, previously verified to contain all 10
      stash SHAs) was relocated to a durable location before `.tabs/3/stash-bundles/` disappeared, or whether this
      represents an unrecovered loss of 10 real stash entries. Update
      `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md` with the outcome either way —
      do not silently flip its delete todo to done without addressing the bundle discrepancy.
- [ ] [DOCS] P3. **Consider a `self_dispatched_orphan_count` addition to `generate_ag_closeout_audit_candidates.py`**
      (finding 12) — segments the headline orphan count so future runs (and readers) don't overstate the batch-needed
      backlog. Design/tooling-priority call, not urgent.
- [ ] [DOCS] P3. **Scope + conflict-check the 2 flagged batch7 candidates** (finding 13: `CITE_RE` hardening design;
      `repo_scripts_governance_audit_2026_06_18.md`'s L208/L213) before any future run drafts them — neither is ready to
      batch as-is.

## Progress Log

- **2026-08-03** — `/ag-closeout-audit infra` run (autonomous mode, scheduled daily run, slot 12). Re-derived the
  candidate set (13 covering docs, 45 members — up from 43 on 2026-08-02 — 2 never-cited). Re-checked all 9
  carried-forward findings live before fresh triage (5 resolved, 1 still open, 3 superseded by this run's own new
  findings 10-11). Ran a 45-agent Phase 1 Workflow over the full candidate set (0 errors, 0 empty results). Verified
  finding 10 (batch3 `assigned_vm`) via direct raw-file read + `git log -p`, not doc prose. Verified finding 11 (missing
  stash bundle) via a real-host `find` sweep across all of `/home/ubuntu`, confirming this is the genuine long-running
  shared host (uptime 5d+), not an ephemeral sandbox. Fixed `infra_satellite_ao_dispatch_batch6_2026_08_02.md` todo 1
  in-line (already-resolved-elsewhere, shipped `unified-trading-pm` LDR) since it is still `status: draft` and safe to
  edit directly. Did not draft `infra_satellite_ao_dispatch_batch7` — of 42 orphaned docs, 15 are already
  self-dispatched (finding 12) and the remaining 27 are each operator/time/design/conflict-gated or this skill's own
  prior-output meta-docs; the 2 "maybe" candidates (finding 13) need dedicated scoping before a future run drafts them.
  **Ledger**: 4 new parked findings + 1 in-line-shipped fix + 6 re-verified carry-forwards, 4 entries written above —
  balanced.

- **na-eligibility-audit 2026-08-03** (infra tranche, dispatch agt-a41abf): **KEEP-NA, valid.** First verdict for this
  doc. Read end-to-end; `grep -cE '^- \[ \]'` = **4**, matching this verdict's item count. Todos 1-2 are explicitly
  `[OPERATOR]`-tagged with a stated reason a worker cannot self-resolve (todo 1: re-applying a live `assigned_vm` flip
  on an active plan needs operator confirmation each time, not a standing approval; todo 2: whether the missing stash
  bundle was durably relocated or genuinely lost is external knowledge no worker here has). Todos 3-4 are `[DOCS] P3`
  but both explicitly self-describe as NOT yet bounded: todo 3 is framed "Design/tooling-priority call, not urgent" (a
  `Consider adding...` suggestion, not a decided spec); todo 4 explicitly states "neither is ready to batch as-is" and
  one half needs "a design decision... that this run did not make." None of the 4 clears the bounded/deterministic bar
  for RECLASSIFY. No other action.
