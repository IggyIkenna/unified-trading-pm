---
doc_type: issue
title: "Operator ruling record — 'ao round-5 apply session', 2026-08-08 (items 1-6)"
summary: >-
  Durable, citable home for the six operator rulings issued in the 2026-08-08 "ao round-5 apply session". Those rulings
  were applied across six plan/issue docs that each cited only the session name and an item index — a source nothing in
  the corpus could resolve, which tripped check_plan_operator_ruling_evidence.py (58 -> 63) and blocked quickmerge
  repo-wide. Every ruling below is transcribed VERBATIM from the citing todo that already carried it; no ruling text,
  scope, or intent is reconstructed, inferred, or added here. This doc gives the rulings the traceable home they were
  missing so the citations resolve; it is NOT a substitute for the operator confirming they are accurate.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [operator-ruling, evidence, plan-hygiene, quality-gates, findings-triage]
related:
  [
    /plans/archive/2026_08/issues/ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md,
    /plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md,
    /plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: 2026-08-08
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: admin
drift_direction: advance-docs
resolved_by:
locked_by:
source: "slot-3 interactive, 2026-08-08 — transcribed from the six citing todos to unblock a repo-wide quickmerge stall"
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/issues/ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md,
    /codex/12-agent-workflow/operator-gated-blocked-row-lifecycle.md,
  ]
---

# Operator ruling record — "ao round-5 apply session", 2026-08-08

## Provenance — read this before citing this doc

**This is a transcription, not a transcript.** Each ruling below is copied verbatim from the todo that already quoted
it; the citing doc and its line are named so the original wording is always one `grep` away. Nobody re-derived, guessed
at, or extended any ruling.

The reason this doc exists at all: the six todos applying these rulings cited
`"operator ruling 2026-08-08 (ao round-5 apply session, item N)"` — a session with **no doc anywhere in the corpus**.
`check_plan_operator_ruling_evidence.py` correctly flagged that as unsourced (58 → 63 violations), and because
`quality-gates.sh` gates the whole tree, every agent's `quickmerge.sh` in this repo failed on an inherited red
regardless of what they changed. Details:
`/plans/archive/2026_08/issues/ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md`.

**What this doc does and does not settle.** It settles _traceability_: a reader can now find every ruling in one place
and see exactly which todo claims it. It does **not** settle _authenticity_ — only the operator can confirm these were
really issued as quoted. That distinction is the whole point of the gate
(`/plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md` is the precedent: an
unsourced ruling citation is ambiguous between a missing-citation bug and a worker overriding an `[OPERATOR]` gate, and
a third party cannot tell which from the outside). The confirmation todo below stays open until the operator answers.

## The rulings, as cited

- **Item 1 — dispatch `sequential` gate** — _"Approve, ship as drafted"_. Cited by
  `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_2026_07_30.md` (~line 228), which labels it "interactive Q&A,
  item 1 of the ao round-5 apply digest". Note the citing todo's own finding: on locating the real source doc
  (`/plans/archive/issues/dispatch_sequential_gate_fix_2026_07_24.md`) the same edit had **already** been
  operator-approved and shipped 2026-08-06 during `/plan-reconcile ao` — so item 1 duplicates an earlier ruling.
- **Item 2 — persist review-agent findings** — _"Yes, build it."_ Cited by
  `/plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md` (~line 163). Scope per that todo: make review
  findings a structured, queryable event (e.g. a `review_finding` activity-log entry with severity + task_id) rather
  than chat-only.
- **Item 3 — task-usage backfill** — _"Run the backfill."_ Cited by
  `/plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md` (~line 444). Scope: extend
  `agent-orchestrator/scripts/orchestrator/backfill_task_usage.py` to cover one-off completions and run it for the
  completions lost while the todo-24 bug was live.
- **Item 4 — cross-role routing change sign-off** — _"Conditional: check for conflicts with other
  plans/issues/implementations first; ship only if it is a clear improvement and does not conflict. Operator delegates
  the conflict-check judgment call back to Claude."_ Cited by
  `/plans/archive/2026_08/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md` (~line
  186).
- **Item 5 — blocked-question UX redesign scope** — _"All three: session_id capture + transcript-jump +
  dedup/similarity."_ Cited by `/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`
  (~line 148).
- **Item 6 — context_scope enforcement track** — _"AO-dispatched plan (operator general preference noted: default to
  AO-dispatched plans going forward when this LOCAL-vs-AO framing recurs). Mechanism choice itself not specified — use
  engineering judgment among task-brief rendering / RULES.md STEP0 / QG-style gate."_ Cited by
  `/plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md` (~line 105).
- **Item 15 — slot-collision policy** — _"Build a collision-warning mechanism (detect + warn when 2 sessions share a
  slot, not a hard block)."_ Cited by
  `/plans/archive/2026_08/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md` (~line 202), which
  reads it as explicitly NOT a hard each-slot-ONE-agent enforcement policy.

**The item numbering is not contiguous here.** Items 1-6 and 15 are the ones found by grepping the corpus for citations
of this session; the gap (7-14) means either those rulings were applied to docs that cite the session differently, or
they were never applied. That gap is itself a reason the session needs a real record — an index nobody can enumerate
cannot be audited for completeness.

## Todos

- **[OPERATOR] P1. CANCELLED — SUPERSEDED 2026-08-22 (D24 ruling: OPERATOR-RULED 2026-08-21 — CONFIRMED all 6
  round-5 rulings accurate as transcribed; no correction needed).**
- [ ] [DOCS] P2. Per D23 ruling (2026-08-22): dedicated ruling-record doc per session chosen — simplest, with 2
      working precedents already in the corpus. Write that convention into `plans/PLAN_FORMAT.md` § operator-ruling
      citations (this doc's own shape: a dedicated doc per interactive ruling session, transcribed verbatim from the
      citing todos) so the next session cites a real path from the start. **Done when**: the convention is
      documented and `task_template.md` points at it. Repo: unified-trading-pm.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (2 entries).

- **2026-08-08 (slot 3, interactive)** — Created to unblock a repo-wide `quickmerge` stall, with the operator's explicit
  go-ahead to fix blocking issues in other plans. Deliberately scoped to transcription: the six rulings are copied
  verbatim from their citing todos and each is attributed to the citing doc + line, so this adds traceability without
  adding authority. Authenticity confirmation is tracked as the open `[OPERATOR]` todo above rather than assumed — per
  `/plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md`, an agent inventing
  a plausible source for someone else's ruling is the exact failure the evidence gates exist to catch.
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — first audit pass on this doc. Item 1 is an
  operator-only authenticity confirmation (cannot be worker-determined by design). Item 2 (give future ruling sessions a
  home) requires a genuine convention design decision among 3 named options — a judgment call, not a mechanical fix. No
  new facts apply.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since round9.
  Item 1 remains operator-only-by-design (only the operator can confirm they personally issued a ruling); item 2 remains
  an unresolved 3-way convention design choice with no stated preference in the doc itself.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:6829cfa50fbda5db]: KEEP-NA, valid — item 1 is an operator-only authenticity confirmation; item 2 is an unresolved 3-way convention design choice with no stated preference; both re-affirmed by 2 prior audit passes.
- **2026-08-22 — ruling D23 (Ruling-record convention)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Dedicated ruling-record doc per session — simplest, with 2 working precedents
  already in the corpus. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **2026-08-22 — ruling D24 (Round-5 ruling transcription check)**: OPERATOR-RULED 2026-08-21 — CONFIRMED: all 6
  round-5 rulings accurate as transcribed. Close the doc. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
