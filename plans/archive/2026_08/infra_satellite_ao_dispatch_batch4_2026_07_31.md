---
doc_type: plan
title:
  Infra satellite AO batch 4 — fourth extraction for the infra tranche (single conflict-clear item, instruments-service
  `_solana_utils.py` line-cap split)
summary: >-
  Fourth AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-07-31). Batch3's own 2026-07-30 audit recommended treating the tranche as having reached its stop-iterating
  condition; this run's fresh Phase 1 pass re-checked the mechanically-narrowed candidate set (the
  `generate_ag_closeout_audit_candidates.py --tranche infra` never-cited set, now 9 docs after corpus growth since
  2026-07-30) plus one previously-"covered" doc (`codex_violations_ratchet_to_five_2026_06_10.md`) whose citation in
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md` turned out, on full re-read, to only partially cover its remaining
  work. Of everything read this run, exactly ONE item is a genuinely new, conflict-clear, bounded,
  never-drafted-anywhere candidate: splitting instruments-service's `_solana_utils.py` (1,068 lines, over the 900-line
  codex cap) — the file has grown since batch1 observed it at 1,016 lines and recommended a rewrite of the source todo,
  but no covering doc has ever actually drafted the split as dispatchable work. Everything else found this run is either
  already correctly gated (unchanged since batch1/batch3's own Deferred tracking), already shipped with a stale
  source-doc checkbox (not new work — flagged separately for `/plan-reconcile`, not drafted here), or non-batchable per
  the skill's own taxonomy (see the parked-findings doc cited below for detail). This is a genuinely single-todo plan —
  per `task_template.md`'s single-todo carve-out (`check_finalize_plan_coverage.py`'s `_todo_count(...) <= 1` threshold,
  filtered on `assigned_vm: planning` regardless of `status`), no separate finalize plan is authored; the archival step
  is folded into this one todo's own "Done when", mirroring the archived `ci_satellite_ao_dispatch_batch3_2026_07_30.md`
  precedent.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-4, plan-hygiene, codex-violations]
related:
  [
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/ag_closeout_audit_infra_parked_2026_07_31.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch3_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    instruments-service/instruments_service/reference_data/adapters/defi/_solana_utils.py,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-07-31 (ag_closeout_auditor scheduled worker, slot 13). Phase 0 re-derived the
  covering set (hub + batch1/finalize + batch2/finalize + batch3(draft)/finalize(draft) + infra_capture_and_devops_
  leftovers/finalize — 9 covering docs) via `generate_ag_closeout_audit_candidates.py --tranche infra`. Phase 1 ran a
  10-agent Workflow: the 9 currently-never-cited docs (8 turned out self-dispatched via `assigned_vm: planning`, 1
  genuinely orphaned but non-batchable per the guardrail-blocked-operator-only taxonomy) plus a targeted re-read of
  `codex_violations_ratchet_to_five_2026_06_10.md` (added because its own text flagged a since-resolved dependency).
  That doc's full Phase 1 read found 5 of its 7 open items genuinely uncovered despite two "next batch" promises (batch2
  2026-07-27, batch3 2026-07-30) neither of which picked them up; of those 5, the `_solana_utils.py` split is the only
  one that is both conflict-clear (verified: no other active plan across any tranche references this file by path) and
  not already resolved elsewhere (the `delta_proxy_repricer.py` wire-in it sits beside turned out to be ALREADY SHIPPED
  — `execution-service@89fbf99d` — with a stale checkbox, not open work). The other 3 uncovered items (pip-audit bumps,
  domain-client base-gate retarget, Phase-3 schema-provenance migration) remain correctly gated by batch1's own
  pre-existing Deferred classification (the `base-service.sh`/`base-library.sh` serialization ruling and the TOO-LARGE
  taxonomy respectively) — unchanged, not re-drafted here.
---

# Infra satellite AO batch 4

> **✅ ARCHIVED 2026-08-08** — single todo complete. `_solana_utils.py` (1,068L) split into `_solana_utils.py` (815L)
>
> - `_solana_pool_discovery.py` (271L); instruments-service@06791d0e; 5,234 tests green. Source doc checkbox flipped
>   (`codex_violations_ratchet_to_five_2026_06_10.md` P3). Archived under `plans/archive/2026_08/`.

## Why this is a single-todo plan with no finalize twin

`task_template.md` §4's finalize-plan-coverage rule requires a gated finalize twin for an `assigned_vm: planning` plan —
EXCEPT the single-todo carve-out, which `scripts/quality_gates/check_finalize_plan_coverage.py` implements literally
(`_todo_count(...) <= 1`, filtered on `assigned_vm: planning` regardless of `status`, so a `draft` plan with exactly one
todo still qualifies). This plan has exactly one todo, so the archival/source-checkbox-reconciliation work that a
finalize twin would normally do is folded directly into that todo's own "Done when" clause instead — the same shape
`ci_satellite_ao_dispatch_batch3_2026_07_30.md` used (now archived, `status: complete`).

## Conflict check performed before drafting

- **`instruments_service/reference_data/adapters/defi/_solana_utils.py`** — `rg` across ALL of `plans/active/` (not just
  infra-tagged docs) for the file's basename and its full relative path returns exactly 3 hits:
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md` (an OBSERVATION only — "the only genuine residual named in the
  doc," recommending the source doc's own todo be rewritten, never drafting the split itself),
  `codex_violations_ratchet_to_five_2026_06_10.md` (the source doc, `[CODE] P3`, still open), and
  `issues/defi_adapter_dead_code_audit_2026_07_24.md` (an UNRELATED topic — confirms the file is "actively imported by
  10 sibling adapters + `engine/orchestrator/__init__.py`," i.e. NOT dead code — orthogonal to whether it should be
  split for size, not a competing claim on the split itself). Zero real conflict.
- **Recent git history** (`git log --oneline -5` on the file) shows only feature commits (adapter additions/removals, a
  UAC venue-launch-dates threading fix, a codex-compliance QG-debt pass) — no in-flight split, no WIP toward one.
- **`check_delete_vm_launch_gating.sh` shape** — the todo performs no GCS delete, no `--apply`, no VM launch. No
  `[OPERATOR]` tag or delete-safety citation required.

## Todos

- [x] ✅ [CODE] P3. **Split instruments-service's `_solana_utils.py` under the 900-line codex cap** —
      instruments-service@06791d0e. `_solana_utils.py` (1,068L) → `_solana_utils.py` (815L) +
      `_solana_pool_discovery.py` (271L); all callers/tests updated; QG green (5,234 pass); source doc checkbox flipped
      @`codex_violations_ratchet_to_five_2026_06_10.md`. Original (currently 1,068 lines, up from 1,016 when
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md` first observed it 2026-07-26 — confirm the live count with
      `wc -l` before starting in case it has grown further). Identify natural seams (e.g. RPC-based creation-timestamp
      resolution vs. the protocol-level floor-date fallback logic — read the module docstring and structure first rather
      than assuming this split) and extract into cleanly-named sibling modules under
      `instruments_service/reference_data/adapters/defi/`, preserving all existing public symbols' import paths (or
      updating every caller in the same unit if a symbol genuinely moves) — mirror the precedent split pattern used for
      `unified-api-contracts@da76afe1` (`partition_paths.py`, 1297→under 900L). Confirm all 10 sibling adapter callers
      plus `engine/orchestrator/__init__.py` still resolve correctly post-split (grep every import site first, then
      verify each one). **Then reconcile the source doc**: in `codex_violations_ratchet_to_five_2026_06_10.md`, flip the
      `_solana_utils.py` `[CODE] P3` checkbox `[x]` citing this todo's actual shipped commit sha (re-verify the sha
      resolves with `git show`, do not copy this todo's own text blind), and confirm whether that doc now has zero open
      todos (expected: no — the pip-audit, domain-client base-gate, and Phase-3 schema-provenance items stay genuinely
      open, correctly gated per `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own Deferred §2/§7/§17 — do NOT
      touch those three, do NOT archive the source doc). **Then archive this batch plan itself** (it will have zero
      remaining open todos) via the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — update every corpus-wide referrer of
      this plan's path (expected: none yet, this is a brand-new plan) before moving it. **Done when**: every resulting
      file from the split is ≤900 lines, `bash scripts/quality-gates.sh` is green in instruments-service with no new
      codex-compliance violations, all pre-existing callers/tests pass with unmodified behavior, the source doc's
      checkbox is flipped with a verified sha, and this batch plan is archived. Repo: instruments-service (split),
      unified-trading-pm (checkbox reconciliation + this plan's own archival). Source:
      `codex_violations_ratchet_to_five_2026_06_10.md` (line ~398-419).

## Codex SSOTs (read before executing this todo)

- `/codex/06-coding-standards/quality-gates.md` — file-size cap enforcement, how gates run
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol this batch
  ran before drafting
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step ritual this todo folds in
- `plans/active/task_template.md` §4 — the single-todo finalize-plan-coverage carve-out this plan uses

## Progress Log

- **2026-07-31** — Drafted by `/ag-closeout-audit infra` (Autonomous/AO-dispatched mode, scheduled daily run, slot 13).
  Phase 0 re-derived the current 9-doc covering set (batch1/batch2/batch3 all active-or-draft with gated/no-twin
  finalizes, plus the hub and `infra_capture_and_devops_leftovers`). Phase 1 ran a 10-agent Workflow over the 9
  currently-never-cited docs (per `generate_ag_closeout_audit_candidates.py --tranche infra`, corpus has grown to 32
  members) plus a targeted re-check of `codex_violations_ratchet_to_five_2026_06_10.md`. Found: 8 of the 9 never-cited
  docs are legitimately self-dispatched (`assigned_vm: planning`, not orphans by the skill's own tooling definition); 1
  (`stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md`) is a genuine orphan but is
  guardrail-blocked operator-only work, correctly non-batchable; `codex_violations_ratchet_to_five` has 5 of 7 open
  items genuinely uncovered, of which 3 remain correctly gated (unchanged) and 1 (`delta_proxy_repricer.py`) turned out
  to be ALREADY SHIPPED with a stale checkbox (flagged for `/plan-reconcile`, not drafted here). The remaining item —
  this batch's sole todo — is genuinely new, conflict-clear, and bounded. Left `status: draft` deliberately; the flip to
  `active` is the operator's call. Parked findings (the stale-checkbox discrepancies, the filesystem-vs-doc mismatch on
  the stash-clone deletion) are recorded in `issues/ag_closeout_audit_infra_parked_2026_07_31.md`, not here.
- **context-scout 2026-08-07**: populated context_scope (4 entries).
