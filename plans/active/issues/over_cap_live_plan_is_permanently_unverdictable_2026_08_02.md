---
doc_type: issue
title: >-
  An over-cap LIVE plan is permanently un-verdictable by /na-eligibility-audit (and /plan-reconcile, /ag-closeout-audit,
  /context-scout) — the 1000L hard gate blocks the verdict marker itself, so the doc is re-read in full on every run
  forever; the 2026-07-30 ruling only exempted ZERO-open-todo docs
summary: >-
  Measured live during the scheduled /na-eligibility-audit defi run 2026-08-02. lst_rate_honest_coverage_2026_07_21.md
  is 1001L — already over check_line_caps.sh's 1000L HARD cap BEFORE this run touched it — and has 6 open todos, so the
  2026-07-30 zero-open-todo archival exception does not apply. The gate's staged-file mode ("a file THIS commit touches
  must not be over its tier's cap, full stop") therefore refuses ANY edit, including the ~4-line dated
  `na-eligibility-audit YYYY-MM-DD` Progress Log verdict marker that Phase 0's incremental mode uses as its skip anchor.
  Net effect: the doc can never carry a marker, so every future na-eligibility-audit / plan-reconcile /
  ag-closeout-audit / context-scout run re-reads all 1001 lines from scratch, forever — the exact waste the 2026-07-30
  ruling was written to stop, just in the live-plan case it did not cover. This run verified the failure empirically
  (check_line_caps.sh exit 1 at 1019L with the marker added), reverted its edit, and extracted the one AO-eligible todo
  to defi_satellite_ao_dispatch_batch8_2026_08_02.md instead — which now has no way to annotate its own source doc's
  checkbox.
