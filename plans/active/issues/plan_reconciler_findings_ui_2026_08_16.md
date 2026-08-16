---
doc_type: issue
title: "plan_reconciler findings — ui tranche, 2026-08-16 (dispatch agt-8fc5a6)"
summary: >-
  Fourth sharded plan_reconciler run over the `ui` asset_group tranche. Full 25-doc inventory computed via
  generate_tranche_doc_inventory.py, 0 grace-blocked (all docs last-touched 12.6h+ before this run). Phase -1
  self-reconciliation resolved/archived the two prior ui-tranche findings docs (2026-08-10, 2026-08-11). 4-hunter
  fan-out covered the remaining 24 docs; 5 done-but-unchecked flips, 5 contradiction/staleness fixes, 3 zero-checkbox
  conversions, 2 AO-dispatch-readiness fixes, 2 archivals, 1 archive_exempt addition, 3 corpus-referrer repoints, and 1
  technical question resolved via direct code-reading (gate_on_depends semantics — no fix needed, mechanism is
  correct). Zero operator escalations this run — every candidate resolved to either HARD-evidenced auto-fix or
  confirmed-still-genuinely-open.
status: open
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, ui, 2026-08-16]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md,
    /plans/archive/2026_08/issues/plan_reconciler_findings_ui_2026_08_11.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: ui_developer
drift_direction: none
locked_by:
locked_since:
resolved_by:
source: "plan_reconciler dispatch agt-8fc5a6 — sharded ui tranche run 2026-08-16"
depends_on: []
---

# plan_reconciler findings — ui tranche, 2026-08-16

> **Run**: dispatch `agt-8fc5a6`, sharded to `tranche=ui`. Fourth `/plan-reconcile ui` run. Full corpus write access —
> 0 of 25 tranche docs grace-blocked.

## Coverage (hunters / batches / docs)

- **Hunters**: 4 parallel read-only hunters (batches A-D, `model=sonnet`), one transient rate-limit failure on batch D
  (resumed successfully, no data lost).
- **Docs read in full**: all 25 `ui`-tranche docs per `generate_tranche_doc_inventory.py --tranche ui` — batch A (7:
  epic hub + AO satellite batches 1/3/4 + their finalize docs), batch B (7: deployment-api/registry docs), batch C (7:
  data-status + observability docs), batch D (3: misc issues + the 2026-08-10 prior findings doc), plus
  `plan_reconciler_findings_ui_2026_08_11.md` read directly by the orchestrator (Phase -1). Also read in full by the
  orchestrator: `deployment_api_unauthenticated_prod_p0_2026_08_10.md` + its finalize plan (P0 security escalation, 651
  + 86 lines), and cross-tranche referrer docs (`cross_cutting_consolidated_closeout_2026_07_25.md`,
  `ag_closeout_audit_cross_cutting_parked_2026_08_06.md`) for archival-referrer hygiene.
