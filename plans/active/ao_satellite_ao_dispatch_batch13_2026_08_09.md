---
doc_type: plan
title:
  AO satellite AO batch 13 — continue the unsourced-operator-ruling-citation ratchet 53→0
  (agent_operating_framework_master epic)
summary: >-
  THIRTEENTH AO-dispatch batch for the `ao` topic tranche — a single-item satellite extraction from
  `operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`, produced by the same 2026-08-09 `/ag-closeout-audit
  ao` Phase 1 run as `ao_satellite_ao_dispatch_batch12_2026_08_09.md`. Split into its own batch rather than folded into
  batch12 because its source doc's `parent_epic` is `agent_operating_framework_master` (doc/plan-hygiene tooling), not
  `orchestrator_master` (the AO service itself) — per the naming-and-conflict-check SSOT's grouping rule, `parent_epic`
  is the clean axis for which batch an item belongs to (batch11 precedent). The extracted item continues ratcheting
  `check_plan_operator_ruling_evidence.py`'s `unsourced_ruling_baseline` from 53 toward 0 — the source doc's own
  2026-08-09 session already fixed 20 of the original 76 (fully verified, cited sources); the remaining 53 need the same
  per-entry verify-or-escalate treatment.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-13, satellite-docs, satellite-extraction, plan-hygiene]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch13_finalize_2026_08_09.md,
    /plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md,
    /plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md,
    scripts/quality_gates/check_plan_operator_ruling_evidence.py,
    /plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md,
  ]
source: >-
  `/ag-closeout-audit ao` Phase 1 run, 2026-08-09 (autonomous, scheduled dispatch `agt-41d860`, slot 10) — see
  `ao_satellite_ao_dispatch_batch12_2026_08_09.md`'s Progress Log for the shared provenance/conflict-check context; this
  item was independently flagged bounded/conflict-clear (zero hits across all 24 prior covering plans) before being
  split out on `parent_epic` grounds.
---

# AO satellite AO batch 13

> **`status: draft`** — pending operator approval, same convention as batch5-12: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

`operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md` carries 2 todos: the first (`[SCRIPT] P2`, making a
ratchet-raise loud rather than silent) is already `[x]` done. The second is the actual ratchet-continuation ask —
verify-or-escalate the remaining 53 unsourced-ruling citations, the same bounded, worker-determinable, no-remaining-
judgment-call shape as the 20 the source doc's own same-day session already closed. Split into its own batch (rather
than folded into `ao_satellite_ao_dispatch_batch12_2026_08_09.md`) solely because its source doc's
`parent_epic: agent_operating_framework_master` differs from batch12's `orchestrator_master` group — per
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2, `parent_epic` (not `asset_group`) is
the grouping axis. A 1-item batch is sanctioned by `task_template.md` §4 ("Fewer is fine; group RELATED items") and has
direct precedent (`ao_satellite_ao_dispatch_batch9_2026_08_08.md`, `ao_satellite_ao_dispatch_batch11_2026_08_09.md`,
both also 1 todo).

## Rules for every worker on this plan

- **Never invent a plausible citation.** Per the source doc's own text: a ruling recorded only in a chat session with no
  durable home, or a named-but-unverifiable source doc, must be recorded as genuinely unrecorded and escalated to the
  operator — not closed by guessing. This is the exact failure mode `check_plan_operator_ruling_evidence.py` exists to
  catch.
- Do not edit the source doc's checkbox beyond appending your evidence when done — the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch13_finalize_2026_08_09.md`) reconciles evidence back into the source
  doc.

## Todos