status: open
nature: issue
asset_group: [defi, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, na-eligibility-audit, incremental-mode, prose-trap, split-needed, blocked-operator]
related:
  [
    /plans/archive/issues/archive_candidate_docs_over_line_cap_blocks_edit_2026_07_29.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: 2026-08-02
author: unknown
last_updated: "2026-08-02"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: worsening-slowly
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  "scheduled /na-eligibility-audit defi run 2026-08-02 (autonomous, na_eligibility_auditor) — hit while trying to write
  a Phase-0 incremental-skip verdict marker into an in-scope doc"
context_scope:
  [
    /plans/archive/issues/archive_candidate_docs_over_line_cap_blocks_edit_2026_07_29.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/plan-hygiene/check_line_caps.sh,
  ]
---

# An over-cap LIVE plan cannot carry an audit verdict marker, so it is re-read forever

## What was measured (this run, not inferred)

1. `plans/active/lst_rate_honest_coverage_2026_07_21.md` is **1001 lines** at HEAD — already over the **1000L HARD cap**
   before this audit touched it. It has **6 open todos**, `status: active`, `assigned_vm: NA`, `priority: P0`.
2. Adding this skill's required dated Progress Log verdict marker (Phase 3's "write the dated Progress Log verdict
   marker ... even when nothing else changes — an audited-and-confirmed doc needs that marker or every future run
   re-reads it from scratch") plus a `last_updated` bump took it to **1019 lines**.
3. `bash scripts/plan-hygiene/check_line_caps.sh <that file>` then returns **exit 1**:
   `HARD lst_rate_honest_coverage_2026_07_21.md 1019L todos=21` →
   `❌ check_line_caps: 1 staged plan(s)/epic(s) over cap — split before committing`. Confirmed by direct execution, not
   by reading the script.
4. That staged-file mode is absolute by design — the script's own header: _"a file THIS commit touches must not be over
   its tier's cap, full stop (RULE-11 blast-radius safety)"_ — and it is wired into prek `--precommit`.
5. The **one documented exception** (operator ruling 2026-07-30, codified in the same header and in
   `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) is gated on **ZERO open todos** and on the
   commit being the archival move itself. With 6 open todos this doc does not qualify.

## Why this matters (it is the 2026-07-30 ruling's own stated rationale, unfixed for live plans)

The 2026-07-30 ruling exists verbatim because blocking an edit "left the doc `active` so every /plan-reconcile,
/ag-closeout-audit and /na-eligibility-audit run re-reads all 1509 lines of it forever." That is **exactly** the
situation here — the only difference is that this doc is a live plan with open work rather than a finished one, so the
exception does not reach it. The consequences compound rather than sit still:

- **Phase 0's incremental mode is permanently defeated for this doc.** No marker can ever land, so it is in scope on
  every single run of a job that fires every 2 hours. It is the most expensive doc in the defi tranche to read (1001L)
  and the only one guaranteed to be re-read every time.
- **Duplicate-extraction risk is real, not theoretical.** This run extracted its Phase-3 `-test-`-bucket force/skip todo
  to `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md` after a clean conflict-check, but could
  not annotate the source checkbox to cite that extraction. A future run reads the same unannotated open checkbox and
  has nothing in the doc telling it the work is already dispatched — the precise failure the KEEP-NA-STALE citation
  mechanism exists to prevent.
- **It is not one doc.** Any `plans/active/*.md` over 1000L with ≥1 open todo has the same property. This is the third
  recorded instance of the over-cap-blocks-edit class after the two in
  [`/plans/archive/issues/archive_candidate_docs_over_line_cap_blocks_edit_2026_07_29.md`](/plans/archive/issues/archive_candidate_docs_over_line_cap_blocks_edit_2026_07_29.md)
  (both of which were the zero-open-todo flavour and are now closed by the 2026-07-30 ruling + archival) — this is the
  first LIVE-plan instance, which that issue explicitly did not cover.

## Decision needed (operator) — options, with a recommendation

This is a policy call about a hard gate, not something a worker can settle alone, which is why it is parked here rather
than acted on:

- **A [WORKER REC]: narrow the existing exception to cover an audit-marker-only edit.** Allow a commit whose diff to an
  over-cap `plans/active/*.md` is confined to appending a dated audit Progress Log line (and/or a `last_updated` bump) —
  the machine-checkable shape is "no `- [ ]`/`- [x]` line added, removed, or changed, and no net new section." This
  keeps the cap's real purpose (stop a LIVE plan growing into an unreadable hub) fully intact, since a marker cannot
  grow a plan's actual content, while restoring incremental mode. Smallest change, directly addresses the measured
  failure, and matches the 2026-07-30 ruling's own reasoning.
- **B: split `lst_rate_honest_coverage_2026_07_21.md` specifically** into a trimmed index/coordination doc under cap
  plus per-phase child docs wired via `depends_on`/`gate_on_depends` (the pattern the operator already ratified for
  `sports_consolidated_closeout_2026_07_19.md`). Fixes this one doc properly but is genuinely open-ended judgment about
  what goes where, leaves the general class unfixed, and the next over-cap live plan re-raises it.
- **C: promote it to a real epic** in `plans/epics/` (2000L tier). Cheapest mechanically, but it is a phase-structured
  build plan, not a long-lived master tracker — this would misuse the epic tier to dodge a cap, exactly what the
  2026-07-24 two-tier ruling was written to stop. Not recommended.
- **D: accept the re-read cost.** Honest but strictly worse over time, and it keeps the duplicate-extraction risk live.
- **Other:** operator custom direction.

## Todos

- [x] ✅ [SCRIPT] P2. **RULED 2026-08-06 (operator), option A [WORKER REC]: narrow the existing exception.** `[SCRIPT]`
      tag (was `[OPERATOR]`), AO-dispatchable — allow a commit whose diff to an over-cap plan is confined to appending a
      dated audit marker / `last_updated` bump (no checkbox lines touched, no net new content) through the line-cap
      gate. **BLOCKED-OPERATOR-DECISION** — rule on A/B/C/D above. A is a change to a hard quality gate's policy
      (`scripts/plan-hygiene/check_line_caps.sh` + its codex SSOT), which is not a worker-determinable outcome. Operator
      ruled option A 2026-08-06. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P2. Once ruled: if A, implement the marker-only carve-out in `scripts/plan-hygiene/check_line_caps.sh`
      (diff-shape check: no checkbox lines touched), update
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "The line-cap does NOT block archival of
      an already-done doc" to state the live-plan marker case alongside it, and add a regression test. If B, author the
      split. Then, either way, land the deferred `/plans/active/lst_rate_honest_coverage_2026_07_21.md` Phase-3
      annotation citing `defi_satellite_ao_dispatch_batch8_2026_08_02.md`, plus that doc's 2026-08-02 KEEP-NA verdict
      marker (both drafted and reverted this run — full text in the Progress Log below). Implemented
      `unified-trading-pm@d4f7fab9d8` (2026-08-02 — **CORRECTED 2026-08-12 `/plan-reconcile`**: was a literal unfilled
      `<sha>` placeholder dated "2026-08-07"; filled from `git log` on `scripts/plan-hygiene/check_line_caps.sh` — the
      small-marker-append carve-out landed in commit `d4f7fab9d8` ("docs(plans): apply operator rulings on 2026-08-02
      scheduled-audit-batch operator-decision queue..."), dated 2026-08-02, not 2026-08-07). (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. Report how wide the class is: list every `plans/active/*.md` over 1000L with ≥1 open todo (the docs
      that are currently un-verdictable), so the fix's real blast radius is a measured number rather than this doc's
      single example. (repo: unified-trading-pm)

## Progress Log

- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): Filed while auditing
  `lst_rate_honest_coverage_2026_07_21.md`. That doc's audit was completed in full — verdict **KEEP-NA valid, MIXED**:
  of 6 open items, 1 (Phase 3's `-test-`-bucket force/skip proof) was conflict-check-cleared and extracted to
  `defi_satellite_ao_dispatch_batch8_2026_08_02.md`; the other 5 stay KEEP-NA valid (Phase 5 #1 CEX-spot Tardis backfill
  is blocked on the separate P0 `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` OOM bug and is Tardis-cap-1
  real-infra; Phase 5 #4 `lst_yields` backfill is an explicitly-held multi-year real-infra backfill whose Solana half
  already shipped; Phase 5 #2 DEX fill has VMs `-1`/`-2` still RUNNING per its own 2026-07-29 re-verify, so there is
  nothing to dispatch until they finish; Phase 6's two `[STRATEGY]` legs are money-path/PnL work with prod-NAV recompute
  operator-gated). **That verdict could not be persisted into the doc** for the reason this issue documents — it is
  recorded here instead so the audit result is not lost, and so whoever resolves the cap question can paste it back. The
  extraction itself is unaffected and stands: batch8 + its gated finalize twin were created normally.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged from prior scout — still accurate: the two
  prior over-cap-blocks-edit instances, the over-cap doc itself, and `check_line_caps.sh`).
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — all 3 open todos are gated on
  an explicit `[OPERATOR]` BLOCKED-OPERATOR-DECISION policy call (A/B/C/D on the line-cap hard-gate exception); nothing
  here is worker-determinable absent the operator's ruling. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a, same run, separate discovery): a FOURTH
  recorded instance of the over-cap-blocks-edit class hit while auditing `data_completion_defi_2026_07_15.md` — **1002L
  at HEAD, 50 open todos, `assigned_vm: NA`**, so neither the 2026-07-30 zero-open-todo exception nor this doc's own
  small-marker-append carve-out (operator ruling 2026-08-02, since shipped into `check_line_caps.sh`) could land the
  verdict marker. Root cause was more specific than the general "any edit is over cap" framing above: the
  small-marker-append carve-out DOES exist and DOES accept an insert-only, ≤10-line, zero-checkbox diff — but
  `prettier-autostage`'s mandatory whole-file `--write` pass (unconditional on any staged touch, no diff-scoping
  available) reformatted 3 unrelated pre-existing long-whitespace-run regions elsewhere in this specific file as a side
  effect, which alone pushed the diff to 49 insertions / 45 deletions and disqualified the exception (requires
  `DELETED == 0`). Confirmed empirically: reverted to HEAD, reapplied ONLY the 4-line marker, prettier reflowed the same
  3 unrelated regions again on the next staged attempt — this is deterministic, not a one-off. So the general class
  (A/B/C/D above) has (at least) two distinct sub-causes: (i) the hard cap itself with no exception path (the
  `lst_rate_honest_coverage` case), and (ii) an exception path that exists but a MANDATORY, non-scopable formatting hook
  can still defeat it on any file carrying pre-existing formatting debt (this case) — worth folding into whatever the
  eventual A/B/C/D resolution designs, since option A's proposed "diff-shape check" alone would not have saved this
  instance. Verdict (KEEP-NA valid — every remaining item gated on the still-open C0/C0f prerequisite, an operator/VM
  long-wall-clock launch, or independent judgment) is recorded in the audit's own commit message
  (`473cccf03`/`b381cbb11`) since it could not be persisted into the source doc; the doc's own content is unchanged from
  HEAD.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (governance-sweep reclassification pass)**: RECLASSIFY,
  `assigned_vm: NA -> planning`. The A/B/C/D policy call on `check_line_caps.sh`'s over-cap edit exception was resolved
  this same session ("RULED 2026-08-06 (operator), option A [WORKER REC]: narrow the existing exception", retagged
  `[OPERATOR] -> [SCRIPT]"; a leftover "BLOCKED-OPERATOR-DECISION" body string in the same checkbox is stale prose, not a live re-block). All 3 remaining open todos are now worker-determinable: implement the diff-shape carve-out in `check_line_caps.sh`+ update the codex SSOT + a regression test, land the already-drafted deferred annotation, and a bounded corpus-wide report of over-cap live plans. Conflict-check cleared (no overlapping claim in`parent_epic:
  plan_hygiene_master`).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