- **Phase -1 (this skill's own prior output)**: `plan_reconciler_findings_ui_2026_08_10.md` and
  `..._ui_2026_08_11.md` both reconciled against fresh state and archived this run (see Archive candidates below) —
  neither had any genuinely-open item left once cross-checked against 2026-08-16 corpus state.
- **Independent live verification performed** (not hunter-trusted): `gcloud run services describe
  uts-shared-deployment-api` (confirmed `DISABLE_AUTH: 'false'`, `API_KEY` bound via `secretKeyRef`); `git log`/`git
  show` on 2 disputed commit shas; direct read of `agent-orchestrator/server/regen_backlog_from_plan.py`'s
  `_wire_gate_on_depends_prereqs` to resolve a dispatch-readiness question via code, not inference.
- **Candidates surfaced**: ~20 across done-but-unchecked, contradictions, zero-checkbox conversions, and
  AO-dispatch-readiness. Every flip/contradiction candidate was either independently re-verified by the orchestrator
  (the highest-stakes ones: P0 security doc live state, Track4's 5 archived source docs, the sha citation) or carried
  hunter-performed live/git verification strong enough to act on directly (small mechanical corrections, sha/path
  fixes). No candidate was applied on hunter-say-so alone.

## Flips verified

1. `plans/active/ui_consolidated_closeout_2026_07_30.md` — Track 4 close-out `[REVIEW] P1` todo. HARD evidence: all 5
   Track 4 Sources independently confirmed archived + `status: resolved` (read in full:
   `deployment_ui_nav_consolidation_2026_07_17.md`, `deployment_ui_l2_smoke_gate_red_2026_07_17.md`,
   `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`, `deployment_api_live_mock_parity_2026_07_17.md`,
   `deployment_api_sigabrt_crash_loop_2026_07_24.md`). Flipped `[ ]`→`[x]`.
2. `plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md` — 3 remaining `[BACKEND] P1` todos (API
   key issuance, caller audit, guard flip). HARD evidence: the successor P0 plan
   (`deployment_api_unauthenticated_prod_p0_2026_08_10.md`) shows all corresponding steps `[x]` with commit shas +
   live verification, independently re-confirmed via a fresh `gcloud run services describe` this session
   (`DISABLE_AUTH: 'false'`, `API_KEY` bound). Flipped all 3.
3. `plans/active/issues/plan_reconciler_findings_ui_2026_08_11.md` — the multiline-frontmatter tranche-inventory todo.
   HARD evidence: `scripts/plan-hygiene/generate_tranche_doc_inventory.py` exists and was run live this session,
   returning 25 docs (matching the doc's own named examples). Flipped, then archived (see below — flipping this left
   the doc with zero open items).

## Contradictions

1. **[FIXED]** `plans/active/ui_satellite_ao_dispatch_batch4_2026_08_13.md` todo 6 cited the wrong commit sha
   (`deployment-ui@9d5ad0d105`, a same-topic mock-API bugfix) for the CloudBuildsTab port. Verified via `git log`: the
   real port commit is `b3300a71a7` ("feat(ui): port manual-trigger build action into /ops/artifacts Pipeline tab,
   retire CloudBuildsTab"), matching the todo's own text and a sibling doc's citation of the same commit. Corrected.
2. **[FIXED]** `plans/active/ui_satellite_ao_dispatch_batch4_2026_08_13_finalize.md`'s header banner still said "the
   batch itself stays `status: draft`" — stale since 2026-08-13 (batch4 was operator-approved same-day and has since
   shipped all 11 todos). Added a correction note.
3. **[FIXED]** `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md`'s `ui` orphan-candidate list still
   claimed `deployment_api_prod_disable_auth_true_2026_08_06.md`'s "4 fix steps still open as of 2026-08-08" —
   provably wrong per Flip #2 above. Corrected in the same edit that repointed this doc's dangling reference to the
   now-archived block-list-parity doc.
4. **[FIXED]** `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md` carried 2 banners (2026-06-16,
   2026-07-28) both asserting "the 3 UI items below stay formally unticked" — stale since 2026-08-14, when a fresh
   `pw:L2` re-run (450/450) closed the cited blocker and all 3 items were checked with their own dated evidence.
   Added a correction banner (append-don't-replace — left the original banners as historical record).
5. **[FIXED]** `plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md`'s Filed item 5 claimed the corpus-wide
   `locked_by` placeholder question's "items 1-2... remains separately open" — stale: item 1 (the auto-clear ruling)
   was resolved 2026-08-15 by a sibling `ao`-tranche session this `ui`-tranche doc had no visibility into; only item 2
   (the actual clearing script) remains open. Corrected the cross-reference (that doc itself is `asset_group: [ao]`,
   outside this run's write-scope — not edited directly).

**Resolved via code-reading, not a contradiction (no fix needed):** whether `gate_on_depends` checks only a plan's
"named" todos or every currently-open one (raised by a hunter as an ambiguity in
`deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md`'s gating). Read
`agent-orchestrator/server/regen_backlog_from_plan.py::_wire_gate_on_depends_prereqs` directly: it wires on the
upstream plan's actual currently-open backlog tasks (every `- [ ]` produces one), not a hardcoded subset — so the
finalize plan is correctly held open by the P0 plan's 2 remaining follow-up todos. No drift; the mechanism works as
designed.

## Doc-drift

None routed this run (no codex-alignment drift found requiring an operator ruling).

## Hygiene fixes

- `deployment_api_unauthenticated_prod_p0_2026_08_10.md` — retagged one todo `[INFRA]`→`[OPERATOR]` (its own text
  confirms it needs sudo/root, which no AO worker container has).
- `deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md` — added `sequential: true` (todo 3's prose-only
  "once the above verify clean" ordering had no machine gate; small 4-todo doc, negligible parallelism cost).

## Filed (zero-checkbox → tracked todo conversions)

1. `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md` — the denominator-freshness/coverage-%
   staleness trust-annotation, hand-off'd in prose from `consolidator_throughput_backlog_monitor_2026_07_09.md`
   2026-07-10 ("HANDED to Ikenna (data-status tab)"), never tracked as a checkbox anywhere in the corpus (fresh
   corpus-wide grep confirmed). Added as a new `[UI] P3` todo.
2. `plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md` — `cursor-configs/skills/plan-reconcile/SKILL.md`'s
   stale opus-dispatch-default claim (contradicts the current sonnet-5 default) was flagged by that doc's own
   Doc-drift #4 (2026-08-10) as "cannot fix, outside `plans/**`" but never converted into a tracked `- [ ]` — a
   violation of the corpus's own "every follow-up is a todo, never prose" rule. Added the todo (still not fixed
   directly — genuinely outside this skill's write-scope, needs a human/operator session).
3. `plans/active/deployment_api_unauthenticated_prod_p0_2026_08_10.md` — the "Google sign-in not yet independently
   verified" retest, real remaining work sitting only in a Progress Log paragraph. Added as a new `[OPERATOR] P3`
   todo.

## Archive candidates (operator review)

1. `plans/active/issues/unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md` — **ARCHIVED**. 0 open
   todos (sole todo done + runtime-verified 2026-08-09); its `archive_exempt: true` existed only because of a
   corpus-wide archival-mechanism deadlock — independently re-verified this session that BOTH of the deadlock doc's
   own conditions are now closed (`status: resolved`, both remediation todos `[x]`, operator-ruled carve-out shipped
   `unified-trading-pm@d765b4cfb1`). Moved to `plans/archive/2026_08/issues/`; 2 corpus referrers repointed
   (`cross_cutting_consolidated_closeout_2026_07_25.md`, `ag_closeout_audit_cross_cutting_parked_2026_08_06.md`).
2. `plans/active/issues/plan_reconciler_findings_ui_2026_08_11.md` — **ARCHIVED** (this skill's own prior findings
   doc, per Phase -1's explicit "archive once genuinely resolved" rule). Its sole todo flipped (Flip #3 above); all 4
   of its own "Deferred to next run" items independently confirmed resolved by this session's work (the tranche
   inventory fix, this session's own contradiction sweep, a fresh batch3-todo-3 adjudication, and re-checking the
   2026-08-10 doc's 4 operator-routed items). Moved to `plans/archive/2026_08/issues/`; 1 formatted corpus referrer
   repointed (`ui_satellite_ao_dispatch_batch4_2026_08_13.md`'s `related:` list).

**Archive-exempt added (not archived — a distinct doc, still genuinely blocked on other work):**

- `plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md` hit 0 open todos after Flip #2, which
  would otherwise make it a mechanical archive candidate — but its full archival (independent re-verification ritual
  + corpus-referrer repoint) is explicitly and deliberately owned by
  `deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md`'s own still-open todos 1-3. Set `archive_exempt:
  true` with a Progress Log reason rather than preempting that finalize plan's review.

## Refuted (dropped by verify)

1. **batch3 todo 3 "VM origin correction" — hunter-adjudicated as genuinely still open, NOT moot.** A prior
   (2026-08-11) run had left this ambiguous ("SOFT-evidence moot, no HARD verification"). This run's batch A hunter
   re-investigated with fresh eyes: read the archived target doc in full and found the original attribution was never
   corrected, while the correcting session's own first-person evidence ("this session ran the launch command at that
   exact timestamp") is stronger than the archived doc's inferential evidence. Confirmed still genuinely open — no
   flip, no moot-closure. Left as-is in `ui_satellite_ao_dispatch_batch3_2026_08_09.md`.
2. **`artifact_pipeline_observability_2026_07_17.md:648-649` checkbox text over-claims scope vs. the actual (correctly
   narrower) `deployment-api@3f13e4435e` commit** — a documentation-completeness nit, not a correctness error (the
   underlying "dead code deleted" claim is true for what was actually dead). Deprioritized as P3, not fixed this run.
3. **`data_status_tab_and_downloads_remediation_2026_06_16.md`'s 2 na-eligibility-audit Progress Log entries citing
   `locked_by: live-defi-rollout`, vs. the doc's actual empty `locked_by:` field** — matches the ALREADY-KNOWN,
   ALREADY-TRACKED corpus-wide `locked_by` placeholder bug (`locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`,
   `asset_group: [ao]`). Not a new finding, not ui-tranche-scoped to fix — will self-resolve once that doc's own
   `[BACKEND] P1` corpus-wide clearing script lands.

## Plans not reached

None — all 25 `ui`-tranche docs were read in full (24 by hunters, 1 by the orchestrator directly). 2 cross-tranche
referrer docs were also read (for archival hygiene) but are outside this tranche's own scope.

## Phase 5.9 NO-MISS LEDGER

- **routed_to_operator**: 0 (no `/blocked` questions this run — every candidate resolved to either a HARD-evidenced
  auto-fix or a confirmed-correctly-still-open state; the one technical ambiguity a hunter raised, `gate_on_depends`
  semantics, was resolved via direct code-reading, not escalated)
- **parked**: 0
- **routed == parked**: 0 == 0, trivially true
- **agent_skips enumerated**: 1 — batch D hit a transient API rate-limit mid-run (not a content skip); resumed via
  `SendMessage` and completed its full report with no data lost.
- **Conservation (archival moves)**: 2 docs moved, 2 sets of corpus referrers repointed (2 for the block-list-parity
  doc, 1 for the ui_2026_08_11 findings doc) — verified via fresh grep before each move, no dangling leftover.

## Corpus-wide hygiene (out of ui-tranche scope, noted for the record)

STEP 1's `run_hygiene_sweep.sh --ci` baseline showed 2 pre-existing hard failures — reference-path convention ratchet
and `assigned_vm:NA` corpus-size ratchet — both corpus-wide, and independently confirmed NOT to include any ui-tranche
docs (checked the actual violated-file lists: all DeFi/TradFi/CI/data-pipeline-scoped). Not this run's job to fix
(`/na-eligibility-audit`'s and other tranches' standing responsibility); every commit this run made was individually
`plan-hygiene`-pre-commit-clean (both pushes succeeded through the full hook chain with zero hygiene failures on the
staged files).

## Progress Log

- **2026-08-16 (plan_reconciler agt-8fc5a6)**: full run as described above. 2 commits landed on `live-defi-rollout`
  (`0474a1e0b6`, `df064366ce`), both independently verified reachable on `origin/live-defi-rollout` post-push. Working
  tree confirmed clean after each. No operator escalations needed.