- [x] ✅ [SCRIPT] P2. **Ratcheted `check_plan_operator_ruling_evidence.py`'s `unsourced_ruling_baseline` from 52
      (measured 26 live violations at pickup — corpus moved between the plan's authoring and dispatch) → 4 (22 fixed).**
      Enumerated all 26 live violations via the checker's own `_violations_for_file`, applied the doc's own 3-class
      method per item: 1 reworded (`ao_open_issues_consolidated_close_out_2026_07_17.md:399`, "Operator ruling needed" →
      "Decision needed" — described absence, not a ruling); 21 fixed by citing a genuinely traceable source at the
      phrase — either an existing sibling doc found by grep (e.g. `agent_reply_cannot_address_a_different_role_...md` →
      cite `/plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md` item 4;
      `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` → cite
      `/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 row 46; 2 stale-path fixes in
      `pm_scripts_typecheck_debt_2026_06_11.md` pointing `plans/active/issues/...` → `plans/archive/issues/...`) or, for
      cases where the ruling is a dated/quoted primary record embedded directly in its own issue doc with no separate
      external doc, a same-doc self-citation naming that doc's own filename (the pattern the corpus's own
      `operator_ruling_record_ao_round5_apply_session_2026_08_08.md` already validates: "give future ruling sessions a
      home" — citing where the primary transcript actually lives is not fabrication).

      **4 remain, in two distinct classes, neither fixable within this todo's own scope:**
              (a) **2 genuinely unrecoverable** — both match the ALREADY-established precedent in this todo's own source doc
              (`operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`: "Not fixed, deliberately... Left in the 53"):
              `ao_open_issues_consolidated_close_out_2026_07_17.md:407` — the AO state-home ruling (2026-07-18, "keep AO
              backend state IN the repo"): grepped `codex/` for any doc recording this ruling (not just describing the
              resulting state) — 0 hits; `data_completion_defi_2026_07_15.md:223` — the DeFi-volatility-family removal
              (2026-07-17, "no DeFi options products"): same grep, 0 hits. Neither has a primary record anywhere in the corpus
              beyond the bare assertion itself; self-citing either would satisfy the gate mechanically while pointing at a doc
              that cannot confirm a human decided anything — the exact failure mode this gate exists to catch, per the source
              doc's own reasoning.
              (b) **2 fixed-then-REVERTED because their host file was already over the 1000-line hard cap before this todo
              touched it** (`check_line_caps.sh`'s precommit gate is an absolute per-staged-file bar, task_template.md §3
              finding J — editing an already-over-cap file blocks the commit regardless of who caused the overage):
              `ao_open_issues_consolidated_close_out_2026_07_17.md` (1014L committed, cap 1000 — both its violations, the
              reword above AND the state-home escalation, had to revert together since they share the file) and
              `sports_consolidated_closeout_2026_07_19.md:720` (1008L committed). A real fix (extract closed Progress-Log
              sections into an archive-bound history doc per finding J's remedy) is its own separate body of work, out of this
              todo's scope — filed as the new todo directly below rather than rushed here.
              Verified: `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py` → 4 (baseline 52, real shrink);
              baseline regenerated via `--baseline-write` → 4. `run_hygiene_sweep.sh --precommit` clean on all 20 shipped files
              (only pre-existing soft line-count warnings, no hard failures). Repo: unified-trading-pm. Source:
              `/plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md:103` (its `[SCRIPT] P2`
              item).

- [ ] [DOC] P3. **Trim `ao_open_issues_consolidated_close_out_2026_07_17.md` (1014L) and
      `sports_consolidated_closeout_2026_07_19.md` (1008L) under the 1000-line hard cap** — both blocked a
      `check_plan_operator_ruling_evidence.py` fix landing in the todo above (`check_line_caps.sh`'s precommit gate
      refuses ANY staged edit to an already-over-cap plan). Apply task_template.md §3 finding J's established remedy:
      extract the oldest fully-closed dated Progress-Log section(s) verbatim into an archive-bound
      `<slug>_history_<date>.md` (`status: complete`, `nature: record`, 0 open todos) and leave a one-line pointer
      behind — do NOT delete content, relocate it. Once both are back under 1000L, re-apply the 2 reverted
      operator-ruling-evidence fixes from the todo above (their exact replacement text is in this plan's git history —
      see the commit that reverted them). Done-when: both files ≤1000L, `check_line_caps.sh` clean on both, and
      `check_plan_operator_ruling_evidence.py`'s baseline drops from 4 → 2. Repo: unified-trading-pm.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09** — Authored by the same `/ag-closeout-audit ao` Phase 1/3 pass as
  `ao_satellite_ao_dispatch_batch12_2026_08_09.md` (dispatch `agt-41d860`, slot 10). Conflict-check: grepped all 24
  prior covering plans for `unsourced_ruling_baseline`/`check_plan_operator_ruling_evidence` — zero hits outside the
  source doc's own self-references and the already-resolved
  `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md` (cited by the source doc as the origin of this
  gate, not a competing claim on this ratchet-continuation work). Clear to extract. Split into its own batch solely on
  `parent_epic` grounds (see "Why this plan exists" above).
